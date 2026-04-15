/*
 * life.c -- Life Stage & Evolution System
 *
 * This module manages the Dilder creature's lifecycle: hatching from an
 * egg, growing through stages (hatchling -> juvenile -> adolescent ->
 * adult -> elder), accumulating lifetime stats, handling misbehavior/
 * discipline events, and calculating which "evolution form" the creature
 * becomes at adulthood.
 *
 * Key concepts used in this file:
 *   - static functions: all helper functions (on_hatch, on_juvenile, etc.)
 *     are `static`, meaning they're private to this file. Only functions
 *     declared in the header (life_init, life_stage_check, etc.) are
 *     callable from other files.
 *   - Compound literals: expressions like `(event_data_t){ .value = X }`
 *     create a temporary struct on the stack. They're valid C99+ and are
 *     commonly used to pass small structs to functions without declaring
 *     a named variable first. The temporary is valid until the enclosing
 *     block ends.
 *   - static local variables: variables declared `static` inside a function
 *     persist across calls (they live in the data segment, not the stack).
 *     They're initialized only once, the first time the function runs.
 *   - #define macros: used for age thresholds so they're compile-time
 *     constants (no runtime cost, no memory allocated).
 */

#include "game/life.h"
#include "game/event.h"
#include "game/time_mgr.h"
#include <math.h>

/* ─── Stage Duration Thresholds (seconds) ────────────────────────
 *
 * These #define macros set the age (in seconds) at which each life-stage
 * transition occurs. 86400 = seconds in one day (60 * 60 * 24).
 *
 * Using #define rather than variables means these values are substituted
 * directly into the code by the preprocessor -- there's no memory
 * allocated for them and no runtime lookup.
 */
#define AGE_HATCH      (1  * 86400)   /* 1 day */
#define AGE_JUVENILE   (3  * 86400)   /* 3 days */
#define AGE_ADOLESCENT (7  * 86400)   /* 7 days */
#define AGE_ADULT      (14 * 86400)   /* 14 days */
#define AGE_ELDER      (30 * 86400)   /* 30 days */

/* ─── Implementation ─────────────────────────────────────────── */

/*
 * life_init -- Initialize the life state to defaults (a fresh egg).
 *
 * Parameters:
 *   life -- pointer to the life_state_t struct to initialize.
 *           The caller owns the memory.
 *
 * memset zeroes all bytes, then we set the specific starting values.
 * sizeof(*life) means "size of the thing life points to" -- this is
 * safer than sizeof(life_state_t) because if the type ever changes,
 * sizeof(*life) automatically stays correct.
 */
void life_init(life_state_t *life) {
    memset(life, 0, sizeof(*life));
    life->stage = LIFE_STAGE_EGG;
    life->adult_form = EVOLUTION_NONE;
}

/* ─── Transition Helpers ─────────────────────────────────────────
 *
 * Each on_* function is called when the creature enters a new life stage.
 * They record the transition timestamp, reset discipline tracking, and
 * fire an event so other systems (UI, dialog, etc.) can react.
 *
 * All are `static` (file-private) because they're only called from
 * life_stage_check() within this file.
 */

/*
 * on_hatch -- Called when the egg hatches into a hatchling.
 *
 * Parameters:
 *   life -- the life state to update
 *
 * The event_fire() call uses a compound literal:
 *   &(event_data_t){ .value = LIFE_STAGE_HATCHLING }
 *
 * Breaking this down:
 *   (event_data_t){ .value = LIFE_STAGE_HATCHLING }
 *     -- Creates a temporary event_data_t struct on the stack, with its
 *        `.value` field set to LIFE_STAGE_HATCHLING and all other fields
 *        zeroed (C99 designated initializer).
 *   &(...)
 *     -- Takes the address of that temporary, giving us a pointer to pass
 *        to event_fire(). The temporary is valid until the end of this
 *        statement, which is fine because event_fire() uses it immediately.
 */
static void on_hatch(life_state_t *life) {
    life->stage_start_seconds = life->age_seconds;
    life->discipline_windows = 0;
    event_fire(EVENT_STAGE_TRANSITION, &(event_data_t){ .value = LIFE_STAGE_HATCHLING });
}

/*
 * on_juvenile -- Called when the creature transitions from hatchling to juvenile.
 */
static void on_juvenile(life_state_t *life) {
    life->stage_start_seconds = life->age_seconds;
    life->discipline_windows = 0;
    event_fire(EVENT_STAGE_TRANSITION, &(event_data_t){ .value = LIFE_STAGE_JUVENILE });
}

