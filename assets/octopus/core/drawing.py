"""Drawing primitives: circles, lines, arcs, rectangles.

All functions draw into the module-level frame buffer via canvas pixel ops.
Functions suffixed _off use body-transform-aware coordinates; plain versions
use absolute coordinates.
"""

import math
from . import canvas


def fill_circle(cx, cy, r_sq, set_val, use_offset=True):
    """Fill a circle at (cx, cy) with squared-radius r_sq.

    set_val: 1 = black (px_set), 0 = white (px_clr)
    use_offset: True = apply body transform, False = absolute coords
    """
    r = int(math.isqrt(r_sq)) + 1
    setter = canvas.px_set_off if use_offset else canvas.px_set
    clearer = canvas.px_clr_off if use_offset else canvas.px_clr
    fn = setter if set_val else clearer
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r_sq:
                fn(cx + dx, cy + dy)


def draw_line(x0, y0, x1, y1, use_offset=False):
    """Bresenham line from (x0,y0) to (x1,y1)."""
    setter = canvas.px_set_off if use_offset else canvas.px_set
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        setter(x0, y0)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def draw_arc(cx, cy, r, start_deg, end_deg, use_offset=False):
    """Draw an arc (outline only) from start_deg to end_deg."""
    setter = canvas.px_set_off if use_offset else canvas.px_set
    steps = max(int(abs(end_deg - start_deg) / 2), 8)
    for i in range(steps + 1):
        t = start_deg + (end_deg - start_deg) * i / steps
        x = cx + int(r * math.cos(math.radians(t)))
        y = cy + int(r * math.sin(math.radians(t)))
        setter(x, y)


def draw_rect(x, y, w, h, filled=False, use_offset=False):
    """Draw a rectangle. Filled = solid black, otherwise outline only."""
    setter = canvas.px_set_off if use_offset else canvas.px_set
    if filled:
        for dy in range(h):
            for dx in range(w):
                setter(x + dx, y + dy)
    else:
        for dx in range(w):
            setter(x + dx, y)
            setter(x + dx, y + h - 1)
        for dy in range(h):
            setter(x, y + dy)
            setter(x + w - 1, y + dy)


def draw_hline(x0, x1, y, use_offset=False):
    """Horizontal line from x0 to x1 at row y."""
    setter = canvas.px_set_off if use_offset else canvas.px_set
    for x in range(min(x0, x1), max(x0, x1) + 1):
        setter(x, y)


def draw_vline(x, y0, y1, use_offset=False):
    """Vertical line from y0 to y1 at column x."""
    setter = canvas.px_set_off if use_offset else canvas.px_set
    for y in range(min(y0, y1), max(y0, y1) + 1):
        setter(x, y)


# ── Dithering / Texture / Shading ──

# Ordered dither matrices (Bayer) for different shade levels
# Returns True if pixel should be black at given density
def _dither_check(x, y, density):
    """Ordered dither: density 0.0 (white) to 1.0 (black).

    Uses a 4x4 Bayer matrix for smooth gradients on 1-bit display.
    """
    BAYER_4x4 = [
        [0,  8,  2, 10],
        [12, 4, 14,  6],
        [3, 11,  1,  9],
        [15, 7, 13,  5],
    ]
    threshold = BAYER_4x4[y % 4][x % 4]
    return density * 16.0 > threshold


def fill_dithered_rect(x, y, w, h, density):
    """Fill a rectangle with ordered dithering at given density (0.0-1.0)."""
    for dy in range(h):
        for dx in range(w):
            px, py = x + dx, y + dy
            if _dither_check(px, py, density):
                canvas.px_set(px, py)


def fill_dithered_circle(cx, cy, r, density):
    """Fill a circle with dithered shading."""
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                px, py = cx + dx, cy + dy
                if _dither_check(px, py, density):
                    canvas.px_set(px, py)


def gradient_vfill(x, y, w, h, density_top, density_bottom):
    """Vertical gradient fill — density interpolates top to bottom."""
    for dy in range(h):
        t = dy / max(h - 1, 1)
        density = density_top + (density_bottom - density_top) * t
        for dx in range(w):
            px, py = x + dx, y + dy
            if _dither_check(px, py, density):
                canvas.px_set(px, py)


