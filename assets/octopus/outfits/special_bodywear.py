"""Special bodywear — occasion/event specific body outfits."""

import math
from ..core import canvas
from ..core.drawing import (
    draw_hline, draw_vline, draw_line, draw_rect,
    fill_dithered_rect, _dither_check, draw_arc,
)
from . import register


@register("rain_coat", "bodywear", "Buttoned front with hood, drip dots on edges")
def draw_rain_coat(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not body_center or not dome_top:
        return
    cx, cy = body_center
    dx_top, dy_top = dome_top
    yo = canvas.Y_OFF
    bx = cx + canvas.body_dx
    by = cy + yo + canvas.body_dy
    dtx = dx_top + canvas.body_dx
    dty = dy_top + yo + canvas.body_dy
    # Hood outline
    for i in range(16):
        t = i / 15.0
        angle = math.pi * (0.2 + t * 0.6)
        hx = dtx + int(12 * math.cos(angle))
        hy = dty + 6 - int(10 * math.sin(angle))
        canvas.px_set(hx, hy)
    # Body covering
    for row in range(-5, 18):
        y = by + row
        half_w = 14 + (row // 4)
        # Outline
        canvas.px_set(bx - half_w, y)
        canvas.px_set(bx + half_w, y)
    # Bottom edge
    draw_hline(bx - 16, bx + 16, by + 17)
    # Center button line
    for dot_y in range(by - 3, by + 15, 4):
        canvas.px_set(bx, dot_y)
    # Drip dots on edges
    for i in range(4):
        dy = by + 18 + (i % 3)
        canvas.px_set(bx - 14 + i * 8, dy)


@register("hospital_gown", "bodywear", "Open-back rectangle with tie dots")
def draw_hospital_gown(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not body_center:
        return
    cx, cy = body_center
    yo = canvas.Y_OFF
    bx = cx + canvas.body_dx
    by = cy + yo + canvas.body_dy
    # Gown body (thin dithered fabric)
    for row in range(-6, 16):
        y = by + row
        for dx in range(-13, 14):
            if _dither_check(bx + dx, y, 0.08):
                canvas.px_set(bx + dx, y)
    # Outline
    draw_vline(bx - 13, by - 6, by + 15)
    draw_vline(bx + 13, by - 6, by + 15)
    draw_hline(bx - 13, bx + 13, by - 6)
    draw_hline(bx - 13, bx + 13, by + 15)
    # Collar V
    draw_line(bx - 4, by - 6, bx, by - 2)
    draw_line(bx + 4, by - 6, bx, by - 2)
    # Tie dots (at back/side)
    for ty in [by - 3, by + 3, by + 9]:
        canvas.px_set(bx + 13, ty)
        canvas.px_set(bx + 14, ty)
        canvas.px_set(bx + 15, ty + 1)


@register("tuxedo", "bodywear", "Lapel V-lines with button dots and bow tie")
def draw_tuxedo(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not body_center or not neck:
        return
    cx, cy = body_center
    nx, ny = neck
    yo = canvas.Y_OFF
    bx = cx + canvas.body_dx
    by = cy + yo + canvas.body_dy
    nby = ny + yo + canvas.body_dy
    # Lapel lines (V shape)
    draw_line(bx - 10, nby - 2, bx - 2, by + 5)
    draw_line(bx + 10, nby - 2, bx + 2, by + 5)
    draw_line(bx - 9, nby - 2, bx - 1, by + 5)
    draw_line(bx + 9, nby - 2, bx + 1, by + 5)
    # Center button line
    for dot_y in range(by, by + 12, 3):
        canvas.px_set(bx, dot_y)
    # Bow tie at neck
    canvas.px_set(bx - 3, nby)
    canvas.px_set(bx - 2, nby - 1)
    canvas.px_set(bx - 2, nby + 1)
    canvas.px_set(bx - 1, nby)
    canvas.px_set(bx, nby)
    canvas.px_set(bx + 1, nby)
    canvas.px_set(bx + 2, nby - 1)
    canvas.px_set(bx + 2, nby + 1)
    canvas.px_set(bx + 3, nby)
    # Pocket square (left lapel)
    draw_rect(bx - 8, by + 1, 4, 3)


@register("wedding_veil", "bodywear", "Draped dotted mesh arc from dome trailing down")
def draw_wedding_veil(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not dome_top:
        return
    x, y = dome_top
    yo = canvas.Y_OFF
    dtx = x + canvas.body_dx
    dty = y + yo + canvas.body_dy
    # Veil origin (top of dome)
    # Draping mesh (dithered, trails behind)
    for row in range(30):
        t = row / 29.0
        width = int(5 + t * 20)
        cy = dty + 2 + row
        for dx in range(0, width):
            px = dtx + 5 + dx
            if _dither_check(px, cy, 0.06 + t * 0.04):
                canvas.px_set(px, cy)
    # Edge scallop
    for i in range(8):
        sx = dtx + 5 + i * 3
        sy = dty + 32 + int(1.5 * math.sin(i * 1.2))
        canvas.px_set(sx, sy)
        canvas.px_set(sx + 1, sy)


@register("superhero_suit", "bodywear", "Chest emblem with lightning bolt and belt")
def draw_superhero_suit(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not body_center:
        return
    cx, cy = body_center
    yo = canvas.Y_OFF
    bx = cx + canvas.body_dx
    by = cy + yo + canvas.body_dy
    # Chest emblem circle
    r = 6
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            dist = dx * dx + dy * dy
            if r * r - r <= dist <= r * r:
                canvas.px_set(bx + dx, by - 2 + dy)
    # Lightning bolt inside emblem
    bolt = [(bx + 1, by - 6), (bx - 2, by - 2), (bx + 1, by - 2),
            (bx - 2, by + 2), (bx + 1, by + 2)]
    for i in range(len(bolt) - 1):
        draw_line(bolt[i][0], bolt[i][1], bolt[i + 1][0], bolt[i + 1][1])
    # Belt line
    draw_hline(bx - 12, bx + 12, by + 8)
    draw_hline(bx - 12, bx + 12, by + 9)
    # Belt buckle
    draw_rect(bx - 2, by + 7, 5, 4)
    canvas.px_clr(bx, by + 9)


@register("wizard_robe", "bodywear", "Long draping lines with star dots and belt sash")
def draw_wizard_robe(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not body_center:
        return
    cx, cy = body_center
    yo = canvas.Y_OFF
    bx = cx + canvas.body_dx
    by = cy + yo + canvas.body_dy
    # Draping robe edges
    for row in range(-5, 20):
        y = by + row
        half_w = 12 + row // 3
        canvas.px_set(bx - half_w, y)
        canvas.px_set(bx + half_w, y)
    draw_hline(bx - 18, bx + 18, by + 19)
    # Star dots pattern
    for sx, sy in [(bx - 6, by - 2), (bx + 5, by + 3), (bx - 3, by + 8),
                   (bx + 7, by + 10), (bx - 8, by + 5)]:
        canvas.px_set(sx, sy)
        canvas.px_set(sx + 1, sy)
        canvas.px_set(sx, sy + 1)
    # Belt sash
    draw_hline(bx - 10, bx + 10, by + 6)
    draw_hline(bx - 10, bx + 10, by + 7)
    # Sash trailing end
    for i in range(5):
        canvas.px_set(bx + 10 + i // 2, by + 7 + i)
        canvas.px_set(bx + 10 + i // 2 + 1, by + 7 + i)
