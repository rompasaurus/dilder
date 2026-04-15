"""Garden environment -- rich grass, fountain, flower beds, trellis, butterflies.

Lush cultivated garden with a central fountain, stepping stone path,
vine-covered trellis, flower beds, bird bath, and fluttering butterflies.
"""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    fill_dithered_poly, _dither_check, draw_curved_surface,
)
from . import register


def _draw_flower(fx, fy, petal_r=2, stem_h=8, petal_density=0.35):
    """Flower with dithered petals and thin stem."""
    # Stem
    draw_vline(fx, fy - stem_h, fy)
    # Leaf on stem
    canvas.px_set(fx - 1, fy - stem_h // 2)
    canvas.px_set(fx - 2, fy - stem_h // 2 + 1)
    # Petals (5 around center)
    for i in range(5):
        angle = math.radians(i * 72 - 90)
        px = fx + int(petal_r * math.cos(angle))
        py = (fy - stem_h) + int(petal_r * math.sin(angle))
        fill_dithered_circle(px, py, petal_r, petal_density)
    # Center dot
    canvas.px_set(fx, fy - stem_h)


def _draw_butterfly(bx, by, frame_idx, phase=0.0):
    """Fluttering butterfly with animated wings."""
    flap = int(2 * math.sin(frame_idx * 0.8 + phase))
    # Body
    canvas.px_set(bx, by)
    canvas.px_set(bx, by + 1)
    # Wings (size varies with flap)
    wing_w = 2 + abs(flap)
    # Upper wings
    for dx in range(1, wing_w + 1):
        canvas.px_set(bx - dx, by - abs(flap))
        canvas.px_set(bx + dx, by - abs(flap))
    # Lower wings (smaller)
    for dx in range(1, max(1, wing_w - 1) + 1):
        canvas.px_set(bx - dx, by + 1 + abs(flap) // 2)
        canvas.px_set(bx + dx, by + 1 + abs(flap) // 2)
    # Antennae
    canvas.px_set(bx - 1, by - 2)
    canvas.px_set(bx + 1, by - 2)


def _draw_fountain(fx, fy, frame_idx):
    """Tiered fountain with water arcs and basin."""
    # Base basin (oval)
    for dy in range(-3, 4):
        hw = int(14 * math.sqrt(max(0, 1 - (dy / 3.5) ** 2)))
        for dx in range(-hw, hw + 1):
            on_edge = abs(dx) >= hw - 1 or abs(dy) >= 2
            if on_edge:
                canvas.px_set(fx + dx, fy + dy)
            elif _dither_check(fx + dx, fy + dy, 0.06):
                canvas.px_set(fx + dx, fy + dy)

    # Pedestal
    draw_thick_line(fx - 2, fy - 12, fx + 2, fy - 12, 1)
    draw_vline(fx - 1, fy - 12, fy - 3)
    draw_vline(fx, fy - 12, fy - 3)
    draw_vline(fx + 1, fy - 12, fy - 3)

    # Upper bowl
    for dx in range(-5, 6):
        canvas.px_set(fx + dx, fy - 12)
    draw_line(fx - 5, fy - 12, fx - 3, fy - 9)
    draw_line(fx + 5, fy - 12, fx + 3, fy - 9)
    draw_hline(fx - 3, fx + 3, fy - 9)

    # Water arcs from top (animated parabolas)
    for side in [-1, 1]:
        for i in range(8):
            t = i / 7.0
            wx = fx + side * int(t * 10)
            anim_offset = int(1.5 * math.sin(frame_idx * 0.6 + i * 0.3))
            wy = fy - 14 + int(t * t * 12) + anim_offset
            canvas.px_set(wx, wy)
            # Water drops
            if i % 2 == 0:
                canvas.px_set(wx, wy + 1)

    # Water surface ripples in basin
    for r in range(3, 12, 4):
        ripple_r = r + int(math.sin(frame_idx * 0.3 + r) * 1.5)
        for angle_i in range(0, 360, 20):
            a = math.radians(angle_i)
            rx = fx + int(ripple_r * math.cos(a) * 0.9)
            ry = fy + int(ripple_r * math.sin(a) * 0.3)
            if abs(ry - fy) < 3:
                canvas.px_set(rx, ry)


def _draw_trellis(tx, ty, w, h):
    """Vine-covered lattice trellis."""
    # Lattice frame
    draw_rect(tx, ty, w, h)
    # Cross-hatching
    spacing = 5
    for i in range(0, w + h, spacing):
        x0 = tx + min(i, w)
        y0 = ty + max(0, i - w)
        x1 = tx + max(0, i - h)
        y1 = ty + min(i, h)
        draw_line(x0, y0, x1, y1)
    for i in range(0, w + h, spacing):
        x0 = tx + w - min(i, w)
        y0 = ty + max(0, i - w)
        x1 = tx + w - max(0, i - h)
        y1 = ty + min(i, h)
        draw_line(x0, y0, x1, y1)

    # Vine leaves (small leaf clusters along lattice)
    for lx, ly in [(tx + 3, ty + 4), (tx + w - 4, ty + 6),
                   (tx + 5, ty + h - 5), (tx + w // 2, ty + 3),
                   (tx + 2, ty + h // 2)]:
        canvas.px_set(lx, ly)
        canvas.px_set(lx - 1, ly + 1)
        canvas.px_set(lx + 1, ly + 1)
        canvas.px_set(lx, ly + 2)


def _draw_stepping_stone(sx, sy, w, h):
    """Flat oval stepping stone."""
    for dy in range(-h, h + 1):
        hw = int(w * math.sqrt(max(0, 1 - (dy / max(h, 1)) ** 2)))
        for dx in range(-hw, hw + 1):
            on_edge = abs(dx) >= hw - 1 or abs(dy) >= h - 1
            if on_edge:
                canvas.px_set(sx + dx, sy + dy)
            elif _dither_check(sx + dx, sy + dy, 0.12):
                canvas.px_set(sx + dx, sy + dy)


def _draw_garden_full(frame_idx):
    """Full-canvas garden scene (idle mode)."""
    W, H = canvas.IMG_W, canvas.IMG_H
    ground_y = 65

    # ── Sky gradient (gentle blue) ──
    gradient_vfill(0, 0, W, ground_y, 0.02, 0.04)

    # ── Light clouds ──
    fill_dithered_circle(40, 12, 5, 0.10)
    fill_dithered_circle(35, 13, 3, 0.10)
    fill_dithered_circle(45, 13, 4, 0.10)
    fill_dithered_circle(180, 10, 6, 0.10)
    fill_dithered_circle(175, 11, 4, 0.10)

    # ── Rich grass ground ──
    for y in range(ground_y, H):
        depth = (y - ground_y) / max(H - ground_y - 1, 1)
        shade = 0.06 + depth * 0.04
        for x in range(W):
            if _dither_check(x, y, shade):
                canvas.px_set(x, y)
    draw_thick_line(0, ground_y, W - 1, ground_y, 2)

    # ── Grass tufts ──
    for gx, gy in [(8, 72), (30, 75), (55, 70), (90, 78), (130, 73),
                   (170, 76), (210, 71), (240, 77), (20, 90), (65, 95),
                   (150, 92), (200, 88), (235, 95)]:
        for i in range(4):
            canvas.px_set(gx - 1, gy - i)
            canvas.px_set(gx + 1, gy - i)
            canvas.px_set(gx, gy - i)

    # ── Trellis (right background) ──
    _draw_trellis(210, 30, 25, 35)

    # ── Central fountain ──
    _draw_fountain(125, ground_y + 28, frame_idx)

    # ── Stepping stone path (leading to fountain) ──
    for sx, sy in [(100, ground_y + 40), (110, ground_y + 35),
                   (118, ground_y + 30), (135, ground_y + 30),
                   (145, ground_y + 35), (155, ground_y + 40)]:
        _draw_stepping_stone(sx, sy, 4, 2)

    # ── Flower beds (left and right) ──
    # Left flower bed border
    fill_dithered_rect(10, ground_y + 5, 50, 3, 0.20)
    for fx, fh in [(15, 10), (22, 12), (30, 9), (38, 11), (46, 8), (54, 10)]:
        _draw_flower(fx, ground_y + 5, petal_r=2, stem_h=fh, petal_density=0.35)

    # Right flower bed border
    fill_dithered_rect(180, ground_y + 8, 40, 3, 0.20)
    for fx, fh in [(185, 9), (192, 11), (200, 8), (208, 12), (215, 10)]:
        _draw_flower(fx, ground_y + 8, petal_r=2, stem_h=fh, petal_density=0.30)

    # ── Bird bath (mid-left) ──
    bbx, bby = 75, ground_y + 15
    # Pedestal
    draw_vline(bbx, bby, bby + 12)
    draw_vline(bbx - 1, bby, bby + 12)
    # Base
    draw_hline(bbx - 4, bbx + 3, bby + 12)
    # Bowl
    for dx in range(-6, 7):
        canvas.px_set(bbx + dx, bby)
    draw_line(bbx - 6, bby, bbx - 4, bby + 3)
    draw_line(bbx + 6, bby, bbx + 4, bby + 3)
    draw_hline(bbx - 4, bbx + 4, bby + 3)
    # Water in bowl
    for dx in range(-3, 4):
        if _dither_check(bbx + dx, bby + 2, 0.08):
            canvas.px_set(bbx + dx, bby + 2)
    # Bird on rim
    canvas.px_set(bbx + 5, bby - 1)
    canvas.px_set(bbx + 5, bby - 2)
    canvas.px_set(bbx + 6, bby - 2)
    canvas.px_set(bbx + 4, bby - 2)

    # ── Butterflies ──
    _draw_butterfly(50, 45, frame_idx, phase=0.0)
    _draw_butterfly(160, 50, frame_idx, phase=1.5)
    _draw_butterfly(95, 42, frame_idx, phase=3.0)

    # ── Hedge row (far background, behind flowers) ──
    for x in range(0, W):
        hedge_h = 6 + int(2 * math.sin(x * 0.08))
        for y in range(ground_y - hedge_h, ground_y):
            shade = 0.15 + 0.05 * math.sin(x * 0.3)
            if _dither_check(x, y, shade):
                canvas.px_set(x, y)


def _draw_garden_speaking(frame_idx):
    """Left-zone garden for speaking mode."""
    ground_y = 70

    # Sky
    gradient_vfill(0, 0, 72, ground_y, 0.02, 0.04)

    # Hedge background
    for x in range(72):
        hedge_h = 5 + int(1.5 * math.sin(x * 0.1))
        for y in range(ground_y - hedge_h, ground_y):
            if _dither_check(x, y, 0.14):
                canvas.px_set(x, y)

    # Ground
    draw_hline(0, 71, ground_y)
    for y in range(ground_y + 1, canvas.IMG_H):
        depth = (y - ground_y) / max(canvas.IMG_H - ground_y - 1, 1)
        for x in range(72):
            if _dither_check(x, y, 0.05 + depth * 0.04):
                canvas.px_set(x, y)

    # Grass tufts
    for gx, gy in [(8, 76), (25, 80), (45, 78), (60, 82)]:
        for i in range(3):
            canvas.px_set(gx, gy - i)
            canvas.px_set(gx - 1, gy - i)
            canvas.px_set(gx + 1, gy - i)

    # Flowers (3 small ones)
    _draw_flower(15, ground_y + 3, petal_r=2, stem_h=8, petal_density=0.30)
    _draw_flower(35, ground_y + 2, petal_r=2, stem_h=10, petal_density=0.35)
    _draw_flower(55, ground_y + 4, petal_r=2, stem_h=7, petal_density=0.30)

    # Stepping stones
    _draw_stepping_stone(20, ground_y + 15, 3, 1)
    _draw_stepping_stone(35, ground_y + 18, 3, 1)

    # Butterfly
    _draw_butterfly(45, 50, frame_idx, phase=0.0)

    # Cloud
    fill_dithered_circle(55, 10, 4, 0.10)
    fill_dithered_circle(51, 11, 3, 0.10)


@register(
    "garden",
    ground_y=65,
    has_weather=True,
    description="Lush garden with fountain, flower beds, trellis, stepping stones, butterflies",
    decor_slots=[(5, 85), (55, 88)],
)
def draw_garden(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_garden_full(frame_idx)
    else:
        _draw_garden_speaking(frame_idx)
