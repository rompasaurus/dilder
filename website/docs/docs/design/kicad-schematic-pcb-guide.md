# KiCad Schematic & PCB Design Guide — Dilder Board

A complete, step-by-step walkthrough for designing the Dilder custom PCB in KiCad 10. Written for someone who has never used CAD software before. Every click is explained, every electronics principle is covered when it matters.

By the end of this guide you will have a fabrication-ready 4-layer PCB with an ESP32-S3, LiPo charging, USB-C, ePaper display connector, accelerometer, joystick, and status LEDs.

---

## Table of Contents

1. [Before You Start](#before-you-start)
2. [Part 1 — Project Setup](#part-1--project-setup)
3. [Part 2 — Schematic Design](#part-2--schematic-design)
    - [2.1 USB-C Power Input](#21-usb-c-power-input)
    - [2.2 Reverse Polarity Protection](#22-reverse-polarity-protection-d1-ss34)
    - [2.3 LiPo Charging (TP4056)](#23-lipo-charging-tp4056)
    - [2.4 Battery Protection (DW01A + FS8205A)](#24-battery-protection-dw01a--fs8205a)
    - [2.5 Voltage Regulation (AMS1117-3.3)](#25-voltage-regulation-ams1117-33)
    - [2.6 ESP32-S3-WROOM-1](#26-esp32-s3-wroom-1)
    - [2.7 ePaper SPI Interface](#27-epaper-spi-interface)
    - [2.8 LIS2DH12TR Accelerometer](#28-lis2dh12tr-accelerometer-i2c)
    - [2.9 AHT20 Temperature & Humidity](#29-aht20-temperature--humidity-sensor-i2c)
    - [2.10 BH1750FVI Light Sensor](#210-bh1750fvi-ambient-light-sensor-i2c)
    - [2.11 Joystick & Buttons](#211-joystick--buttons-renumbered-from-29)
    - [2.12 Status LEDs](#212-status-leds)
    - [2.13 Power Symbols & Flags](#213-power-symbols--flags)
4. [Part 3 — Electrical Rules Check (ERC)](#part-3--electrical-rules-check-erc)
5. [Part 4 — PCB Layout](#part-4--pcb-layout)
    - [4.1 Board Setup](#41-board-setup)
    - [4.2 Import Netlist](#42-import-netlist)
    - [4.3 Component Placement](#43-component-placement)
    - [4.4 Routing — Power Traces](#44-routing--power-traces)
    - [4.5 Routing — Signal Traces](#45-routing--signal-traces)
    - [4.6 Zone Pours & Planes](#46-zone-pours--planes)
    - [4.7 Vias](#47-vias)
    - [4.8 Silkscreen & Labels](#48-silkscreen--labels)
    - [4.9 Design Rules Check (DRC)](#49-design-rules-check-drc)
    - [4.10 Gerber Export](#410-gerber-export)
6. [Part 5 — Ordering from JLCPCB](#part-5--ordering-from-jlcpcb)
7. [Electronics Principles Reference](#electronics-principles-reference)
8. [Glossary](#glossary)
9. [Further Resources](#further-resources)

---

## Before You Start

### What You Need Installed

- **KiCad 10.0** — free, open-source PCB design software. Install from [kicad.org](https://www.kicad.org/download/)
- **JLCPCB Tools Plugin** — for BOM/CPL generation. Install via KiCad Plugin Manager (Tools > Plugin and Content Manager) or run `setup-kicad-jlcpcb.py` in the repo
- **Espressif KiCad Libraries** — symbols and footprints for ESP32 modules. Already in the repo at `reference-boards/espressif-kicad-libs/`

### What You Need to Understand

You do NOT need to understand everything up front. This guide explains each concept when it becomes relevant. But here is the 30-second version of how PCB design works:

1. **Schematic** — a logical diagram of what connects to what. You draw symbols (rectangles with pins) and connect them with wires or labels. This does NOT care about physical size or position.
2. **Netlist** — automatically generated from the schematic. It is a list that says "pin 3 of U1 connects to pin 1 of R4" etc.
3. **PCB Layout** — a physical drawing of copper traces on a board. You place real-sized footprints (the physical pads where components solder down) and draw copper traces between them following the netlist.
4. **Gerber files** — the final output. These are the "print files" that a factory like JLCPCB uses to manufacture the board.

The workflow is always: **Schematic → Netlist → PCB → Gerbers → Factory**.

---

## Part 1 — Project Setup

### Step 1: Create a New KiCad Project

1. Open KiCad
2. **File > New Project**
3. Name it `dilder` and save it in your working directory
4. KiCad creates two files: `dilder.kicad_pro` (project settings) and `dilder.kicad_sch` (schematic)

### Step 2: Configure Libraries

You need the Espressif library for the ESP32-S3 symbol and footprint.

1. In KiCad's main window, go to **Preferences > Manage Symbol Libraries**
2. Click the **Project Libraries** tab
3. Click the **+** button (Add existing library to table)
4. Navigate to `reference-boards/espressif-kicad-libs/symbols/Espressif.kicad_sym`
5. The library name will auto-fill as "Espressif". Click OK.

Repeat for the footprint library:

1. **Preferences > Manage Footprint Libraries**
2. **Project Libraries** tab
3. **+** button
4. Navigate to `reference-boards/espressif-kicad-libs/footprints/Espressif.pretty`
5. Click OK.

### Step 3: Set Schematic Page Size

1. Double-click `dilder.kicad_sch` to open the Schematic Editor
2. **File > Page Settings**
3. Set paper size to **A3** (landscape). This gives you plenty of room.
4. Fill in: Title = "Dilder Custom PCB", Revision = "0.5", Date = today's date

You now have a blank A3 schematic sheet ready to draw on.

---

## Part 2 — Schematic Design

### How the Schematic Editor Works

**Key concepts:**

- **Symbols** are the rectangular/triangular shapes representing components (resistors, ICs, connectors). They have **pins** — the connection points.
- **Wires** are the green lines connecting pins together. When two pins are connected by a wire, they form a **net**.
- **Net labels** are text tags you attach to wires. Two wires with the same label name are electrically connected, even if they are on opposite sides of the sheet. This avoids spaghetti wiring across the page.
- **Power symbols** (GND, +3V3) are special labels that represent power rails.

**Key shortcuts (memorize these):**

| Key | Action |
|-----|--------|
| `A` | Add symbol (opens library browser) |
| `P` | Add power symbol |
| `W` | Draw wire |
| `L` | Add net label |
| `M` | Move component |
| `R` | Rotate component (before placing) |
| `X` | Mirror component horizontally |
| `Esc` | Cancel current action |
| `Ctrl+Z` | Undo |
| Mouse wheel | Zoom in/out |
| Middle-click drag | Pan |

### General Best Practices

1. **Work left to right, top to bottom.** Power input on the left, microcontroller in the center, peripherals on the right.
2. **Power flows top to bottom.** VCC at the top of symbols, GND at the bottom. This is a universal convention that makes schematics readable.
3. **Use net labels instead of long wires.** If a signal needs to cross the sheet, place a label on each end rather than drawing a wire across everything.
4. **Place decoupling capacitors next to every IC.** This is not optional — every IC needs at least one 100nF capacitor between its VCC and GND pins, placed as close as possible. (Why? See [Decoupling Capacitors](#decoupling-capacitors) in the principles section.)
5. **Name your nets.** Instead of leaving wires unnamed, add labels like `I2C_SDA`, `EPD_CLK`, etc. This makes debugging much easier later.
6. **One subcircuit at a time.** Don't try to draw everything at once. Draw one block, wire it, verify it, then move to the next.

---

### 2.1 USB-C Power Input

This is the entry point for power into the board. USB-C provides 5V (called VBUS) and data lines (D+, D-).

#### What You Are Building

```
USB-C Connector (J1)
  ├── VBUS (5V power) ──→ to charging circuit
  ├── GND ──→ ground rail
  ├── D+ ──→ to ESP32 GPIO20
  ├── D- ──→ to ESP32 GPIO19
  ├── CC1 ──→ 5.1k resistor to GND
  └── CC2 ──→ 5.1k resistor to GND
```

#### Why CC Resistors?

USB-C requires two 5.1k resistors on the CC1 and CC2 pins, pulled down to GND. These tell the USB host (your computer or charger) that this device is a **sink** (it wants power, not providing power). Without these resistors, many USB-C chargers will refuse to provide any power at all.

> **Electronics principle: Pull-down resistors.** A pull-down resistor connects a pin to GND through a resistor. This ensures the pin has a known voltage (0V / LOW) when nothing else is driving it. The 5.1k value is specified by the USB-C standard.

#### Steps

1. Press `A` to add a symbol
2. In the search box, type `USB_C_Receptacle`
3. Select `Connector:USB_C_Receptacle` and click OK
4. Click to place it on the left side of your sheet. Press `R` to rotate if needed.
5. Set the Reference to `J1` and Value to `USB-C` (double-click the text to edit)

Now add the CC pull-down resistors:

6. Press `A`, search for `R`, select `Device:R`
7. Place it near the CC1 pin. Set Reference = `R8`, Value = `5.1k`
8. Press `A` again, place another resistor near CC2. Reference = `R9`, Value = `5.1k`
9. Wire CC1 from J1 to pin 1 of R8 (press `W` to start a wire, click pin to pin)
10. Wire pin 2 of R8 to a GND symbol (press `P`, search for `GND`, place it below R8, wire it)
11. Repeat for R9 on CC2

Now add net labels for the outputs:

12. Press `L`, type `VBUS`, place it on the VBUS pin of J1
13. Press `L`, type `USB_DP`, place it on the D+ pin
14. Press `L`, type `USB_DM`, place it on the D- pin
15. Add a `GND` power symbol to the GND pins of J1

**Assign footprint:** Double-click J1 to open properties. In the Footprint field, click the book icon and search for `USB_C_Receptacle_HRO_TYPE-C-31-M-12`. This is the exact physical connector we are using (LCSC part C2765186).

For R8 and R9, assign footprint `Resistor_SMD:R_0402_1005Metric`.

#### Checklist Before Moving On
- [ ] J1 placed with VBUS, GND, D+, D-, CC1, CC2 labeled
- [ ] R8 (5.1k) connects CC1 to GND
- [ ] R9 (5.1k) connects CC2 to GND
- [ ] Footprints assigned to J1, R8, R9
- [ ] LCSC part numbers added (Properties > add field "LCSC" with value)

---

### 2.2 Reverse Polarity Protection (D1: SS34)

A Schottky diode between VBUS and the charging circuit prevents damage if power is applied backwards (e.g., from a faulty cable or if you accidentally reverse battery wires during testing).

> **Electronics principle: Schottky diodes.** A Schottky diode allows current to flow in one direction only, with a very low voltage drop (~0.3V compared to ~0.7V for a regular diode). The SS34 can handle 3 amps — more than enough for USB charging.

#### Steps

1. Press `A`, search for `SS34`, select `Diode:SS34`
2. Place it to the right of J1's VBUS output
3. Wire the **Anode** (triangle side) to the `VBUS` label
4. Add a label `VBUS_CHG` on the **Cathode** (bar side) — this is the protected 5V going to the charger
5. Assign footprint: `Diode_SMD:D_SMA` (LCSC: C8678)

---

### 2.3 LiPo Charging (TP4056)

The TP4056 is a complete single-cell lithium-ion/polymer charger IC. It takes 5V in (VBUS_CHG) and outputs a regulated charging voltage to the battery (VBAT).

#### What You Are Building

```
VBUS_CHG (5V) ──→ VCC (pin 4)
                   TP4056
CE (pin 8) ←── VBUS_CHG (always enabled)
TEMP (pin 1) ──→ GND (disable temp monitoring)
PROG (pin 2) ──→ 1.2k resistor to GND (sets charge current)
BAT (pin 5) ──→ VBAT (to battery + LDO)
CHRG (pin 7) ──→ charge LED (via resistor)
STDBY (pin 6) ──→ standby LED (via resistor)
GND (pin 3) ──→ GND
EPAD (pin 9) ──→ GND (exposed thermal pad)
```

#### Setting the Charge Current with PROG Resistor

The TP4056 datasheet specifies: **charge current = 1200 / R_PROG**. With a 1.2k resistor: 1200 / 1200 = **1A charge current**. This is the maximum rate for most small LiPo cells (500-2000mAh).

> **Electronics principle: Current-setting resistors.** Many ICs use a resistor on a specific pin to set an internal parameter. The IC sources a known voltage on that pin, and the resistor determines how much current flows, which the IC measures to set its behavior. Always check the datasheet for the formula.

#### Steps

1. Press `A`, search for `TP4056`. Select `Battery_Management:TP4056-42-ESOP8`
2. Place it to the right of D1
3. Wire each pin:
    - `VCC` (pin 4) → label `VBUS_CHG`
    - `CE` (pin 8) → label `VBUS_CHG` (charge enable — always on)
    - `TEMP` (pin 1) → `GND` symbol (disables temperature monitoring; for production, connect to a 10k NTC thermistor on the battery)
    - `GND` (pin 3) → `GND` symbol
    - `EPAD` (pin 9) → `GND` symbol (thermal pad must connect to ground for heat dissipation)
    - `BAT` (pin 5) → label `VBAT`
    - `CHRG` (pin 7) → label `CHRG_OUT`
    - `STDBY` (pin 6) → label `STDBY_OUT`

4. Add the PROG resistor:
    - Place `Device:R` near pin 2. R1 = 1.2k.
    - Wire pin 2 (PROG) → R1 pin 1
    - Wire R1 pin 2 → GND

5. Assign footprint: `Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm_ThermalVias` (LCSC: C382139)

**Important:** The SOIC-8-1EP footprint has thermal vias under the exposed pad. These transfer heat from the IC through the PCB to the ground plane — critical for a charging IC that dissipates heat.

---

### 2.4 Battery Protection (DW01A + FS8205A)

These two chips work together to protect the LiPo battery from:

- **Over-discharge** — cuts off power if battery voltage drops below ~2.5V (prevents permanent damage)
- **Over-charge** — cuts off charging above ~4.25V
- **Over-current / short circuit** — cuts off if current exceeds safe limits

The DW01A is the "brain" (monitors voltage and current). The FS8205A is the "muscle" (two N-channel MOSFETs that physically switch the battery connection on/off).

> **Electronics principle: N-channel MOSFETs as switches.** A MOSFET is like an electronically controlled switch. Apply voltage to the Gate, and current flows between Drain and Source. The FS8205A has TWO MOSFETs in one package — one for discharge control (OD) and one for charge control (OC). The DW01A drives their gates.

#### Circuit Topology

```
VBAT ──→ DW01A VCC (pin 5)
         DW01A CS (pin 2) ──→ "CS_DRAIN" node (between the two MOSFETs)
         DW01A OD (pin 1) ──→ FS8205A G1 (pin 2) — over-discharge gate
         DW01A OC (pin 3) ──→ FS8205A G2 (pin 5) — over-charge gate
         DW01A GND (pin 6) ──→ CS_DRAIN node
         DW01A TD (pin 4) ──→ VBAT (no delay)

FS8205A:
  S1 (pin 1) ──→ BAT_MINUS (battery negative terminal)
  G1 (pin 2) ──→ OD from DW01A
  D (pins 3,4) ──→ CS_DRAIN (shared drain, connects to DW01A CS and GND)
  G2 (pin 5) ──→ OC from DW01A
  S2 (pin 6) ──→ circuit GND
```

The two MOSFETs sit in series between the battery's negative terminal and the circuit's ground. When both are ON, current flows normally. When the DW01A detects a fault, it turns off one or both MOSFETs, disconnecting the battery.

#### Steps

1. Place `Battery_Management:DW01A` (U3). Footprint: `Package_TO_SOT_SMD:SOT-23-6`
2. Place `Transistor_FET:Q_Dual_NMOS_S1G1D2S2G2D1` (Q1) OR use a custom FS8205A symbol. Footprint: `Package_TO_SOT_SMD:SOT-23-6`
   - If using a custom symbol: 6 pins — S1(1), G1(2), D(3), D(4), G2(5), S2(6)
3. Wire as shown in the topology above. Use net labels `OD`, `OC`, `CS_DRAIN`, `BAT_MINUS`.
4. Place `Connector_Generic:Conn_01x02` for the battery connector (J2). Footprint: `Connector_JST:JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical`
5. Wire J2 pin 1 → `VBAT`, J2 pin 2 → `BAT_MINUS`

---

### 2.5 Voltage Regulation (AMS1117-3.3)

The battery provides 3.0-4.2V (varying with charge level). The ESP32-S3 needs a stable 3.3V. The AMS1117-3.3 is a Low-Dropout Regulator (LDO) that converts the variable battery voltage to a steady 3.3V.

> **Electronics principle: LDO regulators.** An LDO takes a higher input voltage and outputs a lower, stable voltage. "Low dropout" means the input only needs to be slightly higher than the output — the AMS1117 needs just ~1V headroom, so it works down to 4.3V input. Below that, the output starts to sag (this is called "dropout"). With a 3.0V battery, the output will be ~2.9V. For our application this is acceptable since the ESP32-S3 works down to 2.8V.

#### Steps

1. Place `Regulator_Linear:AMS1117-3.3` (U4). Footprint: `Package_TO_SOT_SMD:SOT-223-3_TabPin2`
2. Wire: pin 3 (VI) → label `VBAT`, pin 2 (VO) → label `3V3`, pin 1 (GND/ADJ) → `GND`
3. Place a `+3V3` power symbol on the output (press `P`, search `+3V3`)

**Decoupling capacitors — critical:**

4. Place C5 = 10uF between `VBAT` and `GND` (near U4 input). This stabilizes the input.
5. Place C6 = 10uF between `3V3` and `GND` (near U4 output). This stabilizes the output.

Both capacitors: footprint `Capacitor_SMD:C_0402_1005Metric`.

> **Why 10uF and not 100nF?** Voltage regulators need BULK capacitance (10uF+) to remain stable. The regulator's internal feedback loop can oscillate without sufficient capacitance. 100nF is for high-frequency noise filtering on IC power pins. Here we need both — 10uF for stability, and each IC that uses 3V3 also gets its own 100nF near its power pins.

---

### 2.6 ESP32-S3-WROOM-1

The microcontroller module. This is the heart of the board.

#### What You Are Connecting

The ESP32-S3-WROOM-1 module has the MCU, flash, PSRAM, crystal, and antenna all integrated. You just need to connect:

- **Power**: 3V3 and GND
- **EN (Enable)**: pull-up to 3V3 via 10k resistor + reset button to GND + 100nF debounce cap
- **GPIO0 (Boot)**: pull-up to 3V3 via 10k resistor + boot button to GND
- **GPIO pins**: connect to peripherals via net labels

> **Electronics principle: Pull-up resistors and boot modes.** The ESP32-S3 checks GPIO0 at boot time. If GPIO0 is HIGH (pulled up to 3V3), it boots normally from flash. If GPIO0 is LOW (held to GND by pressing the BOOT button), it enters download mode for firmware flashing. The 10k pull-up ensures normal boot by default. The button overrides it to GND when pressed.

> **Electronics principle: RC debounce on EN.** The EN pin resets the chip when pulled LOW. Mechanical buttons "bounce" — they rapidly switch on/off for a few milliseconds when pressed. The 100nF capacitor on EN smooths this out, preventing accidental double-resets. The RC time constant is: 10k x 100nF = 1ms, which is enough to filter bounce.

#### Steps

1. Press `A`, search for `ESP32-S3-WROOM-1`. Select from the Espressif library.
2. Place it in the CENTER of your schematic — it is the main component, and everything connects to it.
3. The symbol is large with many pins. Don't panic — most pins are unused.

**Power connections:**

4. Connect the `3V3` pin to a `+3V3` power symbol
5. Connect `GND` pin(s) to `GND` power symbols (the module has multiple GND pins — connect all of them)

**Decoupling capacitors:**

6. Place C3 = 100nF between 3V3 and GND (near the module)
7. Place C4 = 10uF between 3V3 and GND (bulk cap for the module)

> **Why two caps?** The 100nF filters high-frequency noise (MHz range) and the 10uF provides energy storage for current spikes when the WiFi transmitter turns on. The ESP32 can draw 500mA peak — the 10uF cap provides this instantly while the LDO catches up.

**EN (chip enable):**

8. Place R10 = 10k, wire one end to 3V3, other end to `EN` label
9. Place SW3 (Switch:SW_Push), wire one pin to `EN` label, other to `GND` — this is the RESET button
10. Place C8 = 100nF between `EN` and `GND` (debounce)

**GPIO0 (boot select):**

11. Place R11 = 10k, wire one end to 3V3, other end to `BOOT` label
12. Place SW2 (Switch:SW_Push), wire one pin to `BOOT` label, other to `GND` — this is the BOOT button
13. Add label `BOOT` on GPIO0 of the ESP32

**GPIO assignments — add net labels to these pins:**

| ESP32 Pin | Net Label | Goes To |
|-----------|-----------|---------|
| GPIO0 | BOOT | Boot button |
| GPIO3 | EPD_DC | ePaper data/command |
| GPIO4 | JOY_UP | Joystick up |
| GPIO5 | JOY_DOWN | Joystick down |
| GPIO6 | JOY_LEFT | Joystick left |
| GPIO7 | JOY_RIGHT | Joystick right |
| GPIO8 | JOY_CENTER | Joystick center press |
| GPIO9 | EPD_CLK | ePaper SPI clock |
| GPIO10 | EPD_MOSI | ePaper SPI data |
| GPIO11 | EPD_RST | ePaper reset |
| GPIO12 | EPD_BUSY | ePaper busy signal |
| GPIO16 | I2C_SDA | Accelerometer data |
| GPIO17 | I2C_SCL | Accelerometer clock |
| GPIO18 | ACCEL_INT1 | Accelerometer interrupt |
| GPIO19 | USB_DM | USB D- |
| GPIO20 | USB_DP | USB D+ |
| GPIO46 | EPD_CS | ePaper chip select |
| EN | EN | Reset circuit |

14. For every pin in the table above, add a net label with the exact name shown. Pins you are NOT using can be left unconnected — add a "no connect" flag (press `Q` or use Place > No Connect Flag) on unused pins to tell ERC they are intentionally disconnected.

---

### 2.7 ePaper SPI Interface

The ePaper display connects via an 8-pin JST-SH header. It uses the SPI protocol (4 wires) plus a few control signals.

> **Electronics principle: SPI (Serial Peripheral Interface).** SPI uses 4 wires:
>
> - **SCK (Clock)** — the master (ESP32) toggles this to synchronize data transfer
> - **MOSI (Master Out, Slave In)** — data FROM the ESP32 TO the display
> - **CS (Chip Select)** — pulled LOW to select this specific device (you can have multiple SPI devices sharing SCK and MOSI, each with its own CS)
> - **MISO (Master In, Slave Out)** — data FROM the device TO the ESP32 (not used for ePaper — it is write-only)
>
> Additional signals for ePaper: DC (Data/Command — tells display if the bytes are commands or pixel data), RST (hardware reset), BUSY (display pulls this LOW while it is refreshing).

#### Steps

1. Place `Connector_Generic:Conn_01x08` (J3). Footprint: `Connector_JST:JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal`
2. Define the pinout (this matches common ePaper breakout boards):

    | Pin | Net Label | Function |
    |-----|-----------|----------|
    | 1 | 3V3 | Power |
    | 2 | GND | Ground |
    | 3 | EPD_MOSI | SPI data |
    | 4 | EPD_CLK | SPI clock |
    | 5 | EPD_CS | Chip select |
    | 6 | EPD_DC | Data/command |
    | 7 | EPD_RST | Reset |
    | 8 | EPD_BUSY | Busy flag |

3. Wire pin 1 to `+3V3`, pin 2 to `GND`, pins 3-8 to the labels shown above.

These labels match the ones you placed on the ESP32 — KiCad automatically connects them.

---

### 2.8 LIS2DH12TR Accelerometer (I2C)

The LIS2DH12TR measures acceleration (tilt, motion, tap detection). It connects via I2C.

> **Electronics principle: I2C (Inter-Integrated Circuit).** I2C uses just 2 wires:
>
> - **SDA (Serial Data)** — bidirectional data line
> - **SCL (Serial Clock)** — clock driven by the master (ESP32)
>
> Both lines need **pull-up resistors** (typically 10k to 3V3). This is because I2C uses "open-drain" outputs — devices can only pull the line LOW. The resistor pulls it back HIGH when no device is driving it. Without pull-ups, the bus stays LOW forever and nothing works.
>
> Each I2C device has a 7-bit **address** hardwired or pin-selectable. The LIS2DH12 address is 0x18 when SDO is connected to GND, or 0x19 when SDO is connected to VCC.

#### Steps

1. Place `Sensor_Motion:LIS2DH` (U5). Footprint: `Package_LGA:LGA-12_2x2mm_P0.5mm`
2. Wire the pins:

    | Pin | Connection | Why |
    |-----|------------|-----|
    | SCL/SPC (1) | `I2C_SCL` | I2C clock |
    | SDA/SDI (4) | `I2C_SDA` | I2C data |
    | CS (2) | `+3V3` | Tie HIGH to select I2C mode (LOW = SPI mode) |
    | SDO/SA0 (3) | `GND` | Sets I2C address to 0x18 |
    | INT1 (12) | `ACCEL_INT1` | Motion interrupt to ESP32 |
    | INT2 (11) | No connect | Not used |
    | VDD_IO (9) | `+3V3` | Logic level voltage |
    | VDD (8) | `+3V3` | Analog supply |
    | GND (6,7,8) | `GND` | All ground pins |
    | Res (5,10) | No connect | Reserved pins |

3. Add I2C pull-up resistors:
    - R4 = 10k between `I2C_SDA` and `+3V3`
    - R5 = 10k between `I2C_SCL` and `+3V3`

4. Add decoupling capacitor C7 = 100nF between `+3V3` and `GND` (near U5)

---

### 2.9 AHT20 Temperature & Humidity Sensor (I2C)

The AHT20 measures ambient temperature and humidity. It shares the same I2C bus as the accelerometer — no extra GPIOs or pull-ups needed.

> **Electronics principle: I2C bus sharing.** Multiple I2C devices can share the same SDA/SCL wires. Each device has a unique 7-bit address. The master (ESP32) sends the address before each transaction, and only the addressed device responds. Our bus has three devices with no conflicts:
>
> - LIS2DH12 (accelerometer): **0x18**
> - AHT20 (temp/humidity): **0x38**
> - BH1750 (light sensor): **0x23**
>
> Only ONE set of pull-up resistors is needed per bus (R4, R5 already installed).

**What it provides for Dilder:**

- Ambient temperature — gameplay weather sync, "too cold/hot" pet reactions
- Humidity level — "comfort" metrics, environmental awareness
- Sleep mode intelligence — detect pocket vs open air vs refrigerator prank

#### Steps

1. Place `Device:Generic_I2C` or create a custom symbol for AHT20 (U6). If no symbol exists, use `Connector_Generic:Conn_01x04` as a placeholder with pins: VDD, GND, SDA, SCL.
2. Assign footprint: `Package_DFN_QFN:DFN-6-1EP_3x3mm_P1.0mm` (LCSC: C2757850)
3. Wire:

    | Pin | Connection | Why |
    |-----|------------|-----|
    | VDD | `+3V3` | 2.0-5.5V supply, 3.3V is fine |
    | GND | `GND` | Ground |
    | SDA | `I2C_SDA` | Shared with LIS2DH12 |
    | SCL | `I2C_SCL` | Shared with LIS2DH12 |

4. Add decoupling capacitor C9 = 100nF between `+3V3` and `GND` (near U6)

**No additional pull-ups needed** — R4 and R5 (10k) already serve the bus.

---

### 2.10 BH1750FVI Ambient Light Sensor (I2C)

The BH1750FVI measures ambient light intensity in lux and outputs a 16-bit digital value directly via I2C. No ADC needed on the ESP32 side.

> **Electronics principle: Lux.** Lux is the SI unit of illuminance — how much visible light hits a surface. Reference values:
>
> | Condition | Lux |
> |-----------|-----|
> | Moonlight | ~1 |
> | Dim room | ~50 |
> | Office lighting | ~500 |
> | Overcast outdoors | ~10,000 |
> | Direct sunlight | ~100,000 |
>
> The BH1750 uses a photodiode with a spectral filter matched to human eye sensitivity, then integrates the photocurrent over time and converts it to a 16-bit lux value. Range: 1-65535 lux.

**What it provides for Dilder:**

- Day/night detection — pet sleep cycle follows real light conditions
- "In pocket" detection — screen off, low-power mode
- Screen brightness adaptation — dim display in dark rooms
- Light-based gameplay events — "found a sunny spot!" happiness boost

#### Steps

1. Place a custom symbol or generic IC for BH1750FVI (U7). 6 pins: VCC, GND, SDA, SCL, ADDR, DVI.
2. Assign footprint: a WSOF-6 package. Use `Package_SO:SSOP-6_2.8x2.6mm_P0.65mm` or a custom WSOF-6 footprint (LCSC: C78960)
3. Wire:

    | Pin | Connection | Why |
    |-----|------------|-----|
    | VCC | `+3V3` | 2.4-3.6V supply |
    | GND | `GND` | Ground |
    | SDA | `I2C_SDA` | Shared I2C bus |
    | SCL | `I2C_SCL` | Shared I2C bus |
    | ADDR | `GND` | Sets I2C address to 0x23 |
    | DVI | leave unconnected | Data valid input — not needed for basic operation |

4. Add decoupling capacitor C10 = 100nF between `+3V3` and `GND` (near U7)

---

### 2.11 Joystick & Buttons (renumbered from 2.9)

The SKRHABE010 is a 5-way navigation joystick (up, down, left, right, center press). Each direction is simply a switch that connects to GND when pressed.

> **Electronics principle: Internal pull-ups.** The ESP32 has configurable internal pull-up resistors on most GPIO pins (typically 45k). We enable these in firmware so each joystick switch reads HIGH normally and LOW when pressed. This means we do NOT need external pull-up resistors for the joystick — saving 5 components.

#### Steps

Since the SKRHABE010 doesn't have a standard KiCad symbol, model it as 5 individual push buttons:

1. Place 5 copies of `Switch:SW_Push`
2. Name them SW1a (UP), SW1b (DOWN), SW1c (LEFT), SW1d (RIGHT), SW1e (CENTER)
3. For each: wire pin 1 to the corresponding net label (`JOY_UP`, etc.), wire pin 2 to `GND`

For the BOOT and RESET buttons (already placed in section 2.6):

- SW2 connects `BOOT` to GND
- SW3 connects `EN` to GND

**Note on footprints:** The joystick (SKRHABE010) needs a custom footprint based on its datasheet. The PTS810 buttons may also need a custom footprint. You can create these in the Footprint Editor or find them online.

---

### 2.12 Status LEDs

Two LEDs indicate charging status:

- **D2 (RED)** — lit while charging (driven by TP4056 CHRG pin)
- **D3 (GREEN)** — lit when fully charged (driven by TP4056 STDBY pin)

> **Electronics principle: LED current limiting.** LEDs need a series resistor to limit current. Without it, the LED draws too much current and burns out instantly. The TP4056's CHRG and STDBY pins are open-drain — they sink current to GND when active. So the circuit is: 3V3 → LED → Resistor → TP4056 pin → GND.
>
> **Calculating the resistor:** R = (V_supply - V_LED) / I_LED. For a red LED: V_LED ≈ 1.8V, I_LED = 5mA (dim but visible for 0402). R = (3.3 - 1.8) / 0.005 = 300 ohms. We use 1k for a dimmer, lower-power LED (about 1.5mA) which is fine for a status indicator.

#### Steps

1. Place D2 (`Device:LED`), R2 (`Device:R` = 1k) in series
2. Wire: label `CHRG_OUT` → D2 Anode → D2 Cathode → R2 → `GND`
   - Wait: actually the TP4056 CHRG pin sinks current (open-drain to GND), so the correct wiring is:
   - `CHRG_OUT` → R2 → D2 Anode → D2 Cathode → `GND`... No, let me think again.
   - The CHRG pin goes LOW when charging. So: `+3V3` → R2 → LED → `CHRG_OUT`. When CHRG is LOW, current flows through the LED. When HIGH (not charging), no current flows.
   - Actually for simplicity: `CHRG_OUT` → LED Cathode, LED Anode → R2 → `+3V3`. OR: `CHRG_OUT` → R2 → LED → GND. Both work since CHRG is open-drain.
   - **Simplest:** Wire `CHRG_OUT` label to the cathode (K) of D2, wire the anode (A) through R2 to `+3V3`.
3. Repeat for D3 (GREEN) with `STDBY_OUT`
4. Footprints: D2, D3 = `LED_SMD:LED_0402_1005Metric`, R2, R3 = `Resistor_SMD:R_0402_1005Metric`

---

### 2.13 Power Symbols & Flags

Before running ERC, you need to add **power flags** to tell KiCad which nets are actually driven by power.

> **Why?** KiCad's ERC checks that every power pin has a power source. Some pins are "power input" type (they consume power) and some are "power output" (they provide power). If a net only has power inputs, ERC complains. A `PWR_FLAG` tells ERC "yes, this net IS actually powered."

#### Steps

1. Press `P`, search for `PWR_FLAG`
2. Place one on the `VBUS` net (connects to USB-C power output)
3. Place one on the `GND` net if ERC complains about ground not being driven

---

## Part 3 — Electrical Rules Check (ERC)

Now that the schematic is complete, verify it.

1. **Inspect > Electrical Rules Checker** (or press the ERC button in the toolbar)
2. Click **Run ERC**
3. KiCad shows a list of violations. Common ones:

| Error | Meaning | Fix |
|-------|---------|-----|
| "Pin not connected" | A pin has no wire | Wire it, or add No Connect flag (`Q`) if intentional |
| "Power pin not driven" | A power input pin has no power source on its net | Add a `PWR_FLAG` on that net |
| "Wire not connected" | A wire ends in empty space | Extend it to a pin, or delete the dangling end |
| "Duplicate reference" | Two components have the same reference (e.g., two R1s) | Renumber: Tools > Annotate Schematic |
| "Different net names on same wire" | Two labels on the same wire with different names | Remove the duplicate label |

4. Fix all **errors** (red). **Warnings** (yellow) can often be ignored but review each one.
5. Run ERC again until you have zero errors.

**Annotate the schematic:** Before proceeding, run **Tools > Annotate Schematic** to automatically assign reference designators (R1, R2, R3, C1, C2, etc.) if you haven't done so manually.

---

## Part 4 — PCB Layout

### 4.1 Board Setup

1. From the Schematic Editor, click **Tools > Update PCB from Schematic** (or press `F8`). This creates/opens the PCB Editor with all your components imported.
2. All components appear as a pile in the corner. Don't worry — you will place them.

**Board outline:**

3. Select the **Edge.Cuts** layer in the layer panel (right side)
4. Use **Place > Rectangle** to draw the board outline: 30mm x 70mm
5. Or use **Place > Line** to draw each edge (click the start point, click the end point)

**Layer stack:**

6. **File > Board Setup > Board Stackup > Physical Stackup**
7. Set **4 layers**: F.Cu, In1.Cu, In2.Cu, B.Cu
8. Set thickness to 1.6mm

**Design rules:**

9. **File > Board Setup > Design Rules > Net Classes**
10. Set Default net class: Track width = 0.2mm, Clearance = 0.2mm, Via diameter = 0.6mm, Via drill = 0.3mm
11. Create a net class called "Power": Track width = 0.4mm. Assign nets `VBUS`, `VBUS_CHG`, `VBAT`, `3V3`, `GND` to this class.

---

### 4.2 Import Netlist

If you used "Update PCB from Schematic", the footprints are already imported with their nets. If not:

1. In the Schematic Editor: **File > Export > Netlist**, save as `dilder.net`
2. In the PCB Editor: **File > Import > Netlist**, load `dilder.net`
3. Click "Update PCB" — footprints appear with thin lines (called a "ratsnest") showing which pads need to be connected

---

### 4.3 Component Placement

This is the most important step. Good placement makes routing easy; bad placement makes it impossible.

#### Placement Strategy

Our board is divided into 6 zones from top to bottom:

```
┌──────────────────────────────┐ y=0mm
│       Antenna zone            │ Zone A: NO components (0-3mm)
│       (keep clear!)           │
├──────────────────────────────┤ y=3mm
│     ESP32-S3-WROOM-1         │ Zone B: MCU + decoupling (3-25mm)
│   C3 C4 R10 R11 on sides    │
│                D2 R2 D3 R3   │
├──────────────────────────────┤ y=26mm
│  AMS1117  C5 C6              │ Zone C: Power (26-42mm)
│  TP4056  D1  R1              │
│  DW01A  Q1  J2(battery)     │
├──────────────────────────────┤ y=42mm
│  LIS2DH  R4 R5  C7          │ Zone D: Peripherals (42-54mm)
│         J3(ePaper)           │
│  SW2(BOOT) SW3(RESET) C8    │
├──────────────────────────────┤ y=54mm
│     SW1 (Joystick)           │ Zone E: User input (54-62mm)
│                              │
├──────────────────────────────┤ y=62mm
│  R8 R9   J1 (USB-C)         │ Zone F: USB (62-70mm)
└──────────────────────────────┘ y=70mm
```

#### Placement Rules

1. **Start with the largest components** — ESP32 module, USB-C connector, JST connectors, joystick. These constrain everything else.
2. **Place connectors at board edges** — USB-C at the bottom edge, battery connector on the right side, ePaper header accessible.
3. **Place decoupling caps as close as possible to their IC** — C3/C4 next to ESP32, C5/C6 next to AMS1117, C7 next to LIS2DH. "As close as possible" means within 2-3mm of the power pins.
4. **Keep the antenna zone clear** — absolutely NO copper, components, or ground plane within the top 5mm of the board. The ESP32 module's antenna extends beyond its body into this area. Copper near the antenna kills wireless performance.
5. **Group related components** — charging circuit together, battery protection together, etc.

#### How to Place

- Select a component and press `M` to move it
- Press `R` to rotate (90 degrees each press)
- Press `X` to flip to back side of board (for back-mounted components)
- Use the coordinate readout (bottom-left of screen) to place precisely
- Set the grid to 0.5mm or 0.25mm for fine positioning: **Preferences > Grid**

---

### 4.4 Routing — Power Traces

Route power traces FIRST because they carry the most current and are most critical.

> **Electronics principle: Trace width and current capacity.** A PCB trace is just a thin strip of copper. Wider traces carry more current with less resistance and less heat. For 1oz copper (standard):
>
> - 0.2mm trace ≈ 0.5A max (signals)
> - 0.4mm trace ≈ 1.0A max (power)
> - 1.0mm trace ≈ 2.0A max (high-power)
>
> Our power traces need to handle up to 1A (charging current), so 0.4mm is the minimum.

#### Steps

1. Select the **Route Tracks** tool (press `X`)
2. Set track width to 0.4mm (use the dropdown in the top toolbar)
3. Route these power paths on F.Cu:

    - `VBUS`: USB-C → D1 (Schottky diode)
    - `VBUS_CHG`: D1 → TP4056 VCC, TP4056 CE
    - `VBAT`: TP4056 BAT → DW01A VCC → AMS1117 VI → C5
    - `3V3`: AMS1117 VO → C6 → ESP32 3V3 → other 3V3 devices
    - `BAT_PLUS`: FS8205A → J2 battery connector
    - `GND`: handled by zone pours (see section 4.6), but add short stubs to connect pads to the ground pour

**Tip:** Route power as short, wide, direct paths. Avoid zigzags. If a power trace needs to cross another, use a via to jump to B.Cu and back.

---

### 4.5 Routing — Signal Traces

After power, route signal traces at 0.2mm width.

#### Signal Priority Order

Route in this order (highest priority first):

1. **USB D+/D-** — these are a differential pair. Route them parallel, equal length, on the same layer, close together (0.2mm gap). Keep them short.

> **Electronics principle: Differential pairs.** USB uses two signals (D+ and D-) that carry opposite voltages. The receiver measures the DIFFERENCE between them, which rejects noise. For this to work, both traces must be the same length (within 0.5mm) and maintain consistent spacing. For USB 2.0 Full Speed (12 Mbps), this is not super critical, but good practice.

2. **SPI (ePaper)** — EPD_CLK, EPD_MOSI, EPD_DC, EPD_RST, EPD_CS, EPD_BUSY. These can run at 10-40 MHz. Keep traces under 50mm. Route on B.Cu if needed to avoid crossing other signals.

3. **I2C** — I2C_SDA, I2C_SCL. These run at 100-400 kHz (slow). Not length-sensitive. Route however is convenient.

4. **Joystick/buttons** — JOY_UP through JOY_CENTER, BOOT, EN. Pure digital signals, very slow. Route wherever convenient.

5. **LED outputs** — CHRG_OUT, STDBY_OUT. Very slow. Route last.

#### Routing Technique

- Start a trace by clicking on a pad (the highlighted circles are unrouted connections)
- KiCad shows the ratsnest line pointing to where the trace needs to go
- Click intermediate points to add bends
- Double-click the destination pad to finish
- If you need to cross another trace: drop a **via** (press `V` while routing), route on B.Cu, then via back up

---

### 4.6 Zone Pours & Planes

The inner layers (In1.Cu, In2.Cu) are continuous copper planes. The outer layers (F.Cu, B.Cu) get zone pours (copper fill around existing traces).

> **Electronics principle: Ground planes.** A solid copper ground plane has very low resistance and inductance. It provides an excellent return path for all signals, reduces electromagnetic interference (EMI), and improves thermal performance. Every professional board uses at least one ground plane. Our 4-layer stack uses the dedicated In1.Cu layer as a continuous GND plane.
>
> **Why a 3V3 plane too?** Having a dedicated 3V3 plane (In2.Cu) eliminates the need to route 3V3 traces everywhere. Any component that needs 3V3 just drops a via to the plane. This also reduces noise on the power rail.

#### Steps

1. **In1.Cu GND plane:**
    - Select layer In1.Cu
    - **Place > Zone** (or press `Ctrl+Shift+Z`)
    - Select net: `GND`
    - Draw a rectangle covering the entire board (but starting at y=5mm to avoid the antenna zone)
    - Click to close the rectangle

2. **In2.Cu 3V3 plane:**
    - Select layer In2.Cu
    - Place Zone, net: `3V3`
    - Same rectangle (y=5mm to y=70mm, full width)

3. **F.Cu GND pour:**
    - Select F.Cu
    - Place Zone, net: `GND`
    - Same rectangle. Set priority to 0 (lower than signal traces).
    - This fills empty space on the top copper layer with ground copper.

4. **B.Cu GND pour:**
    - Same as above but on B.Cu

5. **Fill all zones:** Press `B` (or Edit > Fill All Zones)

You should see copper fill appear on all layers, with clearances around non-GND pads and traces.

---

### 4.7 Vias

Vias are small plated holes that connect copper between layers.

**3V3 power vias:** For every component pad on F.Cu that connects to 3V3, place a via nearby that drops to In2.Cu (the 3V3 plane). Select the via tool, set net to 3V3, click near the pad, then route a short trace from the pad to the via.

**GND stitching vias:** Place vias around the board perimeter connecting F.Cu ground pour to In1.Cu ground plane. This creates a low-impedance ground path and helps with EMI. Space them every 5-8mm around the edges.

Via settings: Drill = 0.3mm, Diameter = 0.6mm (JLCPCB minimum for standard vias).

---

### 4.8 Silkscreen & Labels

The silkscreen is the white text/markings printed on the board.

1. KiCad automatically places component reference designators (R1, U1, etc.)
2. Adjust their position/size so they don't overlap pads: select, press `M` to move
3. Add custom text: select F.SilkS layer, **Place > Text**
    - Add "DILDER v0.5" near the bottom
    - Add "USB-C" near J1
    - Add "BAT" near J2
    - Add "BOOT" and "RST" near the buttons

---

### 4.9 Design Rules Check (DRC)

1. **Inspect > Design Rules Checker**
2. Click **Run DRC**
3. Fix violations:

| Error | Fix |
|-------|-----|
| Clearance violation | Move traces/components apart |
| Unconnected items | Route the missing connection |
| Track too close to pad | Nudge the trace |
| Via too close to track | Move the via |
| Silk over copper | Move the silkscreen text |
| Courtyard overlap | Spread components apart |
| Drill too small | Increase via drill to 0.3mm minimum |

4. Run DRC repeatedly until ZERO errors.

**Warnings** are OK for prototype boards but fix them for production.

---

### 4.10 Gerber Export

Once DRC is clean:

1. **File > Fabrication Outputs > Gerbers (.gbr)**
2. Select output directory (create a `gerbers/` folder)
3. Check all copper layers: F.Cu, In1.Cu, In2.Cu, B.Cu
4. Check: F.SilkS, B.SilkS, F.Mask, B.Mask, F.Paste, B.Paste, Edge.Cuts
5. Click **Plot**

Then export drill files:

6. Click **Generate Drill Files**
7. Select Excellon format, metric units
8. Click **Generate Drill File**

For JLCPCB SMT assembly, also generate BOM and CPL:

9. Use the JLCPCB Tools plugin: **Tools > Generate JLCPCB Fabrication Files**
10. This creates BOM.csv (bill of materials) and positions.csv (component placement) automatically

11. ZIP all the gerber + drill files together

---

## Part 5 — Ordering from JLCPCB

1. Go to [jlcpcb.com](https://jlcpcb.com)
2. Click **Order Now** and upload the gerber ZIP
3. JLCPCB auto-detects board parameters. Verify:
    - Layers: 4
    - Dimensions: 30 x 70 mm
    - PCB Thickness: 1.6mm
    - Surface Finish: HASL (lead-free)
    - Solder Mask Color: Green
4. Enable **SMT Assembly**:
    - Assembly Side: Top
    - Upload BOM.csv and positions.csv
    - JLCPCB matches your LCSC part numbers and shows which components it can place
5. Review, pay, and wait ~1 week for delivery

Estimated cost: ~$35-50 for 5 assembled boards + shipping.

---

## Electronics Principles Reference

### Ohm's Law

**V = I x R** — Voltage (volts) = Current (amps) x Resistance (ohms).

This is the most fundamental equation in electronics. If you know any two values, you can calculate the third:

- I = V / R (current through a resistor given voltage across it)
- R = V / I (what resistor to use for a desired current at a given voltage)

Example: LED with 3.3V supply, 1.8V forward voltage, 1k resistor:
I = (3.3 - 1.8) / 1000 = 0.0015A = 1.5mA

### Decoupling Capacitors

Every IC needs capacitors between its power and ground pins, placed as close to the IC as physically possible. There are two types:

- **Bulk capacitor (10uF)** — stores energy for sudden current demands. Like a small battery that fills in while the main power supply reacts.
- **Bypass capacitor (100nF)** — filters high-frequency noise. At MHz frequencies, even short wires have significant inductance, so a local cap provides the instantaneous current the IC needs.

Rule of thumb: 100nF on every IC power pin, plus 10uF on voltage regulators and power-hungry ICs (MCUs, wireless modules).

### Pull-Up and Pull-Down Resistors

A pull-up resistor connects a signal to VCC. A pull-down connects it to GND. Purpose: ensure a signal has a known state (HIGH or LOW) when nothing is actively driving it. Without them, the pin "floats" at an unpredictable voltage, causing erratic behavior.

Common values: 10k for general purpose, 4.7k for I2C (faster rise time), 5.1k for USB-C CC pins (specified by standard).

### Power Dissipation

When current flows through a resistor or regulator, power is dissipated as heat: **P = V x I** or **P = I^2 x R**.

The AMS1117 dropping from 4.2V to 3.3V with 200mA load: P = (4.2 - 3.3) x 0.2 = 0.18W. The SOT-223 package can handle about 1.5W, so this is fine.

### Trace Width vs Current

For 1oz copper on outer layers (35um thick):

| Width | Max Current (10C rise) |
|-------|----------------------|
| 0.15mm | 0.3A |
| 0.2mm | 0.5A |
| 0.3mm | 0.7A |
| 0.5mm | 1.0A |
| 1.0mm | 2.0A |

Use [Saturn PCB Toolkit](http://saturnpcb.com/pcb_toolkit/) for precise calculations.

### 4-Layer PCB Stack

```
F.Cu (top)    — signal traces, component pads, GND pour
In1.Cu        — continuous GND plane (return path for signals)
In2.Cu        — continuous 3V3 plane (power distribution)
B.Cu (bottom) — signal traces, GND pour
```

Why this order? Signals on F.Cu have an immediate ground reference on In1.Cu (just 0.2mm away through the prepreg). This gives low impedance and good signal integrity. The 3V3 plane on In2.Cu distributes power without needing traces.

---

## Glossary

| Term | Definition |
|------|-----------|
| **Anode** | The positive terminal of a diode or LED (current flows IN) |
| **BOM** | Bill of Materials — list of all components with part numbers and quantities |
| **Cathode** | The negative terminal of a diode or LED (current flows OUT) |
| **Clearance** | Minimum gap between copper features (traces, pads, pours) |
| **Courtyard** | The physical outline around a component showing how much board space it occupies |
| **CPL** | Component Placement List — XY coordinates and rotation for each component (for pick-and-place machines) |
| **Decoupling cap** | Capacitor placed near an IC to filter noise on power supply |
| **DRC** | Design Rules Check — automated check that the PCB meets manufacturing constraints |
| **Drill file** | File specifying the position and size of all holes (vias, mounting holes, through-hole pads) |
| **ERC** | Electrical Rules Check — automated check for wiring errors in the schematic |
| **Footprint** | The physical land pattern on the PCB where a component is soldered (pads, outline, courtyard) |
| **Gerber** | Industry-standard file format for PCB layers (one file per layer) |
| **GND** | Ground — the 0V reference voltage that all other voltages are measured relative to |
| **HASL** | Hot Air Solder Leveling — a PCB surface finish where exposed copper pads are coated with solder |
| **I2C** | Inter-Integrated Circuit — a 2-wire serial protocol (SDA + SCL) |
| **LCSC** | The component distributor used by JLCPCB for SMT assembly |
| **LDO** | Low-Dropout Regulator — a voltage regulator that works with very small input-output voltage difference |
| **LGA** | Land Grid Array — a package type with pads on the bottom (no leads), common for sensors |
| **MOSFET** | Metal-Oxide-Semiconductor Field-Effect Transistor — an electronically controlled switch |
| **Net** | An electrical connection — all pins/pads on the same net are electrically connected |
| **Netlist** | A file listing all nets and which component pins belong to each |
| **Open-drain** | An output type that can only pull a signal LOW (to GND). Needs an external pull-up to go HIGH |
| **Pad** | The copper area on a PCB where a component pin is soldered |
| **Pull-up** | A resistor connecting a signal line to VCC, ensuring it reads HIGH by default |
| **Pour** | A large area of copper fill on a layer, usually connected to GND |
| **Ratsnest** | Thin lines in the PCB editor showing unrouted connections |
| **Reference designator** | The identifier for a component (R1, C2, U3, J4, etc.) |
| **Schottky diode** | A diode with very low forward voltage drop (~0.3V vs 0.7V for standard) |
| **SMD/SMT** | Surface Mount Device/Technology — components soldered to the surface of the PCB (not through holes) |
| **SOT-23** | Small Outline Transistor package with 3, 5, or 6 pins |
| **SPI** | Serial Peripheral Interface — a 4-wire protocol (SCK, MOSI, MISO, CS) |
| **Symbol** | The schematic representation of a component (shows pins and function, not physical shape) |
| **Thermal relief** | A pad connection to a copper pour through narrow spokes instead of a solid connection, making soldering easier |
| **Trace** | A copper track on the PCB connecting two pads |
| **Via** | A plated hole connecting copper on different layers of the PCB |
| **Zone** | A filled area of copper on a layer (used for ground planes, power planes, and pours) |

---

## Further Resources

### Learning Electronics

- **"The Art of Electronics" by Horowitz & Hill** — the definitive electronics reference. Get the 3rd edition. Read chapters 1-2 for fundamentals.
- **"Getting Started in Electronics" by Forrest Mims** — a beginner-friendly illustrated guide that covers all the basics in 128 pages.
- **EEVBlog YouTube Channel** — Dave Jones explains electronics concepts with practical demonstrations. Start with his "Fundamentals Friday" series.
- **Ben Eater's YouTube Channel** — builds computers from scratch, explains every component along the way.

### Learning KiCad

- **[KiCad Official Getting Started Guide](https://docs.kicad.org/10.0/en/getting_started_in_kicad/getting_started_in_kicad.html)** — the official tutorial, covers the full workflow
- **Digikey's KiCad Tutorial Series on YouTube** — step-by-step video walkthroughs
- **Chris Gammel's "Getting to Blinky"** — free video course that takes you from zero to a blinking LED board

### ESP32-S3 Hardware Design

- **[ESP32-S3-WROOM-1 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)** — pinout, electrical specs, absolute maximums
- **[ESP32-S3 Hardware Design Guidelines](https://www.espressif.com/sites/default/files/documentation/esp32-s3_hardware_design_guidelines_en.pdf)** — antenna placement, decoupling, layout recommendations. READ THIS before finalizing PCB layout.

### Component Datasheets

Always read the datasheet for every IC you use. Key sections:

- **Absolute Maximum Ratings** — voltages/currents that will DESTROY the chip
- **Typical Application Circuit** — copy this! The manufacturer already designed the circuit for you.
- **Pin Description** — what each pin does
- **Electrical Characteristics** — operating voltages, currents, timing

Our component datasheets:

- [TP4056 Datasheet](https://www.lcsc.com/product-detail/Battery-Management_C382139.html)
- [DW01A Datasheet](https://www.lcsc.com/product-detail/Battery-Protection-ICs_C351410.html)
- [AMS1117-3.3 Datasheet](https://www.lcsc.com/product-detail/Voltage-Regulators-Linear-Low-Drop-Out-LDO-Regulators_C6186.html)
- [LIS2DH12TR Datasheet](https://www.st.com/resource/en/datasheet/lis2dh12.pdf)

### PCB Design Calculators

- **[Saturn PCB Toolkit](http://saturnpcb.com/pcb_toolkit/)** — trace width, via current, impedance calculations (free, Windows)
- **[JLCPCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities)** — what JLCPCB can manufacture (minimum trace width, via size, etc.)

### Reference Board Designs

Study existing open-source designs to learn good practices. These are in the repo:

- `reference-boards/esp32s3-ducky-epaper/` — ESP32-S3 with ePaper, very similar to Dilder
- `reference-boards/esp32s3-basic-devboard/` — clean minimal ESP32-S3 reference design
- `reference-boards/rp2040-minimal-jlcpcb/` — minimal MCU board targeting JLCPCB
