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
- **Tone of Voice**: Asciutto, sobrio, fattuale e diretto. Evitare formule enfatiche, liriche o promozionali (es. no "viaggi suggestivi", no aggettivazione enfatica).
- **Ruolo Istituzionale**: Palazzo Usellini non organizza eventi; **ospita** concerti, rassegne e manifestazioni culturali nel proprio giardino o corte. Utilizzare formulazioni chiare ("Casa Usellini ospita...") e mai indicare la dimora come organizzatrice o co-organizzatrice.
- **Nomenclatura Corretta**:
  - Usare **Casa Usellini** per gli eventi, i concerti e le attività nel giardino o negli spazi della dimora.
  - Usare **Palazzo Usellini** per l'istituzione complessiva, la storia e la denominazione del sito.
- **Ambito della Comunicazione**: La comunicazione del sito riguarda unicamente la dimora e il programma culturale e artistico ospitato nei suoi spazi.
- **Inbox Ingestion Workflow**:
  - Elaborare i materiali in `inbox/` generando locandine e foto direttamente ad alta definizione e convertendole in WebP via skill `.agents/skills/optimize-images/scripts/optimize_image.sh`.
  - Creare page bundle bilingue (`index.md` e `index.en.md`) e popolare la voce `events:` nel frontmatter per la sincronizzazione immediata con il calendario della homepage.
  - Non inserire link markdown `[num](tel:...)` per evitare la sanitizzazione Go/Hugo (`#ZgotmplZ`); formattare i numeri come testo chiaro (es. `Tel. 342.0057160`).
  - Rimuovere i file temporanei dalla cartella `inbox/` a fine lavorazione.

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
