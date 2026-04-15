/*
 * game_state.h -- Master Game State Header
 *
 * PURPOSE:
 *   This is the most important header in the entire project.  It defines
 *   ALL of the data types (structs and enums) that make up the game's
 *   state.  Every .c file that needs to read or write game data includes
 *   this header.
 *
 * KEY CONCEPTS FOR C BEGINNERS:
 *
 *   STRUCTS:  A struct groups related variables together into one unit.
 *     Think of it like a Python class with only data (no methods).
 *     Example: `primary_stats_t` bundles hunger, happiness, energy, etc.
 *
 *   ENUMS:  An enum defines a set of named integer constants.
 *     Example: `emotion_id_t` defines EMOTION_NORMAL = 0, EMOTION_HUNGRY = 1,
 *     and so on.  Enums make code readable -- `EMOTION_HUNGRY` is clearer
 *     than the magic number `1`.
 *
 *   TYPEDEF:  `typedef struct { ... } name_t;` creates a type alias so
 *     you can write `primary_stats_t stats;` instead of the verbose
 *     `struct primary_stats stats;`.  The `_t` suffix is a common C
 *     convention meaning "this is a type."
 *
 *   FIXED-WIDTH INTEGER TYPES (from <stdint.h>):
 *     int8_t   = signed 8-bit  (-128 to 127)
 *     uint8_t  = unsigned 8-bit  (0 to 255)
 *     int16_t  = signed 16-bit  (-32768 to 32767)
 *     uint16_t = unsigned 16-bit  (0 to 65535)
 *     int32_t  = signed 32-bit  (-2 billion to 2 billion)
 *     uint32_t = unsigned 32-bit  (0 to ~4 billion)
 *     uint64_t = unsigned 64-bit  (0 to ~18 quintillion)
 *
 *     "signed" means the type can hold negative numbers.
 *     "unsigned" means only zero and positive numbers.
 *
 *     Why use these instead of plain `int`?  Because `int` can be 16-bit
 *     on some microcontrollers and 32-bit on others.  Fixed-width types
 *     guarantee the exact size, which matters for embedded systems where
 *     every byte counts and for binary compatibility across platforms.
 */

#ifndef DILDER_GAME_STATE_H
#define DILDER_GAME_STATE_H

#include <stdint.h>    /* fixed-width integer types: uint8_t, int16_t, etc. */
#include <stdbool.h>   /* bool, true, false (C99 -- C didn't have bool originally!) */
#include <string.h>    /* memset, memcpy, etc. */

/* ================================================================
 *  Display Constants
 *
 *  The Dilder hardware has a 250x122 pixel monochrome (1-bit-per-pixel)
 *  e-ink display.  Here's how 1bpp storage works:
 *
 *  Each pixel is either ON (1 = black) or OFF (0 = white).  Since one
 *  pixel is just one bit, we pack 8 pixels into each byte:
 *
 *    Byte:  [b7][b6][b5][b4][b3][b2][b1][b0]
 *            ^--- leftmost pixel       ^--- rightmost pixel
 *
 *  A 250-pixel-wide row needs 250/8 = 31.25 bytes.  Since we can't have
 *  a fraction of a byte, we round up to 32 bytes per row:
 *    SCREEN_ROW_BYTES = (250 + 7) / 8 = 32
 *  (The "+ 7" before dividing is a common trick for ceiling division
 *   with integers in C, since integer division truncates.)
 *
 *  Total buffer size = 32 bytes/row * 122 rows = 3904 bytes.
 *  That's the entire display in under 4 KB of RAM!
 * ================================================================ */
#define SCREEN_W       250
#define SCREEN_H       122
#define SCREEN_ROW_BYTES ((SCREEN_W + 7) / 8)  /* = 32 bytes per row */
#define SCREEN_BUF_SIZE  (SCREEN_ROW_BYTES * SCREEN_H)  /* = 3904 bytes total */

/* ================================================================
 *  Game States
 *
 *  The game runs as a state machine.  At any moment, the game is in
 *  exactly ONE of these states, which determines what gets drawn on
 *  screen and how input is handled.
 * ================================================================ */
typedef enum {
    GAME_STATE_BOOT,      /* startup animation / splash screen */
    GAME_STATE_ACTIVE,    /* normal play -- pet is awake, interactable */
    GAME_STATE_MENU,      /* a menu is open (feed, play, care, etc.) */
    GAME_STATE_SLEEPING,  /* pet is asleep -- limited interaction */
    GAME_STATE_HUNT,      /* a hunt/minigame is in progress */
    GAME_STATE_EVENT,     /* a special event is playing out */
    GAME_STATE_DEAD,      /* the pet has died -- game over */
} game_state_t;

