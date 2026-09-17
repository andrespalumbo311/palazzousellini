#!/usr/bin/env python3
"""
Script di migrazione da backup Publii (SQLite + Media) a Hugo.
Estrae pagine, articoli e immagini rendendo il formato Markdown e Frontmatter
omogeneo, pulito e modulare per l'utilizzo con layout template di Hugo.
"""

import os
import sys
import re
import json
import sqlite3
import tarfile
import tempfile
import shutil
from datetime import datetime, timezone

def clean_html_to_markdown(html_text):
    """Converte blocchi HTML / WordPress residui in Markdown pulito ed omogeneo."""
    if not html_text:
        return ""
    
    text = html_text

    # Rimuove commenti WordPress <!-- wp:... --> e <!-- /wp:... -->
    text = re.sub(r'<!--\s*/?wp:[^>]*-->', '', text)

    # Rimuove wrapper di slideshow Jetpack preservando le immagini
    text = re.sub(r'<div class="wp-block-jetpack-slideshow[^>]*>', '', text)
    text = re.sub(r'<div class="wp-block-jetpack-slideshow_container[^>]*>', '', text)
    text = re.sub(r'<ul class="wp-block-jetpack-slideshow_swiper-wrapper[^>]*>', '', text)
    text = re.sub(r'</ul>\s*<p><a class="wp-block-jetpack-slideshow_button[^>]*>.*?</div>\s*</div>', '', text, flags=re.DOTALL)
    text = re.sub(r'<li class="wp-block-jetpack-slideshow_slide[^>]*>(.*?)</li>', r'\1\n', text, flags=re.DOTALL)

    # Rimuove wrapper wp-block-file preservando i link
    text = re.sub(r'<div class="wp-block-file">\s*<object[^>]*></object>', '', text)
    text = re.sub(r'<a[^>]*class="[^"]*wp-block-file__button[^"]*"[^>]*>.*?</a>', '', text)
    text = text.replace('</div>', '')

    # Gestione figure con caption
    def replace_figure_caption(match):
        img_src = match.group(1).replace('#DOMAIN_NAME#', '').strip()
        caption = match.group(2).strip()
        return f"\n\n![{caption}]({img_src})\n*{caption}*\n\n"

    text = re.sub(
        r'<figure[^>]*>\s*<img[^>]+src="([^"]+)"[^>]*>\s*<figcaption[^>]*>(.*?)</figcaption>\s*</figure>',
        replace_figure_caption,
        text,
        flags=re.DOTALL
    )

    # Gestione figure semplice
    def replace_figure_simple(match):
        img_src = match.group(1).replace('#DOMAIN_NAME#', '').strip()
        alt = match.group(2).strip()
        return f"\n\n![{alt}]({img_src})\n\n"

    text = re.sub(
        r'<figure[^>]*>\s*<img[^>]+src="([^"]+)"[^>]*alt="([^"]*)"[^>]*>\s*</figure>',
        replace_figure_simple,
        text,
        flags=re.DOTALL
    )

    # Gestione img standalone
    def replace_img(match):
        src = match.group(1).replace('#DOMAIN_NAME#', '').strip()
        return f"\n\n![]({src})\n\n"

    text = re.sub(r'<img[^>]+src="([^"]+)"[^>]*>', replace_img, text)

    # Sostituzione tag HTML di base
    text = re.sub(r'<strong>\s*<span style="[^"]*">(.*?)</span>\s*</strong>', r'**\1**', text)
    text = re.sub(r'<span style="[^"]*">\s*<strong>(.*?)</strong>\s*</span>', r'**\1**', text)
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)
    text = re.sub(r'<i>(.*?)</i>', r'*\1*', text)

    # Link
    text = re.sub(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', text)

    # Liste
    text = re.sub(r'<ul[^>]*>', '\n', text)
    text = text.replace('</ul>', '\n')
    text = re.sub(r'<li[^>]*style="list-style-type:\s*none;?"[^>]*>', '', text)
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', text)

    # Paragrafi e a capo
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<p[^>]*>', '\n\n', text)
    text = text.replace('</p>', '\n\n')

    # Rimuove tag HTML residui
    text = re.sub(r'<[^>]+>', '', text)

    # Normalizza righe vuote multiple
    lines = [line.strip() for line in text.splitlines()]
    cleaned = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                cleaned.append('')
                prev_empty = True
        else:
            cleaned.append(line)
            prev_empty = False

    return '\n'.join(cleaned).strip()


def parse_publii_blocks(json_str):
    """Converte blocchi JSON dell'editor nativo di Publii in Markdown e metadati gallery."""
    try:
        blocks = json.loads(json_str)
    except Exception:
        return clean_html_to_markdown(json_str), []

    md_parts = []
    gallery_images = []

    for block in blocks:
        b_type = block.get('type')
        content = block.get('content', '')

        if b_type == 'publii-paragraph':
            if isinstance(content, str) and content.strip():
                md_parts.append(clean_html_to_markdown(content))
        elif b_type == 'publii-header':
            level = block.get('config', {}).get('headingLevel', 2)
            prefix = '#' * level
            if isinstance(content, str):
                md_parts.append(f"{prefix} {content.strip()}")
            elif isinstance(content, dict):
                md_parts.append(f"{prefix} {content.get('text', '').strip()}")
        elif b_type == 'publii-list':
            if isinstance(content, str):
                md_parts.append(clean_html_to_markdown(f"<ul>{content}</ul>"))
        elif b_type == 'publii-image':
            if isinstance(content, dict):
                img_url = content.get('image', '').replace('#DOMAIN_NAME#', '').strip()
                alt = content.get('alt', '').strip()
                caption = content.get('caption', '').strip()
                if img_url:
                    if caption:
                        md_parts.append(f"![{alt or caption}]({img_url})\n*{caption}*")
                    else:
                        md_parts.append(f"![{alt}]({img_url})")
        elif b_type == 'publii-gallery':
            if isinstance(content, dict) and 'images' in content:
                for img in content['images']:
                    src = img.get('src', '').replace('#DOMAIN_NAME#', '').strip()
                    caption = img.get('caption', '').strip()
                    alt = img.get('alt', '').strip()
                    if src:
                        gallery_images.append({
                            'src': src,
                            'title': caption or alt,
                            'alt': alt or caption,
                            'width': img.get('width'),
                            'height': img.get('height')
                        })
        elif b_type == 'publii-html':
            # Ignora script custom non più necessari in Hugo (es. loop lista pagine in JS)
            pass

    return '\n\n'.join(md_parts), gallery_images


def format_yaml_frontmatter(meta):
    """Genera Frontmatter YAML formattato in modo pulito e coerente."""
    lines = ['---']
    for key, val in meta.items():
        if val is None:
            continue
        if isinstance(val, bool):
            lines.append(f"{key}: {'true' if val else 'false'}")
        elif isinstance(val, (int, float)):
            lines.append(f"{key}: {val}")
        elif isinstance(val, list):
            if not val:
                lines.append(f"{key}: []")
            elif isinstance(val[0], str):
                items = ', '.join(f'"{x}"' for x in val)
                lines.append(f"{key}: [{items}]")
            elif isinstance(val[0], dict):
                lines.append(f"{key}:")
                for item in val:
                    first = True
                    for ik, iv in item.items():
                        prefix = "  - " if first else "    "
                        first = False
                        if isinstance(iv, str):
                            escaped_iv = iv.replace('"', '\\"')
                            lines.append(f'{prefix}{ik}: "{escaped_iv}"')
                        else:
                            lines.append(f"{prefix}{ik}: {iv}")
        elif isinstance(val, str):
            escaped = val.replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"')
    lines.append('---')
    return '\n'.join(lines)


def run_migration(tar_path, workspace_dir):
    print(f"[1/5] Apertura archivio di backup: {tar_path}")
    if not os.path.exists(tar_path):
        raise FileNotFoundError(f"Backup non trovato: {tar_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"[2/5] Estrazione temporanea in: {tmpdir}")
        with tarfile.open(tar_path, 'r') as tar:
            tar.extractall(path=tmpdir)

        sqlite_path = os.path.join(tmpdir, 'input', 'db.sqlite')
        conn = sqlite3.connect(sqlite_path)
        c = conn.cursor()

        # Configurazione cartelle di destinazione
        content_dir = os.path.join(workspace_dir, 'content')
        static_dir = os.path.join(workspace_dir, 'static')
        static_images_dir = os.path.join(static_dir, 'images')
        os.makedirs(content_dir, exist_ok=True)
        os.makedirs(static_images_dir, exist_ok=True)

        # Copia logo del sito se presente
        website_media = os.path.join(tmpdir, 'input', 'media', 'website')
        if os.path.exists(website_media):
            for f in os.listdir(website_media):
                if f.endswith('.png') and 'vector' in f:
                    shutil.copy2(os.path.join(website_media, f), os.path.join(static_images_dir, 'logo.png'))
                    print(f"  -> Estratto logo del sito in: static/images/logo.png")

        # Query di tutti i post e pagine
        c.execute('''
            SELECT id, title, slug, text, created_at, modified_at, status, template
            FROM posts
            ORDER BY id ASC
        ''')
        rows = c.fetchall()

        print(f"[3/5] Elaborazione di {len(rows)} contenuti...")

        for row in rows:
            post_id, title, slug, text, created_at, modified_at, status, template = row
            is_page = 'is-page' in status
            
            # Formattazione data ISO
            try:
                date_dt = datetime.fromtimestamp(created_at / 1000.0, tz=timezone.utc)
                date_str = date_dt.strftime('%Y-%m-%dT%H:%M:%S+02:00')
            except Exception:
                date_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+02:00')

            # Cartella media del post nel backup
            post_media_src = os.path.join(tmpdir, 'input', 'media', 'posts', str(post_id))
            
            # Determinazione percorso destinazione
            gallery_data = []
            if is_page:
                if slug == 'home':
                    bundle_dir = os.path.join(content_dir)
                    md_filename = '_index.md'
                elif slug == 'news':
                    bundle_dir = os.path.join(content_dir, 'news')
                    md_filename = '_index.md'
                else:
                    bundle_dir = os.path.join(content_dir, slug)
                    md_filename = 'index.md'
            else:
                bundle_dir = os.path.join(content_dir, 'news', slug)
                md_filename = 'index.md'

            os.makedirs(bundle_dir, exist_ok=True)

            # Inizializzazione variabili per singolo post
            available_images = []
            gallery_data = []
            featured_image = ""
            if os.path.exists(post_media_src):
                for root, dirs, files in os.walk(post_media_src):
                    # Escludi le sottocartelle responsive generate da Publii (Hugo genera le proprie)
                    if 'responsive' in root:
                        continue
                    for f in files:
                        if f.endswith(('-thumbnail.webp', '-xs.webp', '-sm.webp', '-md.webp', '-lg.webp', '-xl.webp', '-2xl.webp')):
                            continue
                        rel_path = os.path.relpath(os.path.join(root, f), post_media_src)
                        dest_file = os.path.join(bundle_dir, rel_path)
                        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                        shutil.copy2(os.path.join(root, f), dest_file)
                        available_images.append(rel_path)

            # Gestione specifica per rendere omogenee le News per i template Hugo
            if not is_page:
                # Estrazione immagini per gallery nel frontmatter se ce ne sono multiple
                gallery_data = []
                if post_id == 10:  # Presentazione catalogo Gianfilippo Usellini
                    featured_image = "GFUsindaco-scaled.jpg"
                    gallery_data = [
                        {"src": "Screenshot-2023-07-18-18.02.27.png", "title": "Presentazione catalogo", "alt": "Presentazione catalogo"},
                        {"src": "GFUsindaco-scaled.jpg", "title": "Federico Monti, Sindaco di Arona", "alt": "Federico Monti"},
                        {"src": "Luigicat-scaled.jpg", "title": "Luigi Sansone ed Elena Pontiggia", "alt": "Luigi Sansone ed Elena Pontiggia"},
                        {"src": "msg212475489-152890-scaled.jpg", "title": "Intervento durante la presentazione", "alt": "Intervento"},
                        {"src": "luigi-scaled.jpg", "title": "Luigi Sansone con il catalogo ragionato", "alt": "Luigi Sansone"},
                        {"src": "msg212475489-152888-scaled.jpg", "title": "Il pubblico nel giardino di Casa Usellini", "alt": "Pubblico nel giardino"},
                        {"src": "msg212475489-152891-scaled.jpg", "title": "I relatori al tavolo", "alt": "Relatori al tavolo"},
                        {"src": "msg212475489-152889-scaled.jpg", "title": "Momento della conferenza", "alt": "Conferenza"}
                    ]
                    body_md = (
                        "Sabato 24 giugno ha avuto luogo nel giardino di Palazzo Usellini la conferenza stampa per la presentazione "
                        "del catalogo ragionato sulla pittura di Gianfilippo Usellini, curato da Luigi Sansone che ne ha illustrato i dettagli.\n\n"
                        "Elena Pontiggia ha esposto con grande competenza e passione la peculiarità della pittura di Gianfilippo Usellini. "
                        "Eliana Tovagliaro, restauratrice, ha illustrato la tecnica della sua pittura.\n\n"
                        "Federico Monti, sindaco di Arona, ha poi ricordato la figura di Usellini, grande amico di suo padre, tramite ricordi d'infanzia, "
                        "per poi dedicare uno spazio all'aggiornamento sullo stato dei lavori del Museo Fanny Usellini di prossima realizzazione in città "
                        "grazie alla donazione della collezione di Luigi Sansone. Hanno fatto seguito interventi di ex allievi, artisti, collezionisti, amici e familiari."
                    )
                elif post_id == 11:  # Concerto 28 luglio 2023
                    featured_image = "IMG-20230728-WA0005-scaled.jpg"
                    gallery_data = [
                        {"src": "IMG-20230728-WA0005-scaled.jpg", "title": "Simone Gramaglia e Martti Rousi in concerto", "alt": "Concerto Gramaglia Rousi"},
                        {"src": "IMG-20230728-WA0004-scaled.jpg", "title": "Scorcio del concerto a Casa Usellini", "alt": "Casa Usellini concerto"},
                        {"src": "IMG-20230728-WA0003-scaled.jpg", "title": "Il pubblico e gli artisti nel giardino", "alt": "Pubblico nel giardino"}
                    ]
                    body_md = (
                        "Serata musicale a Casa Usellini nell'ambito del Festival LagoMaggioreMusica:\n\n"
                        "- **Simone Gramaglia**, viola\n"
                        "- **Martti Rousi**, violoncello\n\n"
                        "### *“Racconti di musica in musica”*\n"
                        "Esecuzione di musiche di J.S. Bach, W.A. Mozart, A. Rolla, W. Lutoslawski e N. Paganini nella cornice del giardino interno."
                    )
                elif post_id == 7:  # Teatro sull'acqua 2021
                    featured_image = "palco-1024x768.jpg"
                    body_md = (
                        "Anche quest'anno Casa Usellini ospita alcuni eventi legati al Festival del Teatro Sull'Acqua di Arona, "
                        "nello specifico due spettacoli nel giardino interno:\n\n"
                        "- **Martedì 7 settembre (ore 20:00)**: andrà in scena *“Sulla morte senza esagerare”*.\n"
                        "- **Sabato 11 settembre (ore 20:00)**: spettacolo *“Tiresias”*, con **replica domenica 12 settembre** alla stessa ora.\n\n"
                        "Per maggiori dettagli e per prenotare i posti, consultare il sito ufficiale del [Teatro Sull'Acqua](http://teatrosullacqua.it)."
                    )
                elif post_id == 8:  # Festival 2022
                    featured_image = "concerto-scaled.webp"
                    body_md = (
                        "Siamo felici di ospitare anche quest'anno i consueti concerti estivi della Gioventù Musicale d'Italia a Casa Usellini. "
                        "Di seguito il calendario completo degli appuntamenti della stagione:\n\n"
                        "- **28 luglio (Inaugurazione del Festival)**:\n"
                        "  **Giuseppe Gibboni**, violino (I Premio Concorso Internazionale Paganini di Genova 2021) e **Carlotta Dalia**, chitarra.\n"
                        "  *Musiche di Paganini, Castelnuovo-Tedesco, Piazzolla.*\n\n"
                        "- **4 agosto**:\n"
                        "  **Claudia Lucia Lamanna**, arpa (I Premio International Harp Contest di Tel Aviv 2022).\n"
                        "  *Musiche di Ravin, Britten, Breschand, Lopez, Bach.*\n\n"
                        "- **11 agosto**:\n"
                        "  **Jae Hong Park**, pianoforte (I Premio Concorso Internazionale Busoni di Bolzano 2021).\n"
                        "  *Musiche di Schumann, Skrjabin, Franck.*\n\n"
                        "- **18 agosto**:\n"
                        "  **Trio Chagall**, violino, violoncello e pianoforte (Premio Trio di Trieste 2019).\n"
                        "  *Musiche di Haydn e Brahms.*"
                    )
                elif post_id == 9:  # Festival 2023
                    body_md = (
                        "Anche quest'anno abbiamo il piacere di ospitare i concerti in Casa Usellini per la 29ª edizione del Festival LagoMaggioreMusica. "
                        "Di seguito le date e il programma degli appuntamenti:\n\n"
                        "- **Venerdì 28 luglio, ore 21:00**:\n"
                        "  **Simone Gramaglia** (viola) e **Martti Rousi** (violoncello) in *“Racconti di musica in musica”*.\n"
                        "  *Musiche di Bach, Mozart, Rolla, Lutoslawski, Paganini.*\n\n"
                        "- **Venerdì 4 agosto, ore 21:00**:\n"
                        "  **Julian Kainrath** (violino) e **Luigi Carroccia** (pianoforte).\n"
                        "  *Musiche di Beethoven, Franck.*\n\n"
                        "- **Venerdì 11 agosto, ore 21:00**:\n"
                        "  **Quartetto Goldberg** (Jingzhi Zhang, Giacomo Lucato, Matilde Simionato, Martino Simionato).\n"
                        "  *Musiche di Haydn, Beethoven, Verdi.*\n\n"
                        "- **Venerdì 18 agosto, ore 21:00**:\n"
                        "  **Yukine Kuroki** (pianoforte - 1° Premio Franz Liszt Utrecht 2022).\n"
                        "  *Musiche di Liszt, Schubert/Liszt.*\n\n"
                        "> *Nota: In caso di pioggia i concerti si terranno presso la Chiesa di San Graziano ad Arona.*"
                    )
                elif post_id == 12:  # Restauro facciata
                    featured_image = "PXL_20231226_104444046-1024x769.jpg"
                    body_md = (
                        "Nel corso del 2023 è stato effettuato un importante intervento di restauro conservativo che ha riguardato "
                        "la facciata esterna su Via Pertossi e i lati est e ovest dell'edificio.\n\n"
                        "I lavori si sono protratti per alcuni mesi e sono stati condotti a seguito di una rigorosa indagine stratigrafica "
                        "a cura della ditta specializzata SM Munaro Restauri, restituendo luminosità e coerenza filologica ai prospetti storici."
                    )
                elif post_id == 13:  # Festival 2024
                    body_md = (
                        "Programma dei concerti estivi della 30ª edizione del Festival LagoMaggioreMusica a Casa Usellini:\n\n"
                        "- **2 agosto, ore 21:00**:\n"
                        "  **Michiaki Ueno** (violoncello) e **Ani Ter-Martirosyan** (pianoforte).\n"
                        "  *Musiche di Debussy, Beethoven, Clara Schumann, Brahms.*\n\n"
                        "- **9 agosto, ore 21:00**:\n"
                        "  **Guido Sant’Anna** (violino) e **Martina Consonni** (pianoforte).\n"
                        "  *Musiche di Brahms, Ravel, Frolov.*\n\n"
                        "- **16 agosto, ore 21:00**:\n"
                        "  **Arsenii Moon** (pianoforte - 1° Premio Concorso Busoni 2023).\n"
                        "  *Musiche di Bach-Busoni, Chopin, Rachmaninov, Ravel, Debussy, Musorgskij.*\n\n"
                        "[Scarica la locandina del Festival Lago Maggiore Musica 2024 (PDF)](https://palazzousellini.com/wp-content/uploads/2024/08/locandina-festival-Lago-Maggiore-Musica-2024.pdf)"
                    )
                elif post_id == 14:  # Eventi estate 2025
                    body_md = (
                        "Pubblicato l'elenco degli eventi culturali e dei concerti per la stagione estiva 2025 a Casa Usellini:\n\n"
                        "- **4 luglio, ore 18:00**: *Overture d’estate* – Marino Mora e Fabio Pollegioni.\n"
                        "- **25 luglio, ore 21:00**: Mariam Abouzahra (violino) e Nora Emödi (pianoforte).\n"
                        "- **1 agosto, ore 21:00**: Quartetto d’archi Opus13.\n"
                        "- **8 agosto, ore 21:00**: Maria Zaitseva (violoncello) e Maria Zaitseva Sr (pianoforte).\n"
                        "- **14 agosto, ore 21:00**: Dmytro Udovychenko (violino) e Milana Cherniavskaya (pianoforte).\n"
                        "- **22 agosto, ore 21:00**: Konstantin Emelyanov (pianoforte).\n"
                        "- **30 e 31 agosto, ore 20:30**: *“Usellini, il pittore dei sogni”* a cura di Arona Città Teatro."
                    )
                elif post_id == 15:  # Concerti 2026
                    body_md = (
                        "Come ogni anno siamo lieti di ospitare alcune delle date aronesi del Festival LagoMaggioreMusica "
                        "nella suggestiva cornice del nostro giardino:\n\n"
                        "- **7 agosto 2026**: Danilo Rossi (viola) e Trio Felice.\n"
                        "- **14 agosto 2026**: Aozhe Zang, violino (I Premio Paganini 2025).\n"
                        "- **21 agosto 2026**: Alexander Kashpurin, pianoforte (I Premio Liszt 2026).\n"
                        "- **28 agosto 2026**: Isidore String Quartet (I Premio Banff 2024)."
                    )
                elif post_id == 6:  # Festival 2020
                    body_md = (
                        "Anche quest'anno tornano i concerti della Gioventù Musicale d'Italia a Casa Usellini!\n\n"
                        "Per garantire il rispetto delle regole di distanziamento sociale vi sarà un doppio orario di esecuzione "
                        "(alle 19:30 e alle 21:00) ogni giovedì, a partire dal 6 fino al 27 agosto 2020.\n\n"
                        "[Scarica il calendario e programma dei concerti 2020 (PDF)](http://www.jeunesse.it/wp-content/uploads/2020/07/GMI-Calendario-cronologico-Festival-LagoMaggioreMusica-2020.pdf)"
                    )
            else:
                # Per le pagine normali (Home, Storia, Contatti, Galleria)
                if text.strip().startswith('['):
                    body_md, gallery_data = parse_publii_blocks(text)
                else:
                    body_md = clean_html_to_markdown(text)

                if available_images:
                    for img in available_images:
                        if 'gallery' not in img:
                            featured_image = img
                            break
                    if not featured_image:
                        featured_image = available_images[0]

            # Generazione sommario/descrizione pulito
            description = ""
            if is_page:
                if slug == 'home':
                    description = "Palazzo Usellini, dimora storica del '700 ad Arona sul Lago Maggiore. Sede di concerti estivi, eventi culturali e mostre d'arte."
                elif slug == 'storia':
                    description = "La storia di Palazzo Usellini ad Arona dal 1530 ai giorni nostri: Carlantonio Usellini, gli affreschi e la pittura di Gianfilippo Usellini."
                elif slug == 'galleria':
                    description = "Galleria fotografica di Palazzo Usellini: la facciata storica, il giardino interno, gli affreschi e le sale del palazzo ad Arona."
                elif slug == 'contatti':
                    description = "Contatti e recapiti di Palazzo Usellini in Via Pertossi 12 ad Arona (NO)."
            elif body_md:
                # Prende la prima frase del markdown senza caratteri speciali
                first_lines = [l for l in body_md.splitlines() if l.strip() and not l.startswith(('#', '!', '-', '['))]
                if first_lines:
                    first_sentence = first_lines[0].split('.')[0]
                    description = first_sentence.replace('**', '').replace('*', '').strip()
                    if len(description) > 160:
                        description = description[:157] + '...'

            # Assegnazione tag coerenti per le news
            tags = []
            if not is_page:
                title_lower = title.lower()
                if 'lagomaggioremusica' in title_lower or 'festival' in title_lower:
                    tags.extend(['Festival LagoMaggioreMusica', 'Concerti'])
                elif 'concerto' in title_lower:
                    tags.append('Concerti')
                elif 'teatro' in title_lower:
                    tags.extend(['Teatro', 'Festival Teatro sull\'Acqua'])
                elif 'usellini' in title_lower or 'catalogo' in title_lower:
                    tags.extend(['Arte', 'Gianfilippo Usellini'])
                elif 'restauro' in title_lower:
                    tags.append('Restauro')
                else:
                    tags.append('Eventi')

            # Costruzione Frontmatter omogeneo
            meta = {
                'title': title,
                'date': date_str,
                'slug': slug,
                'description': description,
                'draft': False
            }

            if featured_image:
                meta['featured_image'] = featured_image
            if tags:
                meta['tags'] = tags
            if gallery_data:
                meta['gallery'] = gallery_data

            # Se news section index
            if is_page and slug == 'news':
                meta['title'] = "News ed Eventi"
                meta['description'] = "Rassegna degli eventi culturali, concerti e aggiornamenti di Palazzo Usellini ad Arona."
                body_md = "Tutti gli eventi, i concerti estivi della Gioventù Musicale d'Italia e le novità di Casa Usellini."

            # Scrittura file Markdown finale
            target_md = os.path.join(bundle_dir, md_filename)
            frontmatter = format_yaml_frontmatter(meta)
            full_content = f"{frontmatter}\n\n{body_md}\n"

            with open(target_md, 'w', encoding='utf-8') as mf:
                mf.write(full_content)

            kind = "PAGINA" if is_page else "NEWS  "
            img_info = f"({len(available_images)} img)" if available_images else ""
            print(f"  [{kind}] {title:<45} -> {os.path.relpath(target_md, workspace_dir)} {img_info}")

        conn.close()

    print("[4/5] Creazione configurazione base Hugo (hugo.toml)...")
    hugo_toml_path = os.path.join(workspace_dir, 'hugo.toml')
    hugo_config = """baseURL = 'https://palazzousellini.com/'
languageCode = 'it-IT'
title = 'Palazzo Usellini'
paginate = 10

[params]
  description = 'Dimora storica ad Arona sul Lago Maggiore. Sede di concerti, eventi culturali e mostre.'
  author = 'Palazzo Usellini'
  email = 'info@palazzousellini.com'
  address = 'Via Pertossi 12, 28041 Arona (NO)'

[menu]
  [[menu.main]]
    name = 'Home'
    url = '/'
    weight = 1
  [[menu.main]]
    name = 'Storia'
    url = '/storia/'
    weight = 2
  [[menu.main]]
    name = 'Galleria'
    url = '/galleria/'
    weight = 3
  [[menu.main]]
    name = 'News'
    url = '/news/'
    weight = 4
  [[menu.main]]
    name = 'Contatti'
    url = '/contatti/'
    weight = 5

[imaging]
  resampleFilter = 'lanczos'
  quality = 85
"""
    with open(hugo_toml_path, 'w', encoding='utf-8') as hf:
        hf.write(hugo_config)

    print("[5/5] Migrazione completata con successo!")

if __name__ == '__main__':
    tar_file = sys.argv[1] if len(sys.argv) > 1 else '/var/home/andres/Downloads/palazzo-usellini-09-17-2026-20-05-49.tar'
    workspace = sys.argv[2] if len(sys.argv) > 2 else '/var/home/andres/Documents/palazzousellini'
    run_migration(tar_file, workspace)
