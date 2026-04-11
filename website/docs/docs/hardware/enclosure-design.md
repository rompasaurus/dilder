# Enclosure Design

Design specifications and constraints for the Dilder 3D-printed case.

> **Note:** Enclosure design is deferred until Phase 5/6, when the final board (Pico W or Pi Zero) is confirmed. The current prototype lives on a breadboard. These specs are initial concepts based on the Pi Zero + HAT form factor and will be revised.

---

## Form Factor

**Style:** Landscape rectangle — "iPod Nano" layout with display dominating the left face and a compact button cluster on the right.

**Concept renders:**

### v1 — Initial rough layout

![Prototype v1 concept render](../../assets/images/prototype-v1.svg)

### v2 — Dimension-accurate revision (current reference)

![Prototype v2 concept render](../../assets/images/prototype-v2.svg)

---

## v2 Dimensions

| Metric | Value |
|--------|-------|
| Case outer dimensions | 88 × 34 × 19mm |
| Display window cutout | 57 × 27mm |
| Active pixel area | 48.55 × 23.71mm (250×122 px) |
| Button cluster width | ~22mm |
| Button center-to-center | ~10mm |
| Display face coverage | 51% |
| Button face coverage | 12% |
| Display-to-button ratio | 4.3 : 1 |
| Estimated weight | ~45g bare / ~65g with battery |
| Size reference | Slightly wider than a credit card, ~2/3 the height |

---

## Component Dimensions

Sourced from official datasheets and measured hardware.

| Component | Dimension | Source |
|-----------|-----------|--------|
| Pico W board | 51 × 21 × 3.9mm | Pico W datasheet |
| Pi Zero board (future) | 65 × 30 × 5mm | Official Raspberry Pi spec |
| Waveshare HAT board | 65 × 30.2mm | Waveshare specification |
| Display glass outline | 59.2 × 29.2 × 1.05mm | V3 specification PDF |
| Display active area | 48.55 × 23.71mm | V3 specification PDF |
| Dot pitch | 0.194 × 0.194mm | V3 specification PDF |
| 6×6mm tactile button | 6 × 6 × 4.3–9.5mm | Standard spec |

!!! note "Pico W is smaller"
    The Pico W (51 × 21mm) is significantly smaller than the Pi Zero (65 × 30mm). If the final build uses the Pico W, the enclosure could be more compact — but the display board (65 × 30.2mm) is still the space-limiting factor.

---

## Design Constraints

These constraints must be satisfied by any enclosure design:

1. **Display cutout:** 57 × 27mm with 1mm case lip overlap around display glass
2. **Button holes:** 5× circular apertures, ~7mm diameter, d-pad cross pattern with ~10mm center-to-center
3. **USB access:** Micro-USB slot on edge (power and data during development)
4. **Assembly:** 2-piece shell (top + bottom), 4× M2 corner screws
5. **Shell seam:** Horizontal split at case midpoint
6. **Battery bay:** Reserved space for LiPo battery (later phase)
7. **Ventilation:** Slot vents on back panel

---

## Material Options

| Material | Pros | Cons |
|----------|------|------|
| PLA | Easy to print, good detail, cheap | Brittle, warps in heat |
| PETG | Tougher than PLA, better heat resistance | Slightly harder to print, less detail |
| ABS | Good mechanical properties | Warps badly without enclosure, fumes |
| ASA | Weather resistant, UV stable | Expensive, similar print difficulty to ABS |

**Recommendation for prototype:** PLA. Fast to iterate, lowest barrier to getting prints done. Switch to PETG or ASA for a final build.

---

## Future Revisions

- **v3:** Incorporate real component fits once hardware is assembled — verify display + board stack height, button stem clearance
- **v4:** Add lanyard loop, finalize battery bay for specific battery model
- **Final:** Choose between Pico W and Pi Zero form factor, finalize internal mount points
