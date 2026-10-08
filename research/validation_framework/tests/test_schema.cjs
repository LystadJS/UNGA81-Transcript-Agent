'use strict';
// Standalone strict structural validator for the coordinator's JSON Schema subset.
// Does not modify, intercept or bypass the shared contract fixture tests.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {makeFixture,SETTINGS}=require('../examples/synthetic_fixture.cjs');
const {run}=require('../runner.cjs');
const {toInterchangeV1}=require('../interchange.cjs');
const ROOT=path.resolve(__dirname,'../../..');
const read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
const schema=read('docs/parallel-work/interchange-v1.schema.json');
const inputSchema=read('research/validation_framework/schemas/input-frame.v1.schema.json');
const fitSchema=read('research/validation_framework/schemas/fit-record.v1.schema.json');
function isObject(x){return x!==null&&typeof x==='object'&&!Array.isArray(x);}
function validate(def,val,p='$'){
  if(def.anyOf){const accepted=def.anyOf.some(option=>{try{validate(option,val,p);return true;}catch{return false;}});
    assert(accepted,p+': no matching anyOf');}
  if(Object.prototype.hasOwnProperty.call(def,'const'))assert.deepEqual(val,def.const,p+': const');
  if(def.enum)assert(def.enum.includes(val),p+': invalid enum '+String(val));
  if(def.type){
    const allowed=Array.isArray(def.type)?def.type:[def.type];
    assert(allowed.some(t=>t==='null'?val===null:t==='object'?isObject(val):
      t==='array'?Array.isArray(val):t==='integer'?Number.isSafeInteger(val):
      t==='number'?typeof val==='number'&&Number.isFinite(val):typeof val===t),p+': type');}
  if(typeof val==='string'){
    if(def.minLength!==undefined)assert(val.length>=def.minLength,p+': minLength');
    if(def.pattern)assert(new RegExp(def.pattern).test(val),p+': pattern');
    if(def.format==='date-time')assert(!Number.isNaN(Date.parse(val))&&/[zZ]|[+-]\d\d:\d\d$/.test(val),p+': timestamp');
  }
  if(typeof val==='number'){
    if(def.minimum!==undefined)assert(val>=def.minimum,p+': minimum');
    if(def.maximum!==undefined)assert(val<=def.maximum,p+': maximum');
  }
  if(Array.isArray(val)){
    if(def.minItems!==undefined)assert(val.length>=def.minItems,p+': minItems');
    if(def.maxItems!==undefined)assert(val.length<=def.maxItems,p+': maxItems');
    if(def.items)val.forEach((x,i)=>validate(def.items,x,p+'['+i+']'));
  }
  if(isObject(val)){
    (def.required||[]).forEach(k=>assert(Object.prototype.hasOwnProperty.call(val,k),p+': missing '+k));
    for(const [key,value] of Object.entries(val)){
      if(def.properties&&Object.prototype.hasOwnProperty.call(def.properties,key))validate(def.properties[key],value,p+'.'+key);
      else if(def.additionalProperties===false)assert.fail(p+': unknown property '+key);
    }
  }
  return true;
}
async function main(){
  const {frame,saved}=makeFixture();
  validate(inputSchema,frame);
  const output=await run(frame,SETTINGS,{saved,replicates:10});
  const v1=toInterchangeV1(output);
  assert(validate(schema,v1),'v1 structural validation failed');
  for(const fit of output.fit_records)assert(validate(fitSchema,fit),'fit record schema failed');
  const cases=[
    ['invalid upstream source',x=>x.upstream.source_schema='invented'], 
    ['non-contract weighting',x=>x.cohort.weighting='equal_observation'], 
    ['non-contract group',x=>x.cohort.source_group_unit='meeting_and_affiliation'], 
    ['invalid missing status',x=>x.observations[0].source_status='missing_is_zero'],
    ['corrupted hash',x=>x.results[0].representation_basis_id=null],
    ['private text leakage',x=>x.observations[0].text='unwanted raw transcript']
  ];
  for(const [label,mutate] of cases){
    const bad=structuredClone(v1);mutate(bad);
    assert.throws(()=>validate(schema,bad),undefined,'Failed to reject '+label);
  }
  const invalid=structuredClone(frame);invalid.observations[0].text_sha256='not-a-hash';
  assert.throws(()=>validate(inputSchema,invalid));
  const invalidFit=structuredClone(output.fit_records[0]);invalidFit.representation_identity_sha256='invalid';
  assert.throws(()=>validate(fitSchema,invalidFit));
  process.stdout.write(JSON.stringify({suite:'W1-source-schema',shared_contract_schema:'un.parallel-analysis.v1',
    positive_envelope:1,input_frame_valid:1,fit_records_valid:output.fit_records.length,negative:8,
    failed:0,transcript_text_access:false})+'\n');
}
main().catch(e=>{process.stderr.write('FAIL '+(e.stack||e)+'\n');process.exitCode=1;});
