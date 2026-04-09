# Display Setup

How to attach the Waveshare 2.13" e-Paper HAT (V3) and get your first image on screen.

**Prerequisites:** Complete [Pi Zero Setup](pi-zero-setup.md) first — SPI must be enabled and Python dependencies installed.

---

## Attach the HAT

The Waveshare HAT plugs directly onto the Pi Zero's 40-pin GPIO header. No jumper wires needed.

1. Power off the Pi Zero (`sudo shutdown -h now`, wait for the activity LED to stop)
2. Align the HAT's 40-pin female header with the Pi's male header
3. Press down firmly and evenly — you should feel it seat fully
4. Power the Pi back on

!!! warning "Never hot-plug the HAT"
    Always power off the Pi before attaching or detaching the display. The e-ink panel can be damaged by voltage spikes during live connection.

---

## Install the Waveshare Library

```bash
cd ~/dilder
source venv/bin/activate

# Clone the Waveshare e-Paper library
git clone https://github.com/waveshare/e-Paper.git

# Install the Python library
cd e-Paper/RaspberryPi_JetsonNano/python
pip install .
```

### Verify the Driver File

```bash
# The V3 driver should be at:
ls lib/waveshare_epd/epd2in13_V3.py
```

!!! danger "V3 vs V4 driver mismatch"
    Using the wrong driver version will either fail silently or produce garbage output. Confirm your display version before proceeding.

    - **V3** uses `epd2in13_V3.py` (SSD1680)
    - **V4** uses `epd2in13_V4.py` (SSD1680Z8)

    Check your display's PCB silkscreen or the Waveshare product page.

---

## Run the Demo Script

```bash
cd ~/dilder/e-Paper/RaspberryPi_JetsonNano/python/examples
python3 epd_2in13_V3_test.py
```

You should see the display cycle through several test patterns — text, shapes, partial refresh. This confirms the hardware is working.

---

## Write a Minimal Script

Once the demo runs, write a minimal script to confirm you understand the API:

```python
# ~/dilder/hello_display.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 
    'e-Paper/RaspberryPi_JetsonNano/python/lib'))

from waveshare_epd import epd2in13_V3
from PIL import Image, ImageDraw, ImageFont
import time

epd = epd2in13_V3.EPD()

try:
    print("Initializing...")
    epd.init()
    epd.Clear()

    # Create a blank white canvas
    # Note: display is landscape when width > height
    image = Image.new('1', (epd.height, epd.width), 255)  # 255 = white
    draw = ImageDraw.Draw(image)

    # Draw some text
    draw.text((10, 10), "Hello, Dilder!", fill=0)  # 0 = black
    draw.rectangle([(0, 0), (epd.height - 1, epd.width - 1)], outline=0)

    # Display it
    epd.display(epd.getbuffer(image))
    time.sleep(2)

    # Put display to sleep
    epd.sleep()
    print("Done.")

except KeyboardInterrupt:
    epd.sleep()
    epd2in13_V3.epdconfig.module_exit()
```

Run it:

```bash
source venv/bin/activate
python3 hello_display.py
```

---

## Canvas Orientation

The display is 250×122 pixels. The e-Paper library uses a coordinate system where:

- `epd.width` = 122 (short dimension)
- `epd.height` = 250 (long dimension)
- Landscape mode: create `Image.new('1', (epd.height, epd.width))` = 250×122

```
(0,0) ──────────────────── (249, 0)
  │                              │
  │     250 × 122 pixels         │
  │                              │
(0,121) ─────────────── (249, 121)
```

---

## Partial Refresh

Full refresh takes ~2 seconds and causes visible flicker. Partial refresh updates only changed pixels in ~0.3 seconds with no flicker. Use partial refresh for animation and UI updates.

```python
# Initialize for partial refresh
epd.init(epd.PART_UPDATE)

# Update a region without full flicker
epd.displayPartial(epd.getbuffer(image))
```

!!! warning "Refresh interval"
    Full refresh too frequently causes display degradation. Waveshare recommends a full refresh at least every 10 partial updates, and not more frequently than every 180 seconds under normal use.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Display shows nothing | SPI not enabled | `ls /dev/spi*` — if empty, re-enable SPI in raspi-config |
| Display shows garbage | Wrong driver version | Confirm V3 vs V4, use correct driver file |
| Script crashes with permission error | User not in `spi` group | `sudo usermod -aG spi,gpio pi` then re-login |
| Ghost image / burn-in | Too many partial refreshes | Run `epd.Clear()` to do a full reset |
| HAT not recognized | Loose connection | Power off, re-seat HAT |
