# Prompt Progression

A record of every prompt submitted during the development of Dilder.

Spelling and grammar are lightly cleaned for readability while preserving the original intent and voice.

---

## Prompt #1
- **Date/Time:** 2026-04-08
- **Prompt:** "Let's create a new git repo for this project and put it up on my rompasaurus GitHub account. Also create a prompt progression file to notate every prompt that I type out for this project in an MD file with date and time stamp and the token count for each, and the files created or modified, in a file called PromptProgression."
- **Input Tokens (est):** ~75
- **Output Tokens (est):** ~350
- **Commit:** `369880d` — Initial commit: add PromptProgression.md for tracking project prompts
- **Files Created/Modified:**
  - `PromptProgression.md` (created)
  - `.git/` (initialized)
  - GitHub repo `rompasaurus/dilder` (created)

---

## Prompt #2
- **Date/Time:** 2026-04-08
- **Prompt:** "Let's set up a README and plan for this project. The idea is to create a learning platform and blog along with a YouTube series that goes through the development process of creating a Tamagotchi clone using a Pi Zero, e-ink display, battery, and 3D-printed case. As part of this we are going to document the entire process, starting with the prompts and structure of the project and planning process. Flesh out a README that outlines this intent, marking each addition in phases so that it can be compiled into a proper step-by-step instruction."
- **Input Tokens (est):** ~110
- **Output Tokens (est):** ~2,500
- **Commit:** `cc9ea8f` — Add README with phased project roadmap and update prompt log
- **Files Created/Modified:**
  - `README.md` (created)
  - `PromptProgression.md` (modified)

---

## Prompt #3
- **Date/Time:** 2026-04-09
- **Prompt:** "Let's continue the planning process. Bear in mind each prompt I submit needs to be recorded in PromptProgression.md. I suppose Phase 0 planning is somewhat complete — there is a section to define the pet and personality but I believe that should be planned at a later date. I think the focus first will be piecing together the hardware for a prototype testable unit with a display and input, and perhaps we'll put a placeholder animal animation of sorts to get a scaffold in place code-wise and a process in place for deploying code and testing it. As for the hardware, what we are going to be working with is a Pi Zero and this e-ink display. Let's begin to research the materials list to include this and whatever else hardware-wise will be needed to get a test bench setup for developing on this hardware. Also, given this hardware, come up with prototype sketches that could potentially be a 3D-printed casing for these materials and allow for 4–5 buttons of input actions to be recorded on the hardware, and suggest and research the types of cheap off-the-shelf components that can be used to establish input actions."
- **Input Tokens (est):** ~220
- **Output Tokens (est):** ~4,500
- **Commit:** `733c582` — Add hardware research with materials list, component specs, and input options
- **Files Created/Modified:**
  - `PromptProgression.md` (modified)
  - `docs/hardware-research.md` (created)
  - `README.md` (modified)

---

## Prompt #4
- **Date/Time:** 2026-04-09
- **Prompt:** "I also need the output processing token estimate from the prompts as well in the prompt progression."
- **Input Tokens (est):** ~20
- **Output Tokens (est):** ~250
- **Commit:** `8b8b2e4` — Update README and prompt log for Phase 1 hardware planning
- **Files Created/Modified:**
  - `PromptProgression.md` (modified — added output token estimates to all entries)

---

## Prompt #5
- **Date/Time:** 2026-04-09
- **Prompt:** "Those concept ASCII images are neat, but I want something more like a long rectangular case with the buttons on the right of the display — somewhat like the second-to-last generation of iPod Nanos — with four buttons: up, down, left, right, and a center button. Try to mock this up and see if you can generate an actual example, full-resolution prototype concept of this, bearing in mind the hardware we are using."
- **Input Tokens (est):** ~90
- **Output Tokens (est):** ~3,800
- **Commit:** `e1b6891` — Add prototype enclosure concept renders (v1 and v2 SVGs)
- **Files Created/Modified:**
  - `docs/concepts/prototype-v1.svg` (created — full-resolution prototype concept render)
  - `docs/hardware-research.md` (modified — replaced ASCII concepts with SVG reference and updated form factor)
  - `PromptProgression.md` (modified)

---

