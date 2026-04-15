"""City street environment — buildings, lamp posts, crosswalk, urban details.

Dark building rectangles with lit window dots, lamp posts with dithered
glow circles, crosswalk stripes, traffic light, fire hydrant, and a
parked car silhouette for idle mode's full street scene.
"""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    fill_dithered_poly, _dither_check, draw_curved_surface,
)
from . import register


def _draw_building(bx, by, bw, bh, window_spacing_x=6, window_spacing_y=7):
    """Building with lit windows (white dots in dark rect)."""
    # Dark building body
    fill_dithered_rect(bx, by, bw, bh, 0.55)
    # Outline
    draw_rect(bx, by, bw, bh)
    # Lit windows — clear pixels inside the dark fill
    for wy in range(by + 4, by + bh - 3, window_spacing_y):
        for wx in range(bx + 3, bx + bw - 3, window_spacing_x):
            # Small 2x2 window
            canvas.px_clr(wx, wy)
            canvas.px_clr(wx + 1, wy)
            canvas.px_clr(wx, wy + 1)
            canvas.px_clr(wx + 1, wy + 1)
            # Window frame
            canvas.px_set(wx - 1, wy - 1)
            canvas.px_set(wx + 2, wy - 1)
            canvas.px_set(wx - 1, wy + 2)
            canvas.px_set(wx + 2, wy + 2)


def _draw_lamp_post(lx, ground_y, glow=True):
    """Lamp post with optional dithered glow halo."""
    # Pole
    draw_vline(lx, ground_y - 30, ground_y)
    # Arm
    draw_hline(lx, lx + 5, ground_y - 30)
    # Lamp housing
    draw_rect(lx + 3, ground_y - 33, 5, 4, filled=True)
    # Glow circle (light dither around lamp)
    if glow:
        fill_dithered_circle(lx + 5, ground_y - 28, 8, 0.08)
    # Base
    draw_hline(lx - 2, lx + 2, ground_y)
    draw_hline(lx - 1, lx + 1, ground_y + 1)


def _draw_crosswalk(x_start, ground_y, stripe_count, stripe_w, gap):
    """Horizontal crosswalk stripes on the road."""
    for i in range(stripe_count):
        sx = x_start + i * (stripe_w + gap)
        for dy in range(3):
            draw_hline(sx, sx + stripe_w - 1, ground_y + 4 + dy)


def _draw_traffic_light(tx, ground_y):
    """Traffic light on a pole."""
    # Pole
    draw_vline(tx, ground_y - 28, ground_y)
    # Housing
    draw_rect(tx - 3, ground_y - 40, 7, 14)
    # Three lights (circles as filled dots)
    for i, ly in enumerate([ground_y - 37, ground_y - 33, ground_y - 29]):
        # Outline circle
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if abs(dx) + abs(dy) <= 1:
                    canvas.px_set(tx + dx, ly + dy)
        # Only top light is "lit" (filled)
        if i == 0:
            canvas.px_set(tx, ly)


def _draw_car(cx, ground_y):
    """Simple parked car silhouette."""
    # Body
    fill_dithered_rect(cx, ground_y - 8, 28, 8, 0.45)
    draw_rect(cx, ground_y - 8, 28, 8)
    # Roof / cabin
    fill_dithered_poly(
        [(cx + 5, ground_y - 8), (cx + 10, ground_y - 14),
         (cx + 22, ground_y - 14), (cx + 25, ground_y - 8)],
        0.40,
    )
    draw_line(cx + 5, ground_y - 8, cx + 10, ground_y - 14)
    draw_line(cx + 10, ground_y - 14, cx + 22, ground_y - 14)
    draw_line(cx + 22, ground_y - 14, cx + 25, ground_y - 8)
    # Windows (clear inside cabin)
    canvas.px_clr(cx + 12, ground_y - 12)
    canvas.px_clr(cx + 13, ground_y - 12)
    canvas.px_clr(cx + 18, ground_y - 12)
    canvas.px_clr(cx + 19, ground_y - 12)
    # Wheels
    fill_dithered_circle(cx + 5, ground_y, 3, 0.7)
    fill_dithered_circle(cx + 23, ground_y, 3, 0.7)
    # Headlight
    canvas.px_clr(cx + 27, ground_y - 5)


def _draw_fire_hydrant(hx, ground_y):
    """Small fire hydrant."""
    draw_rect(hx - 2, ground_y - 8, 5, 8, filled=True)
    # Cap
    draw_hline(hx - 3, hx + 3, ground_y - 8)
    draw_hline(hx - 3, hx + 3, ground_y - 9)
    # Nozzles
    canvas.px_set(hx - 3, ground_y - 5)
    canvas.px_set(hx + 3, ground_y - 5)
    # Top knob
    canvas.px_set(hx, ground_y - 10)


def _draw_city_street_full(frame_idx):
    """Full-canvas city street scene (idle mode)."""
    W, H = canvas.IMG_W, canvas.IMG_H
    ground_y = 95

    # Night sky — dark gradient
    gradient_vfill(0, 0, W, 40, 0.35, 0.15)

    # Background buildings (perspective, varying heights)
    _draw_building(0, 20, 30, 75)
    _draw_building(32, 30, 25, 65)
    _draw_building(59, 15, 28, 80, window_spacing_x=5, window_spacing_y=6)
    _draw_building(89, 25, 22, 70)
    _draw_building(113, 35, 26, 60)
    _draw_building(141, 10, 30, 85, window_spacing_x=7, window_spacing_y=8)
    _draw_building(173, 28, 24, 67)
    _draw_building(199, 18, 28, 77)
    _draw_building(229, 32, 21, 63)

    # Sidewalk / road
    draw_thick_line(0, ground_y, W - 1, ground_y, 2)
    # Road surface — light dither
    fill_dithered_rect(0, ground_y + 2, W, H - ground_y - 2, 0.08)
    # Curb line
    draw_hline(0, W - 1, ground_y + 2)

    # Crosswalk
    _draw_crosswalk(85, ground_y, 6, 4, 3)

    # Lamp posts
    _draw_lamp_post(45, ground_y)
    _draw_lamp_post(140, ground_y)
    _draw_lamp_post(220, ground_y)

    # Traffic light
    _draw_traffic_light(105, ground_y)

    # Parked car
    _draw_car(155, ground_y + 8)

    # Fire hydrant
    _draw_fire_hydrant(75, ground_y)


def _draw_city_street_speaking(frame_idx):
    """Left-zone city street for speaking mode."""
    ground_y = 95

    # Night sky
    gradient_vfill(0, 0, 72, 30, 0.30, 0.12)

    # Building facade (left portion)
    _draw_building(0, 20, 30, 75)
    _draw_building(32, 30, 20, 65)

    # Sidewalk
    draw_hline(0, 71, ground_y)
    fill_dithered_rect(0, ground_y + 1, 72, 26, 0.06)

    # Lamp post
    _draw_lamp_post(55, ground_y)

    # Crosswalk stripes
    _draw_crosswalk(10, ground_y, 3, 4, 3)


@register(
    "city_street",
    ground_y=95,
    has_weather=False,
    description="City street with lit buildings, lamp posts, crosswalk, car, fire hydrant",
    decor_slots=[(5, 105), (55, 103)],
)
def draw_city_street(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_city_street_full(frame_idx)
    else:
        _draw_city_street_speaking(frame_idx)
