# Independent PR97 failure-control review

Candidate: `ab559b74842e9a9165bf619f4869015d90588e8c`.
Base: `da4ab9ed11dba3693d11aa12f5333963b1b85478`.
No adoption, merge, retargeting, protection changes, publication or real-source reads.

The 15 independent methods contain seven baseline/working-rejection controls and
eight must-reject regressions. At authoring, the exact source-copy execution passed
seven and failed eight, with no errors/skips. These are normal assertions, not
expected-failure decorators. Hosted exact-head/effective-tree evidence is pending.

The reviewer checks all seven gate code blobs, all member hashes in the original
successful artifacts, original native receipts and contrast outcomes. It separately
reconstructs the candidate, effective and combined Git trees using only Git
metadata plus the synthetic stage declaration, verifying all 31 pinned payload
paths and unchanged refs/controller index. No candidate tree helpers are used for
that independent reconstruction. Artifact run 38806920470 remains historical.
Original R/browser/product suites are not rerun or relabeled as fresh validation.
The original 30 gate-control methods are rerun without modifications.

Adversarial cases modify temporary copies only, preserving every outer identity:
missing build/manifest evidence; missing independent observations; explicit measured
contrast failure; explicit axe violation; wrong Phase1 native head; 999 native
tests versus 40 raw test IDs; replacement of the retained R1 test ID; and an
unreviewed fictional source-like .txt file in an otherwise permitted prefix.
The last test uses a separate toy repository containing no real transcript.

These tests concern completeness and cross-record consistency, not cryptographic
proof that arbitrary producer logs are truthful. No change to workflow authority
or trust settings is attempted. Gate adoption remains blocked pending independent
review disposition and repairs; ordinary PR code cannot create signed authority.
