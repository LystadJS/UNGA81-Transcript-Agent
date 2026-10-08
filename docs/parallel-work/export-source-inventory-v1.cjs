#!/usr/bin/env node
'use strict';
/* Offline PRIVATE-only exporter. Does not fit, refit, download or publish sources. */
const fs=require('node:fs');
const path=require('node:path');
const {fromPanel,validateInventory}=require('./source-inventory-v1.cjs');
const ROOT=path.resolve(__dirname,'../..');
function option(args,key){
  const index=args.indexOf(key);
  return index<0?null:args[index+1];
}
function main(argv){
  const panelPath=option(argv,'--panel');
  const upstreamPath=option(argv,'--upstream');
  const outPath=option(argv,'--out');
  const legacyPath=option(argv,'--legacy');
  if(!panelPath||!upstreamPath||!outPath)throw Error('Required --panel --upstream --out');
  const resolved=[panelPath,upstreamPath,outPath,legacyPath].filter(Boolean).map(v=>path.resolve(v));
  const out=path.resolve(outPath);
  if(out===ROOT||out.startsWith(ROOT+path.sep))throw Error('Private original-source inventory output cannot enter public GitHub checkout');
  const panel=JSON.parse(fs.readFileSync(resolved[0],'utf8'));
  const upstream=JSON.parse(fs.readFileSync(resolved[1],'utf8'));
  if(panel.split!=='development'&&panel.split!=='synthetic')throw Error('Unsupported source population');
  const legacy=legacyPath?JSON.parse(fs.readFileSync(path.resolve(legacyPath),'utf8')):null;
  const companion=fromPanel(panel,upstream,{legacy,
    legacyWithheldReason: legacy===null?
      'No source-bound v1 envelope: P2 upstream not approved by legacy source schema':null});
  const audit=validateInventory(companion,legacy);
  fs.writeFileSync(out,JSON.stringify(companion,null,2)+'\n',
    {flag:'wx',encoding:'utf8',mode:0o600});
  process.stdout.write(JSON.stringify({status:'private_source_inventory_exported',
    observations:audit.total,available:audit.available,unverified:audit.unverified,
    other_missing:audit.other_missing,legacy_binding:audit.legacy_binding,
    public_output:false,inference_eligible:false})+'\n');
}
try{main(process.argv.slice(2));}
catch(e){process.stderr.write('Inventory export refused: '+String(e.message||e).slice(0,220)+'\n');
  process.exitCode=2;}
