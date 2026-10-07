'use strict';
// Engineering-only evidence. Never labels the owner's real development sources.
const C = require('../research/corpus/contract.cjs');
module.exports = function fixture() {
  const plan = {schema:'un.passage-plan.v1', selection_rule:'SYNTHETIC boundary-review test',
    development_dates:['2020-01-01','2020-01-02'], holdout_dates:['2020-01-03'],
    split_unit:'whole_meeting', fit_weighting:'equal_passage',
    partition:{algorithm:'balanced_whitespace_v1', max_tokens:40, min_tokens:2},
    language:'en', duplicate_policy:'retain_and_audit', review_policy:'explicit_speech_boundaries', country_missing:'withhold'};
  const meeting = (slug,date,hasTranscript=true) => ({slug,date,hasTranscript,title:'SYNTHETIC '+slug,
    pageUrl:'/en/'+slug,jsonUrl:hasTranscript?'/en/'+slug+'.json':null,category:'SYNTHETIC Council'});
  const inventory = {schema:'un.inventory-frame.v1',transcripts_opened:0,retrieved_at:'2020-01-04T00:00:00Z',
    dates:['2020-01-01','2020-01-02','2020-01-03'].map((date,i) => {
      const meetings = [meeting('fixture/meeting'+i,date)];
      if(i===0) meetings.push(meeting('fixture/unavailable',date,false));
      return {date,pages:[{url:`https://transcripts.un.org/en/meetings.json?date=${date}&xlang=1&page=1`,
        sha256:'a'.repeat(64),data:{page:1,total:meetings.length,hasMore:false,meetings}}]};
    })};
  const frame = C.makeFrame(inventory,plan);
  const sources = frame.meetings.filter(m=>m.split==='development').map((m,i) => {
    if(!m.has_transcript) return {meeting_id:m.meeting_id,status:'inventory_unavailable'};
    const texts = ['SYNTHETIC 😀 é {{CORE}} {{UI}} <script>not executable</script> </script><img src=x onerror=alert(1)> '+
      'climate ocean finance not agree. '.repeat(18),
      'SYNTHETIC continued intervention. '.repeat(20), '', ' \r\n '];
    const doc = {video:{slug:m.meeting_id,date:m.date},transcript:{language:'en',timestamps_flagged:i>0,
      data:texts.map((text,j)=>({speaker:{name:'SYNTHETIC Speaker',affiliation:j<2?'Test Alpha':null},
        paragraphs:[{sentences:[{text}]}]}))}};
    const raw = Buffer.from('\uFEFF'+JSON.stringify(doc,null,2).replace(/\n/g,'\r\n'));
    return {meeting_id:m.meeting_id,status:'downloaded',raw_base64:raw.toString('base64'),raw_sha256:C.sha(raw)};
  });
  const bundle = C.makeBundle(frame,sources,[{country:'Test Alpha',aliases:['Test Alpha'],region:'SYNTHETIC'}]);
  return C.build(frame,bundle);
};
