#!/usr/bin/env python3
"""
Dilder — Pico W & Display First-Time Setup

Interactive step-by-step CLI that walks you through the entire process:
installing the C/C++ SDK toolchain, configuring VSCode, building and
flashing the hello world programs, and connecting the e-ink display.

Usage:
  python3 setup.py              # interactive step-by-step walkthrough
  python3 setup.py --status     # show current setup state
  python3 setup.py --step N     # jump to step N
  python3 setup.py --list       # list all steps
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import textwrap
import threading
import time
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Terminal helpers
# ─────────────────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"

FG_GREEN  = "\033[32m"
FG_YELLOW = "\033[33m"
FG_BLUE   = "\033[34m"
FG_CYAN   = "\033[36m"
FG_RED    = "\033[31m"
FG_WHITE  = "\033[97m"
FG_GREY   = "\033[90m"
FG_MAGENTA = "\033[35m"

NO_COLOUR = bool(os.environ.get("NO_COLOR")) or not sys.stdout.isatty()


def c(text: str, *codes: str) -> str:
    if NO_COLOUR:
        return text
    return "".join(codes) + text + RESET


def icon(sym: str) -> str:
    if platform.system() == "Windows":
        return {"ok": "[OK]", "fail": "[FAIL]", "arrow": "->",
                "gear": "[*]", "warn": "[!]", "dot": "[.]",
                "check": "[x]", "empty": "[ ]"}.get(sym, sym)
    return {"ok": "\u2713", "fail": "\u2717", "arrow": "\u2192",
            "gear": "\u2699", "warn": "\u26a0", "dot": "\u25cf",
            "check": "\u2611", "empty": "\u2610"}.get(sym, sym)


# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

def log_ok(msg: str) -> None:
    print(c(f"  {icon('ok')} {msg}", FG_GREEN))

def log_warn(msg: str) -> None:
    print(c(f"  {icon('warn')} {msg}", FG_YELLOW))

def log_error(msg: str) -> None:
    print(c(f"  {icon('fail')} {msg}", FG_RED, BOLD), file=sys.stderr)

def log_info(msg: str) -> None:
    print(c(f"  {icon('dot')} {msg}", FG_GREY))

def log_step(msg: str) -> None:
    print(c(f"  {icon('arrow')} {msg}", FG_CYAN))

def log_cmd(cmd: str) -> None:
    print(c(f"    $ {cmd}", FG_GREY, DIM))


def log_header(title: str) -> None:
    width = 60
    bar = "\u2500" * width
    print()
    print(c(f"\u250c{bar}\u2510", FG_BLUE, BOLD))
    print(c(f"\u2502{title.center(width)}\u2502", FG_BLUE, BOLD))
    print(c(f"\u2514{bar}\u2518", FG_BLUE, BOLD))
    print()


def log_explain(text: str) -> None:
    """Print a multi-line explanation block with wrapping."""
    lines = textwrap.dedent(text).strip().splitlines()
    print()
    for line in lines:
        if not line.strip():
            print()
            continue
        wrapped = textwrap.fill(line.strip(), width=72,
                                initial_indent="    ",
                                subsequent_indent="    ")
        print(c(wrapped, FG_WHITE))
    print()


def log_manual(text: str) -> None:
    """Print a manual action block (things the user must do physically)."""
    lines = textwrap.dedent(text).strip().splitlines()
    print()
    print(c("  \u250c\u2500 Manual step \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510", FG_MAGENTA))
    for line in lines:
        print(c(f"  \u2502  {line}", FG_MAGENTA))
    print(c("  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518", FG_MAGENTA))
    print()


def log_code_block(code: str) -> None:
    """Print a code block."""
    lines = textwrap.dedent(code).strip().splitlines()
    print()
    print(c("    \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510", FG_GREY))
    for line in lines:
        print(c(f"    \u2502 {line:<47}\u2502", FG_GREY))
    print(c("    \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518", FG_GREY))
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Spinner
# ─────────────────────────────────────────────────────────────────────────────

class Spinner:
    FRAMES = ["\u280b", "\u2819", "\u2839", "\u2838", "\u283c", "\u2834", "\u2826", "\u2827", "\u2807", "\u280f"]

    def __init__(self, label: str) -> None:
        self.label = label
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self) -> None:
        i = 0
        while not self._stop.is_set():
            frame = self.FRAMES[i % len(self.FRAMES)]
            if not NO_COLOUR:
                print(f"\r{c(frame, FG_CYAN)}  {self.label} ", end="", flush=True)
            i += 1
            time.sleep(0.08)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *_):
        self._stop.set()
        self._thread.join()
        if not NO_COLOUR:
            print("\r" + " " * (len(self.label) + 6) + "\r", end="")


# ─────────────────────────────────────────────────────────────────────────────
# Paths and constants
# ─────────────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.resolve()
DEV_SETUP    = PROJECT_ROOT / "dev-setup"
HELLO_SERIAL = DEV_SETUP / "hello-world-serial"
HELLO_DISPLAY = DEV_SETUP / "hello-world"

DEFAULT_SDK_PATH = Path.home() / "pico" / "pico-sdk"


def detect_serial_group() -> str:
    """Detect the correct group for serial port access.

    Arch/CachyOS/Manjaro use 'uucp'. Debian/Ubuntu use 'dialout'.
    Returns whichever group actually exists on the system.
    """
    for group in ("uucp", "dialout"):
        result = subprocess.run(
            ["getent", "group", group],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return group
    # Fallback — try the distro convention
    distro = detect_distro()
    if distro == "arch":
        return "uucp"
    return "dialout"


def user_in_serial_group() -> bool:
    """Check if the current user is in the serial port group."""
    group = detect_serial_group()
    result = run_cmd(["groups"])
    return result.returncode == 0 and group in result.stdout.split()


def get_sdk_path() -> Path:
    env = os.environ.get("PICO_SDK_PATH")
    if env:
        return Path(env)
    return DEFAULT_SDK_PATH


def detect_distro() -> str:
    """Detect the Linux distribution family."""
    try:
        with open("/etc/os-release") as f:
            content = f.read().lower()
        if "cachyos" in content or "arch" in content or "manjaro" in content:
            return "arch"
        if "ubuntu" in content or "debian" in content or "mint" in content:
            return "debian"
        if "fedora" in content or "rhel" in content or "centos" in content:
            return "fedora"
    except FileNotFoundError:
        pass
    return "unknown"


def run_cmd(cmd: list, check: bool = True, capture: bool = True, **kwargs):
    """Run a shell command. Returns CompletedProcess."""
    if capture:
        return subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    return subprocess.run(cmd, **kwargs)


def cmd_exists(name: str) -> bool:
    return shutil.which(name) is not None


def find_rpi_rp2_mount() -> "Path | None":
    """Find the RPI-RP2 USB drive mount point, with retries for automount delay."""
    user = os.environ.get("USER", "")
    static_paths = [
        Path(f"/run/media/{user}/RPI-RP2"),
        Path(f"/media/{user}/RPI-RP2"),
        Path("/mnt/RPI-RP2"),
    ]

    # Try static paths first
    for p in static_paths:
        if p.exists() and p.is_dir():
            return p

    # Fallback: ask findmnt / lsblk for the actual mount
    for cmd in (
        ["findmnt", "-rno", "TARGET", "-S", "LABEL=RPI-RP2"],
        ["lsblk", "-rno", "MOUNTPOINT", "-l", "/dev/sda1"],
    ):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                p = Path(result.stdout.strip().splitlines()[0])
                if p.exists():
                    return p
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    # Retry static paths once more (automount may have finished)
    time.sleep(1)
    for p in static_paths:
        if p.exists() and p.is_dir():
            return p

    return None


def prompt_continue(msg: str = "Press Enter to continue (or 's' to skip)") -> str:
    """Prompt the user. Returns 'continue', 'skip', or 'quit'."""
    try:
        resp = input(c(f"\n  {icon('arrow')} {msg}: ", FG_CYAN)).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        return "quit"
    if resp in ("s", "skip"):
        return "skip"
    if resp in ("q", "quit", "exit"):
        return "quit"
    return "continue"


def prompt_yes_no(msg: str, default: bool = True) -> bool:
    """Ask a yes/no question. Returns True for yes."""
    hint = "[Y/n]" if default else "[y/N]"
    try:
        resp = input(c(f"\n  {icon('arrow')} {msg} {hint}: ", FG_CYAN)).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        return False
    if not resp:
        return default
    return resp in ("y", "yes")


# ─────────────────────────────────────────────────────────────────────────────
# Steps
# ─────────────────────────────────────────────────────────────────────────────

STEPS = []


def step(number: int, title: str, desc: str):
    """Decorator to register a setup step."""
    def decorator(fn):
        STEPS.append({
            "number": number,
            "title": title,
            "desc": desc,
            "fn": fn,
        })
        STEPS.sort(key=lambda s: s["number"])
        return fn
    return decorator


# ── Step 1: Prerequisites ────────────────────────────────────────────────────

@step(1, "Check Prerequisites", "Verify your system has the basics: git, cmake, Python")
def step_prerequisites():
    log_header("Step 1 — Check Prerequisites")

    log_explain("""
        Before we install the Pico toolchain, let's make sure your system
        has the basic tools we need. This step checks for git, cmake, Python,
        and detects your Linux distribution so we install the right packages.
    """)

    all_ok = True
    distro = detect_distro()

    # Platform
    log_info(f"Platform: {platform.system()} {platform.release()}")
    log_info(f"Distribution: {distro if distro != 'unknown' else 'unknown (will use generic commands)'}")

    if platform.system() != "Linux":
        log_warn("This setup script is designed for Linux.")
        log_warn("You may need to adapt commands for your OS.")
        print()

    # Python
    ver = platform.python_version()
    if sys.version_info >= (3, 9):
        log_ok(f"Python {ver}")
    else:
        log_error(f"Python {ver} — need 3.9+")
        all_ok = False

    # Git
    if cmd_exists("git"):
        result = run_cmd(["git", "--version"])
        log_ok(result.stdout.strip())
    else:
        log_error("git not found — install git first")
        all_ok = False

    # CMake
    if cmd_exists("cmake"):
        result = run_cmd(["cmake", "--version"])
        first_line = result.stdout.strip().splitlines()[0]
        log_ok(first_line)
    else:
        log_warn("cmake not found — will install in the next step")

    # Ninja
    if cmd_exists("ninja"):
        log_ok("ninja build system found")
    else:
        log_warn("ninja not found — will install in the next step")

    print()
    if all_ok:
        log_ok("Prerequisites look good. Ready to proceed.")
    else:
        log_warn("Some prerequisites are missing. Install them before continuing.")

    return all_ok


# ── Step 2: ARM Toolchain ────────────────────────────────────────────────────

@step(2, "Install ARM Toolchain", "Install the cross-compiler, CMake, and Ninja for Pico W builds")
def step_toolchain():
    log_header("Step 2 — Install ARM Cross-Compilation Toolchain")

    log_explain("""
        The Pico W uses an ARM Cortex-M0+ processor. Your Linux PC has an
        x86/x64 processor. To compile C code that runs on the Pico, we need
        a cross-compiler — it runs on your PC but produces ARM machine code.

        We also need CMake (the build system the Pico SDK uses) and Ninja
        (a fast build executor that CMake generates instructions for).
    """)

    # Check if already installed
    if cmd_exists("arm-none-eabi-gcc"):
        result = run_cmd(["arm-none-eabi-gcc", "--version"])
        first_line = result.stdout.strip().splitlines()[0]
        log_ok(f"ARM GCC already installed: {first_line}")
        if prompt_yes_no("Reinstall/update anyway?", default=False):
            pass  # continue to install
        else:
            return True

    distro = detect_distro()

    if distro == "arch":
        packages = "arm-none-eabi-gcc arm-none-eabi-newlib cmake ninja python git base-devel"
        install_cmd = f"sudo pacman -S --needed {packages}"
    elif distro == "debian":
        packages = ("gcc-arm-none-eabi libnewlib-arm-none-eabi cmake ninja-build "
                    "python3 git build-essential libstdc++-arm-none-eabi-newlib")
        install_cmd = f"sudo apt update && sudo apt install -y {packages}"
    elif distro == "fedora":
        packages = "arm-none-eabi-gcc-cs arm-none-eabi-newlib cmake ninja-build python3 git"
        install_cmd = f"sudo dnf install -y {packages}"
    else:
        log_warn("Could not detect your distribution.")
        log_info("Install these packages manually:")
        log_info("  - arm-none-eabi-gcc (ARM cross-compiler)")
        log_info("  - arm-none-eabi-newlib (C standard library for ARM)")
        log_info("  - cmake, ninja, git, python3")
        return prompt_continue() != "quit"

    log_explain(f"""
        Detected distribution: {distro}

        The following command will install all required packages:
    """)

    log_code_block(install_cmd)

    if not prompt_yes_no("Run this install command now?"):
        log_info("Skipped. Run the command manually when ready.")
        return True

    log_step("Installing packages (this may take a minute)...")
    print()

    result = subprocess.run(install_cmd, shell=True)

    if result.returncode != 0:
        log_error("Package installation failed. Check the output above.")
        return False

    # Verify
    if cmd_exists("arm-none-eabi-gcc"):
        result = run_cmd(["arm-none-eabi-gcc", "--version"])
        first_line = result.stdout.strip().splitlines()[0]
        log_ok(f"Installed: {first_line}")
    else:
        log_error("arm-none-eabi-gcc still not found after install.")
        return False

    if cmd_exists("cmake"):
        log_ok("cmake installed")
    if cmd_exists("ninja"):
        log_ok("ninja installed")

    return True


# ── Step 3: Pico SDK ─────────────────────────────────────────────────────────

@step(3, "Clone Pico SDK", "Download the official Raspberry Pi Pico C/C++ SDK")
def step_pico_sdk():
    log_header("Step 3 — Clone the Pico SDK")

    log_explain("""
        The Pico SDK is the official C/C++ development kit from Raspberry Pi.
        It provides all the low-level libraries for talking to the RP2040
        hardware: GPIO, SPI, USB, timers, and more.

        We'll clone it to ~/pico/pico-sdk and set an environment variable
        so the build system can find it.
    """)

    sdk_path = get_sdk_path()

    if sdk_path.exists() and (sdk_path / "src").exists():
        log_ok(f"Pico SDK already exists at {sdk_path}")
        if not prompt_yes_no("Re-clone it?", default=False):
            return True

    # Clone
    sdk_parent = sdk_path.parent
    sdk_parent.mkdir(parents=True, exist_ok=True)

    log_step(f"Cloning pico-sdk to {sdk_path}...")
    log_cmd("git clone --recurse-submodules https://github.com/raspberrypi/pico-sdk.git")
    print()

    if sdk_path.exists():
        log_info("Removing existing directory first...")
        shutil.rmtree(sdk_path)

    with Spinner("Cloning pico-sdk (this may take a few minutes)"):
        result = run_cmd(
            ["git", "clone", "--recurse-submodules",
             "https://github.com/raspberrypi/pico-sdk.git",
             str(sdk_path)]
        )

    if result.returncode != 0:
        log_error("Failed to clone pico-sdk:")
        print(result.stderr)
        return False

    log_ok(f"Pico SDK cloned to {sdk_path}")

    # Verify structure
    if (sdk_path / "src").exists() and (sdk_path / "cmake").exists():
        log_ok("SDK structure verified (src/, cmake/ present)")
    else:
        log_warn("SDK directory exists but structure looks wrong")

    return True


# ── Step 4: Environment Variable ─────────────────────────────────────────────

@step(4, "Set PICO_SDK_PATH", "Configure your shell to find the Pico SDK")
def step_env_var():
    log_header("Step 4 — Set PICO_SDK_PATH Environment Variable")

    log_explain("""
        The Pico SDK build system needs to know where the SDK is installed.
        We do this by setting an environment variable called PICO_SDK_PATH
        in your shell profile. This way, every new terminal automatically
        knows where to find the SDK.
    """)

    sdk_path = get_sdk_path()

    # Check if already set
    current = os.environ.get("PICO_SDK_PATH")
    if current:
        log_ok(f"PICO_SDK_PATH is already set: {current}")
        if Path(current).exists():
            log_ok("Path exists and looks valid.")
            return True
        else:
            log_warn("But the path doesn't exist! Let's fix it.")

    # Detect shell
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        rc_file = Path.home() / ".zshrc"
        shell_name = "zsh"
    else:
        rc_file = Path.home() / ".bashrc"
        shell_name = "bash"

    export_line = f'export PICO_SDK_PATH="{sdk_path}"'

    log_explain(f"""
        Your shell is {shell_name}. We'll add this line to {rc_file}:
    """)

    log_code_block(export_line)

    # Check if already in the file
    if rc_file.exists():
        content = rc_file.read_text()
        if "PICO_SDK_PATH" in content:
            log_warn(f"PICO_SDK_PATH is already in {rc_file}")
            log_info("If the path is wrong, edit the file manually.")
            # Set it for this session anyway
            os.environ["PICO_SDK_PATH"] = str(sdk_path)
            return True

    if not prompt_yes_no(f"Add PICO_SDK_PATH to {rc_file}?"):
        log_info("Skipped. Add it manually:")
        log_code_block(export_line)
        return True

    # Append to rc file
    with open(rc_file, "a") as f:
        f.write(f"\n# Pico SDK path (added by Dilder setup)\n")
        f.write(f"{export_line}\n")

    log_ok(f"Added to {rc_file}")

    # Set for current session
    os.environ["PICO_SDK_PATH"] = str(sdk_path)
    log_ok(f"Set for this session: PICO_SDK_PATH={sdk_path}")

    log_warn("For new terminal windows, run:")
    log_code_block(f"source {rc_file}")

    return True


# ── Step 5: Serial Permissions ────────────────────────────────────────────────

@step(5, "Serial Port Permissions", "Grant your user access to /dev/ttyACM0")
def step_serial_permissions():
    log_header("Step 5 — Serial Port Permissions")

    serial_group = detect_serial_group()

    log_explain(f"""
        When the Pico W is plugged in via USB (not in BOOTSEL mode), it
        appears as a serial device at /dev/ttyACM0. Your user needs to be
        in the '{serial_group}' group to access it.

        Without this, you'll get "Permission denied" when trying to read
        serial output from your programs.

        Note: Arch/CachyOS/Manjaro use the 'uucp' group for serial devices,
        while Debian/Ubuntu use 'dialout'. Your system uses '{serial_group}'.
    """)

    # Check if already in the group
    if user_in_serial_group():
        log_ok(f"You are already in the '{serial_group}' group.")
        return True

    log_warn(f"You are NOT in the '{serial_group}' group.")

    user = os.environ.get("USER", "$USER")
    cmd = f"sudo usermod -aG {serial_group} {user}"
    log_explain(f"This command adds your user to the {serial_group} group:")
    log_code_block(cmd)

    if not prompt_yes_no("Run this command now?"):
        log_info("Skipped. Run it manually when ready.")
        return True

    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        log_error(f"Failed to add user to {serial_group} group.")
        return False

    log_ok(f"Added to {serial_group} group.")
    log_manual(f"""\
