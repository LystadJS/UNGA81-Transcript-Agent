/* Engineering fixtures only. Real-source browser checks are separate. */
const assert = require('node:assert/strict');
const test = require('node:test');
const A = require('../site/analysis-core.js');
const C = require('../site/collector.js');

const parameters = {
  topic: '', phrases: [], exclude: [],
  start: '2026-10-01', end: '2026-10-01',
  scope: 'committee_3', region: 'All regions', methods: A.METHODS
};

function record(id, text, extra = {}) {
  return {
    id, text, date: '2026-10-01', country: 'Example', region: 'Africa',
    scope: 'committee_3', language: 'en', meeting: 'Third Committee, meeting 1',
    source_url: 'https://transcripts.un.org/en/ga/c3/81/1',
    text_sha256: 'a'.repeat(64), ...extra
  };
}

const corpus = {
  schema: 'un.browser.corpus.v1', coverage: [], records: [
    record('1', 'Education and health'),
    record('2', 'AI safeguards', { region: 'Asia-Pacific' }),
    record('3', 'Education   and health'),
    record('4', 'Later meeting', { date: '2026-10-02' }),
    record('5', 'French track', { language: 'fr' }),
    record('6', 'Other committee', {
      scope: 'committee_2', meeting: 'Second Committee, meeting 1',
      source_url: 'https://transcripts.un.org/en/ga/c2/81/1'
    })
  ]
};

const countries = [{ country: 'Example', iso3: 'EXA', aliases: 'Example', region: 'Africa' }];
const meeting = {
  date: '2026-10-01T00:00:00Z', slug: 'ga/c3/81/1',
  title: 'Third Committee, 1st plenary meeting - General Assembly, 81st session',
  pageUrl: '/en/ga/c3/81/1', jsonUrl: '/en/ga/c3/81/1.json', hasTranscript: true
};
const document = {
  video: { slug: meeting.slug, date: meeting.date },
  transcript: { language: 'en', data: [
    { speaker: { affiliation: 'EXA' }, paragraphs: [{ sentences: [{ text: 'Health matters' }] }] }
  ] }
};

function requestFor(doc = document, inventory = [meeting]) {
  return async url => ({
    hash: 'f'.repeat(64),
    data: url.includes('meetings.json')
      ? { page: 1, total: inventory.length, hasMore: false, meetings: inventory }
      : doc
  });
}


test('Blank Topic includes every eligible unique passage and keeps raw originals', async () => {
  const before = JSON.stringify(corpus);
  const result = await A.analyze(corpus, parameters);
  assert.equal(result.parameters.mode, 'all');
  assert.equal(result.counts.input, 6);
  assert.equal(result.counts.eligible_before_dedup, 3);
  assert.equal(result.counts.duplicates, 1);
  assert.equal(result.counts.matched, 2);
  assert.equal(result.methods.similarity.compared, 1);
  assert.equal(JSON.stringify(corpus), before);
  assert.equal(parameters.mode, undefined);
});


test('Whitespace Topic ignores stale related and exclusion filters', async () => {
  const result = await A.analyze(corpus, {
    ...parameters, topic: ' \t ', phrases: ['AI'], exclude: ['Education']
  });
  assert.equal(result.counts.matched, 2);
  assert.deepEqual(result.parameters.phrases, []);
  assert.deepEqual(result.parameters.exclude, []);
});


test('Blank Topic retains region, date, scope, and language restrictions', async () => {
  const result = await A.analyze(corpus, { ...parameters, region: 'Africa' });
  assert.deepEqual(result.matched.map(row => row.id), ['1']);
  assert.equal(result.methods.frequency[0].total, 1);
  assert.equal(result.methods.timeline[0].total, 1);
});


test('Nonblank Topic preserves topic and exclusion matching', async () => {
  const p = { ...parameters, topic: 'AI', phrases: ['AI'] };
  assert.equal((await A.analyze(corpus, p)).counts.matched, 1);
  assert.equal((await A.analyze(corpus, { ...p, exclude: ['safeguards'] })).counts.matched, 0);
});


test('Blank mode does not weaken date, size, method, or scope validation', () => {
  for (const change of [
    { start: '2026-02-30' }, { end: '2026-11-02' }, { scope: 'anything' },
    { methods: ['llm'] }, { topic: 'x'.repeat(121) }, { topic: '!!!' }
  ]) assert.throws(() => A.parameters({ ...parameters, ...change }));
});


test('Collector reports successful daily inventory and passage counts', async () => {
  const result = await C.collect(parameters, countries, { request: requestFor() });
  assert.equal(result.records.length, 1);
  assert.equal(result.collection.collected_passages, 1);
  assert.equal(result.collection.collected_meetings, 1);
  assert.deepEqual(result.collection.inventory_days, [
    { date: '2026-10-01', status: 'ok', meetings: 1, selected: 1 }
  ]);
});


test('No in-scope meetings remains distinct from inventory failure', async () => {
  const empty = await C.collect(parameters, countries, { request: requestFor(document, []) });
  assert.equal(empty.collection.selected_meetings, 0);
  assert.equal(empty.collection.failed_inventory_days, 0);
  const failed = await C.collect(parameters, countries, {
    request: async () => { throw Error('Blocked network'); }
  });
  assert.equal(failed.collection.failed_inventory_days, 1);
  assert.equal(failed.coverage[0].status, 'inventory_failed');
  assert.equal(failed.collection.inventory_days[0].error, 'Blocked network');
});


test('Pending, empty, non-English, and failed transcripts remain distinguishable', async () => {
  const cases = [
    [{ video: document.video, transcript: null }, 'unavailable'],
    [{ ...document, transcript: { language: 'en', data: [] } }, 'empty_transcript'],
    [{ ...document, transcript: { language: 'fr', data: [] } }, 'excluded_language'],
    [{ ...document, video: { ...document.video, slug: 'wrong' } }, 'failed']
  ];
  for (const [doc, expected] of cases) {
    const result = await C.collect(parameters, countries, { request: requestFor(doc) });
    assert.equal(result.coverage[0].status, expected);
    assert.equal(result.records.length, 0);
    assert.equal(result.collection.collected_meetings, 0);
  }
});
