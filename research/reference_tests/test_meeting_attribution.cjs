'use strict';
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const {summarize}=require('./meeting_attribution_audit.cjs');
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const text='The speaker records a synthetic discussion of climate adaptation.';
const parent={id:'ga/c2/81/1#0',meeting_id:'ga/c2/81/1',split:'development',date:'2026-10-01',text,text_sha256:sha(text),
  country:'Fictionland',region:'Synthetic',body:'General Assembly',speaker_metadata:{affiliation_full:'Fictionland',function:'Representative',group:null}};
const template=()=>({schema:'un.passage-corpus.v1',sha256:'test-engineering-only',frame:{holdout_state:'reserved_not_downloaded'},parents:[parent],passages:[{id:parent.id+'@0:5',parent_id:parent.id,split:'development',date:parent.date}]});
let n=0;function check(name,fn){fn();n++;console.log('PASS',name)}
check('source segment and single passage counted once',()=>{const r=summarize(template(),{strictDigest:false});assert.equal(r.aggregate.source_segments,1);assert.equal(r.aggregate.source_passages,1);});
check('no invented distinct speakers',()=>{const r=summarize(template(),{strictDigest:false});assert.equal(r.aggregate.attribution.explicit_speaker_identifiers,0);assert.equal(r.aggregate.attribution.verified_distinct_persons,null);});
check('source-path agenda explicitly distinguished from actual agenda',()=>{const a=summarize(template(),{strictDigest:false}).aggregate;assert.equal(a.agenda.canonical_series_segments,1);assert.match(a.agenda.limitation,/not an independently verified/);});
check('affiliation plus function is only a proxy',()=>{const a=summarize(template(),{strictDigest:false}).aggregate;assert.equal(a.attribution.complete_affiliation_function_proxies,1);});
check('unknown identity never invented by repeated proxy',()=>{const x=template(),a={...parent,id:'ga/c2/81/2#0',meeting_id:'ga/c2/81/2'};x.parents.push(a);x.passages.push({...x.passages[0],parent_id:a.id});const r=summarize(x,{strictDigest:false});assert.equal(r.aggregate.attribution.proxy_values_crossing_meetings,1);assert.equal(r.aggregate.attribution.verified_distinct_persons,null);});
check('holdout date rejected',()=>{const x=template();x.parents[0]={...parent,date:'2026-10-05'};assert.throws(()=>summarize(x,{strictDigest:false}),/Nondevelopment/);});
check('wrong split rejected',()=>{const x=template();x.parents[0]={...parent,split:'holdout'};assert.throws(()=>summarize(x,{strictDigest:false}),/Nondevelopment/);});
check('source text tampering rejected',()=>{const x=template();x.parents[0]={...parent,text:'changed'};assert.throws(()=>summarize(x,{strictDigest:false}),/integrity/);});
check('orphan passage rejected',()=>{const x=template();x.passages[0]={...x.passages[0],parent_id:'made-up#1'};assert.throws(()=>summarize(x,{strictDigest:false}),/Unexpected passage/);});
check('changed frozen digest rejected',()=>{assert.throws(()=>summarize(template()),/digest/);});
check('reserved frame state required',()=>{const x=template();x.frame.holdout_state='collected';assert.throws(()=>summarize(x,{strictDigest:false}),/not reserved/);});
console.log(JSON.stringify({status:'PASS',tests:n,synthetic:true}));
