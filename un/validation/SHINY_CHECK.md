# Shiny MVP + D1-I4 integration validation

**Release:** 0.2.0-d1-i4  
**Checkpoint:** UN Daily Briefing R 2.5.0 D1-I4  
**Validation runtime:** R 4.6.1 on Linux/Debian  
**Result:** PASS for backend integration, inherited regressions, adapter contract, custom-topic invariance, and static interface validation. Live Shiny session launch was not executed in this environment because the required Shiny runtime packages are not installed.

## Integrated behavior

- The diplomat-facing interface accepts arbitrary tracked issues without editing the legacy D1 issue codebook.
- The full eligible corpus is processed before user-topic matching; changing tracked issues does not alter the D1 frozen feature artifact or the interface discovery feature fingerprint.
- D1 retains exactly five analytical publication slots, O1 through O5.
- D1 clustering/discovery outputs remain audit-gated; the interface does not promote research-only clusters into released policy claims.
- User-topic matches are conservative literal/approved-phrase candidate matches with source evidence. A no-match remains unresolved rather than being converted to an asserted absence.
- The generated email remains unsent (`X-Unsent: 1`).
- The adapter does not mutate the legacy D1 issue codebook or the legacy `output/latest.json` pointer.
- Mutable D1 analysis state is isolated by request hash under a request-specific runtime namespace.

## Acceptance results

| Check | Result |
|---|---:|
| Legacy base regression | 87 / 87 pass |
| D1 regression | 94 / 94 pass |
| I2 frozen feature/PCA/PCoA regression | 101 / 101 pass |
| Hierarchical clustering regression | 58 / 58 pass |
| PAM regression | 33 / 33 pass |
| **Inherited checkpoint total** | **373 / 373 pass** |
| Shiny MVP backend regression | 97 / 97 pass |
| New D1/Shiny adapter contract | 9 / 9 pass |
| Full D1 replay acceptance | PASS |
| Dynamic-topic feature invariance | PASS |
| Static UI, 1440 px viewport | PASS — no horizontal overflow |
| Static UI, 390 px viewport | PASS — no horizontal overflow |
| D1 connection/pinned adapter check | PASS |
| Live Shiny browser session | NOT EXECUTED — runtime packages unavailable here |

## Full D1 replay acceptance

The integration replayed the bundled 23 September 2026 corpus and completed with:

- 39 speeches processed;
- all 42 registered D1 methods accounted for;
- 133 prerequisite checks accounted for;
- exactly O1–O5 retained;
- three arbitrary user topics applied after full-corpus analytical processing: Artificial Intelligence, Food Security, and Security Council Reform;
- custom-topic evidence written to CSV;
- D1-style HTML, plaintext, and unsent EML generated;
- no analytical packet released merely because a custom topic was supplied;
- no email sent.

## Invariance check

Two materially different tracked-topic configurations were applied to the same corpus. Topic-match results changed as expected, while the analytical feature artifacts did not:

- D1 M02 artifact SHA-256: `7e37ed84a1bf5a21f45ad41019d99358a7fa4cb96fb269a78407fff4f7061691`
- Interface full-corpus feature SHA-256: `c54031831cd900eebd9f12abc01cdc9ff503ad91aeb93bafb5fabd370fc445dc`

This confirms that tracked topics act as a parallel analytical lens rather than a pre-filter on unsupervised discovery.

## Integrity checks

- Legacy `config/issue_codebook.json` SHA-256 remains `6889769c3aeb9b5cdaea75872fe1a5892a027187edc73a4b0979dc0561569303`.
- Integrated adapter SHA-256 is `8ba75a9a667867f500eb37c2d56f3f49637810de62e52b5177bd262b85f8408f`, matching `config/shiny_adapter.sha256`.
- Legacy `output/latest.json` still points to `output/2026-09-23/hierarchical_reference`.
- No request runtime directory or run lock is included in the release package.

## Operational limitation

A live Shiny browser session could not be started in this validation container because `shiny`, `callr`, `jsonlite`, `digest`, `htmltools`, and `zip` are not installed here. The non-Shiny R backend, PDF renderer path, adapter, static responsive UI, and D1 integration were executed. The target Windows acceptance sequence remains:

1. `ui/Setup.bat`
2. `ui/Verify.bat`
3. `ui/Start.bat`

The application should not be treated as deployment-approved until the live Shiny acceptance check succeeds on the target machine with its approved dependency set.
