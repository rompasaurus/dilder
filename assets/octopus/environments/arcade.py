"""Arcade environment — game cabinets, pixel patterns, coin-op outlines."""

from ..core import canvas
from ..core.drawing import draw_rect, draw_hline, draw_vline
from . import register


@register(
    "arcade",
    ground_y=100,
    has_weather=False,
    description="Arcade with game cabinet silhouettes, pixel patterns, coin-op",
    decor_slots=[(5, 90), (55, 92)],
)
def draw_arcade(frame_idx=0):
    # Floor
    draw_hline(0, 70, 100)
    draw_hline(0, 70, 101)

    # Pixel/tile pattern on floor (alternating)
    for y in range(102, 122, 3):
        for x in range(0, 70, 3):
            if ((x // 3) + (y // 3)) % 3 == 0:
                canvas.px_set(x, y)
                canvas.px_set(x + 1, y)

    # Game cabinet 1 (left)
    draw_rect(0, 55, 16, 45)
    # Screen area
    draw_rect(2, 60, 12, 14)
    # Screen content (simple invader shape)
    for dx, dy in [(-2, 0), (-1, -1), (0, -2), (1, -1), (2, 0),
                   (-3, 1), (-1, 1), (1, 1), (3, 1),
                   (-3, 2), (-2, 3), (2, 3), (3, 2)]:
        canvas.px_set(8 + dx, 67 + dy)
    # Control panel
    draw_rect(3, 78, 10, 5)
    # Joystick
    draw_vline(6, 76, 78)
    canvas.px_set(5, 75)
    canvas.px_set(6, 75)
    canvas.px_set(7, 75)
    # Buttons
    canvas.px_set(10, 79)
    canvas.px_set(12, 79)

    # Game cabinet 2 (right, different shape)
    draw_rect(52, 58, 18, 42)
    # Screen
    draw_rect(54, 62, 14, 12)
    # Screen content (pac-man style dots)
    for dx in range(0, 12, 3):
        canvas.px_set(56 + dx, 68)
    # Pac shape
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                canvas.px_set(57 + dx, 68 + dy)
    canvas.px_clr(59, 67)
    canvas.px_clr(59, 68)
    # Control panel
    draw_rect(55, 78, 12, 5)

    # Coin-op machine (center background)
    draw_rect(28, 65, 12, 35)
    # Prize window
    draw_rect(30, 68, 8, 10)
    # Coin slot
    draw_hline(32, 36, 82)
    # "INSERT COIN" (approximated with dot pattern)
    for i, x in enumerate(range(30, 39)):
        if i % 2 == 0:
            canvas.px_set(x, 85)

    # Neon sign dots (animated flash)
    sign_y = 50
    for x in range(5, 68, 4):
        if (x + frame_idx * 2) % 8 < 4:
            canvas.px_set(x, sign_y)
            canvas.px_set(x + 1, sign_y)
