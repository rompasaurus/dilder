# Documentation

Reference documentation for every aspect of the Dilder build. Unlike the [blog](../blog/index.md), docs pages are kept up to date as the project evolves — they reflect current state, not build history.

---

## The Namesake

Everything in these docs traces back to a single plush octopus named **Jamal** — rescued from a TEDi discount bin, anthropomorphized on a walk home, and now the spiritual mascot of the entire project. The digital octopus on the e-ink display is Jamal's avatar: same attitude, same refusal to take anything seriously, compressed into 250x122 pixels. When the docs reference "the octopus," that's who we're talking about. [Full origin story here.](../index.md#the-origin-story--how-jamal-was-found)

---

## Sections

### Hardware

Specs, wiring, and physical design.

- [Materials List](hardware/materials-list.md) — every component, cost, and purchase link
- [Wiring & Pinout](hardware/wiring-pinout.md) — GPIO assignments and breadboard layout
- [Enclosure Design](hardware/enclosure-design.md) — case dimensions, design constraints, concept renders

### Setup

Getting a working development environment.

- [Pico W Setup](setup/pi-zero-setup.md) — firmware flash, serial REPL, and smoke test
- [Display Setup](setup/display-setup.md) — jumper wire connection, Waveshare driver, hello world
- [Dev Environment](setup/dev-environment.md) — VSCode + MicroPico on Linux

### Design

Custom hardware and game design documents.

- [User Engagement Plan](design/user-engagement-plan.md) — gameplay loops, stat system, life stages, progression
- [Custom PCB Design Research](design/custom-pcb-design-research.md) — PicoTop case study, Dilder board spec, KiCad learning path
- [PCB Assembly & Prototyping](design/pcb-assembly-and-prototyping.md) — provider pricing, cost estimates, open-source reference boards
- [Open-Source Board Designs](design/open-board-designs.md) — 7 reference designs with images, walkthroughs, and component overlap analysis
- [Motion & Location Detection](design/motion-location-detection.md) — step counting, WiFi fingerprinting, BLE scanning — no GPS needed

### Software

Code architecture and reference.

- [Project Structure](software/project-structure.md) — directory layout and module overview

### Tools

Python utilities built to support the development workflow.

- [DevTool (GUI)](tools/devtool.md) — Tkinter app with display emulator, serial monitor, firmware flash, asset manager, and more
- [Setup CLI](tools/setup-cli.md) — interactive step-by-step environment setup for the Pico W C SDK toolchain
- [Website Dev CLI](tools/website-dev.md) — MkDocs site management with interactive menu

### Reference

Official hardware documentation.

- [Pico W](reference/pico-w.md) — RP2040 specs, pinout, MicroPython firmware
- [Waveshare e-Paper HAT](reference/waveshare-eink.md) — display specs, SPI protocol, driver setup

---

!!! tip "Looking for a step-by-step walkthrough?"
    The [blog posts](../blog/index.md) walk through each phase in narrative order. Docs are the reference; blog is the story.
