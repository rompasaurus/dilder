cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(sassy_octopus C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(sassy_octopus
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

target_include_directories(sassy_octopus PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/Config
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/e-Paper
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/GUI
    ${CMAKE_CURRENT_SOURCE_DIR}/lib/Fonts
)

target_link_libraries(sassy_octopus
    pico_stdlib
    hardware_spi
    hardware_gpio
)

pico_enable_stdio_usb(sassy_octopus 1)
pico_enable_stdio_uart(sassy_octopus 0)

pico_add_extra_outputs(sassy_octopus)
