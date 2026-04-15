/*
 * Dilder Firmware -- Standalone Desktop CLI  (main_desktop.c)
 *
 * PURPOSE:
 *   This is a standalone test runner that does NOT need the Python DevTool.
 *   It runs the game engine in your terminal and prints the framebuffer as
 *   ASCII art after every tick, along with all the game stats.
 *
 *   This is useful for quick smoke-testing: just compile and run the
 *   binary directly, no Python required.
 *
 * USAGE:
 *   ./dilder_cli [ticks]
 *     ticks: number of game ticks to simulate (default: 30)
 *
 * HOW IT WORKS:
 *   1. Initializes the game engine via dilder_init().
 *   2. Loops for the requested number of ticks.
 *   3. Each iteration: calls dilder_tick(), renders the framebuffer as
 *      ASCII art in the terminal, and prints all game stats.
 *   4. Waits for the user to press Enter before advancing to the next tick
 *      (so you can inspect each frame at your own pace).
 */

#include <stdio.h>     /* printf, getchar */
#include <stdlib.h>    /* atoi (string-to-integer conversion) */
#include <string.h>    /* not used directly here, but included by convention */
#include "dilder.h"           /* public API functions (dilder_init, dilder_tick, etc.) */
#include "game/game_state.h"  /* SCREEN_ROW_BYTES and other display constants */
#include "ui/render.h"        /* (included for any render-related declarations) */

/*
 * print_framebuffer -- render the 1bpp display memory as ASCII art.
 *
 * The framebuffer is a flat array of bytes representing a 250x122
 * monochrome image.  Each bit is one pixel (1 = black, 0 = white).
 * This function reads those bits and prints '#' for black pixels and
 * ' ' (space) for white pixels, creating a text-based visualization
 * of the display.
 *
 * "static" means this function is only visible inside this .c file.
 * It's a helper, not part of the public API.
 */
static void print_framebuffer(void) {
    /*
     * dilder_get_framebuffer() returns a `const uint8_t *` -- a pointer
     * to the raw display bytes.  We store it in a local pointer variable
     * so we can index into it below.
     */
    const uint8_t *fb = dilder_get_framebuffer();

    /*
     * ANSI escape codes for terminal control:
     *   \033  = the ESC character (octal 033, hex 1B)
     *   [2J   = "erase entire screen"
     *   [H    = "move cursor to row 1, column 1 (home position)"
     *
     * Together, "\033[2J\033[H" clears the terminal and moves the cursor
     * to the top-left corner, so each frame draws over the previous one
     * instead of scrolling down endlessly.
     */
    printf("\033[2J\033[H");  /* clear terminal and move cursor to home */

    /* Print the top border of the ASCII art frame */
    printf("+");
    for (int x = 0; x < DILDER_SCREEN_W; x += 2) printf("-");
    printf("+\n");

    /*
     * Iterate over every row (y) and column (x) of the display.
     *
     * We step x by 2 (x += 2) to halve the horizontal resolution,
     * because terminal characters are roughly twice as tall as they
     * are wide.  Without this, the image would look stretched
     * horizontally.
     */
    for (int y = 0; y < DILDER_SCREEN_H; y++) {
        printf("|");  /* left border */
        for (int x = 0; x < DILDER_SCREEN_W; x += 2) {
            /*
             * Convert (x, y) pixel coordinates to a bit position in the
             * framebuffer array:
             *
             * byte_idx: which byte in the array contains this pixel?
             *   - Each row is SCREEN_ROW_BYTES (32) bytes long.
             *   - Within a row, byte position is x / 8 (8 pixels per byte).
             *   - Total: y * SCREEN_ROW_BYTES + x / 8.
             *
             * bit: which bit within that byte is this pixel?
             *   - Bits are stored MSB-first (most significant bit first),
             *     meaning bit 7 is the leftmost pixel in each byte.
             *   - (x & 7) gives the bit index within the byte (0..7).
             *   - (7 - (x & 7)) flips it so bit 7 = leftmost.
             *   - We shift right by that amount and mask with & 1 to
             *     extract just that one bit.
             *
             * Result: bit == 1 means black pixel ('#'), 0 means white (' ').
             */
            int byte_idx = y * SCREEN_ROW_BYTES + x / 8;
            int bit = (fb[byte_idx] >> (7 - (x & 7))) & 1;
            printf("%c", bit ? '#' : ' ');
        }
        printf("|\n");  /* right border + newline */
    }

    /* Print the bottom border */
    printf("+");
    for (int x = 0; x < DILDER_SCREEN_W; x += 2) printf("-");
    printf("+\n");
}

