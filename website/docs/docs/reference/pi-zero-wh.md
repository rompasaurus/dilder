# Raspberry Pi Zero WH — Official Reference

!!! note "Future hardware"
    The Pi Zero WH is planned for Phase 5 (migration from Pico W). This reference is kept for future use. For the current development board, see [Pico W Reference](pico-w.md).

Source: [raspberrypi.com/documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)

---

## Hardware Specifications

| Spec | Value |
|------|-------|
| SoC | BCM2835 |
| CPU | ARM1176JZF-S, 1GHz single-core |
| RAM | 512MB LPDDR2 SDRAM |
| Wi-Fi | 802.11 b/g/n 2.4GHz |
| Bluetooth | 4.2 + BLE |
| USB | Micro-USB OTG |
| Video | Mini HDMI |
| Camera | CSI connector (flex cable) |
| Storage | Micro SD |
| GPIO | 2×20 40-pin header (pre-soldered on WH) |
| Dimensions | 65 × 30 × 5mm |
| Operating temp | 0°C to 70°C |
| Recommended power | 5V DC, 2.5A |

---

## Complete 40-Pin GPIO Pinout

!!! warning "3.3V only"
    GPIO pins are **3.3V logic**. They are NOT 5V tolerant. Applying 5V to any GPIO pin will permanently damage the SoC.

| Physical Pin | BCM GPIO | Primary Function | Notes |
|---|---|---|---|
| 1 | — | 3.3V power | ~500mA total rail |
| 2 | — | 5V power | Direct from USB |
| 3 | GPIO 2 | I²C SDA1 | 1.8kΩ pull-up onboard |
| 4 | — | 5V power | |
| 5 | GPIO 3 | I²C SCL1 | 1.8kΩ pull-up onboard |
| 6 | — | GND | |
| 7 | GPIO 4 | GPCLK0 | General-purpose clock |
| 8 | GPIO 14 | UART TXD0 | Serial transmit |
| 9 | — | GND | |
| 10 | GPIO 15 | UART RXD0 | Serial receive |
| 11 | GPIO 17 | GPIO | **e-Paper RST** |
| 12 | GPIO 18 | PWM0 / PCM CLK | Hardware PWM |
| 13 | GPIO 27 | GPIO | |
| 14 | — | GND | |
| 15 | GPIO 22 | GPIO | |
| 16 | GPIO 23 | GPIO | |
| 17 | — | 3.3V power | Second 3.3V source |
| 18 | GPIO 24 | GPIO | **e-Paper BUSY** |
| 19 | GPIO 10 | SPI0 MOSI | **e-Paper DIN** |
| 20 | — | GND | |
| 21 | GPIO 9 | SPI0 MISO | Unused by e-paper |
| 22 | GPIO 25 | GPIO | **e-Paper DC** |
| 23 | GPIO 11 | SPI0 SCLK | **e-Paper CLK** |
| 24 | GPIO 8 | SPI0 CE0 | **e-Paper CS** |
| 25 | — | GND | |
| 26 | GPIO 7 | SPI0 CE1 | |
| 27 | GPIO 0 | ID EEPROM SDA | HAT ID — reserved |
| 28 | GPIO 1 | ID EEPROM SCL | HAT ID — reserved |
| 29 | GPIO 5 | GPIO | **Button UP** |
| 30 | — | GND | |
| 31 | GPIO 6 | GPIO | **Button DOWN** |
| 32 | GPIO 12 | PWM0 | |
| 33 | GPIO 13 | PWM1 | **Button LEFT** |
| 34 | — | GND | |
| 35 | GPIO 19 | PCM FS / PWM | **Button RIGHT** |
| 36 | GPIO 16 | GPIO | |
| 37 | GPIO 26 | GPIO | **Button CENTER** |
| 38 | GPIO 20 | PCM DIN | |
| 39 | — | GND | |
| 40 | GPIO 21 | PCM DOUT | |

Pins marked **bold** are used by the Dilder hardware — see [Wiring & Pinout](../hardware/wiring-pinout.md) for the full assignment table.

---

## GPIO Electrical Limits

| Parameter | Value |
|-----------|-------|
| Logic voltage | 3.3V max |
| HIGH input threshold | ≥ 1.8V |
| LOW input threshold | ≤ 0.8V |
| Max current per GPIO pin | 16mA |
| Max total GPIO current | 50mA |
| 3.3V rail current | ~500mA |
| Internal pull resistors | ~50kΩ (software configurable) |

---

## Protocol Pin Assignments

### SPI (used by the e-ink display)

| Signal | BCM GPIO | Physical Pin |
|--------|----------|-------------|
| MOSI | GPIO 10 | 19 |
| MISO | GPIO 9 | 21 |
| SCLK | GPIO 11 | 23 |
| CE0 (CS) | GPIO 8 | 24 |
| CE1 | GPIO 7 | 26 |

SPI mode for the Waveshare display: **Mode 0** (CPOL=0, CPHA=0), MSB-first.

### I²C

| Signal | BCM GPIO | Physical Pin |
|--------|----------|-------------|
| SDA1 | GPIO 2 | 3 |
| SCL1 | GPIO 3 | 5 |

### UART

| Signal | BCM GPIO | Physical Pin |
|--------|----------|-------------|
| TXD0 | GPIO 14 | 8 |
| RXD0 | GPIO 15 | 10 |

### Hardware PWM

| Signal | BCM GPIO | Physical Pin |
|--------|----------|-------------|
| PWM0 | GPIO 12 | 32 |
| PWM1 | GPIO 13 | 33 |
| PWM0 (alt) | GPIO 18 | 12 |
| PWM1 (alt) | GPIO 19 | 35 |

---

## GPIO Numbering — BCM vs Physical

!!! danger "Always use BCM numbers in code"
    The Waveshare library and RPi.GPIO default to **BCM numbering** — the number after "GPIO" (e.g. GPIO 17 = BCM 17). Physical pin numbers are the 1–40 positions on the header. These are different. Using physical numbering by mistake will connect to the wrong pin.

    ```python
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)   # use BCM — always set this
    GPIO.setup(17, GPIO.OUT) # GPIO 17 = physical pin 11
    ```

---

## Official Links

| Resource | URL |
|----------|-----|
| Pi Zero W product page | [raspberrypi.com/products/raspberry-pi-zero-w](https://www.raspberrypi.com/products/raspberry-pi-zero-w/) |
| Hardware documentation | [raspberrypi.com/documentation/computers/raspberry-pi.html](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html) |
| GPIO documentation | [raspberrypi.com/documentation/computers/raspberry-pi.html#gpio](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio) |
| Schematics (PDF) | [datasheets.raspberrypi.com/rpizero](https://datasheets.raspberrypi.com/rpizero/raspberry-pi-zero-w-reduced-schematics.pdf) |
| Interactive pinout | [pinout.xyz](https://pinout.xyz) |
