/*
 * emotion.c -- Emotion Resolution Engine
 *
 * This module determines which emotion the Dilder creature is currently
 * feeling. It works like a scoring contest: every tick, each possible
 * emotion gets a "weight" (0.0 to 1.0) that says how strongly the
 * creature should feel that way right now. The emotion with the highest
 * weight wins and becomes the active emotion.
 *
 * Key concepts used in this file:
 *   - Function pointers (eval_fn_t): each emotion has its own evaluator
 *     function stored in a table. The engine loops through the table and
 *     *calls* each function through its pointer -- this avoids a giant
 *     if/else chain and makes it easy to add new emotions.
 *   - Hysteresis: the system resists rapid emotion flickering by requiring
 *     a new emotion to beat the current one by a margin before switching.
 *   - static functions: every eval_* function is declared `static`, which
 *     means it is only visible inside this file. This is C's way of making
 *     something "private" -- other files cannot call these directly.
 *   - extern: used to reference the global game state (g_game) that lives
 *     in another translation unit (another .c file).
 */

#include "game/emotion.h"
#include "game/event.h"
#include "game/time_mgr.h"
#include <math.h>

/* ─── Trigger Evaluation Functions ─────────────────────────────
 *
 * Each eval_* function below takes a snapshot of the creature's stats,
 * the current sensor readings, and the life-stage info, then returns
 * a float between 0.0 (not relevant at all) and 1.0 (strongly triggered).
 *
 * All of them share the same signature so they can be stored in a
 * function-pointer table (see TRIGGERS[] further down).
 *
 * Parameters (same for every eval_* function):
 *   s    -- pointer to the creature's stats (hunger, happiness, etc.)
 *   ctx  -- pointer to sensor data (light, accelerometer, mic, etc.)
 *   life -- pointer to life-stage state (egg, hatchling, adult, etc.)
 *
 * Return: a float weight [0.0 .. 1.0] indicating how strongly this
 *         emotion should be active right now.
 */

/*
 * eval_normal -- The default/baseline emotion.
 * Returns 0.5 (moderate) when all primary stats are in a comfortable
 * middle range, otherwise returns a low baseline of 0.1. This ensures
 * NORMAL always has *some* weight as a fallback.
 */
static float eval_normal(const stats_t *s, const sensor_context_t *ctx,
                         const life_state_t *life) {
    /*
     * &s->primary: takes the address of the `primary` sub-struct inside `s`.
     * Using a local pointer `p` is just for convenience -- shorter to type
     * `p->hunger` than `s->primary.hunger` over and over. `p` lives on the
     * stack and costs nothing extra at runtime.
     */
    const primary_stats_t *p = &s->primary;
    if (p->hunger >= 40 && p->hunger <= 80 &&
        p->happiness >= 40 && p->happiness <= 80 &&
        p->energy >= 40 && p->energy <= 80 &&
        p->hygiene >= 40) {
        return 0.5f;
    }
    return 0.1f;  /* always provide a small weight so NORMAL can still win if nothing else triggers */
}

/*
 * eval_hungry -- Triggers when the creature's hunger stat is low.
 * Lower hunger = stronger weight, using a tiered threshold approach.
 */
static float eval_hungry(const stats_t *s, const sensor_context_t *ctx,
                         const life_state_t *life) {
    if (s->primary.hunger < 10) return 0.95f;  /* critically hungry */
    if (s->primary.hunger < 20) return 0.8f;   /* very hungry */
    if (s->primary.hunger < 30) return 0.3f;   /* a little hungry */
    return 0.0f;                                /* not hungry at all */
}

/*
 * eval_tired -- Triggers when energy is low, boosted by dim lighting.
 * Combines stat thresholds with environmental context (light level).
 */
static float eval_tired(const stats_t *s, const sensor_context_t *ctx,
                        const life_state_t *life) {
    float w = 0.0f;  /* accumulator -- we add contributions from multiple sources */
    if (s->primary.energy < 10) w = 0.9f;
    else if (s->primary.energy < 15) w = 0.7f;
    else if (s->primary.energy < 25) w = 0.3f;

    if (ctx->light.lux < 50.0f) w += 0.15f;  /* dark room makes tiredness more likely */
    /*
     * fminf_safe() clamps w to a maximum of 1.0 so the weight never
     * exceeds the valid range. It's a safe wrapper around fminf() that
     * handles NaN edge cases.
     */
    return fminf_safe(w, 1.0f);
}

