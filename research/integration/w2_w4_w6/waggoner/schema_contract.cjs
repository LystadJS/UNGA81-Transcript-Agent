'use strict';
// Validator for the shared closed-schema subset, not a general schema engine.
const fs=require('node:fs'),path=require('node:path');
const root=JSON.parse(fs.readFileSync(path.join(__dirname,'schema/us_relative.schema.json'),'utf8'));
const allowed=new Set(['$schema','$id','title','description','$defs','$ref','type','const','enum','anyOf','allOf','if','then','else','required','properties','additionalProperties','propertyNames','maxProperties','items','minItems','maxItems','uniqueItems','pattern','format','maxLength','minimum','maximum','exclusiveMinimum']);
const isObject=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
function need(x){if(!x)throw new Error('Invalid closed research schema');}
function equal(a,b){return typeof a===typeof b&&JSON.stringify(a)===JSON.stringify(b);}
function check(v,s){
  if(s===true)return;if(s===false)throw new Error('Forbidden field');
  need(isObject(s)&&Object.keys(s).every(k=>allowed.has(k)));
  if(s.$ref){need(s.$ref.startsWith('#/$defs/'));check(v,root.$defs[s.$ref.split('/').pop()]);}
  const types={null:v===null,boolean:typeof v==='boolean',number:typeof v==='number'&&Number.isFinite(v),integer:Number.isSafeInteger(v),string:typeof v==='string',array:Array.isArray(v),object:isObject(v)};
  if(s.type)need(types[s.type]);
  if(Object.hasOwn(s,'const'))need(equal(v,s.const));if(s.enum)need(s.enum.some(x=>equal(v,x)));
  const accepts=x=>{try{check(v,x);return true;}catch{return false;}};
  if(s.anyOf)need(s.anyOf.some(accepts));if(s.allOf)s.allOf.forEach(x=>check(v,x));
  if(s.if)check(v,s[accepts(s.if)?'then':'else']||{});
  if(isObject(v)){
    need((s.required||[]).every(k=>Object.hasOwn(v,k)));need(Object.keys(v).length<=(s.maxProperties??Infinity));
    for(const [k,x] of Object.entries(v)){
      if(s.propertyNames)check(k,s.propertyNames);
      if(s.properties&&Object.hasOwn(s.properties,k))check(x,s.properties[k]);
      else if(Object.hasOwn(s,'additionalProperties'))check(x,s.additionalProperties);
    }
  }
  if(Array.isArray(v)){
    need(v.length>=(s.minItems??0)&&v.length<=(s.maxItems??Infinity));
    if(s.uniqueItems)need(new Set(v.map(x=>JSON.stringify(x))).size===v.length);
    if(s.items)v.forEach(x=>check(x,s.items));
  }
  if(typeof v==='string'){
    need([...v].length<=(s.maxLength??Infinity));if(s.pattern)need(new RegExp(s.pattern).test(v));
    if(s.format==='date')need(/^\d{4}-\d{2}-\d{2}$/.test(v)&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString().slice(0,10)===v);
  }
  if(typeof v==='number'){
    need(Number.isFinite(v)&&v>=(s.minimum??-Infinity)&&v<=(s.maximum??Infinity));
    if(Object.hasOwn(s,'exclusiveMinimum'))need(v>s.exclusiveMinimum);
  }
}
function validate(value,options={}){check(value,options.source?root.$defs.source:root);return true;}
module.exports={validate};
