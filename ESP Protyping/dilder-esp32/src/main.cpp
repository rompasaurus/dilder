/*
 * Dilder ESP32-S3 — Mood Selector
 *
 * Full port of the Pico W mood-selector with identical octopus rendering,
 * 16 emotional states, 823 quotes, joystick navigation, and serial input.
 *
 * Input:
 *   Joystick LEFT/RIGHT = cycle moods
 *   Joystick CENTER     = random mood
 *   Joystick UP         = new quote (same mood)
 *   Joystick DOWN       = show chip info
 *   Serial keyboard     = same keys as Pico version ([/] navigate, etc.)
 *
 * Display: Waveshare 2.13" V3 (SSD1680) via GxEPD2, landscape 250x122.
 */

#include <Arduino.h>
#include <SPI.h>
#include <GxEPD2_BW.h>
#include <Adafruit_GFX.h>
#include <math.h>
#include <string.h>
#include <stdio.h>

extern "C" {
#include "platform/board_config.h"
#include "platform/hal.h"
}

/* ── Display setup ──────────────────────────────────────────────── */
GxEPD2_BW<GxEPD2_213_BN, GxEPD2_213_BN::HEIGHT>
    display(GxEPD2_213_BN(PIN_EPD_CS, PIN_EPD_DC, PIN_EPD_RST, PIN_EPD_BUSY));

/* ── Canvas constants (same as Pico) ────────────────────────────── */
#define IMG_W         250
#define IMG_H         122
#define IMG_ROW_BYTES ((IMG_W + 7) / 8)

/* ── Mood definitions ───────────────────────────────────────────── */
#define MOOD_NORMAL    0
#define MOOD_WEIRD     1
#define MOOD_UNHINGED  2
#define MOOD_ANGRY     3
#define MOOD_SAD       4
#define MOOD_CHAOTIC   5
#define MOOD_HUNGRY    6
#define MOOD_TIRED     7
#define MOOD_SLAPHAPPY 8
#define MOOD_LAZY      9
#define MOOD_FAT       10
#define MOOD_CHILL     11
#define MOOD_CREEPY    12
#define MOOD_EXCITED   13
#define MOOD_NOSTALGIC 14
#define MOOD_HOMESICK  15
#define MOOD_COUNT     16

/* Mouth expressions */
#define EXPR_SMIRK     0
#define EXPR_OPEN      1
#define EXPR_SMILE     2
#define EXPR_WEIRD     3
#define EXPR_UNHINGED  4
#define EXPR_ANGRY     5
#define EXPR_SAD       6
#define EXPR_CHAOTIC   7
#define EXPR_HUNGRY    8
#define EXPR_TIRED     9
#define EXPR_SLAPHAPPY 10
#define EXPR_LAZY      11
#define EXPR_FAT       12
#define EXPR_CHILL     13
#define EXPR_CREEPY    14
#define EXPR_EXCITED   15
#define EXPR_NOSTALGIC 16
#define EXPR_HOMESICK  17

static const char *mood_names[MOOD_COUNT] = {
    "SASSY",    "WEIRD",    "UNHINGED",   "ANGRY",
    "SAD",      "CHAOTIC",  "HUNGRY",     "TIRED",
    "SLAPHAPPY","LAZY",     "FAT",        "CHILL",
    "CREEPY",   "EXCITED",  "NOSTALGIC",  "HOMESICK",
};

/* ── Framebuffer (landscape, same as Pico) ──────────────────────── */
static uint8_t frame[IMG_ROW_BYTES * IMG_H];

#define Y_OFF 12

/* ── Body animation transform ───────────────────────────────────── */
static int body_dx = 0, body_dy = 0, body_x_expand = 0;
static float wobble_amp = 0, wobble_freq = 0, wobble_phase = 0;

static int row_wobble(int y) {
    if (wobble_amp == 0) return 0;
    return (int)(wobble_amp * sinf(y * wobble_freq + wobble_phase));
}

/* ── Pixel helpers (identical to Pico) ──────────────────────────── */
static inline void px_set(int x, int y) {
    if (x >= 0 && x < IMG_W && y >= 0 && y < IMG_H)
        frame[y * IMG_ROW_BYTES + x / 8] |= (0x80 >> (x & 7));
}
static inline void px_clr(int x, int y) {
    if (x >= 0 && x < IMG_W && y >= 0 && y < IMG_H)
        frame[y * IMG_ROW_BYTES + x / 8] &= ~(0x80 >> (x & 7));
}
static inline void px_set_off(int x, int y) {
    px_set(x + body_dx + row_wobble(y), y + Y_OFF + body_dy);
}
static inline void px_clr_off(int x, int y) {
    px_clr(x + body_dx + row_wobble(y), y + Y_OFF + body_dy);
}

/* ── Quotes (auto-generated, 823 entries) ───────────────────────── */
#include "quotes.h"

/* ══════════════════════════════════════════════════════════════════
 *  OCTOPUS RENDERING ENGINE
 *  (Copied verbatim from Pico mood-selector — platform-independent)
 * ══════════════════════════════════════════════════════════════════ */

/* ── Body RLE data ──────────────────────────────────────────────── */
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
    0xFF
};

