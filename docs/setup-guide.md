# RegardedPal Hardware & Development Setup Guide

A complete, step-by-step guide to setting up a Raspberry Pi Zero WH with a Waveshare 2.13" e-Paper HAT (V3) for the RegardedPal virtual pet project. This guide assumes you have purchased all materials from the [hardware-research.md](hardware-research.md) materials list.

**Target hardware:**
- Raspberry Pi Zero WH (pre-soldered headers)
- Waveshare Pico-ePaper-2.13 (SSD1680 driver, 250x122px, black & white, Pico-native module)
- Half-size breadboard + jumper wires
- 5x 6x6mm tactile push buttons
- Micro SD card (16GB+)
- Micro-USB power supply (5V 2.5A)

---

## Table of Contents

1. [Hardware Overview](#1-hardware-overview)
   - 1.1 [Pi Zero WH Specs](#11-pi-zero-wh-specs)
   - 1.2 [Waveshare 2.13" e-Paper V3 Specs](#12-waveshare-213-e-paper-v3-specs)
   - 1.3 [V3 Version Identification](#13-v3-version-identification)
   - 1.4 [Pin Mapping](#14-pin-mapping)
   - 1.5 [GPIO Pin Budget](#15-gpio-pin-budget)
2. [Flash Raspberry Pi OS](#2-flash-raspberry-pi-os)
   - 2.1 [Download Raspberry Pi Imager](#21-download-raspberry-pi-imager)
   - 2.2 [Choose the Right OS Image](#22-choose-the-right-os-image)
   - 2.3 [Configure Headless Settings](#23-configure-headless-settings)
   - 2.4 [Write the Image](#24-write-the-image)
3. [First Boot & SSH Access](#3-first-boot--ssh-access)
   - 3.1 [Power On and Wait](#31-power-on-and-wait)
   - 3.2 [Find Your Pi on the Network](#32-find-your-pi-on-the-network)
   - 3.3 [Connect via SSH](#33-connect-via-ssh)
   - 3.4 [Set Up SSH Keys (Passwordless Login)](#34-set-up-ssh-keys-passwordless-login)
4. [System Configuration](#4-system-configuration)
   - 4.1 [Update the System](#41-update-the-system)
   - 4.2 [Enable SPI](#42-enable-spi)
   - 4.3 [Enable I2C (Optional)](#43-enable-i2c-optional)
   - 4.4 [Verify Interfaces](#44-verify-interfaces)
   - 4.5 [Set Timezone and Locale](#45-set-timezone-and-locale)
5. [Python Development Environment](#5-python-development-environment)
   - 5.1 [Install System Dependencies](#51-install-system-dependencies)
   - 5.2 [Create a Virtual Environment](#52-create-a-virtual-environment)
   - 5.3 [Install Python Packages](#53-install-python-packages)
   - 5.4 [Install the Waveshare e-Paper Library](#54-install-the-waveshare-e-paper-library)
6. [Connect the Display](#6-connect-the-display)
   - 6.1 [Attach the HAT](#61-attach-the-hat)
   - 6.2 [Verify the Connection](#62-verify-the-connection)
7. [Display "Hello World"](#7-display-hello-world)
   - 7.1 [Run the Waveshare Demo](#71-run-the-waveshare-demo)
   - 7.2 [Write a Minimal Script](#72-write-a-minimal-script)
   - 7.3 [Understanding the Code](#73-understanding-the-code)
   - 7.4 [Custom Fonts](#74-custom-fonts)
   - 7.5 [Drawing Shapes](#75-drawing-shapes)
   - 7.6 [Displaying Images](#76-displaying-images)
   - 7.7 [Partial Refresh (Fast Updates)](#77-partial-refresh-fast-updates)
8. [Wire the Buttons](#8-wire-the-buttons)
   - 8.1 [Breadboard Wiring Diagram](#81-breadboard-wiring-diagram)
   - 8.2 [Button Test Script](#82-button-test-script)
   - 8.3 [Debouncing](#83-debouncing)
9. [Development Workflow](#9-development-workflow)
   - 9.1 [Local Edit + rsync + SSH (Recommended)](#91-local-edit--rsync--ssh-recommended)
   - 9.2 [VS Code Remote-SSH (Pi Zero 2 W Only)](#92-vs-code-remote-ssh-pi-zero-2-w-only)
   - 9.3 [Remote Debugging with debugpy](#93-remote-debugging-with-debugpy)
   - 9.4 [Makefile for Common Tasks](#94-makefile-for-common-tasks)
10. [Project Structure](#10-project-structure)
11. [Run at Boot (systemd)](#11-run-at-boot-systemd)
12. [Debugging & Troubleshooting](#12-debugging--troubleshooting)
    - 12.1 [Display Not Refreshing](#121-display-not-refreshing)
    - 12.2 [SPI Not Detected](#122-spi-not-detected)
    - 12.3 [Permission Errors](#123-permission-errors)
    - 12.4 [Ghost Images / Burn-in](#124-ghost-images--burn-in)
    - 12.5 [GPIO / Button Issues](#125-gpio--button-issues)
    - 12.6 [GPIO Testing Tools](#126-gpio-testing-tools)
13. [Reference Links](#13-reference-links)

---

## 1. Hardware Overview

### 1.1 Pi Zero WH Specs

| Spec | Value |
|------|-------|
| SoC | BCM2835 (ARMv6, 1GHz single-core) |
| RAM | 512MB |
| WiFi | 802.11 b/g/n 2.4GHz |
| Bluetooth | 4.1 BLE |
| GPIO | 40-pin header (pre-soldered on WH) |
| USB | 1x micro-USB (data), 1x micro-USB (power only) |
| Video | mini-HDMI |
| Storage | micro SD |
| Dimensions | 65mm x 30mm x 5mm |

The "WH" designation means the 2x20 GPIO header is pre-soldered. This is essential -- the e-Paper HAT plugs directly onto it.

If you have a Pi Zero 2 W instead, everything in this guide still applies. The Zero 2 W has a quad-core ARMv8 (BCM2710) and supports both 32-bit and 64-bit OS images.

### 1.2 Waveshare 2.13" e-Paper V3 Specs

| Spec | Value |
|------|-------|
| Display size | 2.13 inches diagonal |
| Resolution | 250 x 122 pixels |
| Active area | 48.55mm x 23.71mm |
| Glass outline | 59.2mm x 29.2mm x 1.05mm |
| Colors | Black and white (1-bit) |
| Driver IC | SSD1680Z8 |
| Interface | 4-wire SPI (Mode 0: CPOL=0, CPHA=0) |
| Logic voltage | 3.3V (onboard level shifter supports 5V input) |
| Full refresh time | ~3 seconds |
| Partial refresh time | ~0.3 seconds |
| Deep sleep current | ~1 uA |
| Operating temperature | 0 to 50 C |
| DPI | 130 |
| Weight | ~3.2g (display only) |
| HAT board dimensions | 65mm x 30.2mm |

Source: [Waveshare V3 Specification PDF](https://files.waveshare.com/upload/5/59/2.13inch_e-Paper_V3_Specificition.pdf)

### 1.3 V3 Version Identification

The Waveshare 2.13" e-Paper HAT has gone through multiple hardware revisions. **You must use the correct driver code for your version.** Check the sticker on the back of your display or the product listing:

| Version | Driver IC | Python driver file | Released |
|---------|-----------|-------------------|----------|
| V1 | SSD1675 / IL3897 | `epd2in13.py` | ~2017 |
| V2 | SSD1675B | `epd2in13_V2.py` | ~2019 |
| **V3** | **SSD1680Z8** | **`epd2in13_V3.py`** | **~2022** |
| V4 | SSD1680Z8 | `epd2in13_V4.py` | ~2023 |

V3 and V4 share the same SSD1680 driver IC, but their initialization sequences and lookup tables (LUTs) differ. Using the wrong driver file will result in a blank or garbled display.

### 1.4 Pin Mapping

The HAT plugs directly onto the Pi Zero's 40-pin GPIO header. No jumper wires needed for the display. These are the pins it uses:

| e-Paper Function | BCM GPIO | Physical Pin | Direction |
|-----------------|----------|-------------|-----------|
| VCC (3.3V) | 3.3V | 1 | Power |
| GND | GND | 6 | Power |
| DIN (MOSI) | GPIO 10 | 19 | Pi -> Display |
| CLK (SCLK) | GPIO 11 | 23 | Pi -> Display |
| CS (CE0) | GPIO 8 | 24 | Pi -> Display |
| DC | GPIO 25 | 22 | Pi -> Display |
| RST | GPIO 17 | 11 | Pi -> Display |
| BUSY | GPIO 24 | 18 | Display -> Pi |
| PWR | GPIO 18 | 12 | Pi -> Display |

**Note:** The HAT has no user-accessible switches or jumpers. The SPI bus selection (4-wire vs 3-wire) is hardwired to 4-wire mode on the PCB.

### 1.5 GPIO Pin Budget

With the display using GPIO 8, 10, 11, 17, 18, 24, 25, here are the remaining GPIO pins available for buttons and future peripherals:

| Available GPIO | Physical Pin | Suggested Use |
|---------------|-------------|---------------|
| GPIO 5 | 29 | Button: UP |
| GPIO 6 | 31 | Button: DOWN |
| GPIO 13 | 33 | Button: LEFT |
| GPIO 19 | 35 | Button: RIGHT |
| GPIO 26 | 37 | Button: SELECT |
| GPIO 12 | 32 | Future: Piezo buzzer (PWM0) |
| GPIO 16 | 36 | Future: spare |
| GPIO 20 | 38 | Future: spare |
| GPIO 21 | 40 | Future: spare |
| GPIO 22 | 15 | Future: spare |
| GPIO 23 | 16 | Future: spare |
| GPIO 27 | 13 | Future: spare |

**Pins to avoid:**
- GPIO 2 (SDA) / GPIO 3 (SCL) -- reserved for I2C if needed later
- GPIO 14 (TXD) / GPIO 15 (RXD) -- reserved for serial console
- GPIO 0 / GPIO 1 -- used for HAT EEPROM (ID_SD/ID_SC)

---

## 2. Flash Raspberry Pi OS

### 2.1 Download Raspberry Pi Imager

Download from: https://www.raspberrypi.com/software/

Available for Windows, macOS, and Linux. Install and open it.

### 2.2 Choose the Right OS Image

In Raspberry Pi Imager:

1. **Choose Device** -> Raspberry Pi Zero (or Zero 2 W)
2. **Choose OS** -> Raspberry Pi OS (other) -> **Raspberry Pi OS Lite (32-bit)**

**Why these choices:**
- **32-bit is required** for the original Pi Zero WH (ARMv6). 64-bit images will not boot.
- **Lite (no desktop)** because we are running headless. No monitor needed.
- Use the **Bookworm**-based image. Avoid Trixie-based images (December 2025+) as they have reported WiFi driver issues for headless setup.

### 2.3 Configure Headless Settings

Before clicking "Write", click the **gear icon** (or press **Ctrl+Shift+X**) to open OS Customisation:

**General tab:**
- Set hostname: `regardedpal`
- Set username and password: e.g., `pi` / `your-secure-password`
  - **Important:** There is no default `pi`/`raspberry` login anymore. You must create a user here.

**Services tab:**
- Enable SSH: Yes
- Use password authentication (or paste your public key from `~/.ssh/id_ed25519.pub`)

**WiFi tab (if shown under General):**
- Enter your WiFi SSID and password
- Set your wireless LAN country code (e.g., `DE`, `US`, `GB`)

Click **Save**.

### 2.4 Write the Image

1. **Choose Storage** -> select your micro SD card
2. Click **Write**
3. Wait for the write and verification to complete
4. Eject the SD card

---

## 3. First Boot & SSH Access

### 3.1 Power On and Wait

1. Insert the micro SD card into the Pi Zero WH
2. **Do not attach the e-Paper HAT yet** -- let's get SSH working first
3. Connect the micro-USB power supply to the **PWR** port (the one closer to the edge, not the one near the HDMI port)
4. Wait ~90-120 seconds for first boot. The first boot takes longer as it resizes the filesystem and applies your headless configuration.

### 3.2 Find Your Pi on the Network

**Method 1: mDNS (easiest)**
```bash
ping regardedpal.local
```
This works out of the box on Linux and macOS. On Windows, mDNS support is included with Bonjour (installed with iTunes/iCloud) or natively on Windows 10+.

**Method 2: Network scan**
```bash
# Find all devices on your network
nmap -sn 192.168.1.0/24

# Or specifically look for SSH-enabled devices
nmap -p 22 --open 192.168.1.0/24
```

**Method 3: Router admin page**

Log into your router (usually `192.168.1.1` or `192.168.0.1`) and check the DHCP client list for your hostname.

**Method 4: ARP table**
```bash
# Raspberry Pi Foundation MAC prefixes: b8:27:eb, dc:a6:32, d8:3a:dd, 2c:cf:67
arp -a | grep -i "b8:27:eb\|dc:a6:32\|d8:3a:dd\|2c:cf:67"
```

### 3.3 Connect via SSH

```bash
ssh pi@regardedpal.local
```

Enter the password you set during imaging. You should see a Raspberry Pi OS prompt.

### 3.4 Set Up SSH Keys (Passwordless Login)

On your **development machine** (not the Pi):

```bash
# Generate a key pair if you don't have one
ssh-keygen -t ed25519 -C "dev@regardedpal"

# Copy your public key to the Pi
ssh-copy-id pi@regardedpal.local

# Test passwordless login
ssh pi@regardedpal.local
# Should log in without asking for a password
```

---

## 4. System Configuration

### 4.1 Update the System

```bash
sudo apt update && sudo apt full-upgrade -y
```

This may take a while on the Pi Zero (single-core, limited RAM). Be patient.

If the kernel was updated, reboot:
```bash
sudo reboot
```

### 4.2 Enable SPI

The e-Paper display communicates over SPI. It must be enabled.

**Option A: Interactive**
```bash
sudo raspi-config
# Navigate: Interface Options -> SPI -> Yes -> OK -> Finish
```

**Option B: Non-interactive (one-liner)**
```bash
sudo raspi-config nonint do_spi 0
```

This adds `dtparam=spi=on` to `/boot/firmware/config.txt`.

Reboot after enabling:
```bash
sudo reboot
```

### 4.3 Enable I2C (Optional)

Not needed for the e-Paper display, but useful if you later add I2C peripherals:

```bash
sudo raspi-config nonint do_i2c 0
sudo reboot
```

### 4.4 Verify Interfaces

After reboot, verify SPI is working:

```bash
# Check SPI devices exist
ls /dev/spidev*
# Expected: /dev/spidev0.0  /dev/spidev0.1

# Check the kernel module is loaded
lsmod | grep spi
# Expected: spi_bcm2835
```

If `/dev/spidev*` does not appear, SPI is not enabled. Double-check `/boot/firmware/config.txt` contains `dtparam=spi=on` and reboot.

### 4.5 Set Timezone and Locale

```bash
# Set timezone
sudo timedatectl set-timezone Europe/Berlin    # or your timezone

# Verify
timedatectl
```

---

## 5. Python Development Environment

### 5.1 Install System Dependencies

```bash
sudo apt install -y \
  python3-pip \
  python3-venv \
  python3-dev \
  python3-pil \
  python3-numpy \
  python3-gpiozero \
  python3-lgpio \
  python3-spidev \
  libopenjp2-7 \
  libtiff6 \
  libatlas-base-dev \
  git \
  build-essential \
  cmake \
  gpiod
```

**What these are:**
- `python3-pip, python3-venv, python3-dev` -- Python tooling
- `python3-pil` -- Pillow (PIL) for image creation and manipulation
- `python3-numpy` -- numerical operations (used by some display drivers)
- `python3-gpiozero` -- high-level GPIO library (used by Waveshare epdconfig.py)
- `python3-lgpio` -- low-level GPIO backend for gpiozero on Bookworm
- `python3-spidev` -- SPI communication library
- `libopenjp2-7, libtiff6, libatlas-base-dev` -- native dependencies for Pillow/NumPy
- `git` -- to clone the Waveshare library
- `build-essential, cmake` -- C/C++ build tools for future use
- `gpiod` -- GPIO command-line debugging tools

### 5.2 Create a Virtual Environment

```bash
mkdir -p ~/regardedpal
cd ~/regardedpal

python3 -m venv --system-site-packages .venv
source .venv/bin/activate
```

**Why `--system-site-packages`?** This gives the virtual environment access to system-installed packages like `gpiozero`, `lgpio`, and `spidev` which are pre-installed on Raspberry Pi OS and can be difficult to pip-install from source on the Pi Zero's limited hardware.

**Important (Bookworm change):** Raspberry Pi OS Bookworm enforces PEP 668 -- you cannot `pip install` packages system-wide. You **must** use a virtual environment.

### 5.3 Install Python Packages

With the venv activated:

```bash
pip install Pillow spidev RPi.GPIO
```

Most of these are already available via `--system-site-packages`, but installing them in the venv ensures you have the latest versions.

### 5.4 Install the Waveshare e-Paper Library

```bash
cd ~
git clone https://github.com/waveshareteam/e-Paper.git
```

The library structure you need:

```
~/e-Paper/
  RaspberryPi_JetsonNano/
    python/
      lib/
        waveshare_epd/
          epdconfig.py              # Platform detection, GPIO/SPI init
          epd2in13_V3.py            # <-- V3 driver (this is your file)
      examples/
        epd_2in13_V3_test.py        # V3 demo script
      pic/
        Font.ttc                    # Font used in demos
        2in13.bmp                   # Sample image
```

The library is not pip-installable -- you add it to your Python path at runtime. We will set this up in our scripts.

---

## 6. Connect the Display

### 6.1 Attach the HAT

1. **Power off the Pi** (`sudo shutdown -h now`, then disconnect power)
2. The e-Paper HAT has a 2x20 female header on the underside
3. Align it with the Pi Zero's male GPIO header -- the display should face upward, with the HAT board covering the Pi Zero
4. Press down firmly and evenly until the header is fully seated
5. The HAT board is the same dimensions as the Pi Zero (65x30mm) so they should align perfectly
6. Reconnect power

### 6.2 Verify the Connection

After booting, verify the SPI device is still visible:

```bash
ls /dev/spidev*
# Should still show: /dev/spidev0.0  /dev/spidev0.1
```

If the display HAT is properly seated, the SPI device will still appear. The display won't show anything yet -- it needs software to drive it.

---

## 7. Display "Hello World"

### 7.1 Run the Waveshare Demo

The quickest way to verify everything works:

```bash
cd ~/e-Paper/RaspberryPi_JetsonNano/python/examples/
source ~/regardedpal/.venv/bin/activate
sudo python3 epd_2in13_V3_test.py
```

**Why `sudo`?** GPIO and SPI access requires root privileges (or correct group membership -- see Section 12.3).

This demo will:
1. Clear the display (flash white)
2. Draw text, lines, rectangles, circles
3. Show a bitmap image
4. Demonstrate partial refresh
5. Put the display to sleep

If you see content on the e-ink display, your hardware is working. Move on to writing your own code.

### 7.2 Write a Minimal Script

Create your first RegardedPal script:

```bash
cd ~/regardedpal
source .venv/bin/activate
```

Create `hello.py`:

```python
#!/usr/bin/env python3
"""
RegardedPal - Hello World
Displays text on the Waveshare 2.13" e-Paper V3.
"""

import sys
import os
import time

# Add the Waveshare library to the Python path
libdir = os.path.expanduser('~/e-Paper/RaspberryPi_JetsonNano/python/lib')
sys.path.append(libdir)

from waveshare_epd import epd2in13_V3
from PIL import Image, ImageDraw, ImageFont

def main():
    # Initialize the display
    epd = epd2in13_V3.EPD()
    epd.init()

    # Clear the display (full white)
    print("Clearing display...")
    epd.Clear(0xFF)

    # Create a new blank image
    # Note: width=122, height=250 in the driver, but we create the image
    # as (250, 122) for landscape orientation
    image = Image.new('1', (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)

    # Load default font
    font = ImageFont.load_default()

    # Draw a border
    draw.rectangle([(0, 0), (epd.height - 1, epd.width - 1)], outline=0)

    # Draw text
    draw.text((10, 10), 'Hello, World!', font=font, fill=0)
    draw.text((10, 30), 'RegardedPal v0.1', font=font, fill=0)
    draw.text((10, 50), 'e-Paper is working!', font=font, fill=0)

    # Send the image to the display
    print("Updating display...")
    epd.display(epd.getbuffer(image))

    # Wait a moment, then put the display to sleep
    time.sleep(2)

    print("Putting display to sleep...")
    epd.sleep()
    print("Done.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        epd2in13_V3.epdconfig.module_exit(cleanup=True)
        sys.exit(0)
```

Run it:

```bash
sudo python3 hello.py
```

You should see "Hello, World!" and "RegardedPal v0.1" on the e-ink display.

### 7.3 Understanding the Code

**Key concepts:**

1. **`epd.init()`** -- Initializes the display controller (sends reset pulse, configuration registers, LUT tables). Must be called before any display operation.

2. **`epd.Clear(0xFF)`** -- Fills the entire display with white (0xFF). Use `0x00` for all black. This performs a full refresh.

3. **`Image.new('1', (width, height), 255)`** -- Creates a 1-bit (black and white) PIL image.
   - `'1'` = 1-bit mode. Each pixel is either 0 (black) or 255 (white).
   - The dimensions are `(epd.height, epd.width)` = `(250, 122)` because the display is natively portrait but the driver handles rotation.

4. **`ImageDraw.Draw(image)`** -- Gives you a drawing context to add text, shapes, lines.

5. **`epd.getbuffer(image)`** -- Converts the PIL image into the byte format the SSD1680 controller expects (1 bit per pixel, packed into bytes).

6. **`epd.display(buffer)`** -- Sends the buffer to the display and triggers a full refresh (~3 seconds).

7. **`epd.sleep()`** -- Puts the controller into deep sleep mode (~1 uA). **Always call this when you are done.** Leaving the display in an active state can damage the panel over time.

### 7.4 Custom Fonts

The default font is tiny. Use TrueType fonts for better text:

```python
# Use the font bundled with the Waveshare demos
picdir = os.path.expanduser('~/e-Paper/RaspberryPi_JetsonNano/python/pic')
font_large = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
font_medium = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 16)
font_small = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 12)

draw.text((10, 10), 'Big Text', font=font_large, fill=0)
draw.text((10, 40), 'Medium text', font=font_medium, fill=0)
draw.text((10, 60), 'Small text', font=font_small, fill=0)
```

You can also install and use any `.ttf` font file:

```bash
# Install some common fonts
sudo apt install -y fonts-dejavu-core

# Use in Python
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
```

### 7.5 Drawing Shapes

```python
# Line
draw.line([(0, 0), (249, 121)], fill=0, width=1)

# Rectangle (outline)
draw.rectangle([(10, 10), (100, 50)], outline=0)

# Rectangle (filled)
draw.rectangle([(110, 10), (200, 50)], fill=0)

# Circle / Ellipse
draw.ellipse([(10, 60), (50, 100)], outline=0)

# Filled circle
draw.ellipse([(60, 60), (100, 100)], fill=0)

# Polygon
draw.polygon([(150, 60), (175, 100), (125, 100)], outline=0)

# Arc
draw.arc([(200, 60), (240, 100)], start=0, end=180, fill=0)
```

### 7.6 Displaying Images

```python
# Load a bitmap image and resize to fit the display
bmp = Image.open('my_sprite.bmp')
bmp = bmp.resize((epd.height, epd.width))  # resize to 250x122
bmp = bmp.convert('1')  # convert to 1-bit black and white

epd.display(epd.getbuffer(bmp))
```

For best results with e-ink:
- Use high-contrast black and white images
- Avoid complex gradients (dithering on 1-bit looks noisy)
- Design sprites as actual 1-bit pixel art for clean rendering

### 7.7 Partial Refresh (Fast Updates)

Partial refresh updates only a portion of the screen in ~0.3 seconds instead of a full ~3 second refresh. Ideal for updating stats, time, or animations.

```python
# Step 1: Set the base image (this does a full refresh)
epd.displayPartBaseImage(epd.getbuffer(image))

# Step 2: Make changes to the image and do a partial refresh
draw.rectangle((100, 50, 240, 80), fill=255)   # clear a region
draw.text((100, 50), 'Updated!', font=font, fill=0)
epd.displayPartial(epd.getbuffer(image))

# You can call displayPartial() repeatedly for fast updates
# But do a full refresh every 5-10 partial refreshes to prevent ghosting
```

**Important notes on partial refresh:**
- Call `epd.displayPartBaseImage()` once to establish the base image
- Then call `epd.displayPartial()` for subsequent fast updates
- After many partial refreshes, call `epd.init()` then `epd.display()` for a full refresh to clear ghost artifacts
- Partial refresh works best at room temperature (20-30 C)
- Waveshare recommends at least 180 seconds between full refreshes

---

## 8. Wire the Buttons

### 8.1 Breadboard Wiring Diagram

Since the HAT is seated on the Pi's GPIO header, you cannot directly access the pins. To wire buttons, you have two options:

**Option A: Use a GPIO breakout cable**

A 40-pin ribbon cable with a T-cobbler breakout board. Plug one end into the Pi header (before attaching the HAT), route the cable out, and use the breakout on a breadboard. The HAT then sits on top or beside.

**Option B: Solder wires to the HAT's pass-through header**

Some HATs pass through all 40 pins on top. If yours does, you can plug jumper wires into the top of the HAT. Check if your Waveshare HAT has a top-side header.

**Option C (simplest for prototyping): Use the HAT's unused pins**

The HAT connects to the Pi's full 40-pin header but only uses ~9 pins. The remaining pins are physically accessible through the HAT's header. Use female-to-male jumper wires from the HAT's top header to the breadboard.

**Button wiring (per button):**

```
Pi GPIO Pin (e.g., GPIO 5)
    |
    |---- jumper wire ---> breadboard row A
                               |
                           [button] (spans center channel)
                               |
                           breadboard row B
                               |
    |---- jumper wire ---> GND (any ground pin)
```

No external resistors needed -- we use the Pi's internal pull-up resistors in software.

**Pin assignments:**

| Button | GPIO | Physical Pin |
|--------|------|-------------|
| UP | GPIO 5 | 29 |
| DOWN | GPIO 6 | 31 |
| LEFT | GPIO 13 | 33 |
| RIGHT | GPIO 19 | 35 |
| SELECT | GPIO 26 | 37 |
| GND (shared) | GND | 30, 34, or 39 |

These pins are chosen because they are on the bottom-right of the header (physical pins 29-39), making them easy to access and wire, and they don't conflict with SPI, I2C, or UART.

### 8.2 Button Test Script

Create `button_test.py`:

```python
#!/usr/bin/env python3
"""
RegardedPal - Button Test
Tests all 5 buttons and prints which one is pressed.
"""

from gpiozero import Button
from signal import pause

# Pin assignments
buttons = {
    'UP':     Button(5,  pull_up=True, bounce_time=0.05),
    'DOWN':   Button(6,  pull_up=True, bounce_time=0.05),
    'LEFT':   Button(13, pull_up=True, bounce_time=0.05),
    'RIGHT':  Button(19, pull_up=True, bounce_time=0.05),
    'SELECT': Button(26, pull_up=True, bounce_time=0.05),
}

for name, btn in buttons.items():
    btn.when_pressed = lambda n=name: print(f"[PRESSED]  {n}")
    btn.when_released = lambda n=name: print(f"[RELEASED] {n}")

print("Button test running. Press buttons to test. Ctrl+C to exit.")
print("Pins: UP=5, DOWN=6, LEFT=13, RIGHT=19, SELECT=26")
pause()
```

Run it:

```bash
sudo python3 button_test.py
```

Press each button -- you should see the corresponding name printed. If a button does not register, check your wiring.

### 8.3 Debouncing

Mechanical buttons "bounce" -- they make and break contact several times within a few milliseconds when pressed. This can cause multiple events from a single press.

**Software debounce (built into gpiozero):**

The `bounce_time=0.05` parameter (50ms) in the Button constructor handles this. It ignores additional edges within 50ms of the first edge. This is sufficient for most tactile buttons.

**If you need more control with RPi.GPIO:**

```python
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.add_event_detect(5, GPIO.FALLING, callback=my_callback, bouncetime=50)
```

**Hardware debounce (optional):**

For the cleanest signal, add a 100nF ceramic capacitor between the GPIO pin and GND at each button. This is rarely necessary for a project like this.

---

## 9. Development Workflow

### 9.1 Local Edit + rsync + SSH (Recommended)

The Pi Zero's single-core ARMv6 CPU makes on-device editing slow. The best workflow is to edit code on your development machine and sync to the Pi:

**On your development machine:**

```bash
# Sync your project to the Pi
rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '.git' \
    ~/COdingProjects/regardedPal/src/ pi@regardedpal.local:~/regardedpal/

# SSH in and run
ssh pi@regardedpal.local "cd ~/regardedpal && source .venv/bin/activate && sudo python3 main.py"
```

**Or use scp for a single file:**

```bash
scp hello.py pi@regardedpal.local:~/regardedpal/
```

### 9.2 VS Code Remote-SSH (Pi Zero 2 W Only)

**This does NOT work on the original Pi Zero WH** (ARMv6). The VS Code server requires ARMv7+.

If you have a **Pi Zero 2 W** (ARMv8), install the "Remote - SSH" extension in VS Code, add the Pi as a host, and connect. VS Code installs its server component automatically.

**Workaround for Pi Zero WH:** Use the rsync workflow above. VS Code on your local machine is still your editor -- you just sync files manually.

### 9.3 Remote Debugging with debugpy

Even without VS Code Remote-SSH, you can use remote attach debugging:

**On the Pi**, install debugpy:

```bash
source ~/regardedpal/.venv/bin/activate
pip install debugpy
```

**Add to your script (at the top of main):**

```python
import debugpy
debugpy.listen(("0.0.0.0", 5678))
print("Waiting for debugger to attach...")
debugpy.wait_for_client()
print("Debugger attached.")
```

**In VS Code on your dev machine**, create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Attach to Pi",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "regardedpal.local",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}/src",
                    "remoteRoot": "/home/pi/regardedpal"
                }
            ]
        }
    ]
}
```

Run the script on the Pi (`sudo python3 main.py`), then attach from VS Code. You get breakpoints, variable inspection, and the full debugging experience.

### 9.4 Makefile for Common Tasks

Create a `Makefile` in your project root:

```makefile
REMOTE = pi@regardedpal.local
REMOTE_DIR = ~/regardedpal

.PHONY: deploy run ssh test clean

deploy:
	rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '.git' \
		./src/ $(REMOTE):$(REMOTE_DIR)/

run: deploy
	ssh $(REMOTE) "cd $(REMOTE_DIR) && source .venv/bin/activate && sudo python3 main.py"

ssh:
	ssh $(REMOTE)

test: deploy
	ssh $(REMOTE) "cd $(REMOTE_DIR) && source .venv/bin/activate && python3 -m pytest tests/"

clean:
	ssh $(REMOTE) "cd $(REMOTE_DIR) && find . -name '__pycache__' -exec rm -rf {} + 2>/dev/null; true"
```

Usage:

```bash
make deploy    # sync code to Pi
make run       # sync and run
make ssh       # open SSH session
```

---

## 10. Project Structure

Recommended layout for the RegardedPal project on the Pi:

```
~/regardedpal/
├── main.py                 # Entry point
├── config.py               # Pin assignments and constants
├── hardware/
│   ├── __init__.py
│   ├── display.py          # e-Paper display abstraction
│   └── buttons.py          # Button input abstraction
├── game/
│   ├── __init__.py
│   ├── pet.py              # Pet state and logic
│   ├── renderer.py         # Draws pet and UI to PIL images
│   └── loop.py             # Main game loop
└── assets/
    ├── fonts/              # .ttf font files
    └── sprites/            # .bmp sprite files
```

**Key principle:** Separate hardware interaction (display, buttons) from game logic (pet state, rendering). This lets you test game logic on your dev machine without a Pi.

---

## 11. Run at Boot (systemd)

When your project is ready to run automatically on power-on:

Create `/etc/systemd/system/regardedpal.service`:

```ini
[Unit]
Description=RegardedPal Virtual Pet
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/pi/regardedpal
ExecStart=/home/pi/regardedpal/.venv/bin/python -u main.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Note:** `User=root` is needed because GPIO/SPI access requires root on most configurations. Alternatively, set up udev rules for non-root access (see Section 12.3).

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable regardedpal.service
sudo systemctl start regardedpal.service

# Check status
sudo systemctl status regardedpal.service

# View logs
journalctl -u regardedpal.service -f
```

---

## 12. Debugging & Troubleshooting

### 12.1 Display Not Refreshing

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Display stays blank after running script | Wrong driver version | Verify you are importing `epd2in13_V3`, not V1/V2/V4 |
| Script hangs with no output | BUSY pin stuck HIGH | Check HAT is fully seated on the GPIO header |
| Garbled/corrupted image | SPI data corruption | Reduce SPI clock: edit `epdconfig.py`, change `4000000` to `2000000` |
| Display flashes but shows nothing | Image is all white | Check your `fill=0` (black) vs `fill=255` (white) |
| Script errors on `epd.init()` | SPI not enabled | Run `ls /dev/spidev*` to verify (see Section 4.2) |

**Hard reset procedure:**
1. `sudo shutdown -h now`
2. Disconnect power
3. Remove and reseat the HAT
4. Wait 10 seconds
5. Reconnect power and try again

### 12.2 SPI Not Detected

```bash
# Check if SPI devices exist
ls /dev/spidev*
# Should show: /dev/spidev0.0  /dev/spidev0.1

# Check kernel module
lsmod | grep spi
# Should show: spi_bcm2835

# Check config
grep spi /boot/firmware/config.txt
# Should show: dtparam=spi=on

# If missing, enable it:
sudo raspi-config nonint do_spi 0
sudo reboot
```

### 12.3 Permission Errors

If you get `PermissionError` or `RuntimeError: No access to /dev/mem`:

**Quick fix:** Run with `sudo`:
```bash
sudo python3 hello.py
```

**Proper fix:** Add your user to the required groups:
```bash
sudo usermod -aG spi,gpio,i2c pi
# Log out and log back in (or reboot)
```

**Alternative:** Create udev rules for non-root GPIO/SPI access:

```bash
# Create /etc/udev/rules.d/99-gpio-spi.rules:
echo 'SUBSYSTEM=="spidev", GROUP="spi", MODE="0660"' | sudo tee /etc/udev/rules.d/99-gpio-spi.rules
echo 'SUBSYSTEM=="gpio", GROUP="gpio", MODE="0660"' | sudo tee -a /etc/udev/rules.d/99-gpio-spi.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 12.4 Ghost Images / Burn-in

E-ink displays can show "ghost" remnants of previous images. This is normal and manageable:

- **Prevention:** Perform a full refresh (`epd.init()` + `epd.display()`) every 5-10 partial refreshes
- **Clearing ghosts:** Run several full-refresh cycles alternating all-white and all-black:
  ```python
  for _ in range(3):
      epd.Clear(0x00)  # all black
      time.sleep(2)
      epd.Clear(0xFF)  # all white
      time.sleep(2)
  ```
- **Always call `epd.sleep()`** when finished to prevent panel damage
- **Temperature matters:** Partial refresh is less reliable below 10 C or above 40 C
- **Never leave a static image indefinitely** without periodic refresh

### 12.5 GPIO / Button Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Button always reads pressed | Wired to wrong pins (e.g., 3.3V instead of GND) | Check wiring: button should connect GPIO to GND |
| Button never registers | Wrong GPIO number | Verify BCM number vs physical pin number |
| Multiple presses from one tap | Bouncing | Increase `bounce_time` to 0.1 (100ms) |
| `gpiozero` error about pin factory | lgpio not installed or permission denied | Install `python3-lgpio` or run with sudo |

### 12.6 GPIO Testing Tools

Useful command-line tools for debugging GPIO:

```bash
# Show the Pi's GPIO pinout in the terminal
pinout

# List all GPIO lines and their current state
gpioinfo

# Read a specific GPIO pin (e.g., GPIO 5)
gpioget gpiochip0 5

# Monitor a GPIO pin for changes (press Ctrl+C to stop)
gpiomon gpiochip0 5

# Set a GPIO pin (e.g., for testing an LED)
gpioset gpiochip0 27=1
```

---

## 13. Reference Links

### Official Documentation
- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
- [Raspberry Pi GPIO Pinout](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header)
- [Raspberry Pi config.txt Reference](https://www.raspberrypi.com/documentation/computers/config_txt.html)

### Waveshare Display
- [Waveshare 2.13" e-Paper HAT Wiki](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT)
- [Waveshare 2.13" e-Paper HAT Manual](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT_Manual)
- [Waveshare V3 Specification PDF](https://files.waveshare.com/upload/5/59/2.13inch_e-Paper_V3_Specificition.pdf)
- [Waveshare e-Paper GitHub Repository](https://github.com/waveshareteam/e-Paper)
- [SSD1680 Datasheet (Orient Display)](https://www.orientdisplay.com/wp-content/uploads/2022/08/SSD1680_v0.14.pdf)

### Python Libraries
- [Pillow (PIL) Documentation](https://pillow.readthedocs.io/)
- [gpiozero Documentation](https://gpiozero.readthedocs.io/)
- [RPi.GPIO Documentation](https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/)
- [spidev Documentation](https://pypi.org/project/spidev/)

### Development Tools
- [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
- [VS Code Remote-SSH](https://code.visualstudio.com/docs/remote/ssh)
- [debugpy (Python Debugger)](https://github.com/microsoft/debugpy)