IMPORTANT: You must log out and back in for this to take effect.
A new terminal window is NOT enough — you need a full logout/login.

After logging back in, verify with:
  groups | grep {serial_group}""")

    return True


# ── Step 6: VSCode Extensions ────────────────────────────────────────────────

@step(6, "Install VSCode Extensions", "Set up VSCode with C/C++, CMake, Serial Monitor, and debug tools")
def step_vscode():
    log_header("Step 6 — Install VSCode Extensions")

    log_explain("""
        VSCode needs a few extensions to work as a Pico W development IDE:

        - C/C++: IntelliSense, syntax highlighting, debugging support
        - CMake Tools: integrates with CMake to configure and build projects
        - CMake: syntax highlighting for CMakeLists.txt files
        - Serial Monitor: view printf output from the Pico W over USB
        - Cortex-Debug: hardware debugging via SWD (optional, advanced)
    """)

    if not cmd_exists("code"):
        log_warn("VSCode ('code') not found in PATH.")
        log_info("Install it first:")
        distro = detect_distro()
        if distro == "arch":
            log_code_block("sudo pacman -S code")
        elif distro == "debian":
            log_code_block("sudo apt install code\n# or download from https://code.visualstudio.com/")
        else:
            log_code_block("# Download from https://code.visualstudio.com/")
        return prompt_continue() != "quit"

    log_ok("VSCode found in PATH.")

    extensions = [
        ("ms-vscode.cpptools",              "C/C++"),
        ("ms-vscode.cmake-tools",           "CMake Tools"),
        ("twxs.cmake",                      "CMake syntax"),
        ("ms-vscode.vscode-serial-monitor",  "Serial Monitor"),
        ("marus25.cortex-debug",            "Cortex-Debug"),
    ]

    # Check which are already installed
    result = run_cmd(["code", "--list-extensions"])
    installed = set(result.stdout.strip().lower().splitlines()) if result.returncode == 0 else set()

    to_install = []
    for ext_id, ext_name in extensions:
        if ext_id.lower() in installed:
            log_ok(f"{ext_name} ({ext_id}) — already installed")
        else:
            log_info(f"{ext_name} ({ext_id}) — not installed")
            to_install.append((ext_id, ext_name))

    if not to_install:
        log_ok("All extensions already installed.")
        return True

    print()
    if not prompt_yes_no(f"Install {len(to_install)} missing extension(s)?"):
        log_info("Skipped.")
        return True

    for ext_id, ext_name in to_install:
        log_step(f"Installing {ext_name}...")
        with Spinner(f"Installing {ext_name}"):
            result = run_cmd(["code", "--install-extension", ext_id, "--force"])
        if result.returncode == 0:
            log_ok(f"{ext_name} installed")
        else:
            log_warn(f"Failed to install {ext_name}: {result.stderr.strip()}")

    return True


# ── Step 7: Build Hello Serial ────────────────────────────────────────────────

@step(7, "Build Hello World (Serial)", "Compile the serial-only test — no display wiring needed")
def step_build_serial():
    log_header("Step 7 — Checkpoint 1: Build Hello World (Serial Only)")

    log_explain("""
        This is the first real test of your toolchain. We'll compile a tiny
        C program that does three things:

          1. Prints "Hello, Dilder!" over USB serial
          2. Blinks the onboard LED every second
          3. Prints a heartbeat counter

        No display wiring needed — just the Pico W and a USB cable. If this
        builds, flashes, and runs, your entire development pipeline is working.
    """)

    sdk_path = get_sdk_path()

    if not sdk_path.exists():
        log_error(f"Pico SDK not found at {sdk_path}")
        log_info("Go back and run Step 3 first.")
        return False

    # Copy pico_sdk_import.cmake
    import_cmake = sdk_path / "external" / "pico_sdk_import.cmake"
    dest = HELLO_SERIAL / "pico_sdk_import.cmake"

    if not import_cmake.exists():
        log_error(f"Cannot find {import_cmake}")
        log_info("The Pico SDK may be incomplete. Try re-cloning (Step 3).")
        return False

    if not dest.exists():
        shutil.copy2(import_cmake, dest)
        log_ok("Copied pico_sdk_import.cmake into hello-world-serial/")
    else:
        log_ok("pico_sdk_import.cmake already present")

    # Verify source files exist
    if not (HELLO_SERIAL / "main.c").exists():
        log_error(f"main.c not found at {HELLO_SERIAL}")
        return False
    if not (HELLO_SERIAL / "CMakeLists.txt").exists():
        log_error(f"CMakeLists.txt not found at {HELLO_SERIAL}")
        return False

    log_ok("Source files verified: main.c, CMakeLists.txt")

    # Build
    build_dir = HELLO_SERIAL / "build"
    build_dir.mkdir(exist_ok=True)

    log_step("Configuring with CMake...")
    log_cmd(f"cmake -G Ninja -DPICO_SDK_PATH={sdk_path} -DPICO_BOARD=pico_w ..")
    print()

    with Spinner("Running CMake configure"):
        result = run_cmd(
            ["cmake", "-G", "Ninja",
             f"-DPICO_SDK_PATH={sdk_path}",
             "-DPICO_BOARD=pico_w",
             ".."],
            cwd=build_dir
        )

    if result.returncode != 0:
        log_error("CMake configuration failed:")
        output = (result.stderr or "") + (result.stdout or "")
        print(output[-2000:] if len(output) > 2000 else output)
        return False

    log_ok("CMake configured successfully")

    log_step("Building with Ninja...")
    log_cmd("ninja")
    print()

    with Spinner("Compiling hello_serial (first build takes ~30 seconds)"):
        result = run_cmd(["ninja"], cwd=build_dir)

    if result.returncode != 0:
        log_error("Build failed:")
        output = (result.stderr or "") + (result.stdout or "")
        print(output[-2000:] if len(output) > 2000 else output)
        return False

    uf2 = build_dir / "hello_serial.uf2"
    if uf2.exists():
        size_kb = uf2.stat().st_size / 1024
        log_ok(f"Build successful: hello_serial.uf2 ({size_kb:.0f} KB)")
    else:
        log_error("Build completed but .uf2 file not found")
        return False

    return True


# ── Step 8: Flash Hello Serial ────────────────────────────────────────────────

@step(8, "Flash Hello World (Serial)", "Put the Pico W in BOOTSEL mode and flash the firmware")
def step_flash_serial():
    log_header("Step 8 — Flash Hello World (Serial) to the Pico W")

    uf2 = HELLO_SERIAL / "build" / "hello_serial.uf2"
    if not uf2.exists():
        log_error("hello_serial.uf2 not found. Run Step 7 first (build).")
        return False

    log_explain("""
        Flashing means copying the compiled firmware onto the Pico W's
        internal flash memory. The Pico W has a special mode called BOOTSEL
        that makes it appear as a USB drive — you just drag and drop the
        .uf2 file onto it.
    """)

    log_manual("""\
