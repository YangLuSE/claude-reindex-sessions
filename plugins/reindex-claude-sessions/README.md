# reindex-claude-sessions

Two utilities for local Claude Code conversation data:

- **reindex** — rebuild Claude Desktop's local session/history index after
  a system reinstall (or any time old conversations stop showing up in the
  app's sidebar), even though the raw transcripts are still sitting on disk.
- **export** — dump any conversation (or all of them) to plain, readable
  Markdown, independent of the app and its internal formats. Useful as a
  proactive backup before a reinstall/migration, or just to read/share a
  past conversation as normal text.

## The problem

Claude Code conversations are stored in two separate places:

1. **Raw transcripts** — `~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl`.
   The actual conversation content. Plain files, so they survive being
   copied/restored from a backup.
2. **Desktop sidebar index** — `~/Library/Application Support/Claude/
   claude-code-sessions/<accountUuid>/<orgUuid>/local_<uuid>.json`.
   Small app state the Desktop app scans to populate its per-project
   session list. This lives *outside* `~/.claude`, so restoring only the
   `.claude` folder after a reinstall (or migrating to a new Mac) brings
   back (1) but not (2) — the app shows empty history for every project
   even though every transcript is intact.

This plugin rebuilds (2) from (1).

## Usage — reindex

Ask Claude something like:

- "重装后找不到之前的对话了"
- "my Claude Code conversation history disappeared after reinstalling"
- "reindex my Claude sessions"

Or run the script directly:

```bash
python3 skills/reindex-claude-sessions/reindex_sessions.py --dry-run   # preview
python3 skills/reindex-claude-sessions/reindex_sessions.py             # apply
```

Then **fully quit Claude Desktop (Cmd+Q) and reopen it** — recovered
sessions appear per-project after relaunch.

It's purely additive: it only creates index entries for transcripts that
don't already have one, never touches or deletes an existing entry, and
is safe to re-run at any time.

## Usage — export

Ask Claude something like:

- "导出这个对话" / "导出所有本地对话"
- "export this conversation to a readable file"
- "backup my Claude chat history before I reinstall"

Or run the script directly:

```bash
python3 skills/export-claude-sessions/export_sessions.py --list
python3 skills/export-claude-sessions/export_sessions.py --session <id> -o out.md
python3 skills/export-claude-sessions/export_sessions.py --all -o ~/claude-session-exports
```

Produces plain Markdown: user prompts + assistant replies, in order. Pass
`--tools` to also include a compact one-line note per tool call. Exported
files may contain project file paths, code, or command output verbatim —
review before sharing outside your team.

## Limitations

- macOS + Claude Desktop only (paths are macOS-specific).
- Does not restore missing `.jsonl` transcripts themselves — only
  (re)builds the index for transcripts that already exist locally. If a
  project's transcript itself is missing, restore it first (e.g. from
  Time Machine or another backup) into `~/.claude/projects/`.
- Based on analysis of the on-disk format of Claude Desktop 2.1.197.
  This is undocumented internal app state, not a public API — a future
  Desktop release could change the format. If the script stops working
  after an app update, please open an issue.

## License

MIT
