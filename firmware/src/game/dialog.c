/*
 * dialog.c -- Dialogue / Quote System
 *
 * This module manages the text speech bubbles that appear on the Dilder's
 * display. Each emotion has a pool of themed quotes, and when the creature's
 * emotion changes, a random quote is selected and shown for a duration.
 *
 * Key concepts used in this file:
 *   - Arrays of pointers to strings (const char *QUOTES_X[]): each element
 *     is a pointer to a string literal. The string literals themselves live
 *     in read-only memory; the array stores pointers to them.
 *   - The QSET macro: a convenience for building a { pointer, count } pair
 *     from a string array, using the sizeof trick to count elements.
 *   - Designated initializers: `[EMOTION_NORMAL] = value` initializes a
 *     specific index of an array by name rather than position. This makes
 *     the mapping explicit and safe even if enum values change.
 *   - XorShift PRNG: a simple pseudo-random number generator that uses
 *     bitwise XOR and bit-shift operations for fast, lightweight randomness.
 *   - static variables: the RNG state persists across calls (static), and
 *     the quote arrays are static const (private + read-only).
 */

#include "game/dialog.h"
#include "game/time_mgr.h"
#include <string.h>
#include <stdlib.h>

/* ─── Built-in Quote Database ────────────────────────────────────
 *
 * Each QUOTES_* array below is declared as:
 *   static const char *QUOTES_X[] = { "str1", "str2", ... };
 *
 * Let's break down what this type means:
 *
 *   static    -- file-scoped (private to this .c file, not visible to other files)
 *   const     -- the pointer array itself won't be modified at runtime
 *   char *    -- each element is a pointer to a character (i.e., a C string)
 *   []        -- it's an array; the compiler counts the elements for us
 *
 * So each array is a list of pointers, where each pointer aims at a string
 * literal. String literals like "Just vibin'." are stored in the read-only
 * data segment (.rodata) by the compiler. On embedded systems this typically
 * means flash memory, saving precious RAM.
 *
 * The `static const` qualifier means the arrays themselves are also stored
 * in the read-only segment. They cannot be modified at runtime.
 *
 * Organized by emotion. A few quotes per mood for the emulator.
 * The full 800+ quote set will be pulled from the existing quotes.h later.
 */

static const char *QUOTES_NORMAL[] = {
    "Just vibin'.",
    "Nice day to exist.",
    "I wonder what's for dinner...",
    "*hums quietly*",
    "Life is good.",
    "Hey. You. Yeah you. Hi.",
};

static const char *QUOTES_HUNGRY[] = {
    "FEED ME.",
    "Is that... food I smell?",
    "My tummy is speaking to me.",
    "hungwy...",
    "*stomach growls ominously*",
};

static const char *QUOTES_TIRED[] = {
    "zzzZZZzzz...",
    "Five more minutes...",
    "*yawns dramatically*",
    "Can barely keep my eyes open.",
    "Sleep... need... sleep...",
};

static const char *QUOTES_SAD[] = {
    "Nobody loves me...",
    "*sniff*",
    "Do you even care?",
    "I'm fine. Everything is fine.",
    "Why is the world so cold?",
};

static const char *QUOTES_ANGRY[] = {
    "DON'T TOUCH ME.",
    "I'm NOT mad. I'm FURIOUS.",
    "GRRRR!",
    ">:(",
    "That was UNCALLED for.",
};

static const char *QUOTES_EXCITED[] = {
    "YESSS!!!",
    "OMG OMG OMG!",
    "This is the best day EVER!",
    "*bounces around*",
    "WOOOOOO!",
};

static const char *QUOTES_CHILL[] = {
    "Ahh... peace.",
    "This is nice.",
    "No thoughts. Head empty.",
    "*relaxed bubbling*",
    "Living the dream.",
};

static const char *QUOTES_LAZY[] = {
    "Effort? Never heard of her.",
    "I'll do it later...",
    "*doesn't move*",
    "Why stand when you can sit?",
};

static const char *QUOTES_FAT[] = {
    "I regret nothing.",
    "*waddles*",
    "More food please.",
    "I'm not fat, I'm fluffy.",
};

