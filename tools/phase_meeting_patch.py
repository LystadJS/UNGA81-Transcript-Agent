"""One-time source-only integration patch on the feature branch."""
from pathlib import Path
import os
if os.environ.get('GITHUB_REF_NAME')!='feat/latent-comparison-phase-a':raise SystemExit('Wrong branch')
def patch(file,old,new):
 p=Path(file);text=p.read_text();assert text.count(old)==1,(file,old);p.write_text(text.replace(old,new))
patch('tools/test_latent_ui.cjs',"chromium.launch({headless:true})","chromium.launch({headless:true,...(process.env.PW_CHANNEL?{channel:process.env.PW_CHANNEL}:{})})")
patch('site/latent-core.js',"const ids=new Set();\n    for(const e of result.entries)","const checkCounts=c=>assert(c&&['input','eligible_before_dedup','duplicates','eligible','matched'].every(k=>Number.isSafeInteger(c[k])&&c[k]>=0),'Invalid saved source counts.');\n    checkCounts(result.counts);\n    const ids=new Set();\n    for(const e of result.entries)")
patch('site/latent-core.js',"const by=new Map(e.result.matched.map(r=>[r.id,r]));assert(by.size===e.result.matched.length,'Duplicate saved passage identity.');","checkCounts(e.result.counts);\n      const by=new Map(e.result.matched.map(r=>[r.id,r]));assert(by.size===e.result.matched.length,'Duplicate saved passage identity.');")
patch('site/collector.js',"    if (!Scopes.isValid(p.scope)) throw Error('Invalid meeting scope.');","""    if (!Scopes.isValid(p.scope)) throw Error('Invalid meeting scope.');
    if (p.meeting_slug !== undefined && (typeof p.meeting_slug !== 'string' || !/^asset\\/[A-Za-z0-9_-]+\\/[A-Za-z0-9_-]+$/.test(p.meeting_slug) || p.start !== p.end || p.meeting_date !== p.start || !/^\\d{4}-\\d{2}-\\d{2}$/.test(p.start) || !Number.isFinite(Date.parse(p.start)) || new Date(p.start).toISOString().slice(0,10)!==p.start)) throw Error('Select one meeting on one valid date.');
    const matchesSelection = meeting => Scopes.matchesMeeting(meeting, p.scope) && (!p.meeting_slug || meeting.slug === p.meeting_slug);""")
patch('site/collector.js',"found.filter(meeting => Scopes.matchesMeeting(meeting, p.scope)).length","found.filter(matchesSelection).length")
patch('site/collector.js',"const selected = meetings.filter(meeting => Scopes.matchesMeeting(meeting, p.scope));","""const selected = meetings.filter(matchesSelection);
    if(p.meeting_slug && (inventoryDays.some(d=>d.status!=='ok') || selected.length!==1)) throw Error('The selected meeting could not be verified in the complete inventory. Search the date again; no other meeting was substituted.');""")
patch('site/collector.js',"id: meeting.slug + '#' + segmentIndex,","id: meeting.slug + '#' + segmentIndex,\n            meeting_slug: meeting.slug,")
patch('site/collector.js',"selected_meetings: selected.length,","""selected_meetings: selected.length,
        ...(p.meeting_slug?{selection_mode:'single_meeting',selected_meeting_slug:p.meeting_slug,selected_meeting_title:selected[0].title,selected_meeting_date:p.meeting_date}:{}),""")
patch('site/analysis-core.js',"    const clustering = p.methods.includes('clusters') ? ClusterOptions.options(p.clustering) : undefined;","""    if(p.meeting_slug!==undefined && (typeof p.meeting_slug!=='string'||!/^asset\\/[A-Za-z0-9_-]+\\/[A-Za-z0-9_-]+$/.test(p.meeting_slug)||p.start!==p.end||p.meeting_date!==p.start)) throw Error('Individual meeting analysis requires one valid meeting ID and its exact date.');
    const clustering = p.methods.includes('clusters') ? ClusterOptions.options(p.clustering) : undefined;""")
patch('site/analysis-core.js',"      Scopes.matchesRecord(record, p.scope) &&","      Scopes.matchesRecord(record, p.scope) &&\n      (!p.meeting_slug || (record.meeting_slug || record.id.split('#')[0]) === p.meeting_slug) &&")
patch('site/analysis-ui.js',"        .map(input => input.value)\n    });","        .map(input => input.value),\n      ...(window.UNMeetingPicker?.selection() || {})\n    });")
patch('site/analysis-ui.js',"    if(report.passage_selection)html+=", "    if(report.collection?.selection_mode==='single_meeting')html+=`<p class=\"method-note\"><strong>Individual meeting:</strong> ${esc(report.collection.selected_meeting_title)} · ${esc(report.collection.selected_meeting_date)} · ${esc(report.collection.selected_meeting_slug)}. Only this meeting was collected. Within-meeting passages do not supply independent meeting-level replication.</p>`;\n    if(report.passage_selection)html+=")
patch('site/analysis-ui.js',"      updateNMFControls();\n    }\n  };","      updateNMFControls();\n      window.UNMeetingPicker?.refresh();\n    }\n  };")
patch('site/index.html',"    <script defer src=\"analysis-ui.js?v=1.11.0\"></script>","    <script defer src=\"meeting-picker-core.js?v=1.12.0\"></script>\n    <script defer src=\"meeting-picker.js?v=1.12.0\"></script>\n    <script defer src=\"analysis-ui.js?v=1.12.0\"></script>")
for file in ['site/index.html','site/analysis-core.js','site/analysis-ui.js','site/cluster-worker.js','site/nmf-worker.js']:
 p=Path(file);p.write_text(p.read_text().replace('1.11.0','1.12.0'))
p=Path('site/analysis.css');p.write_text(p.read_text()+'''\n/* Individual-meeting discovery, using the existing report typography. */
.meeting-picker{margin:0 0 1.5rem;padding:1rem;border:1px solid #ccd5df;border-radius:4px;min-width:0}
.meeting-picker legend{font-weight:700;padding:0 .4rem}
.meeting-picker-actions{display:flex;gap:.5rem;align-items:end;flex-wrap:wrap}
.meeting-picker select{width:100%;max-width:100%}
#selectedMeetingInfo{overflow-wrap:anywhere}
.meeting-picker [hidden]{display:none!important}
@media print{.meeting-picker{display:none}}
''')
print('Integrated single-meeting source filtering, inventory metadata, exports, cache versions and controls; numerical kernels and D1 unchanged.')
