# Board Design v0.4

> Custom PCB design for the Dilder — 30x70mm, 4-layer, ESP32-S3, 28 components, ~$4.26/board BOM cost.

---

## Board Overview

| Parameter | Value |
|-----------|-------|
| Board size | 30 x 70 mm |
| Layers | 4 (F.Cu, In1.Cu, In2.Cu, B.Cu) |
| Thickness | 1.6 mm |
| Components | 28 unique (30 placed) |
| Nets | 34 |
| BOM cost | ~$4.26/board |
| Target fab | JLCPCB (SMT assembly) |

```
Board layout (30 x 70 mm, top view):
+------------------------------+ y=0
|  ~~~ Antenna overhang ~~~    | Zone A
|                              |
|    +------------------+      |
|    |   ESP32-S3-WROOM |      |
|    |    -1-N16R8      |      | Zone B
|    |                  |      |
|    +------------------+      |
|  [AMS1117]  [TP4056]        |
|  [DW01A] [FS8205A] [Batt]   | Zone C
|                              |
| [Accel]  [ePaper connector]  |
| [BOOT] [RESET]               | Zone D
|                              |
|     [5-Way Joystick]         | Zone E
|                              |
|      [USB-C]                 | Zone F
+------------------------------+ y=70
```

---

## Layer Stack

| Layer | Purpose |
|-------|---------|
| **F.Cu** | Component pads, short signal stubs, GND pour |
| **In1.Cu** | Continuous ground reference plane |
| **In2.Cu** | 3.3V power distribution plane |
| **B.Cu** | Long signal runs, additional GND pour |

Both ground pours and both planes start below y=5mm to preserve the antenna keep-out zone.

---

## Component Zones

The board is divided into 6 functional zones from top to bottom:

### Zone A — Antenna (y=0-3mm)

No copper on any layer. The ESP32-S3 module antenna extends above the board edge.

### Zone B — ESP32 Module (y=3-25mm)

ESP32-S3-WROOM-1-N16R8 centered at (15, 14.75). Decoupling caps on left margin, charge/standby LEDs on right margin.

### Zone C — Power (y=26-42mm)

AMS1117-3.3 LDO, TP4056 charger, DW01A + FS8205A battery protection, JST-PH battery connector, SS34 Schottky diode.

### Zone D — Peripherals (y=42-54mm)

LIS2DH12TR accelerometer (I2C), 8-pin JST-SH ePaper connector (SPI), BOOT and RESET buttons.

### Zone E — Joystick (y=54-62mm)

SKRHABE010 5-way joystick centered for thumb access.

### Zone F — USB-C (y=62-70mm)

HRO TYPE-C-31-M-12 connector with 5.1k CC pull-down resistors.

---

## GPIO Pin Assignments

| GPIO | Function | Interface |
|------|----------|-----------|
| GPIO0 | Boot select | Digital (pull-up) |
| GPIO3 | e-Paper DC | SPI |
| GPIO4-8 | Joystick (UP/DOWN/LEFT/RIGHT/CENTER) | Digital (internal pull-up) |
| GPIO9 | e-Paper CLK | SPI SCK |
| GPIO10 | e-Paper MOSI | SPI MOSI |
| GPIO11 | e-Paper RST | Digital |
| GPIO12 | e-Paper BUSY | Digital |
| GPIO16 | Accelerometer SDA | I2C |
| GPIO17 | Accelerometer SCL | I2C |
| GPIO18 | Accelerometer INT1 | Digital |
| GPIO19 | USB D- | USB |
| GPIO20 | USB D+ | USB |
| GPIO46 | e-Paper CS | SPI CS |

---

## Bill of Materials

| Ref | Component | Package | Unit Cost |
|-----|-----------|---------|-----------|
| U1 | ESP32-S3-WROOM-1-N16R8 | Module 18x25.5mm | $2.80 |
| U2 | TP4056 (LiPo charger) | ESOP-8 | $0.07 |
| U3 | DW01A (battery protection) | SOT-23-6 | $0.05 |
| Q1 | FS8205A (dual MOSFET) | SOT-23-6 | $0.05 |
| U4 | AMS1117-3.3 (LDO) | SOT-223-3 | $0.05 |
| U5 | LIS2DH12TR (accelerometer) | LGA-12 2x2mm | $0.46 |
| J1 | USB-C 16-pin | HRO TYPE-C-31-M-12 | $0.10 |
| J2 | JST-PH 2-pin (battery) | SMD | $0.03 |
| J3 | JST-SH 8-pin (ePaper) | SMD | $0.05 |
| D1 | SS34 Schottky diode | SMA | $0.03 |
| D2/D3 | LEDs (charge/standby) | 0402 | $0.01 |
| SW1 | 5-way joystick (SKRHABE010) | SMD 7.4x7.5mm | $0.38 |
| SW2/SW3 | BOOT/RESET buttons | PTS810 | $0.05 |
| R1-R11 | Resistors (various) | 0402 | $0.01 |
| C3-C8 | Capacitors (100nF/10uF) | 0402 | $0.01 |
| **Total** | | | **~$4.26** |

---

## Design Rules

| Rule | Value |
|------|-------|
| Min trace width | 0.15 mm (signal), 0.5 mm (power) |
| Min clearance | 0.15 mm |
| Via drill | 0.3 mm |
| Via annular ring | 0.15 mm |
| Antenna keep-out | No copper within 5mm of board top edge |

---

## Fabrication Workflow

1. Run DRC in KiCad against JLCPCB constraints
2. Export Gerbers via JLCPCB fabrication plugin
3. Upload to JLCPCB with 4-layer stackup
4. Select SMT assembly for top-side components
5. Upload BOM and pick-and-place files
6. Review and order (5 boards minimum)

The full KiCad project lives in `hardware-design/Board Design kicad/` with placement scripts, routing scripts, and component libraries.
