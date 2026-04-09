# Wiring & Pinout

GPIO assignments and breadboard wiring for the Dilder test bench.

---

## Display Wiring (HAT)

The Waveshare 2.13" e-Paper HAT is a direct header attachment — it plugs onto the Pi Zero's 40-pin GPIO header with no additional wiring required. This is the advantage of the HAT form factor.

!!! tip "HAT = Header Attachment"
    Just align the HAT's 40-pin header with the Pi Zero's header and press down firmly. No jumper wires needed for the display.

### Display Pin Mapping

| E-Paper Pin | Function | BCM GPIO | Physical Pin |
|-------------|----------|----------|--------------|
| VCC | Power (3.3V) | 3.3V | Pin 1 |
| GND | Ground | GND | Pin 6 |
| DIN | SPI MOSI | GPIO 10 | Pin 19 |
| CLK | SPI Clock | GPIO 11 | Pin 23 |
| CS | Chip Select | GPIO 8 (CE0) | Pin 24 |
| DC | Data/Command | GPIO 25 | Pin 22 |
| RST | Reset | GPIO 17 | Pin 11 |
| BUSY | Busy status | GPIO 24 | Pin 18 |

---

## Button Wiring (Breadboard)

Five tactile buttons are wired to GPIO pins using the Pi's internal pull-up resistors. No external resistors needed.

**Wiring per button:**
- One leg connects to a GPIO pin
- Other leg connects to GND (shared ground rail)
- Pi software enables internal pull-up on the GPIO
- Button press pulls the line LOW → detected as pressed

### Button GPIO Assignments

| Button | BCM GPIO | Physical Pin | Suggested Cap Color |
|--------|----------|--------------|---------------------|
| Up | GPIO 5 | Pin 29 | White |
| Down | GPIO 6 | Pin 31 | White |
| Left | GPIO 13 | Pin 33 | White |
| Right | GPIO 19 | Pin 35 | White |
| Center / Select | GPIO 26 | Pin 37 | Red or Green |

!!! note "GPIO selection rationale"
    Buttons are assigned to GPIO 5, 6, 13, 19, and 26 because these do not conflict with SPI (GPIO 8, 10, 11), UART, I2C, or PWM pins. They're clean digital I/O pins on the lower half of the header.

---

## Full GPIO Pin Budget

| Function | GPIO Pins | Interface |
|----------|-----------|-----------|
| E-ink display | GPIO 8, 10, 11, 17, 24, 25 | SPI |
| Button Up | GPIO 5 | Digital input |
| Button Down | GPIO 6 | Digital input |
| Button Left | GPIO 13 | Digital input |
| Button Right | GPIO 19 | Digital input |
| Button Center | GPIO 26 | Digital input |
| Piezo buzzer (future) | GPIO 12 or 18 | PWM |
| **Pins used** | **12 total** | |
| **Pins remaining** | **14+ free** | |

---

## Breadboard Layout

```
Pi Zero WH (via ribbon cable / T-cobbler)
      │
      ├── 3.3V ──────────── HAT VCC
      ├── GND  ──────────── HAT GND
      │                     Shared breadboard GND rail
      ├── GPIO 10 (MOSI) ── HAT DIN
      ├── GPIO 11 (SCLK) ── HAT CLK
      ├── GPIO 8  (CE0)  ── HAT CS
      ├── GPIO 25        ── HAT DC
      ├── GPIO 17        ── HAT RST
      ├── GPIO 24        ── HAT BUSY
      │
      ├── GPIO 5  ─── [BTN UP]     ─── GND
      ├── GPIO 6  ─── [BTN DOWN]   ─── GND
      ├── GPIO 13 ─── [BTN LEFT]   ─── GND
      ├── GPIO 19 ─── [BTN RIGHT]  ─── GND
      └── GPIO 26 ─── [BTN CENTER] ─── GND
```

!!! info "HAT vs breadboard"
    The display HAT plugs directly onto the Pi and does not use the breadboard. The breadboard is only for the five buttons. Use M-F jumper wires to connect the Pi's GPIO pins (via T-cobbler or directly) to the breadboard button rows.

---

## Pi Zero 40-Pin Header Reference

```
       3V3  (1) (2)  5V
     GPIO2  (3) (4)  5V
     GPIO3  (5) (6)  GND
     GPIO4  (7) (8)  GPIO14
       GND  (9) (10) GPIO15
    GPIO17 (11) (12) GPIO18    ← RST (HAT)
    GPIO27 (13) (14) GND
    GPIO22 (15) (16) GPIO23
       3V3 (17) (18) GPIO24    ← BUSY (HAT)
    GPIO10 (19) (20) GND       ← MOSI/DIN (HAT)
     GPIO9 (21) (22) GPIO25    ← DC (HAT)
    GPIO11 (23) (24) GPIO8     ← SCLK (HAT) / CS (HAT)
       GND (25) (26) GPIO7
     GPIO0 (27) (28) GPIO1
     GPIO5 (29) (30) GND       ← BTN UP
     GPIO6 (31) (32) GPIO12
    GPIO13 (33) (34) GND       ← BTN LEFT
    GPIO19 (35) (36) GPIO16    ← BTN RIGHT
    GPIO26 (37) (38) GPIO20    ← BTN CENTER
       GND (39) (40) GPIO21
                                 BTN DOWN = GPIO6 (pin 31)
```
