# UNGA81 Transcript Agent

Integrated UN transcript analysis and Shiny readout interface, with the USUN
executive email theme and Windows-friendly package paths.

![Interface preview](un/ui/validation/interface_desktop.png)

## Start on Windows

Clone or extract this repository into a short location such as `C:\work\unga81`.
The application is in **un/**. Keep this path short for the saved model files.

1. Install R 4.3 or later.
2. Open `un/ui/Setup.bat` to install the interface's declared dependencies.
3. Open `un/ui/Start.bat` to launch the local Shiny interface.
4. Choose dates and topics, generate a readout, inspect the evidence, and save an unsent draft.

For the full D1 pipeline setup, use [un/START_HERE.md](un/START_HERE.md).
The [UI guide](un/ui/START_HERE.md) explains input modes and setup.
The [read-only preview](un/ui/Interface%20Preview.html) is included for local viewing.

## Included

- Native R D1-I4 analytical pipeline, publication gates, and exactly five email outputs.
- Shiny interface with editable topics, source evidence, coverage, and draft exports.
- USUN seal, navy/red palette, and local outline icons.
- Replay fixtures, frozen model/reference artifacts, inherited validation and tests.
- [Path mapping and extraction notes](un/PATHS.md) and current file checksums.

## Validation status

Windows ZIP extraction and checksums passed. All 62 R files parsed, all 9 Shiny
adapter checks passed, and all 2,567 checked saved-data references resolved.
The backend passed 96/97 checks; PDF creation failed because the local Python
launcher could not run. Desktop and mobile theme previews passed layout checks,
and the Shiny UI constructor rendered. Full Shiny startup for the theme update
remains unverified because the local R installation lacked the `zip` package.

See [packaging validation](docs/packaging.md) and [theme validation](un/ui/THEME.md).
Inherited acceptance records describe their original runs, not a new full
regression run for this repository import. No email is sent automatically.

## Reproduction and provenance

[REPRODUCE.md](REPRODUCE.md) describes this checkout. The source package is the
latest short-path, themed `un-ui.zip` build. Package checksums are preserved
in `un/SHA256SUMS.txt`; `.gitattributes` prevents checkout line-ending conversion
from invalidating them. Keep API keys and local runtime configuration out of Git.

Earlier repository documents are preserved in [docs/legacy](docs/legacy).
They describe earlier deliverables; this import does not include the separate
September 28 execution bundle mentioned in the old reproduction document.
