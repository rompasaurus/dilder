# Dilder PCB Board Design v0.4

Complete design document for the Dilder custom PCB, covering placement, routing, layer stack, and fabrication readiness.

---

## Table of Contents

1. [Board Overview](#board-overview)
2. [Layer Stack](#layer-stack)
3. [Component Zones](#component-zones)
4. [GPIO Pin Assignments](#gpio-pin-assignments)
5. [Bill of Materials](#bill-of-materials)
6. [Placement Script](#placement-script)
7. [Routing Strategy](#routing-strategy)
8. [Routing Scripts](#routing-scripts)
9. [DRC Status](#drc-status)
10. [Design Rules](#design-rules)
11. [Antenna Keep-Out](#antenna-keep-out)
12. [Silkscreen](#silkscreen)
13. [Fabrication Workflow](#fabrication-workflow)
14. [Revision History](#revision-history)

---

## Board Overview

| Parameter | Value |
|-----------|-------|
| Board size | 30 x 70 mm |
| Layers | 4 (F.Cu, In1.Cu, In2.Cu, B.Cu) |
| Thickness | 1.6 mm |
| Components | 30 unique (34 placed incl. duplicates) |
| Nets | 34 |
| Pad connections | 125 |
| BOM cost | ~$5.20/board |
| Target fab | JLCPCB (SMT assembly) |

```
Board layout (30 x 70 mm, top view):
┌──────────────────────────────┐ y=0
│  ~~~ Antenna overhang ~~~    │ Zone A
│                              │
│    ┌──────────────────┐      │
│ C3 │                  │  D2  │
│ C4 │   ESP32-S3-WROOM │  R2  │ Zone B
│R10 │    -1-N16R8      │  D3  │
│R11 │                  │  R3  │
│    └──────────────────┘      │
│  C5  [U4 AMS1117]  C6       │
│  D1  [U2 TP4056 ]  R1       │ Zone C
│  [U3 DW01A] [Q1 FS8205A] J2 │
│                              │
│ U5   R4     [J3 ePaper]      │
│ R5   C7   [SW2 BOOT][SW3]C8 │ Zone D
│                              │
│       [SW1 5-Way Joystick]   │ Zone E
│                              │
│  R8  R9   [J1 USB-C]        │ Zone F
└──────────────────────────────┘ y=70
```

---

## Layer Stack

| Layer | Net | Purpose |
|-------|-----|---------|
| F.Cu | Signals + GND pour | Component pads, short stubs, local traces |
| In1.Cu | GND plane | Continuous ground reference plane |
| In2.Cu | 3V3 plane | 3.3V power distribution plane |
| B.Cu | Signals + GND pour | Long signal runs (B.Cu channels), return path |

Both GND pours (F.Cu, B.Cu) and both planes (In1.Cu, In2.Cu) start below y=5mm to preserve the antenna keep-out zone.

---

## Component Zones

The board is divided into 6 functional zones from top to bottom:

### Zone A — Antenna Overhang (y=0-3mm)

No copper on any layer. The ESP32-S3-WROOM-1 module antenna extends above the board edge into this region. Ground planes, signal traces, and zone pours all start at y=5mm.

### Zone B — ESP32 Module (y=3-25mm)

- **U1** ESP32-S3-WROOM-1-N16R8 centered at (15, 14.75)
- Module body: 18 x 25.5mm, occupies x=6-24
- Left margin (x=1-5): C3, C4 (decoupling), R10 (EN pull-up), R11 (BOOT pull-up)
- Right margin (x=25-29): D2/R2 (charge LED), D3/R3 (standby LED)

### Zone C — Power Section (y=26-42mm)

- **U4** AMS1117-3.3 LDO at (15, 29)
- **U2** TP4056 charger at (15, 35)
- **D1** SS34 Schottky at (5, 35)
- **U3** DW01A battery protection at (7, 41)
- **Q1** FS8205A dual MOSFET at (23, 41)
- **J2** JST-PH battery connector at (27, 41)
- C5, C6 bulk caps; R1 PROG resistor

### Zone D — Peripherals (y=42-54mm)

- **U5** LIS2DH12TR accelerometer at (6, 47), LGA-12 2x2mm
- **U6** AHT20 temp/humidity at (6, 52), DFN-6 3x3mm
- **U7** BH1750FVI light sensor at (13, 52), WSOF-6 3x1.6mm
- **J3** ePaper 8-pin JST-SH at (23, 47)
- R4, R5 I2C pull-ups; C7, C9, C10 sensor decoupling
- **SW2** BOOT button at (8, 52)
- **SW3** RESET button at (22, 52)
- C8 EN debounce cap at (26, 52)

### Zone E — Joystick (y=54-62mm)

- **SW1** SKRHABE010 5-way joystick at (15, 58)
- 6 pads: UP (12.75, 58), DOWN (17.25, 58), LEFT (14.55, 60), RIGHT (15.45, 60), CENTER (16.35, 60), GND

### Zone F — USB-C (y=62-70mm)

- **J1** HRO TYPE-C-31-M-12 USB-C at (15, 67)
- R8, R9 CC pull-down resistors (5.1k) at (7, 64/66)

---

## GPIO Pin Assignments

| GPIO | Function | Net Name | Interface | Direction |
|------|----------|----------|-----------|-----------|
| GPIO0 | Boot select | BOOT | Digital | In (pull-up R11) |
| GPIO3 | e-Paper DC | EPD_DC | SPI | Out |
| GPIO4 | Joystick UP | JOY_UP | Digital | In (internal pull-up) |
| GPIO5 | Joystick DOWN | JOY_DOWN | Digital | In (internal pull-up) |
| GPIO6 | Joystick LEFT | JOY_LEFT | Digital | In (internal pull-up) |
| GPIO7 | Joystick RIGHT | JOY_RIGHT | Digital | In (internal pull-up) |
| GPIO8 | Joystick CENTER | JOY_CENTER | Digital | In (internal pull-up) |
| GPIO9 | e-Paper CLK | EPD_CLK | SPI SCK | Out |
| GPIO10 | e-Paper MOSI | EPD_MOSI | SPI MOSI | Out |
| GPIO11 | e-Paper RST | EPD_RST | Digital | Out |
| GPIO12 | e-Paper BUSY | EPD_BUSY | Digital | In |
| GPIO16 | I2C SDA (accel, temp, light) | I2C_SDA | I2C | Bidir |
| GPIO17 | I2C SCL (accel, temp, light) | I2C_SCL | I2C | Bidir |
| GPIO18 | Accelerometer INT1 | ACCEL_INT1 | Digital | In |
| GPIO19 | USB D- | USB_DM | USB | Bidir |
| GPIO20 | USB D+ | USB_DP | USB | Bidir |
| GPIO46 | e-Paper CS | EPD_CS | SPI CS | Out |
| EN | Chip enable | EN | Control | In (pull-up R10) |

---

## Bill of Materials

| Ref | Component | Package | LCSC | Unit Cost |
|-----|-----------|---------|------|-----------|
| U1 | ESP32-S3-WROOM-1-N16R8 | Module 18x25.5mm | C2913196 | $2.80 |
| U2 | TP4056 (LiPo charger) | ESOP-8 | C382139 | $0.07 |
| U3 | DW01A (battery protection) | SOT-23-6 | C351410 | $0.05 |
| Q1 | FS8205A (dual MOSFET) | SOT-23-6 | C908265 | $0.05 |
| U4 | AMS1117-3.3 (LDO) | SOT-223-3 | C6186 | $0.05 |
| U5 | LIS2DH12TR (accelerometer) | LGA-12 2x2mm | C110926 | $0.46 |
| U6 | AHT20 (temp/humidity) | DFN-6 3x3mm | C2757850 | $0.43 |
| U7 | BH1750FVI-TR (light sensor) | WSOF-6 3x1.6mm | C78960 | $0.49 |
| J1 | USB-C 16-pin | HRO TYPE-C-31-M-12 | C2765186 | $0.10 |
| J2 | JST-PH 2-pin (battery) | SMD | C131337 | $0.03 |
| J3 | JST-SH 8-pin (ePaper) | SMD | — | $0.05 |
| D1 | SS34 Schottky diode | SMA | C8678 | $0.03 |
| D2 | Red LED (charge) | 0402 | C84256 | $0.01 |
| D3 | Green LED (standby) | 0402 | C72043 | $0.01 |
| SW1 | 5-way joystick (SKRHABE010) | SMD 7.4x7.5mm | C139794 | $0.38 |
| SW2 | BOOT button | PTS810 | — | $0.05 |
| SW3 | RESET button | PTS810 | — | $0.05 |
| R1 | 1.2k (PROG) | 0402 | C25752 | $0.01 |
| R2,R3 | 1k (LED current limit) | 0402 | C25585 | $0.01 |
| R4,R5 | 10k (I2C pull-up) | 0402 | C25744 | $0.01 |
| R8,R9 | 5.1k (USB CC) | 0402 | — | $0.01 |
| R10,R11 | 10k (EN/BOOT pull-up) | 0402 | C25744 | $0.01 |
| C3,C7,C8,C9,C10 | 100nF (decoupling) | 0402 | C14663 | $0.01 |
| C4,C5,C6 | 10uF (bulk) | 0402 | C19702 | $0.01 |
| **Total** | | | | **~$5.20** |

---

## Placement Script

`build_esp32s3.py` generates the PCB layout programmatically using KiCad's Python API (`pcbnew`). It:

1. Creates a 30x70mm 4-layer board with design rules matching JLCPCB capabilities
2. Places all 28 components in 6 functional zones
3. Assigns 125 pad-net connections from the `PA` dictionary
4. Creates GND zone pours on F.Cu and B.Cu (starting below antenna keep-out at y=5mm)
5. Adds silkscreen labels (version, USB-C, BAT, BOOT, RST, ePaper)
6. Draws an octopus mascot on the back silkscreen (B.SilkS)
7. Runs DRC via `kicad-cli` and reports violations
8. Renders top, back, and 3D views to `/tmp/dilder-v04/`

When KiCad standard libraries are installed, it loads real footprints. Otherwise, it falls back to manually-defined pads via `make_footprint()` with correct pad geometry for each package type.

---

## Routing Strategy

### Signal Categories

Signals are routed using three strategies based on distance and complexity:

**B.Cu Channels (long-distance, 20-55mm):**
Vertical traces on B.Cu with short F.Cu stubs to component pads. Used for signals that cross multiple zones.

| Signal Group | Channel X | Method |
|-------------|-----------|--------|
| I2C_SCL | 2.0mm | Simple channel |
| I2C_SDA | 4.0mm | Simple channel |
| ACCEL_INT1 | 6.5mm | Simple channel |
| USB_DM | 1.0mm | Custom (left edge, branches to A7+B7) |
| USB_DP | 0.5mm | Custom (left edge, branches to A6+B6) |
| JOY_UP/DOWN/LEFT/RIGHT/CENTER | 7-11mm | Staggered B.Cu L-routes |
| EPD_CLK/MOSI/DC/RST/CS/BUSY | 8.65-26.5mm | Staggered B.Cu L-routes (crossing-free) |
| EN | 3.5mm | Custom multi-zone with T-junctions |
| BOOT | 4.5mm | Custom multi-zone with T-junction |
| CHRG_OUT | 28.0mm | B.Cu crossing under zone C |
| STDBY_OUT | 28.5mm | B.Cu crossing under zone C |

**F.Cu Power (wide traces, 0.4mm):**
Direct L-routes on F.Cu for the power chain:
- VBUS: USB-C → SS34 Schottky (B.Cu right edge to avoid left-side channels)
- VBUS_CHG: Schottky → TP4056
- VBAT: TP4056 → DW01A → AMS1117 → C5 (chain routing)
- BAT_PLUS: FS8205A → JST battery connector

**F.Cu Local (signal traces, 0.2mm):**
Short L-routes on F.Cu within the same zone:
- CC1, CC2: USB-C CC resistors
- PROG: TP4056 charge rate set
- CHRG_LED, STDBY_LED: LED-to-resistor connections
- OD, OC, CS_DRAIN: DW01A ↔ FS8205A (via B.Cu to avoid pad crossings)

### ePaper SPI Routing (Crossing-Free)

The 6 ePaper signals use a staggered B.Cu L-route design that avoids all crossings:

1. Each ESP32 bottom pin gets a 1mm F.Cu stub south to a via at y=28.5
2. B.Cu vertical channel drops to a staggered horizontal Y level
3. B.Cu horizontal crosses to the J3 connector X position
4. B.Cu vertical drops to y=48 (1mm above J3)
5. Via + F.Cu stub to the J3 pin

The stagger order (rightmost ESP32 pin gets lowest horizontal Y) ensures no left-side verticals cross right-side horizontals:

```
EPD_BUSY  (x=15.0) → y=40 → (x=26.5, y=48) → J3.8
EPD_CS    (x=13.7) → y=41 → (x=23.5, y=48) → J3.5
EPD_RST   (x=12.5) → y=42 → (x=25.5, y=48) → J3.7
EPD_DC    (x=11.2) → y=43 → (x=24.5, y=48) → J3.6
EPD_MOSI  (x=9.9)  → y=44 → (x=21.5, y=48) → J3.3
EPD_CLK   (x=8.7)  → y=45 → (x=22.5, y=48) → J3.4
```

### Power Distribution

- **GND**: Zone pours on F.Cu and B.Cu, continuous plane on In1.Cu, 26 stitching vias around perimeter
- **3V3**: Continuous plane on In2.Cu, 17 vias connecting F.Cu pads to the power plane

---

## Routing Scripts

### `route_v04.py` (current)

The v0.4 router loads the placed board from `build_esp32s3.py` and adds:
- Inner layer planes (In1.Cu GND, In2.Cu 3V3)
- B.Cu channel routing for long-distance signals
- Staggered B.Cu L-routes for ePaper and joystick
- Custom routes for USB, EN, BOOT, LED outputs, battery protection
- F.Cu power chain and local signal routes
- 3V3 plane vias and GND stitching vias

Usage:
```bash
python3 build_esp32s3.py     # generate placement
python3 route_v04.py          # add routing
# Then open in KiCad for interactive refinement
```

### Legacy scripts (superseded)

| Script | Era | Notes |
|--------|-----|-------|
| `route_board.py` | RP2040 v0.1 | First attempt, blind L-routing |
| `route_board_v2.py` | RP2040 v0.2 | Collision-aware, 25x75mm board |
| `autorouter.py` | RP2040 | Channel-based auto-routing |
| `fix_drc.py` | RP2040 | DRC fix-up utility |

---

## DRC Status

After programmatic routing (router v0.4):

| Category | Count | Notes |
|----------|-------|-------|
| Unconnected | 67 | GND + 3V3 — resolves with zone fill |
| Shorting items | 69 | F.Cu stubs crossing pads — needs manual fix |
| Track crossings | 37 | B.Cu intersections — needs via pairs |
| Clearance | 54 | Traces close to pads/edges |
| Silk over copper | 49 | Cosmetic |
| Solder mask bridge | 41 | Manufacturing advisory |
| Via dangling | 33 | 3V3 vias to unfilled plane |
| Copper edge clearance | 12 | Near board edges |
| Other | ~30 | Text, hole clearance, etc. |

**To resolve in KiCad:**
1. Run zone fill (Edit > Fill All Zones) — fixes ~67 unconnected + ~33 via_dangling
2. Nudge F.Cu stubs to clear component pads — fixes ~69 shorts
3. Add via pairs at B.Cu crossing points — fixes ~37 crossings
4. Adjust traces near board edges — fixes ~12 edge clearance

---

## Design Rules

Configured for JLCPCB manufacturing:

| Rule | Value |
|------|-------|
| Min trace width | 0.127mm (5mil) |
| Min clearance | 0.2mm |
| Min via diameter | 0.6mm |
| Min via drill | 0.3mm |
| Min drill | 0.2mm |
| Board thickness | 1.6mm |
| Copper weight | 1oz |
| Signal trace width | 0.2mm |
| Power trace width | 0.4mm |
| Solder mask | Green |
| Surface finish | HASL (lead-free) |

---

## Antenna Keep-Out

The ESP32-S3-WROOM-1 module antenna extends above the board's top edge. Per Espressif's hardware design guidelines:

- **No copper on any layer** within the top 5mm of the board (y=0 to y=5)
- GND zone pours start at y=5mm
- Inner planes (In1.Cu, In2.Cu) also start at y=5mm
- Module centered at (15, 14.75) with body top at ~y=2
- Antenna radiates from the module top, extending past the board edge

---

## Silkscreen

### Front (F.SilkS)

- "DILDER v0.4" at bottom center
- "USB-C", "BAT", "BOOT", "RST", "ePaper" functional labels
- Component reference designators

### Back (B.SilkS)

- Octopus mascot artwork (procedurally generated arcs + lines)
- "DILDER" title
- "dilder.dev" website
- "v0.4  2026" version/year

---

## Fabrication Workflow

### Phase 5 — Gerber Export (pending)

After DRC is clean:

1. Assign LCSC part numbers via JLCPCB Tools plugin
2. Generate BOM + CPL CSV files
3. Export Gerber files for all layers + drill files
4. Package into ZIP for upload

### Phase 6 — JLCPCB Order (pending)

| Setting | Value |
|---------|-------|
| PCB Qty | 5 (minimum) |
| Layers | 4 |
| Thickness | 1.6mm |
| Color | Green |
| Surface finish | HASL lead-free |
| SMT Assembly | Top side only |
| Shipping | DHL Express to Germany (~$15-25) |

Estimated total: ~$35-50 for 5 assembled boards.

---

## Revision History

| Version | Date | Board Size | MCU | Components | BOM Cost | Changes |
|---------|------|-----------|-----|------------|----------|---------|
| v0.1 | 2026-04-13 | 25x75mm | RP2040 | 33 | ~$11.14 | Initial design with bare RP2040 |
| v0.2 | 2026-04-14 | 25x75mm | RP2040 | 33 | ~$11.14 | Collision-aware routing |
| v0.3 | 2026-04-15 | 45x80mm | ESP32-S3 | 20 | ~$10.60 | Switched to ESP32-S3 module, dropped flash/crystal/GPS |
| v0.4 | 2026-04-15 | 30x70mm | ESP32-S3 | 28 | ~$4.26 | Compact redesign, LIS2DH12TR, BOOT/RST buttons, 4-layer routing |
