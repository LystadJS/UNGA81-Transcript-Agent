"""Independent sklearn EM, SciPy densities/alignment and NumPy soft-refit checks."""
import argparse
import json
import subprocess
import warnings
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.special import logsumexp, xlogy
from sklearn.mixture import GaussianMixture

parser=argparse.ArgumentParser();parser.add_argument('--node',default='node');parser.add_argument('--fits');args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
def node(code,*values):
    return json.loads(subprocess.check_output([args.node,'-e',code,*map(str,values)],cwd=root,text=True,encoding='utf-8'))
def fit_reference(X,initial,covariance,reg,iterations):
    var=np.asarray(initial['variances']);precisions=1/(var if covariance=='diag' else var[:,0])
    model=GaussianMixture(n_components=len(initial['weights']),covariance_type=covariance,reg_covar=reg,max_iter=iterations,tol=0,n_init=1,
        weights_init=np.array(initial['weights']),means_init=np.array(initial['means']),precisions_init=precisions,random_state=42)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore');model.fit(X)
    return model
code="""
const G=require('./site/gmm-core.js');
(async()=>{const X=Array.from({length:31},(_,i)=>[Math.sin(i*.7)+(i%3)*.3,Math.cos(i*.4)]),out=[];
for(const covariance of ['diag','spherical']){const initial={weights:[.4,.6],means:[[-.5,.2],[.9,-.4]],variances:covariance==='diag'?[[1.2,.7],[.9,1.4]]:[[1.2,1.2],[.9,.9]],covariance,regularization:.001};
out.push({X,initial,covariance,result:await G.solve(X,{covariance,regularization:.001,maxIterations:25,tolerance:0},initial)});}console.log(JSON.stringify(out));})();
"""
fixtures=node(code)
for fixture in fixtures:
    X=np.array(fixture['X']);r=fixture['result'];ref=fit_reference(X,fixture['initial'],fixture['covariance'],.001,25)
    np.testing.assert_allclose(ref.weights_,r['model']['weights'],atol=1e-9,rtol=1e-8)
    np.testing.assert_allclose(ref.means_,r['model']['means'],atol=1e-9,rtol=1e-8)
    np.testing.assert_allclose(ref.predict_proba(X),r['responsibilities'],atol=1e-9,rtol=1e-8)
    np.testing.assert_allclose(ref.score(X)*len(X),r['log_likelihood'],atol=1e-8)
result={'status':'PASS','sklearn_25_iteration_fixtures':['diag','spherical'],'live_fits':[]}
if args.fits:
    for filename in sorted(Path(args.fits)/f'{policy}-{cov}.json' for policy in ['full','substantive','inclusive'] for cov in ['diag','spherical']):
        if filename.name=='reference.json':continue
        data=json.loads(filename.read_text(encoding='utf-8'));left=data['methods']['clusters']
        for f in [left,left['comparison']['alternative']]:
            if f.get('skipped'):continue
            g=f['gmm'];X=np.array([p[f['representation']] for p in f['points']]);n,d=X.shape;k=len(g['weights']);W=np.array(g['weights']);M=np.array(g['means']);V=np.array(g['variances'])
            logs=np.log(W)[None,:]-.5*np.sum(np.log(2*np.pi*V)[None,:,:]+(X[:,None,:]-M[None,:,:])**2/V[None,:,:],axis=2)
            densities=logsumexp(logs,axis=1);posterior=np.exp(logs-densities[:,None]);ll=float(densities.sum())
            stored=np.array([p['memberships'] for p in f['points']]);np.testing.assert_allclose(posterior,stored,atol=1e-9)
            np.testing.assert_array_equal(np.argmax(posterior,axis=1)+1,[p['cluster'] for p in f['points']])
            np.testing.assert_allclose(ll,g['log_likelihood'],atol=1e-8)
            p=k*d+(k*d if g['covariance_type']=='diag' else k)+k-1
            assert p==g['parameter_count'];np.testing.assert_allclose([2*p-2*ll,np.log(n)*p-2*ll],[g['aic'],g['bic']],atol=1e-8)
            entropy=-np.sum(xlogy(posterior,posterior),axis=1)/np.log(k) if k>1 else np.zeros(n)
            np.testing.assert_allclose(entropy,[p['normalized_entropy'] for p in f['points']],atol=1e-9)
            # Use identical JS k-means initialization labels, then independent EM.
            initial_labels=node("const fs=require('fs'),C=require('./site/cluster-core.js');const d=JSON.parse(fs.readFileSync(process.argv[1])).methods.clusters,f=process.argv[2]==='pca'?d:d.comparison.alternative;console.log(JSON.stringify(C.oneKmeans(f.points.map(p=>p[f.representation]),f.parameters.k,C.rng(f.gmm.selected_seed)).labels));",filename.resolve(),f['representation'])
            counts=np.bincount(initial_labels,minlength=k);means=np.array([X[np.array(initial_labels)==c].mean(axis=0) for c in range(k)])
            variances=np.array([np.mean((X[np.array(initial_labels)==c]-means[c])**2,axis=0) for c in range(k)])
            if g['covariance_type']=='spherical':variances=np.repeat(variances.mean(axis=1)[:,None],d,axis=1)
            initial={'weights':(counts/n).tolist(),'means':means.tolist(),'variances':(variances+g['regularization']).tolist()}
            ref=fit_reference(X,initial,g['covariance_type'],g['regularization'],g['iterations'])
            em_error=float(np.max(np.abs(ref.predict_proba(X)-posterior)));np.testing.assert_allclose(ref.predict_proba(X),posterior,atol=1e-7,rtol=1e-7)
            samples=f['stability']['runs'];tv=[];per_point=[[] for _ in range(n)];checked=0
            for sample in samples:
                if sample.get('skipped'):continue
                indices=sample['indices'];a=posterior[indices];b=np.array(sample['memberships']);scores=a.T@b
                ri,ci=linear_sum_assignment(scores,maximize=True);mapping=np.array(sample['soft_agreement']['mapping'])-1
                assert sorted(mapping.tolist())==list(range(k));np.testing.assert_allclose(scores[np.arange(k),mapping].sum(),scores[ri,ci].sum(),atol=1e-8)
                changes=np.abs(a-b[:,mapping]).sum(axis=1)/2
                np.testing.assert_allclose(changes,sample['soft_agreement']['point_total_variation'],atol=1e-9)
                np.testing.assert_allclose(changes.mean(),sample['soft_agreement']['mean_total_variation'],atol=1e-9)
                for i,v in zip(indices,changes):per_point[i].append(float(v))
                tv.append(float(changes.mean()));checked+=1
            s=f['stability']['soft_membership'];assert s['mean_total_variation']['count']==checked
            if tv:np.testing.assert_allclose(np.mean(tv),s['mean_total_variation']['mean'],atol=1e-9)
            for values,p in zip(per_point,s['points']):
                assert len(values)==p['count']
                if values:np.testing.assert_allclose(np.mean(values),p['mean'],atol=1e-9)
            result['live_fits'].append({'file':filename.name,'representation':f['representation'],'passages':n,'independent_EM_max_posterior_error':em_error,'soft_refits_checked':checked})
print(json.dumps(result,indent=2))
