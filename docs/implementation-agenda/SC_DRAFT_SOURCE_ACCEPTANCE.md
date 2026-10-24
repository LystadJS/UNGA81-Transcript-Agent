# Security Council draft-source acceptance

24 October 2026. Status: actual source validation and isolated private import
accepted for the pinned source window. Public data release, comprehensive voting
coverage and policy inference remain separate gates.

The [official DPPA-SCVOTES catalog](https://psdata.un.org/dataset/DPPA-SCVOTES)
provided a CSV with 2207 draft-event rows and these inspected columns: native ID,
year/date, adopted reference, meeting reference, draft, agenda/topic/category/
region, outcome, three named-country choice lists and update date. Its exact
738784 downloaded bytes hash to SHA-256
`ef06cdc34fd8a1a0b080f68b04a92c678fe904a2ece49a7b81a982c04bcd8bdf`.
The update date recorded by the source is 23 October 2026.

## Reconciled import

The frozen window is 24 October 2016 through 23 October 2026. It contains 581
events, 8713 catalog member entries and two separately sourced nonparticipation
notes. Imported event dates run from 31 October 2016 through 20 October 2026;
these endpoints describe this source, not verified absence outside them. The
outcome distribution is:

| Exact source outcome | Events |
|---|---:|
| Adopted unanimously | 400 |
| Adopted by majority | 119 |
| Not adopted - veto | 36 |
| Not adopted - failed to receive required number of votes | 26 |

The source's unanimous category can include adoption without a formal vote.
Consequently, all 6000 member entries in its 400 unanimous events retain their
published choice separately while their individual ballot is `unknown` and
eligibility is unset. They are not counted as 6000 verified affirmative votes.
The remaining normalized member entries are 2027 yes, 170 no and 516 abstain.
Outcome labels follow the source. A permanent member's negative choice does not
by itself establish that an event failed because of a veto.

Country identities use literal registry names, declared registry aliases and an
explicit small alias table; fuzzy matching is not used. Original recorded names
remain private alongside the mapping. Unknown names would retain unknown
identity/ballot handling rather than being assigned to a nearby country. All
names in this imported window resolved through those explicit mappings.

Whitespace around a draft symbol is trimmed for matching while its original
value remains preserved. Raw adopted references are retained; malformed
references are flagged rather than silently repaired or used as an invented
cross-source join. Written-procedure references and an unavailable meeting
reference remain distinguishable from ordinary meeting-record references.

## Nonparticipation is separate evidence

Two catalog events list 14 members. Their original country-choice lists remain
unchanged. Separate primary references identify Algeria's nonparticipation; no
fifteenth ballot or eligibility decision was invented.

The [31 October 2024 UN meeting coverage](https://press.un.org/en/2024/sc15882.doc.htm)
supports one note. Its stored hash covers a browser-rendered primary-text
snapshot, explicitly labelled `browser_rendered_primary_text`; it is not a hash
of the publisher's original HTML response.

The [2025 Security Council practice annex](https://main.un.org/securitycouncil/sites/default/files/2026/2025_annex_highlights_of_security_council_practice.pdf),
pages 13 and 15, supports the other note. Its stored hash covers an explicitly
labelled `tool_extracted_primary_metadata` receipt containing the source URL,
event facts, page references and nonparticipation cue. Original PDF bytes were
not successfully acquired, so no original-PDF hash or authentication is claimed.

Both notes remain `assistant_provisional`. The generic overlay loader verifies
the actual stored evidence-file hash and declared scope. Event ID, date, draft,
meeting reference, outcome, source CSV hash and recorded-choice counts must
match. Extracted-metadata receipts must also match the source URL, adopted
reference, source pages, named country and review state. Unrelated or damaged
overlays fail validation. All actual overlay payloads and evidence snapshots
remain private; the public code and tests contain no imported overlay entries.

## Storage and validation

The import uses its own source family and native-event/country namespaces,
`draft_resolution` stage and isolated private SQLite ledger. All member entries
remain policy-unbound. The completed GA/SC adopted-vote ledger and its cursors
were not modified; its SHA-256 remained
`25312f9349bdd8d604d297ba219183dd47d38e3671a729b3103a95ea87f535a3`.
No imported source was approved for public export.

Every imported event's normalized hash and all 8713 stored member entries were
checked against the saved private collection. Event/member counts, source
revision consistency, foreign keys and SQLite integrity passed. Nonparticipation
notes were confirmed absent from the ballot table. Six synthetic tests passed
for unanimous ambiguity, exact aliases and unknown names, duplicate/incomplete
rosters, official outcomes, literal references, isolated/idempotent imports,
storage reserves and source-scoped overlays. These are engineering checks, not
owner-confirmed labels or estimates of political-position accuracy.

The importer pins source bytes, date window, adapter, normalizer, registry and
overlay identities. It commits bounded batches before advancing its checkpoint,
preserving at least 200 MiB plus the next-batch margin. Recorded free capacity
after reconciliation was 6726500352 bytes. Existing user collections and the
earlier adopted-vote database were untouched.

## Remaining gates

DPPA drafts and Digital Library adopted resolutions may represent the same
voting action. Their raw totals must not be added or treated as independent
agreement evidence. Combined analysis requires an explicit cross-source event
crosswalk and deduplication policy, with unresolved matches kept separate.
Catalog topics are metadata, not explicit national policy positions. A vote on
a full draft does not establish agreement with every clause. Procedural votes,
withdrawn proposals, other committees and statement coverage remain separate
source-feasibility and acceptance work. This import does not establish complete
UN deliberation coverage or an accepted longitudinal model.

## Published browser acceptance

Version1.36.0 is live with a separate private-file draft viewer. Source-free actual-browser CI passed, including five-filter restoration, full frozen replay, script-free export, invalid-family recovery and desktop/mobile layout. A separate live check used the actual private581-event collection: all8713catalog entries,twoseparate notes, date bounds, outcome, query, displayed-country filter and results survived save/reload/reopen/export with exact JSON equality. The final caption/cache correction also passed that replay; no historical opinion inference or public data provisioning follows. Deployment40064972175 and live asset verification40064972260 passed.
