import {createController,MAX_IMPORT_BYTES} from './controller.mjs';
import {createProvider} from './provider.mjs';
import {STATES,SECTIONS,reasonText,scopeTitle} from './copy.mjs';
const $ = id => document.getElementById(id);
const node = (tag,text,className) => {const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;};
const action=(text,fn,cls='secondary')=>{const b=node('button',text,cls);b.type='button';b.addEventListener('click',fn);return b;};
const provider=createProvider(), controller=createController(provider);
let catalog=null, page='explore', selectedMeeting=null, evidenceInvoker=null, polling=false;
const countryName=id=>catalog?.countries.find(x=>x.id===id)?.name||id||'Country not assigned';
const meetingName=id=>catalog?.meetings.find(x=>x.id===id);
function formError(message) {$('form-error').textContent=message;$('form-error').hidden=!message;}
function selection() {
  const start=$('from').value,end=$('to').value;
  if(Boolean(start)!==Boolean(end))throw new Error('Choose both a start and end date, or leave both blank.');
  if(start>end)throw new Error('The end date must be on or after the start date.');
  if(page==='meetings'&&!selectedMeeting)throw new Error('Select a meeting by name, date and forum.');
  if(page==='explore'&&!$('country').value&&!$('topic').value&&!start)throw new Error('Choose a country, topic or date range.');
  return {page,country:$('country').value||null,topic:$('topic').value||null,period:start?{start,end}:null,meeting:page==='meetings'?selectedMeeting:null};
}
function changed() {formError('');controller.invalidate();}
function meetingOptions() {
  if(!catalog)return;
  const term=$('meeting-search').value.trim().toLocaleLowerCase('en');
  const choices=catalog.meetings.filter(m=>(m.name+' '+m.date+' '+m.forum).toLocaleLowerCase('en').includes(term));
  $('meeting-options').replaceChildren();
  for(const meeting of choices) {
    const label=node('label',undefined,'meeting-choice'),radio=document.createElement('input');
    radio.type='radio';radio.name='meeting';radio.value=meeting.id;radio.checked=selectedMeeting===meeting.id;
    const labelText=node('span',meeting.name);labelText.append(node('small',meeting.date+' · '+meeting.forum));label.append(radio,labelText);
    radio.addEventListener('change',()=>{selectedMeeting=meeting.id;changed();});$('meeting-options').append(label);
  }
  if(!choices.length)$('meeting-options').append(node('p','No invented meetings match this name.','hint'));
}
function navigate(next,clear=true) {
  if(page===next)return;
  page=next;if(clear)controller.invalidate();
  document.querySelectorAll('[data-page]').forEach(b=>{if(b.dataset.page===page)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
  const titles={explore:['Explore the conversation','Choose a country or topic. Add dates to narrow your briefing.'],meetings:['Understand a meeting','Find a meeting by name. Choose its date and forum, then create your briefing.'],saved:['Return to a briefing','Reopen a saved result with its original selections and current access checks.']};
  [$('page-title').textContent,$('page-intro').textContent]=titles[page];
  $('selection-panel').hidden=page==='saved';$('saved-panel').hidden=page!=='saved';$('briefing').hidden=page==='saved';$('meeting-picker').hidden=page!=='meetings';
  $('page-title').focus();meetingOptions();renderSaved(controller.snapshot());
}
function renderSaved(state) {
  $('saved-count').textContent=String(state.saved.length);$('saved-list').replaceChildren();
  if(!state.saved.length){$('saved-list').append(node('p','No briefings saved in this session.','panel'));return;}
  for(const record of state.saved){const item=node('article',undefined,'panel saved-card'),text=node('div');text.append(node('h3',scopeTitle(record.query,catalog)),node('p',periodLabel(record.query),'meta'));const buttons=node('div',undefined,'form-actions');buttons.append(action('Open briefing',async()=>{
    // Restoring does not resolve the question or run a model again.
    navigate(record.query.intent==='meeting'?'meetings':'explore');restoreForm(record.query);await controller.openSaved(record.id);
  }),action('Remove',()=>controller.removeSaved(record.id)));item.append(text,buttons);$('saved-list').append(item);}
}
function restoreForm(query){$('country').value=query.requested.countries[0]||'';$('topic').value=query.requested.topic||'';$('from').value=query.requested.period?.start||'';$('to').value=query.requested.period?.end||'';selectedMeeting=query.requested.meeting;meetingOptions();}
function periodLabel(query){const p=query.resolved.period;return `${p.start} to ${p.end} · inclusive New York dates${query.defaulted_fields.includes('period')?' · available preview period':''}`;}
function unavailable(section){const card=node('section',undefined,'panel unavailable');card.append(node('span',STATES[section.state]||'Unavailable','badge '+section.state),node('h3',SECTIONS[section.id]||'Additional analysis'),node('p',reasonText(section.reason),'section-subtitle'));return card;}
function coveragePanel(coverage){const d=node('details',undefined,'coverage-details');d.append(node('summary','See included and unavailable records'));const list=node('dl');for(const [label,count] of [['Records in selected period',coverage.population.frame],['Matching records',coverage.population.eligible],['Outside the selected question',coverage.population.excluded],['Unavailable records',coverage.population.missing],['Unverified records',coverage.population.unverified],['Reader failures',coverage.failed],['Unevaluated matching records',coverage.assignments.not_fitted]])list.append(node('dt',label),node('dd',String(count)));d.append(list);return d;}
function render(state) {
  if(!catalog)return;
  $('status').textContent=(state.notice?reasonText(state.notice):STATES[state.phase])||'Briefing unavailable';
  $('briefing').setAttribute('aria-busy',String(state.phase==='loading'));
  $('create').disabled=state.phase==='loading';renderSaved(state);
  const focused=document.activeElement?.dataset.focusKey;
  const dialog=$('evidence-dialog');
  if(state.details){const detail=state.details;const content=$('evidence-content');content.replaceChildren();const meeting=meetingName(detail.meeting);content.append(node('p',detail.capacity==='national'?countryName(detail.country):'Collective statement · not attributed to a national position','meta'),node('p',meeting?`${meeting.name} · ${meeting.date} · ${meeting.forum}`:'Invented meeting','meta'),node('blockquote',detail.text),node('p','Synthetic source: '+detail.source,'meta'));if(!dialog.open)dialog.showModal();}
  else {if(dialog.open)dialog.close();$('evidence-content').replaceChildren();}
  const root=$('briefing');root.replaceChildren();
  if(state.phase==='idle'||state.phase==='loading') {const box=node('div',undefined,'empty-prompt panel');box.append(node('p',state.phase==='loading'?'Checking available records':'Start with a question','eyebrow'),node('h2',state.phase==='loading'?'Preparing your briefing…':'What would you like to understand?'),node('p','Your briefing combines available records, a short overview and supporting evidence.'),node('p','This preview contains invented examples dated 23–25 September 2024.','hint'));root.append(box);return;}
  if(!state.model||!state.model.valid||!state.query){root.append(node('div',reasonText(state.notice||'invalid_bundle'),'notice'));return;}
  const header=node('header',undefined,'report-top'),heading=node('div');heading.append(node('p','Synthetic briefing','eyebrow'),node('h2',scopeTitle(state.query,catalog)),node('p',periodLabel(state.query),'meta'));header.append(heading);
  const buttons=node('div',undefined,'report-actions');const save=action('Save briefing',()=>controller.save());save.dataset.focusKey='save';save.disabled=!['ready','partial','empty'].includes(state.phase);
  const exp=action('Export read-only result',async()=>{const output=await controller.exportModel();if(!output||!controller.isCurrent(output.ticket))return;const url=URL.createObjectURL(new Blob([output.utf8],{type:output.mediaType}));const a=document.createElement('a');a.href=url;a.download=output.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),0);});exp.dataset.focusKey='export';exp.disabled=!state.canExport;buttons.append(save,exp);header.append(buttons);root.append(header);
  const cov=state.model.sections.find(s=>s.coverage!==null)?.coverage;
  if(cov){const stats=node('div',undefined,'stats');for(const [value,label] of [[cov.population.eligible,'Matching invented records'],[cov.population.missing+cov.population.unverified,'Unavailable or unverified'],[cov.population.excluded,'Outside this question']]){const stat=node('div',undefined,'stat');stat.append(node('b',String(value)),node('span',label));stats.append(stat);}root.append(stats);}
  const overview=state.model.sections.find(s=>s.id==='overview');
  if(!overview||!['ready','partial'].includes(overview.state)){for(const s of state.model.sections)root.append(unavailable(s));return;}
  if(overview.state==='partial')root.append(node('p',reasonText('incomplete_coverage'),'notice'));
  const grid=node('div',undefined,'report-grid'),main=node('section',undefined,'panel'),side=node('div');main.append(node('h2','What the available records show'),node('p',`${cov?.population.eligible??0} invented records match this question. Read the examples below; they do not describe real countries’ positions.`));
  const evidence=[...new Map(state.model.sections.flatMap(s=>s.evidence).map(e=>[e.id,e])).values()];
  const countries=[...new Set(evidence.filter(e=>e.capacity==='national').map(e=>e.country))];
  if(countries.length){main.append(node('p','Highlight a country in the evidence','hint'));const chips=node('div',undefined,'chips');for(const id of [null,...countries]){const b=action(id===null?'All records':countryName(id),()=>controller.highlight(id),'chip');b.dataset.focusKey='highlight-'+(id||'all');b.setAttribute('aria-pressed',String(state.highlight===id));chips.append(b);}main.append(chips);}
  const list=node('div',undefined,'evidence-list');
  for(const e of evidence){const item=node('article',undefined,'evidence-card'+(state.highlight!==null&&e.country===state.highlight&&e.capacity==='national'?' highlighted':''));const meeting=meetingName(e.meeting_id);item.append(node('h3',e.capacity==='national'?countryName(e.country):'Collective statement'),node('p',meeting?`${meeting.name} · ${meeting.date}`:'Invented record','meta'));const b=action('Read supporting record',()=>{evidenceInvoker=e.id;controller.openEvidence(e.id);});b.dataset.evidence=e.id;b.dataset.focusKey=e.id;b.setAttribute('aria-label',`Read supporting record ${e.id}`);item.append(b);list.append(item);}main.append(list);if(cov)main.append(coveragePanel(cov));
  for(const s of state.model.sections.filter(s=>s.id!=='overview'&&s.id!=='evidence')){side.append(unavailable(s));}grid.append(main,side);root.append(grid);
  if(focused&&!dialog.open)document.querySelector(`[data-focus-key="${CSS.escape(focused)}"]`)?.focus();
}
$('question-form').addEventListener('submit',event=>{event.preventDefault();formError('');try{controller.create(selection());}catch(e){formError(e.message);$('form-error').focus();}});
for(const id of ['country','topic','from','to'])$(id).addEventListener('input',changed);
$('meeting-search').addEventListener('input',()=>{selectedMeeting=null;changed();meetingOptions();});
$('reset').addEventListener('click',()=>{$('question-form').reset();selectedMeeting=null;changed();meetingOptions();});
document.querySelectorAll('[data-page]').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.page)));
$('about-button').addEventListener('click',()=>{$('about').open=true;$('about').querySelector('summary').focus();});
$('close-evidence').addEventListener('click',()=>{controller.closeEvidence();if(evidenceInvoker)document.querySelector(`[data-evidence="${CSS.escape(evidenceInvoker)}"]`)?.focus();});
$('evidence-dialog').addEventListener('cancel',()=>{controller.closeEvidence();if(evidenceInvoker)document.querySelector(`[data-evidence="${CSS.escape(evidenceInvoker)}"]`)?.focus();});
$('bundle-file').addEventListener('change',()=>{const f=$('bundle-file').files?.[0];controller.invalidate();if(!f)return;if(f.size>MAX_IMPORT_BYTES){controller.importBundle(Promise.reject(new Error('size')));return;}controller.importBundle(f.text()).then(s=>{if(s?.query){navigate(s.query.intent==='meeting'?'meetings':'explore',false);restoreForm(s.query);}});$('bundle-file').value='';});
$('cancel-import').addEventListener('click',()=>{controller.invalidate();$('bundle-file').value='';});
// Permission checks are refreshed while visible, on focus, before source access and before export.
async function poll(){if(polling||document.hidden)return;polling=true;try{await controller.refreshTrust();}finally{polling=false;}}
setInterval(poll,1000);window.addEventListener('focus',poll);document.addEventListener('visibilitychange',()=>{if(document.hidden)controller.invalidate('permission_changed');else poll();});
window.addEventListener('pagehide',()=>controller.invalidate('permission_changed'));
try {
  if(!['127.0.0.1','localhost','[::1]'].includes(location.hostname)||location.protocol!=='http:'||!crypto.subtle)throw new Error('local_preview_only');
  catalog=await provider.catalog();
  if(catalog.schema!=='u1.synthetic-catalog.v1'||catalog.fixture_kind!=='synthetic')throw new Error('catalog');
  for(const c of catalog.countries){const o=node('option',c.name);o.value=c.id;$('country').append(o);}
  for(const t of catalog.topics){const o=node('option',t.name);o.value=t.id;$('topic').append(o);}
  controller.subscribe(render);$('create').disabled=false;meetingOptions();
} catch {$('host-error').hidden=false;$('status').textContent='Preview unavailable. No unverified briefing is displayed.';}
