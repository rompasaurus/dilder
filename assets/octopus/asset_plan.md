# Jamal the Octopus - Complete Asset Plan

**Canvas:** 250x122px, 1-bit monochrome | **Character footprint:** ~70x70px (left side) | **Bubble:** 170x70px (right side)

---

## Emotion Retention: The "Emotion Echo" System

The core problem: when Jamal changes pose (standing -> sleeping) or enters a new environment, body transforms are overridden and the face may be partially obscured. We need emotion to remain **instantly readable** in any configuration.

### Three-Layer Emotion Encoding

**Layer 1 - Face Invariance (Primary)**
Eyes and mouth are drawn LAST, composited on top of everything. Even in sleeping pose, emotion-specific markers persist above closed eyelids (angry brows, sad droop arcs). Face draw functions are fully decoupled from body/pose — they receive a face anchor point and draw relative to it.

**Layer 2 - Aura Particles (Novel - Key Innovation)**
Each emotion has 3-5 small pixel clusters (2-4px each) that float around the character. These are ALWAYS drawn regardless of pose, environment, or outfit. They orbit the character's center anchor, animated per-frame via sinusoidal motion.

| Emotion    | Aura Particles                                         |
|------------|--------------------------------------------------------|
| Normal     | Gentle dots drifting outward (calm ripple)             |
| Weird      | Wobbly question marks / tilted dots                    |
| Unhinged   | Rapid flickering random dots (static noise)            |
| Angry      | Sharp zigzag sparks (lightning bolt fragments)         |
| Sad        | Falling tear drops (2px dots trailing downward)        |
| Chaotic    | Spiral dots orbiting wildly (variable speed)           |
| Hungry     | Rising sweat drops + tiny fork/knife pixels            |
| Tired      | Floating Z-letters ascending diagonally                |
| Slap Happy | Bouncing exclamation marks, alternating sides          |
| Lazy       | Slow drifting ellipsis dots (...)                      |
| Fat        | Tiny satisfied sparkles (food crumb dots)              |
| Chill      | Wavy tilde lines drifting sideways (~)                 |
| Horny      | Pulsing heart-shaped pixel clusters                    |
| Excited    | Star bursts (+ shaped, rotating outward)               |
| Nostalgic  | Floating clock/hourglass dots (slow upward drift)      |
| Homesick   | Tiny house silhouette pixels dissolving outward        |

**Layer 3 - Environment Modulation (Ambient)**
The environment subtly reacts to the current emotion. This layer is supplementary, not relied upon for recognition:
- Sad + any outdoor env -> rain drops overlay
- Angry + any -> nearby decor items get 1px vibration offset
- Excited + any -> background elements get subtle bounce
- Tired + any -> decor droops/sags 1-2px
- Chaotic + any -> environment elements get row-wobble distortion
- Chill + any -> ambient wavy heat-shimmer effect

**Why this works on 1-bit e-ink:**
- Aura particles are just 3-8 `px_set` calls per frame — negligible cost
- Particles are recognizable even in silhouette (just outline + particles = emotion readable)
- The system degrades gracefully: face alone works, face+aura is better, face+aura+env is best
- Aura animation drives visual interest when body is static (sleeping, sick)

---

## Poses

### Shared Poses (available to ALL 16 emotions)

| Pose       | Body Description                                                  | Tentacles                                        | Notes                                  |
|------------|-------------------------------------------------------------------|--------------------------------------------------|----------------------------------------|
| Standing   | Default upright (existing BODY_RLE_STANDARD)                      | Standard 5-column spread                         | Current default, already implemented   |
| Sitting    | Body compressed ~15px vertically, lower dome flattened             | 3 front tentacles curled under as "seat", 2 back splayed | Face anchor shifts down 8px           |
| Laying     | Body rotated ~80deg, dome on right side                           | Tentacles trailing left as "tail"                | Face anchor rotates, horizontal layout  |
| Sleeping   | Dome shrunk/curled, body compact ball shape                       | Tentacles wrapped around body like blanket       | Eyes forced to closed slits, Z aura    |
| Sick       | Drooping dome, body 2px narrower, slight lean                    | Limp hanging tentacles, reduced spread           | Thermometer pixel-line near mouth      |
| Nauseous   | Hunched forward, dome tilted 15deg down                           | 2 tentacles on "stomach", 3 bracing ground       | Swirl dots around head (dither pattern) |

