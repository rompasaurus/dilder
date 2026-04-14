# ESP32-S3-WROOM-1 — PCB Design Research & Layout Guide

> Research document for designing the Dilder custom PCB around the ESP32-S3-WROOM-1-N16R8 module. Covers module specs, antenna constraints, component placement strategy, reference designs, and 4-layer routing considerations.

---

## Table of Contents

1. [Module Overview](#1-module-overview)
2. [Physical Dimensions & Pin Layout](#2-physical-dimensions--pin-layout)
3. [Antenna Keep-Out Zone](#3-antenna-keep-out-zone)
4. [Ground Pad & Thermal Design](#4-ground-pad--thermal-design)
5. [Power Supply Design](#5-power-supply-design)
6. [USB-C Integration (Native USB-OTG)](#6-usb-c-integration-native-usb-otg)
7. [GPIO Assignment for Dilder](#7-gpio-assignment-for-dilder)
8. [e-Paper Display Connection (24-pin FPC)](#8-e-paper-display-connection-24-pin-fpc)
9. [Component Placement Strategy](#9-component-placement-strategy)
10. [Open-Source Reference Designs](#10-open-source-reference-designs)
11. [4-Layer Stackup & Routing](#11-4-layer-stackup--routing)
12. [JLCPCB 4-Layer Manufacturing](#12-jlcpcb-4-layer-manufacturing)
13. [Comparison: ESP32-S3 vs RP2040](#13-comparison-esp32-s3-vs-rp2040)
14. [Resources & Datasheets](#14-resources--datasheets)

---

## 1. Module Overview

| Parameter | Value |
|-----------|-------|
| **Module** | ESP32-S3-WROOM-1-N16R8 |
| **SoC** | ESP32-S3 (Xtensa LX7 dual-core, 240MHz) |
| **Flash** | 16MB (Quad SPI, integrated in module) |
| **PSRAM** | 8MB (Octal SPI, integrated in module) |
| **WiFi** | 802.11 b/g/n, 2.4GHz |
| **Bluetooth** | BLE 5.0 + Bluetooth Mesh |
| **USB** | Native USB-OTG (no external PHY needed) |
| **GPIO** | 36 programmable GPIOs |
| **ADC** | 2x 12-bit SAR ADC, up to 20 channels |
| **SPI** | 4x SPI interfaces |
| **I2C** | 2x I2C interfaces |
| **UART** | 3x UART interfaces |
| **Operating voltage** | 3.0V – 3.6V |
| **Operating temp** | -40°C to +85°C |
| **LCSC** | C2913196 (base WROOM-1), check N16R8 variant |
| **Price** | ~$2.80 (module) |

### Why N16R8?

The N16R8 is the highest-spec WROOM-1 variant:
- **16MB flash** — enough for OTA updates (dual partition), SPIFFS filesystem, and large firmware
- **8MB PSRAM** — allows framebuffers, image processing, and complex data structures without stack overflow
- Same footprint and pinout as all other WROOM-1 variants (N4, N8, N8R2, etc.)

---

## 2. Physical Dimensions & Pin Layout

### Module Body

| Dimension | Value |
|-----------|-------|
| Length | 25.5mm |
| Width | 18.0mm |
| Height | 3.2mm |
| Weight | ~3.2g |

### Pin Layout

The module has **41 pads** on three sides (castellated edges):
- **Left side** (14 pins): Pins 1-14, pitch 1.27mm
- **Bottom** (12 pins): Pins 15-26, pitch 1.27mm
- **Right side** (14 pins): Pins 27-40, pitch 1.27mm
- **Ground pad** (1 pad): Pin 41 — large exposed copper pad on the bottom center

### KiCad Footprint

The KiCad library footprint `RF_Module:ESP32-S3-WROOM-1` has a **48.0 x 43.2mm** bounding box (including courtyard and antenna keep-out). The actual module body is only 25.5 x 18mm — the difference is the antenna keep-out zone.

Pin positions relative to module center:
- Left pins: x = -8.75mm
- Right pins: x = +8.75mm
- Bottom pins: y = +12.50mm
- Top: antenna area (no pins)

---

## 3. Antenna Keep-Out Zone

This is the **most critical constraint** for PCB layout.

The ESP32-S3-WROOM-1 has an onboard PCB meander antenna at the **top edge** of the module. Espressif mandates strict keep-out rules:

### Rules

1. **No copper on any layer** within the antenna keep-out zone
2. **No components** within the keep-out zone
3. **No ground plane** under the antenna on any layer (including inner layers of 4-layer boards)
4. The module should be placed at or **overhanging the board edge** for best RF performance
5. Keep-out extends **15mm beyond the antenna end** of the module and **5mm to each side**

### Keep-Out Polygon (relative to module center)

```
Module top edge is at y = -12.75mm from center
Antenna area: x = -9mm to +9mm, y = -12.75mm to -25mm (extends 12mm past module)
Side clearance: x = -14mm to +14mm for the antenna zone
```

### Board Layout Implication

If the module is placed at the top of the board with antenna pointing up:
- The antenna area extends ~12-15mm past the top of the module body
- The board edge should be flush with or slightly past the antenna tip
- **No components or copper fill within 15mm of the board top edge** on any layer

### Recommended Placement

Place the ESP32-S3 module with:
- Antenna at the **top edge** of the board (or extending past the edge)
- Module center ~13mm from the top board edge
- Leave the area above and around the antenna completely clear

---

## 4. Ground Pad & Thermal Design

The exposed ground pad (pin 41) on the bottom of the module serves two purposes:
1. **RF ground reference** for the antenna — critical for WiFi/BLE performance
2. **Thermal heatsink** — the SoC dissipates heat through this pad

### Requirements

- Connect to the ground plane with **9 vias minimum** in a 3x3 grid under the pad
- Via diameter: 0.3mm drill, 0.6mm pad
- Via pitch: ~1.2mm spacing
- Use thermal relief on the pad connection for easier soldering (required for reflow)
- The ground pad is approximately **6.7 x 6.7mm**

### Routing Impact

The ground pad + via array creates a **routing blockage** under the center of the module. On a 2-layer board, this effectively prevents any traces from passing under the module. This is the primary reason the Dilder board moved to **4-layer design** — inner layers (In1.Cu, In2.Cu) can route signals around or through gaps in the via array.

---

## 5. Power Supply Design

### Power Input

| Parameter | Value |
|-----------|-------|
| VDD range | 3.0V – 3.6V (nominal 3.3V) |
| Peak current (WiFi TX) | ~500mA |
| Average current (WiFi active) | ~120mA |
| Light sleep | ~240µA |
| Deep sleep | ~10µA |
| Boot surge | up to 600mA for ~10ms |

### Dilder Power Chain

```
USB-C (5V) → SS34 Schottky → TP4056 (1A LiPo charger) → DW01A + FS8205A (protection)
                                                             ↓
                                                        LiPo Battery (3.7V)
                                                             ↓
                                                      AMS1117-3.3 (LDO) → 3.3V rail → ESP32-S3
```

### Decoupling

- **10µF + 100nF** capacitors within 3mm of the 3V3 pin (pin 2)
- **10µF** on LDO input and output
- Place caps on the **same side** of the board as the module

### EN (Chip Enable) Pin

- Pin 3 (EN/CHIP_PU)
- Requires **10kΩ pull-up to 3.3V**
- Optional: 0.1µF cap to GND for power-on delay (prevents brownout during boot)
- The module has an internal pull-up, but an external one is recommended for reliability

---

## 6. USB-C Integration (Native USB-OTG)

The ESP32-S3 has a built-in USB-OTG peripheral — no external USB PHY or series resistors needed.

| Pin | GPIO | Function |
|-----|------|----------|
| 13 | GPIO19 | USB_D- |
| 14 | GPIO20 | USB_D+ |

### USB-C Connector Wiring

- **VBUS** (5V) → Schottky diode → charging circuit
- **D+/D-** → directly to ESP32-S3 GPIO19/GPIO20 (no series resistors needed)
- **CC1/CC2** → 5.1kΩ pull-down to GND each (identifies as UFP/device)
- **GND** → board ground
- **Shield** → GND

### Trace Requirements

- USB D+/D- should be routed as a **90Ω differential pair**
- Keep traces short (< 50mm)
- On a 4-layer board with standard JLCPCB stackup: ~0.2mm trace width, ~0.15mm gap for 90Ω differential

---

## 7. GPIO Assignment for Dilder

### Pin Mapping (ESP32-S3-WROOM-1 pad numbers)

| Pad # | GPIO | Function | Side |
|-------|------|----------|------|
| 1 | GND | Ground | LEFT |
| 2 | 3V3 | Power | LEFT |
| 3 | EN | Enable (10k pull-up) | LEFT |
| 4 | GPIO4 | Joystick UP | LEFT |
| 5 | GPIO5 | Joystick DOWN | LEFT |
| 6 | GPIO6 | Joystick LEFT | LEFT |
| 7 | GPIO7 | Joystick RIGHT | LEFT |
| 8 | GPIO15 | Joystick CENTER | LEFT |
| 9 | GPIO16 | MPU-6050 SDA (I2C) | LEFT |
| 10 | GPIO17 | MPU-6050 SCL (I2C) | LEFT |
| 13 | GPIO19 | USB D- | LEFT |
| 14 | GPIO20 | USB D+ | LEFT |
| 15 | GPIO3 | e-Paper CLK (SPI) | BOTTOM |
| 16 | GPIO46 | e-Paper MOSI (SPI) | BOTTOM |
| 17 | GPIO9 | e-Paper DC | BOTTOM |
| 18 | GPIO10 | e-Paper RST | BOTTOM |
| 19 | GPIO11 | e-Paper CS | BOTTOM |
| 20 | GPIO12 | e-Paper BUSY | BOTTOM |
| 41 | GND | Exposed ground pad | CENTER |

### Routing Implications

- **LEFT side pins** → route to components on the LEFT and BELOW the module
- **BOTTOM pins** → route straight down to the FPC connector below the module
- **RIGHT side pins** → currently unused (available for future expansion: GPS, audio, etc.)
- Joystick and USB-C at BOTTOM of board → traces from LEFT pins run DOWN along the left edge
- IMU (I2C) → place on LEFT side near pins 9-10

---

## 8. e-Paper Display Connection

### Waveshare 2.13" e-Paper HAT V4

The Waveshare display HAT has **two connectors**:

1. **24-pin FPC (0.5mm pitch)** — connects the raw e-paper glass panel to the SSD1680 driver on the HAT PCB. This is internal to the display module.
2. **8-pin header (2.54mm pitch)** — connects the HAT to the host MCU via SPI. This is what our PCB connects to.

We do **NOT** need the 24-pin FPC connector on our board. The Waveshare HAT already implements the SSD1680 driver circuit. Our PCB just needs an **8-pin 2.54mm header** that the HAT's ribbon cable plugs into.

| Parameter | Value |
|-----------|-------|
| Connection to our PCB | 8-pin 2.54mm header |
| Cable from HAT | 8-wire ribbon cable with DuPont ends |
| Display driver | SSD1680 (on the HAT, not our board) |
| Resolution | 250 × 122 pixels |
| Interface | SPI (4-wire, Mode 0) |

### 8-Pin Header Assignment

| Pin | Signal | ESP32 GPIO |
|-----|--------|------------|
| 1 | VCC (3.3V) | — (power rail) |
| 2 | GND | — (ground) |
| 3 | DIN (MOSI) | GPIO46 (pad 16) |
| 4 | CLK (SCLK) | GPIO3 (pad 15) |
| 5 | CS | GPIO11 (pad 19) |
| 6 | DC | GPIO9 (pad 17) |
| 7 | RST | GPIO10 (pad 18) |
| 8 | BUSY | GPIO12 (pad 20) |

### PCB Connector Options

**Option A — Vertical pin header** (simplest, tallest):
- Footprint: `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical`
- Dimensions: 2.5mm x 20.3mm
- Pro: cheapest, simplest soldering
- Con: adds 11mm height

**Option B — Right-angle pin header** (low profile):
- Footprint: `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Horizontal`
- Dimensions: 8.5mm x 20.3mm (extends horizontally)
- Pro: low profile, cable exits to the side
- Con: wider footprint

**Option C — JST-SH 8-pin** (compact, locking):
- Footprint: `Connector_JST:JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal`
- Dimensions: ~9mm x 4mm
- Pro: smallest, locked connection
- Con: requires custom cable with JST-SH connectors

For the Dilder prototype, **Option A (vertical header)** matches the existing Waveshare cable.

---

## 9. Component Placement Strategy

### Critical Rules

1. **ESP32 at top edge** — antenna overhangs or touches the board edge
2. **No copper in antenna zone** — 15mm clear zone above module on ALL layers
3. **FPC connector directly below module** — shortest path from BOTTOM pins to connector
4. **IMU on LEFT** — near I2C pins (9-10) for short traces
5. **Power section BELOW FPC** — middle of board, away from RF
6. **USB-C and joystick at BOTTOM** — user-facing, accessible in enclosure
7. **Decoupling caps within 3mm** of every IC power pin
8. **Battery connector on board edge** — accessible for connection

### Recommended Board Layout

```
┌──────────────────────────────────────────────┐
│          [ANTENNA KEEP-OUT - NO COPPER]       │ ← top edge
│                                              │
│  [C3][C4]  ┌──────────────────┐              │
│  [R10]     │  ESP32-S3-WROOM  │              │
│            │     (U1)         │              │
│  [U6 IMU]  │                  │    [C7][C9]  │
│  [R4][R5]  └──────────────────┘              │
│                                              │
│  ┌────── 24-pin FPC (J3) ──────┐             │
│  └─────────────────────────────┘             │
│                                              │
│  [C5]  [U4 LDO]  [C6]    [D2][R2]  [J2 BAT] │
│        [U2 TP4056]        [D3][R3]           │
│  [D1]  [R1]                                  │
│  [U3 DW01A]          [Q1 FS8205A]            │
│                                              │
│  [R8][R9]                                    │
│           [SW1 Joystick]                     │
│           [J1 USB-C]                         │
│                    DILDER v0.6               │
└──────────────────────────────────────────────┘
```

### Board Dimensions

With an 8-pin header instead of a 24-pin FPC, the board can be significantly narrower:

| Parameter | Value | Notes |
|-----------|-------|-------|
| Width | 28-32mm | Module(18mm) + 5-7mm routing channels each side |
| Height | 70-80mm | Antenna(15mm) + module(25mm) + peripherals(15mm) + power(15mm) + joystick+USB(10mm) |
| Layers | 4 | F.Cu, In1.Cu (signal), In2.Cu (power), B.Cu (GND plane) |
| Thickness | 1.6mm | Standard |

The 28mm width is achievable because:
- Module is 18mm wide
- 8-pin header is only 2.5mm wide (vs 44mm for the 24-pin FPC)
- 5mm routing channels on each side of the module
- Reference: Espressif's DevKitC is 25.4mm wide with WROOM-1

A 30mm x 75mm board at 4 layers would be the target — close to Pico size (21x51mm) but tall enough for all components.

---

## 10. Open-Source Reference Designs

### 10.1 atomic14 Basic ESP32-S3 Dev Board

- **URL**: https://github.com/atomic14/basic-esp32s3-dev-board
- **Board**: Small breakout form factor
- **Layers**: 2
- **Module**: ESP32-S3-WROOM-1 (same as ours)
- **Key insight**: Bare-minimum design — native USB D+/D- direct to USB-C (no resistors), 5.1k CC pull-downs, BOOT switch, EN RC reset, LD117 LDO. Clean USB differential pair routing.
- **KiCad files**: Yes, full KiCad project
- **Relevance**: Best minimal WROOM-1 reference — shows exactly what you need and nothing more

### 10.2 Olimex ESP32-S3-DevKit-LiPo

- **URL**: https://github.com/OLIMEX/ESP32-S3-DevKit-LiPo
- **Board**: Dev board with dimensions PDF in repo
- **Layers**: 4 (professional quality)
- **Module**: ESP32-S3-WROOM-1
- **Key insight**: USB-C with JTAG/debug, LiPo charger with auto power supply switching, ~200µA deep sleep
- **KiCad files**: Yes, full KiCad project (CERN OHL v2 license)
- **Relevance**: **Best reference for battery-powered ESP32-S3 with KiCad** — matches our use case exactly

### 10.3 Unexpected Maker TinyS3 / NanoS3

- **URL**: https://github.com/UnexpectedMaker/esp32s3
- **Board sizes**:
  - NanoS3: **28 x 11mm** (possibly smallest ESP32-S3 board available)
  - TinyS3: **35 x 17.8mm**
  - FeatherS3: **52.3 x 22.9mm**
- **Layers**: 4
- **Module**: ESP32-S3 bare chip (not WROOM module)
- **Key insight**: Uses bare chip for tiny form factor. Onboard 3D antenna + u.FL connector. Shows how small you can go with 4 layers.
- **KiCad files**: Schematics (PDF) + symbol/footprint files

### 10.4 ESP32-S3-DevKitC-1 (Espressif official)

- **URL**: https://github.com/espressif/esp-dev-kits
- **Board**: 69 x 25.4mm
- **Layers**: 2 (!)
- **Module**: ESP32-S3-WROOM-1
- **Key insight**: Even Espressif uses a 69mm long board to route a WROOM-1 on 2 layers
- **Relevance**: Confirms that 2-layer with WROOM-1 requires a long narrow board

### 10.5 Espressif Official KiCad Libraries

- **URL**: https://github.com/espressif/kicad-libraries
- Official symbols, footprints, and 3D models for all ESP32 modules
- **Use these for accurate WROOM-1 footprint** (may differ from KiCad's built-in version)

### Common Patterns Across Reference Designs

1. **All use module at board edge** with antenna overhanging or flush
2. **4-layer is standard** for WROOM-1 designs (Espressif's own DevKitC is the only 2-layer exception, at 69mm length)
3. **USB-C at opposite end** from antenna
4. **Battery connector on the side edge** (not top or bottom)
5. **Decoupling caps immediately adjacent** to module power pins (within 3mm)
6. **Ground plane on B.Cu** is universal — provides RF ground reference
7. **Native USB** — no series resistors needed (ESP32-S3 handles USB internally)
8. **EN pin**: 10k pull-up + optional 0.1µF cap to GND for reliable boot

---

## 11. 4-Layer Stackup & Routing

### JLCPCB Standard 4-Layer Stackup

| Layer | Name | Function | Thickness |
|-------|------|----------|-----------|
| 1 | F.Cu | Component pads + short signal traces | 0.035mm (1oz) |
| | Prepreg | FR-4 dielectric | 0.2104mm |
| 2 | In1.Cu | Signal routing (crosses under module) | 0.0152mm |
| | Core | FR-4 dielectric | 1.065mm |
| 3 | In2.Cu | 3V3 power plane (or more signal routing) | 0.0152mm |
| | Prepreg | FR-4 dielectric | 0.2104mm |
| 4 | B.Cu | GND plane (continuous) | 0.035mm (1oz) |
| **Total** | | | **1.6mm** |

### Routing Strategy

1. **F.Cu**: Component pads, short traces between nearby components, USB differential pair
2. **In1.Cu**: Long signal traces that need to cross under the ESP32 module — this is the key layer that makes 4-layer viable
3. **In2.Cu**: 3V3 power distribution (copper pour assigned to 3V3 net) — eliminates most power traces
4. **B.Cu**: GND plane (continuous copper pour) — provides return path for all signals

### Via Strategy

- **Signal vias**: 0.3mm drill, 0.6mm pad — from F.Cu to In1.Cu for routing under module
- **Power vias**: 0.3mm drill, 0.6mm pad — from F.Cu component pads to In2.Cu power plane
- **Ground vias**: 0.3mm drill, 0.6mm pad — from F.Cu GND pads to B.Cu ground plane
- **Via stitching**: Place ground vias every 5mm around the board perimeter and near the antenna

---

## 12. JLCPCB 4-Layer Manufacturing

### Pricing (as of 2026)

| Parameter | 2-Layer | 4-Layer |
|-----------|---------|---------|
| 5 boards (50x85mm) | ~$2 | ~$7-12 |
| SMT assembly | ~$8 setup | ~$8 setup |
| Total (5 boards + assembly) | ~$25 | ~$35 |

The 4-layer premium is **~$5-10 extra** — well worth it for the routing simplicity and signal integrity.

### Design Rules (4-Layer)

| Parameter | Value |
|-----------|-------|
| Min trace width | 0.09mm (3.5mil) |
| Min trace spacing | 0.09mm (3.5mil) |
| Min via drill | 0.2mm |
| Min via pad | 0.45mm |
| Min hole-to-hole | 0.254mm |
| Controlled impedance | Available (specify in order notes) |

---

## 13. Comparison: ESP32-S3 vs RP2040

| Feature | RP2040 | ESP32-S3-WROOM-1-N16R8 |
|---------|--------|------------------------|
| **WiFi** | No (needs CYW43439) | Yes (built in) |
| **BLE** | No | Yes (BLE 5.0) |
| **Flash** | External (2MB QSPI) | Internal (16MB) |
| **PSRAM** | None | 8MB |
| **USB** | USB 1.1 (needs resistors) | USB-OTG (native) |
| **CPU** | Dual Cortex-M0+ @ 133MHz | Dual Xtensa LX7 @ 240MHz |
| **RAM** | 264KB SRAM | 512KB SRAM + 8MB PSRAM |
| **Crystal** | External 12MHz required | Internal 40MHz (in module) |
| **Package** | QFN-56 (7x7mm) | Module (25.5x18mm) |
| **External parts needed** | Flash + crystal + caps + USB resistors | Decoupling caps only |
| **LCSC price** | $0.70 (chip only) | $2.80 (complete module) |
| **Total BOM for equivalent** | ~$2.00 (chip + flash + crystal + passives) | ~$2.80 (module only) |
| **PCB complexity** | High (QFN-56, 0.4mm pitch) | Low (1.27mm castellated pads) |
| **RF design needed** | Yes (if using CYW43439) | No (antenna in module) |

### Why We Switched

1. **WiFi + BLE built in** — no additional chips
2. **Fewer components** — module integrates flash, crystal, antenna (7 fewer parts)
3. **Easier soldering** — 1.27mm castellated pads vs 0.4mm QFN
4. **More capable** — 240MHz, 512KB RAM + 8MB PSRAM, native USB
5. **Pre-certified RF** — FCC/CE/IC certification included in the module

---

## 14. Resources & Datasheets

- [ESP32-S3-WROOM-1 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)
- [ESP32-S3 Hardware Design Guidelines](https://www.espressif.com/sites/default/files/documentation/esp32-s3_hardware_design_guidelines_en.pdf)
- [ESP32-S3 Technical Reference Manual](https://www.espressif.com/sites/default/files/documentation/esp32-s3_technical_reference_manual_en.pdf)
- [Waveshare 2.13" e-Paper HAT Wiki](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT)
- [Adafruit ESP32-S3 Feather PCB (KiCad)](https://github.com/adafruit/Adafruit-ESP32-S3-Feather-PCB)
- [Unexpected Maker TinyS3 (KiCad)](https://github.com/UnexpectedMaker/esp32s3)
- [JLCPCB 4-Layer Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities)
- [JLCPCB Parts: ESP32-S3-WROOM-1](https://jlcpcb.com/partdetail/EspressifSystems-ESP32S3/C2913192)
