# Breadboard Wiring Guide — Full Test Bench

> Complete wiring diagram and setup instructions for all current hardware components on a single breadboard with the Raspberry Pi Pico WH.

---

## Table of Contents

1. [Components](#1-components)
2. [Pin Assignment Table](#2-pin-assignment-table)
3. [Master Wiring Diagram](#3-master-wiring-diagram)
4. [Pico WH Pin Map — All Peripherals](#4-pico-wh-pin-map--all-peripherals)
5. [Component-by-Component Wiring](#5-component-by-component-wiring)
    - [5.1 Waveshare 2.13" e-Paper V3 (SPI1)](#51-waveshare-213-e-paper-v3-spi1)
    - [5.2 DollaTek 5-Way Joystick (GPIO)](#52-dollatek-5-way-joystick-gpio)
    - [5.3 GY-NEO6MV2 GPS Module (UART0)](#53-gy-neo6mv2-gps-module-uart0)
    - [5.4 HC-SR04 Ultrasonic Sensor (GPIO)](#54-hc-sr04-ultrasonic-sensor-gpio)
6. [Recommended 3.3V Speakers](#6-recommended-33v-speakers)
7. [Breadboard Layout Strategy](#7-breadboard-layout-strategy)
8. [Power Budget](#8-power-budget)
9. [Important Notes and Warnings](#9-important-notes-and-warnings)
10. [Quick Test Code](#10-quick-test-code)
    - [10.1 GPS Serial Test](#101-gps-serial-test)
    - [10.2 HC-SR04 Distance Test](#102-hc-sr04-distance-test)
    - [10.3 All-Peripherals Diagnostic](#103-all-peripherals-diagnostic)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Components

| # | Component | Model | Interface | Voltage | Notes |
|---|-----------|-------|-----------|---------|-------|
| 1 | **Microcontroller** | Raspberry Pi Pico WH | — | 3.3V logic / 5V USB | Pre-soldered headers |
| 2 | **e-Paper Display** | Waveshare Pico-ePaper-2.13 | SPI1 | VSYS (1.8-5.5V) | SSD1680 driver, 250x122px, Pico-native module |
| 3 | **5-Way Joystick** | DollaTek 5D Navigation | GPIO (active LOW) | 3.3V | Up/Down/Left/Right/Center |
| 4 | **GPS Module** | GY-NEO6MV2 (NEO-6M) | UART (9600 baud) | 3.3-5V | NMEA output, onboard regulator |
| 5 | **Ultrasonic Sensor** | HC-SR04 | GPIO (TRIG/ECHO) | **5V** | Needs voltage divider on ECHO |

---

## 2. Pin Assignment Table

| Peripheral | Signal | Pico GPIO | Physical Pin | Direction | Interface |
|------------|--------|-----------|-------------|-----------|-----------|
| **e-Paper** | VSYS | VSYS | 39 | Power in | — |
| | GND | GND | 38 | Ground | — |
| | DIN (MOSI) | GP11 | 15 | Out | SPI1 TX |
| | CLK | GP10 | 14 | Out | SPI1 SCK |
| | CS | GP9 | 12 | Out | SPI1 CSn |
| | DC | GP8 | 11 | Out | Digital |
| | RST | GP12 | 16 | Out | Digital |
| | BUSY | GP13 | 17 | In | Digital |
| **Joystick** | UP | GP2 | 4 | In (pull-up) | GPIO |
| | DOWN | GP3 | 5 | In (pull-up) | GPIO |
| | LEFT | GP4 | 6 | In (pull-up) | GPIO |
| | RIGHT | GP5 | 7 | In (pull-up) | GPIO |
| | CENTER | GP6 | 9 | In (pull-up) | GPIO |
| | COM/GND | GND | 8 | Ground | — |
| **GPS** | TX (to Pico RX) | GP1 (UART0 RX) | 2 | In | UART0 |
| | RX (from Pico TX) | GP0 (UART0 TX) | 1 | Out | UART0 |
| | VCC | 3V3(OUT) | 36 | Power out | — |
| | GND | GND | 3 | Ground | — |
| **HC-SR04** | VCC | VBUS (5V) | 40 | Power out | — |
| | TRIG | GP14 | 19 | Out | Digital |
| | ECHO (via divider) | GP16 | 21 | In | Digital |
| | GND | GND | 23 | Ground | — |
| **Reserved** | Buzzer (future) | GP15 | 20 | Out | PWM |
| **Total** | | **15 GPIO** | | | |
| **Free** | | **GP7, GP15, GP17-22, GP26-28** | | | **11 GPIO remaining** |

---

## 3. Master Wiring Diagram

```
                         PICO WH
                    .----[USB]----.
GPS TX --------> GP0  [1]  |  [40] VBUS ---------> HC-SR04 VCC (5V)
GPS RX <-------- GP1  [2]  |  [39] VSYS ---------> e-Paper VSYS
GPS GND -------> GND  [3]  |  [38] GND ----------> e-Paper GND
Joystick UP ---> GP2  [4]  |  [37] 3V3_EN
Joystick DOWN -> GP3  [5]  |  [36] 3V3(OUT) -----> GPS VCC
Joystick LEFT -> GP4  [6]  |  [35] ADC_VREF
Joystick RIGHT > GP5  [7]  |  [34] GP28
Joystick GND --> GND  [8]  |  [33] AGND
Joystick CTR --> GP6  [9]  |  [32] GP27
                 GP7 [10]  |  [31] GP26
e-Paper DC <---- GP8 [11]  |  [30] RUN
e-Paper CS <---- GP9 [12]  |  [29] GP22
                 GND [13]  |  [28] GND
e-Paper CLK <-- GP10 [14]  |  [27] GP21
e-Paper DIN <-- GP11 [15]  |  [26] GP20
e-Paper RST <-- GP12 [16]  |  [25] GP19
e-Paper BUSY -> GP13 [17]  |  [24] GP18
                 GND [18]  |  [23] GND ----------> HC-SR04 GND
HC-SR04 TRIG <- GP14 [19]  |  [22] GP17
(future buzzer) GP15 [20]  |  [21] GP16 <------.
                    '-------+------'            |
                                                |
                HC-SR04 ECHO --[1K]--+-- GP16   |
                                     |          |
                                   [2K]    (voltage
                                     |     divider)
                                    GND
```

**Legend:**
- `-->` or `<--` = signal direction (arrow points to receiver)
- `-.-->` = power rail split to multiple devices
- HC-SR04 ECHO must go through the 1K+2K voltage divider before reaching GP16

---

## 4. Pico WH Pin Map — All Peripherals

```
                .----[USB]----.
 GPS TX>RX GP0 [1]  |        | [40] VBUS  HC-SR04 5V
 GPS RX<TX GP1 [2]  |        | [39] VSYS  e-Paper VSYS
 GPS GND   GND [3]  |  PICO  | [38] GND   e-Paper GND
 JOY UP    GP2 [4]  |   WH   | [37] 3V3_EN
 JOY DOWN  GP3 [5]  |        | [36] 3V3   GPS VCC
 JOY LEFT  GP4 [6]  |        | [35] VREF
 JOY RIGHT GP5 [7]  |        | [34] GP28
 JOY GND   GND [8]  |        | [33] AGND
 JOY CTR   GP6 [9]  |        | [32] GP27
           GP7 [10] |        | [31] GP26
 EPD DC    GP8 [11] |        | [30] RUN
 EPD CS    GP9 [12] |        | [29] GP22
           GND [13] |        | [28] GND
 EPD CLK  GP10 [14] |        | [27] GP21
 EPD DIN  GP11 [15] |        | [26] GP20
 EPD RST  GP12 [16] |        | [25] GP19
 EPD BUSY GP13 [17] |        | [24] GP18
           GND [18] |        | [23] GND   HC-SR04 GND
 SR04 TRG GP14 [19] |        | [22] GP17
 (buzzer) GP15 [20] |        | [21] GP16  SR04 ECHO (divider)
                '----+--------'
```

---

## 5. Component-by-Component Wiring

### 5.1 Waveshare Pico-ePaper-2.13 (SPI1)

#### About the Module's 40-Pin Header

The Waveshare Pico-ePaper-2.13 is a **Pico-native module** — it has a **40-pin female GPIO header** on the back designed to plug directly onto the Raspberry Pi Pico W's male header pins. When seated directly on the Pico, no jumper wires are needed for the display — all SPI, control, and power pins align automatically.

> **Direct plug vs. breadboard:** You can plug the module straight onto the Pico W for a compact setup. For breadboard prototyping (where you need access to all Pico pins for other peripherals), use the module's **8-pin breakout header** with female-to-male jumper wires instead.

#### Pin Mapping (Pico W)

| e-Paper Pin | Wire Color (suggested) | Pico WH Pin | GPIO | Function |
|------------|------------------------|-------------|------|----------|
| VSYS | Red | Pin 39 (VSYS) | — | System power (1.8-5.5V) |
| GND | Black | Pin 38 (GND) | — | Ground |
| DIN | Blue | Pin 15 | GP11 (SPI1 TX) | SPI MOSI |
| CLK | Yellow | Pin 14 | GP10 (SPI1 SCK) | SPI clock |
| CS | Orange | Pin 12 | GP9 (SPI1 CSn) | Chip select (active LOW) |
| DC | Green | Pin 11 | GP8 | Data/command select |
| RST | White | Pin 16 | GP12 | Reset (active LOW) |
| BUSY | Purple | Pin 17 | GP13 | Busy flag (input) |

**SPI Config:** SPI1, Mode 0, 4 MHz, MSB-first.

> **Power note:** The module's 8-pin header is labeled **VSYS** (not VCC). This connects to the Pico's VSYS rail (pin 39), which provides the USB voltage (~5V when powered via USB). The module has an onboard voltage regulator that steps this down to 3.3V for the display. Do **not** connect VSYS to the 3V3(OUT) pin — use pin 39.

---

### 5.2 DollaTek 5-Way Joystick (GPIO)

Check the module's silkscreen for pin labels. Wire each direction to its GPIO and COM to ground.

| Module Pin | Wire Color (suggested) | Pico WH Pin | GPIO |
|-----------|------------------------|-------------|------|
| COM / GND | Black | Pin 8 (GND) | — |
| UP | Red | Pin 4 | GP2 |
| DOWN | Blue | Pin 5 | GP3 |
| LEFT | Yellow | Pin 6 | GP4 |
| RIGHT | Green | Pin 7 | GP5 |
| CENTER / SET | White | Pin 9 | GP6 |

**Config:** Internal pull-ups enabled in software. Active LOW (pressed = 0).

If your module has a VCC pin, leave it **unconnected**.

---

### 5.3 GY-NEO6MV2 GPS Module (UART0)

The GY-NEO6MV2 has 4 pins: VCC, GND, TX, RX. It has an onboard voltage regulator that accepts 3.3-5V input and an onboard antenna (ceramic patch).

| GPS Pin | Wire Color (suggested) | Pico WH Pin | GPIO | Notes |
|---------|------------------------|-------------|------|-------|
| VCC | Red | Pin 36 (3V3 OUT) | — | 3.3V is fine — onboard regulator handles it |
| GND | Black | Pin 3 (GND) | — | Any GND pin works |
| TX | Green | Pin 2 | GP1 (UART0 RX) | GPS transmits, Pico receives |
| RX | Yellow | Pin 1 | GP0 (UART0 TX) | Pico transmits, GPS receives |

**CRITICAL: TX/RX crossover.** The GPS module's TX pin connects to the Pico's RX pin (GP1), and vice versa. Transmit always connects to receive on the other end.

```
GPS Module       Pico WH
.--------.       .--------.
|     TX |------>| GP1 RX |   GPS sends NMEA data to Pico
|     RX |<-----|  GP0 TX |   Pico sends commands to GPS
|    VCC |------>| 3V3OUT |
|    GND |------>| GND    |
'--------'       '--------'
```

**UART Config:** 9600 baud, 8N1 (default NEO-6M settings).

**First fix:** The GPS needs a clear view of the sky. First cold fix can take **1-5 minutes** outdoors. The onboard LED blinks once per second when it has a fix.

**Power draw:** ~45mA active, ~10mA with backup battery maintaining hot start.

---

### 5.4 HC-SR04 Ultrasonic Sensor (GPIO)

The HC-SR04 measures distance (2-400cm) using ultrasonic pulses. It operates at **5V** — this requires special handling because the Pico's GPIO is **3.3V only**.

| HC-SR04 Pin | Wire Color (suggested) | Pico WH Pin | GPIO | Notes |
|------------|------------------------|-------------|------|-------|
| VCC | Red | Pin 40 (VBUS, 5V) | — | **Must be 5V** — will not work on 3.3V |
| TRIG | Orange | Pin 19 | GP14 | 3.3V output is enough to trigger |
| ECHO | Yellow (through divider) | Pin 21 | GP16 | **MUST use voltage divider** |
| GND | Black | Pin 23 (GND) | — | |

#### ECHO Voltage Divider (Required)

The ECHO pin outputs a 5V pulse. Feeding 5V directly into GP16 **will damage the Pico**. Use a resistor voltage divider to drop it to ~3.3V:

```
HC-SR04 ECHO ---[1K]---+--- GP16 (Pin 21)
                        |
                      [2K]
                        |
                       GND

Output: 5V x 2K / (1K + 2K) = 3.33V   Safe for Pico
```

**Alternative resistor values that work:**
- 1K + 2K = 3.33V (ideal)
- 1K + 1.8K = 3.21V (fine)
- 2.2K + 3.3K = 3.0V (safe, slightly lower)

**Do NOT skip the voltage divider.** Connecting ECHO directly to any Pico GPIO will send 5V into a 3.3V-rated pin and permanently damage the RP2040 chip.

**How the HC-SR04 works:**

1. Pico sends 10us HIGH pulse on TRIG (GP14)
2. HC-SR04 emits 8 ultrasonic bursts at 40kHz
3. HC-SR04 sets ECHO HIGH
4. Sound wave travels, bounces off object, returns
5. HC-SR04 sets ECHO LOW
6. Pico measures ECHO pulse duration
7. Distance (cm) = pulse_duration_us / 58

**Range:** 2cm to 400cm. **Cone angle:** ~15 degrees.

---

## 6. Recommended 3.3V Speakers

GP15 is reserved for audio output (PWM). When you're ready to add sound, these speakers work directly at 3.3V without a transistor or amplifier:

| Speaker | Type | Voltage | Loudness | Cost | Notes |
|---------|------|---------|----------|------|-------|
| **CMT-4023S-SMT** | Piezo SMD buzzer | 1-30V | ~75dB | ~$0.50 | Best for PCB. Wire GP15 to (+), GND to (-). Loud enough for alerts. |
| **PKLCS1212E4001** | Murata piezo disc | 1.5-20V | ~70dB | ~$1 | Thin (1.2mm), good for tight enclosures. |
| **HXD Passive Buzzer Module** | Passive piezo on breakout | 3.3-5V | ~85dB | ~$1-2 | Breadboard-friendly, 3 pins (SIG, VCC, GND). VCC to 3.3V, SIG to GP15. Search "passive buzzer module 3.3V" on AliExpress. |
| **Adafruit Mini Speaker 8ohm** | Magnetic speaker | 2-5V | ~80dB | ~$2 | Richer tone than piezo. Needs a 100ohm series resistor from GP15 to limit current. |
| **CSS-0578-SMT** (CUI) | Piezo SMD | 1.5-20V | ~70dB | ~$1 | Same as PicoTop uses. Proven on RP2040/RP2350 at 3.3V. |

**Simplest option for breadboard testing:** Get a **passive buzzer module** (3-pin, SIG/VCC/GND). Wire VCC to 3.3V, GND to GND, SIG to GP15. No resistors, no transistor, plug and play.

**For the final PCB:** The **CMT-4023S-SMT** or **CSS-0578-SMT** are the best fit — SMD, small, proven at 3.3V, and loud enough for pet notification sounds.

---

## 7. Breadboard Layout Strategy

Use a **full-size breadboard** (830 tie points). A half-size board will be very cramped.

```
.---------------------------------------------------------------.
|                     FULL-SIZE BREADBOARD                       |
|                                                                |
| + Power Rail (top) ---- 3.3V from Pin 36 -------------------- |
| - Ground Rail (top) --- GND from Pin 38 --------------------- |
|                                                                |
| .-------------.                                                |
| | GPS Module  |  Left end, near GP0/GP1                       |
| | GY-NEO6MV2  |  VCC to 3.3V rail, GND to GND rail           |
| '-------------'  TX to Pin 2, RX from Pin 1                   |
|                                                                |
| .---------------------------------------.                      |
| |          PICO WH (centered)           |                      |
| |    Straddles the center channel       |                      |
| |                                       |                      |
| |  Left side:  Joystick (pins 4-9)      |                      |
| |              Display SPI (pins 11-17) |                      |
| |                                       |                      |
| |  Right side: 3V3, GND, VBUS (36-40)  |                      |
| '---------------------------------------'                      |
|                                                                |
| .-------------.    .--------------------.                      |
| | Joystick    |    |    HC-SR04         |                      |
| | Module      |    |  + Voltage Divider |                      |
| | (left of    |    |  (right of Pico)   |                      |
| |  Pico)      |    '--------------------'                      |
| '-------------'                                                |
|                                                                |
| + Power Rail (bottom) - 5V from VBUS Pin 40 (HC-SR04 only) -- |
| - Ground Rail (bottom) - GND (bridged to top GND rail) ------- |
|                                                                |
| e-Paper connects via flying wires (F-M jumpers) from the      |
| module's 8-pin header, or plugs directly onto the Pico        |
'---------------------------------------------------------------'
```

**Rail setup:**
1. Bridge the **top power rail** to **Pin 36 (3V3 OUT)** for 3.3V
2. Bridge the **top ground rail** to **Pin 38 (GND)**
3. Bridge the **bottom power rail** to **Pin 40 (VBUS)** for 5V (HC-SR04 only)
4. Bridge the **bottom ground rail** to the top ground rail (shared GND)

---

## 8. Power Budget

| Component | Active Current | Voltage | Source |
|-----------|---------------|---------|--------|
| Pico WH (WiFi off) | ~28mA | 3.3V | Internal LDO |
| e-Paper display (refreshing) | ~5mA | VSYS | Pin 39 (onboard regulator) |
| e-Paper display (static) | ~0.01mA | VSYS | Pin 39 (onboard regulator) |
| GPS module (acquiring) | ~45mA | 3.3V | 3V3(OUT) |
| GPS module (tracking) | ~35mA | 3.3V | 3V3(OUT) |
| HC-SR04 | ~15mA | 5V | VBUS |
| Joystick | ~0mA | — | Passive switches |
| **Total (all active)** | **~95mA** | | |

The 3V3(OUT) rail is rated for **300mA max**. The e-Paper module draws from VSYS (pin 39) via its own onboard regulator, not from 3V3(OUT) — so the GPS (~45mA) is the main 3V3 consumer, well within limits.

**USB power (from computer/adapter):** Provides 500mA on VBUS, more than enough.

The GPS is the biggest consumer. If running on battery later, consider powering GPS only when needed via a GPIO-controlled MOSFET switch.

---

## 9. Important Notes and Warnings

### Voltage Levels

| Component | Logic Level | Safe on Pico? |
|-----------|------------|---------------|
| e-Paper | 3.3V logic, VSYS power | Yes — SPI signals are 3.3V, power via VSYS (onboard regulator) |
| Joystick | 3.3V (passive) | Yes — direct connection |
| GPS (TX/RX) | 3.3V | Yes — GY-NEO6MV2 has 3.3V logic |
| HC-SR04 TRIG | 3.3V input accepted | Yes — 3.3V exceeds the HIGH threshold |
| HC-SR04 ECHO | **5V output** | **NO — use voltage divider** |

### GPS Antenna

- Keep antenna side facing **up** (toward sky)
- Avoid metallic objects or wires over the antenna
- First fix requires outdoor or window-side placement
- Onboard LED blinks at 1Hz when GPS has a fix

### HC-SR04 Variants

Some modules are available in a **3.3V variant** (labeled HC-SR04P or "3V-5.5V" on the board). If you have this variant, skip the voltage divider and power from 3V3(OUT) instead of VBUS. Check the silkscreen.

### UART0 and USB Serial

UART0 (GP0/GP1) is used for GPS. **USB serial debugging still works** — the Pico SDK sends printf over the USB CDC interface, not UART0. You can monitor GPS data and debug output simultaneously.

---

## 10. Quick Test Code

### 10.1 GPS Serial Test

Read NMEA sentences from the GPS over UART0:

```c
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"

#define GPS_UART uart0
#define GPS_BAUD 9600
#define GPS_TX_PIN 0
#define GPS_RX_PIN 1

int main() {
    stdio_init_all();
    sleep_ms(2000);

    uart_init(GPS_UART, GPS_BAUD);
    gpio_set_function(GPS_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(GPS_RX_PIN, GPIO_FUNC_UART);

    printf("=== GPS Test ===\n");
    printf("Waiting for NMEA data...\n\n");

    while (1) {
        if (uart_is_readable(GPS_UART)) {
            char c = uart_getc(GPS_UART);
            putchar(c);
        }
    }
}
```

**With fix:**
```
$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,47.0,M,,*47
$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
```

**No fix yet:**
```
$GPGGA,,,,,,0,00,99.99,,,,,,*48
```

### 10.2 HC-SR04 Distance Test

```c
#include <stdio.h>
#include "pico/stdlib.h"

#define TRIG_PIN 14
#define ECHO_PIN 16

float measure_distance_cm(void) {
    gpio_put(TRIG_PIN, 1);
    sleep_us(10);
    gpio_put(TRIG_PIN, 0);

    uint32_t start = time_us_32();
    while (gpio_get(ECHO_PIN) == 0) {
        if (time_us_32() - start > 30000) return -1;
    }

    uint32_t pulse_start = time_us_32();
    while (gpio_get(ECHO_PIN) == 1) {
        if (time_us_32() - pulse_start > 30000) return -1;
    }

    return (float)(time_us_32() - pulse_start) / 58.0f;
}

int main() {
    stdio_init_all();
    sleep_ms(2000);

    gpio_init(TRIG_PIN);
    gpio_set_dir(TRIG_PIN, GPIO_OUT);
    gpio_init(ECHO_PIN);
    gpio_set_dir(ECHO_PIN, GPIO_IN);

    printf("=== HC-SR04 Distance Test ===\n\n");

    while (1) {
        float dist = measure_distance_cm();
        if (dist > 0)
            printf("Distance: %.1f cm\n", dist);
        else
            printf("Out of range / timeout\n");
        sleep_ms(500);
    }
}
```

### 10.3 All-Peripherals Diagnostic

```c
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"

#define GPS_UART   uart0
#define GPS_TX     0
#define GPS_RX     1
#define BTN_UP     2
#define BTN_DOWN   3
#define BTN_LEFT   4
#define BTN_RIGHT  5
#define BTN_CENTER 6
#define TRIG_PIN   14
#define ECHO_PIN   16

void test_buttons(void) {
    const uint btns[] = {BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT, BTN_CENTER};
    const char *names[] = {"UP", "DOWN", "LEFT", "RIGHT", "CENTER"};
    printf("[JOYSTICK] ");
    for (int i = 0; i < 5; i++) {
        if (gpio_get(btns[i]) == 0)
            printf("%s ", names[i]);
    }
    printf("\n");
}

float test_distance(void) {
    gpio_put(TRIG_PIN, 1);
    sleep_us(10);
    gpio_put(TRIG_PIN, 0);
    uint32_t start = time_us_32();
    while (gpio_get(ECHO_PIN) == 0)
        if (time_us_32() - start > 30000) return -1;
    uint32_t t0 = time_us_32();
    while (gpio_get(ECHO_PIN) == 1)
        if (time_us_32() - t0 > 30000) return -1;
    return (float)(time_us_32() - t0) / 58.0f;
}

int main() {
    stdio_init_all();
    sleep_ms(2000);

    for (uint pin = BTN_UP; pin <= BTN_CENTER; pin++) {
        gpio_init(pin);
        gpio_set_dir(pin, GPIO_IN);
        gpio_pull_up(pin);
    }

    gpio_init(TRIG_PIN);
    gpio_set_dir(TRIG_PIN, GPIO_OUT);
    gpio_init(ECHO_PIN);
    gpio_set_dir(ECHO_PIN, GPIO_IN);

    uart_init(GPS_UART, 9600);
    gpio_set_function(GPS_TX, GPIO_FUNC_UART);
    gpio_set_function(GPS_RX, GPIO_FUNC_UART);

    printf("==========================================\n");
    printf("  DILDER ALL-PERIPHERALS DIAGNOSTIC\n");
    printf("==========================================\n\n");

    while (1) {
        printf("--- tick ---\n");

        test_buttons();

        float d = test_distance();
        if (d > 0)
            printf("[HC-SR04] Distance: %.1f cm\n", d);
        else
            printf("[HC-SR04] No reading\n");

        printf("[GPS] ");
        bool got_data = false;
        uint32_t gps_start = time_us_32();
        while (time_us_32() - gps_start < 100000) {
            if (uart_is_readable(GPS_UART)) {
                char c = uart_getc(GPS_UART);
                putchar(c);
                got_data = true;
                if (c == '\n') break;
            }
        }
        if (!got_data) printf("No data (check wiring / sky view)\n");

        printf("\n");
        sleep_ms(1000);
    }
}
```

---

## 11. Troubleshooting

| Symptom | Component | Likely Cause | Fix |
|---------|-----------|-------------|-----|
| Display shows nothing | e-Paper | SPI wiring wrong or VCC not on 3V3 | Check all 8 wires, confirm 3V3 not VBUS |
| No joystick response | Joystick | COM not grounded or pull-ups not set | Check GND wire, verify `gpio_pull_up()` |
| GPS shows empty fields | GPS | No satellite fix | Move near window or outdoors, wait 1-5 min |
| GPS shows nothing | GPS | TX/RX swapped or wrong baud | Swap GP0/GP1 wires, confirm 9600 baud |
| GPS shows garbage | GPS | Baud rate mismatch | Default is 9600, don't change it |
| HC-SR04 always -1 | HC-SR04 | No 5V or ECHO divider wrong | Confirm VCC on VBUS (5V), check resistors |
| HC-SR04 damaged Pico | HC-SR04 | ECHO direct (no divider) | Pico is likely damaged. Always use divider |
| HC-SR04 max range | HC-SR04 | Nothing in front or angled | Point at flat surface 10-100cm away |
| Multiple things fail | Power | 3V3 rail overloaded | Check current draw, should be ~80mA |
| Pico resets randomly | Power | USB port weak | Use powered USB hub or wall adapter |
| USB serial nothing | Pico | Not flashed or wrong port | Re-flash via BOOTSEL + UF2 |

---

## Appendix: Wire Shopping List

| Item | Quantity | Notes |
|------|----------|-------|
| Male-to-male jumper wires | ~15 | For breadboard connections |
| Female-to-male jumper wires | ~10 | For e-Paper 8-pin breakout header (if not using direct plug) |
| 1K resistor | 1 | HC-SR04 voltage divider |
| 2K resistor (or 1.8K) | 1 | HC-SR04 voltage divider |
| Full-size breadboard | 1 | 830 tie points recommended |

---

*Document version: 2.0 — Updated 2026-04-14*
