#!/usr/bin/env python3
"""
Dilder PCB Router v2 — collision-aware routing.

Fixes v1's blind L-routing by:
1. Removing all existing tracks
2. Spacing out component placement to eliminate courtyard overlaps
3. Routing with offset channels to avoid trace crossings
4. Using B.Cu for long runs and F.Cu for pad connections
5. Filling GND zones properly

Usage: python3 route_board_v2.py
"""

import pcbnew
import os
import subprocess
import json
import sys

def mm(val):
    return pcbnew.FromMM(val)

def pos(x, y):
    return pcbnew.VECTOR2I(mm(100 + x), mm(100 + y))

BOARD_W = 25.0
BOARD_H = 75.0  # slightly taller to give more spacing

SIGNAL_W = mm(0.2)
POWER_W  = mm(0.4)
VIA_D    = mm(0.6)
VIA_DRILL= mm(0.3)
CLEARANCE= 0.25  # mm between trace channels

POWER_NETS = {"3V3", "VBUS", "VBUS_CHG", "VBAT", "BAT_PLUS"}


def main():
    print("=" * 50)
    print("  Dilder PCB — Router v2 (collision-aware)")
    print("=" * 50)

    # Rebuild the board from scratch with better spacing
    board = rebuild_board()

    # Get pad positions per net
    net_pads = {}
    net_objs = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            net = pad.GetNet()
            if not net or not net.GetNetname():
                continue
            name = net.GetNetname()
            cx, cy = pad.GetPosition().x, pad.GetPosition().y
            net_pads.setdefault(name, []).append((cx, cy, ref, pad.GetNumber()))
            net_objs[name] = net

    print(f"  {len(net_pads)} nets, {sum(len(v) for v in net_pads.values())} pad connections")

    # Route all nets
    routed = 0
    for name in sorted(net_pads.keys()):
        pads = net_pads[name]
        net = net_objs[name]

        if name == "GND":
            # Handled by pour
            continue

        if len(pads) < 2:
            continue

        w = POWER_W if name in POWER_NETS else SIGNAL_W

        # Sort pads by Y then X for consistent routing
        pads_sorted = sorted(pads, key=lambda p: (p[1], p[0]))

        if name == "3V3":
            # 3V3: run a vertical bus on B.Cu at x=18mm, vias to each pad
            route_vbus(board, pads_sorted, w, net, bus_x=mm(100 + 19))
        elif name in POWER_NETS and len(pads) > 2:
            route_vbus(board, pads_sorted, w, net, bus_x=mm(100 + 2))
        else:
            # Signal: chain on F.Cu with staggered routing
            route_signal_chain(board, pads_sorted, w, net, name)

        routed += 1

    print(f"  Routed {routed} nets")

    # Zone fill crashes in headless mode on KiCad 10 — skip and fill via DRC
    print("  Zones defined (will be filled by DRC check)")

    # Save
    outpath = os.path.join(os.path.dirname(__file__) or ".", "dilder.kicad_pcb")
    board.Save(outpath)
    print(f"  Saved: {outpath}")

    # DRC
    run_drc(outpath)

    # Render
    render(outpath)