1. UNPLUG the Pico W from USB.
2. HOLD DOWN the BOOTSEL button (small white button on the board).
3. While holding BOOTSEL, PLUG IN the USB cable.
4. RELEASE BOOTSEL after 1 second.

The Pico W should now appear as a USB drive called "RPI-RP2".""")

    # Retry loop — automount can take a few seconds
    while True:
        action = prompt_continue("Press Enter when RPI-RP2 drive appears (or 's' to skip)")
        if action == "quit":
            return False
        if action == "skip":
            return True

        log_step("Searching for RPI-RP2 mount point...")
        mount = find_rpi_rp2_mount()

        if mount is not None:
            break

        log_warn("Could not find the RPI-RP2 drive yet.")
        log_info("The drive may still be mounting. Tips:")
        log_info("  - Wait a few seconds after plugging in, then press Enter again")
        log_info("  - Check that BOOTSEL was held while plugging in USB")
        log_info("  - Try a different USB cable (must be data, not charge-only)")
        log_info("")
        log_info("Or copy manually:")
        log_code_block(f"cp {uf2} /run/media/$USER/RPI-RP2/")

    log_ok(f"Found RPI-RP2 at {mount}")
    log_step("Copying hello_serial.uf2...")
    log_cmd(f"cp {uf2} {mount}/")

    try:
        shutil.copy2(uf2, mount / "hello_serial.uf2")
    except Exception as e:
        log_error(f"Copy failed: {e}")
        return False

    log_ok("Firmware copied! The Pico W will reboot automatically.")
    log_info("The RPI-RP2 drive will disappear — this is normal.")

    return True


# ── Step 9: Verify Serial Output ─────────────────────────────────────────────

@step(9, "Verify Serial Output", "Open a serial monitor and confirm the Pico W is alive")
def step_verify_serial():
    log_header("Step 9 — Verify Serial Output")

    log_explain("""
        After flashing, the Pico W reboots and runs your program. It sends
        printf() output over USB at 115200 baud. Let's verify it's working.
    """)

    # Check if /dev/ttyACM0 exists
    tty = Path("/dev/ttyACM0")
    if tty.exists():
        log_ok(f"{tty} detected — Pico W is connected and running firmware")
    else:
        log_warn(f"{tty} not found.")
        log_info("Possible causes:")
        log_info("  - Pico W not plugged in")
        log_info("  - Using a charge-only USB cable (no data)")
        log_info("  - Firmware crashed before USB initialized")
        log_info("  - Still in BOOTSEL mode (reflash and let it reboot)")

    log_explain("""
        Open a serial monitor to see the output. You have several options:
    """)

    log_info("Option 1 — VSCode Serial Monitor (recommended):")
    log_code_block("""\
