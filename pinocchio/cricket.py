"""
Cricket — Claude-Mem integration for cross-session memory.

"The Cricket" remembers every verification result across sessions
using Claude-Mem's observation storage.
"""

import json
from pathlib import Path
from typing import Optional
from urllib import request, parse

_SETTINGS = Path.home() / ".claude-mem" / "settings.json"


def _port() -> Optional[int]:
    try:
        return json.loads(_SETTINGS.read_text()).get("port")
    except Exception:
        return None


def store_verification(session_data: dict) -> bool:
    port = _port()
    if not port:
        return False
    try:
        body = json.dumps({
            "type": "verification",
            "project": session_data.get("repo", "unknown"),
            "content": json.dumps(session_data),
            "tags": ["pinocchio"],
        }).encode()
        req = request.Request(
            f"http://127.0.0.1:{port}/api/observations",
            data=body, headers={"Content-Type": "application/json"}, method="POST",
        )
        request.urlopen(req, timeout=5)
        return True
    except Exception:
        return False


def recall_history(repo_name: str) -> Optional[dict]:
    port = _port()
    if not port:
        return None
    try:
        q = parse.urlencode({"q": f"pinocchio {repo_name}", "limit": 10})
        resp = request.urlopen(f"http://127.0.0.1:{port}/api/search?{q}", timeout=5)
        results = json.loads(resp.read())
        patterns, files = set(), set()
        for obs in results if isinstance(results, list) else results.get("results", []):
            content = json.loads(obs.get("content", "{}"))
            for r in content.get("results", []):
                if r.get("verdict") == "LIE":
                    patterns.add(r.get("check_type", ""))
                    files.add(r.get("evidence", "").split(": ")[0].replace("In ", ""))
        return {
            "prior_flags": len(results if isinstance(results, list) else results.get("results", [])),
            "known_patterns": list(patterns),
            "watch_files": list(files),
        }
    except Exception:
        return None
