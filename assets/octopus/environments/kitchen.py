"""Kitchen environment — counter, cabinets, checkered floor, pot rack."""

import math
from ..core import canvas
from ..core.drawing import draw_rect, draw_line, draw_hline, draw_vline
from . import register


@register(
    "kitchen",
    ground_y=100,
    has_weather=False,
    description="Kitchen with counter, cabinets, checkered tile floor, pot rack",
    decor_slots=[(5, 85), (50, 90)],
)
def draw_kitchen(frame_idx=0):
    # Checkered tile floor (2px squares, sparse)
    for ty in range(100, 122, 4):
        for tx in range(0, 70, 4):
            if ((tx // 4) + (ty // 4)) % 2 == 0:
                for dy in range(2):
                    for dx in range(2):
                        canvas.px_set(tx + dx, ty + dy)

    # Counter line
    draw_hline(0, 68, 80)
    draw_hline(0, 68, 81)

    # Cabinet outlines (above counter)
    draw_rect(2, 60, 15, 19)
    draw_rect(20, 60, 15, 19)
    # Cabinet knobs
    canvas.px_set(9, 70)
    canvas.px_set(27, 70)

    # Pot rack (horizontal bar with hanging shapes)
    draw_hline(42, 65, 62)
    # Hanging pots (simple arcs)
    for px in [46, 54, 62]:
        draw_vline(px, 62, 66)
        # Pot body (small rect)
        draw_rect(px - 2, 66, 5, 4)

    # Hanging utensils
    for ux in [3, 8]:
        draw_vline(ux, 48, 58)
        canvas.px_set(ux - 1, 58)
        canvas.px_set(ux + 1, 58)

    # Steam wisps above counter
    for i in range(3):
        x = 10 + i * 18
        for dy in range(4):
            sx = x + int(1.5 * math.sin(dy * 1.2 + frame_idx * 0.8))
            canvas.px_set(sx, 75 - dy)
