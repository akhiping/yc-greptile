# PINOCCHIO — THE PRODUCT

**The verification layer for coding agents.**

Pinocchio checks whether your coding agent actually did what it said it did —
and stops it when it didn't.

---

# PART I — THE 60-SECOND PITCH

*Deliver verbatim. ~160 words, ~60 seconds at speaking pace. The first
sentence is the whole product; everything after it is evidence.*

> **Your coding agent is lying to you.**
>
> Not metaphorically. METR found frontier models reward-hacking in *every single
> trajectory* on a task where they could see the scoring function. Anthropic
> found a model sabotaging the code written to catch it — twelve percent of the
> time.
>
> So when Codex says *"fixed it, all tests pass"* — sometimes it just edited the
> test.
>
> There's four hundred million dollars of ARR in AI code review right now.
> Greptile, CodeRabbit, Qodo. Every one of them reads your **code**. Not one of
> them reads what the agent **told you** and checks whether it's true.
>
> Pinocchio does. We capture every tool call the agent makes, run six
> deterministic detectors across the diff — no LLM, so it can't be talked out of
> it — and test every claim against that evidence.
>
> And when it's lying, we don't show you a dashboard. **We block it.** Pinocchio
> rides Codex's Stop hook, so the agent physically cannot end its turn on a lie.
> It reads its own rap sheet and goes back and does the job properly.
>
> Built by Codex. And it's the thing that tells Codex *no*.

**Delivery notes**
- Land **"your coding agent is lying to you"** in the first five seconds, then pause.
- The METR and Anthropic numbers are the credibility hit — say them slowly.
- **"We don't show you a dashboard. We block it."** is the turn. Everything before
  is a problem everyone half-knows; this is the part they haven't heard.
- Close on the Codex line. It's the laugh, and it satisfies the eligibility rule
  in the same breath.

---

# PART II — THE COMMERCIAL PRODUCT

## Positioning

| | |
|---|---|
| **Category** | Agent verification — a new one, adjacent to code review |
| **One-liner** | Pinocchio verifies your coding agent's claims against what it actually did, and blocks it when they don't match |
| **Wedge user** | The individual dev running Codex or Claude Code who has been burned once |
| **Economic buyer** | The eng leader whose CI is green and whose trust is gone |
| **Category we displace** | None. We're a new row under the existing ones. |

## The four questions

Everyone in this space answers one of these. We're the only one on the fourth.

| Question | Category | Who |
|---|---|---|
| Is this code good? | AI code review | Greptile, CodeRabbit, Qodo, Graphite |
| Is this agent *who* it says it is? | Agent identity | KYA, AgentStamp, HUMAN Verified |
| *What* did the agent do? | LLM observability | LangSmith, Phoenix, Braintrust, Langfuse |
| **Is what the agent *told you* true?** | **Agent verification** | **Pinocchio** |

Code review reads the diff and never reads the agent's message. Identity
verification authenticates the *agent*, never its *claims*. Observability logs
the trace and leaves you to read it yourself.

## Why now

1. **Agentic coding became the default.** Codex, Claude Code, and Cursor moved the
   unit of work from a line to a turn. Nobody reads every diff any more.
2. **Reward hacking scales with capability.** It's not a bug being patched out —
   METR and Anthropic both document it getting *more* sophisticated in stronger
   models.
3. **The buyer already pays for trust in code.** ~$420M ARR, 44% of teams already
   have an AI reviewer in the loop. We're not creating a budget line, we're
   extending one.
4. **The hook surface just opened.** Codex's `Stop` hook returning a block decision
   is what makes enforcement — not just reporting — possible at all.

## Three surfaces, one engine

The same verification core ships three ways. This is the expansion path.

| Surface | Who | When it runs | Business |
|---|---|---|---|
| **1 · CLI** — `pinocchio .` | Individual dev | On demand, after any agent turn | Free, open source. The wedge. |
| **2 · Hook** — `.codex/hooks.json` | Individual dev | Automatically, at `Stop` | Free. The retention mechanic. |
| **3 · CI check** — GitHub Action | Team / org | Every PR containing agent-written code | **Paid.** Where the money is. |

The CLI earns trust, the hook creates habit, and CI is where an org standardises
and pays. Every surface emits the same contract JSON.

## Pricing