/*
 * eval_sad -- Triggers when happiness is low, boosted by long idle time
 * (no user interaction).
 */
static float eval_sad(const stats_t *s, const sensor_context_t *ctx,
                      const life_state_t *life) {
    float w = 0.0f;
    if (s->primary.happiness < 10) w = 0.9f;
    else if (s->primary.happiness < 20) w = 0.75f;
    else if (s->primary.happiness < 30) w = 0.3f;

    /*
     * Calculate how long since the user last interacted, in milliseconds.
     * time_mgr_now_ms() returns the current time as a uint32_t (unsigned
     * 32-bit integer). Subtracting two uint32_t values works correctly
     * even if the timer wraps around (unsigned arithmetic wraps modulo 2^32).
     */
    uint32_t idle_ms = time_mgr_now_ms() - s->hidden.last_interaction_ms;
    /*
     * 4 * 3600 * 1000 = 14,400,000 ms = 4 hours.
     * If the user hasn't interacted for over 4 hours, sadness increases.
     */
    if (idle_ms > 4 * 3600 * 1000) w += 0.2f;

    return fminf_safe(w, 1.0f);
}

/*
 * eval_angry -- Triggers from scolding, device shaking, or combined
 * hunger + unhappiness. Multiple triggers can stack.
 */
static float eval_angry(const stats_t *s, const sensor_context_t *ctx,
                        const life_state_t *life) {
    float w = 0.0f;
    /*
     * event_recent() checks if a specific event happened within the last
     * N milliseconds. Here: was the creature scolded in the last 30 seconds?
     */
    if (event_recent(EVENT_SCOLDED, 30000)) w += 0.7f;
    if (ctx->accel.shaking) w += 0.6f;             /* device is being shaken */
    if (s->primary.hunger < 10 && s->primary.happiness < 30) w += 0.5f;  /* hangry */
    return fminf_safe(w, 1.0f);
}

/*
 * eval_excited -- Triggers from positive events: being fed when hungry,
 * hitting a step milestone, or unlocking an achievement.
 */
static float eval_excited(const stats_t *s, const sensor_context_t *ctx,
                          const life_state_t *life) {
    float w = 0.0f;
    if (event_recent(EVENT_FED, 10000) && s->primary.hunger > 50) w += 0.8f;
    if (event_recent(EVENT_STEP_MILESTONE, 30000)) w += 0.7f;
    if (event_recent(EVENT_ACHIEVEMENT_UNLOCK, 30000)) w += 0.8f;
    return fminf_safe(w, 1.0f);
}

/*
 * eval_chill -- Triggers when all stats are above 60 (creature is
 * content), boosted by quiet environment and comfortable temperature.
 */
static float eval_chill(const stats_t *s, const sensor_context_t *ctx,
                        const life_state_t *life) {
    const primary_stats_t *p = &s->primary;  /* convenience pointer (see eval_normal for explanation) */
    if (p->hunger > 60 && p->happiness > 60 && p->energy > 60 &&
        p->hygiene > 60 && p->health > 60) {
        float w = 0.6f;
        if (ctx->mic.level < 50) w += 0.1f;   /* quiet environment */
        if (ctx->env.celsius >= 18.0f && ctx->env.celsius <= 24.0f) w += 0.1f;  /* comfortable temp */
        return w;
    }
    return 0.0f;
}

/*
 * eval_lazy -- Triggers when energy is in the 15-30 "meh" range and the
 * user hasn't interacted for a while, or when the creature is overweight.
 */
static float eval_lazy(const stats_t *s, const sensor_context_t *ctx,
                       const life_state_t *life) {
    if (s->primary.energy >= 15 && s->primary.energy <= 30) {
        uint32_t idle_ms = time_mgr_now_ms() - s->hidden.last_interaction_ms;
        /* 2 * 3600 * 1000 = 7,200,000 ms = 2 hours idle */
        if (idle_ms > 2 * 3600 * 1000) return 0.65f;
    }
    if (s->secondary.weight > 130) return 0.5f;  /* overweight contributes to laziness */
    return 0.0f;
}