### Unique Poses (1 per emotion, exclusive to that state)

| Emotion    | Pose Name          | Description                                                              |
|------------|--------------------|--------------------------------------------------------------------------|
| Normal     | Hands on Hips      | 2 tentacles akimbo on body sides, confident wide stance                  |
| Weird      | Chin Stroke        | 1 tentacle curled under dome (thinking), body leaning to one side        |
| Unhinged   | Tentacle Splay     | All 5 tentacles splayed outward max width, body vibrating                |
| Angry      | Ground Stomp       | 2 tentacles raised as fists, 3 stomping (thicker at tips)               |
| Sad        | Self Hug           | Tentacles wrapped around own body, dome slightly deflated                |
| Chaotic    | Tornado Spin       | Tentacles spiraling outward in rotation pattern, body blurred with wobble |
| Hungry     | Food Reach         | 2 tentacles reaching upward/forward, body leaning toward food            |
| Tired      | Face Plant         | Body toppled forward, dome on ground, tentacles splayed behind           |
| Slap Happy | Knee Slap          | 1 tentacle curled up slapping body side, body tilted back laughing       |
| Lazy       | Melted Puddle      | Body completely flattened, dome barely raised, tentacles pooled outward  |
| Fat        | Belly Rub          | 2 tentacles on belly, body leaned back, satisfied posture                |
| Chill      | Wall Lean          | Body at angle against invisible wall, tentacles crossed in front         |
| Horny      | Peacock Strut      | Body puffed out, tentacles in walking motion, exaggerated posture        |
| Excited    | Victory Jump       | Body 5px above ground line, all tentacles raised up and spread           |
| Nostalgic  | Photo Gaze         | 1 tentacle holding tiny rectangle (photo), body slightly turned          |
| Homesick   | Globe Hold         | 2 tentacles cradling small circle (globe/house), body hunched protectively |

---

## Rendering Modes

- **Speaking mode**: Character left + dynamic-sized chat bubble (scales with text)
- **Idle mode**: Full 250x122 canvas, no bubble — detailed 3D environments with dithered shading, perspective floors, textured surfaces

Environments support both modes: compact left-zone for speaking, full panoramic for idle.

## Environments (22)

Two rendering modes per environment. Idle mode uses the full canvas with 3D perspective, dithered shading (Bayer 4x4), textured surfaces, and depth layering. Speaking mode uses a compact left-zone version.

### Indoor Environments (10)

| # | Environment  | Type     | Ground/Floor                  | Key Elements                                         | Mood/Vibe                |
|---|--------------|----------|-------------------------------|------------------------------------------------------|--------------------------|
| 1 | Bedroom      | Home     | Perspective checkerboard tile | Bed with blanket folds + pillow, nightstand + lamp, window with crescent moon + curtains, oval rug | Cozy, nighttime          |
| 2 | Kitchen      | Home     | Checkered tile, dithered      | Counter + cabinets, pot rack, hanging utensils, steam wisps | Warm, busy               |
| 3 | Living Room  | Home     | Dithered rug on wood floor    | Couch with cushions, TV, coffee table, remote         | Relaxed, casual          |
| 4 | Bathroom     | Home     | Wet tile with puddle dither   | Bathtub with suds, mirror, towel rack, rubber duck    | Steamy, private          |
| 5 | Office       | Work     | Flat floor, desk shadow       | Desk + monitor, chair, paper stack, coffee mug, sticky notes | Productive, mundane      |
| 6 | Cafe         | Social   | Wood plank floor texture      | Counter + espresso machine, menu board, small tables, steaming cups | Warm, social             |
| 7 | Library      | Quiet    | Carpet dither                 | Tall bookshelves, reading lamp glow, armchair, ladder | Cozy, intellectual       |
| 8 | Arcade       | Fun      | Pixel tile pattern            | Game cabinets with screen art, coin-op, neon sign dots | Loud, fun, retro         |
| 9 | Gym          | Active   | Rubber mat texture            | Dumbbell rack, punching bag, pull-up bar, mirror wall | Energetic, sweaty        |
| 10| Haunted House| Spooky   | Cracked floorboards           | Cobwebs, crooked window, bats, candle flicker, tilted paintings | Creepy, Halloween        |

