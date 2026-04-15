---
date: 2026-04-15
authors:
  - rompasaurus
categories:
  - Hardware
  - Build Guide
slug: breadboard-prototype-guide
---

# Build a Dilder on a Breadboard — Parts, Wiring, and Alpha Board Plans

You don't need to wait for the custom PCB. Here's how to build a working Dilder prototype on a breadboard using off-the-shelf parts, with shopping lists for both EU and US builders.

<!-- more -->

## Choosing a Dev Board

The custom PCB runs an ESP32-S3-WROOM-1-N16R8. For breadboard prototyping, you need a dev board with the same chip (or close enough) and at least 18 free GPIO pins. We evaluated seven options:

**Budget pick: Olimex ESP32-S3-DevKit-Lipo** (7.95 EUR) — has LiPo charging built in, eliminating the TP4056 module entirely. Open-source hardware. Ships from Bulgaria.

**Best silicon match: Generic N16R8 DevKitC** (10-14 EUR) — exact same ESP32-S3-WROOM-1-N16R8 module as the custom PCB. Firmware ports without changes.

**Cleanest prototype: Unexpected Maker FeatherS3** (28.98 EUR) — Feather ecosystem lets you stack an eInk FeatherWing directly. Battery charging, STEMMA QT I2C connector, exact 16MB/8MB match.

One important note: the Seeed XIAO ESP32S3 at 7.50 EUR looks tempting, but it only exposes 11 GPIO pins. Not enough for our circuit.

## The Parts List

| # | Component | Purpose | Price Range |
|---|-----------|---------|-------------|
| 1 | ESP32-S3 dev board | MCU | 8-29 EUR |
| 2 | Waveshare 2.13" e-Paper (V4) | Display | 8-18 EUR |
| 3 | Adafruit LIS3DH breakout | Accelerometer | 5-6 EUR |
| 4 | 5-way navigation joystick | Input | 2-8 EUR |
| 5 | LiPo battery (1000mAh, JST PH) | Power | 6-10 EUR |
| 6 | TP4056 USB-C module | Charging | 1.40-5.50 EUR |
| 7 | Full-size breadboard (830 pts) | Platform | 4-8 EUR |
| 8 | Jumper wire kit (M-M + F-M) | Wiring | 4-8 EUR |
| 9 | 2x 10k resistors | I2C pull-ups | <1 EUR |

**Total: 40-85 EUR** depending on dev board and what you already have. Skip the TP4056 if your dev board has built-in charging.

## GPIO Wiring — Matches the Custom PCB

The pin assignments are identical to the custom board, so firmware ports directly:

- **SPI (e-Paper):** GPIO9 (CLK), GPIO10 (MOSI), GPIO46 (CS), GPIO3 (DC), GPIO11 (RST), GPIO12 (BUSY)
- **I2C (accelerometer):** GPIO16 (SDA), GPIO17 (SCL), GPIO18 (INT1)
- **Joystick:** GPIO4-8 (UP, DOWN, LEFT, RIGHT, CENTER) with internal pull-ups
- **USB:** GPIO19 (D-), GPIO20 (D+)

The display connects through an 8-pin breakout header using female-to-male jumper wires. Everything else plugs directly into the breadboard.

## Shopping by Region

We put together sourcing lists for both Germany and the US, covering Mouser, Reichelt, Botland, exp-tech.de, Amazon, Adafruit, and DigiKey. The full lists with links are in the [Breadboard Prototype Guide](../../docs/design/breadboard-prototype.md) in the docs section. Prices vary by region, but the budget build comes in under 50 EUR/USD either way.

## Beyond the Breadboard — Alpha Board Plans

A breadboard prototype works for firmware development, but it's not something you can carry around. We explored three "alpha board" options for making a portable prototype before the custom PCB arrives:

### Option A: Feather Stack

Use a FeatherS3 dev board with an Adafruit 2.13" Mono eInk FeatherWing stacked on top. The FeatherWing plugs directly into the Feather headers — no wiring needed for the display. Add the LIS3DH breakout via the STEMMA QT connector and the joystick with a few jumper wires. Compact, clean, and the closest thing to a finished product you can get without a custom PCB.

### Option B: Protoboard Solder Build

Solder the dev board, display, and peripherals onto a half-size protoboard (50x70mm). Permanent connections, no jumper wires to fall out. Takes about 2 hours with a soldering iron. Durable enough to carry in a pocket.

### Option C: 3D-Printed Bracket

Design a bracket that holds the breadboard, display, and battery in a fixed arrangement. Quick to iterate on if you already have a 3D printer. Less portable than the protoboard build but easier to modify.

## What's Next

The breadboard prototype is the testbed for all firmware development until the custom PCB arrives from JLCPCB. Every driver, every animation, every game loop gets validated on this setup first. If it works on the breadboard, it'll work on the board.

Pick your parts, wire it up, and flash the octopus. The full guide with exact wiring diagrams is in the [hardware design docs](../../docs/hardware/wiring-pinout.md).
