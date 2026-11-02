$ErrorActionPreference = "Stop"
& (Join-Path (Split-Path $PSScriptRoot -Parent) "install.ps1")
if (-not $?) { exit 1 }
