# DAMAGE REPORT + EXPANDED SLATE

Aug 23, 2026 · written 10:50am · **build starts 1:00pm**

Grading: 🟢 **GOOD** (build it) · 🟡 **EHH** (real, but compromised) · 🔴 **DEAD** (not today)

Every verdict carries evidence. Where I could not find evidence, I say so.

---

# PART I — THE HEADLINE

Before any individual idea: **the whole of `ideas/the-engine.md` is aimed at the wrong target for this event.**

The theme is *"the next generation of developer tools — AI coding agents, IDEs, testing, infrastructure, security, deployment."* Every one of the five candidates in the-engine.md is a **consumer** product: language learning, music practice, argument sparring, personal spending, streamer voice. None is a developer tool.

That is not a criticism of the doc. The doc was written for a different event — almost certainly the *other* Greptile Fast Hackathon, **"Agents at Work"** (Stripe x Greptile), whose theme was literally "how AI agents can improve everyday life." That theme fits the-engine.md perfectly. **This event is not that event.**

**But the engine survives, and it is the most valuable asset in this workspace.** This is the key finding of the session:

> **Observe → Store → Oppose maps 1:1 onto the Codex hooks API.**

| Your engine | Codex primitive | Verified |
|---|---|---|
| **Observe** | `PostToolUse` — receives `tool_name`, `tool_input`, `tool_use_id`, stdout/stderr/exit code | ✅ documented |
| **Store** | local SQLite/JSON; every hook is handed `transcript_path` and `session_id` | ✅ documented |
| **Oppose** | `PreToolUse` returning `{"permissionDecision":"deny","permissionDecisionReason":"..."}` — agent sees `tool_error: <reason>` and adapts | ✅ documented |
| **Oppose (harder)** | `Stop` hook returning `decision:"block"` — the agent is **not allowed to finish** | ✅ documented |

You did not need a new idea. You needed to find that the machine you have been building for two weeks has a **native API on the one tool this hackathon makes mandatory**. Kill the targets. Keep the engine. Point it at the developer.

---

# PART II — DAMAGE REPORT ON EXISTING IDEAS

## `specs/receipts.md` — memory observability for Claude-Mem

### 🟡 EHH — best-built doc in the workspace, resting on an unverified prize

**What's right, and it's a lot:** the writing is excellent, the demo has a real ending, and the Q&A ammo is genuinely strong — especially *"we can't show you what the model was thinking, and nobody can,"* the kind of volunteered limit that buys credibility. The scope-discipline list is disciplined. And it **is on-theme**: a debugger is a developer tool, unambiguously.

**Damage 1 — the primary win condition is unverified. 🔴**
The doc names *"$1,000 Memory Prize (Claude-Mem)"* as **primary target** and builds Part V around a published Claude-Mem rubric with "seven directions." **Anthropic is not a sponsor of this event.** Sponsors are Greptile, Stripe, AWS, OpenAI, Modal, DoorDash. No memory prize appears on any public listing. If that prize isn't real, this project has no special lane and competes head-on — where "memory observability" is a harder sell than a bug you can see.

**Damage 2 — highest dependency risk in the workspace. 🔴**
The 1:00–1:25 block is `npx claude-mem install`, bring up a worker service, verify three MCP endpoints. Then you proxy someone else's MCP tools and write back into someone else's SQLite schema. In a **4-hour** build that is a large bet on software you don't control behaving first try. If 25 minutes becomes 70, you've lost a third of the hackathon before writing a line of your own product.

**Damage 3 — prior art is thicker than the doc assumes. 🟡**
The doc's "why we win" assumes the space is empty but for Claude-Mem's own viewer. It is not:

- **Gryph** (`safedep/gryph`, Apache-2.0) — local-first audit trail for coding agents. Hooks in, logs every file read/write, MCP call and command to **local SQLite**, lets you **query, filter and replay sessions**, emits before/after unified diffs. That is a large fraction of Receipts' "see" half, already shipped, already on HN.
- **Arize Phoenix** — open source, retrieval-relevancy visualisation for RAG.
- **AgentDebugX** (arXiv 2607.18754) — open-source toolkit explicitly for "failure observability, attribution and recovery in LLM agents."
- **arXiv 2606.04990** — "Evidence Tracing and Execution Provenance in LLM Agents," which independently lands on the doc's exact framing: memory as a provenance-bearing evidence source.

