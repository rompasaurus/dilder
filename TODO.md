# Dilder — Rolling Daily TODO

A living task list updated each week. Newest entries at the top.

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
- [x] IMU pegs nudged -1 mm in Y (`imu_hole_y_inset` 2.0 → 3.0) — peg/hole/washer Y from 28.8 → 27.8 (`<TWEAK_HASH>`)
- [x] Wire channels now open-top slots cut through the full 5 mm BuzzerCradleRing height — wires drop in from above instead of threading through a hole (`<TWEAK_HASH>`)

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
- [ ] Determine a power on/off (leave power) mechanism
- [ ] With joystick implement menu and settings system
- [ ] Stand: create a landing page and progression synopsis; purge the stale folders and pointers; perhaps migrate to a V2 repo and project structure
- [ ] Compile a schematic for all the planned hardware; scour the web for best components and JLCPCB's basic components (add flash memory, high voltage level components)
- [ ] Estimate a board/print cost
- [ ] Run battery life benchmarks
- [ ] Estimate how thin this device could be with a dedicated board

### New Items from Today

- [ ] Fix KiCad joystick PCB Rev 2 — re-route with corrected COM/UP pin assignment, re-order from JLCPCB
- [ ] Verify all 5 joystick directions work with corrected wiring (swap COM/UP wires on current board as interim fix)
- [ ] Tune V4 two-pass partial refresh — blacks still slightly washed out with fast waveform, may need custom LUT or voltage adjustment
- [ ] Add pin-1 silkscreen dot to future PCB orders to prevent orientation ambiguity
- [ ] Investigate why V4 display's internal LUT produces weaker blacks than V3's custom LUT — may need to source V3 panels or create hybrid driver
