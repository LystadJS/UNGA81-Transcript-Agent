/* Browser exploratory engine. Independent of frozen D1 and reviewed models. */
(function (root) {
  'use strict';

  const Scopes = typeof module !== 'undefined' && module.exports
    ? require('./meeting-scopes.js')
    : root.UNMeetingScopes;

  const ClusterOptions = typeof module !== 'undefined' && module.exports
    ? require('./cluster-options.js') : root.UNClusterOptions;
  const NMFOptions = typeof module !== 'undefined' && module.exports
    ? require('./nmf-options.js') : root.UNNMFOptions;
  const PassageSelection = typeof module !== 'undefined' && module.exports
    ? require('./passage-selection.js') : root.UNPassageSelection;
  const VERSION = 'browser-descriptive-1.10.0';

  const METHODS = ['frequency', 'timeline', 'length', 'tfidf', 'similarity', 'clusters', 'nmf'];

  const STOP = new Set(
    ('a an and are as at be been being but by can could did do does for from ' +
     'had has have he her his i if in into is it its may more most not of on ' +
     'or our she should so than that the their them there these they this ' +
     'those to under up us was we were what when where which who will with ' +
     'would you your').split(' ')
  );

  const tokens = text => (
    text.normalize('NFKC').toLowerCase().match(/[\p{L}\p{N}]+/gu) || []
  );

  const canonical = text => tokens(text).join(' ');


  // Validate user settings before collecting or analyzing any text.
  function dateOK(value) {
    return typeof value === 'string' &&
      /^\d{4}-\d{2}-\d{2}$/.test(value) &&
      Number.isFinite(Date.parse(value)) &&
      new Date(value).toISOString().slice(0, 10) === value;
  }


  function parameters(p) {
    if (!p || typeof p.topic !== 'string' || p.topic.length > 120) {
      throw Error('Use an optional topic of at most 120 characters.');
    }

    const topic = p.topic.trim();
    const mode = topic ? 'topic' : 'all';

    if (topic && !canonical(topic)) {
      throw Error('A topic must contain at least one letter or number.');
    }

    // A blank Topic explicitly means ALL passages. Stale related/exclusion
    // fields must not silently narrow this request; the UI disables them too.
    const phrases = mode === 'all' ? [] : p.phrases;
    const exclude = mode === 'all' ? [] : p.exclude;

    if (!dateOK(p.start) || !dateOK(p.end) || p.end < p.start) {
      throw Error('Enter a valid inclusive date range.');
    }

    if ((Date.parse(p.end) - Date.parse(p.start)) / 86400000 > 30) {
      throw Error('Use a date range of at most 31 days per collection.');
    }

    if (!Array.isArray(p.methods) || !p.methods.length ||
        p.methods.some(method => !METHODS.includes(method))) {
      throw Error('Choose at least one supported method.');
    }

    if (!Array.isArray(phrases) || (mode === 'topic' && !phrases.length) ||
        phrases.length > 20 || phrases.some(value => typeof value !== 'string' ||
          !canonical(value) || value.length > 120)) {
      throw Error('Use 1–20 topic phrases, or leave Topic blank to include all passages.');
    }

    if (!Array.isArray(exclude) || exclude.length > 20 ||
        exclude.some(value => typeof value !== 'string' ||
          !canonical(value) || value.length > 120)) {
      throw Error('Use at most 20 valid exclusion phrases.');
    }

    if (!Scopes.isValid(p.scope) || typeof p.region !== 'string') {
      throw Error('Invalid collection scope.');
    }

    const clustering = p.methods.includes('clusters') ? ClusterOptions.options(p.clustering) : undefined;
    const nmf=p.methods.includes('nmf')?NMFOptions.options(p.nmf):undefined;
    return { ...p, topic, mode, phrases, exclude, ...(p.methods.includes('clusters')?{clustering}:{}),...(nmf?{nmf}:{}) };
  }


  const hasPhrase = (body, phrase) => (
    (' ' + body + ' ').includes(' ' + canonical(phrase) + ' ')
  );


  // Hashes establish text integrity; imported metadata remains author-supplied.
  function validateCorpus(corpus) {
    if (!corpus || corpus.schema !== 'un.browser.corpus.v1' ||
        !Array.isArray(corpus.records) || corpus.records.length > 15000 ||
        !Array.isArray(corpus.coverage)) {
      throw Error('Use a collected transcript JSON exported by this workspace (un.browser.corpus.v1).');
    }

    const ids = new Set();
    let size = 0;

    for (const record of corpus.records) {
      const required = [
        'id', 'date', 'country', 'region', 'language', 'scope',
        'text', 'source_url', 'meeting', 'text_sha256'
      ];

      for (const key of required) {
        if (typeof record[key] !== 'string') {
          throw Error('Missing transcript field: ' + key);
        }
      }

      if (!record.id || ids.has(record.id) || !dateOK(record.date) ||
          !record.text.trim() || record.text.length > 500000 ||
          !/^[a-f0-9]{64}$/.test(record.text_sha256)) {
        throw Error('Invalid transcript identity, date, text or hash.');
      }

      if (!/^https:\/\//.test(record.source_url)) {
        throw Error('Transcript sources must use HTTPS.');
      }

      new URL(record.source_url);
      ids.add(record.id);
      size += record.text.length;
    }

    if (size > 20000000) {
      throw Error('Corpus text exceeds 20 million characters.');
    }

    return corpus;
  }


  function distribution(records, key, hitIds) {
    const bins = new Map();

    for (const record of records) {
      const name = record[key] || 'Unmapped';
      const bin = bins.get(name) || { name, total: 0, matches: 0 };

      bin.total++;
      if (hitIds.has(record.id)) bin.matches++;
      bins.set(name, bin);
    }

    return [...bins.values()]
      .map(bin => ({ ...bin, percent: 100 * bin.matches / bin.total }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }


  // Sublinear term frequency, smoothed inverse document frequency, L2 scaling.
  function tfidf(records) {
    const counts = records.map(record => {
      const frequencies = new Map();

      for (const term of tokens(record.text)) {
        if (term.length > 2 && !STOP.has(term)) {
          frequencies.set(term, (frequencies.get(term) || 0) + 1);
        }
      }

      return frequencies;
    });

    const documentFrequency = new Map();

    for (const frequencies of counts) {
      for (const term of frequencies.keys()) {
        documentFrequency.set(term, (documentFrequency.get(term) || 0) + 1);
      }
    }

    const vectors = counts.map(frequencies => {
      const vector = new Map();
      let sum = 0;

      for (const [term, count] of frequencies) {
        const weight = (1 + Math.log(count)) *
          (1 + Math.log((1 + records.length) / (1 + documentFrequency.get(term))));

        vector.set(term, weight);
        sum += weight * weight;
      }

      const norm = Math.sqrt(sum) || 1;

      for (const [term, weight] of vector) {
        vector.set(term, weight / norm);
      }

      return vector;
    });

    const sums = new Map();

    for (const vector of vectors) {
      for (const [term, weight] of vector) {
        sums.set(term, (sums.get(term) || 0) + weight);
      }
    }

    const terms = [...sums]
      .map(([term, sum]) => ({
        term,
        mean: sum / (records.length || 1),
        documents: documentFrequency.get(term)
      }))
      .sort((a, b) => b.mean - a.mean || a.term.localeCompare(b.term))
      .slice(0, 20);

    return { vectors, terms, vocabulary: documentFrequency.size };
  }


  async function analyze(corpus, p, yieldProgress = async () => {}, runClusters, runNMF) {
    validateCorpus(corpus);
    p = parameters(p);

    // Apply committee, date, region and language restrictions before deduping.
    // This prevents out-of-scope text from changing denominators or matches.
    const selection=PassageSelection.validate(corpus,p.passageSelection);
    const beforeTypes = corpus.records.filter(record => (
      record.date >= p.start &&
      record.date <= p.end &&
      (p.region === 'All regions' || record.region === p.region) &&
      Scopes.matchesRecord(record, p.scope) &&
      record.language === 'en'
    ));

    const eligible=selection?beforeTypes.filter(r=>selection.selected.has(r.id)):beforeTypes;
    const records = [];
    const duplicates = [];
    const seen = new Map();

    for (const original of eligible) {
      const scope = Scopes.recordScope(original);
      const record = scope === original.scope
        ? original
        : { ...original, scope_original: original.scope, scope };

      const key = record.text.normalize('NFKC').replace(/\s+/g, ' ').trim();

      if (seen.has(key)) {
        duplicates.push({
          id: record.id,
          retained_id: seen.get(key),
          source_url: record.source_url
        });
      } else {
        seen.set(key, record.id);
        records.push(record);
      }
    }

    const matched = p.mode === 'all' ? [...records] : records.filter(record => {
      const body = canonical(record.text);

      return p.phrases.some(phrase => hasPhrase(body, phrase)) &&
        !p.exclude.some(phrase => hasPhrase(body, phrase));
    });

    const ids = new Set(matched.map(record => record.id));

    const result = {
      engine: VERSION,
      parameters: p,
      created_at: new Date().toISOString(),
      source: corpus.origin || 'Imported corpus',
      collection: corpus.collection || null,
      coverage: corpus.coverage,
      counts: {
        input: corpus.records.length,
        eligible_before_dedup: eligible.length,
        duplicates: duplicates.length,
        eligible: records.length,
        matched: matched.length,
        unmapped: records.filter(record => record.region === 'Unmapped').length
      },
      duplicates,
      matched,
      methods: {}
    };
    if(selection){const {selected,...audit}=selection;result.passage_selection={...audit,eligible_before_type_filter:beforeTypes.length,eligible_after_type_filter:eligible.length,excluded_within_filters:beforeTypes.filter(r=>!selected.has(r.id)).map(r=>r.id)};}

    if (p.methods.includes('frequency')) {
      result.methods.frequency = distribution(records, 'region', ids);
    }

    if (p.methods.includes('timeline')) {
      result.methods.timeline = distribution(records, 'date', ids);
    }

    if (p.methods.includes('length')) {
      const bins = [
        { name: '0–99 words', max: 99, total: 0 },
        { name: '100–499 words', max: 499, total: 0 },
        { name: '500–999 words', max: 999, total: 0 },
        { name: '1,000+ words', max: Infinity, total: 0 }
      ];

      for (const record of matched) {
        const count = tokens(record.text).length;
        bins.find(bin => count <= bin.max).total++;
      }

      result.methods.length = bins.map(({ name, total }) => ({ name, total }));
    }

    if (p.methods.includes('clusters') && matched.length>600) {
      result.methods.clusters = {parameters:p.clustering,skipped:'Clustering supports at most 600 selected passages. Narrow the dates, topic or region; no sampling was applied.'};
    }
    if(p.methods.includes('nmf')&&matched.length>600)result.methods.nmf={parameters:p.nmf,skipped:'NMF supports at most 600 selected passages. Narrow the collection; no sampling was applied.'};
    if (p.methods.some(method => ['tfidf', 'similarity'].includes(method)) ||
        (p.methods.includes('nmf')&&!result.methods.nmf) ||
        (p.methods.includes('clusters') && !result.methods.clusters)) {
      await yieldProgress('Calculating TF-IDF');
      const terms = tfidf(matched);

      if(p.methods.includes('nmf')&&!result.methods.nmf){
        const runner=runNMF||((records,vectors,settings,progress)=>{
          if(typeof module==='undefined'||!module.exports)throw Error('NMF worker is unavailable. Reload the page.');
          return require('./nmf-core.js').run(records,vectors,settings,progress);
        });
        result.methods.nmf=await runner(matched,terms.vectors,p.nmf,yieldProgress);
      }

      if (p.methods.includes('clusters') && !result.methods.clusters) {
        const runner = runClusters || ((records,vectors,settings,progress) => {
          if (typeof module === 'undefined' || !module.exports) throw Error('Clustering worker is unavailable. Reload the page.');
          return require('./cluster-core.js').run(records,vectors,settings,progress);
        });
        result.methods.clusters = await runner(matched,terms.vectors,p.clustering,yieldProgress);
      }

      if (p.methods.includes('tfidf')) {
        result.methods.tfidf = {
          terms: terms.terms,
          vocabulary: terms.vocabulary
        };
      }

      if (p.methods.includes('similarity')) {
        if (matched.length > 300) {
          result.methods.similarity = {
            skipped: 'Pairwise similarity requires at most 300 matched segments. Narrow the topic, dates or region.'
          };
        } else {
          const pairs = [];

          for (let i = 0; i < terms.vectors.length; i++) {
            for (let j = i + 1; j < terms.vectors.length; j++) {
              let score = 0;

              for (const [term, weight] of terms.vectors[i]) {
                score += weight * (terms.vectors[j].get(term) || 0);
              }

              pairs.push({
                left: matched[i].id,
                right: matched[j].id,
                cosine: Math.min(1, score)
              });
            }

            if (i % 25 === 0) await yieldProgress('Comparing text similarity');
          }

          pairs.sort((a, b) => (
            b.cosine - a.cosine ||
            a.left.localeCompare(b.left) ||
            a.right.localeCompare(b.right)
          ));

          result.methods.similarity = {
            pairs: pairs.slice(0, 10),
            compared: pairs.length
          };
        }
      }
    }

    return result;
  }


  const api = {
    VERSION,
    METHODS,
    tokens,
    canonical,
    dateOK,
    parameters,
    validateCorpus,
    hasPhrase,
    tfidf,
    analyze
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.UNAnalysis = api;
  }

})(typeof globalThis !== 'undefined' ? globalThis : this);
