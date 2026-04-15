# Weather Detection for Dilder — Hardware Brainstorm

How to get weather data into Jamal's world so environments react to real conditions.

---

## Option 1: WiFi Weather API (Free, No Extra Hardware)

**The cheapest option: $0, 0 components, 0 GPIO pins.**

The ESP32-S3 already has WiFi active (used for location fingerprinting). Piggyback a weather API call onto the existing WiFi connection.

### How It Works
```
ESP32-S3 WiFi -> HTTPS GET -> OpenWeatherMap API -> JSON parse -> weather state
```

### Free API Options
| Service | Free Tier | Update Interval | Data |
|---------|-----------|----------------|------|
| OpenWeatherMap | 1,000 calls/day | Every 86s (~15min is fine) | temp, humidity, pressure, conditions, icon |
| WeatherAPI.com | 1M calls/month | ~2.8s (use 15min) | Same + UV, air quality |
| Open-Meteo | Unlimited | 15min granularity | No API key needed, EU-based |

### Implementation
```c
// Poll every 15 minutes (e-ink doesn't need faster updates)
// Parse JSON for: temp_c, humidity, condition_code
// condition_code maps to environment modulation:
//   200-299: Thunderstorm -> lightning aura
//   300-499: Rain/Drizzle -> rain overlay
//   500-599: Rain -> heavy rain overlay
//   600-699: Snow -> snow overlay
//   800:     Clear -> sun_rays / stars (day/night)
//   801-804: Clouds -> clouds overlay
typedef struct {
    int8_t temp_c;
    uint8_t humidity;
    uint16_t condition;  // OWM condition code
    bool is_night;
} weather_t;
```

### Pros
- Zero extra cost, zero extra hardware, zero extra power draw
- Rich data (temp, humidity, forecast, UV, sunrise/sunset)
- Works indoors (where most Tamagotchis live)
- Can show weather for ANY location (home, travel, etc.)

### Cons
- Needs WiFi connected (already required for location)
- No hyperlocal accuracy (reports city-level weather)
- ~200ms latency per API call (do it in background, non-blocking)

### Power Cost
One HTTPS request every 15 minutes adds ~0.5mA average to the WiFi budget (ESP32-S3 already waking for location scans). Negligible.

**Verdict: Do this first. It's free and the ESP32-S3 already has WiFi.**

---

## Option 2: BME280 Sensor (Best Bang-for-Buck Hardware)

**~$2-3, 1 component, shares existing I2C bus.**

### What You Get
| Measurement | Range | Resolution |
|-------------|-------|------------|
| Temperature | -40 to +85°C | 0.01°C |
| Humidity | 0-100% RH | 0.008% |
| Barometric Pressure | 300-1100 hPa | 0.18 Pa |

### Why Pressure Matters
Barometric pressure trends predict weather changes **before they happen**:
- Pressure dropping fast (>2 hPa/hr) -> storm incoming
- Pressure rising -> clearing up
- Steady low pressure -> overcast/rainy
- Steady high pressure -> fair weather

This gives Jamal **weather prescience** — he can react to weather changes before they're visible outside. "Jamal feels a storm coming" is way more charming than "the API says rain."

### Wiring
```
BME280       ESP32-S3
------       --------
VCC    ->    3.3V
GND    ->    GND
SDA    ->    GPIO16 (shared with accelerometer)
SCL    ->    GPIO17 (shared with accelerometer)
```

The I2C bus already has 10k pull-ups for the LIS2DH12TR accelerometer. The BME280 default address is **0x76** (accelerometer is 0x18) — no conflict.

### PCB Impact
- Add 1 footprint: LGA-8 (2.5x2.5mm) or breakout header
- No new traces needed if placed near existing I2C bus
- Could be mounted on the back of the PCB for ambient sensing

### Power
- Normal mode: 3.6μA (one measurement per second)
- Forced mode (on-demand): <1μA average at 1 reading/minute
- Sleep: 0.1μA

### Code Size
BME280 I2C driver: ~500 bytes flash, ~20 bytes RAM for calibration data.

**Verdict: Best hardware option. Shares I2C bus, tiny, cheap, gives pressure-based weather prediction.**

---

## Option 3: Combo Approach (API + BME280)

**The "best of both worlds" — use BOTH for maximum weather awareness.**

