# RECEIPTS

**Your agent remembers. Now prove it.**

Greptile Fast Hackathon — Aug 23, 2026 · 560 20th St, SF
Target: **$1,000 Memory Prize** (Claude-Mem) + overall placing

> ## ⚠️ UNVERIFIED — READ BEFORE BUILDING (added Aug 23, 10:50am)
>
> **The $1,000 Claude-Mem Memory Prize is not on the public record.** The official
> listing names sponsors as **Greptile, Stripe, AWS, OpenAI, Modal, DoorDash** —
> **Anthropic is not among them.** Participant credits are 100 Greptile / $500
> Stripe / **$50** OpenAI (this doc says $100 for the Codex link — also unverified).
> The quoted rubric line *"everything scores extra for being something someone
> would actually use"* appears on no public page.
>
> The prize may still exist as a day-of sponsor bounty. **Confirm at the door,
> 12:00–12:30, before committing the build to it.**
>
> Two further risks, from `ideas/damage-report.md`:
> - **Dependency risk is the highest of any candidate.** The 1:00–1:25 block is
>   someone else's installer plus a worker service plus three MCP endpoints, in a
>   **4-hour** build.
> - **Prior art is thicker than Part V assumes** — `safedep/gryph` already ships
>   local-first agent audit trails with SQLite, session replay and before/after
>   diffs. Lead the pitch with **mutation** (delete/correct/pin → re-ask → diff),
>   which I could not find shipped anywhere. Visibility alone is taken.
>
> **If the memory prize is confirmed real, this doc is the best-prepared thing in
> the workspace and should be built.** If not, see `ideas/ranked-slate.md`.

---

## PART I — THE PLAIN ENGLISH HALF

### The problem

Your coding agent says something confidently wrong. It insists your auth flow works
a way it hasn't worked since March. You have no idea why.

Somewhere in its memory is the observation that poisoned the answer. You cannot find
it. You cannot see it. You cannot delete it. Your only options are wipe everything and
start cold, or live with it.

Memory systems today are **write-only from the user's perspective.** Stuff goes in.
Answers come out. The middle is a black box.

### The product

Receipts is the debugger for agent memory.

Click any claim in an agent's answer. The trail opens:

- which memories were searched
- which ones survived reranking
- which ones actually got injected into context
- what each one cost you in tokens
- when it was written, from what session, from what source

Then — and this is the part that matters — **you edit it.** Delete the bad memory.
Correct it. Pin the good one. Ask the same question again. Watch the answer change.

### Why it's not a dashboard

Claude-Mem already ships a viewer. If Receipts only *shows* things, we lose.

Receipts closes the loop: see → steer → re-ask → verify. The demo ends with the same
question producing two different answers, side by side, because the user reached in
and fixed the memory that was lying. That is not observability. That is control.

### Who pays for this

Anyone running agents in production who has watched one confidently hallucinate from
its own memory and had no way to trace it. That is currently everyone.

Pricing story: free local, paid team tier where memory trails are shared and
auditable across a team's agents.

### Why this wins the room

The Claude-Mem brief has seven directions. Six of them are about storing and
retrieving better. One says: *"The skills in the repo are CLI-shaped. Wrap them in UI
or UX that makes memory something you can see, steer, or share."*

Everyone builds storage. We build the instrument. We are the only team pitching
directly into their least-crowded ask.

---

## PART II — THE ENGINEERING HALF

### What we're tapping

Claude-Mem's retrieval is a documented 3-layer MCP workflow:

| Layer | Tool | What it returns |
|---|---|---|
| 1 | `search` | compact index with IDs, ~50–100 tokens/result |
| 2 | `timeline` | chronological context around a result |
| 3 | `get_observations` | full detail for filtered IDs, ~500–1,000 tokens/result |

Every layer is a place to tap a wire. Claude-Mem already tracks token cost per layer
(their "progressive disclosure" feature). We surface what it already knows and never
shows anyone.

Backing store is SQLite (sessions, observations, summaries) plus Chroma for hybrid
semantic + keyword search. Worker service exposes a local HTTP API. Hooks:
SessionStart, UserPromptSubmit, PostToolUse, Stop, SessionEnd.

### Architecture

```
Agent asks a question
        │
        ▼
  ┌─────────────────────────────────────┐
  │  MCP proxy shim (our layer)         │
  │  wraps search / timeline /          │
  │  get_observations                   │
  └─────────────────────────────────────┘
        │              │
        │              └──► trace log: every candidate at every
        │                   stage — retrieved, survived, injected,
        │                   dropped, token cost, source obs ID
        ▼
   Answer + trace_id
        │
        ▼
  ┌─────────────────────────────────────┐
  │  RECEIPTS UI                        │
  │  claim → trail → provenance         │
  │  delete / correct / pin             │
  │  re-ask → diff view                 │
  └─────────────────────────────────────┘
        │
        ▼
  writes back to claude-mem SQLite
```

