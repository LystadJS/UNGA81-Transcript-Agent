# Daily operations

**D1-I1 note:** country-summary status and analytical-model readiness are distinct. Even an `AUTOMATED_CHECKS_PASSED` summary run has no released analytical producer in this milestone. Always inspect `audit/analytics/method_ledger.csv` and the five visible slot states. Exit 0 means the allowed workflow completed, not that all 42 models ran. The original three charts are audit-only. `history/` is append-only and must be backed up with the dated runs; see HISTORY_STORE.md.

## Scope and dates

The default live collector reads UN Transcripts, not media schedules. It filters for General Assembly general-debate meetings, uses available English structured transcripts, and retains exclusions. Individual country affiliation must match the versioned registry. It excludes institutional speeches and statements below `live.min_statement_words` (default 250); the exclusion ledger makes that choice inspectable. Long unresolved-affiliation records trigger review. All distinct retained interventions by the same country are combined into one country entry with original source parts preserved.

A day without any discovered in-scope meetings produces an **EMPTY** email. This means no matching items were found in the successfully retrieved inventory, not proof that no real-world event occurred. An in-scope meeting without a usable transcript is a source error, not an empty-day success. This release neither translates missing-language text nor transcribes video/audio.

The report date defaults to yesterday in America/New_York. A manual `--date` overrides it. `--lookback=3` means three separate dates ending at that date, processed oldest first. The Windows task's `-At` is the computer's local clock. Keep the clock/time zone correct; date derivation does not silently switch to UTC.

## Manual commands

From the project root after normal package setup:

```powershell
$rt = Get-Content .\config\runtime.local.json -Raw | ConvertFrom-Json
& $rt.rscript --vanilla .\doctor.R
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-Daily.ps1 -Source live
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-Daily.ps1 -Source live -Date 2026-09-23 -LookbackDays 3
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Open-Latest.ps1
```

The PowerShell launcher imports the DPAPI-protected API key for that process and restores the previous environment afterward. Calling R directly is also supported, but then the operator must supply `OPENAI_API_KEY` locally through an appropriate process environment.

## Exit codes and product status

| Exit/status | Meaning | Operator action |
|---|---|---|
| Exit 0 / `REPLAY` | Archived example passed generation checks | Do not treat it as new collection or fresh semantic review |
| Exit 0 / `EMPTY` | Successful inventory/input processing, no qualifying text and no recorded source errors | Check scope/date; no charts are embedded in the empty email |
| Exit 0 / `AUTOMATED_CHECKS_PASSED` | Available content passed programmatic and model checks | Still review before institutional distribution |
| Exit 2 / `REVIEW_REQUIRED` | At least one uncertainty, source anomaly, model hold/failure or provisional extractive result | Inspect the draft and audit; do not remove caveats to force a pass |
| Exit 2 / dated `FAILED.json` | A day failed; other dates may have completed | Read that date's logs/raw archive and rerun after correction |
| Exit 1 | Setup, argument, prerequisite or global lock failure | Correct environment/arguments; no scheduling until understood |

`generation.fail_on_review_required` defaults true. Turning it off changes process exit signaling, **not** the visible product status or evidentiary quality. Partial draft generation is separately controlled by `allow_partial_draft`; it defaults true so a source gap remains useful and visible. The workflow never automatically sends a partial or complete product.

## Model operations and costs

Fresh OpenAI mode performs a structured summary/issue-coding call followed by a separate review call. Same-model review is permitted but is not an independent human check. Source text, prompts, schemas, and responses are recorded. Full text over the configured bound is held rather than silently truncated.

Caching binds to source hashes, full analysis inputs, prompts, schemas, code version, and model settings. An unchanged speech normally reuses its cached result on a late-source lookback. Cache records are hash-checked and evidence-validated before reuse. A cache hit does not create fresh model review. Review holds are preserved and not automatically converted to acceptance.

The default budget is **120 logical model calls per invocation across all dates**, excluding cache hits. Usually two logical calls are needed per newly analyzed country. HTTP retries can add billable transport attempts; the logical call limit is not a monetary cap. Large first-time backfills should use shorter date windows or a deliberately reviewed budget. Token usage is written to `audit/model_usage.json` when responses provide it. Request failures/incomplete results may incur cost even when they do not yield accepted prose.

No API price or daily dollar cost is guessed here. Review your account's model access, rate limits and usage/billing settings. ChatGPT subscription billing does not cover API usage.

## Failures, late text, and locks

Every run creates a new immutable directory. Existing run IDs are rejected, not overwritten. Raw source objects use content hashes. `output/.run-lock/owner.txt` records the process, machine and start; the lock prevents simultaneous writers. A normal exit removes it. After a crash, **confirm the named process is not still running on that machine** before removing a stale lock. Never delete an active lock simply to force another run.

The task does not trigger automatic repeated retries of a review-required day. Bounded request retries occur within a run; the next daily lookback handles publication delays. Failed or held countries remain represented in the audit and, where possible, the email. Resume a failed live date by rerunning that date; cached validated responses avoid unnecessary repeat calls. `rebuild.R` is for completed archived runs, not an incomplete checkpoint recovery shortcut.

No retention deletion is automatic. Back up dated run directories, `cache`, exact code/assets, and the locally created `renv.lock`. Keep credentials out of archives intended for sharing. Do not delete raw evidence while retaining only polished prose.

## Windows scheduling

`Install-DailyTask.ps1` refuses an existing task name instead of overwriting it. Default execution is under your signed-in account with limited privileges. A locked session is acceptable. `-RunWhileLoggedOff` uses the same account and locally entered Windows credentials; DPAPI material from another account/machine will not decrypt. The registered task runs the PowerShell wrapper, which invokes the recorded Rscript executable.

Power/network availability and task permissions are machine-specific. Setup/Task Scheduler scripts have not been executed on Windows in this build environment. Review the task's history/last result during local acceptance. `0x2` can be the intentional review-required result; inspect logs. `-WakeToRun` is optional and depends on power settings. The task is not installed merely by extracting the package.

## Sources versus official records

UN Transcripts' automatic text can contain transcription, speaker, timing, or publication errors. Code/evidence checks can prove that a quote occurs in the archived text; they cannot prove that the transcript exactly reproduces the original speech or that a government's assertion is true. Preserve these distinctions in any distributed product.
