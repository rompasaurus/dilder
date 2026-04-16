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

/* Mood values (match quotes.h mood_map in devtool.py) */
#define MOOD_NORMAL   0
#define MOOD_WEIRD    1
#define MOOD_UNHINGED 2
#define MOOD_ANGRY    3
#define MOOD_SAD      4
#define MOOD_CHAOTIC  5
#define MOOD_HUNGRY   6
#define MOOD_TIRED    7
#define MOOD_SLAPHAPPY 8
#define MOOD_LAZY      9
#define MOOD_FAT       10
#define MOOD_CHILL     11
#define MOOD_CREEPY     12
#define MOOD_EXCITED   13
#define MOOD_NOSTALGIC 14
#define MOOD_HOMESICK  15

/* Mouth expressions */
#define EXPR_SMIRK    0
#define EXPR_OPEN     1
#define EXPR_SMILE    2
#define EXPR_WEIRD    3
#define EXPR_UNHINGED 4
#define EXPR_ANGRY    5
#define EXPR_SAD      6
#define EXPR_CHAOTIC  7
#define EXPR_HUNGRY   8
#define EXPR_TIRED    9
#define EXPR_SLAPHAPPY 10
#define EXPR_LAZY      11
#define EXPR_FAT       12
#define EXPR_CHILL     13
#define EXPR_CREEPY     14
#define EXPR_EXCITED   15
#define EXPR_NOSTALGIC 16
#define EXPR_HOMESICK  17

/* Landscape frame buffer (1 = black pixel, packed MSB-first) */
static uint8_t frame[IMG_ROW_BYTES * IMG_H];

/* Display buffer (portrait orientation for e-ink driver) */
static uint8_t display_buf[((DISP_W + 7) / 8) * DISP_H];

/* Vertical offset — pushes octopus + bubble down to make room for clock */
#define Y_OFF 12

/* ─── Body animation transform (set per-frame before rendering) ─── */
static int body_dx = 0;     /* global x shift */
static int body_dy = 0;     /* global y shift */
static int body_x_expand = 0; /* expand/shrink body spans (+ = wider) */
/* Per-row wobble amplitude and phase (for wavy effects) */
static float wobble_amp = 0;
static float wobble_freq = 0;
static float wobble_phase = 0;

static int row_wobble(int y) {
    if (wobble_amp == 0) return 0;
    return (int)(wobble_amp * sinf(y * wobble_freq + wobble_phase));
}

/* ─── Pixel helpers ─── */
static inline void px_set(int x, int y) {
    if (x >= 0 && x < IMG_W && y >= 0 && y < IMG_H)
        frame[y * IMG_ROW_BYTES + x / 8] |= (0x80 >> (x & 7));
}
static inline void px_clr(int x, int y) {
    if (x >= 0 && x < IMG_W && y >= 0 && y < IMG_H)
        frame[y * IMG_ROW_BYTES + x / 8] &= ~(0x80 >> (x & 7));
}
/* Offset versions — add Y_OFF + body transform before drawing */
static inline void px_set_off(int x, int y) {
    px_set(x + body_dx + row_wobble(y), y + Y_OFF + body_dy);
}
static inline void px_clr_off(int x, int y) {
    px_clr(x + body_dx + row_wobble(y), y + Y_OFF + body_dy);
}

/* ─── Fat octopus body (RLE: y, num_spans, x0, x1, ...) terminated by 0xFF ─
 *  Wider dome (+5px per side), no waist taper, thicker tentacles (+1px/side).
 *  Visually distinct from standard body — clearly chonky. ─── */
