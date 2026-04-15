# Parts Sheets — Component Reference Library

Detailed specification sheets for every component on the Dilder custom PCB board. Each file documents one component with its specifications, pin assignments, application notes, and links to official manufacturer datasheets.

Manufacturer datasheets that could be downloaded directly are in the `manufacturer-datasheets/` folder. For components where the manufacturer blocks direct PDF downloads, the links below go to the official LCSC product page where the datasheet is available inline.

---

## Core MCU

- [ESP32-S3-WROOM-1-N16R8](esp32-s3-wroom1.md) — Main MCU module (WiFi + BLE, 16MB flash, 8MB PSRAM)

## Sensors

- [LIS2DH12TR](lis2dh12.md) — 3-axis accelerometer with built-in pedometer

## Power Management

- [TP4056](tp4056.md) — LiPo battery charger IC (1A, CC/CV)
- [DW01A](dw01a.md) — Battery protection IC (over-discharge, over-charge, short-circuit)
- [FS8205A](fs8205a.md) — Dual N-channel MOSFET (battery protection switch)
- [AMS1117-3.3](ams1117.md) — 3.3V LDO voltage regulator (1A)
- [SS34](ss34.md) — Schottky barrier diode (USB/battery path selection)

## Input

- [SKRHABE010](skrhabe010.md) — Alps Alpine 5-way SMD joystick

## Connectors

- [USB-C 16-Pin](usb-c-connector.md) — USB Type-C receptacle (programming + charging)
- [JST PH 2-Pin](jst-ph-battery.md) — Battery connector (2.0mm pitch)

## Status Indicators

- [Red LED (0805)](led-red.md) — Charging indicator
- [Green LED (0603)](led-green.md) — Charge complete indicator

---

*Last updated: 2026-04-15*
