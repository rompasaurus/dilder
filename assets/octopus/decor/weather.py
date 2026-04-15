"""Weather effect overlays — rain, snow, sun rays, clouds, lightning, wind.

These are drawn AFTER the environment and character as overlays.
They take frame_idx for animation and density for intensity control.
"""

import math
from ..core import canvas
from ..core.drawing import draw_line, draw_hline
from . import register


@register("rain", "weather", 70, 122, "Diagonal 3px falling lines, density param")
def draw_rain(x=0, y=0, frame_idx=0, density=8):
    """Rain drops across the left 70px (character area)."""
    for i in range(density):
        # Deterministic positions
        seed = (i * 37 + frame_idx * 13) % 997
        rx = seed % 70
        seed = (seed * 31 + 17) % 997
        ry = (seed % 100 + frame_idx * 5 + i * 12) % 122
        # Diagonal 3px line
        for d in range(3):
            px, py = rx + d, ry + d
            if 0 <= px < 70 and 0 <= py < 122:
                canvas.px_set(px, py)


@register("snow", "weather", 70, 122, "Single scattered dots falling slowly")
def draw_snow(x=0, y=0, frame_idx=0, density=12):
    """Snowflakes drifting down across character area."""
    for i in range(density):
        seed = (i * 43 + 7) % 997
        sx = seed % 70
        seed = (seed * 31 + 17) % 997
        sy = (seed % 110 + frame_idx * 2 + i * 9) % 122
        drift = int(1.5 * math.sin(sy * 0.1 + i))
        px = sx + drift
        if 0 <= px < 70:
            canvas.px_set(px, sy)


@register("sun_rays", "weather", 30, 30, "Lines radiating from corner circle")
def draw_sun_rays(x=0, y=0, frame_idx=0, density=0):
    """Sun with radiating rays in upper-left corner."""
    cx, cy = 8, 8
    r = 5
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                canvas.px_set(cx + dx, cy + dy)
    for angle in range(0, 360, 30):
        a_rad = math.radians(angle + frame_idx * 5)
        r0 = 6
        r1 = 10 + (angle % 60 == 0) * 3
        x0 = cx + int(r0 * math.cos(a_rad))
        y0 = cy + int(r0 * math.sin(a_rad))
        x1 = cx + int(r1 * math.cos(a_rad))
        y1 = cy + int(r1 * math.sin(a_rad))
        draw_line(x0, y0, x1, y1)


@register("clouds", "weather", 70, 30, "Overlapping circle clusters")
def draw_clouds(x=0, y=0, frame_idx=0, density=0):
    """Cloud puffs in upper sky area."""
    cloud_defs = [
        (12, 8, [(0, 0, 5), (-5, 1, 3), (5, 1, 3)]),
        (45, 5, [(0, 0, 4), (-4, 1, 3), (4, 1, 3), (0, -2, 3)]),
    ]
    drift = int(math.sin(frame_idx * 0.3) * 2)
    for ccx, ccy, circles in cloud_defs:
        for ox, oy, r in circles:
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r:
                        px = ccx + ox + dx + drift
                        py = ccy + oy + dy
                        if 0 <= px < 70 and 0 <= py < 122:
                            canvas.px_set(px, py)


@register("lightning", "weather", 20, 60, "Zigzag bolt from top, flash frame")
def draw_lightning(x=30, y=0, frame_idx=0, density=0):
    """Lightning bolt — only visible on certain frames (flash effect)."""
    if frame_idx % 4 != 0:
        return  # flash only on every 4th frame
    # Zigzag bolt
    points = [(x, 5), (x - 4, 20), (x + 2, 22), (x - 3, 40),
              (x + 4, 42), (x - 2, 60)]
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        draw_line(x0, y0, x1, y1)
        # Thicken bolt
        draw_line(x0 + 1, y0, x1 + 1, y1)


@register("wind", "weather", 70, 50, "Horizontal wavy lines across canvas")
def draw_wind(x=0, y=0, frame_idx=0, density=0):
    """Wind streaks — horizontal wavy lines."""
    for i in range(4):
        by = 20 + i * 20
        phase = frame_idx * 0.8 + i * 1.5
        for wx in range(5, 65):
            wy = by + int(1.5 * math.sin(wx * 0.15 + phase))
            canvas.px_set(wx, wy)