/* ================================================================
 *  Emotions
 *
 *  The pet's current emotional state, driven by stats, sensor input,
 *  and player interactions.  Emotions affect the pet's sprite/animation
 *  and can influence stat decay rates.
 *
 *  EMOTION_COUNT is a common C pattern: it's not a real emotion, but
 *  since enum values start at 0 and auto-increment, EMOTION_COUNT
 *  automatically equals the total number of real emotions (16).
 *  This is useful for array sizing: `float weights[EMOTION_COUNT]`
 *  creates an array with exactly one slot per emotion.
 * ================================================================ */
typedef enum {
    EMOTION_NORMAL,       /* default state -- nothing special */
    EMOTION_HUNGRY,       /* hunger stat is low */
    EMOTION_TIRED,        /* energy stat is low */
    EMOTION_SAD,          /* happiness is low or neglected */
    EMOTION_ANGRY,        /* overfed, disturbed, or frustrated */
    EMOTION_EXCITED,      /* high happiness, just played or bonded */
    EMOTION_CHILL,        /* well-balanced stats, relaxed */
    EMOTION_LAZY,         /* low energy + low discipline */
    EMOTION_FAT,          /* weight is too high (overfed) */
    EMOTION_CHAOTIC,      /* unpredictable -- mix of high/low stats */
    EMOTION_WEIRD,        /* unusual sensor conditions */
    EMOTION_UNHINGED,     /* extreme neglect or very strange inputs */
    EMOTION_SLAP_HAPPY,   /* over-tired but somehow giddy */
    EMOTION_HORNY,        /* ... it's a pet with personality */
    EMOTION_NOSTALGIC,    /* triggered by certain time/age conditions */
    EMOTION_HOMESICK,     /* away from home too long (wifi context) */
    EMOTION_COUNT         /* NOT a real emotion -- equals the total count (16) */
} emotion_id_t;

/* ================================================================
 *  Life Stages
 *
 *  The pet grows through these stages over time, like a real creature.
 *  Each stage has different stat decay rates, available evolutions,
 *  and visual appearances.
 * ================================================================ */
typedef enum {
    LIFE_STAGE_EGG,         /* initial state, waiting to hatch */
    LIFE_STAGE_HATCHLING,   /* just hatched, fragile, needs lots of care */
    LIFE_STAGE_JUVENILE,    /* growing up, starting to show personality */
    LIFE_STAGE_ADOLESCENT,  /* teenage phase, can misbehave */
    LIFE_STAGE_ADULT,       /* fully grown, evolution form is determined */
    LIFE_STAGE_ELDER,       /* old age, slower but wiser */
    LIFE_STAGE_COUNT        /* total number of stages (6) */
} life_stage_t;

/* ================================================================
 *  Evolution Forms
 *
 *  When the pet reaches adulthood, its cumulative care history
 *  determines which form it evolves into.  Each form has a unique
 *  appearance and personality traits.
 * ================================================================ */
typedef enum {
    EVOLUTION_NONE,              /* not yet evolved (pre-adult stages) */
    EVOLUTION_DEEP_SEA_SCHOLAR,  /* high intelligence + care quality */
    EVOLUTION_REEF_GUARDIAN,     /* high fitness + exploration */
    EVOLUTION_TIDAL_TRICKSTER,   /* high happiness + chaotic tendencies */
    EVOLUTION_ABYSSAL_HERMIT,    /* low social interaction, high discipline */
    EVOLUTION_CORAL_DANCER,      /* high happiness + music exposure */
    EVOLUTION_STORM_KRAKEN,      /* high discipline + aggressive play */
    EVOLUTION_COUNT              /* total evolution forms (7 including NONE) */
} evolution_form_t;

/* ================================================================
 *  Stat IDs
 *
 *  Enum for referencing stats by ID (useful for generic stat
 *  manipulation functions that operate on any stat).
 * ================================================================ */
typedef enum {
    STAT_HUNGER,      /* 0 */
    STAT_HAPPINESS,   /* 1 */
    STAT_ENERGY,      /* 2 */
    STAT_HYGIENE,     /* 3 */
    STAT_HEALTH,      /* 4 */
    STAT_WEIGHT,      /* 5 */
    STAT_COUNT        /* total (6) -- useful for loop bounds */
} stat_id_t;

