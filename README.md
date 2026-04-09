# Dilder

A Tamagotchi-inspired virtual pet built on a Raspberry Pi Zero with an e-ink display, battery pack, and 3D-printed case — developed entirely in the open as a learning platform, blog series, and YouTube companion project.

The goal isn't just to build a thing — it's to show *how* the thing gets built, from the very first idea to a finished handheld device. Every prompt, every design decision, every dead end is documented so anyone can follow along, learn, and build their own.

---

## What This Project Is

- **A virtual pet device** — a pocket-sized, low-power companion with personality, needs, and interactions displayed on an e-ink screen
- **A build series** — a step-by-step guide covering hardware, software, 3D printing, and project planning
- **A transparency experiment** — the entire development process is captured in real time, including AI-assisted prompts, iteration, and mistakes

---

## Hardware

| Component | Details |
|-----------|---------|
| Board | Raspberry Pi Zero WH (W or 2 W, pre-soldered headers) |
| Display | [Waveshare 2.13" e-Paper HAT V4](https://www.amazon.de/-/en/gp/product/B07Q5PZMGT) — 250x122px, black & white, SPI, SSD1680 driver |
| Power | LiPo battery + Adafruit PowerBoost 500C (or TP4056 + MT3608 budget option) |
| Enclosure | 3D-printed case (STL files provided) |
| Input | 5x 6x6mm tactile push buttons (3 nav + 2 action) via GPIO |

---

## Phases

Each phase maps to a section of the blog/YouTube series and can be followed independently.

### Phase 0 — Project Planning & Documentation

- [x] Create repository and project structure
- [x] Define project intent and scope
- [x] Begin prompt progression log ([PromptProgression.md](PromptProgression.md))
- [x] Outline full phase roadmap
- [ ] Define the "pet" — personality, stats, behaviors (deferred to Phase 3)
- [ ] Create initial wireframes / pixel art concepts for e-ink display

### Phase 1 — Hardware Selection & Setup
> *You are here*

- [x] Finalize component list with links/part numbers ([hardware-research.md](docs/hardware-research.md))
- [ ] Set up Pi Zero with headless Raspberry Pi OS ([setup guide](docs/setup-guide.md))
- [ ] Wire and test e-ink display (SPI connection)
- [ ] Wire and test button inputs (GPIO)
- [ ] Test battery + charging circuit
- [ ] Document wiring diagrams and pinouts

### Phase 2 — Software Foundation

- [ ] Choose language/framework (Python w/ Pillow, or C for speed)
- [ ] Build display driver abstraction — render frames to e-ink
- [ ] Create game loop (low-power, event-driven for e-ink refresh rates)
- [ ] Implement basic input handling from GPIO buttons
- [ ] Display a static pet sprite on screen as proof of life

### Phase 3 — Pet Logic & Gameplay

- [ ] Define pet stats (hunger, happiness, energy, health, etc.)
- [ ] Implement stat decay over time
- [ ] Build interaction system — feed, play, sleep, clean
- [ ] Add pet mood / expressions based on stat levels
- [ ] Implement basic animation frames for e-ink (idle, happy, sad, sleeping)
- [ ] Add death/game-over state and reset/new-pet flow

### Phase 4 — UI & Menus

- [ ] Design menu system for e-ink (optimized for minimal refreshes)
- [ ] Build status bar — icons for stats, clock, battery level
- [ ] Add screen transitions between menu, pet view, and interactions
- [ ] Implement settings screen (contrast, name pet, reset)

### Phase 5 — 3D-Printed Case

- [ ] Design enclosure in CAD (FreeCAD / Fusion 360)
- [ ] Account for display cutout, button access, USB charging port, speaker hole
- [ ] Print prototypes and iterate on fit
- [ ] Publish final STL files
- [ ] Assembly instructions with photos

### Phase 6 — Power Management & Polish

- [ ] Implement sleep/wake cycle to conserve battery
- [ ] Add low-battery warning on display
- [ ] Optimize e-ink refresh strategy (partial vs. full refresh)
- [ ] Auto-save pet state to SD card on shutdown
- [ ] Stress test battery life and document results

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
| [PromptProgression.md](PromptProgression.md) | Every AI prompt used in development, timestamped with token counts and file changes |
| [docs/hardware-research.md](docs/hardware-research.md) | Component research, materials list, GPIO pinout, and enclosure concepts |
| [docs/setup-guide.md](docs/setup-guide.md) | Complete hardware & development environment setup guide |
| Blog (TBD) | Written companion posts for each phase |
| YouTube (TBD) | Video walkthroughs for each phase |

---

## Follow Along

This project is built in the open. Star/watch this repo to follow progress. Each phase will have a corresponding blog post and video.

---

## License

TBD

---

*Built with patience, a Pi Zero, and an unreasonable fondness for virtual pets.*
