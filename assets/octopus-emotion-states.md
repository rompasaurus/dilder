# Octopus Emotion States — Asset Map & Implementation Tracker

> Master reference for all octopus emotional states. Each state maps facial features (eyes, pupils, eyebrows, eyelids, mouth) and body behavior. Use the checkboxes to track implementation progress and the notes column for improvements.

---

## Architecture Overview

- **Canvas:** 250x122px, 1-bit (black/white), landscape, MSB-first packing
- **Rendering:** On-the-fly math (circles, parabolas, sine arcs) — no pre-baked bitmaps
- **Composition order:** Body (RLE) → Eye sockets → Pupils → Brows/Lids → Mouth → Bubble → Text
- **Animation:** 4-frame mouth expression cycle per mood (new quote selected on OPEN frames)
- **Body:** Static RLE silhouette (rows 10–80), includes 5 tentacle columns (rows 55–80)

---

## Facial Feature Components

| Component | Rendering Method | Coordinates |
|-----------|-----------------|-------------|
| **Eye sockets** | Filled circles, r²=16 | Left: (22,25), Right: (48,25) |
| **Pupils** | Per-mood shapes/positions | Varies per state |
| **Eyebrows** | Parametric sine arcs, 18px span, 3px thick | Above eye sockets |
| **Eyelids** | Partial circle fill (top of socket) | Same as sockets |
| **Mouth** | Parabolas, ellipses, sine waves, zigzags | ~(35, 39-41) center |
| **Body** | RLE-encoded black silhouette | Rows 10-80, x range ~8-64 |
| **Tentacles** | 5 column pairs within body RLE | Rows 55-80 |

---

## State Definitions

### 0 — NORMAL

| Feature | Description | Asset Status | Body Motion |
|---------|-------------|:------------:|-------------|
| Eyes | White sockets r²=16 | - [x] Done | — |
| Pupils | Centered, r²=4 at (23,26)/(49,26) + highlights r²=1 at (20,23)/(46,23) | - [x] Done | — |
| Eyebrows | None | N/A | — |
| Eyelids | None | N/A | — |
| Mouth cycle | SMIRK → OPEN → SMILE → OPEN | - [x] Done | — |
| Body motion | Static | - [ ] Planned | Gentle idle sway / breathing |

**Notes:**
- [ ] Add subtle tentacle idle animation (slow wave)
- [ ] Add slight body "breathing" bob (1-2px vertical oscillation)
- _Improvements:_

---

### 1 — WEIRD

| Feature | Description | Asset Status | Body Motion |
|---------|-------------|:------------:|-------------|
| Eyes | Standard white sockets | - [x] Done | — |
| Pupils | Misaligned: left at (21,24), right at (50,28) + standard highlights | - [x] Done | — |
| Eyebrows | None | N/A | — |
| Eyelids | None | N/A | — |
| Mouth cycle | WEIRD → OPEN → WEIRD → SMILE | - [x] Done | — |
| Mouth style | Sine-wave wiggle (3 periods across 24px) | - [x] Done | — |
| Body motion | Static | - [ ] Planned | Random tentacle twitches |

**Notes:**
- [ ] Add asymmetric tentacle movement (each tentacle independent timing)
- [ ] Add occasional body tilt (lean left or right randomly)
- _Improvements:_

---

### 2 — UNHINGED

| Feature | Description | Asset Status | Body Motion |
|---------|-------------|:------------:|-------------|
| Eyes | Standard white sockets | - [x] Done | — |
| Pupils | Tiny pinpricks (2x2 pixels), no highlights | - [x] Done | — |
| Eyebrows | None | N/A | — |
| Eyelids | None | N/A | — |
| Mouth cycle | UNHINGED → OPEN → UNHINGED → OPEN | - [x] Done | — |
| Mouth style | Oversized oval (rx=10, ry=7) + tooth-like bars at top | - [x] Done | — |
| Body motion | Static | - [ ] Planned | Vibrating/shaking tremor |

**Notes:**
- [ ] Add rapid full-body vibration (1px jitter each frame)
- [ ] Add tentacle splaying outward in all directions
- [ ] Consider pupil jitter (alternate between 2 positions)
- _Improvements:_

---

### 3 — ANGRY

