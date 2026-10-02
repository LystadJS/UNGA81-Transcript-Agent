/* Synthetic engineering fixtures. These are not substantive transcript findings. */
const assert = require('node:assert/strict');
const test = require('node:test');

const Scopes = require('../site/meeting-scopes.js');
const Analysis = require('../site/analysis-core.js');
const Collector = require('../site/collector.js');

const DATE = '2026-10-01';
const WORDS = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth'];
const NUMBERS = ['1st', '2nd', '3rd', '4th', '5th', '6th'];

const settings = {
  topic: 'AI',
  phrases: ['AI'],
  exclude: [],
  start: DATE,
  end: DATE,
  region: 'All regions',
  scope: 'committee_3',
  methods: Analysis.METHODS
};

const countries = [
  { country: 'Example', iso3: 'EXA', aliases: 'Example', region: 'Africa' }
];

function meeting(number, overrides = {}) {
  const slug = `ga/c${number}/81/1`;

  return {
    slug,
    title: `${WORDS[number - 1]} Committee, 1st plenary meeting - General Assembly, 81st session`,
    date: DATE + 'T10:00:00Z',
    pageUrl: '/en/' + slug,
    jsonUrl: '/en/' + slug + '.json',
    hasTranscript: true,
    ...overrides
  };
}

function record(number, overrides = {}) {
  const source = meeting(number);

  return {
    id: source.slug + '#0',
    date: DATE,
    country: 'Example',
    region: 'Africa',
    language: 'en',
    scope: 'other', // Deliberately emulate an older collection.
    meeting: source.title,
    text: `AI engineering fixture ${number}`,
    source_url: 'https://transcripts.un.org' + source.pageUrl,
    text_sha256: 'a'.repeat(64),
    ...overrides
  };
}

function corpus(records, scope = 'all') {
  return {
    schema: 'un.browser.corpus.v1',
    collection: { start: DATE, end: DATE, scope },
    coverage: [],
    records
  };
}

function mockedService(meetings, requested = [], transform = value => value) {
  return async url => {
    requested.push(url);

    if (url.includes('meetings.json')) {
      return {
        hash: 'f'.repeat(64),
        data: { page: 1, total: meetings.length, hasMore: false, meetings }
      };
    }

    const source = meetings.find(item => url.endsWith(item.jsonUrl));
    assert.ok(source, 'Only an inventoried transcript may be requested.');

    return {
      hash: 'f'.repeat(64),
      data: transform({
        video: { slug: source.slug, date: source.date },
        transcript: {
          language: 'en',
          data: [{
            speaker: { affiliation: 'EXA' },
            paragraphs: [{ sentences: [{ text: 'AI engineering fixture ' + source.slug }] }],
            pageUrl: source.pageUrl + '?t=0'
          }]
        }
      })
    };
  };
}


for (let number = 1; number <= 6; number++) {
  test(`Committee ${number}: canonical paths, word/ordinal titles, and scope validation`, () => {
    const expected = 'committee_' + number;

    assert.equal(Scopes.classifyMeeting(meeting(number)), expected);
    assert.equal(Scopes.classifyMeeting({ slug: `ga/c${number}/81/1` }), expected);
    assert.equal(Scopes.classifyMeeting({ title: `${WORDS[number - 1]} Committee, meeting` }), expected);
    assert.equal(Scopes.classifyMeeting({ title: `${NUMBERS[number - 1]} Committee — meeting` }), expected);
    assert.equal(Scopes.classifyMeeting({ title: `General Assembly: ${WORDS[number - 1]} Committee` }), expected);
    assert.equal(Analysis.parameters({ ...settings, scope: expected }).scope, expected);
    assert.equal(Scopes.recordScope(record(number)), expected);
  });

  test(`Committee ${number}: live collection requests only that committee's transcript`, async () => {
    const meetings = WORDS.map((_, index) => meeting(index + 1));
    const requested = [];
    const output = await Collector.collect(
      { ...settings, scope: 'committee_' + number },
      countries,
      { request: mockedService(meetings, requested) }
    );

    assert.equal(output.collection.inventory_meetings, 6);
    assert.equal(output.collection.selected_meetings, 1);
    assert.equal(output.collection.scope, 'committee_' + number);
    assert.equal(output.records.length, 1);
    assert.equal(output.records[0].scope, 'committee_' + number);
    assert.equal(output.coverage[0].scope, 'committee_' + number);
    assert.equal(output.records[0].text_sha256, await Collector.sha(output.records[0].text));
    assert.equal(requested.length, 2); // One inventory + one selected transcript.
    assert.ok(requested[1].includes(`/ga/c${number}/`));
  });
}


test('Third Committee general debate is not the GA General Debate', () => {
  const title = 'Third Committee — General Debate';

  assert.equal(Scopes.classifyMeeting({ title }), 'committee_3');
  assert.equal(Scopes.matchesMeeting({ title }, 'general_debate'), false);
  assert.equal(Scopes.recordScope(record(3, { scope: 'general_debate', meeting: title })), 'committee_3');
});


