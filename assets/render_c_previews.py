#!/usr/bin/env python3
"""Render octopus emotion previews using the exact C firmware drawing logic.

Produces per-mood PNG images that match what the Pico e-ink display shows,
so they can be compared against the Python devtool previews.

Each function below is a 1:1 translation of the corresponding C function
from dev-setup/sassy-octopus/main.c (and fat/lazy variants).
"""

import math, os
from PIL import Image

# ── Canvas constants (match C firmware) ──
IMG_W = 250
IMG_H = 122
Y_OFF = 12

# ── Frame buffer ──
frame = None  # 2D list [y][x], 1=black, 0=white


def clear_frame():
    global frame
    frame = [[0] * IMG_W for _ in range(IMG_H)]


def px_set(x, y):
    if 0 <= x < IMG_W and 0 <= y < IMG_H:
        frame[y][x] = 1


def px_clr(x, y):
    if 0 <= x < IMG_W and 0 <= y < IMG_H:
        frame[y][x] = 0


# Body transform globals (set per-frame by setup_body_transform)
body_dx = 0
body_dy = 0
body_x_expand = 0
wobble_amp = 0.0
wobble_freq = 0.0
wobble_phase = 0.0


def row_wobble(y):
    if wobble_amp == 0:
        return 0
    return int(wobble_amp * math.sin(y * wobble_freq + wobble_phase))


def px_set_off(x, y):
    px_set(x + body_dx + row_wobble(y), y + Y_OFF + body_dy)


def px_clr_off(x, y):
    px_clr(x + body_dx + row_wobble(y), y + Y_OFF + body_dy)


def setup_body_transform(mood, frame_idx):
    """Exact port of C setup_body_transform() — sets globals per mood+frame."""
    global body_dx, body_dy, body_x_expand, wobble_amp, wobble_freq, wobble_phase
    body_dx = 0
    body_dy = 0
    body_x_expand = 0
    wobble_amp = 0.0
    wobble_freq = 0.0
    wobble_phase = 0.0
    f = frame_idx * math.pi / 2.0

    if mood == "angry":
        body_dy = -1
        body_x_expand = 2
        wobble_amp = 0.5
        wobble_freq = 0.3
        wobble_phase = f
    elif mood == "sad":
        body_dy = 3
        body_x_expand = -1
    elif mood == "unhinged":
        body_dx = int(1.5 * math.sin(f * 7.3))
        body_dy = int(1.5 * math.sin(f * 5.1 + 1))
    elif mood == "weird":
        body_dx = int(3 * math.sin(f * 0.8))
        wobble_amp = 1.5
        wobble_freq = 0.15
        wobble_phase = f
    elif mood == "chaotic":
        body_dx = int(2 * math.sin(f * 2.1))
        body_dy = int(2 * math.sin(f * 1.7))
        wobble_amp = 3
        wobble_freq = 0.25
        wobble_phase = f * 2.0
    elif mood == "hungry":
        body_dy = -2 + int(math.sin(f * 1.5))
    elif mood == "tired":
        body_dy = 2 + int(math.sin(f * 0.5))
        body_x_expand = -1
    elif mood == "slaphappy":
        body_dx = int(3 * math.sin(f * 1.2))
        wobble_amp = 2
        wobble_freq = 0.1
        wobble_phase = f * 1.2
    elif mood == "lazy":
        body_dy = int(0.5 * math.sin(f * 0.3))
        body_dx = int(0.5 * math.sin(f * 0.15))
    elif mood == "fat":
        body_dy = int(1.5 * math.sin(f * 1.8))
    elif mood == "chill":
        body_dx = int(math.sin(f * 0.4))
        body_dy = 1
    elif mood == "creepy":
        body_x_expand = int(2 * math.sin(f * 2.0))
    elif mood == "excited":
        body_dy = int(3 * math.sin(f * 3.0))
    elif mood == "nostalgic":
        body_dx = int(2 * math.sin(f * 0.5))
        body_dy = int(math.sin(f * 0.3))
    elif mood == "homesick":
        body_dy = 1
        body_x_expand = -2
    else:  # normal
        body_dy = int(math.sin(f * 0.8))


# ── Drawing primitives (exact C port) ──

def fill_circle(cx, cy, r_sq, set_val):
    r = 5
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r_sq:
                if set_val:
                    px_set_off(cx + dx, cy + dy)
                else:
                    px_clr_off(cx + dx, cy + dy)


# ── Standard body RLE (from sassy-octopus/main.c) ──