Ctrl+Shift+P > "Serial Monitor: Open Serial Monitor"
Port: /dev/ttyACM0
Baud rate: 115200
Click "Start Monitoring" """)

    log_info("Option 2 — Terminal (screen):")
    log_code_block("""\
screen /dev/ttyACM0 115200
# Exit: Ctrl+A, then K, then Y""")

    log_info("Option 3 — Terminal (minicom):")
    log_code_block("""\
minicom -D /dev/ttyACM0 -b 115200
# Exit: Ctrl+A, then X""")

    log_explain("""
        You should see output like this:
    """)

    log_code_block("""\
=========================
  Hello, Dilder!
  Pico W is alive.
=========================

Heartbeat #1  |  LED: ON
Heartbeat #2  |  LED: OFF
Heartbeat #3  |  LED: ON""")

    log_manual("""\
CHECK: The onboard LED should be blinking on and off every second.
CHECK: Serial output shows "Hello, Dilder!" and heartbeat lines.""")

    if prompt_yes_no("Did you see the serial output and LED blinking?"):
        print()
        log_ok("CHECKPOINT 1 COMPLETE")
        log_ok("Your toolchain, build system, flash process, and serial connection all work.")
        log_ok("Everything from here builds on this foundation.")
        return True
    else:
        log_warn("Don't worry — check the troubleshooting section in the setup guide:")
        log_info("  dev-setup/pico-and-display-first-time-setup.md#10-troubleshooting")
        log_info("")
        log_info("Common fixes:")
        log_info("  - Try a different USB cable (must be data, not charge-only)")
        serial_group = detect_serial_group()
        log_info(f"  - Check serial group: groups | grep {serial_group}")
        log_info("  - Reflash: hold BOOTSEL, plug in, copy .uf2 again")
        return True


