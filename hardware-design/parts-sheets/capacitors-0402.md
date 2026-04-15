# 0402 Capacitors — Passive Component Guide

## Table of Contents

- [Quick Reference](#quick-reference)
- [What Is a Capacitor?](#what-is-a-capacitor)
  - [The Water Tank Analogy](#the-water-tank-analogy)
  - [How Capacitance Works Physically](#how-capacitance-works-physically)
  - [Charge, Voltage, and Capacitance](#charge-voltage-and-capacitance)
- [How MLCC Capacitors Are Made](#how-mlcc-capacitors-are-made)
  - [Multi-Layer Ceramic Construction](#multi-layer-ceramic-construction)
  - [Dielectric Materials (X5R, X7R, C0G)](#dielectric-materials-x5r-x7r-c0g)
- [Why Every IC Needs Decoupling Capacitors](#why-every-ic-needs-decoupling-capacitors)
  - [The Noise Problem](#the-noise-problem)
  - [How a Decoupling Cap Fixes It](#how-a-decoupling-cap-fixes-it)
  - [The 100nF + 10uF Combination](#the-100nf--10uf-combination)
- [Capacitors on the Dilder Board](#capacitors-on-the-dilder-board)
- [Key Specifications](#key-specifications)
- [History and Background](#history-and-background)
- [Datasheet and Sources](#datasheet-and-sources)

---

## Quick Reference

| Ref | Value | LCSC | Purpose | Qty |
|-----|-------|------|---------|-----|
| C3 | 100nF | [C14663](https://www.lcsc.com/product-detail/C14663.html) | ESP32-S3 decoupling (high-freq) | 1 |
| C4 | 10uF | [C19702](https://www.lcsc.com/product-detail/C19702.html) | ESP32-S3 bulk bypass (low-freq) | 1 |
| C5 | 10uF | [C19702](https://www.lcsc.com/product-detail/C19702.html) | AMS1117 LDO input | 1 |
| C6 | 10uF | [C19702](https://www.lcsc.com/product-detail/C19702.html) | AMS1117 LDO output (stability) | 1 |
| C7 | 100nF | [C14663](https://www.lcsc.com/product-detail/C14663.html) | LIS2DH12 VDD decoupling | 1 |
| C9 | 100nF | [C14663](https://www.lcsc.com/product-detail/C14663.html) | LIS2DH12 REGOUT bypass | 1 |

**All are 0402 package (1.0 x 0.5 mm), 10% tolerance, 16V or 25V rating.**

---

## What Is a Capacitor?

A capacitor stores electrical energy in an electric field. It's like a tiny rechargeable battery that charges and discharges in nanoseconds instead of hours.

### The Water Tank Analogy

Imagine a small water tank connected to a pipe:
- **Filling the tank** = charging the capacitor (storing energy)
- **The tank's volume** = capacitance (how much charge it can hold)
- **Water pressure** = voltage (higher charge = higher voltage)
- **Emptying the tank** = discharging (releasing stored energy)

A big tank (large capacitance) holds more water and takes longer to fill/empty. A small tank (small capacitance) responds quickly but holds less.

### How Capacitance Works Physically

A capacitor is two conductive plates separated by an insulator (called a **dielectric**):

```
  ┌──────────┐  ← Metal plate 1 (connected to pin 1)
  │ DIELECTRIC │  ← Insulating material (ceramic in MLCC)
  └──────────┘  ← Metal plate 2 (connected to pin 2)
```

When you apply voltage, electrons accumulate on one plate and are repelled from the other. This creates an electric field across the dielectric that stores energy. The amount of charge stored depends on:

**C = ε × A / d**

- **C** = capacitance (Farads)
- **ε** = permittivity of the dielectric (how well it concentrates the electric field)
- **A** = plate area (bigger plates = more capacitance)
- **d** = distance between plates (thinner dielectric = more capacitance)

### Charge, Voltage, and Capacitance

**Q = C × V**

- **Q** = charge stored (Coulombs)
- **C** = capacitance (Farads)
- **V** = voltage across the capacitor

One **Farad** is enormous — a 1F capacitor at 1V stores 1 Coulomb of charge. The capacitors on the Dilder are measured in:
- **nF** (nanofarads) = 10⁻⁹ F — the 100nF decoupling caps
- **uF** (microfarads) = 10⁻⁶ F — the 10uF bulk caps

---

## How MLCC Capacitors Are Made

### Multi-Layer Ceramic Construction

MLCC stands for **Multi-Layer Ceramic Capacitor**. To get useful capacitance in a tiny 1mm package, manufacturers stack hundreds of alternating metal and ceramic layers:

```
  Metal end cap ──┐    ┌── Metal end cap
                  │    │
     ══════════════════════  Metal electrode (Ni)
     ──────────────────────  Ceramic dielectric
     ══════════════════════  Metal electrode (Ni)
     ──────────────────────  Ceramic dielectric
     ══════════════════════  Metal electrode (Ni)
     ──────────────────────  Ceramic dielectric
     ══════════════════════  Metal electrode (Ni)
          ... hundreds of layers ...
```

Each layer pair acts as a small capacitor. Stacking them in parallel multiplies the total capacitance. A modern 10uF 0402 capacitor may have 200-400 layers, each just a few micrometers thick.

The manufacturing process:
1. Mix ceramic powder (barium titanate, BaTiO₃) with binders to form thin sheets ("green tape")
2. Screen-print nickel paste electrode patterns onto the sheets
3. Stack the sheets (alternating electrode orientations)
4. Cut into individual components
5. Fire at ~1200°C — the ceramic sinters into a dense solid
6. Apply metal end caps (tin over nickel over copper)

### Dielectric Materials (X5R, X7R, C0G)

The ceramic material determines the capacitor's behavior:

| Type | Material | Temp Range | Capacitance Change | Best For |
|------|----------|------------|-------------------|----------|
| **X5R** | Barium titanate (BaTiO₃) | -55°C to +85°C | ±15% over temp | Bulk bypass (10uF) |
| **X7R** | Modified BaTiO₃ | -55°C to +125°C | ±15% over temp | General decoupling (100nF) |
| **C0G/NP0** | Calcium zirconate | -55°C to +125°C | ±30 ppm/°C | Precision timing, filters |

The Dilder's 100nF caps are likely X7R and the 10uF caps are X5R. Both are adequate for decoupling and bypass applications where exact capacitance isn't critical.

**Important: MLCC capacitance decreases with applied voltage (DC bias effect).** A 10uF capacitor rated at 16V may only provide 5-7uF at 3.3V with X5R dielectric. This is usually fine for decoupling because even reduced capacitance provides adequate charge storage.

---

## Why Every IC Needs Decoupling Capacitors

### The Noise Problem

When a digital IC switches its outputs, it briefly draws a surge of current from the power supply. The ESP32-S3 has millions of transistors switching at 240 MHz — each transition creates a tiny current spike.

These spikes travel through the power traces, which have small but non-zero inductance (L) and resistance (R). The voltage drop across this trace inductance is:

**V = L × (dI/dt)**

With fast current changes (dI/dt is huge at 240 MHz), even a few nanohenries of trace inductance can create millivolt or even volt-level noise on the power rail. This noise can cause:
- Logic errors (a 1 flips to a 0)
- ADC reading errors
- Radio interference
- Random crashes

### How a Decoupling Cap Fixes It

A capacitor placed directly next to the IC's power pins acts as a **local charge reservoir**. When the IC needs a burst of current, the capacitor supplies it instantly — the current doesn't need to travel through the long, inductive power trace from the regulator.

```
         Long trace (has inductance)
  LDO ──────╫╫╫╫╫╫╫╫╫╫╫╫╫──┬── VDD pin of IC
                              │
                             [C] ← Decoupling cap (100nF)
                              │
  GND ────────────────────────┴── GND pin of IC
```

The capacitor charges slowly from the LDO (through the inductive trace — that's fine, it's a steady DC current) and discharges quickly to the IC (through a very short, low-inductance trace — the cap is right next to the IC).

### The 100nF + 10uF Combination

Different capacitor values handle different frequency ranges:

- **100nF (C3, C7, C9)** — handles high-frequency noise (1-100 MHz). Small capacitors have low parasitic inductance (ESL) so they can charge/discharge very quickly. The 100nF cap is the "first responder" for fast switching transients.

- **10uF (C4, C5, C6)** — handles low-frequency noise (DC to 1 MHz). Large capacitors store more charge and can sustain current for longer periods (microseconds). The 10uF cap handles sustained current surges like WiFi transmit bursts.

Together, they provide decoupling across the full frequency range. This "100nF + 10uF" pairing is a universal best practice — you'll find it next to virtually every digital IC on any well-designed PCB.

---

## Capacitors on the Dilder Board

```
ESP32-S3 (U1):
  C3 (100nF) ── 3.3V to GND  [close to module pin 2]  High-freq decoupling
  C4 (10uF)  ── 3.3V to GND  [near module]            Bulk bypass

AMS1117-3.3 LDO (U4):
  C5 (10uF)  ── VBAT to GND  [close to VIN pin]       Input filtering
  C6 (10uF)  ── 3.3V to GND  [close to VOUT pin]      Output stability (REQUIRED)

LIS2DH12TR (U5):
  C7 (100nF) ── 3.3V to GND  [close to VDD pin]       High-freq decoupling
  C9 (100nF) ── REGOUT to GND [close to REGOUT pin]    Internal regulator bypass
```

**Placement rule:** Decoupling capacitors must be as close as possible to the IC's power pins. Every millimeter of trace between the cap and the pin adds inductance that reduces the cap's effectiveness. In the Dilder PCB, caps are placed within 2-3mm of their associated IC.

---

## Key Specifications

### 100nF (C3, C7, C9)

| Parameter | Value |
|-----------|-------|
| Capacitance | 100 nF (0.1 uF) |
| Tolerance | ±10% |
| Voltage rating | 16V or 25V |
| Dielectric | X7R |
| Package | 0402 (1.0 x 0.5 mm) |
| ESR | < 100 mΩ |
| LCSC | [C14663](https://www.lcsc.com/product-detail/C14663.html) |

### 10uF (C4, C5, C6)

| Parameter | Value |
|-----------|-------|
| Capacitance | 10 uF |
| Tolerance | ±20% |
| Voltage rating | 16V or 25V |
| Dielectric | X5R |
| Package | 0402 (1.0 x 0.5 mm) |
| ESR | < 10 mΩ |
| LCSC | [C19702](https://www.lcsc.com/product-detail/C19702.html) |

---

## History and Background

The capacitor is one of the oldest electronic components. The **Leyden jar** (1746) — a glass jar coated inside and outside with metal foil — was the first practical capacitor, used to store static electricity for parlor tricks and early experiments.

Michael Faraday (for whom the unit of capacitance "Farad" is named) studied capacitors extensively in the 1830s and established the relationship between charge, voltage, and capacitance.

Ceramic capacitors emerged in the 1930s using barium titanate (BaTiO₃), discovered to have an extraordinarily high dielectric constant (ε ≈ 1000-10000, vs ε ≈ 1 for air). This allows huge capacitance in tiny packages. The MLCC (multi-layer ceramic capacitor) was developed by American Laminates in the 1960s and perfected by Japanese manufacturers (Murata, TDK, Taiyo Yuden) through the 1970s-1990s.

Today, **trillions** of MLCC capacitors are manufactured annually. Murata alone produces 40+ billion per year. A single smartphone contains 800-1000 MLCC capacitors. They are the most manufactured component in the history of electronics.

---

## Datasheet and Sources

- **LCSC — 100nF 0402:** [C14663](https://www.lcsc.com/product-detail/C14663.html)
- **LCSC — 10uF 0402:** [C19702](https://www.lcsc.com/product-detail/C19702.html)
- **Wikipedia — Capacitor:** [en.wikipedia.org/wiki/Capacitor](https://en.wikipedia.org/wiki/Capacitor)
- **Wikipedia — Ceramic capacitor:** [en.wikipedia.org/wiki/Ceramic_capacitor](https://en.wikipedia.org/wiki/Ceramic_capacitor)
- **Murata — MLCC FAQ:** [murata.com/en-global/support/faqs/capacitor](https://www.murata.com/en-global/support/faqs/capacitor)
- **TI — Decoupling Capacitor Basics:** [ti.com/lit/an/slva747/slva747.pdf](https://www.ti.com/lit/an/slva747/slva747.pdf)
- **Analog Devices — Decoupling Techniques:** [analog.com/en/analog-dialogue/articles/decoupling-techniques.html](https://www.analog.com/en/analog-dialogue/articles/decoupling-techniques.html)
