/** Emit reproducible source-free schemas/examples; never emit authority keys. */
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {SCHEMAS,VERSION,canonical,validateProduct} from './contracts.mjs';
import {examples} from './fixtures.mjs';
const here=dirname(fileURLToPath(import.meta.url));
const out=resolve(process.argv[2] || (()=>{throw new Error('Explicit output directory required');})());
const files={};
for(const [name,schema] of Object.entries(SCHEMAS)) files[`${name}.schema.json`]=canonical(schema)+'\n';
const cases=await examples();
for(const f of Object.values(cases)) await validateProduct(f.product,f.query,f.capability);
files['examples.json']=canonical(cases)+'\n';
const hashes=Object.fromEntries(Object.entries(files).map(([name,text])=>[name,createHash('sha256').update(text).digest('hex')]));
const lock={contract_version:VERSION,kind:'synthetic_interface_candidate_not_scientific_freeze',files:hashes};
if(process.argv.includes('--write-lock')) await writeFile(resolve(here,'interface-lock.json'),JSON.stringify(lock,null,2)+'\n',{flag:'wx'});
else {
  const expected=JSON.parse(await readFile(resolve(here,'interface-lock.json'),'utf8'));
  if(canonical(expected)!==canonical(lock)) throw new Error('Interface drift: version/review required; do not overwrite lock automatically');
}
await mkdir(out,{recursive:true});
for(const [name,text] of Object.entries(files)) await writeFile(resolve(out,name),text,{flag:'wx'});
await writeFile(resolve(out,'interface-lock.json'),JSON.stringify(lock,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({schema_files:Object.keys(SCHEMAS).length,examples:Object.keys(cases).length,sha256:hashes,publication_eligible:false}));
