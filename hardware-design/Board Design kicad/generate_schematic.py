#!/usr/bin/env python3
"""
Generate a fully-wired KiCad schematic for the Dilder PCB.
ESP32-S3-WROOM-1-N16R8 version — replaces RP2040.

Removed vs old design:
  - RP2040 (replaced by ESP32-S3 module with integrated flash/PSRAM/crystal/RF)
  - W25Q16JV external flash (integrated in module)
  - 12MHz crystal + load caps (integrated in module)
  - 27R USB series resistors (ESP32-S3 has native USB-OTG)
  - ATGM336H GPS module (deferred to later phase)

Uses net labels on wire stubs to create all electrical connections.

Run from the 'Board Design kicad/' directory:
  python3 generate_schematic.py

═══════════════════════════════════════════════════════════════════
BILL OF MATERIALS (BOM) — 28 components
═══════════════════════════════════════════════════════════════════
Ref   | Value               | Package                    | LCSC     | ~Cost
------+---------------------+----------------------------+----------+------
U1    | ESP32-S3-WROOM-1    | RF_Module (18x25.5mm)      | C2913196 | $2.80
      |   -N16R8            |                            |          |
U2    | TP4056              | ESOP-8                     | C382139  | $0.07
U3    | DW01A               | SOT-23-6                   | C351410  | $0.05
Q1    | FS8205A             | SOT-23-6                   | C908265  | $0.05
U4    | AMS1117-3.3         | SOT-223-3                  | C6186    | $0.05
U5    | LIS2DH12TR          | LGA-12 (2x2mm)             | C110926  | $0.46
J1    | USB-C 16-pin        | HRO TYPE-C-31-M-12         | C2765186 | $0.10
J2    | JST PH 2-pin        | JST_PH_S2B-PH-SM4-TB      | C131337  | $0.03
J3    | ePaper 8-pin        | JST_SH 1mm horiz           | —        | $0.05
D1    | SS34 Schottky       | SMA                        | C8678    | $0.03
D2    | RED LED             | 0402                       | C84256   | $0.01
D3    | GREEN LED           | 0402                       | C72043   | $0.01
SW1   | SKRHABE010 5-way    | SMD                        | C139794  | $0.38
SW2   | BOOT button (PTS810)| SMD                        | —        | $0.05
SW3   | RESET button(PTS810)| SMD                        | —        | $0.05
R1    | 1.2k (TP4056 PROG)  | 0402                       | C25752   | $0.01
R2    | 1k (charge LED)     | 0402                       | C25585   | $0.01
R3    | 1k (standby LED)    | 0402                       | C25585   | $0.01
R4    | 10k (I2C SDA pull)  | 0402                       | C25744   | $0.01
R5    | 10k (I2C SCL pull)  | 0402                       | C25744   | $0.01
R8    | 5.1k (USB CC1)      | 0402                       | —        | $0.01
R9    | 5.1k (USB CC2)      | 0402                       | —        | $0.01
R10   | 10k (EN pull-up)    | 0402                       | C25744   | $0.01
R11   | 10k (BOOT GPIO0     | 0402                       | C25744   | $0.01
      |   pull-up)          |                            |          |
C3    | 100nF (ESP32 decap) | 0402                       | C14663   | $0.01
C4    | 10uF (ESP32 bulk)   | 0402                       | C19702   | $0.01
C5    | 10uF (LDO input)    | 0402                       | C19702   | $0.01
C6    | 10uF (LDO output)   | 0402                       | C19702   | $0.01
C7    | 100nF (IMU decap)   | 0402                       | C14663   | $0.01
C8    | 100nF (EN debounce)  | 0402                       | C14663   | $0.01
------+---------------------+----------------------------+----------+------
                                              TOTAL per board: ~$4.26

GPIO Pin Assignment (ESP32-S3-WROOM-1):
  GPIO0  → BOOT           GPIO3  → EPD_DC
  GPIO4-8  → Joystick (UP/DN/LT/RT/CTR)
  GPIO9  → EPD_CLK (SCK) GPIO10   → EPD_MOSI
  GPIO11 → EPD_RST       GPIO12   → EPD_BUSY
  GPIO16 → I2C_SDA       GPIO17   → I2C_SCL
  GPIO18 → ACCEL_INT1    GPIO19   → USB_D-
  GPIO20 → USB_D+        GPIO46   → EPD_CS
═══════════════════════════════════════════════════════════════════
"""

import uuid as _uuid
import json

# ── Helpers ────────────────────────────────────────────────────────────

_uuid_counter = 0
def uid():
    global _uuid_counter
    _uuid_counter += 1
    return f"a{_uuid_counter:011x}-0000-4000-8000-000000000000"

def wire(x1, y1, x2, y2):
    return f'  (wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{uid()}"))'

def label(name, x, y, angle=0):
    return f'  (label "{name}" (at {x} {y} {angle}) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))'


# ── Component placement coordinates ───────────────────────────────────
# Organized into functional blocks on an A3 sheet (420x297mm)

# POWER SECTION (top area, y=40-120)
USB_C    = (45,  68)     # J1 - USB-C connector
SCHOTTKY = (80,  55)     # D1 - SS34
TP4056   = (115, 68)     # U2 - charger
DW01A    = (170, 68)     # U3 - protection
FS8205A  = (170, 100)    # Q1 - MOSFETs
JST_BAT  = (220, 68)     # J2 - battery connector
LDO      = (115, 115)    # U4 - AMS1117-3.3
RPROG    = (100, 82)     # R1 - 1.2k prog resistor
LED_CHG  = (140, 58)     # D2 - charge LED
LED_DONE = (140, 48)     # D3 - done LED
RLED1    = (152, 58)     # R2 - LED resistor
RLED2    = (152, 48)     # R3 - LED resistor
C_LDO_IN = (100, 115)   # C5 - LDO input cap
C_LDO_OUT= (132, 115)   # C6 - LDO output cap

