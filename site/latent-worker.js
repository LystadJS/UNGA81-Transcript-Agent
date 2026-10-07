'use strict';
importScripts(...['numerics.js','meeting-scopes.js','mds-core.js','gmm-core.js','cluster-options.js','nmf-options.js','passage-selection.js','passage-pilot-core.js','reviewed-units.js','analysis-core.js','lsa-core.js','representation-metrics.js','cluster-algorithms.js','hdbscan-core.js','cluster-core.js','cluster-stability.js','nmf-core.js','latent-core.js'].map(file=>file+'?v=1.1.0'));
const modules=['numerics.js','meeting-scopes.js','mds-core.js','gmm-core.js','cluster-options.js','nmf-options.js','passage-selection.js','passage-pilot-core.js','reviewed-units.js','analysis-core.js','lsa-core.js','representation-metrics.js','cluster-algorithms.js','hdbscan-core.js','cluster-core.js','cluster-stability.js','nmf-core.js','latent-core.js','latent-worker.js','latent-view.js','latent-ui.js','latent.css'];
onmessage=async({data})=>{
  try{
    const progress=async message=>postMessage({type:'progress',message});
    if(data.action==='validate_plan'){postMessage({type:'result',plan:UNLatent.validatePlan(data.plan)});return;}
    if(data.action==='restore'){postMessage({type:'result',...await UNLatent.restore(data.text,progress)});return;}
    if(data.action==='compare_saved'){
      const a=await UNLatent.restore(data.left,progress),b=await UNLatent.restore(data.right,progress);
      const result=await UNLatent.compareSaved(a,b);
      postMessage({type:'result',result});return;
    }
    if(data.action!=='run')throw Error('Unknown comparison operation.');
    const hashes={};
    for(const file of modules){const response=await fetch(file+'?v=1.1.0',{cache:'no-store'});if(!response.ok)throw Error('Cannot record runtime source: '+file);hashes[file]=await UNLatent.hash(new Uint8Array(await response.arrayBuffer()));}
    const runtime={engine:UNLatent.VERSION,execution:'browser Worker',user_agent:navigator.userAgent,module_sha256:hashes};
    const result=await UNLatent.run(data.payload,data.plan,runtime,progress);
    postMessage({type:'result',result,payload:data.payload,archive_text:await UNLatent.pack(data.payload,result)});
  }catch(error){postMessage({type:'error',message:error.message});}
};
