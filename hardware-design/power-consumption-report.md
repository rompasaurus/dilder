# Power Consumption Report — Dilder Hub

## Current Component Inventory (Testbench)

| Component | Model | Voltage | Typical Current | Peak Current | Duty Cycle | Notes |
|-----------|-------|---------|----------------|-------------|------------|-------|
| Pico 2 W (RP2350 + CYW43) | Pico 2 W | 3.3V via VSYS | 30 mA | 50 mA | 100% | WiFi off baseline; CYW43 init'd for VSYS sense |
| Pico 2 W WiFi active | — | 3.3V | 80-120 mA | 250 mA | Variable | TX bursts during scan/connect; idle ~80 mA |
| E-paper display (2.13" V4) | Waveshare 2.13 V4 | 3.3V | 0.01 mA | 5 mA | ~1% | Static: near-zero; refresh burst ~5 mA for ~2s |
| Active buzzer | 3-12V active | 3.3V | 0 mA | 15 mA | <1% | Only during beeps; off = 0 mA |
| 5-way joystick | K1-1506SN-01 | 3.3V | 0 mA | ~0.1 mA | Passive | Internal pull-ups on GPIOs (~50uA total) |
| MPU-6050 (accel/gyro) | GY-521 module | 3.3V | 3.6 mA | 3.9 mA | 100% | Always on; module regulator quiescent ~0.5 mA |
| TP4056 charger board | TP4056 USB-C | 5V USB in | 2 mA | ~1000 mA | Charging only | Quiescent ~2 mA; charge current set by R_prog |
| Battery | LiPo 1000mAh / 10440 | 3.7V nom | — | — | — | Source, not load |

## Power Budget Summary

### Scenario 1: Idle (WiFi off, display static, no motion polling)

| Component | Current |
|-----------|---------|
| Pico 2 W + CYW43 init | 30 mA |
| E-paper (static) | 0.01 mA |
| Joystick pull-ups | 0.05 mA |
| MPU-6050 | 3.6 mA |
| **Total** | **~34 mA** |

**Battery life (1000 mAh LiPo):** ~29 hours continuous

### Scenario 2: Active use (WiFi off, e-paper refreshing every 3s, motion polling)

| Component | Average Current |
|-----------|----------------|
| Pico 2 W + CYW43 init | 30 mA |
| E-paper (refresh 2s on / 1s off) | ~3.3 mA avg |
| Joystick pull-ups | 0.05 mA |
| MPU-6050 | 3.6 mA |
| Buzzer (occasional) | ~0.5 mA avg |
| **Total** | **~38 mA** |

**Battery life (1000 mAh LiPo):** ~26 hours continuous

### Scenario 3: WiFi active (connected, NTP sync, display refreshing)

| Component | Average Current |
|-----------|----------------|
| Pico 2 W + WiFi connected idle | 80 mA |
| E-paper (refreshing) | ~3.3 mA avg |
| MPU-6050 | 3.6 mA |
| Other | ~0.5 mA |
| **Total** | **~88 mA** |

**Battery life (1000 mAh LiPo):** ~11 hours continuous

### Scenario 4: WiFi scan burst (worst case)

| Component | Peak Current |
|-----------|-------------|
| Pico 2 W + WiFi TX | 250 mA |
| E-paper refresh | 5 mA |
| MPU-6050 | 3.9 mA |
| **Total** | **~260 mA** |

Duration: scan bursts last ~2-5 seconds. TP4056 output can handle this.

## Power Reduction Strategies

### 1. MPU-6050 Sleep Mode (saves ~3.5 mA)

The MPU-6050 has a low-power sleep mode (write 0x40 to PWR_MGMT_1). When not in the MOTION menu:
- Put MPU to sleep: `mpu_write_reg(0x6B, 0x40)`
- Wake on entering MOTION menu: `mpu_write_reg(0x6B, 0x00)`
- **Savings:** 3.5 mA (10% of idle budget)
- **Effort:** Low — add sleep/wake calls to state transitions

### 2. MPU-6050 Cycle Mode (saves ~2.5 mA while still counting steps)

For pedometer-only operation (no live display), use the MPU's cycle mode:
- Wakes at 1.25-40 Hz to sample, sleeps between
- At 5 Hz cycle: ~0.5 mA vs 3.6 mA continuous
- **Savings:** ~3.1 mA
- **Effort:** Medium — configure LP_WAKE_CTRL register, adjust pedometer timing

### 3. Pico 2 W Dormant/Sleep Mode (saves ~25 mA)

The RP2350 supports dormant mode (~0.2 mA) and sleep mode (~1 mA). Implement a Tamagotchi-style duty cycle:
- **Active 10 min:** Full operation, display updates, user input
- **Sleep 50 min:** RP2350 dormant, wake on joystick press (GPIO interrupt) or timer
- **Average current:** ~34 mA * (10/60) + 1 mA * (50/60) = ~6.5 mA
- **Battery life (1000 mAh):** ~6.5 days
- **Effort:** High — requires dormant mode setup, GPIO wake interrupts, state preservation

### 4. CYW43 Deinit When Not Needed (saves ~5-10 mA)

Currently CYW43 is initialized at boot for VSYS sensing. When the full board has TP4056 CHRG/STDBY pins wired:
- Remove CYW43 dependency for battery sensing
- Only init CYW43 when WiFi is actually needed
- **Savings:** ~5-10 mA from CYW43 idle current
- **Effort:** Low (once CHRG/STDBY hardware is in place)

### 5. E-paper Deep Sleep (saves ~0.01 mA — negligible)

The e-paper already draws near-zero in static mode. Calling `EPD_Sleep()` after each refresh would save microamps. Not worth the added wake-up latency.

### 6. Reduce Display Refresh Rate (saves CPU time, indirect power)

On the main octopus screen, refresh every 5-6 seconds instead of 3. Reduces CPU active time. Minimal direct current savings but extends battery slightly.

### 7. WiFi Power Management (saves ~30-50 mA when connected)

When WiFi is connected but idle:
- Enable CYW43 power-save mode: `cyw43_wifi_pm(&cyw43_state, CYW43_PERFORMANCE_PM)`
- Or aggressive PS: `cyw43_wifi_pm(&cyw43_state, CYW43_DEFAULT_PM)` (DTIM-based sleep)
- **Savings:** WiFi idle drops from ~80 mA to ~30-50 mA
- **Effort:** Low — single function call after connect

### 8. Voltage Regulator Efficiency

The Pico 2 W onboard SMPS (RT6154) is ~90% efficient at typical loads. No improvement possible without board redesign. On a custom PCB, a more efficient regulator could save 5-10%.

## Recommended Priority

| Priority | Strategy | Savings | Effort | Impact |
|----------|----------|---------|--------|--------|
| 1 | MPU-6050 sleep when not in MOTION menu | 3.5 mA | Low | Do now |
| 2 | WiFi power-save mode when connected | 30-50 mA | Low | Do now |
| 3 | CYW43 deinit (needs CHRG/STDBY hardware) | 5-10 mA | Low | Full board |
| 4 | MPU cycle mode for background pedometer | 3.1 mA | Medium | Later |
| 5 | Dormant/sleep duty cycle | ~28 mA avg | High | Phase 2 |

## Battery Life Projections (1000 mAh LiPo)

| Configuration | Average mA | Battery Life |
|--------------|-----------|-------------|
| Current (WiFi off, idle) | 34 mA | ~29 hours |
| With MPU sleep (#1) | 30.5 mA | ~33 hours |
| With WiFi PS (#2) when connected | ~55 mA | ~18 hours |
| With MPU sleep + no CYW43 idle (#1+#3) | ~25 mA | ~40 hours |
| Full sleep/wake cycle (#5) | ~6.5 mA | ~6.5 days |
| All optimizations combined | ~4 mA avg | ~10 days |

## Solar Charging Viability

With the AK 62x36mm panel (~5-6V, 80-150 mA peak):
- **Best case (direct sun):** 100 mA in, 34 mA out = net positive, charges battery
- **Typical (indirect/cloudy):** 20-40 mA in, 34 mA out = net negative without sleep cycle
- **With sleep cycle (6.5 mA avg):** Solar easily sustains operation in most daylight conditions
- **Conclusion:** Sleep/wake cycle is essential for solar sustainability
