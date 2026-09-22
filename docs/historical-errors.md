# Historical Errors & Prevention Library

## Anomaly Registry and Technical Prevention

*This document tracks error classes, root causes, and architectural prevention strategies following the AGENTS.md operational protocol.*

---

### [Setup & Bootstrap] Repository Initialization and CI/CD SFTP Configuration
- **Context**: Repository setup, Publii-to-SSG migration, and automated SFTP deployment.
- **Root Cause**:
  1. Attempting to use FTP-specific actions (such as `SamKirkland/FTP-Deploy-Action`) with `protocol: sftp` causes immediate validation failures (`protocol: invalid parameter`) because `basic-ftp` exclusively handles FTP/FTPS.
  2. Raw OpenSSH `sftp put -r` combined with absolute remote paths (e.g. `/public_html/`) fails with `path canonicalization failed` because hosting master users land in their account home directory (e.g. `/usr/home/user/`), making `/public_html` non-existent at the filesystem root `/`. Furthermore, raw `sftp put -r` does not create missing parent directory trees.
  3. Inside the interactive `lftp` shell, the `open` command does not accept the `-u` flag (`Unknown command '-p'`). Authentication must be declared with `user "$USER" "$PASS"` prior to invoking `open -p "$PORT" sftp://$HOST`.
  4. By default, `paramiko` searches for local runner SSH keys and probes the SSH agent before submitting passwords, causing strict SFTP servers (such as Hetzner) to immediately reject the handshake (`paramiko.ssh_exception.AuthenticationException`).
- **Prevention Patterns**:
  - Never store plain-text credentials, usernames, or internal server hostnames in repository code; always leverage GitHub Repository Secrets (`HETZNER_SFTP_HOST`, `HETZNER_SFTP_USER`, `HETZNER_SFTP_PASSWORD`, `HETZNER_REMOTE_DIR`).
  - For CI/CD SFTP deployment, prefer `lftp mirror --reverse --delete --parallel=N` for parallel delta-only transfers (only changed files uploaded, stale files removed). This replaces slow sequential Python/paramiko uploads.
  - When scripting SFTP with `paramiko` (e.g. local testing via `scripts/deploy_sftp.py`), use `Transport.auth_password()` directly instead of `SSHClient.connect()`. `SSHClient` probes multiple auth methods in unpredictable order (publickey, keyboard-interactive) before password, causing strict SFTP servers to reject the handshake. Direct `Transport.auth_password()` sends only the password method.
  - Restrict SFTP synchronization strictly to generated build artifacts (`./public/`) without pushing source files to the remote web hosting root.

---

### [Content Migration] HTML Normalization and Regular Expression Scoping
- **Context**: Extracting legacy articles from hybrid database schemas (WordPress Gutenberg blocks / Publii block JSON / raw HTML) into clean Markdown.
- **Root Cause**: Indiscriminate global closing-tag replacements (e.g. `text.replace('</li>', '')` intended to clean up a specific carousel slider container) strip closing tags from legitimate HTML lists throughout the document, causing list items to collapse into a single concatenated block.
- **Prevention Patterns**:
  - Strictly scope regex substitutions to their specific parent classes or container selectors (`re.sub(r'<li class="slider-item[^>]*>(.*?)</li>', ...)`).
  - Test individual list item markdown conversion (`- item`) in isolation before writing target files.

---

### [Hugo & Go Templating] Date Localization and Reference Timestamps
- **Context**: Formatting localized dates (e.g. Italian month names) in Hugo templates.
- **Root Cause**: Go uses fixed reference timestamp tokens (`02` for day, `01`/`January` for month, `2006` for year). Naive format strings such as `"02 Gennaio 2006"` result in Go matching the English substring `"Jan"` inside `"Gennaio"`, leading to corrupted date renderings.
- **Prevention Patterns**:
  - Configure `defaultContentLanguage = 'it'` and `locale = 'it-IT'` in `hugo.toml`.
  - Use Hugo's native localized date formatting functions: `{{ .Date | time.Format ":date_long" }}` to produce correct, fully declined month names.

