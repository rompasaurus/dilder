# Green LED (0603) — Charge Complete Indicator

## Table of Contents

- [Quick Reference](#quick-reference)
- [What Is This Part?](#what-is-this-part)
- [Key Specifications](#key-specifications)
- [Circuit on Dilder Board](#circuit-on-dilder-board)
- [Why Green Has Higher Forward Voltage Than Red](#why-green-has-higher-forward-voltage-than-red)
- [Datasheet and Sources](#datasheet-and-sources)

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Manufacturer** | Everlight Electronics |
| **Part Number** | 19-217/GHC-YR1S2/3T |
| **Function** | Green LED — indicates battery is fully charged |
| **Package** | 0603 (1.6 x 0.8 mm) |
| **LCSC** | [C72043](https://www.lcsc.com/product-detail/C72043.html) |
| **Price (qty 5)** | ~$0.01 |
| **Dilder ref** | D3 |

---

## What Is This Part?

A small green LED that lights up when the battery is fully charged. Connected to the TP4056's STDBY pin — when charging completes, the TP4056 pulls STDBY low, turning this LED on.

Together with the red LED (D2), they form a simple two-color status indicator:
- **Red on, green off** → charging
- **Red off, green on** → charge complete
- **Both off** → no battery or standby

See [led-red.md](led-red.md) for a full explanation of how LEDs work, including the physics of light emission and why current-limiting resistors are needed.

---

## Key Specifications

| Parameter | Value |
|-----------|-------|
| Emitted color | Emerald green (518 nm dominant wavelength) |
| Forward voltage | 3.0V to 3.4V typical |
| Forward current (max) | 20 mA |
| Forward current (Dilder) | ~0.3 mA |
| Luminous intensity | 25-63 mcd (at 20mA) |
| Viewing angle | 130° |
| Package | 0603 (1.6 x 0.8 x 0.6 mm) |

---

## Circuit on Dilder Board

```
  3.3V ──[R3 = 1kΩ]──►|── Green LED (D3) ──── TP4056 STDBY (pin 6)
                       anode         cathode

  TP4056 STDBY = LOW  → current flows → LED ON  (charge complete)
  TP4056 STDBY = HIGH → no current   → LED OFF (charging or no battery)
```

**Note on current:** With a 3.0V forward voltage, the current is (3.3 - 3.0) / 1000 = **0.3 mA**. This is very low but still visible for a green LED in a handheld device held close to the eyes. If brighter output is needed, a lower resistor value (470Ω) could increase current to ~0.6 mA.

---

## Why Green Has Higher Forward Voltage Than Red

Green photons have more energy than red photons (shorter wavelength = higher frequency = higher energy via E = hf). The semiconductor must have a wider bandgap to emit green light:

- **Red LED** (AlGaInP): ~2.0V forward voltage, 625nm wavelength
- **Green LED** (InGaN): ~3.2V forward voltage, 518nm wavelength

InGaN (Indium Gallium Nitride) is a III-V compound semiconductor that was difficult to grow as high-quality crystals until the 1990s. Shuji Nakamura's breakthrough at Nichia Corporation (Japan) in 1993 cracked the problem, enabling bright blue and green LEDs. He won the 2014 Nobel Prize in Physics for this work.

The higher Vf of the green LED means less voltage headroom from the 3.3V supply (only 0.3V across the resistor), resulting in very low current. This is why the green LED is dimmer than the red one in this circuit.

---

## Datasheet and Sources

- **LCSC product page:** [C72043](https://www.lcsc.com/product-detail/C72043.html)
- **Everlight Electronics:** [everlight.com](https://www.everlight.com)
- **Wikipedia — Shuji Nakamura (Nobel Prize for blue/green LED):** [en.wikipedia.org/wiki/Shuji_Nakamura](https://en.wikipedia.org/wiki/Shuji_Nakamura)
