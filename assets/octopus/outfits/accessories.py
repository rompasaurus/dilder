"""Accessories — bandana, bow tie, earring, necklace, watch."""

from ..core import canvas
from ..core.drawing import draw_hline
from . import register


@register("bandana", "accessories", "Tied band around dome with trailing ends")
def draw_bandana(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not dome_top:
        return
    x, y = dome_top
    by = y + canvas.Y_OFF + 6  # sits mid-dome
    bx = x + canvas.body_dx
    by += canvas.body_dy
    # Band
    for dy in range(2):
        draw_hline(bx - 10, bx + 10, by + dy)
    # Trailing triangle ends (right side)
    for i in range(5):
        canvas.px_set(bx + 10 + i, by + i)
        canvas.px_set(bx + 10 + i, by + i + 1)


@register("bow_tie", "accessories", "Small X-shape at neck center")
def draw_bow_tie(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not neck:
        return
    x, y = neck
    bx = x + canvas.body_dx
    by = y + canvas.Y_OFF + canvas.body_dy
    # Left triangle
    canvas.px_set(bx - 3, by - 1)
    canvas.px_set(bx - 2, by)
    canvas.px_set(bx - 3, by + 1)
    canvas.px_set(bx - 1, by)
    # Center knot
    canvas.px_set(bx, by)
    # Right triangle
    canvas.px_set(bx + 3, by - 1)
    canvas.px_set(bx + 2, by)
    canvas.px_set(bx + 3, by + 1)
    canvas.px_set(bx + 1, by)


@register("necklace", "accessories", "Dotted arc below neck with pendant")
def draw_necklace(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not neck:
        return
    import math
    x, y = neck
    bx = x + canvas.body_dx
    by = y + canvas.Y_OFF + canvas.body_dy
    # Arc
    for i in range(12):
        t = i / 11.0
        angle = math.pi * 0.2 + t * math.pi * 0.6
        ax = bx + int(10 * math.cos(angle))
        ay = by + int(6 * math.sin(angle))
        canvas.px_set(ax, ay)
    # Pendant dot at bottom center
    canvas.px_set(bx, by + 6)
    canvas.px_set(bx, by + 7)
    canvas.px_set(bx - 1, by + 7)
    canvas.px_set(bx + 1, by + 7)


@register("flower_crown", "accessories", "Ring of petal clusters on dome with leaf dots")
def draw_flower_crown(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not dome_top:
        return
    import math
    x, y = dome_top
    by = y + canvas.Y_OFF + canvas.body_dy + 3
    bx = x + canvas.body_dx
    # Crown ring following dome curve
    for i in range(12):
        t = i / 11.0
        angle = math.pi * (0.15 + t * 0.7)
        fx = bx + int(11 * math.cos(angle))
        fy = by + 3 - int(8 * math.sin(angle))
        # Flower (3px cluster)
        canvas.px_set(fx, fy - 1)
        canvas.px_set(fx - 1, fy)
        canvas.px_set(fx + 1, fy)
        canvas.px_set(fx, fy + 1)
        # Center dot
        if i % 2 == 0:
            canvas.px_clr(fx, fy)
        # Leaf between flowers
        if i < 11:
            lx = bx + int(11 * math.cos(angle + 0.15))
            ly = by + 3 - int(8 * math.sin(angle + 0.15))
            canvas.px_set(lx, ly)


@register("halo", "accessories", "Dithered ellipse floating above dome top")
def draw_halo(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not dome_top:
        return
    x, y = dome_top
    bx = x + canvas.body_dx
    by = y + canvas.Y_OFF + canvas.body_dy - 5
    # Ellipse ring (wider than tall)
    rx, ry = 10, 3
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            dist = (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry)
            if 0.6 <= dist <= 1.0:
                from ..core.drawing import _dither_check
                if _dither_check(bx + dx, by + dy, 0.4):
                    canvas.px_set(bx + dx, by + dy)


@register("devil_horns", "accessories", "Two pointed triangles on dome sides with tail")
def draw_devil_horns(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not dome_top or not body_center:
        return
    import math
    x, y = dome_top
    bx = x + canvas.body_dx
    by = y + canvas.Y_OFF + canvas.body_dy
    cx, cy = body_center
    bcx = cx + canvas.body_dx
    bcy = cy + canvas.Y_OFF + canvas.body_dy
    # Left horn
    for row in range(8):
        half_w = max(0, 2 - row // 3)
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(bx - 8 + dx, by + 2 - row)
    # Right horn
    for row in range(8):
        half_w = max(0, 2 - row // 3)
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(bx + 8 + dx, by + 2 - row)
    # Pointed tips
    canvas.px_set(bx - 8, by - 6)
    canvas.px_set(bx + 8, by - 6)
    # Tail (curling from back/bottom)
    for i in range(12):
        t = i / 11.0
        tx = bcx + 15 + int(5 * math.sin(t * math.pi * 1.5))
        ty = bcy + 10 + int(t * 15)
        canvas.px_set(tx, ty)
        canvas.px_set(tx + 1, ty)
    # Arrow tip
    last_x = bcx + 15 + int(5 * math.sin(math.pi * 1.5))
    last_y = bcy + 25
    canvas.px_set(last_x - 2, last_y - 1)
    canvas.px_set(last_x + 2, last_y - 1)
    canvas.px_set(last_x, last_y + 1)
