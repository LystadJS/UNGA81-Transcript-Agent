"""Bounded, audit-only reviewed-data experiment; independent of daily model gates."""
import argparse, hashlib, json, os, random
from pathlib import Path
from importlib.metadata import version
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ['TOKENIZERS_PARALLELISM']='false'
import numpy as np
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from transformers import BertTokenizerFast, BertForSequenceClassification
import reviewed_loader as loader
from evaluate_ai_baseline import metrics, predict

def dump(path,data):Path(path).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def seed(n):
    random.seed(n);np.random.seed(n);torch.manual_seed(n)
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
def texts(rows):return [r['quote'] for r in rows]
def labels(rows):
    y=[r['binary_label'] for r in rows]
    if any(v not in (0,1) for v in y):raise ValueError('Unresolved labels')
    return y
def separate(a,b):
    for key in ('iso3','text_sha256'):
        if {r[key] for r in a}&{r[key] for r in b}:raise ValueError('Split overlap: '+key)
    if max(r['event_date'] for r in a)>=min(r['event_date'] for r in b):raise ValueError('Non-forward dates')
def logistic(rows,p):
    c=p['logistic'];m=Pipeline([('tfidf',TfidfVectorizer(ngram_range=tuple(c['ngram_range']),min_df=c['min_df'],max_features=c['max_features'],sublinear_tf=c['sublinear_tf'])),('logistic',LogisticRegression(C=c['C'],max_iter=c['max_iter'],random_state=p['seed'],solver='liblinear'))])
    m.fit(texts(rows),labels(rows));return m
def encode(tokenizer,rows,p):
    limit=p['bert']['max_tokens'];t=texts(rows)
    if any(len(tokenizer(x,add_special_tokens=True)['input_ids'])>limit for x in t):raise ValueError('Input exceeds token limit; no silent truncation')
    return tokenizer(t,padding=True,truncation=False,return_tensors='pt')
def fit_bert(rows,p,checkpoint):
    seed(p['seed']);tokenizer=BertTokenizerFast.from_pretrained(checkpoint,local_files_only=True)
    model=BertForSequenceClassification.from_pretrained(checkpoint,local_files_only=True,use_safetensors=True,num_labels=2)
    encoded=encode(tokenizer,rows,p);y=torch.tensor(labels(rows));c=p['bert'];optimizer=torch.optim.AdamW(model.parameters(),lr=c['learning_rate'],weight_decay=c['weight_decay'])
    initial=model.bert.embeddings.word_embeddings.weight.detach().clone();losses=[]
    for epoch in range(c['epochs']):
        model.train();order=torch.randperm(len(rows));total=0
        for start in range(0,len(rows),c['batch_size']):
            idx=order[start:start+c['batch_size']];optimizer.zero_grad();loss=model(**{k:v[idx] for k,v in encoded.items()},labels=y[idx]).loss
            if not torch.isfinite(loss):raise ValueError('Nonfinite training loss')
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step();total+=loss.item()*len(idx)
        losses.append(total/len(rows))
    if torch.equal(initial,model.bert.embeddings.word_embeddings.weight):raise ValueError('Encoder did not update')
    return model,tokenizer,losses
def bert_prob(model,tokenizer,rows,p):
    model.eval();encoded=encode(tokenizer,rows,p);values=[]
    with torch.no_grad():
        for start in range(0,len(rows),p['bert']['batch_size']):
            values.extend(model(**{k:v[start:start+p['bert']['batch_size']] for k,v in encoded.items()}).logits.softmax(-1)[:,1].tolist())
    return np.array(values)
def score(rows,prob,p):return metrics(labels(rows),(np.asarray(prob)>=p['threshold']).astype(int).tolist())

