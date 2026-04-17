# Dilder ESP32-S3 Firmware — Implementation Guide

> Full mood-selector port for the Olimex ESP32-S3-DevKit-Lipo with Waveshare 2.13" e-Paper V3.

---

## Table of Contents

1. [What This Does](#what-this-does)
2. [Hardware Setup](#hardware-setup)
3. [Project Structure](#project-structure)
4. [Architecture](#architecture)
5. [Build & Flash](#build--flash)
6. [How It Works](#how-it-works)
7. [Code Layout](#code-layout)
8. [Display Pipeline](#display-pipeline)
9. [Rendering Engine](#rendering-engine)
10. [Input Handling](#input-handling)
11. [Design Principles](#design-principles)
12. [File Reference](#file-reference)
13. [Debugging](#debugging)

---

## What This Does

This is the ESP32-S3 port of the Dilder mood-selector — the same octopus character, 16 emotional states, 823 quotes, and animated expressions that run on the Pico W, now running on the Olimex ESP32-S3-DevKit-Lipo.

The octopus has:
- **16 moods**: Sassy, Weird, Unhinged, Angry, Sad, Chaotic, Hungry, Tired, Slaphappy, Lazy, Fat, Chill, Creepy, Excited, Nostalgic, Homesick
- **17 mouth expressions** with 4-frame animation cycles per mood
- **16 eye/pupil variations** with mood-specific eyebrows, eyelids, and tears
- **Body animation transforms** (oscillation, wobble, expansion per mood)
- **823 mood-filtered quotes** in chat bubbles
- **Joystick navigation** + serial keyboard control

---

## Hardware Setup

### Board: Olimex ESP32-S3-DevKit-Lipo

| Spec | Value |
|------|-------|
| MCU | ESP32-S3 (dual-core Xtensa LX7 @ 240MHz) |
| Flash | 8MB QSPI |
| PSRAM | 8MB OPI |
| WiFi | 802.11 b/g/n |
| Bluetooth | BLE 5.0 |
| USB | USB-OTG (native) + USB-UART (CH340X) |
| Battery | LiPo via JST, onboard charger |

### Pin Connections

| Signal | GPIO | Connection |
|--------|------|------------|
| EPD CLK | 12 | Display SPI clock |
| EPD DIN (MOSI) | 11 | Display SPI data |
| EPD CS | 10 | Display chip select |
| EPD DC | 9 | Display data/command |
| EPD RST | 3 | Display reset |
| EPD BUSY | 8 | Display busy signal |
| Joystick UP | 4 | Active LOW, internal pull-up |
| Joystick DOWN | 7 | Active LOW, internal pull-up |
| Joystick LEFT | 1 | Active LOW, internal pull-up |
| Joystick RIGHT | 2 | Active LOW, internal pull-up |
| Joystick CENTER | 15 | Active LOW, internal pull-up |
| Battery ADC | 6 | Voltage divider (4.133x) |
| USB Power ADC | 5 | Voltage divider (1.468x) |
| LED | 38 | Green LED (active LOW) |

---

## Project Structure

```
ESP Protyping/dilder-esp32/
├── platformio.ini              Build config (board, libs, flags)
├── src/
│   ├── main.cpp                Full mood-selector firmware (666 lines)
│   └── quotes.h                Auto-generated quote database (823 entries)
├── README.md                   This file
└── .gitignore                  Excludes .pio/ build cache

Shared firmware headers (included via -I flag):
firmware/
├── include/
│   └── platform/
│       ├── board_config.h      Pin definitions per board (Pico/ESP32/Desktop)
│       └── hal.h               Hardware Abstraction Layer interface
└── src/
    └── platform/
        └── esp32s3/
            └── esp32s3_hal.cpp  ESP32-S3 HAL implementation
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              main.cpp (Arduino)              │
│                                             │
│  setup() → init HAL, SPI, display, RNG      │
│  loop()  → render frame, poll input, repeat │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │      Octopus Rendering Engine       │    │
│  │  (body RLE, eyes, mouth, bubble,    │    │
│  │   font, animation transforms)       │    │
│  │  → renders to frame[] buffer        │    │
│  └───────────────┬─────────────────────┘    │
│                  │                           │
│  ┌───────────────▼─────────────────────┐    │
│  │         GxEPD2 Display Push         │    │
│  │  display.drawBitmap(frame)          │    │
│  │  Full refresh → Partial refresh     │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │         Input Handler               │    │
│  │  Joystick (hal_btn_*) + Serial      │    │
│  │  Edge detection for button presses  │    │
│  └─────────────────────────────────────┘    │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│          HAL (Hardware Abstraction)          │
│                                             │
│  hal.h         → function declarations      │
│  board_config.h → pin numbers per board     │
│  esp32s3_hal.cpp → Arduino GPIO/SPI impl    │
└─────────────────────────────────────────────┘
```

---

## Build & Flash

### Prerequisites

- PlatformIO CLI (`pipx install platformio`)
- USB-UART cable connected to the Olimex board's CH340X port

### Commands

```bash
cd "ESP Protyping/dilder-esp32"

# Build
pio run

# Build + Flash
pio run -t upload

# Serial Monitor
pio device monitor

# All three
pio run -t upload && pio device monitor
```

Or use the DevTool GUI: select the "Flash Firmware" tab → ESP32-S3 board.

---

## How It Works

### Frame Cycle

Each iteration of `loop()`:

1. **Select expression** — look up the 4-frame mouth cycle for the current mood, pick the expression for this frame index
2. **Pick quote** — if mood changed or mouth is "open", randomly select a new quote from the current mood's pool
3. **Render to framebuffer** — `render_frame()` draws everything to the `frame[]` byte array:
   - Clock header (synthetic time from millis())
   - Body (RLE-decoded with animation transforms)
   - Eyes (white sockets cleared in body)
   - Pupils (mood-specific shapes)
   - Eyebrows/eyelids/tears (mood-specific overlays)
   - Mouth expression (one of 17 styles)
   - Chat bubble outline + speech tail
   - Quote text (word-wrapped in bubble)
   - Status bar ("< MOOD_NAME >")
4. **Push to display** — `push_frame_to_display()` sends the framebuffer to the e-paper via GxEPD2
5. **Poll input** — wait 4 seconds, checking joystick + serial every 50ms
6. **Repeat**

### Mood Selection

- **Joystick LEFT/RIGHT**: cycle through 16 moods sequentially
- **Joystick CENTER**: jump to a random mood
- **Joystick UP**: pick a new quote (same mood)
- **Serial keyboard**: single-letter shortcuts (n=Sassy, w=Weird, etc.)

---

## Code Layout

### main.cpp — Section Map

| Lines | Section | What It Contains |
|-------|---------|-----------------|
| 1-30 | Headers | Arduino, GxEPD2, HAL includes |
| 31-75 | Constants | Mood/expression enums, names, framebuffer |
| 76-100 | Pixel helpers | `px_set`, `px_clr`, `px_set_off`, `px_clr_off` |
| 101-115 | Quotes | `#include "quotes.h"` |
| 116-200 | Body data | RLE-encoded octopus body + 5x7 font |
| 200-260 | Drawing | `fill_circle`, `draw_body_transformed`, `draw_eyes` |
| 260-520 | Eyes/Pupils | 16 mood-specific pupil functions + eyebrows/tears |
| 520-750 | Mouths | 17 mouth expression functions |
| 750-830 | Bubble/Text | Chat bubble outline, text rendering with word wrap |
| 830-870 | Clock | millis()-based synthetic clock header |
| 870-930 | Animation | Body transform setup per mood |
| 930-950 | Status bar | "< MOOD >" at bottom of screen |
| 950-1050 | Cycles | 16 mouth animation cycle tables |
| 1050-1100 | Render | `render_frame()` — composites all layers |
| 1100-1140 | Display | `push_frame_to_display()` — GxEPD2 bitmap push |
| 1140-1180 | Setup | Arduino `setup()` — init HAL, SPI, display |
| 1180-end | Loop | Arduino `loop()` — render, poll input, repeat |

---

## Display Pipeline

### Pico W vs ESP32-S3

Both use the same 250x122 framebuffer, but push pixels differently:

| Step | Pico W | ESP32-S3 |
|------|--------|----------|
| Render | → `frame[3904]` | → `frame[3904]` (identical) |
| Transform | `transpose_to_display()` (landscape→portrait) | Not needed (GxEPD2 handles rotation) |
| Push | `EPD_Display(display_buf)` / `EPD_Partial()` | `display.drawBitmap(0,0,frame,250,122,BLACK)` |
| Driver | Waveshare C driver (SSD1680 registers) | GxEPD2 Arduino library (same SSD1680) |

### Framebuffer Format

```
frame[3904 bytes] = 250 x 122 pixels, 1 bit per pixel

Bit layout: MSB-first per byte
  Byte: [b7][b6][b5][b4][b3][b2][b1][b0]
         ^leftmost pixel          ^rightmost

  1 = black pixel, 0 = white pixel

To set pixel (x, y):
  frame[y * 32 + x / 8] |= (0x80 >> (x & 7));
```

---

## Rendering Engine

### Body (RLE Encoding)

The octopus body is stored as Run-Length Encoded spans:

```
Format: y, num_spans, x_start, x_end, [x_start, x_end, ...], ...
Terminator: 0xFF

Example: 55,5, 10,17, 21,28, 32,39, 43,50, 54,61
  → Row 55 has 5 horizontal spans:
    pixels 10-17, 21-28, 32-39, 43-50, 54-61
  → These are the tentacles splitting from the body
```

### Eyes

Eyes are drawn in three layers:
1. **Sockets** — white circles cleared from the black body (`fill_circle(..., 0)`)
2. **Pupils** — black dots/shapes drawn inside the sockets (mood-specific)
3. **Overlays** — eyebrows (angry/sad), eyelids (tired/lazy), tears (homesick)

### Mouth

17 distinct mouth expressions using math curves:
- **Smirk**: tilted arc (sqrt curve)
- **Smile**: parabola (y = x^2 / 25)
- **Open**: elliptical outline (ellipse edge detection)
- **Weird**: sine wave (3 periods)
- **Unhinged**: large ellipse with teeth
- **Angry/Sad**: inverted/normal parabolas
- **Chaotic**: zigzag
- **Hungry**: open ellipse with drool
- And more...

### Animation

Each mood has a 4-frame mouth cycle and body transform:
- **body_dx/dy**: position offset (breathing, bouncing)
- **body_x_expand**: width change (puffing up, shrinking)
- **wobble_amp/freq/phase**: per-row sine wobble (wavy effects)

---

## Input Handling

### Edge Detection

Buttons are active-LOW (pressed = GPIO reads LOW). The HAL inverts this so `hal_btn_up()` returns `true` when pressed.

To detect a new press (not a held button), we compare current vs previous state:

```cpp
if (left && !last_left) {
    // Button was just pressed (rising edge)
    // Do something
}
last_left = left;  // Remember for next iteration
```

This prevents the mood from cycling continuously while the button is held.

---

## Design Principles

1. **Shared rendering engine** — the octopus drawing code is identical between Pico W and ESP32-S3. Same pixel math, same framebuffer layout, same visual output.

2. **Platform abstraction** — `hal.h` defines a common interface. Each board implements it differently (`esp32s3_hal.cpp` uses Arduino, Pico uses the Pico SDK). Application code never touches hardware registers directly.

3. **Compile-time board selection** — `board_config.h` uses `#if defined(BOARD_ESP32S3)` to select pin numbers at compile time. No runtime overhead, no unused code.

4. **No dynamic allocation** — all buffers are statically allocated. The framebuffer, body RLE data, font, and quote database are all compile-time constants. No `malloc()`, no fragmentation risk.

5. **Arduino framework** — used for the ESP32 build because it provides mature SPI, GPIO, and serial APIs plus the GxEPD2 display library. The Pico build uses the native Pico SDK for lower overhead.

---

## File Reference

| File | Location | Lines | Purpose |
|------|----------|-------|---------|
| `main.cpp` | `src/` | ~666 | Complete mood-selector with octopus rendering |
| `quotes.h` | `src/` | ~827 | 823 auto-generated mood-indexed quotes |
| `platformio.ini` | root | 56 | PlatformIO build configuration |
| `board_config.h` | `firmware/include/platform/` | ~120 | Pin definitions for Pico W / ESP32 / Desktop |
| `hal.h` | `firmware/include/platform/` | ~75 | Hardware abstraction interface |
| `esp32s3_hal.cpp` | `firmware/src/platform/esp32s3/` | ~130 | ESP32-S3 GPIO/SPI/ADC implementation |

---

## Debugging

### Serial Monitor

```bash
pio device monitor
```

Every frame prints: `Frame N | < MOOD > (X/16) | "QUOTE TEXT"`

### Common Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| Display blank | SPI pins wrong | Check `board_config.h` GPIO mapping |
| Display shows noise | Wrong GxEPD2 class | Must be `GxEPD2_213_BN` for V3 |
| Joystick not responding | Pull-ups missing | `dilder_hal_init()` sets `INPUT_PULLUP` |
| Build fails: `Arduino.h not found` | IDE error, not real | PlatformIO resolves this at build time |
| Quotes not showing | `quotes.h` missing | Copy from `dev-setup/mood-selector/quotes.h` |
| Flash too slow | Wrong upload port | Set `upload_port` in `platformio.ini` |

### Adding printf Debugging

```cpp
Serial.printf("[DEBUG] mood=%d frame=%lu\n", current_mood, frame_idx);
```

Output appears in `pio device monitor` or the DevTool serial tab.
