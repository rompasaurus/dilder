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
#include <time.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "hardware/pwm.h"
#include "hardware/adc.h"
#include "hardware/i2c.h"
#include "lwip/dns.h"
#include "lwip/pbuf.h"
#include "lwip/udp.h"
#include "rtc_compat.h"
#include "DEV_Config.h"
#include "version.h"
#include "wifi_config.h"

/* ─── Joystick pins ─── */
#define JOY_LEFT   2
#define JOY_DOWN   3
#define JOY_UP     4
#define JOY_RIGHT  5
#define JOY_CENTER 6

/* ─── Speaker (active buzzer on GP14) ─── */
/* Wire: buzzer (+) → pin 19 (GP14), buzzer (-) → GND (pin 18). */
#define BUZZER_PIN 14  /* GP14 = pin 19 — active buzzer (+) */

static bool sound_enabled = true;
static uint8_t sound_vol = 2;  /* 0=short, 1=med, 2=long beep duration */
static const uint16_t vol_durations[] = {20, 50, 100};  /* ms per level */

static void speaker_init(void) {
    gpio_init(BUZZER_PIN);
    gpio_set_dir(BUZZER_PIN, GPIO_OUT);
    gpio_put(BUZZER_PIN, 0);
}

static void speaker_tone(uint16_t freq_hz, uint16_t duration_ms) {
    if (!sound_enabled || freq_hz == 0) { sleep_ms(duration_ms); return; }
    uint16_t actual = duration_ms < vol_durations[sound_vol] ? duration_ms : vol_durations[sound_vol];
    gpio_put(BUZZER_PIN, 1);
    sleep_ms(actual);
    gpio_put(BUZZER_PIN, 0);
    if (duration_ms > actual) sleep_ms(duration_ms - actual);
}

/* ─── Sound patterns (on_ms, off_ms pairs; 0 terminates) ─── */
static const uint16_t pat_beep[]     = {150, 0};
static const uint16_t pat_chirp[]    = {30,30, 30,30, 30,30, 30,30, 30, 0};
static const uint16_t pat_sos[]      = {60,60, 60,60, 60,180, 180,60, 180,60, 180,180, 60,60, 60,60, 60, 0};
static const uint16_t pat_doorbell[] = {200, 100, 300, 0};
static const uint16_t pat_alert[]    = {300,200, 300,200, 300, 0};
static const uint16_t pat_happy[]    = {40,60, 40,60, 40,60, 200,100, 50,50, 50,50, 300, 0};

#define SOUND_PATTERN_COUNT 6
static const char *pattern_names[] = {"BEEP", "CHIRP", "SOS", "DOORBELL", "ALERT", "HAPPY"};
static const uint16_t *patterns[]  = {pat_beep, pat_chirp, pat_sos, pat_doorbell, pat_alert, pat_happy};
static int current_pattern = 0;

static void play_sound_pattern(int idx) {
    if (!sound_enabled || idx < 0 || idx >= SOUND_PATTERN_COUNT) return;
    const uint16_t *p = patterns[idx];
    while (*p) {
        uint16_t on_ms = *p++;
        uint16_t actual = on_ms < vol_durations[sound_vol] ? on_ms : vol_durations[sound_vol];
        gpio_put(BUZZER_PIN, 1);
        sleep_ms(actual);
        gpio_put(BUZZER_PIN, 0);
        if (on_ms > actual) sleep_ms(on_ms - actual);
        if (*p) { sleep_ms(*p); p++; }
    }
}

/* ─── Joystick init ─── */
static void joystick_init(void) {
    const uint pins[] = {JOY_UP, JOY_DOWN, JOY_LEFT, JOY_RIGHT, JOY_CENTER};
    for (int i = 0; i < 5; i++) {
        gpio_init(pins[i]);
        gpio_set_dir(pins[i], GPIO_IN);
        gpio_pull_up(pins[i]);
    }
}

/* ─── Joystick read (returns single direction or 0) ─── */
#define INPUT_NONE   0
#define INPUT_UP     1
#define INPUT_DOWN   2
#define INPUT_LEFT   3
#define INPUT_RIGHT  4
#define INPUT_CENTER 5

static uint8_t read_joystick(void) {
    if (!gpio_get(JOY_UP))     return INPUT_UP;
    if (!gpio_get(JOY_DOWN))   return INPUT_DOWN;
    if (!gpio_get(JOY_LEFT))   return INPUT_LEFT;
    if (!gpio_get(JOY_RIGHT))  return INPUT_RIGHT;
    if (!gpio_get(JOY_CENTER)) return INPUT_CENTER;
    return INPUT_NONE;
}

/* ─── App states ─── */
#define STATE_OCTOPUS     0   /* main screen — octopus + quote + clock */
#define STATE_MENU        1   /* menu overlay */
#define STATE_SOUND       2   /* sound test sub-screen */
#define STATE_INFO        3   /* device info sub-screen */
#define STATE_MOOD_SELECT 4   /* mood picker */
#define STATE_NETWORK     5   /* WiFi status (read-only) */
#define STATE_NET_MENU    6   /* Network submenu */
#define STATE_NET_SCAN    7   /* Scan results list */
#define STATE_NET_KEYBOARD 8  /* On-screen keyboard for WiFi password */
#define STATE_MOTION       9  /* Accelerometer / pedometer menu */

/* ─── WiFi state ─── */
static bool wifi_enabled = false;
static bool wifi_connected = false;
static bool ntp_synced = false;
static int32_t wifi_rssi = 0;
static char wifi_ssid_display[33] = "---";
static char wifi_ip_str[20] = "---";

/* ─── WiFi scan state ─── */
#define MAX_SCAN_RESULTS 16
typedef struct { char ssid[33]; int8_t rssi; uint8_t auth_mode; } scan_entry_t;
static scan_entry_t scan_results[MAX_SCAN_RESULTS];
static int  scan_count = 0;
static int  scan_sel = 0;
static bool scan_in_progress = false;
static bool scan_complete = false;

/* ─── On-screen keyboard state ─── */
#define PW_MAX_LEN 63
static char pw_buf[PW_MAX_LEN + 1];
static int  pw_len = 0;
static int  kb_row = 0;
static int  kb_col = 0;
static bool kb_shift = true;   /* start in CAPS mode */
static int  selected_network = -1;

static const char kb_grid[4][10] = {
    {'Q','W','E','R','T','Y','U','I','O','P'},
    {'A','S','D','F','G','H','J','K','L','.'},
    {'Z','X','C','V','B','N','M','-','!','?'},
    {'0','1','2','3','4','5','6','7','8','9'},
};
#define KB_CHAR_ROWS 4
#define KB_SPECIAL_ROW 4
#define KB_SP_SHIFT  0
#define KB_SP_SPACE  1
#define KB_SP_DEL    2
#define KB_SP_DONE   3
#define KB_SP_CANCEL 4
#define KB_SP_COUNT  5

static char kb_char_at(int row, int col, bool shift) {
    if (row >= KB_CHAR_ROWS) return '\0';
    char c = kb_grid[row][col];
    if (!shift && c >= 'A' && c <= 'Z') return c + 32;
    return c;
}

/* ─── MPU-6050 accelerometer/gyro (I2C0 on GP0/GP1) ─── */
#define MPU_I2C    i2c0
static uint8_t mpu_addr = 0x68;  /* auto-detected in mpu_init */
#define MPU_SDA    0   /* GP0 = pin 1 */
#define MPU_SCL    1   /* GP1 = pin 2 */

/* Registers */
#define MPU_PWR_MGMT_1   0x6B
#define MPU_WHO_AM_I     0x75
#define MPU_ACCEL_XOUT_H 0x3B
#define MPU_GYRO_XOUT_H  0x43
#define MPU_TEMP_OUT_H   0x41
#define MPU_ACCEL_CONFIG  0x1C
#define MPU_GYRO_CONFIG   0x1B

static bool mpu_ok = false;

/* Raw sensor data */
static int16_t accel_x, accel_y, accel_z;
static int16_t gyro_x, gyro_y, gyro_z;
static float   mpu_temp_c;

/* Pedometer state */
static uint32_t step_count = 0;
static float    step_threshold = 1.3f;  /* g — adjustable */
static bool     step_above = false;     /* debounce: was last sample above threshold? */

static bool mpu_write_reg(uint8_t reg, uint8_t val) {
    uint8_t buf[2] = {reg, val};
    return i2c_write_blocking(MPU_I2C, mpu_addr, buf, 2, false) == 2;
}

