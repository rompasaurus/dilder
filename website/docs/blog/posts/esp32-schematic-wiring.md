---
date: 2026-04-15
authors:
  - rompasaurus
categories:
  - Hardware
  - PCB Design
slug: esp32-schematic-complete
---

# The ESP32-S3 Schematic is Fully Wired

Today the Dilder schematic got its biggest overhaul yet. The RP2040 is officially gone, replaced by the ESP32-S3-WROOM-1-N16R8 module with every net wired and validated.

<!-- more -->

## What Changed

The old schematic had 33 components with a bare RP2040 chip that needed external flash, a crystal, crystal load caps, USB series resistors, and QSPI wiring. The ESP32-S3 module integrates all of that — flash, PSRAM, crystal, and RF frontend are all inside the metal can.

**Removed:** RP2040, W25Q16JV flash, 12MHz crystal, 2x 15pF caps, 2x 27R USB resistors, ATGM336H GPS module

**Added:** ESP32-S3-WROOM-1-N16R8 (one module replaces six components)

Component count dropped from 33 to 20. Simpler BOM, easier assembly, fewer things to go wrong.

## The Wiring

Every net is connected via labeled wire stubs in the KiCad schematic:

- **Power:** USB-C VBUS through SS34 Schottky to TP4056 charger, battery protection (DW01A + FS8205A), through AMS1117-3.3 LDO to the 3.3V rail that feeds everything
- **E-Paper SPI:** GPIO9 (CLK), GPIO10 (MOSI), GPIO3 (DC), GPIO11 (RST), GPIO46 (CS), GPIO12 (BUSY) to the 8-pin JST-SH connector
- **Accelerometer I2C:** GPIO16 (SDA), GPIO17 (SCL) to LIS2DH12TR with 10k pull-ups
- **Joystick:** GPIO4-8 for UP/DOWN/LEFT/RIGHT/CENTER, active LOW with internal pull-ups
- **USB:** GPIO19 (D-) and GPIO20 (D+) wired directly to USB-C — no series resistors needed thanks to native USB-OTG
- **EN:** 10k pull-up to keep the module running

## The BOM

A full bill of materials is now tracked in `hardware-design/BOM.md` with LCSC part numbers for every component. Total cost per board: ~$4.18. The most expensive part is the ESP32-S3 module ($2.80) — the LIS2DH12TR accelerometer is just $0.46, and everything else is pennies.

## 11 Reference Designs

To sanity-check the design, I also collected 11 open-source ESP32 KiCad projects that share features with the Dilder. The most useful are:

- **PocketMage PDA** — an ESP32-S3 e-ink handheld with 1800 GitHub stars
- **Lilka** — a Ukrainian ESP32-S3 gaming console with D-pad buttons
- **Ducky Board** — the simplest possible ESP32-S3 + e-paper + battery board
- **BitwiseAjeet** — uses the exact same TP4056 charger IC

All 11 are in `hardware-design/examples/` with detailed ABOUT.md files describing their origin, what's relevant to Dilder, and which KiCad files to look at.

## Next Steps

The schematic is done. The PCB placement script (`build_esp32s3.py`) already has the ESP32-S3 components positioned on a 45x80mm 4-layer board. Next up: routing the traces, running DRC, and generating Gerber files for JLCPCB.
