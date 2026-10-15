/** Loopback synthetic harness adapter. No transcript endpoint or operational issuer. */
import {parseStrict} from '../../../research/integration/product_contracts/contracts.mjs';
const BASE = '/__u1__/';
export function createProvider(fetcher=globalThis.fetch.bind(globalThis)) {
  async function request(path, options={}) {
    const res = await fetcher(BASE+path,{...options,cache:'no-store',credentials:'omit',redirect:'error'});
    if(!res.ok) throw new Error('synthetic_host_unavailable');
    // Bound the stream before parsing. Content-Length alone is not authoritative.
    const reader=res.body.getReader(); let length=0, chunks=[];
    try { for(;;) {const {done,value}=await reader.read(); if(done) break; length+=value.length; if(length>2097152) throw new Error('host_response_size'); chunks.push(value);} }
    finally {await reader.cancel().catch(()=>{});}
    const bytes=new Uint8Array(length);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
    return parseStrict(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
  }
  return Object.freeze({
    catalog:()=>request('catalog'),
    resolve:selection=>request('resolve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(selection)}),
    getTrust:id=>{if(!/^[a-f0-9]{64}$/.test(id))throw new Error('id');return request('trust/'+id);},
    getEvidence:(id,evidence)=>{if(!/^[a-f0-9]{64}$/.test(id)||!/^e[0-9]+$/.test(evidence))throw new Error('id');return request('evidence/'+id+'/'+evidence);}
  });
}