static int mpu_read_reg(uint8_t reg) {
    uint8_t val;
    if (i2c_write_blocking(MPU_I2C, mpu_addr, &reg, 1, true) < 0) return -1;
    if (i2c_read_blocking(MPU_I2C, mpu_addr, &val, 1, false) < 0) return -1;
    return val;
}

static bool mpu_read_burst(uint8_t reg, uint8_t *dst, uint8_t len) {
    if (i2c_write_blocking(MPU_I2C, mpu_addr, &reg, 1, true) < 0) return false;
    return i2c_read_blocking(MPU_I2C, mpu_addr, dst, len, false) == len;
}

static void mpu_init(void) {
    i2c_init(MPU_I2C, 400 * 1000);  /* 400 kHz */
    gpio_set_function(MPU_SDA, GPIO_FUNC_I2C);
    gpio_set_function(MPU_SCL, GPIO_FUNC_I2C);
    gpio_pull_up(MPU_SDA);
    gpio_pull_up(MPU_SCL);
    sleep_ms(100);  /* Let MPU boot */

    /* Try both possible addresses */
    uint8_t try_addrs[] = {0x68, 0x69};
    bool found = false;
    for (int a = 0; a < 2; a++) {
        uint8_t addr = try_addrs[a];
        uint8_t reg = MPU_WHO_AM_I;
        uint8_t who = 0;
        int w = i2c_write_blocking(MPU_I2C, addr, &reg, 1, true);
        int r = i2c_read_blocking(MPU_I2C, addr, &who, 1, false);
        printf("[MPU] Probe 0x%02X: w=%d r=%d who=0x%02X\n", addr, w, r, who);
        if (w >= 0 && r >= 0) {
            mpu_addr = addr;
            found = true;
            printf("[MPU] Using address 0x%02X\n", addr);
            break;
        }
    }

    if (!found) {
        printf("[MPU] NOT DETECTED on I2C0\n");
        mpu_ok = false;
        return;
    }

    mpu_write_reg(MPU_PWR_MGMT_1, 0x00);  /* Wake up (clear sleep bit) */
    sleep_ms(100);
    mpu_write_reg(MPU_ACCEL_CONFIG, 0x00); /* +/- 2g */
    mpu_write_reg(MPU_GYRO_CONFIG, 0x00);  /* +/- 250 deg/s */
    mpu_ok = true;
    printf("[MPU] MPU-6050 initialized OK at 0x%02X\n", mpu_addr);
}

static void mpu_read_all(void) {
    if (!mpu_ok) return;

    /* Burst read accel (6 bytes) + temp (2 bytes) + gyro (6 bytes) = 14 bytes from 0x3B */
    uint8_t buf[14];
    mpu_read_burst(MPU_ACCEL_XOUT_H, buf, 14);

    accel_x = (int16_t)((buf[0] << 8) | buf[1]);
    accel_y = (int16_t)((buf[2] << 8) | buf[3]);
    accel_z = (int16_t)((buf[4] << 8) | buf[5]);

    int16_t temp_raw = (int16_t)((buf[6] << 8) | buf[7]);
    mpu_temp_c = temp_raw / 340.0f + 36.53f;

    gyro_x = (int16_t)((buf[8]  << 8) | buf[9]);
    gyro_y = (int16_t)((buf[10] << 8) | buf[11]);
    gyro_z = (int16_t)((buf[12] << 8) | buf[13]);
}

/* Convert raw accel to g (at +/-2g range, 16384 LSB/g) */
static float accel_g(int16_t raw) { return raw / 16384.0f; }

/* Convert raw gyro to deg/s (at +/-250, 131 LSB/(deg/s)) */
static float gyro_dps(int16_t raw) { return raw / 131.0f; }

/* Magnitude of acceleration vector in g */
static float accel_magnitude(void) {
    float ax = accel_g(accel_x);
    float ay = accel_g(accel_y);
    float az = accel_g(accel_z);
    return sqrtf(ax * ax + ay * ay + az * az);
}

/* Tilt angles in degrees */
static float tilt_x_deg(void) {
    return atan2f(accel_g(accel_x), sqrtf(accel_g(accel_y) * accel_g(accel_y) + accel_g(accel_z) * accel_g(accel_z))) * 57.2958f;
}
static float tilt_y_deg(void) {
    return atan2f(accel_g(accel_y), sqrtf(accel_g(accel_x) * accel_g(accel_x) + accel_g(accel_z) * accel_g(accel_z))) * 57.2958f;
}

/* Simple pedometer: detect step when magnitude crosses threshold going up then back down */
static void pedometer_update(void) {
    float mag = accel_magnitude();
    if (!step_above && mag > step_threshold) {
        step_above = true;
        step_count++;
    } else if (step_above && mag < (step_threshold - 0.3f)) {
        step_above = false;
    }
}

/* ─── NTP ─── */
#define NTP_PORT 123
#define NTP_MSG_LEN 48
#define NTP_DELTA 2208988800ULL

static struct udp_pcb *ntp_pcb = NULL;
static ip_addr_t ntp_server_addr;
static volatile bool ntp_time_received = false;

/* ─── Mood names for the selector ─── */
static const char *mood_names[] = {
    "NORMAL", "WEIRD", "UNHINGED", "ANGRY",
    "SAD", "CHAOTIC", "HUNGRY", "TIRED",
    "SLAP HAPPY", "LAZY", "FAT", "CHILL",
    "CREEPY", "EXCITED", "NOSTALGIC", "HOMESICK",
};
#define MOOD_COUNT 16
static int current_mood = -1;  /* -1 = all moods (random) */

/* Display variant selection */
#if defined(DISPLAY_V2)
  #include "EPD_2in13_V2.h"
  #define DISP_W EPD_2in13_V2_WIDTH
  #define DISP_H EPD_2in13_V2_HEIGHT
  #define EPD_Init()     EPD_2in13_V2_Init()
  #define EPD_Clear()    EPD_2in13_V2_Clear()
  #define EPD_Display(b) EPD_2in13_V2_Display(b)
  #define EPD_Base(b)    EPD_2in13_V2_Display(b)
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
  #define EPD_Base(b)    EPD_2in13_V3a_Display_Base(b)
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
  #define EPD_Base(b)    EPD_2in13_V4_Display_Base(b)
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
  #define EPD_Base(b)    EPD_2in13_V3_Display_Base(b)
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
            body_x_expand = 3; body_dy = (int)sinf(f * 1.8f);
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

    /* 7. Tagline — show current mood/emotion name */
    int tag_y = 5 + 70 + 5 + Y_OFF;
    if (tag_y + 7 < IMG_H) {
        char mood_tag[40];
        snprintf(mood_tag, sizeof(mood_tag), "- %s -",
                 current_mood < 0 ? mood_names[q->mood] : mood_names[current_mood]);
        /* Uppercase it */
        for (char *p = mood_tag; *p; p++)
            if (*p >= 'a' && *p <= 'z') *p -= 32;
        draw_text(81, tag_y, mood_tag, 170);
    }
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

/* ─── Battery / power monitoring ─── */
/* On Pico W / Pico 2 W:
 *   - VSYS/3 sits on GPIO 29 / ADC3, but GPIO 29 is shared with the CYW43
 *     SPI bus, so we average many samples to fight the SPI-induced noise.
 *   - USB presence is detected via CYW43_WL_GPIO_VBUS_PIN (CYW43 GPIO 2)
 *     when the wireless stack has been brought up; otherwise we fall back
 *     to a VSYS threshold. */
static bool battery_adc_ready = false;

static void battery_init(void) {
    adc_gpio_init(29);          /* disable digital pulls on ADC3 */
    battery_adc_ready = true;
}

static float read_vsys_volts(void) {
    if (!battery_adc_ready) battery_init();

    /* GPIO 29 is shared with CYW43 SPI — lock it out while we read */
    cyw43_thread_enter();

    adc_gpio_init(29);              /* reclaim pin as ADC input */
    adc_select_input(3);            /* ADC3 = GP29 = VSYS/3 */
    uint32_t acc = 0;
    const int N = 32;
    for (int i = 0; i < N; i++) acc += adc_read();

    cyw43_thread_exit();

    float raw = (float)acc / (float)N;
    return raw * 3.3f / 4095.0f * 3.0f;   /* 3:1 divider */
}

