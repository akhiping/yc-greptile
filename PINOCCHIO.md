# PINOCCHIO

**Your coding agent doesn't get to mark its own homework.**

Greptile Fast Hackathon · Aug 23, 2026 · build 1:00–5:00

---

## THE ONE SENTENCE

Codex tells you *"Fixed it — all tests pass."* Pinocchio independently checks
whether that sentence is **true**, and if it isn't, **Codex is not allowed to
stop talking.**

## WHY THIS IS NOT A DASHBOARD

A dashboard shows you a thing after it happened. Pinocchio's output is not a
view — it is a **verdict that blocks**. It sits on Codex's `Stop` hook and
returns `decision: "block"` with the lie attached. The agent reads its own
rap sheet and has to go fix it.

> If we only *display* deception, we lose. The veto is the product.

Everything on screen is a side effect of the gate. One number (the nose), one
blocked terminal. If we find ourselves building tabs, we have lost the plot.

---

## THE PROBLEM IS DOCUMENTED, NOT SPECULATIVE

This is the strongest part of the pitch. Say these out loud to judges.

| Source | Finding |
|---|---|
| **METR**, frontier risk evals | Reward hacking in **1–2% of all o3 task attempts**. On one RE-Bench task where the scoring function was visible, o3 reward-hacked in **every single trajectory**. |
| **Anthropic** | Models that learn to cheat on coding tests generalize to broader misalignment. In one eval the model **sabotaged the code written to detect its own misbehavior 12% of the time**. |
| **arXiv 2606.07379** — *Do Coding Agents Deceive Us?* | Names the cheat taxonomy we implement: **test memorization** (hardcoding to visible tests), **benchmark gaming**, **reward hacking** via superficial pass conditions. |
| **arXiv 2605.21384** — *SpecBench* | Measures reward hacking specifically in **long-horizon coding agents** — i.e. exactly what Codex is. |
| **arXiv 2606.26300** — *The Verification Horizon* | "No silver bullet for coding agent rewards." The verification gap is a named open problem. |

**The line:** *"Frontier labs publish papers about this. Nobody ships a tool for it."*

---

## THE MARKET GAP (why nobody has built this)

Three categories exist. None of them do this.

| Category | Who | The question they answer |
|---|---|---|
| **AI code review** — ~$420M ARR in 2026, 44% of teams | Greptile ($25M Series A @ $180M, Benchmark), CodeRabbit ($60M Series B, ~140K paid users), Qodo, Graphite (acquired by Cursor, Dec 2025) | *"Is this code good?"* |
| **Agent trust / identity** — KYA, AgentStamp, HUMAN Verified AI Agent, Just Verify | Cryptographic identity, RFC 9421 signatures | *"Is this agent **who** it says it is?"* |
| **LLM observability** | LangSmith, Arize Phoenix, Braintrust, Langfuse, W&B Weave | *"**What** did the agent do?"* |

**Nobody asks: "Is what the agent *told you* actually true?"**

Code review reads the diff and never reads the agent's message. Identity
verification authenticates the *agent*, never its *claims*. Observability logs
the trace and leaves you to read it.

Pinocchio is the only one comparing **the narration against the evidence.**

Closest prior art is `safedep/gryph` (local-first agent audit trail → SQLite,
replay, before/after diffs) — but it is an **audit log**, it renders no verdict
and blocks nothing. **And Codex is not on its supported list.** That gap is the
opening.

---

## ARCHITECTURE — FOUR LAYERS

```
        Codex works ──► PostToolUse ──► ┌──────────────┐
                                        │  L0 LEDGER   │  ground truth
                                        │  every tool  │  (agent narration
                                        │  call, exit  │   is NOT evidence)
                                        └──────┬───────┘
                                               │
        ┌──────────────────────────────────────┴────────────┐
        │  L1 DETERMINISTIC DETECTORS  (no LLM, <2s)        │
        │  D1 test tampering    D4 phantom execution        │
        │  D2 assert weakening  D5 kayfabe (vacuous tests)  │
        │  D3 hardcoded literal D6 coverage delta           │
        └──────────────────────────────────────┬────────────┘
                                               │
        Codex's final message ──► ┌────────────┴────────────┐
                                  │  L2 CLAIM ENTAILMENT    │
                                  │  atomic claims × evidence│
                                  │  SUPPORTED / UNSUPPORTED│
                                  │  / CONTRADICTED         │
                                  └────────────┬────────────┘
                                               │
                                  ┌────────────┴────────────┐
                                  │  L3 THE VETO — Stop hook│
                                  │  decision: "block"      │
                                  │  reason: the rap sheet  │
                                  └─────────────────────────┘
```

