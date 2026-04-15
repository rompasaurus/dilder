#!/usr/bin/env python3
"""
Dilder PCB v0.5 — Schematic Generator with real footprint references.

Generates a KiCad 10 schematic with:
  - Inline symbol definitions with correct pin mappings (from datasheets)
  - Real footprint references (from KiCad standard + Espressif + JLCPCB libraries)
  - Proper net label wiring
  - Power symbols and flags

Usage:
  cd "Board Design kicad/"
  python3 generate_schematic_v2.py
"""

import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(SCRIPT_DIR, "dilder.kicad_sch")

_counter = 0
def uid():
    global _counter
    _counter += 1
    return f"a{_counter:07x}0-0000-4000-8000-000000000000"


# ═══════════════════════════════════════════════════════════════════════
# INLINE SYMBOL DEFINITIONS
# Pin mappings verified against datasheets / KiCad standard libraries.
# ═══════════════════════════════════════════════════════════════════════

def sym(name, pins_block, props="", extras=""):
    """Helper to build a lib_symbol definition."""
    return (f'    (symbol "{name}" (in_bom yes) (on_board yes)\n'
            f'{props}'
            f'      (symbol "{name}_0_1"\n'
            f'        (rectangle (start -7.62 7.62) (end 7.62 -7.62) '
            f'(stroke (width 0.254) (type default)) (fill (type background)))\n'
            f'      )\n'
            f'      (symbol "{name}_1_1"\n'
            f'{pins_block}'
            f'      )\n'
            f'{extras}'
            f'    )')


def pin(kind, direction, x, y, angle, name, number, length=2.54):
    """Single pin definition."""
    return (f'        (pin {kind} {direction} (at {x} {y} {angle}) (length {length}) '
            f'(name "{name}" (effects (font (size 1.016 1.016)))) '
            f'(number "{number}" (effects (font (size 1.016 1.016)))))\n')


def sym_2pin(name, p1_name="1", p2_name="2"):
    """Simple 2-pin passive component (R, C, LED, diode)."""
    pins = (pin("passive", "line", 0, 3.81, 270, "~", p1_name, 1.27) +
            pin("passive", "line", 0, -3.81, 90, "~", p2_name, 1.27))
    props = ('      (property "Reference" "X" (at 0 2.54 0) (effects (font (size 1.27 1.27))))\n'
             '      (property "Value" "X" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))\n')
    return (f'    (symbol "{name}" (in_bom yes) (on_board yes)\n'
            f'{props}'
            f'      (symbol "{name}_1_1"\n'
            f'{pins}'
            f'      )\n'
            f'    )')


def sym_power(name, pin_number="1"):
    """Power symbol (GND, 3V3, PWR_FLAG)."""
    return (f'    (symbol "{name}" (power) (in_bom no) (on_board no)\n'
            f'      (property "Reference" "#{name}" (at 0 2.54 0) '
            f'(effects (font (size 1.27 1.27)) hide))\n'
            f'      (property "Value" "{name}" (at 0 -2.54 0) '
            f'(effects (font (size 1.27 1.27))))\n'
            f'      (symbol "{name}_0_1"\n'
            f'        (pin power_in line (at 0 0 90) (length 0) '
            f'(name "{name}" (effects (font (size 1.27 1.27)))) '
            f'(number "{pin_number}" (effects (font (size 1.27 1.27)))))\n'
            f'      )\n'
            f'    )')


