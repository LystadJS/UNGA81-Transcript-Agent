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
          ${all ? 'No topic filter; all available passages within the selected dates, scope, and region are included.'
            : `Any phrase: ${esc(p.phrases.join(' | '))}. Exclusions: ${esc(p.exclude.join(' | ') || 'None')}.`}
        </p>
        <p class="method-note">
          Prepared ${esc(report.created_at.slice(0, 10))} · English transcripts
        </p>
    `;

    const metrics = [
      [counts.input, 'Passages collected'],
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
          ${esc(counts.input)} passages collected;
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
        Download analysis JSON or CSV for every included unique passage. Save transcripts retains all original collected segments, including duplicates.
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
            <summary>Read full source segment</summary>
            <blockquote>${esc(record.text)}</blockquote>
            <p class="method-note">Record ${esc(record.id)} · SHA-256 ${esc(record.text_sha256)}</p>
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

    if (!n.eligible) return collected + ' Check dates, speaker region, meeting scope, or the scope of the imported collection.';
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

  el('corpusSource').onchange = () => {
    el('corpusFileLabel').hidden = el('corpusSource').value !== 'import';
  };

  el('cancelAnalysis').onclick = () => controller?.abort();


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
      stale = false;

      if (el('corpusSource').value === 'import') {
        status('Checking imported collection and hashes…');
        const file = el('corpusFile').files[0];

        if (!file || file.size > 30000000) {
          throw Error('Choose a collection JSON under 30 MB.');
        }

        corpus = UNAnalysis.validateCorpus(JSON.parse(await file.text()));

        for (const record of corpus.records) {
          if (controller.signal.aborted) throw new DOMException('Cancelled', 'AbortError');

          if (await UNCollector.sha(record.text) !== record.text_sha256) {
            throw Error('Text hash mismatch for ' + record.id);
          }
        }
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
      });

      if (controller.signal.aborted) throw new DOMException('Cancelled', 'AbortError');

      el('analysisReport').innerHTML = render(result);
      el('analysisOutput').hidden = false;
      exportButtons().forEach(button => { button.disabled = false; });

      el('exportCSV').textContent = result.parameters.mode === 'all'
        ? 'Included passages (.csv)' : 'Matched passages (.csv)';
      status(completionMessage(result));
    } catch (error) {
      result = null;
      corpus = null;
      el('analysisOutput').hidden = true;

      status(error.name === 'AbortError'
        ? 'Collection cancelled. No partial report was released.'
        : 'Could not complete report: ' + error.message +
          ' If live access is blocked by your network, import an exported collection.');
    } finally {
      controller = null;

      for (const control of el('analysisForm').elements) control.disabled = false;
      el('cancelAnalysis').disabled = true;
      updateTopicMode();
    }
  };


  // ---------- Export buttons ----------

  el('exportResult').onclick = () => {
    if (result && !stale) {
      save(JSON.stringify(result, null, 2), 'un-analysis.json', 'application/json');
    }
  };

  el('exportCorpus').onclick = () => {
    if (corpus && !stale) {
      save(JSON.stringify(corpus), 'un-transcripts.json', 'application/json');
    }
  };

  el('exportCSV').onclick = () => {
    if (!result || stale) return;

    const fields = [
      'id', 'date', 'country', 'region', 'scope', 'meeting',
      'source_url', 'text_sha256', 'text'
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
