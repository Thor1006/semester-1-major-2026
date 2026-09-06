<#
.SYNOPSIS
    Runs the refusal-ledger demonstration.

.DESCRIPTION
    Finds a working Python, then runs the demo, the checks, or both. Works from
    any folder: it switches to its own directory first, so the imports resolve.

.EXAMPLE
    .\run.ps1 -Gui         # the Tkinter application
    .\run.ps1              # the console report
    .\run.ps1 -Test        # the checks only
    .\run.ps1 -All         # checks first, then the console report
#>
[CmdletBinding()]
param(
    [switch]$Gui,
    [switch]$Test,
    [switch]$All
)

$ErrorActionPreference = 'Stop'

# Run from this script's own folder so demo.py can import clinic.py, no matter
# where the script was launched from.
$here = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
Set-Location -LiteralPath $here

function Find-Python {
    <#
        Returns the path to an interpreter that actually runs.

        The check matters on this machine: a bare `python` exists but points at
        a manager with no configured runtime, so testing for the command alone
        would find something that cannot execute anything.
    #>
    $candidates = @(
        'C:\ProgramData\miniconda3\python.exe',
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    )

    foreach ($name in @('python', 'py')) {
        $found = Get-Command $name -ErrorAction SilentlyContinue
        if ($found -and $found.Source) { $candidates += $found.Source }
    }

    foreach ($candidate in $candidates) {
        if (-not (Test-Path -LiteralPath $candidate)) { continue }
        & $candidate -c 'import sys' 2>$null
        if ($LASTEXITCODE -eq 0) { return $candidate }
    }

    throw ("No working Python interpreter was found. Install Python 3, or edit " +
           "the `$candidates list at the top of Find-Python in this script.")
}

$python = Find-Python
Write-Host "Python: $python" -ForegroundColor DarkGray

$failed = $false

if ($Test -or $All) {
    Write-Host "`nRunning checks..." -ForegroundColor Cyan
    & $python -m unittest -v test_demo.py
    if ($LASTEXITCODE -ne 0) {
        $failed = $true
        Write-Host "Checks FAILED." -ForegroundColor Red
    }
}

# Something runs by default, and after the checks when -All was given. Nothing
# runs when only -Test was asked for, or when the checks just failed.
if (-not $Test -or $All) {
    if ($failed) {
        Write-Host "`nSkipping the demonstration because the checks failed." -ForegroundColor Yellow
    }
    elseif ($Gui) {
        Write-Host "`nOpening the application window..." -ForegroundColor Cyan
        & $python ledger_app.py
        if ($LASTEXITCODE -ne 0) { $failed = $true }
    }
    else {
        & $python demo.py
        if ($LASTEXITCODE -ne 0) { $failed = $true }
    }
}

if ($failed) { exit 1 }