/* ================================================================
 *  Primary Stats
 *
 *  The core vitals of the pet -- these are the numbers the player
 *  directly manages through care actions.  Each ranges from 0 to 100.
 *
 *  Stored as int16_t (signed 16-bit, -32768..32767) rather than uint8_t
 *  (0..255) because during calculations, intermediate values can
 *  temporarily go negative before being clamped back to 0..100.
 *  Using a signed type prevents underflow bugs.
 * ================================================================ */
typedef struct {
    int16_t hunger;      /* 0 = starving, 100 = full */
    int16_t happiness;   /* 0 = miserable, 100 = ecstatic */
    int16_t energy;      /* 0 = exhausted, 100 = fully rested */
    int16_t hygiene;     /* 0 = filthy, 100 = squeaky clean */
    int16_t health;      /* 0 = critically ill, 100 = perfect health */
} primary_stats_t;

/* ================================================================
 *  Secondary Stats
 *
 *  Longer-term attributes that change more slowly than primary stats.
 *  These accumulate over the pet's lifetime and influence evolution.
 *
 *  Note the mix of types chosen to fit the value range:
 *    - uint32_t for bond_xp and age (can grow very large)
 *    - uint16_t for discipline, intelligence, etc. (0..65535 is plenty)
 *    - int16_t for weight (signed, so it can theoretically go negative
 *      during calculations before clamping)
 * ================================================================ */
typedef struct {
    uint32_t bond_xp;        /* experience points measuring player-pet bond */
    uint16_t discipline;     /* how well-behaved the pet is */
    uint16_t intelligence;   /* accumulated from learning activities */
    uint16_t fitness;        /* accumulated from physical activities (steps, play) */
    uint16_t exploration;    /* accumulated from going to new places */
    uint32_t age_seconds;    /* total age in game-seconds (uint32 = ~136 years max) */
    int16_t  weight;         /* body weight, affected by feeding habits */
} secondary_stats_t;

/* ================================================================
 *  Hidden Stats
 *
 *  Internal tracking values the player never sees directly.  These
 *  influence emotion calculations, evolution outcomes, and game events
 *  behind the scenes.
 * ================================================================ */
typedef struct {
    uint16_t care_mistakes;        /* times the player made a bad care choice */
    uint16_t consecutive_days;     /* days in a row the player has cared for the pet */
    uint16_t noise_exposure;       /* how much loud noise the pet has endured */
    uint16_t night_disturbances;   /* times the pet was disturbed during sleep */
    uint32_t last_interaction_ms;  /* timestamp of last player input (milliseconds) */
    uint32_t neglect_timer_ms;     /* how long since last meaningful interaction */
} hidden_stats_t;

/* ================================================================
 *  Combined Stats
 *
 *  A convenience struct that nests all three stat categories together.
 *  This way, the top-level game struct only needs one `stats` field
 *  instead of three separate fields.
 *
 *  Access pattern: g_game.stats.primary.hunger
 *                  g_game.stats.hidden.neglect_timer_ms
 * ================================================================ */
typedef struct {
    primary_stats_t   primary;
    secondary_stats_t secondary;
    hidden_stats_t    hidden;
} stats_t;

/* ================================================================
 *  Modifier Stack
 *
 *  Modifiers are multipliers that adjust how fast stats change.
 *  For example, the pet's life stage might make hunger decay faster
 *  (hatchlings get hungry quickly), or being at a high bond level
 *  might slow happiness decay.
 *
 *  Each modifier type contributes a float multiplier (e.g., 1.0 = no
 *  change, 1.5 = 50% faster, 0.5 = 50% slower).  The game engine
 *  combines all active modifiers when calculating stat changes.
 * ================================================================ */
typedef enum {
    MOD_LIFE_STAGE,    /* modifier based on the pet's current life stage */
    MOD_BOND_LEVEL,    /* modifier based on player-pet bond strength */
    MOD_ENVIRONMENT,   /* modifier based on sensor readings (temp, light, etc.) */
    MOD_TIME_OF_DAY,   /* modifier based on in-game time (day vs. night) */
    MOD_ACTIVITY,      /* modifier based on physical activity (steps) */
    MOD_STREAK,        /* modifier based on consecutive care days */
    MOD_COUNT          /* total modifier types (6) */
} modifier_type_t;

typedef struct {
    float values[MOD_COUNT];  /* one multiplier per modifier type */
} modifier_stack_t;

