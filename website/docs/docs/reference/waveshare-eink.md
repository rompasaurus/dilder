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

## HAT Pin Mapping

### GPIO Connection Table

| e-Paper Pin | Function | BCM GPIO | Physical Pin | Direction |
|---|---|---|---|---|
| VCC | Power 3.3V | 3.3V | 1 | In |
| GND | Ground | GND | 6 | In |
| DIN | SPI MOSI — data in | GPIO 10 | 19 | In |
| CLK | SPI clock | GPIO 11 | 23 | In |
| CS | Chip select (active LOW) | GPIO 8 (CE0) | 24 | In |
| DC | Data/Command select | GPIO 25 | 22 | In |
| RST | Reset (active LOW) | GPIO 17 | 11 | In |
| BUSY | Busy flag (HIGH = busy) | GPIO 24 | 18 | Out |

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
| Bus | SPI Bus 0, CE0 (`/dev/spidev0.0`) |

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
epd.init(epd.PART_UPDATE)
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
| Driver file | `epd2in13_V3.py` | `epd2in13_V4.py` |
| Fast refresh | Limited | Enhanced |
| Backward compatible | — | Yes — V4 is a drop-in replacement |

!!! warning "Use the correct driver file"
    V3 and V4 require different Python driver files. Using the wrong one will either fail silently or produce garbage output. Check your PCB silkscreen to confirm your version.

---

## Identifying Your Version

Look at the PCB silkscreen on the back of the HAT:

- **V3** — printed as "2.13inch e-Paper HAT V3" or "2.13inch e-Paper HAT (C) V3"
- **V4** — printed as "2.13inch e-Paper HAT V4"

If ordering new: V4 is current. The product linked in the [materials list](../hardware/materials-list.md) (B07Q5PZMGT) ships V3 or V4 depending on stock — confirm on arrival.

---

## Python Library Setup

```bash
# Clone the Waveshare library
git clone https://github.com/waveshare/e-Paper.git

# Install Python library
cd e-Paper/RaspberryPi_JetsonNano/python
pip install .

# Verify driver files exist
ls lib/waveshare_epd/epd2in13_V3.py   # V3
ls lib/waveshare_epd/epd2in13_V4.py   # V4
```

### Minimal Python Example (V3)

```python
import sys, os
sys.path.insert(0, 'e-Paper/RaspberryPi_JetsonNano/python/lib')

from waveshare_epd import epd2in13_V3
from PIL import Image, ImageDraw
import time

epd = epd2in13_V3.EPD()
epd.init()
epd.Clear()

# Canvas — note width/height are swapped for landscape
image = Image.new('1', (epd.height, epd.width), 255)  # white background
draw  = ImageDraw.Draw(image)
draw.text((10, 10), "Hello, Dilder!", fill=0)           # black text

epd.display(epd.getbuffer(image))
time.sleep(2)
epd.sleep()
```

---

## GPIO Configuration in Code

```python
# Default pin assignments used by Waveshare library
RST_PIN  = 17   # GPIO 17, physical pin 11
DC_PIN   = 25   # GPIO 25, physical pin 22
CS_PIN   = 8    # GPIO 8 (CE0), physical pin 24
BUSY_PIN = 24   # GPIO 24, physical pin 18

# SPI configuration
SPI_BUS   = 0         # /dev/spidev0.0
SPI_SPEED = 4_000_000 # 4 MHz
```

---

## Safety Notes

| Risk | Rule |
|------|------|
| GPIO overvoltage | All signals must be 3.3V — do NOT connect 5V sources without a level shifter |
| FPC cable | Fragile — never bend the flat cable vertically or crease it |
| Hot-plugging | Always power off the Pi before attaching or removing the HAT |
| Refresh rate | Never refresh more often than every 3 minutes under sustained use |

---

## Official Links

| Resource | URL |
|----------|-----|
| Waveshare Wiki | [waveshare.com/wiki/2.13inch_e-Paper_HAT](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT) |
| GitHub library | [github.com/waveshare/e-Paper](https://github.com/waveshare/e-Paper) |
| V3 spec sheet (PDF) | [files.waveshare.com — V3 spec](https://files.waveshare.com/upload/4/4e/2.13inch_e-Paper_V3_Specification.pdf) |
| V4 spec sheet (PDF) | [files.waveshare.com — V4 spec](https://files.waveshare.com/upload/4/4e/2.13inch_e-Paper_V4_Specification.pdf) |
| SSD1680 datasheet | [orientdisplay.com — SSD1680](https://www.orientdisplay.com/wp-content/uploads/2022/08/SSD1680_v0.14.pdf) |
