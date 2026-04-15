"""Headwear outfits — drawn relative to dome top anchor.

VISIBILITY RULE: The octopus body is solid black. Outfits must first CLEAR
(px_clr) a white silhouette, then draw black outlines/details on top.
Same technique as the eye sockets.
"""

import math
from ..core import canvas
from ..core.drawing import draw_rect, draw_hline, fill_circle, _dither_check
from . import register


def _clr(x, y):
    """Clear pixel with body offset (white on black body)."""
    canvas.px_clr(x + canvas.body_dx, y + canvas.Y_OFF + canvas.body_dy)

def _set(x, y):
    """Set pixel with body offset (black outline)."""
    canvas.px_set(x + canvas.body_dx, y + canvas.Y_OFF + canvas.body_dy)


@register("top_hat", "headwear", "Tall rectangle on dome top with brim line")
def draw_top_hat(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    # Clear white silhouette first
    for dy in range(-14, 2):
        half = 10 if dy >= 0 else 5  # brim is wider
        for dx in range(-half, half + 1):
            _clr(x + dx, y + dy)
    # Black outline
    # Brim
    for dx in range(-10, 11):
        _set(x + dx, y)
        _set(x + dx, y + 1)
    # Crown outline
    for dy in range(-14, 1):
        _set(x - 6, y + dy)
        _set(x + 6, y + dy)
    for dx in range(-6, 7):
        _set(x + dx, y - 14)
    # Hat band
    for dx in range(-5, 6):
        _set(x + dx, y - 3)


@register("crown", "headwear", "3-point zigzag band with jewel dots")
def draw_crown(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    # Clear white area
    for dy in range(-5, 2):
        for dx in range(-8, 9):
            _clr(x + dx, y + dy)
    # Band outline
    for dx in range(-8, 9):
        _set(x + dx, y)
        _set(x + dx, y + 1)
    # 3 points
    for px in [x - 5, x, x + 5]:
        _set(px, y - 4)
        _set(px - 1, y - 3)
        _set(px + 1, y - 3)
        _set(px, y - 2)
        _set(px - 1, y - 1)
        _set(px + 1, y - 1)
    # Jewel dots (white on the black points)
    for px in [x - 5, x, x + 5]:
        _clr(px, y - 3)


@register("chef_hat", "headwear", "Tall puffy dome wider than head")
def draw_chef_hat(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    # Clear white silhouette (tall puffy shape)
    for row in range(14):
        half_w = 10 - (row * row) // 18
        for dx in range(-half_w, half_w + 1):
            _clr(x + dx, y - 1 - row)
    # Band
    for dx in range(-8, 9):
        _clr(x + dx, y)
    # Black outline
    for dx in range(-8, 9):
        _set(x + dx, y)
        _set(x + dx, y + 1)
    # Dome outline
    for row in range(14):
        half_w = 10 - (row * row) // 18
        _set(x - half_w, y - 1 - row)
        _set(x + half_w, y - 1 - row)
    for dx in range(-6, 7):
        _set(x + dx, y - 14)
    # Puffy crease lines
    for dx in range(-4, 5, 4):
        for dy in range(-12, -3, 3):
            _set(x + dx, y + dy)


@register("beanie", "headwear", "Tight-fitting cap with folded brim and pom-pom")
def draw_beanie(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    # Clear white area
    for row in range(10):
        half_w = 8 - (row * row) // 12
        for dx in range(-half_w, half_w + 1):
            _clr(x + dx, y - row)
    for dx in range(-8, 9):
        for dy in range(3):
            _clr(x + dx, y + dy)
    # Folded brim (thick outline)
    for dy in range(3):
        for dx in range(-8, 9):
            _set(x + dx, y + dy)
    # Brim knit texture (white dashes)
    for dx in range(-7, 8, 3):
        _clr(x + dx, y + 1)
    # Cap dome outline
    for row in range(10):
        half_w = 8 - (row * row) // 12
        _set(x - half_w, y - row)
        _set(x + half_w, y - row)
    # Pom-pom at top
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if abs(dx) + abs(dy) <= 2:
                _set(x + dx, y - 10 + dy)
    _clr(x, y - 10)


@register("cowboy_hat", "headwear", "Wide curved brim with tall pinched crown and star")
def draw_cowboy_hat(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    # Clear white silhouette
    for row in range(12):
        half_w = 7 - int(2 * math.sin(row / 11.0 * math.pi * 0.8))
        for dx in range(-half_w, half_w + 1):
            _clr(x + dx, y - 1 - row)
    for dx in range(-14, 15):
        _clr(x + dx, y)
        _clr(x + dx, y + 1)
    # Brim outline (curved)
    for dx in range(-14, 15):
        curve = int(2 * math.sin(abs(dx) * 0.15))
        _set(x + dx, y + curve)
        _set(x + dx, y + curve + 1)
    # Crown outline
    for row in range(12):
        t = row / 11.0
        half_w = int(7 - 2 * math.sin(t * math.pi * 0.8))
        _set(x - half_w, y - 1 - row)
        _set(x + half_w, y - 1 - row)
    for dx in range(-5, 6):
        _set(x + dx, y - 12)
    # Star badge (white star on dark hat)
    _clr(x, y - 5)
    _clr(x - 1, y - 4)
    _clr(x + 1, y - 4)
    _clr(x, y - 3)


@register("hard_hat", "headwear", "Rounded dome with brim lip and stripe")
def draw_hard_hat(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    # Clear white dome
    for row in range(8):
        half_w = int(9 * math.sqrt(max(0, 1 - (row / 8.0) ** 2)))
        for dx in range(-half_w, half_w + 1):
            _clr(x + dx, y - row)
    for dx in range(-10, 11):
        _clr(x + dx, y + 1)
        _clr(x + dx, y + 2)
    # Dome outline
    for row in range(8):
        half_w = int(9 * math.sqrt(max(0, 1 - (row / 8.0) ** 2)))
        _set(x - half_w, y - row)
        _set(x + half_w, y - row)
    for dx in range(-9, 10):
        _set(x + dx, y - 8)
    # Brim lip
    for dx in range(-10, 11):
        _set(x + dx, y + 1)
        _set(x + dx, y + 2)
    # Stripe (black on white dome)
    for dx in range(-7, 8):
        _set(x + dx, y - 3)


@register("party_hat", "headwear", "Triangle with dot pattern and string line")
def draw_party_hat(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    # Clear white triangle
    for row in range(14):
        half_w = 7 - (row * 7) // 14
        for dx in range(-half_w, half_w + 1):
            _clr(x + dx, y - row)
    # Triangle outline
    for row in range(14):
        half_w = 7 - (row * 7) // 14
        _set(x - half_w, y - row)
        _set(x + half_w, y - row)
    for dx in range(-7, 8):
        _set(x + dx, y)
    _set(x, y - 14)
    # Stripe dot pattern (black dots on white)
    for row in [3, 7, 11]:
        half_w = 7 - (row * 7) // 14
        for dx in range(-half_w + 2, half_w, 3):
            _set(x + dx, y - row)
    # String chin strap
    _set(x - 8, y + 3)
    _set(x - 7, y + 2)


@register("pirate_hat", "headwear", "Wide brim with skull pattern, triangular top")
def draw_pirate_hat(dome_top, eye_centers=None, neck=None, body_center=None):
    x, y = dome_top
    # Clear white silhouette
    for dx in range(-12, 13):
        _clr(x + dx, y)
        _clr(x + dx, y - 1)
    for row in range(2, 10):
        half_w = 10 - row
        for dx in range(-half_w, half_w + 1):
            _clr(x + dx, y - row)
    # Outline
    for dx in range(-12, 13):
        _set(x + dx, y)
    for row in range(2, 10):
        half_w = 10 - row
        _set(x - half_w, y - row)
        _set(x + half_w, y - row)
    for dx in range(-8, 9):
        _set(x + dx, y - 2)
    # Skull (white dots on black outline area)
    _clr(x - 1, y - 5)
    _clr(x + 1, y - 5)
    _clr(x, y - 4)
