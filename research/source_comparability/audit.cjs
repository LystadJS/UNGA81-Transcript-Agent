"use strict";
const fs=require("node:fs"),crypto=require("node:crypto");
const VERSION="un.historical-source-audit.v1";
const sha=x=>crypto.createHash("sha256").update(x).digest("hex");
const hex=/^[a-f0-9]{64}$/;
function readManifest(path){const data=JSON.parse(fs.readFileSync(path,"utf8"));if(data.schema!==VERSION||!Array.isArray(data.observations)||!Array.isArray(data.receipts)||!Array.isArray(data.frames))throw Error("Unsupported manifest contract");return data;}
function audit(m,{originals=null}={}){
 if(m.schema!==VERSION||!Array.isArray(m.frames)||!Array.isArray(m.observations)||!Array.isArray(m.receipts))throw Error("Invalid manifest");
 const problems=[],counts={},ids=new Set(),receipts=new Map(),frameMap=new Map();
 const add=(code,id)=>{problems.push({code,id});counts[code]=(counts[code]||0)+1;};
 for(const f of m.frames){if(!f.id||frameMap.has(f.id))add("duplicate_frame",f.id);frameMap.set(f.id,f);}
 for(const r of m.receipts){if(!r.document_id||receipts.has(r.document_id))add("duplicate_document_identity",r.document_id);receipts.set(r.document_id,r);
 if(r.sha256!=null&&!hex.test(r.sha256))add("invalid_checksum",r.document_id);
 if(r.text_sha256!=null&&!hex.test(r.text_sha256))add("invalid_text_checksum",r.document_id);
 if(originals&&Object.hasOwn(originals,r.document_id)){if(r.sha256!==sha(originals[r.document_id]))add("checksum_mismatch",r.document_id);}
 }
 const rows=[];
 for(const o of m.observations){
 const errors=[];const flag=x=>{errors.push(x);add(x,o.id);};
 if(!o.id||ids.has(o.id))flag("duplicate_observation_identity");ids.add(o.id);
 const f=frameMap.get(o.frame_id),r=receipts.get(o.document_id);
 if(!f)flag("unknown_frame");
 if(!r||r.available===false)flag("missing_document");
 if(r&&r.transcript_available===false)flag("missing_transcript");
 if(!o.meeting_id||!o.speech_id||!o.country)flag("incomplete_lineage");
 if(!Number.isInteger(o.year)||o.year<2008||o.year>2023||o.year!==Number(f?.year??o.year))flag("missing_or_inconsistent_year");
 if(o.attribution!=="verified")flag("ambiguous_attribution");
 if(o.outcome_available===false)flag("missing_outcome");
 if(o.inclusion_probability==null||!Number.isFinite(o.inclusion_probability)||o.inclusion_probability<=0||o.inclusion_probability>1)flag("positivity_violation");
 if(r&&o.meeting_id&&r.meeting_id!==o.meeting_id)flag("meeting_document_mismatch");
 if(r&&o.year&&r.year!==o.year)flag("document_year_mismatch");
 if(r&&o.text_sha256&&r.text_sha256!==o.text_sha256)flag("text_provenance_mismatch");
 rows.push({id:o.id,frame_id:o.frame_id,year:o.year,eligible:errors.length===0,exclusions:errors});
 }
 const groups=Object.groupBy?Object.groupBy(m.observations,x=>x.frame_id):m.observations.reduce((a,x)=>((a[x.frame_id]??=[]).push(x),a),{});
 const comparisons=[];
 for(let i=0;i<m.frames.length;i++)for(let j=i+1;j<m.frames.length;j++){
 const a=m.frames[i],b=m.frames[j],aa=groups[a.id]||[],bb=groups[b.id]||[];
 const dimensions=["meeting_design","genre","language","translation_modality","roster_definition","selection_design"];
 const incompatible=dimensions.filter(k=>a[k]!==b[k]);
 const overlap=aa.filter(x=>bb.some(y=>x.document_id===y.document_id)).length;
 const lens=x=>x.map(z=>z.speech_length).filter(Number.isFinite);
 const la=lens(aa),lb=lens(bb);
 const status=incompatible.length?"inadmissible":(!aa.length||!bb.length||!la.length||!lb.length||!overlap?"uncertain":"supported");
 comparisons.push({frames:[a.id,b.id],status,incompatible_dimensions:incompatible,shared_documents:overlap,year_ranges:[[...new Set(aa.map(x=>x.year))],[...new Set(bb.map(x=>x.year))]],speech_length_ranges:[la.length?[Math.min(...la),Math.max(...la)]:null,lb.length?[Math.min(...lb),Math.max(...lb)]:null],reason:incompatible.length?"Unharmonized design differences":status==="uncertain"?"Insufficient overlap, coverage or length evidence":"Observed common frame; substantive inference still requires calibration"});
 }
 return {schema:VERSION,publication_eligible:false,private_source_validation:originals?"EXECUTED_ON_SUPPLIED_BYTES":"NOT RUN",totals:{observations:rows.length,eligible:rows.filter(x=>x.eligible).length,excluded:rows.filter(x=>!x.eligible).length},counts,problems,eligibility:rows,comparisons};
}
module.exports={VERSION,readManifest,audit,sha};
if(require.main===module){const m=readManifest(process.argv[2]);process.stdout.write(JSON.stringify(audit(m),null,2)+"\n");}
