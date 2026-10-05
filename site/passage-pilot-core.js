/* Reviewed derivatives use original Unicode code-point offsets, never edited text. */
(function(root){
  'use strict';
  const cryptoAPI=typeof module!=='undefined'&&module.exports?require('node:crypto').webcrypto:root.crypto;
  const encoder=new TextEncoder(),hashPattern=/^[a-f0-9]{64}$/;
  const assert=(condition,message)=>{if(!condition)throw Error(message);};
  async function hash(bytes){return [...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');}
  const digest=s=>hash(encoder.encode(s)),slice=(text,start,end)=>Array.from(text).slice(start,end).join('');
  function bounds(parent,start,end){assert(Number.isInteger(start)&&Number.isInteger(end)&&start>=0&&end>start&&end<=Array.from(parent.text).length,'Invalid text offsets.');const text=slice(parent.text,start,end);assert(text.trim().length>0,'Passage cannot be blank.');return text;}
  function source(url){const u=new URL(url);assert(u.protocol==='https:'&&['transcripts.un.org','webtv.un.org'].includes(u.hostname)&&!u.username&&!u.password,'Unexpected source URL.');}
  function decode(s){assert(typeof s==='string'&&/^[A-Za-z0-9+/]*={0,2}$/.test(s),'Invalid audio encoding.');return Uint8Array.from(atob(s),c=>c.charCodeAt(0));}
  async function load(bytes){
    assert(bytes.byteLength<=12000000,'Choose a packet under 12 MB.');const data=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
    assert(data.schema==='un.speech-pilot-packet.v1'&&hashPattern.test(data.corpus_sha256||''),'Invalid review packet.');
    assert(Array.isArray(data.parents)&&data.parents.length>0&&data.parents.length<=20&&Array.isArray(data.passages)&&data.passages.length>0&&data.passages.length<=200&&Array.isArray(data.audio)&&data.audio.length>0&&data.audio.length<=50,'Invalid packet size.');
    const parents=new Map();
    for(const p of data.parents){assert(typeof p.id==='string'&&!parents.has(p.id)&&typeof p.text==='string'&&p.text.length<200000,'Invalid or duplicate parent.');assert(await digest(p.text)===p.text_sha256,'Original parent hash mismatch.');source(p.source_url);parents.set(p.id,p);}
    const ids=new Set();
    for(const p of data.passages){assert(typeof p.id==='string'&&!ids.has(p.id)&&parents.has(p.parent_id),'Invalid or duplicate passage.');ids.add(p.id);const parent=parents.get(p.parent_id);assert(parent.reviewed_type==='substantive_speech','Pilot requires previously reviewed substantive parents.');assert(await digest(bounds(parent,p.start,p.end))===p.text_sha256,'Passage slice hash mismatch.');}
    const audioIds=new Set();
    for(const a of data.audio){assert(typeof a.id==='string'&&!audioIds.has(a.id)&&parents.has(a.parent_id),'Invalid or duplicate audio concern.');audioIds.add(a.id);assert(parents.get(a.parent_id).text_sha256===a.parent_text_sha256&&bounds(parents.get(a.parent_id),a.start,a.end)===a.original_excerpt,'Audio concern offsets mismatch.');source(a.video_url);assert(Number.isFinite(a.clip_start_seconds)&&Number.isFinite(a.clip_end_seconds)&&a.clip_start_seconds>=0&&a.clip_end_seconds>a.clip_start_seconds,'Invalid audio interval.');if(a.audio_base64)assert(await hash(decode(a.audio_base64))===a.clip_sha256,'Audio clip hash mismatch.');}
    return {data,parents,packet_sha256:await hash(bytes)};
  }
  function review(ctx,value){
    assert(value.schema==='un.speech-pilot-review.v1'&&value.packet_sha256===ctx.packet_sha256&&value.corpus_sha256===ctx.data.corpus_sha256,'Review belongs to a different packet.');
    assert(Array.isArray(value.choices),'Missing choices.');const seen=new Set(),passages=new Map(ctx.data.passages.map(x=>[x.id,x])),audio=new Map(ctx.data.audio.map(x=>[x.id,x]));
    for(const c of value.choices){
      const key=c.kind+':'+c.id;assert(!seen.has(key),'Duplicate review choice.');seen.add(key);
      assert(c.confirmed===true&&typeof c.reviewer==='string'&&c.reviewer.trim()&&typeof c.note==='string'&&c.note.length<=10000&&/(Z|[+-]\d\d:\d\d)$/.test(c.reviewed_at||'')&&Number.isFinite(Date.parse(c.reviewed_at))&&Date.parse(c.reviewed_at)<=Date.now()+300000,'Invalid reviewer identity, note or timestamp.');
      if(c.kind==='passage'){
        const p=passages.get(c.id);assert(p&&['include','exclude','revise'].includes(c.decision),'Invalid passage decision.');bounds(ctx.parents.get(p.parent_id),c.start,c.end);
      }else if(c.kind==='audio'){
        assert(audio.has(c.id)&&['supported','mismatch','unclear'].includes(c.decision),'Invalid audio decision.');
        assert(c.decision==='unclear'||c.listened===true,'Listen before confirming or rejecting wording.');
        assert(c.decision!=='mismatch'||c.note.trim(),'Describe the discrepancy before recording it.');
      }else throw Error('Unknown review choice kind.');
    }
    return value;
  }
  async function derive(ctx,value){
    review(ctx,value);const choices=new Map(value.choices.map(c=>[c.kind+':'+c.id,c]));
    assert(ctx.data.passages.every(p=>choices.has('passage:'+p.id))&&ctx.data.audio.every(a=>choices.has('audio:'+a.id)),'Record a decision for every passage and audio concern first.');
    const records=[],withheld=[],ranges=new Map();
    for(const p of ctx.data.passages){
      const c=choices.get('passage:'+p.id),parent=ctx.parents.get(p.parent_id),text=bounds(parent,c.start,c.end);
      if(c.decision!=='include'){withheld.push({id:p.id,reason:c.decision});continue;}
      const conflicts=ctx.data.audio.filter(a=>a.parent_id===p.parent_id&&a.start<c.end&&c.start<a.end&&choices.get('audio:'+a.id).decision!=='supported');
      if(conflicts.length){withheld.push({id:p.id,reason:'Overlapping unresolved or disputed audio wording',audio_ids:conflicts.map(a=>a.id)});continue;}
      const prior=ranges.get(p.parent_id)||[];assert(!prior.some(([start,end])=>c.start<end&&start<c.end),'Approved passages overlap within a parent. Adjust boundaries or exclude one.');prior.push([c.start,c.end]);ranges.set(p.parent_id,prior);
      const text_sha256=await digest(text),id=parent.id+'@cp:'+c.start+'-'+c.end+':'+text_sha256.slice(0,12);
      records.push({id,proposal_id:p.id,parent_id:parent.id,parent_text_sha256:parent.text_sha256,parent_raw_sha256:parent.raw_sha256,corpus_sha256:ctx.data.corpus_sha256,offset_unit:'Unicode code points; zero-based; end exclusive',start:c.start,end:c.end,utf8_start:encoder.encode(slice(parent.text,0,c.start)).length,utf8_end:encoder.encode(slice(parent.text,0,c.end)).length,text,text_sha256,source_url:parent.source_url,date:parent.date,country:parent.country,region:parent.region,source_group:parent.id.split('#')[0],reviewer:c.reviewer,reviewed_at:c.reviewed_at,scope:'Reviewed boundary and inclusion only; not full audio verification, relevance, stance or theme'});
    }
    return {schema:'un.reviewed-speech-units.v1',packet_sha256:ctx.packet_sha256,corpus_sha256:ctx.data.corpus_sha256,selection:ctx.data.selection,records,withheld,originals_changed:false,analysis_status:'Audit pilot only; keep parent speeches and meetings together in any model split or resampling'};
  }
  const api={load,review,derive,bounds,slice,hash,digest,decode};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNSpeechPilot=api;
})(globalThis);
