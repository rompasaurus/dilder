---
date: 2026-04-15
authors:
  - rompasaurus
categories:
  - Hardware
  - PCB Design
slug: esp32-s3-pcb-design
---

# From RP2040 to ESP32-S3 — Designing the Dilder PCB

The breadboard era is ending. After weeks of jumper wires, borrowed breakout boards, and firmware running on a Pico W, it's time to design a real PCB — a single board that holds everything the Dilder needs. And in the process, we swapped the entire MCU.

<!-- more -->

## Why We Left the RP2040

The RP2040 served us well for prototyping. It's cheap, it boots instantly, and the Pico W made breadboard development painless. But when we sat down to design a custom PCB, the problems became obvious:

- **No built-in flash** — the RP2040 needs an external QSPI flash chip, crystal oscillator, and a handful of decoupling caps just to wake up
- **No Bluetooth** — the Pico W has WiFi, but adding BLE means an external module
- **RF certification** — designing an antenna or integrating an uncertified radio module is a project unto itself

We looked at the bill of materials for an RP2040-based custom board and counted 7+ passive components just for the MCU subsystem. There had to be a better way.

## Enter the ESP32-S3-WROOM-1-N16R8

The ESP32-S3-WROOM-1-N16R8 is, frankly, overkill for a Tamagotchi. And that's exactly why we picked it.

- **16MB flash + 8MB PSRAM** — the maxed-out variant, room for every quote Jamal will ever have
- **WiFi + Bluetooth 5 (LE)** — both radios built in, pre-certified
- **Dual-core 240MHz Xtensa LX7** — more power than we need, but nice to have headroom
- **USB OTG** — native USB, no FTDI chip needed
- **44 GPIO pins** — more than enough for our peripherals

The module is a complete system: flash, PSRAM, crystal, antenna, RF matching network, and shielding can — all in one package. Drop it on a PCB, add power, and you have a working computer. That alone eliminated 7 components from the BOM.

## The PCB Design Journey

### KiCad Setup and JLCPCB Integration

We started by setting up KiCad 9 with the JLCPCB fabrication plugin, which lets you export Gerbers in exactly the format JLCPCB expects and includes their parts library for component sourcing. A setup script (`setup-kicad-jlcpcb.py`) automates the installation so anyone following along can replicate the toolchain.

### Component Selection

The full BOM came together around the ESP32-S3:

| Component | Purpose |
|-----------|---------|
| ESP32-S3-WROOM-1-N16R8 | MCU — WiFi, BLE, flash, PSRAM |
| LIS2DH12TR | 3-axis accelerometer (built-in pedometer) |
| AMS1117-3.3 | 3.3V LDO regulator |
| TP4056 | LiPo charging IC (USB-C input) |
| DW01A + FS8205A | Battery protection (over-discharge, over-current) |
| USB-C connector | Charging and programming |
| 5-way joystick | Navigation input |
| 8-pin JST-SH connector | ePaper display connection |

27 components total, including passives. Compare that to the ~34+ we would have needed with a bare RP2040.

### The Schematic

The schematic was built in sections: power (USB-C to TP4056 charger to battery protection to AMS1117 LDO), MCU (ESP32-S3 with boot/reset buttons and USB data lines), peripherals (LIS2DH12TR on I2C, joystick on GPIO, ePaper connector with SPI signals). Net labels keep the schematic readable — no rats' nest of wires crossing the sheet.

### Board Layout — Iteration After Iteration

Layout is where the real decisions happen. We went through multiple placement iterations, optimizing based on signal flow, antenna requirements, and mechanical constraints:

- **ESP32-S3 at the top** — antenna overhanging the board edge for best RF performance
- **LIS2DH12TR below-left** — close to the MCU for clean I2C routing
- **ePaper connector below-right** — 8-pin JST-SH header for the display ribbon cable
- **Power section in the middle** — AMS1117, TP4056, battery protection clustered together
- **5-way joystick centered above USB-C at the bottom** — ergonomic thumb position
- **USB-C at the very bottom** — charging port accessible when held in hand

Component placement was optimized based on which side of the ESP32-S3 module each GPIO pin exits, minimizing trace crossings.

## The Antenna Keep-Out Challenge

