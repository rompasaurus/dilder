/**
 * Sassy Octopus — Runtime-rendered e-ink animation
 *
 * Instead of pre-baking every frame, this firmware renders each frame
 * on the fly: composites the octopus body, eyes, mouth expression,
 * chat bubble, and text at display time.  This means ALL quotes fit
 * in flash (~10KB of strings vs ~4MB of bitmaps).
 *
 * Wiring (same as all Dilder firmware):
 *   VCC  -> 3V3(OUT) pin 36    GND  -> GND      pin 38
 *   DIN  -> GP11     pin 15    CLK  -> GP10     pin 14
 *   CS   -> GP9      pin 12    DC   -> GP8      pin 11
 *   RST  -> GP12     pin 16    BUSY -> GP13     pin 17
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "pico/stdlib.h"
#include "hardware/adc.h"
#include "hardware/rtc.h"
#include "pico/util/datetime.h"
#include "DEV_Config.h"

/* Display variant selection */
#if defined(DISPLAY_V2)
  #include "EPD_2in13_V2.h"
  #define DISP_W EPD_2in13_V2_WIDTH
  #define DISP_H EPD_2in13_V2_HEIGHT
  #define EPD_Init()     EPD_2in13_V2_Init()
  #define EPD_Clear()    EPD_2in13_V2_Clear()
  #define EPD_Display(b) EPD_2in13_V2_Display(b)
  #define EPD_Partial(b) EPD_2in13_V2_Display_Partial(b)
  #define EPD_Sleep()    EPD_2in13_V2_Sleep()
  #define DISPLAY_NAME   "V2"
#elif defined(DISPLAY_V3A)
  #include "EPD_2in13_V3a.h"
  #define DISP_W EPD_2in13_V3a_WIDTH
  #define DISP_H EPD_2in13_V3a_HEIGHT
  #define EPD_Init()     EPD_2in13_V3a_Init()
  #define EPD_Clear()    EPD_2in13_V3a_Clear()
  #define EPD_Display(b) EPD_2in13_V3a_Display(b)
  #define EPD_Partial(b) EPD_2in13_V3a_Display_Partial(b)
  #define EPD_Sleep()    EPD_2in13_V3a_Sleep()
  #define DISPLAY_NAME   "V3a"
#elif defined(DISPLAY_V4)
  #include "EPD_2in13_V4.h"
  #define DISP_W EPD_2in13_V4_WIDTH
  #define DISP_H EPD_2in13_V4_HEIGHT
  #define EPD_Init()     EPD_2in13_V4_Init()
  #define EPD_Clear()    EPD_2in13_V4_Clear()
  #define EPD_Display(b) EPD_2in13_V4_Display(b)
  #define EPD_Partial(b) EPD_2in13_V4_Display_Partial(b)
  #define EPD_Sleep()    EPD_2in13_V4_Sleep()
  #define DISPLAY_NAME   "V4"
#else
  #include "EPD_2in13_V3.h"
  #define DISP_W EPD_2in13_V3_WIDTH
  #define DISP_H EPD_2in13_V3_HEIGHT
  #define EPD_Init()     EPD_2in13_V3_Init()
  #define EPD_Clear()    EPD_2in13_V3_Clear()
  #define EPD_Display(b) EPD_2in13_V3_Display(b)
  #define EPD_Partial(b) EPD_2in13_V3_Display_Partial(b)
  #define EPD_Sleep()    EPD_2in13_V3_Sleep()
  #define DISPLAY_NAME   "V3"
#endif

/* Auto-generated quotes + tagline */
#include "quotes.h"

/* ─── Canvas constants ─── */
#define IMG_W         250
#define IMG_H         122
#define IMG_ROW_BYTES ((IMG_W + 7) / 8)  /* 32 */

/* Mood values (match quotes.h) */
#define MOOD_NORMAL   0
#define MOOD_WEIRD    1
#define MOOD_UNHINGED 2

/* Mouth expressions */
#define EXPR_SMIRK    0
#define EXPR_OPEN     1
#define EXPR_SMILE    2
#define EXPR_WEIRD    3
#define EXPR_UNHINGED 4

/* Landscape frame buffer (1 = black pixel, packed MSB-first) */
static uint8_t frame[IMG_ROW_BYTES * IMG_H];

