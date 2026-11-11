/* Public archive reader. No credentials, inference, ingestion, or private inputs. */
(() => {
  'use strict';
  const MAX_MANIFEST = 1024 * 1024, MAX_PART = 8 * 1024 * 1024, MAX_TOTAL = 64 * 1024 * 1024;
  const PAGE_SIZE = 100, MAX_MEETINGS = 100000;
  const $ = id => document.getElementById(id);
  const state = {meetings: [], manifest: null, url: null, visible: PAGE_SIZE};
  const labels = {strongly_oppose:'Strongly oppose',oppose:'Oppose',neutral:'Neutral',support:'Support',strongly_support:'Strongly support',not_discussed:'Not discussed',no_expressed_position:'No expressed position',insufficient_evidence:'Insufficient evidence',unresolved_attribution:'Unresolved attribution',conditional:'Conditional position',mixed:'Conflicting positions',conflicting:'Conflicting positions',unclear:'Unclear',withheld:'Estimate withheld',not_evaluated:'Not evaluated'};
  const text = value => typeof value === 'string' ? value : '';
  const friendly = value => labels[value] || text(value).replace(/_/g, ' ') || 'Unknown';
  const node = (name, value, cls) => {const el = document.createElement(name); if(value !== undefined)el.textContent = String(value);if(cls)el.className = cls;return el;};
  const modelAccepted = () => state.manifest && ['accepted','evaluated_accepted'].includes(state.manifest.model_status);
  function safeURL(value, base, asset = false) {
    const url = new URL(value, base);
    if(url.username || url.password || url.hash || !(url.protocol === 'https:' || (url.origin === location.origin && url.protocol === 'http:')))throw Error('Unsupported archive URL.');
    if(asset && (url.origin !== new URL(base).origin || !url.pathname.startsWith(new URL('.',base).pathname)))throw Error('Archive file is outside its published snapshot directory.');
    return url.href;
  }
  function sourceLink(url, label) {
    try {
      const u = new URL(url);
      if(u.protocol !== 'https:' || u.hostname !== 'transcripts.un.org' || u.username || u.password)return node('span', label);
      const a = node('a',label);a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';return a;
    } catch {return node('span',label);}
  }
  async function bytes(url, limit) {
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(),30000);
    try {
      const response = await fetch(url,{credentials:'omit',referrerPolicy:'no-referrer',cache:'no-cache',signal:controller.signal});
      if(!response.ok)throw Error('Archive request failed ('+response.status+').');
      const size = Number(response.headers.get('content-length'));
      if(size > limit)throw Error('Archive file exceeds the download limit.');
      const reader=response.body.getReader(),chunks=[];let length=0;
      while(true){const {value,done}=await reader.read();if(done)break;length+=value.byteLength;if(length>limit){await reader.cancel();throw Error('Archive file exceeds the download limit.');}chunks.push(value);}
      const result=new Uint8Array(length);let offset=0;for(const c of chunks){result.set(c,offset);offset+=c.length;}return result;
    } finally {clearTimeout(timer);}
  }
  const decode = data => JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(data));
  function descriptor(value,limit=MAX_PART) {
    if(!value || typeof value.path !== 'string' || !value.path || !Number.isSafeInteger(value.bytes) || value.bytes<0 || value.bytes>limit || !/^[a-f0-9]{64}$/.test(value.sha256))throw Error('Invalid archive file descriptor.');
    safeURL(value.path,state.url,true);return value;
  }
  async function verified(value,limit=MAX_PART) {
    descriptor(value,limit);
    const data=await bytes(safeURL(value.path,state.url,true),limit);
    if(data.length!==value.bytes)throw Error('Archive file byte count does not match its manifest.');
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data)),x=>x.toString(16).padStart(2,'0')).join('');
    if(digest!==value.sha256)throw Error('Archive file integrity check failed.');
    return data;
  }
  function save(data,name,mime) {
    const url=URL.createObjectURL(new Blob([data],{type:mime})),a=node('a');a.href=url;a.download=name.replace(/[^a-zA-Z0-9._-]/g,'_');document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function selectedMeetings() {
    const query=$('archiveSearch').value.trim().toLocaleLowerCase(),body=$('archiveBody').value,start=$('archiveStart').value,end=$('archiveEnd').value;
    if(start && end && start>end)return [];
    return state.meetings.filter(m=>(!body || m.body===body)&&(!start || (m.date && m.date>=start))&&(!end || (m.date && m.date<=end))&&(!query || [m.title,m.meeting_id,...m.issues.map(i=>typeof i==='string'?i: i.label||i.proposition||i.issue_id)].join(' ').toLocaleLowerCase().includes(query)));
  }
  function tableRow(cells){const tr=node('tr');for(const content of cells){const td=node('td');td.append(content instanceof Node?content:document.createTextNode(String(content)));tr.append(td);}return tr;}
  function render() {
    const selected=selectedMeetings();$('meetingRows').replaceChildren();$('positionRows').replaceChildren();
    for(const m of selected.slice(0,state.visible))$('meetingRows').append(tableRow([m.date||'Date unknown',sourceLink(m.source_url,m.title||m.meeting_id),m.body||'Not recorded',friendly(m.status),m.segments]));
    const invalid=$('archiveStart').value && $('archiveEnd').value && $('archiveStart').value>$('archiveEnd').value;
    $('filterStatus').textContent=invalid?'Choose a start date on or before the end date.':`${selected.length.toLocaleString()} meetings match. Showing ${Math.min(state.visible,selected.length).toLocaleString()}.`;
    $('moreMeetings').hidden=state.visible>=selected.length;$('exportSelection').disabled=!selected.length;
    const topics=new Map();
    for(const m of selected){const included=new Set();for(const issue of m.issues){const label=typeof issue==='string'?issue:text(issue.label||issue.proposition||issue.issue_id),kind=typeof issue==='string'?'recorded_issue':text(issue.kind)||'recorded_issue',key=label+'|'+kind;if(!label||included.has(key))continue;included.add(key);const old=topics.get(key)||{label,kind,count:0};old.count++;topics.set(key,old);}}
    $('issueList').replaceChildren();for(const topic of [...topics.values()].sort((a,b)=>b.count-a.count||a.label.localeCompare(b.label)).slice(0,100)){$('issueList').append(node('li',`${topic.label} — ${topic.count} ${topic.count===1?'meeting':'meetings'} · ${friendly(topic.kind)}`));}
    $('issueStatus').textContent=topics.size?`${topics.size} distinct issue entries appear in this selection.${topics.size>100?' Showing the first 100 by meeting coverage.':''}`:'No source-linked issue metadata is available for this selection.';
    if(!modelAccepted()){$('positionStatus').textContent='No evaluated stance estimates are available for this snapshot. Missing predictions do not imply neutral positions.';return;}
    let count=0;const seen=new Set();
    for(const m of selected)for(const p of m.positions){
      const key=[m.meeting_id,p.country,p.group_name,p.issue_id,p.label,p.status].join('|');if(seen.has(key))continue;seen.add(key);count++;
      if(count>500)continue;
      const status=['conditional','mixed','conflicting','unresolved_attribution','insufficient_evidence','no_expressed_position','unclear','withheld'].includes(p.status)?p.status:(p.label||p.stance);
      const estimate=node('span',friendly(status));if(p.condition)estimate.append(node('span',p.condition,'archive-tag'));
      const who=p.capacity==='collective'?(p.group_name||'Recorded collective group'):(p.country||'Attribution unresolved');
      $('positionRows').append(tableRow([m.date||'Date unknown',who,p.proposition||p.issue_label||p.issue||p.issue_id||'Unspecified proposition',estimate,sourceLink(p.source_url||m.source_url,'Open source')]));
    }
    $('positionStatus').textContent=count?`${count.toLocaleString()} distinct dated estimates or gaps. ${count>500?'Showing the first 500; narrow the meeting filters to inspect more.':''}`:'No eligible stance estimates are available for the selected meetings.';
  }
  function displayManifest() {
    const m=state.manifest,stamp=new Date(m.generated_at),age=(Date.now()-stamp.getTime())/86400000;
    $('archiveStats').hidden=false;$('lastUpdate').textContent=stamp.toLocaleString();$('meetingCount').textContent=state.meetings.length.toLocaleString();
    const counts={};for(const meeting of state.meetings)counts[meeting.status]=(counts[meeting.status]||0)+1;
    $('coverageSummary').textContent=Object.entries(counts).map(([k,v])=>`${v} ${friendly(k)}`).join('; ')||'No meetings in this snapshot';
    $('archiveStatus').textContent=m.status==='complete'?'The published collection is available.':`The published snapshot is ${friendly(m.status)}. Coverage gaps remain visible below.`;
    if(m.status!=='complete')$('archiveStatus').classList.add('warning');
    $('freshness').hidden=false;$('freshness').textContent=age>2?'This snapshot is more than two days old. Scheduled updates may be delayed; the last published collection remains available.':'Daily updates are scheduled. The time above is the actual publication time, not a guarantee of source completeness.';
    if(age>2)$('freshness').classList.add('notice','warning');
    $('modelStatus').textContent=modelAccepted()?'Evaluated model estimates are available for supported coverage. Inspect evidence and qualifications before using a result.':`Automatic stance estimates are withheld (${friendly(m.model_status)}). Collection and exploratory analysis remain separate from model acceptance.`;
    $('snapshotId').textContent=m.snapshot_id;$('verificationStatus').textContent='All loaded partitions match the published byte counts and SHA-256 hashes.';
    for(const body of [...new Set(state.meetings.map(x=>x.body).filter(Boolean))].sort()){const option=node('option',body);option.value=body;$('archiveBody').append(option);}
    $('filters').disabled=false;
    $('downloadList').replaceChildren();
    for(const item of m.downloads){const li=node('li'),button=node('button',item.name||item.path,'secondary');button.type='button';button.addEventListener('click',async()=>{button.disabled=true;$('downloadStatus').textContent='Verifying download…';try{const data=await verified(item,MAX_TOTAL);save(data,item.name||item.path.split('/').pop(),'application/octet-stream');$('downloadStatus').textContent='Verified download saved.';}catch(error){$('downloadStatus').textContent=error.message;}finally{button.disabled=false;}});li.append(button,node('span',`${Number(item.rows||0).toLocaleString()} rows · ${item.bytes.toLocaleString()} bytes`,'download-meta'));$('downloadList').append(li);}
    $('downloadStatus').textContent=m.downloads.length?'Select a dataset to verify and download.':'No published downloads are available.';render();
  }
  async function load() {
    try {
      const config=decode(await bytes('archive-config.json',16384));
      if(config.schema!=='un.archive-config.v1')throw Error('Unsupported archive configuration.');
      if(!config.manifest_url){$('archiveStatus').textContent='The shared archive has not been published yet. You can collect and analyze available meetings in the report builder while the maintained archive is being prepared.';return;}
      state.url=safeURL(config.manifest_url,location.href);
      const m=decode(await bytes(state.url,MAX_MANIFEST));
      if(m.schema!=='un.archive.v1'||!text(m.snapshot_id)||!text(m.status)||!text(m.model_status)||!Number.isFinite(Date.parse(m.generated_at))||!Array.isArray(m.partitions)||!Array.isArray(m.downloads)||m.partitions.length>512||m.downloads.length>200)throw Error('Unsupported or incomplete archive manifest.');
      if(Date.parse(m.generated_at)>Date.now()+300000)throw Error('Archive publication time is in the future.');
      for(const file of m.partitions)descriptor(file);for(const file of m.downloads)descriptor(file,MAX_TOTAL);
      if(m.partitions.reduce((sum,p)=>sum+p.bytes,0)>MAX_TOTAL)throw Error('Archive exceeds this browser’s metadata limit.');
      const meetings=[],ids=new Set();
      for(const part of m.partitions){const data=decode(await verified(part));if(!Array.isArray(data.meetings))throw Error('Invalid meeting partition.');for(const r of data.meetings){
        if(!r||!text(r.meeting_id)||ids.has(r.meeting_id)||(r.date!==null&&!/^\d{4}-\d{2}-\d{2}$/.test(r.date))||!Number.isSafeInteger(r.segments)||r.segments<0||!Array.isArray(r.positions)||!Array.isArray(r.issues))throw Error('Invalid or duplicated meeting metadata.');
        if(meetings.length>=MAX_MEETINGS)throw Error('Too many meetings in this snapshot.');
        if(r.positions.some(p=>!p||typeof p!=='object')||r.issues.some(i=>i===null||!['string','object'].includes(typeof i)))throw Error('Invalid issue or position metadata.');
        ids.add(r.meeting_id);meetings.push({...r,title:text(r.title),body:text(r.body),status:text(r.status)||'unknown'});
      }}
      state.meetings=meetings.sort((a,b)=>(b.date||'').localeCompare(a.date||'')||a.meeting_id.localeCompare(b.meeting_id));state.manifest=m;displayManifest();
    } catch(error) {$('archiveStatus').textContent='The archive could not be loaded safely. '+error.message;$('archiveStatus').classList.add('error');$('verificationStatus').textContent='Loading stopped; no unverified data was displayed.';}
  }
  for(const id of ['archiveSearch','archiveBody','archiveStart','archiveEnd'])$(id).addEventListener('input',()=>{state.visible=PAGE_SIZE;render();});
  $('clearFilters').addEventListener('click',()=>{for(const id of ['archiveSearch','archiveBody','archiveStart','archiveEnd'])$(id).value='';state.visible=PAGE_SIZE;render();});
  $('moreMeetings').addEventListener('click',()=>{state.visible+=PAGE_SIZE;render();});
  $('exportSelection').addEventListener('click',()=>{
    const escape=v=>'"'+String(/^[\s]*[=+\-@]/.test(String(v))?"'"+v:v).replace(/"/g,'""')+'"';
    const columns=['meeting_id','date','title','body','status','segments','source_url'];const lines=[columns,...selectedMeetings().map(m=>columns.map(k=>m[k]??''))];
    save(lines.map(row=>row.map(escape).join(',')).join('\r\n'),'meeting-selection.csv','text/csv;charset=utf-8');
  });
  load();
})();
