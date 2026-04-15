# JST PH 2-Pin — Battery Connector

## Table of Contents

- [Quick Reference](#quick-reference)
- [What Is This Part?](#what-is-this-part)
- [The JST Connector Family](#the-jst-connector-family)
  - [Why JST PH 2.0mm?](#why-jst-ph-20mm)
  - [Common JST Types Compared](#common-jst-types-compared)
- [Key Specifications](#key-specifications)
- [Pin Connections](#pin-connections)
- [Polarity Warning](#polarity-warning)
- [History and Background](#history-and-background)
- [Datasheet and Sources](#datasheet-and-sources)

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Manufacturer** | JST (Japan Solderless Terminals) |
| **Part Number** | S2B-PH-SM4-TB (SMD right-angle) |
| **Function** | 2-pin connector for LiPo battery |
| **Pitch** | 2.0 mm |
| **LCSC** | [C131337](https://www.lcsc.com/product-detail/C131337.html) |
| **Price (qty 5)** | ~$0.03 |
| **Dilder ref** | J2 |

---

## What Is This Part?

A small 2-pin connector that the LiPo battery plugs into. It provides a secure, disconnectable connection between the battery and the PCB. You can unplug the battery for storage, replacement, or shipping (lithium batteries must often be disconnected for postal regulations).

The connector has a locking tab that clicks when the plug is fully inserted, preventing accidental disconnection from vibration or handling.

---

## The JST Connector Family

### Why JST PH 2.0mm?

JST PH 2.0mm pitch is the **de facto standard** for single-cell LiPo batteries in the hobby electronics world. If you buy a LiPo battery from Adafruit, SparkFun, or most AliExpress sellers, it comes with a JST PH plug pre-soldered to the battery's leads.

The Dilder's breadboard prototype used a battery with a Molex 1.25mm pitch connector. The PCB specifies JST PH 2.0mm instead because:
1. Far more battery options available with this connector
2. Easier to hand-solder (larger pitch)
3. Higher current rating (2A vs 1A for Molex 1.25mm)
4. More robust mechanically

### Common JST Types Compared

JST makes dozens of connector series. The most common in hobby electronics:

| Series | Pitch | Current Rating | Common Use |
|--------|-------|---------------|------------|
| **JST PH** | 2.0 mm | 2A | LiPo batteries, sensors |
| JST SH | 1.0 mm | 1A | Stemma QT/Qwiic I2C, small sensors |
| JST XH | 2.5 mm | 3A | Multi-cell battery packs |
| JST ZH | 1.5 mm | 1A | Compact sensors |
| Molex PicoBlade | 1.25 mm | 1A | Small batteries |

The Dilder uses JST PH for the battery (J2) and JST SH for the e-paper display connector (J3).

---

## Key Specifications

| Parameter | Value |
|-----------|-------|
| Pitch | 2.0 mm |
| Number of pins | 2 |
| Rated current | 2A |
| Rated voltage | 100V AC/DC |
| Contact resistance | 20 mΩ max |
| Insulation resistance | 1000 MΩ min |
| Mating cycles | 30 cycles minimum |
| Wire gauge | AWG 24-30 |
| Operating temp | -25°C to +85°C |
| Mounting | SMD right-angle (horizontal) |

---

## Pin Connections

| Pin | Function | Wire Color (standard) | Net |
|-----|----------|----------------------|-----|
| 1 | Battery + | Red | BAT_PLUS |
| 2 | Battery - | Black | GND |

---

## Polarity Warning

**There is no universal polarity standard for JST PH battery connectors.** While most hobby suppliers (Adafruit, SparkFun) use Pin 1 = Positive, some cheap batteries from AliExpress reverse the polarity. Always verify with a multimeter before connecting a new battery.

Connecting a battery with reversed polarity will bypass the DW01A protection circuit (it monitors voltage in one direction only) and feed reverse voltage into the TP4056 and LDO, likely destroying them.

---

## History and Background

**JST (Japan Solderless Terminals Mfg. Co., Ltd.)** was founded in 1957 in Osaka, Japan. The name reflects their original product — wire terminals that could be crimped instead of soldered (hence "solderless"). Today JST is one of the world's largest connector manufacturers with factories in 23 countries.

JST connectors are everywhere: inside laptops (battery packs use JST XH), inside drones (LiPo balance leads use JST XH), in IoT devices (Adafruit's STEMMA uses JST PH), and in automotive wiring harnesses. The PH series was introduced in the 1990s and has become so ubiquitous that "JST connector" in the hobby world almost always means JST PH 2.0mm.

---

## Datasheet and Sources

- **LCSC product page:** [C131337](https://www.lcsc.com/product-detail/C131337.html)
- **JST PH series catalog:** [jst-mfg.com/product/detail_e.php?series=199](http://www.jst-mfg.com/product/detail_e.php?series=199)
- **Wikipedia — JST connector:** [en.wikipedia.org/wiki/JST_connector](https://en.wikipedia.org/wiki/JST_connector)
- **Adafruit JST PH guide:** [learn.adafruit.com/jst-connector-types](https://learn.adafruit.com/understanding-the-jst-connector-ecosystem)
