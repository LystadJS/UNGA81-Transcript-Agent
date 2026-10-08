'use strict';
/*
 * Optional real-Chromium, no-npm browser acceptance.
 * Run from any directory: node site/parallel/w05-browser/experimental/method-lab/test-browser.cjs
 * Requires Node 22+ and chromium on PATH (or BROWSER_BIN); no internet.
 */
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const http=require('node:http');
const {setTimeout:delay}=require('node:timers/promises');
const UNClusters=require('../../../cluster-core.js');
const UNLSA=require('../../../lsa-core.js');

const SITE=path.resolve(__dirname,'../../../');
const PREFIX='/parallel/w05-browser/experimental/method-lab/';
const MIME={'.js':'text/javascript','.json':'application/json','.html':'text/html','.css':'text/css'};
const server=http.createServer((req,res)=>{
  const url=new URL(req.url,'http://localhost');
  const pathname=decodeURIComponent(url.pathname);
  const full=path.resolve(SITE,'.'+pathname);
  if(full!==SITE && !full.startsWith(SITE+path.sep)){
    res.writeHead(403);res.end('Forbidden');return;
  }
  const stat=fs.existsSync(full)?fs.statSync(full):null;
  if(!stat?.isFile()){res.writeHead(404);res.end('Not found');return;}
  res.writeHead(200,{'content-type':MIME[path.extname(full)]||'text/plain',
    'cache-control':'no-store','access-control-allow-origin':'none'});
  fs.createReadStream(full).pipe(res);
});
function listen(){
  return new Promise(resolve=>server.listen(0,'127.0.0.1',()=>resolve(server.address().port)));
}
async function awaitFile(filename) {
  for(let i=0;i<100;i++){
    if(fs.existsSync(filename)&&fs.statSync(filename).size>3)return fs.readFileSync(filename,'utf8').split('\n')[0].trim();
    await delay(100);
  }
  throw new Error('Chromium did not start a remote debugging port.');
}
class CDP {
  constructor(url) {
    this.ws=new WebSocket(url);
    this.seq=0;this.pending=new Map();this.listeners=new Map();
    this.ready=new Promise((resolve,reject)=>{
      this.ws.onopen=resolve;
      this.ws.onerror=reject;
    });
    this.ws.onmessage=message=>{
      const payload=JSON.parse(message.data);
      if(payload.id){
        const task=this.pending.get(payload.id);
        if(!task)return;
        this.pending.delete(payload.id);
        if(payload.error)task.reject(new Error(JSON.stringify(payload.error)));
        else task.resolve(payload.result||{});
      }else{
        const listeners=this.listeners.get(payload.method)||[];
        for(const callback of listeners)callback(payload.params||{});
      }
    };
  }
  on(method,fn) {this.listeners.set(method,[...(this.listeners.get(method)||[]),fn]);}
  async send(method,params={}) {
    await this.ready;
    const id=++this.seq;
    return new Promise((resolve,reject)=>{
      this.pending.set(id,{resolve,reject});
      this.ws.send(JSON.stringify({id,method,params}));
    });
  }
  async evaluate(expression) {
    const result=await this.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
    if(result.exceptionDetails)throw new Error(result.exceptionDetails.text);
    return result.result?.value;
  }
  async until(expression,timeout=15000) {
    const start=Date.now();
    while(Date.now()-start<timeout){
      if(await this.evaluate(expression))return true;
      await delay(80);
    }
    throw new Error('Browser assertion timed out: '+expression);
  }
  close(){this.ws.close();}
}
async function main(){
  const port=await listen();
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),'un-method-lab-chromium-'));
  const bin=process.env.BROWSER_BIN || 'chromium';
  const child=spawn(bin,[
    '--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
    '--no-first-run','--no-default-browser-check',
    '--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'
  ],{stdio:'ignore'});
  let cdp;
  try{
    const chromePort=await awaitFile(path.join(profile,'DevToolsActivePort'));
    const pages=await fetch('http://127.0.0.1:'+chromePort+'/json/list').then(r=>r.json());
    const page=pages.find(p=>p.type==='page');
    assert.ok(page?.webSocketDebuggerUrl,'Expected a remote-debuggable browser page.');
    cdp=new CDP(page.webSocketDebuggerUrl);
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    await cdp.send('Network.enable');
    const outside=[],exceptions=[];
    cdp.on('Network.requestWillBeSent',p=>{
      if(!p.request.url.startsWith('http://127.0.0.1:'+port+'/') &&
        !p.request.url.startsWith('data:') &&
        !p.request.url.startsWith('about:'))outside.push(p.request.url);
    });
    cdp.on('Runtime.exceptionThrown',p=>exceptions.push(p.exceptionDetails?.text||'Unknown exception'));
    // Browser Worker and Node use the exact same synthetic vectors. Compare the
    // retained numerical score matrices, not UMAP's visualization coordinates.
    const raw=[
      new Map([['alpha',1],['beta',.4]]),
      new Map([['alpha',.8],['beta',.3]]),
      new Map([['gamma',1],['delta',.4]]),
      new Map([['gamma',.8],['delta',.3]])
    ];
    const expected={pca:UNClusters.pca(raw,2).scores,lsa:UNLSA.lsa(raw,2).scores};
    const snapshots=[];
    for(const [name,width,height,mobile] of [['desktop',1440,900,false],['mobile',390,844,true]]){
      await cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:mobile?2:1,mobile});
      await cdp.send('Page.navigate',{url:'http://127.0.0.1:'+port+PREFIX+'index.html'});
      await cdp.until("document.readyState==='complete' && !!document.querySelector('#example')");
      if(name==='desktop') {
    const browserScores=await cdp.evaluate("(async()=>{const w=new Worker('"+PREFIX+"worker.js');const result=await new Promise((resolve,reject)=>{w.onerror=e=>reject(new Error(e.message));w.onmessage=e=>{if(e.data.type==='result')resolve(e.data);if(e.data.type==='error')reject(new Error(e.data.message));};w.postMessage({id:731,action:'numeric_probe'});});w.terminate();return result.scores;})()");
    for(const method of ['pca','lsa']){
      assert.equal(browserScores[method].length,expected[method].length);
      for(let i=0;i<expected[method].length;i++){
        assert.equal(browserScores[method][i].length,expected[method][i].length);
        for(let j=0;j<expected[method][i].length;j++)
          assert.ok(Math.abs(browserScores[method][i][j]-expected[method][i][j])<1e-7,
            method+' Node/Chromium score mismatch at '+i+','+j);
      }
    }
      }

      const started=Date.now();
      await cdp.evaluate("document.querySelector('#example').click()");
      await cdp.until("!document.querySelector('#results').hidden && !!document.querySelector('#observations table tbody tr')");
      const rendered=await cdp.evaluate("({rows:document.querySelectorAll('#observations tbody tr').length, models:document.querySelectorAll('#left option').length, overflow:document.documentElement.scrollWidth > window.innerWidth + 2, status:document.querySelector('#status').textContent, compare:document.querySelector('#comparison').textContent})");
      assert.equal(rendered.rows,5);
      assert.equal(rendered.models,3);
      assert.equal(rendered.overflow,false,'Unexpected document-level horizontal overflow.');
      assert.match(rendered.compare,/Same source population/);
      await cdp.evaluate("document.querySelector('#observations tbody button').click()");
      assert.equal(await cdp.evaluate("document.querySelector('#inspection').textContent.includes('Text SHA-256')"),true);
      await cdp.evaluate("document.querySelector('#authorize').click()");
      const stale=await cdp.evaluate("({hidden:document.querySelector('#results').hidden, disabled:document.querySelector('#export').disabled})");
      assert.deepEqual(stale,{hidden:true,disabled:true},'Settings must invalidate prior exports.');
      snapshots.push({viewport:name,width,height,fixture_load_ms:Date.now()-started,observations:rendered.rows,
        methods:rendered.models,horizontal_overflow:false,source_inspection:true,stale_export_blocked:true});
    }
    assert.deepEqual(outside,[],'Unexpected external transmission.');
    assert.deepEqual(exceptions,[],'Uncaught browser exceptions.');
    console.log(JSON.stringify({status:'PASS',test:'isolated_method_lab_chromium',snapshots,
      external_requests:outside.length,exceptions:exceptions.length,numeric_parity:['pca','lsa']},null,2));
  } finally {
    cdp?.close();
    child.kill('SIGTERM');
    await new Promise(resolve=>server.close(resolve));
    fs.rmSync(profile,{recursive:true,force:true});
  }
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
