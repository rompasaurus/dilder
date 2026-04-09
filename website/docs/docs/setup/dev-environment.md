# Dev Environment

How to set up your local machine for editing code and deploying it to the Pi Zero efficiently.

---

## The Problem

You can't comfortably edit code directly on the Pi Zero — no GUI, small RAM, slow SD card I/O. The standard solution is to edit on your local machine and push changes to the Pi for execution.

---

## Option A — rsync + SSH (Recommended)

Edit locally, sync to Pi, run on Pi. Simple, works with any editor, no VS Code dependency.

### Workflow

1. Edit files on your local machine
2. `rsync` the changed files to the Pi
3. SSH in and run the script

### Setup

On your local machine, add this to your shell profile or create a `Makefile`:

```bash
# Sync the project to the Pi
alias dilder-sync='rsync -avz --exclude=".git" --exclude="venv" \
    ~/code/dilder/ pi@dilder.local:~/dilder/'

# SSH shortcut
alias dilder='ssh pi@dilder.local'
```

### Example Makefile

```makefile
# ~/code/dilder/Makefile

REMOTE = pi@dilder.local
REMOTE_DIR = ~/dilder

.PHONY: sync run watch

sync:
    rsync -avz --exclude=".git" --exclude="venv" ./ $(REMOTE):$(REMOTE_DIR)/

run: sync
    ssh $(REMOTE) "cd $(REMOTE_DIR) && source venv/bin/activate && python3 main.py"

watch:
    # Requires: brew install fswatch  (macOS)
    fswatch -o src/ | xargs -n1 -I{} make sync
```

Run with:

```bash
make run       # sync and run
make watch     # auto-sync on file change
```

---

## Option B — VS Code Remote-SSH

Full IDE experience directly on the Pi. Works best with the **Pi Zero 2 W** — the original Pi Zero W may be too slow for VS Code's language server.

### Setup

1. Install the **Remote - SSH** extension in VS Code
2. Open Command Palette → **Remote-SSH: Connect to Host**
3. Enter `pi@dilder.local`
4. Open the `~/dilder` folder on the remote

You can now edit files, use the integrated terminal, and run scripts — all executing on the Pi.

!!! warning "Pi Zero W performance"
    The original Pi Zero W (single-core, 512MB) is borderline for VS Code Remote-SSH. Expect slow IntelliSense and occasional timeouts. The rsync workflow is more reliable on the Zero W. The Zero 2 W handles it fine.

---

## Option C — Remote Debugging with debugpy

Run your script on the Pi with a debugger attached, and connect VS Code's debugger from your local machine.

### On the Pi

```bash
pip install debugpy

# Start your script with debugpy listening on port 5678
python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client main.py
```

### In VS Code (local machine)

Add to `.vscode/launch.json`:

```json
{
    "type": "python",
    "request": "attach",
    "name": "Attach to Pi",
    "host": "dilder.local",
    "port": 5678,
    "pathMappings": [{
        "localRoot": "${workspaceFolder}",
        "remoteRoot": "/home/pi/dilder"
    }]
}
```

Press **F5** to connect. You can now set breakpoints locally that trigger on the Pi.

---

## Run at Boot (systemd)

When development is done, run Dilder automatically on boot:

```bash
# Create a service file
sudo nano /etc/systemd/system/dilder.service
```

```ini
[Unit]
Description=Dilder virtual pet
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/dilder
ExecStart=/home/pi/dilder/venv/bin/python3 /home/pi/dilder/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable dilder
sudo systemctl start dilder
sudo systemctl status dilder
```

---

## Useful SSH Aliases

```bash
# Add to ~/.ssh/config on your local machine
Host dilder
    HostName dilder.local
    User pi
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

Then you can just `ssh dilder` instead of `ssh pi@dilder.local`.
