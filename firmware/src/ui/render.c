/*
 * render.c -- Framebuffer Graphics and Screen Renderers
 *
 * PURPOSE:
 *   This module provides all the drawing routines for the Dilder display.
 *   It operates on a 1-bit-per-pixel framebuffer: a flat array of bytes
 *   where each bit represents one pixel (on or off, black or white).
 *
 *   The module is organized in layers, from lowest to highest:
 *     1. PIXEL OPERATIONS   -- set/clear/read individual pixels
 *     2. DRAWING PRIMITIVES -- lines, rectangles, circles
 *     3. TEXT RENDERING     -- bitmap font character/string drawing
 *     4. HIGH-LEVEL RENDERERS -- compose full screens (pet, menu, stats)
 *
 * 1-BIT FRAMEBUFFER LAYOUT:
 *   The display is 250 pixels wide x 122 pixels tall. Each pixel is a
 *   single bit (1 = on/black, 0 = off/white). Bits are packed 8-per-byte,
 *   with the MOST SIGNIFICANT BIT (MSB, bit 7) representing the LEFTMOST
 *   pixel in each group of 8.
 *
 *   Each row of 250 pixels requires ceil(250/8) = 32 bytes (256 bits,
 *   with the last 6 bits unused). This is SCREEN_ROW_BYTES = 32.
 *
 *   The total buffer is 32 bytes/row * 122 rows = 3904 bytes = SCREEN_BUF_SIZE.
 *
 *   To find the byte and bit for pixel (x, y):
 *     byte_index = y * SCREEN_ROW_BYTES + x / 8
 *       - y * SCREEN_ROW_BYTES skips to the correct row
 *       - x / 8 skips to the correct byte within that row
 *         (integer division: pixel 0-7 -> byte 0, pixel 8-15 -> byte 1, etc.)
 *     bit_mask = 0x80 >> (x & 7)
 *       - 0x80 is binary 10000000 (MSB set)
 *       - (x & 7) gives the pixel's position within its byte (0-7)
 *         This is equivalent to (x % 8) but faster because & is a single
 *         CPU instruction. It works because 7 is 0b111, so AND-ing with 7
 *         keeps only the lowest 3 bits, which is the remainder when dividing by 8.
 *       - >> shifts the bit rightward by that amount
 *       - Example: x=3 -> 0x80 >> 3 = 0b00010000 = the 4th pixel from left
 *
 * BITMAP FONT:
 *   The font is a 6x8 pixel bitmap font covering ASCII characters 32-126
 *   (space through tilde). Each character is stored as 6 bytes, one per
 *   COLUMN (not row!). Each byte's 8 bits represent the 8 rows of that
 *   column, with bit 0 = top row and bit 7 = bottom row.
 *
 *   To draw character 'A' (ASCII 65):
 *     1. index = 65 - 32 = 33 (offset from first printable char)
 *     2. Look up FONT_6X8[33] to get 6 bytes: {0x7E,0x11,0x11,0x11,0x7E,0x00}
 *     3. For each column (0-5), check each bit (0-7):
 *        if (byte & (1 << row)) then set the pixel at (x+col, y+row)
 *
 *   Column 0 of 'A' is 0x7E = 0b01111110, meaning rows 1-6 are lit
 *   (the vertical stroke of the letter). The 6th byte is always 0x00,
 *   acting as a 1-pixel gap between characters.
 */

#include "ui/render.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

/* ─── Global Framebuffer ─────────────────────────────────────── */

/*
 * The framebuffer: a flat array of 3904 bytes representing the 250x122
 * 1-bit display. This is declared `extern` in game_state.h so other
 * modules (like the SDL display driver) can read it to push pixels to
 * the actual screen.
 *
 * Unlike the `static` variables in sensor.c and input.c, this is
 * intentionally global -- the display driver needs to read it.
 */
uint8_t g_framebuffer[SCREEN_BUF_SIZE];

/* ─── 6x8 Bitmap Font (ASCII 32-126) ────────────────────────── */
/*
 * Each character is stored as 6 bytes, one per column (left to right).
 * Each byte encodes 8 rows of that column, with bit 0 = topmost row.
 * The 6th column is usually 0x00 to provide inter-character spacing.
 *
 * For example, '!' is {0x00, 0x00, 0x5F, 0x00, 0x00, 0x00}:
 *   - Columns 0,1 are blank (0x00)
 *   - Column 2 is 0x5F = 0b01011111, so rows 0-4 and 6 are lit
 *     (a vertical line with a dot below -- the exclamation mark)
 *   - Columns 3-5 are blank
 *
 * This column-major layout is common in embedded fonts because it makes
 * the rendering loop simple: for each column, shift through the bits
 * and set pixels vertically.
 */
