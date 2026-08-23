# RANKED SLATE + BUILD PLAN

Aug 23, 2026 · **build 1:00–5:00pm · judging 5:00–5:45 · prizes 6:00**

Companion to `ideas/damage-report.md` (evidence + kill notes) and
`notes/hackathon-rules.md` (verified rules). This file is the one to keep open.

---

## THE RANKING

Scored 1–5 on the four things that decide a 4-hour hackathon. **Demo** is
double-weighted, because judging is a 45-minute block across the whole room and
nobody reads your README.

| # | Idea | On-theme | Codex-native | 4h buildable | Demo ×2 | Total | Verdict |
|---|---|---|---|---|---|---|---|
| **1** | **KAYFABE** — fake tests, exposed | 5 | 5 | 5 | 5 (10) | **25** | 🟢 **BUILD** |
| **2** | **RECEIPTS v2** — agent claims vs. tool log | 5 | 5 | 5 | 4 (8) | **23** | 🟢 strong alt |
| **3** | **THRASH** — loop breaker | 5 | 5 | 4 | 4 (8) | **22** | 🟢 alt, demo risk |
| 4 | **THE BOUNCER** — Greptile blocks the Stop | 5 | 5 | 2 | 5 (10) | 22 | 🟡 bolt-on |
| 5 | **RECEIPTS v1** — claude-mem memory debugger | 4 | 3 | 2 | 4 (8) | 17 | 🟡 only if prize real |
| 6 | **BLAST RADIUS** — Greptile code-graph guard | 5 | 4 | 2 | 3 (6) | 17 | 🟡 too many unknowns |
| 7 | **REGRET** — mine reverts → AGENTS.md | 4 | 4 | 5 | 2 (4) | 17 | 🟡 bolt-on |
| 8 | **PARALLEL UNIVERSE** — Modal pre-verify | 5 | 5 | 1 | 3 (6) | 17 | 🟡 90-min hole |
| 9 | **DIVERGENCE** — 3 agents, diff the spec | 4 | 5 | 1 | 4 (8) | 18* | 🟡 wrong event length |
| 10 | **FLAKE ALIBI** | 4 | 4 | 5 | 2 (4) | 17 | 🟡 fold into #1 |
| — | Crutch Breaker / Warden / Sparring / Cart / Streamer | 0 | — | — | — | **0** | 🔴 off-theme |
| — | Audit trail · secret guard · rewind · PreCompact | 5 | 5 | — | — | — | 🔴 taken or unshipped |

\* Divergence scores well and is the most *creative* thing on the slate. It is
ranked down purely on the 4-hour clock. **Keep it — it is a 24-hour-hackathon winner.**

---

## PREDICTIONS

Estimated field: ~40–60 teams. Prizes concentrate at the very top (one YC
interview), so "placing" means roughly top 3.

| Idea | Finishes working by 5:00 | Top-3 | Best realistic outcome |
|---|---|---|---|
| **KAYFABE** | **90%** | **~25%** | Top 3. Testing is a named category and the demo needs no setup. |
| **RECEIPTS v2** | **90%** | ~20% | Top 5, top 3 if claim extraction is crisp. |
| **THRASH** | 85% | ~20% | Top 3 **if the live loop fires**; forgettable if you fall back to video. |
| KAYFABE **+ Bouncer bolt-on** | 70% | **~30%** | **Highest ceiling on the board.** Only if Greptile keys are real and easy. |
| RECEIPTS v1 | 60% | ~10%, or **~45% of a memory prize if it exists** | Binary on one unverified fact. |
| Parallel Universe / Divergence | 40% | ~10% | Great idea, wrong clock. |

**The honest meta-prediction:** in a room where Codex is mandatory, expect a large
cluster of "wrapper on Codex" projects. The differentiator will not be idea
novelty — it will be **whether the thing visibly worked on a laptop at 5:15pm**.
Every ranking above is weighted for that.

---

## VERIFY IN THE FIRST 15 MINUTES — do not skip this

These are facts my sources **disagree on**. Each takes ~3 minutes to check and
each can invalidate a plan.

