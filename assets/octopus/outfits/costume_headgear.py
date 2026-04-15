"""Costume headgear — character/fantasy themed headwear."""

import math
from ..core import canvas
from ..core.drawing import draw_hline, draw_vline, draw_line, draw_rect, draw_arc, _dither_check, fill_dithered_circle
from . import register


@register("viking_helmet", "headwear", "Rounded dome with curved horn arcs")
def draw_viking_helmet(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    by = y + canvas.Y_OFF
    # Helmet dome
    for row in range(8):
        half_w = int(8 * math.sqrt(max(0, 1 - (row / 8.0) ** 2)))
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(x + dx, by - row)
    # Nose guard
    draw_vline(x, by, by + 4)
    # Brim
    draw_hline(x - 9, x + 9, by)
    draw_hline(x - 9, x + 9, by + 1)
    # Left horn (curved outward)
    for i in range(10):
        t = i / 9.0
        hx = x - 9 - int(t * 6)
        hy = by - int(t * t * 8)
        canvas.px_set(hx, hy)
        canvas.px_set(hx, hy + 1)
    # Right horn
    for i in range(10):
        t = i / 9.0
        hx = x + 9 + int(t * 6)
        hy = by - int(t * t * 8)
        canvas.px_set(hx, hy)
        canvas.px_set(hx, hy + 1)


@register("astronaut_helmet", "headwear", "Large circle enclosing head with visor line")
def draw_astronaut_helmet(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    by = y + canvas.Y_OFF + 5  # centered on face area
    r = 16
    # Helmet circle (outline)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            dist = dx * dx + dy * dy
            if r * r - r * 2 <= dist <= r * r:
                canvas.px_set(x + dx, by + dy)
    # Visor (filled band across face area)
    for dy in range(-6, 7):
        for dx in range(-12, 13):
            if dx * dx + dy * dy <= 144 and dy > -3:
                if _dither_check(x + dx, by + dy, 0.12):
                    canvas.px_set(x + dx, by + dy)
    # Visor glare line
    for i in range(8):
        canvas.px_clr(x - 6 + i, by - 2 + i // 3)
    # Antenna nub on top
    canvas.px_set(x, by - r - 1)
    canvas.px_set(x, by - r - 2)
    canvas.px_set(x - 1, by - r - 2)
    canvas.px_set(x + 1, by - r - 2)


@register("detective_hat", "headwear", "Deerstalker with front and back brim flaps")
def draw_detective_hat(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    by = y + canvas.Y_OFF
    # Main cap dome
    for row in range(7):
        half_w = int(7 * math.sqrt(max(0, 1 - (row / 7.0) ** 2)))
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(x + dx, by - row)
    # Front brim flap (angled down-forward)
    for i in range(6):
        bx = x - 7 - i
        b_y = by + i // 2
        canvas.px_set(bx, b_y)
        canvas.px_set(bx, b_y + 1)
        canvas.px_set(bx + 1, b_y)
    # Back brim flap
    for i in range(6):
        bx = x + 7 + i
        b_y = by + i // 2
        canvas.px_set(bx, b_y)
        canvas.px_set(bx, b_y + 1)
        canvas.px_set(bx - 1, b_y)
    # Band line
    draw_hline(x - 7, x + 7, by)
    # Subtle plaid pattern on cap
    for row in range(1, 6):
        for dx in range(-5, 6, 3):
            if abs(dx) < int(6 * math.sqrt(max(0, 1 - (row / 7.0) ** 2))):
                canvas.px_clr(x + dx, by - row)


@register("wizard_hat", "headwear", "Tall floppy cone with star and moon dots")
def draw_wizard_hat(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    by = y + canvas.Y_OFF
    # Wide brim
    draw_hline(x - 12, x + 12, by)
    draw_hline(x - 11, x + 11, by + 1)
    # Tall floppy cone (curves left at top)
    for row in range(20):
        t = row / 19.0
        half_w = int(8 * (1 - t * 0.8))
        lean = -int(t * t * 8)
        cy = by - 1 - row
        canvas.px_set(x + lean - half_w, cy)
        canvas.px_set(x + lean + half_w, cy)
        if row == 0:
            draw_hline(x + lean - half_w, x + lean + half_w, cy)
    # Fill with dithered dark
    for row in range(1, 19):
        t = row / 19.0
        half_w = int(8 * (1 - t * 0.8)) - 1
        lean = -int(t * t * 8)
        cy = by - 1 - row
        for dx in range(-half_w, half_w + 1):
            if _dither_check(x + lean + dx, cy, 0.2):
                canvas.px_set(x + lean + dx, cy)
    # Star decoration
    sx, sy = x - 1, by - 8
    canvas.px_clr(sx, sy)
    canvas.px_clr(sx - 1, sy)
    canvas.px_clr(sx + 1, sy)
    canvas.px_clr(sx, sy - 1)
    canvas.px_clr(sx, sy + 1)
    # Moon decoration
    canvas.px_clr(x + 2, by - 14)
    canvas.px_clr(x + 1, by - 14)
    canvas.px_clr(x + 2, by - 13)
    # Bent tip
    canvas.px_set(x - 8, by - 21)
    canvas.px_set(x - 9, by - 21)