/* ── 5x7 bitmap font ────────────────────────────────────────────── */
static const uint8_t font5x7[][7] = {
    {0x0e,0x11,0x11,0x1f,0x11,0x11,0x11}, {0x1e,0x11,0x11,0x1e,0x11,0x11,0x1e},
    {0x0e,0x11,0x10,0x10,0x10,0x11,0x0e}, {0x1e,0x11,0x11,0x11,0x11,0x11,0x1e},
    {0x1f,0x10,0x10,0x1e,0x10,0x10,0x1f}, {0x1f,0x10,0x10,0x1e,0x10,0x10,0x10},
    {0x0e,0x11,0x10,0x17,0x11,0x11,0x0e}, {0x11,0x11,0x11,0x1f,0x11,0x11,0x11},
    {0x1f,0x04,0x04,0x04,0x04,0x04,0x1f}, {0x07,0x02,0x02,0x02,0x02,0x12,0x0c},
    {0x11,0x12,0x14,0x18,0x14,0x12,0x11}, {0x10,0x10,0x10,0x10,0x10,0x10,0x1f},
    {0x11,0x1b,0x15,0x15,0x11,0x11,0x11}, {0x11,0x11,0x19,0x15,0x13,0x11,0x11},
    {0x0e,0x11,0x11,0x11,0x11,0x11,0x0e}, {0x1e,0x11,0x11,0x1e,0x10,0x10,0x10},
    {0x0e,0x11,0x11,0x11,0x15,0x12,0x0d}, {0x1e,0x11,0x11,0x1e,0x14,0x12,0x11},
    {0x0e,0x11,0x10,0x0e,0x01,0x11,0x0e}, {0x1f,0x04,0x04,0x04,0x04,0x04,0x04},
    {0x11,0x11,0x11,0x11,0x11,0x11,0x0e}, {0x11,0x11,0x11,0x11,0x0a,0x0a,0x04},
    {0x11,0x11,0x11,0x15,0x15,0x15,0x0a}, {0x11,0x11,0x0a,0x04,0x0a,0x11,0x11},
    {0x11,0x11,0x0a,0x04,0x04,0x04,0x04}, {0x1f,0x01,0x02,0x04,0x08,0x10,0x1f},
    {0x0e,0x11,0x13,0x15,0x19,0x11,0x0e}, {0x04,0x0c,0x04,0x04,0x04,0x04,0x0e},
    {0x0e,0x11,0x01,0x06,0x08,0x10,0x1f}, {0x0e,0x11,0x01,0x06,0x01,0x11,0x0e},
    {0x02,0x06,0x0a,0x12,0x1f,0x02,0x02}, {0x1f,0x10,0x1e,0x01,0x01,0x11,0x0e},
    {0x0e,0x11,0x10,0x1e,0x11,0x11,0x0e}, {0x1f,0x01,0x02,0x04,0x08,0x08,0x08},
    {0x0e,0x11,0x11,0x0e,0x11,0x11,0x0e}, {0x0e,0x11,0x11,0x0f,0x01,0x11,0x0e},
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00}, {0x00,0x00,0x00,0x00,0x00,0x0c,0x0c},
    {0x00,0x00,0x00,0x00,0x04,0x04,0x08}, {0x04,0x04,0x04,0x04,0x04,0x00,0x04},
    {0x0e,0x11,0x01,0x06,0x04,0x00,0x04}, {0x04,0x04,0x08,0x00,0x00,0x00,0x00},
    {0x00,0x00,0x00,0x1f,0x00,0x00,0x00}, {0x00,0x00,0x08,0x15,0x02,0x00,0x00},
    {0x01,0x02,0x02,0x04,0x08,0x08,0x10}, {0x00,0x0c,0x0c,0x00,0x0c,0x0c,0x00},
    {0x02,0x04,0x08,0x08,0x08,0x04,0x02}, {0x08,0x04,0x02,0x02,0x02,0x04,0x08},
    {0x19,0x1a,0x02,0x04,0x08,0x0b,0x13}, {0x01,0x02,0x04,0x08,0x04,0x02,0x01},
    {0x10,0x08,0x04,0x02,0x04,0x08,0x10},
};

static const char font_chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?'-~/:()\%<>";

static int font_index(char c) {
    for (int i = 0; font_chars[i]; i++)
        if (font_chars[i] == c) return i;
    return 36;
}

/* ── Drawing primitives ─────────────────────────────────────────── */

static void fill_circle(int cx, int cy, int r_sq, int set) {
    int r = 5;
    for (int dy = -r; dy <= r; dy++)
        for (int dx = -r; dx <= r; dx++)
            if (dx * dx + dy * dy <= r_sq) {
                if (set) px_set_off(cx + dx, cy + dy);
                else     px_clr_off(cx + dx, cy + dy);
            }
}

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

static void draw_eyes(void) { fill_circle(22, 25, 16, 0); fill_circle(48, 25, 16, 0); }

/* ── Pupil variations (identical to Pico) ───────────────────────── */
static void draw_pupils_normal(void) { fill_circle(23,26,4,1); fill_circle(49,26,4,1); fill_circle(20,23,1,0); fill_circle(46,23,1,0); }
static void draw_pupils_weird(void) { fill_circle(21,24,4,1); fill_circle(50,28,4,1); fill_circle(20,23,1,0); fill_circle(46,23,1,0); }
static void draw_pupils_unhinged(void) { px_set_off(22,25); px_set_off(23,25); px_set_off(22,26); px_set_off(23,26); px_set_off(48,25); px_set_off(49,25); px_set_off(48,26); px_set_off(49,26); }
static void draw_pupils_angry(void) { fill_circle(25,27,4,1); fill_circle(47,27,4,1); fill_circle(23,24,1,0); fill_circle(45,24,1,0); }

static void draw_brows_angry(void) {
    for (int i = 0; i < 18; i++) { float t = i / 17.0f; int x = 14 + (int)(t * 16); float arc = 2.5f * sinf(t * 3.14159f); int y = (int)(20 + t * 5 - arc); for (int dy = 0; dy < 3; dy++) px_set_off(x, y + dy); px_set_off(x + 1, y + 1); }
    for (int i = 0; i < 18; i++) { float t = i / 17.0f; int x = 40 + (int)(t * 16); float arc = 2.5f * sinf(t * 3.14159f); int y = (int)(25 - t * 5 - arc); for (int dy = 0; dy < 3; dy++) px_set_off(x, y + dy); px_set_off(x + 1, y + 1); }
}

