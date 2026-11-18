/* Dated reporting comparisons use only existing object-specific source extracts. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const R=require('../site/meeting-report-core.js'),C=require('../site/collector.js'),F=require('./meeting_report_fixture.cjs');
const policy=JSON.parse(fs.readFileSync(require.resolve('../site/reporting-exclusions.json')));
const object='humanitarian access for civilians in the conflict zone and transparent international oversight of aid deliveries';
const passage=(country,text,group=null)=>({speaker:{affiliation:country,name:country+' representative',function:'Representative',group},paragraphs:[{sentences:[{text}]}]});
async function corpus(index,rows,date='2026-11-'+(10+index)){
 const m={...F.meetings[index],date,title:index?'Later <img> source':'Earlier source'};
 return C.collect({start:m.date,end:m.date,scope:'all',meeting_slug:m.slug,meeting_date:m.date},F.countries,{request:async url=>{
  const data=new URL(url).pathname.endsWith('meetings.json')?{meetings:[m],total:1,page:1,hasMore:false}:{video:{slug:m.slug,date:m.date},transcript:{language:'en',data:rows}},raw=JSON.stringify(data);return {data,raw,hash:await C.sha(raw),retrieved_at:'2026-11-18T20:00:00Z'};
 }});
}
(async()=>{
 const earlier=await corpus(0,[passage('Kenya','We oppose '+object+'.'),passage('United States','We support '+object+'.')]);
 const later=await corpus(1,[passage('Kenya','We support '+object+'.')]),corpora=[later,earlier],original=JSON.stringify(corpora);
 await R.validateCorpora(corpora,policy,F.countries);
 const selected=corpora.flatMap(c=>c.coverage.map(m=>m.slug)),report=R.build(corpora,selected),baseline=JSON.stringify(report),csv=R.evidenceCSV(report.records),timeline=R.countryTimeline(report),kenya=timeline.find(c=>c.country==='Kenya'),usa=timeline.find(c=>c.country==='United States');
 assert.deepEqual(timeline.map(c=>c.country),['Kenya','United States']);assert.deepEqual(kenya.observations.map(o=>o.date),['2026-11-10','2026-11-11']);assert.equal(kenya.unobserved_meetings,0);assert.equal(usa.unobserved_meetings,1);
 assert.equal(kenya.observations[0].positions[0].expression_label,'Opposes');assert.equal(kenya.observations[0].us_matches[0].expression_label,'Supports');assert.match(kenya.observations[0].comparison,/no agreement score/);
 assert.equal(kenya.observations[1].us_matches.length,0);assert.match(kenya.observations[1].comparison,/comparison gap/); // Never carry earlier U.S. wording forward.
 const html=R.reportHTML(report);assert(html.includes('country-timeline'));assert(html.includes('No affiliated source segment in 1 others'));assert(!html.includes('in 0 others'));assert(html.includes('not verified government positions or policy changes'));assert(html.includes('Later &lt;img&gt; source'));assert(!html.includes('<img>'));
 assert.equal(JSON.stringify(report),baseline);assert.equal(R.evidenceCSV(report.records),csv);assert.equal(JSON.stringify(corpora),original);
 const saved=R.savedReport(report,corpora);assert(!Object.hasOwn(saved,'country_timeline'));const opened=await R.openSaved({...saved,country_timeline:[{country:'forged'}]},policy,F.countries);assert.deepEqual(R.countryTimeline(R.build(opened.corpora,opened.selected,opened.settings)),timeline);
 assert(html.includes('class="report-country-index"'));assert.equal((html.match(/id="report-country-1"/g)||[]).length,1);assert.equal((html.match(/id="report-country-2"/g)||[]).length,1);assert(html.includes('href="#report-country-index"'));
 const singleNavigation=R.reportHTML(R.build([earlier],[F.meetings[0].slug]));assert(singleNavigation.includes('class="report-country-index"'));assert.equal((singleNavigation.match(/class="report-country-target"/g)||[]).length,2);
 const oneAffiliation=R.reportHTML(R.build([later],[F.meetings[1].slug]));assert(!oneAffiliation.includes('class="report-country-index"'));assert(!oneAffiliation.includes('href="#report-country-index"'));
 const unsafe=structuredClone(report);unsafe.records[0].country='<img src=x onerror=alert(1)>';const escaped=R.reportHTML(unsafe);assert(escaped.includes('&lt;img src=x onerror=alert(1)&gt;'));assert(!escaped.includes('<img'));
 const sameDay=await corpus(1,[passage('Kenya','We support '+object+'.')],'2026-11-10');
 const sameDayCountry=R.countryTimeline(R.build([earlier,sameDay],selected))[0];assert.equal(sameDayCountry.observations.find(o=>o.meeting_slug===F.meetings[1].slug).us_matches.length,0);
 const collective=await corpus(1,[passage('Kenya','We speak on behalf of the Example Group. We support '+object+'.','Example Group')]);
 const collectiveTimeline=R.countryTimeline(R.build([earlier,collective],selected));const group=collectiveTimeline[0].observations[1];assert(group.collective_only);assert.deepEqual(group.positions,[]);assert.deepEqual(group.us_matches,[]);assert(R.reportHTML(R.build([earlier,collective],selected)).includes('Collective statement; no national position assigned.'));
 const differing=await corpus(0,[passage('Kenya','We support '+object.replace('civilians','militias')+'.'),passage('United States','We support '+object+'.')]);
 const differingView=R.countryTimeline(R.build([differing,later],selected))[0].observations[0];assert(differingView.positions.length);assert.equal(differingView.us_matches.length,0);assert.match(differingView.comparison,/comparison gap/); // Subject-family matches never suffice.
 const noUS=await corpus(0,[passage('Kenya','We support '+object+'.'),passage('United States','Thank you President. We appreciate the opportunity to participate in this discussion and listen to colleagues today.')]);
 const noUSTimeline=R.countryTimeline(R.build([noUS,later],selected));assert.match(noUSTimeline.find(c=>c.country==='United States').observations[0].comparison,/No eligible U.S./);assert.equal(noUSTimeline[0].observations[0].us_matches.length,0);
 const repeated=await corpus(0,[...Array.from({length:5},()=>passage('Kenya','We oppose '+object+'.')),passage('United States','We support '+object+'.')]);
 const repeatedKenya=R.countryTimeline(R.build([repeated,later],selected))[0];assert.equal(repeatedKenya.observations.length,2);assert.equal(repeatedKenya.observations[0].positions.length,1);assert.equal(repeatedKenya.observations[0].us_matches.length,1);assert(!Object.hasOwn(repeatedKenya,'score'));assert(!Object.hasOwn(repeatedKenya,'weight'));assert.equal(R.reportHTML(R.build([repeated,later],selected)).split('We oppose '+object+'.').length-1,2);
 const single=R.build([earlier],[F.meetings[0].slug]);assert(!R.reportHTML(single).includes('class="country-timeline"'));assert(R.reportHTML(single).includes('U.S. extracts for this meeting'));
 const empty=R.build(corpora.map(c=>({...c,records:[]})),selected);assert.deepEqual(R.countryTimeline(empty),[]);assert(R.reportHTML(empty).includes('No recorded affiliations in the loaded selected source'));
 console.log('PASS: automatic dated country coverage, exact same-meeting object/US links, opposite expressions without agreement inference, no carry-forward, collective and missing-source gaps, repeat invariance, escaped titles, rebuilt imports, unchanged schemas/sources/CSV and single/empty report boundaries');
})().catch(e=>{console.error(e);process.exitCode=1;});
