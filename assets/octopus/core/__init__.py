"""Core rendering engine: canvas buffer, drawing primitives, body RLE data."""

from .canvas import (
    IMG_W, IMG_H, Y_OFF, SCALE,
    clear_frame, px_set, px_clr, px_set_off, px_clr_off,
    frame_to_image, get_frame,
)
from .drawing import (
    fill_circle, draw_line, draw_arc, draw_rect, draw_hline, draw_vline,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill, gradient_hfill,
    fill_dithered_poly, draw_shadow, draw_floor_perspective,
    draw_curved_surface, draw_thick_line,
)
from .body import BODY_RLE_STANDARD, BODY_RLE_FAT, BODY_RLE_LAZY, draw_body
