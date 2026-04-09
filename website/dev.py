#!/usr/bin/env python3
"""
Dilder website dev CLI.

Run with no arguments for the interactive menu.
Pass a command directly to skip the menu (useful for CI/scripts).

Usage:
  python3 dev.py                          # interactive menu
  python3 dev.py <command> [options]      # direct invocation

Commands:
  install   Create venv and install dependencies
  serve     Start local dev server (hot-reload)
  build     Build static site to site/
  deploy    Deploy to GitHub Pages (gh-deploy)
  clean     Remove the site/ build output
  check     Verify prerequisites
  status    Show project environment status
"""

import argparse
import os
import platform
import select
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Terminal / colour helpers
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

NO_COLOUR = bool(os.environ.get("NO_COLOR")) or not sys.stdout.isatty()


def c(text: str, *codes: str) -> str:
    if NO_COLOUR:
        return text
    return "".join(codes) + text + RESET


def icon(sym: str) -> str:
    if platform.system() == "Windows":
        return {"✓": "[OK]", "✗": "[FAIL]", "→": "->",
                "⚙": "[*]",  "⚠": "[!]",   "●": "[.]"}.get(sym, sym)
    return sym


# ─────────────────────────────────────────────────────────────────────────────
# Logging helpers
# ─────────────────────────────────────────────────────────────────────────────

def log_header(title: str) -> None:
    width = 60
    bar = "─" * width
    print()
    print(c(f"┌{bar}┐", FG_BLUE, BOLD))
    print(c(f"│{title.center(width)}│", FG_BLUE, BOLD))
    print(c(f"└{bar}┘", FG_BLUE, BOLD))
    print()


def log_step(msg: str) -> None:
    print(c(f"  {icon('→')} {msg}", FG_CYAN))


def log_ok(msg: str) -> None:
    print(c(f"  {icon('✓')} {msg}", FG_GREEN))


def log_warn(msg: str) -> None:
    print(c(f"  {icon('⚠')} {msg}", FG_YELLOW))


def log_error(msg: str) -> None:
    print(c(f"  {icon('✗')} {msg}", FG_RED, BOLD), file=sys.stderr)


def log_info(msg: str) -> None:
    print(c(f"  {icon('●')} {msg}", FG_GREY))


def log_section(title: str) -> None:
    print()
    print(c(f"  {BOLD}{title}", FG_WHITE))
    print(c(f"  {'─' * len(title)}", FG_GREY))


# ─────────────────────────────────────────────────────────────────────────────
# Spinner
# ─────────────────────────────────────────────────────────────────────────────

class Spinner:
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

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
# Paths
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent.resolve()
VENV_DIR     = SCRIPT_DIR / "venv"
REQUIREMENTS = SCRIPT_DIR / "requirements.txt"
MKDOCS_YML   = SCRIPT_DIR / "mkdocs.yml"
SITE_DIR     = SCRIPT_DIR / "site"

IS_WINDOWS = platform.system() == "Windows"
VENV_BIN   = VENV_DIR / ("Scripts" if IS_WINDOWS else "bin")
PYTHON_EXE = VENV_BIN / ("python.exe" if IS_WINDOWS else "python")
MKDOCS_EXE = VENV_BIN / ("mkdocs.exe" if IS_WINDOWS else "mkdocs")
PIP_EXE    = VENV_BIN / ("pip.exe"    if IS_WINDOWS else "pip")


# ─────────────────────────────────────────────────────────────────────────────
# Subprocess helpers
# ─────────────────────────────────────────────────────────────────────────────