---

### [SSG & Dynamic Scheduling] Client-Side Daily Date Synchronization vs. Build-Time Static Evaluation
- **Context**: Displaying dynamic event calendars on static sites (Hugo SSG) that must automatically conceal past events and highlight upcoming dates on a daily cadence without requiring automated daily CI/CD rebuilds.
- **Root Cause**: Hugo templates evaluate timestamps strictly at compile/build time (`now`). In a static site without daily cron triggers, hardcoding visibility logic at build time leaves expired events permanently visible as "upcoming" until the next commit.
- **Prevention Patterns**:
  - Keep the Hugo SSG layer responsible for data normalization and emitting structured ISO-8601 attributes (`data-event-date="YYYY-MM-DD"`).
  - Delegate daily state evaluation (`is-past`, `is-upcoming`, season conclusion banner) to lightweight client-side JavaScript comparing against the visitor's local `new Date()`.
  - Provide graceful degradation and progressive disclosure (e.g. "Mostra appuntamenti già trascorsi" toggle) to preserve accessibility, SEO indexing, and user choice.

---

### [i18n & Static Hosting] Dual-Layer Language Redirect Conflicts (Server-Side vs. Client-Side)
- **Context**: Serving multi-language static content (`/` and `/en/`) automatically based on visitor locale while strictly honoring manual user language overrides.
- **Root Cause**: Running **two independent redirect mechanisms** — Apache `.htaccess` `mod_rewrite` checking `Accept-Language` headers AND client-side JavaScript checking `localStorage` — creates an unresolvable conflict. The server-side 302 redirect fires **before** the browser executes any JavaScript, so `localStorage` preferences saved by click handlers are never consulted. Users who click the IT language link get redirected back to EN because Apache intercepts the request to `/` and issues a 302 before the page (and its JS) ever loads. The `.htaccess` also referenced a cookie (`palazzo_usellini_lang=it`) that no code ever set, making the server-side override condition permanently unmet.
- **Prevention Patterns**:
  - **Single source of truth**: Choose ONE layer for language routing — never duplicate redirect logic across server and client.
  - For static sites with JS-based language preference: use client-side `localStorage` as the sole redirect mechanism (runs on `/` after page load). Remove any server-side `mod_rewrite` language negotiation.
  - If server-side routing is preferred (zero-latency): ensure the server-side mechanism (cookie, URL parameter) is actually written by the client-side code that handles user language switches. Never reference state (cookies, headers) that no code path produces.

---

### [Mapping & Third-Party Embedding] Self-Hosted OpenStreetMap DOM Rendering vs. Remote Iframe Embedding
- **Context**: Embedding interactive geographical maps on static sites without violating GDPR or breaking under ad-blockers and privacy shields.
- **Root Cause**: Embedding OpenStreetMap via remote `<iframe>` endpoints (`openstreetmap.org/export/embed.html`) frequently fails or renders blank grey boxes because modern browser tracking protections (Firefox ETP, Brave Shields, Safari ITP, uBlock Origin) intercept remote embed scripts or third-party frame policies.
- **Prevention Patterns**:
  - Avoid third-party remote iframes for location maps.
  - Self-host the lightweight Leaflet engine locally in `static/vendor/leaflet/` to eliminate external runtime dependencies and maintain strict zero-cookie GDPR compliance.
  - Render OpenStreetMap tiles directly into a native local DOM element (`<div id="osm-map">`) with a local marker asset, accompanied by a direct external link for navigation via Google Maps.

---

