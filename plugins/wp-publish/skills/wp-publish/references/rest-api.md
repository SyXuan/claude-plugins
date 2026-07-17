# WordPress REST API Quick Reference

All examples use `curl` (bundled with Windows 10+, macOS, Linux). In Windows PowerShell call `curl.exe` explicitly — bare `curl` aliases `Invoke-WebRequest` there. Load `site_url` and `auth_b64` from the active profile: `~/.config/wp-publish/profiles/<name>.json` (see setup.md for profile selection).

## Authentication

HTTP Basic Auth. The config file stores a precomputed `auth_b64` value (created during setup) so the password never appears on a command line or in session logs. Extract it without printing the secret:

```bash
# bash — sed extraction, no jq required (PROFILE = active profile name)
AUTH=$(sed -n 's/.*"auth_b64"[^"]*"\([^"]*\)".*/\1/p' ~/.config/wp-publish/profiles/$PROFILE.json)
# then on every request:
-H "Authorization: Basic $AUTH"
```

```powershell
# PowerShell
$AUTH = (Get-Content "$env:USERPROFILE\.config\wp-publish\profiles\$PROFILE.json" | ConvertFrom-Json).auth_b64
```

If the config predates `auth_b64` (only has `app_password`), regenerate it per setup.md step 3 — do not inline the password into a command.

Verify credentials (expect 200 + JSON with `slug` and `roles`):

```bash
curl -s -H "Authorization: Basic $AUTH" "$SITE/wp-json/wp/v2/users/me?context=edit"
```

## Endpoints

| Action | Request |
|---|---|
| Recent posts (public, for style reference) | `GET /wp-json/wp/v2/posts?per_page=3` |
| List categories | `GET /wp-json/wp/v2/categories?per_page=100` |
| List tags | `GET /wp-json/wp/v2/tags?per_page=100` |
| Create draft | `POST /wp-json/wp/v2/posts` |
| Update post | `POST /wp-json/wp/v2/posts/{id}` |
| Upload media | `POST /wp-json/wp/v2/media` |
| List own drafts | `GET /wp-json/wp/v2/posts?status=draft` (auth required) |

## Create a draft

Write the payload to a file first (avoids shell-quoting issues with HTML content):

```bash
cat > /tmp/post.json << 'EOF'
{
  "title": "Post Title",
  "content": "<p>HTML content…</p>",
  "status": "draft",
  "excerpt": "One-sentence summary.",
  "categories": [12],
  "featured_media": 345
}
EOF

curl -s -X POST "$SITE/wp-json/wp/v2/posts" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @/tmp/post.json
```

```powershell
# PowerShell equivalent (write post.json with the Write tool first)
Invoke-RestMethod -Uri "$SITE/wp-json/wp/v2/posts" -Method Post `
  -Headers @{ Authorization = "Basic $AUTH" } `
  -ContentType "application/json; charset=utf-8" `
  -Body (Get-Content post.json -Raw -Encoding utf8)
```

The response's `id` gives the edit link: `$SITE/wp-admin/post.php?post={id}&action=edit`

Notes:
- **Encoding**: always send the body as UTF-8 and prefer HTML entities (`&#8212;`, `&#8217;`) over literal non-ASCII in any script you author — Windows PowerShell 5.1 reads a UTF-8 script file as ANSI and silently corrupts em-dashes/smart quotes/CJK before they ever reach the API. Writing the JSON to a file (UTF-8) and sending it with `curl --data-binary @file` sidesteps this entirely; if you must use Invoke-RestMethod, pass `[Text.Encoding]::UTF8.GetBytes($json)` as the body, not the string. Verify with a `curl.exe` read-back, not the PowerShell console (which re-decodes and hides the truth).
- `status` must be `draft` (this skill never publishes directly).
- `categories` / `tags` take arrays of **numeric IDs** — resolve names via the list endpoints.
- `content` accepts plain HTML; WordPress renders it as a classic block. Gutenberg block markup also works but is not required.
- Always `charset=utf-8` — required for non-ASCII content.

## Upload media

```bash
curl -s -X POST "$SITE/wp-json/wp/v2/media" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Disposition: attachment; filename=\"cover.jpg\"" \
  -H "Content-Type: image/jpeg" \
  --data-binary @cover.jpg
```

Response contains `id` (use for `featured_media`) and `source_url` (use to rewrite `<img src>` in the post HTML). The `Content-Disposition` header is mandatory. Use a descriptive ASCII filename — it becomes the attachment slug.

## Role capabilities cheat sheet

| Role | Publish own posts | Upload media | Create categories/tags | Edit others' posts |
|---|---|---|---|---|
| Author | ✅ | ✅ | ❌ (assign existing only) | ❌ |
| Editor | ✅ | ✅ | ✅ | ✅ |

Check the account's role in the `users/me` response before promising the user a capability.