static const char *QUOTES_CHAOTIC[] = {
    "AAAAAAHHHH!",
    "EVERYTHING IS HAPPENING!",
    "CHAOS REIGNS!",
    "*screams in octopus*",
};

static const char *QUOTES_WEIRD[] = {
    "Did you know octopi have 3 hearts?",
    "I can taste with my tentacles.",
    "*stares into the void*",
    "The void stares back.",
};

static const char *QUOTES_UNHINGED[] = {
    "haha... ha... hahahaha",
    "I've seen things...",
    "nothing matters. everything matters.",
    "THE DEEP CALLS.",
};

static const char *QUOTES_SLAPHAPPY[] = {
    "HAHAHA I'M SO HAPPY!",
    "EVERYTHING IS AMAZING!",
    "*laughs uncontrollably*",
};

static const char *QUOTES_HORNY[] = {
    "Hey there...",
    "*wiggles tentacles suggestively*",
    "Is it hot in here or is it just me?",
};

static const char *QUOTES_NOSTALGIC[] = {
    "Remember when...",
    "Those were the days.",
    "Time flies, doesn't it?",
};

static const char *QUOTES_HOMESICK[] = {
    "I miss home...",
    "When are we going back?",
    "It's not the same here.",
};

/* ─── Quote Set Accessor ────────────────────────────────────────
 *
 * We need a way to look up "give me the quote array for emotion X."
 * The quote_set_t struct bundles a pointer to the array with its element
 * count, so we can iterate safely without going out of bounds.
 */

typedef struct {
    const char **quotes;  /* pointer to the first element of a QUOTES_* array */
    int count;            /* number of quotes in that array */
} quote_set_t;

/*
 * QSET macro -- Creates a quote_set_t initializer from an array name.
 *
 * Example: QSET(QUOTES_NORMAL) expands to:
 *   { QUOTES_NORMAL, sizeof(QUOTES_NORMAL) / sizeof(QUOTES_NORMAL[0]) }
 *
 * Breaking this down:
 *   QUOTES_NORMAL         -- the array name, which decays to a pointer
 *                            (const char **) when used in this context
 *   sizeof(arr)           -- total size of the array in bytes
 *   sizeof(arr[0])        -- size of one element (a pointer) in bytes
 *   sizeof(arr)/sizeof(arr[0]) -- number of elements (compile-time constant)
 *
 * This is the standard C idiom for computing array length. It only works
 * on actual arrays (not pointers), which is why we do it here in the
 * macro where `arr` is still known to the compiler as an array.
 */
#define QSET(arr) { arr, sizeof(arr) / sizeof(arr[0]) }

/*
 * QUOTE_SETS[] -- Maps each emotion ID to its quote pool.
 *
 * This uses C99 "designated initializers": [EMOTION_NORMAL] = value
 * explicitly sets the array element at index EMOTION_NORMAL. This is
 * safer than positional initialization because:
 *   1. The mapping is self-documenting (you can see which enum maps where)
 *   2. If someone reorders the emotion_id_t enum, this still works correctly
 *   3. Any unmentioned slots are zero-initialized (quotes=NULL, count=0)
 *
 * static const: stored in read-only memory, private to this file.
 */
static const quote_set_t QUOTE_SETS[EMOTION_COUNT] = {
    [EMOTION_NORMAL]     = QSET(QUOTES_NORMAL),
    [EMOTION_HUNGRY]     = QSET(QUOTES_HUNGRY),
    [EMOTION_TIRED]      = QSET(QUOTES_TIRED),
    [EMOTION_SAD]        = QSET(QUOTES_SAD),
    [EMOTION_ANGRY]      = QSET(QUOTES_ANGRY),
    [EMOTION_EXCITED]    = QSET(QUOTES_EXCITED),
    [EMOTION_CHILL]      = QSET(QUOTES_CHILL),
    [EMOTION_LAZY]       = QSET(QUOTES_LAZY),
    [EMOTION_FAT]        = QSET(QUOTES_FAT),
    [EMOTION_CHAOTIC]    = QSET(QUOTES_CHAOTIC),
    [EMOTION_WEIRD]      = QSET(QUOTES_WEIRD),
    [EMOTION_UNHINGED]   = QSET(QUOTES_UNHINGED),
    [EMOTION_SLAP_HAPPY] = QSET(QUOTES_SLAPHAPPY),
    [EMOTION_HORNY]      = QSET(QUOTES_HORNY),
    [EMOTION_NOSTALGIC]  = QSET(QUOTES_NOSTALGIC),
    [EMOTION_HOMESICK]   = QSET(QUOTES_HOMESICK),
};

