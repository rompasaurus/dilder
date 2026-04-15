"""Per-emotion body transforms.

Exact port of C setup_body_transform(). Each function receives a frame_idx
and sets the canvas body-transform globals accordingly.
"""

import math
from ..core import canvas


def transform_normal(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(dy=int(math.sin(f * 0.8)))


def transform_weird(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(
        dx=int(3 * math.sin(f * 0.8)),
        w_amp=1.5, w_freq=0.15, w_phase=f,
    )


def transform_unhinged(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(
        dx=int(1.5 * math.sin(f * 7.3)),
        dy=int(1.5 * math.sin(f * 5.1 + 1)),
    )


def transform_angry(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(
        dy=-1, x_expand=2,
        w_amp=0.5, w_freq=0.3, w_phase=f,
    )


def transform_sad(frame_idx):
    canvas.set_body_transform(dy=3, x_expand=-1)


def transform_chaotic(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(
        dx=int(2 * math.sin(f * 2.1)),
        dy=int(2 * math.sin(f * 1.7)),
        w_amp=3, w_freq=0.25, w_phase=f * 2.0,
    )


def transform_hungry(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(dy=-2 + int(math.sin(f * 1.5)))


def transform_tired(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(
        dy=2 + int(math.sin(f * 0.5)),
        x_expand=-1,
    )


def transform_slaphappy(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(
        dx=int(3 * math.sin(f * 1.2)),
        w_amp=2, w_freq=0.1, w_phase=f * 1.2,
    )


def transform_lazy(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(
        dy=int(0.5 * math.sin(f * 0.3)),
        dx=int(0.5 * math.sin(f * 0.15)),
    )


def transform_fat(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(dy=int(1.5 * math.sin(f * 1.8)))


def transform_chill(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(dx=int(math.sin(f * 0.4)), dy=1)


def transform_horny(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(x_expand=int(2 * math.sin(f * 2.0)))


def transform_excited(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(dy=int(3 * math.sin(f * 3.0)))


def transform_nostalgic(frame_idx):
    f = frame_idx * math.pi / 2.0
    canvas.set_body_transform(
        dx=int(2 * math.sin(f * 0.5)),
        dy=int(math.sin(f * 0.3)),
    )


def transform_homesick(frame_idx):
    canvas.set_body_transform(dy=1, x_expand=-2)


# Registry: emotion name -> transform function
REGISTRY = {
    "normal": transform_normal,
    "weird": transform_weird,
    "unhinged": transform_unhinged,
    "angry": transform_angry,
    "sad": transform_sad,
    "chaotic": transform_chaotic,
    "hungry": transform_hungry,
    "tired": transform_tired,
    "slaphappy": transform_slaphappy,
    "lazy": transform_lazy,
    "fat": transform_fat,
    "chill": transform_chill,
    "horny": transform_horny,
    "excited": transform_excited,
    "nostalgic": transform_nostalgic,
    "homesick": transform_homesick,
}
