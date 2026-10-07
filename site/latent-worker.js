'use strict';
importScripts('numerics.js','meeting-scopes.js','mds-core.js','gmm-core.js','cluster-options.js','nmf-options.js','passage-selection.js','passage-pilot-core.js','reviewed-units.js','analysis-core.js','lsa-core.js','representation-metrics.js','cluster-algorithms.js','hdbscan-core.js','cluster-core.js','cluster-stability.js','nmf-core.js','latent-core.js');
const modules=['numerics.js','meeting-scopes.js','mds-core.js','gmm-core.js','cluster-options.js','nmf-options.js','passage-selection.js','passage-pilot-core.js','reviewed-units.js','analysis-core.js','lsa-core.js','representation-metrics.js','cluster-algorithms.js','hdbscan-core.js','cluster-core.js','cluster-stability.js','nmf-core.js','latent-core.js','latent-worker.js'];
onmessage=async({data})=>{
  try{
    const progress=async message=>postMessage({type:'progress',message});
    if(data.action==='restore'){
      const restored=await UNLatent.restore(data.text,progress);
      postMessage({type:'result',...restored});
      return;
    }
    if(data.action!=='run')throw Error('Unknown comparison operation.');
    const hashes={};
    for(const file of modules){const response=await fetch(file,{cache:'no-store'});if(!response.ok)throw Error('Cannot record runtime source: '+file);hashes[file]=await UNLatent.hash(new Uint8Array(await response.arrayBuffer()));}
    const runtime={engine:UNLatent.VERSION,execution:'browser Worker',user_agent:navigator.userAgent,module_sha256:hashes};
    const result=await UNLatent.run(data.payload,data.plan,runtime,progress);
    postMessage({type:'result',result,payload:data.payload,archive_text:await UNLatent.pack(data.payload,result)});
  }catch(error){postMessage({type:'error',message:error.message});}
};