/* ─── Simple PRNG for quote selection ────────────────────────────
 *
 * We need randomness to pick quotes, but we don't need cryptographic
 * quality. XorShift is a well-known family of pseudo-random number
 * generators that's fast and has good statistical properties for games.
 */

/*
 * quote_rng_state -- The RNG's internal state.
 *
 * Declared `static` so it persists across function calls (it's stored
 * in the data segment, not the stack) and is private to this file.
 * The value 12345 is the seed -- the starting point of the sequence.
 * Every call to quote_rand() mutates this state, producing a new number.
 */
static uint32_t quote_rng_state = 12345;

/*
 * quote_rand -- Generate the next pseudo-random uint32_t.
 *
 * Returns: a pseudo-random 32-bit unsigned integer.
 *
 * This implements the XorShift32 algorithm by George Marsaglia.
 * It works by applying three rounds of XOR-with-shifted-self:
 *
 *   state ^= state << 13;   -- XOR state with itself shifted left 13 bits
 *   state ^= state >> 17;   -- XOR with itself shifted right 17 bits
 *   state ^= state << 5;    -- XOR with itself shifted left 5 bits
 *
 * The `^=` operator means "XOR and assign" (like += but with XOR).
 * XOR (^) flips bits: 0^1=1, 1^1=0, 0^0=0, 1^0=1.
 * The `<<` and `>>` operators shift bits left/right by N positions.
 *
 * The specific shift amounts (13, 17, 5) were chosen by Marsaglia
 * to maximize the period (how many numbers before the sequence repeats).
 * This particular triple gives a full period of 2^32 - 1.
 */
static uint32_t quote_rand(void) {
    quote_rng_state ^= quote_rng_state << 13;  /* XOR with left-shifted copy */
    quote_rng_state ^= quote_rng_state >> 17;  /* XOR with right-shifted copy */
    quote_rng_state ^= quote_rng_state << 5;   /* XOR with left-shifted copy */
    return quote_rng_state;
}

/* ─── Implementation ─────────────────────────────────────────── */

/*
 * dialogue_init -- Initialize the dialogue state to defaults (nothing showing).
 *
 * Parameters:
 *   dlg -- pointer to the dialogue_state_t to initialize.
 *          The caller owns the memory.
 *
 * memset zeroes all fields: showing=false, pending=false, timers=0, etc.
 */
void dialogue_init(dialogue_state_t *dlg) {
    memset(dlg, 0, sizeof(*dlg));
}

/*
 * dialogue_get_quote -- Pick a random quote for the given emotion.
 *
 * Parameters:
 *   emotion -- which emotion to get a quote for
 *   stage   -- the creature's life stage (currently unused, reserved for
 *              future stage-specific quotes)
 *
 * Returns: a pointer to a string literal (const char *). The returned
 *          string lives in read-only memory and must NOT be freed or
 *          modified by the caller. It remains valid for the entire
 *          lifetime of the program.
 */