static void draw_pupils_sad(void) { fill_circle(23,28,4,1); fill_circle(49,28,4,1); fill_circle(21,25,1,0); fill_circle(47,25,1,0); }

static void draw_brows_sad(void) {
    for (int i = 0; i < 18; i++) { float t = i / 17.0f; int x = 14 + (int)(t * 16); float arc = 2.5f * sinf(t * 3.14159f); int y = (int)(25 - t * 5 - arc); for (int dy = 0; dy < 3; dy++) px_set_off(x, y + dy); }
    for (int i = 0; i < 18; i++) { float t = i / 17.0f; int x = 40 + (int)(t * 16); float arc = 2.5f * sinf(t * 3.14159f); int y = (int)(20 + t * 5 - arc); for (int dy = 0; dy < 3; dy++) px_set_off(x, y + dy); }
}

static void draw_pupils_chaotic(void) {
    for (int ecx_i = 0; ecx_i < 2; ecx_i++) { int ecx = (ecx_i == 0) ? 22 : 48; for (int dy = -3; dy <= 3; dy++) for (int dx = -3; dx <= 3; dx++) { int dist = dx*dx + dy*dy; if (dist >= 5 && dist <= 9) px_set_off(ecx+dx, 25+dy); } px_set_off(ecx, 25); }
}

static void draw_pupils_hungry(void) { fill_circle(23,23,4,1); fill_circle(49,23,4,1); fill_circle(21,21,1,0); fill_circle(47,21,1,0); }
static void draw_pupils_tired(void) { for (int dx = -1; dx <= 1; dx++) { px_set_off(22+dx,27); px_set_off(22+dx,28); px_set_off(48+dx,27); px_set_off(48+dx,28); } }

static void draw_lids_tired(void) {
    for (int ecx_i = 0; ecx_i < 2; ecx_i++) { int ecx = (ecx_i == 0) ? 22 : 48; for (int dy = -4; dy < -1; dy++) for (int dx = -4; dx <= 4; dx++) if (dx*dx+dy*dy <= 16) px_set_off(ecx+dx, 25+dy); }
}

static void draw_eyes_slaphappy(void) {
    for (int dy = -4; dy <= 4; dy++) for (int dx = -4; dx <= 4; dx++) if (dx*dx+dy*dy <= 16) px_set_off(22+dx, 25+dy);
    for (int dx = -3; dx <= 3; dx++) px_clr_off(22+dx, 25);
    fill_circle(49, 26, 9, 1);
}

static void draw_lids_lazy(void) { for (int e = 0; e < 2; e++) { int ecx = e ? 48 : 22; for (int dy = -4; dy < 2; dy++) for (int dx = -4; dx <= 4; dx++) if (dx*dx+dy*dy <= 16) px_set_off(ecx+dx, 25+dy); } }
static void draw_pupils_lazy(void) { for (int e = 0; e < 2; e++) { int ecx = e ? 48 : 22; px_set_off(ecx,28); px_set_off(ecx+1,28); } }
static void draw_pupils_fat(void) { for (int e = 0; e < 2; e++) { int ecx = e ? 49 : 23; for (int dy = -3; dy <= 3; dy++) for (int dx = -3; dx <= 3; dx++) if (dx*dx+dy*dy <= 9) px_set_off(ecx+dx, 26+dy); } }
static void draw_pupils_chill(void) { int c[][2] = {{25,26},{51,26}}; for (int e = 0; e < 2; e++) for (int dy = -2; dy <= 2; dy++) for (int dx = -2; dx <= 2; dx++) if (dx*dx+dy*dy <= 4) px_set_off(c[e][0]+dx, c[e][1]+dy); }

static void draw_pupils_creepy(void) {
    for (int e = 0; e < 2; e++) { int ecx = e ? 48 : 22; static const int8_t top[][2] = {{-2,-1},{-1,-2},{0,-1},{1,-2},{2,-1}}; for (int i = 0; i < 5; i++) px_set_off(ecx+top[i][0], 25+top[i][1]); for (int dx = -2; dx <= 2; dx++) px_set_off(ecx+dx, 25); for (int dx = -1; dx <= 1; dx++) px_set_off(ecx+dx, 26); px_set_off(ecx, 27); }
}

static void draw_pupils_excited(void) { for (int e = 0; e < 2; e++) { int ecx = e ? 48 : 22; for (int d = -2; d <= 2; d++) { px_set_off(ecx+d,25); px_set_off(ecx,25+d); } px_set_off(ecx-1,24); px_set_off(ecx+1,24); px_set_off(ecx-1,26); px_set_off(ecx+1,26); } }
static void draw_pupils_nostalgic(void) { int c[][2] = {{24,23},{50,23}}; for (int e = 0; e < 2; e++) for (int dy = -2; dy <= 2; dy++) for (int dx = -2; dx <= 2; dx++) if (dx*dx+dy*dy <= 4) px_set_off(c[e][0]+dx, c[e][1]+dy); }
static void draw_pupils_homesick(void) { for (int e = 0; e < 2; e++) { int ecx = e ? 49 : 23; for (int dy = -2; dy <= 2; dy++) for (int dx = -2; dx <= 2; dx++) if (dx*dx+dy*dy <= 4) px_set_off(ecx+dx, 27+dy); } }
static void draw_tears_homesick(void) { for (int e = 0; e < 2; e++) { int ecx = e ? 48 : 22; px_set_off(ecx,31); px_set_off(ecx,32); px_set_off(ecx,33); px_set_off(ecx-1,32); px_set_off(ecx+1,32); } }