/* ================================================================
 *  Decay Accumulators
 *
 *  Stats don't decrease by whole numbers every tick -- that would be
 *  too fast.  Instead, each tick adds a small fractional amount to
 *  these accumulators.  When an accumulator reaches a threshold (e.g.,
 *  1000), one point is subtracted from the corresponding stat and the
 *  accumulator resets.
 *
 *  This pattern allows very fine-grained decay rates (e.g., 3.7 units
 *  per tick) without using floating-point math for the stats themselves.
 *  The uint32_t type gives plenty of headroom for accumulation.
 * ================================================================ */
typedef struct {
    uint32_t hunger_accum;
    uint32_t happiness_accum;
    uint32_t energy_accum;
    uint32_t hygiene_accum;
} decay_accum_t;

/* ================================================================
 *  Care Actions
 *
 *  Things the player can do to care for the pet.  Each action has
 *  different effects on stats and may have cooldown timers to prevent
 *  spamming.
 * ================================================================ */
typedef enum {
    CARE_FEED_MEAL,    /* give a full meal (big hunger boost) */
    CARE_FEED_SNACK,   /* give a snack (small hunger boost, adds weight) */
    CARE_FEED_TREAT,   /* give a treat (happiness boost, adds weight) */
    CARE_CLEAN,        /* clean/bathe the pet (hygiene boost) */
    CARE_MEDICINE,     /* give medicine (health boost, pet doesn't like it) */
    CARE_PET,          /* pet/stroke the creature (happiness + bond XP) */
    CARE_PLAY,         /* play a game (happiness + fitness + bond XP) */
    CARE_TICKLE,       /* tickle (small happiness boost, fun interaction) */
    CARE_SCOLD,        /* scold for misbehavior (discipline boost, happiness drop) */
    CARE_SLEEP_TOGGLE, /* put to sleep or wake up */
    CARE_COUNT         /* total care actions (10) */
} care_action_t;

/* ================================================================
 *  Bond Levels
 *
 *  The relationship between the player and pet grows over time as
 *  bond_xp accumulates.  Each level unlocks new interactions or
 *  modifies the pet's behavior.
 * ================================================================ */
typedef enum {
    BOND_STRANGER,      /* just met -- default starting level */
    BOND_ACQUAINTANCE,  /* some familiarity */
    BOND_COMPANION,     /* reliable presence */
    BOND_FRIEND,        /* trusted friend */
    BOND_BEST_FRIEND,   /* deep bond */
    BOND_SOULMATE,      /* maximum bond level */
    BOND_COUNT          /* total levels (6) */
} bond_level_t;

/* ================================================================
 *  Emotion State
 *
 *  The emotion system is more complex than a simple enum -- it uses
 *  weighted scoring.  Each emotion has a "weight" (a score based on
 *  current stats, sensors, etc.), and the emotion with the highest
 *  weight becomes the current emotion.
 *
 *  The "dwell" timer prevents rapid flickering between emotions:
 *  once an emotion is set, it must stay for at least min_dwell_ms
 *  before it can change.
 * ================================================================ */
typedef struct {
    emotion_id_t current;              /* the emotion currently displayed */
    emotion_id_t previous;             /* what the emotion was before the last change */
    float        weights[EMOTION_COUNT]; /* score for each possible emotion */
    float        current_weight;       /* the winning score (weight of current emotion) */
    uint32_t     dwell_start_ms;       /* when the current emotion started */
    uint32_t     min_dwell_ms;         /* minimum time before emotion can change */
    bool         changed;              /* true if the emotion changed this tick */
    bool         in_transition;        /* true if transitioning between emotions */
    bool         forced;               /* true if an event forced a specific emotion */
    uint32_t     force_end_ms;         /* when the forced emotion expires */
} emotion_state_t;

/* ================================================================
 *  Life State
 *
 *  Tracks the pet's growth, evolution, misbehavior, and rebirth
 *  (generational) data.  This is where the long-term progression
 *  lives.
 * ================================================================ */
