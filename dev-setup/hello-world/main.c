/**
 * Hello Dilder — First e-ink display test
 *
 * Draws "Hello, Dilder!" on a Waveshare 2.13" e-Paper V3
 * connected to a Raspberry Pi Pico W via SPI1.
 *
 * Wiring:
 *   VCC  -> 3V3(OUT) pin 36
 *   GND  -> GND      pin 38
 *   DIN  -> GP11     pin 15  (SPI1 TX)
 *   CLK  -> GP10     pin 14  (SPI1 SCK)
 *   CS   -> GP9      pin 12  (SPI1 CSn)
 *   DC   -> GP8      pin 11
 *   RST  -> GP12     pin 16
 *   BUSY -> GP13     pin 17
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "DEV_Config.h"
#include "EPD_2in13_V3.h"
#include "GUI_Paint.h"
#include "fonts.h"

/* Display dimensions (landscape orientation) */
#define DISPLAY_WIDTH   EPD_2in13_V3_WIDTH    /* 122 */
#define DISPLAY_HEIGHT  EPD_2in13_V3_HEIGHT   /* 250 */

int main(void) {
    /* ---- 1. Initialize USB serial (printf) ---- */
    stdio_init_all();

    /*
     * Brief delay so the USB serial connection has time to
     * enumerate. Without this, early printf() output is lost.
     */
    sleep_ms(2000);

    printf("Hello, Dilder!\n");
    printf("Initializing e-Paper display...\n");

    /* ---- 2. Initialize hardware (SPI + GPIO) ---- */
    if (DEV_Module_Init() != 0) {
        printf("ERROR: Hardware init failed.\n");
        return 1;
    }

    /* ---- 3. Initialize the display driver ---- */
    EPD_2in13_V3_Init();
    EPD_2in13_V3_Clear();
    printf("Display initialized.\n");

    /* ---- 4. Allocate the image buffer ---- */
    /*
     * The buffer holds a 1-bit monochrome image.
     * Width is padded to the nearest byte boundary (multiples of 8).
     */
    uint16_t image_width  = DISPLAY_WIDTH;
    uint16_t image_height = DISPLAY_HEIGHT;

    /* Bytes per row, rounded up */
    uint16_t image_size = ((image_width % 8 == 0)
                            ? (image_width / 8)
                            : (image_width / 8 + 1))
                          * image_height;

    uint8_t *image_buffer = (uint8_t *)malloc(image_size);
    if (!image_buffer) {
        printf("ERROR: Could not allocate image buffer (%d bytes).\n", image_size);
        return 1;
    }

    printf("Drawing to display...\n");

    /* ---- 5. Create the image and draw ---- */
    Paint_NewImage(image_buffer, image_width, image_height, 90, WHITE);
    Paint_SelectImage(image_buffer);
    Paint_Clear(WHITE);

    /* Draw a border */
    Paint_DrawRectangle(1, 1, image_height - 2, image_width - 2, BLACK, DOT_PIXEL_1X1, DRAW_FILL_EMPTY);

    /* Draw text */
    Paint_DrawString_EN(10, 10, "Hello, Dilder!", &Font24, WHITE, BLACK);
    Paint_DrawString_EN(10, 42, "Pico W + e-Paper V3", &Font16, WHITE, BLACK);
    Paint_DrawString_EN(10, 66, "First build successful!", &Font12, WHITE, BLACK);

    /* ---- 6. Send the image to the display ---- */
    EPD_2in13_V3_Display(image_buffer);

    printf("Display updated. Entering sleep mode.\n");

    /* ---- 7. Put the display to sleep (saves power) ---- */
    EPD_2in13_V3_Sleep();

    /* Free the buffer */
    free(image_buffer);

    /* ---- 8. Heartbeat loop on serial ---- */
    uint32_t count = 0;
    while (true) {
        count++;
        printf("Heartbeat: %lu\n", (unsigned long)count);
        sleep_ms(5000);
    }

    return 0;
}