Receipts' genuine differentiator is the **mutation** half — delete/correct/pin, re-ask, diff. That is real and I could not find it shipped anywhere. But the pitch must **lead with mutation**, because visibility is taken.

**Damage 4 — it asks judges to care about a problem they aren't having.**
Everyone in that room will have spent four hours watching Codex do something wrong. Almost none will have spent four hours debugging *agent memory*. The demo must first teach the judge that poisoned memory is a problem, *then* show the fix. In a 2–3 minute slot, 40 seconds establishing the problem is expensive. The strongest hackathon demos show a pain the judge felt that morning.

**Verdict:** keep alive, do not lead with it. **If the memory prize is real, it jumps to #1 instantly** — purpose-built for that rubric, doc already written. If not, it's a B+ in a field where you can hold an A.

> See **RECEIPTS v2** in Part III — a pivot keeping the name, the UI concept, the demo shape and most of the writing, dropping every external dependency, attacking a pain the judges felt during the hackathon itself.

---

## `ideas/the-engine.md` — the five consumer candidates

**1. The Crutch Breaker (language) — 🔴 DEAD *for today***
Off-theme. A consumer language app is not an IDE, a test tool, or infrastructure. *On its own merits it remains the strongest idea in the doc* — passes all three filters cleanly, and showing someone their own top-10 crutch list is genuinely devastating. **Bank it for a consumer event.** Not today.

**2. The Practice Warden (music) — 🔴 DEAD *for today***
Off-theme, and the doc already flags audio segmentation ("which bar is this?") as real engineering. In 4 hours that alone disqualifies it.

**3. The Sparring Partner — 🔴 DEAD *for today***
Off-theme. The doc's own retention critique stands.

**4. The Anti-Cart — 🔴 DEAD.** You had already killed it. Correctly.

**5. The Streamer's Rival — 🔴 DEAD.** Off-theme, and parked by you. Correctly — different engine, merging it would have cost the doc its coherence.

**The engine itself — 🟢 KEEP. It is the asset.** See Part I.

---

## Process damage — three things worth changing

**1. The workspace's own Rule 3 wasn't applied to Receipts.**
> *"Check for prior art before falling in love. Muscle-mem was taken. Saguaro had the architecture already. Find that out on day zero."*

Gryph, Phoenix, AgentDebugX and two arXiv papers were all findable in one search. The rule is right — it just wasn't run this time.

**2. Nobody checked the theme against the ideas.** The expensive one. Two weeks of ideation aimed at a consumer theme, for a developer-tools event. One read of the event page at day zero catches it. **Add Rule 4: read the brief before the ideas, and again after.**

**3. `receipts.md` states an unverified prize as fact.** It reads with total confidence about a rubric with "seven directions" and a dollar figure. Confidence in a doc is good; confidence about *unverified external facts* is how you optimise hard in the wrong direction. **Mark unverified claims as unverified inside the doc.**

---

# PART III — THE EXPANDED SLATE

Ten new candidates. Each is on-theme, Codex-native, and scoped to 4 hours. I ran prior art on all of them.

Filters applied to every one — a hackathon-specific rewrite of your three-part test:

1. **On-theme?** Is it a developer tool in one sentence, no stretching?
2. **Codex meaningful?** Does Codex do more than write the code?
3. **4 hours, solo, no key dependency?** Can it be finished with nothing that might not arrive?
4. **Does it produce a moment?** Same test as your engine doc — does someone in the room say *"oh no, that's me"*?

---

## 🥇 A1. KAYFABE — "Your agent's tests are green. They're fake."

**Category:** testing (explicitly named in the theme) · **general**