static bool is_usb_powered(void) {
    /* CYW43 is always initialised at boot — VBUS sense is reliable */
    return cyw43_arch_gpio_get(CYW43_WL_GPIO_VBUS_PIN);
}

/* Returns 0..100 from VSYS, or -1 if running on USB. */
static int read_battery_percent(void) {
    if (is_usb_powered()) return -1;
    float vsys = read_vsys_volts();
    if (vsys >= 4.2f) return 100;
    if (vsys <= 3.0f) return 0;
    return (int)((vsys - 3.0f) / 1.2f * 100.0f);
}

/* ─── Battery icon (16x10 pixels) ─── */
static void draw_battery_icon(int x0, int y0) {
    int pct = read_battery_percent();

    /* Battery outline: 14x8 rectangle + 2x4 terminal nub */
    for (int x = x0; x < x0 + 14; x++) { px_set(x, y0); px_set(x, y0 + 7); }
    for (int y = y0; y < y0 + 8; y++) { px_set(x0, y); px_set(x0 + 13, y); }
    /* Terminal nub on right */
    for (int y = y0 + 2; y < y0 + 6; y++) { px_set(x0 + 14, y); px_set(x0 + 15, y); }

    if (pct < 0) {
        /* USB powered — lightning bolt inside battery */
        px_set(x0 + 8, y0 + 1); px_set(x0 + 7, y0 + 2);
        px_set(x0 + 6, y0 + 2); px_set(x0 + 6, y0 + 3);
        px_set(x0 + 5, y0 + 3); px_set(x0 + 4, y0 + 3);
        px_set(x0 + 5, y0 + 3); px_set(x0 + 9, y0 + 3);
        px_set(x0 + 8, y0 + 3); px_set(x0 + 7, y0 + 3);
        px_set(x0 + 8, y0 + 4); px_set(x0 + 9, y0 + 4);
        px_set(x0 + 7, y0 + 5); px_set(x0 + 8, y0 + 5);
        px_set(x0 + 6, y0 + 6); px_set(x0 + 5, y0 + 6);
    } else {
        /* Fill bars based on percentage (4 bars max) */
        int bars = (pct + 12) / 25;  /* 0-4 bars */
        for (int b = 0; b < bars && b < 4; b++) {
            int bx = x0 + 2 + b * 3;
            for (int y = y0 + 2; y < y0 + 6; y++)
                for (int x = bx; x < bx + 2; x++)
                    px_set(x, y);
        }
    }
}

/* ─── WiFi icon (16x12 pixels) ─── */
static void draw_wifi_icon(int x0, int y0, bool connected) {
    for (int i = -6; i <= 6; i++) {
        int ay = y0 + 1;
        if (i >= -5 && i <= 5) ay = y0;
        if (i >= -3 && i <= 3) ay = y0 - 1;
        px_set(x0 + 8 + i, ay);
    }
    for (int i = -4; i <= 4; i++) {
        int ay = y0 + 4;
        if (i >= -3 && i <= 3) ay = y0 + 3;
        if (i >= -1 && i <= 1) ay = y0 + 2;
        px_set(x0 + 8 + i, ay);
    }
    for (int i = -2; i <= 2; i++) {
        int ay = y0 + 6;
        if (i >= -1 && i <= 1) ay = y0 + 5;
        px_set(x0 + 8 + i, ay);
    }
    px_set(x0 + 7, y0 + 8); px_set(x0 + 8, y0 + 8);
    px_set(x0 + 9, y0 + 8); px_set(x0 + 8, y0 + 9);
    if (!connected) {
        for (int i = 0; i < 11; i++) {
            px_set(x0 + 2 + i, y0 + i);
            px_set(x0 + 3 + i, y0 + i);
        }
    }
}

/* ─── Menu items ─── */
static const char *menu_items[] = {
    "MOOD SELECT",
    "NETWORK",
    "SOUND",
    "MOTION",
    "DEVICE INFO",
    "BACK",
};
#define MENU_COUNT 6

/* ─── Helper: draw inverted text (white on black bar) ─── */
static void draw_inverted_line(int y, const char *text) {
    for (int hy = y - 1; hy < y + 8; hy++)
        for (int hx = 6; hx < 244; hx++)
            px_set(hx, hy);
    int cx = 10;
    for (const char *c = text; *c; c++) {
        char up = *c;
        if (up >= 'a' && up <= 'z') up -= 32;
        const char *pos = strchr(font_chars, up);
        if (pos) {
            int idx = (int)(pos - font_chars);
            for (int row = 0; row < 7; row++) {
                uint8_t bits = font5x7[idx][row];
                for (int col = 0; col < 5; col++)
                    if (bits & (0x10 >> col))
                        px_clr(cx + col, y + row);
            }
        }
        cx += 6;
    }
}

/* ─── Draw menu overlay ─── */
static void render_menu(int selected) {
    /* Clear bottom half of screen for menu overlay */
    for (int y = 72; y < IMG_H; y++)
        for (int x = 0; x < IMG_ROW_BYTES; x++)
            frame[y * IMG_ROW_BYTES + x] = 0;

    for (int x = 5; x < 245; x++) px_set(x, 73);
    draw_text(8, 75, "MENU", IMG_W);

    /* 6 items — scroll if needed */
    int m_vis = 5;
    int m_start = 0;
    if (selected > m_vis - 2) m_start = selected - (m_vis - 2);
    if (m_start + m_vis > MENU_COUNT) m_start = MENU_COUNT - m_vis;
    if (m_start < 0) m_start = 0;
    for (int i = 0; i < m_vis && (m_start + i) < MENU_COUNT; i++) {
        int idx = m_start + i;
        int y = 84 + i * 8;
        char line[40];
        if (idx == selected) {
            snprintf(line, sizeof(line), "> %s", menu_items[idx]);
            draw_inverted_line(y, line);
        } else {
            snprintf(line, sizeof(line), "  %s", menu_items[idx]);
            draw_text(10, y, line, IMG_W);
        }
    }
}

/* ─── Draw sound submenu ─── */
#define SND_ITEM_PATTERN 0
#define SND_ITEM_ONOFF   1
#define SND_ITEM_VOL     2
#define SND_ITEM_BACK    3
#define SND_MENU_COUNT   4

static const char *vol_labels[] = {"LOW", "MED", "HIGH"};

static void render_sound_menu(int sel) {
    memset(frame, 0, sizeof(frame));
    draw_text(30, 3, "SOUND", IMG_W);
    for (int x = 10; x < 240; x++) px_set(x, 14);

    char buf[40];
    const char *items[SND_MENU_COUNT];
    static char pattern_buf[30];
    snprintf(pattern_buf, sizeof(pattern_buf), "TONE: %s", pattern_names[current_pattern]);
    items[SND_ITEM_PATTERN] = pattern_buf;
    static char onoff_buf[20];
    snprintf(onoff_buf, sizeof(onoff_buf), "SOUND: %s", sound_enabled ? "ON" : "OFF");
    items[SND_ITEM_ONOFF] = onoff_buf;
    static char vol_buf[20];
    snprintf(vol_buf, sizeof(vol_buf), "VOLUME: %s", vol_labels[sound_vol]);
    items[SND_ITEM_VOL] = vol_buf;
    items[SND_ITEM_BACK] = "BACK";

    for (int i = 0; i < SND_MENU_COUNT; i++) {
        int y = 22 + i * 12;
        if (i == sel) {
            snprintf(buf, sizeof(buf), "> %s", items[i]);
            draw_inverted_line(y, buf);
        } else {
            snprintf(buf, sizeof(buf), "  %s", items[i]);
            draw_text(10, y, buf, IMG_W);
        }
    }

    draw_text(10, 96, "C:PLAY  L/R:CHANGE TONE", IMG_W);
    draw_text(155, 108, "LEFT:BACK", IMG_W);
}

