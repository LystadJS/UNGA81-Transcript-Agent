"""Independent NumPy/SciPy/sklearn checks, not a claim of global NMF uniqueness."""
import argparse
import json
import subprocess
import warnings
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.sparse import csr_matrix
from sklearn.decomposition import non_negative_factorization

parser=argparse.ArgumentParser()
parser.add_argument('--node',default='node')
parser.add_argument('--corpus')
parser.add_argument('--fits')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
code="""
const N=require('./site/nmf-core.js');
const X=[[1,0,2],[0,3,1],[2,1,0],[1,1,1]],x=N.matrix(X.map(r=>new Map(r.map((v,i)=>['t'+i,v])))),initial=N.initialize(x,2,42);
const W=new Float64Array(initial.W),H=new Float64Array(initial.H);for(let i=0;i<50;i++)N.step(x,W,H,2);
console.log(JSON.stringify({X,W0:[...initial.W],H0:[...initial.H],W:[...W],H:[...H],residual:N.residual(x,W,H,2)}));
"""
d=json.loads(subprocess.check_output([args.node,'-e',code],cwd=root,text=True,encoding='utf-8'))
X=np.array(d['X'],dtype=float);W0=np.array(d['W0']).reshape(4,2);H0=np.array(d['H0']).reshape(2,3)
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    W,H,_=non_negative_factorization(csr_matrix(X),W=W0.copy(),H=H0.copy(),n_components=2,init='custom',solver='mu',beta_loss='frobenius',tol=0,max_iter=50,random_state=42)
np.testing.assert_allclose(W,np.array(d['W']).reshape(4,2),atol=1e-11,rtol=1e-10)
np.testing.assert_allclose(H,np.array(d['H']).reshape(2,3),atol=1e-11,rtol=1e-10)
np.testing.assert_allclose(np.linalg.norm(X-W@H),d['residual'],atol=1e-10)
result={'status':'PASS','fixed_initialization_sklearn_mu_50_iterations':True,'live_fits':[],'alignments':[]}
if args.corpus and args.fits:
    corpus=Path(args.corpus).resolve();folder=Path(args.fits).resolve()
    code="const fs=require('fs'),A=require('./site/analysis-core.js');const rows=JSON.parse(fs.readFileSync(process.argv[1])).records;console.log(JSON.stringify(rows.map(r=>({id:r.id,text:r.text}))));"
    rows=json.loads(subprocess.check_output([args.node,'-e',code,str(corpus)],cwd=root,text=True,encoding='utf-8'))
    fits={}
    for policy in ['full','substantive','inclusive']:
        for k in [4,6,8]:
            f=json.loads((folder/f'{policy}-{k}.json').read_text(encoding='utf-8'));fits[policy,k]=f
            # Reuse production tokenization; independently reconstruct every value and metric.
            code="const fs=require('fs'),A=require('./site/analysis-core.js');const c=JSON.parse(fs.readFileSync(process.argv[1])),f=JSON.parse(fs.readFileSync(process.argv[2])),ids=new Set([...f.points,...f.excluded].map(p=>p.id));const r=c.records.filter(r=>ids.has(r.id));console.log(JSON.stringify({ids:r.map(p=>p.id),vectors:A.tfidf(r).vectors.map(v=>[...v])}));"
            t=json.loads(subprocess.check_output([args.node,'-e',code,str(corpus),str(folder/f'{policy}-{k}.json')],cwd=root,text=True,encoding='utf-8'))
            idx={term:j for j,term in enumerate(f['vocabulary'])};vs=dict(zip(t['ids'],t['vectors']))
            X=np.zeros((len(f['points']),len(idx)))
            for i,p in enumerate(f['points']):
                for term,v in vs[p['id']]:X[i,idx[term]]=v
            W=np.array([p['weights'] for p in f['points']]);H=np.array(f['factors']['H'])
            assert np.min(W)>=0 and np.min(H)>=0
            np.testing.assert_allclose(np.linalg.norm(H,axis=1),1,atol=1e-10)
            residual=float(np.linalg.norm(X-W@H));np.testing.assert_allclose(residual,f['diagnostics']['residual'],atol=1e-9)
            np.testing.assert_allclose(W/W.sum(axis=1,keepdims=True),[p['shares'] for p in f['points']],atol=1e-10)
            np.testing.assert_allclose(1-residual**2/np.sum(X**2),f['diagnostics']['squared_reconstruction_fraction'],atol=1e-10)
            result['live_fits'].append({'policy':policy,'components':k,'passages':len(W),'residual':residual})
    comparison=json.loads((folder/'comparison.json').read_text(encoding='utf-8'))
    for expected in comparison['comparisons']:
        left,right=fits['full',6],fits[expected['policy'],6];li={t:i for i,t in enumerate(left['vocabulary'])};ri={t:i for i,t in enumerate(right['vocabulary'])};terms=sorted(li.keys()&ri.keys())
        cosine=np.array(left['factors']['H'])[:,[li[t] for t in terms]]@np.array(right['factors']['H'])[:,[ri[t] for t in terms]].T
        i,j=linear_sum_assignment(cosine,maximize=True)
        np.testing.assert_allclose(cosine[i,j].mean(),expected['mean_cosine'],atol=1e-10)
        rpoints={p['id']:p for p in right['points']};shared=[p for p in left['points'] if p['id'] in rpoints]
        l1=np.mean([np.abs(np.array(p['shares'])-np.array(rpoints[p['id']]['shares'])[j]).sum() for p in shared])
        np.testing.assert_allclose(l1,expected['mean_mixture_l1'],atol=1e-10)
        result['alignments'].append({'policy':expected['policy'],'cosine':float(cosine[i,j].mean()),'mixture_l1':float(l1)})
print(json.dumps(result,indent=2))
