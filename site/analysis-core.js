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
  const ReviewedUnits = typeof module !== 'undefined' && module.exports
    ? require('./reviewed-units.js') : root.UNReviewedUnits;
  const MeetingQuickReader = typeof module !== 'undefined' && module.exports
    ? require('./meeting-quick-reader.js') : root.UNMeetingQuickReader;
  const TextUnits = typeof module !== 'undefined' && module.exports
    ? require('./text-units.js') : root.UNTextUnits;
  const VERSION = 'browser-descriptive-1.15.0';

  const METHODS = ['frequency', 'timeline', 'length', 'tfidf', 'similarity', 'clusters', 'nmf'];

  const STOP = new Set(
    ('a an and are as at be been being but by can could did do does for from ' +
     'had has have he her his i if in into is it its may more most not of on ' +
     'or our she should so than that the their them there these they this ' +
     'those to under up us was we were what when where which who will with ' +
     'would you your').split(' ')
  );

  const tokens = TextUnits.tokens;

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

    if(p.meeting_slug!==undefined && (typeof p.meeting_slug!=='string'||!/^[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+){1,5}$/.test(p.meeting_slug)||p.start!==p.end||p.meeting_date!==p.start)) throw Error('Individual meeting analysis requires one valid meeting ID and its exact date.');
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
  function tfidf(records, options = {}) {
    const proceduralStop = new Set(['thank','thanks','floor','representative','representatives','statement','statements','give','madam','chair','distinguished','excellencies','excellency','colleagues','mr','mrs','ms','now','speaking','behalf','much','very']);
    const processed = records.map(record => options.reduceProceduralNoise
      ? TextUnits.reduceProceduralNoise(record.text) : {text:record.text,removed_sentence_count:0});
    const processing = {method:options.reduceProceduralNoise ? 'narrow_procedural_sentences_v4' : 'original_text',
      original_included_count:records.length,
      removed_sentence_count:processed.reduce((sum,item)=>sum+item.removed_sentence_count,0),
      zero_text_ids:records.filter((r,i)=>!TextUnits.wordCount(processed[i].text)).map(r=>r.id)};
    if(options.reduceProceduralNoise)processing.procedural_stoplist=[...proceduralStop];
    const counts = records.map((record,index) => {
      const frequencies = new Map();

      for (const term of tokens(processed[index].text)) {
        if (term.length > 2 && !STOP.has(term) && !(options.reduceProceduralNoise && proceduralStop.has(term))) {
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

    processing.zero_vector_ids=records.filter((r,i)=>vectors[i].size===0).map(r=>r.id);
    return { vectors, terms, vocabulary: documentFrequency.size, processing };
  }


  // Imported metadata remains author-supplied. Require exact agreement with
  // every original record before restoring an explicitly saved meeting selection.
  function meetingIdentity(corpus, p) {
    if (corpus.reviewed_units || corpus.records.some(r => r.parent_id)) return null;
    const c = corpus.collection || {};
    if (c.selection_mode !== 'single_meeting') return null;
    const slug = c.selected_meeting_slug, date = c.selected_meeting_date;
    if (typeof slug !== 'string' || !/^[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+){1,5}$/.test(slug) ||
        !dateOK(date) || date < p.start || date > p.end ||
        (p.meeting_slug && (p.meeting_slug !== slug || p.meeting_date !== date))) return null;
    if (!corpus.records.length || !corpus.records.every(r =>
        (r.meeting_slug || r.id.split('#')[0]) === slug && r.date === date)) return null;
    const rows = corpus.records.filter(r => r.language === 'en' && Scopes.matchesRecord(r, p.scope));
    if (!rows.length || rows.length !== corpus.records.filter(r => r.language === 'en').length) return null;
    return {meeting_slug: slug, meeting_date: date, title: c.selected_meeting_title};
  }

  function themeExcerpt(text, pattern) {
    const normalized = text.replace(/\s+/g, ' ');
    const line = TextUnits.sentences(normalized).find(value => pattern.test(value) && TextUnits.summaryEvidenceSentence(value)) || '';
    const at = line.search(pattern), start = Math.max(0, at - 80);
    return (start ? '…' : '') + line.slice(start, start + 240);
  }

  function briefing(records, matched, duplicates, corpus, p) {
    const words = matched.map(r => TextUnits.wordCount(r.text)).sort((a,b) => a-b);
    const median = words.length ? (words[Math.floor((words.length-1)/2)] + words[Math.floor(words.length/2)]) / 2 : null;
    const sources = matched.filter(r => MeetingQuickReader.safeURL(r.source_url)).map(r => ({record_id:r.id,source_url:MeetingQuickReader.safeURL(r.source_url)}));
    const processed = matched.map(r => TextUnits.reduceProceduralNoise(r.text));
    const thematicRecords = matched.map((r,i) => ({...r,text:processed[i].text}));
    const processing={method:'narrow_procedural_sentences_v4',original_included_count:matched.length,
      removed_sentence_count:processed.reduce((n,r)=>n+r.removed_sentence_count,0),
      zero_text_ids:thematicRecords.filter(r=>!TextUnits.wordCount(r.text)).map(r=>r.id)};
    const themes = MeetingQuickReader.ISSUES.map(issue => {
      const hits = thematicRecords.filter(r => issue.pattern.test(r.text));
      return {id:issue.id,label:issue.label,segments:hits.length,evidence:hits.filter(r => MeetingQuickReader.safeURL(r.source_url) && TextUnits.sentences(r.text).some(line => issue.pattern.test(line) && TextUnits.summaryEvidenceSentence(line))).slice(0,2).map(r => ({record_id:r.id,source_url:MeetingQuickReader.safeURL(r.source_url),excerpt:themeExcerpt(r.text, issue.pattern)}))};
    }).filter(t => t.segments).sort((a,b) => b.segments-a.segments || a.label.localeCompare(b.label)).slice(0,6);
    const warnings = corpus.coverage.filter(row => row.status !== 'ok' && row.status !== 'collected');
    const meetings = new Set(matched.map(r => r.meeting_slug || r.id.split('#')[0])).size;
    const paragraphs = [p.mode === 'topic'
      ? `${matched.length} of ${records.length} eligible, distinct English source segments match the saved topic phrases and exclusions across ${meetings} recorded meetings. These are literal phrase matches, not a judgment of substantive relevance.`
      : `The selected dates, scope and passage filters contain ${matched.length} distinct English source segments across ${meetings} recorded meetings.`,
      matched.length ? `The included text contains ${words.reduce((a,b)=>a+b,0)} words, with a median of ${median} words per source segment. Segments may be fragments or several turns; these figures do not measure complete speeches or unique speakers.` : 'No source segments satisfy the current filters. This does not establish that the issue was absent from the proceedings.',
      themes.length ? `The fixed issue dictionary finds references to ${themes.slice(0,2).map(t=>t.label.toLowerCase()).join(' and ')} most often among its issue families. Counts describe mentions in included segments, not priorities, agreement or decisions.` : 'The fixed issue dictionary identifies no subject family in the included text. Subjects outside that dictionary remain unclassified.',
      `${warnings.length} of ${corpus.coverage.length} saved coverage entries have a status other than successful collection. Coverage refers to the saved collection and may extend beyond the current filters; the available text is not proof of complete proceedings.`];
    return {schema:'un.browser-briefing.v1',method:'offline_deterministic_descriptive_summary',paragraphs,processing,
      stats:{eligible_segments:records.length,matched_segments:matched.length,matched_meetings:meetings,matched_words:words.reduce((a,b)=>a+b,0),median_words_per_segment:median,duplicate_segments:duplicates.length,coverage_entries:corpus.coverage.length,coverage_warnings:warnings.length},
      themes,sources,limitations:['Automatic transcript text and imported metadata are not independently authenticated.','Exact-text duplicates are removed within the current selection; source segments are not unique speeches or speakers.','Theme counts use a fixed dictionary after removing narrow procedural sentences; original segment and word totals remain unchanged. They do not infer country positions, voting outcomes or meeting consensus.','This deterministic summary describes the included source text and does not replace reading the linked passages.'],external_ai_calls:0};
  }

  async function analyze(corpus, p, yieldProgress = async () => {}, runClusters, runNMF) {
    validateCorpus(corpus);
    p = parameters(p);
    if(corpus.reviewed_units||corpus.records.some(r=>r.parent_id)){
      if(!ReviewedUnits?.isValidated(corpus))throw Error('Reviewed passages require a validated analysis bundle with original sources and saved decisions.');
      if(p.passageSelection)throw Error('The original passage-type mask cannot be applied to reviewed speech excerpts.');
    }

    // Apply committee, date, region and language restrictions before deduping.
    // This prevents out-of-scope text from changing denominators or matches.
    const identity = meetingIdentity(corpus, p);
    const wholeMeeting = identity ? corpus.records.filter(r => r.language === 'en' && r.date === identity.meeting_date && (r.meeting_slug || r.id.split('#')[0]) === identity.meeting_slug) : [];
    const selection=PassageSelection.validate(corpus,p.passageSelection);
    const beforeTypes = corpus.records.filter(record => (
      record.date >= p.start &&
      record.date <= p.end &&
      (p.region === 'All regions' || record.region === p.region) &&
      Scopes.matchesRecord(record, p.scope) &&
      (!p.meeting_slug || (record.meeting_slug || record.id.split('#')[0]) === p.meeting_slug) &&
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
          source_url: record.source_url,
          ...(record.parent_id?{parent_id:record.parent_id,start:record.start,end:record.end}: {})
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
    result.briefing = briefing(records, matched, duplicates, corpus, p);
    if(identity){
      result.quick_reader=MeetingQuickReader.build(wholeMeeting,identity);
    }
    if(selection){const {selected,...audit}=selection;result.passage_selection={...audit,eligible_before_type_filter:beforeTypes.length,eligible_after_type_filter:eligible.length,excluded_within_filters:beforeTypes.filter(r=>!selected.has(r.id)).map(r=>r.id)};}
    if(corpus.reviewed_units)result.reviewed_units={...corpus.reviewed_units,
      eligible_before_dedup:ReviewedUnits.count(eligible),eligible:ReviewedUnits.count(records),included:ReviewedUnits.count(matched)};

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
        const count = TextUnits.wordCount(record.text);
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
      const needsLexical = p.methods.some(method => ['tfidf','similarity'].includes(method));
      const terms = needsLexical ? tfidf(matched,{reduceProceduralNoise:true}) : null;
      // Research latent models retain the original representation and inputs.
      const latentTerms = (p.methods.includes('nmf') || p.methods.includes('clusters')) ? tfidf(matched) : null;

      if(p.methods.includes('nmf')&&!result.methods.nmf){
        const runner=runNMF||((records,vectors,settings,progress)=>{
          if(typeof module==='undefined'||!module.exports)throw Error('NMF worker is unavailable. Reload the page.');
          return require('./nmf-core.js').run(records,vectors,settings,progress);
        });
        result.methods.nmf=await runner(matched,latentTerms.vectors,p.nmf,yieldProgress);
      }

      if (p.methods.includes('clusters') && !result.methods.clusters) {
        const runner = runClusters || ((records,vectors,settings,progress) => {
          if (typeof module === 'undefined' || !module.exports) throw Error('Clustering worker is unavailable. Reload the page.');
          return require('./cluster-core.js').run(records,vectors,settings,progress);
        });
        result.methods.clusters = await runner(matched,latentTerms.vectors,p.clustering,yieldProgress);
      }

      if (p.methods.includes('tfidf')) {
        result.methods.tfidf = {
          terms: terms.terms,
          vocabulary: terms.vocabulary,
          processing: terms.processing
        };
      }

      if (p.methods.includes('similarity')) {
        // Examine every nonzero-vector pair but retain only the exact top ten.
        // Pair storage stays bounded as multi-meeting collections grow.
        const pairs = [];
        const compare = (a, b) => b.cosine - a.cosine ||
          a.left.localeCompare(b.left) || a.right.localeCompare(b.right);
        const active = terms.vectors.reduce((n, vector) => n + Number(vector.size > 0), 0);
        const total = active * (active - 1) / 2;
        let compared = 0;
        for (let i = 0; i < terms.vectors.length; i++) {
          for (let j = i + 1; j < terms.vectors.length; j++) {
            if (!terms.vectors[i].size || !terms.vectors[j].size) continue;
            let score = 0;
            for (const [term, weight] of terms.vectors[i]) {
              score += weight * (terms.vectors[j].get(term) || 0);
            }
            const pair = {left: matched[i].id, right: matched[j].id, cosine: Math.min(1, score)};
            if (pairs.length < 10 || compare(pair, pairs[pairs.length - 1]) < 0) {
              pairs.push(pair);
              pairs.sort(compare);
              if (pairs.length > 10) pairs.pop();
            }
            compared++;
            if (compared % 1000 === 0) {
              await yieldProgress(`Comparing text similarity: ${compared} of ${total} pairs`);
            }
          }
          if (i % 25 === 0) await yieldProgress(`Comparing text similarity: ${compared} of ${total} pairs`);
        }
        result.methods.similarity = {
          pairs, compared, processing: terms.processing,
          computation: 'exact_all_pairs_bounded_top_10'
        };
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