# ── Step 10: Connect Display ──────────────────────────────────────────────────

@step(10, "Connect the Display", "Slide the Waveshare HAT onto the Pico W headers")
def step_connect_display():
    log_header("Step 10 — Connect the Waveshare e-Ink Display")

    log_explain("""
        The Waveshare 2.13" e-Paper HAT has a female header socket on its
        underside that slides directly onto the Pico W's male header pins.
        No breadboard, no jumper wires — just push it on.
    """)

    log_manual("""\
1. UNPLUG the Pico W from USB.

2. Hold the Pico W with the USB port facing you.

3. Hold the Waveshare HAT with its display FACE UP
   and the 40-pin socket facing DOWN.

4. Align PIN 1 on both boards:
   - Pico W pin 1 = top-left (GP0) when USB faces you
   - The HAT socket has a corresponding pin 1 marking

5. Press DOWN firmly and evenly until the HAT is
   fully seated. No pins should be visible between
   the boards.

   Side view (correct):
   ┌─────────────────────┐  Waveshare HAT
   │  e-ink display       │
   ├─────────────────────┤
   │ female socket ▼▼▼▼  │
   ├═════════════════════┤  <-- flush, no gap
   │ male headers ▲▲▲▲   │
   ├─────────────────────┤
   │  Raspberry Pi Pico W │
   └────────[USB]─────────┘

6. VERIFY before plugging USB back in:
   [ ] HAT fully seated — no pins exposed
   [ ] Pin 1 alignment correct — not offset or rotated
   [ ] FPC ribbon cable not pinched between boards
   [ ] No stray wires or metal touching the boards""")

    log_explain("""
        The HAT routes these signals through its PCB:

        VCC  -> 3V3(OUT) pin 36     DIN  -> GP11 (SPI1 TX) pin 15
        GND  -> GND      pin 38     CLK  -> GP10 (SPI1 SCK) pin 14
        CS   -> GP9      pin 12     DC   -> GP8  pin 11
        RST  -> GP12     pin 16     BUSY -> GP13 pin 17
    """)

    return prompt_continue("Press Enter when the display is connected") != "quit"