### Outdoor Environments (12)

| # | Environment  | Type     | Ground/Terrain                | Key Elements                                         | Mood/Vibe                |
|---|--------------|----------|-------------------------------|------------------------------------------------------|--------------------------|
| 11| Park         | Nature   | Textured grass + tufts        | Trees with dithered canopies + bark, bench, winding path, birds, flowers | Pleasant, daytime        |
| 12| Beach        | Coastal  | Sand dither + wave lines      | Umbrella, sun with rays, seashells, starfish, tide foam | Sunny, relaxing          |
| 13| Space        | Fantasy  | None (floating)               | Star field, planet arc with rings, satellite, nebula dots | Vast, wonder             |
| 14| Underwater   | Fantasy  | Seafloor with coral bumps     | Wavy seaweed, ascending bubbles, fish silhouettes     | Serene, blue             |
| 15| Rooftop      | Urban    | Flat roofline + railing       | City skyline silhouettes, water tower, twinkling stars, antenna | Cool, contemplative      |
| 16| Forest       | Nature   | Leaf litter dither + roots    | Dense tree trunks, dappled light spots, mushrooms, ferns, owl silhouette | Mysterious, enchanting   |
| 17| Mountain     | Alpine   | Rocky terrain + snow patches  | Peak silhouette, distant ranges, cliff edge, flag, cloud wisps, eagle | Epic, achievement        |
| 18| Desert       | Arid     | Sand dunes with wave texture  | Cacti, scorching sun + heat shimmer, skull, tumbleweed, mesa silhouette | Hot, isolated            |
| 19| Snow Field   | Winter   | Smooth snow with drift bumps  | Snowflakes falling, icicles, bare tree, snowman, frozen pond | Cold, quiet, holiday     |
| 20| Rainstorm    | Weather  | Puddles with ripple circles   | Heavy diagonal rain, dark dithered sky, lightning flash, bent trees | Dramatic, moody          |
| 21| City Street  | Urban    | Asphalt with crosswalk lines  | Buildings with lit windows, lamp posts, fire hydrant, parked car, traffic light | Busy, urban              |
| 22| Garden       | Nature   | Rich grass + stepping stones  | Flower beds, fountain with water arc, butterflies, vine trellis, bird bath | Beautiful, peaceful      |

---

## Decor Props

Small pixel-art elements (8-20px each) placed within environments. Each is a standalone draw function.

### Furniture
| Prop       | Size (approx) | Description                                        |
|------------|---------------|----------------------------------------------------|
| Bed        | 40x20px       | Rectangular frame with pillow bump and blanket line |
| Couch      | 35x18px       | Rounded back, seat cushion, armrests               |
| Desk       | 30x15px       | Flat top with two leg rectangles                   |
| Chair      | 15x20px       | Back rest + seat + 4 legs                          |
| Bookshelf  | 20x25px       | Rectangle with 3 horizontal shelf lines + book spines |
| Nightstand | 12x15px       | Small rectangle with drawer line and knob dot      |

### Food
| Prop       | Size (approx) | Description                                       |
|------------|---------------|---------------------------------------------------|
| Pizza      | 10x10px       | Triangle with circle toppings                     |
| Sushi      | 8x6px         | Rectangle with rice dots and nori wrap line       |
| Donut      | 8x8px         | Circle with center hole, sprinkle dots            |
| Coffee     | 8x10px        | Rectangle mug with handle arc, steam curves       |
| Ramen      | 12x10px       | Bowl arc with noodle squiggles and chopstick lines |
| Apple      | 6x7px         | Circle with stem line and leaf pixel              |