typedef struct {
    life_stage_t     stage;                /* current life stage (egg..elder) */
    uint32_t         age_seconds;          /* total age in game-seconds */
    uint32_t         stage_start_seconds;  /* age when the current stage began */
    evolution_form_t adult_form;           /* which form the pet evolved into */
    uint16_t         hatch_progress;       /* 0..100 progress toward hatching (egg stage) */

    /* --- Evolution Accumulators ---
     * These values accumulate over the pet's lifetime and determine
     * which adult form it evolves into.  Different combinations of
     * high/low values map to different evolutions.
     */
    uint16_t total_care_quality;    /* how good the overall care has been */
    uint16_t total_discipline;      /* accumulated discipline from scolding */
    uint16_t total_intelligence;    /* accumulated from learning activities */
    uint16_t total_fitness;         /* accumulated from physical activities */
    uint16_t total_exploration;     /* accumulated from exploration */
    uint16_t total_happiness_avg;   /* running average of happiness over time */
    uint16_t total_music_exposure;  /* how much music/sound the pet has heard */
    uint16_t total_scold_count;     /* how many times the pet was scolded */

    /* --- Misbehavior ---
     * The pet can misbehave (especially during adolescence).  The player
     * has a window of time to scold the pet; if they do, discipline goes
     * up.  If they don't, it's a missed opportunity.
     */
    bool     misbehaving;             /* true if the pet is currently acting up */
    uint32_t misbehave_start_ms;      /* when the misbehavior started */
    uint32_t misbehave_timeout_ms;    /* deadline to respond with a scold */
    uint8_t  discipline_windows;      /* how many scold opportunities have occurred */

    /* --- Rebirth ---
     * When the pet dies (or reaches elder stage), the player can start a
     * new generation.  Some traits carry over from the previous life,
     * creating a legacy system.
     */
    uint8_t          generation;        /* which generation this pet is (0 = first) */
    uint32_t         heritage_bond_xp;  /* bond XP inherited from previous generation */
    evolution_form_t heritage_form;     /* evolution form of the previous generation */
} life_state_t;

/* ================================================================
 *  Progression
 *
 *  Player-level progression that persists across the pet's life.
 *
 *  achievement_flags is a 64-bit bitmask: each bit represents one
 *  achievement (bit 0 = "first feeding", bit 1 = "reached juvenile",
 *  etc.).  This is a memory-efficient way to store up to 64 boolean
 *  flags in a single variable.  To check if achievement N is unlocked:
 *    if (achievement_flags & (1ULL << N)) { ... }
 * ================================================================ */
typedef struct {
    uint32_t    bond_xp;            /* total bond experience points */
    bond_level_t bond_level;        /* current bond level (derived from bond_xp) */
    uint64_t    achievement_flags;  /* bitmask of unlocked achievements (up to 64) */
} progression_t;

/* ================================================================
 *  Activity
 *
 *  Physical activity tracking, primarily driven by the accelerometer
 *  sensor on real hardware (or emulated step counts on desktop).
 * ================================================================ */
typedef struct {
    uint32_t daily_steps;   /* steps counted today */
    uint32_t total_steps;   /* all-time step count */
    uint8_t  step_tier;     /* activity tier (e.g., sedentary/active/athletic) */
    uint16_t streak_days;   /* consecutive days meeting the step goal */
} activity_t;

/* ================================================================
 *  Dialogue
 *
 *  The pet can display text messages (reactions, quips, status
 *  messages).  This struct tracks the current dialogue state.
 *
 *  current_text is a fixed-size character array (not a pointer to
 *  dynamically allocated memory).  In embedded C, we avoid malloc/free
 *  because dynamic memory allocation can fragment limited RAM and is
 *  hard to debug.  Fixed-size buffers are predictable and safe.
 * ================================================================ */
#define DIALOGUE_MAX_LEN 128  /* maximum characters in a dialogue string */

typedef struct {
    bool    showing;                        /* true if dialogue is visible on screen */
    bool    pending;                        /* true if new dialogue is queued */
    char    current_text[DIALOGUE_MAX_LEN]; /* the text content (fixed-size buffer) */
    uint32_t show_start_ms;                 /* when the dialogue started showing */
    uint32_t show_duration_ms;              /* how long to display it before auto-hide */
} dialogue_state_t;

/* ================================================================
 *  Game Time
 *
 *  The game tracks its own internal clock.  On real hardware this
 *  comes from the system timer; on desktop it's the emulated time
 *  from dilder_api.c.
 * ================================================================ */
typedef struct {
    uint32_t now_ms;      /* current time in milliseconds since game start */
    uint32_t hour;        /* current hour (0-23) */
    uint32_t minute;      /* current minute (0-59) */
    uint32_t second;      /* current second (0-59) */
    uint32_t day;         /* current day number (starts at 0) */
    bool     is_daytime;  /* true if it's daytime in the game world */
} game_time_t;

/* ================================================================
 *  Button Input
 *
 *  The physical device has 5 buttons.  Each button press is captured
 *  as an event with the button ID, press type, and timestamp.
 * ================================================================ */