/* ─── Draw device info screen ─── */
static void render_info_screen(void) {
    memset(frame, 0, sizeof(frame));
    draw_text(30, 3, "DEVICE INFO", IMG_W);
    for (int x = 10; x < 240; x++) px_set(x, 14);
    char buf[48];
    int y = 20;

    snprintf(buf, sizeof(buf), "FW: V%s  %s", DILDER_VERSION, DISPLAY_NAME);
    draw_text(10, y, buf, IMG_W); y += 11;

    snprintf(buf, sizeof(buf), "BUILT: %s %s", __DATE__, __TIME__);
    draw_text(10, y, buf, IMG_W); y += 11;

    datetime_t t; rtc_get_datetime(&t);
    int hr12 = t.hour % 12; if (hr12 == 0) hr12 = 12;
    snprintf(buf, sizeof(buf), "%s %d, %d  %d:%02d %s",
             month_names[t.month - 1], t.day, t.year, hr12, t.min,
             t.hour < 12 ? "AM" : "PM");
    draw_text(10, y, buf, IMG_W); y += 11;

    snprintf(buf, sizeof(buf), "MOOD: %s  QUOTES: %d",
             current_mood < 0 ? "ALL" : mood_names[current_mood], QUOTE_COUNT);
    draw_text(10, y, buf, IMG_W); y += 11;

    snprintf(buf, sizeof(buf), "WIFI: %s", wifi_connected ? wifi_ip_str : "OFF");
    draw_text(10, y, buf, IMG_W); y += 11;

    /* Battery / power status */
    int pct = read_battery_percent();
    float vsys = read_vsys_volts();
    if (pct < 0) {
        snprintf(buf, sizeof(buf), "POWER: USB (%.1fV)", (double)vsys);
    } else {
        snprintf(buf, sizeof(buf), "BATTERY: %d%% (%.1fV)", pct, (double)vsys);
    }
    draw_text(10, y, buf, IMG_W); y += 11;

    draw_text(10, 110, "PICO 2 W  RP2350", IMG_W);
    draw_text(175, 110, "LEFT:BACK", IMG_W);
}

/* ─── Draw mood select screen ─── */
static void render_mood_select(int selected) {
    memset(frame, 0, sizeof(frame));
    draw_text(30, 3, "SELECT MOOD", IMG_W);
    for (int x = 10; x < 240; x++) px_set(x, 14);

    /* Show 8 moods at a time (scrolling window) */
    int start = 0;
    /* +1 for "ALL (RANDOM)" option */
    int total = MOOD_COUNT + 1;
    if (selected > 6) start = selected - 6;
    if (start + 8 > total) start = total - 8;
    if (start < 0) start = 0;

    for (int i = 0; i < 8 && (start + i) < total; i++) {
        int idx = start + i;
        int y = 20 + i * 11;
        char line[40];
        if (idx == 0) {
            snprintf(line, sizeof(line), idx == selected ? "> ALL MOODS (RANDOM)" : "  ALL MOODS (RANDOM)");
        } else {
            int mood_idx = idx - 1;
            snprintf(line, sizeof(line), idx == selected ? "> %s" : "  %s", mood_names[mood_idx]);
        }
        if (idx == selected)
            draw_inverted_line(y, line);
        else
            draw_text(10, y, line, IMG_W);
    }

    char hint[40];
    snprintf(hint, sizeof(hint), "CURRENT: %s",
             current_mood < 0 ? "ALL" : mood_names[current_mood]);
    draw_text(10, 110, hint, IMG_W);
    draw_text(175, 110, "LEFT:BACK", IMG_W);
}

/* ─── Draw network status screen (read-only) ─── */
static void render_network_screen(void) {
    memset(frame, 0, sizeof(frame));
    draw_text(30, 3, "WIFI STATUS", IMG_W);
    for (int x = 10; x < 240; x++) px_set(x, 14);
    char buf[48];

    snprintf(buf, sizeof(buf), "WIFI: %s", wifi_enabled ? "ON" : "OFF");
    draw_text(10, 22, buf, IMG_W);

    snprintf(buf, sizeof(buf), "SSID: %s", wifi_ssid_display);
    draw_text(10, 35, buf, IMG_W);

    snprintf(buf, sizeof(buf), "STATUS: %s",
             !wifi_enabled ? "DISABLED" :
             wifi_connected ? "CONNECTED" : "DISCONNECTED");
    draw_text(10, 48, buf, IMG_W);

    snprintf(buf, sizeof(buf), "IP: %s", wifi_connected ? wifi_ip_str : "---");
    draw_text(10, 61, buf, IMG_W);

    if (wifi_connected) {
        snprintf(buf, sizeof(buf), "SIGNAL: %d DBM", (int)wifi_rssi);
        draw_text(10, 74, buf, IMG_W);
    }

    snprintf(buf, sizeof(buf), "NTP: %s", ntp_synced ? "SYNCED" : "NOT SYNCED");
    draw_text(10, 87, buf, IMG_W);

    draw_text(175, 110, "LEFT:BACK", IMG_W);
}

/* ─── Draw network submenu ─── */
#define NET_ITEM_ONOFF      0
#define NET_ITEM_SCAN       1
#define NET_ITEM_STATUS     2
#define NET_ITEM_BACK       3
#define NET_MENU_COUNT      4

static void render_net_menu(int sel) {
    memset(frame, 0, sizeof(frame));
    draw_text(30, 3, "NETWORK", IMG_W);
    for (int x = 10; x < 240; x++) px_set(x, 14);

    char buf[40];
    const char *items[NET_MENU_COUNT];
    static char onoff_buf[20];
    snprintf(onoff_buf, sizeof(onoff_buf), "WIFI: %s", wifi_enabled ? "ON" : "OFF");
    items[NET_ITEM_ONOFF] = onoff_buf;
    items[NET_ITEM_SCAN] = "SCAN NETWORKS";
    items[NET_ITEM_STATUS] = "STATUS";
    items[NET_ITEM_BACK] = "BACK";

    for (int i = 0; i < NET_MENU_COUNT; i++) {
        int y = 22 + i * 12;
        if (i == sel) {
            snprintf(buf, sizeof(buf), "> %s", items[i]);
            draw_inverted_line(y, buf);
        } else {
            snprintf(buf, sizeof(buf), "  %s", items[i]);
            draw_text(10, y, buf, IMG_W);
        }
    }

    snprintf(buf, sizeof(buf), "%s", wifi_connected ? "CONNECTED" : "DISCONNECTED");
    draw_text(10, 100, buf, IMG_W);
    draw_text(175, 110, "LEFT:BACK", IMG_W);
}

/* ─── Draw scan results ─── */
static void render_scan_results(void) {
    memset(frame, 0, sizeof(frame));
    draw_text(30, 3, "WIFI NETWORKS", IMG_W);
    for (int x = 10; x < 240; x++) px_set(x, 14);

    if (scan_in_progress) {
        draw_text(60, 50, "SCANNING...", IMG_W);
        char buf[20];
        snprintf(buf, sizeof(buf), "FOUND: %d", scan_count);
        draw_text(80, 65, buf, IMG_W);
        draw_text(175, 110, "LEFT:CANCEL", IMG_W);
        return;
    }

    if (scan_count == 0) {
        draw_text(50, 55, "NO NETWORKS FOUND", IMG_W);
        draw_text(175, 110, "LEFT:BACK", IMG_W);
        return;
    }

    /* Scrolling list — 7 items visible */
    int start = 0;
    if (scan_sel > 5) start = scan_sel - 5;
    if (start + 7 > scan_count) start = scan_count - 7;
    if (start < 0) start = 0;

    char buf[42];
    for (int i = 0; i < 7 && (start + i) < scan_count; i++) {
        int idx = start + i;
        int y = 20 + i * 12;
        char lock = (scan_results[idx].auth_mode != 0) ? '~' : ' ';
        if (idx == scan_sel) {
            snprintf(buf, sizeof(buf), "> %c%s", lock, scan_results[idx].ssid);
            draw_inverted_line(y, buf);
        } else {
            snprintf(buf, sizeof(buf), "  %c%s", lock, scan_results[idx].ssid);
            draw_text(10, y, buf, IMG_W);
        }
    }

    snprintf(buf, sizeof(buf), "%d FOUND  C:CONNECT", scan_count);
    draw_text(10, 110, buf, IMG_W);
    draw_text(175, 110, "LEFT:BACK", IMG_W);
}

