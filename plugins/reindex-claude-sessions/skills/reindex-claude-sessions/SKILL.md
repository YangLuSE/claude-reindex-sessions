---
name: reindex-claude-sessions
description: Rebuild Claude Desktop's local session/history index after a system reinstall (or any time) when past Claude Code conversations aren't showing up in the app's sidebar even though the raw transcripts still exist under ~/.claude/projects. Trigger on requests like "找不到之前的对话", "重装后会话历史没了", "conversation history disappeared", "recover/restore my Claude Code chat history", "reindex my sessions". macOS + Claude Desktop only.
---

# Reindex Claude Code sessions

## Background

Claude Code conversations live in two separate places:

1. **Raw transcripts** — `~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl`.
   This is the actual conversation content. It's a plain file, so it survives
   being copied/restored from a backup (Time Machine, manual copy of the
   `.claude` folder, etc.).
2. **Desktop sidebar index** — `~/Library/Application Support/Claude/
   claude-code-sessions/<accountUuid>/<orgUuid>/local_<uuid>.json`.
   This is small app state the Desktop app scans to populate its session
   list per project. It lives *outside* `~/.claude`, so restoring only the
   `.claude` folder after a reinstall brings back (1) but not (2) — the app
   shows an empty history even though every transcript is intact on disk.

This skill rebuilds (2) from (1). It is purely additive: it only creates new
index files for transcripts that don't already have one, and never deletes
or overwrites an existing entry, so it's safe to re-run at any time (e.g.
after starting a new project, or just to double check nothing is missing).

## Steps

1. Run the bundled script with `--dry-run` first to preview what it would do:
   ```
   python3 ~/.claude/skills/reindex-claude-sessions/reindex_sessions.py --dry-run
   ```
2. If the preview looks right, run it for real (drop `--dry-run`):
   ```
   python3 ~/.claude/skills/reindex-claude-sessions/reindex_sessions.py
   ```
3. Tell the user to **fully quit Claude Desktop (Cmd+Q, not just close the
   window)** and reopen it — the recovered sessions appear per-project after
   relaunch, not live.
4. If a project still doesn't show its history after that, the likely cause
   is the raw `.jsonl` transcript itself is missing from `~/.claude/projects`
   (not just the index) — that has to be restored first from wherever the
   user's backup lives (Time Machine, an external drive, another Mac) by
   copying the matching `-Users-...` folder into `~/.claude/projects/`, then
   re-run this script.

## What the script does NOT do

- It does not restore missing `.jsonl` transcripts themselves — only builds
  the index pointing at whatever transcripts already exist locally.
- It does not touch `~/.claude/history.jsonl` (shell input history) or any
  cloud-synced conversation list — only the local Desktop sidebar cache.
