# Python-to-C Translation Guide

How the Python asset renderers work, and how to translate them into C for the Pico W firmware with minimal memory and performance overhead.

---

## How the Python Rendering Works

### Architecture

```
canvas.py          Frame buffer (250x122 array) + pixel ops
    |
body.py            RLE body data (run-length encoded row spans)
    |
drawing.py         Primitives: fill_circle, draw_line, draw_rect, draw_arc
    |
faces.py           Per-emotion face components (pupils, mouths, brows, lids)
transforms.py      Per-emotion body transform params (dx, dy, wobble, expand)
    |
particles.py       Per-emotion aura particle positions (sinusoidal orbits)
    |
environments/      Background draw functions (pixel-by-pixel)
outfits/           Overlay draw functions (anchor-relative)
decor/             Standalone prop draw functions
    |
compose.py         13-step pipeline: clear -> env -> body -> outfit -> face -> aura -> bubble
```

### What Each Draw Function Does

Every draw function ultimately calls `px_set(x, y)` or `px_clr(x, y)` to set individual pixels in a 250x122 frame buffer. There are two coordinate modes:

- **Absolute** (`px_set`): Fixed screen coordinates. Used for environments, bubble, aura.
- **Body-relative** (`px_set_off`): Applies body transform offsets (dx, dy, row wobble). Used for body, face, outfits.

The body transform is 6 globals set per-frame:
```python
body_dx, body_dy       # Position offset
body_x_expand          # Horizontal stretch/shrink
wobble_amp, wobble_freq, wobble_phase  # Per-row sine distortion
```

### Data Representations

| Python | What it is | C equivalent |
|--------|-----------|--------------|
| `[[0]*250 for _ in range(122)]` | Frame buffer | `uint8_t frame[122][32]` (bitpacked, 32 bytes/row) |
| `[(y, [(x0,x1), ...])]` | Body RLE | `const uint8_t body_rle[]` (packed struct array) |
| `math.sin(f * k)` | Animation curves | Lookup table `int8_t sin_lut[64]` |
| `fill_circle(cx, cy, r_sq, val)` | Circle fill | Same loop, inline or macro |
| `draw_line(x0, y0, x1, y1)` | Bresenham line | Identical algorithm in C |

---

## C Translation Strategy

### 1. Frame Buffer: Bitpack It

Python uses a 2D int array (30,500 bytes). In C, bitpack to 1 bit per pixel:

```c
// 250 pixels / 8 = 31.25 -> 32 bytes per row
#define FB_W 250
#define FB_H 122
#define FB_ROW_BYTES 32
static uint8_t frame[FB_H][FB_ROW_BYTES];

static inline void px_set(int x, int y) {
    if ((unsigned)x < FB_W && (unsigned)y < FB_H)
        frame[y][x >> 3] |= (0x80 >> (x & 7));
}

static inline void px_clr(int x, int y) {
    if ((unsigned)x < FB_W && (unsigned)y < FB_H)
        frame[y][x >> 3] &= ~(0x80 >> (x & 7));
}
```

**Memory: 122 * 32 = 3,904 bytes** (vs 30,500 in Python). This fits easily in Pico W's 264KB SRAM.

### 2. Body Transform: Global Vars, Reset Per Frame

```c
static int8_t body_dx, body_dy, body_x_expand;
static float wobble_amp, wobble_freq, wobble_phase;

static inline int row_wobble(int y) {
    if (wobble_amp == 0.0f) return 0;
    return (int)(wobble_amp * sin_lut_f(y * wobble_freq + wobble_phase));
}

static inline void px_set_off(int x, int y) {
    px_set(x + body_dx + row_wobble(y), y + Y_OFF + body_dy);
}
```

### 3. Sin/Cos: Use a Lookup Table

Every animation curve in the Python code uses `math.sin()`. Replace with a 64-entry LUT:

```c
// 64-entry sin table, scaled to -127..+127
static const int8_t SIN_LUT[64] = {
    0, 12, 25, 37, 49, 60, 71, 81, 90, 98, 106, 112, 117, 122, 125, 127,
    127, 127, 125, 122, 117, 112, 106, 98, 90, 81, 71, 60, 49, 37, 25, 12,
    0, -12, -25, -37, -49, -60, -71, -81, -90, -98, -106, -112, -117, -122, -125, -127,
    -127, -127, -125, -122, -117, -112, -106, -98, -90, -81, -71, -60, -49, -37, -25, -12,
};

// Returns sin(angle) scaled to -127..+127. Input is 0..255 (full circle)
static inline int8_t fast_sin(uint8_t angle) {
    return SIN_LUT[(angle >> 2) & 63];
}

// Float version for wobble (returns -1.0 .. 1.0, 64 bytes ROM)
static inline float sin_lut_f(float rad) {
    int idx = ((int)(rad * 10.186f)) & 63;  // 64 / (2*pi) ≈ 10.186
    return SIN_LUT[idx] / 127.0f;
}
```