/* Display buffer (portrait orientation for e-ink driver) */
static uint8_t display_buf[((DISP_W + 7) / 8) * DISP_H];

/* Vertical offset — pushes octopus + bubble down to make room for clock */
#define Y_OFF 12

/* ─── Pixel helpers ─── */
static inline void px_set(int x, int y) {
    if (x >= 0 && x < IMG_W && y >= 0 && y < IMG_H)
        frame[y * IMG_ROW_BYTES + x / 8] |= (0x80 >> (x & 7));
}
static inline void px_clr(int x, int y) {
    if (x >= 0 && x < IMG_W && y >= 0 && y < IMG_H)
        frame[y * IMG_ROW_BYTES + x / 8] &= ~(0x80 >> (x & 7));
}
/* Offset versions — add Y_OFF to y before drawing */
static inline void px_set_off(int x, int y) { px_set(x, y + Y_OFF); }
static inline void px_clr_off(int x, int y) { px_clr(x, y + Y_OFF); }

/* ─── Octopus body (RLE: y, num_spans, x0, x1, ...) terminated by 0xFF ─── */
static const uint8_t body_rle[] = {
    10,1, 22,48,  11,1, 18,52,  12,1, 16,54,  13,1, 14,56,
    14,1, 13,57,  15,1, 12,58,  16,1, 11,59,  17,1, 10,60,
    18,1, 10,60,  19,1,  9,61,  20,1,  9,61,  21,1,  9,61,
    22,1,  9,61,  23,1,  9,61,  24,1,  9,61,  25,1,  9,61,
    26,1,  9,61,  27,1,  9,61,  28,1, 10,60,  29,1, 10,60,
    30,1, 10,60,  31,1, 10,60,  32,1, 10,60,  33,1, 10,60,
    34,1, 10,60,  35,1, 10,60,  36,1, 10,60,  37,1, 10,60,
    38,1, 10,60,  39,1, 10,60,  40,1, 10,60,  41,1, 11,59,
    42,1, 11,59,  43,1, 12,58,  44,1, 13,57,  45,1, 14,56,
    46,1, 12,58,  47,1, 11,59,  48,1, 10,60,  49,1, 10,60,
    50,1, 11,59,  51,1, 12,58,  52,1, 13,57,  53,1, 14,56,
    54,1, 15,55,
    /* Tentacles */
    55,5, 10,17, 21,28, 32,39, 43,50, 54,61,
    56,5,  8,15, 19,26, 30,37, 45,52, 56,63,
    57,5,  7,14, 18,24, 29,35, 47,53, 58,64,
    58,5,  6,12, 19,25, 31,37, 46,52, 57,63,
    59,5,  7,13, 21,27, 33,39, 44,50, 55,61,
    60,5,  8,14, 20,26, 31,37, 43,49, 54,60,
    61,5,  9,14, 18,24, 30,36, 44,50, 56,62,
    62,5,  8,13, 17,22, 31,37, 46,52, 57,63,
    63,5,  7,12, 18,23, 33,38, 45,51, 55,61,
    64,5,  8,13, 20,25, 32,37, 43,48, 54,59,
    65,5,  9,14, 19,24, 30,35, 44,49, 55,60,
    66,5, 10,14, 17,22, 31,36, 46,51, 57,62,
    67,5,  9,13, 18,22, 33,37, 45,50, 56,61,
    68,5,  8,12, 19,23, 32,36, 43,48, 54,59,
    69,5,  9,13, 21,25, 30,34, 44,48, 55,59,
    70,5, 10,14, 20,24, 31,35, 46,50, 57,61,
    71,5, 11,14, 18,22, 33,37, 45,49, 56,60,
    72,5, 10,13, 19,22, 32,35, 43,47, 54,58,
    73,5,  9,12, 20,23, 30,33, 44,47, 55,58,
    74,5, 10,13, 21,24, 31,34, 46,49, 57,60,
    75,5, 11,14, 20,23, 33,36, 45,48, 56,59,
    76,5, 12,14, 19,22, 32,35, 43,46, 54,57,
    77,5, 11,13, 20,22, 30,33, 44,46, 55,57,
    78,5, 10,12, 21,23, 31,33, 45,47, 56,58,
    79,5, 11,13, 22,24, 32,34, 44,46, 55,57,
    80,5, 12,14, 21,23, 33,35, 43,45, 54,56,
    0xFF /* terminator */
};

