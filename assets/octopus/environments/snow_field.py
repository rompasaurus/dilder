"""Snow field environment — winter wonderland with drifts, snowflakes, icicles.

Falling snowflakes animate with frame_idx. Dithered snow drifts give
depth to the ground, bare trees and distant pines create a cold forest
feel, and a snowman + frozen pond fill out the idle panorama.
"""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    fill_dithered_poly, _dither_check, draw_curved_surface,
)
from . import register


# Deterministic snowflake positions (x, y_base, speed, wobble_phase)
_FLAKES_LEFT = [
    (5, 10, 3, 0.0), (18, 25, 2, 1.2), (30, 5, 4, 0.7),
    (42, 18, 2, 2.1), (55, 8, 3, 1.5), (12, 40, 3, 0.4),
    (38, 50, 2, 1.8), (62, 35, 4, 2.5), (25, 60, 3, 0.9),
    (48, 55, 2, 1.1), (8, 70, 3, 2.0), (35, 75, 4, 0.3),
    (60, 65, 2, 1.7), (15, 85, 3, 2.3), (50, 80, 2, 0.6),
]
_FLAKES_FULL = _FLAKES_LEFT + [
    (85, 12, 3, 0.5), (110, 30, 2, 1.9), (130, 8, 4, 0.2),
    (155, 22, 3, 2.7), (175, 15, 2, 1.0), (195, 40, 3, 0.8),
    (215, 5, 4, 1.4), (235, 28, 2, 2.2), (100, 55, 3, 0.1),
    (140, 48, 2, 1.6), (170, 60, 4, 2.8), (200, 50, 3, 0.4),
    (225, 65, 2, 1.3), (245, 45, 3, 2.6), (120, 72, 2, 0.7),
]


def _draw_snowflakes(flakes, frame_idx, max_x):
    """Animate falling snowflakes within the given x bound."""
    for sx, sy_base, speed, phase in flakes:
        if sx >= max_x:
            continue
        sy = (sy_base + frame_idx * speed) % 122
        wobble = int(2 * math.sin(frame_idx * 0.3 + phase))
        x = sx + wobble
        if 0 <= x < max_x:
            canvas.px_set(x, sy)
            # Bigger flakes for variety
            if (sx + sy_base) % 5 == 0:
                canvas.px_set(x + 1, sy)
                canvas.px_set(x, sy + 1)


