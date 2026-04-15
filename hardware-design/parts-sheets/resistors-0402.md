# 0402 Resistors — Passive Component Guide

## Table of Contents

- [Quick Reference](#quick-reference)
- [What Is a Resistor?](#what-is-a-resistor)
  - [Ohm's Law — The Foundation](#ohms-law--the-foundation)
  - [What Physically Creates Resistance](#what-physically-creates-resistance)
- [How SMD Resistors Are Made](#how-smd-resistors-are-made)
  - [Thick Film vs Thin Film](#thick-film-vs-thin-film)
  - [The 0402 Package](#the-0402-package)
- [Resistors on the Dilder Board](#resistors-on-the-dilder-board)
- [How Each Resistor Value Is Used](#how-each-resistor-value-is-used)
  - [R1 — 1.2k (TP4056 Charge Current)](#r1--12k-tp4056-charge-current)
  - [R2, R3 — 1k (LED Current Limiting)](#r2-r3--1k-led-current-limiting)
  - [R4, R5 — 10k (I2C Pull-Up)](#r4-r5--10k-i2c-pull-up)
  - [R8, R9 — 5.1k (USB-C CC Pull-Down)](#r8-r9--51k-usb-c-cc-pull-down)
  - [R10 — 10k (ESP32 EN Pull-Up)](#r10--10k-esp32-en-pull-up)
- [Tolerance and Why It Matters](#tolerance-and-why-it-matters)
- [History and Background](#history-and-background)
- [Datasheet and Sources](#datasheet-and-sources)

---

## Quick Reference

| Ref | Value | LCSC | Purpose | Qty |
|-----|-------|------|---------|-----|
| R1 | 1.2kΩ | [C25752](https://www.lcsc.com/product-detail/C25752.html) | TP4056 charge current setting | 1 |
| R2 | 1kΩ | [C25585](https://www.lcsc.com/product-detail/C25585.html) | Red LED current limiting | 1 |
| R3 | 1kΩ | [C25585](https://www.lcsc.com/product-detail/C25585.html) | Green LED current limiting | 1 |
| R4 | 10kΩ | [C25744](https://www.lcsc.com/product-detail/C25744.html) | I2C SDA pull-up | 1 |
| R5 | 10kΩ | [C25744](https://www.lcsc.com/product-detail/C25744.html) | I2C SCL pull-up | 1 |
| R8 | 5.1kΩ | — | USB CC1 pull-down | 1 |
| R9 | 5.1kΩ | — | USB CC2 pull-down | 1 |
| R10 | 10kΩ | [C25744](https://www.lcsc.com/product-detail/C25744.html) | ESP32 EN pin pull-up | 1 |

**All are 0402 package (1.0 x 0.5 mm), 1% tolerance, 1/16W rating.**

---

## What Is a Resistor?

A resistor opposes the flow of electrical current. That's it. It converts electrical energy into heat as current passes through it.

### Ohm's Law — The Foundation

The most important equation in electronics:

**V = I × R**

- **V** = Voltage across the resistor (Volts)
- **I** = Current through the resistor (Amps)
- **R** = Resistance (Ohms, symbol Ω)

Rearranged: **I = V / R** (current equals voltage divided by resistance)

This means a resistor with a fixed value creates a predictable relationship between voltage and current. This is used throughout the Dilder for:
- Setting specific currents (charge current, LED current)
- Creating voltage references (pull-ups, pull-downs)
- Biasing signals to specific voltage levels

### What Physically Creates Resistance

In a metal, electrons flow freely through a lattice of atoms. Resistance comes from **collisions** — electrons bumping into atoms, impurities, and grain boundaries. Each collision converts some of the electron's kinetic energy into heat (lattice vibrations = thermal energy).

Materials with tightly-packed crystal structures and few free electrons (like carbon) have high resistance. Materials with abundant free electrons and regular crystal structures (like copper) have low resistance. Resistor manufacturers exploit this by using specific **resistive materials** (ruthenium oxide, nickel-chromium alloys) to achieve precise resistance values.

---

## How SMD Resistors Are Made

### Thick Film vs Thin Film

**Thick film** (most common, including the Dilder's resistors):
1. Start with a ceramic substrate (alumina, Al₂O₃)
2. Screen-print a paste of ruthenium oxide (RuO₂) mixed with glass frit onto the substrate
3. Fire in a kiln at ~850°C — the glass melts and bonds the resistive layer to the ceramic
4. Laser-trim the resistive layer to achieve the target value (a laser cuts a thin groove, increasing resistance until it hits the target)
5. Add metal end caps (tin-plated nickel over silver) for soldering

**Thin film** (higher precision, more expensive):
1. Sputter a thin layer of nickel-chromium (NiCr) onto the ceramic substrate in a vacuum
2. Pattern the resistive layer using photolithography
3. Laser-trim for precision
4. Better temperature stability and tighter tolerance (0.1% vs 1%)

The Dilder uses thick film resistors — 1% tolerance is adequate for all applications here.

### The 0402 Package

"0402" refers to the package dimensions in imperial units: **0.04" x 0.02"** (1.0mm x 0.5mm). This is one of the smallest resistor packages commonly used in hobby projects.

For scale:
- 0402 = 1.0 x 0.5 mm (grain of sand)
- 0603 = 1.6 x 0.8 mm (grain of coarse sand)
- 0805 = 2.0 x 1.25 mm (sesame seed)
- 1206 = 3.2 x 1.6 mm (grain of rice)

0402 parts are standard for JLCPCB assembly. They're too small for hand soldering without magnification, but pick-and-place machines handle them easily.

---

## Resistors on the Dilder Board

```
Power Section:
  R1 (1.2k) ── TP4056 PROG → GND        Sets 1A charge current
  R2 (1k)   ── 3.3V → Red LED → TP4056   Limits charge LED current
  R3 (1k)   ── 3.3V → Green LED → TP4056  Limits standby LED current

USB Section:
  R8 (5.1k) ── USB CC1 → GND             Identifies as USB device
  R9 (5.1k) ── USB CC2 → GND             Identifies as USB device

MCU Section:
  R10 (10k) ── 3.3V → ESP32 EN pin       Keeps ESP32 enabled

I2C Bus:
  R4 (10k)  ── 3.3V → I2C SDA line       Pull-up for I2C data
  R5 (10k)  ── 3.3V → I2C SCL line       Pull-up for I2C clock
```

---

## How Each Resistor Value Is Used

### R1 — 1.2k (TP4056 Charge Current)

The TP4056 sets its charge current based on the resistor between its PROG pin and ground:

**Icharge = 1200V / RPROG = 1200 / 1200 = 1.0A**

This is the only resistor where the exact value critically affects performance. A 10% error (1.08k or 1.32k) would change the charge current to ~1.1A or ~0.9A — both acceptable for the battery, but the 1% tolerance resistor keeps it close to 1.0A.

### R2, R3 — 1k (LED Current Limiting)

For the red LED (2.0V Vf): **I = (3.3 - 2.0) / 1000 = 1.3 mA**
For the green LED (3.0V Vf): **I = (3.3 - 3.0) / 1000 = 0.3 mA**

Both currents are well below the 20mA LED maximum. The LEDs are dim but visible for status indicators in a handheld device.

### R4, R5 — 10k (I2C Pull-Up)

I2C is an open-drain bus — devices can only pull the line LOW. Pull-up resistors return the line to HIGH when no device is pulling it down. The value is a compromise:

- **Too low (1k):** Faster rise times (good for high-speed I2C) but higher current consumption when the line is pulled LOW (I = 3.3V / 1kΩ = 3.3mA per line)
- **Too high (100k):** Very low current but slow rise times — the RC time constant of the pull-up and bus capacitance limits the switching speed
- **10k (sweet spot):** Current when LOW = 0.33mA per line. Rise time adequate for 400 kHz I2C with short traces.

### R8, R9 — 5.1k (USB-C CC Pull-Down)

The USB-C specification requires a **5.1k ±10%** pull-down on each CC pin for a device that wants to receive power. This exact value tells the USB host "I'm a basic USB device, please provide default power." Any other value would be misinterpreted or ignored by the host.

### R10 — 10k (ESP32 EN Pull-Up)

The ESP32-S3's EN (Enable) pin has a weak internal pull-up, but an external 10k provides more robust noise immunity. If EN goes LOW due to noise, the module resets. The 10k pull-up ensures EN stays HIGH under normal conditions while still allowing it to be pulled LOW intentionally (e.g., by a reset button or supervisor IC, if added later).

---

## Tolerance and Why It Matters

Tolerance is how far the actual resistance can deviate from the labeled value:

| Tolerance | Marking | Actual range for "10kΩ" |
|-----------|---------|------------------------|
| ±5% | Gold band (J) | 9.5k - 10.5k |
| ±1% | Brown band (F) | 9.9k - 10.1k |
| ±0.1% | Purple band (B) | 9.99k - 10.01k |

The Dilder uses 1% resistors throughout. This is the standard for modern SMD resistors — 5% and 1% cost the same in 0402 packages, so there's no reason to use the less precise option.

---

## History and Background

The resistor is the oldest and simplest electronic component. Georg Simon Ohm published his law in 1827, establishing the mathematical relationship between voltage, current, and resistance.

Early resistors were coils of wire (wirewound) — literally a known length of resistive wire wound around a ceramic core. Carbon composition resistors (a mix of carbon powder and ceramic binder) dominated from the 1930s to the 1970s. Modern surface-mount thick film resistors, using screen-printed ruthenium oxide, were developed in the 1980s and have since become the most widely manufactured electronic component in the world. An estimated **trillions** of SMD resistors are produced annually.

---

## Datasheet and Sources

- **LCSC — 1.2k 0402:** [C25752](https://www.lcsc.com/product-detail/C25752.html)
- **LCSC — 1k 0402:** [C25585](https://www.lcsc.com/product-detail/C25585.html)
- **LCSC — 10k 0402:** [C25744](https://www.lcsc.com/product-detail/C25744.html)
- **Wikipedia — Resistor:** [en.wikipedia.org/wiki/Resistor](https://en.wikipedia.org/wiki/Resistor)
- **Wikipedia — Ohm's Law:** [en.wikipedia.org/wiki/Ohm%27s_law](https://en.wikipedia.org/wiki/Ohm%27s_law)
- **Vishay — Thick Film Chip Resistor Guide:** [vishay.com/en/resistors-fixed/thick-film-technology](https://www.vishay.com/en/resistors-fixed/thick-film-technology/)
