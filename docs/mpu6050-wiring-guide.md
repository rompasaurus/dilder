# MPU-6050 Wiring Guide — Pico 2 W

## Module: GY-521 / MPU-6050 (8-pin breakout)

## Wiring Table

| MPU-6050 Pin | Wire To         | Pico 2 W Pin | Notes                          |
|-------------|-----------------|-------------|--------------------------------|
| VCC         | 3V3(OUT)        | Pin 36      | 3.3V regulated output          |
| GND         | GND             | Pin 33      | Any GND pin works              |
| SCL         | GP1 (I2C0 SCL)  | Pin 2       | I2C clock                      |
| SDA         | GP0 (I2C0 SDA)  | Pin 1       | I2C data                       |
| AD0         | GND             | Pin 33      | Sets I2C address to 0x68       |
| INT         | —               | Unconnected | Optional (for interrupt-driven) |
| XDA         | —               | Unconnected | Aux I2C (unused)               |
| XCL         | —               | Unconnected | Aux I2C (unused)               |

## Pin Map on Pico 2 W Header

```
                    Pico 2 W (USB at top)
                  ┌─────────────────────┐
  SDA  GP0  Pin 1 │■                    │ Pin 40  VBUS
  SCL  GP1  Pin 2 │■                    │ Pin 39  VSYS ← TP4056 OUT+
        GND Pin 3 │                     │ Pin 38  GND  ← TP4056 OUT-
  JOY↑ GP2  Pin 4 │                     │ Pin 37  3V3_EN
  JOY↓ GP3  Pin 5 │                     │ Pin 36  3V3(OUT) ← MPU VCC, Waveshare VCC
  JOY← GP4  Pin 6 │                     │ Pin 35  ADC_VREF
  JOY→ GP5  Pin 7 │                     │ Pin 34  GP28/ADC2
        GND Pin 8 │                     │ Pin 33  GND ← MPU GND, MPU AD0
  JOYC GP6  Pin 9 │                     │ Pin 32  GP27/ADC1
  SPK  GP7 Pin 10 │                     │ Pin 31  GP26/ADC0
  DC   GP8 Pin 11 │                     │ Pin 30  RUN
  CS   GP9 Pin 12 │                     │ Pin 29  GP22
  CLK GP10 Pin 13 │                     │ Pin 28  GND
  DIN GP11 Pin 14 │                     │ Pin 27  GP21
  RST GP12 Pin 15 │                     │ Pin 26  GP20
  BSY GP13 Pin 16 │                     │ Pin 25  GP19
  BUZ GP14 Pin 17 │                     │ Pin 24  GP18
        GND Pin 18│                     │ Pin 23  GND
       GP15 Pin 19│ (free)              │ Pin 22  GP17
       GP16 Pin 20│ (free)              │ Pin 21  GP16
                  └─────────────────────┘
```

## I2C Details

- **Bus:** I2C0
- **Address:** 0x68 (AD0 tied to GND)
- **Speed:** 400 kHz (Fast mode — MPU-6050 supports up to 400 kHz)
- **Pull-ups:** Onboard on the GY-521 module (4.7k to VCC). No external resistors needed.

## What the MPU-6050 Provides

| Sensor         | Range (default)   | Resolution |
|---------------|-------------------|------------|
| Accelerometer | +/- 2g            | 16-bit     |
| Gyroscope     | +/- 250 deg/s     | 16-bit     |
| Temperature   | -40 to +85 C      | 16-bit     |

## Register Quick Reference

| Register | Address | Purpose                    |
|---------|---------|----------------------------|
| PWR_MGMT_1  | 0x6B | Power management (write 0 to wake) |
| ACCEL_XOUT_H | 0x3B | Accel X high byte (burst read 6 bytes for XYZ) |
| GYRO_XOUT_H  | 0x43 | Gyro X high byte (burst read 6 bytes for XYZ) |
| TEMP_OUT_H   | 0x41 | Temperature high byte      |
| WHO_AM_I     | 0x75 | Device ID (should read 0x68) |
| ACCEL_CONFIG | 0x1C | Accelerometer range config |
| GYRO_CONFIG  | 0x1B | Gyroscope range config     |