/* ── Mouth expressions (identical to Pico) ──────────────────────── */
static void draw_mouth_smirk(void) { for (int x = 28; x < 44; x++) { float t = (x-28)/15.0f; float tilt = -2.0f+t*4.0f; float v = 2.0f*t-1.0f; float arc = (fabsf(v)<1.0f) ? 5.0f*sqrtf(1.0f-v*v) : 0.0f; int yc = (int)(39.0f+tilt+arc); px_clr_off(x,yc); px_set_off(x,yc-1); px_set_off(x,yc+1); } }
static void draw_mouth_smile(void) { for (int x = 26; x < 45; x++) { int cy = 38+((x-35)*(x-35))/25; px_set_off(x,cy); px_set_off(x,cy+1); } }

static void draw_mouth_open(void) {
    int cx=35, cy=40, rx=7, ry=5;
    for (int dy=-4; dy<=4; dy++) for (int dx=-6; dx<=6; dx++) if (dx*dx*16+dy*dy*36<=36*16) px_clr_off(cx+dx,cy+dy);
    for (int dy=-ry; dy<=ry; dy++) for (int dx=-rx; dx<=rx; dx++) { if (dx*dx*ry*ry+dy*dy*rx*rx>rx*rx*ry*ry) continue; for (int nd=0;nd<4;nd++) { int nx=dx+((nd==0)?-1:(nd==1)?1:0); int ny=dy+((nd==2)?-1:(nd==3)?1:0); if (nx*nx*ry*ry+ny*ny*rx*rx>rx*rx*ry*ry) { px_set_off(cx+dx,cy+dy); break; } } }
}

static void draw_mouth_weird(void) { for (int x=24;x<48;x++) { float t=(x-24)/23.0f; int yc=39+(int)(3.5f*sinf(t*3.14159f*3.0f)); px_clr_off(x,yc); px_set_off(x,yc-1); px_set_off(x,yc+1); } }

static void draw_mouth_unhinged(void) {
    int cx=35,cy=41,rx=10,ry=7;
    for (int dy=-6;dy<=6;dy++) for (int dx=-9;dx<=9;dx++) if (dx*dx*36+dy*dy*81<=81*36) px_clr_off(cx+dx,cy+dy);
    for (int dy=-ry;dy<=ry;dy++) for (int dx=-rx;dx<=rx;dx++) { if (dx*dx*ry*ry+dy*dy*rx*rx>rx*rx*ry*ry) continue; for (int nd=0;nd<4;nd++) { int nx=dx+((nd==0)?-1:(nd==1)?1:0); int ny=dy+((nd==2)?-1:(nd==3)?1:0); if (nx*nx*ry*ry+ny*ny*rx*rx>rx*rx*ry*ry) { px_set_off(cx+dx,cy+dy); break; } } }
    for (int x=cx-7;x<=cx+7;x+=3) { px_set_off(x,cy-5); px_set_off(x,cy-4); px_set_off(x+1,cy-4); }
}

static void draw_mouth_angry(void) { for (int x=28;x<43;x++) { int cy=40-((x-35)*(x-35))/20; px_set_off(x,cy); px_set_off(x,cy+1); } }
static void draw_mouth_sad(void) { for (int x=26;x<45;x++) { int cy=42-((x-35)*(x-35))/30; px_set_off(x,cy); px_set_off(x,cy+1); } }
static void draw_mouth_chaotic(void) { for (int x=24;x<48;x++) { int phase=(x-24)%6; int y=(phase<3)?38+phase*2:44-phase*2+6; px_set_off(x,y); px_set_off(x,y+1); } }

static void draw_mouth_hungry(void) {
    int cx=35,cy=40,rx=8,ry=5;
    for (int dy=-(ry-1);dy<=ry-1;dy++) for (int dx=-(rx-1);dx<=rx-1;dx++) if (dx*dx*(ry-1)*(ry-1)+dy*dy*(rx-1)*(rx-1)<=(rx-1)*(rx-1)*(ry-1)*(ry-1)) px_clr_off(cx+dx,cy+dy);
    for (int dy=-ry;dy<=ry;dy++) for (int dx=-rx;dx<=rx;dx++) { if (dx*dx*ry*ry+dy*dy*rx*rx>rx*rx*ry*ry) continue; for (int nd=0;nd<4;nd++) { int nx=dx+((nd==0)?-1:(nd==1)?1:0); int ny=dy+((nd==2)?-1:(nd==3)?1:0); if (nx*nx*ry*ry+ny*ny*rx*rx>rx*rx*ry*ry) { px_set_off(cx+dx,cy+dy); break; } } }
    for (int dy=1;dy<6;dy++) px_set_off(33,cy+ry+dy); for (int dy=1;dy<4;dy++) px_set_off(37,cy+ry+dy+1);
}

static void draw_mouth_tired(void) {
    int cx=35,cy=40,rx=5,ry=7;
    for (int dy=-(ry-1);dy<=ry-1;dy++) for (int dx=-(rx-1);dx<=rx-1;dx++) if (dx*dx*(ry-1)*(ry-1)+dy*dy*(rx-1)*(rx-1)<=(rx-1)*(rx-1)*(ry-1)*(ry-1)) px_clr_off(cx+dx,cy+dy);
    for (int dy=-ry;dy<=ry;dy++) for (int dx=-rx;dx<=rx;dx++) { if (dx*dx*ry*ry+dy*dy*rx*rx>rx*rx*ry*ry) continue; for (int nd=0;nd<4;nd++) { int nx=dx+((nd==0)?-1:(nd==1)?1:0); int ny=dy+((nd==2)?-1:(nd==3)?1:0); if (nx*nx*ry*ry+ny*ny*rx*rx>rx*rx*ry*ry) { px_set_off(cx+dx,cy+dy); break; } } }
}