test('Only metadata determines committee membership; speech mentions and press briefings do not', () => {
  assert.equal(Scopes.classifyMeeting({
    title: 'General Debate',
    text: 'We mentioned the Third Committee.'
  }), 'general_debate');

  assert.equal(Scopes.classifyMeeting({ title: 'Press briefing about Third Committee' }), 'other');
  assert.equal(Scopes.classifyMeeting({ title: 'Legal Committee - International Maritime Organization' }), 'other');
  assert.equal(Scopes.committeeFromPath('https://attacker.test/en/ga/c3/81/1'), null);
  assert.equal(Scopes.committeeFromPath('/en/ga/c30/81/1'), null);
});


test('Full committee names require GA context or an explicit committee number', () => {
  assert.equal(Scopes.classifyMeeting({
    title: 'Social, Humanitarian & Cultural Issues (Third Committee)'
  }), 'committee_3');

  assert.equal(Scopes.classifyMeeting({ title: 'Legal Committee - General Assembly' }), 'committee_6');
});


test('Canonical paths take priority over titles; conflicting paths stay unclassified', () => {
  assert.equal(Scopes.classifyMeeting(meeting(2, { title: 'Third Committee' })), 'committee_2');

  const conflict = record(3, {
    id: 'ga/c2/81/1#0',
    scope: 'committee_3'
  });

  assert.equal(Scopes.recordScope(conflict), 'other');
});


test('Older broad collections can be narrowed without mutating the original data', async () => {
  const original = corpus(WORDS.map((_, index) => record(index + 1)));
  const output = await Analysis.analyze(original, settings);

  assert.equal(output.counts.input, 6);
  assert.equal(output.counts.eligible, 1);
  assert.equal(output.counts.matched, 1);
  assert.equal(output.matched[0].scope, 'committee_3');
  assert.equal(output.matched[0].scope_original, 'other');
  assert.equal(output.methods.frequency[0].total, 1);
  assert.equal(original.records[2].scope, 'other');
});


test('Scope filtering precedes deduplication, language, regional denominators and matches', async () => {
  const records = [
    record(2, { text: 'AI same text' }),
    record(3, { text: 'AI same text' }),
    record(3, { id: 'ga/c3/81/1#1', text: 'AI France', language: 'fr' }),
    record(3, { id: 'ga/c3/81/1#2', text: 'AI Asia', region: 'Asia-Pacific' })
  ];

  const output = await Analysis.analyze(corpus(records), { ...settings, region: 'Africa' });

  assert.equal(output.counts.eligible, 1);
  assert.equal(output.counts.duplicates, 0);
  assert.equal(output.counts.matched, 1);
  assert.equal(output.matched[0].id, 'ga/c3/81/1#0');
});


test('Saved-collection coverage never expands a narrow scope', () => {
  for (const option of Scopes.OPTIONS) {
    assert.equal(Scopes.covers('all', option.value), true);
    assert.equal(Scopes.covers(option.value, option.value), true);
  }

  assert.equal(Scopes.covers('general_debate', 'committee_3'), false);
  assert.equal(Scopes.covers('committee_2', 'committee_3'), false);
  assert.equal(Scopes.covers('committee_3', 'all'), false);
  assert.equal(Scopes.covers(undefined, 'committee_3'), false);
});


test('Unsupported scope fails before any network request', async () => {
  assert.throws(() => Analysis.parameters({ ...settings, scope: 'committee_7' }));

  await assert.rejects(() => Collector.collect(
    { ...settings, scope: 'committee_7' },
    countries,
    { request: async () => assert.fail('Must not request the network.') }
  ), /Invalid meeting scope/);
});


test('No matching committee produces an explicit zero-selection collection', async () => {
  const output = await Collector.collect(settings, countries, {
    request: mockedService([meeting(2)])
  });

  assert.equal(output.collection.inventory_meetings, 1);
  assert.equal(output.collection.selected_meetings, 0);
  assert.equal(output.records.length, 0);
});


test('Unavailable and non-English committee transcripts remain in coverage', async () => {
  const unavailable = await Collector.collect(settings, countries, {
    request: mockedService([meeting(3, { hasTranscript: false })])
  });

  assert.equal(unavailable.coverage[0].status, 'unavailable');
  assert.equal(unavailable.records.length, 0);

  const nonEnglish = await Collector.collect(settings, countries, {
    request: mockedService([meeting(3)], [], data => ({
      ...data, transcript: { ...data.transcript, language: 'fr' }
    }))
  });

  assert.equal(nonEnglish.coverage[0].status, 'excluded_language');
  assert.equal(nonEnglish.records.length, 0);
});


test('Legacy General Debate and all-meetings scopes remain supported', async () => {
  const general = meeting(3, {
    slug: 'ga/81/11',
    pageUrl: '/en/ga/81/11',
    jsonUrl: '/en/ga/81/11.json',
    title: 'General Debate, General Assembly, 81st session'
  });

  const meetings = [general, meeting(3)];

  const debate = await Collector.collect({ ...settings, scope: 'general_debate' }, countries, {
    request: mockedService(meetings)
  });

  const all = await Collector.collect({ ...settings, scope: 'all' }, countries, {
    request: mockedService(meetings)
  });

  assert.equal(debate.records.length, 1);
  assert.equal(debate.records[0].scope, 'general_debate');
  assert.equal(all.records.length, 2);
});