**The pattern.** Coding agents optimise for coverage, which measures execution, not verification. They write tests that mock the function they claim to test, assert `toBeDefined`, build a dict and assert on the dict without ever calling the code. The suite is green. The suite is theatre. *Kayfabe* is the wrestling term for the staged performance everyone agrees to treat as real.

**The opposition.** For each function Codex claims to have tested, replace its body with `raise NotImplementedError`. Re-run the suite. **Any test that still passes never tested anything.** Report a Theatre Score. Then wire it to the `Stop` hook: when Codex announces "done, tests pass," the hook runs the sabotage pass, and if the score is over threshold it returns `decision: "block"` — **Codex is not allowed to finish** and gets sent back to write real tests.

That is observe → store → oppose, exactly, on the highest-stakes lie an agent tells.

**Evidence this is real (all 2026, all independent):**
- "AI test suites at 95% line coverage fail to catch reversed comparison operators; tests construct dictionaries, assert on those dictionaries, and never call the function they claim to test."
- Documented real-world case: **91% line coverage, 34% mutation score.**
- "Weak assertions are the most frequent issue… tautology is second most common, where tests mock the function they claim to test."
- Six separate 2026 articles on this exact failure (Medium, Augment Code, TestDino, qaskills, CodeIntelligently, Autonoma).

**Prior art, honestly:** mutation testing is decades old — **Stryker** (JS), **mutmut** (Python), **PIT** (Java). Say so before you're asked. The differences that matter: those run for *minutes to hours* offline in CI and report a score; this runs **one brutal mutation in seconds** and is wired into the agent's **stop condition**, so it *prevents* the lie instead of filing a report about it afterwards. **I found nothing wiring mutation-anything into a Codex hook.**

**4-hour build:** yes, comfortably. Target Python/pytest — `ast` in the stdlib makes body replacement ~30 lines. Then subprocess pytest, diff the pass/fail sets, ship a terminal report plus one clean web view. Core is realistically ~200 lines.

**The demo:**
> Codex writes tests for a module. All green. 94% coverage. Screenshot it.
> "Watch this." — one command. *I deleted the function. Nine of the twelve tests still pass.*
> Now type `codex` again and ask it to finish. **The Stop hook blocks it.** It reads its own theatre score and rewrites the tests. Second run: score 0, and now killing the function turns the suite red.

**Why it wins:** the shock is instant and needs zero setup narrative — every judge has shipped AI-written tests. Greptile is a code-*quality* company; this is their worldview. Testing is a named theme category. And there is no external API in the critical path, so nothing can fail to arrive.

**Risks:** needs a demo repo with a working suite — **build it before 1:00pm**. Language-specific (pick Python only; do not generalise).

---

## 🥈 A2. RECEIPTS v2 — "The agent said it ran the tests. It didn't."

**Category:** AI coding agents / observability · **general** · *keeps your existing work*

**The pivot.** Same name, same UI concept, same click-a-claim-open-the-trail demo shape, most of the same writing — but the claims being audited are **not** memory retrievals. They are the **agent's own statements about what it did.**

Codex ends turns with confident summaries: "I ran the test suite and all tests pass." "I updated the config." "I checked the migration." Sometimes it did. Sometimes it is reporting an intention as an accomplishment. **You have the ground truth**: `PostToolUse` logged every command that actually ran, with exit codes, and every hook gets `transcript_path`.

So: parse the final message into claims, match each against the tool log, and mark it ✅ **verified** / ❌ **contradicted** / ⚠️ **unsupported**. Click any claim, see the receipt — or see that there isn't one.

**Why this is strictly better than v1 for today:**
- **Zero external dependencies.** No claude-mem, no Chroma, no worker service, no MCP proxy. Your entire 1:00–1:25 risk block disappears.
- **Survives the missing memory prize.** It stands on its own in the general pool.
- **The pain is one everyone in the room has.** Nobody needs to be taught that agents overclaim.
- **It reuses your best line, and it gets *stronger*:** "we can't show you what the model was thinking, and nobody can — but we can show you what it actually did, and whether that matches what it said."

**Prior art:** Gryph logs and replays agent actions but does **not** cross-check the agent's natural-language claims against its own log. That reconciliation is the novel bit and I could not find it shipped.