/*
 * eval_fat -- Triggers based purely on the creature's weight stat.
 * Higher weight = higher probability of showing the "fat" emotion.
 */
static float eval_fat(const stats_t *s, const sensor_context_t *ctx,
                      const life_state_t *life) {
    if (s->secondary.weight > 130) return 0.7f;  /* very overweight */
    if (s->secondary.weight > 120) return 0.3f;  /* somewhat overweight */
    return 0.0f;
}

/*
 * eval_chaotic -- Triggers when lots of events are happening at once
 * (5+ events in 30 seconds) or when the device is being shaken AND
 * the environment is loud.
 */
static float eval_chaotic(const stats_t *s, const sensor_context_t *ctx,
                          const life_state_t *life) {
    int ec = event_count_recent(30000);  /* count events in last 30 seconds */
    if (ec >= 5) return 0.8f;
    if (ctx->accel.shaking && ctx->mic.level > 2000) return 0.9f;  /* shaking + loud = chaos */
    return 0.0f;
}

/*
 * eval_weird -- Triggers randomly when the creature is bored (idle for
 * over an hour, happiness in the "meh" range).
 *
 * Uses a pseudo-random number trick to fire occasionally.
 */
static float eval_weird(const stats_t *s, const sensor_context_t *ctx,
                        const life_state_t *life) {
    uint32_t idle_ms = time_mgr_now_ms() - s->hidden.last_interaction_ms;
    bool bored = idle_ms > 3600000 &&    /* > 1 hour idle */
                 s->primary.happiness >= 30 && s->primary.happiness <= 60;
    if (bored) {
        /*
         * Divide current time by 5000 to get a "tick" that changes every 5 seconds.
         * Then multiply by the Knuth multiplicative hash constant (2654435761).
         *
         * 2654435761 is a large prime close to 2^32 / phi (the golden ratio).
         * Multiplying by it and taking modulo scrambles the tick value into a
         * pseudo-random distribution. This is a common trick for cheap, deterministic
         * "randomness" when you don't need cryptographic quality.
         *
         * The `u` suffix means "unsigned literal" -- tells the compiler to treat
         * the number as unsigned, which avoids signed overflow (undefined behavior in C).
         *
         * (tick * 2654435761u) % 20 == 0 fires roughly 1 in 20 ticks (~5% chance
         * per 5-second window).
         */
        uint32_t tick = time_mgr_now_ms() / 5000;
        if ((tick * 2654435761u) % 20 == 0) return 0.6f;
    }
    return 0.0f;
}

/*
 * eval_unhinged -- Triggers when the creature is in critical condition:
 * health is very low AND multiple other stats are also critical.
 * This is the most extreme negative emotion.
 */
static float eval_unhinged(const stats_t *s, const sensor_context_t *ctx,
                           const life_state_t *life) {
    int critical = 0;  /* count how many stats are in the danger zone */
    if (s->primary.hunger < 20) critical++;
    if (s->primary.happiness < 20) critical++;
    if (s->primary.energy < 15) critical++;
    if (s->primary.hygiene < 25) critical++;

    if (s->primary.health < 20 && critical >= 2) return 0.9f;  /* very sick + 2 bad stats */
    if (s->primary.health < 30 && critical >= 3) return 0.7f;  /* sick + 3 bad stats */
    return 0.0f;
}

/*
 * eval_slap_happy -- Triggers when happiness is very high AND a stat
 * recently recovered (the relief/euphoria of bouncing back).
 */
static float eval_slap_happy(const stats_t *s, const sensor_context_t *ctx,
                             const life_state_t *life) {
    if (s->primary.happiness > 90 &&
        event_recent(EVENT_STAT_RECOVERED, 300000)) {  /* recovered in last 5 minutes */
        return 0.85f;
    }
    return 0.0f;
}

/*
 * eval_horny -- Only triggers for adolescent/adult creatures with high
 * happiness and strong bond with the user. Fires randomly and rarely.
 */
