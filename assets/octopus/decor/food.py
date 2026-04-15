"""Food props — pizza, sushi, donut, coffee, ramen, apple."""

import math
from ..core import canvas
from ..core.drawing import draw_rect, draw_line, draw_hline
from . import register


@register("pizza", "food", 10, 10, "Triangle with circle toppings")
def draw_pizza(x, y):
    # Triangle slice
    for row in range(10):
        half_w = row // 2
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(x + 5 + dx, y + row)
    # Outline edges
    draw_line(x + 5, y, x, y + 9)
    draw_line(x + 5, y, x + 10, y + 9)
    draw_hline(x, x + 10, y + 9)
    # Toppings (dots)
    canvas.px_set(x + 5, y + 3)
    canvas.px_set(x + 3, y + 6)
    canvas.px_set(x + 7, y + 7)


@register("sushi", "food", 8, 6, "Rectangle with rice dots and nori wrap")
def draw_sushi(x, y):
    draw_rect(x, y, 8, 6)
    # Nori wrap (dark band)
    for dy in range(6):
        canvas.px_set(x + 3, y + dy)
        canvas.px_set(x + 4, y + dy)
    # Rice dots
    canvas.px_set(x + 1, y + 2)
    canvas.px_set(x + 6, y + 3)


@register("donut", "food", 8, 8, "Circle with center hole, sprinkle dots")
def draw_donut(x, y):
    cx, cy = x + 4, y + 4
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            dist = dx * dx + dy * dy
            # Ring: outer r=3, inner r=1
            if 2 <= dist <= 9:
                canvas.px_set(cx + dx, cy + dy)
    # Sprinkles
    canvas.px_set(cx - 2, cy - 2)
    canvas.px_set(cx + 2, cy - 1)
    canvas.px_set(cx + 1, cy + 2)


@register("coffee", "food", 8, 10, "Rectangle mug with handle arc and steam")
def draw_coffee(x, y):
    # Mug body
    draw_rect(x, y + 3, 6, 7)
    # Handle
    canvas.px_set(x + 6, y + 4)
    canvas.px_set(x + 7, y + 5)
    canvas.px_set(x + 7, y + 6)
    canvas.px_set(x + 7, y + 7)
    canvas.px_set(x + 6, y + 8)
    # Steam curves
    for i in range(4):
        sx = x + 2 + int(math.sin(i * 1.2) * 1.5)
        canvas.px_set(sx, y + 2 - i)


@register("ramen", "food", 12, 10, "Bowl arc with noodle squiggles and chopsticks")
def draw_ramen(x, y):
    # Bowl (half circle)
    cx, cy = x + 6, y + 4
    for dy in range(0, 6):
        half_w = int(math.sqrt(max(0, 36 - (dy - 1) * (dy - 1) * 1.5)))
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(cx + dx, cy + dy)
    # Clear interior
    for dy in range(1, 5):
        half_w = int(math.sqrt(max(0, 25 - (dy) * (dy) * 1.5)))
        for dx in range(-half_w + 1, half_w):
            canvas.px_clr(cx + dx, cy + dy)
    # Rim
    draw_hline(x + 1, x + 11, y + 4)
    # Noodle squiggles inside
    for nx in range(x + 3, x + 10, 2):
        canvas.px_set(nx, y + 5)
        canvas.px_set(nx + 1, y + 6)
    # Chopsticks
    draw_line(x + 8, y, x + 10, y + 4)
    draw_line(x + 9, y, x + 11, y + 4)


@register("apple", "food", 6, 7, "Circle with stem and leaf")
def draw_apple(x, y):
    cx, cy = x + 3, y + 4
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 5:
                canvas.px_set(cx + dx, cy + dy)
    # Stem
    canvas.px_set(cx, y + 1)
    canvas.px_set(cx, y)
    # Leaf
    canvas.px_set(cx + 1, y)
    canvas.px_set(cx + 2, y + 1)
