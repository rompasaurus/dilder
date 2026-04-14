#!/usr/bin/env python3
"""
Dilder PCB v6 — 4-layer, 24-pin FPC for Waveshare e-Paper, optimized layout.

Board: 48mm x 85mm, 4-layer
Display: 24-pin 0.5mm FPC (Hirose FH12-24S) for Waveshare 2.13" e-Paper HAT V4
Joystick: centered above USB-C at bottom
ESP32-S3: top, antenna up

4-layer stackup: F.Cu / In1.Cu / In2.Cu / B.Cu
"""

import pcbnew, os, subprocess, json, sys

def mm(v): return pcbnew.FromMM(v)
def pos(x, y): return pcbnew.VECTOR2I(mm(100+x), mm(100+y))

BOARD_W = 48.0
BOARD_H = 85.0
BOARD_FILE = os.path.join(os.path.dirname(__file__) or ".", "dilder.kicad_pcb")
CX = BOARD_W / 2  # 24mm center

# ESP32 module pins exit LEFT (x~15.25) and BOTTOM (y~30.5) when placed at (CX, 18)
# Place peripherals on those sides

COMPONENTS = [
    # ═══ ESP32-S3 — top center, antenna up ═══
    ("U1", "RF_Module:ESP32-S3-WROOM-1", CX, 18, 0, "ESP32-S3-N16R8", "C2913196"),
    ("R10", "Resistor_SMD:R_0402_1005Metric", 6, 16, 0, "10k", "C25744"),   # EN pull-up
    ("C3", "Capacitor_SMD:R_0402_1005Metric", 6, 13, 0, "100nF", "C14663"), # decoupling
    ("C4", "Capacitor_SMD:R_0402_1005Metric", 6, 11, 0, "10uF", "C19702"),

    # ═══ 24-pin FPC connector — below module, for Waveshare e-Paper ribbon ═══
    # Hirose FH12-24S: 44.2mm wide, placed horizontally across board
    ("J3", "Connector_FFC-FPC:Hirose_FH12-24S-0.5SH_1x24-1MP_P0.50mm_Horizontal",
                                              CX, 38, 0, "ePaper-FPC", ""),

    # ═══ IMU — left side, near I2C pins (LEFT side of ESP32) ═══
    ("U6", "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm",
                                              8, 27, 0, "MPU-6050", "C24112"),
    ("R4", "Resistor_SMD:R_0402_1005Metric",  3, 25, 90, "10k", "C25744"),
    ("R5", "Resistor_SMD:R_0402_1005Metric",  3, 29, 90, "10k", "C25744"),
    ("C7", "Capacitor_SMD:C_0402_1005Metric", 14, 25, 0, "100nF", "C14663"),
    ("C9", "Capacitor_SMD:C_0402_1005Metric", 14, 29, 0, "100nF", "C14663"),

    # ═══ POWER — middle zone ═══
    ("U4", "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
                                              CX, 50, 0, "AMS1117-3.3", "C6186"),
    ("C5", "Capacitor_SMD:C_0402_1005Metric", 12, 50, 0, "10uF", "C19702"),
    ("C6", "Capacitor_SMD:C_0402_1005Metric", 36, 50, 0, "10uF", "C19702"),

    ("U2", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
                                              CX, 57, 0, "TP4056", "C382139"),
    ("R1", "Resistor_SMD:R_0402_1005Metric", 36, 55, 0, "1.2k", "C25752"),
    ("D1", "Diode_SMD:D_SMA",                12, 57, 0, "SS34", "C8678"),

    ("U3", "Package_TO_SOT_SMD:SOT-23-6",     8, 63, 0, "DW01A", "C351410"),
    ("Q1", "Package_TO_SOT_SMD:SOT-23-6",    36, 63, 0, "FS8205A", "C908265"),
    ("J2", "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
                                              42, 55, 270, "BAT", "C131337"),

    # LEDs — right side of power section
    ("D2", "LED_SMD:LED_0402_1005Metric", 40, 48, 0, "RED", "C84256"),
    ("R2", "Resistor_SMD:R_0402_1005Metric", 44, 48, 0, "1k", "C25585"),
    ("D3", "LED_SMD:LED_0402_1005Metric", 40, 45, 0, "GREEN", "C72043"),
    ("R3", "Resistor_SMD:R_0402_1005Metric", 44, 45, 0, "1k", "C25585"),

    # ═══ USB CC resistors — near USB-C ═══
    ("R8", "Resistor_SMD:R_0402_1005Metric", 16, 74, 0, "5.1k", ""),
    ("R9", "Resistor_SMD:R_0402_1005Metric", 16, 76, 0, "5.1k", ""),

    # ═══ BOTTOM — joystick centered, USB-C centered below ═══
    ("SW1", "Button_Switch_SMD:SW_SPST_SKQG_WithStem", CX, 72, 0, "5-Way", "C139794"),
    ("J1", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
                                              CX, 82, 180, "USB-C", "C2765186"),
]

