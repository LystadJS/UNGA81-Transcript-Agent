#!/usr/bin/env node
'use strict';
// Private by default: STDOUT contains aggregate diagnostics only, never source text or row IDs.
const fs=require('node:fs');
const path=require('node:path');
const cp=require('node:child_process');
const {run,publicAggregate}=require('./runner.cjs');
const {toInterchangeV1}=require('./interchange.cjs');
const {makeFixture,SETTINGS}=require('./examples/synthetic_fixture.cjs');
const ROOT=path.resolve(__dirname,'../..');
function option(args,name){const i=args.indexOf(name);return i>=0?args[i+1]:null;}
function verifiedCache(frame,cache,python){
  const p=cp.spawnSync(python||'python3',[path.join(__dirname,'pinned_cache.py'),'--cache',cache],{
    input:JSON.stringify(frame),encoding:'utf8',maxBuffer:24*1024*1024,timeout:120000,
    env:{...process.env,PYTHONNOUSERSITE:'1',HF_HUB_OFFLINE:'1',TRANSFORMERS_OFFLINE:'1'}});
  if(p.error||p.status!==0)throw Error('Pinned-cache verification refused: '+String(p.error?.message||p.stderr||'unknown').slice(0,300));
  return JSON.parse(p.stdout);
}
async function main(args){
  const synthetic=args.includes('--synthetic'),file=option(args,'--input');
  if(synthetic===Boolean(file))throw Error('Choose exactly one: --synthetic or --input <private-development-frame.json>');
  const fixture=synthetic?makeFixture():null;
  const frame=synthetic?fixture.frame:JSON.parse(fs.readFileSync(file,'utf8'));
  const saved=synthetic?fixture.saved:option(args,'--cache')?verifiedCache(frame,option(args,'--cache'),option(args,'--python')):null;
  const settings=synthetic?SETTINGS:JSON.parse(fs.readFileSync(option(args,'--settings')||'', 'utf8'));
  const result=await run(frame,settings,{saved,replicates:Number(option(args,'--replicates')||10),
    group_seed:Number(option(args,'--seed')||31415)});
  const privatePath=option(args,'--private-output');
  if(frame.split==='development'){
    if(!privatePath)throw Error('Development exports require --private-output outside the public repository.');
    const target=path.resolve(privatePath);
    if(target===ROOT||target.startsWith(ROOT+path.sep))throw Error('Private output must be outside the public repository.');
    fs.writeFileSync(target,JSON.stringify({interchange:toInterchangeV1(result),
      comparisons:result.comparisons,source_linked_cases:result.source_linked_cases,
      source_audit:result.source_audit,model_reports:result.model_reports},null,2),{encoding:'utf8',flag:'wx',mode:0o600});
    process.stdout.write(JSON.stringify({status:'private-development-complete',models:result.fit_records.length,
      failures:result.failure_ledger.length,public_export:false})+'\n');
    return;
  }
  if(args.includes('--interchange'))process.stdout.write(JSON.stringify(toInterchangeV1(result),null,2)+'\n');
  else process.stdout.write(JSON.stringify(publicAggregate(result),null,2)+'\n');
}
main(process.argv.slice(2)).catch(e=>{process.stderr.write('Validation refused: '+String(e.message||e).slice(0,300)+'\n');process.exitCode=1;});
