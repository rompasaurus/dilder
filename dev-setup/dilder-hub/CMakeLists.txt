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
    bt.c
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
    hardware_flash
    pico_cyw43_arch_lwip_poll
    m
)

# ── Bluetooth LE (BTstack) — peripheral pairing for phones ──
target_compile_definitions(dilder_hub PRIVATE CYW43_ENABLE_BLUETOOTH=1)
target_link_libraries(dilder_hub pico_btstack_ble pico_btstack_cyw43)
# Generate dilder.h (profile_data) from the GATT database.
pico_btstack_make_gatt_header(dilder_hub PRIVATE ${CMAKE_CURRENT_LIST_DIR}/dilder.gatt)

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

# In an OTA build, picowota_build_combined() drives the output artifacts
# (it calls picowota_build_standalone → pico_add_bin_output itself). Calling
# pico_add_extra_outputs here too would define dilder_hub.bin twice, which the
# Ninja generator rejects ("defined as an output multiple times"). So only add
# the normal USB outputs (.uf2/.bin/.hex) for non-OTA builds.
if(NOT PICOWOTA_OTA)
    pico_add_extra_outputs(dilder_hub)
endif()

# ── picowota WiFi OTA (optional) ─────────────────────────────────
# Enable with:  cmake -DPICOWOTA_OTA=ON -DPICO_BOARD=pico2_w \
#                     -DWIFI_SSID="..." -DWIFI_PASS="..." ..
# Produces:
#   picowota_dilder_hub.uf2  — bootloader+app combined image; flash ONCE
#                              over BOOTSEL/USB to install the OTA bootloader.
#   dilder_hub.elf           — standalone app image; push over WiFi with
#                              `serial-flash tcp:<pico-ip>:4242 dilder_hub.elf`.
# The bootloader joins the same WiFi network as the app (reuses WIFI_SSID/PASS).
option(PICOWOTA_OTA "Build the picowota WiFi OTA bootloader + combined image" OFF)
if(PICOWOTA_OTA)
    if(DEFINED WIFI_SSID AND NOT DEFINED PICOWOTA_WIFI_SSID)
        set(PICOWOTA_WIFI_SSID "${WIFI_SSID}")
    endif()
    if(DEFINED WIFI_PASS AND NOT DEFINED PICOWOTA_WIFI_PASS)
        set(PICOWOTA_WIFI_PASS "${WIFI_PASS}")
    endif()
    if(NOT DEFINED PICOWOTA_WIFI_AP)
        set(PICOWOTA_WIFI_AP 0)  # 0 = join existing network, 1 = create AP
    endif()

    add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../../picowota picowota)
    target_link_libraries(dilder_hub picowota_reboot)
    target_compile_definitions(dilder_hub PRIVATE PICOWOTA_OTA=1)
    picowota_build_combined(dilder_hub)
endif()
