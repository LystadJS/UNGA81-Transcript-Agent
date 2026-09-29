# UN Daily Briefing — Analytics Design D1

**Full backend. Exactly five analytical outputs in the email. Native-R design and contract checks.**

This package specifies the next architecture for the user's R workflow 2.1.0. It **does not replace that workflow, run the proposed models, create a task, call an API, or send an email**.

## Read first

`ARCHITECTURE_D1.md` is the complete design: five report products, all 42 registered methods, data/label/history gates, computational schedule, model release rules, source integrity, Outlook safeguards and acceptance criteria.

`docs/IMPLEMENTATION_MAP.md` maps the required changes to the actual inspected v2.1 functions.

## Contents

- `config/method_registry.csv` and `.json`: 42 named methods with R dependencies, schedule, readiness gates, roles and allowed email destinations.
- `config/email_contract.json`: exactly O1–O5; fixed topics and regional ordering; existing summaries preserved.
- `config/email_policy.R`: R-native policy object.
- `config/data_contracts.json`: proposed feature, label, snapshot, method-run, evidence and report-packet records.
- `config/dispatch_policy.json`: inference/refit/cache/resource design.
- `R/validate_contract.R`: implemented structural checks and five-slot bundle construction. It neither fits models nor renders EML.
- `tests/test_design.R`: synthetic structural acceptance/rejection tests; no country/model estimates.
- `validation/`: actual R parsing/test results and source-provenance hashes.
- `docs/SOURCES.md`: documentation/source register.

## Exactly five analytical slots

1. Fixed-topic monitor — Iran, Cuba, Ukraine, AI.
2. Emerging issues.
3. Country discourse map.
4. Rhetorical movement.
5. Discourse-network changes.

The executive takeaway and existing country summaries remain. Countries stay under Africa, Asia-Pacific, Europe & Eurasia, Near East, and Western Hemisphere, alphabetized within each. The original issue bars, heatmap and issue co-occurrence graph become audit-only in the proposed implementation.

A missing historical comparison does not become a zero. Unavailable outputs retain a concise reason. Additional methods never create additional email sections. Current-day text similarity is not automatically policy agreement or coalition membership.

## Run the design checks

From this directory with an installed R runtime:

```powershell
Rscript --vanilla .\tests\test_design.R .
```

Or on another system:

```sh
Rscript --vanilla tests/test_design.R .
```

No non-base R packages are required for these structural tests. The modeling dependencies named in the registry have **not** been installed or benchmarked by this design package. Successful design checks do not establish model accuracy, semantic validity, live-source success, or Outlook rendering.

**Actual development validation:** R 4.6.1; three scripts parsed successfully; 42/42 synthetic engineering checks executed successfully. See `validation/VALIDATION.md`.

## Deployment status

Design complete. Analytical adapters, model training, historical ingestion, five-slot EML integration and operational acceptance are the next implementation stage. Continue running the existing v2.1 installation until that new implementation passes its own acceptance tests. No current source or archive was modified.
