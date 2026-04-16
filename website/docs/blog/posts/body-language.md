---
date: 2026-04-12
authors:
  - rompasaurus
categories:
  - Firmware
  - Design
slug: body-language-animations
---

# Body Language — Custom Body Shapes and Movement Per Emotion

The face was done. 16 distinct expressions. But the body was the same for every mood — a static black blob. Today the octopus learned to move, and two moods got entirely new body shapes. Fat is fat. Lazy lounges. Angry trembles. Chaotic distorts. The body finally matches the face.

<!-- more -->

## The Transform System

Every frame, before drawing anything, the firmware calls `setup_body_transform(mood, frame_idx)`. This function sets four global parameters that affect every subsequent pixel operation:

- **body_dx / body_dy** — shifts the entire octopus horizontally or vertically
- **body_x_expand** — widens or narrows every body span (positive = fatter, negative = thinner)
- **wobble_amp / wobble_freq / wobble_phase** — applies a per-row sinusoidal horizontal offset (makes the body wavy)

These transforms are baked into `px_set_off()` and `px_clr_off()`, so they affect the body, eyes, mouth — everything moves together. No separate animation system needed.

```c
static inline void px_set_off(int x, int y) {
    px_set(x + body_dx + row_wobble(y), y + Y_OFF + body_dy);
}
```

## What Each Mood Does

| Mood | dx | dy | x_expand | Wobble | Visual Effect |
|------|----|----|----------|--------|---------------|
| Normal | 0 | sin(f) | 0 | none | Gentle breathing bob |
| Angry | 0 | -1 | +2 | 0.5 amp | Puffed up, slight tremble |
| Sad | 0 | +3 | -1 | none | Drooped down, deflated |
| Chaotic | sin | sin | 0 | 3 amp | Wild wavy distortion |
| Weird | sin | 0 | 0 | 1.5 amp | Lean + body wave |
| Tired | 0 | +2 | -1 | none | Sagging, melting |
| Slap Happy | sin | 0 | 0 | 2 amp | Drunk sway |
| Excited | 0 | 3*sin | 0 | none | Bouncing up and down |
| Creepy | 0 | 0 | 2*sin | none | Rhythmic expand/contract |
| Homesick | 0 | +1 | -2 | none | Curled inward, smaller |

The `f` value is `frame_idx * PI / 2`, so each frame steps the sine by 90 degrees. Over 4 frames you get one full oscillation.

## Custom Bodies: Fat and Lazy

Two moods needed more than transforms — they needed entirely different body silhouettes.

### Fat Octopus

The standard body has a head dome ~52px wide that tapers to a waist before the tentacles. The fat body:

- Starts 2 rows higher (bigger dome)
- Widens to 60px at peak (+5px per side)
- Has **no waist taper** — stays wide all the way through
- Tentacles are each 2px wider (barely any gap between them)

The visual difference is immediate. Standard octopus has visible space between tentacles and a defined waist. Fat octopus is a continuous mass of chonk.

### Lazy Octopus

This one went through two iterations. The first attempt was a "French woman reclining" pose — asymmetric body sloping rightward with a tentacle draped across the belly. It looked weird. Overcomplicated. Hard to read at 1-bit resolution.

The second iteration (the one that shipped) is much simpler: **same head and body, but all 5 tentacles sweep to the right** instead of hanging straight down. The cheek area tapers rightward to smooth the transition. It reads immediately as "sitting on its side, legs draped over."

Sometimes the clever solution is just the simple one.

## The RLE Format

The body is stored as run-length encoded spans:

```c
static const uint8_t body_rle[] = {
    10,1, 22,48,   // y=10: 1 span from x=22 to x=48
    11,1, 18,52,   // y=11: 1 span from x=18 to x=52
    // ... head rows ...
    55,5, 10,17, 21,28, 32,39, 43,50, 54,61,  // y=55: 5 tentacle spans
    // ... tentacle rows zigzag ...
    0xFF           // terminator
};
```

Standard body: 197 bytes. Fat body: 215 bytes. Lazy body: 220 bytes. Three entirely different silhouettes for less data than a single tweet.

## Verifying Across Implementations

The body rendering exists in three places: the C firmware (runs on the Pico), the Python DevTool (preview emulator), and the C-faithful preview renderer (generates static PNGs). All three need to match pixel-for-pixel, or what you see in the DevTool won't match what appears on the device.

We built a comparison pipeline that renders all 16 moods from both C and Python logic, then diffs them pixel-by-pixel. 10 of 16 match exactly. The other 6 differ by fewer than 256 pixels — all at wobble boundaries where Python's `math.sin()` and C's `sinf()` round differently. Visually identical.

## What's Next

The octopus has a face, a body, and personality. It can emote, animate, and speak. What it can't do yet is *react*. Phase 2 will add user input — buttons or serial commands that let you interact with the octopus and trigger emotional state changes. The keyboard input mapping is already planned. The octopus is ready to listen.
