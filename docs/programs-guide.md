# Dilder Programs Guide

A comprehensive reference for every firmware program in the Dilder project. Each program runs on a Raspberry Pi Pico W with a Waveshare 2.13" e-ink display and renders an animated octopus with mood-specific expressions, body animations, and curated quotes.

---

## Table of Contents

- [Overview](#overview)
- [How Programs Work](#how-programs-work)
  - [Display Layout](#display-layout)
  - [Animation Cycle](#animation-cycle)
  - [Quote System](#quote-system)
  - [Building and Flashing](#building-and-flashing)
- [Utility Programs](#utility-programs)
  - [Hello World](#hello-world)
  - [Hello World Serial](#hello-world-serial)
  - [Image Receiver](#image-receiver)
- [Emotional State Programs](#emotional-state-programs)
  - [Sassy Octopus](#sassy-octopus)
  - [Supportive Octopus](#supportive-octopus)
  - [Angry Octopus](#angry-octopus)
  - [Conspiratorial Octopus](#conspiratorial-octopus)
  - [Sad Octopus](#sad-octopus)
  - [Chaotic Octopus](#chaotic-octopus)
  - [Hungry Octopus](#hungry-octopus)
  - [Tired Octopus](#tired-octopus)
  - [Slap Happy Octopus](#slap-happy-octopus)
  - [Lazy Octopus](#lazy-octopus)
  - [Fat Octopus](#fat-octopus)
  - [Chill Octopus](#chill-octopus)
  - [Creepy Octopus](#creepy-octopus)
  - [Excited Octopus](#excited-octopus)
  - [Nostalgic Octopus](#nostalgic-octopus)
  - [Homesick Octopus](#homesick-octopus)
- [Mood Selector (Interactive)](#mood-selector-interactive)
  - [Serial Input Reference](#serial-input-reference)
  - [Connecting to the Pico](#connecting-to-the-pico)
- [Program Comparison Table](#program-comparison-table)

---

## Overview

The `dev-setup/` directory contains **19 programs** total:

- **3 utility programs** for hardware testing and development
- **16 emotional state programs** each featuring a unique octopus personality
- **1 interactive mood selector** that combines all 16 emotional states with keyboard control

All emotional state programs share the same core rendering engine: a runtime pixel renderer that composites body, eyes, mouth, chat bubble, and text onto a 250x122px 1-bit canvas, then pushes it to the e-ink display using partial refresh (~4 second frame cycle).

---

## How Programs Work

### Display Layout

The 250x122 pixel landscape canvas is organized as:

```
+--------------------------------------------------+
|              APRIL 12, 2026  3:47 PM             |  <-- Clock header (y=1)
|                                                  |
|   @@@@@@     +----------------------------+      |
|  @@    @@    | QUOTE TEXT GOES HERE AND   |      |  <-- Chat bubble (y=17, 170x70)
|  @ O  O @   | WRAPS AUTOMATICALLY TO     |      |
|  @  __  @   | FIT INSIDE THE BUBBLE      |      |
|  @@    @@   |                            |      |
|   @@@@@@ /  +----------------------------+      |
|    |||||       ~ SASSY OCTOPUS ~                 |  <-- Tagline (below bubble)
+--------------------------------------------------+
```

- **Clock header:** Date and time from RTC, centered at y=1
- **Octopus body:** Left side, rendered with RLE-decoded body + mood-specific transforms
- **Eyes:** White sockets with mood-specific pupils (hearts, stars, spirals, etc.)
- **Mouth:** 18 distinct expressions cycled per mood
- **Chat bubble:** Right side, rounded rectangle with speech tail pointing to octopus
- **Quote text:** Word-wrapped 5x7 bitmap font inside the bubble
- **Tagline:** Mood name centered below the bubble

### Animation Cycle

Each mood defines a 4-frame expression cycle. Every ~4 seconds:

1. The current expression is drawn from the cycle (e.g., Smirk -> Open -> Smile -> Open)
2. On every OPEN mouth frame, a new random quote is selected
3. The body transform is applied (shift, wobble, expand based on mood)
4. The frame is rendered to the landscape buffer, transposed to portrait, and pushed via partial refresh

### Quote System

Quotes are stored in `quotes.h` as a static array of `{text, mood_id}` structs. Each program includes only its relevant quotes (except Mood Selector which includes all 823). The DevTool auto-generates `quotes.h` from the Python quote lists in `devtool.py`.

### Building and Flashing

**Via DevTool GUI:**
1. Open DevTool: `python3 DevTool/devtool.py`
2. Select the program from the dropdown
3. Select display variant (V2/V3/V3a/V4)
4. Click "Build & Flash to Pico"
5. Put Pico in BOOTSEL mode (hold BOOTSEL + plug USB)
6. DevTool copies the `.uf2` to the mounted drive

**Via command line:**
```bash
cd dev-setup/
docker compose run --rm build-sassy-octopus bash -c \
  "mkdir -p build && cd build && cmake .. -DDISPLAY_VARIANT=V3 && make -j4"
# Copy build/sassy_octopus.uf2 to the Pico in BOOTSEL mode
cp sassy-octopus/build/sassy_octopus.uf2 /run/media/$USER/RPI-RP2/
```

---

## Utility Programs

### Hello World

**Directory:** `dev-setup/hello-world/`

Basic e-ink display test. Draws a simple pattern to verify the display is wired correctly and the SPI bus is working. This is the first program you should flash to confirm hardware is functional.

**Use case:** Hardware verification after initial wiring.

### Hello World Serial

**Directory:** `dev-setup/hello-world-serial/`

Serial-only test program. Prints messages over USB CDC at 115200 baud without driving the display. Useful for verifying the USB serial connection works before flashing display firmware.

**Use case:** Verify USB serial communication before display testing.

### Image Receiver

**Directory:** `dev-setup/img-receiver/`

Receives raw 1-bit bitmap data over USB serial and displays it on the e-ink screen. Used by the DevTool's display emulator to push custom images to the hardware.

**Use case:** Push arbitrary images from DevTool to the physical display.

---

## Emotional State Programs

Each program below runs autonomously once flashed. The octopus cycles through its personality-specific quotes, changing expression and quote every ~4 seconds.

### Sassy Octopus

**Directory:** `dev-setup/sassy-octopus/` | **Quotes:** 196 | **Default Mood:** Normal

![Sassy](../assets/emotion-previews/normal.png)

A snarky octopus with attitude. Delivers observations like "WIFI IS JUST SPICY AIR" and "I DONT HAVE BONES AND THATS A FLEX." The default personality with centered pupils, smirk/smile mouth cycle, and gentle breathing body animation.

| Feature | Details |
|---------|---------|
| Eyes | Centered pupils with white highlights |
| Mouth Cycle | Smirk -> Open -> Smile -> Open |
| Body | Gentle 1px vertical breathing bob |
| Quotes | Snarky observations, food hot takes, self-aware flexes |

### Supportive Octopus

**Directory:** `dev-setup/supportive-octopus/` | **Quotes:** 160 | **Default Mood:** Normal

![Supportive](../assets/emotion-previews/supportive.png)

Aggressively supportive. Uses the same normal face as Sassy but delivers chaotic affirmations like unhinged pep talks. Some quotes override to weird/unhinged moods for visual variety.

| Feature | Details |
|---------|---------|
| Eyes | Same as Sassy (centered, normal) |
| Mouth Cycle | Smirk -> Open -> Smile -> Open |
| Body | Gentle breathing (same as Sassy) |
| Quotes | Unhinged pep talks, chaotic affirmations, spicy encouragement |

### Angry Octopus

**Directory:** `dev-setup/angry-octopus/` | **Quotes:** 45 | **Default Mood:** Angry

![Angry](../assets/emotion-previews/angry.png)

Furious but adorable. V-shaped eyebrows slant inward, pupils glare toward the nose, and the tight frown shows zero patience. Body puffs up 2px wider with a slight tremble.

| Feature | Details |
|---------|---------|
| Eyes | Pupils shifted inward + down (glaring), thick V-shaped brow arcs |
| Mouth Cycle | Frown -> Open -> Frown -> Frown |
| Body | Puffed up +2px wider, 0.5px wobble tremble |
| Quotes | Rants about shrimp theft, Poseidon, and tentacle violence |

### Conspiratorial Octopus

**Directory:** `dev-setup/conspiratorial-octopus/` | **Quotes:** 47 | **Default Mood:** Weird

![Conspiratorial](../assets/emotion-previews/weird.png)

Tinfoil hat energy. Misaligned pupils (one up-left, one down-right) give a shifty look. The wavy sine-wave mouth and swaying body sell the paranoia.

| Feature | Details |
|---------|---------|
| Eyes | Misaligned: left up-left, right down-right |
| Mouth Cycle | Wavy sine -> Open -> Wavy -> Smile |
| Body | Lean/sway +/-3px, subtle row distortion |
| Quotes | Government conspiracies, simulation theory, birds aren't real |

### Sad Octopus

**Directory:** `dev-setup/sad-octopus/` | **Quotes:** 35 | **Default Mood:** Sad

![Sad](../assets/emotion-previews/sad.png)

Droopy eyes looking at the floor with inverted brow arcs (high inside, low outside). The gentle frown and deflated body convey genuine melancholy.

| Feature | Details |
|---------|---------|
| Eyes | Downward-looking pupils, droopy brow arcs |
| Mouth Cycle | Frown -> Open -> Frown -> Smile |
| Body | Drooped +3px down, deflated 1px narrower |
| Quotes | Existential ocean sadness, melodramatic but relatable |

### Chaotic Octopus

**Directory:** `dev-setup/chaotic-octopus/` | **Quotes:** 40 | **Default Mood:** Chaotic

![Chaotic](../assets/emotion-previews/chaotic.png)

Pure entropy. Spiral ring pupils (concentric circles), a zigzag lightning-bolt mouth, and wild wavy body distortion. The expression cycle is itself chaotic: zigzag -> open -> unhinged scream -> wobbly.

| Feature | Details |
|---------|---------|
| Eyes | Spiral ring pupils (concentric circles with center dot) |
| Mouth Cycle | Zigzag -> Open -> Unhinged -> Wobbly |
| Body | Wild 3px sine wobble per row, shifting phase |
| Quotes | Nonsensical fever-dream energy, entropy incarnate |

### Hungry Octopus

**Directory:** `dev-setup/hungry-octopus/` | **Quotes:** 30 | **Default Mood:** Hungry

![Hungry](../assets/emotion-previews/hungry.png)

Wide eyes staring upward at imaginary food, with a drooling open mouth (oval + drool drops below). Every thought is about snacks.

| Feature | Details |
|---------|---------|
| Eyes | Pupils shifted upward (staring at food) |
| Mouth Cycle | Drool mouth -> Open -> Drool -> Smile |
| Body | Slight upward shift (-2px), breathing |
| Quotes | Taco dreams, snack philosophy, selling hearts for pizza |

### Tired Octopus

**Directory:** `dev-setup/tired-octopus/` | **Quotes:** 30 | **Default Mood:** Tired

![Tired](../assets/emotion-previews/tired.png)

Half-closed eyelids cover the top of each eye socket, tiny sleepy pupils peek out below. The tall yawn mouth is open wide vertically. Running on zero sleep.

| Feature | Details |
|---------|---------|
| Eyes | Half-closed lids (top half black), tiny pupils low in slit |
| Mouth Cycle | Yawn -> Open -> Yawn -> Yawn |
| Body | Slouched +2px down, deflated 1px narrower |
| Quotes | Existential exhaustion, one brain cell, nap theology |

### Slap Happy Octopus

**Directory:** `dev-setup/slaphappy-octopus/` | **Quotes:** 30 | **Default Mood:** Slap Happy

![Slap Happy](../assets/emotion-previews/slaphappy.png)

One eye squinted shut (white slit), one manic oversized pupil. The wide wobbly grin with sine wobble completes the delirious look. Everything is hilarious for no reason.

| Feature | Details |
|---------|---------|
| Eyes | Left squinted shut (slit), right oversized pupil |
| Mouth Cycle | Wobbly grin -> Open -> Wobbly grin -> Smile |
| Body | Bouncing +/-3px lateral sway, 2px row wobble |
| Quotes | Delirious giggling, everything is hilarious |

### Lazy Octopus

**Directory:** `dev-setup/lazy-octopus/` | **Quotes:** 30 | **Default Mood:** Lazy

![Lazy](../assets/emotion-previews/lazy.png)

Nearly-closed slit eyes (only bottom sliver visible), flat horizontal line mouth. Custom body sits on its side with all tentacles draped to the right. Proudly doing nothing.

| Feature | Details |
|---------|---------|
| Eyes | Lids cover most of socket, barely-visible dots low in slit |
| Mouth Cycle | Flat line -> Flat line -> Flat line -> Open |
| Body | Custom side-sitting pose, tentacles drape right, +3px sag |
| Quotes | Philosophical laziness, zero motivation manifestos |

### Fat Octopus

**Directory:** `dev-setup/fat-octopus/` | **Quotes:** 30 | **Default Mood:** Fat

![Fat](../assets/emotion-previews/fat.png)

Custom wider body: dome starts 2 rows earlier, +5px per side at peak, no waist taper, thicker tentacles. Happy wide pupils and a satisfied smile with puffed cheeks. Proudly round.

| Feature | Details |
|---------|---------|
| Eyes | Wider pupils (r=3), happy and satisfied |
| Mouth Cycle | Cheek-puff smile -> Open -> Cheek-puff smile -> Smile |
| Body | Custom fat body RLE: wider dome, no waist, thick tentacles |
| Quotes | Food-positive celebrations, proudly round philosophy |

### Chill Octopus

**Directory:** `dev-setup/chill-octopus/` | **Quotes:** 30 | **Default Mood:** Chill

![Chill](../assets/emotion-previews/chill.png)

Side-glancing cool pupils shifted right, relaxed asymmetric half-smile. Unbothered zen vibes with gentle 1px lateral sway.

| Feature | Details |
|---------|---------|
| Eyes | Pupils shifted right (looking to the side) |
| Mouth Cycle | Half-smile -> Open -> Half-smile -> Smile |
| Body | Gentle 1px sway, lowered 1px |
| Quotes | Stoner philosopher energy, going with the flow |

### Creepy Octopus

**Directory:** `dev-setup/creepy-octopus/` | **Quotes:** 30 | **Default Mood:** Creepy

![Creepy](../assets/emotion-previews/creepy.png)

Heart-shaped pupils in each eye socket, wide open smile with a tongue hanging out (filled oval + tongue bump below). Flirty tentacle energy.

| Feature | Details |
|---------|---------|
| Eyes | Heart-shaped pupils (bumps + taper + point) |
| Mouth Cycle | Tongue-out smile -> Open -> Tongue-out -> Smile |
| Body | Width pulses +/-2px (confident strut) |
| Quotes | Ocean romance, goofy innuendo, tentacle flirting |

### Excited Octopus

**Directory:** `dev-setup/excited-octopus/` | **Quotes:** 30 | **Default Mood:** Excited

![Excited](../assets/emotion-previews/excited.png)

Star/sparkle cross-shaped pupils with diagonal tips in each eye. The wide open smile curves from edge to edge. Bouncing body with +/-3px vertical oscillation.

| Feature | Details |
|---------|---------|
| Eyes | Star/sparkle cross pupils with diagonal tips |
| Mouth Cycle | Wide grin -> Open -> Wide grin -> Smile |
| Body | Bouncing up/down +/-3px |
| Quotes | Maximum hype, caps lock enthusiasm, bouncing energy |

### Nostalgic Octopus

**Directory:** `dev-setup/nostalgic-octopus/` | **Quotes:** 30 | **Default Mood:** Nostalgic

![Nostalgic](../assets/emotion-previews/nostalgic.png)

Pupils shifted up and to the right (remembering), gentle small half-smile. The body sways slowly with a slight tilt, as if lost in thought.

| Feature | Details |
|---------|---------|
| Eyes | Pupils up-right (looking into the distance) |
| Mouth Cycle | Small half-smile -> Open -> Half-smile -> Smile |
| Body | Slow 2px lateral sway + slight vertical drift |
| Quotes | Wistful ocean memories, back-in-my-day nostalgia |

### Homesick Octopus

**Directory:** `dev-setup/homesick-octopus/` | **Quotes:** 30 | **Default Mood:** Homesick

![Homesick](../assets/emotion-previews/homesick.png)

Watery eyes with tear drop pixels below each socket, wobbly trying-not-to-cry mouth line. The body droops and narrows, conveying deflation and longing.

| Feature | Details |
|---------|---------|
| Eyes | Lowered pupils, tear drops below each eye |
| Mouth Cycle | Wobbly line -> Open -> Wobbly -> Wobbly |
| Body | Drooped +1px, narrowed -2px, bittersweet |
| Quotes | Missing the deep ocean, longing for home |

---

## Mood Selector (Interactive)

**Directory:** `dev-setup/mood-selector/` | **Quotes:** 823 (all moods combined)

The Mood Selector combines all 16 emotional states into a single interactive firmware. Instead of being locked to one personality, you browse through moods using keyboard input over USB serial.

**On the display:**
- Clock header at top center
- Octopus with the currently selected mood's face, body animation, and a random quote
- Bottom center: `< MOOD_NAME >` with `<` and `>` arrows indicating left/right navigation

**How to use:**
1. Flash `mood_selector.uf2` to the Pico
2. Connect to serial (see [Connecting to the Pico](#connecting-to-the-pico))
3. Press `[` or `]` to cycle through moods
4. Press a letter key for direct mood selection
5. Press `?` to see all available commands

### Serial Input Reference

Connect to the Pico's USB serial port at 115200 baud. All commands are single keystrokes.

#### Mood Navigation

| Key | Action |
|-----|--------|
| `[` | Previous mood (left) -- wraps around |
| `]` | Next mood (right) -- wraps around |
| `,` | Previous mood (left) -- alternate key |
| `.` | Next mood (right) -- alternate key |
| `r` | Jump to a random mood |

#### Direct Mood Selection

| Key | Mood | Key | Mood |
|-----|------|-----|------|
| `n` | Sassy | `w` | Weird |
| `u` | Unhinged | `a` | Angry |
| `s` | Sad | `c` | Chaotic |
| `h` | Hungry | `t` | Tired |
| `p` | Slap Happy | `l` | Lazy |
| `f` | Fat | `k` | Chill |
| `y` | Creepy | `e` | Excited |
| `o` | Nostalgic | `m` | Homesick |

#### Other Commands

| Key | Action |
|-----|--------|
| `q` | Load a new random quote (same mood) |
| `?` | Print the full help menu to serial |

All keys are case-insensitive (e.g., `A` and `a` both select Angry).

#### Serial Output

When you press a navigation key, the serial monitor shows:

```
----------------------------------------
  KEY ']' pressed  |  >> RIGHT  |  SASSY --> WEIRD
  Now showing: < WEIRD >  (2/16)
----------------------------------------
```

Each animation frame also logs:

```
Frame 5  |  < ANGRY > (4/16)  |  "THE AUDACITY OF THIS ENTIRE OCEAN."
```

### Connecting to the Pico

The Pico communicates over USB CDC serial at 115200 baud. Only one program can hold the port at a time.

**Find the serial port:**
```bash
ls /dev/serial/by-id/
# Look for: usb-Raspberry_Pi_Pico_XXXXX-if00 -> ../../ttyACM0
```

**Connect with screen:**
```bash
screen /dev/ttyACM0 115200
# Exit: Ctrl+A then K then Y
```

**Connect with picocom:**
```bash
picocom -b 115200 /dev/ttyACM0
# Exit: Ctrl+A then Ctrl+X
```

**Connect with minicom:**
```bash
minicom -D /dev/ttyACM0 -b 115200
# Exit: Ctrl+A then X
```

**Via DevTool:** The DevTool's Serial Monitor tab connects automatically. Close it before using a terminal, as only one program can hold the port.

> **Note:** If the Pico was just flashed, it will reboot and appear as a serial device within ~1 second. If no device appears at `/dev/ttyACM0`, try unplugging and re-plugging the USB cable (without holding BOOTSEL).

---

## Program Comparison Table

| Program | Quotes | Body | Eyes | Mouth | Body Animation |
|---------|--------|------|------|-------|----------------|
| Sassy | 196 | Standard | Normal | Smirk/Smile | Breathing bob |
| Supportive | 160 | Standard | Normal | Smirk/Smile | Breathing bob |
| Angry | 45 | Standard | Glare + V-brows | Frown | Puffed +2px, tremble |
| Conspiratorial | 47 | Standard | Misaligned | Sine wave | Sway +/-3px |
| Sad | 35 | Standard | Down + droopy brows | Gentle frown | Drooped +3px, -1px |
| Chaotic | 40 | Standard | Spiral rings | Zigzag lightning | Wild 3px wobble |
| Hungry | 30 | Standard | Up (staring) | Drool mouth | Slight upward shift |
| Tired | 30 | Standard | Half-closed lids | Yawn oval | Slouched +2px |
| Slap Happy | 30 | Standard | One squint, one manic | Wobbly grin | Bounce +/-3px |
| Lazy | 30 | Custom (side-sit) | Barely-open slits | Flat line | Sagged, tentacles right |
| Fat | 30 | Custom (wide) | Wide happy | Cheek-puff smile | Width pulse |
| Chill | 30 | Standard | Side-glance | Half-smile | Gentle 1px sway |
| Creepy | 30 | Standard | Heart-shaped | Tongue out | Width pulse +/-2px |
| Excited | 30 | Standard | Star sparkle | Wide open grin | Bounce +/-3px |
| Nostalgic | 30 | Standard | Up-right gaze | Small half-smile | Slow 2px sway |
| Homesick | 30 | Standard | Tears below | Wobbly line | Drooped, -2px narrow |
| **Mood Selector** | **823** | **All** | **All** | **All** | **All (interactive)** |
