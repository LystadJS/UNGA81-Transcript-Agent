# Windows path update

Extract un.zip into a short folder (for example C:\work); open un\ui\Start.bat.
The longest archive member path is 186 characters, including un/. Keep the
extraction parent path at 60 characters or fewer for legacy Windows tools.
Setup and verification launchers are un/ui/Setup.bat and un/ui/Verify.bat.
The RStudio project is un/un.Rproj. See PATHS.csv for the rename map.

Content-addressed SHA-256 filenames, model scope keys, serialized R objects,
source archives, and frozen analytical policies retain their original bytes.
Their complete hashes are required by the integrity checks. Descriptive parent
folders and selected documentation/launcher filenames have been shortened.

Code, documentation and text path references were updated where needed.
SHA256SUMS.txt and ui/PACKAGE_MANIFEST.json describe this repackaged build.
SHA256SUMS_D1_I4_ORIGINAL.txt is preserved verbatim as historical evidence of
the pre-integration checkpoint; its paths and hashes are intentionally original.
Other inherited test results describe earlier runs, not new acceptance results.
See the separately delivered validation report for checks performed on this ZIP.
