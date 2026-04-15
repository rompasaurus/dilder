"""All face-component draw functions: pupils, mouths, brows, lids, tears.

Exact port from render_c_previews.py. Each function draws into the
module-level frame buffer via canvas pixel operations.

Also wires up the emotion REGISTRY with EmotionConfig instances.
"""

import math
from ..core import canvas
from ..core.drawing import fill_circle
from . import EmotionConfig, REGISTRY
from .transforms import REGISTRY as TRANSFORM_REGISTRY


# ── Eyes (shared across all emotions) ──

def draw_eyes():
    """White eye sockets — always drawn."""
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
        canvas.px_set_off(x, y)

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
                    canvas.px_set_off(ecx + dx, 25 + dy)
        canvas.px_set_off(ecx, 25)

def draw_pupils_hungry():
    fill_circle(23, 23, 4, 1)
    fill_circle(49, 23, 4, 1)
    fill_circle(21, 21, 1, 0)
    fill_circle(47, 21, 1, 0)

def draw_pupils_tired():
    for dx in range(-1, 2):
        canvas.px_set_off(22 + dx, 27)
        canvas.px_set_off(22 + dx, 28)
        canvas.px_set_off(48 + dx, 27)
        canvas.px_set_off(48 + dx, 28)

def draw_pupils_lazy():
    for ecx in [22, 48]:
        canvas.px_set_off(ecx, 28)
        canvas.px_set_off(ecx + 1, 28)

def draw_pupils_fat():
    for ecx in [23, 49]:
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if dx * dx + dy * dy <= 9:
                    canvas.px_set_off(ecx + dx, 26 + dy)

def draw_pupils_chill():
    for ecx, ecy in [(25, 26), (51, 26)]:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    canvas.px_set_off(ecx + dx, ecy + dy)

def draw_pupils_horny():
    for ecx in [22, 48]:
        for dx, dy in [(-2, -1), (-1, -2), (0, -1), (1, -2), (2, -1)]:
            canvas.px_set_off(ecx + dx, 25 + dy)
        for dx in range(-2, 3):
            canvas.px_set_off(ecx + dx, 25)
        for dx in range(-1, 2):
            canvas.px_set_off(ecx + dx, 26)
        canvas.px_set_off(ecx, 27)

def draw_pupils_excited():
    for ecx in [22, 48]:
        for d in range(-2, 3):
            canvas.px_set_off(ecx + d, 25)
            canvas.px_set_off(ecx, 25 + d)
        canvas.px_set_off(ecx - 1, 24)
        canvas.px_set_off(ecx + 1, 24)
        canvas.px_set_off(ecx - 1, 26)
        canvas.px_set_off(ecx + 1, 26)

def draw_pupils_nostalgic():
    for ecx, ecy in [(24, 23), (50, 23)]:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    canvas.px_set_off(ecx + dx, ecy + dy)

def draw_pupils_homesick():
    for ecx in [23, 49]:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    canvas.px_set_off(ecx + dx, 27 + dy)


# ── Brows / Lids / Special eyes ──

def draw_brows_angry():
    for i in range(18):
        t = i / 17.0
        x = 14 + int(t * 16)
        arc = 2.5 * math.sin(t * math.pi)
        y = int(20 + t * 5 - arc)
        for dy in range(3):
            canvas.px_set_off(x, y + dy)
        canvas.px_set_off(x + 1, y + 1)
    for i in range(18):
        t = i / 17.0
        x = 40 + int(t * 16)
        arc = 2.5 * math.sin(t * math.pi)
        y = int(25 - t * 5 - arc)
        for dy in range(3):
            canvas.px_set_off(x, y + dy)
        canvas.px_set_off(x + 1, y + 1)

def draw_brows_sad():
    for i in range(18):
        t = i / 17.0
        x = 14 + int(t * 16)
        arc = 2.5 * math.sin(t * math.pi)
        y = int(25 - t * 5 - arc)
        for dy in range(3):
            canvas.px_set_off(x, y + dy)
    for i in range(18):
        t = i / 17.0
        x = 40 + int(t * 16)
        arc = 2.5 * math.sin(t * math.pi)
        y = int(20 + t * 5 - arc)
        for dy in range(3):
            canvas.px_set_off(x, y + dy)

