# LIS2DH12TR — 3-Axis MEMS Accelerometer

## Table of Contents

- [Quick Reference](#quick-reference)
- [What Is This Part?](#what-is-this-part)
- [How MEMS Accelerometers Work](#how-mems-accelerometers-work)
  - [The Mechanical Structure](#the-mechanical-structure)
  - [From Motion to Voltage](#from-motion-to-voltage)
  - [From Voltage to Digital Numbers](#from-voltage-to-digital-numbers)
- [Why This Part Instead of the MPU-6050](#why-this-part-instead-of-the-mpu-6050)
- [Key Specifications](#key-specifications)
- [Built-In Hardware Features](#built-in-hardware-features)
- [Operating Modes and Power](#operating-modes-and-power)
- [The I2C Interface](#the-i2c-interface)
- [Pin Connections on Dilder Board](#pin-connections-on-dilder-board)
- [Application Circuit](#application-circuit)
- [Register Map Highlights](#register-map-highlights)
- [History and Background](#history-and-background)
- [Datasheet and Sources](#datasheet-and-sources)

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Manufacturer** | STMicroelectronics (Geneva, Switzerland) |
| **Part Number** | LIS2DH12TR |
| **Function** | 3-axis MEMS accelerometer with embedded pedometer |
| **Package** | LGA-12 (2 x 2 x 1 mm) |
| **LCSC** | [C110926](https://www.lcsc.com/product-detail/C110926.html) |
| **Price (qty 5)** | ~$0.46 |
| **Dilder ref** | U5 |

---

## What Is This Part?

The LIS2DH12 is a **tiny motion sensor** that detects acceleration in three dimensions (X, Y, Z). When you move, shake, tilt, tap, or drop the Dilder, this chip measures the forces involved and converts them into digital numbers the ESP32 can read.

It's only 2mm x 2mm — about the size of a sesame seed — yet inside it contains:
- A microscopic mechanical structure that flexes when forces are applied
- Analog electronics to measure that flexion
- A 12-bit analog-to-digital converter
- A digital signal processor with built-in step counter, click detector, and orientation detector
- An I2C/SPI communication interface
- A 32-sample deep FIFO buffer

In the Dilder, it provides:
- **Step counting** — tracks how many steps the user takes (pet engagement metric)
- **Tap/click detection** — tap to pet, double-tap to feed
- **Free-fall detection** — "you dropped me!" emotional reaction
- **Orientation sensing** — face-down triggers sleep mode
- **Wake-from-sleep** — any motion wakes the ESP32 from deep sleep

---

## How MEMS Accelerometers Work

MEMS stands for **Micro-Electro-Mechanical Systems** — microscopic machines built using semiconductor fabrication processes (the same photolithography used to make computer chips).

### The Mechanical Structure

Inside the LIS2DH12, etched into silicon, is a tiny mass suspended by microscopic springs. Imagine a weight hanging from four springs inside a box:

```
     Fixed frame (attached to chip package)
    ┌─────────────────────────────┐
    │   spring    spring          │
    │   ╱╲╱╲╱╲──┬──╱╲╱╲╱╲       │
    │            │                │
    │   spring ──┤── spring      │
    │   ╱╲╱╲╱╲──┤──╱╲╱╲╱╲       │
    │            │                │
    │      PROOF MASS             │
    │    (movable silicon)        │
    │            │                │
    │   spring ──┤── spring      │
    │   ╱╲╱╲╱╲──┴──╱╲╱╲╱╲       │
    └─────────────────────────────┘
```

When the device accelerates (or gravity pulls on it), the proof mass shifts relative to the fixed frame. Newton's second law: F = ma. The springs resist the displacement, reaching equilibrium where the spring force equals the inertial force. More acceleration = more displacement.

The actual MEMS structure is about 500 micrometers across (half a millimeter). The springs are beams a few micrometers wide. The proof mass moves by nanometers — billionths of a meter.

### From Motion to Voltage

The displacement is measured using **differential capacitors**. Comb-like fingers extend from both the proof mass and the fixed frame, interleaved like meshed fingers:

```
Fixed    │  │  │  │  │  │    Fixed
fingers  │  │  │  │  │  │    fingers
         │  │  │  │  │  │
    ─────┤  ├──┤  ├──┤  ├─── Proof mass fingers
         │  │  │  │  │  │
         │  │  │  │  │  │
Fixed    │  │  │  │  │  │    Fixed
fingers  │  │  │  │  │  │    fingers
```

When the proof mass shifts, the gap between one set of fingers decreases (increasing capacitance, since C = εA/d) while the gap on the other side increases (decreasing capacitance). The difference in capacitance is proportional to displacement, which is proportional to acceleration.

A charge amplifier circuit converts this tiny capacitance change (femtofarads — 10^-15 Farads) into a voltage. This is done for each axis independently (X, Y, Z), using three separate mechanical structures oriented in three perpendicular directions.

### From Voltage to Digital Numbers

The analog voltage is fed into a **sigma-delta ADC** (analog-to-digital converter). This type of ADC works by:

1. Comparing the input to a reference voltage
2. If input > reference, output a 1; else output a 0
3. Feed the result back to adjust the reference (this is the "delta" part)
4. Repeat this millions of times per second
5. A digital filter averages the stream of 1s and 0s into a high-resolution digital value

The LIS2DH12 provides up to 12-bit resolution, meaning it divides the measurement range into 4,096 discrete levels. At the ±2g range (default), each LSB (least significant bit) represents 1 mg (one-thousandth of Earth's gravity). So if you're holding the device level, the Z-axis reads approximately +1000 (≈ +1g from gravity).

---

## Why This Part Instead of the MPU-6050

The original design used an MPU-6050 — a 6-axis IMU (3-axis accelerometer + 3-axis gyroscope) at $6.88. The switch to LIS2DH12 was made because:

| Factor | MPU-6050 | LIS2DH12 |
|--------|----------|----------|
| Cost | $6.88 | **$0.46** |
| Axes | 6 (accel + gyro) | 3 (accel only) |
| Package | 4x4mm QFN-24 | **2x2mm LGA-12** |
| Current (low-power) | 10 uA | **2 uA** |
| Current (power-down) | 5 uA | **0.5 uA** |
| Pedometer | No (software only) | **Yes (hardware)** |
| Click detection | No | **Yes (hardware)** |
| Free-fall detection | No | **Yes (hardware)** |
| 6D orientation | No | **Yes (hardware)** |
| FIFO depth | 1024 bytes | 32 samples |
| Gyroscope | Yes | No |

The Dilder has no use for a gyroscope (measuring rotational velocity). The virtual pet doesn't need to know how fast it's spinning. But it does need to count steps, detect taps, and sense orientation — all of which the LIS2DH12 does in hardware, offloading the ESP32 and enabling ultra-low-power operation.

**93% cost reduction** with better functionality for this use case.

---

## Key Specifications

| Parameter | Value |
|-----------|-------|
| Measurement axes | 3 (X, Y, Z) |
| Resolution | 12-bit (high-res), 10-bit (normal), 8-bit (low-power) |
| Measurement range | ±2g, ±4g, ±8g, ±16g (selectable) |
| Sensitivity (±2g) | 1 mg/LSB (high-res mode) |
| Output data rate | 1 Hz to 5.376 kHz |
| Interface | I2C (up to 400 kHz) or SPI (up to 10 MHz) |
| I2C address | 0x18 (SA0=GND) or 0x19 (SA0=VDD) |
| Supply voltage | 1.71V to 3.6V |
| I/O voltage | 1.1V to VDD |
| Current (high-res, 400 Hz) | 185 uA |
| Current (low-power, 1 Hz) | 2 uA |
| Current (power-down) | 0.5 uA |
| Temperature sensor | 8-bit, ±1°C accuracy |
| FIFO | 32 samples (with watermark interrupt) |
| Interrupt pins | 2 (INT1, INT2) — fully programmable |
| Operating temp | -40°C to +85°C |

---

## Built-In Hardware Features

These features run inside the LIS2DH12's embedded logic — no ESP32 processing required:

| Feature | How It Works | Dilder Use |
|---------|-------------|------------|
| **Pedometer** | Counts periodic acceleration patterns matching human gait (configurable thresholds and debounce). Fires an interrupt per step. | Step counting for pet engagement metric |
| **Single-click** | Detects a sharp acceleration spike above a threshold on any axis, with configurable time window. | Tap to pet |
| **Double-click** | Two single-clicks within a configurable time window. | Double-tap to feed |
| **Free-fall** | All three axes simultaneously read near 0g (below threshold for configured duration). | "You dropped me!" reaction |
| **6D Orientation** | Determines which of the 6 device faces is pointing up using gravity vector direction. | Face-down = sleep mode |
| **4D Orientation** | Like 6D but ignores the Z-axis (portrait/landscape only). | Screen rotation if needed |
| **Activity/Inactivity** | Acceleration above/below a threshold for a configured duration. | Sleep when device is idle; wake on motion |
| **Wake-up** | Motion above threshold fires INT1 — can wake ESP32 from deep sleep. | Ultra-low-power idle mode |
| **FIFO watermark** | Buffers up to 32 samples internally, fires interrupt when buffer reaches a set level. | Batch-read samples without polling |

The key advantage: the ESP32 can be in deep sleep (~10 uA) while the LIS2DH12 monitors for motion at just 2 uA. When motion is detected, INT1 fires and wakes the ESP32. Total sleep current: ~12 uA.

---

## Operating Modes and Power

| Mode | ODR | Resolution | Current | Use Case |
|------|-----|------------|---------|----------|
| Power-down | — | — | 0.5 uA | Device completely idle |
| Low-power (1 Hz) | 1 Hz | 8-bit | 2 uA | Motion-detect only (wake trigger) |
| Low-power (10 Hz) | 10 Hz | 8-bit | 3 uA | Step counting while ESP32 sleeps |
| Normal (50 Hz) | 50 Hz | 10-bit | 11 uA | General motion sensing |
| High-res (400 Hz) | 400 Hz | 12-bit | 185 uA | Detailed gesture recognition |

The Dilder will typically run at 10 Hz in low-power mode for step counting, switching to 50 Hz when the device is active for gesture/tap detection.

---

## The I2C Interface

I2C (Inter-Integrated Circuit, pronounced "I-squared-C") is a 2-wire serial bus invented by Philips (now NXP) in 1982. It uses:

- **SDA (Serial Data)** — bidirectional data line
- **SCL (Serial Clock)** — clock line driven by the master (ESP32)

Both lines are pulled HIGH by external resistors (10k in the Dilder) and devices pull them LOW to communicate. This is called **open-drain** — devices can only actively pull low; the resistors pull high when released.

Communication happens in frames:
1. Master sends START condition (SDA goes low while SCL is high)
2. Master sends 7-bit device address (0x18 for LIS2DH12) + read/write bit
3. Slave acknowledges (pulls SDA low for one clock)
4. Data bytes are exchanged (MSB first, 8 bits + ACK)
5. Master sends STOP condition (SDA goes high while SCL is high)

The LIS2DH12 supports up to 400 kHz clock speed ("Fast mode"). At this speed, reading 6 bytes of acceleration data (X, Y, Z as 16-bit values) takes about 180 microseconds.

---

## Pin Connections on Dilder Board

| LIS2DH12 Pin | Pin # | Connect To | Net | Notes |
|--------------|-------|------------|-----|-------|
| VDD_I/O | 1 | 3.3V | 3V3 | I/O voltage level |
| GND | 5, 9, 12 | Ground | GND | All ground pins tied together |
| SDA/SDI | 4 | ESP32 GPIO16 | I2C_SDA | I2C data (10k pull-up) |
| SCL/SPC | 6 | ESP32 GPIO17 | I2C_SCL | I2C clock (10k pull-up) |
| SA0/SDO | 3 | GND | GND | Address bit 0 = 0 → I2C addr 0x18 |
| CS | 7 | 3.3V | 3V3 | HIGH = I2C mode (not SPI) |
| INT1 | 8 | ESP32 GPIO18 | ACCEL_INT1 | Interrupt output (active-high, push-pull) |
| INT2 | 11 | N/C | — | Not used |
| VDD | 10 | 3.3V | 3V3 | Main power supply |
| RES | 2 | N/C | — | Reserved (leave unconnected) |

---

## Application Circuit

```
                  3.3V
                   │
        ┌──[10k]──┤──[10k]──┐       3.3V    3.3V
        │         │          │        │        │
ESP32 GPIO16    GPIO17    GPIO18      │        │
  (SDA)         (SCL)     (INT1)      │        │
        │         │          │        │        │
   .────┤─────────┤──────────┤────────┤────────┤────.
   │   SDA      SCL       INT1     VDD     VDD_IO  │
   │              LIS2DH12TR                        │
   │   SA0=GND  CS=3V3   INT2=NC                   │
   │                                                │
   '────┬──────────────────────────────────────┬────'
        │          GND (pins 5, 9, 12)         │
        └──────────────┬───────────────────────┘
                       │
                      GND
```

**Decoupling:** 100nF ceramic capacitor (C7) between VDD and GND, placed as close to the chip as possible.

---

## Register Map Highlights

| Address | Name | Purpose |
|---------|------|---------|
| 0x0F | WHO_AM_I | Always reads 0x33 — used to verify the chip is alive |
| 0x20 | CTRL_REG1 | Data rate, low-power enable, axis enable |
| 0x22 | CTRL_REG3 | Interrupt 1 source selection |
| 0x23 | CTRL_REG4 | Full-scale range (±2/4/8/16g), high-res mode |
| 0x28-0x2D | OUT_X/Y/Z | Acceleration data (6 bytes, 16-bit per axis) |
| 0x30 | INT1_CFG | Interrupt 1 configuration (6D, 4D, threshold) |
| 0x32 | INT1_SRC | Interrupt 1 source (which event triggered) |
| 0x36 | CLICK_CFG | Click interrupt configuration (single/double, axis) |
| 0x38 | CLICK_SRC | Click interrupt source (which click, which axis) |

**First thing to do after power-up:** Read WHO_AM_I (0x0F). If it returns 0x33, the chip is communicating. If not, check I2C wiring, address, and pull-ups.

---

## History and Background

**STMicroelectronics** is a Franco-Italian semiconductor company (headquarters in Geneva, formed from the merger of SGS Microelettronica of Italy and Thomson Semiconductors of France in 1987). They're one of the world's largest chip makers, particularly strong in:
- MEMS sensors (accelerometers, gyroscopes, pressure sensors)
- Power management (the STM32 MCU family is used in everything from drones to medical devices)
- Automotive electronics

ST pioneered consumer MEMS accelerometers. Their sensors are inside most smartphones — the chip that rotates your screen when you turn your phone sideways is likely an ST accelerometer. They shipped their **10 billionth MEMS sensor** in 2018.

The **LIS2DH12** is part of ST's "femto" accelerometer family, named for the femto-scale (10^-15) capacitance changes they measure. The "TR" suffix means "tape and reel" (packaging format for pick-and-place machines). It's a successor to the popular LIS3DH, with lower power consumption and a smaller package.

**MEMS history in brief:** The concept dates to the 1960s (resonant gate transistor by Westinghouse, 1967). Analog Devices created the first commercial MEMS accelerometer (ADXL50) in 1991 for automotive airbag triggers. Consumer MEMS exploded with the Nintendo Wii (2006, which used an ST accelerometer for motion controls) and the iPhone (2007, which used one for screen rotation).

---

## Datasheet and Sources

- **STMicroelectronics official datasheet:** [LIS2DH12 Datasheet PDF](https://www.st.com/resource/en/datasheet/lis2dh12.pdf)
- **Application note — Pedometer:** [AN5005 — LIS2DH12 Pedometer Functionality](https://www.st.com/resource/en/application_note/an5005-lis2dh12-pedometer-functionality-stmicroelectronics.pdf)
- **Application note — Tilt sensing:** [AN4509 — Tilt Measurement Using ST MEMS](https://www.st.com/resource/en/application_note/an4509-tilt-measurement-using-a-lowg-3axis-accelerometer-stmicroelectronics.pdf)
- **LCSC product page:** [C110926](https://www.lcsc.com/product-detail/C110926.html)
- **Wikipedia — MEMS:** [en.wikipedia.org/wiki/Microelectromechanical_systems](https://en.wikipedia.org/wiki/Microelectromechanical_systems)
- **Wikipedia — Accelerometer:** [en.wikipedia.org/wiki/Accelerometer](https://en.wikipedia.org/wiki/Accelerometer)
- **Analog Devices — MEMS accelerometer tutorial:** [analog.com/en/analog-dialogue/articles/mems-accelerometer-pedometer.html](https://www.analog.com/en/analog-dialogue/articles/mems-accelerometer-pedometer.html)
- **ST MEMS product page:** [st.com/en/mems-and-sensors/accelerometers.html](https://www.st.com/en/mems-and-sensors/accelerometers.html)
