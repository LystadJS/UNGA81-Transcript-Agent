/** Identity checks, not independent source authenticity or full-checkout execution claims. */
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
const root=fileURLToPath(new URL('../../../../',import.meta.url));
const lock=JSON.parse(await readFile(new URL('../dependency-lock.json',import.meta.url),'utf8'));
async function verify(base,entries) {
  for(const entry of entries) {
    const bytes=await readFile(resolve(base,entry.path));
    assert.equal(createHash('sha256').update(bytes).digest('hex'),entry.sha256,entry.path+' SHA256');
    assert.equal(createHash('sha1').update(Buffer.concat([Buffer.from(`blob ${bytes.length}\0`),bytes])).digest('hex'),entry.git_blob,entry.path+' Git blob');
  }
}
await verify(root,lock.base_dependencies);
let u1=0;
if(process.argv.includes('--with-u1')) {
  assert.ok(process.env.U1_CHECKOUT,'U1_CHECKOUT is mandatory for consumer checks');await verify(process.env.U1_CHECKOUT,lock.u1_dependencies);u1=lock.u1_dependencies.length;
}
console.log(JSON.stringify({c0:lock.c0_head,verified_base_files:lock.base_dependencies.length,u1:lock.u1_head,verified_u1_files:u1}));
