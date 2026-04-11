# Project Structure

Directory layout and module overview for the Dilder firmware. This page reflects the planned structure — it will be fleshed out as Phase 2 (firmware) begins.

---

## Repository Layout

```
dilder/
├── README.md                    # Project overview and phase tracker
├── PromptProgression.md         # Every AI prompt logged with token counts
│
├── docs/                        # Raw research and reference docs
│   ├── hardware-research.md     # Component specs and enclosure design
│   └── concepts/
│       ├── prototype-v1.svg
│       └── prototype-v2.svg
│
├── website/                     # This website (MkDocs project)
│   ├── mkdocs.yml
│   └── docs/
│
└── firmware/                    # MicroPython code for Pico W (Phase 2+)
    ├── main.py                  # Entry point (runs on boot)
    ├── boot.py                  # Pre-boot config (Wi-Fi setup, etc.)
    ├── epd2in13_V3.py           # Waveshare display driver (uploaded from lib)
    ├── epdconfig.py             # SPI/GPIO config for driver
    │
    ├── core/
    │   ├── display.py           # Display driver wrapper
    │   ├── input.py             # Button input handler
    │   └── loop.py              # Main game loop
    │
    ├── pet/
    │   ├── pet.py               # Pet state machine
    │   ├── mood.py              # Mood/stat system
    │   └── animations.py        # Sprite animation sequences
    │
    └── assets/
        ├── sprites/             # 1-bit PBM/raw sprites (250×122 or smaller)
        └── fonts/               # Bitmap font data (framebuf built-in or custom)
```

!!! note "Firmware not yet written"
    The `firmware/` directory structure above is the planned layout. Phase 2 will establish this scaffold.

!!! warning "Flash storage limits"
    The Pico W has 2MB of flash. MicroPython firmware uses ~700KB, leaving ~1.3MB for your code and assets. Keep sprite files small — use 1-bit monochrome bitmaps, not PNGs with metadata.

---

## Planned Module Responsibilities

### `core/display.py`

Thin wrapper around the Waveshare e-Paper driver:

- Initializes SPI and the display
- Exposes `render(buf)` for full refresh and `render_partial(buf)` for partial
- Handles cleanup and sleep mode
- Manages refresh rate limiting (prevent over-refreshing)

### `core/input.py`

Button input manager:

- Sets up GPIO pins with internal pull-ups
- Provides event-based callbacks or polling: `is_pressed(button)`
- Handles software debouncing (~10ms default)
- Button constants: `BTN_UP`, `BTN_DOWN`, `BTN_LEFT`, `BTN_RIGHT`, `BTN_SELECT`

```python
from machine import Pin

class Input:
    BTN_UP     = Pin(2, Pin.IN, Pin.PULL_UP)
    BTN_DOWN   = Pin(3, Pin.IN, Pin.PULL_UP)
    BTN_LEFT   = Pin(4, Pin.IN, Pin.PULL_UP)
    BTN_RIGHT  = Pin(5, Pin.IN, Pin.PULL_UP)
    BTN_SELECT = Pin(6, Pin.IN, Pin.PULL_UP)
```

### `core/loop.py`

Main game loop:

- 10Hz target tick rate (100ms per tick)
- Calls `pet.tick()` on each loop iteration
- Reads pending input events and dispatches to pet state machine
- Triggers display refresh when pet state changes

### `pet/pet.py`

Pet state machine:

- States: `IDLE`, `EATING`, `PLAYING`, `SLEEPING`, `SICK`
- Tracks stats: hunger, happiness, energy, age
- Stat decay over time (hunger increases, happiness decreases)
- State transitions driven by input and stat thresholds

### `pet/animations.py`

Sprite animation sequences:

- Each animation is a list of `(sprite_data, duration_ms)` tuples
- `Animator` class tracks current frame, advances on tick
- Renders to a `framebuf.FrameBuffer` passed to `display.render_partial()`

---

## Asset Format

### Sprites

- Format: 1-bit monochrome (raw bytearray or PBM)
- Coordinate space: 250×122 (full display) or any sub-region
- Naming: `{state}_{frame:02d}.pbm` — e.g., `idle_00.pbm`, `idle_01.pbm`

!!! tip "Why not PNG?"
    MicroPython doesn't include PIL/Pillow. The `framebuf` module works with raw byte arrays. Pre-convert sprites to 1-bit raw format on your dev machine before uploading.

### Fonts

- MicroPython's built-in `framebuf.text()` provides an 8×8 pixel font
- For larger text, use bitmap font arrays or a custom font renderer
- Recommended size: 8px–16px works well at 250×122 resolution

---

## Key Differences from Pi Zero Development

| Aspect | Pico W (MicroPython) | Pi Zero (CPython + Linux) |
|--------|---------------------|--------------------------|
| Graphics | `framebuf.FrameBuffer` | `PIL.Image` + `ImageDraw` |
| GPIO | `machine.Pin` | `RPi.GPIO` |
| SPI | `machine.SPI` | `spidev` |
| File I/O | 2MB flash, no SD | Full Linux filesystem |
| Imports | Upload `.py` files to flash | `pip install` packages |
| Debugging | REPL over USB serial | SSH + debugpy |
| Boot | Instant (~1s) | 30–90 seconds |
