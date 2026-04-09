# Hardware Research & Materials List

Research compiled during Phase 1 planning for the Dilder prototype test bench.

---

## Core Components

### 1. Raspberry Pi Zero WH

| Spec | Detail |
|------|--------|
| Model | Pi Zero W or Zero 2 W |
| Get the "WH" variant | Pre-soldered 2x20 GPIO header (saves soldering for prototyping) |
| Price | ~$15 |
| Power | 5V via micro-USB |

The Pi Zero 2 W is recommended if available -- same form factor but quad-core vs single-core. Either works.

### 2. Waveshare 2.13" E-Paper Display HAT (V4)

**Product:** [Amazon DE - B07Q5PZMGT](https://www.amazon.de/-/en/gp/product/B07Q5PZMGT)

| Spec | Detail |
|------|--------|
| Size | 2.13 inches (48.55mm x 23.71mm active area) |
| Resolution | 250 x 122 pixels |
| Colors | Black & White |
| Driver IC | SSD1680Z8 (V4) |
| Interface | SPI (4-wire, Mode 0) |
| Operating Voltage | 3.3V / 5V (onboard voltage translator) |
| Full Refresh | ~2 seconds |
| Partial Refresh | ~0.3 seconds |
| Standby Current | < 0.01 uA |
| Refresh Interval | >= 180 seconds recommended between full refreshes |
| Price | ~$13-18 |

**Pin Connections (BCM GPIO):**

| E-Paper Pin | Function | BCM GPIO | Physical Pin |
|-------------|----------|----------|-------------|
| VCC | Power 3.3V | 3.3V | 1 |
| GND | Ground | GND | 6 |
| DIN | SPI MOSI | GPIO 10 | 19 |
| CLK | SPI Clock | GPIO 11 | 23 |
| CS | Chip Select | GPIO 8 (CE0) | 24 |
| DC | Data/Command | GPIO 25 | 22 |
| RST | Reset | GPIO 17 | 11 |
| BUSY | Busy status | GPIO 24 | 18 |

**Important:** This is the V4 revision -- it requires V4-specific code. Waveshare provides Python and C examples.

**Resources:**
- [Waveshare Wiki](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT)
- [V4 Specification PDF](https://files.waveshare.com/upload/4/4e/2.13inch_e-Paper_V4_Specification.pdf)
- [SSD1680 Datasheet](https://www.orientdisplay.com/wp-content/uploads/2022/08/SSD1680_v0.14.pdf)

---

## Input Options (4-5 Buttons)

### Option A -- Discrete Tactile Buttons (Recommended for Prototype)

Simple 6x6mm through-hole momentary switches, optionally with colored snap-on caps.

| Detail | Value |
|--------|-------|
| Size | 6x6mm (various heights: 4.3mm to 9.5mm) |
| Cost | ~$2-3 for a pack of 20 |
| GPIO per button | 1 (+ shared ground) |
| Pull-up resistors | Use Pi's internal software pull-ups -- no external components needed |
| Debounce | Handle in software |

**Why this option:** Cheapest, simplest, breadboard-friendly for prototyping, easy to mount in a 3D-printed case later. The original Tamagotchi used 3 tactile buttons -- this is the authentic approach.

### Option B -- 5-Way Navigation Switch + 2 Action Buttons

Adafruit 5-way nav switch (up/down/left/right/center-press) plus 2 discrete buttons for A/B actions.

| Detail | Value |
|--------|-------|
| Nav switch | Adafruit ADA504, ~$2 |
| Action buttons | 2x 6x6mm tactile, ~$0.50 |
| GPIO pins | 7 total (5 for nav + 2 for buttons) |
| Total cost | ~$3 |

**Why this option:** Compact d-pad feel, good for menu navigation. More "game device" than "Tamagotchi."

### Option C -- Pimoroni Button SHIM

5 buttons + RGB LED on a single I2C board that solders directly onto the Pi header.

| Detail | Value |
|--------|-------|
| Cost | ~$7 |
| GPIO pins | 2 (I2C: SDA + SCL) |
| Pull-ups | Built in |
| Python library | Official `button-shim` package |

**Why this option:** Cleanest wiring, fewest GPIO pins used. But buttons are side-mounted which limits case design. May be discontinued.

### Other Considered Options

| Type | Cost | Notes |
|------|------|-------|
| 1x4 Membrane Keypad | ~$2-4 | Very thin, adhesive-backed. Mushy feel, only 4 buttons. |
| TTP223 Capacitive Touch | ~$1-3/10-pack | No moving parts, can mount behind plastic. No tactile feedback. |
| Analog Joystick | ~$5-6 | Requires external ADC (Pi has no analog inputs). Overkill for a virtual pet. |

### Decision

**For prototyping: Option A (5x discrete 6x6mm tactile buttons)**
- Layout: 3 nav buttons (left/select/right) + 2 action buttons (A/B)
- Total GPIO: 5 pins + shared ground
- Total cost: ~$2-3
- Can always swap to a different input method later

---

## Test Bench Materials List

### Essential -- Order These First

| Item | Est. Cost | Notes |
|------|-----------|-------|
| Raspberry Pi Zero WH | ~$15 | Pre-soldered headers. Zero 2 WH preferred if available. |
| Waveshare 2.13" e-Paper HAT V3 | ~$15 | [Amazon link](https://www.amazon.de/-/en/gp/product/B07Q5PZMGT). **V3 confirmed purchased.** Uses SSD1680 driver, requires `epd2in13_V3.py` |
| Micro SD card (16GB+) | ~$5-8 | For Raspberry Pi OS |
| Micro-USB power supply (5V 2.5A) | ~$8-10 | Any decent phone charger works |
| Half-size breadboard | ~$3-5 | For prototyping button wiring before soldering to perfboard. Bridges GPIO pins to buttons via jumper wires |
| Jumper wire kit (M-F and M-M) | ~$3-6 | Assorted lengths |
| 6x6mm tactile buttons (pack of 20) | ~$2-3 | Various heights, with snap-on caps |
| **Subtotal** | **~$51-62** | |

### Nice to Have

| Item | Est. Cost | Notes |
|------|-----------|-------|
| GPIO T-Cobbler breakout | ~$6-8 | Labels all pins on the breadboard |
| 10k resistor assortment | ~$2-3 | External pull-ups if needed |
| Multimeter | ~$10-20 | Debugging wiring |
| Soldering iron + solder | ~$20-40 | For permanent connections later |

### For Battery Power (Phase 6)

| Item | Est. Cost | Notes |
|------|-----------|-------|
| Adafruit PowerBoost 500C | ~$18 | LiPo charger + 5V boost, load-sharing |
| 3.7V LiPo battery (1200mAh) | ~$8-12 | JST-PH connector |
| Budget alt: TP4056 + MT3608 | ~$2-3 | Cheaper but more wiring/tuning |

---

## GPIO Pin Budget

| Function | Pins Used | Interface | Pins |
|----------|-----------|-----------|------|
| E-ink display | 6 | SPI | GPIO 8, 10, 11, 17, 24, 25 |
| Buttons (5) | 5 | Digital input | GPIO 5, 6, 13, 19, 26 (suggested) |
| Piezo buzzer (future) | 1 | PWM | GPIO 12 or 18 |
| **Total** | **12** | | **14+ GPIO remaining** |

Note: Buttons are assigned to GPIOs that don't conflict with SPI or other special functions. The specific pins can be changed -- the above are suggestions for clean wiring.

---

## Prototype Enclosure Concept

### Form Factor: "iPod Nano" Style -- Landscape Rectangle with Side D-Pad

Concept renders (open in browser to view):
- [prototype-v1.svg](concepts/prototype-v1.svg) -- Initial rough layout
- **[prototype-v2.svg](concepts/prototype-v2.svg)** -- Dimension-accurate revision (current)

### v2 Design Summary

Landscape rectangular slab with display dominating the left ~75% of the face, compact d-pad cluster on the right.

| Metric | Value |
|--------|-------|
| Case outer | 88 x 34 x 19mm |
| Display window | 57 x 27mm |
| Active pixel area | 48.55 x 23.71mm (250x122 px) |
| Button cluster | ~22mm wide (d-pad cross, 10mm center-to-center) |
| Display face coverage | 51% |
| Button face coverage | 12% |
| Display-to-button ratio | 4.3 : 1 |
| Weight (est.) | ~45g (with battery ~65g) |
| Size reference | Slightly wider than a credit card, ~2/3 the height |

### Component Dimensions (from datasheets)

| Component | Dimension | Source |
|-----------|-----------|--------|
| Pi Zero board | 65 x 30 x 5mm | Official spec |
| Waveshare HAT board | 65 x 30.2mm | Waveshare spec |
| Display glass outline | 59.2 x 29.2 x 1.05mm | V4 specification PDF |
| Display active area | 48.55 x 23.71mm | V4 specification PDF |
| Dot pitch | 0.194 x 0.194mm | V4 specification PDF |
| Pi + HAT stack height | ~15mm (with GPIO header) | Measured |
| 6x6mm tactile button | 6 x 6 x 4.3-9.5mm (various stem heights) | Standard |

### Design Constraints

1. **Display cutout:** 57 x 27mm (glass area with 1mm case lip overlap)
2. **Button holes:** 5x circular, ~7mm diameter, d-pad cross pattern with ~10mm center-to-center
3. **USB access:** Micro-USB slot on bottom edge
4. **SD card access:** Slot on left edge
5. **Ventilation:** 5x slot vents on back panel
6. **Assembly:** 2-piece shell (top + bottom), 4x M2 corner screws
7. **Shell seam:** Horizontal split at case midpoint (~9.5mm from each face)
8. **Battery bay:** Reserved space on right side behind button PCB (30 x 19mm, future)

---

## Next Steps

1. Order the essential materials from the test bench list
2. Set up Pi Zero with headless Raspberry Pi OS
3. Wire the e-ink display (it's a HAT -- just plugs onto the header)
4. Wire 5 buttons on a breadboard
5. Get Waveshare's example Python code running to confirm display works
6. Display a placeholder sprite as proof of life
