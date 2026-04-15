"""Eyewear outfits — drawn relative to eye socket center anchors.

VISIBILITY RULE: The octopus body is black. Eyewear is drawn over/near the
white eye sockets, but any part overlapping the black body must clear white
first, then draw black detail.
"""

from ..core import canvas
from ..core.drawing import draw_rect, draw_line, draw_hline
from . import register


@register("sunglasses", "eyewear", "Two filled dark rectangles over eyes with bridge")
def draw_sunglasses(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not eye_centers:
        return
    (lx, ly), (rx, ry) = eye_centers
    yo = canvas.Y_OFF
    bdx, bdy = canvas.body_dx, canvas.body_dy
    # Lens frames — first clear a slightly larger white border
    for ecx in [lx + bdx, rx + bdx]:
        ecy = ly + yo + bdy
        for dy in range(-4, 5):
            for dx in range(-6, 6):
                canvas.px_clr(ecx + dx, ecy + dy)
    # Dark lenses (filled black)
    for ecx in [lx + bdx, rx + bdx]:
        ecy = ly + yo + bdy
        for dy in range(-3, 4):
            for dx in range(-5, 5):
                canvas.px_set(ecx + dx, ecy + dy)
    # White glare dot on each lens
    canvas.px_clr(lx + bdx - 2, ly + yo + bdy - 1)
    canvas.px_clr(rx + bdx - 2, ry + yo + bdy - 1)
    # Bridge
    bx0 = lx + 5 + bdx
    bx1 = rx - 5 + bdx
    by = ly + yo + bdy
    draw_hline(bx0, bx1, by)


@register("monocle", "eyewear", "Circle over right eye with chain line")
def draw_monocle(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not eye_centers:
        return
    (_, _), (rx, ry) = eye_centers
    yo = canvas.Y_OFF
    cx = rx + canvas.body_dx
    cy = ry + yo + canvas.body_dy
    # Clear white ring area
    r = 6
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                canvas.px_clr(cx + dx, cy + dy)
    # Black circle outline
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            dist = dx * dx + dy * dy
            if r * r - r <= dist <= r * r + 1:
                canvas.px_set(cx + dx, cy + dy)
    # Chain trailing down (white gap then black links)
    for i in range(8):
        canvas.px_clr(cx + 1 + i // 3, cy + r + i)
        canvas.px_set(cx + 1 + i // 3, cy + r + i + 1)


@register("goggles", "eyewear", "Two large circles over eyes with strap line")
def draw_goggles(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not eye_centers:
        return
    (lx, ly), (rx, ry) = eye_centers
    yo = canvas.Y_OFF
    bdx, bdy = canvas.body_dx, canvas.body_dy
    r = 7
    # Clear white circles
    for ecx in [lx + bdx, rx + bdx]:
        ecy = ly + yo + bdy
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    canvas.px_clr(ecx + dx, ecy + dy)
    # Black circle outlines
    for ecx in [lx + bdx, rx + bdx]:
        ecy = ly + yo + bdy
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                dist = dx * dx + dy * dy
                if r * r - r <= dist <= r * r + 1:
                    canvas.px_set(ecx + dx, ecy + dy)
    # Strap line (clear white line, then black line above)
    strap_y = ly + yo + bdy - 5
    for sx in range(lx - 8 + bdx, rx + 8 + bdx):
        canvas.px_clr(sx, strap_y)
        canvas.px_clr(sx, strap_y + 1)
    for sx in range(lx - 8 + bdx, rx + 8 + bdx):
        canvas.px_set(sx, strap_y)


@register("snorkel_mask", "eyewear", "Large single lens with snorkel tube")
def draw_snorkel_mask(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not eye_centers:
        return
    (lx, ly), (rx, ry) = eye_centers
    yo = canvas.Y_OFF
    bdx, bdy = canvas.body_dx, canvas.body_dy
    cx = (lx + rx) // 2 + bdx
    cy = ly + yo + bdy
    # Clear white oval lens area
    for dy in range(-6, 7):
        for dx in range(-16, 17):
            if dx * dx * 36 + dy * dy * 256 <= 9216:
                canvas.px_clr(cx + dx, cy + dy)
    # Black oval outline
    for dy in range(-6, 7):
        for dx in range(-16, 17):
            dist = dx * dx * 36 + dy * dy * 256
            if 8000 <= dist <= 9216:
                canvas.px_set(cx + dx, cy + dy)
    # Strap (clear then outline)
    for sx in range(cx - 18, cx + 19):
        canvas.px_clr(sx, cy - 4)
        canvas.px_set(sx, cy - 5)
    # Snorkel tube (clear tube then outline)
    tube_x = cx - 16
    for i in range(14):
        canvas.px_clr(tube_x, cy - 5 - i)
        canvas.px_clr(tube_x - 1, cy - 5 - i)
    for i in range(14):
        canvas.px_set(tube_x + 1, cy - 5 - i)
        canvas.px_set(tube_x - 2, cy - 5 - i)
    # Snorkel top
    for dx in range(-2, 3):
        canvas.px_set(tube_x + dx, cy - 19)


@register("eye_patch", "eyewear", "Filled circle over left eye with diagonal strap")
def draw_eye_patch(dome_top=None, eye_centers=None, neck=None, body_center=None):
    if not eye_centers:
        return
    (lx, ly), (rx, ry) = eye_centers
    yo = canvas.Y_OFF
    bdx, bdy = canvas.body_dx, canvas.body_dy
    cx = lx + bdx
    cy = ly + yo + bdy
    r = 5
    # Clear white ring then fill black patch
    for dy in range(-r - 1, r + 2):
        for dx in range(-r - 1, r + 2):
            if dx * dx + dy * dy <= (r + 1) * (r + 1):
                canvas.px_clr(cx + dx, cy + dy)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                canvas.px_set(cx + dx, cy + dy)
    # Diagonal strap (clear then draw)
    for i in range(12):
        sx = cx - r + i
        sy = cy - 2 - i
        canvas.px_clr(sx, sy)
        canvas.px_clr(sx, sy - 1)
    for i in range(12):
        canvas.px_set(cx - r + i, cy - 2 - i)
    # Other strap direction
    for i in range(12):
        sx = cx + r - 2 + i // 2
        sy = cy - 2 - i
        canvas.px_set(sx, sy)
