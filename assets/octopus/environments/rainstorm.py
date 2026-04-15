"""Rainstorm environment — dark sky, heavy rain, lightning, puddles.

Dense dithered gradient sky, diagonal rain streaks animated with
frame_idx, periodic lightning flash, puddle ripple circles, and
wind-bent trees for a dramatic storm scene.
"""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    fill_dithered_poly, _dither_check, draw_curved_surface,
)
from . import register


def _draw_rain_lines(frame_idx, max_x, ground_y):
    """Diagonal rain streaks, animated by frame_idx."""
    for i in range(40 if max_x > 72 else 12):
        # Deterministic positions with animation offset
        base_x = (i * 17 + 3) % max_x
        base_y = (i * 23 + frame_idx * 7) % (ground_y + 10)
        length = 5 + (i * 3) % 4
        # Rain falls diagonally: down-right (wind)
        x1 = base_x + length // 3
        y1 = base_y + length
        if 0 <= base_x < max_x and 0 <= x1 < max_x:
            draw_line(base_x, base_y, x1, min(y1, ground_y + 5))


def _draw_puddle(px, py, r_x, frame_idx):
    """Puddle with animated ripple rings."""
    # Flat puddle ellipse outline
    for deg in range(0, 360, 3):
        x = px + int(r_x * math.cos(math.radians(deg)))
        y = py + int(r_x * 0.3 * math.sin(math.radians(deg)))
        if 0 <= x < canvas.IMG_W and 0 <= y < canvas.IMG_H:
            canvas.px_set(x, y)
    # Ripple rings expanding outward
    for ring in range(2):
        ripple_r = (frame_idx * 2 + ring * 5) % (r_x - 2) + 2
        for deg in range(0, 360, 8):
            x = px + int(ripple_r * math.cos(math.radians(deg)))
            y = py + int(ripple_r * 0.25 * math.sin(math.radians(deg)))
            if 0 <= x < canvas.IMG_W and 0 <= y < canvas.IMG_H:
                canvas.px_set(x, y)


def _draw_bent_tree(tx, ground_y, height, bend_dir=1):
    """Wind-bent tree — trunk curves with the storm."""
    # Curved trunk (bending right for positive bend_dir)
    prev_x, prev_y = tx, ground_y
    for i in range(1, height + 1):
        t = i / height
        cx = tx + int(bend_dir * 6 * t * t)
        cy = ground_y - i
        draw_line(prev_x, prev_y, cx, cy)
        # Thicker trunk at base
        if i < height // 2:
            canvas.px_set(cx + 1, cy)
        prev_x, prev_y = cx, cy
    # Branches blown sideways
    top_x = prev_x
    top_y = prev_y
    for br_off in range(3):
        by = top_y + br_off * 4
        bx = top_x - bend_dir * 2
        draw_line(bx, by, bx + bend_dir * 10, by - 2 - br_off)
        draw_line(bx + bend_dir * 10, by - 2 - br_off,
                  bx + bend_dir * 14, by - 1 - br_off)


def _draw_lightning(frame_idx, x_start, y_start):
    """Jagged lightning bolt — visible only on certain frames."""
    if frame_idx % 12 not in (0, 1):
        return
    # Zigzag bolt
    segments = [(0, 0), (4, 12), (-3, 24), (5, 36), (-2, 48), (3, 58)]
    for i in range(len(segments) - 1):
        x0 = x_start + segments[i][0]
        y0 = y_start + segments[i][1]
        x1 = x_start + segments[i + 1][0]
        y1 = y_start + segments[i + 1][1]
        draw_thick_line(x0, y0, x1, y1, 2)
    # Branch bolt
    bx = x_start + segments[2][0]
    by = y_start + segments[2][1]
    draw_line(bx, by, bx + 8, by + 14)
    draw_line(bx + 8, by + 14, bx + 6, by + 22)


def _draw_rainstorm_full(frame_idx):
    """Full-canvas dramatic storm scene (idle mode)."""
    W, H = canvas.IMG_W, canvas.IMG_H
    ground_y = 90

    # Dark sky gradient (dense at top, slightly lighter at horizon)
    gradient_vfill(0, 0, W, ground_y, 0.55, 0.25)

    # Lightning flash — brighten sky on flash frames
    if frame_idx % 12 == 0:
        # Brief sky flash: clear some dither for brightness effect
        for y in range(0, ground_y // 2):
            for x in range(W):
                if _dither_check(x, y, 0.15):
                    canvas.px_clr(x, y)

    # Lightning bolt
    _draw_lightning(frame_idx, 160, 2)

    # Ground — dark, muddy
    draw_thick_line(0, ground_y, W - 1, ground_y, 2)
    fill_dithered_rect(0, ground_y + 2, W, H - ground_y - 2, 0.18)

    # Bent trees
    _draw_bent_tree(30, ground_y, 30, bend_dir=1)
    _draw_bent_tree(200, ground_y, 25, bend_dir=1)

    # Puddles with ripples
    _draw_puddle(80, ground_y + 12, 14, frame_idx)
    _draw_puddle(150, ground_y + 18, 10, frame_idx)
    _draw_puddle(230, ground_y + 10, 11, frame_idx)

    # Heavy rain
    _draw_rain_lines(frame_idx, W, ground_y)


def _draw_rainstorm_speaking(frame_idx):
    """Left-zone storm scene for speaking mode."""
    ground_y = 90

    # Dark sky
    gradient_vfill(0, 0, 72, ground_y, 0.50, 0.22)

    # Ground
    draw_hline(0, 71, ground_y)
    fill_dithered_rect(0, ground_y + 1, 72, 31, 0.15)

    # Puddle
    _draw_puddle(35, ground_y + 14, 12, frame_idx)

    # Rain lines
    _draw_rain_lines(frame_idx, 72, ground_y)


@register(
    "rainstorm",
    ground_y=90,
    has_weather=True,
    description="Dramatic storm with dark sky, diagonal rain, lightning, puddle ripples, bent trees",
    decor_slots=[(5, 100), (55, 98)],
)
def draw_rainstorm(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_rainstorm_full(frame_idx)
    else:
        _draw_rainstorm_speaking(frame_idx)
