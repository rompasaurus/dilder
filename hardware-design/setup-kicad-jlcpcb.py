#!/usr/bin/env python3
"""
Setup script for KiCad 10.0 + JLCPCB tooling for the Dilder PCB project.

What it does:
  1. Installs the KiCad standard symbol/footprint/3D-model libraries (system package)
  2. Installs the Bouni/kicad-jlcpcb-tools plugin (BOM + CPL generation, LCSC part search)
  3. Clones the CDFER/JLCPCB-Kicad-Library (symbols, footprints, 3D models)
  4. Registers the JLCPCB library in KiCad's sym-lib-table and fp-lib-table
  5. Initializes the KiCad project structure for Dilder

Usage:
  python3 setup-kicad-jlcpcb.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# --- Configuration ---

KICAD_VERSION = "10.0"
HOME = Path.home()

# KiCad directories
KICAD_DATA = HOME / ".local" / "share" / "kicad" / KICAD_VERSION
KICAD_CONFIG = HOME / ".config" / "kicad" / KICAD_VERSION
KICAD_PLUGINS_DIR = KICAD_DATA / "scripting" / "plugins"
KICAD_3RDPARTY_DIR = KICAD_DATA / "3rdparty"
KICAD_SYMBOLS_DIR = KICAD_DATA / "symbols"
KICAD_FOOTPRINTS_DIR = KICAD_DATA / "footprints"
KICAD_3DMODELS_DIR = KICAD_DATA / "3dmodels"

# Project directory
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR / "Board Design kicad"
PROJECT_NAME = "dilder"

# Repositories
JLCPCB_TOOLS_REPO = "https://github.com/Bouni/kicad-jlcpcb-tools.git"
JLCPCB_LIBRARY_REPO = "https://github.com/CDFER/JLCPCB-Kicad-Library.git"

SYM_LIB_TABLE = KICAD_CONFIG / "sym-lib-table"
FP_LIB_TABLE = KICAD_CONFIG / "fp-lib-table"


def run(cmd, cwd=None, check=True):
    """Run a shell command and return the result."""
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  STDERR: {result.stderr.strip()}")
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result


def ensure_dir(path):
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def clone_or_update(repo_url, target_dir, name):
    """Clone a repo or pull latest if it already exists."""
    if target_dir.exists() and (target_dir / ".git").exists():
        print(f"  {name} already cloned, pulling latest...")
        run(["git", "pull", "--ff-only"], cwd=target_dir, check=False)
    else:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        print(f"  Cloning {name}...")
        run(["git", "clone", "--depth", "1", repo_url, str(target_dir)])


# --- Step 1: Install KiCad standard libraries (system package) ---

def install_kicad_libraries():
    print("\n[1/5] Installing KiCad standard libraries...")

    # Detect package manager
    pkg_managers = [
        (["pacman", "--version"], ["sudo", "pacman", "-S", "--noconfirm", "kicad-library", "kicad-library-3d"]),
        (["apt", "--version"], ["sudo", "apt-get", "install", "-y", "kicad-libraries"]),
        (["dnf", "--version"], ["sudo", "dnf", "install", "-y", "kicad-packages3d", "kicad-symbols", "kicad-footprints"]),
        (["zypper", "--version"], ["sudo", "zypper", "install", "-y", "kicad-library", "kicad-library-3d"]),
    ]

    install_cmd = None
    for check_cmd, cmd in pkg_managers:
        result = subprocess.run(check_cmd, capture_output=True)
        if result.returncode == 0:
            install_cmd = cmd
            break

    if install_cmd is None:
        print("  WARNING: Could not detect package manager.")
        print("  Please install KiCad standard libraries manually:")
        print("    Arch:   sudo pacman -S kicad-library kicad-library-3d")
        print("    Debian: sudo apt-get install kicad-libraries")
        print("    Fedora: sudo dnf install kicad-packages3d kicad-symbols kicad-footprints")
        return

    # Check if already installed by looking for a known symbol file
    known_sym = Path("/usr/share/kicad/symbols")
    if known_sym.exists() and any(known_sym.glob("*.kicad_sym")):
        print("  KiCad standard libraries already installed")
        return

    print(f"  Running: {' '.join(install_cmd)}")
    print("  (This requires sudo — you may be prompted for your password)")
    result = subprocess.run(install_cmd)
    if result.returncode != 0:
        print("  WARNING: Library install failed. Run manually:")
        print(f"    {' '.join(install_cmd)}")
        print("  The standard libraries provide footprints for QFN-56, SOT-223,")
        print("  SOIC-8, etc. — required for PCB layout.")
    else:
        print("  Done. Standard symbols, footprints, and 3D models installed.")


# --- Step 2: Install kicad-jlcpcb-tools plugin ---

def install_jlcpcb_tools():
    print("\n[2/5] Installing kicad-jlcpcb-tools plugin...")

    ensure_dir(KICAD_PLUGINS_DIR)
    plugin_dir = KICAD_PLUGINS_DIR / "kicad-jlcpcb-tools"
    clone_or_update(JLCPCB_TOOLS_REPO, plugin_dir, "kicad-jlcpcb-tools")

    # Install Python dependencies the plugin needs
    requirements_file = plugin_dir / "requirements.txt"
    if requirements_file.exists():
        print("  Installing plugin Python dependencies...")
        run([sys.executable, "-m", "pip", "install", "--user", "-r", str(requirements_file)],
            check=False)
    else:
        # The plugin bundles deps in lib/, but some may need installing
        print("  Plugin bundles its own dependencies in lib/")

    print("  Done. Plugin will appear in KiCad: Tools > External Plugins > JLCPCB Tools")


# --- Step 3: Install JLCPCB KiCad Library ---

def install_jlcpcb_library():
    print("\n[3/5] Installing JLCPCB KiCad component library...")

    lib_dir = KICAD_3RDPARTY_DIR / "JLCPCB-Kicad-Library"
    clone_or_update(JLCPCB_LIBRARY_REPO, lib_dir, "JLCPCB-Kicad-Library")

    return lib_dir


# --- Step 4: Register library in KiCad ---

def register_library(lib_dir):
    print("\n[4/5] Registering JLCPCB library in KiCad...")

    lib_name = "JLCPCB"
    sym_path = lib_dir / "symbols"
    fp_path = lib_dir / "footprints"

    # Find the actual .kicad_sym files and .pretty dirs
    sym_files = list(sym_path.glob("*.kicad_sym")) if sym_path.exists() else []
    fp_dirs = list(fp_path.glob("*.pretty")) if fp_path.exists() else []

    # If the library uses a flat structure, check root
    if not sym_files:
        sym_files = list(lib_dir.glob("*.kicad_sym"))
    if not fp_dirs:
        fp_dirs = list(lib_dir.glob("*.pretty"))

    # Register symbol libraries
    if sym_files:
        _register_sym_libs(sym_files, lib_name)
    else:
        print("  No .kicad_sym files found — skipping symbol registration")

    # Register footprint libraries
    if fp_dirs:
        _register_fp_libs(fp_dirs, lib_name)
    else:
        print("  No .pretty dirs found — skipping footprint registration")


def _register_sym_libs(sym_files, prefix):
    """Add symbol libraries to sym-lib-table if not already present."""
    table_path = SYM_LIB_TABLE
    content = table_path.read_text() if table_path.exists() else '(sym_lib_table\n  (version 7)\n)'

    added = 0
    for sym_file in sorted(sym_files):
        lib_name = f"{prefix}_{sym_file.stem}"
        if lib_name in content:
            print(f"  Symbol lib '{lib_name}' already registered")
            continue

        entry = f'  (lib (name "{lib_name}") (type "KiCad") (uri "{sym_file}") (options "") (descr "JLCPCB component library"))'

        # Insert before closing paren
        content = content.rstrip().rstrip(")")
        content += f"\n{entry}\n)"
        added += 1

    table_path.write_text(content)
    print(f"  Registered {added} symbol libraries")


def _register_fp_libs(fp_dirs, prefix):
    """Add footprint libraries to fp-lib-table if not already present."""
    table_path = FP_LIB_TABLE
    content = table_path.read_text() if table_path.exists() else '(fp_lib_table\n  (version 7)\n)'

    added = 0
    for fp_dir in sorted(fp_dirs):
        lib_name = f"{prefix}_{fp_dir.stem}"
        if lib_name in content:
            print(f"  Footprint lib '{lib_name}' already registered")
            continue

        entry = f'  (lib (name "{lib_name}") (type "KiCad") (uri "{fp_dir}") (options "") (descr "JLCPCB component footprints"))'

        content = content.rstrip().rstrip(")")
        content += f"\n{entry}\n)"
        added += 1

    table_path.write_text(content)
    print(f"  Registered {added} footprint libraries")


# --- Step 5: Initialize KiCad project ---

def init_project():
    print("\n[5/5] Initializing KiCad project...")

    ensure_dir(PROJECT_DIR)

    pro_file = PROJECT_DIR / f"{PROJECT_NAME}.kicad_pro"
    sch_file = PROJECT_DIR / f"{PROJECT_NAME}.kicad_sch"
    pcb_file = PROJECT_DIR / f"{PROJECT_NAME}.kicad_pcb"

    # Create project file
    if not pro_file.exists():
        pro_file.write_text("""{
  "board": {
    "3dviewports": [],
    "design_settings": {
      "defaults": {
        "board_outline_line_width": 0.1,
        "copper_line_width": 0.2,
        "copper_text_size_h": 1.5,
        "copper_text_size_v": 1.5,
        "copper_text_thickness": 0.3,
        "other_line_width": 0.15,
        "silk_line_width": 0.15,
        "silk_text_size_h": 1.0,
        "silk_text_size_v": 1.0,
        "silk_text_thickness": 0.15
      },
      "diff_pair_dimensions": [],
      "drc_exclusions": [],
      "rules": {
        "min_copper_edge_clearance": 0.3,
        "min_hole_clearance": 0.25,
        "min_hole_to_hole": 0.25,
        "min_microvia_diameter": 0.2,
        "min_microvia_drill": 0.1,
        "min_resolved_spokes": 2,
        "min_silk_clearance": 0.0,
        "min_text_height": 0.8,
        "min_text_thickness": 0.08,
        "min_through_hole_diameter": 0.3,
        "min_track_width": 0.127,
        "min_via_annular_width": 0.13,
        "min_via_diameter": 0.6,
        "solder_mask_to_copper_clearance": 0.0,
        "use_height_for_length_calcs": true
      },
      "track_widths": [0.0, 0.15, 0.25, 0.5, 1.0],
      "via_dimensions": [{"diameter": 0.6, "drill": 0.3}]
    },
    "layer_presets": [],
    "viewports": []
  },
  "boards": [],
  "cvpcb": { "equivalence_files": [] },
  "libraries": { "pinned_footprint_libs": [], "pinned_symbol_libs": [] },
  "meta": { "filename": "dilder.kicad_pro", "version": 1 },
  "net_settings": {
    "classes": [
      {
        "bus_width": 12,
        "clearance": 0.2,
        "diff_pair_gap": 0.25,
        "diff_pair_via_gap": 0.25,
        "diff_pair_width": 0.2,
        "line_style": 0,
        "microvia_diameter": 0.3,
        "microvia_drill": 0.1,
        "name": "Default",
        "pcb_color": "rgba(0, 0, 0, 0.000)",
        "schematic_color": "rgba(0, 0, 0, 0.000)",
        "track_width": 0.25,
        "via_diameter": 0.6,
        "via_drill": 0.3,
        "wire_width": 6
      },
      {
        "bus_width": 12,
        "clearance": 0.3,
        "diff_pair_gap": 0.25,
        "diff_pair_via_gap": 0.25,
        "diff_pair_width": 0.4,
        "line_style": 0,
        "microvia_diameter": 0.3,
        "microvia_drill": 0.1,
        "name": "Power",
        "pcb_color": "rgba(255, 0, 0, 1.000)",
        "schematic_color": "rgba(255, 0, 0, 1.000)",
        "track_width": 0.5,
        "via_diameter": 0.8,
        "via_drill": 0.4,
        "wire_width": 6
      }
    ],
    "meta": { "version": 3 },
    "net_colors": null,
    "netclass_assignments": null,
    "netclass_patterns": []
  },
  "pcbnew": {
    "last_paths": { "gencad": "", "idf": "", "netlist": "", "plot": "", "pos_files": "", "specctra_dsn": "", "step": "", "vrml": "" },
    "page_layout_descr_file": ""
  },
  "schematic": {
    "annotate_start_num": 1,
    "bom_fmt_presets": [],
    "bom_fmt_settings": { "field_delimiter": ",", "keep_line_breaks": false, "keep_tabs": false, "ref_delimiter": ",", "ref_range_delimiter": "", "string_delimiter": "\\\"" },
    "bom_presets": [],
    "drawing": { "dashed_lines_dash_length_ratio": 12.0, "dashed_lines_gap_length_ratio": 3.0, "default_line_thickness": 6.0, "default_text_size": 50.0, "field_names": [], "intersheets_ref_own_page": false, "intersheets_ref_prefix": "", "intersheets_ref_short": false, "intersheets_ref_show": false, "intersheets_ref_suffix": "", "junction_size_choice": 3, "label_size_ratio": 0.375, "operating_point_overlay_i_precision": 3, "operating_point_overlay_v_precision": 3, "overbar_offset_ratio": 1.23, "pin_symbol_size": 25.0, "text_offset_ratio": 0.15 },
    "legacy_lib_dir": "",
    "legacy_lib_list": [],
    "meta": { "version": 1 },
    "net_format_name": "",
    "page_layout_descr_file": "",
    "plot_directory": "",
    "spice_current_sheet_as_root": false,
    "spice_external_command": "spice \\\"%I\\\"",
    "spice_model_current_sheet_as_root": true,
    "spice_save_all_currents": false,
    "spice_save_all_dissipations": false,
    "spice_save_all_voltages": false,
    "subpart_first_id": 65,
    "subpart_id_separator": 0
  },
  "sheets": [["e63e39d7-6ac0-4ffd-8aa3-1841a4541b55", "Root"]],
  "text_variables": {}
}
""")
        print(f"  Created {pro_file.name}")
    else:
        print(f"  {pro_file.name} already exists")

    # Create empty schematic
    if not sch_file.exists():
        sch_file.write_text("""(kicad_sch
  (version 20231120)
  (generator "eeschema")
  (generator_version "10.0")
  (uuid "e63e39d7-6ac0-4ffd-8aa3-1841a4541b55")
  (paper "A3")
  (title_block
    (title "Dilder - Custom PCB")
    (date "2026-04-14")
    (rev "0.1")
    (comment 1 "RP2040 + LiPo + Joystick + Sensors")
    (comment 2 "JLCPCB Assembly Target")
  )
  (lib_symbols)
  (symbol_instances)
)
""")
        print(f"  Created {sch_file.name}")
    else:
        print(f"  {sch_file.name} already exists")

    # Create empty PCB
    if not pcb_file.exists():
        pcb_file.write_text("""(kicad_pcb
  (version 20240108)
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
    (rev "0.1")
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
      (usegerberextensions no)
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
  (net 0 "")
  (gr_rect
    (start 0 0)
    (end 55 35)
    (stroke (width 0.15) (type default))
    (fill none)
    (layer "Edge.Cuts")
    (uuid "board-outline-001")
  )
)
""")
        print(f"  Created {pcb_file.name} (55x35mm board outline)")
    else:
        print(f"  {pcb_file.name} already exists")

    print(f"\n  Project ready at: {PROJECT_DIR}/")
    print(f"  Open in KiCad:  kicad '{PROJECT_DIR / (PROJECT_NAME + '.kicad_pro')}'")


# --- Main ---

def main():
    print("=" * 60)
    print("  Dilder PCB — KiCad + JLCPCB Setup")
    print("=" * 60)

    # Verify KiCad is installed
    result = run(["kicad-cli", "version"], check=False)
    if result.returncode != 0:
        print("ERROR: KiCad not found. Install KiCad 10.0 first.")
        sys.exit(1)
    print(f"  KiCad version: {result.stdout.strip()}")

    # Verify git is available
    result = run(["git", "--version"], check=False)
    if result.returncode != 0:
        print("ERROR: git not found. Install git first.")
        sys.exit(1)

    install_kicad_libraries()
    install_jlcpcb_tools()
    lib_dir = install_jlcpcb_library()
    register_library(lib_dir)
    init_project()

    print("\n" + "=" * 60)
    print("  Setup complete!")
    print("=" * 60)
    print("""
  Next steps:
    1. Open KiCad and load the project:
       kicad 'Board Design kicad/dilder.kicad_pro'

    2. In the schematic editor, add components from the JLCPCB library
       and KiCad's built-in library (RP2040, passives, connectors)

    3. Use the JLCPCB Tools plugin (Tools > External Plugins > JLCPCB Tools)
       to assign LCSC part numbers and verify availability

    4. After completing the schematic + PCB layout, generate fabrication
       files via the plugin for direct upload to jlcpcb.com
""")


if __name__ == "__main__":
    main()