# ── Step 11: Get Waveshare Library ────────────────────────────────────────────

@step(11, "Get Waveshare Library", "Download the C display driver and drawing library")
def step_waveshare_lib():
    log_header("Step 11 — Download the Waveshare C Library")

    log_explain("""
        The Waveshare e-Paper library provides the C driver for the SSD1680
        display controller, plus a drawing library (GUI_Paint) for rendering
        text, lines, rectangles, and bitmaps.

        We'll clone the official repo and copy the relevant files into the
        hello-world project.
    """)

    # Check if files already exist
    lib_dir = HELLO_DISPLAY / "lib"
    driver = lib_dir / "e-Paper" / "EPD_2in13_V3.c"

    if driver.exists():
        log_ok("Waveshare library files already present in hello-world/lib/")
        if not prompt_yes_no("Re-download them?", default=False):
            return True

    log_step("Cloning Waveshare Pico_ePaper_Code repository...")

    tmp_dir = Path("/tmp/Pico_ePaper_Code")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

    with Spinner("Cloning Waveshare library"):
        result = run_cmd(
            ["git", "clone", "--depth", "1",
             "https://github.com/waveshare/Pico_ePaper_Code.git",
             str(tmp_dir)]
        )

    if result.returncode != 0:
        log_error("Failed to clone Waveshare library:")
        print(result.stderr)
        return False

    log_ok("Repository cloned")

    # Copy files
    log_step("Copying library files into hello-world/lib/...")

    copies = [
        ("c/lib/Config/DEV_Config.h",    "lib/Config/DEV_Config.h"),
        ("c/lib/Config/DEV_Config.c",    "lib/Config/DEV_Config.c"),
        ("c/lib/Config/Debug.h",         "lib/Config/Debug.h"),
        ("c/lib/e-Paper/EPD_2in13_V3.h", "lib/e-Paper/EPD_2in13_V3.h"),
        ("c/lib/e-Paper/EPD_2in13_V3.c", "lib/e-Paper/EPD_2in13_V3.c"),
        ("c/lib/GUI/GUI_Paint.h",        "lib/GUI/GUI_Paint.h"),
        ("c/lib/GUI/GUI_Paint.c",        "lib/GUI/GUI_Paint.c"),
        ("c/lib/Fonts/fonts.h",          "lib/Fonts/fonts.h"),
        ("c/lib/Fonts/font8.c",          "lib/Fonts/font8.c"),
        ("c/lib/Fonts/font12.c",         "lib/Fonts/font12.c"),
        ("c/lib/Fonts/font16.c",         "lib/Fonts/font16.c"),
        ("c/lib/Fonts/font20.c",         "lib/Fonts/font20.c"),
        ("c/lib/Fonts/font24.c",         "lib/Fonts/font24.c"),
    ]

    for src_rel, dst_rel in copies:
        src = tmp_dir / src_rel
        dst = HELLO_DISPLAY / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, dst)
        else:
            log_warn(f"Source file not found: {src}")

    # Copy pico_sdk_import.cmake
    sdk_path = get_sdk_path()
    import_cmake = sdk_path / "external" / "pico_sdk_import.cmake"
    dest = HELLO_DISPLAY / "pico_sdk_import.cmake"
    if import_cmake.exists() and not dest.exists():
        shutil.copy2(import_cmake, dest)
        log_ok("Copied pico_sdk_import.cmake")

    # Clean up
    shutil.rmtree(tmp_dir, ignore_errors=True)

    log_ok("Library files copied:")
    for _, dst_rel in copies:
        log_info(f"  {dst_rel}")

    return True


# ── Step 12: Build Hello Display ──────────────────────────────────────────────

@step(12, "Build Hello World (Display)", "Compile the e-ink display test program")
def step_build_display():
    log_header("Step 12 — Checkpoint 2: Build Hello World (e-Ink Display)")

    log_explain("""
        This program draws text on the e-ink display:

          - A black border rectangle around the edges
          - "Hello, Dilder!" in 24px font
          - "Pico W + e-Paper V3" in 16px font
          - "First build successful!" in 12px font

        It also prints status messages to USB serial so you can monitor
        the initialization process.
    """)

    sdk_path = get_sdk_path()

    # Check library files
    driver = HELLO_DISPLAY / "lib" / "e-Paper" / "EPD_2in13_V3.c"
    if not driver.exists():
        log_error("Waveshare library not found. Run Step 11 first.")
        return False

    if not (HELLO_DISPLAY / "pico_sdk_import.cmake").exists():
        import_cmake = sdk_path / "external" / "pico_sdk_import.cmake"
        if import_cmake.exists():
            shutil.copy2(import_cmake, HELLO_DISPLAY / "pico_sdk_import.cmake")
        else:
            log_error("pico_sdk_import.cmake not found.")
            return False

    build_dir = HELLO_DISPLAY / "build"
    build_dir.mkdir(exist_ok=True)

    log_step("Configuring with CMake...")
    print()

    with Spinner("Running CMake configure"):
        result = run_cmd(
            ["cmake", "-G", "Ninja",
             f"-DPICO_SDK_PATH={sdk_path}",
             "-DPICO_BOARD=pico_w",
             ".."],
            cwd=build_dir
        )

    if result.returncode != 0:
        log_error("CMake configuration failed:")
        output = (result.stderr or "") + (result.stdout or "")
        print(output[-2000:] if len(output) > 2000 else output)
        return False

    log_ok("CMake configured")

    log_step("Building with Ninja...")
    print()

    with Spinner("Compiling hello_dilder"):
        result = run_cmd(["ninja"], cwd=build_dir)

    if result.returncode != 0:
        log_error("Build failed:")
        output = (result.stderr or "") + (result.stdout or "")
        print(output[-2000:] if len(output) > 2000 else output)
        return False

    uf2 = build_dir / "hello_dilder.uf2"
    if uf2.exists():
        size_kb = uf2.stat().st_size / 1024
        log_ok(f"Build successful: hello_dilder.uf2 ({size_kb:.0f} KB)")
    else:
        log_error("Build completed but .uf2 file not found")
        return False

    return True


