# I8 acceptance - 30 September 2026

Freshly executed on Windows:

| Suite | Passed |
|---|---:|
| Neural methods, reloads and boundary checks | 41/41 |
| Method/runner/gate accounting | 7/7 |
| Existing R research kernels | 43/43 |
| I7 R research extensions | 55/55 |
| Dataset-review tools | 31/31 |
| **Total** | **177/177** |

Python research/tools sources compiled successfully. The isolated neural
installation passed its dependency consistency check. The offline demo trained,
saved and reloaded both methods with exactly matching predictions. Model
weights and input fixtures remain local and ignored by Git; only numerical
summaries, code and test evidence are committed.

The neural tests check actual encoder weight updates, held-out loss versus
prevalence, a matched last-observation baseline, independent calibration,
country/content/time leakage rejection, future-availability rejection, padding
and batch-order behavior, test-label independence, safe serialization, reload
identity, checkpoint tampering, token/resource limits, immutable outputs and
hashing of the exact consumed input bytes. Network connections are denied in
the local checkpoint and prediction acceptance tests.

These are tiny fictional engineering fixtures, not diplomatic benchmarks. The
M16 marker task is deliberately easy. Its masked-language-model checkpoint lacks
a classifier and pooler; the documented warning is retained, and both are then
trained along with the encoder. No approved natural-language model is claimed.
M38 uses a GRU, not a transformer; its synthetic performance does not establish
real historical forecasting ability or production resource requirements.

`methods.py` confirms 42 registered methods, 12 daily adapters, 27 R research
kernels, two Python research kernels, and M26 unresolved. Original prerequisite
lists and non-publication flags are checked. Research methods still refuse real
or unreviewed data. Nothing under `un/` changed; no daily replay, Shiny browser
or native Outlook acceptance was rerun or claimed.

See [I8 implementation and next steps](../../I8.md), `summary.json`, `runtime.json`,
`demo.json` and the suite logs. Trailing log whitespace and local workspace/temp
path prefixes are normalized; test results and warnings are retained. Earlier
I6/I7 evidence remains historical and is not relabeled as this run.
