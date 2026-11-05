'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
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

check('automatic visualizations declare passages, countries, and meetings', () => {
  const charts = result.visualizations;
  assert.equal(charts.topic_distribution.unit, 'distinct supporting passages');
  assert.match(charts.topic_country_matrix.unit, /country participation/);
  assert.match(charts.meeting_topic_overview.unit, /passages/);
  assert.equal(charts.topic_distribution.status, 'available');
  assert.equal(charts.topic_country_matrix.status, 'available');
  assert.equal(charts.meeting_topic_overview.status, 'available');
});

check('repeated passages cannot inflate national participation', () => {
  const repeated = DaySummary.build([...records, {...records[0], id: `${meetingA}#repeat`}], {date});
  const chart = repeated.visualizations.topic_country_matrix;
  const cell = chart.cells.find(item => item.country === 'Country A' && item.topic_id === ceasefire.id);
  assert.equal(cell.value, 1);
  assert.match(chart.deduplication, /at most once per topic/i);
  const baseRow = result.visualizations.topic_distribution.rows.find(row => row.topic_id === ceasefire.id);
  const repeatedRow = repeated.visualizations.topic_distribution.rows.find(row => row.topic_id === ceasefire.id);
  assert.equal(repeatedRow.value, baseRow.value, 'exact duplicate wording should not inflate distinct-passage distribution');
});

check('unavailable chart data is explicit', () => {
  const empty = DaySummary.build([records.at(-1)], {date});
  assert.equal(empty.visualizations.topic_distribution.status, 'insufficient');
  assert.ok(empty.visualizations.topic_distribution.reason);
  const html = DaySummaryView.render(empty);
  assert.match(html, /Insufficient data/);
});

check('every automatic chart has a table alternative and source drill-down', () => {
  const html = DaySummaryView.automaticVisualizations(result);
  assert.equal((html.match(/Readable table alternative/g) || []).length, 3);
  assert.equal((html.match(/source drill-down/g) || []).length, 3);
  assert.match(html, /Topic distribution/);
  assert.match(html, /Topic by country/);
  assert.match(html, /Meeting by topic/);
  assert.match(html, /https:\/\/transcripts\.un\.org/);
});

check('PCA, clustering and lexical methods are inside advanced controls', () => {
  const html = fs.readFileSync(path.join(__dirname, '../site/index.html'), 'utf8');
  const start = html.indexOf('<details id="advancedMethods">');
  const end = html.indexOf('</details>', html.indexOf('id="nmfSettings"'));
  assert.ok(start > -1 && end > start);
  const advanced = html.slice(start, end);
  for (const id of ['clusterMethod', 'representation', 'nmfMethod']) assert.match(advanced, new RegExp(`id="${id}"`));
  assert.doesNotMatch(html, /checked name="method" type="checkbox" value="(?:clusters|nmf|tfidf|similarity)"/);
});

check('source-derived topics require a self-contained policy object', () => {
  const guarded = DaySummary.build([
    record(meetingA, 20, 'Country A', 'We call for this to be swiftly verified by the relevant mechanisms.', 'Synthetic fragment guard'),
    record(meetingA, 21, 'Country A', 'We propose there to be a period and then we would add the following.', 'Synthetic procedure guard'),
    record(meetingA, 22, 'Country A', 'We call for negotiations on a legally binding treaty prohibiting autonomous weapons without meaningful human control.', 'Synthetic valid source topic')
  ], {date});
  assert.ok(guarded.topics.some(topic => /autonomous weapons/i.test(topic.label)));
  assert.ok(!guarded.topics.some(topic => /swiftly verified|period|add the following/i.test(topic.label)));
  assert.equal(DaySummary.actionObject('We call for this to be swiftly verified by the relevant mechanisms.'), null);
});

check('broad subjects split into distinct policy questions', () => {
  const split = DaySummary.build([
    record(meetingA, 30, 'Country A', 'We request suspension of troop rotations in United Nations peace operations.', 'Synthetic policy split'),
    record(meetingA, 31, 'Country B', 'The Security Council must give the peacekeeping mission resources required for its civilian-protection mandate.', 'Synthetic policy split'),
    record(meetingA, 32, 'Country C', 'Our action plan targets the prevention and eradication of human trafficking.', 'Synthetic policy split'),
    record(meetingA, 33, 'Country D', 'We call for progress in the implementation review mechanism of the UN Convention against Transnational Organized Crime.', 'Synthetic policy split')
  ], {date});
  for (const id of ['peacekeeping_troop_participation','peacekeeping_mandate_resources','human_trafficking','untoc_review']) assert.ok(split.topics.some(topic => topic.id === id), id);
  assert.ok(!split.topics.some(topic => topic.id === 'peacekeeping' && topic.coverage.source_segments === 2));
  assert.ok(!split.topics.some(topic => topic.id === 'organized_crime' && topic.coverage.source_segments === 2));
});

check('meeting administration is withheld before topic and claim extraction', () => {
  const procedural = DaySummary.build([
    record(meetingA, 40, 'Country A', 'Before proceeding further, I propose that the time limit for statements in this debate be five minutes for individual delegations.', 'Synthetic meeting procedure'),
    record(meetingA, 41, 'Country B', 'I want to point out that the footnote is at the very top of the document and should be shown on screen.', 'Synthetic document procedure'),
    record(meetingA, 42, 'Country C', 'The Bureau proposes that the meeting be held in person.', 'Synthetic meeting procedure'),
    record(meetingA, 43, 'Country D', 'We propose a technical addition to the draft report and will read it at dictation speed.', 'Synthetic document procedure')
  ], {date});
  assert.equal(procedural.topics.length, 0);
  assert.ok(procedural.stats.procedural_sentences >= 4);
});

check('collective statements retain the group and never enter country participation', () => {
  const collective = {...record(meetingA, 50, 'Country A', 'The regional group calls for unhindered humanitarian access through all crossings.', 'Synthetic collective'),speaker_metadata:{affiliation:'CTA',affiliation_full:'Country A',function:'Representative',group:'Regional Group'}};
  const national = record(meetingA, 51, 'Country B', 'We call for unhindered humanitarian access through all crossings.', 'Synthetic national');
  const grouped = DaySummary.build([collective,national], {date});
  const topic = grouped.topics.find(row => row.id === 'humanitarian_access');
  assert.deepEqual(topic.participating_countries, ['Country B']);
  assert.deepEqual(topic.participating_collectives, ['Regional Group']);
  assert.ok(topic.claims.some(item => item.text.startsWith('Regional Group records')));
  assert.ok(topic.supporting_passages.some(item => item.attribution_kind === 'collective' && item.recorded_country === 'Country A'));
  assert.ok(!grouped.visualizations.topic_country_matrix.countries.includes('Country A'));
  assert.ok(grouped.visualizations.topic_country_matrix.countries.includes('Country B'));
  const rendered = DaySummaryView.render(grouped);
  assert.match(rendered, /Collective statements:<\/strong> Regional Group/);
  assert.match(rendered, /Collective: Regional Group · recorded affiliation Country A/);
});

check('requested condemnation is one proposal rather than a duplicate disagreement', () => {
  const one = DaySummary.build([
    record(meetingA, 60, 'Country A', 'We call for the Council to condemn the attack on civilians and demand that it not be repeated.', 'Synthetic claim cue')
  ], {date});
  const topic = one.topics.find(row => row.id === 'civilian_protection');
  assert.equal(topic.proposals.length, 1);
  assert.equal(topic.disagreements.length, 0);
});

console.log(JSON.stringify({status: 'PASS', checks, synthetic: true}));