### Weather Effects (overlay, drawn after environment)
| Effect     | Description                                             |
|------------|---------------------------------------------------------|
| Rain       | Diagonal 3px lines falling, density parameter           |
| Snow       | Single scattered dots falling, slow drift               |
| Sun Rays   | Lines radiating from corner circle                      |
| Clouds     | Overlapping circle clusters (3-4 circles per cloud)     |
| Lightning  | Zigzag line from top, 2-3 segments, bright flash frame  |
| Wind       | Horizontal wavy lines across canvas                     |

### Plants
| Prop       | Size (approx) | Description                                     |
|------------|---------------|-------------------------------------------------|
| Potted     | 10x15px       | Trapezoid pot with stem and 3-leaf cluster      |
| Cactus     | 8x14px        | Vertical oval with 2 arm bumps, dot spines      |
| Flower     | 6x10px        | Stem line with 5-petal circle cluster on top    |
| Vine       | 4x20px        | Wavy vertical line with small leaf pairs        |
| Mushroom   | 8x8px         | Dome cap with stem, dot pattern on cap          |

### Electronics
| Prop       | Size (approx) | Description                                      |
|------------|---------------|--------------------------------------------------|
| TV         | 25x18px       | Rectangle with inner screen rect and stand line  |
| Lamp       | 8x20px        | Trapezoid shade on stem with base circle         |
| Phone      | 6x10px        | Rounded rectangle with screen rect and button    |
| Gamepad    | 12x8px        | Rounded rect with d-pad cross and 2 button dots  |
| Headphones | 12x10px       | Arc with two circle ear cups                     |
| Laptop     | 16x12px       | Two connected rectangles at angle (screen+base)  |

---

## Outfits (40)

Outfit overlays are drawn AFTER the body but BEFORE the face. They attach to anchor points on the body that shift with pose.

### Everyday Headwear (6)
| Outfit      | Description                                                    |
|-------------|----------------------------------------------------------------|
| Top Hat     | Tall rectangle on dome top with brim line                      |
| Crown       | 3-point zigzag band on dome top with dot jewels                |
| Chef Hat    | Tall puffy dome (wider than head) on dome top                  |
| Beanie      | Tight-fitting dome cap with folded brim line and pom-pom dot   |
| Cowboy Hat  | Wide curved brim with tall pinched crown, star badge           |
| Hard Hat    | Rounded dome with brim lip and stripe line                     |

### Holiday Headwear (7)
| Outfit      | Occasion     | Description                                           |
|-------------|--------------|-------------------------------------------------------|
| Santa Hat   | Christmas    | Floppy triangle with fur trim band and pom-pom tip    |
| Witch Hat   | Halloween    | Tall pointed cone with wide brim, buckle band         |
| Bunny Ears  | Easter       | Two tall oval ears on headband, pink inner dither      |
| Party Hat   | Birthday     | Triangle with dot pattern, string chin strap, "1" candle on top |
| Shamrock Hat| St. Patrick's| Short top hat with clover leaf on band                |
| Fireworks Crown | New Year | Zigzag crown with star-burst dots radiating upward    |
| Heart Headband | Valentine's | Thin band with two heart-shaped pixels on springs   |

### Eyewear (5)
| Outfit      | Description                                                    |
|-------------|----------------------------------------------------------------|
| Sunglasses  | Two filled rectangles over eye sockets with bridge line        |
| Monocle     | Single circle over right eye with chain line trailing down     |
| Goggles     | Two large circles over eyes with strap line around dome        |
| Eye Patch   | Filled circle over left eye with diagonal strap line           |
| Snorkel Mask| Large single lens over both eyes with snorkel tube arcing up   |

