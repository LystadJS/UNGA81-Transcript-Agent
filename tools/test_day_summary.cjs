'use strict';

const assert = require('node:assert/strict');
const DaySummary = require('../site/day-summary.js');
const DaySummaryView = require('../site/day-summary-view.js');

const date = '2026-11-05';
const meetingA = 'ga/plenary/81/42';
const meetingB = 'sc/81/10021';
const source = slug => `https://transcripts.un.org/en/${slug}`;
const record = (slug, n, country, text, title) => ({
  id: `${slug}#${n}`,
  meeting_slug: slug,
  date,
  country,
  region: 'Synthetic region',
  language: 'en',
  scope: slug.startsWith('sc/') ? 'security_council' : 'ga_plenary',
  meeting: title,
  text,
  source_url: source(slug),
  text_sha256: String(n).padStart(64, 'a').slice(-64),
  attribution: {country_status: 'registry_mapped'},
  speaker_metadata: {affiliation_full: country, function: 'Representative', group: 'National delegation'}
});

// Synthetic policy language deliberately mixes synonyms, nearby but distinct
// policy questions, procedural text, and an issue outside the old fixed themes.
const records = [
  record(meetingA, 1, 'Country A',
    'We call for an immediate ceasefire in Gaza and propose monitored humanitarian pauses. We support unhindered humanitarian access through all crossings.',
    'General Assembly plenary — synthetic'),
  record(meetingB, 2, 'Country B',
    'We demand an immediate cessation of hostilities in Gaza. The parties have signed a monitored ceasefire in Gaza today.',
    'Security Council — synthetic'),
  record(meetingB, 3, 'Country C',
    'We oppose the proposed Gaza ceasefire because it omits the release of hostages. We nevertheless support protected humanitarian access for relief convoys.',
    'Security Council — synthetic'),
  record(meetingA, 4, 'Country D',
    'We propose a new climate finance facility for vulnerable states. We also call for binding national emissions reductions by 2035.',
    'General Assembly plenary — synthetic'),
  record(meetingA, 5, 'Country E',
    'We reject mandatory emissions cuts on developing countries, while supporting additional climate adaptation finance.',
    'General Assembly plenary — synthetic'),
  record(meetingA, 6, 'Country F',
    'We call for negotiations on a legally binding treaty prohibiting autonomous weapons that select targets without human control.',
    'General Assembly plenary — synthetic'),
  record(meetingA, 7, 'Country G',
    'Thank you, Mr. President. I congratulate you on your election and now yield the floor to the next speaker.',
    'General Assembly plenary — synthetic')
];

let checks = 0;
function check(name, fn) {
  fn();
  checks += 1;
  console.log('PASS', name);
}

const result = DaySummary.build(records, {date});
const topics = result.topics || [];
const findTopic = (...terms) => topics.find(topic => {
  const haystack = `${topic.id || ''} ${topic.label || ''}`.toLowerCase();
  return terms.every(term => haystack.includes(term));
});
const ceasefire = topics.find(topic => /ceasefire|cessation of hostilities|truce/i.test(`${topic.id} ${topic.label}`));
const access = topics.find(topic => /humanitarian access|relief access/i.test(`${topic.id} ${topic.label}`));
const finance = topics.find(topic => /climate.*financ|financ.*climate/i.test(`${topic.id} ${topic.label}`));
const emissions = topics.find(topic => /emission/i.test(`${topic.id} ${topic.label}`));
const autonomous = topics.find(topic => /autonomous weapon/i.test(`${topic.id} ${topic.label}`));

check('builds one day-level report from all selected meetings', () => {
  assert.equal(result.date, date);
  assert.equal(result.stats.meetings, 2);
  assert.equal(result.stats.source_segments || result.stats.eligible_english_segments, records.length);
});

check('synonymous ceasefire language resolves to one policy question', () => {
  assert.ok(ceasefire, 'expected a Gaza ceasefire topic');
  assert.ok(ceasefire.coverage.source_segments >= 3);
  assert.equal(ceasefire.coverage.meetings, 2);
  assert.ok(!topics.some(topic => topic !== ceasefire && /cessation of hostilities|\btruce\b/i.test(`${topic.id} ${topic.label}`)));
});

check('meeting-specific distinctions survive the combined day summary', () => {
  const rows = ceasefire.meeting_breakdown || ceasefire.meetings || [];
  const ids = new Set(rows.map(row => row.meeting_slug || row.meeting_id || row.id));
  assert.deepEqual(ids, new Set([meetingA, meetingB]));
});