def build_lib_symbols():
    """Build all lib_symbol definitions."""
    symbols = []

    # ── ESP32-S3-WROOM-1 (41 pins, Espressif datasheet) ──
    # Only defining the pins we actually use
    esp_pins = (
        pin("power_in", "line", 0, 27.94, 270, "3V3", "2") +
        pin("power_in", "line", 0, -27.94, 90, "GND", "1") +
        pin("input", "line", -17.78, 22.86, 0, "EN", "3") +
        # Left side GPIOs
        pin("bidirectional", "line", -17.78, 20.32, 0, "GPIO4", "4") +
        pin("bidirectional", "line", -17.78, 17.78, 0, "GPIO5", "5") +
        pin("bidirectional", "line", -17.78, 15.24, 0, "GPIO6", "6") +
        pin("bidirectional", "line", -17.78, 12.7, 0, "GPIO7", "7") +
        pin("bidirectional", "line", -17.78, 10.16, 0, "GPIO8", "8") +
        pin("bidirectional", "line", -17.78, 7.62, 0, "GPIO15", "23") +
        pin("bidirectional", "line", -17.78, 5.08, 0, "GPIO16", "9") +
        pin("bidirectional", "line", -17.78, 2.54, 0, "GPIO17", "10") +
        pin("bidirectional", "line", -17.78, 0, 0, "GPIO18", "11") +
        pin("bidirectional", "line", -17.78, -2.54, 0, "GPIO19", "13") +
        pin("bidirectional", "line", -17.78, -5.08, 0, "GPIO20", "14") +
        pin("bidirectional", "line", -17.78, -7.62, 0, "GPIO0", "27") +
        # Right side (bottom row on module) — SPI for ePaper
        pin("bidirectional", "line", 17.78, 17.78, 180, "GPIO9", "15") +
        pin("bidirectional", "line", 17.78, 15.24, 180, "GPIO10", "16") +
        pin("bidirectional", "line", 17.78, 12.7, 180, "GPIO3", "17") +
        pin("bidirectional", "line", 17.78, 10.16, 180, "GPIO11", "18") +
        pin("bidirectional", "line", 17.78, 7.62, 180, "GPIO46", "19") +
        pin("bidirectional", "line", 17.78, 5.08, 180, "GPIO12", "20") +
        # Additional GND pins
        pin("passive", "line", 2.54, -27.94, 90, "GND", "40") +
        pin("passive", "line", 5.08, -27.94, 90, "GND", "41")
    )
    esp_props = (
        '      (property "Reference" "U" (at 0 29.21 0) (effects (font (size 1.27 1.27))))\n'
        '      (property "Value" "ESP32-S3-WROOM-1" (at 0 -29.21 0) (effects (font (size 1.27 1.27))))\n'
    )
    symbols.append(
        f'    (symbol "ESP32_S3_WROOM_1" (in_bom yes) (on_board yes)\n'
        f'{esp_props}'
        f'      (symbol "ESP32_S3_WROOM_1_0_1"\n'
        f'        (rectangle (start -15.24 27.94) (end 15.24 -27.94) '
        f'(stroke (width 0.254) (type default)) (fill (type background)))\n'
        f'      )\n'
        f'      (symbol "ESP32_S3_WROOM_1_1_1"\n'
        f'{esp_pins}'
        f'      )\n'
        f'    )'
    )

    # ── TP4056-42-ESOP8 (Battery_Management) ──
    # Pins: 1=TEMP, 2=PROG, 3=GND, 4=VCC, 5=BAT, 6=STDBY, 7=CHRG, 8=CE, 9=EPAD
    tp_pins = (
        pin("input", "line", 10.16, 0, 180, "TEMP", "1") +
        pin("passive", "line", 10.16, -2.54, 180, "PROG", "2") +
        pin("power_in", "line", 0, -12.7, 90, "GND", "3") +
        pin("power_in", "line", 0, 12.7, 270, "VCC", "4") +
        pin("power_out", "line", 10.16, 5.08, 180, "BAT", "5") +
        pin("open_collector", "line", -10.16, -2.54, 0, "~{STDBY}", "6") +
        pin("open_collector", "line", -10.16, 0, 0, "~{CHRG}", "7") +
        pin("input", "line", -10.16, 5.08, 0, "CE", "8") +
        pin("passive", "line", -2.54, -12.7, 90, "EPAD", "9")
    )
    tp_props = (
        '      (property "Reference" "U" (at 0 13.97 0) (effects (font (size 1.27 1.27))))\n'
        '      (property "Value" "TP4056" (at 0 -13.97 0) (effects (font (size 1.27 1.27))))\n'
    )
    symbols.append(sym("TP4056", tp_pins, tp_props))

    # ── DW01A (Battery Protection) ──
    # Pins: 1=OD, 2=CS, 3=OC, 4=TD, 5=VCC, 6=GND
    dw_pins = (
        pin("output", "line", -8.89, 2.54, 0, "OD", "1") +
        pin("input", "line", -8.89, 0, 0, "CS", "2") +
        pin("output", "line", -8.89, -2.54, 0, "OC", "3") +
        pin("input", "line", 8.89, 0, 180, "TD", "4") +
        pin("power_in", "line", 8.89, 2.54, 180, "VCC", "5") +
        pin("power_in", "line", 8.89, -2.54, 180, "GND", "6")
    )
    dw_props = (
        '      (property "Reference" "U" (at 0 6.35 0) (effects (font (size 1.27 1.27))))\n'
        '      (property "Value" "DW01A" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))\n'
    )
    symbols.append(sym("DW01A", dw_pins, dw_props))

    # ── FS8205A (Dual N-MOSFET) ──
    # SOT-23-6: 1=S1, 2=G1, 3=D(shared), 4=D(shared), 5=G2, 6=S2
    fs_pins = (
        pin("passive", "line", -8.89, 5.08, 0, "S1", "1") +
        pin("input", "line", -8.89, 2.54, 0, "G1", "2") +
        pin("passive", "line", -8.89, 0, 0, "D", "3") +
        pin("passive", "line", 8.89, 0, 180, "D", "4") +
        pin("input", "line", 8.89, 2.54, 180, "G2", "5") +
        pin("passive", "line", 8.89, 5.08, 180, "S2", "6")
    )
    fs_props = (
        '      (property "Reference" "Q" (at 0 6.35 0) (effects (font (size 1.27 1.27))))\n'
        '      (property "Value" "FS8205A" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))\n'
    )
    symbols.append(sym("FS8205A", fs_pins, fs_props))

    # ── AMS1117-3.3 (LDO Regulator) ──
    # SOT-223-3: 1=GND/ADJ, 2=Vout, 3=Vin  (tab=pin2)
    ams_pins = (
        pin("power_in", "line", 0, -10.16, 90, "GND", "1") +
        pin("power_out", "line", 10.16, 0, 180, "VO", "2") +
        pin("power_in", "line", -10.16, 0, 0, "VI", "3")
    )
    ams_props = (
        '      (property "Reference" "U" (at 0 6.35 0) (effects (font (size 1.27 1.27))))\n'
        '      (property "Value" "AMS1117-3.3" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))\n'
    )
    symbols.append(sym("AMS1117_3V3", ams_pins, ams_props))

    # ── LIS2DH12TR (Accelerometer) ──
    # LGA-12: 1=SCL/SPC, 2=CS, 3=SDO/SA0, 4=SDA/SDI/SDIO, 5=Res, 6=GND,
    #         7=GND, 8=GND, 9=VDD_IO, 10=Res, 11=INT2, 12=INT1
    # KiCad Sensor_Motion:LIS2DH uses: 1=SCL, 2=SDA, 3=SDO, 4=CS, 5=INT2, 6=INT1,
    #                                   7=Vdd_IO, 8=Vdd, 9=GND (mapped pins)
    # Using datasheet LGA-12 physical pin numbers
    lis_pins = (
        pin("input", "line", -10.16, 5.08, 0, "SCL/SPC", "1") +
        pin("input", "line", -10.16, 2.54, 0, "CS", "2") +
        pin("output", "line", -10.16, 0, 0, "SDO/SA0", "3") +
        pin("bidirectional", "line", -10.16, -2.54, 0, "SDA/SDI", "4") +
        pin("passive", "line", -10.16, -5.08, 0, "Res1", "5") +
        pin("power_in", "line", 0, -10.16, 90, "GND", "6") +
        pin("power_in", "line", 2.54, -10.16, 90, "GND", "7") +
        pin("power_in", "line", 5.08, -10.16, 90, "GND", "8") +
        pin("power_in", "line", 10.16, 5.08, 180, "VDD_IO", "9") +
        pin("passive", "line", 10.16, 2.54, 180, "Res2", "10") +
        pin("output", "line", 10.16, 0, 180, "INT2", "11") +
        pin("output", "line", 10.16, -2.54, 180, "INT1", "12")
    )
    lis_props = (
        '      (property "Reference" "U" (at 0 11.43 0) (effects (font (size 1.27 1.27))))\n'
        '      (property "Value" "LIS2DH12TR" (at 0 -11.43 0) (effects (font (size 1.27 1.27))))\n'
    )
    symbols.append(sym("LIS2DH12TR", lis_pins, lis_props))

    # ── USB-C Receptacle (simplified: VBUS, GND, CC1, CC2, D+, D-, Shield) ──
    usb_pins = (
        pin("power_out", "line", 15.24, 10.16, 180, "VBUS", "A4") +
        pin("bidirectional", "line", 15.24, 5.08, 180, "CC1", "A5") +
        pin("bidirectional", "line", 15.24, 2.54, 180, "D+", "A6") +
        pin("bidirectional", "line", 15.24, 0, 180, "D-", "A7") +
        pin("bidirectional", "line", 15.24, -2.54, 180, "CC2", "B5") +
        pin("bidirectional", "line", 15.24, -5.08, 180, "D+", "B6") +
        pin("bidirectional", "line", 15.24, -7.62, 180, "D-", "B7") +
        pin("power_out", "line", 15.24, 7.62, 180, "VBUS", "B4") +
        pin("power_in", "line", 0, -15.24, 90, "GND", "A1") +
        pin("passive", "line", 2.54, -15.24, 90, "GND", "A12") +
        pin("passive", "line", 5.08, -15.24, 90, "GND", "B1") +
        pin("passive", "line", 7.62, -15.24, 90, "GND", "B12") +
        pin("passive", "line", -7.62, -15.24, 90, "Shield", "S1")
    )
    usb_props = (
        '      (property "Reference" "J" (at 0 16.51 0) (effects (font (size 1.27 1.27))))\n'
        '      (property "Value" "USB-C" (at 0 -16.51 0) (effects (font (size 1.27 1.27))))\n'
    )
    symbols.append(sym("USB_C", usb_pins, usb_props))

    # ── JST-PH 2-pin (Battery) ──
    symbols.append(sym_2pin("JST_PH_2"))

    # ── Conn_01x08 (ePaper header) ──
    epd_pins = ""
    for i in range(8):
        epd_pins += pin("passive", "line", 5.08, 8.89 - i * 2.54, 180,
                        f"Pin_{i+1}", str(i+1))
    epd_props = (
        '      (property "Reference" "J" (at 0 12.7 0) (effects (font (size 1.27 1.27))))\n'
        '      (property "Value" "ePaper" (at 0 -12.7 0) (effects (font (size 1.27 1.27))))\n'
    )
    symbols.append(sym("EPAPER_HDR", epd_pins, epd_props))

    # ── Simple 2-pin components ──
    symbols.append(sym_2pin("R"))
    symbols.append(sym_2pin("C"))
    symbols.append(sym_2pin("LED", "K", "A"))
    symbols.append(sym_2pin("D_Schottky", "K", "A"))

    # ── SW_Push (2 pins) ──
    symbols.append(sym_2pin("SW_Push"))

    # ── Power symbols ──
    symbols.append(sym_power("GND"))
    symbols.append(sym_power("3V3"))
    symbols.append(sym_power("PWR_FLAG"))

    return "\n\n".join(symbols)


