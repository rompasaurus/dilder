# Dilder Firmware — Architecture, Reading Guide & Debugging

> Everything you need to understand, navigate, and debug the Dilder game engine.

---

## Table of Contents

1. [What This Is](#1-what-this-is)
2. [How It Builds](#2-how-it-builds)
3. [Project Structure](#3-project-structure)
4. [Architecture Overview](#4-architecture-overview)
5. [Reading Guide — Where to Start](#5-reading-guide--where-to-start)
6. [Module Deep Dives](#6-module-deep-dives)
7. [Memory Model](#7-memory-model)
8. [The Display Framebuffer](#8-the-display-framebuffer)
9. [How the Game Tick Works](#9-how-the-game-tick-works)
10. [The Event System](#10-the-event-system)
11. [How Emotions Are Resolved](#11-how-emotions-are-resolved)
12. [How the DevTool Talks to the Firmware](#12-how-the-devtool-talks-to-the-firmware)
13. [Debugging Guide](#13-debugging-guide)
14. [Common Patterns in the Code](#14-common-patterns-in-the-code)
15. [Glossary](#15-glossary)

---

## 1. What This Is

This is the **game engine** for the Dilder virtual pet. It implements:

- A Tamagotchi-style stat system (hunger, happiness, energy, hygiene, health)
- 16 distinct emotional states with an AI-like resolution algorithm
- 6 life stages from Egg to Elder with evolution branching
- Sensor-driven gameplay (light, temperature, humidity, pedometer, microphone)
- A 250x122 pixel 1-bit display renderer with a bitmap font and octopus character
- Menu navigation, dialogue, and care actions

The firmware compiles two ways:

| Target | Output | Purpose |
|--------|--------|---------|
| **Shared library** | `libdilder.so` | Loaded by the DevTool via Python ctypes |
| **CLI executable** | `dilder_cli` | Standalone terminal test runner |

Both use the exact same game code — only the entry point differs.

---

## 2. How It Builds

### Prerequisites

- A C compiler (GCC or Clang)
- CMake 3.16+
- `make`

### Build Commands

```bash
cd firmware
mkdir -p build && cd build
cmake ..
make
```

This produces:
- `build/libdilder.so` — shared library for the DevTool
- `build/dilder_cli` — standalone test runner

### Quick Test

```bash
# Run 10 ticks in the terminal
echo "" | ./build/dilder_cli 10

# Verify the library loads from Python
python3 -c "
import ctypes
lib = ctypes.CDLL('build/libdilder.so')
lib.dilder_init()
lib.dilder_tick()
print('OK')
"
```

---

## 3. Project Structure

```
firmware/
├── CMakeLists.txt                      # Build system — produces .so and CLI
│
├── include/                            # Header files (API declarations)
│   ├── dilder.h                        # PUBLIC API — what Python calls
│   ├── game/
│   │   ├── game_state.h                # ALL data types (the most important file)
│   │   ├── event.h                     # Event bus interface
│   │   ├── stat.h                      # Stat system interface
│   │   ├── emotion.h                   # Emotion engine interface
│   │   ├── life.h                      # Life stages interface
│   │   ├── time_mgr.h                  # Time manager interface
│   │   ├── dialog.h                    # Dialogue system interface
│   │   ├── progress.h                  # Progression/bond interface
│   │   └── game_loop.h                 # Game loop interface
│   ├── sensor/
│   │   └── sensor.h                    # Sensor manager interface
│   └── ui/
│       ├── input.h                     # Button input queue
│       ├── render.h                    # Framebuffer rendering
│       └── ui.h                        # UI state machine
│
├── src/                                # Implementation files
│   ├── game/
│   │   ├── event.c                     # Event bus (fire, listen, ring buffer)
│   │   ├── time_mgr.c                  # Virtual game clock
│   │   ├── stat.c                      # Decay, care actions, thresholds
│   │   ├── emotion.c                   # 16 emotion triggers + resolution
│   │   ├── life.c                      # Life stage FSM + evolution
│   │   ├── dialog.c                    # Quote database + selection
│   │   ├── progress.c                  # Bond XP + leveling
│   │   └── game_loop.c                 # MAIN ORCHESTRATOR — ties everything together
│   ├── sensor/
│   │   └── sensor.c                    # Emulated sensor values
│   ├── ui/
│   │   ├── input.c                     # Button event queue
│   │   ├── render.c                    # Bitmap font, drawing, octopus renderer
│   │   └── ui.c                        # Menu FSM, input dispatch, screen selection
│   └── platform/desktop/
│       ├── dilder_api.c                # Shared library entry points (Python bridge)
│       └── main_desktop.c             # CLI test runner
│
└── FIRMWARE.md                         # This file
```

### Header vs Source Files

In C, code is split into two kinds of files:

- **Header files (`.h`)** declare what exists — struct definitions, function signatures, constants. They're like a table of contents.
- **Source files (`.c`)** contain the actual implementation — the function bodies that do the work.

When a `.c` file writes `#include "game/stat.h"`, the compiler copy-pastes the header's contents into that file. This is how different modules know about each other's types and functions.

---

## 4. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   DevTool (Python/Tkinter)                │
│                                                           │
│   Calls: dilder_init(), dilder_tick(),                   │
│          dilder_button_press(), dilder_set_light(), ...   │
│   Reads: dilder_get_framebuffer(), dilder_get_hunger()   │
└────────────────────────┬──────────────────────────────────┘
                         │ ctypes FFI
                         ▼
┌─────────────────────────────────────────────────────────┐
│               dilder_api.c (Shared Library API)          │
│         Thin wrapper — translates simple types to        │
│         game engine calls                                │
└────────────────────────┬──────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    game_loop.c                            │
│              MAIN ORCHESTRATOR                            │
│                                                           │
│  Every tick (1 second):                                   │
│   1. Process button input                                │
│   2. Poll sensors                                        │
│   3. Decay stats                                         │
│   4. Check thresholds → fire events                      │
│   5. Resolve emotion from stats + sensors                │
│   6. Check life stage transitions                        │
│   7. Update dialogue                                     │
│   8. Render to framebuffer if anything changed           │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬─────────────┘
   │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼
 stat   emotion  life  sensor  dialog  ui    event
  .c      .c     .c     .c     .c     .c     .c
```

### Data Flow

1. **Python** sets sensor values and button presses
2. **dilder_tick()** runs one game second
3. Stats decay, emotions resolve, dialogue triggers
4. **render.c** draws the pet, stats, and text to the framebuffer
5. **Python** reads the framebuffer and paints it to the Tkinter canvas

---

## 5. Reading Guide — Where to Start

Read the code in this order for the smoothest learning path:

### Level 1: Data Types (read first)

| File | Why |
|------|-----|
| `include/game/game_state.h` | **Start here.** Defines every struct, enum, and constant. You can't understand any other file without knowing these types. |
| `include/dilder.h` | The public API. Shows what the outside world can call. |

### Level 2: Simple Modules

| File | Why |
|------|-----|
| `src/game/time_mgr.c` | Simplest module. Shows how game time is tracked. |
| `src/game/event.c` | The event bus. Shows the listener pattern (function pointers). |
| `src/ui/input.c` | Ring buffer pattern. Very common in embedded C. |
| `src/game/progress.c` | Small file. Shows XP thresholds and leveling. |

### Level 3: Core Game Systems

| File | Why |
|------|-----|
| `src/game/stat.c` | The heart of gameplay. Stat decay, care actions, modifiers. |
| `src/game/emotion.c` | 16 emotion triggers evaluated every 5 ticks. Function pointer table. |
| `src/game/life.c` | Life stage FSM (finite state machine) with evolution scoring. |
| `src/game/dialog.c` | Quote database using arrays of string pointers. |

### Level 4: Display & UI

| File | Why |
|------|-----|
| `src/ui/render.c` | Bitmap font, pixel drawing, octopus renderer. The most visually interesting code. |
| `src/ui/ui.c` | Menu navigation, input dispatch, screen state machine. |
| `src/sensor/sensor.c` | Emulation layer for all sensors. |

### Level 5: Integration

| File | Why |
|------|-----|
| `src/game/game_loop.c` | The orchestrator. Calls everything else in the right order. |
| `src/platform/desktop/dilder_api.c` | The Python bridge. See how C functions become callable from Python. |

---

## 6. Module Deep Dives

### Stat System (`stat.c`)

The stat system uses **fractional accumulation** to handle decay rates that aren't whole numbers:

```
Problem: Hunger should drop 1 point every 10 minutes (600 ticks).
         But stats are integers — you can't subtract 0.00167 per tick.

Solution: Keep a separate accumulator. Each tick, add 1000 to it.
          When it reaches 600,000, subtract 1 from the stat and
          reset the accumulator.

          This gives perfectly accurate integer decay from fractional rates.
```

### Emotion Engine (`emotion.c`)

The emotion engine uses a **weighted evaluation** system:

1. Every 5 ticks, each of the 16 emotions gets a "weight" (0.0 to 1.0) from its trigger function
2. Life stage gates remove emotions the pet is too young to express
3. The highest-weight emotion wins (with priority as tiebreaker)
4. **Hysteresis** prevents flickering: the new emotion must beat the current one by a margin of 0.15

### Event Bus (`event.c`)

Modules communicate through events, not direct calls. This keeps them decoupled:

```
stat.c fires EVENT_STAT_CRITICAL
  → emotion.c hears it and increases angry/sad weight
  → dialogue.c hears it and shows a worried quote
  → Neither module needs to #include the other
```

### Rendering (`render.c`)

The display is a **1-bit framebuffer**: 250 pixels wide, 122 pixels tall, one bit per pixel (black or white). The buffer is 3,904 bytes.

```
Pixel (x, y) is stored in:
  Byte:  g_framebuffer[y * 32 + x / 8]
  Bit:   bit number (7 - x % 8), where bit 7 is the leftmost pixel

To set pixel (100, 50) black:
  byte_index = 50 * 32 + 100 / 8 = 1612
  bit_mask   = 0x80 >> (100 % 8) = 0x80 >> 4 = 0x08
  g_framebuffer[1612] |= 0x08;
```

---

## 7. Memory Model

### No Heap Allocation

This firmware uses **zero `malloc()`**. All memory is statically allocated:

| Memory Region | What Lives There | Lifetime |
|---------------|------------------|----------|
| **BSS segment** | `g_game` (global game state), `g_framebuffer` | Entire program |
| **Data segment** | `static const` tables (decay rates, emotion triggers, quotes) | Entire program |
| **Stack** | Local variables, function parameters, compound literals | One function call |

Why no malloc?
- Embedded systems (Pico W) have limited RAM (264KB)
- `malloc` can fail, fragment memory, and is harder to debug
- Static allocation means memory usage is 100% predictable at compile time

### The Global Game State

Everything lives in one struct:

```c
game_t g_game;  // ~500 bytes in the BSS segment
```

This contains ALL game state: stats, emotion, life stage, dialogue, menu, sensor data, etc. Every module reads/writes fields of this struct. It's declared `extern` in `game_state.h` so all modules can access it, and defined once in `game_loop.c`.

### Static Variables

Some functions use `static` local variables:

```c
void stat_update_health(stats_t *stats) {
    static uint8_t health_decay_counter = 0;  // Persists between calls!
    if (++health_decay_counter >= 5) { ... }
}
```

A `static` local variable is initialized once and keeps its value between function calls. It lives in the BSS/data segment, not the stack. It's like a private global variable that only that function can see.

---

## 8. The Display Framebuffer

```
g_framebuffer: 3,904 bytes = 32 bytes/row x 122 rows

Each byte holds 8 horizontal pixels:
  Bit 7 (0x80) = leftmost pixel
  Bit 0 (0x01) = rightmost pixel

  1 = black pixel
  0 = white pixel

Row 0:  bytes [0..31]    → pixels (0,0) to (249,0)
Row 1:  bytes [32..63]   → pixels (0,1) to (249,1)
...
Row 121: bytes [3872..3903] → pixels (0,121) to (249,121)

Note: 32 bytes = 256 bits, but only 250 are used per row.
The last 6 bits of each row are padding (ignored).
```

### Screen Layout

```
┌──────────────────────────────────────────────────┐  y=0
│ 12:00 PM    Normal     [stat icons]              │  Header (14px)
├──────────────────────────────────────────────────┤  y=14
│                                                  │
│            [Octopus character]                   │  Pet area (80px)
│            Eyes + mouth change                   │
│            with emotion                          │
│                                                  │
├──────────────────────────────────────────────────┤  y=94
│ "Just vibin'."                                   │  Dialogue (28px)
└──────────────────────────────────────────────────┘  y=122
```

---

## 9. How the Game Tick Works

Every call to `dilder_tick()` advances the game by 1 second:

```
dilder_tick()
  └── game_loop_tick(now_ms)
        │
        ├── Process all queued button presses
        │     └── ui_handle_input() → dispatches based on game state
        │
        ├── sensor_poll() → read emulated sensor values
        │
        ├── sensor_classify_events() → compare current vs previous sensors
        │     └── fires EVENT_SHAKEN, EVENT_LOUD_NOISE, etc.
        │
        ├── IF 1 second has passed since last tick:
        │     └── game_tick()
        │           ├── stat_decay_tick()        — every tick
        │           ├── stat_check_thresholds()  — every tick
        │           ├── life_stage_check()       — every tick
        │           ├── emotion_resolve()        — every 5 ticks
        │           ├── modifier_recalculate()   — every 10 ticks
        │           ├── dialogue_check_triggers() — every 30 ticks
        │           └── stat_cooldown_tick()     — every tick
        │
        └── IF display is dirty:
              └── ui_render() → draws to g_framebuffer
```

### Tick Rates

Not everything runs every second. The `should_tick(count, rate)` function staggers work:

| System | Rate | Runs Every |
|--------|------|-----------|
| Stat decay | 1 | Every tick (1s) |
| Emotion resolution | 5 | Every 5 ticks (5s) |
| Modifier recalculation | 10 | Every 10 ticks (10s) |
| Dialogue triggers | 30 | Every 30 ticks (30s) |
| Misbehavior check | 60 | Every 60 ticks (1 min) |

---

## 10. The Event System

The event system is a simple **publish-subscribe** pattern:

```c
// During init, modules register handlers:
event_listen(EVENT_FED, emotion_on_care_action);

// Later, when a care action happens:
event_fire(EVENT_FED, &(event_data_t){ .value = CARE_FEED_MEAL });
// → emotion_on_care_action() is called immediately
```

Events are also logged to a **ring buffer** (circular array of 16 entries). The emotion engine checks this buffer to see if recent events should influence the pet's mood.

---

## 11. How Emotions Are Resolved

```
1. EVALUATE — Run each emotion's trigger function:
   eval_hungry()  → returns 0.8 (hunger is low)
   eval_chill()   → returns 0.6 (stats are balanced)
   eval_normal()  → returns 0.1

2. GATE — Remove emotions the pet is too young for:
   Hatchlings only get: normal, hungry, tired, sad, excited
   Juveniles lose: creepy, nostalgic, unhinged

3. SELECT — Pick the highest weight:
   hungry wins at 0.8

4. HYSTERESIS — Is 0.8 > current_weight + 0.15?
   If yes → transition to hungry
   If no  → stay at current emotion (prevents flickering)

5. DWELL — Don't re-evaluate for min_dwell_ms (30 seconds)
```

---

## 12. How the DevTool Talks to the Firmware

```
Python (DevTool)                    C (libdilder.so)
─────────────────                   ─────────────────
import ctypes
lib = CDLL("libdilder.so")
                                    ┌─────────────────┐
lib.dilder_init()  ──────────────►  │ game_loop_init() │
                                    └─────────────────┘

lib.dilder_set_temperature(35.0) ►  sensor_emu_set_temperature(35.0)

lib.dilder_button_press(5, 1)  ──►  input_push(BTN_ACTION, PRESS_SHORT)

lib.dilder_tick()  ──────────────►  game_loop_tick(emu_time_ms)
                                      └── stat decay, emotion, render...

fb = lib.dilder_get_framebuffer()    returns pointer to g_framebuffer
fb[0]  ◄─────────────────────────   (Python reads C memory directly)
```

The key insight: **Python doesn't copy the framebuffer**. It gets a pointer into the C process's memory and reads the pixels directly. This is what `ctypes.POINTER(ctypes.c_uint8)` does — it's a raw memory address.

---

## 13. Debugging Guide

### Build Errors

```bash
# Clean build (fixes most issues)
cd firmware/build
rm -rf *
cmake ..
make

# See all compiler warnings
make VERBOSE=1
```

### Common Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| `implicit declaration of function` | Missing `#include` | Add the header that declares the function |
| `undefined reference to` | Function not compiled | Check CMakeLists.txt includes the .c file |
| `segfault in Python` | Wrong ctypes return type | Set `.restype` before calling the function |
| Stat not decaying | Modifier is 0.0 | Check `modifier_recalculate()` — egg stage has 0.0 modifier |
| Emotion won't change | Hysteresis or dwell | Wait for `min_dwell_ms` to pass, or check weight margin |

### Adding printf Debugging

In any `.c` file:

```c
#include <stdio.h>

void my_function(void) {
    printf("[DEBUG] hunger = %d\n", g_game.stats.primary.hunger);
}
```

When running via the DevTool, printf output goes to the terminal where you launched `python3 devtool.py`. When running `dilder_cli`, it goes to stdout.

### Checking Game State from Python

```python
import ctypes
lib = ctypes.CDLL("firmware/build/libdilder.so")
# ... setup ctypes (see dilder_api.c for all functions)

lib.dilder_init()
for i in range(100):
    lib.dilder_tick()
    print(f"Tick {i}: hunger={lib.dilder_get_hunger()}, "
          f"emotion={lib.dilder_get_emotion_name()}")
```

### Rebuilding from the DevTool

Click the **Rebuild** button in the Dilder tab. It runs `cmake .. && make` and reloads the library automatically.

---

## 14. Common Patterns in the Code

### Pattern: Compound Literals

```c
event_fire(EVENT_FED, &(event_data_t){ .value = CARE_FEED_MEAL });
```

`(event_data_t){ .value = CARE_FEED_MEAL }` creates a temporary struct on the stack. The `&` takes its address. This is a C99 feature called a "compound literal" — it's like an anonymous local variable.

### Pattern: Static Const Tables

```c
static const care_effect_t CARE_EFFECTS[CARE_COUNT] = { ... };
```

`static` means this table is only visible in this file. `const` means it can't be modified. The compiler puts it in read-only memory. This is the standard way to define lookup tables in C.

### Pattern: Ring Buffer

```c
ring[ring_head] = new_entry;
ring_head = (ring_head + 1) % RING_SIZE;
```

A ring buffer wraps around when it reaches the end. The `% RING_SIZE` operation makes the index wrap from `RING_SIZE-1` back to 0. This gives you a fixed-size sliding window of recent entries.

### Pattern: Fractional Accumulator

```c
accum += rate_per_600_ticks;
if (accum >= 600000) {
    stat -= 1;
    accum -= 600000;
}
```

When you need to subtract a fractional amount per tick but your stat is an integer, accumulate the fractional part separately. When it reaches a full unit, apply it. This gives exact results without floating point.

### Pattern: Function Pointers

```c
typedef float (*eval_fn_t)(const stats_t *, ...);

static const emotion_trigger_t TRIGGERS[] = {
    { EMOTION_HUNGRY, eval_hungry, 8.0f, 30000 },
    ...
};

// Later:
float weight = TRIGGERS[i].evaluate(stats, ctx, life);
```

A function pointer stores the address of a function. You can call it like a regular function. This lets you build tables of behaviors — each emotion has its own evaluation function, and the engine loops through them all.

### Pattern: Extern Globals

```c
// In game_state.h:
extern game_t g_game;  // "This exists somewhere"

// In game_loop.c:
game_t g_game;  // "Here it is" (actual definition)
```

`extern` says "this variable is defined in another file." Every `.c` file that includes the header can use it. Only one `.c` file actually allocates the storage (without `extern`).

---

## 15. Glossary

| Term | Meaning |
|------|---------|
| **BSS segment** | Memory region for uninitialized/zero-initialized global variables |
| **Data segment** | Memory region for initialized global/static variables |
| **Stack** | Memory for local variables, grows/shrinks with function calls |
| **Heap** | Dynamic memory (malloc/free) — not used in this firmware |
| **FFI** | Foreign Function Interface — calling C from Python |
| **ctypes** | Python library for loading C shared libraries |
| **FSM** | Finite State Machine — a system with defined states and transitions |
| **HAL** | Hardware Abstraction Layer — same API, different implementation per platform |
| **1bpp** | 1 bit per pixel — each pixel is either black (1) or white (0) |
| **Ring buffer** | Circular array that overwrites oldest entries when full |
| **Compound literal** | `(type){ .field = value }` — creates a temporary struct on the stack |
| **Hysteresis** | Requiring a margin before switching states (prevents oscillation) |
| **Dwell time** | Minimum time an emotion must display before it can change |
| **Tick** | One game loop iteration (1 second of game time) |
