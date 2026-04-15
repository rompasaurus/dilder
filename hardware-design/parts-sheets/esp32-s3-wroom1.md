# ESP32-S3-WROOM-1-N16R8 — Main MCU Module

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Manufacturer** | Espressif Systems |
| **Part Number** | ESP32-S3-WROOM-1-N16R8 |
| **Function** | System-on-Module: dual-core MCU + WiFi + BLE |
| **Package** | Module, 18 x 25.5 x 3.1mm |
| **LCSC** | [C2913202](https://www.lcsc.com/product-detail/C2913202.html) |
| **Price (qty 5)** | ~$2.80 |
| **Dilder ref** | U1 |

## Key Specifications

| Parameter | Value |
|-----------|-------|
| CPU | Dual-core Xtensa LX7 @ 240 MHz |
| SRAM | 512 KB |
| Flash | 16 MB (integrated) |
| PSRAM | 8 MB (integrated) |
| WiFi | 802.11 b/g/n, 2.4 GHz |
| Bluetooth | BLE 5.0 |
| GPIO | 36 programmable |
| ADC | 2x 12-bit SAR ADC, 20 channels |
| SPI | 4x SPI interfaces |
| I2C | 2x I2C interfaces |
| UART | 3x UART interfaces |
| USB | USB 1.1 OTG (native, no external PHY) |
| Operating voltage | 3.0V - 3.6V |
| Operating temp | -40C to +85C |
| Antenna | PCB antenna (integrated, requires keep-out zone) |

## Pin Usage on Dilder Board

| GPIO | Function | Interface |
|------|----------|-----------|
| GPIO3 | e-Paper DC | Digital out |
| GPIO4-8 | Joystick (UP/DOWN/LEFT/RIGHT/CENTER) | Digital in (pull-up) |
| GPIO9 | e-Paper CLK | SPI SCK |
| GPIO10 | e-Paper MOSI | SPI MOSI |
| GPIO11 | e-Paper RST | Digital out |
| GPIO12 | e-Paper BUSY | Digital in |
| GPIO16 | LIS2DH12 SDA | I2C data |
| GPIO17 | LIS2DH12 SCL | I2C clock |
| GPIO18 | LIS2DH12 INT1 | Interrupt input |
| GPIO19 | USB D- | USB |
| GPIO20 | USB D+ | USB |
| GPIO46 | e-Paper CS | SPI CS |

## Antenna Keep-Out Zone

The module has a PCB antenna at one end. The area under and around the antenna must be kept clear of copper on ALL layers (including ground planes) for proper RF performance. See the datasheet Section 4.1 for the exact keep-out dimensions.

## Datasheet

- **Local copy:** [manufacturer-datasheets/ESP32-S3-WROOM-1-datasheet.pdf](manufacturer-datasheets/ESP32-S3-WROOM-1-datasheet.pdf)
- **Espressif official:** [esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)
- **Hardware design guidelines:** [ESP32-S3 Schematic Checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html)
- **LCSC product page:** [C2913202](https://www.lcsc.com/product-detail/C2913202.html)
