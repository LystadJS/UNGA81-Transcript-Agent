# Coordinator-only interchange → evidence-first readout adapter (synthetic v1)

**Scope:** New, offline, explicitly synthetic-only coordinator integration candidate. No production import, Shiny/Outlook, D1, shared browser, release manifests, website, private transcripts or automatic publication. Worker PR #70 is a pinned, *unmerged* dependency (source module at `028e3d26f707401cbff498593ab27f64e2cc072a`), not vendor-copied or edited here. All new adapter/tests/docs remain inside `research/integration/diplomatic_readouts/**`; the separate new CI workflow is coordinator-owned.

## Contract and trust boundaries

1. **Accepted structure, not accepted evidence.** Consume exactly `un.parallel-analysis.v1` / contract v1.x. Validate against the immutable official `docs/parallel-work/interchange-v1.schema.json` from the same checkout using pinned `jsonschema`, then independently audit observation/model/evidence identity, missingness, fit, representation and failure invariants. `publication_eligible:false` and `evaluation_role:'engineering_only'` are hard requirements. The producer envelope, country label, cluster ID or UMAP geometry cannot self-authorize findings.
2. **Trusted upstream validation is out-of-band.** `UpstreamValidation` binds the canonical **UTF-8 JSON digest** of the exact input envelope, source schema, original-source aggregate hash basis/hash, and selection hash. It must be supplied by the coordinator *after independently running upstream validators*. The class and hashes are **not cryptographic signatures** or authentication of UN originals. A signed or protected source registry remains required before genuine diplomatic evidence is attempted.
3. **Approved material is out-of-band.** The coordinator supplies `readout.SourceReceipt` objects containing private original bytes, their canonical text representation, provenance, reviewed parent, meeting/speech/source-family identity, HTTPS URL and JSON pointer. The bridge checks actual SHA-256 text hashes, parent-text hash, decoded/JSON-pointer reconstruction, Unicode code-point bounds and evidence identity; it does not fetch or read source files. All accepted receipts remain in memory, never in JSON/HTML/Markdown output. Sources without a compatible original text basis are refused. This intentionally excludes arbitrary reviewed excerpt transforms, which require separately versioned offset reconstruction.
4. **The bridge cannot issue authorization.** `prepare(...)` returns an *unapproved Candidate*, including its authored report, private in-memory proofs and aggregate census. It does **not** construct `ReviewDecision`. Running `readout.normalize(candidate.report, candidate.proofs, None)` always withholds the result. A real reviewer/privacy authority and a separate accepted null/dependence/statistical method gate must supply an exact-digest-bound `ReviewDecision`. The demonstration alone constructs a **fictional** reviewer decision in `examples.py`, only to test the target renderer.
5. **Synthetic-only lock.** Only `cohort.split == 'synthetic'` AND `producer.fixture_kind == 'synthetic'` are accepted. `development`, empirical source frames, genuine votes/country positions, real source annotations and the reserved 37 meetings are refused even when caller-supplied booleans look valid. This is **not** a general production adapter.
6. **No invented positions.** The intent may contain independently reviewed descriptive observations or explicitly experimental language; country attribution and stance must be null. Any national/proposition-specific inference, `assessed_none` contrary claim, ambiguous evidence role, incomplete supporting span, missing source or source-group/representation mismatch is withheld before candidate generation. A descriptive source reference does not imply official agenda adoption, vote or whole-of-government stance.
7. **Do not confuse denominators.** `un.parallel-analysis.v1` distinguishes eligible/excluded observation rows from inventory. The bridge retains native fit ledger and derives display counts as: `eligible = native eligible`; `missing = unavailable rows + unobserved inventory`; `excluded = native excluded − unavailable rows`; `total_in_frame` remains the declared inventory. It discloses a **deterministic primary exclusion reason** (multiple source reason tags are not double-counted); missing source is never zero issue occurrence. Distinct fit planned/attempted/converged/failed/skipped and unassigned remain distinct. Output model selection is explicit; the renderer does not refit or infer unobserved cells.

## Inputs and outputs

- `bridge.prepare(envelope, intent, proofs, validation, readout_module=readout)` returns a `Candidate(report, proofs, envelope_sha256, population_audit)` or raises `Withheld(<safe fixed code>)`. No private text is included in the exception or report.
- `intent` is a **closed** authoring object with report title, template, model ID, finding proposals and required uncertainty, sensitivity and alternative-explanation notes. Finding evidence binds by observation ID to a **unique** native `evidence[]` representative/contrary record (verification must be `synthetic`) and inherits exact text hash, representation, JSON pointer and code-point spans. No raw draft passages or authenticated status fields are accepted. Free prose remains unapproved until a reviewer explicitly authorizes an exact report digest.
- `SourceReceipt` and `UpstreamValidation` are private trusted-host inputs. Their types are not certificates on their own and can be forged in a hostile process; do not accept them from HTTP bodies, project files, notebooks or web forms in any operational adapter.
- JSON, Markdown and HTML are generated *only* by the separately pinned readout module. No network, email, automatic publication or file-system writes occur in `prepare`.