const char *dialogue_get_quote(emotion_id_t emotion, life_stage_t stage) {
    /* Bounds check: if emotion is out of range, fall back to NORMAL */
    if (emotion >= EMOTION_COUNT) emotion = EMOTION_NORMAL;

    /*
     * &QUOTE_SETS[emotion] takes the address of the quote_set_t entry
     * for this emotion. Using a local pointer `qs` avoids repeated
     * array indexing and makes the code more readable.
     */
    const quote_set_t *qs = &QUOTE_SETS[emotion];
    if (qs->count == 0) return "...";  /* safety fallback for empty quote sets */

    /*
     * quote_rand() % qs->count gives a number in [0, count-1].
     * The modulo (%) operator returns the remainder of integer division.
     * This is a common pattern for mapping a large random number into
     * a smaller range. (Note: this has slight bias for non-power-of-2
     * counts, but for small arrays it's perfectly fine.)
     */
    int idx = quote_rand() % qs->count;
    return qs->quotes[idx];  /* return pointer to the selected string literal */
}

/*
 * dialogue_force -- Display a specific text in the speech bubble for a duration.
 *
 * Parameters:
 *   dlg         -- mutable pointer to the dialogue state
 *   text        -- the string to display (will be copied into the state)
 *   duration_ms -- how long to show the text (0 = show indefinitely)
 *
 * Uses strncpy for safe string copying:
 *   strncpy(dest, src, n) copies at most n characters from src to dest.
 *   Unlike strcpy, it won't overflow the buffer if src is too long.
 *   However, strncpy does NOT guarantee null-termination if src is longer
 *   than n, so we manually set the last byte to '\0' on the next line.
 */
void dialogue_force(dialogue_state_t *dlg, const char *text, uint32_t duration_ms) {
    strncpy(dlg->current_text, text, DIALOGUE_MAX_LEN - 1);
    dlg->current_text[DIALOGUE_MAX_LEN - 1] = '\0';  /* ensure null-termination */
    dlg->showing = true;
    dlg->pending = true;
    dlg->show_start_ms = time_mgr_now_ms();
    dlg->show_duration_ms = duration_ms;
}

/*
 * dialogue_dismiss -- Immediately hide the speech bubble.
 *
 * Parameters:
 *   dlg -- mutable pointer to the dialogue state
 */
void dialogue_dismiss(dialogue_state_t *dlg) {
    dlg->showing = false;
    dlg->pending = false;
}

/*
 * dialogue_tick -- Per-tick update: auto-dismiss the speech bubble if its
 * display duration has elapsed.
 *
 * Parameters:
 *   dlg    -- mutable pointer to the dialogue state
 *   now_ms -- current time in milliseconds
 */
void dialogue_tick(dialogue_state_t *dlg, uint32_t now_ms) {
    if (!dlg->showing) return;  /* nothing to do if no bubble is showing */

    /*
     * Check if the display duration has elapsed.
     * show_duration_ms == 0 means "show indefinitely" (the > 0 check skips
     * the timeout logic in that case).
     *
     * now_ms - show_start_ms gives elapsed time. This subtraction works
     * correctly even if now_ms has wrapped around (unsigned arithmetic).
     */
    if (dlg->show_duration_ms > 0 &&
        now_ms - dlg->show_start_ms >= dlg->show_duration_ms) {
        dlg->showing = false;
        dlg->pending = false;
    }
}

/*
 * dialogue_check_triggers -- Check if the dialogue system should show a
 * new speech bubble (e.g., because the emotion just changed).
 *
 * Parameters:
 *   dlg     -- mutable pointer to the dialogue state
 *   emotion -- read-only pointer to the emotion state (to check if it changed)
 *   stats   -- read-only pointer to current stats (reserved for future use)
 *   gt      -- read-only pointer to game time (reserved for future use)
 */
void dialogue_check_triggers(dialogue_state_t *dlg,
                             const emotion_state_t *emotion,
                             const stats_t *stats,
                             const game_time_t *gt) {
    if (dlg->showing) return;  /* don't interrupt an active speech bubble */

    /* Show a quote when emotion changes */
    if (emotion->changed) {
        /*
         * LIFE_STAGE_ADULT is passed as a placeholder here -- the stage
         * parameter is reserved for future stage-specific quote filtering
         * but is not yet used by dialogue_get_quote.
         */
        const char *quote = dialogue_get_quote(emotion->current, LIFE_STAGE_ADULT);
        dialogue_force(dlg, quote, 15000);  /* 15 seconds display time */
    }
}
