#!/usr/bin/env python3
"""
Dilder PCB v0.4 — 30x70mm, 28 components, 4-layer.

Changes from v0.3/v7:
  - Board shrunk from 45x80 to 30x70mm
  - MPU-6050 (QFN-24, 4x4mm) replaced with LIS2DH12TR (LGA-12, 2x2mm)
  - Added SW2 (BOOT button), SW3 (RESET button), R11, C8
  - Removed C9 (REGOUT cap — LIS2DH12 has no REGOUT)
  - Fixed joystick net mapping (all 6 pins)
  - Added octopus silkscreen on back
  - Added functional labels (USB-C, BAT, BOOT, RST, etc.)
  - Antenna keep-out zone enforced in GND zone shapes

Component zones (top to bottom):
  Zone A (y=0-3):    Antenna overhang — NO copper
  Zone B (y=3-25):   ESP32 module + decoupling + LEDs in margins
  Zone C (y=26-42):  Power section (LDO, TP4056, protection, battery)
  Zone D (y=42-54):  LIS2DH12 + ePaper header + BOOT/RESET buttons
  Zone E (y=54-62):  Joystick (centered)
  Zone F (y=62-70):  USB-C + CC resistors
"""

import pcbnew, os, subprocess, json, math

def mm(v): return pcbnew.FromMM(v)
def pos(x, y): return pcbnew.VECTOR2I(mm(100+x), mm(100+y))

BOARD_W = 30.0
BOARD_H = 70.0
BOARD_FILE = os.path.join(os.path.dirname(__file__) or ".", "dilder.kicad_pcb")
CX = BOARD_W / 2  # 15mm

# ESP32 module center — antenna overhangs top edge
# Module body: 18x25.5mm. Center at y=14.75 puts body top at y~2, antenna above
MCU_Y = 14.75

# Antenna keep-out: no copper within top 5mm of board (y=0 to y=5)
ANTENNA_KEEPOUT_Y = 5.0