BODY_RLE_STANDARD = [
    (10, [(22, 48)]), (11, [(18, 52)]), (12, [(16, 54)]), (13, [(14, 56)]),
    (14, [(13, 57)]), (15, [(12, 58)]), (16, [(11, 59)]), (17, [(10, 60)]),
    (18, [(10, 60)]), (19, [(9, 61)]),  (20, [(9, 61)]),  (21, [(9, 61)]),
    (22, [(9, 61)]),  (23, [(9, 61)]),  (24, [(9, 61)]),  (25, [(9, 61)]),
    (26, [(9, 61)]),  (27, [(9, 61)]),  (28, [(10, 60)]), (29, [(10, 60)]),
    (30, [(10, 60)]), (31, [(10, 60)]), (32, [(10, 60)]), (33, [(10, 60)]),
    (34, [(10, 60)]), (35, [(10, 60)]), (36, [(10, 60)]), (37, [(10, 60)]),
    (38, [(10, 60)]), (39, [(10, 60)]), (40, [(10, 60)]), (41, [(11, 59)]),
    (42, [(11, 59)]), (43, [(12, 58)]), (44, [(13, 57)]), (45, [(14, 56)]),
    (46, [(12, 58)]), (47, [(11, 59)]), (48, [(10, 60)]), (49, [(10, 60)]),
    (50, [(11, 59)]), (51, [(12, 58)]), (52, [(13, 57)]), (53, [(14, 56)]),
    (54, [(15, 55)]),
    # Tentacles
    (55, [(10, 17), (21, 28), (32, 39), (43, 50), (54, 61)]),
    (56, [(8, 15), (19, 26), (30, 37), (45, 52), (56, 63)]),
    (57, [(7, 14), (18, 24), (29, 35), (47, 53), (58, 64)]),
    (58, [(6, 12), (19, 25), (31, 37), (46, 52), (57, 63)]),
    (59, [(7, 13), (21, 27), (33, 39), (44, 50), (55, 61)]),
    (60, [(8, 14), (20, 26), (31, 37), (43, 49), (54, 60)]),
    (61, [(9, 14), (18, 24), (30, 36), (44, 50), (56, 62)]),
    (62, [(8, 13), (17, 22), (31, 37), (46, 52), (57, 63)]),
    (63, [(7, 12), (18, 23), (33, 38), (45, 51), (55, 61)]),
    (64, [(8, 13), (20, 25), (32, 37), (43, 48), (54, 59)]),
    (65, [(9, 14), (19, 24), (30, 35), (44, 49), (55, 60)]),
    (66, [(10, 14), (17, 22), (31, 36), (46, 51), (57, 62)]),
    (67, [(9, 13), (18, 22), (33, 37), (45, 50), (56, 61)]),
    (68, [(8, 12), (19, 23), (32, 36), (43, 48), (54, 59)]),
    (69, [(9, 13), (21, 25), (30, 34), (44, 48), (55, 59)]),
    (70, [(10, 14), (20, 24), (31, 35), (46, 50), (57, 61)]),
    (71, [(11, 14), (18, 22), (33, 37), (45, 49), (56, 60)]),
    (72, [(10, 13), (19, 22), (32, 35), (43, 47), (54, 58)]),
    (73, [(9, 12), (20, 23), (30, 33), (44, 47), (55, 58)]),
    (74, [(10, 13), (21, 24), (31, 34), (46, 49), (57, 60)]),
    (75, [(11, 14), (20, 23), (33, 36), (45, 48), (56, 59)]),
    (76, [(12, 14), (19, 22), (32, 35), (43, 46), (54, 57)]),
    (77, [(11, 13), (20, 22), (30, 33), (44, 46), (55, 57)]),
    (78, [(10, 12), (21, 23), (31, 33), (45, 47), (56, 58)]),
    (79, [(11, 13), (22, 24), (32, 34), (44, 46), (55, 57)]),
    (80, [(12, 14), (21, 23), (33, 35), (43, 45), (54, 56)]),
]

# ── Fat body RLE (from fat-octopus/main.c) ──

