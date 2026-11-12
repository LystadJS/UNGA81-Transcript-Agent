# P0–P1 historical UN General Debate acquisition

**Status:** read-only, source-metadata reconnaissance. This module does not certify a real longitudinal W4 panel, fit models, or authorize empirical publication. The 37 reserved October 5–6, 2026 meeting transcripts remain sealed and outside the accepted 2016–2025 General Debate time window.

## Sources and version claims

| Source | Coverage | Fixed endpoint | Inference boundary |
| --- | --- | --- | --- |
| Harvard Dataverse United Nations General Debate Corpus (Jankin, Baturo, Dasandi) | Text corpus; reported sessions 1–80 through 2025; **version must be verified against actual downloaded bytes and Dataverse file metadata** | Dataset DOI https://doi.org/10.7910/DVN/0TJX8Y; **file ID 13591895** (candidate pinned file) | Cleaned third-party text is **not** original UN byte-verified delivery |
| UN Dag Hammarskjöld Library General Debate speaker index (Jan 29, 2026) | Speakers and national affiliations, sessions 1–79 through 2024 | https://digitallibrary.un.org/record/4067189/files/GA_debate_speech_dataset_20260129.csv | National representation is not verified person ID, official stance, or delivered-text fingerprint |

UN Library copyright is noncommercial with attribution. These sources are cited rather than republished. Never silently treat an upstream claim such as "UNGDC v14" as verified if dataset API and file fingerprint have not been checked. Scope excludes 2026 and therefore all October 5–6 reserved meetings.

## Use

Install Python 3.11+ and the pinned country-code library, then run tests:

    python -m pip install pycountry==24.6.1
    python -m unittest discover -s research/source_acquisition/general_debate -p 'test_*.py' -v

Explicit remote acquisition (new directory **outside the repo**):

    python research/source_acquisition/general_debate/acquire.py \
      --download --start-year 2016 --end-year 2025 \
      --out /your/private/research/general-debate-p0p1-001

Offline replay from files legally acquired earlier:

    python research/source_acquisition/general_debate/acquire.py \
      --corpus /your/private/UNGDC_1946-2025.tar.gz \
      --official /your/private/GA_debate_speech_dataset_20260129.csv \
      --out /your/private/research/general-debate-p0p1-002

The runner *never* downloads unless --download is supplied; it only accepts two allowlisted HTTPS URLs. The Harvard datafile ID is pinned, but release version remains **unverified** unless Dataverse metadata reports that ID in the latest released dataset. It refuses to overwrite previous output or to write beneath the git repository. Failure of one source produces an explicit partial-only status, not a fabricated cross-source match.

Outputs under the newly created PRIVATE directory:

- downloaded_sources/: original downloaded tar.gz and UN index CSV; **never publish**.
- private/corpus_members_private.csv: corpus member identities and third-party text SHA-256, **not** original UN document hashes.
- private/un_official_speakers_private.csv: original index speaker names, affiliations and meeting symbols, identity unverified.
- private/candidate_crosswalk_private.csv: country × session candidate grid with null unknowns, mismatch reasons and source identity, **not** a verified UN membership roster.
- acquisition_manifest_private.json: local source ledger, SHA-256, version checks and missingness/QA.
- public_aggregate/per_year_aggregate.csv and public_aggregate/acquisition_receipt.json: summary counts and source-file digests, with **no person names, country-level source rows or speech text**. Only these two files may be uploaded as a CI artifact.

An **observed-union candidate population** is used until an independent UN membership-by-session source is obtained. A country absent from both input files for a year is marked as **unknown**, not proven to have missed the debate. The 2025 index is explicitly out of scope: the January 2026 UN speaker dataset ends at 2024.

## Reconciliation rules

- Corpus member pattern: ISO3_session_year.txt and session = year - 1945; archive parsed without extracting any files; 2026 never read. Target-year raw corpus bytes are hashed but never printed.
- Official fields: Name, Salutation, Member State, GA Session, Meeting Date, Meeting Symbol, Agenda Items, UNDL ID, UNDL Link. Country mapping uses ISO aliases and a small transparent UN-name table, **not fuzzy name matching**; unresolved mappings and multiple speaker rows remain explicit.
- Candidate join on (GA session, ISO3), **not** country name, display order, speaker string or publication year. Exact delivered text, date, person identity, source revisions and original official UN document bytes still require PV/document audits.
- No access or mutation of frozen heldout content, evaluation locks, user-reviewed decisions or D1 O1–O5 gates.
- CI executes synthetic tests and attempts acquisition into an ephemeral runner-private temp directory; it uploads **only aggregate receipts**. Network/source HTTP errors are acquisition blockers, not evidence that tests or sources passed. Never upload private/ or downloaded_sources/.

## Explicit fallback when primary sources cannot be fetched

The first GitHub Actions live acquisition attempted both Harvard Dataverse and the UN Library's direct CSV, but **neither was retrieved** in that run (Actions #37811519412). The offline tests (8 of 8) and privacy contract passed; **no actual source reconciliation was performed**. Consult each newer aggregate receipt for updated status and non-sensitive HTTP error class.

A separately pinned, **lower-trust** open GitHub RDS from Jihyeonbae/UNGDC may provide a partial 2016–2022 filename-equivalent country/session inventory. Its README documents 1946–2022. The file is pinned to repository commit 62df50941fd7afc00cb75256e1f91fe1ae690011 and Git blob 1325ee6b0d6ff2d8a85b11807a514b9fb7d86871; downloaded bytes are verified against the Git blob identity before parsing. Install pyreadr==0.5.4, then run:

    python research/source_acquisition/general_debate/mirror_inventory.py \
      --out /your/private/research/general-debate-mirror-p0-001

