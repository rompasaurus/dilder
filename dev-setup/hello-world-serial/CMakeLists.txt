cmake_minimum_required(VERSION 3.13)

# Pull in the Pico SDK (must come before project())
include(pico_sdk_import.cmake)

project(hello_serial C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the Pico SDK
pico_sdk_init()

# ---------- Executable ----------

add_executable(hello_serial
    main.c
)

# ---------- Link libraries ----------
# pico_cyw43_arch_none: needed to control the Pico W onboard LED,
# which is wired to the CYW43 Wi-Fi chip (not a regular GPIO pin).

target_link_libraries(hello_serial
    pico_stdlib
    pico_cyw43_arch_none
)

# ---------- USB serial output ----------
pico_enable_stdio_usb(hello_serial 1)
pico_enable_stdio_uart(hello_serial 0)

# ---------- Output .uf2, .hex, .bin, .dis ----------
pico_add_extra_outputs(hello_serial)