def run(cmd: list, stream: bool = False, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    kwargs: dict = dict(cwd=cwd or SCRIPT_DIR)
    if stream:
        return subprocess.run(cmd, **kwargs)
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def require_venv() -> None:
    if not PYTHON_EXE.exists():
        log_error("Virtual environment not found. Run install first.")
        sys.exit(1)


def require_mkdocs_yml() -> None:
    if not MKDOCS_YML.exists():
        log_error(f"mkdocs.yml not found in {SCRIPT_DIR}")
        sys.exit(1)


def python_version_ok() -> bool:
    return sys.version_info >= (3, 9)


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

def cmd_check(args) -> None:
    log_header("Prerequisite Check")
    all_ok = True
    has_warnings = False

    ver = platform.python_version()
    if python_version_ok():
        log_ok(f"Python {ver}")
    else:
        log_error(f"Python {ver} — need 3.9+")
        all_ok = False

    pip_path = shutil.which("pip3") or shutil.which("pip")
    if pip_path:
        log_ok(f"pip  {pip_path}")
    else:
        log_warn("pip not found — install Python with pip")
        all_ok = False

    git_path = shutil.which("git")
    if git_path:
        result = run(["git", "--version"])
        log_ok(result.stdout.strip() if result.returncode == 0 else "git found")
    else:
        log_warn("git not found — needed for deploy")
        all_ok = False

    if VENV_DIR.exists() and PYTHON_EXE.exists():
        result = run([str(PYTHON_EXE), "--version"])
        log_ok(f"venv OK — {result.stdout.strip()}")
    else:
        log_warn("venv not found — run install")
        has_warnings = True

    if MKDOCS_EXE.exists():
        result = run([str(MKDOCS_EXE), "--version"])
        log_ok(f"mkdocs — {result.stdout.strip()}")
    else:
        log_warn("mkdocs not installed — run install")
        has_warnings = True

    if MKDOCS_YML.exists():
        log_ok("mkdocs.yml present")
    else:
        log_error("mkdocs.yml missing")
        all_ok = False

    if SITE_DIR.exists():
        log_info(f"site/ exists — {len(list(SITE_DIR.rglob('*.html')))} pages")
    else:
        log_info("site/ not built yet")

    print()
    if not all_ok:
        log_warn("Some checks failed. Run install to fix.")
    elif has_warnings:
        log_warn("Not ready — run install.")
    else:
        log_ok("All checks passed — ready to serve.")
    print()


def cmd_install(args) -> None:
    log_header("Install")

    if not python_version_ok():
        log_error(f"Python {platform.python_version()} is too old. Need 3.9+.")
        sys.exit(1)

    if VENV_DIR.exists():
        log_ok("venv already exists — skipping creation")
    else:
        log_step("Creating virtual environment…")
        with Spinner("Creating venv"):
            result = run([sys.executable, "-m", "venv", str(VENV_DIR)])
        if result.returncode != 0:
            log_error("Failed to create venv")
            print(result.stderr)
            sys.exit(1)
        log_ok("venv created")

    log_step("Upgrading pip…")
    with Spinner("Upgrading pip"):
        run([str(PYTHON_EXE), "-m", "pip", "install", "--upgrade", "pip", "-q"])
    log_ok("pip up to date")

    if REQUIREMENTS.exists():
        log_step("Installing from requirements.txt…")
        with Spinner("Installing packages"):
            result = run([str(PIP_EXE), "install", "-r", str(REQUIREMENTS), "-q"])
    else:
        log_step("No requirements.txt — installing mkdocs-material…")
        with Spinner("Installing mkdocs-material"):
            result = run([str(PIP_EXE), "install", "mkdocs-material", "-q"])

    if result.returncode != 0:
        log_error("Package installation failed")
        print(result.stderr)
        sys.exit(1)
    log_ok("Packages installed")

    if not REQUIREMENTS.exists():
        log_step("Generating requirements.txt…")
        result = run([str(PIP_EXE), "freeze"])
        if result.returncode == 0:
            REQUIREMENTS.write_text(result.stdout)
            log_ok(f"requirements.txt written")

    result = run([str(MKDOCS_EXE), "--version"])
    log_ok(f"Ready — {result.stdout.strip()}")
    print()


def cmd_serve(args) -> None:
    require_venv()
    require_mkdocs_yml()

    port = getattr(args, "port", 8000)
    host = getattr(args, "host", "127.0.0.1")
    strict = getattr(args, "strict", False)

    log_header("Local Dev Server")
    log_step(f"Starting MkDocs on http://{host}:{port}")
    log_info("Press Ctrl+C to stop")
    print()

    cmd = [str(MKDOCS_EXE), "serve", "--dev-addr", f"{host}:{port}"]
    if strict:
        cmd.append("--strict")

    try:
        run(cmd, stream=True)
    except KeyboardInterrupt:
        print()
        log_ok("Server stopped.")
        print()


def cmd_build(args) -> None:
    require_venv()
    require_mkdocs_yml()

    strict = getattr(args, "strict", False)
    clean  = getattr(args, "clean",  False)

    log_header("Build")
    log_step("Building static site…")

    cmd = [str(MKDOCS_EXE), "build"]
    if strict:
        cmd.append("--strict")
    if clean:
        cmd.append("--clean")

    start = time.time()
    with Spinner("Building"):
        result = run(cmd, stream=False)
    elapsed = time.time() - start

    if result.returncode != 0:
        log_error("Build failed")
        print()
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)

    page_count = len(list(SITE_DIR.rglob("*.html"))) if SITE_DIR.exists() else 0
    log_ok(f"Build complete in {elapsed:.1f}s — {page_count} pages → site/")
    print()


