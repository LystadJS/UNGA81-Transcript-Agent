'use strict';
// Independent Node source-bound replay of every exact fictional build result.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const u=require('../read_model.cjs');
const dir=process.argv[2];assert(dir,'A synthetic build directory is required');
const raw=n=>fs.readFileSync(path.join(dir,n));
const manifest=JSON.parse(raw('manifest.json')),cat=JSON.parse(raw('catalogue.json')),proof=JSON.parse(raw('verification.json'));
for(const [name,expected] of Object.entries(manifest.files)) {
  assert(['index.html','catalogue.json','verification.json'].includes(name));
  assert.equal(crypto.createHash('sha256').update(raw(name)).digest('hex'),expected);
}
const withoutHash=Object.fromEntries(Object.entries(cat).filter(([k])=>k!=='sha256'));
assert.equal(u.digest(withoutHash),cat.sha256);
assert.equal(cat.phase1_head,'81110db49786a05f9c8f8ce4d5103c92fe255586');
assert.equal(cat.scenes.length,8);assert.equal(proof.length,8);
const pins={'us_reference.py':'e33b4b40fbe18ab98365501cad45d9529b104d33','arithmetic.R':'0fe4748d88d8ea95a4c6f9422d47239e823f933c',
  'make_schema.py':'fbdaabf88655d42f491f129770bb2b6bfe705161','read_model.cjs':'2416e015a86e41edaac4e6115b84a5eca137a32b',
  'schema_contract.py':'41b425822b2846a182c24ca83a8428de390938cb','schema_contract.cjs':'619fc82887d6a14e196468484dbd07e631d7d966'};
for(const [name,expected] of Object.entries(pins)) {
  const b=fs.readFileSync(path.join(__dirname,'..',name));
  assert.equal(crypto.createHash('sha1').update(Buffer.from(`blob ${b.length}\0`)).update(b).digest('hex'),expected,'Phase 1 changed: '+name);
}
for(const scene of cat.scenes){const v=proof.find(v=>v.id===scene.id);assert(v);u.validateFigureModel(v.model,v.source,v.receipt);
  assert.equal(u.digest(v.model),u.digest(scene.model));assert.equal(scene.model.split,'synthetic');assert.equal(scene.model.permissions.publication_eligible,false);}
console.log(JSON.stringify({suite:'phase2-source-bound-node-replay',scenarios:8,result:'pass',phase1_pins:6,publication_eligible:false}));
