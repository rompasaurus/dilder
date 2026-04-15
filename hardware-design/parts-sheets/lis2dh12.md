# LIS2DH12TR — 3-Axis Accelerometer with Pedometer

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Manufacturer** | STMicroelectronics |
| **Part Number** | LIS2DH12TR |
| **Function** | 3-axis MEMS accelerometer with built-in pedometer |
| **Package** | LGA-12 (2 x 2 x 1mm) |
| **LCSC** | [C110926](https://www.lcsc.com/product-detail/C110926.html) |
| **Price (qty 5)** | ~$0.46 |
| **Dilder ref** | U5 |

## Why This Part

Replaces the MPU-6050 ($6.88) — a 6-axis IMU whose gyroscope was unnecessary. The LIS2DH12 provides everything the Dilder needs (step counting, shake detection, orientation) at **93% less cost** with **lower power consumption** and a **smaller footprint**.

## Key Specifications

| Parameter | Value |
|-----------|-------|
| Axes | 3 (X, Y, Z — accelerometer only) |
| Resolution | 12-bit (high-res), 10-bit (normal), 8-bit (low-power) |
| Measurement range | +/-2g, +/-4g, +/-8g, +/-16g (selectable) |
| Output data rate (ODR) | 1 Hz to 5.376 kHz |
| Interface | I2C (up to 400 kHz) or SPI (up to 10 MHz) |
| I2C address | 0x18 (SA0=GND) or 0x19 (SA0=VCC) |
| Supply voltage | 1.71V to 3.6V |
| I/O voltage | 1.1V to VDD |
| Current (high-res, 400Hz) | 185 uA |
| Current (low-power, 1Hz) | 2 uA |
| Current (power-down) | 0.5 uA |
| Temperature sensor | Yes (8-bit, +/-1C accuracy) |
| FIFO | 32 levels |
| Interrupt pins | 2 (INT1, INT2) — programmable |

## Built-In Features (Hardware)

| Feature | Description | Dilder Use |
|---------|-------------|------------|
| **Pedometer** | Counts steps in hardware, fires interrupt per step | Step counting for pet engagement |
| **Click detection** | Single-click and double-click on any axis | Tap to pet, double-tap to feed |
| **Free-fall** | Detects 0g on all axes simultaneously | "You dropped me!" reaction |
| **Activity/Inactivity** | Threshold-based motion detection | Sleep when device is stationary |
| **6D Orientation** | Detects which face is pointing up | Face-down = sleep mode |
| **Wake-up** | Fires interrupt when motion exceeds threshold | Wake ESP32 from deep sleep |

## Pin Connections (Dilder Board)

| LIS2DH12 Pin | Pin # | Connect To | Notes |
|-------------- |-------|------------|-------|
| VDD | 1 | 3.3V | Power supply |
| GND | 5, 9, 12 | GND | All ground pins connected |
| SDA/SDI | 4 | ESP32 GPIO16 | I2C data (10k pull-up to 3.3V) |
| SCL/SPC | 6 | ESP32 GPIO17 | I2C clock (10k pull-up to 3.3V) |
| SA0/SDO | 3 | GND | Sets I2C address to 0x18 |
| CS | 7 | 3.3V | High = I2C mode (not SPI) |
| INT1 | 8 | ESP32 GPIO18 | Step detector / activity interrupt |
| INT2 | 11 | N/C | Not connected |

## Application Circuit

```
                  3.3V
                   |
                 [10k]  [10k]     3.3V
                   |      |        |
ESP32 GPIO16 ─── SDA    SCL ─── GPIO17
                   |      |
              .----+------+----.
              |   LIS2DH12TR   |
              |                |
              | SA0=GND  CS=3V3|
              |                |
              | INT1 ──────────┼──► GPIO18 (interrupt)
              |                |
              '----+-----------'
                   |
                  GND
```

## Datasheet

- **STMicroelectronics official:** [LIS2DH12 Datasheet](https://www.st.com/resource/en/datasheet/lis2dh12.pdf)
- **Application note (pedometer):** [AN5005 — LIS2DH12 Pedometer](https://www.st.com/resource/en/application_note/an5005-lis2dh12-pedometer-functionality-stmicroelectronics.pdf)
- **LCSC product page:** [C110926](https://www.lcsc.com/product-detail/C110926.html)
