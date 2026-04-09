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
- **Commit:** pending — included in this session's commit
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
- **Commit:** pending — included in this session's commit
- **Files Created/Modified:**
  - `website/dev.py` (created — CLI with subcommands: check, install, serve, build, deploy, clean, status; ANSI colour output with spinner; argparse; no external dependencies)

---

## Prompt #11
- **Date/Time:** 2026-04-09
- **Prompt:** "Give me a nice selection menu interface instead of a list of commands."
- **Input Tokens (est):** ~15
- **Output Tokens (est):** ~3,800
- **Commit:** pending — included in this session's commit
- **Files Created/Modified:**
  - `website/dev.py` (modified — replaced no-args fallback with interactive arrow-key menu: ↑↓ navigation, live description footer, env status badges, returns to menu after each command)

---

## Prompt #12
- **Date/Time:** 2026-04-09
- **Prompt:** "There seems to be a build failure when I build via the CLI script."
- **Input Tokens (est):** ~180 (included full error output)
- **Output Tokens (est):** ~500
- **Commit:** pending — included in this session's commit
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
- **Commit:** pending — this is the commit
- **Files Created/Modified:**
  - `PromptProgression.md` (modified — full grammar/spelling pass, added commit hash field to all entries, added Prompts #11–13)
