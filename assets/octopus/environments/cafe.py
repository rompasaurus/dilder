"""Cafe environment — espresso machine, menu board, tables, pendant lamps."""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    fill_dithered_poly, _dither_check, draw_curved_surface,
)
from . import register


def _draw_cafe_full(frame_idx):
    """Full-canvas cafe scene (idle mode)."""
    W, H = canvas.IMG_W, canvas.IMG_H

    # ── Back wall (warm gradient) ──
    gradient_vfill(0, 0, W, 80, 0.03, 0.08)

    # ── Wood plank floor ──
    for y in range(80, H):
        depth = (y - 80) / max(H - 81, 1)
        for x in range(0, W):
            plank = x // 20
            edge = (x % 20) in (0, 19)
            grain = _dither_check(x, y, 0.06 + depth * 0.08)
            if edge or grain:
                canvas.px_set(x, y)
    draw_thick_line(0, 80, W - 1, 80, 2)

    # ── Menu board (upper-left wall) ──
    bx, by, bw, bh = 10, 8, 48, 32
    fill_dithered_rect(bx, by, bw, bh, 0.85)
    draw_rect(bx - 1, by - 1, bw + 2, bh + 2)
    draw_rect(bx - 2, by - 2, bw + 4, bh + 4)
    # Menu text lines (cleared pixels on dark board)
    for row in range(5):
        ty = by + 5 + row * 5
        for tx in range(bx + 4, bx + bw - 6, 2):
            canvas.px_clr(tx, ty)
    # Board title dots
    for tx in range(bx + 10, bx + 38, 2):
        canvas.px_clr(tx, by + 3)

    # ── Counter (spans middle) ──
    cx, cy = 0, 68
    cw = 120
    fill_dithered_rect(cx, cy, cw, 4, 0.3)
    draw_hline(cx, cx + cw - 1, cy)
    draw_hline(cx, cx + cw - 1, cy + 3)
    # Counter front face
    gradient_vfill(cx, cy + 4, cw, 10, 0.12, 0.20)

    # ── Espresso machine (on counter) ──
    mx, my = 80, 50
    draw_rect(mx, my, 20, 18)
    fill_dithered_rect(mx + 1, my + 1, 18, 16, 0.15)
    # Steam wand
    draw_vline(mx + 3, my + 12, my + 18)
    # Portafilter
    draw_hline(mx + 6, mx + 14, my + 14)
    draw_vline(mx + 10, my + 14, my + 17)
    # Drip tray
    draw_rect(mx + 4, my + 16, 12, 2)
    # Top dome
    for i in range(4):
        half = 8 - i
        draw_hline(mx + 10 - half, mx + 10 + half, my - 1 - i)

    # ── Coffee cup on counter ──
    ccx, ccy = 108, 62
    draw_rect(ccx, ccy, 7, 6)
    canvas.px_set(ccx + 7, ccy + 1)
    canvas.px_set(ccx + 8, ccy + 2)
    canvas.px_set(ccx + 8, ccy + 3)
    canvas.px_set(ccx + 7, ccy + 4)
    # Steam from cup
    for s in range(3):
        for dy in range(5):
            sx = ccx + 2 + s * 2 + int(math.sin(dy * 1.0 + frame_idx * 0.7 + s) * 1.2)
            canvas.px_set(sx, ccy - 2 - dy)

    # ── Round tables (right side) ──
    for tx, ty in [(155, 70), (210, 72)]:
        # Table top (ellipse)
        for dx in range(-14, 15):
            for dy in range(-2, 3):
                if dx * dx * 4 + dy * dy * 49 <= 196:
                    if _dither_check(tx + dx, ty + dy, 0.18):
                        canvas.px_set(tx + dx, ty + dy)
        draw_vline(tx, ty + 3, ty + 22)
        # Base
        draw_hline(tx - 6, tx + 6, ty + 22)
        # Coffee cup on table
        draw_rect(tx - 3, ty - 4, 5, 4)
        canvas.px_set(tx + 2, ty - 3)

    # ── Pendant lamps ──
    for lx in [50, 130, 195]:
        draw_vline(lx, 0, 10)
        # Shade (cone)
        for row in range(6):
            hw = 2 + row
            shade = 0.15 + row * 0.04
            for dx in range(-hw, hw + 1):
                if _dither_check(lx + dx, 10 + row, shade):
                    canvas.px_set(lx + dx, 10 + row)
        draw_line(lx - 2, 10, lx - 8, 16)
        draw_line(lx + 2, 10, lx + 8, 16)
        # Light glow beneath (sparse)
        fill_dithered_circle(lx, 22, 8, 0.04)

    # ── Window (right wall, street view) ──
    wx, wy, ww, wh = 170, 5, 60, 45
    draw_rect(wx, wy, ww, wh)
    draw_rect(wx + 1, wy + 1, ww - 2, wh - 2)
    draw_vline(wx + ww // 2, wy, wy + wh - 1)
    # Street view through window (light dither)
    fill_dithered_rect(wx + 2, wy + 2, ww - 4, wh - 4, 0.03)
    # Buildings outside
    for bx2, bh2 in [(wx + 5, 18), (wx + 18, 25), (wx + 35, 15), (wx + 48, 20)]:
        draw_rect(bx2, wy + wh - 3 - bh2, 10, bh2)

    # ── Chairs at tables (simple outlines) ──
    for chx in [142, 168, 198, 222]:
        draw_rect(chx, 76, 8, 10)
        draw_vline(chx + 4, 72, 76)


def _draw_cafe_speaking(frame_idx):
    """Left-zone cafe for speaking mode."""
    # Wall
    gradient_vfill(0, 0, 72, 68, 0.03, 0.07)

    # Floor (wood planks)
    for y in range(68, canvas.IMG_H):
        for x in range(0, 72):
            plank = x // 14
            edge = (x % 14) == 0
            if edge or _dither_check(x, y, 0.07):
                canvas.px_set(x, y)
    draw_hline(0, 71, 68)
    draw_hline(0, 71, 69)

    # Counter edge
    fill_dithered_rect(0, 58, 72, 3, 0.25)
    draw_hline(0, 71, 58)

    # Menu board hint
    bx, by = 5, 6
    fill_dithered_rect(bx, by, 28, 20, 0.80)
    draw_rect(bx - 1, by - 1, 30, 22)
    for row in range(3):
        for tx in range(bx + 3, bx + 24, 2):
            canvas.px_clr(tx, by + 4 + row * 5)

    # Steam wisps
    for s in range(3):
        for dy in range(4):
            sx = 50 + s * 6 + int(math.sin(dy * 1.1 + frame_idx * 0.6 + s) * 1.3)
            canvas.px_set(sx, 52 - dy)

    # Pendant lamp hint
    draw_vline(40, 0, 8)
    draw_line(38, 8, 34, 12)
    draw_line(42, 8, 46, 12)


@register(
    "cafe",
    ground_y=80,
    has_weather=False,
    description="Coffee shop with espresso machine, menu board, round tables, pendant lamps",
    decor_slots=[(5, 85), (50, 90)],
)
def draw_cafe(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_cafe_full(frame_idx)
    else:
        _draw_cafe_speaking(frame_idx)
