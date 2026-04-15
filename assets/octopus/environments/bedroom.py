"""Bedroom environment — 3D perspective room with bed, nightstand, window, moon.

Uses dithered shading for walls/floor depth, perspective converging lines,
and detailed furniture. Supports both speaking mode (left 70px focus) and
idle mode (full 250x122 canvas scene).
"""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_arc,
    fill_dithered_rect, gradient_vfill, fill_dithered_poly,
    draw_shadow, draw_thick_line, _dither_check,
)
from . import register


def _draw_bedroom_full(frame_idx):
    """Full-canvas bedroom scene (idle mode / no bubble)."""
    W, H = canvas.IMG_W, canvas.IMG_H

    # ── Back wall (light dithered fill) ──
    gradient_vfill(0, 0, W, 75, 0.04, 0.10)

    # ── Floor (perspective checkered tile) ──
    floor_y = 75
    for y in range(floor_y, H):
        depth = (y - floor_y) / max(H - floor_y - 1, 1)
        tile_size = max(3, int(6 + depth * 14))
        for x in range(0, W):
            col = x // tile_size
            row = (y - floor_y) // max(2, int(tile_size * 0.6))
            if (col + row) % 2 == 0:
                shade = 0.08 + depth * 0.12
                if _dither_check(x, y, shade):
                    canvas.px_set(x, y)

    # Floor horizon line
    draw_thick_line(0, floor_y, W - 1, floor_y, 2)

    # ── Wall/floor baseboard ──
    draw_hline(0, W - 1, floor_y + 1)
    draw_hline(0, W - 1, floor_y + 2)

    # ── Window (left wall, with depth frame) ──
    wx, wy, ww, wh = 15, 10, 40, 45
    # Window recess shadow
    fill_dithered_rect(wx - 2, wy - 2, ww + 4, wh + 4, 0.2)
    # Window frame (thick)
    draw_rect(wx, wy, ww, wh)
    draw_rect(wx + 1, wy + 1, ww - 2, wh - 2)
    # Clear glass
    fill_dithered_rect(wx + 2, wy + 2, ww - 4, wh - 4, 0.0)
    # Crossbar
    draw_vline(wx + ww // 2, wy, wy + wh - 1)
    draw_hline(wx, wx + ww - 1, wy + wh // 2)
    # Night sky through window (sparse dither)
    fill_dithered_rect(wx + 3, wy + 3, ww - 6, wh // 2 - 4, 0.06)

    # Moon (upper-left pane, crescent)
    moon_cx, moon_cy = wx + ww // 4, wy + wh // 4
    for dy in range(-5, 6):
        for dx in range(-5, 6):
            if dx * dx + dy * dy <= 25:
                canvas.px_set(moon_cx + dx, moon_cy + dy)
    # Crescent cutout
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if dx * dx + dy * dy <= 12:
                canvas.px_clr(moon_cx + 3 + dx, moon_cy - 1 + dy)
    # Stars through window
    for sx, sy in [(wx + 30, wy + 8), (wx + 25, wy + 15), (wx + 35, wy + 5),
                   (wx + 10, wy + 5), (wx + 33, wy + 18)]:
        canvas.px_set(sx, sy)

    # Curtain left (dithered fabric)
    for y in range(wy - 2, wy + wh + 4):
        for x in range(wx - 6, wx - 1):
            wave = int(1.5 * math.sin(y * 0.3))
            if _dither_check(x + wave, y, 0.25):
                canvas.px_set(x + wave, y)
    # Curtain right
    for y in range(wy - 2, wy + wh + 4):
        for x in range(wx + ww + 1, wx + ww + 6):
            wave = int(1.5 * math.sin(y * 0.3 + 1))
            if _dither_check(x + wave, y, 0.25):
                canvas.px_set(x + wave, y)
    # Curtain rod
    draw_thick_line(wx - 8, wy - 4, wx + ww + 8, wy - 4, 2)

    # ── Bed (right side, perspective) ──
    bx, by = 130, 50
    bw, bh = 100, 55

    # Bed shadow on floor
    fill_dithered_rect(bx + 4, by + bh - 5, bw, 12, 0.15)

    # Headboard (tall, curved top)
    hx, hy = bx + bw - 12, by - 15
    for row in range(35):
        half_w = 5
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(hx + dx, hy + row)
    # Headboard curve
    for i in range(12):
        t = i / 11.0
        x = hx - 5 + int(t * 10)
        y = hy - int(3 * math.sin(t * math.pi))
        canvas.px_set(x, y)
        canvas.px_set(x, y + 1)

    # Mattress (3D box with perspective)
    # Top surface
    fill_dithered_poly(
        [(bx, by + 8), (bx + bw - 15, by + 8),
         (bx + bw - 10, by), (bx + 5, by)],
        0.05
    )
    # Front face
    fill_dithered_poly(
        [(bx, by + 8), (bx + bw - 15, by + 8),
         (bx + bw - 15, by + 18), (bx, by + 18)],
        0.15
    )
    # Mattress outline
    draw_line(bx, by + 8, bx + bw - 15, by + 8)
    draw_line(bx, by + 8, bx, by + 18)
    draw_line(bx, by + 18, bx + bw - 15, by + 18)
    draw_line(bx + bw - 15, by + 8, bx + bw - 15, by + 18)

    # Blanket (draped, with fold texture)
    for row in range(25):
        y = by + 18 + row
        wave = int(2 * math.sin(row * 0.4))
        x0 = bx + wave
        x1 = bx + bw - 15 + int(wave * 0.5)
        for x in range(max(0, x0), min(W, x1)):
            shade = 0.12 + 0.08 * math.sin(row * 0.6 + (x - bx) * 0.1)
            if _dither_check(x, y, shade):
                canvas.px_set(x, y)
    # Blanket fold line
    for x in range(bx + 5, bx + bw - 20):
        fold_y = by + 22 + int(1.5 * math.sin(x * 0.08))
        canvas.px_set(x, fold_y)

    # Pillow (rounded with shading)
    px, py = bx + bw - 35, by + 4
    for dy in range(-5, 6):
        for dx in range(-10, 11):
            if dx * dx * 25 + dy * dy * 100 <= 2500:
                dist = (dx * dx * 25 + dy * dy * 100) / 2500.0
                shade = 0.03 + 0.12 * dist
                if _dither_check(px + dx, py + dy, shade):
                    canvas.px_set(px + dx, py + dy)
    # Pillow outline
    for dy in range(-5, 6):
        for dx in range(-10, 11):
            if dx * dx * 25 + dy * dy * 100 <= 2500:
                for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if (dx + ndx) ** 2 * 25 + (dy + ndy) ** 2 * 100 > 2500:
                        canvas.px_set(px + dx, py + dy)
                        break

    # ── Nightstand (left of bed) ──
    nx, ny = bx - 20, by + 15
    # Shadow
    fill_dithered_rect(nx + 2, ny + 22, 16, 4, 0.15)
    # Body
    draw_rect(nx, ny, 16, 22)
    # Top surface (slight perspective)
    draw_line(nx, ny, nx + 3, ny - 3)
    draw_line(nx + 16, ny, nx + 19, ny - 3)
    draw_hline(nx + 3, nx + 19, ny - 3)
    # Drawer
    draw_hline(nx + 1, nx + 15, ny + 10)
    canvas.px_set(nx + 8, ny + 5)   # knob
    canvas.px_set(nx + 8, ny + 15)  # knob

    # Alarm clock on nightstand
    acx, acy = nx + 8, ny - 6
    for dy in range(-3, 4):
        for dx in range(-4, 5):
            if dx * dx + dy * dy <= 12:
                canvas.px_set(acx + dx, acy + dy)
    canvas.px_clr(acx, acy)     # clock face center
    canvas.px_clr(acx + 1, acy - 1)  # hour hand
    canvas.px_clr(acx, acy - 1)      # minute hand

    # ── Lamp on nightstand ──
    lx, ly = nx + 3, ny - 18
    # Shade (trapezoid with dithered fill)
    for row in range(8):
        half_w = 3 + row
        shade = 0.1 + 0.05 * row / 7
        for dx in range(-half_w, half_w + 1):
            if _dither_check(lx + dx, ly + row, shade):
                canvas.px_set(lx + dx, ly + row)
    # Shade outline
    draw_line(lx - 3, ly, lx - 10, ly + 7)
    draw_line(lx + 3, ly, lx + 10, ly + 7)
    draw_hline(lx - 10, lx + 10, ly + 7)
    # Stem
    draw_vline(lx, ly + 8, ny - 1)

    # ── Rug on floor (oval with pattern) ──
    rug_cx, rug_cy = 100, 95
    for dy in range(-12, 13):
        for dx in range(-35, 36):
            if dx * dx * 144 + dy * dy * 1225 <= 144 * 1225:
                dist = (dx * dx * 144 + dy * dy * 1225) / (144.0 * 1225)
                # Striped pattern
                ring = int(dist * 4)
                shade = 0.15 if ring % 2 == 0 else 0.06
                if _dither_check(rug_cx + dx, rug_cy + dy, shade):
                    canvas.px_set(rug_cx + dx, rug_cy + dy)


def _draw_bedroom_speaking(frame_idx):
    """Left-zone bedroom for speaking mode (character + bubble)."""
    # Simplified version: wall + floor + window in left 70px
    gradient_vfill(0, 0, 72, 75, 0.04, 0.08)

    # Floor
    for y in range(75, canvas.IMG_H):
        depth = (y - 75) / max(canvas.IMG_H - 76, 1)
        for x in range(0, 72):
            tile = (x // 8 + (y - 75) // 5) % 2
            if tile == 0:
                shade = 0.06 + depth * 0.1
                if _dither_check(x, y, shade):
                    canvas.px_set(x, y)
    draw_hline(0, 71, 75)
    draw_hline(0, 71, 76)

    # Small window
    draw_rect(3, 8, 22, 24)
    draw_rect(4, 9, 20, 22)
    draw_vline(14, 8, 31)
    draw_hline(3, 24, 20)
    # Moon
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if dx * dx + dy * dy <= 9:
                canvas.px_set(19, 14 + dy)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                canvas.px_clr(21, 13 + dy)

    # Nightstand hint
    draw_rect(50, 65, 14, 14)
    draw_hline(51, 63, 72)
    canvas.px_set(57, 69)

    # Rug strip
    for x in range(10, 60):
        for y in range(80, 85):
            if (x + y) % 3 == 0:
                canvas.px_set(x, y)


@register(
    "bedroom",
    ground_y=75,
    has_weather=False,
    description="3D bedroom with perspective floor, bed, window+moon, curtains, nightstand",
    decor_slots=[(5, 85), (60, 90)],
)
def draw_bedroom(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_bedroom_full(frame_idx)
    else:
        _draw_bedroom_speaking(frame_idx)
