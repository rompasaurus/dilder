"""Underwater environment — seaweed, bubbles, coral, fish, seafloor."""

import math
from ..core import canvas
from ..core.drawing import draw_hline
from . import register


@register(
    "underwater",
    ground_y=110,
    has_weather=False,
    description="Underwater with seaweed, ascending bubbles, coral, fish silhouettes, seafloor",
    decor_slots=[(5, 100), (55, 100)],
)
def draw_underwater(frame_idx=0):
    # Seafloor (bumpy bottom)
    for x in range(0, 70):
        bump = int(2 * math.sin(x * 0.3) + math.sin(x * 0.7))
        base_y = 110 + bump
        for y in range(base_y, 122):
            canvas.px_set(x, y)

    # Seaweed (wavy vertical strands)
    seaweed_positions = [5, 18, 35, 50, 63]
    for sx in seaweed_positions:
        base = 110 + int(2 * math.sin(sx * 0.3))
        height = 15 + (sx * 3) % 8
        for i in range(height):
            t = i / max(height - 1, 1)
            wobble = int(2 * math.sin(t * math.pi * 2 + frame_idx * 0.7 + sx))
            y = base - i
            canvas.px_set(sx + wobble, y)
            canvas.px_set(sx + wobble + 1, y)
        # Leaf pairs
        for leaf_y in range(base - 4, base - height, -5):
            lw = int(1.5 * math.sin((base - leaf_y) * 0.3 + frame_idx * 0.5 + sx))
            canvas.px_set(sx + lw + 2, leaf_y)
            canvas.px_set(sx + lw - 2, leaf_y)

    # Coral clusters (small bumpy shapes on seafloor)
    for cx, cy in [(12, 108), (42, 109), (58, 107)]:
        for dy in range(4):
            for dx in range(-3, 4):
                if abs(dx) + dy < 5 and ((dx + dy) % 2 == 0):
                    canvas.px_set(cx + dx, cy + dy)

    # Bubbles (ascending circles, animated)
    bubble_cols = [10, 28, 45, 60]
    for i, bx in enumerate(bubble_cols):
        phase = (frame_idx * 0.8 + i * 2.5) % 8
        by = int(100 - phase * 12)
        drift = int(2 * math.sin(phase * 1.5 + i))
        if 0 < by < 120:
            # Small bubble (circle outline)
            r = 2 if i % 2 == 0 else 1
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    dist = dx * dx + dy * dy
                    if r * r - r <= dist <= r * r:
                        canvas.px_set(bx + drift + dx, by + dy)

    # Fish silhouettes (simple shapes)
    for fx, fy, d in [(25, 30, 1), (55, 50, -1)]:
        anim_x = fx + int(3 * math.sin(frame_idx * 0.6 + fx))
        # Body (oval)
        for dy in range(-2, 3):
            for dx in range(-4, 5):
                if dx * dx * 4 + dy * dy * 16 <= 64:
                    canvas.px_set(anim_x + dx, fy + dy)
        # Tail
        for i in range(3):
            canvas.px_set(anim_x + d * (5 + i), fy - i)
            canvas.px_set(anim_x + d * (5 + i), fy + i)
        # Eye (white dot)
        canvas.px_clr(anim_x - d * 2, fy - 1)
