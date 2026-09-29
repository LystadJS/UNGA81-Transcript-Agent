# Security, dependencies, and operating limits

This is a local development prototype, not an accredited government application. It has no authentication, role-based access, centralized audit retention, administrator console, multi-node job queue, virus scanner, or deployment hardening. Do not expose the local Shiny port to a network or deploy it as a shared service without a separate security review.

The default launcher binds only to `127.0.0.1`. Child jobs use unique directories and a separate R process. Uploaded text is data: no source text is evaluated as R, shell, HTML, or prompts. Literal topic input is escaped rather than interpreted as regular expressions. Generated HTML escapes text; the app preview has a sandboxed iframe. Candidate CSV exports protect formula-looking text. ZIP intake prevents path traversal and bounded decoding limits simple oversized-archive cases; that is not malware scanning.

Transcripts and run artifacts remain on disk under `runtime/runs/` until the owner deletes them. Cancellation preserves partial files but does not offer them as a complete report. Local topic preferences are saved only after a user action and are visible to anyone using the same browser profile. An audit ZIP contains source material: review its contents and disclosure authorization before sharing it. No API key is requested or stored.

## Package requirements

The six app dependencies are `shiny` (minimum 1.8.1), `callr`, `jsonlite`, `digest`, `htmltools`, and `zip`. R 4.3+ is the stated minimum, but only R 4.6.1/Debian 13 was executed here. `cluster` supplies PAM and normally accompanies R's recommended packages; verify its availability on the installation computer. The reference backend does not require Python for text processing, geometry, matching, or email.

Setup installs through `UN_READOUT_CRAN` when configured, otherwise `https://cloud.r-project.org`. Use an approved repository and package installation process. Setup records actual versions in `config/packages-installed.local.csv`; it does not fabricate a prevalidated `renv.lock`. A reviewed and reproducibly restorable dependency lock is still required before deployment.

## PDF routes

Preferred: approved `pagedown` plus a local Chromium-family browser. That route was written but could not be executed here because the R package was unavailable.

Optional fallback: an already installed Python/Playwright environment plus a local browser. `scripts/print_pdf.py` was actually executed in this build. It downloads nothing, loads the generated self-contained HTML bytes, disables page JavaScript, blocks non-data resource requests, and verifies the output PDF signature. It is not needed when the R-native route works.

The container acceptance run explicitly used `UN_READOUT_BROWSER_NO_SANDBOX=1` because Chromium was executed in an isolated root-owned test container. **Do not set this variable on an ordinary workstation or institutional deployment.** User launchers do not set it. This test setup is not a recommendation to bypass browser or institutional protections.

## Remaining platform checks

Windows batch launchers, the native R PDF route, live Shiny input/worker interactions, cancellation, keyboard behavior, screen-reader usability, native Outlook rendering, and any managed-device controls need target-environment acceptance. Static screenshots and R syntax checks do not establish these behaviors.
