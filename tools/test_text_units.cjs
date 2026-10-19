'use strict';
const assert=require('node:assert/strict');
const Text=require('../site/text-units.js'),Core=require('../site/analysis-core.js');
assert.deepEqual(Text.tokens('ＦＯＯ café—peace, 123!'),['foo','café','peace','123']);
assert.equal(Text.wordCount('peace—security １０ children’s'),5);
assert.equal(Text.wordCount('...'),0);
assert.equal(Text.reduceProceduralNoise('I thank the representative of China for the statement. And I now give the floor to the representative of Latvia.').text,'');
const courtesy='Thank you, Mr. Chair. We support humanitarian assistance for displaced families and oppose sanctions on medicine.';
assert.equal(Text.reduceProceduralNoise(courtesy).text,'We support humanitarian assistance for displaced families and oppose sanctions on medicine.');
assert.equal(Text.reduceProceduralNoise(courtesy).removed_sentence_count,1);
for(const text of ['I thank the representative for her statement.','The 10,245th meeting of the Security Council is called to order.','I thank the representative of China for the statement.','I thank Mrs. DiCarlo for her briefing.','Thank you, President, for giving me the floor.','I now give the floor to the representative of Example.','The meeting is adjourned.','The Security Council will now begin its consideration of the agenda item.']) assert.equal(Text.reduceProceduralNoise(text).text,'',text);
for(const text of ['Thank you for supporting humanitarian assistance to displaced families.','We call for the Security Council to act now.','The Security Council should protect civilians.','I thank the chair, but sanctions should end.','Thank you, President, sanctions should end immediately.','I thank the representative of China for her statement on sanctions.','I thank Mrs. DiCarlo for supporting sanctions.'])assert.equal(Text.reduceProceduralNoise(text).text,text,text);
const slug='ga/c3/81/1',date='2099-01-01';
const texts=['The Security Council will now begin its consideration of the agenda item.','Thank you, Mr. Chair. Humanitarian assistance for displaced families remains essential.','Education and economic development strengthen communities.'];
const records=texts.map((text,i)=>({id:slug+'#'+i,meeting_slug:slug,date,text,scope:'committee_3',meeting:'Synthetic',country:'Example '+i,region:'Africa',language:'en',source_url:'https://transcripts.un.org/en/'+slug,text_sha256:'a'.repeat(64)}));
const original=JSON.stringify(records),raw=Core.tfidf(records),clean=Core.tfidf(records,{reduceProceduralNoise:true});
const stopped=Core.tfidf([{...records[0],text:'representative floor statement'}],{reduceProceduralNoise:true});
assert.equal(stopped.vectors[0].size,0);assert.deepEqual(stopped.processing.zero_vector_ids,[records[0].id]);assert.ok(stopped.processing.procedural_stoplist.includes('floor'));
assert.ok(raw.terms.some(t=>t.term==='council'));assert.ok(!clean.terms.some(t=>t.term==='council'));assert.ok(clean.terms.some(t=>t.term==='humanitarian'));assert.equal(clean.processing.removed_sentence_count,2);assert.deepEqual(clean.processing.zero_text_ids,[records[0].id]);assert.equal(clean.processing.original_included_count,3);assert.equal(JSON.stringify(records),original);
(async()=>{
 const corpus={schema:'un.browser.corpus.v1',records,coverage:[]};
 let latentCalled=false;
 const result=await Core.analyze(corpus,{start:date,end:date,scope:'all',region:'All regions',topic:'',phrases:[],exclude:[],methods:['tfidf','similarity','clusters','length']},undefined,async(given,vectors)=>{latentCalled=true;assert.deepEqual(given,records);assert.deepEqual(vectors,raw.vectors);return {synthetic:true};});
 assert.ok(latentCalled);assert.equal(result.counts.matched,3);assert.equal(result.briefing.stats.matched_words,texts.reduce((n,t)=>n+Text.wordCount(t),0));assert.ok(!result.briefing.themes.some(t=>t.id==='peace_security'));assert.ok(result.briefing.themes.some(t=>t.id==='humanitarian'));assert.equal(result.methods.tfidf.processing.original_included_count,3);assert.equal(result.methods.similarity.processing.removed_sentence_count,2);assert.equal(result.methods.length.reduce((n,b)=>n+b.total,0),3);assert.equal(JSON.stringify(records),original);
 console.log('PASS shared Unicode counts, narrow procedural sentence reduction, original counts/provenance, lexical audit and unchanged latent vectors (synthetic only; heldout opened: 0)');
})().catch(e=>{console.error(e);process.exitCode=1;});