static float eval_horny(const stats_t *s, const sensor_context_t *ctx,
                        const life_state_t *life) {
    if ((life->stage == LIFE_STAGE_ADOLESCENT || life->stage == LIFE_STAGE_ADULT) &&
        s->primary.happiness > 70 && s->secondary.bond_xp > 4000) {
        /* Same Knuth hash trick as eval_weird, but % 50 = ~2% chance per tick */
        uint32_t tick = time_mgr_now_ms() / 5000;
        if ((tick * 2654435761u) % 50 == 0) return 0.6f;
    }
    return 0.0f;
}

/*
 * eval_nostalgic -- Triggers near "weekly anniversaries" of the creature's
 * birth (within 60 seconds of each 7-day mark), or when the user arrives
 * at a familiar location.
 */
static float eval_nostalgic(const stats_t *s, const sensor_context_t *ctx,
                            const life_state_t *life) {
    /*
     * 7 * 86400 = 604,800 seconds = 1 week.
     * The modulo (%) gives how far past the last weekly mark we are.
     * If that remainder is less than 60 seconds, we're right at the anniversary.
     */
    if (life->age_seconds > 0 && (life->age_seconds % (7 * 86400)) < 60) {
        return 0.7f;
    }
    if (event_recent(EVENT_HOME_ARRIVED, 60000)) return 0.5f;  /* arrived home in last minute */
    return 0.0f;
}

/*
 * eval_homesick -- Triggers when the creature has been away from "home"
 * WiFi for over 4 hours, or when a new location is detected recently.
 */
static float eval_homesick(const stats_t *s, const sensor_context_t *ctx,
                           const life_state_t *life) {
    /* 4 * 3600 * 1000 = 14,400,000 ms = 4 hours away from home WiFi */
    if (ctx->wifi.away_from_home && ctx->wifi.away_duration_ms > 4 * 3600 * 1000) {
        return 0.7f;
    }
    if (event_recent(EVENT_NEW_LOCATION, 300000)) return 0.3f;  /* new location in last 5 min */
    return 0.0f;
}

/* ─── Trigger Table ──────────────────────────────────────────────
 *
 * This is the heart of the emotion system: a table of function pointers.
 *
 * A "function pointer" is a variable that stores the address of a function.
 * Just like a regular pointer holds the address of data, a function pointer
 * holds the address of executable code. You can then "call" the pointer
 * like a regular function: ptr(arg1, arg2).
 *
 * eval_fn_t is a typedef (type alias) for a pointer to any function that
 * takes (const stats_t *, const sensor_context_t *, const life_state_t *)
 * and returns a float. Every eval_* function above matches this signature,
 * so any of them can be stored in an eval_fn_t variable.
 *
 * Each row in the TRIGGERS[] table pairs an emotion ID with:
 *   - evaluate:     function pointer to that emotion's scoring function
 *   - priority:     tie-breaker when two emotions have equal weight
 *   - min_dwell_ms: minimum time (ms) to stay in this emotion before
 *                   allowing a switch (prevents flickering)
 */

typedef float (*eval_fn_t)(const stats_t *, const sensor_context_t *,
                           const life_state_t *);

typedef struct {
    emotion_id_t id;         /* which emotion this row describes */
    eval_fn_t    evaluate;   /* function pointer to the evaluator */
    float        priority;   /* higher = wins ties (10 = highest) */
    uint32_t     min_dwell_ms; /* minimum ms to stay before switching away */
} emotion_trigger_t;

/*
 * TRIGGERS[] -- The static const trigger table.
 *
 * `static` here means file-scoped (private to this file).
 * `const` means the contents cannot be modified at runtime.
 * Together, `static const` tells the compiler to store this in the
 * read-only data segment (.rodata), which is shared by all calls and
 * is safe from accidental writes. On embedded systems, this often
 * lives in flash memory rather than RAM, saving precious SRAM.
 *
 * The table is sorted by priority (highest first), though the code
 * doesn't rely on this ordering -- it iterates all entries anyway.
 */