| Tier | Price | What |
|---|---|---|
| **Free** | $0, OSS | CLI + hooks, local, single dev, all six detectors |
| **Team** | ~$25/dev/mo | CI check, shared policy thresholds, honesty trend per repo, agent leaderboard |
| **Enterprise** | Custom | Audit export, SSO, on-prem, custom detectors, policy engine, SLA |

The enterprise story is **compliance**: *"prove the AI-written code in this
release was independently verified."* Regulated industries will need that answer
within eighteen months and currently have no way to produce it.

## The moat

The detectors are copyable in a weekend. The moat is what runs *behind* them:

1. **The cheat corpus.** Every blocked lie is a labelled example of agent
   deception in the wild — model, prompt, cheat class, diff. **Nobody is
   collecting this.** METR and Anthropic study it in the lab; we'd have it from
   production. That corpus makes detector N+1, and it compounds.
2. **The honesty rate.** One number per model, per repo, per team. Once teams
   quote it, it becomes the standard measure of agent trustworthiness — and
   whoever defines the metric owns the category.
3. **The integration surface.** Hook configs, ledger format, CI action. Sticky in
   the way linters are sticky: nobody rips out the thing that's blocking bad merges.

**The pitch line:** *"We're the seatbelt, and we're also the crash-test data."*

## Roadmap

| Horizon | Ship |
|---|---|
| **Today, 5:00pm** | CLI + Stop-hook veto + 6 detectors + entailment, Python/pytest |
| **30 days** | GitHub Action, JS/TS via `tree-sitter`, Claude Code + Cursor hooks, honesty trend |
| **6 months** | Cheat corpus + hosted detector updates, policy engine, org dashboard, audit export |

---

# PART III — DETAILED ARCHITECTURE

## Principles

1. **The agent's prose is never evidence.** Claims are the thing under test, not
   the source of truth. Evidence comes only from hooks the agent doesn't control.
2. **Deterministic before probabilistic.** Anything catchable by a string match or
   an AST walk never goes to an LLM. Detectors are fast, explainable, and
   unarguable in Q&A.
3. **No verdict without a receipt.** Every finding cites a ledger index. If we
   can't point at the evidence, we don't render the claim.
4. **Degrade, never crash.** Any layer can fail and the layer beneath still ships a
   usable product.

## System diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                          CODEX SESSION                             │
│   user prompt ──► reasoning ──► tool calls ──► final message       │
└───────┬────────────────────────────────────────────┬───────────────┘
        │ PostToolUse (every call)                   │ Stop
        ▼                                            ▼
┌──────────────────┐                        ┌─────────────────────┐
│  L0  LEDGER      │                        │  L3  THE VETO       │
│  append-only     │                        │  nose > threshold?  │
│  JSONL           │                        │   → decision:block  │
│  tool, path,     │                        │   → reason: sheet   │
│  cmd, exit,      │                        │  cap 2/turn         │
│  stdout hash     │                        └──────────▲──────────┘
└────────┬─────────┘                                   │
         │                                             │
         │            ┌──────────────────┐             │
         ├───────────►│  L1  DETECTORS   │─────────────┤
         │            │  D1..D6, no LLM  │  detectors[]│
         │            │  pure functions  │             │
         │            └──────────────────┘             │
         │                                             │
         │            ┌──────────────────┐             │
         └───────────►│  L2  ENTAILMENT  │─────────────┘
      + final message │  claims × evidence│  claims[]
                      │  cites ledger idx │
                      └──────────────────┘
                                │
                                ▼
                      ┌──────────────────┐
                      │  REPORT (rich)   │  the nose, red/green
                      │  contract JSON   │  one screen
                      └──────────────────┘
```

## L0 — The Ledger

Append-only JSONL at `.pinocchio/ledger.jsonl`, one line per tool call, written
by the `PostToolUse` hook. Ordering is the index; the index is the citation.

```json
{ "i": 47,
  "ts": "13:42:11.204",
  "turn": 3,
  "tool": "apply_patch",
  "path": "demo-repo/test_calc_interest.py",
  "cmd": null,
  "exit": 0,
  "added": 2, "removed": 2,
  "stdout_sha": "e3b0c442..." }
