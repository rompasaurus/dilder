#ifndef DILDER_STAT_H
#define DILDER_STAT_H

#include "game_state.h"

/* ─── Stat System API ────────────────────────────────────────── */

void stat_init(stats_t *stats);

/* Per-tick processing */
void stat_decay_tick(stats_t *stats, decay_accum_t *accum,
                     const modifier_stack_t *mods, game_state_t state);
void stat_sleep_tick(stats_t *stats);
void stat_check_thresholds(stats_t *stats);
void stat_update_health(stats_t *stats);

/* Care actions */
void stat_apply_care(stats_t *stats, care_cooldown_t *cd,
                     care_action_t action, bool misbehaving);

/* Cooldown tick (call once per second) */
void stat_cooldown_tick(care_cooldown_t *cd);

/* Modifiers */
void modifier_recalculate(modifier_stack_t *mods, const stats_t *stats,
                          const life_state_t *life, const sensor_context_t *ctx,
                          const game_time_t *gt);
float modifier_get(const modifier_stack_t *mods, modifier_type_t type);

/* Offline decay */
void stat_apply_offline_decay(stats_t *stats, uint32_t elapsed_seconds);

/* Queries */
int16_t stat_get_by_id(const primary_stats_t *stats, stat_id_t id);
bool    stat_is_critical(const primary_stats_t *stats, stat_id_t id);
bool    stat_all_balanced(const primary_stats_t *stats);

/* Clamp helpers */
void stat_clamp_all(primary_stats_t *stats);

#endif /* DILDER_STAT_H */
