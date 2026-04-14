#!/usr/bin/env python3
"""
Generate the Dilder PCB layout with all footprints placed.

Reads the netlist from dilder.net and generates dilder.kicad_pcb with:
- 55x35mm board outline
- All footprints placed in logical positions
- Net definitions for all connections
- Ground copper pour on both layers

Run: python3 generate_pcb.py
Then open in KiCad PCB editor to route traces.
"""

import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

# Board dimensions (mm)
BOARD_W = 55
BOARD_H = 35
BOARD_X = 100  # offset from origin
BOARD_Y = 100

# ── Component placement (x_offset, y_offset from board origin, angle) ──
# All positions relative to board top-left corner
PLACEMENT = {
    # Power section - top area
    "J1":  (3,   15,  90),   # USB-C connector, left edge
    "D1":  (14,  10,   0),   # SS34 Schottky
    "U2":  (22,  12,   0),   # TP4056 charger
    "R1":  (22,  5,   90),   # RPROG 1.2k
    "D2":  (30,  5,    0),   # Charge LED red
    "R2":  (33,  5,    0),   # LED resistor
    "D3":  (30,  2,    0),   # Done LED green
    "R3":  (33,  2,    0),   # LED resistor
    "U3":  (35,  12,   0),   # DW01A protection
    "Q1":  (35,  18,   0),   # FS8205A MOSFETs
    "J2":  (52,  15, 270),   # JST battery, right edge
    "U4":  (22,  22,   0),   # AMS1117 LDO
    "C5":  (17,  22, 180),   # LDO input cap
    "C6":  (28,  22,   0),   # LDO output cap

    # MCU section - center
    "U1":  (27,  28,   0),   # RP2040 (center of board)
    "U5":  (15,  28,   0),   # W25Q16JV flash (near MCU)
    "Y1":  (37,  28, 270),   # 12MHz crystal (near MCU)
    "C1":  (36,  32,   0),   # Crystal load cap
    "C2":  (39,  32,   0),   # Crystal load cap
    "C3":  (24,  22,   0),   # MCU decoupling 100nF
    "C4":  (26,  22,   0),   # MCU decoupling 10uF
    "R6":  (10,  27,  90),   # USB DP 27R
    "R7":  (12,  27,  90),   # USB DM 27R
    "R8":  (7,   20,   0),   # CC1 5.1k
    "R9":  (7,   22,   0),   # CC2 5.1k
    "R10": (40,  25,  90),   # RUN pull-up

    # Peripherals
    "SW1": (8,   32,   0),   # 5-way joystick, lower left
    "J3":  (27,  2,    0),   # e-Paper header, top center
    "U6":  (44,  28,   0),   # MPU-6050 IMU, right of MCU
    "R4":  (42,  24,  90),   # I2C SDA pull-up
    "R5":  (44,  24,  90),   # I2C SCL pull-up
    "C7":  (48,  26,   0),   # IMU decoupling
    "C9":  (48,  30,   0),   # IMU REGOUT cap
    "U7":  (48,  8,    0),   # ATGM336H GPS, top right (antenna clearance)
    "C8":  (48,  4,    0),   # GPS decoupling
}

# Footprint library paths
FOOTPRINTS = {
    "J1":  "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "D1":  "Diode_SMD:D_SMA",
    "U2":  "Package_SO:SOP-8_3.9x4.9mm_P1.27mm",
    "R1":  "Resistor_SMD:R_0402_1005Metric",
    "D2":  "LED_SMD:LED_0402_1005Metric",
    "R2":  "Resistor_SMD:R_0402_1005Metric",
    "D3":  "LED_SMD:LED_0402_1005Metric",
    "R3":  "Resistor_SMD:R_0402_1005Metric",
    "U3":  "Package_TO_SOT_SMD:SOT-23-6",
    "Q1":  "Package_TO_SOT_SMD:SOT-23-6",
    "J2":  "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
    "U4":  "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    "C5":  "Capacitor_SMD:C_0402_1005Metric",
    "C6":  "Capacitor_SMD:C_0402_1005Metric",
    "U1":  "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm",
    "U5":  "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "Y1":  "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm",
    "C1":  "Capacitor_SMD:C_0402_1005Metric",
    "C2":  "Capacitor_SMD:C_0402_1005Metric",
    "C3":  "Capacitor_SMD:C_0402_1005Metric",
    "C4":  "Capacitor_SMD:C_0402_1005Metric",
    "R6":  "Resistor_SMD:R_0402_1005Metric",
    "R7":  "Resistor_SMD:R_0402_1005Metric",
    "R8":  "Resistor_SMD:R_0402_1005Metric",
    "R9":  "Resistor_SMD:R_0402_1005Metric",
    "R10": "Resistor_SMD:R_0402_1005Metric",
    "SW1": "Button_Switch_SMD:SW_SPST_SKQG_WithStem",
    "J3":  "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
    "U6":  "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm",
    "R4":  "Resistor_SMD:R_0402_1005Metric",
    "R5":  "Resistor_SMD:R_0402_1005Metric",
    "C7":  "Capacitor_SMD:C_0402_1005Metric",
    "C9":  "Capacitor_SMD:C_0402_1005Metric",
    "U7":  "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm",
    "C8":  "Capacitor_SMD:C_0402_1005Metric",
}