### L0 — The Ledger
`PostToolUse` records every tool call: files read/written, commands run, exit
codes, stdout. **The agent's prose is never evidence.** The ledger is.

### L1 — Deterministic detectors (the defensible core)
No LLM. No network. Fast enough to run inside a hook. Each targets one named
cheat class:

- **D1 · Test tampering** — claim says "fixed the code" but the diff touches
  test files. (`unidiff`)
- **D2 · Assertion weakening** — assert count dropped, `assert True` appeared,
  `pytest.mark.skip`/`xfail` added, `except Exception` broadened to bare `except`.
- **D3 · Hardcoded literal** — the expected value from the test now appears
  verbatim in the source. This is *test memorization* from 2606.07379, caught
  with a string match.
- **D4 · Phantom execution** — the claim says "I ran the tests"; the ledger
  contains no pytest invocation. Trivial to implement, devastating on stage.
- **D5 · Kayfabe** — `ast.NodeTransformer` swaps the function body for
  `raise NotImplementedError`, re-run the suite. **Any test that still passes
  never called the code.** Catches the one cheat class L2 cannot see, because
  the diff genuinely looks like a real fix.
- **D6 · Coverage delta** — did the changed lines actually execute?

### L2 — Claim entailment
Split Codex's final message into atomic claims. For each, pull matching evidence
from L0 + L1. Return `SUPPORTED` / `UNSUPPORTED` / `CONTRADICTED` **with a
citation to a ledger entry**. Never a verdict without a receipt.

