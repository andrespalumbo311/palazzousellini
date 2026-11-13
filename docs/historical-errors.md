# Historical Errors & Architectural Patterns

## Quick Index
- **1. Deployment & CI/CD SFTP**: `Protocol Mismatch in FTP Action`, `SFTP Root Path Canonicalization`, `lftp Interactive Auth Syntax`, `Paramiko Key-Probing Rejection`
- **2. Hugo SSG, Templating & i18n**: `Go Reference Timestamp Corruption`, `Build-Time vs. Daily Event Filtering`, `Dual-Layer Language Redirect Conflict`, `Relative Bundle Media 404s`, `Menu Prefix Active Collision`, `URI Sanitization #ZgotmplZ`
- **3. Frontend, Accessibility & Core Web Vitals**: `Remote Map Iframe Blocking`, `Uncompressed Camera Assets & Generic Tokens`, `Hero Visual vs. CTA Overlap`, `Dark Mode Contrast Collapse`, `Unscaled Mobile Hero LCP`, `Fake Tablist ARIA Mismatch`, `Label-in-Name Mismatch`, `Opacity Compounding Contrast Loss`, `Hardcoded Base Typography & Asymmetric Attenuation`, `Unprotected Storage & Footer-Only Toggle`
- **4. Content Migration & Editorial Governance**: `Unscoped HTML Regex Replacement`, `Institutional Misattribution`, `Promotional Tone & Scope Creep`, `Toponymic Inaccuracy`

---

## 1. Deployment & CI/CD SFTP

| Error Class / Technical Challenge | Root Cause (Abstract) | Preventive Action / Architectural Pattern |
| :--- | :--- | :--- |
| **Protocol Mismatch in FTP Action** | Using FTP-only actions (e.g. `SamKirkland/FTP-Deploy-Action` backed by `basic-ftp`) with `protocol: sftp` fails validation immediately. | Use `lftp` for SFTP CI/CD (`lftp mirror --reverse --delete --parallel=N`) and restrict sync strictly to `./public/`. |
| **SFTP Root Path Canonicalization** | Raw `sftp put -r` with absolute paths (`/public_html/`) fails when master users land in account home directories (`/usr/home/user/`) and does not create missing parent trees. | Use relative remote paths configured via GitHub Secrets (`HETZNER_SFTP_HOST`, `HETZNER_SFTP_USER`, `HETZNER_SFTP_PASSWORD`, `HETZNER_REMOTE_DIR`). |
| **lftp Interactive Auth Syntax** | Passing `-u` to `open` inside `lftp` fails (`Unknown command '-p'`). | Declare credentials with `user "$USER" "$PASS"` prior to `open -p "$PORT" sftp://$HOST`. |
| **Paramiko Key-Probing Rejection** | `SSHClient.connect()` probes local SSH keys and agent before password auth, causing strict SFTP servers to drop the handshake. | In Python SFTP scripts (`scripts/deploy_sftp.py`), invoke `Transport.auth_password()` directly; never store plain-text credentials in code. |

---

## 2. Hugo SSG, Templating & i18n

| Error Class / Technical Challenge | Root Cause (Abstract) | Preventive Action / Architectural Pattern |
| :--- | :--- | :--- |
| **Go Reference Timestamp Corruption** | Naive format strings like `"02 Gennaio 2006"` match Go's English reference token `"Jan"` inside `"Gennaio"`, corrupting rendered dates. | Set `defaultContentLanguage = 'it'` and `locale = 'it-IT'` in `hugo.toml`; use `{{ .Date \| time.Format ":date_long" }}`. |
| **Build-Time vs. Daily Event Filtering** | Evaluating `now` in Hugo templates freezes event visibility at compile time until the next CI rebuild. | Emit `data-event-date="YYYY-MM-DD"` from Hugo and evaluate `is-past`/`is-upcoming` daily in client JS against `new Date()`, keeping a progressive-disclosure archive toggle. |
| **Dual-Layer Language Redirect Conflict** | Combining Apache `.htaccess` `mod_rewrite` 302 redirects with client-side `localStorage` redirects fires server redirects before JS runs, ignoring manual overrides. | Maintain a single source of truth for language routing (client-side `localStorage` on `/` only); never reference cookies/state in `.htaccess` that client code never writes. |
| **Relative Bundle Media 404s** | Relative `src="gallery/..."` paths resolve under `/en/<section>/` on translated pages while shared assets live under `/<section>/`; `site.RegularPages` also partitions by language. | Normalize media URLs with root-relative paths (`printf "/%s/%s" .Section .src` or `.RelPermalink`) and handle cross-language fallbacks explicitly. |
| **Menu Prefix Active Collision** | Checking `ne .URL "/"` fails on secondary language roots (`/en/`), causing Home to stay active on every `/en/...` subpage. | Compare against `site.Home.RelPermalink` (`ne .URL site.Home.RelPermalink`), emit `canonical` + reciprocal `hreflang` + `x-default`, normalize `og:locale` (`it_IT`), and set `disableKinds = ['taxonomy', 'term']`. |
| **URI Sanitization `#ZgotmplZ`** | Go's `html/template` flags non-standard Markdown URI schemes like `[num](tel:...)` and replaces them with `#ZgotmplZ`. | Format phone numbers as clean plain text (`Tel. 342.0057160`) so mobile OSes auto-detect them safely without raw `tel:` Markdown links. |

