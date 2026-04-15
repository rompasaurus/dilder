"""Decor props — small pixel-art elements placed within environments.

Each prop is a standalone draw function that renders at a given (x, y).

    from octopus.decor import REGISTRY
    draw_fn = REGISTRY["pizza"]
    draw_fn(x=50, y=90)

Categories: furniture, food, weather, plants, electronics
"""

from dataclasses import dataclass
from typing import Callable


@dataclass
class PropConfig:
    name: str
    category: str
    draw: Callable      # (x: int, y: int) -> None
    width: int          # approximate bounding box
    height: int
    description: str = ""


REGISTRY: dict[str, PropConfig] = {}


def register(name: str, category: str, width: int, height: int, description: str = ""):
    """Decorator to register a prop draw function."""
    def decorator(fn):
        REGISTRY[name] = PropConfig(
            name=name, category=category, draw=fn,
            width=width, height=height, description=description,
        )
        return fn
    return decorator


# Import decor modules to trigger registration
from . import furniture, food, weather, plants, electronics  # noqa: E402, F401
