/* Versioned humanitarian policy contract; source contexts remain distinct. */
(function(root){'use strict';
const version='humanitarian-ontology-1';
const policies=[{id:'humanitarian_access',label:'Allow humanitarian access',object:'Safe and unimpeded humanitarian relief access and delivery',exclusions:['general aid funding','economic development','detention monitoring access']},{id:'civilian_protection',label:'Protect civilians',object:'Protection of civilians from conflict-related harm',exclusions:['biographical descriptions','institution names alone','generic concern without an explicit position']}];
const stances=['support','oppose','qualified'];
const discourse=['requested_action','reported_condition','claimed_implementation'];
const rules={national_only:true,collective_not_national:true,conditions_preserved:true,missing_is_not_neutral:true,duplicate_weight:0,unspecified_context_comparable:false,domestic_context_comparable:false,documents_are_un_statements:false};
function resolve(topic){
 const original=String(topic||''),s=original.toLowerCase(),ids=[],access=/humanitarian access|aid access|relief access|access to (?:humanitarian )?aid|access to humanitarian (?:assistance|relief)/gi,protection=/civilian protection|protection of civilians|protect(?:ing)? civilians/gi;
 if(new RegExp(access.source,'i').test(s))ids.push('humanitarian_access');if(new RegExp(protection.source,'i').test(s))ids.push('civilian_protection');
 const positions=typeof module!=='undefined'&&module.exports?require('./position-comparison'):root.UNPositions,catalog=(positions?.CONTEXTS||[]).filter(c=>c.pattern),matched=catalog.filter(c=>c.pattern.test(original)),contexts=matched.map(c=>c.id);
 // Requested filters never assign a context to source evidence. Only existing source context IDs are accepted.
 let remainder=original.replace(access,' ').replace(protection,' ');for(const c of catalog)remainder=remainder.replace(new RegExp(c.pattern.source,'gi'),' ');
 remainder=remainder.replace(/\b(?:and|or|in|for|the|of|on|regarding|concerning|across|within|safe|unimpeded|unhindered|unrestricted|armed|conflict|issue|topic)\b/gi,' ').replace(/[\s,;:.!?/&()–—-]+/g,' ').trim();
 const context_warning=ids.length>0&&remainder.length>0;
 const context_message=context_warning?'Unrecognized topic qualifier: '+remainder+'. Its meaning is not applied; clarify the topic before relying on this report.':contexts.length?'Requested context filter: '+matched.map(c=>c.label).join('; ')+'. Source evidence must independently establish each context.':'All established source contexts are included separately.';
 return {ontology_version:version,policy_ids:ids,status:ids.length?'supported':'unsupported',original_topic:original,context_requires_source_evidence:true,contexts,context_message,context_warning,unrecognized_qualifier:context_warning?remainder:null};
}

const api={version,policies,stances,discourse,rules,resolve};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNIssueOntology=api;
})(typeof globalThis!=='undefined'?globalThis:this);
