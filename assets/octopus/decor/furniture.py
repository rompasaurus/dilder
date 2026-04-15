"""Furniture props — bed, couch, desk, chair, bookshelf, nightstand."""

from ..core import canvas
from ..core.drawing import draw_rect, draw_hline, draw_vline, draw_line
from . import register


@register("bed", "furniture", 40, 20, "Rectangular frame with pillow and blanket")
def draw_bed(x, y):
    draw_rect(x, y, 40, 20)
    # Headboard (taller left side)
    draw_rect(x, y - 8, 6, 28)
    # Pillow bump
    draw_rect(x + 7, y + 2, 10, 6)
    # Blanket fold line
    draw_hline(x + 18, x + 38, y + 10)


@register("couch", "furniture", 35, 18, "Rounded back with cushion and armrests")
def draw_couch(x, y):
    # Back
    draw_rect(x, y, 35, 4)
    # Seat
    draw_rect(x + 2, y + 4, 31, 8)
    # Armrests
    draw_rect(x, y + 4, 4, 14)
    draw_rect(x + 31, y + 4, 4, 14)
    # Cushion divider
    draw_vline(x + 17, y + 5, y + 11)
    # Legs
    draw_vline(x + 3, y + 14, y + 18)
    draw_vline(x + 32, y + 14, y + 18)


@register("desk", "furniture", 30, 15, "Flat top with two legs")
def draw_desk(x, y):
    draw_hline(x, x + 30, y)
    draw_hline(x, x + 30, y + 1)
    draw_vline(x + 2, y + 2, y + 15)
    draw_vline(x + 28, y + 2, y + 15)


@register("chair", "furniture", 15, 20, "Back rest + seat + 4 legs")
def draw_chair(x, y):
    # Back rest
    draw_rect(x + 1, y, 13, 2)
    draw_vline(x + 2, y, y + 12)
    draw_vline(x + 13, y, y + 12)
    # Seat
    draw_hline(x, x + 15, y + 10)
    draw_hline(x, x + 15, y + 11)
    # Legs
    draw_vline(x + 1, y + 12, y + 20)
    draw_vline(x + 14, y + 12, y + 20)


@register("bookshelf", "furniture", 20, 25, "Rectangle with shelf lines and book spines")
def draw_bookshelf(x, y):
    draw_rect(x, y, 20, 25)
    # 3 shelves
    for sy in [y + 8, y + 16]:
        draw_hline(x, x + 20, sy)
    # Book spines (vertical lines on each shelf)
    for shelf_top in [y + 1, y + 9, y + 17]:
        for bx in range(x + 3, x + 18, 3):
            draw_vline(bx, shelf_top, shelf_top + 6)


@register("nightstand", "furniture", 12, 15, "Small rectangle with drawer and knob")
def draw_nightstand(x, y):
    draw_rect(x, y, 12, 15)
    draw_hline(x + 1, x + 11, y + 7)  # drawer line
    canvas.px_set(x + 6, y + 4)       # knob
    canvas.px_set(x + 6, y + 11)      # knob
