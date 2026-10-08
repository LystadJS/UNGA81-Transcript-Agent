# Roster-adapter publication verification — 8 October 2026

The previous GitHub write-access blocker is resolved. The exact ten-file validated
patch is committed remotely in [PR #10](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/10)
as `6d59c9b07bc0db754bc84a87abfb4f133bed9708`, based on
`ab7273d37f8fcff9870f257084cc8fd1dcda7876`.

The publication-pending language in `ROSTER_ADAPTER_REVIEW.md` and
`ROSTER_ADAPTER_VALIDATION.json` describes the earlier local-only session. Those
historical files are deliberately preserved byte-for-byte. This receipt supplies
the subsequent remote-publication evidence rather than rewriting prior results.
The PR records the final merge state and any subsequent checks.

## Exact source verification

All 40 file digests in the supplied archive manifest and the ZIP integrity check
passed. Reversing the supplied patch reconstructed the exact Git blob preimages of
both modified documents; patch application checks passed. Each of the ten uploaded
Git blob identities equals the corresponding packaged source file. The remote
base-to-patch comparison contains exactly ten paths, 850 additions and no deletions.
No temporary installer, encoded transport bundle, private input or model artifact
was committed.

- Supplied ZIP SHA256: `51fedb70cbf2d0ca4b3545d78adfd5422b557a39710e5026be84a0abc2a680e3`.
- Supplied patch SHA256: `b1aa0281fa2b88a56467467be14a811709e17fbd3a7b4d50fed17d15b904e291`.
- Exact patch tree: `e45271801b73d89a5d5e3096b9a36cdf12a4002c`.
- This publication receipt is the only addition beyond the validated ten-file patch.

## Fresh GitHub CI, distinct from inherited local acceptance

All three initial pull-request workflows completed successfully for the patch
commit before this documentation receipt was added:

| Workflow | Verified run | Outcome |
|---|---|---|
| Roster adapter and dependency controls | [37770101087](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/37770101087) | PASS |
| Development-only controls and synthetic evaluation | [37770101058](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/37770101058) | PASS |
| Nuisance reference contract | [37770101215](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/37770101215) | PASS |

The roster workflow executed **35 independent adapter checks**, with zero failures
and zero blocked-network attempts, and **69 reference/dependency Python tests**,
with no failures or skips. The log records Node 22.23.3 and Python 3.13.15.
Its separate parser/eligibility integration conserved all **37 fictitious meeting
slots**: 34 successful, two unavailable and one failed source. The strict artificial
population contains 220 passages from 216 source segments in 27 meetings.

Artifact `11546479304`, `roster-adapter-evidence`, was downloaded and its GitHub
SHA256 (`75396d33081e7b8de016b1c72f5363742426b1945b630c8148435117a3a8ea0b`)
and ZIP integrity independently verified. Its `adapter-tests.json` and
`parser-integration.json` agree with the job log and source contract.

## Preservation and interpretation

The CI integration explicitly records `NOT_RUN_MODEL_NOT_PROVIDED` for full-model
inference. Private saved development arrays and model weights were not uploaded
to GitHub. The earlier two full local inference runs remain historical evidence;
they are not presented as new executions in this publication step.

All **37 real reserved transcripts remain unopened**. The tests read only the
already-frozen roster metadata and use fabricated responses through the in-memory
transport. No live UN availability check, reserved-source collection, holdout
inference, model refit, human confirmation or scientific release is performed.

The sealed evaluation lock, original source frame, reference implementation,
model implementations, `site/`, `un/`, prior human decisions and publication gates
are unchanged. There are no public application-asset changes and no portfolio
mirror deployment is required. Publication closes the repository-delivery gap;
it does not resolve missing verified agenda/speaker metadata, authorize reserved
source access, or establish political alignment.
