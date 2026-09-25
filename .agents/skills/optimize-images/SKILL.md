---
name: optimize-images
description: Image optimization, resizing, EXIF metadata stripping, and WebP conversion for Palazzo Usellini website imagery.
---

# Skill: Image Optimization Protocol (Palazzo Usellini)

## Purpose & Context
This skill standardizes the processing of any image added or updated in the **Palazzo Usellini** repository. It ensures that historical photographs, concert posters, and residence views download quickly on mobile devices, safeguard location privacy (EXIF/GPS stripping), and preserve high aesthetic fidelity.

## When to Use This Skill
Activate this procedure whenever:
- Adding a new cover hero image (`hero.jpg`, `hero.webp`) or full-page banner.
- Uploading new photographs for the **Gallery** section (`content/galleria/gallery/`).
- Publishing new articles with concert posters, artist portraits, or summer festival materials (`content/news/<slug>/`).
- Addressing LCP (*Largest Contentful Paint*) regressions caused by files exceeding 400 KB.

---

## Resolution & Compression Profiles

| Profile | Target Usage | Max Width | Format | Quality | Target Size |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`hero`** | Homepage hero, full-width banners | `2000px` | `.webp` / `.jpg` | `85%` | &le; 350 KB |
| **`gallery`** | Monographs, estate photography, articles | `1400px` | `.webp` | `82%` | 80 – 150 KB |
| **`thumb`** | News grid thumbnails, avatars | `800px` | `.webp` | `80%` | &le; 50 KB |

---

## Execution via Helper Script

The helper script is located at `scripts/optimize_image.sh`:

```bash
# Full-width hero image optimization
./.agents/skills/optimize-images/scripts/optimize_image.sh --profile hero static/images/hero.jpg

# Single photo optimization for article or gallery
./.agents/skills/optimize-images/scripts/optimize_image.sh --profile gallery content/news/my-event/poster.png

# Batch processing an entire folder
./.agents/skills/optimize-images/scripts/optimize_image.sh --profile gallery content/galleria/gallery/*.jpg
```

---

## Mandatory Standards & Conventions
1. **Zero Metadata (Privacy)**: All EXIF, GPS, and camera capture timestamps must be eliminated (`-strip` or `-metadata none`).
2. **Kebab-Case Naming**: Alphanumeric lowercase characters and hyphens only (e.g. `2026-violin-concert.webp`). Never use spaces, special characters, or arbitrary suffixes (`-scaled`, `Screenshot_...`).
3. **WebP First**: Always favor `.webp` for web delivery, retaining fallback JPEG only where explicitly mandated by legacy templates.