check('nearby policy questions remain separate', () => {
  assert.ok(access && access !== ceasefire, 'humanitarian access must not collapse into ceasefire');
  assert.ok(finance && emissions && finance !== emissions, 'climate finance and emissions cuts must remain separate');
});

check('finds a substantive issue beyond the former fixed theme families', () => {
  assert.ok(autonomous, 'expected source-derived autonomous-weapons policy question');
  assert.ok((autonomous.proposals || []).length > 0);
});

check('procedural and ceremonial-only remarks do not become topics', () => {
  assert.ok(!topics.some(topic => /congratulat|election|yield the floor|president/i.test(`${topic.id} ${topic.label}`)));
  assert.ok((result.stats.procedural_sentences || 0) + (result.stats.ceremonial_sentences || 0) >= 1);
  assert.ok(result.stats.substantive_sentences > 0);
});

check('summaries retain proposals, disagreements, and participating countries', () => {
  assert.ok((ceasefire.proposals || []).length > 0);
  assert.ok((ceasefire.disagreements || []).length > 0);
  const participants = new Set((ceasefire.participants || []).map(value => typeof value === 'string' ? value : value.country));
  assert.ok(participants.has('Country A'));
  assert.ok(participants.has('Country B'));
  assert.ok(participants.has('Country C'));
});

check('every substantive summary claim has inspectable source evidence', () => {
  let claimCount = 0;
  for (const topic of topics) {
    for (const key of ['proposals', 'disagreements', 'claims', 'consequential_developments']) {
      for (const claim of topic[key] || []) {
        claimCount += 1;
        assert.ok(String(claim.text || claim.claim || '').trim(), `${topic.id} ${key} claim lacks text`);
        assert.ok(Array.isArray(claim.evidence) && claim.evidence.length, `${topic.id} ${key} claim lacks evidence`);
        for (const item of claim.evidence) {
          assert.ok(item.record_id);
          assert.ok(item.meeting_slug);
          assert.ok(item.excerpt);
          assert.equal(new URL(item.source_url).host, 'transcripts.un.org');
        }
      }
    }
  }
  assert.ok(claimCount > 0);
});

check('consequential developments require explicit outcome language', () => {
  assert.ok(Array.isArray(result.consequential_developments));
  assert.ok(result.consequential_developments.some(item => /signed|truce/i.test(`${item.text || item.claim || ''} ${(item.evidence || []).map(e => e.excerpt).join(' ')}`)));
  assert.ok(!result.consequential_developments.some(item => /autonomous weapon/i.test(item.text || item.claim || '')), 'a proposal alone is not an observed development');
});

check('coverage is reported without converting passage volume into importance', () => {
  assert.ok(topics.every(topic => topic.coverage && Number.isInteger(topic.coverage.source_segments)));
  assert.ok(!topics.some(topic => Object.hasOwn(topic, 'importance') || Object.hasOwn(topic, 'importance_score')));
  const guidance = [...(result.limitations || []), ...Object.values(result.interpretation || {})];
  assert.ok(guidance.some(line => /count|frequency|coverage|volume/i.test(line) && /importance|consequen/i.test(line)));
});

check('unsafe source links never support a substantive claim', () => {
  const unsafe = DaySummary.build([
    {...records[0], id: `${meetingA}#unsafe`, source_url: 'http://example.invalid/transcript'}
  ], {date});
  for (const topic of unsafe.topics || []) {
    for (const key of ['proposals', 'disagreements', 'claims', 'consequential_developments']) {
      assert.equal((topic[key] || []).length, 0);
    }
  }
});

check('other days and non-English records do not bleed into the result', () => {
  const extra = [
    {...records[0], id: `${meetingA}#other-day`, date: '2026-11-04'},
    {...records[0], id: `${meetingA}#french`, language: 'fr'}
  ];
  const filtered = DaySummary.build([...records, ...extra], {date});
  assert.equal(filtered.stats.source_segments || filtered.stats.eligible_english_segments, records.length);
});

check('accessible view renders evidence links and explicit coverage caveat', () => {
  const html = DaySummaryView.render(result);
  assert.match(html, /Day-level proceedings summary|DAY BRIEFING/);
  assert.match(html, /Supporting passage/);
  assert.match(html, /does not measure political importance/);
  assert.match(html, /rel="noopener noreferrer"/);
  assert.doesNotMatch(html, /<script/i);
});

console.log(JSON.stringify({status: 'PASS', checks, synthetic: true}));
