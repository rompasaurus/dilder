# Hardware Research & Materials List

Research compiled during Phase 1 planning for the Dilder prototype test bench.

---

## Development Platform Strategy

**Phase 1 (current):** Raspberry Pi Pico W — cheap, on hand, great for prototyping the display + input system with C/C++ via the Pico SDK.

**Recommended upgrade:** Raspberry Pi Pico 2 W — drop-in replacement with WiFi, BLE, 2× SRAM, 2× flash, faster CPU, near-zero porting effort.

**Future:** Raspberry Pi Zero WH — upgrade when we need Linux, filesystem, networking features, or more compute. The display and button wiring is nearly identical; the firmware port is Phase 5.

---

## Board Comparison

Evaluated against Dilder's requirements: SPI display (6 GPIO), 5 buttons (5 GPIO), USB serial, future WiFi/BLE (Phase 7), and the existing C/Pico SDK firmware.

| Board | CPU | GPIO | Flash | SRAM | WiFi | BT | SPI | USB | SDK Compatibility | Price |
|---|---|---|---|---|---|---|---|---|---|---|
| **Pi Pico** (current) | RP2040 M0+ 133MHz | **26** | 2MB | 264KB | -- | -- | 2× | Micro | Pico SDK (current) | ~4.80 |
| **Pi Pico H** | RP2040 M0+ 133MHz | **26** | 2MB | 264KB | -- | -- | 2× | Micro | Pico SDK (current) | ~4.80 |
| **Pi Pico 2 W** | RP2350 M33 150MHz | **26** | 4MB | 520KB | **Yes** | **BLE 5.2** | 2× | Micro | Pico SDK 2.x (backwards-compatible) | ~7.50 |
| **Pi Pico 2 WH** | RP2350 M33 150MHz | **26** | 4MB | 520KB | **Yes** | **BLE 5.2** | 2× | Micro | Pico SDK 2.x (backwards-compatible) | ~8.50 |
| **XIAO RP2350** | RP2350 M33 150MHz | **11** | 2MB | 520KB | -- | -- | 1× | USB-C | Pico SDK 2.x | ~6.45 |
| **XIAO ESP32S3+** | Xtensa LX7 240MHz | **11** | 8MB | 512KB | **Yes** | **BLE 5.0** | 1× | USB-C | ESP-IDF (full rewrite) | ~9.99 |
| **XIAO nRF52840** | M4 64MHz | **11** | 1MB+2MB | 256KB | -- | **BLE 5.0** | 1× | USB-C | Zephyr/nRF SDK (full rewrite) | ~9.40 |
| **XIAO SAMD21** | M0+ 48MHz | **11** | 256KB | 32KB | -- | -- | 1× | USB-C | Arduino (full rewrite) | ~5.99 |
| **XIAO MG24 Sense** | M33 78MHz | **11** | 1.5MB | 256KB | -- | **BLE+Zigbee** | 1× | USB-C | Gecko SDK (full rewrite) | ~10.60 |

### Key findings

- **All XIAO boards** have only 11 GPIO — exactly enough for 6 display + 5 buttons with zero pins remaining for the planned piezo buzzer or future sensors.
- **Non-RP2350 XIAO boards** require a full firmware rewrite to a different SDK (ESP-IDF, Zephyr, Arduino, Gecko).
- **The Pico 2 W** is the clear upgrade path: same form factor, same pinout, backwards-compatible SDK, WiFi + BLE for Phase 7, 2× memory, and only 2.70 more than the current Pico.
- **XIAO nRF52840** has no WiFi, which blocks Phase 7 networking plans. Its BLE 5.0 alone is not sufficient for the planned WiFi-based features.

### Board recommendation

The **Raspberry Pi Pico 2 W** at 7.50 covers the entire project roadmap through Phase 7 with minimal code changes — just recompile against Pico SDK 2.x.

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
| Firmware | C/C++ via Pico SDK (CMake + arm-none-eabi-gcc) |

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

## Display Comparison

Comparison of the current Waveshare 2.13" V3 against alternative e-paper and LCD displays evaluated for the Dilder project.

### E-Paper Displays

