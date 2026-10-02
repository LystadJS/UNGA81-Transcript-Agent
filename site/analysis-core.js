/* Browser exploratory engine. Independent of frozen D1 and reviewed models. */
(function(root){
'use strict';
const VERSION='browser-descriptive-1.0.0';
const METHODS=['frequency','timeline','length','tfidf','similarity'];
const STOP=new Set('a an and are as at be been being but by can could did do does for from had has have he her his i if in into is it its may more most not of on or our she should so than that the their them there these they this those to under up us was we were what when where which who will with would you your'.split(' '));
const tokens=s=>(s.normalize('NFKC').toLowerCase().match(/[\p{L}\p{N}]+/gu)||[]);
const canonical=s=>tokens(s).join(' ');
function dateOK(s){return typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&Number.isFinite(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s;}
function parameters(p){
 if(!p.topic||p.topic.length>120)throw Error('Enter a topic of 1–120 characters.');
 if(!dateOK(p.start)||!dateOK(p.end)||p.end<p.start)throw Error('Enter a valid inclusive date range.');
 if((Date.parse(p.end)-Date.parse(p.start))/86400000>30)throw Error('Use a date range of at most 31 days per collection.');
 if(!Array.isArray(p.methods)||!p.methods.length||p.methods.some(m=>!METHODS.includes(m)))throw Error('Choose at least one supported method.');
 if(!Array.isArray(p.phrases)||!p.phrases.length||p.phrases.length>20||p.phrases.some(x=>typeof x!=='string'||!canonical(x)||x.length>120))throw Error('Use 1–20 topic phrases of at most 120 characters.');
 if(!Array.isArray(p.exclude)||p.exclude.length>20||p.exclude.some(x=>typeof x!=='string'||!canonical(x)||x.length>120))throw Error('Use at most 20 valid exclusion phrases.');
 if(!['all','general_debate'].includes(p.scope)||typeof p.region!=='string')throw Error('Invalid collection scope.');
 return p;
}
const hasPhrase=(body,phrase)=>(' '+body+' ').includes(' '+canonical(phrase)+' ');
function validateCorpus(c){
 if(!c||c.schema!=='un.browser.corpus.v1'||!Array.isArray(c.records)||c.records.length>15000||!Array.isArray(c.coverage))throw Error('Use a collected transcript JSON exported by this workspace (un.browser.corpus.v1).');
 const ids=new Set();let size=0;
 for(const r of c.records){
  for(const k of ['id','date','country','region','language','scope','text','source_url','meeting','text_sha256'])if(typeof r[k]!=='string')throw Error('Missing transcript field: '+k);
  if(!r.id||ids.has(r.id)||!dateOK(r.date)||!r.text.trim()||r.text.length>500000||!/^[a-f0-9]{64}$/.test(r.text_sha256))throw Error('Invalid transcript identity, date, text or hash.');
  if(!/^https:\/\//.test(r.source_url))throw Error('Transcript sources must use HTTPS.');
  new URL(r.source_url);ids.add(r.id);size+=r.text.length;
 }
 if(size>20000000)throw Error('Corpus text exceeds 20 million characters.');
 return c;
}
function distribution(records,key,hitIds){
 const bins=new Map();for(const r of records){const name=r[key]||'Unmapped',v=bins.get(name)||{name,total:0,matches:0};v.total++;if(hitIds.has(r.id))v.matches++;bins.set(name,v);}
 return [...bins.values()].map(v=>({...v,percent:100*v.matches/v.total})).sort((a,b)=>a.name.localeCompare(b.name));
}
function tfidf(records){
 const counts=records.map(r=>{const m=new Map();for(const t of tokens(r.text))if(t.length>2&&!STOP.has(t))m.set(t,(m.get(t)||0)+1);return m;});
 const df=new Map();for(const m of counts)for(const t of m.keys())df.set(t,(df.get(t)||0)+1);
 const vectors=counts.map(m=>{const v=new Map();let sum=0;for(const [t,n] of m){const w=(1+Math.log(n))*(1+Math.log((1+records.length)/(1+df.get(t))));v.set(t,w);sum+=w*w;}const norm=Math.sqrt(sum)||1;for(const [t,w] of v)v.set(t,w/norm);return v;});
 const sums=new Map();for(const v of vectors)for(const [t,w] of v)sums.set(t,(sums.get(t)||0)+w);
 const terms=[...sums].map(([term,sum])=>({term,mean:sum/(records.length||1),documents:df.get(term)})).sort((a,b)=>b.mean-a.mean||a.term.localeCompare(b.term)).slice(0,20);
 return {vectors,terms,vocabulary:df.size};
}
async function analyze(c,p,yieldProgress=async()=>{}){
 validateCorpus(c);parameters(p);
 const eligible=c.records.filter(r=>r.date>=p.start&&r.date<=p.end&&(p.region==='All regions'||r.region===p.region)&&(p.scope==='all'||r.scope==='general_debate')&&r.language==='en');
 const records=[],duplicates=[],seen=new Map();
 for(const r of eligible){const key=r.text.normalize('NFKC').replace(/\s+/g,' ').trim();if(seen.has(key))duplicates.push({id:r.id,retained_id:seen.get(key),source_url:r.source_url});else{seen.set(key,r.id);records.push(r);}}
 const matched=records.filter(r=>{const b=canonical(r.text);return p.phrases.some(x=>hasPhrase(b,x))&&!p.exclude.some(x=>hasPhrase(b,x));});
 const ids=new Set(matched.map(r=>r.id)),result={engine:VERSION,parameters:p,created_at:new Date().toISOString(),source:c.origin||'Imported corpus',collection:c.collection||null,coverage:c.coverage,counts:{input:c.records.length,eligible_before_dedup:eligible.length,duplicates:duplicates.length,eligible:records.length,matched:matched.length,unmapped:records.filter(r=>r.region==='Unmapped').length},duplicates,matched,methods:{}};
 if(p.methods.includes('frequency'))result.methods.frequency=distribution(records,'region',ids);
 if(p.methods.includes('timeline'))result.methods.timeline=distribution(records,'date',ids);
 if(p.methods.includes('length')){const bins=[{name:'0–99 words',max:99,total:0},{name:'100–499 words',max:499,total:0},{name:'500–999 words',max:999,total:0},{name:'1,000+ words',max:Infinity,total:0}];for(const r of matched){const n=tokens(r.text).length;bins.find(b=>n<=b.max).total++;}result.methods.length=bins.map(({name,total})=>({name,total}));}
 if(p.methods.some(m=>['tfidf','similarity'].includes(m))){
  await yieldProgress('Calculating TF-IDF');const t=tfidf(matched);
  if(p.methods.includes('tfidf'))result.methods.tfidf={terms:t.terms,vocabulary:t.vocabulary};
  if(p.methods.includes('similarity')){
   if(matched.length>300)result.methods.similarity={skipped:'Pairwise similarity requires at most 300 matched segments. Narrow the topic, dates or region.'};
   else {let pairs=[];for(let i=0;i<t.vectors.length;i++){for(let j=i+1;j<t.vectors.length;j++){let score=0;for(const [term,w] of t.vectors[i])score+=w*(t.vectors[j].get(term)||0);pairs.push({left:matched[i].id,right:matched[j].id,cosine:Math.min(1,score)});}if(i%25===0)await yieldProgress('Comparing text similarity');}pairs.sort((a,b)=>b.cosine-a.cosine||a.left.localeCompare(b.left)||a.right.localeCompare(b.right));result.methods.similarity={pairs:pairs.slice(0,10),compared:pairs.length};}
  }
 }
 return result;
}
const api={VERSION,METHODS,tokens,canonical,dateOK,parameters,validateCorpus,hasPhrase,tfidf,analyze};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNAnalysis=api;
})(typeof globalThis!=='undefined'?globalThis:this);