def gradient_hfill(x, y, w, h, density_left, density_right):
    """Horizontal gradient fill — density interpolates left to right."""
    for dx in range(w):
        t = dx / max(w - 1, 1)
        density = density_left + (density_right - density_left) * t
        for dy in range(h):
            px, py = x + dx, y + dy
            if _dither_check(px, py, density):
                canvas.px_set(px, py)


def fill_dithered_poly(points, density):
    """Fill a convex polygon with dithered shading.

    points: list of (x, y) tuples defining polygon vertices.
    Uses scanline fill.
    """
    if len(points) < 3:
        return
    min_y = max(0, min(p[1] for p in points))
    max_y = min(canvas.IMG_H - 1, max(p[1] for p in points))
    for y in range(min_y, max_y + 1):
        intersections = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if y0 == y1:
                continue
            if min(y0, y1) <= y < max(y0, y1):
                x_int = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                intersections.append(x_int)
        intersections.sort()
        for i in range(0, len(intersections) - 1, 2):
            x_start = max(0, int(intersections[i]))
            x_end = min(canvas.IMG_W - 1, int(intersections[i + 1]))
            for x in range(x_start, x_end + 1):
                if _dither_check(x, y, density):
                    canvas.px_set(x, y)


def draw_shadow(x, y, w, h, offset_x=2, offset_y=2, density=0.3):
    """Draw a dithered drop shadow behind a rectangular area."""
    fill_dithered_rect(x + offset_x, y + offset_y, w, h, density)


def draw_floor_perspective(y_horizon, y_bottom, x_left, x_right,
                           tile_w=12, tile_h_near=8, density_far=0.15,
                           density_near=0.05):
    """Draw a perspective floor grid with tiles shrinking toward horizon.

    Creates depth illusion with converging lines and dithered shading.
    """
    depth = y_bottom - y_horizon
    if depth <= 0:
        return
    # Horizontal lines (get closer together near horizon)
    row = 0
    y = y_bottom
    while y > y_horizon:
        t = (y_bottom - y) / depth  # 0 at bottom, 1 at horizon
        spacing = max(2, int(tile_h_near * (1.0 - t * 0.7)))
        # Converging side edges
        squeeze = t * 0.4
        xl = int(x_left + (x_right - x_left) * squeeze * 0.5)
        xr = int(x_right - (x_right - x_left) * squeeze * 0.5)
        draw_hline(xl, xr, y)
        # Alternate row shading for checkerboard
        if row % 2 == 0:
            shade = density_far * t + density_near * (1 - t)
            for dx in range(xl, xr + 1):
                col = (dx - xl) // max(1, int(tile_w * (1 - t * 0.5)))
                if col % 2 == 0:
                    if _dither_check(dx, y, shade):
                        pass  # already set by hline, skip double work
        y -= spacing
        row += 1

    # Vertical converging lines (perspective)
    num_lines = (x_right - x_left) // tile_w
    cx = (x_left + x_right) // 2
    for i in range(num_lines + 1):
        t_line = i / max(num_lines, 1)
        x_bottom = x_left + int(t_line * (x_right - x_left))
        x_top = cx + int((x_bottom - cx) * 0.3)  # converge toward center
        draw_line(x_bottom, y_bottom, x_top, y_horizon)


def draw_curved_surface(cx, cy, rx, ry, density_center=0.1,
                        density_edge=0.6):
    """Draw an ellipse with radial gradient shading — simulates 3D sphere/dome."""
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            nx = dx / max(rx, 1)
            ny = dy / max(ry, 1)
            dist = nx * nx + ny * ny
            if dist <= 1.0:
                # Radial gradient: lighter center, darker edges
                density = density_center + (density_edge - density_center) * dist
                px, py = cx + dx, cy + dy
                if 0 <= px < canvas.IMG_W and 0 <= py < canvas.IMG_H:
                    if _dither_check(px, py, density):
                        canvas.px_set(px, py)


def draw_thick_line(x0, y0, x1, y1, thickness=2, use_offset=False):
    """Draw a line with variable thickness."""
    setter = canvas.px_set_off if use_offset else canvas.px_set
    dx = abs(x1 - x0)
    dy_val = abs(y1 - y0)
    # Draw the main line and offset copies
    half = thickness // 2
    for off in range(-half, half + 1):
        if dx >= dy_val:
            draw_line(x0, y0 + off, x1, y1 + off, use_offset)
        else:
            draw_line(x0 + off, y0, x1 + off, y1, use_offset)
