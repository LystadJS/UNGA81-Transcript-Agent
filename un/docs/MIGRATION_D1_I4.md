# Migration to 2.5.0 D1-I4 checkpoint

1. Preserve the entire prior v2.4 hierarchical-only directory and its archives.
2. Extract this checkpoint into a new directory.
3. Copy only authorized local configuration values. Do not copy stale locks, active model/history directories, or secrets into a shared archive.
4. Run `scripts/Setup-Windows.ps1` so the local environment freezes actual installed versions, including `Matrix` and `cluster`.
5. Run `scripts/Test-Workflow.ps1`. It now includes the PAM suite.
6. Inspect `validation/FINAL_VALIDATION.md`, one hierarchical audit, one PAM audit, and the Outlook draft before changing a scheduled task.
7. Disable the previous scheduled task only after the new installation passes a nonempty live-day acceptance run.

The checkpoint does not migrate or reinterpret old cluster results automatically. Old archives remain reproducible with their original release.
