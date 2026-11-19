# Current capability and acceptance matrix

Updated 19 November 2026, UTC. **Release 1.85.0 is deployed and verified at both
public URLs.** All 201 preferred-site canonical files and all four changed
original-site assets match expected hashes. All four campaign browser suites pass
live at both URLs, including opt-in Current/Incoming profile-update review.
Source #370 passed numerical, browser and contract checks, including sixteen
reporting workflows and four campaign suites; website #201 passed audit and
regression before merge. The unchanged Python suite has 264 tests; all 2,077
retained package checksums and the 209-entry public build pass. Earlier live
reporting and clipboard receipts retain their original scope in the linked
checkpoint. Actual client/OS/Outlook acceptance remains unverified; managed testing
is deferred. The separate acquisition/model-CI approval remains pending.

Campaign follow-ups reuse the report calendar writer without a new runtime file,
dependency, backend, model weight or Hugging Face storage. Calendar copies are
not synchronized; clients control imports, visibility, alerts and duplicates.
These are fictional-data engineering checks, not actual calendar-client, model
quality, desktop Word, government-browser policy or diplomat acceptance. Full
DiploTools parity remains unestablished. See the [current checkpoint](OVERNIGHT_WORK.md).

Managed Edge and Outlook testing is deferred at the owner's request. Development
continues without treating that deferral as client acceptance. Release 1.82.0 adds
a view-only campaign follow-up queue: earliest follow-up/latest logged interaction
ordering, dated/undated filters, missing dates last and alphabetical ties. Existing
full exports and v3 saves retain all records; no runtime files, dependencies,
models or Hugging Face storage are added.

## Reporting and execution

