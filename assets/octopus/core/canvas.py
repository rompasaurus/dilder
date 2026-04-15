"""Frame buffer and pixel operations.

Extracted from render_c_previews.py — same constants and pixel ops the C
firmware uses, wrapped so every module can import them without globals.
"""

import math
from PIL import Image

# ── Canvas constants (match C firmware) ──
IMG_W = 250
IMG_H = 122
Y_OFF = 12
SCALE = 4  # default upscale for preview PNGs

# ── Frame buffer (module-level, shared across draw calls) ──
_frame = None  # 2D list [y][x], 1=black 0=white

# ── Body transform state (set per-frame before drawing) ──
body_dx = 0
body_dy = 0
body_x_expand = 0
wobble_amp = 0.0
wobble_freq = 0.0
wobble_phase = 0.0


def clear_frame():
    """Reset frame buffer to all white."""
    global _frame
    _frame = [[0] * IMG_W for _ in range(IMG_H)]


def get_frame():
    """Return reference to current frame buffer (2D list)."""
    return _frame


def px_set(x, y):
    """Set pixel to black (absolute coordinates)."""
    if 0 <= x < IMG_W and 0 <= y < IMG_H:
        _frame[y][x] = 1


def px_clr(x, y):
    """Clear pixel to white (absolute coordinates)."""
    if 0 <= x < IMG_W and 0 <= y < IMG_H:
        _frame[y][x] = 0


def row_wobble(y):
    """Per-row sine wave distortion for body transforms."""
    if wobble_amp == 0:
        return 0
    return int(wobble_amp * math.sin(y * wobble_freq + wobble_phase))


def px_set_off(x, y):
    """Set pixel with body transform offsets applied."""
    px_set(x + body_dx + row_wobble(y), y + Y_OFF + body_dy)


def px_clr_off(x, y):
    """Clear pixel with body transform offsets applied."""
    px_clr(x + body_dx + row_wobble(y), y + Y_OFF + body_dy)


def reset_body_transform():
    """Reset all body transform globals to zero/default."""
    global body_dx, body_dy, body_x_expand, wobble_amp, wobble_freq, wobble_phase
    body_dx = 0
    body_dy = 0
    body_x_expand = 0
    wobble_amp = 0.0
    wobble_freq = 0.0
    wobble_phase = 0.0


def set_body_transform(dx=0, dy=0, x_expand=0, w_amp=0.0, w_freq=0.0, w_phase=0.0):
    """Set body transform globals explicitly."""
    global body_dx, body_dy, body_x_expand, wobble_amp, wobble_freq, wobble_phase
    body_dx = dx
    body_dy = dy
    body_x_expand = x_expand
    wobble_amp = w_amp
    wobble_freq = w_freq
    wobble_phase = w_phase


def frame_to_image(scale=None):
    """Convert current frame buffer to a Pillow Image, scaled up."""
    if scale is None:
        scale = SCALE
    img = Image.new("1", (IMG_W, IMG_H), color=1)  # 1 = white
    pixels = img.load()
    for y in range(IMG_H):
        for x in range(IMG_W):
            if _frame[y][x]:
                pixels[x, y] = 0  # 0 = black in mode "1"
    if scale > 1:
        img = img.resize((IMG_W * scale, IMG_H * scale), Image.NEAREST)
    return img
