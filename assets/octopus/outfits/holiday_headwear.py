"""Holiday and occasion headwear — seasonal costumes."""

import math
from ..core import canvas
from ..core.drawing import draw_hline, draw_vline, draw_line, draw_rect, fill_dithered_rect, _dither_check
from . import register


@register("santa_hat", "headwear", "Floppy triangle with fur trim and pom-pom")
def draw_santa_hat(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    by = y + canvas.Y_OFF
    # Fur trim band (dithered white/thick)
    for dy in range(3):
        for dx in range(-9, 10):
            if _dither_check(x + dx, by + dy, 0.2):
                canvas.px_set(x + dx, by + dy)
            else:
                canvas.px_clr(x + dx, by + dy)
    draw_hline(x - 9, x + 9, by)
    draw_hline(x - 9, x + 9, by + 2)
    # Floppy cone (curves to right)
    for row in range(14):
        t = row / 13.0
        half_w = int(8 * (1 - t))
        lean = int(t * t * 10)  # curves right
        cy = by - 1 - row
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(x + dx + lean, cy)
    # Fill interior
    for row in range(1, 13):
        t = row / 13.0
        half_w = int(8 * (1 - t)) - 1
        lean = int(t * t * 10)
        cy = by - 1 - row
        for dx in range(-half_w + 1, half_w):
            shade = 0.15 + 0.1 * t
            if _dither_check(x + dx + lean, cy, shade):
                canvas.px_set(x + dx + lean, cy)
    # Pom-pom at tip
    tip_x = x + 10
    tip_y = by - 14
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                canvas.px_set(tip_x + dx, tip_y + dy)


@register("witch_hat", "headwear", "Tall pointed cone with wide brim and buckle")
def draw_witch_hat(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    by = y + canvas.Y_OFF
    # Wide brim
    for dy in range(2):
        draw_hline(x - 14, x + 14, by + dy)
    # Brim curve (slight upturn at edges)
    canvas.px_set(x - 14, by - 1)
    canvas.px_set(x + 14, by - 1)
    # Tall cone
    for row in range(18):
        t = row / 17.0
        half_w = int(7 * (1 - t * 0.85))
        cy = by - 1 - row
        canvas.px_set(x - half_w, cy)
        canvas.px_set(x + half_w, cy)
        if row == 0:
            draw_hline(x - half_w, x + half_w, cy)
    # Fill cone
    for row in range(1, 17):
        t = row / 17.0
        half_w = int(7 * (1 - t * 0.85)) - 1
        cy = by - 1 - row
        for dx in range(-half_w, half_w + 1):
            if _dither_check(x + dx, cy, 0.3):
                canvas.px_set(x + dx, cy)
    # Tip (bent slightly)
    canvas.px_set(x + 1, by - 19)
    canvas.px_set(x + 2, by - 20)
    # Buckle band
    draw_hline(x - 6, x + 6, by - 3)
    draw_hline(x - 6, x + 6, by - 5)
    draw_rect(x - 2, by - 6, 4, 4)
    canvas.px_clr(x - 1, by - 5)
    canvas.px_clr(x, by - 5)


@register("bunny_ears", "headwear", "Two tall oval ears on headband")
def draw_bunny_ears(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    by = y + canvas.Y_OFF
    # Headband
    draw_hline(x - 8, x + 8, by)
    draw_hline(x - 8, x + 8, by + 1)
    # Left ear
    for dy in range(16):
        t = dy / 15.0
        half_w = int(3 * math.sin(t * math.pi))
        ey = by - 1 - dy
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(x - 5 + dx, ey)
        # Inner ear (lighter dither)
        inner_w = max(0, half_w - 1)
        for dx in range(-inner_w, inner_w + 1):
            if _dither_check(x - 5 + dx, ey, 0.15):
                pass  # keep outer, clear inner for "pink"
            else:
                canvas.px_clr(x - 5 + dx, ey)
    # Right ear
    for dy in range(16):
        t = dy / 15.0
        half_w = int(3 * math.sin(t * math.pi))
        ey = by - 1 - dy
        for dx in range(-half_w, half_w + 1):
            canvas.px_set(x + 5 + dx, ey)
        inner_w = max(0, half_w - 1)
        for dx in range(-inner_w, inner_w + 1):
            if not _dither_check(x + 5 + dx, ey, 0.15):
                canvas.px_clr(x + 5 + dx, ey)


@register("shamrock_hat", "headwear", "Short top hat with clover on band")
def draw_shamrock_hat(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    by = y + canvas.Y_OFF
    # Brim
    draw_hline(x - 10, x + 10, by)
    draw_hline(x - 10, x + 10, by + 1)
    # Short crown
    draw_rect(x - 6, by - 8, 13, 8)
    for row in range(1, 7):
        for dx in range(-5, 6):
            if _dither_check(x + dx, by - row, 0.15):
                canvas.px_set(x + dx, by - row)
    # Band
    draw_hline(x - 6, x + 6, by - 2)
    draw_hline(x - 6, x + 6, by - 3)
    # Clover (3 circles + stem)
    cx = x + 1
    cy = by - 3
    for ox, oy in [(-2, -1), (0, -2), (2, -1)]:
        canvas.px_set(cx + ox, cy + oy)
        canvas.px_set(cx + ox + 1, cy + oy)
        canvas.px_set(cx + ox, cy + oy - 1)
    canvas.px_set(cx, cy)  # stem


@register("fireworks_crown", "headwear", "Zigzag crown with starburst dots")
def draw_fireworks_crown(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    by = y + canvas.Y_OFF
    # Crown band
    draw_hline(x - 8, x + 8, by)
    draw_hline(x - 8, x + 8, by + 1)
    # Zigzag points
    for i in range(5):
        px = x - 8 + i * 4
        canvas.px_set(px, by - 3)
        canvas.px_set(px - 1, by - 2)
        canvas.px_set(px + 1, by - 2)
        canvas.px_set(px, by - 1)
    # Starburst dots radiating up (animated)
    import math
    for i in range(6):
        angle = i * 60 + frame_idx_compat(0) * 15
        r = 8 + (i % 3) * 2
        sx = x + int(r * math.cos(math.radians(angle)))
        sy = by - 6 + int(r * 0.6 * math.sin(math.radians(angle)))
        if sy > 0:
            canvas.px_set(sx, sy)


def frame_idx_compat(default):
    """Placeholder for frame_idx when not available in static draw."""
    return default


@register("heart_headband", "headwear", "Thin band with heart shapes on springs")
def draw_heart_headband(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    by = y + canvas.Y_OFF
    # Thin band
    draw_hline(x - 8, x + 8, by + 1)
    # Spring wires
    for side in [-4, 4]:
        hx = x + side
        draw_vline(hx, by - 5, by)
        # Heart at top
        hy = by - 7
        canvas.px_set(hx - 1, hy)
        canvas.px_set(hx + 1, hy)
        canvas.px_set(hx - 2, hy + 1)
        canvas.px_set(hx + 2, hy + 1)
        canvas.px_set(hx - 1, hy + 1)
        canvas.px_set(hx + 1, hy + 1)
        canvas.px_set(hx, hy + 2)


@register("birthday_crown", "headwear", "Party crown with candle on top")
def draw_birthday_crown(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    by = y + canvas.Y_OFF
    # Crown band
    draw_hline(x - 8, x + 8, by)
    draw_hline(x - 8, x + 8, by + 1)
    # 3 points
    for px in [x - 5, x, x + 5]:
        canvas.px_set(px, by - 3)
        canvas.px_set(px - 1, by - 2)
        canvas.px_set(px + 1, by - 2)
        canvas.px_set(px - 1, by - 1)
        canvas.px_set(px + 1, by - 1)
    # Dots on band
    for dx in [-6, -3, 0, 3, 6]:
        canvas.px_clr(x + dx, by)
    # Candle on center point
    draw_vline(x, by - 7, by - 3)
    draw_vline(x + 1, by - 7, by - 3)
    # Flame
    canvas.px_set(x, by - 8)
    canvas.px_set(x - 1, by - 9)
    canvas.px_set(x + 1, by - 9)
    canvas.px_set(x, by - 10)
