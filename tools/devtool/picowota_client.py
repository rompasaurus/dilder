"""
picowota_client.py — Python TCP client for the picowota WiFi OTA bootloader.

Reimplements the serial-flash Go tool's protocol in pure Python.
Supports: SYNC, INFO, ERASE, WRITE, SEAL, GOTO commands over TCP.

Protocol reference: https://github.com/usedbytes/serial-flash

Usage (standalone):
    python picowota_client.py 192.168.4.1 firmware.elf
    python picowota_client.py 192.168.4.1 firmware.bin --addr 0x10000000

Usage (as library):
    from picowota_client import PicowotaClient, load_elf, load_bin

    def on_progress(stage, current, total):
        print(f"{stage}: {current}/{total}")

    client = PicowotaClient("192.168.4.1", 4242)
    client.connect()
    image = load_elf("firmware.elf")
    client.program(image, progress_cb=on_progress)
    client.close()
"""

import socket
import struct
import zlib
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Callable, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Protocol constants
# ─────────────────────────────────────────────────────────────────────────────

PORT = 4242
CONNECT_TIMEOUT = 5.0
RECV_TIMEOUT = 10.0

# Opcodes (4 bytes ASCII)
OP_SYNC = b"SYNC"
OP_READ = b"READ"
OP_CSUM = b"CSUM"
OP_CRCC = b"CRCC"
OP_ERAS = b"ERAS"
OP_WRIT = b"WRIT"
OP_SEAL = b"SEAL"
OP_GOTO = b"GOGO"  # CMD_GO in picowota main.c: 'G','O','G','O'
OP_INFO = b"INFO"

# Response codes
RESP_OK   = b"OKOK"
RESP_ERR  = b"ERR!"
RESP_PICO = b"PICO"
RESP_WOTA = b"WOTA"

# Stages for progress callback
STAGE_SYNC  = "Syncing"
STAGE_INFO  = "Querying device"
STAGE_ERASE = "Erasing"
STAGE_WRITE = "Writing"
STAGE_SEAL  = "Sealing"
STAGE_GOTO  = "Launching"
STAGE_DONE  = "Done"


# ─────────────────────────────────────────────────────────────────────────────
# Data types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FlashInfo:
    """Device flash parameters returned by INFO command."""
    flash_addr: int
    flash_size: int
    erase_size: int
    write_size: int
    max_data_len: int


@dataclass
class FirmwareImage:
    """A firmware image to program."""
    addr: int          # Base address in flash
    data: bytes        # Raw binary data
    entry: int = 0     # Entry point address (for GOTO)


# ─────────────────────────────────────────────────────────────────────────────
# ELF loader (minimal — only loads PT_LOAD segments targeting flash)
# ─────────────────────────────────────────────────────────────────────────────

# ELF constants
EI_MAG = b"\x7fELF"
ET_EXEC = 2
EM_ARM = 40
PT_LOAD = 1
FLASH_BASE = 0x10000000
FLASH_END  = 0x10200000   # 2MB for Pico W
FLASH_END_4MB = 0x10400000  # 4MB for Pico 2 W


