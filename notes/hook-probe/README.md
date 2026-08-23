# Codex hook probe — run this at 1:00pm, takes 60 seconds

Diagnostic only. Lives outside the `kayfabe` repo on purpose, so nothing here
counts as pre-building the product.

## What it settles

My sources contradict each other on three things, and each one can quietly kill a
build plan:

| Question | Official docs | Third-party reference |
|---|---|---|
| Feature flag | Hooks run **by default**; `[features] hooks = false` disables | You must set `[features] codex_hooks = true` or hooks are **silently ignored** |
| `PreToolUse`/`PostToolUse` coverage | Bash + `apply_patch` (Edit/Write) + MCP tools + local function tools | **Bash only, by design** |
| Payload shape | `session_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`, `tool_name`, `tool_input`, `tool_use_id` | points upstream |

Silent failure is the dangerous case. Test, don't trust.

## Install

Codex has no `~/.codex/hooks.json` yet, so you can drop this in whole. From Git Bash:

```bash
cp "C:/Users/nagar/Downloads/YC Hackathon/notes/hook-probe/hooks.json" ~/.codex/hooks.json
```

If you'd rather not touch the global config, put it in the repo instead —
`kayfabe/.codex/hooks.json` — which is also the more realistic test, since that's
where the real hook will ship.

## Run

1. Start Codex in the `kayfabe` repo.
2. **Trust the hooks.** Non-managed hooks require explicit trust by hash before
   they run — use the `/hooks` command. Editing a hook re-triggers this, so
   re-trust after any change. This is the thing most likely to ambush you
   mid-demo.
3. Do exactly three things:
   - send any prompt  → tests `UserPromptSubmit`
   - let it run a shell command (e.g. ask it to run `pytest`) → tests Bash
   - **let it edit a file** → this is the one that matters
4. Let the turn finish → tests `Stop`.

## Read the result

```bash
cd "C:/Users/nagar/Downloads/YC Hackathon/notes/hook-probe"
python -c "import json;[print(json.loads(l)['event'], '|', json.loads(l)['tool_name']) for l in open('probe-log.jsonl')]"
```

### Decision table

| What you see | What it means | Do this |
|---|---|---|
| `probe-log.jsonl` never appears | Hooks silently ignored | Add `[features] codex_hooks = true` to `~/.codex/config.toml`, restart, retry. If still nothing, try `[features] hooks = true`. |
| Log has events, but no `PreToolUse` with a non-Bash `tool_name` | **Bash-only coverage** | Blast Radius and Parallel Universe are dead. Kayfabe is fine — it triggers on `Stop`, not on edits. |
| `PostToolUse` fires with `tool_name` = `apply_patch`/`Edit`/`Write` | Full coverage | Everything on the slate is open. |
| `Stop` event present | The veto mechanism works | Build Kayfabe. |

**The `Stop` line is the one that matters.** Kayfabe's entire mechanism is a
`Stop` hook returning `decision: "block"`. If `Stop` fires, you have a project.

## Cleanup before the demo

```bash
rm ~/.codex/hooks.json
```

Don't demo with the probe still wired in — it logs every payload to disk and adds
a hook invocation to every tool call.