static const uint8_t FONT_6X8[][6] = {
    /* space */ {0x00,0x00,0x00,0x00,0x00,0x00},
    /* !     */ {0x00,0x00,0x5F,0x00,0x00,0x00},
    /* "     */ {0x00,0x07,0x00,0x07,0x00,0x00},
    /* #     */ {0x14,0x7F,0x14,0x7F,0x14,0x00},
    /* $     */ {0x24,0x2A,0x7F,0x2A,0x12,0x00},
    /* %     */ {0x23,0x13,0x08,0x64,0x62,0x00},
    /* &     */ {0x36,0x49,0x55,0x22,0x50,0x00},
    /* '     */ {0x00,0x05,0x03,0x00,0x00,0x00},
    /* (     */ {0x00,0x1C,0x22,0x41,0x00,0x00},
    /* )     */ {0x00,0x41,0x22,0x1C,0x00,0x00},
    /* *     */ {0x08,0x2A,0x1C,0x2A,0x08,0x00},
    /* +     */ {0x08,0x08,0x3E,0x08,0x08,0x00},
    /* ,     */ {0x00,0x50,0x30,0x00,0x00,0x00},
    /* -     */ {0x08,0x08,0x08,0x08,0x08,0x00},
    /* .     */ {0x00,0x60,0x60,0x00,0x00,0x00},
    /* /     */ {0x20,0x10,0x08,0x04,0x02,0x00},
    /* 0     */ {0x3E,0x51,0x49,0x45,0x3E,0x00},
    /* 1     */ {0x00,0x42,0x7F,0x40,0x00,0x00},
    /* 2     */ {0x42,0x61,0x51,0x49,0x46,0x00},
    /* 3     */ {0x21,0x41,0x45,0x4B,0x31,0x00},
    /* 4     */ {0x18,0x14,0x12,0x7F,0x10,0x00},
    /* 5     */ {0x27,0x45,0x45,0x45,0x39,0x00},
    /* 6     */ {0x3C,0x4A,0x49,0x49,0x30,0x00},
    /* 7     */ {0x01,0x71,0x09,0x05,0x03,0x00},
    /* 8     */ {0x36,0x49,0x49,0x49,0x36,0x00},
    /* 9     */ {0x06,0x49,0x49,0x29,0x1E,0x00},
    /* :     */ {0x00,0x36,0x36,0x00,0x00,0x00},
    /* ;     */ {0x00,0x56,0x36,0x00,0x00,0x00},
    /* <     */ {0x00,0x08,0x14,0x22,0x41,0x00},
    /* =     */ {0x14,0x14,0x14,0x14,0x14,0x00},
    /* >     */ {0x41,0x22,0x14,0x08,0x00,0x00},
    /* ?     */ {0x02,0x01,0x51,0x09,0x06,0x00},
    /* @     */ {0x32,0x49,0x79,0x41,0x3E,0x00},
    /* A     */ {0x7E,0x11,0x11,0x11,0x7E,0x00},
    /* B     */ {0x7F,0x49,0x49,0x49,0x36,0x00},
    /* C     */ {0x3E,0x41,0x41,0x41,0x22,0x00},
    /* D     */ {0x7F,0x41,0x41,0x22,0x1C,0x00},
    /* E     */ {0x7F,0x49,0x49,0x49,0x41,0x00},
    /* F     */ {0x7F,0x09,0x09,0x01,0x01,0x00},
    /* G     */ {0x3E,0x41,0x41,0x51,0x32,0x00},
    /* H     */ {0x7F,0x08,0x08,0x08,0x7F,0x00},
    /* I     */ {0x00,0x41,0x7F,0x41,0x00,0x00},
    /* J     */ {0x20,0x40,0x41,0x3F,0x01,0x00},
    /* K     */ {0x7F,0x08,0x14,0x22,0x41,0x00},
    /* L     */ {0x7F,0x40,0x40,0x40,0x40,0x00},
    /* M     */ {0x7F,0x02,0x04,0x02,0x7F,0x00},
    /* N     */ {0x7F,0x04,0x08,0x10,0x7F,0x00},
    /* O     */ {0x3E,0x41,0x41,0x41,0x3E,0x00},
    /* P     */ {0x7F,0x09,0x09,0x09,0x06,0x00},
    /* Q     */ {0x3E,0x41,0x51,0x21,0x5E,0x00},
    /* R     */ {0x7F,0x09,0x19,0x29,0x46,0x00},
    /* S     */ {0x46,0x49,0x49,0x49,0x31,0x00},
    /* T     */ {0x01,0x01,0x7F,0x01,0x01,0x00},
    /* U     */ {0x3F,0x40,0x40,0x40,0x3F,0x00},
    /* V     */ {0x1F,0x20,0x40,0x20,0x1F,0x00},
    /* W     */ {0x7F,0x20,0x18,0x20,0x7F,0x00},
    /* X     */ {0x63,0x14,0x08,0x14,0x63,0x00},
    /* Y     */ {0x03,0x04,0x78,0x04,0x03,0x00},
    /* Z     */ {0x61,0x51,0x49,0x45,0x43,0x00},
    /* [     */ {0x00,0x00,0x7F,0x41,0x41,0x00},
    /* \     */ {0x02,0x04,0x08,0x10,0x20,0x00},
    /* ]     */ {0x00,0x41,0x41,0x7F,0x00,0x00},
    /* ^     */ {0x04,0x02,0x01,0x02,0x04,0x00},
    /* _     */ {0x40,0x40,0x40,0x40,0x40,0x00},
    /* `     */ {0x00,0x01,0x02,0x04,0x00,0x00},
    /* a     */ {0x20,0x54,0x54,0x54,0x78,0x00},
    /* b     */ {0x7F,0x48,0x44,0x44,0x38,0x00},
    /* c     */ {0x38,0x44,0x44,0x44,0x20,0x00},
    /* d     */ {0x38,0x44,0x44,0x48,0x7F,0x00},
    /* e     */ {0x38,0x54,0x54,0x54,0x18,0x00},
    /* f     */ {0x08,0x7E,0x09,0x01,0x02,0x00},
    /* g     */ {0x08,0x14,0x54,0x54,0x3C,0x00},
    /* h     */ {0x7F,0x08,0x04,0x04,0x78,0x00},
    /* i     */ {0x00,0x44,0x7D,0x40,0x00,0x00},
    /* j     */ {0x20,0x40,0x44,0x3D,0x00,0x00},
    /* k     */ {0x00,0x7F,0x10,0x28,0x44,0x00},
    /* l     */ {0x00,0x41,0x7F,0x40,0x00,0x00},
    /* m     */ {0x7C,0x04,0x18,0x04,0x78,0x00},
    /* n     */ {0x7C,0x08,0x04,0x04,0x78,0x00},
    /* o     */ {0x38,0x44,0x44,0x44,0x38,0x00},
    /* p     */ {0x7C,0x14,0x14,0x14,0x08,0x00},
    /* q     */ {0x08,0x14,0x14,0x18,0x7C,0x00},
    /* r     */ {0x7C,0x08,0x04,0x04,0x08,0x00},
    /* s     */ {0x48,0x54,0x54,0x54,0x20,0x00},
    /* t     */ {0x04,0x3F,0x44,0x40,0x20,0x00},
    /* u     */ {0x3C,0x40,0x40,0x20,0x7C,0x00},
    /* v     */ {0x1C,0x20,0x40,0x20,0x1C,0x00},
    /* w     */ {0x3C,0x40,0x30,0x40,0x3C,0x00},
    /* x     */ {0x44,0x28,0x10,0x28,0x44,0x00},
    /* y     */ {0x0C,0x50,0x50,0x50,0x3C,0x00},
    /* z     */ {0x44,0x64,0x54,0x4C,0x44,0x00},
    /* {     */ {0x00,0x08,0x36,0x41,0x00,0x00},
    /* |     */ {0x00,0x00,0x7F,0x00,0x00,0x00},
    /* }     */ {0x00,0x41,0x36,0x08,0x00,0x00},
    /* ~     */ {0x08,0x08,0x2A,0x1C,0x08,0x00},
};

/*
 * Font configuration constants:
 *   FONT_FIRST_CHAR (32) = ASCII space, the first printable character
 *   FONT_LAST_CHAR (126) = ASCII tilde, the last printable character
 *   FONT_CHAR_W (6) = character width in pixels (5 columns + 1 gap)
 *   FONT_CHAR_H (8) = character height in pixels (8 rows)
 *
 * To get the font table index for a character:
 *   index = ascii_value - FONT_FIRST_CHAR
 * Example: 'A' = 65, index = 65 - 32 = 33
 */
#define FONT_FIRST_CHAR 32
#define FONT_LAST_CHAR  126
#define FONT_CHAR_W 6
#define FONT_CHAR_H 8

/* ─── Pixel Operations ───────────────────────────────────────── */

/*
 * fb_clear -- Clear the entire framebuffer (all pixels OFF / white).
 *
 * Parameters: none
 * Returns:    nothing
 *
 * memset fills every byte with 0x00. Since each bit is a pixel,
 * 0x00 = 00000000 binary = all 8 pixels in that byte are OFF.
 */
void fb_clear(void) {
    memset(g_framebuffer, 0x00, SCREEN_BUF_SIZE);
}

/*
 * fb_fill -- Fill the entire framebuffer (all pixels ON / black).
 *
 * Parameters: none
 * Returns:    nothing
 *
 * 0xFF = 11111111 binary = all 8 pixels in each byte are ON.
 */
void fb_fill(void) {
    memset(g_framebuffer, 0xFF, SCREEN_BUF_SIZE);
}

/*
 * fb_set_pixel -- Turn ON a single pixel at coordinates (x, y).
 *
 * Parameters:
 *   x  -- horizontal position (0 = left edge, SCREEN_W-1 = right edge)
 *   y  -- vertical position (0 = top edge, SCREEN_H-1 = bottom edge)
 *
 * Returns: nothing
 *
 * The bounds check prevents writing outside the framebuffer array,
 * which would corrupt other memory (a common source of bugs in C).
 *
 * Bitwise breakdown of the key line:
 *   g_framebuffer[y * SCREEN_ROW_BYTES + x / 8] |= (0x80 >> (x & 7));
 *
 *   Step 1: Find the byte
 *     y * SCREEN_ROW_BYTES  -- skip y full rows (each row is 32 bytes)
 *     x / 8                 -- skip to the byte containing pixel x
 *     Together: the byte index in the flat array
 *
 *   Step 2: Create a bitmask for the target pixel
 *     (x & 7)   -- pixel position within the byte (0-7), same as x % 8
 *     0x80 >> n  -- shift a 1-bit from the MSB rightward by n positions
 *       x&7=0: 0x80 = 10000000  (leftmost pixel in byte)
 *       x&7=1: 0x40 = 01000000
 *       x&7=2: 0x20 = 00100000
 *       ...
 *       x&7=7: 0x01 = 00000001  (rightmost pixel in byte)
 *
 *   Step 3: Set the bit using OR-assign (|=)
 *     |= turns ON just that one bit without affecting the other 7 pixels
 *     in the same byte. Example: 01000000 |= 00100000 = 01100000
 */
