---
name: optimize-images
description: Ottimizzazione, ridimensionamento, rimozione metadati EXIF e conversione in WebP per le immagini del sito Palazzo Usellini.
---

# Skill: Image Optimization Protocol (Palazzo Usellini)

## Scopo & Contesto
Questa skill standardizza il trattamento di qualsiasi immagine aggiunta o aggiornata nel repository del sito di **Palazzo Usellini**. Assicura che le fotografie storiche, le locandine dei concerti e gli scorci della dimora siano veloci da scaricare da dispositivi mobili, rispettino la privacy (stripping EXIF/GPS) e preservino un'elevata fedeltà estetica.

## Quando Utilizzare questa Skill
Attiva questa procedura ogni volta che:
- Viene aggiunta una nuova immagine di copertina (`hero.jpg`, `hero.webp`) o un banner a tutta pagina.
- Vengono caricate nuove foto per la sezione **Galleria** (`content/galleria/gallery/`).
- Vengono pubblicati nuovi articoli con locandine di concerti, foto di artisti o rassegne estive (`content/news/<slug>/`).
- Si riscontrano rallentamenti LCP (*Largest Contentful Paint*) dovuti a file superiori a 400 KB.

---

## Profili di Risoluzione & Compressione

| Profilo | Destinazione d'Uso | Larghezza Max | Formato | Qualità | Target Peso |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`hero`** | Hero Home, banner d'apertura | `2000px` | `.webp` / `.jpg` | `85%` | &le; 350 KB |
| **`gallery`** | Monografie, foto palazzo, articoli | `1400px` | `.webp` | `82%` | 80 – 150 KB |
| **`thumb`** | Miniature griglia news, avatar | `800px` | `.webp` | `80%` | &le; 50 KB |

---

## Esecuzione tramite Helper Script

Lo script helper è posizionato in `scripts/optimize_image.sh`:

```bash
# Ottimizzazione immagine Hero a tutto schermo
./.agents/skills/optimize-images/scripts/optimize_image.sh --profile hero static/images/hero.jpg

# Ottimizzazione singola foto per articolo o galleria
./.agents/skills/optimize-images/scripts/optimize_image.sh --profile gallery content/news/mio-evento/locandina.png

# Elaborazione batch di un'intera cartella
./.agents/skills/optimize-images/scripts/optimize_image.sh --profile gallery content/galleria/gallery/*.jpg
```

---

## Standard & Convenzioni Obbligatorie
1. **Zero Metadati (Privacy)**: Tutti i metadati EXIF, GPS e date di scatto della fotocamera devono essere eliminati (`-strip` o `-metadata none`).
2. **Nomenclatura Kebab-Case**: Solo caratteri minuscoli alfanumerici e trattini (es. `2026-concerto-violino.webp`). Mai spazi, caratteri speciali o suffissi casuali (`-scaled`, `Screenshot_...`).
3. **WebP First**: Preferire sempre `.webp` per il caricamento via web, mantenendo l'eventuale fallback JPEG solo dove esplicitamente richiesto da template legacy.
