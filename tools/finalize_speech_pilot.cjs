/* Fail closed on changed packets, incomplete choices, overlaps and disputed audio. */
const fs=require('node:fs'),path=require('node:path'),C=require('../site/passage-pilot-core.js');
(async()=>{const [packet,review,out]=process.argv.slice(2);if(!out)throw Error('Usage: node finalize_speech_pilot.cjs packet.json review.json new-output-directory');
 const ctx=await C.load(fs.readFileSync(packet)),choices=JSON.parse(fs.readFileSync(review,'utf8')),units=await C.derive(ctx,choices);
 fs.mkdirSync(out,{recursive:false});fs.writeFileSync(path.join(out,'reviewed-speech-units.json'),JSON.stringify(units,null,2)+'\n');
 fs.copyFileSync(review,path.join(out,'review.json'));console.log(JSON.stringify({status:'PASS',approved_units:units.records.length,withheld:units.withheld.length,originals_changed:false}));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
