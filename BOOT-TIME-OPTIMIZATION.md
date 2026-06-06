# Dilder Hub — Boot-Time Optimization Research

Analysis of what makes `dev-setup/dilder-hub` slow to boot on the Pico 2 W, what
was changed, and what else can be done. Times are estimates for the 2.13" e-ink
+ CYW43 (RP2350) and should be measured on-device (`to_ms_since_boot` around each
phase) to confirm.

## Boot sequence (before optimization)

| Phase | Call(s) in `main()` | Est. cost | Notes |
|---|---|---:|---|
| Serial settle | `stdio_init_all(); sleep_ms(1000)` | **~1000 ms** | Pure delay so early `printf` lands on USB CDC. Useless on battery. |
| RTC seed | `init_rtc_from_compile_time()` | <1 ms | Cheap. |
| Display HW init | `DEV_Module_Init()` | ~50–100 ms | SPI/GPIO setup + panel reset. |
| Inputs/speaker | `joystick_init(); speaker_init()` | <5 ms | Cheap. |
| OTA check | `gpio_get(JOY_UP)` + `sleep_ms(20)` | ~20 ms | Fine. |
| Startup chime | 2 tones + `sleep_ms(30)` ×2 | **~340 ms** | UX; blocking. |
| **e-ink init + clear** | `EPD_Init(); EPD_Clear()` | **~2000–4000 ms** | Full-panel refresh. The single biggest *fixed* cost. |
| CYW43 init | `cyw43_arch_init()` | **~700–1000 ms** | Loads WiFi firmware into the chip. Needed for battery sense (GPIO29) + WiFi. |
| **WiFi auto-connect** | `wifi_connect()` | **up to ~15000 ms** | Blocking `cyw43_arch_wifi_connect_timeout_ms(..., 15000)` + NTP. The dominant variable cost. |
| Battery/IMU | `battery_init(); mpu_init()` | ~30 ms | Cheap. |

**Worst case before:** ~1 + 0.34 + ~3 + ~1 + **15** ≈ **~20 s**. Typical (WiFi
present, connects in ~3 s): ~8 s. The two dominant levers are the **blocking
WiFi connect** and the **e-ink clear**.

## Changes applied

1. **Removed the boot-time WiFi auto-connect** (`wifi_connect()` in `main`).
   This was added as "default WiFi on" and blocked up to 15 s. Credentials are
   now cached (see the saved-networks store), so connecting from the Network
   menu needs no password entry, and the clock NTP-syncs whenever WiFi connects.
   **Win: up to ~15 s.**
2. **Cut the serial settle** `sleep_ms(1000)` → `sleep_ms(50)`. **Win: ~0.95 s.**

Estimated new boot: **~3.5–4.5 s**, dominated by the e-ink clear + CYW43 init.

## Further opportunities (not yet done)

Ordered by payoff / risk.

1. **Skip `EPD_Clear()`, make the first frame a full refresh** (~1–2 s).
   `EPD_Clear()` does a full white refresh purely to establish a clean base for
   later partial updates. Instead, keep `EPD_Init()` and make the *first*
   `render → EPD_Display()` (full) the base, then `EPD_Partial()` thereafter.
   Saves one full-panel cycle. Low risk; needs the first draw to use the full
   update path once.
2. **Show the first frame before CYW43 init.** Move `EPD_Init()` + first render
   earlier and do `cyw43_arch_init()` *after* the UI is on screen, so perceived
   boot is just the e-ink time (~2 s) and the ~1 s CYW43 load happens "behind"
   an already-visible screen. Caveat: GPIO29/VSYS battery sense needs CYW43 up,
   so the first battery icon may be stale for ~1 s — acceptable.
3. **Background / async WiFi connect.** If auto-connect is wanted back, use
   `cyw43_arch_wifi_connect_async()` + poll the result in the main loop instead
   of the 15 s blocking call — fast boot *and* eventual NTP. Moderate effort.
4. **Trim / defer the startup chime** (~0.34 s) or play it non-blocking via PWM
   without the `sleep_ms` gaps.
5. **`cyw43_arch_init` cost** is mostly the firmware blob upload; not much to do,
   but it can run concurrently with the e-ink refresh if reordered (it's SPI to
   a different bus). Measure first.
6. **Faster e-ink LUT.** The V4 driver already uses a custom partial LUT; the
   *init/full* refresh is panel-bound (~2 s) and largely fixed. A "fast full"
   waveform exists on some SSD1680 panels but risks ghosting — low priority.
7. **Measure, don't guess.** Wrap each phase in `to_ms_since_boot()` deltas and
   `printf` them once, to replace these estimates with real numbers before
   chasing smaller wins.

## Recommended next steps

- (Done) remove blocking WiFi connect + trim serial sleep.
- (High value, low risk) #1 skip `EPD_Clear`, first frame = full refresh.
- (High *perceived* value) #2 render the first screen before CYW43 init.
- (Optional) #3 async background WiFi if auto-connect is desired again.

With #1 + #2, a realistic target is **~2–2.5 s to first screen**.
