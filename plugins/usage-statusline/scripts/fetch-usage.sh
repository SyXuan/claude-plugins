#!/usr/bin/env bash
# Fetch Claude rate limit usage from API and update local cache
# Part of claude-usage-statusline plugin

python - <<'PYEOF'
import json, time, pathlib, os, urllib.request, urllib.error

claude_dir = pathlib.Path(os.environ.get('CLAUDE_CONFIG_DIR', pathlib.Path.home() / '.claude'))
creds_path = claude_dir / '.credentials.json'
cache_path = claude_dir / 'usage-cache.json'

try:
    with open(creds_path) as f:
        creds = json.load(f)
    token = creds['claudeAiOauth']['accessToken']

    req = urllib.request.Request(
        'https://api.anthropic.com/api/oauth/usage',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'claude-code',
            'anthropic-beta': 'oauth-2025-04-20'
        }
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        d = json.loads(resp.read())

    cache = {
        'session_pct':   d.get('five_hour', {}).get('utilization'),
        'weekly_pct':    d.get('seven_day', {}).get('utilization'),
        'session_reset': d.get('five_hour', {}).get('resets_at', ''),
        'weekly_reset':  d.get('seven_day', {}).get('resets_at', ''),
        'fetched_at':    time.time()
    }
    with open(cache_path, 'w') as f:
        json.dump(cache, f)

    print(f"session={cache['session_pct']}%  weekly={cache['weekly_pct']}%")

except FileNotFoundError:
    print("Error: credentials not found. Make sure you're logged in to Claude Code.")
except KeyError:
    print("Error: OAuth token not found in credentials. API key users are not supported.")
except Exception as e:
    print(f"Error: {e}")
PYEOF
