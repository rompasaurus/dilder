# USB-C 16-Pin Connector — Programming & Charging Input

## Table of Contents

- [Quick Reference](#quick-reference)
- [What Is This Part?](#what-is-this-part)
- [How USB-C Works](#how-usb-c-works)
  - [The Reversible Connector](#the-reversible-connector)
  - [The CC Pins — Orientation and Power Negotiation](#the-cc-pins--orientation-and-power-negotiation)
  - [Why 16 Pins Instead of 24](#why-16-pins-instead-of-24)
  - [USB 2.0 Data on a USB-C Connector](#usb-20-data-on-a-usb-c-connector)
- [Key Specifications](#key-specifications)
- [Required External Components](#required-external-components)
- [Pin Connections on Dilder Board](#pin-connections-on-dilder-board)
- [History and Background](#history-and-background)
- [Datasheet and Sources](#datasheet-and-sources)

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Manufacturer** | SHOU HAN |
| **Part Number** | TYPE-C-16PIN-2MD(073) |
| **Function** | USB Type-C receptacle — power input + USB 2.0 data |
| **Package** | SMD mid-mount |
| **LCSC** | [C2765186](https://www.lcsc.com/product-detail/C2765186.html) |
| **Price (qty 5)** | ~$0.10 |
| **Dilder ref** | J1 |

---

## What Is This Part?

The USB-C connector on the Dilder serves two functions:
1. **Power input** — delivers 5V from a USB charger or computer to charge the battery (via TP4056) and power the device
2. **Data connection** — the ESP32-S3's native USB-OTG provides a serial console for firmware upload and debugging

It's a 16-pin subset of the full 24-pin USB-C specification. The missing 8 pins are for USB 3.x SuperSpeed signals (TX/RX differential pairs) which the Dilder doesn't use — it only needs USB 2.0 speed (12 Mbps).

---

## How USB-C Works

### The Reversible Connector

USB-C's headline feature is that you can plug it in either way. This is achieved by duplicating every signal contact on both sides of the connector:

```
  ┌──────────────── USB-C plug face ────────────────┐
  │  A12 A11 A10 A9 A8 A7 A6 A5 A4 A3 A2 A1       │
  │                                                  │
  │  B1  B2  B3  B4 B5 B6 B7 B8 B9 B10 B11 B12    │
  └──────────────────────────────────────────────────┘
```

Row A and Row B are mirror images. When you flip the cable, what was Row A becomes Row B and vice versa. The device figures out which orientation the cable is in using the CC pins.

### The CC Pins — Orientation and Power Negotiation

The **CC pins (Configuration Channel)** are the most important innovation in USB-C. Each side of the connector has one CC pin: **CC1** (pin A5) and **CC2** (pin B5).

**How orientation detection works:**
1. A USB-C cable connects CC on one row and VCONN on the other
2. The device has 5.1k pull-down resistors on both CC1 and CC2
3. The host (charger or computer) has pull-up resistors on its CC pins
4. When the cable is plugged in, one CC pin sees the host's pull-up (through the cable), the other sees nothing
5. The device reads which CC pin has the pull-up to determine cable orientation

**How power negotiation works:**
The host's pull-up resistor value tells the device how much current is available:
- 56k pull-up → 500mA (USB 2.0 default)
- 22k pull-up → 1.5A
- 10k pull-up → 3.0A

The Dilder's 5.1k pull-downs on CC1 and CC2 tell the host "I'm a USB device that wants power." Without these resistors, a USB-C host won't provide any power at all — this is a common cause of "my device won't charge from USB-C."

### Why 16 Pins Instead of 24

A full USB-C connector has 24 pins:
- 4 power pins (VBUS × 2, GND × 2)
- 4 USB 2.0 data pins (D+/D- on each row)
- 2 CC pins
- 2 SBU pins (sideband use — for alt modes like DisplayPort)
- 8 USB 3.x SuperSpeed pins (TX1+/-, RX1+/-, TX2+/-, RX2+/-)
- 2 VCONN pins (power for active cables)

The 16-pin variant omits the 8 SuperSpeed pins. Since the ESP32-S3 only supports USB 2.0 (12 Mbps), those pins would be unconnected anyway. The 16-pin connector is smaller, cheaper, and easier to solder.

### USB 2.0 Data on a USB-C Connector

USB 2.0 uses a differential pair: **D+** and **D-**. The data is encoded using NRZI (Non-Return-to-Zero Inverted) signaling at 12 MHz. Both D+ and D- carry the same signal but inverted — the receiver looks at the difference between them, which cancels out common-mode noise (noise that affects both wires equally).

In USB-C, D+ and D- appear on both Row A and Row B. Since the cable only connects one row's data pins (based on orientation), the device sees data on exactly one pair regardless of plug orientation.

The ESP32-S3's GPIO19 (D-) and GPIO20 (D+) connect directly to the USB-C data pins — no series resistors needed because the ESP32-S3's USB PHY has integrated termination.

---

## Key Specifications

| Parameter | Value |
|-----------|-------|
| Connector type | USB Type-C 2.0 receptacle |
| Pin count | 16 (omits SuperSpeed pins) |
| Mounting | SMD mid-mount |
| Rated current | 5A max (power pins) |
| Rated voltage | 20V max |
| Contact resistance | 30 mΩ max |
| Insulation resistance | 100 MΩ min |
| Durability | 10,000 mating cycles |
| Operating temp | -30°C to +80°C |

---

## Required External Components

| Component | Value | Ref | Purpose |
|-----------|-------|-----|---------|
| R8 | 5.1k to GND | R8 | CC1 pull-down — identifies as USB device |
| R9 | 5.1k to GND | R9 | CC2 pull-down — identifies as USB device |

**Note:** The ESP32-S3 has native USB with integrated termination, so no series resistors are needed on D+/D-. The old RP2040 design used 27Ω series resistors (R6/R7), but these were removed in the ESP32-S3 version.

---

## Pin Connections on Dilder Board

| USB-C Pin | Name | Connect To | Net |
|-----------|------|------------|-----|
| A4 / B4 | VBUS | SS34 anode (D1) | VBUS |
| A1 / B1 / A12 / B12 | GND | Ground plane | GND |
| A5 | CC1 | 5.1k to GND (R8) | CC1 |
| B5 | CC2 | 5.1k to GND (R9) | CC2 |
| A6 / B6 | D+ | ESP32 GPIO20 | USB_DP |
| A7 / B7 | D- | ESP32 GPIO19 | USB_DM |
| S1 (shield) | Shield | GND | GND |

---

## History and Background

USB Type-C was developed by the **USB Implementers Forum (USB-IF)** and published in August 2014. It was created to address the frustration of USB-A and USB-B's non-reversible connectors and to unify the fragmented world of charging cables.

Key milestones:
- **1996:** USB 1.0 — USB-A/B connectors, 12 Mbps
- **2000:** USB 2.0 — 480 Mbps, Mini-USB
- **2008:** USB 3.0 — 5 Gbps, Micro-USB
- **2014:** USB Type-C connector standard — reversible, supports up to 240W power delivery
- **2019:** EU began push to mandate USB-C for all devices (enacted 2023)
- **2024:** Apple's iPhone switches to USB-C (from Lightning)

The USB-C connector was designed by a team at Intel and was partly inspired by Apple's Lightning connector (2012), which was also reversible. The USB-IF took the reversibility concept and added negotiation capabilities (CC pins), alt modes (DisplayPort, Thunderbolt over USB-C), and power delivery up to 240W.

The 10-cent connector used in the Dilder is a simplified version made by Chinese manufacturers for cost-sensitive applications. It's electrically identical to Apple's or Intel's connectors for USB 2.0 use.

---

## Datasheet and Sources

- **LCSC product page:** [C2765186](https://www.lcsc.com/product-detail/C2765186.html)
- **USB Type-C specification (USB-IF):** [usb.org/document-library/usb-type-cr-cable-and-connector-specification](https://www.usb.org/document-library/usb-type-cr-cable-and-connector-specification)
- **Wikipedia — USB-C:** [en.wikipedia.org/wiki/USB-C](https://en.wikipedia.org/wiki/USB-C)
- **Wikipedia — USB:** [en.wikipedia.org/wiki/USB](https://en.wikipedia.org/wiki/USB)
- **Texas Instruments — USB Type-C basics:** [ti.com/lit/an/slly017/slly017.pdf](https://www.ti.com/lit/an/slly017/slly017.pdf)