static void draw_mouth_slaphappy(void) { for (int x=22;x<49;x++) { float t=(x-22)/26.0f; int base=38+((x-35)*(x-35))/20; int w=(int)(1.5f*sinf(t*3.14159f*4.0f)); px_set_off(x,base+w); px_set_off(x,base+w+1); } }
static void draw_mouth_lazy(void) { for (int x=29;x<42;x++) { px_set_off(x,40); px_set_off(x,41); } }
static void draw_mouth_fat(void) { for (int x=24;x<47;x++) { int cy=38+((x-35)*(x-35))/18; px_set_off(x,cy); px_set_off(x,cy+1); } int ch[][2]={{23,39},{47,39}}; for (int c=0;c<2;c++) for (int dy=-2;dy<=2;dy++) for (int dx=-2;dx<=2;dx++) if (dx*dx+dy*dy<=4) px_set_off(ch[c][0]+dx,ch[c][1]+dy); }
static void draw_mouth_chill(void) { for (int x=29;x<44;x++) { float t=(x-29)/14.0f; int y=40+(int)(1.5f*t*t); px_set_off(x,y); px_set_off(x,y+1); } }

static void draw_mouth_creepy(void) {
    int cx=35,cy=39,rx=8,ry=5;
    for (int dy=0;dy<=ry;dy++) for (int dx=-rx;dx<=rx;dx++) { int in=(dx*dx)*(ry*ry)+(dy*dy)*(rx*rx)<=(rx*rx)*(ry*ry); if (!in) continue; int edge=0; if (dy==0) edge=1; else { int ndxs[]={-1,1,0,0},ndys[]={0,0,-1,1}; for (int n=0;n<4;n++) { int nx=dx+ndxs[n],ny=dy+ndys[n]; if (ny<0) continue; if ((nx*nx)*(ry*ry)+(ny*ny)*(rx*rx)>(rx*rx)*(ry*ry)) {edge=1;break;} } } if (edge) px_set_off(cx+dx,cy+dy); else px_clr_off(cx+dx,cy+dy); }
    for (int dy=1;dy<5;dy++) for (int dx=-2;dx<=2;dx++) if (dx*dx+dy*dy<=8) px_set_off(cx+dx,cy+ry+dy);
    for (int dy=2;dy<4;dy++) for (int dx=-1;dx<=1;dx++) px_clr_off(cx+dx,cy+ry+dy);
}

static void draw_mouth_excited(void) { for (int x=22;x<49;x++) { int cy=37+((x-35)*(x-35))/12; px_set_off(x,cy); px_set_off(x,cy+1); } }
static void draw_mouth_nostalgic(void) { for (int x=31;x<40;x++) { float t=(x-31)/8.0f; float v=2.0f*t-1.0f; int y=40+(int)(1.5f*v*v); px_set_off(x,y); px_set_off(x,y+1); } }
static void draw_mouth_homesick(void) { for (int x=28;x<43;x++) { float t=(x-28)/14.0f; int y=40+(int)(1.5f*sinf(t*3.14159f*3.0f)); px_set_off(x,y); px_set_off(x,y+1); } }

/* ── Chat bubble ────────────────────────────────────────────────── */
static void draw_bubble(void) {
    int bx=75, by=5+Y_OFF, bw=170, bh=70;
    for (int x=bx+3;x<bx+bw-3;x++) { px_set(x,by); px_set(x,by+1); px_set(x,by+bh-1); px_set(x,by+bh-2); }
    for (int y=by+3;y<by+bh-3;y++) { px_set(bx,y); px_set(bx+1,y); px_set(bx+bw-1,y); px_set(bx+bw-2,y); }
    int corners[][2] = {{bx+2,by+2},{bx+bw-3,by+2},{bx+2,by+bh-3},{bx+bw-3,by+bh-3}};
    for (int c=0;c<4;c++) for (int dy=-1;dy<=1;dy++) for (int dx=-1;dx<=1;dx++) if (abs(dx)+abs(dy)<=1) px_set(corners[c][0]+dx,corners[c][1]+dy);
    int tb=35+Y_OFF;
    static const int8_t tail_dx[]={0,-1,-2,-3,-4,-5,-6,-7,-6,-5,-4,-3,-2,-1,0};
    static const int8_t tail_dy[]={0,1,2,3,4,5,6,7,8,8,8,7,6,5,4};
    for (int i=0;i<15;i++) px_set(bx+tail_dx[i], tb+tail_dy[i]);
}

/* ── Text rendering ─────────────────────────────────────────────── */
static void draw_char(int x0, int y0, int idx) { for (int row=0;row<7;row++) { uint8_t bits=font5x7[idx][row]; for (int col=0;col<5;col++) if (bits&(0x10>>col)) px_set(x0+col,y0+row); } }

static void draw_text(int x0, int y0, const char *text, int max_w) {
    int cx=x0, cy=y0, char_w=6;
    const char *p = text;
    while (*p) {
        const char *ws = p; int wlen = 0;
        while (p[wlen] && p[wlen] != ' ') wlen++;
        int word_px = wlen * char_w;
        if (cx > x0 && (cx - x0) + word_px > max_w) { cx = x0; cy += 9; }
        for (int i = 0; i < wlen; i++) { char c = p[i]; if (c >= 'a' && c <= 'z') c -= 32; draw_char(cx, cy, font_index(c)); cx += char_w; }
        p += wlen;
        if (*p == ' ') { cx += char_w; p++; }
    }
}

