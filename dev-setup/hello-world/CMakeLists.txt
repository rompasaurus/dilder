cmake_minimum_required(VERSION 3.13)

# Pull in the Pico SDK (must come before project())
include(pico_sdk_import.cmake)

project(hello_dilder C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the Pico SDK
pico_sdk_init()

# ---------- Source files ----------

add_executable(hello_dilder
    main.c
    lib/Config/DEV_Config.c
    lib/e-Paper/EPD_2in13_V3.c
    lib/GUI/GUI_Paint.c
    lib/Fonts/font8.c
    lib/Fonts/font12.c
    lib/Fonts/font16.c
    lib/Fonts/font20.c
    lib/Fonts/font24.c
)

# ---------- Include paths ----------

target_include_directories(hello_dilder PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/Config
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/e-Paper
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/GUI
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/Fonts
)

# ---------- Pico SDK libraries ----------

target_link_libraries(hello_dilder
    pico_stdlib          # GPIO, time, printf
    hardware_spi         # SPI controller
    hardware_gpio        # GPIO control
)

# ---------- USB serial output ----------
# Enable printf over USB (shows up as /dev/ttyACM0)
# Disable printf over UART (we don't use UART pins)
pico_enable_stdio_usb(hello_dilder 1)
pico_enable_stdio_uart(hello_dilder 0)

# ---------- Output files ----------
# Generates .uf2, .hex, .bin, .dis alongside the .elf
pico_add_extra_outputs(hello_dilder)