| Spec | **Waveshare 2.13" V3** (current) | **DEBO EPA 2.9"** | **DEBO EPA 2.1" RD** | **DEBO EPA 1.54" RD** |
|---|---|---|---|---|
| **Size** | 2.13" (48.6 × 23.7mm active) | **2.9"** (~66.9 × 29.1mm) | 2.1" (~46.9 × 22.5mm) | 1.54" (~27.5 × 27.6mm) |
| **Resolution** | 250 × 122 (30,500 px) | **296 × 128** (37,888 px) | 212 × 104 (22,048 px) | 200 × 200 (40,000 px) |
| **Dot pitch** | 0.194mm | ~0.227mm | ~0.221mm | ~0.138mm |
| **Colors** | Black / White | Black / White | Black / White / **Red** | Black / White / **Red** |
| **Driver IC** | SSD1680 | SSD1680 (likely) | SSD1675B (likely) | SSD1681 (likely) |
| **Interface** | SPI 4-wire | SPI 4-wire | SPI 4-wire | SPI 4-wire |
| **Full refresh** | ~2s | ~2s | **~6–15s** (red layer) | **~6–15s** (red layer) |
| **Partial refresh** | ~0.3s | ~0.3s | **Unreliable / unsupported** | **Unreliable / unsupported** |
| **Standby current** | < 0.01µA | < 0.01µA | < 0.01µA | < 0.01µA |
| **Active power** | ~26.4mW | ~26–30mW | ~30–40mW | ~25–35mW |
| **Buffer size** | 3,904 bytes | **4,736 bytes** | **2× 2,756 bytes** (B/W + Red) | **2× 5,000 bytes** (B/W + Red) |
| **GPIO pins needed** | 6 | 6 | 6 | 6 |
| **Price** | ~13–18 (already owned) | ~19.70 | ~17.50 | ~15.40 |

#### DEBO EPA 2.9" B/W — The Natural Upgrade

**Improvements:**
- 24% more pixels (37,888 vs 30,500) — more room for pet animations, speech bubbles, and status bars.
- 37% larger active area — physically bigger, better for a handheld device.
- Same driver family (SSD1680) — the existing Waveshare C driver likely needs only resolution constant changes and minor init sequence tweaks.
- Same refresh characteristics — full ~2s, partial ~0.3s, same 180s interval rules.
- Same SPI protocol — identical wiring, identical pin count, drop-in on the same breadboard.

**Drawbacks:**
- Buffer grows from 3,904 to 4,736 bytes (still trivial for 264KB SRAM).
- Landscape canvas in DevTool changes from 250×122 to 296×128 — the IMG protocol, transpose logic in `img-receiver/main.c`, and DevTool canvas dimensions all need updating.
- Physically larger — may affect enclosure planning.
- Slightly coarser dot pitch (0.227 vs 0.194mm) — individual pixels are more visible.

**Firmware impact:** Moderate. Update `EPD_WIDTH`/`EPD_HEIGHT` constants, `IMG_W` (250→296), `IMG_H` (122→128), `IMG_ROW_BYTES` (32→37), `IMG_TOTAL` (3904→4736), DevTool canvas size, and Sassy Octopus frame dimensions. Core SPI driver and partial refresh logic stay the same.

#### DEBO EPA 2.1" RD — Tri-Color, Smaller

**Improvements:**
- Red as a third color — could highlight health bars, warnings, and pet emotions.
- Similar physical size to the current display.

**Drawbacks:**
- Resolution drops to 212×104 — 28% fewer pixels than the current display.
- Full refresh takes 6–15 seconds — the red pigment particles are physically larger and slower to move. This is a fundamental physics limitation.
- Partial refresh is unreliable or unsupported on tri-color panels — the current 0.3s partial refresh animation approach (Sassy Octopus) would not work.
- Double buffer required — two separate image planes (B/W layer + Red layer), each ~2,756 bytes.
- Different driver IC (SSD1675B vs SSD1680) — the existing Waveshare C driver will not work. Requires a completely different init sequence, LUT, and command set.
- Red particles ghost worse than black, requiring even longer clearing refresh cycles.

**Firmware impact:** Heavy rewrite. New driver IC, new buffer format, no partial refresh means rethinking the entire animation approach. DevTool would need a 3-color canvas mode.

#### DEBO EPA 1.54" RD — Tri-Color, Square, Tiny

**Improvements:**
- Square aspect ratio (200×200) — unique layout possibilities, centered pet sprite.
- Highest pixel density (0.138mm dot pitch) — sharpest text and detail of all four.
- Smallest physical footprint — easiest to fit in a compact enclosure.