static const uint8_t body_rle[] = {
    /* ── Fat head dome — starts 2 rows earlier, widens faster ── */
     8,1, 25,45,   9,1, 21,49,
    10,1, 18,52,  11,1, 15,55,  12,1, 13,57,  13,1, 11,59,
    14,1, 10,60,  15,1,  9,61,  16,1,  8,62,  17,1,  7,63,
    18,1,  6,64,  19,1,  5,65,  20,1,  5,65,  21,1,  5,65,
    22,1,  5,65,  23,1,  5,65,  24,1,  5,65,  25,1,  5,65,
    26,1,  5,65,  27,1,  5,65,
    /* ── Fat body — stays wide, barely any waist ── */
    28,1,  5,65,  29,1,  5,65,  30,1,  5,65,  31,1,  6,64,
    32,1,  6,64,  33,1,  6,64,  34,1,  6,64,  35,1,  6,64,
    36,1,  6,64,  37,1,  6,64,  38,1,  6,64,  39,1,  6,64,
    40,1,  6,64,  41,1,  7,63,  42,1,  7,63,  43,1,  8,62,
    44,1,  9,61,  45,1, 10,60,
    /* ── Fat cheek bulge — stays wide ── */
    46,1,  8,62,  47,1,  7,63,  48,1,  6,64,  49,1,  6,64,
    50,1,  7,63,  51,1,  8,62,  52,1, 10,60,  53,1, 11,59,
    54,1, 12,58,
    /* ── Fat tentacles — each span widened +1px per side ── */
    55,5,  9,18, 20,29, 31,40, 42,51, 53,62,
    56,5,  7,16, 18,27, 29,38, 44,53, 55,64,
    57,5,  6,15, 17,25, 28,36, 46,54, 57,65,
    58,5,  5,13, 18,26, 30,38, 45,53, 56,64,
    59,5,  6,14, 20,28, 32,40, 43,51, 54,62,
    60,5,  7,15, 19,27, 30,38, 42,50, 53,61,
    61,5,  8,15, 17,25, 29,37, 43,51, 55,63,
    62,5,  7,14, 16,23, 30,38, 45,53, 56,64,
    63,5,  6,13, 17,24, 32,39, 44,52, 54,62,
    64,5,  7,14, 19,26, 31,38, 42,49, 53,60,
    65,5,  8,15, 18,25, 29,36, 43,50, 54,61,
    66,5,  9,15, 16,23, 30,37, 45,52, 56,63,
    67,5,  8,14, 17,23, 32,38, 44,51, 55,62,
    68,5,  7,13, 18,24, 31,37, 42,49, 53,60,
    69,5,  8,14, 20,26, 29,35, 43,49, 54,60,
    70,5,  9,15, 19,25, 30,36, 45,51, 56,62,
    71,5, 10,15, 17,23, 32,38, 44,50, 55,61,
    72,5,  9,14, 18,23, 31,36, 42,48, 53,59,
    73,5,  8,13, 19,24, 29,34, 43,48, 54,59,
    74,5,  9,14, 20,25, 30,35, 45,50, 56,61,
    75,5, 10,15, 19,24, 32,37, 44,49, 55,60,
    76,5, 11,15, 18,23, 31,36, 42,47, 53,58,
    77,5, 10,14, 19,23, 29,34, 43,47, 54,58,
    78,5,  9,13, 20,24, 30,34, 44,48, 55,59,
    79,5, 10,14, 21,25, 31,35, 43,47, 54,58,
    80,5, 11,15, 20,24, 32,36, 42,46, 53,57,
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

/* Body with span expansion applied (uses body_x_expand global) */
static void draw_body_transformed(void) {
    const uint8_t *p = body_rle;
    while (*p != 0xFF) {
        int y = *p++;
        int n = *p++;
        for (int i = 0; i < n; i++) {
            int x0 = *p++;
            int x1 = *p++;
            int ax0 = x0 - body_x_expand;
            int ax1 = x1 + body_x_expand;
            if (ax0 < 0) ax0 = 0;
            if (ax1 >= IMG_W) ax1 = IMG_W - 1;
            for (int x = ax0; x <= ax1; x++)
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

static void draw_pupils_angry(void) {
    /* Pupils shifted inward and down — glaring toward the nose */
    fill_circle(25, 27, 4, 1);  /* left: shifted right+down */
    fill_circle(47, 27, 4, 1);  /* right: shifted left+down */
    fill_circle(23, 24, 1, 0);  /* highlights */
    fill_circle(45, 24, 1, 0);
}

static void draw_brows_angry(void) {
    /* Thick slanted half-circle arcs across top of eye sockets.
       Outer edges high, inner edges low — angry V shape.
       Must match Python _octo_angry_eyes(). */
    for (int i = 0; i < 18; i++) {
        float t = i / 17.0f;
        int x = 14 + (int)(t * 16);
        float arc = 2.5f * sinf(t * 3.14159f);
        int y = (int)(20 + t * 5 - arc);
        for (int dy = 0; dy < 3; dy++) px_set_off(x, y + dy);
        px_set_off(x + 1, y + 1);
    }
    for (int i = 0; i < 18; i++) {
        float t = i / 17.0f;
        int x = 40 + (int)(t * 16);
        float arc = 2.5f * sinf(t * 3.14159f);
        int y = (int)(25 - t * 5 - arc);
        for (int dy = 0; dy < 3; dy++) px_set_off(x, y + dy);
        px_set_off(x + 1, y + 1);
    }
}

static void draw_pupils_sad(void) {
    /* Pupils shifted downward — looking at the floor */
    fill_circle(23, 28, 4, 1);
    fill_circle(49, 28, 4, 1);
    fill_circle(21, 25, 1, 0);
    fill_circle(47, 25, 1, 0);
}

static void draw_brows_sad(void) {
    /* Droopy brows — outer edges low, inner edges high (inverse of angry) */
    for (int i = 0; i < 18; i++) {
        float t = i / 17.0f;
        int x = 14 + (int)(t * 16);
        float arc = 2.5f * sinf(t * 3.14159f);
        int y = (int)(25 - t * 5 - arc);  /* inner high, outer low */
        for (int dy = 0; dy < 3; dy++) px_set_off(x, y + dy);
    }
    for (int i = 0; i < 18; i++) {
        float t = i / 17.0f;
        int x = 40 + (int)(t * 16);
        float arc = 2.5f * sinf(t * 3.14159f);
        int y = (int)(20 + t * 5 - arc);
        for (int dy = 0; dy < 3; dy++) px_set_off(x, y + dy);
    }
}

static void draw_pupils_chaotic(void) {
    /* Spiral/ring eyes — concentric circles for dizzy look */
    for (int ecx_i = 0; ecx_i < 2; ecx_i++) {
        int ecx = (ecx_i == 0) ? 22 : 48;
        /* Outer ring */
        for (int dy = -3; dy <= 3; dy++)
            for (int dx = -3; dx <= 3; dx++) {
                int dist = dx * dx + dy * dy;
                if (dist >= 5 && dist <= 9)
                    px_set_off(ecx + dx, 25 + dy);
            }
        /* Center dot */
        px_set_off(ecx, 25);
    }
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

static void draw_mouth_angry(void) {
    /* Tight downward frown — inverted parabola */
    for (int x = 28; x < 43; x++) {
        int cy = 40 - ((x - 35) * (x - 35)) / 20;
        px_set_off(x, cy);
        px_set_off(x, cy + 1);
    }
}

static void draw_mouth_sad(void) {
    /* Gentle downward curve frown */
    for (int x = 26; x < 45; x++) {
        int cy = 42 - ((x - 35) * (x - 35)) / 30;
        px_set_off(x, cy);
        px_set_off(x, cy + 1);
    }
}

static void draw_mouth_chaotic(void) {
    /* Zigzag lightning-bolt mouth */
    for (int x = 24; x < 48; x++) {
        int phase = (x - 24) % 6;
        int y = (phase < 3) ? 38 + phase * 2 : 44 - phase * 2 + 6;
        px_set_off(x, y);
        px_set_off(x, y + 1);
    }
}

static void draw_pupils_hungry(void) {
    /* Pupils shifted upward — staring at imaginary food */
    fill_circle(23, 23, 4, 1);
    fill_circle(49, 23, 4, 1);
    fill_circle(21, 21, 1, 0);
    fill_circle(47, 21, 1, 0);
}

static void draw_mouth_hungry(void) {
    /* Drooling open mouth — wide oval + drool drops */
    int cx = 35, cy = 40, rx = 8, ry = 5;
    /* White interior */
    for (int dy = -(ry-1); dy <= ry-1; dy++)
        for (int dx = -(rx-1); dx <= rx-1; dx++)
            if (dx*dx*(ry-1)*(ry-1) + dy*dy*(rx-1)*(rx-1) <= (rx-1)*(rx-1)*(ry-1)*(ry-1))
                px_clr_off(cx+dx, cy+dy);
    /* Black border */
    for (int dy = -ry; dy <= ry; dy++)
        for (int dx = -rx; dx <= rx; dx++) {
            if (dx*dx*ry*ry + dy*dy*rx*rx > rx*rx*ry*ry) continue;
            for (int nd = 0; nd < 4; nd++) {
                int nx = dx + ((nd==0)?-1:(nd==1)?1:0);
                int ny = dy + ((nd==2)?-1:(nd==3)?1:0);
                if (nx*nx*ry*ry + ny*ny*rx*rx > rx*rx*ry*ry) {
                    px_set_off(cx+dx, cy+dy);
                    break;
                }
            }
        }
    /* Drool drops */
    for (int dy = 1; dy < 6; dy++) px_set_off(33, cy+ry+dy);
    for (int dy = 1; dy < 4; dy++) px_set_off(37, cy+ry+dy+1);
}

static void draw_pupils_tired(void) {
    /* Tiny sleepy pupils low in half-closed eyes */
    for (int dx = -1; dx <= 1; dx++) {
        px_set_off(22+dx, 27); px_set_off(22+dx, 28);
        px_set_off(48+dx, 27); px_set_off(48+dx, 28);
    }
}

static void draw_lids_tired(void) {
    /* Half-closed eyelids: fill top half of eye sockets black */
    for (int ecx_i = 0; ecx_i < 2; ecx_i++) {
        int ecx = (ecx_i == 0) ? 22 : 48;
        for (int dy = -4; dy < -1; dy++)
            for (int dx = -4; dx <= 4; dx++)
                if (dx*dx + dy*dy <= 16)
                    px_set_off(ecx+dx, 25+dy);
    }
}

static void draw_mouth_tired(void) {
    /* Yawn mouth — tall oval, open wide vertically */
    int cx = 35, cy = 40, rx = 5, ry = 7;
    for (int dy = -(ry-1); dy <= ry-1; dy++)
        for (int dx = -(rx-1); dx <= rx-1; dx++)
            if (dx*dx*(ry-1)*(ry-1) + dy*dy*(rx-1)*(rx-1) <= (rx-1)*(rx-1)*(ry-1)*(ry-1))
                px_clr_off(cx+dx, cy+dy);
    for (int dy = -ry; dy <= ry; dy++)
        for (int dx = -rx; dx <= rx; dx++) {
            if (dx*dx*ry*ry + dy*dy*rx*rx > rx*rx*ry*ry) continue;
            for (int nd = 0; nd < 4; nd++) {
                int nx = dx + ((nd==0)?-1:(nd==1)?1:0);
                int ny = dy + ((nd==2)?-1:(nd==3)?1:0);
                if (nx*nx*ry*ry + ny*ny*rx*rx > rx*rx*ry*ry) {
                    px_set_off(cx+dx, cy+dy);
                    break;
                }
            }
        }
}

static void draw_eyes_slaphappy(void) {
    /* Left eye: squint shut (fill back to black, white slit) */
    for (int dy = -4; dy <= 4; dy++)
        for (int dx = -4; dx <= 4; dx++)
            if (dx*dx + dy*dy <= 16)
                px_set_off(22+dx, 25+dy);
    for (int dx = -3; dx <= 3; dx++)
        px_clr_off(22+dx, 25);
    /* Right eye: oversized pupil */
    fill_circle(49, 26, 9, 1);
}

static void draw_mouth_slaphappy(void) {
    /* Wide wobbly grin */
    for (int x = 22; x < 49; x++) {
        float t = (x - 22) / 26.0f;
        int base = 38 + ((x-35)*(x-35)) / 20;
        int wobble = (int)(1.5f * sinf(t * 3.14159f * 4.0f));
        int y = base + wobble;
        px_set_off(x, y);
        px_set_off(x, y+1);
    }
}

/* ─── Lazy: nearly-closed eyes, flat mouth ─── */

static void draw_lids_lazy(void) {
    /* Cover most of each eye socket — leave only bottom sliver open */
    for (int e = 0; e < 2; e++) {
        int ecx = e ? 48 : 22;
        for (int dy = -4; dy < 2; dy++)
            for (int dx = -4; dx <= 4; dx++)
                if (dx*dx + dy*dy <= 16)
                    px_set_off(ecx+dx, 25+dy);
    }
}

static void draw_pupils_lazy(void) {
    /* Barely visible dots low in the slit */
    for (int e = 0; e < 2; e++) {
        int ecx = e ? 48 : 22;
        px_set_off(ecx, 28);
        px_set_off(ecx+1, 28);
    }
}

static void draw_mouth_lazy(void) {
    /* Flat horizontal line — minimal effort */
    for (int x = 29; x < 42; x++) {
        px_set_off(x, 40);
        px_set_off(x, 41);
    }
}

/* ─── Fat: content wide pupils, smile with cheek puffs ─── */

static void draw_pupils_fat(void) {
    /* Wider pupils — happy and satisfied */
    for (int e = 0; e < 2; e++) {
        int ecx = e ? 49 : 23;
        for (int dy = -3; dy <= 3; dy++)
            for (int dx = -3; dx <= 3; dx++)
                if (dx*dx + dy*dy <= 9)
                    px_set_off(ecx+dx, 26+dy);
    }
}

static void draw_mouth_fat(void) {
    /* Wide satisfied smile + cheek puffs */
    for (int x = 24; x < 47; x++) {
        int cy = 38 + ((x-35)*(x-35)) / 18;
        px_set_off(x, cy);
        px_set_off(x, cy+1);
    }
    /* Cheek puffs */
    int cheeks[][2] = {{23,39},{47,39}};
    for (int c = 0; c < 2; c++)
        for (int dy = -2; dy <= 2; dy++)
            for (int dx = -2; dx <= 2; dx++)
                if (dx*dx + dy*dy <= 4)
                    px_set_off(cheeks[c][0]+dx, cheeks[c][1]+dy);
}

/* ─── Chill: side-glancing pupils, relaxed half-smile ─── */

static void draw_pupils_chill(void) {
    /* Pupils shifted right — looking to the side */
    int centers[][2] = {{25,26},{51,26}};
    for (int e = 0; e < 2; e++)
        for (int dy = -2; dy <= 2; dy++)
            for (int dx = -2; dx <= 2; dx++)
                if (dx*dx + dy*dy <= 4)
                    px_set_off(centers[e][0]+dx, centers[e][1]+dy);
}

static void draw_mouth_chill(void) {
    /* Slight asymmetric half-smile — relaxed */
    for (int x = 29; x < 44; x++) {
        float t = (x - 29) / 14.0f;
        int y = 40 + (int)(1.5f * t * t);
        px_set_off(x, y);
        px_set_off(x, y+1);
    }
}

/* ─── Creepy: heart-shaped pupils, tongue-out mouth ─── */

static void draw_pupils_creepy(void) {
    /* Heart-shaped pupils in each eye socket */
    for (int e = 0; e < 2; e++) {
        int ecx = e ? 48 : 22;
        /* Top bumps */
        static const int8_t top[][2] = {{-2,-1},{-1,-2},{0,-1},{1,-2},{2,-1}};
        for (int i = 0; i < 5; i++)
            px_set_off(ecx+top[i][0], 25+top[i][1]);
        /* Middle row */
        for (int dx = -2; dx <= 2; dx++)
            px_set_off(ecx+dx, 25);
        /* Lower taper */
        for (int dx = -1; dx <= 1; dx++)
            px_set_off(ecx+dx, 26);
        /* Bottom point */
        px_set_off(ecx, 27);
    }
}

static void draw_mouth_creepy(void) {
    /* Wide open smile with tongue hanging out */
    int cx = 35, cy = 39, rx = 8, ry = 5;
    for (int dy = 0; dy <= ry; dy++)
        for (int dx = -rx; dx <= rx; dx++) {
            int in = (dx*dx)*(ry*ry) + (dy*dy)*(rx*rx) <= (rx*rx)*(ry*ry);
            if (!in) continue;
            int edge = 0;
            if (dy == 0) edge = 1;
            else {
                int ndxs[] = {-1,1,0,0}, ndys[] = {0,0,-1,1};
                for (int n = 0; n < 4; n++) {
                    int nx = dx+ndxs[n], ny = dy+ndys[n];
                    if (ny < 0) continue;
                    if ((nx*nx)*(ry*ry)+(ny*ny)*(rx*rx) > (rx*rx)*(ry*ry))
                        { edge = 1; break; }
                }
            }
            if (edge) px_set_off(cx+dx, cy+dy);
            else      px_clr_off(cx+dx, cy+dy);
        }
    /* Tongue */
    for (int dy = 1; dy < 5; dy++)
        for (int dx = -2; dx <= 2; dx++)
            if (dx*dx + dy*dy <= 8)
                px_set_off(cx+dx, cy+ry+dy);
    /* Tongue interior */
    for (int dy = 2; dy < 4; dy++)
        for (int dx = -1; dx <= 1; dx++)
            px_clr_off(cx+dx, cy+ry+dy);
}

/* ─── Excited: star/sparkle pupils, wide open smile ─── */

static void draw_pupils_excited(void) {
    /* Star/sparkle cross-shaped pupils in each eye socket */
    for (int e = 0; e < 2; e++) {
        int ecx = e ? 48 : 22;
        /* Plus/cross shape */
        for (int d = -2; d <= 2; d++) {
            px_set_off(ecx + d, 25);   /* horizontal bar */
            px_set_off(ecx, 25 + d);   /* vertical bar */
        }
        /* Diagonal tips for sparkle */
        px_set_off(ecx - 1, 24); px_set_off(ecx + 1, 24);
        px_set_off(ecx - 1, 26); px_set_off(ecx + 1, 26);
    }
}

static void draw_mouth_excited(void) {
    /* Wide open smile — bigger upward curve than normal */
    for (int x = 22; x < 49; x++) {
        int cy = 37 + ((x - 35) * (x - 35)) / 12;
        px_set_off(x, cy);
        px_set_off(x, cy + 1);
    }
}

/* ─── Nostalgic: pupils looking up-right, gentle half-smile ─── */

static void draw_pupils_nostalgic(void) {
    /* Pupils shifted up and to the right — remembering */
    int centers[][2] = {{24, 23}, {50, 23}};
    for (int e = 0; e < 2; e++)
        for (int dy = -2; dy <= 2; dy++)
            for (int dx = -2; dx <= 2; dx++)
                if (dx*dx + dy*dy <= 4)
                    px_set_off(centers[e][0]+dx, centers[e][1]+dy);
}

static void draw_mouth_nostalgic(void) {
    /* Gentle closed half-smile — small, wistful */
    for (int x = 31; x < 40; x++) {
        float t = (x - 31) / 8.0f;
        float v = 2.0f * t - 1.0f;
        int y = 40 + (int)(1.5f * v * v);
        px_set_off(x, y);
        px_set_off(x, y + 1);
    }
}

/* ─── Homesick: watery eyes with tears, wobbly mouth ─── */

static void draw_pupils_homesick(void) {
    /* Normal-ish pupils, slightly lowered (sad-like) */
    for (int e = 0; e < 2; e++) {
        int ecx = e ? 49 : 23;
        for (int dy = -2; dy <= 2; dy++)
            for (int dx = -2; dx <= 2; dx++)
                if (dx*dx + dy*dy <= 4)
                    px_set_off(ecx+dx, 27+dy);
    }
}

static void draw_tears_homesick(void) {
    /* Tear drop pixels below each eye socket */
    for (int e = 0; e < 2; e++) {
        int ecx = e ? 48 : 22;
        px_set_off(ecx, 31);
        px_set_off(ecx, 32);
        px_set_off(ecx, 33);
        px_set_off(ecx - 1, 32);
        px_set_off(ecx + 1, 32);
    }
}

static void draw_mouth_homesick(void) {
    /* Wobbly trying-not-to-cry line — slightly wavy horizontal */
    for (int x = 28; x < 43; x++) {
        float t = (x - 28) / 14.0f;
        int y = 40 + (int)(1.5f * sinf(t * 3.14159f * 3.0f));
        px_set_off(x, y);
        px_set_off(x, y + 1);
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

static void setup_body_transform(uint8_t mood, uint32_t f) {
    /* Reset */
    body_dx = 0; body_dy = 0; body_x_expand = 0;
    wobble_amp = 0; wobble_freq = 0; wobble_phase = 0;

    float pi = 3.14159f;
    switch (mood) {
        case MOOD_ANGRY:
            body_dy = -1; body_x_expand = 2;
            wobble_amp = 0.5f; wobble_freq = 0.3f; wobble_phase = f * pi;
            break;
        case MOOD_SAD:
            body_dy = 3; body_x_expand = -1;
            break;
        case MOOD_UNHINGED:
            body_dx = (int)(1.5f * sinf(f * 7.3f));
            body_dy = (int)(1.5f * sinf(f * 5.1f + 1));
            break;
        case MOOD_WEIRD:
            body_dx = (int)(3 * sinf(f * 0.8f));
            wobble_amp = 1.5f; wobble_freq = 0.15f; wobble_phase = (float)f;
            break;
        case MOOD_CHAOTIC:
            body_dx = (int)(2 * sinf(f * 2.1f));
            body_dy = (int)(2 * sinf(f * 1.7f));
            wobble_amp = 3; wobble_freq = 0.25f; wobble_phase = f * 2.0f;
            break;
        case MOOD_HUNGRY:
            body_dy = -2 + (int)sinf(f * 1.5f);
            break;
        case MOOD_TIRED:
            body_dy = 2 + (int)sinf(f * 0.5f); body_x_expand = -1;
            break;
        case MOOD_SLAPHAPPY:
            body_dx = (int)(3 * sinf(f * 1.2f));
            wobble_amp = 2; wobble_freq = 0.1f; wobble_phase = f * 1.2f;
            break;
        case MOOD_LAZY:
            body_dy = 3; body_x_expand = 3;
            break;
        case MOOD_FAT:
            /* Body RLE is already fat — just gentle belly jiggle */
            body_dy = (int)(1.5f * sinf(f * 1.8f));
            break;
        case MOOD_CHILL:
            body_dx = (int)sinf(f * 0.4f); body_dy = 1;
            break;
        case MOOD_CREEPY:
            body_x_expand = (int)(2 * sinf(f * 2.0f));
            break;
        case MOOD_EXCITED:
            body_dy = (int)(3 * sinf(f * 3.0f));
            break;
        case MOOD_NOSTALGIC:
            body_dx = (int)(2 * sinf(f * 0.5f));
            body_dy = (int)sinf(f * 0.3f);
            break;
        case MOOD_HOMESICK:
            body_dy = 1; body_x_expand = -2;
            break;
        default: /* NORMAL: gentle breathing */
            body_dy = (int)sinf(f * 0.8f);
            break;
    }
}

static void render_frame(const Quote *q, int expr, uint32_t frame_idx) {
    /* Clear to white */
    memset(frame, 0, sizeof(frame));

    /* 0. Date & time header at top center (no Y offset) */
    draw_clock_header();

    /* 0b. Set up body animation transform for this frame */
    setup_body_transform(q->mood, frame_idx);

    /* 1. Body (with Y_OFF + body transform) */
    draw_body_transformed();

    /* 2. Eyes (white sockets, with Y_OFF) */
    draw_eyes();

    /* 3. Pupils (mood-specific, with Y_OFF) */
    switch (q->mood) {
        case MOOD_WEIRD:    draw_pupils_weird();    break;
        case MOOD_UNHINGED: draw_pupils_unhinged(); break;
        case MOOD_ANGRY:    draw_pupils_angry();    break;
        case MOOD_SAD:      draw_pupils_sad();      break;
        case MOOD_CHAOTIC:  draw_pupils_chaotic();  break;
        case MOOD_HUNGRY:   draw_pupils_hungry();   break;
        case MOOD_TIRED:    draw_pupils_tired();    break;
        case MOOD_LAZY:     draw_pupils_lazy();     break;
        case MOOD_FAT:      draw_pupils_fat();      break;
        case MOOD_CHILL:    draw_pupils_chill();    break;
        case MOOD_CREEPY:    draw_pupils_creepy();    break;
        case MOOD_EXCITED:  draw_pupils_excited();  break;
        case MOOD_NOSTALGIC: draw_pupils_nostalgic(); break;
        case MOOD_HOMESICK: draw_pupils_homesick(); break;
        default:            draw_pupils_normal();   break;
    }

    /* 3b. Eyebrows / eyelids / special eyes */
    if (q->mood == MOOD_ANGRY)     draw_brows_angry();
    if (q->mood == MOOD_SAD)       draw_brows_sad();
    if (q->mood == MOOD_TIRED)     draw_lids_tired();
    if (q->mood == MOOD_SLAPHAPPY) draw_eyes_slaphappy();
    if (q->mood == MOOD_LAZY)      draw_lids_lazy();
    if (q->mood == MOOD_HOMESICK)  draw_tears_homesick();

    /* 4. Mouth expression (with Y_OFF) */
    switch (expr) {
        case EXPR_OPEN:      draw_mouth_open();      break;
        case EXPR_SMILE:     draw_mouth_smile();     break;
        case EXPR_WEIRD:     draw_mouth_weird();     break;
        case EXPR_UNHINGED:  draw_mouth_unhinged();  break;
        case EXPR_ANGRY:     draw_mouth_angry();     break;
        case EXPR_SAD:       draw_mouth_sad();       break;
        case EXPR_CHAOTIC:   draw_mouth_chaotic();   break;
        case EXPR_HUNGRY:    draw_mouth_hungry();    break;
        case EXPR_TIRED:     draw_mouth_tired();     break;
        case EXPR_SLAPHAPPY: draw_mouth_slaphappy(); break;
        case EXPR_LAZY:      draw_mouth_lazy();      break;
        case EXPR_FAT:       draw_mouth_fat();       break;
        case EXPR_CHILL:     draw_mouth_chill();     break;
        case EXPR_CREEPY:     draw_mouth_creepy();     break;
        case EXPR_EXCITED:   draw_mouth_excited();   break;
        case EXPR_NOSTALGIC: draw_mouth_nostalgic(); break;
        case EXPR_HOMESICK:  draw_mouth_homesick();  break;
        default:             draw_mouth_smirk();     break;
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
static const uint8_t cycle_angry[]     = {EXPR_ANGRY, EXPR_OPEN, EXPR_ANGRY, EXPR_ANGRY};
static const uint8_t cycle_sad[]       = {EXPR_SAD, EXPR_OPEN, EXPR_SAD, EXPR_SMILE};
static const uint8_t cycle_chaotic[]   = {EXPR_CHAOTIC, EXPR_OPEN, EXPR_UNHINGED, EXPR_WEIRD};
static const uint8_t cycle_hungry[]    = {EXPR_HUNGRY, EXPR_OPEN, EXPR_HUNGRY, EXPR_SMILE};
static const uint8_t cycle_tired[]     = {EXPR_TIRED, EXPR_OPEN, EXPR_TIRED, EXPR_TIRED};
static const uint8_t cycle_slaphappy[] = {EXPR_SLAPHAPPY, EXPR_OPEN, EXPR_SLAPHAPPY, EXPR_SMILE};
static const uint8_t cycle_lazy[]      = {EXPR_LAZY, EXPR_LAZY, EXPR_LAZY, EXPR_OPEN};
static const uint8_t cycle_fat[]       = {EXPR_FAT, EXPR_OPEN, EXPR_FAT, EXPR_SMILE};
static const uint8_t cycle_chill[]     = {EXPR_CHILL, EXPR_OPEN, EXPR_CHILL, EXPR_SMILE};
static const uint8_t cycle_creepy[]     = {EXPR_CREEPY, EXPR_OPEN, EXPR_CREEPY, EXPR_SMILE};
static const uint8_t cycle_excited[]   = {EXPR_EXCITED, EXPR_OPEN, EXPR_EXCITED, EXPR_SMILE};
static const uint8_t cycle_nostalgic[] = {EXPR_NOSTALGIC, EXPR_OPEN, EXPR_NOSTALGIC, EXPR_SMILE};
static const uint8_t cycle_homesick[]  = {EXPR_HOMESICK, EXPR_OPEN, EXPR_HOMESICK, EXPR_HOMESICK};

static const uint8_t *mood_cycle(uint8_t mood) {
    switch (mood) {
        case MOOD_WEIRD:     return cycle_weird;
        case MOOD_UNHINGED:  return cycle_unhinged;
        case MOOD_ANGRY:     return cycle_angry;
        case MOOD_SAD:       return cycle_sad;
        case MOOD_CHAOTIC:   return cycle_chaotic;
        case MOOD_HUNGRY:    return cycle_hungry;
        case MOOD_TIRED:     return cycle_tired;
        case MOOD_SLAPHAPPY: return cycle_slaphappy;
        case MOOD_LAZY:      return cycle_lazy;
        case MOOD_FAT:       return cycle_fat;
        case MOOD_CHILL:     return cycle_chill;
        case MOOD_CREEPY:     return cycle_creepy;
        case MOOD_EXCITED:   return cycle_excited;
        case MOOD_NOSTALGIC: return cycle_nostalgic;
        case MOOD_HOMESICK:  return cycle_homesick;
        default:             return cycle_normal;
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
        render_frame(&quotes[qi], expr, frame_idx);
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
