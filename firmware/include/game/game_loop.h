#ifndef DILDER_GAME_LOOP_H
#define DILDER_GAME_LOOP_H

#include "game_state.h"

/* ─── Tick rates (as divisors of base 1s tick) ───────────────── */
#define TICK_RATE_STAT_DECAY   1
#define TICK_RATE_EMOTION      5
#define TICK_RATE_DIALOGUE    30
#define TICK_RATE_MISBEHAVIOR 60
#define TICK_RATE_MODIFIER    10

/* ─── Game Loop API ──────────────────────────────────────────── */

/* Initialize all game systems, set up a new game or restore */
void game_loop_init(void);

/* Called every frame (from platform main loop or emulator tick) */
void game_loop_tick(uint32_t now_ms);

/* The core game tick (called internally at 1s intervals) */
void game_tick(uint32_t now_ms, sensor_context_t *ctx);

/* Start a new game (egg state) */
void game_new(void);

/* Transition game state */
void game_state_transition(game_state_t new_state);

/* Should poll at divisor */
static inline bool should_tick(uint32_t tick_count, uint32_t rate) {
    return (tick_count % rate) == 0;
}

#endif /* DILDER_GAME_LOOP_H */
