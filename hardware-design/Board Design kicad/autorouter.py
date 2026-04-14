#!/usr/bin/env python3
"""
Dilder PCB Autorouter — Lee's Algorithm (BFS wavefront) maze router.

Two-layer grid router with:
- Occupancy grid at 0.25mm resolution
- BFS pathfinding avoiding existing traces
- Via transitions between F.Cu and B.Cu
- Clearance-aware cell marking
- Net ordering: short nets first, power nets on dedicated bus

Usage: python3 autorouter.py
"""

import pcbnew
import os
import subprocess
import json
import sys
from collections import deque
import time

def mm(v): return pcbnew.FromMM(v)
def to_mm(v): return pcbnew.ToMM(v)

BOARD_FILE = os.path.join(os.path.dirname(__file__) or ".", "dilder.kicad_pcb")

# Grid parameters
GRID_RES = 0.25  # mm per grid cell
TRACE_W = 0.2    # mm signal trace width
POWER_W = 0.4    # mm power trace width
CLEARANCE = 0.2  # mm clearance between traces
VIA_COST = 8     # extra cost for via transition (discourages unnecessary vias)
VIA_RADIUS = 0.4 # mm — via occupies cells within this radius

# Layer indices for the grid
L_FCU = 0
L_BCU = 1

POWER_NETS = {"3V3", "VBUS", "VBUS_CHG", "VBAT", "BAT_PLUS"}


class Grid:
    """2-layer occupancy grid for the PCB."""

    def __init__(self, board_x, board_y, board_w, board_h):
        self.ox = board_x  # origin in mm
        self.oy = board_y
        self.w = int(board_w / GRID_RES) + 1
        self.h = int(board_h / GRID_RES) + 1
        # 0 = empty, >0 = occupied by net ID
        self.grid = [[[0]*self.w for _ in range(self.h)] for _ in range(2)]  # [layer][y][x]
        print(f"  Grid: {self.w}x{self.h} cells x 2 layers ({self.w*self.h*2:,} cells)")

    def mm_to_grid(self, x_mm, y_mm):
        """Convert mm coordinates to grid coordinates."""
        gx = int(round((x_mm - self.ox) / GRID_RES))
        gy = int(round((y_mm - self.oy) / GRID_RES))
        return max(0, min(gx, self.w-1)), max(0, min(gy, self.h-1))

    def grid_to_mm(self, gx, gy):
        """Convert grid coordinates to mm."""
        return self.ox + gx * GRID_RES, self.oy + gy * GRID_RES

    def is_free(self, layer, gx, gy, net_id=0):
        """Check if a cell is free (empty or same net)."""
        if gx < 0 or gx >= self.w or gy < 0 or gy >= self.h:
            return False
        val = self.grid[layer][gy][gx]
        return val == 0 or val == net_id

    def mark(self, layer, gx, gy, net_id, radius_cells=1):
        """Mark cells as occupied by a net, with clearance radius."""
        for dy in range(-radius_cells, radius_cells + 1):
            for dx in range(-radius_cells, radius_cells + 1):
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < self.w and 0 <= ny < self.h:
                    if self.grid[layer][ny][nx] == 0:
                        self.grid[layer][ny][nx] = net_id

    def mark_line(self, layer, gx1, gy1, gx2, gy2, net_id, radius_cells=1):
        """Mark cells along a line as occupied."""
        # Bresenham-ish line marking
        dx = abs(gx2 - gx1)
        dy = abs(gy2 - gy1)
        steps = max(dx, dy)
        if steps == 0:
            self.mark(layer, gx1, gy1, net_id, radius_cells)
            return
        for i in range(steps + 1):
            t = i / steps
            x = int(round(gx1 + t * (gx2 - gx1)))
            y = int(round(gy1 + t * (gy2 - gy1)))
            self.mark(layer, x, y, net_id, radius_cells)

    def mark_obstacle(self, gx, gy, radius_cells):
        """Mark cells as obstacle (net_id = -1, unclearable)."""
        for dy in range(-radius_cells, radius_cells + 1):
            for dx in range(-radius_cells, radius_cells + 1):
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < self.w and 0 <= ny < self.h:
                    if self.grid[L_FCU][ny][nx] == 0:
                        self.grid[L_FCU][ny][nx] = -1
                    if self.grid[L_BCU][ny][nx] == 0:
                        self.grid[L_BCU][ny][nx] = -1


