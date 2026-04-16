"""Unique poses — one exclusive pose per emotion state.

Each pose is only available when the matching emotion is active.
Registers into both the local REGISTRY and the parent REGISTRY.
"""

from .. import PoseConfig, REGISTRY as _PARENT_REGISTRY

# Local registry for unique poses only
REGISTRY: dict[str, PoseConfig] = {}


def _reg(key, cfg):
    REGISTRY[key] = cfg
    _PARENT_REGISTRY[key] = cfg


_UNIQUE_POSES = [
    ("hands_on_hips",   "normal",    (0, 0),   "2 tentacles akimbo on body sides, confident wide stance"),
    ("chin_stroke",     "weird",     (2, 0),   "1 tentacle curled under dome thinking, body leaning to one side"),
    ("tentacle_splay",  "unhinged",  (0, 0),   "All 5 tentacles splayed outward max width, body vibrating"),
    ("ground_stomp",    "angry",     (0, -2),  "2 tentacles raised as fists, 3 stomping with thick tips"),
    ("self_hug",        "sad",       (0, 3),   "Tentacles wrapped around own body, dome slightly deflated"),
    ("tornado_spin",    "chaotic",   (0, 0),   "Tentacles spiraling outward in rotation, body blurred with wobble"),
    ("food_reach",      "hungry",    (3, -4),  "2 tentacles reaching upward/forward, body leaning toward food"),
    ("face_plant",      "tired",     (0, 25),  "Body toppled forward, dome on ground, tentacles splayed behind"),
    ("knee_slap",       "slaphappy", (-2, 0),  "1 tentacle curled up slapping body side, tilted back laughing"),
    ("melted_puddle",   "lazy",      (0, 30),  "Body completely flattened, dome barely raised, tentacles pooled"),
    ("belly_rub",       "fat",       (0, -2),  "2 tentacles on belly, body leaned back satisfied"),
    ("wall_lean",       "chill",     (-5, 2),  "Body at angle against invisible wall, tentacles crossed in front"),
    ("peacock_strut",   "creepy",     (0, -1),  "Body puffed out, tentacles in walking motion, exaggerated posture"),
    ("victory_jump",    "excited",   (0, -8),  "Body 5px above ground, all tentacles raised up and spread wide"),
    ("photo_gaze",      "nostalgic", (2, 0),   "1 tentacle holding tiny rectangle photo, body slightly turned"),
    ("globe_hold",      "homesick",  (0, 3),   "2 tentacles cradling small circle globe, body hunched protectively"),
]

for name, emotion, anchor_off, desc in _UNIQUE_POSES:
    _reg(name, PoseConfig(
        name=name,
        category="unique",
        emotion=emotion,
        face_anchor_offset=anchor_off,
        description=desc,
    ))