# MCU SECTION (center, y=150-230)
ESP32    = (160, 190)    # U1 - ESP32-S3-WROOM-1-N16R8
C_DEC1   = (145, 155)   # C3 - 100nF decoupling
C_DEC2   = (155, 155)   # C4 - 10uF bulk
R_CC1    = (35,  82)    # R8 - 5.1k CC1
R_CC2    = (45,  82)    # R9 - 5.1k CC2
R_EN     = (200, 170)   # R10 - 10k EN pull-up

# PERIPHERALS (left and right sides)
JOYSTICK = (50,  185)   # SW1 - 5-way nav switch
EPAPER   = (280, 175)   # J3 - e-Paper 8-pin header
ACCEL    = (280, 220)   # U5 - LIS2DH12TR
R_I2C_SDA= (265, 208)  # R4 - 10k I2C pull-up
R_I2C_SCL= (272, 208)  # R5 - 10k I2C pull-up
C_IMU    = (298, 210)   # C7 - 100nF IMU decoupling

# BOOT / RESET SECTION
BOOT_BTN = (230, 205)   # SW2 - BOOT button
RESET_BTN= (230, 175)   # SW3 - RESET button
R_BOOT   = (215, 205)   # R11 - 10k GPIO0 pull-up
C_EN_DEB = (215, 175)   # C8 - 100nF EN debounce


# ── Build lib_symbols inline ─────────────────────────────────────────

