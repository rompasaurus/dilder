"""Library environment — tall bookshelves, reading lamp, armchair, ladder."""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    fill_dithered_poly, _dither_check, draw_curved_surface,
)
from . import register


def _draw_books_on_shelf(sx, sy, shelf_w):
    """Draw a row of books with varying spine widths and dither shading."""
    x = sx
    while x < sx + shelf_w - 2:
        bw = 2 + (x * 7 + sy * 3) % 4
        bh = 12 + (x * 3 + sy) % 5
        if x + bw > sx + shelf_w:
            break
        shade = 0.15 + ((x * 11 + sy * 7) % 10) * 0.06
        fill_dithered_rect(x, sy - bh, bw, bh, shade)
        # Spine line detail
        if bw >= 3:
            draw_vline(x + bw // 2, sy - bh + 2, sy - 3)
        x += bw + 1


def _draw_library_full(frame_idx):
    """Full-canvas grand library scene (idle mode)."""
    W, H = canvas.IMG_W, canvas.IMG_H

    # ── Back wall ──
    gradient_vfill(0, 0, W, 90, 0.02, 0.06)

    # ── Carpet (patterned floor) ──
    for y in range(90, H):
        for x in range(0, W):
            # Diamond pattern on carpet
            cx = (x % 16) - 8
            cy = (y % 12) - 6
            if abs(cx) + abs(cy) < 5:
                if _dither_check(x, y, 0.12):
                    canvas.px_set(x, y)
            elif _dither_check(x, y, 0.04):
                canvas.px_set(x, y)
    draw_thick_line(0, 90, W - 1, 90, 2)

    # ── Tall bookshelves (background, three sections) ──
    for section_x, section_w in [(0, 70), (85, 65), (165, 80)]:
        # Shelf frame
        draw_rect(section_x, 5, section_w, 83)
        draw_vline(section_x + 1, 5, 87)
        draw_vline(section_x + section_w - 2, 5, 87)
        # Shelf rows
        for shelf_y in [25, 42, 58, 74, 87]:
            draw_hline(section_x, section_x + section_w - 1, shelf_y)
            draw_hline(section_x, section_x + section_w - 1, shelf_y + 1)
            _draw_books_on_shelf(section_x + 3, shelf_y, section_w - 6)

    # ── Ladder against left shelf ──
    lx = 60
    draw_line(lx, 10, lx - 8, 88)
    draw_line(lx + 5, 10, lx - 3, 88)
    # Rungs
    for ry in range(18, 85, 10):
        t = (ry - 10) / 78.0
        x_off = int(-8 * t)
        draw_hline(lx + x_off, lx + 5 + x_off, ry)

    # ── Armchair (center-right) ──
    ax, ay = 130, 65
    # Back rest (curved)
    for row in range(18):
        hw = 12 + int(3 * math.sin(row * 0.2))
        shade = 0.20 + 0.05 * (row / 18.0)
        for dx in range(-hw, hw + 1):
            if _dither_check(ax + dx, ay + row, shade):
                canvas.px_set(ax + dx, ay + row)
    # Seat cushion
    fill_dithered_rect(ax - 12, ay + 18, 24, 8, 0.15)
    draw_rect(ax - 12, ay + 18, 24, 8)
    # Armrests
    fill_dithered_rect(ax - 16, ay + 10, 5, 16, 0.25)
    fill_dithered_rect(ax + 11, ay + 10, 5, 16, 0.25)
    # Legs
    draw_vline(ax - 10, ay + 26, ay + 32)
    draw_vline(ax + 10, ay + 26, ay + 32)

    # ── Reading lamp (next to armchair) ──
    lamp_x, lamp_y = 155, 35
    # Tall stem
    draw_vline(lamp_x, lamp_y + 12, ay + 30)
    # Base
    draw_hline(lamp_x - 5, lamp_x + 5, ay + 30)
    # Shade (angled cone)
    for row in range(8):
        hw = 2 + row
        for dx in range(-hw, hw + 1):
            shade = 0.12 + 0.04 * row / 7
            if _dither_check(lamp_x - 4 + dx, lamp_y + row, shade):
                canvas.px_set(lamp_x - 4 + dx, lamp_y + row)
    draw_line(lamp_x - 6, lamp_y, lamp_x - 14, lamp_y + 8)
    draw_line(lamp_x - 2, lamp_y, lamp_x + 6, lamp_y + 8)
    # Warm glow circle
    fill_dithered_circle(lamp_x - 4, lamp_y + 14, 12, 0.04)

    # ── Small side table (by armchair) ──
    draw_hline(ax + 18, ax + 34, ay + 20)
    draw_vline(ax + 22, ay + 20, ay + 30)
    draw_vline(ax + 30, ay + 20, ay + 30)
    # Book on table
    fill_dithered_rect(ax + 23, ay + 16, 8, 4, 0.30)

    # ── Globe on far right ──
    gx, gy = 220, 60
    draw_curved_surface(gx, gy, 10, 10, 0.08, 0.35)
    # Equator line
    for dx in range(-9, 10):
        dy = int(1.5 * math.sin(dx * 0.3))
        canvas.px_set(gx + dx, gy + dy)
    # Stand
    draw_vline(gx, gy + 11, gy + 20)
    draw_hline(gx - 5, gx + 5, gy + 20)


def _draw_library_speaking(frame_idx):
    """Left-zone library for speaking mode."""
    # Wall
    gradient_vfill(0, 0, 72, 90, 0.02, 0.05)

    # Carpet strip
    for y in range(90, canvas.IMG_H):
        for x in range(0, 72):
            cx = (x % 12) - 6
            cy = (y % 10) - 5
            if abs(cx) + abs(cy) < 4:
                if _dither_check(x, y, 0.10):
                    canvas.px_set(x, y)
    draw_hline(0, 71, 90)

    # Bookshelf section
    draw_rect(0, 3, 55, 85)
    for shelf_y in [22, 40, 56, 72, 86]:
        draw_hline(0, 54, shelf_y)
        _draw_books_on_shelf(3, shelf_y, 48)

    # Lamp glow (right edge)
    fill_dithered_circle(62, 40, 9, 0.04)
    # Lamp stem hint
    draw_vline(65, 30, 88)
    draw_hline(60, 70, 88)


@register(
    "library",
    ground_y=90,
    has_weather=False,
    description="Grand library with tall bookshelves, reading lamp, armchair, ladder, carpet",
    decor_slots=[(5, 95), (50, 95)],
)
def draw_library(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_library_full(frame_idx)
    else:
        _draw_library_speaking(frame_idx)
