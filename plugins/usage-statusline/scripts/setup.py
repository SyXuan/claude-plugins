#!/usr/bin/env python3
"""
One-time setup: configure Claude Code settings.json to use the usage statusline.
"""
import json, sys, pathlib, os, tempfile

plugin_root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).parent.parent)
statusline_cmd = f'bash "{plugin_root}/scripts/statusline.sh"'

claude_dir = pathlib.Path(os.environ.get('CLAUDE_CONFIG_DIR', pathlib.Path.home() / '.claude'))
settings_path = claude_dir / 'settings.json'
cache_path = claude_dir / 'usage-cache.json'


def write_json(path: pathlib.Path, data: dict) -> None:
    """Atomically write JSON with owner-only permissions."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f'.{path.name}-')
    try:
        os.chmod(tmp, 0o600)
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2)
        pathlib.Path(tmp).replace(path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# Create usage cache if missing
if not cache_path.exists():
    write_json(cache_path, {'fetched_at': 0})

# Load existing settings
settings = {}
if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text())
    except Exception:
        pass

# Warn if overwriting an existing statusLine config
existing = (settings.get('statusLine') or {}).get('command', '')
if existing and existing != statusline_cmd:
    print(f"WARNING: Overwriting existing statusLine config:")
    print(f"  old: {existing}")
    print(f"  new: {statusline_cmd}")
    print()

settings['statusLine'] = {'type': 'command', 'command': statusline_cmd}
write_json(settings_path, settings)

print(f"[OK] statusLine configured in {settings_path}")
print(f"     command: {statusline_cmd}")
print()
print("Restart Claude Code to apply the change.")