def load_elf(path: str) -> FirmwareImage:
    """Load an ELF file and extract flash-targeted LOAD segments."""
    data = Path(path).read_bytes()

    if data[:4] != EI_MAG:
        raise ValueError(f"Not an ELF file: {path}")

    # Parse ELF header (32-bit little-endian ARM)
    ei_class = data[4]
    if ei_class != 1:
        raise ValueError("Only 32-bit ELF supported (Pico is ARM Cortex-M)")

    # ELF32 header fields we need (offsets from the ELF spec)
    e_type      = struct.unpack_from("<H", data, 16)[0]
    e_machine   = struct.unpack_from("<H", data, 18)[0]
    e_entry     = struct.unpack_from("<I", data, 24)[0]
    e_phoff     = struct.unpack_from("<I", data, 28)[0]
    e_phentsize = struct.unpack_from("<H", data, 42)[0]
    e_phnum     = struct.unpack_from("<H", data, 44)[0]

    if e_machine != EM_ARM:
        raise ValueError(f"ELF machine type {e_machine} is not ARM ({EM_ARM})")

    # Collect flash-targeted LOAD segments
    segments = []
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        p_type   = struct.unpack_from("<I", data, off)[0]
        p_offset = struct.unpack_from("<I", data, off + 4)[0]
        p_vaddr  = struct.unpack_from("<I", data, off + 8)[0]
        p_paddr  = struct.unpack_from("<I", data, off + 12)[0]
        p_filesz = struct.unpack_from("<I", data, off + 16)[0]
        p_memsz  = struct.unpack_from("<I", data, off + 20)[0]

        if p_type != PT_LOAD or p_filesz == 0:
            continue

        # Use physical address for flash detection
        addr = p_paddr
        if FLASH_BASE <= addr < FLASH_END_4MB:
            segments.append((addr, data[p_offset:p_offset + p_filesz]))

    if not segments:
        raise ValueError("No flash-targeted LOAD segments found in ELF")

    # Sort by address and merge into a contiguous image
    segments.sort(key=lambda s: s[0])
    base_addr = segments[0][0]
    # Calculate total size from first segment start to last segment end
    end_addr = max(s[0] + len(s[1]) for s in segments)
    total_size = end_addr - base_addr

    image = bytearray(total_size)
    for seg_addr, seg_data in segments:
        offset = seg_addr - base_addr
        image[offset:offset + len(seg_data)] = seg_data

    return FirmwareImage(addr=base_addr, data=bytes(image), entry=e_entry)


def load_bin(path: str, addr: int = FLASH_BASE) -> FirmwareImage:
    """Load a raw binary file with an explicit base address."""
    data = Path(path).read_bytes()
    return FirmwareImage(addr=addr, data=data, entry=addr)


def load_uf2(path: str) -> FirmwareImage:
    """Load a UF2 file and extract flash-targeted blocks."""
    data = Path(path).read_bytes()
    UF2_MAGIC_START0 = 0x0A324655
    UF2_MAGIC_START1 = 0x9E5D5157
    UF2_MAGIC_END    = 0x0AB16F30
    BLOCK_SIZE = 512

    blocks = []
    offset = 0
    while offset + BLOCK_SIZE <= len(data):
        magic0, magic1 = struct.unpack_from("<II", data, offset)
        if magic0 != UF2_MAGIC_START0 or magic1 != UF2_MAGIC_START1:
            break
        flags      = struct.unpack_from("<I", data, offset + 8)[0]
        target_addr = struct.unpack_from("<I", data, offset + 12)[0]
        payload_sz  = struct.unpack_from("<I", data, offset + 16)[0]
        magic_end   = struct.unpack_from("<I", data, offset + BLOCK_SIZE - 4)[0]

        if magic_end != UF2_MAGIC_END:
            raise ValueError(f"Bad UF2 end magic at block offset {offset}")

        if FLASH_BASE <= target_addr < FLASH_END_4MB:
            payload = data[offset + 32:offset + 32 + payload_sz]
            blocks.append((target_addr, payload))

        offset += BLOCK_SIZE

    if not blocks:
        raise ValueError("No flash-targeted blocks found in UF2")

    blocks.sort(key=lambda b: b[0])
    base_addr = blocks[0][0]
    end_addr = max(b[0] + len(b[1]) for b in blocks)
    total_size = end_addr - base_addr

    image = bytearray(total_size)
    for blk_addr, blk_data in blocks:
        off = blk_addr - base_addr
        image[off:off + len(blk_data)] = blk_data

    return FirmwareImage(addr=base_addr, data=bytes(image), entry=base_addr)


# ─────────────────────────────────────────────────────────────────────────────
# TCP client
# ─────────────────────────────────────────────────────────────────────────────