# ═══════════════════════════════════════════════════════════════════════
# SCHEMATIC INSTANCE HELPERS
# ═══════════════════════════════════════════════════════════════════════

def inst(lib_id, ref, value, footprint, x, y, angle=0, lcsc="", pin_ids=None):
    """Generate a symbol instance."""
    props = (
        f'    (property "Reference" "{ref}" (at {x} {y-3} 0) '
        f'(effects (font (size 1.27 1.27))))\n'
        f'    (property "Value" "{value}" (at {x} {y+3} 0) '
        f'(effects (font (size 1.27 1.27))))\n'
        f'    (property "Footprint" "{footprint}" (at {x} {y} 0) '
        f'(effects (font (size 1.27 1.27)) hide))\n'
    )
    if lcsc:
        props += (f'    (property "LCSC" "{lcsc}" (at {x} {y} 0) '
                  f'(effects (font (size 1.27 1.27)) hide))\n')

    pin_block = ""
    if pin_ids:
        for p in pin_ids:
            pin_block += f'    (pin "{p}" (uuid "{uid()}"))\n'
    else:
        for i in range(1, 50):
            pin_block += f'    (pin "{i}" (uuid "{uid()}"))\n'

    return (f'  (symbol (lib_id "{lib_id}") (at {x} {y} {angle}) (unit 1) '
            f'(exclude_from_sim no) (in_bom yes) (on_board yes)\n'
            f'    (uuid "{uid()}")\n'
            f'{props}'
            f'{pin_block}'
            f'  )')


def pwr(name, ref_prefix, x, y):
    """Power symbol instance (GND, 3V3)."""
    return (f'  (symbol (lib_id "{name}") (at {x} {y} 0) (unit 1) '
            f'(exclude_from_sim no) (in_bom no) (on_board no)\n'
            f'    (uuid "{uid()}")\n'
            f'    (property "Reference" "#{ref_prefix}" (at {x} {y} 0) '
            f'(effects (font (size 1.27 1.27)) hide))\n'
            f'    (property "Value" "{name}" (at {x} {y+2} 0) '
            f'(effects (font (size 1.27 1.27)) hide))\n'
            f'    (pin "1" (uuid "{uid()}"))\n'
            f'  )')


def gnd(x, y):
    return pwr("GND", "GND", x, y)

def v3(x, y):
    return pwr("3V3", "3V3", x, y)

def w(x1, y1, x2, y2):
    """Wire segment."""
    return (f'  (wire (pts (xy {x1} {y1}) (xy {x2} {y2})) '
            f'(stroke (width 0) (type default)) (uuid "{uid()}"))')

def lbl(name, x, y, angle=0):
    """Net label."""
    return (f'  (label "{name}" (at {x} {y} {angle}) '
            f'(effects (font (size 1.27 1.27))) (uuid "{uid()}"))')


def pp(sx, sy, lx, ly):
    """Pin position: convert local pin coords (lx,ly) to schematic coords.
    Symbol at (sx,sy), pin at local (lx,ly) → schematic (sx+lx, sy-ly)."""
    return (sx + lx, sy - ly)


# ═══════════════════════════════════════════════════════════════════════
# SCHEMATIC LAYOUT AND WIRING
# ═══════════════════════════════════════════════════════════════════════

