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

      const bytes=new Uint8Array(size);let offset=0;
      for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
      // Preserve a UTF-8 BOM in the hashed archive; reject malformed bytes rather
      // than silently replacing them and claiming an exact response-byte hash.
      const raw = new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);

      return { data: JSON.parse(raw.replace(/^\uFEFF/,'')), hash: await sha(raw), raw, retrieved_at:new Date().toISOString(), etag:response.headers.get('etag'), last_modified:response.headers.get('last-modified') };
    } finally {
      clearTimeout(timeout);
      signal?.removeEventListener('abort', abort);
    }
  }


  async function collect(p, countries, { signal, progress = () => {}, request = readJSON, resume = null, refresh = false, checkpoint = () => {} } = {}) {
    if (!Scopes.isValid(p.scope)) throw Error('Invalid meeting scope.');
    if (p.meeting_slug !== undefined && (typeof p.meeting_slug !== 'string' || !/^[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+){1,5}$/.test(p.meeting_slug) || p.start !== p.end || p.meeting_date !== p.start || !/^\d{4}-\d{2}-\d{2}$/.test(p.start) || !Number.isFinite(Date.parse(p.start)) || new Date(p.start).toISOString().slice(0,10)!==p.start)) throw Error('Select one meeting on one valid date.');
    if (resume && (resume.schema !== 'un.browser.corpus.v1' || resume.collection?.start !== p.start || resume.collection?.end !== p.end || resume.collection?.scope !== p.scope || (resume.collection.selected_meeting_slug || '') !== (p.meeting_slug || ''))) throw Error('Retry requires the original collection dates and meeting selection.');
    if (resume?.provenance) await verifyProvenance(resume);
    if (refresh && !resume) throw Error('Checking for new transcripts requires a saved collection.');
    const matchesSelection = meeting => Scopes.matchesMeeting(meeting, p.scope) && (!p.meeting_slug || meeting.slug === p.meeting_slug);

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
    const inventoryDays = [];
    let chars = 0;
    const startedAt = new Date().toISOString();
    const sources = new Map((resume?.provenance?.sources || []).map(source => [source.source_id+'|'+source.sha256, {...source}]));
    let rawBytes = [...sources.values()].reduce((n,s)=>n+new TextEncoder().encode(s.raw || '').length,0);
    function retainSource(source_id, response, kind) {
      const source_version='sha256:'+response.hash, key=source_id+'|'+response.hash;
      const metadata={source_id,source_url:source_id,kind,sha256:response.hash,source_version,retrieved_at:response.retrieved_at || new Date().toISOString(),etag:response.etag || null,last_modified:response.last_modified || null};
      if (!sources.has(key)) {
        if(typeof response.raw==='string'){const bytes=new TextEncoder().encode(response.raw).length;if(rawBytes+bytes>25000000)throw Error('Saved raw-source archive exceeds the 25 MB collection limit; narrow the dates.');metadata.raw=response.raw;}
        const serialized=new TextEncoder().encode(JSON.stringify({sources:[...sources.values(),metadata],records,meetings,coverage,days,inventoryDays})).length;
        if(serialized>24000000)throw Error('Saved collection exceeds the 25 MB reproducible archive limit; narrow the dates.');
        sources.set(key,metadata);
        rawBytes+=new TextEncoder().encode(metadata.raw || '').length;
      }
      return metadata;
    }

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

          const inventoryURL=`${BASE}/en/meetings.json?date=${date}&xlang=1&page=${page}`;
          const response=await request(inventoryURL,signal);
          const { data, hash }=response;

          if (!Array.isArray(data.meetings) || data.page !== page ||
              !Number.isInteger(data.total) || data.total < 0 ||
              typeof data.hasMore !== 'boolean') {
            throw Error('Unexpected UN inventory format.');
          }

          if (expected === null) expected = data.total;
          if (expected !== data.total) throw Error('Inventory changed during collection.');

          const provenance=retainSource(inventoryURL,response,'inventory');
          days.push({ date, page, sha256: hash, source_url:inventoryURL, source_version:provenance.source_version, retrieved_at:provenance.retrieved_at });
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

        inventoryDays.push({
          date,
          status: 'ok',
          meetings: found.length,
          selected: found.filter(matchesSelection).length
        });
      } catch (error) {
        check();
        const failure = { date, status: 'inventory_failed', error: error.message };
        coverage.push(failure);
        inventoryDays.push(failure);
      }
    }


    // Filter BEFORE downloading transcripts. Selecting Third Committee does
    // not download every other committee and hide its passages afterward.
    const originalSlugs = resume?.collection?.selected_meeting_slugs;
    const failedDays = new Set((resume?.collection?.inventory_days || []).filter(day => day.status !== 'ok').map(day => day.date));
    const selected = meetings.filter(meeting => matchesSelection(meeting) && (refresh || !Array.isArray(originalSlugs) || originalSlugs.includes(meeting.slug) || failedDays.has(meeting.date.slice(0, 10))));
    const selectedSlugs = [...new Set([...(Array.isArray(originalSlugs) ? originalSlugs : []), ...selected.map(meeting => meeting.slug)])];
    // Keep completed responses from the original run; retry only missing responses.
    // Fresh inventory is still verified and selection is applied before any download.
    const completed = new Map((resume?.coverage || [])
      .filter(row => ['collected', 'excluded_language', ...(!refresh ? ['empty_transcript'] : [])].includes(row.status))
      .map(row => [row.slug, row]));
    for (const row of completed.values()) coverage.push({...row,transcript_status:row.transcript_status || 'available'});
    // Preserve unresolved entries when a fresh inventory cannot be obtained.
    for(const row of resume?.coverage || [])if(row.slug && !completed.has(row.slug) && !selected.some(m=>m.slug===row.slug))coverage.push({...row,inventory_current:false});
    records.push(...(resume?.records || []).filter(record => completed.has(record.meeting_slug)).map(record=>({...record})));
    // Older exports retain text/raw hashes but did not name their JSON endpoint.
    for(const record of records)if(!record.source_id){
      const meeting=meetings.find(m=>m.slug===record.meeting_slug);
      const endpoint=meeting?.jsonUrl;
      if(endpoint&&/^[a-f0-9]{64}$/.test(record.raw_sha256)){
        record.source_id=sourceURL(endpoint);record.source_version='sha256:'+record.raw_sha256;
        const key=record.source_id+'|'+record.raw_sha256;
        if(!sources.has(key))sources.set(key,{source_id:record.source_id,source_url:record.source_id,kind:'transcript',sha256:record.raw_sha256,source_version:record.source_version,retrieved_at:resume.collection.collected_at,legacy_hash_only:true});
      }else record.legacy_provenance_unavailable=true;
    }
    chars = records.reduce((sum, record) => sum + record.text.length, 0);
    if(p.meeting_slug && (inventoryDays.some(d=>d.status!=='ok') || selected.length!==1)) throw Error('The selected meeting could not be verified in the complete inventory. Search the date again; no other meeting was substituted.');

    progress(`Inventory checked: ${meetings.length} meetings; ${selected.length} within the selected scope.`);

    if (selected.length > 300) {
      throw Error('More than 300 meetings selected. Narrow the dates or meeting scope.');
    }

    for (const [index, meeting] of selected.entries()) {
      check();
      if (completed.has(meeting.slug)) {
        const previous = completed.get(meeting.slug);
        if (previous.date !== meeting.date.slice(0, 10)) throw Error('Saved meeting date does not match the inventory.');
        checkpoint(snapshot());
        continue;
      }
      progress(`Collecting meeting ${index + 1} of ${selected.length} · ${meeting.title}`);

      const scope = Scopes.classifyMeeting(meeting);

      const row = {
        date: meeting.date.slice(0, 10),
        title: meeting.title,
        slug: meeting.slug,
        scope,
        source_url: sourceURL(meeting.pageUrl),
        status: 'unavailable',
        transcript_status: /^(pending|processing|queued|preparing)$/i.test(String(meeting.transcriptStatus || meeting.transcript_status || '')) ? 'pending' : 'unavailable',
        inventory_has_transcript:meeting.hasTranscript === true,
        inventory_source_status:meeting.transcriptStatus || meeting.transcript_status || null
      };

      coverage.push(row);
      if (!meeting.hasTranscript) { checkpoint(snapshot()); continue; }

      try {
        const transcriptURL=sourceURL(meeting.jsonUrl);
        const response=await request(transcriptURL, signal);
        const { data, hash }=response;
        check();

        if (data.video?.slug !== meeting.slug ||
            data.video.date?.slice(0, 10) !== row.date) {
          throw Error('Transcript identity or date mismatch.');
        }

        const provenance=retainSource(transcriptURL,response,'transcript');
        Object.assign(row,{source_id:transcriptURL,source_json_url:transcriptURL,source_version:provenance.source_version,retrieved_at:provenance.retrieved_at,raw_sha256:hash,etag:provenance.etag,last_modified:provenance.last_modified});
        if (!data.transcript || !Array.isArray(data.transcript.data)) {
          row.status = 'unavailable';
          row.transcript_status = 'pending';
          row.error = 'Meeting found, but the requested transcript is not ready or has no segment data.';
          continue;
        }

        row.raw_sha256 = hash;
        row.language = data.transcript.language;
        row.timestamps_flagged = !!data.transcript.timestamps_flagged;

        row.transcript_status='available';
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
            meeting_slug: meeting.slug,
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
            source_id:transcriptURL,
            source_version:provenance.source_version,
            json_pointer: '/transcript/data/' + segmentIndex,
            timestamps_flagged: row.timestamps_flagged,
            // Original source labels are retained without inventing personal identity.
            speaker_metadata: {
              affiliation: typeof speaker.affiliation === 'string' ? speaker.affiliation.slice(0, 240) : null,
              affiliation_full: typeof speaker.affiliation_full === 'string' ? speaker.affiliation_full.slice(0, 240) : null,
              function: typeof speaker.function === 'string' ? speaker.function.slice(0, 240) : null,
              group: typeof speaker.group === 'string' ? speaker.group.slice(0, 240) : null,
              ...(typeof speaker.name === 'string' ? {name:speaker.name.slice(0, 240)} : {}),
              ...(typeof speaker.id === 'string' ? {id:speaker.id.slice(0, 240)} : {})
            },
            attribution: {country_status:country?.country?'registry_mapped':'unresolved',basis:country?.country?'source_affiliation_country_registry':'none'}
          });
        }

        const added = batch.reduce((sum, record) => sum + record.text.length, 0);

        if (records.length + batch.length > 15000 || chars + added > 20000000) {
          throw Error('Collection size limit exceeded; narrow the dates.');
        }

        if(new TextEncoder().encode(JSON.stringify({sources:[...sources.values()],records:[...records,...batch],meetings,coverage,days,inventoryDays})).length>24000000)throw Error('Saved collection exceeds the 25 MB reproducible archive limit; narrow the dates.');
        chars += added;
        records.push(...batch);
        row.status = batch.length ? 'collected' : 'empty_transcript';
        row.transcript_status = batch.length ? 'available' : 'unavailable';
        row.segments = batch.length;
        if (!batch.length) row.error = 'Transcript response contains no usable text.';
      } catch (error) {
        check();
        row.status = 'failed';
        row.transcript_status = 'failed';
        row.error = error.message;
      } finally {
        // Exportable checkpoints contain only complete responses, never an unfinished batch.
        checkpoint(snapshot());
      }
    }


    return snapshot();

    function snapshot() { return {
      schema: 'un.browser.corpus.v1',
      origin: BASE,
      collection: {
        start: p.start,
        end: p.end,
        scope: p.scope,
        collected_at: new Date().toISOString(),
        first_collected_at:resume?.collection?.first_collected_at || resume?.collection?.collected_at || startedAt,
        checked_at:startedAt,
        operation:refresh?'refresh':resume?'retry':'collect',
        partial:coverage.some(row=>row.status==='failed'||row.status==='inventory_failed') || inventoryDays.some(day=>day.status!=='ok'),
        transcript_status_counts:Object.fromEntries(['available','pending','unavailable','failed'].map(status=>[status,coverage.filter(row=>row.slug&&row.transcript_status===status).length])),
        inventory_meetings_snapshot:meetings.map(m=>({slug:m.slug,date:m.date,title:m.title,pageUrl:m.pageUrl,jsonUrl:m.jsonUrl || null,hasTranscript:m.hasTranscript,transcript_status:m.transcriptStatus || m.transcript_status || null})),
        inventory_meetings: meetings.length,
        selected_meetings: selectedSlugs.length,
        ...(p.scope === 'ga_sc_formal' ? {formal_meetings:new Set([...selected, ...coverage].map(Scopes.formalMeetingKey).filter(Boolean)).size,meeting_groups:[...new Set([...selected, ...coverage].map(Scopes.formalMeetingKey).filter(Boolean))].map(key=>({meeting:key,source_slugs:selectedSlugs.filter(slug=>Scopes.formalMeetingKey({slug})===key)}))} : {}),
        selected_meeting_slugs: selectedSlugs,
        ...(p.meeting_slug?{selection_mode:'single_meeting',selected_meeting_slug:p.meeting_slug,selected_meeting_title:selected[0].title,selected_meeting_date:p.meeting_date}:{}),
        inventory_pages: days.map(row => ({...row})),
        inventory_days: inventoryDays.map(row => ({...row})),
        failed_inventory_days: inventoryDays.filter(day => day.status !== 'ok').length,
        collected_meetings: coverage.filter(row => row.status === 'collected').length,
        collected_passages: records.length,
        unit: 'Original UN transcript source segment; may include procedural and non-national interventions',
        english_only: true
      },
      provenance:{schema:'un.browser.source-provenance.v1',hash_algorithm:'SHA-256',version_basis:'Exact response-byte hash; not a source-supplied publication revision.',sources:[...sources.values()].map(source=>({...source}))},
      coverage: coverage.map(row => ({...row})),
      records: records.slice()
    }; }
  }


  async function verifyProvenance(corpus) {
    const manifest=corpus.provenance;
    const sources=new Map(), parsedSources=new Map();
    if(manifest){
      if(manifest.schema!=='un.browser.source-provenance.v1'||!Array.isArray(manifest.sources))throw Error('Unsupported source provenance.');
      for(const source of manifest.sources){
        if(sourceURL(source.source_id)!==source.source_id||!/^[a-f0-9]{64}$/.test(source.sha256)||source.source_version!=='sha256:'+source.sha256)throw Error('Invalid source identity or version.');
        const key=source.source_id+'|'+source.sha256;if(sources.has(key))throw Error('Duplicate source version.');sources.set(key,source);
        if(typeof source.raw==='string'&&await sha(source.raw)!==source.sha256)throw Error('Saved raw source hash mismatch.');
      }
    }
    for(const record of corpus.records || []){
      if((manifest&&!record.text_sha256)||(record.text_sha256 && await sha(record.text)!==record.text_sha256))throw Error('Saved transcript text hash mismatch.');
      if(!manifest || record.legacy_provenance_unavailable)continue;
      const source=sources.get(record.source_id+'|'+record.raw_sha256);
      if(!source||source.kind!=='transcript'||record.source_version!==source.source_version)throw Error('Saved record is not bound to a source version.');
      if(typeof source.raw==='string'){
        let parsed=parsedSources.get(source.source_id+'|'+source.sha256);
        if(!parsed){try{parsed=JSON.parse(source.raw.replace(/^\uFEFF/,''));}catch{throw Error('Saved raw source is not valid JSON.');}parsedSources.set(source.source_id+'|'+source.sha256,parsed);}
        const index=Number(String(record.json_pointer).match(/^\/transcript\/data\/(\d+)$/)?.[1]);
        const segment=parsed.transcript?.data?.[index];
        const text=(segment?.paragraphs || []).flatMap(p=>p.sentences || []).map(s=>s.text).join(' ');
        if(!segment||parsed.video?.slug!==record.meeting_slug||record.text!==text)throw Error('Saved record does not match its raw source passage.');
      }
    }
    return {status:'verified',provenance:manifest&&!(corpus.records || []).some(r=>r.legacy_provenance_unavailable)?'source_bound':'legacy_text_hashes_only',raw_sources_verified:[...sources.values()].filter(s=>typeof s.raw==='string').length};
  }
  const api = { collect, sha, sourceURL, readJSON, verifyProvenance };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.UNCollector = api;
  }

})(typeof globalThis !== 'undefined' ? globalThis : this);
