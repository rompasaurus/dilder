# Red LED (0805) — Charging Indicator

## Table of Contents

- [Quick Reference](#quick-reference)
- [What Is This Part?](#what-is-this-part)
- [How LEDs Work](#how-leds-work)
  - [The Light-Emitting PN Junction](#the-light-emitting-pn-junction)
  - [Why Different Colors Have Different Voltages](#why-different-colors-have-different-voltages)
  - [Current Limiting — Why You Need a Resistor](#current-limiting--why-you-need-a-resistor)
- [Key Specifications](#key-specifications)
- [Circuit on Dilder Board](#circuit-on-dilder-board)
- [Datasheet and Sources](#datasheet-and-sources)

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Manufacturer** | Foshan NationStar |
| **Part Number** | NCD0805R1 |
| **Function** | Red LED — indicates battery is charging |
| **Package** | 0805 (2.0 x 1.25 mm) |
| **LCSC** | [C84256](https://www.lcsc.com/product-detail/C84256.html) |
| **Price (qty 5)** | ~$0.01 |
| **Dilder ref** | D2 |

---

## What Is This Part?

A tiny red LED that lights up when the battery is charging. It's connected to the TP4056's CHRG output pin — when charging is in progress, the TP4056 pulls CHRG low, which allows current to flow through the LED, turning it on.

---

## How LEDs Work

### The Light-Emitting PN Junction

An LED (Light-Emitting Diode) is a semiconductor diode that emits light when current flows through it. Like all diodes, it has a PN junction — a boundary between P-type and N-type semiconductor material.

When forward voltage is applied, electrons from the N-side cross the junction and recombine with holes on the P-side. Each recombination releases energy. In a normal silicon diode, this energy is released as heat (phonons). In an LED, the semiconductor material is chosen so the energy is released as a **photon** (a particle of light).

The color of the light depends on the **energy gap** (bandgap) of the semiconductor material. Higher bandgap = higher photon energy = shorter wavelength = bluer color.

### Why Different Colors Have Different Voltages

The forward voltage of an LED directly reflects the photon energy being emitted. Einstein's equation: **E = hf** (energy = Planck's constant × frequency). Higher frequency (bluer light) = higher energy = higher forward voltage.

| Color | Wavelength | Forward Voltage | Semiconductor Material |
|-------|-----------|-----------------|----------------------|
| Infrared | >800 nm | 1.1-1.5V | GaAs |
| **Red** | **625 nm** | **1.8-2.2V** | **AlGaInP** |
| Orange | 590 nm | 2.0-2.4V | AlGaInP |
| Green | 520 nm | 3.0-3.4V | InGaN |
| Blue | 470 nm | 3.0-3.6V | InGaN |
| White | Broad spectrum | 3.0-3.6V | InGaN + phosphor |

Red LEDs are the cheapest and simplest because they use aluminum gallium indium phosphide (AlGaInP), a well-established and inexpensive material system.

### Current Limiting — Why You Need a Resistor

An LED has very low resistance when forward-biased — if connected directly to 3.3V, it would try to draw unlimited current and burn out instantly. A series resistor limits the current.

For the red LED: **R = (Vsupply - Vf) / If = (3.3 - 2.0) / 0.001 = 1300Ω ≈ 1kΩ**

At 1kΩ: I = (3.3 - 2.0) / 1000 = **1.3 mA**. This is enough for a visible indicator LED in a handheld device. The LED is rated for 20mA max, but 1-2mA is plenty bright for a status indicator.

---

## Key Specifications

| Parameter | Value |
|-----------|-------|
| Emitted color | Red (625 nm dominant wavelength) |
| Forward voltage | 1.8V to 2.2V typical |
| Forward current (max) | 20 mA |
| Forward current (Dilder) | ~1.3 mA |
| Luminous intensity | 60-150 mcd (at 20mA) |
| Viewing angle | 120° |
| Package | 0805 (2.0 x 1.25 x 0.8 mm) |

---

## Circuit on Dilder Board

```
  3.3V ──[R2 = 1kΩ]──►|── Red LED (D2) ──── TP4056 CHRG (pin 7)
                       anode        cathode
  
  TP4056 CHRG = LOW  → current flows → LED ON  (charging)
  TP4056 CHRG = HIGH → no current   → LED OFF (not charging)
```

The TP4056's CHRG pin is an open-drain output — it can only pull LOW (sink current). When LOW, current flows from 3.3V through the resistor, through the LED, into the CHRG pin to ground. When HIGH (floating), no path exists and the LED is off.

---

## Datasheet and Sources

- **LCSC product page:** [C84256](https://www.lcsc.com/product-detail/C84256.html)
- **Wikipedia — Light-emitting diode:** [en.wikipedia.org/wiki/Light-emitting_diode](https://en.wikipedia.org/wiki/Light-emitting_diode)
- **LED physics tutorial:** [electronics-tutorials.ws/diode/diode_8.html](https://www.electronics-tutorials.ws/diode/diode_8.html)
