/* Accessible rendering for deterministic, source-linked day summaries. */
(function(root){
  'use strict';

  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[char]));
  const list=value=>Array.isArray(value)?value:[];
  const safeURL=value=>{
    try { const url=new URL(String(value)); return /^(?:https?):$/.test(url.protocol)?url.href:null; }
    catch (_) { return null; }
  };
  const unique=value=>[...new Set(list(value).filter(Boolean).map(String))];
  const count=value=>Number.isFinite(Number(value))?Number(value):0;

  function evidenceItems(claim){
    return list(claim?.evidence||claim?.sources).filter(item=>safeURL(item?.source_url||item?.url));
  }

  function evidence(claim){
    const rows=evidenceItems(claim);
    return rows.map(item=>{
      const url=safeURL(item.source_url||item.url);
      const label=[item.country,item.meeting_title||item.meeting,item.date,item.record_id]
        .filter(Boolean).join(' · ')||'Source transcript';
      return `<li><blockquote>${esc(item.excerpt||item.passage||'Source passage')}</blockquote><p><a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a></p></li>`;
    }).join('');
  }

  function supportedClaims(value){
    return list(value).filter(claim=>claim&&typeof claim==='object'&&claim.text&&evidenceItems(claim).length);
  }

  function claims(title,value,empty){
    const raw=list(value),rows=supportedClaims(raw),withheld=raw.length-rows.length;
    return `<section class="day-topic-claims"><h5>${esc(title)}</h5>${rows.length
      ? `<ul>${rows.map(claim=>`<li><p><strong>${esc(claim.text)}</strong></p><details><summary>Supporting passage${evidenceItems(claim).length===1?'':'s'} · ${evidenceItems(claim).length}</summary><ol>${evidence(claim)}</ol></details></li>`).join('')}</ul>`
      : `<p>${esc(empty)}</p>`}${withheld?`<p class="warning">${withheld} unsupported candidate claim${withheld===1?' was':'s were'} withheld because no safe source link was attached.</p>`:''}</section>`;
  }

  function coverage(topic){
    const c=topic.coverage||{};
    const meetings=count(c.meetings??topic.meeting_count),segments=count(c.segments??topic.segment_count??topic.passage_count);
    const countries=count(c.countries??topic.country_count??list(topic.participants).length);
    return `${meetings} meeting${meetings===1?'':'s'} · ${segments} source segment${segments===1?'':'s'} · ${countries} recorded countr${countries===1?'y':'ies'}`;
  }

  function meetingRows(summary){
    const meetings=list(summary.meetings);
    if(!meetings.length)return '<p>No meeting-specific breakdown is available for this day.</p>';
    return `<div class="table-wrap"><table><thead><tr><th scope="col">Meeting</th><th scope="col">Usable source segments</th><th scope="col">Substantive passages</th><th scope="col">Topics identified</th></tr></thead><tbody>${meetings.map(meeting=>{
      const name=meeting.title||meeting.meeting_title||meeting.id||meeting.meeting_slug||'Recorded meeting';
      const url=safeURL(meeting.source_url);
      return `<tr><td data-label="Meeting">${url?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(name)}</a>`:esc(name)}${meeting.id||meeting.meeting_slug?`<br><small>${esc(meeting.id||meeting.meeting_slug)}</small>`:''}</td><td data-label="Source segments">${count(meeting.source_segments??meeting.segments)}</td><td data-label="Substantive passages">${count(meeting.substantive_passages??meeting.substantive_segments)}</td><td data-label="Topics">${esc(unique(meeting.topics||meeting.topic_labels).join(', ')||'None identified')}</td></tr>`;
    }).join('')}</tbody></table></div>`;
  }

  function topic(topic,index){
    const participants=unique(topic.participants||topic.countries);
    const question=topic.policy_question||topic.question||topic.label||'Policy question not labeled';
    return `<article class="day-topic" aria-labelledby="day-topic-${index}">
      <h4 id="day-topic-${index}">${esc(topic.label||question)}</h4>
      <p><strong>Policy question:</strong> ${esc(question)}</p>
      <p class="method-note"><strong>Coverage:</strong> ${esc(coverage(topic))}. Coverage describes where this question appears; it does not measure political importance.</p>
      <p><strong>Participating recorded countries:</strong> ${esc(participants.join(', ')||'No national attribution established')}</p>
      ${claims('Principal proposals',topic.proposals,'No source-linked proposal was identified.')}
      ${claims('Disagreements and reservations',topic.disagreements||topic.reservations,'No source-linked disagreement was identified.')}
      ${claims('Consequential developments',topic.consequential_developments||topic.developments,'No explicit action, outcome or material change was identified by the consequential-development rules.')}
      ${topic.meetings?.length?`<details><summary>Meeting-specific distinctions</summary><ul>${topic.meetings.map(meeting=>`<li><strong>${esc(meeting.title||meeting.meeting_title||meeting.id||'Meeting')}</strong>${meeting.summary?` — ${esc(meeting.summary)}`:''}${meeting.participants?.length?` · ${esc(unique(meeting.participants).join(', '))}`:''}</li>`).join('')}</ul></details>`:''}
    </article>`;
  }

  function render(summary){
    if(!summary)return '';
    const topics=list(summary.topics),procedural=summary.procedural||summary.processing||{};
    const method=summary.methodology||summary.method||{};
    const limitations=list(summary.limitations);
    const substantive=count(summary.stats?.substantive_passages??summary.stats?.substantive_segments);
    const excluded=count(summary.stats?.procedural_or_ceremonial??procedural.procedural_or_ceremonial_count??procedural.removed_sentence_count);
    const date=summary.date||summary.reporting_date||summary.start_date||'Selected day';
    const topDevelopments=supportedClaims(summary.consequential_developments||summary.developments);
    const rawDevelopments=list(summary.consequential_developments||summary.developments);

    return `<section id="daySummary" class="day-summary" aria-label="Day-level proceedings summary">
      <p class="eyebrow">DAY BRIEFING · OFFLINE, SOURCE-LINKED</p>
      <h3>${esc(date)} proceedings</h3>
      <p><strong>${list(summary.meetings).length} meeting${list(summary.meetings).length===1?'':'s'} combined with meeting distinctions retained.</strong> ${substantive} substantive passage${substantive===1?'':'s'} entered topic synthesis; ${excluded} narrowly identified procedural or ceremonial passage${excluded===1?'':'s'} remained outside substantive claims.</p>
      ${summary.overview?`<p>${esc(summary.overview)}</p>`:''}
      <details open><summary>Meetings covered</summary><p>Each row preserves the source meeting. A topic that appears in several rows is combined at day level only when it maps to the same policy question.</p>${meetingRows(summary)}</details>
      <h4>Substantive topics</h4>
      <p class="method-note">Topics are ordered for navigation by descriptive coverage. Passage volume does not determine importance, consequence or agreement.</p>
      ${topics.length?topics.map(topic).join(''):'<p>No source-linked substantive topic met the local extraction rules. This does not establish that the meetings lacked substantive discussion.</p>'}
      <section aria-label="Consequential developments"><h4>Consequential developments across the day</h4><p>These items require explicit wording about an action, outcome or material change. They are evaluated separately from how often a topic appears.</p>${topDevelopments.length?`<ul>${topDevelopments.map(claim=>`<li><p><strong>${esc(claim.text)}</strong></p><details><summary>Supporting passage${evidenceItems(claim).length===1?'':'s'}</summary><ol>${evidence(claim)}</ol></details></li>`).join('')}</ul>`:'<p>No source-linked consequential development met the explicit cue rules.</p>'}${rawDevelopments.length-topDevelopments.length?`<p class="warning">${rawDevelopments.length-topDevelopments.length} unsupported development candidate${rawDevelopments.length-topDevelopments.length===1?' was':'s were'} withheld.</p>`:''}</section>
      <details><summary>Method, processing and data handling</summary>
        <p>${esc(method.summary||summary.method_summary||'The browser applies deterministic topic, synonym, sentence-role and consequence rules to the retained transcript text.')}</p>
        <ul>
          <li><strong>Processing:</strong> ${esc(method.processing||method.processing_location||'Local browser processing; no claim is displayed without a source-linked passage.')}</li>
          <li><strong>Backend:</strong> ${esc(method.backend||method.backend_requirement||(method.backend_required===false?'No summarization backend required.':'No summarization backend required.'))}</li>
          <li><strong>Data handling:</strong> ${esc(method.data_handling||'Transcript text remains in the browser unless the user explicitly saves or exports the briefing.')}</li>
          <li><strong>Topic boundaries:</strong> ${esc(method.topic_boundaries||'Synonyms can share one policy-question identifier; distinct measures retain separate identifiers.')}</li>
          <li><strong>Consequence:</strong> ${esc(method.consequence_rule||'Frequency is reported as coverage only. Consequential developments require explicit action, outcome or change language.')}</li>
        </ul>
        ${limitations.length?`<h4>Limits</h4><ul>${limitations.map(item=>`<li>${esc(item)}</li>`).join('')}</ul>`:''}
      </details>
    </section>`;
  }

  const api={render,safeURL,evidenceItems,supportedClaims};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else root.UNDaySummaryView=api;
})(typeof globalThis!=='undefined'?globalThis:this);
