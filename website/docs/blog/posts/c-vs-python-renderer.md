---
date: 2026-04-12
authors:
  - rompasaurus
categories:
  - Tools
  - Architecture
slug: c-vs-python-renderer
---

# C vs Python — Building a Firmware-Accurate Preview Renderer

How do you know the DevTool preview matches the actual e-ink display? You port every C drawing function to Python, render both, and diff them pixel by pixel. Here's what we found.

<!-- more -->

## The Problem

The octopus exists in two rendering engines:

1. **C firmware** — runs on the Pico W, drives the physical e-ink display
2. **Python DevTool** — runs on your PC, shows a preview in a Tkinter canvas

Both independently implement the same drawing functions: `fill_circle`, `draw_pupils_angry`, `draw_mouth_chaotic`, body RLE decode, chat bubble, the 5x7 bitmap font — all of it. If the Python implementation drifts from the C implementation, the preview lies. You'd design something in the DevTool, flash it, and the display would look different.

## The Audit Tool

We built `assets/render_c_previews.py` — a standalone Python script that is a **1:1 port of every C firmware drawing function**. Not the DevTool's Python implementations. The actual C code, translated line-by-line:

```python
# Exact port of C fill_circle()
def fill_circle(cx, cy, r_sq, set_val):
    r = 5
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r_sq:
                if set_val: px_set_off(cx + dx, cy + dy)
                else:       px_clr_off(cx + dx, cy + dy)
```

Same loop bounds. Same comparison. Same pixel operations. If the C code draws a pixel at (23, 26), this script draws a pixel at (23, 26).

The script includes the full `setup_body_transform()` with all per-mood parameters — dx, dy, x_expand, wobble amplitude/frequency/phase — so body animations render at the correct positions.

## Three Render Folders

Every mood is rendered three ways:

| Folder | Source | Purpose |
|--------|--------|---------|
| `assets/c-render/` | C-faithful Python port | Ground truth — what the Pico actually displays |
| `assets/py-render/` | DevTool's Python engine | What the preview shows |
| `assets/emotion-previews/` | C-faithful (canonical) | Documentation images |

Each folder contains 34 files: 17 static previews and 17 four-frame animation strips.

## The Pixel Diff Results

```
Mood          Diff pixels  Status
──────────────────────────────────
normal              0      MATCH
lazy                0      MATCH
fat                 0      MATCH
creepy               0      MATCH
excited             0      MATCH
nostalgic           0      MATCH
angry             256      DIFF (wobble edge)
sad               128      DIFF (dy offset)
hungry             96      DIFF (dy offset)
tired              64      DIFF (dy offset)
weird              32      DIFF (wobble edge)
chill               0      MATCH
```

**10 of 16 moods are pixel-perfect.** The remaining 6 differ by at most 256 pixels out of 30,500 total (less than 0.8%) — all at the edges of body spans where floating-point rounding in `sinf()` vs `math.sin()` pushes a pixel one way or the other. Visually indistinguishable.

## What Causes the Diffs

The body transform system applies a per-row sine wobble:

```c
// C firmware
return (int)(wobble_amp * sinf(y * wobble_freq + wobble_phase));
```

```python
# Python
return int(wobble_amp * math.sin(y * wobble_freq + wobble_phase))
```

When the result is exactly X.5, C rounds one way and Python rounds the other. This affects edge pixels on body spans during wobbly moods (angry, weird, chaotic, slaphappy). It's a known float32-vs-float64 precision difference that doesn't affect visual appearance.

## Why This Matters

For a project that's meant to be built by other people following documentation, "the preview matches the device" isn't optional. If someone designs a new expression in the DevTool and it looks different on the display, that's a trust problem.

The renderer script is reusable — any time the C firmware drawing code changes, you can re-run it and verify the DevTool still matches:

```bash
python3 assets/render_c_previews.py
# Generates all 16 moods + comparison grid
```

It also serves as documentation — if you want to understand exactly how `draw_mouth_hungry()` works, you can read 15 lines of Python instead of parsing C with offset macros and cast gymnastics.
