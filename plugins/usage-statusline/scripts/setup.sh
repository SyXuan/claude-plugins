#!/usr/bin/env bash
# Configure Claude Code to use the usage statusline
# Part of claude-usage-statusline plugin
#
# Usage: bash setup.sh [--plugin-root <path>]

PLUGIN_ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
STATUSLINE_CMD="bash \"${PLUGIN_ROOT}/scripts/statusline.sh\""

python - "$PLUGIN_ROOT" "$STATUSLINE_CMD" <<'PYEOF'
import json, sys, pathlib, os

plugin_root = sys.argv[1]
statusline_cmd = sys.argv[2]

claude_dir = pathlib.Path(os.environ.get('CLAUDE_CONFIG_DIR', pathlib.Path.home() / '.claude'))
settings_path = claude_dir / 'settings.json'
cache_path = claude_dir / 'usage-cache.json'

# Create usage cache if missing
if not cache_path.exists():
    cache_path.write_text('{"fetched_at": 0}')

# Update settings.json
settings = {}
if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text())
    except Exception:
        pass

settings['statusLine'] = {
    'type': 'command',
    'command': statusline_cmd
}

settings_path.write_text(json.dumps(settings, indent=2))
print(f"✓ statusLine configured in {settings_path}")
print(f"  command: {statusline_cmd}")
print()
print("Restart Claude Code to apply the change.")
PYEOF
