# Pico W & Waveshare e-Ink Display — First-Time Setup Guide

A complete, step-by-step walkthrough for setting up the Raspberry Pi Pico W development environment, verifying it with a serial-only hello world, physically wiring the Waveshare 2.13" e-Paper display, and building a hello world that draws to the screen.

> **This project runs entirely in C** — no MicroPython, no CircuitPython. C gives us direct hardware control, deterministic timing, and the full performance of the RP2040's dual Cortex-M0+ cores. Every byte of flash and every CPU cycle counts on a microcontroller with 2 MB of storage and 264 KB of RAM.

**Target audience:** Someone with the hardware in hand and zero prior embedded development experience.

**Platform:** Linux (Arch/CachyOS — Debian/Ubuntu alternatives noted where they differ).

---

## Automated Setup Script

Before diving into the manual guide below, you can use the **interactive setup script** that automates the entire process. Run it from the project root:

```bash
python3 setup.py
```

The script walks you through 14 steps with detailed explanations at each stage, automates package installs, SDK cloning, builds, and flashing, and lets you skip, quit, and resume at any point.

### Quick Reference

| Command | What it does |
|---------|-------------|
| `python3 setup.py` | Full interactive walkthrough from Step 1 |
| `python3 setup.py --status` | Show what's installed and what's missing |
| `python3 setup.py --list` | List all 14 steps with descriptions |
| `python3 setup.py --step N` | Jump directly to step N (resume after quitting) |

### What Each Step Does

| Step | Name | Automated? | Description |
|------|------|-----------|-------------|
| 1 | Check Prerequisites | Yes | Detects your Linux distro, verifies git, cmake, Python are installed |
| 2 | Install ARM Toolchain | Yes | Runs the correct `pacman`/`apt`/`dnf` command for your distro to install `arm-none-eabi-gcc`, cmake, ninja |
| 3 | Clone Pico SDK | Yes | Clones the official `pico-sdk` with submodules to `~/pico/pico-sdk` |
| 4 | Set PICO_SDK_PATH | Yes | Appends `export PICO_SDK_PATH=...` to your `.zshrc` or `.bashrc` |
| 5 | Serial Port Permissions | Yes | Adds your user to the correct serial group (`uucp` on Arch/CachyOS, `dialout` on Debian/Ubuntu) |
| 6 | Install VSCode Extensions | Yes | Installs C/C++, CMake Tools, Serial Monitor, and Cortex-Debug extensions |
| 7 | Build Hello Serial | Yes | Copies SDK helper, runs CMake configure + Ninja build for `hello-world-serial` |
| 8 | Flash Hello Serial | Semi | Guides you through BOOTSEL mode, auto-detects the RPI-RP2 mount, copies the `.uf2` |
| 9 | Verify Serial Output | Manual | Shows how to open a serial monitor, what output to expect, confirms Checkpoint 1 |
| 10 | Connect the Display | Manual | Step-by-step instructions for sliding the Waveshare HAT onto the Pico W headers |
| 11 | Get Waveshare Library | Yes | Clones the Waveshare repo, copies the C driver and font files into the project |
| 12 | Build Hello Display | Yes | CMake configure + Ninja build for `hello-world` (the display version) |
| 13 | Flash Hello Display | Semi | Same BOOTSEL flow, auto-detects mount, copies `hello_dilder.uf2` |
| 14 | Verify Display Output | Manual | Shows expected display text, confirms Checkpoint 2, prints completion banner |

### Example Session

```
$ python3 setup.py --status

  Toolchain
  ──────────────────────────────────────────────────
  ✓ ARM GCC: arm-none-eabi-gcc (GCC) 15.2.1
  ✓ CMake: installed
  ✓ Ninja: installed

  Pico SDK
  ──────────────────────────────────────────────────
  ✓ PICO_SDK_PATH: /home/user/pico/pico-sdk
  ✓ SDK directory: /home/user/pico/pico-sdk

  Permissions
  ──────────────────────────────────────────────────
  ✓ User in 'uucp' group

  VSCode
  ──────────────────────────────────────────────────
  ✓ VSCode: installed
  ✓   C/C++
  ✓   CMake Tools
  ✓   Serial Monitor

  Builds
  ──────────────────────────────────────────────────
  ✓ hello_serial.uf2: 554 KB
  ✓ hello_dilder.uf2: 106 KB

  Hardware
  ──────────────────────────────────────────────────
  ✓ Pico W detected on /dev/ttyACM0
```

