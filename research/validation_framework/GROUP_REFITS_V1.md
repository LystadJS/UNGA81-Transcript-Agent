# W1 source-bound child-fit assignments — versioned interchange v1

**Status:** engineering-only, opt-in hard-assignment export. Does not change canonical un.parallel-analysis.v1, existing numerical fits, W1 default output, publication eligibility or frozen evaluation gates.

## Purpose and native opt-in

The original W1 grouped-stability records retain sampled source IDs, seed, status and ARI/AMI summaries, **but no child hard labels**. Summary metrics cannot reconstruct W2 pairwise co-assignment numerators and denominators. The new native opt-in records the **actual hard labels** while each numerical grouped refit runs.

~~~js
const W1 = require('./research/validation_framework/runner.cjs');
const I = require('./research/validation_framework/interchange.cjs');
const G = require('./research/validation_framework/group_refit_interchange.cjs');

const fitted = await W1.run(authorizedFrame, settings, {
  saved: approvedSavedRepresentation,
  group_units: ['meeting'],
  replicates: 18,
  fraction: 0.8,
  group_seed: 31,
  retain_group_assignments: true
});
const originalV1 = I.toInterchangeV1(fitted);
const childSidecar = G.fromNative(fitted, originalV1);
G.validateSidecar(childSidecar, originalV1);
~~~

Actual child labels reside in a **nonenumerable internal property** named _internal_group_refits. Native public W1 summary JSON, normal JSON serialization and original W1 interchange remain unchanged. No original transcript text, vectors or annotations are included. Retention beyond **120,000** possible fitted source-observation opportunities is rejected, never silently truncated. W1 retains its existing 600-eligible observation ceiling; W2's dense pair matrix remains capped at 256.

## Sidecar fields and invariants

- **Schema:** un.source-aware.group-refits.v1; structural reference in schemas/group-refits.v1.schema.json. The canonical coordinator interchange v1 remains unchanged.
- **Immutable source identity:** upstream source schema/hash basis, original source SHA and selection SHA, W1 runner SHA, observation ID/text SHA, parent/source-family/meeting IDs, source URLs, JSON pointers, Unicode offsets and unavailable/excluded source records. Missing source text is not interpreted as missing discussion.
- **Fit identity:** actual method and model identity, original representation/version, original and actual-refit parameter SHA, an **actual child training-selection SHA over sorted sampled observation ID/text-hash pairs**, actual refit seed and a deterministic settings+source replay key. The replay key is **not a checksum of the refitted feature matrix**.
- **Source-group sampling:** original W1 schedule SHA and selected union-group indices are checked against W1 native fit records. Source meetings must be fully included or excluded; within-speech fragments must remain linked to the same source group.
- **Status and denominator:** hard labels are 1+ for assigned, 0 for unassigned/noise, and null for not fitted. The export retains all selected source IDs/hashes, attempted/successful/failed/skipped optimizer counts and explicit failures.
- **Sampling design:** exactly one omitted source meeting is leave_group_out; multiple omitted source meetings are group_subsample **without replacement**. W1 does not run a group bootstrap. Repeated identical selected group sets share a resample ID, while their independent numerical seeds remain separate.
- **Distinct grouping units:** existing W1 affiliation/parent-closure refits are not reinterpreted as meeting-level resamples. Any other W1 grouped designs present in the native object are listed as not_exported_group_units.

The validator rejects missing or duplicate identities, altered source hashes, invalid offsets/parent lineage, source-group splits, incorrect label/noise/null status, inconsistent fit/failure counts, model/representation mismatch, and group-design/seed/schedule mismatch. Coordinator consumers additionally compare a supplied sidecar against the **actual W1 retained child labels**, so a modified-but-plausible numeric cluster label is not accepted based only on a self-reported checksum.

## Privacy and uncertainty boundary

The public exporter refuses development data by default. Its explicit allow_private_development option requires prior authorization and a separate private file-writing environment. The API does not authorize publication of source-linked row records or access to the 37 reserved October 5–6 transcript texts.

Group omission is **descriptive sensitivity**, not independent-source replication, statistical significance, a confidence interval, or a valid null reference. Repeated affiliations, shared source families, meeting type, boilerplate and hyperparameter searches remain material uncertainties. Source-text similarity never establishes official positions, alliances, causality or diplomatic agreement.

## Synthetic reproduction

Requires Node.js 22 and no extra dependencies. From the repository root:

~~~bash
node --test research/validation_framework/tests/test_group_refits.cjs
node --test research/integration/w1_w2/test-grouped-refits.cjs
node research/integration/w1_w2/make_grouped_synthetic.cjs /tmp/new-w1-w2-group-refit-reports
~~~

Tests exercise actual grouped numerical fits, independence of method seed from source-group selection, complete source identifiers and missingness, intentionally insufficient source groups, 10-group subsampling, failed/corrupt fit refusals, deterministic restart/replay and no raw text/vectors.