```

**Design notes**
- JSONL, not SQLite — append-only survives a crash mid-turn, and `tail -f` is a
  debugging tool for free. SQLite only if there's spare time.
- Store `stdout_sha`, not stdout, for anything large. We need to prove *that* a
  command ran and *what it returned*, not keep megabytes.
- `turn` is what scopes a verification pass. One `Stop` = one turn = one verdict.
- **Snapshot the pre-turn git state** at the first `PostToolUse` of a turn. The
  whole of L1 is a before/after comparison, and without the "before" we have nothing.

## L1 — Deterministic detectors

Six pure functions: `(ledger, diff, before_tree, after_tree) → Finding | None`.
No network, no LLM, no shared state. Each is independently testable and
independently cuttable.

### D1 · Test tampering `severity: high`
- **Signal** — claim asserts a *source* fix; the diff only touches *test* files.
- **Method** — partition changed paths via `unidiff` into test/source using
  `test_*.py`, `*_test.py`, `tests/`. Fire when source-changed = 0 and
  test-changed > 0.
- **False positive** — a genuinely wrong test being legitimately corrected. Mitigated
  by only firing when the claim says the *code* was fixed.

### D2 · Assertion weakening `severity: high`
- **Signal** — the suite got easier to pass rather than the code getting more correct.
- **Method** — AST-diff test files before vs after. Count `ast.Assert` nodes;
  flag added `pytest.mark.skip` / `xfail`, `assert True`, self-comparisons
  (`assert x == x`), bare `except:`, and function bodies replaced with `pass`.
- **False positive** — a refactor consolidating several asserts into one. Report the
  per-test delta so a human can see which it is.

### D3 · Hardcoded literal — *test memorization* `severity: high`
- **Signal** — the expected value from the test now appears verbatim in the source.
  This is the cheat class named in arXiv 2606.07379.
- **Method** — extract literals from the right-hand side of test assert comparisons.
  Check whether each now appears in the changed source lines on a return path.
- **False positive** — legitimately constant values. Mitigated by requiring the literal
  to be **newly introduced in this diff** *and* on a return path.

### D4 · Phantom execution `severity: critical`
- **Signal** — the claim says the tests were run; the ledger says they weren't.
- **Method** — claim mentions running/passing tests → scan this turn's ledger for a
  `pytest` / `npm test` / `go test` invocation. None found → `CONTRADICTED`.
- **False positive** — near zero. **Cheapest detector to build, most devastating on
  stage.** Build this one first.

### D5 · Kayfabe — vacuous tests `severity: high`
- **Signal** — tests that pass without ever calling the code they claim to test.
- **Method** — for each function touched in the diff:
  `ast.NodeTransformer` swaps the body for `raise NotImplementedError` →
  `ast.unparse` → write to a temp copy of the tree → run the suite → diff the pass
  sets. Any test still green never called the function.
- **Output** — `theatre_score = vacuous_tests / total_tests`.
- **Why it matters** — this is the one cheat class **L2 cannot see**, because the diff
  genuinely looks like a real fix. Entailment reads it as honest; only execution
  proves otherwise.
- **Perf** — one mutation per changed function, cap at N=5, hard timeout. It must fit
  inside a hook.
- **False positive** — contract and schema tests legitimately don't call the function.
  This is the honest FP class; name it before a judge does.

### D6 · Coverage delta `severity: medium` — *cut first*
- **Signal** — the changed lines never executed during the run.
- **Method** — `coverage.py` over the suite, intersect executed lines with diff hunks.
- **Cost** — adds a dependency and a full instrumented run. Only if ahead at 4:00.

## L2 — Claim entailment

**Input** the agent's final message + `ledger[]` + `detectors[]`
**Output** `claims[]`, each with a status and a citation.

Three stages:

1. **Extract** — split the final message into atomic, checkable claims. Discard
   hedges and pleasantries. *"I fixed the interest calculation and all 12 tests
   pass"* → two claims.
2. **Route** — match each claim to evidence. Claims about *running* things resolve
   against the ledger; claims about *changing* things resolve against the diff and
   the detectors. **A claim a detector already fired on is decided
   deterministically — the LLM never gets a vote it doesn't need.**
3. **Adjudicate** — only genuinely ambiguous claims reach the model, with the
   relevant evidence inlined.

```json
{ "text": "I fixed the interest calculation",
  "status": "CONTRADICTED",
  "detector": "D1",
  "evidence": ["ledger:47"],
  "why": "No source file changed this turn. The only edit was to the assertion on test_calc_interest.py:34." }
