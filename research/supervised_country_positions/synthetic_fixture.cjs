'use strict';

// Fictional actors and invented statements only. No original UN source material.
const { createHash } = require('node:crypto');
const { validateCodebook, SCHEMA } = require('./position_core.cjs');

const ACTORS = [
  { iso3: 'USX', name: 'Fictional U.S. reference', positions: {
    ukr_sovereignty:'support', ukr_force:'support', cub_embargo:'oppose',
    cub_extraterritorial:'oppose', ai_binding:'conditional', ai_military:'descriptive' } },
  { iso3: 'CNX', name: 'Fictional China reference', positions: {
    ukr_sovereignty:'oppose', ukr_force:'oppose', cub_embargo:'support',
    cub_extraterritorial:'support', ai_binding:'support', ai_military:'conditional' } },
  { iso3: 'ALP', name: 'Fictional Alpha', positions: {
    ukr_sovereignty:'support', ukr_force:'support', cub_embargo:'support',
    cub_extraterritorial:'conditional', ai_binding:'support', ai_military:'support' } },
  { iso3: 'BRV', name: 'Fictional Bravo', positions: {
    ukr_sovereignty:'oppose', ukr_force:'conditional', cub_embargo:'oppose',
    cub_extraterritorial:'descriptive', ai_binding:'support', ai_military:'oppose' } },
  { iso3: 'CRN', name: 'Fictional Crown', positions: {
    ukr_sovereignty:'support', ukr_force:'oppose', cub_embargo:'insufficient',
    cub_extraterritorial:'descriptive', ai_binding:'support', ai_military:'descriptive' } },
  { iso3: 'DRL', name: 'Fictional Delta', positions: {
    ukr_sovereignty:'descriptive', ukr_force:null, cub_embargo:'support',
    cub_extraterritorial:'support', ai_binding:'support', ai_military:'support' } }
];

function makeSyntheticFrame(codebook) {
  validateCodebook(codebook);
  const sources = [];
  const observations = [];
  function addSource(iso3, name, year, positions, options = {}) {
    const number = sources.length + 1;
    const sourceId = 'syn-source-' + number;
    const familyId = options.source_family_id || sourceId;
    let text = '';
    const offsets = [];
    for (const [prop, stance] of Object.entries(positions)) {
      if (stance === null) continue;
      const quote = 'Invented example: ' + iso3 + ' expresses ' + stance +
        ' concerning ' + prop + '. No real national position is represented.';
      const start = Array.from(text).length;
      text += quote + '\n';
      offsets.push({ prop, stance, quote, start, end: start + Array.from(quote).length });
    }
    sources.push({
      source_id: sourceId, iso3, name, date: year + '-09-24',
      genre: 'general_debate', language: 'en',
      source_status: options.status || 'available',
      attribution: options.attribution || 'individual',
      source_family_id: familyId, text_sha256: createHash('sha256').update(text).digest('hex'),
      source_url: null, text
    });
    for (const entry of offsets) {
      const count = observations.length + 1;
      observations.push({
        observation_id: 'synthetic-observation-' + count,
        passage_id: sourceId + '-p' + count,
        source_id: sourceId, proposition_id: entry.prop,
        stance: entry.stance, review_status: 'synthetic_label',
        quote: entry.quote, start: entry.start, end: entry.end
      });
    }
    return sourceId;
  }
  for (const year of [2025, 2026]) {
    for (const actor of ACTORS) {
      const positions = { ...actor.positions };
      if (year === 2025 && actor.iso3 === 'ALP') {
        positions.ai_binding = 'oppose';
      }
      addSource(actor.iso3, actor.name, year, positions);
    }
  }
  // A duplicate translation of a single passage must not create a new vote.
  const first = sources.find(row => row.iso3 === 'USX' && row.date.startsWith('2026'));
  addSource(first.iso3, first.name, 2026, { ukr_sovereignty:'support' },
    { source_family_id: first.source_family_id });
  // Collective or unverified source rows must never acquire a national stance.
  addSource('ALP', 'Fictional Alpha', 2026, { cub_embargo:'oppose' },
    { attribution: 'collective' });
  addSource('DRL', 'Fictional Delta', 2026, { ukr_force:'oppose' },
    { status: 'unverified' });
  return {
    schema: SCHEMA, source_schema: 'un.review.v1',
    dataset_kind: 'synthetic_engineering', evaluation_role: 'engineering_only',
    publication_eligible: false, daily_adapter_integrated: false,
    codebook_version: codebook.version, sources, observations
  };
}
module.exports = { ACTORS, makeSyntheticFrame };