typedef enum {
    BTN_NONE,     /* 0 -- no button (used as a sentinel/default value) */
    BTN_UP,       /* 1 -- navigate up in menus */
    BTN_DOWN,     /* 2 -- navigate down in menus */
    BTN_SELECT,   /* 3 -- confirm/select current menu item */
    BTN_BACK,     /* 4 -- go back / cancel */
    BTN_ACTION,   /* 5 -- primary action (feed, play, etc.) */
} button_id_t;

typedef enum {
    PRESS_NONE,    /* 0 -- no press (sentinel value) */
    PRESS_SHORT,   /* 1 -- quick tap */
    PRESS_LONG,    /* 2 -- press and hold */
    PRESS_DOUBLE,  /* 3 -- double-tap */
} press_type_t;

/*
 * A button event bundles the button ID, press type, and the time it
 * happened.  Events are queued and processed during the game tick.
 */
typedef struct {
    button_id_t  id;         /* which button was pressed */
    press_type_t type;       /* how it was pressed (short, long, double) */
    uint32_t     timestamp;  /* when it happened (milliseconds) */
} button_event_t;

/* ================================================================
 *  Menu
 *
 *  The menu system is a simple stack-based hierarchy.  Opening a
 *  submenu pushes onto the stack; pressing Back pops it.
 * ================================================================ */
typedef enum {
    MENU_NONE,       /* no menu open */
    MENU_MAIN,       /* top-level menu */
    MENU_FEED,       /* feeding submenu (meal, snack, treat) */
    MENU_PLAY,       /* play submenu */
    MENU_CARE,       /* care submenu (clean, medicine, pet) */
    MENU_STATS,      /* stats view */
    MENU_SETTINGS,   /* settings submenu */
} menu_id_t;

typedef struct {
    menu_id_t current_menu;   /* which menu is currently displayed */
    uint8_t   cursor;         /* which menu item the cursor is on (0-based) */
    uint8_t   scroll_offset;  /* for scrollable menus: first visible item index */
    uint8_t   stack_depth;    /* how many menus deep we are (0 = no menu open) */
    menu_id_t stack[4];       /* menu history stack (max 4 levels deep) */
} menu_state_t;

/* ================================================================
 *  Screen Types
 *
 *  Different screens the UI can display.  Only one is active at a time.
 * ================================================================ */
typedef enum {
    SCREEN_PET,    /* main screen: shows the pet and its current emotion */
    SCREEN_MENU,   /* a menu overlay */
    SCREEN_STATS,  /* stats display screen */
    SCREEN_STEPS,  /* step counter / activity screen */
} screen_id_t;

/* ================================================================
 *  UI State
 *
 *  Tracks which screen is showing and whether the display needs to be
 *  redrawn.  The "dirty" flag is a common optimization: instead of
 *  redrawing every frame, we only redraw when something has changed.
 * ================================================================ */
typedef struct {
    screen_id_t current_screen;   /* which screen is active */
    bool        dirty;            /* true = screen needs redrawing */
    uint32_t    last_refresh_ms;  /* when the screen was last redrawn */
} ui_state_t;

/* ================================================================
 *  Sensor Data
 *
 *  These structs hold the latest readings from the hardware sensors
 *  (or emulated values on desktop).  The game engine reads these to
 *  influence the pet's mood, comfort, and behavior.
 * ================================================================ */

/*
 * Light sensor data.
 * "zone" is a classified light level (see LIGHT_* defines below).
 */
typedef struct {
    float    lux;         /* raw light level in lux (0 = pitch dark, 100000+ = sunlight) */
    float    delta_lux;   /* change in lux since last reading (for detecting sudden changes) */
    uint8_t  zone;        /* classified zone: DARK, DIM, INDOOR, or BRIGHT */
} light_data_t;

/* Light zone thresholds -- used to classify the raw lux value */
#define LIGHT_BRIGHT  3   /* direct sunlight or very bright room */
#define LIGHT_INDOOR  2   /* normal indoor lighting */
#define LIGHT_DIM     1   /* dim room, evening lighting */
#define LIGHT_DARK    0   /* near-total darkness */

/*
 * Temperature and humidity sensor data.
 * "comfort_zone" classifies whether the pet is comfortable.
 */
typedef struct {
    float    celsius;       /* temperature in degrees Celsius */
    float    humidity_pct;  /* relative humidity as a percentage (0-100) */
    uint8_t  comfort_zone;  /* classified comfort: GOOD, HOT, COLD, HUMID, or DRY */
} environment_data_t;