/* ── Clock header (ESP32 uses millis-based synthetic time) ──────── */
static void draw_clock_header(void) {
    unsigned long ms = millis();
    unsigned long total_s = ms / 1000;
    /* Synthetic clock starting at noon */
    int hour = (12 + (int)(total_s / 3600)) % 24;
    int minute = (int)((total_s % 3600) / 60);
    int hr12 = hour % 12; if (hr12 == 0) hr12 = 12;
    const char *ampm = (hour < 12) ? "AM" : "PM";

    char buf[48];
    snprintf(buf, sizeof(buf), "%d:%02d %s", hr12, minute, ampm);
    int len = (int)strlen(buf);
    int header_x = (IMG_W - len * 6) / 2;
    if (header_x < 0) header_x = 0;
    draw_text(header_x, 1, buf, IMG_W);
}

/* ── Body animation transform ───────────────────────────────────── */
static void setup_body_transform(uint8_t mood, uint32_t f) {
    body_dx=0; body_dy=0; body_x_expand=0; wobble_amp=0; wobble_freq=0; wobble_phase=0;
    float pi=3.14159f;
    switch (mood) {
        case MOOD_ANGRY: body_dy=-1; body_x_expand=2; wobble_amp=0.5f; wobble_freq=0.3f; wobble_phase=f*pi; break;
        case MOOD_SAD: body_dy=3; body_x_expand=-1; break;
        case MOOD_UNHINGED: body_dx=(int)(1.5f*sinf(f*7.3f)); body_dy=(int)(1.5f*sinf(f*5.1f+1)); break;
        case MOOD_WEIRD: body_dx=(int)(3*sinf(f*0.8f)); wobble_amp=1.5f; wobble_freq=0.15f; wobble_phase=(float)f; break;
        case MOOD_CHAOTIC: body_dx=(int)(2*sinf(f*2.1f)); body_dy=(int)(2*sinf(f*1.7f)); wobble_amp=3; wobble_freq=0.25f; wobble_phase=f*2.0f; break;
        case MOOD_HUNGRY: body_dy=-2+(int)sinf(f*1.5f); break;
        case MOOD_TIRED: body_dy=2+(int)sinf(f*0.5f); body_x_expand=-1; break;
        case MOOD_SLAPHAPPY: body_dx=(int)(3*sinf(f*1.2f)); wobble_amp=2; wobble_freq=0.1f; wobble_phase=f*1.2f; break;
        case MOOD_LAZY: body_dy=3; body_x_expand=3; break;
        case MOOD_FAT: body_x_expand=3; body_dy=(int)sinf(f*1.8f); break;
        case MOOD_CHILL: body_dx=(int)sinf(f*0.4f); body_dy=1; break;
        case MOOD_CREEPY: body_x_expand=(int)(2*sinf(f*2.0f)); break;
        case MOOD_EXCITED: body_dy=(int)(3*sinf(f*3.0f)); break;
        case MOOD_NOSTALGIC: body_dx=(int)(2*sinf(f*0.5f)); body_dy=(int)sinf(f*0.3f); break;
        case MOOD_HOMESICK: body_dy=1; body_x_expand=-2; break;
        default: body_dy=(int)sinf(f*0.8f); break;
    }
}

/* ── Status bar ─────────────────────────────────────────────────── */
static void draw_status_bar(uint8_t mood) {
    char status[32];
    snprintf(status, sizeof(status), "< %s >", mood_names[mood]);
    int sw = (int)strlen(status) * 6;
    int sx = (IMG_W - sw) / 2;
    if (sx < 0) sx = 0;
    draw_text(sx, IMG_H - 8, status, IMG_W);
}

/* ── Mouth animation cycles ─────────────────────────────────────── */
static const uint8_t cycle_normal[]    = {EXPR_SMIRK, EXPR_SMIRK, EXPR_OPEN, EXPR_SMILE};
static const uint8_t cycle_weird[]     = {EXPR_WEIRD, EXPR_WEIRD, EXPR_OPEN, EXPR_WEIRD};
static const uint8_t cycle_unhinged[]  = {EXPR_UNHINGED, EXPR_OPEN, EXPR_UNHINGED, EXPR_OPEN};
static const uint8_t cycle_angry[]     = {EXPR_ANGRY, EXPR_ANGRY, EXPR_OPEN, EXPR_ANGRY};
static const uint8_t cycle_sad[]       = {EXPR_SAD, EXPR_SAD, EXPR_OPEN, EXPR_SAD};
static const uint8_t cycle_chaotic[]   = {EXPR_CHAOTIC, EXPR_OPEN, EXPR_CHAOTIC, EXPR_OPEN};
static const uint8_t cycle_hungry[]    = {EXPR_HUNGRY, EXPR_OPEN, EXPR_HUNGRY, EXPR_HUNGRY};
static const uint8_t cycle_tired[]     = {EXPR_TIRED, EXPR_TIRED, EXPR_TIRED, EXPR_OPEN};
static const uint8_t cycle_slaphappy[] = {EXPR_SLAPHAPPY, EXPR_OPEN, EXPR_SLAPHAPPY, EXPR_SMILE};
static const uint8_t cycle_lazy[]      = {EXPR_LAZY, EXPR_LAZY, EXPR_LAZY, EXPR_OPEN};
static const uint8_t cycle_fat[]       = {EXPR_FAT, EXPR_FAT, EXPR_OPEN, EXPR_SMILE};
static const uint8_t cycle_chill[]     = {EXPR_CHILL, EXPR_CHILL, EXPR_SMILE, EXPR_OPEN};
static const uint8_t cycle_creepy[]    = {EXPR_CREEPY, EXPR_CREEPY, EXPR_OPEN, EXPR_CREEPY};
static const uint8_t cycle_excited[]   = {EXPR_EXCITED, EXPR_OPEN, EXPR_EXCITED, EXPR_SMILE};
static const uint8_t cycle_nostalgic[] = {EXPR_NOSTALGIC, EXPR_NOSTALGIC, EXPR_OPEN, EXPR_SMILE};
static const uint8_t cycle_homesick[]  = {EXPR_HOMESICK, EXPR_HOMESICK, EXPR_SAD, EXPR_OPEN};

