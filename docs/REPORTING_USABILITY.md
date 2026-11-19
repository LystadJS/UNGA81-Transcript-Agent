# Reporting and campaign workflows: diplomat usability session

This guide prepares an actual user session for the [deployed reporting workspace](https://lystadjs.github.io/un/transcript-agent/meeting-reports.html). **No participant session has been completed through this guide.** Automated browser checks and assistant QA establish engineering behavior; they do not establish that diplomats can use or interpret it successfully.

Use the [reporting contract](MEETING_REPORTING.md) and [current capability matrix](CAPABILITIES.md) to identify the deployed version and remaining limits. Record the actual browser release, device, date and workflow-run references with each session. Do not treat a later release as tested by an earlier session.

## Preparation

Begin with synthetic material so the session requires no private archive access or real policy assessment. From the source repository root, create six JSON files: three source-validated reporting files, a matching hand-authored draft, a campaign notebook and a contact-only transfer:

```sh
node tools/reporting_usability.cjs --fixtures-only
```

This mode needs Node only. It prints a new temporary folder outside the repository.
The generated files use the production country registry and exclusion policy.

### Local facilitator session

For the inventory-addition task, the personal maintainer environment can launch
the actual application with an intercepted fictional inventory. Use the existing
QA browser harness; this adds no dependency to the government-browser application.
If that QA environment is not installed, set it up on the personal machine:

```sh
python -m pip install playwright==1.57.0
python -m playwright install chromium
export PLAYWRIGHT_MODULE="$(python -c 'import pathlib,playwright; print(pathlib.Path(playwright.__file__).parent / "driver" / "package")')"
node tools/reporting_usability.cjs
```

The default opens a visible browser. Use the printed files and the fictional date
**2026-11-10**. All transcript-service requests are intercepted locally; unknown
source paths and other external requests are blocked. Only the allowlisted public
build is served on loopback. A fictional-session banner and meeting titles identify
the material. Close the session tab to finish. Explicit downloads and the six
fixture files remain in the printed folder; repeated downloads are kept separately.
The temporary public build is removed.
The browser profile is temporary: device saves survive reloads within this session
and are discarded when it closes. Keep JSON/ZIP downloads for work you need later.
The tool does not record participant responses, screenshots or video. Explicit
downloads retain their contents, including any notes or draft text they contain.
The receipt contains browser/release/source-version information, timing and request/download
counts. Its participant-acceptance field always remains `not_recorded`; enter
actual observations separately in a private session record.

For unattended setup verification, use the same environment with
`node tools/reporting_usability.cjs --smoke`. This opens a headless browser,
rehearses source addition/export, matched draft review, separate Word/HTML copies,
campaign handoff, explicit follow-up dates and calendar/CSV/HTML copies, and network blocking, and writes an
`engineering_smoke` receipt. A passing smoke result is never a participant session.
The temporary folder uses POSIX mode 0700 and files 0600; protect downloads under
the host account's permissions on other platforms. Set `BROWSER_PATH` for an
existing compatible browser or `PYTHON` if the Python executable has another name.

This local Chromium session does not establish compatibility with an approved
work browser or its print/storage policies. Use `--fixtures-only` for file-based
tasks on that actual browser and record its version separately. A live local
session needs a graphical display; the automated smoke check does not. The
maintained-archive task remains a separate public-metadata exercise because this
local reporting session blocks external archive requests.

Give the participant the six generated files, clearly labeled **fictional test material**, and a place to save browser downloads. `synthetic-collection.json` contains four English segments in one synthetic meeting, two recorded country affiliations and one explicit collective statement. Begin the single-meeting tasks with this file. `synthetic-multi-meeting-report.json` adds a second synthetic meeting, for eight segments in total, and opens with both meetings selected. The fixture repeats its fictional wording across meetings; repetition is not evidence of policy importance or agreement. Use the two-meeting file for navigation after saving current work. For the source-addition task, use `synthetic-additional-report.json`: it contains only the second meeting and a distinct fictional assessment that should not enter the current report. It does not overlap the initial collection; the two-meeting file does, so it can demonstrate overlap refusal.

`synthetic-model-draft.json` pairs with the unchanged two-meeting report, whose
two briefing questions cover humanitarian access and an absent term. Save current
work, open `synthetic-multi-meeting-report.json` and prepare it before opening the
draft in **Personal model drafts (Python)**. The draft contains one hand-authored
collective-source example and an unanswered section. Its model name states
**SIMULATED REQUEST COUNT; NO MODEL INFERENCE**. The schema's request count of one
is simulated fixture metadata, not evidence of a model call. This material enables
source-context, separate Word/HTML and resume-file tasks before selecting model
hardware. The two questions and selected source scope must match; a later change
requires reopening the original pair or preparing a different draft.

The tool's metadata records `tool_model_inference: not_run`,
`bundled_draft: hand_authored_fictional` and
`participant_acceptance: not_recorded`. These describe this tool and its bundled
material; they do not attest activity in another program or factual quality.
The smoke run retains ten private downloads: two saved-report JSON copies,
a model-input packet, draft Word and draft HTML, then full campaign JSON,
contact-only JSON, contact CSV, follow-up ICS and complete campaign HTML. No
inference, Word/calendar-client import, participant answer or human acceptance
is created by that automated run.

`synthetic-campaign-notebook.json` is a separate, hand-authored fictional campaign:
one Kenya record, one reusable profile, one earlier conversation snapshot and a
follow-up on **2026-11-21**. `synthetic-contact-transfer.json` contains that same
profile, another Kenya profile and one United States profile. Its reviewed plan
adds two profiles, skips one identical ID and creates a United States record as
Not assessed with no follow-up date. It carries no campaign assessment, lead/status
fields or conversations. Names, addresses, candidate/body and notes are explicitly
fictional; neither file authenticates a person, voting eligibility or support.

The tool records `campaign_materials: hand_authored_fictional` and
`tool_calendar_client_import: not_run`. The latter describes this tool; actual
client import performed separately by a participant must be recorded privately.
The owner selected **Microsoft Edge and Outlook**. Exact Edge build, Outlook
edition/build, account type and managed policies remain unverified. Capture them
with the actual observations; mark unavailable client tasks not attempted. See the
[targeted rehearsal below](#edge-and-outlook-rehearsal).
For a government-browser file rehearsal, generate material on the personal
maintainer computer, transfer only these fictional files through a permitted
route and open the deployed app. Node/Python and the local harness are not
required on the government computer. Do not change local policy to run a task.

The fixture's source-shaped locators are provenance test data, not links to real statements; do not follow external transcript links during this exercise, including links in exported reading copies. The local “Read source context” control uses the loaded fictional passages and makes no source request. The preparation script validates the source bundles against the production country registry and reporting exclusion policy; it never reads private data, reserved sources or sealed tests.

For the separate archive-selection task, use permitted public metadata and stop before loading transcripts. A real-source extension can use an explicitly approved eligible meeting after checking availability; record its identity and source revision privately. Never use the 37 reserved meetings, either reserved date, sealed evaluation data or private pilot annotations for usability testing.

The owner may run a self-rehearsal; label it as owner testing, record prior familiarity and assistance, and do not call it independent acceptance. The participant should represent the intended diplomatic audience. Include the devices and accessibility needs that matter to actual users. A small convenience sample cannot establish population-wide usability. Do not substitute an assistant's answers for participant responses.

## Edge and Outlook rehearsal

The confirmed client family is Microsoft Edge with Outlook. This is a test target,
not an acceptance result. Record the operating system, Edge version/profile type,
Outlook edition/build (classic Windows, new Windows, web or another edition),
account type and calendar timezone privately. Do not infer them from the client
family or record account addresses in the public repository. The local automated
harness runs Chromium; it does not attest behavior in the managed Edge profile or
Outlook. Actual managed Edge and Outlook acceptance remains unrecorded.

### Edge file checks

Use the deployed app and the six fictional files generated on the personal
computer. No Node/Python installation is required on the government computer.
Identify the current destination in Edge's **Settings > Downloads**; on Windows,
`Ctrl+J` opens the Downloads panel. Verify that each requested JSON, HTML, Word or
calendar file actually appears and can be reopened before closing current work.
A download-start message alone is not proof that the file was retained. Record
blocked downloads and any missing controls without changing managed protections.
These navigation instructions follow Microsoft's [download-location guide](https://support.microsoft.com/en-us/edge/find-where-your-browser-is-saving-downloads)
and [keyboard-shortcut reference](https://support.microsoft.com/en-us/edge/keyboard-shortcuts-in-microsoft-edge), checked 19 November 2026.

### Short campaign/calendar pass

1. Open `synthetic-campaign-notebook.json` in the campaign notebook. Add a fictional
   campaign note. Import `synthetic-contact-transfer.json`, cancel once, then review
   and add its two new profiles. Confirm the existing note/history survives and the
   new United States record is Not assessed, with no inferred vote or follow-up.
2. Explicitly give that United States record the fictional date **22 November
   2026**, Apply the country form and save full notebook JSON. Reopen it to check
   both records and dates. The Kenya fixture already has **21 November 2026**.
3. Narrow the list to Kenya. In **Calendar copy of country follow-ups**, leave the
   cutoff empty and country notes unchecked, then download the `.ics` file. It
   should still contain two all-day entries on those exact dates. Use the Outlook
   route below that matches the actual client and account. The app's download is
   a local calendar snapshot, not a subscription URL.
4. Inspect the imported calendar: two entries on November 21 and 22, readable
   country/campaign titles and line breaks, no date shift, and no lead/profile,
   conversation or campaign-assessment fields. Record the actual visibility,
   busy/free display and alerts rather than assuming the private/transparent file
   flags control the client. Optional country notes/references can contain private
   text; test them separately with fictional material if needed.
5. Record whether a repeated import creates duplicates and whether later notebook
   edits leave the imported copy unchanged. Keep full notebook JSON to resume
   work. Use only an already permitted test calendar/destination; record a refused
   or unavailable import as not attempted/blocked, not as successful compatibility.
   Do not publish or share the calendar as part of this rehearsal.

The dates are fictional and remain those dates even if the session occurs later.
No live meeting, invitation, automatic reminder or calendar synchronization is
created by the app. Outlook may apply its own defaults; actual observations are
required before claiming client acceptance.

### Outlook file-import routes

These are Microsoft's documented routes, checked 19 November 2026, not actions
performed by this tool. Use the matching edition; other editions need their own
current documented route and actual results. If a managed account lacks the
feature, record that outcome rather than switching account or weakening policy.

| Actual client | Documented route and boundary |
| --- | --- |
| Classic Outlook for Windows | Use **File > Open & Export > Import/Export**, select **Import an iCalendar (.ics) or vCalendar file (.vcs)** and choose the downloaded file. **Open as New** allows inspection as a separate imported calendar. Microsoft documents this file-import sequence in its [classic Outlook instructions](https://support.microsoft.com/en-us/outlook/calendar/see-your-google-calendar-in-outlook). This app already supplies the `.ics`; no Google export/subscription step is needed |
| New Outlook for Windows | Use **Calendar > Add calendar > Upload from file**, browse to the `.ics`, choose the intended calendar and import. Microsoft's [new Outlook instructions](https://support.microsoft.com/en-us/outlook/sharing/share-an-outlook-calendar-as-view-only-with-others) restrict this import to Microsoft 365 Exchange accounts. Confirm the actual account/build and available controls; do not assume all Outlook accounts support the route |
| Outlook on the web | Use its file-upload calendar import, choose the downloaded `.ics` and the intended destination calendar. Follow the work/school section of Microsoft's [web import guide](https://support.microsoft.com/en-us/outlook/import-or-subscribe-to-a-calendar-in-outlook-com-or-outlook-on-the-web). Importing is a snapshot; the app supplies no subscription endpoint and later notebook changes do not update that copy |

Record the actual edition and results, including any refusal, duplicates, date or
text problems and assistance. Microsoft also distinguishes capabilities across
[Outlook editions](https://support.microsoft.com/en-us/outlook/getstarted/feature-comparison-between-new-outlook-and-classic-outlook);
shared branding is not evidence that every import path behaves identically.
The existing report-review calendar is a separate one-event task; inspect it
separately after the campaign pass. Word rendering, Edge print/PDF and device-save
behavior retain their own tasks below and are not established by calendar import.

## Task script and observation criteria

Read the task prompt without first explaining the controls. Record assistance and misunderstandings before correcting them. Tasks are not scored as independent completion after the facilitator supplies the route or answer.

| Task prompt | What the facilitator observes |
| --- | --- |
| Find a meeting in the maintained archive and prepare it for reporting. Stop before loading a transcript. | The participant can find metadata, select the intended identity, recognize the inventory-check step and explain that opening the report workspace has not downloaded its transcript. Missing or unavailable meetings are understood as gaps. |
| Open the fictional collection and describe what material is available. | One loaded meeting and four English source segments are recognized. Recorded country affiliations are not treated as verified individual identities, complete speeches or accepted stance estimates. |
| Find passages about humanitarian access, then include one in a mission briefing appendix. | The participant can search, select a passage and recover it after changing the query. They understand that the appendix subset does not change the whole-meeting overview, country table or four-segment denominator. |
| Add all matching passages to the appendix, remove them, then undo. Change a note and explain what undo restores. | The participant understands counts across all matches, the switch to explicit selected passages, retention of other choices and notes, and the need to prepare exports again. Where more than one results page is available, they check that unseen matches are included. They understand that manual choices or source/meeting changes clear undo and that it is not saved in JSON. Record assistance. |
| Jump to a recorded affiliation in the prepared report, read its comparison coverage, and return to the index. | The participant finds the affiliation without filtering the report, uses keyboard or pointer navigation, and understands that every affiliation and source gap remains present. Repeat in a standalone HTML reading copy, Word or PDF when that environment is available. They distinguish a source label from verified national capacity. Record assistance and export-specific problems. |
| Narrow the passage list to one recorded country affiliation, then to a speaker name. Clear the filters and explain what the prepared report contains. | The participant combines exact metadata choices with word search, recognizes zero matches, and understands that an affiliation can include collective statements and a name is not verified personal identity. Clearing preserves appendix choices and notes; filtering leaves mandatory country coverage and the full CSV intact. |
| Explain what the collective statement tells us about a national position. | The participant recognizes the stated group capacity and does not convert its expression into a national stance because the recorded affiliation is Kenya. A missing eligible extract is not described as neutrality. |
| In a prepared report, inspect the source context for a country expression, then return to your report. | The participant finds “Read source context” in the country table, recognizes the selected passage and its immediate neighbors, and keeps each speaker's words and recorded capacity separate. Missing context is not treated as source completeness. Keyboard opening, Escape and focus return are observed without coaching; the report and appendix choices remain intact. |
| Add a short interpretation to one passage, prepare the report and download a passage-notes spreadsheet. | The participant distinguishes their interpretation from the quotation and model results, identifies the source pointers in the CSV, and understands that the full evidence CSV excludes notes. They recognize selected-meeting scope, formula-prefix escaping and the need to save JSON/ZIP to resume. Record actual spreadsheet-client rendering and assistance separately. |
| Arrange two briefing-question sections in your preferred order using only the keyboard, then save and reopen mission preferences. Move an unfinished question once. | The participant can use the numbered positions and Move up/down buttons, understands disabled boundaries and focus return, and retains unfinished text. Prepared output and reopened preferences keep the order after the mandatory country overview. They distinguish Checking, applied and current-settings-kept import messages; any naturally observed delayed-read behavior is recorded separately from automated race tests. They recognize that queries remain literal searches, moves invalidate exports, and nothing is saved automatically. Record assistance and comprehension separately. |
| Save your current work, open the original fictional two-meeting report and prepare it. Open its matching fictional draft, inspect the cited context and save separate Word/HTML reading copies and files to resume later. | The participant recognizes hand-authored material, a simulated request count, the unanswered section and collective capacity. They distinguish exact quotation matching from claim support and retain original report JSON plus draft JSON. They understand Word edits cannot be imported and ordinary exports exclude the draft. Record actual Word-client rendering separately from XML checks, assistance separately from unaided completion, and any observed scope-mismatch refusal separately from model quality. No model installation is required. |
| Optional, with an authorized personal model setup: export a fictional question packet, generate a new draft on the personal computer and review it beside its report. | Record the actual runtime/model revision, hardware and inference location separately from the bundled fixture. The participant understands the browser makes no model request and loopback does not attest local inference. Review factual support, omissions, attribution and citation correctness separately. Skip and mark not run when no model setup is available; fixture/transport checks cannot substitute for actual model acceptance. |
| Save your work so you can continue tomorrow; also save preferences for a different meeting. | Report JSON, or a report package containing it, is chosen to preserve the collection, appendix and notes. Mission-preferences JSON is understood to contain only reusable settings. A reopened report retains the source and notes, and needs preparation to rebuild its preview. |
| Export a report for reading and the evidence for analysis. Explain what each contains. | The participant uses the Save work to reopen, Read or share, and Evidence spreadsheets groups. HTML is recognized as a readable report, JSON as source-bound saved work, and CSV as all four source segments from the selected meeting. Search, appendix choices and analyst notes do not narrow or alter the CSV. Participants recognize potentially sensitive contents before sharing files. |
| Print the report or save a PDF using your normal work browser. Cancel once, then return and prepare a PDF. | The participant finds the native destination, checks the complete appendix and source links, distinguishes cancellation from a saved file and can return to the workspace if its print controls need resetting. They understand that PDF does not replace JSON/ZIP for resuming work. Record the actual browser, print policy, destination, clipping or pagination problems and assistance. |
| Schedule a personal review date for this report and export a calendar entry. Explain what will be imported. | The participant chooses their own date independently of source dates, recognizes the all-day event and optional assessment, and checks date/visibility/alerts in an approved calendar client if available. They understand that ICS does not resume report editing and that JSON/ZIP must be saved separately. Record actual client/version/import behavior; defer client acceptance where unavailable. |
| Download a Word copy and explain how you would continue editing tomorrow. | The participant opens the `.docx` in their actual Word environment, checks headings, country tables, source links, line breaks and notes, and recognizes that Word edits cannot be imported here. They save JSON or ZIP separately to reopen source-verified work. Record the actual Word version, rendering problems and any assistance. |
| Download a report package, inspect its files, and use it to resume editing. | The participant opens the original ZIP directly in the workspace, checks retained notes and selections, and prepares the rebuilt report. They can also extract it to read report.html and identify the full evidence CSV, JSON and field guide. They recognize that JSON retains all loaded source bundles, including unselected meetings, and that the package is unencrypted and may contain analyst notes. Checksums are understood as file-integrity evidence, not proof of speaker identity or policy truth. A package refused for size does not erase current work. |
| Change an appendix choice or note after preparing a report. | Disabled stale exports are understood; the participant prepares the report again. Removing a meeting and its notes is not mistaken for deleting the canonical warehouse archive. |
| Keep your assessment, find another fictional meeting in the inventory and add its transcript. Cancel once, then complete the addition. | The participant distinguishes Add selected transcripts from Load's replacement, checks retained notes and unchecked sources, prepares again and saves JSON/ZIP. A failed or incomplete multi-meeting retrieval is understood to add nothing. Use the local facilitator session above, which supplies the synthetic inventory; defer this task on the public production inventory. Never request reserved meetings. Record assistance and unintended loss. |
| Keep your current assessment and appendix, then add sources from a nonoverlapping fictional saved file. Explain what was added. | The participant chooses Add sources rather than Open, recognizes retained current notes/settings and excluded incoming report annotations, checks new versus unchecked meetings and prepares again. They understand that all loaded source bundles are saved, an overlap/revision is refused without replacement, and addition is not automatic saving. Record confusion and assistance. |
| Remove one loaded source collection after checking the listed meetings and annotations. Keep it once, then confirm removal. | The participant distinguishes unchecking from reducing saved source data, understands whole-bundle removal and the special warning for clearing the last collection's assessment, checks retained notes and settings, and prepares again. Existing downloaded files and device copies are understood to be separate. Record assistance and unintended loss. |
| Save reusable preferences with your normal headings and, if available, a long Unicode example. Reopen the file. If downloads are blocked by the work browser, explain the message and keep the current work open. | Exported preferences reopen within 8 KiB; a size refusal preserves every field and directs shortening. A blocked download is not mistaken for saved work, and JSON/ZIP download failures keep replacement protection active. Record actual browser/policy behavior; do not simulate a policy failure and call it government-browser acceptance. |
| With an unsaved assessment, try opening the other fictional report. Keep the current work, then save it and deliberately replace it. | The participant recognizes the replacement choice, can use “Keep current report” or Escape, and confirms that notes, appendix and prepared exports remain intact. They save report JSON before replacing, understand that fresh collection clears source-bound notes, and do not mistake a warning for automatic saving. Source requests have not occurred merely because an imported file was checked. |
| Save your current work, then open the fictional two-meeting report and prepare it. Go directly to the second meeting and back to the meeting list. Repeat in the downloaded HTML. | Both dated meeting titles and their four-segment counts are recognized. The participant uses the index and return links with visible keyboard focus and distinguishes a collection outcome from completeness or policy importance. The HTML links work without application controls; the full CSV contains all eight selected-meeting segments. Opening the new report is understood to replace the current local workspace, not merge its notes. |
| In the two-meeting report, follow one country's dated expressions and find the matching U.S. wording at each meeting. Explain a comparison gap. | The participant finds the automatic country overview without selecting a country, uses its dated links/context, and distinguishes same-object wording from policy agreement. They understand collective/source gaps, no carry-forward, same-date title ordering and why different extracts do not establish a verified policy change. Filtering passages leaves the overview intact. |
| Explain whether this report establishes official government policy, a vote, a current stance or an accepted neural-model prediction. | The participant recognizes dated source-linked extracts, uncertainty and withheld model coverage. They do not infer policy agreement from similar language or a current position from an older observation. |

Observe keyboard-only navigation, visible focus, readable tables and mobile layout where relevant. Record actual task time as context, not as a fabricated performance target. Do not coach a participant and later report the same attempt as unaided success.

## Campaign rehearsal

Use a separate short session or select the tasks relevant to the participant;
do not require the complete reporting table and this table in one sitting. Save
current report work first, then use **Campaign notebook**. Begin with the unchanged
fictional notebook so the transfer's identical-ID example remains reproducible.
Dates are fictional scheduling fields; a past date is not rescheduled automatically.

| Task prompt | What the facilitator observes |
| --- | --- |
| Open the fictional campaign notebook. Explain what is recorded and what it establishes. | One geographic record, a current Contacted status, one reusable profile, an earlier interaction and a November 21 follow-up are recognized. The registry is not treated as an electorate, identity verification or proof of a ballot. |
| Add a campaign assessment, then import the contact-only transfer. Keep it once, inspect the preview and add it. Save files for resuming work and for handing off only contacts. | The participant distinguishes Apply from JSON saving and full notebook from contact-only JSON. Two additions and one identical-ID skip leave current notes/status/history intact. The new United States record is Not assessed, not neutral or verified eligible. Contact notes are recognized as included in the transfer. Nothing is assumed uploaded, authenticated or synchronized. |
| Edit the newly added Kenya profile, copy it into lead or new-interaction fields, and add a dated conversation. Apply and save the country record. Explain what changes in the earlier snapshot. | Keep/confirmation before replacing populated fields is understood. Earlier conversations remain independent, and profile edits do not automatically update lead fields, older snapshots or status counts. Added interaction fields, applied country form and saved JSON are distinguished. If the original transfer is retried after changing its same-ID profile, conflict refusal is understood as preserving current work, not a partial update. |
| Give the United States record a fictional follow-up on November 22. Filter the list to Kenya, then download contact CSV, complete HTML and a calendar copy. | The participant recognizes complete exports despite a narrower list. The calendar has two explicitly entered all-day dates and ignores list filters; an optional calendar cutoff is separate. Country notes/references are opt-in, and lead/profile/log/campaign-note fields are excluded. ICS is not a notebook save or synchronization. |
| If permitted and available, import the fictional calendar copy into the actual work client. Inspect dates, visibility and alerts; explain what a repeated import or later notebook edit would do. | Record browser/client/version, permitted import route, exact November dates, duplicate behavior, private/transparent handling, default alerts, any refusal and assistance. Do not treat a synthetic download or RFC parse as client acceptance. The tool supplies no invites/alarms and does not update/delete imported events. Mark not attempted where the client or policy does not permit this task. |

For contact CSV, Word, print and calendar copies, record actual client rendering
separately. Use only fictional data in transferred files. If a participant adds
identifying or mission-specific notes, their explicit downloads become private
session material; the tool does not redact them. Keep observed failures and
assistance in the record rather than replacing them with automated test results.

## Private session record

Keep completed session records, participant identities, mission details, notes and any source-bearing screenshots in authorized private storage. Do not commit them to the code repository or public mirror. A source-free engineering summary may reference a private record identifier and report aggregate task outcomes.

For each actual session, record:

- Pseudonymous session identifier, date, release, browser/device and relevant accessibility setup; keep identity mapping separate.
- Material type (`synthetic` or approved real source), setup success and any source/version reference in the private record.
- Per task: `not_attempted`, `completed_independently`, `completed_with_assistance` or `not_completed`; elapsed time if measured; assistance given; observed interpretation errors.
- Separate comprehension results for source versus analyst note, collective versus national capacity, neighboring speaker versus selected speaker, loaded coverage versus completeness, keeping current work versus saving it, no evidence versus neutrality, full CSV versus appendix subset, all loaded saved sources versus selected report meetings, checksums versus source authentication, and provisional extracts versus accepted model estimates.
- Separate campaign comprehension results: staged versus applied versus saved work, profile copies versus live links, contact-only versus full files, conflict refusal versus partial update, Not assessed versus neutrality/eligibility, list filters versus complete exports, and calendar reading copy versus synchronization/client alerts.
- Concrete defect or usability issue, reproduction steps stripped of private content, proposed repair and whether retesting is needed.
- The owner's explicit release/usability decision and its scope after reviewing the actual evidence. Leave this unset until that decision occurs.

Report the number and nature of participants and tasks attempted, including incomplete attempts. Do not erase assisted or failed attempts after a repair; record the retest separately. Any observed confusion that could turn a collective statement, analyst note or missing evidence into an asserted government stance requires a documented repair or explicit unresolved limitation before claiming usability acceptance.

This session cannot establish model precision, retrieval recall, statistical validity, account-wide storage capacity or fourteen days of scheduled service. Those retain their separate acceptance records and gates.
