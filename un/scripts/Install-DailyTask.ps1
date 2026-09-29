[CmdletBinding()]
param([string]$At='08:00', [ValidateRange(1,14)][int]$LookbackDays=3, [string]$TaskName='UN Daily Briefing', [switch]$RunWhileLoggedOff, [switch]$WakeToRun)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) { throw 'A task with this name exists. Review/remove it explicitly or choose another -TaskName.' }
if (-not (Test-Path (Join-Path $root 'config\runtime.local.json'))) { throw 'Run Setup-Windows.ps1 first.' }
$parsedTime = [DateTime]::MinValue
if (-not [DateTime]::TryParseExact($At,'HH:mm',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::None,[ref]$parsedTime)) { throw 'Use a 24-hour time such as 08:00.' }
$script = Join-Path $root 'scripts\Run-Daily.ps1'
$arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $script + '" -Source live -LookbackDays ' + $LookbackDays
$action = New-ScheduledTaskAction -Execute "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -Argument $arguments -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settingsArgs = @{StartWhenAvailable=$true; MultipleInstances='IgnoreNew'; ExecutionTimeLimit=(New-TimeSpan -Hours 4)}
if ($WakeToRun) { $settingsArgs.WakeToRun = $true }
$settings = New-ScheduledTaskSettingsSet @settingsArgs
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
if ($RunWhileLoggedOff) {
    $cred = Get-Credential -UserName $user -Message 'Task Scheduler needs this account password for unattended network access. This is not your API key.'
    if ($cred.UserName -ne $user) { throw 'Use the same account that stored the DPAPI API key.' }
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($cred.Password)
    try {
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -User $user -Password $plain -RunLevel Limited -Description 'Generate local UN briefing drafts; do not send email.' | Out-Null
    } finally { $plain=$null; [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
} else {
    $principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Generate local UN briefing drafts; do not send email.' | Out-Null
}
Write-Host "Registered: $TaskName at $At in this computer's local time zone."
Write-Host 'Without -RunWhileLoggedOff, the account must remain signed in; a locked screen is acceptable.'