static const uint8_t *mood_cycle(uint8_t mood) {
    switch (mood) {
        case MOOD_WEIRD:     return cycle_weird;     case MOOD_UNHINGED:  return cycle_unhinged;
        case MOOD_ANGRY:     return cycle_angry;     case MOOD_SAD:       return cycle_sad;
        case MOOD_CHAOTIC:   return cycle_chaotic;   case MOOD_HUNGRY:    return cycle_hungry;
        case MOOD_TIRED:     return cycle_tired;     case MOOD_SLAPHAPPY: return cycle_slaphappy;
        case MOOD_LAZY:      return cycle_lazy;      case MOOD_FAT:       return cycle_fat;
        case MOOD_CHILL:     return cycle_chill;     case MOOD_CREEPY:    return cycle_creepy;
        case MOOD_EXCITED:   return cycle_excited;   case MOOD_NOSTALGIC: return cycle_nostalgic;
        case MOOD_HOMESICK:  return cycle_homesick;  default:             return cycle_normal;
    }
}

/* ── Frame composition ──────────────────────────────────────────── */

static void render_frame(const Quote *q, int expr, uint32_t frame_idx, uint8_t mood) {
    memset(frame, 0, sizeof(frame));
    draw_clock_header();
    setup_body_transform(mood, frame_idx);
    draw_body_transformed();
    draw_eyes();

    switch (mood) {
        case MOOD_WEIRD:     draw_pupils_weird();     break;  case MOOD_UNHINGED:  draw_pupils_unhinged();  break;
        case MOOD_ANGRY:     draw_pupils_angry();     break;  case MOOD_SAD:       draw_pupils_sad();       break;
        case MOOD_CHAOTIC:   draw_pupils_chaotic();   break;  case MOOD_HUNGRY:    draw_pupils_hungry();    break;
        case MOOD_TIRED:     draw_pupils_tired();     break;  case MOOD_LAZY:      draw_pupils_lazy();      break;
        case MOOD_FAT:       draw_pupils_fat();       break;  case MOOD_CHILL:     draw_pupils_chill();     break;
        case MOOD_CREEPY:    draw_pupils_creepy();    break;  case MOOD_EXCITED:   draw_pupils_excited();   break;
        case MOOD_NOSTALGIC: draw_pupils_nostalgic(); break;  case MOOD_HOMESICK:  draw_pupils_homesick();  break;
        default:             draw_pupils_normal();    break;
    }

    if (mood == MOOD_ANGRY)     draw_brows_angry();
    if (mood == MOOD_SAD)       draw_brows_sad();
    if (mood == MOOD_TIRED)     draw_lids_tired();
    if (mood == MOOD_SLAPHAPPY) draw_eyes_slaphappy();
    if (mood == MOOD_LAZY)      draw_lids_lazy();
    if (mood == MOOD_HOMESICK)  draw_tears_homesick();

    switch (expr) {
        case EXPR_OPEN:      draw_mouth_open();      break;  case EXPR_SMILE:     draw_mouth_smile();     break;
        case EXPR_WEIRD:     draw_mouth_weird();     break;  case EXPR_UNHINGED:  draw_mouth_unhinged();  break;
        case EXPR_ANGRY:     draw_mouth_angry();     break;  case EXPR_SAD:       draw_mouth_sad();       break;
        case EXPR_CHAOTIC:   draw_mouth_chaotic();   break;  case EXPR_HUNGRY:    draw_mouth_hungry();    break;
        case EXPR_TIRED:     draw_mouth_tired();     break;  case EXPR_SLAPHAPPY: draw_mouth_slaphappy(); break;
        case EXPR_LAZY:      draw_mouth_lazy();      break;  case EXPR_FAT:       draw_mouth_fat();       break;
        case EXPR_CHILL:     draw_mouth_chill();     break;  case EXPR_CREEPY:    draw_mouth_creepy();    break;
        case EXPR_EXCITED:   draw_mouth_excited();   break;  case EXPR_NOSTALGIC: draw_mouth_nostalgic(); break;
        case EXPR_HOMESICK:  draw_mouth_homesick();  break;  default:             draw_mouth_smirk();     break;
    }

    draw_bubble();
    draw_text(81, 11 + Y_OFF, q->text, 158);
    draw_status_bar(mood);
}

/* ══════════════════════════════════════════════════════════════════
 *  ESP32-SPECIFIC: Display push, PRNG, input, main loop
 * ══════════════════════════════════════════════════════════════════ */

/* ── PRNG (ESP32 hardware RNG) ──────────────────────────────────── */
static uint32_t rng_state;
static void rng_seed(void) { rng_state = esp_random(); }
static uint32_t rng_next(void) { rng_state ^= rng_state << 13; rng_state ^= rng_state >> 17; rng_state ^= rng_state << 5; return rng_state; }

/* ── Quote filtering ────────────────────────────────────────────── */
static int pick_quote_for_mood(uint8_t mood) {
    int candidates[QUOTE_COUNT];
    int count = 0;
    for (int i = 0; i < QUOTE_COUNT; i++)
        if (quotes[i].mood == mood)
            candidates[count++] = i;
    if (count == 0) return rng_next() % QUOTE_COUNT;
    return candidates[rng_next() % count];
}

/* ── Display push (GxEPD2) ──────────────────────────────────────── */

static bool first_frame = true;

static void push_frame_to_display(void) {
    /*
     * Our framebuffer: landscape 250x122, MSB-first, 1 = black pixel.
     * GxEPD2 drawBitmap(): same bit ordering (Adafruit_GFX standard).
     * We set rotation(1) = landscape, so coordinates map directly.
     */
    if (first_frame) {
        display.setFullWindow();
        first_frame = false;
    } else {
        display.setPartialWindow(0, 0, display.width(), display.height());
    }

    display.firstPage();
    do {
        display.fillScreen(GxEPD_WHITE);
        display.drawBitmap(0, 0, frame, IMG_W, IMG_H, GxEPD_BLACK);
    } while (display.nextPage());
}

