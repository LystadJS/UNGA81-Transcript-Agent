@echo off
setlocal
cd /d "%~dp0"
call scripts\find-r.cmd
if errorlevel 1 goto end
"%READOUT_R%" --vanilla tests\run_tests.R "%CD%"
if errorlevel 1 goto end
"%READOUT_R%" --vanilla tests\test_shiny.R "%CD%"
:end
pause
