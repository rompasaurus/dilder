# Pi Zero Setup

How to flash Raspberry Pi OS, configure headless access, and prepare the Pi Zero for Dilder development.

For the complete setup guide including display wiring and development environment, see the full [docs/setup-guide.md](https://github.com/rompasaurus/dilder/blob/main/docs/setup-guide.md) in the repo.

---

## What You Need

- Raspberry Pi Zero WH (or Zero 2 WH)
- Micro SD card (16GB+, Class 10)
- A computer with an SD card reader
- Same Wi-Fi network as your development machine

---

## Step 1 — Flash Raspberry Pi OS

### Download Raspberry Pi Imager

[raspberrypi.com/software](https://www.raspberrypi.com/software/)

Available for macOS, Windows, and Linux.

### Choose the Right Image

Open Imager → **Raspberry Pi OS (other)** → **Raspberry Pi OS Lite (32-bit)**

!!! info "Why Lite?"
    No desktop. Saves ~1GB, boots faster, uses less RAM. You don't need a GUI — everything is done over SSH.

### Configure Headless Settings

Before writing, click the **gear icon** (or press `Ctrl+Shift+X`) to open the advanced settings:

| Setting | Value |
|---------|-------|
| Set hostname | `dilder.local` |
| Enable SSH | ✅ (Use password authentication initially) |
| Set username | `pi` (or your preferred name) |
| Set password | Choose something secure |
| Configure Wi-Fi | ✅ Enter your SSID and password |
| Wi-Fi country | Your country code (e.g., `DE`, `GB`, `US`) |

### Write the Image

Select your SD card → **Write**. Takes 2–5 minutes.

---

## Step 2 — First Boot and SSH

1. Insert the SD card into the Pi Zero
2. Connect power via micro-USB
3. Wait ~60–90 seconds for first boot

### Find the Pi on Your Network

```bash
# macOS/Linux
ping dilder.local

# If that fails, check your router's DHCP client list
# Or use nmap to scan your local network
nmap -sn 192.168.1.0/24 | grep -A 2 "Raspberry"
```

### Connect via SSH

```bash
ssh pi@dilder.local
```

Accept the host key fingerprint on first connect.

### Set Up SSH Keys (Recommended)

Passwordless login speeds up your development workflow significantly:

```bash
# On your local machine
ssh-copy-id pi@dilder.local

# Verify it works
ssh pi@dilder.local  # should not ask for password
```

---

## Step 3 — System Configuration

### Update the System

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt autoremove -y
```

This takes 5–10 minutes on a Pi Zero. Do it once after first boot.

### Enable SPI

The e-ink display uses SPI. It must be enabled before the display will work.

```bash
sudo raspi-config
```

Navigate to: **Interface Options** → **SPI** → **Yes** → **OK**

Then reboot:

```bash
sudo reboot
```

### Verify SPI Is Active

After reboot, reconnect via SSH and check:

```bash
ls /dev/spi*
# Expected output: /dev/spidev0.0  /dev/spidev0.1
```

If you see those devices, SPI is working.

### Set Timezone

```bash
sudo raspi-config
# Localisation Options → Timezone → select your region
```

---

## Step 4 — Install Dependencies

```bash
# Python and SPI tools
sudo apt install -y python3-pip python3-venv python3-dev git
sudo apt install -y python3-pil python3-numpy

# SPI library
sudo apt install -y python3-spidev python3-rpi.gpio
```

### Create a Virtual Environment

```bash
mkdir ~/dilder && cd ~/dilder
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install RPi.GPIO spidev Pillow
```

---

## Next Steps

- [Display Setup](display-setup.md) — attach the HAT and get pixels on screen
- [Dev Environment](dev-environment.md) — configure your local machine for remote development