# ── Step 13: Flash Hello Display ──────────────────────────────────────────────

@step(13, "Flash Hello World (Display)", "Flash the display firmware to the Pico W")
def step_flash_display():
    log_header("Step 13 — Flash Hello World (Display)")

    uf2 = HELLO_DISPLAY / "build" / "hello_dilder.uf2"
    if not uf2.exists():
        log_error("hello_dilder.uf2 not found. Run Step 12 first.")
        return False

    log_manual("""\
1. UNPLUG the Pico W from USB.
   (The display stays attached — that's fine.)

2. HOLD DOWN the BOOTSEL button.
   The button is on the Pico W — you may need to reach
   under or around the display HAT to press it.

3. While holding BOOTSEL, PLUG IN the USB cable.

4. RELEASE BOOTSEL after 1 second.

The RPI-RP2 USB drive should appear.""")

    while True:
        action = prompt_continue("Press Enter when RPI-RP2 drive appears (or 's' to skip)")
        if action == "quit":
            return False
        if action == "skip":
            return True

        log_step("Searching for RPI-RP2 mount point...")
        mount = find_rpi_rp2_mount()

        if mount is not None:
            break

        log_warn("Could not find the RPI-RP2 drive yet.")
        log_info("Wait a few seconds and press Enter again, or copy manually:")
        log_code_block(f"cp {uf2} /run/media/$USER/RPI-RP2/")

    log_ok(f"Found RPI-RP2 at {mount}")
    log_step("Copying hello_dilder.uf2...")

    try:
        shutil.copy2(uf2, mount / "hello_dilder.uf2")
    except Exception as e:
        log_error(f"Copy failed: {e}")
        return False

    log_ok("Firmware flashed! Pico W will reboot with the display program.")

    return True


# ── Step 14: Verify Display ──────────────────────────────────────────────────

@step(14, "Verify Display Output", "Confirm text appears on the e-ink display")
def step_verify_display():
    log_header("Step 14 — Verify Display Output")

    log_explain("""
        After flashing, the Pico W reboots and runs the display program.
        It initializes SPI, clears the display, draws text, then enters
        a heartbeat loop on serial.
    """)

    log_info("Serial output should show:")
    log_code_block("""\
Hello, Dilder!
Initializing e-Paper display...
Display initialized.
Drawing to display...
Display updated. Entering sleep mode.
Heartbeat: 1
Heartbeat: 2""")

    log_manual("""\
CHECK the e-ink display. You should see:

  ┌──────────────────────────────────┐
  │                                  │
  │  Hello, Dilder!        (24px)    │
  │                                  │
  │  Pico W + e-Paper V3   (16px)   │
  │                                  │
  │  First build successful! (12px)  │
  │                                  │
  └──────────────────────────────────┘

The display retains the image even when powered off.""")

    if prompt_yes_no("Did text appear on the e-ink display?"):
        print()
        print(c("  ┌────────────────────────────────────────────────────────────┐", FG_GREEN, BOLD))
        print(c("  │                                                            │", FG_GREEN, BOLD))
        print(c("  │           CHECKPOINT 2 COMPLETE — SETUP FINISHED           │", FG_GREEN, BOLD))
        print(c("  │                                                            │", FG_GREEN, BOLD))
        print(c("  │   Your Pico W C development environment is fully working.  │", FG_GREEN, BOLD))
        print(c("  │   Toolchain, build system, flash, serial, and display      │", FG_GREEN, BOLD))
        print(c("  │   are all verified.                                        │", FG_GREEN, BOLD))
        print(c("  │                                                            │", FG_GREEN, BOLD))
        print(c("  └────────────────────────────────────────────────────────────┘", FG_GREEN, BOLD))
        print()
        log_info("Next steps:")
        log_info("  - Modify main.c, rebuild with 'ninja', and reflash")
        log_info("  - Wire the 5 tactile buttons for input")
        log_info("  - Start building the Dilder pet firmware")
        return True
    else:
        log_warn("Troubleshooting tips:")
        log_info("  - Display blank? Check HAT is fully seated on the headers")
        log_info("  - Garbage pixels? Confirm V3 on PCB silkscreen (not V4)")
        log_info("  - Flickers then blank? Reseat the HAT — may be loose")
        log_info("  - Check serial output for error messages")
        log_info("  - Full troubleshooting: dev-setup/pico-and-display-first-time-setup.md")
        return True


# ─────────────────────────────────────────────────────────────────────────────
# Status command
# ─────────────────────────────────────────────────────────────────────────────

def show_status():
    """Show the current state of the setup."""
    log_header("Dilder Setup Status")

    # Toolchain
    print(c("  Toolchain", FG_WHITE, BOLD))
    print(c("  " + "\u2500" * 50, FG_GREY))

    if cmd_exists("arm-none-eabi-gcc"):
        result = run_cmd(["arm-none-eabi-gcc", "--version"])
        line = result.stdout.strip().splitlines()[0] if result.returncode == 0 else "found"
        log_ok(f"ARM GCC: {line}")
    else:
        log_error("ARM GCC: not installed")

    if cmd_exists("cmake"):
        log_ok("CMake: installed")
    else:
        log_error("CMake: not installed")

    if cmd_exists("ninja"):
        log_ok("Ninja: installed")
    else:
        log_error("Ninja: not installed")

    # SDK
    print()
    print(c("  Pico SDK", FG_WHITE, BOLD))
    print(c("  " + "\u2500" * 50, FG_GREY))

    sdk_path = get_sdk_path()
    env_set = os.environ.get("PICO_SDK_PATH")
    if env_set:
        log_ok(f"PICO_SDK_PATH: {env_set}")
    else:
        log_warn("PICO_SDK_PATH: not set in environment")

    if sdk_path.exists() and (sdk_path / "src").exists():
        log_ok(f"SDK directory: {sdk_path}")
    else:
        log_error(f"SDK directory: not found at {sdk_path}")

    # Permissions
    print()
    print(c("  Permissions", FG_WHITE, BOLD))
    print(c("  " + "\u2500" * 50, FG_GREY))

    serial_group = detect_serial_group()
    if user_in_serial_group():
        log_ok(f"User in '{serial_group}' group")
    else:
        log_warn(f"User NOT in '{serial_group}' group")

    # VSCode
    print()
    print(c("  VSCode", FG_WHITE, BOLD))
    print(c("  " + "\u2500" * 50, FG_GREY))

    if cmd_exists("code"):
        log_ok("VSCode: installed")
        result = run_cmd(["code", "--list-extensions"])
        installed = set(result.stdout.strip().lower().splitlines()) if result.returncode == 0 else set()
        exts = [
            ("ms-vscode.cpptools", "C/C++"),
            ("ms-vscode.cmake-tools", "CMake Tools"),
            ("ms-vscode.vscode-serial-monitor", "Serial Monitor"),
        ]
        for ext_id, name in exts:
            if ext_id.lower() in installed:
                log_ok(f"  {name}")
            else:
                log_warn(f"  {name}: not installed")
    else:
        log_warn("VSCode: not found")

    # Builds
    print()
    print(c("  Builds", FG_WHITE, BOLD))
    print(c("  " + "\u2500" * 50, FG_GREY))

    serial_uf2 = HELLO_SERIAL / "build" / "hello_serial.uf2"
    if serial_uf2.exists():
        size = serial_uf2.stat().st_size / 1024
        log_ok(f"hello_serial.uf2: {size:.0f} KB")
    else:
        log_info("hello_serial.uf2: not built")

    display_uf2 = HELLO_DISPLAY / "build" / "hello_dilder.uf2"
    if display_uf2.exists():
        size = display_uf2.stat().st_size / 1024
        log_ok(f"hello_dilder.uf2: {size:.0f} KB")
    else:
        log_info("hello_dilder.uf2: not built")

    # Hardware
    print()
    print(c("  Hardware", FG_WHITE, BOLD))
    print(c("  " + "\u2500" * 50, FG_GREY))

    if Path("/dev/ttyACM0").exists():
        log_ok("Pico W detected on /dev/ttyACM0")
    else:
        log_info("Pico W not connected (or in BOOTSEL mode)")

    print()