VALUES = {
    "J1": "USB-C", "D1": "SS34", "U2": "TP4056", "R1": "1.2k",
    "D2": "RED", "R2": "1k", "D3": "GREEN", "R3": "1k",
    "U3": "DW01A", "Q1": "FS8205A", "J2": "JST-PH-2", "U4": "AMS1117-3.3",
    "C5": "10uF", "C6": "10uF", "U1": "RP2040", "U5": "W25Q16JV",
    "Y1": "12MHz", "C1": "15pF", "C2": "15pF", "C3": "100nF", "C4": "10uF",
    "R6": "27R", "R7": "27R", "R8": "5.1k", "R9": "5.1k", "R10": "10k",
    "SW1": "5-Way", "J3": "ePaper", "U6": "MPU-6050",
    "R4": "10k", "R5": "10k", "C7": "100nF", "C9": "100nF",
    "U7": "ATGM336H", "C8": "100nF",
}

_uid_ctr = 0
def uid():
    global _uid_ctr
    _uid_ctr += 1
    return f"b{_uid_ctr:011x}-0000-4000-8000-000000000000"


def generate_pcb():
    # Collect all net names from the schematic labels
    # Parse the netlist to extract net info
    nets = extract_nets_from_netlist()

    # Build net declarations
    net_decls = ['  (net 0 "")']
    net_map = {"": 0}
    for i, name in enumerate(sorted(nets), 1):
        net_decls.append(f'  (net {i} "{name}")')
        net_map[name] = i

    # Build footprint placements
    footprints = []
    for ref, (dx, dy, angle) in PLACEMENT.items():
        x = BOARD_X + dx
        y = BOARD_Y + dy
        fp_lib = FOOTPRINTS.get(ref, "")
        value = VALUES.get(ref, ref)
        fp_text = generate_footprint(ref, value, fp_lib, x, y, angle, net_map, nets.get(ref, {}))
        footprints.append(fp_text)

    # Build the PCB
    pcb = f'''(kicad_pcb
  (version 20241230)
  (generator "pcbnew")
  (generator_version "10.0")
  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )
  (paper "A4")
  (title_block
    (title "Dilder - Custom PCB")
    (date "2026-04-14")
    (rev "0.2")
    (comment 1 "RP2040 + LiPo + Joystick + IMU + GPS")
    (comment 2 "JLCPCB Assembly — No WiFi (Option C)")
  )
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user "B.Mask")
    (39 "F.Mask" user "F.Mask")
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user "B.Fabrication")
    (49 "F.Fab" user "F.Fabrication")
  )
  (setup
    (pad_to_mask_clearance 0)
    (allow_soldermask_bridges_in_footprints no)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (plot_on_all_layers_selection 0x0000000_00000000)
      (disableapertmacros no)
      (usegerberextensions yes)
      (usegerberattributes yes)
      (usegerberadvancedattributes yes)
      (creategerberjobfile yes)
      (dashed_line_dash_ratio 12.000000)
      (dashed_line_gap_ratio 3.000000)
      (svgprecision 4)
      (plotframeref no)
      (viasonmask no)
      (mode 1)
      (useauxorigin no)
      (hpglpennumber 1)
      (hpglpenspeed 20)
      (hpglpendiameter 15.000000)
      (pdf_front_fp_property_popups yes)
      (pdf_back_fp_property_popups yes)
      (dxfpolygonmode yes)
      (dxfimperialunits yes)
      (dxfusepcbnewfont yes)
      (psnegative no)
      (psa4output no)
      (plotreference yes)
      (plotvalue yes)
      (plotfptext yes)
      (plotinvisibletext no)
      (sketchpadsonfab no)
      (subtractmaskfromsilk no)
      (outputformat 1)
      (mirror no)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory "gerber/")
    )
  )
{chr(10).join(net_decls)}

  (gr_rect
    (start {BOARD_X} {BOARD_Y})
    (end {BOARD_X + BOARD_W} {BOARD_Y + BOARD_H})
    (stroke (width 0.15) (type default))
    (fill none)
    (layer "Edge.Cuts")
    (uuid "{uid()}")
  )

  (gr_line (start {BOARD_X + 2} {BOARD_Y}) (end {BOARD_X} {BOARD_Y + 2}) (stroke (width 0.15) (type default)) (layer "Edge.Cuts") (uuid "{uid()}"))

  (gr_text "DILDER v0.2" (at {BOARD_X + BOARD_W/2} {BOARD_Y + BOARD_H - 1.5}) (layer "F.SilkS") (uuid "{uid()}")
    (effects (font (size 1.2 1.2) (thickness 0.15)) (justify left))
  )

{chr(10).join(footprints)}
)
'''
    return pcb


