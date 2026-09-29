[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$dir = Join-Path $root '.secrets'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
# DPAPI protects this value for this Windows account on this machine. It is not portable.
$key = Read-Host 'Enter your OpenAI API key (stored locally with Windows DPAPI)' -AsSecureString
$key | ConvertFrom-SecureString | Set-Content (Join-Path $dir 'openai_api_key.dpapi') -Encoding ASCII
$account = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls.exe $dir /inheritance:r /grant:r "${account}:(OI)(CI)F" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Secret stored with DPAPI, but directory ACL restriction failed. Inspect permissions.' }
Write-Host 'Key stored locally. No key was transmitted. Enable authorized external AI in config\config.json before live analysis.'
