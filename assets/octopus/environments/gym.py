"""Gym environment — dumbbell rack, punching bag, pull-up bar, mirror wall."""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    _dither_check, draw_curved_surface, draw_shadow,
)
from . import register


def _draw_gym_full(frame_idx):
    W, H = canvas.IMG_W, canvas.IMG_H
    floor_y = 80

    # Back wall (mirror — lighter area with reflection hint)
    gradient_vfill(0, 0, W, floor_y, 0.03, 0.07)

    # Mirror panel (large rectangle with slight reflection)
    mx, my, mw, mh = 80, 5, 120, 65
    draw_rect(mx, my, mw, mh)
    draw_rect(mx + 1, my + 1, mw - 2, mh - 2)
    # Reflection glare line (diagonal)
    for i in range(30):
        gx = mx + 10 + i
        gy = my + 5 + i // 2
        if gx < mx + mw - 2 and gy < my + mh - 2:
            canvas.px_clr(gx, gy)

    # Rubber mat floor
    for y in range(floor_y, H):
        depth = (y - floor_y) / max(H - floor_y - 1, 1)
        for x in range(W):
            # Mat texture: subtle grid
            if (x % 8 == 0 or y % 6 == 0):
                canvas.px_set(x, y)
            elif _dither_check(x, y, 0.04 + depth * 0.06):
                canvas.px_set(x, y)

    draw_thick_line(0, floor_y, W - 1, floor_y, 2)

    # Dumbbell rack (left wall)
    rack_x, rack_y = 10, 40
    draw_rect(rack_x, rack_y, 40, 35)
    # Shelf lines
    for sy in [rack_y + 11, rack_y + 22]:
        draw_hline(rack_x, rack_x + 40, sy)
    # Dumbbells on shelves (circles + bar)
    for shelf_y in [rack_y + 4, rack_y + 15, rack_y + 26]:
        for dx in [8, 22, 36]:
            bx = rack_x + dx
            # Dumbbell shape
            fill_dithered_circle(bx - 3, shelf_y, 2, 0.4)
            draw_hline(bx - 2, bx + 2, shelf_y)
            fill_dithered_circle(bx + 3, shelf_y, 2, 0.4)

    # Punching bag (center, hanging)
    bag_x = 140
    # Chain
    draw_vline(bag_x, 0, 20)
    # Bag body (elongated oval with shading)
    for dy in range(-18, 19):
        half_w = int(8 * math.sqrt(max(0, 1 - (dy / 18.0) ** 2)))
        for dx in range(-half_w, half_w + 1):
            dist = (dx / max(half_w, 1)) ** 2
            shade = 0.2 + 0.15 * dist
            if _dither_check(bag_x + dx, 38 + dy, shade):
                canvas.px_set(bag_x + dx, 38 + dy)
    # Shadow
    fill_dithered_rect(bag_x - 6, floor_y + 2, 14, 4, 0.1)

    # Pull-up bar (right side, high)
    bar_y = 15
    draw_thick_line(200, bar_y, 240, bar_y, 3)
    # Support brackets
    draw_vline(200, bar_y, bar_y + 8)
    draw_vline(240, bar_y, bar_y + 8)
    draw_hline(198, 202, bar_y + 8)
    draw_hline(238, 242, bar_y + 8)

    # Weight plates on floor (stacked circles)
    for px, count in [(210, 3), (225, 2)]:
        for i in range(count):
            py = floor_y - 2 - i * 4
            fill_dithered_circle(px, py, 5, 0.3 + i * 0.05)
            # Hole
            canvas.px_clr(px, py)

    # Exercise ball (right)
    draw_curved_surface(60, floor_y - 10, 10, 10,
                        density_center=0.08, density_edge=0.25)
    fill_dithered_rect(52, floor_y + 1, 18, 3, 0.1)  # shadow

    # Water bottle
    draw_rect(235, floor_y - 12, 5, 12)
    canvas.px_set(237, floor_y - 14)  # cap
    canvas.px_set(237, floor_y - 13)

    # Towel draped on bar
    for i in range(8):
        canvas.px_set(215 + i, bar_y + 2 + i // 2)
        canvas.px_set(215 + i, bar_y + 3 + i // 2)


def _draw_gym_speaking(frame_idx):
    gradient_vfill(0, 0, 72, 78, 0.03, 0.06)

    # Floor
    for y in range(78, canvas.IMG_H):
        for x in range(72):
            if x % 8 == 0 or y % 6 == 0:
                canvas.px_set(x, y)
            elif _dither_check(x, y, 0.04):
                canvas.px_set(x, y)
    draw_hline(0, 71, 78)

    # Dumbbell rack (partial)
    draw_rect(2, 45, 25, 30)
    for sy in [55, 65]:
        draw_hline(2, 27, sy)
    for shelf_y in [50, 60, 70]:
        for dx in [8, 20]:
            fill_dithered_circle(dx - 2, shelf_y, 2, 0.4)
            draw_hline(dx - 1, dx + 1, shelf_y)
            fill_dithered_circle(dx + 2, shelf_y, 2, 0.4)

    # Punching bag hint
    draw_vline(55, 0, 20)
    for dy in range(-12, 13):
        hw = int(5 * math.sqrt(max(0, 1 - (dy / 12.0) ** 2)))
        for dx in range(-hw, hw + 1):
            if _dither_check(55 + dx, 32 + dy, 0.25):
                canvas.px_set(55 + dx, 32 + dy)


@register(
    "gym",
    ground_y=80,
    has_weather=False,
    description="Gym with dumbbell rack, punching bag, pull-up bar, mirror wall, exercise ball",
    decor_slots=[(5, 90), (55, 92)],
)
def draw_gym(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_gym_full(frame_idx)
    else:
        _draw_gym_speaking(frame_idx)
