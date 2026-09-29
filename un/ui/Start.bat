@echo off
setlocal
cd /d "%~dp0"
call scripts\find-r.cmd
if errorlevel 1 goto end
"%READOUT_R%" --vanilla scripts\launch.R "%CD%"
:end
pause
