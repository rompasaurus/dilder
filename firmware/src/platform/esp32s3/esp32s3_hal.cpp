/*
 * esp32s3_hal.cpp -- Hardware Abstraction Layer for Olimex ESP32-S3-DevKit-Lipo
 *
 * Provides board-specific initialization for the ESP32-S3 platform:
 *   - SPI setup for the Waveshare 2.13" e-Paper display (FSPI / SPI3)
 *   - GPIO setup for the 5-way joystick (internal pull-ups)
 *   - Battery voltage ADC reading
 *   - On-board LED control
 *
 * This file is only compiled when BOARD_ESP32S3 is defined.
 * Compiled as C++ for Arduino SPI API, but exports C linkage for the
 * shared game engine.
 */

/*
 * --------------------------------------------------------------------------
 *  BEGINNER NOTES: What is the Arduino framework?
 * --------------------------------------------------------------------------
 *
 *  The Arduino framework is a C/C++ library that gives you simple, friendly
 *  functions for controlling microcontroller hardware.  Instead of writing
 *  raw register addresses like:
 *
 *      *(volatile uint32_t *)0x3FF44004 = (1 << 2);  // yikes
 *
 *  ...you can just call:
 *
 *      pinMode(2, OUTPUT);
 *      digitalWrite(2, HIGH);
 *
 *  Arduino was originally designed for its own boards, but libraries like
 *  "Arduino-ESP32" let us use the same friendly API on ESP32 chips too.
 *
 *  Key Arduino functions used in this file:
 *
 *    pinMode(pin, mode)
 *        Configures a GPIO pin.  Common modes:
 *          - INPUT        : read external signals
 *          - OUTPUT       : drive a pin HIGH or LOW
 *          - INPUT_PULLUP : read external signals, with a built-in pull-up
 *                           resistor enabled (more on this below)
 *
 *    digitalRead(pin)
 *        Returns HIGH (1) or LOW (0) — the current logic level on the pin.
 *
 *    digitalWrite(pin, value)
 *        Sets a pin to HIGH (3.3 V) or LOW (0 V).
 *
 *    analogRead(pin)
 *        Reads an analog voltage and converts it to a number.
 *        With 12-bit resolution: 0 = 0 V, 4095 = 3.3 V.
 *
 *    delay(ms)
 *        Pauses execution for the given number of milliseconds.
 *
 *    millis()
 *        Returns the number of milliseconds since the board powered on.
 *
 *  These functions are declared in <Arduino.h>, which is included below.
 * --------------------------------------------------------------------------
 */

/*
 * --------------------------------------------------------------------------
 *  BEGINNER NOTES: What is INPUT_PULLUP and active-LOW logic?
 * --------------------------------------------------------------------------
 *
 *  Physical buttons are simple switches.  When you press one, it connects
 *  two wires together.  But when a button is NOT pressed, the GPIO pin is
 *  left "floating" — not connected to anything — and it will read random
 *  garbage (sometimes HIGH, sometimes LOW).
 *
 *  A "pull-up resistor" fixes this.  It gently connects the pin to 3.3 V
 *  through a large resistor (~45 kOhm inside the ESP32-S3), so the pin
 *  reads HIGH when the button is not pressed.
 *
 *  When you press the button, it shorts the pin to GND (0 V), which
 *  overpowers the weak pull-up, and the pin reads LOW.
 *
 *  This is called "active LOW" because the button is active (pressed)
 *  when the signal is LOW:
 *
 *      Button released  -->  pin = HIGH  -->  digitalRead() returns 1
 *      Button pressed   -->  pin = LOW   -->  digitalRead() returns 0
 *
 *  But our game engine expects: pressed = 1, not pressed = 0.
 *  So we INVERT the logic by comparing to LOW:
 *
 *      digitalRead(PIN_BTN_UP) == LOW
 *
 *  This expression is true (1) when the button IS pressed, and false (0)
 *  when it is not — exactly what the game engine expects.
 *
 *  INPUT_PULLUP tells the ESP32 to enable this internal pull-up resistor
 *  for us, so we don't need to add an external resistor on the PCB.
 * --------------------------------------------------------------------------
 */

