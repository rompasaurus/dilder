"""Per-emotion aura particle definitions.

Each function draws 3-5 small pixel clusters around the character center.
Particles animate via frame_idx to create motion even when the body is
static (e.g. sleeping, sitting).

All particles are 2-4px each — negligible rendering cost on e-ink.
Positions use sinusoidal orbits relative to (cx, cy) so they track
the character across poses.
"""

import math
from ..core import canvas
from . import register


def _px(x, y):
    """Absolute pixel set (aura is NOT body-transform-relative)."""
    canvas.px_set(x + canvas.body_dx, y + canvas.Y_OFF + canvas.body_dy)


# ── Normal: gentle dots drifting outward (calm ripple) ──
@register("normal")
def aura_normal(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    for i in range(4):
        angle = i * math.pi / 2.0 + f * 0.3
        r = 38 + 3 * math.sin(f * 0.5 + i)
        x = cx + int(r * math.cos(angle))
        y = cy + int(r * 0.6 * math.sin(angle))
        _px(x, y)


# ── Weird: wobbly tilted dots ──
@register("weird")
def aura_weird(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    for i in range(3):
        x = cx - 15 + i * 15 + int(3 * math.sin(f * 1.5 + i * 2))
        y = cy - 25 + int(5 * math.sin(f * 0.8 + i))
        _px(x, y)
        _px(x + 1, y - 1)  # tilted dot pair


# ── Unhinged: rapid flickering static noise ──
@register("unhinged")
def aura_unhinged(cx, cy, frame_idx):
    # Deterministic "random" based on frame_idx — flickers each frame
    seed = frame_idx * 7 + 13
    for i in range(5):
        seed = (seed * 31 + 17) % 997
        x = cx - 30 + (seed % 60)
        seed = (seed * 31 + 17) % 997
        y = cy - 20 + (seed % 40)
        _px(x, y)


# ── Angry: sharp zigzag sparks ──
@register("angry")
def aura_angry(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    # Two zigzag sparks on either side
    for side in [-1, 1]:
        bx = cx + side * 35
        by = cy - 10 + int(4 * math.sin(f * 2.0))
        # 3-segment zigzag
        _px(bx, by)
        _px(bx + side * 2, by - 2)
        _px(bx, by - 4)
        _px(bx + side * 2, by - 6)


# ── Sad: falling tear drops ──
@register("sad")
def aura_sad(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    for i in range(3):
        x = cx - 20 + i * 20
        # Drops fall downward over time
        y = cy + 15 + int(8 * ((f * 0.5 + i * 1.5) % (2 * math.pi)) / (2 * math.pi))
        _px(x, y)
        _px(x, y + 1)  # elongated drop


# ── Chaotic: spiral dots orbiting wildly ──
@register("chaotic")
def aura_chaotic(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    for i in range(5):
        angle = f * 3.0 + i * math.pi * 2.0 / 5.0
        r = 30 + 8 * math.sin(f * 1.5 + i)
        x = cx + int(r * math.cos(angle))
        y = cy + int(r * 0.5 * math.sin(angle))
        _px(x, y)


# ── Hungry: rising sweat drops + fork/knife pixels ──
@register("hungry")
def aura_hungry(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    # Sweat drops rising
    for i in range(2):
        x = cx - 8 + i * 16
        y = cy - 28 - int(3 * ((f + i * 2) % (2 * math.pi)) / math.pi)
        _px(x, y)
        _px(x, y - 1)
    # Tiny fork (3px vertical + 2 tines)
    fx = cx + 25 + int(2 * math.sin(f * 0.5))
    fy = cy - 15
    _px(fx, fy)
    _px(fx, fy + 1)
    _px(fx, fy + 2)
    _px(fx - 1, fy)
    _px(fx + 1, fy)


# ── Tired: floating Z-letters ascending ──
@register("tired")
def aura_tired(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    for i in range(3):
        # Z's float up and to the right
        phase = (f * 0.3 + i * 1.5) % (2 * math.pi)
        x = cx + 20 + i * 8 + int(2 * math.sin(phase))
        y = cy - 20 - i * 6 - int(3 * phase / math.pi)
        # Mini Z: 3px wide
        _px(x, y)
        _px(x + 1, y)
        _px(x + 1, y + 1)
        _px(x, y + 2)
        _px(x + 1, y + 2)


# ── Slap Happy: bouncing exclamation marks ──
@register("slaphappy")
def aura_slaphappy(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    for i, side in enumerate([-1, 1]):
        x = cx + side * 32
        y = cy - 15 + int(5 * abs(math.sin(f * 2.5 + i)))
        # Exclamation: 3px line + dot
        _px(x, y)
        _px(x, y + 1)
        _px(x, y + 2)
        _px(x, y + 4)  # dot


# ── Lazy: slow drifting ellipsis ──
@register("lazy")
def aura_lazy(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    x_base = cx + 20 + int(3 * math.sin(f * 0.2))
    y_base = cy + int(2 * math.sin(f * 0.15))
    for i in range(3):
        _px(x_base + i * 3, y_base)


# ── Fat: tiny sparkles / food crumb dots ──
@register("fat")
def aura_fat(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    for i in range(4):
        angle = i * math.pi / 2.0 + f * 0.4
        r = 32 + 2 * math.sin(f * 0.8 + i)
        x = cx + int(r * math.cos(angle))
        y = cy + int(r * 0.5 * math.sin(angle))
        _px(x, y)
        # Cross sparkle on even frames
        if frame_idx % 2 == 0:
            _px(x + 1, y)
            _px(x, y + 1)


# ── Chill: wavy tilde lines drifting sideways ──
@register("chill")
def aura_chill(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    for i in range(2):
        bx = cx - 25 + i * 50 + int(4 * math.sin(f * 0.3 + i))
        by = cy - 10 + i * 5
        # Tilde shape: ~
        for dx in range(5):
            dy = int(1.5 * math.sin(dx * math.pi / 2.0))
            _px(bx + dx, by + dy)


# ── Creepy: pulsing heart-shaped clusters ──
@register("creepy")
def aura_creepy(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    for i in range(2):
        angle = math.pi / 4.0 + i * math.pi / 2.0 + f * 0.5
        r = 30 + int(4 * math.sin(f * 2.0))
        hx = cx + int(r * math.cos(angle))
        hy = cy + int(r * 0.5 * math.sin(angle)) - 15
        # Tiny heart: 5px
        _px(hx - 1, hy)
        _px(hx + 1, hy)
        _px(hx - 2, hy + 1)
        _px(hx + 2, hy + 1)
        _px(hx, hy + 2)


# ── Excited: star bursts rotating outward ──
@register("excited")
def aura_excited(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    for i in range(4):
        angle = i * math.pi / 2.0 + f * 1.5
        r = 35 + int(3 * math.sin(f * 3.0 + i))
        sx = cx + int(r * math.cos(angle))
        sy = cy + int(r * 0.5 * math.sin(angle))
        # Plus-shaped star
        _px(sx, sy)
        _px(sx - 1, sy)
        _px(sx + 1, sy)
        _px(sx, sy - 1)
        _px(sx, sy + 1)


# ── Nostalgic: floating clock/hourglass dots ──
@register("nostalgic")
def aura_nostalgic(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    # Slow upward drift
    for i in range(3):
        x = cx + 20 + i * 5 + int(2 * math.sin(f * 0.3 + i))
        y = cy - 20 - int(4 * ((f * 0.2 + i) % math.pi) / math.pi)
        # Hourglass: 3px tall
        _px(x - 1, y)
        _px(x + 1, y)
        _px(x, y + 1)
        _px(x - 1, y + 2)
        _px(x + 1, y + 2)


# ── Homesick: tiny house silhouette dissolving outward ──
@register("homesick")
def aura_homesick(cx, cy, frame_idx):
    f = frame_idx * math.pi / 2.0
    # House drifts and fades
    hx = cx + 25 + int(3 * math.sin(f * 0.4))
    hy = cy - 20 + int(2 * math.sin(f * 0.3))
    # Roof (triangle)
    _px(hx, hy - 3)
    _px(hx - 1, hy - 2)
    _px(hx + 1, hy - 2)
    _px(hx - 2, hy - 1)
    _px(hx + 2, hy - 1)
    # Walls
    _px(hx - 2, hy)
    _px(hx + 2, hy)
    _px(hx - 2, hy + 1)
    _px(hx + 2, hy + 1)
    # Base
    for dx in range(-2, 3):
        _px(hx + dx, hy + 2)
    # Dissolving particles (drift outward over frames)
    scatter = int(2 * math.sin(f * 0.8))
    _px(hx + 4 + scatter, hy - 1)
    _px(hx - 4 - scatter, hy)
