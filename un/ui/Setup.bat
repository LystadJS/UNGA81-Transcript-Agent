@echo off
setlocal
cd /d "%~dp0"
echo One-time setup installs R packages in this folder.
echo Continue only on an approved computer and network.
pause
call scripts\find-r.cmd
if errorlevel 1 goto end
"%READOUT_R%" --vanilla scripts\setup.R "%CD%"
:end
pause
