# SKRHABE010 — Alps Alpine 5-Way SMD Joystick

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Manufacturer** | Alps Alpine |
| **Part Number** | SKRHABE010 |
| **Function** | 5-direction SMD navigation switch (UP/DOWN/LEFT/RIGHT + center push) |
| **Package** | SMD, 7.4 x 7.5 x 1.8mm |
| **LCSC** | [C139794](https://www.lcsc.com/product-detail/C139794.html) |
| **Price (qty 5)** | ~$0.38 |
| **Dilder ref** | SW1 |

## Key Specifications

| Parameter | Value |
|-----------|-------|
| Directions | 4-way rocker + center push (5 total) |
| Contact type | Momentary, normally open |
| Operating force | 2.0N (direction), 3.0N (center push) |
| Contact resistance | 1.0 Ohm max |
| Rated voltage | 12V DC |
| Rated current | 50mA |
| Mechanical life | 100,000 cycles |
| Operating temp | -20C to +70C |

## Pin Connections (Dilder Board)

Each direction is a separate switch that connects to the common ground pin when activated:

| Switch Pin | ESP32-S3 GPIO | Direction |
|------------|---------------|-----------|
| UP | GPIO4 | Up |
| DOWN | GPIO5 | Down |
| LEFT | GPIO6 | Left |
| RIGHT | GPIO7 | Right |
| CENTER | GPIO8 | Center push |
| COM | GND | Common ground |

Software config: Internal pull-ups enabled, active LOW (pressed = 0).

## Replaces

This SMD joystick replaces the DollaTek 5-way through-hole module used in the breadboard prototype. Same 5 directions, same active-LOW logic, but in a surface-mount package suitable for PCB assembly.

## Datasheet

- **LCSC product page:** [C139794](https://www.lcsc.com/product-detail/C139794.html) (datasheet available inline)
- **Alps Alpine product page:** [SKRHABE010](https://www.mouser.com/ProductDetail/Alps-Alpine/SKRHABE010)
