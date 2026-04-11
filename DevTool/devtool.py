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
import re
import serial
import serial.tools.list_ports
import shutil
import struct
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog, font as tkfont
from pathlib import Path
from datetime import datetime

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
    """Find the Pico W serial port."""
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
        for dy in range(-half, half + size % 1):
            for dx in range(-half, half + size % 1):
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
        """Send the current image to the Pico W via serial."""
        port = find_pico_serial()
        if not port:
            messagebox.showwarning("No Pico", "No Pico W detected on USB serial.")
            return

        data = self._pixels_to_bytes()
        self.app.log(f"Sending {len(data)} bytes to {port}...")

        try:
            with serial.Serial(port, DEFAULT_BAUD, timeout=2) as ser:
                # Protocol: send "IMG:" header followed by raw bytes
                ser.write(b"IMG:")
                ser.write(struct.pack("<HH", DISPLAY_W, DISPLAY_H))
                ser.write(data)
                ser.flush()
            self.app.log(f"Image sent to Pico W ({len(data)} bytes)")
        except serial.SerialException as e:
            messagebox.showerror("Serial Error", str(e))


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
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5, expand=False)

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

        self.configure(bg=BG_PANEL)

        self._build_ui()

    def _build_ui(self):
        # ── Notebook (tabs) ──
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

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

        # Tab 5: Pin Viewer
        self.pin_tab = PinViewer(self.notebook, self)
        self.notebook.add(self.pin_tab, text="  GPIO Pins  ")

        # ── Log bar at bottom ──
        log_frame = ttk.Frame(self)
        log_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.log_text = tk.Text(
            log_frame, height=3, wrap=tk.WORD, state=tk.DISABLED,
            bg=BG_DARK, fg=FG_DIM, font=("JetBrains Mono", 9),
        )
        self.log_text.pack(fill=tk.X)

    def log(self, msg):
        """Append a message to the bottom log bar."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        def _do():
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.after(0, _do)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Ensure pyserial is available
    try:
        import serial
    except ImportError:
        print("pyserial is required. Install with: pip install pyserial")
        sys.exit(1)

    app = DilderDevTool()
    app.mainloop()


if __name__ == "__main__":
    main()
