<div id="octopus-banner"></div>

# Dilder

**A real-time build journal for an open-source AI-assisted virtual pet.**

Dilder is a Tamagotchi-style device built on a Raspberry Pi Pico W, a Waveshare 2.13" e-ink display, and a 3D-printed case — developed entirely in the open, one phase at a time.

---

## What is Dilder?

Dilder is part hardware project, part learning experiment, part documentation exercise.

The goal is to build a functional pocket virtual pet from scratch — and document every decision, mistake, and breakthrough along the way. Hardware selection, enclosure design, firmware, animations, personality systems — all of it is public, with every AI prompt and design iteration logged.

If you've ever wanted to follow a project from "I have an idea" to "here's a working device," this is that.

---

## Current Phase

!!! info "Phase 2 — Firmware Foundation (C on Pico W)"
    Phase 1 (hardware + tooling) is complete. The octopus now has 16 emotional states with unique faces, body animations, and custom body shapes — all rendered mathematically at runtime in ~100KB of firmware. 17 standalone programs are ready to flash, with 823 total quotes across all personalities. Next up: user input (serial commands and GPIO buttons) and the pet state machine.

    [Setup Guide :material-arrow-right:](docs/setup/first-time-setup.md){ .md-button }
    [DevTool :material-arrow-right:](docs/tools/devtool.md){ .md-button }
    [Emotion States :material-arrow-right:](docs/software/emotion-states.md){ .md-button }

---

## Latest Update

Check the [build journal](blog/index.md) for the most recent post.

---

## Quick Links

<div class="grid cards" markdown>

-   :material-book-open-variant: **Docs**

    ---

    Hardware specs, wiring diagrams, setup guides, and code reference.

    [:octicons-arrow-right-24: Browse Docs](docs/index.md)

-   :material-post: **Blog**

    ---

    Chronological build journal. Every phase, every milestone.

    [:octicons-arrow-right-24: Read the Blog](blog/index.md)

-   :fontawesome-brands-discord: **Discord**

    ---

    Join the community server to ask questions and share your own build.

    [:octicons-arrow-right-24: Join Discord](community/discord.md)

-   :material-tools: **Dev Tools**

    ---

    DevTool GUI, setup CLI, and website dev CLI — built to support the workflow.

    [:octicons-arrow-right-24: Browse Tools](docs/tools/devtool.md)

-   :fontawesome-brands-patreon: **Patreon**

    ---

    Support the project and get early access to content and files.

    [:octicons-arrow-right-24: Support on Patreon](community/support.md)

</div>

---

## How This Project Works

The entire development process is public:

- **Every prompt** submitted to the AI assistant is logged in the [Prompt Log](prompts/index.md)
- **Every hardware decision** is documented in the [Docs](docs/index.md)
- **Every build step** is written up in the [Blog](blog/index.md)
- **All dev tools** are documented in the [Tools section](docs/tools/devtool.md)
- **All source files** are on [GitHub](https://github.com/rompasaurus/dilder)

This is learn-in-public taken to its logical extreme.
