# ESP32 KiCad Reference Designs

A collection of 11 open-source ESP32/ESP32-S3 KiCad projects for reference while designing the Dilder PCB. Each project is in its own folder with full KiCad source files and an ABOUT.md describing its relevance.

---

## Table of Contents

### Tier 1 — Highest Relevance (ESP32-S3 + e-ink/handheld)

| # | Project | MCU | Key Features | Why It Matters |
|---|---------|-----|-------------|---------------|
| [01](01-pocketmage-pda/ABOUT.md) | **PocketMage PDA** | ESP32-S3 | E-ink + OLED, keyboard, battery, USB-C | Closest overall match — ESP32-S3 e-ink handheld |
| [02](02-lilka-console/ABOUT.md) | **Lilka DIY Console** | ESP32-S3 | IPS display, D-pad, speaker, battery | Handheld gaming device, button wiring reference |
| [03](03-ducky-board-epaper/ABOUT.md) | **Ducky Board** | ESP32-S3 | 1.52" e-paper, Li-Ion charger, USB-C | Simplest ESP32-S3 + e-paper + battery reference |

### Tier 2 — High Relevance (TP4056 / power design)

| # | Project | MCU | Key Features | Why It Matters |
|---|---------|-----|-------------|---------------|
| [09](09-bitwiseajeet-tp4056/ABOUT.md) | **BitwiseAjeet TP4056** | ESP32-C3 | **TP4056**, USB-C, battery protection, sensors | Exact same charger IC as Dilder |
| [10](10-klp5e-sensor-board/ABOUT.md) | **KLP-5e Sensor Board** | ESP32-C3 | **TP4056**, hierarchical schematics, sensors | Educational quality, TP4056 reference |
| [04](04-olimex-s3-devkit-lipo/ABOUT.md) | **OLIMEX S3-DevKit-LiPo** | ESP32-S3 | LiPo charger, USB-OTG, JTAG, ESD protection | Professional-grade ESP32-S3 + LiPo reference |

### Tier 3 — Useful Reference (design patterns & evolution)

| # | Project | MCU | Key Features | Why It Matters |
|---|---------|-----|-------------|---------------|
| [05](05-olimex-devkit-lipo/ABOUT.md) | **OLIMEX DevKit-LiPo** | ESP32 | LiPo, **4 hardware revisions** (A1→D) | Study how a PCB design evolves through revisions |
| [06](06-unexpected-maker-s3/ABOUT.md) | **Unexpected Maker S3** | ESP32-S3 | Carrier boards, compact layouts, USB-C | Carrier board design patterns |
| [07](07-whirlingbits-s3-platform/ABOUT.md) | **WhirlingBits S3 Platform** | ESP32-S3 | SD card, e-paper schematic, hierarchical | E-paper schematic + hierarchical organization |
| [08](08-esp-rust-board/ABOUT.md) | **ESP Rust Board** | ESP32-C3 | Feather form, battery, USB-C | Professional schematic quality, Espressif-affiliated |
| [11](11-aeonlabs-s3-template/ABOUT.md) | **AeonLabs S3 Template** | ESP32-S3 | Minimal template, CC0 license | Baseline ESP32-S3 wiring, public domain |

---

## Feature Cross-Reference

Which example to look at for each Dilder feature:

| Dilder Feature | Best References |
|---------------|----------------|
| ESP32-S3 module wiring | 01, 03, 04, 06, 11 |
| E-ink / e-paper SPI | **01**, **03**, 07 |
| TP4056 battery charging | **09**, **10** |
| DW01A/FS8205A protection | 09, 10 |
| AMS1117-3.3 LDO | 04, 05, 08 |
| USB-C connector | 01, 03, 04, 06, 08 |
| Joystick / buttons | **02**, 09 |
| LIS2DH12TR / Accelerometer | 09 (sensors sheet) |
| Compact PCB layout | 03, 06, 08 |
| Hierarchical schematics | 07, 09, 10 |
| Design revision history | **05** (4 revisions!) |

---

## How to Use These Examples

1. **Open in KiCad** — Each folder contains a complete KiCad project. Open the `.kicad_pro` file (or `.sch` for older projects) in KiCad to browse schematics and PCB layouts.

2. **Compare circuits** — Open a reference schematic side-by-side with Dilder's `generate_schematic.py` or the generated `dilder.kicad_sch` to verify wiring.

3. **Copy footprints** — Some projects include custom footprints (especially 01-pocketmage and 07-whirlingbits) that may be useful.

4. **Study layout** — Open `.kicad_pcb` files to see how components are placed and routed on real boards that have been manufactured.

---

## Disk Space

These are shallow clones (`--depth 1`). To save space, you can delete the `.git` folder in any project you don't plan to update:
```bash
rm -rf 01-pocketmage-pda/.git  # saves ~80% of disk usage per repo
```

## Licenses

Each project has its own license. Check the ABOUT.md in each folder or the LICENSE file in the repo root. Licenses range from CC0 (public domain) to GPL-3.0. None of these restrict you from using them as design references for your own original work.
