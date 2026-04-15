#ifndef DILDER_RENDER_H
#define DILDER_RENDER_H

#include "game/game_state.h"

/* ─── Pixel Operations on g_framebuffer ──────────────────────── */

void fb_clear(void);                          /* all white (0x00) */
void fb_fill(void);                           /* all black (0xFF) */
void fb_set_pixel(int x, int y);              /* set black */
void fb_clr_pixel(int x, int y);              /* set white */
int  fb_get_pixel(int x, int y);              /* returns 1=black, 0=white */

/* Drawing primitives */
void fb_line(int x0, int y0, int x1, int y1);
void fb_rect(int x, int y, int w, int h, bool filled);
void fb_circle(int cx, int cy, int r, bool filled);
void fb_hline(int x, int y, int w);
void fb_vline(int x, int y, int h);

/* Text rendering (built-in 6x8 bitmap font) */
void fb_char(int x, int y, char c);
void fb_string(int x, int y, const char *str);
void fb_string_wrap(int x, int y, int max_w, const char *str);

/* Inverted text (white on black) */
void fb_string_inv(int x, int y, const char *str);

/* ─── High-Level Screen Renderers ────────────────────────────── */

void render_pet_screen(const game_t *game);
void render_header(const game_t *game);
void render_stat_bar(int x, int y, const char *label, int16_t value);
void render_stat_icons(const primary_stats_t *stats);
void render_dialogue_box(const char *text);
void render_menu_overlay(const menu_state_t *menu, const game_t *game);
void render_stats_screen(const game_t *game);
void render_octopus(emotion_id_t emotion, life_stage_t stage);

#endif /* DILDER_RENDER_H */