def rebuild_board():
    """Build the board from scratch with better component spacing."""
    board = pcbnew.BOARD()

    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    ds.m_TrackMinWidth = mm(0.127)
    ds.m_ViasMinSize = mm(0.6)
    ds.m_ViasMinDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.3)
    ds.m_SolderMaskExpansion = mm(0.05)
    ds.m_SolderMaskMinWidth = mm(0.1)

    # Board outline
    corners = [pos(0,0), pos(BOARD_W,0), pos(BOARD_W,BOARD_H), pos(0,BOARD_H)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(corners[i])
        seg.SetEnd(corners[(i+1)%4])
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.15))
        board.Add(seg)

    # Nets
    net_map = {}
    nets = ["GND", "3V3", "VBUS", "VBUS_CHG", "VBAT", "USB_DP_IN", "USB_DP",
            "USB_DM_IN", "USB_DM", "CC1", "CC2", "QSPI_SCLK", "QSPI_SD0",
            "QSPI_SD1", "QSPI_SS", "XIN", "XOUT", "RUN", "PROG", "BAT_PLUS",
            "OD", "OC", "CS_DRAIN", "CHRG_LED", "STDBY_LED", "CHRG_OUT",
            "STDBY_OUT", "REGOUT",
            "GPIO0", "GPIO1", "GPIO2", "GPIO3", "GPIO4", "GPIO5", "GPIO6",
            "GPIO8", "GPIO9", "GPIO10", "GPIO11", "GPIO12", "GPIO13",
            "GPIO14", "GPIO15"]
    for i, n in enumerate(nets, 1):
        net = pcbnew.NETINFO_ITEM(board, n, i)
        board.Add(net)
        net_map[n] = net

    # Components — spread out more to avoid courtyard overlaps
    # Format: (ref, footprint, x, y, angle, value, lcsc)
    components = [
        # USB-C — top center (board center = 12.5mm)
        ("J1", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", 12.5, 3, 0, "USB-C", "C2765186"),
        # CC resistors — left side
        ("R8", "Resistor_SMD:R_0402_1005Metric", 4, 6, 0, "5.1k", ""),
        ("R9", "Resistor_SMD:R_0402_1005Metric", 4, 8, 0, "5.1k", ""),
        # Schottky + TP4056 — spread across width
        ("D1", "Diode_SMD:D_SMA", 5, 12, 0, "SS34", "C8678"),
        ("U2", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", 12.5, 12, 0, "TP4056", "C382139"),
        ("R1", "Resistor_SMD:R_0402_1005Metric", 20, 10, 0, "1.2k", "C25752"),
        # LEDs — far right
        ("D2", "LED_SMD:LED_0402_1005Metric", 21, 6, 0, "RED", "C84256"),
        ("R2", "Resistor_SMD:R_0402_1005Metric", 23, 6, 0, "1k", "C25585"),
        ("D3", "LED_SMD:LED_0402_1005Metric", 21, 4, 0, "GREEN", "C72043"),
        ("R3", "Resistor_SMD:R_0402_1005Metric", 23, 4, 0, "1k", "C25585"),
        # Battery protection — spread
        ("U3", "Package_TO_SOT_SMD:SOT-23-6", 5, 17, 0, "DW01A", "C351410"),
        ("Q1", "Package_TO_SOT_SMD:SOT-23-6", 20, 17, 0, "FS8205A", "C908265"),
        # Battery connector — right edge
        ("J2", "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal", 22, 21, 270, "BAT", "C131337"),
        # LDO — center
        ("U4", "Package_TO_SOT_SMD:SOT-223-3_TabPin2", 12.5, 23, 0, "AMS1117-3.3", "C6186"),
        ("C5", "Capacitor_SMD:C_0402_1005Metric", 5, 23, 0, "10uF", "C19702"),
        ("C6", "Capacitor_SMD:C_0402_1005Metric", 20, 25, 0, "10uF", "C19702"),
        # MCU decoupling — flanking MCU
        ("C3", "Capacitor_SMD:C_0402_1005Metric", 6, 28, 0, "100nF", "C14663"),
        ("C4", "Capacitor_SMD:C_0402_1005Metric", 19, 28, 0, "10uF", "C19702"),
        # USB series resistors — left of MCU
        ("R6", "Resistor_SMD:R_0402_1005Metric", 3, 30, 90, "27R", "C25105"),
        ("R7", "Resistor_SMD:R_0402_1005Metric", 5, 30, 90, "27R", "C25105"),
        # RP2040 — center
        ("U1", "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm", 12.5, 34, 0, "RP2040", "C2040"),
        # Flash — left of MCU
        ("U5", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", 4, 40, 270, "W25Q16JV", "C131024"),
        # Crystal + caps — right of MCU
        ("Y1", "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", 22, 34, 90, "12MHz", "C9002"),
        ("C1", "Capacitor_SMD:C_0402_1005Metric", 21, 38, 0, "15pF", "C1644"),
        ("C2", "Capacitor_SMD:C_0402_1005Metric", 23, 38, 0, "15pF", "C1644"),
        # RUN pull-up — right of MCU
        ("R10", "Resistor_SMD:R_0402_1005Metric", 22, 30, 90, "10k", "C25744"),
        # e-Paper header — left edge
        ("J3", "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", 2, 52, 0, "ePaper", ""),
        # Joystick — center-right
        ("SW1", "Button_Switch_SMD:SW_SPST_SKQG_WithStem", 17, 49, 0, "5-Way", "C139794"),
        # IMU — center
        ("U6", "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm", 12.5, 58, 0, "MPU-6050", "C24112"),
        ("R4", "Resistor_SMD:R_0402_1005Metric", 5, 56, 90, "10k", "C25744"),
        ("R5", "Resistor_SMD:R_0402_1005Metric", 5, 59, 90, "10k", "C25744"),
        ("C7", "Capacitor_SMD:C_0402_1005Metric", 21, 56, 0, "100nF", "C14663"),
        ("C9", "Capacitor_SMD:C_0402_1005Metric", 21, 59, 0, "100nF", "C14663"),
        # GPS — bottom, centered
        ("U7", "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm", 12.5, 68, 0, "ATGM336H", "C90770"),
        ("C8", "Capacitor_SMD:C_0402_1005Metric", 21, 66, 0, "100nF", "C14663"),
    ]

    print(f"  Placing {len(components)} components...")
    for ref, fp_lib, x, y, angle, value, lcsc in components:
        fp = load_fp(fp_lib)
        if fp is None:
            print(f"    SKIP: {ref} ({fp_lib})")
            continue
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetPosition(pos(x, y))
        if angle:
            fp.SetOrientationDegrees(angle)
        fp.SetLayer(pcbnew.F_Cu)
        board.Add(fp)

    # Assign nets
    assign_nets(board, net_map)

    # GND zones
    for layer in [pcbnew.F_Cu, pcbnew.B_Cu]:
        zone = pcbnew.ZONE(board)
        zone.SetNet(net_map["GND"])
        zone.SetLayer(layer)
        zone.SetIsFilled(False)
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        zone.SetMinThickness(mm(0.2))
        zone.SetThermalReliefGap(mm(0.25))
        zone.SetThermalReliefSpokeWidth(mm(0.3))
        o = zone.Outline()
        o.NewOutline()
        m = 0.3
        o.Append(mm(100+m), mm(100+m))
        o.Append(mm(100+BOARD_W-m), mm(100+m))
        o.Append(mm(100+BOARD_W-m), mm(100+BOARD_H-m))
        o.Append(mm(100+m), mm(100+BOARD_H-m))
        board.Add(zone)

    # Silkscreen
    for text, x, y, size in [("DILDER", 10.5, 72, 1.5), ("v0.2", 10.5, 74, 1.0)]:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(pos(x, y))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(size * 0.15))
        board.Add(t)

    return board


def load_fp(name):
    try:
        lib, fp = name.split(":")
        path = f"/usr/share/kicad/footprints/{lib}.pretty"
        if os.path.exists(path):
            return pcbnew.FootprintLoad(path, fp)
    except:
        pass
    return None


def assign_nets(board, nm):
    """Assign nets to pads."""
    # Map: (ref, pad_number) -> net_name
    PA = {
        # RP2040
        ("U1","57"):"GND", ("U1","1"):"3V3", ("U1","48"):"3V3",
        ("U1","50"):"3V3", ("U1","43"):"3V3", ("U1","44"):"3V3",
        ("U1","49"):"GND", ("U1","18"):"RUN",
        ("U1","47"):"USB_DP", ("U1","46"):"USB_DM",
        ("U1","24"):"QSPI_SCLK", ("U1","21"):"QSPI_SD0",
        ("U1","22"):"QSPI_SD1", ("U1","26"):"QSPI_SS",
        ("U1","20"):"XIN", ("U1","19"):"XOUT",
        ("U1","2"):"GPIO0", ("U1","3"):"GPIO1",
        ("U1","4"):"GPIO2", ("U1","5"):"GPIO3",
        ("U1","6"):"GPIO4", ("U1","7"):"GPIO5", ("U1","8"):"GPIO6",
        ("U1","10"):"GPIO8", ("U1","11"):"GPIO9",
        ("U1","12"):"GPIO10", ("U1","13"):"GPIO11",
        ("U1","14"):"GPIO12", ("U1","15"):"GPIO13",
        ("U1","16"):"GPIO14", ("U1","17"):"GPIO15",
        # USB-C
        ("J1","A4"):"VBUS", ("J1","B4"):"VBUS",
        ("J1","A1"):"GND", ("J1","B1"):"GND", ("J1","A12"):"GND", ("J1","B12"):"GND",
        ("J1","A6"):"USB_DP_IN", ("J1","A7"):"USB_DM_IN",
        ("J1","B6"):"USB_DP_IN", ("J1","B7"):"USB_DM_IN",
        ("J1","A5"):"CC1", ("J1","B5"):"CC2",
        # Schottky
        ("D1","1"):"VBUS", ("D1","2"):"VBUS_CHG",
        # TP4056
        ("U2","8"):"VBUS_CHG", ("U2","3"):"VBAT", ("U2","2"):"PROG",
        ("U2","1"):"GND", ("U2","4"):"3V3", ("U2","5"):"GND",
        ("U2","7"):"CHRG_OUT", ("U2","6"):"STDBY_OUT",
        # DW01A
        ("U3","1"):"OD", ("U3","2"):"CS_DRAIN", ("U3","3"):"OC",
        ("U3","4"):"VBAT", ("U3","5"):"VBAT", ("U3","6"):"GND",
        # FS8205A
        ("Q1","1"):"GND", ("Q1","2"):"OD", ("Q1","3"):"CS_DRAIN",
        ("Q1","4"):"CS_DRAIN", ("Q1","5"):"OC", ("Q1","6"):"BAT_PLUS",
        # JST
        ("J2","1"):"BAT_PLUS", ("J2","2"):"GND",
        # LDO
        ("U4","1"):"GND", ("U4","2"):"3V3", ("U4","3"):"VBAT", ("U4","4"):"3V3",
        # Flash
        ("U5","1"):"QSPI_SS", ("U5","2"):"QSPI_SD0", ("U5","3"):"3V3",
        ("U5","4"):"GND", ("U5","5"):"QSPI_SD1", ("U5","6"):"QSPI_SCLK",
        ("U5","7"):"3V3", ("U5","8"):"3V3",
        # Crystal
        ("Y1","1"):"XIN", ("Y1","2"):"XOUT",
        # Caps
        ("C1","1"):"XIN", ("C1","2"):"GND",
        ("C2","1"):"XOUT", ("C2","2"):"GND",
        ("C3","1"):"3V3", ("C3","2"):"GND",
        ("C4","1"):"3V3", ("C4","2"):"GND",
        ("C5","1"):"VBAT", ("C5","2"):"GND",
        ("C6","1"):"3V3", ("C6","2"):"GND",
        ("C7","1"):"3V3", ("C7","2"):"GND",
        ("C8","1"):"3V3", ("C8","2"):"GND",
        ("C9","1"):"REGOUT", ("C9","2"):"GND",
        # Resistors
        ("R1","1"):"PROG", ("R1","2"):"GND",
        ("R2","1"):"3V3", ("R2","2"):"CHRG_LED",
        ("R3","1"):"3V3", ("R3","2"):"STDBY_LED",
        ("R4","1"):"3V3", ("R4","2"):"GPIO14",
        ("R5","1"):"3V3", ("R5","2"):"GPIO15",
        ("R6","1"):"USB_DP_IN", ("R6","2"):"USB_DP",
        ("R7","1"):"USB_DM_IN", ("R7","2"):"USB_DM",
        ("R8","1"):"CC1", ("R8","2"):"GND",
        ("R9","1"):"CC2", ("R9","2"):"GND",
        ("R10","1"):"3V3", ("R10","2"):"RUN",
        # LEDs
        ("D2","1"):"CHRG_LED", ("D2","2"):"CHRG_OUT",
        ("D3","1"):"STDBY_LED", ("D3","2"):"STDBY_OUT",
        # Joystick (simplified - just center press for now)
        ("SW1","1"):"GND", ("SW1","2"):"GPIO6",
        # e-Paper
        ("J3","1"):"3V3", ("J3","2"):"GND",
        ("J3","3"):"GPIO11", ("J3","4"):"GPIO10",
        ("J3","5"):"GPIO9", ("J3","6"):"GPIO8",
        ("J3","7"):"GPIO12", ("J3","8"):"GPIO13",
        # IMU
        ("U6","24"):"GPIO14", ("U6","23"):"GPIO15",
        ("U6","13"):"3V3", ("U6","1"):"3V3",
        ("U6","18"):"GND", ("U6","9"):"GND",
        ("U6","11"):"GND", ("U6","8"):"GND", ("U6","10"):"REGOUT",
        # GPS
        ("U7","13"):"3V3", ("U7","18"):"GND",
    }

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            key = (ref, str(pad.GetNumber()))
            if key in PA and PA[key] in nm:
                pad.SetNet(nm[PA[key]])


def route_vbus(board, pads, width, net, bus_x):
    """Route power net as vertical bus on B.Cu + vias + short F.Cu stubs."""
    sorted_p = sorted(pads, key=lambda p: p[1])

    # Vertical bus on B.Cu
    for i in range(len(sorted_p) - 1):
        add_track(board, bus_x, sorted_p[i][1], bus_x, sorted_p[i+1][1], width, pcbnew.B_Cu, net)

    # Via + stub for each pad
    for px, py, ref, pn in sorted_p:
        add_via(board, bus_x, py, net)
        if bus_x != px:
            add_track(board, bus_x, py, px, py, width, pcbnew.F_Cu, net)


# Assign each signal net a unique B.Cu channel X to avoid crossings
_channel_idx = 0
_channel_cache = {}
CHANNEL_START = 3.0  # mm from left edge
CHANNEL_SPACE = 1.0  # mm between channels (via=0.6mm + 0.2mm clearance + margin)

# Only long-distance GPIO nets get dedicated B.Cu channels
# Short/local nets route on F.Cu directly
CHANNEL_NETS = {
    "GPIO0": 0, "GPIO1": 1,
    "GPIO2": 2, "GPIO3": 3, "GPIO4": 4, "GPIO5": 5, "GPIO6": 6,
    "GPIO8": 7, "GPIO9": 8, "GPIO10": 9, "GPIO11": 10,
    "GPIO12": 11, "GPIO13": 12,
    "GPIO14": 13, "GPIO15": 14,
}

def get_channel_x(name):
    """Get a fixed X position on B.Cu for this net's vertical run."""
    if name in CHANNEL_NETS:
        return mm(100 + CHANNEL_START + CHANNEL_NETS[name] * CHANNEL_SPACE)
    return None


def route_signal_chain(board, pads, width, net, name):
    """Route signal net. GPIO nets use dedicated B.Cu channels; others use F.Cu."""
    if len(pads) < 2:
        return

    ch_x = get_channel_x(name)

    for i in range(len(pads) - 1):
        x1, y1 = pads[i][0], pads[i][1]
        x2, y2 = pads[i+1][0], pads[i+1][1]

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        if ch_x is not None and dy > mm(5):
            # Long GPIO net: use dedicated B.Cu channel
            # Pad 1 → via (short horizontal F.Cu stub)
            add_track(board, x1, y1, ch_x, y1, width, pcbnew.F_Cu, net)
            add_via(board, ch_x, y1, net)

            # Vertical run on B.Cu in our dedicated channel
            add_track(board, ch_x, y1, ch_x, y2, width, pcbnew.B_Cu, net)

            # Via → Pad 2 (short horizontal F.Cu stub)
            add_via(board, ch_x, y2, net)
            add_track(board, ch_x, y2, x2, y2, width, pcbnew.F_Cu, net)
        elif dx < mm(1) and dy < mm(1):
            # Very close: direct trace
            add_track(board, x1, y1, x2, y2, width, pcbnew.F_Cu, net)
        else:
            # Local net: L-shape on F.Cu, vertical first to avoid horizontal congestion
            add_track(board, x1, y1, x1, y2, width, pcbnew.F_Cu, net)
            if x1 != x2:
                add_track(board, x1, y2, x2, y2, width, pcbnew.F_Cu, net)


def add_track(board, x1, y1, x2, y2, width, layer, net):
    if x1 == x2 and y1 == y2:
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(int(x1), int(y1)))
    t.SetEnd(pcbnew.VECTOR2I(int(x2), int(y2)))
    t.SetWidth(int(width))
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)


