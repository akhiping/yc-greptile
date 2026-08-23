# YC HACKATHON — WORKSPACE

Sameer Nagar · started Aug 23, 2026

> ## ⏰ THE EVENT IS TODAY
> **The Fast Hackathon** (Greptile, hosted at YC — 560 20th St, SF)
> Doors 12:00 · remarks 12:30 · **build 1:00–5:00** · judging 5:00–5:45 · prizes 6:00
> **Theme: developer tools.** Codex mandatory as primary coding agent. Teams ≤4.
> Full verified rules: **`notes/hackathon-rules.md`**

## Structure

```
ideas/    exploration, ranked candidates, kill notes
specs/    build-ready one-pagers (engineering + demo + Q&A)
notes/    prior art, competitor findings, raw research
```

## Current state

| Doc | What it is | Status |
|---|---|---|
| `notes/hackathon-rules.md` | Verified rules, prizes, sponsors, discrepancies, open questions | **Read first** |
| `ideas/ranked-slate.md` | Ranking, predictions, repos, build plan, demo script, Q&A | **Keep open** |
| `ideas/damage-report.md` | Evidence + verdicts on every idea, old and new | Reference |
| `specs/receipts.md` | Memory observability for Claude-Mem | ⚠️ On hold — see below |
| `ideas/the-engine.md` | observe→store→oppose, aimed at consumer domains | 🔴 Off-theme for today |

## What changed on Aug 23

Two findings reset the plan:

**1. The theme is developer tools.** Every candidate in `ideas/the-engine.md` is a
consumer product — language, music, sparring, spending, streaming. All five are
off-theme for this event. They were written against the *other* Greptile
hackathon ("Agents at Work"), whose theme was everyday life. Bank them; don't
build them today.

**2. The engine is the asset, and it has a native API.**
Observe → Store → Oppose maps 1:1 onto Codex hooks: `PostToolUse` observes,
SQLite stores, and `PreToolUse` / `Stop` can return **deny** / **block**. The
machine from the last two weeks plugs straight into the one tool this hackathon
makes mandatory. Kill the targets, keep the engine, point it at the developer.

**Also:** `specs/receipts.md` names a "$1,000 Claude-Mem Memory Prize" as its
primary target. **Anthropic is not a sponsor of this event and no such prize is
on the public record.** Confirm at the door before betting on it.

## The pick

**KAYFABE** — sabotage the function under test, prove the agent's green suite
never touched the code, and wire the theatre score to the `Stop` hook so Codex
can't declare victory on fake tests. Same engine, on-theme, zero external
dependencies, demo needs no setup. Full spec in `ideas/ranked-slate.md`.

## Open decisions

- [ ] **12:00–12:30, at the door:** memory prize real? judging rubric? Greptile
      API keys and endpoints? is pre-1:00 code allowed?
- [ ] **1:00–1:15:** do hooks fire for `apply_patch` or Bash only? is the feature
      flag on by default? (sources disagree — see the verify table)
- [ ] Bolt on the Bouncer (Greptile) at 3:30, or Receipts v2 claim-check? Not both.

## Rules for this workspace

1. One loop before one platform. Every over-scoped idea here died of "platform."
2. If the user doesn't say "that's genuinely me," the idea is dead. Test the
   recognition moment before building anything around it.
3. Check for prior art before falling in love. Muscle-mem was taken. Saguaro had
   the architecture already. Find that out on day zero.
4. **Read the brief before the ideas, and again after.** Two weeks of consumer
   ideation went into a developer-tools event. One read of the event page on day
   zero would have caught it.
5. **Mark unverified external facts as unverified, inside the doc.** A confident
   sentence about a prize nobody confirmed is how you optimise hard in the wrong
   direction.