void fb_set_pixel(int x, int y) {
    if (x < 0 || x >= SCREEN_W || y < 0 || y >= SCREEN_H) return;
    g_framebuffer[y * SCREEN_ROW_BYTES + x / 8] |= (0x80 >> (x & 7));
}

/*
 * fb_clr_pixel -- Turn OFF a single pixel at coordinates (x, y).
 *
 * Parameters:
 *   x, y  -- pixel coordinates (same as fb_set_pixel)
 *
 * Returns: nothing
 *
 * Similar to fb_set_pixel, but uses AND with the INVERTED mask to clear:
 *   &= ~(mask)
 *
 *   ~ is the bitwise NOT operator: it flips every bit.
 *   ~(0x80 >> 2) = ~(00100000) = 11011111
 *
 *   AND-ing with 11011111 clears bit 5 but leaves all other bits unchanged.
 *   This is a common C idiom: "AND with inverted mask to clear a bit."
 */
void fb_clr_pixel(int x, int y) {
    if (x < 0 || x >= SCREEN_W || y < 0 || y >= SCREEN_H) return;
    g_framebuffer[y * SCREEN_ROW_BYTES + x / 8] &= ~(0x80 >> (x & 7));
}

/*
 * fb_get_pixel -- Read the state of a single pixel.
 *
 * Parameters:
 *   x, y  -- pixel coordinates
 *
 * Returns:
 *   1 if the pixel is ON, 0 if OFF (or if out of bounds).
 *
 * Bitwise breakdown:
 *   (g_framebuffer[...] >> (7 - (x & 7))) & 1
 *
 *   First, shift the target bit down to the least significant position:
 *     If x&7=0 (MSB), shift right by 7 to move it to bit 0
 *     If x&7=3, shift right by 4 to move it to bit 0
 *     If x&7=7 (LSB), shift right by 0 (no shift needed)
 *
 *   Then AND with 1 to mask off all other bits, leaving just 0 or 1.
 */
int fb_get_pixel(int x, int y) {
    if (x < 0 || x >= SCREEN_W || y < 0 || y >= SCREEN_H) return 0;
    return (g_framebuffer[y * SCREEN_ROW_BYTES + x / 8] >> (7 - (x & 7))) & 1;
}

/* ─── Drawing Primitives ─────────────────────────────────────── */

/*
 * fb_hline -- Draw a horizontal line (fast, pixel-by-pixel).
 *
 * Parameters:
 *   x  -- starting X coordinate (left end)
 *   y  -- Y coordinate (row)
 *   w  -- width in pixels
 *
 * Returns: nothing
 *
 * Note: this could be optimized to write whole bytes at a time for
 * long horizontal runs, but pixel-by-pixel is simpler and fast enough
 * for a 250-pixel-wide display.
 */
void fb_hline(int x, int y, int w) {
    for (int i = 0; i < w; i++) fb_set_pixel(x + i, y);
}

/*
 * fb_vline -- Draw a vertical line.
 *
 * Parameters:
 *   x  -- X coordinate (column)
 *   y  -- starting Y coordinate (top end)
 *   h  -- height in pixels
 *
 * Returns: nothing
 */
void fb_vline(int x, int y, int h) {
    for (int i = 0; i < h; i++) fb_set_pixel(x, y + i);
}

/*
 * fb_line -- Draw a line between any two points using Bresenham's algorithm.
 *
 * Parameters:
 *   x0, y0  -- starting point
 *   x1, y1  -- ending point
 *
 * Returns: nothing
 *
 * BRESENHAM'S LINE ALGORITHM:
 *   This is a classic algorithm (from 1962!) for drawing lines using only
 *   integer arithmetic -- no floating point, no division in the loop.
 *   It works by maintaining an "error" accumulator that tracks how far
 *   the ideal (mathematical) line deviates from the pixels we've drawn.
 *
 *   Key variables:
 *     dx = horizontal distance (always positive, via abs())
 *     dy = vertical distance (always NEGATIVE, via -abs())
 *          Making dy negative simplifies the error math.
 *     sx, sy = step direction (+1 or -1) for each axis
 *     err = accumulated error: starts at dx + dy
 *
 *   The loop:
 *     1. Draw the current pixel
 *     2. Check if we've reached the endpoint -> done
 *     3. Compute e2 = 2 * err (doubling avoids fractions)
 *     4. If e2 >= dy: the error says "step horizontally"
 *        -> add dy to err (reducing it) and step x by sx
 *     5. If e2 <= dx: the error says "step vertically"
 *        -> add dx to err (increasing it) and step y by sy
 *     6. Repeat
 *
 *   Both steps can happen in the same iteration (for diagonal movement).
 *   The algorithm always produces the closest pixel approximation of the
 *   ideal line, with no gaps.
 */
void fb_line(int x0, int y0, int x1, int y1) {
    int dx = abs(x1 - x0), sx = x0 < x1 ? 1 : -1;  /* dx = positive distance, sx = direction */
    int dy = -abs(y1 - y0), sy = y0 < y1 ? 1 : -1;  /* dy = NEGATIVE distance, sy = direction */
    int err = dx + dy;  /* initial error (sum of positive dx and negative dy) */

    while (1) {
        fb_set_pixel(x0, y0);                   /* draw current pixel */
        if (x0 == x1 && y0 == y1) break;        /* reached endpoint? stop */
        int e2 = 2 * err;                        /* doubled error for comparison */
        if (e2 >= dy) { err += dy; x0 += sx; }  /* error favors horizontal step */
        if (e2 <= dx) { err += dx; y0 += sy; }  /* error favors vertical step */
    }
}

/*
 * fb_rect -- Draw a rectangle, either outlined or filled.
 *
 * Parameters:
 *   x, y    -- top-left corner
 *   w, h    -- width and height in pixels
 *   filled  -- if true, fill the interior; if false, draw only the outline
 *
 * Returns: nothing
 *
 * Filled: draw w-pixel horizontal lines for each row.
 * Outlined: draw the 4 edges (top, bottom, left, right).
 */
void fb_rect(int x, int y, int w, int h, bool filled) {
    if (filled) {
        for (int j = 0; j < h; j++)
            fb_hline(x, y + j, w);   /* draw one row of the filled rectangle */
    } else {
        fb_hline(x, y, w);           /* top edge */
        fb_hline(x, y + h - 1, w);   /* bottom edge */
        fb_vline(x, y, h);           /* left edge */
        fb_vline(x + w - 1, y, h);   /* right edge */
    }
}

