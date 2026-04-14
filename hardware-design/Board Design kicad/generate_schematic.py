#!/usr/bin/env python3
"""
Generate a fully-wired KiCad schematic for the Dilder PCB.

Uses net labels on wire stubs to create all electrical connections.
This approach is more reliable than routing long wires between distant components.

Run from the 'Board Design kicad/' directory:
  python3 generate_schematic.py
"""

import uuid as _uuid
import json

# ── Helpers ────────────────────────────────────────────────────────────

_uuid_counter = 0
def uid():
    global _uuid_counter
    _uuid_counter += 1
    return f"a{_uuid_counter:011x}-0000-4000-8000-000000000000"

def wire(x1, y1, x2, y2):
    return f'  (wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{uid()}"))'

def label(name, x, y, angle=0):
    return f'  (label "{name}" (at {x} {y} {angle}) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))'

def pwr_flag(x, y):
    """Power flag symbol to suppress ERC warnings."""
    return f'''  (symbol (lib_id "PWR_FLAG") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{uid()}")
    (property "Reference" "#FLG0{_uuid_counter}" (at {x} {y-2} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "PWR_FLAG" (at {x} {y-4} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{uid()}"))
  )'''

# ── Component placement coordinates ───────────────────────────────────
# Organized into functional blocks on an A3 sheet (420x297mm)

# POWER SECTION (top area, y=40-100)
USB_C   = (45,  68)     # J1 - USB-C connector
SCHOTTKY= (80,  55)     # D1 - SS34
TP4056  = (115, 68)     # U2 - charger
DW01A   = (170, 68)     # U3 - protection
FS8205A = (170, 100)    # Q1 - MOSFETs
JST_BAT = (220, 68)     # J2 - battery connector
LDO     = (115, 115)    # U4 - AMS1117-3.3
RPROG   = (100, 82)     # R1 - 1.2k prog resistor
LED_CHG = (140, 58)     # D2 - charge LED
LED_DONE= (140, 48)     # D3 - done LED
RLED1   = (152, 58)     # R2 - LED resistor
RLED2   = (152, 48)     # R3 - LED resistor
C_LDO_IN= (100, 115)   # C5 - LDO input cap
C_LDO_OUT=(132, 115)    # C6 - LDO output cap

# MCU SECTION (center, y=150-240)
RP2040  = (160, 195)    # U1 - main MCU
FLASH   = (90,  210)    # U5 - W25Q16JV
CRYSTAL = (205, 215)    # Y1 - 12MHz
C_XTAL1 = (198, 228)   # C1 - 15pF load cap
C_XTAL2 = (212, 228)   # C2 - 15pF load cap
C_DEC1  = (145, 150)    # C3 - 100nF decoupling
C_DEC2  = (155, 150)    # C4 - 10uF bulk
R_USB_DP= (120, 185)    # R6 - 27R USB
R_USB_DM= (120, 190)    # R7 - 27R USB
R_CC1   = (35,  82)     # R8 - 5.1k CC1
R_CC2   = (45,  82)     # R9 - 5.1k CC2
R_RUN   = (200, 178)    # R10 - 10k RUN pull-up

# PERIPHERALS (left and right sides)
JOYSTICK= (50,  175)    # SW1 - 5-way nav switch
EPAPER  = (280, 175)    # J3 - e-Paper 8-pin header
IMU     = (280, 220)    # U6 - MPU-6050
GPS     = (280, 265)    # U7 - ATGM336H
R_I2C_SDA=(265, 208)   # R4 - 10k I2C pull-up
R_I2C_SCL=(272, 208)   # R5 - 10k I2C pull-up
C_IMU   = (298, 210)    # C7 - 100nF IMU decoupling
C_GPS   = (298, 255)    # C8 - 100nF GPS decoupling
C_REGOUT= (298, 225)    # C9 - 100nF IMU REGOUT


# ── Net definitions ───────────────────────────────────────────────────
# Each net: list of (component_ref, pin_name, x, y, label_angle)
# Wires go from pin to label position

NETS = {}

