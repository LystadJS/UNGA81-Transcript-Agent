/** Coordinator test host: prebuilt fictional metadata only; no real evidence service. */
import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {randomBytes} from 'node:crypto';
const u2=resolve(process.env.U2_CHECKOUT),u1=resolve(process.env.U1_CHECKOUT);
const load=p=>import(pathToFileURL(resolve(u2,p)).href);
const {environment,select}=await load('research/integration/question_router/tests/fixtures.mjs');
const {createU1Provider}=await load('research/integration/question_router/router.mjs');
const {parseStrict}=await load('research/integration/product_contracts/contracts.mjs');
const e=await environment();
// Prebuild a bounded fictional catalogue, before accepting any browser request.
for(const country of [null,'BRA','CAN','USA'])for(const topic of [null,'climate','peace','development']) {
  for(const period of [null,{start:'2024-09-23',end:'2024-09-23'},{start:'2024-09-24',end:'2024-09-24'}])await e.register(select({country,topic,period}));
  for(const meeting of ['01','1'])await e.register(select({page:'meetings',meeting,country,topic,period:null}));
}
const router=await e.router(),provider=createU1Provider(router),control=randomBytes(24).toString('hex');
const assets=new Map();
for(const file of ['index.html','styles.css','app.mjs','controller.mjs','copy.mjs','provider.mjs'])assets.set('/site/parallel/w07-diplomat-ux/'+file,resolve(u1,'site/parallel/w07-diplomat-ux',file));
for(const file of ['contracts.mjs','schemas.mjs'])assets.set('/research/integration/product_contracts/'+file,resolve(u2,'research/integration/product_contracts',file));
let origin='';
const server=http.createServer(async(req,res)=>{
  res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');
  res.setHeader('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'none'; font-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'");
  const send=(code,value)=>{res.writeHead(code,{'Content-Type':'application/json'});res.end(JSON.stringify(value));};
  try {
    if(req.headers.host!==new URL(origin).host || req.headers.origin && req.headers.origin!==origin)return send(403,{error:'host'});
    const url=new URL(req.url,origin);if(url.search)return send(404,{error:'path'});
    if(req.method==='GET' && assets.has(url.pathname)){
      const file=assets.get(url.pathname),bytes=await readFile(file);
      res.writeHead(200,{'Content-Type':file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.css')?'text/css':'text/javascript'});res.end(bytes);return;
    }
    if(req.method==='GET' && url.pathname==='/__u1__/catalog')return send(200,await provider.catalog());
    if(req.method==='GET' && /^\/__u1__\/trust\/[a-f0-9]{64}$/.test(url.pathname))return send(200,await provider.getTrust(url.pathname.split('/').at(-1)));
    if(req.method==='GET' && url.pathname==='/__u2__/stats')return send(200,{lookups:e.state.lookups,model_runs:0});
    let body='';for await(const chunk of req){body+=chunk;if(Buffer.byteLength(body)>8192)return send(413,{error:'size'});}
    if(req.method==='POST' && url.pathname==='/__u1__/resolve')return send(200,await provider.resolve(parseStrict(body)));
    if(req.method==='POST' && url.pathname==='/__u2__/revoke' && req.headers['x-review-token']===control){e.state.revoked=true;e.state.revision++;return send(200,{revoked:true});}
    return send(404,{error:'not_connected'});
  } catch {send(422,{error:'synthetic_product_unavailable'});}
});
server.listen(0,'127.0.0.1',()=>{origin='http://127.0.0.1:'+server.address().port;console.log(JSON.stringify({origin,url:origin+'/site/parallel/w07-diplomat-ux/index.html',control,synthetic_only:true}));});
process.on('SIGTERM',()=>server.close(()=>process.exit(0)));
