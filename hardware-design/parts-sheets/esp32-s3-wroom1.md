# ESP32-S3-WROOM-1-N16R8 — Main MCU Module

## Table of Contents

- [Quick Reference](#quick-reference)
- [What Is This Part?](#what-is-this-part)
- [The Technology Inside](#the-technology-inside)
  - [The CPU — Dual-Core Xtensa LX7](#the-cpu--dual-core-xtensa-lx7)
  - [Memory — Flash and PSRAM](#memory--flash-and-psram)
  - [WiFi — How It Talks to the Internet](#wifi--how-it-talks-to-the-internet)
  - [Bluetooth Low Energy (BLE 5.0)](#bluetooth-low-energy-ble-50)
  - [The Antenna](#the-antenna)
  - [USB On-The-Go (OTG)](#usb-on-the-go-otg)
- [Key Specifications](#key-specifications)
- [Pin Usage on Dilder Board](#pin-usage-on-dilder-board)
- [Power Supply Requirements](#power-supply-requirements)
- [Antenna Keep-Out Zone](#antenna-keep-out-zone)
- [Boot Modes](#boot-modes)
- [Why This Module Instead of a Bare Chip](#why-this-module-instead-of-a-bare-chip)
- [History and Background](#history-and-background)
- [Datasheet and Sources](#datasheet-and-sources)

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Manufacturer** | Espressif Systems (Shanghai, China) |
| **Part Number** | ESP32-S3-WROOM-1-N16R8 |
| **Function** | System-on-Module: dual-core MCU + WiFi + BLE 5.0 |
| **Package** | Module, 18 x 25.5 x 3.1mm |
| **LCSC** | [C2913196](https://www.lcsc.com/product-detail/C2913196.html) |
| **Price (qty 5)** | ~$2.80 |
| **Dilder ref** | U1 |

---

## What Is This Part?

The ESP32-S3-WROOM-1 is a **complete computer on a small metal-canned module**. Inside the 18x25.5mm package is:

- A dual-core processor running at 240 MHz
- 512 KB of fast SRAM
- 16 MB of flash storage (like a tiny SSD — holds your program)
- 8 MB of PSRAM (extra RAM for images, buffers, data)
- A WiFi radio (2.4 GHz, same as your home router)
- A Bluetooth Low Energy radio
- A PCB antenna (the trace pattern at one end of the module)
- A 40 MHz crystal oscillator (the "heartbeat" clock)
- All the power regulation and filtering needed internally

You just give it 3.3V power and connect your peripherals to its GPIO pins. No external flash, no external crystal, no antenna — it's all inside.

In the Dilder, this is the brain. It runs the virtual pet firmware, drives the e-ink display, reads the joystick and accelerometer, manages sleep/wake cycles, and handles USB communication.

---

## The Technology Inside

### The CPU — Dual-Core Xtensa LX7

The ESP32-S3 uses two **Xtensa LX7** cores designed by Cadence (licensed by Espressif). These are 32-bit RISC processors — "RISC" means Reduced Instruction Set Computer, which means each CPU instruction does one simple thing very fast, rather than having complex multi-step instructions.

**What dual-core means in practice:** One core can handle WiFi/BLE protocol processing while the other runs your application code, so radio operations don't stall your display updates or sensor readings. In FreeRTOS (the real-time OS the Dilder runs), you can pin tasks to specific cores.

**240 MHz** means the CPU executes 240 million clock cycles per second. For comparison, the original Arduino Uno runs at 16 MHz — this is 15x faster. The RP2040 (the chip we replaced) runs at 133 MHz dual-core, so the ESP32-S3 is roughly 1.8x faster per core.

The LX7 also includes **vector instructions (SIMD)** for AI/ML workloads — Espressif markets this for on-device neural networks, though the Dilder doesn't use this feature.

### Memory — Flash and PSRAM

**Flash (16 MB):** Non-volatile storage — keeps your data when power is off. This holds the compiled firmware, any stored images, fonts, save data, and OTA update packages. 16 MB is enormous for an embedded device. The firmware for the Dilder is currently under 1 MB, leaving plenty of room for assets and future features.

Flash connects to the CPU via **Quad-SPI (QSPI)** — a 4-lane serial bus that can transfer data at up to 80 MHz, giving about 40 MB/s throughput. This is all internal to the module; you don't need to wire anything.

**PSRAM (8 MB):** Pseudo-Static RAM — acts like regular RAM but is actually DRAM (Dynamic RAM) with a built-in refresh controller that makes it look like SRAM to the CPU. It's slower than the internal 512 KB SRAM (accessed via the cache, with some latency) but 16x larger.

PSRAM is critical for the Dilder because the e-ink display framebuffer needs contiguous memory, and the pet animation system loads multiple sprite frames. Without PSRAM, you'd be limited to 512 KB for everything.

The PSRAM connects via **Octal-SPI (OPI)** — an 8-lane bus running at up to 40 MHz for ~40 MB/s throughput.

### WiFi — How It Talks to the Internet

The module includes a complete **802.11 b/g/n** WiFi radio operating at 2.4 GHz. This is the same WiFi standard used by most home devices.

**How WiFi works (simplified):** The radio converts digital data into radio waves at 2.4 billion cycles per second. It modulates these waves (changes their amplitude, phase, or frequency slightly) to encode 1s and 0s. The PCB antenna on the module transmits and receives these waves. A matching radio in your WiFi router decodes the modulation back into data.

**802.11n** adds OFDM (Orthogonal Frequency-Division Multiplexing) — instead of one carrier frequency, the data is split across 52 sub-carriers, each carrying a piece of the data. This is more resistant to interference and allows higher throughput (up to 150 Mbps for a single antenna).

For the Dilder, WiFi enables OTA firmware updates, time synchronization (NTP), and potential future features like WiFi fingerprint-based location estimation.

### Bluetooth Low Energy (BLE 5.0)

BLE is a separate radio protocol that shares the 2.4 GHz band with WiFi but uses much less power. Where classic Bluetooth maintains a continuous connection (like headphones streaming audio), BLE sends short bursts of data and sleeps in between.

**BLE 5.0** improvements over 4.x:
- 2x data rate (2 Mbps vs 1 Mbps)
- 4x range (by trading data rate for sensitivity)
- 8x broadcast capacity (larger advertising packets)

For the Dilder, BLE could enable device-to-device communication (pet interaction), phone app connectivity, or beacon-based proximity features.

The ESP32-S3 can run WiFi and BLE simultaneously using time-division — the radio switches between protocols in microsecond timeslices.

### The Antenna

The module uses a **meandering inverted-F antenna (MIFA)** — a trace pattern etched directly onto the module's PCB. It's the zigzag pattern visible at one end of the module.

**How a PCB antenna works:** A trace of specific length (about 1/4 wavelength of 2.4 GHz ≈ 31mm) acts as a resonant element. Radio energy from the transmitter causes current to flow through the trace, which radiates electromagnetic waves. The meandering (zigzag) pattern fits a 31mm-equivalent electrical length into a smaller physical space.

**Critical rule:** The area under and around the antenna must have no copper on any PCB layer — no traces, no ground plane, no power planes. Copper near the antenna detunes it (changes its resonant frequency) and absorbs radiated energy, reducing range. See the [Antenna Keep-Out Zone](#antenna-keep-out-zone) section.

### USB On-The-Go (OTG)

The ESP32-S3 has a built-in USB 1.1 controller with **On-The-Go** capability. This means:

- It can act as a **USB device** (like a keyboard or serial port) when plugged into a computer
- It could theoretically act as a **USB host** (like plugging a USB device into it)

The USB PHY (Physical Layer) is integrated — the GPIO19 (D-) and GPIO20 (D+) pins connect directly to the USB-C connector with no external components needed. The RP2040 also had native USB, but many older MCUs require an external USB-to-UART bridge chip (like CP2102 or CH340), adding cost and board space.

**USB 1.1** means 12 Mbps maximum data rate. That's plenty for serial console, firmware upload, and USB HID (Human Interface Device) applications.

---

## Key Specifications

| Parameter | Value |
|-----------|-------|
| CPU | Dual-core Xtensa LX7 @ 240 MHz |
| SRAM | 512 KB |
| Flash | 16 MB (integrated, Quad-SPI) |
| PSRAM | 8 MB (integrated, Octal-SPI) |
| WiFi | 802.11 b/g/n, 2.4 GHz, up to 150 Mbps |
| Bluetooth | BLE 5.0 (LE 1M, LE 2M, LE Coded) |
| GPIO | 36 programmable |
| ADC | 2x 12-bit SAR ADC, 20 channels |
| DAC | None (removed in S3 vs original ESP32) |
| SPI | 4x SPI interfaces |
| I2C | 2x I2C interfaces |
| UART | 3x UART interfaces |
| I2S | 2x I2S interfaces (audio) |
| USB | USB 1.1 OTG (native, no external PHY) |
| Operating voltage | 3.0V - 3.6V (3.3V typical) |
| Active current | ~240 mA peak (WiFi TX) |
| Light sleep current | ~240 uA |
| Deep sleep current | ~10 uA (with RTC) |
| Operating temp | -40C to +85C |
| Module dimensions | 18 x 25.5 x 3.1 mm |
| Antenna | PCB antenna (integrated MIFA) |

---

## Pin Usage on Dilder Board

| GPIO | Function | Interface | Direction |
|------|----------|-----------|-----------|
| GPIO3 | e-Paper DC | Digital | Output |
| GPIO4 | Joystick UP | Digital | Input (pull-up) |
| GPIO5 | Joystick DOWN | Digital | Input (pull-up) |
| GPIO6 | Joystick LEFT | Digital | Input (pull-up) |
| GPIO7 | Joystick RIGHT | Digital | Input (pull-up) |
| GPIO8 | Joystick CENTER | Digital | Input (pull-up) |
| GPIO9 | e-Paper CLK | SPI SCK | Output |
| GPIO10 | e-Paper MOSI | SPI MOSI | Output |
| GPIO11 | e-Paper RST | Digital | Output |
| GPIO12 | e-Paper BUSY | Digital | Input |
| GPIO16 | LIS2DH12 SDA | I2C | Bidirectional |
| GPIO17 | LIS2DH12 SCL | I2C | Output |
| GPIO18 | LIS2DH12 INT1 | Interrupt | Input |
| GPIO19 | USB D- | USB | Bidirectional |
| GPIO20 | USB D+ | USB | Bidirectional |
| GPIO46 | e-Paper CS | SPI CS | Output |

**Unused GPIOs:** Many pins remain available for future expansion (audio, additional sensors, debug UART, etc.).

---

## Power Supply Requirements

| Parameter | Value |
|-----------|-------|
| VDD range | 3.0V - 3.6V |
| Typical VDD | 3.3V (from AMS1117-3.3 LDO) |
| Decoupling | 100nF ceramic close to pin 2 (C3) + 10uF bulk (C4) |
| Peak current (WiFi TX) | ~240 mA |
| Typical active current | ~80-100 mA (no radio) |
| Deep sleep | ~10 uA |

The EN (Enable) pin has an internal pull-up but an external 10k resistor (R10) to 3.3V is recommended for noise immunity. Pulling EN low puts the module in reset/power-down state.

---

## Antenna Keep-Out Zone

The PCB antenna at one end of the module **must have a clearance zone** free of copper on ALL layers:

- **No ground plane** under the antenna area
- **No signal traces** under or adjacent to the antenna
- **No components** within the keep-out zone
- The module is placed at the board edge so the antenna overhangs or is flush with the edge

In the Dilder PCB, the module is placed at the top of the board with the antenna extending to the board edge. The ground plane has a cutout under the antenna section.

See Espressif's hardware design guidelines (Section 4.1) for exact dimensions.

---

## Boot Modes

The ESP32-S3 has several boot modes controlled by GPIO0 and GPIO46 at power-on:

| GPIO0 | GPIO46 | Mode |
|-------|--------|------|
| HIGH | Any | Normal boot (run from flash) |
| LOW | Any | Download mode (firmware upload via USB/UART) |

In normal operation, GPIO0 is pulled high internally. To enter download mode for firmware flashing, GPIO0 must be held low during reset. The USB-OTG interface handles this automatically when using `esptool.py` or the ESP-IDF toolchain.

---

## Why This Module Instead of a Bare Chip

The ESP32-S3 is available as both a bare chip (QFN-56, 7x7mm) and pre-built modules like the WROOM-1. The Dilder uses the module because:

| Factor | Bare Chip | WROOM-1 Module |
|--------|-----------|----------------|
| External flash needed | Yes (QSPI flash IC) | No (16 MB built-in) |
| External crystal needed | Yes (40 MHz + caps) | No (built-in) |
| Antenna design needed | Yes (RF engineering) | No (certified antenna) |
| RF certification | Must do yourself ($$$) | Pre-certified (FCC, CE) |
| PCB layers | 4+ recommended | 2 possible (4 preferred) |
| Total BOM cost | Similar after adding parts | ~$2.80 all-in |
| Design complexity | High (impedance matching, etc.) | Low (just connect power + GPIOs) |

The module trades a slightly larger footprint (18x25.5mm vs 7x7mm) for dramatically simpler design. For a first custom PCB, this is the right tradeoff.

---

## History and Background

**Espressif Systems** was founded in 2008 in Shanghai by Teo Swee Ann, a Singaporean engineer. Their first product, the **ESP8266** (2014), was a $2 WiFi-enabled microcontroller that revolutionized IoT by making WiFi affordable for hobby projects. Before the ESP8266, adding WiFi to a project required $20+ modules.

The **ESP32** (2016) added dual-core processing, Bluetooth, and more peripherals. It became the de facto standard for IoT projects.

The **ESP32-S3** (2020) is the third generation, adding:
- Vector instructions for AI/ML
- USB-OTG (no more external USB-UART bridges)
- More GPIO pins
- Better security (secure boot, flash encryption)
- BLE 5.0

The "WROOM-1" designation means it's a module with a PCB antenna (vs "WROOM-1U" which has a U.FL connector for an external antenna). "N16R8" means 16 MB flash (N16) and 8 MB PSRAM (R8).

---

## Datasheet and Sources

- **Local copy:** [manufacturer-datasheets/ESP32-S3-WROOM-1-datasheet.pdf](manufacturer-datasheets/ESP32-S3-WROOM-1-datasheet.pdf)
- **Espressif official datasheet:** [esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)
- **ESP32-S3 Technical Reference Manual:** [esp32-s3_technical_reference_manual_en.pdf](https://www.espressif.com/sites/default/files/documentation/esp32-s3_technical_reference_manual_en.pdf)
- **Hardware Design Guidelines:** [ESP32-S3 Schematic Checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html)
- **LCSC product page:** [C2913196](https://www.lcsc.com/product-detail/C2913196.html)
- **Espressif company:** [espressif.com](https://www.espressif.com)
- **ESP-IDF (development framework):** [github.com/espressif/esp-idf](https://github.com/espressif/esp-idf)
- **Wikipedia — Espressif ESP32:** [en.wikipedia.org/wiki/ESP32](https://en.wikipedia.org/wiki/ESP32)