/*
 * fb_circle -- Draw a circle using the Midpoint Circle Algorithm.
 *
 * Parameters:
 *   cx, cy  -- center coordinates
 *   r       -- radius in pixels
 *   filled  -- if true, fill the interior; if false, draw only the outline
 *
 * Returns: nothing
 *
 * MIDPOINT CIRCLE ALGORITHM:
 *   This is an efficient integer-only algorithm for rasterizing circles,
 *   similar in spirit to Bresenham's line algorithm.
 *
 *   The key insight is that a circle has 8-fold symmetry: if (x, y) is on
 *   the circle, then so are (-x, y), (x, -y), (-x, -y), (y, x), (-y, x),
 *   (y, -x), and (-y, -x). So we only need to compute 1/8 of the circle
 *   (the "first octant," from 12 o'clock to 1:30) and mirror it to get
 *   all 8 symmetric points. That's why there are 8 fb_set_pixel calls
 *   for the outline case.
 *
 *   Variables:
 *     x starts at 0, y starts at r (top of circle)
 *     d = "decision parameter" = 3 - 2*r (initial value)
 *
 *   The loop runs while x <= y (we're in the first octant):
 *     - Draw the 8 symmetric points (or fill horizontal spans)
 *     - If d < 0: the midpoint is inside the circle, so move only
 *       horizontally -> d += 4*x + 6
 *     - If d >= 0: the midpoint is outside, so move horizontally AND
 *       decrease y -> d += 4*(x-y) + 10, y--
 *     - x++ always (we always step horizontally)
 *
 *   For filled circles: instead of plotting 8 individual points, we draw
 *   4 horizontal lines that connect the symmetric point pairs. This fills
 *   in every pixel inside the circle.
 */
void fb_circle(int cx, int cy, int r, bool filled) {
    int x = 0, y = r, d = 3 - 2 * r;  /* start at top of circle, init decision param */
    while (x <= y) {
        if (filled) {
            /* Draw 4 horizontal spans connecting symmetric point pairs.
             * Each fb_hline draws from the left symmetric point to the right,
             * covering (2*x+1) or (2*y+1) pixels wide. */
            fb_hline(cx - x, cy + y, 2 * x + 1);  /* bottom-center span */
            fb_hline(cx - x, cy - y, 2 * x + 1);  /* top-center span */
            fb_hline(cx - y, cy + x, 2 * y + 1);  /* bottom-side span */
            fb_hline(cx - y, cy - x, 2 * y + 1);  /* top-side span */
        } else {
            /* Draw 8 symmetric outline points -- one in each octant.
             * (cx+x, cy+y) is the primary point; the other 7 are mirrors. */
            fb_set_pixel(cx + x, cy + y); fb_set_pixel(cx - x, cy + y);
            fb_set_pixel(cx + x, cy - y); fb_set_pixel(cx - x, cy - y);
            fb_set_pixel(cx + y, cy + x); fb_set_pixel(cx - y, cy + x);
            fb_set_pixel(cx + y, cy - x); fb_set_pixel(cx - y, cy - x);
        }
        /* Update the decision parameter to decide next pixel position */
        if (d < 0) { d += 4 * x + 6; }             /* stay at same y, move x right */
        else { d += 4 * (x - y) + 10; y--; }        /* move x right AND y inward */
        x++;
    }
}

/* ─── Text Rendering ─────────────────────────────────────────── */

/*
 * fb_char -- Draw a single character at position (x, y).
 *
 * Parameters:
 *   x, y  -- top-left corner of the character cell
 *   c     -- the ASCII character to draw
 *
 * Returns: nothing
 *
 * Characters outside the printable range (32-126) are silently ignored.
 *
 * The rendering loop iterates column-by-column (outer loop) then
 * row-by-row (inner loop). For each column, the byte `bits` contains
 * 8 row-pixels packed into one byte. The expression (bits & (1 << row))
 * tests whether the pixel at that row is set:
 *   (1 << row) creates a mask with a single bit at position `row`
 *   & tests if that bit is set in the glyph data
 *   If yes, draw the pixel; if no, leave it transparent (don't clear it).
 */
void fb_char(int x, int y, char c) {
    if (c < FONT_FIRST_CHAR || c > FONT_LAST_CHAR) return;  /* unprintable */
    int idx = c - FONT_FIRST_CHAR;        /* convert ASCII to font table index */
    const uint8_t *glyph = FONT_6X8[idx]; /* pointer to the 6-byte glyph data */

    for (int col = 0; col < FONT_CHAR_W; col++) {
        uint8_t bits = glyph[col];         /* all 8 row-pixels for this column */
        for (int row = 0; row < FONT_CHAR_H; row++) {
            if (bits & (1 << row)) {       /* test if row-th bit is set */
                fb_set_pixel(x + col, y + row);
            }
        }
    }
}

/*
 * fb_string -- Draw a null-terminated string at position (x, y).
 *
 * Parameters:
 *   x, y  -- top-left corner of the first character
 *   str   -- pointer to a null-terminated C string (const = read-only)
 *
 * Returns: nothing
 *
 * Advances the cursor (cx) by FONT_CHAR_W pixels after each character.
 * Handles '\n' (newline) by resetting cx to the starting x and moving
 * down by FONT_CHAR_H + 1 pixels (the +1 adds inter-line spacing).
 *
 * The while (*str) loop continues until it hits the null terminator
 * character ('\0', value 0) that marks the end of every C string.
 * In C, strings are just arrays of chars terminated by a zero byte.
 * *str dereferences the pointer to get the current character, and
 * str++ advances the pointer to the next character.
 */
void fb_string(int x, int y, const char *str) {
    int cx = x;           /* cursor x -- tracks horizontal position */
    while (*str) {         /* loop until null terminator */
        if (*str == '\n') {
            cx = x;                    /* carriage return: back to left margin */
            y += FONT_CHAR_H + 1;     /* line feed: move down one line */
        } else {
            if (cx + FONT_CHAR_W <= SCREEN_W) {  /* clip: don't draw past right edge */
                fb_char(cx, y, *str);
            }
            cx += FONT_CHAR_W;        /* advance cursor for next character */
        }
        str++;             /* move pointer to next character in the string */
    }
}

/*
 * fb_string_wrap -- Draw a string with automatic word wrapping.
 *
 * Parameters:
 *   x      -- left margin X coordinate
 *   y      -- starting Y coordinate
 *   max_w  -- maximum width in pixels before wrapping to next line
 *   str    -- the null-terminated string to draw
 *
 * Returns: nothing
 *
 * Like fb_string, but wraps to the next line when the cursor would
 * exceed (x + max_w). Also stops drawing if the text would go below
 * the bottom of the screen (y + FONT_CHAR_H > SCREEN_H).
 *
 * Note: this does character-level wrapping (mid-word), not word-level
 * wrapping. A more sophisticated version would look ahead for spaces.
 */
void fb_string_wrap(int x, int y, int max_w, const char *str) {
    int cx = x;
    while (*str) {
        /* Wrap to next line if we hit a newline OR exceed max width */
        if (*str == '\n' || (cx + FONT_CHAR_W > x + max_w)) {
            cx = x;
            y += FONT_CHAR_H + 1;
            if (*str == '\n') { str++; continue; } /* consume the newline char */
        }
        if (y + FONT_CHAR_H > SCREEN_H) break;    /* stop if below screen bottom */
        fb_char(cx, y, *str);
        cx += FONT_CHAR_W;
        str++;
    }
}

/*
 * fb_string_inv -- Draw "inverse" text: white text on a black background.
 *
 * Parameters:
 *   x, y  -- top-left corner
 *   str   -- the null-terminated string to draw
 *
 * Returns: nothing
 *
 * This creates a "selected" or "highlighted" look by:
 *   1. Drawing a filled black rectangle behind the text (+2px padding)
 *   2. Then CLEARING pixels where the glyph bits are set
 *
 * The result is white letters on a black background -- the inverse of
 * normal rendering. fb_clr_pixel is used instead of fb_set_pixel because
 * we need to "punch holes" in the filled rectangle to reveal the white
 * background color of the display.
 */