def _draw_bare_tree(tx, ground_y, height):
    """Bare winter tree — trunk and forking branches, no leaves."""
    # Trunk
    draw_thick_line(tx, ground_y, tx, ground_y - height, 2)
    # Main branches
    h3 = height // 3
    for sign in (-1, 1):
        bx = tx + sign * (height // 3)
        by = ground_y - height + h3
        draw_line(tx, ground_y - height + h3 + 2, bx, by - 5)
        # Twigs
        draw_line(bx, by - 5, bx + sign * 4, by - 10)
        draw_line(bx, by - 5, bx + sign * 2, by - 12)
    # Top fork
    draw_line(tx, ground_y - height, tx - 3, ground_y - height - 6)
    draw_line(tx, ground_y - height, tx + 3, ground_y - height - 6)


def _draw_snow_field_full(frame_idx):
    """Full-canvas winter wonderland (idle mode)."""
    W, H = canvas.IMG_W, canvas.IMG_H
    ground_y = 85

    # Sky — very light dither, overcast feel
    gradient_vfill(0, 0, W, ground_y - 10, 0.04, 0.02)

    # Icicles hanging from top edge
    for ix in range(8, W - 5, 18):
        length = 6 + (ix * 7) % 8
        draw_vline(ix, 0, length)
        draw_vline(ix + 1, 0, length - 2)
        # Tapered tip
        canvas.px_set(ix, length + 1)

    # Distant pine trees (small, light silhouettes)
    for px_pos in [90, 115, 138, 160, 185, 210, 232]:
        h = 10 + (px_pos * 3) % 6
        for row in range(h):
            half_w = 1 + row // 2
            for dx in range(-half_w, half_w + 1):
                x = px_pos + dx
                if 0 <= x < W:
                    y = ground_y - h + row - 3
                    if _dither_check(x, y, 0.25):
                        canvas.px_set(x, y)
        # Trunk stub
        canvas.px_set(px_pos, ground_y - 3)
        canvas.px_set(px_pos, ground_y - 2)

    # Snow ground — white with subtle drift bumps
    draw_hline(0, W - 1, ground_y)
    for x in range(W):
        drift = int(3 * math.sin(x * 0.04) + 2 * math.sin(x * 0.09 + 1.5))
        line_y = ground_y + drift
        canvas.px_set(x, line_y)
        # Sparse ground texture below
        for y in range(max(ground_y, line_y), H):
            if _dither_check(x, y, 0.03):
                canvas.px_set(x, y)

    # Frozen pond (elliptical, dithered light on surface)
    pond_cx, pond_cy = 170, ground_y + 12
    for dy in range(-6, 7):
        for dx in range(-18, 19):
            if (dx * dx) / 324.0 + (dy * dy) / 36.0 <= 1.0:
                px, py = pond_cx + dx, pond_cy + dy
                if 0 <= px < W and 0 <= py < H:
                    canvas.px_set(px, py)
    # Ice highlight — clear inner area
    for dy in range(-4, 5):
        for dx in range(-15, 16):
            if (dx * dx) / 225.0 + (dy * dy) / 16.0 <= 1.0:
                canvas.px_clr(pond_cx + dx, pond_cy + dy)
    # Crack lines on ice
    draw_line(pond_cx - 8, pond_cy - 2, pond_cx + 5, pond_cy + 3)
    draw_line(pond_cx + 2, pond_cy - 3, pond_cx - 3, pond_cy + 2)

    # Snowman
    sm_x = 120
    # Bottom ball
    draw_curved_surface(sm_x, ground_y - 3, 8, 7, 0.02, 0.18)
    # Middle ball
    draw_curved_surface(sm_x, ground_y - 14, 6, 5, 0.02, 0.15)
    # Head
    draw_curved_surface(sm_x, ground_y - 22, 4, 4, 0.02, 0.12)
    # Eyes
    canvas.px_set(sm_x - 2, ground_y - 23)
    canvas.px_set(sm_x + 2, ground_y - 23)
    # Nose (carrot)
    canvas.px_set(sm_x + 1, ground_y - 21)
    canvas.px_set(sm_x + 2, ground_y - 21)
    # Arms (sticks)
    draw_line(sm_x - 6, ground_y - 17, sm_x - 12, ground_y - 22)
    draw_line(sm_x + 6, ground_y - 17, sm_x + 12, ground_y - 22)
    # Hat brim + top
    draw_hline(sm_x - 5, sm_x + 5, ground_y - 26)
    draw_rect(sm_x - 3, ground_y - 33, 7, 7, filled=True)

    # Bare trees
    _draw_bare_tree(35, ground_y + 2, 28)
    _draw_bare_tree(220, ground_y, 22)

    # Snowflakes
    _draw_snowflakes(_FLAKES_FULL, frame_idx, W)


def _draw_snow_field_speaking(frame_idx):
    """Left-zone snow scene for speaking mode."""
    ground_y = 85

    # Light overcast sky
    gradient_vfill(0, 0, 72, ground_y - 5, 0.03, 0.01)

    # Snow ground with drift
    draw_hline(0, 71, ground_y)
    for x in range(72):
        drift = int(2 * math.sin(x * 0.06))
        line_y = ground_y + drift
        canvas.px_set(x, line_y)
        for y in range(max(ground_y, line_y), 122):
            if _dither_check(x, y, 0.03):
                canvas.px_set(x, y)

    # Bare tree
    _draw_bare_tree(55, ground_y + 2, 22)

    # Snowflakes
    _draw_snowflakes(_FLAKES_LEFT, frame_idx, 72)


@register(
    "snow_field",
    ground_y=85,
    has_weather=True,
    description="Winter wonderland with snow drifts, snowman, icicles, frozen pond, bare trees",
    decor_slots=[(5, 95), (55, 92)],
)
def draw_snow_field(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_snow_field_full(frame_idx)
    else:
        _draw_snow_field_speaking(frame_idx)
