/*
 * ui.c -- UI Controller: State Machine + Input Dispatch + Render Dispatch
 *
 * PURPOSE:
 *   This is the central UI controller for the Dilder virtual pet. It ties
 *   together three concerns:
 *     1. SCREEN STATE -- which screen is currently displayed (pet, menu, stats)
 *     2. INPUT ROUTING -- how button presses are interpreted depends on what
 *        screen/state the game is in (this is the "state machine" pattern)
 *     3. RENDER DISPATCH -- calling the right renderer for the current screen
 *
 * STATE MACHINE PATTERN:
 *   A state machine is a programming pattern where the same input (e.g., a
 *   button press) does DIFFERENT things depending on what "state" the system
 *   is in. Think of it like modes on a calculator: pressing "5" types a digit
 *   in normal mode but selects a memory slot in memory mode.
 *
 *   In this code, the game has these main states (defined in game_state_t):
 *     - GAME_STATE_ACTIVE:   pet view, buttons interact with the pet
 *     - GAME_STATE_MENU:     menu is open, buttons navigate menu items
 *     - GAME_STATE_SLEEPING: pet is asleep, any button wakes it up
 *
 *   The ui_handle_input() function acts as a DISPATCHER: it checks the current
 *   state and routes the button event to the appropriate handler function.
 *   Each handler only knows about its own state's behavior.
 *
 * DIRTY FLAG PATTERN:
 *   Instead of redrawing the screen every frame (wasteful for an e-ink or
 *   low-power display), we use a "dirty flag." When something changes
 *   (a button press, a stat update), we set ui.dirty = true. The render
 *   function checks this flag and only redraws when needed. After rendering,
 *   the flag is cleared back to false.
 *
 * GLOBAL STATE:
 *   This module accesses g_game (the global game struct) directly. In a
 *   larger codebase you might pass it as a parameter, but for a small
 *   embedded project, a single global is simpler and avoids passing the
 *   same pointer through every function call.
 */

#include "ui/ui.h"
#include "ui/render.h"
#include "ui/input.h"
#include "game/game_loop.h"
#include "game/stat.h"
#include "game/emotion.h"
#include "game/dialog.h"
#include "game/life.h"
#include "game/event.h"
#include "game/time_mgr.h"

/* ─── Implementation ─────────────────────────────────────────── */

/*
 * ui_init -- Initialize the UI state to its default values.
 *
 * Parameters:
 *   ui  -- pointer to the ui_state_t struct to initialize.
 *          Using a pointer lets us modify the caller's struct directly.
 *          Without a pointer, C would copy the struct and our changes
 *          would be lost when the function returns.
 *
 * Returns: nothing
 *
 * Sets the initial screen to the pet view, marks the display as dirty
 * (needs drawing), and zeroes the refresh timer.
 */
void ui_init(ui_state_t *ui) {
    ui->current_screen = SCREEN_PET;   /* start on the main pet screen */
    ui->dirty = true;                  /* force an initial draw */
    ui->last_refresh_ms = 0;
}

/*
 * ui_mark_dirty -- Signal that the screen needs to be redrawn.
 *
 * Parameters: none
 * Returns:    nothing
 *
 * Called from many places (input handlers, stat changes, dialogue events)
 * whenever something visible on screen has changed. This is the "setter"
 * side of the dirty flag pattern.
 *
 * Accesses g_game directly -- the global game instance defined in
 * game_state.h. The dot-and-arrow chain g_game.ui.dirty means:
 * "the `ui` field of the global game struct, then its `dirty` field."
 */
void ui_mark_dirty(void) {
    g_game.ui.dirty = true;
}

/*
 * ui_needs_redraw -- Check whether the screen needs to be redrawn.
 *
 * Parameters: none
 *
 * Returns:
 *   true if ui_mark_dirty() was called since the last render, false otherwise.
 *
 * This is the "getter" side of the dirty flag pattern. The main loop
 * can use this to decide whether to call ui_render().
 */
bool ui_needs_redraw(void) {
    return g_game.ui.dirty;
}

/* ─── Input Dispatch ─────────────────────────────────────────── */

/*
 * context_action_resolve -- Decide what the "context action" button should do.
 *
 * Parameters:
 *   stats  -- pointer to the current stats (const = read-only, won't modify)
 *
 * Returns:
 *   A care_action_t value representing the most appropriate action right now.
 *
 * This implements a "smart" context button: instead of always doing the
 * same thing, it looks at the pet's stats and picks the most urgent need.
 * If hunger is below 30, feed. If hygiene is below 30, clean. Otherwise
 * default to petting.
 *
 * The `static` keyword on a function (as opposed to a variable) means
 * the function is only visible within this file. It's like a "private
 * method" -- other .c files can't call it. This is good for helper
 * functions that are implementation details.
 */
