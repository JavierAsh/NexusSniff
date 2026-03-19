# 🔍 NexusSniff

> Analizador de paquetes de red de alto rendimiento con motor C++20 e interfaz PyQt6.

## Arquitectura

| Capa | Tecnología | Descripción |
|------|-----------|-------------|
| **Motor de Captura** | C++20 + Npcap SDK | Captura y decodificación de paquetes a nivel de enlace |
| **Bindings** | pybind11 | Expone el motor como módulo `.pyd` importable desde Python |
| **Frontend** | PyQt6 + pyqtgraph | Interfaz gráfica con Dark Mode y gráficas en tiempo real |
| **Persistencia** | PostgreSQL + ClickHouse + Redis | Almacenamiento de sesiones, paquetes y cache |

## Requisitos

- **Windows 10/11** con [Npcap](https://npcap.com/) instalado
- **Visual Studio 2022** con herramientas C++ (MSVC)
- **CMake 3.20+**
- **Python 3.12+**

## Compilar el Motor C++

```powershell
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

## Ejecutar la Aplicación

```powershell
pip install -r requirements.txt
python -m app.main
```

## Estructura del Proyecto

```
NexusSniff/
├── engine/          # Motor de captura C++
│   ├── include/     # Headers públicos
│   ├── src/         # Implementación
│   └── bindings/    # Bindings pybind11
├── app/             # Aplicación PyQt6
│   ├── core/        # Lógica de negocio
│   ├── ui/          # Componentes de interfaz
│   └── themes/      # Hojas de estilo QSS
├── scripts/         # Utilidades de build
└── third_party/     # Npcap SDK + pybind11
```

## Licencia

MIT
