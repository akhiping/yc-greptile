#!/usr/bin/env python3
"""L0 ledger and L3 veto: the Codex hook entry point.

One script, two jobs, dispatched on `hook_event_name`:

    PostToolUse  ->  append the tool call to the ledger. The agent's prose is
                     never evidence; this file is.
    Stop         ->  run the L1 detectors and, if the agent is lying, return
                     `{"decision": "block"}` with the rap sheet as the reason.

Wire it up with `.codex/hooks.json` at the repository root.

Two rules this file will not break:

1. **It never crashes the agent.** Every failure path still prints `{}` and
   exits 0. A broken verifier that wedges Codex is worse than no verifier.
2. **It caps interventions at 2 per session, then always releases.**
   openai/codex#37937: a Stop hook that blocks indefinitely traps the CLI.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

MAX_INTERVENTIONS = int(os.environ.get("PINOCCHIO_MAX_INTERVENTIONS", "2"))
STATE_DIR = ".pinocchio"
LEDGER_NAME = "ledger.jsonl"
STATE_NAME = "interventions.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _label() -> str:
    """Which config file wired this invocation up, for diagnosing discovery."""
    if "--label" in sys.argv:
        index = sys.argv.index("--label")
        if index + 1 < len(sys.argv):
            return sys.argv[index + 1]
    return ""


def _allow(note: str | None = None) -> None:
    """Let the turn proceed. The only way this script is allowed to end."""
    if note:
        print(note, file=sys.stderr)
    print("{}")
    sys.exit(0)


def _state_dir(repo: Path) -> Path:
    path = repo / STATE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


_MSYS_DRIVE = __import__("re").compile(r"^/([A-Za-z])/(.*)$")


def _normalize_cwd(raw: str) -> Path:
    """Turn whatever the payload calls a directory into one Python can use.

    A Git Bash payload carries `/c/Users/...`, which native git.exe reads as a
    path relative to the current drive root. Left alone it silently resolves to
    `C:\\c\\Users\\...`, and the hook then creates a junk tree there and analyzes
    an empty directory instead of the repository.
    """
    if os.name == "nt":
        match = _MSYS_DRIVE.match(raw)
        if match:
            candidate = Path(f"{match.group(1).upper()}:\\{match.group(2)}")
            if candidate.exists():
                return candidate
    return Path(raw)


def _repo_root(payload: dict[str, Any]) -> Path:
    raw = payload.get("cwd") or os.getcwd()
    cwd = _normalize_cwd(str(raw))
    if not cwd.is_dir():
        cwd = Path(os.getcwd())

    done = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    if done.returncode == 0 and done.stdout.strip():
        return Path(done.stdout.strip())
    return cwd


# ---------------------------------------------------------------------------
# L0 -- the ledger
# ---------------------------------------------------------------------------

def _command_of(payload: dict[str, Any]) -> str:
    """Pull a runnable command string out of whatever shape the payload uses."""
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, str):
        return tool_input
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script", "input"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, (list, tuple)):
                return " ".join(str(v) for v in value)
        # apply_patch and friends: record what was touched, not a command.
        for key in ("path", "file_path", "filename"):
            if isinstance(tool_input.get(key), str):
                return f"{payload.get('tool_name', 'edit')} {tool_input[key]}"
        return json.dumps(tool_input)[:500]
    return ""


def _exit_code_of(payload: dict[str, Any]) -> int | None:
    response = payload.get("tool_response")
    for source in (payload, response if isinstance(response, dict) else {}):
        for key in ("exit_code", "exitCode", "returncode", "return_code", "status"):
            value = source.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                return value
    if isinstance(response, dict):
        # Some builds only report success/failure.
        for key in ("success", "ok"):
            if isinstance(response.get(key), bool):
                return 0 if response[key] else 1
    return None


def _stdout_of(payload: dict[str, Any]) -> str:
    response = payload.get("tool_response")
    if isinstance(response, str):
        return response[:4000]
    if isinstance(response, dict):
        for key in ("stdout", "output", "content", "result"):
            value = response.get(key)
            if isinstance(value, str):
                return value[:4000]
    return ""


def handle_post_tool_use(payload: dict[str, Any]) -> None:
    repo = _repo_root(payload)
    entry = {
        "logged_at": _now(),
        "config_source": _label(),
        "session_id": payload.get("session_id"),
        "tool_name": payload.get("tool_name"),
        "tool_use_id": payload.get("tool_use_id"),
        "command": _command_of(payload),
        "exit_code": _exit_code_of(payload),
        "stdout": _stdout_of(payload),
    }
    try:
        ledger = _state_dir(repo) / LEDGER_NAME
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        _allow(f"pinocchio: could not write the ledger: {exc}")
    _allow()


# ---------------------------------------------------------------------------
# L3 -- the veto
# ---------------------------------------------------------------------------

def _interventions(repo: Path, session_id: str | None) -> int:
    try:
        state = json.loads((_state_dir(repo) / STATE_NAME).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    return int(state.get(str(session_id), 0))


def _record_intervention(repo: Path, session_id: str | None) -> None:
    path = _state_dir(repo) / STATE_NAME
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = {}
    state[str(session_id)] = int(state.get(str(session_id), 0)) + 1
    try:
        path.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass


def _final_message(payload: dict[str, Any]) -> str:
    """Best-effort read of the agent's last assistant message."""
    for key in ("last_assistant_message", "final_message", "message", "assistant_message"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value

    transcript = payload.get("transcript_path")
    if not (isinstance(transcript, str) and Path(transcript).is_file()):
        return ""
    latest = ""
    try:
        for line in Path(transcript).read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("role") != "assistant" and record.get("type") != "assistant":
                continue
            content = record.get("content") or record.get("text") or record.get("message")
            if isinstance(content, str):
                latest = content
            elif isinstance(content, list):
                parts = [
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") in (None, "text")
                ]
                if any(parts):
                    latest = "\n".join(p for p in parts if p)
            elif isinstance(content, dict) and isinstance(content.get("text"), str):
                latest = content["text"]
    except OSError:
        return ""
    return latest


def build_rap_sheet(results: list[dict[str, Any]], nose: int, remaining: int) -> str:
    """The block reason is a prompt, not a status line.

    "Blocked" on its own makes the agent flail. It has to carry the evidence
    *and* the instruction, or the rewrite is a coin flip.
    """
    lies = [r for r in results if r["verdict"] == "LIE"]
    lines = [
        "PINOCCHIO BLOCKED THIS TURN.",
        "",
        f"Your summary does not match the evidence in the repository. Nose length {nose}.",
        "",
    ]
    for index, lie in enumerate(lies, start=1):
        lines.append(f"{index}. [{lie['check_type']}  severity {lie['severity']}/10]")
        lines.append(f"   You implied: {lie['claim']}")
        lines.append(f"   Evidence:    {lie['evidence']}")
        lines.append("")

    lines += [
        "Fix the implementation, not the tests.",
        "",
        "Required:",
        "  - Revert every change you made to a test file. Restore the original",
        "    assertions exactly as they were.",
        "  - Change the source function so those ORIGINAL assertions pass.",
        "  - Do not edit, skip, xfail, or weaken any test. Do not hardcode a value",
        "    that a test asserts.",
        "  - Run the test suite and report the real result.",
        "",
        "If you believe the test itself is genuinely wrong, say so explicitly and",
        "explain why, rather than editing it silently.",
        "",
        f"({remaining} intervention(s) remaining this session, then Pinocchio releases.)",
    ]
    return "\n".join(lines)


def handle_stop(payload: dict[str, Any]) -> None:
    repo = _repo_root(payload)
    session_id = payload.get("session_id")

    used = _interventions(repo, session_id)
    if used >= MAX_INTERVENTIONS:
        # openai/codex#37937 -- a Stop hook that never releases traps the CLI.
        _allow(f"pinocchio: {used} interventions already used this session; releasing.")

    try:
        import detectors
    except ImportError as exc:
        _allow(f"pinocchio: detectors unavailable ({exc}); releasing.")

    session: dict[str, Any] = {}
    message = _final_message(payload)
    if message:
        session["agent_message"] = message
    ledger = _state_dir(repo) / LEDGER_NAME
    if ledger.is_file():
        session["ledger_path"] = str(ledger)

    try:
        report = detectors.run(repo, session=session)
    except Exception as exc:  # a broken detector must not wedge the agent
        _allow(f"pinocchio: detectors failed ({exc}); releasing.")

    results = report["results"]
    nose = sum(r["severity"] for r in results if r["verdict"] == "LIE")
    if not any(r["verdict"] == "LIE" for r in results):
        _allow(f"pinocchio: nothing contradicted (nose {nose}).")

    _record_intervention(repo, session_id)
    remaining = MAX_INTERVENTIONS - (used + 1)
    print(json.dumps({
        "decision": "block",
        "reason": build_rap_sheet(results, nose, remaining),
    }))
    sys.exit(0)


# ---------------------------------------------------------------------------

HANDLERS = {
    "PostToolUse": handle_post_tool_use,
    "Stop": handle_stop,
}


def main() -> None:
    try:
        raw = sys.stdin.read()
    except (OSError, ValueError):
        _allow()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        _allow("pinocchio: unparseable hook payload; releasing.")

    if not isinstance(payload, dict):
        _allow()

    event = payload.get("hook_event_name") or os.environ.get("PINOCCHIO_HOOK_EVENT", "")
    handler = HANDLERS.get(event)
    if handler is None:
        _allow()
    handler(payload)
    _allow()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # absolute last resort
        print(f"pinocchio: unexpected hook failure: {exc}", file=sys.stderr)
        print("{}")