def build_lib_symbols():
    return """(lib_symbols

    (symbol "ESP32-S3-WROOM-1" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 26.67 0) (effects (font (size 1.27 1.27))))
      (property "Value" "ESP32-S3-WROOM-1-N16R8" (at 0 -26.67 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "RF_Module:ESP32-S3-WROOM-1" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C2913196" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "ESP32-S3-WROOM-1_0_1"
        (rectangle (start -15.24 25.4) (end 15.24 -25.4) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "ESP32-S3-WROOM-1_1_1"
        (pin power_in line (at 0 27.94 270) (length 2.54) (name "3V3" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
        (pin input line (at -17.78 22.86 0) (length 2.54) (name "EN" (effects (font (size 1.016 1.016)))) (number "3" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -17.78 20.32 0) (length 2.54) (name "GPIO0" (effects (font (size 1.016 1.016)))) (number "27" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -17.78 17.78 0) (length 2.54) (name "GPIO4" (effects (font (size 1.016 1.016)))) (number "4" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -17.78 15.24 0) (length 2.54) (name "GPIO5" (effects (font (size 1.016 1.016)))) (number "5" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -17.78 12.7 0) (length 2.54) (name "GPIO6" (effects (font (size 1.016 1.016)))) (number "6" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -17.78 10.16 0) (length 2.54) (name "GPIO7" (effects (font (size 1.016 1.016)))) (number "7" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -17.78 7.62 0) (length 2.54) (name "GPIO8" (effects (font (size 1.016 1.016)))) (number "8" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -17.78 2.54 0) (length 2.54) (name "GPIO16/SDA" (effects (font (size 1.016 1.016)))) (number "9" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -17.78 0 0) (length 2.54) (name "GPIO17/SCL" (effects (font (size 1.016 1.016)))) (number "10" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -17.78 -2.54 0) (length 2.54) (name "GPIO18" (effects (font (size 1.016 1.016)))) (number "11" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -17.78 -5.08 0) (length 2.54) (name "GPIO19/D-" (effects (font (size 1.016 1.016)))) (number "13" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -17.78 -7.62 0) (length 2.54) (name "GPIO20/D+" (effects (font (size 1.016 1.016)))) (number "14" (effects (font (size 1.016 1.016)))))
        (pin output line (at 17.78 17.78 180) (length 2.54) (name "GPIO9/SCK" (effects (font (size 1.016 1.016)))) (number "15" (effects (font (size 1.016 1.016)))))
        (pin output line (at 17.78 15.24 180) (length 2.54) (name "GPIO10/MOSI" (effects (font (size 1.016 1.016)))) (number "16" (effects (font (size 1.016 1.016)))))
        (pin output line (at 17.78 12.7 180) (length 2.54) (name "GPIO3/DC" (effects (font (size 1.016 1.016)))) (number "17" (effects (font (size 1.016 1.016)))))
        (pin output line (at 17.78 10.16 180) (length 2.54) (name "GPIO11/RST" (effects (font (size 1.016 1.016)))) (number "18" (effects (font (size 1.016 1.016)))))
        (pin output line (at 17.78 7.62 180) (length 2.54) (name "GPIO46/CS" (effects (font (size 1.016 1.016)))) (number "19" (effects (font (size 1.016 1.016)))))
        (pin input line (at 17.78 5.08 180) (length 2.54) (name "GPIO12/BUSY" (effects (font (size 1.016 1.016)))) (number "20" (effects (font (size 1.016 1.016)))))
        (pin power_in line (at 0 -27.94 90) (length 2.54) (name "GND" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "TP4056" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 8.89 0) (effects (font (size 1.27 1.27))))
      (property "Value" "TP4056" (at 0 -8.89 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_SO:ESOP-8_3.9x4.9mm_P1.27mm" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C382139" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "TP4056_0_1"
        (rectangle (start -7.62 7.62) (end 7.62 -7.62) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "TP4056_1_1"
        (pin input line (at -10.16 5.08 0) (length 2.54) (name "VCC" (effects (font (size 1.016 1.016)))) (number "8" (effects (font (size 1.016 1.016)))))
        (pin output line (at 10.16 5.08 180) (length 2.54) (name "BAT" (effects (font (size 1.016 1.016)))) (number "3" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -10.16 2.54 0) (length 2.54) (name "PROG" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
        (pin input line (at -10.16 0 0) (length 2.54) (name "TEMP" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
        (pin open_collector line (at 10.16 2.54 180) (length 2.54) (name "~{STDBY}" (effects (font (size 1.016 1.016)))) (number "6" (effects (font (size 1.016 1.016)))))
        (pin open_collector line (at 10.16 0 180) (length 2.54) (name "~{CHRG}" (effects (font (size 1.016 1.016)))) (number "7" (effects (font (size 1.016 1.016)))))
        (pin input line (at -10.16 -2.54 0) (length 2.54) (name "CE" (effects (font (size 1.016 1.016)))) (number "4" (effects (font (size 1.016 1.016)))))
        (pin power_in line (at 0 -10.16 90) (length 2.54) (name "GND" (effects (font (size 1.016 1.016)))) (number "5" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "DW01A" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 6.35 0) (effects (font (size 1.27 1.27))))
      (property "Value" "DW01A" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_TO_SOT_SMD:SOT-23-6" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C351410" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "DW01A_0_1"
        (rectangle (start -6.35 5.08) (end 6.35 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "DW01A_1_1"
        (pin output line (at -8.89 2.54 0) (length 2.54) (name "OD" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
        (pin input line (at -8.89 0 0) (length 2.54) (name "CS" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
        (pin output line (at -8.89 -2.54 0) (length 2.54) (name "OC" (effects (font (size 1.016 1.016)))) (number "3" (effects (font (size 1.016 1.016)))))
        (pin power_in line (at 8.89 2.54 180) (length 2.54) (name "VCC" (effects (font (size 1.016 1.016)))) (number "5" (effects (font (size 1.016 1.016)))))
        (pin power_in line (at 8.89 -2.54 180) (length 2.54) (name "GND" (effects (font (size 1.016 1.016)))) (number "6" (effects (font (size 1.016 1.016)))))
        (pin input line (at 8.89 0 180) (length 2.54) (name "TD" (effects (font (size 1.016 1.016)))) (number "4" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "FS8205A" (in_bom yes) (on_board yes)
      (property "Reference" "Q" (at 0 6.35 0) (effects (font (size 1.27 1.27))))
      (property "Value" "FS8205A" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_TO_SOT_SMD:SOT-23-6" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C908265" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "FS8205A_0_1"
        (rectangle (start -6.35 5.08) (end 6.35 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "FS8205A_1_1"
        (pin passive line (at -8.89 2.54 0) (length 2.54) (name "S1" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
        (pin input line (at -8.89 0 0) (length 2.54) (name "G1" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
        (pin passive line (at 8.89 2.54 180) (length 2.54) (name "S2" (effects (font (size 1.016 1.016)))) (number "6" (effects (font (size 1.016 1.016)))))
        (pin input line (at 8.89 0 180) (length 2.54) (name "G2" (effects (font (size 1.016 1.016)))) (number "5" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -8.89 -2.54 0) (length 2.54) (name "D12" (effects (font (size 1.016 1.016)))) (number "3" (effects (font (size 1.016 1.016)))))
        (pin passive line (at 8.89 -2.54 180) (length 2.54) (name "D12B" (effects (font (size 1.016 1.016)))) (number "4" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "AMS1117-3.3" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "AMS1117-3.3" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_TO_SOT_SMD:SOT-223-3_TabPin2" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C6186" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "AMS1117-3.3_0_1"
        (rectangle (start -5.08 3.81) (end 5.08 -3.81) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "AMS1117-3.3_1_1"
        (pin power_in line (at -7.62 1.27 0) (length 2.54) (name "VIN" (effects (font (size 1.016 1.016)))) (number "3" (effects (font (size 1.016 1.016)))))
        (pin power_out line (at 7.62 1.27 180) (length 2.54) (name "VOUT" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
        (pin power_in line (at 0 -6.35 90) (length 2.54) (name "GND" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "LIS2DH12TR" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 10.16 0) (effects (font (size 1.27 1.27))))
      (property "Value" "LIS2DH12TR" (at 0 -10.16 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_LGA:LGA-12_2x2mm_P0.5mm" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C110926" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "LIS2DH12TR_0_1"
        (rectangle (start -7.62 8.89) (end 7.62 -8.89) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "LIS2DH12TR_1_1"
        (pin power_in line (at 0 11.43 270) (length 2.54) (name "VDD" (effects (font (size 1.016 1.016)))) (number "10" (effects (font (size 1.016 1.016)))))
        (pin power_in line (at 2.54 11.43 270) (length 2.54) (name "VDD_IO" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
        (pin power_in line (at 0 -11.43 90) (length 2.54) (name "GND" (effects (font (size 1.016 1.016)))) (number "5" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -10.16 5.08 0) (length 2.54) (name "SDA" (effects (font (size 1.016 1.016)))) (number "6" (effects (font (size 1.016 1.016)))))
        (pin input line (at -10.16 2.54 0) (length 2.54) (name "SCL" (effects (font (size 1.016 1.016)))) (number "7" (effects (font (size 1.016 1.016)))))
        (pin input line (at -10.16 0 0) (length 2.54) (name "CS" (effects (font (size 1.016 1.016)))) (number "4" (effects (font (size 1.016 1.016)))))
        (pin input line (at -10.16 -2.54 0) (length 2.54) (name "SA0" (effects (font (size 1.016 1.016)))) (number "3" (effects (font (size 1.016 1.016)))))
        (pin output line (at 10.16 5.08 180) (length 2.54) (name "INT1" (effects (font (size 1.016 1.016)))) (number "8" (effects (font (size 1.016 1.016)))))
        (pin output line (at 10.16 2.54 180) (length 2.54) (name "INT2" (effects (font (size 1.016 1.016)))) (number "9" (effects (font (size 1.016 1.016)))))
        (pin passive line (at 10.16 -2.54 180) (length 2.54) (name "RES" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "SKRHABE010" (in_bom yes) (on_board yes)
      (property "Reference" "SW" (at 0 8.89 0) (effects (font (size 1.27 1.27))))
      (property "Value" "SKRHABE010" (at 0 -8.89 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C139794" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "SKRHABE010_0_1"
        (rectangle (start -7.62 7.62) (end 7.62 -7.62) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "SKRHABE010_1_1"
        (pin passive line (at -10.16 5.08 0) (length 2.54) (name "UP" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -10.16 2.54 0) (length 2.54) (name "DOWN" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -10.16 0 0) (length 2.54) (name "LEFT" (effects (font (size 1.016 1.016)))) (number "3" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -10.16 -2.54 0) (length 2.54) (name "RIGHT" (effects (font (size 1.016 1.016)))) (number "4" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -10.16 -5.08 0) (length 2.54) (name "CENTER" (effects (font (size 1.016 1.016)))) (number "5" (effects (font (size 1.016 1.016)))))
        (pin passive line (at 10.16 0 180) (length 2.54) (name "COM" (effects (font (size 1.016 1.016)))) (number "6" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "USB_C_16P" (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 10.16 0) (effects (font (size 1.27 1.27))))
      (property "Value" "USB-C" (at 0 -10.16 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C2765186" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "USB_C_16P_0_1"
        (rectangle (start -7.62 8.89) (end 7.62 -8.89) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "USB_C_16P_1_1"
        (pin power_out line (at 0 11.43 270) (length 2.54) (name "VBUS" (effects (font (size 1.016 1.016)))) (number "A4" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -10.16 2.54 0) (length 2.54) (name "CC1" (effects (font (size 1.016 1.016)))) (number "A5" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -10.16 0 0) (length 2.54) (name "CC2" (effects (font (size 1.016 1.016)))) (number "B5" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -10.16 -2.54 0) (length 2.54) (name "D+" (effects (font (size 1.016 1.016)))) (number "A6" (effects (font (size 1.016 1.016)))))
        (pin bidirectional line (at -10.16 -5.08 0) (length 2.54) (name "D-" (effects (font (size 1.016 1.016)))) (number "A7" (effects (font (size 1.016 1.016)))))
        (pin power_in line (at 0 -11.43 90) (length 2.54) (name "GND" (effects (font (size 1.016 1.016)))) (number "A1" (effects (font (size 1.016 1.016)))))
        (pin passive line (at 10.16 0 180) (length 2.54) (name "SHIELD" (effects (font (size 1.016 1.016)))) (number "S1" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "JST_PH_2" (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "JST-PH-2" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C131337" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "JST_PH_2_0_1"
        (rectangle (start -3.81 3.81) (end 3.81 -3.81) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "JST_PH_2_1_1"
        (pin passive line (at -6.35 1.27 0) (length 2.54) (name "+" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -6.35 -1.27 0) (length 2.54) (name "-" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "EPAPER_HEADER" (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 12.7 0) (effects (font (size 1.27 1.27))))
      (property "Value" "ePaper_8pin" (at 0 -12.7 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Connector_JST:JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "EPAPER_HEADER_0_1"
        (rectangle (start -5.08 11.43) (end 5.08 -11.43) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "EPAPER_HEADER_1_1"
        (pin passive line (at -7.62 8.89 0) (length 2.54) (name "VCC" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -7.62 6.35 0) (length 2.54) (name "GND" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -7.62 3.81 0) (length 2.54) (name "DIN" (effects (font (size 1.016 1.016)))) (number "3" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -7.62 1.27 0) (length 2.54) (name "CLK" (effects (font (size 1.016 1.016)))) (number "4" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -7.62 -1.27 0) (length 2.54) (name "CS" (effects (font (size 1.016 1.016)))) (number "5" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -7.62 -3.81 0) (length 2.54) (name "DC" (effects (font (size 1.016 1.016)))) (number "6" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -7.62 -6.35 0) (length 2.54) (name "RST" (effects (font (size 1.016 1.016)))) (number "7" (effects (font (size 1.016 1.016)))))
        (pin passive line (at -7.62 -8.89 0) (length 2.54) (name "BUSY" (effects (font (size 1.016 1.016)))) (number "8" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "C" (in_bom yes) (on_board yes)
      (property "Reference" "C" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "C" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Capacitor_SMD:C_0402_1005Metric" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "C_0_1"
        (polyline (pts (xy -1.27 0.635) (xy 1.27 0.635)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -1.27 -0.635) (xy 1.27 -0.635)) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "C_1_1"
        (pin passive line (at 0 2.54 270) (length 1.905) (name "1" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
        (pin passive line (at 0 -2.54 90) (length 1.905) (name "2" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "R" (in_bom yes) (on_board yes)
      (property "Reference" "R" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "R" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Resistor_SMD:R_0402_1005Metric" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "R_0_1"
        (rectangle (start -1.016 1.778) (end 1.016 -1.778) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "R_1_1"
        (pin passive line (at 0 2.54 270) (length 0.762) (name "1" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
        (pin passive line (at 0 -2.54 90) (length 0.762) (name "2" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "LED" (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Value" "LED" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "LED_SMD:LED_0402_1005Metric" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "LED_0_1"
        (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27) (xy 1.27 0) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "LED_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54) (name "A" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "K" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "SW_Push" (in_bom yes) (on_board yes)
      (property "Reference" "SW" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Value" "SW_Push" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Button_Switch_SMD:SW_SPST_PTS810" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "SW_Push_0_1"
        (circle (center -1.27 0) (radius 0.508) (stroke (width 0.254) (type default)) (fill (type none)))
        (circle (center 1.27 0) (radius 0.508) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -0.762 1.27) (xy 0.762 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "SW_Push_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54) (name "1" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "2" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
      )
    )

    (symbol "D_Schottky" (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Value" "SS34" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Diode_SMD:D_SMA" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C8678" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "D_Schottky_0_1"
        (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27) (xy 1.27 0) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "D_Schottky_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54) (name "A" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "K" (effects (font (size 1.016 1.016)))) (number "2" (effects (font (size 1.016 1.016)))))
      )
    )

  )"""


