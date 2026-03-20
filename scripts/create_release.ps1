<#
.SYNOPSIS
Crea un ejecutable (EXE) comercial para NexusSniff empacado en un ZIP.

.DESCRIPTION
Este script usa PyInstaller para compilar la aplicación, copia los binarios, 
recursos, iconos y el motor DLL en una carpeta limpia de distribución y 
genera un archivo ZIP listo para ser subido.

.EXAMPLE
.\scripts\create_release.ps1
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = (Get-Item $PSScriptRoot).Parent.FullName
$ReleaseDir = Join-Path $ProjectRoot "release_build"
$DistDir = Join-Path $ProjectRoot "dist"
$DistAppDir = Join-Path $DistDir "NexusSniff"
$ReleaseZip = Join-Path $ProjectRoot "NexusSniff_v1.4.0-beta.1.zip"

Write-Host "Preparando release comercial (Ejecutable) para NexusSniff..." -ForegroundColor Cyan

# 1. Asegurar que haya entorno e instalar PyInstaller
$PythonExe = "C:\msys64\mingw64\bin\python.exe"
if (-not (Test-Path $PythonExe)) {
    # Fallback if the user doesn't have MSYS2 python, try local venv
    if (Test-Path "$ProjectRoot\.venv\bin\python.exe") {
        $PythonExe = "$ProjectRoot\.venv\bin\python.exe"
    } elseif (Test-Path "$ProjectRoot\.venv\Scripts\python.exe") {
        $PythonExe = "$ProjectRoot\.venv\Scripts\python.exe"
    } else {
        $PythonExe = "python.exe" # Global python
    }
}
Write-Host "Usando Python: $PythonExe"

if ($PythonExe -match "msys64") {
    Write-Host "  -> Instalando PyInstaller via pacman..."
    & C:\msys64\usr\bin\pacman.exe --noconfirm -S mingw-w64-x86_64-pyinstaller mingw-w64-x86_64-pyinstaller-hooks-contrib
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: No se pudo instalar PyInstaller con pacman." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  -> Instalando PyInstaller via pip..."
    & $PythonExe -m pip install -q pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: No se pudo instalar PyInstaller con pip." -ForegroundColor Red
        exit 1
    }
}

# 2. Compilar con PyInstaller
Write-Host "[2/4] Compilando ejecutable nativo..." -ForegroundColor Yellow
$IconPath = Join-Path $ProjectRoot "app\resources\icons\logo_icon.ico"

# Construimos el comando con `--noconsole` para evitar ventana CMD
# y añadimos los recursos (add-data) de temas y recursos
$PyInstallerArgs = @(
    "--noconfirm"
    "--windowed"
    "--onedir"
    "--name=NexusSniff"
    "--icon=$IconPath"
    "--add-data=app/resources;app/resources"
    "--add-data=app/themes;app/themes"
    "--splash=app/resources/icons/splash.png"
    "--hidden-import=psycopg2"
    "--hidden-import=clickhouse_driver"
    "--hidden-import=redis"
    "app/main.py"
)

$PyInstallerExe = if ($PythonExe -match "msys64") { "C:\msys64\mingw64\bin\pyinstaller.exe" } else { "pyinstaller" }

Set-Location $ProjectRoot
& $PyInstallerExe $PyInstallerArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Falló la compilación de PyInstaller." -ForegroundColor Red
    exit 1
}

# 3. Empaquetar el ZIP
Write-Host "[3/4] Empaquetando en ZIP para distribución..." -ForegroundColor Yellow
if (Test-Path $ReleaseDir) { Remove-Item -Path $ReleaseDir -Recurse -Force }
New-Item -ItemType Directory -Path $ReleaseDir | Out-Null
if (Test-Path $ReleaseZip) { Remove-Item -Path $ReleaseZip -Force }

# Copiar el ejecutable generado
Copy-Item -Path $DistAppDir -Destination "$ReleaseDir\NexusSniff" -Recurse -Force

# Asegurarnos de que el motor PYD local se comparta en el subdirectorio app del target si es necesario
# PyInstaller debería incluirlo, pero para mayor seguridad lo iteramos
$PydFile = Get-ChildItem -Path "$ProjectRoot\app" -Filter "*.pyd" | Select-Object -First 1
if ($PydFile) {
    $TargetAppDir = Join-Path "$ReleaseDir\NexusSniff" "_internal\app"
    if (-not (Test-Path $TargetAppDir)) {
        New-Item -ItemType Directory -Path $TargetAppDir -Force | Out-Null
    }
    Copy-Item $PydFile.FullName -Destination $TargetAppDir -Force
}

# Comprimir
Compress-Archive -Path "$ReleaseDir\NexusSniff\*" -DestinationPath $ReleaseZip -CompressionLevel Optimal

# 4. Limpieza
Write-Host "[4/4] Limpiando archivos temporales..." -ForegroundColor Yellow
Remove-Item -Path $ReleaseDir -Recurse -Force
if (Test-Path "$ProjectRoot\build") { Remove-Item -Path "$ProjectRoot\build" -Recurse -Force }
if (Test-Path "$ProjectRoot\NexusSniff.spec") { Remove-Item -Path "$ProjectRoot\NexusSniff.spec" -Force }

Write-Host "¡Release (Executable) generado con éxito!" -ForegroundColor Green
Write-Host "El paquete comercial está listo en: $ReleaseZip" -ForegroundColor Yellow
