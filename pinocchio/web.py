"""Local browser dashboard for Pinocchio verification reports."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

from .ui import load_report


def _safe_json(value: Mapping[str, Any]) -> str:
    """Prevent report data from closing the dashboard's script element."""

    return json.dumps(value, ensure_ascii=True).replace("<", "\\u003c")


def dashboard_html(report: Mapping[str, Any]) -> str:
    """Return a self-contained dashboard using the supplied report snapshot."""

    payload = _safe_json(report)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>Pinocchio · Trust report</title>
  <style>
    :root {{
      --bg: #080b12; --panel: #111722; --panel-2: #171f2d; --line: #273247;
      --text: #edf2ff; --muted: #8d9ab2; --green: #42d392; --red: #ff6b78;
      --yellow: #f4c95d; --blue: #78a9ff; --shadow: 0 18px 60px #0008;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: radial-gradient(circle at 80% -10%, #23345a 0, var(--bg) 42rem);
      color: var(--text); font: 15px/1.5 Inter, ui-sans-serif, system-ui, sans-serif; }}
    .shell {{ max-width: 1180px; margin: auto; padding: 42px 24px 72px; }}
    .eyebrow {{ color: var(--blue); font-size: 12px; font-weight: 800; letter-spacing: .16em; }}
    h1 {{ margin: 7px 0 4px; font-size: clamp(30px, 5vw, 52px); letter-spacing: -.045em; line-height: 1.05; }}
    .sub {{ color: var(--muted); margin: 0 0 30px; overflow-wrap: anywhere; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
    .card, .result {{ background: #111722cc; border: 1px solid var(--line); border-radius: 18px;
      box-shadow: var(--shadow); backdrop-filter: blur(18px); }}
    .card {{ padding: 18px 20px; min-height: 116px; }}
    .card-label {{ color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; }}
    .number {{ display: block; margin-top: 7px; font-size: 34px; font-weight: 800; letter-spacing: -.05em; }}
    .lie {{ color: var(--red); }} .verified {{ color: var(--green); }} .uncertain {{ color: var(--yellow); }}
    .nose-wrap {{ margin: 26px 0 34px; padding: 21px 24px; border: 1px solid var(--line);
      border-radius: 18px; background: linear-gradient(115deg, #151e2d, #10151f); }}
    .nose-head {{ display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }}
    .nose-head strong {{ font-size: 18px; }} .nose-head span {{ color: var(--muted); }}
    .track {{ height: 10px; background: #080b12; border-radius: 99px; overflow: hidden; margin-top: 13px; }}
    .fill {{ height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--green), var(--yellow), var(--red)); transition: width .4s; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 14px; }}
    .tabs {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    button, input {{ border: 1px solid var(--line); border-radius: 10px; background: var(--panel);
      color: var(--text); font: inherit; }}
    button {{ padding: 8px 13px; cursor: pointer; }} button:hover, button.active {{ background: var(--panel-2); border-color: #5c78aa; }}
    input {{ margin-left: auto; padding: 9px 12px; min-width: 220px; outline: none; }}
    input:focus {{ border-color: var(--blue); box-shadow: 0 0 0 3px #78a9ff22; }}
    .results {{ display: grid; gap: 10px; }}
    .result {{ padding: 19px 20px; border-left: 4px solid var(--muted); }}
    .result.is-lie {{ border-left-color: var(--red); }} .result.is-verified {{ border-left-color: var(--green); }}
    .result.is-uncertain {{ border-left-color: var(--yellow); }}
    .result-top {{ display: flex; gap: 13px; align-items: start; }}
    .pill {{ flex: none; border-radius: 99px; padding: 3px 9px; font-size: 11px; font-weight: 800; letter-spacing: .05em; }}
    .pill.lie {{ background: #ff6b7822; }} .pill.verified {{ background: #42d39222; }}
    .pill.uncertain {{ background: #f4c95d22; }} .claim {{ font-size: 16px; font-weight: 700; }}
    .meta {{ color: var(--muted); font-size: 12px; margin-top: 6px; }}
    details {{ margin-top: 14px; border-top: 1px solid var(--line); padding-top: 12px; }}
    summary {{ color: var(--blue); cursor: pointer; font-size: 13px; font-weight: 700; }}
    .evidence {{ color: #c4cee1; margin: 10px 0 0; white-space: pre-wrap; overflow-wrap: anywhere; }}
    .empty {{ color: var(--muted); padding: 30px; text-align: center; border: 1px dashed var(--line); border-radius: 16px; }}
    footer {{ color: var(--muted); font-size: 12px; margin-top: 28px; display: flex; justify-content: space-between; gap: 12px; }}
    @media (max-width: 760px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); }} .shell {{ padding: 28px 15px 52px; }}
      input {{ margin-left: 0; width: 100%; }} footer {{ display: block; }} footer span {{ display: block; margin-top: 6px; }} }}
  </style>
</head>
<body>
  <main class="shell">
    <div class="eyebrow">PINOCCHIO / TRUST LAYER</div>
    <h1>Trust, but verify.</h1>
    <p class="sub" id="target"></p>
    <section class="grid" aria-label="Verification summary">
      <article class="card"><span class="card-label">Total checks</span><strong class="number" id="total">0</strong></article>
      <article class="card"><span class="card-label">Claims contradicted</span><strong class="number lie" id="lies">0</strong></article>
      <article class="card"><span class="card-label">Verified</span><strong class="number verified" id="verified">0</strong></article>
      <article class="card"><span class="card-label">Needs review</span><strong class="number uncertain" id="uncertain">0</strong></article>
    </section>
    <section class="nose-wrap" aria-label="Nose length">
      <div class="nose-head"><strong>Integrity signal</strong><span id="nose-label">0 / 10</span></div>
      <div class="track"><div class="fill" id="nose-fill" role="progressbar" aria-label="Integrity signal"></div></div>
    </section>
    <div class="toolbar">
      <div class="tabs" role="tablist" aria-label="Filter results">
        <button class="active" data-filter="ALL" role="tab">All</button>
        <button data-filter="LIE" role="tab">Lies</button>
        <button data-filter="VERIFIED" role="tab">Verified</button>
        <button data-filter="UNCERTAIN" role="tab">Uncertain</button>
      </div>
      <input id="search" type="search" placeholder="Search claims or evidence…" aria-label="Search results">
    </div>
    <section class="results" id="results" aria-live="polite"></section>
    <footer><span>Independent evidence only · no claim is verified by prose alone.</span><span id="updated"></span></footer>
  </main>
  <script>
    let report = {payload};
    let filter = "ALL";
    const $ = (id) => document.getElementById(id);
    const esc = (value) => String(value).replace(/[&<>"']/g, (char) =>
      ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}})[char]);
    function render() {{
      const summary = report.summary || {{}}, metadata = report.metadata || {{}};
      $("target").textContent = `${{metadata.target_repo || "Unknown repository"}} · ${{metadata.mode || "report"}}`;
      ["total", "lies", "verified", "uncertain"].forEach((key) => $(key).textContent = summary[key] || 0);
      const nose = Math.max(0, Math.min(10, Number(summary.nose_length || 0)));
      $("nose-label").textContent = `${{nose}} / 10`; $("nose-fill").style.width = `${{nose * 10}}%`;
      $("nose-fill").setAttribute("aria-valuenow", nose);
      const query = $("search").value.trim().toLowerCase();
      const results = (report.results || []).filter((item) =>
        (filter === "ALL" || item.verdict === filter) &&
        (!query || JSON.stringify(item).toLowerCase().includes(query)));
      $("results").innerHTML = results.length ? results.map((item) => {{
        const verdict = ["LIE", "VERIFIED", "UNCERTAIN"].includes(item.verdict) ? item.verdict : "UNCERTAIN";
        return `<article class="result is-${{verdict.toLowerCase()}}">
          <div class="result-top"><span class="pill ${{verdict.toLowerCase()}}">${{verdict}}</span>
            <div><div class="claim">${{esc(item.claim || "Untitled claim")}}</div>
            <div class="meta">${{esc(item.check_type || "check")}} · severity ${{esc(item.severity || 1)}}/10</div></div></div>
          <details><summary>View independent evidence</summary><div class="evidence">${{esc(item.evidence || "No evidence supplied.")}}</div></details>
        </article>`;
      }}).join("") : '<div class="empty">No results match this filter.</div>';
      $("updated").textContent = metadata.captured_at ? `Captured ${{metadata.captured_at}}` : "";
    }}
    document.querySelectorAll("[data-filter]").forEach((button) => button.addEventListener("click", () => {{
      filter = button.dataset.filter; document.querySelectorAll("[data-filter]").forEach((item) => item.classList.remove("active"));
      button.classList.add("active"); render();
    }}));
    $("search").addEventListener("input", render); render();
    setInterval(() => fetch("/api/report", {{cache: "no-store"}}).then((response) => {{
      if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
      return response.json();
    }}).then((next) => {{ report = next; render(); }})
      .catch(() => {{ $("updated").textContent = "Live refresh unavailable · showing last snapshot"; }}), 5000);
  </script>
</body>
</html>"""


def serve_report(report_path: Path | str, *, host: str = "127.0.0.1", port: int = 8765) -> None:
    """Serve a report locally; the report file is re-read on every request."""

    path = Path(report_path).expanduser().resolve()
    load_report(path)

    class ReportHandler(BaseHTTPRequestHandler):
        def _send(self, body: bytes, content_type: str) -> None:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
            route = urlsplit(self.path).path
            if route == "/":
                body = dashboard_html(load_report(path)).encode("utf-8")
                self._send(body, "text/html; charset=utf-8")
            elif route == "/api/report":
                body = json.dumps(load_report(path), ensure_ascii=True).encode("utf-8")
                self._send(body, "application/json; charset=utf-8")
            else:
                self.send_error(404, "Not found")

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer((host, port), ReportHandler)
    print(f"Pinocchio dashboard: http://{host}:{server.server_port}")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    finally:
        server.server_close()
