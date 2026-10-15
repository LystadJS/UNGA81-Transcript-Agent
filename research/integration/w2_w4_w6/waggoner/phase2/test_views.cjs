'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const v=require('./views.js');
assert(process.env.PHASE2_BUILD_DIR,'PHASE2_BUILD_DIR is required; no silent fixture fallback');
const catalogue=JSON.parse(fs.readFileSync(path.join(process.env.PHASE2_BUILD_DIR,'catalogue.json'),'utf8'));
const model=id=>catalogue.scenes.find(s=>s.id===id).model;
const original=JSON.stringify(catalogue);
test('eight bounded fictional scenarios retain strict nonrelease permissions',()=>{
 assert.equal(catalogue.scenes.length,8);
 for(const {model:m} of catalogue.scenes){assert.equal(m.split,'synthetic');assert.equal(m.permissions.publication_eligible,false);assert.equal(m.uncertainty.interval,null);}
});
test('common fixed plot radius is independent of highlighted country and period',()=>{
 const m=model('moving'),r=v.radius(m);
 for(const c of m.scope.countries)for(const p of m.periods){v.replay(catalogue,'moving',c,p.id);assert.equal(v.radius(m),r);}
});
test('missing middle US period creates no connector or structural zero',()=>{
 const m=model('missing-us');
 for(const c of m.scope.countries)for(const kind of ['gap','absolute','relative']){
  const s=v.series(m,c,kind);assert.equal(s.points[2].ready,false);assert.equal(s.points[2].value,null);
  assert(s.edges.every(([a,b])=>b.i===a.i+1 && a.i!==2 && b.i!==2));
 }
 assert.equal(v.series(m,'CAN','gap').edges.length,2);
});
test('elapsed time is numeric, not equally spaced categorical periods',()=>{
 const x=v.elapsedPositions(model('moving').periods);
 assert.equal(x[0],0);assert.equal(x.at(-1),1);assert(x[2]-x[1]>1.9*(x[1]-x[0]));
});
test('movement outside the plane remains in high-dimensional gaps',()=>{
 const m=model('hidden-dimension');assert.deepEqual(v.series(m,'CAN','gap').points.map(p=>p.value),[0,1,2,3,4]);
 assert(v.series(m,'CAN','relative').points.every(p=>p.value[0]===0&&p.value[1]===0));
});
test('display rejection does not erase metrics and never invents coordinates',()=>{
 const m=model('display-withheld');assert(v.series(m,'CAN','gap').points.every(p=>p.ready));
 assert(v.series(m,'CAN','absolute').points.every(p=>p.value===null));assert.equal(v.series(m,'CAN','relative').edges.length,0);
});
test('zero, failed, empty and incompatible-support states remain distinct',()=>{
 assert(v.series(model('zero-gap'),'CAN','gap').points.every(p=>p.value===0));
 assert(v.series(model('failed-source'),'CAN','gap').points.every(p=>p.value===null));
 assert(v.series(model('empty'),'USA','gap').points.every(p=>p.value===null));
 assert.equal(model('support-gap').comparisons.find(c=>c.id==='CAN/p2').reason,'scope_incompatible');
});
test('every country-period selection has a strict portable replay',()=>{
 for(const scene of catalogue.scenes)for(const c of scene.model.scope.countries)for(const p of scene.model.periods){
  const r=v.replay(catalogue,scene.id,c,p.id);assert.deepEqual(v.validateReplay(JSON.parse(JSON.stringify(r)),catalogue),r);
 }
});
test('arbitrary models, changed scope, forged permissions and unknown fields fail closed',()=>{
 const r=v.replay(catalogue,'moving','CAN','p4');
 const bad=[null,[],{}, {...r,publication_eligible:true},{...r,split:'development'},{...r,model_sha256:'f'.repeat(64)},
  {...r,catalogue_sha256:'f'.repeat(64)},{...r,scene_id:'holdout'},{...r,period:'2026-10-05'},
  {...r,country_iso3:'XXX'},{...r,source_text:'<script>alert(1)</script>'},{...r,model:model('moving')}];
 bad.forEach(b=>assert.throws(()=>v.validateReplay(b,catalogue)));
});
test('CSV retains all 30 cells, exact periods and null rather than zero',()=>{
 const text=v.csv(model('missing-us'));assert.equal(text.split('\r\n').length,32);
 const line=text.split('\r\n').find(l=>l.startsWith('"CAN/p2"'));assert(line.includes('"baseline_missing"'));assert(line.includes('"p2","2003-01-01","2003-12-31"'));
 assert(line.includes(',,,,,'));assert(text.includes(model('missing-us').sha256));
});
test('CSV neutralizes spreadsheet formula-shaped labels without changing numeric values',()=>{
 const m=structuredClone(model('moving'));m.comparisons[0].id='=HYPERLINK("bad")';
 assert(v.csv(m).includes('"\'=HYPERLINK(""bad"")"'));
});
test('view planning, selection and export never mutate source-bound models',()=>{assert.equal(JSON.stringify(catalogue),original);});
