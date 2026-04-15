# USB-C 16-Pin Connector — Programming & Charging Input

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Manufacturer** | SHOU HAN |
| **Part Number** | TYPE-C-16PIN-2MD(073) |
| **Function** | USB Type-C receptacle for power input and USB data |
| **Package** | SMD, mid-mount |
| **LCSC** | [C2765186](https://www.lcsc.com/product-detail/C2765186.html) |
| **Price (qty 5)** | ~$0.10 |
| **Dilder ref** | J1 |

## Key Specifications

| Parameter | Value |
|-----------|-------|
| Type | USB Type-C 2.0 receptacle |
| Pins | 16 (subset — not full 24-pin) |
| Rated current | 5A max |
| Contact resistance | 30 mOhm max |
| Durability | 10,000 mating cycles |

## Required External Components

| Component | Value | Purpose |
|-----------|-------|---------|
| R8, R9 | 5.1k to GND | CC1/CC2 pull-down — tells USB host this is a device drawing power |
| R6, R7 | 27 Ohm series | USB D+/D- series resistors (signal integrity) |

## Datasheet

- **LCSC product page:** [C2765186](https://www.lcsc.com/product-detail/C2765186.html) (datasheet available inline)