ProgressCallback = Callable[[str, int, int], None]


class PicowotaError(Exception):
    """Error communicating with picowota bootloader."""
    pass


class PicowotaClient:
    """TCP client for the picowota WiFi OTA bootloader."""

    def __init__(self, host: str, port: int = PORT):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.info: Optional[FlashInfo] = None
        self._is_wota = False

    def connect(self, timeout: float = CONNECT_TIMEOUT):
        """Establish TCP connection to the bootloader."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((self.host, self.port))
        # picowota needs a brief delay after TCP connect
        time.sleep(0.5)
        self.sock.settimeout(RECV_TIMEOUT)

    def close(self):
        """Close the TCP connection."""
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def _send(self, data: bytes):
        """Send data to the bootloader."""
        self.sock.sendall(data)

    def _recv(self, size: int) -> bytes:
        """Receive exactly `size` bytes from the bootloader."""
        buf = b""
        while len(buf) < size:
            chunk = self.sock.recv(size - len(buf))
            if not chunk:
                raise PicowotaError("Connection closed by bootloader")
            buf += chunk
        return buf

    def _recv_response(self, expected_extra: int = 0) -> bytes:
        """Receive a 4-byte status + optional extra data. Raises on ERR!."""
        resp = self._recv(4 + expected_extra)
        status = resp[:4]
        if status == RESP_ERR:
            raise PicowotaError("Bootloader returned ERR!")
        if status != RESP_OK:
            raise PicowotaError(f"Unexpected response: {status!r}")
        return resp[4:]

    # ── Protocol commands ──

    def sync(self, retries: int = 5) -> bool:
        """Send SYNC and check for PICO/WOTA response."""
        for attempt in range(retries):
            try:
                self._send(OP_SYNC)
                resp = self._recv(4)
                if resp in (RESP_PICO, RESP_WOTA):
                    self._is_wota = (resp == RESP_WOTA)
                    return True
            except (socket.timeout, PicowotaError):
                if attempt < retries - 1:
                    time.sleep(0.2)
                    continue
                raise
        return False

    def query_info(self) -> FlashInfo:
        """Query device flash parameters."""
        self._send(OP_INFO)
        data = self._recv_response(expected_extra=20)
        flash_addr, flash_size, erase_size, write_size, max_data_len = \
            struct.unpack("<IIIII", data)
        self.info = FlashInfo(
            flash_addr=flash_addr,
            flash_size=flash_size,
            erase_size=erase_size,
            write_size=write_size,
            max_data_len=max_data_len,
        )
        return self.info

    def erase(self, addr: int, length: int):
        """Erase a region of flash."""
        self._send(OP_ERAS + struct.pack("<II", addr, length))
        self._recv_response()

    def write(self, addr: int, data: bytes) -> int:
        """Write data to flash. Returns CRC32 from device."""
        self._send(OP_WRIT + struct.pack("<II", addr, len(data)) + data)
        crc_data = self._recv_response(expected_extra=4)
        return struct.unpack("<I", crc_data)[0]

    def seal(self, addr: int, length: int, crc: int):
        """Seal a written region with CRC verification."""
        self._send(OP_SEAL + struct.pack("<III", addr, length, crc))
        self._recv_response()

    def goto(self, addr: int):
        """Jump to address (fire-and-forget — no response expected)."""
        self._send(OP_GOTO + struct.pack("<I", addr))

    def read(self, addr: int, length: int) -> bytes:
        """Read data from flash."""
        self._send(OP_READ + struct.pack("<II", addr, length))
        return self._recv_response(expected_extra=length)

    def crc32(self, addr: int, length: int) -> int:
        """Calculate CRC32 of a flash region on-device."""
        self._send(OP_CRCC + struct.pack("<II", addr, length))
        data = self._recv_response(expected_extra=4)
        return struct.unpack("<I", data)[0]

    # ── High-level programming flow ──

    def program(self, image: FirmwareImage,
                progress_cb: Optional[ProgressCallback] = None):
        """
        Full programming flow: sync → info → erase → write → seal → goto.

        Args:
            image: FirmwareImage to program
            progress_cb: Optional callback(stage, current, total)
        """
        def report(stage, current=0, total=0):
            if progress_cb:
                progress_cb(stage, current, total)

        # 1. Sync
        report(STAGE_SYNC, 0, 1)
        self.sync()
        report(STAGE_SYNC, 1, 1)

        # 2. Query device info
        report(STAGE_INFO, 0, 1)
        info = self.query_info()
        report(STAGE_INFO, 1, 1)

        # Sanity-check the INFO response.  When an RP2040 build runs on
        # the Pico 2 W in compatibility mode the flash_addr can come back
        # as a RAM address (e.g. 0x200023EC) — fall back to safe defaults
        # in that case.
        if info.flash_addr < FLASH_BASE or info.flash_addr > FLASH_END_4MB:
            info = FlashInfo(
                flash_addr=FLASH_BASE,
                flash_size=4 * 1024 * 1024,  # 4MB (Pico 2 W)
                erase_size=info.erase_size if info.erase_size in (4096, 8192) else 4096,
                write_size=info.write_size if 0 < info.write_size <= 4096 else 256,
                max_data_len=info.max_data_len if 0 < info.max_data_len <= 4096 else 1024,
            )

        # Validate image fits in flash
        if image.addr < info.flash_addr:
            raise PicowotaError(
                f"Image address 0x{image.addr:08X} is below flash "
                f"start 0x{info.flash_addr:08X}")
        img_end = image.addr + len(image.data)
        flash_end = info.flash_addr + info.flash_size
        if img_end > flash_end:
            raise PicowotaError(
                f"Image end 0x{img_end:08X} exceeds flash "
                f"end 0x{flash_end:08X}")

        # Pad data to write alignment
        pad_len = _align(len(image.data), info.write_size) - len(image.data)
        padded_data = image.data + (b"\xff" * pad_len)
        total_len = len(padded_data)

        # 3. Erase
        erase_len = _align(total_len, info.erase_size)
        erase_steps = erase_len // info.erase_size
        for i in range(erase_steps):
            report(STAGE_ERASE, i, erase_steps)
            erase_addr = image.addr + i * info.erase_size
            self.erase(erase_addr, info.erase_size)
        report(STAGE_ERASE, erase_steps, erase_steps)

        # 4. Write in chunks
        chunk_size = info.max_data_len
        write_steps = (total_len + chunk_size - 1) // chunk_size
        for i in range(write_steps):
            offset = i * chunk_size
            chunk = padded_data[offset:offset + chunk_size]
            report(STAGE_WRITE, i, write_steps)
            self.write(image.addr + offset, chunk)
        report(STAGE_WRITE, write_steps, write_steps)

        # 5. Seal with CRC32
        report(STAGE_SEAL, 0, 1)
        crc = zlib.crc32(padded_data) & 0xFFFFFFFF
        self.seal(image.addr, total_len, crc)
        report(STAGE_SEAL, 1, 1)

        # 6. GOTO the vector-table base. picowota's jump_to_vtor() reads the
        # initial SP from [vtor] and the reset handler from [vtor+4], so this
        # must be the image base (the vector table), NOT the ELF entry point.
        report(STAGE_GOTO, 0, 1)
        self.goto(image.addr)
        report(STAGE_GOTO, 1, 1)

        report(STAGE_DONE, 1, 1)


def _align(value: int, alignment: int) -> int:
    """Round up to the next multiple of alignment."""
    return ((value + alignment - 1) // alignment) * alignment


# ─────────────────────────────────────────────────────────────────────────────
# Device discovery (mDNS / network scan)
# ─────────────────────────────────────────────────────────────────────────────

def scan_for_picowota(timeout: float = 3.0,
                       subnet: str = "192.168.4") -> list:
    """
    Scan a /24 subnet for picowota devices by attempting TCP connect on port 4242.
    Returns list of (ip, response_time_ms) tuples.

    For AP mode the default subnet is 192.168.4.x (picowota default).
    For STA mode pass your local subnet, e.g. "192.168.1".
    """
    found = []

    def _probe(ip):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            t0 = time.monotonic()
            sock.connect((ip, PORT))
            dt = (time.monotonic() - t0) * 1000
            # Try SYNC to confirm it's picowota
            sock.sendall(OP_SYNC)
            resp = sock.recv(4)
            sock.close()
            if resp in (RESP_PICO, RESP_WOTA):
                found.append((ip, dt))
        except (socket.timeout, ConnectionRefusedError, OSError):
            pass

    # One worker per address so every IP is probed concurrently. A dead host
    # blocks its worker for the full `timeout` (no SYN-ACK), so with too few
    # workers the upper half of the subnet is never reached before we give up.
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=254) as pool:
        futures = [pool.submit(_probe, f"{subnet}.{i}") for i in range(1, 255)]
        concurrent.futures.wait(futures, timeout=timeout + 5)

    found.sort(key=lambda x: x[1])
    return found


def probe_picowota(host: str, port: int = PORT,
                    timeout: float = 2.0) -> Optional[str]:
    """
    Probe a single host for picowota. Returns "PICO" or "WOTA" on success,
    None if unreachable or not a picowota device.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        time.sleep(0.3)
        sock.sendall(OP_SYNC)
        resp = sock.recv(4)
        sock.close()
        if resp == RESP_PICO:
            return "PICO"
        elif resp == RESP_WOTA:
            return "WOTA"
    except (socket.timeout, ConnectionRefusedError, OSError):
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="picowota WiFi OTA flasher for Raspberry Pi Pico W")
    parser.add_argument("host", help="IP address of the Pico W")
    parser.add_argument("firmware", help="Firmware file (.elf, .bin, or .uf2)")
    parser.add_argument("--port", type=int, default=PORT,
                        help=f"TCP port (default: {PORT})")
    parser.add_argument("--addr", type=lambda x: int(x, 0),
                        default=FLASH_BASE,
                        help="Base address for .bin files (default: 0x10000000)")
    parser.add_argument("--scan", action="store_true",
                        help="Scan subnet for picowota devices instead of flashing")
    parser.add_argument("--subnet", default="192.168.4",
                        help="Subnet to scan (default: 192.168.4)")
    args = parser.parse_args()

    if args.scan:
        print(f"Scanning {args.subnet}.0/24 for picowota devices...")
        devices = scan_for_picowota(subnet=args.subnet)
        if devices:
            for ip, ms in devices:
                print(f"  Found: {ip} ({ms:.0f}ms)")
        else:
            print("  No devices found.")
        return

    # Load firmware
    path = args.firmware
    ext = Path(path).suffix.lower()
    if ext == ".elf":
        print(f"Loading ELF: {path}")
        image = load_elf(path)
    elif ext == ".uf2":
        print(f"Loading UF2: {path}")
        image = load_uf2(path)
    else:
        print(f"Loading binary: {path} at 0x{args.addr:08X}")
        image = load_bin(path, args.addr)

    print(f"Image: {len(image.data)} bytes at 0x{image.addr:08X}, "
          f"entry 0x{image.entry:08X}")

    def on_progress(stage, current, total):
        if total > 0:
            pct = current * 100 // total
            bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
            print(f"\r  {stage:12s} [{bar}] {pct:3d}%", end="", flush=True)
            if current >= total:
                print()
        else:
            print(f"  {stage}")

    client = PicowotaClient(args.host, args.port)
    try:
        print(f"Connecting to {args.host}:{args.port}...")
        client.connect()
        print("Connected. Programming...")
        client.program(image, progress_cb=on_progress)
        print("Done! Firmware uploaded and launched.")
    except PicowotaError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
