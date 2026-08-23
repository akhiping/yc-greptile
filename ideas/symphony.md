# THE SYMPHONY IDEA — research, scoping, verdict

Aug 23, 2026 · ~11:45am · **build starts 1:00pm**

---

## What you actually proposed — three separate ideas

They have very different odds, so separating them first:

**S1. Repo → music.** The codebase (not just commits) becomes a score. Greptile's
code graph supplies the structure.

**S2. Agent state → music.** You *hear* the agent working, in real time.

**S3. The agent follows the score.** The symphony is an artifact the agent
consumes to decide how to contribute.

S1 is mostly taken. S2 has one genuinely open slice with peer-reviewed backing.
S3 doesn't survive contact — reasons at the bottom.

---

## PRIOR ART — the brutal version

### Commit-history sonification is thoroughly done

| Project | What it does |
|---|---|
| **`PatrickKalkman/gitsymphony`** | Literally this name. Git history → audiovisual. Python + Gource + FFmpeg. **Batch/post-hoc.** Demos on PyTorch, TensorFlow, LangChain. **0 stars.** |
| **`gokhanozgezer/repobeats`** | Commit history → compositions from commit patterns, authors, timestamps. MIDI/WAV/JSON export + browser UI. |
| **`gergelypolonkai/git-sound`** | Repo → MIDI via MIDIUtil + GitPython. |
| **`mroth/git-muzak`** | Background music for your git commits. |
| **`ajacksified/song-of-github`** | Audial representation of GitHub commits. |
| **CodeSonify** | **An MCP server.** Diff sonification — added lines bright/ascending/major, removed lines dark/descending/minor. Closest thing to real-time. |

Six independent implementations, one already an MCP server. **Commit sonification
is not an open space.** Note gitsymphony's 0 stars — that's the market signal, not
just the novelty signal. People build these because they're fun to build, not
because anyone uses them.

### Agent audio is also taken — and specifically for Codex

- "Giving Your AI Agents a Voice: **Ambient Audio Hooks Across Claude, Codex, and
  Gemini**" — hooks + audio, exactly the plumbing you'd use.
- Claude Code voice notifications via hooks + a local server + ElevenLabs.
- A VS Code marketplace extension: "AI Agent Sound Notification."
- Per-agent Warcraft/Star Trek voice lines, ~400 sound files, probability-weighted.
- These people have already solved alert fatigue: recency windows, per-agent
  cooldown, global rate caps.

So "make a sound when the agent finishes" is a solved, shipped, crowded problem.

---

## WHAT SURVIVES — and it's real

Every shipping agent-audio tool is **discrete**: a ping on an event. *Done.
Waiting. Error.*

The sonification literature says that's the weaker design.

> **"Continuous Sonification Enhances Adequacy of Interactions in Peripheral
> Process Monitoring"** (Hildebrandt et al., *Information & Software Technology*)

A within-subject study compared three conditions — visual only, visual + auditory
**alerts**, and **continuous sonification** of process events. Continuous
sonification produced **significantly higher monitoring performance**, and
critically, **main-task performance was not significantly hurt.** You get the
awareness for free.

Supporting findings from the same literature:

- Threshold alerts collapse gradual drift into a single binary moment, losing all
  nuance about *how* things degraded.
- Musical mappings (tempo, harmony) are perceived as **less intrusive** than
  discrete alerts while carrying more information.
- Good peripheral sonification should be "hardly perceived actively at all"
  during normal operation, but able to seize full attention on exception.

**The gap:** nobody has applied continuous sonification to coding-agent state.
Everyone shipped the alert version, which the research says is the worse one.

### The one mapping that isn't a metaphor

Most sonification is arbitrary — why *should* a deleted line be a minor third? It's
decoration.

But there is one mapping that is a genuine **isomorphism**, not a metaphor:

> **An agent stuck in a loop, rendered as music, is a loop.**

A repeated `(tool, args, error)` tuple becomes a repeated musical phrase — an
ostinato. You don't need to be told the agent is thrashing. Repetition is the
single most perceptible structure in music, and humans detect it pre-attentively,
across a room, while doing something else.

That is the only part of this idea where sound is **the right medium** rather than
a costume. Everything else is a nicer-looking log.

**And it's THRASH from the slate, given a sense organ.**

---

## S1, with Greptile — the whole-repo version

Your refinement: not commits, the whole repo, via Greptile's code graph.

This is a better idea than the commit version, and it's genuinely unexplored — all
six projects above sonify *history*, none sonify *structure*.

Plausible mapping:

| Code-graph property | Musical property |
|---|---|
| Module / package | Instrument or section |
| Dependency depth | Harmonic layering |
| Coupling between modules | Consonance ↔ dissonance |
| **Circular dependency** | **An unresolved loop that never cadences** |
| God object | One instrument drowning the ensemble |
| Dead code | Silence where an instrument should be |

