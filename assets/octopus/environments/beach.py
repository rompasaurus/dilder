"""Beach environment — waves, sand, umbrella, sun, shells."""

import math
from ..core import canvas
from ..core.drawing import draw_hline, draw_line
from . import register


@register(
    "beach",
    ground_y=100,
    has_weather=True,
    description="Beach with sine waves, sand dither, umbrella, sun, seashells",
    decor_slots=[(5, 90), (55, 95)],
)
def draw_beach(frame_idx=0):
    # Sand (sparse dither pattern below ground)
    for y in range(100, 122):
        for x in range(0, 70):
            if ((x * 7 + y * 13) % 11) < 2:
                canvas.px_set(x, y)

    # Wave lines (3 rows of sine waves)
    for wave_i, (base_y, amp, freq) in enumerate([
        (92, 2, 0.15), (96, 1.5, 0.12), (100, 1, 0.18)
    ]):
        phase = frame_idx * 0.5 + wave_i * 1.2
        for x in range(0, 70):
            y = int(base_y + amp * math.sin(x * freq + phase))
            canvas.px_set(x, y)
            if wave_i == 2:  # thicker for shoreline
                canvas.px_set(x, y + 1)

    # Umbrella (triangle + pole)
    pole_x, pole_y = 55, 75
    # Pole
    for y in range(pole_y, 100):
        canvas.px_set(pole_x, y)
    # Canopy triangle
    for row in range(12):
        half_w = row + 1
        y = pole_y - 12 + row
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(pole_x + dx, y)
    # Clear interior for pattern
    for row in range(1, 11):
        half_w = row
        y = pole_y - 11 + row
        for dx in range(-half_w + 1, half_w):
            canvas.px_clr(pole_x + dx, y)
    # Stripe pattern on umbrella
    for row in range(0, 12, 3):
        half_w = row + 1
        y = pole_y - 12 + row
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(pole_x + dx, y)

    # Sun (upper right of character area)
    sun_cx, sun_cy = 8, 8
    r = 5
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                canvas.px_set(sun_cx + dx, sun_cy + dy)
    # Rays
    for angle in range(0, 360, 45):
        rx = sun_cx + int(8 * math.cos(math.radians(angle)))
        ry = sun_cy + int(8 * math.sin(math.radians(angle)))
        draw_line(sun_cx + int(6 * math.cos(math.radians(angle))),
                  sun_cy + int(6 * math.sin(math.radians(angle))),
                  rx, ry)

    # Seashell (small spiral near sand)
    sx, sy = 20, 105
    canvas.px_set(sx, sy)
    canvas.px_set(sx + 1, sy)
    canvas.px_set(sx + 1, sy - 1)
    canvas.px_set(sx, sy - 1)
    canvas.px_set(sx - 1, sy)

    # Starfish
    stx, sty = 40, 108
    canvas.px_set(stx, sty)
    canvas.px_set(stx - 2, sty - 1)
    canvas.px_set(stx + 2, sty - 1)
    canvas.px_set(stx - 1, sty + 2)
    canvas.px_set(stx + 1, sty + 2)
