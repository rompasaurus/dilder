---
date: 2026-04-09
authors:
  - rompasaurus
categories:
  - Hardware
slug: phase-1-hardware-begins
---

# Phase 1: Hardware — Pico W + E-Ink, Let's Go

The planning phase is done. We've got hardware on the bench. Phase 1 begins now.

<!-- more -->

## The Hardware

We're starting with what's on hand: a **Raspberry Pi Pico W** and a **Waveshare 2.13" e-Paper HAT V3**. The original plan called for a Pi Zero WH, but the Pico W is cheaper, boots instantly, and is perfect for prototyping the display and input system. The Pi Zero upgrade is planned for Phase 5 when we need Linux.

| Item | Notes |
|------|-------|
| Raspberry Pi Pico W | RP2040 dual-core, 264KB SRAM, WiFi + BLE, ~€6 |
| Waveshare 2.13" e-Paper HAT V3 | SSD1680 driver, 250×122px, ~€15 |
| Micro-USB cable | Power + data |
| Half-size breadboard | Prototyping |
| Jumper wire kit (M-F, M-M) | Display HAT connects via jumper wires, not the 40-pin header |
| 6×6mm tactile buttons (×20) | With snap-on caps |

## The Test Bench Plan

The Pico W sits on a breadboard. The e-ink display connects via 8 jumper wires from the HAT's side header to the Pico W's SPI1 pins. Five tactile buttons wire to GPIOs with internal pull-ups.

No soldering, no permanent connections. Just enough to confirm everything works before committing to a final layout.

**Display pin mapping (Pico W SPI1):**

| E-Paper Pin | Pico W GPIO | Pin # |
|-------------|-------------|-------|
| VCC | 3V3(OUT) | 36 |
| GND | GND | 38 |
| DIN | GP11 (SPI1 TX) | 15 |
| CLK | GP10 (SPI1 SCK) | 14 |
| CS | GP9 (SPI1 CSn) | 12 |
| DC | GP8 | 11 |
| RST | GP12 | 16 |
| BUSY | GP13 | 17 |

**Button GPIO assignments:**

| Button | Pico W GPIO | Pin # |
|--------|-------------|-------|
| Up | GP2 | 4 |
| Down | GP3 | 5 |
| Left | GP4 | 6 |
| Right | GP5 | 7 |
| Center / Select | GP6 | 9 |

## Phase 1 Goals

- [ ] Flash MicroPython firmware onto Pico W
- [ ] Set up VSCode with MicroPico extension on Linux
- [ ] Wire display to Pico W via jumper wires
- [ ] Run Waveshare demo script — confirm display renders
- [ ] Wire 5 buttons on breadboard
- [ ] Write button test script — confirm all 5 inputs register
- [ ] Display a custom image or text as proof-of-life

When all seven bullets are checked, Phase 1 is complete and Phase 2 (firmware scaffold) begins.

## Setup Guides

The full step-by-step setup process is in the docs:

[Pico W Setup Guide :material-arrow-right:](../../docs/setup/pi-zero-setup.md){ .md-button }
[Display Setup Guide :material-arrow-right:](../../docs/setup/display-setup.md){ .md-button }
[Dev Environment Guide :material-arrow-right:](../../docs/setup/dev-environment.md){ .md-button }
