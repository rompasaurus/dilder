"""Mountain environment -- rocky peaks, layered ranges, clouds, eagle, flag.

Panoramic vista with depth-sorted mountain silhouettes (far ranges light,
near ranges dark). Snow patches as white gaps, cliff edge detail.
"""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    fill_dithered_poly, _dither_check, draw_curved_surface,
)
from . import register


def _draw_mountain_range(y_base, peaks, density, snow_line=None):
    """Draw a mountain range as connected peaks with dithered fill.

    peaks: list of (x, height) tuples for peak positions.
    snow_line: if set, pixels above this y are cleared for snow effect.
    """
    W = canvas.IMG_W
    # Build height map by interpolating between peaks
    heights = [0] * W
    for i in range(len(peaks) - 1):
        x0, h0 = peaks[i]
        x1, h1 = peaks[i + 1]
        for x in range(max(0, x0), min(W, x1 + 1)):
            t = (x - x0) / max(x1 - x0, 1)
            heights[x] = int(h0 + (h1 - h0) * t)
    # Extend edges
    if peaks[0][0] > 0:
        for x in range(peaks[0][0]):
            heights[x] = peaks[0][1]
    if peaks[-1][0] < W - 1:
        for x in range(peaks[-1][0], W):
            heights[x] = peaks[-1][1]

    # Fill mountain body
    for x in range(W):
        peak_y = y_base - heights[x]
        for y in range(peak_y, y_base):
            depth = (y - peak_y) / max(y_base - peak_y, 1)
            shade = density * (0.6 + 0.4 * depth)
            if _dither_check(x, y, shade):
                canvas.px_set(x, y)

        # Snow patches (clear pixels above snow_line)
        if snow_line is not None and peak_y < snow_line:
            for y in range(peak_y, min(snow_line, y_base)):
                # Irregular snow edge
                noise = int(2 * math.sin(x * 0.5 + y * 0.3))
                if y < snow_line - 3 + noise:
                    canvas.px_clr(x, y)

    # Ridge line (outline along top)
    for x in range(W - 1):
        y0 = y_base - heights[x]
        y1 = y_base - heights[x + 1]
        canvas.px_set(x, y0)
        if abs(y1 - y0) > 1:
            draw_line(x, y0, x + 1, y1)


def _draw_cloud(cx, cy, scale=1.0):
    """Puffy cloud from overlapping dithered circles."""
    for r, ox, oy in [(int(6 * scale), 0, 0),
                      (int(4 * scale), int(-5 * scale), int(1 * scale)),
                      (int(4 * scale), int(5 * scale), int(1 * scale)),
                      (int(3 * scale), int(-2 * scale), int(-3 * scale))]:
        fill_dithered_circle(cx + ox, cy + oy, r, 0.12)


def _draw_eagle(ex, ey, frame_idx):
    """Soaring eagle silhouette with animated wing flap."""
    flap = int(2 * math.sin(frame_idx * 0.6))
    # Body
    draw_thick_line(ex - 2, ey, ex + 2, ey, 2)
    # Left wing
    draw_line(ex - 2, ey, ex - 8, ey - 3 + flap)
    draw_line(ex - 8, ey - 3 + flap, ex - 12, ey - 2 + flap)
    # Right wing
    draw_line(ex + 2, ey, ex + 8, ey - 3 + flap)
    draw_line(ex + 8, ey - 3 + flap, ex + 12, ey - 2 + flap)
    # Tail
    canvas.px_set(ex - 3, ey + 1)
    canvas.px_set(ex - 4, ey + 2)


def _draw_flag(fx, fy):
    """Small flag on a pole at a summit."""
    # Pole
    draw_vline(fx, fy - 14, fy)
    # Flag (triangular pennant)
    fill_dithered_poly(
        [(fx, fy - 14), (fx + 8, fy - 11), (fx, fy - 8)],
        0.45
    )
    draw_line(fx, fy - 14, fx + 8, fy - 11)
    draw_line(fx + 8, fy - 11, fx, fy - 8)


