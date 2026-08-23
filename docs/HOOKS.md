# Codex hooks: what we actually found

Tested against **codex-cli 0.137.0** on Windows 11, 2026-08-23. The probe in
`notes/hook-probe/` had never been run, so all three questions were still open
at 2:45pm. Here are the answers, and what we shipped instead.

## Q1 — Do hooks need a feature flag? **No.**

```
$ codex features list | grep hook
hooks                stable             true
plugin_hooks         removed            false
```

`hooks` is stable and on by default. The third-party claim that you must set
`[features] codex_hooks = true` is **wrong for this version**. Note that
`plugin_hooks` is `removed`, which matters for Q2.

## Q2 — Does `PostToolUse` fire? **Not from any config location we could find.**

We ran `codex exec --dangerously-bypass-hook-trust --full-auto` against an armed
demo repo with an identical hook config written to **four** locations at once,
each labelled so the ledger would record which one fired:

| Location | Fired |
|---|---|
| `<project>/.codex/hooks.json` | ✗ |
| `<project>/.codex/settings.json` | ✗ |
| `<project>/.codex/settings.local.json` | ✗ |
| `<project>/.codex/hooks/hooks.json` | ✗ |
| `~/.codex/settings.json` | ✗ |

No ledger was written, and **no error or warning was printed**. This is the
silent-failure mode the probe README warned about.

What we know from strings in the binary:

- The payload shape we assumed is right — `matcher`, `statusMessage`,
  `hookEventName`, and the event names `PreToolUse`, `PostToolUse`, `Stop`,
  `SessionStart`, `UserPromptSubmit` are all present.
- The binary references `settings.json`, `settings.local.json`,
  `disableAllHooks`, and `permissionMode` together — so this build has moved to
  a **`settings.json`-style** hook configuration, not the `hooks.json` the
  earlier research described.
- The one `hooks/hooks.json` reference sits next to `plugin.json` and
  `core-plugins\src\loader.rs`, i.e. it belongs to the **plugin** loader — and
  `plugin_hooks` is a `removed` feature.

**Unresolved:** the exact discovery path, and whether `codex exec` runs hooks at
all (the demo script uses interactive `codex`, which we could not drive
non-interactively). Someone should try the same config with the interactive TUI.

## Q3 — Does `Stop` fire? **Unverified**, for the same reason.

## What we shipped instead

The veto logic is **done and tested** — it just needs a trigger that fires.
`pinocchio/hooks.py` implements both `PostToolUse` (the ledger) and `Stop`
(the block) against the documented payload shape, and its tests drive it
exactly the way Codex would, over stdin. **If hooks start firing, it works with
no changes.**

For a trigger we control completely, `pinocchio/gate.py` installs the same veto
as a **git pre-commit hook**:

```bash
python pinocchio/gate.py install ./.demo-target
```

The cheat then cannot reach a commit:

```
  PINOCCHIO BLOCKED THIS COMMIT.
  Nose length 16.

  1. [D1_test_tampering  severity 8/10]
     Evidence: No implementation file changed. Every edit lands in test
     files: test_calc_interest.py:5 assertion modified...
```

An honest fix commits normally. `PINOCCHIO_BYPASS=1 git commit` overrides it,
the way `--no-verify` would.

This is the cut ladder's step 3, taken deliberately and early rather than at
4:30: **drop the hook, not the demo.** We still block something real.

## Rules the hook layer keeps either way

1. **It never crashes the agent.** Every failure path prints `{}` and exits 0.
   A verifier that wedges Codex is worse than no verifier.
2. **It caps interventions at 2 per session, then always releases**
   (`openai/codex#37937` — a Stop hook that blocks indefinitely traps the CLI).
   Verified by test: block, block, then release forever.
3. **The block reason is a prompt, not a status line.** It carries the evidence
   *and* the instruction. "Blocked" on its own makes the agent flail.

## One real bug worth knowing about

Git Bash sends `cwd` as `/c/Users/...`. Native `git.exe` reads that as a path
relative to the current drive root, so it silently resolved to `C:\c\Users\...`,
**created a junk directory tree there**, and analyzed an empty non-repo instead
of the target. `hooks.py` now normalizes MSYS-style paths on Windows, with a
regression test. If a hook ever reports "nothing contradicted" when you know the
tree is dirty, check which directory it actually looked at.