BODY_RLE_FAT = [
    (8, [(25, 45)]),  (9, [(21, 49)]),
    (10, [(18, 52)]), (11, [(15, 55)]), (12, [(13, 57)]), (13, [(11, 59)]),
    (14, [(10, 60)]), (15, [(9, 61)]),  (16, [(8, 62)]),  (17, [(7, 63)]),
    (18, [(6, 64)]),  (19, [(5, 65)]),  (20, [(5, 65)]),  (21, [(5, 65)]),
    (22, [(5, 65)]),  (23, [(5, 65)]),  (24, [(5, 65)]),  (25, [(5, 65)]),
    (26, [(5, 65)]),  (27, [(5, 65)]),
    (28, [(5, 65)]),  (29, [(5, 65)]),  (30, [(5, 65)]),  (31, [(6, 64)]),
    (32, [(6, 64)]),  (33, [(6, 64)]),  (34, [(6, 64)]),  (35, [(6, 64)]),
    (36, [(6, 64)]),  (37, [(6, 64)]),  (38, [(6, 64)]),  (39, [(6, 64)]),
    (40, [(6, 64)]),  (41, [(7, 63)]),  (42, [(7, 63)]),  (43, [(8, 62)]),
    (44, [(9, 61)]),  (45, [(10, 60)]),
    (46, [(8, 62)]),  (47, [(7, 63)]),  (48, [(6, 64)]),  (49, [(6, 64)]),
    (50, [(7, 63)]),  (51, [(8, 62)]),  (52, [(10, 60)]), (53, [(11, 59)]),
    (54, [(12, 58)]),
    (55, [(9, 18), (20, 29), (31, 40), (42, 51), (53, 62)]),
    (56, [(7, 16), (18, 27), (29, 38), (44, 53), (55, 64)]),
    (57, [(6, 15), (17, 25), (28, 36), (46, 54), (57, 65)]),
    (58, [(5, 13), (18, 26), (30, 38), (45, 53), (56, 64)]),
    (59, [(6, 14), (20, 28), (32, 40), (43, 51), (54, 62)]),
    (60, [(7, 15), (19, 27), (30, 38), (42, 50), (53, 61)]),
    (61, [(8, 15), (17, 25), (29, 37), (43, 51), (55, 63)]),
    (62, [(7, 14), (16, 23), (30, 38), (45, 53), (56, 64)]),
    (63, [(6, 13), (17, 24), (32, 39), (44, 52), (54, 62)]),
    (64, [(7, 14), (19, 26), (31, 38), (42, 49), (53, 60)]),
    (65, [(8, 15), (18, 25), (29, 36), (43, 50), (54, 61)]),
    (66, [(9, 15), (16, 23), (30, 37), (45, 52), (56, 63)]),
    (67, [(8, 14), (17, 23), (32, 38), (44, 51), (55, 62)]),
    (68, [(7, 13), (18, 24), (31, 37), (42, 49), (53, 60)]),
    (69, [(8, 14), (20, 26), (29, 35), (43, 49), (54, 60)]),
    (70, [(9, 15), (19, 25), (30, 36), (45, 51), (56, 62)]),
    (71, [(10, 15), (17, 23), (32, 38), (44, 50), (55, 61)]),
    (72, [(9, 14), (18, 23), (31, 36), (42, 48), (53, 59)]),
    (73, [(8, 13), (19, 24), (29, 34), (43, 48), (54, 59)]),
    (74, [(9, 14), (20, 25), (30, 35), (45, 50), (56, 61)]),
    (75, [(10, 15), (19, 24), (32, 37), (44, 49), (55, 60)]),
    (76, [(11, 15), (18, 23), (31, 36), (42, 47), (53, 58)]),
    (77, [(10, 14), (19, 23), (29, 34), (43, 47), (54, 58)]),
    (78, [(9, 13), (20, 24), (30, 34), (44, 48), (55, 59)]),
    (79, [(10, 14), (21, 25), (31, 35), (43, 47), (54, 58)]),
    (80, [(11, 15), (20, 24), (32, 36), (42, 46), (53, 57)]),
]

# ── Lazy body RLE (from lazy-octopus/main.c — legs draped right) ──

BODY_RLE_LAZY = [
    # Standard head dome
    (10, [(22, 48)]), (11, [(18, 52)]), (12, [(16, 54)]), (13, [(14, 56)]),
    (14, [(13, 57)]), (15, [(12, 58)]), (16, [(11, 59)]), (17, [(10, 60)]),
    (18, [(10, 60)]), (19, [(9, 61)]),  (20, [(9, 61)]),  (21, [(9, 61)]),
    (22, [(9, 61)]),  (23, [(9, 61)]),  (24, [(9, 61)]),  (25, [(9, 61)]),
    (26, [(9, 61)]),  (27, [(9, 61)]),
    # Standard body
    (28, [(10, 60)]), (29, [(10, 60)]), (30, [(10, 60)]), (31, [(10, 60)]),
    (32, [(10, 60)]), (33, [(10, 60)]), (34, [(10, 60)]), (35, [(10, 60)]),
    (36, [(10, 60)]), (37, [(10, 60)]), (38, [(10, 60)]), (39, [(10, 60)]),
    (40, [(10, 60)]), (41, [(11, 59)]), (42, [(11, 59)]), (43, [(12, 58)]),
    (44, [(13, 57)]), (45, [(14, 56)]),
    # Cheeks taper rightward
    (46, [(13, 59)]), (47, [(14, 60)]), (48, [(14, 61)]), (49, [(15, 61)]),
    (50, [(16, 61)]), (51, [(17, 60)]), (52, [(18, 59)]), (53, [(19, 58)]),
    (54, [(20, 57)]),
    # Tentacles — all 5 drape to the right
    (55, [(14, 21), (25, 32), (34, 41), (42, 49), (53, 60)]),
    (56, [(15, 21), (26, 32), (34, 40), (43, 49), (55, 61)]),
    (57, [(17, 23), (26, 32), (34, 40), (45, 51), (57, 63)]),
    (58, [(18, 24), (27, 33), (35, 41), (47, 53), (58, 64)]),
    (59, [(19, 25), (27, 33), (37, 43), (49, 55), (59, 65)]),
    (60, [(19, 25), (28, 34), (39, 45), (50, 56), (60, 66)]),
    (61, [(19, 25), (29, 35), (41, 47), (52, 58), (60, 66)]),
    (62, [(20, 26), (30, 36), (42, 48), (52, 58), (60, 66)]),
    (63, [(21, 27), (32, 38), (44, 50), (52, 58), (61, 67)]),
    (64, [(22, 28), (34, 40), (45, 51), (53, 59), (62, 68)]),
    (65, [(24, 30), (36, 42), (45, 51), (53, 59), (64, 70)]),
    (66, [(26, 31), (37, 42), (45, 50), (54, 59)]),
    (67, [(28, 33), (38, 43), (46, 51), (56, 61)]),
    (68, [(29, 34), (38, 43), (46, 51), (57, 62)]),
    (69, [(30, 35), (38, 43), (48, 53), (59, 64)]),
    (70, [(31, 36), (39, 44), (49, 54), (61, 66)]),
    (71, [(31, 36), (40, 45), (51, 56), (63, 68)]),
    (72, [(31, 36), (41, 46), (53, 58), (63, 68)]),
    (73, [(32, 37), (43, 48), (55, 60), (64, 69)]),
    (74, [(33, 38), (45, 50), (56, 61), (64, 69)]),
]