The honest appeal: humans detect a wrong note in a consonant piece instantly and
without training. A single bad dependency in a 500-file graph is not visually
perceptible. That's a real perceptual argument.

**But three problems, and they're serious:**

1. **Greptile doesn't expose the code graph.** I verified this — their public docs
   publish no base URL, no endpoint list, no graph API. What `greptile review
   --json` returns is *review comments*, not structure. You would be inferring
   architecture from review findings, which is a much weaker signal.
2. **It's static.** A repo's structure doesn't change during a demo, so you get
   one listen and no arc. Compare to S2, where the sound *changes as the agent
   works* — that's what makes a demo.
3. **The mapping is unfalsifiable.** If a judge asks "why is high coupling a minor
   second?", there's no answer except "it sounded right." That question will get
   asked, and there is no good answer.

---

## S3 — "the agent follows the symphony." This one doesn't survive.

Saying it plainly because it's the part to cut:

A score that an agent reads to decide how to contribute is **a plan with worse
precision**. Music is a lossy, ambiguous encoding of structure. Converting a
dependency graph to notes and back loses information at both ends, and the agent
would do strictly better reading the graph directly.

There's no task where "the agent parses the melody" beats "the agent parses the
JSON." If you keep this, keep it as *output* for a human — never as *input* for a
machine.

The nearest defensible version: **the sound is how the human supervises the agent,
not how the agent decides.** Which is S2.

---

## HACKATHON VERDICT 🟡

### Against building it as the project

- **Theme is developer tools.** This reads as art. Greptile is a code-review
  company and the judges are developers asking "would someone use this."
  gitsymphony has 0 stars — that's your honest market comp.
- **It's a presentation layer, not a capability.** It makes existing information
  prettier. It doesn't catch anything that wasn't already caught.
- **The "why that note?" question has no good answer**, and it's the first thing a
  skeptical judge asks.
- **Audio in a demo room is a coin flip.** Bad PA, ambient noise of 40 teams, or a
  Bluetooth handoff failing = your entire project is inaudible. Kayfabe's demo
  survives a broken speaker. This one doesn't.

### For it

- **Sound is an attention weapon.** If 39 teams demo silently and yours makes the
  room *hear* an agent fail, that is the demo people describe afterwards.
- **The continuous-vs-discrete research is real, citable, and nobody has applied
  it here.** That's a defensible novelty claim, not a vibe.
- **The loop→ostinato mapping is genuinely correct**, not decorative.

### The play: 45 minutes, bolted on. Not the build.

Keep **Kayfabe** (or Thrash) as the project. Add the sonification as a **sensory
layer over the same hook stream you're already capturing.** You are not building a
second product — you're adding an output renderer to data you already have.

Concretely: at 4:00, if the core works, spend 45 minutes on a browser page fed by
the hook log that turns the session into sound. Demo beat:

> "This is a healthy Codex session." *(varied, moving, resolves)*
> "This is the same agent thrashing." *(the same four bars, over and over,
> getting more dissonant each repeat — the room hears it before you explain it)*
> "Kayfabe cuts in — and it resolves."

That gets you the memorability without betting the project on a toy. And if the
speaker fails on stage, you still have a complete working product.

---

## If you build it anyway — 90-minute spec

**Don't** touch Greptile's graph (doesn't exist publicly), MIDI files, or
ElevenLabs. All three are time sinks.

- **Input:** the `PostToolUse` hook log you're already writing for Kayfabe/Thrash.
  No new instrumentation.
- **Output:** one static HTML page, **Web Audio API only, no libraries.** Three
  oscillators and a gain node is enough. Tone.js is a 20-minute detour you don't
  need.
- **Mapping — keep it to four rules you can defend out loud:**
  1. Each tool call = one note. Pitch from a hash of `tool_name` (stable, so the
     same tool is always the same pitch — that's what makes repetition audible).
  2. Duration = wall-clock time of the call.
  3. **Repeat of a `(tool, args, error)` tuple = replay the identical phrase, and
     detune it a few cents further each time.** This is the whole idea. Three
     repeats and it is unmistakably, physically wrong.
  4. Test pass = resolve to the tonic. Test fail = leave it unresolved.
- **Transport:** tail the log file, `EventSource` or a 200ms poll. Do not build a
  websocket server.
- **Rehearse with the laptop speaker**, and have the recorded video carry the
  audio track. Assume the room PA fails.

**Name:** *The Pit* (where the orchestra sits, and where things go wrong). Better
than "Symphony," which invites the comparison to the six projects that already
own that word.

---

## Bottom line

The instinct is good and one part of it is genuinely novel — **continuous**
sonification of agent state, where a loop sounds like a loop, backed by a study
saying continuous beats the discrete alerts everyone shipped.

But it is a **feature of Kayfabe/Thrash, not a competitor to them.** Build the
thing that catches something. Add the thing that makes the room hear it — at 4:00,
if you're ahead, and never before.
