---
date: 2026-04-12
authors:
  - rompasaurus
categories:
  - Firmware
  - Design
slug: sixteen-emotions
---

# 16 Emotions — Building the Octopus Personality System

One octopus personality isn't a pet. It's a novelty. Today the octopus learned to feel — angry eyebrows, sad droopy eyes, chaotic spiral pupils, heart-shaped creepy eyes, and 12 more distinct emotional states. Each one changes how the octopus looks, moves, and talks.

<!-- more -->

## The Emotion Architecture

Every emotional state is a combination of independently drawn components:

- **Pupils** — position, size, and shape (centered, shifted, spiral rings, hearts, stars, pinpricks)
- **Eyebrows** — parametric sine arcs above the eye sockets (angry V-shape, sad droopy)
- **Eyelids** — partial circle fills covering the top of the eye socket (tired, lazy)
- **Mouth** — distinct mathematical curve per emotion (parabola, sine wave, zigzag, ellipse with drool)
- **Body transform** — per-frame animation (breathing bob, jitter, sway, puff, droop)
- **Special effects** — tear drops (homesick), tongue (creepy), cheek puffs (fat)

The system is composable. Adding a new emotion means writing 2-3 small draw functions and a 4-element animation cycle. No bitmaps to create, no sprites to manage.

## The Lineup

The octopus went from 1 personality to 16 in a few sessions:

| Emotion | Eyes | Mouth | Body | Vibe |
|---------|------|-------|------|------|
| Normal | Centered pupils, highlights | Smirk/smile | Gentle breathing | Default sassy |
| Weird | Misaligned pupils | Sine wiggle | Lean + wave | Conspiratorial |
| Unhinged | Tiny pinpricks | Giant scream | Rapid jitter | Chaos mode |
| Angry | Glaring inward, V-brows | Tight frown | Puffed up, tremble | 8 arms, 0 patience |
| Sad | Downward, droopy brows | Gentle curve | Drooped, deflated | Ocean melancholy |
| Chaotic | Spiral rings | Zigzag bolt | Wild distortion | Entropy incarnate |
| Hungry | Looking up | Drool oval | Lean upward | Will sell hearts for tacos |
| Tired | Half-closed lids | Big yawn | Sagging down | One brain cell left |
| Slap Happy | One squint, one manic | Wobbly grin | Swaying | Deliriously giddy |
| Lazy | Nearly shut slits | Flat line | Tentacles draped right | Proudly doing nothing |
| Fat | Wide happy | Smile + cheek puffs | Wide dome, thick tentacles | Food-positive king |
| Chill | Side-glancing | Half-smile | Subtle lean | Stoner philosopher |
| Creepy | Heart-shaped | Tongue out | Rhythmic pulse | Tentacle romance |
| Excited | Star sparkles | Wide grin | Bouncing | CAPS LOCK ENERGY |
| Nostalgic | Looking up-right | Wistful smile | Gentle sway | Back in my day |
| Homesick | Teary + drops | Wobbly line | Curled inward | Missing the deep |

## How the Mouth Cycle Works

Each mood has a fixed 4-frame animation cycle that determines which mouth expression plays on each frame:

```c
static const uint8_t cycle_angry[] = {EXPR_ANGRY, EXPR_OPEN, EXPR_ANGRY, EXPR_ANGRY};
static const uint8_t cycle_sad[]   = {EXPR_SAD,   EXPR_OPEN, EXPR_SAD,   EXPR_SMILE};
static const uint8_t cycle_lazy[]  = {EXPR_LAZY,  EXPR_LAZY, EXPR_LAZY,  EXPR_OPEN};
```

New quotes are selected on `EXPR_OPEN` frames. So the angry octopus mostly frowns with brief mouth-opens between rants. The lazy octopus holds its flat line for three frames before reluctantly opening its mouth. The chaotic octopus mixes chaotic, unhinged, and weird mouths — it can't even commit to one expression.

## Each Emotion is a Standalone Firmware

Every emotional state has its own firmware directory under `dev-setup/` — `angry-octopus/`, `sad-octopus/`, `creepy-octopus/`, etc. Each has its own `main.c` (identical rendering code) and `quotes.h` (30-196 themed quotes generated to match the personality).

Pick a mood, flash it, and your desk octopus becomes that emotion permanently until you flash a different one. Or use the Mood Selector firmware that contains all 823 quotes across all 16 moods and lets you browse with serial commands.

## The Quote Generation Pipeline

Each personality has a curated quote list. The quotes are short (fits in a 170x70 pixel bubble at 5x7 font), thematically consistent, and written in ALL CAPS (the font only has uppercase). Some examples:

**Angry:** "I DIDN'T ASK TO BE BORN WITH 8 ARMS AND ANGER ISSUES."

**Tired:** "MY BRAIN HAS 47 TABS OPEN AND THEY'RE ALL LOADING."

**Creepy:** "ARE YOU A CORAL REEF? BECAUSE I WANT TO EXPLORE YOU."

**Homesick:** "THE DEEP OCEAN NEVER JUDGED ME FOR BEING SQUISHY."

## What This Enables

With 16 emotions, the octopus isn't a static display anymore. It's a character. It has range. Future features can trigger emotional transitions — feed the octopus and it goes from hungry to fat, ignore it and it goes from normal to sad, play with it and it gets excited. The emotion system is the foundation for the actual Tamagotchi gameplay loop.

But that's Phase 3. Right now, 16 different desk companions is already pretty great.