If any step fails, the script explains the issue and lets you retry or skip. You can quit at any time with `q` or `Ctrl+C` and resume later with `--step N`.

---

## Table of Contents (Manual Guide)

The rest of this document is the full manual version of the same process, for reference or if you prefer to run each command yourself.

1. [What You Need](#1-what-you-need)
2. [Understanding the Hardware](#2-understanding-the-hardware)
3. [Install the Pico C/C++ SDK Toolchain](#3-install-the-pico-cc-sdk-toolchain)
4. [Set Up the Docker Build Environment (Optional)](#4-set-up-the-docker-build-environment-optional)
5. [Configure VSCode for Pico Development](#5-configure-vscode-for-pico-development)
6. [Checkpoint 1 — Hello World Serial (No Wiring Needed)](#6-checkpoint-1--hello-world-serial-no-wiring-needed)
7. [Connect the Display to the Pico W](#7-connect-the-display-to-the-pico-w)
8. [Checkpoint 2 — Hello World e-Ink Display](#8-checkpoint-2--hello-world-e-ink-display)
9. [Debugging](#9-debugging)
10. [Troubleshooting](#10-troubleshooting)
11. [Next Steps](#11-next-steps)

---

## 1. What You Need

### Hardware

| Item | Notes |
|------|-------|
| Raspberry Pi Pico W | **With male headers soldered on** |
| Waveshare 2.13" e-Paper HAT V3 | SSD1680 driver — check the PCB silkscreen on the back |
| Micro-USB data cable | **Must be a data cable, not charge-only** — this is the #1 gotcha |
| Linux PC | Arch/CachyOS, Ubuntu, Debian, or Fedora |

> **No breadboard or jumper wires needed.** The Waveshare HAT has a female header socket that slides directly onto the Pico W's male header pins.

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

- **Chip:** RP2040 — dual-core ARM Cortex-M0+ at 133 MHz
- **RAM:** 264 KB SRAM
- **Flash:** 2 MB onboard QSPI
- **GPIO:** 26 multi-function pins (3.3V logic — **NOT 5V tolerant**)
- **USB:** Micro-USB 1.1 — used for flashing and serial output
- **Wi-Fi:** 802.11n 2.4 GHz (Infineon CYW43439)

### The Waveshare 2.13" e-Paper V3 at a Glance

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

The Pico SDK needs an environment variable pointing to its location. Add this to your shell profile:

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

`picotool` lets you inspect and flash `.uf2` files from the command line.

=== "Arch / CachyOS"

    ```bash
    # Available in the AUR
    yay -S picotool
    # or: paru -S picotool
    ```

=== "Build from Source (any distro)"

    ```bash
    cd ~/pico
    git clone https://github.com/raspberrypi/picotool.git
    cd picotool
    mkdir build && cd build
    cmake ..
    make -j$(nproc)
    sudo make install
    ```

### Step 3.6 — Serial Port Permissions

The Pico W appears as `/dev/ttyACM0` when connected via USB. You need permission to access it.

The group name depends on your distro:
- **Arch / CachyOS / Manjaro:** `uucp`
- **Ubuntu / Debian:** `dialout`

```bash
# Arch / CachyOS — use the 'uucp' group
sudo usermod -aG uucp $USER

# Ubuntu / Debian — use the 'dialout' group
sudo usermod -aG dialout $USER
```

**You must log out and back in** (or reboot) for this to take effect. A new terminal is not enough.

Verify after logging back in:

```bash
# Arch / CachyOS
groups | grep uucp

# Ubuntu / Debian
groups | grep dialout
```

---

## 4. Set Up the Docker Build Environment (Optional)

If you prefer a containerized build environment for reproducibility (or don't want to install the ARM toolchain globally), use the provided Docker setup.

### Step 4.1 — Install Docker and Docker Compose

=== "Arch / CachyOS"

    ```bash
    sudo pacman -S docker docker-compose
    sudo systemctl enable --now docker
    sudo usermod -aG docker $USER
    # Log out and back in
    ```

=== "Ubuntu / Debian"

    ```bash
    sudo apt install docker.io docker-compose-v2
    sudo systemctl enable --now docker
    sudo usermod -aG docker $USER
    # Log out and back in
    ```

### Step 4.2 — Build Using the Container

From the `dev-setup/` directory:

```bash
cd dev-setup/

# Build the container image
docker compose build

# Compile the hello-world-serial project
docker compose run --rm -w /project build
# (mount hello-world-serial instead — see docker-compose.yml)

# The compiled .uf2 file will appear in the build/ directory
```

The container mounts your project directory, compiles the code, and outputs the binary. You flash it to the Pico W the same way as a native build.

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
    # Or download from https://code.visualstudio.com/
    ```

### Step 5.2 — Install Required Extensions

Open VSCode and install these extensions (`Ctrl+Shift+X` to open the Extensions panel):

| Extension | ID | Purpose |
|-----------|----|---------|
| **C/C++** | `ms-vscode.cpptools` | IntelliSense, syntax highlighting, debugging |
| **CMake Tools** | `ms-vscode.cmake-tools` | CMake project management, build, configure |
| **CMake** | `twxs.cmake` | CMake syntax highlighting for `CMakeLists.txt` |
| **Serial Monitor** | `ms-vscode.vscode-serial-monitor` | View serial output from the Pico W |
| **Cortex-Debug** | `marus25.cortex-debug` | ARM Cortex debugging via SWD (optional) |

Or install from the command line:

```bash
code --install-extension ms-vscode.cpptools
code --install-extension ms-vscode.cmake-tools
code --install-extension twxs.cmake
code --install-extension ms-vscode.vscode-serial-monitor
code --install-extension marus25.cortex-debug
```

### Step 5.3 — Configure CMake Tools for Cross-Compilation

Open your Dilder project in VSCode:

```bash
code /home/<your-username>/CodingProjects/Dilder
```

Create the VSCode settings directory and configuration:

```bash
mkdir -p .vscode
```

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
    "files.associations": {
        "*.h": "c",
        "*.c": "c"
    }
}
```

> **Note:** This initially points at `hello-world-serial`. After you complete Checkpoint 1, change `cmake.sourceDirectory` and `cmake.buildDirectory` to `hello-world` for the display project.

Create `.vscode/cmake-kits.json` to tell CMake Tools to use the ARM cross-compiler:

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

### Step 5.4 — Configure IntelliSense

Create `.vscode/c_cpp_properties.json` so IntelliSense resolves Pico SDK headers:

```json
{
    "configurations": [
        {
            "name": "Pico W",
            "includePath": [
                "${workspaceFolder}/dev-setup/**",
                "${env:PICO_SDK_PATH}/src/**"
            ],
            "defines": [
                "PICO_BOARD=pico_w",
                "LIB_PICO_STDIO_USB"
            ],
            "compilerPath": "/usr/bin/arm-none-eabi-gcc",
            "cStandard": "c11",
            "intelliSenseMode": "gcc-arm"
        }
    ],
    "version": 4
}
```

### Step 5.5 — Select the Build Kit

1. Open the Command Palette (`Ctrl+Shift+P`).
2. Type **"CMake: Select a Kit"** and press Enter.
3. Choose **"Pico W ARM GCC"** from the list.

If it doesn't appear, reload VSCode (`Ctrl+Shift+P` > "Developer: Reload Window").

---

## 6. Checkpoint 1 — Hello World Serial (No Wiring Needed)

**Goal:** Verify the entire toolchain works before touching the display. Just the Pico W plugged into USB — nothing else.

This builds and flashes a minimal C program that blinks the onboard LED and prints to USB serial. If this works, your toolchain, build system, flash process, and serial connection are all confirmed good.

### Step 6.1 — Copy the SDK CMake Helper

Every Pico C project needs this file. Copy it into the serial project:

```bash
cp $PICO_SDK_PATH/external/pico_sdk_import.cmake \
   ~/CodingProjects/Dilder/dev-setup/hello-world-serial/
```

### Step 6.2 — Review the Code

The project is at `dev-setup/hello-world-serial/`. It contains two files:

**`CMakeLists.txt`** �� minimal build config:
- Links only `pico_stdlib` (no SPI, no display libraries)
- Enables USB serial, disables UART serial
- Produces `hello_serial.uf2`

**`main.c`** — the program:
```c
#include <stdio.h>
#include "pico/stdlib.h"

int main(void) {
    stdio_init_all();
    sleep_ms(2000);

    printf("=========================\n");
    printf("  Hello, Dilder!\n");
    printf("  Pico W is alive.\n");
    printf("=========================\n\n");

    gpio_init(PICO_DEFAULT_LED_PIN);
    gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);

    uint32_t count = 0;
    bool led_on = false;

    while (true) {
        count++;
        led_on = !led_on;
        gpio_put(PICO_DEFAULT_LED_PIN, led_on);
        printf("Heartbeat #%lu  |  LED: %s\n",
               (unsigned long)count, led_on ? "ON" : "OFF");
        sleep_ms(1000);
    }

    return 0;
}
```

It does three things:
1. Prints "Hello, Dilder!" to USB serial
2. Blinks the onboard LED every second
3. Prints a heartbeat counter

### Step 6.3 — Build

**From the terminal:**

```bash
cd ~/CodingProjects/Dilder/dev-setup/hello-world-serial

mkdir -p build && cd build

cmake -G Ninja \
      -DPICO_SDK_PATH=$PICO_SDK_PATH \
      -DPICO_BOARD=pico_w \
      ..

ninja
```

**From VSCode:**

1. `Ctrl+Shift+P` > **"CMake: Configure"** — select "Pico W ARM GCC" if prompted.
2. `Ctrl+Shift+P` > **"CMake: Build"** (or press `F7`).

If successful, you will see `hello_serial.uf2` in the `build/` directory.

### Step 6.4 — Flash

1. **Unplug** the Pico W from USB.
2. **Hold down the BOOTSEL button** (the small white button on the board).
3. **While holding BOOTSEL**, plug the USB cable into the Pico W and your computer.
4. **Release BOOTSEL** after 1 second.

The Pico W appears as a USB drive named **RPI-RP2**.

```bash
# Copy the firmware
cp build/hello_serial.uf2 /run/media/$USER/RPI-RP2/

# On Ubuntu/Debian:
# cp build/hello_serial.uf2 /media/$USER/RPI-RP2/
```

The Pico automatically reboots and the USB drive disappears. This is normal — it's now running your code.

### Step 6.5 — Verify

**Open a serial monitor:**

In VSCode:
1. `Ctrl+Shift+P` > **"Serial Monitor: Open Serial Monitor"**
2. Port: `/dev/ttyACM0`
3. Baud rate: **115200**
4. Click **Start Monitoring**

Or from the terminal:
```bash
screen /dev/ttyACM0 115200
# Exit: Ctrl+A, then K, then Y
```

**You should see:**

```
=========================
  Hello, Dilder!
  Pico W is alive.
=========================

Heartbeat #1  |  LED: ON
Heartbeat #2  |  LED: OFF
Heartbeat #3  |  LED: ON
...
```

**Check the board:** The onboard LED should blink on and off every second.

### Checkpoint 1 Complete

If you see the serial output and the LED blinks — congratulations. Your toolchain, build system, flash process, and serial connection all work. Everything from here builds on this foundation.

If something failed, see [Troubleshooting](#10-troubleshooting) before continuing.

---

## 7. Connect the Display to the Pico W

Now that the Pico W is confirmed working, let's attach the e-ink display.

> **IMPORTANT:** Disconnect the Pico W from USB before attaching the display. Voltage spikes can damage the e-ink panel.

### Direct Header Connection

The Pico W has **male header pins soldered on**. The Waveshare HAT has a **female header socket** on its underside that accepts a full 40-pin header. The display slides directly onto the Pico W — no breadboard, no jumper wires.

### Step 7.1 — Align the Headers

1. Hold the Pico W with the **USB port facing you**.
2. Hold the Waveshare HAT with its **display face up** and the 40-pin socket facing down.
3. Align **pin 1** on both boards. Pin 1 on the Pico W is the top-left pin (GP0) when the USB port faces you. The HAT's socket has a corresponding pin 1 marking.
4. The HAT's header socket covers all 40 pins of the Pico W.

### Step 7.2 — Seat the Display

1. Line up all pins carefully — **do not force it at an angle**.
2. Press down firmly and evenly until the HAT is fully seated on the Pico W headers.
3. The HAT should sit snug with no pins visible between the boards.

```
    Side view (seated correctly):

    ┌─────────────────────────┐  Waveshare HAT (display face up)
    │  ▓▓▓ e-ink display ▓▓▓ │
    ├─────────────────────────┤
    │ female socket ▼▼▼▼▼▼▼▼ │
    ├═════════════════════════┤  <-- flush, no gap
    │ male headers ▲▲▲▲▲▲▲▲  │
    ├─────────────────────────┤
    │    Raspberry Pi Pico W  │
    └────────[USB]────────────┘
```

### Step 7.3 — Verify the Connection

Before plugging in USB, check:

- [ ] **The HAT is fully seated** — no header pins are exposed between the boards.
- [ ] **Pin 1 alignment is correct** — the HAT is not offset or rotated.
- [ ] **The display's FPC ribbon cable is not pinched** between the boards.
- [ ] **Nothing is shorting** — no stray wires or metal touching the boards.

> **Photos coming soon** — this section will be updated with reference images showing the correct assembly.

### Pin Mapping (for reference)

The HAT routes these signals through its PCB from the 40-pin socket to the display:

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

These are the same pins used in the Waveshare Pico examples — the HAT takes care of routing them.

---

## 8. Checkpoint 2 — Hello World e-Ink Display

**Goal:** Draw text on the e-ink display using the Waveshare C library.

### Step 8.1 — Copy the SDK CMake Helper

```bash
cp $PICO_SDK_PATH/external/pico_sdk_import.cmake \
   ~/CodingProjects/Dilder/dev-setup/hello-world/
```

### Step 8.2 — Get the Waveshare C Library

The display driver and drawing library come from Waveshare's official repository:

```bash
cd /tmp
git clone https://github.com/waveshare/Pico_ePaper_Code.git

# Copy the C library files into your project
cd ~/CodingProjects/Dilder/dev-setup/hello-world

mkdir -p lib/Config lib/e-Paper lib/GUI lib/Fonts

# Config files (SPI/GPIO setup + debug header)
cp /tmp/Pico_ePaper_Code/c/lib/Config/DEV_Config.h lib/Config/
cp /tmp/Pico_ePaper_Code/c/lib/Config/DEV_Config.c lib/Config/
cp /tmp/Pico_ePaper_Code/c/lib/Config/Debug.h lib/Config/

# Display driver (V3)
cp /tmp/Pico_ePaper_Code/c/lib/e-Paper/EPD_2in13_V3.h lib/e-Paper/
cp /tmp/Pico_ePaper_Code/c/lib/e-Paper/EPD_2in13_V3.c lib/e-Paper/

# GUI/Paint library
cp /tmp/Pico_ePaper_Code/c/lib/GUI/GUI_Paint.h lib/GUI/
cp /tmp/Pico_ePaper_Code/c/lib/GUI/GUI_Paint.c lib/GUI/

# Fonts
cp /tmp/Pico_ePaper_Code/c/lib/Fonts/fonts.h lib/Fonts/
cp /tmp/Pico_ePaper_Code/c/lib/Fonts/font8.c lib/Fonts/
cp /tmp/Pico_ePaper_Code/c/lib/Fonts/font12.c lib/Fonts/
cp /tmp/Pico_ePaper_Code/c/lib/Fonts/font16.c lib/Fonts/
cp /tmp/Pico_ePaper_Code/c/lib/Fonts/font20.c lib/Fonts/
cp /tmp/Pico_ePaper_Code/c/lib/Fonts/font24.c lib/Fonts/

# Clean up
rm -rf /tmp/Pico_ePaper_Code
```

> **Note:** The Waveshare library files are not included in this repository to respect licensing. You must clone them yourself using the commands above.

### Step 8.3 — Project Structure

```
dev-setup/hello-world/
    CMakeLists.txt          # Build configuration
    pico_sdk_import.cmake   # Pico SDK CMake helper (copied from SDK)
    main.c                  # Application code — draws to the display
    lib/
        Config/
            DEV_Config.h    # Hardware pin definitions
            DEV_Config.c    # SPI and GPIO initialization
        e-Paper/
            EPD_2in13_V3.h  # Display driver header
            EPD_2in13_V3.c  # Display driver implementation
        GUI/
            GUI_Paint.h     # Drawing library header
            GUI_Paint.c     # Drawing library (text, lines, shapes)
        Fonts/
            fonts.h         # Font declarations
            font8.c – font24.c  # Font data (8px through 24px)
```

### Step 8.4 — What the Code Does

`main.c` runs this sequence:

1. Initializes USB serial output (so `printf` goes to your terminal)
2. Initializes the SPI bus and GPIO pins for the display
3. Clears the e-ink display (full white)
4. Draws a black border rectangle
5. Draws "Hello, Dilder!" in 24px font
6. Draws "Pico W + e-Paper V3" in 16px font
7. Draws "First build successful!" in 12px font
8. Puts the display to sleep (low power)
9. Enters a heartbeat loop on serial

### Step 8.5 — Update VSCode Source Directory

If you configured VSCode to point at `hello-world-serial` in Step 5, update `.vscode/settings.json`:

```json
{
    "cmake.sourceDirectory": "${workspaceFolder}/dev-setup/hello-world",
    "cmake.buildDirectory": "${workspaceFolder}/dev-setup/hello-world/build"
}
```

### Step 8.6 — Build

**From the terminal:**

```bash
cd ~/CodingProjects/Dilder/dev-setup/hello-world

mkdir -p build && cd build

cmake -G Ninja \
      -DPICO_SDK_PATH=$PICO_SDK_PATH \
      -DPICO_BOARD=pico_w \
      ..

ninja
```

**From VSCode:**

1. `Ctrl+Shift+P` > **"CMake: Configure"**
2. `Ctrl+Shift+P` > **"CMake: Build"** (or `F7`)

Output: `build/hello_dilder.uf2`

### Step 8.7 — Flash

1. Unplug the Pico W.
2. Hold BOOTSEL, plug in USB, release BOOTSEL.
3. Copy the firmware:

```bash
cp build/hello_dilder.uf2 /run/media/$USER/RPI-RP2/
# Ubuntu: cp build/hello_dilder.uf2 /media/$USER/RPI-RP2/
```

Or with picotool:
```bash
picotool load build/hello_dilder.uf2
picotool reboot
```

### Step 8.8 — Verify

**Serial output** (same as Checkpoint 1):

```
Hello, Dilder!
Initializing e-Paper display...
Display initialized.
Drawing to display...
Display updated. Entering sleep mode.
Heartbeat: 1
Heartbeat: 2
...
```

**The display** should show:

- A **black border** rectangle around the edges
- **"Hello, Dilder!"** in 24px font near the top
- **"Pico W + e-Paper V3"** in 16px font below that
- **"First build successful!"** in 12px font at the bottom

### Checkpoint 2 Complete

If text appears on the display and serial output is flowing — the full hardware stack is working. You have a verified build-flash-debug pipeline for C development on the Pico W with the e-ink display.

---

## 9. Debugging

### 9.1 — Printf Debugging (USB Serial)

The simplest and most effective approach. Both hello world projects are configured for this — `printf()` output goes to USB serial at 115200 baud.

```c
#include <stdio.h>

printf("SPI initialized: SCK=%d, TX=%d\n", 10, 11);
printf("Display BUSY pin state: %d\n", gpio_get(13));
printf("Buffer size: %d bytes\n", image_size);
```

### 9.2 — Hardware Debugging with SWD (Advanced)

For breakpoint debugging (stepping through code line by line), you need a second Pico W acting as a debug probe.

**Hardware required:**

- A second Pico W (or Pico) flashed with the **Picoprobe** firmware.
- 3 jumper wires connecting the debug probe to the target Pico W.

**Wiring (debug probe to target):**

| Debug Probe Pin | Target Pin | Signal |
|-----------------|------------|--------|
| GP2 | SWCLK | Debug clock |
| GP3 | SWDIO | Debug data |
| GND | GND | Ground |

The target's SWCLK and SWDIO are the two pads on the bottom of the Pico W board (not GPIO header pins).

**Setup:**

1. Flash the debug probe Pico with `picoprobe.uf2` from [the Picoprobe releases](https://github.com/raspberrypi/picoprobe/releases).
2. Install OpenOCD:

=== "Arch / CachyOS"

    ```bash
    sudo pacman -S openocd
    ```

=== "Ubuntu / Debian"

    ```bash
    sudo apt install openocd
    ```

3. Add a `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Pico Debug (Cortex-Debug)",
            "type": "cortex-debug",
            "request": "launch",
            "cwd": "${workspaceFolder}/dev-setup/hello-world",
            "executable": "${workspaceFolder}/dev-setup/hello-world/build/hello_dilder.elf",
            "servertype": "openocd",
            "configFiles": [
                "interface/cmsis-dap.cfg",
                "target/rp2040.cfg"
            ],
            "searchDir": [],
            "runToEntryPoint": "main",
            "showDevDebugOutput": "raw"
        }
    ]
}
```

4. Press `F5` in VSCode to start debugging. Set breakpoints, step through code, inspect variables.

> **For this guide, printf debugging is more than sufficient.** SWD debugging is included for completeness.

---

## 10. Troubleshooting

### Build Issues

| Problem | Solution |
|---------|----------|
| `arm-none-eabi-gcc: command not found` | Toolchain not installed. Re-run Step 3.1 |
| `PICO_SDK_PATH is not defined` | Set the environment variable (Step 3.4). Restart your terminal |
| `Could not find pico_sdk_import.cmake` | Copy it from the SDK (Step 6.1 or 8.1) |
| CMake error about missing submodules | Run `cd $PICO_SDK_PATH && git submodule update --init` |
| Ninja not found | Install ninja: `sudo pacman -S ninja` or `sudo apt install ninja-build` |

### Flashing Issues

| Problem | Solution |
|---------|----------|
| RPI-RP2 drive doesn't appear | Hold BOOTSEL **before** plugging in USB. Try a different cable — **charge-only cables won't work** |
| Drive appears but copy fails | Try `picotool load` instead. Check if the `.uf2` file is 0 bytes (build failed) |
| Pico doesn't reboot after copy | Wait 5 seconds. If stuck, unplug and replug |

### Serial Issues

| Problem | Solution |
|---------|----------|
| `/dev/ttyACM0` doesn't exist | Pico not connected, or using charge-only cable, or firmware crashed before USB init |
| Permission denied on `/dev/ttyACM0` | Add yourself to the serial group — `uucp` on Arch/CachyOS, `dialout` on Ubuntu/Debian (Step 3.6), then **log out and back in** |
| Serial monitor shows nothing | Baud rate must be 115200. Check that `stdio_init_all()` is in your code |
| Garbled output | Wrong baud rate. Ensure both sides use 115200 |

### Display Issues

| Problem | Solution |
|---------|----------|
| Display completely blank | Check VCC is on 3V3(OUT) pin 36, not VBUS pin 40. Check all 8 wires |
| Display flickers then goes blank | RST or BUSY wires swapped. Compare against the wiring table |
| Garbage/random pixels | Wrong driver version — confirm V3 on PCB silkscreen. Check DIN/CLK wires |
| Display shows old image | E-ink retains the last image. Run a full clear (`EPD_2in13_V3_Clear()`) |
| `BUSY` pin always high | Display stuck mid-refresh. Disconnect power, wait 10 sec, reconnect, run Clear |

---

## 11. Next Steps

Now that you have a working C build and flash pipeline:

1. **Modify the text** — Change the strings in `main.c` and rebuild to see your changes.
2. **Add button input** — Wire the 5 tactile buttons (see [Wiring & Pinout](../website/docs/docs/hardware/wiring-pinout.md)) and read them with `gpio_get()`.
3. **Draw graphics** — The `GUI_Paint` library supports lines, rectangles, circles, and bitmap images.
4. **Try partial refresh** — Use `EPD_2in13_V3_Display_Partial()` for fast updates without full-screen flicker.
5. **Move to the firmware scaffold** — Start building the Dilder pet logic in a proper project structure.

---

## Quick Reference Card

| Action | Command |
|--------|---------|
| Build (serial) | `cd dev-setup/hello-world-serial/build && ninja` |
| Build (display) | `cd dev-setup/hello-world/build && ninja` |
| Flash | Hold BOOTSEL + plug USB, then `cp build/<name>.uf2 /run/media/$USER/RPI-RP2/` |
| Flash (picotool) | `picotool load build/<name>.uf2 && picotool reboot` |
| Serial monitor | `screen /dev/ttyACM0 115200` |
| Serial monitor (VSCode) | `Ctrl+Shift+P` > "Serial Monitor: Open Serial Monitor" |
| Clean rebuild | `rm -rf build && mkdir build && cd build && cmake -G Ninja -DPICO_SDK_PATH=$PICO_SDK_PATH -DPICO_BOARD=pico_w .. && ninja` |
| Build with Docker | `cd dev-setup && docker compose run --rm build` |