def cmd_deploy(args) -> None:
    require_venv()
    require_mkdocs_yml()

    yes     = getattr(args, "yes",     False)
    message = getattr(args, "message", None)

    if not yes:
        print()
        log_warn("This will push to the gh-pages branch on GitHub.")
        answer = input(c("  Continue? [y/N] ", FG_YELLOW)).strip().lower()
        if answer not in ("y", "yes"):
            log_info("Aborted.")
            print()
            return

    log_header("Deploy → GitHub Pages")
    log_step("Running mkdocs gh-deploy…")
    print()

    cmd = [str(MKDOCS_EXE), "gh-deploy", "--force"]
    if message:
        cmd += ["--message", message]

    result = run(cmd, stream=True)
    print()

    if result.returncode == 0:
        log_ok("Deployed successfully.")
        log_info("Site will update on GitHub Pages in ~1 minute.")
        log_info("github.com/rompasaurus/dilder/actions")
    else:
        log_error("Deploy failed.")
        sys.exit(1)
    print()


def cmd_clean(args) -> None:
    log_header("Clean")

    if not SITE_DIR.exists():
        log_info("site/ does not exist — nothing to clean.")
        print()
        return

    page_count = len(list(SITE_DIR.rglob("*.html")))
    log_step(f"Removing site/ ({page_count} HTML files)…")
    shutil.rmtree(SITE_DIR)
    log_ok("site/ removed.")
    print()


def cmd_status(args) -> None:
    log_header("Dilder Dev Status")

    log_section("Environment")
    log_info(f"Script dir : {SCRIPT_DIR}")
    log_info(f"Python     : {platform.python_version()} ({sys.executable})")
    log_info(f"Platform   : {platform.system()} {platform.release()}")

    log_section("Venv")
    if VENV_DIR.exists():
        log_ok(f"venv at {VENV_DIR}")
        if MKDOCS_EXE.exists():
            result = run([str(MKDOCS_EXE), "--version"])
            log_ok(result.stdout.strip())
        else:
            log_warn("mkdocs not installed in venv")
    else:
        log_warn("No venv — run install")

    log_section("Site")
    if MKDOCS_YML.exists():
        log_ok("mkdocs.yml present")
    else:
        log_error("mkdocs.yml missing")

    if SITE_DIR.exists():
        page_count = len(list(SITE_DIR.rglob("*.html")))
        size_mb = sum(f.stat().st_size for f in SITE_DIR.rglob("*") if f.is_file()) / 1_048_576
        log_ok(f"site/ built — {page_count} pages, {size_mb:.1f}MB")
    else:
        log_info("site/ not built")

    log_section("Content")
    docs_dir = SCRIPT_DIR / "docs"
    if docs_dir.exists():
        md_files   = list(docs_dir.rglob("*.md"))
        blog_posts = list((docs_dir / "blog" / "posts").rglob("*.md"))
        log_ok(f"{len(md_files)} Markdown pages total")
        log_ok(f"{len(blog_posts)} blog posts")
    else:
        log_warn("docs/ directory not found")

    log_section("Git")
    result = run(["git", "status", "--short"])
    if result.returncode == 0:
        changed = result.stdout.strip().splitlines()
        if changed:
            log_warn(f"{len(changed)} uncommitted changes")
        else:
            log_ok("Working tree clean")
        result = run(["git", "log", "--oneline", "-5"])
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                log_info(line)
    else:
        log_warn("Not a git repo or git not available")

    print()


# ─────────────────────────────────────────────────────────────────────────────
# Interactive menu
# ─────────────────────────────────────────────────────────────────────────────

# Try to import Unix tty/termios; fall back gracefully on Windows
try:
    import tty as _tty
    import termios as _termios
    _HAS_TTY = True
except ImportError:
    _HAS_TTY = False

try:
    import msvcrt as _msvcrt
    _HAS_MSVCRT = True
except ImportError:
    _HAS_MSVCRT = False

# ANSI cursor codes
_CUP  = "\033[{}A"   # cursor up N lines
_EOS  = "\033[J"     # erase from cursor to end of screen
_HIDE = "\033[?25l"  # hide cursor
_SHOW = "\033[?25h"  # show cursor

# Key constants (raw bytes)
_UP    = b"\x1b[A"
_DOWN  = b"\x1b[B"
_ENTER = (b"\r", b"\n", b" ")
_QUIT  = (b"q", b"Q", b"\x03")   # q, Q, Ctrl-C


