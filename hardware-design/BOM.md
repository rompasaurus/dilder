# Dilder PCB v0.3 — Bill of Materials

ESP32-S3-WROOM-1-N16R8 design, 27 components, target fab: JLCPCB

## ICs & Modules

| Ref | Part | Package | LCSC | Qty | ~Cost |
|-----|------|---------|------|-----|-------|
| U1 | ESP32-S3-WROOM-1-N16R8 | RF Module (18x25.5mm) | C2913196 | 1 | $2.80 |
| U2 | TP4056 (1A LiPo charger) | ESOP-8 | C382139 | 1 | $0.07 |
| U3 | DW01A (battery protection) | SOT-23-6 | C351410 | 1 | $0.05 |
| Q1 | FS8205A (dual MOSFET) | SOT-23-6 | C908265 | 1 | $0.05 |
| U4 | AMS1117-3.3 (3.3V LDO) | SOT-223-3 | C6186 | 1 | $0.05 |
| U6 | LIS2DH12TR (3-axis accelerometer) | LGA-12 2x2mm | C110926 | 1 | $0.46 |

## Connectors

| Ref | Part | Package | LCSC | Qty | ~Cost |
|-----|------|---------|------|-----|-------|
| J1 | USB-C 16-pin receptacle | HRO TYPE-C-31-M-12 | C2765186 | 1 | $0.10 |
| J2 | JST PH 2-pin (battery) | JST_PH_S2B horizontal | C131337 | 1 | $0.03 |
| J3 | 8-pin JST-SH (ePaper) | JST_SH 1mm horizontal | — | 1 | $0.05 |

## Switches & Diodes

| Ref | Part | Package | LCSC | Qty | ~Cost |
|-----|------|---------|------|-----|-------|
| SW1 | SKRHABE010 (5-way joystick) | Alps SMD | C139794 | 1 | $0.38 |
| D1 | SS34 Schottky diode | SMA | C8678 | 1 | $0.03 |
| D2 | Red LED (charge indicator) | 0402 | C84256 | 1 | $0.01 |
| D3 | Green LED (standby indicator) | 0402 | C72043 | 1 | $0.01 |

## Resistors (all 0402)

| Ref | Value | Purpose | LCSC | Qty | ~Cost |
|-----|-------|---------|------|-----|-------|
| R1 | 1.2k | TP4056 PROG (sets 1A charge) | C25752 | 1 | $0.01 |
| R2 | 1k | Charge LED current limit | C25585 | 1 | $0.01 |
| R3 | 1k | Standby LED current limit | C25585 | 1 | $0.01 |
| R4 | 10k | I2C SDA pull-up | C25744 | 1 | $0.01 |
| R5 | 10k | I2C SCL pull-up | C25744 | 1 | $0.01 |
| R8 | 5.1k | USB CC1 pull-down | — | 1 | $0.01 |
| R9 | 5.1k | USB CC2 pull-down | — | 1 | $0.01 |
| R10 | 10k | ESP32 EN pull-up | C25744 | 1 | $0.01 |

## Capacitors (all 0402)

| Ref | Value | Purpose | LCSC | Qty | ~Cost |
|-----|-------|---------|------|-----|-------|
| C3 | 100nF | ESP32 decoupling | C14663 | 1 | $0.01 |
| C4 | 10uF | ESP32 bulk bypass | C19702 | 1 | $0.01 |
| C5 | 10uF | LDO input | C19702 | 1 | $0.01 |
| C6 | 10uF | LDO output | C19702 | 1 | $0.01 |
| C7 | 100nF | IMU VDD decoupling | C14663 | 1 | $0.01 |
| C9 | 100nF | IMU REGOUT bypass | C14663 | 1 | $0.01 |

## Cost Summary

| Category | Cost/board |
|----------|-----------|
| Components (total) | ~$4.18 |
| PCB fabrication (5 boards) | ~$2.00 |
| SMT assembly (5 boards) | ~$8.00 + parts |
| **Estimated total (5 boards)** | **~$35-50** |

## GPIO Pin Assignment

| GPIO | Function | Interface |
|------|----------|-----------|
| GPIO3 | EPD_DC | SPI (digital) |
| GPIO4 | Joystick UP | Digital in (pull-up) |
| GPIO5 | Joystick DOWN | Digital in (pull-up) |
| GPIO6 | Joystick LEFT | Digital in (pull-up) |
| GPIO7 | Joystick RIGHT | Digital in (pull-up) |
| GPIO8 | Joystick CENTER | Digital in (pull-up) |
| GPIO9 | EPD_CLK (SCK) | SPI |
| GPIO10 | EPD_MOSI | SPI |
| GPIO11 | EPD_RST | Digital out |
| GPIO12 | EPD_BUSY | Digital in |
| GPIO16 | I2C SDA (LIS2DH12TR) | I2C |
| GPIO17 | I2C SCL (LIS2DH12TR) | I2C |
| GPIO19 | USB D- | USB-OTG |
| GPIO20 | USB D+ | USB-OTG |
| GPIO46 | EPD_CS | SPI CS |

## Changes from v0.2 (RP2040)

Removed:
- RP2040 bare MCU (replaced by ESP32-S3 module)
- W25Q16JV external flash (16MB integrated in module)
- 12MHz crystal + 2x 15pF load caps (integrated in module)
- 2x 27R USB series resistors (ESP32-S3 native USB-OTG)
- ATGM336H GPS module + decoupling cap (dropped — using WiFi fingerprinting + BLE scanning)

Added:
- ESP32-S3-WROOM-1-N16R8 module (WiFi + BLE 5.0, 16MB flash, 8MB PSRAM)

Net component count: 27 → 20 unique parts (simpler BOM, easier assembly)
