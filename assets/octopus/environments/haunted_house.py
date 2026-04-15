"""Haunted house environment — cobwebs, bats, candle, broken chandelier, spider."""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    fill_dithered_poly, _dither_check, draw_curved_surface,
)
from . import register


def _draw_cobweb(cx, cy, size, direction=1):
    """Draw a cobweb radiating from corner point (cx, cy).

    direction: 1 = upper-left corner, -1 = upper-right.
    """
    # Radial threads
    for i in range(5):
        angle = (math.pi / 2) * i / 4
        ex = cx + int(direction * size * math.cos(angle))
        ey = cy + int(size * math.sin(angle))
        draw_line(cx, cy, ex, ey)
    # Connecting arcs (concentric rings)
    for ring in range(2, size, max(3, size // 4)):
        for i in range(20):
            angle = (math.pi / 2) * i / 19
            x = cx + int(direction * ring * math.cos(angle))
            y = cy + int(ring * math.sin(angle))
            canvas.px_set(x, y)


def _draw_bat(x, y, frame_idx, offset=0):
    """Draw a small bat (V-shape wings with flap animation)."""
    flap = 1 if (frame_idx + offset) % 4 < 2 else -1
    # Body
    canvas.px_set(x, y)
    canvas.px_set(x, y + 1)
    # Wings
    for w in range(1, 5):
        wy = y - w * flap + (w // 3)
        canvas.px_set(x - w, wy)
        canvas.px_set(x + w, wy)


def _draw_haunted_full(frame_idx):
    """Full-canvas haunted house scene (idle mode)."""
    W, H = canvas.IMG_W, canvas.IMG_H

    # ── Dark atmosphere (heavy dithered walls) ──
    gradient_vfill(0, 0, W, 85, 0.08, 0.18)

    # ── Cracked floorboards ──
    for y in range(85, H):
        for x in range(0, W):
            board = x // 18
            edge = (x % 18) in (0, 17)
            if edge:
                canvas.px_set(x, y)
            elif _dither_check(x, y, 0.10):
                canvas.px_set(x, y)
    draw_thick_line(0, 85, W - 1, 85, 2)
    # Floor cracks
    draw_line(40, 90, 55, 105)
    draw_line(130, 88, 140, 100)
    draw_line(200, 92, 190, 108)

    # ── Crooked window (left wall) ──
    wx, wy = 20, 15
    # Tilted frame (slightly off-angle)
    draw_line(wx, wy, wx + 35, wy + 2)
    draw_line(wx, wy, wx - 2, wy + 40)
    draw_line(wx + 35, wy + 2, wx + 33, wy + 42)
    draw_line(wx - 2, wy + 40, wx + 33, wy + 42)
    # Crossbars (also crooked)
    draw_line(wx + 17, wy + 1, wx + 15, wy + 41)
    draw_line(wx - 1, wy + 20, wx + 34, wy + 22)
    # Broken pane (missing glass, dark)
    fill_dithered_rect(wx + 1, wy + 3, 15, 17, 0.30)
    # Moonlight through window
    fill_dithered_rect(wx + 18, wy + 4, 14, 16, 0.05)
    # Moon
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if dx * dx + dy * dy <= 16:
                canvas.px_set(wx + 28 + dx, wy + 10 + dy)

    # ── Cobwebs ──
    _draw_cobweb(0, 0, 22, direction=1)
    _draw_cobweb(W - 1, 0, 18, direction=-1)
    _draw_cobweb(80, 0, 14, direction=1)

    # ── Broken chandelier (center ceiling) ──
    ch_cx = 125
    # Chain
    draw_vline(ch_cx, 0, 15)
    # Main ring (tilted — one side lower)
    draw_line(ch_cx - 15, 16, ch_cx + 15, 20)
    draw_line(ch_cx - 15, 18, ch_cx + 15, 22)
    # Hanging arms (some broken)
    for arm_x, arm_len, broken in [(-12, 10, False), (-5, 12, True),
                                    (3, 8, False), (10, 14, True)]:
        ex = ch_cx + arm_x
        ey = 18 + (arm_x + 15) * 4 // 30
        if broken:
            draw_vline(ex, ey, ey + arm_len // 2)
            # Dangling piece
            draw_line(ex, ey + arm_len // 2, ex + 2, ey + arm_len)
        else:
            draw_vline(ex, ey, ey + arm_len)
            # Candle stub
            draw_rect(ex - 1, ey + arm_len, 3, 3)

    # ── Flickering candle (on floor, right area) ──
    candle_x, candle_y = 180, 72
    # Candle body
    draw_rect(candle_x - 2, candle_y, 5, 13)
    fill_dithered_rect(candle_x - 1, candle_y + 1, 3, 11, 0.12)
    # Flame (animated flicker)
    flicker = int(2 * math.sin(frame_idx * 1.5))
    fx = candle_x + flicker
    for dy in range(-5, 0):
        hw = max(0, 2 + dy)
        for dx in range(-hw, hw + 1):
            canvas.px_set(fx + dx, candle_y + dy)
    # Glow
    fill_dithered_circle(candle_x, candle_y - 2, 10, 0.03)

    # ── Tilted painting (right wall) ──
    px, py = 195, 25
    # Tilted frame
    draw_line(px, py, px + 30, py - 3)
    draw_line(px, py, px - 2, py + 25)
    draw_line(px + 30, py - 3, px + 28, py + 22)
    draw_line(px - 2, py + 25, px + 28, py + 22)
    # Dark interior
    fill_dithered_poly(
        [(px + 2, py + 2), (px + 28, py - 1),
         (px + 26, py + 20), (px, py + 23)],
        0.25
    )
    # Eyes in painting (creepy)
    canvas.px_set(px + 10, py + 8)
    canvas.px_set(px + 18, py + 7)

    # ── Bats ──
    for bx, by, off in [(90, 8, 0), (150, 12, 2), (210, 6, 1),
                         (170, 18, 3), (100, 20, 5)]:
        _draw_bat(bx, by, frame_idx, off)

    # ── Spider (hanging from chandelier) ──
    sp_x, sp_y = ch_cx + 8, 38
    # Thread
    draw_vline(sp_x, 22, sp_y)
    # Body
    fill_dithered_circle(sp_x, sp_y, 2, 0.7)
    canvas.px_set(sp_x, sp_y + 3)  # abdomen
    # Legs (four per side)
    for i, angle_off in enumerate([0.3, 0.8, 1.3, 1.8]):
        lx = sp_x + int(3 * math.cos(angle_off))
        ly = sp_y + int(2 * math.sin(angle_off))
        canvas.px_set(lx, ly)
        canvas.px_set(sp_x - (lx - sp_x), ly)

    # ── Spooky shadows (dithered pools along walls) ──
    fill_dithered_rect(0, 70, 18, 15, 0.22)
    fill_dithered_rect(230, 65, 20, 20, 0.20)
    gradient_vfill(60, 75, 30, 10, 0.15, 0.05)


def _draw_haunted_speaking(frame_idx):
    """Left-zone haunted house for speaking mode."""
    # Dark wall
    gradient_vfill(0, 0, 72, 85, 0.07, 0.15)

    # Cracked floor
    for y in range(85, canvas.IMG_H):
        for x in range(0, 72):
            if (x % 16) in (0, 15) or _dither_check(x, y, 0.09):
                canvas.px_set(x, y)
    draw_hline(0, 71, 85)
    draw_line(20, 88, 30, 100)

    # Cobweb (upper-left corner)
    _draw_cobweb(0, 0, 18, direction=1)

    # Crooked window
    wx, wy = 30, 10
    draw_line(wx, wy, wx + 25, wy + 1)
    draw_line(wx, wy, wx - 1, wy + 28)
    draw_line(wx + 25, wy + 1, wx + 24, wy + 29)
    draw_line(wx - 1, wy + 28, wx + 24, wy + 29)
    draw_line(wx + 12, wy, wx + 11, wy + 28)
    fill_dithered_rect(wx + 1, wy + 2, 10, 25, 0.25)
    # Moon
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if dx * dx + dy * dy <= 9:
                canvas.px_set(wx + 20 + dx, wy + 10 + dy)

    # Candle
    cx, cy = 60, 70
    draw_rect(cx - 1, cy, 4, 10)
    flicker = int(math.sin(frame_idx * 1.5))
    for dy in range(-3, 0):
        hw = max(0, 1 + dy)
        for dx in range(-hw, hw + 1):
            canvas.px_set(cx + flicker + dx, cy + dy)
    fill_dithered_circle(cx, cy - 1, 6, 0.03)

    # Bat
    _draw_bat(15, 50, frame_idx)

    # Shadow pool
    fill_dithered_rect(0, 75, 15, 10, 0.18)


@register(
    "haunted_house",
    ground_y=85,
    has_weather=True,
    description="Haunted house with cobwebs, bats, crooked window, candle, broken chandelier",
    decor_slots=[(5, 90), (50, 95)],
)
def draw_haunted_house(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_haunted_full(frame_idx)
    else:
        _draw_haunted_speaking(frame_idx)
