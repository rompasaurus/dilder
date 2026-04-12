cmake_minimum_required(VERSION 3.13)

# Pull in the Pico SDK (must come before project())
include(pico_sdk_import.cmake)

project(img_receiver C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the Pico SDK
pico_sdk_init()

# ---------- Source files ----------

add_executable(img_receiver
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

target_include_directories(img_receiver PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/Config
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/e-Paper
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/GUI
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/Fonts
)

# ---------- Pico SDK libraries ----------

target_link_libraries(img_receiver
    pico_stdlib
    hardware_spi
    hardware_gpio
)

# ---------- USB serial ----------
pico_enable_stdio_usb(img_receiver 1)
pico_enable_stdio_uart(img_receiver 0)

# ---------- Output files ----------
pico_add_extra_outputs(img_receiver)
