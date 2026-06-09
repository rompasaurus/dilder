#!/usr/bin/env bash
# Identify which USB port the Pico uses (or why it won't enumerate).
# Run with sudo, then within ~12s PLUG IN THE PICO holding BOOTSEL.
#   sudo ./detect_pico_usb.sh
set -u
if [ "$(id -u)" -ne 0 ]; then echo "Run with sudo: sudo ./detect_pico_usb.sh"; exit 1; fi

echo "Occupied ports on the keyboard controller (bus 3/4) BEFORE plug-in:"
for d in /sys/bus/usb/devices/3-* /sys/bus/usb/devices/4-*; do
    [ -e "$d/idVendor" ] || continue
    printf "  %s  %s:%s  %s\n" "$(basename "$d")" \
        "$(cat "$d/idVendor")" "$(cat "$d/idProduct")" "$(cat "$d/product" 2>/dev/null)"
done

echo
echo ">>> PLUG IN THE PICO NOW (hold BOOTSEL). Watching kernel log for 12s..."
( timeout 12 dmesg -w | grep --line-buffered -iE "new .*usb device|2e8a|cannot enable|over-current|disabl|reset .*port|raspberry" ) || true

echo
echo "=== lsusb 2e8a ==="
lsusb | grep -i 2e8a && echo ">>> PICO DETECTED" || echo ">>> still no 2e8a"
echo "=== /dev/ttyACM* ==="
ls /dev/ttyACM* 2>/dev/null || echo "(none)"
