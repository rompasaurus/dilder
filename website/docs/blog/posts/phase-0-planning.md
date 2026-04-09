---
date: 2026-04-08
authors:
  - rompasaurus
categories:
  - Planning
slug: phase-0-planning
---

# Phase 0: Planning — From Idea to Blueprint

Every project starts somewhere. Dilder started with a question: how hard is it to actually build a Tamagotchi?

<!-- more -->

## The Idea

The original Tamagotchi was a 1996 keychain toy with a tiny LCD, three buttons, and a virtual pet that needed feeding, attention, and care. The concept is simple. The implementation, for a modern DIY version with a proper e-ink display, 3D-printed case, and programmable firmware, is substantially more involved.

The goals for Dilder:

1. A functional virtual pet device you can hold in your hand
2. A documented build process — hardware, software, enclosure, everything
3. A public project with a community that can build their own
4. An honest look at AI-assisted development — all prompts logged

## What Phase 0 Covered

Phase 0 was purely planning. No hardware ordered, no code written. Just research and documentation:

- **Hardware research** — identifying the right display (Waveshare 2.13" e-ink), compute (Pi Zero WH), and input options (tactile buttons)
- **Enclosure concepts** — rough proportions, button layout, display-to-case ratio
- **Project structure** — phases, documentation format, GitHub repo
- **Website and community planning** — this site, Discord, Patreon

## Key Decisions Made

### E-Ink Over LCD

E-ink was chosen over a small OLED or TFT LCD for a few reasons:

- **Standby current** — less than 0.01µA in standby. Perfect for a device that needs to run on a small battery.
- **Readability** — high contrast in any lighting condition, no backlight needed
- **Aesthetic** — the Tamagotchi style aesthetic benefits from a high-contrast, "paper" look
- **Tradeoff** — 2-second full refresh, 0.3-second partial refresh. Animation is possible but limited.

### Pi Zero WH

The Pi Zero WH was chosen over a custom MCU (Arduino, ESP32) because:

- Python ecosystem makes firmware prototyping fast
- The Waveshare HAT plugs directly onto the 40-pin header
- WiFi built in for remote development workflow
- More processing headroom for a future personality/AI system

The "WH" variant is critical — pre-soldered headers. Without it you'd need to solder the 40-pin header yourself.

### Tactile Buttons Over Capacitive Touch

Five discrete 6×6mm tactile buttons (up, down, left, right, center/select) beat capacitive touch for a first prototype because:

- Breadboard-friendly — no soldering required for the test bench
- Tactile feedback matters for a game device
- Zero additional components needed (Pi's internal pull-ups handle everything)

## Prototype Concept

The enclosure concept settled on an "iPod Nano" style layout — landscape rectangle, display on the left covering ~75% of the face, compact d-pad cluster on the right.

**v2 dimensions:**

| Metric | Value |
|--------|-------|
| Case outer | 88 × 34 × 19mm |
| Display window | 57 × 27mm |
| Active pixel area | 48.55 × 23.71mm (250×122 px) |

[See the hardware docs for full enclosure specs](../../docs/hardware/enclosure-design.md)

## What's Next

Phase 1 is hardware assembly. The components are ordered. The goal: power on the Pi, attach the display HAT, wire up buttons on a breadboard, and get something — anything — to show on the screen.

When the display shows its first pixel, Phase 1 is done.
