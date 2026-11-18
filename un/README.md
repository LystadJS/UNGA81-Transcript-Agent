# Personal R briefing and research workflow

The current package has 12 executable adapters among 42 registered methods.
Additional registrations are plans, not operational methods. The Shiny interface
accepts tracked issues as evidence queries; they do not create an accepted stance
classifier. Read the [method boundary](../docs/I5.md) and
[installation guide](START_HERE.md). The government-browser application is
separate and needs no R or Python installation.

## Start and verify

Use R 4.3 or newer and the package's dependency setup. The personal runtime and
its locked dependencies belong on the user's computer, outside version control.
On Windows, follow `scripts/Setup-Windows.ps1`, then `ui/Setup.bat`, `ui/Verify.bat`
and `ui/Start.bat`. The pinned adapter and publication/no-send gates are unchanged.

Run offline checks in a separate checkout or copy because they write validation
receipts. From this `un` directory:

```sh
Rscript --vanilla tests/run_tests.R --minimal=true
Rscript --vanilla tests/run_d1_tests.R --minimal=true
Rscript --vanilla tests/run_i2_tests.R --minimal=true
Rscript --vanilla tests/run_hierarchical_tests.R --minimal=true
Rscript --vanilla tests/run_pam_tests.R --minimal=true
Rscript --vanilla tests/run_i5_tests.R
Rscript --vanilla tests/run_shiny_adapter_tests.R
```

Matrix, cluster and igraph are required for the applicable numerical checks;
minimal mode is not a substitute for those dependencies. Live Shiny and PDF checks
have separate dependencies and acceptance records. A successful Linux offline run
does not establish Windows or live-interface acceptance.

Generate a fresh local replay from retained inputs when checking the whole CLI:

```sh
Rscript --vanilla run_daily.R --source=replay --date=2026-09-23 --run-id=my_replay --minimal=true
```

Choose a new run ID each time. Outputs remain local and unsent. Review source,
coverage and publication status before circulation. Scientific gates remain in
force even when engineering tests pass.

## Generated runs and historical references

`output/`, caches, history, models and installed libraries are runtime state and
are not shipped as application source. The original replay inputs, frozen feature
fixtures, policies and original checksum records remain. Source/report provenance
is not rewritten.

The former generated runs and three obsolete I4 checkpoint-freezing scripts are
preserved in [commit ea18ad8](https://github.com/LystadJS/UNGA81-Transcript-Agent/tree/ea18ad83b030e10abfb32d2525c17ada5f5939b9/un).
Historical scripts assume six adapters and must not be used to certify the current
12-adapter implementation. Their historical receipts remain dated evidence.

For an old frozen-run audit, restore that commit's `un/output` into a separate
folder. From an existing full Git checkout, create the ignored `review-work`
directory, then export without altering the current checkout:

```sh
git archive --format=zip --output=review-work/frozen-r-output.zip ea18ad83b030e10abfb32d2525c17ada5f5939b9 un/output un/validation/checkpoint_audit.R un/validation/finalize_checkpoint.R un/validation/write_manifest.R
```

Extract the ZIP outside the source package. Set `UNBRIEF_ARCHIVED_RUN` to the
restored completed replay directory before running `tests/run_tests.R` to include
its two optional frozen-run checks. Without that variable, those checks explicitly
report not executed. Tests never discover archives through a user's mutable
`output/latest.json`. Runtime differences must fail closed; do not refit a frozen
reference merely to make a gate pass.

## Package integrity

`SHA256SUMS.txt` describes the current tracked package. Maintainers stage intended
package changes, then run `python tools/package_checksums.py --write` from the
repository root; the default command checks rather than writes. Runtime files are
excluded. The ORIGINAL checksum inventory and I4 checkpoint manifest are immutable
historical records, not current file counts or fresh acceptance.

The [previous package README](https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/ea18ad83b030e10abfb32d2525c17ada5f5939b9/un/README.md)
retains the original I4 findings and commands. Current entry points above supersede
those historical setup/output assumptions.
