"""Manual, optional-dependency training. Never invoked by collection or publication."""
import math
import random
import re
from pathlib import Path
from .contracts import LABELS, STATUSES, check_labels, digest, read_json, write_json
from .runtime import source_windows


def train(labels, registration, base_model, revision, policy, output, epochs=3, batch_size=8, resume=None):
    rows = check_labels(labels, registration, 'train')
    if registration.get('policy_sha256') != digest(policy):
        raise ValueError('Training policy differs from the prospective acceptance lock')
    from ..attribution import infer_capacity
    attribution=infer_capacity({'text':''})
    if any(registration.get(k)!=attribution[k] for k in ('attribution_method_version','attribution_registry_sha256')):
        raise ValueError('Attribution pipeline changed after benchmark registration')
    if not re.fullmatch(r'[a-f0-9]{40}', revision):
        raise ValueError('An immutable upstream model commit is required')
    if set(r['label'] for r in rows if r['status']=='clear') != set(LABELS):
        raise ValueError('Training requires actual reviewed examples of all five stance classes')
    base = Path(base_model)
    if not base.is_dir():
        raise ValueError('Pretrained model/tokenizer must already exist locally')
    out = Path(output)
    if out.exists() and not resume:
        raise ValueError('Use a new candidate directory, or explicitly resume a checkpoint')
    try:
        import numpy as np
        import torch
        from torch import nn
        from transformers import AutoModel, AutoTokenizer
        from safetensors.torch import save_file
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
    except ImportError as exc:
        raise RuntimeError('Install requirements-model.txt for manual local training') from exc
    if epochs < 1 or batch_size < 1:
        raise ValueError('Positive training budget required')
    random.seed(20261111); np.random.seed(20261111); torch.manual_seed(20261111)
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(str(base), local_files_only=True, use_fast=True)
    encoder = AutoModel.from_pretrained(str(base), local_files_only=True, trust_remote_code=False)
    if encoder.config.model_type != 'distilbert':
        raise ValueError('This candidate runner supports the built-in DistilBERT architecture only')

    class Heads(nn.Module):
        def __init__(self):
            super().__init__(); self.encoder = encoder
            self.stance = nn.Linear(encoder.config.hidden_size, len(LABELS))
            self.status = nn.Linear(encoder.config.hidden_size, len(STATUSES))

        def forward(self, input_ids, attention_mask):
            representation = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state[:,0]
            return self.stance(representation), self.status(representation)

    model = Heads().cpu()
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    input_digest = digest({'labels':digest(labels),'registration':digest(registration),'revision':revision,
                           'base_assets':{p.name:digest(p.read_bytes()) for p in base.iterdir() if p.is_file()},
                           'policy':digest(policy)})
    start_epoch = 0
    if resume:
        checkpoint = torch.load(resume, map_location='cpu', weights_only=True)
        if checkpoint['input_sha256'] != input_digest:
            raise ValueError('Checkpoint does not match source labels, model assets and policy')
        model.load_state_dict(checkpoint['model']); optimizer.load_state_dict(checkpoint['optimizer'])
        start_epoch = checkpoint['next_epoch']
    examples = []
    for row in rows:
        budget = min(350,512-len(tokenizer(row['proposition'],add_special_tokens=False)['input_ids'])-3)
        if budget <= 64: raise ValueError('Proposition exceeds context budget')
        # Gold focal offsets are relative to the provided context, distinct from absolute source offsets.
        focal_start = row.get('focal_start',0); focal_end = row.get('focal_end',len(row['text']))
        before=len(examples)
        for window in source_windows(row['text'],budget,64,tokenizer):
            if not (window['start'] <= focal_start and window['end'] >= focal_end):
                continue
            examples.append((row['proposition'],window['text'],
                             LABELS.index(row['label']) if row['status']=='clear' else -100,
                             STATUSES.index(row['status'])))
        if before==len(examples):
            raise ValueError('Gold focal span does not fit any window: '+row['pair_id'])
    if not examples: raise ValueError('No gold focal spans fit a context window; supply narrower reviewed focal spans')
    out.mkdir(parents=True,exist_ok=True)
    losses=[]
    for epoch in range(start_epoch,epochs):
        model.train(); order=list(range(len(examples))); random.Random(20261111+epoch).shuffle(order)
        epoch_loss=0.
        for offset in range(0,len(order),batch_size):
            batch=[examples[i] for i in order[offset:offset+batch_size]]
            encoded=tokenizer([x[0] for x in batch],[x[1] for x in batch],padding=True,return_tensors='pt',truncation=False)
            if encoded['input_ids'].shape[-1]>512: raise ValueError('Context budget exceeded')
            stance,status=model(encoded['input_ids'],encoded['attention_mask'])
            target=torch.tensor([x[2] for x in batch]); mask=target!=-100
            loss=nn.functional.cross_entropy(status,torch.tensor([x[3] for x in batch]))
            if mask.any(): loss=loss+nn.functional.cross_entropy(stance[mask],target[mask])
            optimizer.zero_grad();loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step()
            epoch_loss+=float(loss.detach())
        losses.append(epoch_loss)
        torch.save({'model':model.state_dict(),'optimizer':optimizer.state_dict(),'next_epoch':epoch+1,
                    'input_sha256':input_digest},out/'checkpoint.pt')
    model.eval(); tokenizer.save_pretrained(out); encoder.config.save_pretrained(out)
    save_file({k:v.contiguous() for k,v in model.state_dict().items()},str(out/'model.safetensors'))
    dummy=tokenizer('A precisely defined proposition','A source-backed statement.',return_tensors='pt')
    torch.onnx.export(model,(dummy['input_ids'],dummy['attention_mask']),str(out/'model.onnx'),
                      input_names=['input_ids','attention_mask'],output_names=['stance_logits','status_logits'],
                      dynamic_axes={'input_ids':{0:'batch',1:'sequence'},'attention_mask':{0:'batch',1:'sequence'},
                                    'stance_logits':{0:'batch'},'status_logits':{0:'batch'}},opset_version=17,dynamo=False)
    clear=[r for r in rows if r['status']=='clear']
    vectorizer=TfidfVectorizer(ngram_range=(1,2),max_features=20000)
    matrix=vectorizer.fit_transform([r['proposition']+' [SEP] '+r['text'] for r in clear])
    baseline=LogisticRegression(max_iter=1000,random_state=20261111).fit(matrix,[r['label'] for r in clear])
    write_json(out/'baseline.json',{'kind':'tfidf_logistic','classes':baseline.classes_.tolist(),
               'vocabulary':{k:int(v) for k,v in vectorizer.vocabulary_.items()},'idf':vectorizer.idf_.tolist(),
               'coefficients':baseline.coef_.tolist(),'intercept':baseline.intercept_.tolist(),
               'status':'fitted_on_training_only_not_empirically_accepted'})
    artifacts={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.is_file() and p.name!='checkpoint.pt'}
    manifest={'schema':'un.stance-model.v1','model_id':'distilbert-'+digest(artifacts)[:20],
              'candidate':'distilbert/distilbert-base-uncased','upstream_revision':revision,
              'registration_sha256':digest(registration),'training_labels_sha256':digest(labels),
              'policy_sha256':digest(policy),
              'attribution_method_version':attribution['attribution_method_version'],
              'attribution_registry_sha256':attribution['attribution_registry_sha256'],
              'input_sha256':input_digest,'artifacts':artifacts,'labels':list(LABELS),'statuses':list(STATUSES),
              'temperature':1.0,'decision_threshold':policy.get('production_threshold_default',.9),
              'status_threshold':policy.get('production_status_threshold',.9),
              'calibration_status':'not_run','production_accepted':False,
              'training':{'rows':len(rows),'windows':len(examples),'epochs':epochs,'losses':losses,'device':'cpu'}}
    write_json(out/'manifest.json',manifest)
    return {'status':'candidate_trained_not_accepted','model_id':manifest['model_id'],'training_rows':len(rows)}