def draw_body(rle):
    for y, runs in rle:
        for x0, x1 in runs:
            ax0 = x0 - body_x_expand
            ax1 = x1 + body_x_expand
            if ax0 < 0:
                ax0 = 0
            if ax1 >= IMG_W:
                ax1 = IMG_W - 1
            for x in range(ax0, ax1 + 1):
                px_set_off(x, y)


# ── Eyes ──

def draw_eyes():
    fill_circle(22, 25, 16, 0)
    fill_circle(48, 25, 16, 0)


# ── Pupils per mood ──

def draw_pupils_normal():
    fill_circle(23, 26, 4, 1)
    fill_circle(49, 26, 4, 1)
    fill_circle(20, 23, 1, 0)
    fill_circle(46, 23, 1, 0)


def draw_pupils_weird():
    fill_circle(21, 24, 4, 1)
    fill_circle(50, 28, 4, 1)
    fill_circle(20, 23, 1, 0)
    fill_circle(46, 23, 1, 0)


def draw_pupils_unhinged():
    for x, y in [(22, 25), (23, 25), (22, 26), (23, 26),
                 (48, 25), (49, 25), (48, 26), (49, 26)]:
        px_set_off(x, y)


def draw_pupils_angry():
    fill_circle(25, 27, 4, 1)
    fill_circle(47, 27, 4, 1)
    fill_circle(23, 24, 1, 0)
    fill_circle(45, 24, 1, 0)


def draw_pupils_sad():
    fill_circle(23, 28, 4, 1)
    fill_circle(49, 28, 4, 1)
    fill_circle(21, 25, 1, 0)
    fill_circle(47, 25, 1, 0)


def draw_pupils_chaotic():
    for ecx in [22, 48]:
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                dist = dx * dx + dy * dy
                if 5 <= dist <= 9:
                    px_set_off(ecx + dx, 25 + dy)
        px_set_off(ecx, 25)


def draw_pupils_hungry():
    fill_circle(23, 23, 4, 1)
    fill_circle(49, 23, 4, 1)
    fill_circle(21, 21, 1, 0)
    fill_circle(47, 21, 1, 0)


def draw_pupils_tired():
    for dx in range(-1, 2):
        px_set_off(22 + dx, 27)
        px_set_off(22 + dx, 28)
        px_set_off(48 + dx, 27)
        px_set_off(48 + dx, 28)


def draw_pupils_lazy():
    for ecx in [22, 48]:
        px_set_off(ecx, 28)
        px_set_off(ecx + 1, 28)


def draw_pupils_fat():
    for ecx in [23, 49]:
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if dx * dx + dy * dy <= 9:
                    px_set_off(ecx + dx, 26 + dy)


def draw_pupils_chill():
    centers = [(25, 26), (51, 26)]
    for ecx, ecy in centers:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    px_set_off(ecx + dx, ecy + dy)


def draw_pupils_creepy():
    for ecx in [22, 48]:
        top = [(-2, -1), (-1, -2), (0, -1), (1, -2), (2, -1)]
        for dx, dy in top:
            px_set_off(ecx + dx, 25 + dy)
        for dx in range(-2, 3):
            px_set_off(ecx + dx, 25)
        for dx in range(-1, 2):
            px_set_off(ecx + dx, 26)
        px_set_off(ecx, 27)


