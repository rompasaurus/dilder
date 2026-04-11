# Waveshare 2.13" e-Paper HAT — Official Reference

Source: [waveshare.com/wiki/2.13inch_e-Paper_HAT](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT)

---

## Display Specifications

| Spec | Value |
|------|-------|
| Size | 2.13 inches |
| Resolution | 250 × 122 pixels |
| Active area | 48.55 × 23.71mm |
| Dot pitch | 0.194 × 0.194mm |
| Colors | Black and white |
| Viewing angle | > 170° |
| Operating voltage | 3.3V / 5V (onboard level converter) |
| Active power | 26.4mW (during refresh) |
| Standby current | < 0.01µA |
| Full refresh time | ~2 seconds |
| Partial refresh time | ~0.3 seconds |
| Min refresh interval | 180 seconds recommended |
| Interface | SPI 4-wire, Mode 0 |
| Connector | 40-pin GPIO HAT or 8-pin FPC (2.54mm) |

---

## Pin Mapping

### Connecting to Pico W (jumper wires)

The Waveshare HAT is designed for the Pi Zero's 40-pin header, but only 8 pins are actually used by the display. Connect these via jumper wires to the Pico W.

| e-Paper Pin | Function | Pico W GPIO | Pico W Pin # | Direction |
|---|---|---|---|---|
| VCC | Power 3.3V | 3V3(OUT) | 36 | → display |
| GND | Ground | GND | 38 | → display |
| DIN | SPI MOSI — data in | GP11 (SPI1 TX) | 15 | → display |
| CLK | SPI clock | GP10 (SPI1 SCK) | 14 | → display |
| CS | Chip select (active LOW) | GP9 (SPI1 CSn) | 12 | → display |
| DC | Data/Command select | GP8 | 11 | → display |
| RST | Reset (active LOW) | GP12 | 16 | → display |
| BUSY | Busy flag (HIGH = busy) | GP13 | 17 | ← display |

!!! tip "Where to connect on the HAT"
    The HAT has an 8-pin 2.54mm header on the edge labeled VCC, GND, DIN, CLK, CS, DC, RST, BUSY. Use female-to-male jumper wires from these pins to the Pico W breadboard.

### Connecting to Pi Zero (HAT — future)

When migrating to the Pi Zero in Phase 5, the HAT plugs directly onto the 40-pin header. No jumper wires needed.

| e-Paper Pin | Function | BCM GPIO | Physical Pin |
|---|---|---|---|
| VCC | Power 3.3V | 3.3V | 1 |
| GND | Ground | GND | 6 |
| DIN | SPI MOSI — data in | GPIO 10 | 19 |
| CLK | SPI clock | GPIO 11 | 23 |
| CS | Chip select (active LOW) | GPIO 8 (CE0) | 24 |
| DC | Data/Command select | GPIO 25 | 22 |
| RST | Reset (active LOW) | GPIO 17 | 11 |
| BUSY | Busy flag (HIGH = busy) | GPIO 24 | 18 |

### Signal Descriptions

| Signal | Behaviour |
|--------|-----------|
| **CS** | Pull LOW to address the display; HIGH to deselect |
| **DC** | HIGH = send pixel data; LOW = send command byte |
| **RST** | Normally HIGH; pulse LOW to hardware-reset the display |
| **BUSY** | HIGH while display is refreshing — poll before sending commands |

---

## SPI Protocol Details

| Parameter | Value |
|-----------|-------|
| Mode | Mode 0 (CPOL=0, CPHA=0) |
| Bit order | MSB first |
| Clock speed | 1–10 MHz typical |
| Bus | SPI1 on Pico W (`GP10/GP11/GP9`); SPI0 CE0 on Pi Zero (`/dev/spidev0.0`) |

### Typical Command Sequence

```
CS LOW
  DC LOW  → send 1-byte command
  DC HIGH → send parameter bytes (if any)
  wait for BUSY LOW
CS HIGH
```

### Typical Data (Pixel) Write

```
CS LOW
  DC HIGH → send pixel data bytes
  wait for BUSY LOW
CS HIGH
```

---

## Refresh Rules

!!! danger "Follow these or risk permanent damage"
    E-ink displays are not like LCDs. Violating refresh rules causes ghosting artifacts and can permanently damage pixels.

| Rule | Requirement |
|------|-------------|
| Minimum interval | ≥ 180 seconds between operations |
| Partial refresh limit | Max 5 consecutive partial refreshes before a full refresh |
| Full refresh procedure | White → refresh → black → refresh → content → refresh |

### Full Refresh Cycle (clears ghosting)

```python
epd.init()
epd.Clear()          # writes white, then refreshes
# wait 2 seconds
# now send your content image
epd.display(epd.getbuffer(image))
epd.sleep()
```

### Partial Refresh (fast updates, no flicker)

