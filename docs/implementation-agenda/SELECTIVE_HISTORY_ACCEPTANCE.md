# Selective historical evidence: source-free acceptance

Status: source-free Node acceptance passed; actual-browser CI acceptance pending. All records in these tests are fictional. No private database was written, actual source row read, transcript downloaded, reserved meeting opened or scientific model accepted.

## Required parity

Downloading selected policy/year/body shards must produce the same issue-report country roster, policy observations, current country counts, source coverage and exact-date U.S. comparisons as querying the full equivalent snapshot. A country with evidence only on another policy, or a recorded affiliation with no extracted position, remains in the selected report's Unknown denominator. Selecting a topic must not select away its unknown countries.

The independent compact roster contract is `{date, body, family, countries, source_count}`. It is policy-independent. Report source coverage uses these exact-date aggregates once, or unique source identities when no compact roster is provided; it must never add both. Identical roster rows repeated across loaded shards are counted once. Official documents and votes cannot establish statement-opinion denominators or statement source counts.

Exact partial-year dates remain authoritative even though transport shards are grouped by year. General Assembly selection includes plenary and GA_C1–GA_C6, while an individual committee excludes plenary, other committees and Security Council sources.

## Tests

`tools/test_issue_report.cjs` includes the existing report safeguards plus an independent full-versus-selected fixture. It checks policy-independent Unknowns, coverage parity, repeated source and observation invariance, repeated compact roster invariance, both ten-year endpoint dates, GA committee hierarchy, and official-document/vote separation. The fixture deliberately includes an excluded previous-day source and an excluded following-day source in endpoint years.

Method provenance checks require compatible ontology/extractor pairs for an exact comparison. Distinct extractor versions on the same source/stance cannot disappear through duplicate removal. Known-versus-legacy and differing extractor pairs must display `method_version_gap`. A matching known pair preserves observed direction. A known unsupported ontology is withheld from current position counts rather than treated as the same policy object. Version strings document provenance; they do not authenticate source truth or establish empirical model validity.

`tools/test_issue_selective_ui.cjs` is a dedicated actual-browser CI test with five tiny fictional shards. The UI must request only the selected SC access shard and its independent SC roster, omit the other policy and GA shards, reproduce the full-fixture report, and preserve the frozen result/filters/provenance through save and reopen. It also rejects an overlong topic before manifest retrieval and preserves the prior report. It produces no screenshot or bulky output. Browser dependency installation is outside this test and was not performed locally.

## Execution record

- Existing report safeguards: passed on the initial implementation tree.
- New full-versus-selected parity test: initially failed as intended against the pre-integration report. Selected loading removed France and Ghana from the roster, shrinking the comparison denominator from four countries to two, and reduced 2026 source coverage from four sources to two. The report integrator was notified; this is a release gate until corrected.
- Browser test syntax check: passed. Actual browser execution: not run in this worker; CI execution is required before browser acceptance is claimed.
- After integration, `node tools/test_issue_report.cjs` passed all existing and new assertions, including visible legacy and method-gap notices.
- `node tools/test_issue_history_client.cjs` passed selective/full retrieval, independent roster, body hierarchy, endpoint years, byte limits, legacy fallback, immutable subset identity, cache integrity and cancellation checks.
- Independent review found and corrected two additional integration defects: legacy shards without roster metadata were being represented as authoritative empty rosters, and duplicate removal discarded differing extractor versions before compatibility assessment. The client now distinguishes absent from explicitly empty roster metadata; report duplicate identity includes method versions.
- The dedicated browser case is wired into the existing meeting quick-reader workflow after archive UI acceptance. Its execution remains a CI release gate; syntax validation alone is not browser acceptance.

This document records engineering acceptance only. Successful fictional tests do not certify historical source completeness, deployment, public data permissions, owner-confirmed labels, calibrated trajectory estimates or scientific readiness.
