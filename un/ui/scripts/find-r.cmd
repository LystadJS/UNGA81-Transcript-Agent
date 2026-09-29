@echo off
set "READOUT_R="
for /f "delims=" %%I in ('where Rscript.exe 2^>nul') do if not defined READOUT_R set "READOUT_R=%%I"
if defined READOUT_R exit /b 0
for /f "delims=" %%D in ('dir /b /ad /o-n "%ProgramFiles%\R\R-*" 2^>nul') do if not defined READOUT_R if exist "%ProgramFiles%\R\%%D\bin\Rscript.exe" set "READOUT_R=%ProgramFiles%\R\%%D\bin\Rscript.exe"
if defined READOUT_R exit /b 0
for /f "delims=" %%D in ('dir /b /ad /o-n "%LocalAppData%\Programs\R\R-*" 2^>nul') do if not defined READOUT_R if exist "%LocalAppData%\Programs\R\%%D\bin\Rscript.exe" set "READOUT_R=%LocalAppData%\Programs\R\%%D\bin\Rscript.exe"
if defined READOUT_R exit /b 0
echo R was not found. Ask the installation owner to install an approved R version, 4.3 or newer.
exit /b 1