void fb_string_inv(int x, int y, const char *str) {
    /* Draw background rect then white-on-black text */
    int len = strlen(str);  /* strlen counts characters (not including '\0') */
    fb_rect(x, y, len * FONT_CHAR_W + 2, FONT_CHAR_H + 2, true); /* black bg */

    int cx = x + 1;  /* +1 pixel offset for padding inside the rectangle */
    while (*str) {
        if (*str >= FONT_FIRST_CHAR && *str <= FONT_LAST_CHAR) {
            int idx = *str - FONT_FIRST_CHAR;
            const uint8_t *glyph = FONT_6X8[idx];
            for (int col = 0; col < FONT_CHAR_W; col++) {
                uint8_t bits = glyph[col];
                for (int row = 0; row < FONT_CHAR_H; row++) {
                    if (bits & (1 << row)) {
                        /* CLEAR pixel = white dot on the black background */
                        fb_clr_pixel(cx + col, y + 1 + row);
                    }
                }
            }
        }
        cx += FONT_CHAR_W;
        str++;
    }
}

/* ─── High-Level Renderers ───────────────────────────────────── */

/*
 * Screen layout constants (in pixels from top):
 *   HEADER_Y (0)    -- header starts at the very top
 *   HEADER_H (14)   -- header is 14 pixels tall (time, emotion, stat icons)
 *   PET_Y (14)      -- pet area starts right below the header
 *   PET_H (80)      -- pet area is 80 pixels tall (octopus lives here)
 *   DIALOG_Y (94)   -- dialogue box starts below the pet area
 *   DIALOG_H (28)   -- dialogue box is 28 pixels tall
 *
 * Total: 14 + 80 + 28 = 122 = SCREEN_H
 */
#define HEADER_Y       0
#define HEADER_H       14
#define PET_Y          14
#define PET_H          80
#define DIALOG_Y       94
#define DIALOG_H       28

/*
 * render_header -- Draw the status bar at the top of the pet screen.
 *
 * Parameters:
 *   game  -- pointer to the game state (const = read-only)
 *
 * Returns: nothing
 *
 * Draws (left to right):
 *   - Current time in 12-hour format (e.g., "2:30 PM")
 *   - Current emotion name (e.g., "Happy", "Tired")
 *   - 5 tiny stat-bar icons showing hunger/happiness/energy/hygiene/health
 *   - A separator line across the bottom of the header
 *
 * The stat icons are small 10x10 outlined boxes with a proportional
 * fill level. When a stat drops below 20, the icon is fully filled
 * (inverted) to signal "critical."
 */
void render_header(const game_t *game) {
    /* Time string: format as 12-hour clock */
    char time_str[16];
    int h = game->time.hour % 12;   /* convert 24h to 12h (13->1, 0->12) */
    if (h == 0) h = 12;             /* midnight/noon: 0 becomes 12 */
    snprintf(time_str, sizeof(time_str), "%d:%02d %s",
             h, game->time.minute, game->time.hour < 12 ? "AM" : "PM");
    fb_string(2, 2, time_str);

    /* Emotion name on the right side of the header */
    fb_string(70, 2, emotion_name(game->emotion.current));

    /* Stat icons: 5 small boxes with proportional fill.
     * These provide an at-a-glance view of the pet's vital stats. */
    const int icon_x_start = SCREEN_W - 62;  /* position from right edge */
    const int icon_w = 10;                     /* each icon is 10x10 pixels */
    const int icon_gap = 12;                   /* 12px center-to-center spacing */

    /* Pack the 5 stat values into an array so we can loop over them.
     * The `const` keyword means we won't modify these values.
     * int16_t is a signed 16-bit integer (-32768 to +32767). */
    const primary_stats_t *s = &game->stats.primary;
    const int16_t vals[] = { s->hunger, s->happiness, s->energy, s->hygiene, s->health };
    for (int i = 0; i < 5; i++) {
        int ix = icon_x_start + i * icon_gap;  /* x position of this icon */
        int iy = 2;                              /* y position (near top) */

        /* Outline: unfilled rectangle */
        fb_rect(ix, iy, icon_w, icon_w, false);

        /* Fill proportional to value (0-100 maps to 0 to icon_w-2 pixels).
         * The -2 accounts for the 1-pixel border on each side.
         * Integer division truncates: 50 * 8 / 100 = 400 / 100 = 4 pixels. */
        int fill = (vals[i] * (icon_w - 2)) / 100;
        if (fill > 0) {
            /* Fill from bottom up: draw horizontal lines starting from
             * the bottom of the icon interior, working upward. */
            for (int f = 0; f < fill; f++) {
                fb_hline(ix + 1, iy + icon_w - 2 - f, icon_w - 2);
            }
        }

        /* Critical: invert the entire icon (fill it solid) when stat < 20.
         * This makes critically low stats visually alarming. */
        if (vals[i] < 20) {
            fb_rect(ix, iy, icon_w, icon_w, true);
        }
    }

    /* Separator line across the full width, at the bottom of the header */
    fb_hline(0, HEADER_H - 1, SCREEN_W);
}

/*
 * render_stat_bar -- Draw a labeled stat bar with numeric value.
 *
 * Parameters:
 *   x, y   -- top-left corner
 *   label  -- 3-character label (e.g., "HUN", "HAP")
 *   value  -- stat value 0-100
 *
 * Returns: nothing
 *
 * Draws: [label] [========--] [value]
 * The bar is 100 pixels wide, so 1 pixel = 1% -- easy mental mapping.
 */
void render_stat_bar(int x, int y, const char *label, int16_t value) {
    fb_string(x, y, label);         /* draw the 3-letter label */
    int bar_x = x + 24;             /* bar starts 24px right of the label */
    int bar_w = 100;                 /* 100px wide = 1px per percent */
    fb_rect(bar_x, y, bar_w, 10, false);  /* draw the empty bar outline */

    /* Fill the bar proportionally. The -2 accounts for the 1px border
     * on each side of the outline. */
    int fill_w = (value * (bar_w - 2)) / 100;
    if (fill_w > 0) {
        fb_rect(bar_x + 1, y + 1, fill_w, 8, true);  /* filled portion */
    }

    /* Numeric value to the right of the bar */
    char val_str[8];
    snprintf(val_str, sizeof(val_str), "%d", value);
    fb_string(bar_x + bar_w + 4, y, val_str);
}

/*
 * render_dialogue_box -- Draw a dialogue/speech bubble at the bottom of the screen.
 *
 * Parameters:
 *   text  -- the dialogue text to display (null-terminated string)
 *
 * Returns: nothing
 *
 * Draws a horizontal line separator and then the text with word-wrapping.
 * The dialogue area occupies the bottom 28 pixels of the screen.
 */
void render_dialogue_box(const char *text) {
    if (!text || !text[0]) return;  /* do nothing if text is NULL or empty */

    /* Clear dialogue area */
    /* (framebuffer already cleared, just draw the box) */
    fb_hline(0, DIALOG_Y, SCREEN_W);             /* separator line */
    fb_string_wrap(4, DIALOG_Y + 3, SCREEN_W - 8, text);  /* wrapped text */
}

/* ─── Octopus Renderer ───────────────────────────────────────── */
/*
 * THE OCTOPUS:
 *   The Dilder pet is an octopus. It's drawn procedurally (calculated in
 *   code) rather than from a sprite/bitmap. This approach uses less memory
 *   and allows dynamic changes based on emotion.
 *
 *   The octopus is composed of three parts, each drawn by a separate function:
 *     1. BODY   -- draw_octopus_body(): a double circle for the head + 6 wavy
 *                  tentacles using sine waves
 *     2. EYES   -- draw_eyes(): different eye styles for each emotion
 *     3. MOUTH  -- draw_mouth(): different mouth shapes for each emotion
 *
 *   By swapping just the eyes and mouth, the same body can express many
 *   different emotions without needing separate sprite sheets for each one.
 *   This is a form of "procedural animation" -- generating visuals from
 *   math rather than pre-drawn images.
 *
 *   The cx, cy parameters are the CENTER of the octopus head. All body
 *   parts are positioned relative to this center point, so moving the
 *   octopus only requires changing one coordinate pair.
 */

