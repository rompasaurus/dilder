# Website Implementation Process

Step-by-step notes on how the Dilder website was built and how to maintain it. This document is both a process log and a reference for anyone setting up MkDocs Material from scratch.

---

## Table of Contents

1. [Overview and Technology Choice](#1-overview-and-technology-choice)
2. [Prerequisites](#2-prerequisites)
3. [Repository Structure](#3-repository-structure)
4. [Install MkDocs Material](#4-install-mkdocs-material)
5. [Configure mkdocs.yml](#5-configure-mkdocsyml)
6. [Content Structure](#6-content-structure)
7. [Local Development](#7-local-development)
8. [Deployment — GitHub Pages (Free)](#8-deployment--github-pages-free)
9. [Deployment — Digital Ocean (Cheapest Path)](#9-deployment--digital-ocean-cheapest-path)
10. [Domain Registration](#10-domain-registration)
11. [Domain Ideas for Dilder](#11-domain-ideas-for-dilder)
12. [Discord Server Setup](#12-discord-server-setup)
13. [Patreon Page Setup](#13-patreon-page-setup)
14. [Ongoing Maintenance Checklist](#14-ongoing-maintenance-checklist)

---

## 1. Overview and Technology Choice

### What We're Building

A static documentation and blog site for the Dilder hardware project. Static means:
- No backend server required
- Pages are pre-built HTML/CSS/JS files
- Can be hosted for free or very cheaply
- Fast to load, simple to maintain

### Why MkDocs Material

Evaluated options: Hugo, Astro, Jekyll, MkDocs. Chose **MkDocs + Material theme** because:

- Zero frontend work required — Material handles all layout and styling
- Built-in blog plugin with tags, categories, and RSS feed
- Built-in search (client-side, no server)
- Python-based (already in our stack for the Pi firmware)
- All content is plain Markdown — easy to write, easy to migrate later
- `mkdocs gh-deploy` deploys to GitHub Pages in one command
- Best-in-class Markdown extensions: admonitions, code annotations, Mermaid diagrams, tabbed content

**Reference:** [squidfunk.github.io/mkdocs-material](https://squidfunk.github.io/mkdocs-material)

---

## 2. Prerequisites

### Software Required

| Tool | Install Command | Purpose |
|------|----------------|---------|
| Python 3.10+ | `brew install python` (macOS) | MkDocs runtime |
| pip | comes with Python | Package installer |
| git | `brew install git` | Version control |
| GitHub account | [github.com](https://github.com) | Code hosting + free Pages deployment |

### Verify Python

```bash
python3 --version
# Should be 3.10 or newer
```

---

## 3. Repository Structure

The website lives inside the main `dilder` repo in a `website/` subdirectory. This keeps the hardware docs, firmware, and website all in one repo.

```
dilder/
└── website/
    ├── PLAN.md              ← original website plan
    ├── IMPLEMENTATION.md    ← this file
    ├── CONTENT-GUIDE.md     ← how to add/update content
    ├── mkdocs.yml           ← MkDocs configuration
    └── docs/                ← all site content (Markdown files)
        ├── index.md         ← landing page
        ├── about/
        ├── blog/
        │   └── posts/       ← blog post files go here
        ├── docs/            ← reference documentation
        │   ├── hardware/
        │   ├── setup/
        │   └── software/
        ├── community/
        ├── prompts/
        └── stylesheets/
            └── extra.css    ← custom CSS overrides
```

**Key rule:** All content files live in `website/docs/`. The `website/mkdocs.yml` config tells MkDocs where to find them.

---

## 4. Install MkDocs Material

### Create a Python Virtual Environment

Always use a virtual environment so project dependencies don't conflict with your system Python.

```bash
cd ~/dilder/website

# Create venv
python3 -m venv venv

# Activate it
source venv/bin/activate       # macOS/Linux
# venv\Scripts\activate        # Windows

# Verify
which python   # should show path inside venv/
```

### Install MkDocs Material and Plugins

```bash
pip install mkdocs-material
```

This single command installs MkDocs, the Material theme, and all built-in plugins including the blog plugin.

### Verify Installation

```bash
mkdocs --version
# mkdocs, version 1.5.x from ...

python -c "import material; print(material.__version__)"
# 9.x.x
```

### Save Dependencies

```bash
pip freeze > requirements.txt
```

This file lets anyone else (or your CI system) install the exact same versions:

```bash
pip install -r requirements.txt
```

---

## 5. Configure mkdocs.yml

The `mkdocs.yml` file controls everything: theme, plugins, navigation, social links, Markdown extensions.

### Key Sections Explained

#### Site Metadata

```yaml
site_name: Dilder
site_url: https://dilder.dev
site_description: An open-source AI-assisted virtual pet...
site_author: rompasaurus
repo_url: https://github.com/rompasaurus/dilder
edit_uri: edit/main/website/docs/
```

`site_url` is important — it's used to generate the correct canonical URLs and sitemap. Set this to your actual domain once you have one.

`edit_uri` adds "Edit this page" links to every page pointing to the correct GitHub location.

#### Theme Configuration

```yaml
theme:
  name: material
  palette:
    - scheme: default      # light mode
      primary: deep purple
      accent: teal
    - scheme: slate        # dark mode
      primary: deep purple
      accent: teal
  features:
    - navigation.tabs       # top-level nav as tabs
    - navigation.sections   # collapsible nav sections
    - navigation.top        # "back to top" button
    - content.code.copy     # copy button on code blocks
```

`primary` and `accent` control the color scheme. See [Material color docs](https://squidfunk.github.io/mkdocs-material/setup/changing-the-colors/) for all options.

#### Blog Plugin

```yaml
plugins:
  - search
  - blog:
      blog_dir: blog
      post_url_format: "{slug}"    # /blog/my-post-title
      archive: true
      categories: true
      pagination_per_page: 10
```

The blog plugin reads posts from `docs/blog/posts/` and automatically generates the blog index, archive, and category pages.

#### Navigation

```yaml
nav:
  - Home: index.md
  - Blog:
      - blog/index.md
  - Docs:
      - Overview: docs/index.md
      - Hardware:
          - Materials List: docs/hardware/materials-list.md
          ...
```

The `nav` section defines the sidebar structure. Any `.md` file in `docs/` not listed here will still be built but won't appear in the nav.

---

## 6. Content Structure

### Pages vs Blog Posts

| Type | Location | Purpose |
|------|----------|---------|
| Pages | `docs/` (any subfolder) | Reference docs, evergreen content |
| Blog posts | `docs/blog/posts/` | Timestamped build journal entries |

### Blog Post Front Matter

Every blog post needs a `date` field at minimum:

```markdown
---
date: 2026-04-09
authors:
  - rompasaurus
categories:
  - Hardware
slug: my-post-slug
---

# Post Title

Preview text shown on the blog index page.

<!-- more -->

Full post content below the fold.
```

- `<!-- more -->` is the fold marker — text before it appears as the preview on the blog index
- `slug` controls the URL: `blog/my-post-slug`
- `categories` are auto-linked across posts

### Author Configuration

Create `docs/blog/.authors.yml`:

```yaml
authors:
  rompasaurus:
    name: rompasaurus
    description: Builder
    avatar: https://avatars.githubusercontent.com/rompasaurus
```

---

## 7. Local Development

### Start the Dev Server

```bash
cd ~/dilder/website
source venv/bin/activate
mkdocs serve
```

Output:

```
INFO     -  Building documentation...
INFO     -  Serving on http://127.0.0.1:8000/
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

The server hot-reloads on every file save — edit a Markdown file, refresh the browser, see the change instantly.

### Build Static Files

```bash
mkdocs build
```

This generates a `site/` directory containing all HTML, CSS, and JS. This is what gets deployed.

### Common Issues

| Problem | Fix |
|---------|-----|
| `KeyError: 'blog'` | Ensure `- blog:` is in plugins section |
| Post doesn't appear on blog index | Check `date:` field in frontmatter |
| Missing nav page warning | Add the file to `nav:` in mkdocs.yml |
| CSS not updating | Hard-refresh browser (Cmd+Shift+R) |

---

## 8. Deployment — GitHub Pages (Free)

GitHub Pages hosts static sites for free, tied directly to your GitHub repo. This is the recommended starting point.

### Step 1 — Enable GitHub Pages

1. Go to `github.com/rompasaurus/dilder`
2. Settings → Pages
3. Source: **GitHub Actions** (not "Deploy from a branch")

### Step 2 — Create the Workflow File

Create `.github/workflows/deploy-site.yml` in the repo root:

```yaml
name: Deploy Site

on:
  push:
    branches:
      - main
    paths:
      - 'website/**'

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r website/requirements.txt

      - name: Deploy
        run: |
          cd website
          mkdocs gh-deploy --force
```

### Step 3 — Push and Verify

```bash
git add .github/workflows/deploy-site.yml
git commit -m "Add GitHub Pages deployment workflow"
git push
```

GitHub Actions will build and deploy the site automatically. Check the Actions tab to monitor progress.

The site will be live at: `https://rompasaurus.github.io/dilder/`

### Step 4 — Custom Domain (Optional)

Once you have a domain, add it to GitHub Pages:

1. Settings → Pages → Custom domain → enter your domain
2. Add a `CNAME` file to `website/docs/` with just your domain:

```
dilder.dev
```

3. Update `site_url` in `mkdocs.yml` to match

Then update your DNS (see [Section 10](#10-domain-registration)).

---

## 9. Deployment — Digital Ocean (Cheapest Path)

If you want more control than GitHub Pages, Digital Ocean is the next cheapest option.

### Option A — DO App Platform (Static Sites = Free)

Digital Ocean's App Platform has a **free tier for static sites**. Zero monthly cost.

**Steps:**

1. Create a Digital Ocean account at [cloud.digitalocean.com](https://cloud.digitalocean.com)
2. Apps → Create App
3. Source: GitHub → select `rompasaurus/dilder` repo
4. Resource type: **Static Site**
5. Build command: `pip install -r website/requirements.txt && cd website && mkdocs build`
6. Output directory: `website/site`
7. Deploy

DO will auto-deploy on every push to `main`.

**Cost:** Free for static sites. No credit card required beyond initial account verification.

**Custom domain:** Settings → Domains → add your domain → copy the CNAME value → update DNS.

### Option B — DO Droplet ($4/month smallest)

If you need a server (for future dynamic features), the smallest Droplet costs $4/month.

1. Create a Droplet → Ubuntu 22.04 → Basic plan → $4/month (1 vCPU, 512MB RAM, 10GB SSD)
2. SSH in: `ssh root@YOUR_DROPLET_IP`
3. Install Nginx:
   ```bash
   apt update && apt install -y nginx
   ```
4. Deploy the site:
   ```bash
   mkdocs build
   rsync -avz site/ root@YOUR_IP:/var/www/html/
   ```
5. Configure Nginx:
   ```nginx
   server {
       listen 80;
       server_name dilder.dev www.dilder.dev;
       root /var/www/html;
       index index.html;
       location / {
           try_files $uri $uri/ =404;
       }
   }
   ```
6. Add SSL with Certbot (free, auto-renewing):
   ```bash
   apt install -y certbot python3-certbot-nginx
   certbot --nginx -d dilder.dev -d www.dilder.dev
   ```

**Recommendation:** Start with DO App Platform (free) or GitHub Pages. Only move to a Droplet if you need server-side functionality.

---

## 10. Domain Registration

### Best Registrars (Cost vs Quality)

| Registrar | Pros | Cons |
|-----------|------|------|
| **Cloudflare Registrar** | At-cost pricing (cheapest for most TLDs), free privacy protection, excellent DNS | Must transfer from another registrar first for initial registration |
| **Porkbun** | Very cheap, modern interface, free privacy, good first-year deals | Less established than Namecheap |
| **Namecheap** | Reliable, good UI, competitive prices | Privacy protection costs extra |
| **Google Domains (now Squarespace)** | Simple, good Google Workspace integration | Slightly more expensive |

**Recommendation:** Register at Porkbun or Namecheap first, then transfer to Cloudflare after a year for the cheapest long-term cost.

### .dev vs Other TLDs

| TLD | Annual Cost | Notes |
|-----|-------------|-------|
| `.dev` | ~$12–15/year | Requires HTTPS (enforced by browser), tech-credible |
| `.pet` | ~$20–30/year | Cute and relevant for a virtual pet project |
| `.xyz` | ~$1–2 first year, ~$12/year after | Cheap, modern, neutral |
| `.com` | ~$10–15/year | Most familiar, but `dilder.com` may be taken |
| `.io` | ~$30–50/year | Popular with devs but expensive |
| `.build` | ~$15–25/year | Relevant but less recognizable |

### How to Point Your Domain to GitHub Pages

After registering, update DNS at your registrar:

**For apex domain (`dilder.dev`):**

Add these A records pointing to GitHub's servers:

```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

**For www subdomain:**

Add a CNAME record:
```
www → rompasaurus.github.io
```

DNS propagation takes 10 minutes to 24 hours.

### How to Point Your Domain to Digital Ocean App Platform

In your registrar DNS settings, add a CNAME record:

```
@ (apex) → your-app.ondigitalocean.app
```

Or use DO's nameservers and manage DNS from there.

---

## 11. Domain Ideas for Dilder

Brainstormed options — check availability at [porkbun.com](https://porkbun.com) or [namecheap.com](https://namecheap.com).

### Top Picks

| Domain | Appeal |
|--------|--------|
| `dilder.dev` | Clean, tech-focused, exactly the project name. **Best option.** |
| `dilder.pet` | Perfect TLD for a virtual pet project — memorable and on-theme |
| `dilder.build` | "Build a Dilder" — fits the build journal framing |
| `dilder.xyz` | Cheap, modern, neutral — good if .dev is expensive |

### Personal Brand Options

| Domain | Appeal |
|--------|--------|
| `rompasaurus.dev` | Personal brand — useful if you plan more projects |
| `rompasaurus.xyz` | Cheap version of the above |

### Descriptive Options

| Domain | Appeal |
|--------|--------|
| `buildadilder.com` | Clear, describes what the site is for |
| `buildingdilder.com` | Build journal framing |
| `opendilder.dev` | Emphasizes open-source nature |

### Fun Options

| Domain | Appeal |
|--------|--------|
| `dilder.fun` | Playful, cheap |
| `dilder.lol` | Even more playful |
| `tamadilder.dev` | Nods to Tamagotchi origin |

**Recommendation:** Secure `dilder.dev` first. Check if `dilder.pet` is available — it's the most on-brand option for the project long-term.

---

## 12. Discord Server Setup

### Create the Server

1. Open Discord (desktop app or [discord.com](https://discord.com))
2. Click the **+** icon in the left sidebar → **Create My Own**
3. Select **For a club or community** → **For me and my friends** → **Create**
4. Name: `Dilder`
5. Add a server icon (use the prototype render or a placeholder)

### Configure Community Mode

Settings (gear icon) → **Community** → Enable → follow the setup steps. Community mode unlocks:
- Welcome screen
- Onboarding flow
- Announcement channels
- Server insights

### Create Channels

Follow the structure from PLAN.md:

**Welcome category:**
- `#welcome` — set as rules channel
- `#introductions`

**General category:**
- `#general`
- `#off-topic`

**Build Series category:**
- `#hardware`
- `#software`
- `#3d-printing`
- `#show-your-build`

**Development category:**
- `#dev-log` — set as announcement channel
- `#suggestions`
- `#bugs`

**Support category (Patreon tier):**
- `#patreon-chat` — restrict to a Patreon supporter role

### Set Up the Welcome Screen

Settings → **Community** → **Welcome Screen** → enable and configure with links to key channels.

### Create Roles

| Role | Color | Permission |
|------|-------|------------|
| Moderator | Purple | Manage messages, kick |
| Patreon Supporter | Gold | Access to #patreon-chat |
| Builder | Green | Show in member list |
| Member | Grey | Default for everyone |

### Get Your Invite Link

Click the server name → **Invite People** → create a permanent invite link. This is what goes in the website's community pages.

### Connect GitHub to Discord (Webhook)

For auto-posting GitHub commits to `#dev-log`:

1. Edit `#dev-log` channel → Integrations → Webhooks → New Webhook → Copy URL
2. In GitHub: repo → Settings → Webhooks → Add webhook
3. Payload URL: the Discord webhook URL + `/github`
4. Content type: `application/json`
5. Events: select **Pushes** and **Releases**

---

## 13. Patreon Page Setup

### Create the Page

1. Go to [patreon.com/create](https://www.patreon.com/create)
2. Sign up or log into your Patreon account
3. Choose **Creator** → select a category (Technology → DIY / Maker)
4. Page name: `Dilder` (or `rompasaurus` if you want a personal brand page)

### Fill In the Page

**About section:**
- Write a 2–3 paragraph description of the project
- Explain what supporters get
- Link to the website and GitHub

**Cover image:** Use the prototype-v2 concept render or a photo of the hardware once built.

**Profile image:** Your avatar or the Dilder logo.

### Create Tiers

Based on PLAN.md:

**Tier 1: Pal — $3/month**
- Description: "Early access to blog posts and Discord supporter role"
- Perks: Early post access, Discord @Patreon Supporter role, name in credits

**Tier 2: Builder — $5/month**
- Description: "Build alongside the project with early file access"
- Perks: Everything in Pal + STL files before public release, behind-the-scenes content

**Tier 3: Contributor — $10/month**
- Description: "Help shape what Dilder becomes"
- Perks: Everything in Builder + vote on features, name in credits with Contributor badge

### Payment Setup

Patreon requires:
- Bank account or PayPal for payouts
- Tax information (even for zero income, they require W-9/W-8 for US, or equivalent)

Payments are processed on the 1st of each month for the previous month's pledges.

Patreon's fee: 8% of income on the free plan (Lite), or 5% on Pro ($25/month fixed fee — worthwhile only after ~$500/month income).

### Connect Patreon to Discord

Patreon has an official Discord integration that automatically assigns roles when someone subscribes:

1. Patreon creator dashboard → **Apps** → **Discord**
2. Connect your Discord account
3. Map each Patreon tier to a Discord role
4. Members who subscribe automatically get the role

### Get Your Page URL

Once published (or even in draft), your URL is `patreon.com/YOUR_PAGE_NAME`. Update this in:
- `website/mkdocs.yml` (social links)
- `website/docs/community/support.md`
- `website/docs/community/discord.md`
- `website/docs/about/contact.md`

---

## 14. Ongoing Maintenance Checklist

### After Each Phase Milestone

- [ ] Write a blog post in `docs/blog/posts/`
- [ ] Update relevant docs pages to reflect current state
- [ ] Update the phase status on the landing page (`docs/index.md`)
- [ ] Push to GitHub (triggers auto-deploy)
- [ ] Post update in Discord `#dev-log` (or let the GitHub webhook do it)

### When Adding Community Links

When Discord/Patreon are live, update these `PLACEHOLDER` values:

- `website/mkdocs.yml` → `extra.social` links
- `website/docs/community/discord.md` → invite link
- `website/docs/community/support.md` → Patreon URL
- `website/docs/about/contact.md` → Discord and Patreon URLs

### When Domain Is Registered

- Update `site_url` in `mkdocs.yml`
- Add `CNAME` file to `website/docs/`
- Update GitHub Pages custom domain in repo Settings
- Wait for DNS propagation (up to 24 hours)
