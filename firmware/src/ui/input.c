/*
 * input.c -- Button Input Queue (Circular / Ring Buffer)
 *
 * PURPOSE:
 *   This module queues button press events so they can be processed later
 *   by the UI state machine. Button presses can arrive at any time (from
 *   an interrupt on real hardware, or from SDL key events in the emulator),
 *   but the game loop processes them once per frame. The queue decouples
 *   "when a press happens" from "when the game handles it."
 *
 * DATA STRUCTURE -- CIRCULAR BUFFER (RING BUFFER):
 *   A circular buffer is a fixed-size array that wraps around. It uses
 *   two indices:
 *
 *     head -- points to the OLDEST item (the next one to be read/consumed)
 *     tail -- points to the NEXT EMPTY SLOT (where new items get written)
 *
 *   When head == tail and count == 0, the buffer is empty.
 *   When count == INPUT_QUEUE_SIZE, the buffer is full.
 *
 *   The "circular" part comes from the modulo trick:
 *     queue_tail = (queue_tail + 1) % INPUT_QUEUE_SIZE;
 *   When tail reaches the end of the array (index 7), adding 1 gives 8,
 *   and 8 % 8 = 0 -- so it wraps back to the beginning. This means we
 *   never need to shift elements like you would with a regular array-based
 *   queue, making both push and poll O(1) operations.
 *
 *   Visual example with size 4:
 *
 *     After pushing A, B, C:
 *       [A] [B] [C] [ ]
 *        ^head        ^tail    count=3
 *
 *     After polling (removes A):
 *       [ ] [B] [C] [ ]
 *            ^head    ^tail    count=2
 *
 *     After pushing D, E (wraps!):
 *       [E] [B] [C] [D]
 *            ^head
 *        ^tail                 count=4 (full!)
 *
 * MEMORY MODEL:
 *   All variables are `static` at file scope, meaning:
 *     - They persist for the program's entire lifetime (not stack-allocated)
 *     - They are private to this file (encapsulation)
 *   The queue array holds 8 button_event_t structs on the data segment
 *   (not the heap -- no malloc/free needed). This is ideal for embedded
 *   systems where dynamic memory allocation is avoided.
 */

#include "ui/input.h"
#include "game/time_mgr.h"

/* ─── Input Queue ────────────────────────────────────────────── */

/*
 * INPUT_QUEUE_SIZE defines how many button events we can buffer before
 * new ones get dropped. 8 is plenty -- the game processes input every
 * frame (~16ms), and humans can't press buttons faster than that.
 */
#define INPUT_QUEUE_SIZE 8

/*
 * The queue itself: a fixed-size array of button_event_t structs.
 * Each event records which button was pressed, how it was pressed
 * (short/long/double), and when.
 *
 * queue_head: index of the next event to READ (oldest unprocessed event)
 * queue_tail: index of the next EMPTY SLOT to write into
 * queue_count: how many events are currently in the buffer
 *
 * All three are uint8_t (unsigned 8-bit, 0-255) which is more than
 * enough for a queue of size 8. Using the smallest type that fits
 * saves memory -- important on microcontrollers with limited RAM.
 */
static button_event_t queue[INPUT_QUEUE_SIZE];
static uint8_t queue_head = 0;
static uint8_t queue_tail = 0;
static uint8_t queue_count = 0;

/*
 * input_init -- Reset the input queue to empty.
 *
 * Parameters: none
 * Returns:    nothing
 *
 * Called once at startup. Sets all indices to 0. We don't need to
 * zero the queue array itself because we only read entries between
 * head and tail, and those will be overwritten before being read.
 */
void input_init(void) {
    queue_head = 0;
    queue_tail = 0;
    queue_count = 0;
}

/*
 * input_push -- Add a new button event to the back of the queue.
 *
 * Parameters:
 *   id   -- which button was pressed (BTN_UP, BTN_SELECT, etc.)
 *   type -- how it was pressed (PRESS_SHORT, PRESS_LONG, PRESS_DOUBLE)
 *
 * Returns: nothing
 *
 * If the queue is full (8 events buffered), the new event is silently
 * dropped. This is a design choice: we'd rather lose an input than
 * corrupt memory by writing past the array bounds.
 *
 * The compound literal syntax:
 *   (button_event_t){ .id = id, .type = type, .timestamp = ... }
 * creates a temporary struct value with named field initialization
 * (a C99 feature called "designated initializers"). This is cleaner
 * than setting each field on a separate line.
 */
void input_push(button_id_t id, press_type_t type) {
    if (queue_count >= INPUT_QUEUE_SIZE) return;  /* drop if full */

    /* Write the new event at the tail position using a compound literal.
     * .id, .type, .timestamp are "designated initializers" -- they let you
     * name which fields you're setting, making the code self-documenting. */
    queue[queue_tail] = (button_event_t){
        .id = id,
        .type = type,
        .timestamp = time_mgr_now_ms(),
    };

    /* Advance tail with wraparound. The modulo (%) operator makes the
     * index wrap from INPUT_QUEUE_SIZE-1 back to 0, creating the
     * "circular" behavior. Example: (7 + 1) % 8 = 0. */
    queue_tail = (queue_tail + 1) % INPUT_QUEUE_SIZE;
    queue_count++;
}

/*
 * input_poll -- Remove and return the oldest event from the queue.
 *
 * Parameters: none
 *
 * Returns:
 *   button_event_t -- the oldest queued event. If the queue is empty,
 *   returns a "null event" with BTN_NONE and PRESS_NONE, which callers
 *   check to know there was nothing to process.
 *
 * This is the "consumer" side of the producer-consumer pattern.
 * input_push is the producer (called when buttons are pressed),
 * input_poll is the consumer (called by the game loop each frame).
 *
 * Note: the struct is returned BY VALUE (copied), not by pointer.
 * This is safe because button_event_t is small (8 bytes). Returning
 * a pointer to queue[queue_head] would be dangerous because the slot
 * could be overwritten by a future push.
 */
button_event_t input_poll(void) {
    /* If empty, return a sentinel value that callers can check */
    if (queue_count == 0) {
        return (button_event_t){ .id = BTN_NONE, .type = PRESS_NONE };
    }

    /* Read the oldest event from the head position */
    button_event_t evt = queue[queue_head];

    /* Advance head with the same modulo wraparound as push uses for tail */
    queue_head = (queue_head + 1) % INPUT_QUEUE_SIZE;
    queue_count--;
    return evt;
}

/*
 * input_has_event -- Check whether there are any queued events.
 *
 * Parameters: none
 *
 * Returns:
 *   true if at least one event is waiting, false if the queue is empty.
 *
 * This lets callers peek without consuming an event. Useful for
 * "should I bother calling input_poll?" checks.
 */
bool input_has_event(void) {
    return queue_count > 0;
}
