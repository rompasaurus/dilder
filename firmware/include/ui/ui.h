#ifndef DILDER_UI_H
#define DILDER_UI_H

#include "game/game_state.h"

/* ─── UI System API ──────────────────────────────────────────── */

void ui_init(ui_state_t *ui);

/* Handle a button event (dispatches based on game state) */
void ui_handle_input(button_event_t btn);

/* Mark display as needing redraw */
void ui_mark_dirty(void);
bool ui_needs_redraw(void);

/* Render the current screen to g_framebuffer */
void ui_render(void);

/* Menu operations */
void menu_open(menu_id_t menu);
void menu_close(void);

#endif /* DILDER_UI_H */