### [Asset Pipeline & Identity] Uncompressed Photographic Bloat & Authentic Architectural Color Calibration
- **Context**: Managing high-resolution camera assets (hero photos, concert galleries) and harmonizing CSS design tokens with authentic historic architectural features.
- **Root Cause**: Raw camera uploads (often 4–15 MB JPEGs/PNGs containing unstripped EXIF/GPS telemetry) severely degrade mobile performance (LCP) and risk location privacy. Additionally, defining site palettes with arbitrary generic hex values (e.g. generic forest green `#2C5A46`) disconnects the digital branding from the authentic 18th-century material reality (e.g. weathered verdigris patina `#3B5D55` on garden shutters and warm walnut-lacquered wood `#74242B` on portico shutters).
- **Prevention Patterns**:
  - Encapsulate image ingestion into a deterministic Project Skill (`.agents/skills/optimize-images/`) with predefined profiles (`hero` at 2000px/85%, `gallery` at 1400px/82%, `thumb` at 800px/80%).
  - Automatically strip all EXIF/GPS metadata during processing to safeguard private residential privacy.
  - Implement modern WebP delivery with `<picture>` fallbacks for full-width hero media, reducing asset payload by over 85–95%.
  - Sample design tokens directly from calibrated, authentic photographic evidence of the physical structure, compensating for lighting conditions (e.g. direct sun vs. shadowed colonnades).

---

### [Hugo i18n & Asset Resolution] Relative Resource Resolution in Translated Leaf Bundles & Cross-Language Fallbacks
- **Context**: Serving multi-language static websites (`/` and `/en/`) where static media and articles exist primarily in the default language bundle.
- **Root Cause**: Relative URLs (e.g. `src="gallery/photo.jpg"`) resolve relative to the current URL path. In translated URLs (e.g. `/en/galleria/`), the browser attempts to fetch from `/en/galleria/gallery/photo.jpg`, producing 404 errors because Hugo outputs shared non-page bundle files at `/galleria/gallery/`. Furthermore, `site.RegularPages` in Hugo multilingual mode strictly partitions pages by language; if translated posts do not exist for a section, section archives and dynamic homepage data loops (like concert calendars) silently evaluate to empty collections.
- **Prevention Patterns**:
  - Always normalize media URLs in multilingual templates with absolute root paths (e.g. `printf "/%s/%s" .Section .src` or `.RelPermalink`) to ensure valid resolution across all language prefixes.
---

### [Responsive Layout & Visual Hierarchy] Structural Decoupling of Hero Visual Media and Interactive Actions
- **Context**: Designing full-bleed hero sections on responsive websites where photography must be prominent without obscuring critical calls to action (CTAs) across disparate aspect ratios.
- **Root Cause**: Forcing interactive buttons inside the same absolute-positioned media container across both desktop and mobile viewports causes visual overlap and clutter on tall vertical mobile screens. Simultaneously, eliminating section top margins without dedicated section anchor padding causes below-the-fold titles (e.g. event calendars) to collide visually with the hero edge or get obscured beneath sticky headers upon in-page anchor navigation.
- **Prevention Patterns**:
  - Structurally separate the visual media wrapper (`.hero-visual`) from responsive action bars (`.hero-actions-mobile`), rendering desktop CTAs overlaid inside the media and mobile CTAs cleanly below the photograph in normal document flow.
---

### [Theme Architecture & Contrast Calibration] Chromatic Inversion in Dark Mode vs. Authentic Historic Palettes
- **Context**: Introducing dark mode styling to historic or heritage brand identities where core identity colors are inherently dark (such as 18th-century noble bordeaux `#74242B` derived from courtyard portico shutters).
- **Root Cause**: Inverting background surfaces to dark charcoal/ebony while preserving deep brand colors causes textual contrast to collapse from >9:1 (light background) to an unreadable 1.8:1 (dark background), violating WCAG AAA standards. Furthermore, sharing a single color token across both text headings and solid interactive button fills causes buttons to wash out if the token is globally brightened.
- **Prevention Patterns**:
  - Perform tonal elevation for typography: elevate deep heritage shades to their luminous, antique equivalents (e.g. `#E57D86` antique ruby) for headings and text accents to maintain contrast >8.5:1 on dark surfaces.
  - Decouple interactive button fills: preserve deep, saturated bordeaux fills (`#8F242C`) with crisp white typography for primary CTAs so buttons retain authority and tactile contrast.
  - Implement a zero-FOUC (Flash of Unstyled Content) synchronous bootstrap in `<head>` alongside dual-layer CSS cascade (supporting both system `prefers-color-scheme` and persistent `data-theme` manual overrides).

