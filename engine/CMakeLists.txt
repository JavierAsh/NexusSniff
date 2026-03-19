# ══════════════════════════════════════════════════════════════
# Motor de Captura NexusSniff — nexus_core + nexus_engine.pyd
# ══════════════════════════════════════════════════════════════

# ── Archivos fuente del motor ──
set(NEXUS_SOURCES
    src/packet.cpp
    src/decoder.cpp
    src/filter.cpp
    src/stats.cpp
    src/session.cpp
    src/capturer.cpp
)

# ── Librería estática nexus_core ──
add_library(nexus_core STATIC ${NEXUS_SOURCES})

target_include_directories(nexus_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${NPCAP_SDK_DIR}/Include
)

# Determinar arquitectura para Npcap libs
if(CMAKE_SIZEOF_VOID_P EQUAL 8)
    set(NPCAP_LIB_DIR "${NPCAP_SDK_DIR}/Lib/x64")
else()
    set(NPCAP_LIB_DIR "${NPCAP_SDK_DIR}/Lib")
endif()

target_link_directories(nexus_core PUBLIC ${NPCAP_LIB_DIR})
target_link_libraries(nexus_core PUBLIC wpcap Packet ws2_32 iphlpapi)

# Warnings estrictos
target_compile_options(nexus_core PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/W4 /permissive->
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-Wall -Wextra -Wpedantic>
)

# ── Módulo Python (pybind11) ──
if(NEXUS_BUILD_PYTHON)
    pybind11_add_module(nexus_engine bindings/py_nexus.cpp)
    target_link_libraries(nexus_engine PRIVATE nexus_core)
    
    # Copiar .pyd al directorio de la app Python
    add_custom_command(TARGET nexus_engine POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy
            $<TARGET_FILE:nexus_engine>
            "${CMAKE_SOURCE_DIR}/app/$<TARGET_FILE_NAME:nexus_engine>"
        COMMENT "Copiando nexus_engine.pyd a app/"
    )
endif()

# ── Tests ──
if(NEXUS_BUILD_TESTS)
    add_subdirectory(tests)
endif()