def draw_pupils_excited():
    for ecx in [22, 48]:
        for d in range(-2, 3):
            px_set_off(ecx + d, 25)
            px_set_off(ecx, 25 + d)
        px_set_off(ecx - 1, 24)
        px_set_off(ecx + 1, 24)
        px_set_off(ecx - 1, 26)
        px_set_off(ecx + 1, 26)


def draw_pupils_nostalgic():
    centers = [(24, 23), (50, 23)]
    for ecx, ecy in centers:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    px_set_off(ecx + dx, ecy + dy)


def draw_pupils_homesick():
    for ecx in [23, 49]:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    px_set_off(ecx + dx, 27 + dy)


# ── Eyebrows / Eyelids ──

def draw_brows_angry():
    for i in range(18):
        t = i / 17.0
        x = 14 + int(t * 16)
        arc = 2.5 * math.sin(t * math.pi)
        y = int(20 + t * 5 - arc)
        for dy in range(3):
            px_set_off(x, y + dy)
        px_set_off(x + 1, y + 1)
    for i in range(18):
        t = i / 17.0
        x = 40 + int(t * 16)
        arc = 2.5 * math.sin(t * math.pi)
        y = int(25 - t * 5 - arc)
        for dy in range(3):
            px_set_off(x, y + dy)
        px_set_off(x + 1, y + 1)


def draw_brows_sad():
    for i in range(18):
        t = i / 17.0
        x = 14 + int(t * 16)
        arc = 2.5 * math.sin(t * math.pi)
        y = int(25 - t * 5 - arc)
        for dy in range(3):
            px_set_off(x, y + dy)
    for i in range(18):
        t = i / 17.0
        x = 40 + int(t * 16)
        arc = 2.5 * math.sin(t * math.pi)
        y = int(20 + t * 5 - arc)
        for dy in range(3):
            px_set_off(x, y + dy)


def draw_lids_tired():
    for ecx in [22, 48]:
        for dy in range(-4, -1):
            for dx in range(-4, 5):
                if dx * dx + dy * dy <= 16:
                    px_set_off(ecx + dx, 25 + dy)


def draw_eyes_slaphappy():
    # Left eye: squint shut
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if dx * dx + dy * dy <= 16:
                px_set_off(22 + dx, 25 + dy)
    for dx in range(-3, 4):
        px_clr_off(22 + dx, 25)
    # Right eye: oversized pupil
    fill_circle(49, 26, 9, 1)


def draw_lids_lazy():
    for ecx in [22, 48]:
        for dy in range(-4, 2):
            for dx in range(-4, 5):
                if dx * dx + dy * dy <= 16:
                    px_set_off(ecx + dx, 25 + dy)


def draw_tears_homesick():
    for ecx in [22, 48]:
        px_set_off(ecx, 31)
        px_set_off(ecx, 32)
        px_set_off(ecx, 33)
        px_set_off(ecx - 1, 32)
        px_set_off(ecx + 1, 32)


# ── Mouth expressions ──

def draw_mouth_smirk():
    for x in range(28, 44):
        t = (x - 28) / 15.0
        tilt = -2.0 + t * 4.0
        v = 2.0 * t - 1.0
        arc = 5.0 * math.sqrt(1.0 - v * v) if abs(v) < 1.0 else 0.0
        yc = int(39.0 + tilt + arc)
        px_clr_off(x, yc)
        px_set_off(x, yc - 1)
        px_set_off(x, yc + 1)


def draw_mouth_smile():
    for x in range(26, 45):
        cy = 38 + ((x - 35) * (x - 35)) // 25
        px_set_off(x, cy)
        px_set_off(x, cy + 1)


def draw_mouth_open():
    cx, cy, rx, ry = 35, 40, 7, 5
    for dy in range(-4, 5):
        for dx in range(-6, 7):
            if dx * dx * 16 + dy * dy * 36 <= 36 * 16:
                px_clr_off(cx + dx, cy + dy)
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            if dx * dx * ry * ry + dy * dy * rx * rx > rx * rx * ry * ry:
                continue
            for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = dx + ndx, dy + ndy
                if nx * nx * ry * ry + ny * ny * rx * rx > rx * rx * ry * ry:
                    px_set_off(cx + dx, cy + dy)
                    break


def draw_mouth_weird():
    for x in range(24, 48):
        t = (x - 24) / 23.0
        yc = 39 + int(3.5 * math.sin(t * math.pi * 3.0))
        px_clr_off(x, yc)
        px_set_off(x, yc - 1)
        px_set_off(x, yc + 1)