PA = {
    ("U1","1"):"GND", ("U1","2"):"3V3", ("U1","3"):"EN",
    ("U1","4"):"JOY_UP", ("U1","5"):"JOY_DOWN",
    ("U1","6"):"JOY_LEFT", ("U1","7"):"JOY_RIGHT",
    ("U1","8"):"JOY_CENTER",
    ("U1","9"):"I2C_SDA", ("U1","10"):"I2C_SCL",
    ("U1","13"):"USB_DM", ("U1","14"):"USB_DP",
    # Bottom pins — SPI to e-Paper (directly to FPC below)
    ("U1","15"):"EPD_CLK", ("U1","16"):"EPD_MOSI",
    ("U1","17"):"EPD_DC", ("U1","18"):"EPD_RST",
    ("U1","19"):"EPD_CS", ("U1","20"):"EPD_BUSY",
    ("U1","31"):"GND", ("U1","32"):"GND",
    ("U1","40"):"GND", ("U1","41"):"GND",
    # USB-C
    ("J1","A4"):"VBUS", ("J1","B4"):"VBUS",
    ("J1","A1"):"GND", ("J1","B1"):"GND",
    ("J1","A12"):"GND", ("J1","B12"):"GND",
    ("J1","A6"):"USB_DP", ("J1","A7"):"USB_DM",
    ("J1","B6"):"USB_DP", ("J1","B7"):"USB_DM",
    ("J1","A5"):"CC1", ("J1","B5"):"CC2",
    # Power chain
    ("D1","1"):"VBUS", ("D1","2"):"VBUS_CHG",
    ("U2","8"):"VBUS_CHG", ("U2","3"):"VBAT", ("U2","2"):"PROG",
    ("U2","1"):"GND", ("U2","4"):"3V3", ("U2","5"):"GND",
    ("U2","7"):"CHRG_OUT", ("U2","6"):"STDBY_OUT",
    ("U3","1"):"OD", ("U3","2"):"CS_DRAIN", ("U3","3"):"OC",
    ("U3","4"):"VBAT", ("U3","5"):"VBAT", ("U3","6"):"GND",
    ("Q1","1"):"GND", ("Q1","2"):"OD", ("Q1","3"):"CS_DRAIN",
    ("Q1","4"):"CS_DRAIN", ("Q1","5"):"OC", ("Q1","6"):"BAT_PLUS",
    ("J2","1"):"BAT_PLUS", ("J2","2"):"GND",
    ("U4","1"):"GND", ("U4","2"):"3V3", ("U4","3"):"VBAT", ("U4","4"):"3V3",
    # Caps
    ("C3","1"):"3V3", ("C3","2"):"GND",
    ("C4","1"):"3V3", ("C4","2"):"GND",
    ("C5","1"):"VBAT", ("C5","2"):"GND",
    ("C6","1"):"3V3", ("C6","2"):"GND",
    ("C7","1"):"3V3", ("C7","2"):"GND",
    ("C9","1"):"REGOUT", ("C9","2"):"GND",
    # Resistors
    ("R1","1"):"PROG", ("R1","2"):"GND",
    ("R2","1"):"3V3", ("R2","2"):"CHRG_LED",
    ("R3","1"):"3V3", ("R3","2"):"STDBY_LED",
    ("R4","1"):"3V3", ("R4","2"):"I2C_SDA",
    ("R5","1"):"3V3", ("R5","2"):"I2C_SCL",
    ("R8","1"):"CC1", ("R8","2"):"GND",
    ("R9","1"):"CC2", ("R9","2"):"GND",
    ("R10","1"):"3V3", ("R10","2"):"EN",
    # LEDs
    ("D2","1"):"CHRG_LED", ("D2","2"):"CHRG_OUT",
    ("D3","1"):"STDBY_LED", ("D3","2"):"STDBY_OUT",
    # Joystick
    ("SW1","1"):"GND", ("SW1","2"):"JOY_CENTER",
    # FPC 24-pin — only pins 1-8 used for SPI, rest NC
    # Waveshare pinout: 1=VCC, 2=GND, 3=DIN, 4=CLK, 5=CS, 6=DC, 7=RST, 8=BUSY
    ("J3","1"):"3V3", ("J3","2"):"GND",
    ("J3","3"):"EPD_MOSI", ("J3","4"):"EPD_CLK",
    ("J3","5"):"EPD_CS", ("J3","6"):"EPD_DC",
    ("J3","7"):"EPD_RST", ("J3","8"):"EPD_BUSY",
    # IMU
    ("U6","24"):"I2C_SDA", ("U6","23"):"I2C_SCL",
    ("U6","13"):"3V3", ("U6","1"):"3V3",
    ("U6","18"):"GND", ("U6","9"):"GND",
    ("U6","11"):"GND", ("U6","8"):"GND", ("U6","10"):"REGOUT",
}

