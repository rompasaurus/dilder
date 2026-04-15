"""Electronics props — TV, lamp, phone, gamepad, headphones, laptop."""

import math
from ..core import canvas
from ..core.drawing import draw_rect, draw_hline, draw_vline, draw_line, draw_arc
from . import register


@register("tv", "electronics", 25, 18, "Rectangle with screen and stand")
def draw_tv(x, y):
    # Outer frame
    draw_rect(x, y, 25, 15)
    # Screen (inner)
    draw_rect(x + 2, y + 2, 21, 11)
    # Stand
    draw_vline(x + 12, y + 15, y + 17)
    draw_hline(x + 8, x + 16, y + 17)


@register("lamp", "electronics", 8, 20, "Trapezoid shade on stem with base")
def draw_lamp(x, y):
    cx = x + 4
    # Shade (trapezoid)
    for row in range(6):
        half_w = 1 + row
        for dx in range(-half_w, half_w + 1):
            if row == 0 or row == 5 or abs(dx) == half_w:
                canvas.px_set(cx + dx, y + row)
    # Stem
    draw_vline(cx, y + 6, y + 16)
    # Base (circle)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 5:
                canvas.px_set(cx + dx, y + 18 + dy)


@register("phone", "electronics", 6, 10, "Rounded rectangle with screen and button")
def draw_phone(x, y):
    draw_rect(x, y, 6, 10)
    # Rounded corners (clear)
    canvas.px_clr(x, y)
    canvas.px_clr(x + 5, y)
    canvas.px_clr(x, y + 9)
    canvas.px_clr(x + 5, y + 9)
    # Screen
    draw_rect(x + 1, y + 1, 4, 6)
    # Home button
    canvas.px_set(x + 3, y + 8)


@register("gamepad", "electronics", 12, 8, "Rounded rect with d-pad and buttons")
def draw_gamepad(x, y):
    draw_rect(x + 1, y + 1, 10, 6)
    # Rounded-ish edges
    canvas.px_set(x, y + 2)
    canvas.px_set(x, y + 5)
    canvas.px_set(x + 11, y + 2)
    canvas.px_set(x + 11, y + 5)
    # D-pad (left side)
    canvas.px_set(x + 3, y + 3)  # center
    canvas.px_set(x + 2, y + 3)  # left
    canvas.px_set(x + 4, y + 3)  # right
    canvas.px_set(x + 3, y + 2)  # up
    canvas.px_set(x + 3, y + 4)  # down
    # Buttons (right side)
    canvas.px_set(x + 8, y + 3)
    canvas.px_set(x + 10, y + 3)
    canvas.px_set(x + 9, y + 2)
    canvas.px_set(x + 9, y + 4)


@register("headphones", "electronics", 12, 10, "Arc with two circle ear cups")
def draw_headphones(x, y):
    cx = x + 6
    # Headband arc
    for i in range(10):
        t = i / 9.0
        angle = math.pi * (0.1 + t * 0.8)
        ax = cx + int(5 * math.cos(angle))
        ay = y + 2 - int(3 * math.sin(angle))
        canvas.px_set(ax, ay)
    # Left ear cup
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                canvas.px_set(x + 1 + dx, y + 5 + dy)
    # Right ear cup
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                canvas.px_set(x + 11 + dx, y + 5 + dy)


@register("laptop", "electronics", 16, 12, "Two rectangles at angle, screen + base")
def draw_laptop(x, y):
    # Screen (angled back slightly)
    draw_rect(x + 1, y, 14, 8)
    # Screen content
    draw_rect(x + 2, y + 1, 12, 6)
    # Base / keyboard
    draw_rect(x, y + 8, 16, 4)
    # Keyboard dots
    for ky in [y + 9, y + 10]:
        for kx in range(x + 2, x + 14, 2):
            canvas.px_set(kx, ky)
    # Trackpad
    draw_rect(x + 6, y + 11, 4, 1)
