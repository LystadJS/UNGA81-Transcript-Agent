[CmdletBinding()]
param([ValidateSet('live','local','replay')][string]$Source='live', [string]$Date='', [string]$InputPath='', [ValidateRange(1,14)][int]$LookbackDays=1, [string]$ConfigPath='', [switch]$Minimal)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$runtimePath = Join-Path $root 'config\runtime.local.json'
if (-not (Test-Path $runtimePath)) { throw 'Run Setup-Windows.ps1 first. For zero-dependency replay, run Rscript run_daily.R --source=replay --date=2026-09-23 --minimal=true directly.' }
$rt = Get-Content $runtimePath -Raw | ConvertFrom-Json
if (-not $ConfigPath) { $ConfigPath = Join-Path $root 'config\config.json' }
$secretFile = Join-Path $root '.secrets\openai_api_key.dpapi'
$oldKey = $env:OPENAI_API_KEY
$exitCode = 1
$logDir = Join-Path $root 'logs'; New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ('run_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
try {
    if (-not $env:OPENAI_API_KEY -and (Test-Path $secretFile)) {
        $secure = Get-Content $secretFile -Raw | ConvertTo-SecureString
        $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try { $env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
    }
    $argv = @('--vanilla', (Join-Path $root 'run_daily.R'), "--source=$Source", "--config=$ConfigPath", "--lookback=$LookbackDays")
    if ($Date) { $argv += "--date=$Date" }
    if ($InputPath) { $argv += "--input=$InputPath" }
    if ($Minimal) { $argv += '--minimal=true' }
    Push-Location $root
    try { & $rt.rscript @argv *>> $log; $exitCode = $LASTEXITCODE }
    finally { Pop-Location }
    Get-Content $log -Tail 20 | Write-Host
} finally { $env:OPENAI_API_KEY = $oldKey }
if ($exitCode -eq 2) { Write-Warning 'One or more dates need review; a local draft may still exist. See output\latest.json and the audit.' }
elseif ($exitCode -ne 0) { Write-Error "Workflow failed. Inspect $log" -ErrorAction Continue }
exit $exitCode
