# Dilder

A Tamagotchi-inspired virtual pet built on a Raspberry Pi Pico W with an e-ink display, battery pack, and 3D-printed case — developed entirely in the open as a learning platform, blog series, and YouTube companion project.

The goal isn't just to build a thing — it's to show *how* the thing gets built, from the very first idea to a finished handheld device. Every prompt, every design decision, every dead end is documented so anyone can follow along, learn, and build their own.

---

## How It Started — Meet Jamal

<p align="center">
  <img src="website/docs/assets/images/jamal-the-original.jpg" alt="Jamal the plush octopus" width="400" />
  <br />
  <em>Jamal. The plush octopus who started it all.</em>
</p>

This project didn't start with a schematic or a product spec. It started in a TEDi — a German dollar store — where my wife Emma and I found a giant plush octopus grinning up from a discount bin. We bought him on the spot, and on the walk home we started giving him a personality: laid-back, opinionated, a little sassy, suspiciously wise for a boneless creature. By the time we got home, he had a name — **Jamal** — and he'd claimed the armchair like he'd been paying rent.

The question asked itself: *what if we could actually bring him to life?* Not literally — but as a tiny digital companion. A pocket-sized octopus with moods, opinions, and an attitude problem, living on an e-ink screen and judging your life choices in ALL CAPS.

That's how Dilder was born. Not from an engineering roadmap, but from a stuffed animal and two people who couldn't stop anthropomorphizing it on a walk home.

---

## What This Project Is

- **A virtual pet device** — a pocket-sized, low-power companion with personality, needs, and interactions displayed on an e-ink screen
- **A build series** — a step-by-step guide covering hardware, software, 3D printing, and project planning
- **A transparency experiment** — the entire development process is captured in real time, including AI-assisted prompts, iteration, and mistakes

---

## Hardware

### Phase 1 — Pico W Prototype (current)

