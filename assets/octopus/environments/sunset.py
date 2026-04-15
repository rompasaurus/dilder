"""Sunset environment — gradient sky, sun disc, silhouettes, birds.

Rich vertical dithered gradient from dark top to light horizon, a
half-sun circle at the horizon line, layered hill silhouettes,
V-formation birds, and foreground grass/tree silhouettes.
"""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    fill_dithered_poly, _dither_check, draw_curved_surface,
)
from . import register


def _draw_sun_disc(cx, cy, radius):
    """Half-sun at horizon — filled circle clipped at horizon line."""
    for dy in range(-radius, 1):  # Only upper half
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                px, py = cx + dx, cy + dy
                if 0 <= px < canvas.IMG_W and 0 <= py < canvas.IMG_H:
                    # Lighter center, denser edges for glow
                    dist = math.sqrt(dx * dx + dy * dy) / radius
                    if dist < 0.5:
                        canvas.px_clr(px, py)  # Bright center
                    elif _dither_check(px, py, dist * 0.3):
                        canvas.px_set(px, py)
                    else:
                        canvas.px_clr(px, py)
    # Sun outline (upper arc)
    for deg in range(180, 361):
        x = cx + int(radius * math.cos(math.radians(deg)))
        y = cy + int(radius * math.sin(math.radians(deg)))
        if 0 <= x < canvas.IMG_W and 0 <= y < canvas.IMG_H:
            canvas.px_set(x, y)


def _draw_hill_silhouette(y_base, amplitude, freq, offset, max_x, density):
    """Sine-based hill silhouette filled downward with dithering."""
    for x in range(max_x):
        hill_y = y_base - int(amplitude * math.sin(x * freq + offset))
        for y in range(hill_y, y_base + 8):
            if 0 <= y < canvas.IMG_H:
                if _dither_check(x, y, density):
                    canvas.px_set(x, y)
        # Solid edge line
        if 0 <= hill_y < canvas.IMG_H:
            canvas.px_set(x, hill_y)