COMPONENTS = [
    # ═══ ZONE B: ESP32 MODULE (y=3-25) ═══
    ("U1", "RF_Module:ESP32-S3-WROOM-1", CX, MCU_Y, 0, "ESP32-S3-N16R8", "C2913196"),

    # Left margin (x=1-5, beside module)
    ("C3", "Capacitor_SMD:C_0402_1005Metric", 3, 8, 90, "100nF", "C14663"),
    ("C4", "Capacitor_SMD:C_0402_1005Metric", 3, 12, 90, "10uF", "C19702"),
    ("R10", "Resistor_SMD:R_0402_1005Metric", 3, 16, 90, "10k", "C25744"),
    ("R11", "Resistor_SMD:R_0402_1005Metric", 3, 20, 90, "10k", "C25744"),

    # Right margin (x=25-29, beside module)
    ("D2", "LED_SMD:LED_0402_1005Metric", 27, 8, 90, "RED", "C84256"),
    ("R2", "Resistor_SMD:R_0402_1005Metric", 27, 12, 90, "1k", "C25585"),
    ("D3", "LED_SMD:LED_0402_1005Metric", 27, 16, 90, "GREEN", "C72043"),
    ("R3", "Resistor_SMD:R_0402_1005Metric", 27, 20, 90, "1k", "C25585"),

    # ═══ ZONE C: POWER (y=26-42) ═══
    ("U4", "Package_TO_SOT_SMD:SOT-223-3_TabPin2", CX, 29, 0, "AMS1117-3.3", "C6186"),
    ("C5", "Capacitor_SMD:C_0402_1005Metric", 5, 29, 0, "10uF", "C19702"),
    ("C6", "Capacitor_SMD:C_0402_1005Metric", 25, 29, 0, "10uF", "C19702"),

    ("U2", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", CX, 35, 0, "TP4056", "C382139"),
    ("R1", "Resistor_SMD:R_0402_1005Metric", 24, 33, 0, "1.2k", "C25752"),
    ("D1", "Diode_SMD:D_SMA", 5, 35, 0, "SS34", "C8678"),

    ("U3", "Package_TO_SOT_SMD:SOT-23-6", 7, 41, 0, "DW01A", "C351410"),
    ("Q1", "Package_TO_SOT_SMD:SOT-23-6", 23, 41, 0, "FS8205A", "C908265"),

    ("J2", "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
                                              27, 41, 270, "BAT", "C131337"),

    # ═══ ZONE D: PERIPHERALS (y=42-54) ═══
    # LIS2DH12TR — tiny (2x2mm), left side
    ("U5", "Package_LGA:LGA-12_2x2mm_P0.5mm", 6, 47, 0, "LIS2DH12TR", "C110926"),
    ("R4", "Resistor_SMD:R_0402_1005Metric", 3, 45, 90, "10k", "C25744"),
    ("R5", "Resistor_SMD:R_0402_1005Metric", 3, 49, 90, "10k", "C25744"),
    ("C7", "Capacitor_SMD:C_0402_1005Metric", 10, 45, 0, "100nF", "C14663"),

    # ePaper JST-SH 8-pin — right side
    ("J3", "Connector_JST:JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal",
                                              23, 47, 0, "ePaper", ""),

    # BOOT and RESET buttons
    ("SW2", "Button_Switch_SMD:SW_SPST_PTS810", 8, 52, 0, "BOOT", ""),
    ("SW3", "Button_Switch_SMD:SW_SPST_PTS810", 22, 52, 0, "RESET", ""),
    ("C8", "Capacitor_SMD:C_0402_1005Metric", 26, 52, 90, "100nF", "C14663"),

    # ═══ ZONE E: JOYSTICK (y=55-62) ═══
    ("SW1", "Button_Switch_SMD:SW_SPST_SKQG_WithStem", CX, 58, 0, "5-Way", "C139794"),

    # ═══ ZONE F: USB-C (y=62-70) ═══
    ("R8", "Resistor_SMD:R_0402_1005Metric", 7, 64, 0, "5.1k", ""),
    ("R9", "Resistor_SMD:R_0402_1005Metric", 7, 66, 0, "5.1k", ""),
    ("J1", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
                                              CX, 67, 0, "USB-C", "C2765186"),
]

# ═══ NET ASSIGNMENTS (pad → net) ═══
PA = {
    # ESP32-S3 module
    ("U1","1"):"GND", ("U1","2"):"3V3", ("U1","3"):"EN",
    ("U1","27"):"BOOT",  # GPIO0
    ("U1","4"):"JOY_UP", ("U1","5"):"JOY_DOWN",
    ("U1","6"):"JOY_LEFT", ("U1","7"):"JOY_RIGHT",
    ("U1","8"):"JOY_CENTER",
    ("U1","9"):"I2C_SDA", ("U1","10"):"I2C_SCL",
    ("U1","11"):"ACCEL_INT1",  # GPIO18
    ("U1","13"):"USB_DM", ("U1","14"):"USB_DP",
    ("U1","15"):"EPD_CLK", ("U1","16"):"EPD_MOSI",
    ("U1","17"):"EPD_DC", ("U1","18"):"EPD_RST",
    ("U1","19"):"EPD_CS", ("U1","20"):"EPD_BUSY",
    ("U1","31"):"GND", ("U1","32"):"GND",
    ("U1","40"):"GND", ("U1","41"):"GND",

    # USB-C connector
    ("J1","A4"):"VBUS", ("J1","B4"):"VBUS",
    ("J1","A1"):"GND", ("J1","B1"):"GND",
    ("J1","A12"):"GND", ("J1","B12"):"GND",
    ("J1","A6"):"USB_DP", ("J1","A7"):"USB_DM",
    ("J1","B6"):"USB_DP", ("J1","B7"):"USB_DM",
    ("J1","A5"):"CC1", ("J1","B5"):"CC2",

    # Schottky diode
    ("D1","1"):"VBUS", ("D1","2"):"VBUS_CHG",

    # TP4056 charger
    ("U2","8"):"VBUS_CHG", ("U2","3"):"VBAT", ("U2","2"):"PROG",
    ("U2","1"):"GND", ("U2","4"):"3V3", ("U2","5"):"GND",
    ("U2","7"):"CHRG_OUT", ("U2","6"):"STDBY_OUT",

    # Battery protection
    ("U3","1"):"OD", ("U3","2"):"CS_DRAIN", ("U3","3"):"OC",
    ("U3","4"):"VBAT", ("U3","5"):"VBAT", ("U3","6"):"GND",
    ("Q1","1"):"GND", ("Q1","2"):"OD", ("Q1","3"):"CS_DRAIN",
    ("Q1","4"):"CS_DRAIN", ("Q1","5"):"OC", ("Q1","6"):"BAT_PLUS",

    # Battery connector
    ("J2","1"):"BAT_PLUS", ("J2","2"):"GND",

    # LDO regulator
    ("U4","1"):"GND", ("U4","2"):"3V3", ("U4","3"):"VBAT", ("U4","4"):"3V3",

    # Decoupling caps
    ("C3","1"):"3V3", ("C3","2"):"GND",
    ("C4","1"):"3V3", ("C4","2"):"GND",
    ("C5","1"):"VBAT", ("C5","2"):"GND",
    ("C6","1"):"3V3", ("C6","2"):"GND",
    ("C7","1"):"3V3", ("C7","2"):"GND",
    ("C8","1"):"EN", ("C8","2"):"GND",

    # Resistors
    ("R1","1"):"PROG", ("R1","2"):"GND",
    ("R2","1"):"3V3", ("R2","2"):"CHRG_LED",
    ("R3","1"):"3V3", ("R3","2"):"STDBY_LED",
    ("R4","1"):"3V3", ("R4","2"):"I2C_SDA",
    ("R5","1"):"3V3", ("R5","2"):"I2C_SCL",
    ("R8","1"):"CC1", ("R8","2"):"GND",
    ("R9","1"):"CC2", ("R9","2"):"GND",
    ("R10","1"):"3V3", ("R10","2"):"EN",
    ("R11","1"):"3V3", ("R11","2"):"BOOT",

    # LEDs
    ("D2","1"):"CHRG_LED", ("D2","2"):"CHRG_OUT",
    ("D3","1"):"STDBY_LED", ("D3","2"):"STDBY_OUT",

    # Joystick (all 6 pins)
    ("SW1","1"):"JOY_UP", ("SW1","2"):"JOY_DOWN",
    ("SW1","3"):"JOY_LEFT", ("SW1","4"):"JOY_RIGHT",
    ("SW1","5"):"JOY_CENTER", ("SW1","6"):"GND",

    # BOOT and RESET buttons
    ("SW2","1"):"BOOT", ("SW2","2"):"GND",
    ("SW3","1"):"EN", ("SW3","2"):"GND",

    # ePaper header
    ("J3","1"):"3V3", ("J3","2"):"GND",
    ("J3","3"):"EPD_MOSI", ("J3","4"):"EPD_CLK",
    ("J3","5"):"EPD_CS", ("J3","6"):"EPD_DC",
    ("J3","7"):"EPD_RST", ("J3","8"):"EPD_BUSY",

    # LIS2DH12TR accelerometer
    ("U5","10"):"3V3", ("U5","1"):"3V3",  # VDD, VDD_IO
    ("U5","5"):"GND",                      # GND
    ("U5","6"):"I2C_SDA", ("U5","7"):"I2C_SCL",
    ("U5","4"):"3V3",                      # CS → HIGH for I2C mode
    ("U5","3"):"GND",                      # SA0 → LOW for addr 0x18
    ("U5","8"):"ACCEL_INT1",               # INT1
    ("U5","2"):"GND",                      # RES → GND per datasheet
}

ALL_NETS = sorted(set(v for v in PA.values() if v))


def make_smd_pad(fp, num, x, y, w, h, shape=pcbnew.PAD_SHAPE_RECT):
    """Create an SMD pad on a footprint."""
    pad = pcbnew.PAD(fp)
    pad.SetNumber(str(num))
    pad.SetShape(shape)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetLayerSet(pad.SMDMask())
    pad.SetSize(pcbnew.VECTOR2I(mm(w), mm(h)))
    pad.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    fp.Add(pad)
    return pad


def make_footprint(board, ref, fp_lib):
    """Create a minimal footprint with correct pads when KiCad libs aren't installed."""
    fp = pcbnew.FOOTPRINT(board)

    # ── 0402 (1005 Metric) — resistors, caps, LEDs ──
    if "0402" in fp_lib or "LED_0402" in fp_lib:
        make_smd_pad(fp, "1", -0.48, 0, 0.56, 0.62)
        make_smd_pad(fp, "2",  0.48, 0, 0.56, 0.62)

    # ── ESP32-S3-WROOM-1 module (18x25.5mm) ──
    elif "ESP32-S3-WROOM-1" in fp_lib:
        # Left column pins (14 pins, pitch 1.27mm)
        left_pins = [("2",0), ("3",1), ("27",2), ("4",3), ("5",4), ("6",5),
                     ("7",6), ("8",7), ("9",8), ("10",9), ("11",10),
                     ("13",11), ("14",12)]
        for pnum, idx in left_pins:
            make_smd_pad(fp, pnum, -9.5, -11.43 + idx * 1.27, 0.9, 0.6)
        # Bottom row pins (6 pins)
        bot_pins = [("15",0), ("16",1), ("17",2), ("18",3), ("19",4), ("20",5)]
        for pnum, idx in bot_pins:
            make_smd_pad(fp, pnum, -6.35 + idx * 1.27, 12.75, 0.6, 0.9)
        # GND pad (large central)
        make_smd_pad(fp, "1", 0, 12.75, 6.0, 0.9)
        # Additional GND pads (castellation)
        for g in ["31", "32", "40", "41"]:
            make_smd_pad(fp, g, 9.5, 0, 0.9, 0.6)

    # ── SOT-223-3 (AMS1117) ──
    elif "SOT-223" in fp_lib:
        make_smd_pad(fp, "1", -2.3, 3.25, 1.0, 1.5)
        make_smd_pad(fp, "2",  0.0, 3.25, 1.0, 1.5)
        make_smd_pad(fp, "3",  2.3, 3.25, 1.0, 1.5)
        make_smd_pad(fp, "4",  0.0, -3.25, 3.3, 1.5)  # Tab

    # ── SOIC-8 / ESOP-8 (TP4056) ──
    elif "SOIC-8" in fp_lib or "ESOP-8" in fp_lib:
        for i in range(4):
            make_smd_pad(fp, str(i + 1), -1.905 + i * 1.27, 2.7, 0.6, 1.5)
            make_smd_pad(fp, str(8 - i), -1.905 + i * 1.27, -2.7, 0.6, 1.5)

    # ── SOT-23-6 (DW01A, FS8205A) ──
    elif "SOT-23-6" in fp_lib:
        for i in range(3):
            make_smd_pad(fp, str(i + 1), -0.95 + i * 0.95, 1.1, 0.6, 0.7)
            make_smd_pad(fp, str(6 - i), -0.95 + i * 0.95, -1.1, 0.6, 0.7)

    # ── SMA diode (SS34) ──
    elif "D_SMA" in fp_lib:
        make_smd_pad(fp, "1", -2.0, 0, 1.5, 1.5)
        make_smd_pad(fp, "2",  2.0, 0, 1.5, 1.5)

    # ── USB-C (HRO TYPE-C-31-M-12) ──
    elif "USB_C" in fp_lib:
        usb_pins = {
            "A1": (-3.25, 4.1), "A4": (-2.45, 4.1),
            "A5": (-0.25, 4.1), "A6": (0.25, 4.1),
            "A7": (0.75, 4.1), "A12": (3.25, 4.1),
            "B1": (-3.25, 4.1), "B4": (2.45, 4.1),
            "B5": (1.75, 4.1), "B6": (-0.75, 4.1),
            "B7": (-1.25, 4.1), "B12": (3.25, 4.1),
        }
        for pnum, (px, py) in usb_pins.items():
            make_smd_pad(fp, pnum, px, py, 0.3, 1.0)
        # Shield pins
        make_smd_pad(fp, "S1", -4.32, 0, 1.0, 1.5)

    # ── JST PH 2-pin (battery) ──
    elif "JST_PH" in fp_lib:
        make_smd_pad(fp, "1", -1.0, 0, 1.0, 2.0)
        make_smd_pad(fp, "2",  1.0, 0, 1.0, 2.0)

    # ── JST SH 8-pin (ePaper) ──
    elif "JST_SH" in fp_lib:
        for i in range(8):
            make_smd_pad(fp, str(i + 1), -3.5 + i * 1.0, 0, 0.6, 1.2)

    # ── LGA-12 2x2mm (LIS2DH12TR) ──
    elif "LGA-12" in fp_lib:
        # 12 pads around a 2x2mm package, 0.5mm pitch
        # Left column: pins 1-3 (bottom to top)
        for i in range(3):
            make_smd_pad(fp, str(i + 1), -1.0, 0.5 - i * 0.5, 0.55, 0.3)
        # Bottom: pins 4-6
        for i in range(3):
            make_smd_pad(fp, str(i + 4), -0.5 + i * 0.5, 1.0, 0.3, 0.55)
        # Right column: pins 7-9
        for i in range(3):
            make_smd_pad(fp, str(i + 7), 1.0, 0.5 - i * 0.5, 0.55, 0.3)
        # Top: pins 10-12
        for i in range(3):
            make_smd_pad(fp, str(i + 10), 0.5 - i * 0.5, -1.0, 0.3, 0.55)

    # ── Push button (PTS810 / SKQG) ──
    elif "SW_SPST" in fp_lib or "PTS810" in fp_lib:
        make_smd_pad(fp, "1", -2.25, 0, 1.0, 1.2)
        make_smd_pad(fp, "2",  2.25, 0, 1.0, 1.2)
        # For 5-way joystick, add extra pads
        if "SKQG" in fp_lib:
            for i in range(3, 7):
                make_smd_pad(fp, str(i), -2.25 + (i - 1) * 0.9, 2.0, 0.6, 0.8)

    else:
        return None

    return fp


def draw_octopus_silkscreen(board):
    """Draw a small octopus on the back silkscreen (B.SilkS)."""
    # Center the octopus on the back of the board
    ocx, ocy = CX, 35.0
    layer = pcbnew.B_SilkS
    width = mm(0.2)

    def line(x1, y1, x2, y2):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pos(ocx + x1, ocy + y1))
        seg.SetEnd(pos(ocx + x2, ocy + y2))
        seg.SetLayer(layer)
        seg.SetWidth(width)
        board.Add(seg)

    def arc(cx_, cy_, r, start_deg, end_deg, steps=16):
        for i in range(steps):
            a1 = math.radians(start_deg + (end_deg - start_deg) * i / steps)
            a2 = math.radians(start_deg + (end_deg - start_deg) * (i + 1) / steps)
            line(cx_ + r * math.cos(a1), cy_ + r * math.sin(a1),
                 cx_ + r * math.cos(a2), cy_ + r * math.sin(a2))

    # Head (dome)
    arc(0, -2, 5, 180, 360, 20)
    # Body sides
    line(-5, -2, -5, 2)
    line(5, -2, 5, 2)
    # Body bottom curve
    arc(0, 2, 5, 0, 180, 12)

    # Eyes (small circles)
    arc(-2, -2, 0.8, 0, 360, 8)
    arc(2, -2, 0.8, 0, 360, 8)

    # Tentacles (4 wavy lines)
    for tx in [-4, -1.5, 1.5, 4]:
        y0 = 4
        for seg_i in range(4):
            y1 = y0 + 1.5
            dx = 0.8 if seg_i % 2 == 0 else -0.8
            line(tx, y0, tx + dx, y1)
            tx += dx
            y0 = y1

    # Mouth (small smile)
    arc(0, 0, 1.5, 20, 160, 6)


