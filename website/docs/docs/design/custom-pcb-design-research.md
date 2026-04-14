# Custom PCB Design Research — Dilder Board

> From breadboard prototype to purpose-built hardware: a complete research document covering PCB design tools, fabrication services, component integration, and a learning path for designing a custom Dilder board — informed by reverse-engineering the PicoTop project.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Case Study: Reverse-Engineering the PicoTop Board](#2-case-study-reverse-engineering-the-picotop-board)
    - [2.1 Project Overview](#21-project-overview)
    - [2.2 Board Architecture](#22-board-architecture)
    - [2.3 Component Inventory](#23-component-inventory)
    - [2.4 Design Decisions](#24-design-decisions)
    - [2.5 Manufacturing Pipeline](#25-manufacturing-pipeline)
    - [2.6 Firmware Architecture](#26-firmware-architecture)
    - [2.7 Lessons for Dilder](#27-lessons-for-dilder)
3. [Dilder Custom Board — Target Specification](#3-dilder-custom-board--target-specification)
    - [3.1 Component Inventory](#31-component-inventory)
    - [3.2 Interface Map](#32-interface-map)
    - [3.3 Power Architecture](#33-power-architecture)
    - [3.4 Board Tiers (Phased Complexity)](#34-board-tiers-phased-complexity)
4. [PCB Design Tools — Open-Source Options](#4-pcb-design-tools--open-source-options)
    - [4.1 KiCad (Recommended)](#41-kicad-recommended)
    - [4.2 LibrePCB](#42-librepcb)
    - [4.3 Horizon EDA](#43-horizon-eda)
    - [4.4 Comparison Table](#44-comparison-table)
5. [The RP2040 Minimal Circuit](#5-the-rp2040-minimal-circuit)
    - [5.1 Required Components](#51-required-components)
    - [5.2 Reference Designs](#52-reference-designs)
    - [5.3 Flash Memory Requirements](#53-flash-memory-requirements)
    - [5.4 Power Regulation](#54-power-regulation)
    - [5.5 USB Circuit](#55-usb-circuit)
    - [5.6 Minimal BOM with LCSC Part Numbers](#56-minimal-bom-with-lcsc-part-numbers)
6. [From Schematic to Physical Board — The Full Workflow](#6-from-schematic-to-physical-board--the-full-workflow)
    - [6.1 Step 1 — Schematic Capture](#61-step-1--schematic-capture)
    - [6.2 Step 2 — Footprint Assignment](#62-step-2--footprint-assignment)
    - [6.3 Step 3 — PCB Layout](#63-step-3--pcb-layout)
    - [6.4 Step 4 — Design Rule Check (DRC)](#64-step-4--design-rule-check-drc)
    - [6.5 Step 5 — Gerber Export](#65-step-5--gerber-export)
    - [6.6 Step 6 — Fabrication](#66-step-6--fabrication)
    - [6.7 Step 7 — Assembly (PCBA)](#67-step-7--assembly-pcba)
    - [6.8 Step 8 — Testing and Bring-Up](#68-step-8--testing-and-bring-up)
    - [6.9 Timeline Estimate](#69-timeline-estimate)
7. [PCB Fabrication Services](#7-pcb-fabrication-services)
    - [7.1 Service Comparison](#71-service-comparison)
    - [7.2 JLCPCB Deep Dive (Recommended)](#72-jlcpcb-deep-dive-recommended)
    - [7.3 Assembly (PCBA) Options](#73-assembly-pcba-options)
    - [7.4 Shipping and Import](#74-shipping-and-import)
8. [Component Sourcing](#8-component-sourcing)
    - [8.1 Distributor Comparison](#81-distributor-comparison)
    - [8.2 LCSC + JLCPCB Integration](#82-lcsc--jlcpcb-integration)
    - [8.3 Sourcing Strategy](#83-sourcing-strategy)
9. [Dilder Board — Schematic Block Diagram](#9-dilder-board--schematic-block-diagram)
    - [9.1 System Block Diagram](#91-system-block-diagram)
    - [9.2 I2C Bus Architecture](#92-i2c-bus-architecture)
    - [9.3 Power Tree](#93-power-tree)
    - [9.4 Estimated Board Dimensions](#94-estimated-board-dimensions)
10. [Learning Path — From Zero to Custom Board](#10-learning-path--from-zero-to-custom-board)
    - [10.1 Phase A — Fundamentals (Week 1-2)](#101-phase-a--fundamentals-week-1-2)
    - [10.2 Phase B — First KiCad Project (Week 3-4)](#102-phase-b--first-kicad-project-week-3-4)
    - [10.3 Phase C — RP2040 Board Design (Week 5-8)](#103-phase-c--rp2040-board-design-week-5-8)
    - [10.4 Phase D — Dilder Board V1 (Week 9-14)](#104-phase-d--dilder-board-v1-week-9-14)
    - [10.5 Phase E — Iteration and Production (Week 15+)](#105-phase-e--iteration-and-production-week-15)
11. [Resources](#11-resources)
    - [11.1 Essential Documentation](#111-essential-documentation)
    - [11.2 Video Tutorials](#112-video-tutorials)
    - [11.3 Books](#113-books)
    - [11.4 Community](#114-community)
    - [11.5 Reference Designs and Open Hardware](#115-reference-designs-and-open-hardware)
12. [Cost Estimate — Dilder Board V1](#12-cost-estimate--dilder-board-v1)
13. [Risk Assessment and Mitigations](#13-risk-assessment-and-mitigations)
14. [Implementation Plan](#14-implementation-plan)

---

## 1. Introduction

The Dilder currently runs on a breadboard with a Raspberry Pi Pico W, a Waveshare e-ink display, and a joystick module connected via jumper wires. This works for development, but a portable, pocket-sized virtual pet needs a purpose-built PCB — a single board integrating the MCU, sensors, charging, and connectors.

This document researches what that transition looks like: the tools, the process, the costs, and the learning curve. It is informed by reverse-engineering the **PicoTop** project (https://github.com/7west/PicoTop/), which successfully designed and fabricated a custom RP2350 board using open-source tools and affordable fabrication services.

---

## 2. Case Study: Reverse-Engineering the PicoTop Board

### 2.1 Project Overview

**PicoTop** is a self-contained computer built around the **RP2350A** chip (the successor to the RP2040). It runs a custom keyboard-only OS called "WestOS" with a shell, text editor, calculator, and hangman game. It outputs 640x480 black-and-white over HDMI, takes USB keyboard input, and runs on a LiPo battery.

The project is fully open-source, with all KiCad schematics, PCB layouts, Gerber files, BOM, and firmware published on GitHub.

**Repo:** https://github.com/7west/PicoTop/

### 2.2 Board Architecture

The PicoTop board integrates everything except the monitor, keyboard, and battery:

```
┌─────────────────────────────────────────────────┐
│                 PicoTop Board Rev2               │
│                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ RP2350A  │   │ W25Q128  │   │ RV-3028  │    │
│  │ QFN-60   │   │ 16MB     │   │ RTC      │    │
│  │ (MCU)    │   │ Flash    │   │ (I2C)    │    │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘    │
│       │              │              │            │
│  ┌────┴──────────────┴──────────────┴────┐      │
│  │            Internal Buses             │      │
│  │    SPI (Flash) / I2C (RTC) / GPIO    │      │
│  └────┬──────┬──────┬──────┬──────┬─────┘      │
│       │      │      │      │      │              │
│  ┌────┴┐ ┌──┴──┐ ┌─┴──┐ ┌┴───┐ ┌┴────┐        │
│  │HDMI │ │USB-A│ │SD  │ │USB │ │JST  │        │
│  │HSTX │ │Host │ │Card│ │-C  │ │Batt │        │
│  └─────┘ └─────┘ └────┘ └────┘ └─────┘        │
│                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │MCP73871  │ │TPS61092  │ │RT6150B   │        │
│  │LiPo     │ │5V Boost  │ │3.3V Buck │        │
│  │Charger  │ │(for HDMI)│ │-Boost    │        │
│  └──────────┘ └──────────┘ └──────────┘        │
│                                                  │
│  12MHz Crystal    2x LEDs    3x Switches        │
│  Piezo Buzzer     Expansion Header (12-pin)     │
└─────────────────────────────────────────────────┘
```

### 2.3 Component Inventory

**Total: ~85 unique component designators, all SMD, all top-side placement.**

#### ICs (6)

| Ref | Part | Function |
|-----|------|----------|
| U1 | RP2350A-QFN60 | Main MCU |
| U2 | MCP73871-2CCI/ML | LiPo battery charge management |
| U3 | TPS61092RSAR | 5V boost converter (for HDMI) |
| U4 | RT6150B-33GQW | 3.3V buck-boost regulator |
| U5 | W25Q128JVS | 16MB SPI NOR flash |
| U6 | RV-3028-C7 | Real-time clock (I2C, battery-backed) |

#### Connectors (6)

| Ref | Part | Function |
|-----|------|----------|
| J1 | 2x06 pin header | Expansion: 3V3, GND, I2C, UART, GPIO, SWD |
| J2 | USB-C 6P (GCT USB4125) | USB-C power/charging input |
| J3 | MSD-7-A (CUI) | Micro SD card slot |
| J4 | USB-A1HSW6 (OST) | USB-A host for keyboard |
| J5 | JST PH 2-pin | LiPo battery connector |
| — | HSTX pins 12-19 | HDMI/DVI output (routed to connector) |

#### Passive Components

- 32 capacitors (0402/0603, 15pF to 100uF)
- 26 resistors (0402, 27R to 1M)
- 2 resistor arrays (4x0603, 220R for HDMI TMDS termination)
- 3 inductors (for power regulation)
- 3 transistors (2N7002, BSS84, BC817 — power switching)
- 2 LEDs, 1 diode, 1 piezo buzzer, 3 switches, 1 crystal (12MHz)

### 2.4 Design Decisions

Key decisions the PicoTop designer made that inform our approach:

| Decision | Rationale | Dilder Relevance |
|----------|-----------|------------------|
| **Bare RP2350A chip** (not a Pico module) | Full control over layout, smaller board, custom pin routing | We should do the same — bare RP2040 gives us control over sensor placement and board size |
| **KiCad for design** | Free, open-source, industry-capable, huge community | Direct match for our needs |
| **JLCPCB for fabrication** | Cheapest, fastest, integrated LCSC parts, supports PCBA | Best option for small-run prototypes |
| **LCSC part numbers in BOM** | Direct integration with JLCPCB assembly service | Follow this pattern exactly |
| **All SMD, all top-side** | Cheaper PCBA (single-side assembly), smaller board | Standard practice for hobby boards |
| **USB-C for charging** | Modern standard, reversible connector | We should use USB-C too |
| **JST PH for battery** | Standard LiPo connector | Our battery uses Molex 1.25mm — we can add both footprints |
| **Expansion header** | Future-proofing with exposed I2C, UART, GPIO, SWD | Critical for Dilder — allows breadboarding new sensors before integrating |
| **Fabrication toolkit plugin** | KiCad plugin generates JLCPCB-ready files automatically | Huge workflow simplification |

### 2.5 Manufacturing Pipeline

The PicoTop's manufacturing workflow:

```
KiCad Schematic → KiCad PCB Layout → DRC Check → Gerber Export
     │                                                │
     │   JLCPCB Fabrication Toolkit Plugin            │
     │   (auto-generates BOM + positions)             │
     ▼                                                ▼
  BOM.csv + positions.csv + Gerbers.zip ──► JLCPCB Upload
                                                      │
                                            ┌─────────┴─────────┐
                                            │ JLCPCB fabricates  │
                                            │ PCB + assembles    │
                                            │ SMD components     │
                                            └─────────┬─────────┘
                                                      │
                                            Boards shipped (~7-14 days)
                                                      │
                                            Hand-solder connectors
                                            (USB, SD, JST, headers)
                                                      │
                                            Flash firmware via SWD
                                                      │
                                            Test and iterate
```

Production backup files in the repo show **14 iterations** between January 22 and February 10, 2026 — about 3 weeks of active PCB design refinement before the final order.

### 2.6 Firmware Architecture

Written in C using the Pico SDK v2.2.0:

- **Core 0:** OS — shell, programs, filesystem, battery/clock monitoring
- **Core 1:** Display (DVI via HSTX + DMA) and USB keyboard (TinyUSB host)
- **Libraries:** Custom FAT16 filesystem, AES-256-CTR encryption, PWM buzzer, RTC with DST, battery ADC monitoring
- **Build:** CMake + Pico SDK extension for VS Code

The dual-core split is notable — display rendering on a dedicated core ensures no UI glitches regardless of what the OS is doing.

### 2.7 Lessons for Dilder

| PicoTop Approach | Dilder Adaptation |
|-----------------|-------------------|
| RP2350A bare chip | Start with RP2040 bare chip (cheaper, more references, proven SDK) |
| 16MB external flash | 2MB is enough for Phase 1-4; add footprint for larger flash |
| MCP73871 battery charger | TP4056/MCP73831 is simpler and cheaper for our needs |
| HDMI output via HSTX | Not needed — we use e-ink SPI instead |
| USB-A host for keyboard | Not needed — we use GPIO buttons/joystick |
| SD card slot | Consider for Phase 4+ (save data, cosmetics, treasure logs) |
| Expansion header | Essential — expose I2C, SPI, UART, ADC for sensor experimentation |
| KiCad + JLCPCB + LCSC | Follow this exact pipeline |

---

## 3. Dilder Custom Board — Target Specification

### 3.1 Component Inventory

Everything the Dilder board needs to integrate:

#### MCU and Core

| Component | Part | Package | Interface | Notes |
|-----------|------|---------|-----------|-------|
| MCU | RP2040 | QFN-56 (7x7mm) | — | Dual-core ARM Cortex-M0+ @ 133MHz, 264KB SRAM |
| Flash | W25Q16JVSSIQ (2MB) | SOIC-8 | SPI (QSPI) | Minimum for firmware. Footprint for W25Q128 (16MB) upgrade |
| Crystal | 12MHz (ABM8-272-T3 or equiv) | 3.2x2.5mm | — | Required for RP2040 clock |
| 3.3V Regulator | XC6206P332MR | SOT-23 | — | 200mA LDO, powers RP2040 + sensors |
| Decoupling | 10x 100nF + 1x 1uF + 1x 10uF | 0402/0603 | — | Per RP2040 hardware design guide |

#### Display

| Component | Part | Interface | Pins |
|-----------|------|-----------|------|
| e-Paper connector | FPC/FFC or 8-pin header | SPI1 | GP8-GP13 (6 GPIO) |

#### Input

| Component | Part | Interface | Pins |
|-----------|------|-----------|------|
| 5-way joystick | DollaTek 5D rocker | GPIO (active LOW) | GP2-GP6 (5 GPIO) |
| BOOTSEL button | Tactile switch | — | Connected to RP2040 QSPI_SS |
| Reset button | Tactile switch | — | Connected to RUN pin |

#### Sensors (I2C Bus)

| Sensor | Part | I2C Address | Function |
|--------|------|-------------|----------|
| Accelerometer | LSM6DSO | 0x6A | Steps, motion, tilt |
| Touch | MPR121 | 0x5A | 12-channel capacitive touch |
| Light | BH1750 | 0x23 | Ambient light (lux) |
| Temp/Humidity | BME280 | 0x76 | Temperature, humidity, pressure |
| GPS | PA1010D | 0x10 | Location (Phase 4B) |
| Magnetometer | QMC5883L | 0x0D | Compass heading (Phase 4B) |

#### Analog Sensor

| Sensor | Part | Interface | Pin |
|--------|------|-----------|-----|
| Microphone | MAX9814 | ADC | GP26 (ADC0) |

#### Audio

| Component | Part | Interface | Pin |
|-----------|------|-----------|-----|
| Piezo buzzer | CSS-0578-SMT or equiv | PWM | GP15 |

#### Power

| Component | Part | Function |
|-----------|------|----------|
| LiPo charger | MCP73831 or TP4056 IC | Single-cell LiPo charging from USB |
| Battery connector | JST PH 2-pin + Molex 1.25mm pad | Battery input |
| USB-C connector | USB4125 (GCT) or equiv | Power input + programming |
| Battery ADC | Voltage divider (200K/100K) | Battery monitoring on ADC3 |
| Power switch | Slide switch | Hard power disconnect |

#### Expansion

| Component | Pins | Signals |
|-----------|------|---------|
| Expansion header | 2x05 or 2x06 | 3V3, GND, I2C0 (SDA/SCL), UART0 (TX/RX), SWD (SWCLK/SWDIO), 2x GPIO |

### 3.2 Interface Map

```
                    RP2040 (QFN-56)
                   ┌───────────────┐
            QSPI ──┤ Flash (2-16MB)│
                   │               │
      SPI1 (6pin)──┤ e-Paper Disp  │
                   │               │
   GPIO (5 pin) ──┤ 5-Way Joystick│
                   │               │
    I2C0 (2 pin)──┤ Sensor Bus    │──► LSM6DSO, MPR121, BH1750,
                   │               │    BME280, PA1010D, QMC5883L
                   │               │
     ADC0 (1 pin)──┤ Microphone    │
                   │               │
     PWM (1 pin) ──┤ Piezo Buzzer  │
                   │               │
     USB (2 pin) ──┤ USB-C         │──► Programming + Charging
                   │               │
     VSYS/GND   ──┤ Power In      │──► LiPo via charger IC
                   │               │
     ADC3 (int) ──┤ Battery Mon   │
                   │               │
   Expansion    ──┤ Header        │──► I2C, UART, SWD, GPIO
                   └───────────────┘

Total GPIO used: 16 (of 26 available)
Total GPIO free: 10 (exposed on expansion header or reserved)
```

### 3.3 Power Architecture

```
                    ┌───────────┐
USB-C 5V ──────────┤ MCP73831  ├──────► LiPo Battery (3.7V)
                    │ Charger   │        JST PH / Molex 1.25mm
                    └─────┬─────┘
                          │
                    ┌─────┴─────┐
                    │ Power MUX │  (Schottky diode or load switch)
                    │ USB/Batt  │
                    └─────┬─────┘
                          │ VSYS (3.0-5.0V)
                    ┌─────┴─────┐
                    │ XC6206    │
                    │ 3.3V LDO  │
                    └─────┬─────┘
                          │ 3V3
            ┌─────────────┼─────────────┐
            │             │             │
         RP2040      Sensors       e-Paper
        (~28mA)     (~3.5mA)     (~5mA peak)

Total active: ~37mA  │  Sleep: ~0.8mA
Battery life (1000mAh): ~6.8 days Tamagotchi mode
```

### 3.4 Board Tiers (Phased Complexity)

Design the board in tiers to manage complexity:

| Tier | Components | Board Complexity | Purpose |
|------|-----------|-----------------|---------|
| **V0 — Breakout** | RP2040 + flash + regulator + USB-C + headers | Simple | Learn the process, validate minimal circuit |
| **V1 — Core** | V0 + e-paper connector + joystick pads + buzzer + battery charger | Medium | Functional Dilder with buttons and display |
| **V2 — Sensors** | V1 + I2C sensor bus + microphone ADC + all sensors onboard | Complex | Full-featured Dilder with all planned sensors |
| **V3 — Production** | V2 optimized: smaller footprint, cleaner routing, enclosure-matched | Advanced | Final form factor for 3D-printed case |

**Recommendation:** Start with V0 to learn KiCad and validate the RP2040 circuit. Then jump to V1 for a usable Dilder board. V2 and V3 come after iteration.

---

## 4. PCB Design Tools — Open-Source Options

### 4.1 KiCad (Recommended)

**Version:** KiCad 10 (released March 2026)

KiCad is the industry-standard open-source EDA (Electronic Design Automation) tool. It handles schematic capture, PCB layout, 3D preview, Gerber export, and BOM generation.

**Key features:**
- Full schematic editor with hierarchical sheets
- PCB layout with interactive router and length tuning
- 3D board viewer (STEP/VRML model support)
- Built-in SPICE simulation
- Fabrication toolkit plugins (JLCPCB, PCBWay)
- Massive component library (KiCad standard + community)
- Cross-platform (Linux, macOS, Windows)
- **New in KiCad 10:** Dark mode, graphical DRC rule editor, PCB Design Blocks, schematic variants

**Website:** https://www.kicad.org/
**Download:** https://www.kicad.org/download/
**Documentation:** https://docs.kicad.org/

### 4.2 LibrePCB

**Version:** LibrePCB 2.0.1 (February 2026)

A newer, simpler alternative focused on clean library management and beginner-friendliness.

**Pros:** Excellent library management, clean UI, lower learning curve
**Cons:** No 3D board view, no hierarchical sheets, smaller community, fewer plugins
**Website:** https://librepcb.org/

### 4.3 Horizon EDA

**Version:** Horizon EDA 2.7

A capable but niche tool with a unique pool-based library system.

**Pros:** Fast interactive router, integrated 3D viewer
**Cons:** Very small community, steep learning curve, limited documentation
**Website:** https://horizon-eda.org/

### 4.4 Comparison Table

| Feature | KiCad 10 | LibrePCB 2.0 | Horizon EDA 2.7 |
|---------|----------|-------------|-----------------|
| Schematic editor | Full, hierarchical | Basic, flat | Full |
| PCB layout | Interactive router | Basic | Interactive router |
| 3D preview | Yes (STEP/VRML) | No | Yes |
| SPICE simulation | Built-in | No | No |
| Fab plugins (JLCPCB) | Yes | No | No |
| Component library | Massive | Growing | Small (pool-based) |
| Community size | Very large | Medium | Small |
| Learning curve | Medium | Low | High |
| RP2040 templates | Yes (many) | Few | None |
| **Recommendation** | **Use this** | Backup option | Skip |

---

## 5. The RP2040 Minimal Circuit

!!! warning "Update: Transition to ESP32-S3"
    The Dilder project has transitioned from the RP2040 to the **ESP32-S3-WROOM-1-N16R8** module for built-in WiFi and BLE support. The RP2040 minimal circuit below is retained for historical reference. See the [ESP32-S3 WROOM-1 reference page](../reference/esp32-s3-wroom1.md) for current hardware details.

The RP2040 chip needs a specific supporting circuit to function. This is well-documented by Raspberry Pi.

### 5.1 Required Components

The absolute minimum to get an RP2040 running:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  12MHz Crystal ──► RP2040 (XIN/XOUT)               │
│  + 2x 33pF load caps                               │
│                                                     │
│  W25Q Flash ──► RP2040 (QSPI pins)                 │
│  + 100nF decoupling                                │
│                                                     │
│  XC6206 3.3V LDO ──► RP2040 DVDD + IOVDD          │
│  + 1uF input cap + 1uF output cap                  │
│                                                     │
│  1.1V core supply: RP2040 internal regulator        │
│  + 1uF cap on VREG_VOUT                            │
│                                                     │
│  6x 100nF decoupling caps (one per DVDD/IOVDD pin) │
│  1x 100nF on USB_VDD                               │
│                                                     │
│  USB-C connector ──► RP2040 (USB_DP, USB_DM)       │
│  + 2x 27R series resistors                          │
│  + 2x 5.1K CC resistors (USB-C identification)     │
│                                                     │
│  BOOTSEL button ──► QSPI_SS (pull-up to 3V3)       │
│  RESET button ──► RUN pin (pull-up to 3V3)          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 5.2 Reference Designs

| Resource | URL | Notes |
|----------|-----|-------|
| **RP2040 Hardware Design Guide** | https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf | **Start here.** Official guide with full schematics, layout guidelines, and BOM |
| **Pico W schematic** | https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf | The board we currently use — see how they implemented the minimal circuit |
| **RP2040 datasheet** | https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf | Full chip specification |
| **PicoTop schematic** | https://github.com/7west/PicoTop/blob/main/HARDWARE/PicoTopSchematic.pdf | Real-world custom board (uses RP2350, but power/flash circuit is similar) |
| **Raspberry Pi Design Files** | https://datasheets.raspberrypi.com/pico/RPi-Pico-R3-PUBLIC-20200119.zip | Official KiCad files for the Pico board |

### 5.3 Flash Memory Requirements

The RP2040 boots from external QSPI flash. Requirements:

- **Must be Winbond W25Q series** (or compatible with the RP2040 boot ROM's QSPI sequence)
- Minimum: **W25Q16JVSSIQ** (2MB) — enough for our firmware
- Maximum practical: **W25Q128JVSIQ** (16MB) — for future expansion
- Package: SOIC-8 (easy to hand-solder if needed)
- Connected via 6-pin QSPI: CS, CLK, D0-D3

### 5.4 Power Regulation

The RP2040 needs two voltage rails:

| Rail | Voltage | Current | Source |
|------|---------|---------|--------|
| IOVDD + DVDD | 3.3V | ~100mA (MCU + sensors) | External LDO (XC6206P332MR) |
| Core | 1.1V | ~50mA | RP2040 internal regulator (fed from 3.3V via VREG_VIN) |

The XC6206P332MR is a 200mA LDO in SOT-23 package. It accepts 1.8-6V input — perfect for both USB (5V) and LiPo (3.0-4.2V) sources.

For higher current (if many sensors are active), consider the **AP2112K-3.3** (600mA) or **RT6150B** (buck-boost, used by the Pico itself).

### 5.5 USB Circuit

USB-C with power-only (no data) is simpler, but we want USB data for programming:

```
USB-C Connector
  VBUS ──► Schottky diode ──► VSYS
  GND  ──► GND
  D+   ──► 27R ──► RP2040 USB_DP
  D-   ──► 27R ──► RP2040 USB_DM
  CC1  ──► 5.1K ──► GND   (identifies as USB device)
  CC2  ──► 5.1K ──► GND
```

### 5.6 Minimal BOM with LCSC Part Numbers

| Component | Value | Package | Qty | LCSC Part | ~Cost |
|-----------|-------|---------|-----|-----------|-------|
| RP2040 | — | QFN-56 | 1 | C2040 | $0.70 |
| W25Q16JVSSIQ | 2MB Flash | SOIC-8 | 1 | C131024 | $0.35 |
| XC6206P332MR | 3.3V LDO | SOT-23 | 1 | C5446 | $0.15 |
| 12MHz Crystal | ABM8 equiv | 3215 | 1 | C9002 | $0.20 |
| 100nF Caps | MLCC | 0402 | 8 | C1525 | $0.01/ea |
| 1uF Caps | MLCC | 0402 | 3 | C52923 | $0.01/ea |
| 10uF Cap | MLCC | 0603 | 1 | C19702 | $0.02 |
| 33pF Caps | Crystal load | 0402 | 2 | C1560 | $0.01/ea |
| 27R Resistors | USB series | 0402 | 2 | C25100 | $0.01/ea |
| 5.1K Resistors | USB CC | 0402 | 2 | C25905 | $0.01/ea |
| 10K Resistors | Pull-up | 0402 | 2 | C25744 | $0.01/ea |
| 1K Resistor | LED current | 0402 | 1 | C11702 | $0.01 |
| USB-C 6P | Power + data | — | 1 | C2765186 | $0.30 |
| Tactile Switch | BOOTSEL | 3x4mm | 1 | C318884 | $0.05 |
| Tactile Switch | Reset | 3x4mm | 1 | C318884 | $0.05 |
| LED | Status | 0603 | 1 | C72043 | $0.03 |
| **Total** | | | **~28** | | **~$2.00** |

The RP2040 minimal circuit costs about **$2 in components** — remarkably cheap.

---

## 6. From Schematic to Physical Board — The Full Workflow

### 6.1 Step 1 — Schematic Capture

**Tool:** KiCad Schematic Editor (Eeschema)

Draw the circuit diagram connecting all components logically. This is the "what connects to what" step — no physical layout yet.

**Tasks:**
1. Create a new KiCad project
2. Place component symbols from the KiCad library (RP2040, capacitors, etc.)
3. Draw wires connecting pins
4. Add power flags (VCC, GND)
5. Annotate components (R1, R2, C1, C2, U1, etc.)
6. Run Electrical Rules Check (ERC)

**Tips:**
- Use hierarchical sheets to organize: one sheet per subsystem (MCU, power, sensors, connectors)
- Copy the RP2040 reference design schematic as a starting point
- Label nets clearly (SDA, SCL, MOSI, etc.)

### 6.2 Step 2 — Footprint Assignment

**Tool:** KiCad Footprint Assignment Tool

Map each schematic symbol to a physical PCB footprint (the copper pads the component solders to).

**Tasks:**
1. Open the footprint assignment dialog
2. Assign footprints: e.g., RP2040 → QFN-56-1EP_7x7mm_P0.4mm
3. Use the KiCad standard library for common passives (0402, 0603, SOT-23)
4. Download or create custom footprints for unusual parts

### 6.3 Step 3 — PCB Layout

**Tool:** KiCad PCB Editor (Pcbnew)

Arrange components physically on the board and route copper traces between them. This is the most time-consuming and skill-intensive step.

**Tasks:**
1. Import netlist from schematic
2. Define board outline (edge cuts)
3. Place components — group by function, minimize trace lengths
4. Route traces — start with critical signals (QSPI, USB, crystal), then power, then I2C/SPI
5. Add ground plane (copper fill on both sides)
6. Add via stitching for ground continuity
7. Add silkscreen labels

**Layout guidelines for RP2040:**
- Place crystal within 5mm of XIN/XOUT pins
- Place flash chip within 10mm of QSPI pins
- Keep USB traces matched in length (±0.5mm)
- Place decoupling caps as close as possible to power pins
- Use 0.25mm traces for signals, 0.5mm for power, wider for VSYS/VBUS

### 6.4 Step 4 — Design Rule Check (DRC)

**Tool:** KiCad DRC

Automated check for:
- Trace-to-trace clearance violations
- Unconnected nets
- Minimum trace width violations
- Drill size violations
- Courtyard overlaps

**Must pass with zero errors before proceeding.**

### 6.5 Step 5 — Gerber Export

**Tool:** KiCad Plot / JLCPCB Fabrication Toolkit

Generate the manufacturing files:

| File | Purpose |
|------|---------|
| `*.gtl` / `*.gbl` | Front/back copper layers |
| `*.gts` / `*.gbs` | Front/back solder mask |
| `*.gto` / `*.gbo` | Front/back silkscreen |
| `*.gm1` | Board outline (edge cuts) |
| `*.drl` | Drill file (hole locations and sizes) |
| `bom.csv` | Bill of materials (with LCSC part numbers) |
| `positions.csv` | Component placement coordinates for PCBA |

**The JLCPCB Fabrication Toolkit KiCad plugin** automates this entire step — install it and it generates all files in the correct format with one click.

**Plugin:** https://github.com/Bouni/kicad-jlcpcb-tools

### 6.6 Step 6 — Fabrication

Upload the Gerber zip to your chosen fab house.

**JLCPCB process:**
1. Go to https://jlcpcb.com
2. Click "Order Now" → upload Gerber zip
3. Configure: layers (2), thickness (1.6mm), color (green/black), surface finish (HASL)
4. Review auto-detected board dimensions and price
5. Add PCBA (assembly) if desired — upload BOM and positions CSV
6. Pay and wait (~3-5 days production + 5-10 days shipping)

### 6.7 Step 7 — Assembly (PCBA)

Two approaches:

**Option A — JLCPCB PCBA (recommended for SMD):**
- Upload BOM + positions files with the Gerber order
- JLCPCB picks and places all SMD components
- You receive fully assembled boards (except through-hole connectors)
- Cost: ~$8 setup + per-component charges

**Option B — Hand assembly:**
- Order bare PCBs + components separately
- Apply solder paste with a stencil (order from JLCPCB too)
- Place components with tweezers
- Reflow in a hot air station or reflow oven (~$50-100 for a T962)
- **QFN-56 (RP2040) is very difficult to hand-solder** — PCBA recommended for this chip

### 6.8 Step 8 — Testing and Bring-Up

1. **Visual inspection** — check for solder bridges, missing components, tombstoned parts
2. **Power test** — connect USB, measure 3.3V on the LDO output with a multimeter
3. **BOOTSEL test** — hold BOOTSEL, connect USB, check if the board appears as a USB mass storage device (RPI-RP2)
4. **Flash firmware** — drag a UF2 file onto the USB drive, or use SWD with a debug probe
5. **Blink test** — flash a simple LED blink program
6. **Peripheral test** — test each subsystem: display, buttons, I2C sensors, buzzer, battery ADC

### 6.9 Timeline Estimate

| Phase | Duration | Notes |
|-------|----------|-------|
| Learn KiCad basics | 1-2 weeks | Tutorials, practice projects |
| Schematic capture | 3-5 days | Can reference PicoTop and Pico schematics |
| PCB layout | 5-10 days | Most time-consuming step |
| Review and DRC | 1-2 days | Triple-check before ordering |
| Fabrication + shipping | 7-14 days | JLCPCB standard |
| Assembly + testing | 2-3 days | Hand-solder connectors, flash firmware |
| **Total (first board)** | **5-8 weeks** | Subsequent revisions: 2-3 weeks |

---

## 7. PCB Fabrication Services

### 7.1 Service Comparison

| Service | Location | 5 Boards (2-layer) | Turnaround | PCBA | Strengths |
|---------|----------|-------------------|------------|------|-----------|
| **JLCPCB** | China | **$2** | 1-3 days prod + 5-10 ship | Yes ($8+) | Cheapest, fastest, LCSC integration |
| **PCBWay** | China | $5 | 1-3 days + 5-10 ship | Yes | Good quality, easy UI |
| **Seeed Fusion** | China | $4.90 (10 boards) | 4-7 days + 5-14 ship | Yes | Free assembly promos, Seeed ecosystem |
| **OSH Park** | USA | $5/sq inch | 12 days (included shipping) | No | US-made, purple boards, no shipping cost |
| **Aisler** | Germany | EUR 12.20 | 3-5 days + 2-3 ship (EU) | Yes | Best for EU, fast local delivery |
| **AllPCB** | China | $5 | 1-3 days + 5-10 ship | Yes | Low-volume specialty options |

### 7.2 JLCPCB Deep Dive (Recommended)

| Spec | Value |
|------|-------|
| Minimum order | 5 boards |
| 2-layer price | $2 for 5 boards (100x100mm max at this price) |
| 4-layer price | $8 for 5 boards |
| PCB thickness | 0.6mm, 0.8mm, 1.0mm, 1.2mm, 1.6mm (default), 2.0mm |
| Colors | Green (cheapest), black, white, blue, red, yellow, purple |
| Surface finish | HASL (free), Lead-free HASL (+$1), ENIG (+$7) |
| Min trace/space | 0.1mm/0.1mm (3.5mil) |
| Min drill | 0.2mm |
| Production time | 24 hours (express) to 3 days (standard) |
| PCBA setup fee | $8 (one-time per order) |
| PCBA per part | $0.0017/joint (common parts from LCSC Basic library are free setup) |

**JLCPCB Fabrication Toolkit Plugin** for KiCad:
- Generates Gerbers, BOM, and position files in JLCPCB's exact format
- Auto-fills LCSC part numbers
- One-click export — no manual file preparation needed
- **Install:** KiCad → Plugin Manager → search "JLCPCB" → Install

### 7.3 Assembly (PCBA) Options

| Option | Cost | Best For |
|--------|------|----------|
| **JLCPCB Economic** | $8 setup + parts | Standard parts from LCSC Basic library |
| **JLCPCB Standard** | $8 setup + parts | Extended library + consigned parts |
| **Hand solder** | Your time + tools | Through-hole connectors, prototyping |
| **Stencil + reflow** | $7 stencil + reflow oven | Full hand assembly when you want control |

### 7.4 Shipping and Import

| Method | Cost | Time | Notes |
|--------|------|------|-------|
| JLCPCB Global Standard | $1-3 | 7-14 days | Cheapest |
| JLCPCB DHL Express | $15-25 | 3-5 days | Fast, tracked |
| OSH Park | Included | 12 days | US domestic, free shipping |
| Aisler (to EU) | EUR 4-7 | 2-3 days | No customs (EU origin) |

**EU import note:** Orders from China under EUR 150 are subject to VAT (19-21%) on import. JLCPCB pre-pays EU VAT via IOSS on most shipments, so no customs surprise.

---

## 8. Component Sourcing

### 8.1 Distributor Comparison

| Distributor | Location | Strengths | Pricing | Min Order |
|-------------|----------|-----------|---------|-----------|
| **LCSC** | China | Cheapest, JLCPCB integration | 30-50% below Western | 1 piece |
| **DigiKey** | USA | Massive inventory, fast shipping | Standard | 1 piece |
| **Mouser** | USA | Wide selection, datasheets | Standard | 1 piece |
| **Farnell/Newark** | UK/USA | Good EU source | Standard | 1 piece |
| **AliExpress** | China | Cheapest for breakout modules | Budget | Varies |

### 8.2 LCSC + JLCPCB Integration

The killer advantage of LCSC: when you order PCBA from JLCPCB, components from the **LCSC Basic Parts Library** (~4,000 common parts) have **zero placement fee** — you only pay for the component itself.

**LCSC Extended Parts Library** (~100,000 parts) has a small placement surcharge (~$3/unique part).

**Workflow:**
1. When designing in KiCad, note the LCSC part number for each component
2. Add LCSC part numbers to your schematic as a custom field
3. The JLCPCB fabrication toolkit reads these and generates the BOM automatically
4. When you order PCBA, JLCPCB pulls the parts directly from LCSC

### 8.3 Sourcing Strategy

| Component Type | Source | Reason |
|---------------|--------|--------|
| RP2040, flash, LDO, passives | LCSC (via JLCPCB PCBA) | Cheapest, auto-placed |
| Sensors (LSM6DSO, BME280, etc.) | LCSC Extended Library | Available for PCBA |
| USB-C connector | LCSC | Standard part |
| Joystick module | AliExpress/Amazon | Pre-assembled module, hand-solder |
| e-Paper display | Waveshare direct / Amazon | Pre-assembled module with FPC |
| LiPo battery | Amazon/AliExpress | Standard pouch cell |
| Crystal, switches | LCSC | Standard parts |

---

## 9. Dilder Board — Schematic Block Diagram

### 9.1 System Block Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        DILDER BOARD V1                           │
│                                                                  │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐  │
│  │  USB-C   │────►│ MCP73831│────►│  LiPo   │     │ Slide   │  │
│  │  Power   │     │ Charger │     │ Battery │     │ Switch  │  │
│  │  + Data  │     │         │     │ JST PH  │     │ On/Off  │  │
│  └────┬─────┘     └────┬────┘     └────┬────┘     └────┬────┘  │
│       │                │               │               │        │
│       │         ┌──────┴───────────────┴───────────────┘        │
│       │         │  VSYS (3.0-5.0V)                              │
│       │         │                                                │
│       │    ┌────┴─────┐          ┌──────────┐                   │
│       │    │ XC6206   │          │ Battery  │                   │
│       │    │ 3.3V LDO │          │ ADC      │                   │
│       │    └────┬─────┘          │ (GP29)   │                   │
│       │         │ 3V3             └──────────┘                   │
│  ┌────┴─────────┴────────────────────────────────┐              │
│  │                   RP2040                       │              │
│  │                                                │              │
│  │  QSPI ──► W25Q16 Flash (2MB)                  │              │
│  │  XIN  ──► 12MHz Crystal                        │              │
│  │                                                │              │
│  │  GP8-13 (SPI1) ──► e-Paper Display Connector   │              │
│  │  GP2-6  (GPIO) ──► 5-Way Joystick Pads         │              │
│  │  GP15   (PWM)  ──► Piezo Buzzer                │              │
│  │  GP26   (ADC)  ──► MAX9814 Microphone          │              │
│  │                                                │              │
│  │  GP16 (SDA) ──┬──► LSM6DSO (0x6A)             │              │
│  │  GP17 (SCL) ──┤──► MPR121  (0x5A)             │              │
│  │    I2C0       ├──► BH1750  (0x23)             │              │
│  │               ├──► BME280  (0x76)             │              │
│  │               ├──► PA1010D (0x10) [DNP V1]    │              │
│  │               └──► QMC5883L(0x0D) [DNP V1]    │              │
│  │                                                │              │
│  │  USB_DP/DM ──► USB-C (data lines)             │              │
│  │  SWD      ──► Expansion Header                │              │
│  │  UART0    ──► Expansion Header                │              │
│  └───────────────────────────────────────────────┘              │
│                                                                  │
│  ┌──────────────────────────────────────────┐                   │
│  │  Expansion Header (2x05 or 2x06)        │                   │
│  │  3V3, GND, SDA, SCL, TX, RX,            │                   │
│  │  SWCLK, SWDIO, GP0, GP1                 │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                  │
│  BOOTSEL Button    RESET Button    Status LED                   │
└──────────────────────────────────────────────────────────────────┘

DNP = "Do Not Place" — footprint present but component omitted in V1
```

### 9.2 I2C Bus Architecture

All sensors share a single I2C0 bus with 4.7K pull-up resistors:

```
3V3 ──┬──── 4.7K ────┬──── SDA (GP16)
      │              │
      └──── 4.7K ────┼──── SCL (GP17)
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────┴──┐   ┌────┴──┐   ┌────┴──┐
   │LSM6DSO│   │MPR121 │   │BH1750 │   ... (BME280, PA1010D, QMC5883L)
   │ 0x6A  │   │ 0x5A  │   │ 0x23  │
   └───────┘   └───────┘   └───────┘

Bus speed: 400kHz (Fast Mode)
Max devices: 6 (no address conflicts)
Wire length: <15cm (PCB traces = sub-cm, ideal)
```

### 9.3 Power Tree

```
USB-C 5V ──► Schottky (BAT54S) ──┬──► MCP73831 ──► LiPo (3.7V)
                                  │
LiPo 3.7V ──────────────────────┘
                                  │
                            VSYS (3.0-5.0V)
                                  │
                     ┌────────────┴────────────┐
                     │                         │
              ┌──────┴──────┐           ┌──────┴──────┐
              │   XC6206    │           │  200K/100K  │
              │   3.3V LDO  │           │  Voltage    │
              │   (200mA)   │           │  Divider    │
              └──────┬──────┘           └──────┬──────┘
                     │                         │
                   3V3 rail                  ADC3 (GP29)
                     │                    Battery monitor
        ┌────────────┼─────────────┐
        │            │             │
     RP2040       Sensors      Buzzer
     (~28mA)     (~3.5mA)    (~5mA peak)
                                e-Paper
                              (~5mA peak)
```

### 9.4 Estimated Board Dimensions

Based on the Dilder enclosure design (88 x 34 x 19mm):

| Constraint | Value |
|-----------|-------|
| Max PCB width | ~32mm (2mm clearance per side) |
| Max PCB length | ~82mm (3mm clearance per end) |
| Max component height (top) | ~8mm (below display) |
| Max component height (bottom) | ~5mm (above battery) |
| Layer count | 2 (minimum) or 4 (better routing, slightly more expensive) |
| PCB thickness | 1.0mm or 1.2mm (thinner = more room for battery) |

**Comparison with PicoTop:** The PicoTop board fits in a custom 3D-printed case with a similar design philosophy — PCB dimensions matched to case ID.

---

## 10. Learning Path — From Zero to Custom Board

### 10.1 Phase A — Fundamentals (Week 1-2)

**Goal:** Understand PCB design concepts and get comfortable with KiCad.

| Task | Resource | Time |
|------|----------|------|
| Install KiCad 10 | https://www.kicad.org/download/ | 15 min |
| Complete the KiCad Getting Started tutorial | https://docs.kicad.org/master/en/getting_started_in_kicad/getting_started_in_kicad.html | 3-4 hours |
| Watch Phil's Lab "KiCad 6 STM32 Board" tutorial | https://www.youtube.com/watch?v=aVUqaB0IMh4 | 2 hours |
| Watch DigiKey's "How to Make a Custom PCB" series | Search "DigiKey KiCad RP2040" on YouTube | 2 hours |
| Read: What is a PCB? (layers, traces, vias, pads) | https://www.youtube.com/watch?v=C1Nt3T4gMBE (Phil's Lab Intro) | 1 hour |
| Practice: Design a simple LED + resistor + USB-C board | Self-directed in KiCad | 4-6 hours |

### 10.2 Phase B — First KiCad Project (Week 3-4)

**Goal:** Design, order, and receive a simple PCB.

| Task | Resource | Time |
|------|----------|------|
| Design a breakout board for the RP2040 with just: MCU + flash + crystal + LDO + USB-C + LED | RP2040 Hardware Design Guide (PDF) | 8-12 hours |
| Install JLCPCB Fabrication Toolkit plugin | https://github.com/Bouni/kicad-jlcpcb-tools | 30 min |
| Run DRC, fix all errors | KiCad built-in | 2-3 hours |
| Export Gerbers and order from JLCPCB (5 boards, ~$2 + $8 PCBA) | https://jlcpcb.com | 1 hour |
| Wait for delivery | — | 7-14 days |
| Flash firmware and test | Pico SDK "blink" example | 2-3 hours |

**This is the most important step.** Getting a real board in your hands — even a simple one — demystifies the entire process.

### 10.3 Phase C — RP2040 Board Design (Week 5-8)

**Goal:** Add peripherals to the RP2040 breakout.

| Task | Resource | Time |
|------|----------|------|
| Read the full RP2040 Hardware Design Guide | https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf | 3-4 hours |
| Study the PicoTop schematic (PDF) | https://github.com/7west/PicoTop/blob/main/HARDWARE/PicoTopSchematic.pdf | 2 hours |
| Study the official Pico W schematic | https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf | 2 hours |
| Add battery charging circuit (MCP73831) | MCP73831 datasheet application circuit | 4-6 hours |
| Add I2C header for external sensors | — | 2 hours |
| Add e-paper display connector | Match existing wiring (GP8-13) | 2 hours |
| Add button/joystick pads | Match existing wiring (GP2-6) | 2 hours |
| Order V1 board from JLCPCB | — | 1 hour + 7-14 day wait |
| Test all peripherals | Existing Dilder firmware | 3-5 hours |

### 10.4 Phase D — Dilder Board V1 (Week 9-14)

**Goal:** Full Dilder board with integrated sensors.

| Task | Resource | Time |
|------|----------|------|
| Add all I2C sensors to schematic (LSM6DSO, MPR121, BH1750, BME280) | Datasheets for each | 8-12 hours |
| Add MAX9814 microphone circuit | MAX9814 datasheet | 2-3 hours |
| Add piezo buzzer + PWM driver | — | 1-2 hours |
| Add GPS + magnetometer footprints (DNP) | PA1010D, QMC5883L datasheets | 3-4 hours |
| Add expansion header | — | 1 hour |
| PCB layout — fit everything in 82x32mm | — | 15-20 hours |
| 3D preview — verify alignment with enclosure | KiCad 3D viewer + case STL | 2-3 hours |
| Order V1 boards + PCBA from JLCPCB | — | 1 hour + 7-14 day wait |
| Full integration testing | All Dilder firmware | 5-10 hours |

### 10.5 Phase E — Iteration and Production (Week 15+)

| Task | Notes |
|------|-------|
| Fix issues found in V1 testing | Layout tweaks, component changes |
| Order V2 revision | — |
| Optimize for enclosure fit | Match 3D-printed case exactly |
| Consider 4-layer board for better routing | +$6 from JLCPCB |
| Design flex cable for e-paper connection | If direct FPC routing is needed |
| Document final design for the community | Publish KiCad files to the Dilder repo |

---

## 11. Resources

### 11.1 Essential Documentation

| Resource | URL | Why |
|----------|-----|-----|
| **RP2040 Hardware Design Guide** | https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf | **The** reference for RP2040 board design |
| **RP2040 Datasheet** | https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf | Full chip specification |
| **Pico W Datasheet** | https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf | Reference schematic for a working RP2040 board |
| **Pico W Design Files (KiCad)** | https://datasheets.raspberrypi.com/pico/RPi-Pico-R3-PUBLIC-20200119.zip | Official KiCad project files |
| **KiCad 10 Documentation** | https://docs.kicad.org/ | Tool reference |
| **PicoTop Schematic** | https://github.com/7west/PicoTop/blob/main/HARDWARE/PicoTopSchematic.pdf | Real-world custom RP2350 board |
| **PicoTop KiCad Files** | https://github.com/7west/PicoTop/tree/main/HARDWARE/PicoTop%20Board%20Rev2 | Full KiCad project to study |

### 11.2 Video Tutorials

| Channel / Video | URL | Topic |
|----------------|-----|-------|
| **Phil's Lab** — "How to Make a Custom PCB" | https://www.youtube.com/c/PhilsLab | Best PCB design YouTube channel, period |
| **Phil's Lab** — "KiCad 6 STM32 PCB Design" | https://www.youtube.com/watch?v=aVUqaB0IMh4 | Full KiCad walkthrough (applies to RP2040 too) |
| **DigiKey** — "RP2040 KiCad Tutorial" | Search: "DigiKey RP2040 KiCad" | Two-part series designing an RP2040 board |
| **Robert Feranec** — PCB Design courses | https://www.youtube.com/c/RobertFeranec | Advanced layout techniques |
| **EEVblog** — "PCB Design Tutorial" | https://www.youtube.com/user/EEVblog | Component selection, layout tips |
| **SiliconWit** — RP2040 custom board course | Search: "SiliconWit RP2040 custom board" | Builds a real RP2040 board start to finish |

### 11.3 Books

| Title | Author | Notes |
|-------|--------|-------|
| **"Design an RP2040 board with KiCad"** | Raspberry Pi Press | Official step-by-step guide, best starting point |
| **"The Art of Electronics"** (3rd ed) | Horowitz & Hill | The electronics bible — reference, not cover-to-cover |
| **"PCB Design for Real-World EMI Control"** | Archambeault | Advanced — for when you care about signal integrity |

### 11.4 Community

| Community | URL | Notes |
|-----------|-----|-------|
| **KiCad Forums** | https://forum.kicad.info/ | Official, very helpful |
| **r/PrintedCircuitBoard** | https://reddit.com/r/PrintedCircuitBoard | PCB design reviews and help |
| **r/AskElectronics** | https://reddit.com/r/AskElectronics | General electronics Q&A |
| **EEVblog Forum** | https://www.eevblog.com/forum/ | Deep technical discussions |
| **Raspberry Pi Forums** | https://forums.raspberrypi.com/ | RP2040-specific questions |
| **KiCad Discord** | https://discord.gg/kicad | Real-time help |
| **JLCPCB Discord/Forum** | https://jlcpcb.com/help | Fabrication-specific questions |

### 11.5 Reference Designs and Open Hardware

| Project | URL | Relevance |
|---------|-----|-----------|
| **PicoTop** | https://github.com/7west/PicoTop/ | Custom RP2350 board with full KiCad files |
| **Raspberry Pi Pico** | https://datasheets.raspberrypi.com/pico/RPi-Pico-R3-PUBLIC-20200119.zip | Official RP2040 reference design |
| **Adafruit Feather RP2040** | https://github.com/adafruit/Adafruit-Feather-RP2040-PCB | Open-source RP2040 board with battery charger |
| **SparkFun Thing Plus RP2040** | https://github.com/sparkfun/SparkFun_Thing_Plus_RP2040 | Another open RP2040 reference |
| **Pwnagotchi** | https://github.com/evilsocket/pwnagotchi | Inspiration project — e-ink + RPi |
| **Watchy** | https://github.com/sqfmi/Watchy | ESP32 e-paper watch — similar form factor goals |

---

## 12. Cost Estimate — Dilder Board V1

### Per-Board Cost (5-board run with PCBA)

| Item | Cost (5 boards) | Per Board |
|------|-----------------|-----------|
| PCB fabrication (2-layer, JLCPCB) | $2 | $0.40 |
| PCBA setup fee | $8 | $1.60 |
| RP2040 + flash + LDO + passives (LCSC) | ~$15 | ~$3.00 |
| MCP73831 charger + battery circuit | ~$5 | ~$1.00 |
| I2C sensors (LSM6DSO, MPR121, BH1750, BME280) | ~$40 | ~$8.00 |
| MAX9814 microphone | ~$10 | ~$2.00 |
| Piezo buzzer | ~$3 | ~$0.60 |
| Connectors (USB-C, JST, headers) | ~$8 | ~$1.60 |
| Crystal, switches, LEDs, diodes | ~$5 | ~$1.00 |
| Shipping (JLCPCB to EU) | ~$10 | ~$2.00 |
| **Total** | **~$106** | **~$21.20** |

### One-Time Costs

| Item | Cost | Notes |
|------|------|-------|
| Soldering iron (for connectors) | ~$30-50 | Pinecil or TS100 recommended |
| Solder + flux | ~$15 | Lead-free for EU compliance |
| Multimeter | ~$15-25 | Essential for testing |
| Debug probe (Pico as SWD debugger) | $0 | Use a spare Pico W as a debug probe (Picoprobe firmware) |
| **Total one-time** | **~$60-90** | Only needed once |

### Comparison: Breadboard vs Custom Board

| Metric | Breadboard Prototype | Custom PCB |
|--------|---------------------|-----------|
| Size | ~170x55mm (half breadboard) | ~82x32mm |
| Weight | ~120g (board + wires) | ~15g (PCB only) |
| Reliability | Loose wires, intermittent contacts | Permanent, vibration-proof |
| Assembly time | 30 min (per rebuild) | 0 (arrives assembled) |
| Per-unit cost | ~$45 (Pico W + sensors + breadboard) | ~$21 |
| Enclosure fit | No | Yes (designed to match) |

---

## 13. Risk Assessment and Mitigations

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| **RP2040 QFN soldering failure** | High | Low (if using PCBA) | Use JLCPCB PCBA — they handle QFN placement with pick-and-place machines |
| **Wrong footprint for a component** | High | Medium | Triple-check footprints against datasheets. Order one component of each type and physically verify before finalizing PCB |
| **I2C bus issues with many sensors** | Medium | Medium | Use 4.7K pull-ups, keep traces short (<15cm), add test points for debugging with oscilloscope/logic analyzer |
| **Power regulation issues** | High | Low | Follow RP2040 hardware design guide exactly. Use the same LDO (XC6206) as the reference design |
| **Board too large for enclosure** | Medium | Low | Design PCB outline from the enclosure CAD model first, then fit components inside |
| **Component out of stock at LCSC** | Medium | Medium | Check LCSC stock before finalizing BOM. Identify alternate parts for each critical component |
| **First board doesn't work** | High | High (normal) | Budget for 2-3 board revisions. Order 5 boards minimum. Use the expansion header to debug individual subsystems |
| **USB-C not recognized** | Medium | Medium | Follow the USB circuit exactly from the Pico reference. Add test points on D+/D- |

---

## 14. Implementation Plan

### Milestone Timeline

```
Week 1-2:   LEARN
            ├── Install KiCad 10
            ├── Complete Getting Started tutorial
            ├── Watch Phil's Lab tutorials
            └── Design a practice LED board

Week 3-4:   FIRST BOARD (V0 — RP2040 Breakout)
            ├── Schematic: RP2040 + flash + LDO + USB-C + LED
            ├── PCB layout
            ├── Order from JLCPCB (with PCBA)
            └── While waiting: study PicoTop and Pico schematics

Week 5-6:   TEST V0
            ├── Receive boards
            ├── Hand-solder connectors
            ├── Flash Pico SDK blink test
            └── Validate: USB works, 3.3V stable, flash boots

Week 7-8:   DILDER BOARD V1 — SCHEMATIC
            ├── Add battery charging (MCP73831)
            ├── Add e-paper connector (SPI1, 8-pin)
            ├── Add joystick pads (5x GPIO + GND)
            ├── Add I2C sensor bus (LSM6DSO, MPR121, BH1750, BME280)
            ├── Add microphone (MAX9814 + ADC)
            ├── Add buzzer (PWM)
            ├── Add expansion header
            └── Add DNP footprints for GPS + magnetometer

Week 9-10:  DILDER BOARD V1 — PCB LAYOUT
            ├── Place components to match enclosure dimensions
            ├── Route traces (critical signals first)
            ├── Ground plane, via stitching
            ├── DRC — zero errors
            ├── 3D preview — check enclosure fit
            └── Order from JLCPCB (PCB + PCBA)

Week 11-12: TEST V1
            ├── Receive boards
            ├── Hand-solder connectors + joystick
            ├── Flash Dilder firmware
            ├── Test every subsystem
            └── Document issues for V2

Week 13-14: ITERATE
            ├── Fix V1 issues in schematic/layout
            ├── Order V2 if needed
            └── Begin integrating with 3D-printed enclosure

Week 15+:   PRODUCTION
            ├── Finalize V2/V3 design
            ├── Publish KiCad files to Dilder repo
            ├── Document build guide for community
            └── Consider small production run
```

### Decision Points

| Decision | When | Options |
|----------|------|---------|
| RP2040 vs RP2350 | Before V0 order | RP2040 is cheaper, better documented, proven. RP2350 has more RAM/flash and HSTX. **Recommend RP2040 for V1.** |
| 2-layer vs 4-layer | Before V1 order | 2-layer is $2 (simpler routing, bigger board). 4-layer is $8 (better signal integrity, smaller board). **Start with 2-layer.** |
| Sensors onboard vs header | Before V1 schematic | Onboard is more compact but harder to debug. Headers allow swapping sensors. **V1: sensors on expansion header. V2: onboard.** |
| Flash size | Before V0 order | 2MB is enough for firmware. 16MB enables SD-less storage. **Use 2MB footprint with 16MB compatible.** |

---

*Document version: 1.0 — Created 2026-04-14*
*This is a living document. Update as the PCB design progresses.*
