'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),http=require('node:http');
const previousModule=process.env.PLAYWRIGHT_MODULE;
process.env.PLAYWRIGHT_MODULE='/unavailable-playwright-for-server-contract';
const {startServer}=require('./reporting_browser_fixture.cjs');
const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'reporting-server-')),root=path.join(temporary,'site');
let server;
(async()=>{
 fs.mkdirSync(root);fs.writeFileSync(path.join(temporary,'private.txt'),'FICTIONAL-OUTSIDE-CONTENT');
 const fixtures={'app.js':['text/javascript','const text="Fictional 😀";'],'app.css':['text/css','body{color:black}'],'data.json':['application/json','{"fictional":true}'],'page.html':['text/html','<p>Fictional page</p>']};
 for(const [name,[,body]] of Object.entries(fixtures))fs.writeFileSync(path.join(root,name),body);
 let downloaded='<p>Script-free fictional reading copy</p>';
 server=await startServer({root,html:url=>url==='/downloaded-report.html'?downloaded:undefined});
 assert.equal(server.address().address,'127.0.0.1');assert(server.address().port>0);
 const base='http://127.0.0.1:'+server.address().port;
 for(const [name,[type,body]] of Object.entries(fixtures)){
  const response=await fetch(base+'/'+name+'?v=fixture');assert.equal(response.status,200);assert.equal(response.headers.get('content-type'),type);assert.equal(await response.text(),body);
 }
 const dynamic=await fetch(base+'/downloaded-report.html');assert.equal(dynamic.headers.get('content-type'),'text/html');assert.equal(await dynamic.text(),downloaded);
 downloaded=undefined;assert.equal((await fetch(base+'/downloaded-report.html')).status,404);assert.equal((await fetch(base+'/missing.json')).status,404);assert.equal((await fetch(base+'/')).status,403);
 for(const target of ['/../private.txt','/..%2fprivate.txt','/%2e%2e/private.txt']){
  const response=await new Promise((resolve,reject)=>{http.get(base,{path:target},res=>{let body='';res.setEncoding('utf8');res.on('data',x=>body+=x);res.on('end',()=>resolve({status:res.statusCode,body}));}).on('error',reject);});
  assert([403,404].includes(response.status));assert(!response.body.includes('FICTIONAL-OUTSIDE-CONTENT'));
 }
 console.log('PASS: shared loopback server, query-aware public MIME/UTF-8 bytes, dynamic reading copy, missing/root/traversal refusal and no Playwright dependency for HTTP contracts');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{
 if(server)await new Promise(resolve=>server.close(resolve));fs.rmSync(temporary,{recursive:true,force:true});
 if(previousModule===undefined)delete process.env.PLAYWRIGHT_MODULE;else process.env.PLAYWRIGHT_MODULE=previousModule;
});
