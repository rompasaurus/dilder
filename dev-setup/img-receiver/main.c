/**
 * IMG Receiver — Serial image display firmware for Dilder DevTool
 *
 * Listens on USB serial for the IMG: protocol and displays received
 * images on a Waveshare 2.13" e-Paper V3 via SPI1.
 *
 * Protocol (from DevTool):
 *   "IMG:"                        — 4-byte header
 *   uint16_t width  (LE)          — image width  (250)
 *   uint16_t height (LE)          — image height (122)
 *   <packed bitmap bytes>         — 1-bit MSB-first, ceil(width/8)*height bytes
 *
 * Wiring (same as hello-world):
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

/* Display dimensions (native orientation) */
#define DISP_W  EPD_2in13_V3_WIDTH   /* 122 */
#define DISP_H  EPD_2in13_V3_HEIGHT  /* 250 */

/* Landscape dimensions (what DevTool sends) */
#define IMG_W   250
#define IMG_H   122

/* Bytes per row in the packed bitmap the DevTool sends */
#define IMG_ROW_BYTES  ((IMG_W + 7) / 8)   /* 32 */
#define IMG_TOTAL      (IMG_ROW_BYTES * IMG_H)  /* 3904 */

/* Image buffer used by the display driver (native orientation) */
static uint8_t display_buf[((DISP_W + 7) / 8) * DISP_H];

/* Receive buffer (landscape orientation from DevTool) */
static uint8_t recv_buf[IMG_TOTAL];

/**
 * Read exactly `count` bytes from stdin into `buf`.
 * Returns true on success, false on timeout/error.
 */
static bool read_exact(uint8_t *buf, uint32_t count, uint32_t timeout_ms) {
    absolute_time_t deadline = make_timeout_time_ms(timeout_ms);
    uint32_t got = 0;
    while (got < count) {
        int ch = getchar_timeout_us(1000);  /* 1 ms poll */
        if (ch != PICO_ERROR_TIMEOUT) {
            buf[got++] = (uint8_t)ch;
        }
        if (absolute_time_diff_us(get_absolute_time(), deadline) < 0) {
            return false;  /* timed out */
        }
    }
    return true;
}

/**
 * Transpose the landscape bitmap (250w x 122h) into the native
 * display orientation (122w x 250h, rotated 90 CW) so we can
 * pass it straight to EPD_2in13_V3_Display().
 *
 * DevTool pixel (x, y) in landscape where x=[0..249], y=[0..121]
 * maps to display pixel (y, 249-x) in portrait.
 */
static void transpose_to_display(const uint8_t *src, uint8_t *dst) {
    uint16_t dst_row_bytes = (DISP_W + 7) / 8;  /* 16 */
    memset(dst, 0xFF, dst_row_bytes * DISP_H);   /* white = 0xFF for e-ink */

    for (int y = 0; y < IMG_H; y++) {
        for (int x = 0; x < IMG_W; x++) {
            /* Read source pixel (landscape) */
            int src_byte = y * IMG_ROW_BYTES + x / 8;
            int src_bit  = 7 - (x % 8);
            int pixel    = (src[src_byte] >> src_bit) & 1;  /* 1 = black */

            if (pixel) {
                /* Map to display native coords */
                int dx = y;            /* display x = landscape y */
                int dy = 249 - x;     /* display y = 249 - landscape x */

                int dst_byte = dy * dst_row_bytes + dx / 8;
                int dst_bit  = 7 - (dx % 8);
                dst[dst_byte] &= ~(1 << dst_bit);  /* 0 = black for e-ink */
            }
        }
    }
}

int main(void) {
    /* Initialize USB serial */
    stdio_init_all();
    sleep_ms(2000);

    printf("IMG Receiver ready.\n");
    printf("Waiting for display init...\n");

    /* Initialize hardware (SPI + GPIO) */
    if (DEV_Module_Init() != 0) {
        printf("ERROR: Hardware init failed.\n");
        return 1;
    }

    /* Initialize display */
    EPD_2in13_V3_Init();
    EPD_2in13_V3_Clear();
    printf("Display ready. Listening for IMG: commands...\n");

    uint8_t header[4];
    uint8_t dim_buf[4];
    uint32_t frame_count = 0;

    while (true) {
        /* Wait for 'I' */
        int ch = getchar_timeout_us(100000);  /* 100ms poll */
        if (ch == PICO_ERROR_TIMEOUT) continue;

        if (ch != 'I') continue;

        /* Try to read "MG:" */
        if (!read_exact(header, 3, 500)) continue;
        if (header[0] != 'M' || header[1] != 'G' || header[2] != ':') continue;

        /* Read width and height (uint16 LE each) */
        if (!read_exact(dim_buf, 4, 1000)) {
            printf("Timeout reading dimensions.\n");
            continue;
        }

        uint16_t w = dim_buf[0] | (dim_buf[1] << 8);
        uint16_t h = dim_buf[2] | (dim_buf[3] << 8);

        if (w != IMG_W || h != IMG_H) {
            printf("Bad dimensions: %dx%d (expected %dx%d)\n", w, h, IMG_W, IMG_H);
            continue;
        }

        /* Read pixel data */
        uint32_t expected = IMG_ROW_BYTES * h;
        if (!read_exact(recv_buf, expected, 5000)) {
            printf("Timeout reading %lu bytes of pixel data.\n",
                   (unsigned long)expected);
            continue;
        }

        frame_count++;
        printf("Frame %lu received (%lu bytes). Updating display...\n",
               (unsigned long)frame_count, (unsigned long)expected);

        /* Transpose landscape → native portrait and display */
        transpose_to_display(recv_buf, display_buf);

        if (frame_count == 1) {
            /* First frame: full refresh */
            EPD_2in13_V3_Display(display_buf);
        } else {
            /* Subsequent frames: partial refresh (faster) */
            EPD_2in13_V3_Display_Partial(display_buf);
        }

        printf("Display updated.\n");
    }

    return 0;
}