/*
 * draw_octopus_body -- Draw the octopus head and tentacles.
 *
 * Parameters:
 *   cx, cy  -- center coordinates of the head
 *
 * Returns: nothing
 *
 * The head is drawn as two concentric circles (radius 18 and 17) to
 * create a thicker outline. The tentacles are 6 wavy lines drawn using
 * sine functions. Each tentacle starts at a slightly different angle
 * and wiggles based on a sine wave offset.
 *
 * sinf() returns a float between -1.0 and 1.0. Multiplying by 3 gives
 * a 3-pixel wave amplitude. The `seg * 0.8f + angle` creates a wave
 * that varies along the tentacle length AND differs per tentacle.
 *
 * The (int) casts convert float results to integer pixel coordinates.
 * C truncates toward zero: (int)2.9 = 2, (int)-1.3 = -1.
 */
static void draw_octopus_body(int cx, int cy) {
    /* Head: large ellipse (two concentric circles for a thicker outline) */
    fb_circle(cx, cy, 18, false);
    fb_circle(cx, cy, 17, false);

    /* Tentacles: 6 wavy lines extending downward from the head.
     * Each tentacle has a slightly different starting angle for variety. */
    for (int t = 0; t < 6; t++) {
        float angle = -0.8f + t * 0.32f;  /* spread tentacles across ~1.6 radians */
        int tx = cx + (int)(sinf(angle) * 16);  /* horizontal offset from center */
        int ty = cy + 16;                         /* start just below the head */

        /* Draw 12 segments per tentacle, each 2 pixels apart vertically.
         * The sinf() creates a wave pattern; each tentacle wiggles differently
         * because `angle` differs per tentacle. */
        for (int seg = 0; seg < 12; seg++) {
            int sx = tx + (int)(sinf(seg * 0.8f + angle) * 3);  /* wave offset */
            int sy = ty + seg * 2;                                /* step down */
            fb_set_pixel(sx, sy);       /* draw a 2-pixel-wide tentacle segment */
            fb_set_pixel(sx + 1, sy);
        }
    }
}

/*
 * draw_eyes -- Draw emotion-specific eyes on the octopus.
 *
 * Parameters:
 *   cx, cy   -- center of the octopus head
 *   emotion  -- the current emotion, determines eye style
 *
 * Returns: nothing
 *
 * Eye positions:
 *   lx, rx = left/right eye X centers (7 pixels left/right of head center)
 *   ey     = eye Y position (4 pixels above head center)
 *
 * Each emotion case draws a unique eye style. Some examples:
 *   - NORMAL: simple circles with dot pupils
 *   - ANGRY: circles + angled "furrowed brow" lines above
 *   - TIRED: horizontal lines (half-closed/squinting)
 *   - EXCITED: bigger circles with sparkle dots
 *   - CHAOTIC: "X" shaped eyes (drawn with two crossed lines)
 *   - UNHINGED: asymmetric eyes (one big, one small)
 *
 * The switch statement handles each emotion as a separate case. The
 * `break` after each case prevents "fall-through" to the next case,
 * which is a C gotcha -- without break, execution continues into the
 * next case block.
 */
static void draw_eyes(int cx, int cy, emotion_id_t emotion) {
    int lx = cx - 7, rx = cx + 7;  /* left and right eye X positions */
    int ey = cy - 4;                /* eye Y position (above center) */

    switch (emotion) {
    case EMOTION_NORMAL:
    case EMOTION_CHILL:
        /* Normal round eyes with small dot pupils.
         * Two cases share the same code by omitting `break` between them. */
        fb_circle(lx, ey, 3, false);   /* left eye outline */
        fb_circle(rx, ey, 3, false);   /* right eye outline */
        fb_set_pixel(lx, ey); fb_set_pixel(rx, ey);      /* pupils (center dots) */
        fb_set_pixel(lx+1, ey); fb_set_pixel(rx+1, ey);  /* 2px-wide pupils */
        break;

    case EMOTION_ANGRY:
        /* Angry: normal eyes + angled eyebrow lines slanting inward.
         * The brows slope down toward the center, creating a "furrowed" look. */
        fb_circle(lx, ey, 3, false); fb_circle(rx, ey, 3, false);
        fb_set_pixel(lx, ey); fb_set_pixel(rx, ey);
        fb_line(lx - 4, ey - 5, lx + 2, ey - 3);  /* left brow: outer-high to inner-low */
        fb_line(rx - 2, ey - 3, rx + 4, ey - 5);  /* right brow: inner-low to outer-high */
        break;

    case EMOTION_SAD:
        /* Sad: eyes with pupils shifted down + upward-slanting brows.
         * The brows slope UP toward the center (opposite of angry). */
        fb_circle(lx, ey, 3, false); fb_circle(rx, ey, 3, false);
        fb_set_pixel(lx, ey + 1); fb_set_pixel(rx, ey + 1);  /* pupils shifted down */
        fb_line(lx - 4, ey - 3, lx + 2, ey - 5);  /* sad brows (opposite slope from angry) */
        fb_line(rx - 2, ey - 5, rx + 4, ey - 3);
        break;

    case EMOTION_TIRED:
        /* Half-closed eyes: just horizontal lines (no circles).
         * Two lines per eye create a "squinting" or "drooping" look. */
        fb_hline(lx - 3, ey, 6);      /* left eye top lid */
        fb_hline(rx - 3, ey, 6);      /* right eye top lid */
        fb_hline(lx - 2, ey + 1, 4);  /* left eye bottom lid (slightly narrower) */
        fb_hline(rx - 2, ey + 1, 4);  /* right eye bottom lid */
        break;

    case EMOTION_EXCITED:
    case EMOTION_SLAP_HAPPY:
        /* Big sparkly eyes: larger circles with filled inner circles
         * and a sparkle dot in the upper-right of each eye. */
        fb_circle(lx, ey, 4, false); fb_circle(rx, ey, 4, false);      /* big outlines */
        fb_circle(lx, ey - 1, 1, true); fb_circle(rx, ey - 1, 1, true); /* highlight dots */
        fb_set_pixel(lx + 2, ey - 2); fb_set_pixel(rx + 2, ey - 2);    /* sparkle pixels */
        break;

    case EMOTION_HUNGRY:
        /* Pleading eyes: big outlined circles with filled inner circles.
         * The double-circle creates a "puppy dog eyes" look. */
        fb_circle(lx, ey, 4, false); fb_circle(rx, ey, 4, false);  /* outer ring */
        fb_circle(lx, ey, 2, true); fb_circle(rx, ey, 2, true);    /* big filled pupils */
        break;

    case EMOTION_UNHINGED:
        /* Different sized eyes: one big (radius 5), one small (radius 2).
         * Asymmetry = unsettling / unhinged look. */
        fb_circle(lx, ey, 5, false);   /* left eye: big */
        fb_circle(rx, ey, 2, false);   /* right eye: small */
        fb_set_pixel(lx, ey); fb_set_pixel(rx, ey);  /* tiny dot pupils */
        break;

    case EMOTION_WEIRD:
        /* Spiral eyes: concentric circles in each eye (radius 3 + radius 1).
         * Looks like the classic "hypnotized" cartoon eyes. */
        fb_circle(lx, ey, 3, false);
        fb_circle(rx, ey, 3, false);
        fb_circle(lx, ey, 1, false);  /* inner ring */
        fb_circle(rx, ey, 1, false);
        break;

    case EMOTION_CHAOTIC:
        /* X-shaped eyes: two crossed diagonal lines per eye.
         * The universal "knocked out" or "dead" cartoon eye symbol. */
        fb_line(lx - 3, ey - 3, lx + 3, ey + 3);  /* left eye:  \ diagonal */
        fb_line(lx - 3, ey + 3, lx + 3, ey - 3);  /* left eye:  / diagonal */
        fb_line(rx - 3, ey - 3, rx + 3, ey + 3);  /* right eye: \ diagonal */
        fb_line(rx - 3, ey + 3, rx + 3, ey - 3);  /* right eye: / diagonal */
        break;

    case EMOTION_CREEPY:
        /* Heart-shaped eyes: two overlapping filled circles per eye,
         * positioned side by side and slightly above center.
         * The overlap creates a rough heart shape. */
        fb_circle(lx - 1, ey - 1, 2, true);   /* left eye: left lobe */
        fb_circle(lx + 1, ey - 1, 2, true);   /* left eye: right lobe */
        fb_circle(rx - 1, ey - 1, 2, true);   /* right eye: left lobe */
        fb_circle(rx + 1, ey - 1, 2, true);   /* right eye: right lobe */
        break;

    default:
        /* Fallback: same as NORMAL eyes */
        fb_circle(lx, ey, 3, false); fb_circle(rx, ey, 3, false);
        fb_set_pixel(lx, ey); fb_set_pixel(rx, ey);
        break;
    }
}

