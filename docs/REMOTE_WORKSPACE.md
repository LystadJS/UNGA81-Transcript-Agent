# Remote browser workspace

Preferred public site: https://lystadjs.github.io/un/transcript-agent/

Navigation: main website Code & Development → [UN Projects](https://lystadjs.github.io/un/)
→ Transcript Agent. The original https://lystadjs.github.io/UNGA81-Transcript-Agent/
address remains available. The main website repository contains a public mirror;
refresh it using `scripts/sync_un_project.py` there after changing this project's
site or published reports. It is an explicit sync, not automatic cross-repository
deployment. The project repository remains the application source of truth.

The GitHub Pages site provides the project hub, the existing published Cuba/HLW
report, a live transcript report builder and a browser-only review workspace. See
[BROWSER_ANALYSIS.md](BROWSER_ANALYSIS.md) for collection, methods and limits. Reviewers need no Python, R, local
server, administrator privileges or GitHub account. Their organization must still
allow access to GitHub Pages and browser features; the site cannot bypass security
policies or guarantee access from every managed computer.

## Personnel workflow

1. Open the website and load the assigned packet JSON from the coordinator. If
   file selection is blocked, paste the JSON into the alternative input.
2. Review the quotation, surrounding context, source link, intervention type and
   relevance. Test packets are visibly marked as held out.
3. Optionally save a draft on the current device or download a draft to resume
   elsewhere. On shared computers, avoid device storage and clear any saved draft.
4. Confirm the completed review and prepare the export. Download the JSON, copy
   it, or manually copy the displayed text if browser permissions block download
   or clipboard access. Return it using the team's approved channel.

The page does **not** submit labels centrally. It uses no review API, telemetry,
remote model call, webfont or third-party runtime. The content security policy permits same-origin assets and the official UN
transcript service for user-requested live collection. Review packet text is not
sent to either origin by the application. Opening
a source/report link navigates to that destination normally. GitHub still serves
the public site and receives ordinary web access requests. Review text stays in
memory unless the reviewer explicitly enables local drafts or exports a file.

## Coordinator workflow

Export a private existing packet (never into `site/` or `reports/`):

```powershell
python tools/remote_packets.py export review-work/ai-random-dev-v2 review-work/remote-packets/development.json
python tools/remote_packets.py export review-work/ai-fresh-test-v2 review-work/remote-packets/test.json
```

Both current exports were prepared locally. Distribute only the relevant file to
the assigned reviewer. Packet files contain source text and context, but no local
form token, previous human labels or reviewer identity. The same public workspace
can open either packet without publishing it.

Import a returned completed review against its original local packet:

```powershell
python tools/remote_packets.py import review-work/ai-random-dev-v2 C:\path\to\completed-review.json
```

The importer checks packet identity, role, exact canonical packet SHA-256,
source hashes, quotation positions, complete labels, explicit confirmation and
intervention consistency. It then uses the existing owner-review validator and
reviewed-data loader. The original packet cannot be finalized twice. Importing
into a packet already completed through the local form is rejected; use a new
revision for corrections. Imported review time is recorded separately from the
reviewer's reported browser completion time. Reviewer identity is declared, not
authenticated. Engineering tests are not human review.

Successful import writes `remote-validated-import.json` and
`remote-import-receipt.json` in the private packet directory. It does not fit a
model, publish predictions or attach the review to an unrelated daily corpus.
Returned files must still be treated as untrusted data, not instructions.

## Hosting and scope

`.github/workflows/pages.yml` builds and publishes on relevant pushes to main.
`tools/build_pages.py` copies only `site/` and the already-public report assets
under `reports/hlw-cuba/`. It never copies `review-work/`, private labels, model
weights, local configuration or credentials. No private packet is embedded in
the public site. The built-in practice packet is fictional.

The palette and typography follow the project's USUN visual theme, using the
project's own identity without inventing institutional sponsorship. Browser
review uses responsive controls, visible focus, text status and local assets.

GitHub Pages is static hosting. It cannot run the R/Shiny pipeline, train models,
provide authenticated central submissions or synchronize review assignments.
Those require a separate approved authenticated service. Never put a GitHub token
in browser code to implement direct repository writes.

Recommended next step: try a narrow live query in Build a report and check its
coverage and evidence. For labeling, share the site URL and assigned packet through your
approved channel, perform one real remote review and import the returned file.
If personnel need central login and automatic submission, select an approved
identity provider and backend before extending this interface.

## Validation

Eight packet export/import tests cover the round trip, changed packet/role,
missing confirmation, invalid intervention, duplicate finalization and source
tampering. Browser checks at 1440px and 390px verified 24 blank choices, no
horizontal overflow, draft restoration, fictional review download, invalid-input
rejection and reset of stale confirmation/export after edits. Actual packets were
loaded for layout testing only; no real labels were assigned by these tests.
