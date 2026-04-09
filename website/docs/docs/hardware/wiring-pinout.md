# Wiring & Pinout

GPIO assignments and breadboard wiring for the Dilder test bench.

Full official hardware reference docs:

- [Raspberry Pi Zero WH reference](../reference/pi-zero-wh.md)
- [Waveshare 2.13" e-Paper HAT reference](../reference/waveshare-eink.md)

---

## Display Wiring (HAT — no jumpers needed)

The Waveshare 2.13" e-Paper HAT plugs directly onto the Pi Zero's 40-pin GPIO header. No jumper wires are needed for the display.

!!! tip "HAT = Header Attachment"
    Align pin 1 on the HAT with pin 1 on the Pi (the corner nearest the SD card slot), press down firmly until the HAT sits flush. Always power off the Pi before attaching or removing it.

### Display Pin Mapping

Sourced from the [Waveshare official reference](../reference/waveshare-eink.md).

| e-Paper Signal | Function | BCM GPIO | Physical Pin | Direction |
|---|---|---|---|---|
| VCC | 3.3V power | 3.3V rail | 1 | → display |
| GND | Ground | GND | 6 | → display |
| DIN | SPI MOSI — pixel data | GPIO 10 | 19 | → display |
| CLK | SPI clock | GPIO 11 | 23 | → display |
| CS | Chip select (active LOW) | GPIO 8 (CE0) | 24 | → display |
| DC | Data / command select | GPIO 25 | 22 | → display |
| RST | Reset (active LOW) | GPIO 17 | 11 | → display |
| BUSY | Busy flag (HIGH = refreshing) | GPIO 24 | 18 | ← display |

#### Signal Quick Reference

| Signal | When HIGH | When LOW |
|--------|-----------|----------|
| CS | Display deselected | **Display active** |
| DC | Sending pixel data | Sending command byte |
| RST | Normal operation | **Hardware reset** |
| BUSY | **Display refreshing — wait** | Ready for commands |

---

## Button Wiring (Breadboard)

Five 6×6mm tactile buttons wired to GPIO pins using the Pi's internal pull-up resistors. No external resistors needed.

**Per-button wiring:**
```
Pi GPIO pin ──── button leg A
                 button leg B ──── GND rail
```

When the button is pressed it pulls the GPIO line LOW → software reads as pressed.

### Button GPIO Assignments

Sourced from the [Pi Zero WH GPIO reference](../reference/pi-zero-wh.md) — pins chosen to avoid SPI, I²C, UART, and PWM conflicts.

| Button | BCM GPIO | Physical Pin | Internal pull-up |
|--------|----------|-------------|-----------------|
| Up | GPIO 5 | 29 | Enabled in software |
| Down | GPIO 6 | 31 | Enabled in software |
| Left | GPIO 13 | 33 | Enabled in software |
| Right | GPIO 19 | 35 | Enabled in software |
| Center / Select | GPIO 26 | 37 | Enabled in software |

```python
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

BUTTONS = {
    'up':     5,
    'down':   6,
    'left':   13,
    'right':  19,
    'center': 26,
}

for pin in BUTTONS.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
```

---

## Full GPIO Pin Budget

| Function | BCM GPIO | Physical Pin | Interface |
|----------|----------|-------------|-----------|
| e-ink VCC | 3.3V | 1 | Power |
| e-ink GND | GND | 6 | Ground |
| e-ink DIN | GPIO 10 | 19 | SPI MOSI |
| e-ink CLK | GPIO 11 | 23 | SPI SCLK |
| e-ink CS | GPIO 8 | 24 | SPI CE0 |
| e-ink DC | GPIO 25 | 22 | Digital out |
| e-ink RST | GPIO 17 | 11 | Digital out |
| e-ink BUSY | GPIO 24 | 18 | Digital in |
| Button UP | GPIO 5 | 29 | Digital in |
| Button DOWN | GPIO 6 | 31 | Digital in |
| Button LEFT | GPIO 13 | 33 | Digital in |
| Button RIGHT | GPIO 19 | 35 | Digital in |
| Button CENTER | GPIO 26 | 37 | Digital in |
| Piezo buzzer (future) | GPIO 12 or 18 | 32 / 12 | PWM |
| **Pins used** | **13** | | |
| **Pins free** | **13+ general GPIO remaining** | | |

---

## Complete 40-Pin Header Map

Pins used by this project are highlighted. Full electrical specs in the [Pi Zero WH reference](../reference/pi-zero-wh.md).

```
       3V3  [ 1] [ 2]  5V
     GPIO2  [ 3] [ 4]  5V
     GPIO3  [ 5] [ 6]  GND
     GPIO4  [ 7] [ 8]  GPIO14
       GND  [ 9] [10]  GPIO15
▶  GPIO17  [11] [12]  GPIO18      RST  (e-ink)
    GPIO27  [13] [14]  GND
    GPIO22  [15] [16]  GPIO23
       3V3  [17] [18]  GPIO24 ◀   BUSY (e-ink)
▶  GPIO10  [19] [20]  GND         DIN  (e-ink)
     GPIO9  [21] [22]  GPIO25 ▶   DC   (e-ink)
▶  GPIO11  [23] [24]  GPIO8  ▶   CLK / CS (e-ink)
       GND  [25] [26]  GPIO7
     GPIO0  [27] [28]  GPIO1
▶   GPIO5  [29] [30]  GND         UP   (button)
▶   GPIO6  [31] [32]  GPIO12
▶  GPIO13  [33] [34]  GND         LEFT (button)
▶  GPIO19  [35] [36]  GPIO16      RIGHT (button)
▶  GPIO26  [37] [38]  GPIO20      CENTER (button)
       GND  [39] [40]  GPIO21
                                   DOWN = GPIO6 (pin 31)
▶ = used by Dilder
```

---

## Wiring Diagram (Text)

```
Pi Zero WH
│
├─ Pin 1  (3.3V) ──────────────── HAT VCC
├─ Pin 6  (GND)  ──────────────── HAT GND ── breadboard GND rail
├─ Pin 19 (GPIO10 / MOSI) ─────── HAT DIN
├─ Pin 23 (GPIO11 / SCLK) ─────── HAT CLK
├─ Pin 24 (GPIO8  / CE0)  ─────── HAT CS
├─ Pin 22 (GPIO25) ────────────── HAT DC
├─ Pin 11 (GPIO17) ────────────── HAT RST
├─ Pin 18 (GPIO24) ────────────── HAT BUSY
│
├─ Pin 29 (GPIO5)  ─── [BTN UP]     ─── GND
├─ Pin 31 (GPIO6)  ─── [BTN DOWN]   ─── GND
├─ Pin 33 (GPIO13) ─── [BTN LEFT]   ─── GND
├─ Pin 35 (GPIO19) ─── [BTN RIGHT]  ─── GND
└─ Pin 37 (GPIO26) ─── [BTN CENTER] ─── GND
```

---

## SPI Configuration

The e-ink display requires SPI to be enabled before use. See [Pi Zero Setup](../setup/pi-zero-setup.md) for instructions.

| SPI Parameter | Value |
|---------------|-------|
| Bus | SPI0 (`/dev/spidev0.0`) |
| Mode | Mode 0 (CPOL=0, CPHA=0) |
| Bit order | MSB first |
| Clock speed | 4 MHz (typical) |
| CS signal | Active LOW |

Verify SPI is active after enabling:
```bash
ls /dev/spi*
# Expected: /dev/spidev0.0   /dev/spidev0.1
```

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Display shows nothing | SPI enabled? Run `ls /dev/spi*` |
| Garbage output | Wrong driver version (V3 vs V4) — check PCB silkscreen |
| Permission error on `/dev/spidev` | Add user to `spi` group: `sudo usermod -aG spi,gpio pi` |
| BUSY pin always HIGH | Display stuck in refresh — power cycle and run `epd.Clear()` |
| Button reads always HIGH | `GPIO.PUD_UP` not set, or button not connected to GND |
| Button reads always LOW | Short to ground — check breadboard wiring |