/*
 * draw_mouth -- Draw an emotion-specific mouth on the octopus.
 *
 * Parameters:
 *   cx, cy   -- center of the octopus head
 *   emotion  -- the current emotion, determines mouth shape
 *
 * Returns: nothing
 *
 * The mouth is positioned at my = cy + 6 (6 pixels below head center).
 * Each emotion draws a different shape:
 *   - NORMAL: gentle upward curve (3-segment polyline smile)
 *   - ANGRY/SAD: downward curves (frowns) of varying depth
 *   - EXCITED: wide open smile (polyline + horizontal line)
 *   - HUNGRY: circular open mouth ("O" shape)
 *   - TIRED: small circle (yawn)
 *   - UNHINGED: jagged zigzag smile
 *   - WEIRD: sine-wave squiggly line
 *   - CHAOTIC: double-circle scream
 */
static void draw_mouth(int cx, int cy, emotion_id_t emotion) {
    int my = cy + 6;  /* mouth Y position: 6px below head center */

    switch (emotion) {
    case EMOTION_NORMAL:
    case EMOTION_CHILL:
        /* Small smile: 3-segment polyline curving upward at the corners.
         * Left corner -> bottom-left -> bottom-right -> right corner. */
        fb_line(cx - 4, my, cx - 2, my + 2);      /* left corner down */
        fb_line(cx - 2, my + 2, cx + 2, my + 2);  /* flat bottom */
        fb_line(cx + 2, my + 2, cx + 4, my);      /* right corner up */
        break;

    case EMOTION_ANGRY:
        /* Frown: V-shape pointing down (inverted smile).
         * The corners are higher (my+2) and the center is lower (my). */
        fb_line(cx - 5, my + 2, cx, my);     /* left side slopes down */
        fb_line(cx, my, cx + 5, my + 2);     /* right side slopes up */
        break;

    case EMOTION_SAD:
        /* Deep frown: wider and more pronounced than angry frown.
         * Corners are 3px below, center is at my. */
        fb_line(cx - 5, my + 3, cx - 2, my);      /* left side slopes up */
        fb_line(cx - 2, my, cx + 2, my);            /* flat top center */
        fb_line(cx + 2, my, cx + 5, my + 3);        /* right side slopes down */
        break;

    case EMOTION_EXCITED:
    case EMOTION_SLAP_HAPPY:
        /* Big open smile: wide mouth with a flat top line.
         * The bottom curve is 4px below the top, creating an open grin. */
        fb_line(cx - 6, my, cx - 3, my + 4);      /* left side of smile */
        fb_line(cx - 3, my + 4, cx + 3, my + 4);  /* flat bottom */
        fb_line(cx + 3, my + 4, cx + 6, my);      /* right side of smile */
        fb_hline(cx - 5, my, 10);                  /* flat top (teeth line) */
        break;

    case EMOTION_HUNGRY:
        /* Open mouth: circle centered 2px below mouth position.
         * The "O" shape looks like a begging/hungry expression. */
        fb_circle(cx, my + 2, 4, false);
        break;

    case EMOTION_TIRED:
        /* Small O (yawn): smaller circle than hungry mouth. */
        fb_circle(cx, my + 1, 2, false);
        break;

    case EMOTION_UNHINGED:
        /* Jagged smile: zigzag line making a creepy/unhinged grin.
         * 4 segments creating a W-shape rotated to be a toothy smile. */
        fb_line(cx - 6, my, cx - 3, my + 3);      /* down */
        fb_line(cx - 3, my + 3, cx, my);            /* up */
        fb_line(cx, my, cx + 3, my + 3);            /* down */
        fb_line(cx + 3, my + 3, cx + 6, my);        /* up */
        break;

    case EMOTION_WEIRD:
        /* Squiggly line: pixels placed along a sine wave.
         * sinf(i * 0.8f) creates a wave, * 2 sets the amplitude.
         * (int) truncates the float to an integer pixel position. */
        for (int i = -5; i <= 5; i++) {
            fb_set_pixel(cx + i, my + (int)(sinf(i * 0.8f) * 2));
        }
        break;

    case EMOTION_CHAOTIC:
        /* Open scream: two concentric circles for a thick "O" shape.
         * Bigger than the hungry mouth -- this is a full scream. */
        fb_circle(cx, my + 2, 5, false);   /* outer ring */
        fb_circle(cx, my + 2, 4, false);   /* inner ring (thickens the outline) */
        break;

    default:
        /* Neutral: simple horizontal line (no curve, no expression) */
        fb_line(cx - 4, my, cx + 4, my);
        break;
    }
}

/*
 * render_octopus -- Draw the complete octopus pet at the correct position.
 *
 * Parameters:
 *   emotion  -- current emotion (affects eyes and mouth)
 *   stage    -- life stage (egg gets special rendering)
 *
 * Returns: nothing
 *
 * The octopus is centered at x = SCREEN_W / 3 (the left third of the
 * screen), leaving the right side free for the menu overlay.
 *
 * Special case: LIFE_STAGE_EGG renders an oval with crack lines instead
 * of the full octopus, since the pet hasn't hatched yet.
 */
void render_octopus(emotion_id_t emotion, life_stage_t stage) {
    int cx = SCREEN_W / 3;  /* left third for octopus */
    int cy = PET_Y + PET_H / 2 - 4;  /* vertically centered in pet area, nudged up 4px */

    if (stage == LIFE_STAGE_EGG) {
        /* Egg: simple oval with crack lines instead of a full octopus.
         * Two concentric circles create a thicker egg outline. */
        fb_circle(cx, cy, 16, false);
        fb_circle(cx, cy, 15, false);
        /* Crack lines: a zigzag pattern near the top of the egg */
        fb_line(cx - 5, cy - 8, cx - 2, cy - 3);
        fb_line(cx - 2, cy - 3, cx + 1, cy - 6);
        fb_string(cx - 9, cy + 20, "* egg *");  /* label below the egg */
        return;  /* early return: don't draw body/eyes/mouth for an egg */
    }

    /* For all post-egg stages, draw the three components.
     * The emotion parameter only affects eyes and mouth -- the body
     * always looks the same regardless of emotion. */
    draw_octopus_body(cx, cy);
    draw_eyes(cx, cy, emotion);
    draw_mouth(cx, cy, emotion);
}

/* ─── Menu Overlay ───────────────────────────────────────────── */