static care_action_t context_action_resolve(const stats_t *stats) {
    if (stats->primary.hunger < 30) return CARE_FEED_MEAL;
    if (stats->primary.hygiene < 30) return CARE_CLEAN;
    if (stats->primary.happiness < 30) return CARE_PET;
    return CARE_PET;  /* default: pet */
}

/* ─── Menu Action Mapping ────────────────────────────────────── */

/*
 * menu_action_for_cursor -- Map a menu + cursor position to a care action.
 *
 * Parameters:
 *   menu   -- which submenu is currently displayed (MENU_FEED, MENU_PLAY, etc.)
 *   cursor -- which item in the menu is highlighted (0-based index)
 *
 * Returns:
 *   The care_action_t that corresponds to the selected menu item.
 *   Falls back to CARE_PET if the combination is unrecognized.
 *
 * This is a lookup table implemented with nested switch statements.
 * The outer switch selects the menu, the inner switch selects the item
 * within that menu.
 */
static care_action_t menu_action_for_cursor(menu_id_t menu, uint8_t cursor) {
    switch (menu) {
    case MENU_FEED:
        switch (cursor) {
        case 0: return CARE_FEED_MEAL;    /* "Meal" */
        case 1: return CARE_FEED_SNACK;   /* "Snack" */
        case 2: return CARE_FEED_TREAT;   /* "Treat" */
        }
        break;
    case MENU_PLAY:
        switch (cursor) {
        case 0: return CARE_PLAY;         /* "Mini-game" */
        case 1: return CARE_TICKLE;       /* "Tickle" */
        }
        break;
    case MENU_CARE:
        switch (cursor) {
        case 0: return CARE_CLEAN;        /* "Clean" */
        case 1: return CARE_MEDICINE;     /* "Medicine" */
        case 2: return CARE_SLEEP_TOGGLE; /* "Light" (sleep toggle) */
        }
        break;
    default:
        break;
    }
    return CARE_PET;  /* fallback if menu/cursor combo is unrecognized */
}

/*
 * menu_item_count -- Return how many items a given menu contains.
 *
 * Parameters:
 *   menu  -- the menu to query
 *
 * Returns:
 *   The number of selectable items in that menu.
 *   Returns 0 for menus that don't have navigable items (like STATS).
 */
static int menu_item_count(menu_id_t menu) {
    switch (menu) {
    case MENU_MAIN: return 5;   /* Feed, Play, Care, Stats, Settings */
    case MENU_FEED: return 3;   /* Meal, Snack, Treat */
    case MENU_PLAY: return 2;   /* Mini-game, Tickle */
    case MENU_CARE: return 3;   /* Clean, Medicine, Light */
    case MENU_STATS: return 0;  /* stats screen has no menu items */
    default: return 0;
    }
}

/*
 * main_menu_submenu -- Map a cursor position on the main menu to a submenu ID.
 *
 * Parameters:
 *   cursor  -- which main menu item is highlighted (0-4)
 *
 * Returns:
 *   The menu_id_t of the submenu to open, or MENU_NONE if invalid.
 */
static menu_id_t main_menu_submenu(uint8_t cursor) {
    switch (cursor) {
    case 0: return MENU_FEED;
    case 1: return MENU_PLAY;
    case 2: return MENU_CARE;
    case 3: return MENU_STATS;
    case 4: return MENU_SETTINGS;
    default: return MENU_NONE;
    }
}

/* ─── Active State Input ─────────────────────────────────────── */

/*
 * handle_active_input -- Process button presses when the game is in
 *                        GAME_STATE_ACTIVE (the normal pet-viewing state).
 *
 * Parameters:
 *   btn  -- the button event to handle (passed by value = copied onto stack)
 *
 * Returns: nothing
 *
 * In active state:
 *   - SELECT long-press: opens the main menu
 *   - SELECT short-press: dismisses any dialogue bubble
 *   - ACTION short-press: performs a context-sensitive care action
 *   - ACTION long-press: scolds the pet (resolves misbehavior if active)
 *
 * This is one "state handler" in the state machine. It only handles
 * the ACTIVE state's behavior. The state machine dispatcher
 * (ui_handle_input) decides which handler to call.
 */