**Cost: 64 bytes ROM.** Replaces all `math.sin()` calls. Accuracy is ~1 pixel at this resolution — imperceptible on e-ink.

### 4. Body RLE: Pack Into Const Flash

Python stores RLE as a list of tuples. In C, pack into a flat `const` array in flash (not RAM):

```c
// Format: [y_row, num_spans, x0, x1, x0, x1, ...]
// Terminated by y_row = 0xFF
static const uint8_t BODY_RLE_STANDARD[] PROGMEM = {
    10, 1,  22, 48,
    11, 1,  18, 52,
    12, 1,  16, 54,
    // ... dome rows (1 span each)
    55, 5,  10, 17, 21, 28, 32, 39, 43, 50, 54, 61,  // tentacle row
    // ...
    0xFF  // sentinel
};
```

**Drawing:**
```c
void draw_body(const uint8_t *rle) {
    const uint8_t *p = rle;
    while (*p != 0xFF) {
        uint8_t y = *p++;
        uint8_t n = *p++;
        for (uint8_t i = 0; i < n; i++) {
            int x0 = *p++ - body_x_expand;
            int x1 = *p++ + body_x_expand;
            if (x0 < 0) x0 = 0;
            if (x1 >= FB_W) x1 = FB_W - 1;
            for (int x = x0; x <= x1; x++)
                px_set_off(x, y);
        }
    }
}
```

**Memory: ~300 bytes flash per body variant.** Zero RAM cost since it's `const`.

### 5. Environment Draw Functions: Direct Port

Each Python environment function is a series of `px_set()`, `draw_rect()`, `draw_line()` calls. These translate 1:1 to C:

```python
# Python
def draw_bedroom(frame_idx=0):
    draw_hline(0, 70, 100)
    draw_rect(0, 75, 8, 25)
```

```c
// C — identical logic
void draw_env_bedroom(uint8_t frame_idx) {
    draw_hline(0, 70, 100);
    draw_rect(0, 75, 8, 25);
}
```

**Key: environments are procedural (no data), so they cost only code space (flash), not RAM.**

### 6. Outfit/Aura Functions: Same Pattern

Outfits take anchor points and draw relative to them. Auras take center coordinates and frame_idx. Both translate identically — the Python is already written like C.

### 7. Registry System: Use Function Pointer Arrays

Python uses dicts of callables. In C, use indexed arrays of function pointers:

```c
typedef void (*draw_fn_t)(void);
typedef void (*env_fn_t)(uint8_t frame_idx);
typedef void (*outfit_fn_t)(int dome_x, int dome_y, int eye_lx, int eye_ly, int eye_rx, int eye_ry);
typedef void (*aura_fn_t)(int cx, int cy, uint8_t frame_idx);

// Emotion config
typedef struct {
    const uint8_t *body_rle;
    draw_fn_t draw_pupils;
    draw_fn_t draw_mouth;
    draw_fn_t draw_brows;     // NULL if unused
    draw_fn_t draw_lids;      // NULL if unused
    draw_fn_t draw_tears;     // NULL if unused
    void (*setup_transform)(uint8_t frame_idx);
    aura_fn_t draw_aura;
} emotion_config_t;

static const emotion_config_t EMOTIONS[16] = {
    [MOOD_NORMAL]  = { BODY_RLE_STANDARD, draw_pupils_normal, draw_mouth_smirk, NULL, NULL, NULL, transform_normal, aura_normal },
    [MOOD_ANGRY]   = { BODY_RLE_STANDARD, draw_pupils_angry,  draw_mouth_angry,  draw_brows_angry, NULL, NULL, transform_angry, aura_angry },
    // ...
};

// Environment dispatch
static const env_fn_t ENVIRONMENTS[10] = {
    draw_env_bedroom, draw_env_kitchen, draw_env_living_room,
    draw_env_park, draw_env_beach, draw_env_space,
    draw_env_underwater, draw_env_office, draw_env_rooftop, draw_env_arcade,
};
```

**Each config struct is ~32 bytes. 16 emotions = 512 bytes flash.** Traversal is O(1) array indexing.

