/* Builds a private, self-contained import in a new output directory. */
const fs=require('node:fs'),path=require('node:path'),R=require('../site/reviewed-units.js'),A=require('../site/analysis-core.js');
(async()=>{
  const [source,packet,review,out]=process.argv.slice(2);
  if(!out)throw Error('Usage: node prepare_reviewed_analysis.cjs original-corpus.json packet.json saved-review.json NEW_OUTPUT_DIRECTORY');
  const read=p=>new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(fs.readFileSync(p));
  const result=await R.create(read(source),read(packet),read(review),A.validateCorpus);
  fs.mkdirSync(out,{recursive:false});
  fs.writeFileSync(path.join(out,'reviewed-analysis.json'),result.bytes);
  for(const [name,data] of [['reviewed-speech-units',result.units],['audio-review-ledger',result.ledger],['import-summary',result.corpus.reviewed_units]])
    fs.writeFileSync(path.join(out,name+'.json'),JSON.stringify(data,null,2)+'\n');
  console.log(JSON.stringify({status:'PASS',...result.corpus.reviewed_units.input,audio:result.corpus.reviewed_units.audio_decisions,originals_changed:false}));
})().catch(e=>{console.error(e);process.exitCode=1;});