/*
 * --------------------------------------------------------------------------
 *  BEGINNER NOTES: What is extern "C"?
 * --------------------------------------------------------------------------
 *
 *  C++ changes the names of functions behind the scenes.  A function called
 *  "hal_btn_up" might become something like "_Z10hal_btn_upv" in the
 *  compiled binary.  This is called "name mangling" and it lets C++ support
 *  function overloading (multiple functions with the same name but different
 *  parameters).
 *
 *  The game engine is written in plain C, which does NOT mangle names.
 *  When the C game engine calls hal_btn_up(), it looks for a symbol named
 *  exactly "hal_btn_up" in the binary — not the mangled C++ version.
 *
 *  extern "C" { ... } tells the C++ compiler: "Don't mangle the names of
 *  these functions.  Use plain C naming so that C code can find and call
 *  them."
 *
 *  We NEED C++ in this file because Arduino's SPI library (SPIClass) is a
 *  C++ class.  But we need C linkage so the C game engine can call our
 *  HAL functions.  extern "C" gives us both.
 *
 *  You'll see a matching extern "C" block in hal.h — that's the other side
 *  of this handshake, making sure the function declarations (prototypes)
 *  also use C linkage.
 * --------------------------------------------------------------------------
 */

/*
 * #ifdef BOARD_ESP32S3
 *
 * This is a "preprocessor guard."  The preprocessor is a text-processing
 * step that runs BEFORE the actual C/C++ compiler.  #ifdef means "if
 * defined" — it checks whether the symbol BOARD_ESP32S3 was defined
 * (usually via a -DBOARD_ESP32S3 flag passed by the build system).
 *
 * If BOARD_ESP32S3 is NOT defined, the preprocessor throws away ALL the
 * code between #ifdef and the matching #endif at the bottom of the file.
 * The compiler never even sees it.
 *
 * This lets us have multiple HAL implementation files in the project
 * (one per board) and only compile the one that matches our target board.
 */
#ifdef BOARD_ESP32S3

#include "platform/board_config.h"

/*
 * #ifdef ARDUINO
 *
 * This guard checks if we're building with the Arduino framework.
 * The Arduino build system automatically defines this symbol.
 * If someone were to build this project with ESP-IDF directly (no
 * Arduino layer), this block would be skipped and a different
 * implementation could be provided below.
 */
#ifdef ARDUINO
/* ── Arduino framework (PlatformIO default) ────────────────────────── */

/*
 * <Arduino.h> — Pulls in all the core Arduino functions we use:
 *   pinMode(), digitalRead(), digitalWrite(), analogRead(),
 *   delay(), millis(), HIGH, LOW, INPUT, OUTPUT, INPUT_PULLUP, etc.
 *
 * <SPI.h> — The Arduino SPI library.  SPI (Serial Peripheral Interface)
 *   is a communication protocol used to talk to the e-Paper display.
 *   It uses 4 wires: CLK (clock), MOSI (data out), CS (chip select),
 *   and optionally MISO (data in — we don't use it because we only
 *   WRITE to the display, never read from it).
 */
#include <Arduino.h>
#include <SPI.h>

/*
 * static SPIClass *epd_spi = NULL;
 *
 * This is a pointer to an SPIClass object — Arduino's C++ class for
 * controlling an SPI bus.  "static" here means this variable is private
 * to this file — no other .cpp file can access it.
 *
 * It starts as NULL (pointing to nothing) and gets created in
 * dilder_hal_init() with "new SPIClass(FSPI)".
 *
 * Why a pointer and "new" instead of a normal variable?
 * Because we want to control exactly WHEN the object is created
 * (during init, not at program startup), and we want to pick which
 * SPI bus to use at runtime (FSPI = SPI3 on the ESP32-S3).
 */
static SPIClass *epd_spi = NULL;

