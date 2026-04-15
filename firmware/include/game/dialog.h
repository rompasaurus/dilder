#ifndef DILDER_DIALOG_H
#define DILDER_DIALOG_H

#include "game_state.h"

/* ─── Dialogue System API ────────────────────────────────────── */

void dialogue_init(dialogue_state_t *dlg);

/* Check for idle dialogue triggers */
void dialogue_check_triggers(dialogue_state_t *dlg,
                             const emotion_state_t *emotion,
                             const stats_t *stats,
                             const game_time_t *gt);

/* Force show a specific line */
void dialogue_force(dialogue_state_t *dlg, const char *text, uint32_t duration_ms);

/* Dismiss current dialogue */
void dialogue_dismiss(dialogue_state_t *dlg);

/* Tick: handle auto-dismiss */
void dialogue_tick(dialogue_state_t *dlg, uint32_t now_ms);

/* Get a random quote for an emotion */
const char *dialogue_get_quote(emotion_id_t emotion, life_stage_t stage);

#endif /* DILDER_DIALOG_H */