| Component | Details |
|-----------|---------|
| Board | Raspberry Pi Pico W (or Pico WH with pre-soldered headers) |
| Display | [Waveshare Pico-ePaper-2.13](https://www.waveshare.com/pico-epaper-2.13.htm) — 250x122px, black & white, SPI1, SSD1680 driver, Pico-native 40-pin plug-in module |
| Power | USB micro-B (development); battery TBD |
| Input | 5x 6x6mm tactile push buttons (3 nav + 2 action) via GPIO |

### Future — Pi Zero Upgrade

| Component | Details |
|-----------|---------|
| Board | Raspberry Pi Zero WH (W or 2 W, pre-soldered headers) |
| Power | LiPo battery + Adafruit PowerBoost 500C |
| Enclosure | 3D-printed case (STL files provided) |

> The Pico W is the starting platform — it's what we have on hand, it's cheap, and it's excellent for prototyping the display and input system. The Pi Zero upgrade comes later when we need Linux, networking features, or more compute.

---

## Phases

Each phase maps to a section of the blog/YouTube series and can be followed independently.

### Phase 0 — Project Planning & Documentation ✓

- [x] Create repository and project structure
- [x] Define project intent and scope
- [x] Begin prompt progression log ([PromptProgression.md](PromptProgression.md))
- [x] Outline full phase roadmap
- [x] Create pixel art concepts for e-ink display (octopus character with 16 emotional states)
- [x] Define enclosure concept and prototype dimensions

### Phase 1 — Hardware Selection & Setup (Pico W) ✓

- [x] Finalize component list with links/part numbers ([hardware-research.md](docs/hardware-research.md))
- [x] Set up Docker-based C SDK cross-compilation toolchain
- [x] Wire e-ink display to Pico W via jumper wires (SPI)
- [x] Flash and run "Hello, Dilder!" on the e-ink display — proof of life
- [x] Build DevTool GUI — display emulator, serial monitor, firmware flash, asset manager, GPIO reference, connection utility, documentation ([DevTool/](DevTool/))
- [x] Add Programs tab with animated octopus preview, firmware size estimation, and deploy
- [x] Build IMG-receiver firmware — stream images from PC to Pico display via USB serial ([dev-setup/img-receiver/](dev-setup/img-receiver/))
- [x] Build standalone deploy — runtime-rendered animation, runs without PC
- [ ] Wire and test button inputs (GPIO)
- [ ] Battery power prototype

### Phase 2 — Firmware Foundation (C on Pico W)
> *You are here*

- [x] Runtime rendering engine — draw octopus mathematically (no pre-baked frames)
- [x] Animation system — 4-frame mouth cycle with per-mood expression sequences
- [x] Body transform system — dx/dy offset, x_expand, per-row sine wobble
- [x] Custom body shapes for Fat (wider dome, thick tentacles) and Lazy (tentacles draped right)
- [x] 16 emotional states with unique eyes, pupils, eyebrows, eyelids, mouths, and body animations
- [x] 17 standalone firmware programs (16 emotions + mood selector with all 823 quotes)
- [x] Date/time clock header from RTC
- [x] C-faithful preview renderer for verifying firmware matches DevTool
- [x] Keyboard-to-Pico input mapping plan ([docs/keyboard-to-pico-input.md](docs/keyboard-to-pico-input.md))
- [ ] Implement serial command input for interactive mood control
- [ ] Wire and test GPIO button inputs
- [ ] Build game loop with state machine (idle, interact, sleep)

### Phase 3 — Pet Logic & Gameplay

- [ ] Define pet stats (hunger, happiness, energy, health, etc.)
- [ ] Implement stat decay over time
- [ ] Build interaction system — feed, play, sleep, clean
- [x] Pet mood / expressions based on emotional states (16 implemented)
- [x] Animation frames for e-ink (idle expressions, body movement per mood)
- [ ] Emotional state transitions triggered by interactions and stats
- [ ] Add death/game-over state and reset/new-pet flow

### Phase 4 — UI & Menus

- [ ] Design menu system for e-ink (optimized for minimal refreshes)
- [ ] Build status bar — icons for stats, clock, battery level
- [ ] Add screen transitions between menu, pet view, and interactions
- [ ] Implement settings screen (contrast, name pet, reset)

### Phase 5 — Pi Zero Migration

- [ ] Port MicroPython firmware to CPython on Pi Zero
- [ ] Set up headless Raspberry Pi OS
- [ ] Adapt display driver for Pi Zero SPI + Waveshare HAT
- [ ] Adapt input handler for Pi Zero GPIO
- [ ] Validate all Phase 2-4 functionality on Pi Zero

### Phase 6 — 3D-Printed Case & Power

- [ ] Design enclosure in CAD (FreeCAD / Fusion 360)
- [ ] Account for display cutout, button access, USB charging port, speaker hole
- [ ] Print prototypes and iterate on fit
- [ ] Implement battery power (LiPo + PowerBoost 500C)
- [ ] Implement sleep/wake cycle to conserve battery
- [ ] Publish final STL files and assembly instructions

### Phase 7 — Extras & Community

- [ ] Add sound (piezo buzzer for beeps/alerts)
- [ ] Explore connectivity — Bluetooth/Wi-Fi pet interactions?
- [ ] Mini-games
- [ ] Seasonal/event-based pet outfits or moods
- [ ] Publish a "build your own" kit guide
- [ ] Community gallery — show off your Dilder

---

## Content & Documentation

| Resource | Description |
|----------|-------------|
| [PromptProgression.md](PromptProgression.md) | Every AI prompt used in development (104+), timestamped with token counts and file changes |
| [docs/hardware-research.md](docs/hardware-research.md) | Component research, materials list, GPIO pinout, and enclosure concepts |
| [Emotion States](https://dilder.dev/docs/software/emotion-states/) | All 16 emotional states with rendered previews and animation strips |
| [docs/keyboard-to-pico-input.md](docs/keyboard-to-pico-input.md) | Input mapping plan for interactive octopus control |
| [Blog](https://dilder.dev/blog/) | Build journal — 8 posts covering planning through body animations |
| YouTube (TBD) | Video walkthroughs for each phase |

---

## Follow Along

This project is built in the open. Star/watch this repo to follow progress. Each phase will have a corresponding blog post and video.

---

## License

TBD

---

*Built with patience, a Pico W, and an unreasonable fondness for a plush octopus named Jamal.*
