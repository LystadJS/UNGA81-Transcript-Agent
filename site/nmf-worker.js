'use strict';
importScripts('numerics.js','meeting-scopes.js?v=1.2.0','mds-core.js?v=1.11.0','gmm-core.js?v=1.11.0','cluster-options.js?v=1.11.0','nmf-options.js?v=1.11.0',
  'passage-selection.js?v=1.11.0','analysis-core.js?v=1.11.0','lsa-core.js?v=1.11.0','representation-metrics.js?v=1.11.0',
  'cluster-algorithms.js?v=1.11.0','hdbscan-core.js?v=1.11.0','cluster-core.js?v=1.11.0','cluster-stability.js?v=1.11.0','nmf-core.js?v=1.11.0');
onmessage=async({data})=>{
  try{postMessage({type:'result',result:await UNNMF.run(data.records,data.vectors,data.options,async message=>postMessage({type:'progress',message}))});}
  catch(error){postMessage({type:'error',message:error.message});}
};
