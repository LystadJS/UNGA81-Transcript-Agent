# I5 Windows acceptance — 29 September 2026

Executed with R 4.5.3 on Windows 11 x64. Tests used a disposable short-path
copy with local model references; I5 tests used synthetic fixtures explicitly
for engineering verification. Imported model artifacts were not migrated or
rewritten. Logs in this directory are current executions; workspace paths have
been abbreviated to `<workspace>`.

| Suite | Passed | Failed |
|---|---:|---:|
| Base regression | 93 | 0 |
| D1 accounting | 94 | 0 |
| Frozen TF-IDF / PCA / PCoA | 101 | 0 |
| Hierarchical clustering | 58 | 0 |
| PAM | 33 | 0 |
| Shiny adapter | 9 | 0 |
| New I5 methods | 71 | 0 |
| Total | 459 | 0 |

All 64 R files parsed. Shiny `testServer` acceptance passed generation with a
real separate worker, duplicate-click prevention, cancellation, and session
disconnect cleanup. This is server/controller acceptance, not a browser or
native Outlook visual acceptance test. The QA library supplied the missing
`zip` package without changing the user's main R library.

The I5 tests cover deterministic computation and restored random state,
resource/input limits, isolated and empty graphs, known network metrics,
source/reference bindings, save/reload stability, independent recomputation,
and rejection of forged gates and publication eligibility. The base suite now
checks strict Base64 rejection with the optional library installed. Its archive
test explicitly verifies rejection when the inherited reference environment is
incompatible; the new frozen-analysis suite separately tests valid fresh-local
outputs. No runtime integrity gate was relaxed.

PDF rendering, complete browser interaction, live-source collection and native
Outlook rendering are not certified by these results. No email was sent. The
six I5 adapters remain audit-only regardless of test success; 30 registered
methods remain unimplemented. M31 does not supply stance/event layers and M36
does not supply temporal comparisons.

## Full source-backed replay

The 23 September archived replay completed successfully with 39 country
statements, 42 accounted methods, 133 prerequisite checks and exactly O1–O5.
Final structural/MIME/output validation passed; an unsent EML was generated.
This does not establish semantic accuracy or native Outlook rendering.

| New method | Replay outcome |
|---|---|
| M08 k-means | Quality-withheld |
| M31 lexical network | Executed, audit-only |
| M32 Louvain | Quality-withheld |
| M33 Leiden | Quality-withheld |
| M34 spectral | Blocked: isolated nodes; roster not silently reduced |
| M36 snapshot metrics | Executed, audit-only |

`replay_methods.csv` is a status extract from the completed run, not a replacement
for its full artifact archive. `replay_qa.json` contains the final validator
result. The disposable run's full feature/model artifacts were not added to Git.
The inherited source fixture remains in `un/examples/2026-09-23/`.

Replay command, from the disposable package directory:

```text
Rscript run_daily.R --source=replay --date=2026-09-23 --config=config/config.example.json --run-id=i5_acceptance
```
