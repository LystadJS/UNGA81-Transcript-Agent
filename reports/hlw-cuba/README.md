# Cuba review: UNGA81 High-Level Week, 21–28 September 2026

Open `index.html` for the linked working brief. `cuba.csv` contains direct Cuba
candidate passages; `evidence.csv` includes all eight topic searches. Generic
sanctions, embargo or sovereignty wording is not automatically Cuba-specific.
`countries.csv` links General Debate country/observer attributions with direct
Cuba wording. These are mention counts, not a stance classifier or vote forecast.

## Collection

The official public service at https://transcripts.un.org was queried with
`/en/meetings.json?date=YYYY-MM-DD&xlang=1&page=N` for all eight dates. Pagination,
totals, date identity and duplicate meeting IDs were checked. All available
detail URLs were downloaded, with hashes of the original response bytes retained.
There were 226 indexed meetings: 170 downloadable transcripts and 56 explicitly
unavailable transcripts. No collection errors occurred. Six General Debate
meetings were downloaded. This is complete within the retrieved inventory, not
proof that every delivered HLW speech has been published or independently found.

Of the 170 downloads, 163 identify English, six floor-language, and one French.
Original language labels are retained. The collection contains automatic speech
recognition, interpretation and attribution errors; it is not an official
verbatim record. The tool's original disclaimer is retained with every raw source.
The source flags timestamps in 59 transcripts as unreliable. The evidence and
coverage exports retain that flag; time links are navigation aids, not verified
timing evidence. Exact quotations are bound to text offsets and raw JSON pointers.

Broad scope includes General Debate, high-level meetings, side events, relevant
Council proceedings and press remarks. Obvious unrelated HRC, Crime Congress,
treaty-body, Geneva press and IPPO proceedings are retained and searched as
background. Remaining non-General-Debate meetings are broad HLW candidates;
venue and formal event membership have not been independently reconciled.
`coverage.csv` discloses every meeting, scope decision and availability gap.

## Existing workflow with a task-local batch wrapper

No files under `un/` were edited. Collection, format conversion, run configuration
and delivery helpers were added under `tools/`. The existing Shiny multi-date
**upload backend** was invoked directly through `run_readout`, using local files,
literal topic matching, exact source quotations and unsent email exports. This
does not claim execution of the full D1 daily adapters.

All 11,146 nonempty source segments are preserved. Segments sharing an explicitly
recorded affiliation within a meeting are grouped into 3,728 upload records.
Names and speaker metadata remain in `segments.json`; unknown affiliations are
not assigned to countries. A grouped record can contain several interventions,
so it is not a distinct-speech denominator. Three batches respect the existing
2,500-record upload limit. Research discovery remains subject to the unchanged
500-text limit per run; no research outputs are released or silently sampled.

The eight searches cover Cuba; embargo/blockade; unilateral sanctions;
terrorism-list designation; extraterritorial restrictions; medical cooperation;
humanitarian/development effects; and sovereignty/non-interference. See the
saved request files for exact terms. Human-rights and recruitment concerns in the
brief come from reading direct Cuba contexts, not from a newly trained model.

Windows initially selected a non-UTF-8 locale, causing partial CSV reads. Those
initial runs were rejected and are excluded from the delivery. The run wrapper
sets UTF-8, fails on preflight read warnings, and checks input row counts. Final
validation reconciles every input record, source hash and exact quote offset
against the original source segment. See `validation.json` for actual results.
The run wrapper caches the existing passage parser's exact results and applies
the existing vector-capable phrase predicate to batches of passages. This avoids
parsing each full body and rebuilding the same pattern for every sentence/topic.
The task-local matcher is checked for exact agreement with the original matcher
on boundary, exclusion, Unicode, empty-text and acronym cases; every delivered
quote is independently checked against its source. Core application files and
matching rules are unchanged. This is a performance wrapper for this collection,
not a replacement for the application's default matcher.

## Reproduce

From the repository root, with the existing R dependencies installed:

```powershell
python tools/collect_hlw.py review-work/hlw
python tools/prepare_hlw.py review-work/hlw
Rscript tools/run_hlw.R un/ui review-work/hlw
Rscript tools/check_hlw.R un/ui review-work/hlw
python tools/report_hlw.py review-work/hlw reports/hlw-cuba
python tools/package_hlw.py review-work/hlw reports/hlw-cuba C:\short\hlw-cuba.zip
```

The collector reuses cached response bytes. For a fresh availability check, use
a new collection directory; existing finalized outputs are retained. Source
archives and full run products are delivered in the local ZIP rather than adding
hundreds of megabytes to Git history. The repository retains retrieval helpers,
hashes, coverage, the brief and evidence exports. Local raw sources remain under
the ignored `review-work/hlw` directory. No labels were represented as human
reviewed, no real-data model was trained and no email was sent.

## Recommended next steps

1. Review Cuba's and the United States' statements alongside the Caribbean
   dialogue/reform positions; avoid collapsing them into a binary alignment label.
2. Verify consequential wording, figures and allegations against audio or the
   submitted written speech before quoting them externally.
3. Obtain the 56 missing transcripts or repeat collection into a fresh directory.
   Keep background proceedings separate from HLW findings.
