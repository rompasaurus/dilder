"""Outfit overlay system.

Outfits are drawn AFTER the body but BEFORE the face. They attach to
anchor points that shift with the current pose.

    from octopus.outfits import REGISTRY
    draw_fn = REGISTRY["top_hat"]
    draw_fn(dome_top=(35, 10), eye_centers=((22, 25), (48, 25)))

Anchor points provided to each draw function:
  - dome_top: (x, y) of the top-center of the dome
  - eye_centers: ((lx, ly), (rx, ry)) left and right eye socket centers
  - neck: (x, y) where dome meets body
  - body_center: (x, y) center of body mass
"""

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class OutfitConfig:
    name: str
    category: str       # "headwear", "eyewear", "bodywear", "accessories"
    draw: Callable      # (dome_top, eye_centers, neck, body_center) -> None
    description: str = ""


REGISTRY: dict[str, OutfitConfig] = {}


def register(name: str, category: str, description: str = ""):
    """Decorator to register an outfit draw function."""
    def decorator(fn):
        REGISTRY[name] = OutfitConfig(
            name=name, category=category, draw=fn, description=description,
        )
        return fn
    return decorator


# Standard anchor points (for standing pose with standard body)
DEFAULT_ANCHORS = {
    "dome_top": (35, 10),
    "eye_centers": ((22, 25), (48, 25)),
    "neck": (35, 45),
    "body_center": (35, 35),
}

# Import outfit modules to trigger registration
from . import (  # noqa: E402, F401
    headwear, eyewear, bodywear, accessories,
    holiday_headwear, costume_headgear, special_bodywear,
)
