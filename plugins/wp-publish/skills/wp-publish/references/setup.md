# First-Time Setup

Walk the user through this conversationally — one step at a time, confirming each before moving on.

## 1. Collect three values

| Value | How to guide the user |
|---|---|
| **Site URL** | Ask for the WordPress site URL (e.g. `https://example.com`). Any WordPress 5.6+ site works. Strip trailing slash. If the user enters an `http://` URL, warn immediately: WordPress disables Application Passwords over plain HTTP unless the site sets `WP_ENVIRONMENT_TYPE=local` — expect auth to fail on a production site without HTTPS. |
| **Username** | Recommend a dedicated low-privilege account (Author role), not an admin — a leaked publishing credential then can't control the whole site. Offer: **(a)** use an existing account — they type the username; **(b)** create a brand-new dedicated publishing user — walk them through "Creating a dedicated publishing user" below. |
| **Application Password** | If they already have one, they can paste it directly. Otherwise guide them through creating one (below). |

### Creating a dedicated publishing user (user does this in the browser; needs an admin account)

1. Log in to `{site_url}/wp-admin` with an administrator account
2. **Users → Add New User**: pick a username (e.g. `blog-bot` or `claude-publisher`), any valid email
3. **Role: Author** (recommended) — can publish its own posts and upload media, nothing more. Choose Editor only if the account must manage other people's posts or create categories/tags. Never Administrator.
4. Set a strong main password — it will never be used again (all access goes through application passwords), so a long random one is fine
5. Continue to "Creating an Application Password" below for this new user

### Creating an Application Password (user does this in the browser)

1. Log in to `{site_url}/wp-admin` as the publishing account
2. **Users → Profile** → scroll to **Application Passwords**
3. Enter a name — e.g. `claude-code` (or `claude-code-<machine>` if you use several machines, so each is individually revocable)
4. Click **Add New Application Password** and copy the result — **it is shown only once**. Spaces in it don't matter (works with or without).

One account can hold many application passwords; revoke any one without affecting the others.

If the Application Passwords section is missing: the site is either not HTTPS, or a security plugin disabled the feature — an admin needs to resolve that first.

## 2. Verify before saving

This is the ONLY moment the raw password may appear in a command — everything afterwards uses the stored `auth_b64`.

```bash
# tr -d '\n' handles GNU base64's 76-char line wrapping (BSD/macOS base64 doesn't wrap)
AUTH=$(printf '%s' "USERNAME:APP_PASSWORD" | base64 | tr -d '\n')
curl -s -H "Authorization: Basic $AUTH" "SITE_URL/wp-json/wp/v2/users/me?context=edit"
```

```powershell
# PowerShell equivalent
$AUTH = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("USERNAME:APP_PASSWORD"))
Invoke-RestMethod -Uri "SITE_URL/wp-json/wp/v2/users/me?context=edit" -Headers @{ Authorization = "Basic $AUTH" }
```

Expect HTTP 200 with the user's `slug` and `roles`. Report the role to the user and note its limits (Author: can publish own posts and upload media; cannot create categories/tags).

If the role is `administrator`: warn that publishing should use a low-privilege account (a leaked credential would then control the whole site) and offer to set one up via "Creating a dedicated publishing user" above — but proceed if the user explicitly chooses to.

## 3. Save the profile

Write `~/.config/wp-publish/profiles/<name>.json` (create directories if needed). Profile name defaults to the username; if that name is taken (e.g. same username on a second site), ask for a label like `myblog-staging`.

```json
{
  "site_url": "https://example.com",
  "username": "your-user",
  "auth_b64": "<the base64 AUTH value computed in step 2>"
}
```

Do not store the raw password — `auth_b64` is all requests need (it's reversible base64 of `username:password`, so the file is still a secret; it just never has to appear on a command line again).

If this is the first/only profile, also write `~/.config/wp-publish/config.json`:

```json
{ "default_profile": "your-user" }
```

When adding an additional profile, ask whether it should become the default.

On macOS/Linux, `chmod 600` the files. On Windows no action is needed — `%USERPROFILE%` is already ACL-protected per user. Never commit these files, never copy them into a project directory.

Setup is done — return to step 2 of the main workflow (SKILL.md) and continue publishing.

## Troubleshooting

### 403 on every request, response header `Cf-Mitigated: challenge`

The site is behind Cloudflare, which is challenging non-browser clients before the request ever reaches WordPress. Diagnose in the Cloudflare dashboard: **Security → Events**, filter by your public IP or the `CF-RAY` value from the response header — the event names the exact feature responsible.

- If it's **(Super) Bot Fight Mode** ("Bot Fight Mode for Definite Bots"): on Free/Pro plans this CANNOT be bypassed with WAF custom rules (Enterprise-only). Fix: **Security → Bots** → set **"Definitely automated"** to **Allow**. Write operations are still protected by the application password.
- If it's a WAF custom rule or Security Level: add a Skip rule for `URI Path starts with /wp-json/` scoped to your IP or a secret header.
- Changes take effect within seconds — retry immediately.

### Browser blocked in wp-admin: "Sorry, you have been blocked" when pressing Publish/Update

This is a WAF **managed-rule** false positive, distinct from bot protection: the classic editor form-POSTs the entire article body to `/wp-admin/post.php`, and a phrase in the text matches a SQLi/XSS signature. The identical content usually passes as REST JSON — so drafts created by this skill save fine, and a status-only REST update (`{"status":"publish"}`) publishes fine.

Permanent fix in the Cloudflare dashboard:
1. **Security → Events** — locate the block by the Ray ID shown at the bottom of the block page. The event names the exact managed rule that fired.
2. **Security → WAF → Managed rules → Add exception** — skip that specific rule (not the whole ruleset) scoped to `URI Path starts with /wp-admin/` **and** the editor's IP. Never skip WAF on `/wp-admin/` for all visitors.
3. If the block recurs with a different rule ID on other articles, widen the exception to the managed ruleset for `/wp-admin/post.php` + trusted IPs only.

### 401 with correct credentials

- The `Authorization` header may be stripped by Apache/FastCGI. Fix in the site's `.htaccess`, near the top of the WordPress block:
  `RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]`
- The application password may have been revoked — check wp-admin → Users → Profile → Application Passwords.
- Application Passwords are disabled over plain HTTP unless `WP_ENVIRONMENT_TYPE` is `local`.

### `/wp-json/` returns 404

Pretty permalinks are disabled or `.htaccess` rewrites are missing. Fallback that always works: replace `/wp-json/` with `/?rest_route=/` (e.g. `/?rest_route=/wp/v2/posts`).

### REST API blocked entirely (403 from WordPress itself, no `Cf-Mitigated`)

A security plugin (Wordfence, iThemes, etc.) is restricting the REST API — an admin needs to allow authenticated REST access.
