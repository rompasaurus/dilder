# IMU + DAC + Speaker — Schematic & KiCad GUI Walkthrough

This guide is the working reference for adding three new component groups to the Dilder Full Board:

1. **IMU** — the 6-axis accelerometer/gyro the FreeCAD macro models (GY-6500 / MPU-6500 module).
2. **DAC** — an I²S DAC for clean audio out from the Pico 2 W (PCM5102A).
3. **Speaker + amp** — a small 8 Ω speaker driven by a Class-D I²S amp (MAX98357A).

For each one you get:
- A reference schematic you can copy/clone from inside this repo.
- A symbol + footprint pair that's confirmed JLCPCB-orderable (LCSC part numbers).
- A step-by-step KiCad GUI walkthrough — menus, dialogs, hotkeys, no scripting.

> **Companion docs:**
> - `COMPONENTS-AND-IMPORT-GUIDE.md` (component list + import strategy for the Full Board)
> - `BOM.md` (parts list, GPIO assignments)
> - `pcb-design-plan.md` (phase plan)

---

## 1. The IMU — MPU-6500 / GY-6500

The macro models the **GY-6500 breakout** (MPU-6500 chip on a 25 × 15 mm carrier with an 8-pin 2.54 mm header). You have two paths on the Full Board:

### Path A — Keep it as a breakout (recommended for v0.5)

You don't need the chip's schematic at all. The Full Board just exposes an **8-pin 2.54 mm header** that the GY-6500 module plugs into.

| Header pin | Module label | Net |
|---|---|---|
| 1 | VCC | +3V3 |
| 2 | GND | GND |
| 3 | SCL | SCL (Pico GP5, I2C0_SCL) |
| 4 | SDA | SDA (Pico GP4, I2C0_SDA) |
| 5 | XDA | NC |
| 6 | XCL | NC |
| 7 | AD0 | GND (sets I²C addr to 0x68) |
| 8 | INT | (optional) Pico GP22 |

- **Symbol:** `Connector_Generic:Conn_01x08`
- **Footprint:** `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical` (KiCad stock)
- **JLCPCB:** any 8-pin 2.54 mm vertical header — generic LCSC part `C2337` (or any equivalent), no special placement needed.

This is the lowest-risk option. The MPU-6500 chip itself is only stocked on JLCPCB's *Extended* parts library (extra setup fee). Keeping it on the breakout sidesteps that and still gives you the same I²C bus.

### Path B — Bring the IMU chip on-board

If you want a single, sealed PCB instead of a header-mounted breakout, drop the chip directly. The closest reference design in the repo uses the **TDK ICM-42670-P** (a newer pin-compatible-ish part) — see:

```
hardware-design/examples/08-esp-rust-board/hardware/esp-rust-board/esp-rust-board.kicad_sch
```

Refdes `U2`, value `ICM-42670-P`, footprint `Rust_Board:IC_ICM-42670-P` (QFN-16, 2.5 × 3 mm). The schematic shows the canonical I²C decoupling: 100 nF + 10 nF in parallel from VDD to GND, AP_SDO/AD0 strapped, AP_CS tied high to select I²C mode. Open it in KiCad, copy the block, retarget the labels.

| Chip | Package | LCSC | JLCPCB tier | Notes |
|---|---|---|---|---|
| **MPU-6500** (matches the macro/firmware) | QFN-24 4×4 mm | C353159 | Extended | Same chip as the GY-6500; firmware "just works". |
| **ICM-42670-P** (drop-in upgrade) | QFN-16 2.5×3 mm | C2657735 | Extended | Lower power, smaller — has a local KiCad reference in this repo. |
| **MPU-6050** (legacy fallback) | QFN-24 4×4 mm | C24112 | **Basic** | Cheapest, on JLCPCB Basic library; older but well-supported in MicroPython. |

> If JLCPCB SMT cost matters more than firmware identity, **MPU-6050 is the only Basic-library option**. Move to it if you want a cheap turnkey assembly.

