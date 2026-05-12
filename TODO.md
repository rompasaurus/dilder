# Dilder — Rolling Daily TODO

A living task list updated each week. Newest entries at the top.

## Status legend

- `[x]` — done
- `[ ]` — open
- `[~]` — in progress / partial

## Index

- [Week 5 — 2026-05-12 (Full Board schematic: accel, joystick, power switch)](#week-5--2026-05-12-full-board-schematic-accel-joystick-power-switch)
- [Week 4 — 2026-05-08 (NoSolar+Buzzer enclosure overhaul)](#week-4--2026-05-08-nosolarbuzzer-enclosure-overhaul)
- [Week 3 — 2026-05-04 (Joystick PCB arrival, firmware versioning, V4 driver)](#week-3--2026-05-04-session-progress)

---

## Week 5 — 2026-05-12 (Full Board schematic: accel, joystick, power switch)

Project: **Dilder-PCB** — Dilder Full PCB Rev 1 (KiCad). All work in the working tree (not yet committed).

### Completed Today

#### Component selection (BOM additions)

- [x] **3-axis accelerometer chosen: SC7A20HTR** (Silan, LCSC `C19274408`) — LIS2DH-register-compatible, $0.16 @ qty 1k, 99,130 in stock at JLCPCB. Evaluated and rejected: LIS2DH12 ($0.44, 2.7× more expensive), genuine MPU-6050 ($8, TDK EOL'd 2020), QMI8658C (0 stock), MSA3S02/MSA321 (no docs), STK8321 (custom driver), QMA6100P (custom driver)
- [x] **Joystick confirmed: K1-1506SN-01** (Korean Hroparts, LCSC `C145910`) — same part already verified on hand-routed joystick PCB; no center/up swap risk
- [x] **Power switch chosen: MSK12C02** (Shou Han, LCSC `C431540`) — side-actuated SPDT SMD slide switch, $0.06 @ qty 1, 102k stock
- [x] **Passives library populated** — C1525 (100nF 0402), C15850 (10µF 0805), C25768 (2.2k 0402)

#### KiCad library work (`JLCPCB_lib.kicad_sym`)

- [x] Pulled SC7A20HTR + footprint + 3D model via `easyeda2kicad --lcsc_id=C19274408`
- [x] Pulled K1-1506SN-01 via `--lcsc_id=C145910`
- [x] Pulled MSK12C02 via `--lcsc_id=C431540`
- [x] Patched SC7A20HTR pin electrical types: SDO/CS → `input`, SDx/SCx → `bidirectional`, VDD/VDDIO/GND/GNDIO → `power_in`, INT1/INT2 → `output`, NC pads → `no_connect`
- [x] Patched K1-1506SN-01 with semantic pin names (`UP/DOWN/LEFT/RIGHT/CENTER/COM`) replacing the easyeda numeric names; all pins → `passive`
- [x] Patched 100nF / 10µF caps + 2.2k resistor pin types from `unspecified` / `input` → `passive`

#### SC7A20 schematic wiring (ERC clean)

- [x] Placed SC7A20HTR at (46.99, 130.81) in schematic
- [x] I²C0 bus wired: SDx → `I2C0_SDA` → Pico GP0, SCx → `I2C0_SCL` → Pico GP1 — matches `dilder-hub/main.c:181-182` exactly, zero firmware change needed
- [x] Interrupt: INT1 → `ACCEL_INT1` → Pico GP15 (avoided original GP22 plan because schematic uses GP22 for `EINK_BUSY`)
- [x] CS pulled to `+3V3` to lock I²C mode; SDO grounded to set address `0x18`
- [x] Decoupling caps placed: C4 (100nF on VDDIO), C5 (10µF bulk), C6 (100nF on VDD) — all GND returns to power ports
- [x] I²C pull-ups installed: R6/R7 (2 kΩ, functional substitute for 2.2 kΩ) — corrected from series-resistor topology after audit
- [x] NC pins (pin 4, 6, 11) carry no-connect flags
- [x] Three orphan-net `PCM_4ms_Power-symbol:+3.3V` placements caught and replaced with standard `power:+3V3` (on VDDIO, VDD, CS in sequence)
- [x] ERC: 0 errors, 0 warnings

#### Planning / mechanical decisions

- [x] Joystick placement decided: **back-mount on B.Cu** via `F` flip in PCB editor (thumb-access pattern). Will DNP in JLC BOM and hand-solder to avoid double-side assembly fee
- [x] Power switch placement decided: **Option A** — switch sits between battery+ and TP4056 BAT pin, so USB-only operation still works when switch is off. Pad 3 leaves NC (no slider-position short to GND); 4 mount tabs tied to GND
- [x] Verified GP map vs `board_config.h:226-241` — accel uses GP0/GP1/GP15 (free), joystick uses GP2-GP6 (free, matches firmware), e-ink uses GP17-GP22 (already wired)

### Resolved from earlier weeks

- [x] **"Determine a power on/off (leave power) mechanism"** (Week 3 carryover) — MSK12C02 picked, schematic plan locked
- [x] **"Fix KiCad joystick Rev 2 — re-route with corrected COM/UP pin assignment"** (Week 3 new items) — folded into Full Board schematic with verified pin map; standalone Rev 2 not needed
- [x] **"Add pin-1 silkscreen dot to future PCB orders"** (Week 3 new items) — incorporated as a layout-step reminder; planned for Full Board

### Still Open

- [ ] Place SC7A20 + joystick + slide switch footprints on the PCB layout (`F8 → Update PCB from Schematic`)
- [ ] Press `F` to flip the joystick to B.Cu and confirm silkscreen mirrors correctly
- [ ] Route I²C0 traces (GP0/GP1 → SC7A20) with the standard rules: ≤25 mm length, no acute corners, keep clear of switching nodes
- [ ] Drop GND vias under SC7A20 center pad (3-4 minimum) for thermal/return path
- [ ] Confirm `BAT_RAW` / `BAT_SW` nets propagated correctly after the slide switch is wired in
- [ ] Mark joystick row as DNP in the BOM/CPL export so JLC skips double-side assembly
- [ ] Replace R6/R7 with the imported 2.2 kΩ (`0402WGF2202TCE` / C25768) for BOM consistency — currently 2 kΩ (`0402WGF2001TCE`), functional but off-BOM
- [ ] Reconcile schematic vs firmware e-ink pin assignments — schematic uses GP17-GP22, `board_config.h:226-231` still says GP8-GP13; one side needs to change
- [ ] Add the new `PIN_I2C_SDA` / `PIN_I2C_SCL` / `PIN_ACCEL_INT1` / `ACCEL_I2C_ADDR` defines to `board_config.h` under `BOARD_PICO2_W`
- [ ] Patch `dilder-hub/main.c` MPU-6050 driver → SC7A20 / LIS2DH-style driver (register map: WHO_AM_I=0x33 at reg 0x0F, CTRL_REG1=0x20, OUT_X_L=0x28 with auto-increment MSB=1, 10-bit data right-shifted 6, ±2g = 256 LSB/g) — ~50 lines of changes, no consumer-API impact
- [ ] Commit today's schematic work to git (currently uncommitted in working tree)

### New Items from Today

- [ ] Add pin-1 silkscreen dot to SC7A20 + joystick + slide switch footprints before fab (lesson from Week 3's JLC placement-verification round-trip)
- [ ] Disable the `PCM_4ms_Power-symbol` library in KiCad preferences to prevent re-introducing orphan `+3.3V` nets (3 caught + fixed today)
- [ ] Update `IMU-DAC-SPEAKER-GUIDE.md` lines 33-34 — it still says I²C is on GP4/GP5, which conflicts with BTN_UP/BTN_RIGHT in `board_config.h`. Correct mapping is GP0/GP1
- [ ] Plan firmware patch: change MPU driver address probe from {0x68, 0x69} to {0x18, 0x19} and WHO_AM_I expected value to 0x33

---

## Week 4 — 2026-05-08 (NoSolar+Buzzer enclosure overhaul)

### Completed Today

- [x] Sound routing redesigned — removed through-floor port, added lateral cradle pit + horizontal channel exiting the cover -X side wall (`fdadd83`)
- [x] Base plate sides extended +5 mm (bp_h 4 → 9) for cable routing room — USB-C cutout + USB platform auto-track up 5 mm; cradle/cover/peripheral Z values cascaded (`fdadd83`)
- [x] BuzzerCradleRing containment ring added on base plate floor — 0.9 mm-thick ring keeps speaker laterally located (`fdadd83`)
- [x] Speaker lifted +2 mm in Z (Z=2.6 instead of 0.6) — 2 mm gap for wires to route along floor; cradle BuzzerPocket deepened 2 mm to compensate (`fdadd83`)
- [x] Wire pass-through notches in BuzzerCradleRing (don't cut floor — no holes on base plate underside) (`fdadd83`)
- [x] IMU pocket resized to MPU-6050 spec (20 × 15.6 mm), 2 corner mounting pegs added (15 mm hole-to-hole spacing on +Y long edge) (`fdadd83`)
- [x] PCB visualization updated — through-holes cut at peg positions (`fdadd83`)
- [x] Square peg-washer body added — 6×6×1.5 mm with 2.7 mm hole, 2 separate printable instances (`IMUPegWasher_MX`/`_PX`) (`fdadd83`)
- [x] Macro top-level docstring + many cascading Z comments rewritten to reflect new geometry (`fdadd83`)
- [x] IMU pegs nudged -1 mm in Y (`imu_hole_y_inset` 2.0 → 3.0) — peg/hole/washer Y from 28.8 → 27.8 (`312a65b`)
- [x] Wire channels now open-top slots cut through the full 5 mm BuzzerCradleRing height — wires drop in from above instead of threading through a hole (`312a65b`)

### Still Open

- [ ] Print and verify the new no-solar-buzzer build — confirm speaker friction-fit in deeper cradle pocket, wire channels clear, IMU pegs align with MPU-6050 board holes
- [ ] Verify the lateral sound channel actually projects audible sound out the cover side — may need to enlarge `buzz_port_d` past 2 mm
- [ ] Decide whether the BuzzerCradleRing needs an internal lip/shelf to physically support the lifted speaker (currently friction-fit in cradle pocket only)
- [ ] If the IMU board's hole positions don't match 15 mm spacing exactly, parameterize `imu_hole_spacing` from measurements

---

## Week 3 — 2026-05-04 (Session Progress)

### Completed Today

- [x] Joystick PCB arrived from JLCPCB — unboxed, photographed, tested
- [x] Discovered COM/UP pin swap in EasyEDA-imported KiCad symbol — root cause traced, schematic fixed for Rev 2
- [x] Wired joystick breakout to Pico 2 W — GPIO mapping confirmed: L=GP2, D=GP3, UP=GP4, R=GP5, C=GP6
- [x] GPIO diagnostic added to firmware — prints raw pin states at startup and every 2s during runtime
- [x] Switched display driver from V3 to V4 (internal LUT, no custom waveform tables)
- [x] Rewrote V4 partial refresh driver 4 times (V1.0→V1.4) — final version uses two-pass diff-based partial refresh for ghost-free updates
- [x] Added firmware version system (`version.h`, v0.5.4) — all 20 programs print version + build timestamp at startup
- [x] Added "Clean Build & Deploy" button to DevTool Programs tab
- [x] Changed all display variant defaults from V3 to V4 (CMakeLists, Dockerfile, DevTool dropdown)
- [x] Mk2 translucent case photos converted, named, placed in website assets
- [x] Front page gallery updated with Mk2 translucent + joystick PCB photos
- [x] Blog post and design evolution entries for Mk2 translucent prototype
- [x] Created rolling TODO.md at project root

### Still Open from Handwritten List

> OCR'd from handwritten notes (see `website/docs/assets/images/hardware/handwritten-todo-list-week3-20260504.jpg`)

- [ ] Wire up and test speaker
- [ ] Put a speaker grill cutout for the case
- [ ] Research if wireless firmware deployment is possible to streamline deploy and testing pipeline
- [x] ~~Wednesday: wire up joystick mount~~ (done — wired and tested 2026-05-04)
- [ ] Add a chamfer and joystick retention square so that it fits around snugly the base of the joystick
- [x] ~~Determine a power on/off (leave power) mechanism~~ (done — MSK12C02 slide switch picked, wired in Full Board schematic 2026-05-12)
- [ ] With joystick implement menu and settings system
- [ ] Stand: create a landing page and progression synopsis; purge the stale folders and pointers; perhaps migrate to a V2 repo and project structure
- [~] Compile a schematic for all the planned hardware; scour the web for best components and JLCPCB's basic components (add flash memory, high voltage level components) — *in progress: Full Board schematic now has Pico 2 W, e-ink header, charger, USB-C, accelerometer (SC7A20), joystick (K1-1506SN-01), power switch (MSK12C02). Still needed: speaker/DAC, flash memory*
- [ ] Estimate a board/print cost
- [ ] Run battery life benchmarks
- [ ] Estimate how thin this device could be with a dedicated board

### New Items from Today

- [x] ~~Fix KiCad joystick PCB Rev 2 — re-route with corrected COM/UP pin assignment, re-order from JLCPCB~~ (done — folded into Full Board schematic 2026-05-12 with verified K1-1506SN-01 pin map, no center/up swap)
- [ ] Verify all 5 joystick directions work with corrected wiring (swap COM/UP wires on current board as interim fix)
- [ ] Tune V4 two-pass partial refresh — blacks still slightly washed out with fast waveform, may need custom LUT or voltage adjustment
- [x] ~~Add pin-1 silkscreen dot to future PCB orders to prevent orientation ambiguity~~ (carried forward into Week 5 as a per-footprint reminder)
- [ ] Investigate why V4 display's internal LUT produces weaker blacks than V3's custom LUT — may need to source V3 panels or create hybrid driver
