"""Living room environment — couch, TV, coffee table, rug."""

from ..core import canvas
from ..core.drawing import draw_rect, draw_hline, draw_vline, draw_line
from . import register


@register(
    "living_room",
    ground_y=100,
    has_weather=False,
    description="Living room with couch, TV, coffee table, rug pattern",
    decor_slots=[(10, 85), (55, 92)],
)
def draw_living_room(frame_idx=0):
    # Floor
    draw_hline(0, 70, 100)
    draw_hline(0, 70, 101)

    # Rug pattern (dotted rectangle on floor)
    for x in range(8, 62, 3):
        canvas.px_set(x, 103)
        canvas.px_set(x, 115)
    for y in range(103, 116, 3):
        canvas.px_set(8, y)
        canvas.px_set(61, y)

    # Couch (far left background)
    # Back
    draw_rect(0, 78, 30, 4)
    # Seat
    draw_rect(2, 82, 26, 8)
    # Armrests
    draw_rect(0, 82, 4, 18)
    draw_rect(26, 82, 4, 18)
    # Cushion divider
    draw_vline(15, 83, 89)

    # Coffee table (low, in front)
    draw_hline(35, 55, 95)
    draw_hline(35, 55, 96)
    draw_vline(37, 96, 100)
    draw_vline(53, 96, 100)

    # TV (on wall, upper area)
    draw_rect(40, 55, 25, 18)
    # Screen inner
    draw_rect(42, 57, 21, 14)
    # Stand
    draw_vline(52, 73, 78)
    draw_hline(48, 56, 78)

    # Remote on coffee table
    draw_rect(42, 93, 5, 2)
    canvas.px_set(44, 93)