/* ─── 5×7 bitmap font ─── */
/* Index: A=0..Z=25, 0=26..9=35, ' '=36, .=37, ,=38, !=39, ?=40,
   '=41, -=42, ~=43, /=44, :=45, (=46, )=47, %=48 */
static const uint8_t font5x7[][7] = {
    {0x0e,0x11,0x11,0x1f,0x11,0x11,0x11}, /* A */
    {0x1e,0x11,0x11,0x1e,0x11,0x11,0x1e}, /* B */
    {0x0e,0x11,0x10,0x10,0x10,0x11,0x0e}, /* C */
    {0x1e,0x11,0x11,0x11,0x11,0x11,0x1e}, /* D */
    {0x1f,0x10,0x10,0x1e,0x10,0x10,0x1f}, /* E */
    {0x1f,0x10,0x10,0x1e,0x10,0x10,0x10}, /* F */
    {0x0e,0x11,0x10,0x17,0x11,0x11,0x0e}, /* G */
    {0x11,0x11,0x11,0x1f,0x11,0x11,0x11}, /* H */
    {0x1f,0x04,0x04,0x04,0x04,0x04,0x1f}, /* I */
    {0x07,0x02,0x02,0x02,0x02,0x12,0x0c}, /* J */
    {0x11,0x12,0x14,0x18,0x14,0x12,0x11}, /* K */
    {0x10,0x10,0x10,0x10,0x10,0x10,0x1f}, /* L */
    {0x11,0x1b,0x15,0x15,0x11,0x11,0x11}, /* M */
    {0x11,0x11,0x19,0x15,0x13,0x11,0x11}, /* N */
    {0x0e,0x11,0x11,0x11,0x11,0x11,0x0e}, /* O */
    {0x1e,0x11,0x11,0x1e,0x10,0x10,0x10}, /* P */
    {0x0e,0x11,0x11,0x11,0x15,0x12,0x0d}, /* Q */
    {0x1e,0x11,0x11,0x1e,0x14,0x12,0x11}, /* R */
    {0x0e,0x11,0x10,0x0e,0x01,0x11,0x0e}, /* S */
    {0x1f,0x04,0x04,0x04,0x04,0x04,0x04}, /* T */
    {0x11,0x11,0x11,0x11,0x11,0x11,0x0e}, /* U */
    {0x11,0x11,0x11,0x11,0x0a,0x0a,0x04}, /* V */
    {0x11,0x11,0x11,0x15,0x15,0x15,0x0a}, /* W */
    {0x11,0x11,0x0a,0x04,0x0a,0x11,0x11}, /* X */
    {0x11,0x11,0x0a,0x04,0x04,0x04,0x04}, /* Y */
    {0x1f,0x01,0x02,0x04,0x08,0x10,0x1f}, /* Z */
    {0x0e,0x11,0x13,0x15,0x19,0x11,0x0e}, /* 0 */
    {0x04,0x0c,0x04,0x04,0x04,0x04,0x0e}, /* 1 */
    {0x0e,0x11,0x01,0x06,0x08,0x10,0x1f}, /* 2 */
    {0x0e,0x11,0x01,0x06,0x01,0x11,0x0e}, /* 3 */
    {0x02,0x06,0x0a,0x12,0x1f,0x02,0x02}, /* 4 */
    {0x1f,0x10,0x1e,0x01,0x01,0x11,0x0e}, /* 5 */
    {0x0e,0x11,0x10,0x1e,0x11,0x11,0x0e}, /* 6 */
    {0x1f,0x01,0x02,0x04,0x08,0x08,0x08}, /* 7 */
    {0x0e,0x11,0x11,0x0e,0x11,0x11,0x0e}, /* 8 */
    {0x0e,0x11,0x11,0x0f,0x01,0x11,0x0e}, /* 9 */
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00}, /* ' ' */
    {0x00,0x00,0x00,0x00,0x00,0x0c,0x0c}, /* . */
    {0x00,0x00,0x00,0x00,0x04,0x04,0x08}, /* , */
    {0x04,0x04,0x04,0x04,0x04,0x00,0x04}, /* ! */
    {0x0e,0x11,0x01,0x06,0x04,0x00,0x04}, /* ? */
    {0x04,0x04,0x08,0x00,0x00,0x00,0x00}, /* ' */
    {0x00,0x00,0x00,0x1f,0x00,0x00,0x00}, /* - */
    {0x00,0x00,0x08,0x15,0x02,0x00,0x00}, /* ~ */
    {0x01,0x02,0x02,0x04,0x08,0x08,0x10}, /* / */
    {0x00,0x0c,0x0c,0x00,0x0c,0x0c,0x00}, /* : */
    {0x02,0x04,0x08,0x08,0x08,0x04,0x02}, /* ( */
    {0x08,0x04,0x02,0x02,0x02,0x04,0x08}, /* ) */
    {0x19,0x1a,0x02,0x04,0x08,0x0b,0x13}, /* % */
};