/*
 * Menu label arrays: these static const arrays hold the display text
 * for each menu's items. They're stored in the read-only data segment
 * since they never change at runtime.
 *
 * The `const char *` type means "pointer to a character that won't be
 * modified." The arrays themselves are `static`, so they're private to
 * this file.
 */
static const char *MAIN_MENU_LABELS[] = { "Feed", "Play", "Care", "Stats", "Settings" };
static const int MAIN_MENU_COUNT = 5;
static const char *FEED_MENU_LABELS[] = { "Meal", "Snack", "Treat" };
static const int FEED_MENU_COUNT = 3;
static const char *PLAY_MENU_LABELS[] = { "Mini-game", "Tickle" };
static const int PLAY_MENU_COUNT = 2;
static const char *CARE_MENU_LABELS[] = { "Clean", "Medicine", "Light" };
static const int CARE_MENU_COUNT = 3;

/*
 * get_menu_items -- Look up the label array and item count for a menu.
 *
 * Parameters:
 *   menu    -- which menu to look up
 *   labels  -- OUTPUT: pointer to a pointer-to-pointer that will receive
 *              the label array address. This is a triple pointer (const char ***):
 *                - labels is a pointer to a variable
 *                - that variable is a `const char **` (pointer to an array of strings)
 *                - we write to *labels to set the caller's pointer
 *              This "output parameter" pattern is common in C because functions
 *              can only return one value. When you need to return multiple values,
 *              you pass pointers to variables that the function fills in.
 *   count   -- OUTPUT: pointer to an int that receives the item count
 *
 * Returns: nothing (results via output parameters)
 */
static void get_menu_items(menu_id_t menu, const char ***labels, int *count) {
    switch (menu) {
    case MENU_FEED: *labels = FEED_MENU_LABELS; *count = FEED_MENU_COUNT; break;
    case MENU_PLAY: *labels = PLAY_MENU_LABELS; *count = PLAY_MENU_COUNT; break;
    case MENU_CARE: *labels = CARE_MENU_LABELS; *count = CARE_MENU_COUNT; break;
    case MENU_MAIN:
    default:
        *labels = MAIN_MENU_LABELS; *count = MAIN_MENU_COUNT; break;
    }
}

/*
 * render_menu_overlay -- Draw the menu panel over the right half of the screen.
 *
 * Parameters:
 *   menu  -- pointer to the current menu state (cursor position, which menu, etc.)
 *   game  -- pointer to the game state (unused here but available for future use)
 *
 * Returns: nothing
 *
 * The menu is drawn as an overlay on the RIGHT HALF of the screen:
 *   1. Clear the right half to white (by clearing individual pixels)
 *   2. Draw a vertical border line on the left edge of the menu
 *   3. Draw each menu item as text, highlighting the cursor position
 *      with inverse text (white on black)
 *
 * The highlighted item uses fb_rect (filled) + fb_string_inv to create
 * a selection bar effect.
 */
void render_menu_overlay(const menu_state_t *menu, const game_t *game) {
    int mx = SCREEN_W / 2;  /* menu starts at screen midpoint */
    int mw = SCREEN_W / 2;  /* menu width = half the screen */

    /* White background: clear all pixels in the menu area.
     * This erases whatever was drawn behind the menu (the pet, etc.)
     * so the menu text is readable. */
    for (int y = HEADER_H; y < SCREEN_H; y++) {
        for (int x = mx; x < SCREEN_W; x++) {
            fb_clr_pixel(x, y);
        }
    }

    /* Border: vertical line at the left edge of the menu panel */
    fb_vline(mx, HEADER_H, SCREEN_H - HEADER_H);

    /* Get the labels and count for the current menu */
    const char **labels;
    int count;
    get_menu_items(menu->current_menu, &labels, &count);

    /* Draw each menu item. Items are spaced 14px apart vertically. */
    for (int i = 0; i < count; i++) {
        int y = HEADER_H + 4 + i * 14;  /* 4px top padding + 14px per item */
        if (i == menu->cursor) {
            /* Highlighted item: filled rectangle + inverse text.
             * The rect is 2px narrower than the menu width to leave border room. */
            fb_rect(mx + 1, y - 1, mw - 2, 12, true);    /* black highlight bar */
            fb_string_inv(mx + 14, y, labels[i]);          /* white text on black */
        } else {
            /* Normal item: just draw the text */
            fb_string(mx + 14, y, labels[i]);              /* black text on white */
        }
    }
}

/* ─── Stats Screen ───────────────────────────────────────────── */

/*
 * render_stats_screen -- Draw the full-screen statistics view.
 *
 * Parameters:
 *   game  -- pointer to the game state (const = read-only)
 *
 * Returns: nothing
 *
 * Shows all 5 primary stats as horizontal bars, plus secondary info
 * (bond level, age, weight, life stage) as text below.
 *
 * The `y += 14` pattern advances the cursor down the screen after each
 * line, creating a vertical list layout. This is a common alternative to
 * maintaining a layout engine -- just track y manually.
 *
 * snprintf is "safe printf to buffer": it writes formatted text into
 * buf[] but will never write more than sizeof(buf) bytes, preventing
 * buffer overflow. The %d format prints an integer, %lu prints an
 * unsigned long, and %s prints a string.
 */
void render_stats_screen(const game_t *game) {
    fb_clear();                          /* clear entire screen for stats view */
    fb_string_inv(2, 2, " STATS ");     /* title with inverse highlight */
    fb_hline(0, 12, SCREEN_W);          /* separator under title */

    int y = 16;  /* starting Y for the stat bars */
    render_stat_bar(4, y, "HUN", game->stats.primary.hunger);    y += 14;
    render_stat_bar(4, y, "HAP", game->stats.primary.happiness); y += 14;
    render_stat_bar(4, y, "ENE", game->stats.primary.energy);    y += 14;
    render_stat_bar(4, y, "HYG", game->stats.primary.hygiene);   y += 14;
    render_stat_bar(4, y, "HEA", game->stats.primary.health);    y += 18; /* extra gap before text */

    /* Bond info: level and XP.
     * (unsigned long) cast is needed because %lu expects an unsigned long,
     * but bond_xp is uint32_t. On most platforms they're the same size,
     * but the cast makes the code portable and silences compiler warnings. */
    char buf[48];
    snprintf(buf, sizeof(buf), "Bond: Lv%d  XP:%lu",
             game->progression.bond_level, (unsigned long)game->progression.bond_xp);
    fb_string(4, y, buf); y += 10;

    /* Age and weight.
     * age_seconds / 86400 converts seconds to days (86400 = 60*60*24). */
    snprintf(buf, sizeof(buf), "Age: %lud  Weight:%d",
             (unsigned long)(game->life.age_seconds / 86400), game->stats.secondary.weight);
    fb_string(4, y, buf); y += 10;

    /* Life stage name (Egg, Hatchling, Juvenile, etc.) */
    snprintf(buf, sizeof(buf), "Stage: %s", life_stage_name(game->life.stage));
    fb_string(4, y, buf);
}

/* ─── Pet Screen (main view) ─────────────────────────────────── */

/*
 * render_pet_screen -- Draw the main pet view (header + octopus + dialogue).
 *
 * Parameters:
 *   game  -- pointer to the game state (const = read-only)
 *
 * Returns: nothing
 *
 * This composes three layers:
 *   1. The status header (time, emotion, stat icons) at the top
 *   2. The octopus pet (body + eyes + mouth) in the middle
 *   3. The dialogue box at the bottom (only if there's text to show)
 *
 * The dialogue check (game->dialogue.showing) prevents drawing an empty
 * box when the pet has nothing to say.
 */
void render_pet_screen(const game_t *game) {
    render_header(game);
    render_octopus(game->emotion.current, game->life.stage);

    if (game->dialogue.showing) {
        render_dialogue_box(game->dialogue.current_text);
    }
}
