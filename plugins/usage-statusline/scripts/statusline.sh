#!/usr/bin/env bash
# Claude Code status line wrapper — delegates to statusline.py
exec python "$(dirname "$0")/statusline.py"
