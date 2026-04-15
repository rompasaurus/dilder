# Dilder User Engagement Plan

> Comprehensive design document for gameplay loops, progression systems, real-world integration, and hardware requirements for the Dilder digital octopus pet.

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Core Gameplay Loop](#2-core-gameplay-loop)
3. [Stat System](#3-stat-system)
4. [Emotional State Engine](#4-emotional-state-engine)
5. [User Interactions — Digital](#5-user-interactions--digital)
6. [User Interactions — Physical (Sensors)](#6-user-interactions--physical-sensors)
7. [Real-World Activity Integration](#7-real-world-activity-integration)
8. [Life Stages & Evolution](#8-life-stages--evolution)
9. [Progression & Unlock System](#9-progression--unlock-system)
10. [Dialogue System](#10-dialogue-system)
11. [Decor, Animations & Cosmetics](#11-decor-animations--cosmetics)
12. [Engagement Hooks & Retention](#12-engagement-hooks--retention)
13. [Treasure Hunt System](#13-treasure-hunt-system)
14. [Step Target Rewards — Daily, Weekly, Monthly](#14-step-target-rewards--daily-weekly-monthly)
15. [Hardware Requirements & Cost](#15-hardware-requirements--cost)
16. [Research: Tamagotchi & Virtual Pet Precedents](#16-research-tamagotchi--virtual-pet-precedents)
17. [Research: Real-World Activity Games](#17-research-real-world-activity-games)
18. [Research: Voice Interaction in Games](#18-research-voice-interaction-in-games)
19. [Implementation Challenges](#19-implementation-challenges)
20. [Phased Rollout Plan](#20-phased-rollout-plan)
21. [References](#21-references)

---

## 1. Design Philosophy

Dilder is not just a Tamagotchi clone. It is a **physical companion** that bridges the digital pet experience with the user's real-world behavior. The core principles:

- **Obligation through attachment**: The user cares for Dilder not because of gamification pressure, but because they develop a genuine emotional bond. The 16 emotional states and unique personality create something that feels alive.
- **Real life rewards virtual life**: Walking, exploring, talking — the user's physical actions directly feed Dilder's wellbeing. This reframes healthy habits as nurturing acts.
- **No permanent death, but real consequences**: Neglect makes Dilder visibly suffer (sad, hungry, tired, homesick). Recovery is always possible, but neglect leaves marks — slower growth, missed evolution windows, lost cosmetics. The sweet spot between Tamagotchi's harshness and modern apps' toothlessness.
- **Surprise and delight**: Dilder should do unexpected things — initiate conversations, react to environment changes, have opinions, remember events. Predictability kills engagement.
- **Depth through simplicity**: The e-ink screen and limited buttons force creative expression. Constraints breed character.

---

## 2. Core Gameplay Loop

### The Daily Rhythm

```
┌─────────────────────────────────────────────┐
│                WAKE UP                       │
│  Dilder wakes with the ambient light         │
│  Morning greeting based on mood + stats      │
│  Shows overnight stat changes                │
├─────────────────────────────────────────────┤
│              MORNING CARE                    │
│  Feed (hunger decays overnight)              │
│  Check emotional state                       │
│  Pet/interact for happiness boost            │
├─────────────────────────────────────────────┤
│             DAYTIME ACTIVITY                 │
│  User carries Dilder / leaves at home        │
│  Steps & distance tracked (accelerometer)    │
│  Location changes detected (WiFi geo)        │
│  Environmental sensing (light, temp, sound)  │
│  Periodic check-ins with dialogue            │
├─────────────────────────────────────────────┤
│            EVENING CARE                      │
│  Feed again (hunger decayed during day)      │
│  Review daily activity summary               │
│  Play / interact for happiness               │
│  Unlock rewards based on daily progress      │
├─────────────────────────────────────────────┤
│               BEDTIME                        │
│  Lights dim → Dilder gets tired              │
│  Turn off light / put in dark place          │
│  Dilder sleeps (low power mode)              │
│  Stats decay slowly overnight                │
└─────────────────────────────────────────────┘
```

### The Micro-Loop (Every 1-5 Minutes)

Each tick (configurable, default 60 seconds):
1. Decay stats (hunger, happiness, energy, hygiene)
2. Read sensor inputs (light, sound, motion, touch, temp)
3. Evaluate emotional state based on stats + sensor context
4. Update display if state changed
5. Check for trigger events (thresholds, time-based, environmental)
6. Optionally display a quote or initiate a dialogue prompt

### The Engagement Loop (Hourly/Session)

1. User checks on Dilder → sees current state
2. Takes an action (feed, pet, play, talk)
3. Sees immediate response (mood shift, animation, dialogue)
4. Gets feedback on progress (XP, stat bars, unlock hints)
5. Leaves with anticipation (what will happen next? will it evolve?)

---

## 3. Stat System

### Primary Stats

| Stat | Range | Decay Rate | Refill Method | Critical Threshold |
|------|-------|-----------|---------------|-------------------|
| **Hunger** | 0-100 | -1/10min | Feed action | <20 → Hungry mood |
| **Happiness** | 0-100 | -1/15min | Pet, play, talk, walk | <20 → Sad mood |
| **Energy** | 0-100 | -1/12min (awake) | Sleep | <15 → Tired mood |
| **Hygiene** | 0-100 | -1/30min | Clean action | <25 → Uncomfortable |
| **Health** | 0-100 | Static unless neglected | Maintain other stats | <30 → Sick |

### Secondary Stats (Derived / Accumulated)

| Stat | Source | Effect |
|------|--------|--------|
| **Bond Level** | Total interactions over lifetime | Unlocks dialogue, features, evolutions |
| **Discipline** | Scolding when misbehaving | Affects evolution path |
| **Intelligence** | Talking to Dilder, word exposure | Unlocks dialogue complexity |
| **Fitness** | Steps walked, distance | Unlocks physical abilities, animations |
| **Exploration** | Unique locations visited | Unlocks decor themes, world knowledge |
| **Age** | Real time elapsed since hatch | Triggers life stage transitions |
| **Weight** | Feeding frequency & type | Visual change (Fat mood if overfed) |

### Hidden Stats

| Stat | Tracking | Purpose |
|------|----------|---------|
| **Care Mistakes** | Times a critical need went unmet for >15 min | Affects evolution quality |
| **Consecutive Days** | Streak of daily interaction | Streak bonuses |
| **Noise Exposure** | Cumulative loud sound events | Personality trait development |
| **Night Disturbances** | Times woken during sleep hours | Affects morning mood |

### Stat Decay Modifiers

- **Life stage**: Baby decays 2x faster (needier), Adult decays 0.75x (more self-sufficient)
- **Bond level**: Higher bond = slightly slower happiness decay (pet trusts you)
- **Environment**: Good temp/humidity = slower hygiene decay; bad conditions = faster
- **Activity**: Walking reduces energy faster but boosts happiness
- **Time of day**: Hunger decays faster during "active hours" (8am-8pm)

---

## 4. Emotional State Engine

### Emotion Resolution Algorithm

The 16 existing emotional states map to stat combinations and sensor inputs:

```
EMOTION = f(hunger, happiness, energy, hygiene, health,
            sensor_context, recent_events, personality_traits)
```

### Emotion Trigger Table

| Emotion | Primary Trigger | Secondary Triggers |
|---------|----------------|-------------------|
| **Normal/Sassy** | All stats 40-80 (balanced) | Default personality |
| **Hungry** | Hunger < 20 | — |
| **Tired** | Energy < 15 | Late hour + low energy |
| **Sad** | Happiness < 20 | Neglect streak > 4 hours |
| **Angry** | Scolded too harshly, shaken violently | Hunger < 10 AND happiness < 30 |
| **Excited** | Just received food/pet when stats were low | Step milestone reached |
| **Chill** | All stats > 60, calm environment | Low noise, comfortable temp |
| **Lazy** | Energy 15-30, no interaction for 2+ hours | Overfed (weight high) |
| **Fat** | Weight > threshold (overfed) | Happiness high + hunger full |
| **Chaotic** | Rapidly changing inputs, conflicting stats | Shaken + loud noise + touch |
| **Weird** | Random trigger (5% chance per tick if bored) | Low interaction + moderate stats |
| **Unhinged** | Health < 20, multiple stats critical | Extreme neglect |
| **Slap Happy** | Happiness > 90 after being < 30 | Major recovery event |
| **Horny** | Specific life stage + happiness > 70 | Bond level > threshold |
| **Nostalgic** | Age milestone reached, returning to known location | — |
| **Homesick** | Away from "home" WiFi for extended period | First time at new location |

### Sensor-Driven Emotion Modifiers

| Sensor Input | Emotion Effect |
|-------------|---------------|
| **Bright light** | +energy (morning), forced awake if sleeping |
| **Darkness** | Triggers tiredness, enables sleep |
| **Loud noise** | Startled → brief Excited or Angry; sustained → Annoyed |
| **Gentle touch** | +happiness, calming effect |
| **Rapid shaking** | Angry or Chaotic; if playful context → Excited |
| **Cold temperature** | Uncomfortable → Sad; extreme → Sick |
| **Hot temperature** | Uncomfortable → Angry; octopus prefers cool |
| **Walking motion** | +happiness (adventure), +fitness |
| **Stillness (long)** | Boredom → Lazy → Weird |
| **Voice/talking** | +intelligence, +happiness (attention) |
| **Yelling** | Discipline effect OR Sad (context-dependent) |
| **Silence (long)** | Lonely → Homesick if away, → Nostalgic if home |

### Emotion Blending

Emotions don't snap — they transition. Each emotion has a **weight** (0.0-1.0) and the highest-weight emotion wins, but the transition includes a brief "between" animation:

```
Current: Chill (0.7) → recalculate → Hungry wins (0.8)
Transition: Chill face slowly shifts → brief pause → Hungry face appears
Duration: 2-3 frames (~8-12 seconds on e-ink)
```

---

## 5. User Interactions — Digital

### Button Actions (3-5 GPIO Buttons)

| Button | Short Press | Long Press (2s) | Double Press |
|--------|------------|-----------------|-------------|
| **A (Select)** | Confirm / interact | Open menu | — |
| **B (Back)** | Cancel / dismiss | Toggle backlight | — |
| **Up** | Scroll up / navigate | — | — |
| **Down** | Scroll down / navigate | — | — |
| **C (Action)** | Context action (feed/pet/play) | Scold | Quick status view |

### Menu System

```
Main Menu
├── Feed
│   ├── Meal (fills hunger, +1 weight)
│   ├── Snack (fills happiness, +2 weight)
│   └── Treat (rare, unlockable, special effects)
├── Play
│   ├── Mini-game (happiness + bond)
│   └── Tickle (quick happiness boost)
├── Care
│   ├── Clean (hygiene)
│   ├── Medicine (when sick)
│   └── Light on/off (sleep control)
├── Stats
│   ├── Health meter (hunger/happy/energy/hygiene)
│   ├── Bond level & XP
│   ├── Today's activity (steps/distance)
│   └── Achievements
├── Decor
│   ├── Hats & accessories
│   ├── Background themes
│   └── Animation styles
└── Settings
    ├── Sound (beeper on/off)
    ├── Time display
    └── Brightness
```

### Scolding Mechanic

Scolding serves the **discipline** function (from Tamagotchi research):

- **When to scold**: Dilder sometimes misbehaves — refuses food, makes a mess, acts out. A prompt appears: "Dilder is being defiant!"
- **Correct scold**: +25% discipline. Dilder briefly shows Angry face, then complies.
- **Incorrect scold** (scolding when Dilder actually needed something): -happiness, -bond. Dilder shows Sad face.
- **Yelling at mic as scold**: Volume spike during misbehavior event counts as scolding. Adds immersive feel.
- **Discipline affects evolution**: 100% discipline at life stage transition → best evolution path.

---

## 6. User Interactions — Physical (Sensors)

### Touch / Petting (MPR121 Capacitive Touch)

Multiple touch zones on the octopus enclosure:

| Zone | Touch Effect | Location on Case |
|------|-------------|-----------------|
| **Head** | +happiness (petting), calming | Top of device |
| **Side (left)** | Tickle → brief Excited/Slap Happy | Left panel |
| **Side (right)** | Tickle → brief Excited/Slap Happy | Right panel |
| **Back** | Comfort → reduces Sad/Homesick faster | Rear of device |
| **Sustained hold** | Maximum comfort. Dilder "purrs" (happy animation) | Any zone, 5+ seconds |
| **Rapid tapping** | Annoyance → Angry if overdone | Any zone |

### Microphone Interactions (MAX9814 Analog Mic)

| Sound Event | Detection Method | Game Effect |
|-------------|-----------------|-------------|
| **Talking (moderate volume)** | Sustained mid-level signal >3s | +intelligence, +happiness (attention) |
| **Yelling (high volume)** | Signal above high threshold | Discipline (if misbehaving) or Scare (Sad/Angry) |
| **Singing** | Sustained mid-level, rhythmic pattern | +happiness, special animation |
| **Clap** | Sharp spike then silence | Attention getter — Dilder looks at you |
| **Sustained silence** | No signal above noise floor >30min | Loneliness timer starts |
| **Music** | Sustained varied signal (heuristic) | Chill mood boost, special animation |
| **Whisper (low volume)** | Just above noise floor, sustained | Secret/intimate interaction, +bond |

**Note**: The Pico W cannot do speech recognition. All mic interactions are volume/pattern-based. True voice commands are a Phase 5 (Pi Zero WH) feature.

### Light Sensing (BH1750)

| Light Level | Lux Range | Game Effect |
|------------|-----------|-------------|
| **Bright daylight** | >500 lux | Active mode, energy decay normal |
| **Indoor normal** | 100-500 lux | Standard operation |
| **Dim/evening** | 10-100 lux | Dilder gets drowsy, yawns |
| **Dark** | <10 lux | Sleep mode triggers (if energy low) |
| **Sudden bright** | Delta >300 lux in <5s | Startled reaction, forced wake |
| **Sustained dark + awake** | <10 lux for >5min, energy >50 | Scared/Homesick (too dark, not sleepy) |

### Temperature / Humidity (BME280)

| Condition | Range | Game Effect |
|-----------|-------|-------------|
| **Comfortable** | 18-24°C, 40-60% RH | Neutral / Chill mood bonus |
| **Too hot** | >28°C | Uncomfortable → Angry, faster hygiene decay |
| **Too cold** | <15°C | Uncomfortable → Sad, huddles up animation |
| **Very humid** | >70% RH | Happy (octopus likes moisture!) |
| **Very dry** | <30% RH | Uncomfortable, skin drying out dialogue |
| **Temperature swing** | >5°C change in 10min | Confused/Chaotic reaction |

### Motion / Accelerometer (LSM6DSO)

| Motion Event | Detection | Game Effect |
|-------------|-----------|-------------|
| **Walking** | Step counter | +fitness, +exploration XP |
| **Running** | High step frequency | +fitness (2x), Excited mood |
| **Stationary (long)** | No steps >2 hours | Boredom → Lazy |
| **Picked up** | Orientation change from resting | Alert, Dilder "wakes up" |
| **Put down** | Transition to stationary after carried | Settling animation |
| **Shaking** | High-frequency motion | Angry/Chaotic (or playful if brief) |
| **Falling** | Free-fall detection | Scared reaction, health check |
| **Tilted** | Sustained angle >45° | Confused, "I'm sideways!" dialogue |

---

## 7. Real-World Activity Integration

### Step Counter System

Daily step integration with Dilder's stats:

| Daily Steps | Tier | Dilder Effect |
|------------|------|---------------|
| 0-500 | Sedentary | Dilder gets Lazy, -happiness over time |
| 500-2,000 | Light | Baseline — no bonus or penalty |
| 2,000-5,000 | Active | +happiness bonus, Dilder is Chill |
| 5,000-8,000 | Fit | +happiness, +fitness XP, special dialogue |
| 8,000-12,000 | Athletic | All bonuses + unlock chance for special animation |
| 12,000+ | Explorer | Maximum bonuses + rare unlock chance |

**Weekly step milestones**:
- 10,000 weekly → Small reward (snack item, decor piece)
- 35,000 weekly → Medium reward (new animation, dialogue set)
- 70,000 weekly → Large reward (evolution XP boost, rare cosmetic)

### Distance & Location System

Using WiFi geolocation (free, no extra hardware):

| Feature | Implementation | Game Effect |
|---------|---------------|-------------|
| **Home detection** | Recognize home WiFi SSID/BSSID | Dilder is "home" — comfort bonus, no Homesick |
| **Away from home** | Home WiFi not detected | Adventure mode — exploration XP, but Homesick risk |
| **New location** | New WiFi fingerprint not seen before | Discovery bonus! +exploration XP, special dialogue |
| **Familiar location** | Previously seen WiFi fingerprint | Nostalgic reaction, comfort |
| **Work/School** | User-tagged location | Dilder knows your routine — anticipatory dialogue |
| **Distance estimate** | Count of unique WiFi environments per day | Rough proxy for distance traveled |

**Location-Themed Unlocks**:
- Visit 5 unique locations → Unlock "Explorer" hat
- Visit 10 → Unlock ocean-themed background
- Visit 25 → Unlock deep-sea animation set
- Visit a new location 3 days in a row → Unlock "Adventurer" title

### Real-World Weather Integration (Phase 5 — Pi Zero WH with Internet)

- Fetch local weather via API based on WiFi geolocation
- Rainy day → Dilder is happy (octopus loves water)
- Sunny day → Dilder needs shade/cooling
- Snowy → Special rare animation, Dilder plays in snow

---

## 8. Life Stages & Evolution

### Life Stage Progression

```
Stage 1: EGG          (Age 0-1 day)
   │ Hatches after warmth (touch), patience, gentle interaction
   ▼
Stage 2: HATCHLING    (Age 1-3 days)
   │ Tiny octopus, very needy, limited expressions
   │ Stats decay 2x normal, requires frequent care
   │ 4 misbehavior windows for discipline
   ▼
Stage 3: JUVENILE     (Age 3-7 days)
   │ Growing, personality starts forming
   │ Unlock: basic dialogue, first decor slot
   │ Evolution branch based on care quality
   ▼
Stage 4: ADOLESCENT   (Age 7-14 days)
   │ Moody, unpredictable, tests boundaries
   │ All 16 emotions now possible
   │ Unlock: full dialogue, play mini-games
   │ Evolution branch based on discipline + fitness + bond
   ▼
Stage 5: ADULT        (Age 14-30 days)
   │ Stable personality, full feature access
   │ Final form determined by accumulated stats
   │ Unlock: all decor, advanced animations
   │ Can mentor new eggs (if breeding implemented)
   ▼
Stage 6: ELDER        (Age 30+ days)
   │ Slower stat decay, wiser dialogue
   │ Nostalgic, reflective personality
   │ Unique elder-only animations and quotes
   │ Eventually: peaceful retirement or rebirth
```

### Evolution Branches (Adult Forms)

The adult form Dilder evolves into depends on how it was raised. Inspired by Tamagotchi's deterministic evolution:

| Adult Form | Requirements | Visual Changes | Personality |
|-----------|-------------|----------------|-------------|
| **Deep-Sea Scholar** | High intelligence, high bond, moderate discipline | Glasses, book, contemplative pose | Philosophical, verbose quotes |
| **Reef Guardian** | High fitness, high exploration, balanced stats | Muscular tentacles, coral crown | Adventurous, encouraging quotes |
| **Tidal Trickster** | Low discipline, high happiness, chaotic care pattern | Jester hat, mischievous grin | Chaotic, unpredictable, funny |
| **Abyssal Hermit** | High discipline, low social interaction, self-sufficient | Cloak, dim eyes, stoic | Quiet, rare but profound dialogue |
| **Coral Dancer** | High happiness, lots of music/singing exposure, creative | Flowing ribbons, graceful animations | Artistic, poetic quotes |
| **Storm Kraken** | Lots of scolding, high anger exposure, but survived | Larger, intimidating, powerful look | Tough, confrontational but loyal |

### Stage-Specific Needs

| Stage | Primary Need | Unique Mechanic | Failure Consequence |
|-------|-------------|-----------------|-------------------|
| **Egg** | Warmth (touch) | Must be held/touched periodically | Delayed hatching |
| **Hatchling** | Constant feeding | Cries every 3 minutes if hungry | Care mistakes accumulate fast |
| **Juvenile** | Exploration | Wants to go to new places | Becomes Homesick/bored |
| **Adolescent** | Discipline + Freedom balance | Rebels, tests limits | Evolves into lesser adult form |
| **Adult** | Maintenance + Activity | Self-sufficient but still needs bond | Gradual happiness decline |
| **Elder** | Comfort + Routine | Prefers familiar locations, gentle touch | Accelerated aging |

---

## 9. Progression & Unlock System

### Experience & Leveling

| XP Source | Amount | Category |
|----------|--------|----------|
| Feed when hungry | +5 | Care |
| Pet (touch) | +2 | Bond |
| Play mini-game | +10 | Bond |
| Walk 1,000 steps | +15 | Fitness |
| Visit new location | +25 | Exploration |
| Talk to Dilder (mic activity) | +3 | Intelligence |
| Maintain all stats >50 for 1 hour | +10 | Care |
| Survive a full day with no care mistakes | +20 | Care |
| Reach a step milestone | +50 | Fitness |
| Weather event (rain while outside) | +30 | Exploration |

### Unlock Tiers

| Bond Level | XP Required | Unlocks |
|-----------|-------------|---------|
| **1: Stranger** | 0 | Basic feeding, minimal dialogue |
| **2: Acquaintance** | 100 | Petting response, more expressions |
| **3: Companion** | 500 | Dialogue options, 1 decor slot |
| **4: Friend** | 1,500 | Mini-games, nickname feature |
| **5: Best Friend** | 4,000 | Full dialogue tree, 3 decor slots |
| **6: Soulmate** | 10,000 | Secret dialogue, all decor, special animations |
| **7: Bonded** | 25,000 | Dilder initiates conversation, remembers things |
| **8: Legendary** | 50,000+ | Everything unlocked, elder wisdom mode |

### Achievement System

Achievements provide one-time rewards and visible badges:

**Care Achievements**:
- "First Meal" — Feed Dilder for the first time → Unlock Snack item
- "Perfect Day" — No care mistakes for 24 hours → +100 XP
- "Week of Love" — 7-day care streak → Unlock heart animation
- "Month of Devotion" — 30-day care streak → Unlock rare decor set

**Exploration Achievements**:
- "First Steps" — Walk 100 steps with Dilder → Unlock step counter display
- "Neighborhood Explorer" — Visit 5 unique locations → Unlock Explorer hat
- "City Mapper" — Visit 25 unique locations → Unlock map background
- "Marathon" — Walk 42,195 steps in one day → Unlock running animation

**Social Achievements**:
- "First Words" — Talk to Dilder via mic for 10 seconds → Unlock dialogue
- "Storyteller" — 100 cumulative minutes of mic activity → Unlock complex dialogue
- "Loud and Proud" — Yell at Dilder (intentionally) → Unlock Angry response set
- "Whisper Secret" — Low-volume mic input for 30s → Unlock secret dialogue

**Environmental Achievements**:
- "Night Owl" — Keep Dilder awake past midnight → Unique tired dialogue
- "Early Bird" — Interact before 6 AM → Special morning greeting
- "Weather Friend" — Experience rain while carrying Dilder → Happy dance animation
- "Cozy Keeper" — Maintain optimal temp/humidity for 8 hours → Comfort decor

**Mastery Achievements**:
- "All Emotions" — Witness all 16 emotional states → Unlock emotion gallery
- "Disciplinarian" — Reach 100% discipline → Evolution bonus
- "Zen Master" — Keep all stats >60 for 72 hours → Unlock Chill mode
- "Chaos Agent" — Trigger Chaotic + Unhinged + Weird in one day → Special quote set

---

## 10. Dialogue System

### Dialogue by Life Stage

**Hatchling (Simple, one-line)**:
```
"mama?"
"hungwy..."
"*happy bubbles*"
"dark... scary..."
"warm... nice..."
```

**Juvenile (Short phrases, curious)**:
```
"What's out there?"
"Can we go somewhere new?"
"I learned a new word today!"
"Why is it so hot in here?"
"Are you my person?"
```

**Adolescent (Opinionated, moody)**:
```
"Whatever."
"You don't understand me."
"Actually, I read that octopuses are the smartest invertebrates."
"Leave me alone... wait, don't actually leave."
"I could totally survive on my own. ...right?"
```

**Adult (Full personality, context-aware)**:
```
"Good morning! I had the strangest dream about the Mariana Trench."
"We've walked 3,247 steps today. My tentacles are getting toned."
"It's been 4 hours since you last checked in. I was starting to worry."
"This new place smells different. I like it."
"Remember when I was just a hatchling? You were so attentive back then..."
```

**Elder (Wise, reflective)**:
```
"I've seen many sunrises through this screen. Each one different."
"You know, discipline isn't about control. It's about trust."
"My tentacles may be slower, but my hearts are fuller."
"Thank you for every step we've walked together."
"When I was young, I thought the world was just this room..."
```

### Context-Sensitive Dialogue Triggers

| Context | Dialogue Example |
|---------|-----------------|
| First interaction of the day | "Oh! You're here! I missed you." |
| After 8+ hours of no interaction | "I was starting to think you forgot about me..." |
| When steps milestone reached | "We did it! 5,000 steps! My tentacles are BURNING." |
| When visiting new location | "Whoa, where are we? Everything's different here!" |
| When temperature drops | "Brrr... can you put me somewhere warmer?" |
| After being yelled at | "...that was loud. Are you okay?" |
| After gentle sustained petting | "Mmm... keep doing that. Eight arms of relaxation." |
| When overfed | "I can't... eat... another... *burp*" |
| When all stats are perfect | "You know what? Life is good. Really good." |
| At night, refusing sleep | "Five more minutes? The dark is so... dark." |

### Dialogue Unlock by Intelligence Stat

| Intelligence Level | Dialogue Complexity |
|-------------------|-------------------|
| 0-20 | Simple phrases, emotes, sound effects |
| 20-40 | Full sentences, basic opinions |
| 40-60 | Multi-sentence responses, questions back to user |
| 60-80 | References to past events, preferences, humor |
| 80-100 | Philosophy, complex emotion, callbacks to user behavior |

---

## 11. Decor, Animations & Cosmetics

### Decor Slots

| Slot | Examples | Unlock Method |
|------|----------|--------------|
| **Hat** | None, bow, crown, glasses, explorer hat, jester hat, coral crown | Bond level + achievements |
| **Background** | Ocean floor, reef, deep sea, city (location-based), cozy room | Exploration milestones |
| **Accessory** | Scarf (cold weather), sunglasses (bright), book (intelligent) | Stat thresholds |
| **Animation Style** | Calm sway, energetic bounce, lazy slouch, regal float | Life stage + personality |

### Special Animations (Unlockable)

| Animation | Trigger / Unlock |
|-----------|-----------------|
| **Happy Dance** | First rain encounter OR happiness >90 |
| **Tentacle Wave** | Greeting after long absence |
| **Ink Cloud** | Scared reaction (sudden loud noise, fall) |
| **Sleep Bubble** | Sleeping with full stats (peaceful sleep) |
| **Victory Pose** | Achievement unlocked |
| **Sad Curl** | Extreme sadness, tentacles wrap around body |
| **Thinking Pose** | High intelligence, contemplating |
| **Workout Flex** | Fitness milestone reached |
| **Shiver** | Cold temperature detected |
| **Puff Up** | Angry, making self look bigger |
| **Color Pulse** | (E-ink dither pattern) Excited/emotional moment |
| **Bubble Stream** | Happy in humid environment |

### Seasonal / Time-Based Cosmetics

| Event | Duration | Unlockable |
|-------|----------|-----------|
| **Night mode** | 10pm-6am | Starry background, moon hat |
| **Weekend** | Sat-Sun | Relaxed animations, lazy dialogue |
| **Milestone birthday** | Each life stage transition | Birthday hat (24 hours) |
| **Streak celebrations** | 7, 14, 30, 60, 90 day streaks | Increasingly rare party decor |

---

## 12. Engagement Hooks & Retention

### Daily Hooks

| Hook | Mechanism | Psychological Lever |
|------|-----------|-------------------|
| **Morning greeting** | Unique message each day based on stats/weather/events | Curiosity ("what will it say today?") |
| **Stat decay** | Stats drop overnight — user must tend to pet | Obligation (Tamagotchi effect) |
| **Daily challenge** | "Walk 3,000 steps today for a bonus" | Goal-setting |
| **Streak counter** | Consecutive days of care | Loss aversion ("don't break the streak") |
| **Random event** | 10% chance per day of special event (e.g., "Dilder found a treasure!") | Variable reward (slot machine psychology) |

### Weekly Hooks

| Hook | Mechanism |
|------|-----------|
| **Weekly step summary** | "This week we walked 23,451 steps together!" |
| **Evolution progress** | Visual progress bar toward next life stage |
| **Weekly challenge** | "Visit 3 new places this week" |
| **Mood journal** | Summary of emotional states over the week |

### Long-Term Hooks

| Hook | Mechanism |
|------|-----------|
| **Life stage transitions** | Visible growth creates anticipation and reward |
| **Evolution mystery** | "What adult form will I become?" Unknown outcome drives engagement |
| **Achievement hunting** | Completionism drive |
| **Dialogue discovery** | New dialogue unlocked gradually — always something new to find |
| **Decor collection** | Cosmetic goals for customization enthusiasts |
| **Bond level progression** | Slow, meaningful progression that rewards dedication |
| **Rebirth cycle** | After Elder stage, option to start over with inherited bonuses |

### Anti-Churn Mechanisms

| Problem | Solution |
|---------|----------|
| User forgets about device | Push notification if WiFi connected (Phase 5); sad animations visible on desk |
| Stats feel punishing | Recovery is always fast — 2-3 interactions restore from critical |
| Nothing new happening | Random events, seasonal content, environmental reactivity |
| Progress feels slow | Multiple parallel progression tracks (bond, fitness, exploration, intelligence) |
| User feels guilty after neglect | Dilder forgives quickly — "You're back! I knew you'd come back!" |

### The Rebirth System

After the Elder stage (30+ days), the user can choose:
- **Continue**: Dilder lives on as an Elder, slowly accumulating wisdom
- **Rebirth**: Dilder lays an egg. The new Dilder inherits:
  - 10% of parent's bond XP (head start)
  - One decor item from parent
  - A "heritage trait" that slightly biases evolution
  - A memorial entry in the journal

This creates infinite replayability and emotional weight ("my 3rd-generation Deep-Sea Scholar").

---

## 13. Treasure Hunt System

### Overview

Dilder generates GPS-based treasure hunts — virtual "gifts" placed at real-world coordinates that the user must physically walk to in order to collect. The device displays a compass heading and distance readout to guide the user, turning the e-ink screen into a pirate treasure map.

### How It Works

```
┌─────────────────────────────────────────────────┐
│  1. TREASURE SPAWNS                              │
│     System selects a location within walkable    │
│     radius of user's current position            │
│     (configurable: 200m, 500m, 1km, 2km)        │
├─────────────────────────────────────────────────┤
│  2. HUNT MODE ACTIVATES                          │
│     E-ink screen shows:                          │
│     ┌──────────────────────────────┐             │
│     │    ↗ NE                      │             │
│     │                              │             │
│     │      ◎ ─ ─ ─ → 🎁            │             │
│     │                              │             │
│     │   Distance: 347m             │             │
│     │   "I smell something good!"  │             │
│     └──────────────────────────────┘             │
│     Compass arrow updates every 10s              │
│     Distance updates every 10s                   │
├─────────────────────────────────────────────────┤
│  3. PROXIMITY DETECTION                          │
│     Distance thresholds:                         │
│     >500m  → "Far away... keep going!"           │
│     200-500m → "Getting warmer!"                 │
│     50-200m → "So close! I can feel it!"         │
│     <50m   → "HERE! Look around!"                │
│     <15m   → TREASURE FOUND — collect screen     │
├─────────────────────────────────────────────────┤
│  4. COLLECTION                                   │
│     User presses button to collect               │
│     Reward animation plays                       │
│     Item/XP/cosmetic added to inventory          │
│     Dilder reacts with Excited mood              │
└─────────────────────────────────────────────────┘
```

### Treasure Types

| Type | Rarity | Reward | Spawn Condition |
|------|--------|--------|----------------|
| **Snack Crate** | Common (60%) | Special food item — restores hunger + happiness | Any time |
| **Cosmetic Shell** | Uncommon (25%) | Random decor item (hat, accessory, background) | Bond level 3+ |
| **Memory Fragment** | Rare (10%) | Lore piece about Dilder's ocean origins — unlocks special dialogue | Bond level 5+ |
| **Golden Pearl** | Legendary (5%) | Major XP boost (+500) OR rare evolution modifier | Once per week max |
| **Elder Relic** | Mythic (<1%) | Unique one-of-a-kind cosmetic or animation | Lifetime achievement |

### Spawn Rules

- **Maximum 1 active treasure hunt at a time** — prevents overwhelming the user
- **Spawn triggers**:
  - Daily: 1 guaranteed treasure spawns at a random time (if GPS is active)
  - Step milestone: Bonus treasure at 5,000 and 10,000 daily steps
  - New location: 30% chance of treasure when visiting a new WiFi fingerprint
  - Life stage transition: Guaranteed legendary treasure on evolution
- **Minimum distance**: Treasures spawn at least 100m away (must walk, not just stand there)
- **Maximum distance**: Configurable per user — default 1km radius, up to 5km for adventurers
- **Expiration**: Treasures expire after 24 hours if uncollected (creates urgency)
- **Safety radius**: No spawns in unsafe areas — user can flag zones to exclude

### Compass & Navigation Display

The e-ink display shows a dedicated treasure hunt screen:

```
┌──────────────────────────────────┐
│         N                        │
│       ╱   ╲                      │
│     W   ↗   E     347m           │
│       ╲   ╱                      │
│         S                        │
│                                  │
│  ┌──────────────────────────┐    │
│  │ Dilder: "That way! I can │    │
│  │ smell something salty!"  │    │
│  └──────────────────────────┘    │
│                                  │
│  [A: Collect]  [B: Cancel Hunt]  │
└──────────────────────────────────┘
```

**Compass implementation**:
- Requires accelerometer (LSM6DSO) for tilt compensation
- Magnetometer needed for true heading — **add HMC5883L or LIS3MDL** (~$2-4)
- Alternative: heading derived from GPS track (only works while moving)
- Update rate: Every 10 seconds (e-ink partial refresh)
- Arrow drawn as a rotated triangle pointing toward target bearing

**Distance calculation**:
- Haversine formula for GPS coordinates: `d = 2r × arcsin(√(sin²(Δlat/2) + cos(lat1)×cos(lat2)×sin²(Δlon/2)))`
- Rounded to nearest 10m when >100m, nearest 1m when <100m
- Display in meters (<1km) or km (>1km)

### Magnetometer Hardware for Compass

| Part | Cost | Interface | Notes |
|------|------|-----------|-------|
| **HMC5883L** | ~$2-3 | I2C (0x1E) | Popular, cheap. Discontinued by Honeywell but clones everywhere. |
| **LIS3MDL** | ~$3-5 | I2C (0x1C/0x1E) | STMicro. Better accuracy. Adafruit breakout available. |
| **QMC5883L** | ~$1-2 | I2C (0x0D) | Chinese replacement for HMC5883L. Works fine. Cheapest option. |
| **MMC5603** | ~$4-6 | I2C (0x30) | Memsic. High accuracy. SparkFun breakout. |
| **BMM150** | ~$3-5 | I2C (0x10-0x13) | Bosch. Often paired with BME280 on combo boards. |

**Recommendation**: QMC5883L for budget (~$1-2) or LIS3MDL for quality (~$4). Both work on I2C with no address conflicts with existing sensors.

### Treasure Hunt Dialogue

| Proximity | Dilder Quote Examples |
|-----------|----------------------|
| Hunt starts | "Ooh! I sense something nearby! Let's go find it!" |
| Far (>500m) | "Still far... but the adventure is the journey, right?" |
| Medium (200-500m) | "Getting warmer! My tentacles are tingling!" |
| Close (50-200m) | "SO CLOSE! I can practically taste it!" |
| Very close (<50m) | "RIGHT HERE! It's gotta be around here somewhere!" |
| Found | "WE DID IT! Look what we found! *happy dance*" |
| Expired | "Aww... the tide washed it away. There'll be another one." |
| Cancelled | "Oh well. Maybe next time we'll go treasure hunting." |

### Implementation Notes

- GPS module (PA1010D) required — WiFi geolocation too imprecise for navigation (<50m accuracy needed)
- Treasure coordinates stored in flash — 12 bytes per treasure (lat: 4B, lon: 4B, type: 1B, timestamp: 3B)
- Compass calibration required on first use (figure-8 motion to calibrate magnetometer)
- Battery impact: GPS active during hunt draws ~25mA additional. Hunts should be time-limited (1 hour max active hunt)
- Anti-cheat: Verify GPS fix quality (HDOP < 5) before allowing collection

---

## 14. Step Target Rewards — Daily, Weekly, Monthly

### Daily Step Targets

Progressive daily goals with escalating rewards. The user can see their progress on the stats screen.

| Target | Steps | Reward | Dilder Reaction |
|--------|-------|--------|----------------|
| **Bronze** | 2,000 | +10 XP, +5 happiness | "Nice walk! My tentacles feel stretchy." |
| **Silver** | 5,000 | +25 XP, +10 happiness, 1 snack | "Great job! We really covered some ground!" |
| **Gold** | 8,000 | +50 XP, +15 happiness, random cosmetic chance (20%) | "Wow! You're a machine! ...a walking machine!" |
| **Platinum** | 12,000 | +100 XP, +20 happiness, guaranteed cosmetic | "LEGENDARY! My fitness stat is through the ROOF!" |
| **Diamond** | 20,000 | +200 XP, full stat restore, rare cosmetic | "I... I didn't know legs could DO that. Respect." |

**Daily bonus**: Completing any tier gives a "daily check" mark. Consecutive daily checks build the streak system (see below).

**Display on e-ink**:
```
┌──────────────────────────────────┐
│  Today's Steps: 6,247            │
│  ██████████████░░░░░ 8,000 Gold  │
│                                  │
│  ✓ Bronze (2,000)                │
│  ✓ Silver (5,000)                │
│  ○ Gold   (8,000) — 1,753 to go │
│  ○ Platinum (12,000)             │
│  ○ Diamond  (20,000)             │
└──────────────────────────────────┘
```

### Weekly Step Targets

Accumulate across the week (Monday-Sunday). Missed daily targets don't matter — only the weekly total counts.

| Target | Steps | Reward |
|--------|-------|--------|
| **Week Walker** | 10,000 | +50 XP, 3 snacks |
| **Week Runner** | 25,000 | +150 XP, random cosmetic, special weekly dialogue |
| **Week Warrior** | 50,000 | +400 XP, rare cosmetic, +1 decor slot unlock |
| **Week Legend** | 75,000 | +800 XP, legendary cosmetic, evolution XP bonus |
| **Week Titan** | 100,000+ | +1,500 XP, mythic reward, unique animation unlock |

**Weekly summary screen** (displayed Sunday evening or Monday morning):
```
┌──────────────────────────────────┐
│  WEEKLY SUMMARY                  │
│  Total Steps: 34,891             │
│  Rank: Week Runner ★★            │
│                                  │
│  Best Day: Thursday (8,234)      │
│  Rest Day: Sunday (1,102)        │
│  Daily Streak: 5 days            │
│                                  │
│  Dilder says: "We explored 3     │
│  new places this week!"          │
│  Reward: Ocean Sunset Background │
└──────────────────────────────────┘
```

### Monthly Step Targets

Accumulate across the calendar month. These are the "big goals" that drive long-term engagement.

| Target | Steps | Reward |
|--------|-------|--------|
| **Monthly Mover** | 50,000 | +200 XP, monthly badge, stat decay -10% for next month |
| **Monthly Marcher** | 100,000 | +500 XP, exclusive monthly cosmetic (unique per month) |
| **Monthly Marathoner** | 200,000 | +1,200 XP, evolution accelerator, rare animation |
| **Monthly Monster** | 300,000 | +2,500 XP, legendary monthly badge, permanent stat bonus |
| **Monthly Mythic** | 500,000+ | +5,000 XP, one-of-a-kind cosmetic, "Hall of Fame" entry |

**Monthly cosmetics are unique per calendar month** — miss April's exclusive hat and it's gone forever (FOMO-driven). This mirrors Neopets' limited-time items and Pokemon GO's Community Day exclusives.

**Monthly summary** includes:
- Total steps, daily average, best/worst day
- Locations visited count
- Care quality score (% of time with stats >50)
- Treasure hunts completed
- Life stage progress
- Comparison to previous month

### Streak System

Consecutive days of meeting the Bronze daily target (2,000 steps):

| Streak | Bonus |
|--------|-------|
| **3 days** | +25 XP, "Getting started!" badge |
| **7 days** | +100 XP, streak fire animation on step counter |
| **14 days** | +250 XP, happiness decay reduced by 10% |
| **30 days** | +750 XP, exclusive 30-day cosmetic, bond level boost |
| **60 days** | +2,000 XP, evolution guarantee (best path if stats allow) |
| **90 days** | +5,000 XP, "Legendary Companion" title, permanent stat bonus |
| **365 days** | +25,000 XP, "Eternal Bond" achievement, unique elder dialogue set |

**Streak protection**:
- **1 free miss per week**: Missing one day doesn't break the streak (grace day). Prevents frustration from illness/travel.
- **Streak freeze item**: Earned from treasure hunts. Allows 1 additional miss day. Stackable up to 3.
- **Partial credit**: Walking 1,000-1,999 steps counts as a "half day" — two half-days equal one full streak day.

### Step Target Gifts (Physical Rewards Concept)

At major milestones, the device displays a "gift box" animation. The user "opens" it by pressing a button, and the reward is revealed with a special animation sequence:

```
Frame 1: Gift box appears on screen
Frame 2: Dilder approaches the box, curious
Frame 3: Dilder taps the box with a tentacle
Frame 4: Box opens — sparkle effect (dithered stars)
Frame 5: Reward revealed with Dilder in Excited mood
Frame 6: Reward description + stat changes displayed
```

### Fitness Integration with Emotional State

Steps don't just give rewards — they continuously affect Dilder's mood:

| Daily Step Progress | Mood Modifier |
|--------------------|---------------|
| 0% of Bronze target | Lazy → Sad (progressive) |
| 25% (500 steps) | Neutral — no modifier |
| 50% (1,000 steps) | Slight happiness boost |
| 100% Bronze (2,000) | Chill mood more likely |
| 100% Silver (5,000) | Excited mood more likely, special "fit" dialogue |
| 100% Gold+ (8,000+) | Maximum happiness modifier, Dilder radiates confidence |

**Fitness stat** accumulates over weeks, affecting:
- Adult evolution options (Reef Guardian requires high fitness)
- Dialogue options ("Let's run!" vs "Let's nap..." depends on fitness history)
- Maximum energy stat (fitter Dilder has higher energy cap)
- Treasure hunt spawn radius (fitter = farther, rarer treasures)

---

## 15. Hardware Requirements & Cost

### Recommended Sensor Stack

| Component | Part | Interface | Cost (USD) | Priority |
|-----------|------|-----------|-----------|----------|
| **Accelerometer/Pedometer** | LIS2DH12TR | I2C (0x18) | ~$0.46 | High |
| **Capacitive Touch** | MPR121 (12-channel) | I2C (0x5A) | ~$4 | High |
| **Ambient Light** | BH1750 | I2C (0x23) | ~$2 | High |
| **Microphone** | MAX9814 (analog) | ADC (GP26) | ~$4 | High |
| **Temp/Humidity** | BME280 | I2C (0x76) | ~$4 | Medium |
| **Battery** | 1000mAh LiPo pouch | — | ~$5 | High |
| **Battery Management** | TP4056 with protection | USB-C input | ~$1.50 | High |
| **GPS (treasure hunt)** | PA1010D | I2C (0x10) | ~$12 | Medium |
| **Magnetometer (compass)** | QMC5883L or LIS3MDL | I2C (0x0D/0x1C) | ~$2-4 | Medium (with GPS) |
| **Gesture (optional)** | APDS-9960 | I2C (0x39) | ~$5 | Low |

### Cost Tiers

| Tier | Components | Total Cost |
|------|-----------|-----------|
| **Essential** | LIS2DH12TR + MPR121 + BH1750 + MAX9814 + Battery + TP4056 | **~$16.96** |
| **Recommended** | Essential + BME280 | **~$20.96** |
| **Explorer** | Recommended + QMC5883L (compass, WiFi/BLE location) | **~$24.96** |
| **Full** | Explorer + APDS-9960 + LIS3MDL upgrade | **~$33.96** |

*Costs are for breakout boards from AliExpress/generic sources. Adafruit/SparkFun branded boards typically 2-3x more.*

### I2C Bus Layout (No Address Conflicts)

```
Pico W I2C0 (GP4=SDA, GP5=SCL)
  ├── 0x10  PA1010D (GPS)
  ├── 0x23  BH1750  (Light)
  ├── 0x39  APDS-9960 (Gesture)
  ├── 0x5A  MPR121  (Touch)
  ├── 0x6A  LSM6DSO (Accel/Gyro/Pedometer)
  └── 0x76  BME280  (Temp/Humidity/Pressure)

ADC (GP26): MAX9814 microphone analog output
```

All sensors on a single I2C bus with no address conflicts. Pico W's I2C1 available as backup if needed.

### Power Budget

| Component | Active (mA) | Sleep (mA) |
|-----------|------------|-----------|
| Pico W (WiFi off) | 30 | 0.8 |
| E-ink display | 5 (refresh) / 0 (static) | 0 |
| LIS2DH12TR (pedometer mode) | 0.02 | 0.003 |
| MPR121 | 0.03 | 0.003 |
| BH1750 | 0.12 | 0.01 |
| MAX9814 | 3.0 | 0 (power gate) |
| BME280 | 0.004 | 0.0001 |
| **Total** | **~38 mA** | **~0.8 mA** |

**Battery life estimates (1000mAh LiPo)**:
- Active use: ~26 hours
- Intermittent use (50% active): ~40 hours
- Sleep mode (night): ~50+ days standby

### Alternative Accelerometer Options

If LSM6DSO is unavailable or too expensive:

| Part | Cost | Built-in Pedometer? | Notes |
|------|------|---------------------|-------|
| **BMA400** | ~$4 | Yes | Ultra-low power (14uA with step counter). Best power efficiency. |
| **LIS2DH12TR** | ~$0.46 | Yes (built-in pedometer) | Cheapest. Built-in step counter, LGA-12 (2x2mm), ultra-low power. **Selected for Dilder BOM.** |
| **LIS3DH** | ~$3 | No | Good low-power option. Hardware high-pass filter helps. |
| **ADXL345** | ~$3 | No | Activity/inactivity detection assists pedometer logic. |

**Recommendation**: LIS2DH12TR selected for Dilder — $0.46, built-in pedometer, ultra-low power, smallest footprint (LGA-12, 2x2mm). LSM6DSO or BMA400 are alternatives if 6-axis IMU is needed later.

### Software Step Counting Algorithm (for chips without built-in pedometer)

```
1. Sample accelerometer at 25-50Hz
2. Compute magnitude: mag = sqrt(ax² + ay² + az²)
3. Apply low-pass filter (moving average, ~10 samples)
4. Apply high-pass filter to remove gravity bias
5. Detect zero-crossings or peaks above threshold
6. Debounce: reject steps closer than 200ms apart
7. Timeout: reset if no step within 2 seconds
```

The Pico W's RP2040 at 133MHz handles this easily in C.

---

## 16. Research: Tamagotchi & Virtual Pet Precedents

### Original Tamagotchi (1996-1997)

The Tamagotchi established the virtual pet genre with these core mechanics:

**Stats**: Hunger (4 hearts), Happiness (4 hearts), Discipline (0-100%), Weight, Age.

**Stat Decay Rates** (character-specific, from community reverse-engineering):
- Baby (Babytchi): Hunger -1 heart every **3 minutes**, Happiness -1 every **4 minutes** — extremely needy
- Child (Marutchi): Hunger -1 every **50 min**, Happiness -1 every **60 min**
- Teen (Tamatchi): Hunger -1 every **75 min**, Happiness -1 every **85 min**
- Adult/Elderly: Decay accelerates, capping at -1 Hunger every **6 min**, -1 Happy every **7 min**

**Care Mechanics**:
- Feed a meal: +1 Hunger heart, +1 weight
- Feed a snack: +1 Happiness heart, +2 weight
- Play a game: Win 3/5 rounds → +1 Happy heart, -1 weight
- Discipline: +25% per correct scolding (4 windows per stage)
- Care mistake: Accrued when a need goes unmet for **15 minutes**. Irreversible. Shortens lifespan.
- Poop: Must be cleaned. 4+ accumulated → sickness.

**Life Stages & Timing**:
- Egg: 5 minutes
- Baby: 65 minutes (60 awake + 5 asleep). Nothing affects evolution.
- Child: Evolves at age 3 (~3 real days). Care mistakes start mattering.
- Teen: Evolves at age 6.
- Adult: Lives until death from age or neglect.
- Age increments: 1 year per real day (increments on wake).

**Evolution System** — Fully deterministic, no randomization:
- Child → Teen: 0-1 care mistakes → good teen; 2+ → bad teen
- Teen → Adult: Discipline determines tier (100% = best, 50% or less = worst)
- Secret character (Oyajitchi): Requires 0% discipline through multiple stages
- Each stage has exactly 4 misbehavior windows for discipline

**Death**: Occurs from old age, accumulated care mistakes (shortens lifespan), prolonged zero-stat neglect (~12+ hours with both Hunger and Happiness at 0), untreated sickness, or overfeeding baby (5+ snacks).

**Key Insight**: The deterministic evolution system gives players agency — they can deliberately aim for specific outcomes. Bad care isn't random bad luck; it's knowable cause and effect. This is more satisfying than random chance.

**References**:
- Thaao's Tamas P1 Care Guide: https://thaao.net/tama/p1/
- "I solved the original 1997 Tamagotchi": https://hive.blog/hive-140217/@mustachepod/i-solved-the-original-1997-tamagotchi
- tama96 Documentation: https://www.tama96.com/docs/

### Modern Tamagotchi (ON, Pix, Uni)

Key innovations in modern versions:
- **Gene Mixing** (m!x, ON): Marriage between two Tamagotchis produces offspring inheriting traits from both parents — body parts, eye shape, color. Creates billions of possible combinations.
- **Tamagotchi Uni**: Wi-Fi connectivity, downloadable content, online meeting spaces (Tamaverse), personality mechanics.
- **Social connectivity**: Marriage requires two physical devices to connect, creating a social layer.

### Digimon Virtual Pets

Key differences from Tamagotchi:
- **Battle-focused**: Two devices connect via conductors for battles. This was the core differentiator.
- **Evolution requires battles**: Ultimate level requires **15+ battles** at Rookie and Champion, winning **~60%**.
- **Less needy**: Could be left alone more than Tamagotchi. The care loop is lighter.
- **Win/loss ratio directly influences evolution paths** — combat skill matters.

**Relevance to Dilder**: The activity-based evolution (battles → evolution) is analogous to our step-based and exploration-based evolution. Physical effort should unlock growth.

### Neopets

- Browser-based virtual pet world. Peak: **35 million MAU** (2005), 150 million total registrations.
- **Player-driven economy**: Full marketplace with fluctuating item values, creating metagame depth.
- **Variety is key**: Hundreds of mini-games, customization options, events. Different player types find different things engaging.
- **FOMO-driven**: Limited-time events, exclusive releases, avatar hunts create urgency.

**Relevance to Dilder**: Collection mechanics and economic depth create long-term engagement. Even without multiplayer, the breadth of unlockables and achievements serves a similar function.

### Pou

- Mobile virtual pet with 4 status bars: hunger, health, happiness, sleep.
- **No permanent death**: Neglect makes Pou unwell but recovery is always possible.
- **Mini-games earn currency** for customization.
- **Key insight**: Removing permanent consequences reduces anxiety but maintains engagement through cosmetic goals and daily habits.

### My Talking Tom

- **Talk-back mechanic**: Records user speech, plays back in modified voice. Simple but extremely engaging — became franchise signature.
- **Growth stages**: Baby kitten → full-grown tomcat.
- **Extensive monetization** through cosmetics and virtual currency.

**Relevance to Dilder**: The mic echo/response concept could be adapted — Dilder "reacting" to voice input creates a sense of conversation even without speech recognition.

### Nintendogs (DS, 2005)

- **Touch-based petting**: DS stylus creates hand icon. Lifelike reactions depend on where/how you touch.
- **Voice recognition**: Microphone teaches dogs their name and tricks ("sit," "roll over"). Adapted to multiple languages and accents.
- **23.96 million copies sold** — demonstrated massive market for interactive pet simulation.

**Relevance to Dilder**: The capacitive touch zones directly mirror Nintendogs' touch interaction model. The voice element validates mic input as engaging.

### Creatures (1996 Artificial Life Game)

The most technically sophisticated virtual pet:
- **Neural network brain**: 952 neurons in 9 lobes, ~5,000 connections
- **Artificial biochemistry**: Simulated metabolism and hormones interact with neural network
- **Genuine learning**: Creatures learn through Hebbian reinforcement — reward/punishment chemicals shape behavior
- **Genetic DNA**: Sexual reproduction passes traits to offspring, enabling genuine evolution

**Relevance to Dilder**: While we can't replicate neural networks on a Pico W, the principle of **emergent behavior from simple rules** is key. Our stat-to-emotion mapping should produce surprising combinations.

### Finch (Modern Self-Care App)

- Virtual pet bird that grows based on completing daily wellness tasks.
- **Positive reinforcement only**: No penalties, no shame, no death.
- **Reframes obligation as nurturing**: Users complete self-care tasks "for their bird," not for themselves.
- **2.34 million downloads in 90 days**.

**Relevance to Dilder**: The real-world activity → pet benefit pipeline is exactly our model. Steps and exploration feed Dilder just as Finch ties self-care to pet growth. The "nurturing reframe" is powerful.

---

## 17. Research: Real-World Activity Games

### Pokemon GO

- **Adventure Sync**: Tracks walking distance via phone pedometer even when app is closed. Connects to Apple Health / Google Fit.
- **Buddy system**: Walking earns candy for a selected Pokemon. Distance tiers: 1, 3, 5, or 20 km per candy.
- **Egg hatching**: 2/5/7/10/12 km walking required. Speed cap of **~10.5 km/h** prevents driving.
- **Weekly rewards**: 5km = Poke Balls, 25km = Great Balls, 50km = Ultra Balls + rare items.
- **Over $6 billion lifetime revenue** — validates activity integration commercially.

**Relevance to Dilder**: The tiered step reward system and weekly milestones directly inform our step counter design. The speed cap concept could prevent "cheat shaking" of the accelerometer.

### Pikmin Bloom

- **Passive walking game**: Designed as background activity, not attention-demanding.
- **Flower planting**: Walking plants flowers on a real-world map, leaving colorful trails.
- **Decor Pikmin**: At high friendship, Pikmin get costumes based on **where their seedling was found** (restaurant → chef hat, park → clover). Encourages visiting diverse location types.
- **Lifelog**: Daily summary of where you walked. Weekly comparison.

**Relevance to Dilder**: The location-type-based cosmetics directly inspire our "location-themed unlocks." The ambient, background nature of engagement matches our always-on e-ink device.

### Walkr

- **Steps = spaceship fuel**: Phone pedometer converts daily steps into energy for galactic exploration.
- **100+ planets** to discover, each with a mini-ecosystem.
- **Co-pilots**: Friends provide extra fuel.

**Relevance to Dilder**: Shows that steps as a universal currency for progression works. The "fuel" abstraction is elegant — our equivalent is "Dilder's vitality."

---

## 18. Research: Voice Interaction in Games

### Hey You, Pikachu! (N64, 1998)

- Used VRU peripheral with **200-256 recognizable words**.
- Voice commands for simple actions: identify objects, direct Pikachu.
- **Frustration**: Unreliable recognition. Unclear if failures were tech limitations or intentional game mechanic (Pikachu being disobedient).
- **Lesson**: Voice input must have clear, forgiving interaction models. Ambiguity between "not recognized" and "pet chose to ignore" can be a feature, not a bug.

### Seaman (Dreamcast, 1999-2000)

- Fish-human hybrid that **speaks, asks personal questions, remembers answers**, evolves based on verbal interactions.
- Full conversational voice input via Dreamcast microphone.
- Creature's personality shaped by player's verbal interactions over time.
- Narrated by Leonard Nimoy.
- **Lesson**: Conversational depth creates deep attachment. Even primitive voice interaction feels magical when the pet seems to "listen."

### Design Patterns for Voice in Games (Academic Research)

A survey of 449 videogames using voice identified these categories:
- **Sound detection**: Any mic input triggers events (blowing, volume level)
- **Speech recognition**: Specific words mapped to commands
- **Voice as emotional input**: Tone/volume affects game state
- **Silence as mechanic**: Requiring players to stay quiet

**Relevance to Dilder**: On Pico W, we're limited to the first and third categories (sound detection, volume-as-emotion). This is actually sufficient for compelling interaction:
- Volume level → mood influence
- Duration of sound → attention metric
- Silence → loneliness metric
- Sudden spike → startle/discipline mechanic
- Rhythmic pattern → possible singing/music detection

---

## 19. Implementation Challenges

### Hardware Challenges

| Challenge | Severity | Mitigation |
|-----------|----------|-----------|
| **I2C bus reliability with many devices** | Medium | Keep wires short (<15cm), use pull-up resistors (4.7kΩ), scan bus on boot |
| **ADC noise from mic** | Medium | Add hardware LP filter (RC circuit) before ADC pin, software averaging |
| **Battery life optimization** | High | Aggressive sleep modes, sensor duty cycling, e-ink (no backlight drain) |
| **GPS power drain** | High | Defer to WiFi geolocation; GPS only on Phase 5 with larger battery |
| **Capacitive touch through case** | Medium | Test sensitivity per case material; adjustable thresholds in MPR121 registers |
| **Sensor wiring in small enclosure** | Medium | Use Qwiic/STEMMA QT connectors for I2C daisy chain; design PCB in Phase 5 |
| **Pico W RAM limits (264KB)** | Medium | Keep stat arrays compact, don't buffer full audio, stream sensor data |
| **E-ink refresh rate** | Low | Already handled — partial refresh works for 4s frame cycle |

### Software Challenges

| Challenge | Severity | Mitigation |
|-----------|----------|-----------|
| **State machine complexity** | High | Hierarchical FSM — top level (life stage), mid (activity state), low (emotion) |
| **Persistent storage** | High | Pico W flash wear leveling for stats/progress. Save every 5 min, not every tick. Use EEPROM-like library or flash filesystem (LittleFS). |
| **Step counting accuracy** | Medium | Use LIS2DH12TR built-in pedometer (hardware). If software: tune threshold per user weight/gait. |
| **WiFi geolocation latency** | Medium | Cache last-known location. Only re-resolve when WiFi environment changes significantly. |
| **Emotion blending algorithm** | Medium | Weight-based priority system with hysteresis (don't flip-flop between emotions). Minimum dwell time per emotion (30 seconds). |
| **Dialogue management** | Medium | Indexed quote arrays per mood/stage. Random selection with recency filter (don't repeat within last 10). |
| **Time tracking without NTP** | Low | RTC keeps time between reboots. Drift ~2 min/day acceptable. Sync via WiFi NTP when available. |
| **OTA firmware updates** | High (future) | Phase 5 — Pi Zero WH can pull updates from GitHub. Pico W OTA is possible but complex (dual-bank flash). |

### Design Challenges

| Challenge | Severity | Mitigation |
|-----------|----------|-----------|
| **Balancing punishment vs reward** | High | Default to Finch model (positive reinforcement). Neglect causes visible sadness but quick recovery. Death only from extreme sustained neglect (3+ days). |
| **Preventing cheat-shaking for steps** | Medium | Step detection algorithm with gait-pattern validation. Reject frequencies >4Hz (natural walking is 1.5-2.5Hz). |
| **Keeping dialogue fresh** | High | 800+ quotes already exist. Expand per life stage. Context-sensitive triggers prevent repetition. |
| **Evolution feeling meaningful** | High | Clear visual differences between adult forms. Unique dialogue sets per form. The journey matters — evolution is the payoff for weeks of care. |
| **Sensor data overwhelming the game loop** | Medium | Sample sensors on different tick intervals: touch (every tick), sound (every 100ms), light (every 5s), temp (every 60s), steps (hardware counter, read every 10s). |
| **Scope creep** | High | This document is intentionally comprehensive. Implementation must be phased ruthlessly. See Phase Rollout Plan below. |

---

## 20. Phased Rollout Plan

### Phase 3A: Core Game Loop (Immediate Priority)

**Goal**: Basic Tamagotchi functionality with stats and care actions.

| Task | Dependency |
|------|-----------|
| Implement stat system (hunger, happiness, energy, hygiene, health) | None |
| Implement stat decay with configurable rates | Stat system |
| Implement care actions via serial/GPIO buttons (feed, pet, clean, sleep) | Input system (Phase 2) |
| Implement emotion resolution from stats | Stat system + existing emotion renderer |
| Implement basic dialogue (mood-matched quotes already exist) | Emotion system |
| Implement day/night cycle from RTC | RTC (exists) |
| Persistent stat storage to flash | LittleFS or flash write |

### Phase 3B: Sensor Integration

**Goal**: Physical interaction through hardware sensors.

| Task | Hardware Needed |
|------|----------------|
| Integrate BH1750 light sensor → sleep/wake mechanics | BH1750 (~$2) |
| Integrate MPR121 touch → petting/interaction | MPR121 (~$4) |
| Integrate MAX9814 mic → volume-based reactions | MAX9814 (~$4) |
| Integrate BME280 temp/humidity → comfort mechanics | BME280 (~$4) |

### Phase 3C: Activity Tracking

**Goal**: Steps and location affect Dilder.

| Task | Hardware Needed |
|------|----------------|
| Integrate LIS2DH12TR step counter | LIS2DH12TR (~$0.46, on-board) |
| Implement step milestone rewards | LIS2DH12TR |
| Implement WiFi geolocation for location awareness | Built-in WiFi |
| Implement home detection and exploration tracking | WiFi |

### Phase 4: Progression & Life Stages

**Goal**: Long-term engagement systems.

| Task | Dependency |
|------|-----------|
| Implement life stage system (egg → elder) | Phase 3A |
| Implement evolution branching | Stat accumulation from Phase 3 |
| Implement bond level / XP system | Interaction tracking |
| Implement achievement system | All stat tracking |
| Implement decor/cosmetic unlocks | Achievement system |
| Implement dialogue per life stage | Life stage system |
| Implement rebirth system | Elder stage |

### Phase 4B: Treasure Hunts & Step Targets

**Goal**: GPS-based treasure hunting and structured step reward system.

| Task | Hardware Needed |
|------|----------------|
| Integrate PA1010D GPS module | PA1010D (~$12) |
| Integrate QMC5883L/LIS3MDL magnetometer for compass | QMC5883L (~$2) |
| Implement compass display with bearing calculation | GPS + Magnetometer |
| Implement treasure spawn system with rarity tiers | GPS + flash storage |
| Implement proximity detection and distance display | GPS |
| Implement daily/weekly/monthly step targets | LSM6DSO (from Phase 3C) |
| Implement streak system with grace days | Step tracking |
| Implement gift box animation sequence | Display renderer |
| Implement step target UI (progress bars, summaries) | Display renderer |

### Phase 5: Pi Zero WH Upgrade

**Goal**: Advanced features requiring more compute.

| Task | Hardware |
|------|---------|
| Speech recognition (cloud API or local keyword spotting) | Pi Zero WH + mic |
| Weather API integration | Pi Zero WH + internet |
| OTA firmware updates | Pi Zero WH |
| Enhanced location tracking (optional) | WiFi fingerprinting + BLE scanning (built-in) |
| Web dashboard / companion app | Pi Zero WH + WiFi |
| Social features (multiple Dilders interacting) | WiFi |

---

## 21. References

### Tamagotchi & Virtual Pet Research
- Thaao's Tamas P1 Care Guide — https://thaao.net/tama/p1/
- "I solved the original 1997 Tamagotchi" — https://hive.blog/hive-140217/@mustachepod/i-solved-the-original-1997-tamagotchi
- tama96 Documentation — https://www.tama96.com/docs/
- Tamagotchi Wiki (Care, Health Meter, Marriage, Genetics) — https://tamagotchi.fandom.com/
- Digimon V-Pet Guide — https://digivicemon.com/digimon-v-pet-guide-version-1/
- Creatures AI Analysis — https://www.alanzucconi.com/2020/07/27/the-ai-of-creatures/
- Neopets Engagement Design — https://www.deanagalbraith.com/post/designing-for-engagement-how-neopets-captivated-audiences-across-generations
- Pet Companion Design in Gamification (Yu-kai Chou) — https://yukaichou.com/advanced-gamification/the-pet-companion-design-in-gamification/

### Real-World Activity Integration
- Pokemon GO Adventure Sync — https://niantic.helpshift.com/hc/en/6-pokemon-go/faq/3265-adventure-sync/
- Pikmin Bloom — https://en.wikipedia.org/wiki/Pikmin_Bloom
- Walkr — https://sparkful.app/walkr
- Finch Self-Care App — https://apps.apple.com/us/app/finch-self-care-pet/id1528595748

### Voice Interaction
- 19 Games With Voice Commands — https://www.thegamer.com/games-with-voice-commands-speech-recognition/
- Design Patterns for Voice Interaction (ACM) — https://dl.acm.org/doi/10.1145/3242671.3242712
- Technology Behind Nintendogs — https://www.thetechedvocate.org/the-technology-behind-nintendogs-pushing-the-nintendo-ds-to-its-limits/

### Hardware Datasheets
- Raspberry Pi Pico W — https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf
- RP2040 — https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
- LSM6DSO — https://www.st.com/en/mems-and-sensors/lsm6dso.html
- MPR121 — https://www.adafruit.com/product/1982
- BH1750 — https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf
- MAX9814 — https://www.adafruit.com/product/1713
- BME280 — https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/
- PA1010D GPS — https://www.adafruit.com/product/4415
- APDS-9960 — https://www.adafruit.com/product/3595

### Game Design & Retention
- UX Principles for Pet Care Systems — https://www.zigpoll.com/content/what-key-ux-principles-should-i-prioritize-when-designing-an-ingame-pet-care-system-to-maximize-player-engagement-and-satisfaction
- Game Retention Strategies — https://featureupvote.com/blog/game-retention/

---

*Document version: 1.0 — Created 2026-04-13*
*This is a living document. Update as implementation progresses and design decisions are made.*
