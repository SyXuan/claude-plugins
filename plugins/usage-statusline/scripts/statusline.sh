#!/usr/bin/env bash
# Claude Code status line: context window + auto-refreshed rate limit usage
# Part of claude-usage-statusline plugin

input=$(cat)

echo "$input" | _INPUT="$input" python - <<'PYEOF'
import json, sys, os, time, pathlib, urllib.request, urllib.error, threading

# Resolve Claude config directory (cross-platform)
claude_dir = pathlib.Path(os.environ.get('CLAUDE_CONFIG_DIR', pathlib.Path.home() / '.claude'))
creds_path = claude_dir / '.credentials.json'
cache_path = claude_dir / 'usage-cache.json'
REFRESH_SECS = 300  # 5 minutes

# Read JSON from stdin pipe (bash passes it via echo "$input" |)
raw = os.environ.get('_INPUT', '')
data = json.loads(raw) if raw.strip() else {}

model    = (data.get('model') or {}).get('display_name', 'Claude')
cwd      = ((data.get('workspace') or {}).get('current_dir') or data.get('cwd', ''))
dir_name = pathlib.Path(cwd).name or cwd
ctx      = data.get('context_window') or {}
used_pct = ctx.get('used_percentage')
total_in = int(ctx.get('total_input_tokens') or 0)
total_out = int(ctx.get('total_output_tokens') or 0)
cost_usd = (data.get('cost') or {}).get('total_cost_usd')

def fetch_usage():
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
        return cache
    except Exception:
        return None

# Load cache; refresh if stale
session_pct = None
weekly_pct  = None
cache = {}
if cache_path.exists():
    try:
        cache = json.loads(cache_path.read_text())
        session_pct = cache.get('session_pct')
        weekly_pct  = cache.get('weekly_pct')
    except Exception:
        pass

if (time.time() - cache.get('fetched_at', 0)) > REFRESH_SECS:
    t = threading.Thread(target=fetch_usage, daemon=True)
    t.start()
    t.join(timeout=4)
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text())
            session_pct = cache.get('session_pct')
            weekly_pct  = cache.get('weekly_pct')
        except Exception:
            pass

def make_bar(pct, width=8):
    if pct is None:
        return '[' + '-' * width + '] ?%'
    p = int(round(float(pct)))
    filled = max(0, min(width, p * width // 100))
    bar = '#' * filled + '-' * (width - filled)
    color = '\033[31m' if p >= 80 else '\033[33m' if p >= 60 else '\033[32m'
    return f'{color}[{bar}] {p}%\033[0m'

cost_info = f'  \033[33m${cost_usd:.2f}\033[0m' if cost_usd is not None else ''

print(
    f'\033[36m{dir_name}\033[0m \033[35m{model}\033[0m'
    f'  ctx:{make_bar(used_pct)}'
    f'  sess:{make_bar(session_pct)}'
    f'  week:{make_bar(weekly_pct)}'
    f'  \033[90min:{total_in:,} out:{total_out:,}\033[0m'
    f'{cost_info}'
)
PYEOF
