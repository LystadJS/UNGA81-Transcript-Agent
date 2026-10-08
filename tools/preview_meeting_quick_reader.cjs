'use strict';
/** In-memory static QA fixture. No source retrieval, browser scripts or network. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'../site'),Quick=require('../site/meeting-quick-reader.js');
const slug='hrc/99/1',link='https://transcripts.un.org/en/'+slug;
const rows=[
 {s:'HRC',fn:'Vice-President',text:'The council will now hold the interactive dialogue on the oral update about conditions in Example Territory. This is fabricated opening context.'},
 {s:'Imaginary Country',fn:'Representative',text:'Thank you, Mr. President. We strongly support humanitarian assistance for displaced families and transparent monitoring. This is only synthetic testimony.',group:'National delegation'},
 {s:'Imaginary Country',fn:'Representative',text:'We do not support sanctions on essential food and medical supplies. This is an intentionally synthetic contrasting position.',group:'National delegation'},
 {s:'Imaginary Country',fn:'Representative',text:'I have the honour to speak on behalf of the Regional Group. We strongly support humanitarian assistance for families. This is a group statement.',group:'Regional Group'},
 {s:'HRC',fn:'Vice-President',text:'We will now hold the interactive dialogue with the Special Rapporteur on rights in Another Territory. A second agenda segment is introduced here.'},
 {s:'Imaginary Country',fn:'Representative',text:'We call for decolonization and self-determination. The supporting evidence is artificial and carries no political information.',group:'National delegation'}
].map(({s,fn,text,group},i)=>({id:slug+'#'+i,meeting_slug:slug,date:'2099-01-01',language:'en',meeting:'SYNTHETIC council meeting',text,source_url:link,
  country:s,region:s==='HRC'?'Unmapped':'Synthetic',attribution:{country_status:s==='HRC'?'unresolved':'registry_mapped'},speaker_metadata:{affiliation_full:s,function:fn,group:group||null},json_pointer:'/transcript/data/'+i,text_sha256:'a'.repeat(64)}));
const q=Quick.build(rows,{meeting_slug:slug,meeting_date:'2099-01-01',title:'SYNTHETIC council meeting'});
const ui=fs.readFileSync(path.join(root,'analysis-ui.js'),'utf8');const start=ui.indexOf('  function renderQuickReader(q){'),end=ui.indexOf('  // ---------- Report content ----------',start);
if(start<0||end<0)throw Error('Render function missing');
const esc=x=>String(x??'').replace(/[&<>"']/g,k=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[k]));
const table=(h,rs)=>`<div class="table-wrap"><table><thead><tr>${h.map(x=>`<th>${esc(x)}</th>`).join('')}</tr></thead><tbody>${rs.map(r=>`<tr>${r.map(x=>`<td>${esc(x)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
const render=vm.runInNewContext(ui.slice(start,end)+'\nrenderQuickReader;',{esc,table,UNMeetingQuickReader:Quick});
const css=['theme.css','app.css','analysis.css'].map(x=>fs.readFileSync(path.join(root,x),'utf8')).join('\n');
const html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic quick reader QA</title><style>'+css+'</style></head><body><main style="max-width:1100px;margin:auto"><div class="report-document"><h2>SYNTHETIC council meeting</h2>'+render(q)+'</div></main></body></html>';
if(process.argv.length!==3)throw Error('Usage: node preview_meeting_quick_reader.cjs NEW_OUTPUT_HTML');
const target=path.resolve(process.argv[2]);if(fs.existsSync(target))throw Error('Do not overwrite');
fs.writeFileSync(target,html);fs.writeFileSync(target+'.json',JSON.stringify(q,null,2)+'\n');
console.log(JSON.stringify({preview:target,records:rows.length,positions:q.positions.length,agenda_cues:q.agenda_cues.length,collective_withheld:q.stats.withheld_collective_segments}));