/*
 * on_adolescent -- Called when the creature transitions from juvenile to adolescent.
 */
static void on_adolescent(life_state_t *life) {
    life->stage_start_seconds = life->age_seconds;
    life->discipline_windows = 0;
    event_fire(EVENT_STAGE_TRANSITION, &(event_data_t){ .value = LIFE_STAGE_ADOLESCENT });
}

/*
 * on_adult -- Called when the creature transitions from adolescent to adult.
 *
 * This is the big one: it calculates the creature's evolution form based on
 * lifetime stats, then fires two events (evolution and stage transition).
 *
 * Parameters:
 *   life  -- the life state to update
 *   stats -- read-only pointer to current stats (used for evolution calc)
 */
static void on_adult(life_state_t *life, const stats_t *stats) {
    life->stage_start_seconds = life->age_seconds;
    life->adult_form = evolution_calculate(life, stats);  /* determine which form to evolve into */
    event_fire(EVENT_EVOLUTION, &(event_data_t){ .value = life->adult_form });
    event_fire(EVENT_STAGE_TRANSITION, &(event_data_t){ .value = LIFE_STAGE_ADULT });
}

/*
 * on_elder -- Called when the creature transitions from adult to elder.
 */
static void on_elder(life_state_t *life) {
    life->stage_start_seconds = life->age_seconds;
    event_fire(EVENT_STAGE_TRANSITION, &(event_data_t){ .value = LIFE_STAGE_ELDER });
}

/* ─── Egg Progress ───────────────────────────────────────────────
 *
 * The egg doesn't hatch based on time alone -- the player must interact
 * with it. Picking it up, shaking it, keeping it warm, and talking to it
 * all contribute to a hatch_progress counter (0-100).
 */

/*
 * egg_progress_update -- Add hatch progress based on sensor activity.
 *
 * Parameters:
 *   life -- the life state (we update life->hatch_progress)
 *   ctx  -- read-only sensor context (accelerometer, environment, mic)
 */
static void egg_progress_update(life_state_t *life, const sensor_context_t *ctx) {
    if (ctx->accel.picked_up || ctx->accel.shaking) {
        life->hatch_progress += 2;  /* physical interaction gives the most progress */
    }
    if (ctx->env.comfort_zone == COMFORT_GOOD) {
        life->hatch_progress += 1;  /* comfortable environment helps */
    }
    if (ctx->mic.level >= 200) {
        life->hatch_progress += 1;  /* talking/noise helps too */
    }
    if (life->hatch_progress > 100) life->hatch_progress = 100;  /* cap at 100% */
}

/* ─── Stat Accumulation ──────────────────────────────────────────
 *
 * Tracks running averages and totals of the creature's stats over its
 * lifetime. These accumulated values are used later to determine which
 * evolution form the creature becomes (see evolution_calculate).
 */

/*
 * life_accumulate_stats -- Snapshot current stats into lifetime accumulators.
 *
 * Parameters:
 *   life  -- the life state to update with accumulated values
 *   stats -- read-only snapshot of the creature's current stats
 */
static void life_accumulate_stats(life_state_t *life, const stats_t *stats) {
    /*
     * These `static` local variables persist across function calls.
     *
     * Unlike regular local variables (which are created on the stack each
     * time a function is called and destroyed when it returns), `static`
     * locals are stored in the program's data segment. They are initialized
     * only once (at program start) and retain their values between calls.
     *
     * This is used here to maintain a running sum and count for computing
     * an average happiness over the creature's entire lifetime.
     *
     * IMPORTANT CAVEAT: because these are static, there can only be one
     * creature at a time -- if you had two creatures, they'd share these
     * accumulators. For a single-pet game, this is fine.
     */
    static uint32_t happiness_sum = 0;
    static uint32_t happiness_count = 0;
    happiness_sum += stats->primary.happiness;
    happiness_count++;
    /*
     * Cast to uint16_t truncates the result to 16 bits. This is safe because
     * happiness values are 0-100 so the average will always fit in a uint16_t.
     */
    life->total_happiness_avg = (uint16_t)(happiness_sum / happiness_count);

    /*
     * Care quality: starts at 100 and decreases by 5 for each care mistake.
     * fminf_safe clamps the penalty to a max of 100 (so quality can't go
     * negative after the subtraction).
     */
    life->total_care_quality = (uint16_t)(100 -
        fminf_safe(stats->hidden.care_mistakes * 5.0f, 100.0f));
    life->total_discipline = stats->secondary.discipline;
    life->total_intelligence = stats->secondary.intelligence;
    life->total_fitness = stats->secondary.fitness;
    life->total_exploration = stats->secondary.exploration;
}

