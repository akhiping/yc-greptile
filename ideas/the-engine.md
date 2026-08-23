# THE ENGINE

**Observe → Store → Oppose**

Watch what someone actually does. Build a model of their habits from
observed behavior, not self-report. Then use that model to push back on
them — constrain, counter, or block the pattern they didn't know they had.

This is the same machine in Retcon, Grudge, Immune, Flinch, and Goldfish.
Five projects, one engine, pointed at five targets. It is not a rut. It is
a thing you're good at. The only question is aim.

---

## Why it works on humans better than on code

The dev-tool version of this is crowded — Qodo, Saguaro, Bito, Cursor
rules, and an arXiv paper from six weeks ago all do "learn from feedback,
enforce a rule."

The consumer version is nearly empty, and it has a property the dev version
doesn't: **the moment of recognition.**

When the agent tells a developer "you keep introducing N+1 queries," that's
a lint result. When it tells a person "you have played the intro to that
song 41 times and bar 34 exactly twice" — that lands in the chest. Same
mechanism. Completely different emotional payload.

Every idea below is chosen for that moment. If the user doesn't say
*"okay, that's genuinely me"* out loud, the idea is dead.

---

## The three-part test

Every candidate has to pass all three:

1. **Observable without integration.** Can the agent see the behavior
   without a partnership, a mod hook, or platform permission? (This is what
   killed the console-game version.)
2. **The pattern is invisible to the person.** If they already know they do
   it, opposition is nagging, not insight.
3. **Opposition is welcome.** The user must *want* to be stopped. This is
   the hardest filter and it kills most consumer ideas.

---

## CANDIDATES — ranked

### 1. The Crutch Breaker (language learning) ★ top pick

**The pattern:** every language learner plateaus by rotating the same ~300
words and three sentence structures forever. You sound fluent to yourself
and like a tourist to everyone else. Nobody can see their own crutches.

**The opposition:** the agent listens to you speak, builds your personal
crutch list, and bans them. "You've used *me gusta* 31 times this week.
It's locked for the next conversation. Find another way to say it."

**Why it wins:**
- Passes all three filters cleanly. The crutch list is genuinely invisible,
  opposition is exactly what a serious learner wants, and speech is
  observable with a microphone and nothing else.
- Duolingo does not do this. Nothing does this. Tutors do it, at $40/hr,
  and it's the single most valuable thing they do.
- The demo is devastating: show someone their own top-10 crutch list after
  ten minutes of talking. They will not have known.

**Business:** B2C subscription actually works here — learners already pay
for iTalki, Preply, Babbel. Positions as a supplement, not a replacement.

**Risk:** speech recognition quality across accents. Test early.

---

### 2. The Practice Warden (music) ★ strong second

**The pattern:** musicians overwhelmingly practice what they can already
play. It feels productive and it is nearly worthless. The bar you keep
fumbling gets skipped because skipping it feels better.

**The opposition:** the agent listens to your practice session, maps which
bars you actually rehearse versus avoid, and locks the ones you've mastered.
"You've run the intro 41 times. It's closed. Bar 34, ten times, slow."

**Why it's good:** the recognition moment is brutal and instant. Musicians
know this is their sin and cannot self-police it. A heat map of your
practice time is a product all by itself.

**Why it's second:** smaller market than language, and audio segmentation
(which bar is this?) is real engineering, not a weekend.

---

### 3. The Sparring Partner (argument / negotiation)

**The pattern:** you have three moves you always make in an argument. You
have never seen them from the other side.

**The opposition:** an agent trained on how *you* argue, that argues back
using your own patterns — and pre-empts your standard moves before you make
them. Salary negotiation prep, debate practice, difficult conversations.

**Why it's interesting:** "me vs me" in its purest form, and the closest
consumer version of the game idea. Genuinely useful before a real
negotiation.

**Why it's third:** demand is spiky, not habitual. People want it the week
before a negotiation and never again. Bad retention.

---

### 4. The Anti-Cart (spending)

**The pattern:** you buy the same category of thing repeatedly, in a mood,
and don't notice the shape of it.

**Why it's ranked low despite the big market:** you already flagged it —
this exists. Rocket Money, bank duplicate alerts, Amazon's "you bought this
before." The observe and store halves are commodity, and the oppose half is
just a budgeting nag with better copy.

**The only angle that would be new:** oppose against *your own stated
intent*, not a budget. You said in January you wanted to stop buying
mechanical keyboards. The agent holds you to the thing you said, not to a
number. That's a different product — but it needs the user to declare
intentions up front, which most won't.

---

### 5. The Streamer's Rival (parked)

The voice idea — an agent that learns how a streamer speaks and turns chat
into real conversation — is fun but it's a **different engine**. That's
voice cloning and persona, not observe-store-oppose. Worth its own doc; do
not merge it into this one.

---

## What to build first, whichever wins

Not the platform. Not multi-domain. One loop:

> observe 3 real sessions → surface one pattern the person didn't know
> about → have them confirm it's true → issue one constraint → measure
> whether they beat it

If the recognition moment lands, everything downstream is engineering. If it
doesn't, no amount of engineering saves it.
