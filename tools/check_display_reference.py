"""Independent distance, neighborhood, and SMACOF checks from actual saved layouts."""
import argparse,json,subprocess,warnings
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist,squareform
from sklearn.manifold import smacof

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def order(x):
    sq=squareform(pdist(np.array(x),'sqeuclidean'));rounded=np.floor(sq*1e12+.5)/1e12;n=len(x)
    return np.array([sorted((j for j in range(n) if j!=i),key=lambda j:(rounded[i,j],j)) for i in range(n)])
def metrics(a,b,k=10):
    n=len(a);intrusion=omission=shared=0
    for i in range(n):
        original=set(a[i,:k]);display=set(b[i,:k]);shared+=len(original&display)
        intrusion+=sum(int(np.where(a[i]==j)[0][0])+1-k for j in display-original)
        omission+=sum(int(np.where(b[i]==j)[0][0])+1-k for j in original-display)
    factor=2/(n*k*(2*n-3*k-1))
    return {'neighbor_overlap':shared/(n*k),'trustworthiness':1-factor*intrusion,'continuity':1-factor*omission}
def check_values(actual,expected):
    for key,v in expected.items():np.testing.assert_allclose(actual[key],v,atol=1e-10,rtol=1e-10)
def scaled_error(x,y):
    a=pdist(x);b=pdist(y);scale=np.dot(a,b)/np.dot(b,b);return {'scale':scale,'relative_distance_error':np.linalg.norm(a-scale*b)/np.linalg.norm(a)}

def run(umap_path,mds_path,node):
    u=read(umap_path);umap_checks=seed_checks=0
    for f in u['fits']:
        high=order(f['scores']);baseline=next(r for r in f['runs'] if r['seed']==42 and r['neighbors']==15);base_order=order(baseline['coordinates'])
        ranks={}
        for r in f['runs']:
            low=order(r['coordinates']);ranks[(r['neighbors'],r['seed'])]=low
            check_values(r['fidelity'],metrics(high,low));check_values(r,scaled_error(f['scores'],r['coordinates']))
            np.testing.assert_allclose(metrics(base_order,low)['neighbor_overlap'],r['reference_layout_overlap'],atol=1e-12);umap_checks+=1
        for pair in f['seed_comparisons']:
            np.testing.assert_allclose(metrics(ranks[(pair['neighbors'],pair['seeds'][0])],ranks[(pair['neighbors'],pair['seeds'][1])])['neighbor_overlap'],pair['overlap'],atol=1e-12);seed_checks+=1
    result={'status':'PASS','umap_layouts_checked':umap_checks,'umap_seed_pairs_checked':seed_checks,'mds_fits':[]}
    if mds_path:
        root=Path(__file__).resolve().parents[1]
        code="const D=require('./site/mds-core.js');const x=Array.from({length:31},(_,i)=>[Math.sin(i),Math.cos(i*.4),i%5/5]),initial=D.initialize(x.length,D.distances(x),42);D.solve(D.distances(x),initial,{maxIterations:50,tolerance:0}).then(f=>console.log(JSON.stringify({x,initial,...f})));"
        fixture=json.loads(subprocess.check_output([node,'-e',code],cwd=root,text=True,encoding='utf-8'))
        y,stress=smacof(squareform(pdist(fixture['x'])),metric=True,init=np.array(fixture['initial']),n_init=1,max_iter=50,eps=0,normalized_stress=False)
        np.testing.assert_allclose(y,fixture['coordinates'],atol=1e-9);np.testing.assert_allclose(stress,fixture['stress'],atol=1e-9);result['independent_smacof_50_steps']=True
        for m in read(mds_path)['fits']:
            f=next(f for f in u['fits'] if f['policy']==m['policy'] and f['representation']==m['representation']);x=np.array(f['scores']);y=np.array(m['coordinates']);a=pdist(x);b=pdist(y);stress=float(np.sum((a-b)**2))
            np.testing.assert_allclose([stress,np.sqrt(stress/np.sum(a*a)),np.sqrt(stress/np.sum(b*b))],[m['stress'],m['relative_distance_error'],m['stress1']],atol=1e-9)
            check_values(m['fidelity'],metrics(order(x),order(y)));check_values(m['scale_adjusted'],scaled_error(x,y))
            errors=squareform((a-b)**2).sum(axis=1);np.testing.assert_allclose(np.sqrt(errors/(len(x)-1)/np.mean(a*a)),m['point_relative_error'],atol=1e-9)
            assert sum(bin['count'] for bin in m['bins'])==len(a)
            # Independently fit the actual selected start for its recorded step count.
            init_code="const D=require('./site/mds-core.js'),fs=require('fs'),f=JSON.parse(fs.readFileSync(process.argv[1])).fits.find(f=>f.policy===process.argv[2]&&f.representation===process.argv[3]);console.log(JSON.stringify(D.initialize(f.scores.length,D.distances(f.scores),Number(process.argv[4]))));"
            initial=json.loads(subprocess.check_output([node,'-e',init_code,str(Path(umap_path).resolve()),m['policy'],m['representation'],str(m['seed'])],cwd=root,text=True,encoding='utf-8'))
            ref,refstress=smacof(squareform(pdist(x)),metric=True,init=np.array(initial),n_init=1,max_iter=m['iterations'],eps=0,normalized_stress=False)
            error=float(np.max(np.abs(ref-y)));np.testing.assert_allclose(ref,y,atol=1e-7,rtol=1e-7);np.testing.assert_allclose(refstress,stress,atol=1e-7)
            result['mds_fits'].append({'policy':m['policy'],'representation':m['representation'],'pairs':len(a),'maximum_coordinate_error':error})
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('umap');p.add_argument('--mds');p.add_argument('--node',default='node');a=p.parse_args();print(json.dumps(run(a.umap,a.mds,a.node),indent=2))
