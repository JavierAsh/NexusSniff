cmake_minimum_required(VERSION 3.20)
project(NexusSniff VERSION 1.2.0 LANGUAGES CXX)

# ══════════════════════════════════════════════════════════════
# Estándar C++20
# ══════════════════════════════════════════════════════════════
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ══════════════════════════════════════════════════════════════
# Opciones de compilación
# ══════════════════════════════════════════════════════════════
option(NEXUS_BUILD_TESTS "Compilar tests del motor" ON)
option(NEXUS_BUILD_PYTHON "Compilar módulo Python (pybind11)" ON)

# ══════════════════════════════════════════════════════════════
# Npcap SDK
# ══════════════════════════════════════════════════════════════
set(NPCAP_SDK_DIR "${CMAKE_SOURCE_DIR}/third_party/npcap-sdk" CACHE PATH "Ruta al Npcap SDK")

if(NOT EXISTS "${NPCAP_SDK_DIR}/Include")
    message(WARNING "Npcap SDK no encontrado en ${NPCAP_SDK_DIR}. "
                    "Descárgalo de https://npcap.com/#download y extráelo ahí.")
endif()

# ══════════════════════════════════════════════════════════════
# pybind11
# ══════════════════════════════════════════════════════════════
if(NEXUS_BUILD_PYTHON)
    add_subdirectory(third_party/pybind11)
endif()

# ══════════════════════════════════════════════════════════════
# Motor de captura
# ══════════════════════════════════════════════════════════════
add_subdirectory(engine)
