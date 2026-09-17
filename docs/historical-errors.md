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
  - Deploy via dedicated Python `paramiko` script (`scripts/deploy_sftp.py`): Explicitly set `look_for_keys=False` and `allow_agent=False` on `ssh.connect()`, backed by a fallback handler for PAM `keyboard-interactive`. This completely isolates SFTP deployment from shell quoting, heredoc parsing, and OpenSSH path canonicalization bugs (`path canonicalization failed`), auto-detects remote directory layout, and creates directory trees (`mkdir -p`) deterministically.
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

### [i18n & Static Hosting] Hybrid Content Negotiation and Language Preference Persistence
- **Context**: Serving multi-language static content (`/` and `/en/`) automatically based on visitor locale while strictly honoring manual user language overrides.
- **Root Cause**: Relying exclusively on client-side JS redirects produces visible layout shifts (FOIC) on first load for non-default locales; conversely, relying strictly on server `Accept-Language` headers without state overrides forces users back to the detected language if they intentionally switch locales.
- **Prevention Patterns**:
  - Implement a hybrid strategy: server-level `.htaccess` rewrite conditions on Hetzner Apache for instant zero-latency routing of new visitors requesting English.
  - Complement with client-side `localStorage` persistence (`palazzo_usellini_lang`) to record explicit user clicks on language links, preventing automatic redirects if an English speaker intentionally explores the Italian version.

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
  - Implement cross-language fallbacks for dynamic data loops and listings (`{{ if eq (len $newsPages) 0 }}{{ $newsPages = where (index hugo.Sites 0).RegularPages "Section" "news" }}{{ end }}`) so that complete archives and event schedules remain visible to international visitors even before dedicated translated articles are authored.





