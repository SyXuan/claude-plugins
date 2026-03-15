---
name: setup
description: Configure Claude Code to display the usage statusline. Run this once after installing the plugin.
---

Run the setup script to configure the statusLine in `~/.claude/settings.json`:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh" "${CLAUDE_PLUGIN_ROOT}"
```

After running, tell the user:
1. The statusLine has been configured
2. They need to restart Claude Code for the change to take effect
3. The status bar will show: `dir  Model  ctx:[bar]%  sess:[bar]%  week:[bar]%  in:X out:X  $cost`
4. Data auto-refreshes every 5 minutes from the Anthropic API
