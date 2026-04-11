# Hardware Enclosure Design — Planning Document

A step-by-step plan for designing and prototyping the Dilder's 3D-printed enclosure, from component dimensions through CAD modelling to a printed prototype in hand.

---

## Table of Contents

1. [Component Dimensions Reference](#1-component-dimensions-reference)
2. [Button Selection and Cost Breakdown](#2-button-selection-and-cost-breakdown)
3. [Concept Images](#3-concept-images)
4. [Enclosure Design Constraints](#4-enclosure-design-constraints)
5. [CAD Software Recommendation](#5-cad-software-recommendation)
6. [3D Modelling Plan — Step by Step](#6-3d-modelling-plan--step-by-step)
7. [3D Printing Services and Estimated Costs](#7-3d-printing-services-and-estimated-costs)
8. [Prototype Timeline](#8-prototype-timeline)

---

## 1. Component Dimensions Reference

Every internal component must be accounted for when modelling the case. These are the dimensions that drive the enclosure design.

### Raspberry Pi Pico W

| Spec | Value |
|------|-------|
| Board dimensions | 51 x 21 x 3.9 mm |
| Mounting holes | 2x M2.5, 4.8 mm from each end, 11.4 mm apart |
| USB connector protrusion | ~2 mm beyond board edge |
| Header pins (if soldered) | ~2.5 mm below board, ~8 mm above |
| Weight | ~3 g |

### Waveshare 2.13" e-Paper HAT V3

| Spec | Value |
|------|-------|
| HAT board dimensions | 65 x 30.2 mm |
| Display glass outline | 59.2 x 29.2 x 1.05 mm |
| Active pixel area | 48.55 x 23.71 mm (250 x 122 px) |
| FPC cable side | Short edge (top of board) |
| Mounting holes | 4x M2.5 at corners |
| Total stack height (board + glass) | ~4.5 mm |

### Internal Stack Height Estimate

| Layer | Thickness |
|-------|-----------|
| Bottom shell wall | 1.5 mm |
| Pico W board | 3.9 mm |
| Clearance / wiring | 2–3 mm |
| Display board | ~1.6 mm |
| Display glass | 1.05 mm |
| Top shell wall + bezel | 1.5 mm |
| **Total estimated** | **~12–14 mm** |

> The v2 concept specified 19 mm depth, which leaves comfortable room for wiring and a future battery bay.

---

## 2. Button Selection and Cost Breakdown

The Dilder uses 5 buttons: 3 navigation (left / select / right) and 2 action (A / B). All buttons wire to Pico W GPIO with internal pull-ups — no external components needed.

### Recommended: Adafruit Colorful Round Tactile Button Assortment

| Detail | Value |
|--------|-------|
| Product | Adafruit #1009 — Colorful Round Tactile Button Switch Assortment |
| Source | [adafruit.com/product/1009](https://www.adafruit.com/product/1009) |
| Price | $5.95 for 15 buttons (5 colours x 3 each) |
| Per-button cost | ~$0.40 |
| Dimensions | 12 x 12 mm base, ~12 mm total height with cap |
| Mount type | Through-hole PCB (4-pin DIP) |
| Cap colours | Blue, grey, yellow, green, red |

**Why this option:** Colour-coded caps let you visually differentiate navigation and action buttons. The snap-on caps protrude cleanly through rectangular cutouts in the 3D-printed shell. 15 buttons in the pack means 10 spares. Best balance of price, tactile feel, and enclosure compatibility.

**Suggested colour assignment:**
- Navigation (3): grey (left / select / right)
- Action (2): blue (A / B)

### Alternative Options Considered

| Option | Source | Price | Dimensions | Notes |
|--------|--------|-------|------------|-------|
| Adafruit 12 mm tact switch, no cap (#1119) | adafruit.com/product/1119 | $2.50 / 10 | 12 x 12 x 6 mm | Cheap, but no cap — bare nub is uncomfortable for a handheld. Add your own 3D-printed caps. |
| Adafruit 6 mm extra-tall tact switch (#1490) | adafruit.com/product/1490 | $2.50 / 10 | 6 x 6 x 12 mm | Small footprint fits tight layouts. Tall plunger pokes through case. Can feel wobbly without support. |
| Adafruit 6 mm standard tact switch (#367) | adafruit.com/product/367 | $2.50 / 20 | 6 x 6 x 5 mm | Cheapest option. Too small and short for comfortable handheld use — breadboard prototyping only. |
| SparkFun 12 mm momentary switch | sparkfun.com | ~$0.55 each | 12 x 12 mm | Sold individually. Good quality, but more expensive per unit than Adafruit packs. |
| Illuminated tact switches (Amazon, 20-pack) | Amazon | ~$10–12 / 20 | 12 x 12 x 7.3 mm | Built-in LEDs, but draws extra current — poor fit for a battery-powered e-ink device. |

### Total Button Cost

| Item | Cost |
|------|------|
| Adafruit #1009 (15-pack, recommended) | $5.95 |
| Shipping (Adafruit, US) | ~$3–5 |
| **Total** | **~$9–11** |

---

## 3. Concept Images

The existing concept renders define the target form factor. Both are dimension-accurate SVGs at 4:1 scale.

### v1 — Initial Rough Layout

![Prototype v1](../docs/concepts/prototype-v1.svg)

Source file: [`docs/concepts/prototype-v1.svg`](../docs/concepts/prototype-v1.svg)

### v2 — Dimension-Accurate Revision (Current Reference)

![Prototype v2](../docs/concepts/prototype-v2.svg)

Source file: [`docs/concepts/prototype-v2.svg`](../docs/concepts/prototype-v2.svg)

**v2 key measurements:**

| Metric | Value |
|--------|-------|
| Case outer dimensions | 88 x 34 x 19 mm |
| Display window cutout | 57 x 27 mm |
| Button cluster width | ~22 mm |
| Button centre-to-centre | ~10 mm |
| Display face coverage | 51% |
| Button face coverage | 12% |

> The v2 concept was designed around the Pi Zero + HAT form factor (65 x 30 mm board). The Pico W (51 x 21 mm) is smaller, so the case width could shrink by ~10 mm if we drop the HAT board from the design. However, the display glass (59.2 x 29.2 mm) is still the space-limiting factor, so the overall dimensions will stay similar.

---

## 4. Enclosure Design Constraints

These constraints must be satisfied by the CAD model:

1. **Two-piece shell** — top half and bottom half, horizontal split at the case midpoint
2. **Display cutout** — 57 x 27 mm window with 1 mm lip overlap around the display glass
3. **Button apertures** — 5x rectangular holes sized for 12 mm button caps to protrude through the top shell
4. **USB access** — micro-USB slot on the short edge for power and programming
5. **Assembly** — 4x M2 heat-set inserts in bottom shell, M2 x 6 mm screws from top shell
6. **Wall thickness** — 1.5 mm minimum for FDM printability
7. **Internal standoffs** — raised posts to seat the Pico W and display board at correct heights
8. **Battery bay** — reserved cavity in the bottom shell (not populated in prototype, but modelled for future use)
9. **Ventilation** — slot vents on the back panel

---

## 5. CAD Software Recommendation

### Primary Recommendation: Autodesk Fusion 360 (Free for Personal Use)

| Detail | Value |
|--------|-------|
| Cost | Free (personal / hobbyist licence) |
| Platform | Windows, macOS (cloud-based project storage) |
| Learning curve | Moderate — extensive YouTube tutorial ecosystem |
| Strengths | Parametric modelling, integrated simulation, PCB import, huge community |
| Export formats | STL, STEP, 3MF, OBJ |

**Why Fusion 360:** Parametric modelling means every dimension is a variable — change wall thickness once and the entire model updates. You can import the Pico W and display board as reference bodies to design the case around them. The personal licence is free and covers everything needed for this project.

### Alternatives

| Software | Cost | Best For | Drawback |
|----------|------|----------|----------|
| FreeCAD | Free (open source) | Full parametric modelling without any licence restrictions | Steeper learning curve, occasional UI quirks |
| TinkerCAD | Free (browser) | Quick first prototype, absolute beginners | Not parametric — tedious to iterate dimensions |
| Onshape Free | Free tier | Professional CAD in the browser, real-time collaboration | Free plan = all designs are public, 10-document limit |
| SolidWorks | ~$3,995/year | Industry standard for product design | Overkill and expensive for a hobby project |

### Recommended Workflow

1. **Quick shape exploration** — sketch the case in TinkerCAD to confirm proportions (1–2 hours)
2. **Parametric model** — rebuild in Fusion 360 with proper constraints and variables (4–8 hours)
3. **Export STL** — generate print-ready files from Fusion 360

---

## 6. 3D Modelling Plan — Step by Step

### Step 1: Set Up the Fusion 360 Project

- Create a new project called "Dilder Enclosure"
- Define user parameters for all key dimensions (wall thickness, display cutout, button spacing, screw post diameter)
- Import or model the Pico W board as a reference body (51 x 21 x 3.9 mm)
- Import or model the display board as a reference body (65 x 30.2 mm)

### Step 2: Model the Bottom Shell

- Sketch the outer profile (88 x 34 mm rounded rectangle, 2 mm corner radius)
- Extrude to half the case depth (~9.5 mm)
- Shell the interior (1.5 mm wall thickness)
- Add internal standoffs for Pico W mounting (2x posts, M2.5 through-holes)
- Add internal standoffs for display board mounting (4x posts, M2.5 through-holes)
- Model the battery bay cavity (reserved, unfilled for prototype)
- Add 4x M2 heat-set insert holes at corners
- Cut the micro-USB access slot on the short edge

### Step 3: Model the Top Shell

- Mirror the bottom shell outer profile
- Extrude to remaining case depth (~9.5 mm)
- Shell the interior (1.5 mm wall)
- Cut the display window (57 x 27 mm, with 1 mm lip)
- Cut 5x button apertures (12.5 x 12.5 mm square holes for cap protrusion)
- Add alignment pins / slots to register with bottom shell
- Add 4x M2 screw clearance holes at corners
- Add slot vents on the back face

### Step 4: Test Fit and Iterate

- Use Fusion 360's interference check to verify no component collisions
- Check button cap protrusion height (caps should sit ~1 mm above the case surface)
- Verify USB port alignment with Pico W board position
- Export cross-section views to confirm internal clearances

### Step 5: Export for Printing

- Export top shell and bottom shell as separate STL files
- Set mesh resolution to "high" (max deviation 0.01 mm)
- Orient parts for printing: flat face down, no supports needed if designed correctly
- Generate a 3MF file as an alternative (preserves colour and material data)

---

## 7. 3D Printing Services and Estimated Costs

### Service Comparison

The Dilder case is small (~88 x 34 x 19 mm, two-part shell). Material usage is roughly 15–25 g total.

| Service | Base Part Cost (PLA) | Base Part Cost (PETG) | Shipping to US | Turnaround | Best For |
|---------|---------------------|-----------------------|----------------|------------|----------|
| **JLC3DP (JLCPCB)** | $1–3 | $2–5 | $5–15 (from China) | 7–15 days total | Cheapest option, especially bundled with PCB orders |
| **Craftcloud (All3DP)** | $8–20 | $10–25 | Included | 3–7 days (domestic) | Price comparison across 150+ manufacturers |
| **PCBWay** | $25 minimum | $25 minimum | $5–15 (from China) | 8–14 days total | Good quality, but $25 minimum hurts small orders |
| **Xometry** | $15–30 | $20–40 | Included (US) | 3–5 days | Fastest US-based option |
| **Shapeways** | — | — | $5–10 | 7–12 days | Best for SLS nylon (final quality), not FDM |

### Material Recommendations by Phase

| Phase | Material | Why | Est. Cost (Printed + Shipped) |
|-------|----------|-----|-------------------------------|
| Early prototype | PLA | Cheapest, fastest to iterate, good detail | $8–15 (JLC3DP) |
| Functional prototype | PETG | Tougher, slight flex, better heat resistance | $15–25 (Craftcloud) |
| Final build | SLS Nylon | Professional feel, no visible layer lines, very durable | $25–40 (Shapeways or JLC3DP) |

### Estimated Total Cost for First Prototype

| Item | Cost |
|------|------|
| 3D print — 2-part PLA case (JLC3DP) | ~$3 |
| Shipping (JLC3DP standard) | ~$8 |
| M2 heat-set inserts (50-pack, Amazon) | ~$6 |
| M2 x 6 mm screws (50-pack, Amazon) | ~$5 |
| **Total for first printed case** | **~$22** |

> If you already have an order pending at JLCPCB for PCBs, adding the 3D print to the same shipment eliminates the separate shipping cost.

### Recommended Service: JLC3DP

**For the first prototype, use JLC3DP (jlc3dp.com).** Upload the STL files, select PLA, and order. The part cost is under $5. Shipping from China takes 7–15 days but is the most cost-effective path to a physical prototype. For faster iteration (3–5 days), use Craftcloud to find a domestic US printer.

---

## 8. Prototype Timeline

| Step | Task | Tools | Est. Effort |
|------|------|-------|-------------|
| 1 | Install Fusion 360, complete an enclosure tutorial | Fusion 360 | 1 session |
| 2 | Model the bottom shell with standoffs and screw posts | Fusion 360 | 1–2 sessions |
| 3 | Model the top shell with display cutout and button holes | Fusion 360 | 1–2 sessions |
| 4 | Test fit check — interference analysis, cross-sections | Fusion 360 | 1 session |
| 5 | Export STL, upload to JLC3DP or Craftcloud, order print | Browser | 30 minutes |
| 6 | Receive print, test-fit components, document issues | Physical | After delivery |
| 7 | Revise model based on fit test, order v2 print | Fusion 360 + printer | Repeat as needed |

---

## Next Steps

1. Order the Adafruit #1009 button assortment ($5.95)
2. Install Fusion 360 (free personal licence)
3. Complete one beginner enclosure tutorial in Fusion 360
4. Begin modelling the bottom shell using the dimensions in this document
5. Upload and order the first PLA prototype print
