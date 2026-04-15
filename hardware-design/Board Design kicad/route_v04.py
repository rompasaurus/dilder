#!/usr/bin/env python3
"""
Dilder v0.4 Router — routes the placed board from build_esp32s3.py.

4-layer strategy:
  F.Cu   — component pads, local traces, short stubs
  In1.Cu — continuous GND plane
  In2.Cu — 3V3 power plane
  B.Cu   — long signal runs, GND pour

Usage: python3 route_v04.py [--no-render]
"""

import pcbnew
import os, sys, json, subprocess

def mm(v): return pcbnew.FromMM(v)
def to_mm(v): return pcbnew.ToMM(v)
def pos(x, y): return pcbnew.VECTOR2I(mm(100 + x), mm(100 + y))

BOARD_FILE = os.path.join(os.path.dirname(__file__) or ".", "dilder.kicad_pcb")
BOARD_W, BOARD_H = 30.0, 70.0
ANTENNA_Y = 5.0  # no copper above this Y

SIG_W = 0.2   # signal trace width mm
PWR_W = 0.4   # power trace width mm
VIA_D = 0.6   # via diameter mm
VIA_DR = 0.3  # via drill mm


# ── Helpers ──────────────────────────────────────────────────────

def add_track(board, x1, y1, x2, y2, width, layer, net):
    """Add a track segment. Coordinates in board mm (not KiCad offset)."""
    if abs(x1 - x2) < 0.01 and abs(y1 - y2) < 0.01:
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pos(x1, y1))
    t.SetEnd(pos(x2, y2))
    t.SetWidth(mm(width))
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)


def add_via(board, x, y, net):
    """Add a through-hole via at board coordinates."""
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pos(x, y))
    v.SetWidth(mm(VIA_D))
    v.SetDrill(mm(VIA_DR))
    v.SetNet(net)
    board.Add(v)


def fcu(board, x1, y1, x2, y2, net, w=None):
    add_track(board, x1, y1, x2, y2, w or SIG_W, pcbnew.F_Cu, net)

def bcu(board, x1, y1, x2, y2, net, w=None):
    add_track(board, x1, y1, x2, y2, w or SIG_W, pcbnew.B_Cu, net)

def fcu_L(board, x1, y1, x2, y2, net, w=None):
    """L-route on F.Cu: vertical first, then horizontal."""
    fcu(board, x1, y1, x1, y2, net, w)
    fcu(board, x1, y2, x2, y2, net, w)

def bcu_L(board, x1, y1, x2, y2, net, w=None):
    """L-route on B.Cu: vertical first, then horizontal."""
    bcu(board, x1, y1, x1, y2, net, w)
    bcu(board, x1, y2, x2, y2, net, w)


# ── Pad collection ───────────────────────────────────────────────

