# claude-plugins

Personal Claude Code plugin marketplace by [BingSyuan](https://github.com/SyXuan).

## Add this marketplace

**Step 1** — Register the marketplace (once per machine):

```
/plugin marketplace add SyXuan/claude-plugins
```

Or manually add to `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "SyXuan": {
      "source": {
        "source": "github",
        "repo": "SyXuan/claude-plugins"
      }
    }
  }
}
```

**Step 2** — Install a plugin:

```
/plugin install <name>@SyXuan
```

## Available Plugins

### `usage-statusline`

Displays real-time usage in Claude Code status bar:

![screenshot](plugins/usage-statusline/screenshot.png)

```
ClaudeCode  Sonnet 4.6  ctx:[###-----] 38%  sess:[##------] 25%  week:[--------] 4%  in:45,231 out:12,048  $1.23
```

| Field | Description |
|-------|-------------|
| `ctx` | Context window usage (current conversation) |
| `sess` | Session rate limit (~5 hr window) |
| `week` | Weekly rate limit |
| `in/out` | Cumulative token counts |
| `$cost` | Estimated session cost |

**Install:**
```
/plugin install usage-statusline@SyXuan
/claude-usage-statusline:setup
```

**Requirements:** Claude Code with claude.ai subscription (OAuth login), Python 3.x

### `wp-publish`

Turns any content source into a **draft** post on your WordPress site via the REST API. Just describe what you want in a Claude Code session:

- `Publish this docx as a blog draft: ~/Documents/article.docx`
- `Turn this markdown file into a WordPress draft`
- `Write a blog post about <topic> and put it on my site as a draft`

Handles it end to end: first-time credential setup (creates/uses an Application Password, stored per-site under `~/.config/wp-publish/`), any source format (Word/PDF/Markdown/folder/dictated/agent-written), image upload with featured-image selection, category selection, matching your site's existing style, and image-generation prompts for AI-written articles. Always creates drafts — never publishes directly — and gives you the wp-admin edit link.

No pre-installed tools required beyond `curl` (ships with Windows 10+/macOS/Linux); uses `pandoc` or Docker for docx if available, with built-in fallbacks.

**Install:**
```
/plugin install wp-publish@SyXuan
```

**Requirements:** WordPress 5.6+ over HTTPS, an account with at least the Author role (the skill walks you through creating an Application Password).
