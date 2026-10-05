/* Shared, lightweight validation for the form, worker and Node entry points. */
(function(root) {
  'use strict';
  const STABILITY = Object.freeze({enabled:false, unit:'meeting', replicates:30, fraction:0.8, seed:31415});
  const DEFAULTS = Object.freeze({representation:'pca', components:20, k:4, neighbors:15, minDist:0.1, seed:42, umapSeed:42, stability:STABILITY});
  function integer(value, key, min, max) {
    if (!Number.isInteger(value) || value < min || value > max) {
      throw Error(`Invalid clustering setting: ${key} (${min}–${max}).`);
    }
  }
  function options(value = {}) {
    const o = {...DEFAULTS, ...value, stability:{...STABILITY, ...value.stability}};
    if(!['pca','lsa','compare'].includes(o.representation))throw Error('Choose PCA, LSA or a comparison of both representations.');
    for (const [key,min,max] of [['components',2,50],['k',2,12],['neighbors',2,100],['seed',0,4294967295],['umapSeed',0,4294967295]]) integer(o[key],key,min,max);
    if (!Number.isFinite(o.minDist) || o.minDist < 0 || o.minDist > 0.99) throw Error('UMAP minimum distance must be between 0 and 0.99.');
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
  const api={DEFAULTS,STABILITY,options};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNClusterOptions=api;
})(globalThis);
