#ifndef DILDER_EMOTION_H
#define DILDER_EMOTION_H

#include "game_state.h"
#include "event.h"

/* ─── Emotion Engine API ─────────────────────────────────────── */

void emotion_init(emotion_state_t *state);

/* Per-tick resolution (called every ~5 ticks) */
void emotion_resolve(emotion_state_t *state, const stats_t *stats,
                     const sensor_context_t *ctx, const life_state_t *life);

/* Force override */
void emotion_force(emotion_state_t *state, emotion_id_t emotion,
                   uint32_t duration_ms, uint32_t now_ms);

/* Queries */
emotion_id_t emotion_current(const emotion_state_t *state);
bool         emotion_changed(const emotion_state_t *state);

/* Event handlers (registered during game init) */
void emotion_on_care_action(event_type_t type, const event_data_t *data);

#endif /* DILDER_EMOTION_H */
