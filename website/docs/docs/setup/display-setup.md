# Display Setup

How to wire the Waveshare 2.13" e-Paper HAT (V3) to the Pico W and get your first image on screen.

**Prerequisites:** Complete [Pico W Setup](pi-zero-setup.md) first — MicroPython must be flashed and the serial REPL working.

---

## Wire the Display

The Waveshare HAT is designed for the Pi Zero's 40-pin header, but we connect it to the Pico W using the HAT's 8-pin side header and jumper wires.

!!! warning "Power off before wiring"
    Always disconnect USB before connecting or disconnecting jumper wires. The e-ink panel can be damaged by voltage spikes.

### Wiring Table

Use **female-to-male jumper wires**: female end onto the HAT's 8-pin header, male end into the Pico W's breadboard row.

| e-Paper Pin (on HAT header) | Pico W GPIO | Pico W Pin # | Wire Color (suggested) |
|---|---|---|---|
| VCC | 3V3(OUT) | 36 | Red |
| GND | GND | 38 | Black |
| DIN | GP11 (SPI1 TX) | 15 | Blue |
| CLK | GP10 (SPI1 SCK) | 14 | Yellow |
| CS | GP9 (SPI1 CSn) | 12 | Orange |
| DC | GP8 | 11 | Green |
| RST | GP12 | 16 | White |
| BUSY | GP13 | 17 | Purple |

See the [Wiring & Pinout](../hardware/wiring-pinout.md) page for the full visual diagram.

---

## Install the Waveshare MicroPython Driver

The Waveshare Pico e-Paper library provides MicroPython drivers for the display.

### Download the Driver Files

On your dev machine:

```bash
git clone https://github.com/waveshare/Pico_ePaper_Code.git
```

You need two files from `Pico_ePaper_Code/python/lib/`:

- `epd2in13_V3.py` — the V3 display driver
- `epdconfig.py` — SPI and GPIO configuration

### Upload to Pico W

Using the MicroPico VSCode extension (see [Dev Environment](dev-environment.md)):

1. Open the `Pico_ePaper_Code/python/lib/` folder
2. Upload `epd2in13_V3.py` and `epdconfig.py` to the Pico W's root filesystem

Or via the REPL with `mpremote`:

```bash
# Install mpremote if you don't have it
pip install mpremote

# Upload driver files
mpremote cp Pico_ePaper_Code/python/lib/epd2in13_V3.py :epd2in13_V3.py
mpremote cp Pico_ePaper_Code/python/lib/epdconfig.py :epdconfig.py
```

### Verify the Driver File

```python
>>> import os
>>> os.listdir('/')
['boot.py', 'epd2in13_V3.py', 'epdconfig.py']
```

!!! danger "V3 vs V4 driver mismatch"
    Using the wrong driver version will either fail silently or produce garbage output. Confirm your display version before proceeding.

    - **V3** uses `epd2in13_V3.py` (SSD1680)
    - **V4** uses `epd2in13_V4.py` (SSD1680Z8)

    Check your display's PCB silkscreen.

---

## Run a Test

### Quick Smoke Test via REPL

Connect to the Pico W REPL and run:

```python
from epd2in13_V3 import EPD_2in13_V3

epd = EPD_2in13_V3()
epd.init()
epd.Clear()
print("Display cleared — you should see a white screen")
```

If the display goes white, the wiring and driver are working.

---

## Write a Hello World Script

Create `hello_display.py` on your dev machine and upload it to the Pico W:

```python
# hello_display.py

from epd2in13_V3 import EPD_2in13_V3
import framebuf
import utime

epd = EPD_2in13_V3()

try:
    print("Initializing display...")
    epd.init()
    epd.Clear()

    # Create a framebuffer — 250×122, 1-bit mono
    buf = bytearray(epd.height * epd.width // 8)
    fb = framebuf.FrameBuffer(buf, epd.height, epd.width, framebuf.MONO_HLSB)

    # White background
    fb.fill(0xff)

    # Black text and border
    fb.text("Hello, Dilder!", 10, 10, 0x00)
    fb.text("Pico W + e-ink", 10, 30, 0x00)
    fb.rect(0, 0, epd.height, epd.width, 0x00)

    # Send to display
    epd.display(buf)
    print("Image displayed!")

    utime.sleep(5)

    # Put display to sleep (low power)
    epd.sleep()
    print("Display sleeping. Done.")

except Exception as e:
    print(f"Error: {e}")
    try:
        epd.sleep()
    except:
        pass
```

Run it:

```bash
mpremote run hello_display.py
```

Or upload and run via MicroPico in VSCode.

---

## Canvas Orientation

The display is 250×122 pixels. The Waveshare MicroPython driver uses:

- `epd.width` = 122 (short dimension)
- `epd.height` = 250 (long dimension)
- Landscape mode: create `FrameBuffer(buf, epd.height, epd.width)` = 250×122

```
(0,0) ──────────────────── (249, 0)
  │                              │
  │     250 × 122 pixels         │
  │                              │
(0,121) ─────────────── (249, 121)
```

!!! note "framebuf vs PIL"
    MicroPython uses `framebuf.FrameBuffer` instead of PIL/Pillow. The API is simpler — `fb.text()`, `fb.rect()`, `fb.pixel()`, `fb.fill()`. For more advanced graphics, you can draw into a bytearray and send it to the display.

---

## Partial Refresh

Full refresh takes ~2 seconds and causes visible flicker. Partial refresh updates only changed pixels in ~0.3 seconds with no flicker. Use partial refresh for animation and UI updates.

```python
# Initialize for partial refresh
epd.init_part()

# Update without full flicker
epd.displayPartial(buf)
```

!!! warning "Refresh interval"
    Full refresh too frequently causes display degradation. Waveshare recommends a full refresh at least every 5 partial updates, and not more frequently than every 180 seconds under sustained use.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Display shows nothing | Wiring wrong, or VCC not on 3V3(OUT) | Double-check all 8 wires against the wiring table |
| Display shows garbage | Wrong driver version | Confirm V3 vs V4, use correct driver file |
| `OSError: [Errno 5] EIO` | SPI misconfigured | Verify GP10=SCK, GP11=MOSI, GP9=CS |
| `ImportError: no module named 'epd2in13_V3'` | Driver not uploaded | Upload `epd2in13_V3.py` and `epdconfig.py` to Pico W |
| Ghost image / burn-in | Too many partial refreshes | Run `epd.Clear()` to do a full reset |
| No serial connection | Cable is charge-only | Use a data-capable USB cable |