| Capability | Available implementation | Boundary / acceptance |
| --- | --- | --- |
| Campaign outreach notebook | Campaign details, one current lead/status row per place, reusable contact profiles, dated interaction snapshots, explicit 1 MiB v3 JSON save/reopen (v1/v2 readable), complete country/contact/interaction CSV and script-free HTML | Manual unverified records. Registry is not an electorate; support is not an actual vote/prediction. No account, automatic storage/history, messages or shared CRM. Copies remain independent; actual usability/client acceptance outstanding |
| Reviewed contact transfer | Contact-only JSON export and grouped add preview; default same-country/ID conflict refusal, opt-in Current/Incoming field-change review, identical pairs skipped and complete-state limits enforced atomically | Includes complete contact notes; excludes campaign assessments, leads/statuses and conversations. No name-based identity merging, authentication or synchronization. Dirty/stale and per-control file guards preserve work |
| Campaign follow-up calendar | Explicit all-day ICS for every dated country record, optional cutoff and opt-in country notes/references, independent of list filters; 1 MiB encoded bound | Lead/profile fields, conversations and campaign notes excluded. No dates, invitations or alarms invented. Options reset on New/Open; dirty/stale guards and module isolation. No synchronization; actual client import/visibility/alerts/duplicates need acceptance |
| Campaign editable Word briefing | Complete browser-generated `.docx` copy of campaign notes, country records, profiles and interaction logs, independent of filters; reuses report Word/ZIP writers | 1 MiB whole-file bound without truncation; JSON required to resume. Optional modules fail separately; stale edits/source operations and pending fields preserve work. No desktop Word acceptance |
| Meeting-first reporting | Explicit selected English-source loading; mission briefing, negotiation record and evidence digest; literal evidence search; source context; passage notes and selected appendices | Up to five meetings per load. Reports preserve country-expression coverage and visible comparison gaps. Actual diplomat usability acceptance remains outstanding |
| Remove loaded sources | Whole original collections with meeting/note/appendix impact confirmation, JSON byte counts, selective annotation pruning and stale-decision refusal | Keep and Escape preserve work; last removal explicitly clears the current assessment. Kept bytes, mission settings, downloaded files and device copies stay intact. No new dependencies or source requests |
| Open report-package ZIP | Direct local reopening or source addition from original five-file uncompressed packages; ZIP structure, CRC/SHA-256 and manifest checks precede source revalidation | Imported HTML is never executed; derived reports rebuilt. Keep/Replace and stale-operation protection apply. ZIPs outside this format require extracted JSON; checksums do not authenticate a source |
| Add inventory transcripts | Explicit all-or-nothing retrieval of up to five new meetings into the current report, retaining sources, notes, appendix, questions and existing selections | Overlap/capacity/policy preflight; source and complete-state byte validation; cancellation, incomplete retrieval, newer edits/operations keep current work. Separate Load action retains replacement semantics |
| Add saved sources | Atomic addition of verified collection/report sources while keeping current settings, notes, appendix and selections; incoming report annotations are excluded | Refuses all meeting overlap/revisions, reserved/corrupt files, stale operations and oversized combined saved JSON. All loaded source bundles are retained; new exports require preparation. No source requests or schema change |
| Cross-meeting country overview | Automatic dated rows for every recorded affiliation, source/collective gaps and exact displayed-object U.S. extracts from the same meeting; matched U.S. wording also appears in individual tables | Reuses existing provisional extracts. No carry-forward, agreement score, verified policy-change claim or repeated-quote weighting. Original sources and full CSV remain unchanged |
| Passage-note spreadsheet | Separate source-bound CSV of analyst notes in prepared selected meetings, with interpretation labels, source identities/hashes and formula escaping | Excludes transcript text and report assessment; independent of search/appendix. Existing full evidence CSV unchanged. Reading/follow-up copy outside ZIP; JSON/ZIP needed to resume. Actual spreadsheet-client acceptance outstanding |
| Calendar review entry | User-scheduled all-day ICS copy of a prepared report, with explicit date, source references and optional report-level assessment | No account connection, invitations or automatic saving. Date/options excluded from saved reports; ICS is not resumable state. Client import/alerts/visibility need actual acceptance |
| Affiliation navigation | Automatic alphabetical index and focusable first country rows with return links in single/multi-meeting reports; native HTML, Word and PDF destinations | All affiliations and comparison gaps remain visible. Navigation does not change source scope, notes, filters, appendix or exports; no source requests or new schema |
| Bulk evidence appendix | Add/remove every filtered match across pages, with affected counts and one-step restoration of the previous mode and explicit choices | Preserves other choices, notes, source bytes, full country coverage and CSV. History is session-only and clears on manual selections or source/meeting changes; exports require preparation |
| Passage-list filters | Exact recorded country/affiliation and speaker-name filters combined with literal search and appendix selection | Temporary view only; full country overview, prepared report, source context and CSV unchanged. Names and affiliations are source labels, not verified personal identity or national capacity |
| Portable reports | Purpose-grouped resumable saves, reading copies and spreadsheets; script-free HTML, verified source-bearing JSON, full evidence CSV and a ZIP with checksums | 25 MB encoded bounds; oversized downloads fail without truncation. Exports can contain source text and analyst notes; review before sharing |
| Copy report for email | Explicit complete HTML/plain-text clipboard write, expanded provenance and source URLs, shared 25 MB UTF-8 budget; no source filters affect coverage | No clipboard reads, account access or sending. API failures preserve work; submitted writes cannot be cancelled and may finish with an earlier snapshot, which the UI identifies. OS/Outlook paste unverified; managed testing deferred |
| Print / browser PDF | Complete prepared report in the native print dialog, isolated from workspace controls, with expanded provenance and unclipped evidence | Printed HTML bounded to 25 MB; browser controls final PDF size and destination. PDF cannot resume work. Actual government-browser dialogs and participant usability remain unaccepted |
| Editable Word reading copy | Native browser-generated `.docx` with complete report text, editable country tables, source links, questions, selected evidence and separate notes | 25 MB whole-document bound; no Word import or embedded source bundle. Save JSON/ZIP separately to resume. Desktop Word rendering and diplomat usability remain unaccepted |
| Personal generated drafts | Separate Python command for configurable loopback OpenAI-compatible servers, bounded question-matched evidence, exact citation checks, browser review/context and separate HTML/editable Word copies | Unreviewed sidecar; Word retains the complete ordinary report first and rechecks source/question scope. ordinary exports unchanged. No weights bundled, real-model acceptance outstanding; loopback server may route inference elsewhere depending on configuration |
| Briefing questions | Up to eight reusable headed literal searches with Move up/down, numbered positions, source evidence/unanswered gaps and saved order | Country overview remains first; ordinary reports have no generated answers. Separate personal drafts are optional. Report v4/preferences v2; older report v1–v3 and preference v1 remain readable. Draft fields move intact; complete them before preparing or saving preferences. Standalone preferences share an 8 KiB compact UTF-8 export/import budget; full report JSON remains 25 MB |
| Device report library | Eight explicitly saved reports sharing a 25 MB UTF-8 JSON budget; title/time/size selection, source-verified reopening, stale-tab checks, atomic upgrade and retained-copy recovery | Same browser profile only; no automatic saving or authenticated collaboration. Browser cleanup may remove it. Source #295 and website #169 merged after passing checks; live migration, concurrent limits, quota rollback and recovery-download tests passed |
| Advanced browser analysis | On-demand collection, source-linked descriptive reports, dimensional methods, clustering, component analysis and saved-run comparison | JavaScript on the user's device. English-only published transcripts; no real-time audio ingestion or multilingual parity. Similar language is not policy agreement |
| Local R/Shiny | Preserved personal briefing, controlled D1 adapters, evidence inspection and unsent email exports | Separate from the public browser. Twelve executable adapters among 42 registered methods; registered plans are not operational methods |
| Personal Python pipeline | Versioned collection, immutable sources, SQLite warehouse, research exports, publication guards and recovery/inspection tooling | Separate personal/operational execution; not required on government browser clients. Existing storage limits and private/public allowlists remain intact |

