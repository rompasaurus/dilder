#!/usr/bin/env python3
"""
Route all traces on the Dilder PCB using KiCad's pcbnew Python API.

Strategy:
  - GND: handled by copper pour on both layers (thermal relief pads)
  - 3V3: route a power bus on B.Cu with vias up to each pad
  - All other nets: L-shaped traces on F.Cu, use B.Cu + vias for crossings
  - Power traces: 0.5mm width
  - Signal traces: 0.25mm width

Usage: python3 route_board.py
"""

import pcbnew
import os
import subprocess
import sys

def mm(val):
    return pcbnew.FromMM(val)

SIGNAL_WIDTH = mm(0.25)
POWER_WIDTH  = mm(0.5)
VIA_DIAM     = mm(0.6)
VIA_DRILL    = mm(0.3)

POWER_NETS = {"3V3", "VBUS", "VBUS_CHG", "VBAT", "BAT_PLUS"}


def load_board():
    path = os.path.join(os.path.dirname(__file__) or ".", "dilder.kicad_pcb")
    board = pcbnew.LoadBoard(path)
    print(f"  Loaded {path}")
    return board, path


def get_net_pads(board):
    """Build a dict of net_name -> list of (pad_center_x, pad_center_y, pad_ref)."""
    net_pads = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            net = pad.GetNet()
            if net is None:
                continue
            net_name = net.GetNetname()
            if not net_name or net_name == "":
                continue
            center = pad.GetPosition()
            if net_name not in net_pads:
                net_pads[net_name] = []
            net_pads[net_name].append((center.x, center.y, ref, pad.GetNumber()))
    return net_pads


def add_track(board, x1, y1, x2, y2, width, layer, net):
    """Add a copper track segment."""
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(pcbnew.VECTOR2I(x1, y1))
    track.SetEnd(pcbnew.VECTOR2I(x2, y2))
    track.SetWidth(width)
    track.SetLayer(layer)
    track.SetNet(net)
    board.Add(track)
    return track


def add_via(board, x, y, net):
    """Add a through-hole via."""
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(x, y))
    via.SetWidth(VIA_DIAM)
    via.SetDrill(VIA_DRILL)
    via.SetNet(net)
    board.Add(via)
    return via


def route_l_shape(board, x1, y1, x2, y2, width, layer, net, horizontal_first=True):
    """Route an L-shaped trace between two points."""
    if horizontal_first:
        # Go horizontal first, then vertical
        add_track(board, x1, y1, x2, y1, width, layer, net)
        if y1 != y2:
            add_track(board, x2, y1, x2, y2, width, layer, net)
    else:
        # Go vertical first, then horizontal
        add_track(board, x1, y1, x1, y2, width, layer, net)
        if x1 != x2:
            add_track(board, x1, y2, x2, y2, width, layer, net)


def route_chain(board, pads, width, layer, net):
    """Route a chain of pads: connect pad[0]→pad[1]→pad[2]→..."""
    for i in range(len(pads) - 1):
        x1, y1 = pads[i][0], pads[i][1]
        x2, y2 = pads[i+1][0], pads[i+1][1]
        # Choose L-shape direction based on relative position
        horizontal_first = abs(x2 - x1) < abs(y2 - y1)
        route_l_shape(board, x1, y1, x2, y2, width, layer, net, horizontal_first)


def route_star(board, pads, width, layer, net, hub_idx=0):
    """Route all pads to a central hub pad."""
    hub = pads[hub_idx]
    for i, pad in enumerate(pads):
        if i == hub_idx:
            continue
        x1, y1 = hub[0], hub[1]
        x2, y2 = pad[0], pad[1]
        horizontal_first = abs(x2 - x1) > abs(y2 - y1)
        route_l_shape(board, x1, y1, x2, y2, width, layer, net, horizontal_first)


def route_power_via(board, pads, width, net):
    """Route power net: bus on B.Cu, vias up to pads on F.Cu."""
    if len(pads) < 2:
        return

    # Sort pads by Y position (top to bottom along the board)
    sorted_pads = sorted(pads, key=lambda p: p[1])

    # Create a vertical bus on B.Cu at the average X position
    xs = [p[0] for p in sorted_pads]
    bus_x = sum(xs) // len(xs)

    # Route the bus on B.Cu
    for i in range(len(sorted_pads) - 1):
        y1 = sorted_pads[i][1]
        y2 = sorted_pads[i+1][1]
        add_track(board, bus_x, y1, bus_x, y2, width, pcbnew.B_Cu, net)

    # For each pad, add a via and short trace on F.Cu to reach the pad
    for px, py, ref, pad_num in sorted_pads:
        # Place via near the pad
        via_x = bus_x
        via_y = py
        add_via(board, via_x, via_y, net)
        # Short trace on F.Cu from via to pad
        if via_x != px or via_y != py:
            add_track(board, via_x, via_y, px, py, width, pcbnew.F_Cu, net)


