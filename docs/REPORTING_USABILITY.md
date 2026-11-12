# Meeting reporting: diplomat usability session

This guide prepares an actual user session for the [deployed reporting workspace](https://lystadjs.github.io/un/transcript-agent/meeting-reports.html). **No participant session has been completed through this guide.** Automated browser checks and assistant QA establish engineering behavior; they do not establish that diplomats can use or interpret it successfully.

Use the [reporting contract](MEETING_REPORTING.md) and [current capability matrix](CAPABILITIES.md) to identify the deployed version and remaining limits. Record the actual browser release, device, date and workflow-run references with each session. Do not treat a later release as tested by an earlier session.

## Preparation

Begin with synthetic material so the session requires no private archive access or real policy assessment. A maintainer can create an original-bound collection from the existing test fixture without making network requests:

```sh
node - <<'JS'
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const fixture = require('./tests/meeting_report_fixture.cjs');
const Collector = require('./site/collector.js'), Report = require('./site/meeting-report-core.js');
(async () => {
  const countries = JSON.parse(fs.readFileSync('site/countries.json'));
  const policy = JSON.parse(fs.readFileSync('site/reporting-exclusions.json'));
  const meeting = fixture.meetings[0];
  const request = async url => {
    const pathname = new URL(url).pathname;
    if (!pathname.endsWith('/meetings.json') && pathname !== '/en/' + meeting.slug + '.json') throw Error('Unexpected fixture request');
    const data = pathname.endsWith('/meetings.json')
      ? {meetings: fixture.meetings, page: 1, total: 2, hasMore: false}
      : fixture.transcript(meeting);
    const raw = JSON.stringify(data);
    return {data, raw, hash: await Collector.sha(raw), retrieved_at: new Date().toISOString()};
  };
  const corpus = await Collector.collect({start: fixture.date, end: fixture.date, scope: 'all', meeting_slug: meeting.slug, meeting_date: fixture.date}, countries, {request});
  await Report.validateCorpora([corpus], policy, countries);
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'un-reporting-usability-'));
  const file = path.join(folder, 'synthetic-collection.json');
  fs.writeFileSync(file, JSON.stringify(corpus), {mode: 0o600});
  console.log(file);
})().catch(error => { console.error(error.message); process.exitCode = 1; });
JS
```

Run this from the source repository root. Give the participant the generated file, clearly labeled **fictional test material**, and a place to save browser downloads. It contains four English segments in one synthetic meeting, two recorded country affiliations and one explicit collective statement. The fixture's source-shaped locators are provenance test data, not links to real statements; do not use them as real evidence or follow them during this exercise.

For the separate archive-selection task, use permitted public metadata and stop before loading transcripts. A real-source extension can use an explicitly approved eligible meeting after checking availability; record its identity and source revision privately. Never use the 37 reserved meetings, either reserved date, sealed evaluation data or private pilot annotations for usability testing.

The participant should represent the intended diplomatic audience. Include the devices and accessibility needs that matter to actual users. A small convenience sample cannot establish population-wide usability. Do not substitute an assistant's answers for participant responses.

## Task script and observation criteria

Read the task prompt without first explaining the controls. Record assistance and misunderstandings before correcting them. Tasks are not scored as independent completion after the facilitator supplies the route or answer.

| Task prompt | What the facilitator observes |
| --- | --- |
| Find a meeting in the maintained archive and prepare it for reporting. Stop before loading a transcript. | The participant can find metadata, select the intended identity, recognize the inventory-check step and explain that opening the report workspace has not downloaded its transcript. Missing or unavailable meetings are understood as gaps. |
| Open the fictional collection and describe what material is available. | One loaded meeting and four English source segments are recognized. Recorded country affiliations are not treated as verified individual identities, complete speeches or accepted stance estimates. |
| Find passages about humanitarian access, then include one in a mission briefing appendix. | The participant can search, select a passage and recover it after changing the query. They understand that the appendix subset does not change the whole-meeting overview, country table or four-segment denominator. |
| Explain what the collective statement tells us about a national position. | The participant recognizes the stated group capacity and does not convert its expression into a national stance because the recorded affiliation is Kenya. A missing eligible extract is not described as neutrality. |
| Add a short interpretation to one passage and prepare the report. | The participant can find the note editor and distinguish the original quotation from their own note. They understand that their note does not become a model result or source statement. |
| Save your work so you can continue tomorrow; also save preferences for a different meeting. | Report JSON is chosen to preserve the collection, appendix and notes. Mission-preferences JSON is understood to contain only reusable settings. A reopened report retains the source and notes, and needs preparation to rebuild its preview. |
| Export a report for reading and the evidence for analysis. Explain what each contains. | HTML is recognized as a readable report, JSON as source-bound saved work, and CSV as all four source segments from the selected meeting. Search, appendix choices and analyst notes do not narrow or alter the CSV. Participants recognize potentially sensitive contents before sharing files. |
| Change an appendix choice or note after preparing a report. | Disabled stale exports are understood; the participant prepares the report again. Removing a meeting and its notes is not mistaken for deleting the canonical warehouse archive. |
| Explain whether this report establishes official government policy, a vote, a current stance or an accepted neural-model prediction. | The participant recognizes dated source-linked extracts, uncertainty and withheld model coverage. They do not infer policy agreement from similar language or a current position from an older observation. |

Observe keyboard-only navigation, visible focus, readable tables and mobile layout where relevant. Record actual task time as context, not as a fabricated performance target. Do not coach a participant and later report the same attempt as unaided success.

## Private session record

Keep completed session records, participant identities, mission details, notes and any source-bearing screenshots in authorized private storage. Do not commit them to the code repository or public mirror. A source-free engineering summary may reference a private record identifier and report aggregate task outcomes.

For each actual session, record:

- Pseudonymous session identifier, date, release, browser/device and relevant accessibility setup; keep identity mapping separate.
- Material type (`synthetic` or approved real source), setup success and any source/version reference in the private record.
- Per task: `not_attempted`, `completed_independently`, `completed_with_assistance` or `not_completed`; elapsed time if measured; assistance given; observed interpretation errors.
- Separate comprehension results for source versus analyst note, collective versus national capacity, no evidence versus neutrality, full CSV versus appendix subset, and provisional extracts versus accepted model estimates.
- Concrete defect or usability issue, reproduction steps stripped of private content, proposed repair and whether retesting is needed.
- The owner's explicit release/usability decision and its scope after reviewing the actual evidence. Leave this unset until that decision occurs.

Report the number and nature of participants and tasks attempted, including incomplete attempts. Do not erase assisted or failed attempts after a repair; record the retest separately. Any observed confusion that could turn a collective statement, analyst note or missing evidence into an asserted government stance requires a documented repair or explicit unresolved limitation before claiming usability acceptance.

This session cannot establish model precision, retrieval recall, statistical validity, account-wide storage capacity or fourteen days of scheduled service. Those retain their separate acceptance records and gates.