| Question | Why it matters | How to check |
|---|---|---|
| 🔴 **Do `PreToolUse`/`PostToolUse` fire for `apply_patch`/Edit/Write, or Bash only?** | Official docs say Bash + `apply_patch` + MCP + local function tools. A third-party reference says **Bash only, by design**. If it's Bash-only, Blast Radius and Parallel Universe die and Kayfabe must trigger off the **Stop** hook (which it already does). | Register a no-op `PostToolUse` that logs to a file, make Codex edit a file, check the log. |
| 🟠 **Is the hooks feature flag on by default?** | Official docs: hooks run by default, `[features] hooks = false` disables. Third-party: you must set `[features] codex_hooks = true` or hooks are **silently ignored**. Silent failure is the worst kind. | Same no-op test. If nothing logs, set the flag. |
| 🔴 **Hook trust prompt.** | Non-managed hooks require **explicit trust by hash** via the `/hooks` command before they run — and *changing* a hook re-triggers it. This can ambush you mid-demo. | Trust your hooks early; re-trust after every edit. |
| 🟠 **Is there a Claude-Mem / memory prize? Any sponsor bounties?** | Decides whether Receipts v1 is live. | Ask at the door, 12:00–12:30. |
| 🟠 **Greptile API: base URL, auth, endpoints?** | Gates the Bouncer and Blast Radius. Their public docs publish none of it. | Ask a Greptile person during opening remarks. |
| 🟡 **Is pre-1:00pm code allowed?** | Decides whether you can prep the demo repo now. | Ask at the door. |

---

## OPEN SOURCE TO BUILD ON OR STEAL FROM

**Directly useful today**

| Repo | Use |
|---|---|
| `openai/codex` — `docs/config.md`, and `learn.chatgpt.com/docs/hooks` | The primary source for hook events, payloads, `hooks.json` schema and the deny contract. **Read this first, it's the spec you're building against.** |
| `Yeachan-Heo/oh-my-codex` (OMX) | Most popular Codex hooks framework. `docs/codex-native-hooks.md` is the best plain-English writeup of the native hook surface. v0.13.1 wires through `.codex/hooks.json` natively. **Read its docs; don't depend on it.** |
| `RoggeOhta/awesome-codex-cli` | 150+ Codex tools/skills/plugins. **Use it as a 10-minute prior-art check** — if your idea is in there, change your idea. |
| `mutmut` (Python) / `Stryker` (JS) / `PIT` (Java) | Mutation-testing ancestors of Kayfabe. **Do not depend on them** — they're far too slow for a Stop hook. Read `mutmut`'s AST mutation for the technique, then write the 30-line version. |
| Python stdlib `ast` | The whole of Kayfabe's core. `ast.NodeTransformer` to swap a function body for `raise NotImplementedError`, `ast.unparse` to write it back. No dependency. |

**Prior art — know these so you're not blindsided in Q&A**

| Repo / work | What it already does |
|---|---|
| `safedep/gryph` (Apache-2.0) | Local-first agent audit trail: every file read/write, MCP call, command → SQLite; query, filter, replay; before/after diffs. **The closest thing to Receipts.** Notably its supported list is Claude Code, Cursor, Windsurf, Gemini CLI, OpenCode, Pi Agent — **Codex is not named.** That gap is your opening. |
| `thedotmack/claude-mem` (~46k★) | The memory system Receipts v1 instruments. Works with Claude Code, **Codex**, Gemini, Copilot, OpenCode. SQLite + Chroma, 3-layer MCP retrieval, lifecycle hooks. |
| Arize **Phoenix** / **MLflow** | Open-source LLM/agent observability, retrieval-relevancy views. |
| **AgentDebugX** (arXiv 2607.18754) | Open-source failure observability, attribution, recovery for LLM agents. |
| arXiv 2606.04990 | "Evidence Tracing and Execution Provenance in LLM Agents" — memory as provenance-bearing evidence. |
| `openai/codex` issues **#27588, #17480, #37937, #14203** | Loop/thrash reports. **Cite these on stage for Thrash.** |
| `openai/codex` issue **#16098** | PreCompact/PostCompact hooks — *open request*. The reason not to build on compaction. |
| `AGENTS.md` spec (Agentic AI Foundation, Linux Foundation) | Read by Codex, Cursor, Cline, Windsurf, Gemini CLI, Claude Code. One file, every agent — the output target for REGRET. |

---

## RECOMMENDATION

**Build KAYFABE. Ship Receipts v2 as the second beat only if you're ahead at 3:45.**

Reasons, in order of weight:

1. **No external dependency in the critical path.** Nothing to install, no API key to arrive, no worker service. Compare to Receipts v1, whose first 25 minutes are someone else's installer.
2. **Testing is a named theme category** and Greptile is a code-quality company. You are pitching their worldview back at them.
3. **The demo needs zero setup narrative.** Delete a function, tests still pass. A judge understands it in four seconds, with no context.
4. **It is your engine, unchanged.** Observe (what did it test), store (theatre score), oppose (Stop hook blocks it). You are not abandoning two weeks of thinking — you are aiming it at a target that's in scope.
5. **Codex's role is unarguable.** Built by Codex, plugged into Codex, and it *opposes* Codex on stage.

