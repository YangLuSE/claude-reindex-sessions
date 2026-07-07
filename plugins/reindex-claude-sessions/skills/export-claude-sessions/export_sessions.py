#!/usr/bin/env python3
"""
Export Claude Code conversation transcripts (~/.claude/projects/*/*.jsonl)
into plain, human-readable Markdown.

Two use cases:
  1. Read/share/archive a past conversation as normal text, without needing
     Claude Desktop or the CCD session tools at all.
  2. Proactive backup: run with --all before a system reinstall/migration so
     you have a plain-text copy of every conversation that survives even if
     ~/.claude itself is ever lost (unlike the raw .jsonl, a .md file is
     readable by anything, forever, format changes or not).

Usage:
  export_sessions.py --list                      list every session found
  export_sessions.py --session <id> [-o out.md]   export one session
  export_sessions.py --all [-o out_dir]           export every session found

By default, text-only view (skips thinking blocks, raw tool_use/tool_result
payloads). Pass --tools to also include a compact one-line note per tool call.
"""
import argparse
import glob
import json
import os
import re
import datetime

PROJECTS_DIR = os.path.expanduser("~/.claude/projects")
DEFAULT_OUT_DIR = os.path.expanduser("~/claude-session-exports")


def find_jsonl(session_id):
    matches = glob.glob(os.path.join(PROJECTS_DIR, "*", f"{session_id}.jsonl"))
    return matches[0] if matches else None


def slugify(text, max_len=50):
    text = re.sub(r"[^\w一-鿿\- ]", "", text).strip()
    text = re.sub(r"\s+", "-", text)
    return text[:max_len] or "untitled"


def extract_text(message):
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [b.get("text", "") for b in content if b.get("type") == "text"]
        joined = "\n".join(t for t in texts if t)
        return joined or None
    return None


def extract_tool_calls(message):
    content = message.get("content")
    calls = []
    if isinstance(content, list):
        for b in content:
            if b.get("type") == "tool_use":
                calls.append((b.get("name", "?"), b.get("input", {})))
    return calls


def session_summary(path):
    """Returns (session_id, cwd, first_ts, last_ts, title, turns) without full export."""
    session_id = os.path.basename(path)[:-len(".jsonl")]
    cwd = None
    first_ts = last_ts = None
    title = None
    turns = 0
    with open(path, errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            ts = d.get("timestamp")
            if ts:
                first_ts = first_ts or ts
                last_ts = ts
            if cwd is None and d.get("cwd"):
                cwd = d["cwd"]
            if d.get("type") == "user":
                text = extract_text(d.get("message", {}))
                if text:
                    turns += 1
                    if title is None:
                        title = text.strip().replace("\n", " ")[:70]
    if cwd is None:
        folder = os.path.basename(os.path.dirname(path))
        cwd = folder.replace("-Users-", "/Users/").replace("-", "/")
    return session_id, cwd, first_ts, last_ts, title or "(untitled)", turns


def export_to_markdown(path, include_tools=False):
    session_id, cwd, first_ts, last_ts, title, _ = session_summary(path)
    lines = [
        f"# {title}",
        "",
        f"- session: `{session_id}`",
        f"- project: `{cwd}`",
        f"- date: {first_ts} → {last_ts}",
        "",
        "---",
        "",
    ]
    last_role = None
    with open(path, errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            t = d.get("type")
            if t not in ("user", "assistant"):
                continue
            message = d.get("message", {})
            text = extract_text(message)
            if text and text.strip():
                role_label = "**User:**" if t == "user" else "**Assistant:**"
                if last_role != t:
                    lines.append(role_label)
                lines.append(text.strip())
                lines.append("")
                last_role = t
            if include_tools and t == "assistant":
                for name, inp in extract_tool_calls(message):
                    hint = next(iter(inp.values()), "") if isinstance(inp, dict) else ""
                    hint = str(hint).replace("\n", " ")[:80]
                    lines.append(f"_(ran {name}: {hint})_")
                    lines.append("")
                    last_role = t
    return "\n".join(lines)


def cmd_list():
    files = glob.glob(os.path.join(PROJECTS_DIR, "*", "*.jsonl"))
    for path in sorted(files, key=os.path.getmtime, reverse=True):
        session_id, cwd, first_ts, last_ts, title, turns = session_summary(path)
        print(f"{session_id}  {cwd}  {turns} turns  {title[:50]}")


def cmd_export_one(session_id, output, include_tools):
    path = find_jsonl(session_id)
    if not path:
        print(f"No transcript found for session {session_id} under {PROJECTS_DIR}")
        return
    md = export_to_markdown(path, include_tools)
    if output:
        out_path = output
    else:
        _, cwd, _, _, title, _ = session_summary(path)
        os.makedirs(DEFAULT_OUT_DIR, exist_ok=True)
        out_path = os.path.join(DEFAULT_OUT_DIR, f"{slugify(title)}-{session_id[:8]}.md")
    with open(out_path, "w") as fh:
        fh.write(md)
    print(f"Exported {session_id} -> {out_path}")


def cmd_export_all(out_dir, include_tools):
    out_dir = out_dir or DEFAULT_OUT_DIR
    files = glob.glob(os.path.join(PROJECTS_DIR, "*", "*.jsonl"))
    count = 0
    for path in files:
        session_id, cwd, _, _, title, _ = session_summary(path)
        project_name = os.path.basename(cwd.rstrip("/")) or "root"
        project_dir = os.path.join(out_dir, slugify(project_name))
        os.makedirs(project_dir, exist_ok=True)
        out_path = os.path.join(project_dir, f"{slugify(title)}-{session_id[:8]}.md")
        md = export_to_markdown(path, include_tools)
        with open(out_path, "w") as fh:
            fh.write(md)
        count += 1
    print(f"Exported {count} sessions to {out_dir}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--list", action="store_true")
    p.add_argument("--session", metavar="SESSION_ID")
    p.add_argument("--all", action="store_true")
    p.add_argument("-o", "--output", metavar="PATH", help="output file (--session) or dir (--all)")
    p.add_argument("--tools", action="store_true", help="include compact tool-call notes")
    args = p.parse_args()

    if args.list:
        cmd_list()
    elif args.session:
        cmd_export_one(args.session, args.output, args.tools)
    elif args.all:
        cmd_export_all(args.output, args.tools)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
