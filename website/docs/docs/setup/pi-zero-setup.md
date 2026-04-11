# Pico W Setup

How to flash MicroPython firmware onto the Raspberry Pi Pico W and verify it's working.

---

## What You Need

- Raspberry Pi Pico W (or Pico WH)
- Micro-USB cable that supports **data** (not just charging)
- A Linux computer (this guide targets Linux — macOS/Windows steps are similar)

---

## Step 1 — Download MicroPython Firmware

Go to the official MicroPython downloads page and grab the latest stable `.uf2` file for the Pico W:

[micropython.org/download/RPI_PICO_W](https://micropython.org/download/RPI_PICO_W/)

!!! info "Why MicroPython?"
    MicroPython runs directly on the RP2040 with no OS. It gives us a Python REPL, filesystem on flash, and hardware access — all with instant boot. Perfect for prototyping a display + button project.

---

## Step 2 — Flash the Firmware

### Enter BOOTSEL Mode

1. **Hold the BOOTSEL button** on the Pico W (the small white button on the board)
2. While holding it, **plug the USB cable** into the Pico W and your computer
3. **Release BOOTSEL** — the Pico appears as a USB mass storage drive named `RPI-RP2`

### Copy the Firmware

```bash
# The drive typically mounts at /run/media/<user>/RPI-RP2 or /media/<user>/RPI-RP2
# Copy the UF2 file to it
cp ~/Downloads/RPI_PICO_W-*.uf2 /run/media/$USER/RPI-RP2/

# The Pico reboots automatically — the drive disappears
# This is normal. The firmware is now installed.
```

Or just drag and drop the `.uf2` file in your file manager.

---

## Step 3 — Verify MicroPython Is Running

After flashing, the Pico W reboots and appears as a serial device.

### Find the Serial Port

```bash
ls /dev/ttyACM*
# Expected: /dev/ttyACM0
```

If you don't see it, check:

- Is the USB cable a data cable? Charge-only cables won't work.
- Does your user have permission? Add yourself to the `dialout` group:

```bash
sudo usermod -aG dialout $USER
# Log out and back in for this to take effect
```

### Connect to the REPL

```bash
# Option 1: screen
screen /dev/ttyACM0 115200

# Option 2: minicom
minicom -D /dev/ttyACM0 -b 115200

# Option 3: picocom
picocom /dev/ttyACM0 -b 115200
```

Press **Enter** and you should see the MicroPython prompt:

```
MicroPython v1.x.x on 2026-xx-xx; Raspberry Pi Pico W with RP2040
Type "help()" for more information.
>>>
```

### Quick Smoke Test

```python
>>> import machine
>>> led = machine.Pin("LED", machine.Pin.OUT)
>>> led.on()    # onboard LED turns on
>>> led.off()   # onboard LED turns off
>>> print("Pico W is alive!")
Pico W is alive!
```

!!! tip "Exit screen"
    Press `Ctrl+A` then `K` then `Y` to exit `screen`. For minicom: `Ctrl+A` then `X`.

---

## Step 4 — Test Wi-Fi (Optional)

The Pico W has onboard Wi-Fi. Verify it can connect to your network:

```python
>>> import network
>>> wlan = network.WLAN(network.STA_IF)
>>> wlan.active(True)
>>> wlan.connect("YOUR_SSID", "YOUR_PASSWORD")
>>> # Wait a few seconds
>>> wlan.isconnected()
True
>>> wlan.ifconfig()
('192.168.1.xxx', '255.255.255.0', '192.168.1.1', '8.8.8.8')
```

Wi-Fi isn't required for the display prototype, but it's useful to confirm the wireless chip works.

---

## Step 5 — Understand the Filesystem

MicroPython provides a small filesystem on the Pico W's 2MB flash. Key files:

| File | Purpose |
|------|---------|
| `boot.py` | Runs on power-up before anything else. Use for Wi-Fi setup. |
| `main.py` | Runs automatically after `boot.py`. Put your application here. |
| Other `.py` files | Imported as modules. Upload your libraries here. |

```python
>>> import os
>>> os.listdir('/')
['boot.py']
```

Files are uploaded from your dev machine using the MicroPico VSCode extension (see [Dev Environment](dev-environment.md)).

---

## Next Steps

- [Display Setup](display-setup.md) — wire the e-ink display and get pixels on screen
- [Dev Environment](dev-environment.md) — set up VSCode with MicroPico for development and debugging
