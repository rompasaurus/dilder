/*
 * event.c -- Lightweight publish/subscribe event system
 *
 * This module implements two things:
 *   1. An observer pattern: other modules register callback functions
 *      ("listeners") for specific event types, and when that event fires,
 *      all registered callbacks are invoked.
 *   2. A ring buffer that keeps a short history of the most recent events
 *      so other code can ask "did event X happen in the last N ms?"
 *
 * Memory model:
 *   All state lives in file-scope static arrays -- no heap (malloc) is used.
 *   The `listeners` 2D array and the `ring` buffer both live in the BSS
 *   segment (zero-initialized global memory) because they are static and
 *   have no initializer with non-zero data at compile time.
 *
 * Key C concepts used:
 *   - Function pointers (event_handler_t is a pointer to a function)
 *   - Compound literals to build a struct on the stack in one expression
 *   - Ring buffer with modulo arithmetic for constant-size history
 *   - const pointer return to give read-only access to internal data
 */

#include "game/event.h"
#include "game/time_mgr.h"

/* ─── State ──────────────────────────────────────────────────── */

/*
 * listeners -- 2D array of function pointers.
 *
 * Indexed as listeners[event_type][slot_index].
 * Each event type gets up to MAX_LISTENERS_PER_EVENT callback slots.
 *
 * `event_handler_t` is a typedef for:
 *     void (*)(event_type_t type, const event_data_t *data)
 * In other words, each element is a pointer to a function that takes an
 * event type and a pointer to event data, and returns nothing.
 *
 * "static" at file scope means these are only visible within this .c file
 * (internal linkage). This is C's version of making something "private"
 * to a module.
 */
static event_handler_t listeners[EVENT_TYPE_COUNT][MAX_LISTENERS_PER_EVENT];

/*
 * ring / ring_head -- A fixed-size circular (ring) buffer for event history.
 *
 * `ring` stores the last EVENT_RING_SIZE events (16 by default).
 * `ring_head` is the index where the *next* event will be written.
 * When ring_head reaches the end, it wraps around to 0 via modulo (%).
 *
 * This means old events get overwritten once the buffer is full -- we
 * never allocate more memory, we just recycle the oldest slot.
 */
static event_record_t  ring[EVENT_RING_SIZE];
static uint8_t         ring_head = 0;

/*
 * event_init -- Reset the entire event system to a clean state.
 *
 * Parameters: none
 * Returns:    nothing
 *
 * Called once at startup (from game_loop_init) to ensure all listener
 * slots are NULL and the ring buffer is empty.
 *
 * memset(ptr, 0, size) fills `size` bytes starting at `ptr` with zero.
 * For pointers, all-zero-bits is NULL on every platform we target.
 * For structs, this zeroes every field (timestamps become 0, types
 * become the first enum value, etc.).
 */
void event_init(void) {
    memset(listeners, 0, sizeof(listeners));
    memset(ring, 0, sizeof(ring));
    ring_head = 0;
}

/*
 * event_listen -- Register a callback for a specific event type.
 *
 * Parameters:
 *   type    -- Which event to listen for (e.g. EVENT_FED, EVENT_PETTED).
 *   handler -- A function pointer: the function to call when this event fires.
 *
 * Returns: nothing
 *
 * The function scans the listener slots for the given event type and
 * places the handler in the first empty (NULL) slot. If all slots are
 * full, the registration is silently dropped.
 *
 * Why the guard "type >= EVENT_TYPE_COUNT"?
 *   Enum values in C are just integers. If someone passes a garbage value,
 *   we'd index out of bounds on the array. This check prevents that.
 *
 * Why "!handler"?
 *   We don't want to store a NULL function pointer -- calling NULL would
 *   crash. The `!` operator on a pointer is true when the pointer is NULL.
 */
void event_listen(event_type_t type, event_handler_t handler) {
    if (type >= EVENT_TYPE_COUNT || !handler) return;  /* bounds + null check */

    for (int i = 0; i < MAX_LISTENERS_PER_EVENT; i++) {
        if (listeners[type][i] == NULL) {   /* found an empty slot */
            listeners[type][i] = handler;
            return;                         /* done -- only register once */
        }
    }
    /* All slots full — drop silently */
}

/*
 * event_fire -- Emit an event: log it to the ring buffer, then notify listeners.
 *
 * Parameters:
 *   type -- The event type being fired.
 *   data -- Optional pointer to extra data about the event (can be NULL).
 *
 * Returns: nothing
 *
 * This is the "publish" side of the pub/sub pattern.
 *
 * Step 1: Record the event in the ring buffer so other code can query
 *         recent history later with event_recent().
 * Step 2: Walk through all listener slots for this event type and call
 *         each non-NULL function pointer.
 */
