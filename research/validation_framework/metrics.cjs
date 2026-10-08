'use strict';
// Descriptive, label-invariant comparisons. Null means not statistically assessable.
const C = require('../../site/cluster-core.js');

function assert(ok, why) { if (!ok) throw Error(why); }
function finite(x) { return typeof x === 'number' && Number.isFinite(x); }
function combinations2(n) { return n * (n - 1) / 2; }
function partitionEquivalent(a,b) {
  for(let i=0;i<a.length;i++) for(let j=0;j<i;j++) {
    if ((a[i]===a[j]) !== (b[i]===b[j])) return false;
  }
  return true;
}
function contingency(a,b) {
  assert(Array.isArray(a) && Array.isArray(b) && a.length === b.length && a.length >= 2, 'Paired labels require at least two records.');
  const aa=[...new Set(a)], bb=[...new Set(b)];
  const r=aa.map(x=>a.filter(v=>v===x).length);
  const c=bb.map(x=>b.filter(v=>v===x).length);
  const cells=aa.map(x=>bb.map(y=>a.filter((v,i)=>v===x&&b[i]===y).length));
  return {r,c,cells,n:a.length};
}
function adjustedMutualInformation(a,b) {
  const {r,c,cells,n}=contingency(a,b);
  const entropy=counts=>-counts.reduce((s,z)=>s+(z?z/n*Math.log(z/n):0),0);
  const ha=entropy(r), hb=entropy(c);
  if (ha===0 && hb===0) return 1;
  let mi=0,emi=0;
  const logfactorials=[0];
  for(let i=1;i<=n;i++)logfactorials.push(logfactorials[i-1]+Math.log(i));
  const lc=(u,v)=>v<0||v>u ? -Infinity : logfactorials[u]-logfactorials[v]-logfactorials[u-v];
  for(let i=0;i<r.length;i++) for(let j=0;j<c.length;j++){
    const ai=r[i],bj=c[j],nij=cells[i][j];
    if(nij)mi+=nij/n*Math.log(n*nij/(ai*bj));
    for(let t=Math.max(1,ai+bj-n);t<=Math.min(ai,bj);t++){
      const probability=Math.exp(lc(bj,t)+lc(n-bj,ai-t)-lc(n,ai));
      emi+=probability*t/n*Math.log(n*t/(ai*bj));
    }
  }
  const denominator=(ha+hb)/2-emi;
  if(Math.abs(denominator)<1e-12) return partitionEquivalent(a,b)?1:0;
  return Math.max(-1,Math.min(1,(mi-emi)/denominator));
}
function summarize(values) {
  const v=values.filter(finite);
  if(!v.length)return {n:0,mean:null,min:null,max:null};
  return {n:v.length,mean:v.reduce((s,x)=>s+x,0)/v.length,min:Math.min(...v),max:Math.max(...v)};
}
function evaluateAssignments(left,right) {
  assert(left.length===right.length,'Populations must have identical length.');
  const n=left.length, both=[], transitions={both_assigned:0,left_only:0,right_only:0,both_unassigned:0};
  for(let i=0;i<n;i++){
    const l=left[i]>0,r=right[i]>0;
    if(l&&r){transitions.both_assigned++;both.push(i);}
    else if(l)transitions.left_only++;
    else if(r)transitions.right_only++;
    else transitions.both_unassigned++;
  }
  const x=both.map(i=>left[i]),y=both.map(i=>right[i]);
  const enough=both.length>=2 && new Set(x).size>=2 && new Set(y).size>=2;
  let pairConsistent=0;
  for(let i=0;i<both.length;i++)for(let j=0;j<i;j++){
    const a=both[i],b=both[j];
    if((left[a]===left[b])===(right[a]===right[b]))pairConsistent++;
  }
  const pairs=combinations2(both.length);
  return {
    observations:n,transitions,
    assignment_coverage_left:n?left.filter(x=>x>0).length/n:null,
    assignment_coverage_right:n?right.filter(x=>x>0).length/n:null,
    assignment_status_agreement:n?(transitions.both_assigned+transitions.both_unassigned)/n:null,
    ari:enough?C.ari(x,y):null,
    adjusted_mutual_information:enough?adjustedMutualInformation(x,y):null,
    assigned_both:both.length, pair_opportunities_all:combinations2(n),
    pair_opportunities_assigned_both:pairs,
    pairwise_assignment_consistency:pairs?pairConsistent/pairs:null,
    pairwise_consistent_count:pairConsistent,
    reason:enough?null:'ARI/AMI withheld: fewer than two represented assigned clusters in at least one fit'
  };
}
function compareFits(a,b) {
  assert(a.population_hash===b.population_hash,'Population changed: comparisons require the same ordered ID and text-hash identities.');
  assert(a.observation_ids.length===b.observation_ids.length && a.observation_ids.every((v,i)=>v===b.observation_ids[i]),'Observation order or identity drift.');
  if(a.status!=='fitted'||b.status!=='fitted')return {left:a.model_id,right:b.model_id,status:'unassessable',reason:'At least one fit did not complete',metrics:null};
  return {left:a.model_id,right:b.model_id,status:'descriptive',comparison_protocol:a.representation_id===b.representation_id?'same-representation':'paired-representations-same-population',
    metrics:evaluateAssignments(a.assignments,b.assignments)};
}
module.exports={adjustedMutualInformation,evaluateAssignments,compareFits,summarize,partitionEquivalent,combinations2};
