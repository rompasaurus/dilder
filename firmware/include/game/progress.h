#ifndef DILDER_PROGRESS_H
#define DILDER_PROGRESS_H

#include "game_state.h"
#include "event.h"

/* ─── Bond XP thresholds ─────────────────────────────────────── */
#define BOND_XP_ACQUAINTANCE   500
#define BOND_XP_COMPANION     2000
#define BOND_XP_FRIEND        5000
#define BOND_XP_BEST_FRIEND  12000
#define BOND_XP_SOULMATE     25000

/* ─── Progression API ────────────────────────────────────────── */

void progression_init(progression_t *prog);

/* Add XP and check for level up */
void progression_add_xp(progression_t *prog, uint16_t amount);

/* Check bond level from XP */
bond_level_t progression_calc_level(uint32_t bond_xp);

/* Event handlers */
void progression_on_care_action(event_type_t type, const event_data_t *data);
void progression_on_step_milestone(event_type_t type, const event_data_t *data);

#endif /* DILDER_PROGRESS_H */
