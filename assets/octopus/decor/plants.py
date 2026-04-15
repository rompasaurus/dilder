"""Plant props — potted plant, cactus, flower, vine, mushroom."""

import math
from ..core import canvas
from ..core.drawing import draw_rect, draw_vline, draw_hline
from . import register


@register("potted_plant", "plants", 10, 15, "Trapezoid pot with stem and leaf cluster")
def draw_potted_plant(x, y):
    # Pot (trapezoid)
    for row in range(6):
        half_w = 3 + row // 2
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(x + 5 + dx, y + 9 + row)
    # Rim
    draw_hline(x + 1, x + 9, y + 9)
    # Stem
    draw_vline(x + 5, y + 3, y + 9)
    # Leaves (3 small circles)
    for lx, ly in [(x + 5, y + 2), (x + 3, y + 3), (x + 7, y + 3)]:
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if abs(dx) + abs(dy) <= 1:
                    canvas.px_set(lx + dx, ly + dy)


@register("cactus", "plants", 8, 14, "Vertical oval with arm bumps and dot spines")
def draw_cactus(x, y):
    # Main body (vertical oval)
    cx, cy = x + 4, y + 7
    for dy in range(-5, 6):
        for dx in range(-2, 3):
            if dx * dx * 25 + dy * dy * 4 <= 100:
                canvas.px_set(cx + dx, cy + dy)
    # Left arm
    for i in range(4):
        canvas.px_set(cx - 3, cy - 2 + i)
    canvas.px_set(cx - 4, cy - 2)
    canvas.px_set(cx - 4, cy - 1)
    # Right arm
    for i in range(4):
        canvas.px_set(cx + 3, cy + i)
    canvas.px_set(cx + 4, cy)
    canvas.px_set(cx + 4, cy + 1)
    # Spines (dots)
    for sx, sy in [(cx - 1, cy - 3), (cx + 1, cy - 1), (cx - 1, cy + 2),
                   (cx + 1, cy + 4), (cx, cy + 1)]:
        canvas.px_clr(sx, sy)
    # Pot
    draw_rect(x + 1, y + 12, 6, 2)


@register("flower", "plants", 6, 10, "Stem with 5-petal circle cluster on top")
def draw_flower(x, y):
    cx, cy = x + 3, y + 2
    # Stem
    draw_vline(cx, y + 4, y + 10)
    # 5 petals (circle pattern)
    for angle in range(0, 360, 72):
        px = cx + int(2 * math.cos(math.radians(angle)))
        py = cy + int(2 * math.sin(math.radians(angle)))
        canvas.px_set(px, py)
        canvas.px_set(px + 1, py)
        canvas.px_set(px, py + 1)
    # Center
    canvas.px_set(cx, cy)
    # Leaves
    canvas.px_set(cx - 1, y + 6)
    canvas.px_set(cx - 2, y + 7)
    canvas.px_set(cx + 1, y + 7)
    canvas.px_set(cx + 2, y + 8)


@register("vine", "plants", 4, 20, "Wavy vertical line with leaf pairs")
def draw_vine(x, y):
    for i in range(20):
        wobble = int(1.5 * math.sin(i * 0.6))
        canvas.px_set(x + 2 + wobble, y + i)
        # Leaf pairs every 4px
        if i % 4 == 0 and i > 0:
            canvas.px_set(x + 2 + wobble - 2, y + i)
            canvas.px_set(x + 2 + wobble + 2, y + i - 1)


@register("mushroom", "plants", 8, 8, "Dome cap with stem and dot pattern on cap")
def draw_mushroom(x, y):
    cx = x + 4
    # Cap dome
    for dy in range(-3, 1):
        half_w = int(math.sqrt(max(0, 16 - dy * dy)))
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(cx + dx, y + 3 + dy)
    # Dots on cap
    canvas.px_clr(cx - 1, y + 1)
    canvas.px_clr(cx + 2, y + 2)
    # Stem
    draw_vline(cx - 1, y + 4, y + 8)
    draw_vline(cx, y + 4, y + 8)
    draw_vline(cx + 1, y + 4, y + 8)
