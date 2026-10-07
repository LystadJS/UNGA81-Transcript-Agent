/* Local-only reviewer interface. Text is rendered with textContent, never HTML. */
(async function () {
  'use strict';
  const B = globalThis.UNBoundaryReview, $ = id => document.getElementById(id);
  const message = (text, error = false) => { $('message').textContent = text; $('message').classList.toggle('error', error); };
  try {
    const p = JSON.parse($('packet-data').textContent);
    await B.validatePacket(p);
    const key = 'un-boundary-review:' + p.sha256;
    const meetingRows = new Map(p.meetings.map(m => [m.meeting_id, p.records.filter(r => r.meeting_id === m.meeting_id)]));
    let review = B.seed(p), current = p.records[0]?.id || null, changed = false, lastExport = null;
    const choice = id => review.choices.find(c => c.id === id);
    const row = () => p.records.find(r => r.id === current);
    const counts = () => ({confirmed: review.choices.filter(c => c.confirmed).length, total: review.choices.length});
    try {
      const cached = localStorage.getItem(key);
      if (cached) { review = B.validateReview(p, JSON.parse(cached)); message('Restored this packet’s browser copy. Save a JSON file for a durable backup.'); }
    } catch (e) { message('Browser copy was not restored: ' + e.message + ' Use Resume saved JSON.', true); }
    function cache() {
      changed = true;
      try { localStorage.setItem(key, JSON.stringify(review)); $('cache-status').textContent = 'Browser copy updated · export JSON before closing'; }
      catch (_) { $('cache-status').textContent = 'Browser storage unavailable · use Save review JSON'; }
    }
    function progress() {
      const c = counts();
      $('progress-label').textContent = c.confirmed.toLocaleString() + ' / ' + c.total.toLocaleString() + ' reviews confirmed';
      $('progress').value = c.total ? 100 * c.confirmed / c.total : 0;
      $('footer-counts').textContent = p.counts.meetings + ' development meetings · ' + p.counts.source_segments.toLocaleString() +
        ' source segments · ' + p.counts.passages.toLocaleString() + ' technical windows';
    }
    function visible(r) {
      const c = choice(r.id), filter = $('filter').value;
      return filter === 'all' || filter === 'pending' && !c.confirmed || filter === 'confirmed' && c.confirmed ||
        filter === 'flagged' && c.confirmed && ['uncertain', 'suspected_transcription_issue', 'speech_fragment'].includes(c.type) ||
        filter === 'unknown-country' && !r.country;
    }
    function queue() {
      const id = $('meeting').value, rows = meetingRows.get(id) || [], m = p.meetings.find(m => m.meeting_id === id);
      const seen = rows.filter(visible), confirmed = rows.filter(r => choice(r.id).confirmed).length;
      $('meeting-status').textContent = m ? m.date + ' · ' + m.genre + ' · ' + m.status.replace(/_/g, ' ') +
        '\n' + confirmed + ' / ' + rows.length + ' reviews confirmed' : '';
      $('segment').replaceChildren();
      for (const r of seen) {
        const c = choice(r.id), o = document.createElement('option');
        o.value = r.id; o.textContent = (c.confirmed ? '✓ ' : '○ ') + (r.source_index + 1) + ' · ' + (r.affiliation_raw || r.speaker_metadata.function || 'Unidentified');
        $('segment').append(o);
      }
      if (!seen.some(r => r.id === current)) current = seen[0]?.id || null;
      $('segment').value = current || '';
      $('queue-count').textContent = seen.length + ' shown of ' + rows.length + ' source segments. All remain in the packet.';
    }
    function element(tag, text, className) {
      const e = document.createElement(tag); e.textContent = text;
      if (className) e.className = className;
      return e;
    }
    function fields(c) {
      $('type').value = c.type || ''; $('extent').value = c.extent; $('speech').value = c.speech_id || ''; $('note').value = c.note || '';
      for (const id of ['type', 'extent', 'speech', 'note', 'use-id', 'confirm']) $(id).disabled = c.confirmed;
      $('reopen').disabled = !c.confirmed;
      $('decision-status').textContent = c.confirmed ? 'Confirmed' : 'Pending / draft';
      $('decision-history').textContent = c.confirmed ? 'Recorded by ' + c.reviewer + ' at ' + c.reviewed_at + '. Reopen before changing this decision.' :
        'Draft only. No human confirmation has been recorded for this segment.';
    }
    function render() {
      queue(); progress();
      const r = row(), m = p.meetings.find(m => m.meeting_id === $('meeting').value);
      $('record-view').hidden = !r; $('empty-state').hidden = !!r;
      if (!r) {
        $('empty-message').textContent = m?.status !== 'collected' ? 'This meeting has no collected source segment. Its missing-source status remains in the coverage record; no review task is invented.' : 'No segments match the current display filter. Select All source segments to see the full meeting.';
        return;
      }
      const c = choice(r.id), rows = meetingRows.get(r.meeting_id), index = rows.findIndex(x => x.id === r.id);
      $('position').textContent = r.date + ' / source segment ' + (index + 1) + ' of ' + rows.length;
      $('record-title').textContent = m.title;
      const who = r.affiliation_raw || 'Affiliation not recorded';
      $('metadata').textContent = who + ' · Country: ' + (r.country || 'unresolved') + ' · Language: ' + r.language +
        (r.speaker_metadata.function ? ' · ' + r.speaker_metadata.function : '');
      $('source-link').href = r.source_url;
      $('raw-link').href = m.raw_file || ''; $('raw-link').hidden = !m.raw_file;
      const warnings = [];
      if (r.timestamps_flagged) warnings.push('The source flags its timestamps as unreliable. No audio-boundary accuracy is asserted.');
      if (!r.country) warnings.push('Country attribution is unresolved. It is not editable in this boundary review.');
      if (!r.partitions.some(w => !w.exclusions.length)) warnings.push('No current technical window meets the audit eligibility policy. Keep this source in the review record.');
      $('source-warning').textContent = warnings.join(' '); $('source-warning').hidden = !warnings.length;
      $('source-text').textContent = r.text || '[Empty original source segment]'; $('source-text').scrollTop = 0;
      $('previous-context').textContent = index > 0 ? rows[index - 1].text || '[Empty source segment]' : '[Start of the collected meeting transcript; no previous segment.]';
      $('next-context').textContent = index + 1 < rows.length ? rows[index + 1].text || '[Empty source segment]' : '[End of the collected meeting transcript; no next segment.]';
      $('partition-summary').textContent = r.partitions.length + ' technical passage window' + (r.partitions.length === 1 ? '' : 's');
      $('partition-list').replaceChildren();
      const chars = Array.from(r.text);
      r.partitions.forEach((w, i) => {
        const e = document.createElement('div'); e.className = 'window';
        e.append(element('p', 'Window ' + (i + 1) + ' · [' + w.parent_start + ', ' + w.parent_end + ') · ' + w.tokens +
          ' tokens · ' + (w.exclusions.length ? 'Audit exclusion: ' + w.exclusions.join(', ') : 'Audit-eligible before review'), 'small'));
        e.append(element('div', chars.slice(w.parent_start, w.parent_end).join(''), 'source-text'));
        $('partition-list').append(e);
      });
      $('lineage').textContent = 'Source ID: ' + r.id + '\nRaw response SHA-256: ' + r.raw_sha256 +
        '\nOriginal text SHA-256: ' + r.text_sha256 + '\nJSON pointer: ' + r.json_pointer + '\nOffset unit: ' + p.offset_unit +
        '\nRecorded speaker metadata:\n' + JSON.stringify(r.speaker_metadata, null, 2);
      $('sentences').replaceChildren();
      for (const s of r.sentences) {
        const d = document.createElement('details');
        d.append(element('summary', '[' + s.start + ', ' + s.end + ') ' + s.json_pointer));
        d.append(element('p', chars.slice(s.start, s.end).join(''), 'source-text'));
        $('sentences').append(d);
      }
      fields(c);
      const listed = Array.from($('segment').options).map(o => o.value), pos = listed.indexOf(current);
      $('previous').disabled = pos <= 0; $('next').disabled = pos >= listed.length - 1;
    }
    function draft() {
      const r = row(); if (!r || choice(r.id).confirmed) return;
      const c = choice(r.id);
      Object.assign(c, {type: $('type').value || null, extent: $('extent').value, speech_id: $('speech').value.trim() || null,
        reviewer: $('reviewer').value.trim(), reviewed_at: '', note: $('note').value});
      cache();
    }
    function selectRecord(id) {
      const r = p.records.find(r => r.id === id); if (!r) return;
      current = id; $('meeting').value = r.meeting_id; render();
    }
    function nextPending() {
      const index = p.records.findIndex(r => r.id === current);
      for (let i = 1; i <= p.records.length; i++) {
        const r = p.records[(index + i) % p.records.length];
        if (!choice(r.id).confirmed) { $('filter').value = 'all'; selectRecord(r.id); return; }
      }
      message('All source-segment decisions are confirmed. Save the review JSON. Uncertain decisions remain explicit, not resolved speeches.'); render();
    }
    for (const m of p.meetings) {
      const option = document.createElement('option'); option.value = m.meeting_id;
      option.textContent = m.date + ' · ' + m.title + (m.status !== 'collected' ? ' [no collected text]' : '');
      $('meeting').append(option);
    }
    $('meeting').value = p.records[0]?.meeting_id || p.meetings[0]?.meeting_id || '';
    $('scope-summary').textContent = 'Development corpus · ' + p.development_dates[0] + ' through ' + p.development_dates.at(-1) + '. Review source segments in context before treating them as complete speeches.';
    $('holdout').textContent = p.holdout.meetings + ' held-out meetings remain unopened · no held-out text or source links in this packet';
    $('provenance').textContent = 'Packet SHA-256:\n' + p.sha256 + '\n\nCorpus:\n' + p.corpus_sha256 +
      '\n\nSource bundle:\n' + p.source_bundle_sha256 + '\n\nAll links were checked against frozen development identities and cached bytes. No live-source request was made.';
    const priorReviewer = [...review.choices].reverse().find(c => c.reviewer)?.reviewer;
    if (priorReviewer) $('reviewer').value = priorReviewer;
    $('meeting').addEventListener('change', () => { current = null; render(); });
    $('filter').addEventListener('change', render);
    $('segment').addEventListener('change', () => { current = $('segment').value; render(); });
    for (const id of ['type', 'extent', 'speech', 'note']) $(id).addEventListener('input', draft);
    $('reviewer').addEventListener('input', draft);
    $('use-id').addEventListener('click', () => { $('speech').value = row().id + ':speech'; draft(); message('Speech ID filled as a draft. Confirm only when the source and context support the declared extent.'); });
    $('confirm').addEventListener('click', () => {
      try {
        draft(); const c = choice(current);
        const copy = B.clone(review), target = copy.choices.find(x => x.id === current);
        Object.assign(target, {confirmed: true, reviewer: $('reviewer').value.trim(), reviewed_at: new Date().toISOString()});
        if (['uncertain', 'suspected_transcription_issue'].includes(target.type) && !target.note.trim())
          throw Error('Describe the uncertainty or suspected transcription problem in notes.');
        review = B.validateReview(p, copy); cache();
        message('Decision confirmed. Source wording and raw evidence remain unchanged.'); nextPending();
        $('record-title').focus({preventScroll: true});
      } catch (e) { message(e.message, true); }
    });
    $('reopen').addEventListener('click', () => {
      if (!confirm('Reopen this confirmed decision? Save your current review JSON first to retain a separate copy of the earlier decision.')) return;
      Object.assign(choice(current), {confirmed: false, reviewed_at: ''}); cache(); fields(choice(current)); progress(); queue();
      message('Review reopened as a draft. Source text has not changed.');
    });
    $('next-pending').addEventListener('click', nextPending);
    for (const [id, step] of [['previous', -1], ['next', 1]]) $(id).addEventListener('click', () => {
      const ids = Array.from($('segment').options).map(o => o.value), at = ids.indexOf(current) + step;
      if (ids[at]) selectRecord(ids[at]);
    });
    $('save').addEventListener('click', () => {
      try {
        draft(); review = B.validateReview(p, review);
        const blob = new Blob([JSON.stringify(review, null, 2) + '\n'], {type: 'application/json'});
        const url = URL.createObjectURL(blob), a = document.createElement('a');
        a.href = url; a.download = 'boundary-review-' + new Date().toISOString().replace(/[:.]/g, '-') + '.json'; a.click();
        setTimeout(() => URL.revokeObjectURL(url), 10000);
        changed = false; lastExport = new Date().toLocaleTimeString();
        message('Review JSON export requested at ' + lastExport + '. Confirm the file appears in your downloads; partial reviews can be resumed.');
      } catch (e) { message(e.message, true); }
    });
    $('import').addEventListener('change', async event => {
      const file = event.target.files?.[0]; if (!file) return;
      try {
        if (file.size > 16 * 1024 * 1024) throw Error('Review file exceeds 16 MB.');
        const imported = B.validateReview(p, JSON.parse((await file.text()).replace(/^\uFEFF/, '')));
        if ((changed || counts().confirmed) && !confirm('Replace this session with the imported source-bound review? Save current work first to preserve it separately.')) return;
        review = imported; cache(); const name = review.choices.find(c => c.reviewer)?.reviewer;
        if (name) $('reviewer').value = name;
        render(); message('Imported matching source-bound review. No source text or held-out material was loaded.');
      } catch (e) { message('Import rejected: ' + e.message, true); }
      finally { event.target.value = ''; }
    });
    $('clear-cache').addEventListener('click', () => {
      if (!confirm('Delete only this packet’s browser-stored copy? The open session and downloaded JSON files will not be deleted.')) return;
      try { localStorage.removeItem(key); $('cache-status').textContent = 'Browser copy removed; the next edit will create a new copy.'; }
      catch (e) { message('Browser storage could not be cleared: ' + e.message, true); }
    });
    window.addEventListener('beforeunload', event => { if (changed) { event.preventDefault(); event.returnValue = ''; } });
    $('loading').hidden = true; $('app').hidden = false; render();
  } catch (e) { $('loading').textContent = 'Packet cannot be opened: ' + e.message; $('loading').setAttribute('role', 'alert'); }
})();