def collect_pads(board):
    """Collect pad positions and net objects from the board.
    Returns (pads, nets) where:
      pads = {net_name: [(x, y, ref, pad_num), ...]}
      nets = {net_name: NETINFO_ITEM}
    Coordinates in board mm (0-based, no 100mm offset).
    """
    pads, nets = {}, {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            net = pad.GetNet()
            if not net or not net.GetNetname():
                continue
            name = net.GetNetname()
            x = round(to_mm(pad.GetPosition().x) - 100, 2)
            y = round(to_mm(pad.GetPosition().y) - 100, 2)
            pads.setdefault(name, []).append((x, y, ref, str(pad.GetNumber())))
            nets[name] = net
    return pads, nets


# ── Inner layer planes ───────────────────────────────────────────

def add_inner_planes(board, nets):
    """Add GND plane on In1.Cu and 3V3 plane on In2.Cu."""
    m = 0.3
    for layer, net_name in [(pcbnew.In1_Cu, "GND"), (pcbnew.In2_Cu, "3V3")]:
        if net_name not in nets:
            continue
        zone = pcbnew.ZONE(board)
        zone.SetNet(nets[net_name])
        zone.SetLayer(layer)
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        zone.SetMinThickness(mm(0.2))
        zone.SetThermalReliefGap(mm(0.3))
        zone.SetThermalReliefSpokeWidth(mm(0.4))
        o = zone.Outline()
        o.NewOutline()
        o.Append(mm(100 + m), mm(100 + ANTENNA_Y))
        o.Append(mm(100 + BOARD_W - m), mm(100 + ANTENNA_Y))
        o.Append(mm(100 + BOARD_W - m), mm(100 + BOARD_H - m))
        o.Append(mm(100 + m), mm(100 + BOARD_H - m))
        board.Add(zone)
    print("  Added In1.Cu GND plane + In2.Cu 3V3 plane")


# ── Channel routing (B.Cu vertical + F.Cu stubs) ────────────────

# B.Cu vertical channel X assignments (only nets that work well as simple channels)
CHANNELS = {
    "I2C_SCL":     2.0,
    "I2C_SDA":     4.0,   # offset from EN at 3.5
    "ACCEL_INT1":  6.5,
}
# BOOT, USB, Joystick use custom routes to avoid crossing issues


def route_channels(board, pads, nets):
    """Route nets that need B.Cu vertical channels."""
    routed = 0
    for name, ch_x in CHANNELS.items():
        if name not in pads or name not in nets:
            continue
        net = nets[name]
        pad_list = sorted(pads[name], key=lambda p: p[1])  # sort by Y

        # Place via + F.Cu stub at each pad
        for px, py, ref, pn in pad_list:
            fcu(board, px, py, ch_x, py, net)
            add_via(board, ch_x, py, net)

        # B.Cu vertical connecting all vias
        for i in range(len(pad_list) - 1):
            bcu(board, ch_x, pad_list[i][1], ch_x, pad_list[i + 1][1], net)

        routed += 1

    print(f"  Routed {routed} channel nets")


# ── ePaper SPI routing (staggered B.Cu L-routes, crossing-free) ─

# Ordered: rightmost ESP32 pin gets lowest horizontal Y → no crossings
EPD_ROUTES = [
    # (net_name, esp32_pin_x, horiz_y, j3_pin_x)
    ("EPD_BUSY",  15.00, 40.0, 26.50),
    ("EPD_CS",    13.73, 41.0, 23.50),
    ("EPD_RST",   12.46, 42.0, 25.50),
    ("EPD_DC",    11.19, 43.0, 24.50),
    ("EPD_MOSI",   9.92, 44.0, 21.50),
    ("EPD_CLK",    8.65, 45.0, 22.50),
]


def route_epaper(board, pads, nets):
    """Route ePaper SPI signals with staggered B.Cu L-routes."""
    for name, esp_x, horiz_y, j3_x in EPD_ROUTES:
        if name not in nets:
            continue
        net = nets[name]

        # ESP32 end: short F.Cu stub south from pin, then via to B.Cu
        fcu(board, esp_x, 27.5, esp_x, 28.5, net)
        add_via(board, esp_x, 28.5, net)

        # B.Cu L-route: vertical down → horizontal → vertical down
        bcu(board, esp_x, 28.5, esp_x, horiz_y, net)
        bcu(board, esp_x, horiz_y, j3_x, horiz_y, net)
        bcu(board, j3_x, horiz_y, j3_x, 48.0, net)

        # J3 end: via up to F.Cu, short stub to J3 pin
        add_via(board, j3_x, 48.0, net)
        fcu(board, j3_x, 48.0, j3_x, 47.0, net)

    print("  Routed 6 ePaper SPI signals (staggered B.Cu)")


# ── USB routing (custom B.Cu, left edge) ────────────────────────

def route_usb(board, nets):
    """Route USB_DM and USB_DP via B.Cu on left edge.
    Each J1 pad is reached independently from below (no horizontal
    jumper across the connector pads at y=71.10).
    """
    # USB_DM: U1.13 (5.50, 17.29) → J1.B7 (13.75, 71.10) + J1.A7 (15.75, 71.10)
    if "USB_DM" in nets:
        net = nets["USB_DM"]
        # U1 end: stub left, via to B.Cu
        fcu(board, 5.50, 17.29, 1.5, 17.29, net)
        add_via(board, 1.5, 17.29, net)
        # B.Cu vertical down left edge
        bcu(board, 1.5, 17.29, 1.5, 69.5, net)
        # Branch to J1.B7 (x=13.75)
        add_via(board, 1.5, 69.5, net)
        fcu(board, 1.5, 69.5, 13.75, 69.5, net)
        fcu(board, 13.75, 69.5, 13.75, 71.10, net)
        # Branch to J1.A7 (x=15.75) via B.Cu to avoid crossing CC1
        bcu(board, 1.5, 69.5, 15.75, 69.5, net)
        add_via(board, 15.75, 69.5, net)
        fcu(board, 15.75, 69.5, 15.75, 71.10, net)

    # USB_DP: U1.14 (5.50, 18.56) → J1.B6 (14.25, 71.10) + J1.A6 (15.25, 71.10)
    if "USB_DP" in nets:
        net = nets["USB_DP"]
        fcu(board, 5.50, 18.56, 0.5, 18.56, net)
        add_via(board, 0.5, 18.56, net)
        bcu(board, 0.5, 18.56, 0.5, 68.5, net)
        # Branch to J1.B6 (x=14.25)
        add_via(board, 0.5, 68.5, net)
        fcu(board, 0.5, 68.5, 14.25, 68.5, net)
        fcu(board, 14.25, 68.5, 14.25, 71.10, net)
        # Branch to J1.A6 (x=15.25) via B.Cu
        bcu(board, 0.5, 68.5, 15.25, 68.5, net)
        add_via(board, 15.25, 68.5, net)
        fcu(board, 15.25, 68.5, 15.25, 71.10, net)

    print("  Routed USB_DM + USB_DP (B.Cu left edge)")


# ── Joystick routing (staggered B.Cu L-routes) ──────────────────

# Staggered Y levels for B.Cu horizontals to avoid crossings
# Ordered so left-most source gets highest Y (same principle as ePaper)
JOY_ROUTES = [
    # (net, u1_y, ch_x, horiz_y, sw1_x, sw1_y)
    ("JOY_CENTER", 12.21, 7.0,  56.0, 16.35, 60.0),
    ("JOY_RIGHT",  10.94, 8.0,  55.0, 15.45, 60.0),
    ("JOY_LEFT",    9.67, 9.0,  54.0, 14.55, 60.0),
    ("JOY_DOWN",    8.40, 10.0, 57.0, 17.25, 58.0),
    ("JOY_UP",      7.13, 11.0, 57.5, 12.75, 58.0),
]


def route_joystick(board, nets):
    """Route joystick signals with staggered B.Cu L-routes."""
    for name, u1_y, ch_x, horiz_y, sw_x, sw_y in JOY_ROUTES:
        if name not in nets:
            continue
        net = nets[name]

        # U1 end: F.Cu stub from pin → via (under module body, safe)
        fcu(board, 5.50, u1_y, ch_x, u1_y, net)
        add_via(board, ch_x, u1_y, net)

        # B.Cu: vertical channel → horizontal at staggered Y → vertical to SW1
        bcu(board, ch_x, u1_y, ch_x, horiz_y, net)
        bcu(board, ch_x, horiz_y, sw_x, horiz_y, net)
        bcu(board, sw_x, horiz_y, sw_x, sw_y, net)

        # SW1 end: via + short F.Cu stub
        add_via(board, sw_x, sw_y, net)
        # No additional stub needed — via is at pad position

    print("  Routed 5 joystick signals (staggered B.Cu)")


# ── EN route (custom multi-zone) ────────────────────────────────

def route_en(board, nets):
    """EN: U1.3 → R10 → SW3 → C8 via custom B.Cu path."""
    if "EN" not in nets:
        return
    net = nets["EN"]

    # U1.3 (5.50, 4.59) → left stub → B.Cu vertical at x=3.5
    fcu(board, 5.50, 4.59, 3.5, 4.59, net)
    add_via(board, 3.5, 4.59, net)

    # B.Cu vertical at x=3.5 from y=4.59 to y=53
    bcu(board, 3.5, 4.59, 3.5, 53.0, net)

    # T-junction via at R10 level for branch
    add_via(board, 3.5, 15.52, net)
    fcu(board, 3.5, 15.52, 3.0, 15.52, net)  # → R10.2

    # B.Cu horizontal at y=53 to SW3 area (under buttons on B.Cu)
    bcu(board, 3.5, 53.0, 19.0, 53.0, net)

    # Via up to F.Cu for SW3 connection
    add_via(board, 19.0, 53.0, net)
    fcu(board, 19.0, 53.0, 19.75, 53.0, net)
    fcu(board, 19.75, 53.0, 19.75, 52.0, net)  # → SW3.1

    # SW3 → C8: route above buttons at y=50 to avoid SW3.2 GND pad
    fcu(board, 19.75, 52.0, 19.75, 50.0, net)
    fcu(board, 19.75, 50.0, 26.0, 50.0, net)
    fcu(board, 26.0, 50.0, 26.0, 52.48, net)  # → C8.1

    print("  Routed EN (custom)")


# ── BOOT route (custom multi-zone) ──────────────────────────────

def route_boot(board, nets):
    """BOOT: U1.27 → R11 → SW2 via B.Cu channel at x=5.0."""
    if "BOOT" not in nets:
        return
    net = nets["BOOT"]

    # U1.27 (5.50, 5.86) → left stub → via
    fcu(board, 5.50, 5.86, 4.5, 5.86, net)
    add_via(board, 4.5, 5.86, net)

    # B.Cu vertical at x=4.5 from y=5.86 to y=52
    bcu(board, 4.5, 5.86, 4.5, 52.0, net)

    # T-junction via at R11 level
    add_via(board, 4.5, 19.52, net)
    fcu(board, 4.5, 19.52, 3.0, 19.52, net)  # → R11.2

    # B.Cu horizontal to SW2 area
    bcu(board, 4.5, 52.0, 5.75, 52.0, net)

    # Via up at SW2.1
    add_via(board, 5.5, 52.0, net)
    fcu(board, 5.5, 52.0, 5.75, 52.0, net)  # → SW2.1

    print("  Routed BOOT (custom)")


# ── LED output routes (CHRG_OUT, STDBY_OUT) ─────────────────────

def route_led_outputs(board, nets):
    """Route CHRG_OUT and STDBY_OUT via B.Cu to cross zone C."""
    # CHRG_OUT: D2.2 (27.0, 7.52) → U2.7 (14.36, 32.30)
    if "CHRG_OUT" in nets:
        net = nets["CHRG_OUT"]
        fcu(board, 27.0, 7.52, 28.0, 7.52, net)
        add_via(board, 28.0, 7.52, net)
        bcu(board, 28.0, 7.52, 28.0, 32.0, net)
        bcu(board, 28.0, 32.0, 14.36, 32.0, net)
        add_via(board, 14.36, 32.0, net)
        fcu(board, 14.36, 32.0, 14.36, 32.30, net)

    # STDBY_OUT: D3.2 (27.0, 15.52) → U2.6 (15.64, 32.30)
    if "STDBY_OUT" in nets:
        net = nets["STDBY_OUT"]
        fcu(board, 27.0, 15.52, 28.5, 15.52, net)
        add_via(board, 28.5, 15.52, net)
        bcu(board, 28.5, 15.52, 28.5, 32.5, net)
        bcu(board, 28.5, 32.5, 15.64, 32.5, net)
        add_via(board, 15.64, 32.5, net)
        fcu(board, 15.64, 32.5, 15.64, 32.30, net)

    print("  Routed CHRG_OUT + STDBY_OUT (B.Cu crossing)")


# ── Battery protection IC routes (OD, OC, CS_DRAIN) ─────────────

def route_protection(board, nets):
    """Route DW01A ↔ FS8205A connections via B.Cu to avoid pad crossings."""
    # OD: U3.1 (6.05, 42.10) → Q1.2 (23.00, 42.10)
    if "OD" in nets:
        net = nets["OD"]
        fcu(board, 6.05, 42.10, 5.5, 42.10, net)
        add_via(board, 5.5, 42.5, net)
        bcu(board, 5.5, 42.5, 23.5, 42.5, net)
        add_via(board, 23.5, 42.5, net)
        fcu(board, 23.5, 42.5, 23.0, 42.5, net)
        fcu(board, 23.0, 42.5, 23.0, 42.10, net)

    # OC: U3.3 (7.95, 42.10) → Q1.5 (23.00, 39.90)
    if "OC" in nets:
        net = nets["OC"]
        fcu(board, 7.95, 42.10, 7.95, 41.0, net)
        add_via(board, 7.95, 41.0, net)
        bcu(board, 7.95, 41.0, 23.5, 41.0, net)
        add_via(board, 23.5, 41.0, net)
        fcu(board, 23.5, 41.0, 23.0, 41.0, net)
        fcu(board, 23.0, 41.0, 23.0, 39.90, net)

    # CS_DRAIN: U3.2 (7.00, 42.10) → Q1.3 (23.95, 42.10) + Q1.4 (23.95, 39.90)
    if "CS_DRAIN" in nets:
        net = nets["CS_DRAIN"]
        fcu(board, 7.0, 42.10, 7.0, 43.0, net)
        add_via(board, 7.0, 43.0, net)
        bcu(board, 7.0, 43.0, 24.5, 43.0, net)
        add_via(board, 24.5, 43.0, net)
        fcu(board, 24.5, 43.0, 23.95, 43.0, net)
        fcu(board, 23.95, 43.0, 23.95, 42.10, net)  # → Q1.3
        fcu(board, 23.95, 42.10, 23.95, 39.90, net)  # → Q1.4

    print("  Routed OD + OC + CS_DRAIN (B.Cu crossings)")


# ── F.Cu power routes ────────────────────────────────────────────

def route_power(board, pads, nets):
    """Route power chain and local power nets on F.Cu."""

    # VBUS: J1.A4 + J1.B4 → D1.1 (each pad routed independently from below)
    if "VBUS" in nets:
        net = nets["VBUS"]
        # Main run: B.Cu from bottom area to D1
        # J1.A4 (12.55, 71.10) — via below, B.Cu to D1
        fcu(board, 12.55, 71.10, 12.55, 67.0, net, PWR_W)
        add_via(board, 12.55, 67.0, net)
        # B.Cu: route along right edge to avoid joystick channels on left
        bcu(board, 12.55, 67.0, 29.0, 67.0, net, PWR_W)
        bcu(board, 29.0, 67.0, 29.0, 35.0, net, PWR_W)
        bcu(board, 29.0, 35.0, 3.5, 35.0, net, PWR_W)
        add_via(board, 3.5, 35.0, net)
        fcu(board, 3.5, 35.0, 3.0, 35.0, net, PWR_W)  # → D1.1
        # J1.B4 (17.45, 71.10) — connect to same B.Cu run
        fcu(board, 17.45, 71.10, 17.45, 67.5, net, PWR_W)
        add_via(board, 17.45, 67.5, net)
        bcu(board, 17.45, 67.5, 12.55, 67.5, net, PWR_W)
        bcu(board, 12.55, 67.5, 12.55, 67.0, net, PWR_W)

    # VBUS_CHG: D1.2 (7.0, 35.0) → U2.8 (13.09, 32.30)
    if "VBUS_CHG" in nets:
        net = nets["VBUS_CHG"]
        fcu(board, 7.0, 35.0, 13.09, 35.0, net, PWR_W)
        fcu(board, 13.09, 35.0, 13.09, 32.30, net, PWR_W)

    # VBAT: C5.1 → U4.3 → U2.3 → U3.4 → U3.5
    if "VBAT" in nets:
        net = nets["VBAT"]
        fcu(board, 4.52, 29.0, 17.30, 29.0, net, PWR_W)   # C5 → U4.3 horizontal
        fcu(board, 17.30, 29.0, 17.30, 32.25, net, PWR_W)  # down to U4.3
        fcu_L(board, 17.30, 32.25, 15.64, 37.70, net, PWR_W)  # → U2.3
        fcu_L(board, 15.64, 37.70, 7.95, 39.90, net, PWR_W)   # → U3.4
        fcu(board, 7.95, 39.90, 7.0, 39.90, net, PWR_W)       # → U3.5

    # BAT_PLUS: Q1.6 (22.05, 39.90) → J2.1 (27.0, 40.0)
    if "BAT_PLUS" in nets:
        net = nets["BAT_PLUS"]
        fcu(board, 22.05, 39.90, 27.0, 39.90, net, PWR_W)
        fcu(board, 27.0, 39.90, 27.0, 40.0, net, PWR_W)

    print("  Routed power chain (VBUS → VBUS_CHG → VBAT → BAT_PLUS)")


# ── F.Cu local signal routes ─────────────────────────────────────

def route_locals(board, nets):
    """Route short local signals on F.Cu."""

    # CC1: R8.1 (6.52, 64.0) → J1.A5 (14.75, 71.10)
    if "CC1" in nets:
        net = nets["CC1"]
        fcu(board, 6.52, 64.0, 14.75, 64.0, net)
        fcu(board, 14.75, 64.0, 14.75, 71.10, net)

    # CC2: R9.1 (6.52, 66.0) → J1.B5 (16.75, 71.10)
    if "CC2" in nets:
        net = nets["CC2"]
        fcu(board, 6.52, 66.0, 16.75, 66.0, net)
        fcu(board, 16.75, 66.0, 16.75, 71.10, net)

    # PROG: R1.1 (23.52, 33.0) → U2.2 (14.36, 37.70)
    if "PROG" in nets:
        net = nets["PROG"]
        fcu_L(board, 23.52, 33.0, 14.36, 37.70, net)

    # CHRG_LED: D2.1 (27.0, 8.48) → R2.2 (27.0, 11.52)
    if "CHRG_LED" in nets:
        fcu(board, 27.0, 8.48, 27.0, 11.52, nets["CHRG_LED"])

    # STDBY_LED: D3.1 (27.0, 16.48) → R3.2 (27.0, 19.52)
    if "STDBY_LED" in nets:
        fcu(board, 27.0, 16.48, 27.0, 19.52, nets["STDBY_LED"])

    print("  Routed local signals (CC1/2, PROG, LEDs)")


# ── 3V3 distribution vias ───────────────────────────────────────

def add_3v3_vias(board, pads, nets):
    """Add vias from 3V3 F.Cu pads to In2.Cu power plane.
    Offset vias vertically to avoid crossing power traces at y=29.
    """
    if "3V3" not in nets:
        return
    net = nets["3V3"]
    count = 0
    for px, py, ref, pn in pads.get("3V3", []):
        # Skip pads in antenna keep-out
        if py < ANTENNA_Y + 1:
            continue
        # Offset via away from pad, avoiding VBAT trace at y=29
        vx = px + 0.8 if px < BOARD_W / 2 else px - 0.8
        vy = py
        if 28.0 < py < 30.0:  # near VBAT horizontal trace
            vy = py + 1.5  # shift south to avoid
        add_via(board, vx, vy, net)
        fcu(board, px, py, vx, py, net, PWR_W)
        if abs(vy - py) > 0.1:
            fcu(board, vx, py, vx, vy, net, PWR_W)
        count += 1
    print(f"  Added {count} 3V3 plane vias")


# ── GND stitching vias ──────────────────────────────────────────

def add_gnd_stitching(board, nets):
    """Add GND stitching vias around the board perimeter."""
    if "GND" not in nets:
        return
    net = nets["GND"]
    count = 0
    m = 1.5
    # Left and right edges
    for y in range(int(ANTENNA_Y) + 3, int(BOARD_H) - 1, 7):
        for x in [m, BOARD_W - m]:
            add_via(board, x, y, net)
            count += 1
    # Top and bottom edges
    for x in range(4, int(BOARD_W) - 1, 7):
        add_via(board, x, ANTENNA_Y + 2, net)
        add_via(board, x, BOARD_H - 2, net)
        count += 2
    print(f"  Added {count} GND stitching vias")


# ── DRC + Render ─────────────────────────────────────────────────

def run_drc(path):
    print("  Running DRC...")
    os.makedirs("/tmp/dilder-drc", exist_ok=True)
    subprocess.run(["kicad-cli", "pcb", "drc",
                    "--output", "/tmp/dilder-drc/drc-report.json",
                    "--format", "json", "--severity-all", path],
                   capture_output=True)
    try:
        with open("/tmp/dilder-drc/drc-report.json") as f:
            drc = json.load(f)
        violations = drc.get("violations", [])
        by_type = {}
        for v in violations:
            t = v.get("type", "?")
            by_type[t] = by_type.get(t, 0) + 1
        uncon = len(drc.get("unconnected_items", []))
        errors = sum(1 for v in violations if v.get("severity") == "error")
        warns = sum(1 for v in violations if v.get("severity") == "warning")
        print(f"  DRC: {errors} errors, {warns} warnings, {uncon} unconnected")
        for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
            print(f"    {t}: {c}")
    except Exception as e:
        print(f"  DRC parse error: {e}")


def render(path):
    print("  Rendering...")
    os.makedirs("/tmp/dilder-v04-routed", exist_ok=True)
    for args, out in [
        ([], "board-top.png"),
        (["--side", "back"], "board-back.png"),
    ]:
        subprocess.run(["kicad-cli", "pcb", "render",
                       "--output", f"/tmp/dilder-v04-routed/{out}",
                       "--width", "2400", "--height", "1600",
                       "--quality", "basic", *args, path],
                      capture_output=True)
    print("  Renders: /tmp/dilder-v04-routed/")


# ── Main ─────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Dilder v0.4 Router")
    print("=" * 55)

    board = pcbnew.LoadBoard(BOARD_FILE)
    fps = list(board.GetFootprints())
    if not fps:
        print("  ERROR: No footprints. Run build_esp32s3.py first.")
        return
    print(f"  Loaded board with {len(fps)} footprints")

    # Clean existing tracks/vias
    removed = 0
    for t in list(board.GetTracks()):
        board.Remove(t)
        removed += 1
    if removed:
        print(f"  Removed {removed} existing tracks/vias")

    # Collect pads and nets
    pads, nets = collect_pads(board)
    print(f"  Found {len(nets)} nets, {sum(len(v) for v in pads.values())} pad connections")

    # Add inner planes (In1.Cu=GND, In2.Cu=3V3)
    add_inner_planes(board, nets)

    # Route signals
    route_channels(board, pads, nets)
    route_epaper(board, pads, nets)
    route_usb(board, nets)
    route_joystick(board, nets)
    route_en(board, nets)
    route_boot(board, nets)
    route_led_outputs(board, nets)
    route_protection(board, nets)
    route_power(board, pads, nets)
    route_locals(board, nets)

    # Power distribution
    add_3v3_vias(board, pads, nets)
    add_gnd_stitching(board, nets)

    # Save
    board.Save(BOARD_FILE)
    print(f"  Saved: {BOARD_FILE}")

    # DRC
    run_drc(BOARD_FILE)

    # Render
    if "--no-render" not in sys.argv:
        render(BOARD_FILE)

    print("  Done!")


if __name__ == "__main__":
    main()