def main():
    print("=" * 55)
    print(f"  Dilder v0.4 — {BOARD_W}x{BOARD_H}mm, 28 components")
    print("=" * 55)

    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    ds.m_TrackMinWidth = mm(0.127)
    ds.m_ViasMinSize = mm(0.6)
    ds.m_ViasMinDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.3)
    board.SetCopperLayerCount(4)

    # Board outline (30x70mm)
    pts = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pos(*pts[i]))
        seg.SetEnd(pos(*pts[(i + 1) % 4]))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.15))
        board.Add(seg)

    # Nets
    nm = {}
    for i, n in enumerate(ALL_NETS, 1):
        net = pcbnew.NETINFO_ITEM(board, n, i)
        board.Add(net)
        nm[n] = net

    # Place components — try loading from library, fall back to manual creation
    placed = 0
    skipped = []
    for ref, fp_lib, x, y, angle, value, lcsc in COMPONENTS:
        lib, name = fp_lib.split(":")
        path = f"/usr/share/kicad/footprints/{lib}.pretty"
        fp = pcbnew.FootprintLoad(path, name) if os.path.exists(path) else None
        if not fp:
            # Create minimal footprint manually (for systems without KiCad libs)
            fp = make_footprint(board, ref, fp_lib)
        if not fp:
            skipped.append(ref)
            continue
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetPosition(pos(x, y))
        if angle:
            fp.SetOrientationDegrees(angle)
        fp.SetLayer(pcbnew.F_Cu)
        board.Add(fp)
        placed += 1

    print(f"  Placed {placed}/{len(COMPONENTS)} components")
    if skipped:
        print(f"  Skipped (missing footprint): {', '.join(skipped)}")

    # Assign nets to pads
    assigned = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            key = (ref, str(pad.GetNumber()))
            if key in PA and PA[key] in nm:
                pad.SetNet(nm[PA[key]])
                assigned += 1

    print(f"  Assigned {assigned} pad-net connections")

    # GND zones on F.Cu and B.Cu — with antenna keep-out
    # The antenna area (top ~5mm) must have no copper on ANY layer
    for layer in [pcbnew.F_Cu, pcbnew.B_Cu]:
        zone = pcbnew.ZONE(board)
        zone.SetNet(nm["GND"])
        zone.SetLayer(layer)
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        zone.SetMinThickness(mm(0.2))
        zone.SetThermalReliefGap(mm(0.3))
        zone.SetThermalReliefSpokeWidth(mm(0.4))
        o = zone.Outline()
        o.NewOutline()
        m = 0.3  # margin from edge
        # Start below antenna keep-out zone
        o.Append(mm(100 + m), mm(100 + ANTENNA_KEEPOUT_Y))
        o.Append(mm(100 + BOARD_W - m), mm(100 + ANTENNA_KEEPOUT_Y))
        o.Append(mm(100 + BOARD_W - m), mm(100 + BOARD_H - m))
        o.Append(mm(100 + m), mm(100 + BOARD_H - m))
        board.Add(zone)

    # Front silkscreen — board labels
    labels = [
        ("DILDER v0.4", CX, BOARD_H - 1.5, 1.0),
        ("USB-C", CX, 63, 0.7),
        ("BAT", 27, 38, 0.6),
        ("BOOT", 8, 54.5, 0.5),
        ("RST", 22, 54.5, 0.5),
        ("ePaper", 23, 44, 0.5),
    ]
    for txt, x, y, sz in labels:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt)
        t.SetPosition(pos(x, y))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(sz), mm(sz)))
        t.SetTextThickness(mm(sz * 0.15))
        board.Add(t)

    # Back silkscreen — octopus art
    draw_octopus_silkscreen(board)

    # Back silkscreen — project info
    for txt, x, y, sz in [
        ("DILDER", CX, 55, 1.5),
        ("dilder.dev", CX, 58, 0.8),
        ("v0.4  2026", CX, 61, 0.6),
    ]:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt)
        t.SetPosition(pos(x, y))
        t.SetLayer(pcbnew.B_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(sz), mm(sz)))
        t.SetTextThickness(mm(sz * 0.15))
        board.Add(t)

    board.Save(BOARD_FILE)
    print(f"  Saved: {BOARD_FILE}")
    print(f"  Board: {BOARD_W}x{BOARD_H}mm, 4-layer, {len(COMPONENTS)} components")
    print(f"  Antenna keep-out: top {ANTENNA_KEEPOUT_Y}mm (no copper)")

    # DRC check
    print("  Running DRC...")
    os.makedirs("/tmp/dilder-drc", exist_ok=True)
    subprocess.run(["kicad-cli", "pcb", "drc", "--output", "/tmp/dilder-drc/drc-report.json",
                    "--format", "json", "--severity-all", BOARD_FILE], capture_output=True)
    try:
        with open("/tmp/dilder-drc/drc-report.json") as f:
            drc = json.load(f)
        v = drc.get("violations", [])
        by_type = {}
        for x in v:
            by_type.setdefault(x["type"], 0)
            by_type[x["type"]] += 1
        for t in ["courtyards_overlap", "copper_edge_clearance", "silk_overlap"]:
            if t in by_type:
                print(f"    {t}: {by_type[t]}")
        uncon = len(drc.get("unconnected_items", []))
        print(f"    unconnected: {uncon} (expected — no routing yet)")
    except Exception:
        pass

    # Render
    print("  Rendering...")
    os.makedirs("/tmp/dilder-v04", exist_ok=True)
    for args, out in [
        ([], "board-top.png"),
        (["--perspective", "--rotate", "-35,0,15"], "board-3d.png"),
        (["--side", "back"], "board-back.png"),
    ]:
        subprocess.run(["kicad-cli", "pcb", "render", "--output", f"/tmp/dilder-v04/{out}",
                       "--width", "2400", "--height", "1600", "--quality", "basic",
                       *args, BOARD_FILE], capture_output=True)

    print("  Renders saved to /tmp/dilder-v04/")
    print("  Done! Open in KiCad to verify placement.")


if __name__ == "__main__":
    main()
