#Requires -Version 5.1
<#
.SYNOPSIS
    One-click setup and launch for DWG AI Extractor.
.DESCRIPTION
    Creates venv, installs dependencies, and starts the GUI.
    First run takes ~1-2 minutes; subsequent launches are instant.
.EXAMPLE
    .\start.ps1
#>

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

# 1. Create venv (first run only)
if (-not (Test-Path $venvPython)) {
    Write-Host "[1/3] Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create venv. Please install Python 3.10+."
        exit 1
    }
} else {
    Write-Host "[1/3] Venv already exists, skipping." -ForegroundColor DarkGray
}

# 2. Install / update dependencies
Write-Host "[2/3] Installing dependencies..." -ForegroundColor Cyan
& $venvPython -m pip install -e ".[dev]" -q --disable-pip-version-check
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install dependencies."
    exit 1
}

# 3. Launch GUI
Write-Host "[3/3] Launching GUI..." -ForegroundColor Green
& $venvPython -m frontend.desktop.app
