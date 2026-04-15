"""Desert environment -- sand dunes, cacti, scorching sun, mesa, tumbleweed.

Wide-open arid landscape with wave-textured dunes, heat shimmer lines,
and distant mesa/butte silhouettes. Skull detail in foreground.
"""

import math
from ..core import canvas
from ..core.drawing import (
    draw_rect, draw_line, draw_hline, draw_vline, draw_thick_line,
    fill_dithered_rect, fill_dithered_circle, gradient_vfill,
    fill_dithered_poly, _dither_check, draw_curved_surface,
)
from . import register


def _draw_sun(sx, sy, r, frame_idx):
    """Scorching sun with animated heat rays."""
    # Solid sun disc
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                canvas.px_set(sx + dx, sy + dy)
    # Rays (alternating lengths, animated)
    for i in range(12):
        angle = math.radians(i * 30 + frame_idx * 3)
        r_inner = r + 2
        r_outer = r + 4 + int(2 * math.sin(frame_idx * 0.5 + i))
        x0 = sx + int(r_inner * math.cos(angle))
        y0 = sy + int(r_inner * math.sin(angle))
        x1 = sx + int(r_outer * math.cos(angle))
        y1 = sy + int(r_outer * math.sin(angle))
        draw_line(x0, y0, x1, y1)


def _draw_cactus(cx, cy, height, arm_l=True, arm_r=True):
    """Saguaro cactus with optional arms and rib texture."""
    # Main trunk
    draw_thick_line(cx, cy - height, cx, cy, 3)
    # Rib lines (vertical texture)
    for y in range(cy - height + 2, cy):
        if y % 3 == 0:
            canvas.px_set(cx - 1, y)
            canvas.px_set(cx + 1, y)
    # Top rounded cap
    canvas.px_set(cx, cy - height - 1)
    canvas.px_set(cx - 1, cy - height)
    canvas.px_set(cx + 1, cy - height)

    # Left arm
    if arm_l:
        arm_y = cy - int(height * 0.6)
        draw_thick_line(cx, arm_y, cx - 6, arm_y, 2)
        draw_thick_line(cx - 6, arm_y, cx - 6, arm_y - 8, 2)
        canvas.px_set(cx - 6, arm_y - 9)
    # Right arm
    if arm_r:
        arm_y = cy - int(height * 0.4)
        draw_thick_line(cx, arm_y, cx + 5, arm_y, 2)
        draw_thick_line(cx + 5, arm_y, cx + 5, arm_y - 6, 2)
        canvas.px_set(cx + 5, arm_y - 7)


