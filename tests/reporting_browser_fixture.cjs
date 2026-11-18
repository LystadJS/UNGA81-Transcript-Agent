/* Shared personal/CI harness; never included in the government-browser app. */
'use strict';
const fs=require('node:fs'),http=require('node:http'),path=require('node:path');

async function startServer({root=path.resolve(__dirname,'../site'),html}={}){
 root=path.resolve(root);
 const server=http.createServer((req,res)=>{
  const rendered=html?.(req.url);
  if(rendered!==undefined){res.setHeader('Content-Type','text/html');res.end(rendered);return;}
  const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);
  if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
  try{
   res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':file.endsWith('.json')?'application/json':'text/html');
   res.end(fs.readFileSync(file));
  }catch{res.writeHead(404);res.end();}
 });
 await new Promise((resolve,reject)=>{
  server.once('error',reject);
  server.listen(0,'127.0.0.1',()=>{server.off('error',reject);resolve();});
 });
 return server;
}

function launchBrowser(){
 const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
 return chromium.launch({headless:true,executablePath:process.env.BROWSER_PATH||'/usr/bin/chromium'});
}
module.exports={startServer,launchBrowser};