static void handle_active_input(button_event_t btn) {
    switch (btn.id) {
    case BTN_SELECT:
        if (btn.type == PRESS_LONG) {
            /* Long press SELECT = open menu. This transitions the game
             * from ACTIVE state to MENU state. */
            menu_open(MENU_MAIN);
            game_state_transition(GAME_STATE_MENU);
        } else if (btn.type == PRESS_SHORT) {
            /* Short press SELECT = dismiss dialogue if one is showing. */
            if (g_game.dialogue.showing) {
                dialogue_dismiss(&g_game.dialogue);
                ui_mark_dirty();
            }
        }
        break;

    case BTN_ACTION:
        if (btn.type == PRESS_SHORT) {
            /* Short press ACTION = smart context action.
             * context_action_resolve() picks the most urgent need. */
            care_action_t action = context_action_resolve(&g_game.stats);
            stat_apply_care(&g_game.stats, &g_game.care_cd, action, false);
            ui_mark_dirty();
        } else if (btn.type == PRESS_LONG) {
            /* Long press ACTION = scold the pet.
             * The second parameter to stat_apply_care indicates whether
             * the scold was "justified" (the pet was misbehaving).
             * If so, also resolve the misbehavior event. */
            stat_apply_care(&g_game.stats, &g_game.care_cd,
                            CARE_SCOLD, g_game.life.misbehaving);
            if (g_game.life.misbehaving) {
                misbehavior_resolve(&g_game.life, &g_game.stats, true);
            }
            ui_mark_dirty();
        }
        break;

    default:
        break;  /* UP, DOWN, BACK do nothing in active state */
    }
}

/* ─── Menu State Input ───────────────────────────────────────── */

/*
 * handle_menu_input -- Process button presses when a menu is open.
 *
 * Parameters:
 *   btn  -- the button event to handle
 *
 * Returns: nothing
 *
 * In menu state:
 *   - UP/DOWN: move the cursor within the current menu
 *   - SELECT: activate the highlighted item (open submenu or perform action)
 *   - BACK: go back to parent menu, or close menu entirely
 *
 * MENU STACK:
 *   The menu system supports nested submenus using a stack (array + depth
 *   counter). When you enter a submenu, the current menu is pushed onto
 *   the stack. When you press BACK, the previous menu is popped off.
 *
 *   m->stack[m->stack_depth++] = m->current_menu;
 *   This line does three things:
 *     1. Stores current_menu at stack[stack_depth]
 *     2. Increments stack_depth (the ++ is post-increment, so the old
 *        value is used as the index, then it increases by 1)
 *     3. Now current_menu can be changed to the submenu
 *
 *   m->current_menu = m->stack[--m->stack_depth];
 *   This pops by doing the reverse:
 *     1. Decrements stack_depth first (pre-increment --)
 *     2. Reads the menu stored at that position
 *     3. Restores it as the current menu
 */
static void handle_menu_input(button_event_t btn) {
    menu_state_t *m = &g_game.menu;  /* pointer to menu state, for brevity */
    int count = menu_item_count(m->current_menu);

    switch (btn.id) {
    case BTN_UP:
        /* Move cursor up, but don't go below 0 */
        if (m->cursor > 0) m->cursor--;
        ui_mark_dirty();
        break;

    case BTN_DOWN:
        /* Move cursor down, but don't exceed the menu's item count */
        if (m->cursor < count - 1) m->cursor++;
        ui_mark_dirty();
        break;

    case BTN_SELECT:
        if (m->current_menu == MENU_MAIN) {
            /* On the main menu, SELECT opens a submenu */
            menu_id_t sub = main_menu_submenu(m->cursor);
            if (sub == MENU_STATS) {
                /* Stats is a full-screen view, not a submenu */
                g_game.ui.current_screen = SCREEN_STATS;
                ui_mark_dirty();
                return;  /* early return -- don't fall through to mark dirty again */
            }
            if (sub != MENU_NONE && sub != MENU_SETTINGS) {
                /* Push current menu onto the stack before descending.
                 * stack_depth++ is post-increment: use current value as index,
                 * THEN increase the depth counter by 1. */
                m->stack[m->stack_depth++] = m->current_menu;
                m->current_menu = sub;
                m->cursor = 0;   /* reset cursor for the new submenu */
            }
        } else {
            /* In a submenu, SELECT executes the action (leaf node).
             * Then close the menu and return to the active pet view. */
            care_action_t action = menu_action_for_cursor(m->current_menu, m->cursor);
            stat_apply_care(&g_game.stats, &g_game.care_cd, action, false);
            menu_close();
            game_state_transition(GAME_STATE_ACTIVE);
        }
        ui_mark_dirty();
        break;

    case BTN_BACK:
        if (m->stack_depth > 0) {
            /* Pop the parent menu off the stack.
             * --m->stack_depth is pre-decrement: decrease the depth FIRST,
             * then use the new value as the array index. */
            m->current_menu = m->stack[--m->stack_depth];
            m->cursor = 0;  /* reset cursor when going back */
        } else {
            /* Already at top level -- close the entire menu system */
            menu_close();
            game_state_transition(GAME_STATE_ACTIVE);
        }
        ui_mark_dirty();
        break;

    default:
        break;
    }
}

/* ─── Top-Level Input Handler ────────────────────────────────── */