| Feature | Description | Asset Status | Body Motion |
|---------|-------------|:------------:|-------------|
| Eyes | Standard white sockets | - [x] Done | — |
| Pupils | Shifted inward+down: left (25,27), right (47,27) — glaring | - [x] Done | — |
| Eyebrows | V-shaped angry arcs: parametric sine, outer high → inner low, 3px thick | - [x] Done | — |
| Eyelids | None | N/A | — |
| Mouth cycle | ANGRY → OPEN → ANGRY → ANGRY | - [x] Done | — |
| Mouth style | Tight inverted parabola frown (15px wide) | - [x] Done | — |
| Body motion | Static | - [ ] Planned | Tensed up, pulsing/swelling |

**Notes:**
- [ ] Add body "puffing up" (expand silhouette 1-2px outward on alternate frames)
- [ ] Add tentacle clenching (curl inward tighter)
- [ ] Consider red tint effect (if display supports it in future)
- _Improvements:_

---

### 4 — SAD

| Feature | Description | Asset Status | Body Motion |
|---------|-------------|:------------:|-------------|
| Eyes | Standard white sockets | - [x] Done | — |
| Pupils | Shifted down: (23,28)/(49,28) — looking at floor | - [x] Done | — |
| Eyebrows | Droopy arcs: inner high → outer low (inverse angry), 3px thick | - [x] Done | — |
| Eyelids | None | N/A | — |
| Mouth cycle | SAD → OPEN → SAD → SMILE | - [x] Done | — |
| Mouth style | Gentle downward curve frown (19px wide) | - [x] Done | — |
| Body motion | Static | - [ ] Planned | Drooping/wilting posture |

**Notes:**
- [ ] Add body slump (shift entire octopus down 2-3px, compress vertically)
- [ ] Add tentacle droop (tentacles hang limp, less spread)
- [ ] Add tear drop animation (pixel falling from eye on some frames)
- _Improvements:_

---

### 5 — CHAOTIC

| Feature | Description | Asset Status | Body Motion |
|---------|-------------|:------------:|-------------|
| Eyes | Standard white sockets | - [x] Done | — |
| Pupils | Spiral/ring eyes: concentric circles (r²=5..9 ring + center dot) | - [x] Done | — |
| Eyebrows | None | N/A | — |
| Eyelids | None | N/A | — |
| Mouth cycle | CHAOTIC → OPEN → UNHINGED → WEIRD | - [x] Done | — |
| Mouth style | Zigzag lightning-bolt (6px period, 24px wide) | - [x] Done | — |
| Body motion | Static | - [ ] Planned | Erratic spinning/bouncing |

**Notes:**
- [ ] Add full body rotation oscillation (tilt back and forth rapidly)
- [ ] Add tentacle flailing (random positions each frame)
- [ ] Add body position jitter (random 1-3px offset each frame)
- [ ] Consider spiral rotation animation for pupils
- _Improvements:_

---

### 6 — HUNGRY

| Feature | Description | Asset Status | Body Motion |
|---------|-------------|:------------:|-------------|
| Eyes | Standard white sockets | - [x] Done | — |
| Pupils | Shifted upward: (23,23)/(49,23) — staring at food | - [x] Done | — |
| Eyebrows | None | N/A | — |
| Eyelids | None | N/A | — |
| Mouth cycle | HUNGRY → OPEN → HUNGRY → SMILE | - [x] Done | — |
| Mouth style | Drooling oval (rx=8, ry=5) + 2 drool drop lines | - [x] Done | — |
| Body motion | Static | - [ ] Planned | Reaching/leaning forward |

**Notes:**
- [ ] Add body lean upward (shift octopus up 1-2px, stretch toward "food")
- [ ] Add tentacle reaching motion (front tentacles extend upward)
- [ ] Add drool drop animation (drops fall frame-by-frame)
- [ ] Add stomach growl body shake (occasional wobble)
- _Improvements:_

---

### 7 — TIRED

| Feature | Description | Asset Status | Body Motion |
|---------|-------------|:------------:|-------------|
| Eyes | Standard white sockets + half-closed lids | - [x] Done | — |
| Pupils | Tiny sleepy dots (3px wide, low in socket) at y=27-28 | - [x] Done | — |
| Eyebrows | None | N/A | — |
| Eyelids | Top half of sockets filled black (dy=-4 to -1) | - [x] Done | — |
| Mouth cycle | TIRED → OPEN → TIRED → TIRED | - [x] Done | — |
| Mouth style | Tall yawn oval (rx=5, ry=7) | - [x] Done | — |
| Body motion | Static | - [ ] Planned | Slow drooping, nodding off |

**Notes:**
- [ ] Add slow body nod (gradual tilt downward over frames, snap back up)
- [ ] Add eyelid flutter (lid position oscillates between frames)
- [ ] Add tentacle sag (limp, dragging appearance)
- [ ] Add "Z" particle floating from head on sleep frames
- _Improvements:_

