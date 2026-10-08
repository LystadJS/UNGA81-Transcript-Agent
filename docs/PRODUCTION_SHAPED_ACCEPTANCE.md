# Production-shaped synthetic acceptance and nuisance-sensitivity follow-up — 8 October 2026

**Status: ENGINEERING ACCEPTANCE WITH MATERIAL HOLD — DO NOT OPEN THE RESERVED 37 MEETINGS.** This change exercises the real saved-development parsing/review/inference machinery using *fabricated* transcript JSON. The 37 reserved transcripts from 5–6 October 2026 were **not fetched, opened, encoded, searched, or scored**. The SHA256-sealed historical evaluation lock and all daily publication gates are unchanged. A synthetic pass does **not** authorize real held-out access or establish diplomatic political alignment.

## Production-shaped acceptance

`research/reference_tests/synthetic_un_fixture.cjs` deterministically generates 37 fictitious meeting records dated **2099-01-05**, with fake slugs under `synthetic_fixture_`, inert UN-shaped URL strings, and 34 fabricated JSON responses, two unavailable inventory entries, and one simulated retrieval failure. A separately generated fake future frame sentinel satisfies the original source contract's development-vs-holdout shape; it is **not** a 38th tested meeting or a real reserved meeting. The generator contains no HTTP client. All text is artificially authored to test classifications and is *not* UN speech.

The fixture calls unchanged `research/corpus/contract.cjs`: metadata inventory checks, response byte hashes, exact video/date identity, nested sentence pointers, language/timestamp flags, source segments, contiguous Unicode partitions, and per-meeting status accounting. `production_synthetic.py` independently re-derives the corpus using the unchanged source validator and calls unchanged deterministic provisional machine classification. It never creates speech IDs, human confirmations, or corrected affiliations.

With the **saved** lexical TF-IDF vocabulary/IDF/SVD64, the **pinned** MiniLM ONNX 384-dimensional encoder, the frozen semantic PCA64/centroids, and all locks verified, the full local trial completed:

| Synthetic stage | Verified local output |
|---|---:|
| Fabricated meeting status rows | 37 (34 collected, 2 unavailable, 1 failed) |
| Preserved UN-shaped source segments | 442 |
| Exact partitioned passages | 412 |
| Strict machine-only passages | 220 |
| Observed strict source segments | 216 in 27 meetings |
| MiniLM inference | 29,621 WordPieces in 220 chunks, none truncated |
| Frozen centroid predictions | 220; no refitting |
| Synthetic text/source-family overlap with saved development | 0 |
| Raw primary comparison dimensions | Lexical 64D vs. raw semantic 384D |
| Historical dry-run decision | Inconclusive: some collected meetings lack eligible source segments |
| Production-shaped raw-384 synthetic gate | Inconclusive for the same coverage reason |

The raw-384 simulation had 0.4605 mean shared cross-meeting neighbors and 0.0738 conditional null mean (999 draws). The **synthetic** nominal p-value was 0.001, Holm-adjusted 0.002; those numbers describe only deliberately fabricated language and **cannot** be treated as real held-out replication. Exact output files were byte-for-byte identical across two complete local CPU runs. The synthetic gate correctly withheld a verdict despite the artificial numerical signal because ineligible/foreign-language/press-only meetings were not silently removed from coverage.

**Previously undetected engineering mismatch:** The historical `holdout_dryrun.py` requires two 64D input matrices. The frozen scientific metric compares 64D lexical geometry with **raw 384D semantic geometry**. This release retains the original file and lock, explicitly labels the legacy 64D result as a *projection proxy*, and adds a separate synthetic-only raw-384 calculation with the same 15 cross-meeting neighbors, 999 blocked permutations, country-label secondary calculation, Holm correction, effect floor and coverage gate. It is **not** a validated real-source evaluator. A separately authorized future implementation must use the correct raw input, enforce the actual 37-row roster, and undergo pre-access engineering approval.

## Genre, role, institutional language and speaker-proxy controls

`nuisance_stress.py` operates exclusively on the original saved strict **1,641 passages / 523 observed source segments / 16 meetings**. It independently reconstructs cross-meeting 15-neighbor retrieval from saved high-dimensional lexical and semantic vectors. Conditioning changes the eligible retrieval population, therefore the figures below are **sensitivity diagnostics, not causal adjustments or comparable p-values**:

| Exclusion imposed in addition to the same-meeting exclusion | Queries with 15 eligible neighbors | Lexical–semantic neighbor overlap |
|---|---:|---:|
| None | 523 / 523 | 39.4% |
| Same recorded genre | 523 / 523 | 34.6% |
| Same recorded actor role | 523 / 523 | 42.9% |
| Both same genre and same role | **326 / 523** | 39.5% among retained queries only |

An affiliation+function metadata proxy exists for 517 source segments; **91 proxy values occur in multiple meetings**, and 4.59% of neighbor pairs with both proxies recorded share that proxy. **This is not a verified unique person identifier**; a national delegation or office can have multiple speakers. Do not use it to claim genuine speaker recurrence or to remove repeated persons. Literal formula flags additionally document institutional language concentration (e.g. “thank you” in 486/523 segments and “human rights” in 346/523). These are string indicators, not speaker IDs or ideological labels.

### Corrected country-name alias sensitivity — separate v2, old result unchanged

The original saved 687-name mask matched the ambiguous generic word `island` **32** times and `Thai` **6** times in strict-development text. The explicit, versioned **v2 sensitivity** removes just those two aliases (685 remain). Original source text, prior 3,330-replacement mask, results, saved model weights and human/machine labels are immutable. Of the 1,641 passages, **1,607** had byte-identical v1/v2 masked text and reused previously hash-verified v1 embeddings; just **34** needed new ONNX inference (5,291 WordPieces in 34 chunks; zero truncation). The 1,641 passage identities and all parent IDs are unchanged; the v2 transformation neither fitted nor tuned any model.

| Same recorded-country share among 15 raw-semantic neighbors | Value |
|---|---:|
| Original unmasked | **9.11%** |
| Original saved v1 mask | **3.76%** |
| New v2 conservative alias sensitivity | **3.78%** |

The 0.02-percentage-point v1/v2 change does not materially affect the original conclusion: explicit country wording is a substantial nuisance, while remaining same-country association does not demonstrate policy agreement. This mask still omits many demonyms, institution names, grammatical variations, and context-dependent references. No new hypothesis test or comprehensive geopolitical-entity redaction is claimed.

## Readiness disposition

**HOLD for real held-out evaluation.** Supported engineering controls now cover synthetic raw-source status/identity checks, exact partitioning, machine-only eligibility, frozen model inference, no-refit predictions, source leakage and deliberate unavailable/failed/novel-genre scenarios. The fake test cannot validate changes in the real upstream schema, actual availability, missingness in reserved text, or ability to enforce real roster/source substitutions under a production collection interface; the latter interface remains intentionally unavailable. Missing genuine speaker IDs, incomplete human boundaries, severe genre imbalance and uncertainty about substantive-null exchangeability remain.

**Do not weaken the original 37-meeting lock or revise old p-values retrospectively.** Before future authorized real evaluation, first build a separately reviewed, read-only-to-until-approved production input adapter that checks roster and date identities from the sealed metadata, rejects unexpected source families, and records each collection failure without suppressing it. Its authorization and substantive review are **separate** steps. Failure of any locked coverage gate means *inconclusive*, never silent resampling or model tuning.

## Reproduce (no holdout access)

From repository root with Python 3.13, Node 22 and the existing pinned semantic dependencies:

```bash
python -m unittest discover -s research/reference_tests -p 'test_*.py'
python research/reference_tests/production_synthetic.py synthetic-review-only.json
python research/reference_tests/production_synthetic.py synthetic-with-encoder.json \
  --saved-development-models /path/to/UN_machine_review_results \
  --saved-semantic-models /path/to/UN_semantic_comparison/results \
  --pinned-local-encoder /path/to/verified-MiniLM-model
python research/reference_tests/nuisance_stress.py \
  /path/to/UN_machine_review_results /path/to/UN_semantic_comparison/results \
  /path/to/development-controls/evidence/masked new-v2-output \
  --pinned-local-encoder /path/to/verified-MiniLM-model
```

The source-authenticated model weights and development checkpoint are separate private conversation files, not stored in this public repository. Repository CI runs schema/integrity tests and other existing suites but does **not** download transcript content or claim it reran real ONNX inference without private local inputs. All user-delivered row-level vectors/alias audit remain outside the public GitHub tree.
