# Motion & Location Detection — Design Plan

> How the Dilder detects movement, counts steps, senses gestures, and knows when you've gone somewhere new — all without GPS, using a $0.46 accelerometer and the ESP32-S3's built-in WiFi and BLE.

---

## Table of Contents

1. [Design Goals](#1-design-goals)
2. [Hardware — LIS2DH12TR Accelerometer](#2-hardware--lis2dh12tr-accelerometer)
3. [Motion Detection — What the Accelerometer Provides](#3-motion-detection--what-the-accelerometer-provides)
4. [Location Detection — WiFi Fingerprinting](#4-location-detection--wifi-fingerprinting)
5. [Location Detection — BLE Scanning](#5-location-detection--ble-scanning)
6. [Integration with Pet Logic](#6-integration-with-pet-logic)
7. [Power Budget](#7-power-budget)
8. [Why Not GPS?](#8-why-not-gps)
9. [Implementation Phases](#9-implementation-phases)
10. [Sources](#10-sources)

---

## 1. Design Goals

The Dilder is a virtual pet. It doesn't need to know its precise latitude and longitude. It needs to answer simpler questions:

| Question | Method | Hardware |
|----------|--------|----------|
| **Is the user walking?** | Step counter (hardware pedometer) | LIS2DH12 |
| **Did the user shake me?** | Tap/shake interrupt | LIS2DH12 |
| **Am I being carried or sitting still?** | Activity/inactivity detection | LIS2DH12 |
| **Am I at the same place as before?** | WiFi AP fingerprint delta | ESP32-S3 WiFi (built-in) |
| **Are other Dilders nearby?** | BLE scan for peer devices | ESP32-S3 BLE (built-in) |
| **Am I upside down?** | Orientation detection | LIS2DH12 |

All of this is achieved with **zero additional hardware beyond the LIS2DH12** — the ESP32-S3 provides WiFi and BLE natively.

---

## 2. Hardware — LIS2DH12TR Accelerometer

### Why LIS2DH12TR

The original design used the MPU-6050 (6-axis IMU with gyroscope) at **$6.88**. The gyroscope is unnecessary for step counting and gesture detection. The LIS2DH12TR is a 3-axis accelerometer with a **built-in hardware pedometer** that handles step counting in silicon, waking the MCU only when needed.

### Specifications

| Attribute | Value |
|-----------|-------|
| **Part** | STMicroelectronics LIS2DH12TR |
| **Axes** | 3 (X, Y, Z accelerometer only — no gyroscope) |
| **Resolution** | 12-bit (high-resolution mode), 10-bit, or 8-bit selectable |
| **Range** | +/-2g, +/-4g, +/-8g, +/-16g selectable |
| **Interface** | I2C (up to 400kHz) / SPI (up to 10MHz) |
| **Address** | 0x18 (SA0=GND) or 0x19 (SA0=VCC) |
| **Package** | LGA-12 (2x2mm) — same footprint as MPU-6050's QFN-24 is larger, this is smaller |
| **Supply** | 1.71V to 3.6V |
| **Current (normal)** | 185uA @ 400Hz ODR |
| **Current (low power)** | 2uA @ 1Hz ODR |
| **Current (power down)** | 0.5uA |
| **Built-in features** | Pedometer (step counter + step detector interrupt), click/double-click detection, free-fall detection, wake-up/activity recognition, 6D/4D orientation detection, temperature sensor |
| **FIFO** | 32-level, reduces I2C/SPI traffic |
| **LCSC** | [C110926](https://www.lcsc.com/product-detail/C110926.html) |
| **Price** | **$0.46** (qty 5) |

### Pin Connections (Dilder Board)

| LIS2DH12 Pin | ESP32-S3 GPIO | Function |
|--------------|---------------|----------|
| SDA/SDI | GPIO16 | I2C data |
| SCL/SPC | GPIO17 | I2C clock |
| SA0/SDO | GND | Sets I2C address to 0x18 |
| CS | VCC (3.3V) | Pulled high to select I2C mode (not SPI) |
| INT1 | GPIO18 (TBD) | Step detector interrupt / activity wakeup |
| INT2 | N/C | Not connected (single interrupt sufficient) |
| VDD | 3.3V | Power |
| GND | GND | Ground |

### Cost Savings

| Component | Old | New | Savings |
|-----------|-----|-----|---------|
| Sensor IC | MPU-6050 ($6.88) | LIS2DH12TR ($0.46) | **-$6.42** |
| I2C pull-ups | 2x 10k (same) | 2x 10k (same) | $0.00 |
| GPS module | ATGM336H ($1.80 planned) | Dropped | **-$1.80** |
| **Total sensor savings** | | | **-$8.22/board** |

---

## 3. Motion Detection — What the Accelerometer Provides

### 3.1 Step Counting (Hardware Pedometer)

The LIS2DH12 has a **built-in step counter** that runs in hardware even when the ESP32-S3 is in deep sleep:

- The pedometer algorithm runs inside the LIS2DH12 at ~2uA
- A step counter register (16-bit) accumulates steps
- INT1 can fire a **step detector interrupt** on each detected step, or a **significant motion interrupt** after a configurable threshold
- The ESP32-S3 reads the step count register during each wake cycle (e.g. every 10 minutes in Tamagotchi mode)

**No software step-counting algorithm needed.** The LIS2DH12 handles it in silicon.

```
ESP32-S3 (deep sleep, 10uA)     LIS2DH12 (pedometer active, 2uA)
         |                                |
         |     [user walks 500 steps]     |
         |                                | step_count += 500
         |                                |
    [wake every 10 min] ────── I2C read ──► step_count = 500
         |                                |
    "You walked 500 steps!"               |
    [update display, sleep]               |
```

### 3.2 Shake / Tap Detection

The LIS2DH12 has hardware **click/double-click detection** on all three axes:

- **Single tap** — user taps the device (e.g. "pet the octopus")
- **Double tap** — user double-taps (e.g. "feed the octopus")
- **Shake** — high-g activity on multiple axes (e.g. "wake up!" or "you're scaring me")

Each generates a hardware interrupt — the ESP32-S3 doesn't need to poll.

### 3.3 Activity / Inactivity Detection

- **Activity interrupt** — fires when acceleration exceeds a threshold (user picked up the device)
- **Inactivity interrupt** — fires when acceleration stays below threshold for N seconds (device put down)

This lets the pet know:
- "I'm being carried" (activity + steps)
- "I'm sitting on a desk" (inactivity)
- "I'm in a pocket" (occasional movement but no steps)

### 3.4 Orientation Detection (6D)

The LIS2DH12 can detect which face of the device is pointing up:

- **Face up** — display visible (normal operation)
- **Face down** — display hidden (sleep mode? privacy mode?)
- **Tilted left/right/forward/back** — could map to pet interactions

### 3.5 Free-Fall Detection

Detects when the device is in free fall (all axes read ~0g). Could trigger:
- "You dropped me!" reaction
- Save state before potential impact

---

## 4. Location Detection — WiFi Fingerprinting

### How It Works

The ESP32-S3 scans for nearby WiFi access points and records their BSSIDs (MAC addresses) and signal strengths (RSSI). This creates a "fingerprint" of the current location.

```
Location A (home):          Location B (office):
  BSSID_1: -45 dBm           BSSID_5: -30 dBm
  BSSID_2: -60 dBm           BSSID_6: -55 dBm
  BSSID_3: -70 dBm           BSSID_7: -70 dBm
  
  Hash: 0xA3F2                Hash: 0x7C91
  → Different hashes = different location!
```

### Algorithm

1. During each active wake cycle, scan WiFi (takes ~2 seconds)
2. Collect top-5 strongest BSSIDs + their RSSI values
3. Hash the BSSID list → produces a location fingerprint
4. Compare with the previous fingerprint:
   - **Same hash** → same location → pet is stationary
   - **Different hash** → new location → pet was taken somewhere!
   - **No APs found** → outdoors or rural → pet is on an adventure

### Accuracy

| Environment | Accuracy | Notes |
|-------------|----------|-------|
| Dense urban | ~20-50m | Many overlapping APs |
| Suburban | ~50-100m | Fewer APs, wider spacing |
| Rural / outdoors | Cannot detect | No WiFi APs to fingerprint |
| Indoors (same building) | Room-level | Different rooms have distinct RSSI patterns |

### Power Cost

- WiFi scan: ~80mA for ~2 seconds = **~0.044 mAh per scan**
- At 1 scan per 30 minutes: **~0.088 mAh/hour** — negligible impact on battery life
- Compare to GPS: 25mA continuous tracking = orders of magnitude more power

### What It Can't Do

- No absolute coordinates (lat/lon) — just "same place" vs "different place"
- Doesn't work in areas with no WiFi coverage
- Can't measure distance traveled

For absolute coordinates, use the **WiFi Geolocation API** (Option 3 below) which sends the BSSID list to a cloud service and gets back approximate lat/lon. This requires an internet connection but is free (Google: 40k requests/month, Mozilla Location Service: unlimited).

---

## 5. Location Detection — BLE Scanning

### How It Works

The ESP32-S3 scans for nearby BLE advertisements. This serves two purposes:

1. **Peer discovery** — Find other Dilder devices for social interactions (already planned for the engagement system)
2. **Environment fingerprinting** — BLE devices (phones, smart watches, fitness trackers) create a rough signature of the current environment

### Power Cost

- BLE scan: ~15mA for ~3 seconds = **~0.012 mAh per scan**
- ~5x more power-efficient than WiFi scanning

### Best Used For

- Detecting other Dilders nearby (mating system, social interactions)
- Counting nearby BLE devices as a proxy for "busy location" vs "quiet location"
- Augmenting WiFi fingerprinting with BLE data for better location delta detection

---

## 6. Integration with Pet Logic

### Sensor Events → Pet Behaviors

| Sensor Event | Pet Interpretation | Game Effect |
|-------------|-------------------|-------------|
| Steps > 500 in a wake cycle | "We went for a walk!" | +happiness, +health, unlock "adventure" dialogue |
| Steps > 2000 in a day | "Big adventure!" | +XP, possible evolution trigger, treasure hunt progress |
| Shake detected | "Hey! That's rude!" or "Wheee!" | Mood-dependent reaction |
| Single tap | "Oh, a pet!" | +happiness (if not angry) |
| Double tap | "Feed me!" | Trigger feeding interaction |
| Free fall | "AAAAAHHH!" | -happiness, panic expression |
| Face down | "It's dark in here..." | Enter sleep/sulk mode |
| WiFi fingerprint changed | "New place! What's this?" | +curiosity, new location dialogue, exploration XP |
| WiFi fingerprint same (24h+) | "We never go anywhere..." | -happiness (homesick/bored) |
| BLE: other Dilder found | "A friend!" | Trigger peer interaction / mating |
| Inactivity > 1 hour | "...hello? Anyone there?" | Lonely mood, attention-seeking quotes |

### Data Persistence

Store in ESP32-S3 NVS (non-volatile storage):
- `daily_steps` — reset at midnight
- `total_steps` — lifetime counter
- `last_wifi_hash` — for location delta comparison
- `locations_visited` — count of unique WiFi fingerprints seen
- `last_activity_time` — for inactivity detection

---

## 7. Power Budget

### Motion + Location Detection Power

| Source | Current | Duration | Frequency | Avg mA |
|--------|---------|----------|-----------|--------|
| LIS2DH12 pedometer (always on) | 2uA | Continuous | Always | 0.002 |
| LIS2DH12 interrupt wake | 0uA (ESP32 handles) | — | Per-step | 0.000 |
| WiFi scan (location fingerprint) | 80mA | 2 sec | Every 30 min | 0.089 |
| BLE scan (peer discovery) | 15mA | 3 sec | Every 30 min | 0.025 |
| I2C step count read | 5mA | 10ms | Every 10 min | 0.000 |
| **Total detection overhead** | | | | **~0.116 mA** |

This adds **~0.1 mA average** to the power budget — less than 2% of the Tamagotchi mode baseline (~5.5 mA average). Battery life impact: effectively zero.

### Comparison with GPS

| Method | Avg current | Battery impact (1000mAh) |
|--------|-------------|-------------------------|
| **LIS2DH12 + WiFi/BLE scans** | **~0.1 mA** | **Negligible (<2%)** |
| GPS (always tracking) | 25 mA | -4.3 days battery life |
| GPS (periodic fix, 1/30min) | ~1.5 mA avg | -1.1 days battery life |

---

## 8. Why Not GPS?

| Factor | GPS | WiFi + Accelerometer |
|--------|-----|---------------------|
| **Component cost** | $1.80-4.00 | $0.00 (WiFi built-in) |
| **Power draw** | 20-45mA active | 0.1mA average |
| **Board space** | ~12x12mm module + antenna | 0mm (no additional component) |
| **Works indoors** | No (needs sky view) | Yes |
| **Cold start time** | 30-60 seconds | Instant |
| **Accuracy outdoors** | 2.5m | ~50-100m (WiFi), or step count only |
| **Accuracy indoors** | Doesn't work | Room-level (WiFi fingerprint) |
| **Complexity** | UART driver + NMEA parsing + antenna design | WiFi scan API (built-in) |

GPS is overkill for a virtual pet. The pet doesn't need to know it's at 48.1351°N, 11.5820°E. It needs to know "you took me somewhere new" and "you're walking." WiFi fingerprinting + step counting provides exactly that at zero additional cost and negligible power.

**GPS stays in the design as a Phase 7 optional add-on** for users who want real geocaching/treasure-hunt features. The board can be designed with unpopulated GPS pads for future hand-soldering.

---

## 9. Implementation Phases

### Phase 2 (Current) — Hardware Foundation

- [x] LIS2DH12TR selected and added to BOM ($0.46 replaces $6.88 MPU-6050)
- [x] I2C wiring planned (GPIO16/17, same bus as the old MPU-6050 plan)
- [ ] Update KiCad schematic with LIS2DH12 footprint and connections
- [ ] Verify LIS2DH12 LCSC stock and JLCPCB assembly compatibility

### Phase 3 — Pet Logic (Firmware)

- [ ] Initialize LIS2DH12 over I2C (set ODR, range, enable pedometer)
- [ ] Enable step detector interrupt on INT1
- [ ] Read step count register during each wake cycle
- [ ] Implement shake/tap detection via click interrupt
- [ ] Map accelerometer events to pet mood changes

### Phase 4 — Location Awareness (Firmware)

- [ ] Implement WiFi AP scan during active wake
- [ ] Hash top-5 BSSIDs into location fingerprint
- [ ] Store fingerprint in NVS, compare with previous
- [ ] Trigger "new location" pet event on fingerprint delta
- [ ] Implement BLE scan for peer Dilder discovery

### Phase 7 — Optional GPS Expansion

- [ ] Design unpopulated GPS pads on PCB (ATGM336H footprint)
- [ ] Implement UART GPS driver (for users who hand-solder the module)
- [ ] WiFi Geolocation API integration (cloud-based lat/lon from BSSID list)
- [ ] Geocaching / treasure hunt features using approximate coordinates

---

## 10. Sources

- [LIS2DH12TR Datasheet (STMicroelectronics)](https://www.st.com/resource/en/datasheet/lis2dh12.pdf)
- [LIS2DH12 on LCSC — C110926](https://www.lcsc.com/product-detail/C110926.html) — $0.46
- [AN-2554: Step Counting Using ADXL367 (Analog Devices)](https://www.analog.com/en/resources/app-notes/an-2554.html) — pedometer algorithm reference
- [Ultra-low power IMU for step counting (ST Community)](https://community.st.com/t5/mems-sensors/ultra-low-power-imu-for-step-counting/td-p/176779)
- [WiFi RSSI-Based Localization Using ESP32 (IIT Bombay)](https://github.com/ani8897/RSSI-based-Localization-using-ESP32)
- [WiFi Indoor Positioning on Arduino](https://eloquentarduino.github.io/2019/12/wifi-indoor-positioning-on-arduino/)
- [Google Geolocation API](https://developers.google.com/maps/documentation/geolocation/overview) — free tier: 40k requests/month
- [Mozilla Location Service](https://location.services.mozilla.com/) — fully free, open-source

---

*Document version: 1.0 — 2026-04-15*
