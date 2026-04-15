"""Shared poses available to all 16 emotions.

Each pose registers into both the local REGISTRY and the parent REGISTRY.
"""

from .. import PoseConfig, REGISTRY as _PARENT_REGISTRY

# Local registry for shared poses only
REGISTRY: dict[str, PoseConfig] = {}


def _reg(key, cfg):
    REGISTRY[key] = cfg
    _PARENT_REGISTRY[key] = cfg


_reg("standing", PoseConfig(
    name="standing",
    category="shared",
    description="Default upright stance, standard tentacle spread",
))

_reg("sitting", PoseConfig(
    name="sitting",
    category="shared",
    face_anchor_offset=(0, 8),
    description="Body compressed vertically, 3 front tentacles curled under as seat, 2 splayed back",
))

_reg("laying", PoseConfig(
    name="laying",
    category="shared",
    face_anchor_offset=(15, 20),
    description="Body rotated ~80deg on side, dome right, tentacles trailing left",
))

_reg("sleeping", PoseConfig(
    name="sleeping",
    category="shared",
    face_anchor_offset=(5, 15),
    force_eyes_closed=True,
    description="Compact curled ball, tentacles wrapped around body like blanket, eyes forced shut",
))

_reg("sick", PoseConfig(
    name="sick",
    category="shared",
    face_anchor_offset=(0, 2),
    description="Drooping dome 2px narrower, limp hanging tentacles, thermometer near mouth",
))

_reg("nauseous", PoseConfig(
    name="nauseous",
    category="shared",
    face_anchor_offset=(0, -3),
    description="Hunched forward, dome tilted down, 2 tentacles on stomach, 3 bracing ground",
))
