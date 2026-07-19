---
name: wp-publish
description: Use when the user wants to publish, draft, or post an article or blog post to a WordPress site — from a Word docx, PDF, Markdown file, a folder of content, dictated title and text, or a topic the agent should write about. Also use for uploading images to WordPress media, or setting up / troubleshooting WordPress publishing credentials (401/403 errors, application passwords).
---

# WordPress Publishing

## Overview

Guide the user from any content source to a **draft** post on their WordPress site, using the WordPress REST API with an Application Password. The agent adapts to whatever tools exist on the machine — nothing needs to be pre-installed beyond `curl` (bundled with Windows 10+, macOS, and Linux).

**Hard rules — no exceptions:**
- ALWAYS create posts with `"status": "draft"`. Never publish directly, even if asked mid-flow; tell the user to publish from wp-admin after review. **Single exception:** the user has already reviewed the draft and tried to publish it themselves but wp-admin is blocked (e.g. Cloudflare WAF, see Common mistakes) — then, at their request, flip only the status: `POST /wp-json/wp/v2/posts/{id}` with body `{"status":"publish"}` and nothing else.
- NEVER modify or delete existing posts/media unless the user explicitly asks for that specific post.
- NEVER write credentials anywhere except the profile files under `~/.config/wp-publish/`. Never echo the application password back to the user or into logs/commits.

## Workflow

Follow these steps in order. Announce progress briefly at each step.

### 1. Credentials