static const char font_chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?'-~/:()\%";

static int font_index(char c) {
    for (int i = 0; font_chars[i]; i++)
        if (font_chars[i] == c) return i;
    return 36; /* space fallback */
}

/* ─── Drawing primitives ─── */

static void fill_circle(int cx, int cy, int r_sq, int set) {
    int r = 5;
    for (int dy = -r; dy <= r; dy++)
        for (int dx = -r; dx <= r; dx++)
            if (dx * dx + dy * dy <= r_sq) {
                if (set) px_set_off(cx + dx, cy + dy);
                else     px_clr_off(cx + dx, cy + dy);
            }
}

static void draw_body(void) {
    const uint8_t *p = body_rle;
    while (*p != 0xFF) {
        int y = *p++;
        int n = *p++;
        for (int i = 0; i < n; i++) {
            int x0 = *p++;
            int x1 = *p++;
            for (int x = x0; x <= x1; x++)
                px_set_off(x, y);
        }
    }
}

static void draw_eyes(void) {
    /* White eye sockets: two circles r²=16 at (22,25) and (48,25) */
    fill_circle(22, 25, 16, 0);
    fill_circle(48, 25, 16, 0);
}

static void draw_pupils_normal(void) {
    /* Black pupils: r²=4 at (23,26) and (49,26) */
    fill_circle(23, 26, 4, 1);
    fill_circle(49, 26, 4, 1);
    /* White highlights: r²=1 at (20,23) and (46,23) */
    fill_circle(20, 23, 1, 0);
    fill_circle(46, 23, 1, 0);
}

static void draw_pupils_weird(void) {
    /* Misaligned: left up-left (21,24), right down-right (50,28) */
    fill_circle(21, 24, 4, 1);
    fill_circle(50, 28, 4, 1);
    fill_circle(20, 23, 1, 0);
    fill_circle(46, 23, 1, 0);
}

static void draw_pupils_unhinged(void) {
    /* Tiny pinprick pupils, no highlights */
    px_set_off(22, 25); px_set_off(23, 25); px_set_off(22, 26); px_set_off(23, 26);
    px_set_off(48, 25); px_set_off(49, 25); px_set_off(48, 26); px_set_off(49, 26);
}

/* ─── Mouth expressions ─── */

static void draw_mouth_smirk(void) {
    for (int x = 28; x < 44; x++) {
        float t = (x - 28) / 15.0f;
        float tilt = -2.0f + t * 4.0f;
        float v = 2.0f * t - 1.0f;
        float arc = (fabsf(v) < 1.0f) ? 5.0f * sqrtf(1.0f - v * v) : 0.0f;
        int yc = (int)(39.0f + tilt + arc);
        px_clr_off(x, yc);
        px_set_off(x, yc - 1);
        px_set_off(x, yc + 1);
    }
}

static void draw_mouth_smile(void) {
    for (int x = 26; x < 45; x++) {
        int cy = 38 + ((x - 35) * (x - 35)) / 25;
        px_set_off(x, cy);
        px_set_off(x, cy + 1);
    }
}

