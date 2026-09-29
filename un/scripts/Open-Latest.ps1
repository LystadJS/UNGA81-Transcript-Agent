[CmdletBinding()]
param([switch]$Html, [string]$Date='')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if ($Date -and $Date -notmatch '^\d{4}-\d{2}-\d{2}$') { throw 'Use -Date YYYY-MM-DD.' }
$index = if($Date) { 'output\latest_' + $Date + '.json' } else { 'output\latest.json' }
$latest = Get-Content (Join-Path $root $index) -Raw | ConvertFrom-Json
$path = if($Html) { Join-Path (Join-Path $root $latest.run) 'daily_briefing_preview.html' } else { Join-Path $root $latest.eml }
Start-Process $path
