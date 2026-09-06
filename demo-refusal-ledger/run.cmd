@echo off
REM Double-clickable launcher for the refusal-ledger demonstration.
REM
REM Double-clicking a .ps1 opens it in Notepad rather than running it, and the
REM execution policy usually blocks unsigned scripts. This wrapper sidesteps
REM both. Arguments are passed through, so "run.cmd -All" works too.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" %*
set EXITCODE=%ERRORLEVEL%

REM Keep the window open when this was double-clicked, so the report can be
REM read. Launched from a terminal, the output stays on screen anyway.
echo(
echo Press any key to close this window.
pause >nul

exit /b %EXITCODE%
