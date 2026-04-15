# Dilder Custom PCB Design Plan

From breadboard prototype to a manufacturable PCB via JLCPCB. This document covers component selection, schematic design, board layout, and fabrication workflow.

---

## Phase Overview

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | KiCad setup + JLCPCB tools plugin | Done |
| 2 | Component selection + LCSC part sourcing | Done |
| 3 | Schematic capture in KiCad | In Progress |
| 4 | PCB board layout + DRC | Pending |
| 5 | Gerber export + BOM/CPL generation | Pending |
| 6 | Order from JLCPCB (PCB + SMT assembly) | Pending |

---

## Phase 1 — KiCad Environment Setup

### Prerequisites

- KiCad 10.0 installed (`/usr/bin/kicad`)
- Git installed
- Python 3 installed

### Step-by-step

```bash
# 1. Run the setup script (does everything below automatically)
cd hardware-design/
python3 setup-kicad-jlcpcb.py
```

The script performs these 5 steps:

1. **Install KiCad standard libraries** — `sudo pacman -S kicad-library kicad-library-3d`
   - Provides built-in symbols/footprints (QFN-56, SOT-223, SOIC-8, crystal, connectors)
   - Required for PCB layout — without these, footprints won't resolve
   - Prompts for sudo password

2. **Install kicad-jlcpcb-tools plugin** — cloned to `~/.local/share/kicad/10.0/scripting/plugins/`
   - [Bouni/kicad-jlcpcb-tools](https://github.com/Bouni/kicad-jlcpcb-tools)
   - Access in KiCad: **Tools > External Plugins > JLCPCB Tools**
   - Generates BOM + CPL files, assigns LCSC part numbers, queries JLCPCB parts database

3. **Install JLCPCB KiCad Library** — cloned to `~/.local/share/kicad/10.0/3rdparty/`
   - [CDFER/JLCPCB-Kicad-Library](https://github.com/CDFER/JLCPCB-Kicad-Library)
   - 20 symbol libraries (MCUs, power, connectors, passives, etc.)
   - Matched footprints and 3D STEP models

4. **Register libraries** — adds entries to `~/.config/kicad/10.0/sym-lib-table` and `fp-lib-table`
   - Libraries appear in KiCad's symbol/footprint browsers prefixed with `JLCPCB_`

5. **Initialize project** — creates `Board Design kicad/dilder.kicad_pro`, `.kicad_sch`, `.kicad_pcb`
   - 30x75mm board outline preset
   - JLCPCB design rules (0.127mm min trace, 0.3mm min drill, 0.6mm min via)
   - Power net class with wider traces (0.5mm) preconfigured

### Verify setup

```bash
# Open the project in KiCad
kicad 'Board Design kicad/dilder.kicad_pro'

# In KiCad, verify:
# - Schematic editor opens (Ctrl+E) — all 11 components visible
# - PCB editor opens (Ctrl+P) — 30x75mm board outline visible
# - Tools > External Plugins > JLCPCB Tools — plugin loads
# - Symbol browser shows JLCPCB_* libraries (20 entries)
```

### Re-running the script

The script is idempotent — safe to run again. It will:
- Pull latest changes for already-cloned repos
- Skip already-registered libraries
- Skip already-created project files

---

## Phase 2 — Component Selection (JLCPCB/LCSC Sourced)

All components selected for JLCPCB SMT assembly availability. LCSC part numbers verified.

### Core MCU

| Component | Part | LCSC # | Package | Price (ea.) | Notes |
|-----------|------|--------|---------|-------------|-------|
| MCU module | ESP32-S3-WROOM-1-N16R8 | C2913202 | Module 18x25.5mm | ~$2.80 | Dual-core Xtensa LX7 @ 240MHz, 512KB SRAM, 16MB flash, 8MB PSRAM, WiFi+BLE 5.0 built-in |
| USB connector | USB-C 16-pin | C2765186 | SMD | ~$0.10 | Programming + charging input |

> **Note:** The ESP32-S3-WROOM-1 module integrates flash, crystal, and RF frontend — no external W25Q16JV, 12MHz crystal, or crystal load caps needed.

### Power / Battery Charging

| Component | Part | LCSC # | Package | Price (ea.) | Notes |
|-----------|------|--------|---------|-------------|-------|
| LiPo charger IC | TP4056 | C382139 | ESOP-8 | ~$0.07 | 1A linear charger, 4.2V CC/CV, auto-recharge |
| Battery protection | DW01A + FS8205A | C351410 / C908265 | SOT-23 / SOT-23-6 | ~$0.05 | Over-discharge, over-charge, short-circuit protection |
| LDO 3.3V regulator | AMS1117-3.3 | C6186 | SOT-223 | ~$0.05 | 1A output, powers ESP32-S3 3.3V rail |
| Battery connector | JST PH 2.0mm 2-pin | C131337 | SMD | ~$0.03 | Standard LiPo battery connector |
| Schottky diode | SS34 | C8678 | SMA | ~$0.03 | USB/battery path selection |
| USB ESD protection | USBLC6-2SC6 | C7519 | SOT-23-6 | ~$0.08 | TVS diode array for USB data lines |

### Display Interface

| Component | Part | Notes |
|-----------|------|-------|
| e-Paper connector | 8-pin 2.54mm header | Connects to Waveshare Pico-ePaper-2.13 HAT via 8-pin header (VCC, GND, DIN, CLK, CS, DC, RST, BUSY) |
| SPI interface | GPIO3/46/9/10/11/12 | DC, CS, CLK, MOSI, RST, BUSY — see GPIO table below |

> The e-Paper display remains an off-board module connected via 8-pin 2.54mm header to the HAT board. The 24-pin FPC connects the raw e-Paper panel to the HAT — we connect to the HAT, not the panel directly. No display IC on the PCB.

### Input — 5-Way Navigation Switch

| Component | Part | LCSC # | Package | Price (ea.) | Notes |
|-----------|------|--------|---------|-------------|-------|
| 5-way joystick switch | SKRHABE010 (Alps Alpine) | C139794 | SMD 7.4x7.5x1.8mm | ~$0.38 | 4-direction + center push, replaces DollaTek module |

- Maps to GPIO4-GPIO8 (updated for ESP32-S3 pinout)
- Active LOW with internal pull-ups — no external resistors needed
- Rated 50mA @ 12V DC, 100k cycle life

### Sensors

| Component | Part | LCSC # | Package | Price (ea.) | Notes |
|-----------|------|--------|---------|-------------|-------|
| Accelerometer | LIS2DH12TR | C110926 | LGA-12 (2x2mm) | ~$0.46 | 3-axis accelerometer, I2C, built-in pedometer |

- LIS2DH12TR: I2C on GPIO16 (SDA) + GPIO17 (SCL)

> **GPS dropped:** The ATGM336H-5N31 has been removed. Location detection uses WiFi fingerprinting and BLE scanning (built into the ESP32-S3).

### Passive Components

| Component | Value | LCSC # | Package | Notes |
|-----------|-------|--------|---------|-------|
| Decoupling caps | 100nF | C14663 | 0402 | Per IC power pin |
| Bulk caps | 10uF | C19702 | 0402 | Power rail filtering |
| Charge current resistor | 1.2kΩ (RPROG) | C25752 | 0402 | Sets TP4056 to ~1A charge rate |
| Pull-up resistors | 10kΩ | C25744 | 0402 | I2C bus, reset lines |
| Status LEDs | Red + Green | C84256 / C72043 | 0402 | Charge status indicators |
| LED current limiting | 1kΩ | C25585 | 0402 | For status LEDs |

### Estimated BOM Cost (per board, qty 5)

| Category | Est. Cost |
|----------|-----------|
| ESP32-S3-WROOM-1-N16R8 | ~$2.80 |
| Power (TP4056, protection, LDO) | ~$0.28 |
| Input (joystick switch) | ~$0.38 |
| Sensors (LIS2DH12TR) | ~$0.46 |
| Connectors + passives | ~$0.80 |
| **Total per board** | **~$4.72** |
| PCB fabrication (5 boards) | ~$2.00 |
| SMT assembly (5 boards) | ~$8.00 setup + parts |
| Shipping to Germany | ~$15-25 (DHL) |

---

## Phase 3 — Schematic Design

### Block Diagram

```
                    ┌──────────────────────────────────────────────┐
                    │     ESP32-S3-WROOM-1-N16R8                   │
                    │     (WiFi + BLE 5.0 built-in)                │
                    │                                              │
  USB-C ──┬──────▶ │ USB D+/D- (GPIO19/20)                        │
           │        │                                              │
           │        │ SPI (GPIO3/46/9/10/11/12) ──▶ e-Paper Header │
           │        │                                              │
           │        │ GPIO4-8 ◀────────── 5-Way Joystick           │
           │        │                                              │
           │        │ I2C (GPIO16/17) ◀────── LIS2DH12TR           │
           │        │                                              │
           │        │ ADC ◀──── VSYS/3 (batt monitor)              │
           │        │                                              │
           │        └──────────────────────────────────────────────┘
           │
           ▼
  TP4056 ──▶ DW01A/FS8205A ──▶ JST Battery Connector
           │
           ▼
  AMS1117-3.3 ──▶ 3.3V rail ──▶ All ICs
```

### GPIO Pin Assignment (Final)

| GPIO | Function | Interface | Direction |
|------|----------|-----------|-----------|
| GPIO3 | e-Paper DC | Digital | Out |
| GPIO4 | Joystick UP | Digital | In (pull-up) |
| GPIO5 | Joystick DOWN | Digital | In (pull-up) |
| GPIO6 | Joystick LEFT | Digital | In (pull-up) |
| GPIO7 | Joystick RIGHT | Digital | In (pull-up) |
| GPIO8 | Joystick CENTER | Digital | In (pull-up) |
| GPIO9 | e-Paper CLK | SPI SCK | Out |
| GPIO10 | e-Paper MOSI | SPI MOSI | Out |
| GPIO11 | e-Paper RST | Digital | Out |
| GPIO12 | e-Paper BUSY | Digital | In |
| GPIO16 | LIS2DH12TR SDA | I2C SDA | Bidir |
| GPIO17 | LIS2DH12TR SCL | I2C SCL | Bidir |
| GPIO19 | USB D- | USB | Bidir |
| GPIO20 | USB D+ | USB | Bidir |
| GPIO46 | e-Paper CS | SPI CS | Out |

### Current Schematic State

Components for the updated schematic:

| Ref | Component | Lib Symbol | LCSC |
|-----|-----------|------------|------|
| U1 | ESP32-S3-WROOM-1-N16R8 | ESP32-S3-WROOM-1 (local) | C2913202 |
| U2 | TP4056 | TP4056 (local) | C382139 |
| U3 | DW01A | DW01A (local) | C351410 |
| U4 | AMS1117-3.3 | AMS1117-3.3 (local) | C6186 |
| U5 | LIS2DH12TR | LIS2DH12TR (local) | C110926 |
| Q1 | FS8205A | FS8205A (local) | C908265 |
| D1 | SS34 | D_Schottky (local) | C8678 |
| SW1 | SKRHABE010 | SKRHABE010 (local) | C139794 |
| J1 | USB-C | USB_C_16P (local) | C2765186 |
| J2 | JST-PH-2 | JST_PH_2 (local) | C131337 |
| J3 | e-Paper 8-pin | Pin_Header_1x08_P2.54mm (local) | — |

Plus passives: R1-R5 (resistors), C1-C7 (capacitors), D2-D3 (LEDs).

> Removed from RP2040 design: W25Q16JV (U5), ATGM336H (U7), 12MHz crystal (Y1), crystal load caps (C1/C2), USB series resistors (R6/R7) — all either integrated in the ESP32-S3 module or dropped for v1.

### Step-by-step: Wire the schematic in KiCad

```bash
# Open the project
kicad 'hardware-design/Board Design kicad/dilder.kicad_pro'
```

1. **Open the schematic editor** (double-click `dilder.kicad_sch` or Ctrl+E)

2. **Wire the power section** (top of schematic):
   - J1 VBUS → D1 anode (SS34 Schottky)
   - D1 cathode → U2 VCC (TP4056 input)
   - U2 BAT → U3 VCC (DW01A battery+)
   - U3 OD → Q1 G1, U3 OC → Q1 G2 (MOSFET gates)
   - Q1 S2 → J2 pin 1 (battery+), Q1 S1 → GND through U3
   - U2 BAT → U4 VIN (AMS1117 input) — this is the VBAT net
   - U4 VOUT → 3V3 rail
   - R1 (1.2k) between U2 PROG and GND — sets 1A charge rate
   - U2 TEMP → GND through 10k NTC or direct to GND (disable temp sense)
   - U2 CE → VCC (always enabled)
   - D2 (RED) + R2 (1k) from 3V3 to U2 CHRG pin — charging indicator
   - D3 (GREEN) + R3 (1k) from 3V3 to U2 STDBY pin — charge done indicator

3. **Wire the MCU section** (center):
   - U4 VOUT (3V3) → U1 3V3 pin
   - U1 GND → ground plane
   - U1 EN → R4 (10k) → 3V3 (pull-up to keep chip running)
   - C3 (100nF) + C4 (10uF) between 3V3 and GND near U1

   > No external flash, crystal, or crystal caps needed — all integrated in the ESP32-S3-WROOM-1 module.

4. **Wire USB** (left of MCU):
   - J1 D+ → U1 GPIO20 (USB_D+) — direct connection, no series resistors needed
   - J1 D- → U1 GPIO19 (USB_D-)
   - J1 CC1 → R8 (5.1k) → GND (UFP identification)
   - J1 CC2 → R9 (5.1k) → GND
   - J1 GND → GND, J1 SHIELD → GND

5. **Wire the joystick** (left side):
   - SW1 UP → U1 GPIO4 (label: JOY_UP)
   - SW1 DOWN → U1 GPIO5 (label: JOY_DOWN)
   - SW1 LEFT → U1 GPIO6 (label: JOY_LEFT)
   - SW1 RIGHT → U1 GPIO7 (label: JOY_RIGHT)
   - SW1 CENTER → U1 GPIO8 (label: JOY_CENTER)
   - SW1 COM → GND

6. **Wire the e-Paper header** (right side):
   - J3 DIN → U1 GPIO10 (SPI MOSI)
   - J3 CLK → U1 GPIO9 (SPI SCK)
   - J3 CS → U1 GPIO46 (SPI CS)
   - J3 DC → U1 GPIO3
   - J3 RST → U1 GPIO11
   - J3 BUSY → U1 GPIO12
   - J3 VCC → 3V3, J3 GND → GND

7. **Wire the LIS2DH12TR** (right side):
   - U5 SDA → U1 GPIO16 (I2C SDA)
   - U5 SCL → U1 GPIO17 (I2C SCL)
   - R4 (10k) from SDA to 3V3, R5 (10k) from SCL to 3V3 — I2C pull-ups
   - U5 VDD_I/O → 3V3, U5 VDD → 3V3
   - U5 GND → GND, U5 SDO/SA0 → GND (I2C address 0x18)
   - C6 (100nF) from VDD to GND, C7 (100nF) from VDD_I/O to GND
   - U5 INT1 → leave unconnected (or route to spare GPIO for interrupt-driven reads)

8. **Add power symbols** — place VCC/GND power flags on the power nets

9. **Run ERC** (Inspect > Electrical Rules Checker) — fix any errors

### Schematic Sheets (optional split)

For a cleaner layout, consider splitting into sub-sheets:

1. **MCU** — ESP32-S3-WROOM-1, decoupling, USB
2. **Power** — USB-C input, TP4056, battery protection, LDO, power path
3. **Input/Output** — 5-way joystick, e-Paper header, status LEDs
4. **Sensors** — LIS2DH12TR (I2C)

---

## Phase 4 — PCB Board Layout

### Board Constraints

| Parameter | Value |
|-----------|-------|
| Target size | 30 x 75mm |
| Layers | 4-layer (inner layers for GND and power planes) |
| Copper weight | 1oz |
| Min trace width | 0.15mm (6mil) |
| Min via | 0.3mm drill / 0.6mm pad |
| Surface finish | HASL (lead-free) |
| Impedance control | Not required (no high-speed signals) |

### Step-by-step: Board layout in KiCad

1. **Generate netlist from schematic**
   - In schematic editor: Tools > Update PCB from Schematic (F8)
   - All components appear as a "rat's nest" with airwires

2. **Set design rules** (already configured in .kicad_pro)
   - File > Board Setup > Design Rules > Constraints
   - Verify: min clearance 0.2mm, min track 0.127mm, min via 0.6mm/0.3mm
   - Net class "Power" uses 0.5mm traces (VBAT, 3V3, GND)

3. **Place components** — follow this layout strategy:

   ```
   ┌────────────────────────┐
   │ [J3 e-Paper header]    │  ← top edge (8-pin 2.54mm)
   │                        │
   │ [U1 ESP32-S3-WROOM-1]  │  ← module (18x25.5mm), keep
   │                        │    antenna area clear at top
   │                        │
   │ [U5 LIS2DH12TR]        │
   │                        │
   │ [SW1 Joystick]         │
   │                        │
   │ [U4 LDO] [U2 TP4056]  │
   │ [U3][Q1]               │
   │                        │
   │ [J1 USB-C] [J2 Batt]  │  ← bottom edge
   └────────────────────────┘
        30mm x 75mm
   ```

   - U1 (ESP32-S3) upper area — keep antenna end at board edge, no copper/ground pour under antenna
   - J3 (e-Paper header) top edge — 8-pin 2.54mm header
   - J1 (USB-C) bottom edge — accessible for programming/charging
   - J2 (battery) bottom edge — accessible for battery swap
   - SW1 (joystick) center — thumb-accessible in enclosure
   - Power ICs (U2, U3, Q1, U4) grouped near bottom

4. **Route critical traces first**:
   - USB D+/D- (keep short, matched length, ~0.25mm traces)
   - Power traces (0.5mm width for VBAT, 3V3, GND)

5. **Route remaining signals**:
   - SPI to e-Paper header (GPIO3/46/9/10/11/12)
   - I2C to LIS2DH12TR (GPIO16/17)
   - Joystick GPIO4-8

6. **Add copper pours**:
   - F.Cu: GND pour (entire board)
   - In1.Cu: GND plane (continuous)
   - In2.Cu: 3V3 power plane
   - B.Cu: GND pour (entire board)
   - Leave clearance under ESP32-S3 antenna area (no copper/ground pour under antenna overhang)

7. **Add mounting holes** (optional):
   - 4x M2 mounting holes at corners (2.2mm drill)
   - Match enclosure mounting points

8. **Run DRC** (Inspect > Design Rules Checker):
   - Fix any clearance violations
   - Fix any unconnected nets
   - Verify all JLCPCB manufacturing constraints pass

9. **3D view** (Alt+3): Visual check — verify component heights don't conflict

### Design Rules (JLCPCB Capability)

- Minimum trace/space: 0.127mm / 0.127mm (5mil/5mil)
- Minimum drill: 0.2mm
- Board thickness: 1.6mm standard
- Solder mask: green (cheapest)
- Silkscreen: white

---

## Phase 5 — Fabrication Output

### Step-by-step: Generate files and order

1. **Assign LCSC part numbers** (if not already done):
   - Open PCB editor
   - Tools > External Plugins > JLCPCB Tools
   - Click each component → assign LCSC number from the plan above
   - The plugin queries JLCPCB's live inventory to verify stock

2. **Generate BOM + CPL**:
   - In JLCPCB Tools plugin: click "Generate BOM/CPL"
   - Creates two CSV files in `gerber/` directory
   - BOM: component values, LCSC part numbers, quantities
   - CPL: X/Y coordinates and rotation for pick-and-place

3. **Export Gerber files**:
   - File > Plot (or use JLCPCB Tools "Generate Gerber")
   - Output directory: `gerber/`
   - Select layers: F.Cu, In1.Cu, In2.Cu, B.Cu, F.SilkS, B.SilkS, F.Mask, B.Mask, Edge.Cuts
   - Generate drill files: PTH and NPTH

4. **Upload to JLCPCB**:
   - Go to https://jlcpcb.com/
   - Click "Order Now" → upload the Gerber ZIP
   - Review PCB preview — verify board outline, drill holes, silkscreen
   - Enable "SMT Assembly" → upload BOM and CPL CSVs
   - Select "Top Side" assembly
   - Review component placements — check rotation of ICs
   - Confirm parts are in stock (the plugin pre-verified this)

5. **JLCPCB order settings**:
   - PCB Qty: 5 (minimum order)
   - Layers: 4
   - Thickness: 1.6mm
   - Color: green
   - Surface finish: HASL lead-free
   - SMT Assembly: yes (top side only)
   - Tooling holes: added by JLCPCB
   - Confirm delivery: mark

6. **Shipping to Germany**:
   - DHL Express: 5-8 days, ~$15-25
   - Expect 19% VAT + ~6 EUR DHL customs handling fee on import
   - Total estimated order: ~$35-50 for 5 assembled boards

---

## Key Design Decisions

### Why ESP32-S3-WROOM-1-N16R8 instead of bare RP2040?

- **Integrated module** — flash (16MB), PSRAM (8MB), crystal, and RF frontend all built in. Eliminates W25Q16JV, 12MHz crystal, crystal load caps, and USB series resistors from the BOM.
- **WiFi + BLE 5.0 built-in** — enables OTA firmware updates, wireless data sync, and WiFi-based location. No separate wireless module needed.
- **More capable CPU** — dual-core Xtensa LX7 @ 240MHz with 512KB SRAM vs dual-core Cortex-M0+ @ 133MHz with 264KB SRAM. More headroom for future features.
- **Native USB** — USB-OTG on GPIO19/20, no series resistors required.
- **Simpler PCB** — fewer external components means fewer traces, fewer potential failure points, and faster assembly.
- **Cost trade-off** — module costs ~$2.80 vs ~$1.15 for RP2040+flash+crystal, but the ~$1.65 increase buys WiFi/BLE, 8x more flash, PSRAM, and a simpler layout. Total BOM cost stays similar after removing eliminated parts.
- **JLCPCB available** — in stock on LCSC for SMT assembly.

### Why TP4056 instead of Adafruit PowerBoost?

- Available as JLCPCB basic part — can be SMT assembled
- $0.07 vs $16.00 per unit
- 1A charge rate is sufficient for 1000mAh battery
- Combined with DW01A provides complete charging + protection
- No boost converter needed (VSYS accepts 3.7V directly)

### Why no GPS?

- ATGM336H-5N31 dropped entirely
- Location detection uses WiFi fingerprinting and BLE scanning (built into the ESP32-S3)
- No additional hardware needed for location awareness

---

## Reference Documents

- [Breadboard Wiring Guide](../docs/breadboard-wiring-guide.md) — current prototype pin assignments
- [Battery Wiring Guide](../website/docs/docs/hardware/battery-wiring.md) — LiPo integration details
- [Hardware Research](../docs/hardware-research.md) — component evaluation
- [ESP32-S3 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf) — SoC pinout, electrical characteristics
- [ESP32-S3-WROOM-1 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) — module dimensions, pin definitions, antenna keepout
- [ESP32-S3 Hardware Design Guidelines](https://www.espressif.com/sites/default/files/documentation/esp32-s3_hardware_design_guidelines_en.pdf) — reference schematic, layout recommendations
- [JLCPCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) — manufacturing limits