# ─────────────────────────────────────────────────────────────────────────────
# List steps
# ─────────────────────────────────────────────────────────────────────────────

def list_steps():
    """Print all steps with their status."""
    log_header("Setup Steps")

    for s in STEPS:
        num = s["number"]
        title = s["title"]
        desc = s["desc"]
        print(f"  {c(f'Step {num:2d}', FG_CYAN, BOLD)}  {c(title, FG_WHITE)}")
        print(c(f"           {desc}", FG_GREY))
        print()


# ─────────────────────────────────────────────────────────────────────────────
# Main walkthrough
# ─────────────────────────────────────────────────────────────────────────────

def run_walkthrough(start_step: int = 1):
    """Run the interactive step-by-step setup."""

    for s in STEPS:
        if s["number"] < start_step:
            continue

        num = s["number"]
        title = s["title"]
        total = len(STEPS)

        # Step banner
        print()
        bar = "\u2500" * 58
        print(c(f"  {bar}", FG_GREY))
        progress = f"Step {num}/{total}"
        print(c(f"  {progress:>10}  ", FG_CYAN, BOLD) + c(title, FG_WHITE, BOLD))
        print(c(f"  {bar}", FG_GREY))

        result = s["fn"]()

        if result is False:
            log_warn(f"Step {num} reported an issue.")
            action = prompt_continue("Press Enter to continue anyway, 's' to skip, 'q' to quit")
            if action == "quit":
                print()
                log_info(f"Stopped at Step {num}. Resume later with: python3 setup.py --step {num}")
                return
            continue

        # Ask before continuing to next step
        if s["number"] < total:
            next_step = STEPS[STEPS.index(s) + 1] if STEPS.index(s) + 1 < len(STEPS) else None
            if next_step:
                print()
                print(c(f"  Next: Step {next_step['number']} — {next_step['title']}", FG_GREY))
                action = prompt_continue("Press Enter to continue (or 'q' to quit)")
                if action == "quit":
                    print()
                    log_info(f"Resume later with: python3 setup.py --step {next_step['number']}")
                    return

    # All done
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

BANNER = """\
  ██████╗ ██╗██╗     ██████╗ ███████╗██████╗
  ██╔══██╗██║██║     ██╔══██╗██╔════╝██╔══██╗
  ██║  ██║██║██║     ██║  ██║█████╗  ██████╔╝
  ██║  ██║██║██║     ██║  ██║██╔══╝  ██╔══██╗
  ██████╔╝██║███████╗██████╔╝███████╗██║  ██║
  ╚═════╝ ╚═╝╚══════╝╚═════╝ ╚══════╝╚═╝  ╚═╝"""


def main():
    parser = argparse.ArgumentParser(
        prog="setup.py",
        description="Dilder — Pico W & Display First-Time Setup CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  python3 setup.py              # full interactive walkthrough
  python3 setup.py --status     # check what's installed
  python3 setup.py --step 7     # jump to step 7 (build serial hello world)
  python3 setup.py --list       # show all steps
""",
    )
    parser.add_argument("--status", action="store_true",
                        help="Show current setup state")
    parser.add_argument("--step", type=int, metavar="N",
                        help="Jump to step N")
    parser.add_argument("--list", action="store_true",
                        help="List all setup steps")

    args = parser.parse_args()

    # Banner
    if not NO_COLOUR:
        print()
        for i, line in enumerate(BANNER.splitlines()):
            color = FG_CYAN if i % 2 == 0 else FG_BLUE
            print(c(line, color, BOLD))
        print(c("  Pico W & Display — First-Time Setup", FG_GREY))
        print(c(f"  Project: {PROJECT_ROOT}", FG_GREY, DIM))
    else:
        print("\nDILDER — Pico W & Display First-Time Setup\n")

    if args.status:
        show_status()
        return

    if args.list:
        list_steps()
        return

    start = args.step if args.step else 1

    if start < 1 or start > len(STEPS):
        log_error(f"Invalid step number. Valid range: 1-{len(STEPS)}")
        sys.exit(1)

    log_explain(f"""
        This script walks you through the complete first-time setup for
        Pico W development with the Waveshare e-ink display, using C and
        the official Pico SDK.

        It will:
          1. Install the ARM cross-compilation toolchain
          2. Clone the Pico SDK
          3. Configure your shell and permissions
          4. Set up VSCode with the right extensions
          5. Build and flash a serial "Hello World" (Checkpoint 1)
          6. Connect the display and build a display "Hello World" (Checkpoint 2)

        At each step, you'll see an explanation of what's happening and why.
        You can skip any step, quit at any time, and resume later with:
          python3 setup.py --step N

        {"Starting from Step " + str(start) + "." if start > 1 else "Let's begin."}
    """)

    action = prompt_continue("Press Enter to start")
    if action == "quit":
        return

    run_walkthrough(start)


if __name__ == "__main__":
    main()
