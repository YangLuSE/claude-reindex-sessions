# claude-reindex-sessions

A small personal Claude Code plugin marketplace.

## Install

In Claude Code:

```
/plugin marketplace add YangLuSE/claude-reindex-sessions
/plugin install reindex-claude-sessions
```

## Plugins

- [`reindex-claude-sessions`](plugins/reindex-claude-sessions/README.md) —
  Two utilities for local Claude Code conversation data:
  - **reindex** — rebuild Claude Desktop's session/history index after a
    system reinstall, when old conversations stop showing up in the
    sidebar even though the raw transcripts are still on disk.
  - **export** — dump any conversation (or all of them) to plain readable
    Markdown, for backup or sharing, independent of the app.

  macOS + Claude Desktop only.
