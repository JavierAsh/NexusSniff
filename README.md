# 🔍 NexusSniff

> Analizador de paquetes de red de nivel empresarial con motor C++20 ultrarrápido e interfaz PyQt6 moderna.

NexusSniff es una herramienta de análisis de tráfico de red en tiempo real diseñada para ofrecer rendimiento extremo, inspección precisa y una interfaz de usuario fluida y profesional.

![Logo](app/resources/icons/logo_icon.ico)

## Características Principales

- **Motor de Captura C++**: Desarrollado estrictamente en C++ con uso del SDK de Npcap para procesamiento rápido y sin fugas de memoria.
- **Eficiencia**: Zero-allocation bindings entre C++ y Python usando `pybind11`, garantizando cero bloqueos en la interfaz gráfica durante capturas masivas.
- **Interfaz Moderna**: Diseño Dark/Light Mode en PyQt6, con soporte High DPI y autoscroll optimizado.
- **Análisis Profundo**: Soporte para protocolos L2/L3/L4 con decodificación hexadecimal estructurada y herramientas de búsqueda rápida.
- **Exportación Flexible**: Guarda capturas en PCAP, CSV, JSON y Excel.

## Requisitos del Sistema

- **Sistemas Operativos**: Windows 10 / Windows 11
- **Dependencia Principal**: [Npcap](https://npcap.com/) (debe estar instalado en el sistema)

*(Nota para desarrolladores: Se recomienda Visual Studio 2022 con soporte para C++, CMake 3.20+ y Python 3.12+ para compilación desde el código fuente).*

## Instalación para el Usuario Final

NexusSniff se distribuye como una aplicación nativa pre-compilada. Simplemente descarga la última versión desde la página de releases, descomprime el archivo ZIP y ejecuta `NexusSniff.exe`.

## Guía para Desarrolladores

Si deseas contribuir, desarrollar nuevas funcionalidades, o compilar la aplicación desde cero, sigue estos pasos:

### 1. Compilar el Motor C++

```powershell
# Usar el script dedicado para validar dependencias y compilar
.\scripts\build_engine.ps1 -BuildType Release
```

### 2. Ejecutar la Aplicación en Modo Desarrollo

```powershell
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación usando Python
python -m app.main
```

### 3. Generar un Release Comercial

Para empaquetar la aplicación en un ejecutable cerrado para entorno productivo:

```powershell
.\scripts\create_release.ps1
```
Este script utilizará PyInstaller para empaquetar el código Python y el motor nativo `.pyd` en un paquete EXE instalable (o archivo `.zip` distribuible) ubicado en la carpeta raíz.

## Estructura del Proyecto

```text
NexusSniff/
├── app/             # Aplicación Frontend PyQt6
│   ├── core/        # Lógica de negocio y modelos de datos
│   ├── ui/          # Componentes de interfaz (Ventana, Filtros, Gráficos)
│   ├── resources/   # Recursos estáticos (Iconos, Previsualizaciones)
│   └── themes/      # Hojas de estilo QSS
├── docs/            # Documentación del sistema y planes de implementación
├── engine/          # Motor backend C++ de captura de red
│   ├── include/     # Headers públicos
│   └── src/         # Implementación de decodificadores y gestión
├── scripts/         # Scripts PowerShell para pipelines y compilacion
├── tests/           # Conjuntos de pruebas en C++ y Python
└── third_party/     # SDKs y módulos (Npcap SDK, PyBind11)
```

## Licencia

Distribuido bajo la Licencia MIT. Ver documento `LICENSE` para mayor información.