def draw_mouth_unhinged():
    cx, cy, rx, ry = 35, 41, 10, 7
    for dy in range(-6, 7):
        for dx in range(-9, 10):
            if dx * dx * 36 + dy * dy * 81 <= 81 * 36:
                px_clr_off(cx + dx, cy + dy)
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            if dx * dx * ry * ry + dy * dy * rx * rx > rx * rx * ry * ry:
                continue
            for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = dx + ndx, dy + ndy
                if nx * nx * ry * ry + ny * ny * rx * rx > rx * rx * ry * ry:
                    px_set_off(cx + dx, cy + dy)
                    break
    for x in range(cx - 7, cx + 8, 3):
        px_set_off(x, cy - 5)
        px_set_off(x, cy - 4)
        px_set_off(x + 1, cy - 4)


def draw_mouth_angry():
    for x in range(28, 43):
        cy = 40 - ((x - 35) * (x - 35)) // 20
        px_set_off(x, cy)
        px_set_off(x, cy + 1)


def draw_mouth_sad():
    for x in range(26, 45):
        cy = 42 - ((x - 35) * (x - 35)) // 30
        px_set_off(x, cy)
        px_set_off(x, cy + 1)


def draw_mouth_chaotic():
    for x in range(24, 48):
        phase = (x - 24) % 6
        y = (38 + phase * 2) if phase < 3 else (44 - phase * 2 + 6)
        px_set_off(x, y)
        px_set_off(x, y + 1)


def draw_mouth_hungry():
    cx, cy, rx, ry = 35, 40, 8, 5
    for dy in range(-(ry - 1), ry):
        for dx in range(-(rx - 1), rx):
            if dx * dx * (ry - 1) ** 2 + dy * dy * (rx - 1) ** 2 <= (rx - 1) ** 2 * (ry - 1) ** 2:
                px_clr_off(cx + dx, cy + dy)
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            if dx * dx * ry * ry + dy * dy * rx * rx > rx * rx * ry * ry:
                continue
            for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = dx + ndx, dy + ndy
                if nx * nx * ry * ry + ny * ny * rx * rx > rx * rx * ry * ry:
                    px_set_off(cx + dx, cy + dy)
                    break
    for dy in range(1, 6):
        px_set_off(33, cy + ry + dy)
    for dy in range(1, 4):
        px_set_off(37, cy + ry + dy + 1)


def draw_mouth_tired():
    cx, cy, rx, ry = 35, 40, 5, 7
    for dy in range(-(ry - 1), ry):
        for dx in range(-(rx - 1), rx):
            if dx * dx * (ry - 1) ** 2 + dy * dy * (rx - 1) ** 2 <= (rx - 1) ** 2 * (ry - 1) ** 2:
                px_clr_off(cx + dx, cy + dy)
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            if dx * dx * ry * ry + dy * dy * rx * rx > rx * rx * ry * ry:
                continue
            for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = dx + ndx, dy + ndy
                if nx * nx * ry * ry + ny * ny * rx * rx > rx * rx * ry * ry:
                    px_set_off(cx + dx, cy + dy)
                    break


def draw_mouth_slaphappy():
    for x in range(22, 49):
        t = (x - 22) / 26.0
        base = 38 + ((x - 35) * (x - 35)) // 20
        wobble = int(1.5 * math.sin(t * math.pi * 4.0))
        y = base + wobble
        px_set_off(x, y)
        px_set_off(x, y + 1)


def draw_mouth_lazy():
    for x in range(29, 42):
        px_set_off(x, 40)
        px_set_off(x, 41)


def draw_mouth_fat():
    for x in range(24, 47):
        cy = 38 + ((x - 35) * (x - 35)) // 18
        px_set_off(x, cy)
        px_set_off(x, cy + 1)
    cheeks = [(23, 39), (47, 39)]
    for cx, cy in cheeks:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    px_set_off(cx + dx, cy + dy)


def draw_mouth_chill():
    for x in range(29, 44):
        t = (x - 29) / 14.0
        y = 40 + int(1.5 * t * t)
        px_set_off(x, y)
        px_set_off(x, y + 1)


def draw_mouth_creepy():
    cx, cy, rx, ry = 35, 39, 8, 5
    for dy in range(0, ry + 1):
        for dx in range(-rx, rx + 1):
            inside = dx * dx * ry * ry + dy * dy * rx * rx <= rx * rx * ry * ry
            if not inside:
                continue
            edge = 0
            if dy == 0:
                edge = 1
            else:
                for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = dx + ndx, dy + ndy
                    if ny < 0:
                        continue
                    if nx * nx * ry * ry + ny * ny * rx * rx > rx * rx * ry * ry:
                        edge = 1
                        break
            if edge:
                px_set_off(cx + dx, cy + dy)
            else:
                px_clr_off(cx + dx, cy + dy)
    # Tongue
    for dy in range(1, 5):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 8:
                px_set_off(cx + dx, cy + ry + dy)
    for dy in range(2, 4):
        for dx in range(-1, 2):
            px_clr_off(cx + dx, cy + ry + dy)


