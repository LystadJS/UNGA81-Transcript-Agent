/* Synthetic-only, read-only evidence renderer. No numerical fitting. */
(function(root,factory){const api=factory();if(typeof module==="object"&&module.exports)module.exports=api;else root.UNResearchValidationV2=api;})(typeof globalThis!=="undefined"?globalThis:this,function(){
"use strict";
const kinds=["consensus","country-theme","longitudinal","method-comparison"];
function check(x){if(!x||x.schema!=="un.research-validation-v2.synthetic"||x.publication_eligible!==false||x.evaluation_role!=="engineering_only"||x.fixture_kind!=="synthetic")throw Error("Unsupported or non-synthetic evidence");
if(!Array.isArray(x.panels)||!Array.isArray(x.sources))throw Error("Missing evidence ledger");
const ids=new Set();for(const s of x.sources){if(!s.id||ids.has(s.id)||!(/^[a-f0-9]{64}$/.test(s.sha256))||!["available","missing","failed","excluded"].includes(s.status))throw Error("Invalid source identity");ids.add(s.id);}
for(const p of x.panels){if(!kinds.includes(p.kind)||!["ready","withheld","failed","empty"].includes(p.status)||!p.identity||!p.coverage||!Array.isArray(p.rows))throw Error("Invalid panel");
if(p.status!=="ready"&&!p.reason)throw Error("Abstention requires reason");
const c=p.coverage;if(!Number.isInteger(c.frame)||!Number.isInteger(c.eligible)||c.frame<0||c.eligible<0||c.eligible>c.frame||!Number.isInteger(c.missing)||c.missing<0||c.missing>c.frame)throw Error("Invalid coverage");
for(const id of p.identity.source_ids||[])if(!ids.has(id))throw Error("Unknown source");
for(const row of p.rows){for(const id of row.source_ids||[])if(!ids.has(id))throw Error("Unknown row source");
if(p.kind==="consensus"&&row.families){const seen=new Set();for(const f of row.families){if(seen.has(f.family)||!Number.isInteger(f.eligible)||f.eligible<0||!Number.isInteger(f.together)||f.together<0||f.together>f.eligible||!Number.isInteger(f.failed)||f.failed<0)throw Error("Invalid family counts");seen.add(f.family);}}
}}
return x;}
function el(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);return n;}
function mount(host,data){check(data);host.replaceChildren();const h=el("h2","Research evidence — synthetic demonstration");host.append(h,el("p","Engineering-only. Co-assignment is not diplomatic agreement; theme shares are not stance; movement is not influence."));
for(const p of data.panels){const section=el("section");section.className="rv-panel";section.append(el("h3",p.kind),el("p","Population: "+p.identity.population+" | Weighting: "+p.identity.weighting+" | Representation: "+p.identity.representation_id),el("p","Frame: "+p.coverage.frame+" | Eligible: "+p.coverage.eligible+" | Missing: "+p.coverage.missing+" | Excluded: "+(p.coverage.excluded??"not supplied")));
if(p.status!=="ready"){section.append(el("strong","ABSTAIN — "+p.status+": "+p.reason));host.append(section);continue;}
const table=el("table"),caption=el("caption","Source-aware "+p.kind+" (accessible data table)"),thead=el("thead"),head=el("tr");const keys=[...new Set(p.rows.flatMap(r=>Object.keys(r)))];for(const k of keys)head.append(el("th",k));thead.append(head);table.append(caption,thead);const body=el("tbody");
for(const row of p.rows){const tr=el("tr");for(const k of keys){let v=row[k];if(k==="families"&&Array.isArray(v))v=v.map(f=>f.family+": "+f.together+"/"+f.eligible+" (failed "+f.failed+")").join("; ");else if(typeof v==="object"&&v!==null)v=JSON.stringify(v);tr.append(el("td",v??"missing"));}body.append(tr);}table.append(body);const wrap=el("div");wrap.className="rv-scroll";wrap.append(table);section.append(wrap);host.append(section);}
const details=el("details"),summary=el("summary","Result-level provenance inspector");details.append(summary);const table=el("table");const body=el("tbody");for(const s of data.sources){const tr=el("tr");tr.append(el("th",s.id),el("td",s.sha256),el("td",s.status),el("td",s.review_status||"unreviewed"));body.append(tr);}table.append(body);const wrap=el("div");wrap.className="rv-scroll";wrap.append(table);details.append(wrap);host.append(details);return host;}
function exportJSON(x){check(x);return JSON.stringify(x,null,2)+"\n";}
return {check,mount,exportJSON};
});