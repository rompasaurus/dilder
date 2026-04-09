# Materials List

All components needed to build a Dilder test bench. This list assumes you are building a breadboard prototype — no soldering required at this stage.

---

## Essential Components

Order these first. Everything else can wait.

| Item | Est. Cost | Notes |
|------|-----------|-------|
| Raspberry Pi Zero WH | ~€15 | **Get the "WH" variant** — pre-soldered 40-pin GPIO header. Zero 2 WH preferred if available (quad-core). |
| Waveshare 2.13" e-Paper HAT V3 | ~€15 | SSD1680 driver, 250×122px, black/white. Plugs directly onto Pi Zero header. |
| Micro SD card (16GB+) | ~€6 | Class 10 or better. For Raspberry Pi OS Lite. |
| Micro-USB power supply (5V 2.5A) | ~€9 | Any decent phone charger works during development. |
| Half-size breadboard | ~€4 | For wiring buttons without soldering. |
| Jumper wire kit (M-F and M-M) | ~€4 | Assorted lengths. M-F for GPIO to breadboard, M-M for breadboard connections. |
| 6×6mm tactile buttons (pack of 20) | ~€3 | Various stem heights. Snap-on colored caps recommended for identifying buttons. |
| **Subtotal** | **~€56** | |

---

## Useful Extras

Not required to get started, but helpful.

| Item | Est. Cost | Notes |
|------|-----------|-------|
| GPIO T-Cobbler breakout + ribbon cable | ~€7 | Labels all GPIO pins on the breadboard. Eliminates pin-counting errors. |
| 10kΩ resistor assortment | ~€2 | External pull-ups as backup if internal GPIO pull-ups cause issues. |
| Multimeter | ~€12–20 | Debugging wiring continuity and voltage. Useful throughout the build. |
| Soldering iron + solder | ~€20–40 | Not needed for the test bench, but you'll want it for permanent connections later. |

---

## Battery Power (Phase 6)

Order these when you're ready to move off USB power.

| Item | Est. Cost | Notes |
|------|-----------|-------|
| Adafruit PowerBoost 500C | ~€18 | LiPo charger + 5V boost regulator with load sharing. Best option for clean power. |
| 3.7V LiPo battery (1200mAh) | ~€10 | JST-PH connector. Fits the battery bay reserved in the enclosure. |
| Budget alternative: TP4056 + MT3608 | ~€2–3 | More wiring, more tuning, lower cost. Good for experienced builders. |

---

## Component Specs Reference

### Raspberry Pi Zero WH

| Spec | Value |
|------|-------|
| SoC | BCM2835 (ARMv6, 1GHz single-core) |
| RAM | 512MB LPDDR2 |
| Wi-Fi | 802.11 b/g/n 2.4GHz |
| Bluetooth | 4.1 BLE |
| GPIO | 40-pin header (pre-soldered on WH) |
| USB | 1× micro-USB data, 1× micro-USB power |
| Storage | micro SD |
| Dimensions | 65 × 30 × 5mm |

!!! note "Pi Zero 2 W"
    The Zero 2 W (BCM2710, quad-core ARMv8) is a drop-in replacement with significantly more CPU headroom. Everything in this guide applies to both.

### Waveshare 2.13" e-Paper HAT V3

| Spec | Value |
|------|-------|
| Display size | 2.13 inches |
| Resolution | 250 × 122 pixels |
| Active area | 48.55 × 23.71mm |
| Colors | Black and white |
| Driver IC | SSD1680 |
| Interface | SPI (4-wire, Mode 0) |
| Operating voltage | 3.3V / 5V (onboard translator) |
| Full refresh time | ~2 seconds |
| Partial refresh time | ~0.3 seconds |
| Standby current | < 0.01µA |
| Recommended refresh interval | ≥ 180 seconds for full refresh |
| Board dimensions | 65 × 30.2mm |

!!! warning "Version check"
    This guide targets the **V3** revision (SSD1680 driver). The V4 revision exists with a different driver IC (SSD1680Z8). Confirm your version before running demo code — V3 and V4 require different driver files.

    To identify: check the PCB silkscreen or the Waveshare product page. The V3 box says "2.13inch e-Paper HAT (C) V3" or similar.

---

## Where to Buy

| Retailer | Notes |
|----------|-------|
| [Waveshare official store](https://www.waveshare.com) | Best for the e-ink display — ensure you get V3 specifically |
| [Amazon DE / UK](https://www.amazon.de/-/en/gp/product/B07Q5PZMGT) | Original linked product |
| [Pimoroni](https://shop.pimoroni.com) | Good UK/EU source for Pi Zero WH |
| [Adafruit](https://www.adafruit.com) | US source, good component quality |
| [AliExpress](https://www.aliexpress.com) | Cheapest for breadboards, buttons, and jumper wire kits |
