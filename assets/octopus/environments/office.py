"""Office environment — desk, monitor, chair, paper stack, coffee mug."""

from ..core import canvas
from ..core.drawing import draw_rect, draw_hline, draw_vline, draw_line
from . import register


@register(
    "office",
    ground_y=100,
    has_weather=False,
    description="Office with desk, monitor, spinning chair, paper stack, coffee mug",
    decor_slots=[(5, 88), (55, 92)],
)
def draw_office(frame_idx=0):
    # Floor
    draw_hline(0, 70, 100)
    draw_hline(0, 70, 101)

    # Desk (large, right side)
    draw_hline(30, 68, 82)
    draw_hline(30, 68, 83)
    draw_vline(32, 83, 100)
    draw_vline(66, 83, 100)
    # Drawer
    draw_rect(45, 84, 18, 10)
    draw_hline(46, 62, 89)
    canvas.px_set(54, 87)  # knob

    # Monitor on desk
    draw_rect(40, 60, 22, 16)
    # Screen (inner)
    draw_rect(42, 62, 18, 12)
    # Stand
    draw_vline(51, 76, 82)
    draw_hline(47, 55, 82)
    # Screen content (simple lines to suggest text)
    for ty in [64, 67, 70]:
        draw_hline(44, 56, ty)

    # Office chair (left side)
    # Seat
    draw_hline(5, 20, 90)
    draw_hline(5, 20, 91)
    # Back rest
    draw_rect(7, 78, 12, 12)
    # Wheel base
    draw_vline(12, 92, 98)
    # Wheels
    canvas.px_set(8, 99)
    canvas.px_set(9, 100)
    canvas.px_set(15, 99)
    canvas.px_set(16, 100)

    # Paper stack on desk
    for i in range(3):
        draw_rect(34, 77 - i * 2, 8, 5)

    # Coffee mug on desk
    mx, my = 60, 76
    draw_rect(mx, my, 5, 6)
    # Handle
    canvas.px_set(mx + 5, my + 1)
    canvas.px_set(mx + 6, my + 2)
    canvas.px_set(mx + 6, my + 3)
    canvas.px_set(mx + 5, my + 4)

    # Pen
    draw_line(36, 80, 42, 75)

    # Sticky notes on wall
    for nx, ny, w in [(4, 55, 8), (14, 58, 7)]:
        draw_rect(nx, ny, w, 6)
