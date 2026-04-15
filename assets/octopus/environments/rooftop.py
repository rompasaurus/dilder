"""Rooftop environment — city skyline, water tower, stars, railing, antenna."""

from ..core import canvas
from ..core.drawing import draw_rect, draw_hline, draw_vline, draw_line
from . import register


@register(
    "rooftop",
    ground_y=100,
    has_weather=True,
    description="Rooftop with city skyline silhouettes, water tower, stars, railing",
    decor_slots=[(5, 90), (55, 92)],
)
def draw_rooftop(frame_idx=0):
    # Roof line (thick)
    draw_hline(0, 70, 100)
    draw_hline(0, 70, 101)
    draw_hline(0, 70, 102)

    # City skyline (background, behind character)
    buildings = [
        (0, 60, 8, 40),    # tall thin
        (9, 70, 10, 30),   # medium
        (20, 55, 7, 45),   # tallest
        (28, 72, 9, 28),   # medium
        (38, 65, 6, 35),   # tall
        (45, 75, 10, 25),  # short wide
        (56, 68, 7, 32),   # tall
        (64, 73, 6, 27),   # medium
    ]
    for bx, by, bw, bh in buildings:
        # Just outlines so they don't obscure the character
        draw_rect(bx, by, bw, bh)
        # Window dots
        for wy in range(by + 3, by + bh - 2, 5):
            for wx in range(bx + 2, bx + bw - 1, 3):
                canvas.px_set(wx, wy)

    # Water tower (distinctive silhouette)
    wt_x = 60
    # Tank (barrel shape)
    draw_rect(wt_x, 50, 10, 10)
    # Legs
    draw_line(wt_x + 1, 60, wt_x - 1, 72)
    draw_line(wt_x + 9, 60, wt_x + 11, 72)
    # Cone roof
    for i in range(4):
        half = 5 - i
        draw_hline(wt_x + 5 - half, wt_x + 5 + half, 49 - i)
    canvas.px_set(wt_x + 5, 44)

    # Railing posts
    for rx in range(3, 70, 8):
        draw_vline(rx, 95, 100)
    # Top rail
    draw_hline(3, 67, 95)
    draw_hline(3, 67, 96)

    # Stars
    star_positions = [
        (5, 5), (15, 3), (28, 8), (42, 4), (55, 7), (68, 3),
        (10, 15), (35, 12), (50, 10), (62, 14),
    ]
    for sx, sy in star_positions:
        canvas.px_set(sx, sy)
        # Twinkle: some stars get cross shape on certain frames
        if (sx + sy + frame_idx) % 4 == 0:
            canvas.px_set(sx + 1, sy)
            canvas.px_set(sx - 1, sy)
            canvas.px_set(sx, sy + 1)
            canvas.px_set(sx, sy - 1)

    # Antenna on one building
    draw_vline(23, 40, 55)
    canvas.px_set(22, 42)
    canvas.px_set(24, 42)
    canvas.px_set(21, 44)
    canvas.px_set(25, 44)