static const emotion_trigger_t TRIGGERS[] = {
    { EMOTION_UNHINGED,   eval_unhinged,   10.0f, 60000 },
    { EMOTION_ANGRY,      eval_angry,       9.0f, 30000 },
    { EMOTION_HUNGRY,     eval_hungry,      8.0f, 30000 },
    { EMOTION_TIRED,      eval_tired,       7.5f, 30000 },
    { EMOTION_SAD,        eval_sad,         7.0f, 30000 },
    { EMOTION_EXCITED,    eval_excited,     6.5f, 15000 },
    { EMOTION_SLAP_HAPPY, eval_slap_happy,  6.0f, 20000 },
    { EMOTION_CHAOTIC,    eval_chaotic,     5.5f, 10000 },
    { EMOTION_HOMESICK,   eval_homesick,    5.0f, 45000 },
    { EMOTION_NOSTALGIC,  eval_nostalgic,   4.5f, 30000 },
    { EMOTION_FAT,        eval_fat,         4.0f, 30000 },
    { EMOTION_LAZY,       eval_lazy,        3.5f, 30000 },
    { EMOTION_HORNY,      eval_horny,       3.0f, 20000 },
    { EMOTION_WEIRD,      eval_weird,       2.5f, 20000 },
    { EMOTION_CHILL,      eval_chill,       2.0f, 30000 },
    { EMOTION_NORMAL,     eval_normal,      1.0f, 30000 },
};

/*
 * NUM_TRIGGERS -- Compute the number of entries in TRIGGERS[] at compile time.
 *
 * sizeof(TRIGGERS)      = total size of the array in bytes
 * sizeof(TRIGGERS[0])   = size of one element in bytes
 * Dividing gives the element count.
 *
 * This is a standard C idiom. It's done as a macro (#define) rather than
 * a variable so the compiler treats it as a compile-time constant, which
 * can be used in places where a variable cannot (like array declarations).
 */
#define NUM_TRIGGERS (sizeof(TRIGGERS) / sizeof(TRIGGERS[0]))

/* ─── Hysteresis ─────────────────────────────────────────────────
 *
 * Hysteresis prevents rapid back-and-forth switching between emotions.
 * A new emotion must beat the current one's weight by at least this
 * margin before the system will switch. Without this, two emotions
 * with nearly equal weights would cause flickering every tick.
 */
#define HYSTERESIS_MARGIN 0.15f

/* ─── Implementation ─────────────────────────────────────────── */

/*
 * emotion_init -- Initialize the emotion state to defaults.
 *
 * Parameters:
 *   state -- pointer to the emotion_state_t struct to initialize.
 *            The caller owns this memory (it's part of the game struct).
 *
 * memset(state, 0, sizeof(*state)) fills all bytes of the struct with
 * zero. sizeof(*state) means "the size of whatever state points to"
 * (i.e., sizeof(emotion_state_t)). This is safer than sizeof(state)
 * which would give the size of the pointer itself (4 or 8 bytes).
 */
void emotion_init(emotion_state_t *state) {
    memset(state, 0, sizeof(*state));
    state->current = EMOTION_NORMAL;
    state->previous = EMOTION_NORMAL;
    state->current_weight = 0.5f;
    state->min_dwell_ms = 30000;  /* 30 seconds before first switch allowed */
}

/*
 * emotion_resolve -- The main emotion update function, called every game tick.
 *
 * Evaluates all emotion triggers, applies life-stage gating, picks a winner,
 * applies hysteresis, and (if warranted) transitions to the new emotion.
 *
 * Parameters:
 *   state -- mutable pointer to the emotion state to update
 *   stats -- read-only pointer to the creature's current stats
 *   ctx   -- read-only pointer to current sensor readings
 *   life  -- read-only pointer to the creature's life stage info
 *
 * Uses `const` on the read-only parameters to signal (and enforce) that
 * this function will not modify them. This is good practice in C -- it
 * prevents accidental writes and helps the compiler optimize.
 */