/*
 * ui_handle_input -- The STATE MACHINE DISPATCHER.
 *
 * Parameters:
 *   btn  -- a button event from the input queue
 *
 * Returns: nothing
 *
 * This is the heart of the state machine pattern. It examines the
 * current game state (g_game.state) and routes the button event to
 * the appropriate handler. The same physical button press results in
 * completely different behavior depending on the current state:
 *
 *   ACTIVE state   -> handle_active_input (interact with pet)
 *   MENU state     -> handle_menu_input (navigate menus)
 *   SLEEPING state -> any button wakes the pet
 *   Other states   -> BACK or SELECT returns to pet view
 *
 * The early return for BTN_NONE/PRESS_NONE filters out the "empty"
 * sentinel events that input_poll() returns when the queue is empty.
 */
void ui_handle_input(button_event_t btn) {
    /* Ignore "no event" sentinels from the input queue */
    if (btn.id == BTN_NONE || btn.type == PRESS_NONE) return;

    switch (g_game.state) {
    case GAME_STATE_ACTIVE:
        handle_active_input(btn);
        break;
    case GAME_STATE_MENU:
        handle_menu_input(btn);
        break;
    case GAME_STATE_SLEEPING:
        /* Any button wakes the pet -- no need to check which button.
         * Transition back to ACTIVE and fire a wake-up event. */
        game_state_transition(GAME_STATE_ACTIVE);
        event_fire(EVENT_WAKE_UP, NULL);
        ui_mark_dirty();
        break;
    default:
        /* For stats screen or other non-primary states:
         * BACK or SELECT returns to the main pet view. */
        if (btn.id == BTN_BACK || btn.id == BTN_SELECT) {
            g_game.ui.current_screen = SCREEN_PET;
            game_state_transition(GAME_STATE_ACTIVE);
            ui_mark_dirty();
        }
        break;
    }
}

/* ─── Menu Operations ────────────────────────────────────────── */

/*
 * menu_open -- Open a menu and switch to the menu screen.
 *
 * Parameters:
 *   menu  -- which menu to open (typically MENU_MAIN)
 *
 * Returns: nothing
 *
 * Resets the cursor and stack so we start fresh. The menu is displayed
 * as an overlay on the right half of the pet screen.
 */
void menu_open(menu_id_t menu) {
    g_game.menu.current_menu = menu;
    g_game.menu.cursor = 0;          /* highlight the first item */
    g_game.menu.stack_depth = 0;     /* clear the submenu history stack */
    g_game.ui.current_screen = SCREEN_MENU;
}

/*
 * menu_close -- Close the menu and return to the pet screen.
 *
 * Parameters: none
 * Returns:    nothing
 *
 * Resets all menu state back to "no menu." The pet screen will be
 * rendered on the next frame.
 */
void menu_close(void) {
    g_game.menu.current_menu = MENU_NONE;
    g_game.menu.cursor = 0;
    g_game.menu.stack_depth = 0;
    g_game.ui.current_screen = SCREEN_PET;
}

/* ─── Render Dispatch ────────────────────────────────────────── */

/*
 * ui_render -- Render the current screen to the framebuffer.
 *
 * Parameters: none
 * Returns:    nothing
 *
 * This function implements the "render side" of the dirty flag pattern:
 *   1. Check if the screen is dirty (something changed). If not, skip.
 *   2. Clear the framebuffer to all-black.
 *   3. Draw the appropriate screen based on current_screen.
 *   4. Clear the dirty flag and record the refresh timestamp.
 *
 * For the MENU screen, note that we draw the pet screen FIRST, then
 * draw the menu on TOP as an overlay. This gives the "menu slides in
 * over the pet" look.
 *
 * fb_clear() fills the entire framebuffer with zeros (all pixels off).
 * The render_*() functions then set individual pixels to draw content.
 * After this function returns, the framebuffer is ready to be sent to
 * the display hardware (or drawn to the SDL window in the emulator).
 */
void ui_render(void) {
    if (!g_game.ui.dirty) return;  /* nothing changed, skip rendering */

    fb_clear();  /* wipe the framebuffer to start fresh */

    /* Draw the screen appropriate for the current UI state */
    switch (g_game.ui.current_screen) {
    case SCREEN_PET:
        render_pet_screen(&g_game);
        break;
    case SCREEN_MENU:
        render_pet_screen(&g_game);             /* draw pet in background */
        render_menu_overlay(&g_game.menu, &g_game); /* draw menu on top */
        break;
    case SCREEN_STATS:
        render_stats_screen(&g_game);
        break;
    default:
        render_pet_screen(&g_game);  /* fallback to pet view */
        break;
    }

    g_game.ui.dirty = false;                    /* clear the dirty flag */
    g_game.ui.last_refresh_ms = time_mgr_now_ms(); /* record when we drew */
}
