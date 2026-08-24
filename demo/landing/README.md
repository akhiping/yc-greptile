# Pinocchio Landing Harness

Run the local YC demo page:

```powershell
cd demo/landing
npm install
npm run build
cd ..\..
python demo/landing/server.py
```

Open `http://127.0.0.1:8797/`.

## Render

This folder is deployable through the root `render.yaml` Blueprint:

- Runtime: Python
- Build command: `pip install -r pinocchio/requirements.txt`
- Start command: `python demo/landing/server.py`
- Health check: `/api/status`

The modern frontend source lives in `demo/landing/src` and is built with Vite,
React, and TypeScript. The compiled `demo/landing/dist` bundle is committed so
the Render Python service can serve the demo even when the hosted build image has
no Node toolchain.

The browser UI can stream the existing terminal demos:

- `Play caught-cheat reel` runs `python demo/landing/harness_demo.py caught-cheat`
- `Run verifier` arms `.demo-target` and writes `.pinocchio/live-report.json`
- `Dry loop` runs the loop without calling Codex
- `Live Codex loop` arms `.demo-target` and runs the existing Codex loop once,
  falling back to the recorded caught-cheat reel when the Codex CLI is not
  installed in the hosted runtime.

Computer Use safety rules forbid automating terminal apps or the Codex CLI through Windows UI automation, so this page acts as a local browser harness around the terminal commands instead.
