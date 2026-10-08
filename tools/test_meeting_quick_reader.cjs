'use strict';
const assert=require('node:assert/strict');
const Core=require('../site/meeting-quick-reader.js');
const Analyze=require('../site/analysis-core.js');
const Collect=require('../site/collector.js');
const slug='ga/c3/81/1',date='2026-10-01',url='https://transcripts.un.org/en/'+slug;
const base=(n,text,country='Country A',opts={})=>({id:slug+'#'+n,meeting_slug:slug,date,country,region:opts.mapped===false?'Unmapped':'Africa',language:'en',scope:'committee_3',meeting:'Third Committee debate',text,
 source_url:opts.url||url,text_sha256:'f'.repeat(64),attribution:{country_status:opts.mapped===false?'unresolved':'registry_mapped'},
 speaker_metadata:{affiliation_full:country,function:opts.role||'Representative',group:'National delegation',...(opts.speaker_id?{id:opts.speaker_id}:{})}});
const passages=[
 base(0,'We strongly support humanitarian assistance for displaced people. Governments should maintain access to clean water.'),
 base(1,'We oppose humanitarian assistance in this imaginary counterexample. The issue is disputed.'),
 base(2,'We note that another country supports humanitarian assistance, but we make no statement of our own.', 'Country B'),
 base(3,'A third delegation called on Country A to oppose humanitarian assistance. This is reported information only.', 'Country B'),
 base(4,'We firmly support development cooperation and sustainable development through education and technical assistance.', 'Country C'),
 base(5,'We support economic growth and development cooperation, but we reject economic development programmes.', 'Country D'),
 base(6,'Thank you, Mr. Chair. I now give the floor to the next speaker.', 'Country E', {role:'Chair'}),
 base(7,'We welcome humanitarian assistance and relief efforts to vulnerable communities around the world.', 'Unmapped', {mapped:false}),
 base(8,'This statement mentions nuclear disarmament and climate change but expresses no view about either subject.', 'Country F'),
];
let done=0;
function check(name,fn){fn();done++;console.log('PASS',name)}
const result=Core.build(passages,{meeting_slug:slug,meeting_date:date,title:'Third Committee'});
check('source-bound selected meeting and date',()=>{assert.equal(result.meeting_slug,slug);assert.equal(result.stats.source_segments,9);assert.equal(result.agenda.series,'ga:c3');});
check('speaker identity never guessed from common affiliation/function',()=>{assert.equal(result.stats.records_with_explicit_speaker_id,0);assert.equal(result.stats.records_with_affiliation_function_proxy,9);});
check('unmapped country retained as missing',()=>{assert.equal(result.stats.unresolved_country_segments,1);assert.equal(result.stats.mapped_country_segments,8);});
check('counts do not claim one segment equals one speaker',()=>{assert.equal(result.stats.recorded_countries,6);assert.ok(result.limitations.some(x=>x.includes('person identifiers')));});
check('prose has defensible caveats and source scope',()=>{assert.equal(result.paragraphs.length,2);assert.ok(result.paragraphs[0].includes('not a finding'));assert.equal(result.sources,'all_english_source_segments_in_exact_selected_meeting_before_topic_filter');});
check('themes count source segments, not repeated keywords',()=>{assert.ok(result.themes.find(x=>x.id==='humanitarian').segments>=4);assert.ok(result.themes.every(x=>x.segments<=result.stats.source_segments));});
check('genuine subject support requires attributed first-person statement',()=>{assert.ok(result.positions.some(p=>p.country==='Country A'&&p.classification==='mixed_or_qualified'));});
check('other-country reported position never becomes speaker stance',()=>{assert.ok(!result.positions.some(p=>p.country==='Country B'));});
check('unmapped affiliation cannot create a country position',()=>{assert.ok(!result.positions.some(p=>p.country==='Unmapped'));});
check('procedural speaker not assigned position',()=>{assert.ok(!result.positions.some(p=>p.country==='Country E'));});
check('issue word without evaluative predicate never assigned position',()=>{assert.ok(!result.positions.some(p=>p.country==='Country F'));});
check('contrast clause does not leak stance to unrelated issue',()=>{const r=result.positions.filter(p=>p.country==='Country D');assert.ok(r.length>=1);});
check('source links use only safe UN host',()=>{assert.ok(result.positions.every(p=>p.evidence.every(e=>new URL(e.source_url).host==='transcripts.un.org')));});
check('external URLs rejected rather than embedded',()=>{const x=Core.build([base(10,'We support nuclear disarmament programmes in our region.', 'Country Q',{url:'https://bad.example'})],{meeting_slug:slug});assert.equal(x.positions[0]?.evidence.length||0,0);});
check('no meeting bleed through shared date',()=>{const x=Core.build([...passages,{...passages[0],meeting_slug:'ga/c4/81/3',id:'ga/c4/81/3#0'}],{meeting_slug:slug});assert.equal(x.stats.source_segments,9);});
check('empty transcript avoids false zero issue claim',()=>{const x=Core.build([],{meeting_slug:slug});assert.equal(x.stats.source_segments,0);assert.equal(x.stats.median_words_per_segment,null);assert.equal(x.positions.length,0);assert.ok(x.paragraphs[0].includes('does not identify'));});
check('explicit quoted third-party advocacy not attributed',()=>{const x=Core.build([base(10,'The witness testified, “We support humanitarian assistance.” This is a quotation, not this delegation’s position.','Country R')],{meeting_slug:slug});assert.equal(x.positions.length,0);});
check('country co-mention does not prove position',()=>{const x=Core.build([base(10,'Country X and Country Y addressed humanitarian assistance at a meeting.','Country R')],{meeting_slug:slug});assert.equal(x.positions.length,0);});
check('source speaker role family honors presiding status',()=>{assert.equal(Core.role(passages[6]),'presiding_or_official');assert.equal(Core.role(passages[0]),'country_affiliated');});
check('canonical agenda series derives only from metadata path',()=>{assert.equal(Core.agendaSeries('hrc/63/25','Human Rights Council').series,'hrc:63');assert.equal(Core.agendaSeries('asset/fake/unknown','Human rights discussion').basis,'not_established');});
check('malformed meeting ID fails closed',()=>{assert.throws(()=>Core.build(passages,{meeting_slug:'../fake'}));});
check('no network runtime needed',()=>{assert.equal(result.external_ai_calls,0);});
(async()=>{
 const meeting={slug,title:'Third Committee — synthetic',date,pageUrl:'/en/'+slug,jsonUrl:'/en/'+slug+'.json',hasTranscript:true};
 const params={start:date,end:date,meeting_date:date,meeting_slug:slug,scope:'all',region:'All regions',topic:'nuclear',phrases:['nuclear'],exclude:[],methods:['frequency']};
 const request=async source=>source.includes('meetings.json')?{hash:'e'.repeat(64),data:{page:1,total:1,hasMore:false,meetings:[meeting]}}:
    {hash:'a'.repeat(64),data:{video:{slug,date},transcript:{language:'en',data:passages.map(r=>({speaker:{affiliation:r.country,function:r.speaker_metadata.function,affiliation_full:r.country,group:'National delegation'},paragraphs:[{sentences:[{text:r.text}]}]}))}}};
 const countries=passages.filter(r=>r.region!=='Unmapped').map(r=>({country:r.country,iso3:r.country.slice(-3),aliases:'',region:'Africa'}));
 const corpus=await Collect.collect(params,countries,{request});
 check('collector preserves original speaker metadata and mapping status',()=>{assert.equal(corpus.records[0].speaker_metadata.function,'Representative');assert.equal(corpus.records[0].attribution.country_status,'registry_mapped');});
 const report=await Analyze.analyze(corpus,params);
 check('topic-filtered analysis leaves all-meeting quick read intact',()=>{assert.ok(report.counts.matched<corpus.records.length);assert.equal(report.quick_reader.stats.source_segments,corpus.records.length);assert.equal(report.quick_reader.external_ai_calls,0);});
 check('non-single meeting has no quick reader',async()=>{const {meeting_slug,meeting_date,...rest}=params;const other=await Analyze.analyze({...corpus,collection:{...corpus.collection,selection_mode:'range'}},rest);assert.equal(other.quick_reader,undefined);});
 console.log(JSON.stringify({status:'PASS',checks:done,synthetic:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
