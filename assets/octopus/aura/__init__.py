"""Emotion Echo — the aura particle system.

Each emotion has a set of 3-5 small pixel clusters that orbit/float
around the character. These are ALWAYS drawn regardless of pose,
environment, or outfit, making emotion readable in any configuration.

The three-layer emotion encoding:
  Layer 1: Face (eyes + mouth) — always drawn last
  Layer 2: Aura particles — THIS MODULE — persistent signature
  Layer 3: Environment modulation — handled by compose.py

Aura particles are positioned relative to a center anchor (cx, cy)
that tracks the character's body center across poses.

    from octopus.aura import REGISTRY
    draw_aura = REGISTRY["angry"]
    draw_aura(cx=35, cy=45, frame_idx=2)
"""

from typing import Callable

REGISTRY: dict[str, Callable] = {}


def register(emotion: str):
    """Decorator to register an aura draw function for an emotion."""
    def decorator(fn):
        REGISTRY[emotion] = fn
        return fn
    return decorator


# Import particles module to populate registry
from . import particles  # noqa: E402, F401
