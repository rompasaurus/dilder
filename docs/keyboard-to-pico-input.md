# Keyboard-to-Pico Input Mapping — Interactive Octopus Control

> How to wire PC keyboard actions to the Pico so you can play with octopus emotions, expressions, and body states in real time during development.

---

## What We Have Now

| Layer | Status | Details |
|-------|--------|---------|
| USB CDC serial (PC → Pico) | **Active** | `stdio_usb` enabled, 115200 baud, `getchar_timeout_us()` works |
| USB CDC serial (Pico → PC) | **Active** | `printf()` output, DevTool serial monitor reads it |
| GPIO buttons | **Not wired** | GP0-7, GP14-22, GP27-28 all free |
| Display SPI | **Occupied** | GP8-13 (don't touch) |
| ADC | **Occupied** | GP26 (PRNG seed) |

**Key insight:** The Pico already has a bidirectional USB serial channel. We don't need hardware buttons to start — we can send single-character commands from the PC keyboard over serial and have the firmware react immediately.

---

## Three Options

### Option A: Serial Command Mode (Recommended — Start Here)

**What:** Type single keys in a terminal (or DevTool serial monitor) → Pico receives them over USB CDC → firmware changes mood/expression/body state instantly.

**Effort:** ~30 lines of C added to the main loop. No hardware changes. No new firmware variant needed.

**How it works:**
1. Replace `sleep_ms(4000)` with a polling loop that checks for serial input every 50ms
2. On keypress, change mood/expression/body state and re-render immediately
3. No keypress for 4 seconds → auto-advance frame as normal

```
Main loop (modified):
    for each 50ms tick within the 4-second frame window:
        ch = getchar_timeout_us(50000)   // 50ms poll
        if ch != TIMEOUT:
            handle_command(ch)
            re-render immediately
    auto-advance frame
```

**Pros:**
- Zero hardware needed — works right now with existing USB cable
- Full keyboard available (26+ letters, numbers, arrows via escape sequences)
- Easy to extend — add new commands without re-wiring anything
- DevTool can send commands programmatically too
- Can log all state transitions via printf

**Cons:**
- Requires terminal/DevTool open on PC
- Not standalone (tethered to computer)
- ~50ms input latency (imperceptible)

---

### Option B: GPIO Button Array

**What:** Wire 3-5 tactile buttons to free GPIO pins. Firmware reads them via polling or interrupts.

**Effort:** Hardware wiring + ~80 lines of C (debounce, pin init, interrupt handlers).

**Free GPIO pins for buttons:**

| Pin | GPIO | Location | Notes |
|-----|------|----------|-------|
| Pin 1 | GP0 | Top-left | Good for button cluster |
| Pin 2 | GP1 | Adjacent | |
| Pin 4 | GP2 | Adjacent | |
| Pin 5 | GP3 | Adjacent | |
| Pin 6 | GP4 | Adjacent | |
| Pin 7 | GP5 | Near USB end | |
| Pin 19 | GP14 | Bottom row | First free after SPI |
| Pin 20 | GP15 | Bottom row | |

**Suggested 5-button layout:**
- **GP0:** Cycle mood forward
- **GP1:** Cycle mood backward
- **GP2:** Trigger animation / re-render
- **GP3:** Toggle body motion on/off
- **GP4:** Random mood

**Debounce:** 20ms software debounce with `to_ms_since_boot()` timestamp comparison.

**Pros:**
- Standalone — no PC needed
- Physical, tactile feedback
- Low latency (~20ms debounce)

**Cons:**
- Needs hardware (buttons, wires, possibly resistors)
- Limited to number of physical buttons
- Must re-flash firmware to change button mappings

---

### Option C: Hybrid (Serial + Buttons)

**What:** Implement both. Serial commands for development, GPIO buttons for standalone use. Same internal `handle_command()` function — two input sources.

**Effort:** Option A + Option B combined. Shared command handler.

**This is the end goal**, but start with Option A to unblock development immediately.

---

## Option A: Detailed Key Mapping

### Mood Selection (Direct)

| Key | Action | Mood ID |
|-----|--------|---------|
| `n` | Normal | 0 |
| `w` | Weird | 1 |
| `u` | Unhinged | 2 |
| `a` | Angry | 3 |
| `s` | Sad | 4 |
| `c` | Chaotic | 5 |
| `h` | Hungry | 6 |
| `t` | Tired | 7 |
| `p` | Slap Happy | 8 |
| `l` | Lazy | 9 |
| `f` | Fat | 10 |
| `k` | Chill | 11 |
| `y` | Creepy | 12 |

### Mood Cycling

| Key | Action |
|-----|--------|
| `]` | Next mood (wraps 12 → 0) |
| `[` | Previous mood (wraps 0 → 12) |
| `r` | Random mood |

### Expression Override (Manual Frame Control)

| Key | Action |
|-----|--------|
| `0` | Force SMIRK mouth |
| `1` | Force OPEN mouth |
| `2` | Force SMILE mouth |
| `3` | Force WEIRD mouth |
| `4` | Force UNHINGED mouth |
| `5` | Force ANGRY mouth |
| `6` | Force SAD mouth |
| `7` | Force CHAOTIC mouth |
| `8` | Force HUNGRY mouth |
| `9` | Force TIRED mouth |

### Animation Control

| Key | Action |
|-----|--------|
| `.` | Step one frame forward (manual advance) |
| `,` | Step one frame backward |
| `SPACE` | Pause/resume auto-cycle |
| `+` | Speed up frame rate (halve delay) |
| `-` | Slow down frame rate (double delay) |

### Body Motion (Future — For When Body Anims Are Implemented)

| Key | Action |
|-----|--------|
| `b` | Toggle body motion on/off |
| `j` | Trigger body jitter |
| `d` | Trigger body droop/slump |
| `g` | Trigger body sway |
| `x` | Reset body to default position |

### Quote Control

| Key | Action |
|-----|--------|
| `q` | Next random quote |
| `Q` | Print current quote to serial |

### System

| Key | Action |
|-----|--------|
| `?` | Print help (all key mappings) to serial |
| `!` | Print current state (mood, expression, frame, body) to serial |
| `~` | Full display refresh (fix ghosting) |

---

## Firmware Changes Required (Option A)

### 1. Add state variables

```c
/* Interactive control state */
static uint8_t current_mood = MOOD_NORMAL;
static int8_t  expr_override = -1;     /* -1 = use cycle, 0-14 = forced */
static bool    auto_advance = true;
static uint32_t frame_delay_ms = 4000;
static bool    body_motion = false;
static bool    paused = false;
```

### 2. Add command handler

```c
static void handle_command(int ch) {
    switch (ch) {
        /* Direct mood selection */
        case 'n': current_mood = MOOD_NORMAL;   break;
        case 'a': current_mood = MOOD_ANGRY;    break;
        case 's': current_mood = MOOD_SAD;       break;
        // ... etc for all moods

        /* Cycling */
        case ']': current_mood = (current_mood + 1) % 13; break;
        case '[': current_mood = (current_mood + 12) % 13; break;
        case 'r': current_mood = rng_next() % 13; break;

        /* Expression override */
        case '0': case '1': case '2': case '3': case '4':
        case '5': case '6': case '7': case '8': case '9':
            expr_override = ch - '0'; break;

        /* Animation */
        case ' ': paused = !paused; break;
        case '.': frame_idx++; break;
        case '+': if (frame_delay_ms > 500) frame_delay_ms /= 2; break;
        case '-': if (frame_delay_ms < 16000) frame_delay_ms *= 2; break;

        /* System */
        case '?': print_help(); break;
        case '!': print_state(); break;
        case '~': EPD_Init(); EPD_Display(display_buf); break;

        default: break;
    }
    printf("-> mood=%d expr_ovr=%d frame=%lu\n",
           current_mood, expr_override, (unsigned long)frame_idx);
}
```

### 3. Replace main loop

```c
while (true) {
    /* Determine expression */
    uint8_t expr;
    if (expr_override >= 0)
        expr = (uint8_t)expr_override;
    else {
        const uint8_t *cycle = mood_cycle(current_mood);
        expr = cycle[frame_idx % 4];
    }

    /* Pick quote matching current mood */
    // ... existing quote selection logic, filtered by current_mood

    /* Render */
    render_frame(q, expr);
    transpose_to_display();
    EPD_Partial(display_buf);

    /* Poll for serial input during frame delay */
    uint32_t elapsed = 0;
    while (elapsed < frame_delay_ms) {
        int ch = getchar_timeout_us(50000);  /* 50ms poll */
        if (ch != PICO_ERROR_TIMEOUT) {
            handle_command(ch);
            break;  /* re-render immediately */
        }
        elapsed += 50;
        if (paused) elapsed = 0;  /* stay in loop when paused */
    }

    if (!paused && auto_advance)
        frame_idx++;
}
```

---

## DevTool Integration (Optional Enhancement)

The DevTool Python app could add a keyboard listener panel:

```
┌─────────────────────────────────────┐
│  Octopus Remote Control             │
│                                     │
│  Mood: [ANGRY] (a)    Frame: 2/4   │
│  Expr: [cycle]        Body: OFF    │
│                                     │
│  [n]ormal [w]eird [u]nhinged       │
│  [a]ngry  [s]ad   [c]haotic        │
│  [h]ungry [t]ired [p]slaphappy     │
│  [l]azy   [f]at   [k]chill [y]creepy│
│                                     │
│  [space] pause  [.] step  [r]andom │
│  [[] prev  []] next  [?] help      │
└─────────────────────────────────────┘
```

This would just be a thin wrapper that sends the character over the existing serial connection — `ser.write(b'a')` to switch to angry, etc.

---

## Implementation Plan

| Step | Task | Depends On |
|------|------|------------|
| 1 | Create `interactive-octopus/` firmware variant (copy sassy-octopus) | — |
| 2 | Add state variables + `handle_command()` | Step 1 |
| 3 | Replace `sleep_ms(4000)` with polling loop | Step 2 |
| 4 | Test: open `minicom`/`screen` at 115200 → type keys → watch display | Step 3 |
| 5 | Add `print_help()` and `print_state()` for `?` and `!` keys | Step 3 |
| 6 | Add expression override (`0`-`9` keys) | Step 3 |
| 7 | Add frame stepping (`.`, `,`) and speed control (`+`, `-`) | Step 3 |
| 8 | Add body motion keys (once body anims exist) | Body anim implementation |
| 9 | (Optional) Add DevTool keyboard control panel | Step 4 |
| 10 | (Future) Add GPIO button input alongside serial | Hardware available |

---

## Quick-Start Test (After Firmware Is Built)

```bash
# Flash the interactive-octopus.uf2 to the Pico, then:

# Option 1: minicom
minicom -b 115200 -D /dev/ttyACM0

# Option 2: screen
screen /dev/ttyACM0 115200

# Option 3: picocom (simplest)
picocom -b 115200 /dev/ttyACM0

# Then just type:
# a     → angry face
# s     → sad face
# ]     → next mood
# .     → step frame
# space → pause
# ?     → print all commands
```

---

## GPIO Pinout Quick Reference (For Future Button Phase)

```
                     ┌───────────┐
 [BTN0]  GP0  ─  1  ─┤ ◯     ◯ ├─  40  ─  VBUS
 [BTN1]  GP1  ─  2  ─┤           ├─  39  ─  VSYS
          GND ─  3  ─┤           ├─  38  ─  GND
 [BTN2]  GP2  ─  4  ─┤           ├─  37  ─  3V3_EN
 [BTN3]  GP3  ─  5  ─┤   PICO    ├─  36  ─  3V3 (display VCC)
 [BTN4]  GP4  ─  6  ─┤           ├─  35  ─  ADC_VREF
          GP5 ─  7  ─┤           ├─  34  ─  GP28 (free)
          GND ─  8  ─┤           ├─  33  ─  GND
          GP6 ─  9  ─┤           ├─  32  ─  GP27 (free)
          GP7 ─ 10  ─┤           ├─  31  ─  GP26 (ADC → PRNG)
 [DC]    GP8  ─ 11  ─┤           ├─  30  ─  RUN
 [CS]    GP9  ─ 12  ─┤           ├─  29  ─  GP22 (free)
          GND ─ 13  ─┤           ├─  28  ─  GND
 [CLK]   GP10 ─ 14  ─┤           ├─  27  ─  GP21 (free)
 [MOSI]  GP11 ─ 15  ─┤           ├─  26  ─  GP20 (free)
 [RST]   GP12 ─ 16  ─┤           ├─  25  ─  GP19 (free)
 [BUSY]  GP13 ─ 17  ─┤           ├─  24  ─  GP18 (free)
          GND ─ 18  ─┤           ├─  23  ─  GND
 [free]  GP14 ─ 19  ─┤           ├─  22  ─  GP17 (free)
 [free]  GP15 ─ 20  ─┤ ◯     ◯ ├─  21  ─  GP16 (free)
                     └───────────┘
```

**Buttons → GP0-GP4** with internal pull-up (`gpio_pull_up()`), active-low (button connects pin to GND).

---

*Last updated: 2026-04-12*
