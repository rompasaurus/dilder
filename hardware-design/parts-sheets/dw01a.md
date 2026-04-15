# DW01A — Battery Protection IC

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Manufacturer** | PUOLOP |
| **Part Number** | DW01A |
| **Function** | Li-Ion/LiPo battery protection (over-discharge, over-charge, short-circuit) |
| **Package** | SOT-23-6 |
| **LCSC** | [C351410](https://www.lcsc.com/product-detail/C351410.html) |
| **Price (qty 5)** | ~$0.05 |
| **Dilder ref** | U3 |

## Key Specifications

| Parameter | Value |
|-----------|-------|
| Over-discharge detection | 2.4V (releases at 3.0V) |
| Over-charge detection | 4.3V (releases at 4.15V) |
| Over-current detection | 150mV across FS8205A Rds(on) |
| Short-circuit detection | 1.35V across sense resistor |
| Quiescent current | 3 uA typical |
| Operating voltage | 2.0V to 5.5V |

## How It Works

The DW01A monitors the battery voltage and controls the FS8205A dual MOSFET to disconnect the battery in dangerous conditions:

- **Over-discharge:** If battery drops below 2.4V, the DW01A turns off the discharge MOSFET → device powers off, preventing deep discharge damage
- **Over-charge:** If battery exceeds 4.3V, the DW01A turns off the charge MOSFET → stops charging
- **Short-circuit:** If excessive current flows (e.g. shorted output), the DW01A cuts power immediately

## Pin Connections (Dilder Board)

| DW01A Pin | Pin # | Connect To | Notes |
|-----------|-------|------------|-------|
| OD | 1 | FS8205A Gate 1 | Over-discharge control |
| CS | 2 | FS8205A source (sense) | Current sense input |
| OC | 3 | FS8205A Gate 2 | Over-charge control |
| TD | 4 | N/C or delay cap | Timing delay (optional) |
| VCC | 5 | Battery + | Battery voltage monitoring |
| GND | 6 | FS8205A source | Circuit ground |

## Works With

This IC is always paired with the **FS8205A** dual MOSFET — see [fs8205a.md](fs8205a.md). Together they form the complete battery protection circuit. This same DW01A + FS8205A combination is used in the [OpenTama virtual pet](../reference-boards/opentama-virtual-pet/) reference design.

## Datasheet

- **LCSC product page:** [C351410](https://www.lcsc.com/product-detail/C351410.html) (datasheet available inline)
