/* Shared validation for the local, source-bound review packet. No networking. */
(function (root) {
  'use strict';
  const VERSION = 'boundary-review-1.0.0';
  const TYPES = ['substantive_speech', 'mixed_speech_procedure', 'right_of_reply',
    'procedure', 'speech_fragment', 'suspected_transcription_issue', 'uncertain'];
  const EXTENTS = ['complete', 'near_complete', 'fragment', 'unknown'];
  const assert = (ok, message) => { if (!ok) throw Error(message); };
  const stable = x => Array.isArray(x) ? '[' + x.map(stable).join(',') + ']' :
    x && typeof x === 'object' ? '{' + Object.keys(x).sort().filter(k => x[k] !== undefined)
      .map(k => JSON.stringify(k) + ':' + stable(x[k])).join(',') + '}' : JSON.stringify(x);
  const clone = x => JSON.parse(JSON.stringify(x));
  const digestOK = x => typeof x === 'string' && /^[a-f0-9]{64}$/.test(x);
  const unsigned = x => Object.fromEntries(Object.entries(x).filter(([k]) => k !== 'sha256'));
  async function sha(text) {
    const bytes = new TextEncoder().encode(text);
    return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
      n => n.toString(16).padStart(2, '0')).join('');
  }
  function pending(row) {
    return {id: row.id, text_sha256: row.text_sha256, confirmed: false, type: null,
      extent: 'unknown', speech_id: null, reviewer: '', reviewed_at: '', note: ''};
  }
  function seed(packet) {
    return {schema: 'un.corpus-boundary-review.v1', source_bundle_sha256: packet.source_bundle_sha256,
      packet_sha256: packet.sha256,
      scope: 'Development only. Whole original source-segment boundaries; no transcript corrections or automatic speech inference.',
      choices: packet.records.map(r => ({...pending(r), ...(r.initial_choice || {})}))};
  }
  function validateReview(packet, review) {
    assert(review && review.schema === 'un.corpus-boundary-review.v1', 'Choose a boundary-review JSON file.');
    assert(review.source_bundle_sha256 === packet.source_bundle_sha256, 'Review belongs to a different source bundle.');
    assert(!review.packet_sha256 || review.packet_sha256 === packet.sha256, 'Review belongs to a different packet version.');
    assert(Array.isArray(review.choices) && review.choices.length <= packet.records.length, 'Invalid number of review choices.');
    const rows = new Map(packet.records.map(r => [r.id, r]));
    const choices = new Map(seed(packet).choices.map(c => [c.id, c]));
    const seen = new Set();
    const fields = ['id', 'text_sha256', 'confirmed', 'type', 'extent', 'speech_id', 'reviewer', 'reviewed_at', 'note'];
    for (const input of review.choices) {
      assert(input && typeof input === 'object' && Object.keys(input).every(k => fields.includes(k)), 'Unknown review field.');
      const r = rows.get(input.id);
      assert(r && !seen.has(r.id), 'Unknown, held-out or duplicate source ID.');
      seen.add(r.id);
      assert(input.text_sha256 === r.text_sha256, 'Source text hash mismatch: ' + r.id);
      const c = {...pending(r), ...input};
      assert(typeof c.confirmed === 'boolean', 'Confirmation must be true or false.');
      assert(c.type === null || TYPES.includes(c.type), 'Unknown source type.');
      assert(EXTENTS.includes(c.extent), 'Unknown speech extent.');
      assert(c.speech_id === null || (typeof c.speech_id === 'string' && c.speech_id.length <= 240), 'Invalid speech ID.');
      assert(typeof c.reviewer === 'string' && c.reviewer.length <= 120, 'Reviewer name is too long.');
      assert(typeof c.note === 'string' && c.note.length <= 10000, 'Notes must be text of at most 10,000 characters.');
      assert(typeof c.reviewed_at === 'string', 'Invalid review timestamp.');
      if (c.confirmed) {
        assert(TYPES.includes(c.type) && c.reviewer.trim(), 'Choose a type and enter your reviewer name before confirming.');
        const time = Date.parse(c.reviewed_at);
        assert(/(Z|[+-]\d\d:\d\d)$/.test(c.reviewed_at) && Number.isFinite(time) && time <= Date.now() + 300000,
          'A confirmed choice needs a valid, non-future timestamp with timezone.');
        if (['complete', 'near_complete'].includes(c.extent))
          assert(c.speech_id && c.speech_id.trim(), 'Complete or near-complete speech coverage needs an explicit speech ID.');
        if (c.extent === 'near_complete') assert(c.note.trim(), 'Explain the missing part of a near-complete speech.');
      }
      choices.set(r.id, c);
    }
    // Match the existing corpus contract: a shared speech ID cannot cross source identities.
    const speeches = new Map();
    for (const c of choices.values()) {
      if (!c.confirmed || !c.speech_id) continue;
      const r = rows.get(c.id);
      const signature = stable([r.meeting_id, r.country, r.affiliation_raw, r.speaker_metadata]);
      assert(!speeches.has(c.speech_id) || speeches.get(c.speech_id) === signature,
        'Shared speech ID crosses meetings or conflicts with recorded speaker/affiliation metadata.');
      speeches.set(c.speech_id, signature);
    }
    return {...seed(packet), choices: packet.records.map(r => choices.get(r.id))};
  }
  async function validatePacket(packet) {
    assert(packet && packet.schema === 'un.boundary-packet.v1' && packet.engine === VERSION, 'Unsupported review packet.');
    assert(digestOK(packet.sha256) && await sha(stable(unsigned(packet))) === packet.sha256, 'Packet content digest mismatch.');
    assert(digestOK(packet.source_bundle_sha256) && digestOK(packet.corpus_sha256) && digestOK(packet.frame_sha256), 'Missing source lineage.');
    assert(packet.holdout.transcripts_opened === 0 && packet.holdout.state === 'reserved_not_downloaded', 'Holdout is not sealed.');
    const meetings = new Map();
    for (const m of packet.meetings) {
      assert(!meetings.has(m.meeting_id) && m.split === 'development' && packet.development_dates.includes(m.date), 'Invalid development meeting.');
      assert(m.source_url === 'https://transcripts.un.org/en/' + m.meeting_id, 'Unsafe source link.');
      const u = new URL(m.source_url);
      assert(u.origin === 'https://transcripts.un.org' && !u.search && !u.hash && !u.username && !u.password &&
        !m.meeting_id.split('/').some(s => !/^[A-Za-z0-9_-]+$/.test(s)), 'Unsafe meeting path.');
      assert(m.raw_file === null || /^sources\/m\d{3}\.json$/.test(m.raw_file), 'Unsafe local source path.');
      meetings.set(m.meeting_id, m);
    }
    const ids = new Set();
    for (const r of packet.records) {
      const m = meetings.get(r.meeting_id);
      assert(m && r.split === 'development' && !ids.has(r.id) && r.date === m.date, 'Unknown or repeated development record.');
      ids.add(r.id);
      assert(r.source_url === m.source_url && r.raw_sha256 === m.raw_sha256, 'Record source lineage mismatch.');
      assert(r.json_pointer === '/transcript/data/' + r.source_index && r.id === r.meeting_id + '#' + r.source_index, 'Invalid source pointer.');
      assert(await sha(r.text) === r.text_sha256, 'Original text digest mismatch.');
      const chars = Array.from(r.text); let end = 0;
      for (const p of r.partitions) {
        assert(p.parent_start === end && Number.isSafeInteger(p.parent_end) && p.parent_end > end && p.parent_end <= chars.length,
          'Partition bounds are incomplete, overlapping or invalid.');
        assert(await sha(chars.slice(end, p.parent_end).join('')) === p.text_sha256, 'Partition text digest mismatch.');
        end = p.parent_end;
      }
      assert(end === chars.length, 'Source text is not completely accounted for.');
    }
    assert(packet.records.length === packet.counts.source_segments && packet.meetings.length === packet.counts.meetings,
      'Packet count mismatch.');
    validateReview(packet, seed(packet));
    return packet;
  }
  const api = {VERSION, TYPES, EXTENTS, stable, clone, sha, pending, seed, validateReview, validatePacket};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.UNBoundaryReview = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
