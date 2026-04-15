"""Space environment — star field, planet arc, satellite."""

import math
from ..core import canvas
from ..core.drawing import draw_arc, draw_line
from . import register

# Deterministic star positions (seeded, not random)
_STARS = [
    (3, 8), (12, 3), (25, 15), (40, 5), (55, 10), (8, 30),
    (20, 45), (50, 35), (62, 8), (15, 55), (45, 50), (58, 45),
    (30, 60), (5, 70), (65, 65), (10, 95), (35, 90), (55, 80),
    (22, 75), (48, 95), (60, 100), (3, 110), (28, 105), (42, 115),
    (68, 112), (15, 118), (50, 108),
]


@register(
    "space",
    ground_y=-1,  # no ground (floating)
    has_weather=False,
    description="Deep space with star field, planet arc, satellite",
    decor_slots=[(5, 50), (60, 80)],
)
def draw_space(frame_idx=0):
    # Star field
    for sx, sy in _STARS:
        canvas.px_set(sx, sy)
        # A few brighter stars (2px)
        if (sx + sy) % 7 == 0:
            canvas.px_set(sx + 1, sy)

    # Planet arc (bottom-left corner, partially visible)
    cx, cy, r = -10, 130, 40
    for deg in range(0, 360):
        x = cx + int(r * math.cos(math.radians(deg)))
        y = cy + int(r * math.sin(math.radians(deg)))
        if 0 <= x < 70 and 0 <= y < canvas.IMG_H:
            canvas.px_set(x, y)

    # Planet ring (slightly larger arc)
    ring_r = 48
    for deg in range(200, 340):
        x = cx + int(ring_r * math.cos(math.radians(deg)))
        y = cy + int(ring_r * 0.3 * math.sin(math.radians(deg)))
        if 0 <= x < 70 and 0 <= y < canvas.IMG_H:
            canvas.px_set(x, y)

    # Small satellite (upper area)
    sat_x, sat_y = 55, 15
    # Body
    canvas.px_set(sat_x, sat_y)
    canvas.px_set(sat_x + 1, sat_y)
    canvas.px_set(sat_x, sat_y + 1)
    canvas.px_set(sat_x + 1, sat_y + 1)
    # Solar panels (horizontal lines)
    for dx in range(-3, 0):
        canvas.px_set(sat_x + dx, sat_y)
    for dx in range(2, 5):
        canvas.px_set(sat_x + dx, sat_y + 1)
