# Daily UN briefing — D1 research pipeline

Current source includes the I5 extension: 12 executable adapters, 30 still
unimplemented, and six new audit-only lexical research methods. See the
[current implementation and roadmap](../docs/I5.md) and
[Windows acceptance](validation/i5/README.md). The Shiny interface supports
editable user topics; the fixed codebook described below is the legacy CLI
codebook. The following milestone notes preserve the imported I4 baseline.

**Release 2.5.0-d1-i4-checkpoint | R-native | local unsent Outlook drafts | 25 September 2026**

This checkpoint adds **M09 PAM / k-medoids** to the validated frozen TF-IDF analytical layer. Six D1 adapters are implemented: M01, M02, M05, M06, M07 and M09. The remaining 36 registrations remain explicitly unimplemented; all 42 methods and all 133 original prerequisites still receive daily accounting.

Both clustering adapters use the **same full frozen TF-IDF Euclidean-chord distance space**. M07 hierarchical clustering remains the primary clustering diagnostic; M09 PAM is a challenger with inspectable medoids. Neither is permitted to add an email section or publish country groupings. Their figures and assignments are audit-only.

The email contract remains unchanged: exactly five analytical outputs, followed by regional country readouts. Fixed topics remain **Iran, Cuba, Ukraine, AI**. Countries remain grouped by region and alphabetized within region.

## Quick start

Read [START_HERE.md](START_HERE.md), then run the normal Windows setup. For offline verification with the tested R runtime:

```sh
Rscript --vanilla tests/run_tests.R --minimal=true
Rscript --vanilla tests/run_d1_tests.R --minimal=true
Rscript --vanilla tests/run_i2_tests.R --minimal=true
Rscript --vanilla tests/run_hierarchical_tests.R --minimal=true
Rscript --vanilla tests/run_pam_tests.R --minimal=true
```

To reproduce PAM only from a trusted completed frozen-feature run:

```sh
Rscript --vanilla pam_only.R \
  --input=output/2026-09-23/hierarchical_reference \
  --output=output/pam_standalone \
  --minimal=true
```

No source collection, API call, feature refit, email send, or Windows scheduling occurs in that standalone command.

## Checkpoint findings

On the 39-speech inherited replay, PAM selects **k=2** with **22 and 17 countries**, with medoids **POL** and **BDI**. Mean silhouette is **0.015** and mean roster-deletion ARI is **0.717**, below the frozen release screens. Hierarchical clustering also fails its gates and yields a 38/1 average-linkage split. The adjusted Rand agreement between the two selected partitions is approximately **-0.012**. These differences support retaining both methods as diagnostics rather than labeling the groups as geopolitical blocs.

All five engineering/regression suites pass (**371 tests, zero failures**). See [validation/FINAL_VALIDATION.md](validation/FINAL_VALIDATION.md) and [docs/CLUSTERING_CHECKPOINT.md](docs/CLUSTERING_CHECKPOINT.md).

## Diplomat interface — dynamic tracked issues

This integrated checkpoint includes `ui/`, a Shiny front end intended for nontechnical users, and a pinned adapter at `interfaces/shiny_v1.R`.

The interface lets a user type up to 20 tracked issues. These issue definitions are immutable within a run and are applied as evidence-retrieval candidates after the D1 corpus is collected. They do **not** replace or mutate the legacy four-topic codebook used by archived CLI runs, and they do not create a released classifier. Non-matches remain unresolved rather than being coded absent.

The full eligible transcript corpus continues through D1 method accounting independently of the tracked issue list. Current-corpus clustering suggestions can appear in the interface as audit-only research candidates; D1 O2 remains the publication authority. The five-output boundary and no-send behavior remain intact.

Launch from `ui/Start.bat` after running the interface setup. See `ui/docs/INTEGRATION.md` and `validation/SHINY_CHECK.md`.
