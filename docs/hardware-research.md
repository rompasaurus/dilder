# Hardware Research & Materials List

Research compiled during Phase 1 planning for the Dilder prototype test bench.

---

## Development Platform Strategy

**Phase 1 (current):** Raspberry Pi Pico W — cheap, on hand, great for prototyping the display + input system with MicroPython.

**Future:** Raspberry Pi Zero WH — upgrade when we need Linux, filesystem, networking features, or more compute. The display and button wiring is nearly identical; the firmware port is Phase 5.

---

## Core Components

### 1. Raspberry Pi Pico W

| Spec | Detail |
|------|--------|
| Chip | RP2040 — dual-core ARM Cortex-M0+ @ 133MHz |
| RAM | 264KB SRAM |
| Flash | 2MB onboard (no SD card) |
| Wi-Fi | 802.11n 2.4GHz (CYW43439) |
| Bluetooth | BLE 5.2 |
| GPIO | 26 multi-function pins (GP0–GP28, not all exposed) |
| ADC | 3 channels (12-bit) |
| SPI | 2× SPI controllers |
| USB | Micro-USB (power + data, device/host) |
| Dimensions | 51 × 21 × 3.9mm |
| Price | ~$6 |
| Firmware | MicroPython (recommended) or CircuitPython |

The Pico WH variant has pre-soldered headers — convenient for breadboard prototyping but either works.

