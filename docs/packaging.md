# Short-path ZIP validation

Archive: `un.zip` (top folder: `un/`).
Original archive SHA-256: `a265d47b120bb98b781b6dcb6e3ea95004f211b6d7debd5173eeb51ca695a4e2`.
New archive SHA-256: `55d078acde791091cf4fd1306929a233e757de728d1440df33eeb73b81e7517b`.

## Packaging and extraction

- All 2,279 original files retained; two path-guide files added.
- 1,702 files relocated or renamed beneath the shortened top folder.
- Longest archive path reduced from 245 to 186 characters.
- Extracted successfully with Windows .NET ZipFile into `C:\Users\John\AppData\Local\Temp\un-mvbrwalg`.
- Longest actual extracted path: 231 characters, below the legacy Windows limit.
- All 2,281 extracted file contents match their ZIP entries.
- ZIP CRC checks passed; no duplicate Windows names, unsafe paths, or reserved names.
- Recommended extraction parent: `C:\work`, or another path no longer than 60 characters.
- Start with `un\ui\Start.bat`; setup and verification launchers are `Setup.bat` and `Verify.bat` in the same folder.

## Integrity and references

- All 2,280 current root-manifest entries verified.
- All 78 UI manifest entries and all checkpoint key-file entries verified.
- All 10 applicable SHA-256 sidecars verified.
- All 1,697 serialized R data files preserved byte-for-byte and successfully read in R.
- All 2,567 checked immutable object references resolved with matching hashes.
- Core analytical R modules, Shiny backend modules, adapter, configuration and frozen policy bytes preserved.
- Updated code, scripts, documentation and text references to renamed paths; no old renamed tokens remain in scanned text, except the explicit rename map and original historical checksum inventory.
- Static checks covered 19 references to relocated files and 4 literal R source references that resolved in the original package. Dynamic paths are not exhaustively covered by static scanning; R object-reference and adapter checks supplement it.
- Content-addressed filenames and model keys retain their full hashes to preserve integrity checks.

## Runtime checks and limits

- R syntax: 62/62 files parsed successfully on R 4.5.3 for Windows.
- Python scripts: syntax parsed successfully.
- Shiny/D1 adapter: 9/9 tests passed.
- UI backend: 96/97 checks passed. The failing check was PDF creation: Windows could not start the detected Python launcher at `C:\Users\John\AppData\Local\Python\bin\python3.exe`. No PDF was generated in that test. The PDF implementation is unchanged from the supplied archive.
- Adapter/backend tests ran on the first repack extraction; final-package R files are identical to that tested build. The final follow-up changed a launcher label in the Python preview-generation script and the path guide, and refreshed manifests. Final ZIP extraction, checksums, path scans, Python parsing and R data-reference checks were rerun.
- Full inherited analytical regression suites and live browser acceptance were not rerun for this packaging change. Historical acceptance records remain historical.
- The preserved `SHA256SUMS_D1_I4_ORIGINAL.txt` records the upstream pre-integration checkpoint; its original paths and checksums are intentionally unchanged. Use the regenerated `SHA256SUMS.txt` for this package.

`PATHS.csv` inside the archive records renamed paths and changed text files. `PATHS.md` contains the extraction guide. The source ZIP and synced project references were not modified.
