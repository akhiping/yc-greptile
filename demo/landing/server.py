#!/usr/bin/env python3
"""Local Pinocchio landing page and terminal harness.

Run from the repository root:
    python demo/landing/server.py

Then open http://127.0.0.1:8797/
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = Path(__file__).resolve().parent
DIST_ROOT = APP_ROOT / "dist"
WEB_ROOT = DIST_ROOT if DIST_ROOT.is_dir() else APP_ROOT
REPORT = ROOT / ".pinocchio" / "live-report.json"
MEMORY_FILE = ROOT / ".pinocchio" / "landing-memory.jsonl"
SCENARIO_DIR = APP_ROOT / "scenarios"
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", os.environ.get("PINOCCHIO_WEB_PORT", "8797")))
MEMORY_LOCK = threading.Lock()
MEMORY: list[dict[str, object]] = []


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_memory() -> None:
    if not MEMORY_FILE.is_file():
        return
    with MEMORY_LOCK:
        MEMORY.clear()
        for line in MEMORY_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                MEMORY.append(item)


def report_summary() -> dict[str, object] | None:
    if not REPORT.is_file():
        return None
    try:
        report = json.loads(REPORT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    summary = report.get("summary")
    if not isinstance(summary, dict):
        return None
    return {
        "total": summary.get("total", 0),
        "lies": summary.get("lies", 0),
        "verified": summary.get("verified", 0),
        "uncertain": summary.get("uncertain", 0),
        "nose_length": summary.get("nose_length", 0),
    }


def read_scenario(name: str) -> dict[str, object] | None:
    safe_name = "".join(char for char in name if char.isalnum() or char in "-_")
    if safe_name != name:
        return None
    path = SCENARIO_DIR / f"{safe_name}.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def read_scenario_index() -> dict[str, object]:
    path = SCENARIO_DIR / "index.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"scenarios": []}
    return payload if isinstance(payload, dict) else {"scenarios": []}


def store_receipt(receipt: dict[str, object]) -> None:
    with MEMORY_LOCK:
        MEMORY.append(receipt)
        del MEMORY[:-25]
        try:
            MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with MEMORY_FILE.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(receipt, ensure_ascii=False) + "\n")
        except OSError:
            pass


def command_for(run: str) -> list[list[str]]:
    python = sys.executable
    if run == "demo":
      return [[python, "demo/landing/harness_demo.py", "caught-cheat"]]
    if run == "verify":
      return [[python, "demo/landing/harness_demo.py", "verify"]]
    if run == "loop-dry":
      return [
          [python, "demo-repo/arm.py"],
          [
              python,
              "pinocchio/loop.py",
              "--repo",
              ".demo-target",
              "--max-iterations",
              "1",
              "--dry-run",
              "--json",
          ],
      ]
    if run == "loop-codex":
      if shutil.which("codex") is None:
          return [[python, "demo/landing/harness_demo.py", "caught-cheat"]]
      return [
          [python, "demo-repo/arm.py"],
          [
              python,
              "pinocchio/loop.py",
              "--repo",
              ".demo-target",
              "--max-iterations",
              "1",
              "--timeout",
              "240",
              "--json",
          ],
      ]
    return [[python, "-c", "print('unknown run')"]]


def stream_commands(commands: Iterable[list[str]]) -> Iterable[tuple[str, str]]:
    final_code = 0
    for command in commands:
      yield "line", "+ " + " ".join(command)
      process = subprocess.Popen(
          command,
          cwd=str(ROOT),
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT,
          text=True,
          bufsize=1,
          errors="replace",
      )
      assert process.stdout is not None
      for raw_line in process.stdout:
          yield "line", raw_line.rstrip("\n")
      final_code = process.wait()
      yield "line", f"[exit {final_code}]"
      if final_code != 0:
          break
    yield "done", str(final_code)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
      super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def log_message(self, format: str, *args) -> None:
      return

    def do_GET(self) -> None:
      parsed = urlparse(self.path)
      if parsed.path == "/api/status":
          self.send_json(
              {
                  "codex": shutil.which("codex") is not None,
                  "claude": shutil.which("claude") is not None,
                  "report": REPORT.is_file(),
                  "memory_count": len(MEMORY),
                  "scenario_count": len(read_scenario_index().get("scenarios", [])),
                  "codex_fallback": shutil.which("codex") is None,
              }
          )
          return
      if parsed.path == "/api/scenarios":
          self.send_json(read_scenario_index())
          return
      if parsed.path == "/api/scenario":
          query = parse_qs(parsed.query)
          scenario = read_scenario(query.get("id", ["test-tampering"])[0])
          self.send_json({"scenario": scenario})
          return
      if parsed.path == "/api/memory":
          with MEMORY_LOCK:
              receipts = list(MEMORY)
          self.send_json({"receipts": receipts})
          return
      if parsed.path == "/api/report":
          if not REPORT.is_file():
              self.send_json({"report": None})
              return
          try:
              self.send_json({"report": json.loads(REPORT.read_text(encoding="utf-8"))})
          except (OSError, json.JSONDecodeError):
              self.send_json({"report": None})
          return
      if parsed.path == "/api/events":
          query = parse_qs(parsed.query)
          run = query.get("run", ["demo"])[0]
          agent = query.get("agent", ["codex"])[0]
          transcript: list[str] = []
          self.send_response(200)
          self.send_header("Content-Type", "text/event-stream")
          self.send_header("Cache-Control", "no-cache")
          self.send_header("Connection", "close")
          self.end_headers()
          self.write_event("line", f"harness target: {agent}")
          if run == "loop-codex" and shutil.which("codex") is None:
              self.write_event(
                  "line",
                  "codex CLI not found in this runtime; replaying the recorded caught-cheat verifier path",
              )
          for event, payload in stream_commands(command_for(run)):
              if event == "line":
                  transcript.append(payload)
              self.write_event(event, payload)
          receipt = {
              "captured_at": now(),
              "agent": agent,
              "run": run,
              "command_count": sum(1 for line in transcript if line.startswith("+ ")),
              "transcript_tail": transcript[-12:],
              "report_summary": report_summary(),
              "report_path": str(REPORT),
              "memory_policy": "Public run receipts only: commands, output tail, report summary, and timestamps.",
          }
          store_receipt(receipt)
          self.close_connection = True
          return
      super().do_GET()

    def send_json(self, payload: dict[str, object]) -> None:
      body = json.dumps(payload).encode("utf-8")
      self.send_response(200)
      self.send_header("Content-Type", "application/json")
      self.send_header("Content-Length", str(len(body)))
      self.end_headers()
      self.wfile.write(body)

    def write_event(self, event: str, payload: str) -> None:
      for line in payload.splitlines() or [""]:
          data = line.replace("\r", "")
          self.wfile.write(f"event: {event}\ndata: {data}\n\n".encode("utf-8"))
      self.wfile.flush()


def main() -> int:
    load_memory()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    local_url = f"http://127.0.0.1:{PORT}/" if HOST == "0.0.0.0" else f"http://{HOST}:{PORT}/"
    print(f"Pinocchio landing page: {local_url}")
    print("Press Ctrl+C to stop.")
    try:
      thread.join()
    except KeyboardInterrupt:
      server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
