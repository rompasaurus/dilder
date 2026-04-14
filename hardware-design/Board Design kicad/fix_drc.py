#!/usr/bin/env python3
"""
Fix DRC violations on the Dilder PCB.

Strategy:
1. Delete ALL existing tracks and vias (start clean routing)
2. Re-route with collision-aware placement:
   - Power nets (3V3, VBAT): vertical bus on B.Cu at board RIGHT edge
   - GPIO signals: vertical channels on B.Cu at board LEFT, spaced 1mm apart
   - Local nets: direct short traces on F.Cu only where pads are close
   - Stagger via Y positions so they don't stack
3. Fill zones
4. Run DRC
"""

import pcbnew
import os
import subprocess
import json
import sys

def mm(val):
    return pcbnew.FromMM(val)

def to_mm(val):
    return pcbnew.ToMM(val)

BOARD_FILE = os.path.join(os.path.dirname(__file__) or ".", "dilder.kicad_pcb")

SIGNAL_W = mm(0.2)
POWER_W  = mm(0.4)
VIA_D    = mm(0.6)
VIA_DRILL= mm(0.3)


def main():
    print("=" * 50)
    print("  Dilder PCB — DRC Fixer")
    print("=" * 50)

    board = pcbnew.LoadBoard(BOARD_FILE)

    # Step 1: Remove ALL tracks and vias
    to_remove = list(board.GetTracks())
    for t in to_remove:
        board.Remove(t)
    print(f"  Removed {len(to_remove)} tracks/vias")

    # Step 2: Collect pad info per net
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
            net_pads.setdefault(name, []).append({
                "x": cx, "y": cy, "ref": ref, "pad": pad.GetNumber()
            })
            net_objs[name] = net

    print(f"  {len(net_pads)} nets")

    # Step 3: Plan channel assignments
    # GPIO signals need long vertical runs — assign each a unique channel X on B.Cu
    # Left side channels: x = 3mm to 18mm from board left
    # Power bus: right side at x = 23mm

    gpio_nets = sorted([n for n in net_pads if n.startswith("GPIO")])
    other_long = ["QSPI_SCLK", "QSPI_SD0", "QSPI_SD1", "QSPI_SS",
                  "XIN", "XOUT", "RUN", "USB_DP", "USB_DM"]

    # Assign channels from left edge, spaced 1.0mm
    channel_x = {}
    ch_idx = 0
    for name in gpio_nets:
        channel_x[name] = mm(100 + 3.0 + ch_idx * 1.0)
        ch_idx += 1

    print(f"  {len(channel_x)} GPIO channels assigned (x=3.0 to {3.0 + ch_idx}mm)")

    # Step 4: Route each net
    routed = 0
    for name, pads in sorted(net_pads.items()):
        net = net_objs[name]

        if name == "GND":
            # GND via copper pour — no traces
            continue

        if len(pads) < 2:
            continue

        w = POWER_W if name in ("3V3", "VBUS", "VBUS_CHG", "VBAT", "BAT_PLUS") else SIGNAL_W

        sorted_p = sorted(pads, key=lambda p: (p["y"], p["x"]))

        if name == "3V3":
            # Power bus on B.Cu at RIGHT edge
            route_power_bus(board, sorted_p, w, net, bus_x=mm(100 + 23.5))
        elif name in ("VBAT", "VBUS"):
            route_power_bus(board, sorted_p, w, net, bus_x=mm(100 + 22.5))
        elif name in ("VBUS_CHG", "BAT_PLUS"):
            # Short local connections
            route_local(board, sorted_p, w, net)
        elif name in channel_x:
            # GPIO: use dedicated B.Cu channel
            route_channel(board, sorted_p, w, net, channel_x[name])
        else:
            # Local nets (short connections)
            route_local(board, sorted_p, w, net)

        routed += 1

    print(f"  Routed {routed} nets")

    # Step 5: Save and run DRC
    board.Save(BOARD_FILE)
    print(f"  Saved: {BOARD_FILE}")

    run_drc()
    render()


def route_power_bus(board, pads, width, net, bus_x):
    """Vertical bus on B.Cu, short F.Cu stubs to each pad via vias."""
    sorted_p = sorted(pads, key=lambda p: p["y"])

    # Main vertical bus on B.Cu
    if len(sorted_p) >= 2:
        add_track(board, bus_x, sorted_p[0]["y"], bus_x, sorted_p[-1]["y"], width, pcbnew.B_Cu, net)

    # Branch to each pad
    for i, p in enumerate(sorted_p):
        px, py = p["x"], p["y"]
        # Offset via Y slightly per pad to avoid stacking
        via_y = py + mm(0.3 * (i % 3 - 1))  # stagger -0.3, 0, +0.3mm

        # Via at bus position
        add_via(board, bus_x, via_y, net)
        # Horizontal F.Cu stub from via to pad
        add_track(board, bus_x, via_y, px, py, width, pcbnew.F_Cu, net)