## Prompt #6
- **Date/Time:** 2026-04-09
- **Prompt:** "That's a good start. Let's create another revision of the prototype and make a v2. This time let's make the dimensions make sense — the display is going to take up the largest area of the device with the buttons being a quarter or less of the device's face real estate. Let's also take into account the Waveshare's actual dimensions and account for these ratios."
- **Input Tokens (est):** ~75
- **Output Tokens (est):** ~6,500
- **Commit:** `e1b6891` — Add prototype enclosure concept renders (v1 and v2 SVGs)
- **Files Created/Modified:**
  - `docs/concepts/prototype-v2.svg` (created — dimension-accurate prototype concept at 4:1 scale)
  - `docs/hardware-research.md` (modified — updated enclosure section with v2 specs and real component dimensions)
  - `PromptProgression.md` (modified)

---

## Prompt #7
- **Date/Time:** 2026-04-09
- **Prompt:** "For the hardware research we will need a breadboard to wire everything together — add that in there. Then we can begin the hardware setup and configuration, assuming we bought all the materials listed and a Waveshare e-ink display 2.13 V3. Compose an in-depth, well-researched setup guide to begin displaying text on the display and compile and run embedded code on the Raspberry Pi. Make the guide as simple and exhaustive as possible. Include a table of contents and walk me through the documentation for the hardware and how to set up the development and debugging environment. Pull in and research every bit of documentation I will need to be successful in this project."
- **Input Tokens (est):** ~130
- **Output Tokens (est):** ~12,000
- **Commit:** `30bb8b7` — Add comprehensive hardware and dev environment setup guide
- **Files Created/Modified:**
  - `docs/setup-guide.md` (created — comprehensive hardware and dev environment setup guide with 13 sections)
  - `docs/hardware-research.md` (modified — updated display to V3, added breadboard detail)
  - `README.md` (modified — added setup guide link to docs table and Phase 1 checklist)
  - `PromptProgression.md` (modified)

---

## Prompt #8
- **Date/Time:** 2026-04-09
- **Prompt:** "I want to set up a documentation webpage/portfolio to provide an in-depth guide on how this project is progressing in real time, along with a page for documentation and research, contact information, and an introduction. Let's create a new folder to begin planning this. I would also like to use pwnagotchi.ai as something of an inspiration for how to set this up and organise the website. It doesn't need to be anything ridiculous — in fact, static pages may be the ideal format — along with a Discord group and Patreon page. Let's roll out this folder and christen it with a new MD file."
- **Input Tokens (est):** ~120
- **Output Tokens (est):** ~3,500
- **Commit:** `f44695c` — Add website planning folder with site structure and community plan
- **Files Created/Modified:**
  - `website/PLAN.md` (created — website plan with site structure, page descriptions, Discord/Patreon plans, SSG comparison, pwnagotchi analysis)
  - `PromptProgression.md` (modified)

---

## Prompt #9
- **Date/Time:** 2026-04-09
- **Prompt:** "Let's kick off the website implementation. Look through the plan and start fleshing this out. Make sure while implementing the site to notate every step taken in a website implementation process MD, which will have a nicely structured TOC and detailed step-by-step notes on the process of creating this static site — to act as instruction and documentation. I also need a detailed guide on how to add and update content and the structure of the site, and further steps to deploy on Digital Ocean for as cheap as possible, and the best way to secure a domain for a website. Come up with domain ideas as well. Add steps to create a Patreon and Discord account. Don't forget to update PromptProgression with any prompt I input — don't be afraid to clean spelling and grammar before putting it in there too."
- **Input Tokens (est):** ~180
- **Output Tokens (est):** ~35,000
- **Commit:** `0360ba9` — Build out full MkDocs website scaffold and dev tooling (Prompts 9–13)
- **Files Created/Modified:**
  - `website/mkdocs.yml` (created — full MkDocs Material config with blog plugin, nav, social links, extensions)
  - `website/docs/index.md` (created — landing page)
  - `website/docs/about/index.md` (created — about page)
  - `website/docs/about/contact.md` (created — contact page)
  - `website/docs/blog/index.md` (created — blog landing)
  - `website/docs/blog/posts/phase-0-planning.md` (created — Phase 0 blog post)
  - `website/docs/blog/posts/phase-1-hardware.md` (created — Phase 1 blog post)
  - `website/docs/docs/index.md` (created — docs overview)
  - `website/docs/docs/hardware/materials-list.md` (created — migrated from hardware-research.md)
  - `website/docs/docs/hardware/wiring-pinout.md` (created — GPIO assignments and breadboard layout)
  - `website/docs/docs/hardware/enclosure-design.md` (created — case dimensions and design constraints)
  - `website/docs/docs/setup/pi-zero-setup.md` (created — OS flash, SSH, SPI setup)
  - `website/docs/docs/setup/display-setup.md` (created — HAT attachment, Waveshare library, hello world)
  - `website/docs/docs/setup/dev-environment.md` (created — rsync workflow, VS Code Remote-SSH, systemd)
  - `website/docs/docs/software/project-structure.md` (created — planned firmware architecture)
  - `website/docs/community/index.md` (created — community overview)
  - `website/docs/community/discord.md` (created — Discord server structure)
  - `website/docs/community/support.md` (created — Patreon tiers)
  - `website/docs/prompts/index.md` (created — prompt log mirroring PromptProgression.md)
  - `website/docs/stylesheets/extra.css` (created — custom CSS overrides)
  - `website/IMPLEMENTATION.md` (created — 14-section build process doc covering MkDocs setup, GitHub Pages, Digital Ocean deployment, domain registration guide, domain ideas, Discord setup, Patreon setup)
  - `website/CONTENT-GUIDE.md` (created — 11-section content management guide covering blog posts, docs pages, nav, Markdown features, images, and publishing)
  - `PromptProgression.md` (modified)

