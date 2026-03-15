#!/usr/bin/env python3
"""
Fetch Claude rate limit usage from the Anthropic API and update local cache.
Standalone utility; also imported by statusline.py.
"""
import json, time, pathlib, os, urllib.request, urllib.error, tempfile

claude_dir = pathlib.Path(os.environ.get('CLAUDE_CONFIG_DIR', pathlib.Path.home() / '.claude'))
creds_path = claude_dir / '.credentials.json'
cache_path = claude_dir / 'usage-cache.json'


def write_cache(data: dict) -> None:
    """Atomically write cache with owner-only permissions."""
    fd, tmp = tempfile.mkstemp(dir=claude_dir, prefix='.usage-cache-')
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


def fetch() -> dict:
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
        return json.loads(resp.read())


def main() -> None:
    try:
        d = fetch()
        cache = {
            'session_pct':   d.get('five_hour', {}).get('utilization'),
            'weekly_pct':    d.get('seven_day', {}).get('utilization'),
            'session_reset': d.get('five_hour', {}).get('resets_at', ''),
            'weekly_reset':  d.get('seven_day', {}).get('resets_at', ''),
            'fetched_at':    time.time(),
        }
        write_cache(cache)
        print(f"session={cache['session_pct']}%  weekly={cache['weekly_pct']}%")

    except FileNotFoundError:
        print("Error: credentials not found. Make sure you are logged in to Claude Code.")
    except KeyError:
        print("Error: OAuth token not found. API key users are not supported.")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("Error: OAuth token expired or invalid (401). Re-authenticate with Claude Code.")
            write_cache({'error': 401, 'fetched_at': time.time()})
        elif e.code == 429:
            print("Error: Rate limited by API (429). Retry later.")
        else:
            print(f"Error: HTTP {e.code}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