static void draw_mouth_open(void) {
    int cx = 35, cy = 40, rx = 7, ry = 5;
    for (int dy = -4; dy <= 4; dy++)
        for (int dx = -6; dx <= 6; dx++)
            if (dx*dx*16 + dy*dy*36 <= 36*16)
                px_clr_off(cx + dx, cy + dy);
    for (int dy = -ry; dy <= ry; dy++)
        for (int dx = -rx; dx <= rx; dx++) {
            if (dx*dx*ry*ry + dy*dy*rx*rx > rx*rx*ry*ry) continue;
            for (int nd = 0; nd < 4; nd++) {
                int nx = dx + ((nd==0)?-1:(nd==1)?1:0);
                int ny = dy + ((nd==2)?-1:(nd==3)?1:0);
                if (nx*nx*ry*ry + ny*ny*rx*rx > rx*rx*ry*ry) {
                    px_set_off(cx + dx, cy + dy);
                    break;
                }
            }
        }
}

static void draw_mouth_weird(void) {
    for (int x = 24; x < 48; x++) {
        float t = (x - 24) / 23.0f;
        int yc = 39 + (int)(3.5f * sinf(t * 3.14159f * 3.0f));
        px_clr_off(x, yc);
        px_set_off(x, yc - 1);
        px_set_off(x, yc + 1);
    }
}

static void draw_mouth_unhinged(void) {
    int cx = 35, cy = 41, rx = 10, ry = 7;
    for (int dy = -6; dy <= 6; dy++)
        for (int dx = -9; dx <= 9; dx++)
            if (dx*dx*36 + dy*dy*81 <= 81*36)
                px_clr_off(cx + dx, cy + dy);
    for (int dy = -ry; dy <= ry; dy++)
        for (int dx = -rx; dx <= rx; dx++) {
            if (dx*dx*ry*ry + dy*dy*rx*rx > rx*rx*ry*ry) continue;
            for (int nd = 0; nd < 4; nd++) {
                int nx = dx + ((nd==0)?-1:(nd==1)?1:0);
                int ny = dy + ((nd==2)?-1:(nd==3)?1:0);
                if (nx*nx*ry*ry + ny*ny*rx*rx > rx*rx*ry*ry) {
                    px_set_off(cx + dx, cy + dy);
                    break;
                }
            }
        }
    for (int x = cx - 7; x <= cx + 7; x += 3) {
        px_set_off(x, cy - 5);
        px_set_off(x, cy - 4);
        px_set_off(x + 1, cy - 4);
    }
}

/* ─── Chat bubble ─── */

static void draw_bubble(void) {
    int bx = 75, by = 5 + Y_OFF, bw = 170, bh = 70;
    /* Top/bottom edges (double thick) */
    for (int x = bx + 3; x < bx + bw - 3; x++) {
        px_set(x, by); px_set(x, by + 1);
        px_set(x, by + bh - 1); px_set(x, by + bh - 2);
    }
    /* Left/right edges */
    for (int y = by + 3; y < by + bh - 3; y++) {
        px_set(bx, y); px_set(bx + 1, y);
        px_set(bx + bw - 1, y); px_set(bx + bw - 2, y);
    }
    /* Rounded corners */
    int corners[][2] = {{bx+2,by+2},{bx+bw-3,by+2},{bx+2,by+bh-3},{bx+bw-3,by+bh-3}};
    for (int c = 0; c < 4; c++)
        for (int dy = -1; dy <= 1; dy++)
            for (int dx = -1; dx <= 1; dx++)
                if (abs(dx) + abs(dy) <= 1)
                    px_set(corners[c][0]+dx, corners[c][1]+dy);
    /* Speech tail */
    int tb = 35 + Y_OFF;
    static const int8_t tail_dx[] = {0,-1,-2,-3,-4,-5,-6,-7,-6,-5,-4,-3,-2,-1,0};
    static const int8_t tail_dy[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 7, 6, 5, 4};
    for (int i = 0; i < 15; i++)
        px_set(bx + tail_dx[i], tb + tail_dy[i]);
}

/* ─── Text rendering ─── */

static void draw_char(int x0, int y0, int idx) {
    for (int row = 0; row < 7; row++) {
        uint8_t bits = font5x7[idx][row];
        for (int col = 0; col < 5; col++)
            if (bits & (0x10 >> col))
                px_set(x0 + col, y0 + row);
    }
}