def bfs_route(grid, start_layer, start_gx, start_gy, targets, net_id):
    """
    BFS wavefront router. Finds shortest path from start to any target.
    Returns list of (layer, gx, gy) waypoints, or None if no path found.

    State: (layer, gx, gy)
    Moves: 4-directional on same layer + via to other layer
    """
    start = (start_layer, start_gx, start_gy)
    target_set = set(targets)  # set of (layer, gx, gy)

    if start in target_set:
        return [start]

    # BFS
    queue = deque()
    queue.append((start, 0))  # (state, cost)
    came_from = {start: None}
    cost_so_far = {start: 0}

    while queue:
        (layer, gx, gy), cost = queue.popleft()

        # Check if reached a target
        # Accept target on either layer (we can add a via at the end)
        for tl, tgx, tgy in target_set:
            if gx == tgx and gy == tgy and layer == tl:
                # Reconstruct path
                path = []
                state = (layer, gx, gy)
                while state is not None:
                    path.append(state)
                    state = came_from[state]
                path.reverse()
                return path

        # Explore neighbors — 4 directions on same layer
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = gx+dx, gy+dy
            nstate = (layer, nx, ny)
            if nstate in came_from:
                continue
            if not grid.is_free(layer, nx, ny, net_id):
                continue
            new_cost = cost + 1
            came_from[nstate] = (layer, gx, gy)
            cost_so_far[nstate] = new_cost
            queue.append((nstate, new_cost))

        # Via transition to other layer
        other_layer = 1 - layer
        vstate = (other_layer, gx, gy)
        if vstate not in came_from and grid.is_free(other_layer, gx, gy, net_id):
            new_cost = cost + VIA_COST
            came_from[vstate] = (layer, gx, gy)
            cost_so_far[vstate] = new_cost
            queue.append((vstate, new_cost))

    return None  # No path found


def path_to_segments(path):
    """Convert a list of (layer, gx, gy) waypoints to track segments and vias."""
    if not path or len(path) < 2:
        return [], []

    segments = []  # (layer, gx1, gy1, gx2, gy2)
    vias = []      # (gx, gy)

    seg_start = path[0]
    for i in range(1, len(path)):
        prev = path[i-1]
        curr = path[i]

        if prev[0] != curr[0]:
            # Layer change — emit current segment and via
            if seg_start != prev:
                segments.append((seg_start[0], seg_start[1], seg_start[2], prev[1], prev[2]))
            vias.append((prev[1], prev[2]))
            seg_start = curr
        elif (curr[1] - prev[1], curr[2] - prev[2]) != \
             (prev[1] - path[i-2][1] if i >= 2 and prev[0] == path[i-2][0] else 999,
              prev[2] - path[i-2][2] if i >= 2 and prev[0] == path[i-2][0] else 999):
            # Direction changed — emit segment, start new one
            if seg_start[1] != prev[1] or seg_start[2] != prev[2]:
                segments.append((seg_start[0], seg_start[1], seg_start[2], prev[1], prev[2]))
            seg_start = prev

    # Final segment
    last = path[-1]
    if seg_start[1] != last[1] or seg_start[2] != last[2]:
        segments.append((seg_start[0], seg_start[1], seg_start[2], last[1], last[2]))

    return segments, vias


def simplify_path(path):
    """Remove redundant waypoints — keep only direction changes and layer changes."""
    if len(path) <= 2:
        return path

    result = [path[0]]
    for i in range(1, len(path) - 1):
        prev, curr, nxt = path[i-1], path[i], path[i+1]
        # Keep if layer change
        if prev[0] != curr[0] or curr[0] != nxt[0]:
            result.append(curr)
            continue
        # Keep if direction change
        d1 = (curr[1]-prev[1], curr[2]-prev[2])
        d2 = (nxt[1]-curr[1], nxt[2]-curr[2])
        if d1 != d2:
            result.append(curr)
    result.append(path[-1])
    return result


