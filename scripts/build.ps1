$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
& .venv/Scripts/python.exe scripts/build_distribution.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed; see output above.' }
