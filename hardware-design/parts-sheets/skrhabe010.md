# SKRHABE010 — Alps Alpine 5-Way SMD Joystick

## Table of Contents

- [Quick Reference](#quick-reference)
- [What Is This Part?](#what-is-this-part)
- [How a Multi-Direction Switch Works](#how-a-multi-direction-switch-works)
  - [Mechanical Design](#mechanical-design)
  - [The Rocker Mechanism](#the-rocker-mechanism)
  - [Contact Physics](#contact-physics)
- [Key Specifications](#key-specifications)
- [Pin Connections on Dilder Board](#pin-connections-on-dilder-board)
- [Software Interface](#software-interface)
- [Debouncing](#debouncing)
- [Replaces the Breadboard Module](#replaces-the-breadboard-module)
- [History and Background](#history-and-background)
- [Datasheet and Sources](#datasheet-and-sources)

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Manufacturer** | Alps Alpine Co., Ltd. (Tokyo, Japan) |
| **Part Number** | SKRHABE010 |
| **Function** | 5-direction SMD navigation switch (UP/DOWN/LEFT/RIGHT + center push) |
| **Package** | SMD, 7.4 x 7.5 x 1.8 mm |
| **LCSC** | [C139794](https://www.lcsc.com/product-detail/C139794.html) |
| **Price (qty 5)** | ~$0.38 |
| **Dilder ref** | SW1 |

---

## What Is This Part?

The SKRHABE010 is a **5-way navigation switch** — a tiny joystick that can be pressed in four directions (up, down, left, right) and pushed straight down (center click). It's the same type of control you'd find on old iPods, feature phones, or digital cameras.

In the Dilder, this is the primary input device. Players navigate menus, interact with the virtual pet, and control the UI using these five inputs. Each direction is a separate momentary switch that connects to ground when pressed.

It's only 1.8mm tall — thin enough to fit inside a slim handheld enclosure with a small button cap on top.

---

## How a Multi-Direction Switch Works

### Mechanical Design

The SKRHABE010 has a small rocker actuator on top (a dome-shaped nub about 2mm diameter). Underneath this actuator are **five separate contact pairs** arranged in a cross pattern:

```
         ┌─────────┐
         │   UP    │
         │   ⬤    │
    ┌────┤         ├────┐
    │LEFT│ CENTER  │RIGHT│
    │ ⬤  │   ⬤    │  ⬤ │
    └────┤         ├────┘
         │  DOWN   │
         │   ⬤    │
         └─────────┘
    
    (⬤ = contact dome underneath actuator)
```

### The Rocker Mechanism

When you push the actuator in a direction (say, up), a lever mechanism deflects a metal dome contact downward, completing the UP circuit. The center push compresses a separate contact directly below the actuator.

The four directional contacts use a **tactile dome** (a small metal disc that snaps when pressed). The snap provides tactile feedback — you feel a click when the switch activates, confirming your input. The center push has its own dome with a slightly higher activation force (3.0N vs 2.0N for directions) so accidental center-clicks are less likely during directional inputs.

Each switch is independent — the rocker mechanism doesn't prevent pressing two directions simultaneously (like UP + RIGHT for diagonal), though the physical actuator makes this difficult for human fingers.

### Contact Physics

The contacts are made of **silver-plated copper alloy**. When the dome deflects and touches the fixed contact pad, electrical continuity is established. The contact resistance is specified as less than 1Ω — essentially zero compared to the 10kΩ pull-up resistors in the circuit.

The silver plating prevents oxidation that would increase contact resistance over time. The rated life of 100,000 cycles per direction means at 100 presses per day, the switch would last nearly 3 years — well beyond the expected product lifetime.

---

## Key Specifications

| Parameter | Value |
|-----------|-------|
| Directions | 4-way rocker + center push (5 total) |
| Contact type | Momentary, normally open (NO) |
| Operating force (direction) | 2.0N (±0.75N) |
| Operating force (center) | 3.0N (±1.0N) |
| Contact resistance | 1.0Ω max |
| Rated voltage | 12V DC |
| Rated current | 50 mA |
| Insulation resistance | 100 MΩ min |
| Mechanical life | 100,000 cycles per direction |
| Operating temp | -20°C to +70°C |
| Dimensions | 7.4 x 7.5 x 1.8 mm |

---

## Pin Connections on Dilder Board

| Switch Pin | Pin # | ESP32-S3 GPIO | Direction | Net |
|------------|-------|---------------|-----------|-----|
| UP | 1 | GPIO4 | Up | JOY_UP |
| DOWN | 2 | GPIO5 | Down | JOY_DOWN |
| LEFT | 3 | GPIO6 | Left | JOY_LEFT |
| RIGHT | 4 | GPIO7 | Right | JOY_RIGHT |
| CENTER | 5 | GPIO8 | Center push | JOY_CENTER |
| COM | 6 | GND | Common ground | GND |

---

## Software Interface

Each direction is wired as a simple switch between the GPIO pin and ground:

```
  3.3V ──[10k internal pull-up]── GPIO4 ──┤ ├── GND
                                           SW1 UP
  
  Not pressed: GPIO4 reads HIGH (3.3V)
  Pressed:     GPIO4 reads LOW  (GND)
```

The ESP32-S3's internal pull-up resistors are enabled in software (`gpio_set_pull_mode(GPIO_NUM_4, GPIO_PULLUP_ONLY)`). No external pull-up resistors are needed.

**Reading the joystick:**
```c
// Active LOW — pressed = 0
bool up     = !gpio_get_level(GPIO_NUM_4);
bool down   = !gpio_get_level(GPIO_NUM_5);
bool left   = !gpio_get_level(GPIO_NUM_6);
bool right  = !gpio_get_level(GPIO_NUM_7);
bool center = !gpio_get_level(GPIO_NUM_8);
```

---

## Debouncing

Mechanical switches don't make clean transitions. When a contact closes, it physically bounces — making and breaking contact several times in the first 1-5 milliseconds. This can register as multiple button presses.

**Hardware debouncing** would add a small capacitor (10-100nF) across each switch. The Dilder doesn't use this — the passive components would add 5 caps and board space.

**Software debouncing** is used instead: after detecting a state change, the firmware ignores further changes for 20-50ms. This is simpler and uses no additional components. The ESP32-S3 has plenty of processing power for software debounce.

---

## Replaces the Breadboard Module

The breadboard prototype used a **DollaTek 5-way through-hole navigation module** (~$3). The SKRHABE010 provides the same 5 inputs in a surface-mount package:

| Factor | DollaTek Module | SKRHABE010 |
|--------|----------------|------------|
| Type | Through-hole breakout | SMD component |
| Height | ~10mm | 1.8mm |
| Cost | ~$3.00 | ~$0.38 |
| Mounting | Pin headers | Solder pads (pick-and-place) |
| Logic | Same active-LOW | Same active-LOW |

---

## History and Background

**Alps Alpine** (formed in 2019 by the merger of Alps Electric and Alpine Electronics) is a Japanese manufacturer of electronic components. Alps Electric was founded in 1948 in Tokyo and is one of the world's largest manufacturers of:
- Tactile switches and buttons
- Encoders and potentiometers
- Touchpads and pointing devices
- Automotive infotainment controls

Alps supplies components to nearly every major electronics brand — their switches are inside PlayStation controllers, laptop trackpads, car dashboards, and medical devices. The SKRHABE010 is from their "Multidirectional Switches" product line, designed for portable devices and remote controls.

The 5-way navigation switch concept dates back to the early 2000s when mobile phones needed compact directional controls for navigating menus (before touchscreens). Nokia's iconic phones used similar Alps switches. While smartphones have made these switches less common in phones, they remain popular in cameras, medical devices, industrial controls, and hobbyist projects where physical buttons are preferred over touchscreens.

---

## Datasheet and Sources

- **LCSC product page:** [C139794](https://www.lcsc.com/product-detail/C139794.html)
- **Alps Alpine product page:** [SKRHABE010](https://tech.alpsalpine.com/e/products/detail/SKRHABE010/)
- **Alps Alpine switch guide:** [tech.alpsalpine.com/e/products/category/switch/](https://tech.alpsalpine.com/e/products/category/switch/)
- **Mouser product page:** [SKRHABE010 on Mouser](https://www.mouser.com/ProductDetail/Alps-Alpine/SKRHABE010)
- **Wikipedia — Alps Alpine:** [en.wikipedia.org/wiki/Alps_Alpine](https://en.wikipedia.org/wiki/Alps_Alpine)