/* ── Setup ──────────────────────────────────────────────────────── */

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n=== Dilder ESP32-S3 — Mood Selector ===");
    Serial.printf("Board: %s  |  %d quotes\n", BOARD_NAME, QUOTE_COUNT);

    dilder_hal_init();

    SPI.begin(PIN_EPD_CLK, -1, PIN_EPD_DIN, PIN_EPD_CS);
    display.init(115200, true, 2, false);
    display.setRotation(1);

    rng_seed();

    Serial.println("Controls:");
    Serial.println("  Joystick LEFT/RIGHT = cycle moods");
    Serial.println("  Joystick CENTER     = random mood");
    Serial.println("  Joystick UP         = new quote");
    Serial.println("  Serial: [/] = navigate, r = random, ? = help");
    Serial.println("Ready.\n");
}

/* ── Main loop ──────────────────────────────────────────────────── */

static uint8_t current_mood = MOOD_NORMAL;
static uint32_t frame_idx = 0;
static int qi = -1;
static bool mood_changed = true;

/* Joystick edge detection */
static bool last_left = false, last_right = false, last_center = false,
            last_up = false, last_down = false;

void loop() {
    if (qi < 0) qi = pick_quote_for_mood(current_mood);

    const uint8_t *cycle = mood_cycle(current_mood);
    uint8_t expr = cycle[frame_idx % 4];

    if (mood_changed || (expr == EXPR_OPEN && frame_idx > 0)) {
        qi = pick_quote_for_mood(current_mood);
        mood_changed = false;
    }

    /* Render + push */
    render_frame(&quotes[qi], expr, frame_idx, current_mood);
    push_frame_to_display();

    Serial.printf("Frame %lu | < %s > (%d/%d) | \"%s\"\n",
                  (unsigned long)frame_idx, mood_names[current_mood],
                  current_mood + 1, MOOD_COUNT, quotes[qi].text);
    frame_idx++;

    /* Poll joystick + serial for 4 seconds between frames */
    unsigned long deadline = millis() + 4000;
    while (millis() < deadline) {
        bool left   = hal_btn_left();
        bool right  = hal_btn_right();
        bool center = hal_btn_center();
        bool up     = hal_btn_up();
        bool down   = hal_btn_down();

        uint8_t prev = current_mood;
        bool input_received = false;

        /* Joystick: LEFT = previous mood */
        if (left && !last_left) {
            current_mood = (current_mood == 0) ? MOOD_COUNT - 1 : current_mood - 1;
            input_received = true;
        }
        /* Joystick: RIGHT = next mood */
        if (right && !last_right) {
            current_mood = (current_mood + 1) % MOOD_COUNT;
            input_received = true;
        }
        /* Joystick: CENTER = random mood */
        if (center && !last_center) {
            current_mood = rng_next() % MOOD_COUNT;
            input_received = true;
        }
        /* Joystick: UP = new quote (same mood) */
        if (up && !last_up) {
            qi = pick_quote_for_mood(current_mood);
            mood_changed = true;
            input_received = true;
        }

        last_left = left; last_right = right; last_center = center;
        last_up = up; last_down = down;

        /* Serial input (same keys as Pico) */
        while (Serial.available()) {
            int ch = Serial.read();
            switch (ch) {
                case '[': case ',': current_mood = (current_mood == 0) ? MOOD_COUNT - 1 : current_mood - 1; input_received = true; break;
                case ']': case '.': current_mood = (current_mood + 1) % MOOD_COUNT; input_received = true; break;
                case 'r': case 'R': current_mood = rng_next() % MOOD_COUNT; input_received = true; break;
                case 'n': case 'N': current_mood = MOOD_NORMAL;    input_received = true; break;
                case 'w': case 'W': current_mood = MOOD_WEIRD;     input_received = true; break;
                case 'u': case 'U': current_mood = MOOD_UNHINGED;  input_received = true; break;
                case 'a': case 'A': current_mood = MOOD_ANGRY;     input_received = true; break;
                case 's': case 'S': current_mood = MOOD_SAD;       input_received = true; break;
                case 'c': case 'C': current_mood = MOOD_CHAOTIC;   input_received = true; break;
                case 'h': case 'H': current_mood = MOOD_HUNGRY;    input_received = true; break;
                case 't': case 'T': current_mood = MOOD_TIRED;     input_received = true; break;
                case 'p': case 'P': current_mood = MOOD_SLAPHAPPY; input_received = true; break;
                case 'l': case 'L': current_mood = MOOD_LAZY;      input_received = true; break;
                case 'f': case 'F': current_mood = MOOD_FAT;       input_received = true; break;
                case 'k': case 'K': current_mood = MOOD_CHILL;     input_received = true; break;
                case 'y': case 'Y': current_mood = MOOD_CREEPY;    input_received = true; break;
                case 'e': case 'E': current_mood = MOOD_EXCITED;   input_received = true; break;
                case 'o': case 'O': current_mood = MOOD_NOSTALGIC; input_received = true; break;
                case 'm': case 'M': current_mood = MOOD_HOMESICK;  input_received = true; break;
                case 'q': case 'Q': qi = pick_quote_for_mood(current_mood); mood_changed = true; input_received = true; break;
            }
        }

        if (current_mood != prev) {
            mood_changed = true;
            Serial.printf(">> Mood changed: %s --> %s\n", mood_names[prev], mood_names[current_mood]);
        }

        if (input_received) break;
        delay(50);
    }
}
