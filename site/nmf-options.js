/* Settings shared by the form, worker and reproducible local audits. */
(function(root){
  'use strict';
  const DEFAULTS=Object.freeze({components:6,starts:3,maxIterations:300,tolerance:0.0001,seed:42,
    stability:{enabled:false,unit:'meeting',replicates:30,fraction:0.8,seed:31415}});
  function options(value={}){
    const o={...DEFAULTS,...value,stability:{...DEFAULTS.stability,...value.stability}};
    const integer=(v,min,max,key)=>{if(!Number.isInteger(v)||v<min||v>max)throw Error(`Invalid NMF ${key}: use ${min}–${max}.`);};
    integer(o.components,2,12,'components');integer(o.starts,1,5,'starts');integer(o.maxIterations,50,1000,'iteration limit');integer(o.seed,0,4294967295,'seed');
    if(!Number.isFinite(o.tolerance)||o.tolerance<0.000001||o.tolerance>0.01)throw Error('NMF tolerance must be 0.000001–0.01.');
    const s=o.stability;if(typeof s.enabled!=='boolean')throw Error('Choose whether to assess NMF stability.');
    if(s.enabled){
      if(!['meeting','affiliation'].includes(s.unit))throw Error('Choose meeting or recorded affiliation resampling.');
      integer(s.replicates,10,100,'repetitions');integer(s.seed,0,4294967295,'resampling seed');
      if(!Number.isFinite(s.fraction)||s.fraction<0.5||s.fraction>0.9)throw Error('Retain 50%–90% of groups.');
    }
    return o;
  }
  const api={DEFAULTS,options};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNNMFOptions=api;
})(globalThis);
