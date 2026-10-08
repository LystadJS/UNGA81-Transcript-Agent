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

## Outstanding P0–P1 gates

1. Obtain both actual source files, verify file ID, version, SHA-256 and year/session coverage; if the endpoint blocks automated requests, use authorized offline download rather than bypassing controls.
2. Resolve country aliases and one-to-many authority rows using independently reviewed evidence. Obtain the historical UN membership denominator; do not equate the observed union with 193 annual speeches.
3. Independently audit a stratified sample of original UN PV and source versions; retain translation, OCR, agenda, duplicate and delivery discrepancies in private logs.
4. Authenticate original UN bytes and actor/meeting attribution before freezing a historical representation.
5. W4 currently rejects null meeting IDs/source hashes for genuinely unavailable rows. **Do not invent these identifiers to make ingestion pass.** Fix the W4 source adapter under a subsequent approved change.

**Release boundary:** Candidate coverage and archive hashes are P0–P1 research logistics, not W4 empirical statistical validation, political change, significance or publication eligibility.