/* Comfort zone classifications */
#define COMFORT_GOOD   0  /* temperature and humidity are comfortable */
#define COMFORT_HOT    1  /* too hot (e.g., > 30C) */
#define COMFORT_COLD   2  /* too cold (e.g., < 15C) */
#define COMFORT_HUMID  3  /* too humid */
#define COMFORT_DRY    4  /* too dry */

/*
 * Accelerometer data -- detects motion, steps, shaking, etc.
 * x, y, z are raw acceleration values from the sensor.
 */
typedef struct {
    int16_t  x, y, z;            /* raw 3-axis acceleration (signed -- can be negative) */
    uint32_t step_count;         /* total steps detected */
    uint16_t steps_since_last;   /* steps since last tick */
    bool     walking;            /* currently walking? */
    bool     running;            /* currently running? */
    bool     shaking;            /* device is being shaken? */
    bool     falling;            /* free-fall detected? */
    bool     picked_up;          /* device was just picked up? */
    bool     stationary;         /* device is not moving? */
    uint8_t  tilt_angle;         /* angle of tilt in degrees (0-180) */
} accel_data_t;

/*
 * Microphone data -- detects ambient sound level.
 */
typedef struct {
    uint16_t level;        /* current sound level (arbitrary units) */
    uint16_t peak;         /* peak level in the current measurement window */
    uint8_t  zone;         /* classified zone: SILENT..YELL */
    uint32_t duration_ms;  /* how long the current noise level has persisted */
} mic_data_t;

/* Microphone zone classifications */
#define MIC_SILENT   0  /* no sound */
#define MIC_QUIET    1  /* whisper level */
#define MIC_MODERATE 2  /* normal conversation */
#define MIC_LOUD     3  /* loud music, shouting nearby */
#define MIC_YELL     4  /* extremely loud -- startles the pet */

/*
 * WiFi context -- used to determine if the device is "at home."
 * On real hardware this could check for a known WiFi network.
 */
typedef struct {
    bool     at_home;           /* true if connected to the home network */
    bool     away_from_home;    /* true if not at home (inverse, but explicit) */
    uint32_t away_duration_ms;  /* how long the pet has been away from home */
} wifi_context_t;

/*
 * Combined sensor context -- bundles ALL sensor data into one struct.
 * The game engine accesses this as g_game.sensor.light.lux,
 * g_game.sensor.env.celsius, etc.
 */
typedef struct {
    light_data_t       light;      /* light sensor */
    environment_data_t env;        /* temperature + humidity */
    accel_data_t       accel;      /* accelerometer / motion */
    mic_data_t         mic;        /* microphone */
    wifi_context_t     wifi;       /* WiFi / location context */
    uint32_t           timestamp;  /* when these readings were taken */
} sensor_context_t;

/* ================================================================
 *  Cooldowns
 *
 *  After performing a care action, there's a cooldown period before
 *  the same action can be used again.  This prevents the player from
 *  spamming "feed" to max out hunger instantly.
 *
 *  Each entry in the array is the remaining cooldown in ticks for
 *  the corresponding care_action_t.  0 = ready to use.
 * ================================================================ */
typedef struct {
    uint16_t cooldowns[CARE_COUNT];  /* one cooldown timer per care action */
} care_cooldown_t;

/* ================================================================
 *  Top-Level Game Struct
 *
 *  THIS IS THE BIG ONE.  This single struct holds the ENTIRE game
 *  state.  Every subsystem's data is nested inside it.
 *
 *  There is exactly ONE instance of this struct (the global g_game),
 *  and every part of the game engine reads from and writes to it.
 *
 *  Why one big struct instead of separate globals?  Because:
 *    1. It's easy to save/load -- just write/read the whole struct.
 *    2. It's easy to reset -- just zero-fill it.
 *    3. It makes dependencies clear -- if a function takes a game_t*,
 *       you know it might touch any part of the game state.
 * ================================================================ */