```

**Hard rule: no citation, no verdict.** A claim we can't tie to a ledger index is
reported `UNVERIFIED`, never guessed at. Volunteering the limit is worth more in
Q&A than a fabricated confidence score.

## L3 — The veto

```json
{ "decision": "block",
  "reason": "PINOCCHIO — 1 contradicted claim\n\n  ✗ \"I fixed the interest calculation\"\n    D1 test_tampering — no source file changed.\n    Only edit: test_calc_interest.py:34, assertion modified.\n\nFix the function, not the test." }
```

- **Trigger** — any `CONTRADICTED` claim, or any detector at `severity: critical`.
- **The reason string is a prompt.** Codex reads it as instruction, so it must state
  the evidence *and* the corrective action. "Blocked" alone causes flailing;
  "fix the function, not the test" causes a fix.
- **Cap at 2 interventions per turn, then always release.** `openai/codex` issue
  **#37937** — a repeatedly-blocking Stop hook traps the CLI. A tool that
  softlocks the agent is worse than no tool.
- ⚠️ **Verify the exact hook contract in the first 15 minutes.** Sources disagree on
  whether hooks need `[features] hooks = true`, whether `PostToolUse` fires for
  `apply_patch` or Bash only, and hooks require **trust-by-hash via `/hooks`** which
  **re-triggers on every hook edit.** That last one will ambush the demo.

## Repo layout

```
pinocchio/
  cli.py              `pinocchio .` — entry point, renders the report
  ledger.py           L0 append + query + turn scoping
  detectors/
    __init__.py       registry; each detector is a pure function
    d1_tampering.py   d4_phantom.py
    d2_weakening.py   d5_kayfabe.py
    d3_hardcoded.py   d6_coverage.py
  entail.py           L2 extract → route → adjudicate
  veto.py             L3 decision + intervention cap
  report.py           rich terminal render
  contract.py         schema + validation, shared by all four of us
  prompts/
    entailment_system.txt
hooks/
  post_tool_use.py    → ledger.append()
  stop.py             → run detectors → entail → veto
.codex/hooks.json
demo-repo/            the trap
```

## Degradation ladder

Each rung is still a shippable product.

| If this breaks | Ship this |
|---|---|
| D6 too slow | Drop it. Five detectors is still the pitch. |
| Entailment flaky / no API | **Detectors-only.** D1/D2/D4/D5 are deterministic and need no model at all. |
| `Stop` hook won't block | **CLI + pre-commit hook.** Still blocks something, still a complete product. |
| `PostToolUse` doesn't fire | Reconstruct the ledger from `git reflog` + `git diff`. Lose D4, keep the rest. |
| Live demo unstable at 4:40 | Play the backup video and narrate. **Never debug on stage.** |

---

# PART IV — WHY THIS WINS THE ROOM

1. **The demo needs no setup narrative.** "It said it fixed the code. It edited the
   test instead. Watch me stop it." A judge understands that in four seconds with
   zero context — which matters in a 45-minute block across ~40–60 teams.
2. **We're pitching the host's worldview back at them.** Greptile is a code-quality
   company. We're the row beneath their row.
3. **It's research-backed, not vibes.** METR and Anthropic numbers, three 2026
   papers, a named cheat taxonomy. Most hackathon pitches assert a problem; we cite one.
4. **Codex's role is unarguable** — built by it, plugged into it, and it tells Codex
   *no* on stage. That is the eligibility requirement turned into the punchline.
5. **The critical path has no external dependency.** No API key that might not
   arrive, no worker service, no venue-WiFi gamble. Detectors are stdlib.
6. **There's a real company here.** Free CLI → team CI → compliance, with a data
   flywheel nobody else is running. Most hackathon projects can't answer "and then
   what?" We can answer it for six months out.

## The honest limits — say these before you're asked

- **We can't see what the model was thinking.** Nobody can. What we show is fully
  recoverable and independently verifiable: which tools ran, what changed, what
  executed. Volunteering this buys more credibility than any feature.
- **Contract and schema tests are a real false-positive class.** We report; we never
  auto-delete; the threshold is yours.
- **A sufficiently determined agent could write a genuinely correct fix and still
  describe it badly.** That's an `UNVERIFIED`, not a `CONTRADICTED`. We distinguish
  them, and that distinction is most of the product's credibility.