**Resources:**
- [Pico W Datasheet (PDF)](https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf)
- [RP2040 Datasheet (PDF)](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)
- [MicroPython for Pico W](https://micropython.org/download/RPI_PICO_W/)
- [Pico W Pinout](https://datasheets.raspberrypi.com/picow/PicoW-A4-Pinout.pdf)

### 2. Waveshare 2.13" E-Paper Display HAT (V3)

**Product:** [Amazon DE - B07Q5PZMGT](https://www.amazon.de/-/en/gp/product/B07Q5PZMGT)

| Spec | Detail |
|------|--------|
| Size | 2.13 inches (48.55mm x 23.71mm active area) |
| Resolution | 250 x 122 pixels |
| Colors | Black & White |
| Driver IC | SSD1680 (V3) |
| Interface | SPI (4-wire, Mode 0) |
| Operating Voltage | 3.3V / 5V (onboard voltage translator) |
| Full Refresh | ~2 seconds |
| Partial Refresh | ~0.3 seconds |
| Standby Current | < 0.01 uA |
| Refresh Interval | >= 180 seconds recommended between full refreshes |
| Price | ~$13-18 |

**Important:** This is the **V3** revision (SSD1680 driver). The HAT is designed for Pi Zero's 40-pin header, but we connect to the Pico W via jumper wires using the 8-pin SPI interface.

**Pin Connections to Pico W (via jumper wires):**

| E-Paper Pin | Function | Pico W GPIO | Pico W Pin # |
|-------------|----------|-------------|-------------|
| VCC | Power 3.3V | 3V3(OUT) | 36 |
| GND | Ground | GND | 38 |
| DIN | SPI MOSI | GP11 (SPI1 TX) | 15 |
| CLK | SPI Clock | GP10 (SPI1 SCK) | 14 |
| CS | Chip Select | GP9 (SPI1 CSn) | 12 |
| DC | Data/Command | GP8 | 11 |
| RST | Reset | GP12 | 16 |
| BUSY | Busy status | GP13 | 17 |

**Resources:**
- [Waveshare Wiki](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT)
- [Waveshare Pico e-Paper Code](https://github.com/waveshare/Pico_ePaper_Code)
- [V3 Specification PDF](https://files.waveshare.com/upload/4/4e/2.13inch_e-Paper_V3_Specification.pdf)
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
| Pull-up resistors | Use Pico W's internal software pull-ups -- no external components needed |
| Debounce | Handle in software |

**Why this option:** Cheapest, simplest, breadboard-friendly for prototyping. The original Tamagotchi used 3 tactile buttons -- this is the authentic approach.

### Other Considered Options

| Type | Cost | Notes |
|------|------|-------|
| 5-Way Nav Switch + 2 buttons | ~$3 | Compact d-pad feel, 7 GPIO pins. More "game device" than "Tamagotchi." |
| 1x4 Membrane Keypad | ~$2-4 | Very thin, adhesive-backed. Mushy feel, only 4 buttons. |
| TTP223 Capacitive Touch | ~$1-3/10-pack | No moving parts. No tactile feedback. |

### Decision

**For prototyping: Option A (5x discrete 6x6mm tactile buttons)**
- Layout: 3 nav buttons (left/select/right) + 2 action buttons (A/B)
- Total GPIO: 5 pins + shared ground
- Total cost: ~$2-3

---

## Test Bench Materials List

### Essential -- On Hand

| Item | Est. Cost | Notes |
|------|-----------|-------|
| Raspberry Pi Pico W | ~$6 | On hand. Micro-USB for power + data. |
| Waveshare 2.13" e-Paper HAT V3 | ~$15 | On hand. SSD1680 driver, 250×122px. Connected via jumper wires (not HAT connector). |
| Micro-USB cable | ~$2 | For Pico W power + programming |
| Half-size breadboard | ~$3-5 | For prototyping button + display wiring |
| Jumper wire kit (M-F and M-M) | ~$3-6 | **Required** — the display HAT doesn't plug into the Pico W directly |
| 6x6mm tactile buttons (pack of 20) | ~$2-3 | Various heights, with snap-on caps |
| **Subtotal** | **~$31-37** | |

### Nice to Have

| Item | Est. Cost | Notes |
|------|-----------|-------|
| Pico WH (pre-soldered headers) | ~$7 | Easier breadboard use than bare Pico W |
| 10k resistor assortment | ~$2-3 | External pull-ups if needed |
| Multimeter | ~$10-20 | Debugging wiring |

### For Battery Power (Later Phase)

| Item | Est. Cost | Notes |
|------|-----------|-------|
| 3.7V LiPo battery (1200mAh) | ~$8-12 | JST connector |
| Adafruit PowerBoost 500C | ~$18 | LiPo charger + 5V boost, load-sharing |
| Budget alt: TP4056 + boost converter | ~$2-3 | Cheaper but more wiring |

---

## GPIO Pin Budget (Pico W)

| Function | Pins Used | Interface | Pico W GPIO |
|----------|-----------|-----------|-------------|
| E-ink display | 6 | SPI1 + control | GP8, GP9, GP10, GP11, GP12, GP13 |
| Buttons (5) | 5 | Digital input | GP2, GP3, GP4, GP5, GP6 |
| Piezo buzzer (future) | 1 | PWM | GP15 |
| **Total** | **12** | | **14+ GPIO remaining** |

Note: Button GPIOs are chosen to avoid SPI1 pins and leave SPI0 free for future use. The specific pins can be changed — the above are suggestions for clean wiring.

---

## Prototype Enclosure Concept

> Enclosure design is deferred until Phase 5/6 when we migrate to the Pi Zero. The Pico W prototype lives on a breadboard.

### Original Form Factor: "iPod Nano" Style -- Landscape Rectangle with Side D-Pad

Concept renders (designed for Pi Zero + HAT form factor):
- [prototype-v1.svg](concepts/prototype-v1.svg) -- Initial rough layout
- **[prototype-v2.svg](concepts/prototype-v2.svg)** -- Dimension-accurate revision

These will be revised when the final board (Pico W or Pi Zero) is chosen for the enclosure build.

---

## Next Steps

1. Flash MicroPython firmware onto Pico W
2. Set up VSCode with MicroPico extension
3. Wire the e-ink display to the Pico W via jumper wires
4. Wire 5 buttons on the breadboard
5. Get Waveshare's MicroPython example code running to confirm display works
6. Display a placeholder sprite as proof of life