extern "C" {

/* ── dilder_hal_init ──────────────────────────────────────────────────
 *
 * This is the master initialization function.  It runs once at startup
 * and sets up every piece of hardware the Dilder needs:
 *   1. Joystick buttons (GPIO inputs with pull-ups)
 *   2. LED (GPIO output)
 *   3. e-Paper display control pins (GPIO outputs + one input)
 *   4. SPI bus for talking to the display
 *   5. ADC (Analog-to-Digital Converter) for battery monitoring
 */
void dilder_hal_init(void) {
    /*
     * Joystick — all buttons are active LOW, use internal pull-ups.
     *
     * INPUT_PULLUP enables a weak internal resistor that pulls the pin
     * to HIGH (3.3V) when the button is not pressed.  Pressing the
     * button connects the pin to GND (LOW).  See the "active-LOW"
     * explanation in the big comment block at the top of this file.
     *
     * Each of the 5 joystick directions is wired to a separate GPIO pin.
     * The PIN_BTN_* macros are defined in board_config.h and expand to
     * the actual GPIO numbers for this board (e.g., PIN_BTN_UP = GPIO 4).
     */
    pinMode(PIN_BTN_UP,     INPUT_PULLUP);
    pinMode(PIN_BTN_DOWN,   INPUT_PULLUP);
    pinMode(PIN_BTN_LEFT,   INPUT_PULLUP);
    pinMode(PIN_BTN_RIGHT,  INPUT_PULLUP);
    pinMode(PIN_BTN_CENTER, INPUT_PULLUP);

    /*
     * On-board LED (active LOW).
     *
     * This LED is wired between 3.3V and the GPIO pin through a resistor.
     * "Active LOW" means: setting the pin LOW turns the LED ON (current
     * flows from 3.3V through the LED to the LOW pin), and setting it
     * HIGH turns the LED OFF (no voltage difference, no current flow).
     *
     * We start with it OFF by writing HIGH.
     */
    pinMode(PIN_LED, OUTPUT);
    digitalWrite(PIN_LED, HIGH);  /* OFF */

    /*
     * e-Paper display control pins.
     *
     * Besides the SPI data lines (CLK and MOSI), the e-Paper display
     * needs several extra control signals:
     *
     *   CS   (Chip Select) — OUTPUT.  Pull LOW to tell the display
     *        "I'm talking to you."  Pull HIGH to deselect it.
     *        We start HIGH (deselected).
     *
     *   DC   (Data/Command) — OUTPUT.  Tells the display whether the
     *        bytes we're sending are commands (LOW) or pixel data (HIGH).
     *
     *   RST  (Reset) — OUTPUT.  Pulsing this LOW resets the display
     *        controller, like a reboot.
     *
     *   BUSY — INPUT.  The display sets this pin HIGH while it's busy
     *        updating.  We read it to know when it's safe to send more.
     */
    pinMode(PIN_EPD_CS,   OUTPUT);
    pinMode(PIN_EPD_DC,   OUTPUT);
    pinMode(PIN_EPD_RST,  OUTPUT);
    pinMode(PIN_EPD_BUSY, INPUT);

    digitalWrite(PIN_EPD_CS, HIGH);  /* deselect */

    /*
     * SPI bus initialization.
     *
     * The ESP32-S3 has multiple SPI controllers.  We use FSPI (also
     * called SPI3) because SPI0 and SPI1 are reserved for the flash
     * memory chip that stores our firmware.
     *
     * new SPIClass(FSPI)  — creates an SPI controller object using FSPI.
     *
     * epd_spi->begin(CLK, MISO, MOSI, CS) sets up the SPI pins:
     *   CLK  = PIN_EPD_CLK (clock signal, GPIO 12)
     *   MISO = -1  (not used — we never read FROM the display)
     *   MOSI = PIN_EPD_DIN (data IN to the display, GPIO 11)
     *   CS   = PIN_EPD_CS  (chip select, GPIO 10)
     *
     * After this call, the SPI hardware is ready to send data.
     */
    epd_spi = new SPIClass(FSPI);
    epd_spi->begin(PIN_EPD_CLK, -1 /* MISO unused */, PIN_EPD_DIN, PIN_EPD_CS);

    /*
     * Battery ADC (Analog-to-Digital Converter) configuration.
     *
     * analogReadResolution(12) — sets the ADC to 12-bit mode, meaning
     *   it returns values from 0 to 4095 (2^12 - 1 = 4095).
     *   0 means 0 volts, 4095 means the maximum measurable voltage.
     *
     * analogSetAttenuation(ADC_11db) — sets the input range to 0-3.3V.
     *   Without attenuation, the ADC can only measure up to ~1.1V.
     *   The 11dB attenuator scales the input down internally so we can
     *   measure the full 0-3.3V range that the voltage dividers output.
     */
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);
}