def main():
    print("=" * 50)
    print("  Dilder PCB — Trace Router")
    print("=" * 50)

    board, board_path = load_board()

    # Remove any existing tracks and vias (clean slate)
    tracks_to_remove = list(board.GetTracks())
    for t in tracks_to_remove:
        board.Remove(t)
    print(f"  Cleared {len(tracks_to_remove)} existing tracks")

    # Get net info
    net_pads = get_net_pads(board)
    print(f"  Found {len(net_pads)} nets with pads")

    # Build net object lookup
    netinfo = board.GetNetInfo()
    net_objects = {}
    for name in net_pads:
        net_obj = netinfo.GetNetItem(name)
        if net_obj:
            net_objects[name] = net_obj

    routed = 0
    skipped = 0

    for net_name, pads in sorted(net_pads.items()):
        if net_name not in net_objects:
            continue
        net = net_objects[net_name]
        width = POWER_WIDTH if net_name in POWER_NETS else SIGNAL_WIDTH

        if net_name == "GND":
            # GND is handled by copper pour — no traces needed
            print(f"  GND: {len(pads)} pads — handled by copper pour")
            skipped += 1
            continue

        if len(pads) < 2:
            skipped += 1
            continue

        if net_name in POWER_NETS and len(pads) > 3:
            # Power nets with many pads: use B.Cu bus + vias
            route_power_via(board, pads, width, net)
            print(f"  {net_name}: {len(pads)} pads — power bus on B.Cu")
        elif len(pads) == 2:
            # Simple 2-pad net: direct L-shaped trace on F.Cu
            x1, y1 = pads[0][0], pads[0][1]
            x2, y2 = pads[1][0], pads[1][1]
            horizontal_first = abs(x2 - x1) > abs(y2 - y1)
            route_l_shape(board, x1, y1, x2, y2, width, pcbnew.F_Cu, net, horizontal_first)
            print(f"  {net_name}: 2 pads — L-trace on F.Cu")
        elif len(pads) <= 5:
            # Small multi-pad net: chain them together
            sorted_p = sorted(pads, key=lambda p: (p[1], p[0]))
            route_chain(board, sorted_p, width, pcbnew.F_Cu, net)
            print(f"  {net_name}: {len(pads)} pads — chained on F.Cu")
        else:
            # Large multi-pad net: use B.Cu bus
            route_power_via(board, pads, width, net)
            print(f"  {net_name}: {len(pads)} pads — bus on B.Cu")

        routed += 1

    print(f"\n  Routed {routed} nets, skipped {skipped}")

    # Fill copper zones (GND pour)
    print("  Filling copper zones...")
    try:
        filler = pcbnew.ZONE_FILLER(board)
        zones = board.Zones()
        zone_list = [zones[i] for i in range(zones.size())] if hasattr(zones, 'size') else list(zones)
        filler.Fill(zone_list)
        print(f"  Filled {len(zone_list)} zones")
    except Exception as e:
        print(f"  Zone fill error: {e} — fill manually in KiCad (Edit > Fill All Zones)")

    # Save
    board.Save(board_path)
    print(f"  Saved: {board_path}")

    # Run DRC
    print("  Running DRC...")
    os.makedirs("/tmp/dilder-drc", exist_ok=True)
    result = subprocess.run(
        ["kicad-cli", "pcb", "drc",
         "--output", "/tmp/dilder-drc/drc-report.json",
         "--format", "json",
         "--severity-all",
         board_path],
        capture_output=True, text=True
    )
    try:
        import json
        with open("/tmp/dilder-drc/drc-report.json") as f:
            drc = json.load(f)
        violations = drc.get("violations", [])
        errors = [v for v in violations if v.get("severity") == "error"]
        warnings = [v for v in violations if v.get("severity") == "warning"]
        unconnected = [v for v in violations if "unconnected" in v.get("type", "").lower()]
        clearance = [v for v in violations if "clearance" in v.get("type", "").lower()]
        print(f"  DRC: {len(errors)} errors, {len(warnings)} warnings")
        print(f"    Unconnected: {len(unconnected)}")
        print(f"    Clearance: {len(clearance)}")
        if errors:
            # Show first few error types
            types = {}
            for e in errors:
                t = e.get("type", "unknown")
                types[t] = types.get(t, 0) + 1
            for t, c in sorted(types.items(), key=lambda x: -x[1])[:5]:
                print(f"    {t}: {c}")
    except Exception as e:
        print(f"  DRC parse error: {e}")

    # Render
    print("  Rendering...")
    os.makedirs("/tmp/dilder-routed", exist_ok=True)

    subprocess.run(
        ["kicad-cli", "pcb", "render",
         "--output", "/tmp/dilder-routed/board-top.png",
         "--width", "2400", "--height", "1600",
         "--quality", "basic",
         board_path],
        capture_output=True, text=True
    )

    subprocess.run(
        ["kicad-cli", "pcb", "render",
         "--output", "/tmp/dilder-routed/board-3d.png",
         "--width", "2400", "--height", "1600",
         "--quality", "basic",
         "--perspective",
         "--rotate", "-45,0,25",
         board_path],
        capture_output=True, text=True
    )

    subprocess.run(
        ["kicad-cli", "pcb", "export", "svg",
         "--layers", "F.Cu,B.Cu,Edge.Cuts,F.SilkS",
         "--output", "/tmp/dilder-routed/",
         "--page-size-mode", "2",
         board_path],
        capture_output=True, text=True
    )

    print("  Renders saved to /tmp/dilder-routed/")
    print("\n  Done!")


if __name__ == "__main__":
    main()
