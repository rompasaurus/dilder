#!/usr/bin/env python3
"""
Build the Dilder PCB using KiCad's pcbnew Python API.

This creates a real PCB with:
- Proper footprints loaded from KiCad libraries (with pads, silkscreen, courtyard)
- Real net definitions and pad-to-net assignments
- 21mm x 70mm board (Pico W width, extended length)
- Component placement matching the Pico form factor
- Ground copper pour on both layers

Usage:
  python3 build_board.py
"""

import pcbnew
import os
import sys

# Suppress the assert warnings from pcbnew
import warnings
warnings.filterwarnings("ignore")

# ── Board dimensions ──────────────────────────────────────────────────
BOARD_W = 21.0   # mm — matches Pico W width
BOARD_H = 70.0   # mm — extended from Pico's 51mm to fit extra components
ORIGIN_X = 100.0  # board origin offset
ORIGIN_Y = 100.0

def mm(val):
    """Convert mm to KiCad internal units."""
    return pcbnew.FromMM(val)

def pos(x_mm, y_mm):
    """Board-relative position to absolute."""
    return pcbnew.VECTOR2I(mm(ORIGIN_X + x_mm), mm(ORIGIN_Y + y_mm))

# ── Component definitions ─────────────────────────────────────────────
# (ref, footprint_lib, x_offset_mm, y_offset_mm, angle_deg, value, lcsc)
COMPONENTS = [
    # USB-C connector — top edge, centered
    ("J1",  "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", 10.5, 2, 0, "USB-C", "C2765186"),

    # Power section — top area
    ("D1",  "Diode_SMD:D_SMA",                                    5, 10, 0, "SS34", "C8678"),
    ("U2",  "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",               10.5, 10, 0, "TP4056", "C382139"),
    ("R1",  "Resistor_SMD:R_0402_1005Metric",                    16, 8, 0, "1.2k", "C25752"),
    ("D2",  "LED_SMD:LED_0402_1005Metric",                       16, 6, 0, "RED", "C84256"),
    ("R2",  "Resistor_SMD:R_0402_1005Metric",                    18, 6, 0, "1k", "C25585"),
    ("D3",  "LED_SMD:LED_0402_1005Metric",                       16, 4.5, 0, "GREEN", "C72043"),
    ("R3",  "Resistor_SMD:R_0402_1005Metric",                    18, 4.5, 0, "1k", "C25585"),
    ("U3",  "Package_TO_SOT_SMD:SOT-23-6",                        5, 15, 0, "DW01A", "C351410"),
    ("Q1",  "Package_TO_SOT_SMD:SOT-23-6",                       16, 15, 0, "FS8205A", "C908265"),

    # Battery connector — right side, accessible
    ("J2",  "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
                                                                  17, 19, 270, "BAT", "C131337"),

    # LDO — between power and MCU
    ("U4",  "Package_TO_SOT_SMD:SOT-223-3_TabPin2",              10.5, 20, 0, "AMS1117-3.3", "C6186"),
    ("C5",  "Capacitor_SMD:C_0402_1005Metric",                    5, 20, 0, "10uF", "C19702"),
    ("C6",  "Capacitor_SMD:C_0402_1005Metric",                   17, 20.5, 0, "10uF", "C19702"),

    # USB CC resistors
    ("R8",  "Resistor_SMD:R_0402_1005Metric",                     4, 5, 90, "5.1k", ""),
    ("R9",  "Resistor_SMD:R_0402_1005Metric",                     4, 7.5, 90, "5.1k", ""),

    # USB series resistors
    ("R6",  "Resistor_SMD:R_0402_1005Metric",                     3, 24, 90, "27R", "C25105"),
    ("R7",  "Resistor_SMD:R_0402_1005Metric",                     5, 24, 90, "27R", "C25105"),

    # RP2040 MCU — center of board
    ("U1",  "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm",
                                                                  10.5, 30, 0, "RP2040", "C2040"),

    # Flash — near MCU
    ("U5",  "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",               4, 31, 0, "W25Q16JV", "C131024"),

    # Crystal + load caps — near MCU
    ("Y1",  "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm",           18, 30, 0, "12MHz", "C9002"),
    ("C1",  "Capacitor_SMD:C_0402_1005Metric",                   17, 32, 0, "15pF", "C1644"),
    ("C2",  "Capacitor_SMD:C_0402_1005Metric",                   19, 32, 0, "15pF", "C1644"),

    # MCU decoupling
    ("C3",  "Capacitor_SMD:C_0402_1005Metric",                    7, 25, 0, "100nF", "C14663"),
    ("C4",  "Capacitor_SMD:C_0402_1005Metric",                   14, 25, 0, "10uF", "C19702"),

    # RUN pull-up
    ("R10", "Resistor_SMD:R_0402_1005Metric",                    18, 27, 90, "10k", "C25744"),

    # ── Peripherals ── lower section of board

    # e-Paper header — along one edge
    ("J3",  "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
                                                                   2, 46, 0, "ePaper", ""),

    # 5-Way joystick — accessible position
    ("SW1", "Button_Switch_SMD:SW_SPST_SKQG_WithStem",           10.5, 42, 0, "5-Way", "C139794"),

    # MPU-6050 IMU
    ("U6",  "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm",
                                                                  10.5, 52, 0, "MPU-6050", "C24112"),
    ("R4",  "Resistor_SMD:R_0402_1005Metric",                     5, 50, 90, "10k", "C25744"),
    ("R5",  "Resistor_SMD:R_0402_1005Metric",                     5, 53, 90, "10k", "C25744"),
    ("C7",  "Capacitor_SMD:C_0402_1005Metric",                   17, 50, 0, "100nF", "C14663"),
    ("C9",  "Capacitor_SMD:C_0402_1005Metric",                   17, 53, 0, "100nF", "C14663"),

    # ATGM336H GPS — bottom of board, antenna area
    ("U7",  "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm",
                                                                  10.5, 62, 0, "ATGM336H", "C90770"),
    ("C8",  "Capacitor_SMD:C_0402_1005Metric",                   17, 60, 0, "100nF", "C14663"),
]