ALL_NETS = sorted(set(v for v in PA.values() if v))

def main():
    print("=" * 55)
    print(f"  Dilder v6 — 4-layer {BOARD_W}x{BOARD_H}mm")
    print(f"  24-pin FPC, joystick+USB centered bottom")
    print("=" * 55)

    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_ViasMinSize = mm(0.6)
    ds.m_ViasMinDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.3)
    board.SetCopperLayerCount(4)

    # Board outline
    pts = [(0,0),(BOARD_W,0),(BOARD_W,BOARD_H),(0,BOARD_H)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pos(*pts[i])); seg.SetEnd(pos(*pts[(i+1)%4]))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(mm(0.15))
        board.Add(seg)

    # Nets
    nm = {}
    for i, n in enumerate(ALL_NETS, 1):
        net = pcbnew.NETINFO_ITEM(board, n, i)
        board.Add(net); nm[n] = net

    # Place components
    placed = 0
    for ref, fp_lib, x, y, angle, value, lcsc in COMPONENTS:
        lib, name = fp_lib.split(":")
        path = f"/usr/share/kicad/footprints/{lib}.pretty"
        fp = pcbnew.FootprintLoad(path, name) if os.path.exists(path) else None
        if not fp:
            print(f"  SKIP {ref} ({fp_lib})"); continue
        fp.SetReference(ref); fp.SetValue(value)
        fp.SetPosition(pos(x, y))
        if angle: fp.SetOrientationDegrees(angle)
        fp.SetLayer(pcbnew.F_Cu)
        board.Add(fp); placed += 1
    print(f"  Placed {placed}/{len(COMPONENTS)} components")

    # Assign nets
    assigned = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            key = (ref, str(pad.GetNumber()))
            if key in PA and PA[key] in nm:
                pad.SetNet(nm[PA[key]])
                assigned += 1
    print(f"  Assigned {assigned} pad-net connections")

    # GND zones on F.Cu and B.Cu
    for layer in [pcbnew.F_Cu, pcbnew.B_Cu]:
        zone = pcbnew.ZONE(board)
        zone.SetNet(nm["GND"]); zone.SetLayer(layer)
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        zone.SetMinThickness(mm(0.2))
        zone.SetThermalReliefGap(mm(0.3))
        zone.SetThermalReliefSpokeWidth(mm(0.4))
        o = zone.Outline(); o.NewOutline()
        m = 0.3
        o.Append(mm(100+m), mm(100+m))
        o.Append(mm(100+BOARD_W-m), mm(100+m))
        o.Append(mm(100+BOARD_W-m), mm(100+BOARD_H-m))
        o.Append(mm(100+m), mm(100+BOARD_H-m))
        board.Add(zone)

    # Silkscreen
    for txt, x, y, sz in [("DILDER", CX, 83, 1.2), ("v0.6", CX+8, 83, 0.8)]:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt); t.SetPosition(pos(x, y)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(sz), mm(sz)))
        t.SetTextThickness(mm(sz * 0.15))
        board.Add(t)

    # Save
    board.Save(BOARD_FILE)
    print(f"  Saved: {BOARD_FILE}")

    # Export DSN
    pcbnew.ExportSpecctraDSN(board, '/tmp/freerouting/dilder_v6.dsn')
    print("  Exported DSN for FreeRouting")

    # Run FreeRouting
    print("  Running FreeRouting (500 passes, 4 layers)...")
    r = subprocess.run([
        "/tmp/freerouting/freerouting-2.1.0-linux-x64/bin/freerouting",
        "-de", "/tmp/freerouting/dilder_v6.dsn",
        "-do", "/tmp/freerouting/dilder_v6.ses",
        "-mp", "500", "-mt", "1"
    ], capture_output=True, text=True, timeout=600)

    # Show routing result
    for line in (r.stdout + r.stderr).split('\n'):
        if any(k in line for k in ['Auto-routing was', 'Optimization was', 'unrouted']):
            part = line.split('INFO')[-1].strip() if 'INFO' in line else line.strip()
            print(f"  {part}")

    # Import SES
    print("  Importing routed result...")
    board2 = pcbnew.LoadBoard(BOARD_FILE)
    try:
        result = pcbnew.ImportSpecctraSES(board2, '/tmp/freerouting/dilder_v6.ses')
        board2.Save(BOARD_FILE)
        tracks = sum(1 for t in board2.GetTracks() if t.GetClass() == 'PCB_TRACK')
        vias = sum(1 for t in board2.GetTracks() if t.GetClass() == 'PCB_VIA')
        print(f"  Imported: {tracks} tracks, {vias} vias")
    except Exception as e:
        print(f"  Import error: {e}")
        # Try manual SES parsing as fallback
        if os.path.exists('/tmp/freerouting/dilder_v6.ses'):
            with open('/tmp/freerouting/dilder_v6.ses') as f:
                ses_content = f.read()
            wire_count = ses_content.count('(wire')
            via_count = ses_content.count('(via')
            print(f"  SES file contains {wire_count} wires, {via_count} vias")
            if wire_count == 0:
                print("  FreeRouting produced no routes — board may need wider spacing")

    # DRC
    print("  Running DRC...")
    os.makedirs("/tmp/dilder-drc", exist_ok=True)
    subprocess.run(["kicad-cli", "pcb", "drc", "--output", "/tmp/dilder-drc/drc-report.json",
                    "--format", "json", "--severity-all", BOARD_FILE], capture_output=True)
    try:
        with open("/tmp/dilder-drc/drc-report.json") as f:
            drc = json.load(f)
        v = drc.get("violations", [])
        by_type = {}
        for x in v: by_type.setdefault(x["type"], 0); by_type[x["type"]] += 1
        cosmetic = {"solder_mask_bridge","silk_over_copper","silk_overlap","silk_edge_clearance"}
        errors = sum(1 for x in v if x["severity"] == "error")
        warns = sum(1 for x in v if x["severity"] == "warning")
        c = sum(by_type.get(t,0) for t in cosmetic)
        uncon = len(drc.get("unconnected_items", []))
        print(f"  ERRORS: {errors} | WARNS: {warns} | UNCONNECTED: {uncon}")
        print(f"  Routing: {errors-c} | Cosmetic: {c}")
        for t, cnt in sorted(by_type.items(), key=lambda x: -x[1]):
            tag = " *" if t in cosmetic else ""
            print(f"    {t}: {cnt}{tag}")
    except Exception as e:
        print(f"  DRC: {e}")

    # Render
    print("  Rendering...")
    os.makedirs("/tmp/dilder-routed", exist_ok=True)
    for args, out in [
        ([], "board-top.png"),
        (["--perspective", "--rotate", "-35,0,15"], "board-3d.png"),
    ]:
        subprocess.run(["kicad-cli", "pcb", "render", "--output", f"/tmp/dilder-routed/{out}",
                       "--width", "2400", "--height", "1600", "--quality", "basic",
                       *args, BOARD_FILE], capture_output=True)
    print("  Done! Renders: /tmp/dilder-routed/")


if __name__ == "__main__":
    main()
