# AGENTS.md

## Repository Overview
Static website for **Palazzo Usellini** (Arona, NO, Italy) - [palazzousellini.com](https://palazzousellini.com).

## Architecture & Conventions
- **SSG**: Hugo Extended for long-term stability and zero runtime dependencies.
- **Deployment**: GitHub Actions CI/CD via SFTP to Hetzner web hosting (configured via GitHub Secrets).
- **Content**: Markdown with YAML frontmatter, optimized images and responsive galleries.
- **Host Environment**: Fedora Atomic (ublue). Avoid modifications to `/usr`. Use isolated runtimes or Homebrew for local developer tooling.
- **Authentic Palette**: Colors derived directly from the physical palace:
  - `--color-bordeaux` (`#74242B`): Portico window shutters.
  - `--color-verde` (`#487A6F`): 18th-century verdigris shutters on the Casacce garden building.
  - `--color-giallo-portico` (`#DCAE45`): Internal courtyard portico stucco.
  - `--color-azzurro-facciata` (`#EDF3F7`): Restored exterior facade on Via Pertossi.

## Editorial & Content Guidelines (Tone of Voice & Entity Naming)
- **Tone of Voice**: Dry, sober, factual, and direct. Avoid emphatic, lyrical, or promotional phrasing (e.g. no "evocative journeys", no embellished adjectives).
- **Institutional Role**: Palazzo Usellini does not organize events; it solely **hosts** concerts, festivals, and cultural events within its garden or courtyard. Use clear phrasing (*"Casa Usellini hosts..."*) and never frame the residence as organizer or co-organizer.
- **Authentic Naming**:
  - Use **Casa Usellini** for events, concerts, and activities taking place in the garden or inner spaces of the residence.
  - Use **Palazzo Usellini** for the global historic institution, history, and overall site naming.
- **Content Scope**: Site communication strictly pertains to the historic residence and the cultural and artistic program hosted within its grounds.
- **Inbox Ingestion Workflow**:
  - Process raw materials in `inbox/` by rendering flyers and photos in high resolution and converting them to WebP via the project skill `.agents/skills/optimize-images/scripts/optimize_image.sh`.
  - Create bilingual page bundles (`index.md` and `index.en.md`) and populate the `events:` frontmatter parameter for seamless synchronization with the homepage calendar.
  - Do not use markdown `[num](tel:...)` links to prevent Go/Hugo template sanitization (`#ZgotmplZ`); format phone numbers as clean plain text (e.g. `Tel. 342.0057160`).
  - Remove temporary source files from `inbox/` once processing is complete.

## Image Management Standard
- **Skill**: Standardized via project skill [`.agents/skills/optimize-images/`](file:///.agents/skills/optimize-images/SKILL.md).
- **Tooling**: Use Homebrew `cwebp` and `magick` (`./.agents/skills/optimize-images/scripts/optimize_image.sh`).
- **Profiles**:
  - `hero`: max width 2000px, quality 85, WebP/progressive JPEG, target &le; 350 KB.
  - `gallery`: max width 1400px, quality 82, WebP, target 80–150 KB.
  - `thumb`: max width 800px, quality 80, WebP, target &le; 50 KB.
- **Privacy & Hygiene**: Always strip EXIF and GPS metadata from photographic assets.
- **Licensing & Open Source**: Content & photographic assets licensed under CC BY 4.0 (attribution required to `palazzousellini.com`). Public repository hosted at `andrespalumbo311/palazzousellini`.

## Operational Memory Protocol
- Always consult [docs/historical-errors.md](file:///var/home/andres/Documents/palazzousellini/docs/historical-errors.md) before architectural or structural changes.
- Upon resolving technical issues, update the historical errors library with abstract, reusable explanations and prevention patterns.