def draw_mouth_excited():
    for x in range(22, 49):
        cy = 37 + ((x - 35) * (x - 35)) // 12
        px_set_off(x, cy)
        px_set_off(x, cy + 1)


def draw_mouth_nostalgic():
    for x in range(31, 40):
        t = (x - 31) / 8.0
        v = 2.0 * t - 1.0
        y = 40 + int(1.5 * v * v)
        px_set_off(x, y)
        px_set_off(x, y + 1)


def draw_mouth_homesick():
    for x in range(28, 43):
        t = (x - 28) / 14.0
        y = 40 + int(1.5 * math.sin(t * math.pi * 3.0))
        px_set_off(x, y)
        px_set_off(x, y + 1)


# ── Lazy belly tentacle ──

def draw_belly_tentacle_lazy():
    # White outline
    for i in range(30):
        t = i / 29.0
        x = 15 + int(t * 42)
        wave = 2.0 * math.sin(t * math.pi * 1.5)
        y = int(30 + t * 8 + wave)
        for dy in range(-2, 3):
            for dx in range(-1, 2):
                px_clr_off(x + dx, y + dy)
    # Black stroke
    for i in range(30):
        t = i / 29.0
        x = 15 + int(t * 42)
        wave = 2.0 * math.sin(t * math.pi * 1.5)
        y = int(30 + t * 8 + wave)
        for dy in range(-1, 2):
            px_set_off(x, y + dy)
        px_set_off(x + 1, y)
    # Tip curl
    for i in range(6):
        t = i / 5.0
        x = 57 + int(3 * math.sin(t * math.pi))
        y = 38 + i
        px_set_off(x, y)
        px_set_off(x + 1, y)


# ── Chat bubble ──

def draw_bubble():
    bx, by, bw, bh = 75, 5 + Y_OFF, 170, 70
    # Top/bottom edges (double thick)
    for x in range(bx + 3, bx + bw - 3):
        px_set(x, by)
        px_set(x, by + 1)
        px_set(x, by + bh - 1)
        px_set(x, by + bh - 2)
    # Left/right edges
    for y in range(by + 3, by + bh - 3):
        px_set(bx, y)
        px_set(bx + 1, y)
        px_set(bx + bw - 1, y)
        px_set(bx + bw - 2, y)
    # Rounded corners
    corners = [(bx + 2, by + 2), (bx + bw - 3, by + 2),
               (bx + 2, by + bh - 3), (bx + bw - 3, by + bh - 3)]
    for cx, cy in corners:
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if abs(dx) + abs(dy) <= 1:
                    px_set(cx + dx, cy + dy)
    # Speech tail
    tb = 35 + Y_OFF
    tail_dx = [0, -1, -2, -3, -4, -5, -6, -7, -6, -5, -4, -3, -2, -1, 0]
    tail_dy = [0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 7, 6, 5, 4]
    for i in range(15):
        px_set(bx + tail_dx[i], tb + tail_dy[i])


# ── Mood → draw functions mapping ──

