#ifndef DILDER_EVENT_H
#define DILDER_EVENT_H

#include "game_state.h"

/* ─── Event Types ────────────────────────────────────────────── */
typedef enum {
    /* Stat events */
    EVENT_STAT_CRITICAL,
    EVENT_STAT_ZERO,
    EVENT_STAT_RECOVERED,
    EVENT_ALL_STATS_BALANCED,

    /* Care events */
    EVENT_FED,
    EVENT_PETTED,
    EVENT_CLEANED,
    EVENT_PLAYED,
    EVENT_SCOLDED,
    EVENT_MEDICINE,

    /* Sensor events */
    EVENT_LOUD_NOISE,
    EVENT_TALKING,
    EVENT_SILENCE_LONG,
    EVENT_SHAKEN,
    EVENT_DROPPED,
    EVENT_PICKED_UP,
    EVENT_TEMPERATURE_EXTREME,

    /* Activity events */
    EVENT_STEP_MILESTONE,
    EVENT_NEW_LOCATION,
    EVENT_HOME_ARRIVED,
    EVENT_HOME_LEFT,

    /* Progression events */
    EVENT_XP_GAINED,
    EVENT_BOND_LEVEL_UP,
    EVENT_ACHIEVEMENT_UNLOCK,

    /* Life events */
    EVENT_STAGE_TRANSITION,
    EVENT_EVOLUTION,
    EVENT_MISBEHAVIOR,
    EVENT_WAKE_UP,
    EVENT_SLEEP,

    /* System */
    EVENT_DAY_CHANGE,

    EVENT_TYPE_COUNT
} event_type_t;

/* ─── Event Data ─────────────────────────────────────────────── */
typedef struct {
    uint8_t  stat_id;
    int16_t  value;
    uint32_t timestamp;
} event_data_t;

/* ─── Event Record (ring buffer entry) ───────────────────────── */
#define EVENT_RING_SIZE 16

typedef struct {
    event_type_t type;
    int16_t      value;
    uint32_t     timestamp;
} event_record_t;

/* ─── Event Handler ──────────────────────────────────────────── */
typedef void (*event_handler_t)(event_type_t type, const event_data_t *data);

#define MAX_LISTENERS_PER_EVENT 4

/* ─── Event System API ───────────────────────────────────────── */
void event_init(void);
void event_listen(event_type_t type, event_handler_t handler);
void event_fire(event_type_t type, const event_data_t *data);

/* Query recent events */
bool event_recent(event_type_t type, uint32_t within_ms);
int  event_count_recent(uint32_t within_ms);

/* Access ring buffer */
const event_record_t *event_get_ring(void);
uint8_t event_get_ring_head(void);

#endif /* DILDER_EVENT_H */