/* ─── Draw on-screen keyboard ─── */
static void render_keyboard(void) {
    memset(frame, 0, sizeof(frame));

    /* Header: SSID */
    char hdr[42];
    snprintf(hdr, sizeof(hdr), "CONNECT: %s",
             selected_network >= 0 ? scan_results[selected_network].ssid : "?");
    draw_text(5, 0, hdr, IMG_W);

    /* Password field + shift indicator */
    char pw_show[35];
    int vis_start = pw_len > 28 ? pw_len - 28 : 0;
    for (int i = 0; i < pw_len - vis_start; i++) {
        char c = pw_buf[vis_start + i];
        pw_show[i] = (c >= 'a' && c <= 'z') ? c - 32 : c;
    }
    pw_show[pw_len - vis_start] = '\0';
    char pw_line[42];
    snprintf(pw_line, sizeof(pw_line), "PW:%s %s", pw_show, kb_shift ? "(CAPS)" : "(LOW)");
    draw_text(5, 10, pw_line, IMG_W);

    /* Separator */
    for (int x = 5; x < 245; x++) px_set(x, 20);

    /* Character grid: 4 rows x 10 cols, cells 24px wide x 12px tall */
    for (int r = 0; r < KB_CHAR_ROWS; r++) {
        for (int c = 0; c < 10; c++) {
            int cx = 5 + c * 24;
            int cy = 24 + r * 12;
            char ch = kb_grid[r][c];

            if (kb_row == r && kb_col == c) {
                /* Selected: inverted cell */
                for (int iy = cy; iy < cy + 10; iy++)
                    for (int ix = cx; ix < cx + 22; ix++)
                        px_set(ix, iy);
                /* Draw character white-on-black */
                const char *pos = strchr(font_chars, ch);
                if (pos) {
                    int fi = (int)(pos - font_chars);
                    for (int row2 = 0; row2 < 7; row2++) {
                        uint8_t bits = font5x7[fi][row2];
                        for (int col2 = 0; col2 < 5; col2++)
                            if (bits & (0x10 >> col2))
                                px_clr(cx + 8 + col2, cy + 1 + row2);
                    }
                }
            } else {
                /* Normal cell */
                const char *pos = strchr(font_chars, ch);
                if (pos) draw_char(cx + 8, cy + 1, (int)(pos - font_chars));
            }
        }
    }

    /* Special keys row at y=76 */
    static const char *sp_labels[] = {"SHIFT", "SPC", "DEL", "DONE", "CANCEL"};
    int sp_x[] = {5, 50, 90, 135, 190};
    int sp_w[] = {40, 35, 40, 50, 55};
    for (int i = 0; i < KB_SP_COUNT; i++) {
        int sx = sp_x[i];
        int sy = 76;
        if (kb_row == KB_SPECIAL_ROW && kb_col == i) {
            for (int iy = sy; iy < sy + 10; iy++)
                for (int ix = sx; ix < sx + sp_w[i]; ix++)
                    px_set(ix, iy);
            /* Draw label white-on-black */
            int tx = sx + 3;
            for (const char *cp = sp_labels[i]; *cp; cp++) {
                char up = *cp;
                const char *pos = strchr(font_chars, up);
                if (pos) {
                    int fi = (int)(pos - font_chars);
                    for (int row2 = 0; row2 < 7; row2++) {
                        uint8_t bits = font5x7[fi][row2];
                        for (int col2 = 0; col2 < 5; col2++)
                            if (bits & (0x10 >> col2))
                                px_clr(tx + col2, sy + 1 + row2);
                    }
                }
                tx += 6;
            }
        } else {
            draw_text(sx + 3, sy + 1, sp_labels[i], sp_w[i]);
        }
    }

    /* Help text */
    draw_text(5, 108, "U/D/L/R:MOVE  C:SELECT", IMG_W);
}

/* ─── Draw motion / accelerometer menu ─── */
#define MOT_ITEM_LIVE      0
#define MOT_ITEM_PEDOMETER 1
#define MOT_ITEM_TILT      2
#define MOT_ITEM_RESET     3
#define MOT_ITEM_THRESH    4
#define MOT_ITEM_I2CSCAN   5
#define MOT_ITEM_BACK      6
#define MOT_MENU_COUNT     7

static void render_motion_menu(int sel) {
    /* Poll sensor fresh data */
    mpu_read_all();
    pedometer_update();

    memset(frame, 0, sizeof(frame));
    draw_text(30, 3, "MOTION", IMG_W);
    for (int x = 10; x < 240; x++) px_set(x, 14);

    char buf[42];
    const char *items[MOT_MENU_COUNT];

    static char live_buf[42];
    snprintf(live_buf, sizeof(live_buf), "ACCEL: %.1f  %.1f  %.1fG",
             (double)accel_g(accel_x), (double)accel_g(accel_y), (double)accel_g(accel_z));
    items[MOT_ITEM_LIVE] = live_buf;

    static char ped_buf[25];
    snprintf(ped_buf, sizeof(ped_buf), "STEPS: %lu", (unsigned long)step_count);
    items[MOT_ITEM_PEDOMETER] = ped_buf;

    static char tilt_buf[30];
    snprintf(tilt_buf, sizeof(tilt_buf), "TILT: X%.0f  Y%.0f  %.1fC",
             (double)tilt_x_deg(), (double)tilt_y_deg(), (double)mpu_temp_c);
    items[MOT_ITEM_TILT] = tilt_buf;

    items[MOT_ITEM_RESET] = "RESET PEDOMETER";

    static char thresh_buf[25];
    snprintf(thresh_buf, sizeof(thresh_buf), "THRESHOLD: %.1fG", (double)step_threshold);
    items[MOT_ITEM_THRESH] = thresh_buf;

    items[MOT_ITEM_I2CSCAN] = "I2C BUS SCAN";
    items[MOT_ITEM_BACK] = "BACK";

    /* Scrolling window — 5 items visible */
    int vis = 5;
    int start = 0;
    if (sel > vis - 2) start = sel - (vis - 2);
    if (start + vis > MOT_MENU_COUNT) start = MOT_MENU_COUNT - vis;
    if (start < 0) start = 0;

    for (int i = 0; i < vis && (start + i) < MOT_MENU_COUNT; i++) {
        int idx = start + i;
        int y = 18 + i * 11;
        if (idx == sel) {
            snprintf(buf, sizeof(buf), "> %s", items[idx]);
            draw_inverted_line(y, buf);
        } else {
            snprintf(buf, sizeof(buf), "  %s", items[idx]);
            draw_text(10, y, buf, IMG_W);
        }
    }

    /* Scroll indicators */
    if (start > 0) draw_text(235, 18, "/", IMG_W);
    if (start + vis < MOT_MENU_COUNT) draw_text(235, 18 + (vis - 1) * 11, "/", IMG_W);

    /* Gyro readout at bottom */
    static char gyro_buf[42];
    snprintf(gyro_buf, sizeof(gyro_buf), "GYRO: %.0f  %.0f  %.0f D/S",
             (double)gyro_dps(gyro_x), (double)gyro_dps(gyro_y), (double)gyro_dps(gyro_z));
    draw_text(10, 86, gyro_buf, IMG_W);

    /* Magnitude bar */
    float mag = accel_magnitude();
    snprintf(buf, sizeof(buf), "MAG: %.2fG", (double)mag);
    draw_text(10, 98, buf, IMG_W);

    if (!mpu_ok) draw_text(130, 98, "MPU:NO", IMG_W);
    else draw_text(130, 98, "MPU:OK", IMG_W);
    draw_text(175, 110, "LEFT:BACK", IMG_W);
}

/* ─── I2C bus scan screen ─── */
static void render_i2c_scan(void) {
    memset(frame, 0, sizeof(frame));
    draw_text(30, 3, "I2C BUS SCAN", IMG_W);
    for (int x = 10; x < 240; x++) px_set(x, 14);

    draw_text(10, 20, "SCANNING I2C0 (GP0/GP1)...", IMG_W);
    transpose_to_display();
    EPD_Partial(display_buf);

    /* Scan all valid 7-bit addresses */
    uint8_t found[16];
    int found_count = 0;
    printf("[I2C] Scanning I2C0 bus...\n");

    for (int addr = 0x08; addr < 0x78; addr++) {
        uint8_t dummy;
        int ret = i2c_read_blocking(MPU_I2C, addr, &dummy, 1, false);
        if (ret >= 0 && found_count < 16) {
            found[found_count++] = (uint8_t)addr;
            printf("[I2C]   Device at 0x%02X\n", addr);
        }
    }
    printf("[I2C] Scan complete: %d device(s)\n", found_count);

    /* Show results */
    memset(frame, 0, sizeof(frame));
    draw_text(30, 3, "I2C BUS SCAN", IMG_W);
    for (int x = 10; x < 240; x++) px_set(x, 14);

    char buf[42];
    snprintf(buf, sizeof(buf), "FOUND %d DEVICE(S):", found_count);
    draw_text(10, 20, buf, IMG_W);

    for (int i = 0; i < found_count && i < 8; i++) {
        const char *desc = "";
        if (found[i] == 0x68) desc = " (MPU-6050)";
        else if (found[i] == 0x69) desc = " (MPU-6050 AD0:H)";
        else if (found[i] == 0x76) desc = " (BME280/BMP280)";
        else if (found[i] == 0x77) desc = " (BME280/BMP280)";
        else if (found[i] == 0x3C) desc = " (SSD1306 OLED)";
        else if (found[i] == 0x50) desc = " (EEPROM)";
        snprintf(buf, sizeof(buf), "  0X%02X%s", found[i], desc);
        draw_text(10, 32 + i * 10, buf, IMG_W);
    }

    if (found_count == 0) {
        draw_text(10, 40, "NO DEVICES FOUND", IMG_W);
        draw_text(10, 55, "CHECK WIRING:", IMG_W);
        draw_text(10, 66, "SDA:GP0(PIN1) SCL:GP1(PIN2)", IMG_W);
        draw_text(10, 77, "VCC:3V3 GND:GND AD0:GND", IMG_W);
    }

    draw_text(155, 110, "C:BACK", IMG_W);
}

