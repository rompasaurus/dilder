# RegardedPal Website Plan

A static documentation site and project portfolio for the RegardedPal build series -- inspired by [pwnagotchi.ai](https://pwnagotchi.ai/) but tailored for a build-along audience with blog updates, video embeds, and community links.

---

## Site Goals

1. **Real-time build journal** -- visitors follow the project as it unfolds, phase by phase
2. **Reference documentation** -- hardware specs, setup guides, wiring diagrams, code reference
3. **Community hub** -- Discord invite, Patreon support, contact info
4. **Portfolio / intro page** -- who is building this and why

---

## Inspiration: pwnagotchi.ai

The pwnagotchi site is built with **Hugo** using the **Hugo Learn** documentation theme. It is a flat, docs-only site with no blog or landing page. What we are borrowing and what we are doing differently:

| pwnagotchi pattern | RegardedPal approach |
|-------------------|---------------------|
| Hugo Learn theme (sidebar nav, sequential reading) | Similar sidebar nav, but with a proper landing page |
| FontAwesome icons per nav section | Keep this -- makes the sidebar scannable |
| Discord badge in sidebar | Yes -- Discord invite link prominent in nav/header |
| No blog / no updates section | **Add a blog section** for build updates and video posts |
| No landing page (jumps straight to docs) | **Add a landing page** with hero, project summary, latest update |
| Client-side search (Lunr.js) | Keep this -- static site search with no server |
| Community hacks / Hall of Fame | Future: community gallery for user builds |
| Purely text docs, no embedded media | **Embed YouTube videos** in build series posts |

---

## Static Site Generator: MkDocs + Material

**Why MkDocs Material over Hugo/Astro/Jekyll:**

- Fastest path to professional-looking docs with zero frontend work
- Best-in-class Markdown extensions (admonitions, tabs, code annotations, tables)
- Built-in blog plugin (handles our build series posts)
- Built-in search (no external service needed)
- Single-command deploy to GitHub Pages (`mkdocs gh-deploy`)
- Python is already in our stack (Pi Zero development)
- All content is plain Markdown -- easy to migrate later if we outgrow it

**Install:** `pip install mkdocs-material`

**Relevant Material features:**
- Admonitions (tip/warning/note boxes) -- perfect for hardware gotchas
- Tabbed content -- show Python/C code side by side
- Code blocks with line highlighting and annotations
- Mermaid diagrams -- for flowcharts, wiring logic
- Blog plugin with tags, categories, RSS feed
- Social cards (auto-generated OG images)
- Light/dark mode toggle
- Mobile responsive

---

## Site Structure

```
regardedpal.dev (or GitHub Pages)
|
+-- / ............................ Landing page (hero, project intro, latest update)
|
+-- /about/ ...................... Who is building this, project vision, contact
|   +-- /about/contact/ ......... Email, GitHub, social links
|
+-- /blog/ ....................... Build series journal (chronological posts)
|   +-- /blog/phase-0-planning/
|   +-- /blog/phase-1-hardware/
|   +-- /blog/first-display-test/
|   +-- ...
|
+-- /docs/ ....................... Reference documentation
|   +-- /docs/hardware/
|   |   +-- materials-list/
|   |   +-- wiring-pinout/
|   |   +-- enclosure-design/
|   +-- /docs/setup/
|   |   +-- pi-zero-setup/
|   |   +-- display-setup/
|   |   +-- button-wiring/
|   |   +-- dev-environment/
|   +-- /docs/software/
|   |   +-- project-structure/
|   |   +-- display-driver/
|   |   +-- game-loop/
|   +-- /docs/3d-printing/
|       +-- case-design/
|       +-- print-settings/
|
+-- /community/ ................. Discord, Patreon, gallery
|   +-- /community/discord/ ..... Discord invite + server info
|   +-- /community/support/ ..... Patreon tiers and link
|   +-- /community/gallery/ ..... User builds showcase (future)
|
+-- /prompts/ ................... AI prompt log (transparency experiment)
```

---

## Page Descriptions

### Landing Page (`/`)
- Hero section with project tagline and a render/photo of the device
- "What is RegardedPal?" -- 2-3 sentence summary
- Current phase status badge (e.g., "Phase 1: Hardware Setup")
- Latest blog post preview
- Quick links: Docs, Blog, Discord, GitHub

### About (`/about/`)
- Who is building this (rompasaurus) and why
- Project philosophy: open development, AI-assisted, learn-in-public
- Tech stack summary
- Links to YouTube channel, blog, GitHub

### Contact (`/about/contact/`)
- GitHub: rompasaurus
- Discord: server invite
- Email or contact form
- YouTube channel link

### Blog (`/blog/`)
- Reverse-chronological post list
- Each post maps to a milestone or phase step
- Embedded YouTube videos where applicable
- Tags: `hardware`, `software`, `3d-printing`, `planning`, `community`
- RSS feed for subscribers

### Documentation (`/docs/`)
- Reference material organized by topic, not chronology
- Hardware: materials list, wiring, pinout diagrams, enclosure specs
- Setup: Pi Zero config, display, buttons, dev environment
- Software: code reference, architecture, API
- Each page is self-contained and linkable

### Community (`/community/`)
- Discord invite with server description and rules summary
- Patreon with tier descriptions
- Future: gallery of community-built RegardedPals

### Prompt Log (`/prompts/`)
- Rendered version of PromptProgression.md
- Shows every prompt, token counts, and files modified
- Part of the "transparency experiment" -- showing AI-assisted development openly

---

## Discord Server Plan

**Server name:** RegardedPal

**Channels:**

| Category | Channel | Purpose |
|----------|---------|---------|
| Welcome | #welcome | Rules, intro, role assignment |
| Welcome | #introductions | New members say hello |
| General | #general | Main chat |
| General | #off-topic | Non-project chat |
| Build Series | #hardware | Hardware questions, wiring help |
| Build Series | #software | Code questions, debugging |
| Build Series | #3d-printing | Case design, print settings |
| Build Series | #show-your-build | Photos/videos of your RegardedPal |
| Development | #dev-log | Automated updates from GitHub pushes |
| Development | #suggestions | Feature requests and ideas |
| Development | #bugs | Bug reports |
| Support | #patreon-chat | Patreon supporters only |

---

## Patreon Plan

**Page name:** RegardedPal (or rompasaurus)

**Tiers (suggested):**

| Tier | Price | Perks |
|------|-------|-------|
| Pal | $3/mo | Early access to blog posts, Discord supporter role |
| Builder | $5/mo | Above + access to STL files before public release, behind-the-scenes content |
| Contributor | $10/mo | Above + name in credits, vote on pet personality/features |

---

## Deployment

- **Host:** GitHub Pages (free, tied to the repo)
- **Domain:** Custom domain TBD (e.g., `regardedpal.dev` or subdomain)
- **Build:** GitHub Actions workflow -- on push to `main`, build MkDocs and deploy to `gh-pages` branch
- **Source:** `website/` folder in the main repo, or a separate `docs` branch

---

## File Structure (in this repo)

```
website/
├── PLAN.md              <-- this file
├── mkdocs.yml           <-- MkDocs configuration (to be created)
├── docs/                <-- MkDocs content source
│   ├── index.md         <-- Landing page
│   ├── about/
│   ├── blog/
│   │   └── posts/
│   ├── docs/            <-- reference documentation
│   ├── community/
│   └── prompts/
└── overrides/           <-- theme customizations (optional)
```

---

## Next Steps

1. Set up Discord server and get invite link
2. Set up Patreon page with initial tiers
3. Initialize MkDocs project (`mkdocs new .`)
4. Configure `mkdocs.yml` with Material theme, blog plugin, nav structure
5. Create landing page and about page content
6. Migrate existing docs (hardware-research, setup-guide) into the site
7. Set up GitHub Actions for auto-deploy to GitHub Pages
8. Choose and register a domain (optional)