def draw_lids_tired():
    for ecx in [22, 48]:
        for dy in range(-4, -1):
            for dx in range(-4, 5):
                if dx * dx + dy * dy <= 16:
                    canvas.px_set_off(ecx + dx, 25 + dy)

def draw_eyes_slaphappy():
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if dx * dx + dy * dy <= 16:
                canvas.px_set_off(22 + dx, 25 + dy)
    for dx in range(-3, 4):
        canvas.px_clr_off(22 + dx, 25)
    fill_circle(49, 26, 9, 1)

def draw_lids_lazy():
    for ecx in [22, 48]:
        for dy in range(-4, 2):
            for dx in range(-4, 5):
                if dx * dx + dy * dy <= 16:
                    canvas.px_set_off(ecx + dx, 25 + dy)

def draw_tears_homesick():
    for ecx in [22, 48]:
        canvas.px_set_off(ecx, 31)
        canvas.px_set_off(ecx, 32)
        canvas.px_set_off(ecx, 33)
        canvas.px_set_off(ecx - 1, 32)
        canvas.px_set_off(ecx + 1, 32)


# ── Mouths ──

def draw_mouth_smirk():
    for x in range(28, 44):
        t = (x - 28) / 15.0
        tilt = -2.0 + t * 4.0
        v = 2.0 * t - 1.0
        arc = 5.0 * math.sqrt(1.0 - v * v) if abs(v) < 1.0 else 0.0
        yc = int(39.0 + tilt + arc)
        canvas.px_clr_off(x, yc)
        canvas.px_set_off(x, yc - 1)
        canvas.px_set_off(x, yc + 1)

def draw_mouth_smile():
    for x in range(26, 45):
        cy = 38 + ((x - 35) * (x - 35)) // 25
        canvas.px_set_off(x, cy)
        canvas.px_set_off(x, cy + 1)

def draw_mouth_open():
    cx, cy, rx, ry = 35, 40, 7, 5
    for dy in range(-4, 5):
        for dx in range(-6, 7):
            if dx * dx * 16 + dy * dy * 36 <= 36 * 16:
                canvas.px_clr_off(cx + dx, cy + dy)
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            if dx * dx * ry * ry + dy * dy * rx * rx > rx * rx * ry * ry:
                continue
            for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = dx + ndx, dy + ndy
                if nx * nx * ry * ry + ny * ny * rx * rx > rx * rx * ry * ry:
                    canvas.px_set_off(cx + dx, cy + dy)
                    break

def draw_mouth_weird():
    for x in range(24, 48):
        t = (x - 24) / 23.0
        yc = 39 + int(3.5 * math.sin(t * math.pi * 3.0))
        canvas.px_clr_off(x, yc)
        canvas.px_set_off(x, yc - 1)
        canvas.px_set_off(x, yc + 1)

def draw_mouth_unhinged():
    cx, cy, rx, ry = 35, 41, 10, 7
    for dy in range(-6, 7):
        for dx in range(-9, 10):
            if dx * dx * 36 + dy * dy * 81 <= 81 * 36:
                canvas.px_clr_off(cx + dx, cy + dy)
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            if dx * dx * ry * ry + dy * dy * rx * rx > rx * rx * ry * ry:
                continue
            for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = dx + ndx, dy + ndy
                if nx * nx * ry * ry + ny * ny * rx * rx > rx * rx * ry * ry:
                    canvas.px_set_off(cx + dx, cy + dy)
                    break
    for x in range(cx - 7, cx + 8, 3):
        canvas.px_set_off(x, cy - 5)
        canvas.px_set_off(x, cy - 4)
        canvas.px_set_off(x + 1, cy - 4)

def draw_mouth_angry():
    for x in range(28, 43):
        cy = 40 - ((x - 35) * (x - 35)) // 20
        canvas.px_set_off(x, cy)
        canvas.px_set_off(x, cy + 1)

def draw_mouth_sad():
    for x in range(26, 45):
        cy = 42 - ((x - 35) * (x - 35)) // 30
        canvas.px_set_off(x, cy)
        canvas.px_set_off(x, cy + 1)

def draw_mouth_chaotic():
    for x in range(24, 48):
        phase = (x - 24) % 6
        y = (38 + phase * 2) if phase < 3 else (44 - phase * 2 + 6)
        canvas.px_set_off(x, y)
        canvas.px_set_off(x, y + 1)