void emotion_resolve(emotion_state_t *state, const stats_t *stats,
                     const sensor_context_t *ctx, const life_state_t *life) {
    uint32_t now = time_mgr_now_ms();

    /* Skip if forced override active -- a forced emotion (from a care
     * action like feeding) takes priority until its timer expires. */
    if (state->forced && now < state->force_end_ms) return;
    state->forced = false;

    /* Skip if within minimum dwell -- prevent switching away from the
     * current emotion too quickly. */
    if (now - state->dwell_start_ms < state->min_dwell_ms) return;

    /* Phase 1: evaluate all triggers.
     * Loop through every entry in TRIGGERS[] and call its evaluate function
     * pointer. The result is stored in the weights[] array indexed by
     * emotion ID, so we can look up any emotion's weight later.
     *
     * TRIGGERS[i].evaluate is a function pointer. The syntax
     * TRIGGERS[i].evaluate(stats, ctx, life) calls the pointed-to function
     * just like a normal function call.
     */
    for (size_t i = 0; i < NUM_TRIGGERS; i++) {
        state->weights[TRIGGERS[i].id] = TRIGGERS[i].evaluate(stats, ctx, life);
    }

    /* Phase 2: life stage gating.
     * Certain emotions are inappropriate for certain life stages.
     * For example, eggs can't feel emotions, and hatchlings only have
     * a limited emotional range. Zero out disallowed emotions.
     */
    if (life->stage == LIFE_STAGE_EGG) {
        /* Eggs have no emotion */
        for (int i = 0; i < EMOTION_COUNT; i++)
            state->weights[i] = 0.0f;
        state->weights[EMOTION_NORMAL] = 1.0f;
    } else if (life->stage == LIFE_STAGE_HATCHLING) {
        /* Hatchlings can only feel: normal, hungry, tired, sad, excited */
        for (int i = 0; i < EMOTION_COUNT; i++) {
            if (i != EMOTION_NORMAL && i != EMOTION_HUNGRY &&
                i != EMOTION_TIRED && i != EMOTION_SAD &&
                i != EMOTION_EXCITED) {
                state->weights[i] = 0.0f;
            }
        }
    } else if (life->stage == LIFE_STAGE_JUVENILE) {
        /* Juveniles can't feel horny, nostalgic, or unhinged */
        state->weights[EMOTION_HORNY] = 0.0f;
        state->weights[EMOTION_NOSTALGIC] = 0.0f;
        state->weights[EMOTION_UNHINGED] = 0.0f;
    }

    /* Phase 3: find winner.
     * Scan all trigger entries and find the emotion with the highest weight.
     * On ties, the one with higher priority wins.
     */
    emotion_id_t winner = EMOTION_NORMAL;
    float max_weight = 0.0f;
    float max_priority = 0.0f;

    for (size_t i = 0; i < NUM_TRIGGERS; i++) {
        emotion_id_t eid = TRIGGERS[i].id;
        float w = state->weights[eid];
        float p = TRIGGERS[i].priority;

        /*
         * Pick this emotion if its weight is strictly higher, OR if the
         * weight ties but it has higher priority. This ensures deterministic
         * tie-breaking.
         */
        if (w > max_weight || (w == max_weight && p > max_priority)) {
            max_weight = w;
            max_priority = p;
            winner = eid;
        }
    }

    /* Phase 4: hysteresis.
     * Only switch to the new emotion if it beats the current emotion's
     * weight by at least HYSTERESIS_MARGIN (0.15). This prevents the
     * creature from flip-flopping between two similar emotions.
     */
    if (winner != state->current) {
        float current_w = state->weights[state->current];
        if (max_weight < current_w + HYSTERESIS_MARGIN) {
            state->changed = false;  /* not enough margin -- stay put */
            return;
        }
    } else {
        state->changed = false;  /* winner is already the current emotion -- no change */
        return;
    }

    /* Phase 5: transition.
     * We've decided to switch. Record the old emotion, install the new
     * one, and reset the dwell timer.
     */
    state->previous = state->current;
    state->current = winner;
    state->current_weight = max_weight;
    state->dwell_start_ms = now;
    state->changed = true;          /* flag for other systems (e.g., dialog) to react */
    state->in_transition = true;    /* animation system can use this for transition effects */

    /* Find min dwell for winner -- look up how long this emotion should
     * persist before we allow switching away from it again. */
    for (size_t i = 0; i < NUM_TRIGGERS; i++) {
        if (TRIGGERS[i].id == winner) {
            state->min_dwell_ms = TRIGGERS[i].min_dwell_ms;
            break;
        }
    }
}

