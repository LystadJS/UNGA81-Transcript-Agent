# Troubleshooting

| Symptom | Inspect / action |
|---|---|
| R not found | Supply the actual `-RscriptPath` to Setup-Windows; do not rename a different runtime to look like the reference version. |
| Package download blocked | Check the reported CRAN/network error on the personal PC. Minimal replay remains available but does not enable live processing. Do not disable TLS verification. |
| `renv.lock already exists` | Use `-Restore`; do not silently replace a deployment lock with current packages. |
| Invalid API key / model access | Re-run Set-ApiKey locally, verify account access and configured model. No secret value is written in workflow logs. |
| External AI disabled | This is the safe default. Enable it only for authorized text, or deliberately select extractive mode. |
| Model call budget reached | Inspect coverage, cache and usage. Process a shorter date window or deliberately change the configured logical-call budget. Retries can incur additional costs. |
| Review-required exit 2 | Open the draft and `audit.html`; look for unknown codes, source anomalies, failed countries and model holds. Do not treat it as a fully verified product. |
| No current EML after a failed run | Inspect dated `FAILED.json`. Latest pointers are updated only after a structurally valid draft; they may still point to an earlier completed day. |
| EMPTY result | Check the requested date and default general-debate filters. This does not mean all UN activity was absent. |
| In-scope transcript missing | Preserve the error. Revisit through lookback or rerun that date later. Do not infer speech contents from a speaker schedule. |
| Unexpected inventory/detail schema | Upstream API may have changed. Raw responses remain archived. Repair and test the parser; do not skip identity/count checks. |
| Unresolved country | Inspect structured affiliation in the source. Add a reviewed exact alias to the registry; do not infer from a person's name. Preserve this as a new registry version. |
| DOCX rejected | Supported layout has a Date line, resolvable country filename and a `Full Speech Text` heading in ordinary body paragraphs. Arbitrary layout/PDF/OCR is not implemented. |
| Stale `.run-lock` | Verify PID/host/time and that no process owns it. Remove only after proving it stale. Concurrent generation is intentionally blocked. |
| Rebuild code hash mismatch | Restore the matching workflow release. Do not edit the archived manifest to force acceptance. |
| Rebuild bytes differ | Compare R version, platform, fonts, preparation timestamp and packages. The report explicitly records byte differences. |
| Outlook artifacts | Use `daily_briefing.eml`, not the raw HTML source or raw MIME text. Inspect CID images, Unicode and widths. A browser pass is not a native Outlook guarantee. |
| Task does not run signed out | Default task is interactive. Re-register deliberately with `-RunWhileLoggedOff` under the same account that stored the DPAPI key. |
| Task result `0x2` | May be intentional review-required status; inspect the run log rather than repeatedly launching it. |

## Optional native-R browser check

With `chromote` installed during setup and a compatible local browser:

```powershell
$rt = Get-Content .\config\runtime.local.json -Raw | ConvertFrom-Json
$latest = Get-Content .\output\latest.json -Raw | ConvertFrom-Json
& $rt.rscript --vanilla .\scripts\check_browser.R $latest.run
```

If browser discovery fails, set `CHROMOTE_CHROME` to the actual browser executable in the current PowerShell process. The script tests 390, 720, 1280 and 1600 px views and saves screenshots/metrics. It does not test the Microsoft Word-based Outlook renderer. Perform the Outlook-native inspection separately on the Windows machine.

## Asking for help without exposing secrets

Provide `validation/doctor.json`, the relevant run log, `validation.json` or `FAILED.json`, and a screenshot of the visible issue. Remove authorization data or restricted speech content from any files before sharing. Never provide `.secrets`, API keys, Windows account passwords, or a full environment dump. Raw source/model archives may contain the texts you processed; share only what you are authorized to share.