## Reproduction, synthetic only

Run in a full repository checkout with the **unmodified** PR #70 module available under `research/diplomatic_readouts` (the coordinator workflow checks out that exact SHA in a separate directory and adds it to `PYTHONPATH` without committing it).

```sh
python3 -m pip install jsonschema==4.26.0
PYTHONPATH=research/diplomatic_readouts:research/integration/diplomatic_readouts \
  python3 -m unittest discover -s research/integration/diplomatic_readouts/tests -v
PYTHONPATH=research/diplomatic_readouts:research/integration/diplomatic_readouts \
  python3 research/integration/diplomatic_readouts/examples.py --output /tmp/unga-bridge-a
PYTHONPATH=research/diplomatic_readouts:research/integration/diplomatic_readouts \
  python3 research/integration/diplomatic_readouts/examples.py --output /tmp/unga-bridge-b
diff -rq /tmp/unga-bridge-a /tmp/unga-bridge-b
```

Native upstream source/interchange regressions are run independently by the read-only coordinator CI workflow pinned to the current `main` source contract. These prove **synthetic interoperability**, not field-level provenance in any real UNGA transcript, temporal replication, statistical identification or authorization for government positions. No original-source, held-out, Shiny, Outlook, public browser or deployment test is claimed.

## Metadata-only source registry preflight (synthetic v0; no authority)

See [REGISTRY_PREFLIGHT.md](REGISTRY_PREFLIGHT.md), [registry_preflight.py](registry_preflight.py), and the portable input/output v0 schemas. This separate, standard-library-only preflight accepts a fictional source inventory snapshot, fictional custody-intent metadata, a checked-at UTC timestamp, an internally consistent synthetic audit chain, and the existing **unapproved** `un.private-source-authorization.proposal.v0`. It revalidates source and selection digests, exclusion/unavailable denominators and audit/custody scope; its digest chaining is **not** authentication of an actual custodian or revocation feed. It cannot read original bytes, issue reviewer or statistical decisions, grant access, or change the 37 reserved meeting lock.

```sh
python3 -m unittest discover -s research/integration/diplomatic_readouts/tests -v
python3 research/integration/diplomatic_readouts/examples_registry.py --output /tmp/registry-preflight-a
python3 research/integration/diplomatic_readouts/examples_registry.py --output /tmp/registry-preflight-b
diff -rq /tmp/registry-preflight-a /tmp/registry-preflight-b
```

Seven invented scenarios include a consistent but **unauthorized** metadata packet and six withheld/refused cases. All **13** private-source, actual reviewer, statistical identification, protected holdout and D1 statuses remain `NOT_RUN`; output is aggregate-only and `publication_eligible=false`. No source URL, private passage or row-level UN data is included. Do not treat a synthetic-consistent receipt as a real-source permission token.

## Coordinator handoff, not part of this PR

For a subsequent separate integration proposal, perform an official contract-version/schema pin, independently validate original byte/text and selection identities on an approved private host, join source groups and representation lineage against W1/W2/W4 accepted outputs, verify actual human labels and proposition-specific stance under the quick-reader rules, independently establish all applicable statistical and privacy gates, and regression-test D1 O1–O5, Shiny, non-send Outlook and browser replay before *any* operational use. Engineering validation must not change a frozen gate or be used as scientific or publication authority. **Do not merge or publish either PR automatically.**

## Synthetic custodian-signature and independent revocation simulation

See [SYNTHETIC_CUSTODIAN_SIGNATURES.md](SYNTHETIC_CUSTODIAN_SIGNATURES.md) for the Ed25519 custody/revocation trust model, two portable closed schemas, 56 signed-metadata negative/positive tests, ten source-free examples, and a bounded median/p95 benchmark. Publicly reconstructible **test-only keys** verify cryptographic binding and deny access on tampering, revocation, expiry, rollback, wrong signer, or policy confusion. Even valid signatures produce `authority=none`, 13 `NOT_RUN` gates, `authorized=false`, `can_read_source=false`, and `publication_eligible=false`. This is **not** an operational PKI, access authorizer, private-source fetcher, or publication producer.