/* ─── Per-Tick Check ─────────────────────────────────────────────
 *
 * Called once per game "tick" (once per second) to advance the creature's
 * age and check for life-stage transitions.
 */

/*
 * life_stage_check -- Main per-tick lifecycle update.
 *
 * Parameters:
 *   life  -- mutable pointer to the creature's life state
 *   stats -- read-only pointer to the creature's current stats
 *   ctx   -- read-only pointer to current sensor readings
 *   gt    -- read-only pointer to the game time state
 */
void life_stage_check(life_state_t *life, const stats_t *stats,
                      const sensor_context_t *ctx, const game_time_t *gt) {
    life->age_seconds++;

    /* Egg: accumulate hatch progress from sensor interaction */
    if (life->stage == LIFE_STAGE_EGG) {
        egg_progress_update(life, ctx);
        if (life->hatch_progress >= 100) {
            life->stage = LIFE_STAGE_HATCHLING;
            on_hatch(life);
            return;  /* don't also check age-based transitions this tick */
        }
    }

    /* Age-based transitions.
     * Each case checks if the creature is old enough to advance to the
     * next stage. When it is, we accumulate stats (for evolution scoring),
     * change the stage, and call the transition handler.
     */
    switch (life->stage) {
        case LIFE_STAGE_HATCHLING:
            if (life->age_seconds >= AGE_JUVENILE) {
                life_accumulate_stats(life, stats);
                life->stage = LIFE_STAGE_JUVENILE;
                on_juvenile(life);
            }
            break;
        case LIFE_STAGE_JUVENILE:
            if (life->age_seconds >= AGE_ADOLESCENT) {
                life_accumulate_stats(life, stats);
                life->stage = LIFE_STAGE_ADOLESCENT;
                on_adolescent(life);
            }
            break;
        case LIFE_STAGE_ADOLESCENT:
            if (life->age_seconds >= AGE_ADULT) {
                life_accumulate_stats(life, stats);
                life->stage = LIFE_STAGE_ADULT;
                on_adult(life, stats);
            }
            break;
        case LIFE_STAGE_ADULT:
            if (life->age_seconds >= AGE_ELDER) {
                life->stage = LIFE_STAGE_ELDER;
                on_elder(life);
            }
            break;
        default:
            break;  /* LIFE_STAGE_EGG and LIFE_STAGE_ELDER: no further transitions */
    }

    /* Hourly accumulation.
     *
     * `static uint32_t last_accumulate = 0` is a static local variable
     * (persists across calls, initialized once to 0). It tracks when we
     * last ran the accumulation. Every 3600 seconds (1 hour), we snapshot
     * the current stats into the lifetime accumulators.
     */
    static uint32_t last_accumulate = 0;
    if (life->age_seconds - last_accumulate >= 3600) {
        last_accumulate = life->age_seconds;
        life_accumulate_stats(life, stats);
    }
}

/* ─── Misbehavior ────────────────────────────────────────────────
 *
 * The misbehavior system creates "discipline windows" -- moments where
 * the creature acts out and the player can choose to scold it. This
 * is part of the evolution system: how (and whether) you discipline
 * affects which form the creature evolves into.
 */

/*
 * misbehavior_check -- Check whether the creature should start misbehaving.
 *
 * Parameters:
 *   life  -- mutable pointer to the life state
 *   stats -- read-only pointer to current stats
 *   now   -- current time in milliseconds
 */
