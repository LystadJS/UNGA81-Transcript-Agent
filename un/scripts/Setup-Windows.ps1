[CmdletBinding()]
param([string]$RscriptPath='', [switch]$WithBrowserChecks, [switch]$Restore)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $RscriptPath) {
    $cmd = Get-Command Rscript.exe -ErrorAction SilentlyContinue
    if ($cmd) { $RscriptPath = $cmd.Source }
    else {
        $candidates = Get-ChildItem "$env:ProgramFiles\R\R-*\bin\Rscript.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending
        if ($candidates) { $RscriptPath = $candidates[0].FullName }
    }
}
if (-not $RscriptPath -or -not (Test-Path $RscriptPath)) { throw 'Install R, then provide -RscriptPath "C:\Program Files\R\R-4.6.1\bin\Rscript.exe".' }
$RscriptPath = (Resolve-Path $RscriptPath).Path
$argv = @('--vanilla', (Join-Path $root 'setup.R'))
if ($WithBrowserChecks) { $argv += '--with-browser=true' }
if ($Restore) { $argv += '--restore=true' }
Push-Location $root
try {
    & $RscriptPath @argv
    if ($LASTEXITCODE -ne 0) { throw 'R package setup failed. Review the error; no schedule was installed.' }
    # Record the exact executable selected by the user rather than a guessed R.home executable suffix.
    $rtPath = Join-Path $root 'config\runtime.local.json'
    $rt = Get-Content $rtPath -Raw | ConvertFrom-Json
    $rt.rscript = $RscriptPath
    $rt | ConvertTo-Json | Set-Content $rtPath -Encoding UTF8
} finally { Pop-Location }
Write-Host 'Native R setup complete. No Python installation is required. Run Test-Workflow.ps1 next.'
