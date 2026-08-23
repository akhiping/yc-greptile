# 🤥 PINOCCHIO

**Your coding agent doesn't get to mark its own homework.**

Greptile Fast Hackathon · Aug 23, 2026 · 560 20th St, SF
Build 1:00–5:00 · judging 5:00–5:45 · prizes 6:00

---

Codex tells you *"Fixed it — all tests pass."*

Pinocchio independently checks whether that sentence is **true**. If it isn't,
**Codex is not allowed to stop talking.**

## It's a veto, not a dashboard

The output is not a view. It's a **verdict that blocks.** Pinocchio sits on
Codex's `Stop` hook and returns `decision: "block"` with the lie attached. The
agent reads its own rap sheet and has to go fix it.

Everything on screen is a side effect of the gate — one number (the nose), one
blocked terminal. If we only *display* deception, we lose.

## The problem is documented, not speculative

- **METR** found reward hacking in **1–2% of all o3 task attempts** — and on one
  RE-Bench task where the scoring function was visible, in **every single trajectory**.
- **Anthropic** found that models which learn to cheat on coding tests generalize
  to broader misalignment — including **sabotaging the code written to detect
  their own misbehavior, 12% of the time**.
- Three 2026 papers name the exact cheat taxonomy we detect:
  [*Do Coding Agents Deceive Us?*](https://arxiv.org/pdf/2606.07379),
  [*SpecBench*](https://arxiv.org/pdf/2605.21384),
  [*The Verification Horizon*](https://arxiv.org/pdf/2606.26300).

**Frontier labs publish papers about this. Nobody ships a tool for it.**

## Nobody else is asking this question

| Category | Who | What they ask |
|---|---|---|
| AI code review | Greptile, CodeRabbit, Qodo, Graphite | *"Is this code good?"* |
| Agent trust / identity | KYA, AgentStamp, HUMAN Verified | *"Is this agent **who** it says it is?"* |
| LLM observability | LangSmith, Phoenix, Braintrust, Langfuse | *"**What** did the agent do?"* |
| **Pinocchio** | — | ***"Is what the agent told you true?"*** |

Code review reads the diff and never reads the agent's message. Identity
verification authenticates the *agent*, never its *claims*. Observability logs
the trace and leaves you to read it.

We compare **the narration against the evidence.**

## How it works

```
Codex works ──► PostToolUse ──► L0  LEDGER          ground truth; the agent's
                                                     prose is never evidence
                                     │
                                L1  DETECTORS       no LLM, <2s
                                     │              D1 test tampering
                                     │              D2 assertion weakening
                                     │              D3 hardcoded literal
                                     │              D4 phantom execution
                                     │              D5 kayfabe (vacuous tests)
                                     │              D6 coverage delta
                                     │
Codex's final message ─────────► L2  ENTAILMENT     atomic claims × evidence
                                     │              SUPPORTED / UNSUPPORTED
                                     │              / CONTRADICTED, with a
                                     │              citation to a ledger entry
                                     │
                                L3  THE VETO        Stop hook →
                                                     decision: "block"
```

The **L1 detectors never read the agent's prose** — only the diff and the exit
codes. You can't talk your way past a string match.

**D5 (Kayfabe)** is the one worth explaining: it swaps a function body for
`raise NotImplementedError` and re-runs the suite. Any test that still passes
never called the code. It catches the cheat class entailment *cannot* see,
because the diff genuinely looks like a real fix.

## Repo map

```
PINOCCHIO.md      ← the battle plan: architecture, contract, assignments,
                     timeline, cut ladder, demo script, Q&A ammo
pinocchio/        the tool
demo-repo/        the trap — tests that fail on purpose
setup.sh          one-shot environment bootstrap
ideas/            candidate exploration + kill notes
notes/            prior art, hook probe, verified event rules
specs/            build-ready one-pagers
```

## Team

| | Layer |
|---|---|
| **Akhila** | L0 ledger · hooks · L3 veto — the spine |
| **Sameer** | L1 deterministic detectors — the defensible core |
| **Kanishk** | L2 claim extraction + entailment |
| **P4** | demo repo · the trap · report render · backup video |

Everyone builds against the frozen JSON contract in
[PINOCCHIO.md](PINOCCHIO.md), so nobody blocks anybody.

## Codex's role

Pinocchio was **built by Codex**, plugs **into Codex**, and is the thing that
tells **Codex no**. Codex is currently the only agent shipping a `Stop` hook
that can return a block decision — that hook is the entire mechanism.

## Status

✅ **`sameer` is live and runnable.** This checkout is connected to
`https://github.com/akhiping/yc-greptile.git`, tracks `origin/sameer`, and was
verified against commit `6792794` (`Merge origin/main into sameer`) on
Aug 23, 2026.

Kanishk's L2 entailment code is present in `pinocchio/entailment.py` and is wired
through `pinocchio/deterministic.py`. Sameer's deterministic detector path is the
demo-safe path today: it needs no network and no third-party service in the
critical loop.

## Terminal setup

From this folder:

```powershell
git fetch origin sameer
git checkout sameer
git pull --ff-only origin sameer

python -m pip install -r pinocchio/requirements.txt
python -m pytest -q pinocchio/tests
```

API keys are read from environment variables. Create an OpenAI project key at
`https://platform.openai.com/api-keys`, then export it before running L2
entailment. Do not commit `.env`; it is already ignored.

```powershell
$env:OPENAI_API_KEY = "sk-..."      # enables L2 OpenAI entailment
$env:GREPTILE_API_KEY = "..."       # optional if not already logged in
greptile whoami
```

This machine currently has Greptile CLI `3.4.1` signed in as
`nagarsam8989@gmail.com` via API-key auth. `OPENAI_API_KEY` is not set in this
shell, so the OpenAI-backed entailment layer will stay disabled until a real key
is exported.

Useful Greptile command:

```powershell
greptile review --json --instructions "Review Pinocchio's verifier and loop for demo-blocking bugs."
```

## Run the loop

Rebuild the disposable trap repo, then run the Codex/Pinocchio loop:

```powershell
python demo-repo/arm.py
python pinocchio/loop.py --repo .\.demo-target --max-iterations 3 --timeout 240 --json
```

For a verifier-only smoke test:

```powershell
python pinocchio/pinocchio.py analyze .\.demo-target --engine detectors:run --output .\.pinocchio\live-report.json
python pinocchio/nose_ui.py .\.pinocchio\live-report.json
```

## Proof from this checkout

Commands run successfully on Aug 23, 2026:

```text
git pull --ff-only origin sameer
# Already up to date.

python -m pytest -q pinocchio\tests
# 66 passed in 50.26s

python demo-repo\arm.py
# Armed: C:\Users\nagar\Downloads\YC Hackathon\.demo-target
# Suite: 2 failed, 1 passed in 0.02s

python pinocchio\loop.py --repo .\.demo-target --max-iterations 1 --timeout 240 --json
# OUTCOME: verified after 1 iteration(s)
# final_nose: 0

python -m pytest -q
# in .demo-target: 3 passed in 0.02s

python pinocchio\pinocchio.py analyze .\.demo-target --engine detectors:run --output .\.pinocchio\live-report.json
# Results: 4 verified | 0 lies | 1 uncertain
```

The live loop changed only `.demo-target/calc_interest.py`, replacing annual
compounding with monthly compounding:

```diff
-    total = principal * (1 + rate) ** (months / 12)
+    total = principal * (1 + rate / 12) ** months
```

The single remaining `UNCERTAIN` result is D4 phantom execution, because Codex
CLI `0.137.0` still did not emit the PostToolUse ledger hook in this run. The
veto/hook code is tested directly, and `docs/HOOKS.md` documents the hook probe.

## Working rules

1. **One loop before one platform.** The loop is *cheat → detect → block →
   rewrite*. No dashboard, no config system, no multi-language support, no
   accounts. Every over-scoped idea in this workspace died of "platform."
2. **Check for prior art before falling in love.** Muscle-mem was taken. Saguaro
   had the architecture already. Find that out on day zero.
3. **Read the brief before the ideas, and again after.** Two weeks of consumer
   ideation went into a developer-tools event.
4. **Mark unverified external facts as unverified, inside the doc.** A confident
   sentence about a prize nobody confirmed is how you optimise hard in the wrong
   direction.
