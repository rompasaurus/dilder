# Parts Sheets — Component Reference Library

Detailed specification sheets for every component on the Dilder custom PCB. Each file documents one component with full technical background, how-it-works explanations, specifications, pin assignments, application notes, and links to official manufacturer datasheets.

Every sheet includes a **Table of Contents**, a **technology explainer** (dumbed down for beginners), a **history/background** section, and **cited sources**.

Manufacturer datasheets (PDF) are in the `manufacturer-datasheets/` folder. See `manufacturer-datasheets/DOWNLOAD-GUIDE.md` for download links.

---

## Core MCU

- [ESP32-S3-WROOM-1-N16R8](esp32-s3-wroom1.md) — Main MCU module (dual-core Xtensa LX7, WiFi + BLE 5.0, 16MB flash, 8MB PSRAM). Covers CPU architecture, memory types (flash vs PSRAM), WiFi/BLE radio technology, PCB antenna design, USB-OTG, boot modes, and Espressif company history.

## Sensors

- [LIS2DH12TR](lis2dh12.md) — 3-axis MEMS accelerometer with hardware pedometer. Covers MEMS fabrication (proof mass, differential capacitors, sigma-delta ADC), all built-in features (step counter, click detection, free-fall, 6D orientation), operating modes and power, I2C protocol explanation, and STMicroelectronics/MEMS history.
- [AHT20](aht20.md) — Temperature and humidity sensor (I2C, DFN-6). Covers capacitive humidity sensing, CMOS temperature measurement, factory calibration, and signal conditioning.
- [BH1750FVI-TR](bh1750fvi.md) — Ambient light sensor (I2C, WSOF-6). Covers photodiode-based lux measurement, spectral response close to human eye, measurement modes, and adjustable sensitivity.

## Power Management

- [TP4056](tp4056.md) — LiPo battery charger IC (1A, CC/CV). Covers lithium battery charging theory (three phases, CC/CV algorithm), internal block diagram, thermal regulation, charge termination, RPROG current setting table, status LED wiring, and common mistakes.
- [DW01A](dw01a.md) — Battery protection IC. Covers why lithium batteries need protection (over-discharge chemistry, over-charge thermal runaway, short circuit), monitoring circuit internals, MOSFET gate control, detection thresholds with hysteresis, and the DW01A+FS8205A pairing.
- [FS8205A](fs8205a.md) — Dual N-channel MOSFET (battery protection switch). Covers how MOSFETs work (field-effect switching, gate-source voltage, Rds(on)), the back-to-back configuration (body diode problem), and independent charge/discharge path control.
- [AMS1117-3.3](ams1117.md) — 3.3V LDO voltage regulator (1A). Covers voltage regulation theory (linear vs switching), bandgap reference internals, dropout voltage, capacitor requirements, thermal calculations, LDO vs buck converter tradeoffs, and the 1117 family history.
- [SS34](ss34.md) — Schottky barrier diode (USB/battery path selection). Covers diode physics (PN junction, forward/reverse bias), what makes Schottky special (metal-semiconductor junction, lower Vf, no reverse recovery), and power path design.

## Input

- [SKRHABE010](skrhabe010.md) — Alps Alpine 5-way SMD joystick. Covers multi-direction switch mechanics (rocker mechanism, tactile dome contacts, contact physics), GPIO wiring with internal pull-ups, software debouncing, and Alps Alpine company history.

## Connectors

- [USB-C 16-Pin](usb-c-connector.md) — USB Type-C receptacle (programming + charging). Covers USB-C reversibility (dual-row design), CC pin orientation detection and power negotiation, 16-pin vs 24-pin differences, USB 2.0 differential signaling, and USB history from 1996 to EU mandate.
- [JST PH 2-Pin](jst-ph-battery.md) — Battery connector (2.0mm pitch). Covers JST connector family comparison (PH, SH, XH, ZH), polarity warning, and JST company history.
- [JST SH 8-Pin](jst-sh-epaper.md) — E-paper display connector (1.0mm pitch). Covers the SPI interface to the e-paper display (SCK, MOSI, CS, DC, RST, BUSY signals), data rates, and frame buffer transfer times.

## Status Indicators

- [Red LED (0805)](led-red.md) — Charging indicator. Covers LED physics (light-emitting PN junction, bandgap energy to photon wavelength), semiconductor materials for each color, current limiting calculations, and the TP4056 open-drain interface.
- [Green LED (0603)](led-green.md) — Charge complete indicator. Covers InGaN material system, higher Vf explanation, Shuji Nakamura's Nobel Prize for blue/green LEDs.

## Passive Components

- [Resistors (0402)](resistors-0402.md) — All 8 resistors on the board. Covers Ohm's Law, what physically creates resistance, thick film vs thin film manufacturing (ruthenium oxide screen printing, laser trimming), each resistor's specific function (charge current, LED limiting, I2C pull-up, USB CC, EN pull-up), and tolerance grades.
- [Capacitors (0402)](capacitors-0402.md) — All 8 capacitors on the board. Covers capacitor physics (charge storage in electric fields), MLCC construction (hundreds of stacked layers), dielectric materials (X5R, X7R, C0G), why every IC needs decoupling caps (switching noise, trace inductance, local charge reservoir), the 100nF + 10uF combination, and DC bias effect.

---

## Component Count Summary

| Category | Count | Parts |
|----------|-------|-------|
| ICs & Modules | 8 | ESP32-S3, TP4056, DW01A, FS8205A, AMS1117, LIS2DH12, AHT20, BH1750 |
| Connectors | 3 | USB-C, JST PH battery, JST SH e-paper |
| Switch | 1 | SKRHABE010 5-way joystick |
| Diodes & LEDs | 3 | SS34, Red LED, Green LED |
| Resistors | 8 | 1.2k, 2x 1k, 3x 10k, 2x 5.1k |
| Capacitors | 8 | 5x 100nF, 3x 10uF |
| **Total** | **31** | |

---

*Last updated: 2026-04-15*
