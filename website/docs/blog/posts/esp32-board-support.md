---
date: 2026-04-17
authors:
  - rompasaurus
categories:
  - Hardware
  - DevTool
slug: esp32-board-support
---

# ESP32-S3 Board Support — Multi-Board Architecture Goes Live

The Olimex ESP32-S3-DevKit-Lipo is now a fully supported second target board alongside the Pico W. The DevTool, setup CLI, and firmware all handle both boards natively — no forks, no feature flags, just a board selector.

<!-- more -->

## DevTool Changes

The Programs tab gained a **Target Board** dropdown. Selecting ESP32 switches Deploy Standalone and Flash to use PlatformIO instead of UF2/BOOTSEL. The Connect tab adapts too — it shows CH340X USB-serial steps for ESP32 (including download mode via BOOT + RST buttons) versus the ttyACM workflow for Pico.

## Setup CLI

`setup.py` now accepts `--board pico` or `--board esp32` to filter steps for one board. Without the flag, an interactive board selection menu appears at startup. On Arch/CachyOS, the CLI uses `pipx` instead of `pip install --user` to avoid PEP 668 externally-managed-environment errors. The dev setup guide covers both boards side-by-side in every step.

## Firmware

PlatformIO handles all ESP32 builds and flashing. Auto-reset via DTR means no BOOTSEL dance — `pio run -t upload` flashes directly. The firmware compiles with a HAL abstraction layer using `extern "C"` linkage so C firmware links cleanly against the C++ Arduino-ESP32 SDK. A shared `board_config.h` provides compile-time pin selection per board. The resulting ESP32 firmware image is 293KB.

## What Changed Under the Hood

The CMakeLists.txt gained board-conditional paths. Platform-specific source lives in `firmware/src/platform/esp32s3/` with HAL implementations for GPIO, SPI, and timing. The build system picks the right HAL at compile time based on the target board — same application code, different hardware interface.