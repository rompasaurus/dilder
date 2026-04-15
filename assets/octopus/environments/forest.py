"""Forest environment -- dense trees, dappled light, mushrooms, ferns, owl.

Layered depth with background trees (light dither) and foreground trunks
(dark bark texture). Leaf litter floor with dithered ground cover.
"""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    fill_dithered_poly, _dither_check, draw_curved_surface,
)
from . import register


def _draw_trunk(tx, y_top, y_bot, width, shade=0.55):
    """Draw a textured tree trunk with bark lines."""
    hw = width // 2
    for y in range(y_top, y_bot):
        for dx in range(-hw, hw + 1):
            bark = shade + 0.1 * math.sin(y * 0.9 + dx * 3)
            if _dither_check(tx + dx, y, bark):
                canvas.px_set(tx + dx, y)
    draw_vline(tx - hw, y_top, y_bot)
    draw_vline(tx + hw, y_top, y_bot)


def _draw_mushroom(mx, my, cap_w=5, cap_h=3):
    """Small mushroom with rounded cap and stem."""
    # Stem
    draw_vline(mx, my - cap_h, my)
    draw_vline(mx + 1, my - cap_h, my)
    # Cap (dithered dome)
    for dy in range(-cap_h, 1):
        half = cap_w - abs(dy)
        for dx in range(-half, half + 1):
            shade = 0.3 + 0.15 * (1.0 - abs(dy) / max(cap_h, 1))
            if _dither_check(mx + dx, my - cap_h + dy - 1, shade):
                canvas.px_set(mx + dx, my - cap_h + dy - 1)
    # Spots (clear a couple pixels on cap for white dots)
    canvas.px_clr(mx - 1, my - cap_h - 1)
    canvas.px_clr(mx + 2, my - cap_h)


