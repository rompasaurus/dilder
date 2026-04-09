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
│   ├── setup-guide.md           # Full Pi Zero + display setup walkthrough
│   └── concepts/
│       ├── prototype-v1.svg
│       └── prototype-v2.svg
│
├── website/                     # This website (MkDocs project)
│   ├── mkdocs.yml
│   └── docs/
│
└── firmware/                    # Pi Zero code (Phase 2+)
    ├── main.py                  # Entry point
    ├── requirements.txt
    ├── venv/                    # (not committed)
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
        ├── sprites/             # 1-bit PNG sprites (250×122 or smaller)
        └── fonts/               # TTF fonts for display text
```

!!! note "Firmware not yet written"
    The `firmware/` directory structure above is the planned layout. Phase 2 will establish this scaffold.

---

## Planned Module Responsibilities

### `core/display.py`

Thin wrapper around the Waveshare e-Paper library:

- Initializes the display
- Exposes `render(image)` for full refresh and `render_partial(image)` for partial
- Handles cleanup and sleep mode
- Manages refresh rate limiting (prevent over-refreshing)

### `core/input.py`

Button input manager:

- Sets up GPIO pins with internal pull-ups
- Provides event-based callbacks: `on_press(button, callback)`
- Handles software debouncing (10ms default)
- Button constants: `BTN_UP`, `BTN_DOWN`, `BTN_LEFT`, `BTN_RIGHT`, `BTN_SELECT`

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

- Each animation is a list of `(image_path, duration_ms)` tuples
- `Animator` class tracks current frame, advances on tick
- Renders to a PIL `Image` object passed to `display.render_partial()`

---

## Asset Format

### Sprites

- Format: 1-bit PNG (black and white only)
- Coordinate space: 250×122 (full display) or any sub-region
- Naming: `{state}_{frame:02d}.png` — e.g., `idle_00.png`, `idle_01.png`

### Fonts

- Format: TTF
- Recommended: [Monocraft](https://github.com/IdreesInc/Monocraft) or any bitmap-style monospace font
- Size: 8px–16px works well at 250×122 resolution
