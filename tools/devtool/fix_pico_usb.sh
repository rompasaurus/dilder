#!/usr/bin/env bash
# Reset the EMPTY xHCI controllers to clear an eject-wedged Pico port.
# Explicitly EXCLUDES 0000:12:00.0 (keyboard/mouse/audio) so input is untouched.
#
# Usage:  hold the Pico's BOOTSEL button, plug it into the usual port, then:
#             sudo bash fix_pico_usb.sh
set -u
CTRLS=(0000:10:00.0 0000:7a:00.0 0000:7c:00.3 0000:7c:00.4 0000:7d:00.0)
DRV=/sys/bus/pci/drivers/xhci_hcd

if [ "$(id -u)" -ne 0 ]; then
    echo "Run with sudo:  sudo bash $0"
    exit 1
fi

echo "Unbinding empty xHCI controllers..."
for c in "${CTRLS[@]}"; do
    echo "$c" > "$DRV/unbind" 2>/dev/null && echo "  unbound $c" || echo "  (skip $c)"
done

sleep 2

echo "Rebinding..."
for c in "${CTRLS[@]}"; do
    echo "$c" > "$DRV/bind" 2>/dev/null && echo "  bound $c" || echo "  (already bound $c)"
done

sleep 2
echo
if lsusb | grep -i 2e8a; then
    echo "PICO BACK"
else
    echo "no pico yet"
fi
