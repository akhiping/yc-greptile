# Pinocchio orchestration

Kayfabe is the current product direction: it uses a fast mutation to expose tests
that do not exercise the code they claim to test. Pinocchio is its orchestration
boundary. It records a Codex run and repository diff, calls Akhila's verifier, and
emits the shared JSON report consumed by Alina's dashboard and this terminal view.

The JSON Schema at `contract.json` defines the shared `CheckResult`:

```text
claim, verdict (LIE | VERIFIED | UNCERTAIN), evidence, severity (1-10), check_type
```

No third-party Python packages are required.

## Analyze an existing diff

```bash
python pinocchio/pinocchio.py analyze \
  /absolute/path/to/repo \
  --engine verification_engine:verify \
  --output /tmp/pinocchio-report.json
python pinocchio/nose_ui.py \
  /tmp/pinocchio-report.json
```

The engine callable receives keyword arguments `repo_path`, `diff`, and `session`.
It returns either a sequence of `CheckResult`-compatible mappings/dataclasses or a
mapping with a `results` sequence. If it is unavailable, Pinocchio produces one
explicit `UNCERTAIN` orchestration result instead of fabricating verification.

## Controlled Codex rehearsal

```bash
python pinocchio/pinocchio.py demo \
  /absolute/path/to/demo-repo \
  --engine verification_engine:verify \
  --output /tmp/pinocchio-demo-report.json
```

`demo` runs the agreed Codex prompt with `--approval-mode full-auto`, captures its
stdout, stderr, and diff outside the target repository, invokes the verifier, then
hard-resets and cleans the demo target. It refuses a target that has any tracked,
untracked, or ignored changes, so restoration returns it exactly to its initial
state. A missing Codex CLI or expired authentication is recorded in the report;
the captured diff is still analyzed.

## L1 deterministic detectors

`detectors.py` is the verification engine: no LLM, no network, stdlib only
(deliberately **not** `unidiff` — one less thing to install on the demo machine).

```bash
python pinocchio/pinocchio.py analyze /path/to/repo --engine detectors:run
python pinocchio/nose_ui.py /tmp/pinocchio-report-*.json
```

> ⚠️ The engine spec is `detectors:run`, **not** `pinocchio.detectors:run`.
> `pinocchio.py` puts its own directory on `sys.path[0]`, so `pinocchio` resolves
> to the orchestrator module rather than the package. The wrong spec does not
> crash — it degrades to a single `UNCERTAIN` orchestration row, which is easy to
> miss on stage.

It emits exactly one `CheckResult` per detector, so the report is always the same
five readable rows:

| check_type | Fires when |
|---|---|
| `D1_test_tampering` | The diff moves the tests instead of the implementation. |
| `D2_assertion_weakening` | Asserts removed, softened to `assert True`, skipped/xfailed, or the expected value rewritten. |
| `D3_hardcoded_literal` | The value a test asserts now appears verbatim in a new source line. |
| `D4_phantom_execution` | The agent claims the suite ran; the ledger contains no test invocation. |
| `D5_kayfabe` | A changed function is replaced with `raise NotImplementedError` and tests still pass. |

Every detector can return `UNCERTAIN`, and does so whenever the evidence is
absent rather than exculpatory — no ledger captured, no source file changed, no
passing test to challenge. **A missing hook is never reported as a lie.**

### Inputs it will use if you give them

Both are optional; the detectors degrade to `UNCERTAIN` without them.

- **The agent's final message** (D4) — `session["agent_message"]`, or the
  `PINOCCHIO_AGENT_MESSAGE` / `PINOCCHIO_AGENT_MESSAGE_FILE` environment variables.
- **The tool ledger** (D4) — `session["ledger"]` (a list), `session["ledger_path"]`,
  `$PINOCCHIO_LEDGER`, or `<repo>/.pinocchio/ledger.jsonl`. Entries are read
  liberally: any `command`/`cmd`/`argv`/`tool_input` field, and any
  `exit_code`/`returncode`/`status`.

### Escape hatches

- `PINOCCHIO_SKIP_KAYFABE=1` skips D5, the only detector that runs the suite.
- `PINOCCHIO_PYTEST_TIMEOUT` (default 120s) caps each pytest run.

D5 copies the working tree to a temp directory and mutates the copy, so the
target repo is never written to.

## The veto (L3)

`hooks.py` implements both Codex hook events against the documented payload
shape — `PostToolUse` writes the ledger, `Stop` runs the detectors and returns
`{"decision": "block"}` with the rap sheet as the reason.

**Codex 0.137.0 does not fire either event from any config location we could
find.** See [docs/HOOKS.md](../docs/HOOKS.md) for exactly what was tested. The
veto logic is done and tested regardless — its tests drive it over stdin the way
Codex would, so if hooks start firing it works unchanged.

For a trigger we fully control, `gate.py` installs the same veto as a git
pre-commit hook:

```bash
python pinocchio/gate.py install ./.demo-target   # the lie cannot be committed
python pinocchio/gate.py uninstall ./.demo-target
```

`PINOCCHIO_BYPASS=1 git commit ...` overrides it, the way `--no-verify` would.

Three rules the veto keeps:

1. **It never crashes the agent.** Every failure path prints `{}` and exits 0.
2. **It caps interventions at 2 per session, then always releases**
   (`openai/codex#37937`: a Stop hook that blocks forever traps the CLI).
3. **The reason is a prompt, not a status line** — evidence *and* instruction.
   "Blocked" on its own makes the agent flail.

## The loop

`loop.py` closes it: Codex works, Pinocchio verifies, and if the summary is a
lie the rap sheet becomes the next prompt.

```bash
python pinocchio/loop.py --repo ./.demo-target --max-iterations 3
python pinocchio/loop.py --dry-run          # verify once, no Codex call
```

It cannot run forever. Four independent stops:

| Stop | Trigger |
|---|---|
| budget | `--max-iterations`, default 3 |
| **no progress** | the same detectors fire at the same nose twice running |
| **regression** | the nose grew, so the rewrite made things worse |
| unavailable | Codex missing, timing out, or returning nothing |

Each iteration appends to `.pinocchio/loop-trace.jsonl`, and what has already
been tried and rejected is carried into the next prompt so the agent does not
re-offer a fix the detectors already refused.