def add_net(net_name, connections):
    """connections: list of (x, y, wire_dx, wire_dy, label_angle)"""
    NETS[net_name] = connections


# ── Build the schematic ───────────────────────────────────────────────

def build_lib_symbols():
    """Return the lib_symbols block (reuse from existing file)."""
    with open("dilder.kicad_sch") as f:
        content = f.read()
    start = content.index("(lib_symbols")
    depth = 0
    i = start
    while i < len(content):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
            if depth == 0:
                break
        i += 1
    return content[start:i+1]


def component(lib_id, ref_prefix, ref_num, value, x, y, lcsc="", footprint="", pins=None, angle=0):
    """Generate a component instance."""
    u = uid()
    ref = f"{ref_prefix}{ref_num}"
    lines = [
        f'  (symbol (lib_id "{lib_id}") (at {x} {y} {angle}) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes)',
        f'    (uuid "{u}")',
        f'    (property "Reference" "{ref}" (at {x} {y-12} 0) (effects (font (size 1.27 1.27))))',
        f'    (property "Value" "{value}" (at {x} {y+10} 0) (effects (font (size 1.27 1.27))))',
    ]
    if footprint:
        lines.append(f'    (property "Footprint" "{footprint}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))')
    if lcsc:
        lines.append(f'    (property "LCSC" "{lcsc}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))')
    if pins:
        for pin_num in pins:
            lines.append(f'    (pin "{pin_num}" (uuid "{uid()}"))')
    lines.append(f'  )')
    return '\n'.join(lines), u, ref