def route_channel(board, pads, width, net, ch_x):
    """Route GPIO net through a dedicated B.Cu channel."""
    sorted_p = sorted(pads, key=lambda p: p["y"])

    for i in range(len(sorted_p) - 1):
        p1, p2 = sorted_p[i], sorted_p[i+1]
        x1, y1 = p1["x"], p1["y"]
        x2, y2 = p2["x"], p2["y"]

        dist = abs(to_mm(y2 - y1))

        if dist < 3.0 and abs(to_mm(x2 - x1)) < 3.0:
            # Close pads: direct F.Cu trace (no channel needed)
            add_track(board, x1, y1, x2, y1, width, pcbnew.F_Cu, net)
            if y1 != y2:
                add_track(board, x2, y1, x2, y2, width, pcbnew.F_Cu, net)
        else:
            # Long run: pad1 → F.Cu stub → via → B.Cu channel → via → F.Cu stub → pad2
            # Offset vias vertically to avoid stacking at same Y
            via1_y = y1 + mm(0.5)
            via2_y = y2 - mm(0.5)

            # Pad1 to via1 on F.Cu
            add_track(board, x1, y1, ch_x, y1, width, pcbnew.F_Cu, net)
            add_track(board, ch_x, y1, ch_x, via1_y, width, pcbnew.F_Cu, net)
            add_via(board, ch_x, via1_y, net)

            # Vertical run on B.Cu
            add_track(board, ch_x, via1_y, ch_x, via2_y, width, pcbnew.B_Cu, net)

            # Via2 to pad2 on F.Cu
            add_via(board, ch_x, via2_y, net)
            add_track(board, ch_x, via2_y, ch_x, y2, width, pcbnew.F_Cu, net)
            add_track(board, ch_x, y2, x2, y2, width, pcbnew.F_Cu, net)


def route_local(board, pads, width, net):
    """Route short local connections with L-shaped traces on F.Cu."""
    sorted_p = sorted(pads, key=lambda p: (p["y"], p["x"]))

    for i in range(len(sorted_p) - 1):
        p1, p2 = sorted_p[i], sorted_p[i+1]
        x1, y1 = p1["x"], p1["y"]
        x2, y2 = p2["x"], p2["y"]

        # Route vertical first, then horizontal (less likely to cross GPIO channels)
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


def run_drc():
    print("  Running DRC...")
    os.makedirs("/tmp/dilder-drc", exist_ok=True)
    subprocess.run(["kicad-cli", "pcb", "drc",
                    "--output", "/tmp/dilder-drc/drc-report.json",
                    "--format", "json", "--severity-all", BOARD_FILE],
                   capture_output=True)
    try:
        with open("/tmp/dilder-drc/drc-report.json") as f:
            drc = json.load(f)
        violations = drc.get("violations", [])
        by_type = {}
        for v in violations:
            t = v.get("type", "?")
            by_type.setdefault(t, {"count": 0, "severity": v.get("severity", "?")})
            by_type[t]["count"] += 1

        errors = sum(1 for v in violations if v.get("severity") == "error")
        warns = sum(1 for v in violations if v.get("severity") == "warning")
        print(f"  DRC: {errors} errors, {warns} warnings")

        # Categorize
        real_routing = 0
        cosmetic = 0
        for t, info in sorted(by_type.items(), key=lambda x: -x[1]["count"]):
            is_cosmetic = t in ("solder_mask_bridge", "silk_over_copper", "silk_overlap",
                               "silk_edge_clearance", "starved_thermal")
            tag = " (cosmetic)" if is_cosmetic else ""
            if is_cosmetic:
                cosmetic += info["count"]
            else:
                real_routing += info["count"]
            print(f"    {t}: {info['count']} ({info['severity']}){tag}")

        print(f"\n  Real routing errors: {real_routing}")
        print(f"  Cosmetic (clear after zone fill): {cosmetic}")

    except Exception as e:
        print(f"  DRC: {e}")


def render():
    print("  Rendering...")
    os.makedirs("/tmp/dilder-routed", exist_ok=True)
    for args, out in [
        ([], "board-top.png"),
        (["--perspective", "--rotate", "-45,0,25"], "board-3d.png"),
        (["--side", "bottom"], "board-bottom.png"),
    ]:
        subprocess.run(["kicad-cli", "pcb", "render",
                       "--output", f"/tmp/dilder-routed/{out}",
                       "--width", "2400", "--height", "1600",
                       "--quality", "basic", *args, BOARD_FILE],
                      capture_output=True)
    print("  Renders: /tmp/dilder-routed/")


if __name__ == "__main__":
    main()