**Contingency, decided in advance:**
- **Greptile keys real + API sane at 1:15?** → bolt the **Bouncer** on at 3:30. Highest ceiling.
- **Memory prize confirmed real at 12:30?** → switch to **Receipts v1**. It's purpose-built, the doc is already written, and a narrow prize with a published rubric is easier to win than an open field.
- **Kayfabe's Stop-hook block not working by 3:30?** → ship the CLI-only version. `kayfabe .` printing a theatre score is still a complete product and still shocking. **Drop the hook, not the demo.**

---

## THE 4-HOUR PLAN

| Time | Task | Cut? |
|---|---|---|
| **before 1:00** | Prep demo repo: small Python module + pytest suite. Ask at the door whether pre-work is allowed; if not, have it *designed* and type it at 1:00. | — |
| 1:00–1:15 | **Verify list above.** No-op hook → does it fire, for which tools, does it need the flag, trust it. | critical |
| 1:15–2:15 | **Core sabotage engine.** `ast` swap of function body → `raise NotImplementedError`; run pytest before/after; diff pass sets; theatre score. **Protect this hour.** | critical |
| 2:15–2:45 | Have Codex write tests for the demo module — **this is your demo footage and your Codex-role proof.** Capture the terminal. | critical |
| 2:45–3:30 | **Stop hook.** Score over threshold → `decision:"block"` with the theatre report as the reason. Watch Codex read it and rewrite. | critical |
| 3:30–4:00 | One clean view — terminal table is fine, red/green per test. Resist building a web app. | high |
| 4:00–4:20 | *Ahead?* Bouncer (Greptile) **or** Receipts v2 claim-check as beat two. Not both. | cut first |
| 4:20–4:40 | **Rehearse ×2. Record the backup video.** README naming Codex's role. | critical |
| 4:40–5:00 | Submit with buffer. | critical |

**Hard rule, from your own workspace:** *one loop before one platform.* The loop is
write tests → sabotage → block → rewrite. Do not build a dashboard, a config
system, or multi-language support. Every over-scoped idea in this workspace died
of "platform."

---

## THE DEMO (target 2:30, assume you get cut off at 2:00)

> **0:00** "Codex just wrote me twelve tests. All green. 94% coverage."
> *(green terminal on screen)*
>
> **0:20** "Watch." — `kayfabe .`
> **"I deleted the function under test. Nine of these twelve still pass.
> They never called the code. Your coverage number is a costume."**
>
> **1:00** "So we wired it into Codex's Stop hook." Ask Codex to finish.
> **It gets blocked.** It reads its own theatre score on screen and rewrites the tests.
>
> **1:50** Second run. Theatre score 0. Now delete the function — **the suite goes red.**
> "That's the difference between tests that pass and tests that test."
>
> **2:10** "Built by Codex, and it's the thing that tells Codex no.
> One file in `.codex/hooks.json`. Open source."

Say **"your agent's tests are lying to you"** in the first fifteen seconds. It is
the whole pitch and it survives being the only sentence a judge remembers.

---

## Q&A AMMO

**"Isn't this just mutation testing?"**
"It's mutation testing's angriest single mutation. Stryker and mutmut run for
minutes in CI and hand you a score. We run one mutation in seconds and wire it to
the agent's stop condition, so the agent can't ship the lie in the first place.
The novelty isn't the mutation — it's the veto."

**"Deleting the whole function is crude."**
"Deliberately. It's the cheapest possible test of whether a test touches the code
at all, and it runs fast enough to sit in a hook. Finer mutants are the roadmap;
this one catches the failure mode agents actually have, which is not subtle."

**"What about tests that legitimately don't call the function?"**
"Contract and schema tests, yes — that's the honest false-positive class. We
report, we don't auto-delete, and the threshold is yours."

**"Won't this annoy the agent into a loop?"**
"Known failure mode — it's `openai/codex` issue 37937, where a repeatedly
blocking Stop hook traps the CLI. We cap at two interventions per turn and then
always release." *(This answer alone signals you read the source.)*

**"Why does this need Codex?"**
"It doesn't only work on Codex — but Codex is the only agent shipping a Stop hook
that can return a block decision, which is the entire mechanism. It's also what
built it."

**"Who pays for this?"**
"Anyone whose coverage gate is currently a lie. It's a CI check and a pre-merge
hook — the same buyer as a linter, with a much scarier report."