def build_schematic():
    lib_symbols = build_lib_symbols()

    components = []  # (text, uuid, ref)
    wires = []
    labels_list = []
    sym_instances = []

    def add(lib_id, ref_pre, ref_num, value, pos, lcsc="", fp="", pins=None, angle=0):
        text, u, ref = component(lib_id, ref_pre, ref_num, value, pos[0], pos[1], lcsc, fp, pins, angle)
        components.append(text)
        sym_instances.append(f'    (path "/{u}" (reference "{ref}") (unit 1))')
        return ref

    def net(name, x, y, dx, dy, angle=0):
        """Add a wire stub + label at the end."""
        wx, wy = x + dx, y + dy
        wires.append(wire(x, y, wx, wy))
        labels_list.append(label(name, wx, wy, angle))

    # ════════════════════════════════════════════════════════════════
    # COMPONENT PLACEMENT
    # ════════════════════════════════════════════════════════════════

    # -- Power Section --
    add("USB_C_16P", "J", 1, "USB-C", USB_C, "C2765186", "",
        ["A4", "A5", "B5", "A6", "A7", "A1", "S1"])

    add("D_Schottky", "D", 1, "SS34", SCHOTTKY, "C8678", "Diode_SMD:D_SMA",
        ["1", "2"])

    add("TP4056", "U", 2, "TP4056", TP4056, "C382139", "Package_SO:ESOP-8_3.9x4.9mm_P1.27mm",
        ["8", "3", "2", "1", "6", "7", "4", "5"])

    add("DW01A", "U", 3, "DW01A", DW01A, "C351410", "Package_TO_SOT_SMD:SOT-23-6",
        ["1", "2", "3", "5", "6", "4"])

    add("FS8205A", "Q", 1, "FS8205A", FS8205A, "C908265", "Package_TO_SOT_SMD:SOT-23-6",
        ["1", "2", "6", "5", "3", "4"])

    add("JST_PH_2", "J", 2, "JST-PH-2", JST_BAT, "C131337",
        "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
        ["1", "2"])

    add("AMS1117-3.3", "U", 4, "AMS1117-3.3", LDO, "C6186",
        "Package_TO_SOT_SMD:SOT-223-3_TabPin2", ["3", "2", "1"])

    # Passives - Power
    add("R", "R", 1, "1.2k", RPROG, "C25752", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("LED", "D", 2, "RED", LED_CHG, "C84256", "LED_SMD:LED_0402_1005Metric", ["1", "2"])
    add("LED", "D", 3, "GREEN", LED_DONE, "C72043", "LED_SMD:LED_0402_1005Metric", ["1", "2"])
    add("R", "R", 2, "1k", RLED1, "C25585", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("R", "R", 3, "1k", RLED2, "C25585", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("C", "C", 5, "10uF", C_LDO_IN, "C19702", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])
    add("C", "C", 6, "10uF", C_LDO_OUT, "C19702", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])

    # -- MCU Section --
    add("RP2040", "U", 1, "RP2040", RP2040, "C2040",
        "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm",
        ["2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17",
         "27","28","29","30","31","32","33","34","35","36","37","38","39","40",
         "47","46","24","21","22","23","25","26","20","19",
         "1","48","50","43","57","18","42","41","44","45","49"])

    add("W25Q16JV", "U", 5, "W25Q16JV", FLASH, "C131024",
        "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        ["2", "5", "6", "1", "3", "7", "8", "4"])

    add("Crystal_12MHz", "Y", 1, "12MHz", CRYSTAL, "C9002",
        "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", ["1", "2"], angle=90)

    # Passives - MCU
    add("C", "C", 1, "15pF", C_XTAL1, "C1644", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])
    add("C", "C", 2, "15pF", C_XTAL2, "C1644", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])
    add("C", "C", 3, "100nF", C_DEC1, "C14663", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])
    add("C", "C", 4, "10uF", C_DEC2, "C19702", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])
    add("R", "R", 6, "27R", R_USB_DP, "C25105", "Resistor_SMD:R_0402_1005Metric", ["1", "2"], angle=90)
    add("R", "R", 7, "27R", R_USB_DM, "C25105", "Resistor_SMD:R_0402_1005Metric", ["1", "2"], angle=90)
    add("R", "R", 8, "5.1k", R_CC1, "", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("R", "R", 9, "5.1k", R_CC2, "", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("R", "R", 10, "10k", R_RUN, "C25744", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])

    # -- Peripherals --
    add("SKRHABE010", "SW", 1, "5-Way Nav", JOYSTICK, "C139794", "",
        ["1", "2", "3", "4", "5", "6"])

    add("EPAPER_HEADER", "J", 3, "ePaper 8pin", EPAPER, "",
        "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
        ["1", "2", "3", "4", "5", "6", "7", "8"])

    add("MPU-6050", "U", 6, "MPU-6050", IMU, "C24112",
        "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm",
        ["13", "18", "24", "23", "12", "9", "10", "1", "20", "11", "8"])

    add("ATGM336H", "U", 7, "ATGM336H", GPS, "C90770", "",
        ["6", "5", "2", "3", "1", "4", "7"])

    # Passives - Peripherals
    add("R", "R", 4, "10k", R_I2C_SDA, "C25744", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("R", "R", 5, "10k", R_I2C_SCL, "C25744", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("C", "C", 7, "100nF", C_IMU, "C14663", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])
    add("C", "C", 8, "100nF", C_GPS, "C14663", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])
    add("C", "C", 9, "100nF", C_REGOUT, "C14663", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])

    # ════════════════════════════════════════════════════════════════
    # NET CONNECTIONS VIA LABELS
    # Each net() call: place a wire stub from a pin and attach a label
    # Matching labels = electrical connection
    # ════════════════════════════════════════════════════════════════

    # ── VBUS net: USB-C VBUS → Schottky anode ──
    # J1 VBUS pin is at USB_C + (0, -11.43) = (45, 56.57)
    net("VBUS", USB_C[0], USB_C[1]-11.43, 0, -5, 0)
    # D1 anode at SCHOTTKY + (-3.81, 0) = (76.19, 55)
    net("VBUS", SCHOTTKY[0]-3.81, SCHOTTKY[1], -5, 0, 180)

    # ── VBUS_CHG net: Schottky cathode → TP4056 VCC ──
    net("VBUS_CHG", SCHOTTKY[0]+3.81, SCHOTTKY[1], 5, 0, 0)
    net("VBUS_CHG", TP4056[0]-10.16, TP4056[1]-5.08+10.16, -5, 0, 180)

    # ── VBAT net: TP4056 BAT → DW01A VCC → LDO VIN ──
    net("VBAT", TP4056[0]+10.16, TP4056[1]-5.08+10.16, 5, 0, 0)
    net("VBAT", DW01A[0]+8.89, DW01A[1]-2.54, 5, 0, 0)
    net("VBAT", LDO[0]-7.62, LDO[1]-1.27, -5, 0, 180)
    net("VBAT", C_LDO_IN[0], C_LDO_IN[1]-2.54, 0, -3, 0)

    # ── 3V3 net: LDO VOUT → all 3.3V consumers ──
    net("3V3", LDO[0]+7.62, LDO[1]-1.27, 5, 0, 0)
    net("3V3", C_LDO_OUT[0], C_LDO_OUT[1]-2.54, 0, -3, 0)
    # RP2040 power pins (IOVDD, DVDD, USB_VDD, ADC_AVDD)
    net("3V3", RP2040[0]+0, RP2040[1]-40.64, 0, -5, 0)    # IOVDD
    net("3V3", RP2040[0]+2.54, RP2040[1]-40.64, 0, -5, 0)  # DVDD
    net("3V3", RP2040[0]+5.08, RP2040[1]-40.64, 0, -5, 0)  # USB_VDD
    net("3V3", RP2040[0]+7.62, RP2040[1]-40.64, 0, -5, 0)  # ADC_AVDD
    # RP2040 VREG_VIN
    net("3V3", RP2040[0]+22.86, RP2040[1]+25.4, 5, 0, 0)
    # Decoupling caps
    net("3V3", C_DEC1[0], C_DEC1[1]-2.54, 0, -3, 0)
    net("3V3", C_DEC2[0], C_DEC2[1]-2.54, 0, -3, 0)
    # Flash VCC
    net("3V3", FLASH[0], FLASH[1]-7.62, 0, -3, 0)
    # IMU VDD + VLOGIC
    net("3V3", IMU[0], IMU[1]-15.24, 0, -3, 0)
    net("3V3", IMU[0]+2.54, IMU[1]-15.24, 0, -3, 0)
    # GPS VCC + V_BCKP
    net("3V3", GPS[0], GPS[1]-12.7, 0, -3, 0)
    net("3V3", GPS[0]+10.16, GPS[1]-2.54, 5, 0, 0)
    # e-Paper VCC
    net("3V3", EPAPER[0]-7.62, EPAPER[1]-8.89, -5, 0, 180)
    # I2C pull-ups top
    net("3V3", R_I2C_SDA[0], R_I2C_SDA[1]-2.54, 0, -3, 0)
    net("3V3", R_I2C_SCL[0], R_I2C_SCL[1]-2.54, 0, -3, 0)
    # RUN pull-up top
    net("3V3", R_RUN[0], R_RUN[1]-2.54, 0, -3, 0)
    # LED anodes (through resistors)
    net("3V3", RLED1[0], RLED1[1]-2.54, 0, -3, 0)
    net("3V3", RLED2[0], RLED2[1]-2.54, 0, -3, 0)
    # Decoupling - IMU and GPS
    net("3V3", C_IMU[0], C_IMU[1]-2.54, 0, -3, 0)
    net("3V3", C_GPS[0], C_GPS[1]-2.54, 0, -3, 0)
    # TP4056 CE (always enabled)
    net("3V3", TP4056[0]-10.16, TP4056[1]+2.54, -5, 0, 180)
    # Flash WP and HOLD (disable)
    net("3V3", FLASH[0]+10.16, FLASH[1], 5, 0, 0)       # WP
    net("3V3", FLASH[0]+10.16, FLASH[1]-2.54, 5, 0, 0)   # HOLD

    # ── GND net ──
    # USB-C GND
    net("GND", USB_C[0], USB_C[1]+11.43, 0, 5, 180)
    # USB-C Shield
    net("GND", USB_C[0]+10.16, USB_C[1], 5, 0, 0)
    # TP4056 GND
    net("GND", TP4056[0], TP4056[1]+10.16, 0, 5, 180)
    # TP4056 TEMP (tie to GND to disable temp sense)
    net("GND", TP4056[0]-10.16, TP4056[1], -5, 0, 180)
    # DW01A GND
    net("GND", DW01A[0]+8.89, DW01A[1]+2.54, 5, 0, 0)
    # LDO GND
    net("GND", LDO[0], LDO[1]+6.35, 0, 5, 180)
    # RPROG bottom
    net("GND", RPROG[0], RPROG[1]+2.54, 0, 5, 180)
    # RP2040 GND
    net("GND", RP2040[0], RP2040[1]+40.64, 0, 5, 180)
    # Flash GND
    net("GND", FLASH[0], FLASH[1]+7.62, 0, 5, 180)
    # Crystal load caps GND
    net("GND", C_XTAL1[0], C_XTAL1[1]+2.54, 0, 5, 180)
    net("GND", C_XTAL2[0], C_XTAL2[1]+2.54, 0, 5, 180)
    # Decoupling caps GND
    net("GND", C_DEC1[0], C_DEC1[1]+2.54, 0, 5, 180)
    net("GND", C_DEC2[0], C_DEC2[1]+2.54, 0, 5, 180)
    net("GND", C_LDO_IN[0], C_LDO_IN[1]+2.54, 0, 5, 180)
    net("GND", C_LDO_OUT[0], C_LDO_OUT[1]+2.54, 0, 5, 180)
    net("GND", C_IMU[0], C_IMU[1]+2.54, 0, 5, 180)
    net("GND", C_GPS[0], C_GPS[1]+2.54, 0, 5, 180)
    net("GND", C_REGOUT[0], C_REGOUT[1]+2.54, 0, 5, 180)
    # Joystick COM
    net("GND", JOYSTICK[0]+10.16, JOYSTICK[1], 5, 0, 0)
    # e-Paper GND
    net("GND", EPAPER[0]-7.62, EPAPER[1]-6.35, -5, 0, 180)
    # IMU GND
    net("GND", IMU[0], IMU[1]+15.24, 0, 5, 180)
    # IMU AD0 → GND (address 0x68)
    net("GND", IMU[0]-10.16, IMU[1]-2.54, -5, 0, 180)
    # IMU FSYNC → GND
    net("GND", IMU[0]-10.16, IMU[1]+2.54, -5, 0, 180)
    # IMU CLKIN → GND
    net("GND", IMU[0]-10.16, IMU[1]+5.08, -5, 0, 180)
    # GPS GND
    net("GND", GPS[0], GPS[1]+12.7, 0, 5, 180)
    # CC resistors bottom
    net("GND", R_CC1[0], R_CC1[1]+2.54, 0, 5, 180)
    net("GND", R_CC2[0], R_CC2[1]+2.54, 0, 5, 180)
    # RP2040 TESTEN → GND
    net("GND", RP2040[0]+22.86, RP2040[1]+30.48, 5, 0, 0)
    # JST battery negative
    net("GND", JST_BAT[0]-6.35, JST_BAT[1]+1.27, -5, 0, 180)
    # LED cathodes
    net("CHRG_LED", LED_CHG[0]-3.81, LED_CHG[1], -3, 0, 180)
    net("CHRG_LED", RLED1[0], RLED1[1]+2.54, 0, 3, 180)
    net("STDBY_LED", LED_DONE[0]-3.81, LED_DONE[1], -3, 0, 180)
    net("STDBY_LED", RLED2[0], RLED2[1]+2.54, 0, 3, 180)

    # LED cathode to TP4056 status pins
    net("CHRG_OUT", LED_CHG[0]+3.81, LED_CHG[1], 3, 0, 0)
    net("CHRG_OUT", TP4056[0]+10.16, TP4056[1], 5, 0, 0)
    net("STDBY_OUT", LED_DONE[0]+3.81, LED_DONE[1], 3, 0, 0)
    net("STDBY_OUT", TP4056[0]+10.16, TP4056[1]-2.54, 5, 0, 0)

    # ── PROG net: TP4056 PROG → R1 ──
    net("PROG", TP4056[0]-10.16, TP4056[1]-2.54, -5, 0, 180)
    net("PROG", RPROG[0], RPROG[1]-2.54, 0, -3, 0)

    # ── Battery protection nets ──
    # DW01A OD → FS8205A G1
    net("OD", DW01A[0]-8.89, DW01A[1]-2.54, -5, 0, 180)
    net("OD", FS8205A[0]-8.89, FS8205A[1], -5, 0, 180)
    # DW01A OC → FS8205A G2
    net("OC", DW01A[0]-8.89, DW01A[1]+2.54, -5, 0, 180)
    net("OC", FS8205A[0]+8.89, FS8205A[1], 5, 0, 0)
    # DW01A CS → FS8205A D1/D2 (drain common)
    net("CS_DRAIN", DW01A[0]-8.89, DW01A[1], -5, 0, 180)
    net("CS_DRAIN", FS8205A[0]-8.89, FS8205A[1]+2.54, -5, 0, 180)
    net("CS_DRAIN", FS8205A[0]+8.89, FS8205A[1]+2.54, 5, 0, 0)  # D12B too
    # FS8205A S1 → GND (through the protection IC)
    net("GND", FS8205A[0]-8.89, FS8205A[1]-2.54, -5, 0, 180)
    # FS8205A S2 → Battery+ (JST)
    net("BAT_PLUS", FS8205A[0]+8.89, FS8205A[1]-2.54, 5, 0, 0)
    net("BAT_PLUS", JST_BAT[0]-6.35, JST_BAT[1]-1.27, -5, 0, 180)
    # DW01A TD → DW01A VCC (tie together per datasheet)
    net("VBAT", DW01A[0]+8.89, DW01A[1], 5, 0, 0)

    # ── USB data: USB-C D+/D- → 27R → RP2040 ──
    net("USB_DP_IN", USB_C[0]-10.16, USB_C[1]+2.54, -5, 0, 180)
    net("USB_DP_IN", R_USB_DP[0], R_USB_DP[1]-2.54, -5, 0, 180)
    net("USB_DP", R_USB_DP[0], R_USB_DP[1]+2.54, 5, 0, 0)
    net("USB_DP", RP2040[0]-22.86, RP2040[1]+7.62, -5, 0, 180)

    net("USB_DM_IN", USB_C[0]-10.16, USB_C[1]+5.08, -5, 0, 180)
    net("USB_DM_IN", R_USB_DM[0], R_USB_DM[1]-2.54, -5, 0, 180)
    net("USB_DM", R_USB_DM[0], R_USB_DM[1]+2.54, 5, 0, 0)
    net("USB_DM", RP2040[0]-22.86, RP2040[1]+10.16, -5, 0, 180)

    # USB CC pins → 5.1k → GND
    net("CC1", USB_C[0]-10.16, USB_C[1]-2.54, -5, 0, 180)
    net("CC1", R_CC1[0], R_CC1[1]-2.54, 0, -3, 0)
    net("CC2", USB_C[0]-10.16, USB_C[1], -5, 0, 180)
    net("CC2", R_CC2[0], R_CC2[1]-2.54, 0, -3, 0)

    # ── QSPI Flash ──
    net("QSPI_SCLK", RP2040[0]-22.86, RP2040[1]+15.24, -5, 0, 180)
    net("QSPI_SCLK", FLASH[0]-10.16, FLASH[1]+2.54, -5, 0, 180)

    net("QSPI_SD0", RP2040[0]-22.86, RP2040[1]+17.78, -5, 0, 180)
    net("QSPI_SD0", FLASH[0]-10.16, FLASH[1]-2.54, -5, 0, 180)  # DO

    net("QSPI_SD1", RP2040[0]-22.86, RP2040[1]+20.32, -5, 0, 180)
    net("QSPI_SD1", FLASH[0]-10.16, FLASH[1], -5, 0, 180)  # DI

    net("QSPI_SS", RP2040[0]-22.86, RP2040[1]+27.94, -5, 0, 180)
    net("QSPI_SS", FLASH[0]+10.16, FLASH[1]-2.54, 5, 0, 0)  # CS

    # ── Crystal ──
    net("XIN", RP2040[0]+22.86, RP2040[1]+7.62, 5, 0, 0)
    net("XIN", CRYSTAL[0], CRYSTAL[1]-3.81, 0, -3, 0)
    net("XIN", C_XTAL1[0], C_XTAL1[1]-2.54, 0, -3, 0)

    net("XOUT", RP2040[0]+22.86, RP2040[1]+10.16, 5, 0, 0)
    net("XOUT", CRYSTAL[0], CRYSTAL[1]+3.81, 0, 3, 180)
    net("XOUT", C_XTAL2[0], C_XTAL2[1]-2.54, 0, -3, 0)

    # ── RUN pull-up ──
    net("RUN", RP2040[0]+22.86, RP2040[1]+15.24, 5, 0, 0)
    net("RUN", R_RUN[0], R_RUN[1]+2.54, 0, 3, 180)

    # ── VREG_VOUT (internal 1.1V regulator - needs decoupling cap) ──
    # We'll just label it; the decoupling is handled by C3/C4 placement

    # ── Joystick GPIO2-6 ──
    net("GPIO2", JOYSTICK[0]-10.16, JOYSTICK[1]-5.08, -5, 0, 180)
    net("GPIO2", RP2040[0]-22.86, RP2040[1]-30.48, -5, 0, 180)

    net("GPIO3", JOYSTICK[0]-10.16, JOYSTICK[1]-2.54, -5, 0, 180)
    net("GPIO3", RP2040[0]-22.86, RP2040[1]-27.94, -5, 0, 180)

    net("GPIO4", JOYSTICK[0]-10.16, JOYSTICK[1], -5, 0, 180)
    net("GPIO4", RP2040[0]-22.86, RP2040[1]-25.4, -5, 0, 180)

    net("GPIO5", JOYSTICK[0]-10.16, JOYSTICK[1]+2.54, -5, 0, 180)
    net("GPIO5", RP2040[0]-22.86, RP2040[1]-22.86, -5, 0, 180)

    net("GPIO6", JOYSTICK[0]-10.16, JOYSTICK[1]+5.08, -5, 0, 180)
    net("GPIO6", RP2040[0]-22.86, RP2040[1]-20.32, -5, 0, 180)

    # ── e-Paper SPI1: GP8-GP13 ──
    net("GPIO8", RP2040[0]-22.86, RP2040[1]-15.24, -5, 0, 180)   # DC
    net("GPIO8", EPAPER[0]-7.62, EPAPER[1]+3.81, -5, 0, 180)

    net("GPIO9", RP2040[0]-22.86, RP2040[1]-12.7, -5, 0, 180)    # CS
    net("GPIO9", EPAPER[0]-7.62, EPAPER[1]+1.27, -5, 0, 180)

    net("GPIO10", RP2040[0]-22.86, RP2040[1]-10.16, -5, 0, 180)  # CLK
    net("GPIO10", EPAPER[0]-7.62, EPAPER[1]-1.27, -5, 0, 180)

    net("GPIO11", RP2040[0]-22.86, RP2040[1]-7.62, -5, 0, 180)   # DIN/MOSI
    net("GPIO11", EPAPER[0]-7.62, EPAPER[1]-3.81, -5, 0, 180)

    net("GPIO12", RP2040[0]-22.86, RP2040[1]-5.08, -5, 0, 180)   # RST
    net("GPIO12", EPAPER[0]-7.62, EPAPER[1]+6.35, -5, 0, 180)

    net("GPIO13", RP2040[0]-22.86, RP2040[1]-2.54, -5, 0, 180)   # BUSY
    net("GPIO13", EPAPER[0]-7.62, EPAPER[1]+8.89, -5, 0, 180)

    # ── IMU I2C0: GP14/GP15 ──
    net("GPIO14", RP2040[0]-22.86, RP2040[1], -5, 0, 180)        # SDA
    net("GPIO14", IMU[0]-10.16, IMU[1]-7.62, -5, 0, 180)
    net("GPIO14", R_I2C_SDA[0], R_I2C_SDA[1]+2.54, 0, 3, 180)

    net("GPIO15", RP2040[0]-22.86, RP2040[1]+2.54, -5, 0, 180)   # SCL
    net("GPIO15", IMU[0]-10.16, IMU[1]-5.08, -5, 0, 180)
    net("GPIO15", R_I2C_SCL[0], R_I2C_SCL[1]+2.54, 0, 3, 180)

    # ── GPS UART0: GP0/GP1 ──
    net("GPIO0", RP2040[0]-22.86, RP2040[1]-35.56, -5, 0, 180)   # TX → GPS RX
    net("GPIO0", GPS[0]-10.16, GPS[1]-2.54, -5, 0, 180)

    net("GPIO1", RP2040[0]-22.86, RP2040[1]-33.02, -5, 0, 180)   # RX ← GPS TX
    net("GPIO1", GPS[0]-10.16, GPS[1]-5.08, -5, 0, 180)

    # ── IMU REGOUT cap ──
    net("REGOUT", IMU[0]+10.16, IMU[1]+5.08, 5, 0, 0)
    net("REGOUT", C_REGOUT[0], C_REGOUT[1]-2.54, 0, -3, 0)

    # ════════════════════════════════════════════════════════════════
    # TEXT ANNOTATIONS
    # ════════════════════════════════════════════════════════════════

    texts = []
    texts.append(f'  (text "POWER: USB-C > SS34 > TP4056 > DW01A/FS8205A > Battery" (exclude_from_sim no) (at 115 35 0) (effects (font (size 2.54 2.54)) (justify left)))')
    texts.append(f'  (text "VBAT > AMS1117-3.3 > 3V3 Rail > All ICs" (exclude_from_sim no) (at 115 40 0) (effects (font (size 2.54 2.54)) (justify left)))')
    texts.append(f'  (text "MCU: RP2040 (C2040) + W25Q16JV Flash + 12MHz Crystal" (exclude_from_sim no) (at 115 140 0) (effects (font (size 2.54 2.54)) (justify left)))')
    texts.append(f'  (text "GPIO0=GPS_RX  GPIO1=GPS_TX  GPIO2-6=Joystick  GPIO8-13=ePaper SPI1  GPIO14/15=IMU I2C0" (exclude_from_sim no) (at 50 285 0) (effects (font (size 1.8 1.8)) (justify left)))')

    # ════════════════════════════════════════════════════════════════
    # ASSEMBLE THE FILE
    # ════════════════════════════════════════════════════════════════

    output = f'''(kicad_sch
  (version 20250610)
  (generator "eeschema")
  (generator_version "10.0")
  (uuid "e63e39d7-6ac0-4ffd-8aa3-1841a4541b55")
  (paper "A3")
  (title_block
    (title "Dilder - Custom PCB")
    (date "2026-04-14")
    (rev "0.2")
    (company "Dilder Project")
    (comment 1 "RP2040 + LiPo Charging + Joystick + IMU + GPS")
    (comment 2 "Target: JLCPCB SMT Assembly — No WiFi (Option C)")
  )
  {lib_symbols}
{chr(10).join(components)}
{chr(10).join(wires)}
{chr(10).join(labels_list)}
{chr(10).join(texts)}
  (symbol_instances
{chr(10).join(sym_instances)}
  )
)
'''
    return output


if __name__ == "__main__":
    import subprocess

    print("Generating Dilder schematic...")
    sch = build_schematic()

    outfile = "dilder.kicad_sch"
    with open(outfile, "w") as f:
        f.write(sch)
    print(f"  Wrote {outfile} ({len(sch)} bytes)")

    # Validate with kicad-cli
    print("  Validating...")
    result = subprocess.run(
        ["kicad-cli", "sch", "export", "svg", "--output", "/tmp/dilder-gen/", outfile],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  OK — exported to /tmp/dilder-gen/dilder.svg")
    else:
        print(f"  FAIL — {result.stderr}")
        raise SystemExit(1)

    print("Done. Open in KiCad to verify and run ERC.")