### Scope discipline — what we are NOT building

- ❌ No knowledge graph rendering (90 min sink, unreadable on a projector)
- ❌ No new memory store — we instrument theirs
- ❌ No accounts, no auth, no multi-user
- ❌ No new agent framework
- ❌ No fine-tuning, no embeddings of our own

### Build schedule (1:00 – 5:00)

| Time | Task | Cut priority |
|---|---|---|
| 1:00–1:25 | `npx claude-mem install`, worker up, verify all 3 MCP endpoints respond | critical |
| 1:25–2:25 | **Instrumentation.** Proxy the 3 tools, log every candidate at every stage with survive/drop + token cost. Protect this hour. | critical |
| 2:25–3:15 | Trail UI — answer with expandable claims, each opening its provenance chain | critical |
| 3:15–3:50 | Steering — delete / correct / pin, write back to SQLite | critical |
| 3:50–4:10 | Diff view — same question before/after, side by side | high |
| 4:10–4:25 | Polish: token cost badges, source timestamps | cut first |
| 4:25–4:45 | Rehearse ×2, **record backup video**, README | critical |
| 4:45–5:00 | Submit with buffer | critical |

### Codex requirement

Codex is the primary coding agent — mandatory for eligibility. Keep the session
visible, mention it in the README, and note in the demo that Receipts was built by
Codex under Claude-Mem observation. Redeem the $100 link in a **personal** ChatGPT
workspace (not Business/managed), single-use, expires Aug 25 11:59 PM PT.

### Stretch (only if ahead at 4:00)

Greptile tie-in: when a memory cites a file, link the trail entry to Greptile's
indexed view of that file so you can see whether the memory still matches the code as
it exists now. **Stale memory detection.** Powerful, but do not start this before 4:00.

---

## PART III — THE DEMO (3 minutes)

**0:00–0:25 — The setup**
"Here's an agent with memory. I ask it about our auth flow." Agent answers
confidently. One claim in the answer is wrong.

**0:25–1:10 — Open the receipt**
Click the wrong claim. The trail opens. Eleven memories searched. Four survived
rerank. Two got injected. One of them is from a session three weeks ago, describing
code that has since been rewritten. There it is — the liar, with a timestamp and a
source session ID.

**1:10–2:00 — Steer**
Delete it. Correct it in place. One click.

**2:00–2:40 — The money shot**
Re-ask the exact same question. Split screen: before and after. The answer changed.
The trail now shows the corrected memory carrying the claim.

**2:40–3:00 — Close**
"Every memory system on the market is write-only. You can put things in and you can
hope. Receipts is the first one you can debug. One npx install, works on Codex and
Claude Code, and it's open source on top of Claude-Mem."

---

## PART IV — Q&A AMMO (2 minutes)

**"Claude-Mem already has a viewer."**
Their viewer shows you the stream. It doesn't tell you which memory produced which
sentence, and it doesn't let you fix it. We're not visualizing storage — we're
tracing causation and closing the loop on it.

**"Isn't this just RAG debugging?"**
RAG debuggers show retrieval. We show retrieval *plus* what survived rerank, what
actually made it into context, what it cost, and then let you mutate the store and
re-run. The mutation is the product.

**"Can you show what the model was actually thinking?"**
No, and anyone claiming that is lying to you. Attention weights aren't provenance.
What we show is fully recoverable and independently verifiable: which records were
fetched, which were injected, from where, at what cost.

**"Why would I pay for this?"**
The first time your agent hallucinates from a poisoned memory in production, your
only current option is nuking the whole store. That's a $0 tool with a very high
cost. This is the alternative.

**"What if the memory that's wrong isn't in the trail?"**
Then the failure isn't memory — it's the model, and we've just told you that in ten
seconds instead of an hour. Ruling memory out is worth the same as ruling it in.

---

## PART V — WIN STRATEGY

**Primary target:** $1,000 Memory Prize. Judged separately from 1st–3rd, narrow
published rubric, and we hit "see, steer, or share" dead center — the one direction
that isn't another storage engine.

**Secondary:** overall placing. The rubric line is *"everything scores extra for being
something someone would actually use."* Receipts is a debugger. Debuggers are the most
obviously-useful category of developer tool that exists.

**Three things that decide it:**

1. **The diff view lands or nothing lands.** If the before/after doesn't work on
   stage, the demo has no ending. Rehearse it twice. Record the backup.
2. **Say "steer" out loud, early.** Judges have the brief in front of them. Use their
   word in the first fifteen seconds.
3. **Name the honest limit before they ask it.** Volunteering "we can't show you what
   the model was thinking, and nobody can" buys more credibility than any feature.

**Failure mode to pre-empt:** if instrumentation isn't producing clean traces by 2:30,
drop steering and ship trail-only with a hardcoded corrected memory for the diff. A
scripted diff that works beats a live one that doesn't.
