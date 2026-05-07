# Implementation Session — May 7, 2026

## Overview

Testbench session adding multiple hardware components and firmware features to the Dilder Hub. All changes in a single commit: `ff836b7`.

## Hardware Changes

### Power Wiring

- Waveshare display VCC moved from VSYS (pin 39) to 3V3(OUT) (pin 36) to free VSYS for TP4056 charger board
- TP4056 USB-C charger module wired: OUT+ to VSYS (pin 39), OUT- to GND (pin 38)
- Battery successfully reporting voltage and percentage through ADC3/GPIO 29

### Active Buzzer

- Replaced passive piezo (GP14+GP15 push-pull PWM) with active buzzer (GP14 only, GPIO on/off)
- Wiring: buzzer (+) to GP14 (pin 19), buzzer (-) to GND (pin 18)
- Old PWM code had inverted polarity on channel A causing the buzzer to scream continuously when "off" -- fixed by switching to simple GPIO driver

### MPU-6050 Accelerometer/Gyroscope

- GY-521 module wired via I2C0: SDA to GP0 (pin 1), SCL to GP1 (pin 2)
- VCC shared with Waveshare on 3V3(OUT) (pin 36), GND on pin 33
- AD0 floating (address 0x69) -- firmware auto-detects both 0x68 and 0x69
- Full wiring guide: `docs/mpu6050-wiring-guide.md`

## Firmware Changes

### Bug Fixes

- **cyw43_arch_gpio_get API** -- function takes 1 argument (returns bool), not 2 with output pointer
- **CYW43 init at boot** -- required even without WiFi because CYW43's SPI CS line shares GPIO 29 (VSYS sense). Uninitialized CYW43 pulls GPIO 29 low, causing ADC to read 0V for battery
- **WiFi disconnect** -- changed from `cyw43_arch_deinit()` to `cyw43_wifi_leave()` to keep CYW43 alive for battery sensing
- **VSYS reads** -- wrapped in `cyw43_thread_enter()`/`cyw43_thread_exit()` to prevent SPI bus interference during ADC sampling

### Active Buzzer Driver

- Replaced PWM piezo code with GPIO on/off for active buzzer
- `speaker_tone()` respects `sound_enabled` flag and `sound_vol` (LOW/MED/HIGH controls beep duration: 20/50/100ms)
- Volume clamps the on-time, preserves total duration for timing consistency

### Sound Patterns

- 6 named patterns: BEEP, CHIRP, SOS, DOORBELL, ALERT, HAPPY
- Defined as on_ms/off_ms pair arrays with 0 terminator
- `play_sound_pattern()` respects volume setting per-step
- Sound menu: LEFT/RIGHT cycles patterns, CENTER plays, plus SOUND ON/OFF and VOLUME controls

### WiFi Menu Overhaul

- **Network submenu** (STATE_NET_MENU): WIFI ON/OFF toggle, SCAN NETWORKS, STATUS, BACK
- **WiFi scanning** (STATE_NET_SCAN): async `cyw43_wifi_scan()` with callback, deduplicates by SSID, shows "SCANNING... FOUND: N" with 500ms refresh, scrollable results list with lock icon for encrypted networks
- **On-screen keyboard** (STATE_NET_KEYBOARD): 4x10 character grid + 5 special keys (SHIFT, SPC, DEL, DONE, CANCEL), joystick-navigated, shift toggles upper/lowercase, CAPS/LOW indicator
- **wifi_connect_to()**: new function accepting arbitrary SSID/password, auto-detects open vs WPA2. Original `wifi_connect()` is now a wrapper for hardcoded credentials
- **Connecting screen**: shows "CONNECTING TO [SSID]... PLEASE WAIT" during the blocking 15s connect call
- POLL_INPUT macro updated to call `cyw43_arch_poll()` during scans (`|| scan_in_progress`)

### MPU-6050 Driver

- I2C0 at 400kHz on GP0/GP1 with internal pull-ups
- Auto-detects address (probes 0x68 then 0x69)
- Burst read: 14 bytes from 0x3B for accel+temp+gyro in one transaction
- Error-checked I2C read/write functions
- Acceleration in g (+/-2g range, 16384 LSB/g), gyro in deg/s (+/-250, 131 LSB/(deg/s))
- Tilt angles via atan2, temperature from chip sensor
- Simple pedometer: step detected when acceleration magnitude crosses configurable threshold (default 1.3g) with hysteresis (0.3g deadband)

### Motion Menu (STATE_MOTION)

- Live accelerometer values (X/Y/Z in g)
- Step counter (pedometer)
- Tilt angles + chip temperature
- Reset pedometer
- Adjustable step threshold (0.8g-2.5g, cycles with CENTER or RIGHT)
- I2C bus scanner with device identification (MPU-6050, BME280, SSD1306, EEPROM)
- Gyro readout and magnitude display at bottom
- Scrolling menu (5 items visible)

### UI Improvements

- Input debounce reduced from 200ms to 5ms, poll interval from 20ms to 5ms (200Hz input checking)
- All menus now scroll when items exceed visible area (main menu, motion menu, scan results)
- Main menu supports 6 items: MOOD SELECT, NETWORK, SOUND, MOTION, DEVICE INFO, BACK

### Build Changes

- Added `hardware_i2c` to CMakeLists.txt link libraries
- Added `#include "hardware/i2c.h"` to main.c

## New Documentation

- `docs/mpu6050-wiring-guide.md` -- pin table, header map, I2C details, register reference
- `hardware-design/power-consumption-report.md` -- 4-scenario power budget, 8 reduction strategies, battery life projections, solar viability
- `docs/session-2026-05-07-implementation.md` -- this file

## Design Notes for Full Board

- TP4056 CHRG/STDBY pins should be wired to GPIOs (e.g., GP15/GP16) for USB-C charge detection. Not implemented on testbench (would require soldering). The CYW43 VBUS pin only detects the Pico's own USB port.
- See `memory/project_tp4056_charge_detect.md` for details.

## File Changes

| File | Change |
|------|--------|
| `dev-setup/dilder-hub/main.c` | +959/-125 lines -- all firmware features |
| `dev-setup/dilder-hub/CMakeLists.txt` | +1 line (hardware_i2c) |
| `docs/mpu6050-wiring-guide.md` | New -- wiring guide |
| `hardware-design/power-consumption-report.md` | New -- power analysis |
