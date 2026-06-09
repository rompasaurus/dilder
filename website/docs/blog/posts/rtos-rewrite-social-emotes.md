---
date: 2026-06-09
authors:
  - rompasaurus
categories:
  - Firmware
  - RTOS
  - Milestone
tags:
  - freertos
  - rtos
  - bluetooth
  - social
  - emotes
  - debugging
slug: rtos-rewrite-social-emotes
---

# Dilder Goes Real-Time: FreeRTOS, Dilder-to-Dilder Hellos, and a BUSY-Line Whodunit

The Dilder firmware grew up this month. It moved off a single bare-metal super-loop and onto **FreeRTOS running on both cores** of the RP2350, learned how to **wave hello to other Dilders in the wild**, got a proper **emote system**, and — along the way — taught us to read a board's health from a single line of serial output while chasing down three "dead" units that turned out to be very much alive.

<!-- more -->

## Why rewrite it at all?

The old firmware was one big loop: animate the octopus, poll the joystick, refresh the e-ink, repeat. The problem is that an e-ink refresh **takes about 700 ms**, and during that whole time the loop couldn't do anything else — including notice that you pressed a button. Inputs felt mushy, and the longer the screen took, the worse it got.

The fix is the classic real-time-systems move: **stop doing slow things on the same thread as responsive things.** So the firmware was rebuilt on **FreeRTOS in dual-core SMP mode**:

- **Core 1** does nothing but drive the e-ink display.
- **Core 0** runs everything else — input, the UI/state machine, and a housekeeping task for sensors and battery.

The slow screen refresh now happens *beside* the rest of the device instead of *blocking* it. Buttons stay responsive even mid-refresh, and the architecture has room to grow.

## Dilders can say hello now 🐙👋

The headline feature: **proximity social**. Turn on scanning in the new **Social** menu, and when another Dilder comes into Bluetooth range, yours pipes up — *"A DILDER APPEARS IN THE WILD! Say hi?"*

Say yes and you pick an **emote** to send. The octopus stays on screen and **acts it out**:

- **WAVE** — a little hand waves back and forth
- **LOVE** — hearts float up
- **LAUGH** — "HAHA" bounces
- **PARTY** — music notes bob
- **SLEEPY** — "Z z z" stacks up
- **WHOA** — "!!!"

The other Dilder sees your emote performed on *its* octopus, with a caption, and gets a menu to respond. If you both spot each other at the same instant, whoever fires first wins and the other's screen flips from "say hi?" to "…says hello!" — the race is handled.

Every Dilder gets an auto-generated, gloriously stupid name derived from a random ID (think *Unhinged Trashpanda* or *Soggy Noodle*), so the names are consistent everywhere without ever being transmitted. There's a **Dilders Met** log, a 24-hour re-greet cooldown so it never spams, and you can re-roll your own name in the menu.

The clever part under the hood: the whole exchange is **connectionless**. Instead of pairing and connecting (which two Dilders can't do — neither can type the other's passkey), each Dilder simply **broadcasts** a tiny beacon in its Bluetooth advertisement, with a "directed emote" field aimed at a specific ID for ~15 seconds. The other one sees it while scanning. No pairing, no connection, and it never touches the secure phone-pairing path. It also gracefully handles the other Dilder wandering out of range mid-greeting.

## The input trick: pace the buttons to the screen

E-ink is slow, so a held or mashed button used to pile up a backlog of "ghost" presses that all fired after the refresh finished — you'd tap once and the menu would jump three items.

The neat fix: **pace input to the display itself.** The firmware already knows exactly when the panel is busy (a frame is in flight) versus idle. So now a press fires **instantly when the screen is idle**, a mash *during* a refresh **collapses into one move**, and **holding a direction scrolls at exactly the panel's real refresh rate** — never faster, never backed up. No magic timeout; the response time tunes itself to the hardware.

## The BUSY-line whodunit 🔎

Then three units "died." Snow on the screen, refusing to boot — but they'd still accept a firmware flash just fine. Was it the battery? Over-discharge? The missing accelerometer? A fried board?

The serial log cracked it in one line. A healthy e-ink refresh logs **~700 ms**. The dead units logged:

- **~21 ms** on two of them, and
- **~5000 ms** (or nothing at all) on the third.

That's the **BUSY signal** — the wire the display uses to say "I'm still drawing." If it never asserts, the refresh "finishes" in 21 ms having drawn nothing (snow). If it's stuck on, the driver waits forever (freeze). Both point at one pin: **the e-ink BUSY line on a hand-soldered 2×4 header**, where BUSY sits in a corner right next to a data pin and a power pin — exactly where a sloppy iron leaves a solder bridge or a cold joint.

So: **not the silicon.** The boards, flash, and firmware were all fine. Three display-connection faults from the same assembly step. The cure is a soldering-iron, not a landfill.

The whole adventure left the firmware tougher, too. We added **timeouts** to the things that can hang on bad hardware — the accelerometer I²C probe and the e-ink BUSY wait — so a missing sensor or a stuck panel can **never freeze the device at boot** again. It degrades to a diagnosable state instead of bricking. And the refresh-time reading became a one-glance health meter:

> **~700 ms = healthy · ~20 ms = BUSY open/dead · ~5 s = BUSY stuck.**

## Also in this drop

- **Battery gauge** reworked to a load-aware **peak-hold + smoothing** reading (e-ink and the radio sag the rail; the peak across a window tracks the true resting voltage), with **no calibration ritual** required.
- A hard look at the **charging path** turned up the real Rev 1 power flaw — the running load hangs on the battery node with no power-path, so the radio can **starve the charger**. That's now a blocking requirement for the Rev 2 board (true load-sharing + reverse-polarity protection + a keyed connector).
- New **Social** status icon, every new screen works in **both screen orientations**, and the DevTool gained a **Full Erase** button to recover flash-corrupted units.

## Where this leaves us

Dilder is now a real-time, multi-core, *social* device — and considerably harder to brick. Two Dilders in the same room can wave at each other. The next time you see snow on an e-ink screen, check the refresh time before you blame the chip. 🐙