/* ─── Show connecting screen (blocks during wifi_connect_to) ─── */
static void show_connecting_screen(const char *ssid) {
    memset(frame, 0, sizeof(frame));
    draw_text(40, 40, "CONNECTING TO", IMG_W);
    draw_text(40, 55, ssid, IMG_W);
    draw_text(40, 75, "PLEASE WAIT...", IMG_W);
    transpose_to_display();
    EPD_Partial(display_buf);
}

/* ─── WiFi / NTP functions ─── */

static void ntp_recv_cb(void *arg, struct udp_pcb *pcb, struct pbuf *p,
                         const ip_addr_t *addr, u16_t port) {
    (void)arg; (void)pcb; (void)addr; (void)port;
    if (p->tot_len >= NTP_MSG_LEN) {
        uint8_t *buf = (uint8_t *)p->payload;
        uint32_t secs = (buf[40] << 24) | (buf[41] << 16) | (buf[42] << 8) | buf[43];
        time_t epoch = (time_t)(secs - NTP_DELTA) + TIMEZONE_OFFSET_SEC;
        struct tm *t = gmtime(&epoch);
        datetime_t dt = {
            .year  = (int16_t)(t->tm_year + 1900),
            .month = (int8_t)(t->tm_mon + 1),
            .day   = (int8_t)t->tm_mday,
            .dotw  = (int8_t)t->tm_wday,
            .hour  = (int8_t)t->tm_hour,
            .min   = (int8_t)t->tm_min,
            .sec   = (int8_t)t->tm_sec,
        };
        rtc_set_datetime(&dt);
        ntp_synced = true;
        ntp_time_received = true;
        printf("[NTP] Synced: %04d-%02d-%02d %02d:%02d:%02d\n",
               dt.year, dt.month, dt.day, dt.hour, dt.min, dt.sec);
    }
    pbuf_free(p);
}

static void ntp_dns_cb(const char *name, const ip_addr_t *addr, void *arg) {
    (void)arg;
    if (addr) {
        ntp_server_addr = *addr;
        struct pbuf *p = pbuf_alloc(PBUF_TRANSPORT, NTP_MSG_LEN, PBUF_RAM);
        if (p) {
            memset(p->payload, 0, NTP_MSG_LEN);
            ((uint8_t *)p->payload)[0] = 0x1b;
            udp_sendto(ntp_pcb, p, &ntp_server_addr, NTP_PORT);
            pbuf_free(p);
            printf("[NTP] Request sent to %s\n", ipaddr_ntoa(addr));
        }
    }
}

static void ntp_request(void) {
    if (!ntp_pcb) {
        ntp_pcb = udp_new();
        if (!ntp_pcb) return;
        udp_recv(ntp_pcb, ntp_recv_cb, NULL);
    }
    dns_gethostbyname(NTP_SERVER, &ntp_server_addr, ntp_dns_cb, NULL);
}

/* ─── WiFi scan ─── */
static int wifi_scan_callback(void *env, const cyw43_ev_scan_result_t *result) {
    (void)env;
    if (!result || scan_count >= MAX_SCAN_RESULTS) return 0;
    if (result->ssid_len == 0) return 0;  /* skip hidden networks */

    /* Deduplicate — keep the one with better RSSI */
    for (int i = 0; i < scan_count; i++) {
        if (strncmp(scan_results[i].ssid, (const char *)result->ssid, result->ssid_len) == 0
            && strlen(scan_results[i].ssid) == result->ssid_len) {
            if (result->rssi > scan_results[i].rssi) {
                scan_results[i].rssi = (int8_t)result->rssi;
                scan_results[i].auth_mode = result->auth_mode;
            }
            return 0;
        }
    }

    memcpy(scan_results[scan_count].ssid, result->ssid, result->ssid_len);
    scan_results[scan_count].ssid[result->ssid_len] = '\0';
    scan_results[scan_count].rssi = (int8_t)result->rssi;
    scan_results[scan_count].auth_mode = result->auth_mode;
    scan_count++;
    return 0;
}

static void wifi_start_scan(void) {
    scan_count = 0;
    scan_sel = 0;
    scan_in_progress = true;
    scan_complete = false;
    cyw43_arch_enable_sta_mode();
    cyw43_wifi_scan_options_t opts = {0};
    cyw43_wifi_scan(&cyw43_state, &opts, NULL, wifi_scan_callback);
    printf("[WiFi] Scan started\n");
}

/* ─── WiFi connect (accepts arbitrary SSID/password) ─── */
static void wifi_connect_to(const char *ssid, const char *password) {
    printf("[WiFi] Connecting to \"%s\"...\n", ssid);
    strncpy(wifi_ssid_display, ssid, sizeof(wifi_ssid_display) - 1);
    wifi_ssid_display[sizeof(wifi_ssid_display) - 1] = '\0';
    wifi_enabled = true;

    cyw43_arch_enable_sta_mode();

    uint32_t auth = (password[0] != '\0') ? CYW43_AUTH_WPA2_AES_PSK : 0;
    int err = cyw43_arch_wifi_connect_timeout_ms(ssid, password, auth, 15000);
    if (err) {
        printf("[WiFi] Connection failed (err=%d)\n", err);
        wifi_connected = false;
        return;
    }

    wifi_connected = true;
    struct netif *netif = &cyw43_state.netif[CYW43_ITF_STA];
    snprintf(wifi_ip_str, sizeof(wifi_ip_str), "%s", ipaddr_ntoa(&netif->ip_addr));
    cyw43_wifi_get_rssi(&cyw43_state, &wifi_rssi);
    printf("[WiFi] Connected: %s  RSSI: %d\n", wifi_ip_str, (int)wifi_rssi);

    ntp_request();
}

static void wifi_connect(void) {
    wifi_connect_to(WIFI_SSID, WIFI_PASS);
}

static void wifi_disconnect(void) {
    printf("[WiFi] Disconnecting...\n");
    cyw43_wifi_leave(&cyw43_state, CYW43_ITF_STA);
    /* Keep CYW43 initialised — battery VSYS sense needs it on GPIO 29 */
    wifi_connected = false;
    wifi_enabled = false;
    ntp_synced = false;
    strncpy(wifi_ssid_display, "---", sizeof(wifi_ssid_display));
    strncpy(wifi_ip_str, "---", sizeof(wifi_ip_str));
}

/* ─── Pick a quote matching current_mood, or random if -1 ─── */
static int pick_quote(void) {
    if (current_mood < 0)
        return rng_next() % QUOTE_COUNT;

    /* Collect indices matching the mood */
    int matches[QUOTE_COUNT];
    int count = 0;
    for (int i = 0; i < QUOTE_COUNT; i++) {
        if (quotes[i].mood == (uint8_t)current_mood)
            matches[count++] = i;
    }
    if (count == 0)
        return rng_next() % QUOTE_COUNT;  /* fallback */
    return matches[rng_next() % count];
}

