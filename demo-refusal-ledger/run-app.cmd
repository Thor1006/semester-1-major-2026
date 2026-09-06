@echo off
REM Double-click this to open the Tkinter application.
REM
REM run.cmd prints the console report instead. Both are the same demonstration;
REM this one has a window.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" -Gui
set EXITCODE=%ERRORLEVEL%

REM Only pause on failure. On success the window has already been shown and
REM closed by the user, so there is nothing left to read.
if not "%EXITCODE%"=="0" (
    echo(
    echo The application exited with an error. Press any key to close.
    pause >nul
)

exit /b %EXITCODE%