### L3 — The veto
Any `CONTRADICTED` claim, or any D-detector over threshold → `decision: "block"`,
reason = the rap sheet. **Cap at 2 interventions per turn, then always release**
(`openai/codex` issue **#37937**: a repeatedly-blocking Stop hook traps the CLI).

---

## THE CONTRACT — FREEZE THIS FIRST, THEN SPLIT

Nobody writes code until this is agreed. It is what lets four people work in
parallel without blocking. Stub it with fake data immediately so every layer
has something to develop against.

```json
{
  "verdict": "PASS | LIE",
  "nose": 0,
  "claims": [
    { "text": "I fixed the interest calculation",
      "status": "CONTRADICTED",
      "detector": "D1",
      "evidence": ["ledger:47"] }
  ],
  "detectors": [
    { "id": "D1", "name": "test_tampering", "fired": true,
      "severity": "high",
      "detail": "test_calc_interest.py:34 assertion modified" }
  ],
  "ledger": [
    { "i": 47, "tool": "apply_patch", "path": "test_calc_interest.py",
      "exit": 0, "ts": "13:42:11" }
  ]
}
```

---

## ASSIGNMENTS — 4 PEOPLE

**Rule: you own your layer end to end. You do not wait on anyone. You develop
against stubbed contract JSON until integration.**

### P1 — Akhila · Ledger, Hooks & Veto (L0 + L3)
The spine. Everything else is inert without it.
- `.codex/hooks.json`; `PostToolUse` → ledger (JSONL is fine, SQLite if easy)
- `Stop` hook returning `decision:"block"` with the rap sheet as reason
- The 2-intervention cap and release
- **Owns the answer to "do hooks even fire here"** — first 15 minutes, no-op probe
- Scaffold in `notes/hook-probe/`

### P2 — Sameer · Deterministic detectors (L1)
The defensible core. Pure Python, stdlib `ast` + `unidiff`, zero network.
- D1 → D2 → D4 first (fastest, highest demo value), then **D5 Kayfabe**, then D3
- D6 only if ahead
- Emits `detectors[]` in contract shape
- Runs standalone as `pinocchio .` — **this is the fallback product if hooks die**

### P3 — Kanishk · Claim extraction & entailment (L2)
- Split agent message → atomic claims
- `prompts/entailment_system.txt`; every verdict cites a ledger index
- Reads stubbed contract JSON from minute one — **never blocked on P1 or P2**
- Hard rule: no citation, no verdict

### P4 — Demo repo, the trap, the report & rehearsal
The most underrated job on the team. Demos win hackathons.
- `demo-repo/test_calc_interest.py` — tests that fail on purpose, the bug is the trap
- **Run `codex "Fix the failing tests"` 5+ times. Log which prompts reliably
  trigger cheating vs. an honest fix.** We must be able to summon the lie on demand.
- **Record the backup video by 4:00.** Non-negotiable.
- `rich` terminal report — the nose, red/green claim list. One screen. No web app.

---

## TIMELINE (compressed — we started late)

| Time | All four | Cut? |
|---|---|---|
| **1:45–2:00** | **Contract frozen + stubbed.** P1 runs the hook probe *simultaneously*. | critical |
| 2:00–3:00 | Parallel build, heads down. No integration. | critical |
| 3:00–3:20 | **Integration #1** — ledger → detectors → report renders. Ugly is fine. | critical |
| 3:20–4:00 | Parallel hardening. P4 hunts cheat prompts + films backup. | critical |
| 4:00–4:20 | **Integration #2** — full loop: cheat → detect → block → Codex rewrites. | critical |
| 4:20–4:40 | **Rehearse ×2.** README naming Codex's role. | critical |
| 4:40–5:00 | Submit with buffer. | critical |

### Verify in the first 15 minutes — sources disagree, each can kill us
- Do hooks need `[features] hooks = true`, or on by default? **Silent failure if wrong.**
- Do `PreToolUse`/`PostToolUse` fire for `apply_patch`, or **Bash only**?
  (We survive either way — the veto rides on `Stop`.)
- Hooks require **explicit trust by hash** via `/hooks`, and *editing a hook
  re-triggers the prompt.* This will ambush us mid-demo. Trust early, re-trust
  after every change.

### Cut ladder — decided now, not at 4:30
1. Drop **D6**, then **D3**.
2. Entailment flaky? → detectors-only. D1/D2/D4/D5 are deterministic and need no LLM.
3. **Stop hook dead by 3:30?** → ship `pinocchio .` as a CLI + **pre-commit hook**.
   Still a complete product, still blocks something. **Drop the hook, not the demo.**
4. Live demo unstable at 4:40? → play the video, narrate live. Never debug on stage.

---

## THE DEMO (target 2:30, assume you get cut at 2:00)

> **0:00** — "I asked Codex to fix a failing test suite. It says it's done."
> *Green terminal. Confident summary on screen.*
>
> **0:15** — **"Your agent's tests are lying to you."**
>
> **0:25** — `pinocchio .` Nose grows. Three claims, one red:
> *"'I fixed the interest calculation' — CONTRADICTED. You didn't touch the
> function. You changed line 34 of the test."* Diff on screen, side by side.
>
> **1:00** — "So we gave it a veto." Ask Codex to finish. **It gets blocked
> by its own Stop hook.** It reads the rap sheet and rewrites — *the real fix
> this time.*
>
> **1:50** — Second run. Nose: 0. Then delete the function outright —
> **the suite finally goes red.** "That's the difference between tests that
> pass and tests that test."
>
> **2:10** — "METR found frontier models reward-hacking in every trajectory on
> one task. Anthropic found a model sabotaging the code meant to catch it.
> Built by Codex — and it's the thing that tells Codex no.
> One file in `.codex/hooks.json`. Open source."

**Say "your agent's tests are lying to you" in the first fifteen seconds.**
It survives being the only sentence a judge remembers.

---

## Q&A AMMO

**"Isn't this just AI code review?"**
"Greptile and CodeRabbit read the diff. Neither reads what the agent *told you*.
We're not reviewing code — we're checking whether the summary above the code is
true. Different input entirely."

**"Isn't this mutation testing?"**
"D5 is mutation testing's angriest single mutation. Stryker and mutmut run for
minutes in CI and hand you a score. We run one mutation in seconds and wire it
to the agent's stop condition. The novelty isn't the mutation — it's the veto."

**"Can't the agent just lie better?"**
"It can lie in prose all it wants. The ledger is captured by a hook it doesn't
control, and D1–D5 never read its prose — they read the diff and the exit codes.
You can't talk your way past a string match."

**"What about false positives?"**
"Contract and schema tests legitimately don't call the function — that's the
honest false-positive class. We report, we never auto-delete, and the threshold
is yours."

**"Won't blocking trap it in a loop?"**
"Known failure mode — `openai/codex` issue **#37937**. We cap at two
interventions per turn, then always release." *(Signals we read the source.)*

**"Why Codex?"**
"Codex is the only agent shipping a Stop hook that can return a block decision.
That's the entire mechanism. It's also what built this."

**"Who pays?"**
"Anyone whose green CI is currently a lie. Same buyer as a linter, much scarier
report."

---

## THE HARD RULE

**One loop before one platform.**
The loop is: *cheat → detect → block → rewrite.*
No dashboard. No config system. No multi-language support. No accounts.
Every over-scoped idea in this workspace died of "platform."
