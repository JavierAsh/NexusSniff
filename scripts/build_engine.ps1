param(
    [string]$BuildType = "Release",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "-----------------------------------------------" -ForegroundColor Cyan
Write-Host "  NexusSniff - Compilar Motor C++              " -ForegroundColor Cyan
Write-Host "-----------------------------------------------" -ForegroundColor Cyan
Write-Host ""

# Verificar prerequisitos
Write-Host "[1/4] Verificando prerequisitos..." -ForegroundColor Yellow

# CMake
if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: CMake no encontrado. Instala CMake 3.20+" -ForegroundColor Red
    exit 1
}
$cmakeVersion = cmake --version | Select-Object -First 1
Write-Host "  [OK] $cmakeVersion" -ForegroundColor Green

# Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python no encontrado." -ForegroundColor Red
    exit 1
}
$pythonVersion = python --version
Write-Host "  [OK] $pythonVersion" -ForegroundColor Green

# Npcap SDK
$npcapPath = Join-Path $ProjectRoot "third_party\npcap-sdk\Include"
if (-not (Test-Path $npcapPath)) {
    Write-Host "ERROR: Npcap SDK no encontrado en third_party/npcap-sdk/" -ForegroundColor Red
    Write-Host "  Descargalo de: https://npcap.com/#download" -ForegroundColor Yellow
    exit 1
}
Write-Host "  [OK] Npcap SDK encontrado" -ForegroundColor Green

# pybind11
$pybindPath = Join-Path $ProjectRoot "third_party\pybind11\CMakeLists.txt"
if (-not (Test-Path $pybindPath)) {
    Write-Host "  [WARN] pybind11 no encontrado, clonando..." -ForegroundColor Yellow
    Push-Location (Join-Path $ProjectRoot "third_party")
    git clone https://github.com/pybind/pybind11.git
    Pop-Location
}
if (Test-Path $pybindPath) {
    Write-Host "  [OK] pybind11 encontrado" -ForegroundColor Green
}

# Limpiar build si se solicita
if ($Clean) {
    Write-Host ""
    Write-Host "[2/4] Limpiando build anterior..." -ForegroundColor Yellow
    $buildDir = Join-Path $ProjectRoot "build"
    if (Test-Path $buildDir) {
        Remove-Item -Recurse -Force $buildDir
    }
}

# Configurar CMake
Write-Host ""
Write-Host "[2/4] Configurando CMake ($BuildType)..." -ForegroundColor Yellow
Push-Location $ProjectRoot
cmake -B build -S . "-DCMAKE_BUILD_TYPE=$BuildType" -DCMAKE_CXX_SCAN_FOR_MODULES=OFF -DPython_EXECUTABLE="C:/msys64/mingw64/bin/python.exe" -DPYBIND11_FINDPYTHON=ON
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo la configuracion de CMake" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Compilar
Write-Host ""
Write-Host "[3/4] Compilando motor C++..." -ForegroundColor Yellow
cmake --build build --config "$BuildType" --parallel
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo la compilacion" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Verificar .pyd
Write-Host ""
Write-Host "[4/4] Verificando modulo Python..." -ForegroundColor Yellow
$pydFile = Get-ChildItem -Path "$ProjectRoot\app" -Filter "nexus_engine*.pyd" -ErrorAction SilentlyContinue
if ($pydFile) {
    Write-Host "  [OK] $($pydFile.Name) ($([math]::Round($pydFile.Length / 1KB)) KB)" -ForegroundColor Green
}
if (-not $pydFile) {
    Write-Host "  [WARN] nexus_engine.pyd no encontrado en app/" -ForegroundColor Yellow
}

Pop-Location

Write-Host ""
Write-Host "-----------------------------------------------" -ForegroundColor Green
Write-Host "  [OK] Compilacion completada exitosamente     " -ForegroundColor Green
Write-Host "-----------------------------------------------" -ForegroundColor Green
Write-Host ""
