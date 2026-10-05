/* Shared, lightweight validation for the form, worker and Node entry points. */
(function(root) {
  'use strict';
  const STABILITY = Object.freeze({enabled:false, unit:'meeting', replicates:30, fraction:0.8, seed:31415});
  const HDBSCAN = Object.freeze({minClusterSize:15,minSamples:5,selection:'eom'});
  const G=typeof module!=='undefined'&&module.exports?require('./gmm-core.js'):root.UNGaussianMixture;
  const D=typeof module!=='undefined'&&module.exports?require('./mds-core.js'):root.UNMetricMDS;
  const DEFAULTS = Object.freeze({representation:'pca', algorithm:'kmeans', linkage:'ward', components:20, k:4, neighbors:15, minDist:0.1, seed:42, umapSeed:42, stability:STABILITY,hdbscan:HDBSCAN,gmm:G.DEFAULTS,mds:D.DEFAULTS});
  function integer(value, key, min, max) {
    if (!Number.isInteger(value) || value < min || value > max) {
      throw Error(`Invalid clustering setting: ${key} (${min}–${max}).`);
    }
  }
  function options(value = {}) {
    const o = {...DEFAULTS, ...value, stability:{...STABILITY, ...value.stability},hdbscan:{...HDBSCAN,...value.hdbscan},gmm:{...G.DEFAULTS,...value.gmm},mds:{...D.DEFAULTS,...value.mds}};
    if(typeof o.mds.enabled!=='boolean')throw Error('Choose whether to compare metric MDS.');
    if(o.mds.enabled)o.mds=D.options(o.mds);
    if(!['pca','lsa','compare'].includes(o.representation))throw Error('Choose PCA, LSA or a comparison of both representations.');
    if(!['kmeans','pam','hierarchical','hdbscan','gmm'].includes(o.algorithm))throw Error('Choose k-means, PAM, hierarchical clustering, HDBSCAN or a Gaussian mixture.');
    if(!['ward','average'].includes(o.linkage))throw Error('Choose Ward or average linkage.');
    for (const [key,min,max] of [['components',2,50],['k',o.algorithm==='gmm'?1:2,12],['neighbors',2,100],['seed',0,4294967295],['umapSeed',0,4294967295]]) integer(o[key],key,min,max);
    if(o.algorithm==='gmm')o.gmm=G.options(o.gmm);
    if (!Number.isFinite(o.minDist) || o.minDist < 0 || o.minDist > 0.99) throw Error('UMAP minimum distance must be between 0 and 0.99.');
    if(o.algorithm==='hdbscan'){
      integer(o.hdbscan.minClusterSize,'minimum cluster size',2,600);integer(o.hdbscan.minSamples,'density neighbors',2,600);
      if(!['eom','leaf'].includes(o.hdbscan.selection))throw Error('Choose EOM or leaf cluster selection.');
    }
    const s=o.stability;
    if (typeof s.enabled !== 'boolean') throw Error('Choose whether to assess cluster stability.');
    if (s.enabled) {
      if (!['meeting','affiliation'].includes(s.unit)) throw Error('Choose meetings or recorded speaker affiliations as the resampling unit.');
      integer(s.replicates,'stability repetitions',10,100);
      integer(s.seed,'stability seed',0,4294967295);
      if (!Number.isFinite(s.fraction) || s.fraction < 0.5 || s.fraction > 0.9) throw Error('Retain between 50% and 90% of groups in each stability sample.');
    }
    return o;
  }
  const api={DEFAULTS,STABILITY,HDBSCAN,options};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNClusterOptions=api;
})(globalThis);