---

### [Core Web Vitals & Accessibility] Mobile LCP Asset Sizing, ARIA Role Hierarchies & Agentic Browsing Readiness
- **Context**: Optimizing static sites (Hugo SSG) for Google Lighthouse 13 / PageSpeed Insights across Mobile/Desktop, WCAG AA/AAA standards, and AI Agentic Browsing (`agent-accessibility-tree` & `llms.txt`).
- **Root Cause**:
  1. *Unscaled Hero Images*: Serving a desktop 2000px WebP (~620 KB) indiscriminately to mobile screens inflates LCP (4.4s) due to excessive payload and decode latency on bandwidth-constrained mobile devices.
  2. *ARIA Children-Role Mismatch*: Using `role="tablist"` on a container where children are standard `<button>` tags without `role="tab"` violates WCAG 1.3.1 (`aria-required-children`), which in turn invalidates the browser's accessibility tree and collapses Lighthouse's `agent-accessibility-tree` / `agentic-browsing` audit from 100% to 50%.
  3. *WCAG 2.5.3 (Label in Name) Discrepancies*: Setting a static descriptive `aria-label` (e.g. "Toggle theme (dark / light)") on a button whose visible inner text is "Theme: Light" causes a mismatch because assistive tech and screen readers expect the accessible name to strictly include or match the visible label.
  4. *Compounded CSS Opacity degrading Color Contrast*: Applying `opacity: 0.85` to a parent card and another `opacity: 0.85` to an inner element washes out text (`#66625D`) against light surfaces down to `#8f8c87` (~3.1:1 contrast), violating WCAG AA 4.5:1.
- **Prevention Patterns**:
  1. *Responsive `<picture>` with Preloads*: Serve dedicated mobile breakpoints (`hero-mobile.webp` at ≤ 800px / ~98 KB) via `<source media="(max-width: 768px)">` and paired `<link rel="preload" as="image" ... media="...">` in `<head>` to cut mobile LCP by > 80%.
  2. *Semantic Filter Groups over Fake Tabs*: Use `role="group"` with `aria-pressed="true|false"` for in-page list filtering rather than `role="tablist"`, maintaining clean accessibility trees for both human screen readers and autonomous AI agents.
  3. *Synchronized Accessible Names*: Keep `aria-label` synchronized with the visible text string whenever UI state changes, or allow the element's visible text node to serve as its accessible name.
  4. *Opacity-Free Visual Attenuation & Calibrated Tokens*: Differentiate past or secondary items via subtle background tints (`#fdfbf7`), grayscale filters, and darkened text tokens (`#54504C`, `#26544A`) that retain > 7:1 contrast without opacity bleed.
  5. *Standardized Agentic Browsing Assets*: Provide root `/llms.txt` and `/llms-full.txt` alongside JSON-LD Schema.org (`LandmarksOrHistoricalBuildings`) to ensure autonomous AI search engines and agents parse site structure without crawling degradation.

---

