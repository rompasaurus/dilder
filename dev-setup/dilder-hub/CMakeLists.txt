cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(dilder_hub C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

# Display variant: pass -DDISPLAY_VARIANT=V2|V3|V3a|V4 to cmake.
if(NOT DEFINED DISPLAY_VARIANT)
    set(DISPLAY_VARIANT "V4")
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

add_executable(dilder_hub
    main.c
    lib/Config/DEV_Config.c
    ${EPD_SOURCE}
)

if(EPD_DEFINE)
    target_compile_definitions(dilder_hub PRIVATE ${EPD_DEFINE}=1)
endif()

target_include_directories(dilder_hub PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/lib
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/Config
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/e-Paper
)

target_link_libraries(dilder_hub
    pico_stdlib
    hardware_spi
    hardware_gpio
    hardware_adc
    hardware_pwm
    hardware_i2c
    pico_cyw43_arch_lwip_poll
    m
)

# WiFi credentials — pass via cmake -D or edit wifi_config.h
if(DEFINED WIFI_SSID)
    target_compile_definitions(dilder_hub PRIVATE WIFI_SSID="${WIFI_SSID}")
endif()
if(DEFINED WIFI_PASS)
    target_compile_definitions(dilder_hub PRIVATE WIFI_PASS="${WIFI_PASS}")
endif()

# hardware_rtc only exists on RP2040 — RP2350 uses software fallback
if(PICO_PLATFORM STREQUAL "rp2040")
    target_link_libraries(dilder_hub hardware_rtc)
endif()

pico_enable_stdio_usb(dilder_hub 1)
pico_enable_stdio_uart(dilder_hub 0)

pico_add_extra_outputs(dilder_hub)