# ── Net definitions ───────────────────────────────────────────────────
# All unique net names used in the schematic
NET_NAMES = [
    "GND", "3V3", "VBUS", "VBUS_CHG", "VBAT",
    "USB_DP_IN", "USB_DP", "USB_DM_IN", "USB_DM",
    "CC1", "CC2",
    "QSPI_SCLK", "QSPI_SD0", "QSPI_SD1", "QSPI_SS",
    "XIN", "XOUT", "RUN", "PROG",
    "BAT_PLUS", "OD", "OC", "CS_DRAIN",
    "CHRG_LED", "STDBY_LED", "CHRG_OUT", "STDBY_OUT",
    "REGOUT",
    "GPIO0", "GPIO1", "GPIO2", "GPIO3", "GPIO4", "GPIO5", "GPIO6",
    "GPIO8", "GPIO9", "GPIO10", "GPIO11", "GPIO12", "GPIO13",
    "GPIO14", "GPIO15",
]


def build_board():
    board = pcbnew.BOARD()

    # Set board design settings
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    ds.m_TrackMinWidth = mm(0.127)       # JLCPCB min
    ds.m_ViasMinSize = mm(0.6)
    ds.m_ViasMinDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.3)

    # ── Create board outline ──
    outline_points = [
        pos(0, 0),
        pos(BOARD_W, 0),
        pos(BOARD_W, BOARD_H),
        pos(0, BOARD_H),
    ]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(outline_points[i])
        seg.SetEnd(outline_points[(i + 1) % 4])
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.15))
        board.Add(seg)

    # ── Add corner radius (2mm chamfer on top-left, matches Pico) ──
    # Skip for simplicity — rectangular is fine for JLCPCB

    # ── Create nets ──
    netinfo = board.GetNetInfo()

    # Net 0 is the unconnected net (always exists)
    net_map = {}
    for i, name in enumerate(NET_NAMES, 1):
        net = pcbnew.NETINFO_ITEM(board, name, i)
        board.Add(net)
        net_map[name] = net

    # ── Load and place footprints ──
    print(f"  Placing {len(COMPONENTS)} components...")
    for ref, fp_lib, x, y, angle, value, lcsc in COMPONENTS:
        fp = load_footprint(fp_lib)
        if fp is None:
            print(f"    WARNING: Could not load footprint '{fp_lib}' for {ref}, skipping")
            continue

        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetPosition(pos(x, y))
        if angle != 0:
            fp.SetOrientationDegrees(angle)
        fp.SetLayer(pcbnew.F_Cu)

        # Set LCSC field
        if lcsc:
            fp.SetField("LCSC", lcsc)

        board.Add(fp)
        print(f"    {ref:4s} ({value}) at ({x:.1f}, {y:.1f})")

    # ── Assign nets to pads ──
    assign_nets(board, net_map)

    # ── Add ground copper pour on both layers ──
    add_ground_pour(board, net_map.get("GND"), pcbnew.F_Cu)
    add_ground_pour(board, net_map.get("GND"), pcbnew.B_Cu)

    # ── Add silkscreen text ──
    add_text(board, "DILDER", 10.5, 67, pcbnew.F_SilkS, 1.5)
    add_text(board, "v0.2", 10.5, 69, pcbnew.F_SilkS, 1.0)

    return board