def draw_mouth_hungry():
    cx, cy, rx, ry = 35, 40, 8, 5
    for dy in range(-(ry - 1), ry):
        for dx in range(-(rx - 1), rx):
            if dx * dx * (ry - 1)**2 + dy * dy * (rx - 1)**2 <= (rx - 1)**2 * (ry - 1)**2:
                canvas.px_clr_off(cx + dx, cy + dy)
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            if dx * dx * ry * ry + dy * dy * rx * rx > rx * rx * ry * ry:
                continue
            for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = dx + ndx, dy + ndy
                if nx * nx * ry * ry + ny * ny * rx * rx > rx * rx * ry * ry:
                    canvas.px_set_off(cx + dx, cy + dy)
                    break
    for dy in range(1, 6):
        canvas.px_set_off(33, cy + ry + dy)
    for dy in range(1, 4):
        canvas.px_set_off(37, cy + ry + dy + 1)

def draw_mouth_tired():
    cx, cy, rx, ry = 35, 40, 5, 7
    for dy in range(-(ry - 1), ry):
        for dx in range(-(rx - 1), rx):
            if dx * dx * (ry - 1)**2 + dy * dy * (rx - 1)**2 <= (rx - 1)**2 * (ry - 1)**2:
                canvas.px_clr_off(cx + dx, cy + dy)
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            if dx * dx * ry * ry + dy * dy * rx * rx > rx * rx * ry * ry:
                continue
            for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = dx + ndx, dy + ndy
                if nx * nx * ry * ry + ny * ny * rx * rx > rx * rx * ry * ry:
                    canvas.px_set_off(cx + dx, cy + dy)
                    break

def draw_mouth_slaphappy():
    for x in range(22, 49):
        t = (x - 22) / 26.0
        base = 38 + ((x - 35) * (x - 35)) // 20
        wobble = int(1.5 * math.sin(t * math.pi * 4.0))
        y = base + wobble
        canvas.px_set_off(x, y)
        canvas.px_set_off(x, y + 1)

def draw_mouth_lazy():
    for x in range(29, 42):
        canvas.px_set_off(x, 40)
        canvas.px_set_off(x, 41)

def draw_mouth_fat():
    for x in range(24, 47):
        cy = 38 + ((x - 35) * (x - 35)) // 18
        canvas.px_set_off(x, cy)
        canvas.px_set_off(x, cy + 1)
    for cx, cy in [(23, 39), (47, 39)]:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    canvas.px_set_off(cx + dx, cy + dy)

def draw_mouth_chill():
    for x in range(29, 44):
        t = (x - 29) / 14.0
        y = 40 + int(1.5 * t * t)
        canvas.px_set_off(x, y)
        canvas.px_set_off(x, y + 1)

def draw_mouth_horny():
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
                canvas.px_set_off(cx + dx, cy + dy)
            else:
                canvas.px_clr_off(cx + dx, cy + dy)
    for dy in range(1, 5):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 8:
                canvas.px_set_off(cx + dx, cy + ry + dy)
    for dy in range(2, 4):
        for dx in range(-1, 2):
            canvas.px_clr_off(cx + dx, cy + ry + dy)

def draw_mouth_excited():
    for x in range(22, 49):
        cy = 37 + ((x - 35) * (x - 35)) // 12
        canvas.px_set_off(x, cy)
        canvas.px_set_off(x, cy + 1)

def draw_mouth_nostalgic():
    for x in range(31, 40):
        t = (x - 31) / 8.0
        v = 2.0 * t - 1.0
        y = 40 + int(1.5 * v * v)
        canvas.px_set_off(x, y)
        canvas.px_set_off(x, y + 1)

def draw_mouth_homesick():
    for x in range(28, 43):
        t = (x - 28) / 14.0
        y = 40 + int(1.5 * math.sin(t * math.pi * 3.0))
        canvas.px_set_off(x, y)
        canvas.px_set_off(x, y + 1)


# ── Lazy belly tentacle ──