---

## 3. Frontend, Accessibility & Core Web Vitals

| Error Class / Technical Challenge | Root Cause (Abstract) | Preventive Action / Architectural Pattern |
| :--- | :--- | :--- |
| **Remote Map Iframe Blocking** | Remote OpenStreetMap `<iframe>` embeds fail or render blank boxes under browser tracking protection (Firefox ETP, Brave Shields, Safari ITP, uBlock). | Self-host Leaflet in `static/vendor/leaflet/`, render tiles into `<div id="osm-map">` with local markers, and include a direct external Google Maps link. |
| **Uncompressed Camera Assets & Generic Tokens** | Raw 4–15 MB camera uploads with EXIF/GPS bloat mobile LCP and leak location data; generic hex colors disconnect from physical architecture. | Process images via `.agents/skills/optimize-images/` (`hero` 2000px/85%, `gallery` 1400px/82%, `thumb` 800px/80%), strip EXIF/GPS, deliver WebP `<picture>`, and calibrate tokens from physical palace photos. |
| **Hero Visual vs. CTA Overlap** | Placing CTAs inside absolute-positioned hero media causes overlap on tall mobile screens and sticky-header anchor collisions. | Decouple `.hero-visual` from `.hero-actions-mobile` in normal document flow on mobile and add section anchor padding. |
| **Dark Mode Contrast Collapse** | Inverting backgrounds while keeping deep heritage bordeaux (`#74242B`) drops contrast to ~1.8:1; sharing one token washes out solid buttons. | Elevate text/heading tokens to antique ruby (`#E57D86`, >8.5:1), keep saturated `#8F242C` + white text for primary buttons, and use inline anti-FOUC `<head>` init. |
| **Unscaled Mobile Hero LCP** | Serving a 2000px (~620 KB) desktop WebP to mobile viewports inflates mobile LCP (~4.4s). | Serve `hero-mobile.webp` (<=800px) via `<source media="(max-width: 768px)">` paired with media-matched `<link rel="preload" fetchpriority="high">` in `<head>`. |
| **Fake Tablist ARIA Mismatch** | Using `role="tablist"` with plain `<button>` children lacks `role="tab"`, breaking WCAG 1.3.1 and Lighthouse `agent-accessibility-tree`. | Use `role="group"` with `aria-pressed="true\|false"` for list filters, and provide `/llms.txt`, `/llms-full.txt`, and JSON-LD Schema.org (`LandmarksOrHistoricalBuildings`). |
| **Label-in-Name Mismatch** | Static `aria-label` differing from visible button text violates WCAG 2.5.3 (Label in Name). | Keep `aria-label` synchronized with visible button text on every state transition. |
| **Opacity Compounding Contrast Loss** | Nesting `opacity: 0.85` on cards and inner text degrades contrast to ~3.1:1. | Attenuate past items with explicit background tints (`#fdfbf7`), grayscale image filters, and darkened text tokens (`#54504C`, `#26544A`). |
| **Hardcoded Base Typography & Asymmetric Attenuation** | Fixed dark hexes on `h1-h6`/`.page-body` or `.is-past` selectors without dark-mode pairs produce ~1.05:1–1.8:1 black-on-black text in dark mode. | Bind all typography to semantic CSS variables (`var(--color-text)`) and pair every state attenuation selector with an explicit dark-mode override (`#D2CCC2`, >7:1). |
| **Unprotected Storage & Footer-Only Toggle** | Unwrapped `localStorage` calls throw in strict mobile privacy modes, halting JS before listeners bind; footer-only toggles hurt mobile ergonomics. | Wrap all `localStorage` calls in `try/catch`, initialize theme listeners early, and sync multi-instance `.theme-toggle-btn` controls in both mobile drawer and footer. |

---

## 4. Content Migration & Editorial Governance

| Error Class / Technical Challenge | Root Cause (Abstract) | Preventive Action / Architectural Pattern |
| :--- | :--- | :--- |
| **Unscoped HTML Regex Replacement** | Global string/regex replacements (e.g. `text.replace('</li>', '')`) strip closing tags from legitimate HTML lists across documents. | Scope regex substitutions strictly to target parent classes/selectors and unit-test list conversion in isolation. |
| **Institutional Misattribution** | Framing the historic residence as organizer or co-organizer of hosted third-party events. | Always state *"Casa Usellini ospita..."*; never assert co-organization or institutional partnership. |
| **Promotional Tone & Scope Creep** | Importing lyrical marketing copy or unrelated partner notices from `inbox/` flyers. | Keep copy dry, sober, and factual (dates, times, performers, practical details) strictly scoped to the residence and its hosted program. |
| **Toponymic Inaccuracy** | Mixing up institutional and venue naming across articles. | Use **Casa Usellini** for resident/garden events and **Palazzo Usellini** for the global historic institution. |