/* ─── Main ─── */
int main(void) {
    stdio_init_all();
    sleep_ms(1000);
    printf("DILDER HUB v%s (%s) | display: %s | %d quotes | built %s %s\n",
           DILDER_VERSION, DILDER_VERSION_DATE, DISPLAY_NAME, QUOTE_COUNT, __DATE__, __TIME__);

    init_rtc_from_compile_time();

    if (DEV_Module_Init() != 0) {
        printf("ERROR: Hardware init failed.\n");
        return 1;
    }

    joystick_init();
    speaker_init();

    /* Startup chime */
    speaker_tone(1000, 80); sleep_ms(30);
    speaker_tone(1500, 80); sleep_ms(30);
    speaker_tone(2000, 120);

    EPD_Init();
    EPD_Clear();
    rng_seed();

    /* Init CYW43 early — even without WiFi, the chip's SPI CS shares
       GPIO 29 (ADC3/VSYS sense) and will hold it low if uninitialised. */
    if (cyw43_arch_init()) {
        printf("WARNING: CYW43 init failed — battery reads may be 0\n");
    }

    battery_init();
    mpu_init();

    /* ─── State machine ─── */
    uint8_t state = STATE_OCTOPUS;
    uint32_t frame_idx = 0;
    int qi = pick_quote();
    int menu_sel = 0;
    int mood_sel = 0;  /* 0 = ALL, 1-16 = specific mood */

    int snd_sel = 0;

    uint32_t last_input_ms = 0;
    #define INPUT_DEBOUNCE 5

    /* Helper macro for polling input in sub-screens */
    #define POLL_INPUT(ms) \
        for (int _pi = 0; _pi < ((ms)/5); _pi++) { \
            sleep_ms(5); \
            if (wifi_enabled || scan_in_progress) cyw43_arch_poll(); \
            if (to_ms_since_boot(get_absolute_time()) - last_input_ms < INPUT_DEBOUNCE) continue; \
            uint8_t inp = read_joystick(); \
            if (inp == INPUT_NONE) continue; \
            last_input_ms = to_ms_since_boot(get_absolute_time());

    #define POLL_END break; }

    while (true) {
        uint32_t now = to_ms_since_boot(get_absolute_time());

        /* Poll WiFi / scan */
        if (wifi_enabled || scan_in_progress) cyw43_arch_poll();

        switch (state) {

        /* ════════ OCTOPUS MAIN SCREEN ════════ */
        case STATE_OCTOPUS: {
            const Quote *q = &quotes[qi];
            const uint8_t *cycle = mood_cycle(q->mood);
            uint8_t expr = cycle[frame_idx % 4];

            if (expr == EXPR_OPEN && frame_idx > 0)
                qi = pick_quote();

            render_frame(&quotes[qi], expr, frame_idx);
            /* WiFi icon top-left, battery icon top-right */
            draw_wifi_icon(0, 1, wifi_connected);
            draw_battery_icon(234, 1);
            draw_text(175, 113, "DOWN:MENU", IMG_W);
            transpose_to_display();

            EPD_Partial(display_buf);
            frame_idx++;

            /* Poll 3 seconds for joystick */
            for (int i = 0; i < 600 && state == STATE_OCTOPUS; i++) {
                sleep_ms(5);
                if (wifi_enabled || scan_in_progress) cyw43_arch_poll();
                if (to_ms_since_boot(get_absolute_time()) - last_input_ms < INPUT_DEBOUNCE) continue;
                uint8_t inp = read_joystick();
                if (inp == INPUT_DOWN) {
                    last_input_ms = to_ms_since_boot(get_absolute_time());
                    state = STATE_MENU; menu_sel = 0;
                    speaker_tone(800, 50);
                } else if (inp == INPUT_CENTER) {
                    last_input_ms = to_ms_since_boot(get_absolute_time());
                    speaker_tone(1319, 100);
                }
            }
            break;
        }

        /* ════════ MENU ════════ */
        case STATE_MENU: {
            const Quote *q = &quotes[qi];
            render_frame(q, mood_cycle(q->mood)[frame_idx % 4], frame_idx);
            render_menu(menu_sel);
            transpose_to_display();
            EPD_Partial(display_buf);

            POLL_INPUT(4000)
                if (inp == INPUT_UP) {
                    menu_sel = (menu_sel - 1 + MENU_COUNT) % MENU_COUNT;
                    speaker_tone(600, 30); break;
                } else if (inp == INPUT_DOWN) {
                    menu_sel = (menu_sel + 1) % MENU_COUNT;
                    speaker_tone(600, 30); break;
                } else if (inp == INPUT_CENTER) {
                    speaker_tone(1000, 50);
                    
                    switch (menu_sel) {
                        case 0: state = STATE_MOOD_SELECT; mood_sel = current_mood + 1; break;
                        case 1: state = STATE_NET_MENU; break;
                        case 2: state = STATE_SOUND; snd_sel = 0; break;
                        case 3: state = STATE_MOTION; break;
                        case 4: state = STATE_INFO; break;
                        default: state = STATE_OCTOPUS; break;
                    }
                    break;
                } else if (inp == INPUT_LEFT) {
                    state = STATE_OCTOPUS; 
                    speaker_tone(500, 50); break;
                }
            POLL_END
            break;
        }

        /* ════════ MOOD SELECT ════════ */
        case STATE_MOOD_SELECT: {
            render_mood_select(mood_sel);
            transpose_to_display();
            EPD_Partial(display_buf);

            POLL_INPUT(4000)
                if (inp == INPUT_UP) {
                    mood_sel = (mood_sel - 1 + MOOD_COUNT + 1) % (MOOD_COUNT + 1);
                    speaker_tone(600, 30); break;
                } else if (inp == INPUT_DOWN) {
                    mood_sel = (mood_sel + 1) % (MOOD_COUNT + 1);
                    speaker_tone(600, 30); break;
                } else if (inp == INPUT_CENTER) {
                    current_mood = mood_sel == 0 ? -1 : mood_sel - 1;
                    qi = pick_quote();
                    frame_idx = 0;  /* reset animation */
                    state = STATE_OCTOPUS;  /* return to octopus */
                    speaker_tone(1200, 80);
                    printf("[mood] Selected: %s → back to octopus\n",
                           current_mood < 0 ? "ALL" : mood_names[current_mood]);
                    break;
                } else if (inp == INPUT_LEFT) {
                    state = STATE_MENU; 
                    speaker_tone(500, 50); break;
                }
            POLL_END
            break;
        }

        /* ════════ NETWORK STATUS (read-only) ════════ */
        case STATE_NETWORK: {
            render_network_screen();
            transpose_to_display();
            EPD_Partial(display_buf);

            POLL_INPUT(4000)
                if (inp == INPUT_LEFT || inp == INPUT_CENTER) {
                    state = STATE_NET_MENU;
                    speaker_tone(500, 50); break;
                }
            POLL_END
            break;
        }

        /* ════════ SOUND SUBMENU ════════ */
        case STATE_SOUND: {
            render_sound_menu(snd_sel);
            transpose_to_display();
            EPD_Partial(display_buf);

            POLL_INPUT(4000)
                if (inp == INPUT_UP) {
                    snd_sel = (snd_sel - 1 + SND_MENU_COUNT) % SND_MENU_COUNT;
                    speaker_tone(800, 50); break;
                }
                if (inp == INPUT_DOWN) {
                    snd_sel = (snd_sel + 1) % SND_MENU_COUNT;
                    speaker_tone(800, 50); break;
                }
                if (inp == INPUT_LEFT) {
                    if (snd_sel == SND_ITEM_PATTERN) {
                        current_pattern = (current_pattern - 1 + SOUND_PATTERN_COUNT) % SOUND_PATTERN_COUNT;
                        speaker_tone(800, 30); break;
                    }
                    state = STATE_MENU;
                    speaker_tone(500, 50); break;
                }
                if (inp == INPUT_RIGHT) {
                    if (snd_sel == SND_ITEM_PATTERN) {
                        current_pattern = (current_pattern + 1) % SOUND_PATTERN_COUNT;
                        speaker_tone(800, 30); break;
                    }
                }
                if (inp == INPUT_CENTER) {
                    switch (snd_sel) {
                        case SND_ITEM_PATTERN:
                            play_sound_pattern(current_pattern);
                            break;
                        case SND_ITEM_ONOFF:
                            sound_enabled = !sound_enabled;
                            if (sound_enabled) speaker_tone(1000, 50);
                            break;
                        case SND_ITEM_VOL:
                            sound_vol = (sound_vol + 1) % 3;
                            speaker_tone(1000, 100);
                            break;
                        case SND_ITEM_BACK:
                            state = STATE_MENU;
                            speaker_tone(500, 50);
                            break;
                    }
                    break;
                }
            POLL_END
            break;
        }

        /* ════════ DEVICE INFO ════════ */
        case STATE_INFO: {
            render_info_screen();
            transpose_to_display();
            EPD_Partial(display_buf);

            POLL_INPUT(4000)
                if (inp == INPUT_LEFT || inp == INPUT_CENTER) {
                    state = STATE_MENU; 
                    speaker_tone(500, 50); break;
                }
            POLL_END
            break;
        }

        /* ════════ NETWORK SUBMENU ════════ */
        case STATE_NET_MENU: {
            static int net_menu_sel = 0;
            render_net_menu(net_menu_sel);
            transpose_to_display();
            EPD_Partial(display_buf);

            POLL_INPUT(4000)
                if (inp == INPUT_UP) {
                    net_menu_sel = (net_menu_sel - 1 + NET_MENU_COUNT) % NET_MENU_COUNT;
                    speaker_tone(600, 30); break;
                }
                if (inp == INPUT_DOWN) {
                    net_menu_sel = (net_menu_sel + 1) % NET_MENU_COUNT;
                    speaker_tone(600, 30); break;
                }
                if (inp == INPUT_LEFT) {
                    state = STATE_MENU;
                    speaker_tone(500, 50); break;
                }
                if (inp == INPUT_CENTER) {
                    speaker_tone(1000, 50);
                    switch (net_menu_sel) {
                        case NET_ITEM_ONOFF:
                            if (wifi_enabled) wifi_disconnect();
                            else wifi_connect();
                            break;
                        case NET_ITEM_SCAN:
                            wifi_start_scan();
                            state = STATE_NET_SCAN; break;
                        case NET_ITEM_STATUS:
                            state = STATE_NETWORK; break;
                        case NET_ITEM_BACK:
                            state = STATE_MENU; break;
                    }
                    break;
                }
            POLL_END
            break;
        }

        /* ════════ SCAN RESULTS ════════ */
        case STATE_NET_SCAN: {
            /* Check if scan finished */
            if (scan_in_progress && !cyw43_wifi_scan_active(&cyw43_state)) {
                scan_in_progress = false;
                scan_complete = true;
                printf("[WiFi] Scan complete: %d networks\n", scan_count);
            }

            render_scan_results();
            transpose_to_display();
            EPD_Partial(display_buf);

            POLL_INPUT(scan_in_progress ? 500 : 4000)
                if (inp == INPUT_LEFT) {
                    scan_in_progress = false;
                    state = STATE_NET_MENU;
                    speaker_tone(500, 50); break;
                }
                if (scan_complete && scan_count > 0) {
                    if (inp == INPUT_UP) {
                        scan_sel = (scan_sel - 1 + scan_count) % scan_count;
                        speaker_tone(600, 30); break;
                    }
                    if (inp == INPUT_DOWN) {
                        scan_sel = (scan_sel + 1) % scan_count;
                        speaker_tone(600, 30); break;
                    }
                    if (inp == INPUT_CENTER) {
                        speaker_tone(1000, 50);
                        selected_network = scan_sel;
                        if (scan_results[scan_sel].auth_mode == 0) {
                            /* Open network — connect directly */
                            show_connecting_screen(scan_results[scan_sel].ssid);
                            wifi_connect_to(scan_results[scan_sel].ssid, "");
                            state = STATE_NETWORK;
                        } else {
                            /* Needs password — keyboard */
                            pw_len = 0;
                            pw_buf[0] = '\0';
                            kb_row = 0; kb_col = 0; kb_shift = true;
                            state = STATE_NET_KEYBOARD;
                        }
                        break;
                    }
                }
            POLL_END
            break;
        }

        /* ════════ ON-SCREEN KEYBOARD ════════ */
        case STATE_NET_KEYBOARD: {
            render_keyboard();
            transpose_to_display();
            EPD_Partial(display_buf);

            POLL_INPUT(4000)
                if (inp == INPUT_UP) {
                    if (kb_row > 0) kb_row--;
                    if (kb_row < KB_SPECIAL_ROW && kb_col >= 10) kb_col = 9;
                    speaker_tone(600, 20); break;
                }
                if (inp == INPUT_DOWN) {
                    if (kb_row < KB_SPECIAL_ROW) kb_row++;
                    if (kb_row == KB_SPECIAL_ROW && kb_col >= KB_SP_COUNT) kb_col = KB_SP_COUNT - 1;
                    speaker_tone(600, 20); break;
                }
                if (inp == INPUT_LEFT) {
                    if (kb_row < KB_SPECIAL_ROW)
                        kb_col = (kb_col - 1 + 10) % 10;
                    else
                        kb_col = (kb_col - 1 + KB_SP_COUNT) % KB_SP_COUNT;
                    speaker_tone(600, 20); break;
                }
                if (inp == INPUT_RIGHT) {
                    if (kb_row < KB_SPECIAL_ROW)
                        kb_col = (kb_col + 1) % 10;
                    else
                        kb_col = (kb_col + 1) % KB_SP_COUNT;
                    speaker_tone(600, 20); break;
                }
                if (inp == INPUT_CENTER) {
                    if (kb_row < KB_SPECIAL_ROW) {
                        /* Insert character */
                        if (pw_len < PW_MAX_LEN) {
                            pw_buf[pw_len++] = kb_char_at(kb_row, kb_col, kb_shift);
                            pw_buf[pw_len] = '\0';
                            speaker_tone(1000, 30);
                        }
                    } else {
                        /* Special key */
                        switch (kb_col) {
                            case KB_SP_SHIFT:
                                kb_shift = !kb_shift;
                                speaker_tone(800, 30);
                                break;
                            case KB_SP_SPACE:
                                if (pw_len < PW_MAX_LEN) {
                                    pw_buf[pw_len++] = ' ';
                                    pw_buf[pw_len] = '\0';
                                }
                                speaker_tone(1000, 30);
                                break;
                            case KB_SP_DEL:
                                if (pw_len > 0) pw_buf[--pw_len] = '\0';
                                speaker_tone(500, 30);
                                break;
                            case KB_SP_DONE:
                                speaker_tone(1200, 80);
                                show_connecting_screen(scan_results[selected_network].ssid);
                                wifi_connect_to(scan_results[selected_network].ssid, pw_buf);
                                state = STATE_NETWORK;
                                break;
                            case KB_SP_CANCEL:
                                speaker_tone(500, 50);
                                state = STATE_NET_SCAN;
                                break;
                        }
                    }
                    break;
                }
            POLL_END
            break;
        }

        /* ════════ MOTION / ACCELEROMETER ════════ */
        case STATE_MOTION: {
            static int mot_sel = 0;
            render_motion_menu(mot_sel);
            transpose_to_display();
            EPD_Partial(display_buf);

            POLL_INPUT(500)  /* fast refresh for live data */
                if (inp == INPUT_UP) {
                    mot_sel = (mot_sel - 1 + MOT_MENU_COUNT) % MOT_MENU_COUNT;
                    speaker_tone(600, 20); break;
                }
                if (inp == INPUT_DOWN) {
                    mot_sel = (mot_sel + 1) % MOT_MENU_COUNT;
                    speaker_tone(600, 20); break;
                }
                if (inp == INPUT_LEFT) {
                    state = STATE_MENU;
                    speaker_tone(500, 50); break;
                }
                if (inp == INPUT_CENTER) {
                    switch (mot_sel) {
                        case MOT_ITEM_RESET:
                            step_count = 0;
                            speaker_tone(1000, 50);
                            break;
                        case MOT_ITEM_THRESH:
                            step_threshold += 0.1f;
                            if (step_threshold > 2.5f) step_threshold = 0.8f;
                            speaker_tone(800, 30);
                            break;
                        case MOT_ITEM_I2CSCAN:
                            speaker_tone(1000, 50);
                            render_i2c_scan();
                            transpose_to_display();
                            EPD_Partial(display_buf);
                            /* Wait for any button to go back */
                            POLL_INPUT(30000)
                                speaker_tone(500, 30);
                            POLL_END
                            break;
                        case MOT_ITEM_BACK:
                            state = STATE_MENU;
                            speaker_tone(500, 50);
                            break;
                        default:
                            break;
                    }
                    break;
                }
                if (inp == INPUT_RIGHT && mot_sel == MOT_ITEM_THRESH) {
                    step_threshold += 0.1f;
                    if (step_threshold > 2.5f) step_threshold = 0.8f;
                    speaker_tone(800, 30); break;
                }
            POLL_END
            break;
        }

        } /* end switch */
    }

    return 0;
}
