# Palazzo Usellini - Official Static Website

Static website for **Palazzo Usellini** located in Arona (NO), Italy - [palazzousellini.com](https://palazzousellini.com).

## 🏛️ Architecture & Technologies
- **SSG**: [Hugo Extended](https://gohugo.io/) (v0.166+)
- **Hosting**: Hetzner Web Hosting
- **CI/CD**: GitHub Actions with automatic SFTP deployment on push to `main`
- **Privacy & GDPR**: *Privacy by Design* architecture with zero tracking cookies and no third-party CDN dependencies.
- **Localization Ready**: Native support for multilingual content (currently Italian, ready for English dual-language setup).

---

## 🚀 Local Development

To start the local development server with live reload:

```bash
# If using Homebrew
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

# Start Hugo server
hugo server -D
```

The site will be available at `http://localhost:1313`.

---

## 📁 Project Structure & Content

- `content/`:
  - `_index.md`: Homepage (Casa Usellini presentation, hero banner, and recent highlights)
  - `storia/index.md`: Historical monograph, 1721 Teresian cadastral map, and historical photos
  - `galleria/index.md`: Photo gallery (20 curated high-resolution photos with metadata)
  - `contatti/index.md`: Location and contact information
  - `privacy/index.md`: GDPR-compliant zero-cookie privacy policy
  - `news/`: Historical events and concert news stored as *Page Bundles* (`content/news/<slug>/index.md`)
- `layouts/`:
  - `_default/baseof.html`: Master HTML shell (header, navigation, footer, metadata)
  - `index.html`: Homepage layout with hero section and latest events
  - `news/single.html`: **Centralized single template for all news/articles** (modifying this file updates the layout of every article)
  - `news/list.html`: Archive and catalog listing template (`/news/`)
  - `galleria/single.html`: Photo gallery layout
- `static/`:
  - `css/style.css`: Responsive, elegant CSS stylesheet
  - `images/`: Official vector logo (`logo.png`) and cover image (`hero.jpg`)
- `inbox/`: Drop-zone folder for uploading raw materials (notes, brochures, photos) to be processed into articles
- `scripts/`:
  - `migrate_publii.py`: Automated migration script from Publii backups (`.tar` with SQLite and media)

---

## 🔐 GitHub Actions Deployment Setup (Hetzner SFTP)

The deployment pipeline is defined in `.github/workflows/deploy.yml`. It builds the static site and securely transfers only modified files to Hetzner via SFTP.

To enable deployment, configure the following secrets in GitHub (**Settings > Secrets and variables > Actions**):

| Secret | Description | Required |
|---|---|---|
| `HETZNER_SFTP_HOST` | SFTP host address of the Hetzner server | Yes |
| `HETZNER_SFTP_USER` | SFTP account username | Yes |
| `HETZNER_SFTP_PASSWORD` | SFTP account password | Yes |
| `HETZNER_REMOTE_DIR` | Destination root directory on Hetzner (e.g. `/public_html/static/` or `/public_html/`) | Yes |
| `HETZNER_SFTP_PORT` | SFTP port (defaults to `22` if not specified) | No |