/*
 * print_game_state -- display all game stats in the terminal.
 *
 * Calls the public API query functions (dilder_get_*) to read the
 * current game state and prints them in a human-readable format.
 * This is the same data the DevTool shows in its GUI panels.
 */
static void print_game_state(void) {
    printf("\n--- Game State ---\n");
    printf("State: %s  |  Emotion: %s  |  Stage: %s\n",
           dilder_get_state_name(),
           dilder_get_emotion_name(),
           dilder_get_stage_name());
    printf("Tick: %d  |  Age: %ds\n",
           dilder_get_tick_count(), dilder_get_age_seconds());

    /*
     * Primary stats -- these are the core vitals of the pet.
     * Abbreviated for compact display:
     *   HUN = hunger, HAP = happiness, ENE = energy,
     *   HYG = hygiene, HEA = health, WGT = weight
     */
    printf("HUN:%d  HAP:%d  ENE:%d  HYG:%d  HEA:%d  WGT:%d\n",
           dilder_get_hunger(), dilder_get_happiness(),
           dilder_get_energy(), dilder_get_hygiene(),
           dilder_get_health(), dilder_get_weight());
    printf("Bond XP:%d  Level:%d  Discipline:%d\n",
           dilder_get_bond_xp(), dilder_get_bond_level(),
           dilder_get_discipline());

    /*
     * Sensor readings -- these are the emulated sensor values the game
     * engine is currently using.  "%.0f" means print a float with zero
     * decimal places; "%.1f" means one decimal place.
     */
    printf("Light:%.0f lux  Temp:%.1fC  Humidity:%.0f%%\n",
           dilder_get_sensor_light(), dilder_get_sensor_temp(),
           dilder_get_sensor_humidity());

    /*
     * Dialogue text -- only printed if there's active dialogue.
     * The `dlg[0]` check tests whether the first character is non-zero
     * (i.e., the string is not empty).  In C, strings are arrays of
     * characters ending with a '\0' (null terminator).  An empty string
     * "" has only the null terminator, so dlg[0] == '\0' == 0 == false.
     */
    const char *dlg = dilder_get_dialogue_text();
    if (dlg && dlg[0]) {
        printf("Dialogue: \"%s\"\n", dlg);
    }
}

/*
 * main -- the program entry point.
 *
 * In C, every program starts executing at the main() function.
 *
 * Parameters:
 *   argc -- "argument count": how many command-line arguments were passed
 *           (including the program name itself, so argc >= 1 always).
 *   argv -- "argument vector": an array of C strings (char *) containing
 *           the actual arguments.  argv[0] is the program name,
 *           argv[1] is the first user argument, etc.
 *
 * Return value:
 *   0 means success (convention in C/Unix).  Non-zero means error.
 */
int main(int argc, char *argv[]) {
    /*
     * Parse the optional "ticks" argument from the command line.
     * atoi() converts a string like "50" to the integer 50.
     * If no argument is given, default to 30 ticks.
     */
    int ticks = 30;
    if (argc > 1) ticks = atoi(argv[1]);
    if (ticks < 1) ticks = 1;  /* at least one tick */

    printf("Dilder Firmware CLI — running %d ticks\n\n", ticks);

    /* Initialize all game systems (stats, emotion, display, etc.) */
    dilder_init();

    /*
     * Main simulation loop -- run the game for the requested number of
     * ticks.  Some interesting events are injected at specific ticks
     * to demonstrate game behavior:
     */
    for (int i = 0; i < ticks; i++) {
        /* At tick 3: simulate pressing the ACTION button (short press)
         * to feed the pet, so we can see stat changes from a care action. */
        if (i == 3) {
            printf(">>> Pressing ACTION (feed)\n");
            dilder_button_press(5, 1);  /* 5 = BTN_ACTION, 1 = PRESS_SHORT */
        }

        /* At tick 10: set the temperature to 35C to test the pet's
         * reaction to an uncomfortable environment. */
        if (i == 10) {
            printf(">>> Setting temperature to 35C (too hot!)\n");
            dilder_set_temperature(35.0f);  /* the 'f' suffix makes this a float literal */
        }

        /* Advance the game by one tick (one game-second) */
        dilder_tick();

        /* Render the current frame and stats to the terminal */
        print_framebuffer();
        print_game_state();

        /*
         * Pause and wait for the user to press Enter before continuing.
         * getchar() reads one character from standard input (the keyboard).
         * When you press Enter, it reads the newline character and returns.
         *
         * We skip the wait on the last tick (i == ticks - 1) so the
         * program exits immediately after the final frame.
         */
        printf("\n[Tick %d/%d] Press Enter to continue...", i + 1, ticks);
        if (i < ticks - 1) getchar();
    }

    printf("\nDone.\n");
    return 0;  /* exit code 0 = success */
}
