/**
 * Hello World — Bare-minimum Pico W serial test
 *
 * No display, no wiring, no external libraries.
 * Just the Pico W plugged into USB.
 *
 * Verifies:
 *   - Toolchain compiles correctly
 *   - UF2 flashes to the board
 *   - USB serial (printf) works at 115200 baud
 *   - The board is alive and running your code
 *
 * Note: The Pico W's onboard LED is connected to the CYW43 Wi-Fi chip,
 * not a regular GPIO pin. We use cyw43_arch to control it.
 *
 * Open a serial monitor after flashing:
 *   screen /dev/ttyACM0 115200
 */

#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"

int main(void) {
    /* Initialize USB serial output */
    stdio_init_all();

    /* Initialize the CYW43 Wi-Fi chip (needed to control the onboard LED) */
    if (cyw43_arch_init()) {
        printf("ERROR: CYW43 init failed\n");
        return 1;
    }

    /* Wait for the USB connection to enumerate */
    sleep_ms(2000);

    printf("=========================\n");
    printf("  Hello, Dilder!\n");
    printf("  Pico W is alive.\n");
    printf("=========================\n\n");

    /* Blink the onboard LED and print a heartbeat */
    uint32_t count = 0;
    bool led_on = false;

    while (true) {
        count++;
        led_on = !led_on;
        cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, led_on);

        printf("Heartbeat #%lu  |  LED: %s\n",
               (unsigned long)count,
               led_on ? "ON" : "OFF");

        sleep_ms(1000);
    }

    return 0;
}