### [Hugo i18n & Multilingual Architecture] Prefix-Based Menu Active State Collisions, SEO Alternates & Localization Leaks
- **Context**: Serving multi-language static websites (`/` and `/en/`) with Hugo SSG where the default language resides at the root `/` and secondary languages reside in subdirectories (`/en/`).
- **Root Cause**:
  1. *Hardcoded Root URL Checks for Menu Active State*: Testing `ne .URL "/"` to exclude the home item from prefix-based active matching (`hasPrefix $.RelPermalink .URL`) fails on secondary languages where the home URL is `/en/`. Because `"/en/" != "/"`, all pages under `/en/` match the prefix `"/en/"`, causing the home menu item to remain active concurrently with the actual current section on every subpage.
  2. *Missing Bidirectional `<head>` hreflang & Canonical Directives*: Relying exclusively on XML sitemaps without declaring `<link rel="canonical">` and `<link rel="alternate" hreflang="...">` (including `x-default`) in the HTML `<head>` leaves search engine crawlers without unambiguous language pairing and canonical directives.
  3. *Unlocalized UI Strings and Hardcoded Backlinks*: Omitting language conditionals or dictionary lookups on utility UI badges, back links, and aria-labels leads to Italian strings leaking into English templates and back-links navigating across language boundaries (e.g. English subpage returning to `/` instead of `/en/`).
  4. *Unused Taxonomy Kinds*: Leaving `disableKinds` unset generates empty or unlocalized tag/category archive listings that degrade crawl budgets.
- **Prevention Patterns**:
  - In navigation templates, always evaluate parent/prefix active states against the language-specific root dynamically (`ne .URL site.Home.RelPermalink`) instead of a static `"/"`.
  - Always render canonical URLs and iterate `.AllTranslations` in `<head>` to emit reciprocal `hreflang` tags alongside `x-default` mapped to the primary language edition.
  - Bind all inter-language back-links to `site.Home.RelPermalink` rather than hardcoded `/`.
  - Normalize Open Graph `og:locale` to underscore notation (`it_IT`, `en_US`) and emit `og:locale:alternate`.
  - Explicitly disable unused SSG taxonomy kinds (`disableKinds = ['taxonomy', 'term']`) in `hugo.toml` to prevent thin or unlocalized orphan pages.

---

### [Theme Architecture & Mobile Ergonomics] Base Heading Dark Mode Inversion Leaks, Past-Event Contrast & Multi-Instance Toggle Synchronization
- **Context**: Multilingual static websites with client-side dark mode toggling, dynamic date-based status attenuation (e.g. past events), and mobile-first responsive navigation.
- **Root Cause**:
  1. *Hardcoded Dark Hex Values in Base Typography*: Declaring fixed dark hex colors (such as `#171615` on `h1-h6` or `#272523` on `.page-body`) instead of semantic CSS variables (`var(--color-text)`) causes unstyled headings (e.g. `.intro-text-box h2`) and body text to remain dark when background surfaces shift to ebony/charcoal (`#151312` / `#201D1B`), collapsing contrast to unreadable black-on-black (~1.05:1).
  2. *Asymmetric Attenuation Rules on State-Altered Components*: Attenuating past or completed items via hardcoded muted colors (e.g. `.calendar-event-card.is-past .event-card-title { color: #4a4640; }`) without declaring paired dark-mode selectors overrides global text variables due to CSS specificity `(0, 2, 1)`, resulting in illegible dark grey on dark surfaces (~1.8:1).
  3. *Unprotected Client-Side Storage & Footer-Only Mobile Ergonomics*: Reading `localStorage` unconditionally on language negotiation scripts without `try/catch` causes script termination in strict/private mobile browsing environments before theme event listeners are bound. Furthermore, confining the theme toggle exclusively to the bottom footer forces mobile users to scroll through entire archives to toggle appearances.
- **Prevention Patterns**:
  - Always bind base headings and typography to semantic tokens (`var(--color-text)` or `--color-bordeaux`), ensuring uniform automatic adaptation across both Light and Dark palettes.
  - Whenever defining state attenuation styles (`.is-past`, `.is-disabled`), always pair them with explicit dark-mode overrides (`:root[data-theme="dark"] .is-past ... { color: #D2CCC2; }`) to maintain WCAG AAA contrast (> 7:1) against dark surfaces.
  - Always wrap client storage calls (`localStorage`) in `try/catch` and initialize theme listeners early in `DOMContentLoaded`.
  - Provide synchronized multi-instance theme toggles via `querySelectorAll('.theme-toggle-btn')`, exposing immediate toggling within the mobile navigation drawer (`.site-nav`) as well as the global footer.

