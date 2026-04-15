# DW01A — Battery Protection IC

## Table of Contents

- [Quick Reference](#quick-reference)
- [What Is This Part?](#what-is-this-part)
- [Why Lithium Batteries Need Protection](#why-lithium-batteries-need-protection)
  - [Over-Discharge — The Silent Killer](#over-discharge--the-silent-killer)
  - [Over-Charge — The Fire Hazard](#over-charge--the-fire-hazard)
  - [Short Circuit and Over-Current](#short-circuit-and-over-current)
- [How the DW01A Works](#how-the-dw01a-works)
  - [The Monitoring Circuit](#the-monitoring-circuit)
  - [How It Controls the MOSFETs](#how-it-controls-the-mosfets)
  - [Detection Thresholds and Hysteresis](#detection-thresholds-and-hysteresis)
- [Key Specifications](#key-specifications)
- [Pin Connections on Dilder Board](#pin-connections-on-dilder-board)
- [The DW01A + FS8205A Pair](#the-dw01a--fs8205a-pair)
- [History and Background](#history-and-background)
- [Datasheet and Sources](#datasheet-and-sources)

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Manufacturer** | PUOLOP Microelectronics |
| **Part Number** | DW01A |
| **Function** | Li-Ion/LiPo battery protection IC |
| **Package** | SOT-23-6 (2.9 x 1.6 x 1.1 mm) |
| **LCSC** | [C351410](https://www.lcsc.com/product-detail/C351410.html) |
| **Price (qty 5)** | ~$0.05 |
| **Dilder ref** | U3 |

---

## What Is This Part?

The DW01A is a **battery bodyguard**. It continuously monitors the voltage across a single lithium cell and, when things go wrong, it tells an external MOSFET switch (the FS8205A) to disconnect the battery from the circuit.

It protects against three dangers:
1. **Over-discharge** — battery voltage drops too low (below 2.4V)
2. **Over-charge** — battery voltage rises too high (above 4.3V)
3. **Short-circuit / over-current** — too much current flows (accidental short)

Without this chip, a lithium battery could be discharged to 0V (destroying it permanently) or charged past 4.2V (risking thermal runaway and fire). The DW01A ensures neither happens.

In the Dilder, the DW01A sits between the battery and the rest of the circuit, working with the FS8205A MOSFET to form a protection barrier.

---

## Why Lithium Batteries Need Protection

### Over-Discharge — The Silent Killer

When a lithium cell drops below about 2.5V, its internal chemistry begins to break down:

1. The **copper current collector** on the anode (negative electrode) starts to dissolve into the electrolyte
2. When the battery is later recharged, this dissolved copper plates out as metallic copper dendrites — tiny metal spikes that can pierce the separator
3. The separator is a thin polymer membrane (about 25 micrometers) that keeps the positive and negative electrodes apart. If a dendrite punches through it, the electrodes touch and the cell short-circuits internally

This is particularly insidious because the damage happens silently. The cell might seem fine for weeks after a deep discharge, then suddenly swell or catch fire during the next charge.

Professional battery packs (laptops, phones) always include protection circuits. Bare hobby LiPo cells typically don't — that's why the DW01A exists.

### Over-Charge — The Fire Hazard

Above 4.2V, the cathode material (typically lithium cobalt oxide, LiCoO2) becomes unstable. At 4.3V+:

1. The cathode starts releasing oxygen from its crystal structure
2. This oxygen reacts exothermically with the organic electrolyte
3. The reaction generates heat, which causes more oxygen release — **thermal runaway**
4. The cell swells, ruptures, and can ignite

The TP4056 charger already limits voltage to 4.2V, but the DW01A provides a second layer of defense. Belt and suspenders.

### Short Circuit and Over-Current

If the output is accidentally shorted (dropped on something conductive, damaged trace, etc.), the current through the FS8205A MOSFETs creates a voltage across their on-resistance. The DW01A senses this voltage — if it exceeds 150mV (corresponding to ~3A through the 50mΩ MOSFETs), it immediately disconnects the battery. Response time is about 10 milliseconds.

---

## How the DW01A Works

### The Monitoring Circuit

Inside the DW01A:

1. **Precision voltage comparators** — Two comparators with bandgap-referenced thresholds continuously monitor the battery voltage on the VCC pin:
   - Over-discharge comparator: trips at 2.4V (falling)
   - Over-charge comparator: trips at 4.3V (rising)

2. **Current sense comparator** — Monitors the voltage on the CS pin (connected to the source of the discharge MOSFET). Current flowing through the MOSFET's on-resistance creates a voltage drop. If this exceeds the threshold, it means excessive current.

3. **Logic and timers** — Debounce timers prevent false triggers from brief transients. The over-discharge detection has a ~50ms delay; short-circuit detection has a ~10ms delay.

4. **Gate drivers** — Two outputs (OD and OC) drive the gates of the external MOSFET pair.

### How It Controls the MOSFETs

The DW01A has two control outputs:

- **OD (Over-Discharge)** — Controls the discharge MOSFET. Goes LOW to block discharge current when battery is too low.
- **OC (Over-Charge)** — Controls the charge MOSFET. Goes LOW to block charge current when battery is too high.

In normal operation, both OD and OC are HIGH, keeping both MOSFETs turned on, and current flows freely in both directions.

### Detection Thresholds and Hysteresis

Hysteresis prevents oscillation. If the over-discharge threshold were a single voltage, the circuit would rapidly switch on and off as the battery hovered around the threshold. Hysteresis adds a gap:

| Protection | Trip Voltage | Release Voltage | Hysteresis |
|-----------|-------------|-----------------|------------|
| Over-discharge | 2.4V (falling) | 3.0V (rising) | 0.6V |
| Over-charge | 4.3V (rising) | 4.15V (falling) | 0.15V |
| Over-current | 150mV (on CS pin) | 100mV | 50mV |

**Over-discharge recovery example:** The battery drops to 2.4V → DW01A disconnects load → battery voltage immediately bounces up (no more load current) → but DW01A doesn't reconnect until voltage reaches 3.0V. This usually requires plugging in a charger.

---

## Key Specifications

| Parameter | Value |
|-----------|-------|
| Over-discharge detection | 2.4V (±50mV) |
| Over-discharge release | 3.0V (±100mV) |
| Over-charge detection | 4.3V (±50mV) |
| Over-charge release | 4.15V (±50mV) |
| Over-current (short-circuit) | 150mV on CS pin |
| Short-circuit response time | ~10 ms |
| Quiescent current | 3 uA typical |
| Operating voltage | 2.0V to 5.5V |
| Package | SOT-23-6 |
| Operating temp | -40°C to +85°C |

---

## Pin Connections on Dilder Board

| DW01A Pin | Pin # | Connect To | Net | Notes |
|-----------|-------|------------|-----|-------|
| OD | 1 | FS8205A Gate 1 (pin 2) | OD | Over-discharge MOSFET control |
| CS | 2 | FS8205A Source 1 (pin 1) | CS_DRAIN | Current sense input |
| OC | 3 | FS8205A Gate 2 (pin 5) | OC | Over-charge MOSFET control |
| TD | 4 | VCC (tied to battery+) | VBAT | Delay pin — tied to VCC per datasheet |
| VCC | 5 | Battery positive terminal | VBAT | Battery voltage monitoring |
| GND | 6 | FS8205A Source 1 (pin 1) | GND | Circuit ground reference |

---

## The DW01A + FS8205A Pair

The DW01A **always** works with an external dual MOSFET — in our case, the FS8205A. This pairing is so common it's practically a single component in the hobby world. You'll see it on virtually every LiPo protection board.

See [fs8205a.md](fs8205a.md) for the MOSFET side of this circuit and how the two chips work together.

```
Battery +  ────────────────────────── VCC (DW01A)
              │                         │
              │                        TD
              │
              ├── FS8205A Drain (common) ── Load+
              │
              │   FS8205A Gate2 ◄──── OC (DW01A)
              │   FS8205A Source2
              │   FS8205A Source1 ──── CS (DW01A)
              │   FS8205A Gate1 ◄──── OD (DW01A)
              │
Battery -  ────────────────── GND ──── GND (DW01A)
```

---

## History and Background

The DW01A is manufactured by **Shenzhen PUOLOP Microelectronics**, one of many Chinese semiconductor companies producing battery protection ICs. The design is functionally equivalent to the **Seiko S-8241** (one of the first single-cell protection ICs, from the 1990s) and the **Fortune Semi FS312F**.

Battery protection ICs became essential when lithium batteries moved from controlled industrial applications into consumer devices in the early 1990s. Sony's first commercial lithium-ion battery (1991) included built-in protection circuitry. As lithium batteries became commoditized, the protection circuit was often separated from the cell to reduce cost — which created the market for standalone protection ICs.

The DW01A + FS8205A combination has become the de facto standard for low-cost single-cell protection. You'll find it inside most AliExpress/eBay "18650 charger boards," inside cheap power banks, and inside most open-source hardware projects that use lithium batteries. Its 3 uA quiescent current means the protection circuit itself barely drains the battery.

---

## Datasheet and Sources

- **LCSC product page:** [C351410](https://www.lcsc.com/product-detail/C351410.html)
- **DW01A datasheet (English):** Available on LCSC product page (click "Datasheet" tab)
- **Fortune Semi FS312F (equivalent):** [FS312F Datasheet](https://datasheet.lcsc.com/lcsc/2206241830_FORTUNE-SEMI-SHENZHEN-FS312F-G_C82736.pdf)
- **Battery University — Lithium safety:** [batteryuniversity.com/article/bu-304a](https://batteryuniversity.com/article/bu-304a)
- **Wikipedia — Lithium-ion battery safety:** [en.wikipedia.org/wiki/Lithium-ion_battery#Safety](https://en.wikipedia.org/wiki/Lithium-ion_battery#Safety)