def _read_key() -> bytes:
    """Block until a keypress and return its raw bytes."""
    if _HAS_TTY and sys.stdin.isatty():
        fd = sys.stdin.fileno()
        old = _termios.tcgetattr(fd)
        try:
            _tty.setraw(fd)
            ch = os.read(fd, 1)
            if ch == b"\x1b":
                # read the rest of the escape sequence (50 ms window)
                r, _, _ = select.select([fd], [], [], 0.05)
                if r:
                    ch += os.read(fd, 2)
        finally:
            _termios.tcsetattr(fd, _termios.TCSADRAIN, old)
        return ch
    elif _HAS_MSVCRT:
        ch = _msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):
            ch2 = _msvcrt.getch()
            if ch2 == b"H": return _UP
            if ch2 == b"P": return _DOWN
            return b"\x00"
        return ch
    else:
        line = sys.stdin.readline().strip().encode()
        return line[:1] if line else b"\n"


# Menu item definitions -------------------------------------------------------

_ITEMS = [
    dict(name="install", desc="Create venv and install MkDocs Material",
         fn=cmd_install, args=argparse.Namespace()),
    dict(name="serve",   desc="Start hot-reload dev server on localhost:8000",
         fn=cmd_serve,   args=argparse.Namespace(port=8000, host="127.0.0.1", strict=False)),
    dict(name="build",   desc="Build static site to site/",
         fn=cmd_build,   args=argparse.Namespace(strict=False, clean=False)),
    dict(name="deploy",  desc="Push site to GitHub Pages (asks to confirm)",
         fn=cmd_deploy,  args=argparse.Namespace(message=None, yes=False)),
    dict(name="clean",   desc="Delete the site/ build output",
         fn=cmd_clean,   args=argparse.Namespace()),
    dict(name="check",   desc="Verify all prerequisites",
         fn=cmd_check,   args=argparse.Namespace()),
    dict(name="status",  desc="Show full project environment status",
         fn=cmd_status,  args=argparse.Namespace()),
    dict(name="quit",    desc="Exit",
         fn=None,        args=None),
]

# Must match the exact number of print() calls inside _draw_menu()
_MENU_HEIGHT = 16


def _draw_menu(items: list, selected: int) -> None:
    """Print the interactive menu. Always prints exactly _MENU_HEIGHT lines."""

    SEP = c("  " + "─" * 56, FG_GREY)

    # ── header separator ─────────────────────────────────── line 1–3
    print()
    print(SEP)
    print()

    # ── item rows ────────────────────────────────────────── lines 4–11
    for i, item in enumerate(items):
        is_sel  = (i == selected)
        is_quit = (item["name"] == "quit")

        if is_sel:
            cursor   = c(" ▶ ", FG_CYAN, BOLD)
            name_str = c(f"{item['name']:<10}", FG_CYAN, BOLD)
            desc_str = c(item["desc"], FG_WHITE)
        elif is_quit:
            cursor   = "   "
            name_str = c(f"{item['name']:<10}", FG_GREY, DIM)
            desc_str = c(item["desc"], FG_GREY, DIM)
        else:
            cursor   = "   "
            name_str = c(f"{item['name']:<10}", FG_WHITE)
            desc_str = c(item["desc"], FG_GREY)

        print(f"  {cursor}{name_str}  {desc_str}")

    # ── footer ───────────────────────────────────────────── lines 12–16
    print()

    # env status badges
    venv_badge = (c("venv ✓", FG_GREEN)  if PYTHON_EXE.exists()
                  else c("venv ○", FG_YELLOW))
    site_badge = (c("site ✓", FG_GREEN)  if SITE_DIR.exists()
                  else c("site ○", FG_GREY))

    hints = (
        c("  ↑↓", FG_CYAN) + c(" navigate   ", FG_GREY) +
        c("enter", FG_CYAN) + c(" run   ", FG_GREY) +
        c("q", FG_CYAN) + c(" quit", FG_GREY)
    )

    print(SEP)
    print(f"{hints}          {venv_badge}  {site_badge}")
    print()

    # description of selected item (always last — line 16)
    print(c(f"  {items[selected]['desc']}", FG_CYAN))


