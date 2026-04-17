# Pico W & Display — First-Time Setup

A complete, step-by-step walkthrough for setting up the Raspberry Pi Pico W development environment, verifying it with a serial-only hello world, physically connecting the Waveshare 2.13" e-Paper display, and building a hello world that draws to the screen.

!!! info "This project runs entirely in C"
    No MicroPython, no CircuitPython. C gives us direct hardware control, deterministic timing, and the full performance of the RP2040's dual Cortex-M0+ cores. Every byte of flash and every CPU cycle counts on a microcontroller with 2 MB of storage and 264 KB of RAM.

**Target audience:** Someone with the hardware in hand and zero prior embedded development experience.

**Platform:** Linux (Arch/CachyOS — Debian/Ubuntu alternatives noted where they differ).

---

## Automated Setup Script

!!! tip "Recommended: Use the interactive setup script"
    Before following the manual steps below, try the automated setup script. It walks you through the entire process with explanations, automates installs and builds, and lets you skip/quit/resume at any point.

```bash
python3 setup.py              # interactive board selection menu (Pico W / ESP32-S3 / Both)
python3 setup.py --board pico # run setup for Pico W only
python3 setup.py --board esp32 # run setup for ESP32-S3 only
python3 setup.py --status     # see what's installed and what's missing
python3 setup.py --list       # list all 16 steps
python3 setup.py --step 7     # jump to a specific step
python3 setup.py --test-setup # install testing dependencies
```

![Setup CLI step list](../../assets/images/setup-cli/setup_cli_list_rendered.png)

The script handles 16 steps across three checkpoints:

| Step | Name | Board | Description |
|------|------|-------|-------------|
| 1 | Check Prerequisites | [Both] | Detects distro, verifies git/cmake/Python/Tkinter/pyserial |
| 2 | Install ARM Toolchain | [Pico W] | Runs the correct package manager command |
| 3 | Clone Pico SDK | [Pico W] | Clones `pico-sdk` with submodules |
| 4 | Set PICO_SDK_PATH | [Pico W] | Adds export to your shell profile |
| 5 | Serial Port Permissions | [Both] | Adds user to `uucp` (Arch) or `dialout` (Debian) |
| 6 | Install VSCode Extensions | [Both] | Installs C/C++ (or clangd for Code OSS), CMake Tools, Cortex-Debug |
| 7 | Build Hello Serial | [Pico W] | CMake + Ninja build of serial-only test |
| 8 | Flash Hello Serial | [Pico W] | Guides BOOTSEL, auto-detects mount, copies UF2 |
| 9 | Verify Serial Output | [Pico W] | Confirms serial and LED work (Checkpoint 1) |
| 10 | Connect the Display | [Pico W] | Guides HAT-on-header assembly |
| 11 | Get Waveshare Library | [Pico W] | Clones and copies C driver files |
| 12 | Build Hello Display | [Pico W] | Builds the e-ink display test |
| 13 | Flash Hello Display | [Pico W] | Flash display firmware |
| 14 | Verify Display Output | [Pico W] | Confirms text on display (Checkpoint 2) |
| 15 | Docker Build Toolchain | [Both] | Installs Docker and pre-builds the ARM container (Checkpoint 3) |
| 16 | ESP32-S3 Toolchain (PlatformIO) | [ESP32-S3] | Set up PlatformIO and ESP-IDF for the Olimex ESP32-S3 |

Use `--status` to check your current environment at a glance:

![Setup CLI status dashboard](../../assets/images/setup-cli/setup_cli_status_rendered.png)

---

## Table of Contents (Manual Guide)