def _draw_mesa(mx, my, top_w, height, density=0.25):
    """Flat-topped mesa/butte silhouette."""
    base_w = top_w + height // 2
    fill_dithered_poly([
        (mx - top_w // 2, my - height),
        (mx + top_w // 2, my - height),
        (mx + base_w // 2, my),
        (mx - base_w // 2, my),
    ], density)
    # Flat top line
    draw_hline(mx - top_w // 2, mx + top_w // 2, my - height)
    # Side edges
    draw_line(mx - top_w // 2, my - height, mx - base_w // 2, my)
    draw_line(mx + top_w // 2, my - height, mx + base_w // 2, my)
    # Horizontal erosion lines
    for i in range(1, 4):
        stripe_y = my - height + i * (height // 4)
        w_at_y = top_w // 2 + (base_w - top_w) // 2 * i // 4
        draw_hline(mx - w_at_y, mx + w_at_y, stripe_y)


def _draw_skull(sx, sy):
    """Small skull on the sand."""
    # Cranium (rounded top)
    for dy in range(-4, 1):
        hw = int(3 * math.sqrt(max(0, 1 - (dy / 4.0) ** 2)))
        for dx in range(-hw, hw + 1):
            canvas.px_set(sx + dx, sy + dy)
    # Jaw (narrower)
    for dx in range(-2, 3):
        canvas.px_set(sx + dx, sy + 1)
    for dx in range(-1, 2):
        canvas.px_set(sx + dx, sy + 2)
    # Eye sockets (clear)
    canvas.px_clr(sx - 1, sy - 1)
    canvas.px_clr(sx + 1, sy - 1)
    # Nose
    canvas.px_clr(sx, sy)


def _draw_tumbleweed(tx, ty, r, frame_idx):
    """Rolling tumbleweed with internal tangles."""
    phase = frame_idx * 0.3
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                # On the edge
                if dx * dx + dy * dy > (r - 1) * (r - 1):
                    canvas.px_set(tx + dx, ty + dy)
                # Interior tangle lines
                elif (dx + dy + int(phase)) % 3 == 0:
                    canvas.px_set(tx + dx, ty + dy)


def _draw_dune_wave(y_base, x_start, x_end, amplitude, freq, density):
    """Sine-wave textured sand dune surface."""
    for x in range(x_start, x_end):
        wave_h = int(amplitude * math.sin(x * freq))
        surface_y = y_base - wave_h
        # Fill below surface
        for y in range(surface_y, y_base + 5):
            depth = (y - surface_y) / max(10, 1)
            shade = density * (0.6 + 0.4 * min(1.0, depth))
            if _dither_check(x, y, shade):
                canvas.px_set(x, y)
        # Surface line
        canvas.px_set(x, surface_y)


def _draw_desert_full(frame_idx):
    """Full-canvas desert panorama (idle mode)."""
    W, H = canvas.IMG_W, canvas.IMG_H
    ground_y = 85

    # ── Sky gradient (intense, white-hot horizon) ──
    gradient_vfill(0, 0, W, 50, 0.03, 0.01)

    # ── Sun (top right, blazing) ──
    _draw_sun(210, 15, 7, frame_idx)

    # ── Heat shimmer lines (animated wavy horizontals) ──
    for hy in [42, 47, 52]:
        for x in range(W):
            wave = int(1.5 * math.sin(x * 0.15 + frame_idx * 0.4 + hy))
            if x % 4 < 2:
                canvas.px_set(x, hy + wave)

    # ── Distant mesa (far, light) ──
    _draw_mesa(60, ground_y - 8, 30, 25, density=0.12)
    _draw_mesa(180, ground_y - 5, 22, 18, density=0.10)

    # ── Dune layers (back to front, increasing density) ──
    # Far dunes
    _draw_dune_wave(ground_y - 5, 0, W, 4, 0.025, 0.08)
    # Mid dunes
    _draw_dune_wave(ground_y + 5, 0, W, 6, 0.018, 0.12)
    # Near dunes (foreground)
    _draw_dune_wave(ground_y + 15, 0, W, 8, 0.013, 0.18)

    # ── Main ground fill ──
    for y in range(ground_y + 8, H):
        depth = (y - ground_y) / max(H - ground_y - 1, 1)
        for x in range(W):
            shade = 0.06 + depth * 0.06
            # Sand ripple texture
            ripple = 0.02 * math.sin(x * 0.3 + y * 0.15)
            if _dither_check(x, y, shade + ripple):
                canvas.px_set(x, y)

    # ── Cacti ──
    _draw_cactus(120, ground_y + 10, 28, arm_l=True, arm_r=True)
    _draw_cactus(35, ground_y + 12, 18, arm_l=False, arm_r=True)
    _draw_cactus(200, ground_y + 8, 22, arm_l=True, arm_r=False)

    # ── Tumbleweed (animated roll) ──
    tw_x = 155 + int(8 * math.sin(frame_idx * 0.2))
    _draw_tumbleweed(tw_x, ground_y + 18, 4, frame_idx)

    # ── Skull ──
    _draw_skull(85, ground_y + 16)

    # ── Small rocks scattered ──
    for rx, ry in [(25, ground_y + 20), (145, ground_y + 22),
                   (220, ground_y + 18), (100, ground_y + 25)]:
        canvas.px_set(rx, ry)
        canvas.px_set(rx + 1, ry)
        canvas.px_set(rx, ry - 1)


def _draw_desert_speaking(frame_idx):
    """Left-zone desert for speaking mode."""
    ground_y = 82

    # Sky
    gradient_vfill(0, 0, 72, 45, 0.03, 0.01)

    # Sun (small)
    _draw_sun(10, 10, 4, frame_idx)

    # Heat shimmer
    for hy in [40, 45]:
        for x in range(72):
            wave = int(math.sin(x * 0.15 + frame_idx * 0.4 + hy))
            if x % 5 < 2:
                canvas.px_set(x, hy + wave)

    # Distant mesa hint
    _draw_mesa(55, ground_y - 5, 12, 12, density=0.10)

    # Dune curve
    for x in range(72):
        wave_h = int(4 * math.sin(x * 0.04))
        surface_y = ground_y - wave_h
        canvas.px_set(x, surface_y)
        for y in range(surface_y + 1, surface_y + 4):
            if _dither_check(x, y, 0.10):
                canvas.px_set(x, y)

    # Ground sand
    for y in range(ground_y + 1, canvas.IMG_H):
        depth = (y - ground_y) / max(canvas.IMG_H - ground_y - 1, 1)
        for x in range(72):
            shade = 0.05 + depth * 0.05
            if _dither_check(x, y, shade):
                canvas.px_set(x, y)
    draw_hline(0, 71, ground_y)

    # Cactus
    _draw_cactus(40, ground_y + 5, 20, arm_l=True, arm_r=False)

    # Small rock
    canvas.px_set(20, ground_y + 8)
    canvas.px_set(21, ground_y + 8)
    canvas.px_set(20, ground_y + 7)


@register(
    "desert",
    ground_y=85,
    has_weather=True,
    description="Arid desert with sand dunes, cacti, mesa, scorching sun, heat shimmer, skull",
    decor_slots=[(8, 100), (50, 102)],
)
def draw_desert(frame_idx=0, mode="speaking"):
    if mode == "idle":
        _draw_desert_full(frame_idx)
    else:
        _draw_desert_speaking(frame_idx)