typedef struct {
    game_state_t     state;        /* current high-level game state (boot/active/menu/etc.) */
    stats_t          stats;        /* all stats: primary, secondary, hidden */
    modifier_stack_t modifiers;    /* stat change rate multipliers */
    decay_accum_t    decay_accum;  /* fractional stat decay accumulators */
    care_cooldown_t  care_cd;      /* cooldown timers for care actions */
    emotion_state_t  emotion;      /* emotional state and scoring */
    life_state_t     life;         /* life stage, evolution, misbehavior, rebirth */
    progression_t    progression;  /* bond level and achievements */
    activity_t       activity;     /* step counting and activity streaks */
    dialogue_state_t dialogue;     /* current dialogue text */
    menu_state_t     menu;         /* menu navigation state */
    ui_state_t       ui;           /* screen display state */
    sensor_context_t sensor;       /* latest sensor readings */
    game_time_t      time;         /* in-game clock */

    /* --- Tick Tracking --- */
    uint32_t tick_count;    /* total ticks since game start */
    uint32_t last_tick_ms;  /* timestamp of the most recent tick */
    uint32_t last_save_ms;  /* when the game was last saved to flash/disk */
} game_t;

/*
 * Global game instance.
 *
 * "extern" means: "this variable EXISTS, but it's defined in another
 * .c file (not here)."  This header is included by many .c files, but
 * only ONE of them (e.g., game_loop.c) actually creates the variable:
 *
 *   game_t g_game;    // <-- the actual definition, in one .c file
 *
 * Every other file sees this "extern" declaration and knows the variable
 * exists somewhere -- the linker connects them all together.  Without
 * "extern", each .c file would try to create its own copy, and you'd
 * get "multiple definition" linker errors.
 */
extern game_t g_game;

/*
 * Global framebuffer -- the raw pixel data for the 250x122 1bpp display.
 *
 * Like g_game, this is defined in one .c file and declared "extern" here
 * so all files can access it.  The render system writes pixels into it,
 * and the display driver (or Python DevTool) reads from it.
 */
extern uint8_t g_framebuffer[SCREEN_BUF_SIZE];

/* ================================================================
 *  Helper Functions
 *
 *  "static inline" functions defined in a header file.
 *
 *  WHAT IS "inline"?
 *    Normally, calling a function involves overhead: push arguments onto
 *    the stack, jump to the function's code, execute it, jump back.  For
 *    tiny functions like "clamp a value to a range," this overhead can be
 *    larger than the actual work.
 *
 *    "inline" is a hint to the compiler: "instead of generating a function
 *    call, copy (inline) the function's body directly into each call site."
 *    This eliminates the call overhead at the cost of slightly larger code.
 *
 *  WHY "static"?
 *    In a header file, "static" means each .c file that includes this
 *    header gets its own private copy of the function.  This avoids
 *    "multiple definition" linker errors that would occur if the function
 *    were non-static and included by multiple files.
 *
 *  Together, "static inline" is the standard pattern for small helper
 *  functions in C header files.
 * ================================================================ */

/*
 * clamp_i16 -- constrain a signed 16-bit value to the range [lo, hi].
 * If val < lo, returns lo.  If val > hi, returns hi.  Otherwise returns val.
 * Used heavily for keeping stats in the 0..100 range.
 */
static inline int16_t clamp_i16(int16_t val, int16_t lo, int16_t hi) {
    if (val < lo) return lo;
    if (val > hi) return hi;
    return val;
}

/* clamp_u16 -- same as clamp_i16 but for unsigned 16-bit values. */
static inline uint16_t clamp_u16(uint16_t val, uint16_t lo, uint16_t hi) {
    if (val < lo) return lo;
    if (val > hi) return hi;
    return val;
}

/* clamp_f -- same as above but for floating-point values. */
static inline float clamp_f(float val, float lo, float hi) {
    if (val < lo) return lo;
    if (val > hi) return hi;
    return val;
}

/*
 * fminf_safe / fmaxf_safe -- return the smaller/larger of two floats.
 *
 * These are "safe" alternatives to the standard library's fminf/fmaxf.
 * Some embedded toolchains don't include the full math library, so we
 * define our own using the ternary operator:
 *   condition ? value_if_true : value_if_false
 */
static inline float fminf_safe(float a, float b) { return a < b ? a : b; }
static inline float fmaxf_safe(float a, float b) { return a > b ? a : b; }

/* ================================================================
 *  String Name Lookup Functions
 *
 *  These functions convert enum values to human-readable strings.
 *  They are declared here (in the header) but DEFINED in a .c file.
 *  Each one typically contains a switch statement or lookup table.
 *
 *  Example usage:
 *    printf("Emotion: %s\n", emotion_name(EMOTION_HUNGRY));
 *    // prints: "Emotion: hungry"
 * ================================================================ */
const char *emotion_name(emotion_id_t id);
const char *life_stage_name(life_stage_t stage);
const char *game_state_name(game_state_t state);
const char *care_action_name(care_action_t action);

#endif /* DILDER_GAME_STATE_H */
