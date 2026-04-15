"""Jamal the Octopus - Modular Asset System

Directory tree designed for programmatic traversal:

    octopus/
    +-- core/           Canvas, drawing primitives, body RLE data
    +-- emotions/       16 emotion states (faces, transforms, aura defs)
    +-- poses/
    |   +-- shared/     6 poses available to every emotion
    |   +-- unique/     16 poses, one exclusive per emotion
    +-- environments/   10 background scenes
    +-- decor/          Props: furniture, food, weather, plants, electronics
    +-- outfits/        Wearables: headwear, eyewear, bodywear, accessories
    +-- aura/           Emotion Echo particle system
    +-- compose.py      Scene compositor (layers everything together)
    +-- render_all.py   Batch renderer

Every category exposes a REGISTRY dict mapping string keys to draw
callables, so the tree can be walked with:

    from octopus.emotions import REGISTRY as EMOTIONS
    from octopus.poses.shared import REGISTRY as SHARED_POSES
    from octopus.environments import REGISTRY as ENVIRONMENTS
"""

__version__ = "0.1.0"
