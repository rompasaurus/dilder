# Emotion Engine

> Emotion resolution algorithm, trigger evaluation, weight blending, transitions, and sensor-to-emotion mapping.

---

## Table of Contents

1. [Data Structures](#1-data-structures)
2. [Emotion Trigger Table](#2-emotion-trigger-table)
3. [Resolution Algorithm](#3-resolution-algorithm)
4. [Sensor-Driven Modifiers](#4-sensor-driven-modifiers)
5. [Blending & Transitions](#5-blending--transitions)
6. [Forced Emotions & Overrides](#6-forced-emotions--overrides)

---

## 1. Data Structures

```c
typedef enum {
    EMOTION_NORMAL,       // 0  — All stats balanced, default personality
    EMOTION_HUNGRY,       // 1  — Hunger < 20
    EMOTION_TIRED,        // 2  — Energy < 15
    EMOTION_SAD,          // 3  — Happiness < 20
    EMOTION_ANGRY,        // 4  — Scolded harshly, shaken, extreme neglect
    EMOTION_EXCITED,      // 5  — Just fed when hungry, milestone reached
    EMOTION_CHILL,        // 6  — All stats > 60, calm environment
    EMOTION_LAZY,         // 7  — Low energy, no interaction for 2+ hours
    EMOTION_FAT,          // 8  — Weight > threshold
    EMOTION_CHAOTIC,      // 9  — Rapidly changing inputs, conflicting stats
    EMOTION_WEIRD,        // 10 — Random trigger when bored
    EMOTION_UNHINGED,     // 11 — Health < 20, multiple stats critical
    EMOTION_SLAP_HAPPY,   // 12 — Happiness > 90 after being < 30
    EMOTION_CREEPY,        // 13 — Specific stage + happiness > 70
    EMOTION_NOSTALGIC,    // 14 — Age milestone, familiar location
    EMOTION_HOMESICK,     // 15 — Away from home WiFi for extended period
    EMOTION_COUNT
} emotion_id_t;

typedef struct {
    emotion_id_t current;       // Active displayed emotion
    emotion_id_t previous;      // Last emotion (for transition animation)
    float        weights[EMOTION_COUNT];  // Current weight per emotion
    float        current_weight;          // Weight of active emotion
    uint32_t     dwell_start_ms;          // When current emotion began
    uint32_t     min_dwell_ms;            // Minimum time before switching (30s default)
    bool         changed;                 // True if emotion changed this tick
    bool         in_transition;           // Currently blending between two
    bool         forced;                  // Override active (e.g., care response)
    uint32_t     force_end_ms;            // When forced override expires
} emotion_state_t;
```

---

## 2. Emotion Trigger Table

Each emotion has a primary trigger function and optional secondary conditions:

```c
typedef struct {
    emotion_id_t id;
    float (*evaluate)(const stats_t *stats,
                      const sensor_context_t *ctx,
                      const event_record_t *recent_events,
                      const life_state_t *life);
    float priority;           // Tie-breaker: higher priority wins when weights equal
    uint32_t min_dwell_ms;    // Minimum display time before allowing switch
} emotion_trigger_t;

// ─── Trigger Evaluation Functions ────────────────────────────

float eval_normal(const stats_t *s, const sensor_context_t *ctx,
                  const event_record_t *ev, const life_state_t *life) {
    // Default fallback — weight increases when no other emotion is strong
    primary_stats_t *p = &s->primary;
    if (p->hunger >= 40 && p->hunger <= 80 &&
        p->happiness >= 40 && p->happiness <= 80 &&
        p->energy >= 40 && p->energy <= 80 &&
        p->hygiene >= 40) {
        return 0.5f;  // Moderate weight when balanced
    }
    return 0.1f;  // Low weight otherwise
}

float eval_hungry(const stats_t *s, const sensor_context_t *ctx,
                  const event_record_t *ev, const life_state_t *life) {
    if (s->primary.hunger < 10) return 0.95f;       // Starving → very strong
    if (s->primary.hunger < 20) return 0.8f;        // Hungry
    if (s->primary.hunger < 30) return 0.3f;        // Getting hungry
    return 0.0f;
}

float eval_tired(const stats_t *s, const sensor_context_t *ctx,
                 const event_record_t *ev, const life_state_t *life) {
    float weight = 0.0f;
    if (s->primary.energy < 10) weight = 0.9f;
    else if (s->primary.energy < 15) weight = 0.7f;
    else if (s->primary.energy < 25) weight = 0.3f;

    // Boost if it's late at night
    if (ctx->light.lux < 50) weight += 0.15f;

    return fminf(weight, 1.0f);
}

float eval_sad(const stats_t *s, const sensor_context_t *ctx,
               const event_record_t *ev, const life_state_t *life) {
    float weight = 0.0f;
    if (s->primary.happiness < 10) weight = 0.9f;
    else if (s->primary.happiness < 20) weight = 0.75f;
    else if (s->primary.happiness < 30) weight = 0.3f;

    // Boost from neglect streak (no interaction for 4+ hours)
    uint32_t idle_ms = time_mgr_now_ms() - s->hidden.last_interaction_ms;
    if (idle_ms > 4 * 3600 * 1000) weight += 0.2f;

    return fminf(weight, 1.0f);
}

float eval_angry(const stats_t *s, const sensor_context_t *ctx,
                 const event_record_t *ev, const life_state_t *life) {
    float weight = 0.0f;

    // Recent incorrect scold
    if (event_recent(ev, EVENT_SCOLDED, 30000)) weight += 0.7f;

    // Shaken violently
    if (ctx->accel.shaking) weight += 0.6f;

    // Extreme hunger + low happiness combo
    if (s->primary.hunger < 10 && s->primary.happiness < 30) weight += 0.5f;

    return fminf(weight, 1.0f);
}

float eval_excited(const stats_t *s, const sensor_context_t *ctx,
                   const event_record_t *ev, const life_state_t *life) {
    float weight = 0.0f;

    // Just fed when very hungry (relief/gratitude)
    if (event_recent(ev, EVENT_FED, 10000) && s->primary.hunger > 50) {
        weight += 0.8f;
    }

    // Step milestone just reached
    if (event_recent(ev, EVENT_STEP_MILESTONE, 30000)) weight += 0.7f;

    // Achievement unlocked
    if (event_recent(ev, EVENT_ACHIEVEMENT_UNLOCK, 30000)) weight += 0.8f;

    return fminf(weight, 1.0f);
}

float eval_chill(const stats_t *s, const sensor_context_t *ctx,
                 const event_record_t *ev, const life_state_t *life) {
    primary_stats_t *p = &s->primary;
    if (p->hunger > 60 && p->happiness > 60 && p->energy > 60 &&
        p->hygiene > 60 && p->health > 60) {
        float weight = 0.6f;
        // Boost in calm environment
        if (ctx->mic.level < MIC_QUIET_THRESHOLD) weight += 0.1f;
        if (ctx->temperature.celsius >= 18.0f &&
            ctx->temperature.celsius <= 24.0f) weight += 0.1f;
        return weight;
    }
    return 0.0f;
}

float eval_lazy(const stats_t *s, const sensor_context_t *ctx,
                const event_record_t *ev, const life_state_t *life) {
    // Energy 15-30, no interaction for 2+ hours
    if (s->primary.energy >= 15 && s->primary.energy <= 30) {
        uint32_t idle_ms = time_mgr_now_ms() - s->hidden.last_interaction_ms;
        if (idle_ms > 2 * 3600 * 1000) return 0.65f;
    }
    // Overfed
    if (s->secondary.weight > 130) return 0.5f;
    return 0.0f;
}

float eval_fat(const stats_t *s, const sensor_context_t *ctx,
               const event_record_t *ev, const life_state_t *life) {
    if (s->secondary.weight > 130) return 0.7f;
    if (s->secondary.weight > 120) return 0.3f;
    return 0.0f;
}

float eval_chaotic(const stats_t *s, const sensor_context_t *ctx,
                   const event_record_t *ev, const life_state_t *life) {
    // Count recent events in last 30 seconds
    int event_count = event_count_recent(ev, 30000);
    if (event_count >= 5) return 0.8f;  // Lots happening at once

    // Shaken + loud noise simultaneously
    if (ctx->accel.shaking && ctx->mic.level > MIC_YELL_THRESHOLD) return 0.9f;

    return 0.0f;
}

float eval_weird(const stats_t *s, const sensor_context_t *ctx,
                 const event_record_t *ev, const life_state_t *life) {
    // 5% chance per emotion tick if bored (low interaction, moderate stats)
    uint32_t idle_ms = time_mgr_now_ms() - s->hidden.last_interaction_ms;
    bool bored = idle_ms > 1 * 3600 * 1000 &&
                 s->primary.happiness >= 30 && s->primary.happiness <= 60;
    if (bored) {
        // Deterministic "random" based on tick count to avoid true RNG
        uint32_t tick = time_mgr_now_ms() / 5000;  // 5-second emotion tick
        if ((tick * 2654435761u) % 20 == 0) return 0.6f;  // ~5% chance
    }
    return 0.0f;
}

float eval_unhinged(const stats_t *s, const sensor_context_t *ctx,
                    const event_record_t *ev, const life_state_t *life) {
    // Health < 20 AND multiple stats critical
    int critical = 0;
    if (s->primary.hunger < 20) critical++;
    if (s->primary.happiness < 20) critical++;
    if (s->primary.energy < 15) critical++;
    if (s->primary.hygiene < 25) critical++;

    if (s->primary.health < 20 && critical >= 2) return 0.9f;
    if (s->primary.health < 30 && critical >= 3) return 0.7f;
    return 0.0f;
}

float eval_slap_happy(const stats_t *s, const sensor_context_t *ctx,
                      const event_record_t *ev, const life_state_t *life) {
    // Happiness > 90 after recently being < 30
    // Track via recent EVENT_STAT_RECOVERED for happiness
    if (s->primary.happiness > 90 &&
        event_recent(ev, EVENT_STAT_RECOVERED, 300000)) {  // Within 5 min
        return 0.85f;
    }
    return 0.0f;
}

float eval_creepy(const stats_t *s, const sensor_context_t *ctx,
                 const event_record_t *ev, const life_state_t *life) {
    // Only adolescent or adult, happiness > 70, bond > threshold
    if ((life->stage == LIFE_STAGE_ADOLESCENT || life->stage == LIFE_STAGE_ADULT) &&
        s->primary.happiness > 70 && s->secondary.bond_xp > 4000) {
        // Low probability trigger
        uint32_t tick = time_mgr_now_ms() / 5000;
        if ((tick * 2654435761u) % 50 == 0) return 0.6f;  // ~2% chance
    }
    return 0.0f;
}

float eval_nostalgic(const stats_t *s, const sensor_context_t *ctx,
                     const event_record_t *ev, const life_state_t *life) {
    // Age milestone (every 7 days)
    if (life->age_seconds > 0 && (life->age_seconds % (7 * 86400)) < 60) {
        return 0.7f;
    }
    // Returned to familiar location
    if (event_recent(ev, EVENT_HOME_ARRIVED, 60000)) return 0.5f;
    return 0.0f;
}

float eval_homesick(const stats_t *s, const sensor_context_t *ctx,
                    const event_record_t *ev, const life_state_t *life) {
    // Away from home WiFi for > 4 hours
    if (ctx->wifi.away_from_home && ctx->wifi.away_duration_ms > 4 * 3600 * 1000) {
        return 0.7f;
    }
    // First time at new location (brief trigger)
    if (event_recent(ev, EVENT_NEW_LOCATION, 300000)) return 0.3f;
    return 0.0f;
}
```

### Trigger Registration Table

```c
static const emotion_trigger_t TRIGGERS[] = {
    //  id                evaluate         priority  min_dwell
    { EMOTION_UNHINGED,   eval_unhinged,   10.0f,    60000 },  // Highest priority
    { EMOTION_ANGRY,      eval_angry,       9.0f,    30000 },
    { EMOTION_HUNGRY,     eval_hungry,      8.0f,    30000 },
    { EMOTION_TIRED,      eval_tired,       7.5f,    30000 },
    { EMOTION_SAD,        eval_sad,          7.0f,    30000 },
    { EMOTION_EXCITED,    eval_excited,      6.5f,    15000 },  // Short dwell
    { EMOTION_SLAP_HAPPY, eval_slap_happy,  6.0f,    20000 },
    { EMOTION_CHAOTIC,    eval_chaotic,      5.5f,    10000 },  // Very short
    { EMOTION_HOMESICK,   eval_homesick,     5.0f,    45000 },
    { EMOTION_NOSTALGIC,  eval_nostalgic,    4.5f,    30000 },
    { EMOTION_FAT,        eval_fat,          4.0f,    30000 },
    { EMOTION_LAZY,       eval_lazy,         3.5f,    30000 },
    { EMOTION_CREEPY,      eval_creepy,        3.0f,    20000 },
    { EMOTION_WEIRD,      eval_weird,        2.5f,    20000 },
    { EMOTION_CHILL,      eval_chill,        2.0f,    30000 },
    { EMOTION_NORMAL,     eval_normal,       1.0f,    30000 },  // Lowest priority
};
```

---

## 3. Resolution Algorithm

```c
void emotion_resolve(emotion_state_t *state, const stats_t *stats,
                     const sensor_context_t *ctx,
                     const event_record_t *recent_events,
                     const life_state_t *life) {
    uint32_t now = time_mgr_now_ms();

    // Skip if forced override is active
    if (state->forced && now < state->force_end_ms) return;
    state->forced = false;

    // Skip if within minimum dwell period
    if (now - state->dwell_start_ms < state->min_dwell_ms) return;

    // Phase 1: Evaluate all trigger weights
    for (int i = 0; i < EMOTION_COUNT; i++) {
        state->weights[i] = TRIGGERS[i].evaluate(stats, ctx, recent_events, life);
    }

    // Phase 2: Life stage gating
    // Hatchlings can only express: normal, hungry, tired, sad, excited
    if (life->stage == LIFE_STAGE_HATCHLING) {
        for (int i = 0; i < EMOTION_COUNT; i++) {
            if (i != EMOTION_NORMAL && i != EMOTION_HUNGRY &&
                i != EMOTION_TIRED && i != EMOTION_SAD &&
                i != EMOTION_EXCITED) {
                state->weights[i] = 0.0f;
            }
        }
    }
    // Juveniles add: chill, lazy, angry, weird
    else if (life->stage == LIFE_STAGE_JUVENILE) {
        state->weights[EMOTION_CREEPY] = 0.0f;
        state->weights[EMOTION_NOSTALGIC] = 0.0f;
        state->weights[EMOTION_UNHINGED] = 0.0f;
    }
    // Adolescents and above: all 16 emotions available

    // Phase 3: Find winning emotion (highest weight, priority as tiebreaker)
    emotion_id_t winner = EMOTION_NORMAL;
    float max_weight = 0.0f;
    float max_priority = 0.0f;

    for (int i = 0; i < EMOTION_COUNT; i++) {
        if (state->weights[i] > max_weight ||
            (state->weights[i] == max_weight &&
             TRIGGERS[i].priority > max_priority)) {
            max_weight = state->weights[i];
            max_priority = TRIGGERS[i].priority;
            winner = TRIGGERS[i].id;
        }
    }

    // Phase 4: Hysteresis — require new emotion to beat current by margin
    #define HYSTERESIS_MARGIN 0.15f

    if (winner != state->current) {
        float current_weight = state->weights[state->current];
        if (max_weight < current_weight + HYSTERESIS_MARGIN) {
            // Not strong enough to overcome current — stay
            return;
        }
    } else {
        // Same emotion — no transition needed
        state->changed = false;
        return;
    }

    // Phase 5: Transition
    state->previous = state->current;
    state->current = winner;
    state->current_weight = max_weight;
    state->dwell_start_ms = now;
    state->min_dwell_ms = TRIGGERS[winner].min_dwell_ms;
    state->changed = true;
    state->in_transition = true;  // UI will animate the blend
}
```

---

## 4. Sensor-Driven Modifiers

Sensors modify emotion weights as additive bonuses applied during evaluation:

```c
// These modifiers are folded into the eval_* functions above, but
// documented here for clarity on the sensor → emotion mapping.

typedef struct {
    // Light
    float light_energy_boost;   // Bright → +energy feel → less tired weight
    float dark_tired_boost;     // Dark → +tired weight

    // Sound
    float loud_startle;         // Spike → brief excited or angry
    float talking_happy;        // Sustained mid → +happy, +intelligence
    float silence_lonely;       // Long silence → +sad, +homesick

    // Interaction
    float comfort_happy;        // Center button comfort → +happy weight
    float accel_tap_annoy;      // Rapid accelerometer taps → +angry weight

    // Motion
    float walking_happy;        // Steps → +happy, +excited weight
    float shaking_chaotic;      // Violent shake → +chaotic, +angry
    float stillness_lazy;       // Long stillness → +lazy, +bored

    // Temperature
    float cold_sad;             // < 15C → +sad weight
    float hot_angry;            // > 28C → +angry weight
    float comfortable_chill;    // 18-24C → +chill weight
} sensor_emotion_modifiers_t;

// Applied inside each eval_* function as additive weight adjustments.
// Example in eval_chill():
//   if (ctx->temperature.celsius >= 18 && ctx->temperature.celsius <= 24)
//       weight += 0.1f;   // comfortable_chill modifier
```

---

## 5. Blending & Transitions

### Transition Animation

Emotions don't snap on e-ink. The UI layer handles the visual blend:

```c
typedef struct {
    emotion_id_t from;
    emotion_id_t to;
    uint8_t      frame;        // 0 = current face, 1 = neutral/pause, 2 = new face
    uint32_t     frame_start_ms;
    uint32_t     frame_duration_ms;  // ~4000ms per frame (e-ink refresh speed)
} emotion_transition_t;

void emotion_transition_update(emotion_transition_t *trans, uint32_t now) {
    if (!trans->active) return;

    uint32_t elapsed = now - trans->frame_start_ms;
    if (elapsed >= trans->frame_duration_ms) {
        trans->frame++;
        trans->frame_start_ms = now;

        if (trans->frame > 2) {
            // Transition complete
            trans->active = false;
        }
    }
}

// Frame rendering:
// Frame 0: Current emotion face (already displayed)
// Frame 1: Neutral/blank expression (brief pause — ~2 seconds)
// Frame 2: New emotion face renders
//
// Total transition time: ~8-12 seconds depending on e-ink refresh
```

### Minimum Dwell Time

Prevents emotion flickering. Each emotion defines its own minimum:

```
UNHINGED:    60s   — Player should see the distress clearly
ANGRY:       30s   — Strong emotion, needs to register
HUNGRY:      30s   — Needs to be noticed
SAD:         30s   — Lingering emotion
EXCITED:     15s   — Brief burst is natural
CHAOTIC:     10s   — Chaos is fleeting by design
CHILL:       30s   — Relaxed state should persist
NORMAL:      30s   — Default state stability
```

---

## 6. Forced Emotions & Overrides

Some game events need to override the natural emotion resolution:

```c
// Force an emotion for a fixed duration (overrides normal resolution)
void emotion_force(emotion_state_t *state, emotion_id_t emotion,
                   uint32_t duration_ms) {
    state->previous = state->current;
    state->current = emotion;
    state->forced = true;
    state->force_end_ms = time_mgr_now_ms() + duration_ms;
    state->changed = true;
    state->in_transition = true;
}
```

### When to Force

```c
// Care action responses (immediate visual feedback)
void on_care_action(care_action_t action) {
    switch (action) {
        case CARE_FEED_MEAL:
        case CARE_FEED_SNACK:
            emotion_force(&game.emotion, EMOTION_EXCITED, 10000);  // 10s happy eating
            break;
        case CARE_PET:
            emotion_force(&game.emotion, EMOTION_CHILL, 8000);     // 8s relaxed
            break;
        case CARE_PLAY:
            emotion_force(&game.emotion, EMOTION_EXCITED, 15000);  // 15s play excitement
            break;
        case CARE_SCOLD:
            emotion_force(&game.emotion, EMOTION_ANGRY, 5000);     // 5s angry (correct)
            // or EMOTION_SAD for 8000ms if incorrect scold
            break;
        case CARE_MEDICINE:
            emotion_force(&game.emotion, EMOTION_SAD, 5000);       // 5s — medicine is yucky
            break;
    }
}

// Sensor shock responses
void on_sensor_event(event_type_t type) {
    switch (type) {
        case EVENT_DROPPED:
            emotion_force(&game.emotion, EMOTION_CHAOTIC, 8000);
            break;
        case EVENT_LOUD_NOISE:
            emotion_force(&game.emotion, EMOTION_EXCITED, 5000);  // Startled
            break;
    }
}
```

---

### Emotion API Summary

```c
// ─── Public Interface (emotion.h) ────────────────────────────

// Initialization
void emotion_init(emotion_state_t *state);

// Per-tick resolution (called every TICK_RATE_EMOTION ticks)
void emotion_resolve(emotion_state_t *state, const stats_t *stats,
                     const sensor_context_t *ctx,
                     const event_record_t *recent_events,
                     const life_state_t *life);

// Force override
void emotion_force(emotion_state_t *state, emotion_id_t emotion,
                   uint32_t duration_ms);

// Transition animation
void emotion_transition_update(emotion_transition_t *trans, uint32_t now);

// Queries
emotion_id_t emotion_current(const emotion_state_t *state);
bool         emotion_changed(const emotion_state_t *state);
bool         emotion_in_transition(const emotion_state_t *state);
float        emotion_weight(const emotion_state_t *state, emotion_id_t id);

// Event handlers (registered on game init)
void emotion_on_stat_critical(event_type_t type, const event_data_t *data);
void emotion_on_care_action(event_type_t type, const event_data_t *data);
void emotion_on_sensor_event(event_type_t type, const event_data_t *data);
```

---

*Next: [04-sensor-interfaces.md](04-sensor-interfaces.md) — Hardware abstraction for all sensors and polling strategy.*