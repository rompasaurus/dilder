---
date: 2026-04-15
authors:
  - rompasaurus
categories:
  - Hardware
  - Design
slug: motion-location-detection
---

# Teaching the Octopus to Feel — Motion & Location Without GPS

The Dilder just got a new sense. We swapped out the $6.88 MPU-6050 gyroscope for a $0.46 accelerometer that does *more* with *less* — and designed a location system that doesn't need GPS at all.

<!-- more -->

## The MPU-6050 Had to Go

The original design included an MPU-6050, a 6-axis IMU with both accelerometer and gyroscope. It's a capable chip, but for a virtual pet that needs to count steps and detect shakes, half of it was dead weight. The gyroscope measures rotational velocity — useful for drones and VR controllers, completely unnecessary for knowing if someone is walking.

Worse, at $6.88 per unit, it was the most expensive component on the board after the ESP32-S3 module itself.

## Enter the LIS2DH12TR

The replacement is the STMicroelectronics LIS2DH12TR — a 3-axis accelerometer in a 2x2mm LGA-12 package. At **$0.46** on LCSC, it costs less than a single decoupling capacitor would cost at retail.

But the price isn't the interesting part. The LIS2DH12 has a **built-in hardware pedometer**. The step counting algorithm runs inside the chip at 2uA, accumulating steps in a 16-bit register even while the ESP32-S3 is in deep sleep. No software pedometer, no polling, no wasted cycles.

The chip also provides:

- **Tap and double-tap detection** — pet the octopus with a single tap, feed it with a double-tap
- **Activity/inactivity interrupts** — the device knows when it's been picked up or set down, no polling required
- **6D orientation detection** — which face is pointing up (face-down could mean sleep mode)
- **Free-fall detection** — "You dropped me!" before impact

All of these generate hardware interrupts. The ESP32-S3 can stay in deep sleep until something actually happens.

## Location Without GPS

A virtual pet that knows it's in a *different place* is more interesting than one that knows its latitude. We don't need GPS — we need location *changes*.

### WiFi Fingerprinting

The ESP32-S3 scans for nearby WiFi access points during each wake cycle. Each location has a unique pattern of BSSIDs and signal strengths. The device stores a fingerprint of each place it recognizes:

- **Home** has routers X and Y at strong signal
- **Office** has routers A, B, and C
- **Coffee shop** has a completely different set

When the fingerprint changes significantly, the pet knows you went somewhere. That triggers exploration moods, new quotes, and engagement bonuses. No GPS module, no antenna, no extra power draw — the WiFi radio was already on the board.

### BLE Peer Detection

The ESP32-S3's Bluetooth 5 LE radio enables one more trick: **peer discovery**. When two Dilders are within BLE range, they can detect each other. Your octopus knows when another octopus is nearby. Social interactions, trading, competitive moods — all enabled by hardware that was already in the design.

## The Numbers

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| Motion sensor | MPU-6050 ($6.88) | LIS2DH12TR ($0.46) | **-$6.42** |
| GPS module | ATGM336H ($1.80, planned) | Dropped entirely | **-$1.80** |
| **Total per board** | | | **-$8.22** |

The new sensor is cheaper, smaller (2x2mm vs 4x4mm QFN), uses less power (2uA in pedometer mode vs 3.9mA for the MPU-6050), and does more of the work in hardware. The GPS module was dropped entirely — WiFi fingerprinting gives us what we actually need.

## How It Connects to the Pet

The motion and location data feeds directly into the engagement system:

- **Steps walked** increase the pet's happiness and energy stats
- **Shaking the device** triggers surprise or annoyance depending on mood
- **Being set down for hours** makes the pet lonely or lazy
- **Visiting a new location** triggers exploration moods and unique quotes
- **Being near another Dilder** enables social interactions

The octopus doesn't just sit on a screen waiting for button presses. It responds to how you carry it through the world.

## What's Next

The LIS2DH12TR is placed on the custom PCB at position (6, 47) in Zone D, connected via I2C on GPIO16/17 with INT1 on GPIO18. The breadboard prototype uses an Adafruit LIS3DH breakout as a pin-compatible stand-in. Next up: writing the ESP-IDF driver and wiring the interrupt handler.

The octopus can feel you now.
