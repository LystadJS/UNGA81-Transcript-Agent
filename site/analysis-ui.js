/* User interface, report rendering, and local downloads. */
(function () {
  'use strict';

  const el = id => document.getElementById(id);

  const esc = value => String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[character]);

  const pause = () => new Promise(resolve => setTimeout(resolve, 0));
  const split = value => value.split(',').map(item => item.trim()).filter(Boolean);

  let countries = [];
  let controller = null;
  let corpus = null;
  let importedCorpusFile = null;
  let audioLedger = null;
  let result = null;
  let ready = false;
  let stale = false;
  let datesEdited = false;


  // ---------- Form settings and status ----------

  function status(message) {
    el('analysisStatus').textContent = message;
  }


  function openPanel() {
    const id = location.hash === '#review'
      ? 'reviewPanel'
      : location.hash === '#help' ? 'helpPanel' : null;

    if (id) el(id).open = true;
  }

  window.addEventListener('hashchange', openPanel);
  openPanel();


  function settings() {
    return UNAnalysis.parameters({
      topic: el('topic').value.trim(),
      phrases: [el('topic').value.trim(), ...split(el('phrases').value)].filter(Boolean),
      exclude: split(el('excludePhrases').value),
      start: el('startDate').value,
      end: el('endDate').value,
      region: el('region').value,
      scope: el('meetingScope').value,
      nmf:{components:Number(el('nmfComponents').value),starts:Number(el('nmfStarts').value),maxIterations:Number(el('nmfIterations').value),seed:Number(el('nmfSeed').value),
        stability:{enabled:el('nmfStability').checked,unit:el('nmfUnit').value,replicates:Number(el('nmfReplicates').value),fraction:0.8,seed:31415}},
      clustering: {representation:el('representation').value,algorithm:el('clusterAlgorithm').value,linkage:el('clusterLinkage').value,components:Number(el('pcaComponents').value), k:Number(el('clusterCount').value), neighbors:Number(el('umapNeighbors').value), minDist:Number(el('umapDistance').value), seed:Number(el('clusterSeed').value), umapSeed:Number(el('umapSeed').value),
        mds:{enabled:el('mdsEnabled').checked,starts:Number(el('mdsStarts').value),maxIterations:Number(el('mdsIterations').value),seed:Number(el('mdsSeed').value)},
        hdbscan:{minClusterSize:Number(el('hdbMinClusterSize').value),minSamples:Number(el('hdbMinSamples').value),selection:el('hdbSelection').value},
        gmm:{covariance:el('gmmCovariance').value,regularization:Number(el('gmmRegularization').value),starts:Number(el('gmmStarts').value),maxIterations:Number(el('gmmIterations').value),ambiguity:Number(el('gmmAmbiguity').value)},
        stability:{enabled:el('stabilityEnabled').checked,unit:el('stabilityUnit').value,replicates:Number(el('stabilityReplicates').value),fraction:Number(el('stabilityFraction').value),seed:Number(el('stabilitySeed').value)}},
      methods: [...document.querySelectorAll('input[name=method]:checked')]
        .map(input => input.value)
    });
  }


  function updateTopicMode() {
    const all = !el('topic').value.trim();

    el('phrases').disabled = all || !!controller;
    el('excludePhrases').disabled = all || !!controller;
    el('topicModeHelp').textContent = all
      ? 'All passages mode: no topic, related-phrase, or exclusion filtering. Dates, meeting scope, and speaker region still apply.'
      : 'Topic search: match the topic or any comma-separated related phrase. Exclusion phrases remove matching passages.';

    el('frequencyLabel').textContent = all ? 'Passages by region' : 'Topic frequency by region';
    el('timelineLabel').textContent = all ? 'Passages by date' : 'Topic frequency by date';
  }


  function recentDates() {
    // Use the UN New York calendar date, not the visitor's timezone or UTC day.
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit'
    }).formatToParts(new Date());

    const part = type => parts.find(item => item.type === type).value;
    const end = `${part('year')}-${part('month')}-${part('day')}`;
    const start = new Date(end + 'T12:00:00Z');
    start.setUTCDate(start.getUTCDate() - 6);

    return { start: start.toISOString().slice(0, 10), end };
  }


  function setDates(start, end, explanation) {
    el('startDate').value = start;
    el('endDate').value = end;
    el('dateRangeNote').textContent = `${explanation} ${start} through ${end}.`;
    invalidate();
  }


  el('topic').addEventListener('input', updateTopicMode);
  updateTopicMode();

  for (const id of ['startDate', 'endDate']) {
    el(id).addEventListener('input', () => {
      datesEdited = true;
      el('dateRangeNote').textContent = 'Using your selected dates. Changing meeting scope will not change them.';
    });
  }

  el('recentDates').onclick = () => {
    const dates = recentDates();
    datesEdited = true;
    setDates(dates.start, dates.end, 'Last 7 days (New York):');
  };

  el('debateDates').onclick = () => {
    datesEdited = true;
    setDates(el('startDate').defaultValue, el('endDate').defaultValue,
      'General Debate dates; committee proceedings may fall outside this period:');
  };

  el('meetingScope').addEventListener('change', () => {
    const untouched = !datesEdited &&
      el('startDate').value === el('startDate').defaultValue &&
      el('endDate').value === el('endDate').defaultValue;

    if (untouched && el('meetingScope').value.startsWith('committee_')) {
      const dates = recentDates();
      setDates(dates.start, dates.end, 'Switched untouched General Debate defaults to recent dates for committee collection:');
    }

    invalidate();
  });


  // ---------- Reusable report elements ----------

  function table(headers, rows) {
    return `
      <div class="table-wrap">
        <table>
          <thead>
            <tr>${headers.map(value => `<th scope="col">${esc(value)}</th>`).join('')}</tr>
          </thead>
          <tbody>
            ${rows.map(row => `
              <tr>${row.map(value => `<td>${esc(value)}</td>`).join('')}</tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }


  function chart(title, items, label, value, suffix = '') {
    if (!items.length) return '<p>No observations.</p>';

    const maximum = Math.max(...items.map(value), 1e-12);
    const height = items.length * 32 + 36;

    const bars = items.map((item, index) => {
      const amount = value(item);
      const y = index * 32 + 14;
      const shown = suffix === '%'
        ? amount.toFixed(1)
        : Number.isInteger(amount) ? amount : amount.toFixed(3);

      return `
        <text x="0" y="${y + 14}" font-size="13">${esc(label(item).slice(0, 27))}</text>
        <rect class="bar" fill="#002d74" x="220" y="${y}"
              width="${(amount / maximum * 500).toFixed(2)}" height="20" />
        <text x="730" y="${y + 14}" font-size="13">${esc(shown + suffix)}</text>
      `;
    }).join('');

    return `
      <div class="chart-wrap">
        <svg viewBox="0 0 850 ${height}" role="img" aria-label="${esc(title)}">
          <title>${esc(title)}</title>
          ${bars}
        </svg>
      </div>
    `;
  }


  // ---------- Report content ----------

  function render(report) {
    const p = report.parameters;
    const counts = report.counts;
    const methods = report.methods;
    const all = p.mode === 'all';
    const issues = report.coverage.filter(entry => entry.status !== 'collected');
    const byStatus = {};

    for (const entry of report.coverage) {
      byStatus[entry.status] = (byStatus[entry.status] || 0) + 1;
    }

    let html = `
      <div class="report-document">
        <p class="eyebrow">TRANSCRIPT REPORT</p>
        <h2>${esc(all ? 'All passages' : p.topic)}</h2>
        <p>${esc(p.start)} through ${esc(p.end)} · ${esc(p.region)}</p>
        <p><strong>Meeting scope:</strong> ${esc(UNMeetingScopes.label(p.scope))}</p>
        <p>
          ${all ? 'No topic filter; passages follow the selected dates, scope, region and inclusion policy.'
            : `Any phrase: ${esc(p.phrases.join(' | '))}. Exclusions: ${esc(p.exclude.join(' | ') || 'None')}.`}
        </p>
        <p class="method-note">
          Prepared ${esc(report.created_at.slice(0, 10))} · English transcripts
        </p>
    `;

    if(report.passage_selection)html+=`<p class="warning">Reviewed inclusion: ${esc(report.passage_selection.policy==='substantive'?'substantive address segments':'substantive, mixed and fragment segments')}. ${report.passage_selection.eligible_after_type_filter} of ${report.passage_selection.eligible_before_type_filter} passages within the date, scope and region filters remain before deduplication. ${report.passage_selection.human_confirmed} explicit passage decisions; reviewer identity is self-declared. Original text is preserved.</p>`;
    if(report.reviewed_units){const r=report.reviewed_units;
      html+=`<section class="reviewed-unit-summary"><h3>Reviewed speech excerpts</h3>
        <p><strong>${r.included.passages} included excerpts · ${r.included.parent_speeches} parent speeches · ${r.included.meetings} meetings.</strong>
        The import contains ${r.input.passages} excerpts from ${r.input.parent_speeches} speeches; ${r.eligible_before_dedup.passages} pass date, scope and region filters before deduplication.</p>
        <p class="warning">Selected windows do not cover whole speeches. Boundary approval does not verify every word against audio or establish a theme, relevance or stance. These excerpts cannot support representative performance claims.</p>
        <details><summary>Speech coverage and review record</summary>
        ${table(['Parent speech','Excerpts in import','Original text covered'],r.coverage.map(c=>[`${c.country} · ${c.parent_id}`,c.passages,c.coverage_percent.toFixed(1)+'%']))}
        <p>Coverage uses original Unicode code points before topic and date filtering. Each unique excerpt has equal weight; speeches with more retained excerpts contribute more observations.</p>
        <p>Audio checks: ${r.audio_decisions.supported} supported, ${r.audio_decisions.mismatch} discrepancies, ${r.audio_decisions.unclear} unclear. Disputed or unclear overlaps are withheld (${r.withheld.length} proposals). Wording notes remain separate; originals are unchanged. Reviewer identity is self-declared.</p>
        <p>Resampling keeps children of the same parent together using inherited meeting or affiliation groups. Repeated excerpts do not add independent speeches.</p>
        <p class="method-note">Bundle SHA-256 ${esc(r.bundle_sha256)}<br>Original corpus SHA-256 ${esc(r.corpus_sha256)}</p></details></section>`;
    }
    const metrics = [
      [counts.input, report.reviewed_units?'Excerpts imported':'Passages collected'],
      [counts.eligible, 'Unique passages analyzed'],
      [counts.matched, all ? 'Included passages' : 'Topic matches'],
      [counts.duplicates, 'Duplicates removed']
    ];

    html += `
      <div class="metrics">
        ${metrics.map(([value, title]) => `
          <div class="metric"><strong>${esc(value)}</strong>${esc(title)}</div>
        `).join('')}
      </div>
      <p class="method-note">
        ${all ? 'All passages mode includes every eligible unique passage, regardless of its subject.'
          : 'Matches identify language, not a speaker’s position.'}
        These results describe the collected passages; verify their meaning in the source.
      </p>
    `;

    if (!counts.input || !counts.eligible || (!all && !counts.matched)) {
      html += `<p class="warning">${esc(completionMessage(report))}</p>`;
    }

    if (report.collection && (
      p.start < report.collection.start ||
      p.end > report.collection.end ||
      !UNMeetingScopes.covers(report.collection.scope, p.scope)
    )) {
      html += `
        <p class="warning">
          This saved collection does not cover the requested dates or meeting scope.
          Collect live transcripts with the required scope, or import an appropriate collection.
          A General Debate-only collection cannot supply committee proceedings.
        </p>
      `;
    }

    if (report.collection?.selected_meetings === 0 && !report.coverage.some(row => row.status === 'inventory_failed')) {
      html += `
        <p class="warning">
          No meetings were selected from the available inventory for this collection.
          Check the dates and meeting scope; committee meetings may fall outside General Debate dates.
          An empty inventory does not establish that no meeting occurred.
        </p>
      `;
    }

    if (issues.length) {
      html += `
        <p class="warning">
          ${issues.length} collection entries lack usable English text.
          Missing sources are excluded from the match rate.
        </p>
      `;
    }

    html += `
      <details class="coverage-panel"${issues.length || !counts.input ? ' open' : ''}>
        <summary>Collection coverage</summary>
        <p>
          ${esc(counts.input)} ${report.reviewed_units?'excerpts imported':'passages collected'};
          ${esc(counts.eligible_before_dedup)} eligible before deduplication;
          ${esc(counts.unmapped)} with unmapped regions.
        </p>
    `;

    if (report.collection) {
      html += `
        <p>
          Collected ${esc(report.collection.start)}–${esc(report.collection.end)}.
          ${esc(report.collection.selected_meetings)} meetings selected from
          ${esc(report.collection.inventory_meetings)} in the inventory.
          Collection scope: ${esc(UNMeetingScopes.label(report.collection.scope))}.
        </p>
        <p class="method-note">
          Coverage describes the original collection. The analysis above applies
          the currently selected dates, meeting scope, and speaker region.
        </p>
      `;
    }

    if (report.collection?.inventory_days) {
      html += table(['Date', 'Inventory status', 'Meetings found', 'Within selected scope'],
        report.collection.inventory_days.map(day => [
          day.date, day.status, day.meetings ?? 'Unknown', day.selected ?? 'Unknown'
        ]));
    }

    html += table(['Status', 'Entries'], Object.entries(byStatus));
    html += table(
      ['Date', 'Meeting / day', 'Status', 'Detail'],
      report.coverage.map(entry => [
        entry.date,
        entry.title || 'Daily inventory',
        entry.status,
        entry.error || entry.language || ''
      ])
    );
    html += '</details>';

    for (const [key, title] of [
      ['frequency', 'Topic frequency by region'],
      ['timeline', 'Topic frequency by date']
    ]) {
      if (!methods[key]) continue;

      html += `
        <h3>${all ? title.replace('Topic frequency', 'Passages') : title}</h3>
        <p class="method-note">
          ${all ? 'Counts of unique eligible passages, without topic filtering.'
            : 'Share of eligible passages containing the topic.'}
          Groups without eligible text are omitted.
        </p>
        ${chart(all ? title.replace('Topic frequency', 'Passages') : title, methods[key],
          row => row.name, row => all ? row.total : row.percent, all ? '' : '%')}
        <details>
          <summary>View figures</summary>
          ${all ? table(['Group', 'Passages'], methods[key].map(row => [row.name, row.total]))
            : table(['Group', 'Matched', 'Eligible', 'Match %'], methods[key].map(row => [
              row.name, row.matches, row.total, row.percent.toFixed(2)
            ]))}
        </details>
      `;
    }

    if (methods.length) {
      html += `
        <h3>Passage length</h3>
        <p class="method-note">Word counts for included unique passages.</p>
        ${chart('Segment length', methods.length, row => row.name, row => row.total)}
        <details>
          <summary>View figures</summary>
          ${table(['Words', 'Passages'], methods.length.map(row => [row.name, row.total]))}
        </details>
      `;
    }

    if (methods.clusters) html += UNClusterView.render(methods.clusters,report.matched,table,chart);
    if (methods.nmf) html += UNNMFView.render(methods.nmf,report.matched,table);

    if (methods.tfidf) {
      html += `
        <h3>TF-IDF term ranking</h3>
        <p class="method-note">Terms ranked by their average TF-IDF weight across included unique passages.</p>
        <details>
          <summary>Calculation</summary>
          <p>
            Top 20 mean L2-normalized weights across included segments; lowercase Unicode unigrams,
            length &gt;2, fixed English stop list, sublinear TF = 1 + ln(count),
            smoothed IDF = 1 + ln((1 + N)/(1 + document frequency)).
            Vocabulary: ${methods.tfidf.vocabulary}. Query terms may rank highly.
          </p>
        </details>
        ${chart('Mean TF-IDF weight', methods.tfidf.terms, row => row.term, row => row.mean)}
        <details>
          <summary>View figures</summary>
          ${table(['Term', 'Mean weight', 'Passages'], methods.tfidf.terms.map(row => [
            row.term, row.mean.toFixed(5), row.documents
          ]))}
        </details>
      `;
    }

    if (methods.similarity) {
      html += '<h3>Pairwise cosine text similarity</h3>';

      if (methods.similarity.skipped) {
        html += `<p class="warning">${esc(methods.similarity.skipped)}</p>`;
      } else {
        html += `
          <p class="method-note">
            Top 10 of ${methods.similarity.compared} pairs using the same full TF-IDF vectors.
            Similar language is not evidence of shared stance or coordination.
            Exact duplicates have already been removed.
          </p>
          ${table(['Segment A', 'Segment B', 'Cosine'], methods.similarity.pairs.map(row => [
            row.left, row.right, row.cosine.toFixed(4)
          ]))}
        `;
      }
    }

    html += `
      <h3>Source passages</h3>
      <p>
        Showing ${Math.min(100, report.matched.length)} of ${report.matched.length} source segments.
        Download analysis JSON or CSV for every included unique passage. ${report.reviewed_units?'Save reviewed bundle retains the original collection, review packet and choices for re-import.':'Save transcripts retains all original collected segments, including duplicates.'}
      </p>
    `;

    for (const record of report.matched.slice(0, 100)) {
      html += `
        <div class="evidence-item">
          <strong>${esc(record.country)} · ${esc(record.date)}</strong>
          <p>${esc(record.meeting)}</p>
          <p class="method-note">${esc(record.region)} · ${esc(UNMeetingScopes.label(record.scope))}</p>
          <p>${esc(record.text.slice(0, 350))}${record.text.length > 350 ? '…' : ''}</p>
          <details>
            <summary>${record.parent_id?'Read reviewed excerpt':'Read full source segment'}</summary>
            <blockquote>${esc(record.text)}</blockquote>
            <p class="method-note">Record ${esc(record.id)} · SHA-256 ${esc(record.text_sha256)}</p>
            ${record.parent_id?`<p class="method-note">Parent ${esc(record.parent_id)} · Original offsets ${record.start}–${record.end} (Unicode code points, zero-based, end exclusive). ${esc(record.review_scope)}</p>`:''}
          </details>
          <a href="${esc(record.source_url)}" target="_blank" rel="noopener noreferrer">
            Open original source ↗
          </a>
        </div>
      `;
    }

    html += `
        <details class="report-notes">
          <summary>Methods and source record</summary>
          <p>
            <strong>These comparisons describe the collected text.</strong>
            Segments can contain procedural remarks, repeat a speaker or depend on the same meeting.
            The figures do not estimate population effects or establish coordination.
          </p>
          <p>
            <strong>Meeting scope follows meeting identity, not speech content.</strong>
            Canonical UN committee paths take priority; recognized meeting-title labels are a fallback.
            Older saved records are reclassified from their retained meeting metadata when possible.
            Imported metadata remains author-supplied, not authenticated.
          </p>
          <p>
            <strong>The data export preserves the analysis.</strong>
            It records the query, methods, source links, text hashes and duplicate mapping.
            Exact-text deduplication normalizes Unicode and whitespace; near-duplicates remain.
            Text hashes establish integrity rather than authenticity.
          </p>
          <p class="method-note">Engine: ${esc(report.engine)} · Prepared: ${esc(report.created_at)}</p>
        </details>
      </div>
    `;

    return html;
  }


  // Different failure stages must not be reported as successful zero matches.
  function completionMessage(report) {
    const n = report.counts;
    const failedDays = report.coverage.filter(row => row.status === 'inventory_failed');
    const failedMeetings = report.coverage.filter(row => row.status === 'failed');
    const selected = report.collection?.selected_meetings;
    const range = `${report.parameters.start} through ${report.parameters.end}`;
    const scope = UNMeetingScopes.label(report.parameters.scope);

    if (!n.input && (failedDays.length || failedMeetings.length)) {
      const reason = (failedDays[0] || failedMeetings[0]).error || 'Unknown download error';
      return `Collection incomplete: no usable passages were downloaded. ${reason} See Collection coverage; this is not a zero-match finding.`;
    }

    if (!n.input && selected === 0) {
      return `No meetings found for ${scope} from ${range}. Check the dates or use Last 7 days. No transcripts were downloaded.`;
    }

    if (!n.input) {
      return `${selected ?? 'Selected'} meetings found, but no usable English transcript passages were available. See Collection coverage for unavailable, pending, or non-English sources.`;
    }

    const prefix = failedDays.length || report.coverage.some(row => row.status !== 'collected')
      ? 'Partial collection' : 'Collection ready';
    const collected = `${prefix}: ${n.input} passages collected; ${n.eligible} unique passages within your filters.`;

    if (!n.eligible) return collected + ' Check dates, speaker region, meeting scope, passage inclusion, or the scope of the imported collection.';
    if (report.parameters.mode === 'all') return collected + ' All passages mode — no topic filter.';
    if (!n.matched) return collected + ' No topic matches; leave Topic blank to include all passages.';

    return collected + ` ${n.matched} topic matches.`;
  }


  // ---------- Local downloads and stale-result protection ----------

  function save(value, name, type) {
    const url = URL.createObjectURL(new Blob([value], { type }));
    const link = document.createElement('a');

    link.href = url;
    link.download = name;
    link.click();

    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }


  const exportButtons = () => [...el('analysisOutput').querySelectorAll('button')];

  function invalidate() {
    if (!result) return;

    stale = true;
    exportButtons().forEach(button => { button.disabled = true; });
    status('Settings changed. Generate a new report before exporting.');
  }

  el('analysisForm').addEventListener('input', invalidate);
  el('analysisForm').addEventListener('change', invalidate);

  el('corpusSource').onchange = () => {
    el('corpusFileLabel').hidden = el('corpusSource').value !== 'import';
    el('reviewedSelection').hidden=el('corpusSource').value!=='import';
    el('reviewedUnitsFileLabel').hidden=el('corpusSource').value!=='reviewed';
  };

  el('cancelAnalysis').onclick = () => controller?.abort();


  function updateClusterControls() {
    const active=el('clusterMethod').checked;
    el('clusterSettings').hidden=!active;
    el('clusterSettings').querySelectorAll('input,select').forEach(input=>{input.disabled=!active || !!controller;});
    const hierarchical=el('clusterAlgorithm').value==='hierarchical';
    el('linkageLabel').hidden=!hierarchical;
    el('clusterLinkage').disabled=!active||!hierarchical||!!controller;
    const mixture=el('clusterAlgorithm').value==='gmm';
    el('gmmSettings').hidden=!mixture;
    el('gmmSettings').querySelectorAll('input,select').forEach(input=>{input.disabled=!active||!mixture||!!controller;});
    el('clusterCount').min=mixture?'1':'2';
    if(!mixture&&el('clusterCount').value==='1')el('clusterCount').value='2';
    el('clusterSeedLabel').textContent=mixture?'Mixture initialization seed':'K-means seed';
    const seeded=el('clusterAlgorithm').value==='kmeans'||mixture;
    el('clusterSeed').disabled=!active||!seeded||!!controller;
    el('clusterSeed').parentElement.hidden=!seeded;
    const density=el('clusterAlgorithm').value==='hdbscan';
    el('clusterCount').disabled=!active||density||!!controller;
    el('clusterCount').parentElement.hidden=density;
    el('hdbscanSettings').hidden=!density;
    el('hdbscanSettings').querySelectorAll('input,select').forEach(input=>{input.disabled=!active||!density||!!controller;});
    const mds=active&&el('mdsEnabled').checked;el('mdsSettings').hidden=!mds;
    el('mdsSettings').querySelectorAll('input').forEach(input=>{input.disabled=!mds||!!controller;});
    const stability=active&&el('stabilityEnabled').checked;
    el('stabilitySettings').hidden=!stability;
    el('stabilitySettings').querySelectorAll('input,select').forEach(input=>{input.disabled=!stability || !!controller;});
  }
  el('clusterMethod').addEventListener('change',updateClusterControls);
  el('mdsEnabled').addEventListener('change',updateClusterControls);
  el('stabilityEnabled').addEventListener('change',updateClusterControls);
  el('clusterAlgorithm').addEventListener('change',updateClusterControls);
  updateClusterControls();

  function updateNMFControls(){
    const active=el('nmfMethod').checked;el('nmfSettings').hidden=!active;
    el('nmfSettings').querySelectorAll('input,select').forEach(e=>{e.disabled=!active||!!controller;});
    el('nmfResampling').hidden=!el('nmfStability').checked;
    el('nmfResampling').querySelectorAll('input,select').forEach(e=>{e.disabled=!active||!el('nmfStability').checked||!!controller;});
  }
  el('nmfMethod').addEventListener('change',updateNMFControls);el('nmfStability').addEventListener('change',updateNMFControls);updateNMFControls();
  function runNMFWorker(records,vectors,options){
    return new Promise((resolve,reject)=>{
      const signal=controller.signal,worker=new Worker('nmf-worker.js?v=1.11.0');
      const finish=(fn,v)=>{worker.terminate();signal.removeEventListener('abort',abort);fn(v);};
      const abort=()=>finish(reject,new DOMException('Cancelled','AbortError'));signal.addEventListener('abort',abort,{once:true});
      worker.onerror=()=>finish(reject,Error('NMF worker could not run. Reload the page or check browser permissions.'));
      worker.onmessage=({data})=>{if(data.type==='progress')status(data.message);if(data.type==='result')finish(resolve,data.result);if(data.type==='error')finish(reject,Error(data.message));};
      if(signal.aborted){abort();return;}worker.postMessage({records,vectors:vectors.map(v=>[...v]),options});
    });
  }

  function runClusterWorker(records,vectors,options,progress) {
    return new Promise((resolve,reject)=>{
      const signal=controller.signal,worker=new Worker('cluster-worker.js?v=1.11.0');
      const finish=(fn,value)=>{worker.terminate();signal.removeEventListener('abort',abort);fn(value);};
      const abort=()=>finish(reject,new DOMException('Cancelled','AbortError'));
      signal.addEventListener('abort',abort,{once:true});
      worker.onerror=()=>finish(reject,Error('The clustering worker could not run. Reload the page or check browser permissions.'));
      worker.onmessage=({data})=>{
        if(data.type==='progress')status(data.message);
        if(data.type==='result')finish(resolve,data.result);
        if(data.type==='error')finish(reject,Error(data.message));
      };
      if(signal.aborted){abort();return;}
      worker.postMessage({records:records.map(r=>({id:r.id,text_sha256:r.text_sha256,
        ...(options.stability.enabled?{text:r.text,date:r.date,meeting:r.meeting,scope:r.scope,country:r.country,source_url:r.source_url}:{})})),vectors:vectors.map(v=>[...v]),options});
    });
  }

  // ---------- Collect / import, analyze, and render ----------

  el('analysisForm').onsubmit = async event => {
    event.preventDefault();
    if (controller) return;

    try {
      if (!ready) throw Error('Country registry is not available. Reload the page.');

      const p = settings();
      controller = new AbortController();

      for (const control of el('analysisForm').elements) control.disabled = true;

      el('cancelAnalysis').disabled = false;
      el('analysisOutput').hidden = true;
      result = null;
      corpus = null;
      importedCorpusFile = null;
      audioLedger = null;
      stale = false;

      if (el('corpusSource').value === 'import') {
        status('Checking imported collection and hashes…');
        const file = el('corpusFile').files[0];

        if (!file || file.size > 30000000) {
          throw Error('Choose a collection JSON under 30 MB.');
        }

        const savedText=await file.text();
        corpus = UNAnalysis.validateCorpus(JSON.parse(savedText.replace(/^\uFEFF/,'')));
        importedCorpusFile = file;

        for (const record of corpus.records) {
          if (controller.signal.aborted) throw new DOMException('Cancelled', 'AbortError');

          if (await UNCollector.sha(record.text) !== record.text_sha256) {
            throw Error('Text hash mismatch for ' + record.id);
          }
        }
        if(el('passagePolicy').value!=='full'){
          const reviewFile=el('passageReviewFile').files[0];
          if(!reviewFile||reviewFile.size>2000000)throw Error('Choose the completed passage review JSON under 2 MB.');
          const reviewText=await reviewFile.text();
          const digest=await crypto.subtle.digest('SHA-256',await file.arrayBuffer());
          p.passageSelection={policy:el('passagePolicy').value,review:JSON.parse(reviewText.replace(/^\uFEFF/,'')),
            corpus_sha256:[...new Uint8Array(digest)].map(b=>b.toString(16).padStart(2,'0')).join(''),review_sha256:await UNCollector.sha(reviewText)};
          UNPassageSelection.validate(corpus,p.passageSelection);
        }
      } else if(el('corpusSource').value==='reviewed'){
        status('Validating reviewed excerpts against originals and saved decisions…');
        const file=el('reviewedUnitsFile').files[0];
        if(!file||file.size>30000000)throw Error('Choose a reviewed analysis bundle under 30 MB.');
        const loaded=await UNReviewedUnits.load(await file.arrayBuffer(),UNAnalysis.validateCorpus,async message=>{
          status(message);await pause();if(controller.signal.aborted)throw new DOMException('Cancelled','AbortError');
        });
        corpus=loaded.corpus;audioLedger=loaded.ledger;importedCorpusFile=file;
      } else {
        corpus = await UNCollector.collect(p, countries, {
          signal: controller.signal,
          progress: status
        });
      }

      if (controller.signal.aborted) throw new DOMException('Cancelled', 'AbortError');

      status('Analyzing collected text…');
      await pause();

      result = await UNAnalysis.analyze(corpus, p, async message => {
        status(message);
        await pause();

        if (controller.signal.aborted) throw new DOMException('Cancelled', 'AbortError');
      }, runClusterWorker, runNMFWorker);

      if (controller.signal.aborted) throw new DOMException('Cancelled', 'AbortError');

      el('analysisReport').innerHTML = render(result);
      el('exportClusters').hidden=!clusterFits(result.methods.clusters).some(f=>f.points);
      el('exportConsensus').hidden=!clusterFits(result.methods.clusters).some(f=>f.stability?.consensus&&!f.stability.skipped);
      el('exportHierarchy').hidden=!clusterFits(result.methods.clusters).some(f=>f.hierarchical);
      el('exportNMF').hidden=!result.methods.nmf?.points;
      el('exportAudioLedger').hidden=!audioLedger;
      el('exportCorpus').textContent=result.reviewed_units?'Save reviewed bundle':'Save transcripts';
      el('analysisOutput').hidden = false;
      exportButtons().forEach(button => { button.disabled = false; });

      el('exportCSV').textContent = result.parameters.mode === 'all'
        ? 'Included passages (.csv)' : 'Matched passages (.csv)';
      status(completionMessage(result));
    } catch (error) {
      result = null;
      corpus = null;
      importedCorpusFile = null;
      audioLedger = null;
      el('analysisOutput').hidden = true;

      status(error.name === 'AbortError'
        ? 'Collection cancelled. No partial report was released.'
        : 'Could not complete report: ' + error.message +
          (el('corpusSource').value==='live'?' If live access is blocked by your network, import an exported collection.':''));
    } finally {
      controller = null;

      for (const control of el('analysisForm').elements) control.disabled = false;
      el('cancelAnalysis').disabled = true;
      updateTopicMode();
      updateClusterControls();
      updateNMFControls();
    }
  };


  // ---------- Export buttons ----------
  const clusterFits=fit=>!fit?[]:[fit,...(fit.comparison?[fit.comparison.alternative]:[])];
  const lineageFields=()=>result?.reviewed_units?['parent_id','parent_text_sha256','start','end','offset_unit']:[];
  const lineageValues=id=>{const r=result.matched.find(r=>r.id===id);return lineageFields().map(k=>r?.[k]);};
  el('exportConsensus').onclick=()=>{
    if(stale)return;
    const fits=clusterFits(result?.methods.clusters).filter(f=>f.stability?.consensus&&!f.stability.skipped);
    if(!fits.length)return;
    const compare=!!result.methods.clusters.comparison,typed=fits[0].algorithm!=='kmeans';
    const density=fits[0].algorithm==='hdbscan';
    const quote=v=>'"'+String(v??'').replace(/^[=+@\-\t\r]/,"'$&").replace(/"/g,'""')+'"';
    const rows=[['representation',...(typed?['algorithm','linkage']:[]),'left_id','right_id','left_cluster','right_cluster','co_observed','co_clustered','co_assignment_rate',...(density?['left_assignment','right_assignment','co_assigned','co_assignment_given_assigned']:[])]];
    for(const fit of fits){const s=fit.stability;
      for(let i=1;i<s.reference_ids.length;i++)for(let j=0;j<i;j++){
        const pos=i*(i-1)/2+j,o=s.consensus.co_observed[pos],t=s.consensus.co_clustered[pos];
        rows.push([fit.representation||'pca',...(typed?[fit.algorithm,fit.hierarchical?.linkage||'']:[]),s.reference_ids[i],s.reference_ids[j],s.reference_clusters[i],s.reference_clusters[j],o,t,o?t/o:'',
          ...(density?[s.reference_clusters[i]?'assigned':'unassigned',s.reference_clusters[j]?'assigned':'unassigned',s.consensus.co_assigned[pos],s.consensus.co_assigned[pos]?t/s.consensus.co_assigned[pos]:'']:[])]);
      }
    }
    // Preserve the previous PCA-only column contract.
    if(!compare&&!typed&&fits[0].representation!=='lsa')rows.forEach(row=>row.shift());
    save('\uFEFF'+rows.map(row=>row.map(quote).join(',')).join('\r\n'),'un-consensus.csv','text/csv;charset=utf-8');
  };
  el('exportClusters').onclick=()=>{
    if(stale)return;
    const fits=clusterFits(result?.methods.clusters).filter(f=>f.points);if(!fits.length)return;
    const compare=!!result.methods.clusters.comparison,typed=fits[0].algorithm!=='kmeans';
    const density=fits[0].algorithm==='hdbscan',mds=fits.some(f=>f.points.some(p=>p.mds));
    const mixture=fits[0].algorithm==='gmm',mixtureK=mixture?fits[0].parameters.k:0;
    const quote=v=>'"'+String(v??'').replace(/^[=+@\-\t\r]/,"'$&").replace(/"/g,'""')+'"';
    const stable=fits.some(f=>f.stability?.consensus&&!f.stability.skipped);
    const dimensions=Math.max(...fits.map(f=>f[f.representation||'pca'].components));
    const prefix=compare?'D':fits[0].representation==='lsa'?'LS':'PC';
    const fields=[...(compare||typed?['representation']:[]),...(typed?['algorithm','linkage','representative_role','is_representative']:[]),'id','text_sha256','cluster',...(density?['assignment_status','membership_strength']:[]),...(mixture?['covariance','regularization','max_membership','membership_margin','normalized_entropy','ambiguous',...Array.from({length:mixtureK},(_,i)=>'component_'+(i+1)+'_membership'),'membership_refits','mean_membership_tv']:[]),...Array.from({length:dimensions},(_,i)=>prefix+(i+1)),'UMAP1','UMAP2',...(mds?['MDS1','MDS2']:[]),
      ...(stable?['resamples_included','observed_peers','within_cluster_consensus','strongest_other_consensus','consensus_margin',...(density?['resamples_assigned','resamples_unassigned','assignment_rate']:[])]:[])];
    const rows=[[...fields,...lineageFields()]];
    for(const fit of fits){const method=fit.representation||'pca';
      fit.points.forEach((p,i)=>{const s=!fit.stability?.skipped?fit.stability?.consensus?.points[i]:null;
        const soft=fit.stability?.soft_membership?.points[i];
        const group=fit.clusters[p.cluster-1];
        rows.push([...(compare||typed?[method]:[]),...(typed?[fit.algorithm,fit.hierarchical?.linkage||'',group?.representative_role||'',group?.representative_id===p.id]:[]),p.id,p.text_sha256,p.cluster,...(density?[p.assignment_status,p.membership_strength]:[]),...(mixture?[fit.gmm.covariance_type,fit.gmm.regularization,p.max_membership,p.membership_margin,p.normalized_entropy,p.ambiguous,...p.memberships,soft?.count,soft?.mean]:[]),...Array.from({length:dimensions},(_,d)=>p[method][d]??''),...p.umap,...(mds?(p.mds||['','']):[]),
          ...(stable?[s?.included,s?.observed_peers,s?.within_cluster,s?.strongest_other,s?.margin,...(density?[s?.assigned,s?.unassigned,s?.assignment_rate]:[])]:[]),...lineageValues(p.id)]);
      });
    }
    save('\uFEFF'+rows.map(row=>row.map(quote).join(',')).join('\r\n'),'un-clusters.csv','text/csv;charset=utf-8');
  };

  el('exportHierarchy').onclick=()=>{
    if(stale)return;
    const fits=clusterFits(result?.methods.clusters).filter(f=>f.hierarchical);if(!fits.length)return;
    const rows=[['representation','algorithm','linkage','node','left','right','height','size','leaf_id','source_url','selected_cluster',...lineageFields()]];
    const byId=new Map(result.matched.map(r=>[r.id,r]));
    for(const fit of fits){const h=fit.hierarchical,prefix=[fit.representation,fit.algorithm,h.linkage];
      fit.points.forEach((p,i)=>rows.push([...prefix,i,'','',0,1,p.id,byId.get(p.id).source_url,p.cluster,...lineageValues(p.id)]));
      h.merges.forEach(m=>rows.push([...prefix,m.node,m.left,m.right,m.height,m.size,'','',h.cut_nodes.includes(m.node)?h.cut_nodes.indexOf(m.node)+1:'',...lineageFields().map(()=>'')]));
    }
    const quote=v=>'"'+String(v??'').replace(/^[=+@\-\t\r]/,"'$&").replace(/"/g,'""')+'"';
    save('\uFEFF'+rows.map(row=>row.map(quote).join(',')).join('\r\n'),'un-hierarchy.csv','text/csv;charset=utf-8');
  };

  el('exportNMF').onclick=()=>{
    const f=result?.methods.nmf;if(!f?.points||stale)return;
    const byId=new Map(result.matched.map(r=>[r.id,r]));
    const rows=[['id','source_url','text_sha256',...f.components.map(c=>'component_'+c.component+'_weight'),...f.components.map(c=>'component_'+c.component+'_share'),...lineageFields()],
      ...f.points.map(p=>[p.id,byId.get(p.id)?.source_url,p.text_sha256,...p.weights,...(p.shares||f.components.map(()=>'')),...lineageValues(p.id)])];
    const cell=v=>'"'+String(v??'').replace(/^[=+@\-\t\r]/,"'$&").replace(/"/g,'""')+'"';
    save('\uFEFF'+rows.map(r=>r.map(cell).join(',')).join('\r\n'),'un-nmf-mixtures.csv','text/csv;charset=utf-8');
  };
  el('exportResult').onclick = () => {
    if (result && !stale) {
      save(JSON.stringify(result, null, 2), 'un-analysis.json', 'application/json');
    }
  };

  el('exportCorpus').onclick = () => {
    if (corpus && !stale) {
      save(importedCorpusFile || JSON.stringify(corpus), result.reviewed_units?'reviewed-analysis.json':'un-transcripts.json', 'application/json');
    }
  };
  el('exportAudioLedger').onclick=()=>{
    if(audioLedger&&!stale)save(JSON.stringify(audioLedger,null,2),'audio-review-ledger.json','application/json');
  };

  el('exportCSV').onclick = () => {
    if (!result || stale) return;

    const fields = [
      'id', 'date', 'country', 'region', 'scope', 'meeting',
      'source_url', 'text_sha256', 'text',
      ...(result.reviewed_units?['parent_id','parent_text_sha256','parent_raw_sha256','corpus_sha256','start','end','offset_unit','utf8_start','utf8_end','source_group','reviewer','reviewed_at','review_scope']:[])
    ];

    const cell = value => '"' + String(value ?? '')
      .replace(/^[=+@\-\t\r]/, "'$&")
      .replace(/"/g, '""') + '"';

    const rows = [fields, ...result.matched.map(record => fields.map(field => record[field]))];
    const csv = '\uFEFF' + rows.map(row => row.map(cell).join(',')).join('\r\n');

    save(csv, result.parameters.mode === 'all' ? 'un-all-passages.csv' : 'un-matched-segments.csv',
      'text/csv;charset=utf-8');
  };

  el('exportHTML').onclick = async () => {
    if (!result || stale) return;

    try {
      const response = await fetch('analysis.css');
      if (!response.ok) throw Error('Styles unavailable');

      const css = await response.text();
      const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'">
  <title>UN transcript report</title>
  <style>
    body { font: 16px/1.5 Arial,sans-serif; max-width: 1100px; margin: auto; padding: 28px; }
    ${css}
  </style>
</head>
<body>
  ${render(result)}
</body>
</html>`;

      save(html, 'un-report.html', 'text/html');
    } catch (error) {
      status('Report download failed: ' + error.message);
    }
  };

  el('printAnalysis').onclick = () => {
    if (result && !stale) window.print();
  };


  // ---------- Initial country-registry load ----------

  fetch('countries.json')
    .then(response => {
      if (!response.ok) throw Error('Registry unavailable');
      return response.json();
    })
    .then(data => {
      countries = data;

      for (const region of [...new Set(data.map(country => country.region))].sort()) {
        const option = document.createElement('option');
        option.textContent = region;
        el('region').append(option);
      }

      ready = true;
    })
    .catch(error => status('Country registry failed to load: ' + error.message));

})();
