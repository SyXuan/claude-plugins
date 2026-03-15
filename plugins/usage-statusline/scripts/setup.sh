#!/usr/bin/env bash
# Configure Claude Code to use the usage statusline
# Usage: bash setup.sh [--plugin-root <path> | <path>]

PLUGIN_ROOT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --plugin-root)
      PLUGIN_ROOT="$2"
      shift 2
      ;;
    *)
      PLUGIN_ROOT="$1"
      shift
      ;;
  esac
done
PLUGIN_ROOT="${PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

python "$PLUGIN_ROOT/scripts/setup.py" "$PLUGIN_ROOT"
