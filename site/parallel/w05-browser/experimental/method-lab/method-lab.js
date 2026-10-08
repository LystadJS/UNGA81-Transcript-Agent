/* W5 browser research prototype. All source values use textContent, never HTML injection. */
(function() {
  'use strict';
  const C=window.UNMethodLabContracts;
  const A=window.UNMethodLabAdapters;
  const controller=new window.UNMethodLabTasks.TaskController('worker.js');
  const el=id=>document.getElementById(id);
  const state={views:[],kind:null,archive_text:null,comparison:null,resource:null};
  let epoch=0;
  const bytes=n=>Number.isFinite(n) ? (n/1024/1024).toFixed(2)+' MiB' : 'unavailable';
  const integer=n=>Number.isFinite(n) ? String(n) : 'unavailable';
  function node(tag,text,className) {
    const e=document.createElement(tag);
    if(text!==undefined && text!==null)e.textContent=String(text);
    if(className)e.className=className;
    return e;
  }
  function append(parent,...children) {
    for(const child of children)parent.append(child);
    return parent;
  }
  function empty(parent) { parent.replaceChildren(); }
  function status(message,error=false) {
    el('status').textContent=message;
    el('status').classList.toggle('error',error);
  }
  function busy(value) {
    el('cancel').disabled=!value;
    el('open').disabled=value;
    el('execute').disabled=value;
    el('example').disabled=value;
    el('export').disabled=value || !state.views.length;
  }
  function resource(data) {
    if(!data)return;
    state.resource=data.resource;
    const memory=data.resource?.used_heap_bytes === null ||
      !Number.isFinite(data.resource?.used_heap_bytes) ?
      'Heap: not exposed by this browser' : 'Heap: '+bytes(data.resource.used_heap_bytes);
    const elapsed=Number.isFinite(data.elapsed_ms) ? 'Elapsed: '+(data.elapsed_ms/1000).toFixed(2)+' s' : null;
    const input=Number.isFinite(data.supplied_bytes) ? 'Imported data: '+bytes(data.supplied_bytes) : null;
    const retained=Number.isFinite(data.retained_observations) ?
      'Retained source observations: '+integer(data.retained_observations) : null;
    el('resources').textContent=[elapsed,input,retained,memory].filter(Boolean).join(' · ');
  }
  function invalidate() {
    epoch++;
    controller.cancel();
    state.views=[];state.kind=null;state.archive_text=null;state.comparison=null;state.resource=null;
    el('results').hidden=true;
    empty(el('resources'));
    empty(el('observations'));
    empty(el('inspection'));
    busy(false);
  }
  function confirmDevelopment() {
    if (!el('authorize').checked) throw new Error('Confirm that no reserved/holdout transcripts are included.');
    return 'development';
  }
  async function read(file,limit,label) {
    if(!file)throw new Error('Select '+label+'.');
    if(file.size>limit)throw new Error(label+' exceeds the existing '+bytes(limit)+' cap; no sampling performed.');
    return await file.text();
  }
  function modelOptions(select) {
    empty(select);
    state.views.forEach((view,index)=>{
      for(const model of view.models) {
        const option=node('option', 'Run '+(index+1)+' · '+model.label+' ['+model.method+']');
        option.value=index+'|'+model.id;
        select.append(option);
      }
    });
  }
  function chosen(select) {
    const value=select.value, divider=value.indexOf('|');
    const view=state.views[Number(value.slice(0,divider))];
    const model=view?.models.find(m=>m.id===value.slice(divider+1));
    if(!view || !model) throw new Error('Select a valid model.');
    return {view,model};
  }
  function detail(dl,name,value) {
    dl.append(node('dt',name),node('dd',value===null||value===undefined?'not recorded':value));
  }
  function renderModel(id,selected) {
    const target=el(id),model=selected.model,view=selected.view;
    empty(target);
    target.append(node('h3',model.label));
    const dl=node('dl');
    detail(dl,'Method',model.method);
    detail(dl,'Family',model.family);
    detail(dl,'Representation',model.representation+' · '+model.representation_version);
    detail(dl,'Execution',model.execution.replaceAll('_',' '));
    detail(dl,'Cohort unit',model.unit || view.source.unit);
    detail(dl,'Source hash',view.source.hash || 'missing — see upstream');
    detail(dl,'Source hash basis',view.source.hash_basis);
    detail(dl,'Selection hash',view.source.selection_hash || 'not provided');
    for(const key of ['eligible','assigned','unassigned','not_fitted','excluded']) {
      if(model.coverage && model.coverage[key] !== undefined) detail(dl,key.replaceAll('_',' '),integer(model.coverage[key]));
    }
    if(model.coverage?.attempted_fits !== undefined) {
      detail(dl,'Fit attempts',integer(model.coverage.attempted_fits));
      detail(dl,'Successful / failed',integer(model.coverage.successful_fits)+' / '+integer(model.coverage.failed_fits));
    }
    target.append(dl);
    const disclosure=node('details');
    disclosure.append(node('summary','Model diagnostics and limitations'));
    disclosure.append(node('pre',JSON.stringify({diagnostics:model.diagnostics, limitations:view.limitations},null,2)));
    target.append(disclosure);
  }
  function latestRow(selected,id) {
    return selected.model.rows.find(r=>r.observation_id===id);
  }
  function modelValue(record) {
    if(!record)return 'not in this model population';
    if(record.status==='mixture')return 'mixture shares (no exclusive cluster)';
    if(record.status==='assigned')return 'cluster '+record.cluster;
    if(record.status==='unassigned')return 'unassigned (0)';
    return record.status.replaceAll('_',' ');
  }
  function sourceLink(record) {
    if(!record?.source_url)return node('span','No verified URL recorded');
    const link=node('a','Open recorded source (new tab)');
    link.href=record.source_url;
    link.target='_blank';
    link.rel='noopener noreferrer';
    return link;
  }
  function inspect(selected,id,other,comparable) {
    const target=el('inspection');
    empty(target);
    const source=selected.view.observations.find(o=>o.id===id);
    if(!source)return;
    target.append(node('h3','Source observation · '+(source.original_id || source.id)));
    const dl=node('dl');
    detail(dl,'Text SHA-256',source.text_sha256);
    detail(dl,'Affiliation label (not verified speaker)',source.country);
    detail(dl,'Date',source.date);
    detail(dl,'Meeting',source.meeting_id);
    detail(dl,'Parent',source.parent_id);
    detail(dl,'Availability',source.source_status);
    detail(dl,'Missing / exclusion',JSON.stringify({missing:source.missing_reason, excluded:source.exclusion_reasons}));
    detail(dl,'Unicode source span',source.start===null?'not recorded':source.start+'–'+source.end);
    target.append(dl,sourceLink(source));
    const rows=[['Model A',selected.model,latestRow(selected,id)]];
    if(comparable)rows.push(['Model B',other.model,latestRow(other,id)]);
    for(const [label,model,row] of rows) {
      target.append(node('h3',label+' · '+model.label));
      if(!row) {target.append(node('p','No source-matched model result.'));continue;}
      target.append(node('p',modelValue(row)+(row.reason?' · '+row.reason:'')));
      if(Array.isArray(row.memberships)) {
        const kind=row.membership_kind==='nmf_share'?'Normalized NMF component shares':
          row.membership_kind==='gmm_responsibility'?'GMM model responsibilities':'Membership values';
        target.append(node('p',kind+' (not government stance or calibrated probabilities):'));
        target.append(node('pre',JSON.stringify(row.memberships,null,2)));
      }
      if(Number.isFinite(row.membership_strength)) {
        target.append(node('p','Model-specific assignment strength: '+row.membership_strength));
      }
      if(Array.isArray(row.score_coordinates)) {
        target.append(node('p','Retained score coordinates (not map distances): '+JSON.stringify(row.score_coordinates)));
      }
    }
  }
  function renderObservations(left,right,comparison) {
    const target=el('observations');
    empty(target);
    const table=node('table');
    const thead=node('thead'),head=node('tr');
    for(const name of ['Source ID','Date','Recorded affiliation','Model A','Model B','Inspect'])head.append(node('th',name));
    thead.append(head);table.append(thead);
    const tbody=node('tbody');
    const ids=new Set(left.model.rows.map(r=>r.observation_id));
    const records=left.view.observations.filter(o=>ids.has(o.id));
    for (const o of records) {
      const row=node('tr'),a=latestRow(left,o.id),b=comparison.identical_population?latestRow(right,o.id):null;
      row.append(node('td',o.original_id || o.id),node('td',o.date||'not recorded'),
        node('td',o.country||'unverified'),node('td',modelValue(a)),
        node('td',comparison.identical_population?modelValue(b):'comparison blocked'));
      const cell=node('td'),button=node('button','Inspect');
      button.type='button';
      button.addEventListener('click',()=>inspect(left,o.id,right,comparison.identical_population));
      cell.append(button);row.append(cell);tbody.append(row);
    }
    table.append(tbody);target.append(table);
    const count=node('p','Showing all '+records.length+' observations for Model A. No analytical rows sampled.','note');
    target.append(count);
  }
  function render() {
    const left=chosen(el('left')),right=chosen(el('right'));
    renderModel('left-result',left);
    renderModel('right-result',right);
    const comparison=A.compareViews(left.view,right.view,left.model.id,right.model.id);
    state.comparison=comparison;
    el('comparison').textContent=(comparison.identical_population?
      'Same source population ('+comparison.paired_count+' observations). ':
      'Incompatible source populations. ')+comparison.reason;
    renderObservations(left,right,comparison);
    empty(el('inspection'));
  }
  function adopt(result) {
    if(!Array.isArray(result.views)||!result.views.length)throw new Error('Worker did not provide a retained model.');
    state.views=result.views;state.kind=result.kind;
    state.archive_text=result.archive_text || null;
    modelOptions(el('left'));modelOptions(el('right'));
    el('right').selectedIndex=Math.min(1,el('right').options.length-1);
    el('results').hidden=false;
    render();
    resource(result);
    status('Validated '+state.views.length+' source-bound run(s). '+
      (result.runtime_warning || 'Inspect fit coverage and exclusions before interpreting patterns.'));
    busy(false);
  }
  async function task(action, fields, expectedEpoch=epoch) {
    if(expectedEpoch !== epoch)return;
    busy(true);
    status('Validating source identity and input versions…');
    try {
      const result=await controller.start(action,fields,event=>{
        status(event.message || 'Working: '+event.phase);
        resource(event);
      });
      if(expectedEpoch !== epoch)return;
      if(result.kind==='export') {
        saveFile('method-lab-saved-run.json',result.text);
        resource(result);
        status('Source-bound method-lab archive exported. No refit was performed.');
      } else adopt(result);
    } catch(error) {
      if(expectedEpoch !== epoch)return;
      status(error.message,true);
    }
    if(expectedEpoch === epoch)busy(false);
  }
  function saveFile(name,text) {
    const blob=new Blob([text],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const link=document.createElement('a');
    link.href=url;link.download=name;
    document.body.append(link);
    link.click();link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function wire() {
    for (const {name,id,availability,detail:description} of A.METHODS) {
      const card=node('article',null,'capability');
      append(card,node('strong',name),node('span',availability.replaceAll('_',' ')),node('p',description));
      el('capabilities').append(card);
    }
    for(const id of ['archive','corpus','plan','authorize']){
      el(id).addEventListener('change',()=>{
        invalidate();
        status('Input changed. Previous run cleared; reload or execute to avoid stale exports.');
      });
    }
    for(const id of ['left','right'])el(id).addEventListener('change',()=> {
      try{render();}catch(error){status(error.message,true);}
    });
    el('open').addEventListener('click',async()=>{
      invalidate();
      const ticket=epoch;
      try {
        const text=await read(el('archive').files?.[0],C.MAX_ARCHIVE_BYTES,'saved run');
        if(ticket!==epoch)return;
        const header=JSON.parse(text.replace(/^\uFEFF/,''));
        const authorization=header.schema==='un.latent-saved-run.v1'?confirmDevelopment():null;
        await task('open',{text,authorization},ticket);
      }catch(error){if(ticket===epoch)status(error.message,true);}
    });
    el('execute').addEventListener('click',async()=>{
      invalidate();
      const ticket=epoch;
      try {
        const authorization=confirmDevelopment();
        const source=await read(el('corpus').files?.[0],40*1024*1024,'local source');
        const planText=await read(el('plan').files?.[0],1024*1024,'latent method plan');
        if(ticket!==epoch)return;
        const parsed=JSON.parse(source.replace(/^\uFEFF/,''));
        const kind=parsed.schema==='un.browser.corpus.v1'?'corpus':
          parsed.schema==='un.reviewed-speech-analysis.v1'?'reviewed':null;
        if(!kind)throw new Error('Run requires a current browser corpus or validated reviewed bundle.');
        await task('run_local',{authorization,payload:{kind,text:source},plan:JSON.parse(planText)},ticket);
      }catch(error){if(ticket===epoch)status(error.message,true);}
    });
    el('example').addEventListener('click',async()=>{
      invalidate();
      const ticket=epoch;
      try{
        const response=await fetch('./fixtures/synthetic-contract.json',{cache:'no-store'});
        if(!response.ok)throw new Error('Synthetic fixture unavailable.');
        const text=await response.text();
        if(ticket!==epoch)return;
        await task('open',{text},ticket);
      }catch(error){if(ticket===epoch)status(error.message,true);}
    });
    el('cancel').addEventListener('click',()=>{
      controller.cancel();
      invalidate();
      status('Cancelled; no partial result or saved run was retained.');
    });
    el('export').addEventListener('click',async()=>{
      if(!state.views.length) return;
      if(state.kind==='legacy') {
        if(!state.archive_text) {status('Legacy archive is unavailable; rerun or restore the source-bound original.',true);return;}
        saveFile('latent-saved-run.json',state.archive_text);
        status('Original legacy archive exported. WARNING: this file contains the original locally supplied transcript input.');
        return;
      }
      await task('save_parallel',{envelopes:state.views.map(v=>v.envelope)});
    });
  }
  wire();
})();