---

### 8 — SLAPHAPPY

| Feature | Description | Asset Status | Body Motion |
|---------|-------------|:------------:|-------------|
| Eyes | Left: squint shut (socket filled, white slit). Right: oversized pupil (r²=9) | - [x] Done | — |
| Pupils | Left: none (squinted). Right: huge black circle | - [x] Done | — |
| Eyebrows | None | N/A | — |
| Eyelids | Left eye fully covered except center slit | - [x] Done | — |
| Mouth cycle | SLAPHAPPY → OPEN → SLAPHAPPY → SMILE | - [x] Done | — |
| Mouth style | Wide wobbly grin: parabola + sine wobble (4 periods, 27px) | - [x] Done | — |
| Body motion | Static | - [ ] Planned | Wobbly swaying, off-balance |

**Notes:**
- [ ] Add body sway (sine-wave horizontal offset, slow period)
- [ ] Add alternating lean (body tilts left then right)
- [ ] Add tentacle stumble (uneven, drunk-walk tentacle positions)
- [ ] Consider alternating which eye is squinted between frames
- _Improvements:_

---

### 9 — LAZY

| Feature | Description | Asset Status | Body Motion |
|---------|-------------|:------------:|-------------|
| Eyes | Standard sockets + heavy lids (only bottom sliver open) | - [x] Done | — |
| Pupils | Barely visible dots at y=28 in each socket | - [x] Done | — |
| Eyebrows | None | N/A | — |
| Eyelids | Sockets covered dy=-4 to +1 (nearly closed) | - [x] Done | — |
| Mouth cycle | LAZY → LAZY → LAZY → OPEN | - [x] Done | — |
| Mouth style | Flat horizontal line (13px, 2px thick) | - [x] Done | — |
| Body motion | Static | - [ ] Planned | Melted/slouched, barely moving |

**Notes:**
- [ ] Add body "melting" (flatten silhouette: compress top, spread bottom)
- [ ] Add tentacle pooling (tentacles spread flat on ground)
- [ ] Minimal animation — delay between frames should be longer
- [ ] Consider occasional single-tentacle twitch
- _Improvements:_

---

### 10 — FAT

| Feature | Description | Asset Status | Body Motion |
|---------|-------------|:------------:|-------------|
| Eyes | Standard white sockets | - [x] Done | — |
| Pupils | Wider happy pupils, r²=9 at (23,26)/(49,26) | - [x] Done | — |
| Eyebrows | None | N/A | — |
| Eyelids | None | N/A | — |
| Mouth cycle | FAT → OPEN → FAT → SMILE | - [x] Done | — |
| Mouth style | Wide satisfied smile (23px) + cheek puff circles (r²=4) at (23,39)/(47,39) | - [x] Done | — |
| Body motion | Static | - [ ] Planned | Round, content jiggle |

**Notes:**
- [ ] Add body puff (expand silhouette outward 2-3px, rounder shape)
- [ ] Add belly jiggle (body outline wobbles slightly on frame change)
- [ ] Add content tentacle curl (tentacles curl inward, resting)
- [ ] Consider adding food crumb particles near mouth
- _Improvements:_

---

### 11 — CHILL

| Feature | Description | Asset Status | Body Motion |
|---------|-------------|:------------:|-------------|
| Eyes | Standard white sockets | - [x] Done | — |
| Pupils | Side-glancing: shifted right, r²=4 at (25,26)/(51,26) | - [x] Done | — |
| Eyebrows | None | N/A | — |
| Eyelids | None | N/A | — |
| Mouth cycle | CHILL → OPEN → CHILL → SMILE | - [x] Done | — |
| Mouth style | Asymmetric half-smile: quadratic curve, 15px, slight upturn | - [x] Done | — |
| Body motion | Static | - [ ] Planned | Slow float, gentle drift |

**Notes:**
- [ ] Add slow floating motion (body drifts up/down over long cycle)
- [ ] Add relaxed tentacle wave (slow, smooth, in-sync wave pattern)
- [ ] Add subtle lean-back posture (tilt body slightly backward)
- [ ] Consider half-closed eyelids (not as heavy as lazy/tired)
- _Improvements:_

---

### 12 — HORNY

| Feature | Description | Asset Status | Body Motion |
|---------|-------------|:------------:|-------------|
| Eyes | Standard white sockets | - [x] Done | — |
| Pupils | Heart-shaped: 5-point top bumps + taper + bottom point | - [x] Done | — |
| Eyebrows | None | N/A | — |
| Eyelids | None | N/A | — |
| Mouth cycle | HORNY → OPEN → HORNY → SMILE | - [x] Done | — |
| Mouth style | Bottom-half open smile (rx=8, ry=5) + tongue (r²=8, 5px long) | - [x] Done | — |
| Body motion | Static | - [ ] Planned | Excited wiggle, leaning in |

