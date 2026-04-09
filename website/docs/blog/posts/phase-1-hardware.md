---
date: 2026-04-09
authors:
  - rompasaurus
categories:
  - Hardware
slug: phase-1-hardware-begins
---

# Phase 1: Hardware — Components Ordered, Test Bench Planned

The planning phase is done. The orders are placed. Phase 1 begins when the first package lands.

<!-- more -->

## What Was Ordered

| Item | Cost | Notes |
|------|------|-------|
| Raspberry Pi Zero WH | ~€15 | Pre-soldered 40-pin header |
| Waveshare 2.13" e-Paper HAT V3 | ~€15 | SSD1680 driver, 250×122px |
| Micro SD card (32GB) | ~€6 | For Raspberry Pi OS Lite |
| Micro-USB power supply (5V 2.5A) | ~€9 | Any decent phone charger |
| Half-size breadboard | ~€4 | Prototyping button wiring |
| Jumper wire kit (M-F, M-M) | ~€4 | Assorted lengths |
| 6×6mm tactile buttons (×20) | ~€3 | With snap-on caps |
| **Total** | **~€56** | |

## The Test Bench Plan

The test bench is just a Pi Zero WH with the e-ink HAT plugged directly onto the header, and five tactile buttons wired to GPIOs on a half-size breadboard with jumper wires.

No soldering, no permanent connections. Just enough to confirm everything works before committing to a final layout.

**Display pin mapping:**

| E-Paper Pin | BCM GPIO |
|-------------|----------|
| VCC | 3.3V (Pin 1) |
| GND | GND (Pin 6) |
| DIN | GPIO 10 (MOSI) |
| CLK | GPIO 11 (SCLK) |
| CS | GPIO 8 (CE0) |
| DC | GPIO 25 |
| RST | GPIO 17 |
| BUSY | GPIO 24 |

**Button GPIO assignments:**

| Button | BCM GPIO |
|--------|----------|
| Up | GPIO 5 |
| Down | GPIO 6 |
| Left | GPIO 13 |
| Right | GPIO 19 |
| Center / Select | GPIO 26 |

## Phase 1 Goals

- [ ] Flash Pi Zero with Raspberry Pi OS Lite (headless)
- [ ] First SSH connection
- [ ] Enable SPI interface
- [ ] Plug HAT onto header, verify display initializes
- [ ] Run Waveshare demo script — confirm display renders
- [ ] Wire 5 buttons on breadboard
- [ ] Write button test script — confirm all 5 inputs register
- [ ] Display a custom image or text as proof-of-life

When all eight bullets are checked, Phase 1 is complete and Phase 2 (firmware scaffold) begins.

## Setup Guide

The full step-by-step setup process is in the docs:

[Pi Zero Setup Guide :material-arrow-right:](../../docs/setup/pi-zero-setup.md){ .md-button }
[Display Setup Guide :material-arrow-right:](../../docs/setup/display-setup.md){ .md-button }
