# Raspberry Pi Pico W — Official Reference

Source: [raspberrypi.com/documentation/microcontrollers/pico-series.html](https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html)

---

## Hardware Specifications

| Spec | Value |
|------|-------|
| Chip | RP2040 |
| CPU | Dual-core ARM Cortex-M0+ @ 133MHz |
| RAM | 264KB SRAM |
| Flash | 2MB onboard QSPI |
| Wi-Fi | 802.11n 2.4GHz (Infineon CYW43439) |
| Bluetooth | BLE 5.2 |
| USB | Micro-USB 1.1 (device and host) |
| GPIO | 26 multi-function pins (GP0–GP28, not all exposed) |
| ADC | 3 external channels + 1 internal (12-bit, 500ksps) |
| SPI | 2× SPI controllers (SPI0, SPI1) |
| I²C | 2× I²C controllers |
| UART | 2× UART |
| PWM | 16 channels (8 slices × 2 outputs) |
| Dimensions | 51 × 21 × 3.9mm |
| Operating temp | -20°C to +85°C |
| Power input | 1.8V–5.5V via VSYS, or 5V via micro-USB |

---

## Pinout Overview

!!! warning "3.3V logic"
    GPIO pins are **3.3V logic**. They are NOT 5V tolerant. Applying 5V to any GPIO pin will damage the RP2040.

### Pico W Pin Map (40-pin header)

| Pin # | GPIO | Function | Notes |
|-------|------|----------|-------|
| 1 | GP0 | SPI0 RX / I2C0 SDA / UART0 TX | |
| 2 | GP1 | SPI0 CSn / I2C0 SCL / UART0 RX | |
| 3 | — | GND | |
| 4 | GP2 | SPI0 SCK / I2C1 SDA | **Button UP** |
| 5 | GP3 | SPI0 TX / I2C1 SCL | **Button DOWN** |
| 6 | GP4 | SPI0 RX / I2C0 SDA / UART1 TX | **Button LEFT** |
| 7 | GP5 | SPI0 CSn / I2C0 SCL / UART1 RX | **Button RIGHT** |
| 8 | — | GND | |
| 9 | GP6 | SPI0 SCK / I2C1 SDA | **Button CENTER** |
| 10 | GP7 | SPI0 TX / I2C1 SCL | |
| 11 | GP8 | SPI1 RX / I2C0 SDA | **e-Paper DC** |
| 12 | GP9 | SPI1 CSn / I2C0 SCL | **e-Paper CS** |
| 13 | — | GND | |
| 14 | GP10 | SPI1 SCK / I2C1 SDA | **e-Paper CLK** |
| 15 | GP11 | SPI1 TX / I2C1 SCL | **e-Paper DIN** |
| 16 | GP12 | SPI1 RX / I2C0 SDA | **e-Paper RST** |
| 17 | GP13 | SPI1 CSn / I2C0 SCL | **e-Paper BUSY** |
| 18 | — | GND | |
| 19 | GP14 | SPI1 SCK / I2C1 SDA | |
| 20 | GP15 | SPI1 TX / I2C1 SCL | Future: piezo buzzer (PWM) |
| 21 | GP16 | SPI0 RX / I2C0 SDA | |
| 22 | GP17 | SPI0 CSn / I2C0 SCL | |
| 23 | — | GND | |
| 24 | GP18 | SPI0 SCK / I2C1 SDA | |
| 25 | GP19 | SPI0 TX / I2C1 SCL | |
| 26 | GP20 | SPI0 RX / I2C0 SDA | |
| 27 | GP21 | SPI0 CSn / I2C0 SCL | |
| 28 | — | GND | |
| 29 | GP22 | GPIO | |
| 30 | — | RUN | Reset pin (pull LOW to reset) |
| 31 | GP26 | ADC0 / GPIO | |
| 32 | GP27 | ADC1 / GPIO | |
| 33 | — | AGND | Analog ground reference |
| 34 | GP28 | ADC2 / GPIO | |
| 35 | — | ADC_VREF | ADC voltage reference |
| 36 | — | 3V3(OUT) | **3.3V regulated output** (300mA) |
| 37 | — | 3V3_EN | Pull LOW to disable 3.3V regulator |
| 38 | — | GND | |
| 39 | — | VSYS | 1.8–5.5V system input |
| 40 | — | VBUS | 5V from USB (when connected) |

Pins marked **bold** are used by the Dilder hardware — see [Wiring & Pinout](../hardware/wiring-pinout.md) for the full assignment table.

---

## GPIO Electrical Limits