def main():
    t0 = time.time()
    print("=" * 55)
    print("  Dilder PCB — AUTOROUTER (Lee's Algorithm)")
    print("=" * 55)

    board = pcbnew.LoadBoard(BOARD_FILE)

    # Get board bounds
    bb = board.GetBoardEdgesBoundingBox()
    bx = to_mm(bb.GetLeft())
    by = to_mm(bb.GetTop())
    bw = to_mm(bb.GetWidth())
    bh = to_mm(bb.GetHeight())
    print(f"  Board: {bw:.0f}x{bh:.0f}mm at ({bx:.0f},{by:.0f})")

    # Remove existing tracks and vias
    old_tracks = list(board.GetTracks())
    for t in old_tracks:
        board.Remove(t)
    print(f"  Removed {len(old_tracks)} existing tracks/vias")

    # Build grid
    grid = Grid(bx, by, bw, bh)

    # Mark board edge as obstacle (1 cell border)
    for gx in range(grid.w):
        for layer in range(2):
            grid.grid[layer][0][gx] = -1
            grid.grid[layer][1][gx] = -1
            grid.grid[layer][grid.h-1][gx] = -1
            grid.grid[layer][grid.h-2][gx] = -1
    for gy in range(grid.h):
        for layer in range(2):
            grid.grid[layer][gy][0] = -1
            grid.grid[layer][gy][1] = -1
            grid.grid[layer][gy][grid.w-1] = -1
            grid.grid[layer][gy][grid.w-2] = -1

    # Collect pad info per net
    net_pads = {}  # name -> [(x_mm, y_mm, layer)]
    net_objs = {}
    net_ids = {}  # name -> unique int id
    next_id = 1

    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNet()
            if not net or not net.GetNetname():
                continue
            name = net.GetNetname()
            if name not in net_ids:
                net_ids[name] = next_id
                next_id += 1
            px = to_mm(pad.GetPosition().x)
            py = to_mm(pad.GetPosition().y)
            # Determine pad layer
            pad_layer = L_FCU  # most SMD pads are on F.Cu
            net_pads.setdefault(name, []).append((px, py, pad_layer))
            net_objs[name] = net

    print(f"  {len(net_pads)} nets, {sum(len(v) for v in net_pads.values())} pads")

    # Mark all pads on the grid (as their net — passable by same net)
    for name, pads in net_pads.items():
        nid = net_ids[name]
        for px, py, pl in pads:
            gx, gy = grid.mm_to_grid(px, py)
            grid.mark(pl, gx, gy, nid, radius_cells=1)

    # Sort nets: route short (2-pad) nets first, then larger nets
    # Skip GND (handled by pour)
    nets_to_route = []
    for name, pads in net_pads.items():
        if name == "GND":
            continue
        if len(pads) < 2:
            continue
        # Calculate total span
        xs = [p[0] for p in pads]
        ys = [p[1] for p in pads]
        span = (max(xs) - min(xs)) + (max(ys) - min(ys))
        nets_to_route.append((span, len(pads), name))

    nets_to_route.sort()  # shortest first
    print(f"  Routing {len(nets_to_route)} nets (shortest first)...")

    # Clearance radius in grid cells
    trace_radius = max(1, int((TRACE_W/2 + CLEARANCE) / GRID_RES))
    power_radius = max(1, int((POWER_W/2 + CLEARANCE) / GRID_RES))
    via_radius = max(1, int(VIA_RADIUS / GRID_RES))

    routed = 0
    failed = 0

    for span, npad, name in nets_to_route:
        pads = net_pads[name]
        net = net_objs[name]
        nid = net_ids[name]
        is_power = name in POWER_NETS
        radius = power_radius if is_power else trace_radius
        width = mm(POWER_W) if is_power else mm(TRACE_W)

        # Sort pads by position
        sorted_pads = sorted(pads, key=lambda p: (p[1], p[0]))

        # Route as a chain: pad[0]→pad[1]→pad[2]→...
        net_ok = True
        for i in range(len(sorted_pads) - 1):
            p1 = sorted_pads[i]
            p2 = sorted_pads[i+1]

            gx1, gy1 = grid.mm_to_grid(p1[0], p1[1])
            gx2, gy2 = grid.mm_to_grid(p2[0], p2[1])

            # Start on F.Cu (most pads are SMD on front)
            start = (L_FCU, gx1, gy1)
            # Accept target on either layer
            targets = [(L_FCU, gx2, gy2), (L_BCU, gx2, gy2)]

            path = bfs_route(grid, L_FCU, gx1, gy1, targets, nid)

            if path is None:
                # Try starting from B.Cu
                path = bfs_route(grid, L_BCU, gx1, gy1, targets, nid)

            if path is None:
                net_ok = False
                continue

            # Simplify path
            path = simplify_path(path)

            # Mark path on grid
            for j in range(len(path) - 1):
                l1, x1, y1 = path[j]
                l2, x2, y2 = path[j+1]
                if l1 == l2:
                    grid.mark_line(l1, x1, y1, x2, y2, nid, radius)
                else:
                    # Via — mark on both layers
                    grid.mark(L_FCU, x1, y1, nid, via_radius)
                    grid.mark(L_BCU, x1, y1, nid, via_radius)

            # Convert path to PCB tracks
            for j in range(len(path) - 1):
                l1, x1, y1 = path[j]
                l2, x2, y2 = path[j+1]

                if l1 != l2:
                    # Via
                    mx, my = grid.grid_to_mm(x1, y1)
                    via = pcbnew.PCB_VIA(board)
                    via.SetPosition(pcbnew.VECTOR2I(mm(mx), mm(my)))
                    via.SetWidth(int(mm(0.6)))
                    via.SetDrill(int(mm(0.3)))
                    via.SetNet(net)
                    board.Add(via)
                else:
                    # Track segment
                    mx1, my1 = grid.grid_to_mm(x1, y1)
                    mx2, my2 = grid.grid_to_mm(x2, y2)
                    layer = pcbnew.F_Cu if l1 == L_FCU else pcbnew.B_Cu
                    trk = pcbnew.PCB_TRACK(board)
                    trk.SetStart(pcbnew.VECTOR2I(mm(mx1), mm(my1)))
                    trk.SetEnd(pcbnew.VECTOR2I(mm(mx2), mm(my2)))
                    trk.SetWidth(int(width))
                    trk.SetLayer(layer)
                    trk.SetNet(net)
                    board.Add(trk)

        if net_ok:
            routed += 1
            status = "OK"
        else:
            failed += 1
            status = "FAIL"

        if failed > 0 or routed % 5 == 0:
            print(f"    {status} {name:15s} ({npad} pads, span={span:.1f}mm)")

    print(f"\n  Routed: {routed}/{routed+failed} nets")
    if failed:
        print(f"  Failed: {failed} nets (no path found)")

    # Save
    board.Save(BOARD_FILE)
    t1 = time.time()
    print(f"  Saved in {t1-t0:.1f}s")

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
        for x in v:
            by_type.setdefault(x["type"], 0)
            by_type[x["type"]] += 1
        cosmetic_types = {"solder_mask_bridge","silk_over_copper","silk_overlap","silk_edge_clearance","starved_thermal"}
        errors = sum(1 for x in v if x.get("severity") == "error")
        warns = sum(1 for x in v if x.get("severity") == "warning")
        cosmetic = sum(by_type.get(t,0) for t in cosmetic_types)
        print(f"  DRC: {errors} errors, {warns} warnings")
        print(f"  Routing errors: {errors - cosmetic} | Cosmetic: {cosmetic}")
        for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
            tag = " *" if t in cosmetic_types else ""
            print(f"    {t}: {c}{tag}")
    except Exception as e:
        print(f"  DRC: {e}")

    # Render
    print("  Rendering...")
    os.makedirs("/tmp/dilder-routed", exist_ok=True)
    for args, out in [
        ([], "board-top.png"),
        (["--perspective", "--rotate", "-40,0,20"], "board-3d.png"),
        (["--side", "bottom"], "board-bottom.png"),
    ]:
        subprocess.run(["kicad-cli", "pcb", "render", "--output", f"/tmp/dilder-routed/{out}",
                       "--width", "2400", "--height", "1600", "--quality", "basic",
                       *args, BOARD_FILE], capture_output=True)

    print(f"\n  DONE in {time.time()-t0:.1f}s")
    print(f"  Renders: /tmp/dilder-routed/")


if __name__ == "__main__":
    main()
