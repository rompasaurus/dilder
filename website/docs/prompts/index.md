# Prompt Log

Every prompt submitted to the AI assistant during Dilder's development, logged with date, token estimates, and files affected.

This is part of the transparency experiment — showing AI-assisted development openly rather than pretending the AI contributions didn't happen.

---

!!! info "Source file"
    This page mirrors [PromptProgression.md](https://github.com/rompasaurus/dilder/blob/main/PromptProgression.md) in the repo. The repo version is always authoritative — this page is updated periodically.

---

## Prompt #1 — 2026-04-08

**Prompt:** "Ok, let's create a new git repo for this project and put it up on my rompasaurus GitHub account. Also create a prompt progression file to notate every prompt that I type out for this project in an MD file with date and time stamp and the token count for each and the files created or modified, in an MD file called PromptProgression."

- **Input Tokens (est):** ~75
- **Output Tokens (est):** ~350
- **Files:** `PromptProgression.md` (created), `.git/` (initialized), GitHub repo `rompasaurus/dilder` (created)

---

## Prompt #2 — 2026-04-08

**Prompt:** "Ok let's set up a README and plan for this project. The idea is to create a learning platform and blog along with a YouTube series that goes through the development process of creating somewhat of a Tamagotchi clone using a Pi Zero, e-ink display, battery, and 3D-printed case. As part of this we are going to document the entire process in this idea creation, starting with the prompts and structure of the project and planning process. Flesh out a README that outlines this intent, marking each addition in phases so that it can be compiled in a proper step-by-step instruction."

- **Input Tokens (est):** ~110
- **Output Tokens (est):** ~2,500
- **Files:** `README.md` (created), `PromptProgression.md` (modified)

---

## Prompt #3 — 2026-04-09

**Prompt:** "Ok let's continue the planning process. Bear in mind each prompt I submit needs to be recorded in PromptProgression.md. I suppose Phase 0 planning is somewhat complete — there is a section to define the pet and personality but I believe that should be planned at a later date. I think the focus first will be piecing together the hardware for a prototype testable unit with a display and input, and perhaps we'll put a placeholder animal animation of sorts to get a scaffold in place code-wise and a process in place for deploying code and testing it. As for the hardware — what we are going to be working with is a Pi Zero and this e-ink display. Let's begin to research the materials list to include this and whatever else hardware-wise will be needed to get a test bench setup for developing on this hardware. Also given this hardware, come up with prototype sketches that could potentially be a 3D-printed casing for these materials and allow for 4–5 buttons of input actions to be recorded on the hardware, and suggest further and research the types of cheap off-the-shelf components that can be used to establish input actions."

- **Input Tokens (est):** ~220
- **Output Tokens (est):** ~4,500
- **Files:** `PromptProgression.md` (modified), `docs/hardware-research.md` (created), `README.md` (modified)

---

## Prompt #4 — 2026-04-09

**Prompt:** "I also need the output processing token estimate from the prompts as well in the prompt progression."

- **Input Tokens (est):** ~20
- **Output Tokens (est):** ~250
- **Files:** `PromptProgression.md` (modified — added output token estimates to all entries)

---

## Prompt #5 — 2026-04-09

**Prompt:** "Ok those concept ASCII images are neat but I want something more like a long rectangular case with the buttons on the right of the display, somewhat like the second-to-last generation of iPod Nanos, with four buttons — up, down, left, right — and a center button. Try to mock this up and see if you can generate an actual example prototype full-resolution concept of this, bearing in mind the hardware we are using."

- **Input Tokens (est):** ~90
- **Output Tokens (est):** ~3,800
- **Files:** `docs/concepts/prototype-v1.svg` (created), `docs/hardware-research.md` (modified), `PromptProgression.md` (modified)

---

## Prompt #6 — 2026-04-09

**Prompt:** "Ok that's a good start. Let's create another revision of the prototype and make a v2. This time let's make the dimensions make sense — the display is going to take up the largest area of the device with the buttons being a quarter or less of the device's face real estate. Let's also take into account the Waveshare's actual dimensions and account for these ratios."

- **Input Tokens (est):** ~75
- **Output Tokens (est):** ~6,500
- **Files:** `docs/concepts/prototype-v2.svg` (created), `docs/hardware-research.md` (modified), `PromptProgression.md` (modified)

---

## Prompt #7 — 2026-04-09

**Prompt:** "Ok for the hardware research we will need a breadboard to wire everything together — add that in there. Then we can begin the hardware setup and configure, assuming we bought all the materials listed and assume we bought a Waveshare e-ink display 2.13 the V3 of that display. Compose an in-depth, well-researched setup guide to begin displaying text on the display and compile and run embedded code on the Raspberry Pi. Make the guide as simple and exhaustive as possible. Include a table of contents and walk me through the documentation for the hardware and how to set up the development and debugging environment. Pull in and research every bit of documentation I will need to be successful in this project."

- **Input Tokens (est):** ~130
- **Output Tokens (est):** ~12,000
- **Files:** `docs/setup-guide.md` (created), `docs/hardware-research.md` (modified), `README.md` (modified), `PromptProgression.md` (modified)

---

## Prompt #8 — 2026-04-09

**Prompt:** "Ok I want to set up a documentation webpage/portfolio to provide an in-depth guide on how this project is progressing in real time, along with a page for documentation and research, contact information, and an introduction. Let's create a new folder to begin planning this. I would also like to use pwnagotchi.ai as somewhat of an inspiration for how to set this up and organize the website. It doesn't need to be anything ridiculous — in fact, static pages may be the ideal format — along with a Discord group and Patreon page. Let's roll out this folder and christen it with a new MD file."

- **Input Tokens (est):** ~120
- **Output Tokens (est):** ~3,500
- **Files:** `website/PLAN.md` (created), `PromptProgression.md` (modified)

---

## Prompt #9 — 2026-04-09

**Prompt:** "Ok let's kick off the website implementation. Look through the plan and start fleshing this out. Make sure while implementing the site to notate every step taken in a website implementation process MD, which will have a nice structured TOC and detailed step-by-step notes on the process of creating this static site — to act as instruction and documentation. I also need a detailed guide on how to add content and update content and the structure of the site, and further steps to deploy on Digital Ocean for as cheap as possible, and the best way to secure a domain for a website. Come up with domain ideas as well. Add steps to create a Patreon and Discord account. Don't forget to update PromptProgression with any prompt I input — don't be afraid to clean spelling and grammar before putting it in there too."

- **Input Tokens (est):** ~180
- **Output Tokens (est):** ~35,000 (est)
- **Files:** `website/mkdocs.yml`, `website/docs/index.md`, `website/docs/about/`, `website/docs/blog/`, `website/docs/docs/`, `website/docs/community/`, `website/docs/prompts/`, `website/docs/stylesheets/`, `website/IMPLEMENTATION.md`, `website/CONTENT-GUIDE.md`, `PromptProgression.md` (all created/modified)
