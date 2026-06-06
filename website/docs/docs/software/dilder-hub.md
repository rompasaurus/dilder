# Dilder Hub — All-In-One Firmware

The combined firmware that brings together all Dilder features: animated octopus with 16 moods, joystick menu navigation, **accelerometer-driven auto-rotation** (wide + tall "longways" layouts), a **step / activity tracker**, WiFi with **saved networks** and NTP clock sync, **Bluetooth LE phone pairing**, **WiFi OTA updates**, an active buzzer with sound patterns, battery monitoring, and navigable menu screens.

---

## Features

| Feature | Details |
|---------|---------|
| **Octopus Display** | 16 animated moods with 823 quotes, RTC clock header, mood-based body transforms |
| **Auto-Rotation** | SC7A20 tilt classifier picks 3 orientations; dedicated wide + tall "longways" layouts (speech-bubble quote above the octopus) |
| **Activity Tracker** | Low-power pedometer — step count + active minutes from the accelerometer, shown on the home screen |
| **Mood Selector** | Joystick-navigable picker for all 16 moods + "ALL (RANDOM)" |
| **WiFi** | CYW43 STA mode, network scanning (sorted by signal), on-screen keyboard for password entry |
| **Saved Networks** | Credentials cached to the last flash sector — survives reboot **and** OTA; save / forget in-menu, no password re-entry (seeded with Moop Ship + MoopsterCell) |
| **NTP Time Sync** | Syncs RTC to pool.ntp.org on WiFi connect (UTC+2 CEST) |
| **Bluetooth LE** | BTstack peripheral "Dilder Hub" — **passkey pairing** (6-digit code on e-ink, MITM-protected) + custom GATT service exposing live mood/steps and a phone command byte |
| **WiFi OTA** | picowota bootloader ported to RP2350 — hold joystick **UP** at boot to reflash over WiFi; USB reflash needs no BOOTSEL button |
| **Sound** | Active buzzer with 6 patterns (beep, chirp, SOS, doorbell, alert, happy), volume control, on/off toggle |
| **Motion** | SC7A20 accelerometer (I²C, 0x18) — live values, pedometer, tilt angles, I2C bus scanner |
| **Set Time** | On-device date/time setter (year → minute) |
| **Device Info** | Firmware version, build date, display variant, battery voltage, WiFi status |
| **Battery Monitor** | ADC3 reads VSYS/3 via CYW43 SPI lock — shows percentage or USB-powered status |
| **Status Icons** | WiFi icon (top-left), Bluetooth rune (shown when paired), battery icon with lightning bolt (top-right) — both orientations |

---

## Screens

### Main Screen (STATE_OCTOPUS)

The default view: animated octopus with mouth cycling, random quotes filtered by current mood, RTC clock header at the top, WiFi status icon top-left, battery icon top-right, and "DOWN:MENU" hint.

The tagline below the speech bubble shows the current mood name (e.g. "- CONSPIRATORIAL -", "- ANGRY -"). When mood is set to ALL, it shows the mood of the current quote.

### Menu (STATE_MENU)

Press joystick DOWN on the main screen. Renders upright in both the wide and tall holds:

1. **MOOD SELECT** — pick a personality
2. **NETWORK** — WiFi on/off, scan, saved networks, status
3. **BLUETOOTH** — pair to a phone (passkey on screen)
4. **SOUND** — test patterns, volume, on/off
5. **MOTION** — accelerometer, pedometer, tilt, I2C scan
6. **DEVICE INFO** — system information
7. **SET TIME** — set date & time
8. **BACK** — return to octopus

Navigate: UP/DOWN to move, CENTER to select, LEFT to go back.

### Mood Selector (STATE_MOOD_SELECT)

Scrollable list of all 16 moods + "ALL MOODS (RANDOM)" at the top. The current selection is highlighted with an inverted bar. Press CENTER to apply — the octopus immediately switches to quotes from that mood and returns to the main screen.

| Mood | Quote Count | Body Animation |
|------|-------------|----------------|
| Normal | 30+ | Gentle breathing bob |
| Weird | 30+ | Lateral sway + body wobble |
| Unhinged | 30+ | Random x/y jitter |
| Angry | 30+ | Trembling + expanded body |
| Sad | 30+ | Drooped posture |
| Chaotic | 30+ | Full-body distortion |
| Hungry | 30+ | Upward reaching |
| Tired | 30+ | Sagging + slow bob |
| Slap Happy | 30+ | Bouncing sway |
| Lazy | 30+ | Lazy tentacle drape |
| Fat | 30+ | Thicc body, no waist |
| Chill | 30+ | Subtle rocking |
| Creepy | 30+ | Slow wobble |
| Excited | 30+ | Fast bouncing |
| Nostalgic | 30+ | Gentle swaying |
| Homesick | 30+ | Drooped + lateral drift |

### Network Menu (STATE_NET_MENU)

A submenu with four options:

- **WIFI: ON/OFF** — toggle WiFi connection (connects to hardcoded SSID or last scanned network)
- **SCAN NETWORKS** — async CYW43 scan, shows scrollable list of discovered SSIDs with lock icon (~) for encrypted networks
- **STATUS** — read-only display of WiFi state, SSID, IP, RSSI, NTP sync
- **BACK** — return to main menu

### WiFi Scan (STATE_NET_SCAN)

Shows "SCANNING... FOUND: N" during the async scan (refreshes every 500ms). When complete, displays a scrollable list of up to 16 networks. Selecting an open network connects immediately. Selecting an encrypted network opens the on-screen keyboard.

