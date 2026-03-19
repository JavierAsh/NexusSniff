# ══ NexusSniff — Ejecución Rápida ══
# Uso: .\run_nexus.ps1

$ErrorActionPreference = "Stop"

Write-Host "-----------------------------------------------" -ForegroundColor Cyan
Write-Host "  Iniciando NexusSniff                         " -ForegroundColor Cyan
Write-Host "-----------------------------------------------" -ForegroundColor Cyan

$msys2Python = "C:\msys64\mingw64\bin\python.exe"
$venvPython = ".\.venv\Scripts\python.exe"

if (Test-Path $msys2Python) {
    Write-Host "  Usando Python nativo de MSYS2/MinGW..." -ForegroundColor Green
    & $msys2Python -m app.main
} elseif (Test-Path $venvPython) {
    Write-Host "  Usando Python del Entorno Virtual (.venv)..." -ForegroundColor Green
    & $venvPython -m app.main
} else {
    Write-Host "  Usando Python global del sistema..." -ForegroundColor Yellow
    python -m app.main
}