### Everyday Bodywear (6)
| Outfit      | Description                                                    |
|-------------|----------------------------------------------------------------|
| Cape        | Triangle hanging from neck area behind body, fluttering edge   |
| Scarf       | Wrapped band around neck with trailing end, knit pattern dots  |
| Sweater     | Body-covering pattern with collar line and sleeve edges        |
| Apron       | Front-only rectangle with neck strap and tie lines             |
| Toga        | Diagonal drape from one shoulder across body                   |
| Hoodie      | Body covering with hood outline around dome top                |

### Special Bodywear (6)
| Outfit      | Occasion     | Description                                           |
|-------------|--------------|-------------------------------------------------------|
| Rain Coat   | Rainy/gloomy | Buttoned front with hood outline, drip dots on edges  |
| Hospital Gown | Sick       | Open-back rectangle with tie dots, thin fabric dither |
| Tuxedo      | Formal/gala  | Lapel V-lines on chest with center button dots        |
| Wedding Veil| Wedding      | Draped dotted mesh arc from dome top trailing down    |
| Superhero Suit | Fun       | Chest emblem circle with lightning bolt, belt line    |
| Wizard Robe | Fantasy      | Long draping lines with star dot pattern, belt sash   |

### Costume Headgear (5)
| Outfit      | Description                                                    |
|-------------|----------------------------------------------------------------|
| Viking Helmet | Rounded dome with two curved horn arcs on sides             |
| Astronaut Helmet | Large circle enclosing head with visor reflection line    |
| Pirate Hat  | Wide brim with skull dot pattern, triangular top               |
| Detective Hat | Deerstalker: rounded cap with front and back brim flaps     |
| Wizard Hat  | Tall floppy cone with star and moon dot pattern, bent tip      |

### Accessories (5)
| Outfit      | Description                                                    |
|-------------|----------------------------------------------------------------|
| Bandana     | Tied band around dome with trailing triangle ends              |
| Bow Tie     | Small X-shape at neck center                                   |
| Flower Crown| Ring of alternating petal clusters on dome, leaf dots between  |
| Halo        | Dithered ellipse floating above dome top                       |
| Devil Horns | Two small pointed triangles on dome sides, tail from back      |

---

## Composition Pipeline (draw order)

```
1.  Clear frame (white)
2.  Draw ENVIRONMENT background
3.  Apply POSE body transform + select pose RLE body
4.  Draw BODY (RLE with transforms)
5.  Draw OUTFIT (body-relative anchors)
6.  Draw white eye sockets
7.  Draw PUPILS (emotion-specific)
8.  Draw BROWS / LIDS / SPECIAL EYES (emotion-specific)
9.  Draw TEARS (if applicable)
10. Draw MOUTH (emotion-specific)
11. Draw AURA PARTICLES (emotion-specific, body-center-relative)
12. Draw WEATHER overlay (if environment has weather + emotion modulation)
13. Draw CHAT BUBBLE
```

---

## Scene Address Format

Every rendered scene has a unique address: `{emotion}/{pose}/{environment}/{outfit}`

Examples:
- `angry/stomping/kitchen/chef_hat` -> Angry Jamal stomping in kitchen wearing chef hat
- `sad/sleeping/bedroom/none` -> Sad Jamal sleeping in bedroom, no outfit
- `excited/victory_jump/space/cape` -> Excited Jamal jumping in space wearing cape

This address maps directly to the output file tree:
```
output/by_emotion/angry/stomping_kitchen_chef_hat.png
output/by_environment/kitchen/angry_stomping_chef_hat.png
output/by_pose/stomping/angry_kitchen_chef_hat.png
```

---

## Directory Structure