---

## Prompt #10
- **Date/Time:** 2026-04-09
- **Prompt:** "Give me a Python setup CLI script I can run to deploy this locally, with nice logging and status output when it is running, and various helper options for this project."
- **Input Tokens (est):** ~40
- **Output Tokens (est):** ~4,500
- **Commit:** `0360ba9` — Build out full MkDocs website scaffold and dev tooling (Prompts 9–13)
- **Files Created/Modified:**
  - `website/dev.py` (created — CLI with subcommands: check, install, serve, build, deploy, clean, status; ANSI colour output with spinner; argparse; no external dependencies)

---

## Prompt #11
- **Date/Time:** 2026-04-09
- **Prompt:** "Give me a nice selection menu interface instead of a list of commands."
- **Input Tokens (est):** ~15
- **Output Tokens (est):** ~3,800
- **Commit:** `0360ba9` — Build out full MkDocs website scaffold and dev tooling (Prompts 9–13)
- **Files Created/Modified:**
  - `website/dev.py` (modified — replaced no-args fallback with interactive arrow-key menu: ↑↓ navigation, live description footer, env status badges, returns to menu after each command)

---

## Prompt #12
- **Date/Time:** 2026-04-09
- **Prompt:** "There seems to be a build failure when I build via the CLI script."
- **Input Tokens (est):** ~180 (included full error output)
- **Output Tokens (est):** ~500
- **Commit:** `0360ba9` — Build out full MkDocs website scaffold and dev tooling (Prompts 9–13)
- **Files Created/Modified:**
  - `website/docs/blog/.authors.yml` (created — required by MkDocs blog plugin for named authors)
  - `website/docs/blog/index.md` (modified — removed dead RSS link that wasn't a source file)
  - `website/docs/docs/hardware/enclosure-design.md` (modified — changed SVG links from broken relative paths to GitHub URLs)

---

## Prompt #13
- **Date/Time:** 2026-04-09
- **Prompt:** "Let's update the prompts with the last ones I sent through — divide and describe them. Commit the changes, and also apply the git commit as another field in the prompt progression where the prompt's changes were applied. Don't be afraid to clean up the spelling and grammar a bit. Report this prompt as well."
- **Input Tokens (est):** ~65
- **Output Tokens (est):** ~2,500
- **Commit:** `78ea1a0` — Backfill commit hash in PromptProgression.md (Prompt 13)
- **Files Created/Modified:**
  - `PromptProgression.md` (modified — full grammar/spelling pass, added commit hash field to all entries, added Prompts #11–13)

---

## Prompt #14
- **Date/Time:** 2026-04-09
- **Prompt:** "Walk me through how I could deploy this on GitHub Pages and the pricing structure — hopefully free — and if a domain can be linked to a GitHub Pages account."
- **Input Tokens (est):** ~35
- **Output Tokens (est):** ~900
- **Commit:** `633b084` — Add GitHub Actions workflow for automatic Pages deployment
- **Files Created/Modified:**
  - `.github/workflows/deploy-site.yml` (created — workflow that triggers on pushes to `website/` on main, installs MkDocs Material, and runs `mkdocs gh-deploy`)

---

## Prompt #15
- **Date/Time:** 2026-04-09
- **Prompt:** "Can you embed the concept images instead of linking to the GitHub page on the website?"
- **Input Tokens (est):** ~30
- **Output Tokens (est):** ~300
- **Commit:** `e358a1f` — Embed prototype SVG renders directly in enclosure design page
- **Files Created/Modified:**
  - `website/docs/assets/images/prototype-v1.svg` (created — copied from docs/concepts/)
  - `website/docs/assets/images/prototype-v2.svg` (created — copied from docs/concepts/)
  - `website/docs/docs/hardware/enclosure-design.md` (modified — replaced GitHub links with inline `![img]()` embeds)

---

## Prompt #16
- **Date/Time:** 2026-04-09
- **Prompt:** "Should the site folder be in the gitignore or will that need to be included to render on the GitHub Pages?"
- **Input Tokens (est):** ~25
- **Output Tokens (est):** ~150
- **Commit:** n/a — explanation only, no files changed
- **Files Created/Modified:** none

---

## Prompt #17
- **Date/Time:** 2026-04-09
- **Prompt:** "Add the last prompts with code changes to the prompt history with a commit ref."
- **Input Tokens (est):** ~20
- **Output Tokens (est):** ~400
- **Commit:** `1c270fd` — Update PromptProgression with Prompts 14–17 and fix #13 commit ref
- **Files Created/Modified:**
  - `PromptProgression.md` (modified — fixed Prompt #13 commit hash, added Prompts #14–17)

---

## Prompt #18
- **Date/Time:** 2026-04-09
- **Prompt:** "I need a website deployment process guide for GitHub Pages. I have a registered domain on Squarespace and I would like to deploy this site on GitHub and link my domain to this page."
- **Input Tokens (est):** ~45
- **Output Tokens (est):** ~2,800
- **Commit:** `38baa75` — Add deployment guide and CNAME file for Squarespace domain setup
- **Files Created/Modified:**
  - `website/DEPLOY.md` (created — 13-section deployment guide: GitHub Pages setup, first deployment, CNAME file, Squarespace DNS configuration with step-by-step record setup, HTTPS, mkdocs.yml update, end-to-end verification checklist, troubleshooting)
  - `website/docs/CNAME` (created — placeholder CNAME file, update with real domain before deploying)

---

## Prompt #19
- **Date/Time:** 2026-04-09
- **Prompt:** "Add my Patreon page to the site."
- **Input Tokens (est):** ~15
- **Output Tokens (est):** ~100
- **Commit:** `3b36905` — Add real Patreon URL (MchenrysDevelopment) across site
- **Files Created/Modified:**
  - `website/mkdocs.yml` (modified — Patreon social link updated)
  - `website/docs/community/support.md` (modified — Patreon URL updated)
  - `website/docs/about/contact.md` (modified — Patreon URL updated)

---

## Prompt #20
- **Date/Time:** 2026-04-09
- **Prompt:** "There's a 404 error — it's not loading despite the domain pointing correctly and the GitHub hook deploying."
- **Input Tokens (est):** ~40
- **Output Tokens (est):** ~300
- **Commit:** `0af7962` — Clarify Pages source setting in workflow comment
- **Files Created/Modified:**
  - `.github/workflows/deploy-site.yml` (modified — added comment clarifying Pages must be set to "Deploy from a branch → gh-pages" not "GitHub Actions")

---

## Prompt #21
- **Date/Time:** 2026-04-09
- **Prompt:** "Make that branch for me so that it triggers the deploy."
- **Input Tokens (est):** ~20
- **Output Tokens (est):** ~150
- **Commit:** `1c7f210` — Trigger GitHub Pages deployment via website/ path change
- **Files Created/Modified:**
  - `website/requirements.txt` (modified — added comment to satisfy workflow paths filter and trigger first deployment)

---

## Prompt #22
- **Date/Time:** 2026-04-09
- **Prompt:** *(Shared GitHub Actions build log showing successful deploy to gh-pages branch with CNAME resolution to dilder.dev)*
- **Input Tokens (est):** ~200 (build log)
- **Output Tokens (est):** ~200
- **Commit:** `18c8876` — Lowercase CNAME domain
- **Files Created/Modified:**
  - `website/docs/CNAME` (modified — changed `Dilder.dev` to `dilder.dev` for consistency)

---

## Prompt #23
- **Date/Time:** 2026-04-09
- **Prompt:** "Now we need to pull in the documentation for the Pi Zero WH and the e-ink display. Reach out to the official documentation and put it in its own folder in the docs folder. We need to then extract the pinout and pertinent documentation and attach it to the Wiring & Pinout doc."
- **Input Tokens (est):** ~55
- **Output Tokens (est):** ~8,500
- **Commit:** `61525d6` — Add official hardware reference docs and expand wiring pinout
- **Files Created/Modified:**
  - `website/docs/docs/reference/pi-zero-wh.md` (created — full 40-pin GPIO table, electrical limits, SPI/I²C/UART/PWM protocol assignments, BCM vs physical numbering guide, official links)
  - `website/docs/docs/reference/waveshare-eink.md` (created — display specs, HAT pin mapping with signal behaviour table, SPI protocol details, refresh rules, V3 vs V4 comparison, Python setup examples, safety notes, official links)
  - `website/docs/docs/hardware/wiring-pinout.md` (modified — expanded with full 40-pin header map, signal behaviour table, wiring diagram, SPI config table, links to new reference docs, troubleshooting section)
  - `website/mkdocs.yml` (modified — Reference section added to nav)

---

## Prompt #24
- **Date/Time:** 2026-04-09
- **Prompt:** "Update the prompts file with this and the commit."
- **Input Tokens (est):** ~15
- **Output Tokens (est):** ~400
- **Commit:** `09519b5` — Update PromptProgression with Prompts 20–24
- **Files Created/Modified:**
  - `PromptProgression.md` (modified — added Prompts #20–24)

---

## Prompt #25
- **Date/Time:** 2026-04-10
- **Prompt:** "Let's update this plan and the hardware we are going to use. For now I have a set of Waveshare 2.13 V3 displays and Pico W boards on hand that I would like to use to start this project with instead of the Pi Zero. We'll put the Pi Zero in a later dev phase and start with what we have. Update the documentation to account for this hardware change and pull in the correct documentation for this hardware and setup in the project and on the site. Update everything and replace the Zero with the Pico, and then we need to create a setup document to wire up the Waveshare to the Pico W and begin debugging from VSCode on Linux."
- **Input Tokens (est):** ~130
- **Output Tokens (est):** ~45,000
- **Commit:** `604039f` — Migrate from Pi Zero to Pico W as Phase 1 development platform
- **Files Created/Modified:**
  - `README.md` (modified — Pico W as primary board, Pi Zero deferred to Phase 5, new phase roadmap)
  - `docs/hardware-research.md` (modified — Pico W specs, SPI1 pin mapping, updated materials list and GPIO budget)
  - `website/docs/docs/reference/pico-w.md` (created — full Pico W reference: RP2040 specs, pinout, electrical limits, MicroPython firmware, Pico W vs Pi Zero comparison)
  - `website/docs/docs/reference/waveshare-eink.md` (modified — added Pico W jumper wire mapping, MicroPython driver setup, kept Pi Zero mapping for future)
  - `website/docs/docs/reference/pi-zero-wh.md` (modified — added "future hardware" banner)
  - `website/docs/docs/hardware/materials-list.md` (modified — Pico W components, updated costs and specs)
  - `website/docs/docs/hardware/wiring-pinout.md` (modified — complete rewrite for Pico W GPIO, jumper wire diagrams, MicroPython button code, visual pin map)
  - `website/docs/docs/hardware/enclosure-design.md` (modified — Pico W dimensions, enclosure deferred note)
  - `website/docs/docs/setup/pi-zero-setup.md` (modified — rewritten as Pico W setup: MicroPython flash, BOOTSEL, serial REPL, Wi-Fi test)
  - `website/docs/docs/setup/display-setup.md` (modified — rewritten for Pico W jumper wire connection, Waveshare MicroPython driver, framebuf hello world)
  - `website/docs/docs/setup/dev-environment.md` (modified — rewritten for VSCode + MicroPico on Linux: serial permissions, project config, file upload, mpremote CLI, debugging)
  - `website/docs/docs/software/project-structure.md` (modified — updated for MicroPython: framebuf, machine.Pin, flash storage notes)
  - `website/docs/docs/index.md` (modified — updated section names and descriptions for Pico W)
  - `website/docs/index.md` (modified — landing page updated for Pico W)
  - `website/mkdocs.yml` (modified — site description, nav labels, added Pico W reference page)
  - `website/docs/blog/posts/phase-1-hardware.md` (modified — rewritten for Pico W test bench)
  - `website/docs/blog/posts/phase-0-planning.md` (modified — hardware decision section updated for Pico W first approach)

---

## Prompt #26
- **Date/Time:** 2026-04-10
- **Prompt:** "Update the prompts file and fix grammar a bit. Divide, describe, and commit."
- **Input Tokens (est):** ~20
- **Output Tokens (est):** ~1,500
- **Commit:** `604039f` — Migrate from Pi Zero to Pico W as Phase 1 development platform
- **Files Created/Modified:**
  - `PromptProgression.md` (modified — added Prompts #25–26)