void misbehavior_check(life_state_t *life, const stats_t *stats, uint32_t now) {
    /* If already misbehaving, check if the timeout has expired */
    if (life->misbehaving) {
        if (now - life->misbehave_start_ms > life->misbehave_timeout_ms) {
            life->misbehaving = false;  /* misbehavior window expired (player didn't scold) */
        }
        return;  /* either way, don't start a new misbehavior while one is active */
    }

    /* Only hatchlings through adolescents misbehave.
     * The < and > comparisons work because life stages are stored as
     * sequential enum values (EGG=0, HATCHLING=1, JUVENILE=2, etc.). */
    if (life->stage < LIFE_STAGE_HATCHLING || life->stage > LIFE_STAGE_ADOLESCENT) return;

    /* Max 4 discipline windows per life stage */
    if (life->discipline_windows >= 4) return;

    /*
     * Pseudo-random trigger using the Knuth multiplicative hash.
     *
     * `now / 60000` converts milliseconds to minutes (integer division
     * truncates, giving us a "tick" that changes once per minute).
     *
     * Multiplying by 2654435761u (a prime near 2^32 / golden ratio) and
     * taking modulo 100 produces a pseudo-random value from 0-99.
     * Checking == 0 gives roughly a 1% chance per minute.
     *
     * The `u` suffix marks the literal as unsigned to prevent signed
     * integer overflow (which is undefined behavior in C). Unsigned
     * overflow is well-defined: it wraps modulo 2^32.
     */
    uint32_t tick = now / 60000;
    bool trigger = ((tick * 2654435761u) % 100) == 0;

    /* Happy, well-fed creatures have double the chance of misbehaving
     * (they have energy to be naughty). The || means trigger becomes true
     * if EITHER the original check OR this additional check passes. */
    if (stats->primary.happiness > 60 && stats->primary.hunger > 40) {
        trigger = trigger || ((tick * 2654435761u) % 50) == 0;
    }

    if (trigger) {
        life->misbehaving = true;
        life->misbehave_start_ms = now;
        life->misbehave_timeout_ms = 60000;  /* player has 60 seconds to respond */
        life->discipline_windows++;
        event_fire(EVENT_MISBEHAVIOR, NULL);  /* NULL = no extra event data */
    }
}

/*
 * misbehavior_resolve -- Called when the player responds (or not) to misbehavior.
 *
 * Parameters:
 *   life    -- mutable pointer to the life state
 *   stats   -- mutable pointer to stats (discipline may be updated)
 *   scolded -- true if the player scolded the creature, false if they ignored it
 */
void misbehavior_resolve(life_state_t *life, stats_t *stats, bool scolded) {
    if (!life->misbehaving) return;  /* nothing to resolve */
    life->misbehaving = false;

    if (scolded) {
        stats->secondary.discipline += 25;
        /* clamp_u16 ensures the value stays in [0, 100] range.
         * Without clamping, discipline could overflow past 100. */
        stats->secondary.discipline = clamp_u16(stats->secondary.discipline, 0, 100);
        life->total_scold_count++;  /* lifetime counter, used in evolution scoring */
    }
}

/* ─── Evolution ──────────────────────────────────────────────────
 *
 * When the creature reaches adulthood, this function determines which
 * of 6 possible evolution forms it becomes. The form is based on a
 * weighted scoring of lifetime stats: intelligence, fitness, happiness,
 * discipline, care quality, etc.
 *
 * Each form represents a different "personality archetype" shaped by
 * how the player raised the creature.
 */

/*
 * evolution_calculate -- Determine the creature's adult evolution form.
 *
 * Parameters:
 *   life  -- read-only pointer to lifetime state (accumulated stats, counters)
 *   stats -- read-only pointer to current stats at time of evolution
 *
 * Returns: an evolution_form_t enum value (EVOLUTION_DEEP_SEA_SCHOLAR, etc.)
 */