const opening='The 11th meeting of the Disarmament and International Security Committee of the 81st session of the General Assembly is called to order.';
assert.equal(Text.reduceProceduralNoise(opening).text,'');
assert.equal(Text.reduceProceduralNoise('Distinguished delegates, dear colleagues.').text,'');
assert.equal(Text.reduceProceduralNoise('The full version of this statement will be submitted to the Secretariat.').text,'');
for(const line of ['Distinguished delegates, nuclear weapons threaten humanity.','The meeting of the committee is called to order, but we oppose nuclear weapons.','We speak on behalf of our group and support disarmament.','Permanent membership of the Security Council requires reform.']) assert.equal(Text.reduceProceduralNoise(line).text,line);
const ceremony=Core.tfidf([{...records[0],text:'Distinguished representatives now speaking on behalf of permanent members discuss nuclear disarmament.'}],{reduceProceduralNoise:true});
for(const term of ['distinguished','now','speaking','behalf'])assert.ok(!ceremony.terms.some(t=>t.term===term));
assert.ok(ceremony.terms.some(t=>t.term==='permanent'));

for(const line of ['I thank the distinguished permanent representative of Vietnam speaking on behalf of ASEAN.','Now I give the floor to the distinguished permanent representative of Vietnam, speaking on behalf of ASEAN.','And now I give the floor to Her Excellency, Ambassador Example, Director of the Agency.','I now call on the distinguished delegate for Costa Rica.','You have the floor.'])assert.equal(Text.reduceProceduralNoise(line).text,'',line);
for(const line of ['I thank the representative for supporting sanctions.','I thank the representative who condemns nuclear weapons.'])assert.equal(Text.reduceProceduralNoise(line).text,line);
assert.equal(Text.summaryEvidenceSentence('In accordance with the program of work, the committee will discuss disarmament.'),false);
assert.equal(Text.summaryEvidenceSentence('We support nuclear disarmament and must continue negotiations.'),true);
const Q=require('../site/meeting-quick-reader.js');
const exampleRecords=[{...records[0],text:opening+' In accordance with the program of work, the committee will discuss disarmament.'},{...records[1],text:'We support nuclear disarmament and must continue negotiations.'}];
const example=Q.build(exampleRecords,{meeting_slug:slug,meeting_date:date,title:'Synthetic'});
assert.ok(example.themes.find(t=>t.id==='peace_security').evidence.every(e=>e.record_id===records[1].id));

assert.equal(Text.summaryEvidenceSentence('I thank the Director and Deputy to the High Representative for Disarmament Affairs, Mr. Example, for his statement.'),false);

assert.ok(!Core.tfidf([{...records[0],text:'His Excellency discusses nuclear disarmament.'}],{reduceProceduralNoise:true}).terms.some(t=>t.term==='excellency'));

for(const ordinal of ['eighth','ninth','twenty-first','one hundred and second']){
 const line=`The ${ordinal} meeting of the Disarmament and International Security Committee of the 81st session of the General Assembly is called to order.`;
 assert.equal(Text.reduceProceduralNoise(line).text,'');assert.equal(Text.summaryEvidenceSentence(line),false);
 assert.equal(Text.reduceProceduralNoise(line.replace('.',', but we support nuclear disarmament.')).text,line.replace('.',', but we support nuclear disarmament.'));
}
