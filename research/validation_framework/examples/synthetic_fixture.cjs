'use strict';
// Invented vocabulary and deterministic vectors. This fixture contains no UN speech.
const {digest}=require('../frame.cjs');
const TERMS=[
  'Harbor ferry cargo docks maritime vessels shipping port quay navigation',
  'Forest canopy oak nature wildlife ecology biodiversity reserves woodland',
  'Clinic nurse treatment vaccine medical patients doctors health hospital'
];
const MEETING_WORDS=['alpha','bravo','charlie','delta','echo','foxtrot'];
function makeFixture(){
  const observations=[],semanticRows=[];
  for(let meeting=0;meeting<6;meeting++)for(let affiliation=0;affiliation<4;affiliation++){
    const i=meeting*4+affiliation,id='synthetic-'+String(i+1).padStart(2,'0');
    const theme=(meeting+affiliation)%3;
    const text=TERMS[theme]+' invented example '+MEETING_WORDS[meeting]+' sample';
    const parent='fictional-parent-'+meeting+'-'+affiliation;
    observations.push({id,split:'synthetic',source_status:'available',exclusion_reasons:[],
      text,text_sha256:digest(text),parent_id:parent,parent_text_sha256:digest(parent),
      meeting_id:'fictional-meeting-'+meeting,source_family_id:'synthetic-family-'+meeting+'-'+affiliation,
      date:'2026-01-'+String(meeting+1).padStart(2,'0'),country:affiliation===3&&meeting===0?null:'synthetic-affiliation-'+affiliation,
      affiliation:affiliation===3&&meeting===0?null:'synthetic-affiliation-'+affiliation,
      genre:meeting%2?'fictional-dialogue':'fictional-address',role:affiliation%2?'fictional-respondent':'fictional-presenter',
      review_status:'not_applicable',source_url:null,json_pointer:'/imaginary/'+i,start:0,end:[...text].length,unit:'synthetic'});
    // Deliberately does not exactly reproduce the lexical groupings.
    const g=(Math.floor(i/3)+affiliation)%3;
    const vector=Array.from({length:8},(_,d)=>((d%3===g)?2:0.1)+(i%4)*0.015+(d*0.004));
    semanticRows.push({id,text_sha256:digest(text),vector});
  }
  observations.push({id:'synthetic-unavailable',split:'synthetic',source_status:'unavailable',
    exclusion_reasons:['source_not_collected'],text_sha256:null,parent_id:null,parent_text_sha256:null,
    meeting_id:'fictional-meeting-6',date:'2026-01-07',country:null,
    source_url:null,unit:'synthetic',start:null,end:null,review_status:'not_applicable',
    missing_reason:'Fictional missing source; never code as zero mentions'});
  return {frame:{schema:'un.source-validation.frame.v1',split:'synthetic',
    source_schema:'un.source-validation.synthetic.v1',
    source_engine:'synthetic-generated-only',source_hash_basis:'synthetic',
    source_sha256:digest('fictional-source-record-v1'),unit:'synthetic',inventory_meetings:7,
    observations},saved:{id:'synthetic-minilm-control-v1',version:'1.0.0',
    kind:'synthetic-saved',identity_sha256:digest('synthetic-embedding-fixture'),
    rows:semanticRows}};
}
const SETTINGS=[
  {id:'lexical-lsa-kmeans',representation:'lsa',algorithm:'kmeans',components:4,k:3,seed:17},
  {id:'lexical-pca-pam',representation:'pca',algorithm:'pam',components:4,k:3,seed:17},
  {id:'lexical-lsa-ward',representation:'lsa',algorithm:'hierarchical',linkage:'ward',components:4,k:3,seed:17},
  {id:'lexical-pca-gmm',representation:'pca',algorithm:'gmm',components:4,k:3,seed:17,
   gmm:{starts:2,maxIterations:60,regularization:0.001,tolerance:0.0001}},
  {id:'synthetic-semantic-hdbscan',representation:'minilm_pca',algorithm:'hdbscan',components:4,
   hdbscan:{minClusterSize:3,minSamples:2,selection:'eom'},seed:17}
];
module.exports={makeFixture,SETTINGS};