**Drawbacks:**
- Same 6–15s tri-color refresh penalty — same red particle physics problem.
- Same "no partial refresh" limitation — animations are dead.
- Physically tiny (27.5mm square) — smaller than the current 2.13" display.
- Double buffer — 2× 5,000 bytes (larger than the 2.1" RD due to higher resolution).
- Different driver IC (SSD1681) — yet another driver to write from scratch.
- Square aspect ratio means every existing asset needs redesigning for a completely different layout.

**Firmware impact:** Complete rewrite. New driver, new aspect ratio, new buffer format, no partial refresh.

### The Core Trade-off: Red Color vs. Animation

| | B/W e-ink | Tri-color (B/W/R) e-ink |
|---|---|---|
| **Full refresh** | ~2s | ~6–15s |
| **Partial refresh** | ~0.3s (smooth-ish animation) | Not reliably supported |
| **Sassy Octopus animation** | Works (current approach) | Broken — 6–15s between frames |
| **Interactive pet** | Feasible with partial refresh | Effectively a static display |
| **Visual flair** | Black and white only | Red accents for highlights |
| **Driver complexity** | Simpler (single buffer) | Double buffer, longer LUTs |

For a Tamagotchi-style pet that needs to react, animate, and feel alive, partial refresh is non-negotiable. That rules out both red displays for the primary screen.

### LCD/TFT Alternatives (Also Evaluated)

| Display | Type | Size | Resolution | Driver | Refresh | Active Power | Price |
|---|---|---|---|---|---|---|---|
| **DEBO LCD128X128** | LCD TFT | 1.44" | 128×128 | ST7735S | ~60+ FPS | ~20–40mW | ~5.90 |
| **DEBO LCD 2.0** | LCD TFT | 2.0" | 220×176 | ILI9225 | ~60+ FPS | ~40–80mW | ~7.99 |
| **DEBO LCD240X240** | LCD IPS | 1.3" | 240×240 | ST7789 | ~60+ FPS | ~30–60mW | ~10.60 |
| **DEBO TFT 1.8** | LCD TFT | 1.8" | 128×160 | ST7735R | ~60+ FPS | ~30–60mW | ~9.80 |
| **DEBO TFT 1.8 TD** | LCD TFT+Touch | 1.8" | 128×160 | ST7735R | ~60+ FPS | ~35–65mW | ~8.95 |
| **ARD SHD 2.6TD** | LCD TFT+Touch | 2.6" | 320×240 | ILI9341 | ~30–60 FPS | ~80–150mW | ~6.65 |
| **ARD SHD 2.8TD** | LCD TFT+Touch | 2.8" | 320×240 | ILI9341 | ~30–60 FPS | ~100–200mW | ~11.60 |

LCDs offer 60+ FPS full-color animation but require an always-on backlight (20–200mW continuous), killing battery life compared to e-paper's near-zero idle draw. Touch-capable displays (ILI9341 shields) could replace physical buttons but consume more GPIO pins — problematic on XIAO boards.

### Display Recommendation

**Primary display upgrade:** The **DEBO EPA 2.9" B/W** is the best fit — bigger, more pixels, same speed, same driver family, minimal porting work. Paired with the Pico 2 W, it covers the entire project roadmap.

**Red displays** could be fun for a secondary notification screen or a different project, but their 6–15s refresh and lack of partial refresh make them unusable as Dilder's primary display.

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
| Waveshare Pico-ePaper-2.13 | ~$15 | On hand. SSD1680 driver, 250×122px. Pico-native module — plugs directly onto Pico W or connects via 8-pin breakout header. |
| Micro-USB cable | ~$2 | For Pico W power + programming |
| Half-size breadboard | ~$3-5 | For prototyping button + display wiring |
| Jumper wire kit (M-F and M-M) | ~$3-6 | Needed for breadboard peripherals (joystick, GPS, HC-SR04). Display can plug directly onto Pico. |
| 6x6mm tactile buttons (pack of 20) | ~$2-3 | Various heights, with snap-on caps |
| **Subtotal** | **~$31-37** | |

### Nice to Have

| Item | Est. Cost | Notes |
|------|-----------|-------|
| Pico WH (pre-soldered headers) | ~$7 | Easier breadboard use than bare Pico W |
| 10k resistor assortment | ~$2-3 | External pull-ups if needed |
| Multimeter | ~$10-20 | Debugging wiring |

### For Battery Power (Phase 6)

See the [Battery & Power](#battery--power) section below for full analysis.

| Item | Est. Cost | Notes |
|------|-----------|-------|
| 3.7V LiPo battery (1000mAh, recommended) | ~$7 | JST PH 2.0mm connector. Wires directly to VSYS on Pico W — no boost converter needed. |
| TP4056 charging module | ~$1.50 | Budget USB charging with over-discharge protection. |
| Adafruit PowerBoost 500C (upgrade) | ~$16 | LiPo charger + 5V boost + load sharing (use device while charging). |

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

## Battery & Power

### Board Power Consumption

| Board | Active (WiFi off) | Active (WiFi on) | Deep Sleep | VSYS/BAT Input | Boost Needed? |
|---|---|---|---|---|---|
| **Pico W** (current) | ~28mA | ~80mA | ~1.0mA | VSYS: 1.8–5.5V | No |
| **Pico 2 W** (recommended) | ~32mA | ~85mA | ~0.7mA | VSYS: 1.8–5.5V | No |
| **XIAO ESP32S3+** | ~35mA | ~100mA (350mA TX peaks) | ~8µA | BAT pads (built-in charger) | No |
| **XIAO nRF52840** | ~8mA | N/A (BLE only: ~12mA) | ~3µA | BAT pads (built-in charger) | No |
| **XIAO RP2350** | ~30mA | N/A (no wireless) | ~0.5mA | BAT pads (built-in charger) | No |
| **Pi Zero W** (Phase 5) | ~90mA @ 5V | ~140mA @ 5V | ~35mA (halt only) | 5V GPIO pin | **Yes** (3.7→5V) |

The Waveshare e-ink display adds negligible average current: ~0.013mA at 3-minute partial refresh intervals (~8mA active for 0.3s every 180s).

### Battery Monitoring (Built-in)

- **Pico W / Pico 2 W:** GPIO29 (ADC3) reads VSYS through an onboard 3:1 voltage divider. GPIO24 detects USB connection (HIGH = plugged in). No external components needed.
- **XIAO nRF52840:** Onboard voltage divider to P0.31 (AIN7) for battery voltage. No external components needed.
- **XIAO ESP32S3+:** May need an external voltage divider (2× 100k resistors) from BAT+ to an ADC GPIO, depending on board revision.
- **Pi Zero W:** No onboard ADC — requires an external ADC module (ADS1015 or INA219 over I2C, ~$3–5).

### LiPo Battery Options

All batteries are 3.7V nominal (4.2V full charge, 3.0V cutoff), single-cell lithium polymer with JST PH 2.0mm 2-pin connector.

**Important:** Always verify connector polarity before connecting. Chinese LiPo cells often have reversed polarity compared to Adafruit convention.

| Size | Capacity | Typical Dimensions | Weight | Price | Notes |
|---|---|---|---|---|---|
| **Small** | 400–500mAh | 35×20×5mm | ~10–12g | ~$3–7 | Thin, fits easily in any enclosure. Good for testing. |
| **Medium** (recommended) | 800–1000mAh | 50×34×5mm | ~18–22g | ~$5–10 | Best balance of capacity, size, and cost for Dilder. |
| **Large** | 1200–1500mAh | 59×37×5mm | ~25–30g | ~$7–12 | Good runtime, still fits 80×40mm enclosure footprint. |
| **XL** | 2000mAh | 60×40×7mm | ~35g | ~$8–15 | Near-maximum for the planned enclosure. 7mm thick — verify clearance with PCB + display. |
| **XXL** | 3000mAh | 70×50×8mm | ~50g | ~$10–18 | Likely too large for the current enclosure design (80×40×15mm). Would require a thicker or wider case. Overkill for most use cases. |

### Battery Life Estimates

Calculated in "Tamagotchi mode": active 10 minutes per hour (CPU running, polling buttons, occasional display refresh, WiFi off), deep sleep for the remaining 50 minutes. Battery capacity derated to 90% for real-world performance.

| Board | 500mAh | 1000mAh | 2000mAh | 3000mAh |
|---|---|---|---|---|
| **Pico W** | 3.4 days | **6.8 days** | 13.6 days | 20.5 days |
| **Pico 2 W** | 3.2 days | **6.4 days** | 12.7 days | 19.1 days |
| **XIAO ESP32S3+** | 3.2 days | 6.4 days | 12.8 days | 19.3 days |
| **XIAO nRF52840** | 14 days | **28 days** | 56 days | 84 days |
| **XIAO RP2350** | 3.5 days | 7.0 days | 13.9 days | 20.9 days |
| **Pi Zero W** | 0.3 days | 0.5 days | 1.0 day | 1.6 days |

The XIAO nRF52840 is the standout for battery life due to its ~8mA active draw and ~3µA deep sleep, but it has no WiFi. The Pi Zero W is unsuitable for battery-powered handheld use — even 3000mAh barely lasts 1.5 days.

### Charging Solutions

| Solution | Input | Charge Rate | Output | Load Sharing | Price | Best For |
|---|---|---|---|---|---|---|
| **TP4056 module** | USB 5V | 1A | Battery voltage (3.7V) | Partial | ~$1.50 | Budget Pico W builds — output wires to VSYS |
| **Adafruit PowerBoost 500C** | USB 5V | 500mA | 5.2V boosted | **Yes** | ~$16 | Pico W / Pico 2 W with clean USB charging |
| **Adafruit PowerBoost 1000C** | USB 5V | 1A | 5.2V boosted | **Yes** | ~$22 | Pi Zero W (needs 5V and higher current) |
| **MCP73831 breakout** | USB 5V | 100–500mA | Battery voltage | No | ~$2 | Custom PCB with minimal charging |
| **XIAO built-in** | USB-C | ~50–100mA | 3.3V regulated | **Yes** | **$0** | All XIAO boards — no external board needed |

XIAO boards have built-in LiPo charging, making them the simplest option (just solder battery wires to BAT pads). The trade-off is slow charging: ~50–100mA means a 1000mAh battery takes 10–20 hours to fully charge.

### Wiring — Pico W / Pico 2 W

No boost converter needed — VSYS accepts 3.7V LiPo directly (rated 1.8–5.5V).

**Recommended setup (TP4056 — budget):**

```
USB 5V ──► TP4056 IN+          LiPo(+) ◄── TP4056 BAT+
GND ──────► TP4056 IN-          LiPo(-) ◄── TP4056 BAT-
                                TP4056 OUT+ ──► VSYS (pin 39)
                                TP4056 OUT- ──► GND  (pin 38)
```

**Upgrade setup (PowerBoost 500C — load sharing):**

```
USB 5V ──► PowerBoost VIN      LiPo(+) ◄── PowerBoost BAT+
GND ──────► PowerBoost GND      LiPo(-) ◄── PowerBoost BAT-
                                PowerBoost 5V OUT ──► VBUS (pin 40)
                                PowerBoost GND    ──► GND  (pin 38)
                                PowerBoost LBO    ──► GP15 (low-battery alert)
```

### Wiring — XIAO Boards (ESP32S3+, nRF52840, RP2350)

```
LiPo(+) ──► BAT+ pad (bottom of board)
LiPo(-) ──► BAT- pad (bottom of board)

That's it. USB-C charges automatically.
```

### Wiring — Pi Zero W (Boost Required)

```
USB 5V ──► PowerBoost 1000C VIN    LiPo(+) ◄── PowerBoost BAT+
GND ──────► PowerBoost GND          LiPo(-) ◄── PowerBoost BAT-
                                    PowerBoost 5V OUT ──► GPIO pin 2 (5V)
                                    PowerBoost GND    ──► GPIO pin 6 (GND)
                                    PowerBoost LBO    ──► GPIO17 (low-battery)
```

Requires an external ADC module (ADS1015 or INA219 on I2C) for battery level monitoring.

### Alternative: 3× AAA NiMH (Rechargeable)

3 AAA NiMH cells in series produce 3.6V nominal (3.0–4.2V range) — compatible with Pico W VSYS. No boost converter needed.

| Spec | 3× AAA NiMH (Eneloop) | LiPo 1000mAh |
|---|---|---|
| **Voltage** | 3.6V (3× 1.2V series) | 3.7V |
| **Capacity** | ~800mAh usable | 1000mAh |
| **Dimensions** | ~45×32×11mm (in holder) | 50×34×5mm |
| **Swappable** | Yes — pop in fresh cells | No — USB charge only |
| **Cycle life** | ~2100 cycles | ~300–500 cycles |
| **Tamagotchi life (Pico W)** | ~5.4 days | ~6.8 days |
| **Cost** | ~$10 (cells + holder + external charger) | ~$8.50 (cell + TP4056) |

The main trade-off is form factor: the 3-cell holder is 11mm thick vs 5mm for a flat LiPo pouch. A single AAA (1.2V) does not work — it falls below VSYS minimum (1.8V) and a boost converter adds cost, complexity, and ~15–20% efficiency loss.

### Battery Recommendation

**For Dilder:** A **1000mAh LiPo** (503450 form factor, 50×34×5mm) paired with a **TP4056 module** is the best starting point at ~$8.50 total. This provides ~6.8 days in Tamagotchi mode on the Pico W. Upgrade to the PowerBoost 500C later if load sharing (use while charging) is needed.

For maximum runtime without changing the enclosure, a **2000mAh** cell (60×40×7mm) doubles battery life to ~13.6 days. A 3000mAh cell would require a larger enclosure.

---

## Flash Memory Expansion

The Pico W's 2MB onboard flash is soldered to the board and cannot be upgraded in-place. If future features (large encounter logs, creature databases, asset storage) outgrow the onboard flash, external storage can be added via the second SPI bus.

### Current Flash Budget

| Consumer | Estimated Size | Notes |
|---|---|---|
| Firmware code | ~200–500KB | Grows with features but well within 2MB |
| Peer discovery + breeding data | ~3.4KB | Encounter log, offspring, trait tables |
| Future creature assets / lookup tables | ~10–50KB | Conservative upper bound for modular trait system |
| **Headroom remaining** | **~1.4–1.8MB** | On the current 2MB Pico W |

The breeding system and peer discovery need negligible flash. Expansion is only relevant if the project grows to include large asset libraries, sound samples, or extensive save data.

### Option 0: Board Upgrade (More Onboard Flash)

Before adding external hardware, consider boards with more built-in flash.

| Board | Chip | Flash | SRAM | WiFi | BLE | Price | SDK Compatibility |
|---|---|---|---|---|---|---|---|
| **Pico W** (current) | RP2040 | 2MB | 264KB | Yes | Yes | ~$6 | Pico SDK (current) |
| **Pico 2 W** | RP2350 | 4MB | 520KB | Yes | BLE 5.2 | ~$7.50 | Pico SDK 2.x (backwards-compatible) |
| **Adafruit Feather RP2040** | RP2040 | 8MB | 264KB | No | No | ~$12 | Pico SDK (compatible) |
| **SparkFun Thing Plus RP2040** | RP2040 | 16MB | 264KB | No | No | ~$18 | Pico SDK (compatible) |
| **Pimoroni Pico Plus 2 W** | RP2350 | **16MB** | 520KB + **8MB PSRAM** | **Yes** | **BLE 5.2** | ~$14 | Pico SDK 2.x (compatible) |

**Key findings:**
- No RP2040/RP2350 board ships with more than 16MB onboard flash. NAND (100+ MB) is always an external add-on — microcontroller boards are sized for firmware, not bulk storage.
- The **Pimoroni Pico Plus 2 W** is the standout: 16MB flash (4x Pico 2 W), 8MB PSRAM for runtime data, WiFi + BLE, same RP2350 chip. At ~$14 it's the most flash you can get without external hardware.
- The Adafruit and SparkFun boards lack WiFi/BLE, which blocks peer discovery — they're not viable for Dilder without an external wireless module.
- The **Pico 2 W** remains the best value for the standard roadmap at ~$7.50.

#### Power Consumption Comparison

| Board | Active (WiFi off) | Active (WiFi on) | Deep Sleep | Notes |
|---|---|---|---|---|
| **Pico W** (current) | ~28mA | ~80mA | ~1.0mA | Baseline |
| **Pico 2 W** | ~32mA | ~85mA | ~0.7mA | Slightly higher active, better sleep |
| **Adafruit Feather RP2040** | ~25mA | N/A (no WiFi) | ~1.0mA | Similar to Pico W (same RP2040) |
| **SparkFun Thing Plus RP2040** | ~25mA | N/A (no WiFi) | ~1.0mA | Similar to Pico W (same RP2040) |
| **Pimoroni Pico Plus 2 W** | ~35–40mA | ~90–100mA | ~0.8–1.0mA | Slightly higher due to PSRAM (continuous refresh ~2–5mA) |

The Pimoroni Pico Plus 2 W draws slightly more power than the Pico 2 W because the 8MB PSRAM requires periodic refresh cycles even when idle. Estimated battery life impact:

| Board | 1000mAh battery (Tamagotchi mode) |
|---|---|
| **Pico W** | ~6.8 days |
| **Pico 2 W** | ~6.4 days |
| **Pimoroni Pico Plus 2 W** | ~5.5–6.0 days |

The ~0.5–1 day difference from PSRAM overhead is minor. If 16MB onboard flash eliminates the need for an external NAND chip (which itself draws ~5mA during reads), the Pimoroni board may actually break even on power.

#### Board Recommendation for Flash

- **Standard path:** Pico 2 W (~$7.50) — 4MB is plenty for the current roadmap. Add external NAND later only if needed.
- **Maximum onboard flash:** Pimoroni Pico Plus 2 W (~$14) — 16MB flash + 8MB PSRAM, WiFi + BLE, same SDK. Worth it if you want headroom without external chips.
- **100+ MB:** Any board above + external W25N NAND chip (~$2–5) or MicroSD (~$5). No board in this class ships with that much built in.

### Option 1: SPI Flash Chip (Best for Dilder)

A dedicated SPI NOR flash chip on the Pico's second SPI bus (SPI0). This is the standard microcontroller approach for external storage.

| Chip | Capacity | Interface | Speed | Package | Price | Source |
|---|---|---|---|---|---|---|
| **W25Q16JV** | 2MB | SPI / Dual / Quad | 133MHz | SOIC-8 | ~$0.40 | AliExpress, LCSC, Mouser |
| **W25Q32JV** | 4MB | SPI / Dual / Quad | 133MHz | SOIC-8 | ~$0.50 | AliExpress, LCSC, Mouser |
| **W25Q64JV** | 8MB | SPI / Dual / Quad | 133MHz | SOIC-8 | ~$0.60 | AliExpress, LCSC, Mouser |
| **W25Q128JV** | **16MB** | SPI / Dual / Quad | 133MHz | SOIC-8 | ~$0.80 | AliExpress, LCSC, Mouser |

**Recommended: W25Q128JV (16MB, ~$0.80).** At this price point there's no reason to go smaller. 16MB is 8x the Pico W's onboard flash.

**Wiring (SPI0):**

| Flash Pin | Function | Pico W GPIO | Pico W Pin # |
|---|---|---|---|
| CS | Chip Select | GP17 | 22 |
| CLK | SPI Clock | GP18 (SPI0 SCK) | 24 |
| DI (MOSI) | Data In | GP19 (SPI0 TX) | 25 |
| DO (MISO) | Data Out | GP16 (SPI0 RX) | 21 |
| WP | Write Protect | 3V3 (tied high) | 36 |
| HOLD | Hold | 3V3 (tied high) | 36 |
| VCC | Power | 3V3 | 36 |
| GND | Ground | GND | 38 |

**GPIO cost:** 4 pins (GP16–GP19), using SPI0 which is currently free. Leaves 10+ GPIO still available.

**Software:** The Pico SDK includes `hardware_spi` for raw SPI access. Winbond W25Q chips use a standard command set (read: `0x03`, write: `0x02`, erase: `0x20`). A simple read/write driver is ~100 lines of C. Community libraries exist (e.g., `pico-w25q`).

**Breadboard note:** SOIC-8 is a surface-mount package (not breadboard-friendly). For prototyping, use a **SOIC-8 to DIP breakout board** (~$0.50 for a pack of 10) or buy a **pre-mounted module** (see below).

### Option 2: SPI Flash Module (Breadboard-Friendly)

Pre-assembled breakout boards with a W25Q chip already soldered, with DIP header pins for direct breadboard use.

| Module | Capacity | Price | Notes |
|---|---|---|---|
| W25Q32 breakout (generic) | 4MB | ~$1.50–2.50 | Common on AliExpress, 6-pin or 8-pin DIP |
| W25Q128 breakout (generic) | 16MB | ~$2.00–3.50 | Same form factor, just larger chip |
| Adafruit SPI Flash (W25Q128) | 16MB | ~$5.95 | Higher quality, well-documented, STEMMA QT option |

**Recommended for prototyping: Generic W25Q128 breakout (~$2.50).** Same wiring as Option 1, but plugs directly into the breadboard. Upgrade to the bare SOIC-8 chip for the final PCB.

### Option 3: SPI NAND Flash (100+ MB)

For high-capacity storage without an SD card, SPI NAND flash chips offer 128MB–1GB in the same SOIC-8 package as the NOR chips above. Same SPI0 wiring, same pinout — just a different command set and page-based access.

| Chip | Capacity | Interface | Speed | Package | Price | Source |
|---|---|---|---|---|---|---|
| **W25N512GV** | 64MB | SPI / Quad | 104MHz | SOIC-8 | ~$1.00–1.50 | AliExpress, LCSC, Mouser |
| **W25N01GV** | **128MB** | SPI / Quad | 104MHz | SOIC-8 | ~$1.50–2.50 | AliExpress, LCSC, Mouser |
| **W25N02KV** | **256MB** | SPI / Quad | 104MHz | SOIC-8 | ~$3.00–4.00 | AliExpress, LCSC, Mouser |
| **W25M02GV** | **256MB** | SPI / Quad | 104MHz | SOIC-8 (stacked die) | ~$4.00–5.00 | AliExpress, LCSC, Mouser |
| **W25N04KV** | **512MB** | SPI / Quad | 104MHz | SOIC-8 | ~$5.00–7.00 | LCSC, Mouser |
| **W25N01GV x2 (stacked)** | **256MB** | SPI / Quad | 104MHz | 2x SOIC-8 (shared bus, separate CS) | ~$3.00–5.00 | Use 1 extra GPIO for second CS |

**Wiring:** Identical to the NOR flash chips (Option 1) — same 4 GPIO on SPI0.

**Breakout modules:** Less common than NOR breakouts, but generic W25N01GV modules exist on AliExpress for ~$2.50–4.00. For breadboard prototyping, a bare chip on a SOIC-8 to DIP adapter (~$0.50) also works.

#### NOR vs NAND — Key Differences

| | NOR (W25Q series) | NAND (W25N series) |
|---|---|---|
| Max affordable capacity | ~16–32MB | **128MB–512MB** |
| Read access | Byte-addressable, random access | Page-based (2KB pages) |
| Write | Byte/page program | Page program only (2KB) |
| Erase granularity | 4KB sector erase | **128KB block erase** |
| Bad blocks | None — every block guaranteed | **Must manage bad block table** |
| Read speed | Fast random reads | Fast sequential, slower random |
| Driver complexity | Simple (~100 lines of C) | Moderate (~300–500 lines, need bad block management) |
| Wear leveling | Not needed at low write rates | **Recommended** — NAND blocks wear faster |

**Software:** No Pico SDK built-in support for NAND. You need a driver that handles:
1. Page-based read/write (2KB aligned)
2. Bad block table (BBT) — scan on first boot, skip known-bad blocks
3. Optional wear leveling if writes are frequent (a simple block rotation scheme is sufficient)

This is ~300–500 lines of C — more work than NOR but well within reach. The dhara library (open-source NAND FTL) is a lightweight option that handles bad blocks and wear leveling in ~1,500 lines of C.

**Best for:** Large asset storage (sound samples, sprite libraries, extensive creature databases) where you need 100+ MB but want to avoid the SD card form factor and filesystem overhead.

### Option 4: MicroSD Card (Simplest Path to 100+ MB)

An SD card module communicates over SPI and provides gigabytes of storage. The easiest way to get massive capacity with the least software complexity for large storage.

| Module | Capacity | Price | Source |
|---|---|---|---|
| Generic MicroSD SPI module | — (card-dependent) | ~$1.00–2.00 (module only) | AliExpress, Amazon |
| + MicroSD card (8GB) | 8GB (8,192MB) | ~$3.00–4.00 | Amazon, any retailer |
| + MicroSD card (32GB) | 32GB (32,768MB) | ~$4.00–6.00 | Amazon, any retailer |
| **Total (module + 8GB card)** | **8GB** | **~$4.00–6.00** | |

**Wiring:** Same as SPI flash (4 GPIO on SPI0). Slightly higher power draw (~20–30mA during read/write vs ~5mA for NAND flash).

**Software:** Requires a FAT filesystem library (FatFS). Well-documented for the Pico SDK — the `pico-extras` repo includes an SD card SPI example. More setup than raw NOR but less custom code than NAND (FatFS is battle-tested and handles all the block management internally).

**Advantages over NAND:**
- PC-readable — pop the card out and browse files on any computer
- Swappable — upgrade capacity by swapping cards
- No bad block management — the SD card controller handles this internally
- FatFS is a proven library vs. writing a custom NAND driver

**Disadvantages:**
- Physically larger — the SD module adds ~24x18mm to the board footprint
- Higher power draw (~20–30mA active vs ~5mA for NAND)
- Slightly slower random access due to FAT filesystem overhead
- Moving part (removable card) — less robust for a handheld device

### Comparison Summary

| Option | Capacity | Cost | GPIO | Power (active) | Breadboard Ready | Complexity | Best For |
|---|---|---|---|---|---|---|---|
| **Pico 2 W upgrade** | 4MB (+2MB) | ~$1.50 | 0 | +4mA | Yes | None | First step — do this regardless |
| **Pimoroni Pico Plus 2 W** | **16MB onboard** | ~$14 | 0 | +7–12mA | Yes | None | Max onboard flash + PSRAM |
| **W25Q128 NOR chip** | +16MB external | ~$0.80 | 4 (SPI0) | +5mA (read) | No (needs breakout) | Low | Final PCB, up to 16MB |
| **W25Q128 NOR breakout** | +16MB external | ~$2.50 | 4 (SPI0) | +5mA (read) | Yes | Low | Prototyping, up to 16MB |
| **Adafruit SPI Flash** | +16MB external | ~$5.95 | 4 (SPI0) | +5mA (read) | Yes | Low | Best documentation |
| **W25N01GV NAND chip** | **+128MB external** | ~$1.50–2.50 | 4 (SPI0) | +5mA (read) | No (needs breakout) | Medium | 100+ MB on final PCB |
| **W25N02KV NAND chip** | **+256MB external** | ~$3.00–4.00 | 4 (SPI0) | +5mA (read) | No (needs breakout) | Medium | 256MB on final PCB |
| **W25N04KV NAND chip** | **+512MB external** | ~$5.00–7.00 | 4 (SPI0) | +5mA (read) | No (needs breakout) | Medium | Maximum NAND capacity |
| **MicroSD module + 8GB** | **+8GB external** | ~$4.00–6.00 | 4 (SPI0) | +20–30mA (read) | Yes | Medium | Easiest 100+ MB, PC-readable |
| **MicroSD module + 32GB** | **+32GB external** | ~$5.00–8.00 | 4 (SPI0) | +20–30mA (read) | Yes | Medium | Maximum cheap storage |

### External Flash Power Consumption

| Storage Type | Active Read | Active Write | Standby | Notes |
|---|---|---|---|---|
| **NOR flash (W25Q)** | ~5mA | ~10–15mA | <1µA | Near-zero idle draw, brief write spikes |
| **NAND flash (W25N)** | ~5mA | ~10–15mA | <1µA | Similar to NOR; writes are page-based (2KB chunks) |
| **MicroSD card** | ~20–30mA | ~30–50mA | ~0.1–0.2mA | Highest draw; SD controller always partially active |
| **PSRAM (Pimoroni board)** | ~2–5mA | ~2–5mA | ~2–5mA (refresh) | Always-on refresh is the cost — no true standby |

For Tamagotchi mode (mostly sleeping, brief bursts of activity), NOR and NAND flash are effectively free — standby is <1µA. MicroSD costs ~0.1–0.2mA even when idle, which adds ~0.1 day battery drain on 1000mAh. PSRAM's constant refresh is the most significant but still minor (~0.5–1 day impact).

### Recommendation

1. **Now:** Don't worry about it. The 2MB onboard flash has ~1.5MB of headroom — more than enough for the current roadmap including breeding.
2. **When upgrading the board:** Move to the **Pico 2 W** for 4MB flash at ~$1.50 extra cost.
3. **If you want max onboard flash:** The **Pimoroni Pico Plus 2 W** (~$14) gives 16MB flash + 8MB PSRAM with no external wiring. ~0.5–1 day battery life trade-off from PSRAM refresh.
4. **If you need up to 16MB external:** Add a **W25Q128 NOR breakout** (~$2.50) for prototyping, bare chip (~$0.80) for the final PCB. Simplest driver, no bad block headaches, near-zero power impact.
5. **If you need 100+ MB:** Two viable paths:
   - **MicroSD module + card (~$5)** — easiest software (FatFS), PC-readable, swappable. Highest power draw (+20–30mA active). Best if form factor allows.
   - **W25N01GV NAND chip (~$2)** — smaller footprint, lower power (+5mA active, <1µA standby), no moving parts. Better for a compact handheld, but requires a custom NAND driver with bad block management.

Total cost for maximum compact storage: **~$5.50** (Pico 2 W upgrade + W25N02KV NAND = 4MB onboard + 256MB external = 260MB total, no SD card slot needed, +5mA active draw only during reads).

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