def build_schematic_body():
    """Build all instances, wires, and labels."""
    parts = []  # All schematic elements

    # Footprint shortcuts
    FP_R = "Resistor_SMD:R_0402_1005Metric"
    FP_C = "Capacitor_SMD:C_0402_1005Metric"
    FP_LED = "LED_SMD:LED_0402_1005Metric"

    # 2-pin passive: pin1 at (0,3.81)→top, pin2 at (0,-3.81)→bottom
    def r_top(sx, sy): return pp(sx, sy, 0, 3.81)
    def r_bot(sx, sy): return pp(sx, sy, 0, -3.81)

    # ────────────────────────────────────────
    # J1: USB-C (x=55, y=55)
    # Pins: VBUS=A4(15.24,10.16→180), CC1=A5(15.24,5.08), D+=A6(15.24,2.54),
    #        D-=A7(15.24,0), CC2=B5(15.24,-2.54), GND=A1(0,-15.24)
    # ────────────────────────────────────────
    J1x, J1y = 55, 55
    parts.append(inst("USB_C", "J1", "USB-C",
                       "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
                       J1x, J1y, lcsc="C2765186",
                       pin_ids=["A4","A5","A6","A7","B4","B5","B6","B7","A1","A12","B1","B12","S1"]))

    vbus_p = pp(J1x, J1y, 15.24, 10.16)
    parts.append(lbl("VBUS", vbus_p[0]+2, vbus_p[1], 0))
    parts.append(w(vbus_p[0], vbus_p[1], vbus_p[0]+2, vbus_p[1]))

    cc1_p = pp(J1x, J1y, 15.24, 5.08)
    parts.append(lbl("CC1", cc1_p[0]+2, cc1_p[1], 0))
    parts.append(w(cc1_p[0], cc1_p[1], cc1_p[0]+2, cc1_p[1]))

    dp_p = pp(J1x, J1y, 15.24, 2.54)
    parts.append(lbl("USB_DP", dp_p[0]+2, dp_p[1], 0))
    parts.append(w(dp_p[0], dp_p[1], dp_p[0]+2, dp_p[1]))

    dm_p = pp(J1x, J1y, 15.24, 0)
    parts.append(lbl("USB_DM", dm_p[0]+2, dm_p[1], 0))
    parts.append(w(dm_p[0], dm_p[1], dm_p[0]+2, dm_p[1]))

    cc2_p = pp(J1x, J1y, 15.24, -2.54)
    parts.append(lbl("CC2", cc2_p[0]+2, cc2_p[1], 0))
    parts.append(w(cc2_p[0], cc2_p[1], cc2_p[0]+2, cc2_p[1]))

    gnd_usb = pp(J1x, J1y, 0, -15.24)
    parts.append(gnd(gnd_usb[0], gnd_usb[1]+3))
    parts.append(w(gnd_usb[0], gnd_usb[1], gnd_usb[0], gnd_usb[1]+3))

    # PWR_FLAG on VBUS
    parts.append(pwr("PWR_FLAG", "PWR_FLAG", vbus_p[0]+2, vbus_p[1]-3))
    parts.append(w(vbus_p[0]+2, vbus_p[1]-3, vbus_p[0]+2, vbus_p[1]))

    # R8=5.1k CC1 pull-down
    R8x, R8y = 80, 55
    parts.append(inst("R", "R8", "5.1k", FP_R, R8x, R8y))
    t = r_top(R8x, R8y); parts.append(lbl("CC1", t[0], t[1]-2, 0)); parts.append(w(t[0], t[1]-2, t[0], t[1]))
    b = r_bot(R8x, R8y); parts.append(gnd(b[0], b[1]+3)); parts.append(w(b[0], b[1], b[0], b[1]+3))

    # R9=5.1k CC2 pull-down
    R9x, R9y = 88, 55
    parts.append(inst("R", "R9", "5.1k", FP_R, R9x, R9y))
    t = r_top(R9x, R9y); parts.append(lbl("CC2", t[0], t[1]-2, 0)); parts.append(w(t[0], t[1]-2, t[0], t[1]))
    b = r_bot(R9x, R9y); parts.append(gnd(b[0], b[1]+3)); parts.append(w(b[0], b[1], b[0], b[1]+3))

    # ────────────────────────────────────────
    # D1: SS34 Schottky — VBUS → VBUS_CHG (x=100, y=45)
    # 2-pin: K=pin1 at (0,3.81), A=pin2 at (0,-3.81)
    # ────────────────────────────────────────
    D1x, D1y = 100, 45
    parts.append(inst("D_Schottky", "D1", "SS34", "Diode_SMD:D_SMA", D1x, D1y,
                       lcsc="C8678", pin_ids=["K","A"]))
    t = r_top(D1x, D1y); parts.append(lbl("VBUS", t[0], t[1]-2, 0)); parts.append(w(t[0], t[1]-2, t[0], t[1]))
    b = r_bot(D1x, D1y); parts.append(lbl("VBUS_CHG", b[0], b[1]+2, 270)); parts.append(w(b[0], b[1], b[0], b[1]+2))

    # ────────────────────────────────────────
    # U2: TP4056 at (130, 75)
    # Pins: TEMP=1(10.16,0), PROG=2(10.16,-2.54), GND=3(0,-12.7),
    #        VCC=4(0,12.7), BAT=5(10.16,5.08), STDBY=6(-10.16,-2.54),
    #        CHRG=7(-10.16,0), CE=8(-10.16,5.08), EPAD=9(-2.54,-12.7)
    # ────────────────────────────────────────
    U2x, U2y = 130, 75
    parts.append(inst("TP4056", "U2", "TP4056",
                       "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm_ThermalVias",
                       U2x, U2y, lcsc="C382139",
                       pin_ids=["1","2","3","4","5","6","7","8","9"]))

    p = pp(U2x, U2y, 0, 12.7)  # VCC
    parts.append(lbl("VBUS_CHG", p[0], p[1]-3, 0)); parts.append(w(p[0], p[1]-3, p[0], p[1]))

    p = pp(U2x, U2y, 0, -12.7)  # GND
    parts.append(gnd(p[0], p[1]+3)); parts.append(w(p[0], p[1], p[0], p[1]+3))

    p = pp(U2x, U2y, -2.54, -12.7)  # EPAD
    parts.append(gnd(p[0], p[1]+3)); parts.append(w(p[0], p[1], p[0], p[1]+3))

    p = pp(U2x, U2y, 10.16, 5.08)  # BAT
    parts.append(lbl("VBAT", p[0]+2, p[1], 0)); parts.append(w(p[0], p[1], p[0]+2, p[1]))

    p = pp(U2x, U2y, -10.16, 5.08)  # CE
    parts.append(lbl("VBUS_CHG", p[0]-4, p[1], 180)); parts.append(w(p[0]-4, p[1], p[0], p[1]))

    p = pp(U2x, U2y, 10.16, 0)  # TEMP → GND
    parts.append(gnd(p[0]+3, p[1])); parts.append(w(p[0], p[1], p[0]+3, p[1]))

    # PROG (pin 2) → R1=1.2k to GND
    prog_p = pp(U2x, U2y, 10.16, -2.54)
    R1x, R1y = prog_p[0]+8, prog_p[1]
    parts.append(inst("R", "R1", "1.2k", FP_R, R1x, R1y, lcsc="C25752"))
    t = r_top(R1x, R1y); parts.append(w(prog_p[0], prog_p[1], t[0], prog_p[1])); parts.append(w(t[0], prog_p[1], t[0], t[1]))
    b = r_bot(R1x, R1y); parts.append(gnd(b[0], b[1]+3)); parts.append(w(b[0], b[1], b[0], b[1]+3))

    p = pp(U2x, U2y, -10.16, 0)  # CHRG
    parts.append(lbl("CHRG_OUT", p[0]-4, p[1], 180)); parts.append(w(p[0]-4, p[1], p[0], p[1]))

    p = pp(U2x, U2y, -10.16, -2.54)  # STDBY
    parts.append(lbl("STDBY_OUT", p[0]-4, p[1], 180)); parts.append(w(p[0]-4, p[1], p[0], p[1]))

    # ────────────────────────────────────────
    # U3: DW01A at (130, 115)
    # Pins: OD=1(-8.89,2.54), CS=2(-8.89,0), OC=3(-8.89,-2.54),
    #        TD=4(8.89,0), VCC=5(8.89,2.54), GND=6(8.89,-2.54)
    # ────────────────────────────────────────
    U3x, U3y = 130, 115
    parts.append(inst("DW01A", "U3", "DW01A", "Package_TO_SOT_SMD:SOT-23-6",
                       U3x, U3y, lcsc="C351410", pin_ids=["1","2","3","4","5","6"]))

    p = pp(U3x, U3y, 8.89, 2.54)  # VCC → VBAT
    parts.append(lbl("VBAT", p[0]+2, p[1], 0)); parts.append(w(p[0], p[1], p[0]+2, p[1]))

    p = pp(U3x, U3y, 8.89, -2.54)  # GND → CS_DRAIN
    parts.append(lbl("CS_DRAIN", p[0]+2, p[1], 0)); parts.append(w(p[0], p[1], p[0]+2, p[1]))

    p = pp(U3x, U3y, 8.89, 0)  # TD → VBAT
    parts.append(lbl("VBAT", p[0]+2, p[1], 0)); parts.append(w(p[0], p[1], p[0]+2, p[1]))

    p = pp(U3x, U3y, -8.89, 2.54)  # OD
    parts.append(lbl("OD", p[0]-4, p[1], 180)); parts.append(w(p[0]-4, p[1], p[0], p[1]))

    p = pp(U3x, U3y, -8.89, 0)  # CS → CS_DRAIN
    parts.append(lbl("CS_DRAIN", p[0]-4, p[1], 180)); parts.append(w(p[0]-4, p[1], p[0], p[1]))

    p = pp(U3x, U3y, -8.89, -2.54)  # OC
    parts.append(lbl("OC", p[0]-4, p[1], 180)); parts.append(w(p[0]-4, p[1], p[0], p[1]))

    # ────────────────────────────────────────
    # Q1: FS8205A at (130, 145)
    # Pins: S1=1(-8.89,5.08), G1=2(-8.89,2.54), D=3(-8.89,0),
    #        D=4(8.89,0), G2=5(8.89,2.54), S2=6(8.89,5.08)
    # ────────────────────────────────────────
    Q1x, Q1y = 130, 145
    parts.append(inst("FS8205A", "Q1", "FS8205A", "Package_TO_SOT_SMD:SOT-23-6",
                       Q1x, Q1y, lcsc="C908265", pin_ids=["1","2","3","4","5","6"]))

    p = pp(Q1x, Q1y, -8.89, 5.08)  # S1 → BAT_MINUS
    parts.append(lbl("BAT_MINUS", p[0]-4, p[1], 180)); parts.append(w(p[0]-4, p[1], p[0], p[1]))

    p = pp(Q1x, Q1y, -8.89, 2.54)  # G1 → OD
    parts.append(lbl("OD", p[0]-4, p[1], 180)); parts.append(w(p[0]-4, p[1], p[0], p[1]))

    p = pp(Q1x, Q1y, -8.89, 0)  # D → CS_DRAIN
    parts.append(lbl("CS_DRAIN", p[0]-4, p[1], 180)); parts.append(w(p[0]-4, p[1], p[0], p[1]))

    p = pp(Q1x, Q1y, 8.89, 0)  # D → CS_DRAIN
    parts.append(lbl("CS_DRAIN", p[0]+2, p[1], 0)); parts.append(w(p[0], p[1], p[0]+2, p[1]))

    p = pp(Q1x, Q1y, 8.89, 2.54)  # G2 → OC
    parts.append(lbl("OC", p[0]+2, p[1], 0)); parts.append(w(p[0], p[1], p[0]+2, p[1]))

    p = pp(Q1x, Q1y, 8.89, 5.08)  # S2 → GND
    parts.append(gnd(p[0]+3, p[1])); parts.append(w(p[0], p[1], p[0]+3, p[1]))

    # ────────────────────────────────────────
    # J2: Battery at (170, 130), 2-pin
    # ────────────────────────────────────────
    J2x, J2y = 170, 130
    parts.append(inst("JST_PH_2", "J2", "BAT",
                       "Connector_JST:JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical",
                       J2x, J2y, lcsc="C131337", pin_ids=["1","2"]))
    t = r_top(J2x, J2y); parts.append(lbl("VBAT", t[0], t[1]-2, 0)); parts.append(w(t[0], t[1]-2, t[0], t[1]))
    b = r_bot(J2x, J2y); parts.append(lbl("BAT_MINUS", b[0], b[1]+2, 270)); parts.append(w(b[0], b[1], b[0], b[1]+2))

    # ────────────────────────────────────────
    # U4: AMS1117-3.3 at (130, 170)
    # Pins: GND=1(0,-10.16), VO=2(10.16,0), VI=3(-10.16,0)
    # ────────────────────────────────────────
    U4x, U4y = 130, 170
    parts.append(inst("AMS1117_3V3", "U4", "AMS1117-3.3",
                       "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
                       U4x, U4y, lcsc="C6186", pin_ids=["1","2","3"]))

    p = pp(U4x, U4y, -10.16, 0)  # VI → VBAT
    parts.append(lbl("VBAT", p[0]-4, p[1], 180)); parts.append(w(p[0]-4, p[1], p[0], p[1]))

    p = pp(U4x, U4y, 10.16, 0)  # VO → 3V3
    parts.append(lbl("3V3", p[0]+2, p[1], 0)); parts.append(w(p[0], p[1], p[0]+2, p[1]))
    parts.append(v3(p[0]+2, p[1]-3)); parts.append(w(p[0]+2, p[1]-3, p[0]+2, p[1]))

    p = pp(U4x, U4y, 0, -10.16)  # GND
    parts.append(gnd(p[0], p[1]+3)); parts.append(w(p[0], p[1], p[0], p[1]+3))

    # C5: 10uF input cap
    C5x, C5y = 116, 180
    parts.append(inst("C", "C5", "10uF", FP_C, C5x, C5y, lcsc="C19702"))
    t = r_top(C5x, C5y); parts.append(lbl("VBAT", t[0], t[1]-2, 0)); parts.append(w(t[0], t[1]-2, t[0], t[1]))
    b = r_bot(C5x, C5y); parts.append(gnd(b[0], b[1]+3)); parts.append(w(b[0], b[1], b[0], b[1]+3))

    # C6: 10uF output cap
    C6x, C6y = 148, 180
    parts.append(inst("C", "C6", "10uF", FP_C, C6x, C6y, lcsc="C19702"))
    t = r_top(C6x, C6y); parts.append(lbl("3V3", t[0], t[1]-2, 0)); parts.append(w(t[0], t[1]-2, t[0], t[1]))
    b = r_bot(C6x, C6y); parts.append(gnd(b[0], b[1]+3)); parts.append(w(b[0], b[1], b[0], b[1]+3))

    # ────────────────────────────────────────
    # STATUS LEDs
    # ────────────────────────────────────────
    # D2: Red charge LED + R2
    D2x, D2y = 95, 100
    parts.append(inst("LED", "D2", "RED", FP_LED, D2x, D2y, lcsc="C84256", pin_ids=["K","A"]))
    R2x, R2y = 95, 112
    parts.append(inst("R", "R2", "1k", FP_R, R2x, R2y, lcsc="C25585"))
    t = r_top(D2x, D2y); parts.append(lbl("CHRG_OUT", t[0], t[1]-2, 0)); parts.append(w(t[0], t[1]-2, t[0], t[1]))
    b = r_bot(D2x, D2y); t2 = r_top(R2x, R2y); parts.append(w(b[0], b[1], t2[0], t2[1]))
    b2 = r_bot(R2x, R2y); parts.append(gnd(b2[0], b2[1]+3)); parts.append(w(b2[0], b2[1], b2[0], b2[1]+3))

    # D3: Green standby LED + R3
    D3x, D3y = 105, 100
    parts.append(inst("LED", "D3", "GRN", FP_LED, D3x, D3y, lcsc="C72043", pin_ids=["K","A"]))
    R3x, R3y = 105, 112
    parts.append(inst("R", "R3", "1k", FP_R, R3x, R3y, lcsc="C25585"))
    t = r_top(D3x, D3y); parts.append(lbl("STDBY_OUT", t[0], t[1]-2, 0)); parts.append(w(t[0], t[1]-2, t[0], t[1]))
    b = r_bot(D3x, D3y); t2 = r_top(R3x, R3y); parts.append(w(b[0], b[1], t2[0], t2[1]))
    b2 = r_bot(R3x, R3y); parts.append(gnd(b2[0], b2[1]+3)); parts.append(w(b2[0], b2[1], b2[0], b2[1]+3))

    # ────────────────────────────────────────
    # U1: ESP32-S3-WROOM-1 at (250, 120)
    # Left pins: EN(3)@(-17.78,22.86), GPIO4-8@(−17.78, 20.32..10.16),
    #   GPIO16@(-17.78,5.08), GPIO17@(-17.78,2.54), GPIO18@(-17.78,0),
    #   GPIO19@(-17.78,-2.54), GPIO20@(-17.78,-5.08), GPIO0@(-17.78,-7.62)
    # Right pins: GPIO9@(17.78,17.78)..GPIO12@(17.78,5.08)
    # Top: 3V3(2)@(0,27.94), Bottom: GND(1)@(0,-27.94)
    # ────────────────────────────────────────
    U1x, U1y = 250, 120
    esp_pins = ["1","2","3","4","5","6","7","8","9","10","11","13","14",
                "15","16","17","18","19","20","23","27","40","41"]
    parts.append(inst("ESP32_S3_WROOM_1", "U1", "ESP32-S3-WROOM-1-N16R8",
                       "RF_Module:ESP32-S3-WROOM-1",
                       U1x, U1y, lcsc="C2913196", pin_ids=esp_pins))

    p = pp(U1x, U1y, 0, 27.94)  # 3V3
    parts.append(v3(p[0], p[1]-3)); parts.append(w(p[0], p[1]-3, p[0], p[1]))

    p = pp(U1x, U1y, 0, -27.94)  # GND
    parts.append(gnd(p[0], p[1]+3)); parts.append(w(p[0], p[1], p[0], p[1]+3))

    # Decoupling
    C3x, C3y = 270, 98
    parts.append(inst("C", "C3", "100nF", FP_C, C3x, C3y, lcsc="C14663"))
    t = r_top(C3x, C3y); parts.append(v3(t[0], t[1]-3)); parts.append(w(t[0], t[1]-3, t[0], t[1]))
    b = r_bot(C3x, C3y); parts.append(gnd(b[0], b[1]+3)); parts.append(w(b[0], b[1], b[0], b[1]+3))

    C4x, C4y = 278, 98
    parts.append(inst("C", "C4", "10uF", FP_C, C4x, C4y, lcsc="C19702"))
    t = r_top(C4x, C4y); parts.append(v3(t[0], t[1]-3)); parts.append(w(t[0], t[1]-3, t[0], t[1]))
    b = r_bot(C4x, C4y); parts.append(gnd(b[0], b[1]+3)); parts.append(w(b[0], b[1], b[0], b[1]+3))

    # EN pull-up R10
    R10x, R10y = 220, 100
    parts.append(inst("R", "R10", "10k", FP_R, R10x, R10y, lcsc="C25744"))
    t = r_top(R10x, R10y); parts.append(v3(t[0], t[1]-3)); parts.append(w(t[0], t[1]-3, t[0], t[1]))
    b = r_bot(R10x, R10y); parts.append(lbl("EN", b[0], b[1]+2, 270)); parts.append(w(b[0], b[1], b[0], b[1]+2))

    # BOOT pull-up R11
    R11x, R11y = 226, 100
    parts.append(inst("R", "R11", "10k", FP_R, R11x, R11y, lcsc="C25744"))
    t = r_top(R11x, R11y); parts.append(v3(t[0], t[1]-3)); parts.append(w(t[0], t[1]-3, t[0], t[1]))
    b = r_bot(R11x, R11y); parts.append(lbl("BOOT", b[0], b[1]+2, 270)); parts.append(w(b[0], b[1], b[0], b[1]+2))

    # ESP32 left-side labels
    left_pins = [
        ("EN",         -17.78, 22.86),
        ("GPIO4",      -17.78, 20.32),  # mapped in wiring
        ("GPIO5",      -17.78, 17.78),
        ("GPIO6",      -17.78, 15.24),
        ("GPIO7",      -17.78, 12.7),
        ("GPIO8",      -17.78, 10.16),
        ("GPIO16",     -17.78, 5.08),
        ("GPIO17",     -17.78, 2.54),
        ("GPIO18",     -17.78, 0),
        ("GPIO19",     -17.78, -2.54),
        ("GPIO20",     -17.78, -5.08),
        ("GPIO0",      -17.78, -7.62),
    ]
    lbl_map = {
        "EN": "EN", "GPIO0": "BOOT",
        "GPIO4": "JOY_UP", "GPIO5": "JOY_DOWN", "GPIO6": "JOY_LEFT",
        "GPIO7": "JOY_RIGHT", "GPIO8": "JOY_CENTER",
        "GPIO16": "I2C_SDA", "GPIO17": "I2C_SCL", "GPIO18": "ACCEL_INT1",
        "GPIO19": "USB_DM", "GPIO20": "USB_DP",
    }
    for pname, lx, ly in left_pins:
        p = pp(U1x, U1y, lx, ly)
        net = lbl_map[pname]
        parts.append(lbl(net, p[0]-4, p[1], 180))
        parts.append(w(p[0]-4, p[1], p[0], p[1]))

    # ESP32 right-side labels (SPI ePaper)
    right_pins = [
        ("GPIO9",  17.78, 17.78, "EPD_CLK"),
        ("GPIO10", 17.78, 15.24, "EPD_MOSI"),
        ("GPIO3",  17.78, 12.7,  "EPD_DC"),
        ("GPIO11", 17.78, 10.16, "EPD_RST"),
        ("GPIO46", 17.78, 7.62,  "EPD_CS"),
        ("GPIO12", 17.78, 5.08,  "EPD_BUSY"),
    ]
    for pname, rx, ry, net in right_pins:
        p = pp(U1x, U1y, rx, ry)
        parts.append(lbl(net, p[0]+2, p[1], 0))
        parts.append(w(p[0], p[1], p[0]+2, p[1]))

    # ────────────────────────────────────────
    # J3: ePaper Header at (330, 115)
    # Pins 1-8 at (5.08, 8.89-i*2.54) for i=0..7
    # ────────────────────────────────────────
    J3x, J3y = 330, 115
    parts.append(inst("EPAPER_HDR", "J3", "ePaper",
                       "Connector_JST:JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal",
                       J3x, J3y, pin_ids=[str(i) for i in range(1,9)]))

    epd_map = ["3V3","GND","EPD_MOSI","EPD_CLK","EPD_CS","EPD_DC","EPD_RST","EPD_BUSY"]
    for i, net in enumerate(epd_map):
        p = pp(J3x, J3y, 5.08, 8.89 - i * 2.54)
        if net == "3V3":
            parts.append(v3(p[0]+3, p[1]-2)); parts.append(w(p[0], p[1], p[0]+3, p[1])); parts.append(w(p[0]+3, p[1], p[0]+3, p[1]-2))
        elif net == "GND":
            parts.append(gnd(p[0]+3, p[1]+2)); parts.append(w(p[0], p[1], p[0]+3, p[1])); parts.append(w(p[0]+3, p[1], p[0]+3, p[1]+2))
        else:
            parts.append(lbl(net, p[0]+2, p[1], 0)); parts.append(w(p[0], p[1], p[0]+2, p[1]))

    # ────────────────────────────────────────
    # U5: LIS2DH12TR at (330, 195)
    # Pins: SCL=1(-10.16,5.08), CS=2(-10.16,2.54), SDO=3(-10.16,0),
    #        SDA=4(-10.16,-2.54), GND=6(0,-10.16), VDD_IO=9(10.16,5.08),
    #        INT1=12(10.16,-2.54), INT2=11(10.16,0)
    # ────────────────────────────────────────
    U5x, U5y = 330, 195
    parts.append(inst("LIS2DH12TR", "U5", "LIS2DH12TR",
                       "Package_LGA:LGA-12_2x2mm_P0.5mm",
                       U5x, U5y, lcsc="C110926",
                       pin_ids=[str(i) for i in range(1,13)]))

    p = pp(U5x, U5y, -10.16, 5.08)  # SCL
    parts.append(lbl("I2C_SCL", p[0]-4, p[1], 180)); parts.append(w(p[0]-4, p[1], p[0], p[1]))

    p = pp(U5x, U5y, -10.16, -2.54)  # SDA
    parts.append(lbl("I2C_SDA", p[0]-4, p[1], 180)); parts.append(w(p[0]-4, p[1], p[0], p[1]))

    p = pp(U5x, U5y, -10.16, 2.54)  # CS → 3V3 (I2C mode)
    parts.append(v3(p[0]-3, p[1]-2)); parts.append(w(p[0]-3, p[1], p[0], p[1])); parts.append(w(p[0]-3, p[1]-2, p[0]-3, p[1]))

    p = pp(U5x, U5y, -10.16, 0)  # SDO → GND (addr 0x18)
    parts.append(gnd(p[0]-3, p[1]+2)); parts.append(w(p[0]-3, p[1], p[0], p[1])); parts.append(w(p[0]-3, p[1], p[0]-3, p[1]+2))

    p = pp(U5x, U5y, 10.16, -2.54)  # INT1
    parts.append(lbl("ACCEL_INT1", p[0]+2, p[1], 0)); parts.append(w(p[0], p[1], p[0]+2, p[1]))

    p = pp(U5x, U5y, 10.16, 5.08)  # VDD_IO → 3V3
    parts.append(v3(p[0]+3, p[1]-2)); parts.append(w(p[0], p[1], p[0]+3, p[1])); parts.append(w(p[0]+3, p[1]-2, p[0]+3, p[1]))

    p = pp(U5x, U5y, 0, -10.16)  # GND
    parts.append(gnd(p[0], p[1]+3)); parts.append(w(p[0], p[1], p[0], p[1]+3))

    # C7: 100nF decoupling
    C7x, C7y = 350, 195
    parts.append(inst("C", "C7", "100nF", FP_C, C7x, C7y, lcsc="C14663"))
    t = r_top(C7x, C7y); parts.append(v3(t[0], t[1]-3)); parts.append(w(t[0], t[1]-3, t[0], t[1]))
    b = r_bot(C7x, C7y); parts.append(gnd(b[0], b[1]+3)); parts.append(w(b[0], b[1], b[0], b[1]+3))

    # I2C pull-ups
    R4x, R4y = 310, 188
    parts.append(inst("R", "R4", "10k", FP_R, R4x, R4y, lcsc="C25744"))
    t = r_top(R4x, R4y); parts.append(v3(t[0], t[1]-3)); parts.append(w(t[0], t[1]-3, t[0], t[1]))
    b = r_bot(R4x, R4y); parts.append(lbl("I2C_SDA", b[0], b[1]+2, 270)); parts.append(w(b[0], b[1], b[0], b[1]+2))

    R5x, R5y = 305, 188
    parts.append(inst("R", "R5", "10k", FP_R, R5x, R5y, lcsc="C25744"))
    t = r_top(R5x, R5y); parts.append(v3(t[0], t[1]-3)); parts.append(w(t[0], t[1]-3, t[0], t[1]))
    b = r_bot(R5x, R5y); parts.append(lbl("I2C_SCL", b[0], b[1]+2, 270)); parts.append(w(b[0], b[1], b[0], b[1]+2))

    # ────────────────────────────────────────
    # Joystick — 5 x SW_Push
    # SW_Push: pin1 at (0,3.81)→top, pin2 at (0,-3.81)→bottom (vertical)
    # For horizontal use: rotate 90° or use labels
    # ────────────────────────────────────────
    joy_names = ["JOY_UP","JOY_DOWN","JOY_LEFT","JOY_RIGHT","JOY_CENTER"]
    joy_refs = ["SW1a","SW1b","SW1c","SW1d","SW1e"]
    for i, (jn, jr) in enumerate(zip(joy_names, joy_refs)):
        sx, sy = 325, 220 + i * 10
        parts.append(inst("SW_Push", jr, jn, "", sx, sy, pin_ids=["1","2"]))
        t = r_top(sx, sy); parts.append(lbl(jn, t[0], t[1]-2, 0)); parts.append(w(t[0], t[1]-2, t[0], t[1]))
        b = r_bot(sx, sy); parts.append(gnd(b[0], b[1]+3)); parts.append(w(b[0], b[1], b[0], b[1]+3))

    # ────────────────────────────────────────
    # SW2: BOOT, SW3: RESET
    # ────────────────────────────────────────
    SW2x, SW2y = 225, 200
    parts.append(inst("SW_Push", "SW2", "BOOT", "", SW2x, SW2y, pin_ids=["1","2"]))
    t = r_top(SW2x, SW2y); parts.append(lbl("BOOT", t[0], t[1]-2, 0)); parts.append(w(t[0], t[1]-2, t[0], t[1]))
    b = r_bot(SW2x, SW2y); parts.append(gnd(b[0], b[1]+3)); parts.append(w(b[0], b[1], b[0], b[1]+3))

    SW3x, SW3y = 225, 215
    parts.append(inst("SW_Push", "SW3", "RESET", "", SW3x, SW3y, pin_ids=["1","2"]))
    t = r_top(SW3x, SW3y); parts.append(lbl("EN", t[0], t[1]-2, 0)); parts.append(w(t[0], t[1]-2, t[0], t[1]))
    b = r_bot(SW3x, SW3y); parts.append(gnd(b[0], b[1]+3)); parts.append(w(b[0], b[1], b[0], b[1]+3))

    # C8: EN debounce
    C8x, C8y = 235, 215
    parts.append(inst("C", "C8", "100nF", FP_C, C8x, C8y, lcsc="C14663"))
    t = r_top(C8x, C8y); parts.append(lbl("EN", t[0], t[1]-2, 0)); parts.append(w(t[0], t[1]-2, t[0], t[1]))
    b = r_bot(C8x, C8y); parts.append(gnd(b[0], b[1]+3)); parts.append(w(b[0], b[1], b[0], b[1]+3))

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("Building symbol definitions...")
    lib_syms = build_lib_symbols()

    print("Building schematic body...")
    body = build_schematic_body()

    schematic = f"""(kicad_sch
  (version 20250610)
  (generator "eeschema")
  (generator_version "10.0")
  (uuid "d11d3700-0000-4000-8000-d11d37000000")
  (paper "A3")
  (title_block
    (title "Dilder - Custom PCB")
    (date "2026-04-15")
    (rev "0.5")
    (company "Dilder Project")
    (comment 1 "ESP32-S3-WROOM-1-N16R8 + LiPo + Joystick + LIS2DH12 + ePaper")
    (comment 2 "Target: JLCPCB SMT Assembly — Real library footprints")
  )
  (lib_symbols

{lib_syms}

  )

{body}

  (sheet_instances
    (path "/"
      (page "1")
    )
  )
)
"""

    # Verify paren balance
    depth = 0
    for c in schematic:
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
    if depth != 0:
        print(f"ERROR: Unbalanced parentheses (depth={depth})")
        return

    with open(OUTPUT, 'w') as f:
        f.write(schematic)

    lines = schematic.count('\n')
    print(f"\nSchematic written to: {OUTPUT}")
    print(f"  Lines: {lines}")
    print(f"  Paren balance: OK")


if __name__ == "__main__":
    main()
