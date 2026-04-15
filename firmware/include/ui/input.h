#ifndef DILDER_INPUT_H
#define DILDER_INPUT_H

#include "game/game_state.h"

/* ─── Input System API ───────────────────────────────────────── */

void input_init(void);

/* Push a button event (from platform or emulator) */
void input_push(button_id_t id, press_type_t type);

/* Poll: returns the next queued event, or BTN_NONE */
button_event_t input_poll(void);

/* Check if any input is pending */
bool input_has_event(void);

#endif /* DILDER_INPUT_H */
