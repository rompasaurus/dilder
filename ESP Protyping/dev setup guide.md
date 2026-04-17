# Dev Setup Guide — Multi-Board Code Changes & Deployment Walkthrough

> Step-by-step guide covering the multi-board architecture, the code changes made to support both the **Pico W (RP2040)** and the **Olimex ESP32-S3-DevKit-Lipo**, and how to go from a bare board to running firmware through the DevTool or terminal. Each deployment step includes board-specific options where the instructions differ.

---

## Choosing Your Board

Before you begin, decide which board you're setting up. Steps that are the same for both boards show a single set of instructions. Steps that differ show clearly marked options:

> **Pico W** — The Raspberry Pi Pico W (RP2040). HAT plugs directly onto the headers — no breadboard wiring. Uses the ARM GCC toolchain and CMake/Ninja. Flash via BOOTSEL + UF2.

> **ESP32-S3 (Olimex)** — The Olimex ESP32-S3-DevKit-Lipo. Uses breadboard + jumper wires. Uses PlatformIO + Arduino/ESP-IDF. Flash via USB-UART + esptool.

The setup CLI also supports board filtering:

```bash
python3 setup.py --board pico    # only Pico W steps
python3 setup.py --board esp32   # only ESP32-S3 steps
python3 setup.py                 # all steps for both boards
```

---

## Table of Contents