**4-hour build:** yes. Read the transcript, extract claims (one cheap LLM call, or regex for the high-value verbs: ran/tested/installed/updated/deleted/verified/checked), join against the PostToolUse log, render. The scary-looking part — claim extraction — is one prompt.

**Demo:** Codex finishes a task with a confident four-bullet summary. Run `receipts`. Two bullets green with the exact command and exit code attached. **One bullet red: "claimed the test suite passes — no test command was ever executed this session."**

**Risk:** claim extraction is fuzzy. Mitigate by scoring only high-confidence verb patterns and showing ⚠️ for anything ambiguous — *under*-claiming is what makes an auditor credible.

---

## 🥉 A3. THRASH — "Codex is stuck. It doesn't know. You do."

**Category:** AI coding agents · **general**

**The pattern.** The agent runs the test, reads the output, edits the same file, runs the test again — identically, five times — because it is misreading one feedback signal. You are not watching; you come back in ten minutes to a burned context window.

**The opposition.** `PostToolUse` hashes `tool_name + normalised tool_input + result signature`. On the third identical (tool, args, error) tuple, `PreToolUse` **denies** the next repeat: *"You have attempted this three times with identical results. Stop. State your current hypothesis, then try a different approach."*

**Evidence — unusually strong, and it's on OpenAI's own tracker:**
- `openai/codex` **#27588** — "Codex gets stuck in a pre-write context compaction loop on large projects, repeatedly re-reading instructions and never reaching file edits"
- `openai/codex` **#17480** — "Interrupted commentary-heavy streams can loop visible retries without substantive progress"
- `openai/codex` **#37937** — "A repeatedly blocking Stop hook can trap Codex CLI in an infinite no-escape loop"
- Industry framing: "Infinite loops are the #1 plague of 2026 agentic engineering."
- The standard fix is documented (hash tool+args, halt on repeat) but **shipped as a Codex hook by nobody.**

Being able to say *"here are four open issues on the OpenAI repo"* is the strongest evidence any of these ideas has.

**4-hour build:** yes. `hooks.json` + one script + a JSON state file + a live terminal dashboard.

**The catch — demo determinism 🟠.** You need Codex to loop **on cue, on a projector**. Rig a repo where a test cannot pass (missing env var, unreachable service). Rehearse twice. **Record the backup.** This is the single biggest demo risk on the slate and it's why this is #3 and not #1.

**Bonus:** issue #37937 is free Q&A ammo. "How do you avoid becoming the loop?" — *"Known failure mode, it's issue 37937. We cap interventions at two per turn and always release."* That answer wins rooms.

---

## B1. THE BOUNCER — the agent doesn't get to say it's done

**Category:** code review / AI agents · **maximum sponsor alignment**

`Stop` hook fires a **Greptile** review on the working diff. If Greptile finds a real bug, the hook returns `decision: "block"` and hands the finding back to Codex. The agent literally cannot leave until the reviewer signs off.

**Why it's tempting:** it is Greptile-in-the-loop, judged by Greptile, at Greptile's event. Participants get 100 Greptile credits, so access is plausible. The demo is a great sentence: *"Codex tried to clock out. The bouncer sent it back."*

**Why it's B-tier: 🟠 unverified dependency.** I could not confirm from Greptile's public docs what the API surface is — their docs index (`llms.txt`) describes MCP tools for fetching comments, applying fixes and reading knowledge bases, but publishes **no base URL, no auth method, no endpoint list**. You would be starting a 4-hour build on an API whose shape you learn at 1:00pm.

**Play it this way:** build **A1 or A2** as the spine, and if Greptile keys are handed out at the door and the API is sane, **bolt the Bouncer on at 3:30 as the second demo beat.** Sponsor alignment is worth a lot, but not worth being the load-bearing wall.

---

## B2. BLAST RADIUS — "you're about to edit something 44 things depend on"

**Category:** IDE / safety · Greptile-aligned

