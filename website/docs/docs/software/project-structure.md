# Project Structure

Directory layout and module overview for the Dilder project.

---

## Repository Layout

```
dilder/
├── README.md                    # Project overview and phase tracker
├── PromptProgression.md         # Every AI prompt logged with token counts
├── setup.py                     # Interactive CLI for first-time dev environment setup
│
├── DevTool/                     # Tkinter GUI for Pico W development
│   ├── devtool.py               # Main application (9 classes, 7 tabs)
│   ├── requirements.txt         # Python dependencies (pyserial, Pillow)
│   └── README.md                # Comprehensive usage walkthrough
│
├── dev-setup/                   # Hardware setup resources
│   ├── pico-and-display-first-time-setup.md  # Step-by-step hardware guide
│   ├── hello-world/             # C project — e-ink display Hello World
│   ├── hello-world-serial/      # C project — serial-only Hello World
│   ├── img-receiver/            # C project — receive images over serial
│   ├── sassy-octopus/           # Sassy personality (196 quotes)
│   ├── supportive-octopus/      # Supportive personality (160 quotes)
│   ├── angry-octopus/           # Angry personality (45 quotes)
│   ├── conspiratorial-octopus/  # Conspiratorial/weird personality (47 quotes)
│   ├── sad-octopus/             # Sad personality (35 quotes)
│   ├── chaotic-octopus/         # Chaotic personality (40 quotes)
│   ├── hungry-octopus/          # Hungry personality (30 quotes)
│   ├── tired-octopus/           # Tired personality (30 quotes)
│   ├── slaphappy-octopus/       # Slap happy personality (30 quotes)
│   ├── lazy-octopus/            # Lazy personality (30 quotes, custom body)
│   ├── fat-octopus/             # Fat personality (30 quotes, custom body)
│   ├── chill-octopus/           # Chill personality (30 quotes)
│   ├── horny-octopus/           # Horny personality (30 quotes)
│   ├── excited-octopus/         # Excited personality (30 quotes)
│   ├── nostalgic-octopus/       # Nostalgic personality (30 quotes)
│   ├── homesick-octopus/        # Homesick personality (30 quotes)
│   ├── mood-selector/           # Interactive: all 16 moods, serial input
│   ├── Dockerfile               # Reproducible ARM cross-compile container
│   └── docker-compose.yml       # Build services for all programs
│
├── hardware-design/             # Enclosure and component planning
│   └── hardware-planning.md     # Dimensions, button options, CAD plan, print costs
│
├── docs/                        # Raw research and reference docs
│   ├── hardware-research.md     # Component specs and GPIO budget
│   ├── setup-guide.md           # Original setup walkthrough
│   ├── keyboard-to-pico-input.md # Serial/GPIO input mapping guide
│   ├── programs-guide.md        # Comprehensive guide to all 19 programs
│   └── concepts/
│       ├── prototype-v1.svg     # Enclosure concept render v1
│       └── prototype-v2.svg     # Dimension-accurate concept render v2
│
├── assets/                      # Saved display images from DevTool
│   ├── *.pbm                    # Portable Bitmap format
│   ├── *.bin                    # Raw display buffer
│   └── *.png                    # PNG exports
│
├── website/                     # This website (MkDocs Material project)
│   ├── mkdocs.yml               # Site configuration
│   ├── dev.py                   # Website dev CLI (serve, build, deploy)
│   ├── requirements.txt         # MkDocs dependencies
│   ├── PLAN.md                  # Site architecture plan
│   ├── IMPLEMENTATION.md        # Build process documentation
│   ├── CONTENT-GUIDE.md         # Content management guide
│   ├── DEPLOY.md                # GitHub Pages deployment guide
│   └── docs/                    # Site content (Markdown)
│
├── firmware/                    # C game engine (compiles to .so + CLI)
│   ├── CMakeLists.txt           # Build system (shared lib + standalone CLI)
│   ├── FIRMWARE.md              # Architecture guide, reading order, debugging
│   ├── include/                 # Headers: all types, API declarations
│   │   ├── dilder.h             # Public API (called from Python via ctypes)
│   │   ├── game/                # game_state.h, event.h, stat.h, emotion.h, life.h, etc.
│   │   ├── sensor/              # sensor.h (emulation layer)
│   │   └── ui/                  # input.h, render.h, ui.h
│   └── src/                     # Implementation
│       ├── game/                # stat.c, emotion.c, life.c, dialog.c, event.c, game_loop.c
│       ├── sensor/              # sensor.c (emulated sensor values)
│       ├── ui/                  # render.c (bitmap font, octopus), ui.c (menus), input.c
│       └── platform/desktop/    # dilder_api.c (Python bridge), main_desktop.c (CLI)
│
└── Gameplay Planning/           # 13 design documents (11,000+ lines)
    ├── 00-architecture-overview.md
    ├── 01-core-game-loop.md
    ├── 02-stat-system.md
    ├── 03-emotion-engine.md
    ├── 04-sensor-interfaces.md
    └── ... (through 13-feature-menus-achievements.md)
```

