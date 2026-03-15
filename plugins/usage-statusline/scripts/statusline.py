#!/usr/bin/env python3
"""
Claude Code status line: context window + auto-refreshed rate limit usage.
Reads JSON from stdin (provided by Claude Code), prints a colored status line.
"""
import json, sys, os, time, pathlib, urllib.request, urllib.error, threading, tempfile

REFRESH_SECS = 300  # 5 minutes

claude_dir = pathlib.Path(os.environ.get('CLAUDE_CONFIG_DIR', pathlib.Path.home() / '.claude'))
creds_path = claude_dir / '.credentials.json'
cache_path = claude_dir / 'usage-cache.json'


def write_cache(data: dict) -> None:
    """Atomically write cache with owner-only permissions."""
    dir_path = cache_path.parent
    fd, tmp = tempfile.mkstemp(dir=dir_path, prefix='.usage-cache-')
    try:
        os.chmod(tmp, 0o600)
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f)
        pathlib.Path(tmp).replace(cache_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def read_cache() -> dict:
    try:
        return json.loads(cache_path.read_text())
    except Exception:
        return {}


def fetch_usage() -> None:
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
                'anthropic-beta': 'oauth-2025-04-20',
            }
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            d = json.loads(resp.read())
        write_cache({
            'session_pct':   d.get('five_hour', {}).get('utilization'),
            'weekly_pct':    d.get('seven_day', {}).get('utilization'),
            'session_reset': d.get('five_hour', {}).get('resets_at', ''),
            'weekly_reset':  d.get('seven_day', {}).get('resets_at', ''),
            'fetched_at':    time.time(),
        })
    except urllib.error.HTTPError as e:
        # Write sentinel so we don't hammer a 401/429 on every message
        write_cache({'error': e.code, 'fetched_at': time.time()})
    except Exception:
        pass  # network unavailable — keep showing stale data


def refresh_if_stale(cache: dict) -> dict:
    stale = (time.time() - cache.get('fetched_at', 0)) > REFRESH_SECS
    if not stale or cache.get('error') == 401:
        return cache
    t = threading.Thread(target=fetch_usage, daemon=True)
    t.start()
    t.join(timeout=4)
    return read_cache()


def make_bar(pct, width: int = 8) -> str:
    if pct is None:
        return '[' + '-' * width + '] ?%'
    p = int(round(float(pct)))
    filled = max(0, min(width, p * width // 100))
    bar = '#' * filled + '-' * (width - filled)
    color = '\033[31m' if p >= 80 else '\033[33m' if p >= 60 else '\033[32m'
    return f'{color}[{bar}] {p}%\033[0m'


def main() -> None:
    data = json.loads(sys.stdin.read() or '{}')

    model     = (data.get('model') or {}).get('display_name', 'Claude')
    cwd       = ((data.get('workspace') or {}).get('current_dir') or data.get('cwd', ''))
    dir_name  = pathlib.Path(cwd).name or cwd
    ctx       = data.get('context_window') or {}
    used_pct  = ctx.get('used_percentage')
    total_in  = int(ctx.get('total_input_tokens') or 0)
    total_out = int(ctx.get('total_output_tokens') or 0)
    cost_usd  = (data.get('cost') or {}).get('total_cost_usd')

    cache       = refresh_if_stale(read_cache())
    session_pct = cache.get('session_pct')
    weekly_pct  = cache.get('weekly_pct')

    cost_info = f'  \033[33m${cost_usd:.2f}\033[0m' if cost_usd is not None else ''

    print(
        f'\033[36m{dir_name}\033[0m \033[35m{model}\033[0m'
        f'  ctx:{make_bar(used_pct)}'
        f'  sess:{make_bar(session_pct)}'
        f'  week:{make_bar(weekly_pct)}'
        f'  \033[90min:{total_in:,} out:{total_out:,}\033[0m'
        f'{cost_info}'
    )


if __name__ == '__main__':
    main()
