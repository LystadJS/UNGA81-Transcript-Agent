'use strict';
const assert=require('node:assert/strict');
function cpu(profile,allowedScripts){
 assert.ok(Array.isArray(profile.nodes)&&Array.isArray(profile.samples)&&Array.isArray(profile.timeDeltas));
 assert.equal(profile.samples.length,profile.timeDeltas.length,'sample/delta cardinality');
 assert.ok(Number.isFinite(profile.startTime)&&Number.isFinite(profile.endTime)&&profile.endTime>=profile.startTime,'ordered finite profile bounds');
 const nodes=new Map(profile.nodes.map(n=>[n.id,n])),rows=new Map();let total=0;
 for(let i=0;i<profile.samples.length;i++){
  const delta=profile.timeDeltas[i];assert.ok(Number.isFinite(delta)&&delta>=0,'nonnegative finite sampling interval');
  const frame=nodes.get(profile.samples[i])?.callFrame,name=frame?.functionName||'(anonymous)',url=frame?.url||'';
  let bucket='unattributed',script=null,fn=null;
  if(['(idle)','(program)','(garbage collector)'].includes(name))bucket=name.slice(1,-1);
  else if(allowedScripts.includes(url)){bucket='known_script';script=url.split('/').pop();fn=name;}
  const key=JSON.stringify([bucket,script,fn]),row=rows.get(key)||{bucket,script,function:fn,samples:0,weighted_interval_ms:0};
  row.samples++;row.weighted_interval_ms+=delta/1000;rows.set(key,row);total+=delta/1000;
 }
 const elapsed=(profile.endTime-profile.startTime)/1000;assert.ok(total<=elapsed+0.001,'sampling intervals cannot exceed profile bounds');
 return {samples:profile.samples.length,weighted_interval_ms:total,profile_elapsed_ms:elapsed,unrepresented_tail_ms:Math.max(0,elapsed-total),rows:[...rows.values()].sort((a,b)=>b.weighted_interval_ms-a.weighted_interval_ms),notes:'Leaf sample timeDelta weights are sampling intervals, not exact function CPU duration. Missing/native/unknown frames remain unattributed; trailing profile time is unrepresented. No fraction of wall elapsed or causal claim.'};
}
function timeline(events,beginName,endName){
 const begin=events.find(e=>e.name===beginName),end=events.find(e=>e.name===endName);
 assert.ok(begin&&end&&begin.pid===end.pid&&begin.tid===end.tid&&end.ts>=begin.ts,'same-document ordered markers');
 const output={window_ms:(end.ts-begin.ts)/1000,events:{},notes:'Complete X events on marker pid/tid, clipped to markers; within-category unions only. Categories overlap and cannot be summed; absent categories do not imply zero work.'};
 for(const name of ['Layout','UpdateLayoutTree','Paint','PrePaint','ParseHTML','EvaluateScript','FunctionCall','RunTask']){
  const intervals=events.filter(e=>e.ph==='X'&&e.pid===begin.pid&&e.tid===begin.tid&&e.name===name&&Number.isFinite(e.ts)&&Number.isFinite(e.dur)&&e.dur>=0&&e.ts<end.ts&&e.ts+e.dur>begin.ts).map(e=>[Math.max(e.ts,begin.ts),Math.min(e.ts+e.dur,end.ts)]).sort((a,b)=>a[0]-b[0]);
  let sum=0,left=null,right=null;for(const [a,b] of intervals){if(left===null){left=a;right=b;}else if(a<=right)right=Math.max(right,b);else{sum+=right-left;left=a;right=b;}}
  output.events[name]={count:intervals.length,union_ms:(sum+(left===null?0:right-left))/1000,max_clipped_ms:Math.max(0,...intervals.map(([a,b])=>(b-a)/1000))};
 }
 return output;
}
function captureCpu(profile,allowedScripts){
 try{return {status:'usable_capture',...cpu(profile,allowedScripts)};}
 catch(error){
  const deltas=Array.isArray(profile?.timeDeltas)?profile.timeDeltas:[],negative=deltas.filter(v=>Number.isFinite(v)&&v<0);
  return {status:'unusable_capture',reason:String(error.message).slice(0,240),diagnostics:{sample_count:Array.isArray(profile?.samples)?profile.samples.length:null,delta_count:Array.isArray(profile?.timeDeltas)?profile.timeDeltas.length:null,negative_interval_count:negative.length,minimum_negative_interval_us:negative.length?negative.reduce((a,b)=>Math.min(a,b),0):null,has_nonfinite_interval:deltas.some(v=>!Number.isFinite(v)),has_invalid_profile_bounds:!Number.isFinite(profile?.startTime)||!Number.isFinite(profile?.endTime)||profile.endTime<profile.startTime},rows:null,weighted_interval_ms:null,profile_elapsed_ms:null,unrepresented_tail_ms:null,notes:'Strict CPU-profile reduction failed. No interval is clamped, repaired or attributed. Functional and timeline checks are separate from CPU capture acceptance.'};
 }
}
module.exports={cpu,timeline,captureCpu};