!!! success "Firmware implemented"
    The `firmware/` directory contains a complete, working game engine. Build with `cd firmware/build && cmake .. && make`. Run the Dilder tab in the DevTool or test with `./dilder_cli`. See [Firmware Game Engine](firmware-engine.md) for full documentation.

!!! warning "Flash storage limits"
    The Pico W has 2MB of flash. C firmware is much smaller than MicroPython, but keep sprite files small — use 1-bit monochrome bitmaps, not PNGs with metadata.

---

## Planned Firmware Modules (C)

The firmware is written in C using the Pico SDK. The planned module structure:

### `core/display.c`

Thin wrapper around the Waveshare e-Paper driver:

- Initializes SPI and the display via the Pico SDK
- Exposes `display_render()` for full refresh and `display_render_partial()` for partial
- Handles cleanup and sleep mode
- Manages refresh rate limiting (prevent over-refreshing)

### `core/input.c`

Button input manager:

- Sets up GPIO pins with internal pull-ups via `gpio_set_pulls()`
- Provides polling: `input_is_pressed(button)`
- Handles software debouncing (~10ms default)
- Button constants: `BTN_UP` (GP2), `BTN_DOWN` (GP3), `BTN_LEFT` (GP4), `BTN_RIGHT` (GP5), `BTN_SELECT` (GP6)

### `core/loop.c`

Main game loop:

- 10Hz target tick rate (100ms per tick)
- Calls `pet_tick()` on each loop iteration
- Reads pending input events and dispatches to pet state machine
- Triggers display refresh when pet state changes

### `pet/pet.c`

Pet state machine:

- States: `IDLE`, `EATING`, `PLAYING`, `SLEEPING`, `SICK`
- Tracks stats: hunger, happiness, energy, age
- Stat decay over time (hunger increases, happiness decreases)
- State transitions driven by input and stat thresholds

### `pet/animations.c`

Sprite animation sequences:

- Each animation is an array of `{sprite_data, duration_ms}` structs
- Animator tracks current frame, advances on tick
- Renders to a framebuffer passed to `display_render_partial()`

---

## Asset Format

### Sprites

- Format: 1-bit monochrome (raw byte arrays or PBM)
- Coordinate space: 250×122 (full display) or any sub-region
- Naming: `{state}_{frame:02d}.pbm` — e.g., `idle_00.pbm`, `idle_01.pbm`
- The [DevTool](../tools/devtool.md) display emulator can create and preview sprites at exact display resolution

!!! tip "Why not PNG?"
    The Pico W firmware works with raw byte arrays for display rendering. Pre-convert sprites to 1-bit raw format on your dev machine using the DevTool or command-line tools before embedding in firmware.

### Fonts

- For small text, use bitmap font arrays compiled into the firmware
- For larger text, use a custom font renderer
- Recommended size: 8px–16px works well at 250×122 resolution

---

## Key Differences from Pi Zero Development

| Aspect | Pico W (C SDK) | Pi Zero (CPython + Linux) |
|--------|---------------|--------------------------|
| Language | C with Pico SDK | Python with PIL/Pillow |
| Graphics | Raw framebuffer | `PIL.Image` + `ImageDraw` |
| GPIO | `gpio_init()` / `gpio_get()` | `RPi.GPIO` |
| SPI | Pico SDK `spi_init()` | `spidev` |
| File I/O | 2MB flash, no filesystem | Full Linux filesystem |
| Build | CMake + Ninja cross-compile | `pip install` packages |
| Debugging | Serial over USB + SWD | SSH + debugpy |
| Boot | Instant (~1s) | 30–90 seconds |