**Required passives for any of the three (off the chip's VDD/VDDIO):**
- `C1` 100 nF 0402 (high-frequency decoupling)
- `C2` 10 nF 0402 (mid-frequency)
- `C3` 2.2 µF 0402 X7R (bulk)
- `R1`, `R2` 10 kΩ 0402 — shared SDA/SCL pull-ups (only **one pair on the bus**, even with AHT20/BH1750 added in v0.5)
- Optional `C4` 10 nF on REGOUT (datasheet)

---

## 2. The DAC — PCM5102A (I²S, no MCLK needed)

The Pico's PIO can synthesise I²S in software, but it doesn't have a hardware I²S MCLK. The **PCM5102A** is the perfect match: it has an internal PLL that derives MCLK from BCK alone, so the Pico just needs to feed it three lines (BCK, LRCK, DIN).

### Reference schematic in the repo

```
hardware-design/examples/02-lilka-console/hardware/v2/main.kicad_sch
```

Search for refdes `H1`, value `PCM5102A`, in the `connector:PCM5102A-I2S-Module` symbol. Lilka uses it as a **breakout module** (the standard ~$1 PCM5102A board on Aliexpress/Amazon), so the symbol is just a 13-pin connector you wire to.

| Pin | PCM5102A signal | Net |
|---|---|---|
| VCC | 3.3 V | +3V3 |
| GND | GND | GND |
| SCK | system clock | NC (internal PLL) |
| BCK | bit clock | Pico GP18 (I²S BCK) |
| DIN | data in | Pico GP19 (I²S DOUT) |
| LRCK | left/right word clock | Pico GP20 (I²S LRCK) |
| FMT | format select | GND (I²S mode) |
| XSMT | mute / soft-unmute | +3V3 (un-mute) |
| FLT | filter | GND |
| DEMP | de-emphasis | GND |
| OUT-L / OUT-R | analog L/R | (to amp or jack) |
| AGND | analog GND | GND (single-point) |

### Path A — Use the breakout module (matches lilka)

- **Symbol:** `Connector_Generic:Conn_01x07` (or copy `connector:PCM5102A-I2S-Module` from lilka's local library)
- **Footprint:** 7-pin 2.54 mm header (`Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical`)
- **JLCPCB:** the module ships as a soldered-in sub-board; you only place a header on the main PCB.

### Path B — Bare chip on the Full Board

| Chip | Package | LCSC | JLCPCB tier |
|---|---|---|---|
| **PCM5102APWR** | TSSOP-20 6.5 × 4.4 mm | C45641 | Extended |

If you go bare, you need a 4-layer board (or careful AGND/DGND star) and these passives per the TI datasheet's typical app circuit:

- `100 nF` from each of CPVDD, DVDD, AVDD to GND (close to the chip)
- `10 µF` bulk on each rail
- `LDOO` to GND via `1 µF` (internal LDO output decoupling)
- 3 × 10 kΩ pull-ups on `XSMT`/`FLT`/`DEMP` mode pins (or hardwired per the table above)

Honestly, for a hand-assembled prototype, **Path A (the module) is the right call**. Move to bare chip in a v2 spin once the audio path is proven.

---

## 3. The Speaker + Amp — MAX98357A driving an 8 Ω speaker

The PCM5102A puts out a low-level analog L+R signal that needs amplification before a speaker. But there's a cleaner, smaller option that **replaces the PCM5102A entirely** for mono use cases: the **MAX98357A**, a Class-D amp that takes I²S in directly and drives a speaker out — no separate DAC, no analog stage.

For a handheld pet that just needs beeps and short audio cues, **MAX98357A alone is the right architecture.** The PCM5102A only earns its place if you need stereo or line-out to a 3.5 mm jack.

### Reference schematic

```
hardware-design/examples/02-lilka-console/hardware/v2/main.kicad_sch
```

Refdes `J5`, symbol `connector:MAX98357-I2S-Module`, footprint `footprints:MAX98357-I2S-Module`. Lilka places it as a module (the same form factor as the Adafruit/Aliexpress break-out).

### Pinout (MAX98357A → Pico)

| Pin | Signal | Net |
|---|---|---|
| VIN | 2.7 V – 5.5 V | VBUS or +3V3 (use VBUS for louder output) |
| GND | — | GND |
| SD | shutdown / channel-select | +3V3 (mono, L+R summed) |
| GAIN | gain select | Float = 9 dB (good default) |
| LRC | LRCLK | Pico GP20 |
| BCLK | bit clock | Pico GP18 |
| DIN | data | Pico GP19 |
| OUT+ / OUT- | speaker | screw terminal or 2-pin JST |

### Speaker

The macro currently models a **20 mm piezo disc** (FT-20T). That's *not* what MAX98357A wants — it wants a real coil speaker (4 – 8 Ω, 1 – 3 W). Two options:

| Option | Part | LCSC | When to use |
|---|---|---|---|
| **Tiny coil speaker** | CUI CMS-20158-078SP, 20 mm × 14 mm × 3.6 mm, 8 Ω 0.5 W | C2879612 | Best fidelity for tones/short clips. Needs MAX98357A. |
| **SMT magnetic buzzer** (active) | CMI-1295-100T-CT-TR | C95011 | Single net, no amp needed. PWM directly from a Pico GPIO. **Drop-in replacement for the macro's piezo.** |
| **SMT piezo** (passive) | CUI CPT-9019S-SMT (used in OpenTama) | C391035 | Same idea — direct GPIO PWM, no amp. See `reference-boards/opentama-virtual-pet/`. |

**Pick one architecture, not both.** Either:
- **Audio-quality path:** Pico → I²S → MAX98357A → 8 Ω coil speaker (3 GPIO + 1 power pin). Use a 2-pin JST or screw terminal for the speaker leads.
- **Beeper path:** Pico → 1 GPIO (PWM) → SMT piezo or magnetic buzzer. No amp, no I²S, much smaller PCB area.

For a pet device, the **beeper path is more in keeping with the Tamagotchi feel**, uses less power, and aligns with the FreeCAD macro's existing piezo. The MAX98357A path is for if you want it to play melodies / voice samples.

### Speaker connector footprint

If you go MAX98357A:
- **Symbol:** `Connector_Generic:Conn_01x02`
- **Footprint:** `Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal` (JST PH 2.0 mm, very common, JLCPCB stocks the SMT variant `S2B-PH-SM4-TB(LF)(SN)` as `C144394`).

---

## 4. Walking through KiCad — the GUI workflow

Everything below is GUI-only. No editing `.kicad_sch` files by hand, no Python.

### 4.1 Open the project

1. Launch KiCad (`kicad` from a terminal, or your distro's launcher).
2. **File → Open Project** → navigate to:
   `hardware-design/PCB Designs/Dilder Full Board/Dilder-Full-board/Dilder-Full-board.kicad_pro`
3. The KiCad **Project Manager** window opens. Double-click the schematic icon (or hit `Ctrl+E`) to open **Eeschema**.

### 4.2 Register the local libraries that have these symbols

You'll be cherry-picking the ICM-42670 symbol from the rust-board project and the audio module symbols from lilka. KiCad needs to know about those libraries first.

1. In Eeschema: **Preferences → Manage Symbol Libraries…**
2. Click the **Project Specific Libraries** tab (so you don't pollute global).
3. Click the **+** button at the bottom-left of the table. A new empty row appears.
4. **Nickname:** `Rust_Board`
5. **Library Path:** click the folder icon and navigate to
   `…/hardware-design/examples/08-esp-rust-board/kicad_libs/Rust_Board.kicad_sym`
6. Repeat for the lilka audio symbols. Add another row:
   - **Nickname:** `lilka_connector`
   - **Library Path:** `…/hardware-design/examples/02-lilka-console/hardware/v2/symbols/connector.kicad_sym`
   *(or whatever the file is called — open the Files browser and look in the `symbols/` folder; the lilka project keeps the audio module symbols there.)*
7. Click **OK**.
8. Now do the footprints: **Preferences → Manage Footprint Libraries…** → Project Specific tab → **+** for each:
   - **Nickname:** `Rust_Board` → path: `…/08-esp-rust-board/kicad_libs/Rust_Board.pretty`
   - **Nickname:** `lilka_footprints` → path: `…/02-lilka-console/hardware/v2/footprints/`

The libraries are now visible in the Symbol Chooser and the Footprint Chooser.

### 4.3 Place the IMU header (Path A — breakout)

1. In Eeschema, press **`A`** (or **Place → Add Symbol**).
2. The **Choose Symbol** dialog opens. In the search box, type `Conn_01x08`.
3. Select `Connector_Generic:Conn_01x08`. Click OK.
4. Click on a clear area of the sheet — somewhere near the right side, separated from the Pico — to drop the symbol.
5. Hit **`Esc`** to stop placing.
6. Hover the symbol and press **`E`** to edit its properties.
   - Set **Reference** to `J3` (or whatever's free).
   - Set **Value** to `IMU_HEADER`.
   - In the **Footprint** field, click the library browser button and choose
     `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical`.
   - OK.

### 4.4 Label the IMU pins

You want each pin to land on a known net. The fastest way:

1. Press **`L`** (or **Place → Add Net Label**). A floating label appears at your cursor.
2. Type the first label name — `+3V3` — press **Enter**, then click on **pin 1** of `J3`. KiCad attaches the label to that pin's wire stub.
3. Press **`L`** again. Type `GND`, Enter, click pin 2.
4. Continue: `SCL` on pin 3, `SDA` on pin 4, leave 5 and 6 unconnected (place a small "no-connect" `X` flag with **`Q`** so ERC doesn't complain), `GND` on pin 7, `IMU_INT` on pin 8.
5. Power flags: `+3V3` and `GND` need to be **power symbols**, not plain net labels, so KiCad's ERC recognises them. After labeling, find one of each:
   - Press **`P`** (Place → Add Power Port).
   - Type `+3V3`, place near `J3` pin 1's wire (it'll auto-merge with the existing label).
   - Repeat for `GND` near pin 2 and pin 7.

> **Tip:** if a label is wrong, hover it and press **`E`** to rename it. To rename in bulk (e.g. you decide `IMU_INT` should be `INT_IMU`), use **Edit → Find and Replace** (`Ctrl+H`), tick **"Search and replace in net labels"**, and confirm.

### 4.5 Place the MAX98357A audio module

1. Press **`A`**.
2. In the Choose Symbol search box, type `MAX98357`. The symbol from `lilka_connector` should appear.
3. Select it, click OK, click to place — somewhere along the top-right edge, near where the speaker will exit.
4. Press **`E`** on the placed symbol:
   - Reference → `U5` (or next free `U`).
   - Footprint → click browser, pick `lilka_footprints:MAX98357-I2S-Module`.
   - OK.
5. Place an `Conn_01x02` for the speaker (the module's OUT+/OUT- pads are on the module itself, but you still need a connector to bring the speaker leads off the main board if the module sits on headers).
   - Actually — the module *is* the connector. Skip this step if you're using the breakout module form-factor; only add `Conn_01x02` if you go bare-chip.

### 4.6 Wire the audio nets

You want three I²S signals (BCK, LRCK, DIN) to land on Pico GP18/GP20/GP19, and power on VBUS + GND.

1. Press **`L`** and label the module's pins:
   - `BCLK` pin → label `I2S_BCK`
   - `LRC` pin → label `I2S_LRCK`
   - `DIN` pin → label `I2S_DIN`
   - `SD` pin → label `+3V3` (mono mode, both channels summed)
   - `GAIN` pin → leave floating (no label = 9 dB default)
   - `VIN` pin → label `VBUS` (or `+3V3` if you want to keep audio inside the regulated rail)
   - `GND` pin → power port `GND`
2. Hop over to the Pico symbol on the sheet. Find pins `GP18`, `GP19`, `GP20`. Use **`L`** to drop matching labels (`I2S_BCK`, `I2S_DIN`, `I2S_LRCK`) on their wire stubs.
3. KiCad ties the nets by **name** — same label on two pins means they're connected, even if no visible wire runs between them. (This is why the schematic doesn't have to look like a rat's nest.)

### 4.7 Run ERC to confirm everything's wired

1. **Inspect → Electrical Rules Checker** (or the bug-with-checkmark icon in the toolbar).
2. Click **Run ERC**.
3. The bottom panel lists violations. The two you care about:
   - **"Pin not connected"** — every pin without a wire or a `no-connect` flag. Either wire it or place an X with **`Q`**.
   - **"No driver for net X"** — a label exists but no power source / output drives it. Usually means you forgot a power port (`+3V3`, `GND`).
4. Re-run until clean.

### 4.8 Update the PCB from the schematic

1. Save the schematic (`Ctrl+S`).
2. Switch to **Pcbnew** (the PCB icon in the project manager, or `Ctrl+Shift+E` from Eeschema).
3. **Tools → Update PCB from Schematic…** (or hit **`F8`**).
4. The dialog lists every new component (the IMU header, the MAX98357A module). Click **Update PCB**.
5. The new footprints appear at the cursor — click to drop them. Position them near where the FreeCAD macro expects the modules (use the `setup_spreadsheet()` XY coordinates from `dilder_rev2_mk2.FCMacro`).

### 4.9 Confirm JLCPCB-orderability

1. In Eeschema, **Tools → Edit Symbol Fields…**.
2. Add a column called `LCSC` if it doesn't exist (gear icon → Add column).
3. Fill in:
   - IMU header `J3` → `C2337` (generic 8-pin header)
   - MAX98357A module `U5` → leave blank if module, or `C910544` if bare chip
   - PCM5102A (if you go that route) → `C45641`
   - Pull-up resistors `R1`, `R2` → `C25803` (10 kΩ 0402)
   - Decoupling caps → `C1525` (100 nF 0402), `C19702` (10 µF 0402), `C15849` (2.2 µF 0402)
4. Save. The `kicad-jlcpcb-tools` plugin (Phase 1 of `pcb-design-plan.md`) reads these fields when exporting the BOM/CPL for JLCPCB SMT.

---

## 5. Recommended path summary

For the v0.5 Full Board, my recommendation:

| Component | Path | Why |
|---|---|---|
| IMU | **Breakout module on 8-pin header** | The macro models it this way; sidesteps JLCPCB Extended fees; no chip decoupling layout work. |
| Audio | **MAX98357A module + 8 Ω coil speaker** *or* **passive piezo on a single GPIO** | If audio fidelity matters, MAX98357A. If you want simplicity + the macro's existing piezo body, stay with a piezo on PWM. |
| DAC | **Skip the PCM5102A** | MAX98357A already does I²S → speaker in one chip. PCM5102A is only needed for stereo or line-out. |

Result: you add **one 8-pin header** (IMU) and **one audio module** (or one piezo) to the Full Board schematic. That's it.

---

## 6. Reference path quick list

```
hardware-design/
├── examples/
│   ├── 02-lilka-console/hardware/v2/main.kicad_sch     ← PCM5102A + MAX98357A modules
│   ├── 08-esp-rust-board/hardware/esp-rust-board/
│   │   └── esp-rust-board.kicad_sch                    ← ICM-42670-P bare-chip wiring
│   └── 08-esp-rust-board/kicad_libs/
│       ├── Rust_Board.kicad_sym                        ← IMU symbol library
│       └── Rust_Board.pretty/IC_ICM-42670-P.kicad_mod  ← IMU footprint
└── reference-boards/
    └── opentama-virtual-pet/                           ← passive piezo reference (CPT-9019S-SMT)
```
