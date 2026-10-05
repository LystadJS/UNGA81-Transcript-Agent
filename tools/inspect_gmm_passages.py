"""Rank existing mixture sensitivity; keep inspection separate from human labels."""
import argparse, hashlib, html, json
from pathlib import Path

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def run(corpus_path, fits_path, output):
    repo=Path(__file__).resolve().parents[1]
    corpus=read(corpus_path); comparison=read(Path(fits_path)/'comparison.json')
    assert hashlib.sha256(Path(corpus_path).read_bytes()).hexdigest()==comparison['corpus_sha256']
    records={r['id']:r for r in corpus['records']}
    mask_path=repo/'docs/passage-type-reviewed-mask.json';mask=read(mask_path)
    assert hashlib.sha256(mask_path.read_bytes()).hexdigest()==comparison['mask_sha256']
    types={r['id']:r['confirmed_type'] for r in mask['rows']}
    notes=read(repo/'docs/membership-inspection-notes.json')['notes'];selected={};rankings={}
    for policy in ['full','substantive','inclusive']:
        scores={}
        for cov in ['diag','spherical']:
            fit=read(Path(fits_path)/f'{policy}-{cov}.json')['methods']['clusters']
            for f in [fit,fit['comparison']['alternative']]:
                points={p['id']:p for p in f['points']}
                for p in f['stability']['soft_membership']['points']:
                    assert p['count']>0 and points[p['id']]['text_sha256']==records[p['id']]['text_sha256']
                    scores.setdefault(p['id'],[]).append({'representation':f['representation'],'covariance':cov,'mean_tv':p['mean'],'sampled_refits':p['count'],'reference_max_membership':points[p['id']]['max_membership']})
        rows=[]
        for id,models in scores.items():
            assert len(models)==4
            r=records[id];rows.append({'id':id,'country':r['country'],'date':r['date'],'source_url':r['source_url'],'text_sha256':r['text_sha256'],'reviewed_type':types[id],'words':len(r['text'].split()),'mean_tv_across_four_models':sum(m['mean_tv'] for m in models)/4,'models':models})
        rows.sort(key=lambda r:(-r['mean_tv_across_four_models'],r['id']));rankings[policy]=rows
        for r in rows[:5]:
            assert r['id'] in notes,'A selected passage still needs inspection'
            selected[r['id']]={**r,'inspection_note':notes[r['id']]}
    assert set(notes)==set(selected),'Inspection notes must describe the selected top-five union'
    result={'schema':'un.membership-inspection.v1','corpus_sha256':comparison['corpus_sha256'],'mask_sha256':comparison['mask_sha256'],'protocol':'Top five per inclusion policy, ranked by equal-weight mean of per-passage mean TV across PCA/LSA and diagonal/spherical four-component fits. Means use successful sampled refits only; this ranks review leads, not significance or semantic error. Text inspection does not authenticate audio or factual assertions. No human labels or originals changed.','rankings':rankings,'inspected':list(selected.values())}
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    (output/'inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    sections=[]
    for r in selected.values():
        sections.append(f'<section><h2>{html.escape(r["country"])} · {r["date"]}</h2><p>{html.escape(r["id"])}</p><p>{html.escape(r["inspection_note"])}</p><a href="{html.escape(r["source_url"],quote=True)}">Open original source</a><details><summary>Complete cached segment</summary><p>{html.escape(records[r["id"]]["text"])}</p></details></section>')
    (output/'source-inspection.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Membership change: source inspection</title><style>body{max-width:1000px;margin:32px auto;padding:16px;font:17px/1.6 Arial;color:#152c43}section{border-top:1px solid #ccd7e0;padding:20px 0}details{margin-top:16px}a{color:#002d74}</style><h1>Source inspection</h1><p>Local full-text companion. Analyst observations are separate from the saved human passage-type review. Factual assertions and audio have not been authenticated.</p>'+''.join(sections)+'</html>',encoding='utf-8')
    print(json.dumps({'inspected':len(selected),'original_sha256':comparison['corpus_sha256'],'labels_unchanged':True}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('corpus');p.add_argument('fits');p.add_argument('output');a=p.parse_args();run(a.corpus,a.fits,a.output)