evolution_form_t evolution_calculate(const life_state_t *life,
                                    const stats_t *stats) {
    /*
     * scores[] is a stack-allocated array of int16_t (signed 16-bit integers).
     *
     * EVOLUTION_COUNT - 1 entries because EVOLUTION_NONE (index 0) is not a
     * valid form. So scores[0] = Deep-Sea Scholar, scores[1] = Reef Guardian,
     * etc. The array lives on the stack and is automatically freed when this
     * function returns.
     *
     * int16_t is used (rather than int) to match the uint16_t stat types
     * and keep memory usage small on embedded systems.
     */
    int16_t scores[EVOLUTION_COUNT - 1];

    /* Deep-Sea Scholar: intelligence + bond + discipline.
     *
     * (int16_t)(stats->secondary.bond_xp / 500) -- the cast to int16_t
     * truncates the division result to 16 bits. bond_xp is uint32_t,
     * dividing by 500 scales it down to a comparable range, and the cast
     * prevents implicit conversion warnings.
     */
    scores[0] = stats->secondary.intelligence +
                (int16_t)(stats->secondary.bond_xp / 500) +
                life->total_discipline / 2;

    /* Reef Guardian: fitness + exploration + care quality */
    scores[1] = stats->secondary.fitness +
                stats->secondary.exploration +
                life->total_care_quality / 3;

    /* Tidal Trickster: inverse discipline + happiness + chaos.
     * (100 - discipline) means LESS discipline = HIGHER score for this form.
     * care_mistakes also boost this form -- a neglected/chaotic upbringing. */
    scores[2] = (100 - life->total_discipline) +
                life->total_happiness_avg +
                stats->hidden.care_mistakes;

    /* Abyssal Hermit: discipline + low social + stoic.
     * High discipline but low bond and low happiness = hermit personality. */
    scores[3] = life->total_discipline +
                (int16_t)(100 - (stats->secondary.bond_xp / 500)) +
                (100 - life->total_happiness_avg) / 2;

    /* Coral Dancer: happiness + music + intelligence */
    scores[4] = life->total_happiness_avg +
                life->total_music_exposure * 5 +
                stats->secondary.intelligence / 2;

    /* Storm Kraken: scolding + survival.
     *
     * The ternary operator `condition ? value_if_true : value_if_false`
     * is a compact if/else. Here: if health > 50, add 50 points; otherwise
     * add 0. This rewards creatures that survived harsh treatment.
     */
    scores[5] = life->total_scold_count * 3 +
                stats->hidden.care_mistakes * 2 +
                (stats->primary.health > 50 ? 50 : 0);

    /* Heritage bias: if the creature has a parent (generation > 0) with a
     * known evolution form, give that form a 20-point bonus. This creates
     * a "family tree" tendency across generations.
     *
     * heritage_form - 1 converts from the enum value (where EVOLUTION_NONE=0,
     * first real form=1) to the scores[] index (where first real form=0).
     */
    if (life->generation > 0 && life->heritage_form > EVOLUTION_NONE &&
        life->heritage_form < EVOLUTION_COUNT) {
        scores[life->heritage_form - 1] += 20;
    }

    /* Find winner: iterate through all scores to find the highest.
     *
     * (evolution_form_t)(i + 1) casts the integer index back to the enum.
     * The +1 offset accounts for EVOLUTION_NONE being enum value 0 and
     * EVOLUTION_DEEP_SEA_SCHOLAR being enum value 1.
     */
    evolution_form_t winner = EVOLUTION_DEEP_SEA_SCHOLAR;
    int16_t max_score = scores[0];
    for (int i = 1; i < EVOLUTION_COUNT - 1; i++) {
        if (scores[i] > max_score) {
            max_score = scores[i];
            winner = (evolution_form_t)(i + 1);  /* cast integer to enum type */
        }
    }

    return winner;
}

/* ─── Queries ────────────────────────────────────────────────── */

/*
 * life_stage_progress -- Calculate how far through the current life stage
 * the creature is, as a float from 0.0 (just entered) to 1.0 (about to
 * transition to the next stage).
 *
 * Parameters:
 *   life -- read-only pointer to the life state
 *
 * Returns: a float in [0.0, 1.0] representing progress through current stage.
 */
float life_stage_progress(const life_state_t *life) {
    uint32_t start = 0, end = 0;
    switch (life->stage) {
        case LIFE_STAGE_EGG:        start = 0;             end = AGE_HATCH;      break;
        case LIFE_STAGE_HATCHLING:  start = AGE_HATCH;     end = AGE_JUVENILE;   break;
        case LIFE_STAGE_JUVENILE:   start = AGE_JUVENILE;  end = AGE_ADOLESCENT; break;
        case LIFE_STAGE_ADOLESCENT: start = AGE_ADOLESCENT;end = AGE_ADULT;      break;
        case LIFE_STAGE_ADULT:      start = AGE_ADULT;     end = AGE_ELDER;      break;
        case LIFE_STAGE_ELDER:      return 1.0f;  /* elders are always "100% done" */
        default: return 0.0f;
    }
    if (end <= start) return 1.0f;  /* safety check to avoid division by zero */
    /*
     * (float) casts are needed because age_seconds, start, and end are all
     * uint32_t (unsigned integers). Without the cast, the division would be
     * integer division which truncates (e.g., 3/4 = 0 instead of 0.75).
     * Casting to float first makes it floating-point division.
     */
    float p = (float)(life->age_seconds - start) / (float)(end - start);
    return clamp_f(p, 0.0f, 1.0f);  /* clamp to [0, 1] in case of edge cases */
}
