<#
.SYNOPSIS
Crea un paquete de distribución (ZIP) comercial para NexusSniff.

.DESCRIPTION
Este script recopila los binarios compilados, el código fuente en Python, 
los temas, iconos y scripts de ejecución para crear un ZIP listo para 
entregar a los usuarios.

.EXAMPLE
.\scripts\create_release.ps1
#>

$ProjectRoot = (Get-Item $PSScriptRoot).Parent.FullName
$ReleaseDir = Join-Path $ProjectRoot "release_build"
$ReleaseZip = Join-Path $ProjectRoot "NexusSniff_v1.0.0.zip"

Write-Host "Preparando release para distribución comercial..." -ForegroundColor Cyan

# 1. Limpiar directorio previo
if (Test-Path $ReleaseDir) { Remove-Item -Path $ReleaseDir -Recurse -Force }
New-Item -ItemType Directory -Path $ReleaseDir | Out-Null

if (Test-Path $ReleaseZip) { Remove-Item -Path $ReleaseZip -Force }

# 2. Copiar elementos necesarios
Write-Host "  -> Copiando código fuente y UI..."
Copy-Item -Path "$ProjectRoot\app" -Destination "$ReleaseDir\app" -Recurse
# Eliminar posibles cachés (__pycache__)
Get-ChildItem -Path "$ReleaseDir\app" -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

Write-Host "  -> Copiando scripts de ejecución..."
Copy-Item -Path "$ProjectRoot\run_nexus.bat" -Destination $ReleaseDir
Copy-Item -Path "$ProjectRoot\run_nexus.ps1" -Destination $ReleaseDir

Write-Host "  -> Copiando configuración..."
Copy-Item -Path "$ProjectRoot\docker-compose.yml" -Destination $ReleaseDir
Copy-Item -Path "$ProjectRoot\requirements.txt" -Destination $ReleaseDir
Copy-Item -Path "$ProjectRoot\README.md" -Destination $ReleaseDir

# 3. Empaquetar en formato ZIP
Write-Host "  -> Generando archivo ZIP: $ReleaseZip..."
Compress-Archive -Path "$ReleaseDir\*" -DestinationPath $ReleaseZip -CompressionLevel Optimal

# 4. Limpieza
Write-Host "  -> Limpiando directorio temporal..."
Remove-Item -Path $ReleaseDir -Recurse -Force

Write-Host "¡Release generado con éxito!" -ForegroundColor Green
Write-Host "El paquete está listo en: $ReleaseZip" -ForegroundColor Yellow
