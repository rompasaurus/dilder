cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(sassy_octopus C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

# Display variant: pass -DDISPLAY_VARIANT=V2|V3|V3a|V4 to cmake.
# Default is V3 (standard).
if(NOT DEFINED DISPLAY_VARIANT)
    set(DISPLAY_VARIANT "V3")
endif()

if(DISPLAY_VARIANT STREQUAL "V2")
    set(EPD_SOURCE lib/e-Paper/EPD_2in13_V2.c)
    set(EPD_DEFINE DISPLAY_V2)
    message(STATUS "Display variant: V2 (SSD1675B)")
elseif(DISPLAY_VARIANT STREQUAL "V3a")
    set(EPD_SOURCE lib/e-Paper/EPD_2in13_V3a.c)
    set(EPD_DEFINE DISPLAY_V3A)
    message(STATUS "Display variant: V3a (revision A)")
elseif(DISPLAY_VARIANT STREQUAL "V4")
    set(EPD_SOURCE lib/e-Paper/EPD_2in13_V4.c)
    set(EPD_DEFINE DISPLAY_V4)
    message(STATUS "Display variant: V4 (internal LUT)")
else()
    set(EPD_SOURCE lib/e-Paper/EPD_2in13_V3.c)
    set(EPD_DEFINE "")
    message(STATUS "Display variant: V3 (standard)")
endif()

add_executable(sassy_octopus
    main.c
    lib/Config/DEV_Config.c
    ${EPD_SOURCE}
)

if(EPD_DEFINE)
    target_compile_definitions(sassy_octopus PRIVATE ${EPD_DEFINE}=1)
endif()

target_include_directories(sassy_octopus PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/Config
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/e-Paper
)

target_link_libraries(sassy_octopus
    pico_stdlib
    hardware_spi
    hardware_gpio
    hardware_adc
    hardware_rtc
    m
)

pico_enable_stdio_usb(sassy_octopus 1)
pico_enable_stdio_uart(sassy_octopus 0)

pico_add_extra_outputs(sassy_octopus)
