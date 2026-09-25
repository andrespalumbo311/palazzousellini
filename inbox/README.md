# 📥 Palazzo Usellini Inbox

This folder serves as your **temporary upload drop zone**.

### How it works:
1. Drop or copy any raw files related to an upcoming event or news into this folder:
   - Text drafts (notes `.txt`, Word documents `.docx`, press releases, concert schedules)
   - Images and photography (posters `.png`, artist headshots `.jpg`, courtyard and garden photos)
2. Ask Antigravity: *"Create an article using the files in inbox"* (you can also provide additional notes such as custom title or date).
3. The assistant will:
   - Analyze the files in this folder
   - Generate the new article in `content/news/<slug>/index.md` with standardized frontmatter and clean Markdown
   - Move the required images directly into the article's Page Bundle
   - **Automatically delete the temporary source files from this `inbox/` folder**, keeping it clean and ready for the next event.

### 🗓️ Automatic Homepage Calendar Integration
Whenever an uploaded draft or press release contains specific concert dates or season itineraries, the assistant automatically populates the `events:` frontmatter list in the article. These events are immediately picked up by the homepage calendar, displaying date badges, time, performer names, and automatically retiring past events on a daily basis.

### ✍️ Editorial Guidelines for Agents
- **Authentic Naming**: Use **Casa Usellini** for hosted events and garden concerts; use **Palazzo Usellini** for the global historical monument.
- **Host Demarcation**: Casa Usellini solely **hosts** events (*"Casa Usellini ospita..."*). Do not frame the property as organizer or co-organizer.
- **Dry & Factual Tone**: Keep copy concise and strictly informative (date, time, performers, practical info). Avoid marketing rhetoric or lyrical flourishes.
- **Content Scope**: Communication focuses exclusively on the venue and the hosted cultural and artistic programme.
- **Phone Formatting**: Write telephone numbers as plain text (e.g. `Tel. 342.0057160`), never as Markdown `[num](tel:...)` links to prevent template engine sanitization (`#ZgotmplZ`).
