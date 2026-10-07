'use strict';
importScripts('numerics.js','meeting-scopes.js','mds-core.js','gmm-core.js','cluster-options.js','nmf-options.js','passage-selection.js','passage-pilot-core.js','reviewed-units.js','analysis-core.js','lsa-core.js','representation-metrics.js','cluster-algorithms.js','hdbscan-core.js','cluster-core.js','cluster-stability.js','nmf-core.js','latent-core.js');
const modules=['numerics.js','meeting-scopes.js','mds-core.js','gmm-core.js','cluster-options.js','nmf-options.js','passage-selection.js','passage-pilot-core.js','reviewed-units.js','analysis-core.js','lsa-core.js','representation-metrics.js','cluster-algorithms.js','hdbscan-core.js','cluster-core.js','cluster-stability.js','nmf-core.js','latent-core.js','latent-worker.js','latent-view.js','latent-ui.js','latent.css'];
onmessage=async({data})=>{
  try{
    const progress=async message=>postMessage({type:'progress',message});
    if(data.action==='validate_plan'){postMessage({type:'result',plan:UNLatent.validatePlan(data.plan)});return;}
    if(data.action==='restore'){postMessage({type:'result',...await UNLatent.restore(data.text,progress)});return;}
    if(data.action==='compare_saved'){
      const a=await UNLatent.restore(data.left,progress),b=await UNLatent.restore(data.right,progress);
      const prefix=(entries,p)=>entries.map(e=>({...e,id:p+e.id,label:p+e.label,summary:{...e.summary,id:p+e.id,label:p+e.label}}));
      const left=prefix(a.result.entries,'A/'),right=prefix(b.result.entries,'B/'),pairs=[];
      for(const l of left)for(const r of right)if(l.unit===r.unit)pairs.push(UNLatent.paired(l,r));
      const result={schema:'un.latent-saved-comparison.v1',engine:UNLatent.VERSION,created_at:new Date().toISOString(),entries:[...left,...right],pairs,coverage:[],runtime:{left:a.result.runtime,right:b.result.runtime},source_hash:{left:a.result.source_hash,right:b.result.source_hash},selection_hash:{left:a.result.selection_hash,right:b.result.selection_hash},interpretation:'Two stored runs compared without refitting. Like-for-like metrics require identical source IDs, order and text hashes. Settings agreement is not substantive validation.',weighting:'Each archived fit retains its original weighting and coverage. Original archives are required for exact replay.'};
      postMessage({type:'result',result});return;
    }
    if(data.action!=='run')throw Error('Unknown comparison operation.');
    const hashes={};
    for(const file of modules){const response=await fetch(file,{cache:'no-store'});if(!response.ok)throw Error('Cannot record runtime source: '+file);hashes[file]=await UNLatent.hash(new Uint8Array(await response.arrayBuffer()));}
    const runtime={engine:UNLatent.VERSION,execution:'browser Worker',user_agent:navigator.userAgent,module_sha256:hashes};
    const result=await UNLatent.run(data.payload,data.plan,runtime,progress);
    postMessage({type:'result',result,payload:data.payload,archive_text:await UNLatent.pack(data.payload,result)});
  }catch(error){postMessage({type:'error',message:error.message});}
};
