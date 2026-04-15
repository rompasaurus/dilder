---
date: 2026-04-15
authors:
  - rompasaurus
categories:
  - Hardware
  - PCB Design
  - Manufacturing
slug: pcb-fab-pricing-research
---

# PCB Fabrication Pricing — Where to Build the Board

With the Dilder PCB design taking shape, it was time to figure out where to actually get it made. I spent a session researching five different PCB fabrication and assembly houses, comparing pricing for our specific board (45x80mm, 4-layer, 27 components, SMT assembly).

<!-- more -->

## The Contenders

I compared **JLCPCB**, **PCBWay**, **OSH Park**, **Aisler**, and **Seeed Fusion**. The price differences are dramatic — from $35 for 5 boards at JLCPCB to over $150 at OSH Park for the same order.

## JLCPCB Wins (For Now)

For a small prototype run of 5 boards with SMT assembly, JLCPCB comes out ahead:

- **PCB fabrication:** ~$2 for 5 boards (yes, really)
- **SMT assembly:** ~$8 setup + component costs
- **Components:** ~$10-11 per board (the ESP32-S3 module and MPU-6050 are the big-ticket items)
- **Total:** ~$35-50 for 5 assembled boards

The catch is shipping from China (7-14 days). If you're in Europe, Aisler is interesting — more expensive per board but no customs delays or 19% VAT surprise.

## Open-Source Reference Designs

While researching, I also found and catalogued 7 open-source KiCad reference designs that match parts of the Dilder's design. These range from an RP2040 minimal board to an ESP32-S3 e-paper breakout (the Ducky Board) to OpenTama — a literal open-source Tamagotchi. Each one is now in our `hardware-design/reference-boards/` directory with documentation.

## Component Visual BOM

I also pulled product photos for every component on the board from LCSC. There's something satisfying about seeing the actual tiny parts that will make up the device — especially the 0402 capacitors that are literally 1mm long.

The full pricing breakdown, provider comparison, and reference board analysis are in the [PCB Assembly & Prototyping](../../docs/design/pcb-assembly-and-prototyping.md) doc.