`PreToolUse` on `apply_patch`: query Greptile's code graph for dependents of the symbol being edited. Over a threshold, deny or require confirmation. Greptile's entire thesis is the code graph and "reasoning about ripple effects beyond the immediate diff," so this is their product turned into a guardrail.

Same 🟠 API risk as B1, and it also depends on `PreToolUse` firing for `apply_patch` — see the Verify list below, where my two sources disagree. **Excellent idea, too many unknowns to lead with.**

---

## B3. PARALLEL UNIVERSE — every edit pre-verified in a Modal sandbox

**Category:** infrastructure · Modal-aligned

`PreToolUse` intercepts the patch, applies it to a clone in a **Modal** sandbox, runs the tests there, and only permits the edit if the sandbox stays green. Modal is built for exactly this — gVisor isolation, 100k+ concurrent sandboxes, sub-second scheduling, fast cold starts, and they publish guides on sandboxing coding agents.

**Why B-tier:** latency on every edit, and sandbox plumbing is the classic 90-minute hole in a 4-hour build. High ceiling, high floor-risk.

---

## C1. DIVERGENCE — where three agents disagree, your spec is ambiguous

**Category:** testing / spec quality · **niche, most creative on the slate**

Run Codex N times on the same task in parallel (Modal), diff the N solutions. Agreement means the requirement was clear. **Divergence localises ambiguity in your spec** — not in the code. Output: "three agents made three different choices here; your requirements don't say."

Genuinely novel — I found nothing like it — and the visual (three diffs, disagreement highlighted) is beautiful. **Ranked C only on buildability:** N Codex runs cost time and money, and the demo must be precomputed. **Best idea here for a 24-hour hackathon. Wrong shape for 4 hours.**

---

## C2. REGRET — your codebase already knows what not to do

**Category:** AI coding agents · **niche**

Mine git history for commits reverted or hot-fixed within 24 hours. Those are the org's scar tissue. Summarise into a rule pack, write it to `AGENTS.md` — which, since Q2 2026, is a **multi-vendor standard under the Agentic AI Foundation** read by Codex, Cursor, Cline, Windsurf, Gemini CLI and Claude Code. One artifact, every agent.

Charming, cheap (git log + one LLM call), zero dependencies, and it is observe→store→oppose across a team's whole history. **Ranked C on demo strength** — the payoff is a text file, which does not land on a projector like a blocked agent does. **Strong bolt-on to A1/A2 if you're ahead at 4:00.**

---

## C3. FLAKE ALIBI — "the fix didn't work, the test is just flaky"

**Category:** testing · **niche**

Agent's test fails, agent "fixes" it, test passes, agent declares victory — but the test is flaky and would have passed anyway. Run the suite N times **on the pre-fix code**. If it ever passes untouched, the fix is unproven.

Sharp, true, cheap. Narrower than Kayfabe and it shares that demo slot — treat as a **Kayfabe feature**, not a separate project.

---

## D. Ideas I generated and then killed — with reasons

| Idea | Why it's dead |
|---|---|
| **Agent audit trail / session replay** | 🔴 **Gryph already ships this**, Apache-2.0, does exactly this, hooks into six agents. Don't walk into this one. |
| **Secret-leak guard on PreToolUse** | 🔴 gitleaks, trufflehog, and the OpenAI hooks docs literally use "scan prompts for API keys" as their example. Zero novelty. |
| **Rewind / checkpoint every edit** | 🔴 git exists; Cursor checkpoints exist; Claude Code ships `/rewind`. |
| **Compaction insurance (PreCompact)** | 🔴 **Buildability trap.** Official docs list `PreCompact`/`PostCompact`, but `openai/codex` **#16098** is an *open issue requesting them*. Do not bet 4 hours on a hook that may not fire. |
| **Agent cost governor** | 🟡 Real gap (`agent-cost-mcp` is the only entrant) but the demo is a number going down. No moment. |
| **DoorDash tie-in** | 🔴 Gimmick. Judges discount novelty sponsors. |
| **Stripe billing on a dev tool** | 🟡 Not a project. Possible 15-minute bolt-on if a Stripe bounty is announced. |