### On-Screen Keyboard (STATE_NET_KEYBOARD)

Full keyboard for WiFi password entry:

- 4 rows of 10 characters (QWERTY layout + numbers + punctuation)
- 5 special keys: SHIFT (toggle CAPS/lowercase), SPC, DEL, DONE, CANCEL
- CAPS/LOW indicator next to password field
- Navigate with joystick, CENTER to select

### Sound Menu (STATE_SOUND)

- **TONE: [pattern name]** — LEFT/RIGHT cycles through 6 patterns, CENTER plays
- **SOUND: ON/OFF** — global toggle
- **VOLUME: LOW/MED/HIGH** — controls beep duration (20/50/100ms)
- **BACK** — return to main menu

Sound patterns: BEEP, CHIRP, SOS, DOORBELL, ALERT, HAPPY. All are rhythmic on/off sequences (active buzzer has fixed pitch).

### Motion Menu (STATE_MOTION)

Scrolling menu with live sensor data from the MPU-6050:

- **ACCEL: X Y Z (g)** — live accelerometer values
- **STEPS: N** — pedometer count
- **TILT: X Y (deg) + temperature** — tilt angles and chip temperature
- **RESET PEDOMETER** — zero the step counter
- **THRESHOLD: N.Ng** — adjustable step detection threshold (0.8g-2.5g)
- **I2C BUS SCAN** — scans all I2C addresses, identifies known devices
- **BACK** — return to main menu

Gyro readout and acceleration magnitude displayed at the bottom. Refreshes every 500ms for live data.

### Device Info (STATE_INFO)

- Firmware version and display variant
- Build date and time
- Live RTC clock (network time if WiFi connected)
- Current mood and quote count
- WiFi status and IP
- Battery: percentage and voltage (or "USB" with voltage)
- Board: PICO 2 W RP2350

---

## Hardware Wiring

| Component | Pin | GPIO | Function |
|-----------|-----|------|----------|
| Display CS | 22 | GP17 | SPI0 CSn |
| Display CLK (SCL) | 24 | GP18 | SPI0 SCK |
| Display DIN (SDA) | 25 | GP19 | SPI0 TX |
| Display DC | 26 | GP20 | Data/command |
| Display RST (RES) | 27 | GP21 | Reset |
| Display BUSY | 29 | GP22 | Busy flag |
| Joystick L | 4 | GP2 | Left |
| Joystick D | 5 | GP3 | Down |
| Joystick UP | 6 | GP4 | Up |
| Joystick R | 7 | GP5 | Right |
| Joystick C | 9 | GP6 | Center/push |
| Buzzer + | 19 | GP14 | GPIO out (active buzzer) |
| Buzzer - | 18 | GND | Ground |
| MPU-6050 SDA | 1 | GP0 | I2C0 data |
| MPU-6050 SCL | 2 | GP1 | I2C0 clock |
| MPU-6050 VCC | 36 | 3V3(OUT) | Shared with display |
| MPU-6050 GND | 33 | GND | Ground |
| Battery sense | — | GP29 | ADC3 (VSYS/3, CYW43 shared) |
| TP4056 OUT+ | 39 | VSYS | Battery/charger power input |
| TP4056 OUT- | 38 | GND | Ground |

### Active Buzzer

Single GPIO pin drive — GP14 HIGH to buzz, LOW to silence. No PWM needed. Volume is controlled by adjusting beep duration (20/50/100ms). The old push-pull piezo driver was replaced because active buzzers have a built-in oscillator.

### MPU-6050 (I2C)

I2C0 at 400kHz. The GY-521 module has onboard pull-ups. Firmware auto-detects the device at 0x68 or 0x69 (depending on AD0 pin state). See [MPU-6050 wiring guide](../../../docs/mpu6050-wiring-guide.md) for full details.

### Battery Sensing

GPIO 29 (ADC3) reads VSYS/3 through an onboard voltage divider. On the Pico W/2 W, GPIO 29 is shared with the CYW43 WiFi chip's SPI bus. The firmware locks the CYW43 driver (`cyw43_thread_enter/exit`) during ADC reads. CYW43 must be initialized at boot even without WiFi for this to work.

---

## WiFi Configuration

Edit `dev-setup/dilder-hub/wifi_config.h`:

```c
#define WIFI_SSID  "YourNetwork"
#define WIFI_PASS  "YourPassword"
#define NTP_SERVER "pool.ntp.org"
#define TIMEZONE_OFFSET_SEC  7200   // UTC+2 (CEST)
```

Or pass via cmake: `-DWIFI_SSID="YourNetwork" -DWIFI_PASS="YourPassword"`

---

## Building

### Via DevTool

1. Open the Picotool tab
2. Select "Dilder Hub" from the firmware list
3. Click "Clean Build & Flash"

### Via Command Line

```bash
cd dev-setup
docker compose run --rm \
  -e DISPLAY_VARIANT=V4 \
  -e PICO_BOARD=pico2_w \
  build-dilder-hub
```

Output: `dev-setup/dilder-hub/build/dilder_hub.uf2`

---

## Source

- Firmware: `dev-setup/dilder-hub/main.c` (~1,935 lines)
- Quotes: `dev-setup/dilder-hub/quotes.h` (823 quotes, all 16 moods)
- Build: `dev-setup/dilder-hub/CMakeLists.txt`
- WiFi: `dev-setup/dilder-hub/wifi_config.h`
- Display driver: `dev-setup/hello-world/lib/e-Paper/EPD_2in13_V4.c` (shared)