```
assets/octopus/
|-- __init__.py              # Package root with REGISTRY imports
|-- asset_plan.md            # This file
|
|-- core/                    # Core rendering engine
|   |-- __init__.py
|   |-- canvas.py            # Frame buffer, pixel ops, IMG_W/H/Y_OFF constants
|   |-- body.py              # RLE body data (standard, fat, lazy + pose bodies)
|   +-- drawing.py           # Primitives: fill_circle, draw_line, draw_arc, draw_rect
|
|-- emotions/                # Emotion state definitions
|   |-- __init__.py          # REGISTRY: str -> EmotionConfig
|   |-- faces.py             # All pupil, mouth, brow, lid draw functions
|   +-- transforms.py        # setup_body_transform per emotion
|
|-- poses/                   # Pose system
|   |-- __init__.py          # Combined REGISTRY (shared + unique)
|   |-- shared/              # Available to every emotion
|   |   |-- __init__.py      # REGISTRY: str -> PoseConfig
|   |   |-- standing.py
|   |   |-- sitting.py
|   |   |-- laying.py
|   |   |-- sleeping.py
|   |   |-- sick.py
|   |   +-- nauseous.py
|   +-- unique/              # One per emotion
|       |-- __init__.py      # REGISTRY: str -> PoseConfig
|       |-- normal_hands_on_hips.py
|       |-- angry_stomp.py
|       |-- sad_self_hug.py
|       +-- ... (16 total)
|
|-- environments/            # Background scenes
|   |-- __init__.py          # REGISTRY: str -> draw_env(frame)
|   |-- bedroom.py
|   |-- kitchen.py
|   |-- living_room.py
|   |-- park.py
|   |-- beach.py
|   |-- space.py
|   |-- underwater.py
|   |-- office.py
|   |-- rooftop.py
|   +-- arcade.py
|
|-- decor/                   # Props and decorative elements
|   |-- __init__.py          # REGISTRY: str -> draw_prop(x, y, frame)
|   |-- furniture.py
|   |-- food.py
|   |-- weather.py
|   |-- plants.py
|   +-- electronics.py
|
|-- outfits/                 # Wearable overlays
|   |-- __init__.py          # REGISTRY: str -> draw_outfit(anchors, frame)
|   |-- headwear.py
|   |-- eyewear.py
|   |-- bodywear.py
|   +-- accessories.py
|
|-- aura/                    # Emotion Echo particle system
|   |-- __init__.py          # REGISTRY: str -> draw_aura(cx, cy, frame_idx, frame)
|   +-- particles.py         # Per-emotion particle definitions
|
|-- compose.py               # Scene compositor (env + body + outfit + face + aura)
|-- render_all.py            # Batch render: all combos or targeted subsets
|
+-- output/                  # Rendered outputs (gitignored)
    |-- by_emotion/
    |   +-- {emotion}/
    |       +-- {pose}_{env}_{outfit}.png
    |-- by_environment/
    |   +-- {env}/
    |       +-- {emotion}_{pose}_{outfit}.png
    |-- by_pose/
    |   +-- {pose}/
    |       +-- {emotion}_{env}_{outfit}.png
    +-- grids/
        +-- {type}_grid.png
```

Every `__init__.py` exposes a `REGISTRY` dict mapping `str -> callable` so the entire tree is walkable:

```python
from octopus.emotions import REGISTRY as EMOTIONS
from octopus.poses.shared import REGISTRY as SHARED_POSES
from octopus.poses.unique import REGISTRY as UNIQUE_POSES
from octopus.environments import REGISTRY as ENVIRONMENTS
from octopus.outfits import REGISTRY as OUTFITS
from octopus.aura import REGISTRY as AURAS
```

---

## Asset Count Summary

| Category     | Count | Items                                            |
|--------------|-------|--------------------------------------------------|
| Emotions     | 16    | existing                                         |
| Shared Poses | 6     | standing, sitting, laying, sleeping, sick, nauseous |
| Unique Poses | 16    | 1 per emotion                                    |
| Environments | 22    | 10 indoor + 12 outdoor (each with idle + speaking mode) |
| Decor Props  | 29    | 6 furniture + 6 food + 6 weather + 5 plants + 6 electronics |
| Outfits      | 40    | 6 everyday head + 7 holiday head + 5 eyewear + 6 everyday body + 6 special body + 5 costume head + 5 accessories |
| Aura Sets    | 16    | 1 particle set per emotion                       |