1. [What Changed — Overview](#1-what-changed--overview)
2. [New Files Created](#2-new-files-created)
3. [Modified Files](#3-modified-files)
4. [Architecture — How Multi-Board Works](#4-architecture--how-multi-board-works)
   - [4.1 Compile-Time Board Selection (C)](#41-compile-time-board-selection-c)
   - [4.2 Runtime Board Selection (DevTool)](#42-runtime-board-selection-devtool)
   - [4.3 Pin Mapping Comparison](#43-pin-mapping-comparison)
5. [Prerequisites](#5-prerequisites)
6. [Step 1 — Install Toolchain](#6-step-1--install-toolchain)
7. [Step 2 — Verify USB Serial Driver](#7-step-2--verify-usb-serial-driver)
8. [Step 3 — Wire the Board](#8-step-3--wire-the-board)
9. [Step 4 — Build & Flash from Terminal](#9-step-4--build--flash-from-terminal)
10. [Step 5 — Build & Flash from DevTool](#10-step-5--build--flash-from-devtool)
11. [Step 6 — Verify Everything Works](#11-step-6--verify-everything-works)
12. [The Automated Way — setup.py](#12-the-automated-way--setuppy)
13. [Troubleshooting](#13-troubleshooting)
14. [File Reference](#14-file-reference)

---

## 1. What Changed — Overview

The Dilder project previously only targeted the **Raspberry Pi Pico W (RP2040)**. These changes add the **Olimex ESP32-S3-DevKit-Lipo** as a second deployment target. Everything is designed so you can switch between boards without changing any game engine code — the pin assignments, SPI controller, and hardware I/O are abstracted behind a compile-time config header and a runtime board selector in the DevTool GUI.

**Summary of changes:**

| Area | What | Why |
|------|------|-----|
| **DevTool** | Board selector dropdown, ESP32 serial detection, esptool flash support | Switch deployment target with one click |
| **Firmware** | `board_config.h` pin abstraction, `hal.h` interface, ESP32 HAL implementation | Same game engine code runs on both boards |
| **PlatformIO project** | `platformio.ini` + `main.cpp` in `ESP Protyping/dilder-esp32/` | Build system for the ESP32-S3 with all dependencies |
| **setup.py** | Step 16 — PlatformIO + esptool + ESP-IDF installation | One-command toolchain setup |

---

## 2. New Files Created

### Firmware Platform Layer

```
firmware/
  include/
    platform/
      board_config.h    ← Compile-time pin definitions for all boards
      hal.h             ← Hardware abstraction interface (SPI, buttons, LED, battery)
  src/
    platform/
      esp32s3/
        esp32s3_hal.c   ← ESP32-S3 HAL implementation (Arduino framework)
```

### PlatformIO Project

```
ESP Protyping/
  dilder-esp32/
    platformio.ini      ← Build config: board, framework, libraries, flags
    src/
      main.cpp          ← ESP32-S3 entry point: display test + joystick handler
    include/            ← (empty, for project-local headers)
```

---

## 3. Modified Files

### `DevTool/devtool.py`

| Change | Details |
|--------|---------|
| Version bumped | `1.0.0` → `1.1.0` |
| Board constants | `BOARD_PICO_W`, `BOARD_ESP32S3`, `BOARD_LABELS` dict |
| `find_esp32_serial()` | Detects Olimex board via CH340X VID `0x1A86` on `/dev/ttyUSB*` |
| `find_serial_for_board(board)` | Unified serial detection that routes by selected board |
| `DilderDevTool._build_ui()` | Board selector toolbar added above the notebook tabs |
| `DilderDevTool._on_board_changed()` | Switches pin viewer, flash utility, and serial detection |
| `FlashUtility` | Rebuilt to support both Pico (BOOTSEL + UF2) and ESP32 (esptool + .bin) |
| `PinViewer` | Shows Olimex ESP32-S3 pinout when ESP board selected |
| `ProgramsTab` | Deploy button is board-aware, flash size adjusts (2 MB Pico / 8 MB ESP32) |

### `firmware/CMakeLists.txt`

Added `TARGET_BOARD` CMake variable with `add_compile_definitions(BOARD_${TARGET_BOARD})`. Defaults to `DESKTOP` for the shared library build.

### `setup.py`

- Docstring and banner updated to mention both boards
- `ESP32_PROJECT` path constant added
- **Step 16** added: installs PlatformIO CLI, esptool, checks CH340X driver, verifies project, pre-downloads ESP32-S3 platform
- `show_status()` now reports PlatformIO version, esptool, ESP32 project state, and `/dev/ttyUSB*` detection

---

## 4. Architecture — How Multi-Board Works

### 4.1 Compile-Time Board Selection (C)

The header `firmware/include/platform/board_config.h` uses preprocessor guards to define the same set of macros for each board:

```c
// Set at build time:
//   PlatformIO:  build_flags = -DBOARD_ESP32S3
//   CMake:       cmake -DTARGET_BOARD=ESP32S3 ..
//   Pico SDK:    -DPICO_BOARD=pico_w  (auto-defines BOARD_PICO_W)

#if defined(BOARD_PICO_W) || defined(PICO_BOARD)
    #define PIN_EPD_CLK   10    // GP10 SPI1
    #define PIN_BTN_UP     2    // GP2
    // ...
#elif defined(BOARD_ESP32S3)
    #define PIN_EPD_CLK   12    // GPIO12 FSPI
    #define PIN_BTN_UP     4    // GPIO4
    // ...
#else  // Desktop
    #define PIN_EPD_CLK    0    // dummy
    // ...
#endif
```

Game engine code uses `PIN_EPD_CLK`, `PIN_BTN_UP`, etc. without knowing which board is active.

### 4.2 Runtime Board Selection (DevTool)

The DevTool GUI stores the selected board in `DilderDevTool._target_board` (a `tk.StringVar`). When you change the dropdown:

1. `_on_board_changed()` fires
2. Updates `self._target_board` to `"pico_w"` or `"esp32s3"`
3. Calls `pin_tab.refresh_for_board(board)` — swaps the pinout display
4. Calls `flash_tab.refresh_for_board(board)` — switches between BOOTSEL/UF2 and esptool/.bin
5. Serial detection uses `find_serial_for_board(board)` which routes to `find_pico_serial()` or `find_esp32_serial()`

The `ProgramsTab` reads `self.app.target_board` to determine flash size and which serial port to stream frames to.

### 4.3 Pin Mapping Comparison

| Signal | Pico W (RP2040) | ESP32-S3 (Olimex) |
|--------|----------------|--------------------|
| **e-Paper CLK** | GP10 (SPI1 SCK) pin 14 | GPIO12 (FSPI CLK) EXT1-18 |
| **e-Paper DIN** | GP11 (SPI1 TX) pin 15 | GPIO11 (FSPI MOSI) EXT1-17 |
| **e-Paper CS** | GP9 pin 12 | GPIO10 (10k pull-up) EXT1-16 |
| **e-Paper DC** | GP8 pin 11 | GPIO9 EXT1-15 |
| **e-Paper RST** | GP12 pin 16 | GPIO3 EXT1-13 |
| **e-Paper BUSY** | GP13 pin 17 | GPIO8 EXT1-12 |
| **Joystick UP** | GP2 pin 4 | GPIO4 EXT1-4 |
| **Joystick DOWN** | GP3 pin 5 | GPIO7 EXT1-7 |
| **Joystick LEFT** | GP4 pin 6 | GPIO1 EXT2-4 |
| **Joystick RIGHT** | GP5 pin 7 | GPIO2 EXT2-5 |
| **Joystick CENTER** | GP6 pin 9 | GPIO15 EXT1-8 |
| **LED** | — | GPIO38 (active LOW) |
| **Battery ADC** | — | GPIO6 (divider x4.133) |
| **USB Power** | — | GPIO5 (divider x1.468) |

---

## 5. Prerequisites

**Both boards:**

- [ ] **Waveshare 2.13" e-Paper HAT V3**
- [ ] **5-way joystick module** (DollaTek or similar)
- [ ] **Python 3.9+** on your system
- [ ] **pip** available (`python3 -m pip --version`)

### Pico W

- [ ] **Raspberry Pi Pico W** board (with micro-USB data cable)
- [ ] No extra wiring — the Waveshare HAT plugs directly onto the Pico W headers

### ESP32-S3 (Olimex)

- [ ] **Olimex ESP32-S3-DevKit-Lipo** board (with USB-C data cable)
- [ ] **Breadboard + jumper wires** (see `setup wiring guide.md` for wiring details)

---

## 6. Step 1 — Install Toolchain

### Pico W

**Automated (recommended):**

```bash
python3 setup.py --board pico --step 2
```

Steps 2-4 install the ARM GCC cross-compiler, clone the Pico SDK, and set `PICO_SDK_PATH`.

**Manual:**

```bash
# Arch / CachyOS
sudo pacman -S arm-none-eabi-gcc arm-none-eabi-newlib cmake ninja

# Debian / Ubuntu
sudo apt install gcc-arm-none-eabi libnewlib-arm-none-eabi cmake ninja-build

# Clone the Pico SDK
git clone --depth 1 https://github.com/raspberrypi/pico-sdk.git ~/pico/pico-sdk
cd ~/pico/pico-sdk && git submodule update --init

# Set the SDK path (add to ~/.zshrc or ~/.bashrc)
export PICO_SDK_PATH="$HOME/pico/pico-sdk"
```

### ESP32-S3 (Olimex)

**Automated (recommended):**

```bash
python3 setup.py --board esp32 --step 16
```

This walks you through everything interactively — installs PlatformIO, esptool, checks the CH340X driver, and pre-downloads the ESP32-S3 platform (~500 MB first time).

**Manual (Arch / CachyOS — uses pipx due to PEP 668):**

```bash
# Install pipx if you don't have it
sudo pacman -S python-pipx

# Install PlatformIO CLI
pipx install platformio
pio --version

# Install esptool (for direct flashing from DevTool)
pipx install esptool
esptool.py version
```

**Manual (Debian / Ubuntu / Fedora — uses pip):**

```bash
# Install PlatformIO CLI
pip install --user platformio
pio --version

# Install esptool
pip install --user esptool
esptool.py version

# If pio/esptool not found, add ~/.local/bin to PATH:
export PATH="$HOME/.local/bin:$PATH"
```

**Both — pre-download the ESP32-S3 platform:**

```bash
# Triggers ~500 MB download on first run (Xtensa compiler, ESP-IDF, Arduino core)
cd "ESP Protyping/dilder-esp32"
pio run
```

> **Note:** PlatformIO includes its own bundled esptool, so the standalone install is only needed if you flash from DevTool directly.

---

## 7. Step 2 — Verify USB Serial Driver

### Pico W

The Pico W uses the RP2040's native USB which shows up as `/dev/ttyACM*`. No extra driver needed — the `cdc_acm` module is built into the kernel.

**Plug in the Pico W via USB**, then:

```bash
# Check the device exists
ls -la /dev/ttyACM*
# Should show: /dev/ttyACM0

# If "Permission denied":
sudo usermod -aG uucp $USER    # Arch/CachyOS
sudo usermod -aG dialout $USER  # Debian/Ubuntu
# Then log out and back in
```

### ESP32-S3 (Olimex)

The Olimex board uses a **CH340X** USB-to-serial chip. The `ch341` kernel module is built into most modern Linux kernels (including CachyOS).

**Plug in the board via the USB-UART port** (the one near the RST/BOOT buttons), then:

```bash
# Check kernel detected it
dmesg | tail -10
# Should show: "ch341-uart converter now attached to ttyUSB0"

# Verify the device exists
ls -la /dev/ttyUSB*
# Should show: /dev/ttyUSB0

# If "Permission denied":
sudo usermod -aG uucp $USER    # Arch/CachyOS
sudo usermod -aG dialout $USER  # Debian/Ubuntu
# Then log out and back in
```

**Which USB port to use on the Olimex board:**

| Port | Location | Chip | Use for |
|------|----------|------|---------|
| **USB-UART** | Near the buttons | CH340X | Uploading firmware, serial monitor |
| **USB-OTG** | Near the antenna | Native | JTAG debugging (advanced) |

For all normal development, use **USB-UART**. It has auto-reset so PlatformIO and esptool can flash without pressing any buttons.

---

## 8. Step 3 — Wire the Board

### Pico W

No breadboard wiring needed. The Waveshare 2.13" e-Paper HAT plugs directly onto the Pico W's 40-pin header:

1. **Unplug** the Pico W from USB.
2. Align pin 1 on both boards (top-left when USB faces you).
3. Press the HAT down firmly until fully seated — no pins visible between boards.

The HAT routes these signals through its PCB:

| Signal | Pico W Pin | GPIO |
|--------|-----------|------|
| VCC | Pin 36 | 3V3(OUT) |
| GND | Pin 38 | GND |
| DIN | Pin 15 | GP11 (SPI1 TX) |
| CLK | Pin 14 | GP10 (SPI1 SCK) |
| CS | Pin 12 | GP9 |
| DC | Pin 11 | GP8 |
| RST | Pin 16 | GP12 |
| BUSY | Pin 17 | GP13 |

The joystick wires to the Pico W breadboard (if using external joystick):

| Joystick Pin | Pico W GPIO | Pin |
|-------------|-------------|-----|
| COM / GND | GND | Pin 38 |
| UP | GP2 | Pin 4 |
| DOWN | GP3 | Pin 5 |
| LEFT | GP4 | Pin 6 |
| RIGHT | GP5 | Pin 7 |
| CENTER | GP6 | Pin 9 |

### ESP32-S3 (Olimex)

Follow the wiring instructions in **`setup wiring guide.md`** Section 5. Here's the quick reference:

**e-Paper Display (female-to-male jumpers):**

| HAT Pin | Wire to | ESP32 GPIO | Board Pin |
|---------|---------|-----------|-----------|
| VCC | 3.3V rail | — | EXT1-1 |
| GND | GND rail | — | EXT1-22 |
| DIN | GPIO11 | EXT1-17 |
| CLK | GPIO12 | EXT1-18 |
| CS | GPIO10 | EXT1-16 |
| DC | GPIO9 | EXT1-15 |
| RST | GPIO3 | EXT1-13 |
| BUSY | GPIO8 | EXT1-12 |

**Joystick (male-to-male jumpers):**

| Joystick Pin | Wire to | ESP32 GPIO | Board Pin |
|-------------|---------|-----------|-----------|
| COM / GND | GND rail | — | — |
| UP | GPIO4 | EXT1-4 |
| DOWN | GPIO7 | EXT1-7 |
| LEFT | GPIO1 | EXT2-4 |
| RIGHT | GPIO2 | EXT2-5 |
| CENTER | GPIO15 | EXT1-8 |

---

## 9. Step 4 — Build & Flash from Terminal

### Pico W

```bash
cd dev-setup/hello-world-serial

# Configure (first time only)
mkdir -p build && cd build
cmake -G Ninja -DPICO_SDK_PATH=$PICO_SDK_PATH -DPICO_BOARD=pico_w ..

# Build
ninja

# Flash: hold BOOTSEL on the Pico, plug USB, release — it mounts as RPI-RP2
cp hello_serial.uf2 /run/media/$USER/RPI-RP2/

# Serial monitor (115200 baud)
screen /dev/ttyACM0 115200
```

**Expected serial output after flash:**

```
Hello, Dilder!
Heartbeat: 1
Heartbeat: 2
...
```

The onboard LED blinks once per second.

### ESP32-S3 (Olimex)

```bash
cd "ESP Protyping/dilder-esp32"

# Build only
pio run

# Build + flash (auto-detects /dev/ttyUSB0)
pio run -t upload

# Open serial monitor (115200 baud)
pio device monitor
```

**Expected serial output after flash:**

```
=== Dilder ESP32-S3 Firmware ===
Board: ESP32-S3 (Olimex)
Flash: 8192 KB
PSRAM: 8388608 bytes
Setup complete. Entering main loop.
Joystick: UP/DOWN/LEFT/RIGHT/CENTER
```

**Expected display output:**

The e-Paper display should show:

```
DILDER
ESP32-S3 Olimex DevKit-Lipo
─────────────────────────────
PSRAM: 8192 KB
Battery: 4.12V
USB: connected
Press joystick to test...
```

The green LED on the board blinks once after the startup screen draws.

**Test the joystick:**

Press each direction — the green LED flashes and the serial monitor prints the direction. Press CENTER to show the chip info screen on the display.

---

## 10. Step 5 — Build & Flash from DevTool

```bash
python3 DevTool/devtool.py
```

Both boards use the same DevTool GUI. The **"Target Board"** dropdown at the top of the window controls which board you're working with. All tabs (GPIO Pins, Flash Firmware, Programs) adapt to the selected board.

### Pico W

1. **Select the board:** Use the **"Target Board"** dropdown — make sure **"Pico W (RP2040)"** is selected (this is the default).

2. **Check detection:** The status next to the dropdown should show `Serial: /dev/ttyACM0` in green. If it shows "Not detected", plug in the USB cable.

3. **View the pinout:** Click the **"GPIO Pins"** tab — shows the Pico W pinout with Dilder-assigned pins marked.

4. **Flash the firmware:** Go to the **"Flash Firmware"** tab. Put the Pico W in BOOTSEL mode, then click **"Flash UF2"** to copy the firmware.

5. **Deploy a program:** Go to the **"Programs"** tab. Select any octopus program. Flash size shows "Pico W (RP2040) flash: 2048 KB". Click **"Deploy to Board"** to stream frames.

### ESP32-S3 (Olimex)

1. **Select the board:** Use the **"Target Board"** dropdown. Change it from "Pico W (RP2040)" to **"ESP32-S3 (Olimex)"**.

2. **Check detection:** The status next to the dropdown should show `Serial: /dev/ttyUSB0` in green. If it shows "Not detected", plug in the USB-UART cable.

3. **View the pinout:** Click the **"GPIO Pins"** tab — it now shows the full Olimex ESP32-S3 pinout with all Dilder-assigned pins marked.

4. **Build the firmware:** Go to the **"Flash Firmware"** tab. Click **"Build ESP32 (PlatformIO)"**. Watch the log panel at the bottom for build progress.

5. **Flash the firmware:** After the build completes, click **"Detect ESP32"** to confirm the port, then click **"Flash"** to upload.

6. **Deploy a program:** Go to the **"Programs"** tab. Select any octopus program. The flash size display now shows "ESP32-S3 (Olimex) flash: 8192 KB" instead of the Pico's 2048 KB. Click **"Deploy to Board"** to stream frames, or **"Deploy Standalone"** to build a self-contained firmware.

---

## 11. Step 6 — Verify Everything Works

### Pico W

- [ ] Serial monitor shows `Hello, Dilder!` and heartbeat counter
- [ ] Onboard LED blinks once per second
- [ ] Display shows text after flashing the display hello world (Steps 10-14 in setup.py)
- [ ] Joystick directions print to serial (if joystick wired)
- [ ] Switching to "ESP32-S3 (Olimex)" in DevTool still works

### ESP32-S3 (Olimex)

- [ ] Serial monitor shows `=== Dilder ESP32-S3 Firmware ===`
- [ ] PSRAM reports 8388608 bytes (8 MB)
- [ ] Display shows the startup screen with board info
- [ ] Battery voltage reads a sane value (3.3-4.2V if on USB, 0V if no battery)
- [ ] USB power shows "connected" when on USB
- [ ] Each joystick direction prints to serial and blinks the green LED
- [ ] CENTER button shows the chip info screen on the display
- [ ] Switching back to "Pico W" in DevTool still works for Pico builds

---

## 12. The Automated Way — setup.py

The setup CLI supports board-specific walkthrough via the `--board` flag:

```bash
# Full setup for a specific board
python3 setup.py --board pico       # Pico W only (steps 1-15)
python3 setup.py --board esp32      # ESP32-S3 only (steps 1, 5-6, 15-16)

# Or run everything
python3 setup.py                    # all steps for both boards

# Jump to a specific step
python3 setup.py --step 16          # ESP32-S3 toolchain step directly

# List available steps (filtered by board)
python3 setup.py --board esp32 --list

# Check overall status
python3 setup.py --status
```

### Pico W steps (1-15)

Steps 2-4 install the ARM GCC cross-compiler, clone the Pico SDK, and set the environment variable. Steps 7-14 build, flash, and verify the hello world programs (serial and display).

### ESP32-S3 step (16)

1. Checks pip is available
2. Installs PlatformIO CLI (`pip install --user platformio`)
3. Installs esptool (`pip install --user esptool`)
4. Verifies the CH340X kernel module exists
5. Checks serial group membership (`uucp` or `dialout`)
6. Verifies the PlatformIO project at `ESP Protyping/dilder-esp32/` has `platformio.ini` and `src/main.cpp`
7. Optionally pre-downloads the ESP32-S3 platform + libraries and does a test build

**Status output (after setup):**

```
  ESP32-S3 Toolchain
  ──────────────────────────────────────────────────
  ✓ PlatformIO: PlatformIO Core, version 6.x.x
  ✓ esptool: /home/user/.local/bin/esptool.py
  ✓ ESP32 project: .../ESP Protyping/dilder-esp32
  ✓ ESP32 firmware.bin: 245 KB

  Hardware
  ──────────────────────────────────────────────────
  ✓ Pico W detected on /dev/ttyACM0
  ✓ ESP32-S3 (CH340X) candidate: /dev/ttyUSB0
```

---

## 13. Troubleshooting

### Both Boards

#### Serial port permission denied (`/dev/ttyACM0` or `/dev/ttyUSB0`)

```bash
# CachyOS / Arch
sudo usermod -aG uucp $USER

# Debian / Ubuntu
sudo usermod -aG dialout $USER

# Then log out and back in (or reboot)
```

#### Display doesn't show anything

**Pico W:** Make sure the HAT is fully seated — no pins exposed between boards. Check FPC ribbon cable is not pinched.

**ESP32-S3:** Double-check all 8 wires (VCC, GND, DIN, CLK, CS, DC, RST, BUSY). Make sure VCC goes to **3.3V** (EXT1-1), NOT 5V. Verify wiring matches the pin table in Section 8. Check serial monitor — `GxEPD2` prints SPI diagnostics during `display.init()`.

### Pico W

#### CMake can't find Pico SDK

```bash
# Make sure PICO_SDK_PATH is set
echo $PICO_SDK_PATH
# Should show ~/pico/pico-sdk or wherever you cloned it

# If empty, set it:
export PICO_SDK_PATH="$HOME/pico/pico-sdk"
# Add to ~/.zshrc or ~/.bashrc to persist
```

#### Pico W doesn't mount as RPI-RP2

1. Hold **BOOTSEL** before plugging in USB
2. Keep holding BOOTSEL while plugging in
3. Release BOOTSEL — it should mount as a USB drive
4. Check `lsblk` or `dmesg | tail` for the device

#### DevTool doesn't detect the Pico W

The DevTool looks for the Raspberry Pi USB Vendor ID (`0x2E8A`). If detection fails:

1. Unplug and re-plug the USB cable
2. Check `ls /dev/ttyACM*`
3. Make sure no other serial monitor is open (only one process can hold the port)

### ESP32-S3 (Olimex)

#### PlatformIO not found after install

```bash
# pip/pipx installed to ~/.local/bin which isn't in PATH
export PATH="$HOME/.local/bin:$PATH"
# Add to ~/.zshrc or ~/.bashrc to persist
```

#### `pip install` fails with "externally-managed-environment" (Arch/CachyOS)

Arch-based distros block `pip install --user` (PEP 668). Use `pipx` instead:

```bash
sudo pacman -S python-pipx
pipx install platformio
pipx install esptool
```

The setup CLI (`python3 setup.py --step 16`) handles this automatically.

#### Build fails: "No such file or directory: board_config.h"

The `platformio.ini` uses `build_src_filter` to include the shared firmware source. The include path for shared headers is set via `build_src_extra`. If this fails, add an explicit include path:

```ini
; In platformio.ini, under build_flags:
build_flags =
    -DBOARD_ESP32S3
    -I../../firmware/include
```

#### esptool can't connect / times out

If auto-reset isn't working:

1. Hold the **BOOT** button on the board
2. Press and release **RST** while still holding BOOT
3. Release **BOOT**
4. Run the flash command within 5 seconds

#### PSRAM shows 0 bytes

Verify `platformio.ini` has both of these:

```ini
board_build.psram = enabled
board_build.arduino.memory_type = qio_opi
```

The `qio_opi` memory type is required for the N8R8 module's octal PSRAM.

#### DevTool doesn't detect the ESP32

The DevTool looks for the CH340X chip by USB Vendor ID (`0x1A86`). If detection fails:

1. Unplug and re-plug the USB-UART cable
2. Check `dmesg | tail` for the device name
3. The fallback detection matches any `/dev/ttyUSB*` device

---

## 14. File Reference

Quick lookup for every file involved in the ESP32-S3 support:

| File | Purpose |
|------|---------|
| `ESP Protyping/dilder-esp32/platformio.ini` | PlatformIO build config — board, framework, libraries, flags |
| `ESP Protyping/dilder-esp32/src/main.cpp` | ESP32 firmware entry point — display test, joystick, chip info |
| `firmware/include/platform/board_config.h` | Compile-time pin definitions for Pico W, ESP32-S3, Desktop |
| `firmware/include/platform/hal.h` | Hardware abstraction interface (SPI, buttons, LED, battery, timing) |
| `firmware/src/platform/esp32s3/esp32s3_hal.c` | ESP32-S3 HAL implementation using Arduino framework |
| `firmware/CMakeLists.txt` | Updated with `TARGET_BOARD` variable for board selection |
| `DevTool/devtool.py` | Board selector, ESP32 serial detection, esptool flash, pin viewer |
| `setup.py` | Step 16 — PlatformIO + esptool + ESP-IDF toolchain installation |
| `ESP Protyping/setup wiring guide.md` | Physical wiring reference (breadboard, pinout, connectors) |
| `ESP Protyping/dev setup guide.md` | This file |
