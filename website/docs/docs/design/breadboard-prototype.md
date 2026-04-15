# Breadboard Prototype Guide

> Build a working Dilder on a breadboard using off-the-shelf ESP32-S3 dev boards. Same GPIO assignments as the custom PCB — firmware ports directly.

---

## Dev Board Options

Pick an ESP32-S3 dev board with at least 18 free GPIO pins.

| Board | Price | Flash/PSRAM | Battery Charging | Best For |
|-------|-------|-------------|-----------------|----------|
| **Olimex ESP32-S3-DevKit-Lipo** | **7.95 EUR** | 8MB/8MB | **Yes** (built-in) | Best value, skip TP4056 |
| Waveshare ESP32-S3 N8R8 | 10.50 EUR | 8MB/8MB | No | Cheap, widely stocked |
| Generic N16R8 DevKitC | 8-14 EUR | **16MB/8MB** | No | Exact PCB silicon match |
| **UM FeatherS3** | **28.98 EUR** | **16MB/8MB** | **Yes** (JST + fuel gauge) | Feather ecosystem, cleanest |
| Adafruit ESP32-S3 Feather | 22.96 EUR | 4MB/2MB | **Yes** | Budget Feather option |

!!! warning "Not enough GPIO"
    The Seeed XIAO ESP32S3 (7.50 EUR) only exposes 11 GPIO pins — not enough for the Dilder circuit.

### Recommendations

- **Budget pick:** Olimex ESP32-S3-DevKit-Lipo — LiPo charging built in, open-source hardware
- **Best PCB match:** Generic N16R8 DevKitC — same ESP32-S3-WROOM-1-N16R8 module
- **Cleanest prototype:** UM FeatherS3 — Feather ecosystem, stack the eInk FeatherWing directly

---

## Parts List

| # | Component | Purpose | Est. Price | Notes |
|---|-----------|---------|------------|-------|
| 1 | ESP32-S3 dev board | Main MCU | 8-29 EUR | See comparison above |
| 2 | Waveshare 2.13" e-Paper (V4, SSD1680) | Display | 8-18 EUR | 8-pin breakout header with F-M jumper wires |
| 3 | Adafruit LIS3DH breakout | Accelerometer | 5-6 EUR | Pin-compatible stand-in for LIS2DH12 |
| 4 | 5-way navigation joystick | Input | 2-8 EUR | Through-hole; Adafruit ADA504 or DollaTek |
| 5 | LiPo battery (1000-1200mAh, JST PH 2.0mm) | Power | 6-10 EUR | Verify polarity matches dev board |
| 6 | TP4056 USB-C module | Battery charging | 1.40-5.50 EUR | **Skip if dev board has charging** |
| 7 | Full-size breadboard (830 pts) | Prototyping | 4-8 EUR | Half-size is too small |
| 8 | Jumper wire kit (M-M + F-M) | Wiring | 4-8 EUR | ~15 M-M, ~10 F-M for display |
| 9 | 2x 10k resistors | I2C pull-ups | <1 EUR | Skip if accel breakout has onboard pull-ups |

**Total: 40-85 EUR** depending on dev board and what you already have.

---

## GPIO Wiring Map

Same pin assignments as the custom PCB — firmware ports directly.

```
ESP32-S3 GPIO  ->  Component            ->  Notes
---------------------------------------------------
GPIO3          ->  e-Paper DC            ->  Display pin 6
GPIO4          ->  Joystick UP           ->  Internal pull-up
GPIO5          ->  Joystick DOWN         ->  Internal pull-up
GPIO6          ->  Joystick LEFT         ->  Internal pull-up
GPIO7          ->  Joystick RIGHT        ->  Internal pull-up
GPIO8          ->  Joystick CENTER       ->  Internal pull-up
GPIO9          ->  e-Paper CLK (SCK)     ->  Display pin 4
GPIO10         ->  e-Paper MOSI (DIN)    ->  Display pin 3
GPIO11         ->  e-Paper RST           ->  Display pin 7
GPIO12         ->  e-Paper BUSY          ->  Display pin 8
GPIO16         ->  Accelerometer SDA     ->  I2C data
GPIO17         ->  Accelerometer SCL     ->  I2C clock
GPIO18         ->  Accelerometer INT1    ->  Step/tap interrupt
GPIO46         ->  e-Paper CS            ->  Display pin 5
3V3            ->  Display VCC, Accel VCC
GND            ->  Display GND, Accel GND, Joystick COM
```

---

## Compact Alpha Board Options

For portable prototyping before the custom PCB arrives:

### Option A: Feather Stack (Recommended)

Use a FeatherS3 with an Adafruit 2.13" Mono eInk FeatherWing stacked on top. Display connects through the Feather headers — no wiring needed. Add the LIS3DH via STEMMA QT and the joystick with a few wires.

### Option B: Protoboard Solder Build

Solder everything onto a half-size protoboard (50x70mm). Permanent connections, no jumper wires to fall out. Takes ~2 hours. Durable enough to carry in a pocket.

### Option C: 3D-Printed Bracket

Print a bracket that holds the breadboard, display, and battery in a fixed arrangement. Easy to iterate, less portable than protoboard.

---

## Key Notes

!!! tip "Polarity check"
    Always verify LiPo battery connector polarity before plugging in. Adafruit, SparkFun, and generic batteries often have reversed polarity on their JST connectors. Reversing polarity can permanently damage the dev board.

!!! info "I2C pull-ups"
    Most accelerometer breakout boards have 10k pull-ups onboard. If yours does, skip the external resistors.

!!! note "Display version"
    Make sure you get the Waveshare 2.13" e-Paper **V4** (SSD1680 driver). Earlier versions use different drivers and need different firmware.
