'use strict';
const C=require('../site/passage-pilot-core.js'),R=require('../site/reviewed-units.js'),A=require('../site/analysis-core.js');
async function fixture(count=6){
  const names=['alpha','bravo','charlie','delta','echo','foxtrot'],records=[],passages=[];
  for(let i=0;i<count;i++){
    const parts=[`Ocean climate resilience financing coastal adaptation ${names[i]} 😀.`,`Security peace diplomacy conflict prevention ceasefire ${names[i]}.`,`Development debt trade investment infrastructure ${names[i]}.`];
    const text=parts.join(' ')+' Closing procedural sentence not selected.',id='asset/test/group'+i+'#1';
    records.push({id,text,text_sha256:await C.digest(text),raw_sha256:'b'.repeat(64),date:'2026-09-22',country:'Synthetic '+names[i],region:'Asia-Pacific',language:'en',scope:'general_debate',meeting:'Synthetic meeting '+i,source_url:'https://transcripts.un.org/en/asset/test/group'+i});
    let start=0;for(let j=0;j<parts.length;j++){const end=start+Array.from(parts[j]).length;passages.push({id:'P'+i+j,parent_id:id,start,end,text_sha256:await C.digest(parts[j])});start=end+1;}
  }
  const source='\uFEFF'+JSON.stringify({schema:'un.browser.corpus.v1',origin:'SYNTHETIC ENGINEERING INPUT — not UN evidence',records,coverage:[]},null,2).replace(/\n/g,'\r\n');
  const first=records[0],audio={id:'A01',parent_id:first.id,parent_text_sha256:first.text_sha256,source_snapshot_sha256:first.raw_sha256,start:0,end:5,original_excerpt:C.slice(first.text,0,5),video_url:'https://webtv.un.org/en/asset/test/group0',source_url:first.source_url,clip_start_seconds:0,clip_end_seconds:5,clip_sha256:await C.digest('abc'),audio_base64:'YWJj'};
  const packet={schema:'un.speech-pilot-packet.v1',corpus_sha256:await C.digest(source),selection:'SYNTHETIC ENGINEERING FIXTURE; dummy bytes are not an audio recording or a human review',parents:records.map(r=>({...r,reviewed_type:'substantive_speech'})),passages,audio:[audio]};
  const packetText=JSON.stringify(packet),ctx=await C.load(new TextEncoder().encode(packetText)),confirmed={confirmed:true,reviewer:'SYNTHETIC ENGINEERING FIXTURE',reviewed_at:'2020-01-01T00:00:00Z',note:'Synthetic test choice, not a user label'};
  const review={schema:'un.speech-pilot-review.v1',packet_sha256:ctx.packet_sha256,corpus_sha256:packet.corpus_sha256,choices:[{...confirmed,kind:'audio',id:'A01',decision:'supported',listened:true},...passages.map(p=>({...confirmed,kind:'passage',id:p.id,decision:'include',start:p.start,end:p.end}))]};
  const created=await R.create(source,packetText,JSON.stringify(review),A.validateCorpus);
  const payload={kind:'reviewed',text:new TextDecoder().decode(created.bytes)};
  const plan={schema:'un.latent-plan.v1',base:{topic:'',start:'2026-09-22',end:'2026-09-28',region:'All regions',scope:'general_debate'},compare_parents:true,stability:{enabled:false,unit:'meeting',replicates:10,fraction:0.8,seed:31415},settings:['pca','lsa'].map(representation=>({label:representation+' synthetic baseline',method:'clusters',options:{representation,algorithm:'kmeans',components:4,k:2,neighbors:3,seed:42,umapSeed:42}}))};
  return {payload,plain:{kind:'corpus',text:source},plan,records,passages};
}
module.exports={fixture};
if(require.main===module){const fs=require('node:fs'),path=require('node:path');fixture(Number(process.argv[3]||6)).then(f=>{const out=process.argv[2];if(!out)throw Error('Usage: node tools/latent_fixture.cjs NEW_DIRECTORY [PARENTS]');fs.mkdirSync(out,{recursive:false});fs.writeFileSync(path.join(out,'reviewed.json'),f.payload.text);fs.writeFileSync(path.join(out,'corpus.json'),f.plain.text);fs.writeFileSync(path.join(out,'plan.json'),JSON.stringify(f.plan,null,2));console.log(JSON.stringify({synthetic:true,parents:f.records.length,passages:f.passages.length,output:out}));}).catch(e=>{console.error(e);process.exitCode=1;});}