### 8. Composition Pipeline: Direct Port

```c
void render_scene(uint8_t emotion, uint8_t pose, uint8_t env, uint8_t outfit, uint8_t frame_idx) {
    clear_frame();
    if (env < 10) ENVIRONMENTS[env](frame_idx);

    const emotion_config_t *e = &EMOTIONS[emotion];
    e->setup_transform(frame_idx);
    draw_body(e->body_rle);

    if (outfit < NUM_OUTFITS) OUTFITS[outfit](dome_x, dome_y, ...);

    draw_eyes();
    if (e->draw_pupils) e->draw_pupils();
    if (e->draw_brows)  e->draw_brows();
    if (e->draw_lids)   e->draw_lids();
    if (e->draw_tears)  e->draw_tears();
    e->draw_mouth();
    if (e->draw_aura)   e->draw_aura(35, 45, frame_idx);

    draw_bubble();
}
```

---

## Memory Budget (Pico W: 264KB SRAM, 2MB Flash)

| Component | RAM | Flash | Notes |
|-----------|-----|-------|-------|
| Frame buffer | 3,904 B | 0 | Bitpacked 250x122 |
| Body RLE (3 variants) | 0 | ~900 B | `const` in flash |
| Sin LUT | 0 | 64 B | `const` in flash |
| Emotion configs (16) | 0 | ~512 B | Function pointer structs |
| Face draw functions (16 pupils + 16 mouths + brows/lids) | 0 | ~8 KB | Code in flash |
| Environment draw functions (10) | 0 | ~6 KB | Code in flash |
| Outfit draw functions (21) | 0 | ~5 KB | Code in flash |
| Aura draw functions (16) | 0 | ~4 KB | Code in flash |
| Decor draw functions (29) | 0 | ~4 KB | Code in flash |
| Drawing primitives | 0 | ~1 KB | Code in flash |
| Transform globals | 24 B | 0 | 6 variables |
| **Total** | **~4 KB RAM** | **~26 KB flash** | |

That's **1.5% of RAM** and **1.3% of flash**. Plenty of room for quotes, WiFi stack, and e-ink driver.

---

## Performance Considerations

### E-ink Refresh is the Bottleneck

The Waveshare 2.13" e-ink partial refresh takes ~300ms. Frame rendering takes <5ms on the Pico W's 133MHz ARM Cortex-M0+. The rendering is never the bottleneck.

### Avoid These Python-isms in C

| Python pattern | C alternative | Why |
|---------------|---------------|-----|
| `math.sin()` (libm) | `SIN_LUT[idx]` | libm sin is ~100 cycles; LUT is 2 cycles |
| `range()` loops | `for(int i=0; i<n; i++)` | Already what the compiler generates |
| `int(float_val)` | `(int)(float_val)` | Identical |
| Dict lookup `REGISTRY[key]` | Array index `arr[idx]` | O(1) both, but array avoids hash overhead |
| `if key in dict` | `if (idx < NUM_ITEMS && arr[idx] != NULL)` | Bounds check + null check |
| PIL Image creation | Direct SPI write to e-ink | Frame buffer IS the display buffer |

### Rendering Directly to Display Buffer

On the Pico, the frame buffer can be the exact buffer sent to the e-ink display via SPI. No intermediate Image conversion needed:

```c
// After render_scene(), frame[] is ready for SPI transfer
EPD_2in13_V4_Display(frame);
```

### Conditional Compilation for Variants

If flash is tight, use `#ifdef` to include only the environments/outfits the device needs:

```c
#ifdef INCLUDE_ENV_SPACE
void draw_env_space(uint8_t frame_idx) { ... }
#endif
```

---

## Translation Checklist

For each Python draw function, the C translation follows this pattern:

1. **Same function signature** (adjust types: `int` params, `uint8_t frame_idx`)
2. **Same loop structure** (Python `for x in range(a, b)` -> C `for(int x=a; x<b; x++)`)
3. **Same pixel ops** (`px_set`, `px_clr`, `px_set_off`, `px_clr_off`)
4. **Replace `math.sin`** with `sin_lut_f()` or `fast_sin()`
5. **Replace `math.sqrt`** with integer approximation or precomputed values
6. **Add `const`** to all data arrays so they live in flash
7. **Add `static`** to all internal functions for inlining opportunities
8. **Test**: render in Python, render in C, diff the frame buffers — they should be identical

The Python renderers are intentionally written in a C-like style (no classes, no generators, no list comprehensions in draw loops) specifically so they can be ported line-by-line.