static void draw_text(int x0, int y0, const char *text, int max_w) {
    int cx = x0, cy = y0;
    int char_w = 6; /* 5px + 1px gap */

    /* Simple word-wrap */
    const char *p = text;
    while (*p) {
        /* Measure next word */
        const char *word_start = p;
        int wlen = 0;
        while (p[wlen] && p[wlen] != ' ') wlen++;

        int word_px = wlen * char_w;

        /* Wrap if this word won't fit on current line */
        if (cx > x0 && (cx - x0) + word_px > max_w) {
            cx = x0;
            cy += 9; /* 7px + 2px line gap */
        }

        /* Render the word */
        for (int i = 0; i < wlen; i++) {
            char c = p[i];
            if (c >= 'a' && c <= 'z') c -= 32; /* uppercase */
            draw_char(cx, cy, font_index(c));
            cx += char_w;
        }

        p += wlen;
        /* Skip spaces */
        if (*p == ' ') {
            cx += char_w;
            p++;
        }
    }
}

/* ─── Frame composition ─── */

/* ─── RTC clock helpers ─── */

static const char *month_names[] = {
    "JANUARY","FEBRUARY","MARCH","APRIL","MAY","JUNE",
    "JULY","AUGUST","SEPTEMBER","OCTOBER","NOVEMBER","DECEMBER"
};

static void draw_clock_header(void) {
    datetime_t t;
    rtc_get_datetime(&t);

    /* Format: "APRIL 12, 2026  3:47 PM" */
    char buf[48];
    int hr12 = t.hour % 12;
    if (hr12 == 0) hr12 = 12;
    const char *ampm = (t.hour < 12) ? "AM" : "PM";
    snprintf(buf, sizeof(buf), "%s %d, %d  %d:%02d %s",
             month_names[t.month - 1], t.day, t.year, hr12, t.min, ampm);

    /* Center the header (6px per char) */
    int len = (int)strlen(buf);
    int header_w = len * 6;
    int header_x = (IMG_W - header_w) / 2;
    if (header_x < 0) header_x = 0;

    /* draw_text uses raw px_set (no offset) — renders at y=1, top of screen */
    draw_text(header_x, 1, buf, IMG_W);
}

static void render_frame(const Quote *q, int expr) {
    /* Clear to white */
    memset(frame, 0, sizeof(frame));

    /* 0. Date & time header at top center (no Y offset) */
    draw_clock_header();

    /* 1. Body (with Y_OFF) */
    draw_body();

    /* 2. Eyes (white sockets, with Y_OFF) */
    draw_eyes();

    /* 3. Pupils (mood-specific, with Y_OFF) */
    switch (q->mood) {
        case MOOD_WEIRD:    draw_pupils_weird();    break;
        case MOOD_UNHINGED: draw_pupils_unhinged(); break;
        default:            draw_pupils_normal();   break;
    }

    /* 4. Mouth expression (with Y_OFF) */
    switch (expr) {
        case EXPR_OPEN:     draw_mouth_open();     break;
        case EXPR_SMILE:    draw_mouth_smile();    break;
        case EXPR_WEIRD:    draw_mouth_weird();    break;
        case EXPR_UNHINGED: draw_mouth_unhinged(); break;
        default:            draw_mouth_smirk();    break;
    }

    /* 5. Chat bubble outline (with Y_OFF via draw_bubble) */
    draw_bubble();

    /* 6. Quote text inside bubble (manually offset) */
    draw_text(81, 11 + Y_OFF, q->text, 158);

    /* 7. Tagline below bubble (manually offset) */
    int tag_y = 5 + 70 + 5 + Y_OFF;
    if (tag_y + 7 < IMG_H)
        draw_text(81, tag_y, TAGLINE, 170);
}

/* ─── Transpose landscape → portrait for e-ink driver ─── */

static void transpose_to_display(void) {
    uint16_t dst_row_bytes = (DISP_W + 7) / 8;
    memset(display_buf, 0xFF, sizeof(display_buf));

    for (int y = 0; y < IMG_H; y++) {
        for (int x = 0; x < IMG_W; x++) {
            int src_byte = y * IMG_ROW_BYTES + x / 8;
            int src_bit  = 7 - (x & 7);
            if ((frame[src_byte] >> src_bit) & 1) {
                int dx = y;
                int dy = 249 - x;
                int dst_byte = dy * dst_row_bytes + dx / 8;
                int dst_bit  = 7 - (dx & 7);
                display_buf[dst_byte] &= ~(1 << dst_bit);
            }
        }
    }
}

