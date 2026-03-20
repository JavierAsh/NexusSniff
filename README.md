# 🔍 NexusSniff v1.3.0

NexusSniff es un analizador de paquetes de red diseñado para la interceptación y el diagnóstico profundo de tráfico en tiempo real. Esta herramienta permite desglosar la estructura de los datos que circulan por la interfaz de red, facilitando la identificación de protocolos, la detección de anomalías y el estudio del flujo de información en entornos de sistemas distribuidos o redes complejas.

![Logo](app/resources/icons/logo_icon.ico)

## Requisitos Previos

- **Sistema Operativo**: Windows 10 / Windows 11
- **Motor de Captura (Red)**: [Npcap](https://npcap.com/) (debe estar instalado previamente en el sistema)
- **Compilación (Desarrollo)**: CMake 3.20+, Visual Studio 2022 (con soporte para C++20)
- **Entorno (Desarrollo)**: Python 3.12+

## Instalación para Uso Rápido

Para iniciar rápidamente usando los binarios pre-compilados:

1. Descarga el último release (`NexusSniff_v1.3.0.zip`) desde GitHub.
2. Descomprime el archivo en cualquier ubicación.
3. Ejecuta el archivo en PowerShell o haz doble clic:

```powershell
.\NexusSniff.exe
```

## Instalación desde Código Fuente (Desarrollo)

Asegúrate de tener instalado Python, CMake, Visual Studio y Npcap. Ejecuta lo siguiente literalmente copiando y pegando en PowerShell:

```powershell
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/NexusSniff.git
cd NexusSniff

# 2. Instalar dependencias del frontend (se recomienda usar venv)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Compilar el motor C++
.\scripts\build_engine.ps1 -BuildType Release

# 4. Lanzar la aplicación
python -m app.main
```

## Ejemplo de Uso Rápido

1. Abre la aplicación NexusSniff (`NexusSniff.exe` o `python -m app.main`).
2. En la interfaz principal, selecciona la **interfaz de red** deseada desde el selector.
3. Ingresa un filtro si lo necesitas (por ejemplo, `tcp port 80` o `udp`).
4. Presiona el botón **Play (Iniciar)** para comenzar a capturar los paquetes en tiempo real.
5. Selecciona cualquier paquete de la lista para ver el desglose en el panel de detalle y su contenido en el visor hexadecimal.

## Estructura del Proyecto

```text
NexusSniff/
├── app/             # Frontend en Python (PyQt6)
│   ├── core/        # Lógica de negocio, gestión de DB, exportación y trabajadores
│   ├── ui/          # Componentes visuales (Dark Mode, gráficas, paneles)
│   ├── resources/   # Iconos y recursos estáticos
│   └── themes/      # Hojas de estilo QSS
├── docs/            # Documentación extendida
├── engine/          # Backend C++20 (Motor de captura ultrarrápido)
│   ├── include/     # Cabeceras (.hpp) con JSDoc
│   └── src/         # Implementación de decodificadores y gestión
├── scripts/         # Herramientas de PowerShell (compilación y release)
├── tests/           # Pruebas automatizadas (C++ Catch2 y Python Pytest)
└── third_party/     # Bibliotecas de terceros (Npcap SDK, PyBind11)
```

## Variables de Entorno

Actualmente, **NexusSniff v1.3.0** está diseñado para ejecutarse sin depender de variables de entorno globales. La configuración del compilador la gestionan los scripts de CMake (`CMakeLists.txt`) o el script de PowerShell (`\scripts\build_engine.ps1`), ubicando el SDK de Npcap mediante rutas relativas o especificándolas si difieren del estándar:

| Variable | Descripción | Ejemplo | Requerida |
| :--- | :--- | :--- | :--- |
| `NPCAP_SDK_DIR` | (Sólo para compilación) Ruta hacia la carpeta del SDK de Npcap si varía del defecto (`third_party/npcap-sdk`). Esta puede ser pasada al invocar CMake manualmente. | `C:\Npcap-SDK` | Solo si varía de ruta default |

## Tests

El proyecto cuenta con pruebas automatizadas tanto para el backend (C++) como para el frontend (Python).

**Para compilar y ejecutar los tests en C++ (Catch2):**

```powershell
# Después de compilar el motor utilizando CMake:
cd build
ctest --output-on-failure
```

**Para correr tests del Python:**

```powershell
pip install pytest
pytest tests/
```

## Contribuir

¡Las contribuciones son bienvenidas!

1. Realiza un *Fork* del repositorio.
2. Crea una rama para tu feature (`git checkout -b feature/NuevaIdea`).
3. Sigue las reglas de estilo (Docstrings para Python, JSDoc style para C++).
4. Verifica que no se produzcan *memory leaks* en el código de C++ y que los tests existentes pasen correctamente.
5. Sube tus cambios (`git commit -m 'feat: Agrega NuevaIdea'`).
6. Abre un Pull Request describiendo detalladamente tus cambios.

## Licencia

Distribuido bajo la Licencia MIT. Ver documento `LICENSE` para mayor información.