def run(protocol,checkpoint,development,test_root,output):
    protocol,checkpoint,test_root,output=map(Path,(protocol,checkpoint,test_root,output))
    if output.exists():raise FileExistsError(output)
    p=json.loads(protocol.read_text());seed(p['seed'])
    bundles=[loader.load_bundle(root) for root in development]
    if any(b['engineering_fixture'] or not b['human_review_complete'] for b in bundles):raise ValueError('Human-reviewed development required')
    dev=[r for b in bundles for r in b['records']];labels(dev)
    if len(dev)!=48 or {r['binary_label'] for r in dev}!={0,1}:raise ValueError('Expected bounded two-class 48-label development pilot')
    separate(bundles[0]['records'],bundles[1]['records'])
    manifest=json.loads((checkpoint/'manifest.json').read_text())
    if manifest['revision']!='30b0a37ccaaa32f332884b96992754e246e48c5f':raise ValueError('Unapproved checkpoint revision')
    for name,h in manifest['assets'].items():
        if loader.sha(loader.safe(checkpoint,name))!=h:raise ValueError('Checkpoint changed')
    output.mkdir(parents=True);dump(output/'protocol.json',p)
    train,val=[b['records'] for b in bundles]
    lm=logistic(train,p);bm,tok,losses=fit_bert(train,p,checkpoint)
    validation={'logistic':score(val,lm.predict_proba(texts(val))[:,1],p),'bert':score(val,bert_prob(bm,tok,val,p),p)}
    del bm
    # Fixed refit, not selection or early stopping based on validation results.
    lm=logistic(dev,p);bm,tok,final_losses=fit_bert(dev,p,checkpoint)
    modeldir=output/'bert';bm.save_pretrained(modeldir,safe_serialization=True);tok.save_pretrained(modeldir)
    vec=lm.named_steps['tfidf'];clf=lm.named_steps['logistic']
    dump(output/'logistic.json',dict(vocabulary={k:int(v) for k,v in vec.vocabulary_.items()},idf=vec.idf_.tolist(),coef=clf.coef_.tolist(),intercept=clf.intercept_.tolist(),classes=clf.classes_.tolist()))
    model_hashes={x.relative_to(output).as_posix():loader.sha(x) for x in output.rglob('*') if x.is_file()}
    dump(output/'fit-complete.json',dict(protocol_sha256=loader.sha(protocol),development_hashes=[b['bundle_sha256'] for b in bundles],artifacts=model_hashes,validation=validation,validation_losses=losses,final_losses=final_losses))
    # Only now read the held-out lock, labels and export.
    lock=json.loads((test_root/'test-lock.json').read_text());test=loader.load_bundle(test_root)
    if loader.sha(test_root/'validated-test-import.json')!=lock['export_sha256'] or test['bundle_sha256']!=lock['bundle_sha256']:raise ValueError('Frozen test changed')
    if json.loads((test_root/'validated-test-import.json').read_text())!=test:raise ValueError('Test export differs')
    if [b['bundle_sha256'] for b in bundles]!=lock['development_bundle_hashes']:raise ValueError('Development identities changed')
    rows=test['records'];separate(dev,rows)
    if len(rows)!=24 or test['engineering_fixture'] or not test['human_review_complete']:raise ValueError('Wrong test packet')
    lp=lm.predict_proba(texts(rows))[:,1];bp=bert_prob(bm,tok,rows,p)
    # Verify persisted BERT and logistic parameters reproduce predictions.
    reload=BertForSequenceClassification.from_pretrained(modeldir,local_files_only=True,use_safetensors=True)
    if not np.allclose(bp,bert_prob(reload,tok,rows,p),rtol=0,atol=1e-7):raise ValueError('BERT roundtrip mismatch')
    saved=json.loads((output/'logistic.json').read_text());v=TfidfVectorizer(ngram_range=tuple(p['logistic']['ngram_range']),sublinear_tf=p['logistic']['sublinear_tf'],vocabulary=saved['vocabulary']);v.idf_=np.array(saved['idf'])
    decision=v.transform(texts(rows))@np.array(saved['coef'])[0]+saved['intercept'][0]
    if not np.allclose(lp,1/(1+np.exp(-decision)),atol=1e-10):raise ValueError('Logistic roundtrip mismatch')
    spec=json.loads((protocol.parent/'ai_baseline_v1.json').read_text())
    report=dict(protocol=p,protocol_sha256=loader.sha(protocol),runner_sha256=loader.sha(__file__),development_bundle_hashes=lock['development_bundle_hashes'],test_bundle_sha256=test['bundle_sha256'],validation=validation,test={'logistic':score(rows,lp,p),'bert':score(rows,bp,p),'keyword':metrics(labels(rows),[predict(r['quote'],spec) for r in rows]),'always_not_relevant':metrics(labels(rows),[0]*len(rows))},checkpoint_revision=manifest['revision'],runtime={k:version(k) for k in ['torch','transformers','scikit-learn','numpy','scipy']},model_artifacts_sha256=model_hashes,roundtrip_verified=True,publication_eligible=False,daily_integration=False,note='Single fixed run; 48 enriched development labels, 24 test passages with 3 positives; retrospective audit-only comparison, not release approval.')
    dump(output/'report.json',report);dump(output/'predictions-private.json',[dict(passage_id=r['passage_id'],actual=r['binary_label'],logistic=float(a),bert=float(b)) for r,a,b in zip(rows,lp,bp)])
    for name,h in model_hashes.items():
        if loader.sha(output/name)!=h:raise ValueError('Fit artifact changed during test evaluation')
    return report

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('protocol');a.add_argument('checkpoint');a.add_argument('test');a.add_argument('output');a.add_argument('--development',nargs=2,required=True);p=a.parse_args();print(json.dumps(run(p.protocol,p.checkpoint,p.development,p.test,p.output),indent=2))