def component(lib_id, ref_prefix, ref_num, value, x, y, lcsc="", footprint="", pins=None, angle=0):
    """Generate a component instance."""
    u = uid()
    ref = f"{ref_prefix}{ref_num}"
    lines = [
        f'  (symbol (lib_id "{lib_id}") (at {x} {y} {angle}) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes)',
        f'    (uuid "{u}")',
        f'    (property "Reference" "{ref}" (at {x} {y-12} 0) (effects (font (size 1.27 1.27))))',
        f'    (property "Value" "{value}" (at {x} {y+10} 0) (effects (font (size 1.27 1.27))))',
    ]
    if footprint:
        lines.append(f'    (property "Footprint" "{footprint}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))')
    if lcsc:
        lines.append(f'    (property "LCSC" "{lcsc}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))')
    if pins:
        for pin_num in pins:
            lines.append(f'    (pin "{pin_num}" (uuid "{uid()}"))')
    lines.append(f'  )')
    return '\n'.join(lines), u, ref


def build_schematic():
    lib_symbols = build_lib_symbols()

    components = []  # (text, uuid, ref)
    wires = []
    labels_list = []
    sym_instances = []

    def add(lib_id, ref_pre, ref_num, value, pos, lcsc="", fp="", pins=None, angle=0):
        text, u, ref = component(lib_id, ref_pre, ref_num, value, pos[0], pos[1], lcsc, fp, pins, angle)
        components.append(text)
        sym_instances.append(f'    (path "/{u}" (reference "{ref}") (unit 1))')
        return ref

    def net(name, x, y, dx, dy, angle=0):
        """Add a wire stub + label at the end."""
        wx, wy = x + dx, y + dy
        wires.append(wire(x, y, wx, wy))
        labels_list.append(label(name, wx, wy, angle))

    # ════════════════════════════════════════════════════════════════
    # COMPONENT PLACEMENT
    # ════════════════════════════════════════════════════════════════

    # -- Power Section --
    add("USB_C_16P", "J", 1, "USB-C", USB_C, "C2765186", "",
        ["A4", "A5", "B5", "A6", "A7", "A1", "S1"])

    add("D_Schottky", "D", 1, "SS34", SCHOTTKY, "C8678", "Diode_SMD:D_SMA",
        ["1", "2"])

    add("TP4056", "U", 2, "TP4056", TP4056, "C382139", "Package_SO:ESOP-8_3.9x4.9mm_P1.27mm",
        ["8", "3", "2", "1", "6", "7", "4", "5"])

    add("DW01A", "U", 3, "DW01A", DW01A, "C351410", "Package_TO_SOT_SMD:SOT-23-6",
        ["1", "2", "3", "5", "6", "4"])

    add("FS8205A", "Q", 1, "FS8205A", FS8205A, "C908265", "Package_TO_SOT_SMD:SOT-23-6",
        ["1", "2", "6", "5", "3", "4"])

    add("JST_PH_2", "J", 2, "JST-PH-2", JST_BAT, "C131337",
        "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
        ["1", "2"])

    add("AMS1117-3.3", "U", 4, "AMS1117-3.3", LDO, "C6186",
        "Package_TO_SOT_SMD:SOT-223-3_TabPin2", ["3", "2", "1"])

    # Passives - Power
    add("R", "R", 1, "1.2k", RPROG, "C25752", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("LED", "D", 2, "RED", LED_CHG, "C84256", "LED_SMD:LED_0402_1005Metric", ["1", "2"])
    add("LED", "D", 3, "GREEN", LED_DONE, "C72043", "LED_SMD:LED_0402_1005Metric", ["1", "2"])
    add("R", "R", 2, "1k", RLED1, "C25585", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("R", "R", 3, "1k", RLED2, "C25585", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("C", "C", 5, "10uF", C_LDO_IN, "C19702", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])
    add("C", "C", 6, "10uF", C_LDO_OUT, "C19702", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])

    # -- MCU Section: ESP32-S3-WROOM-1-N16R8 --
    add("ESP32-S3-WROOM-1", "U", 1, "ESP32-S3-N16R8", ESP32, "C2913196",
        "RF_Module:ESP32-S3-WROOM-1",
        ["1", "2", "3", "27", "4", "5", "6", "7", "8", "9", "10", "11",
         "13", "14", "15", "16", "17", "18", "19", "20"])

    # Passives - MCU
    add("C", "C", 3, "100nF", C_DEC1, "C14663", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])
    add("C", "C", 4, "10uF", C_DEC2, "C19702", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])
    add("R", "R", 8, "5.1k", R_CC1, "", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("R", "R", 9, "5.1k", R_CC2, "", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("R", "R", 10, "10k", R_EN, "C25744", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])

    # -- Peripherals --
    add("SKRHABE010", "SW", 1, "5-Way Nav", JOYSTICK, "C139794", "",
        ["1", "2", "3", "4", "5", "6"])

    add("EPAPER_HEADER", "J", 3, "ePaper 8pin", EPAPER, "",
        "Connector_JST:JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal",
        ["1", "2", "3", "4", "5", "6", "7", "8"])

    add("LIS2DH12TR", "U", 5, "LIS2DH12TR", ACCEL, "C110926",
        "Package_LGA:LGA-12_2x2mm_P0.5mm",
        ["10", "1", "5", "6", "7", "4", "3", "8", "9", "2"])

    # Passives - Peripherals
    add("R", "R", 4, "10k", R_I2C_SDA, "C25744", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("R", "R", 5, "10k", R_I2C_SCL, "C25744", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("C", "C", 7, "100nF", C_IMU, "C14663", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])

    # BOOT and RESET buttons
    add("SW_Push", "SW", 2, "BOOT", BOOT_BTN, "", "Button_Switch_SMD:SW_SPST_PTS810", ["1", "2"])
    add("SW_Push", "SW", 3, "RESET", RESET_BTN, "", "Button_Switch_SMD:SW_SPST_PTS810", ["1", "2"])
    add("R", "R", 11, "10k", R_BOOT, "C25744", "Resistor_SMD:R_0402_1005Metric", ["1", "2"])
    add("C", "C", 8, "100nF", C_EN_DEB, "C14663", "Capacitor_SMD:C_0402_1005Metric", ["1", "2"])

    # ════════════════════════════════════════════════════════════════
    # NET CONNECTIONS VIA LABELS
    # ════════════════════════════════════════════════════════════════

    # ── VBUS net: USB-C VBUS → Schottky anode ──
    net("VBUS", USB_C[0], USB_C[1]-11.43, 0, -5, 0)
    net("VBUS", SCHOTTKY[0]-3.81, SCHOTTKY[1], -5, 0, 180)

    # ── VBUS_CHG net: Schottky cathode → TP4056 VCC ──
    net("VBUS_CHG", SCHOTTKY[0]+3.81, SCHOTTKY[1], 5, 0, 0)
    net("VBUS_CHG", TP4056[0]-10.16, TP4056[1]-5.08+10.16, -5, 0, 180)

    # ── VBAT net: TP4056 BAT → DW01A VCC → LDO VIN ──
    net("VBAT", TP4056[0]+10.16, TP4056[1]-5.08+10.16, 5, 0, 0)
    net("VBAT", DW01A[0]+8.89, DW01A[1]-2.54, 5, 0, 0)
    net("VBAT", LDO[0]-7.62, LDO[1]-1.27, -5, 0, 180)
    net("VBAT", C_LDO_IN[0], C_LDO_IN[1]-2.54, 0, -3, 0)

    # ── 3V3 net: LDO VOUT → all 3.3V consumers ──
    net("3V3", LDO[0]+7.62, LDO[1]-1.27, 5, 0, 0)
    net("3V3", C_LDO_OUT[0], C_LDO_OUT[1]-2.54, 0, -3, 0)
    # ESP32-S3 3V3 power pin (pin 2, at top center)
    net("3V3", ESP32[0], ESP32[1]-27.94, 0, -5, 0)
    # Decoupling caps
    net("3V3", C_DEC1[0], C_DEC1[1]-2.54, 0, -3, 0)
    net("3V3", C_DEC2[0], C_DEC2[1]-2.54, 0, -3, 0)
    # LIS2DH12 VDD + VDD_IO → 3V3
    net("3V3", ACCEL[0], ACCEL[1]-11.43, 0, -3, 0)                 # VDD
    net("3V3", ACCEL[0]+2.54, ACCEL[1]-11.43, 0, -3, 0)            # VDD_IO
    # e-Paper VCC
    net("3V3", EPAPER[0]-7.62, EPAPER[1]-8.89, -5, 0, 180)
    # I2C pull-ups top
    net("3V3", R_I2C_SDA[0], R_I2C_SDA[1]-2.54, 0, -3, 0)
    net("3V3", R_I2C_SCL[0], R_I2C_SCL[1]-2.54, 0, -3, 0)
    # EN pull-up top
    net("3V3", R_EN[0], R_EN[1]-2.54, 0, -3, 0)
    # LED anodes (through resistors)
    net("3V3", RLED1[0], RLED1[1]-2.54, 0, -3, 0)
    net("3V3", RLED2[0], RLED2[1]-2.54, 0, -3, 0)
    # LIS2DH12 decoupling cap
    net("3V3", C_IMU[0], C_IMU[1]-2.54, 0, -3, 0)
    # TP4056 CE (always enabled)
    net("3V3", TP4056[0]-10.16, TP4056[1]+2.54, -5, 0, 180)

    # ── GND net ──
    # USB-C GND
    net("GND", USB_C[0], USB_C[1]+11.43, 0, 5, 180)
    # USB-C Shield
    net("GND", USB_C[0]+10.16, USB_C[1], 5, 0, 0)
    # TP4056 GND
    net("GND", TP4056[0], TP4056[1]+10.16, 0, 5, 180)
    # TP4056 TEMP (tie to GND to disable temp sense)
    net("GND", TP4056[0]-10.16, TP4056[1], -5, 0, 180)
    # DW01A GND
    net("GND", DW01A[0]+8.89, DW01A[1]+2.54, 5, 0, 0)
    # LDO GND
    net("GND", LDO[0], LDO[1]+6.35, 0, 5, 180)
    # RPROG bottom
    net("GND", RPROG[0], RPROG[1]+2.54, 0, 5, 180)
    # ESP32-S3 GND (pin 1, at bottom center)
    net("GND", ESP32[0], ESP32[1]+27.94, 0, 5, 180)
    # Decoupling caps GND
    net("GND", C_DEC1[0], C_DEC1[1]+2.54, 0, 5, 180)
    net("GND", C_DEC2[0], C_DEC2[1]+2.54, 0, 5, 180)
    net("GND", C_LDO_IN[0], C_LDO_IN[1]+2.54, 0, 5, 180)
    net("GND", C_LDO_OUT[0], C_LDO_OUT[1]+2.54, 0, 5, 180)
    net("GND", C_IMU[0], C_IMU[1]+2.54, 0, 5, 180)
    # Joystick COM
    net("GND", JOYSTICK[0]+10.16, JOYSTICK[1], 5, 0, 0)
    # e-Paper GND
    net("GND", EPAPER[0]-7.62, EPAPER[1]-6.35, -5, 0, 180)
    # LIS2DH12 GND
    net("GND", ACCEL[0], ACCEL[1]+11.43, 0, 5, 180)                # GND
    # LIS2DH12 SA0 → GND (address 0x18)
    net("GND", ACCEL[0]-10.16, ACCEL[1]+2.54, -5, 0, 180)          # SA0 pin LOW
    # LIS2DH12 RES → GND (reserved, tie low per datasheet)
    net("GND", ACCEL[0]+10.16, ACCEL[1]+2.54, 5, 0, 0)             # RES pin
    # CC resistors bottom
    net("GND", R_CC1[0], R_CC1[1]+2.54, 0, 5, 180)
    net("GND", R_CC2[0], R_CC2[1]+2.54, 0, 5, 180)
    # JST battery negative
    net("GND", JST_BAT[0]-6.35, JST_BAT[1]+1.27, -5, 0, 180)

    # LED intermediate nets
    net("CHRG_LED", LED_CHG[0]-3.81, LED_CHG[1], -3, 0, 180)
    net("CHRG_LED", RLED1[0], RLED1[1]+2.54, 0, 3, 180)
    net("STDBY_LED", LED_DONE[0]-3.81, LED_DONE[1], -3, 0, 180)
    net("STDBY_LED", RLED2[0], RLED2[1]+2.54, 0, 3, 180)

    # LED cathode to TP4056 status pins
    net("CHRG_OUT", LED_CHG[0]+3.81, LED_CHG[1], 3, 0, 0)
    net("CHRG_OUT", TP4056[0]+10.16, TP4056[1], 5, 0, 0)
    net("STDBY_OUT", LED_DONE[0]+3.81, LED_DONE[1], 3, 0, 0)
    net("STDBY_OUT", TP4056[0]+10.16, TP4056[1]-2.54, 5, 0, 0)

    # ── PROG net: TP4056 PROG → R1 ──
    net("PROG", TP4056[0]-10.16, TP4056[1]-2.54, -5, 0, 180)
    net("PROG", RPROG[0], RPROG[1]-2.54, 0, -3, 0)

    # ── Battery protection nets ──
    net("OD", DW01A[0]-8.89, DW01A[1]-2.54, -5, 0, 180)
    net("OD", FS8205A[0]-8.89, FS8205A[1], -5, 0, 180)
    net("OC", DW01A[0]-8.89, DW01A[1]+2.54, -5, 0, 180)
    net("OC", FS8205A[0]+8.89, FS8205A[1], 5, 0, 0)
    net("CS_DRAIN", DW01A[0]-8.89, DW01A[1], -5, 0, 180)
    net("CS_DRAIN", FS8205A[0]-8.89, FS8205A[1]+2.54, -5, 0, 180)
    net("CS_DRAIN", FS8205A[0]+8.89, FS8205A[1]+2.54, 5, 0, 0)
    net("GND", FS8205A[0]-8.89, FS8205A[1]-2.54, -5, 0, 180)
    net("BAT_PLUS", FS8205A[0]+8.89, FS8205A[1]-2.54, 5, 0, 0)
    net("BAT_PLUS", JST_BAT[0]-6.35, JST_BAT[1]-1.27, -5, 0, 180)
    net("VBAT", DW01A[0]+8.89, DW01A[1], 5, 0, 0)

    # ── USB data: USB-C D+/D- → ESP32-S3 directly (native USB-OTG) ──
    net("USB_DP", USB_C[0]-10.16, USB_C[1]+2.54, -5, 0, 180)
    net("USB_DP", ESP32[0]-17.78, ESP32[1]+7.62, -5, 0, 180)    # GPIO20/D+

    net("USB_DM", USB_C[0]-10.16, USB_C[1]+5.08, -5, 0, 180)
    net("USB_DM", ESP32[0]-17.78, ESP32[1]+5.08, -5, 0, 180)    # GPIO19/D-

    # USB CC pins → 5.1k → GND
    net("CC1", USB_C[0]-10.16, USB_C[1]-2.54, -5, 0, 180)
    net("CC1", R_CC1[0], R_CC1[1]-2.54, 0, -3, 0)
    net("CC2", USB_C[0]-10.16, USB_C[1], -5, 0, 180)
    net("CC2", R_CC2[0], R_CC2[1]-2.54, 0, -3, 0)

    # ── RESET button (EN): R10 pull-up + C8 debounce + SW3 to GND ──
    net("EN", ESP32[0]-17.78, ESP32[1]-22.86, -5, 0, 180)          # EN pin (existing)
    net("EN", R_EN[0], R_EN[1]+2.54, 0, 3, 180)                    # R10 bottom → EN (existing)
    net("EN", RESET_BTN[0]-3.81, RESET_BTN[1], -3, 0, 180)         # SW3 pin 1 → EN
    net("GND", RESET_BTN[0]+3.81, RESET_BTN[1], 3, 0, 0)           # SW3 pin 2 → GND
    net("EN", C_EN_DEB[0], C_EN_DEB[1]-2.54, 0, -3, 0)             # C8 top → EN
    net("GND", C_EN_DEB[0], C_EN_DEB[1]+2.54, 0, 5, 180)           # C8 bottom → GND

    # ── BOOT button (GPIO0): R11 pull-up + SW2 to GND ──
    net("BOOT", ESP32[0]-17.78, ESP32[1]-20.32, -5, 0, 180)        # GPIO0 (new pin)
    net("BOOT", BOOT_BTN[0]-3.81, BOOT_BTN[1], -3, 0, 180)         # SW2 pin 1
    net("GND", BOOT_BTN[0]+3.81, BOOT_BTN[1], 3, 0, 0)             # SW2 pin 2 → GND
    net("3V3", R_BOOT[0], R_BOOT[1]-2.54, 0, -3, 0)                # R11 top → 3V3
    net("BOOT", R_BOOT[0], R_BOOT[1]+2.54, 0, 3, 180)              # R11 bottom → BOOT net

    # ── Joystick GPIO4-8 (active LOW, internal pull-ups) ──
    net("JOY_UP", JOYSTICK[0]-10.16, JOYSTICK[1]-5.08, -5, 0, 180)
    net("JOY_UP", ESP32[0]-17.78, ESP32[1]-17.78, -5, 0, 180)       # GPIO4

    net("JOY_DOWN", JOYSTICK[0]-10.16, JOYSTICK[1]-2.54, -5, 0, 180)
    net("JOY_DOWN", ESP32[0]-17.78, ESP32[1]-15.24, -5, 0, 180)     # GPIO5

    net("JOY_LEFT", JOYSTICK[0]-10.16, JOYSTICK[1], -5, 0, 180)
    net("JOY_LEFT", ESP32[0]-17.78, ESP32[1]-12.7, -5, 0, 180)      # GPIO6

    net("JOY_RIGHT", JOYSTICK[0]-10.16, JOYSTICK[1]+2.54, -5, 0, 180)
    net("JOY_RIGHT", ESP32[0]-17.78, ESP32[1]-10.16, -5, 0, 180)    # GPIO7

    net("JOY_CENTER", JOYSTICK[0]-10.16, JOYSTICK[1]+5.08, -5, 0, 180)
    net("JOY_CENTER", ESP32[0]-17.78, ESP32[1]-7.62, -5, 0, 180)    # GPIO8

    # ── e-Paper SPI: ESP32 → J3 connector ──
    # GPIO9/SCK → J3 pin 4 (CLK)
    net("EPD_CLK", ESP32[0]+17.78, ESP32[1]-17.78, 5, 0, 0)
    net("EPD_CLK", EPAPER[0]-7.62, EPAPER[1]-1.27, -5, 0, 180)

    # GPIO10/MOSI → J3 pin 3 (DIN)
    net("EPD_MOSI", ESP32[0]+17.78, ESP32[1]-15.24, 5, 0, 0)
    net("EPD_MOSI", EPAPER[0]-7.62, EPAPER[1]-3.81, -5, 0, 180)

    # GPIO3/DC → J3 pin 6 (DC)
    net("EPD_DC", ESP32[0]+17.78, ESP32[1]-12.7, 5, 0, 0)
    net("EPD_DC", EPAPER[0]-7.62, EPAPER[1]+3.81, -5, 0, 180)

    # GPIO11/RST → J3 pin 7 (RST)
    net("EPD_RST", ESP32[0]+17.78, ESP32[1]-10.16, 5, 0, 0)
    net("EPD_RST", EPAPER[0]-7.62, EPAPER[1]+6.35, -5, 0, 180)

    # GPIO46/CS → J3 pin 5 (CS)
    net("EPD_CS", ESP32[0]+17.78, ESP32[1]-7.62, 5, 0, 0)
    net("EPD_CS", EPAPER[0]-7.62, EPAPER[1]+1.27, -5, 0, 180)

    # GPIO12/BUSY → J3 pin 8 (BUSY)
    net("EPD_BUSY", ESP32[0]+17.78, ESP32[1]-5.08, 5, 0, 0)
    net("EPD_BUSY", EPAPER[0]-7.62, EPAPER[1]+8.89, -5, 0, 180)

    # ── LIS2DH12 I2C: GPIO16/17 + GPIO18 (INT1) ──
    net("I2C_SDA", ESP32[0]-17.78, ESP32[1]-2.54, -5, 0, 180)      # GPIO16
    net("I2C_SDA", ACCEL[0]-10.16, ACCEL[1]-5.08, -5, 0, 180)      # SDA pin
    net("I2C_SDA", R_I2C_SDA[0], R_I2C_SDA[1]+2.54, 0, 3, 180)

    net("I2C_SCL", ESP32[0]-17.78, ESP32[1], -5, 0, 180)            # GPIO17
    net("I2C_SCL", ACCEL[0]-10.16, ACCEL[1]-2.54, -5, 0, 180)      # SCL pin
    net("I2C_SCL", R_I2C_SCL[0], R_I2C_SCL[1]+2.54, 0, 3, 180)

    # GPIO18 → LIS2DH12 INT1
    net("ACCEL_INT1", ESP32[0]-17.78, ESP32[1]+2.54, -5, 0, 180)   # GPIO18 (new pin)
    net("ACCEL_INT1", ACCEL[0]+10.16, ACCEL[1]-5.08, 5, 0, 0)      # INT1 pin

    # LIS2DH12 CS → 3V3 (I2C mode)
    net("3V3", ACCEL[0]-10.16, ACCEL[1], -5, 0, 180)               # CS pin HIGH

    # ════════════════════════════════════════════════════════════════
    # TEXT ANNOTATIONS
    # ════════════════════════════════════════════════════════════════

    texts = []
    texts.append(f'  (text "POWER: USB-C > SS34 > TP4056 > DW01A/FS8205A > Battery" (exclude_from_sim no) (at 115 35 0) (effects (font (size 2.54 2.54)) (justify left)))')
    texts.append(f'  (text "VBAT > AMS1117-3.3 > 3V3 Rail > All ICs" (exclude_from_sim no) (at 115 40 0) (effects (font (size 2.54 2.54)) (justify left)))')
    texts.append(f'  (text "MCU: ESP32-S3-WROOM-1-N16R8 (WiFi+BLE, 16MB flash, 8MB PSRAM)" (exclude_from_sim no) (at 115 140 0) (effects (font (size 2.54 2.54)) (justify left)))')
    texts.append(f'  (text "GPIO0=BOOT  GPIO4-8=Joystick  GPIO9/10=SPI(CLK/MOSI)  GPIO3=DC  GPIO11=RST  GPIO46=CS  GPIO12=BUSY" (exclude_from_sim no) (at 50 250 0) (effects (font (size 1.8 1.8)) (justify left)))')
    texts.append(f'  (text "GPIO16/17=I2C(SDA/SCL)  GPIO18=ACCEL_INT1  GPIO19/20=USB(D-/D+)  EN=RESET" (exclude_from_sim no) (at 50 255 0) (effects (font (size 1.8 1.8)) (justify left)))')

    # ════════════════════════════════════════════════════════════════
    # ASSEMBLE THE FILE
    # ════════════════════════════════════════════════════════════════

    output = f'''(kicad_sch
  (version 20250610)
  (generator "eeschema")
  (generator_version "10.0")
  (uuid "e63e39d7-6ac0-4ffd-8aa3-1841a4541b55")
  (paper "A3")
  (title_block
    (title "Dilder - Custom PCB")
    (date "2026-04-15")
    (rev "0.4")
    (company "Dilder Project")
    (comment 1 "ESP32-S3-WROOM-1-N16R8 + LiPo + Joystick + LIS2DH12 + ePaper + BOOT/RESET")
    (comment 2 "Target: JLCPCB SMT Assembly — WiFi+BLE integrated")
  )
  {lib_symbols}
{chr(10).join(components)}
{chr(10).join(wires)}
{chr(10).join(labels_list)}
{chr(10).join(texts)}
  (symbol_instances
{chr(10).join(sym_instances)}
  )
)
'''
    return output


if __name__ == "__main__":
    import subprocess

    print("Generating Dilder schematic v0.4 (ESP32-S3 version, 28 components)...")
    sch = build_schematic()

    outfile = "dilder.kicad_sch"
    with open(outfile, "w") as f:
        f.write(sch)
    print(f"  Wrote {outfile} ({len(sch)} bytes)")

    # Validate with kicad-cli
    print("  Validating...")
    result = subprocess.run(
        ["kicad-cli", "sch", "export", "svg", "--output", "/tmp/dilder-gen/", outfile],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  OK — exported to /tmp/dilder-gen/dilder.svg")
    else:
        print(f"  FAIL — {result.stderr}")
        raise SystemExit(1)

    print("Done. Open in KiCad to verify and run ERC.")
