/** Synthetic metadata-only demonstration; emits no signatures, source text or access grants. */
import {environment,select} from './tests/fixtures.mjs';
const summaries=[];
for(const [name,selection,status,verdicts] of [
  ['country',select({country:'BRA'}),'auto',{}],
  ['topic',select({topic:'climate'}),'auto',{}],
  ['meeting',select({page:'meetings',meeting:'01'}),'auto',{}],
  ['partial',select({period:null}),'auto',{}],
  ['no_match',select({country:'CAN',topic:'climate'}),'auto',{}],
  ['failed_reader',select(),'failed',{}],
  ['source_veto',select(),'auto',{source:'fail'}]
]) {
  const env=await environment();await env.register(selection,'description',status,verdicts);
  const result=await (await env.router()).route(selection);
  summaries.push({name,state:result.state,reason:result.reason,query:result.plan.query,
    population:result.plan.fit_population,display:result.plan.display_population,
    routes:result.trace.map(t=>({capability:t.capability_id,outcome:t.outcome,reason:t.reason,planned:t.fit?.planned??null,failed:t.fit?.failed??null,skipped:t.fit?.skipped??null}))});
}
const env=await environment(),router=await env.router();
for(const [name,selection] of [['no_product',select()],['unsupported_history',select({period:{start:'2000-01-01',end:'2024-09-23'}})]]) {
  const result=await router.route(selection);summaries.push({name,state:result.state,reason:result.reason});
}
console.log(JSON.stringify({schema:'u2.synthetic-demonstration.v1',model_runs:0,authority:'none',publication_eligible:false,cases:summaries},null,2));