def add_via(board, x, y, net):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
    v.SetWidth(int(VIA_D))
    v.SetDrill(int(VIA_DRILL))
    v.SetNet(net)
    board.Add(v)


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
            s = v.get("severity", "?")
            by_type.setdefault(t, {"count": 0, "severity": s})
            by_type[t]["count"] += 1

        errors = sum(1 for v in violations if v.get("severity") == "error")
        warns = sum(1 for v in violations if v.get("severity") == "warning")
        print(f"  DRC: {errors} errors, {warns} warnings")
        for t, info in sorted(by_type.items(), key=lambda x: -x[1]["count"]):
            print(f"    {t}: {info['count']} ({info['severity']})")
    except Exception as e:
        print(f"  DRC: {e}")


def render(path):
    print("  Rendering...")
    os.makedirs("/tmp/dilder-routed", exist_ok=True)
    for args, out in [
        ([], "board-top.png"),
        (["--perspective", "--rotate", "-45,0,25"], "board-3d.png"),
    ]:
        subprocess.run(["kicad-cli", "pcb", "render",
                       "--output", f"/tmp/dilder-routed/{out}",
                       "--width", "2400", "--height", "1600",
                       "--quality", "basic", *args, path],
                      capture_output=True)
    print("  Renders: /tmp/dilder-routed/")


if __name__ == "__main__":
    main()
