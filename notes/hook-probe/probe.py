#!/usr/bin/env python3
"""
Codex hook probe — diagnostic, not product code.

Answers three questions my research could not settle, in about 60 seconds:

  1. Do hooks fire at all, or are they silently ignored without a feature flag?
     (Official docs say hooks run by default and `[features] hooks = false`
     disables them. A third-party reference says you must set
     `[features] codex_hooks = true` or hooks are silently ignored. Silent
     failure is the worst kind, so test it rather than trust either source.)

  2. Which tools trigger PreToolUse / PostToolUse? Official docs claim Bash +
     apply_patch + MCP + local function tools. A third-party reference says
     Bash only, by design. This decides whether a hook can see file edits.

  3. What is actually in the payload? Field names matter more than docs do.

Never blocks anything. Always emits {} so Codex proceeds normally.

Usage: wire into ~/.codex/hooks.json (see hooks.json next to this file),
then run Codex and do three things: send a prompt, let it run a shell
command, and let it edit a file. Then read probe-log.jsonl.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(__file__).parent / "probe-log.jsonl"


def main() -> None:
    raw = sys.stdin.read()

    try:
        payload = json.loads(raw) if raw.strip() else {}
        parsed = True
    except json.JSONDecodeError:
        payload = {"_unparsed_stdin": raw[:2000]}
        parsed = False

    entry = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "parsed_ok": parsed,
        "event": payload.get("hook_event_name"),
        "tool_name": payload.get("tool_name"),
        "top_level_keys": sorted(payload.keys()),
        "payload": payload,
    }

    try:
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:  # never let the probe break the agent
        print(f"probe log write failed: {exc}", file=sys.stderr)

    # No-op decision: allow everything through.
    print("{}")


if __name__ == "__main__":
    main()
