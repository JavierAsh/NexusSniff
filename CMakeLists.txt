cmake_minimum_required(VERSION 3.20)
project(NexusSniff VERSION 1.4.0 LANGUAGES CXX)
# Nota: v1.4.0-beta.1 (CMake no soporta suffixes en VERSION)

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

# ══════════════════════════════════════════════════════════════
# Tests (Catch2 via FetchContent)
# ══════════════════════════════════════════════════════════════
if(NEXUS_BUILD_TESTS)
    include(FetchContent)
    FetchContent_Declare(
        Catch2
        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
        GIT_TAG        v3.5.2
    )
    FetchContent_MakeAvailable(Catch2)

    add_executable(test_nexus
        tests/cpp/test_ring_buffer.cpp
    )
    target_link_libraries(test_nexus PRIVATE
        nexus_core
        Catch2::Catch2WithMain
    )
    target_include_directories(test_nexus PRIVATE
        ${CMAKE_SOURCE_DIR}/engine/include
        ${NPCAP_SDK_DIR}/Include
    )

    include(CTest)
    include(Catch)
    catch_discover_tests(test_nexus)
endif()