def _draw_birds_v(bx, by, count, spacing, frame_idx):
    """V-formation birds."""
    for i in range(count):
        for side in (-1, 1):
            ox = side * (i + 1) * spacing
            oy = (i + 1) * (spacing // 2)
            x = bx + ox
            y = by + oy
            anim = int(1.5 * math.sin(frame_idx * 0.6 + i * 0.8))
            if 0 <= x < canvas.IMG_W and 0 <= y < canvas.IMG_H:
                canvas.px_set(x - 1, y + anim)
                canvas.px_set(x, y - 1 + anim)
                canvas.px_set(x + 1, y + anim)


def _draw_tree_silhouette(tx, ground_y, height, canopy_r):
    """Solid black tree silhouette."""
    # Trunk
    for y in range(ground_y - height, ground_y):
        canvas.px_set(tx, y)
        canvas.px_set(tx + 1, y)
    # Canopy (solid dark circle)
    cy = ground_y - height - canopy_r // 2
    for dy_c in range(-canopy_r, canopy_r + 1):
        for dx_c in range(-canopy_r, canopy_r + 1):
            if dx_c * dx_c + dy_c * dy_c <= canopy_r * canopy_r:
                px, py = tx + dx_c, cy + dy_c
                if 0 <= px < canvas.IMG_W and 0 <= py < canvas.IMG_H:
                    canvas.px_set(px, py)


def _draw_grass_silhouettes(ground_y, max_x):
    """Foreground grass tufts as silhouettes."""
    for gx in range(0, max_x, 5):
        h = 3 + (gx * 7) % 5
        lean = (gx * 3) % 3 - 1
        for i in range(h):
            x = gx + (lean * i) // h
            y = ground_y - i
            if 0 <= x < max_x and 0 <= y < canvas.IMG_H:
                canvas.px_set(x, y)


def _draw_water_reflection(horizon_y, sun_cx, max_x):
    """Dithered water reflection below the horizon."""
    water_h = canvas.IMG_H - horizon_y
    for y in range(horizon_y + 1, canvas.IMG_H):
        depth = (y - horizon_y) / max(water_h, 1)
        for x in range(max_x):
            # Reflection column under sun is brighter
            dist_to_sun = abs(x - sun_cx)
            reflect = max(0.02, 0.15 - dist_to_sun * 0.003)
            density = 0.05 + depth * 0.12 + reflect * (1 - depth)
            if _dither_check(x, y, density):
                canvas.px_set(x, y)
    # Horizontal shimmer lines
    for y in range(horizon_y + 4, canvas.IMG_H, 5):
        x_start = max(0, sun_cx - 20)
        x_end = min(max_x - 1, sun_cx + 20)
        draw_hline(x_start, x_end, y)


def _draw_sunset_full(frame_idx):
    """Full-canvas panoramic sunset (idle mode)."""
    W, H = canvas.IMG_W, canvas.IMG_H
    horizon_y = 65

    # Sky gradient — dense (dark) at top, very light near horizon
    gradient_vfill(0, 0, W, horizon_y, 0.40, 0.04)

    # Sun disc at horizon
    sun_cx = 160
    _draw_sun_disc(sun_cx, horizon_y, 14)

    # Sun rays (radial lines from sun, fading)
    for angle in range(-160, -20, 15):
        rx0 = sun_cx + int(16 * math.cos(math.radians(angle)))
        ry0 = horizon_y + int(16 * math.sin(math.radians(angle)))
        rx1 = sun_cx + int(40 * math.cos(math.radians(angle)))
        ry1 = horizon_y + int(40 * math.sin(math.radians(angle)))
        # Dithered ray — only some pixels
        dx_r = rx1 - rx0
        dy_r = ry1 - ry0
        steps = max(abs(dx_r), abs(dy_r), 1)
        for s in range(steps):
            t = s / steps
            px = int(rx0 + dx_r * t)
            py = int(ry0 + dy_r * t)
            if 0 <= px < W and 0 <= py < H:
                if _dither_check(px, py, 0.15 * (1 - t)):
                    canvas.px_set(px, py)

    # Layered hill silhouettes (far to near, progressively darker)
    _draw_hill_silhouette(horizon_y + 5, 6, 0.025, 0.0, W, 0.25)
    _draw_hill_silhouette(horizon_y + 12, 5, 0.035, 1.5, W, 0.40)
    _draw_hill_silhouette(horizon_y + 20, 4, 0.05, 3.0, W, 0.55)

    # Water reflection below hills
    water_start = horizon_y + 28
    _draw_water_reflection(water_start, sun_cx, W)

    # Tree silhouettes on hills
    _draw_tree_silhouette(40, horizon_y + 10, 12, 7)
    _draw_tree_silhouette(75, horizon_y + 8, 10, 5)
    _draw_tree_silhouette(210, horizon_y + 14, 14, 8)

    # V-formation birds
    _draw_birds_v(100, 20, 4, 5, frame_idx)
    _draw_birds_v(60, 30, 3, 4, frame_idx)

    # Foreground grass silhouettes
    _draw_grass_silhouettes(horizon_y + 25, W)


def _draw_sunset_speaking(frame_idx):
    """Left-zone sunset for speaking mode."""
    horizon_y = 65

    # Sky gradient
    gradient_vfill(0, 0, 72, horizon_y, 0.35, 0.03)

    # Sun on horizon (partially visible, right edge of speaking zone)
    _draw_sun_disc(60, horizon_y, 10)

    # Hill silhouette
    _draw_hill_silhouette(horizon_y + 5, 4, 0.04, 0.5, 72, 0.30)
    _draw_hill_silhouette(horizon_y + 12, 3, 0.06, 2.0, 72, 0.50)

    # Ground below
    for y in range(horizon_y + 18, 122):
        for x in range(72):
            depth = (y - horizon_y - 18) / max(122 - horizon_y - 18, 1)
            if _dither_check(x, y, 0.06 + depth * 0.10):
                canvas.px_set(x, y)

    # Tree silhouette
    _draw_tree_silhouette(15, horizon_y + 8, 10, 6)

    # Birds
    _draw_birds_v(35, 18, 3, 4, frame_idx)

    # Grass
    _draw_grass_silhouettes(horizon_y + 18, 72)


@register(
    "sunset",
    ground_y=85,
    has_weather=False,
    description="Panoramic sunset with gradient sky, sun disc, layered hills, birds, water reflection",
    decor_slots=[(5, 95), (55, 92)],
)
def draw_sunset(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_sunset_full(frame_idx)
    else:
        _draw_sunset_speaking(frame_idx)
