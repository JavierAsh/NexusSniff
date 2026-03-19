@echo off
REM ═══════════════════════════════════════════════════════════════
REM  NexusSniff v1.2.0 — Script de Lanzamiento
REM  Detecta automáticamente el entorno Python correcto
REM ═══════════════════════════════════════════════════════════════

title NexusSniff v1.2.0

set MSYS2_PYTHON=C:\msys64\mingw64\bin\python.exe
set VENV_PYTHON=%~dp0.venv\Scripts\python.exe
set MODULE=app

echo.
echo  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
echo  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
echo  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
echo  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
echo  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
echo  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
echo           Network Packet Analyzer v1.2.0
echo.

REM Verificar que el motor C++ esté compilado
if not exist "%~dp0app\nexus_engine.cp312-mingw_x86_64_msvcrt_gnu.pyd" (
    echo  [AVISO] Motor C++ no compilado detectado.
    echo  [AVISO] Para compilar ejecuta:
    echo          .\scripts\build_engine.ps1
    echo.
)

REM Detectar Python: primero MSYS2 (compilacion compatible), luego venv, luego global
if exist "%MSYS2_PYTHON%" (
    echo  [✓] Usando Python MSYS2/MinGW: %MSYS2_PYTHON%
    echo  [→] Iniciando NexusSniff...
    echo.
    "%MSYS2_PYTHON%" -m %MODULE%
    goto :end
)

if exist "%VENV_PYTHON%" (
    echo  [✓] Usando Python del Entorno Virtual: %VENV_PYTHON%
    echo  [→] Iniciando NexusSniff...
    echo.
    "%VENV_PYTHON%" -m %MODULE%
    goto :end
)

REM Verificar que Python global esté disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no encontrado en el sistema.
    echo  [ERROR] Instala Python 3.12+ o configura el venv con:
    echo          .\scripts\setup_dev.ps1
    echo.
    pause
    exit /b 1
)

echo  [✓] Usando Python global del sistema
echo  [→] Iniciando NexusSniff...
echo.
python -m %MODULE%

:end
if errorlevel 1 (
    echo.
    echo  [ERROR] NexusSniff terminó con un error (código: %errorlevel%)
    echo  [INFO]  Revisa los mensajes de arriba para diagnosticar el problema.
    echo.
    pause
)