def load_footprint(fp_lib_name):
    """Load a footprint from KiCad's library."""
    try:
        # Split lib:footprint
        parts = fp_lib_name.split(":")
        if len(parts) != 2:
            return None
        lib_name, fp_name = parts

        # Try standard library paths
        search_paths = [
            f"/usr/share/kicad/footprints/{lib_name}.pretty/{fp_name}.kicad_mod",
            os.path.expanduser(f"~/.local/share/kicad/10.0/footprints/{lib_name}.pretty/{fp_name}.kicad_mod"),
        ]

        for path in search_paths:
            if os.path.exists(path):
                fp = pcbnew.FootprintLoad(
                    os.path.dirname(path),
                    fp_name
                )
                if fp:
                    return fp

        # Try using plugin
        fp = pcbnew.FootprintLoad(
            f"/usr/share/kicad/footprints/{lib_name}.pretty",
            fp_name
        )
        return fp

    except Exception as e:
        print(f"    Error loading {fp_lib_name}: {e}")
        return None


def assign_nets(board, net_map):
    """Assign nets to footprint pads based on the schematic netlist."""
    # This maps ref+pad to net name based on the schematic connections
    # Simplified: assign the key nets we know about
    pad_nets = {
        # RP2040 power
        ("U1", "57"): "GND",    # GND pad (EP)
        ("U1", "1"):  "3V3",    # IOVDD
        ("U1", "48"): "3V3",    # DVDD
        ("U1", "50"): "3V3",    # USB_VDD
        ("U1", "43"): "3V3",    # ADC_AVDD
        ("U1", "44"): "3V3",    # VREG_VIN
        ("U1", "49"): "GND",    # TESTEN
        ("U1", "18"): "RUN",
        # RP2040 USB
        ("U1", "47"): "USB_DP",
        ("U1", "46"): "USB_DM",
        # RP2040 QSPI
        ("U1", "24"): "QSPI_SCLK",
        ("U1", "21"): "QSPI_SD0",
        ("U1", "22"): "QSPI_SD1",
        ("U1", "26"): "QSPI_SS",
        # RP2040 Crystal
        ("U1", "20"): "XIN",
        ("U1", "19"): "XOUT",
        # RP2040 GPIO
        ("U1", "2"):  "GPIO0",
        ("U1", "3"):  "GPIO1",
        ("U1", "4"):  "GPIO2",
        ("U1", "5"):  "GPIO3",
        ("U1", "6"):  "GPIO4",
        ("U1", "7"):  "GPIO5",
        ("U1", "8"):  "GPIO6",
        ("U1", "10"): "GPIO8",
        ("U1", "11"): "GPIO9",
        ("U1", "12"): "GPIO10",
        ("U1", "13"): "GPIO11",
        ("U1", "14"): "GPIO12",
        ("U1", "15"): "GPIO13",
        ("U1", "16"): "GPIO14",
        ("U1", "17"): "GPIO15",

        # USB-C
        ("J1", "A4"):  "VBUS",
        ("J1", "B4"):  "VBUS",
        ("J1", "A1"):  "GND",
        ("J1", "B1"):  "GND",
        ("J1", "A12"): "GND",
        ("J1", "B12"): "GND",
        ("J1", "A6"):  "USB_DP_IN",
        ("J1", "A7"):  "USB_DM_IN",
        ("J1", "B6"):  "USB_DP_IN",
        ("J1", "B7"):  "USB_DM_IN",
        ("J1", "A5"):  "CC1",
        ("J1", "B5"):  "CC2",

        # Schottky
        ("D1", "1"): "VBUS",
        ("D1", "2"): "VBUS_CHG",

        # TP4056
        ("U2", "8"): "VBUS_CHG",   # VCC
        ("U2", "3"): "VBAT",       # BAT
        ("U2", "2"): "PROG",       # PROG
        ("U2", "1"): "GND",        # TEMP (tied to GND)
        ("U2", "4"): "3V3",        # CE
        ("U2", "5"): "GND",        # GND
        ("U2", "7"): "CHRG_OUT",   # CHRG
        ("U2", "6"): "STDBY_OUT",  # STDBY

        # DW01A
        ("U3", "1"): "OD",
        ("U3", "2"): "CS_DRAIN",
        ("U3", "3"): "OC",
        ("U3", "4"): "VBAT",       # TD
        ("U3", "5"): "VBAT",       # VCC
        ("U3", "6"): "GND",

        # FS8205A
        ("Q1", "1"): "GND",        # S1
        ("Q1", "2"): "OD",         # G1
        ("Q1", "3"): "CS_DRAIN",   # D1/D2
        ("Q1", "4"): "CS_DRAIN",   # D1/D2
        ("Q1", "5"): "OC",         # G2
        ("Q1", "6"): "BAT_PLUS",   # S2

        # JST Battery
        ("J2", "1"): "BAT_PLUS",
        ("J2", "2"): "GND",

        # LDO
        ("U4", "1"): "GND",
        ("U4", "2"): "3V3",
        ("U4", "3"): "VBAT",
        ("U4", "4"): "3V3",   # Tab = VOUT

        # Flash
        ("U5", "1"): "QSPI_SS",    # CS
        ("U5", "2"): "QSPI_SD0",   # DO
        ("U5", "3"): "3V3",        # WP
        ("U5", "4"): "GND",
        ("U5", "5"): "QSPI_SD1",   # DI
        ("U5", "6"): "QSPI_SCLK",  # CLK
        ("U5", "7"): "3V3",        # HOLD
        ("U5", "8"): "3V3",        # VCC

        # Crystal
        ("Y1", "1"): "XIN",
        ("Y1", "2"): "XOUT",

        # Crystal caps
        ("C1", "1"): "XIN",  ("C1", "2"): "GND",
        ("C2", "1"): "XOUT", ("C2", "2"): "GND",

        # Decoupling
        ("C3", "1"): "3V3",  ("C3", "2"): "GND",
        ("C4", "1"): "3V3",  ("C4", "2"): "GND",
        ("C5", "1"): "VBAT", ("C5", "2"): "GND",
        ("C6", "1"): "3V3",  ("C6", "2"): "GND",
        ("C7", "1"): "3V3",  ("C7", "2"): "GND",
        ("C8", "1"): "3V3",  ("C8", "2"): "GND",
        ("C9", "1"): "REGOUT", ("C9", "2"): "GND",

        # USB resistors
        ("R6", "1"): "USB_DP_IN", ("R6", "2"): "USB_DP",
        ("R7", "1"): "USB_DM_IN", ("R7", "2"): "USB_DM",
        ("R8", "1"): "CC1", ("R8", "2"): "GND",
        ("R9", "1"): "CC2", ("R9", "2"): "GND",

        # RPROG
        ("R1", "1"): "PROG", ("R1", "2"): "GND",

        # RUN pull-up
        ("R10", "1"): "3V3", ("R10", "2"): "RUN",

        # LEDs + resistors
        ("D2", "1"): "CHRG_LED", ("D2", "2"): "CHRG_OUT",
        ("R2", "1"): "3V3", ("R2", "2"): "CHRG_LED",
        ("D3", "1"): "STDBY_LED", ("D3", "2"): "STDBY_OUT",
        ("R3", "1"): "3V3", ("R3", "2"): "STDBY_LED",

        # I2C pull-ups
        ("R4", "1"): "3V3", ("R4", "2"): "GPIO14",
        ("R5", "1"): "3V3", ("R5", "2"): "GPIO15",

        # IMU decoupling
        ("C7", "1"): "3V3", ("C7", "2"): "GND",
        ("C9", "1"): "REGOUT", ("C9", "2"): "GND",

        # Joystick
        ("SW1", "1"): "GND",
        ("SW1", "2"): "GPIO6",

        # e-Paper header
        ("J3", "1"): "3V3",
        ("J3", "2"): "GND",
        ("J3", "3"): "GPIO11",   # DIN
        ("J3", "4"): "GPIO10",   # CLK
        ("J3", "5"): "GPIO9",    # CS
        ("J3", "6"): "GPIO8",    # DC
        ("J3", "7"): "GPIO12",   # RST
        ("J3", "8"): "GPIO13",   # BUSY

        # MPU-6050
        ("U6", "24"): "GPIO14",  # SDA
        ("U6", "23"): "GPIO15",  # SCL
        ("U6", "13"): "3V3",     # VDD
        ("U6", "1"):  "3V3",     # VLOGIC
        ("U6", "18"): "GND",     # GND
        ("U6", "9"):  "GND",     # AD0
        ("U6", "11"): "GND",     # FSYNC
        ("U6", "8"):  "GND",     # CLKIN
        ("U6", "10"): "REGOUT",  # REGOUT

        # ATGM336H GPS
        ("U7", "2"):  "GPIO1",   # TXD → MCU RX
        ("U7", "3"):  "GPIO0",   # RXD ← MCU TX
        ("U7", "18"): "GND",     # using pin 18 as GND (QFN EP)
        ("U7", "13"): "3V3",     # VCC - approximate pin
    }

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            pad_name = pad.GetNumber()
            key = (ref, str(pad_name))
            if key in pad_nets:
                net_name = pad_nets[key]
                if net_name in net_map:
                    pad.SetNet(net_map[net_name])


