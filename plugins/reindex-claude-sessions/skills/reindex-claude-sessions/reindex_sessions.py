#!/usr/bin/env python3
"""
Rebuild Claude Desktop's local session index (the sidebar/history list) from
the raw Claude Code session transcripts under ~/.claude/projects.

Background: Claude Code conversations are stored in two places:
  1. Raw transcripts: ~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl
     (the actual conversation content, survives being copied/restored as
     plain files).
  2. Desktop sidebar index: ~/Library/Application Support/Claude/
     claude-code-sessions/<accountUuid>/<orgUuid>/local_<uuid>.json
     (small metadata records the app scans to populate its session list —
     this is app state, NOT part of ~/.claude, so a plain "copy the .claude
     folder back" restore after a reinstall will bring back (1) but not (2),
     and the app will show no history even though the transcripts are intact).

This script scans (1), finds every session that has no corresponding entry
in (2), and synthesizes a minimal index record for it (cwd, first/last
timestamp, a title derived from the first prompt). It never touches or
deletes existing index entries — it's safe to re-run any time.

After running, fully quit Claude Desktop (Cmd+Q) and reopen it for the
rebuilt entries to appear.

macOS + Claude Desktop only.
"""
import json
import glob
import os
import sys
import uuid
import datetime

APP_SUPPORT = os.path.expanduser("~/Library/Application Support/Claude")
PROJECTS_DIR = os.path.expanduser("~/.claude/projects")


def find_account_id():
    cfg_path = os.path.join(APP_SUPPORT, "config.json")
    if os.path.exists(cfg_path):
        try:
            cfg = json.load(open(cfg_path))
            if cfg.get("lastKnownAccountUuid"):
                return cfg["lastKnownAccountUuid"]
        except Exception:
            pass
    ops_path = os.path.join(APP_SUPPORT, "cowork-enabled-cli-ops.json")
    if os.path.exists(ops_path):
        try:
            ops = json.load(open(ops_path))
            if ops.get("ownerAccountId"):
                return ops["ownerAccountId"]
        except Exception:
            pass
    return None


def find_org_dirs(account_id):
    base = os.path.join(APP_SUPPORT, "claude-code-sessions", account_id)
    if os.path.isdir(base):
        dirs = [d for d in glob.glob(base + "/*") if os.path.isdir(d)]
        if dirs:
            return dirs
    return []


def to_ms(iso):
    return int(datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


def scan_indexed(org_dir):
    indexed = set()
    for f in glob.glob(org_dir + "/*.json"):
        try:
            d = json.load(open(f))
            if d.get("cliSessionId"):
                indexed.add(d["cliSessionId"])
        except Exception:
            pass
    return indexed


def extract_meta(path):
    cwd = None
    first_ts = None
    last_ts = None
    title_raw = None
    turns = 0
    with open(path, "r", errors="ignore") as fh:
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
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
            if cwd is None and d.get("cwd"):
                cwd = d["cwd"]
            if title_raw is None and d.get("type") == "queue-operation" \
                    and d.get("operation") == "enqueue" and d.get("content"):
                title_raw = d["content"]
            if d.get("type") == "user":
                turns += 1
    if cwd is None:
        folder = os.path.basename(os.path.dirname(path))
        cwd = folder.replace("-Users-", "/Users/").replace("-", "/")
    title = (title_raw or os.path.basename(os.path.dirname(path))).strip()
    title = title.replace("\n", " ")[:70]
    return cwd, first_ts, last_ts, title, turns


def main():
    dry_run = "--dry-run" in sys.argv

    account_id = find_account_id()
    if not account_id:
        print("Could not find your Claude account id in "
              f"{APP_SUPPORT}/config.json — is Claude Desktop installed and "
              "have you signed in at least once since reinstalling?")
        sys.exit(1)

    org_dirs = find_org_dirs(account_id)
    if not org_dirs:
        print(f"No org directory found under claude-code-sessions/{account_id}/. "
              "Open Claude Desktop at least once (so it creates its session "
              "folder) before running this script.")
        sys.exit(1)

    jsonl_files = glob.glob(os.path.join(PROJECTS_DIR, "*", "*.jsonl"))
    if not jsonl_files:
        print(f"No session transcripts found under {PROJECTS_DIR}.")
        sys.exit(0)

    target_org_dir = org_dirs[0]
    already_indexed = set()
    for od in org_dirs:
        already_indexed |= scan_indexed(od)

    created = []
    for path in jsonl_files:
        session_id = os.path.basename(path)[:-len(".jsonl")]
        if session_id in already_indexed:
            continue
        cwd, first_ts, last_ts, title, turns = extract_meta(path)
        entry = {
            "sessionId": f"local_{uuid.uuid4()}",
            "cliSessionId": session_id,
            "cwd": cwd,
            "originCwd": cwd,
            "lastFocusedAt": to_ms(last_ts) if last_ts else 0,
            "createdAt": to_ms(first_ts) if first_ts else 0,
            "lastActivityAt": to_ms(last_ts) if last_ts else 0,
            "model": "claude-sonnet-5",
            "effort": "high",
            "isArchived": False,
            "title": f"{title} (recovered)",
            "titleSource": "auto",
            "permissionMode": "default",
            "remoteMcpServersConfig": [],
            "completedTurns": turns,
            "alwaysAllowedReasons": [],
            "sessionPermissionUpdates": [],
            "classifierSummaryEnabled": True,
            "spawnSeed": {},
        }
        created.append((session_id, cwd, title))
        if not dry_run:
            out_path = os.path.join(target_org_dir, entry["sessionId"] + ".json")
            with open(out_path, "w") as fh:
                json.dump(entry, fh, indent=4)

    if not created:
        print("Nothing to do — every transcript already has an index entry.")
        return

    verb = "Would create" if dry_run else "Created"
    print(f"{verb} {len(created)} index entries:")
    for session_id, cwd, title in created:
        print(f"  - {cwd}  |  {title[:60]}")

    if not dry_run:
        print("\nFully quit Claude Desktop (Cmd+Q) and reopen it to see the "
              "recovered conversations in each project's history.")


if __name__ == "__main__":
    main()