The ESP32-S3-WROOM-1 has a PCB antenna that extends beyond the module's footprint. Espressif's hardware design guidelines are strict: **no copper (traces, pours, or planes) under or near the antenna area**, on any layer. No components either. The antenna needs to overhang the board edge into free space.

This single requirement drove a major decision: we needed a **4-layer PCB**. With only 2 layers, routing traces around the antenna keep-out zone while still connecting all the GPIO pins would have been nearly impossible without making the board much larger. Four layers give us:

- **Top** — signal traces and components
- **Inner 1** — continuous ground plane (critical for RF and signal integrity)
- **Inner 2** — power plane (3.3V distribution)
- **Bottom** — additional signal routing

The unbroken ground plane on Inner 1 is especially important — it provides the RF ground reference the antenna needs and keeps return current paths clean for high-speed signals.

## The Display Connector Decision

This one caused some head-scratching. The Waveshare 2.13" ePaper display we've been using comes in two form factors:

1. **Pico-ePaper-2.13** — a Pico-native module with a 40-pin header that plugs directly onto the Pico W (what we've been using for prototyping)
2. **Waveshare 2.13" e-Paper HAT** — a Raspberry Pi HAT version with a 24-pin FPC connector to the raw display panel

For the custom PCB, we considered putting a raw 24-pin FPC connector on the board to connect directly to the display's flex cable. But that would mean:

- Sourcing and routing a 24-pin FPC connector (tight pitch, tricky to solder)
- Handling the display driver signals directly
- Losing compatibility with the HAT's built-in level shifting and connector

Instead, we went with an **8-pin JST-SH connector** that carries only the SPI signals (MOSI, CLK, CS, DC, RST, BUSY) plus power and ground. This connects to the Waveshare HAT via its 8-pin ribbon cable header. Simpler routing, proven signal integrity, and we can swap display modules without redesigning the PCB.

## FreeRouting — The Autorouter Experiment

With 27 components placed, we needed to route the traces. KiCad has a built-in interactive router, but we also tried **FreeRouting**, an open-source autorouter, to see if it could handle the job.

Results: mixed. FreeRouting can solve simple boards quickly, but our 4-layer design with antenna keep-out zones, ground plane requirements, and mixed-signal routing (SPI, I2C, USB, analog) pushed it past its comfort zone. The autorouter would complete routes but produce suboptimal results — traces taking unnecessary detours, vias placed in awkward locations, ground plane integrity compromised.

The lesson: autorouters are useful for getting a rough first pass or solving simple boards, but for a design like this, **interactive routing in KiCad is the way to go**. You need human judgment for antenna keep-out compliance, controlled impedance traces for USB, and clean power distribution.

## Reference Designs That Helped

We didn't design in a vacuum. Three open-source reference designs were particularly useful:

- **Olimex ESP32-S3-DevKit-Lipo** — clean power management with LiPo charging, open hardware with full KiCad files
- **atomic14 ESP32-S3 boards** — minimal designs that show what you can strip away and still have a working system
- **UnexpectedMaker FeatherS3** — excellent example of antenna placement and 4-layer routing for ESP32-S3

Studying these designs confirmed our approach and caught potential mistakes before they were committed to copper.

## Where We Are Now

The board sits at **45mm x 80mm**, 4-layer, with all 27 components placed and ready for routing. The design lives in `hardware-design/Board Design kicad/` with:

- Full KiCad project (`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`)
- Python build scripts that place components programmatically via KiCad's pcbnew API
- Research documentation covering module specs, antenna requirements, and design decisions

The PCB can be regenerated from scratch by running the build script — every component position, every design rule is captured in code, not just in KiCad's GUI state.

## What's Next

1. **Interactive routing in KiCad** — manually route all traces with proper design rules (antenna keep-out, USB impedance, power trace widths)
2. **Design rule check (DRC)** — verify the board passes KiCad's and JLCPCB's manufacturing constraints
3. **Generate Gerbers** — export fabrication files in JLCPCB format
4. **Order from JLCPCB** — ship to Germany, wait for boards
5. **Assemble and test** — solder components, flash firmware, see if the octopus boots on custom hardware

From a breadboard held together with optimism and jumper wires to a real PCB. The octopus is getting a proper home.
