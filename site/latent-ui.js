/* Local-only comparison controls. Changing inputs invalidates every completed export. */
(function(){
  'use strict';
  const $=id=>document.getElementById(id),L=UNLatent,V=UNLatentView;
  let rows=[],payload=null,current=null,archiveA=null,task=null,ticket=0;
  const split=value=>value.split(',').map(s=>s.trim()).filter(Boolean);
  const numbers=(id,integer=true)=>{const values=split($(id).value).map(Number);if(!values.length||values.some(v=>!Number.isFinite(v)||(integer&&!Number.isInteger(v))))throw Error('Use comma-separated '+(integer?'integers':'numbers')+' for '+id+'.');return [...new Set(values)];};
  const read=async(file,limit=40*1024*1024)=>{if(!file)throw Error('Choose a file.');if(file.size>limit)throw Error('File exceeds this import limit.');return new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(await file.arrayBuffer());};
  const status=message=>{$('status').textContent=message;};
  function busy(value){$('run').disabled=value;$('cancel').disabled=!value;}
  function stop(message='Cancelled. No partial comparison was released.'){
    if(task){const t=task;task=null;t.worker.terminate();t.reject(Error(message));}busy(false);
  }
  function invalidate(){ticket++;stop('Settings changed; active calculation cancelled.');current=null;archiveA=null;$('results').hidden=true;status('Settings changed. Run or reopen a saved comparison before exporting.');}
  function worker(data){
    stop();busy(true);
    return new Promise((resolve,reject)=>{const w=new Worker('latent-worker.js?v=1.1.0');task={worker:w,reject};
      const finish=()=>{w.terminate();if(task?.worker===w)task=null;busy(false);};
      w.onmessage=({data:d})=>{if(d.type==='progress'){status(d.message);return;}finish();if(d.type==='error')reject(Error(d.message));else resolve(d);};
      w.onerror=event=>{finish();reject(Error(event.message||'The comparison worker could not run.'));};w.postMessage(data);
    });
  }
  const guarded=fn=>async()=>{try{await fn();}catch(error){status('Could not complete: '+error.message);}};
  function base(){const topic=$('topic').value.trim();return {topic,phrases:topic?[topic,...split($('phrases').value)]:[],exclude:topic?split($('exclude').value):[],start:$('start').value,end:$('end').value,scope:$('scope').value,region:$('region').value};}
  function plan(){return {schema:'un.latent-plan.v1',base:base(),compare_parents:$('parents').checked,stability:{enabled:$('stability').checked,unit:$('groupUnit').value,replicates:Number($('replicates').value),fraction:Number($('fraction').value),seed:Number($('groupSeed').value)},settings:JSON.parse(JSON.stringify(rows))};}
  function renderRows(){
    $('planRows').replaceChildren();rows.forEach((row,i)=>{const tr=document.createElement('tr');for(const text of [row.label,JSON.stringify(row.options)]){const td=document.createElement('td');td.textContent=text;tr.append(td);}const td=document.createElement('td'),button=document.createElement('button');button.type='button';button.textContent='Remove '+(i+1);button.addEventListener('click',()=>{invalidate();rows.splice(i,1);renderRows();});td.append(button);tr.append(td);$('planRows').append(tr);});
    $('planCount').textContent=rows.length+' settings · '+rows.length*($('parents').checked?2:1)+' full fits, plus any selected group refits. Maximum 12 settings.';
  }
  function addSettings(){
    const algorithm=$('algorithm').value,representations=$('representation').value==='both'?['pca','lsa']:[$('representation').value];
    const additions=[];
    if(algorithm==='nmf')for(const components of numbers('clusterCounts'))additions.push({label:'NMF · rank '+components,method:'nmf',options:{components,seed:Number($('fitSeed').value)}});
    else{
      const dims=numbers('dimensions'),counts=algorithm==='hdbscan'?[4]:numbers('clusterCounts'),neighbors=numbers('neighbors'),seeds=numbers('displaySeeds');
      const covariances=algorithm==='gmm'?($('covariance').value==='both'?['diag','spherical']:[$('covariance').value==='diagonal'?'diag':$('covariance').value]):['diag'];
      const floors=algorithm==='gmm'?numbers('regularization',false):[0.0001],sizes=algorithm==='hdbscan'?numbers('minSizes'):[15],density=algorithm==='hdbscan'?numbers('densityNeighbors'):[5];
      for(const representation of representations)for(const components of dims)for(const k of counts)for(const nn of neighbors)for(const umapSeed of seeds)for(const covariance of covariances)for(const regularization of floors)for(const minClusterSize of sizes)for(const minSamples of density){
        const options={representation,algorithm:['ward','average'].includes(algorithm)?'hierarchical':algorithm,components,k,seed:Number($('fitSeed').value),neighbors:nn,umapSeed,minDist:Number($('minDist').value),mds:{enabled:$('mds').checked}};
        if(['ward','average'].includes(algorithm))options.linkage=algorithm;
        if(algorithm==='hdbscan')options.hdbscan={minClusterSize,minSamples,selection:$('densitySelection').value};
        if(algorithm==='gmm')options.gmm={covariance,regularization};
        const label=representation.toUpperCase()+' · '+algorithm+' · d='+components+(algorithm==='hdbscan'?' · min='+minClusterSize+'/'+minSamples:' · k='+k)+(algorithm==='gmm'?' · '+covariance+' '+regularization:'')+' · U='+nn+'/'+umapSeed;
        additions.push({label,method:'clusters',options});if(rows.length+additions.length>12)throw Error('This grid exceeds 12 settings. Reduce a list; no settings were added.');
      }
    }
    if(rows.length+additions.length>12)throw Error('Maximum 12 settings.');
    const identities=new Set(rows.map(r=>L.stable({method:r.method,options:r.options})));
    for(const row of additions){const key=L.stable({method:row.method,options:row.options});if(identities.has(key))throw Error('That setting is already present.');identities.add(key);}
    invalidate();rows.push(...additions);renderRows();status('Settings added. Inspect the plan, then run.');
  }
  function setPlan(p){
    if(p.schema!=='un.latent-plan.v1'||!Array.isArray(p.settings)||p.settings.length>12||!p.base)throw Error('Invalid settings plan.');
    rows=JSON.parse(JSON.stringify(p.settings));
    for(const id of ['topic','start','end','scope','region'])$(id).value=p.base[id]??'';
    $('phrases').value=(p.base.phrases||[]).filter(v=>v!==p.base.topic).join(', ');$('exclude').value=(p.base.exclude||[]).join(', ');
    $('parents').checked=p.compare_parents===true;$('stability').checked=p.stability?.enabled===true;
    for(const [id,key,fallback] of [['groupUnit','unit','meeting'],['replicates','replicates',30],['fraction','fraction',0.8],['groupSeed','seed',31415]])$(id).value=p.stability?.[key]??fallback;
    renderRows();
  }
  function show(data,mode){
    current=data;$('output').innerHTML=V.html(data.result);$('resultMode').textContent=mode;$('results').hidden=false;$('saveRun').disabled=!data.archive_text;
    status('Complete. Inspect coverage, fit status, source examples and comparison denominators.');
  }
  function download(name,text,type='application/json'){
    const url=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
  }
  function requireResult(){if(!current)throw Error('Run or reopen a comparison before exporting.');return current;}
  UNMeetingScopes.OPTIONS.forEach(o=>{const option=document.createElement('option');option.value=o.value;option.textContent=o.label;$('scope').append(option);});
  fetch('countries.json').then(r=>r.json()).then(countries=>{const regions=[...new Set(countries.map(r=>r.region).filter(Boolean))];regions.forEach(region=>{const o=document.createElement('option');o.value=region;$('regions').append(o);});}).catch(()=>{});
  document.querySelectorAll('#inputs input,#inputs select,#settings input,#settings select').forEach(el=>{if(el.type!=='file')el.addEventListener('input',()=>{invalidate();renderRows();});});
  $('sourceFile').addEventListener('change',guarded(async()=>{
    invalidate();payload=null;$('sourceStatus').textContent='Validating selected file type…';const t=ticket,text=await read($('sourceFile').files[0]);if(t!==ticket)return;const source=L.parse(text);
    const kind=source.schema==='un.reviewed-speech-analysis.v1'?'reviewed':source.schema==='un.browser.corpus.v1'?'corpus':null;if(!kind)throw Error('Choose a collected corpus or reviewed analysis bundle.');
    payload={kind,text};$('policy').disabled=kind==='reviewed';$('parents').disabled=kind!=='reviewed';if(kind!=='reviewed')$('parents').checked=false;else $('policy').value='';
    $('sourceStatus').textContent='Selected '+$('sourceFile').files[0].name+' · '+kind+'. Source hashes and review lineage will be validated before fitting.';renderRows();
  }));
  $('reviewFile').addEventListener('change',invalidate);
  $('add').addEventListener('click',guarded(addSettings));
  $('clear').addEventListener('click',()=>{invalidate();rows=[];renderRows();});
  $('baseline').addEventListener('click',()=>{invalidate();rows=['pca','lsa'].map(representation=>({label:representation.toUpperCase()+' · k-means · d=20 · k=4',method:'clusters',options:{representation,algorithm:'kmeans',components:20,k:4,neighbors:15,umapSeed:42,seed:42}}));renderRows();});
  $('run').addEventListener('click',guarded(async()=>{
    if(!payload)throw Error('Select source evidence or reopen a saved run first.');
    current=null;archiveA=null;$('results').hidden=true;const t=++ticket,source={kind:payload.kind,text:payload.text};
    if($('policy').value){source.policy=$('policy').value;source.review_text=$('reviewFile').files[0]?await read($('reviewFile').files[0],4*1024*1024):payload.review_text;if(!source.review_text)throw Error('Choose the completed passage review.');}
    if(t!==ticket)return;const data=await worker({action:'run',payload:source,plan:plan()});if(t!==ticket)return;payload=source;archiveA=data.archive_text;show(data,'New comparison · no automatic method selection.');
  }));
  $('cancel').addEventListener('click',()=>{ticket++;stop();current=null;archiveA=null;$('results').hidden=true;status('Cancelled. No partial result or export was released.');});
  $('planFile').addEventListener('change',guarded(async()=>{invalidate();const t=ticket,text=await read($('planFile').files[0],1024*1024);if(t!==ticket)return;setPlan(L.parse(text));status('Plan opened. It will be validated against the current engines before fitting.');}));
  $('savePlan').addEventListener('click',guarded(async()=>{const p=plan();if(!p.settings.length)throw Error('Add a setting first.');const data=await worker({action:'validate_plan',plan:p});download('latent-plan.json',JSON.stringify(data.plan,null,2));status('Validated settings plan saved; it contains no source text.');}));
  $('savedA').addEventListener('change',guarded(async()=>{
    invalidate();payload=null;const t=ticket,text=await read($('savedA').files[0],L.LIMIT);if(t!==ticket)return;const data=await worker({action:'restore',text});if(t!==ticket)return;
    payload=data.payload;setPlan(data.result.plan);$('policy').value=payload.policy||'';$('policy').disabled=payload.kind==='reviewed';$('parents').disabled=payload.kind!=='reviewed';$('sourceStatus').textContent='Exact source restored from saved run A; no re-upload is required.';
    archiveA=text;show(data,'Archived snapshot · stored results and coordinates restored without refitting. Current renderer; saved numerical runtime is recorded below.');
  }));
  $('savedB').addEventListener('change',guarded(async()=>{
    if(!archiveA)throw Error('Run a comparison or open saved run A first.');current=null;$('results').hidden=true;const t=++ticket,text=await read($('savedB').files[0],L.LIMIT);if(t!==ticket)return;
    const data=await worker({action:'compare_saved',left:archiveA,right:text});if(t!==ticket)return;
    show(data,'Two archived runs · paired only on identical source populations. Keep the original A and B archives for replay; the exported comparison JSON is not a replay bundle.');
  }));
  $('saveRun').addEventListener('click',guarded(()=>{const d=requireResult();if(!d.archive_text)throw Error('Preserve the two original run archives separately.');download('latent-saved-run.json',d.archive_text);}));
  $('saveJSON').addEventListener('click',guarded(()=>download('latent-comparison.json',JSON.stringify(requireResult().result,null,2))));
  $('saveCSV').addEventListener('click',guarded(()=>download('latent-diagnostics.csv',V.csv(requireResult().result),'text/csv;charset=utf-8')));
  $('saveCoverage').addEventListener('click',guarded(()=>download('latent-coverage.csv',V.coverageCSV(requireResult().result),'text/csv;charset=utf-8')));
  $('saveWeights').addEventListener('click',guarded(()=>download('latent-weights.csv',V.weightsCSV(requireResult().result),'text/csv;charset=utf-8')));
  $('saveHTML').addEventListener('click',guarded(async()=>{const d=requireResult(),css=await fetch('latent.css').then(r=>{if(!r.ok)throw Error('Export stylesheet unavailable.');return r.text();});if(current!==d)throw Error('Result changed before export.');const content=V.html(d.result).replace(/<details>/g,'<details open>');download('latent-comparison.html','<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><title>Latent structure comparison</title><style>'+css+'</style></head><body><main><h1>Latent structure comparison</h1><p>Exploratory, source-linked output. No automatic substantive labels or publication release.</p>'+content+'</main></body></html>','text/html;charset=utf-8');}));
  renderRows();
})();
