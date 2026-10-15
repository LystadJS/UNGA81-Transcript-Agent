# Evidence-first diplomatic research readouts

**Engineering-only / offline / no publication authority.** The standalone Python 3.10+ standard-library renderer does not touch D1 O1–O5, the R/Shiny briefing application, the Outlook sender, shared browser entry points, or publication manifests. All examples are synthetic. No original UN text, private excerpts, protected holdouts, or reviewer labels are included.

## Contract and evidence states

- **Schema:** `un.diplomatic-readout.v1`; see [`schema.v1.json`](schema.v1.json). `readout.py` enforces additional relational and trusted-evidence requirements that JSON Schema alone cannot express.
- **Templates:** `emerging_themes`, `discourse_communities`, `changing_actor_profiles`, `boundary_cases`, and `source_backed_anomalies`. These are presentation categories, not tests of substantive political hypotheses.
- **Separate finding fields:** `observation` (literal descriptive source claim), `pattern` (explicitly exploratory, requiring statistical fit gate), `reviewer_interpretation` (requires separate reviewer release). A finding contains **exactly one** observation or pattern, not both.
- **Coverage disclosures:** population, period, unit, weighting, source-group unit, total inventory, eligible, excluded, missing, reasoned exclusion/missingness counts, planned/attempted/converged/failed/skipped fits, and unassigned/noise. Check: `total_in_frame = eligible + excluded + missing`; `planned_fits = attempted_fits + skipped_fits`; `attempted_fits = converged_fits + failed_fits`. These count partitions are explicit; they are **not** automatically verified against an upstream census.
- **Sources:** stable source ID, raw-original SHA-256, text SHA-256, raw-hash basis, versioned Unicode text representation, parent, meeting/speech/source-family identifiers (nullable where unverified), optional verified HTTPS URL/JSON pointer, original text length in Unicode code points. Unverified speech/country cannot be invented.
- **Evidence references:** supporting and contrary arrays contain exact source ID, text hash, representation ID, code-point start/end and matching JSON pointer. End offsets are exclusive. A source copy is authenticated against independently supplied original bytes; if JSON, its pointer must resolve to the exact versioned text. No original text or excerpt is serialized.
- **Contrary evidence:** `contrary_search` is `not_assessed`, `assessed_none`, or `identified`; absence of supplied contrary passages does **not** imply none exist. An unsupported finding is withheld rather than asserted.
- **Country attribution:** an independently adjudicated exact pointer and individual/collective mode must match the displayed claim. Collective-source text can never be presented as an individual national statement. Country affiliation alone is insufficient.
- **Stance:** requires a *specific proposition*, position, exact supporting pointer, matching proposition-text digest, and a separate adjudication; mere topic mention or cluster membership is insufficient. A verified expression is not automatically an official vote or whole-of-government policy.
- **Uncertainty, sensitivity, alternatives:** required at report and finding levels; limitations remain visible in every export.

### Trusted inputs, mandatory separation

The **authored report dict is untrusted**. Do not put `gates`, transcript strings, tokens, or unknown fields into it. The separate `SourceReceipt` provides authenticated read-only source bytes and the exact Unicode offset basis. The separate `ReviewDecision` binds the approved report digest and declares source, reviewer, privacy and statistical gates (`pass`, `fail`, `not_run`). The caller **must** obtain these receipts/decisions from accepted upstream validators and an actual reviewer; neither is produced by the renderer or inferred from report fields. In an unintegrated invocation, these are unavailable and the renderer withholds the result.

`report_digest(report)` is a canonical UTF-8 SHA-256 consistency check, **not a signature**. A caller could forge a `ReviewDecision`; the coordinator must enforce trusted provenance and authorization boundaries independently. `SourceReceipt.accepted` is similarly a typed downstream assertion, not proof that the source was accepted upstream. No claim of real-data calibration or independently authenticated human review is made by this module.

**Outputs:** `synthetic_demo` (fictional successful fixture), `descriptive_only` (verified source claim but no inferred pattern), `qualified_experimental` (non-synthetic, explicitly qualified after trusted research gates), or `withheld` (no authorized evidence). A withheld finding omits the original candidate text, country/stance, and raw pointer. Malformed, unreviewed, or privacy-failed input withholds all authored copy. `publication_eligible` is **always `false`**, irrespective of research status. This is not D1 or a production report.

## Run and reproduce (offline, no dependencies)

From the repository root:

```sh
python3 -m unittest discover -s research/diplomatic_readouts/tests -v
python3 research/diplomatic_readouts/examples/generate.py --output /tmp/unga81-synthetic-readouts
```

The generator writes ten deterministic cases (complete, partial, abstaining, failed source, missing evidence, and one of each template), each as JSON, Markdown and standalone HTML. It writes a `manifest.json` with SHA-256 for the exact public bytes. It refuses an existing nonempty/symlink target and never performs network requests. To replay, choose another **empty** output directory and compare manifests or `diff -rq` directories. Fixtures are fictional, seeded by immutable literals (no random draws), and use a synthetic JSON document with Unicode characters to test original-byte hashes and code-point offsets.

As a library:

```python
from readout import SourceReceipt, ReviewDecision, report_digest, validate, render, export
# Build SourceReceipt objects ONLY from authenticated original bytes and
# externally established metadata; obtain ReviewDecision outside this module.
errors = validate(report, proofs=trusted_receipts, decision=review_decision)
html = render(report, "html", proofs=trusted_receipts, decision=review_decision)
hashes = export(report, "/tmp/readout-001", proofs=trusted_receipts, decision=review_decision)
```

`export()` is no-overwrite and creates a fresh output directory; the caller controls paths. HTML uses a local-only content-security policy and escapes authored material; Markdown escapes HTML-like content. JSON exports contain source IDs/hashes and bounded pointers, **not bytes or quoted passages**. Unknown nested fields fail closed; a conservative 32-code-point verbatim-source overlap check can withhold text. This is a defense in depth, not a substitute for upstream human privacy review (short excerpts, paraphrases and other sensitive information are not automatically detectable).

## Limits and coordinator integration

See [`INTEGRATION.md`](INTEGRATION.md) for the required adapter and non-publishing path. A source hash match proves only equality to the **supplied** original bytes, not that those bytes were obtained from a trusted source. The renderer does not fit models, calibrate nulls, independently evaluate research, establish source-selection positivity, authenticate a human reviewer, or verify upstream population counts. It must not receive private originals in a public build or source-control fixture.

Do not treat similarity as agreement, clusters as coordination, distances as influence, temporal movement as realignment, missing sources as zero issue occurrence, or successful synthetic tests as scientific release readiness.
