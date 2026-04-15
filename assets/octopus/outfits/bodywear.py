"""Bodywear outfits — cape, scarf, sweater, apron, toga, hoodie."""

from ..core import canvas
from ..core.drawing import draw_line, draw_hline, draw_rect
from . import register


@register("cape", "bodywear", "Triangle behind body with fluttering edge")
def draw_cape(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not neck:
        return
    nx, ny = neck
    yo = canvas.Y_OFF
    bx = nx + canvas.body_dx
    by = ny + yo + canvas.body_dy
    # Cape triangle hanging behind (drawn before body ideally, but outline visible)
    for row in range(20):
        half_w = 3 + row
        cy = by + row
        if cy < canvas.IMG_H:
            canvas.px_set(bx - half_w, cy)
            canvas.px_set(bx + half_w, cy)
    # Bottom edge with flutter
    import math
    for dx in range(-23, 24):
        flutter = int(1.5 * math.sin(dx * 0.5))
        canvas.px_set(bx + dx, by + 20 + flutter)


@register("scarf", "bodywear", "Wrapped band around neck with trailing end")
def draw_scarf(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not neck:
        return
    nx, ny = neck
    yo = canvas.Y_OFF
    bx = nx + canvas.body_dx
    by = ny + yo + canvas.body_dy
    # Band around neck
    for dy in range(3):
        draw_hline(bx - 10, bx + 10, by - 2 + dy)
    # Knit pattern dots
    for dx in range(-9, 10, 3):
        canvas.px_clr(bx + dx, by - 1)
    # Trailing end
    for i in range(8):
        canvas.px_set(bx + 8 + i // 2, by + i)
        canvas.px_set(bx + 9 + i // 2, by + i)


@register("sweater", "bodywear", "Body-covering pattern with collar and sleeves")
def draw_sweater(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not body_center:
        return
    cx, cy = body_center
    yo = canvas.Y_OFF
    bx = cx + canvas.body_dx
    by = cy + yo + canvas.body_dy
    # Collar line
    draw_hline(bx - 6, bx + 6, by - 8)
    draw_hline(bx - 6, bx + 6, by - 7)
    # Horizontal stripe pattern on body
    for stripe_y in [by - 3, by + 2, by + 7]:
        if 0 <= stripe_y < canvas.IMG_H:
            draw_hline(bx - 15, bx + 15, stripe_y)


@register("apron", "bodywear", "Front rectangle with neck strap and tie lines")
def draw_apron(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not body_center or not neck:
        return
    cx, cy = body_center
    nx, ny = neck
    yo = canvas.Y_OFF
    bx = cx + canvas.body_dx
    by = cy + yo + canvas.body_dy
    # Neck strap
    canvas.px_set(bx, ny + yo + canvas.body_dy - 5)
    canvas.px_set(bx, ny + yo + canvas.body_dy - 4)
    # Apron front
    draw_rect(bx - 8, by - 2, 17, 18)
    # Pocket
    draw_rect(bx - 4, by + 6, 9, 6)
    # Tie lines at waist
    draw_line(bx - 8, by + 4, bx - 14, by + 7)
    draw_line(bx + 8, by + 4, bx + 14, by + 7)


@register("toga", "bodywear", "Diagonal drape from one shoulder across body")
def draw_toga(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not body_center or not neck:
        return
    cx, cy = body_center
    nx, ny = neck
    yo = canvas.Y_OFF
    bx = cx + canvas.body_dx
    by = cy + yo + canvas.body_dy
    nby = ny + yo + canvas.body_dy
    # Diagonal drape from left shoulder to right hip
    for i in range(25):
        t = i / 24.0
        x = bx - 12 + int(t * 24)
        y = nby - 3 + int(t * 18)
        canvas.px_set(x, y)
        canvas.px_set(x, y + 1)
    # Shoulder clasp
    canvas.px_set(bx - 12, nby - 3)
    canvas.px_set(bx - 12, nby - 2)
    canvas.px_set(bx - 11, nby - 3)
    # Drape folds (parallel lines)
    for offset in [4, 8]:
        for i in range(18):
            t = i / 17.0
            x = bx - 12 + offset + int(t * 20)
            y = nby - 1 + int(t * 16)
            canvas.px_set(x, y)


@register("hoodie", "bodywear", "Body covering with hood outline around dome top")
def draw_hoodie(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not dome_top or not body_center:
        return
    import math
    dx_top, dy_top = dome_top
    cx, cy = body_center
    yo = canvas.Y_OFF
    bx = cx + canvas.body_dx
    by = cy + yo + canvas.body_dy
    dtx = dx_top + canvas.body_dx
    dty = dy_top + yo + canvas.body_dy
    # Hood outline (arc around dome)
    for i in range(20):
        t = i / 19.0
        angle = math.pi * (0.15 + t * 0.7)
        hx = dtx + int(14 * math.cos(angle))
        hy = dty + 8 - int(12 * math.sin(angle))
        canvas.px_set(hx, hy)
        canvas.px_set(hx, hy + 1)
    # Body horizontal stripes
    for stripe_y in [by - 2, by + 3, by + 8]:
        if 0 <= stripe_y < canvas.IMG_H:
            draw_hline(bx - 14, bx + 14, stripe_y)
    # Pocket (kangaroo pouch)
    draw_rect(bx - 6, by + 4, 13, 6)
    # Drawstrings
    for side in [-1, 1]:
        canvas.px_set(dtx + side * 3, dty + 16)
        canvas.px_set(dtx + side * 3, dty + 17)
        canvas.px_set(dtx + side * 3, dty + 18)