| Source | What It Provides | Update Rate |
|--------|-----------------|-------------|
| WiFi API | Conditions (rain/snow/sun), forecast, sunrise/sunset | Every 15 min |
| BME280 | Ambient temp, humidity, pressure **trend** | Every 1 min |

### Fusion Logic
```c
// API gives the "official" weather
// BME280 gives the local/indoor reality + pressure predictions

weather_state_t get_weather() {
    weather_state_t w = api_weather;  // base from API

    // Override with local conditions
    if (bme_temp < 10) w.feels_cold = true;   // Jamal shivers
    if (bme_humidity > 80) w.feels_muggy = true;

    // Pressure trend prediction (last 3 hours)
    float dp = pressure_now - pressure_3h_ago;
    if (dp < -3.0) w.storm_incoming = true;   // "Jamal senses a storm"
    if (dp > 3.0) w.clearing_up = true;       // "Jamal feels the sun coming"

    return w;
}
```

This creates **two layers of weather personality:**
1. API-driven: Jamal knows it's raining outside (rain overlay, sad modulation)
2. Sensor-driven: Jamal *feels* the room (shivers if cold, sweats if humid, senses storms)

---

## Option 4: Cheap Trick — LDR (Light Sensor)

**~$0.10, 1 resistor + 1 LDR, 1 ADC pin.**

A light-dependent resistor on an ADC pin gives day/night detection and crude cloud cover estimation.

### Wiring
```
3.3V -> LDR -> ADC_PIN (GPIO1/2/3) -> 10kΩ -> GND
```

Voltage divider. Read ADC value:
- High value = bright = daytime/sunny
- Medium = cloudy/overcast
- Low = nighttime/dark room

### What It Enables
- Automatic day/night environment switching (bedroom at night, park during day)
- "Jamal notices it's getting dark" personality triggers
- Crude indoor/outdoor detection (fluorescent vs sunlight spectrum varies, but ADC can't distinguish)

### Limitation
Only measures **light at the device location**, not actual weather. But combined with an API, it tells you "is the device in a bright or dark room" which is useful for Tamagotchi personality.

**Verdict: Cute party trick for $0.10. Add it if you have a spare ADC pin.**

---

## Option 5: Rain Sensor Module

**~$1, but requires outdoor exposure.**

Analog rain detector PCB. Resistance drops when water bridges the traces.

### Why It Probably Doesn't Work Here
- Needs to be **outdoors** or near a window
- Tamagotchi lives indoors on a desk
- Corrosion over time degrades the sensor
- Already solved better by WiFi API

**Verdict: Skip. The API does this better without hardware.**

---

## Recommendation

### Phase 1: WiFi API (implement now, zero cost)
- OpenWeatherMap or Open-Meteo free tier
- Poll every 15 minutes in background
- Map condition codes to environment overlays + emotion modulation
- Already have WiFi connected for location

### Phase 2: BME280 (add to next PCB revision)
- $2-3, shares I2C bus, tiny footprint
- Pressure trend prediction ("Jamal feels a storm coming")
- Room temperature/humidity awareness ("Jamal is cold/hot/muggy")
- Combines with API for rich weather personality

### Phase 3 (Optional): LDR for day/night
- $0.10, automatic day/night switching
- Only if a spare ADC pin is available on the next PCB

---

## How Weather Maps to the Asset System

```
Weather State           Environment Modulation      Aura Effect
─────────────          ─────────────────────       ────────────
Clear/Sunny            sun_rays overlay             warm sparkle dots
Cloudy                 clouds overlay               muted aura (slower)
Rain                   rain overlay (density=API)   sad tears amplified
Heavy Rain             rain overlay (density=max)   chaotic wobble added
Thunderstorm           rain + lightning overlay      unhinged static noise
Snow                   snow overlay                 gentle drift particles
Wind                   wind streaks overlay          aura particles drift faster
Hot (>30°C)            heat shimmer effect           sweat drops near head
Cold (<5°C)            (no overlay)                 shiver wobble on body
Storm Incoming (BME)   darkening sky gradient        anticipation particles
Night                  swap to night variant env     stars in aura
```

The weather overlays from `decor/weather.py` are already implemented and ready to be triggered by real weather data. The composition pipeline in `compose.py` has the hook point at step 12 (weather overlay) waiting to be wired up.
