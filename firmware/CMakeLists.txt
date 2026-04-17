cmake_minimum_required(VERSION 3.16)
project(dilder_firmware C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ── Target board selection ──────────────────────────────────────
# Set via: cmake -DTARGET_BOARD=PICO_W ..  (or ESP32S3, DESKTOP)
# Defaults to DESKTOP for the shared library / CLI build.
if(NOT DEFINED TARGET_BOARD)
    set(TARGET_BOARD "DESKTOP")
endif()
add_compile_definitions(BOARD_${TARGET_BOARD})

# ── Compiler Warnings ───────────────────────────────────────────
add_compile_options(-Wall -Wextra -Wno-unused-parameter)

# ── Include Paths ───────────────────────────────────────────────
include_directories(${CMAKE_SOURCE_DIR}/include)

# ── Source Files ────────────────────────────────────────────────
set(GAME_SOURCES
    src/game/event.c
    src/game/time_mgr.c
    src/game/stat.c
    src/game/emotion.c
    src/game/life.c
    src/game/dialog.c
    src/game/progress.c
    src/game/game_loop.c
)

set(SENSOR_SOURCES
    src/sensor/sensor.c
)

set(UI_SOURCES
    src/ui/input.c
    src/ui/render.c
    src/ui/ui.c
)

set(API_SOURCES
    src/platform/desktop/dilder_api.c
)

set(ALL_SOURCES
    ${GAME_SOURCES}
    ${SENSOR_SOURCES}
    ${UI_SOURCES}
    ${API_SOURCES}
)

# ── Shared Library (loaded by DevTool via ctypes) ───────────────
add_library(dilder SHARED ${ALL_SOURCES})
target_link_libraries(dilder m)  # math library

# ── Standalone Executable (for CLI testing) ─────────────────────
add_executable(dilder_cli
    src/platform/desktop/main_desktop.c
    ${GAME_SOURCES}
    ${SENSOR_SOURCES}
    ${UI_SOURCES}
    ${API_SOURCES}
)
target_link_libraries(dilder_cli m)

# ── Install ─────────────────────────────────────────────────────
install(TARGETS dilder LIBRARY DESTINATION lib)
install(TARGETS dilder_cli RUNTIME DESTINATION bin)
