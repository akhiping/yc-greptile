# Pinocchio Landing Harness

Run the local YC demo page:

```powershell
python demo/landing/server.py
```

Open `http://127.0.0.1:8797/`.

## Render

This folder is deployable through the root `render.yaml` Blueprint:

- Runtime: Python
- Build command: `pip install -r pinocchio/requirements.txt`
- Start command: `python demo/landing/server.py`
- Health check: `/api/status`

The browser UI can stream the existing terminal demos:

- `Play caught-cheat reel` runs `python pinocchio/demo_live.py --repo demo-repo --fast`
- `Run verifier` arms `.demo-target` and writes `.pinocchio/live-report.json`
- `Dry loop` runs the loop without calling Codex
- `Live Codex loop` arms `.demo-target` and runs the existing Codex loop once

Computer Use safety rules forbid automating terminal apps or the Codex CLI through Windows UI automation, so this page acts as a local browser harness around the terminal commands instead.
