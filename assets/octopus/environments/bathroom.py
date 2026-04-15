"""Bathroom environment — bathtub with bubbles, tile walls, mirror, rubber duck."""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    fill_dithered_poly, _dither_check, draw_curved_surface,
)
from . import register


def _draw_tile_wall(x0, y0, w, h, tile_size=8):
    """Draw a tile grid pattern with subtle dithered grout lines."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            row = (y - y0) // tile_size
            col = (x - x0) // tile_size
            # Offset every other row (brick pattern)
            offset = (tile_size // 2) * (row % 2)
            tx = (x - x0 + offset) % tile_size
            ty = (y - y0) % tile_size
            if tx == 0 or ty == 0:
                if _dither_check(x, y, 0.18):
                    canvas.px_set(x, y)


def _draw_bathroom_full(frame_idx):
    """Full-canvas bathroom scene (idle mode)."""
    W, H = canvas.IMG_W, canvas.IMG_H

    # ── Tile walls ──
    _draw_tile_wall(0, 0, W, 78, tile_size=10)

    # ── Floor (wet, reflective) ──
    for y in range(78, H):
        for x in range(0, W):
            if _dither_check(x, y, 0.05):
                canvas.px_set(x, y)
    draw_thick_line(0, 78, W - 1, 78, 2)

    # ── Bathtub (center-left, large) ──
    tx, ty = 20, 55
    tw, th = 100, 35
    # Tub body (rounded with shading)
    fill_dithered_poly(
        [(tx, ty + 8), (tx + tw, ty + 8),
         (tx + tw - 5, ty + th), (tx + 5, ty + th)],
        0.10
    )
    # Rim (thick line)
    draw_thick_line(tx - 2, ty + 8, tx + tw + 2, ty + 8, 3)
    # Curved ends
    for i in range(8):
        draw_hline(tx + 5 - i, tx + 8, ty + 8 + i)
        draw_hline(tx + tw - 8, tx + tw - 5 + i, ty + 8 + i)
    # Feet (claw foot)
    for fx in [tx + 10, tx + tw - 10]:
        draw_line(fx, ty + th, fx - 3, ty + th + 5)
        draw_line(fx, ty + th, fx + 3, ty + th + 5)
        canvas.px_set(fx - 4, ty + th + 5)
        canvas.px_set(fx + 4, ty + th + 5)

    # Bubble suds (clusters of dithered circles on water surface)
    bubbles = [(35, 52), (50, 48), (65, 51), (80, 49), (95, 53),
               (42, 45), (72, 46), (58, 55), (88, 50), (105, 52)]
    for bx, by in bubbles:
        r = 3 + (bx * 7 + by) % 3
        fill_dithered_circle(bx, by, r, 0.08)
        # Highlight (clear center pixel)
        canvas.px_clr(bx - 1, by - 1)

    # Faucet
    draw_rect(tx + tw // 2 - 4, ty - 5, 8, 8)
    draw_hline(tx + tw // 2 - 8, tx + tw // 2 - 4, ty - 2)
    draw_hline(tx + tw // 2 + 4, tx + tw // 2 + 8, ty - 2)
    # Drip animation
    drip_y = ty + 4 + (frame_idx % 6)
    canvas.px_set(tx + tw // 2, drip_y)

    # ── Rubber duck (in tub) ──
    dx, dy = 90, 47
    # Body
    draw_curved_surface(dx, dy, 5, 4, 0.05, 0.20)
    # Head
    for ddx in range(-2, 3):
        for ddy in range(-2, 3):
            if ddx * ddx + ddy * ddy <= 4:
                canvas.px_set(dx + 5 + ddx, dy - 3 + ddy)
    # Eye
    canvas.px_set(dx + 6, dy - 4)
    # Beak
    canvas.px_set(dx + 8, dy - 3)
    canvas.px_set(dx + 9, dy - 3)

    # ── Mirror (on wall, right side) ──
    mx, my = 170, 8
    mw, mh = 40, 35
    # Frame (ornate double border)
    draw_rect(mx - 2, my - 2, mw + 4, mh + 4)
    draw_rect(mx - 1, my - 1, mw + 2, mh + 2)
    draw_rect(mx, my, mw, mh)
    # Mirror surface (very light)
    fill_dithered_rect(mx + 1, my + 1, mw - 2, mh - 2, 0.02)
    # Reflection hint (faint shape)
    fill_dithered_circle(mx + mw // 2, my + mh // 2, 8, 0.04)

    # ── Towel rack (far right wall) ──
    rx, ry = 225, 20
    draw_hline(rx, rx + 20, ry)
    draw_hline(rx, rx + 20, ry + 1)
    # Towel hanging (draped with folds)
    for row in range(22):
        wave = int(2 * math.sin(row * 0.5))
        for dx in range(16):
            shade = 0.15 + 0.05 * math.sin(dx * 0.5 + row * 0.3)
            if _dither_check(rx + 2 + dx + wave, ry + 3 + row, shade):
                canvas.px_set(rx + 2 + dx + wave, ry + 3 + row)

    # ── Soap dispenser (on tub rim) ──
    sx, sy = 35, ty - 8
    draw_rect(sx, sy, 6, 8)
    draw_vline(sx + 3, sy - 4, sy)
    draw_hline(sx + 3, sx + 6, sy - 4)

    # ── Wet floor puddle (dithered) ──
    for ddx in range(-15, 16):
        for ddy in range(-3, 4):
            if ddx * ddx * 9 + ddy * ddy * 225 <= 225 * 9:
                if _dither_check(140 + ddx, 100 + ddy, 0.10):
                    canvas.px_set(140 + ddx, 100 + ddy)

    # ── Steam wisps (above tub) ──
    for s in range(5):
        for step in range(6):
            sx2 = 40 + s * 16 + int(2 * math.sin(step * 0.8 + frame_idx * 0.5 + s))
            canvas.px_set(sx2, 38 - step)


def _draw_bathroom_speaking(frame_idx):
    """Left-zone bathroom for speaking mode."""
    # Tile wall
    _draw_tile_wall(0, 0, 72, 65, tile_size=8)

    # Floor
    draw_hline(0, 71, 65)
    draw_hline(0, 71, 66)
    for y in range(67, canvas.IMG_H):
        for x in range(0, 72):
            if _dither_check(x, y, 0.04):
                canvas.px_set(x, y)

    # Bathtub edge (rim)
    draw_thick_line(0, 58, 72, 58, 3)
    # Tub interior hint
    gradient_vfill(0, 61, 72, 4, 0.06, 0.10)

    # Bubbles (small clusters)
    for bx, by in [(12, 53), (30, 50), (50, 54), (22, 47), (42, 52)]:
        r = 2 + (bx + by) % 2
        fill_dithered_circle(bx, by, r, 0.07)
        canvas.px_clr(bx, by - 1)

    # Steam
    for s in range(3):
        for dy in range(4):
            sx = 15 + s * 18 + int(math.sin(dy * 1.0 + frame_idx * 0.6 + s) * 1.5)
            canvas.px_set(sx, 42 - dy)

    # Mirror hint (upper right)
    draw_rect(55, 5, 14, 18)
    draw_rect(56, 6, 12, 16)
    fill_dithered_rect(57, 7, 10, 14, 0.02)


@register(
    "bathroom",
    ground_y=78,
    has_weather=False,
    description="Bathroom with bathtub, bubbles, tile walls, mirror, towel rack, rubber duck",
    decor_slots=[(5, 85), (50, 90)],
)
def draw_bathroom(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_bathroom_full(frame_idx)
    else:
        _draw_bathroom_speaking(frame_idx)