def _draw_mountain_full(frame_idx):
    """Full-canvas mountain panorama (idle mode)."""
    W, H = canvas.IMG_W, canvas.IMG_H
    ground_y = 95

    # ── Sky gradient (deep blue to light horizon) ──
    gradient_vfill(0, 0, W, 50, 0.06, 0.02)

    # ── Clouds ──
    _draw_cloud(35, 10, 1.0)
    _draw_cloud(170, 14, 1.3)
    _draw_cloud(230, 8, 0.7)

    # ── Eagle soaring ──
    _draw_eagle(100, 20, frame_idx)

    # ── Far range (lightest, distant) ──
    _draw_mountain_range(70, [
        (0, 10), (30, 22), (60, 14), (100, 28), (140, 18),
        (180, 25), (210, 12), (249, 16),
    ], density=0.10, snow_line=48)

    # ── Mid range (medium shade) ──
    _draw_mountain_range(82, [
        (0, 18), (40, 35), (80, 20), (120, 40), (160, 28),
        (200, 38), (240, 22), (249, 25),
    ], density=0.22, snow_line=50)

    # ── Near range (darkest, prominent) ──
    _draw_mountain_range(ground_y, [
        (0, 8), (25, 15), (55, 45), (80, 30), (110, 50),
        (140, 35), (170, 20), (200, 42), (230, 28), (249, 12),
    ], density=0.38, snow_line=60)

    # ── Flag on highest near peak ──
    _draw_flag(110, ground_y - 50)

    # ── Rocky cliff edge (foreground, bottom) ──
    draw_thick_line(0, ground_y, W - 1, ground_y, 2)
    for y in range(ground_y + 2, H):
        depth = (y - ground_y) / max(H - ground_y - 1, 1)
        for x in range(W):
            # Rocky texture with cracks
            shade = 0.15 + depth * 0.12 + 0.05 * math.sin(x * 1.3 + y * 0.7)
            if _dither_check(x, y, shade):
                canvas.px_set(x, y)

    # ── Rock details on cliff face ──
    for rx, ry in [(20, 102), (80, 108), (150, 104), (210, 110)]:
        draw_line(rx, ry, rx + 6, ry + 2)
        draw_line(rx + 6, ry + 2, rx + 3, ry + 5)

    # ── Scattered rocks on cliff top ──
    for rx, ry, rw, rh in [(15, ground_y - 3, 5, 4), (180, ground_y - 2, 4, 3),
                            (65, ground_y - 4, 6, 5), (230, ground_y - 2, 3, 3)]:
        fill_dithered_poly(
            [(rx, ry + rh), (rx + rw // 2, ry), (rx + rw, ry + rh)],
            0.35
        )


def _draw_mountain_speaking(frame_idx):
    """Left-zone mountain for speaking mode."""
    ground_y = 80

    # Sky
    gradient_vfill(0, 0, 72, 40, 0.04, 0.02)

    # Cloud
    _draw_cloud(50, 8, 0.6)

    # Far range (light)
    for x in range(72):
        h = int(8 * math.sin(x * 0.06 + 1) + 5 * math.sin(x * 0.12))
        peak_y = 45 - h
        for y in range(peak_y, 50):
            if _dither_check(x, y, 0.08):
                canvas.px_set(x, y)
        canvas.px_set(x, peak_y)

    # Near range (darker, prominent peak)
    peaks_near = [(0, 6), (15, 22), (35, 35), (55, 18), (71, 10)]
    heights = [0] * 72
    for i in range(len(peaks_near) - 1):
        x0, h0 = peaks_near[i]
        x1, h1 = peaks_near[i + 1]
        for x in range(x0, min(72, x1 + 1)):
            t = (x - x0) / max(x1 - x0, 1)
            heights[x] = int(h0 + (h1 - h0) * t)

    for x in range(72):
        peak_y = ground_y - heights[x]
        for y in range(peak_y, ground_y):
            depth = (y - peak_y) / max(ground_y - peak_y, 1)
            shade = 0.30 * (0.5 + 0.5 * depth)
            if _dither_check(x, y, shade):
                canvas.px_set(x, y)
        canvas.px_set(x, peak_y)

    # Snow on peak
    for x in range(25, 45):
        peak_y = ground_y - heights[x]
        snow_depth = max(0, 3 - abs(x - 35) // 3)
        for y in range(peak_y, peak_y + snow_depth):
            canvas.px_clr(x, y)

    # Rocky ground
    draw_hline(0, 71, ground_y)
    for y in range(ground_y + 1, canvas.IMG_H):
        depth = (y - ground_y) / max(canvas.IMG_H - ground_y - 1, 1)
        for x in range(72):
            shade = 0.10 + depth * 0.08 + 0.03 * math.sin(x * 1.3 + y * 0.7)
            if _dither_check(x, y, shade):
                canvas.px_set(x, y)

    # Small rock
    fill_dithered_poly([(10, ground_y), (14, ground_y - 4), (18, ground_y)], 0.30)


@register(
    "mountain",
    ground_y=95,
    has_weather=True,
    description="Panoramic mountain vista with layered ranges, snow, eagle, flag, cliff edge",
    decor_slots=[(8, 105), (50, 108)],
)
def draw_mountain(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_mountain_full(frame_idx)
    else:
        _draw_mountain_speaking(frame_idx)