def _draw_fern(fx, fy, height=8):
    """Small fern frond curving upward."""
    for i in range(height):
        cx = fx + int(1.5 * math.sin(i * 0.5))
        cy = fy - i
        canvas.px_set(cx, cy)
        # Side leaflets
        if i > 1 and i % 2 == 0:
            spread = max(1, (height - i) // 2)
            for s in range(1, spread + 1):
                canvas.px_set(cx - s, cy + s // 2)
                canvas.px_set(cx + s, cy + s // 2)


def _draw_owl(ox, oy):
    """Small owl silhouette perched on a branch."""
    # Body (filled oval)
    for dy in range(-5, 6):
        hw = int(3 * math.sqrt(max(0, 1 - (dy / 5.0) ** 2)))
        for dx in range(-hw, hw + 1):
            canvas.px_set(ox + dx, oy + dy)
    # Ear tufts
    canvas.px_set(ox - 2, oy - 6)
    canvas.px_set(ox + 2, oy - 6)
    canvas.px_set(ox - 3, oy - 7)
    canvas.px_set(ox + 3, oy - 7)
    # Eyes (clear two circles)
    for ex in [-1, 1]:
        canvas.px_clr(ox + ex, oy - 2)
        canvas.px_clr(ox + ex, oy - 1)


def _draw_forest_full(frame_idx):
    """Full-canvas dense forest (idle mode)."""
    W, H = canvas.IMG_W, canvas.IMG_H
    ground_y = 80

    # ── Canopy sky (glimpses through leaves, very light) ──
    gradient_vfill(0, 0, W, ground_y - 15, 0.02, 0.06)

    # ── Dappled light spots (animated, flickering) ──
    spots = [(30, 25), (80, 18), (135, 22), (190, 15), (220, 28),
             (55, 35), (110, 30), (170, 38), (240, 20)]
    for sx, sy in spots:
        phase = frame_idx * 0.4 + sx * 0.1
        r = 2 + int(1.5 * abs(math.sin(phase)))
        fill_dithered_circle(sx, sy, r, 0.03)

    # ── Background trees (far, small, light dither) ──
    for tx, th, cw in [(40, 18, 10), (90, 15, 8), (145, 20, 12),
                        (195, 16, 9), (230, 14, 7)]:
        ty = ground_y - 8
        _draw_trunk(tx, ty - th, ty, 2, shade=0.2)
        draw_curved_surface(tx, ty - th - cw // 2, cw, int(cw * 0.7),
                            density_center=0.08, density_edge=0.18)

    # ── Mid-ground trees (medium detail) ──
    for tx, th, cw in [(20, 28, 16), (110, 30, 18), (175, 25, 14)]:
        ty = ground_y - 3
        _draw_trunk(tx, ty - th, ty, 3, shade=0.4)
        cy = ty - th - cw // 2
        draw_curved_surface(tx, cy, cw, int(cw * 0.8),
                            density_center=0.15, density_edge=0.35)
        # Side clusters
        draw_curved_surface(tx - int(cw * 0.5), cy + 3,
                            int(cw * 0.5), int(cw * 0.4),
                            density_center=0.12, density_edge=0.30)
        draw_curved_surface(tx + int(cw * 0.5), cy + 3,
                            int(cw * 0.5), int(cw * 0.4),
                            density_center=0.12, density_edge=0.30)

    # ── Foreground tree trunks (large, detailed bark, partial view) ──
    _draw_trunk(0, 10, H, 6, shade=0.6)       # left edge trunk
    _draw_trunk(240, 5, H, 7, shade=0.55)      # right edge trunk
    # Branch from left trunk
    draw_thick_line(6, 40, 30, 28, 2)
    # Owl perched on left branch
    _draw_owl(25, 24)

    # ── Ground / leaf litter ──
    for y in range(ground_y, H):
        depth = (y - ground_y) / max(H - ground_y - 1, 1)
        for x in range(W):
            shade = 0.08 + depth * 0.06
            # Leaf texture variation
            shade += 0.04 * math.sin(x * 0.7 + y * 1.1)
            if _dither_check(x, y, shade):
                canvas.px_set(x, y)
    draw_thick_line(0, ground_y, W - 1, ground_y, 2)

    # ── Mushroom clusters ──
    _draw_mushroom(60, ground_y + 8, 4, 3)
    _draw_mushroom(68, ground_y + 10, 3, 2)
    _draw_mushroom(155, ground_y + 6, 5, 3)
    _draw_mushroom(200, ground_y + 12, 4, 3)

    # ── Ferns ──
    _draw_fern(80, ground_y + 2, 10)
    _draw_fern(130, ground_y + 4, 8)
    _draw_fern(210, ground_y + 3, 9)

    # ── Fallen log (mid-ground) ──
    fill_dithered_poly(
        [(95, ground_y + 15), (140, ground_y + 12),
         (142, ground_y + 16), (95, ground_y + 19)],
        0.35
    )
    draw_line(95, ground_y + 15, 140, ground_y + 12)
    draw_line(95, ground_y + 19, 142, ground_y + 16)

    # ── Roots at base of foreground trunks ──
    for rx, ry, dx in [(4, ground_y + 2, 1), (6, ground_y + 4, 1),
                        (236, ground_y + 2, -1), (234, ground_y + 5, -1)]:
        draw_thick_line(rx, ry, rx + dx * 8, ry + 4, 2)


def _draw_forest_speaking(frame_idx):
    """Left-zone forest for speaking mode."""
    ground_y = 80

    # Dim canopy light
    gradient_vfill(0, 0, 72, ground_y - 10, 0.02, 0.05)

    # Dappled light spots
    for sx, sy in [(15, 20), (45, 28), (60, 15)]:
        phase = frame_idx * 0.4 + sx * 0.1
        r = 2 + int(abs(math.sin(phase)))
        fill_dithered_circle(sx, sy, r, 0.03)

    # Two tree trunks
    _draw_trunk(5, 0, canvas.IMG_H, 4, shade=0.55)
    _draw_trunk(60, 15, canvas.IMG_H, 3, shade=0.45)

    # Canopy overhead hint
    draw_curved_surface(5, -5, 14, 10, density_center=0.10, density_edge=0.25)
    draw_curved_surface(60, 8, 12, 9, density_center=0.10, density_edge=0.25)

    # Ground / leaf litter
    draw_hline(0, 71, ground_y)
    for y in range(ground_y + 1, canvas.IMG_H):
        depth = (y - ground_y) / max(canvas.IMG_H - ground_y - 1, 1)
        for x in range(72):
            shade = 0.06 + depth * 0.05 + 0.03 * math.sin(x * 0.7 + y)
            if _dither_check(x, y, shade):
                canvas.px_set(x, y)

    # Mushrooms
    _draw_mushroom(25, ground_y + 7, 4, 2)
    _draw_mushroom(45, ground_y + 10, 3, 2)

    # Small fern
    _draw_fern(35, ground_y + 2, 6)


@register(
    "forest",
    ground_y=80,
    has_weather=False,
    description="Dense forest with layered trees, dappled light, mushrooms, ferns, owl",
    decor_slots=[(10, 95), (50, 98)],
)
def draw_forest(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_forest_full(frame_idx)
    else:
        _draw_forest_speaking(frame_idx)