1. [What You Need](#1-what-you-need)
2. [Understanding the Hardware](#2-understanding-the-hardware)
3. [Install the Pico C/C++ SDK Toolchain](#3-install-the-pico-cc-sdk-toolchain)
4. [Set Up the Docker Build Environment (Optional)](#4-set-up-the-docker-build-environment-optional)
5. [Configure VSCode for Pico Development](#5-configure-vscode-for-pico-development)
6. [Checkpoint 1 — Hello World Serial (No Wiring Needed)](#6-checkpoint-1-hello-world-serial-no-wiring-needed)
7. [Connect the Display to the Pico W](#7-connect-the-display-to-the-pico-w)
8. [Checkpoint 2 — Hello World e-Ink Display](#8-checkpoint-2-hello-world-e-ink-display)
9. [Debugging](#9-debugging)
10. [Troubleshooting](#10-troubleshooting)
11. [Next Steps](#11-next-steps)

---

## 1. What You Need

### Hardware

| Item | Notes |
|------|-------|
| Raspberry Pi Pico W | **With male headers soldered on** |
| Waveshare Pico-ePaper-2.13 | SSD1680 driver, Pico-native module — plugs directly onto Pico W |
| Micro-USB data cable | **Must be a data cable, not charge-only** — this is the #1 gotcha |
| Linux PC | Arch/CachyOS, Ubuntu, Debian, or Fedora |

![Pico W and e-Paper display — the two components you need](../../assets/images/hardware/pico-w-and-display-separated.jpg)

!!! tip "No breadboard or jumper wires needed"
    The Waveshare HAT has a female header socket that slides directly onto the Pico W's male header pins. No breadboard, no jumper wires — just push it on.

### Software (installed in this guide)

| Tool | Purpose |
|------|---------|
| `arm-none-eabi-gcc` | ARM cross-compiler for the RP2040 |
| `cmake` + `ninja` | Build system used by the Pico SDK |
| `pico-sdk` | Official Raspberry Pi Pico C/C++ SDK |
| `picotool` | CLI utility for flashing and inspecting Pico boards |
| VSCode | Editor and IDE |
| CMake Tools extension | CMake integration for VSCode |
| Serial Monitor extension | View USB serial output from the Pico W |
| Cortex-Debug extension | On-chip debugging via SWD (optional) |

---

## 2. Understanding the Hardware

### The Pico W at a Glance

![Raspberry Pi Pico W — top view](../../assets/images/hardware/pico-w-board.jpg)

- **Chip:** RP2040 — dual-core ARM Cortex-M0+ at 133 MHz
- **RAM:** 264 KB SRAM
- **Flash:** 2 MB onboard QSPI
- **GPIO:** 26 multi-function pins (3.3V logic — **NOT 5V tolerant**)
- **USB:** Micro-USB 1.1 — used for flashing and serial output
- **Wi-Fi:** 802.11n 2.4 GHz (Infineon CYW43439)

### The Waveshare 2.13" e-Paper V3 at a Glance

![Waveshare e-Paper HAT — back side showing pin labels and SPI connections](../../assets/images/hardware/waveshare-hat-back.jpg)

- **Resolution:** 250 x 122 pixels, black and white
- **Driver IC:** SSD1680
- **Interface:** SPI (4-wire, Mode 0)
- **Refresh:** Full refresh ~2 sec, partial ~0.3 sec
- **Minimum refresh interval:** 180 seconds between operations
- **Standby current:** < 0.01 uA (practically zero)

### How They Talk to Each Other

The display communicates over **SPI** (Serial Peripheral Interface). The Pico W has two SPI controllers (SPI0 and SPI1). We use **SPI1** for the display, leaving SPI0 free for future peripherals.

The display needs 8 connections total: power (VCC + GND), four SPI signals (MOSI, CLK, CS, DC), a reset line, and a busy flag.

### Why C Instead of MicroPython

| | C (Pico SDK) | MicroPython |
|---|---|---|
| **Speed** | Native machine code, 133 MHz both cores | Interpreted, ~100x slower for compute |
| **Flash usage** | Your code only | ~700 KB for the interpreter alone |
| **RAM** | Full 264 KB available | ~180 KB after interpreter overhead |
| **Timing** | Deterministic, microsecond precision | GC pauses, non-deterministic |
| **Debugging** | SWD breakpoints, printf, full GDB | REPL print statements only |
| **Libraries** | Pico SDK, direct register access | Limited to what's been ported |

For a real-time pet with animations, input handling, and tight display refresh timing, C is the right choice.

---

## 3. Install the Pico C/C++ SDK Toolchain

!!! tip "The setup script automates all of this"
    Steps 1-6 of `python3 setup.py` handle the entire toolchain installation automatically with distro detection. Here's what the prerequisite check looks like:

    ![Step 1 — Prerequisites check](../../assets/images/setup-cli/setup_cli_step_01.png)

### Step 3.1 — Install System Dependencies

=== "Arch / CachyOS"

    ```bash
    sudo pacman -S --needed \
        arm-none-eabi-gcc \
        arm-none-eabi-newlib \
        cmake \
        ninja \
        python \
        git \
        base-devel
    ```

=== "Ubuntu / Debian"

    ```bash
    sudo apt update && sudo apt install -y \
        gcc-arm-none-eabi \
        libnewlib-arm-none-eabi \
        cmake \
        ninja-build \
        python3 \
        git \
        build-essential \
        libstdc++-arm-none-eabi-newlib
    ```

=== "Fedora"

    ```bash
    sudo dnf install -y \
        arm-none-eabi-gcc-cs \
        arm-none-eabi-newlib \
        cmake \
        ninja-build \
        python3 \
        git
    ```

### Step 3.2 — Verify the Cross-Compiler

```bash
arm-none-eabi-gcc --version
```

You should see output like:

```
arm-none-eabi-gcc (GCC) 14.x.x
...
```

If this fails, the toolchain is not installed correctly. Do not proceed until this works.

### Step 3.3 — Clone the Pico SDK

```bash
# Create a workspace for Pico development
mkdir -p ~/pico && cd ~/pico

# Clone the SDK
git clone --recurse-submodules https://github.com/raspberrypi/pico-sdk.git

# Verify it downloaded
ls pico-sdk/
```

You should see directories like `src/`, `lib/`, `cmake/`, etc.

### Step 3.4 — Set the SDK Environment Variable

Add this to your shell profile:

```bash
# For zsh (~/.zshrc)
echo 'export PICO_SDK_PATH="$HOME/pico/pico-sdk"' >> ~/.zshrc
source ~/.zshrc

# For bash (~/.bashrc)
echo 'export PICO_SDK_PATH="$HOME/pico/pico-sdk"' >> ~/.bashrc
source ~/.bashrc
```

Verify:

```bash
echo $PICO_SDK_PATH
# Should print: /home/<your-username>/pico/pico-sdk
```

### Step 3.5 — Install picotool (Optional but Recommended)

=== "Arch / CachyOS"

    ```bash
    yay -S picotool
    ```

=== "Build from Source (any distro)"

    ```bash
    cd ~/pico
    git clone https://github.com/raspberrypi/picotool.git
    cd picotool && mkdir build && cd build
    cmake .. && make -j$(nproc)
    sudo make install
    ```

### Step 3.6 — Serial Port Permissions

The group name depends on your distro:

=== "Arch / CachyOS"

    ```bash
    sudo usermod -aG uucp $USER
    ```

=== "Ubuntu / Debian"

    ```bash
    sudo usermod -aG dialout $USER
    ```

!!! warning "Log out required"
    You **must log out and back in** (or reboot) for this to take effect. A new terminal window is not enough.

Verify after logging back in:

```bash
# Arch / CachyOS
groups | grep uucp

# Ubuntu / Debian
groups | grep dialout
```

---

## 4. Set Up the Docker Build Environment (Optional)

!!! tip "The setup script automates Docker installation"
    Step 15 of `python3 setup.py` handles Docker install, daemon setup, group permissions, and image pre-build:

    ![Step 15 — Docker Build Toolchain](../../assets/images/setup-cli/setup_cli_step_15.png)

If you prefer a containerized build environment for reproducibility, use the provided Docker setup in `dev-setup/`.

=== "Arch / CachyOS"

    ```bash
    sudo pacman -S docker docker-compose
    sudo systemctl enable --now docker
    sudo usermod -aG docker $USER
    ```

=== "Ubuntu / Debian"

    ```bash
    sudo apt install docker.io docker-compose-v2
    sudo systemctl enable --now docker
    sudo usermod -aG docker $USER
    ```

Then build:

```bash
cd dev-setup/
docker compose build
docker compose run --rm build
```

---

## 5. Configure VSCode for Pico Development

### Step 5.1 — Install VSCode

=== "Arch / CachyOS"

    ```bash
    sudo pacman -S code
    ```

=== "Ubuntu / Debian"

    ```bash
    sudo apt install code
    ```

### Step 5.2 — Install Required Extensions

```bash
code --install-extension ms-vscode.cpptools
code --install-extension ms-vscode.cmake-tools
code --install-extension twxs.cmake
code --install-extension ms-vscode.vscode-serial-monitor
code --install-extension marus25.cortex-debug
```

| Extension | Purpose |
|-----------|---------|
| **C/C++** | IntelliSense, syntax highlighting, debugging |
| **CMake Tools** | CMake project management, build, configure |
| **CMake** | CMake syntax highlighting |
| **Serial Monitor** | View serial output from the Pico W |
| **Cortex-Debug** | ARM Cortex debugging via SWD (optional) |

### Step 5.3 — Configure CMake Tools

Create `.vscode/settings.json`:

```json
{
    "cmake.generator": "Ninja",
    "cmake.configureSettings": {
        "PICO_SDK_PATH": "${env:PICO_SDK_PATH}",
        "PICO_BOARD": "pico_w"
    },
    "cmake.sourceDirectory": "${workspaceFolder}/dev-setup/hello-world-serial",
    "cmake.buildDirectory": "${workspaceFolder}/dev-setup/hello-world-serial/build",
    "C_Cpp.default.configurationProvider": "ms-vscode.cmake-tools",
    "files.associations": { "*.h": "c", "*.c": "c" }
}
```

Create `.vscode/cmake-kits.json`:

```json
[
    {
        "name": "Pico W ARM GCC",
        "compilers": {
            "C": "/usr/bin/arm-none-eabi-gcc",
            "CXX": "/usr/bin/arm-none-eabi-g++"
        },
        "isTrusted": true
    }
]
```

Create `.vscode/c_cpp_properties.json`:

```json
{
    "configurations": [
        {
            "name": "Pico W",
            "includePath": [
                "${workspaceFolder}/dev-setup/**",
                "${env:PICO_SDK_PATH}/src/**"
            ],
            "defines": ["PICO_BOARD=pico_w", "LIB_PICO_STDIO_USB"],
            "compilerPath": "/usr/bin/arm-none-eabi-gcc",
            "cStandard": "c11",
            "intelliSenseMode": "gcc-arm"
        }
    ],
    "version": 4
}
```

Select the build kit: `Ctrl+Shift+P` > **"CMake: Select a Kit"** > **"Pico W ARM GCC"**

---

## 6. Checkpoint 1 — Hello World Serial (No Wiring Needed)

**Goal:** Verify the entire toolchain before touching the display. Just the Pico W plugged into USB.

!!! tip "The setup script handles build + flash + verify"
    Steps 7-9 of `python3 setup.py` automate the build, flash (with BOOTSEL detection), and serial verification:

    ![Step 7 — Build Hello Serial](../../assets/images/setup-cli/setup_cli_step_07.png)

### Build

```bash
cp $PICO_SDK_PATH/external/pico_sdk_import.cmake \
   dev-setup/hello-world-serial/

cd dev-setup/hello-world-serial
mkdir -p build && cd build
cmake -G Ninja -DPICO_SDK_PATH=$PICO_SDK_PATH -DPICO_BOARD=pico_w ..
ninja
```

### Flash

1. **Unplug** the Pico W.
2. **Hold BOOTSEL**, plug in USB, release after 1 second.
3. Copy: `cp build/hello_serial.uf2 /run/media/$USER/RPI-RP2/`

### Verify

Open serial monitor: `Ctrl+Shift+P` > "Serial Monitor" > port `/dev/ttyACM0` > baud `115200`

```
=========================
  Hello, Dilder!
  Pico W is alive.
=========================

Heartbeat #1  |  LED: ON
Heartbeat #2  |  LED: OFF
...
```

The onboard LED should blink every second. If this works, your entire toolchain is verified.

---

## 7. Connect the Display to the Pico W

!!! tip "The setup script shows detailed connection instructions"
    Step 10 of `python3 setup.py` provides a guided walkthrough with ASCII diagrams:

    ![Step 10 — Connect the Display](../../assets/images/setup-cli/setup_cli_step_10.png)

!!! danger "Power off before connecting"
    Disconnect the Pico W from USB before attaching the display. Voltage spikes can damage the e-ink panel.

### Direct Header Connection

The Pico W has **male header pins soldered on**. The Waveshare HAT has a **female header socket** on its underside. The display slides directly onto the Pico W's headers — no breadboard or jumper wires required.

### Step 7.1 — Align the Headers

1. Hold the Pico W with the **USB port facing you**.
2. Hold the Waveshare HAT with its **display face up** and the 40-pin socket facing down.
3. Align **pin 1** on both boards. Pin 1 on the Pico W is the top-left pin (GP0) when the USB port faces you. The HAT's socket has a corresponding pin 1 marking.
4. The HAT's header socket covers pins 1-40 of the Pico W.

### Step 7.2 — Seat the Display

1. Line up all pins carefully — **do not force it at an angle**.
2. Press down firmly and evenly until the HAT is fully seated on the Pico W headers.
3. The HAT should sit snug with no pins visible between the boards.

![Pico W mounted on the Waveshare HAT — side view showing header connection](../../assets/images/hardware/pico-mounted-on-hat-side.jpg)

![Pico W mounted on the Waveshare HAT — top view](../../assets/images/hardware/pico-mounted-on-hat-top.jpg)

![Assembled unit — back view showing pin headers](../../assets/images/hardware/assembled-back-view.jpg)

### Step 7.3 — Verify the Connection

Before plugging in USB, check:

- [ ] **The HAT is fully seated** — no pins are exposed between the boards.
- [ ] **Pin 1 alignment is correct** — the HAT is not offset or rotated.
- [ ] **The display's FPC ribbon cable is not pinched** between the boards.
- [ ] **Nothing is shorting** — no stray wires or metal touching the boards.

### Pin Mapping (for reference)

The HAT uses these Pico W pins through the direct header connection:

| e-Paper Signal | Function | Pico W GPIO | Pico W Pin # |
|---|---|---|---|
| VCC | 3.3V power | 3V3(OUT) | 36 |
| GND | Ground | GND | 38 |
| DIN | SPI MOSI | GP11 (SPI1 TX) | 15 |
| CLK | SPI clock | GP10 (SPI1 SCK) | 14 |
| CS | Chip select | GP9 (SPI1 CSn) | 12 |
| DC | Data/Command | GP8 | 11 |
| RST | Reset | GP12 | 16 |
| BUSY | Busy flag | GP13 | 17 |

These are the same pins used in the Waveshare Pico examples. The HAT routes them through its PCB from the 40-pin socket.

---

## 8. Checkpoint 2 — Hello World e-Ink Display

**Goal:** Draw text on the e-ink display using the Waveshare C library.

!!! tip "The setup script automates the library download, build, and flash"
    Steps 11-14 of `python3 setup.py` handle everything:

    ![Step 12 — Build Hello Display](../../assets/images/setup-cli/setup_cli_step_12.png)

### Get the Waveshare C Library

```bash
cd /tmp && git clone https://github.com/waveshare/Pico_ePaper_Code.git
cd ~/CodingProjects/Dilder/dev-setup/hello-world
mkdir -p lib/Config lib/e-Paper lib/GUI lib/Fonts

cp /tmp/Pico_ePaper_Code/c/lib/Config/DEV_Config.{h,c} lib/Config/
cp /tmp/Pico_ePaper_Code/c/lib/Config/Debug.h lib/Config/
cp /tmp/Pico_ePaper_Code/c/lib/e-Paper/EPD_2in13_V3.{h,c} lib/e-Paper/
cp /tmp/Pico_ePaper_Code/c/lib/GUI/GUI_Paint.{h,c} lib/GUI/
cp /tmp/Pico_ePaper_Code/c/lib/Fonts/fonts.h lib/Fonts/
cp /tmp/Pico_ePaper_Code/c/lib/Fonts/font{8,12,16,20,24}.c lib/Fonts/

cp $PICO_SDK_PATH/external/pico_sdk_import.cmake .
rm -rf /tmp/Pico_ePaper_Code
```

### Build

```bash
mkdir -p build && cd build
cmake -G Ninja -DPICO_SDK_PATH=$PICO_SDK_PATH -DPICO_BOARD=pico_w ..
ninja
```

### Flash

1. Unplug, hold BOOTSEL, plug in, release.
2. `cp build/hello_dilder.uf2 /run/media/$USER/RPI-RP2/`

### Verify

**Serial output:**

```
Hello, Dilder!
Initializing e-Paper display...
Display initialized.
Drawing to display...
Display updated. Entering sleep mode.
Heartbeat: 1
```

**The display** should show:

- A **black border** rectangle
- **"Hello, Dilder!"** in 24px font
- **"Pico W + e-Paper V3"** in 16px font
- **"First build successful!"** in 12px font

![Hello, Dilder! running on the e-ink display — proof of life](../../assets/images/hardware/hello-dilder-running.jpg)

If text appears on the display — the full hardware stack is working.

![Sassy Octopus running standalone on the Pico W](../../assets/images/hardware/sassy-octopus-running.jpg)

---

## 9. Debugging

### Printf Debugging (USB Serial)

Add `printf()` anywhere — output appears on the serial monitor at 115200 baud.

```c
printf("Display BUSY pin: %d\n", gpio_get(13));
printf("Buffer size: %d bytes\n", image_size);
```

### Hardware Debugging with SWD (Advanced)

For breakpoint debugging, you need a second Pico as a debug probe. See the [full guide](../../dev-setup/pico-and-display-first-time-setup.md#9-debugging) in `dev-setup/` for SWD wiring and configuration.

---

## 10. Troubleshooting

| Problem | Solution |
|---------|----------|
| `arm-none-eabi-gcc: command not found` | Toolchain not installed — re-run Step 3.1 |
| `PICO_SDK_PATH is not defined` | Set the env var (Step 3.4), restart terminal |
| RPI-RP2 drive doesn't appear | Hold BOOTSEL **before** plugging in. Try a different cable |
| `/dev/ttyACM0` doesn't exist | Wrong cable (charge-only), or firmware crashed |
| Permission denied on serial | Add to serial group: `uucp` on Arch/CachyOS, `dialout` on Ubuntu/Debian, then log out and back in |
| Serial shows nothing | Baud rate must be 115200 |
| Display blank | Check HAT is fully seated on headers, pin 1 aligned |
| Garbage pixels | Wrong driver version — confirm V3 on PCB silkscreen |
| Display flickers then blank | HAT not seated properly — reseat it firmly |
| Old image stuck | E-ink retains last image — flash code that calls `EPD_2in13_V3_Clear()` |

---

## 11. Next Steps

1. **Modify the text** — Change strings in `main.c`, rebuild, flash.
2. **Add button input** — Wire the 5 tactile buttons (see [Wiring & Pinout](../hardware/wiring-pinout.md)).
3. **Draw graphics** — `GUI_Paint` supports lines, rectangles, circles, bitmaps.
4. **Try partial refresh** — `EPD_2in13_V3_Display_Partial()` for fast updates.
5. **Build the firmware scaffold** — Start the Dilder pet logic.