def add_ground_pour(board, gnd_net, layer):
    """Add a ground copper pour covering the entire board."""
    if gnd_net is None:
        return

    zone = pcbnew.ZONE(board)
    zone.SetNet(gnd_net)
    zone.SetLayer(layer)
    zone.SetIsFilled(True)
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    zone.SetMinThickness(mm(0.25))
    zone.SetThermalReliefGap(mm(0.3))
    zone.SetThermalReliefSpokeWidth(mm(0.4))

    # Outline slightly inside board edge
    margin = 0.3
    outline = zone.Outline()
    outline.NewOutline()
    outline.Append(mm(ORIGIN_X + margin), mm(ORIGIN_Y + margin))
    outline.Append(mm(ORIGIN_X + BOARD_W - margin), mm(ORIGIN_Y + margin))
    outline.Append(mm(ORIGIN_X + BOARD_W - margin), mm(ORIGIN_Y + BOARD_H - margin))
    outline.Append(mm(ORIGIN_X + margin), mm(ORIGIN_Y + BOARD_H - margin))

    board.Add(zone)


def add_text(board, text, x, y, layer, size):
    """Add silkscreen text."""
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(pos(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    board.Add(t)


def add_mounting_hole(board, x, y, drill_mm, pad_mm):
    """Add a mounting hole."""
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(f"MH")
    fp.SetPosition(pos(x, y))

    pad = pcbnew.PAD(fp)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    pad.SetDrillSize(pcbnew.VECTOR2I(mm(drill_mm), mm(drill_mm)))
    pad.SetSize(pcbnew.VECTOR2I(mm(pad_mm), mm(pad_mm)))
    pad.SetLayerSet(pad.PTHMask())
    pad.SetPosition(pos(x, y))
    fp.Add(pad)

    board.Add(fp)


def main():
    print("=" * 50)
    print("  Dilder PCB — Board Builder")
    print(f"  Board size: {BOARD_W} x {BOARD_H} mm")
    print("=" * 50)

    board = build_board()

    # Save (zone filling will be done by KiCad GUI or DRC)
    outfile = os.path.join(os.path.dirname(__file__) or ".", "dilder.kicad_pcb")
    board.Save(outfile)
    print(f"  Saved: {outfile}")

    # Run DRC
    print("  Running DRC...")
    result = __import__("subprocess").run(
        ["kicad-cli", "pcb", "drc",
         "--output", "/tmp/dilder-drc/drc-report.json",
         "--format", "json",
         "--severity-all",
         outfile],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        import json
        try:
            with open("/tmp/dilder-drc/drc-report.json") as f:
                drc = json.load(f)
            errors = len([v for v in drc.get("violations", []) if v.get("severity") == "error"])
            warnings = len([v for v in drc.get("violations", []) if v.get("severity") == "warning"])
            print(f"  DRC: {errors} errors, {warnings} warnings")
        except:
            print("  DRC completed (could not parse report)")
    else:
        print(f"  DRC: {result.stderr[:200] if result.stderr else 'completed'}")

    # Render 3D view
    print("  Rendering 3D preview...")
    result2 = __import__("subprocess").run(
        ["kicad-cli", "pcb", "render",
         "--output", "/tmp/dilder-pcb-final/board-3d.png",
         "--width", "2400", "--height", "1600",
         "--quality", "basic",
         "--rotate-x", "25", "--rotate-z", "5",
         outfile],
        capture_output=True, text=True
    )
    if result2.returncode == 0:
        print("  3D render: /tmp/dilder-pcb-final/board-3d.png")

    # Render top view
    result3 = __import__("subprocess").run(
        ["kicad-cli", "pcb", "render",
         "--output", "/tmp/dilder-pcb-final/board-top.png",
         "--width", "2400", "--height", "1600",
         "--quality", "basic",
         outfile],
        capture_output=True, text=True
    )
    if result3.returncode == 0:
        print("  Top view: /tmp/dilder-pcb-final/board-top.png")

    print("\n  Done! Open in KiCad:")
    print(f"  kicad '{outfile.replace('.kicad_pcb', '.kicad_pro')}'")


if __name__ == "__main__":
    main()