MOOD_CONFIG = {
    "normal":       {"body": BODY_RLE_STANDARD, "pupils": draw_pupils_normal, "mouth": draw_mouth_smirk,
                     "brows": None, "lids": None, "special_eyes": None, "tears": None, "belly": None},
    "weird":        {"body": BODY_RLE_STANDARD, "pupils": draw_pupils_weird, "mouth": draw_mouth_weird,
                     "brows": None, "lids": None, "special_eyes": None, "tears": None, "belly": None},
    "unhinged":     {"body": BODY_RLE_STANDARD, "pupils": draw_pupils_unhinged, "mouth": draw_mouth_unhinged,
                     "brows": None, "lids": None, "special_eyes": None, "tears": None, "belly": None},
    "angry":        {"body": BODY_RLE_STANDARD, "pupils": draw_pupils_angry, "mouth": draw_mouth_angry,
                     "brows": draw_brows_angry, "lids": None, "special_eyes": None, "tears": None, "belly": None},
    "sad":          {"body": BODY_RLE_STANDARD, "pupils": draw_pupils_sad, "mouth": draw_mouth_sad,
                     "brows": draw_brows_sad, "lids": None, "special_eyes": None, "tears": None, "belly": None},
    "chaotic":      {"body": BODY_RLE_STANDARD, "pupils": draw_pupils_chaotic, "mouth": draw_mouth_chaotic,
                     "brows": None, "lids": None, "special_eyes": None, "tears": None, "belly": None},
    "hungry":       {"body": BODY_RLE_STANDARD, "pupils": draw_pupils_hungry, "mouth": draw_mouth_hungry,
                     "brows": None, "lids": None, "special_eyes": None, "tears": None, "belly": None},
    "tired":        {"body": BODY_RLE_STANDARD, "pupils": draw_pupils_tired, "mouth": draw_mouth_tired,
                     "brows": None, "lids": draw_lids_tired, "special_eyes": None, "tears": None, "belly": None},
    "slaphappy":    {"body": BODY_RLE_STANDARD, "pupils": None, "mouth": draw_mouth_slaphappy,
                     "brows": None, "lids": None, "special_eyes": draw_eyes_slaphappy, "tears": None, "belly": None},
    "lazy":         {"body": BODY_RLE_LAZY, "pupils": draw_pupils_lazy, "mouth": draw_mouth_lazy,
                     "brows": None, "lids": draw_lids_lazy, "special_eyes": None, "tears": None, "belly": None},
    "fat":          {"body": BODY_RLE_FAT, "pupils": draw_pupils_fat, "mouth": draw_mouth_fat,
                     "brows": None, "lids": None, "special_eyes": None, "tears": None, "belly": None},
    "chill":        {"body": BODY_RLE_STANDARD, "pupils": draw_pupils_chill, "mouth": draw_mouth_chill,
                     "brows": None, "lids": None, "special_eyes": None, "tears": None, "belly": None},
    "creepy":        {"body": BODY_RLE_STANDARD, "pupils": draw_pupils_creepy, "mouth": draw_mouth_creepy,
                     "brows": None, "lids": None, "special_eyes": None, "tears": None, "belly": None},
    "excited":      {"body": BODY_RLE_STANDARD, "pupils": draw_pupils_excited, "mouth": draw_mouth_excited,
                     "brows": None, "lids": None, "special_eyes": None, "tears": None, "belly": None},
    "nostalgic":    {"body": BODY_RLE_STANDARD, "pupils": draw_pupils_nostalgic, "mouth": draw_mouth_nostalgic,
                     "brows": None, "lids": None, "special_eyes": None, "tears": None, "belly": None},
    "homesick":     {"body": BODY_RLE_STANDARD, "pupils": draw_pupils_homesick, "mouth": draw_mouth_homesick,
                     "brows": None, "lids": None, "special_eyes": None, "tears": draw_tears_homesick, "belly": None},
}


def render_mood(mood_name, frame_idx=0):
    """Render a single mood frame following the exact C composition pipeline."""
    cfg = MOOD_CONFIG[mood_name]
    clear_frame()

    # Apply body transform (matches C setup_body_transform)
    setup_body_transform(mood_name, frame_idx)

    # 1. Body
    draw_body(cfg["body"])

    # 2. White eye sockets
    draw_eyes()

    # 3. Pupils
    if cfg["pupils"]:
        cfg["pupils"]()

    # 3b. Brows / lids / special eyes
    if cfg["brows"]:
        cfg["brows"]()
    if cfg["lids"]:
        cfg["lids"]()
    if cfg["special_eyes"]:
        cfg["special_eyes"]()
    if cfg["tears"]:
        cfg["tears"]()

    # 4. Mouth
    cfg["mouth"]()

    # 4b. Belly tentacle (lazy only)
    if cfg["belly"]:
        cfg["belly"]()

    # 5. Chat bubble (empty — no text for preview)
    draw_bubble()


def frame_to_image(scale=4):
    """Convert current frame buffer to a Pillow Image, scaled up."""
    img = Image.new("1", (IMG_W, IMG_H), color=1)  # 1 = white
    pixels = img.load()
    for y in range(IMG_H):
        for x in range(IMG_W):
            if frame[y][x]:
                pixels[x, y] = 0  # 0 = black in mode "1"
    if scale > 1:
        img = img.resize((IMG_W * scale, IMG_H * scale), Image.NEAREST)
    return img


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "c-render")
    os.makedirs(out_dir, exist_ok=True)

    scale = 4
    moods = list(MOOD_CONFIG.keys())

    for mood in moods:
        render_mood(mood)
        img = frame_to_image(scale=scale)
        path = os.path.join(out_dir, f"{mood}.png")
        img.save(path)
        print(f"  {mood:12s} -> {path}")

    # Also generate a comparison grid — all moods side by side
    cell_w, cell_h = IMG_W * scale, IMG_H * scale
    cols = 4
    rows_needed = (len(moods) + cols - 1) // cols
    grid = Image.new("1", (cell_w * cols, cell_h * rows_needed), color=1)

    for i, mood in enumerate(moods):
        render_mood(mood)
        cell = frame_to_image(scale=scale)
        col, row = i % cols, i // cols
        grid.paste(cell, (col * cell_w, row * cell_h))

    grid_path = os.path.join(out_dir, "_grid_all_moods.png")
    grid.save(grid_path)
    print(f"\n  Grid -> {grid_path}")
    print(f"\nDone — {len(moods)} moods rendered to {out_dir}/")


if __name__ == "__main__":
    main()
