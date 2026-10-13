'use strict';
/* Offline disposable browser acceptance page. Never copied by build_pages. */
const fs=require('node:fs'),path=require('node:path');
const B=require('./w2_bridge.cjs');
const V=require('./evidence_renderer.cjs');
const root=path.resolve(__dirname,'../../..');
function preview(input,out){
  if(!input||!out)throw Error('Provide synthetic fixture and empty output directories.');
  const read=name=>JSON.parse(fs.readFileSync(path.join(input,name),'utf8'));
  const w2Envelope=read('w2-envelope.json'),w2Report=read('w2-report.json');
  const w2Panel=B.toW6Consensus(w2Report,w2Envelope);
  const w4Envelope=read('w4-envelope.json'),w4Panel=read('w4-panel.json');
  for(const [e,p] of [[w2Envelope,w2Panel],[w4Envelope,w4Panel]])
    V.renderPanel(e,p);
  fs.mkdirSync(out,{recursive:true});
  if(fs.readdirSync(out).length)throw Error('Preview destination is not empty.');
  // Preview uses the coordinator-only extension. The published W6 renderer
  // and browser Pages allowlist are unchanged by this engineering PR.
  fs.copyFileSync(path.join(__dirname,'evidence_renderer.cjs'),
    path.join(out,'evidence-viz.js'));
  fs.copyFileSync(path.join(root,'site/experimental/evidence-viz/styles.css'),
    path.join(out,'styles.css'));
  const pack=value=>JSON.stringify(value).replace(/</g,'\\u003c');
  fs.writeFileSync(path.join(out,'data.js'),
    'window.W2Bundle='+pack({envelope:w2Envelope,panel:w2Panel})+';\n'+
    'window.W4Bundle='+pack({envelope:w4Envelope,panel:w4Panel})+';\n');
  const runtime=[
    '(function(){',
    "'use strict';",
    'const V=window.UNEvidenceViz,views={};',
    'for(const [id,data] of Object.entries({w2:window.W2Bundle,w4:window.W4Bundle})){',
    "  views[id]=V.mount(document.getElementById(id+'-chart'),data.envelope,[data.panel])[0];",
    '}',
    "document.getElementById('qa-status').textContent='Two synthetic producers rendered; original fit and source identities preserved.';",
    'function save(name,body,type){',
    '  const href=URL.createObjectURL(new Blob([body],{type}));',
    "  const a=document.createElement('a');a.href=href;a.download=name;document.body.append(a);a.click();a.remove();",
    '  setTimeout(()=>URL.revokeObjectURL(href),1000);',
    '}',
    "for(const button of document.querySelectorAll('[data-qa-export]')){",
    "  button.addEventListener('click',()=>{",
    "    const id=button.dataset.qaExport,type=button.dataset.type,view=views[id];",
    "    if(type==='svg')save(id+'.svg',view.svg,'image/svg+xml;charset=utf-8');",
    "    else save(id+'.html',V.htmlDocument(view),'text/html;charset=utf-8');",
    '  });',
    '}',
    '})();'
  ].join('\n');
  fs.writeFileSync(path.join(out,'preview.js'),runtime);
  const page=[
    '<!doctype html><html lang="en"><head><meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width,initial-scale=1">',
    '<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\'; style-src \'self\'; connect-src \'none\'; img-src \'self\' data:; object-src \'none\'">',
    '<title>W2/W4 → W6 synthetic validation</title><link rel="stylesheet" href="styles.css"></head>',
    '<body class="ev-demo"><header class="ev-masthead"><div>',
    '<p class="ev-overline">Coordinator source-contract QA</p>',
    '<h1>W2/W4 → W6 evidence compatibility</h1></div>',
    '<p class="ev-byline">Fictional identities, zero network requests, no published findings.</p></header>',
    '<main class="ev-wrap"><p class="ev-flag">SYNTHETIC ENGINEERING ONLY — NOT DIPLOMATIC EVIDENCE</p>',
    '<p id="qa-status" role="status" aria-live="polite">Validating source identities…</p>',
    '<div class="ev-toolbar">',
    '<button type="button" data-qa-export="w2" data-type="svg">Export W2 SVG</button>',
    '<button type="button" data-qa-export="w2" data-type="html">Export W2 HTML</button>',
    '<button type="button" data-qa-export="w4" data-type="svg">Export W4 SVG</button>',
    '<button type="button" data-qa-export="w4" data-type="html">Export W4 HTML</button>',
    '</div><div id="w2-chart"></div><div id="w4-chart"></div>',
    '<p class="ev-note">W2 agreement is not significance. W4 display positions are not political trajectories.</p>',
    '</main><script src="data.js"></script><script src="evidence-viz.js"></script>',
    '<script src="preview.js"></script></body></html>'
  ].join('\n');
  fs.writeFileSync(path.join(out,'index.html'),page);
  return {source:'synthetic',rendered:['consensus','longitudinal'],publication_eligible:false};
}
if(require.main===module){
  try{console.log(JSON.stringify(preview(process.argv[2],process.argv[3])));}
  catch(e){console.error(e.stack||e);process.exitCode=1;}
}
module.exports={preview};
