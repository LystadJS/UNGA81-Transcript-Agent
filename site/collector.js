/* Collect only the selected meeting scope from the official UN inventory. */
(function (root) {
  'use strict';

  const Scopes = typeof module !== 'undefined' && module.exports
    ? require('./meeting-scopes.js')
    : root.UNMeetingScopes;

  const BASE = 'https://transcripts.un.org';


  async function sha(text) {
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));

    return [...new Uint8Array(digest)]
      .map(value => value.toString(16).padStart(2, '0'))
      .join('');
  }


  function sourceURL(path) {
    const url = new URL(path, BASE);

    if (url.origin !== BASE || url.username || url.password) {
      throw Error('Unexpected transcript host.');
    }

    return url.href;
  }


  async function readJSON(url, signal) {
    const timer = new AbortController();
    const timeout = setTimeout(() => timer.abort(), 45000);
    const abort = () => timer.abort();

    signal?.addEventListener('abort', abort, { once: true });

    try {
      if (signal?.aborted) throw new DOMException('Cancelled', 'AbortError');

      const response = await fetch(sourceURL(url), {
        signal: timer.signal,
        credentials: 'omit',
        referrerPolicy: 'no-referrer'
      });

      if (!response.ok) throw Error('UN service returned HTTP ' + response.status);

      const reader = response.body.getReader();
      const chunks = [];
      let size = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        size += value.length;

        if (size > 25000000) {
          await reader.cancel();
          throw Error('UN response exceeds the 25 MB request limit.');
        }

        chunks.push(value);
      }

      const raw = await new Blob(chunks).text();

      return { data: JSON.parse(raw), hash: await sha(raw) };
    } finally {
      clearTimeout(timeout);
      signal?.removeEventListener('abort', abort);
    }
  }


  async function collect(p, countries, { signal, progress = () => {}, request = readJSON } = {}) {
    if (!Scopes.isValid(p.scope)) throw Error('Invalid meeting scope.');

    const alias = new Map();

    for (const country of countries) {
      for (const name of [country.country, country.iso3, ...country.aliases.split('|')]) {
        alias.set(name.toLowerCase(), country);
      }
    }

    const meetings = [];
    const coverage = [];
    const days = [];
    const records = [];
    let chars = 0;

    const check = () => {
      if (signal?.aborted) throw new DOMException('Cancelled', 'AbortError');
    };


    // Inventory pagination is checked before deciding which meetings to fetch.
    for (let day = new Date(p.start + 'T00:00:00Z');
         day <= new Date(p.end + 'T00:00:00Z');
         day.setUTCDate(day.getUTCDate() + 1)) {
      check();

      const date = day.toISOString().slice(0, 10);
      const found = [];
      let expected = null;
      let done = false;

      progress('Finding meetings · ' + date);

      try {
        for (let page = 1; page <= 50; page++) {
          check();

          const { data, hash } = await request(
            `${BASE}/en/meetings.json?date=${date}&xlang=1&page=${page}`,
            signal
          );

          if (!Array.isArray(data.meetings) || data.page !== page ||
              !Number.isInteger(data.total) || data.total < 0 ||
              typeof data.hasMore !== 'boolean') {
            throw Error('Unexpected UN inventory format.');
          }

          if (expected === null) expected = data.total;
          if (expected !== data.total) throw Error('Inventory changed during collection.');

          days.push({ date, page, sha256: hash });
          found.push(...data.meetings);

          if (!data.hasMore) {
            done = true;
            break;
          }
        }

        if (!done || found.length !== expected ||
            new Set(found.map(meeting => meeting.slug)).size !== expected ||
            found.some(meeting => meeting.date?.slice(0, 10) !== date)) {
          throw Error('Inventory count, date or pagination mismatch.');
        }

        meetings.push(...found);
      } catch (error) {
        check();
        coverage.push({ date, status: 'inventory_failed', error: error.message });
      }
    }


    // Filter BEFORE downloading transcripts. Selecting Third Committee does
    // not download every other committee and hide its passages afterward.
    const selected = meetings.filter(meeting => Scopes.matchesMeeting(meeting, p.scope));

    if (selected.length > 300) {
      throw Error('More than 300 meetings selected. Narrow the dates or meeting scope.');
    }

    for (const [index, meeting] of selected.entries()) {
      check();
      progress(`Collecting meeting ${index + 1} of ${selected.length} · ${meeting.title}`);

      const scope = Scopes.classifyMeeting(meeting);

      const row = {
        date: meeting.date.slice(0, 10),
        title: meeting.title,
        slug: meeting.slug,
        scope,
        source_url: sourceURL(meeting.pageUrl),
        status: 'unavailable'
      };

      coverage.push(row);
      if (!meeting.hasTranscript) continue;

      try {
        const { data, hash } = await request(sourceURL(meeting.jsonUrl), signal);
        check();

        if (data.video?.slug !== meeting.slug ||
            data.video.date?.slice(0, 10) !== row.date ||
            !Array.isArray(data.transcript?.data)) {
          throw Error('Transcript identity or date mismatch.');
        }

        row.raw_sha256 = hash;
        row.language = data.transcript.language;
        row.timestamps_flagged = !!data.transcript.timestamps_flagged;

        if (row.language !== 'en') {
          row.status = 'excluded_language';
          continue;
        }

        const batch = [];

        for (const [segmentIndex, segment] of data.transcript.data.entries()) {
          check();

          const text = (segment.paragraphs || [])
            .flatMap(paragraph => paragraph.sentences || [])
            .map(sentence => sentence.text)
            .join(' ');

          if (!text.trim()) continue;

          const speaker = segment.speaker || {};
          const affiliation = speaker.affiliation || speaker.affiliation_full || '';
          const country = alias.get(affiliation.toLowerCase()) ||
            alias.get((speaker.affiliation_full || '').toLowerCase());

          batch.push({
            id: meeting.slug + '#' + segmentIndex,
            date: row.date,
            country: country?.country || affiliation || 'Unidentified',
            region: country?.region || 'Unmapped',
            language: row.language,
            scope,
            meeting: meeting.title,
            text,
            source_url: sourceURL(segment.pageUrl || meeting.pageUrl),
            text_sha256: await sha(text),
            raw_sha256: hash,
            json_pointer: '/transcript/data/' + segmentIndex,
            timestamps_flagged: row.timestamps_flagged
          });
        }

        const added = batch.reduce((sum, record) => sum + record.text.length, 0);

        if (records.length + batch.length > 15000 || chars + added > 20000000) {
          throw Error('Collection size limit exceeded; narrow the dates.');
        }

        chars += added;
        records.push(...batch);
        row.status = 'collected';
        row.segments = batch.length;
      } catch (error) {
        check();
        row.status = 'failed';
        row.error = error.message;
      }
    }


    return {
      schema: 'un.browser.corpus.v1',
      origin: BASE,
      collection: {
        start: p.start,
        end: p.end,
        scope: p.scope,
        collected_at: new Date().toISOString(),
        inventory_meetings: meetings.length,
        selected_meetings: selected.length,
        inventory_pages: days,
        unit: 'Original UN transcript source segment; may include procedural and non-national interventions',
        english_only: true
      },
      coverage,
      records
    };
  }


  const api = { collect, sha, sourceURL, readJSON };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.UNCollector = api;
  }

})(typeof globalThis !== 'undefined' ? globalThis : this);
