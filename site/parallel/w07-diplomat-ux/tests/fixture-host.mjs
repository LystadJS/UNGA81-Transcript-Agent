/** Explicit synthetic QA host. Loopback only, no arbitrary file serving or data imports. */
import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {randomBytes} from 'node:crypto';
import {makeHarness} from './fixtures.mjs';
import {verifyDependencies} from './verify_dependencies.mjs';
import {parseStrict,canonical,digest} from '../../../../research/integration/product_contracts/contracts.mjs';
const here=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(here,'../../../..');
export const PAGE='/site/parallel/w07-diplomat-ux/';
const TYPES={html:'text/html; charset=utf-8',css:'text/css; charset=utf-8',mjs:'text/javascript; charset=utf-8'};
const CSP="default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'none'; font-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'";
export async function startFixtureHost({port=0,qa=false}={}) {
  const dependencies=await verifyDependencies(),harness=await makeHarness(),qaToken=qa?randomBytes(24).toString('hex'):null;
  const routes=new Map(['index.html','app.mjs','styles.css','copy.mjs','controller.mjs','provider.mjs'].map(f=>[PAGE+f,path.join(ROOT,PAGE,f)]));
  for(const name of ['contracts.mjs','schemas.mjs'])routes.set('/research/integration/product_contracts/'+name,path.join(ROOT,'research/integration/product_contracts',name));
  let origin='',lastBundle=null;
  const server=http.createServer(async(req,res)=>{
    const reply=(status,value,type='application/json; charset=utf-8')=>{res.writeHead(status,{'Content-Type':type,'Cache-Control':'no-store','Content-Security-Policy':CSP,'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'});res.end(typeof value==='string'||Buffer.isBuffer(value)?value:canonical(value));};
    try {
      if(req.headers.host!==origin.slice(7)||req.headers.origin&&req.headers.origin!==origin){reply(403,{error:'origin_refused'});return;}
      const url=new URL(req.url,origin),p=url.pathname;
      if(url.search){reply(400,{error:'query_refused'});return;}
      const readJSON=async()=>{if(req.headers['content-type']!=='application/json')throw new Error('content_type');let size=0,chunks=[];for await(const chunk of req){size+=chunk.length;if(size>2097152)throw new Error('body_size');chunks.push(chunk);}return parseStrict(new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(chunks)));};
      if(req.method==='GET'&&(p===PAGE||routes.has(p))){const filename=routes.get(p===PAGE?PAGE+'index.html':p);reply(200,await readFile(filename),TYPES[filename.split('.').pop()]);return;}
      if(req.method==='GET'&&p==='/__u1__/catalog'){reply(200,await harness.catalog());return;}
      if(req.method==='POST'&&p==='/__u1__/resolve'){lastBundle=await harness.resolve(await readJSON());reply(200,lastBundle);return;}
      const trust=/^\/__u1__\/trust\/([a-f0-9]{64})$/.exec(p);
      if(req.method==='GET'&&trust){reply(200,await harness.getTrust(trust[1]));return;}
      const evidence=/^\/__u1__\/evidence\/([a-f0-9]{64})\/(e[0-9]+)$/.exec(p);
      if(req.method==='GET'&&evidence){reply(200,await harness.getEvidence(evidence[1],evidence[2]));return;}
      // QA controls are explicitly enabled, non-operational and never loaded by the application.
      if(qa&&req.method==='POST'&&p==='/__u1__/test-event'&&req.headers.authorization==='Bearer '+qaToken){const event=await readJSON();if(event.name==='revoke')harness.revoke();else if(event.name==='expire')harness.expire();else if(event.name==='reset')harness.reset();else if(event.name==='veto'&&lastBundle)await harness.veto(await digest(lastBundle.product));else throw new Error('event');reply(200,{ok:true});return;}
      reply(404,{error:'not_available'});
    }catch {reply(400,{error:'synthetic_request_refused'});}
  });
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',resolve);});origin=`http://127.0.0.1:${server.address().port}`;
  return {origin,url:origin+PAGE,qaToken,dependencies,harness,close:()=>new Promise(resolve=>server.close(resolve))};
}
if(process.argv[1]===fileURLToPath(import.meta.url)) {
  const args=process.argv.slice(2);if(args.some(a=>a!=='--qa'&&!/^--port=\d+$/.test(a)))throw new Error('Usage: node tests/fixture-host.mjs [--qa] [--port=0]');
  const host=await startFixtureHost({qa:args.includes('--qa'),port:Number(args.find(a=>a.startsWith('--port='))?.split('=')[1]||0)});
  console.log(JSON.stringify({url:host.url,origin:host.origin,qaToken:host.qaToken,dependencies:host.dependencies,synthetic_only:true,model_runs:0}));
  for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>host.close().then(()=>process.exit(0)));
}