/* ─── Simple PRNG (seeded from ADC noise) ─── */

static uint32_t rng_state;

static void rng_seed(void) {
    adc_init();
    adc_gpio_init(26);
    adc_select_input(0);
    uint32_t seed = 0;
    for (int i = 0; i < 32; i++)
        seed = (seed << 1) | (adc_read() & 1);
    seed ^= time_us_32();
    rng_state = seed ? seed : 0xDEADBEEF;
}

static uint32_t rng_next(void) {
    rng_state ^= rng_state << 13;
    rng_state ^= rng_state >> 17;
    rng_state ^= rng_state << 5;
    return rng_state;
}

/* ─── Expression cycles per mood ─── */

static const uint8_t cycle_normal[]   = {EXPR_SMIRK, EXPR_OPEN, EXPR_SMILE, EXPR_OPEN};
static const uint8_t cycle_weird[]    = {EXPR_WEIRD, EXPR_OPEN, EXPR_WEIRD, EXPR_SMILE};
static const uint8_t cycle_unhinged[] = {EXPR_UNHINGED, EXPR_OPEN, EXPR_UNHINGED, EXPR_OPEN};

static const uint8_t *mood_cycle(uint8_t mood) {
    switch (mood) {
        case MOOD_WEIRD:    return cycle_weird;
        case MOOD_UNHINGED: return cycle_unhinged;
        default:            return cycle_normal;
    }
}

/* ─── Main ─── */

/* ─── Parse compile-time date/time to seed the RTC ─── */

static int parse_month(const char *s) {
    static const char *m[] = {"Jan","Feb","Mar","Apr","May","Jun",
                              "Jul","Aug","Sep","Oct","Nov","Dec"};
    for (int i = 0; i < 12; i++)
        if (s[0] == m[i][0] && s[1] == m[i][1] && s[2] == m[i][2])
            return i + 1;
    return 1;
}

static void init_rtc_from_compile_time(void) {
    /* __DATE__ = "Apr 12 2026", __TIME__ = "19:05:15" */
    const char *d = __DATE__;
    const char *t = __TIME__;

    datetime_t dt = {
        .year  = (int16_t)(atoi(d + 7)),
        .month = (int8_t)parse_month(d),
        .day   = (int8_t)atoi(d + 4),
        .dotw  = 0,  /* RTC doesn't need accurate day-of-week */
        .hour  = (int8_t)atoi(t),
        .min   = (int8_t)atoi(t + 3),
        .sec   = (int8_t)atoi(t + 6),
    };

    rtc_init();
    rtc_set_datetime(&dt);
    sleep_us(64);  /* wait for RTC to latch */
    printf("RTC set to %04d-%02d-%02d %02d:%02d:%02d\n",
           dt.year, dt.month, dt.day, dt.hour, dt.min, dt.sec);
}

int main(void) {
    stdio_init_all();
    sleep_ms(1000);
    printf("%s starting (display: %s, %d quotes)...\n", TAGLINE, DISPLAY_NAME, QUOTE_COUNT);

    /* Initialize RTC from compile time (keeps ticking from there) */
    init_rtc_from_compile_time();

    if (DEV_Module_Init() != 0) {
        printf("ERROR: Hardware init failed.\n");
        return 1;
    }

    EPD_Init();
    EPD_Clear();

    rng_seed();

    uint32_t frame_idx = 0;
    int qi = rng_next() % QUOTE_COUNT;

    while (true) {
        const Quote *q = &quotes[qi];
        const uint8_t *cycle = mood_cycle(q->mood);
        uint8_t expr = cycle[frame_idx % 4];

        /* Pick new quote on every OPEN mouth frame */
        if (expr == EXPR_OPEN && frame_idx > 0)
            qi = rng_next() % QUOTE_COUNT;

        /* Render */
        render_frame(&quotes[qi], expr);
        transpose_to_display();

        if (frame_idx == 0)
            EPD_Display(display_buf);
        else
            EPD_Partial(display_buf);

        printf("Frame %lu: [%s] %s\n",
               (unsigned long)frame_idx,
               q->mood == MOOD_WEIRD ? "weird" :
               q->mood == MOOD_UNHINGED ? "unhinged" : "normal",
               q->text);

        frame_idx++;
        sleep_ms(4000);
    }

    return 0;
}
