'use strict';
// Actual coordinator-validator contract test. No upstream copies, private rows or schema edits.
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const {auditInventory, sha} = require('./audit.cjs');
const source = path.resolve(__dirname, '../../docs/parallel-work/source-inventory-v1.cjs');
const repo = path.resolve(__dirname, '../../AGENTS.md');

// An isolated worker directory cannot faithfully test coordinator code. Skip explicitly
// rather than substituting a mock or misreporting integration as passed.
if (!fs.existsSync(repo)) {
  test('actual coordinator source-inventory integration', {skip:'NOT RUN: upstream repository checkout unavailable'}, () => {});
} else {
  assert(fs.existsSync(source), 'Coordinator source-inventory validator missing from complete repository');
  const {fromPanel, validateInventory, hash} = require(source);
  const hex = value => sha(Buffer.from(value, 'utf8'));
  const makePanel = () => ({
    schema:'un.longitudinal-panel.v1', split:'synthetic',
    periods:[
      {id:'early',start:'2010-01-01',end:'2010-12-31'},
      {id:'late',start:'2020-01-01',end:'2020-12-31'}
    ],
    observations:[
      {id:'synthetic-early',period:'early',year:2010,actor_kind:'synthetic',
        actor_id:'AAA',genre:'synthetic',source_status:'available',missing_reason:null,
        date:'2010-09-23',meeting_id:'synthetic-meeting-2010',
        source_family_id:'synthetic-family-2010',source_sha256:hex('synthetic original'),
        text_sha256:hex('synthetic canonical text'),review_status:'not_applicable'},
      {id:'synthetic-late',period:'late',year:2020,actor_kind:'synthetic',
        actor_id:'AAA',genre:'synthetic',source_status:'unverified',
        missing_reason:'not obtained in synthetic fixture',date:null,meeting_id:null,
        source_family_id:null,source_sha256:null,text_sha256:null,review_status:'not_applicable'}
    ]
  });
  const original = {
    source_schema:'synthetic.v1',source_engine:'synthetic_source_adapter',
    source_hash_basis:'synthetic',source_sha256:hex('original population'),
    selection_sha256:hex('original selection')
  };
  const makeInventory = () => fromPanel(makePanel(),original);

  test("coordinator's unmodified v1 inventory validates and audit preserves denominators",()=>{
    const inventory=makeInventory();
    assert.equal(validateInventory(inventory).status,'valid_inventory_contract');
    const receipt=auditInventory(inventory);
    assert.equal(receipt.periods[0].total,1);
    assert.equal(receipt.periods[0].available,1);
    assert.equal(receipt.periods[1].unverified,1);
    assert.equal(receipt.year_coverage['2010'].available,1);
    assert.equal(receipt.year_coverage['2020'].unverified,1);
    assert.equal(receipt.original_inventory_sha256,inventory.inventory_sha256);
    assert.equal(receipt.original_selection_sha256,inventory.upstream.selection_sha256);
    assert.equal(receipt.comparisons[0].status,'uncertain');
    assert.equal(receipt.private_source_validation,'NOT RUN');
    assert.equal(receipt.first_stage_positivity,'NOT RUN');
    assert.equal(receipt.inference_eligible,false);
    assert.equal(receipt.publication_eligible,false);
  });
  const rejects = (label,change) => test(label,()=>{
    const i=makeInventory();change(i);
    assert.throws(()=>auditInventory(i),undefined,label);
  });
  rejects('upstream inventory digest tampering is rejected',x=>x.inventory_sha256='f'.repeat(64));
  rejects('unauthorized legacy analytical binding is rejected',x=>{
    x.legacy_v1_binding={mode:'verified_subset_projection',reason:null,
      legacy_selection_sha256:'f'.repeat(64),legacy_eligible:1};
  });
  rejects('source-bearing raw text in inventory is rejected',x=>{x.observations[0].text='forbidden source text';});
  rejects('missing source invented as available is rejected',x=>{x.observations[1].source_status='available';});
  rejects('duplicate observation identity cannot be hidden by updated hash or totals',x=>{
    x.observations.push({...x.observations[0]});
    x.inventory_sha256=hash(x.observations);
    x.population.total_in_frame+=1;
    x.population.available+=1;
    x.coverage[0].total+=1;
    x.coverage[0].available+=1;
  });
  rejects('out-of-period event date is rejected even with updated inventory digest',x=>{
    x.observations[0].event_date='2011-01-01';
    x.inventory_sha256=hash(x.observations);
  });
}
