"""Environment background scenes.

Each environment is a draw function that renders background elements
into the frame buffer BEFORE the character is drawn.

    from octopus.environments import REGISTRY
    draw_fn = REGISTRY["bedroom"]
    draw_fn(frame_idx=0)

Environments avoid the chat-bubble region (x=75..245, y=17..87) and
place ground/floor elements near the bottom of the 250x122 canvas.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class EnvironmentConfig:
    name: str
    draw_bg: Callable           # (frame_idx: int) -> None
    ground_y: int = 100         # y-coordinate of ground/floor line
    has_weather: bool = False   # whether emotion modulation can add weather
    description: str = ""
    decor_slots: list = field(default_factory=list)  # [(x, y)] positions for decor


# Populated by individual environment modules — import them to register
REGISTRY: dict[str, EnvironmentConfig] = {}


def register(name: str, **kwargs):
    """Decorator to register an environment draw function."""
    def decorator(fn):
        REGISTRY[name] = EnvironmentConfig(name=name, draw_bg=fn, **kwargs)
        return fn
    return decorator


# Import environment modules to trigger registration
from . import (  # noqa: E402, F401
    bedroom, kitchen, living_room, park, beach,
    space, underwater, office, rooftop, arcade,
    forest, mountain, desert, garden, gym,
    snow_field, rainstorm, city_street, sunset,
    cafe, library, bathroom, haunted_house,
)
