# Dev Environment

How to set up VSCode on Linux for Pico W development, debugging, and file management.

---

## Overview

The Pico W is a microcontroller, not a Linux computer — you can't SSH into it or run an editor on it. Instead, you edit code on your local machine and upload it to the Pico W over USB.

The recommended workflow:

1. **Edit** code in VSCode on your Linux machine
2. **Upload** files to the Pico W via the MicroPico extension
3. **Run** and **debug** directly from VSCode using the serial REPL

---

## Step 1 — Install VSCode

If you don't already have VSCode installed:

```bash
# Arch Linux / CachyOS
sudo pacman -S code

# Ubuntu / Debian
sudo apt install code

# Or download from https://code.visualstudio.com/
```

---

## Step 2 — Install the MicroPico Extension

MicroPico (formerly Pico-W-Go) provides:

- File upload/download to/from the Pico W
- Integrated MicroPython REPL terminal
- Run scripts directly on the Pico W
- Auto-completion for MicroPython APIs
- Pico W project management

### Install

1. Open VSCode
2. Go to **Extensions** (`Ctrl+Shift+X`)
3. Search for **"MicroPico"**
4. Install the extension by **paulober**

### Configure

After installing, set your project as a MicroPico project:

1. Open your Dilder project folder in VSCode
2. Open the Command Palette (`Ctrl+Shift+P`)
3. Run **MicroPico: Configure Project**
4. This creates a `.micropico` file in your project root

---

## Step 3 — Serial Port Permissions (Linux)

The Pico W appears as `/dev/ttyACM0` when connected. Your user needs permission to access it.

```bash
# Add your user to the dialout group
sudo usermod -aG dialout $USER

# Log out and back in for the change to take effect
# Verify:
groups | grep dialout
```

!!! warning "Common gotcha"
    If MicroPico can't connect, this is almost always the cause. The group change only takes effect after a full logout/login (not just a new terminal).

---

## Step 4 — Connect to the Pico W

1. Plug the Pico W into your computer via USB
2. In VSCode, the MicroPico status bar should show **"Pico Connected"** at the bottom
3. If not, open Command Palette → **MicroPico: Connect**

### Open the REPL

- Click the **MicroPico terminal icon** in the bottom panel, or
- Command Palette → **MicroPico: Toggle REPL**

You should see the MicroPython `>>>` prompt in the VSCode terminal.

---

## Step 5 — Project Structure

Create this structure in your project for the firmware:

```
dilder/
├── firmware/              # MicroPython code for the Pico W
│   ├── main.py            # Entry point (runs on boot)
│   ├── boot.py            # Pre-boot config (Wi-Fi, etc.)
│   ├── epd2in13_V3.py     # Waveshare display driver
│   ├── epdconfig.py       # SPI/GPIO config for driver
│   ├── core/
│   │   ├── display.py     # Display wrapper
│   │   └── input.py       # Button input handler
│   └── assets/
│       └── sprites/       # 1-bit images
├── website/               # MkDocs site (existing)
├── docs/                  # Research docs (existing)
└── .micropico             # MicroPico config
```

### Upload Files to Pico W

- **Upload a single file:** Right-click the file in the explorer → **MicroPico: Upload File to Pico**
- **Upload the entire project:** Command Palette → **MicroPico: Upload Project to Pico**
- **Download from Pico:** Command Palette → **MicroPico: Download Project from Pico**

---

## Step 6 — Running Code

### Run the Current File

1. Open a `.py` file in the editor
2. Click the **Run** button in the MicroPico status bar, or
3. Command Palette → **MicroPico: Run Current File on Pico**

The script runs on the Pico W and output appears in the REPL terminal.

### Run on Boot

Any code in `main.py` on the Pico W runs automatically when it powers on. Upload your `main.py` and reset the board to test auto-start behavior.

```python
# Reset the Pico W from REPL
>>> import machine
>>> machine.reset()
```

---

## Step 7 — Debugging

### REPL Debugging

The simplest approach: use `print()` statements and the REPL.

```python
# In your code
print(f"Button state: {btn.value()}")
print(f"Display BUSY: {busy_pin.value()}")
```

### Interactive Debugging

You can paste code directly into the REPL to test hardware interactively:

```python
>>> from machine import Pin, SPI
>>> spi = SPI(1, baudrate=4_000_000, sck=Pin(10), mosi=Pin(11))
>>> cs = Pin(9, Pin.OUT, value=1)
>>> cs.value(0)  # select display
>>> spi.write(b'\x00')  # send a test byte
>>> cs.value(1)  # deselect
```

### mpremote (CLI Alternative)

`mpremote` is a command-line tool for managing MicroPython devices. Useful when you want to script uploads or run files without VSCode.

```bash
# Install
pip install mpremote

# List connected devices
mpremote connect list

# Run a file on the Pico W (without uploading)
mpremote run firmware/hello_display.py

# Upload a file
mpremote cp firmware/main.py :main.py

# Upload a directory
mpremote cp -r firmware/ :

# Open the REPL
mpremote repl

# Reset the board
mpremote reset
```

---

## Useful VSCode Settings

Add to your `.vscode/settings.json`:

```json
{
    "micropico.syncFolder": "firmware",
    "micropico.openOnStart": true,
    "python.languageServer": "Pylance",
    "python.analysis.extraPaths": [
        "firmware"
    ],
    "files.associations": {
        "*.py": "python"
    }
}
```

This tells MicroPico to sync only the `firmware/` folder to the Pico W, and gives Pylance the right paths for autocomplete.

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Toggle REPL | `Ctrl+Shift+P` → "MicroPico: Toggle REPL" |
| Run current file | Click status bar **Run** button |
| Upload file | Right-click → "Upload File to Pico" |
| Upload project | `Ctrl+Shift+P` → "MicroPico: Upload Project" |
| Soft reset | Type `Ctrl+D` in the REPL |
| Interrupt running code | Type `Ctrl+C` in the REPL |

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| MicroPico shows "No Pico connected" | USB cable plugged in? Data cable (not charge-only)? Check `ls /dev/ttyACM*` |
| Permission denied on `/dev/ttyACM0` | Add user to `dialout` group, then log out and back in |
| REPL unresponsive | Press `Ctrl+C` to interrupt running code, or `Ctrl+D` to soft-reset |
| Upload fails | Close any other serial connections (screen, minicom) — only one program can use the serial port |
| MicroPython autocomplete not working | Install the `micropython-stubs` package and configure `python.analysis.extraPaths` |
| File not found on Pico after upload | Check `micropico.syncFolder` setting — it may be uploading from the wrong directory |
