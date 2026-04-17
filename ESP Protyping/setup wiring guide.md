# Olimex ESP32-S3-DevKit-Lipo — Setup, Wiring & Development Guide

> Complete hands-on guide for setting up the Olimex ESP32-S3-DevKit-Lipo with the Waveshare 2.13" e-Paper V3 display and 5-way joystick for Dilder prototyping. Covers board features, pinout, breadboard wiring, VSCode + PlatformIO setup, firmware compilation, and flashing.

---

## Table of Contents

1. [Board Overview — Olimex ESP32-S3-DevKit-Lipo](#1-board-overview)
   - [1.1 Key Specifications](#11-key-specifications)
   - [1.2 What's On the Board](#12-whats-on-the-board)
   - [1.3 USB Ports — Which Is Which](#13-usb-ports--which-is-which)
   - [1.4 Buttons and LEDs](#14-buttons-and-leds)
   - [1.5 Battery Charging](#15-battery-charging)
     - [Battery Connector Details](#battery-connector-details)
     - [Compatible LiPo Battery Options](#compatible-lipo-battery-options)
   - [1.6 Power Architecture](#16-power-architecture)
   - [1.7 pUEXT Connector](#17-puext-connector)
2. [Full GPIO Pinout](#2-full-gpio-pinout)
   - [2.1 Header EXT1 (Left Side)](#21-header-ext1-left-side)
   - [2.2 Header EXT2 (Right Side)](#22-header-ext2-right-side)
   - [2.3 GPIO Restrictions and Warnings](#23-gpio-restrictions-and-warnings)
   - [2.4 Freely Available GPIO Pins](#24-freely-available-gpio-pins)
   - [2.5 Strapping Pins](#25-strapping-pins)
3. [Parts You Already Have](#3-parts-you-already-have)
4. [GPIO Assignment for Dilder](#4-gpio-assignment-for-dilder)
   - [4.1 Pin Mapping Table](#41-pin-mapping-table)
   - [4.2 Bus Summary Diagram](#42-bus-summary-diagram)
5. [Breadboard Wiring — Step by Step](#5-breadboard-wiring--step-by-step)
   - [5.1 What You Need](#51-what-you-need)
   - [5.2 Phase 1 — Board on Breadboard](#52-phase-1--board-on-breadboard)
   - [5.3 Phase 2 — Wire the Joystick](#53-phase-2--wire-the-joystick)
   - [5.4 Phase 3 — Wire the e-Paper Display](#54-phase-3--wire-the-e-paper-display)
   - [5.5 Master Wiring Diagram](#55-master-wiring-diagram)
   - [5.6 Wiring Checklist](#56-wiring-checklist)
6. [VSCode + PlatformIO Setup](#6-vscode--platformio-setup)
   - [6.1 Install PlatformIO](#61-install-platformio)
   - [6.2 Create the Project](#62-create-the-project)
   - [6.3 Configure platformio.ini](#63-configure-platformioini)
   - [6.4 USB Driver Setup (Linux)](#64-usb-driver-setup-linux)
   - [6.5 First Upload — Blink Test](#65-first-upload--blink-test)
7. [Test Sketches](#7-test-sketches)
   - [7.1 Chip Info Sketch](#71-chip-info-sketch)
   - [7.2 Battery Monitor Sketch](#72-battery-monitor-sketch)
   - [7.3 Joystick Test Sketch](#73-joystick-test-sketch)
   - [7.4 e-Paper Display Test Sketch](#74-e-paper-display-test-sketch)
   - [7.5 Combined Test — All Peripherals](#75-combined-test--all-peripherals)
8. [Compiling and Flashing Firmware](#8-compiling-and-flashing-firmware)
   - [8.1 Build from VSCode](#81-build-from-vscode)
   - [8.2 Build from Terminal](#82-build-from-terminal)
   - [8.3 Serial Monitor](#83-serial-monitor)
   - [8.4 Troubleshooting Upload Issues](#84-troubleshooting-upload-issues)
9. [Integrating with the Dilder DevTool](#9-integrating-with-the-dilder-devtool)
   - [9.1 Architecture Overview](#91-architecture-overview)
   - [9.2 Firmware Build Pipeline](#92-firmware-build-pipeline)
   - [9.3 Serial Communication Protocol](#93-serial-communication-protocol)
10. [Important Notes and Warnings](#10-important-notes-and-warnings)
11. [Resources, Documentation & Videos](#11-resources-documentation--videos)
    - [11.1 Olimex Board Resources](#111-olimex-board-resources)
    - [11.2 ESP32-S3 Resources](#112-esp32-s3-resources)
    - [11.3 Waveshare e-Paper Resources](#113-waveshare-e-paper-resources)
    - [11.4 PlatformIO & Development](#114-platformio--development)
    - [11.5 Video Tutorials](#115-video-tutorials)

---

## 1. Board Overview

![Olimex ESP32-S3-DevKit-Lipo — Angled view](https://raw.githubusercontent.com/OLIMEX/ESP32-S3-DevKit-LiPo/main/DOCUMENTS/ESP32-S3-DevKit-LiPo1w.jpg)

*Olimex ESP32-S3-DevKit-Lipo — open-source ESP32-S3 dev board with LiPo charging, dual USB-C, and 8MB PSRAM.*

### 1.1 Key Specifications

| Parameter | Value |
|-----------|-------|
| **Board** | ESP32-S3-DevKit-Lipo (Olimex) |
| **Module** | ESP32-S3-WROOM-1-N8R8 |
| **CPU** | Dual-core Xtensa LX7, up to 240 MHz |
| **Flash** | 8 MB (QIO, 80 MHz) |
| **PSRAM** | 8 MB (Octal, OPI mode) |
| **SRAM** | 512 KB internal |
| **Wi-Fi** | 2.4 GHz 802.11 b/g/n |
| **Bluetooth** | 5.0 LE |
| **Antenna** | PCB antenna (built into the module) |
| **USB** | Dual USB-C (native USB-OTG + CH340X UART) |
| **Battery** | LiPo charging built-in (BL4054B, 100 mA default) |
| **Voltage Regulator** | SY8089AAAC — 3.3V buck converter, 2A output |
| **Deep Sleep** | ~200 µA from LiPo |
| **Pin Headers** | 2x 22-pin, 2.54mm pitch (breadboard-friendly) |
| **Board Dimensions** | 27.94 x 55.88 mm (1.1" x 2.2") |
| **Logic Level** | 3.3V |
| **Price** | €7.95 each |
| **License** | CERN-OHL-S-2.0 (open-source hardware) |
| **OSHW UID** | BG0000108 |

### 1.2 What's On the Board

| Top (component side) | Bottom (silkscreen with GPIO labels) |
|---|---|
| ![Board top view](https://raw.githubusercontent.com/OLIMEX/ESP32-S3-DevKit-LiPo/main/DOCUMENTS/ESP32-S3-DevKit-LiPo2w.jpg) | ![Board bottom view — GPIO pin labels](https://raw.githubusercontent.com/OLIMEX/ESP32-S3-DevKit-LiPo/main/DOCUMENTS/ESP32-S3-DevKit-LiPo3w.jpg) |
| *Component side — USB-C ports, buttons, LEDs, pUEXT connector, battery connector* | *Bottom silkscreen — every GPIO pin labeled in white. Flip the board to read pin numbers while wiring.* |

```
    ┌──────────────────────────────────────────┐
    │  ┌─[USB-OTG]──┐    ┌─[USB-UART]──┐     │
    │  │  (native)   │    │  (CH340X)   │     │
    │  └─────────────┘    └─────────────┘     │
    │                                          │
    │  [RST]  [BOOT]    (o) GREEN LED (GPIO38) │
    │                    (o) YELLOW LED (CHG)   │
    │                                          │
    │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │
    │  ▓   ESP32-S3-WROOM-1-N8R8 Module   ▓   │
    │  ▓   (8MB Flash + 8MB PSRAM)        ▓   │
    │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │
    │                                          │
    │  [pUEXT 10-pin connector]   [BAT conn]   │
    │                                          │
    │  EXT1 (22 pins)        EXT2 (22 pins)    │
    │  ● ● ● ● ● ... ●    ● ● ● ● ● ... ●   │
    └──────────────────────────────────────────┘
```

**Key components on the PCB:**

| Component | Chip | Function |
|-----------|------|----------|
| Voltage Regulator | SY8089AAAC | 3.3V buck converter (2.7–5.5V in, 2A out) |
| Battery Charger | BL4054B-42TPRN | Li-Ion charger, 4.2V float, 100 mA charge rate |
| USB-to-Serial | CH340X | For UART upload and serial monitor |
| Power Switch | WPM2015-3/TR | P-MOSFET auto-switchover between USB and battery |
| Schottky Diodes | 3x 1N5819S4 | OR-ing between USB power sources and battery |
| Auto-Reset | 2x BC817-40 | DTR/RTS to EN/GPIO0 for automatic bootloader entry |

### 1.3 USB Ports — Which Is Which

The board has **two USB-C ports**. This is important — they do different things.

| Port | Label | Chip | What It Does |
|------|-------|------|-------------|
| **USB-OTG** | Near the module antenna end | None (native) | Direct ESP32-S3 USB. JTAG debugging, USB CDC serial, USB OTG. Uses GPIO19/GPIO20. |
| **USB-UART** | Near the buttons | CH340X | Traditional serial upload. Auto-reset into bootloader. Shows as `/dev/ttyUSB0` or `/dev/ttyACM0`. |

**Which port to use:**

- **For uploading firmware:** Use **USB-UART** (the one with the CH340X). It has auto-reset, so PlatformIO can automatically put the board into bootloader mode and flash.
- **For serial monitor:** Either port works. USB-UART gives you traditional UART serial. USB-OTG gives you USB CDC serial (requires `ARDUINO_USB_CDC_ON_BOOT=1`).
- **For JTAG debugging:** Use **USB-OTG** (native USB). Supports hardware breakpoints and step-through debugging.

**Tip:** You can have both plugged in simultaneously. USB-UART for upload + serial, USB-OTG for JTAG debug.

### 1.4 Buttons and LEDs

| Element | GPIO/Pin | Function |
|---------|---------|----------|
| **RST button** | ESP_EN | Resets the ESP32-S3. Has 10k pull-up + 1µF debounce cap. |
| **BOOT button** | GPIO0 | Hold during reset to enter bootloader (download mode). Also usable as a general-purpose user button during normal operation. |
| **Green LED** | GPIO38 | **Active LOW** — `digitalWrite(38, LOW)` turns it ON. Has 2.2k current-limiting resistor to 3.3V. |
| **Yellow LED** | BL4054B CHRGb | Lights while battery is charging. Not software-controllable. |

### 1.5 Battery Charging

The board has a built-in LiPo charger — **no external TP4056 module needed**.

| Parameter | Value |
|-----------|-------|
| Charger IC | BL4054B-42TPRN |
| Float voltage | 4.2V (±1%) |
| Charge current | 100 mA (set by R4 = 10k PROG resistor) |
| Termination | C/10 (10 mA) |
| Trickle charge | Below 2.9V |
| Connector | 2-pin JST-compatible vertical connector |
| Status LED | Yellow — ON while charging, OFF when done |

**Battery voltage monitoring:** The board has a voltage divider on **GPIO6** (470k/150k) that lets you read the battery voltage via ADC. The divider ratio is **4.133**:

```
Battery Voltage = ADC_reading × (3.3 / 4095) × 4.133
```

**External power detection:** A second voltage divider on **GPIO5** (220k/470k) lets you detect whether USB power is connected. Divider ratio: **1.468**.

**To increase charge current:** Replace R4 (the 10k PROG resistor) with a smaller value. 2k = ~500 mA, 1.65k = ~600 mA. Max is 800 mA (thermal limit of SOT23-5 package).

#### Battery Connector Details

| Parameter | Value |
|-----------|-------|
| **Connector on board** | DW02S vertical (CVILUX CI0102M1VT0-LF) |
| **Compatible plug type** | **JST PH 2.0mm, 2-pin** (standard LiPo connector) |
| **Polarity** | Pin 1 = **VBAT (+)**, Pin 2 = **GND (−)** |
| **Polarity convention** | Same as Adafruit / SparkFun / Pimoroni |

> **CRITICAL — POLARITY WARNING:** There is NO universal polarity standard for JST PH battery connectors. The Olimex board has **no reverse-polarity protection**. Connecting a battery with swapped polarity **will destroy the charger IC and possibly the ESP32-S3 module**. Always verify with a multimeter before first connection: the red wire on the battery plug must align with the **+** marking on the board's silkscreen (Pin 1 = VBAT).

#### Compatible LiPo Battery Options

> **How to read LiPo model numbers:** The model encodes dimensions as XXYYZZ where XX = thickness (×0.1mm), YY = width (mm), ZZ = length (mm). Example: **102050** = 10mm thick × 20mm wide × 50mm long. The Olimex board is 28mm wide, so batteries under 24mm wide fit within the board footprint.

**Tier 1 — Guaranteed Compatible (Olimex direct)**

Olimex's own batteries — same connector, correct polarity, no risk. Buy from [olimex.com](https://www.olimex.com/Products/Power-Supply/Lipo-battery/).

| Battery | Capacity | Dimensions (W × L × T) | Width | Price | Notes |
|---------|----------|------------------------|-------|-------|-------|
| **BATTERY-LIPO250mAh** | 250 mAh | 21 × 27 × 5 mm | 21 mm | €3.55 | Fits under board width (< 24mm). |
| **BATTERY-LIPO800mAh** | 800 mAh | 30 × 50 × 5 mm | 30 mm | €4.55 | Check stock — sometimes unavailable. |
| **BATTERY-LIPO1400mAh** | 1400 mAh | 34 × 50 × 8 mm | 34 mm | €5.95 | **Best mid-range.** Same footprint as board. |
| **BATTERY-LIPO3000mAh** | 3000 mAh | 45 × 135 × 5 mm | 45 mm | €7.95 | Very long. Good for prototyping. |
| **BATTERY-LIPO4400mAh** | 4400 mAh | 37 × 68 × 18 mm | 37 mm | €8.95 | Highest capacity. Thick. |

All include overcharge + short-circuit protection. Ships from Plovdiv, Bulgaria (3-7 days to Germany).

**Tier 2 — Confirmed Compatible (Adafruit / SparkFun / Pimoroni)**

Same JST PH 2.0mm polarity convention as Olimex. Available through European resellers.

| Battery | Capacity | Dimensions (W × L × T) | Width | Price | Source |
|---------|----------|------------------------|-------|-------|--------|
| **Pimoroni BAT0002** | 150 mAh | 20.5 × 27 × 4.3 mm | 20.5 mm | ~€3.75 | shop.pimoroni.com |
| **SparkFun PRT-13851** | 400 mAh | 25 × 37 × 5 mm | 25 mm | ~€7.20 | sparkfun.com (no intl. shipping) |
| **Pimoroni BAT0003** | 500 mAh | 30.5 × 37 × 5.3 mm | 30.5 mm | ~€6.75 | shop.pimoroni.com |
| **Adafruit LiPo 1578** | 500 mAh | 26 × 35 × 5 mm | 26 mm | ~€7.20 | adafruit.com / exp-tech.de |
| **SparkFun PRT-13854** | 850 mAh | 35 × 45 × 5 mm | 35 mm | ~€12.30 | sparkfun.com (no intl. shipping) |
| **Pimoroni BAT0004** | 1200 mAh | 35.5 × 64 × 5.3 mm | 35.5 mm | ~€9.70 | shop.pimoroni.com |
| **Adafruit LiPo 328** | 2500 mAh | 50 × 60 × 7.3 mm | 50 mm | ~€13.50 | adafruit.com / exp-tech.de |

**Note:** SparkFun and Adafruit do not ship lithium batteries internationally. Use European resellers like exp-tech.de, The Pi Hut, or Pimoroni for delivery to Germany.

**Tier 3 — Compatible, Verify Polarity (German retailers)**

JST PH 2.0mm connectors but polarity not always documented. **Test with a multimeter before plugging in.**

| Battery | Capacity | Dimensions (W × L × T) | Width | Price | Source |
|---------|----------|------------------------|-------|-------|--------|
| **BerryBase LP-503035** | 500 mAh | 30 × 35.5 × 5 mm | 30 mm | €5.10 | berrybase.de |
| **Eckstein-Shop LP503035** | 500 mAh | 30 × 35.5 × 5 mm | 30 mm | €5.19 | eckstein-shop.de |
| **BerryBase LP-503562** | 1200 mAh | 36 × 62.5 × 5 mm | 36 mm | €5.50 | berrybase.de |
| **Eckstein-Shop LP503562** | 1200 mAh | 36 × 62.5 × 5 mm | 36 mm | €6.97 | eckstein-shop.de |
| **BerryBase LP-785060** | 2500 mAh | 50 × 60.5 × 7.8 mm | 50 mm | €7.70 | berrybase.de |

**Tier 4 — Narrow Cells (< 24mm wide, fits under the board)**

These are the only 1000+ mAh batteries that fit within the Olimex board's 28mm width. The **102050** cell format is the sweet spot. Most ship with JST PH 2.0mm but **always verify polarity with a multimeter** — Amazon/generic sellers have ~50% chance of reversed wiring.

| Battery | Capacity | Dimensions (W × L × T) | Width | Price | Connector | Source |
|---------|----------|------------------------|-------|-------|-----------|--------|
| **102050 (YDL)** | 1000 mAh | 20 × 50 × 10 mm | **20 mm** | ~$2.80 | JST-PH 2.0mm | ydlbattery.com |
| **102050 (AKZYTUE)** | 1000 mAh | 20 × 50 × 10 mm | **20 mm** | ~€8-10 | JST-PH 2.0mm | Amazon (B0GHR4GJK8) |
| **102050 (MakerHawk)** | 1000 mAh | 20 × 50 × 10 mm | **20 mm** | ~€8-12 | JST-PH 2.0mm | Amazon (B0D9K7HQHT) |
| **102050 (Ampul.eu)** | 1000 mAh | 20 × 50 × 10 mm | **20 mm** | €7.18 | Verify before buying | ampul.eu |
| **102060** | 1300 mAh | 20 × 60 × 10 mm | **20 mm** | ~€4-8 | Varies — check listing | eBay (115955049826) |
| **LP102250** | 1200 mAh | 22 × 50 × 10 mm | **22 mm** | ~€5-8 | 3-pin JST (needs swap) | li-polymer-battery.com |

> **Warning — Amazon generics:** Many listings say "Micro JST 2.0" but some ship with **Micro JST 1.25mm** (different connector — does NOT fit). Read each listing description carefully. The YDL and AKZYTUE listings explicitly confirm 2.0mm pitch.

**Tier 5 — HIGH RISK (unbranded Amazon / AliExpress)**

| Battery | Capacity | Dimensions (W × L × T) | Width | Price | Risk |
|---------|----------|------------------------|-------|-------|------|
| Generic "3.7V LiPo JST PH" | 1000-3000 mAh | Varies wildly | 20-60 mm | €5-12 | **~50% polarity reversal, dimensions often wrong** |

To swap reversed JST PH pins: use a fine needle to lift the locking tab on each pin inside the housing, pull the wire out, and reinsert in the correct order.

#### All Batteries — Master Size Comparison

Sorted by width (narrowest first). **Bold** = fits under the board (< 24mm wide).

| Battery | mAh | Width | Length | Thick | Fits < 24mm? | Price | Polarity |
|---------|-----|-------|--------|-------|--------------|-------|----------|
| **102050 (any brand)** | **1000** | **20 mm** | **50 mm** | **10 mm** | **YES** | **€3-10** | **Verify** |
| **102060** | **1300** | **20 mm** | **60 mm** | **10 mm** | **YES** | **€4-8** | **Verify** |
| Pimoroni BAT0002 | 150 | 20.5 mm | 27 mm | 4.3 mm | **YES** | ~€3.75 | Confirmed |
| Olimex 250mAh | 250 | 21 mm | 27 mm | 5 mm | **YES** | €3.55 | Guaranteed |
| **LP102250** | **1200** | **22 mm** | **50 mm** | **10 mm** | **YES** | **€5-8** | **Verify** |
| SparkFun PRT-13851 | 400 | 25 mm | 37 mm | 5 mm | No | ~€7.20 | Confirmed |
| Adafruit LiPo 1578 | 500 | 26 mm | 35 mm | 5 mm | No | ~€7.20 | Confirmed |
| Olimex 800mAh | 800 | 30 mm | 50 mm | 5 mm | No | €4.55 | Guaranteed |
| BerryBase LP-503035 | 500 | 30 mm | 35.5 mm | 5 mm | No | €5.10 | Verify |
| Pimoroni BAT0003 | 500 | 30.5 mm | 37 mm | 5.3 mm | No | ~€6.75 | Confirmed |
| Olimex 1400mAh | 1400 | 34 mm | 50 mm | 8 mm | No | €5.95 | Guaranteed |
| SparkFun PRT-13854 | 850 | 35 mm | 45 mm | 5 mm | No | ~€12.30 | Confirmed |
| Pimoroni BAT0004 | 1200 | 35.5 mm | 64 mm | 5.3 mm | No | ~€9.70 | Confirmed |
| BerryBase LP-503562 | 1200 | 36 mm | 62.5 mm | 5 mm | No | €5.50 | Verify |
| Eckstein LP503562 | 1200 | 36 mm | 62.5 mm | 5 mm | No | €6.97 | Verify |
| Olimex 4400mAh | 4400 | 37 mm | 68 mm | 18 mm | No | €8.95 | Guaranteed |
| Olimex 3000mAh | 3000 | 45 mm | 135 mm | 5 mm | No | €7.95 | Guaranteed |
| BerryBase LP-785060 | 2500 | 50 mm | 60.5 mm | 7.8 mm | No | €7.70 | Verify |
| Adafruit LiPo 328 | 2500 | 50 mm | 60 mm | 7.3 mm | No | ~€13.50 | Confirmed |

#### Recommended Battery for Dilder Prototyping

**Best narrow fit (< 24mm wide): 102050 cell — 1000 mAh (20 × 50 × 10 mm)**
- Fits under the Olimex board with 4mm clearance per side
- 1000 mAh = ~10+ hours of Dilder runtime (display + joystick, no WiFi)
- JST PH 2.0mm connector on most listings — plugs straight in
- Buy from YDL Battery ($2.80 direct) or Amazon (€8-10 with Prime)
- **Always verify polarity with a multimeter before connecting**

**Best guaranteed-safe pick: Olimex BATTERY-LIPO1400mAh (€5.95)**
- No polarity risk — guaranteed compatible
- 1400 mAh, 34 × 50 × 8 mm (wider than the board but fine for breadboard prototyping)
- Ships from the same company that makes the board
- At 100 mA charge rate, full charge takes ~14 hours (upgrade R4 to 2k for ~500 mA / 3-hour charge)

### 1.6 Power Architecture

![ESP32-S3 DevKit System Block Diagram](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/_images/ESP32-S3-DevKitC-1_v2-SystemBlock.png)

*System block diagram (Espressif DevKitC-1 — same architecture as the Olimex board). Source: Espressif.*

```
USB-OTG (5V) ──D3──┐
                    ├──> +5V rail ──> SY8089AAAC ──> 3.3V rail ──> ESP32-S3 + peripherals
USB-UART (5V) ─D1──┘                                   │
                                                    BL4054B ──> LiPo Battery
LiPo Battery ──D2──> P-FET ──> SY8089 input            │
                       │                            (charges when USB connected)
                    (FET OFF when USB present,
                     FET ON when on battery)
```

When USB is connected, the P-MOSFET disconnects the battery from the power path and the charger tops it up. When USB is removed, the FET conducts and the battery powers everything through the buck regulator.

### 1.7 pUEXT Connector

The board has a 10-pin JST SH 1.0mm pitch connector (pUEXT) that breaks out UART, I2C, and SPI:

| Pin | Signal | GPIO | Notes |
|-----|--------|------|-------|
| 0 | GND | — | |
| 1 | 3.3V | — | |
| 2 | GND | — | |
| 3 | UART1 TX | GPIO17 | |
| 4 | UART1 RX | GPIO18 | |
| 5 | I2C SCL | GPIO47 | 2.2k pull-up to 3.3V on board |
| 6 | I2C SDA | GPIO48 | 2.2k pull-up to 3.3V on board |
| 7 | SPI MISO | GPIO13 | |
| 8 | SPI MOSI | GPIO11 | |
| 9 | SPI CLK | GPIO12 | |
| 10 | SPI CS0 | GPIO10 | 10k pull-up to 3.3V on board |

This connector is compatible with Olimex UEXT breakout modules. The I2C lines on GPIO47/48 already have 2.2k pull-ups on the board, so **no external pull-ups are needed if you use these pins for I2C**.

---

## 2. Full GPIO Pinout

> **Note:** The Olimex board's header pinout is fully compatible with the Espressif ESP32-S3-DevKitC-1. The Espressif pinout diagram below is an accurate reference for the GPIO assignments on both boards.

![ESP32-S3-DevKitC-1 Pinout Diagram](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/_images/ESP32-S3_DevKitC-1_pinlayout_v1.1.jpg)

*ESP32-S3-DevKitC-1 pinout (compatible with Olimex ESP32-S3-DevKit-Lipo headers). Source: Espressif.*

> **Tip:** Flip your Olimex board over — every pin is labeled on the bottom silkscreen (see photo in Section 1.2).

### 2.1 Header EXT1 (Left Side) — 22 Pins

| EXT1 Pin | Signal | ESP32-S3 GPIO | Notes |
|----------|--------|---------------|-------|
| 1 | 3.3V | — | Regulated 3.3V output |
| 2 | 3.3V | — | Regulated 3.3V output |
| 3 | ESP_EN | EN | Reset (10k pull-up, 1µF cap) |
| 4 | GPIO4 | Pin 4 | **Free** — ADC1_CH3, Touch4 |
| 5 | GPIO5 | Pin 5 | External power sense (220k/470k divider from 5V) |
| 6 | GPIO6 | Pin 6 | Battery voltage sense (470k/150k divider from VBAT) |
| 7 | GPIO7 | Pin 7 | **Free** — ADC1_CH6, Touch7 |
| 8 | GPIO15 | Pin 8 | **Free** — ADC2_CH4 |
| 9 | GPIO16 | Pin 9 | **Free** — ADC2_CH5 |
| 10 | GPIO17 | Pin 10 | UART1 TX, shared with pUEXT pin 3 |
| 11 | GPIO18 | Pin 11 | UART1 RX, shared with pUEXT pin 4 |
| 12 | GPIO8 | Pin 12 | **Free** — ADC1_CH7, Touch8 |
| 13 | GPIO3 | Pin 15 | **Strapping pin** (10k pull-up R18). Safe for output after boot. |
| 14 | GPIO46 | Pin 16 | **Strapping pin**. Safe for output after boot. |
| 15 | GPIO9 | Pin 17 | **Free** — ADC1_CH8, Touch9 |
| 16 | GPIO10 | Pin 18 | SPI CS, shared with pUEXT (10k pull-up) |
| 17 | GPIO11 | Pin 19 | SPI MOSI, shared with pUEXT |
| 18 | GPIO12 | Pin 20 | SPI CLK, shared with pUEXT |
| 19 | GPIO13 | Pin 21 | SPI MISO, shared with pUEXT |
| 20 | GPIO14 | Pin 22 | **Free** — ADC2_CH3, Touch14 |
| 21 | +5V | — | 5V from USB (through Schottky diode) |
| 22 | GND | — | Ground |

### 2.2 Header EXT2 (Right Side) — 22 Pins

| EXT2 Pin | Signal | ESP32-S3 GPIO | Notes |
|----------|--------|---------------|-------|
| 1 | GND | — | Ground |
| 2 | GPIO43 | Pin 37 | UART0 TX — connected to CH340X |
| 3 | GPIO44 | Pin 36 | UART0 RX — connected to CH340X |
| 4 | GPIO1 | Pin 39 | **Free** — ADC1_CH0, Touch1 |
| 5 | GPIO2 | Pin 38 | **Free** — ADC1_CH1, Touch2 |
| 6 | GPIO42 | Pin 35 | **Free** — MTMS |
| 7 | GPIO41 | Pin 34 | **Free** — MTDI |
| 8 | GPIO40 | Pin 33 | **Free** — MTDO |
| 9 | GPIO39 | Pin 32 | **Free** — MTCK |
| 10 | GPIO38 | Pin 31 | **On-board green LED (active LOW via 2.2k to 3.3V)** |
| 11 | GPIO37 | Pin 30 | **DO NOT USE** — Octal PSRAM SPIIO6 |
| 12 | GPIO36 | Pin 29 | **DO NOT USE** — Octal PSRAM SPIIO5 |
| 13 | GPIO35 | Pin 28 | **DO NOT USE** — Octal PSRAM SPIIO4 |
| 14 | GPIO0 | Pin 27 | **Strapping pin** — BOOT button, boot mode select |
| 15 | GPIO45 | Pin 26 | **Strapping pin** — VDD_SPI voltage select |
| 16 | GPIO48 | Pin 25 | I2C SDA, shared with pUEXT (2.2k pull-up on board) |
| 17 | GPIO47 | Pin 24 | I2C SCL, shared with pUEXT (2.2k pull-up on board) |
| 18 | GPIO21 | Pin 23 | **Free** |
| 19 | GPIO20 | Pin 14 | **Native USB D+** — wired to USB-OTG port |
| 20 | GPIO19 | Pin 13 | **Native USB D-** — wired to USB-OTG port |
| 21 | GND | — | Ground |
| 22 | GND | — | Ground |

### 2.3 GPIO Restrictions and Warnings

**DO NOT USE — Reserved for internal PSRAM (N8R8 Octal):**

| GPIO | Reason | Header Location |
|------|--------|-----------------|
| GPIO35 | PSRAM SPIIO4 | EXT2 pin 13 |
| GPIO36 | PSRAM SPIIO5 | EXT2 pin 12 |
| GPIO37 | PSRAM SPIIO6 | EXT2 pin 11 |

These are broken out on the header but connecting anything to them **will break PSRAM operation**. Treat them as off-limits.

**Use with awareness — On-board peripherals connected:**

| GPIO | Connection | Still usable? |
|------|-----------|---------------|
| GPIO5 | 220k/470k voltage divider from 5V rail | Yes — reads external power. Cannot use as digital output. |
| GPIO6 | 470k/150k voltage divider from VBAT | Yes — reads battery voltage. Cannot use as digital output. |
| GPIO38 | Green LED (2.2k to 3.3V, active LOW) | Yes — LED reflects pin state. |
| GPIO19 | USB D- (wired to USB-OTG connector) | Lose USB-OTG/JTAG if repurposed. |
| GPIO20 | USB D+ (wired to USB-OTG connector) | Lose USB-OTG/JTAG if repurposed. |
| GPIO43 | UART0 TX (wired to CH340X) | Lose serial console if repurposed. |
| GPIO44 | UART0 RX (wired to CH340X) | Lose serial console if repurposed. |

### 2.4 Freely Available GPIO Pins

These have NO on-board connections (just header breakout):

| GPIO | ADC | Touch | Header Pin |
|------|-----|-------|------------|
| GPIO1 | ADC1_CH0 | Touch1 | EXT2 pin 4 |
| GPIO2 | ADC1_CH1 | Touch2 | EXT2 pin 5 |
| GPIO4 | ADC1_CH3 | Touch4 | EXT1 pin 4 |
| GPIO7 | ADC1_CH6 | Touch7 | EXT1 pin 7 |
| GPIO8 | ADC1_CH7 | Touch8 | EXT1 pin 12 |
| GPIO9 | ADC1_CH8 | Touch9 | EXT1 pin 15 |
| GPIO14 | ADC2_CH3 | Touch14 | EXT1 pin 20 |
| GPIO15 | ADC2_CH4 | — | EXT1 pin 8 |
| GPIO16 | ADC2_CH5 | — | EXT1 pin 9 |
| GPIO21 | — | — | EXT2 pin 18 |
| GPIO39 | — | — | EXT2 pin 9 |
| GPIO40 | — | — | EXT2 pin 8 |
| GPIO41 | — | — | EXT2 pin 7 |
| GPIO42 | — | — | EXT2 pin 6 |

That's **14 completely free GPIO pins** — more than enough for the Dilder peripherals.

### 2.5 Strapping Pins

These GPIOs have special boot-time functions. External circuits should not force them to unexpected states during power-on.

| GPIO | Boot Function | Board State | Safe for Dilder? |
|------|--------------|-------------|-----------------|
| GPIO0 | Boot mode select | Internal pull-up. BOOT button pulls LOW. | **Avoid** — used for BOOT button |
| GPIO3 | JTAG signal source | 10k pull-up (R18) | **Yes** — output after boot is fine |
| GPIO45 | VDD_SPI voltage select | Internal pull-down (3.3V SPI) | **Avoid** — don't connect |
| GPIO46 | ROM debug messages | Internal pull-down | **Yes** — output after boot is fine |

---

## 3. Parts You Already Have

Based on the Dilder hardware design plan and breadboard prototype guide:

| # | Part | Model | Interface | Source | Status |
|---|------|-------|-----------|--------|--------|
| 1 | **ESP32-S3 Dev Board** | Olimex ESP32-S3-DevKit-Lipo | — | Olimex.com | **Just received** (4 pcs) |
| 2 | **e-Ink Display** | Waveshare 2.13" e-Paper HAT V3 | SPI (SSD1680) | Previously purchased | **In hand** |
| 3 | **5-Way Joystick** | DollaTek 5D Navigation Module | GPIO (active LOW) | Amazon B07HBPW3DF | **In hand** (from Pico prototype) |
| 4 | **Breadboard** | 830 tie-point full-size | — | — | Should have from Pico build |
| 5 | **Jumper Wires** | M-M and F-M assortment | — | — | Should have from Pico build |

**What you might still need:**

| Part | Purpose | Price | Notes |
|------|---------|-------|-------|
| LiPo battery (JST PH 2.0mm) | Battery power | €3.55-8.95 | See [Compatible LiPo Battery Options](#compatible-lipo-battery-options) — recommended: **Olimex BATTERY-LIPO1400mAh** (€5.95) |
| USB-C cable (data, not charge-only) | Upload and serial | ~€3-5 | Must be a data cable, not charge-only |

---

## 4. GPIO Assignment for Dilder

### 4.1 Pin Mapping Table

These assignments match the Dilder custom PCB design where possible, adapted for the Olimex board's pin restrictions. **GPIO5 and GPIO6 are NOT used for joystick** on the Olimex (unlike the breadboard prototype guide for the generic board) because they have voltage dividers connected.

| Peripheral | Signal | ESP32-S3 GPIO | EXT Pin | Direction | Notes |
|-----------|--------|---------------|---------|-----------|-------|
| **e-Paper** | CLK (SCLK) | GPIO12 | EXT1-18 | Out | SPI bus clock |
| | DIN (MOSI) | GPIO11 | EXT1-17 | Out | SPI data |
| | CS | GPIO10 | EXT1-16 | Out | Active LOW chip select (10k pull-up on board) |
| | DC | GPIO9 | EXT1-15 | Out | Data/Command select |
| | RST | GPIO3 | EXT1-13 | Out | Active LOW reset (strapping pin — safe after boot) |
| | BUSY | GPIO8 | EXT1-12 | In | HIGH = display busy |
| | VCC | 3.3V | EXT1-1 | Power | |
| | GND | GND | EXT1-22 | Ground | |
| **Joystick** | UP | GPIO4 | EXT1-4 | In (pull-up) | Active LOW |
| | DOWN | GPIO7 | EXT1-7 | In (pull-up) | Active LOW |
| | LEFT | GPIO1 | EXT2-4 | In (pull-up) | Active LOW |
| | RIGHT | GPIO2 | EXT2-5 | In (pull-up) | Active LOW |
| | CENTER | GPIO15 | EXT1-8 | In (pull-up) | Active LOW |
| | COM/GND | GND | EXT1-22 | Ground | |
| **Board** | LED | GPIO38 | EXT2-10 | Out | Active LOW (on-board green LED) |
| | BOOT btn | GPIO0 | EXT2-14 | In | User button during runtime |
| | BAT sense | GPIO6 | EXT1-6 | ADC In | Battery voltage × 4.133 |
| | PWR sense | GPIO5 | EXT1-5 | ADC In | USB power detection × 1.468 |

**Total GPIO used:** 13 (6 display + 5 joystick + LED + BOOT button)
**Remaining free:** GPIO14, GPIO16, GPIO17, GPIO18, GPIO21, GPIO39-42, GPIO46-48 (12+ pins for future sensors)

### 4.2 Bus Summary Diagram

```
                    Olimex ESP32-S3-DevKit-Lipo
                   ┌─────────────────────────┐
                   │                         │
   SPI (FSPI) ────┤ GPIO12 (CLK)            │
                   │ GPIO11 (MOSI)           ├──────── Waveshare 2.13" e-Paper V3
                   │ GPIO10 (CS)             │         (SSD1680, 250×122)
                   │ GPIO9  (DC)             │
                   │ GPIO3  (RST)            │
                   │ GPIO8  (BUSY)           │
                   │                         │
   GPIO ──────────┤ GPIO4  (UP)             │
                   │ GPIO7  (DOWN)           ├──────── 5-Way Joystick
                   │ GPIO1  (LEFT)           │         (DollaTek module)
                   │ GPIO2  (RIGHT)          │
                   │ GPIO15 (CENTER)         │
                   │                         │
   On-board ──────┤ GPIO38 (LED)            │
                   │ GPIO0  (BOOT btn)       │
                   │ GPIO6  (BAT ADC)        │
                   │ GPIO5  (PWR ADC)        │
                   │                         │
   Reserved ──────┤ GPIO47 (I2C SCL) ───────┤──── Future: Accelerometer, SHT40
   (for later)     │ GPIO48 (I2C SDA) ───────┤──── (pull-ups already on board)
                   │                         │
                   │ 3V3 ────────────────────┼──── 3.3V to all peripherals
                   │ GND ────────────────────┼──── Common ground
                   └─────────────────────────┘
```

**Why these specific pins?**
- **SPI on GPIO10-12:** These are the default FSPI (SPI3) pins with hardware SPI support and already on the pUEXT connector. Using hardware SPI is faster and frees the CPU.
- **GPIO9 for DC, GPIO3 for RST, GPIO8 for BUSY:** Free pins close to the SPI cluster on EXT1 header, keeping wiring clean.
- **GPIO10 for CS:** Has a 10k pull-up on the board already — ideal for chip-select which is active LOW.
- **Joystick on GPIO1, 2, 4, 7, 15:** All completely free pins with no board-level connections. Avoids GPIO5/6 (voltage dividers) and GPIO0 (boot button).
- **I2C reserved on GPIO47/48:** These already have 2.2k pull-ups on the board. When you add the accelerometer and SHT40 later, no external pull-up resistors needed.

---

## 5. Breadboard Wiring — Step by Step

### 5.1 What You Need

- [ ] Olimex ESP32-S3-DevKit-Lipo (1 of your 4 units)
- [ ] Waveshare 2.13" e-Paper HAT V3
- [ ] DollaTek 5-way joystick module
- [ ] Full-size breadboard (830 tie points)
- [ ] Jumper wires: ~8 male-to-male, ~8 female-to-male
- [ ] USB-C data cable (for the USB-UART port)

### 5.2 Phase 1 — Board on Breadboard

1. **Orient the board** with the USB ports facing up (away from you).
2. **Place the Olimex board** straddling the center channel of the breadboard. The 22-pin headers on each side should drop into the breadboard rows.
3. **Note:** The board is narrow (27.94mm) so it fits cleanly across the center channel with access to both pin rows.
4. **Connect power rails:**
   - Run a jumper from **EXT1 pin 1 (3.3V)** to the breadboard's **+** power rail.
   - Run a jumper from **EXT1 pin 22 (GND)** to the breadboard's **−** ground rail.
   - Bridge the ground rail to the other side if your breadboard has split rails.
5. **Plug in the USB-C cable** to the **USB-UART port** (the one near the buttons, with the CH340X chip).
6. The green LED may blink or stay on depending on what firmware is loaded. If the board is new, it should be running a factory demo.

### 5.3 Phase 2 — Wire the Joystick

The DollaTek 5-way module is a passive switch-to-ground device. Each direction connects its pin to COM (ground) when pressed. We enable internal pull-ups in software.

**Wiring (use male-to-male jumper wires):**

| Joystick Pin | → | Breadboard Row → ESP32 GPIO | EXT Pin |
|-------------|---|---------------------------|---------|
| COM / GND | → | Ground rail (−) | — |
| UP | → | GPIO4 row | EXT1 pin 4 |
| DOWN | → | GPIO7 row | EXT1 pin 7 |
| LEFT | → | GPIO1 row | EXT2 pin 4 |
| RIGHT | → | GPIO2 row | EXT2 pin 5 |
| CENTER / SET | → | GPIO15 row | EXT1 pin 8 |
| VCC (if present) | → | Leave unconnected | — |

**Tips:**
- Check your module's silkscreen — the pin labels vary between batches (SET/MID/CENTER, COM/GND).
- If the module has a VCC pin, leave it disconnected.
- Use color-coded wires: Black=GND, Red=UP, Blue=DOWN, Yellow=LEFT, Green=RIGHT, White=CENTER.

### 5.4 Phase 3 — Wire the e-Paper Display

The Waveshare 2.13" HAT has an 8-pin header on the edge labeled: VCC, GND, DIN, CLK, CS, DC, RST, BUSY. Use **female-to-male jumper wires** (female end onto the HAT header, male end into the breadboard).

**Wiring:**

| Display Pin | Function | → | ESP32 GPIO | EXT Pin |
|------------|----------|---|-----------|---------|
| VCC | 3.3V power | → | 3.3V rail (+) | EXT1 pin 1/2 |
| GND | Ground | → | Ground rail (−) | EXT1 pin 22 |
| DIN | SPI MOSI | → | GPIO11 | EXT1 pin 17 |
| CLK | SPI Clock | → | GPIO12 | EXT1 pin 18 |
| CS | Chip Select | → | GPIO10 | EXT1 pin 16 |
| DC | Data/Command | → | GPIO9 | EXT1 pin 15 |
| RST | Reset | → | GPIO3 | EXT1 pin 13 |
| BUSY | Busy flag | → | GPIO8 | EXT1 pin 12 |

**SPI protocol settings:**
- Mode: 0 (CPOL=0, CPHA=0)
- Bit order: MSB first
- Clock speed: 4 MHz (safe default; can go up to 10 MHz)

### 5.5 Master Wiring Diagram

```
DollaTek Joystick                     Olimex ESP32-S3-DevKit-Lipo                   Waveshare e-Paper V3
┌──────────────┐                     ┌────── USB-UART ──────┐                      ┌──────────────┐
│              │                     │      (upload here)    │                      │              │
│  COM ────────┼──── GND rail ──────┤ GND              3.3V ├──── + rail ──────────┤ VCC          │
│              │                     │                       │                      │              │
│  UP  ────────┼────────────────────┤ GPIO4 (EXT1-4)        │          GND rail ───┤ GND          │
│              │                     │                       │                      │              │
│  DOWN ───────┼────────────────────┤ GPIO7 (EXT1-7)        │                      │              │
│              │                     │                       │                      │              │
│  LEFT ───────┼────────────────────┤ GPIO1 (EXT2-4)        │      GPIO11 ─────────┤ DIN (MOSI)   │
│              │                     │                       │                      │              │
│  RIGHT ──────┼────────────────────┤ GPIO2 (EXT2-5)        │      GPIO12 ─────────┤ CLK (SCLK)   │
│              │                     │                       │                      │              │
│  CENTER ─────┼────────────────────┤ GPIO15 (EXT1-8)       │      GPIO10 ─────────┤ CS           │
│              │                     │                       │                      │              │
│  (VCC — NC)  │                     │              GPIO9  ──┼─────────────────────┤ DC           │
│              │                     │                       │                      │              │
└──────────────┘                     │              GPIO3  ──┼─────────────────────┤ RST          │
                                     │                       │                      │              │
                                     │              GPIO8  ──┼─────────────────────┤ BUSY         │
                                     │                       │                      │              │
                                     │       GPIO38 ── LED (onboard)               └──────────────┘
                                     │       GPIO0  ── BOOT button (onboard)
                                     │       GPIO6  ── Battery ADC (onboard)
                                     │       GPIO5  ── Power detect (onboard)
                                     │                       │
                                     └───────────────────────┘
```

### 5.6 Wiring Checklist

Before powering on, verify:

- [ ] **No shorts** — no signal wires touch each other or ground
- [ ] **Correct power** — display VCC goes to 3.3V rail, NOT 5V
- [ ] **GND connected** — joystick COM, display GND, and board GND are all on the same ground rail
- [ ] **Display cable** — the FPC ribbon cable from the display panel to the HAT board is seated properly (fragile!)
- [ ] **Right USB port** — cable is in the USB-UART port (near the buttons), not USB-OTG
- [ ] **No VCC on joystick** — if the module has a VCC pin, leave it floating
- [ ] **SPI wires correct** — DIN→GPIO11, CLK→GPIO12, CS→GPIO10 (double-check, swapped SPI wires produce no output)

---

## 6. VSCode + PlatformIO Setup

### 6.1 Install PlatformIO

1. Open **VSCode**.
2. Go to the **Extensions** panel (Ctrl+Shift+X).
3. Search for **"PlatformIO IDE"** and install it.
4. Wait for PlatformIO to finish installing its core tools (this takes a few minutes on first install). You'll see progress in the bottom status bar.
5. Restart VSCode when prompted.

**Verify installation:** Open the PlatformIO sidebar (alien icon in the left bar) → should show "PIO Home" tab.

### 6.2 Create the Project

**Option A — From PlatformIO Home (GUI):**

1. Click the PlatformIO alien icon → **"+ New Project"**
2. Name: `dilder-esp32`
3. Board: **"Espressif ESP32-S3-DevKitC-1"** (search for "S3-DevKitC")
4. Framework: **Arduino**
5. Location: Inside your Dilder project at `ESP Protyping/dilder-esp32/`
6. Click **"Finish"**

**Option B — From terminal:**

```bash
mkdir -p "ESP Protyping/dilder-esp32"
cd "ESP Protyping/dilder-esp32"
pio project init --board esp32-s3-devkitc-1 --project-option "framework=arduino"
```

### 6.3 Configure platformio.ini

Replace the generated `platformio.ini` with this Olimex-specific configuration:

```ini
[env:olimex-esp32s3-devkit-lipo]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
monitor_speed = 115200

; ── Olimex ESP32-S3-DevKit-Lipo specific settings ──
build_flags =
    -DARDUINO_USB_CDC_ON_BOOT=1    ; Enable serial over USB-OTG port too
    -DBOARD_HAS_PSRAM              ; Board has 8MB octal PSRAM

board_build.psram = enabled        ; Enable PSRAM in the build
board_build.arduino.memory_type = qio_opi  ; QIO flash + OPI PSRAM

; ── Upload settings ──
; Use USB-UART port (CH340X) for upload — it has auto-reset
upload_speed = 460800
upload_port = /dev/ttyUSB0         ; Adjust if your port differs

; ── Monitor settings ──
monitor_port = /dev/ttyUSB0        ; Same port for serial monitor
monitor_filters = esp32_exception_decoder  ; Decode crash backtraces

; ── Library dependencies ──
lib_deps =
    ; Add libraries here as you need them, e.g.:
    ; zinggjm/GxEPD2@^1.5.0       ; e-Paper display library
```

**Key flags explained:**

| Flag | Why |
|------|-----|
| `ARDUINO_USB_CDC_ON_BOOT=1` | Enables USB CDC serial output on the USB-OTG port. Without this, `Serial.print()` only works through the CH340X UART port. |
| `BOARD_HAS_PSRAM` | Tells the Arduino core that PSRAM is available. Some libraries check this flag. |
| `board_build.psram = enabled` | Enables PSRAM initialization at boot. The 8MB PSRAM shows up in `ESP.getPsramSize()`. |
| `qio_opi` | Sets the memory access mode: QIO (Quad I/O) for flash, OPI (Octal) for PSRAM. Must match the N8R8 module. |

### 6.4 USB Driver Setup (Linux)

The CH340X USB-to-serial chip is supported by the `ch341` kernel module, which is built into most Linux distributions (including CachyOS).

**Check if the board is detected:**

```bash
# Plug in the USB-UART port, then:
dmesg | tail -20
# Should show: "ch341-uart converter now attached to ttyUSB0"

# Or check for the device:
ls -la /dev/ttyUSB*
```

**If you get permission denied:**

```bash
# Add your user to the dialout group (one-time)
sudo usermod -a -G dialout $USER

# Log out and back in (or reboot) for the group change to take effect
```

**If using the USB-OTG port instead:**

```bash
# The native USB shows up as ttyACM0
ls -la /dev/ttyACM*
```

### 6.5 First Upload — Blink Test

Create `src/main.cpp` with this minimal blink sketch to verify your toolchain:

```cpp
#include <Arduino.h>

// Olimex ESP32-S3-DevKit-Lipo onboard LED
// Active LOW: LOW = ON, HIGH = OFF
#define LED_PIN 38

void setup() {
    Serial.begin(115200);

    // Wait for USB CDC serial (up to 3 seconds)
    unsigned long start = millis();
    while (!Serial && millis() - start < 3000) {
        delay(10);
    }

    pinMode(LED_PIN, OUTPUT);
    Serial.println("Olimex ESP32-S3-DevKit-Lipo — Blink Test");
    Serial.printf("Flash: %u MB\n", ESP.getFlashChipSize() / (1024 * 1024));
    Serial.printf("PSRAM: %u bytes\n", ESP.getPsramSize());
}

void loop() {
    digitalWrite(LED_PIN, LOW);   // LED ON
    Serial.println("LED ON");
    delay(500);

    digitalWrite(LED_PIN, HIGH);  // LED OFF
    Serial.println("LED OFF");
    delay(500);
}
```

**Upload from VSCode:**

1. Click the **→ (Upload)** button in the PlatformIO toolbar (bottom bar), or press **Ctrl+Alt+U**.
2. PlatformIO compiles the code, detects the board on `/dev/ttyUSB0`, and uploads.
3. The green LED should start blinking at 1 Hz.
4. Click the **plug icon (Serial Monitor)** in the PlatformIO toolbar, or press **Ctrl+Alt+S**.
5. You should see "LED ON" / "LED OFF" alternating in the terminal.

**If upload fails:** See Section 8.4 (Troubleshooting).

---

## 7. Test Sketches

### 7.1 Chip Info Sketch

Dumps full chip/memory information to verify the board is working correctly:

```cpp
#include <Arduino.h>

void printChipInfo() {
    Serial.printf("\n[Uptime: %lu seconds]\n", millis() / 1000);
    Serial.println("=== ESP32-S3 Chip Information ===");
    Serial.printf("Chip model: %s\n", ESP.getChipModel());
    Serial.printf("Chip revision: %d\n", ESP.getChipRevision());
    Serial.printf("Chip cores: %d\n", ESP.getChipCores());
    Serial.printf("CPU frequency: %d MHz\n", ESP.getCpuFreqMHz());
    Serial.printf("Flash size: %u MB\n", ESP.getFlashChipSize() / (1024 * 1024));
    Serial.printf("Flash speed: %u MHz\n", ESP.getFlashChipSpeed() / 1000000);
    Serial.printf("Heap size: %u bytes\n", ESP.getHeapSize());
    Serial.printf("Free heap: %u bytes\n", ESP.getFreeHeap());

    if (ESP.getPsramSize() > 0) {
        Serial.printf("PSRAM size: %u bytes (%u MB)\n",
                      ESP.getPsramSize(), ESP.getPsramSize() / (1024 * 1024));
        Serial.printf("Free PSRAM: %u bytes\n", ESP.getFreePsram());
    } else {
        Serial.println("WARNING: No PSRAM detected! Check board_build.psram = enabled");
    }

    uint64_t chipid = ESP.getEfuseMac();
    Serial.printf("Chip ID (MAC): %04X%08X\n",
                  (uint16_t)(chipid >> 32), (uint32_t)chipid);
    Serial.println("================================\n");
}

void setup() {
    Serial.begin(115200);
    unsigned long start = millis();
    while (!Serial && millis() - start < 5000) delay(10);
    delay(200);
    printChipInfo();
}

void loop() {
    delay(30000);
    printChipInfo();
}
```

**Expected output:**

```
=== ESP32-S3 Chip Information ===
Chip model: ESP32-S3
Chip revision: 0
Chip cores: 2
CPU frequency: 240 MHz
Flash size: 8 MB
Flash speed: 80 MHz
PSRAM size: 8388608 bytes (8 MB)
...
```

If PSRAM shows 0, double-check your `platformio.ini` has `board_build.psram = enabled` and `board_build.arduino.memory_type = qio_opi`.

### 7.2 Battery Monitor Sketch

Reads battery voltage and external power status using the on-board voltage dividers:

```cpp
#include <Arduino.h>

#define LED_PIN        38
#define BAT_ADC_PIN    6
#define PWR_ADC_PIN    5

#define BAT_DIVIDER_RATIO  4.1333   // (470k + 150k) / 150k
#define PWR_THRESHOLD_MV   400      // Above this = USB power present

void setup() {
    Serial.begin(115200);
    unsigned long start = millis();
    while (!Serial && millis() - start < 3000) delay(10);

    analogReadResolution(12);
    pinMode(LED_PIN, OUTPUT);
    Serial.println("Battery Monitor Started");
}

void loop() {
    // Read battery voltage
    uint32_t batRaw = analogRead(BAT_ADC_PIN);
    float batVoltage = (batRaw / 4095.0) * 3.3 * BAT_DIVIDER_RATIO;

    // Read external power
    uint32_t pwrRaw = analogRead(PWR_ADC_PIN);
    float pwrMv = (pwrRaw / 4095.0) * 3300.0;
    bool usbPower = (pwrMv > PWR_THRESHOLD_MV);

    Serial.printf("Battery: %.3f V | USB Power: %s\n",
                  batVoltage, usbPower ? "PRESENT" : "NOT PRESENT");

    // LED on when USB power is present
    digitalWrite(LED_PIN, usbPower ? LOW : HIGH);

    delay(2000);
}
```

### 7.3 Joystick Test Sketch

Tests all 5 directions with the adapted GPIO pins:

```cpp
#include <Arduino.h>

// Olimex GPIO assignments (avoiding GPIO5/6 voltage dividers)
#define BTN_UP      4
#define BTN_DOWN    7
#define BTN_LEFT    1
#define BTN_RIGHT   2
#define BTN_CENTER  15

const uint8_t buttons[] = {BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT, BTN_CENTER};
const char* names[]      = {"UP", "DOWN", "LEFT", "RIGHT", "CENTER"};

void setup() {
    Serial.begin(115200);
    unsigned long start = millis();
    while (!Serial && millis() - start < 3000) delay(10);

    for (int i = 0; i < 5; i++) {
        pinMode(buttons[i], INPUT_PULLUP);
    }

    Serial.println("=== Joystick Test ===");
    Serial.println("Press any direction...\n");
}

void loop() {
    for (int i = 0; i < 5; i++) {
        if (digitalRead(buttons[i]) == LOW) {
            Serial.printf("[PRESSED] %s (GPIO%d)\n", names[i], buttons[i]);
        }
    }
    delay(100);
}
```

**Expected output when pressing each direction:**

```
=== Joystick Test ===
Press any direction...

[PRESSED] UP (GPIO4)
[PRESSED] DOWN (GPIO7)
[PRESSED] LEFT (GPIO1)
[PRESSED] RIGHT (GPIO2)
[PRESSED] CENTER (GPIO15)
```

### 7.4 e-Paper Display Test Sketch

Uses the GxEPD2 library to drive the Waveshare 2.13" V3 display.

**First, add the library to `platformio.ini`:**

```ini
lib_deps =
    zinggjm/GxEPD2@^1.5.0
    adafruit/Adafruit GFX Library@^1.11.0
```

**Then create the test sketch:**

```cpp
#include <Arduino.h>
#include <GxEPD2_BW.h>

// ── Pin definitions for Olimex ESP32-S3-DevKit-Lipo ──
#define EPD_CS    10
#define EPD_DC     9
#define EPD_RST    3
#define EPD_BUSY   8
#define EPD_CLK   12
#define EPD_MOSI  11

// Waveshare 2.13" V3 (SSD1680, 250x122)
// GxEPD2 class: GxEPD2_213_BN (for SSD1680-based 2.13" displays)
GxEPD2_BW<GxEPD2_213_BN, GxEPD2_213_BN::HEIGHT>
    display(GxEPD2_213_BN(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));

void setup() {
    Serial.begin(115200);
    unsigned long start = millis();
    while (!Serial && millis() - start < 3000) delay(10);
    Serial.println("e-Paper Display Test");

    // Initialize SPI with custom pins
    SPI.begin(EPD_CLK, -1, EPD_MOSI, EPD_CS);  // CLK, MISO (none), MOSI, CS

    display.init(115200);  // Debug output at 115200

    // Full window mode
    display.setRotation(1);  // Landscape
    display.setTextColor(GxEPD2_BW<GxEPD2_213_BN, GxEPD2_213_BN::HEIGHT>::BLACK);
    display.setTextSize(2);

    display.setFullWindow();
    display.firstPage();
    do {
        display.fillScreen(GxEPD_WHITE);
        display.setCursor(10, 20);
        display.print("Hello Dilder!");
        display.setTextSize(1);
        display.setCursor(10, 50);
        display.print("Olimex ESP32-S3-DevKit-Lipo");
        display.setCursor(10, 65);
        display.print("Waveshare 2.13\" V3 (SSD1680)");
        display.setCursor(10, 85);
        display.printf("PSRAM: %u KB", ESP.getPsramSize() / 1024);
        display.setCursor(10, 100);
        display.printf("Free heap: %u KB", ESP.getFreeHeap() / 1024);
    } while (display.nextPage());

    Serial.println("Display updated!");
    display.hibernate();
}

void loop() {
    // Nothing — e-paper retains image with no power
    delay(10000);
}
```

**If you see garbage or nothing on the display:**
- Double-check DIN (MOSI) and CLK wires aren't swapped
- Verify you're using V3 of the display, not V2 or V4 (check PCB silkscreen)
- Try the `GxEPD2_213_B74` class instead of `GxEPD2_213_BN` if the SSD1680 variant differs
- Make sure the FPC cable between the e-paper panel and the HAT PCB is firmly seated

### 7.5 Combined Test — All Peripherals

Once joystick and display work individually, combine them:

```cpp
#include <Arduino.h>
#include <GxEPD2_BW.h>

// ── Pin definitions ──
#define EPD_CS    10
#define EPD_DC     9
#define EPD_RST    3
#define EPD_BUSY   8
#define EPD_CLK   12
#define EPD_MOSI  11

#define BTN_UP      4
#define BTN_DOWN    7
#define BTN_LEFT    1
#define BTN_RIGHT   2
#define BTN_CENTER  15

#define LED_PIN     38
#define BAT_ADC     6

GxEPD2_BW<GxEPD2_213_BN, GxEPD2_213_BN::HEIGHT>
    display(GxEPD2_213_BN(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));

const uint8_t buttons[] = {BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT, BTN_CENTER};
const char* btnNames[]  = {"UP", "DOWN", "LEFT", "RIGHT", "CENTER"};

void updateDisplay(const char* lastButton, float batV) {
    display.setFullWindow();
    display.firstPage();
    do {
        display.fillScreen(GxEPD_WHITE);
        display.setTextColor(GxEPD_BLACK);

        display.setTextSize(2);
        display.setCursor(10, 15);
        display.print("Dilder Proto");

        display.setTextSize(1);
        display.setCursor(10, 45);
        display.printf("Battery: %.2f V", batV);

        display.setCursor(10, 60);
        display.printf("PSRAM: %u KB free", ESP.getFreePsram() / 1024);

        display.setCursor(10, 80);
        display.print("Last input: ");
        display.print(lastButton);

        display.setCursor(10, 100);
        display.print("Press CENTER to refresh");
    } while (display.nextPage());
}

void setup() {
    Serial.begin(115200);
    unsigned long start = millis();
    while (!Serial && millis() - start < 3000) delay(10);

    // Init buttons
    for (int i = 0; i < 5; i++) {
        pinMode(buttons[i], INPUT_PULLUP);
    }

    // Init LED
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, HIGH);  // OFF

    // Init ADC
    analogReadResolution(12);

    // Init display
    SPI.begin(EPD_CLK, -1, EPD_MOSI, EPD_CS);
    display.init(115200);
    display.setRotation(1);

    float batV = (analogRead(BAT_ADC) / 4095.0) * 3.3 * 4.1333;
    updateDisplay("none", batV);

    Serial.println("Combined test ready. Press joystick directions.");
}

void loop() {
    for (int i = 0; i < 5; i++) {
        if (digitalRead(buttons[i]) == LOW) {
            Serial.printf("[PRESSED] %s\n", btnNames[i]);

            // Flash LED
            digitalWrite(LED_PIN, LOW);
            delay(100);
            digitalWrite(LED_PIN, HIGH);

            // Update display only on CENTER press (e-paper is slow)
            if (i == 4) {  // CENTER
                float batV = (analogRead(BAT_ADC) / 4095.0) * 3.3 * 4.1333;
                updateDisplay(btnNames[i], batV);
            }

            // Debounce
            while (digitalRead(buttons[i]) == LOW) delay(10);
            delay(50);
        }
    }
    delay(50);
}
```

---

## 8. Compiling and Flashing Firmware

### 8.1 Build from VSCode

| Action | Button | Shortcut |
|--------|--------|----------|
| **Build** | Checkmark (✓) in PlatformIO toolbar | Ctrl+Alt+B |
| **Upload** | Arrow (→) in PlatformIO toolbar | Ctrl+Alt+U |
| **Serial Monitor** | Plug icon in PlatformIO toolbar | Ctrl+Alt+S |
| **Clean** | Trash icon | — |
| **Upload + Monitor** | — | `pio run -t upload && pio device monitor` |

The PlatformIO toolbar lives at the **bottom of the VSCode window**. If you don't see it, click the PlatformIO alien icon in the left sidebar.

### 8.2 Build from Terminal

```bash
cd "ESP Protyping/dilder-esp32"

# Build only
pio run

# Build and upload
pio run -t upload

# Clean build
pio run -t clean

# Serial monitor
pio device monitor

# Build, upload, then monitor (chained)
pio run -t upload && pio device monitor
```

**Build output location:** `.pio/build/olimex-esp32s3-devkit-lipo/firmware.bin`

### 8.3 Serial Monitor

```bash
# PlatformIO monitor (auto-detects port and baud)
pio device monitor

# Or specify explicitly
pio device monitor -p /dev/ttyUSB0 -b 115200

# Or use screen/picocom directly
screen /dev/ttyUSB0 115200
picocom -b 115200 /dev/ttyUSB0
```

**Exit screen:** Ctrl+A then K then Y
**Exit picocom:** Ctrl+A then Ctrl+X

### 8.4 Troubleshooting Upload Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| `No such file: /dev/ttyUSB0` | Board not detected or wrong port | Unplug/replug USB. Check `dmesg \| tail`. Try `/dev/ttyUSB1`. |
| `Permission denied: /dev/ttyUSB0` | User not in `dialout` group | `sudo usermod -a -G dialout $USER` then log out/in |
| `Failed to connect to ESP32-S3` | Wrong USB port | Make sure you're using the **USB-UART** port (near the buttons), not USB-OTG |
| `A fatal error occurred: Could not open port` | Port locked by another process | Close any other serial monitors (screen, picocom, Arduino IDE) |
| `Timed out waiting for packet header` | Board not in bootloader mode | Hold **BOOT** button, press **RST**, release BOOT. Then upload. |
| `PSRAM shows 0 bytes` | Wrong memory type config | Add `board_build.arduino.memory_type = qio_opi` to platformio.ini |
| `Brownout detector was triggered` | Insufficient USB power | Use a different USB cable or port. Avoid USB hubs. |
| `Upload succeeds but no serial output` | CDC not enabled | Add `-DARDUINO_USB_CDC_ON_BOOT=1` to build_flags |
| `Wrong chip ID` | Board variant mismatch | Verify you selected `esp32-s3-devkitc-1` as the board |

**Manual bootloader mode (if auto-reset fails):**

1. Hold the **BOOT** button
2. Press and release the **RST** button
3. Release the **BOOT** button
4. The board is now in download mode — upload immediately

---

## 9. Integrating with the Dilder DevTool

### 9.1 Architecture Overview

The Dilder firmware is written in portable C with a platform abstraction layer. The game engine (events, emotions, stats, lifecycle) is the same code on every platform. Only the hardware interface layer changes.

```
┌─────────────────────────────────────────────────┐
│              Dilder Game Engine                   │
│  (event.c, emotion.c, stat.c, life.c, etc.)     │
│  Written in pure C — platform-independent        │
├──────────────┬──────────────┬────────────────────┤
│  Desktop HAL │  Pico W HAL  │  ESP32-S3 HAL      │
│  (DevTool)   │  (current)   │  (you're building) │
│  libdilder.so│  pico-sdk    │  Arduino/ESP-IDF    │
└──────────────┴──────────────┴────────────────────┘
```

The DevTool loads `libdilder.so` (compiled from the same C source) via Python `ctypes` to run the game engine in a GUI emulator. The ESP32-S3 HAL will call the same game engine functions but route display output to the e-Paper and input from the joystick.

### 9.2 Firmware Build Pipeline

For the ESP32-S3 prototype, the build pipeline is:

```
1. Edit C firmware in firmware/src/ and firmware/include/
2. PlatformIO compiles with Arduino framework (wraps ESP-IDF)
3. The ESP32-S3 HAL (src/platform/esp32/) translates:
   - render() calls → GxEPD2 e-Paper commands
   - input() calls → joystick GPIO reads
   - sensor() calls → I2C accelerometer/SHT40 reads
4. Upload via USB-UART to the Olimex board
5. Serial monitor for debug output
```

The DevTool remains your primary development tool for rapid iteration — it compiles and runs the game engine instantly on desktop. The ESP32 upload is for hardware validation.

### 9.3 Serial Communication Protocol

The DevTool can communicate with the ESP32-S3 board over serial for live debugging:

```
DevTool (Python)  ──── USB Serial (/dev/ttyUSB0) ────  ESP32-S3
                        115200 baud, 8N1
```

This lets you:
- Send test commands from DevTool to the board
- Stream game state from the board back to DevTool for visualization
- Update individual game parameters in real time

The protocol is defined in the Dilder firmware's serial handler and will be implemented as the ESP32-S3 HAL matures.

---

## 10. Important Notes and Warnings

### Voltage Levels

All peripherals are **3.3V**. The ESP32-S3 GPIOs are 3.3V and both the Waveshare display and joystick module are 3.3V compatible. **Do not connect 5V signals to any GPIO pin** — this will damage the ESP32-S3.

### GPIO5 and GPIO6 Are Not Free

Unlike the generic ESP32-S3 DevKitC, the Olimex board has voltage dividers permanently connected to GPIO5 (external power sense) and GPIO6 (battery sense). You **cannot use these as general-purpose digital I/O**. They can only be read as ADC inputs.

### GPIO35/36/37 Are Dead

The N8R8 module uses octal PSRAM which internally connects to GPIO35, 36, and 37. These pins are exposed on the EXT2 header but **connecting anything to them will break PSRAM**. Do not use them.

### Battery Safety

- **Verify JST polarity** with a multimeter before connecting any LiPo battery. There is no universal JST polarity standard. Reversed polarity will destroy the charger IC.
- During prototyping, power via USB only. Only connect the battery after all wiring is verified.
- A shorted LiPo can cause fire. Never leave a charging battery unattended.

### Display Refresh Rules

The Waveshare 2.13" e-Paper has strict refresh rules:

| Rule | Requirement |
|------|-------------|
| Minimum interval | ≥ 180 seconds between full refreshes |
| Partial refresh limit | Max 5 consecutive partial refreshes before a full refresh |
| Full refresh procedure | Clear to white → refresh → draw content → refresh |

Violating these causes ghosting artifacts and can permanently damage the display.

### Antenna Clearance

The ESP32-S3 module's PCB antenna is at one end of the board. Do not place metal objects, wires, or your hand directly over the antenna area during Wi-Fi/BLE operation. On the breadboard, keep the antenna end clear.

### SPI Bus Selection

The ESP32-S3 has 4 SPI controllers. SPI0 and SPI1 are reserved for internal flash/PSRAM. We use **SPI3 (FSPI)** for the e-Paper display on GPIO10-13. The Arduino `SPI.begin()` call with custom pins configures this automatically.

---

## 11. Resources, Documentation & Videos

### 11.1 Olimex Board Resources

| Resource | URL |
|----------|-----|
| **Product page** | https://www.olimex.com/Products/IoT/ESP32-S3/ESP32-S3-DevKit-Lipo/open-source-hardware |
| **GitHub repo (schematics, KiCad, software)** | https://github.com/OLIMEX/ESP32-S3-DevKit-LiPo |
| **Schematic PDF (Rev B)** | https://github.com/OLIMEX/ESP32-S3-DevKit-LiPo/blob/main/HARDWARE/ESP32-S3-DevKit-LiPo_Rev_B/ESP32-S3-DevKit-LiPo_Rev_B.pdf |
| **User manual PDF** | https://github.com/OLIMEX/ESP32-S3-DevKit-LiPo/blob/main/DOCUMENTS/ESP32-S3-DevKit-LiPo.pdf |
| **Board dimensions** | https://github.com/OLIMEX/ESP32-S3-DevKit-LiPo/tree/main/HARDWARE/Dimensions |
| **Arduino & PlatformIO examples** | https://github.com/OLIMEX/ESP32-S3-DevKit-LiPo/tree/main/SOFTWARE |
| **Olimex forum** | https://www.olimex.com/forum/ |

### 11.2 ESP32-S3 Resources

| Resource | URL |
|----------|-----|
| **ESP32-S3 Datasheet** | https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf |
| **ESP32-S3 Technical Reference Manual** | https://www.espressif.com/sites/default/files/documentation/esp32-s3_technical_reference_manual_en.pdf |
| **ESP32-S3-WROOM-1 Module Datasheet** | https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf |
| **ESP32-S3 Pinout Guide (RandomNerdTutorials)** | https://randomnerdtutorials.com/esp32-s3-devkitc-pinout-guide/ |
| **ESP32-S3 Strapping Pins Guide** | https://www.espboards.dev/blog/esp32-strapping-pins/ |
| **Espressif Arduino Core (GitHub)** | https://github.com/espressif/arduino-esp32 |
| **ESP-IDF Programming Guide** | https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/ |

### 11.3 Waveshare e-Paper Resources

| Resource | URL |
|----------|-----|
| **Waveshare 2.13" Wiki** | https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT |
| **Waveshare e-Paper GitHub (Pi)** | https://github.com/waveshare/e-Paper |
| **Waveshare Pico e-Paper GitHub** | https://github.com/waveshare/Pico_ePaper_Code |
| **V3 Specification PDF** | https://files.waveshare.com/upload/4/4e/2.13inch_e-Paper_V3_Specification.pdf |
| **SSD1680 Driver IC Datasheet** | https://www.orientdisplay.com/wp-content/uploads/2022/08/SSD1680_v0.14.pdf |
| **GxEPD2 Library (ESP32 e-Paper)** | https://github.com/ZinggJM/GxEPD2 |
| **GxEPD2 Display Selection Guide** | https://github.com/ZinggJM/GxEPD2/blob/master/extras/GxEPD2_selection_new_style.h |

### 11.4 PlatformIO & Development

| Resource | URL |
|----------|-----|
| **PlatformIO Docs — ESP32-S3** | https://docs.platformio.org/en/latest/boards/espressif32/esp32-s3-devkitc-1.html |
| **PlatformIO Quick Start** | https://docs.platformio.org/en/latest/integration/ide/vscode.html |
| **PlatformIO CLI Reference** | https://docs.platformio.org/en/latest/core/userguide/index.html |
| **Arduino-ESP32 GPIO API** | https://docs.espressif.com/projects/arduino-esp32/en/latest/api/gpio.html |
| **Arduino-ESP32 SPI API** | https://docs.espressif.com/projects/arduino-esp32/en/latest/api/spi.html |
| **Arduino-ESP32 I2C API** | https://docs.espressif.com/projects/arduino-esp32/en/latest/api/i2c.html |
| **ESP32-S3 USB CDC Guide** | https://docs.espressif.com/projects/arduino-esp32/en/latest/api/usb_cdc.html |

### 11.5 Video Tutorials

**ESP32-S3 Getting Started:**

| Video | Channel | What It Covers |
|-------|---------|----------------|
| "Getting Started with ESP32-S3" | RandomNerdTutorials | Board overview, Arduino IDE setup, first upload |
| "ESP32-S3 Complete Guide" | DroneBot Workshop | Pinout, SPI/I2C, WiFi, BLE, PSRAM usage |
| "ESP32-S3 with PlatformIO" | Rui Santos (RNT) | VSCode + PlatformIO setup, upload, debug |
| "Olimex ESP32-S3 DevKit Review" | Olimex (official) | Board walkthrough, features, battery charging |

**e-Paper with ESP32:**

| Video | Channel | What It Covers |
|-------|---------|----------------|
| "E-Paper Display with ESP32 — Complete Guide" | RandomNerdTutorials | GxEPD2 library setup, wiring, code examples |
| "Waveshare e-Paper + ESP32-S3" | Volos Projects | SPI wiring, partial refresh, power saving |
| "GxEPD2 Tutorial for ESP32" | Brian Lough | Library deep dive, display selection, custom fonts |
| "E-Ink Weather Display ESP32" | G6EJD (David Bird) | Real-world e-paper project with sensor data display |

**PlatformIO:**

| Video | Channel | What It Covers |
|-------|---------|----------------|
| "PlatformIO with VSCode — Complete Tutorial" | Rui Santos (RNT) | Installation, project creation, serial monitor, debugging |
| "PlatformIO Advanced Tips" | Andreas Spiess | Multiple environments, OTA, library management |
| "ESP32 Debugging with JTAG in PlatformIO" | PlatformIO (official) | USB-OTG JTAG debug setup for ESP32-S3 |

**Search these on YouTube** — the titles describe the content. Look for the most recent uploads (2024-2026) as the ESP32-S3 ecosystem evolves quickly.

---

## Quick Reference Card

```
╔══════════════════════════════════════════════════════════════╗
║              OLIMEX ESP32-S3-DEVKIT-LIPO                     ║
║              DILDER PROTOTYPE QUICK REFERENCE                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  DISPLAY (SPI)           JOYSTICK (GPIO)                     ║
║  ─────────────           ──────────────                      ║
║  DIN  → GPIO11           UP     → GPIO4                     ║
║  CLK  → GPIO12           DOWN   → GPIO7                     ║
║  CS   → GPIO10           LEFT   → GPIO1                     ║
║  DC   → GPIO9            RIGHT  → GPIO2                     ║
║  RST  → GPIO3            CENTER → GPIO15                    ║
║  BUSY → GPIO8            COM    → GND                       ║
║  VCC  → 3.3V                                                ║
║  GND  → GND             ON-BOARD                             ║
║                          ────────                            ║
║  SPI MODE: 0             LED    → GPIO38 (active LOW)        ║
║  SPI CLK:  4 MHz         BOOT   → GPIO0                     ║
║                          BAT    → GPIO6 (ADC, ×4.133)       ║
║  UPLOAD PORT:            PWR    → GPIO5 (ADC, ×1.468)       ║
║  USB-UART (/dev/ttyUSB0)                                    ║
║  115200 baud             DEAD PINS: GPIO35, 36, 37 (PSRAM)  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

*Document version: 2.0 — Rewritten 2026-04-17 for hands-on setup with received hardware*
*Previous version: Breakout board design guide (v1.0)*
