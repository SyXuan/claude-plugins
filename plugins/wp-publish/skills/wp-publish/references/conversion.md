# Converting Source Documents to Post HTML

Target output: clean semantic HTML — `<h2>/<h3>` for sections, `<p>` for text, `<em>` paragraphs or `<figure>` for captions, `<img>` with placeholder srcs to be rewritten after media upload. No inline styles, no fixed image sizes.

## Word (.docx)

Try in this order — use the first available option, never ask the user to install anything until all fallbacks are exhausted:

1. **pandoc installed?** (`pandoc --version`)
   ```bash
   pandoc input.docx -t html -o post.html --extract-media=media
   ```
2. **Docker available?** (`docker --version`)
   ```bash
   docker run --rm -v "$PWD:/data" pandoc/core:latest input.docx -t html -o post.html --extract-media=media
   ```
3. **No tools at all** — a .docx is a ZIP archive. Extract it yourself:
   ```bash
   mkdir -p unpacked && cd unpacked && tar -xf ../input.docx
   ```
   `tar` reads zip archives on Windows 10+ and macOS (bsdtar). On Linux, GNU `tar` does NOT read zip — use `unzip ../input.docx`, or `python3 -m zipfile -e ../input.docx .` if unzip is missing.
   - Text: `word/document.xml` — each `<w:p>` is a paragraph, `<w:t>` holds text runs. Heading styles appear as `<w:pStyle w:val="Heading1"/>` etc. Read it and reconstruct the HTML manually.
   - Images: `word/media/*` — in document order, cross-referenced via `word/_rels/document.xml.rels`.

**Pitfall:** if the document uses bold text instead of real Heading styles for section titles, every converter emits plain `<p>`. Detect heading-like short bold paragraphs and promote them to `<h2>`, confirming with the user if ambiguous.

**Title:** usually the document's first paragraph. Lift it out — it becomes the post title, not part of the content.

## PDF

Do NOT machine-convert PDF to HTML — layout formats convert badly (broken paragraphs, lost heading hierarchy, scrambled columns). Instead:

1. Read the PDF directly with the **Read tool** (it renders PDFs natively) and re-author the content as clean HTML yourself.
2. Images: extract with `pdfimages -all input.pdf img` if poppler is available; otherwise ask the user to provide the original image files (quality will be better anyway).
3. If the source also exists as .docx or .md, always prefer that over the PDF.

## Markdown (.md)

Convert directly yourself — no tools needed. Rules: `#` heading becomes the post title; `##`→`<h2>`, `###`→`<h3>`; fenced code → `<pre><code>`; images `![alt](path)` → upload the local file, then `<img src="{source_url}" alt="alt">`. An emphasized line (`*...*`) immediately after an image is a caption — render both as `<figure><img …><figcaption>…</figcaption></figure>`. Preserve link targets exactly.

## Folder

1. List the folder. Identify: exactly one document (.docx/.md/.pdf) and any loose images.
2. Confirm the mapping with the user: which file is the article, whether loose images should be inserted (and where) or only offered as featured-image candidates.
3. Proceed with the matching converter above.

## After any conversion — checklist

- [ ] Title extracted and removed from body
- [ ] Section headings are `<h2>/<h3>`, not bold paragraphs
- [ ] All `<img src>` rewritten to uploaded `source_url`s (zero local paths left)
- [ ] Word inch-based `style="width:…in"` attributes stripped
- [ ] Non-ASCII characters intact (UTF-8 end to end)