/*
 * emotion_force -- Immediately override the current emotion for a set duration.
 *
 * Used by care actions (feeding, petting, scolding) to produce an immediate
 * emotional reaction that bypasses the normal evaluation system.
 *
 * Parameters:
 *   state       -- the emotion state to modify
 *   emotion     -- which emotion to force
 *   duration_ms -- how long the forced emotion lasts (in milliseconds)
 *   now_ms      -- the current timestamp in milliseconds
 */
void emotion_force(emotion_state_t *state, emotion_id_t emotion,
                   uint32_t duration_ms, uint32_t now_ms) {
    state->previous = state->current;
    state->current = emotion;
    state->forced = true;
    state->force_end_ms = now_ms + duration_ms;  /* when the override expires */
    state->changed = true;
    state->in_transition = true;
}

/*
 * emotion_current -- Simple getter: returns the current emotion ID.
 *
 * Parameters:
 *   state -- read-only pointer to the emotion state
 *
 * Returns: the emotion_id_t of the currently active emotion.
 *
 * The `const` on the parameter means this function promises not to
 * modify the state -- it's purely a read/query operation.
 */
emotion_id_t emotion_current(const emotion_state_t *state) {
    return state->current;
}

/*
 * emotion_changed -- Query whether the emotion changed on the last tick.
 *
 * Parameters:
 *   state -- read-only pointer to the emotion state
 *
 * Returns: true if the emotion changed during the most recent
 *          emotion_resolve() call, false otherwise.
 */
bool emotion_changed(const emotion_state_t *state) {
    return state->changed;
}

/*
 * emotion_on_care_action -- Event handler callback for care actions.
 *
 * This function is registered as a listener with the event system. When the
 * player feeds, pets, plays with, scolds, or cleans the creature, the event
 * system calls this function. It forces an immediate emotional reaction.
 *
 * Parameters:
 *   type -- which event fired (EVENT_FED, EVENT_PETTED, etc.)
 *   data -- optional extra data. For EVENT_SCOLDED, data->value == 1 means
 *           the scolding was severe (creature gets angry rather than sad).
 *
 * Note the `extern game_t g_game` declaration inside the function body.
 * `extern` tells the compiler "this variable exists, but it's defined in
 * another .c file -- don't allocate storage here, just let me reference it."
 * g_game is the single global game state struct that holds everything:
 * stats, emotion, life stage, progression, etc. Declaring it inside the
 * function (rather than at file scope) limits its visibility to just this
 * function, which is slightly tidier.
 */
void emotion_on_care_action(event_type_t type, const event_data_t *data) {
    extern game_t g_game;
    uint32_t now = time_mgr_now_ms();

    if (type == EVENT_FED) {
        emotion_force(&g_game.emotion, EMOTION_EXCITED, 10000, now);
    } else if (type == EVENT_PETTED) {
        emotion_force(&g_game.emotion, EMOTION_CHILL, 8000, now);
    } else if (type == EVENT_PLAYED) {
        emotion_force(&g_game.emotion, EMOTION_EXCITED, 15000, now);
    } else if (type == EVENT_SCOLDED) {
        /*
         * data->value distinguishes scolding severity:
         *   1 = harsh scolding -> anger (short duration)
         *   anything else      -> sadness (longer duration)
         *
         * The `data &&` check guards against a NULL pointer. If no data
         * was provided (data == NULL), accessing data->value would crash
         * (segmentation fault). The && operator short-circuits: if `data`
         * is NULL (falsy), the right side is never evaluated.
         */
        if (data && data->value == 1) {
            emotion_force(&g_game.emotion, EMOTION_ANGRY, 5000, now);
        } else {
            emotion_force(&g_game.emotion, EMOTION_SAD, 8000, now);
        }
    } else if (type == EVENT_CLEANED) {
        emotion_force(&g_game.emotion, EMOTION_CHILL, 5000, now);
    }
}
