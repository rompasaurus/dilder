"""Emotion state registry.

Each emotion is an EmotionConfig dataclass holding references to all
draw callables needed to render that emotion's face and body transform.

    from octopus.emotions import REGISTRY
    cfg = REGISTRY["angry"]
    cfg.setup_transform(frame_idx=2)
    cfg.draw_pupils()
    cfg.draw_mouth()
"""

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class EmotionConfig:
    """Everything needed to render one emotion state."""
    name: str
    body_key: str                          # "standard", "fat", or "lazy"
    draw_pupils: Optional[Callable]        # pupils draw function
    draw_mouth: Callable                   # mouth draw function
    draw_brows: Optional[Callable] = None
    draw_lids: Optional[Callable] = None
    draw_special_eyes: Optional[Callable] = None
    draw_tears: Optional[Callable] = None
    draw_belly: Optional[Callable] = None
    setup_transform: Optional[Callable] = None  # (frame_idx) -> sets body globals
    unique_pose: Optional[str] = None      # key into poses.unique.REGISTRY
    aura_key: Optional[str] = None         # key into aura.REGISTRY
    mouth_cycle: tuple = field(default_factory=lambda: (0, 1, 2, 1))


# Keys for all 16 emotions — functions wired in faces.py and transforms.py
EMOTION_NAMES = [
    "normal", "weird", "unhinged", "angry", "sad", "chaotic",
    "hungry", "tired", "slaphappy", "lazy", "fat", "chill",
    "horny", "excited", "nostalgic", "homesick",
]

# REGISTRY is populated by faces.py on import
REGISTRY: dict[str, EmotionConfig] = {}

# Import faces to trigger registry population
from . import faces  # noqa: E402, F401