Read the [reporting contract](MEETING_REPORTING.md), [browser guide](BROWSER_ANALYSIS.md)
and [operations guide](OPERATIONS.md) for setup and format limits. Browser reports
remain useful while automated stance predictions are withheld. Source hashes verify
byte consistency, not speaker identity, factual correctness or national capacity.

## Vendor comparison and remaining work

Public evidence refreshed **19 November 2026**. [FIT's product description](https://www.fondation-fit.ch/en/general/news/2026/fit-supports-impli-with-a-tech-seed-loan-and-diplotools-and-hafnova-with-two-digital-seed-loans)
identifies PowerTranscript's generated transcripts/summaries, user-defined templates
and centralized retrieval, and PowerElection's UN campaign CRM.
[UNITAR's launch account](https://unitar.org/about/news-stories/news/unitar-and-diplotools-launch-tech-solutions-growing-diplomatic-workloads)
confirms an election-management demonstration.
[Venture Kick's February 2026 account](https://www.venturekick.ch/DiploTools-receives-CHF-150000-from-Venture-Kick-to-build-purposebuilt-AI-tools-for-modern-diplomacy)
also describes position coordination and secure communication, alongside election
tracking and automated conference reporting. These are publisher/vendor descriptions,
not independent technical security tests or measured acceptance for this app.

The [vendor homepage](https://diplotools.com/) returned a JavaScript shell to the
text tool; rendering its public page in an isolated browser exposed general
report-generation/campaign/centralization claims and demo links, but no detailed
product checklist. No account was accessed, demo requested or communication sent.
The time-saving claims are promotional figures, not benchmarks for this project.
Product names or fine-grained features found only in secondary/AI-generated
listings are not treated as confirmed requirements. Unrelated DiploFoundation
products are not DiploTools evidence.

| Documented category | Current project | Additional work |
| --- | --- | --- |
| Generated transcripts/summaries and configurable reports | Published English sources, deterministic country-first reports, editable settings/literal questions and optional personal draft protocol | Confirm required input/audio/language scope from a permitted vendor specification. Choose personal runtime/hardware and storage budget before weights; validate actual generation/transcription and citation/attribution quality. Current app has no audio ingestion/live ASR or accepted generative model |
| Centralized retrieval | Public metadata archive, personal warehouse, loaded-source search and explicit device/file saves | An authorized shared private store, identity/access rules, source versions, retention/capacity and recovery acceptance are needed for mission-wide retrieval. Public static assets and local JSON are not that service |
| Election/campaign management | One manual campaign per file, current country statuses, profiles, interaction snapshots, reviewed contact handoff and calendar reading copies | Obtain the actual workflow checklist before adding multi-election/eligibility or reciprocal-support behavior. Confirm authoritative election inputs and acceptance cases; do not turn reported support or geographic labels into observed votes or voter eligibility |
| Position coordination and secure communication | Source-based comparisons and explicit report/contact reading copies; no authenticated team approval or messaging | Specify actual headquarters/mission roles and workflows, then an authorized identity/storage/communication integration with access, conflict and audit behavior. Local editable notes, checksums and profile IDs do not authenticate collaborators or provide secure communications |

This is a bounded comparison, not a complete vendor feature inventory. Full parity
cannot be established from public marketing or synthetic QA alone. The next
requirements evidence is a permitted feature checklist or walkthrough, paired
with real user/client task results. Preserve the JavaScript government-browser
path, separate personal R/Python execution, storage bounds and scientific/source
gates while deciding which shared or compute-heavy functions are feasible.

The [facilitator setup](REPORTING_USABILITY.md) creates six fictional JSON files
using Node alone: three reporting files, a matching hand-authored model draft,
a campaign notebook and a contact-only transfer. Its isolated browser rehearsal
retains ten private report/campaign downloads and checks handoff, explicit calendar
dates and complete reading copies. Model inference, calendar-client import and
participant acceptance remain explicitly unperformed by the tool. Actual user
and client observations belong in a separate private session record. [Source #355](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/355) passed
its contract check and is merged. At that facilitator checkpoint, public
application bytes remained 1.81.0 and repeat mirror synchronization copied/removed
zero files; the current release is recorded at the top of this document.

The owner selected **Microsoft Edge and Outlook** for the actual client rehearsal.
The [targeted guide](REPORTING_USABILITY.md#edge-and-outlook-rehearsal) gives file
checks and edition-specific calendar import routes based on current Microsoft
instructions. Exact edition/build/account policy and observed results remain
unrecorded. The subsequent [native Edge engineering pass](REPORTING_USABILITY.md#native-edge-engineering-receipt)
passed 19 local UI suites, the facilitator contract and six preferred-site suites
in unmanaged Linux headless Edge 157.0.4341.60; all 201 deployed file hashes matched.
No app fix was required. This does not establish managed government Edge, Outlook
import or participant acceptance.

## Operational and scientific boundaries

The public archive is read-only allowlisted metadata; it is not a shared repository
of private transcripts or mission notes. Coverage is partial. Browser collection
is user-triggered and may retrieve a newer source revision than the scheduled
warehouse. Check the actual manifest and source revision rather than treating
historical meeting totals as current availability.

Durable collection, private/public publication, restore/re-export replay and
bounded storage accounting have real engineering receipts. They do not establish
account-wide quota acceptance or sustained scheduled service. The recorded first
scheduled success was delayed; fourteen-day operational acceptance remains
outstanding. Read [operational acceptance](OPERATIONAL_ACCEPTANCE.md) and
[storage accounting](STORAGE_CAPACITY.md) before making reliability claims.

**No accepted five-level stance model or complete owner benchmark exists.**
Candidate preparation, training interfaces and assistant QA do not substitute for
actual owner labels, source-disjoint calibration and untouched evaluation. Collective,
conditional, missing and ambiguous evidence must stay distinct from neutrality.
The single-reviewer owner mode remains in force; do not claim independent agreement.
Historical issue/vote infrastructure and research previews are not accepted fitted
models or proof of government alignment. All 37 reserved meetings remain closed.

## Acceptance dependencies

1. Complete representative diplomat tasks using the [usability guide](REPORTING_USABILITY.md) and its runnable local synthetic facilitator session
   and record actual findings separately from synthetic browser tests.
2. Complete continued scheduled-operation, recovery and account-wide capacity
   acceptance without treating manual runs or elapsed time as acceptance.
3. Complete owner labeling, then train/calibrate/evaluate on the designated source
   splits. Preserve failed gates as failures.
4. Evaluate optional generative reporting separately for factual coverage, citation
   correctness and unsupported claims. The quick reader remains deterministic.
5. Confirm a permitted vendor feature checklist/walkthrough before claiming feature parity.
   Scope audio/language support, authenticated retrieval, headquarters/mission
   coordination, secure communication and full election workflows as separate
   requirements with explicit execution/storage/identity constraints.

## Repository cleanup

The public builder excludes `issue-candidates.js` and `issue-extraction.js`:
neither is referenced by a published page, script or worker. Both remain available
to their offline research tests. This removes 9,909 bytes from publication without
changing any retained public file: 198 files in 207 build entries. A build test
checks the exclusion and refuses a future published dependency on either module.
This is publication cleanup, not removal of the active research source or an
accepted model. App release 1.85.0 and browser functionality are unchanged.

The initial inventory measured approximately 127 MB under `un/` and 24 MB under
`docs/`, including repeated fixtures and frozen receipts. Three generated GMM,
NMF and display comparison snapshots were verified against commit
`5d0ca060b7cfb90509b47ed4ac0c87a532eb637e` and removed from the active tree:
**16,269,686 bytes**. All nine links now use that immutable Git archive; archived
inputs regenerate the current HTML audits byte for byte. Current status documents
have been consolidated; their historical receipts remain linked below.

The personal R package now also excludes 226 generated output files
(50,521,390 bytes) and three superseded I4 freezer scripts. Their exact versions
remain recoverable from [the preserved archive](https://github.com/LystadJS/UNGA81-Transcript-Agent/tree/ea18ad83b030e10abfb32d2525c17ada5f5939b9/un).
The old scripts hardcoded six adapters and 371 checks; current code has 12 adapters.
Generated output, local libraries, caches and models are ignored. Default tests no
longer read a user's latest output; optional frozen-run checks require an explicit
`UNBRIEF_ARCHIVED_RUN`. See [the R guide](../un/README.md).

All 1,673 retained RDS fixtures are byte-identical to the preserved commit and
read successfully without direct output-path references. Original checksum
records, the historical checkpoint manifest, Shiny pin and UI manifest are
unchanged. `tools/package_checksums.py` verifies the current 2,077-file tracked
inventory in CI and refreshes only the current checksum record after staged edits.
Six focused tests cover inventory maintenance and unsafe refresh cases.

On Linux with R 4.5.0, Matrix 1.7.3, cluster 2.1.8.1 and igraph 2.1.4, the seven
retained suites pass 453 default checks; explicit archived-run selection passes
the two additional frozen-run checks (455 unique checks). This is personal-runtime
validation, not Windows, live Shiny, PDF or scientific acceptance. At that cleanup checkpoint, the Python suite
passed 256 tests; the current total is recorded above.

Fresh full offline replays before and after cleanup both exit successfully with
identical validation: 39 country sections, 507 coding cells, five report packets,
42 methods accounted and 133 prerequisites. Seven fitted candidates remain withheld;
no released model or semantic-accuracy claim follows from structural QA.

The R cleanup added no browser dependency or Hugging Face storage; its
validation is separate from subsequent browser reporting releases.

These removals reduce the active checkout, not retained Git history. Reproducibility
fixtures and source corpora remain; a runtime-only repository has not been achieved.
Keep future generated output out of version control and preserve original records.

## Licensing and historical receipts

Keep third-party notices in `site/NUMERICS_LICENSES.txt` and
`site/HDBSCAN_LICENSE.txt`, plus model/package provenance. No blanket license is
added to inherited code, UN text or annotations. Public availability does not
establish redistribution rights; do not broaden source-bearing public exports
without resolving those rights and preserving the publication boundary.

Detailed historical deployment, data-count, owner-review, storage and replay
receipts remain in the [archived capability record](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/44cf6ba28a5b38693547407a4ac2414e6b607c82/docs/CAPABILITIES.md).
Use each receipt's original date and scope; these are not fresh acceptance checks.
