# Security Council cross-source voting event reconciliation

This milestone checks whether DPPA draft events and Digital Library adopted-resolution records refer to the same voting action. It does not merge the original ledgers, publish a combined voting corpus, establish policy positions or select a longitudinal model.

## Identity and evidence rules

Only literal adopted-resolution symbols with explicit years and exact dates can form one-to-one identity candidates. Malformed references, multiple draft candidates and conflicting identities remain unresolved. Draft and adopted stages retain their original identities. Failed drafts never become adopted events. Normalized ledger fields that lack draft or meeting references remain explicit reference gaps; matching a resolution and date does not claim those absent fields were independently reconciled.

Event identity and ballot consistency are separate results. Full country-code rosters must reconcile before ballot agreement can be asserted. Recorded disagreements and roster gaps remain visible. DPPA unanimous entries remain unknown even when the adopted-resolution source records affirmative ballots. Unknowns are not affirmative agreement, and nonparticipation notes are not votes. The existing source rows, revisions, private collections and durable import cursors remain unchanged.

The new implementation and synthetic tests contain no actual collection records. Detailed crosswalk links and source-bearing receipts remain in private staging. Production use still requires an explicit downstream event-selection policy; this diagnostic crosswalk does not silently add, remove or reweight historical evidence.

## Validation

Read-only reconciliation found511unique resolution/date candidates between581DPPAevents and516DDLadopted-event groups. Of those candidates,116have fully matching recorded ballots and395have unknown/modality gaps:393unverified-unanimous events and two events with source-backed nonparticipation notes. Across118events with recorded DPPA ballots,1768comparable individual categories agree; the two noted nonparticipants correspond to DDLunknown entries. The393unanimous events contain5820DPPAunknown/DDLaffirmative pairs and75unknown/unknown pairs in five DDLwithout-vote groups. None becomes newly verified affirmation.

The normalized ledger lacks draft/meeting fields. A second check enriched only those fields from the pinned original official CSV (decompressed SHA256`c73e8d7b61ee1323e8a48af2fcbb5b8d14ab05619030862793a79ecfb0cbb5c2`), confirming that the ledger source pin matches. This exposed22reference conflicts:15draft-reference disagreements and seven meeting-reference disagreements. Those22are ineligible for automatic event deduplication. The remaining489reference-consistent candidates comprise110fully recorded-ballot matches and379event-identity-only candidates with evidence gaps. These are diagnostic eligibility results, not a merged or publicly accepted historical corpus.

Seventy DPPAevents remain without an exact link:62failed drafts and eight adopted events. The eight adopted gaps include four same-resolution/different-date cases, one malformed symbol, one unmatched event inside the observed DDLdate range and two events after the DDLfile's latest date. Five DDLevents lack exact DPPAcandidates. No fuzzy repair, date correction, duplicate vote weight or policy binding was applied.

Thirteen new synthetic regression checks cover literal normalization, deterministic replay, immutable inputs, unknown unanimity, unresolved dates/symbols, country/ballot conflicts, ambiguous links, duplicate members, source/stage/revision validation, resolution-year conflicts, participation-proof validation, explicit nonparticipation-versus-ballot conflicts and input overwrite prevention. All59Python checks and existing draft/report Node checks passed locally. The wrapper uses read-only database access, current source revisions, bounded source reads, dependency/input hashes, atomic output and input-path protection. Original ledgers, source collections and import checkpoints remain unchanged. Publication checks are recorded in the execution ledger.
