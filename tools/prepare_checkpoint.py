"""Prepare the user-selected, pinned local BERT pilot candidate; never publish it."""
from pathlib import Path
import argparse, hashlib, json, urllib.request

MODEL='google/bert_uncased_L-2_H-128_A-2'
REVISION='30b0a37ccaaa32f332884b96992754e246e48c5f'
FILES={'config.json':('git','333ec19609b98a6cd11b79a5770a163a2f0464c8'),
       'vocab.txt':('git','fb140275c155a9c7c5a3b3e0e77a9e839594a938'),
       'model.safetensors':('sha256','7fb69ad9f6866d8983183c930e33828f326470bf6ad8bbb2ad4ed957a92e9414')}

def prepare(root):
    from transformers import BertTokenizerFast, BertForSequenceClassification
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    for name,(kind,expected) in FILES.items():
        with urllib.request.urlopen(f'https://huggingface.co/{MODEL}/resolve/{REVISION}/{name}',timeout=120) as r:raw=r.read(25_000_001)
        if len(raw)>25_000_000:raise ValueError('Checkpoint member exceeds bound')
        actual=hashlib.sha256(raw).hexdigest() if kind=='sha256' else hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
        if actual!=expected:raise ValueError('Upstream checkpoint hash mismatch: '+name)
        (root/name).write_bytes(raw)
    tokenizer=BertTokenizerFast(vocab_file=str(root/'vocab.txt'),do_lower_case=True);tokenizer.save_pretrained(root)
    model,info=BertForSequenceClassification.from_pretrained(root,local_files_only=True,use_safetensors=True,num_labels=2,output_loading_info=True)
    if any(k.startswith(('bert.encoder.','bert.embeddings.')) for k in info['missing_keys']):raise ValueError('Missing pretrained encoder')
    manifest={'purpose':'selected_candidate','model_id':MODEL,'revision':REVISION,'selection':'User selected for local audit-only pilot; not a validated classifier','license':'Apache-2.0 (publisher model card)','model_card':f'https://huggingface.co/{MODEL}',
      'assets':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()},'parameters':sum(p.numel() for p in model.parameters()),'encoder_loaded':True,'loading_info':info,'tokenizer_size':len(tokenizer),'publication_eligible':False,'training_started':False}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return {k:v for k,v in manifest.items() if k!='assets'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();print(json.dumps(prepare(a.output),indent=2))
