$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "-----------------------------------------------" -ForegroundColor Cyan
Write-Host "  NexusSniff - Configurar Entorno Dev          " -ForegroundColor Cyan
Write-Host "-----------------------------------------------" -ForegroundColor Cyan
Write-Host ""

# 1. Crear entorno virtual Python
Write-Host "[1/4] Creando entorno virtual Python..." -ForegroundColor Yellow
$venvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
    Write-Host "  [OK] Entorno virtual creado en .venv/" -ForegroundColor Green
}
if (Test-Path $venvPath) {
    Write-Host "  [OK] Entorno virtual verificado" -ForegroundColor Green
}

# 2. Activar e instalar dependencias
Write-Host ""
Write-Host "[2/4] Instalando dependencias Python..." -ForegroundColor Yellow

$venvPython = "$venvPath\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = "$venvPath\bin\python.exe"
}

if (-not (Test-Path $venvPython)) {
    Write-Host "  [ERROR] No se pudo encontrar el ejecutable Python en el entorno virtual." -ForegroundColor Red
    exit 1
}

& "$venvPython" -m pip install -r "$ProjectRoot\requirements.txt" --quiet
Write-Host "  [OK] Dependencias instaladas" -ForegroundColor Green

# 3. Verificar Npcap
Write-Host ""
Write-Host "[3/4] Verificando Npcap..." -ForegroundColor Yellow
$npcapDll = "C:\Windows\System32\Npcap\wpcap.dll"
if (Test-Path $npcapDll) {
    Write-Host "  [OK] Npcap instalado en el sistema" -ForegroundColor Green
}
if (-not (Test-Path $npcapDll)) {
    Write-Host "  [WARN] Npcap NO detectado. Descargalo de: https://npcap.com/" -ForegroundColor Yellow
}

# 4. Verificar Npcap SDK
Write-Host ""
Write-Host "[4/4] Verificando Npcap SDK..." -ForegroundColor Yellow
$sdkPath = Join-Path $ProjectRoot "third_party\npcap-sdk\Include"
if (Test-Path $sdkPath) {
    Write-Host "  [OK] Npcap SDK encontrado" -ForegroundColor Green
}
if (-not (Test-Path $sdkPath)) {
    Write-Host "  [WARN] Npcap SDK no encontrado en third_party/npcap-sdk/" -ForegroundColor Yellow
    Write-Host "  Descargalo de https://npcap.com/#download y extraelo ahi" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "-----------------------------------------------" -ForegroundColor Green
Write-Host "  Proximos pasos:                              " -ForegroundColor Green
Write-Host "  1. .\.venv\Scripts\Activate.ps1              " -ForegroundColor White
Write-Host "  2. .\scripts\build_engine.ps1                " -ForegroundColor White
Write-Host "  3. python -m app.main                        " -ForegroundColor White
Write-Host "-----------------------------------------------" -ForegroundColor Green
Write-Host ""
