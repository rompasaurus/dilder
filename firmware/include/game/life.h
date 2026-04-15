#ifndef DILDER_LIFE_H
#define DILDER_LIFE_H

#include "game_state.h"

/* ─── Life Stage API ─────────────────────────────────────────── */

void life_init(life_state_t *life);

/* Per-tick processing */
void life_stage_check(life_state_t *life, const stats_t *stats,
                      const sensor_context_t *ctx, const game_time_t *gt);

/* Misbehavior */
void misbehavior_check(life_state_t *life, const stats_t *stats, uint32_t now);
void misbehavior_resolve(life_state_t *life, stats_t *stats, bool scolded);

/* Evolution */
evolution_form_t evolution_calculate(const life_state_t *life,
                                    const stats_t *stats);

/* Queries */
float life_stage_progress(const life_state_t *life);

#endif /* DILDER_LIFE_H */
