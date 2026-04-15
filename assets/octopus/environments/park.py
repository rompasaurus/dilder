"""Park environment — 3D outdoor scene with trees, bench, path, sky.

Uses dithered shading for tree canopies, textured grass, perspective path,
layered depth (foreground darker, background lighter).
"""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_hline, draw_line, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    fill_dithered_poly, _dither_check, draw_curved_surface,
)
from . import register


def _draw_tree(tx, ground_y, trunk_h, canopy_r, depth_shade=0.0):
    """Draw a tree with dithered canopy shading and textured trunk."""
    # Trunk (textured bark)
    tw = max(2, canopy_r // 3)
    for y in range(ground_y - trunk_h, ground_y):
        for dx in range(-tw // 2, tw // 2 + 1):
            shade = 0.5 + 0.1 * math.sin(y * 0.8 + dx * 2)
            if _dither_check(tx + dx, y, shade):
                canvas.px_set(tx + dx, y)
    # Trunk outline
    draw_vline(tx - tw // 2, ground_y - trunk_h, ground_y)
    draw_vline(tx + tw // 2, ground_y - trunk_h, ground_y)

    # Canopy (multiple overlapping dithered circles for organic shape)
    cy = ground_y - trunk_h - canopy_r // 2
    base_shade = 0.25 + depth_shade
    # Main dome
    draw_curved_surface(tx, cy, canopy_r, int(canopy_r * 0.8),
                        density_center=base_shade * 0.5,
                        density_edge=base_shade)
    # Side clusters
    for ox, oy, sr in [(-canopy_r * 0.6, canopy_r * 0.2, canopy_r * 0.6),
                       (canopy_r * 0.6, canopy_r * 0.2, canopy_r * 0.6),
                       (0, -canopy_r * 0.3, canopy_r * 0.5)]:
        draw_curved_surface(tx + int(ox), cy + int(oy),
                            int(sr), int(sr * 0.8),
                            density_center=base_shade * 0.4,
                            density_edge=base_shade * 0.9)


def _draw_park_full(frame_idx):
    """Full-canvas park scene (idle mode)."""
    W, H = canvas.IMG_W, canvas.IMG_H
    ground_y = 70

    # ── Sky gradient (lighter at horizon) ──
    gradient_vfill(0, 0, W, ground_y, 0.01, 0.06)

    # ── Clouds (puffy, dithered) ──
    for ccx, ccy, scale in [(40, 12, 1.0), (130, 8, 1.3), (200, 15, 0.8)]:
        for r, ox, oy in [(int(7 * scale), 0, 0),
                          (int(5 * scale), int(-6 * scale), int(1 * scale)),
                          (int(5 * scale), int(6 * scale), int(1 * scale)),
                          (int(4 * scale), int(0), int(-3 * scale))]:
            fill_dithered_circle(ccx + ox, ccy + oy, r, 0.15)

    # ── Background hills (far, light dither) ──
    for x in range(W):
        hill_h = int(8 * math.sin(x * 0.02 + 0.5) + 5 * math.sin(x * 0.05))
        for y in range(ground_y - 15 - hill_h, ground_y - 10):
            if _dither_check(x, y, 0.08):
                canvas.px_set(x, y)

    # ── Ground / Grass ──
    # Base grass fill
    for y in range(ground_y, H):
        depth = (y - ground_y) / max(H - ground_y - 1, 1)
        shade = 0.05 + depth * 0.05
        for x in range(W):
            if _dither_check(x, y, shade):
                canvas.px_set(x, y)

    # Grass tufts (detailed V shapes, denser in foreground)
    tufts = [
        (8, 80), (25, 78), (50, 82), (70, 76), (95, 84), (120, 79),
        (150, 83), (175, 77), (200, 81), (225, 85), (240, 78),
        (15, 95), (40, 100), (65, 92), (90, 105), (110, 98),
        (140, 102), (170, 95), (195, 110), (220, 100), (235, 108),
        (30, 112), (80, 115), (130, 118), (180, 112), (210, 116),
    ]
    for gx, gy in tufts:
        h = 3 + (gx * 7 + gy * 3) % 4
        # V-shape grass blades
        for i in range(h):
            canvas.px_set(gx - 1 - i // 2, gy - i)
            canvas.px_set(gx + 1 + i // 2, gy - i)
            canvas.px_set(gx, gy - i)

    # Ground line
    draw_thick_line(0, ground_y, W - 1, ground_y, 2)

    # ── Background trees (small, light) ──
    _draw_tree(180, ground_y, 12, 8, depth_shade=-0.05)
    _draw_tree(210, ground_y, 10, 7, depth_shade=-0.05)

    # ── Foreground tree (left, large, detailed) ──
    _draw_tree(30, ground_y + 5, 25, 18, depth_shade=0.05)

    # ── Foreground tree (right, medium) ──
    _draw_tree(220, ground_y + 3, 20, 14, depth_shade=0.03)

    # ── Bench (mid-ground, 3D) ──
    bench_x, bench_y = 100, ground_y + 3
    # Shadow
    fill_dithered_rect(bench_x + 2, bench_y + 16, 40, 5, 0.12)
    # Legs
    draw_thick_line(bench_x + 3, bench_y + 8, bench_x + 3, bench_y + 16, 2)
    draw_thick_line(bench_x + 37, bench_y + 8, bench_x + 37, bench_y + 16, 2)
    # Seat planks (3 horizontal bars with gaps)
    for py in [bench_y + 5, bench_y + 7, bench_y + 9]:
        draw_hline(bench_x, bench_x + 40, py)
    # Back rest
    draw_vline(bench_x + 2, bench_y - 10, bench_y + 5)
    draw_vline(bench_x + 38, bench_y - 10, bench_y + 5)
    for py in [bench_y - 8, bench_y - 5, bench_y - 2]:
        draw_hline(bench_x + 2, bench_x + 38, py)

    # ── Winding path (perspective, wider at bottom) ──
    for i in range(50):
        t = i / 49.0
        cx = 140 + int(30 * math.sin(t * math.pi * 1.2))
        cy = ground_y + 5 + int(t * (H - ground_y - 10))
        width = int(3 + t * 10)
        for dx in range(-width, width + 1):
            x = cx + dx
            if 0 <= x < W:
                edge = abs(dx) >= width - 1
                if edge:
                    canvas.px_set(x, cy)
                elif _dither_check(x, cy, 0.08):
                    canvas.px_set(x, cy)

    # ── Birds (V shapes in sky) ──
    for bx, by in [(60, 18), (85, 12), (110, 20), (160, 10)]:
        anim = int(2 * math.sin(frame_idx * 0.8 + bx * 0.1))
        canvas.px_set(bx - 3, by + anim)
        canvas.px_set(bx - 2, by - 1 + anim)
        canvas.px_set(bx - 1, by + anim)
        canvas.px_set(bx, by + 1 + anim)
        canvas.px_set(bx + 1, by + anim)
        canvas.px_set(bx + 2, by - 1 + anim)
        canvas.px_set(bx + 3, by + anim)

    # ── Flowers near path ──
    for fx, fy in [(125, ground_y + 10), (155, ground_y + 15), (135, ground_y + 25)]:
        # Stem
        draw_vline(fx, fy - 5, fy)
        # Petals (5 dots around center)
        for angle in range(0, 360, 72):
            px = fx + int(2 * math.cos(math.radians(angle)))
            py = fy - 5 + int(2 * math.sin(math.radians(angle)))
            canvas.px_set(px, py)
        canvas.px_set(fx, fy - 5)


def _draw_park_speaking(frame_idx):
    """Left-zone park for speaking mode."""
    ground_y = 75

    # Sky
    gradient_vfill(0, 0, 72, ground_y, 0.01, 0.05)

    # Hills
    for x in range(72):
        hill_h = int(5 * math.sin(x * 0.04))
        for y in range(ground_y - 8 - hill_h, ground_y - 5):
            if _dither_check(x, y, 0.06):
                canvas.px_set(x, y)

    # Ground
    draw_hline(0, 71, ground_y)
    for y in range(ground_y + 1, canvas.IMG_H):
        depth = (y - ground_y) / max(canvas.IMG_H - ground_y - 1, 1)
        for x in range(72):
            if _dither_check(x, y, 0.04 + depth * 0.04):
                canvas.px_set(x, y)

    # Tree
    _draw_tree(55, ground_y + 3, 18, 12, 0.0)

    # Grass tufts
    for gx, gy in [(8, 80), (25, 85), (45, 82), (60, 88), (15, 100), (35, 110)]:
        for i in range(3):
            canvas.px_set(gx - 1, gy - i)
            canvas.px_set(gx + 1, gy - i)
            canvas.px_set(gx, gy - i)

    # Cloud
    fill_dithered_circle(25, 10, 5, 0.12)
    fill_dithered_circle(20, 11, 3, 0.12)
    fill_dithered_circle(30, 11, 3, 0.12)

    # Bird
    for bx, by in [(40, 15)]:
        canvas.px_set(bx - 2, by)
        canvas.px_set(bx - 1, by - 1)
        canvas.px_set(bx, by)
        canvas.px_set(bx + 1, by - 1)
        canvas.px_set(bx + 2, by)


@register(
    "park",
    ground_y=70,
    has_weather=True,
    description="3D park with textured trees, dithered canopies, perspective path, grass, clouds",
    decor_slots=[(5, 90), (55, 92)],
)
def draw_park(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_park_full(frame_idx)
    else:
        _draw_park_speaking(frame_idx)
