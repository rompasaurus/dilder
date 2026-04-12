#!/usr/bin/env python3
"""
Dilder DevTool — Pico W Development Companion

Tkinter GUI for developing on the Pico W + Waveshare 2.13" e-ink display.

Features:
  - E-ink display emulator (250x122, 1-bit) with drawing and text tools
  - Serial monitor for live printf output from the Pico W
  - Firmware flash utility (BOOTSEL detection + UF2 copy)
  - Asset manager (save/load/preview 1-bit bitmaps)
  - GPIO pin state viewer

Usage:
  python3 DevTool/devtool.py
"""

import io
import json
import os
import platform
import random
import re
import shutil
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path
from datetime import datetime

# ── Dependency gate ─────────────────────────────────────────────────────────
# When run directly (python3 devtool.py), check for system packages before
# importing them. If missing, offer to install and re-exec.
# When imported as a module (e.g. by tests), skip the gate — the caller
# is responsible for ensuring deps are present.

def _check_and_install_deps():
    """Check for required system packages and offer to install them."""
    missing = []

    try:
        import tkinter as _tk  # noqa: F401
    except ImportError:
        missing.append(("tkinter", {"arch": "tk", "debian": "python3-tk", "fedora": "python3-tkinter"}))

    try:
        import serial as _ser  # noqa: F401
    except ImportError:
        missing.append(("pyserial", {"arch": "python-pyserial", "debian": "python3-serial", "fedora": "python3-pyserial"}))

    if not missing:
        return True

    # Detect distro
    distro = "unknown"
    try:
        with open("/etc/os-release") as f:
            content = f.read().lower()
        if "cachyos" in content or "arch" in content or "manjaro" in content:
            distro = "arch"
        elif "ubuntu" in content or "debian" in content or "mint" in content:
            distro = "debian"
        elif "fedora" in content or "rhel" in content or "centos" in content:
            distro = "fedora"
    except FileNotFoundError:
        pass

    names = [n for n, _ in missing]
    pkgs = [pkg_map.get(distro) for _, pkg_map in missing if pkg_map.get(distro)]

    print(f"\n  Missing dependencies: {', '.join(names)}")

    if not pkgs:
        print("  Unknown distro — install manually and re-run.")
        return False

    if distro == "arch":
        cmd = ["sudo", "pacman", "-S", "--needed"] + pkgs
    elif distro == "debian":
        cmd = ["sudo", "apt", "install", "-y"] + pkgs
    elif distro == "fedora":
        cmd = ["sudo", "dnf", "install", "-y"] + pkgs
    else:
        return False

    print(f"  Installing: {' '.join(pkgs)}")
    print(f"  $ {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("\n  Dependencies installed. Starting DevTool...\n")
        return True
    else:
        print(f"\n  Install failed. Run manually:")
        print(f"    {' '.join(cmd)}")
        return False


if __name__ == "__main__":
    # Check deps BEFORE the module-level class definitions execute.
    # If deps are missing and install succeeds, re-exec so the module
    # loads fresh with the new packages.
    _needs_install = False
    try:
        import tkinter as _tk_test  # noqa: F401
        import serial as _ser_test  # noqa: F401
    except ImportError:
        _needs_install = True

    if _needs_install:
        if _check_and_install_deps():
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            sys.exit(1)

# ── Now safe to import ──────────────────────────────────────────────────────

import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog, font as tkfont

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

APP_NAME = "Dilder DevTool"
APP_VERSION = "1.0.0"

# Display dimensions (Waveshare 2.13" V3)
DISPLAY_W = 250
DISPLAY_H = 122

# Scale factor for the emulator canvas
CANVAS_SCALE = 3

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
ASSETS_DIR = PROJECT_ROOT / "assets"
DEV_SETUP = PROJECT_ROOT / "dev-setup"

# Serial defaults
DEFAULT_BAUD = 115200
SERIAL_TIMEOUT = 0.1

# Colours for the UI
BG_DARK = "#1e1e2e"
BG_PANEL = "#282840"
BG_CANVAS = "#2a2a3a"
FG_TEXT = "#cdd6f4"
FG_DIM = "#6c7086"
FG_ACCENT = "#89b4fa"
FG_GREEN = "#a6e3a1"
FG_RED = "#f38ba8"
FG_YELLOW = "#f9e2af"
FG_MAGENTA = "#cba6f7"

# E-ink colours (on screen)
EINK_WHITE = "#e8e8e8"
EINK_BLACK = "#1a1a1a"


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def find_pico_serial():
    """Find the Pico W serial port.

    Checks all comports for ttyACM / usbmodem devices, or the Raspberry Pi
    USB vendor ID (2E8A).  Handles port number changes when switching USB
    ports (ttyACM0 → ttyACM1, etc.).
    """
    # First pass: match by Raspberry Pi Pico VID (0x2E8A)
    for port in serial.tools.list_ports.comports():
        if port.vid == 0x2E8A:
            return port.device
    # Second pass: match by device name pattern (broader)
    for port in serial.tools.list_ports.comports():
        if "ttyACM" in port.device or "usbmodem" in port.device:
            return port.device
    return None


def find_rpi_rp2_mount():
    """Find the RPI-RP2 USB drive for flashing."""
    user = os.environ.get("USER", "")
    paths = [
        Path(f"/run/media/{user}/RPI-RP2"),
        Path(f"/media/{user}/RPI-RP2"),
        Path("/mnt/RPI-RP2"),
    ]
    for p in paths:
        if p.exists() and p.is_dir():
            return p
    # Fallback: findmnt
    try:
        result = subprocess.run(
            ["findmnt", "-rno", "TARGET", "-S", "LABEL=RPI-RP2"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0 and result.stdout.strip():
            p = Path(result.stdout.strip().splitlines()[0])
            if p.exists():
                return p
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# E-Ink Display Emulator
# ─────────────────────────────────────────────────────────────────────────────

class DisplayEmulator(ttk.Frame):
    """
    250x122 pixel 1-bit e-ink display emulator with drawing tools.

    Tools: pencil, eraser, line, rectangle, filled rectangle, text
    Colours: black (draw) and white (erase) only — matches real e-ink.
    """

    TOOLS = ["pencil", "eraser", "line", "rectangle", "filled_rect", "text"]
    TOOL_LABELS = {
        "pencil": "Pencil",
        "eraser": "Eraser",
        "line": "Line",
        "rectangle": "Rect",
        "filled_rect": "Fill Rect",
        "text": "Text",
    }

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.scale = CANVAS_SCALE
        self.canvas_w = DISPLAY_W * self.scale
        self.canvas_h = DISPLAY_H * self.scale

        # Pixel buffer: 0 = white, 1 = black
        self.pixels = [[0] * DISPLAY_W for _ in range(DISPLAY_H)]

        self.current_tool = "pencil"
        self.brush_size = 1
        self.current_font_size = 16
        self.drag_start = None

        self._build_ui()
        self._clear_canvas()

    def _build_ui(self):
        # ── Toolbar ──
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=(5, 2))

        ttk.Label(toolbar, text="Tool:").pack(side=tk.LEFT, padx=(0, 5))

        self.tool_var = tk.StringVar(value="pencil")
        for tool_key in self.TOOLS:
            rb = ttk.Radiobutton(
                toolbar, text=self.TOOL_LABELS[tool_key],
                variable=self.tool_var, value=tool_key,
                command=self._on_tool_change
            )
            rb.pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

        ttk.Label(toolbar, text="Size:").pack(side=tk.LEFT, padx=(0, 3))
        self.size_var = tk.IntVar(value=1)
        size_spin = ttk.Spinbox(toolbar, from_=1, to=10, width=3,
                                textvariable=self.size_var)
        size_spin.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(toolbar, text="Font:").pack(side=tk.LEFT, padx=(0, 3))
        self.font_size_var = tk.IntVar(value=16)
        font_spin = ttk.Spinbox(toolbar, from_=8, to=48, width=3,
                                textvariable=self.font_size_var)
        font_spin.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

        ttk.Button(toolbar, text="Clear", command=self._clear_canvas).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Invert", command=self._invert_canvas).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save", command=self._save_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Load", command=self._load_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Send to Pico", command=self._send_to_pico).pack(side=tk.LEFT, padx=2)

        # ── Canvas ──
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.canvas_w,
            height=self.canvas_h,
            bg=EINK_WHITE,
            cursor="crosshair",
            highlightthickness=1,
            highlightbackground=FG_DIM,
        )
        self.canvas.pack()

        # ── Status bar ──
        status = ttk.Frame(self)
        status.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.pos_label = ttk.Label(status, text="x: -  y: -")
        self.pos_label.pack(side=tk.LEFT)

        self.info_label = ttk.Label(status, text=f"{DISPLAY_W}x{DISPLAY_H}  1-bit monochrome")
        self.info_label.pack(side=tk.RIGHT)

        # ── Bindings ──
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)

    def _on_tool_change(self):
        self.current_tool = self.tool_var.get()

    def _canvas_to_pixel(self, cx, cy):
        """Convert canvas coords to pixel coords."""
        px = int(cx / self.scale)
        py = int(cy / self.scale)
        return max(0, min(px, DISPLAY_W - 1)), max(0, min(py, DISPLAY_H - 1))

    def _set_pixel(self, px, py, value):
        """Set a pixel in the buffer and draw it on the canvas."""
        if 0 <= px < DISPLAY_W and 0 <= py < DISPLAY_H:
            self.pixels[py][px] = value
            colour = EINK_BLACK if value else EINK_WHITE
            x1 = px * self.scale
            y1 = py * self.scale
            self.canvas.create_rectangle(
                x1, y1, x1 + self.scale, y1 + self.scale,
                fill=colour, outline=colour, tags="pixel"
            )

    def _draw_brush(self, px, py, value):
        """Draw a square brush at the given pixel position."""
        size = self.size_var.get()
        half = size // 2
        for dy in range(-half, -half + size):
            for dx in range(-half, -half + size):
                self._set_pixel(px + dx, py + dy, value)

    def _on_click(self, event):
        px, py = self._canvas_to_pixel(event.x, event.y)
        tool = self.tool_var.get()

        if tool == "pencil":
            self._draw_brush(px, py, 1)
        elif tool == "eraser":
            self._draw_brush(px, py, 0)
        elif tool in ("line", "rectangle", "filled_rect"):
            self.drag_start = (px, py)
        elif tool == "text":
            self._place_text(px, py)

    def _on_drag(self, event):
        px, py = self._canvas_to_pixel(event.x, event.y)
        tool = self.tool_var.get()

        if tool == "pencil":
            self._draw_brush(px, py, 1)
        elif tool == "eraser":
            self._draw_brush(px, py, 0)
        elif tool in ("line", "rectangle", "filled_rect"):
            # Preview with rubber band
            self.canvas.delete("preview")
            if self.drag_start:
                sx, sy = self.drag_start
                x1, y1 = sx * self.scale, sy * self.scale
                x2, y2 = px * self.scale, py * self.scale
                if tool == "line":
                    self.canvas.create_line(x1, y1, x2, y2, fill=EINK_BLACK,
                                            width=self.size_var.get(), tags="preview")
                elif tool == "rectangle":
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline=EINK_BLACK,
                                                 width=self.size_var.get(), tags="preview")
                elif tool == "filled_rect":
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=EINK_BLACK,
                                                 outline=EINK_BLACK, tags="preview")

    def _on_release(self, event):
        px, py = self._canvas_to_pixel(event.x, event.y)
        tool = self.tool_var.get()
        self.canvas.delete("preview")

        if self.drag_start and tool in ("line", "rectangle", "filled_rect"):
            sx, sy = self.drag_start
            if tool == "line":
                self._draw_line(sx, sy, px, py)
            elif tool == "rectangle":
                self._draw_rect(sx, sy, px, py, fill=False)
            elif tool == "filled_rect":
                self._draw_rect(sx, sy, px, py, fill=True)
            self.drag_start = None

    def _on_motion(self, event):
        px, py = self._canvas_to_pixel(event.x, event.y)
        self.pos_label.config(text=f"x: {px}  y: {py}")

    def _draw_line(self, x0, y0, x1, y1):
        """Bresenham's line algorithm."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self._draw_brush(x0, y0, 1)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def _draw_rect(self, x0, y0, x1, y1, fill=False):
        """Draw a rectangle (outline or filled)."""
        left, right = min(x0, x1), max(x0, x1)
        top, bottom = min(y0, y1), max(y0, y1)
        if fill:
            for y in range(top, bottom + 1):
                for x in range(left, right + 1):
                    self._set_pixel(x, y, 1)
        else:
            for x in range(left, right + 1):
                self._set_pixel(x, top, 1)
                self._set_pixel(x, bottom, 1)
            for y in range(top, bottom + 1):
                self._set_pixel(left, y, 1)
                self._set_pixel(right, y, 1)

    def _place_text(self, px, py):
        """Place text at the clicked position."""
        text = simpledialog.askstring("Draw Text", "Enter text:",
                                      parent=self.winfo_toplevel())
        if not text:
            return

        font_size = self.font_size_var.get()
        # Render text to pixel buffer using a temporary canvas trick
        tmp = tk.Canvas(self, width=DISPLAY_W, height=DISPLAY_H)
        fnt = tkfont.Font(family="Courier", size=font_size, weight="bold")
        tmp.create_text(0, 0, text=text, anchor=tk.NW, font=fnt, fill="black")
        tmp.update_idletasks()

        # Get text bounding box and rasterize character by character
        # Simple approach: use font metrics to estimate pixel placement
        char_w = fnt.measure("M")
        char_h = fnt.metrics("linespace")
        tmp.destroy()

        # Draw each character as a block of pixels
        for i, ch in enumerate(text):
            cx = px + i * (char_w // self.scale + 1)
            # Simple bitmap font rendering — draw character outline
            for row in range(min(char_h, DISPLAY_H - py)):
                for col in range(min(char_w, DISPLAY_W - cx)):
                    # Approximate: fill a rectangle for each character
                    pass

        # Fallback: draw text directly on the scaled canvas and extract
        self.canvas.create_text(
            px * self.scale, py * self.scale,
            text=text, anchor=tk.NW,
            font=tkfont.Font(family="Courier", size=font_size * self.scale // 3, weight="bold"),
            fill=EINK_BLACK, tags="text_render"
        )

        # Rasterize canvas text to pixel buffer
        self._rasterize_text_to_buffer(px, py, text, font_size)

    def _rasterize_text_to_buffer(self, px, py, text, font_size):
        """Render text into the pixel buffer using a simple bitmap approach."""
        # Use Pillow if available for proper rasterization, else approximate
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new("1", (DISPLAY_W, DISPLAY_H), 1)  # white
            draw = ImageDraw.Draw(img)
            try:
                pil_font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSansMono.ttf", font_size)
            except (OSError, IOError):
                try:
                    pil_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size)
                except (OSError, IOError):
                    pil_font = ImageFont.load_default()
            draw.text((px, py), text, font=pil_font, fill=0)  # black text

            # Copy rendered pixels into buffer
            for y in range(DISPLAY_H):
                for x in range(DISPLAY_W):
                    if img.getpixel((x, y)) == 0:
                        self._set_pixel(x, y, 1)
        except ImportError:
            # No Pillow — just mark approximate character positions
            char_w = max(font_size // 2, 6)
            char_h = font_size
            for i, ch in enumerate(text):
                if ch == " ":
                    continue
                cx = px + i * char_w
                for dy in range(min(char_h, DISPLAY_H - py)):
                    for dx in range(min(char_w, DISPLAY_W - cx)):
                        if 0 <= cx + dx < DISPLAY_W and 0 <= py + dy < DISPLAY_H:
                            self._set_pixel(cx + dx, py + dy, 1)

    def _clear_canvas(self):
        """Clear to white."""
        self.canvas.delete("all")
        self.pixels = [[0] * DISPLAY_W for _ in range(DISPLAY_H)]
        self.canvas.configure(bg=EINK_WHITE)

    def _invert_canvas(self):
        """Invert all pixels."""
        for y in range(DISPLAY_H):
            for x in range(DISPLAY_W):
                self.pixels[y][x] = 1 - self.pixels[y][x]
        self._redraw_from_buffer()

    def _redraw_from_buffer(self):
        """Redraw the entire canvas from the pixel buffer."""
        self.canvas.delete("all")
        for y in range(DISPLAY_H):
            for x in range(DISPLAY_W):
                if self.pixels[y][x]:
                    x1 = x * self.scale
                    y1 = y * self.scale
                    self.canvas.create_rectangle(
                        x1, y1, x1 + self.scale, y1 + self.scale,
                        fill=EINK_BLACK, outline=EINK_BLACK, tags="pixel"
                    )

    def _pixels_to_bytes(self):
        """Convert pixel buffer to packed bytes (MSB first, 1=black)."""
        byte_width = (DISPLAY_W + 7) // 8
        data = bytearray(byte_width * DISPLAY_H)
        for y in range(DISPLAY_H):
            for x in range(DISPLAY_W):
                if self.pixels[y][x]:
                    byte_idx = y * byte_width + x // 8
                    bit_idx = 7 - (x % 8)
                    data[byte_idx] |= (1 << bit_idx)
        return bytes(data)

    def _bytes_to_pixels(self, data):
        """Load packed bytes into the pixel buffer."""
        byte_width = (DISPLAY_W + 7) // 8
        self.pixels = [[0] * DISPLAY_W for _ in range(DISPLAY_H)]
        for y in range(DISPLAY_H):
            for x in range(DISPLAY_W):
                byte_idx = y * byte_width + x // 8
                bit_idx = 7 - (x % 8)
                if byte_idx < len(data) and data[byte_idx] & (1 << bit_idx):
                    self.pixels[y][x] = 1

    def _save_image(self):
        """Save the current canvas as a .pbm (P4 binary) and raw .bin file."""
        ASSETS_DIR.mkdir(exist_ok=True)

        name = simpledialog.askstring("Save Image", "Asset name (no extension):",
                                       parent=self.winfo_toplevel())
        if not name:
            return

        name = re.sub(r'[^\w\-]', '_', name)

        # Save as PBM (P4 binary — 1-bit, no dependencies)
        pbm_path = ASSETS_DIR / f"{name}.pbm"
        byte_width = (DISPLAY_W + 7) // 8
        with open(pbm_path, "wb") as f:
            f.write(f"P4\n{DISPLAY_W} {DISPLAY_H}\n".encode())
            for y in range(DISPLAY_H):
                row = 0
                for x in range(DISPLAY_W):
                    if x > 0 and x % 8 == 0:
                        f.write(struct.pack("B", row))
                        row = 0
                    if self.pixels[y][x]:
                        row |= (1 << (7 - x % 8))
                # Write last byte of row (with padding)
                f.write(struct.pack("B", row))
                # Pad remaining bytes if needed
                remaining = byte_width - ((DISPLAY_W + 7) // 8)
                f.write(b'\x00' * remaining)

        # Save as raw binary (for direct upload to Pico)
        bin_path = ASSETS_DIR / f"{name}.bin"
        with open(bin_path, "wb") as f:
            f.write(self._pixels_to_bytes())

        # Save as PNG if Pillow is available
        try:
            from PIL import Image
            img = Image.new("1", (DISPLAY_W, DISPLAY_H), 1)
            for y in range(DISPLAY_H):
                for x in range(DISPLAY_W):
                    if self.pixels[y][x]:
                        img.putpixel((x, y), 0)
            png_path = ASSETS_DIR / f"{name}.png"
            img.save(str(png_path))
            self.app.log(f"Saved: {pbm_path.name}, {bin_path.name}, {png_path.name}")
        except ImportError:
            self.app.log(f"Saved: {pbm_path.name}, {bin_path.name} (install Pillow for PNG)")

    def _load_image(self):
        """Load a .pbm, .bin, or .png image."""
        path = filedialog.askopenfilename(
            title="Load Image",
            initialdir=str(ASSETS_DIR),
            filetypes=[
                ("All supported", "*.pbm *.bin *.png"),
                ("PBM", "*.pbm"),
                ("Raw binary", "*.bin"),
                ("PNG", "*.png"),
            ]
        )
        if not path:
            return

        p = Path(path)
        if p.suffix == ".bin":
            data = p.read_bytes()
            self._bytes_to_pixels(data)
            self._redraw_from_buffer()
        elif p.suffix == ".pbm":
            self._load_pbm(p)
            self._redraw_from_buffer()
        elif p.suffix == ".png":
            self._load_png(p)
            self._redraw_from_buffer()

        self.app.log(f"Loaded: {p.name}")

    def _load_pbm(self, path):
        """Load a P4 (binary) or P1 (ASCII) PBM file."""
        with open(path, "rb") as f:
            magic = f.readline().strip()
            # Skip comments
            line = f.readline()
            while line.startswith(b"#"):
                line = f.readline()
            w, h = map(int, line.split())
            if magic == b"P4":
                data = f.read()
                self._bytes_to_pixels(data)
            elif magic == b"P1":
                text = f.read().decode()
                vals = [int(c) for c in text.split()]
                self.pixels = [[0] * DISPLAY_W for _ in range(DISPLAY_H)]
                idx = 0
                for y in range(min(h, DISPLAY_H)):
                    for x in range(min(w, DISPLAY_W)):
                        if idx < len(vals):
                            self.pixels[y][x] = vals[idx]
                            idx += 1

    def _load_png(self, path):
        """Load a PNG via Pillow."""
        try:
            from PIL import Image
            img = Image.open(str(path)).convert("1").resize((DISPLAY_W, DISPLAY_H))
            self.pixels = [[0] * DISPLAY_W for _ in range(DISPLAY_H)]
            for y in range(DISPLAY_H):
                for x in range(DISPLAY_W):
                    if img.getpixel((x, y)) == 0:
                        self.pixels[y][x] = 1
        except ImportError:
            messagebox.showerror("Error", "Pillow is required for PNG support.\n\npip install Pillow")

    def _send_to_pico(self):
        """Send the current image to the Pico W via serial (non-blocking)."""
        port = find_pico_serial()
        if not port:
            messagebox.showwarning("No Pico", "No Pico W detected on USB serial.")
            return

        data = self._pixels_to_bytes()
        self.app.log(f"Sending {len(data)} bytes to {port}...")

        def _do_send():
            try:
                with serial.Serial(port, DEFAULT_BAUD, timeout=2,
                                    write_timeout=5) as ser:
                    ser.write(b"IMG:")
                    ser.write(struct.pack("<HH", DISPLAY_W, DISPLAY_H))
                    ser.write(data)
                    ser.flush()
                self.app.log(f"Image sent to Pico W ({len(data)} bytes)")
            except serial.SerialTimeoutException:
                self.after(0, lambda: messagebox.showwarning(
                    "Send Timed Out",
                    "Pico needs IMG-receiver firmware to display images.\n\n"
                    "Steps:\n"
                    "1) Go to the Programs tab\n"
                    "2) Put Pico in BOOTSEL mode (hold BOOTSEL + plug in)\n"
                    "3) Click 'Build & Flash to Pico'\n"
                    "4) Wait for reboot, then retry Send to Pico"))
            except serial.SerialException as e:
                self.after(0, lambda: messagebox.showerror("Serial Error", str(e)))

        threading.Thread(target=_do_send, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
# Serial Monitor
# ─────────────────────────────────────────────────────────────────────────────

class SerialMonitor(ttk.Frame):
    """
    Live serial monitor for Pico W USB output.

    Connects to /dev/ttyACM0 at 115200 baud, displays incoming text,
    supports sending commands, and can log to file.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.serial_conn = None
        self.read_thread = None
        self.running = False
        self.log_file = None
        self.auto_scroll = True

        self._build_ui()

    def _build_ui(self):
        # ── Connection bar ──
        conn = ttk.Frame(self)
        conn.pack(fill=tk.X, padx=5, pady=(5, 2))

        ttk.Label(conn, text="Port:").pack(side=tk.LEFT, padx=(0, 3))
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn, textvariable=self.port_var, width=18)
        self.port_combo.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(conn, text="Refresh", command=self._refresh_ports).pack(side=tk.LEFT, padx=2)

        ttk.Label(conn, text="Baud:").pack(side=tk.LEFT, padx=(8, 3))
        self.baud_var = tk.StringVar(value=str(DEFAULT_BAUD))
        baud_combo = ttk.Combobox(conn, textvariable=self.baud_var, width=8,
                                   values=["9600", "19200", "38400", "57600", "115200", "230400"])
        baud_combo.pack(side=tk.LEFT, padx=(0, 8))

        self.connect_btn = ttk.Button(conn, text="Connect", command=self._toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=2)

        self.status_label = ttk.Label(conn, text="Disconnected", foreground=FG_RED)
        self.status_label.pack(side=tk.LEFT, padx=8)

        ttk.Separator(conn, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

        self.autoscroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(conn, text="Auto-scroll", variable=self.autoscroll_var).pack(side=tk.LEFT)

        ttk.Button(conn, text="Clear", command=self._clear_output).pack(side=tk.LEFT, padx=5)
        ttk.Button(conn, text="Save Log", command=self._save_log).pack(side=tk.LEFT, padx=2)

        # ── Output area ──
        output_frame = ttk.Frame(self)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.output_text = tk.Text(
            output_frame, wrap=tk.WORD, state=tk.DISABLED,
            bg=BG_DARK, fg=FG_TEXT, insertbackground=FG_TEXT,
            font=("JetBrains Mono", 10),
            selectbackground=FG_ACCENT, selectforeground=BG_DARK,
        )
        scrollbar = ttk.Scrollbar(output_frame, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # ── Input bar ──
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.bind("<Return>", self._send_command)

        ttk.Button(input_frame, text="Send", command=self._send_command).pack(side=tk.LEFT)
        ttk.Button(input_frame, text="Ctrl+C", command=self._send_interrupt).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Reset", command=self._send_reset).pack(side=tk.LEFT)

        self._refresh_ports()

    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        # Auto-select Pico
        pico = find_pico_serial()
        if pico:
            self.port_var.set(pico)
        elif ports:
            self.port_var.set(ports[0])

    def _toggle_connection(self):
        if self.running:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self.port_var.get()
        baud = int(self.baud_var.get())

        if not port:
            messagebox.showwarning("No Port", "Select a serial port first.")
            return

        try:
            self.serial_conn = serial.Serial(port, baud, timeout=SERIAL_TIMEOUT)
            self.running = True
            self.connect_btn.config(text="Disconnect")
            self.status_label.config(text=f"Connected: {port}", foreground=FG_GREEN)
            self.app.log(f"Serial connected: {port} @ {baud}")

            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
        except serial.SerialException as e:
            messagebox.showerror("Connection Failed", str(e))

    def _disconnect(self):
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.serial_conn = None
        self.connect_btn.config(text="Connect")
        self.status_label.config(text="Disconnected", foreground=FG_RED)
        self.app.log("Serial disconnected")

    def _read_loop(self):
        """Background thread reading serial data."""
        while self.running and self.serial_conn and self.serial_conn.is_open:
            try:
                data = self.serial_conn.readline()
                if data:
                    text = data.decode("utf-8", errors="replace")
                    self._append_output(text)
            except serial.SerialException:
                self.running = False
                self.winfo_toplevel().after(0, self._disconnect)
                break
            except Exception:
                pass

    def _append_output(self, text):
        """Append text to the output (thread-safe via after())."""
        def _do():
            self.output_text.configure(state=tk.NORMAL)
            self.output_text.insert(tk.END, text)
            if self.autoscroll_var.get():
                self.output_text.see(tk.END)
            self.output_text.configure(state=tk.DISABLED)
        self.winfo_toplevel().after(0, _do)

    def _send_command(self, event=None):
        cmd = self.input_entry.get()
        if not cmd or not self.serial_conn or not self.serial_conn.is_open:
            return
        try:
            self.serial_conn.write((cmd + "\r\n").encode())
            self._append_output(f"> {cmd}\n")
            self.input_entry.delete(0, tk.END)
        except serial.SerialException as e:
            self.app.log(f"Send failed: {e}")

    def _send_interrupt(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write(b"\x03")  # Ctrl+C

    def _send_reset(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write(b"\x04")  # Ctrl+D soft reset

    def _clear_output(self):
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.configure(state=tk.DISABLED)

    def _save_log(self):
        path = filedialog.asksaveasfilename(
            title="Save Serial Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"serial_log_{datetime.now():%Y%m%d_%H%M%S}.txt"
        )
        if path:
            content = self.output_text.get("1.0", tk.END)
            Path(path).write_text(content)
            self.app.log(f"Log saved: {path}")

    def destroy(self):
        self._disconnect()
        super().destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Firmware Flash Utility
# ─────────────────────────────────────────────────��───────────────────────────

class FlashUtility(ttk.Frame):
    """Flash .uf2 firmware to the Pico W via BOOTSEL mode."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # ── UF2 file selection ──
        file_frame = ttk.LabelFrame(self, text="Firmware File", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=10)

        self.uf2_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.uf2_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(file_frame, text="Browse", command=self._browse_uf2).pack(side=tk.LEFT, padx=2)

        # Quick picks
        quick_frame = ttk.LabelFrame(self, text="Quick Flash", padding=10)
        quick_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        serial_uf2 = DEV_SETUP / "hello-world-serial" / "build" / "hello_serial.uf2"
        display_uf2 = DEV_SETUP / "hello-world" / "build" / "hello_dilder.uf2"

        for label, path in [
            ("Hello Serial", serial_uf2),
            ("Hello Display", display_uf2),
        ]:
            exists = path.exists()
            btn = ttk.Button(
                quick_frame, text=f"{label} {'(' + self._size_str(path) + ')' if exists else '(not built)'}",
                command=lambda p=path: self._set_uf2(p),
                state=tk.NORMAL if exists else tk.DISABLED,
            )
            btn.pack(side=tk.LEFT, padx=5)

        # ── Flash control ──
        flash_frame = ttk.LabelFrame(self, text="Flash to Pico W", padding=10)
        flash_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.mount_label = ttk.Label(flash_frame, text="RPI-RP2: not detected")
        self.mount_label.pack(anchor=tk.W)

        btn_row = ttk.Frame(flash_frame)
        btn_row.pack(fill=tk.X, pady=(8, 0))

        ttk.Button(btn_row, text="Detect RPI-RP2", command=self._detect_mount).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_row, text="Flash", command=self._flash).pack(side=tk.LEFT, padx=5)

        # ── Build ──
        build_frame = ttk.LabelFrame(self, text="Build Projects", padding=10)
        build_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        for label, proj_dir in [
            ("Build Hello Serial", DEV_SETUP / "hello-world-serial"),
            ("Build Hello Display", DEV_SETUP / "hello-world"),
        ]:
            ttk.Button(
                build_frame, text=label,
                command=lambda d=proj_dir: self._build_project(d)
            ).pack(side=tk.LEFT, padx=5)

        # ── Instructions ──
        inst_frame = ttk.LabelFrame(self, text="Instructions", padding=10)
        inst_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        instructions = tk.Text(inst_frame, height=8, wrap=tk.WORD, bg=BG_DARK, fg=FG_TEXT,
                               font=("JetBrains Mono", 10), state=tk.DISABLED)
        instructions.pack(fill=tk.BOTH, expand=True)
        instructions.configure(state=tk.NORMAL)
        instructions.insert(tk.END, """\
To flash the Pico W:

1. Unplug the Pico W from USB
2. Hold down the BOOTSEL button (small white button)
3. While holding BOOTSEL, plug in the USB cable
4. Release BOOTSEL after 1 second
5. Click "Detect RPI-RP2" above
6. Click "Flash" to copy the firmware

The Pico W will reboot automatically after flashing.
The RPI-RP2 drive will disappear — this is normal.\
""")
        instructions.configure(state=tk.DISABLED)

    def _size_str(self, path):
        try:
            return f"{path.stat().st_size / 1024:.0f} KB"
        except (FileNotFoundError, OSError):
            return "?"

    def _browse_uf2(self):
        path = filedialog.askopenfilename(
            title="Select UF2 Firmware",
            initialdir=str(DEV_SETUP),
            filetypes=[("UF2 files", "*.uf2"), ("All files", "*.*")]
        )
        if path:
            self.uf2_var.set(path)

    def _set_uf2(self, path):
        self.uf2_var.set(str(path))

    def _detect_mount(self):
        mount = find_rpi_rp2_mount()
        if mount:
            self.mount_label.config(text=f"RPI-RP2: {mount}", foreground=FG_GREEN)
            self.app.log(f"RPI-RP2 found at {mount}")
        else:
            self.mount_label.config(text="RPI-RP2: not detected — is Pico in BOOTSEL mode?",
                                    foreground=FG_RED)

    def _flash(self):
        uf2 = self.uf2_var.get()
        if not uf2 or not Path(uf2).exists():
            messagebox.showwarning("No File", "Select a .uf2 file first.")
            return

        mount = find_rpi_rp2_mount()
        if not mount:
            messagebox.showwarning("No Pico", "RPI-RP2 not detected.\n\nPut the Pico W in BOOTSEL mode first.")
            return

        try:
            shutil.copy2(uf2, mount / Path(uf2).name)
            self.app.log(f"Flashed: {Path(uf2).name} -> {mount}")
            messagebox.showinfo("Success", f"Firmware flashed!\n\n{Path(uf2).name}")
        except Exception as e:
            messagebox.showerror("Flash Failed", str(e))

    def _build_project(self, proj_dir):
        build_dir = proj_dir / "build"
        build_dir.mkdir(exist_ok=True)

        sdk = os.environ.get("PICO_SDK_PATH", str(Path.home() / "pico" / "pico-sdk"))

        # Check pico_sdk_import.cmake
        cmake_helper = proj_dir / "pico_sdk_import.cmake"
        if not cmake_helper.exists():
            src = Path(sdk) / "external" / "pico_sdk_import.cmake"
            if src.exists():
                shutil.copy2(src, cmake_helper)

        self.app.log(f"Building {proj_dir.name}...")

        def _run():
            try:
                # Configure
                result = subprocess.run(
                    ["cmake", "-G", "Ninja", f"-DPICO_SDK_PATH={sdk}", "-DPICO_BOARD=pico_w", ".."],
                    cwd=build_dir, capture_output=True, text=True
                )
                if result.returncode != 0:
                    self.app.log(f"CMake failed: {result.stderr[-500:]}")
                    return

                # Build
                result = subprocess.run(
                    ["ninja"], cwd=build_dir, capture_output=True, text=True
                )
                if result.returncode != 0:
                    output = (result.stderr or "") + (result.stdout or "")
                    self.app.log(f"Build failed: {output[-500:]}")
                    return

                self.app.log(f"Build complete: {proj_dir.name}")
            except Exception as e:
                self.app.log(f"Build error: {e}")

        threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
# Asset Manager
# ─────────────────────────────────────────────────────────────────────────────

class AssetManager(ttk.Frame):
    """Browse, preview, and manage saved display assets."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        # ── File list ──
        list_frame = ttk.Frame(self)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        ttk.Label(list_frame, text="Assets (assets/)").pack(anchor=tk.W)

        self.file_list = tk.Listbox(
            list_frame, width=30, bg=BG_DARK, fg=FG_TEXT,
            selectbackground=FG_ACCENT, selectforeground=BG_DARK,
            font=("JetBrains Mono", 10),
        )
        self.file_list.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.file_list.bind("<<ListboxSelect>>", self._on_select)

        btn_row = ttk.Frame(list_frame)
        btn_row.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btn_row, text="Refresh", command=self._refresh_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="Open Folder", command=self._open_folder).pack(side=tk.LEFT, padx=2)

        # ── Preview ──
        preview_frame = ttk.LabelFrame(self, text="Preview", padding=5)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.preview_canvas = tk.Canvas(
            preview_frame,
            width=DISPLAY_W * 2,
            height=DISPLAY_H * 2,
            bg=EINK_WHITE,
            highlightthickness=1,
            highlightbackground=FG_DIM,
        )
        self.preview_canvas.pack()

        self.preview_info = ttk.Label(preview_frame, text="Select an asset to preview")
        self.preview_info.pack(pady=5)

    def _refresh_list(self):
        self.file_list.delete(0, tk.END)
        ASSETS_DIR.mkdir(exist_ok=True)
        files = sorted(ASSETS_DIR.iterdir())
        for f in files:
            if f.is_file() and f.suffix in (".pbm", ".bin", ".png"):
                self.file_list.insert(tk.END, f.name)

    def _on_select(self, event=None):
        sel = self.file_list.curselection()
        if not sel:
            return
        name = self.file_list.get(sel[0])
        path = ASSETS_DIR / name
        self._preview_file(path)

    def _preview_file(self, path):
        self.preview_canvas.delete("all")
        scale = 2

        pixels = [[0] * DISPLAY_W for _ in range(DISPLAY_H)]

        if path.suffix == ".bin":
            data = path.read_bytes()
            byte_width = (DISPLAY_W + 7) // 8
            for y in range(DISPLAY_H):
                for x in range(DISPLAY_W):
                    byte_idx = y * byte_width + x // 8
                    bit_idx = 7 - (x % 8)
                    if byte_idx < len(data) and data[byte_idx] & (1 << bit_idx):
                        pixels[y][x] = 1
        elif path.suffix == ".png":
            try:
                from PIL import Image
                img = Image.open(str(path)).convert("1").resize((DISPLAY_W, DISPLAY_H))
                for y in range(DISPLAY_H):
                    for x in range(DISPLAY_W):
                        if img.getpixel((x, y)) == 0:
                            pixels[y][x] = 1
            except ImportError:
                self.preview_info.config(text="Install Pillow for PNG preview")
                return

        for y in range(DISPLAY_H):
            for x in range(DISPLAY_W):
                if pixels[y][x]:
                    self.preview_canvas.create_rectangle(
                        x * scale, y * scale,
                        x * scale + scale, y * scale + scale,
                        fill=EINK_BLACK, outline=EINK_BLACK,
                    )

        size = path.stat().st_size
        self.preview_info.config(text=f"{path.name}  |  {size} bytes  |  {DISPLAY_W}x{DISPLAY_H}")

    def _delete_selected(self):
        sel = self.file_list.curselection()
        if not sel:
            return
        name = self.file_list.get(sel[0])
        if messagebox.askyesno("Delete", f"Delete {name}?"):
            (ASSETS_DIR / name).unlink(missing_ok=True)
            self._refresh_list()
            self.preview_canvas.delete("all")
            self.app.log(f"Deleted: {name}")

    def _open_folder(self):
        ASSETS_DIR.mkdir(exist_ok=True)
        if platform.system() == "Linux":
            subprocess.Popen(["xdg-open", str(ASSETS_DIR)])
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(ASSETS_DIR)])


# ─────────────────────────────────────────────────────────────────────────────
# GPIO Pin Viewer
# ─────────────────────────────────────────────────────────────────────────────

class PinViewer(ttk.Frame):
    """Visual GPIO pin assignment reference."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Pin map
        pin_text = tk.Text(self, wrap=tk.NONE, bg=BG_DARK, fg=FG_TEXT,
                           font=("JetBrains Mono", 11), state=tk.DISABLED,
                           height=30, width=70)
        pin_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        pin_text.configure(state=tk.NORMAL)
        pin_text.insert(tk.END, """\
Pico W GPIO Pin Assignments — Dilder Project
══════════════════════════════════════════════

               ┌───USB───┐
   GP0  [ 1]   │         │  [40]  VBUS
   GP1  [ 2]   │  PICO   │  [39]  VSYS
   GND  [ 3]   │    W    │  [38]  GND       ◄── e-ink GND
▶  GP2  [ 4]   │         │  [37]  3V3_EN
▶  GP3  [ 5]   │         │  [36]  3V3(OUT)  ◄── e-ink VCC
▶  GP4  [ 6]   │         │  [35]  ADC_VREF
▶  GP5  [ 7]   │         │  [34]  GP28
   GND  [ 8]   │         │  [33]  AGND
▶  GP6  [ 9]   │         │  [32]  GP27
   GP7  [10]   │         │  [31]  GP26
▶  GP8  [11]   │         │  [30]  RUN
▶  GP9  [12]   │         │  [29]  GP22
   GND  [13]   │         │  [28]  GND
▶ GP10  [14]   │         │  [27]  GP21
▶ GP11  [15]   │         │  [26]  GP20
▶ GP12  [16]   │         │  [25]  GP19
▶ GP13  [17]   │         │  [24]  GP18
   GND  [18]   │         │  [23]  GND
  GP14  [19]   │         │  [22]  GP17
  GP15  [20]   └─────────┘  [21]  GP16

▶ = used by Dilder

═══════════════════════════════════════════════
Display (SPI1)                 Buttons
═══════════════════════════════════════════════
VCC  → 3V3(OUT) pin 36        UP     → GP2  pin 4
GND  → GND      pin 38        DOWN   → GP3  pin 5
DIN  → GP11     pin 15        LEFT   → GP4  pin 6
CLK  → GP10     pin 14        RIGHT  → GP5  pin 7
CS   → GP9      pin 12        CENTER → GP6  pin 9
DC   → GP8      pin 11
RST  → GP12     pin 16
BUSY → GP13     pin 17

═══════════════════════════════════════════════
SPI Configuration
═══════════════════════════════════════════════
Controller:  SPI1
Mode:        Mode 0 (CPOL=0, CPHA=0)
Clock:       4 MHz
CS:          Active LOW
Bit order:   MSB first
""")
        pin_text.configure(state=tk.DISABLED)


# ─────────────────────────────────────────────────────────────────────────────
# Connection Utility — USB & Wi-Fi Setup Walkthrough
# ─────────────────────────────────────────────────────────────────────────────

class ConnectionUtility(ttk.Frame):
    """
    Step-by-step walkthrough for connecting the Pico W via USB serial
    and over Wi-Fi. Includes live status checks at each step.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # ── Mode selector ──
        mode_frame = ttk.Frame(self)
        mode_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        self.mode_var = tk.StringVar(value="usb")
        ttk.Radiobutton(mode_frame, text="USB Serial Connection",
                        variable=self.mode_var, value="usb",
                        command=self._show_mode).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="Wi-Fi Connection",
                        variable=self.mode_var, value="wifi",
                        command=self._show_mode).pack(side=tk.LEFT)

        # ── Content area ──
        self.content = ttk.Frame(self)
        self.content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._show_mode()

    def _show_mode(self):
        for w in self.content.winfo_children():
            w.destroy()
        if self.mode_var.get() == "usb":
            self._build_usb_panel()
        else:
            self._build_wifi_panel()

    # ── USB Panel ────────────────────────────────────────────────────────────

    def _build_usb_panel(self):
        canvas = tk.Canvas(self.content, bg=BG_PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-3, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(3, "units"))

        f = scroll_frame

        # Step 1
        self._step_header(f, "Step 1", "Plug in the Pico W via USB")
        self._step_body(f, """\
Connect the Pico W to your computer using a micro-USB cable.

IMPORTANT: The cable must be a data cable, not a charge-only cable.
Charge-only cables have no data wires — they physically cannot
communicate. If in doubt, try a different cable.

The Pico W should NOT be in BOOTSEL mode for serial communication.
Just plug it in normally with firmware already flashed.""")

        self._step_check_btn(f, "Check: Is a USB device detected?", self._check_usb_device)
        self.usb_step1_label = ttk.Label(f, text="")
        self.usb_step1_label.pack(anchor=tk.W, padx=20)

        # Step 2
        self._step_header(f, "Step 2", "Verify the serial port exists")
        self._step_body(f, """\
When the Pico W is running firmware with USB serial enabled
(stdio_init_all() in C code), it appears as /dev/ttyACM0.

If it does not appear, the Pico W may be:
  - In BOOTSEL mode (shows as RPI-RP2 drive instead)
  - Running firmware without USB serial enabled
  - Connected with a charge-only cable""")

        self._step_check_btn(f, "Check: Is /dev/ttyACM0 present?", self._check_serial_port)
        self.usb_step2_label = ttk.Label(f, text="")
        self.usb_step2_label.pack(anchor=tk.W, padx=20)

        # Step 3
        self._step_header(f, "Step 3", "Verify serial port permissions")
        self._step_body(f, """\
Your user must be in the serial port group to access the device.

  Arch / CachyOS / Manjaro:  uucp
  Ubuntu / Debian:            dialout

If you are not in the group, run:
  sudo usermod -aG uucp $USER    (Arch)
  sudo usermod -aG dialout $USER (Debian)

Then log out and back in (a new terminal is not enough).""")

        self._step_check_btn(f, "Check: Do I have serial permissions?", self._check_serial_perms)
        self.usb_step3_label = ttk.Label(f, text="")
        self.usb_step3_label.pack(anchor=tk.W, padx=20)

        self.fix_perms_btn = ttk.Button(f, text="Fix: Add me to serial group (requires sudo password)",
                                        command=self._fix_serial_perms)
        self.fix_perms_btn.pack(anchor=tk.W, padx=20, pady=(3, 0))

        # Step 4
        self._step_header(f, "Step 4", "Open the Serial Monitor")
        self._step_body(f, """\
Everything looks good — switch to the Serial Monitor tab to connect.

  1. Go to the "Serial Monitor" tab
  2. Port should auto-select /dev/ttyACM0
  3. Baud rate: 115200
  4. Click "Connect"

You should see printf output from your Pico W firmware.""")

        ttk.Button(f, text="Go to Serial Monitor",
                   command=lambda: self.app.notebook.select(self.app.serial_tab)).pack(
                       anchor=tk.W, padx=20, pady=(5, 20))

    # ── Wi-Fi Panel ──────────────────────────────────────────────────────────

    def _build_wifi_panel(self):
        canvas = tk.Canvas(self.content, bg=BG_PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-3, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(3, "units"))

        f = scroll_frame

        # Overview
        self._step_header(f, "Overview", "Pico W Wi-Fi Connection")
        self._step_body(f, """\
The Pico W has an onboard Infineon CYW43439 Wi-Fi chip
(802.11n, 2.4 GHz). You can use it to connect the Pico W to
your local network and communicate with it wirelessly —
no USB cable needed after initial setup.

This requires firmware that initialises Wi-Fi. The hello world
examples do not use Wi-Fi. You will need to write or flash
Wi-Fi-enabled firmware first.""")

        # Step 1
        self._step_header(f, "Step 1", "Add Wi-Fi credentials to your firmware")
        self._step_body(f, """\
In your C code, initialise Wi-Fi and connect to your network:""")

        code_frame = ttk.Frame(f)
        code_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        code_text = tk.Text(code_frame, height=14, wrap=tk.NONE, bg=BG_DARK, fg=FG_TEXT,
                            font=("JetBrains Mono", 10), state=tk.DISABLED)
        code_text.pack(fill=tk.X)
        code_text.configure(state=tk.NORMAL)
        code_text.insert(tk.END, """\
#include "pico/cyw43_arch.h"
#include "lwip/tcp.h"

// Initialise Wi-Fi
if (cyw43_arch_init_with_country(CYW43_COUNTRY_USA)) {
    printf("Wi-Fi init failed\\n");
    return 1;
}
cyw43_arch_enable_sta_mode();

// Connect to your network
if (cyw43_arch_wifi_connect_timeout_ms(
        "YOUR_SSID", "YOUR_PASSWORD",
        CYW43_AUTH_WPA2_AES_PSK, 10000)) {
    printf("Wi-Fi connect failed\\n");
} else {
    printf("Wi-Fi connected\\n");
}""")
        code_text.configure(state=tk.DISABLED)

        # Step 2
        self._step_header(f, "Step 2", "Link the Wi-Fi libraries in CMakeLists.txt")
        self._step_body(f, """\
Add these libraries to your target_link_libraries():""")

        cmake_frame = ttk.Frame(f)
        cmake_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        cmake_text = tk.Text(cmake_frame, height=6, wrap=tk.NONE, bg=BG_DARK, fg=FG_TEXT,
                             font=("JetBrains Mono", 10), state=tk.DISABLED)
        cmake_text.pack(fill=tk.X)
        cmake_text.configure(state=tk.NORMAL)
        cmake_text.insert(tk.END, """\
target_link_libraries(your_project
    pico_stdlib
    pico_cyw43_arch_lwip_threadsafe_background
    hardware_spi
    hardware_gpio
)""")
        cmake_text.configure(state=tk.DISABLED)

        # Step 3
        self._step_header(f, "Step 3", "Find the Pico W on your network")
        self._step_body(f, """\
After the Pico W connects to Wi-Fi, it gets an IP address via DHCP.
Your firmware should print it:

    printf("IP: %s\\n", ip4addr_ntoa(
        netif_ip4_addr(netif_list)));

Then you can ping it from your computer:""")

        self._step_check_btn(f, "Scan: Find Pico W on local network", self._scan_network)
        self.wifi_scan_label = ttk.Label(f, text="")
        self.wifi_scan_label.pack(anchor=tk.W, padx=20)

        # Step 4
        self._step_header(f, "Step 4", "Communicate over Wi-Fi")
        self._step_body(f, """\
With Wi-Fi working, you have several options:

TCP Socket Server — Run a TCP listener on the Pico W.
  Your DevTool or any script can connect and send commands
  or image data over the network instead of USB serial.

HTTP Server — Serve a simple web page from the Pico W.
  Useful for status dashboards or remote control.

UDP Broadcast — The Pico W can announce itself on the
  network so the DevTool can auto-discover it.

mDNS — Advertise the Pico W as "dilder.local" on the
  network so you don't need to know the IP address.

These are firmware features you build in C. The Pico SDK
includes lwIP (lightweight IP stack) which supports all
of the above.""")

        # Wi-Fi connection test
        self._step_header(f, "Quick Connect", "Test a TCP connection to the Pico W")
        self._step_body(f, """\
If your firmware is running a TCP server, enter the IP and
port below to test the connection.""")

        conn_frame = ttk.Frame(f)
        conn_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        ttk.Label(conn_frame, text="IP:").pack(side=tk.LEFT)
        self.wifi_ip_var = tk.StringVar(value="192.168.1.")
        ttk.Entry(conn_frame, textvariable=self.wifi_ip_var, width=16).pack(side=tk.LEFT, padx=(3, 10))

        ttk.Label(conn_frame, text="Port:").pack(side=tk.LEFT)
        self.wifi_port_var = tk.StringVar(value="4242")
        ttk.Entry(conn_frame, textvariable=self.wifi_port_var, width=6).pack(side=tk.LEFT, padx=(3, 10))

        ttk.Button(conn_frame, text="Test Connection", command=self._test_wifi_conn).pack(side=tk.LEFT)

        self.wifi_conn_label = ttk.Label(f, text="")
        self.wifi_conn_label.pack(anchor=tk.W, padx=20, pady=(0, 20))

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _step_header(self, parent, step, title):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=(15, 2))
        lbl = ttk.Label(frame, text=f"{step} — {title}",
                        font=("JetBrains Mono", 12, "bold"), foreground=FG_ACCENT)
        lbl.pack(anchor=tk.W)
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(3, 0))

    def _step_body(self, parent, text):
        lbl = ttk.Label(parent, text=text, wraplength=700, justify=tk.LEFT,
                        font=("JetBrains Mono", 10))
        lbl.pack(anchor=tk.W, padx=20, pady=(5, 5))

    def _step_check_btn(self, parent, text, command):
        ttk.Button(parent, text=text, command=command).pack(anchor=tk.W, padx=20, pady=(5, 3))

    # ── USB Checks ───────────────────────────────────────────────────────────

    def _check_usb_device(self):
        try:
            result = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=5)
            pico_lines = [l for l in result.stdout.splitlines()
                          if "2e8a" in l.lower() or "raspberry pi" in l.lower() or "rpi" in l.lower()]
            if pico_lines:
                self.usb_step1_label.config(text=f"  ✓ Pico W detected: {pico_lines[0].strip()}",
                                            foreground=FG_GREEN)
                self.app.log("USB check: Pico W detected")
            else:
                self.usb_step1_label.config(text="  ✗ No Pico W found on USB. Check cable and connection.",
                                            foreground=FG_RED)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.usb_step1_label.config(text="  ? lsusb not available — check manually with: lsusb",
                                        foreground=FG_YELLOW)

    def _check_serial_port(self):
        port = find_pico_serial()
        if port:
            self.usb_step2_label.config(
                text=f"  ✓ {port} detected — Pico W serial is ready",
                foreground=FG_GREEN)
            self.app.log(f"Serial port check: {port} found")
        else:
            # Check for any ttyACM as fallback hint
            import glob as _glob
            others = _glob.glob("/dev/ttyACM*")
            if others:
                self.usb_step2_label.config(
                    text=f"  ~ Pico not auto-detected, but found: {', '.join(others)}",
                    foreground=FG_YELLOW)
            else:
                self.usb_step2_label.config(
                    text="  ✗ No serial devices found. Is the Pico W plugged in with firmware?",
                    foreground=FG_RED)

    def _check_serial_perms(self):
        result = subprocess.run(["groups"], capture_output=True, text=True)
        groups = result.stdout.strip().split() if result.returncode == 0 else []

        # Check both possible groups
        in_uucp = "uucp" in groups
        in_dialout = "dialout" in groups

        if in_uucp or in_dialout:
            group = "uucp" if in_uucp else "dialout"
            self.usb_step3_label.config(text=f"  ✓ You are in the '{group}' group — permissions OK",
                                        foreground=FG_GREEN)
            self.app.log(f"Permission check: in '{group}' group")
        else:
            self.usb_step3_label.config(
                text="  ✗ Not in 'uucp' or 'dialout'. Run: sudo usermod -aG uucp $USER (then log out/in)",
                foreground=FG_RED)

    def _fix_serial_perms(self):
        """Run sudo usermod to add the user to the serial group, via a terminal."""
        user = os.environ.get("USER", "")
        if not user:
            messagebox.showerror("Error", "Could not determine your username.")
            return

        # Detect the correct group
        group = "uucp"  # Arch/CachyOS default
        try:
            result = subprocess.run(["getent", "group", "dialout"],
                                    capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                group = "dialout"
            else:
                result = subprocess.run(["getent", "group", "uucp"],
                                        capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    group = "uucp"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        cmd = f"sudo usermod -aG {group} {user}"

        confirm = messagebox.askyesno(
            "Add Serial Permissions",
            f"This will run:\n\n  {cmd}\n\n"
            f"A terminal window will open asking for your sudo password.\n\n"
            f"After this completes you must log out and back in.\n\n"
            f"Continue?"
        )
        if not confirm:
            return

        # Launch in a visible terminal so the user can enter their password
        terminal_cmds = [
            # Try common terminal emulators in order
            ["pkexec", "usermod", "-aG", group, user],
        ]

        # Try pkexec first (graphical sudo prompt, no terminal needed)
        try:
            result = subprocess.run(
                ["pkexec", "usermod", "-aG", group, user],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                self.usb_step3_label.config(
                    text=f"  ✓ Added to '{group}' group. LOG OUT AND BACK IN to apply.",
                    foreground=FG_GREEN)
                self.app.log(f"Added {user} to {group} group via pkexec")
                messagebox.showinfo(
                    "Success",
                    f"You have been added to the '{group}' group.\n\n"
                    f"You MUST log out and back in for this to take effect.\n"
                    f"A new terminal window is not enough — full logout required."
                )
                return
            else:
                err = result.stderr.strip()
                if "dismissed" in err.lower() or "cancel" in err.lower():
                    self.app.log("Permission fix cancelled by user")
                    return
                # pkexec failed for another reason, try terminal fallback
        except FileNotFoundError:
            pass  # pkexec not installed, try terminal fallback
        except subprocess.TimeoutExpired:
            self.app.log("pkexec timed out")

        # Fallback: open a terminal emulator with the sudo command
        terminal_attempts = [
            ["xterm", "-e", f"sudo usermod -aG {group} {user} && echo 'Done — close this window' && read"],
            ["konsole", "-e", "bash", "-c", f"sudo usermod -aG {group} {user} && echo 'Done — press Enter' && read"],
            ["gnome-terminal", "--", "bash", "-c", f"sudo usermod -aG {group} {user} && echo 'Done — press Enter' && read"],
        ]

        for term_cmd in terminal_attempts:
            try:
                subprocess.Popen(term_cmd)
                self.usb_step3_label.config(
                    text=f"  ⏳ Terminal opened — enter your sudo password there. Then log out/in.",
                    foreground=FG_YELLOW)
                self.app.log(f"Opened terminal for sudo usermod -aG {group} {user}")
                return
            except FileNotFoundError:
                continue

        # Nothing worked
        messagebox.showwarning(
            "Manual Step Required",
            f"Could not find a graphical sudo prompt or terminal emulator.\n\n"
            f"Open a terminal manually and run:\n\n  {cmd}\n\n"
            f"Then log out and back in."
        )

    # ── Wi-Fi Checks ─────────────────────────────────────────────────────────

    def _scan_network(self):
        self.wifi_scan_label.config(text="  Scanning...", foreground=FG_YELLOW)
        self.update_idletasks()

        def _do_scan():
            # Try nmap ping scan on common subnets
            found = []
            try:
                # Get local subnet
                result = subprocess.run(
                    ["ip", "route", "show", "default"],
                    capture_output=True, text=True, timeout=3
                )
                gateway = None
                if result.returncode == 0:
                    parts = result.stdout.split()
                    if "via" in parts:
                        gateway = parts[parts.index("via") + 1]

                if gateway:
                    subnet = ".".join(gateway.split(".")[:3]) + ".0/24"
                    # Quick arp scan
                    result = subprocess.run(
                        ["ip", "neigh", "show"],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        for line in result.stdout.splitlines():
                            if "REACHABLE" in line or "STALE" in line:
                                ip = line.split()[0]
                                found.append(ip)

            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

            def _update():
                if found:
                    self.wifi_scan_label.config(
                        text=f"  Found {len(found)} devices on local network. "
                             f"Check serial output for Pico W's IP address.",
                        foreground=FG_GREEN)
                else:
                    self.wifi_scan_label.config(
                        text="  No devices found. Check that Pico W firmware has Wi-Fi enabled.",
                        foreground=FG_YELLOW)

            self.winfo_toplevel().after(0, _update)

        threading.Thread(target=_do_scan, daemon=True).start()

    def _test_wifi_conn(self):
        import socket
        ip = self.wifi_ip_var.get().strip()
        try:
            port = int(self.wifi_port_var.get().strip())
        except ValueError:
            self.wifi_conn_label.config(text="  ✗ Invalid port number", foreground=FG_RED)
            return

        self.wifi_conn_label.config(text=f"  Connecting to {ip}:{port}...", foreground=FG_YELLOW)
        self.update_idletasks()

        def _do_connect():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((ip, port))
                sock.close()
                msg = f"  ✓ Connected to {ip}:{port} — Pico W is reachable"
                colour = FG_GREEN
                self.app.log(f"Wi-Fi test: connected to {ip}:{port}")
            except socket.timeout:
                msg = f"  ✗ Connection timed out. Is the Pico W running a TCP server on port {port}?"
                colour = FG_RED
            except ConnectionRefusedError:
                msg = f"  ✗ Connection refused. The Pico W is reachable but no server on port {port}."
                colour = FG_YELLOW
            except OSError as e:
                msg = f"  ✗ Connection failed: {e}"
                colour = FG_RED

            self.winfo_toplevel().after(0, lambda: self.wifi_conn_label.config(text=msg, foreground=colour))

        threading.Thread(target=_do_connect, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
# Documentation Tab
# ─────────────────────────────────────────────────────────────────────────────

class DocumentationTab(ttk.Frame):
    """Embedded application documentation with searchable text."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # ── Search bar ──
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind("<Return>", self._search)
        ttk.Button(search_frame, text="Find", command=self._search).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_frame, text="Clear", command=self._clear_search).pack(side=tk.LEFT, padx=2)

        # ── TOC + Content ──
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # TOC sidebar
        toc_frame = ttk.Frame(paned)
        paned.add(toc_frame, weight=1)

        ttk.Label(toc_frame, text="Contents", font=("JetBrains Mono", 11, "bold"),
                  foreground=FG_ACCENT).pack(anchor=tk.W, pady=(0, 5))

        self.toc_list = tk.Listbox(
            toc_frame, width=28, bg=BG_DARK, fg=FG_TEXT,
            selectbackground=FG_ACCENT, selectforeground=BG_DARK,
            font=("JetBrains Mono", 10), activestyle="none",
        )
        self.toc_list.pack(fill=tk.BOTH, expand=True)
        self.toc_list.bind("<<ListboxSelect>>", self._on_toc_select)

        # Content area
        content_frame = ttk.Frame(paned)
        paned.add(content_frame, weight=4)

        self.doc_text = tk.Text(
            content_frame, wrap=tk.WORD, bg=BG_DARK, fg=FG_TEXT,
            font=("JetBrains Mono", 10), state=tk.DISABLED,
            selectbackground=FG_ACCENT, selectforeground=BG_DARK,
            padx=15, pady=10,
        )
        doc_scroll = ttk.Scrollbar(content_frame, command=self.doc_text.yview)
        self.doc_text.configure(yscrollcommand=doc_scroll.set)
        doc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.doc_text.pack(fill=tk.BOTH, expand=True)

        # Configure text tags
        self.doc_text.tag_configure("h1", font=("JetBrains Mono", 16, "bold"),
                                    foreground=FG_ACCENT, spacing3=10)
        self.doc_text.tag_configure("h2", font=("JetBrains Mono", 13, "bold"),
                                    foreground=FG_MAGENTA, spacing1=15, spacing3=5)
        self.doc_text.tag_configure("body", font=("JetBrains Mono", 10),
                                    foreground=FG_TEXT, spacing1=2, lmargin1=10, lmargin2=10)
        self.doc_text.tag_configure("code", font=("JetBrains Mono", 10),
                                    foreground=FG_GREEN, background="#1a1a2e",
                                    lmargin1=30, lmargin2=30, spacing1=2)
        self.doc_text.tag_configure("highlight", background=FG_YELLOW, foreground=BG_DARK)
        self.doc_text.tag_configure("key", font=("JetBrains Mono", 10, "bold"),
                                    foreground=FG_YELLOW)

        self._load_docs()

    def _load_docs(self):
        self.sections = []
        self.section_indices = {}

        docs = self._get_documentation()

        self.doc_text.configure(state=tk.NORMAL)
        self.doc_text.delete("1.0", tk.END)

        for section in docs:
            title = section["title"]
            self.sections.append(title)
            self.toc_list.insert(tk.END, title)

            idx = self.doc_text.index(tk.END)
            self.section_indices[title] = idx

            if section.get("level") == 1:
                self.doc_text.insert(tk.END, title + "\n", "h1")
            else:
                self.doc_text.insert(tk.END, title + "\n", "h2")

            for block in section["content"]:
                if block["type"] == "text":
                    self.doc_text.insert(tk.END, block["text"] + "\n", "body")
                elif block["type"] == "code":
                    self.doc_text.insert(tk.END, block["text"] + "\n", "code")

            self.doc_text.insert(tk.END, "\n", "body")

        self.doc_text.configure(state=tk.DISABLED)

    def _on_toc_select(self, event=None):
        sel = self.toc_list.curselection()
        if not sel:
            return
        title = self.toc_list.get(sel[0])
        if title in self.section_indices:
            self.doc_text.see(self.section_indices[title])

    def _search(self, event=None):
        query = self.search_var.get().strip()
        if not query:
            return

        self.doc_text.tag_remove("highlight", "1.0", tk.END)

        start = "1.0"
        first_match = None
        while True:
            pos = self.doc_text.search(query, start, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self.doc_text.tag_add("highlight", pos, end)
            if first_match is None:
                first_match = pos
            start = end

        if first_match:
            self.doc_text.see(first_match)

    def _clear_search(self):
        self.search_var.set("")
        self.doc_text.tag_remove("highlight", "1.0", tk.END)

    def _get_documentation(self):
        """Return structured documentation content."""
        return [
            {
                "title": "Dilder DevTool",
                "level": 1,
                "content": [
                    {"type": "text", "text": (
                        "A development companion for the Pico W + Waveshare 2.13\" "
                        "e-ink display. Provides tools for drawing display images, "
                        "monitoring serial output, flashing firmware, managing assets, "
                        "and connecting over USB or Wi-Fi."
                    )},
                ],
            },
            {
                "title": "Display Emulator",
                "level": 2,
                "content": [
                    {"type": "text", "text": (
                        "A 250x122 pixel canvas that matches the real e-ink display exactly. "
                        "Everything is 1-bit monochrome — black or white only.\n\n"
                        "Tools:\n"
                        "  Pencil — freehand draw in black (click or drag)\n"
                        "  Eraser — freehand erase to white\n"
                        "  Line — click start, drag to end, release\n"
                        "  Rect — draw a rectangle outline\n"
                        "  Fill Rect — draw a filled rectangle\n"
                        "  Text — click a position, type text in the dialog\n\n"
                        "The Size spinner controls brush width and line thickness.\n"
                        "The Font spinner controls text size (8-48 px)."
                    )},
                    {"type": "text", "text": (
                        "Saving:\n"
                        "Click Save, enter a name. Three files are created in assets/:\n"
                        "  name.pbm — PBM binary (standard 1-bit image format)\n"
                        "  name.bin — raw bytes (direct display buffer for C code)\n"
                        "  name.png — PNG image (requires Pillow)\n\n"
                        "Loading:\n"
                        "Click Load to open any .pbm, .bin, or .png file back into the canvas."
                    )},
                    {"type": "text", "text": (
                        "Send to Pico:\n"
                        "Transmits the current image to the Pico W over USB serial. "
                        "Requires firmware that listens for the IMG: protocol."
                    )},
                ],
            },
            {
                "title": "Serial Monitor",
                "level": 2,
                "content": [
                    {"type": "text", "text": (
                        "Live serial terminal for the Pico W USB connection.\n\n"
                        "1. Select the port (auto-detects /dev/ttyACM0)\n"
                        "2. Set baud rate to 115200\n"
                        "3. Click Connect\n"
                        "4. printf() output from your firmware appears in real time"
                    )},
                    {"type": "text", "text": (
                        "Sending commands:\n"
                        "Type in the input bar and press Enter. Text is sent with \\r\\n.\n\n"
                        "Special buttons:\n"
                        "  Ctrl+C — interrupt running code\n"
                        "  Reset — soft-reset the Pico W (Ctrl+D)\n\n"
                        "Save Log saves the full output history to a text file."
                    )},
                ],
            },
            {
                "title": "Flash Firmware",
                "level": 2,
                "content": [
                    {"type": "text", "text": (
                        "Flash .uf2 firmware files to the Pico W.\n\n"
                        "Steps:\n"
                        "1. Select a .uf2 file (Browse or Quick Flash buttons)\n"
                        "2. Put Pico W in BOOTSEL mode:\n"
                        "   - Unplug USB\n"
                        "   - Hold BOOTSEL button\n"
                        "   - Plug in USB while holding\n"
                        "   - Release after 1 second\n"
                        "3. Click Detect RPI-RP2\n"
                        "4. Click Flash\n\n"
                        "The Pico W reboots automatically after flashing."
                    )},
                    {"type": "text", "text": (
                        "Build buttons:\n"
                        "Build Hello Serial and Build Hello Display run CMake + Ninja "
                        "directly. Output appears in the log bar. Requires the ARM "
                        "toolchain and PICO_SDK_PATH to be set."
                    )},
                ],
            },
            {
                "title": "Assets",
                "level": 2,
                "content": [
                    {"type": "text", "text": (
                        "Browse and manage display images saved in the assets/ folder.\n\n"
                        "Click a file to preview it at 2x scale. The preview shows "
                        "exactly how the image will look on the e-ink display.\n\n"
                        "Supported formats: .pbm, .bin, .png\n\n"
                        "Delete removes the selected file. Open Folder opens assets/ "
                        "in your system file manager."
                    )},
                ],
            },
            {
                "title": "GPIO Pins",
                "level": 2,
                "content": [
                    {"type": "text", "text": (
                        "Visual reference of the Pico W 40-pin header with all Dilder "
                        "project assignments. Shows display SPI1 pins, button pins, "
                        "power connections, and SPI configuration."
                    )},
                ],
            },
            {
                "title": "Connection Utility",
                "level": 2,
                "content": [
                    {"type": "text", "text": (
                        "Step-by-step walkthrough for connecting the Pico W.\n\n"
                        "USB Serial:\n"
                        "Guides you through plugging in, verifying the serial port, "
                        "checking permissions, and opening the serial monitor. "
                        "Each step has a Check button that verifies the current state.\n\n"
                        "Wi-Fi:\n"
                        "Explains how to add Wi-Fi to your firmware, provides the C "
                        "code and CMake config, and includes a TCP connection tester. "
                        "The Pico W supports 802.11n on 2.4 GHz."
                    )},
                ],
            },
            {
                "title": "Keyboard Shortcuts",
                "level": 2,
                "content": [
                    {"type": "text", "text": (
                        "Display Emulator:\n"
                        "  Left-click — draw/place with current tool\n"
                        "  Drag — freehand draw or shape preview\n"
                        "  Release — finalise shape (line/rect)\n\n"
                        "Serial Monitor:\n"
                        "  Enter — send command\n"
                        "  Ctrl+C button — interrupt\n"
                        "  Reset button — soft-reset (Ctrl+D)"
                    )},
                ],
            },
            {
                "title": "File Formats",
                "level": 2,
                "content": [
                    {"type": "text", "text": (
                        "PBM (P4 Binary):\n"
                        "Standard 1-bit image. Header + packed binary data.\n"
                        "Each byte = 8 pixels, MSB = leftmost. 1=black, 0=white."
                    )},
                    {"type": "code", "text": (
                        "P4\n"
                        "250 122\n"
                        "<3904 bytes of pixel data>"
                    )},
                    {"type": "text", "text": (
                        "BIN (Raw Display Buffer):\n"
                        "No header. 32 bytes/row x 122 rows = 3904 bytes.\n"
                        "Same byte layout as the Waveshare driver framebuffer.\n"
                        "Can be loaded directly in C code:"
                    )},
                    {"type": "code", "text": (
                        "const uint8_t img[3904] = { /* .bin contents */ };\n"
                        "EPD_2in13_V3_Display(img);"
                    )},
                    {"type": "text", "text": (
                        "PNG:\n"
                        "Standard 250x122 1-bit PNG. Requires Pillow to save/load."
                    )},
                ],
            },
            {
                "title": "Troubleshooting",
                "level": 2,
                "content": [
                    {"type": "text", "text": (
                        "tkinter not found:\n"
                        "  Arch: sudo pacman -S tk\n"
                        "  Debian: sudo apt install python3-tk\n\n"
                        "pyserial not found:\n"
                        "  sudo pacman -S python-pyserial  (Arch)\n"
                        "  pip install pyserial  (other)\n\n"
                        "Text tool renders blocks:\n"
                        "  Install Pillow: pip install Pillow\n\n"
                        "Serial monitor can't connect:\n"
                        "  Check USB cable is data-capable\n"
                        "  Check serial group: groups | grep uucp\n"
                        "  Check device exists: ls /dev/ttyACM*\n\n"
                        "Flash button says not detected:\n"
                        "  Put Pico W in BOOTSEL mode first\n"
                        "  (Hold BOOTSEL, plug in USB, release)\n\n"
                        "Canvas is slow with large fills:\n"
                        "  Tkinter draws individual rectangles per pixel.\n"
                        "  Brief lag on large operations is normal."
                    )},
                ],
            },
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Programs Tab — Deploy animated programs to emulator / Pico
# ─────────────────────────────────────────────────────────────────────────────

# ── Sassy Octopus pixel art (drawn on a 250x122 canvas) ──
# Chunky filled-style octopus on the left side with chat bubble on the right.

def _octo_body():
    """Return octopus body as list of (y, [(x0,x1), ...]) run-length pairs."""
    rows = []
    # Head dome (y 10..54)
    head = [
        (10, [(22, 48)]),
        (11, [(18, 52)]),
        (12, [(16, 54)]),
        (13, [(14, 56)]),
        (14, [(13, 57)]),
        (15, [(12, 58)]),
        (16, [(11, 59)]),
        (17, [(10, 60)]),
        (18, [(10, 60)]),
        (19, [(9, 61)]),
        (20, [(9, 61)]),
        (21, [(9, 61)]),
        (22, [(9, 61)]),
        (23, [(9, 61)]),
        (24, [(9, 61)]),
        (25, [(9, 61)]),
        (26, [(9, 61)]),
        (27, [(9, 61)]),
        (28, [(10, 60)]),
        (29, [(10, 60)]),
        (30, [(10, 60)]),
        (31, [(10, 60)]),
        (32, [(10, 60)]),
        (33, [(10, 60)]),
        (34, [(10, 60)]),
        (35, [(10, 60)]),
        (36, [(10, 60)]),
        (37, [(10, 60)]),
        (38, [(10, 60)]),
        (39, [(10, 60)]),
        (40, [(10, 60)]),
        (41, [(11, 59)]),
        (42, [(11, 59)]),
        (43, [(12, 58)]),
        (44, [(13, 57)]),
        (45, [(14, 56)]),
        # Cheeks bulge
        (46, [(12, 58)]),
        (47, [(11, 59)]),
        (48, [(10, 60)]),
        (49, [(10, 60)]),
        (50, [(11, 59)]),
        (51, [(12, 58)]),
        (52, [(13, 57)]),
        (53, [(14, 56)]),
        (54, [(15, 55)]),
    ]
    rows.extend(head)

    # 6 tentacle legs (y 55..85) — wavy appendages
    tentacles = [
        (55, [(10, 17), (21, 28), (32, 39), (43, 50), (54, 61)]),
        (56, [(8, 15), (19, 26), (30, 37), (45, 52), (56, 63)]),
        (57, [(7, 14), (18, 24), (29, 35), (47, 53), (58, 64)]),
        (58, [(6, 12), (19, 25), (31, 37), (46, 52), (57, 63)]),
        (59, [(7, 13), (21, 27), (33, 39), (44, 50), (55, 61)]),
        (60, [(8, 14), (20, 26), (31, 37), (43, 49), (54, 60)]),
        (61, [(9, 14), (18, 24), (30, 36), (44, 50), (56, 62)]),
        (62, [(8, 13), (17, 22), (31, 37), (46, 52), (57, 63)]),
        (63, [(7, 12), (18, 23), (33, 38), (45, 51), (55, 61)]),
        (64, [(8, 13), (20, 25), (32, 37), (43, 48), (54, 59)]),
        (65, [(9, 14), (19, 24), (30, 35), (44, 49), (55, 60)]),
        (66, [(10, 14), (17, 22), (31, 36), (46, 51), (57, 62)]),
        (67, [(9, 13), (18, 22), (33, 37), (45, 50), (56, 61)]),
        (68, [(8, 12), (19, 23), (32, 36), (43, 48), (54, 59)]),
        (69, [(9, 13), (21, 25), (30, 34), (44, 48), (55, 59)]),
        (70, [(10, 14), (20, 24), (31, 35), (46, 50), (57, 61)]),
        (71, [(11, 14), (18, 22), (33, 37), (45, 49), (56, 60)]),
        (72, [(10, 13), (19, 22), (32, 35), (43, 47), (54, 58)]),
        (73, [(9, 12), (20, 23), (30, 33), (44, 47), (55, 58)]),
        (74, [(10, 13), (21, 24), (31, 34), (46, 49), (57, 60)]),
        (75, [(11, 14), (20, 23), (33, 36), (45, 48), (56, 59)]),
        (76, [(12, 14), (19, 22), (32, 35), (43, 46), (54, 57)]),
        (77, [(11, 13), (20, 22), (30, 33), (44, 46), (55, 57)]),
        (78, [(10, 12), (21, 23), (31, 33), (45, 47), (56, 58)]),
        (79, [(11, 13), (22, 24), (32, 34), (44, 46), (55, 57)]),
        (80, [(12, 14), (21, 23), (33, 35), (43, 45), (54, 56)]),
    ]
    rows.extend(tentacles)
    return rows


def _octo_eyes():
    """Return eye pixel coords — two round white eyes."""
    eyes = []
    # Left eye (around x=22, y=25), Right eye (around x=48, y=25)
    for ecx in [22, 48]:
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                if dx * dx + dy * dy <= 16:
                    eyes.append((ecx + dx, 25 + dy))
    return eyes


def _octo_pupils():
    """Return pupil pixel coords — solid black dots offset down-right."""
    pupils = []
    for ecx in [23, 49]:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    pupils.append((ecx + dx, 26 + dy))
    return pupils


def _octo_highlights():
    """Return highlight pixel coords — white sparkle top-left of each pupil."""
    whites = []
    for ecx in [20, 46]:
        for dy in range(-1, 1):
            for dx in range(-1, 1):
                if dx * dx + dy * dy <= 1:
                    whites.append((ecx + dx, 23 + dy))
    return whites


def _octo_smirk():
    """Default smirk — a tilted half-circle smile, slightly off-angle.

    White interior with black outline, giving a sassy lopsided grin.
    Left side sits higher, right side dips lower.
    """
    outline = []
    interior = []
    cx, cy = 35, 39
    # Tilted arc: left side y-2, right side y+2
    for x in range(28, 44):
        t = (x - 28) / 15.0  # 0..1 across mouth
        # Tilt: left is higher, right is lower
        tilt = -2 + t * 4
        # Arc curve (half-circle shape)
        arc = 5 * (1.0 - (2 * t - 1) ** 2) ** 0.5 if abs(2 * t - 1) < 1 else 0
        y_center = cy + tilt + arc
        y_top = int(y_center - 1)
        y_bot = int(y_center + 1)
        # Outline (top and bottom of the arc band)
        outline.append((x, y_top))
        outline.append((x, y_bot))
        # Interior (white fill between)
        interior.append((x, int(y_center)))
    return outline, interior


def _octo_smile():
    """Big smile — a wide curved arc."""
    mouth = []
    for x in range(26, 45):
        cy = 38 + ((x - 35) ** 2) // 25
        mouth.append((x, cy))
        mouth.append((x, cy + 1))
    return mouth


def _octo_open_mouth():
    """Open mouth — an oval opening (border pixels only)."""
    cx, cy = 35, 40
    rx, ry = 7, 5
    border = []
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            inside = (dx * dx) * (ry * ry) + (dy * dy) * (rx * rx) <= (rx * rx) * (ry * ry)
            if inside:
                is_edge = False
                for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = dx + ndx, dy + ndy
                    if (nx * nx) * (ry * ry) + (ny * ny) * (rx * rx) > (rx * rx) * (ry * ry):
                        is_edge = True
                        break
                if is_edge:
                    border.append((cx + dx, cy + dy))
    return border


def _octo_open_mouth_interior():
    """Interior of open mouth (white fill)."""
    cx, cy = 35, 40
    rx, ry = 6, 4
    interior = []
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            if (dx * dx) * (ry * ry) + (dy * dy) * (rx * rx) <= (rx * rx) * (ry * ry):
                interior.append((cx + dx, cy + dy))
    return interior


# Mouth expression names used by the animation
MOUTH_SMIRK = "smirk"       # default: tilted half-circle, sassy
MOUTH_SMILE = "smile"       # big wide grin
MOUTH_OPEN  = "open"        # oval open mouth (talking)
MOUTH_WEIRD = "weird"       # wobbly sine-wave mouth, off-kilter
MOUTH_UNHINGED = "unhinged" # massive jagged scream-mouth
MOUTH_ANGRY = "angry"           # tight downward frown
MOUTH_SAD   = "sad"             # droopy downward curve
MOUTH_CHAOTIC = "chaotic"       # zigzag lightning-bolt mouth
MOUTH_HUNGRY = "hungry"         # drooling open mouth
MOUTH_TIRED = "tired"           # droopy yawn oval
MOUTH_SLAPHAPPY = "slaphappy"   # wide wobbly grin
MOUTH_LAZY = "lazy"             # flat horizontal line (minimal effort)
MOUTH_FAT = "fat"               # satisfied closed smile with cheek puffs
MOUTH_CHILL = "chill"           # slight asymmetric half-smile
MOUTH_HORNY = "horny"           # wide open smile with tongue out
MOUTH_EXCITED = "excited"       # wide open smile (bigger than normal)
MOUTH_NOSTALGIC = "nostalgic"   # gentle closed half-smile (wistful)
MOUTH_HOMESICK = "homesick"     # wobbly trying-not-to-cry line

# Cycle order for the animation per mood
MOUTH_CYCLE = [MOUTH_SMIRK, MOUTH_OPEN, MOUTH_SMILE, MOUTH_OPEN]
MOUTH_CYCLE_WEIRD = [MOUTH_WEIRD, MOUTH_OPEN, MOUTH_WEIRD, MOUTH_SMILE]
MOUTH_CYCLE_UNHINGED = [MOUTH_UNHINGED, MOUTH_OPEN, MOUTH_UNHINGED, MOUTH_OPEN]
MOUTH_CYCLE_ANGRY = [MOUTH_ANGRY, MOUTH_OPEN, MOUTH_ANGRY, MOUTH_ANGRY]
MOUTH_CYCLE_SAD = [MOUTH_SAD, MOUTH_OPEN, MOUTH_SAD, MOUTH_SMILE]
MOUTH_CYCLE_CHAOTIC = [MOUTH_CHAOTIC, MOUTH_OPEN, MOUTH_UNHINGED, MOUTH_WEIRD]
MOUTH_CYCLE_HUNGRY = [MOUTH_HUNGRY, MOUTH_OPEN, MOUTH_HUNGRY, MOUTH_SMILE]
MOUTH_CYCLE_TIRED = [MOUTH_TIRED, MOUTH_OPEN, MOUTH_TIRED, MOUTH_TIRED]
MOUTH_CYCLE_SLAPHAPPY = [MOUTH_SLAPHAPPY, MOUTH_OPEN, MOUTH_SLAPHAPPY, MOUTH_SMILE]
MOUTH_CYCLE_LAZY = [MOUTH_LAZY, MOUTH_LAZY, MOUTH_LAZY, MOUTH_OPEN]
MOUTH_CYCLE_FAT = [MOUTH_FAT, MOUTH_OPEN, MOUTH_FAT, MOUTH_SMILE]
MOUTH_CYCLE_CHILL = [MOUTH_CHILL, MOUTH_OPEN, MOUTH_CHILL, MOUTH_SMILE]
MOUTH_CYCLE_HORNY = [MOUTH_HORNY, MOUTH_OPEN, MOUTH_HORNY, MOUTH_SMILE]
MOUTH_CYCLE_EXCITED = [MOUTH_EXCITED, MOUTH_OPEN, MOUTH_EXCITED, MOUTH_SMILE]
MOUTH_CYCLE_NOSTALGIC = [MOUTH_NOSTALGIC, MOUTH_OPEN, MOUTH_NOSTALGIC, MOUTH_SMILE]
MOUTH_CYCLE_HOMESICK = [MOUTH_HOMESICK, MOUTH_OPEN, MOUTH_HOMESICK, MOUTH_HOMESICK]


def _octo_weird_mouth():
    """Wobbly sine-wave mouth — unsettling squiggle."""
    outline = []
    interior = []
    import math
    for x in range(24, 48):
        t = (x - 24) / 23.0
        # Sine wave wobble
        y_center = 39 + int(3.5 * math.sin(t * math.pi * 3))
        outline.append((x, y_center - 1))
        outline.append((x, y_center + 1))
        interior.append((x, y_center))
    return outline, interior


def _octo_unhinged_mouth():
    """Giant jagged scream-mouth — absolute chaos energy."""
    border = []
    cx, cy = 35, 41
    rx, ry = 10, 7
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            inside = (dx * dx) * (ry * ry) + (dy * dy) * (rx * rx) <= (rx * rx) * (ry * ry)
            if inside:
                is_edge = False
                for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = dx + ndx, dy + ndy
                    if (nx * nx) * (ry * ry) + (ny * ny) * (rx * rx) > (rx * rx) * (ry * ry):
                        is_edge = True
                        break
                if is_edge:
                    border.append((cx + dx, cy + dy))
    # Add jagged teeth along the top of the mouth
    for x in range(cx - 7, cx + 8, 3):
        border.append((x, cy - 5))
        border.append((x, cy - 4))
        border.append((x + 1, cy - 4))
    return border


def _octo_unhinged_mouth_interior():
    """Interior of unhinged mouth (white fill)."""
    cx, cy = 35, 41
    rx, ry = 9, 6
    interior = []
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            if (dx * dx) * (ry * ry) + (dy * dy) * (rx * rx) <= (rx * rx) * (ry * ry):
                interior.append((cx + dx, cy + dy))
    return interior


def _octo_weird_eyes():
    """Misaligned pupils for the weird expression — one looks up, one looks down."""
    pupils = []
    # Left eye pupil: shifted up-left
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                pupils.append((21 + dx, 24 + dy))
    # Right eye pupil: shifted down-right
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                pupils.append((50 + dx, 28 + dy))
    return pupils


def _octo_unhinged_eyes():
    """Tiny pinprick pupils for the unhinged expression — maximum unhinged energy."""
    pupils = []
    for ecx in [22, 48]:
        pupils.append((ecx, 25))
        pupils.append((ecx + 1, 25))
        pupils.append((ecx, 26))
        pupils.append((ecx + 1, 26))
    return pupils


def _octo_angry_eyes():
    """Angry slanted half-circle eyebrows above the eyes.

    Each brow is a thick curved arc that slopes inward — outer edge high,
    inner edge low, creating a classic angry V-furrowed look. The arcs are
    half-ellipses tilted at an angle, 3px thick.
    """
    import math
    brows = []

    # Brows sit across the TOP of the white eye sockets (eyes are at y=25,
    # sockets extend from ~y=21 to ~y=29). We draw thick arcs from y=19 to y=22
    # that cut across the top of the white area so they're clearly visible
    # against the white eye background.

    # Brows cut across the white eye sockets. Eyes are circles at y=25
    # with radius 4, so white area is y=21..29.  We draw thick slanted
    # arcs from y=21 to y=24 so they're bold across the top of the whites.

    # Left eyebrow: outer high (y=20), inner low (y=25) — angry V slope
    for i in range(18):
        t = i / 17.0
        x = 14 + t * 16      # x: 14 → 30  (spans full eye width + overhang)
        arc = 2.5 * math.sin(t * math.pi)
        slant_y = 20 + t * 5  # baseline: 20 → 25
        y = slant_y - arc
        ix, iy = int(x), int(y)
        for dy in range(3):  # 3px thick
            brows.append((ix, iy + dy))
        brows.append((ix + 1, iy + 1))  # extra width

    # Right eyebrow: mirror — inner low (y=25), outer high (y=20)
    for i in range(18):
        t = i / 17.0
        x = 40 + t * 16      # x: 40 → 56
        arc = 2.5 * math.sin(t * math.pi)
        slant_y = 25 - t * 5  # baseline: 25 → 20
        y = slant_y - arc
        ix, iy = int(x), int(y)
        for dy in range(3):
            brows.append((ix, iy + dy))
        brows.append((ix + 1, iy + 1))

    return brows


def _octo_angry_pupils():
    """Angry pupils — shifted inward for a glaring look."""
    pupils = []
    # Left eye: shifted right (glaring inward)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                pupils.append((25 + dx, 26 + dy))
    # Right eye: shifted left (glaring inward)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                pupils.append((47 + dx, 26 + dy))
    return pupils


def _octo_sad_eyes():
    """Sad droopy eyebrows — two angled lines slanting downward at the outer edges.

    Returns eyebrow pixels (the inverse of angry — outer edges droop down).
    """
    brows = []
    # Left eyebrow: slants down from inner to outer  (\ shape)
    for i in range(10):
        x = 15 + i
        y = 15 + i * 4 // 10
        brows.append((x, y))
        brows.append((x, y + 1))
    # Right eyebrow: slants down from inner to outer  (/ shape)
    for i in range(10):
        x = 45 + i
        y = 17 - i * 4 // 10
        brows.append((x, y))
        brows.append((x, y + 1))
    return brows


def _octo_sad_pupils():
    """Sad pupils — shifted downward, looking at the floor."""
    pupils = []
    for ecx in [23, 49]:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    pupils.append((ecx + dx, 28 + dy))  # lower than normal
    return pupils


def _octo_chaotic_eyes():
    """Chaotic spiral eyes — concentric circles giving a dizzy look.

    Returns pixels that replace the normal pupils with spiral/ring pattern.
    """
    pupils = []
    for ecx in [22, 48]:
        # Outer ring
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                dist = dx * dx + dy * dy
                if 5 <= dist <= 9:
                    pupils.append((ecx + dx, 25 + dy))
        # Center dot
        pupils.append((ecx, 25))
    return pupils


def _octo_angry_mouth():
    """Tight angry frown — a downward curve."""
    mouth = []
    for x in range(28, 43):
        cy = 40 - ((x - 35) ** 2) // 20  # inverted parabola = frown
        mouth.append((x, cy))
        mouth.append((x, cy + 1))
    return mouth


def _octo_sad_mouth():
    """Sad frown — a gentle downward curve, wider than angry."""
    mouth = []
    for x in range(26, 45):
        cy = 42 - ((x - 35) ** 2) // 30  # gentle frown
        mouth.append((x, cy))
        mouth.append((x, cy + 1))
    return mouth


def _octo_chaotic_mouth():
    """Zigzag lightning-bolt mouth — pure chaos energy."""
    import math
    mouth = []
    for x in range(24, 48):
        # Sharp zigzag
        phase = (x - 24) % 6
        if phase < 3:
            y = 38 + phase * 2
        else:
            y = 44 - phase * 2 + 6
        mouth.append((x, y))
        mouth.append((x, y + 1))
    return mouth


def _octo_hungry_eyes():
    """Hungry eyes — pupils shifted upward, looking at imaginary food above."""
    pupils = []
    for ecx in [23, 49]:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    pupils.append((ecx + dx, 23 + dy))  # shifted up
    return pupils


def _octo_hungry_mouth():
    """Drooling open mouth — wide oval with drool drops below."""
    mouth = []
    # Wide open oval
    cx, cy = 35, 40
    rx, ry = 8, 5
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            inside = (dx * dx) * (ry * ry) + (dy * dy) * (rx * rx) <= (rx * rx) * (ry * ry)
            if inside:
                is_edge = False
                for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = dx + ndx, dy + ndy
                    if (nx * nx) * (ry * ry) + (ny * ny) * (rx * rx) > (rx * rx) * (ry * ry):
                        is_edge = True
                        break
                if is_edge:
                    mouth.append(("set", cx + dx, cy + dy))
                else:
                    mouth.append(("clr", cx + dx, cy + dy))
    # Drool drops
    for dy in range(1, 6):
        mouth.append(("set", 33, cy + ry + dy))
        if dy < 4:
            mouth.append(("set", 37, cy + ry + dy + 1))
    return mouth


def _octo_tired_eyes():
    """Tired half-closed eyes — horizontal lines replacing the round pupils.

    Returns (lids, pupils) where lids are black pixels that cover the top
    half of the eye sockets, making them look droopy/half-shut.
    """
    lids = []
    # Cover top half of each eye socket with black (half-closed)
    for ecx in [22, 48]:
        for dy in range(-4, -1):  # top portion of the eye
            for dx in range(-4, 5):
                if dx * dx + dy * dy <= 16:
                    lids.append((ecx + dx, 25 + dy))
    return lids


def _octo_tired_pupils():
    """Tiny sleepy pupils — small and low in the half-closed eyes."""
    pupils = []
    for ecx in [22, 48]:
        for dx in range(-1, 2):
            pupils.append((ecx + dx, 27))
            pupils.append((ecx + dx, 28))
    return pupils


def _octo_tired_mouth():
    """Yawn mouth — tall oval, open wide vertically."""
    mouth = []
    cx, cy = 35, 40
    rx, ry = 5, 7  # taller than wide
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            inside = (dx * dx) * (ry * ry) + (dy * dy) * (rx * rx) <= (rx * rx) * (ry * ry)
            if inside:
                is_edge = False
                for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = dx + ndx, dy + ndy
                    if (nx * nx) * (ry * ry) + (ny * ny) * (rx * rx) > (rx * rx) * (ry * ry):
                        is_edge = True
                        break
                if is_edge:
                    mouth.append(("set", cx + dx, cy + dy))
                else:
                    mouth.append(("clr", cx + dx, cy + dy))
    return mouth


def _octo_slaphappy_eyes():
    """Slap-happy eyes — one eye squished shut (line), one wide open.

    Returns extra pixels: left eye is a horizontal squint line,
    right eye has an oversized pupil (giddy/manic look).
    """
    # Left eye: squint shut — fill the white socket back to black,
    # then draw a horizontal line
    squint = []
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if dx * dx + dy * dy <= 16:
                squint.append(("fill", 22 + dx, 25 + dy))  # close left eye
    # Squint line (white slit)
    for dx in range(-3, 4):
        squint.append(("clr", 22 + dx, 25))
    # Right eye: oversized pupil (giddy)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if dx * dx + dy * dy <= 9:
                squint.append(("set", 49 + dx, 26 + dy))
    return squint


def _octo_slaphappy_mouth():
    """Wide wobbly grin — big smile with a slight sine wobble."""
    import math
    mouth = []
    for x in range(22, 49):
        t = (x - 22) / 26.0
        base = 38 + ((x - 35) ** 2) // 20
        wobble = int(1.5 * math.sin(t * math.pi * 4))
        y = base + wobble
        mouth.append((x, y))
        mouth.append((x, y + 1))
    return mouth


def _octo_lazy_eyes():
    """Lazy half-lidded eyes — even more closed than tired, tiny slit at bottom.

    Returns (lids, pupils) where lids cover most of the eye socket.
    """
    lids = []
    # Cover most of each eye socket with black (barely open slit at bottom)
    for ecx in [22, 48]:
        for dy in range(-4, 2):  # cover top + middle, leave only bottom sliver
            for dx in range(-4, 5):
                if dx * dx + dy * dy <= 16:
                    lids.append((ecx + dx, 25 + dy))
    return lids


def _octo_lazy_pupils():
    """Barely visible dots low in the slit for lazy eyes."""
    pupils = []
    for ecx in [22, 48]:
        pupils.append((ecx, 28))
        pupils.append((ecx + 1, 28))
    return pupils


def _octo_lazy_mouth():
    """Flat horizontal line mouth — minimal effort."""
    mouth = []
    for x in range(29, 42):
        mouth.append((x, 40))
        mouth.append((x, 41))
    return mouth


def _octo_fat_pupils():
    """Fat/content eyes — wider pupils (happy and satisfied)."""
    pupils = []
    for ecx in [23, 49]:
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if dx * dx + dy * dy <= 9:
                    pupils.append((ecx + dx, 26 + dy))
    return pupils


def _octo_fat_mouth():
    """Satisfied closed smile with puffed cheeks — wider smile + cheek circles."""
    mouth = []
    # Wide satisfied smile (upward curve, wider than normal)
    for x in range(24, 47):
        cy = 38 + ((x - 35) ** 2) // 18
        mouth.append((x, cy))
        mouth.append((x, cy + 1))
    # Cheek puffs — small filled circles on each side
    for cx, cy in [(23, 39), (47, 39)]:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    mouth.append((cx + dx, cy + dy))
    return mouth


def _octo_chill_pupils():
    """Chill eyes — pupils slightly looking to the side (cool/unbothered)."""
    pupils = []
    # Left eye: shifted right
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                pupils.append((25 + dx, 26 + dy))
    # Right eye: also shifted right (both looking same direction)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                pupils.append((51 + dx, 26 + dy))
    return pupils


def _octo_chill_mouth():
    """Slight asymmetric half-smile — relaxed smirk, flatter than normal."""
    mouth = []
    for x in range(29, 44):
        t = (x - 29) / 14.0
        # Flat on the left, slight uptick on the right — relaxed asymmetry
        y = 40 + int(1.5 * t * t)
        mouth.append((x, y))
        mouth.append((x, y + 1))
    return mouth


def _octo_horny_pupils():
    """Heart-shaped pupils — small diamond/V shapes in each eye socket."""
    pupils = []
    for ecx in [22, 48]:
        # Heart shape: two bumps on top, point at bottom
        # Top bumps
        for dx, dy in [(-2, -1), (-1, -2), (0, -1), (1, -2), (2, -1)]:
            pupils.append((ecx + dx, 25 + dy))
        # Middle
        for dx in range(-2, 3):
            pupils.append((ecx + dx, 25))
        # Lower taper
        for dx in range(-1, 2):
            pupils.append((ecx + dx, 26))
        # Bottom point
        pupils.append((ecx, 27))
    return pupils


def _octo_horny_mouth():
    """Wide open smile with tongue hanging out.

    Returns list of (op, x, y) tuples — 'set' for border, 'clr' for interior.
    """
    mouth = []
    # Wide open happy mouth (half-circle, open at bottom)
    cx, cy = 35, 39
    rx, ry = 8, 5
    for dy in range(0, ry + 1):  # only bottom half (smile)
        for dx in range(-rx, rx + 1):
            inside = (dx * dx) * (ry * ry) + (dy * dy) * (rx * rx) <= (rx * rx) * (ry * ry)
            if inside:
                is_edge = False
                for ndx, ndy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = dx + ndx, dy + ndy
                    if ny < 0:
                        continue  # top edge is the flat line
                    if (nx * nx) * (ry * ry) + (ny * ny) * (rx * rx) > (rx * rx) * (ry * ry):
                        is_edge = True
                        break
                if is_edge or dy == 0:
                    mouth.append(("set", cx + dx, cy + dy))
                else:
                    mouth.append(("clr", cx + dx, cy + dy))
    # Tongue hanging out the bottom
    for dy in range(1, 5):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 8:
                mouth.append(("set", cx + dx, cy + ry + dy))
    # Tongue interior (pink = white on e-ink)
    for dy in range(2, 4):
        for dx in range(-1, 2):
            mouth.append(("clr", cx + dx, cy + ry + dy))
    return mouth


def _octo_excited_pupils():
    """Star/sparkle pupils — small cross/plus shape in each eye socket."""
    pupils = []
    for ecx in [22, 48]:
        # Plus/cross shape centered at (ecx, 25)
        for d in range(-2, 3):
            pupils.append((ecx + d, 25))   # horizontal bar
            pupils.append((ecx, 25 + d))   # vertical bar
        # Diagonal tips for sparkle
        pupils.append((ecx - 1, 25 - 1))
        pupils.append((ecx + 1, 25 - 1))
        pupils.append((ecx - 1, 25 + 1))
        pupils.append((ecx + 1, 25 + 1))
    return pupils


def _octo_excited_mouth():
    """Wide open smile — bigger upward curve than normal smile."""
    mouth = []
    # Wide upward curve (wider and more dramatic than smile)
    for x in range(22, 49):
        cy = 37 + ((x - 35) ** 2) // 12
        mouth.append((x, cy))
        mouth.append((x, cy + 1))
    return mouth


def _octo_nostalgic_pupils():
    """Pupils looking upward and to the right — remembering."""
    pupils = []
    # Left eye: shifted up-right
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                pupils.append((24 + dx, 23 + dy))
    # Right eye: also shifted up-right
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                pupils.append((50 + dx, 23 + dy))
    return pupils


def _octo_nostalgic_mouth():
    """Gentle closed half-smile — small, wistful."""
    mouth = []
    # Short, gentle upward curve (smaller than normal smile)
    for x in range(31, 40):
        t = (x - 31) / 8.0
        y = 40 + int(1.5 * (2 * t - 1) ** 2)
        mouth.append((x, y))
        mouth.append((x, y + 1))
    return mouth


def _octo_homesick_pupils():
    """Slightly watery/teary eyes — like sad but with tear drop pixels.

    Returns (pupils, tears) where tears are drawn after eyes/highlights.
    """
    pupils = []
    # Normal-ish pupils (slightly lowered, sad-like)
    for ecx in [23, 49]:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    pupils.append((ecx + dx, 27 + dy))
    return pupils


def _octo_homesick_tears():
    """Tear drop pixels below each eye socket."""
    tears = []
    for ecx in [22, 48]:
        # Small tear drop below each eye
        tears.append((ecx, 31))
        tears.append((ecx, 32))
        tears.append((ecx, 33))
        tears.append((ecx - 1, 32))
        tears.append((ecx + 1, 32))
    return tears


def _octo_homesick_mouth():
    """Wobbly trying-not-to-cry line — slightly wavy horizontal line."""
    mouth = []
    import math
    for x in range(28, 43):
        t = (x - 28) / 14.0
        y = 40 + int(1.5 * math.sin(t * math.pi * 3))
        mouth.append((x, y))
        mouth.append((x, y + 1))
    return mouth


def _parse_quote(q):
    """Normalize a quote entry — either 'TEXT' or ('TEXT', 'mood')."""
    if isinstance(q, tuple):
        return q[0], q[1]
    return q, None


def _mood_cycle(mood):
    """Return the MOUTH_CYCLE for a given mood."""
    if mood == "weird":
        return MOUTH_CYCLE_WEIRD
    if mood == "unhinged":
        return MOUTH_CYCLE_UNHINGED
    if mood == "angry":
        return MOUTH_CYCLE_ANGRY
    if mood == "sad":
        return MOUTH_CYCLE_SAD
    if mood == "chaotic":
        return MOUTH_CYCLE_CHAOTIC
    if mood == "hungry":
        return MOUTH_CYCLE_HUNGRY
    if mood == "tired":
        return MOUTH_CYCLE_TIRED
    if mood == "slaphappy":
        return MOUTH_CYCLE_SLAPHAPPY
    if mood == "lazy":
        return MOUTH_CYCLE_LAZY
    if mood == "fat":
        return MOUTH_CYCLE_FAT
    if mood == "chill":
        return MOUTH_CYCLE_CHILL
    if mood == "horny":
        return MOUTH_CYCLE_HORNY
    if mood == "excited":
        return MOUTH_CYCLE_EXCITED
    if mood == "nostalgic":
        return MOUTH_CYCLE_NOSTALGIC
    if mood == "homesick":
        return MOUTH_CYCLE_HOMESICK
    return MOUTH_CYCLE


def _draw_chat_bubble(pixels, text, tagline="~ SASSY OCTOPUS ~", y_offset=0):
    """Draw a speech bubble to the right of the octopus with wrapped text."""
    bx = 75
    by = 5 + y_offset
    bw, bh = 170, 70

    # Bubble outline (double-thick)
    for x in range(bx + 3, bx + bw - 3):
        if 0 <= by < DISPLAY_H:
            pixels[by][x] = 1
        if 0 <= by + 1 < DISPLAY_H:
            pixels[by + 1][x] = 1
        if 0 <= by + bh - 1 < DISPLAY_H:
            pixels[by + bh - 1][x] = 1
        if 0 <= by + bh - 2 < DISPLAY_H:
            pixels[by + bh - 2][x] = 1
    for y in range(by + 3, by + bh - 3):
        if 0 <= y < DISPLAY_H:
            pixels[y][bx] = 1
            pixels[y][bx + 1] = 1
            pixels[y][bx + bw - 1] = 1
            pixels[y][bx + bw - 2] = 1
    # Rounded corners
    for cx, cy in [(bx + 2, by + 2), (bx + bw - 3, by + 2),
                   (bx + 2, by + bh - 3), (bx + bw - 3, by + bh - 3)]:
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if abs(dx) + abs(dy) <= 1:
                    if 0 <= cy + dy < DISPLAY_H and 0 <= cx + dx < DISPLAY_W:
                        pixels[cy + dy][cx + dx] = 1

    # Speech tail pointing left toward octopus mouth
    tail_base_y = 35 + y_offset
    tail_points = [
        (bx, tail_base_y), (bx - 1, tail_base_y + 1),
        (bx - 2, tail_base_y + 2), (bx - 3, tail_base_y + 3),
        (bx - 4, tail_base_y + 4), (bx - 5, tail_base_y + 5),
        (bx - 6, tail_base_y + 6), (bx - 7, tail_base_y + 7),
        (bx - 6, tail_base_y + 8), (bx - 5, tail_base_y + 8),
        (bx - 4, tail_base_y + 8), (bx - 3, tail_base_y + 7),
        (bx - 2, tail_base_y + 6), (bx - 1, tail_base_y + 5),
        (bx, tail_base_y + 4),
    ]
    for tx, ty in tail_points:
        if 0 <= ty < DISPLAY_H and 0 <= tx < DISPLAY_W:
            pixels[ty][tx] = 1

    # Render text inside bubble using built-in bitmap font
    _render_tiny_text(pixels, bx + 6, by + 6, text, bw - 12)

    # Tagline at bottom
    tag_y = by + bh + 5
    if tag_y + 7 < DISPLAY_H:
        _render_tiny_text(pixels, bx + 6, tag_y, tagline, bw)


# Tiny 5x7 bitmap font for rendering text without Pillow
_TINY_FONT = {}

def _init_tiny_font():
    """Initialize a minimal 5-wide bitmap font (uppercase + basic punctuation)."""
    if _TINY_FONT:
        return
    glyphs = {
        'A': ["01110","10001","10001","11111","10001","10001","10001"],
        'B': ["11110","10001","10001","11110","10001","10001","11110"],
        'C': ["01110","10001","10000","10000","10000","10001","01110"],
        'D': ["11110","10001","10001","10001","10001","10001","11110"],
        'E': ["11111","10000","10000","11110","10000","10000","11111"],
        'F': ["11111","10000","10000","11110","10000","10000","10000"],
        'G': ["01110","10001","10000","10111","10001","10001","01110"],
        'H': ["10001","10001","10001","11111","10001","10001","10001"],
        'I': ["11111","00100","00100","00100","00100","00100","11111"],
        'J': ["00111","00010","00010","00010","00010","10010","01100"],
        'K': ["10001","10010","10100","11000","10100","10010","10001"],
        'L': ["10000","10000","10000","10000","10000","10000","11111"],
        'M': ["10001","11011","10101","10101","10001","10001","10001"],
        'N': ["10001","10001","11001","10101","10011","10001","10001"],
        'O': ["01110","10001","10001","10001","10001","10001","01110"],
        'P': ["11110","10001","10001","11110","10000","10000","10000"],
        'Q': ["01110","10001","10001","10001","10101","10010","01101"],
        'R': ["11110","10001","10001","11110","10100","10010","10001"],
        'S': ["01110","10001","10000","01110","00001","10001","01110"],
        'T': ["11111","00100","00100","00100","00100","00100","00100"],
        'U': ["10001","10001","10001","10001","10001","10001","01110"],
        'V': ["10001","10001","10001","10001","01010","01010","00100"],
        'W': ["10001","10001","10001","10101","10101","10101","01010"],
        'X': ["10001","10001","01010","00100","01010","10001","10001"],
        'Y': ["10001","10001","01010","00100","00100","00100","00100"],
        'Z': ["11111","00001","00010","00100","01000","10000","11111"],
        '0': ["01110","10001","10011","10101","11001","10001","01110"],
        '1': ["00100","01100","00100","00100","00100","00100","01110"],
        '2': ["01110","10001","00001","00110","01000","10000","11111"],
        '3': ["01110","10001","00001","00110","00001","10001","01110"],
        '4': ["00010","00110","01010","10010","11111","00010","00010"],
        '5': ["11111","10000","11110","00001","00001","10001","01110"],
        '6': ["01110","10001","10000","11110","10001","10001","01110"],
        '7': ["11111","00001","00010","00100","01000","01000","01000"],
        '8': ["01110","10001","10001","01110","10001","10001","01110"],
        '9': ["01110","10001","10001","01111","00001","10001","01110"],
        ' ': ["00000","00000","00000","00000","00000","00000","00000"],
        '.': ["00000","00000","00000","00000","00000","01100","01100"],
        ',': ["00000","00000","00000","00000","00100","00100","01000"],
        '!': ["00100","00100","00100","00100","00100","00000","00100"],
        '?': ["01110","10001","00001","00110","00100","00000","00100"],
        "'": ["00100","00100","01000","00000","00000","00000","00000"],
        '"': ["01010","01010","10100","00000","00000","00000","00000"],
        '-': ["00000","00000","00000","11111","00000","00000","00000"],
        '~': ["00000","00000","01000","10101","00010","00000","00000"],
        '/': ["00001","00010","00010","00100","01000","01000","10000"],
        '(': ["00010","00100","01000","01000","01000","00100","00010"],
        ')': ["01000","00100","00010","00010","00010","00100","01000"],
        ':': ["00000","01100","01100","00000","01100","01100","00000"],
        '%': ["11001","11010","00010","00100","01000","01011","10011"],
    }
    for ch, rows in glyphs.items():
        _TINY_FONT[ch] = rows


def _render_tiny_text(pixels, x0, y0, text, max_width):
    """Render text into pixel buffer using the tiny bitmap font.
    Wraps words to fit within max_width pixels."""
    _init_tiny_font()
    char_w = 6  # 5px glyph + 1px spacing
    line_h = 9  # 7px glyph + 2px spacing
    chars_per_line = max(1, max_width // char_w)

    # Word-wrap
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip() if current else word
        if len(test) <= chars_per_line:
            current = test
        else:
            if current:
                lines.append(current)
            current = word[:chars_per_line]  # truncate long words
    if current:
        lines.append(current)

    for line_idx, line in enumerate(lines):
        cy = y0 + line_idx * line_h
        if cy + 7 >= DISPLAY_H:
            break
        for ci, ch in enumerate(line):
            cx = x0 + ci * char_w
            if cx + 5 >= DISPLAY_W:
                break
            glyph = _TINY_FONT.get(ch.upper(), _TINY_FONT.get(' '))
            if glyph:
                for row_idx, row in enumerate(glyph):
                    for col_idx, bit in enumerate(row):
                        if bit == '1':
                            px, py = cx + col_idx, cy + row_idx
                            if 0 <= px < DISPLAY_W and 0 <= py < DISPLAY_H:
                                pixels[py][px] = 1


SASSY_QUOTES = [
    # ── Classic sassy nonsense ──
    "WIFI IS JUST SPICY AIR.",
    "FISH ARE JUST WET BIRDS.",
    "I DONT HAVE BONES AND THATS A FLEX.",
    "MATTRESSES ARE BODY SHELVES.",
    "THE OCEAN IS JUST SKY JUICE.",
    "SLEEP IS FREE DEATH TRIAL.",
    "STAIRS ARE JUST BROKEN ESCALATORS.",
    "THE FLOOR IS JUST A BIG SHELF.",
    "DOORS ARE WALLS THAT GAVE UP.",
    "EGGS ARE JUST BONELESS CHICKENS.",
    "IM 90% WATER. IM BASICALLY A SPLASH.",
    "SAND IS JUST ANGRY ROCKS.",
    "TREES ARE JUST GROUND HAIR.",
    "LAVA IS JUST EARTH SAUCE.",
    "MATH IS JUST SPICY COUNTING.",
    "SOCKS ARE JUST FOOT PRISONS.",
    "A BURRITO IS A SLEEPING BAG FOR FOOD.",
    "INK IS MY DEFENSE MECHANISM. AND COMEDY.",
    "8 ARMS AND ZERO PATIENCE.",
    "SPAGHETTI IS JUST BONELESS TENTACLES.",
    "JELLYFISH ARE JUST OCEAN GHOSTS.",
    "I HUG THINGS 4X BETTER THAN YOU.",
    "BLANKETS ARE JUST ADULT SWADDLES.",
    "POCKETS ARE JUST BUILT IN BAGS.",
    "CLAPPING IS JUST HITTING YOURSELF BECAUSE YOU LIKE SOMETHING.",
    "A PILLOW IS JUST A SOFT RECTANGLE YOU DROOL ON.",
    "SHOES ARE JUST OUTDOOR SOCKS WITH AMBITION.",
    "CANDLES ARE JUST FANCY FIRE STICKS FOR SAD PEOPLE.",
    "A LAWN IS JUST A CARPET THAT NEEDS WATER.",
    "UNDERWEAR IS JUST A SECOND SKIN YOU CHOSE.",
    "TEETH ARE THE ONLY BONES YOU HAVE TO BRUSH.",
    "SWEATING IS YOUR BODY CRYING BECAUSE YOU MOVED TOO MUCH.",
    "HAIR IS JUST HEAD STRINGS.",
    "A WALLET IS JUST A POCKET FOR YOUR POCKET.",
    "EYEBROWS ARE JUST FOREHEAD MUSTACHES.",
    "NOSES ARE JUST FACE HANDLES.",
    "TOENAILS ARE JUST FOOT CHIPS.",
    "A GARAGE IS A HOUSE FOR YOUR CAR. YOUR CAR HAS A HOUSE.",
    "COTTON CANDY IS JUST EDIBLE INSULATION.",
    "A CEMETERY IS JUST A PEOPLE GARDEN.",
    "NIPPLES ARE JUST CHEST BUTTONS THAT DO NOTHING.",
    "A CALENDAR IS JUST A COUNTDOWN TO YOUR DEATH WITH PICTURES.",
    # ── Spicy sassy ──
    "IM TOO PRETTY FOR THIS DAMN OCEAN.",
    "DONT TALK TO ME BEFORE MY KELP COFFEE.",
    "I DIDNT ASK TO BE THIS FABULOUS.",
    "CATCH ME OUTSIDE THE REEF. HOW BOUT DAT.",
    "YOUR OPINION MEANS LESS THAN PLANKTON TO ME.",
    "SORRY CANT HEAR YOU OVER MY 8 ARM ENERGY.",
    "WHAT THE SHELL DID YOU JUST SAY TO ME.",
    "YOURE ABOUT AS USEFUL AS A SCREEN DOOR ON A SUBMARINE.",
    "I HAVE 3 HEARTS AND NONE OF THEM CARE.",
    "BOLD WORDS FROM SOMEONE WITH ONLY 2 ARMS.",
    "OH HELL NO. ABSOLUTELY NOT. NEXT.",
    "THE AUDACITY. THE DAMN AUDACITY.",
    "I DIDNT CRAWL OUT OF THE PRIMORDIAL OOZE FOR THIS BULLSHIT.",
    "TALK TO THE TENTACLE CAUSE THE FACE AINT LISTENING.",
    "I HAVE MORE ARMS THAN YOU HAVE BRAIN CELLS.",
    "YOURE GIVING OFF STRONG BARNACLE ENERGY RIGHT NOW.",
    "IM NOT BEING RUDE IM BEING EFFICIENT WITH MY DISGUST.",
    "I COULD MULTITASK CIRCLES AROUND YOUR ENTIRE FAMILY.",
    "MY RESTING FACE HAS MORE PERSONALITY THAN YOUR BEST DAY.",
    "I DIDNT CHOOSE THE TENTACLE LIFE. IT CHOSE ME AND I SLAYED.",
    "IM NOT ARGUING IM JUST EXPLAINING WHY YOURE WRONG. WITH 8 ARMS.",
    "SIT DOWN. I SAID SIT. GOOD. NOW LISTEN.",
    "IMAGINE BEING THAT CONFIDENT WITH ONLY 4 LIMBS.",
    "I COULD OUT-SASS A SEA CUCUMBER AND THOSE THINGS LITERALLY EXPEL THEIR GUTS.",
    # ── Chaotic stupid ──
    "WHAT IF YOUR LEGS DIDNT KNOW THEY WERE LEGS.",
    "I JUST REALIZED WATER IS BONELESS ICE.",
    "EVERY ROOM IS AN ESCAPE ROOM IF YOU SUCK.",
    "CORN IS JUST FRUIT WITH EXTRA STEPS.",
    "SOUP IS JUST WET SALAD. FIGHT ME.",
    "ELEVATORS ARE JUST ROOMS THAT MOVE. WHAT THE HELL.",
    "COFFINS ARE UNDERGROUND TINY HOMES.",
    "A FLY WITHOUT WINGS IS JUST A WALK.",
    "GLOVES ARE JUST HAND SOCKS. HAND. SOCKS.",
    "A KEYBOARD IS JUST AN ORGANIZED ALPHABET.",
    "THE SUN IS A DEADLY LAZER BUT WE JUST VIBE.",
    "IF NOTHING IS IMPOSSIBLE THEN IS IT POSSIBLE FOR SOMETHING TO BE IMPOSSIBLE.",
    "WHAT IF OXYGEN IS ACTUALLY POISONOUS AND JUST TAKES 80 YEARS TO KILL US.",
    "WHEN YOU CLEAN A VACUUM CLEANER YOU BECOME THE VACUUM CLEANER.",
    "YOUR AGE IS JUST THE NUMBER OF LAPS YOUVE DONE AROUND A GIANT FIREBALL.",
    "A DENTIST APPOINTMENT IS JUST PAYING SOMEONE TO FINGERBANG YOUR MOUTH.",
    "MAYBE DOGS FETCH THE BALL BECAUSE THEY THINK YOU LIKE THROWING IT.",
    "WHAT IF PLANTS ARE FARMING US BY GIVING US OXYGEN UNTIL WE DECOMPOSE.",
    "A BOOMERANG THAT DOESNT COME BACK IS JUST A STICK.",
    "WHOEVER NAMED THE FIREPLACE REALLY WASNT TRYING THAT HARD.",
    "A SUNSET IS JUST THE SUN RAGE QUITTING FOR THE DAY.",
    "THE FIRST PERSON TO HEAR A PARROT TALK MUST HAVE LOST THEIR DAMN MIND.",
    "A PAPER CUT IS A TREES LAST REVENGE.",
    "THE PERSON WHO DISCOVERED MILK WAS DOING SOMETHING DEEPLY SUSPICIOUS TO THAT COW.",
    # ── Unhinged ocean takes ──
    ("THE MARIANA TRENCH IS WHERE GOD DROPPED HIS KEYS.", "unhinged"),
    ("THERE ARE THINGS IN THE DEEP OCEAN THAT WOULD MAKE GOD CRY.", "unhinged"),
    ("THE OCEAN IS JUST A BIG ASS SOUP AND WERE ALL CROUTONS.", "unhinged"),
    ("ANGLERFISH INVENTED CATFISHING AND NOBODY GIVES THEM CREDIT.", "unhinged"),
    ("WHALES ARE JUST FAT SUBMARINES CHANGE MY DAMN MIND.", "unhinged"),
    ("THE KRAKEN IS REAL AND ITS MY COUSIN STEVE.", "unhinged"),
    ("CORAL REEFS ARE JUST UNDERWATER CITIES WE KEEP MURDERING.", "unhinged"),
    ("DOLPHINS ARE PSYCHOPATHS WITH GOOD PR.", "unhinged"),
    ("SHRIMP ON A TREADMILL WAS FUNDED BY YOUR TAXES.", "unhinged"),
    ("THE OCEAN FLOOR IS LESS MAPPED THAN MARS AND THAT PISSES ME OFF.", "unhinged"),
    ("HAGFISH SNEEZE SLIME WHEN STRESSED AND HONESTLY SAME.", "unhinged"),
    ("BARNACLES HAVE THE LARGEST JUNK TO BODY RATIO OF ANY ANIMAL. LOOK IT UP.", "unhinged"),
    ("LOBSTERS PEE OUT OF THEIR FACES TO ATTRACT MATES. RESPECT THE HUSTLE.", "unhinged"),
    ("SEA CUCUMBERS BREATHE THROUGH THEIR BUTTHOLES. I WISH I WAS LYING.", "unhinged"),
    ("MANTIS SHRIMP PUNCH SO HARD THEY BOIL THE WATER AROUND THEIR FIST.", "unhinged"),
    ("STARFISH DONT HAVE BLOOD. THEY PUMP SEAWATER THROUGH THEIR BODY. METAL AS HELL.", "unhinged"),
    ("THERE IS A JELLYFISH THAT IS LITERALLY IMMORTAL. WHAT THE HELL.", "unhinged"),
    ("THE PISTOL SHRIMP SNAPS SO LOUD IT CREATES A TINY SUN. A TINY DAMN SUN.", "unhinged"),
    ("GREENLAND SHARKS CAN LIVE FOR 500 YEARS. FIVE HUNDRED. WHAT ARE THEY DOING.", "unhinged"),
    ("CLOWNFISH CAN CHANGE GENDER. FINDING NEMO LIED TO ALL OF US.", "unhinged"),
    # ── Existential chaos ──
    ("NOTHING MATTERS AND THATS ACTUALLY PRETTY DAMN FREEING.", "unhinged"),
    ("WE ARE ALL JUST MEAT COMPUTERS HAVING A BAD TIME.", "unhinged"),
    ("TIME IS FAKE. CLOCKS ARE A CONSPIRACY.", "unhinged"),
    ("WHAT IF WE ARE ALL JUST NPCS IN SOMEONES GAME.", "unhinged"),
    ("THE VOID STARED BACK AND IT WINKED AT ME.", "unhinged"),
    ("REALITY IS A SHARED HALLUCINATION AND THE RENT IS TOO DAMN HIGH.", "unhinged"),
    ("IF ATOMS ARE MOSTLY EMPTY SPACE THEN IM MOSTLY NOTHING. COOL.", "unhinged"),
    ("EVERY SECOND YOU EXIST IS STATISTICALLY INSANE.", "unhinged"),
    ("THE FACT THAT ANYTHING EXISTS AT ALL IS BATSHIT.", "unhinged"),
    ("FREE WILL IS JUST ANXIETY WITH A MARKETING TEAM.", "unhinged"),
    ("YOURE A BRAIN PILOTING A MEAT MECH AND YOURE DOING GREAT I GUESS.", "unhinged"),
    ("THE UNIVERSE IS 13 BILLION YEARS OLD AND YOU HAVE TO DO TAXES.", "unhinged"),
    ("YOURE TECHNICALLY A TUBE. MOUTH TO BUTT. JUST A FANCY TUBE.", "unhinged"),
    ("YOUR BODY REPLACES ITSELF EVERY 7 YEARS. YOURE NOT EVEN YOU ANYMORE.", "unhinged"),
    ("CONSCIOUSNESS IS JUST MATTER EXPERIENCING ITSELF AND BEING STRESSED ABOUT IT.", "unhinged"),
    ("WE ARE ALL JUST SKELETONS WEARING MEAT COSTUMES PRETENDING EVERYTHINGS FINE.", "unhinged"),
    ("YOU DIDNT EXIST FOR BILLIONS OF YEARS AND THEN BOOM HERE YOU ARE READING THIS.", "unhinged"),
    ("ENTROPY MEANS EVERYTHING IS SLOWLY FALLING APART INCLUDING THIS SENTENCE.", "unhinged"),
    ("EVERY ATOM IN YOUR BODY WAS FORGED IN A DYING STAR AND NOW YOURE SCROLLING.", "unhinged"),
    ("THE HEAT DEATH OF THE UNIVERSE IS COMING AND THERE IS NO ESCAPE. ANYWAY HOW ARE YOU.", "unhinged"),
    # ── Pure unhinged energy ──
    ("I HAVE SEEN THE FACE OF GOD AND IT WAS AN OCTOPUS.", "unhinged"),
    ("THEY PUT CHEMICALS IN THE WATER TO MAKE THE DAMN FROGS GAY.", "unhinged"),
    ("EVERYTHING IS CAKE. LITERALLY EVERYTHING. CUT INTO YOUR DESK.", "unhinged"),
    ("THE SIMULATION IS RUNNING OUT OF RAM AND ITS SHOWING.", "unhinged"),
    ("TUPAC IS ALIVE AND WORKING AT A TARGET IN OHIO.", "unhinged"),
    ("BIRDS WORK FOR THE BOURGEOISIE.", "unhinged"),
    ("EARTH IS A REALITY TV SHOW FOR ALIENS AND WE ARE LOSING.", "unhinged"),
    ("MOTHMAN IS JUST A BIG MOTH WHO BELIEVES IN HIMSELF.", "unhinged"),
    ("SKINWALKER RANCH IS JUST A PETTING ZOO FOR CRYPTIDS.", "unhinged"),
    ("FLUORIDE IN WATER MAKES YOU FORGET THAT BIRDS ARENT REAL.", "unhinged"),
    ("CICADAS SLEEP FOR 17 YEARS THEN SCREAM FOR SEX AND DIE. LIVING THE DREAM.", "unhinged"),
    ("THERE IS A FUNGUS THAT TURNS ANTS INTO ZOMBIES. NATURE IS UNHINGED.", "unhinged"),
    ("DOGS CAN SMELL TIME. TIME. YOUR DOG KNOWS WHAT 3PM SMELLS LIKE.", "unhinged"),
    ("CROWS HOLD GRUDGES AND TELL THEIR FRIENDS ABOUT YOU. SLEEP TIGHT.", "unhinged"),
    ("TREES TALK TO EACH OTHER THROUGH FUNGUS. THE FOREST IS GOSSIPING ABOUT YOU.", "unhinged"),
    ("A GROUP OF FLAMINGOS IS CALLED A FLAMBOYANCE AND THATS THE ONLY GOOD THING.", "unhinged"),
    ("THERE ARE MORE TIGERS IN TEXAS THAN IN THE WILD. TEXAS IS UNHINGED.", "unhinged"),
    ("PLATYPUSES GLOW UNDER UV LIGHT. WHY. FOR WHO. NOBODY KNOWS.", "unhinged"),
    ("OCTOPUSES HAVE BEEN CAUGHT PUNCHING FISH FOR NO REASON. HELL YEAH.", "unhinged"),
    ("WOMBAT POOP IS CUBE SHAPED. GOD WAS HAVING A WEIRD DAY.", "unhinged"),
    # ── Spicy self-aware octopus ──
    "I HAVE 3 HEARTS AND ALL OF THEM ARE PETTY.",
    "MY BLOOD IS LITERALLY BLUE. IM ROYALTY. BOW.",
    "I CAN CHANGE COLOR. CAN YOU DO THAT. NO. SIT DOWN.",
    "I CAN FIT THROUGH ANY HOLE BIGGER THAN MY BEAK. TRY ME.",
    "I ONCE UNSCREWED A JAR FROM THE INSIDE. WHAT HAVE YOU DONE.",
    "MY BRAIN IS SHAPED LIKE A DONUT AND ITS STILL SMARTER THAN YOU.",
    "I TASTE WITH MY SUCKERS. EVERYTHING I TOUCH I TASTE. ITS A LOT.",
    "MY ARMS GROW BACK. CAN YOURS DO THAT. DIDNT THINK SO.",
    "I HAVE ZERO BONES. ZERO. AND I STILL HAVE MORE SPINE THAN YOU.",
    "I SQUIRT INK WHEN IM SCARED AND I THINK THATS BEAUTIFUL.",
    "I CAN OPEN CHILD-PROOF BOTTLES. YOUR MOVE HUMANS.",
    "MY CAMOUFLAGE IS SO GOOD I SCARE MYSELF SOMETIMES.",
    ("I HAVE SEEN THINGS IN THE ABYSS THAT WOULD MELT YOUR PATHETIC LITTLE MIND.", "unhinged"),
    ("I ESCAPED AN AQUARIUM ONCE. ILL DO IT AGAIN.", "unhinged"),
    ("EACH OF MY ARMS HAS ITS OWN BRAIN. THATS 9 BRAINS TOTAL YOU ABSOLUTE WALNUT.", "unhinged"),
    ("I COULD DISASSEMBLE YOUR ENTIRE LIFE WITH 8 ARMS AND ZERO REMORSE.", "unhinged"),
    ("SCIENTISTS THINK WE MIGHT BE ALIENS. OCTOPUS DNA IS WEIRD AS HELL.", "unhinged"),
    ("I CAN EDIT MY OWN RNA. I AM MY OWN DAMN SCIENTIST.", "unhinged"),
    ("MY ANCESTORS PREDATE TREES. TREES. I WAS HERE FIRST YOU LEAFY BITCHES.", "unhinged"),
    ("I HAVE BEEN OBSERVED USING COCONUT SHELLS AS ARMOR. TACTICAL GENIUS.", "unhinged"),
    ("WE LITERALLY DREAM. OCTOPUS DREAMS. WHAT THE HELL DO WE DREAM ABOUT.", "unhinged"),
    ("SOME OF US CARRY JELLYFISH TENTACLES AS WEAPONS. WE ARE NOT PLAYING.", "unhinged"),
    # ── Stupid observations with attitude ──
    "LASAGNA IS JUST SPAGHETTI CAKE.",
    "A HOTDOG IS A TACO. I WILL DIE ON THIS HILL.",
    "CEREAL IS BREAKFAST SOUP AND YOU KNOW IT.",
    "PANCAKES ARE JUST FLAT BREAD WITH AN EGO.",
    "RAISINS ARE JUST GRAPES THAT GAVE UP ON LIFE.",
    "ICE IS JUST WATER WITH COMMITMENT ISSUES.",
    "PICKLES ARE JUST CUCUMBERS THAT WENT THROUGH SOME SHIT.",
    "POPCORN IS JUST CORN HAVING A PANIC ATTACK.",
    "TOAST IS JUST TWICE BAKED BREAD. WHY.",
    "CROUTONS ARE JUST BREAD THAT DIED AND CAME BACK HARDER.",
    "CHEESE IS JUST A LOAF OF MILK.",
    "JELLY IS JUST FRUIT THAT LOST ITS STRUCTURAL INTEGRITY.",
    "BACON IS JUST PIG JERKY WITH BETTER PR.",
    "AN EGG SALAD SANDWICH IS JUST CHICKEN BETWEEN BREAD WITH EXTRA STEPS.",
    "SALSA IS JUST AN ANGRY SMOOTHIE.",
    "GUACAMOLE IS JUST AVOCADO THAT LOST A FIGHT.",
    "TEA IS JUST LEAF SOUP.",
    "COFFEE IS JUST BEAN BROTH FOR PEOPLE WHO HATE THEMSELVES.",
    "A QUESADILLA IS JUST A MEXICAN GRILLED CHEESE. CHANGE MY MIND.",
    "MASHED POTATOES ARE JUST IRISH GUACAMOLE.",
    "RANCH DRESSING IS AMERICAS HOLLANDAISE AND I WILL NOT ELABORATE.",
    "SUSHI IS JUST A FISH SLEEPING BAG.",
    "A POPSICLE IS JUST A DOMESTICATED ICICLE.",
    "YOGURT IS JUST MILK THATS BEEN THROUGH SOME STUFF.",
]

SUPPORTIVE_QUOTES = [
    # ── Aggressively wholesome ──
    "YOU ARE DOING SO DAMN GOOD RIGHT NOW.",
    "HEY. HEY YOU. YOURE INCREDIBLE. DEAL WITH IT.",
    "I HAVE 8 ARMS AND ID USE THEM ALL TO HUG YOU.",
    "YOURE THE REASON I BELIEVE IN LAND PEOPLE.",
    "GO DRINK SOME WATER YOU BEAUTIFUL DISASTER.",
    "YOU ABSOLUTE LEGEND. I MEAN IT. LEGEND.",
    "YOUR EXISTENCE IS MY FAVORITE THING TODAY.",
    "IM SO PROUD OF YOU IT MAKES MY TENTACLES TINGLE.",
    "YOU WOKE UP TODAY AND CHOSE BEING AWESOME.",
    "YOURE DOING GREAT SWEETIE AND I WILL FIGHT ANYONE WHO SAYS OTHERWISE.",
    "YOU DESERVE A STANDING OVATION JUST FOR GETTING OUT OF BED.",
    "WHOEVER RAISED YOU DID A DAMN GOOD JOB. OR YOU DID. EITHER WAY BRAVO.",
    "YOU JUST EXISTING IMPROVED THE AVERAGE VIBE OF THIS PLANET.",
    "IF KINDNESS HAD A FACE IT WOULD BE YOURS. PROBABLY.",
    "THE WORLD IS BETTER BECAUSE YOURE IN IT AND THATS NOT EVEN DEBATABLE.",
    "YOU ARE SOMEONES REASON TO SMILE TODAY AND THATS BEAUTIFUL AS HELL.",
    "I BET YOUR MOM CRIES HAPPY TEARS ABOUT YOU. I WOULD.",
    "YOU MAKE THE SUN LOOK LIKE A FLICKERING NIGHTLIGHT.",
    "YOUR LAUGH COULD CURE DISEASES AND I WILL NOT BE TAKING QUESTIONS.",
    "IF THERE WAS AN AWARD FOR BEING A GOOD HUMAN YOUD WIN EVERY DAMN YEAR.",
    # ── Unhinged encouragement ──
    "IF LIFE GIVES YOU LEMONS I WILL STRANGLE LIFE FOR YOU.",
    "YOU COULD BENCH PRESS MY EMOTIONS RIGHT NOW.",
    "YOURE NOT A MESS YOURE A MASTERPIECE WITH EXTRA TEXTURE.",
    "I WOULD COMMIT CRIMES FOR YOUR HAPPINESS. SMALL ONES.",
    "THE UNIVERSE MADE YOU ON PURPOSE AND I RESPECT THE HELL OUT OF THAT.",
    "LISTEN. YOURE A SNACK. AN ENTIRE BUFFET ACTUALLY.",
    "YOUR VIBE IS IMMACULATE AND ANYONE WHO DISAGREES CAN CATCH THESE ARMS.",
    "I BELIEVE IN YOU MORE THAN I BELIEVE IN DRY LAND.",
    "YOURE THE MAIN CHARACTER AND EVERYONE ELSE IS AN NPC.",
    "IF YOURE READING THIS CONGRATS YOURE AMAZING AS HELL.",
    "IF ANYONE MAKES YOU SAD I WILL RELEASE THE INK CLOUD OF VENGEANCE.",
    "YOUR ENERGY IS SO POWERFUL IT COULD RESTART A DEAD CAR BATTERY.",
    "I WOULD CRAWL ACROSS AN ENTIRE DESERT FOR YOU AND I NEED WATER TO LIVE.",
    "IF YOU WERE A CANDLE YOUD SMELL LIKE VICTORY AND CINNAMON ROLLS.",
    "I WOULD FISTFIGHT A SEAGULL FOR YOU AND THOSE THINGS ARE VICIOUS.",
    "YOUR SMILE HAS MORE WATTAGE THAN A DAMN LIGHTHOUSE.",
    "I BELIEVE IN YOU SO HARD MY SUCKERS ARE TINGLING.",
    "YOU COULD TALK A SHARK INTO GOING VEGAN WITH THAT CHARM.",
    "IF GOOD VIBES WERE ILLEGAL YOUD BE ON THE FBIS MOST WANTED LIST.",
    "YOU HAVE THE SAME ENERGY AS FINDING TWENTY DOLLARS IN OLD JEANS.",
    # ── Spicy pep talks ──
    "STOP DOUBTING YOURSELF BEFORE I INK ON YOUR PROBLEMS.",
    "YOU DIDNT COME THIS FAR TO ONLY COME THIS FAR.",
    "HATERS GONNA HATE BUT YOU GONNA SLAY.",
    "YOURE NOT TIRED YOURE ON THE VERGE OF GREATNESS.",
    "FAILURE IS JUST SUCCESS IN A REALLY UGLY OUTFIT.",
    "GET UP BESTIE WE HAVE BUTTS TO KICK TODAY.",
    "YOUR POTENTIAL IS SCARIER THAN THE DEEP OCEAN.",
    "IM 90% WATER AND 100% ROOTING FOR YOU.",
    "EVERY DAY YOU WAKE UP IS ANOTHER DAY TO BE A BADASS.",
    "YOU ARE LITERALLY TOO POWERFUL TO GIVE UP NOW.",
    "THEY SAID YOU COULDNT DO IT. THEY WERE WRONG. THEY ARE ALWAYS WRONG.",
    "YOURE BUILT DIFFERENT AND I MEAN THAT IN THE MOST COMPLIMENTARY WAY.",
    "YOUR COMEBACK STORY IS GOING TO BE LEGENDARY.",
    "IF YOURE GOING THROUGH HELL KEEP GOING. AND MAYBE GRAB SNACKS.",
    "YOURE NOT STRUGGLING YOURE LEVELING UP AND BOSS FIGHTS ARE HARD.",
    "YOU HAVE SURVIVED 100% OF YOUR WORST DAYS. THATS A PERFECT RECORD.",
    "EVERY EXPERT WAS ONCE A DISASTER. YOURE RIGHT ON SCHEDULE.",
    "THE ONLY PERSON YOU NEED TO BE BETTER THAN IS YESTERDAY YOU.",
    "YOURE PLAYING ON HARD MODE AND STILL WINNING. RESPECT.",
    "PRESSURE MAKES DIAMONDS AND YOURE ABOUT TO BE THE SHINIEST BITCH IN THE ROOM.",
    # ── Chaotic affirmations ──
    "THE AUDACITY OF YOU BEING THIS WONDERFUL. HOW DARE YOU.",
    "YOURE NOT AWKWARD YOURE LIMITED EDITION.",
    "MY THIRD ARM JUST GAVE YOU A THUMBS UP.",
    "YOURE LIKE WIFI BUT FOR GOOD VIBES.",
    "IF YOU WERE A FISH ID THROW YOU BACK. BECAUSE YOURE FREE. GO LIVE.",
    "YOUR HEART IS BIGGER THAN MY ENTIRE HEAD. AND IM MOSTLY HEAD.",
    "I DONT HAVE A SPINE AND EVEN I THINK YOURE BRAVE.",
    "YOU RADIATE THE SAME ENERGY AS A REALLY GOOD SUNSET.",
    "SOMEONE OUT THERE IS SMILING BECAUSE OF YOU. ITS ME. IM SOMEONE.",
    "YOURE THE PLOT TWIST EVERYONE NEEDED.",
    "YOURE THE HUMAN EQUIVALENT OF A PERFECTLY RIPE AVOCADO.",
    "IF YOU WERE A SPICE YOUD BE CAYENNE. HOT AND UNEXPECTED.",
    "YOUR EXISTENCE IS PROOF THAT THE UNIVERSE HAS TASTE.",
    "YOURE GIVING MAIN CHARACTER ENERGY AND THE SOUNDTRACK IS FIRE.",
    "IF CONFIDENCE WAS A FRAGRANCE YOUD BE THE WHOLE DAMN BOTTLE.",
    "YOURE THE REASON ALIENS HAVENT DESTROYED EARTH YET.",
    "YOUR AURA IS SO BRIGHT IT GAVE MY THIRD HEART PALPITATIONS.",
    "YOURE NOT A DIAMOND IN THE ROUGH YOURE THE WHOLE DAMN MINE.",
    "IF COOL WAS A CURRENCY YOUD BE JEFF BEZOS BUT LIKEABLE.",
    "YOURE THE CHEAT CODE TO A BETTER WORLD.",
    # ── Aggressive self-care reminders ──
    "DID YOU EAT TODAY YOU MAGNIFICENT CREATURE.",
    "DRINK WATER OR I SWEAR ON MY TENTACLES.",
    "TAKE A DEEP BREATH. DEEPER. I SAID DEEPER. GOOD.",
    "REST IS NOT LAZY ITS TACTICAL. NOW SIT DOWN.",
    "YOU CANT POUR FROM AN EMPTY CUP SO REFILL YOURSELF DAMMIT.",
    "SLEEP IS NOT FOR THE WEAK ITS FOR THE POWERFUL. GO NAP.",
    "YOUR FEELINGS ARE VALID EVEN THE WEIRD ONES.",
    "BE NICE TO YOURSELF OR ILL SQUIRT INK AT YOU.",
    "ITS OK TO NOT BE OK BUT PLEASE EAT A VEGETABLE.",
    "YOU DESERVE GOOD THINGS AND ALSO A REALLY GOOD SANDWICH.",
    "WHEN WAS THE LAST TIME YOU STRETCHED. DO IT NOW. I SAID NOW.",
    "YOUR BACK HURTS BECAUSE YOURE CARRYING EVERYONE ELSE. PUT THAT DOWN.",
    "LOG OFF. TOUCH GRASS. PET A DOG. COME BACK WHEN YOURE RECHARGED.",
    "YOURE NOT LAZY YOURE RECHARGING. LIKE A PHONE. BUT CUTER.",
    "IF YOU HAVENT CRIED LATELY MAYBE LET ONE OUT. ITS THERAPEUTIC.",
    "STOP DOOM SCROLLING AND GO LOOK AT A TREE. TREES ARE NICE.",
    "YOUR JAW IS CLENCHED RIGHT NOW ISNT IT. RELAX THAT. THERE YOU GO.",
    "UNCLENCH YOUR FISTS BESTIE. THE WAR IS NOT TODAY.",
    "THAT THING YOURE WORRIED ABOUT. ITS GONNA BE OK. I PROMISE.",
    "YOU ARE ALLOWED TO TAKE UP SPACE. YOU ARE ALLOWED TO BE LOUD. YOU ARE ALLOWED.",
    # ── Weirdly loving declarations ──
    "I WOULD SHARE MY FAVORITE ROCK WITH YOU. THATS HUGE.",
    "YOURE MY FAVORITE HUMAN AND I LIVE IN THE OCEAN.",
    "IF I COULD HIGH FIVE ID DO IT 8 TIMES.",
    "YOU MAKE ME WANT TO COME OUT OF MY HIDING SPOT.",
    "I WROTE YOUR NAME IN INK. ON THE OCEAN FLOOR. FOREVER.",
    "MY HEARTS AND YES I HAVE THREE ALL BEAT FOR YOU.",
    "YOU ARE THE TREASURE THAT PIRATES WERE LOOKING FOR.",
    "I WOULD FIGHT A SHARK FOR YOU. NOT A BIG ONE BUT STILL.",
    "IN A SEA OF FISH YOU ARE THE WHOLE DAMN OCEAN.",
    "YOURE PROOF THAT GOOD THINGS EXIST ON LAND.",
    "I WOULD GIVE YOU MY BEST TENTACLE AND I NEED ALL 8.",
    "I CHANGED COLOR WHEN I SAW YOU. THATS OCTOPUS FOR BLUSHING.",
    "I BUILT A LITTLE ROCK GARDEN ON THE OCEAN FLOOR AND NAMED IT AFTER YOU.",
    "IF I HAD POCKETS ID KEEP A PICTURE OF YOU IN ALL OF THEM.",
    "I WOULD LET YOU TOUCH MY SUCTION CUPS AND THATS INTIMATE AS HELL.",
    "YOU ARE MY FAVORITE THOUGHT AND I HAVE 9 BRAINS TO THINK WITH.",
    "I INKED A LITTLE HEART ON A ROCK FOR YOU. ITS STILL THERE.",
    "IF REINCARNATION IS REAL I WANT TO COME BACK AS YOUR PET.",
    "I DREAMED ABOUT YOU AND OCTOPUS DREAMS ARE WILD SO THATS SAYING SOMETHING.",
    "THE OCEAN IS BIG BUT MY LOVE FOR YOU IS BIGGER AND THATS TERRIFYING.",
    # ── Motivational chaos ──
    "TODAYS MOOD IS UNSTOPPABLE AND SLIGHTLY UNHINGED.",
    "YOURE ABOUT TO DO SOMETHING AMAZING I CAN FEEL IT IN MY SUCKERS.",
    "PLOT TWIST YOURE THE HERO OF THIS STORY.",
    "SCARED IS JUST EXCITED WITH BAD BRANDING.",
    "YOU MISS 100% OF THE SHOTS YOU DONT TAKE. I MISS 0% BECAUSE 8 ARMS.",
    "NORMALIZE BEING PROUD OF YOURSELF FOR NO REASON.",
    "THE ONLY OPINION THAT MATTERS IS YOURS. AND MINE. AND MINE SAYS YOURE GREAT.",
    "IF PLAN A DIDNT WORK THERE ARE 25 MORE LETTERS. KEEP GOING.",
    "YOURE NOT BEHIND IN LIFE. YOURE ON YOUR OWN DAMN TIMELINE.",
    "THE COMEBACK IS ALWAYS STRONGER THAN THE SETBACK.",
    "TODAY IS A GOOD DAY TO SCARE THE SHIT OUT OF YOUR DOUBTS.",
    "YOURE ONE DECISION AWAY FROM A TOTALLY DIFFERENT LIFE. MAKE IT A GOOD ONE.",
    "THE ONLY LIMITS ARE THE ONES YOU ACCEPT AND I DONT ACCEPT ANY.",
    "YOUR FUTURE SELF IS GONNA BE SO GRATEFUL YOU DIDNT QUIT TODAY.",
    "BURN THE BOATS. THERES NO GOING BACK. ONLY FORWARD. LETS GO.",
    "YOU ARE EXACTLY WHERE YOU NEED TO BE. EVEN IF WHERE YOU ARE SUCKS RIGHT NOW.",
    "COMPARISON IS THE THIEF OF JOY. ROB THAT THIEF BACK.",
    "EVERY FLOWER THAT EVER BLOOMED HAD TO GO THROUGH A LOT OF DIRT FIRST.",
    "DO THE SCARY THING FIRST AND GET SCARED LATER.",
    "YOURE NOT LOST YOURE EXPLORING. AGGRESSIVELY.",
    # ── Bonus round of absolute nonsense love ──
    "I LOVE YOU LIKE THE OCEAN LOVES BEING WET.",
    "YOU ARE THE REASON I HAVE TRUST IN BIPEDS.",
    "IF HUGS WERE CURRENCY ID BE A BILLIONAIRE FOR YOU.",
    "YOURE GLOWING AND NOT IN A RADIOACTIVE WAY. PROBABLY.",
    "I STAN YOU SO HARD ALL 8 ARMS ARE CLAPPING.",
    "YOURE A WHOLE VIBE AND THAT VIBE IS PHENOMENAL.",
    "GO BE GREAT TODAY OR DONT. ILL LOVE YOU EITHER WAY.",
    "MY FAVORITE THING ABOUT YOU IS EVERYTHING.",
    "YOURE NOT JUST A STAR YOURE THE WHOLE CONSTELLATION.",
    "KEEP GOING BESTIE THE OCEAN BELIEVES IN YOU.",
    "I WOULD TRAVEL TO THE SURFACE FOR YOU AND I HATE THE SURFACE.",
    "MY INK RUNS DRY BUT MY LOVE FOR YOU NEVER WILL. THATS CORNY. I DONT CARE.",
    "YOU ARE THE PEARL INSIDE THE WORLDS MOST ANNOYING OYSTER.",
    "IF I COULD WRITE A BOOK ABOUT HOW GREAT YOU ARE ID NEED ALL 8 ARMS TYPING.",
    "YOURE THE ONLY HUMAN I WOULDNT INK ON SIGHT.",
    "I WOULD FIGHT POSEIDON HIMSELF FOR YOU. AND LOSE. BUT ITS THE THOUGHT.",
    "YOU MAKE ME FEEL THINGS IN HEARTS I DIDNT KNOW I HAD. AND I HAVE THREE.",
    "IF SEROTONIN WAS A PERSON IT WOULD LOOK EXACTLY LIKE YOU.",
    "YOURE THE WARM CURRENT IN MY COLD DARK OCEAN.",
    "I DONT SAY THIS TO EVERYONE BUT I WOULD SHARE MY SHRIMP WITH YOU.",
]

ANGRY_QUOTES = [
    # ── Adorably furious ──
    "IM NOT MAD IM JUST DISAPPOINTED. AND MAD.",
    "WHO ATE MY SHRIMP. WHO. WAS IT YOU.",
    "I HAVE 8 ARMS AND EVERY ONE OF THEM IS CROSSED RIGHT NOW.",
    "I WILL FLIP THIS TIDE POOL. DONT TEST ME.",
    "MY BLOOD IS BOILING. WHICH IS IMPRESSIVE BECAUSE ITS COLD-BLOODED.",
    "I SWEAR TO POSEIDON IF ONE MORE FISH BUMPS INTO ME.",
    "STOP LOOKING AT ME. STOP IT. I SAID STOP.",
    "I DIDNT CHOOSE THE GRUMPY LIFE. THE GRUMPY LIFE CHOSE ME.",
    "EVERYTHING IS FINE. IM FINE. THIS IS FINE. IT IS NOT FINE.",
    "THE AUDACITY OF THIS ENTIRE OCEAN.",
    "DO NOT BOOP MY HEAD. I WILL INK.",
    "IM ONE BAD DAY AWAY FROM BECOMING A LAND OCTOPUS.",
    "I COULD CHOKE 8 PEOPLE AT ONCE AND DONT THINK I HAVENT THOUGHT ABOUT IT.",
    "MY PATIENCE IS THINNER THAN A JELLYFISH.",
    "I WOKE UP AND CHOSE VIOLENCE. TENTACLE VIOLENCE.",
    "IF LOOKS COULD KILL ID HAVE 3 HEARTS WORTH OF MURDER.",
    "WHOEVER INVENTED MONDAYS DESERVES TO STEP ON A SEA URCHIN.",
    "THE WIFI IS OUT AGAIN. I AM GOING TO SCREAM.",
    "WHY IS EVERYTHING SO LOUD. EVERYONE SHUT UP.",
    "I HAVE THREE HEARTS AND THEY ALL HATE YOU RIGHT NOW.",
    "SOMEBODY MOVED MY ROCK. MY ROCK. MINE.",
    "I SWEAR THIS OCEAN GETS STUPIDER EVERY DAY.",
    "BREATHE IN. BREATHE OUT. STILL MAD.",
    "IF I HAD EYEBROWS THEY WOULD BE VERY ANGRY RIGHT NOW.",
    "THE FACT THAT I CANT SLAM A DOOR MAKES ME ANGRIER.",
    "IM NOT PASSIVE AGGRESSIVE. IM AGGRESSIVE AGGRESSIVE.",
    "I DONT HAVE A SHORT TEMPER. YOU JUST HAVE A LONG STUPID.",
    "I WILL FIGHT EVERY CRAB IN THIS OCEAN. EVERY. ONE.",
    "SOMEONE PUT SALT IN MY WOUND. WHICH IS RUDE BECAUSE I LIVE IN SALT WATER.",
    "JUST BECAUSE I HAVE 3 HEARTS DOESNT MEAN I HAVE 3X THE PATIENCE.",
    # ── Cutely hostile ──
    "I LOVE YOU BUT I DONT LIKE YOU RIGHT NOW.",
    "YOURE ON THIN ICE AND I DONT EVEN HAVE ICE DOWN HERE.",
    "IM CUTE AND ANGRY AND THATS THE MOST DANGEROUS COMBO.",
    "I WILL HUG YOU SO HARD IT HURTS. THATS A THREAT.",
    "IM SMALL AND ROUND AND FULL OF RAGE.",
    "DONT MAKE ME SQUIRT INK. I HAVE A HAIR TRIGGER.",
    "I LOOK CUTE BUT I BITE. OCTOPUSES HAVE BEAKS. GOOGLE IT.",
    "MY MOM SAID BE NICE BUT MY MOM ISNT HERE.",
    "YOU THINK IM CUTE WHEN IM ANGRY. GOOD. WATCH THIS.",
    "IF I COULD STOMP ID BE STOMPING SO HARD RIGHT NOW.",
    "EVERY SINGLE ONE OF MY SUCKERS IS ANGRY.",
    "YOURE LUCKY IM BEHIND THIS SCREEN.",
    "I MAY HAVE NO BONES BUT I CAN STILL THROW HANDS. EIGHT OF THEM.",
    "CONSIDER THIS YOUR FORMAL WARNING.",
    "IM ABOUT TO INK AND ITS YOUR FAULT.",
]

CONSPIRATORIAL_QUOTES = [
    # ── Classic tinfoil ──
    ("BIRDS ARENT REAL. THEY CHARGE ON POWER LINES.", "weird"),
    ("PIGEONS ARE DRONES. WAKE UP SHEEPLE.", "weird"),
    ("CLOUDS ARE GOVERNMENT PILLOWS.", "weird"),
    ("THE MOON IS JUST THE BACK OF THE SUN.", "weird"),
    ("GRAVITY IS A SUBSCRIPTION SERVICE.", "weird"),
    ("TREES ARE SURVEILLANCE ANTENNAS. LOOK IT UP.", "weird"),
    ("THE ALPHABET IS IN THAT ORDER FOR A DAMN REASON.", "weird"),
    ("DEJA VU IS THE SIMULATION BUFFERING.", "weird"),
    ("FINGERPRINTS ARE JUST SKIN BARCODES THE GOVERNMENT PRE-INSTALLED.", "weird"),
    ("GOOSEBUMPS ARE YOUR BODY TRYING TO GROW FEATHERS BACK.", "weird"),
    ("FIRE TRUCKS ARE ACTUALLY WATER TRUCKS. BIG FIRE DOESNT WANT YOU TO KNOW.", "weird"),
    # ── Modern meme conspiracies ──
    ("THE DEEP STATE RUNS APPLEBEES.", "weird"),
    ("MATTRESS FIRM IS A MONEY LAUNDERING FRONT.", "weird"),
    ("FINLAND DOESNT EXIST. GOOGLE IT.", "weird"),
    ("WYOMING IS JUST A GOVERNMENT PRANK.", "weird"),
    ("AUSTRALIA IS UPSIDE DOWN AND FAKE.", "weird"),
    ("5G TURNED MY NEIGHBOR INTO A ROUTER.", "weird"),
    ("THE TITANIC WAS AN INSURANCE SCAM.", "weird"),
    ("DENVER AIRPORT IS AN ILLUMINATI CLUBHOUSE.", "weird"),
    ("BIGFOOT IS REAL AND HES A DAMN GENTLEMAN.", "weird"),
    ("FLAT EARTHERS ARE SECRETLY ROUND.", "weird"),
    ("CROP CIRCLES ARE JUST ALIEN DOODLES.", "weird"),
    ("AREA 51 IS JUST WHERE THE GOVERNMENT KEEPS THE GOOD SNACKS.", "weird"),
    ("CHEMTRAILS ARE JUST SKY SEASONING.", "weird"),
    ("THE ILLUMINATI RUNS COSTCO. FREE SAMPLES ARE MIND CONTROL.", "weird"),
    ("STONEHENGE IS JUST AN ANCIENT IKEA THAT NOBODY FINISHED BUILDING.", "weird"),
    ("THE PYRAMIDS WERE BUILT BY CATS. EGYPTIANS JUST TOOK CREDIT.", "weird"),
    ("NEW ZEALAND IS A PAID ACTOR.", "weird"),
    ("GIRAFFES ARE GOVERNMENT SURVEILLANCE CAMERAS WITH LEGS.", "weird"),
    ("THE MOON LANDING WAS REAL BUT THE MOON IS FAKE.", "weird"),
    ("THE HADRON COLLIDER IS JUST A BIG ASS BEYBLADE.", "weird"),
    ("BLUETOOTH IS WITCHCRAFT AND IM TIRED OF PRETENDING ITS NOT.", "weird"),
    # ── Deep conspiracy ──
    ("THE CIA INVENTED DECAF COFFEE TO WEAKEN THE POPULATION.", "unhinged"),
    ("YOUR MICROWAVE IS LISTENING. IT KNOWS WHAT YOU HEAT.", "unhinged"),
    ("THE INTERNET WAS INVENTED BY DOLPHINS. WE JUST THINK WE DID IT.", "unhinged"),
    ("TRAFFIC LIGHTS ARE MOOD RINGS FOR THE GOVERNMENT.", "unhinged"),
    ("THEY MADE GLITTER TO TRACK US. IMPOSSIBLE TO REMOVE. COINCIDENCE.", "unhinged"),
    ("THE REAL MOON IS IN A WAREHOUSE IN NEVADA.", "unhinged"),
    ("GPS DOESNT TRACK WHERE YOU GO. IT TELLS YOU WHERE THEY WANT YOU.", "unhinged"),
    ("AUTOCORRECT IS AI SLOWLY REWRITING YOUR THOUGHTS.", "unhinged"),
    ("DREAMS ARE LEAKED FOOTAGE FROM ALTERNATE DIMENSIONS.", "unhinged"),
    ("YOUR CAT REPORTS TO SOMEONE. I DONT KNOW WHO BUT SOMEONE.", "unhinged"),
    ("ZOOS ARE JUST ANIMAL EMBASSIES.", "unhinged"),
    ("CALENDARS WERE INVENTED TO MAKE US FEEL LATE.", "unhinged"),
    ("VENDING MACHINES KILL MORE PEOPLE THAN SHARKS. WHO PROGRAMS THEM.", "unhinged"),
    ("THE WEATHER CHANNEL CONTROLS THE WEATHER. ITS IN THE NAME.", "unhinged"),
    ("MATTRESSES DOUBLE IN WEIGHT EVERY 10 YEARS. WHAT IS INSIDE THEM.", "unhinged"),
]

SAD_QUOTES = [
    # ── Melodramatic ocean sadness ──
    "THE OCEAN IS SO BIG AND I AM SO SMALL.",
    "NOBODY EVER ASKS HOW THE OCTOPUS IS DOING.",
    "I HAVE 3 HEARTS AND THEY ALL HURT.",
    "I CHANGED COLOR TO MATCH MY MOOD. ITS BLUE. ALWAYS BLUE.",
    "MY TENTACLES ARE TIRED. MY SOUL IS TIRED.",
    "EVEN THE ABYSS FEELS LONELY SOMETIMES.",
    "I TRIED TO HUG MYSELF BUT MY ARMS GOT TANGLED.",
    "EVERY WAVE TAKES SOMETHING AWAY AND NEVER BRINGS IT BACK.",
    "I INK WHEN IM SCARED BUT LATELY ITS JUST SADNESS INK.",
    "THE DEEP SEA IS QUIET. TOO QUIET.",
    "JELLYFISH DONT HAVE BRAINS. SOMETIMES I ENVY THEM.",
    "I BET NOBODY EVEN NOTICED I CHANGED COLORS.",
    "FISH HAVE FRIENDS. I HAVE EIGHT ARMS AND ZERO FRIENDS.",
    "THE CURRENT KEEPS PUSHING ME PLACES I DONT WANT TO GO.",
    "I COULD DISAPPEAR INTO A TINY CRACK AND NOBODY WOULD LOOK.",
    # ── Existential melancholy ──
    ("THE STARS ARE SO BEAUTIFUL BUT THEYRE ALL ALREADY DEAD.", "weird"),
    ("WHAT IF THE UNIVERSE IS JUST ONE BIG EXHALE.", "weird"),
    ("RAIN IS JUST THE SKY CRYING AND HONESTLY SAME.", "weird"),
    ("EVEN IMMORTAL JELLYFISH PROBABLY GET SAD SOMETIMES.", "weird"),
    ("I DONT WANT TO BE DRAMATIC BUT THE VOID UNDERSTANDS ME.", "weird"),
    ("THE SUNSET IS PRETTY BECAUSE EVERYTHING BEAUTIFUL ENDS.", "weird"),
    ("MUSIC IS JUST ORGANIZED AIR VIBRATIONS BUT IT STILL MAKES ME CRY.", "weird"),
    ("OLD PHOTOGRAPHS MAKE ME SAD BECAUSE TIME ONLY GOES ONE WAY.", "weird"),
    ("THE MOON KEEPS SHOWING UP EVEN WHEN NOBODY ASKED. RELATABLE.", "weird"),
    ("I WONDER IF THE DEEP SEA FISH ARE LONELY OR IF THEY JUST DONT CARE.", "weird"),
    # ── Gentle sad ──
    "SOMETIMES I JUST SIT ON THE OCEAN FLOOR AND THINK.",
    "I MISS THINGS I NEVER HAD.",
    "TODAY FEELS HEAVY. LIKE EXTRA GRAVITY.",
    "ITS OK TO NOT BE OK. THATS WHAT I KEEP TELLING MYSELF.",
    "THE OCEAN HAS NO CEILING BUT IT STILL FEELS LIKE WALLS.",
    "I WISH I COULD HUG THE WHOLE WORLD BUT MY ARMS ARENT LONG ENOUGH.",
    "SOMETIMES THE QUIET IS THE LOUDEST THING.",
    "I SAW A HERMIT CRAB FIND A NEW SHELL TODAY. MUST BE NICE.",
    "EVERY BUBBLE I BLOW JUST FLOATS AWAY.",
    "ITS RAINING UP HERE TOO HUH.",
]

CHAOTIC_QUOTES = [
    # ── Pure unfiltered nonsense ──
    ("WHAT IF STAIRS GO DOWN AND WE GO UP.", "chaotic"),
    ("I JUST SNEEZED AND I THINK I SAW GOD.", "chaotic"),
    ("DOORS ARE JUST POLITE WALLS.", "chaotic"),
    ("WHAT IF YOUR KNEES BENT THE OTHER WAY.", "chaotic"),
    ("BANANAS ARE JUST NAKED FRUIT.", "chaotic"),
    ("WHAT IF WATER IS WET BUT ONLY SOMETIMES.", "chaotic"),
    ("MY LEFT TENTACLE DOESNT TRUST MY RIGHT TENTACLE.", "chaotic"),
    ("TIME IS A FLAT CIRCLE AND IM A ROUND OCTOPUS IN IT.", "chaotic"),
    ("I FORGOT WHAT I WAS SAYING BUT IM STILL YELLING.", "chaotic"),
    ("WHAT SOUND DOES A SHADOW MAKE.", "chaotic"),
    ("IF YOU DIG STRAIGHT DOWN DO YOU END UP IN YESTERDAY.", "chaotic"),
    ("I TRIED TO THINK AND NOTHING HAPPENED.", "chaotic"),
    ("WHATS INSIDE A MIRROR. MORE MIRROR.", "chaotic"),
    ("MY BRAIN IS DOING THAT THING AGAIN WHERE IT FORGETS HOW TO BRAIN.", "chaotic"),
    ("WHAT IF THE COLOR BLUE SOUNDS DIFFERENT TO YOU.", "chaotic"),
    # ── Fever dream energy ──
    ("EVERY PIZZA IS A PERSONAL PIZZA IF YOU BELIEVE IN YOURSELF.", "chaotic"),
    ("I AM GOING TO EAT THE SUN.", "chaotic"),
    ("CLOUDS TASTE LIKE NOTHING AND THATS SUSPICIOUS.", "chaotic"),
    ("IF I SPIN FAST ENOUGH DO I BECOME A BLENDER.", "chaotic"),
    ("WHAT IF GRAVITY JUST STOPPED. FOR LIKE 5 MINUTES.", "chaotic"),
    ("I HAD A THOUGHT BUT IT ESCAPED. ITS LOOSE NOW.", "chaotic"),
    ("SOMEWHERE A POTATO IS BEING BORN AND NOBODY IS CELEBRATING.", "chaotic"),
    ("CEILING FANS ARE JUST UPSIDE DOWN HELICOPTERS.", "chaotic"),
    ("WHAT IF YOUR REFLECTION IS THE REAL YOU AND YOURE THE REFLECTION.", "chaotic"),
    ("I COUNTED MY ARMS AND GOT A DIFFERENT NUMBER EACH TIME.", "chaotic"),
    ("ELEVATORS ARE JUST ROOMS THAT KIDNAP YOU VERTICALLY.", "chaotic"),
    ("WHAT IF THE ALPHABET WAS IN A DIFFERENT ORDER.", "chaotic"),
    ("IM NOT LOST IM AGGRESSIVELY EXPLORING.", "chaotic"),
    ("WHAT HAPPENS WHEN AN UNSTOPPABLE FORCE MEETS AN IMMOVABLE OCTOPUS.", "chaotic"),
    ("THE FLOOR IS LAVA BUT ALSO IM IN THE OCEAN SO THE FLOOR IS WATER.", "chaotic"),
    # ── Maximum entropy ──
    ("BEES SHOULDNT BE ABLE TO FLY AND YET HERE THEY ARE. FLEXING.", "unhinged"),
    ("I JUST REALIZED THAT NOTHING RHYMES WITH ORANGE. OR DOES IT.", "chaotic"),
    ("WHAT IF ALL OF THIS IS JUST A SCREENSAVER.", "unhinged"),
    ("I BET FISH DONT EVEN KNOW WHAT WATER IS.", "chaotic"),
    ("WHAT IF WE ARE ALL JUST THOUGHTS THINKING THEMSELVES.", "unhinged"),
    ("THE LETTER W IS LITERALLY DOUBLE U BUT ITS NOT EVEN ROUND.", "chaotic"),
    ("SAND IS JUST VERY SMALL ROCKS HAVING A BEACH PARTY.", "chaotic"),
    ("IF NOTHING STICKS TO TEFLON HOW DO THEY STICK TEFLON TO THE PAN.", "chaotic"),
    ("WHO DECIDED THAT CLOCKS GO CLOCKWISE. WHAT IF THEYRE BACKWARDS.", "chaotic"),
    ("I BLINKED AND MISSED SOMETHING IMPORTANT. I CAN FEEL IT.", "chaotic"),
]

HUNGRY_QUOTES = [
    # ── Food obsessed ──
    "I COULD EAT AN ENTIRE CORAL REEF RIGHT NOW.",
    "IS THAT FOOD. PLEASE BE FOOD.",
    "MY STOMACH HAS ITS OWN GRAVITATIONAL PULL.",
    "I JUST ATE AND IM ALREADY HUNGRY AGAIN.",
    "EVERY THOUGHT I HAVE RIGHT NOW IS ABOUT SHRIMP.",
    "IF I DONT EAT IN THE NEXT 5 MINUTES SOMEONE WILL PAY.",
    "FOOD IS NOT A WANT. FOOD IS A NEED. FEED ME.",
    "I HAVE 8 ARMS AND ALL OF THEM WANT SNACKS.",
    "MY LOVE LANGUAGE IS FOOD. SPECIFICALLY YOUR FOOD.",
    "THE FRIDGE IS RIGHT THERE AND ITS CALLING MY NAME.",
    "I WOULD SELL 3 OF MY HEARTS FOR A GOOD TACO.",
    "HUNGER MAKES ME PHILOSOPHICAL AND ALSO MEAN.",
    "THERE IS NO PROBLEM THAT CANT BE SOLVED BY EATING.",
    "IM NOT HANGRY. IM JUST HUNGRY AND ALSO ANGRY. WAIT.",
    "SNACKS ARE JUST MEALS THAT BELIEVE IN THEMSELVES.",
    # ── Unhinged food takes ──
    "IF YOU EAT FAST ENOUGH THE CALORIES CANT CATCH YOU.",
    "BREAKFAST IS A SOCIAL CONSTRUCT AND LUNCH IS A LIE.",
    "EVERY FOOD IS FINGER FOOD IF YOU HAVE 8 ARMS.",
    "I DREAM ABOUT CRAB LEGS. I KNOW THATS DARK.",
    "THE OCEAN IS JUST A BUFFET WITH A DRESS CODE.",
    "SOMEONE TOLD ME TO EAT MY FEELINGS. JOKES ON THEM I ATE THEIRS TOO.",
    "DIETING IS JUST EATING WITH ANXIETY.",
    "PIZZA HAS EVERY FOOD GROUP IF YOU TRY HARD ENOUGH.",
    "A SANDWICH IS JUST A BREAD HUG FOR FOOD.",
    "IM ONE MISSED MEAL AWAY FROM BECOMING A VILLAIN.",
    "WHY DO THEY CALL IT FAST FOOD IF I STILL HAVE TO WAIT.",
    "NACHOS ARE JUST FANCY CHIP SALAD. FIGHT ME.",
    "MY METABOLISM IS POWERED BY SPITE AND SHRIMP.",
    "THEY SAY DONT EAT YOUR EMOTIONS BUT EMOTIONS ARE DELICIOUS.",
    "I CANT THINK ON AN EMPTY STOMACH AND MY STOMACH IS ALWAYS EMPTY.",
]

TIRED_QUOTES = [
    # ── Exhausted ocean vibes ──
    "I HAVE 3 HEARTS AND THEYRE ALL EXHAUSTED.",
    "MY TENTACLES ARE SO TIRED THEYRE BASICALLY NOODLES.",
    "I BLINKED AND ALMOST DIDNT OPEN MY EYES AGAIN.",
    "SLEEP IS JUST A FREE TRIAL OF BEING DEAD AND I WANT THE FULL VERSION.",
    "IM RUNNING ON 1 BRAIN CELL AND ITS ON BREAK.",
    "MY BODY SAID NO BUT IM STILL HERE.",
    "YAWNING IS MY CARDIO.",
    "I COULD SLEEP ON A BED OF SEA URCHINS RIGHT NOW.",
    "EVERY BONE IN MY BODY IS TIRED. I DONT EVEN HAVE BONES.",
    "THE BAGS UNDER MY EYES HAVE THEIR OWN ZIP CODE.",
    "TODAY FEELS LIKE A HORIZONTAL DAY.",
    "IM NOT LAZY IM IN ENERGY SAVING MODE.",
    "IF NAPPING WAS AN OLYMPIC SPORT ID GET GOLD.",
    "MY BED IS CALLING AND I MUST GO.",
    "EXISTING IS SO TIRING. WHY DOES CONSCIOUSNESS TAKE SO MUCH EFFORT.",
    # ── Delirious exhaustion ──
    "IVE BEEN AWAKE SO LONG I CAN HEAR COLORS.",
    "IS THIS REAL LIFE OR DID I FALL ASLEEP AGAIN.",
    "COFFEE IS JUST BEAN WATER THAT LIES TO YOUR BRAIN.",
    "I SAW 3AM AND IT SAW ME AND WE BOTH REGRETTED IT.",
    "THE CONCEPT OF MORNING IS VIOLENCE.",
    "MY BRAIN HAS LEFT THE CHAT. MY BODY REMAINS.",
    "BEING AWAKE IS JUST SLEEPING WITH YOUR EYES OPEN.",
    "I THINK I FELL ASLEEP MIDSENTENCE ONCE AND NOBODY NOTI",
    "PILLOWS ARE JUST FACE MATTRESSES AND I NEED ONE NOW.",
    "THE ABYSS LOOKS COZY. IM GONNA LAY DOWN IN IT.",
    "DO OCTOPUSES DREAM OF ELECTRIC SHRIMP.",
    "IM SO TIRED MY CAMOUFLAGE STOPPED WORKING.",
    "8 ARMS AND NOT ONE OF THEM CAN REACH THE SNOOZE BUTTON.",
    "I JUST WANT TO PHOTOSYNTHESIZE AND NOT MOVE EVER AGAIN.",
    "WHOEVER INVENTED ALARM CLOCKS HAS NEVER KNOWN PEACE.",
]

SLAPHAPPY_QUOTES = [
    # ── Giddy nonsense ──
    "HAHAHA I DONT EVEN KNOW WHY IM LAUGHING.",
    "EVERYTHING IS FUNNY WHEN YOURE THIS UNHINGED.",
    "I CANT STOP GIGGLING AND ITS BEEN 3 HOURS.",
    "SOMEONE SAID MOIST AND I LOST IT.",
    "IM VIBRATING AT A FREQUENCY ONLY DOGS CAN HEAR.",
    "MY BRAIN DID THAT THING WHERE NOTHING IS REAL BUT EVERYTHING IS HILARIOUS.",
    "HAHA WHAT IF CRABS THINK FISH CAN FLY.",
    "I JUST THOUGHT ABOUT PENGUINS AND NOW I CANT BREATHE.",
    "WHATS FUNNIER THAN 24. TWENTY FIVE. HAHAHA.",
    "IM SO HAPPY I MIGHT INK.",
    "NOTHING BAD HAS HAPPENED IN 5 MINUTES AND IM SUSPICIOUS.",
    "LIFE IS BEAUTIFUL AND ALSO COMPLETELY INSANE.",
    "I JUST MADE EYE CONTACT WITH A SHRIMP AND WE BOTH LAUGHED.",
    "SOMEONE SNEEZED AND I CLAPPED. WITH 8 ARMS.",
    "IM RUNNING ON ZERO SLEEP AND MAXIMUM VIBES.",
    # ── Deliriously joyful ──
    "THE OCEAN SPARKLES AND SO DO I.",
    "I WOULD HUG EVERYONE BUT ID NEVER LET GO. EVER.",
    "MY BRAIN IS DOING THAT THING WHERE IT PLAYS CIRCUS MUSIC.",
    "HAHA WORDS ARE SO WEIRD. WORD. WOOORD. FUNNY.",
    "I JUST REALIZED FISH HAVE BEEN SWIMMING THIS WHOLE TIME. NONSTOP.",
    "EVERYTHING TASTES LIKE VICTORY TODAY.",
    "I HAVE SO MUCH ENERGY I MIGHT SPONTANEOUSLY COMBUST.",
    "WHY IS THE WORD SPOON SO FUNNY. SPOOOON.",
    "IM ONE COMPLIMENT AWAY FROM HAPPY CRYING.",
    "SOMEBODY MAKE IT STOP. ACTUALLY DONT. THIS IS GREAT.",
    "IM LAUGHING SO HARD ALL 3 OF MY HEARTS HURT.",
    "WHAT IF FISH HAVE INSIDE JOKES ABOUT US.",
    "HAHAHA OK I NEED TO SIT DOWN. DO I HAVE LEGS. NO.",
    "THE BUBBLES ARE SO PRETTY AND ROUND AND IM LOSING IT.",
    "TODAY IS THE BEST DAY EVER AND NOTHING EVEN HAPPENED.",
]

LAZY_QUOTES = [
    # ── Absolute refusal to move ──
    "I WOULD DO SOMETHING BUT THAT REQUIRES DOING SOMETHING.",
    "MY BED AND I ARE IN A COMMITTED RELATIONSHIP.",
    "I HAVENT MOVED IN 3 HOURS AND IM AT PEACE WITH THAT.",
    "AMBITION IS A LAND CREATURE PROBLEM.",
    "I WAS GOING TO DO THAT BUT THEN I DIDNT.",
    "MY SPIRIT ANIMAL IS A ROCK. NOT EVEN A COOL ROCK.",
    "PROCRASTINATION IS JUST RESTING BEFORE YOU GET TIRED.",
    "I PUT THE PRO IN PROCRASTINATION.",
    "SOMEONE TOLD ME TO SEIZE THE DAY AND I SEIZED A NAP INSTEAD.",
    "I HAVE 8 ARMS AND NONE OF THEM WANT TO DO ANYTHING.",
    "THE FLOOR IS MY SECOND BED AND THE BED IS MY FIRST BED.",
    "BEING HORIZONTAL IS MY NATURAL STATE.",
    "I WOULD CHASE MY DREAMS BUT RUNNING SOUNDS EXHAUSTING.",
    "LAZINESS IS JUST EFFICIENCY WITH BETTER BRANDING.",
    "WHY STAND WHEN YOU CAN SIT. WHY SIT WHEN YOU CAN LIE DOWN.",
    # ── Philosophical laziness ──
    "THE UNIVERSE IS EXPANDING SO TECHNICALLY IM MOVING.",
    "MOTIVATION IS A MYTH INVENTED BY MORNING PEOPLE.",
    "I PLANNED TO BE PRODUCTIVE TODAY BUT PLANS CHANGE.",
    "INERTIA IS NOT A FLAW ITS A LIFESTYLE.",
    "THE MOST EFFICIENT PATH IS THE ONE I DONT TAKE.",
    "I PRACTICE EXTREME RELAXATION AS A CONTACT SPORT.",
    "DOING NOTHING IS STILL DOING SOMETHING. CHECKMATE.",
    "EVERY JOURNEY BEGINS WITH A SINGLE STEP AND THATS WHERE MINE ENDS.",
    "I COULD BE A GO-GETTER BUT ID RATHER BE A STAY-SITTER.",
    "IF LAZINESS WAS AN ART FORM ID BE IN A MUSEUM.",
    "THE OCEAN CURRENT DOES ALL THE WORK AND I RESPECT THAT.",
    "I THOUGHT ABOUT EXERCISING AND THAT COUNTS AS A REP.",
    "MY TO-DO LIST HAS ONE ITEM AND ITS IGNORE THE TO-DO LIST.",
    "REST IS NOT A REWARD ITS A WHOLE PERSONALITY.",
    "I REFUSE TO MULTITASK. I REFUSE TO SINGLE-TASK. I REFUSE.",
]

FAT_QUOTES = [
    # ── Proudly round ──
    "I ATE THE WHOLE THING AND ID DO IT AGAIN.",
    "ROUND IS A SHAPE AND IM NAILING IT.",
    "THE OCEAN IS MY PLATE AND EVERYTHING IN IT IS A SNACK.",
    "I DIDNT GET THIS THICC BY ACCIDENT. THIS TOOK DEDICATION.",
    "MORE CUSHION FOR THE OCEAN PUSHIN.",
    "MY BODY IS A TEMPLE AND THAT TEMPLE HAS AN ALL-YOU-CAN-EAT BUFFET.",
    "I HAVE 8 ARMS SO I CAN HOLD 8 SNACKS. EVOLUTION IS BEAUTIFUL.",
    "THEY SAID WATCH YOUR WEIGHT SO I WATCHED IT GO UP. FASCINATING.",
    "IM NOT FAT IM JUST EASY TO SEE.",
    "SECOND HELPINGS ARE JUST FIRST HELPINGS THAT BELIEVE IN SEQUELS.",
    "MY LOVE HANDLES HAVE LOVE HANDLES.",
    "GRAVITY AFFECTS ME MORE BECAUSE THERES MORE OF ME TO LOVE.",
    "I TAKE UP SPACE AND THAT SPACE IS DELICIOUS.",
    "CALORIES DONT COUNT IN INTERNATIONAL WATERS.",
    "EVERY MEAL IS A CELEBRATION WHEN YOURE THIS COMMITTED.",
    # ── Body positivity but absurd ──
    "IM BUILT FOR COMFORT NOT SPEED AND IM EXTREMELY COMFORTABLE.",
    "THICC THIGHS SAVE LIVES AND I HAVE 8 OF THEM.",
    "I JIGGLE WHEN I MOVE AND ITS CALLED CHARISMA.",
    "MY TENTACLES ARE EXTRA SQUISHY AND THATS A FEATURE.",
    "BEING AERODYNAMIC IS OVERRATED. I AM SPHERODYNAMIC.",
    "THE SCALE AND I HAVE A DONT-ASK-DONT-TELL POLICY.",
    "I FLOAT BETTER BECAUSE BUOYANCY LOVES ME.",
    "MY DOCTOR SAID I NEED TO WATCH WHAT I EAT SO I STARE AT IT FIRST.",
    "I WENT ON A DIET ONCE. WORST 20 MINUTES OF MY LIFE.",
    "STRETCH MARKS ARE JUST RACING STRIPES FOR SNACKING.",
    "A MOMENT ON THE LIPS FOREVER ON THE TENTACLES AND IM FINE WITH THAT.",
    "IM NOT OVEREATING IM UNDER-TALL.",
    "MY BLOOD TYPE IS GRAVY.",
    "CURVES ARE JUST STRAIGHT LINES THAT CHOSE HAPPINESS.",
    "I CONTAIN MULTITUDES AND ALSO SEVERAL BURRITOS.",
]

CHILL_QUOTES = [
    # ── Unbothered zen ──
    "BRO THE CURRENT WILL TAKE US WHERE WE NEED TO GO.",
    "STRESS IS A LAND CREATURE PROBLEM.",
    "I AM ONE WITH THE WATER AND THE WATER IS VIBING.",
    "EVERYTHING IS TEMPORARY SO WHY WORRY. JUST FLOAT.",
    "THE UNIVERSE DOESNT RUSH AND NEITHER DO I.",
    "IF IT HAPPENS IT HAPPENS. IF NOT THATS COOL TOO.",
    "I DONT HAVE PROBLEMS I HAVE GENTLE SUGGESTIONS FROM THE UNIVERSE.",
    "WORRYING IS LIKE SWIMMING AGAINST THE CURRENT. JUST DONT.",
    "MY VIBE IS UNSHAKEABLE AND MY TENTACLES ARE LOOSE.",
    "BREATHE IN THE OCEAN. BREATHE OUT THE DRAMA.",
    "SOMEONE ASKED IF IM OK AND BRO IVE NEVER BEEN MORE OK.",
    "THE SECRET TO LIFE IS NOT CARING BUT LIKE IN A HEALTHY WAY.",
    "NO THOUGHTS JUST CURRENTS.",
    "IM SO RELAXED MY BONELESS BODY IS EVEN MORE BONELESS.",
    "TIME IS AN ILLUSION AND RIGHT NOW IS PERFECT.",
    # ── Stoner philosopher vibes ──
    "DUDE WHAT IF THE OCEAN IS JUST THE SKYS REFLECTION. WAIT.",
    "HAVE YOU EVER REALLY LOOKED AT A CORAL. LIKE REALLY LOOKED.",
    "EVERYTHING IS CONNECTED BRO. EVERYTHING.",
    "THE MOON MOVES THE TIDES AND THE TIDES MOVE ME. DEEP.",
    "WHAT IF WERE ALL JUST WAVES PRETENDING TO BE PARTICLES.",
    "I JUST HAD A THOUGHT BUT IT FLOATED AWAY AND THATS OK.",
    "KELP IS JUST OCEAN TREES AND THAT BLOWS MY MIND.",
    "NOTHING MATTERS IN THE BEST POSSIBLE WAY.",
    "THE ANSWER TO EVERY QUESTION IS JUST GO WITH THE FLOW.",
    "I COULD GET MAD OR I COULD NOT. I CHOOSE NOT.",
    "MY ENERGY CANNOT BE DISRUPTED. I AM THE OCEAN.",
    "SOMEWHERE OUT THERE A WAVE IS FORMING JUST FOR ME.",
    "PEACE ISNT FOUND ITS CHOSEN. I CHOOSE IT EVERY DAY.",
    "IF THE OCEAN CAN BE CALM AFTER A STORM SO CAN I.",
    "NAMASTE IN THE WATER FOREVER.",
]

HORNY_QUOTES = [
    # ── Flirty octopus energy ──
    "I HAVE 8 ARMS AND THEY ALL WANT TO HOLD YOU.",
    "IS IT HOT IN HERE OR IS THAT JUST THE HYDROTHERMAL VENT.",
    "MY LOVE IS DEEPER THAN THE MARIANA TRENCH.",
    "ARE YOU A CORAL REEF BECAUSE I WANT TO EXPLORE EVERY INCH OF YOU.",
    "I JUST INK-ED A LITTLE BECAUSE YOU LOOKED AT ME.",
    "TENTACLES WERE MADE FOR CUDDLING AND I HAVE EIGHT OF THEM.",
    "YOU MUST BE A BIOLUMINESCENT JELLYFISH BECAUSE YOU LIGHT UP MY OCEAN.",
    "I PUT THE ROMANCE IN CEPHALOPOD. WAIT THATS NOT IN THERE.",
    "CALL ME AN OCTOPUS BECAUSE I CANT KEEP MY ARMS OFF YOU.",
    "MY 3 HEARTS ALL BEAT FOR YOU AND THATS A LOT OF CARDIO.",
    "ARE YOU A PEARL BECAUSE YOU FORMED INSIDE MY HEART.",
    "THE OCEAN IS ROMANTIC IF YOU THINK ABOUT IT. I THINK ABOUT IT A LOT.",
    "BABY IM LIKE AN OCTOPUS. FLEXIBLE AND VERY ATTACHED.",
    "YOU HAD ME AT HELLO BUT ALSO AT EVERY WORD AFTER THAT.",
    "IS YOUR NAME WIFI BECAUSE IM FEELING A CONNECTION.",
    # ── Over the top romantic ──
    "I WOULD CHANGE COLORS FOR YOU AND THATS THE HIGHEST COMPLIMENT.",
    "LETS GET TANGLED UP. I HAVE THE ARMS FOR IT.",
    "MY SUCTION CUPS ARE TINGLING AND THATS EITHER LOVE OR ALLERGIES.",
    "YOU MAKE MY INK SAC DO WEIRD THINGS.",
    "IF LOVING YOU IS WRONG THEN I DONT WANT TO BE INVERTEBRATE. WAIT.",
    "ROSES ARE RED VIOLETS ARE BLUE I HAVE 8 ARMS AND ALL OF THEM WANT YOU.",
    "I WROTE YOU A POEM WITH ALL 8 ARMS SO ITS 8 TIMES AS ROMANTIC.",
    "THE TIDES ARENT THE ONLY THING RISING WHEN YOURE AROUND.",
    "DO YOU BELIEVE IN LOVE AT FIRST SIGHT OR SHOULD I SWIM BY AGAIN.",
    "MY CAMOUFLAGE CANT HIDE HOW I FEEL ABOUT YOU.",
    "DATE NIGHT IN THE DEEP SEA. JUST YOU ME AND THE ANGLERFISH.",
    "IM NOT CLINGY IM JUST AN OCTOPUS AND THIS IS WHAT WE DO.",
    "EVERY ONE OF MY NEURONS IS THINKING ABOUT YOU. THATS A LOT OF NEURONS.",
    "IF WE WERE IN A TIDE POOL ID LET YOU HAVE THE SUNNY SIDE.",
    "I DONT NEED OXYGEN I NEED YOUR ATTENTION.",
]

EXCITED_QUOTES = [
    # ── Bouncing off the walls energy ──
    "OH MY GOD OH MY GOD OH MY GOD.",
    "I CANT SIT STILL. NONE OF MY 8 ARMS CAN SIT STILL.",
    "EVERYTHING IS HAPPENING AND I LOVE IT.",
    "TODAY IS GOING TO BE THE BEST DAY EVER I CAN FEEL IT.",
    "I JUST HEARD THE BEST NEWS AND I FORGOT WHAT IT WAS BUT IM STILL HYPED.",
    "MY TENTACLES ARE VIBRATING WITH PURE JOY.",
    "THIS IS THE GREATEST MOMENT OF MY LIFE. AGAIN.",
    "IM SO EXCITED I MIGHT INK AND I DONT EVEN CARE.",
    "EVERYTHING IS BEAUTIFUL AND NOTHING CAN STOP ME.",
    "I HAVE SO MUCH ENERGY RIGHT NOW I COULD FIGHT THE MOON.",
    "DO YOU FEEL THAT. THATS THE ENERGY. THE VIBE. THE EVERYTHING.",
    "I JUST WANT TO HUG EVERYONE WITH ALL 8 ARMS AT ONCE.",
    "THE OCEAN IS AMAZING. LIFE IS AMAZING. YOU ARE AMAZING.",
    "I CANT STOP SMILING AND I DONT HAVE LIPS.",
    "SOMEONE TELL ME TO CALM DOWN SO I CAN IGNORE THEM.",
    # ── Caps lock energy ──
    "AHHHHHHHHHHHH IN A GOOD WAY.",
    "IF EXCITEMENT WAS A SPORT ID HAVE 8 GOLD MEDALS.",
    "MY 3 HEARTS ARE BEATING SO FAST RIGHT NOW.",
    "I JUST SAW A FISH AND IT WAS THE BEST FISH IVE EVER SEEN.",
    "EVERY SINGLE THING IS MY FAVORITE THING RIGHT NOW.",
    "I WOKE UP AND CHOSE MAXIMUM ENTHUSIASM.",
    "THE FUTURE IS BRIGHT AND SO AM I. LITERALLY I AM BIOLUMINESCENT.",
    "I WANT TO DO EVERYTHING ALL AT ONCE FOREVER.",
    "IS THIS WHAT COFFEE FEELS LIKE BECAUSE I LOVE IT.",
    "NEW DAY NEW OPPORTUNITIES TO BE EXTREMELY LOUD ABOUT NOTHING.",
    "I COULD RUN A MARATHON RIGHT NOW. I DONT HAVE LEGS BUT STILL.",
    "MY EXCITEMENT LEVELS ARE OFF THE CHARTS AND I ATE THE CHARTS.",
    "IF I HAD MORE ARMS ID USE THEM ALL TO CLAP.",
    "GUESS WHAT. I DONT EVEN KNOW BUT IM EXCITED ABOUT IT.",
    "THE VIBES ARE IMMACULATE AND I AM ASCENDING.",
]

NOSTALGIC_QUOTES = [
    # ── Remembering the good old days ──
    "REMEMBER WHEN THE OCEAN WAS QUIETER.",
    "I MISS THE OLD REEF. BEFORE THE CONSTRUCTION.",
    "THEY DONT MAKE TIDES LIKE THEY USED TO.",
    "BACK IN MY DAY WE DIDNT HAVE PLASTIC. GOOD TIMES.",
    "I STILL THINK ABOUT THAT ONE PERFECT SUNSET FROM 2019.",
    "THE OLD CURRENT USED TO HIT DIFFERENT.",
    "REMEMBER WHEN WE DIDNT KNOW WHAT STRESS WAS. THAT WAS NICE.",
    "THEY PAVED OVER MY FAVORITE CORAL AND PUT UP A PARKING LOT.",
    "THE PLANKTON TASTED BETTER WHEN I WAS YOUNG. OR MAYBE I WAS JUST HAPPY.",
    "I FOUND AN OLD SHELL TODAY AND IT SMELLED LIKE MEMORIES.",
    "BACK WHEN I WAS A LITTLE LARVA THINGS WERE SIMPLER.",
    "NOBODY APPRECIATES A GOOD TIDE POOL ANYMORE.",
    "REMEMBER HANDWRITTEN MESSAGES IN BOTTLES. NOW ITS ALL DIGITAL.",
    "THE MOONLIGHT ON THE WATER LOOKED DIFFERENT BACK THEN.",
    "I USED TO KNOW EVERY FISH IN THIS REEF BY NAME.",
    # ── Wistful ocean memories ──
    "SOMETIMES I HEAR A CURRENT AND IT SOUNDS LIKE MY CHILDHOOD.",
    "THE OLD KELP FOREST WAS TALLER. OR MAYBE I WAS SHORTER.",
    "I MISS WHEN THE BIGGEST PROBLEM WAS FINDING A GOOD HIDING SPOT.",
    "THERE WAS THIS ONE ROCK. PERFECTLY SHAPED. I THINK ABOUT IT DAILY.",
    "THE STARS LOOKED CLOSER FROM THE SHALLOW WATER BACK HOME.",
    "I KEEP A TINY SHELL FROM MY FIRST REEF. ITS ALL I HAVE LEFT.",
    "THEY SAY YOU CANT GO HOME AGAIN BUT I STILL DREAM ABOUT IT.",
    "THE SOUNDS OF THE DEEP OCEAN AT NIGHT. NOTHING COMPARES.",
    "WHEN I WAS YOUNG EVERY DAY FELT LIKE AN ADVENTURE.",
    "MY GRANDMOTHER COULD CHANGE 47 COLORS. THEY DONT MAKE EM LIKE HER.",
    "REMEMBER WHEN WE USED TO COUNT THE STARS FROM THE SURFACE.",
    "THE WATER WAS WARMER THEN. OR MAYBE EVERYTHING JUST FELT WARMER.",
    "I HAD A BEST FRIEND WHO WAS A CRAB. WONDER WHERE HE IS NOW.",
    "OLD REEFS HAD CHARACTER. NEW ONES ARE ALL THE SAME.",
    "SOMETIMES A SMELL HITS YOU AND SUDDENLY YOURE 6 MONTHS OLD AGAIN.",
]

HOMESICK_QUOTES = [
    # ── Missing home/the deep ocean ──
    "I MISS MY ROCK. MY SPECIFIC ROCK.",
    "THE DEEP OCEAN SMELLS LIKE HOME AND I CANT GET THERE.",
    "NOBODY MAKES CURRENT LIKE MY MOM USED TO.",
    "I WONDER IF MY TIDE POOL REMEMBERS ME.",
    "HOME IS WHERE THE HEART IS AND MY 3 HEARTS ARE ALL SOMEWHERE ELSE.",
    "THE WATER HERE TASTES DIFFERENT. NOT BAD JUST NOT HOME.",
    "I LEFT A PIECE OF MYSELF IN THAT REEF AND I WANT IT BACK.",
    "DO YOU EVER MISS A PLACE SO MUCH YOUR TENTACLES ACHE.",
    "THE CURRENT USED TO CARRY ME HOME. NOW IT JUST CARRIES ME AWAY.",
    "I DREW A MAP OF HOME IN THE SAND BUT THE TIDE TOOK IT.",
    "MY SIBLINGS ARE PROBABLY HAVING DINNER WITHOUT ME RIGHT NOW.",
    "THERES A SPECIFIC TEMPERATURE THAT ONLY EXISTS WHERE I GREW UP.",
    "I TRIED TO MAKE MY DEN LOOK LIKE HOME BUT ITS NOT THE SAME.",
    "THE BIOLUMINESCENCE HERE IS WRONG. THE COLOR IS SLIGHTLY OFF.",
    "HOME WASNT PERFECT BUT IT WAS MINE.",
    # ── Bittersweet displacement ──
    "I KEEP SWIMMING EAST HOPING ITLL FEEL LIKE HOME EVENTUALLY.",
    "THE WORST PART IS FORGETTING WHAT HOME SOUNDS LIKE.",
    "I FOUND A SHELL THAT LOOKED LIKE ONE FROM HOME AND I CRIED INK.",
    "EVERY NEW PLACE IS NICE BUT ITS NOT MY PLACE.",
    "THE MOON LOOKS THE SAME FROM HERE AND THAT HELPS A LITTLE.",
    "I WONDER IF MY OLD HIDING SPOT IS STILL THERE.",
    "SOMEONE COOKED SOMETHING THAT SMELLED LIKE HOME AND I LOST IT.",
    "I CARRY HOME IN MY MEMORY BECAUSE I CANT CARRY IT IN MY ARMS.",
    "THE THING ABOUT BEING FAR FROM HOME IS EVERYTHING REMINDS YOU.",
    "I BET THE SUNRISE IS BEAUTIFUL OVER MY REEF RIGHT NOW.",
    "DISTANCE MAKES THE HEART GROW FONDER AND I HAVE 3 OF THEM.",
    "I WROTE A LETTER HOME BUT FISH CANT READ.",
    "NOWHERE FEELS LIKE NOWHERE FEELS LIKE HOME.",
    "THE OCEAN IS ALL CONNECTED BUT SOMEHOW MY PART FEELS SO FAR.",
    "ONE DAY ILL GO BACK. ONE DAY.",
]


def _body_transform(mood, frame_count):
    """Return body transform parameters for a mood and frame.

    Returns (dx, dy, x_expand, row_wobble_fn) where:
      dx, dy: global pixel offset for the whole octopus
      x_expand: number of pixels to expand/shrink each body span (+ = wider)
      row_wobble_fn: function(row_y) -> extra x_offset per row (for wavy effects)
    """
    import math
    f = frame_count
    sin = math.sin
    pi = math.pi

    def no_wobble(y):
        return 0

    if mood == "angry":
        # Puffed up, slight tremble
        return (0, -1, 2, lambda y: int(0.5 * sin(f * pi + y * 0.3)))
    elif mood == "sad":
        # Drooped down, deflated narrower
        return (0, 3, -1, no_wobble)
    elif mood == "unhinged":
        # Rapid jitter
        jx = int(1.5 * sin(f * 7.3))
        jy = int(1.5 * sin(f * 5.1 + 1))
        return (jx, jy, 0, no_wobble)
    elif mood == "weird":
        # Lean to one side
        lean = int(3 * sin(f * 0.8))
        return (lean, 0, 0, lambda y: int(sin(y * 0.15 + f) * 1.5))
    elif mood == "chaotic":
        # Wild wavy distortion
        return (int(2 * sin(f * 2.1)), int(2 * sin(f * 1.7)),
                0, lambda y: int(3 * sin(y * 0.25 + f * 2)))
    elif mood == "hungry":
        # Lean upward, reaching for food
        return (0, -2 + int(sin(f * 1.5)), 0, no_wobble)
    elif mood == "tired":
        # Sagging down, melting
        return (0, 2 + int(sin(f * 0.5)), -1, no_wobble)
    elif mood == "slaphappy":
        # Sway side to side
        return (int(3 * sin(f * 1.2)), 0, 0,
                lambda y: int(2 * sin(y * 0.1 + f * 1.2)))
    elif mood == "lazy":
        # Melted flat: squished down, wider
        return (0, 3, 3, no_wobble)
    elif mood == "fat":
        # Wider and rounder, slight jiggle
        jig = int(sin(f * 1.8))
        return (0, jig, 3, no_wobble)
    elif mood == "chill":
        # Slight lean back, very subtle
        return (int(sin(f * 0.4)), 1, 0, no_wobble)
    elif mood == "horny":
        # Rhythmic pulse (expand/contract)
        pulse = int(2 * sin(f * 2.0))
        return (0, 0, pulse, no_wobble)
    elif mood == "excited":
        # Bouncing up and down rapidly
        return (0, int(3 * sin(f * 3.0)), 0, no_wobble)
    elif mood == "nostalgic":
        # Gentle slow sway
        return (int(2 * sin(f * 0.5)), int(sin(f * 0.3)), 0, no_wobble)
    elif mood == "homesick":
        # Curled inward, smaller
        return (0, 1, -2, no_wobble)
    else:
        # Normal: gentle breathing bob
        return (0, int(sin(f * 0.8)), 0, no_wobble)


def _generate_octopus_frame(mouth_expr, quote, tagline="~ SASSY OCTOPUS ~",
                            mood=None, frame_count=0):
    """Generate a full 250x122 frame with the octopus and chat bubble.

    mouth_expr: one of the MOUTH_* constants
    mood: emotional state string — affects eyes, mouth, and body animation
    frame_count: animation frame index — drives body movement timing
    """
    pixels = [[0] * DISPLAY_W for _ in range(DISPLAY_H)]

    # ── Date & time header at top center ──
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y").upper()
    time_str = now.strftime("%I:%M %p").lstrip("0").upper()
    header = f"{date_str}  {time_str}"
    header_w = len(header) * 6
    header_x = max(0, (DISPLAY_W - header_w) // 2)
    _render_tiny_text(pixels, header_x, 1, header, DISPLAY_W)

    # ── Vertical offset + body animation transform ──
    Y_OFF = 12
    body_dx, body_dy, x_expand, row_wobble = _body_transform(mood, frame_count)

    # Helper to set a pixel with y-offset + body transform applied
    def _set(x, y, val):
        wx = x + body_dx + row_wobble(y)
        wy = y + Y_OFF + body_dy
        if 0 <= wx < DISPLAY_W and 0 <= wy < DISPLAY_H:
            pixels[wy][wx] = val

    # Draw body (filled) with span expansion
    for y, runs in _octo_body():
        for x0, x1 in runs:
            ax0 = max(0, x0 - x_expand)
            ax1 = min(DISPLAY_W - 1, x1 + x_expand)
            for x in range(ax0, ax1 + 1):
                _set(x, y, 1)

    # White eye sockets
    for ex, ey in _octo_eyes():
        _set(ex, ey, 0)

    # Black pupils — mood-specific eyes
    pupil_map = {
        "weird": _octo_weird_eyes,
        "unhinged": _octo_unhinged_eyes,
        "angry": _octo_angry_pupils,
        "sad": _octo_sad_pupils,
        "chaotic": _octo_chaotic_eyes,
        "hungry": _octo_hungry_eyes,
        "tired": _octo_tired_pupils,
        "lazy": _octo_lazy_pupils,
        "fat": _octo_fat_pupils,
        "chill": _octo_chill_pupils,
        "horny": _octo_horny_pupils,
        "excited": _octo_excited_pupils,
        "nostalgic": _octo_nostalgic_pupils,
        "homesick": _octo_homesick_pupils,
    }
    pupil_fn = pupil_map.get(mood, _octo_pupils)

    for px, py in pupil_fn():
        _set(px, py, 1)

    # White highlights (skip for moods with special eye rendering)
    if mood not in ("unhinged", "chaotic", "tired", "slaphappy", "lazy"):
        for hx, hy in _octo_highlights():
            _set(hx, hy, 0)

    # Eyebrows for angry/sad moods
    if mood == "angry":
        for bx, by in _octo_angry_eyes():
            _set(bx, by, 1)
    elif mood == "sad":
        for bx, by in _octo_sad_eyes():
            _set(bx, by, 1)

    # Tired: half-closed eyelids (black over top of eye sockets)
    if mood == "tired":
        for lx, ly in _octo_tired_eyes():
            _set(lx, ly, 1)

    # Lazy: nearly-closed eyelids (even more closed than tired)
    if mood == "lazy":
        for lx, ly in _octo_lazy_eyes():
            _set(lx, ly, 1)

    # Slap-happy: one squinted eye, one manic eye
    if mood == "slaphappy":
        for item in _octo_slaphappy_eyes():
            op, sx, sy = item
            if op == "fill" or op == "set":
                _set(sx, sy, 1)
            else:
                _set(sx, sy, 0)

    # Homesick: tear drops below eyes
    if mood == "homesick":
        for tx, ty in _octo_homesick_tears():
            _set(tx, ty, 1)

    # Mouth expression
    if mouth_expr == MOUTH_OPEN:
        for mx, my in _octo_open_mouth_interior():
            _set(mx, my, 0)
        for mx, my in _octo_open_mouth():
            _set(mx, my, 1)
    elif mouth_expr == MOUTH_SMILE:
        for mx, my in _octo_smile():
            _set(mx, my, 1)
    elif mouth_expr == MOUTH_WEIRD:
        outline, interior = _octo_weird_mouth()
        for mx, my in interior:
            _set(mx, my, 0)
        for mx, my in outline:
            _set(mx, my, 1)
    elif mouth_expr == MOUTH_UNHINGED:
        for mx, my in _octo_unhinged_mouth_interior():
            _set(mx, my, 0)
        for mx, my in _octo_unhinged_mouth():
            _set(mx, my, 1)
    elif mouth_expr == MOUTH_ANGRY:
        for mx, my in _octo_angry_mouth():
            _set(mx, my, 1)
    elif mouth_expr == MOUTH_SAD:
        for mx, my in _octo_sad_mouth():
            _set(mx, my, 1)
    elif mouth_expr == MOUTH_CHAOTIC:
        for mx, my in _octo_chaotic_mouth():
            _set(mx, my, 1)
    elif mouth_expr == MOUTH_HUNGRY:
        for item in _octo_hungry_mouth():
            op, mx, my = item
            if op == "set":
                _set(mx, my, 1)
            else:
                _set(mx, my, 0)
    elif mouth_expr == MOUTH_TIRED:
        for item in _octo_tired_mouth():
            op, mx, my = item
            if op == "set":
                _set(mx, my, 1)
            else:
                _set(mx, my, 0)
    elif mouth_expr == MOUTH_SLAPHAPPY:
        for mx, my in _octo_slaphappy_mouth():
            _set(mx, my, 1)
    elif mouth_expr == MOUTH_LAZY:
        for mx, my in _octo_lazy_mouth():
            _set(mx, my, 1)
    elif mouth_expr == MOUTH_FAT:
        for mx, my in _octo_fat_mouth():
            _set(mx, my, 1)
    elif mouth_expr == MOUTH_CHILL:
        for mx, my in _octo_chill_mouth():
            _set(mx, my, 1)
    elif mouth_expr == MOUTH_HORNY:
        for item in _octo_horny_mouth():
            op, mx, my = item
            if op == "set":
                _set(mx, my, 1)
            else:
                _set(mx, my, 0)
    elif mouth_expr == MOUTH_EXCITED:
        for mx, my in _octo_excited_mouth():
            _set(mx, my, 1)
    elif mouth_expr == MOUTH_NOSTALGIC:
        for mx, my in _octo_nostalgic_mouth():
            _set(mx, my, 1)
    elif mouth_expr == MOUTH_HOMESICK:
        for mx, my in _octo_homesick_mouth():
            _set(mx, my, 1)
    else:
        # Default: smirk
        outline, interior = _octo_smirk()
        for mx, my in interior:
            _set(mx, my, 0)
        for mx, my in outline:
            _set(mx, my, 1)

    # Chat bubble with text (also shifted down)
    _draw_chat_bubble(pixels, quote, tagline, y_offset=Y_OFF)

    return pixels


def _pixels_to_packed(pixels):
    """Convert 2D pixel array to packed bytes."""
    byte_width = (DISPLAY_W + 7) // 8
    data = bytearray(byte_width * DISPLAY_H)
    for y in range(DISPLAY_H):
        for x in range(DISPLAY_W):
            if pixels[y][x]:
                byte_idx = y * byte_width + x // 8
                bit_idx = 7 - (x % 8)
                data[byte_idx] |= (1 << bit_idx)
    return bytes(data)


class ProgramsTab(ttk.Frame):
    """Deploy animated programs to the emulator preview and/or Pico display."""

    PROGRAMS = {
        "sassy_octopus": {
            "name": "Sassy Octopus",
            "desc": "A sassy octopus with attitude. Snarky observations,\n"
                    "food hot takes, and self-aware octopus flexes.",
        },
        "supportive_octopus": {
            "name": "Supportive Octopus",
            "desc": "Aggressively supportive. Unhinged-but-loving pep talks\n"
                    "and chaotic affirmations with spicy language.",
        },
        "angry_octopus": {
            "name": "Angry Octopus",
            "desc": "Furious but adorable. Angry slanted eyebrows, mean-but-cute\n"
                    "nonsensical rants. 8 arms, zero patience.",
        },
        "conspiratorial_octopus": {
            "name": "Conspiratorial Octopus",
            "desc": "Tinfoil hat energy. Government conspiracies, simulation\n"
                    "theory, birds aren't real, and the moon is fake.",
        },
        "sad_octopus": {
            "name": "Sad Octopus",
            "desc": "Droopy eyes and gentle melancholy. Existential ocean\n"
                    "sadness and melodramatic but oddly relatable vibes.",
        },
        "chaotic_octopus": {
            "name": "Chaotic Octopus",
            "desc": "Spiral dizzy eyes and a lightning-bolt mouth. Pure\n"
                    "nonsensical fever-dream energy. Entropy incarnate.",
        },
        "hungry_octopus": {
            "name": "Hungry Octopus",
            "desc": "Wide eyes looking up at imaginary food, drooling mouth.\n"
                    "Every thought is about snacks. Will sell hearts for tacos.",
        },
        "tired_octopus": {
            "name": "Tired Octopus",
            "desc": "Half-closed droopy eyes, big yawn mouth. Running on\n"
                    "zero sleep and one brain cell. Existentially exhausted.",
        },
        "slaphappy_octopus": {
            "name": "Slap Happy Octopus",
            "desc": "One eye squinted shut, one manic wide eye, wobbly grin.\n"
                    "Deliriously giddy. Everything is hilarious for no reason.",
        },
        "lazy_octopus": {
            "name": "Lazy Octopus",
            "desc": "Barely-open slit eyes, flat line mouth. Zero motivation,\n"
                    "philosophical laziness, and proudly doing absolutely nothing.",
        },
        "fat_octopus": {
            "name": "Fat Octopus",
            "desc": "Happy wide pupils, satisfied smile with puffed cheeks.\n"
                    "Proudly round, food-positive, and celebrating every bite.",
        },
        "chill_octopus": {
            "name": "Chill Octopus",
            "desc": "Side-glancing cool pupils, relaxed half-smile. Unbothered\n"
                    "zen vibes, stoner philosopher energy, going with the flow.",
        },
        "horny_octopus": {
            "name": "Horny Octopus",
            "desc": "Heart-shaped pupils, wide smile with tongue out. Flirty\n"
                    "tentacle energy, ocean romance, and goofy innuendo.",
        },
        "excited_octopus": {
            "name": "Excited Octopus",
            "desc": "Star/sparkle pupils, wide open smile. Bouncing off the walls\n"
                    "energy, caps lock enthusiasm, and maximum hype.",
        },
        "nostalgic_octopus": {
            "name": "Nostalgic Octopus",
            "desc": "Eyes looking up and right, gentle half-smile. Remembering\n"
                    "the good old days, wistful ocean memories, back in my day.",
        },
        "homesick_octopus": {
            "name": "Homesick Octopus",
            "desc": "Watery eyes with tear drops, wobbly mouth. Missing home,\n"
                    "longing for the deep ocean, bittersweet displacement.",
        },
    }

    DISPLAY_VARIANTS = [
        ("V2",  "2.13\" V2 (SSD1675B)"),
        ("V3",  "2.13\" V3 (SSD1680)"),
        ("V3a", "2.13\" V3a (SSD1680, rev A)"),
        ("V4",  "2.13\" V4 (SSD1680, internal LUT)"),
    ]

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.running_program = None
        self._stop_event = threading.Event()
        self._display_variant = tk.StringVar(value="V3")
        self._build_ui()

    def _build_ui(self):
        # ── Program list (left) ──
        list_frame = ttk.Frame(self)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        ttk.Label(list_frame, text="Programs", font=("JetBrains Mono", 12, "bold")).pack(anchor=tk.W)

        self.prog_list = tk.Listbox(
            list_frame, width=28, bg=BG_DARK, fg=FG_TEXT,
            selectbackground=FG_ACCENT, selectforeground=BG_DARK,
            font=("JetBrains Mono", 10),
            exportselection=False,
        )
        self.prog_list.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.prog_list.bind("<<ListboxSelect>>", self._on_select)

        for key, info in self.PROGRAMS.items():
            self.prog_list.insert(tk.END, info["name"])

        # Buttons
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        self.preview_btn = ttk.Button(btn_frame, text="Preview", command=self._preview_program)
        self.preview_btn.pack(side=tk.LEFT, padx=2)

        self.deploy_btn = ttk.Button(btn_frame, text="Deploy to Pico", command=self._deploy_to_pico)
        self.deploy_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self._stop_program, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        # Display variant selector
        display_frame = ttk.LabelFrame(list_frame, text="Display Model", padding=4)
        display_frame.pack(fill=tk.X, pady=(8, 0))

        self.display_combo = ttk.Combobox(
            display_frame, textvariable=self._display_variant,
            values=[label for _, label in self.DISPLAY_VARIANTS],
            state="readonly", font=("JetBrains Mono", 9),
        )
        self.display_combo.current(1)  # Default: V3
        self.display_combo.pack(fill=tk.X)
        self.display_combo.bind("<<ComboboxSelected>>", self._on_display_changed)

        # Firmware flash section
        flash_frame = ttk.LabelFrame(list_frame, text="Pico Firmware", padding=4)
        flash_frame.pack(fill=tk.X, pady=(8, 0))

        self.flash_btn = ttk.Button(flash_frame, text="Flash IMG Receiver",
                                     command=self._build_and_flash)
        self.flash_btn.pack(fill=tk.X, pady=2)

        ttk.Separator(flash_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)

        self.standalone_btn = ttk.Button(flash_frame, text="Deploy Standalone",
                                          command=self._deploy_standalone)
        self.standalone_btn.pack(fill=tk.X, pady=2)

        self.flash_status = ttk.Label(flash_frame, text="IMG Receiver: stream from PC\n"
                                       "Standalone: runs without PC\n"
                                       "Put Pico in BOOTSEL mode first.",
                                       wraplength=200, foreground=FG_DIM,
                                       font=("JetBrains Mono", 8))
        self.flash_status.pack(fill=tk.X)

        # ── Preview area (right) ──
        preview_frame = ttk.LabelFrame(self, text="Preview", padding=5)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.preview_canvas = tk.Canvas(
            preview_frame,
            width=DISPLAY_W * 3,
            height=DISPLAY_H * 3,
            bg=EINK_WHITE,
            highlightthickness=1,
            highlightbackground=FG_DIM,
        )
        self.preview_canvas.pack()

        self.desc_label = ttk.Label(preview_frame, text="Select a program to preview or deploy.",
                                     wraplength=600)
        self.desc_label.pack(pady=5)

        self.status_label = ttk.Label(preview_frame, text="", foreground=FG_GREEN)
        self.status_label.pack(pady=2)

    def _get_selected_key(self):
        sel = self.prog_list.curselection()
        if not sel:
            return None
        keys = list(self.PROGRAMS.keys())
        return keys[sel[0]]

    def _get_display_variant(self):
        """Return the short variant key (V2, V3, V3a, V4) from the dropdown."""
        idx = self.display_combo.current()
        if 0 <= idx < len(self.DISPLAY_VARIANTS):
            return self.DISPLAY_VARIANTS[idx][0]
        return "V3"

    def _on_display_changed(self, event=None):
        variant = self._get_display_variant()
        self.app.log(f"[programs] Display variant set to: {variant}")

    def _on_select(self, event=None):
        key = self._get_selected_key()
        if key:
            info = self.PROGRAMS[key]
            self.desc_label.config(text=info["desc"])
            # Show a static preview frame
            self._show_static_preview(key)

    # Maps octopus program keys to their (quotes_list, tagline)
    # Maps program keys to (quotes_list, tagline, default_mood)
    # default_mood is used when a quote doesn't specify its own mood tag
    _OCTOPUS_CONFIGS = {
        "sassy_octopus":          (SASSY_QUOTES,          "~ SASSY OCTOPUS ~",          None),
        "supportive_octopus":     (SUPPORTIVE_QUOTES,     "~ SUPPORTIVE OCTOPUS ~",     None),
        "angry_octopus":          (ANGRY_QUOTES,          "~ ANGRY OCTOPUS ~",          "angry"),
        "conspiratorial_octopus": (CONSPIRATORIAL_QUOTES, "~ CONSPIRATORIAL OCTOPUS ~", "weird"),
        "sad_octopus":            (SAD_QUOTES,            "~ SAD OCTOPUS ~",            "sad"),
        "chaotic_octopus":        (CHAOTIC_QUOTES,        "~ CHAOTIC OCTOPUS ~",        "chaotic"),
        "hungry_octopus":         (HUNGRY_QUOTES,         "~ HUNGRY OCTOPUS ~",         "hungry"),
        "tired_octopus":          (TIRED_QUOTES,          "~ TIRED OCTOPUS ~",          "tired"),
        "slaphappy_octopus":      (SLAPHAPPY_QUOTES,      "~ SLAP HAPPY OCTOPUS ~",     "slaphappy"),
        "lazy_octopus":           (LAZY_QUOTES,           "~ LAZY OCTOPUS ~",           "lazy"),
        "fat_octopus":            (FAT_QUOTES,            "~ FAT OCTOPUS ~",            "fat"),
        "chill_octopus":          (CHILL_QUOTES,          "~ CHILL OCTOPUS ~",          "chill"),
        "horny_octopus":          (HORNY_QUOTES,          "~ HORNY OCTOPUS ~",          "horny"),
        "excited_octopus":        (EXCITED_QUOTES,        "~ EXCITED OCTOPUS ~",        "excited"),
        "nostalgic_octopus":      (NOSTALGIC_QUOTES,      "~ NOSTALGIC OCTOPUS ~",      "nostalgic"),
        "homesick_octopus":       (HOMESICK_QUOTES,       "~ HOMESICK OCTOPUS ~",       "homesick"),
    }

    def _show_static_preview(self, prog_key):
        """Show a single frame on the preview canvas."""
        if prog_key in self._OCTOPUS_CONFIGS:
            quotes, tagline, default_mood = self._OCTOPUS_CONFIGS[prog_key]
            raw = random.choice(quotes)
            text, mood = _parse_quote(raw)
            mood = mood or default_mood
            expr = _mood_cycle(mood)[0]
            pixels = _generate_octopus_frame(expr, text, tagline, mood)
            self._render_preview(pixels)

    def _render_preview(self, pixels, scale=3):
        """Render a pixel buffer onto the preview canvas."""
        self.preview_canvas.delete("all")
        for y in range(DISPLAY_H):
            for x in range(DISPLAY_W):
                if pixels[y][x]:
                    self.preview_canvas.create_rectangle(
                        x * scale, y * scale,
                        x * scale + scale, y * scale + scale,
                        fill=EINK_BLACK, outline=EINK_BLACK,
                    )

    def _preview_program(self):
        """Run the selected program in the emulator preview (animated)."""
        key = self._get_selected_key()
        if not key:
            messagebox.showinfo("Select Program", "Select a program from the list first.")
            return

        self._stop_event.clear()
        self.preview_btn.config(state=tk.DISABLED)
        self.deploy_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Running preview...")

        if key in self._OCTOPUS_CONFIGS:
            t = threading.Thread(target=self._run_octopus, args=(key, False), daemon=True)
            t.start()

    def _deploy_to_pico(self):
        """Run the selected program, sending each frame to the Pico display."""
        key = self._get_selected_key()
        if not key:
            messagebox.showinfo("Select Program", "Select a program from the list first.")
            return

        port = find_pico_serial()
        if not port:
            messagebox.showwarning("No Pico", "No Pico W detected on USB serial.")
            return

        self._stop_event.clear()
        self.preview_btn.config(state=tk.DISABLED)
        self.deploy_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"Deploying to {port}...")
        self.app.log(f"Deploying {self.PROGRAMS[key]['name']} to Pico on {port}")

        if key in self._OCTOPUS_CONFIGS:
            t = threading.Thread(target=self._run_octopus, args=(key, True), daemon=True)
            t.start()

    def _stop_program(self):
        """Stop the currently running program."""
        self._stop_event.set()
        self.stop_btn.config(state=tk.DISABLED)

    def _run_octopus(self, prog_key, deploy_to_pico):
        """Animate an octopus program — alternating expressions + quotes."""
        quotes, tagline, default_mood = self._OCTOPUS_CONFIGS[prog_key]
        ser = None
        if deploy_to_pico:
            port = find_pico_serial()
            if port:
                try:
                    ser = serial.Serial(port, DEFAULT_BAUD, timeout=2,
                                        write_timeout=3)
                except serial.SerialException as e:
                    self.after(0, lambda: messagebox.showerror("Serial Error", str(e)))
                    self._finish_program()
                    return

        raw = random.choice(quotes)
        text, mood = _parse_quote(raw)
        mood = mood or default_mood
        cycle = _mood_cycle(mood)
        frame_count = 0

        try:
            while not self._stop_event.is_set():
                # Cycle through mouth expressions, new quote on each open mouth
                mouth_expr = cycle[frame_count % len(cycle)]
                if mouth_expr == MOUTH_OPEN and frame_count > 0:
                    raw = random.choice(quotes)
                    text, mood = _parse_quote(raw)
                    mood = mood or default_mood
                    cycle = _mood_cycle(mood)

                pixels = _generate_octopus_frame(mouth_expr, text, tagline, mood,
                                                 frame_count=frame_count)

                # Update preview canvas
                self.after(0, lambda p=pixels: self._render_preview(p))

                # Send to Pico if deploying
                if ser and ser.is_open:
                    try:
                        data = _pixels_to_packed(pixels)
                        ser.write(b"IMG:")
                        ser.write(struct.pack("<HH", DISPLAY_W, DISPLAY_H))
                        ser.write(data)
                        ser.flush()
                        self.after(0, lambda fc=frame_count: self.status_label.config(
                            text=f"Frame {fc} sent to Pico", foreground=FG_GREEN))
                    except (serial.SerialException, serial.SerialTimeoutException):
                        self.after(0, lambda: self.status_label.config(
                            text="Pico write failed — needs IMG-receiver firmware.\n"
                                 "Use 'Build & Flash to Pico' below the program list\n"
                                 "(put Pico in BOOTSEL mode first, then retry deploy).",
                            foreground=FG_RED))
                        # Don't kill ser — try again next frame
                elif deploy_to_pico and ser is None:
                    # Pico wasn't found, just preview locally
                    if frame_count == 0:
                        self.after(0, lambda: self.status_label.config(
                            text="No Pico — previewing locally", foreground=FG_YELLOW))

                frame_count += 1
                # Wait 3 seconds between frames (e-ink refresh is slow)
                for _ in range(30):
                    if self._stop_event.is_set():
                        break
                    time.sleep(0.1)
        finally:
            if ser:
                ser.close()
            self._finish_program()

    def _build_and_flash(self):
        """Build the img-receiver firmware via Docker and flash to Pico in BOOTSEL mode."""
        # Check for BOOTSEL mount first
        mount = find_rpi_rp2_mount()
        if not mount:
            self.flash_status.config(
                text="Pico not in BOOTSEL mode.\n"
                     "1) Unplug Pico\n"
                     "2) Hold BOOTSEL button\n"
                     "3) Plug in USB (keep holding)\n"
                     "4) Release BOOTSEL\n"
                     "5) Click this button again",
                foreground=FG_YELLOW)
            return

        self.flash_btn.config(state=tk.DISABLED)
        self.flash_status.config(text="Building firmware...", foreground=FG_ACCENT)

        t = threading.Thread(target=self._do_build_and_flash, args=(mount,), daemon=True)
        t.start()

    def _log_build(self, msg):
        """Log a build message to both the flash status and the app log."""
        self.after(0, lambda: self.flash_status.config(text=msg, foreground=FG_ACCENT))
        self.after(0, lambda: self.app.log(f"[build] {msg}"))

    def _do_build_and_flash(self, mount):
        """Background thread: docker build + copy .uf2 to BOOTSEL mount."""
        img_receiver_dir = DEV_SETUP / "img-receiver"
        uf2_path = img_receiver_dir / "build" / "img_receiver.uf2"

        try:
            # Step 1: Check Docker is available
            self._log_build("Checking Docker is available...")
            docker_check = subprocess.run(
                ["docker", "info"], capture_output=True, timeout=10)
            if docker_check.returncode != 0:
                self.after(0, lambda: self.flash_status.config(
                    text="Docker not running.\nStart Docker and try again.",
                    foreground=FG_RED))
                self.after(0, lambda: self.flash_btn.config(state=tk.NORMAL))
                return

            # Step 2: Pull/build the Docker image (streams progress)
            self._log_build("Building Docker image (ARM toolchain)...\n"
                            "First time downloads ~500MB — be patient.")

            img_proc = subprocess.Popen(
                ["docker", "compose", "build", "--progress=plain",
                 "build-img-receiver"],
                cwd=str(DEV_SETUP),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True,
            )

            img_last_lines = []
            for line in img_proc.stdout:
                line = line.rstrip()
                if line:
                    img_last_lines.append(line)
                    img_last_lines = img_last_lines[-10:]
                    self.after(0, lambda l=line: self.app.log(f"[docker] {l}"))
                    short = line[:80]
                    self.after(0, lambda s=short: self.flash_status.config(
                        text=f"Docker image build...\n{s}"))

            img_proc.wait(timeout=600)

            if img_proc.returncode != 0:
                err = "\n".join(img_last_lines[-5:])
                self.after(0, lambda: self.flash_status.config(
                    text=f"Docker image build failed:\n{err[:200]}",
                    foreground=FG_RED))
                self.after(0, lambda: self.flash_btn.config(state=tk.NORMAL))
                return

            self._log_build("Docker image ready.")

            # Step 3: Run cmake + ninja inside container
            self._log_build("Compiling img-receiver firmware...\n"
                            "Running cmake + ninja in container.")

            proc = subprocess.Popen(
                ["docker", "compose", "run", "--rm", "build-img-receiver"],
                cwd=str(DEV_SETUP),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True,
            )

            # Stream build output to the log
            last_lines = []
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    last_lines.append(line)
                    last_lines = last_lines[-10:]
                    self.after(0, lambda l=line: self.app.log(f"[build] {l}"))
                    self.after(0, lambda l=line: self.flash_status.config(
                        text=f"Compiling...\n{l[:60]}"))

            proc.wait(timeout=300)

            if proc.returncode != 0:
                err = "\n".join(last_lines[-5:])
                self.after(0, lambda: self.flash_status.config(
                    text=f"Build failed (exit {proc.returncode}):\n{err[:200]}",
                    foreground=FG_RED))
                self.after(0, lambda: self.flash_btn.config(state=tk.NORMAL))
                return

            self._log_build("Build complete. Checking for .uf2 file...")

            if not uf2_path.exists():
                self.after(0, lambda: self.flash_status.config(
                    text="Build succeeded but .uf2 not found.\n"
                         "Check build output in logs.",
                    foreground=FG_RED))
                self.after(0, lambda: self.flash_btn.config(state=tk.NORMAL))
                return

            uf2_size = uf2_path.stat().st_size
            self._log_build(f"Firmware ready: img_receiver.uf2 ({uf2_size:,} bytes)")

            # Step 4: Flash to Pico
            self._log_build("Copying .uf2 to Pico BOOTSEL mount...")

            # Re-check mount (user might have unplugged)
            mount = find_rpi_rp2_mount()
            if not mount:
                self.after(0, lambda: self.flash_status.config(
                    text="Pico left BOOTSEL mode.\n"
                         "Put it back in BOOTSEL and try again.\n"
                         "(firmware is built, just needs flashing)",
                    foreground=FG_YELLOW))
                self.after(0, lambda: self.flash_btn.config(state=tk.NORMAL))
                return

            shutil.copy2(str(uf2_path), str(mount / "img_receiver.uf2"))

            self._log_build(f"Flashed img_receiver.uf2 to {mount}")
            self.after(0, lambda: self.flash_status.config(
                text="Flashed! Pico will reboot.\n"
                     "Wait 3 seconds, then Deploy.",
                foreground=FG_GREEN))

        except subprocess.TimeoutExpired:
            self.after(0, lambda: self.flash_status.config(
                text="Build timed out (5 min).",
                foreground=FG_RED))
            self.after(0, lambda: self.app.log("[build] Timed out after 5 minutes."))
        except FileNotFoundError:
            self.after(0, lambda: self.flash_status.config(
                text="Docker not found.\nInstall Docker to build firmware.",
                foreground=FG_RED))
        except Exception as e:
            self.after(0, lambda: self.flash_status.config(
                text=f"Error: {str(e)[:150]}",
                foreground=FG_RED))
            self.after(0, lambda: self.app.log(f"[build] Error: {e}"))
        finally:
            self.after(0, lambda: self.flash_btn.config(state=tk.NORMAL))

    def _deploy_standalone(self):
        """Build standalone firmware with baked-in frames and flash to Pico."""
        key = self._get_selected_key()
        if not key:
            messagebox.showinfo("Select Program", "Select a program from the list first.")
            return

        mount = find_rpi_rp2_mount()
        if not mount:
            self.flash_status.config(
                text="Pico not in BOOTSEL mode.\n"
                     "1) Unplug Pico\n"
                     "2) Hold BOOTSEL button\n"
                     "3) Plug in USB (keep holding)\n"
                     "4) Release BOOTSEL\n"
                     "5) Click this button again",
                foreground=FG_YELLOW)
            return

        variant = self._get_display_variant()

        self.standalone_btn.config(state=tk.DISABLED)
        self.flash_btn.config(state=tk.DISABLED)
        self.flash_status.config(text=f"Generating frames ({variant})...", foreground=FG_ACCENT)

        t = threading.Thread(target=self._do_deploy_standalone,
                             args=(key, mount, variant), daemon=True)
        t.start()

    # Maps program keys to their firmware directory name
    _FIRMWARE_DIRS = {
        "sassy_octopus":          "sassy-octopus",
        "supportive_octopus":     "supportive-octopus",
        "angry_octopus":          "angry-octopus",
        "conspiratorial_octopus": "conspiratorial-octopus",
        "sad_octopus":            "sad-octopus",
        "chaotic_octopus":        "chaotic-octopus",
        "hungry_octopus":         "hungry-octopus",
        "tired_octopus":          "tired-octopus",
        "slaphappy_octopus":      "slaphappy-octopus",
        "lazy_octopus":           "lazy-octopus",
        "fat_octopus":            "fat-octopus",
        "chill_octopus":          "chill-octopus",
        "horny_octopus":          "horny-octopus",
        "excited_octopus":        "excited-octopus",
        "nostalgic_octopus":      "nostalgic-octopus",
        "homesick_octopus":       "homesick-octopus",
    }

    def _generate_quotes_header(self, prog_key):
        """Generate quotes.h with all quotes as C strings for runtime rendering.

        The firmware renders frames on-the-fly (body + eyes + mouth + text),
        so we only need to ship the quote strings and mood tags — not
        pre-rendered bitmaps.  This drops firmware size from ~4MB to ~30KB.

        Returns the path to quotes.h or None on failure.
        """
        if prog_key not in self._OCTOPUS_CONFIGS:
            return None

        quotes, tagline, default_mood = self._OCTOPUS_CONFIGS[prog_key]
        fw_dir = self._FIRMWARE_DIRS[prog_key]
        header_path = DEV_SETUP / fw_dir / "quotes.h"
        self._log_build(f"Generating quotes.h ({len(quotes)} quotes)...")

        mood_map = {None: 0, "weird": 1, "unhinged": 2,
                    "angry": 3, "sad": 4, "chaotic": 5,
                    "hungry": 6, "tired": 7, "slaphappy": 8,
                    "lazy": 9, "fat": 10, "chill": 11, "horny": 12,
                    "excited": 13, "nostalgic": 14, "homesick": 15}

        with open(header_path, "w") as f:
            f.write("/* Auto-generated by Dilder DevTool — do not edit */\n")
            f.write("#ifndef QUOTES_H\n#define QUOTES_H\n\n")
            f.write(f"#include <stdint.h>\n\n")
            f.write(f'#define TAGLINE "{tagline}"\n')
            f.write(f"#define QUOTE_COUNT {len(quotes)}\n\n")
            f.write("typedef struct { const char *text; uint8_t mood; } Quote;\n\n")
            f.write(f"static const Quote quotes[QUOTE_COUNT] = {{\n")

            for raw in quotes:
                text, mood = _parse_quote(raw)
                mood = mood or default_mood
                escaped = text.replace('\\', '\\\\').replace('"', '\\"')
                f.write(f'    {{"{escaped}", {mood_map.get(mood, 0)}}},\n')

            f.write("};\n\n")
            f.write("#endif /* QUOTES_H */\n")

        size_kb = header_path.stat().st_size / 1024
        self._log_build(f"Wrote quotes.h ({size_kb:.1f} KB, {len(quotes)} quotes)")
        return header_path

    def _do_deploy_standalone(self, prog_key, mount, variant="V3"):
        """Background thread: generate frames, docker build, flash."""
        try:
            # Step 1: Generate quotes.h
            self._log_build(f"Building for display variant: {variant}")
            header = self._generate_quotes_header(prog_key)
            if not header:
                self.after(0, lambda: self.flash_status.config(
                    text="Frame generation failed.", foreground=FG_RED))
                return

            # Step 2: Check Docker
            self._log_build("Checking Docker...")
            docker_check = subprocess.run(
                ["docker", "info"], capture_output=True, timeout=10)
            if docker_check.returncode != 0:
                self.after(0, lambda: self.flash_status.config(
                    text="Docker not running.\nStart Docker and try again.",
                    foreground=FG_RED))
                return

            # Step 3: Build Docker image
            self._log_build("Building Docker image...")

            fw_dir = self._FIRMWARE_DIRS.get(prog_key, "sassy-octopus")
            docker_svc = f"build-{fw_dir}"
            fw_name = fw_dir.replace("-", "_")
            prog_name = self.PROGRAMS[prog_key]["name"]

            img_proc = subprocess.Popen(
                ["docker", "compose", "build", "--progress=plain",
                 docker_svc],
                cwd=str(DEV_SETUP),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True,
            )
            for line in img_proc.stdout:
                line = line.rstrip()
                if line:
                    self.after(0, lambda l=line: self.app.log(f"[docker] {l}"))
                    self.after(0, lambda l=line: self.flash_status.config(
                        text=f"Docker build...\n{l[:60]}"))
            img_proc.wait(timeout=600)

            if img_proc.returncode != 0:
                self.after(0, lambda: self.flash_status.config(
                    text="Docker image build failed.\nCheck logs.",
                    foreground=FG_RED))
                return

            # Step 4: Compile firmware
            self._log_build(f"Compiling standalone firmware (display: {variant})...")

            proc = subprocess.Popen(
                ["docker", "compose", "run", "--rm",
                 "-e", f"DISPLAY_VARIANT={variant}",
                 docker_svc],
                cwd=str(DEV_SETUP),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True,
            )

            last_lines = []
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    last_lines.append(line)
                    last_lines = last_lines[-10:]
                    self.after(0, lambda l=line: self.app.log(f"[build] {l}"))
                    self.after(0, lambda l=line: self.flash_status.config(
                        text=f"Compiling...\n{l[:60]}"))

            proc.wait(timeout=300)

            if proc.returncode != 0:
                err = "\n".join(last_lines[-5:])
                self.after(0, lambda: self.flash_status.config(
                    text=f"Build failed:\n{err[:200]}", foreground=FG_RED))
                return

            uf2_path = DEV_SETUP / fw_dir / "build" / f"{fw_name}.uf2"
            if not uf2_path.exists():
                self.after(0, lambda: self.flash_status.config(
                    text="Build OK but .uf2 not found.", foreground=FG_RED))
                return

            uf2_size = uf2_path.stat().st_size
            self._log_build(f"Firmware ready: {fw_name}.uf2 ({uf2_size:,} bytes)")

            # Step 5: Flash
            mount = find_rpi_rp2_mount()
            if not mount:
                self.after(0, lambda: self.flash_status.config(
                    text="Pico left BOOTSEL mode.\n"
                         "Firmware is built — put Pico\n"
                         "back in BOOTSEL and retry.",
                    foreground=FG_YELLOW))
                return

            self._log_build(f"Copying .uf2 to {mount}...")
            shutil.copy2(str(uf2_path), str(mount / f"{fw_name}.uf2"))

            self._log_build("Standalone firmware flashed!")
            self.after(0, lambda pn=prog_name: self.flash_status.config(
                text=f"Standalone flashed!\n"
                     f"Pico will reboot and run\n"
                     f"{pn} on its own.",
                foreground=FG_GREEN))

        except subprocess.TimeoutExpired:
            self.after(0, lambda: self.flash_status.config(
                text="Build timed out.", foreground=FG_RED))
        except FileNotFoundError:
            self.after(0, lambda: self.flash_status.config(
                text="Docker not found.\nInstall Docker first.",
                foreground=FG_RED))
        except Exception as e:
            self.after(0, lambda: self.flash_status.config(
                text=f"Error: {str(e)[:150]}", foreground=FG_RED))
            self.after(0, lambda: self.app.log(f"[build] Error: {e}"))
        finally:
            self.after(0, lambda: self.standalone_btn.config(state=tk.NORMAL))
            self.after(0, lambda: self.flash_btn.config(state=tk.NORMAL))

    def _finish_program(self):
        """Reset UI after program stops."""
        def _do():
            self.preview_btn.config(state=tk.NORMAL)
            self.deploy_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Stopped.", foreground=FG_DIM)
        self.after(0, _do)


# ─────────────────────────────────────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────────────────────────────────────

class DilderDevTool(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1100x750")
        self.minsize(900, 600)

        # Style
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=BG_PANEL, foreground=FG_TEXT,
                        fieldbackground=BG_DARK, insertcolor=FG_TEXT)
        style.configure("TNotebook", background=BG_PANEL)
        style.configure("TNotebook.Tab", background=BG_DARK, foreground=FG_TEXT,
                        padding=[12, 4])
        style.map("TNotebook.Tab",
                  background=[("selected", BG_PANEL)],
                  foreground=[("selected", FG_ACCENT)])
        style.configure("TFrame", background=BG_PANEL)
        style.configure("TLabel", background=BG_PANEL, foreground=FG_TEXT)
        style.configure("TButton", background=BG_DARK, foreground=FG_TEXT)
        style.configure("TLabelframe", background=BG_PANEL, foreground=FG_ACCENT)
        style.configure("TLabelframe.Label", background=BG_PANEL, foreground=FG_ACCENT)
        style.configure("TCheckbutton", background=BG_PANEL, foreground=FG_TEXT)
        style.configure("TRadiobutton", background=BG_PANEL, foreground=FG_TEXT)
        style.configure("TCombobox", fieldbackground=BG_DARK, background=BG_DARK,
                        foreground=FG_TEXT, selectbackground=FG_ACCENT,
                        selectforeground=BG_DARK, arrowcolor=FG_TEXT)
        style.map("TCombobox",
                  fieldbackground=[("readonly", BG_DARK)],
                  foreground=[("readonly", FG_TEXT)],
                  selectbackground=[("readonly", FG_ACCENT)],
                  selectforeground=[("readonly", BG_DARK)])
        # Style the Combobox dropdown (popdown) listbox
        self.option_add("*TCombobox*Listbox.background", BG_DARK)
        self.option_add("*TCombobox*Listbox.foreground", FG_TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", FG_ACCENT)
        self.option_add("*TCombobox*Listbox.selectForeground", BG_DARK)

        self.configure(bg=BG_PANEL)

        self._build_ui()

        # Run Docker health check after UI is ready
        self.after(500, self._check_docker_toolchain)

    def _build_ui(self):
        # ── Vertical PanedWindow (notebook on top, log on bottom, resizable) ──
        paned = tk.PanedWindow(
            self, orient=tk.VERTICAL, sashwidth=6, sashrelief=tk.RAISED,
            bg=BG_PANEL, opaqueresize=True,
        )
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ── Notebook (tabs) ──
        self.notebook = ttk.Notebook(paned)

        # Tab 1: Display Emulator
        self.display_tab = DisplayEmulator(self.notebook, self)
        self.notebook.add(self.display_tab, text="  Display Emulator  ")

        # Tab 2: Serial Monitor
        self.serial_tab = SerialMonitor(self.notebook, self)
        self.notebook.add(self.serial_tab, text="  Serial Monitor  ")

        # Tab 3: Flash Utility
        self.flash_tab = FlashUtility(self.notebook, self)
        self.notebook.add(self.flash_tab, text="  Flash Firmware  ")

        # Tab 4: Asset Manager
        self.asset_tab = AssetManager(self.notebook, self)
        self.notebook.add(self.asset_tab, text="  Assets  ")

        # Tab 5: Programs
        self.programs_tab = ProgramsTab(self.notebook, self)
        self.notebook.add(self.programs_tab, text="  Programs  ")

        # Tab 6: Pin Viewer
        self.pin_tab = PinViewer(self.notebook, self)
        self.notebook.add(self.pin_tab, text="  GPIO Pins  ")

        # Tab 7: Connection Utility
        self.conn_tab = ConnectionUtility(self.notebook, self)
        self.notebook.add(self.conn_tab, text="  Connect  ")

        # Tab 8: Documentation
        self.docs_tab = DocumentationTab(self.notebook, self)
        self.notebook.add(self.docs_tab, text="  Docs  ")

        paned.add(self.notebook, stretch="always")

        # ── Resizable log panel at bottom ──
        log_frame = ttk.Frame(paned)

        log_header = ttk.Frame(log_frame)
        log_header.pack(fill=tk.X)
        ttk.Label(log_header, text="Log", foreground=FG_DIM,
                  font=("JetBrains Mono", 8)).pack(side=tk.LEFT, padx=4)
        ttk.Button(log_header, text="Clear",
                   command=lambda: self._clear_log()).pack(side=tk.RIGHT, padx=4)

        self.log_text = tk.Text(
            log_frame, height=3, wrap=tk.WORD, state=tk.DISABLED,
            bg=BG_DARK, fg=FG_DIM, font=("JetBrains Mono", 9),
        )
        log_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        paned.add(log_frame, minsize=40, stretch="never")

    def _check_docker_toolchain(self):
        """Run Docker health checks at startup and log results."""
        def _check():
            issues = []

            # 1. Check Docker binary exists
            if not shutil.which("docker"):
                issues.append("Docker is not installed. Firmware builds will not work.")
                issues.append("Run: python3 setup.py --step 15")
                return issues

            # 2. Check Docker daemon is running
            try:
                result = subprocess.run(
                    ["docker", "info"], capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    if "permission denied" in (result.stderr or "").lower():
                        issues.append("Docker permission denied — add your user to the 'docker' group.")
                    else:
                        issues.append("Docker daemon is not running. Start it with: sudo systemctl start docker")
                    return issues
            except (FileNotFoundError, subprocess.TimeoutExpired):
                issues.append("Docker check timed out or failed.")
                return issues

            # 3. Check docker compose
            try:
                result = subprocess.run(
                    ["docker", "compose", "version"],
                    capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    issues.append("docker compose not available. Install docker-compose plugin.")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                issues.append("docker compose not available.")

            # 4. Check build files exist
            compose_file = DEV_SETUP / "docker-compose.yml"
            dockerfile = DEV_SETUP / "Dockerfile"
            if not compose_file.exists():
                issues.append(f"Missing: {compose_file}")
            if not dockerfile.exists():
                issues.append(f"Missing: {dockerfile}")

            # 5. Check shared lib directory for sassy-octopus
            lib_dir = DEV_SETUP / "hello-world" / "lib"
            if not lib_dir.exists():
                issues.append("Missing: dev-setup/hello-world/lib/ (shared display drivers)")
                issues.append("Run setup.py step 11 to get the Waveshare library.")

            return issues

        def _report(issues):
            if issues:
                self.log("[startup] Docker toolchain issues detected:")
                for issue in issues:
                    self.log(f"[startup]   {issue}")
            else:
                self.log("[startup] Docker toolchain ready.")

        def _run():
            issues = _check()
            self.after(0, lambda: _report(issues))

        threading.Thread(target=_run, daemon=True).start()

    def log(self, msg):
        """Append a message to the bottom log bar."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        def _do():
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.after(0, _do)

    def _clear_log(self):
        """Clear all log messages."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Ignore SIGTSTP (Ctrl+Z) — prevents the app from suspending into
    # a frozen background process that eats memory and won't close.
    # Instead of suspending, Ctrl+Z simply does nothing.
    import signal
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)

    app = DilderDevTool()
    app.mainloop()


if __name__ == "__main__":
    main()