```python
epd.init_part()
epd.displayPartial(epd.getbuffer(image))
# After 5 partial updates — do a full refresh to prevent ghosting
```

---

## Version Comparison: V3 vs V4

| Feature | V3 | V4 |
|---------|----|----|
| Resolution | 250 × 122 | 250 × 122 |
| GPIO pinout | Standard | Identical to V3 |
| SPI interface | Mode 0 | Mode 0 |
| Driver IC | SSD1680 | SSD1680Z8 |
| MicroPython driver | `epd2in13_V3.py` | `epd2in13_V4.py` |
| CPython driver (Pi) | `epd2in13_V3.py` | `epd2in13_V4.py` |
| Fast refresh | Limited | Enhanced |
| Backward compatible | — | Yes — V4 is a drop-in replacement |

!!! warning "Use the correct driver file"
    V3 and V4 require different driver files. Using the wrong one will either fail silently or produce garbage output. Check your PCB silkscreen to confirm your version.

    **This project uses V3** (SSD1680 driver, confirmed on hand).

---

## Identifying Your Version

Look at the PCB silkscreen on the back of the HAT:

- **V3** — printed as "2.13inch e-Paper HAT V3" or "2.13inch e-Paper HAT (C) V3"
- **V4** — printed as "2.13inch e-Paper HAT V4"

---

## MicroPython Library Setup (Pico W)

```bash
# Clone the Waveshare Pico e-Paper library
git clone https://github.com/waveshare/Pico_ePaper_Code.git
```

The MicroPython driver files are in `Pico_ePaper_Code/python/lib/`. Upload these to your Pico W:

- `epd2in13_V3.py` — display driver
- `epdconfig.py` — SPI/GPIO configuration

### Minimal MicroPython Example (V3)

```python
from machine import Pin, SPI
import framebuf
import utime

# Import the Waveshare driver (upload to Pico W first)
from epd2in13_V3 import EPD_2in13_V3

epd = EPD_2in13_V3()
epd.init()
epd.Clear()

# Create a framebuffer — 250×122, 1-bit mono
buf = bytearray(epd.height * epd.width // 8)
fb = framebuf.FrameBuffer(buf, epd.height, epd.width, framebuf.MONO_HLSB)

# White background, black text
fb.fill(0xff)
fb.text("Hello, Dilder!", 10, 10, 0x00)

epd.display(buf)
utime.sleep(2)
epd.sleep()
```

---

## CPython Library Setup (Pi Zero — future)

```bash
# Clone the Waveshare library
git clone https://github.com/waveshare/e-Paper.git

# Install Python library
cd e-Paper/RaspberryPi_JetsonNano/python
pip install .

# Verify driver files exist
ls lib/waveshare_epd/epd2in13_V3.py
```

---

## GPIO Configuration in MicroPython

```python
# Default pin assignments for Pico W (Waveshare convention)
RST_PIN  = 12   # GP12, Pico pin 16
DC_PIN   = 8    # GP8, Pico pin 11
CS_PIN   = 9    # GP9 (SPI1 CSn), Pico pin 12
BUSY_PIN = 13   # GP13, Pico pin 17

# SPI1 configuration
SCK_PIN  = 10   # GP10 (SPI1 SCK), Pico pin 14
MOSI_PIN = 11   # GP11 (SPI1 TX), Pico pin 15

# SPI setup in MicroPython
spi = SPI(1, baudrate=4_000_000, polarity=0, phase=0,
          sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN))
```

---

## Safety Notes

| Risk | Rule |
|------|------|
| GPIO overvoltage | All signals must be 3.3V — the Pico W is 3.3V logic, matching the display |
| FPC cable | Fragile — never bend the flat cable vertically or crease it |
| Hot-plugging | Always disconnect power before changing wiring |
| Refresh rate | Never refresh more often than every 3 minutes under sustained use |

---

## Official Links

| Resource | URL |
|----------|-----|
| Waveshare Wiki | [waveshare.com/wiki/2.13inch_e-Paper_HAT](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT) |
| GitHub library (Pi) | [github.com/waveshare/e-Paper](https://github.com/waveshare/e-Paper) |
| GitHub library (Pico) | [github.com/waveshare/Pico_ePaper_Code](https://github.com/waveshare/Pico_ePaper_Code) |
| V3 spec sheet (PDF) | [files.waveshare.com — V3 spec](https://files.waveshare.com/upload/4/4e/2.13inch_e-Paper_V3_Specification.pdf) |
| V4 spec sheet (PDF) | [files.waveshare.com — V4 spec](https://files.waveshare.com/upload/4/4e/2.13inch_e-Paper_V4_Specification.pdf) |
| SSD1680 datasheet | [orientdisplay.com — SSD1680](https://www.orientdisplay.com/wp-content/uploads/2022/08/SSD1680_v0.14.pdf) |
