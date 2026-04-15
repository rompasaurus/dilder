#ifndef DILDER_TIME_MGR_H
#define DILDER_TIME_MGR_H

#include "game_state.h"

/* ─── Time Manager API ───────────────────────────────────────── */

void time_mgr_init(void);

/* Call once per tick to advance game time */
game_time_t time_mgr_update(uint32_t real_ms);

/* Get current game time */
game_time_t time_mgr_get(void);

/* Get current ms (from platform clock) */
uint32_t time_mgr_now_ms(void);

/* Set the platform ms source (for emulation) */
void time_mgr_set_ms(uint32_t ms);

/* Advance by delta ms (for emulation fast-forward) */
void time_mgr_advance(uint32_t delta_ms);

#endif /* DILDER_TIME_MGR_H */
