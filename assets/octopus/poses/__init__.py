"""Pose system — shared poses + unique-per-emotion poses.

    from octopus.poses import ALL_POSES, get_pose
    pose = get_pose("sitting")          # shared pose
    pose = get_pose("angry_stomp")      # unique pose

Each pose provides:
  - body_rle: RLE data (or None to use the emotion's default)
  - face_anchor: (x, y) offset for face drawing relative to standard
  - tentacle_config: description of tentacle arrangement
  - override_lids: if True, force eyes closed (sleeping pose)
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PoseConfig:
    """Definition of a character pose."""
    name: str
    category: str                          # "shared" or "unique"
    emotion: Optional[str] = None          # only for unique poses
    body_rle: Optional[list] = None        # None = use emotion default
    face_anchor_offset: tuple = (0, 0)     # (dx, dy) from standard face pos
    force_eyes_closed: bool = False        # override for sleeping
    description: str = ""


# Combined registry — populated by shared/ and unique/ subpackages
REGISTRY: dict[str, PoseConfig] = {}


def get_pose(name: str) -> PoseConfig:
    """Look up a pose by name, raising KeyError if not found."""
    return REGISTRY[name]


def poses_for_emotion(emotion: str) -> list[str]:
    """Return all pose keys available to a given emotion.

    Every emotion gets all shared poses plus its own unique pose.
    """
    shared = [k for k, v in REGISTRY.items() if v.category == "shared"]
    unique = [k for k, v in REGISTRY.items()
              if v.category == "unique" and v.emotion == emotion]
    return shared + unique


# Import subpackages to trigger registration
from . import shared, unique  # noqa: E402, F401
