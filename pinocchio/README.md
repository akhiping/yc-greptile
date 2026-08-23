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
