#!/usr/bin/env python3
"""Generate the Dilder breadboard-prototype wiring guide PDF.

A schematic-style connection diagram for wiring the Dilder PCB firmware on a
breadboard with a Raspberry Pi Pico 2 W. Pin map = the Dilder PCB (SPI0,
GP17-22) so the breadboard validates the exact PCB GPIO assignments.

Outputs:
    Dilder-Breadboard-Wiring.pdf   (2-page vector PDF)
    /tmp/dilder_wiring_preview.png  (preview for review)
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Polygon
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.font_manager as fm

# ── Palette (dark "sick" theme) ──────────────────────────────────────────────
BG      = "#0d1117"
PANEL   = "#161b22"
EDGE    = "#30363d"
PICO    = "#1b3a2b"   # Pico board green
PICO_E  = "#2ea043"
TEXT    = "#e6edf3"
DIM     = "#8b949e"

C_PWR   = "#ff5d5d"   # 3V3
C_GND   = "#c9d1d9"   # GND
C_SPI   = "#3fb6ff"   # SPI0 data/clk/cs
C_CTRL  = "#5ad469"   # display control (DC/RST/BUSY)
C_I2C   = "#ffa94d"   # I2C (accel)
C_INT   = "#ff79c6"   # accel INT
C_BTN   = "#bd93f9"   # joystick buttons
C_SPK   = "#ffd43b"   # speaker

MONO = fm.FontProperties(family="monospace")

# ── Pico 2 W geometry (vertical board, USB at top) ───────────────────────────
BL, BR = 44.0, 56.0          # board left/right x
BT, BB = 88.0, 14.0          # board top/bottom y
PITCH  = (BT - BB) / 19.0     # 20 pins/side

def lpin(p):   # physical pin 1..20 on the left, top->bottom
    return (BL, BT - (p - 1) * PITCH)

def rpin(p):   # physical pin 21..40 on the right, pin40 top -> pin21 bottom
    return (BR, BT - (40 - p) * PITCH)

# Used-pin definitions: (physical_pin, gpio_label, signal, color, side)
LEFT_PINS = [
    (1,  "GP0",  "SDA  (I2C0)",   C_I2C),
    (2,  "GP1",  "SCL  (I2C0)",   C_I2C),
    (4,  "GP2",  "BTN LEFT",      C_BTN),
    (5,  "GP3",  "BTN DOWN",      C_BTN),
    (6,  "GP4",  "BTN UP",        C_BTN),
    (7,  "GP5",  "BTN RIGHT",     C_BTN),
    (9,  "GP6",  "BTN CENTER",    C_BTN),
    (10, "GP7",  "SPEAKER",       C_SPK),
    (8,  "GND",  "GND",           C_GND),
    (20, "GP15", "ACCEL INT1",    C_INT),
]
RIGHT_PINS = [
    (36, "3V3",  "3V3 OUT",       C_PWR),
    (38, "GND",  "GND",           C_GND),
    (22, "GP17", "CS   (SPI0)",   C_SPI),
    (24, "GP18", "SCL  (SPI0)",   C_SPI),
    (25, "GP19", "SDA  (SPI0)",   C_SPI),
    (26, "GP20", "DC",            C_CTRL),
    (27, "GP21", "RES",           C_CTRL),
    (29, "GP22", "BUSY",          C_CTRL),
]


def wire(ax, a, b, color, rad=0.2, lw=2.6):
    """Curved wire with a soft glow."""
    for w, al in ((lw + 4, 0.18), (lw, 1.0)):
        ax.add_patch(FancyArrowPatch(
            a, b, connectionstyle=f"arc3,rad={rad}", arrowstyle="-",
            mutation_scale=1, lw=w, color=color, alpha=al,
            shrinkA=0, shrinkB=0, capstyle="round", zorder=3))


def pin_pad(ax, xy, side, gpio, color):
    """Draw a pin pad sticking out of the board with its GPIO label."""
    x, y = xy
    w, h = 2.0, PITCH * 0.62
    px = x - w if side == "L" else x
    ax.add_patch(Rectangle((px, y - h / 2), w, h, facecolor=color,
                           edgecolor="black", lw=0.4, zorder=4))
    lx = x - w - 0.6 if side == "L" else x + w + 0.6
    ax.text(lx, y, gpio, color=TEXT, fontsize=6.2, fontproperties=MONO,
            ha="right" if side == "L" else "left", va="center", zorder=5)


def card(ax, x, y, w, h, title, sub, accent):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.4",
                                facecolor=PANEL, edgecolor=accent, lw=2.0, zorder=2))
    ax.add_patch(Rectangle((x, y + h - 3.0), w, 3.0, facecolor=accent,
                           edgecolor="none", alpha=0.20, zorder=2))
    ax.text(x + w / 2, y + h - 1.5, title, color=TEXT, fontsize=9.5,
            fontweight="bold", ha="center", va="center", zorder=5)
    ax.text(x + w / 2, y + h - 3.9, sub, color=DIM, fontsize=6.4,
            fontproperties=MONO, ha="center", va="center", zorder=5)


def term(ax, x, y, label, color, side="L"):
    ax.add_patch(Circle((x, y), 0.7, facecolor=color, edgecolor="black",
                        lw=0.4, zorder=6))
    lx = x + 1.3 if side == "L" else x - 1.3
    ax.text(lx, y, label, color=TEXT, fontsize=6.0, fontproperties=MONO,
            ha="left" if side == "L" else "right", va="center", zorder=6)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1 — wiring diagram
# ─────────────────────────────────────────────────────────────────────────────
def page_diagram(pdf):
    fig = plt.figure(figsize=(16.5, 11.2))
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 150)
    ax.set_ylim(0, 102)
    ax.set_aspect("equal")
    ax.axis("off")

    # Title banner
    ax.add_patch(Rectangle((0, 94.5), 150, 7.5, facecolor=PANEL, edgecolor="none"))
    ax.add_patch(Rectangle((0, 94.2), 150, 0.4, facecolor=PICO_E, edgecolor="none"))
    ax.text(4, 98.7, "DILDER  ·  BREADBOARD PROTOTYPE WIRING",
            color=TEXT, fontsize=20, fontweight="bold", va="center")
    ax.text(4, 96.0, "Raspberry Pi Pico 2 W (RP2350)  ·  e-ink on SPI0 (GP17-22)  ·  matches the Dilder PCB pin map",
            color=DIM, fontsize=9.5, fontproperties=MONO, va="center")

    # ── Pico board (shift to a center band) ──
    bx = 24  # x offset to center the board in the 0..150 canvas
    def L(p):
        x, y = lpin(p); return (x + bx, y)
    def R(p):
        x, y = rpin(p); return (x + bx, y)

    ax.add_patch(FancyBboxPatch((BL + bx, BB), BR - BL, BT - BB,
                                boxstyle="round,pad=0.3,rounding_size=1.6",
                                facecolor=PICO, edgecolor=PICO_E, lw=2.4, zorder=2))
    # USB notch
    ax.add_patch(FancyBboxPatch((BL + bx + 3.2, BT - 0.5, ), BR - BL - 6.4, 3.2,
                                boxstyle="round,pad=0.1,rounding_size=0.8",
                                facecolor="#444c56", edgecolor=DIM, lw=1.0, zorder=3))
    ax.text((BL + BR) / 2 + bx, BT + 1.1, "USB-C", color=TEXT, fontsize=6.5,
            fontproperties=MONO, ha="center", va="center", zorder=4)
    ax.text((BL + BR) / 2 + bx, (BT + BB) / 2 + 6, "Raspberry Pi", color=TEXT,
            fontsize=10, ha="center", va="center", rotation=90, zorder=3, alpha=0.85)
    ax.text((BL + BR) / 2 + bx, (BT + BB) / 2 - 10, "Pico 2 W", color=PICO_E,
            fontsize=13, fontweight="bold", ha="center", va="center", rotation=90, zorder=3)

    # draw pads
    pin_xy = {}
    for p, g, s, c in LEFT_PINS:
        xy = L(p); pin_xy[p] = (xy, c, "L"); pin_pad(ax, xy, "L", g, c)
    for p, g, s, c in RIGHT_PINS:
        xy = R(p); pin_xy[p] = (xy, c, "R"); pin_pad(ax, xy, "R", g, c)

    # ── Components ──
    # e-ink display (right)
    dx, dy, dw, dh = 104, 44, 28, 40
    card(ax, dx, dy, dw, dh, "2.13\" e-Paper", "WeAct SSD1680", C_SPI)
    disp_t = {
        "CS":   (dx, dy + 33, C_SPI),
        "SCL":  (dx, dy + 29, C_SPI),
        "SDA":  (dx, dy + 25, C_SPI),
        "DC":   (dx, dy + 21, C_CTRL),
        "RES":  (dx, dy + 17, C_CTRL),
        "BUSY": (dx, dy + 13, C_CTRL),
        "VCC":  (dx, dy + 8,  C_PWR),
        "GND":  (dx, dy + 4,  C_GND),
    }
    for name, (tx, ty, c) in disp_t.items():
        term(ax, tx, ty, name, c, "L")

    # joystick (left)
    jx, jy, jw, jh = 8, 50, 30, 30
    card(ax, jx, jy, jw, jh, "5-Way Joystick", "K1-1506SN-01", C_BTN)
    joy_t = {
        "UP":     (jx + jw, jy + 22, C_BTN),
        "DOWN":   (jx + jw, jy + 18, C_BTN),
        "LEFT":   (jx + jw, jy + 14, C_BTN),
        "RIGHT":  (jx + jw, jy + 10, C_BTN),
        "CENTER": (jx + jw, jy + 6,  C_BTN),
        "COM":    (jx + jw, jy + 2,  C_GND),
    }
    for name, (tx, ty, c) in joy_t.items():
        term(ax, tx, ty, name, c, "R")

    # accelerometer (left, top)
    ax_, ay, aw, ah = 8, 84, 30, 13
    card(ax, ax_, ay, aw, ah, "SC7A20 Accel", "I2C0 · 0x18/0x19", C_I2C)
    acc_t = {
        "SDA": (ax_ + aw, ay + 9, C_I2C),
        "SCL": (ax_ + aw, ay + 6.5, C_I2C),
        "INT": (ax_ + aw, ay + 4, C_INT),
        "VCC": (ax_ + aw, ay + 1.5, C_PWR),
    }
    for name, (tx, ty, c) in acc_t.items():
        term(ax, tx, ty, name, c, "R")

    # speaker (left, bottom)
    sx, sy = 20, 22
    ax.add_patch(Circle((sx, sy), 7.5, facecolor=PANEL, edgecolor=C_SPK, lw=2.0, zorder=2))
    ax.add_patch(Circle((sx, sy), 3.2, facecolor=EDGE, edgecolor=C_SPK, lw=1.2, zorder=3))
    ax.text(sx, sy - 11, "Piezo Speaker", color=TEXT, fontsize=8.5,
            fontweight="bold", ha="center", va="center")
    spk_p = (sx + 7.5, sy + 1.5, C_SPK)
    spk_g = (sx + 7.5, sy - 1.5, C_GND)
    term(ax, *spk_p[:2], "+", C_SPK, "R")
    term(ax, *spk_g[:2], "-", C_GND, "R")

    # ── Wires ──
    # display SPI0 + control + power
    wmap = [
        (22, disp_t["CS"][:2],   C_SPI,  -0.18),
        (24, disp_t["SCL"][:2],  C_SPI,  -0.12),
        (25, disp_t["SDA"][:2],  C_SPI,  -0.06),
        (26, disp_t["DC"][:2],   C_CTRL,  0.05),
        (27, disp_t["RES"][:2],  C_CTRL,  0.12),
        (29, disp_t["BUSY"][:2], C_CTRL,  0.18),
        (36, disp_t["VCC"][:2],  C_PWR,  -0.30),
        (38, disp_t["GND"][:2],  C_GND,  -0.36),
    ]
    for p, b, c, r in wmap:
        wire(ax, pin_xy[p][0], b, c, rad=r)

    # joystick
    for p, name, r in [(6, "UP", 0.15), (5, "DOWN", 0.10), (4, "LEFT", 0.0),
                       (7, "RIGHT", -0.10), (9, "CENTER", -0.18)]:
        wire(ax, pin_xy[p][0], joy_t[name][:2], C_BTN, rad=r)
    wire(ax, pin_xy[8][0], joy_t["COM"][:2], C_GND, rad=-0.25)

    # accel
    wire(ax, pin_xy[1][0], acc_t["SDA"][:2], C_I2C, rad=0.32)
    wire(ax, pin_xy[2][0], acc_t["SCL"][:2], C_I2C, rad=0.30)
    wire(ax, pin_xy[20][0], acc_t["INT"][:2], C_INT, rad=-0.32)
    wire(ax, pin_xy[36][0], acc_t["VCC"][:2], C_PWR, rad=0.28)

    # speaker
    wire(ax, pin_xy[10][0], spk_p[:2], C_SPK, rad=0.25)
    wire(ax, pin_xy[8][0], spk_g[:2], C_GND, rad=0.30)

    # ── Legend ──
    leg = [("3V3 power", C_PWR), ("GND", C_GND), ("SPI0 data/clk/cs", C_SPI),
           ("Display control", C_CTRL), ("I2C (accel)", C_I2C),
           ("Accel INT", C_INT), ("Buttons", C_BTN), ("Speaker", C_SPK)]
    lx0, ly0 = 5, 9.5
    ax.text(lx0, ly0 + 2.2, "WIRE COLOUR KEY", color=TEXT, fontsize=8.5, fontweight="bold")
    for i, (lbl, c) in enumerate(leg):
        col = i % 4
        row = i // 4
        x = lx0 + col * 22
        y = ly0 - row * 3.2
        ax.add_patch(Rectangle((x, y - 0.6), 2.4, 1.2, facecolor=c, edgecolor="black", lw=0.3))
        ax.text(x + 3.2, y, lbl, color=DIM, fontsize=7, fontproperties=MONO, va="center")

    ax.text(146, 1.6, "Dilder · breadboard build · SPI0 / GP17-22",
            color=DIM, fontsize=6.5, fontproperties=MONO, ha="right", va="center")

    pdf.savefig(fig, facecolor=BG)
    fig.savefig("/tmp/dilder_wiring_preview.png", facecolor=BG, dpi=110)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2 — connection table + steps
# ─────────────────────────────────────────────────────────────────────────────
ROWS = [
    ("e-Paper", "CS",   "GP17", "22", C_SPI),
    ("e-Paper", "SCL/CLK", "GP18", "24", C_SPI),
    ("e-Paper", "SDA/DIN", "GP19", "25", C_SPI),
    ("e-Paper", "DC",   "GP20", "26", C_CTRL),
    ("e-Paper", "RES/RST", "GP21", "27", C_CTRL),
    ("e-Paper", "BUSY", "GP22", "29", C_CTRL),
    ("e-Paper", "VCC",  "3V3 OUT", "36", C_PWR),
    ("e-Paper", "GND",  "GND", "38", C_GND),
    ("Joystick", "UP",  "GP4", "6", C_BTN),
    ("Joystick", "DOWN", "GP3", "5", C_BTN),
    ("Joystick", "LEFT", "GP2", "4", C_BTN),
    ("Joystick", "RIGHT", "GP5", "7", C_BTN),
    ("Joystick", "CENTER", "GP6", "9", C_BTN),
    ("Joystick", "COM",  "GND", "8", C_GND),
    ("SC7A20",  "SDA",  "GP0", "1", C_I2C),
    ("SC7A20",  "SCL",  "GP1", "2", C_I2C),
    ("SC7A20",  "INT1", "GP15", "20", C_INT),
    ("SC7A20",  "VCC",  "3V3 OUT", "36", C_PWR),
    ("SC7A20",  "GND",  "GND", "(any GND)", C_GND),
    ("Speaker", "+",    "GP7", "10", C_SPK),
    ("Speaker", "-",    "GND", "(any GND)", C_GND),
]

STEPS = [
    "1. POWER RAILS — Run a red rail from Pico 3V3(OUT) pin 36 and a black rail",
    "   from any GND pin (3, 8, 13, 18, 23, 28, 38). Every VCC/GND below taps these.",
    "2. DISPLAY (SPI0) — Wire the 6 signal lines exactly: CS=GP17, SCL=GP18,",
    "   SDA=GP19, DC=GP20, RES=GP21, BUSY=GP22. VCC->3V3, GND->GND. Keep SCL/SDA short.",
    "3. JOYSTICK — Each direction pin to its GPIO, COM to GND. Internal pull-ups are",
    "   enabled in firmware, so NO external resistors are needed.",
    "4. ACCELEROMETER — SDA=GP0, SCL=GP1 (I2C0), INT1=GP15, VCC=3V3, GND=GND.",
    "5. SPEAKER — Piezo + to GP7, - to GND. (Passive piezo, driven straight off PWM.)",
    "6. POWER — USB-C is enough for the bench. Do NOT also feed VSYS from a second",
    "   supply while USB is connected.",
]

NOTES = [
    ("Board target", "Build/flash as Pico 2 W (pico2_w). This map = the Dilder PCB (SPI0)."),
    ("Display power", "WeAct panel is 3.3 V -> use 3V3(OUT) pin 36, NOT VSYS (5 V)."),
    ("WiFi", "2.4 GHz only (CYW43). picowota bootloader expects WPA2-AES."),
    ("Enter OTA mode", "Hold joystick UP at power-on to drop into the picowota bootloader."),
    ("Heads-up", "GP15 doubles as the accel INT; that's why OTA uses joystick-UP, not GP15."),
]


def page_table(pdf):
    fig = plt.figure(figsize=(16.5, 11.2))
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 150); ax.set_ylim(0, 102); ax.axis("off")

    ax.add_patch(Rectangle((0, 94.5), 150, 7.5, facecolor=PANEL, edgecolor="none"))
    ax.add_patch(Rectangle((0, 94.2), 150, 0.4, facecolor=PICO_E, edgecolor="none"))
    ax.text(4, 98.5, "CONNECTION TABLE  ·  WIRING STEPS", color=TEXT, fontsize=19,
            fontweight="bold", va="center")
    ax.text(4, 95.9, "Tap pin numbers off the Pico 2 W 40-pin header (USB at top, pin 1 top-left)",
            color=DIM, fontsize=9, fontproperties=MONO, va="center")

    # Table (left half)
    tx, tw = 4, 70
    th_y = 90
    headers = ["COMPONENT", "SIGNAL", "PICO GPIO", "PIN #"]
    colx = [tx + 1, tx + 22, tx + 38, tx + 58]
    ax.add_patch(Rectangle((tx, th_y - 1.6), tw, 3.0, facecolor=EDGE, edgecolor="none"))
    for h, x in zip(headers, colx):
        ax.text(x, th_y, h, color=TEXT, fontsize=8, fontweight="bold",
                fontproperties=MONO, va="center")
    rh = 3.6
    for i, (comp, sig, gpio, pin, c) in enumerate(ROWS):
        y = th_y - 2.0 - (i + 1) * rh
        if i % 2 == 0:
            ax.add_patch(Rectangle((tx, y - rh / 2 + 0.4), tw, rh, facecolor=PANEL,
                                   edgecolor="none", alpha=0.6))
        ax.add_patch(Rectangle((tx, y - 1.0), 1.4, 2.0, facecolor=c, edgecolor="none"))
        ax.text(colx[0], y, comp, color=TEXT, fontsize=7.5, fontproperties=MONO, va="center")
        ax.text(colx[1], y, sig, color=DIM, fontsize=7.5, fontproperties=MONO, va="center")
        ax.text(colx[2], y, gpio, color=c, fontsize=7.5, fontproperties=MONO,
                fontweight="bold", va="center")
        ax.text(colx[3], y, pin, color=TEXT, fontsize=7.5, fontproperties=MONO, va="center")

    # Steps (right half, top)
    sx = 80
    ax.text(sx, 90, "WIRING STEPS", color=TEXT, fontsize=11, fontweight="bold")
    for i, line in enumerate(STEPS):
        ax.text(sx, 86.5 - i * 3.0, line, color=DIM, fontsize=7.6,
                fontproperties=MONO, va="top")

    # Notes (right half, bottom) as cards
    ny = 52
    ax.text(sx, ny + 3, "NOTES & GOTCHAS", color=TEXT, fontsize=11, fontweight="bold")
    for i, (k, v) in enumerate(NOTES):
        y = ny - i * 8.4
        ax.add_patch(FancyBboxPatch((sx, y - 6.6), 66, 7.4,
                                    boxstyle="round,pad=0.3,rounding_size=1.0",
                                    facecolor=PANEL, edgecolor=PICO_E, lw=1.2))
        ax.text(sx + 2, y - 1.4, k, color=PICO_E, fontsize=8, fontweight="bold", va="center")
        # wrap value
        words, line, lines = v.split(), "", []
        for w in words:
            if len(line) + len(w) > 58:
                lines.append(line); line = w
            else:
                line = (line + " " + w).strip()
        lines.append(line)
        for j, ln in enumerate(lines[:2]):
            ax.text(sx + 2, y - 3.8 - j * 2.1, ln, color=DIM, fontsize=7,
                    fontproperties=MONO, va="center")

    ax.text(146, 1.6, "Dilder · breadboard build · SPI0 / GP17-22",
            color=DIM, fontsize=6.5, fontproperties=MONO, ha="right", va="center")
    pdf.savefig(fig, facecolor=BG)
    fig.savefig("/tmp/dilder_wiring_preview2.png", facecolor=BG, dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    out = "Dilder-Breadboard-Wiring.pdf"
    with PdfPages(out) as pdf:
        page_diagram(pdf)
        page_table(pdf)
    print("wrote", out)