**Notes:**
- [ ] Add body wiggle (rapid side-to-side oscillation)
- [ ] Add tentacle reaching/grabbing motion
- [ ] Add heart-pupil pulsing (alternate between 2 sizes)
- [ ] Consider blush marks on cheeks (small pixel clusters)
- _Improvements:_

---

## Body Motion Priority Matrix

> Proposed body animations ranked by impact and implementation difficulty.

| Motion Type | States That Use It | Difficulty | Impact |
|-------------|-------------------|:----------:|:------:|
| **Idle sway** (slow tentacle wave) | NORMAL, CHILL | Low | High |
| **Breathing bob** (1-2px vertical) | ALL states as base layer | Low | High |
| **Body jitter** (random 1px offset) | UNHINGED, CHAOTIC | Low | Medium |
| **Horizontal sway** (sine wave) | SLAPHAPPY, WEIRD | Medium | High |
| **Body slump/droop** (shift down) | SAD, TIRED, LAZY | Medium | High |
| **Body puff** (expand outline) | ANGRY, FAT | Medium | Medium |
| **Tentacle curl variations** | ANGRY (clench), FAT (rest), SAD (droop) | High | High |
| **Nod-off cycle** | TIRED | Medium | Medium |
| **Lean direction** | HUNGRY (up), HORNY (forward), CHILL (back) | Medium | Medium |
| **Full body wobble** | SLAPHAPPY, CHAOTIC | Medium | Medium |
| **Tentacle flail** | CHAOTIC, UNHINGED | High | High |
| **Melt/flatten** | LAZY | High | Medium |

---

## Animation Cycle Reference

| Mood | Frame 0 | Frame 1 | Frame 2 | Frame 3 |
|------|---------|---------|---------|---------|
| NORMAL | SMIRK | OPEN | SMILE | OPEN |
| WEIRD | WEIRD | OPEN | WEIRD | SMILE |
| UNHINGED | UNHINGED | OPEN | UNHINGED | OPEN |
| ANGRY | ANGRY | OPEN | ANGRY | ANGRY |
| SAD | SAD | OPEN | SAD | SMILE |
| CHAOTIC | CHAOTIC | OPEN | UNHINGED | WEIRD |
| HUNGRY | HUNGRY | OPEN | HUNGRY | SMILE |
| TIRED | TIRED | OPEN | TIRED | TIRED |
| SLAPHAPPY | SLAPHAPPY | OPEN | SLAPHAPPY | SMILE |
| LAZY | LAZY | LAZY | LAZY | OPEN |
| FAT | FAT | OPEN | FAT | SMILE |
| CHILL | CHILL | OPEN | CHILL | SMILE |
| HORNY | HORNY | OPEN | HORNY | SMILE |

---

## Implementation Approach for Body Motion

### Strategy: RLE Body Variants

The current body is a single static `body_rle[]`. To add body motion:

1. **Base RLE + transform functions** — Apply offsets/scaling to existing RLE at render time
2. **Per-mood body modifier** — Each mood calls a transform before RLE render:
   - `body_shift_y(int dy)` — vertical offset (slump, bob)
   - `body_shift_x(int dx)` — horizontal offset (sway, jitter)
   - `body_scale(float sx, float sy)` — puff up / flatten
3. **Tentacle animation** — Separate tentacle RLE from head, animate independently
4. **Frame counter** — Use existing 4-frame cycle index to drive body position

### Suggested Implementation Order

1. Separate tentacles from head in RLE data
2. Add `body_shift_y()` — enables breathing bob for ALL moods
3. Add `body_shift_x()` — enables sway, jitter, wobble
4. Add per-mood tentacle position tables (4 frames each)
5. Add body scale transform for ANGRY puff / LAZY melt

---

## Source File Reference

| File | Content | Key Lines |
|------|---------|-----------|
| `dev-setup/sassy-octopus/main.c` | Reference firmware (all states) | 77-107: constants, 264-701: draw functions, 921-953: cycles |
| `DevTool/devtool.py` | Python preview/generator | 2364-2394: expressions, 4085-4152: program configs |
| `dev-setup/sassy-octopus/frames.h` | Body RLE data (if extracted) | — |
| `assets/octopus-emotion-states.md` | This document | — |

---

*Last updated: 2026-04-12*