This produces ONLY a partial third-party-derived 2016–2022 private index and non-identifying aggregate receipts; 2023–2025 cells explicitly say **outside the documented mirror release**, never no speech. Git identity checks provenance **to that mirror**, not fidelity to original UN documents or equivalence to Harvard v14. Do not merge the mirror text fingerprint with the original Harvard/UN byte basis or promote mirror results into W4 inference. This branch's CI may run the mirror independently of the two-source acquisition gate; failure of either primary source remains unresolved.

## Actual 8 October 2026 execution receipt

**Executed, not hypothetical.** The public Dataverse metadata API returned **dataset version 14.0**, a named file ID 13591895, file size **71,280,312 bytes**, and archive MD5 **81bdd06086d9e7c4e67026acb7325df3**. These are publisher-supplied metadata; archive bytes and SHA-256 have NOT been acquired or verified. The direct Harvard file endpoint returned HTTP 400. The UN index HEAD returned HTTP 202 and text/html rather than downloadable CSV. Both primary-file acquisition attempts were blocked, and official two-source reconciliation remains NOT RUN.

The independent GitHub mirror job **did succeed**: pinned source blob SHA1 1325ee6b0d6ff2d8a85b11807a514b9fb7d86871, computed RDS SHA-256 d7d9c74c1ad8a5f107bffd296ff035e2efa3deedb2f7c0870e564be5664428b1, **1,354** retained country/session observations from 2016–2022. It excluded **seven invalid/unresolved ISO3 rows**, retained in a private exception ledger for future adjudication. The 2023–2025 gap is **release noncoverage**, not verified absence.

Permanent text-free aggregate source receipts:
- receipts/2026-10-08-pinned-mirror-aggregate.json
- receipts/2026-10-08-primary-source-metadata.json

**Required private owner handoff if HTTP barriers persist:** download from the two official source landing pages using their normal authorized browser/download interface, satisfy any Dataverse terms or guestbook, and provide (1) UNGDC_1946-2025.tar.gz (Harvard v14 file ID 13591895) and (2) GA_debate_speech_dataset_20260129.csv (UN speaker index) through an approved private channel. Never upload original texts or row-level identity ledgers into this public GitHub repository. The CLI will hash the supplied files and use the original source URLs for provenance. Keep source-data licensing and reuse restrictions.

## Outstanding P0–P1 gates

1. Obtain both actual source files, verify file ID, version, SHA-256 and year/session coverage; if the endpoint blocks automated requests, use authorized offline download rather than bypassing controls.
2. Resolve country aliases and one-to-many authority rows using independently reviewed evidence. Obtain the historical UN membership denominator; do not equate the observed union with 193 annual speeches.
3. Independently audit a stratified sample of original UN PV and source versions; retain translation, OCR, agenda, duplicate and delivery discrepancies in private logs.
4. Authenticate original UN bytes and actor/meeting attribution before freezing a historical representation.
5. W4 currently rejects null meeting IDs/source hashes for genuinely unavailable rows. **Do not invent these identifiers to make ingestion pass.** Fix the W4 source adapter under a subsequent approved change.

**Release boundary:** Candidate coverage and archive hashes are P0–P1 research logistics, not W4 empirical statistical validation, political change, significance or publication eligibility.

## Uploaded primary-source reconstruction — 8 October 2026

Both previously unavailable original source files were supplied through the private chat (not added to public GitHub). The Dataverse `dataverse_files.zip` contained the exact v14.0 `UNGDC_1946-2025.tar.gz` and `Speakers_by_session.xlsx`; both **publisher-reported MD5 checksums and sizes passed**. ZIP CRC passed. The uploaded UN Library `GA_debate_speech_dataset_20260129.csv` passed expected header and link structure and its local SHA-256 was recorded, but an external publisher checksum was unavailable.

**Aggregate outcomes:** 1,926 ISO3 country speech text files for 2016–2025 plus nine separately inventoried two-letter EU observer text files; 2,008 official UN speaker index rows in 2016–2024 (1,734 distinct country-session keys); 1,936 Harvard speaker metadata rows in 2016–2025; candidate union of 195 ISO3 entities across 1,950 year cells; 1,733 three-source **key-only** matches for 2016–2024. For 2025, all 190 Harvard country speech files have Harvard-associated speaker metadata but no independent UN index in this version. Historical-year missing cells remain **unknown rather than verified absent**.

**Discrepancies:** Full confidential ledger with 719 open flags: 3 critical, 21 high, 694 review, 1 medium. It includes 273 country-year groups with multiple UN speaker records, 340 nonidentical normalized speaker-name strings (not proof of different people), five malformed raw Harvard workbook ISO values, and source-key gap flags. Nine EU texts are retained as non-state observations; they must not be counted as 193-state roster entries.

**Important archival fidelity warning:** The v14 README documents **2024 mixed PDF/OCR/automated translation** methods and **2025 Whisper-1 ASR from simultaneous interpretation audio**. These are *not* observationally exchangeable with earlier written UN speech records without a validated method-stratified design. No original UN PV statement text was independently compared, no speakers were authenticated as individuals, no historical membership census was validated, and W4 empirical/inferential/publication eligibility remains **WITHHELD**.

Aggregate public-safe receipt: [2026-10-08-uploaded-v14-reconciliation-aggregate.json](receipts/2026-10-08-uploaded-v14-reconciliation-aggregate.json). The full country-session inventory, source-linked discrepancy ledger, and executable local reconciliation script were delivered **privately** in the conversation and must not be committed to this public repository. The earlier GitHub Actions remote-download failure remains correctly recorded; it does not negate the separate verified local files.