/* ── SPI write functions ──────────────────────────────────────────────
 *
 * These functions handle the low-level SPI communication with the
 * e-Paper display.  SPI works like this:
 *
 *   1. Begin a "transaction" — locks the bus settings (speed, bit order)
 *   2. Pull CS LOW to select the display chip
 *   3. Send the bytes over the MOSI wire, clocked by CLK
 *   4. Pull CS HIGH to deselect the display
 *   5. End the transaction — unlocks the bus
 *
 * SPISettings(EPD_SPI_FREQ_HZ, MSBFIRST, SPI_MODE0) configures:
 *   - EPD_SPI_FREQ_HZ = 4,000,000 (4 MHz clock speed)
 *   - MSBFIRST = send the Most Significant Bit first (standard for
 *     most SPI devices)
 *   - SPI_MODE0 = clock idles LOW, data sampled on rising edge
 *     (the most common SPI mode)
 */
void hal_spi_write(const uint8_t *data, uint16_t len) {
    if (!epd_spi) return;
    epd_spi->beginTransaction(SPISettings(EPD_SPI_FREQ_HZ, MSBFIRST, SPI_MODE0));
    digitalWrite(PIN_EPD_CS, LOW);
    epd_spi->transferBytes(data, NULL, len);
    digitalWrite(PIN_EPD_CS, HIGH);
    epd_spi->endTransaction();
}

/*
 * hal_epd_cmd — Send a command byte to the display controller.
 *
 * The e-Paper display uses the DC (Data/Command) pin to distinguish
 * between commands and data:
 *   DC = LOW  --> the byte is a COMMAND (e.g., "start full refresh")
 *   DC = HIGH --> the byte is DATA (e.g., pixel values)
 *
 * So to send a command, we pull DC LOW, send the byte over SPI,
 * then pull DC back HIGH (data mode is the default/safe state).
 */
void hal_epd_cmd(uint8_t cmd) {
    digitalWrite(PIN_EPD_DC, LOW);   /* command mode */
    hal_spi_write(&cmd, 1);
    digitalWrite(PIN_EPD_DC, HIGH);  /* back to data mode */
}

/*
 * hal_epd_data — Send one or more data bytes to the display.
 *
 * DC is kept HIGH to indicate these are data bytes, not commands.
 * This is used to send pixel data, configuration parameters, etc.
 */
void hal_epd_data(const uint8_t *data, uint16_t len) {
    digitalWrite(PIN_EPD_DC, HIGH);  /* data mode */
    if (!epd_spi) return;
    epd_spi->beginTransaction(SPISettings(EPD_SPI_FREQ_HZ, MSBFIRST, SPI_MODE0));
    digitalWrite(PIN_EPD_CS, LOW);
    epd_spi->transferBytes(data, NULL, len);
    digitalWrite(PIN_EPD_CS, HIGH);
    epd_spi->endTransaction();
}

/*
 * hal_epd_reset — Hardware-reset the display by pulsing RST LOW.
 *
 * Many chips have a hardware reset pin that forces them back to their
 * power-on default state, like unplugging and replugging them.
 * The display datasheet says: pull RST LOW for at least 10 ms, then
 * release it HIGH and wait at least 10 ms for the chip to start up.
 */
void hal_epd_reset(void) {
    digitalWrite(PIN_EPD_RST, LOW);
    delay(10);
    digitalWrite(PIN_EPD_RST, HIGH);
    delay(10);
}

/*
 * hal_epd_busy — Check if the display is still working.
 *
 * The display pulls its BUSY pin HIGH while it's updating the screen
 * (which can take seconds for e-Paper).  We poll this to know when
 * it's safe to send the next command.
 *
 * Returns: 1 if busy, 0 if ready.
 */
int hal_epd_busy(void) {
    return digitalRead(PIN_EPD_BUSY) == HIGH;
}

/* ── Joystick reading ─────────────────────────────────────────────────
 *
 * Each function reads one joystick direction.  Remember: the buttons
 * are wired active-LOW with internal pull-ups:
 *
 *   Not pressed: pin = HIGH (pulled up to 3.3V)
 *   Pressed:     pin = LOW  (shorted to GND)
 *
 * We compare to LOW so the function returns:
 *   1 (true)  when the button IS pressed
 *   0 (false) when the button is NOT pressed
 *
 * This inverts the electrical signal to match the logical meaning
 * that the rest of the code expects ("1 = pressed").
 */
