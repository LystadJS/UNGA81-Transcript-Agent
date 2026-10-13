#!/usr/bin/env node
'use strict';
/*
 * Node 22, offline only. Results are fictional aggregate receipts, never
 * fitted original text or source-bearing row-level analysis.
 */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {lock}=require('./lock.cjs');
const {calibration}=require('./calibration.cjs');
const ROOT=path.resolve(__dirname,'../../../..');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const field=(args,key)=>{const i=args.indexOf(key);return i<0?null:args[i+1];};
function outputSafe(dir){
 if(typeof dir!=='string'||!dir.length)throw Error('--output <new-local-directory> required');
 const destination=path.resolve(dir);
 if(destination===ROOT||destination.startsWith(ROOT+path.sep))
   throw Error('Refuse local artifacts inside the source repository.');
 if(fs.existsSync(destination))throw Error('Refuse to overwrite an existing output directory.');
 return destination;
}
async function main(args){
 const frozen=lock();
 const mode=field(args,'--mode')||'smoke',output=outputSafe(field(args,'--output'));
 const ids=field(args,'--scenarios')?.split(',')||null;
 if(mode==='full_shard'&&!args.includes('--acknowledge-heavy-fictional-only'))
   throw Error('Full-shard simulation requires --acknowledge-heavy-fictional-only and offline CPU budget.');
 const opts={mode,scenarioIds:ids};
 if(mode==='full_shard'){
   opts.outerStart=Number(field(args,'--outer-start'));
   opts.outerCount=1;opts.referenceDraws=1999;
 }
 const result=await calibration(opts);
 if(result.protocol_sha256!==frozen.protocol_sha256||
   result.inferential_eligible!==false||result.reserved_transcripts_opened!==0||
   result.g01_g13_all_not_run!==true)
   throw Error('Frozen source/null inferential restrictions do not reconcile.');
 const totals={
   schema:'un.w1-w2.synthetic-null.receipt.v1',
   protocol_sha256:result.protocol_sha256,
   protocol_blob_sha1:result.protocol_git_blob_sha1,
   generator_kind:frozen.protocol.reference_generator.kind,
   mode:result.mode,
   status:'SYNTHETIC_ENGINEERING_PILOT_ONLY',
   scenarios:result.num_scenarios,
   attempted_worlds:result.worlds_attempted,
   delivered_worlds:result.worlds_delivered,
   withheld_worlds:result.worlds_withheld,
   attempted_reference_draws:result.attempted_reference_draws,
   successful_reference_draws:result.successful_reference_draws,
   failed_reference_draws:result.failed_reference_draws,
   empirical_inference_eligible:false,
   public_release_eligible:false,reference_model_calibrated_to_real_sources:false,
   gates_passed:0,gates_not_run:13,reserved_transcripts_opened:0,
   evaluated_dates:'invented-2000s-source-metadata-only',
   source_rows_exported:0,feature_vectors_exported:0,
   limitations:result.notes
 };
 const aggregates={
   schema:'un.w1-w2.synthetic-null.aggregates.v1',
   protocol_sha256:result.protocol_sha256,
   mode:result.mode,scenarios:result.scenarios,
   inferential_eligible:false
 };
 fs.mkdirSync(output,{recursive:false,mode:0o700});
 const contents={
   'receipt.json':JSON.stringify(totals,null,2)+'\n',
   'scenario-aggregates.json':JSON.stringify(aggregates,null,2)+'\n',
   'synthetic-pilot-diagnostics.json':JSON.stringify(result,null,2)+'\n'
 };
 const sha={};
 for(const [filename,text] of Object.entries(contents)){
   if(/"text"\s*:|"vector"\s*:|Harbor ferry cargo|UNGA speech|2026-10-0[56]/.test(text))
     throw Error('Unsafe original or raw text representation attempted in synthetic output.');
   const bytes=Buffer.from(text,'utf8');
   fs.writeFileSync(path.join(output,filename),bytes,{encoding:undefined,flag:'wx',mode:0o600});
   sha[filename]=hash(bytes);
 }
 fs.writeFileSync(path.join(output,'SHA256.json'),JSON.stringify(sha,null,2)+'\n',
   {encoding:'utf8',flag:'wx',mode:0o600});
 process.stdout.write(JSON.stringify(totals)+'\n');
}
if(require.main===module)main(process.argv.slice(2))
 .catch(e=>{process.stderr.write('WITHHELD: '+String(e.message||e).slice(0,700)+'\n');process.exitCode=1;});
module.exports={main,outputSafe};
