# Start here — D1 clustering checkpoint

**Release:** 2.5.0-d1-i4-checkpoint. **Target:** Windows 11 with R. Daily analysis remains R-native; Python is not required.

This checkpoint adds PAM to the existing hierarchical clustering audit. Both are deliberately excluded from the five reader-facing analytical slots.

## Install

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Setup-Windows.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-Workflow.ps1
```

Setup installs and freezes the normal workflow dependencies plus `Matrix` and `cluster`. Preserve the locally generated `renv.lock` after acceptance.

## Run a daily draft

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-Daily.ps1 -Source live -Date 2026-09-24
```

Use a completed reporting date. The output is an unsent Outlook EML plus HTML/plaintext and a full audit archive. Review before institutional distribution.

## Audit clustering from an archived frozen feature run

```powershell
$rt = Get-Content .\config\runtime.local.json -Raw | ConvertFrom-Json
& $rt.rscript --vanilla .\hierarchical_only.R --input=PATH_TO_RUN --output=PATH_TO_NEW_HC_AUDIT --minimal=true
& $rt.rscript --vanilla .\pam_only.R --input=PATH_TO_RUN --output=PATH_TO_NEW_PAM_AUDIT --minimal=true
```

The commands require a trusted M02 artifact created by a compatible release/runtime. They do not send email or refit TF-IDF.

See `docs\MIGRATION_D1_I4.md`, `docs\CLUSTERING_CHECKPOINT.md`, and `validation\FINAL_VALIDATION.md`.
