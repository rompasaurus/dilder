# Materials List

All components needed to build a Dilder test bench. This list assumes you are building a breadboard prototype — no soldering required at this stage.

---

## Development Platform

**Phase 1 (current):** Raspberry Pi Pico W with MicroPython. Cheap, fast to iterate, instant boot.

**Future (Phase 5):** Raspberry Pi Zero WH with Linux. Upgrade when you need a filesystem, SSH, or more compute.

---

## Essential Components

Order these first. Everything else can wait.

| Item | Est. Cost | Notes |
|------|-----------|-------|
| Raspberry Pi Pico W | ~€6 | RP2040 dual-core, 264KB SRAM, 2MB flash, WiFi + BLE. Micro-USB for power and programming. |
| Waveshare Pico-ePaper-2.13 | ~€15 | SSD1680 driver, 250×122px, black/white. Pico-native module — plugs directly onto the Pico W's 40-pin header, or connect via **8-pin breakout header** with jumper wires for breadboard use. |
| Micro-USB cable | ~€2 | Powers the Pico W and provides serial connection to your dev machine. |
| Half-size breadboard | ~€4 | For wiring buttons and display connections. |
| Jumper wire kit (M-F and M-M) | ~€4 | Needed for breadboard wiring (joystick, GPS, HC-SR04). Display can plug directly onto Pico or use F-M wires from its 8-pin breakout header. |
| 6×6mm tactile buttons (pack of 20) | ~€3 | Various stem heights. Snap-on colored caps recommended for identifying buttons. |
| DollaTek 5-Way Navigation Button Module | ~€8.17 (5-pack) | [B07HBPW3DF](https://www.amazon.de/dp/B07HBPW3DF) — 5-direction rocker joystick (Up/Down/Left/Right/Center). GPIO digital input, active LOW. Drop-in replacement for the 5 tactile buttons above. See [Joystick Wiring Guide](joystick-wiring.md). |
| **Subtotal** | **~€42** | |

---

## Useful Extras

Not required to get started, but helpful.

| Item | Est. Cost | Notes |
|------|-----------|-------|
| Pico WH (pre-soldered headers) | ~€7 | Easier breadboard use — no header soldering needed. Either Pico W or WH works. |
| 10kΩ resistor assortment | ~€2 | External pull-ups as backup if internal GPIO pull-ups cause issues. |
| Multimeter | ~€12–20 | Debugging wiring continuity and voltage. Useful throughout the build. |
| Soldering iron + solder | ~€20–40 | Not needed for the test bench, but you'll want it for permanent connections later. |

---

## Battery Power (Phase 6)

Order these when you're ready to move off USB power. See [Hardware Research](https://github.com/rompasaurus/dilder/blob/main/docs/hardware-research.md#battery--power) for the full analysis including battery life estimates and wiring diagrams.

| Item | Est. Cost | Notes |
|------|-----------|-------|
| 3.7V LiPo battery (1000mAh, recommended) | ~€8 | [InnCraft Energy 503450](https://www.amazon.de/dp/B0F88RQX7C) — Molex 51021-0200 1.25mm connector, 51×34×5mm. Wires directly to VSYS — no boost converter needed. Provides ~6.8 days in Tamagotchi mode. See [Battery Wiring Guide](battery-wiring.md). |
| 3.7V LiPo battery (2000mAh, max runtime) | ~€10 | 60×40×7mm. ~13.6 days in Tamagotchi mode. Verify enclosure clearance (7mm thick). |
| TP4056 charging module (budget) | ~€1.50 | USB charging with over-discharge protection. Output wires to VSYS pin. |
| Adafruit PowerBoost 500C (upgrade) | ~€16 | LiPo charger + 5V boost + load sharing (use device while charging). Has low-battery output pin. |

!!! tip "No boost converter needed"
    The Pico W's VSYS pin accepts 1.8–5.5V. A 3.7V LiPo sits right in range — just wire LiPo(+) to VSYS and LiPo(-) to GND. Battery voltage monitoring is built in via GPIO29 (ADC3).

---

## Component Specs Reference

### Raspberry Pi Pico W

| Spec | Value |
|------|-------|
| Chip | RP2040 (dual-core ARM Cortex-M0+ @ 133MHz) |
| RAM | 264KB SRAM |
| Flash | 2MB onboard QSPI |
| Wi-Fi | 802.11n 2.4GHz |
| Bluetooth | BLE 5.2 |
| GPIO | 26 multi-function pins |
| USB | Micro-USB 1.1 (power + data) |
| ADC | 3 external channels (12-bit) |
| Dimensions | 51 × 21 × 3.9mm |
| Firmware | C/C++ via Pico SDK |

Full reference: [Pico W Reference](../reference/pico-w.md)

### Waveshare Pico-ePaper-2.13

| Spec | Value |
|------|-------|
| Display size | 2.13 inches |
| Resolution | 250 × 122 pixels |
| Active area | 48.55 × 23.71mm |
| Colors | Black and white |
| Driver IC | SSD1680 |
| Interface | SPI1 (4-wire, Mode 0) |
| Power | VSYS (1.8-5.5V, onboard regulator) |
| Form factor | Pico-native — 40-pin female header plugs directly onto Pico W |
| Full refresh time | ~2 seconds |
| Partial refresh time | ~0.3 seconds |
| Standby current | < 0.01µA |
| Recommended refresh interval | ≥ 180 seconds for full refresh |
| Board dimensions | 65 × 30.2mm |

!!! warning "Version check"
    This guide targets the **V3** revision (SSD1680 driver). Confirm your version by checking the PCB silkscreen on the back of the display board.

Full reference: [Waveshare e-Paper Reference](../reference/waveshare-eink.md)

---

## Where to Buy

| Retailer | Notes |
|----------|-------|
| [Raspberry Pi official store](https://www.raspberrypi.com/products/raspberry-pi-pico/) | Pico W / Pico WH |
| [Waveshare official store](https://www.waveshare.com) | Best for the e-ink display |
| [Amazon DE / UK](https://www.amazon.de/-/en/gp/product/B07Q5PZMGT) | Original linked e-Paper product |
| [Pimoroni](https://shop.pimoroni.com) | Good UK/EU source for Pico W and accessories |
| [Adafruit](https://www.adafruit.com) | US source, good component quality |
| [AliExpress](https://www.aliexpress.com) | Cheapest for breadboards, buttons, and jumper wire kits |