def run_menu() -> None:
    """Launch the interactive arrow-key selection menu."""
    selected    = 0
    from_scratch = True  # first draw — don't attempt to move cursor up

    if not NO_COLOUR:
        sys.stdout.write(_HIDE)
        sys.stdout.flush()

    try:
        while True:
            if from_scratch:
                _draw_menu(_ITEMS, selected)
                from_scratch = False
            else:
                # move up and erase previous menu, then redraw in-place
                sys.stdout.write(f"\033[{_MENU_HEIGHT}A\033[J")
                sys.stdout.flush()
                _draw_menu(_ITEMS, selected)

            key = _read_key()

            if key == _UP:
                selected = (selected - 1) % len(_ITEMS)

            elif key == _DOWN:
                selected = (selected + 1) % len(_ITEMS)

            elif key in _ENTER:
                item = _ITEMS[selected]

                if item["fn"] is None:          # quit item
                    break

                # clear menu area before running
                sys.stdout.write(f"\033[{_MENU_HEIGHT}A\033[J")
                sys.stdout.flush()

                # restore cursor visibility while command runs
                if not NO_COLOUR:
                    sys.stdout.write(_SHOW)
                    sys.stdout.flush()

                item["fn"](item["args"])

                print()
                print(c("  ↩  press any key to return to menu…", FG_GREY),
                      end="", flush=True)
                _read_key()
                print("\n")

                if not NO_COLOUR:
                    sys.stdout.write(_HIDE)
                    sys.stdout.flush()

                from_scratch = True             # redraw fresh after output

            elif key in _QUIT:
                break

    except KeyboardInterrupt:
        pass
    finally:
        if not NO_COLOUR:
            sys.stdout.write(_SHOW)
            sys.stdout.flush()
        print()


# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing  (direct CLI — skips the menu)
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dev.py",
        description="Dilder website dev CLI  (run with no args for interactive menu)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
commands:
  check     Verify prerequisites
  install   Create venv and install dependencies
  serve     Start local hot-reload dev server
  build     Build static site to site/
  deploy    Deploy to GitHub Pages
  clean     Remove site/ build output
  status    Show project environment status

examples:
  python3 dev.py                              # interactive menu
  python3 dev.py serve --port 9000
  python3 dev.py build --strict
  python3 dev.py deploy -m "Add Phase 2" -y
""",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    sub.add_parser("check",   help="Verify prerequisites")
    sub.add_parser("install", help="Create venv and install dependencies")
    sub.add_parser("clean",   help="Remove site/ build output")
    sub.add_parser("status",  help="Show project environment status")

    p = sub.add_parser("serve", help="Start local dev server")
    p.add_argument("--port",   type=int, default=8000,        help="Port (default: 8000)")
    p.add_argument("--host",   default="127.0.0.1",           help="Host (default: 127.0.0.1)")
    p.add_argument("--strict", action="store_true",           help="Treat warnings as errors")

    p = sub.add_parser("build", help="Build static site to site/")
    p.add_argument("--strict", action="store_true",           help="Treat warnings as errors")
    p.add_argument("--clean",  action="store_true",           help="Remove site/ before building")

    p = sub.add_parser("deploy", help="Deploy to GitHub Pages")
    p.add_argument("--message", "-m", default=None, metavar="MSG")
    p.add_argument("--yes",     "-y", action="store_true",    help="Skip confirmation")

    return parser


_CMD_MAP = {
    "check":   cmd_check,
    "install": cmd_install,
    "serve":   cmd_serve,
    "build":   cmd_build,
    "deploy":  cmd_deploy,
    "clean":   cmd_clean,
    "status":  cmd_status,
}


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    # Banner — always shown
    if not NO_COLOUR:
        print()
        print(c("  ██████╗ ██╗██╗     ██████╗ ███████╗██████╗ ", FG_CYAN, BOLD))
        print(c("  ██╔══██╗██║██║     ██╔══██╗██╔════╝██╔══██╗", FG_CYAN, BOLD))
        print(c("  ██║  ██║██║██║     ██║  ██║█████╗  ██████╔╝", FG_BLUE, BOLD))
        print(c("  ██║  ██║██║██║     ██║  ██║██╔══╝  ██╔══██╗", FG_BLUE, BOLD))
        print(c("  ██████╔╝██║███████╗██████╔╝███████╗██║  ██║", FG_CYAN, BOLD))
        print(c("  ╚═════╝ ╚═╝╚══════╝╚═════╝ ╚══════╝╚═╝  ╚═╝", FG_CYAN, BOLD))
        print(c("  website dev CLI", FG_GREY))

    parser = _build_parser()
    args   = parser.parse_args()

    # No command → interactive menu (TTY) or help text (piped)
    if not args.command:
        if sys.stdout.isatty():
            run_menu()
        else:
            parser.print_help()
        sys.exit(0)

    fn = _CMD_MAP.get(args.command)
    if fn:
        print()
        fn(args)
    else:
        log_error(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
