import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const here=path.dirname(fileURLToPath(import.meta.url));
export async function verifyDependencies(root=path.resolve(here,'../../../..')) {
  const lock=JSON.parse(await readFile(path.join(here,'../dependency-lock.json'),'utf8'));
  if(lock.c0_commit!=='884097997f89b0040e4418480378f077e3b65434')throw new Error('wrong_c0_pin');
  for(const file of lock.files){const bytes=await readFile(path.join(root,file.path));const blob=createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex');const sha=createHash('sha256').update(bytes).digest('hex');if(blob!==file.git_blob||sha!==file.sha256)throw new Error('dependency_drift:'+file.path);}
  return {c0:lock.c0_commit,verified_files:lock.files.length};
}
if(process.argv[1]===fileURLToPath(import.meta.url))console.log(JSON.stringify(await verifyDependencies()));