Profiles live in `~/.config/wp-publish/profiles/*.json` (Windows: `%USERPROFILE%\.config\wp-publish\profiles\`), one file per account; `~/.config/wp-publish/config.json` holds `{"default_profile": "<name>"}`.

- **No profiles** (or a chosen profile is malformed / fails verification) → run first-time setup: see [references/setup.md](references/setup.md). Walk the user through it — do not just error out.
- **Exactly one profile** → confirm with the user: use this account (name it explicitly, e.g. "myblog @ https://example.com") or set up a different one? Don't use it silently.
- **Multiple profiles** → ask which to use, preselecting `default_profile`. When confirming, name each profile's full `site_url` and flag which are production (https, public host) vs local/staging, so the user never publishes to the wrong site by accepting a default.
- In both cases, always offer **"set up a new account"** as an option — including creating a brand-new dedicated publishing user on the site (setup.md covers that path).
- Verify the chosen profile silently with `GET /wp-json/wp/v2/users/me` (see [references/rest-api.md](references/rest-api.md)). On 401/403, consult the troubleshooting table in setup.md before asking the user anything.
- **Site memory**: once a profile is chosen, read `~/.config/wp-publish/notes/<profile>.md` if it exists — see [references/site-notes.md](references/site-notes.md). Apply its **Preferences** as binding and its **Observed conventions** as hints. Absent = no memory yet.
- **Legacy config**: if `config.json` itself contains credentials (old single-account format), migrate it to `profiles/<username>.json` first.

### 1b. Check how the theme renders the body

Most themes render the post body from the standard `content` field — the normal case. Some custom themes render it from custom fields instead, and publishing into `content` then produces a broken page. Check before composing: fetch `GET /wp-json/wp/v2/posts?per_page=1` and inspect it.

- **`content.rendered` carries the full article body** → standard theme; use `content` normally. This is the common case.
- **`content.rendered` is empty or suspiciously short** (e.g. a one-line byline) while the real body clearly lives elsewhere, or the response carries unfamiliar custom-field objects that hold the body → the theme uses custom fields. Stop; ask the user which field(s) hold the body (or inspect a fully-populated existing post), and note that custom fields usually need a small REST bridge to be writable. Don't stuff the article into `content`.
- If the site's memory file (step 1, [references/site-notes.md](references/site-notes.md)) already records a confirmed `## Layout` mapping, use it and skip the investigation — but still do one live GET to sanity-check it hasn't changed.

### 2. Content source

If not obvious from the user's request, ask which of these they have:

| Source | Approach |
|---|---|
| Word (.docx) | Convert to HTML — see [references/conversion.md](references/conversion.md) |
| PDF | Read it directly with the Read tool, reconstruct as HTML — see conversion.md |
| Markdown (.md) | Convert to HTML yourself (headings, lists, links, code blocks) |
| Folder | List files, identify the document + images, confirm the mapping with the user |
| Dictated | User gives title + content in chat; format as clean HTML |
| "Write it for me" | Run the interview protocol below BEFORE writing anything |

### 3. Match the site's style

Fetch recent posts (public, no auth): `GET /wp-json/wp/v2/posts?per_page=3`. Skim `content.rendered` for conventions — heading levels used, how image captions are formatted, intro/outro patterns, typical length. Make the new post consistent with them. If recent posts show no clear conventions (new or sparse site), default to clean semantic HTML: `<h2>` sections, `<figure>/<figcaption>` for captioned images.

Combine this with the site memory loaded in step 1: the user's saved **Preferences** win over everything; live observation here is the current truth for style and supersedes stale "Observed conventions" notes.

### 4. Category

`GET /wp-json/wp/v2/categories?per_page=100` and present the existing category names for the user to pick. If the user delegates ("you pick"), choose the best fit and disclose the choice in the step-6 summary. An Author-role account **cannot create** new categories or tags — only assign existing ones. If the user wants a new category, tell them to create it in wp-admin first (or use an Editor account).

### 5. Images

- Extract/collect images from the source. Upload each via `POST /wp-json/wp/v2/media` and replace local references in the HTML with the returned `source_url`.
- Strip Word's inch-based inline sizing (`style="width:...in"`); let the theme size images.
- Multiple images → ask the user which one should be the featured image (describe each by filename/caption/position). Exactly one image → propose it as featured inside the step-6 summary instead of asking separately. No images → skip featured image; offer to proceed without.

### 6. Confirm summary

Before creating the draft, show a one-screen summary: title, category, excerpt, word count, number of images, featured image choice. Write a one-sentence excerpt yourself if the source doesn't provide one. **Explicitly flag any choice that came from the saved site memory** (e.g. "category Educational and Title Case headings — from saved site preferences"), so the user can veto a remembered default rather than have it applied silently. One confirmation is enough — the post is only a draft. (Agent-written articles additionally get outline + full-text review in the interview protocol; converted documents do not need a full-text preview unless the user asks.)

### 7. Create the draft

`POST /wp-json/wp/v2/posts` with `status: "draft"`. Then give the user:
- Edit link: `{site_url}/wp-admin/post.php?post={id}&action=edit`
- Reminder: review in wp-admin, then press Publish there.
- Note: opening that link requires a wp-admin login that can see the draft — the publishing account itself, or any Editor/Administrator. (Another Author's login cannot see this account's drafts.)

### 8. Update site memory

After the draft is created, record durable, site-specific learnings into `~/.config/wp-publish/notes/<profile>.md` so the next post reuses them — see [references/site-notes.md](references/site-notes.md). Read the existing file first and merge; if it already covers everything, leave it unchanged. Save any explicit preference or correction the user gave this session, stable conventions you confirmed, the category name→ID map, and any confirmed custom-field layout mapping. Do NOT save per-post specifics or the article content. Tell the user in one line whether you updated the notes or they were already current.

## Interview protocol ("write it for me")

Never start writing from just a topic. First ask (one round, 2-4 questions max):
1. **Audience and goal** — who reads this, and what should they take away?
2. **Key points or source material** — links, papers, data, personal notes; anything the article must contain.
3. **Length and tone** — if unknown, propose based on the site's recent posts.

Then: propose a short **outline** (headings + one line each) → iterate until the user approves → write the full draft → show the full text for review → only then continue with steps 4-7 above. Outline-first prevents discovering a wrong direction after 2000 words.

### Images for agent-written articles

After the draft is approved, ask whether the article should have images. If yes, and the user has no photos of their own:

1. Propose where images belong (featured image + key sections), one line each on what the image should show.
2. For each spot, write a ready-to-paste **image generation prompt** the user can run in their preferred image AI (ChatGPT, Gemini, Grok, Meta AI, Midjourney, …). Prompt rules:
   - Subject + setting + style + composition in one paragraph; keep style consistent across all prompts in the article
   - Suggest aspect ratio (16:9 for featured/hero, 4:3 or 1:1 inline)
   - If the image should contain text (labels, diagram captions, signage), spell out the exact wording in quotes in the prompt — modern image models render text reliably
   - No real brand logos or real people's likenesses
3. Wait for the user to come back with the generated files, then continue with step 5 (upload, captions, featured pick). Proceeding without images is equally fine — never block on this.

## Common mistakes

| Symptom | Cause / fix |
|---|---|
| 403 + `Cf-Mitigated: challenge` header | Cloudflare bot protection, not WordPress. See setup.md → Cloudflare section |
| wp-admin Publish/Update shows Cloudflare "Sorry, you have been blocked" | WAF false positive: the editor form-POSTs the whole article to `post.php`, and something in the text matches a SQLi/XSS signature. The same content passes as REST JSON. Workaround: publish via status-only REST update (see hard-rules exception). Permanent fix: Cloudflare dashboard → Security → Events, find the event by Ray ID, add a WAF exception for the fired rule scoped to `/wp-admin/*` + the editor's IP |
| 401 with correct credentials | Authorization header stripped by server, or app password revoked. See setup.md |
| Post invisible on the site | It's a draft — that's by design. Check wp-admin → Posts |
| Garbled non-ASCII text | Missing `charset=utf-8`, or a script encoding issue — see rest-api.md encoding note |
| Media upload rejected | Missing `Content-Disposition: attachment; filename="..."` header |
| New category silently failed | Author role can't create terms — pick an existing one |
| Curl works but PowerShell `curl` fails | In Windows PowerShell, `curl` aliases Invoke-WebRequest; call `curl.exe` explicitly |