int hal_btn_up(void)     { return digitalRead(PIN_BTN_UP)     == LOW; }
int hal_btn_down(void)   { return digitalRead(PIN_BTN_DOWN)   == LOW; }
int hal_btn_left(void)   { return digitalRead(PIN_BTN_LEFT)   == LOW; }
int hal_btn_right(void)  { return digitalRead(PIN_BTN_RIGHT)  == LOW; }
int hal_btn_center(void) { return digitalRead(PIN_BTN_CENTER) == LOW; }

/* ── LED control ──────────────────────────────────────────────────────
 *
 * The on-board LED is active LOW (see explanation above in init):
 *   LOW  = LED ON  (current flows through the LED)
 *   HIGH = LED OFF (no current flow)
 */
void hal_led_on(void)  { digitalWrite(PIN_LED, LOW);  }
void hal_led_off(void) { digitalWrite(PIN_LED, HIGH); }

/* ── Battery voltage measurement ──────────────────────────────────────
 *
 * The battery voltage (typically 3.0V - 4.2V for a LiPo cell) is too
 * high for the ESP32-S3's ADC to measure directly (max 3.3V input).
 *
 * So the Olimex board has a VOLTAGE DIVIDER — two resistors in series
 * that scale the voltage down.  The divider ratio is 4.133:1, meaning
 * the ADC sees (battery_voltage / 4.133).
 *
 * For example, a fully charged 4.2V battery:
 *   ADC sees: 4.2V / 4.133 = ~1.016V  (safely under 3.3V)
 *
 * To calculate the real battery voltage, we reverse the math:
 *
 *   Step 1: Convert the raw ADC reading to volts at the ADC pin.
 *           The ADC has 12-bit resolution (0-4095) over a 3.3V range:
 *
 *             adc_voltage = raw * (3.3 / 4095)
 *
 *   Step 2: Multiply by the divider ratio to get the real voltage:
 *
 *             battery_voltage = adc_voltage * 4.133
 *
 *   Combined into one line:
 *
 *             battery_voltage = raw * (3.3 / 4095.0) * 4.133
 *
 * The "f" suffix on numbers like 3.3f means "float" (single precision),
 * which is fine for our ~2 decimal places of accuracy.
 */
float hal_battery_voltage(void) {
    int raw = analogRead(PIN_BAT_ADC);
    return raw * (3.3f / 4095.0f) * 4.133f;
}

/* ── USB power detection ──────────────────────────────────────────────
 *
 * A separate voltage divider (ratio 1.468:1) scales the USB 5V power
 * rail down to a safe level for the ADC.
 *
 * When USB is plugged in:  5V / 1.468 = ~3.4V at the ADC pin
 * When USB is unplugged:   0V (or very low from battery backfeed)
 *
 * We convert the ADC reading to the real voltage using the same
 * approach as the battery measurement, then check if it's above 3.0V.
 *
 * If voltage > 3.0V, USB power is connected (returns 1).
 * If voltage <= 3.0V, USB power is not connected (returns 0).
 *
 * The 3.0V threshold gives us some margin — a solid USB connection
 * reads ~3.4V, so 3.0V handles slightly droopy USB supplies too.
 */
int hal_usb_power_connected(void) {
    int raw = analogRead(PIN_PWR_ADC);
    float voltage = raw * (3.3f / 4095.0f) * 1.468f;
    return voltage > 3.0f;  /* USB 5V through divider reads ~3.4V */
}

/*
 * hal_millis / hal_delay_ms — Thin wrappers around Arduino's
 * millis() and delay() functions.
 *
 * Why wrap them?  Because the game engine (written in C) calls these
 * through the HAL interface.  On a desktop build, hal_millis() might
 * use SDL_GetTicks() instead.  On Pico W, it might use to_ms_since_boot().
 * The game engine doesn't care — it just calls hal_millis() and gets
 * a millisecond count regardless of the platform.
 */
uint32_t hal_millis(void) {
    return millis();
}

void hal_delay_ms(uint32_t ms) {
    delay(ms);
}

} /* extern "C" */

#endif /* ARDUINO */
#endif /* BOARD_ESP32S3 */
