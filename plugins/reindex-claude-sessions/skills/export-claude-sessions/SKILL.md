---
name: export-claude-sessions
description: Export Claude Code conversation transcripts (~/.claude/projects/*/*.jsonl) into plain, readable Markdown files — either one specific conversation, or all of them as a proactive backup. Trigger on requests like "导出这个对话", "导出所有本地对话", "export this conversation", "backup my Claude chat history", "save this session as a readable file".
---

# Export Claude Code sessions to Markdown

## Why

Raw transcripts (`~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl`) are
JSON-lines with tool payloads, thinking blocks, and internal metadata mixed
in — not something a person wants to read directly, and not portable if the
on-disk format ever changes. This exports just the human-readable dialogue
(user prompts + assistant replies, optionally with compact tool-call notes)
into a plain `.md` file that opens anywhere, forever.

Companion to [[reindex-claude-sessions]] — that skill rebuilds the Desktop
app's index after a reinstall; this one produces a plain-text copy that
doesn't depend on the app or its internal formats at all, so it survives
even if `~/.claude` itself is ever lost.

## Steps

1. List available sessions if the user hasn't named one:
   ```
   python3 ~/.claude/skills/export-claude-sessions/export_sessions.py --list
   ```
2. Export a single session (ask which one if ambiguous):
   ```
   python3 ~/.claude/skills/export-claude-sessions/export_sessions.py --session <id> -o <output.md>
   ```
   Add `--tools` to include compact one-line notes for tool calls (e.g.
   `_(ran Bash: ls -la)_`), otherwise only the readable dialogue is kept.
3. Export everything (good as a pre-reinstall/migration backup — suggest
   this proactively when the user is about to reinstall, reset, or migrate
   machines):
   ```
   python3 ~/.claude/skills/export-claude-sessions/export_sessions.py --all -o ~/claude-session-exports
   ```
   Writes one `.md` per session, grouped into subfolders per project.
4. Tell the user where the file(s) landed. If exporting for sharing, remind
   them the export may contain project file paths, code, or command output
   verbatim — check whether it needs to be redacted before sending outside
   the team.
