# Dilder Hub RTOS — Start Here

Welcome. This folder is a **rewrite of the Dilder Hub firmware on top of a real-time
operating system (FreeRTOS)**, written deliberately as a *teaching codebase*. If you
know JavaScript but are new to C, microcontrollers, and operating-system concepts,
these docs are written for you. Nothing is assumed.

---

## What is this thing?

The **Dilder** is a handheld gadget: a Raspberry Pi **Pico 2 W** board (which contains
an **RP2350** chip — two CPU cores, 520 KB of RAM), a small **e-ink** screen, a 5-way
joystick, an accelerometer, a battery, and Wi-Fi/Bluetooth. The firmware draws an
animated octopus that shows moods and quotes, tracks your steps, talks to your phone
over Bluetooth, and can update itself over Wi-Fi.

The **original** firmware (`../dilder-hub`) works, but it is one giant loop running on a
single core. When the e-ink screen refreshes — which takes about **300 milliseconds** —
the whole program is stuck waiting, so button presses feel laggy or get dropped.

This **RTOS version** fixes that by running several independent **tasks** that the
operating system schedules across **both** CPU cores. The slow screen refresh runs on
one core while buttons, sensors, and Wi-Fi keep running on the other. Buttons stay
instant.

> **The one-sentence "why":** an RTOS lets the firmware do several things at once, so a
> slow job (the screen) can't freeze the responsive jobs (the buttons).

---

## What is an "RTOS" and why does a toy need one?

**RTOS** = *Real-Time Operating System*. It is **not** like Windows or Linux — there is
no desktop, no files, no users. It is a tiny library (FreeRTOS) compiled directly into
our firmware whose **only** job is to share the CPU(s) between several pieces of our own
code, called **tasks**, and to let those tasks talk to each other safely.

If you come from JavaScript, the closest mental model:

| JavaScript | This firmware (FreeRTOS) |
|---|---|
| One thread, an event loop, `async`/`await` | Several **tasks**, each like its own little `while(true)` loop |
| The engine decides when callbacks run | The **scheduler** decides which task runs on which core, by **priority** |
| `await fetch()` yields so other code runs | A task calls `vTaskDelay()` or waits on a **queue** to yield |
| You never see threads or locks | You DO — two cores can touch the same memory at once, so we use **mutexes** |
| Garbage collector frees memory | **You** manage memory; there is no GC (see doc 04) |

The Dilder "needs" one because it has genuinely concurrent work — refresh the screen,
poll the joystick, read the accelerometer, service Wi-Fi/Bluetooth, keep a clock — and
on a single thread those fight each other. See **doc 03** for the full primer.

---

## How to read this codebase

1. **Read the docs in order** (below). They build on each other.
2. **Every source file starts with a banner comment** explaining its purpose, which task
   uses it, and what it owns. Read the banner before the code.
3. **Comments are verbose on purpose.** Where C does something that has no JavaScript
   equivalent (pointers, casts, bit operations, manual memory), the comment spells it
   out. This is unusual for production C — it is intentional here.
4. When a comment says *"WHY:"* it is explaining an engineering decision, not just what
   the code does.

---

## The documentation set (read in this order)

| # | Doc | What it covers |
|---|---|---|
| 00 | **00-START-HERE.md** (this file) | Orientation, the big picture |
| 01 | **01-ENVIRONMENT-SETUP.md** | Step-by-step: install every tool/library/dependency and build it from a blank machine |
| 02 | **02-FILE-MANIFEST.md** | Every single file — source, config, generated, and build output — explained, plus the directory tree |
| 03 | **03-RTOS-PRIMER-FOR-JS-DEVS.md** | Tasks, scheduler, priorities, preemption, cores — from zero |
| 04 | **04-MEMORY-POINTERS-ADDRESSING.md** | Pointers, the stack vs the heap, addresses, `volatile`, no garbage collector |
| 05 | **05-DESIGN-AND-ARCHITECTURE.md** | The task model, why dual-core SMP, how a frame flows to the screen |
| 06 | **06-SYNCHRONIZATION.md** | Queues, mutexes, task notifications, race conditions, deadlocks |
| 07 | **07-BUILD-AND-DEPLOY.md** | How to compile, flash over USB, and update over Wi-Fi (incl. the DevTool) |
| 08 | **08-FUNCTION-REFERENCE.md** | Per-module breakdown of the important functions and calls |
| 09 | **09-SOURCES-AND-FURTHER-READING.md** | Cited, linked references that justify these design choices |

---

## Project status (phased build)

This firmware is built in phases so each step is independently testable. See
**05-DESIGN-AND-ARCHITECTURE.md** for details.

- ✅ **Phase 0/1 — DONE:** FreeRTOS is integrated; the entire original program runs as a
  single task under the scheduler on core 0; builds for USB and Wi-Fi-OTA. This proves
  the operating system, Wi-Fi, Bluetooth, and the updater all work under the RTOS.
- 🔜 **Phase 2 — task split:** carve the monolith into Input / UI / Display / Housekeeping
  tasks and pin the slow Display task to core 1 (the responsiveness payoff).
- 🔜 **Phase 3 — hardening:** background sensor task, multicore-safe flash writes, a
  hardware interrupt for the screen-busy signal, and stack tuning.

Where a doc describes Phase 2/3 design that is not yet in the code, it says so.

---

## The absolute fastest path to seeing it run

If you just want it on the device, jump to **07-BUILD-AND-DEPLOY.md**. The short version
(after doing **01-ENVIRONMENT-SETUP.md** once) is:

```bash
cd dev-setup/dilder-hub-rtos
mkdir build && cd build
cmake -G Ninja -DPICO_BOARD=pico2_w -DDISPLAY_VARIANT=V4 ..
ninja
# hold BOOTSEL, plug in the Pico, copy dilder_hub_rtos.uf2 onto the RP2350 drive
```

…or use the **DevTool** GUI (Programs / Picotool / OTA tabs) which now lists
`dilder-hub-rtos` as a selectable target.