def draw_belly_tentacle_lazy():
    for i in range(30):
        t = i / 29.0
        x = 15 + int(t * 42)
        wave = 2.0 * math.sin(t * math.pi * 1.5)
        y = int(30 + t * 8 + wave)
        for dy in range(-2, 3):
            for dx in range(-1, 2):
                canvas.px_clr_off(x + dx, y + dy)
    for i in range(30):
        t = i / 29.0
        x = 15 + int(t * 42)
        wave = 2.0 * math.sin(t * math.pi * 1.5)
        y = int(30 + t * 8 + wave)
        for dy in range(-1, 2):
            canvas.px_set_off(x, y + dy)
        canvas.px_set_off(x + 1, y)
    for i in range(6):
        t = i / 5.0
        x = 57 + int(3 * math.sin(t * math.pi))
        y = 38 + i
        canvas.px_set_off(x, y)
        canvas.px_set_off(x + 1, y)


# ── Wire up REGISTRY ──

_CONFIGS = {
    "normal":    {"body_key": "standard", "pupils": draw_pupils_normal,    "mouth": draw_mouth_smirk,    "unique_pose": "hands_on_hips"},
    "weird":     {"body_key": "standard", "pupils": draw_pupils_weird,     "mouth": draw_mouth_weird,    "unique_pose": "chin_stroke"},
    "unhinged":  {"body_key": "standard", "pupils": draw_pupils_unhinged,  "mouth": draw_mouth_unhinged, "unique_pose": "tentacle_splay"},
    "angry":     {"body_key": "standard", "pupils": draw_pupils_angry,     "mouth": draw_mouth_angry,    "brows": draw_brows_angry, "unique_pose": "ground_stomp"},
    "sad":       {"body_key": "standard", "pupils": draw_pupils_sad,       "mouth": draw_mouth_sad,      "brows": draw_brows_sad, "unique_pose": "self_hug"},
    "chaotic":   {"body_key": "standard", "pupils": draw_pupils_chaotic,   "mouth": draw_mouth_chaotic,  "unique_pose": "tornado_spin"},
    "hungry":    {"body_key": "standard", "pupils": draw_pupils_hungry,    "mouth": draw_mouth_hungry,   "unique_pose": "food_reach"},
    "tired":     {"body_key": "standard", "pupils": draw_pupils_tired,     "mouth": draw_mouth_tired,    "lids": draw_lids_tired, "unique_pose": "face_plant"},
    "slaphappy": {"body_key": "standard", "pupils": None,                  "mouth": draw_mouth_slaphappy, "special_eyes": draw_eyes_slaphappy, "unique_pose": "knee_slap"},
    "lazy":      {"body_key": "lazy",     "pupils": draw_pupils_lazy,      "mouth": draw_mouth_lazy,     "lids": draw_lids_lazy, "belly": draw_belly_tentacle_lazy, "unique_pose": "melted_puddle"},
    "fat":       {"body_key": "fat",      "pupils": draw_pupils_fat,       "mouth": draw_mouth_fat,      "unique_pose": "belly_rub"},
    "chill":     {"body_key": "standard", "pupils": draw_pupils_chill,     "mouth": draw_mouth_chill,    "unique_pose": "wall_lean"},
    "horny":     {"body_key": "standard", "pupils": draw_pupils_horny,     "mouth": draw_mouth_horny,    "unique_pose": "peacock_strut"},
    "excited":   {"body_key": "standard", "pupils": draw_pupils_excited,   "mouth": draw_mouth_excited,  "unique_pose": "victory_jump"},
    "nostalgic": {"body_key": "standard", "pupils": draw_pupils_nostalgic, "mouth": draw_mouth_nostalgic, "unique_pose": "photo_gaze"},
    "homesick":  {"body_key": "standard", "pupils": draw_pupils_homesick,  "mouth": draw_mouth_homesick, "tears": draw_tears_homesick, "unique_pose": "globe_hold"},
}

for name, cfg in _CONFIGS.items():
    REGISTRY[name] = EmotionConfig(
        name=name,
        body_key=cfg["body_key"],
        draw_pupils=cfg.get("pupils"),
        draw_mouth=cfg["mouth"],
        draw_brows=cfg.get("brows"),
        draw_lids=cfg.get("lids"),
        draw_special_eyes=cfg.get("special_eyes"),
        draw_tears=cfg.get("tears"),
        draw_belly=cfg.get("belly"),
        setup_transform=TRANSFORM_REGISTRY[name],
        unique_pose=cfg.get("unique_pose"),
        aura_key=name,
    )
