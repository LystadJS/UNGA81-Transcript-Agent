'use strict';
/* The pinned real release cannot be manufactured in a synthetic fixture.
 * Test the archived-member parser independently using source-free fictional tar
 * members; real 105-PV/790-text attestation is executed only in private QA.
 */
const assert=require('node:assert/strict');
const zlib=require('node:zlib');
const {sourceMemberHashesFromGzip,digest}=require('./p2_to_w1_source_adapter.cjs');

function tarMember(name,data){
  const b=Buffer.from(data,'utf8'),head=Buffer.alloc(512);
  head.write(name,0,100,'utf8');
  head.write(b.length.toString(8).padStart(11,'0')+'\0',124,12,'ascii');
  head.write('0',156,1,'ascii');
  return Buffer.concat([head,b,Buffer.alloc((512-b.length%512)%512)]);
}
function fixture(items){
  return zlib.gzipSync(Buffer.concat([...items,Buffer.alloc(1024)]));
}
const one=tarMember('TXT/Session 71 - 2016/AAA_71_2016.txt','fictional eligible speech content');
const two=tarMember('TXT/Session 72 - 2017/BBB_72_2017.txt','fictional second fictional statement');
const payload=fixture([one,two]);
let passes=0;
function check(name,action){action();passes++;console.log('PASS '+name);}
check('exact archived member hashes bound to immutable country-year',()=>{
 const actual=sourceMemberHashesFromGzip(payload,new Set(['country-AAA-2016','country-BBB-2017']));
 assert.equal(actual.size,2);
 assert.equal(actual.get('country-AAA-2016'),digest(Buffer.from('fictional eligible speech content')));
});
check('missing archived source cannot be replaced by a user-claimed SHA',()=>{
 assert.throws(()=>sourceMemberHashesFromGzip(payload,new Set(['country-CCC-2016'])),
  /missing verified country-year speech/);
});
check('duplicate archived speech cannot be silently assigned to a source ID',()=>{
 assert.throws(()=>sourceMemberHashesFromGzip(fixture([one,one]),new Set(['country-AAA-2016'])),
  /Duplicate Harvard tar member/);
});
check('unapproved future-year source cannot sneak into verified 2016–2023 population',()=>{
 assert.throws(()=>sourceMemberHashesFromGzip(payload,new Set(['country-AAA-2026'])),
  /missing verified country-year speech/);
});
console.log(JSON.stringify({suite:'P2-Harvard-archive-member-byte-authentication-synthetic',
 passed:passes,failed:0,original_UN_documents_used:0,heldout_read:0}));
