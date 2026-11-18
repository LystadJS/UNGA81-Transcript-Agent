# Start the personal R application

The personal application targets Windows 11 with R 4.3 or newer. It runs separately
from the JavaScript-only public reporting workspace and never sends email
implicitly. Read [the current package guide](README.md) for method and storage
boundaries; an executable adapter is not an accepted substantive classifier.

## Installation

Install the normal pipeline dependencies through the existing package controls:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Setup-Windows.ps1
```

Then run `ui\Setup.bat`, `ui\Verify.bat` and `ui\Start.bat`. Retain the generated
`renv.lock` and use the recorded R executable/library rather than silently upgrading
a frozen environment. Neither runtime libraries nor personal outputs belong in
Git. Follow [the UI guide](ui/START_HERE.md) for generation and cancellation controls.

## Daily drafts

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-Daily.ps1 -Source live -Date 2026-09-24
```

Replace the example date with an eligible completed reporting date. Review the
unsent EML, HTML/plaintext, source evidence and coverage before circulation. The
interface can use explicit user topics; the archived CLI codebook remains a
separate legacy contract.

For offline verification, run the commands in [README.md](README.md) in a separate
copy. Frozen example inputs remain; historical generated output runs are retrieved
only when explicitly requested. The main tests do not read personal `output/latest.json`.

## Archived clustering

`hierarchical_only.R` and `pam_only.R` remain available with explicit `--input`
and `--output` paths. They require a trusted completed frozen-feature run produced
by a compatible runtime, and do not send email or refit TF-IDF. Restore an old
reference using the archive instructions in README.md; do not assume an old
output directory is bundled in the current source tree.