void event_fire(event_type_t type, const event_data_t *data) {
    if (type >= EVENT_TYPE_COUNT) return;  /* bounds check */

    uint32_t now = time_mgr_now_ms();

    /* Log to ring buffer.
     *
     * The right-hand side is a "compound literal":
     *   (event_record_t){ .type = ..., .value = ..., .timestamp = ... }
     * This creates a temporary event_record_t value on the stack with
     * the specified fields, then assigns (copies) it into ring[ring_head].
     *
     * The ternary `data ? data->value : 0` safely handles a NULL data
     * pointer: if data is non-NULL, use its value field; otherwise use 0.
     */
    ring[ring_head] = (event_record_t){
        .type      = type,
        .value     = data ? data->value : 0,  /* ternary: NULL-safe access */
        .timestamp = now,
    };

    /*
     * Advance the ring head and wrap around using modulo.
     * If ring_head is 15 and EVENT_RING_SIZE is 16:
     *   (15 + 1) % 16 = 0  --> wraps back to the start.
     * This is the standard trick for circular/ring buffers.
     */
    ring_head = (ring_head + 1) % EVENT_RING_SIZE;

    /* Dispatch to listeners.
     *
     * listeners[type][i] is a function pointer. If it's not NULL,
     * we call it by writing: listeners[type][i](type, data)
     * This is identical to: (*listeners[type][i])(type, data)
     * C allows calling function pointers with the same syntax as functions.
     */
    for (int i = 0; i < MAX_LISTENERS_PER_EVENT; i++) {
        if (listeners[type][i]) {           /* non-NULL means registered */
            listeners[type][i](type, data); /* call the handler function */
        }
    }
}

/*
 * event_recent -- Check if a specific event type occurred within a time window.
 *
 * Parameters:
 *   type      -- The event type to look for.
 *   within_ms -- How far back to look (in milliseconds).
 *
 * Returns:
 *   true  if an event of `type` exists in the ring buffer with a timestamp
 *         no older than `within_ms` from now.
 *   false otherwise.
 *
 * This performs a linear scan of the entire ring buffer (all 16 slots).
 * We check timestamp > 0 to skip empty/zeroed slots that were never written.
 *
 * The subtraction `now - ring[i].timestamp` works correctly even without
 * overflow handling here because our timestamps come from a monotonic
 * millisecond counter that won't wrap during normal gameplay sessions.
 */
bool event_recent(event_type_t type, uint32_t within_ms) {
    uint32_t now = time_mgr_now_ms();

    for (int i = 0; i < EVENT_RING_SIZE; i++) {
        if (ring[i].type == type && ring[i].timestamp > 0) {
            if (now - ring[i].timestamp <= within_ms) {
                return true;
            }
        }
    }
    return false;
}

/*
 * event_count_recent -- Count how many events (of any type) occurred recently.
 *
 * Parameters:
 *   within_ms -- Time window in milliseconds.
 *
 * Returns:
 *   The number of ring buffer entries whose timestamp falls within
 *   the last `within_ms` milliseconds.
 *
 * Useful for detecting bursts of activity (e.g. "has the player been
 * interacting a lot in the last 30 seconds?").
 */
int event_count_recent(uint32_t within_ms) {
    uint32_t now = time_mgr_now_ms();
    int count = 0;

    for (int i = 0; i < EVENT_RING_SIZE; i++) {
        if (ring[i].timestamp > 0 && now - ring[i].timestamp <= within_ms) {
            count++;
        }
    }
    return count;
}

/*
 * event_get_ring -- Get a read-only pointer to the ring buffer array.
 *
 * Parameters: none
 * Returns:    const pointer to the first element of the ring[] array.
 *
 * The `const` in the return type means the caller cannot modify the
 * ring buffer through this pointer -- it's read-only access.
 * This lets external code (like a debug UI) inspect event history
 * without being able to corrupt it.
 *
 * Note: this returns a pointer to the static array itself, NOT a copy.
 * No memory is allocated. The pointer is valid as long as the program runs.
 */
const event_record_t *event_get_ring(void) {
    return ring;
}

/*
 * event_get_ring_head -- Get the current write position in the ring buffer.
 *
 * Parameters: none
 * Returns:    The index where the next event will be written.
 *
 * Combined with event_get_ring(), this lets external code iterate
 * the ring buffer in chronological order: start at ring_head (oldest)
 * and wrap around.
 */
uint8_t event_get_ring_head(void) {
    return ring_head;
}