| Parameter | Value |
|-----------|-------|
| Logic voltage | 3.3V max |
| HIGH input threshold | ≥ 2.0V |
| LOW input threshold | ≤ 0.8V |
| Max current per GPIO pin | 12mA (recommended), 16mA absolute max |
| Total GPIO current | ~50mA recommended |
| 3V3(OUT) rail current | 300mA |
| Internal pull resistors | ~50–80kΩ (software configurable up/down) |

---

## Protocol Pin Assignments

### SPI1 (used by the e-ink display)

| Signal | Pico W GPIO | Pin # |
|--------|-------------|-------|
| SCK | GP10 | 14 |
| TX (MOSI) | GP11 | 15 |
| RX (MISO) | GP12 | 16 |
| CSn | GP9 | 12 |

SPI mode for the Waveshare display: **Mode 0** (CPOL=0, CPHA=0), MSB-first.

!!! note "SPI naming"
    The RP2040 uses TX/RX instead of MOSI/MISO. For the e-ink display: **TX = MOSI** (data to display), RX is unused (display is write-only).

### SPI0 (free for future use)

| Signal | Pico W GPIO | Pin # |
|--------|-------------|-------|
| SCK | GP18 | 24 |
| TX (MOSI) | GP19 | 25 |
| RX (MISO) | GP16 | 21 |
| CSn | GP17 | 22 |

### I²C0

| Signal | Pico W GPIO | Pin # |
|--------|-------------|-------|
| SDA | GP0 | 1 |
| SCL | GP1 | 2 |

### UART0

| Signal | Pico W GPIO | Pin # |
|--------|-------------|-------|
| TX | GP0 | 1 |
| RX | GP1 | 2 |

---

## Power Options

| Source | Pin | Notes |
|--------|-----|-------|
| USB | VBUS (pin 40) | 5V from USB cable — simplest for development |
| External | VSYS (pin 39) | 1.8–5.5V — use for battery power via a boost/buck regulator |
| 3.3V out | 3V3(OUT) (pin 36) | Regulated 3.3V output for peripherals (300mA max) |

!!! tip "BOOTSEL button"
    Hold BOOTSEL while plugging in USB to enter USB mass-storage mode for firmware flashing. The board appears as a drive — drag and drop the `.uf2` firmware file.

---

## MicroPython Firmware

```bash
# Download the latest MicroPython UF2 for Pico W
# https://micropython.org/download/RPI_PICO_W/

# Flash procedure:
# 1. Hold BOOTSEL button on Pico W
# 2. Plug in USB cable (while holding BOOTSEL)
# 3. Release BOOTSEL — Pico appears as USB drive "RPI-RP2"
# 4. Drag the .uf2 file onto the drive
# 5. Pico reboots automatically into MicroPython
```

Verify via serial REPL:

```bash
# Linux
screen /dev/ttyACM0 115200
# or
minicom -D /dev/ttyACM0 -b 115200
```

You should see the MicroPython `>>>` prompt.

---

## Key Differences: Pico W vs Pi Zero

| Feature | Pico W | Pi Zero WH |
|---------|--------|-----------|
| CPU | Dual Cortex-M0+ @ 133MHz | ARM1176 @ 1GHz |
| RAM | 264KB | 512MB |
| Storage | 2MB flash | Micro SD (GB+) |
| OS | Bare metal / MicroPython | Linux (Raspberry Pi OS) |
| Boot time | Instant (~1 second) | 30–90 seconds |
| Power draw | ~40mA active | ~120mA idle, ~200mA+ active |
| USB | Micro-USB (device) | Micro-USB OTG + power |
| GPIO | 26 pins | 26 usable GPIO (40-pin header) |
| Price | ~$6 | ~$15 |
| Filesystem | Flash only (2MB) | Full Linux filesystem |
| SSH | No | Yes |
| HAT support | No (jumper wires) | Yes (40-pin header) |

---

## Official Links

| Resource | URL |
|----------|-----|
| Pico W product page | [raspberrypi.com/products/raspberry-pi-pico](https://www.raspberrypi.com/products/raspberry-pi-pico/) |
| Pico W datasheet (PDF) | [datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf](https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf) |
| RP2040 datasheet (PDF) | [datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf) |
| Pinout diagram (PDF) | [datasheets.raspberrypi.com/picow/PicoW-A4-Pinout.pdf](https://datasheets.raspberrypi.com/picow/PicoW-A4-Pinout.pdf) |
| MicroPython downloads | [micropython.org/download/RPI_PICO_W](https://micropython.org/download/RPI_PICO_W/) |
| Pico SDK (C/C++) | [github.com/raspberrypi/pico-sdk](https://github.com/raspberrypi/pico-sdk) |
| Getting Started guide | [datasheets.raspberrypi.com/pico/getting-started-with-pico.pdf](https://datasheets.raspberrypi.com/pico/getting-started-with-pico.pdf) |
