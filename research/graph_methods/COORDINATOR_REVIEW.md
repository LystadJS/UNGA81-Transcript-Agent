# W3 / PR #16 — coordinator merge-review handoff

**Disposition:** engineering review candidate; keep draft and unmerged until
the W3 ownership exception is resolved. W1 was merged into main as an
engineering source-aware validator at commit
87dedd6ee7b30fb7cd1e26e8ef26e30ee8e52329 (PR #19). Actual W1↔W3
synthetic interoperability has passed on GitHub PR merged-tree CI; private
development-data validation and scientific release remain separate withheld
gates. Do not inspect the 37 reserved October 5–6 transcripts.

## Baseline and file boundary

- Repository: LystadJS/UNGA81-Transcript-Agent
- Worker branch: feat/graph-based-learning; PR #16
- Original branch base: main at 773ecc90310d674905889441491937b8a13a3515
- Read current PR head SHA and every changed path from GitHub just before merge
- Changed namespace: research/graph_methods/**, plus uniquely named
  .github/workflows/graph-based-learning-research.yml
- No changes to D1 M34, existing numerical/browser workers, shared schema,
  research/corpus, frozen reference/evaluation lock, un/, O1–O5 release gates,
  site release manifests, or the website mirror

## Coordinator acceptance ledger

| Gate | Result | Evidence and condition |
| --- | --- | --- |
| Standalone graph methods | PASS engineering | Weighted exact kNN, spectral, and transductive diffusion algorithms |
| Synthetic known-structure and adversarial tests | PASS newly executed | 59 W3 + bridge tests on accepted-W1 PR merged-tree checkout, plus source/integrity refusal cases; inspect latest head before approval |
| Graph quality and numerical sensitivity | PASS synthetic | Eigenvalues/gaps/residual, components, isolates, hub degree, duplicate/tied observations, neighborhood/kernel/alpha/time/dimension sweeps |
| Source group resampling | PASS synthetic | Whole-meeting omission with planned/succeeded/failed denominators; not confidence coverage |
| W3 v1 interchange | PASS synthetic | Original row IDs, hashes, full observed/excluded/missing frame, explicit not-fitted/unassigned states |
| Source-bound private output | PASS synthetic | Reject checkout paths; private directory 0700, JSON exclusive owner-only 0600; real inputs NOT RUN |
| Existing source/browser regressions | PASS on CI head | PCA/LSA, clustering, stability, NMF/GMM/HDBSCAN/MDS, latent comparison, reviewed units, passage, parallel v1 tests |
| W1 Node API in PR merged-tree checkout | PASS synthetic | Merged PR #19 available on main; W3 bridge invokes W1's real validateFrame, grouped meeting schedule, validateRelational and evaluateAssignments |
| Cross-W1 metrics on matched invented sources | PASS synthetic | 24 eligible / 1 unavailable; exact paired source hashes, one verified upstream model, independent ARI/AMI references, failure and hash-tampering refusals. CI text-free artifact: w1-w3-interoperability.json |
| Cross-W1 metrics on authorized *real development* sources | NOT RUN | Requires actual source/representation cache, coordinator-supplied approval record and private output location |
| Held-out or nuisance-calibrated cluster significance | NOT RUN / WITHHELD | Requires separately authorized scientific protocol |
| Browser release and D1 integration | NOT APPLICABLE | No existing site, D1 or release file modified |
| Exclusive ownership | EXCEPTION | User-requested graph_methods/ and unique CI conflict with coordinator OWNERSHIP.md's reserved W3 prefix and coordinator-owned CI |
| Merger | BLOCKED for coordinator decision | Do not merge on green fixture CI alone |

## Conditional W1 integration interface

W1 PR #19, now merged on main, supplies the Node API:
- frame.cjs: validateFrame and group-preserving source schedules
- metrics.cjs: evaluateAssignments / adjustedMutualInformation / compareFits
- interchange.cjs: versioned v1 export and relational validation

The W3 Python module w1_bridge.py uses those **real merged W1** interfaces.
PR merged-tree CI has verified the synthetic cross-language pathway, including
native frame validation, group schedule, independent ARI/AMI, original
source/selection/identity checks and refusal cases. On a standalone W3 branch
checkout without main's merged W1 files, the bridge still fails closed.
For a real authorized development source, provide a coordinator-authored local
approval record with:

~~~json
{
  "schema": "un.w1-approval.v1",
  "accepted": true,
  "adapter_version": "source-validation-1.0.0",
  "w1_producer_code_sha256": "64 lowercase hex digits from accepted runner.cjs",
  "w1_merged_commit_sha": "40 lowercase hex digits of verified GitHub merge commit"
}
~~~

The adapter verifies W1 producer code SHA-256 and `git merge-base --is-ancestor`
against the declared merge commit in a full-history checkout. The coordinator
must still approve the local record and confirm original source/model hash
lineage; the record is not a signature. The above placeholders are not usable
approval values.

After approval and private setup, the local comparison command is:

~~~sh
python -m research.graph_methods.reproduce \
  --input-manifest /private/w3-frame.json \
  --vectors /private/w3-vector-matrix.npz \
  --w1-envelope /private/w1-evidence.json \
  --w1-approval /private/w1-approval.json \
  --w1-model-id verified-pca-pam-model \
  --output /private/w3-source-bound-review
~~~

An accepted W1 comparator is invoked via actual installed Node interfaces,
not a Python reimplementation. W3 verifies exact upstream source/schema/hash
basis/selection, ordered eligible and excluded original ID+text SHA identities,
parent/meeting/source family/date/source offset and source status, and missing
inventory denominators; requires matching model representation ID and version;
checks the authoritative v1 JSON Schema and W1 relational invariants; and
retains W1's ARI/AMI, native source-frame/group-schedule audit, and
both-assigned/opportunity denominators without reinterpretation.
A failure refuses the comparison. The missing/unavailable
frame is not zero evidence. W1 model data are never used to override a failed
graph fit or to release W3 results.

**Limit of matching:** identical representation ID/version is a declared model
identity, not a full independent byte verification of a fitted transform or
encoder. A source/basis verification by upstream W1/MiniLM validators remains
mandatory; otherwise the comparative claim is withheld. Different geometry
cannot be quietly treated as the same metric space.

## Scientific limitations

This is a graph of *constructed textual geometry*. A diffusion coordinate
shows a random-walk relationship in that geometry, not political influence,
policy transfer or causal diffusion. Spectral partitions depend on the
chosen kernel, kNN graph, and feature representation. Eigenvectors can rotate
in degenerate subspaces. There is no accepted out-of-sample Nyström transform;
source-group deletion is descriptive sensitivity, not independent replication
or null-calibrated evidence. Recorded country affiliation is not verified
speaker identity, a vote, a stance, or an alliance. No model can promote a
source-unavailable/missing transcript to absence of an issue.

## Coordinator sequence

1. Re-fetch main and PR #16, verify changed paths, current base/head SHA,
   artifact hashes, source privacy and all Actions job conclusions on that head.
2. Approve the explicit W3 namespace/unique-CI exception in a coordinator-owned
   decision record **or** relocate W3 files into the original ownership prefix.
3. Confirm W1 merge SHA 87dedd6ee7b30fb7cd1e26e8ef26e30ee8e52329
   remains an ancestor of the PR test checkout and verify its Node code hash.
   Review W1's unsupported un.passage-frame.v1 interchange enum; no
   cross-schema relabeling is permitted.
4. Inspect the newly executed native W1-W3 synthetic interchange receipt,
   its code/input digests, original 25-row missingness ledger and independent
   ARI/AMI comparison; check the deliberate rejection tests.
5. Validate any later authorized real development data privately under W1's
   original source/meeting dependence contract, without opening the
   37 reserved transcripts or claiming inferential discovery.
6. Coordinator alone merges after ownership approval, integrates accepted
   methods with active browser workers, updates release manifests, and later
   mirrors a separately verified public build.

Recommended coordinator disposition now: **engineering review-ready, W1/W3
synthetic interoperability verified, real private-source comparability and
scientific release withheld, W3 ownership exception unresolved; leave PR #16
unmerged until that coordinator decision.**