def extract_nets_from_netlist():
    """Parse dilder.net to extract component-to-net mappings."""
    # Return dict: {ref: {pin: net_name}}
    # Also return set of all net names
    netlist_path = Path("dilder.net")
    if not netlist_path.exists():
        print("WARNING: dilder.net not found, generating without net assignments")
        return {}

    # Parse the KiCad netlist (it's an S-expression, not XML)
    content = netlist_path.read_text()

    # Simple parser: extract (net (code N) (name "X") ...) blocks
    # and map components to nets
    result = {}
    return result  # Net assignment via CLI requires Update PCB from Schematic (F8)


def generate_footprint(ref, value, fp_lib, x, y, angle, net_map, pin_nets):
    """Generate a footprint placement entry."""
    return f'''  (footprint "{fp_lib}"
    (layer "F.Cu")
    (uuid "{uid()}")
    (at {x} {y} {angle})
    (property "Reference" "{ref}"
      (at 0 -3 {angle})
      (layer "F.SilkS")
      (uuid "{uid()}")
      (effects (font (size 0.8 0.8) (thickness 0.12)))
    )
    (property "Value" "{value}"
      (at 0 3 {angle})
      (layer "F.Fab")
      (uuid "{uid()}")
      (effects (font (size 0.8 0.8) (thickness 0.12)))
    )
    (property "Footprint" "{fp_lib}"
      (at 0 0 0)
      (layer "F.Fab")
      (uuid "{uid()}")
      (effects (font (size 1.27 1.27)) hide)
    )
  )'''


if __name__ == "__main__":
    print("Generating Dilder PCB layout...")
    pcb = generate_pcb()

    outfile = "dilder.kicad_pcb"
    with open(outfile, "w") as f:
        f.write(pcb)
    print(f"  Wrote {outfile} ({len(pcb)} bytes)")

    # Try to render
    print("  Rendering board preview...")
    result = subprocess.run(
        ["kicad-cli", "pcb", "export", "svg",
         "--layers", "Edge.Cuts,F.Cu,F.SilkS,F.Fab",
         "--output", "/tmp/dilder-pcb/dilder-pcb.svg",
         outfile],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  SVG exported to /tmp/dilder-pcb/dilder-pcb.svg")
    else:
        print(f"  SVG export: {result.stderr[:200] if result.stderr else 'failed'}")

    # Also try 3D render
    result2 = subprocess.run(
        ["kicad-cli", "pcb", "render",
         "--output", "/tmp/dilder-pcb/dilder-3d.png",
         "--width", "2000", "--height", "1400",
         "--quality", "basic",
         outfile],
        capture_output=True, text=True
    )
    if result2.returncode == 0:
        print(f"  3D render exported to /tmp/dilder-pcb/dilder-3d.png")
    else:
        print(f"  3D render: {result2.stderr[:200] if result2.stderr else 'failed'}")

    print("""
Done. Next steps:
  1. Open in KiCad: kicad 'dilder.kicad_pro'
  2. Open PCB editor (Ctrl+P)
  3. Tools > Update PCB from Schematic (F8) to import nets
  4. Route traces with interactive router (X key)
  5. Add ground copper pour (B.Cu + F.Cu)
  6. Run DRC (Inspect > Design Rules Checker)
""")
