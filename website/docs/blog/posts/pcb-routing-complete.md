---
date: 2026-04-15
authors:
  - rompasaurus
categories:
  - Hardware
  - PCB Design
slug: pcb-routing-complete
---

# PCB v0.4 — Board Routed, Gerbers Next

The Dilder PCB design hit a milestone: v0.4 is fully placed and routed. 30 components on a 30x70mm 4-layer board, 34 nets, 125 pad connections. The board is ready for design rule checks and Gerber export.

<!-- more -->

## From 45x80mm to 30x70mm

Between v0.3 and v0.4, the board shrank. The original 45x80mm layout had generous spacing between component zones but wasted board area. By tightening placement — especially in the power section where the TP4056, DW01A, and FS8205A share a compact cluster — we got down to **30x70mm** without sacrificing routability.

That's roughly the size of a credit card plus a centimeter. Small enough to fit inside the 3D-printed enclosure alongside the battery and display.

## The Layer Stack

Four layers, each with a clear job:

| Layer | Purpose |
|-------|---------|
| **F.Cu** | Component pads, short signal stubs, GND pour |
| **In1.Cu** | Continuous ground plane (RF reference + return paths) |
| **In2.Cu** | 3.3V power distribution plane |
| **B.Cu** | Long signal runs, additional GND pour |

The unbroken ground plane on In1.Cu is the backbone. It gives the ESP32-S3 antenna its RF ground reference, provides clean return paths for SPI and I2C signals, and keeps the power section quiet. Both ground pours and both planes start below y=5mm to respect the antenna keep-out zone.

## Six Zones, Top to Bottom

The board is organized into functional zones that follow signal flow:

**Zone A (Antenna)** — Empty. No copper on any layer. The ESP32-S3-WROOM-1 antenna overhangs the board edge here.

**Zone B (ESP32-S3)** — The module sits centered with decoupling caps on the left margin and charge/standby LEDs on the right.

**Zone C (Power)** — AMS1117-3.3 LDO, TP4056 charger, DW01A battery protection, FS8205A MOSFETs, and the JST-PH battery connector. USB-C power enters at the bottom and flows up through this section.

**Zone D (Peripherals)** — LIS2DH12TR accelerometer (I2C), 8-pin JST-SH ePaper connector (SPI), BOOT and RESET buttons.

**Zone E (Joystick)** — SKRHABE010 5-way joystick, centered for thumb access.

**Zone F (USB-C)** — HRO TYPE-C-31-M-12 connector with CC pull-down resistors.

## The BOM at $4.26

28 unique components, 30 placed (including duplicate passives). Total BOM cost at JLCPCB quantities: **~$4.26 per board**. The ESP32-S3 module at $2.80 is two-thirds of that. Everything else is under $0.50 each, most under $0.10.

For comparison, the breadboard prototype using off-the-shelf dev boards costs 40-85 EUR. The custom PCB brings that down to single digits — that's the whole point.

## Routing Strategy

The routing follows a zone-based approach:

- **Power traces** are wider (0.5mm+) for current carrying capacity
- **SPI signals** (ePaper) route on F.Cu with short stubs to the JST-SH connector
- **I2C signals** route to the LIS2DH12TR with matched-length traces and nearby pull-ups
- **USB D+/D-** are routed as a differential pair with controlled impedance
- **Joystick GPIO** lines are simple digital traces with internal pull-ups in the ESP32-S3

The routing scripts use KiCad's pcbnew Python API to set track widths, via sizes, and design rules programmatically. Every trace can be regenerated from code.

## What's Next

1. **DRC (Design Rule Check)** — run KiCad's checker against JLCPCB's manufacturing constraints
2. **Generate Gerbers** — export fabrication files in JLCPCB format
3. **Order prototypes** — 5 boards from JLCPCB, shipped to Germany
4. **Assemble and test** — hand-solder components, flash firmware, boot the octopus

The board design lives in `hardware-design/Board Design kicad/` with the full KiCad project, build scripts, and design documentation. From breadboard to a 30x70mm PCB that costs $4.26 in parts. The octopus is getting its proper home.
