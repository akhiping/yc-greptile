# `greptile review --json` — verified schema and behaviour

Tested live on Aug 23, 2026 against a throwaway branch in `kayfabe`. This is the
data path The Bouncer would consume from a Codex `Stop` hook.

## Auth: API key is enough for review

| Command | API-key auth |
|---|---|
| `greptile whoami` | ✅ works |
| `greptile review` | ✅ **works** |
| `greptile skills install` | ✅ works (no auth needed at all) |
| `greptile init` | ❌ **rejects API keys** — "requires signing in with your Greptile account" |

So repo enablement needs the browser flow or the dashboard, but **the local
review loop does not**. The Bouncer is unblocked.

Exit code was `0` on a review that returned findings — so **gate on the parsed
JSON, never on the exit code.** Same trap as `greptile whoami`, which exits 0
while printing "Not signed in".

## Response shape

```jsonc
{
  "summary": "…markdown…",
  "confidence": 4,                  // 1–5
  "confidenceReasoning": "…",
  "securitySummary": null,
  "instructions": null,
  "comments": [
    {
      "id": "comment-1787507475098-vju1e3e",
      "path": "sample/discount.py",
      "startLine": 1,
      "endLine": 1,
      "side": "new",
      "severity": "P2",             // P0…P3
      "securityIssue": false,
      "category": "comment",
      "body": "**Title**\n\n…markdown…",
      "verifiedEvidence": null,
      "suggestion": null,
      "hunk": {
        "header": "@@ -0,0 +1,8 @@",
        "oldRange": { "start": 0, "lines": 0 },
        "newRange": { "start": 1, "lines": 8 },
        "before": "def apply_discount(price, percent):",
        "after": null
      }
    }
  ]
}
```

**For a Stop-hook veto:** block on `comments[]` filtered by `severity` in
`P0`/`P1`, or on `securityIssue == true`. Do not block on `confidence` alone —
Greptile's own `greploop` skill says the score is "informational only" and "never
a reason to edit".

## It enforces AGENTS.md — confirmed

The only finding it returned was *"omit the type annotations required by
repository conventions."* Nothing in the diff mentions typing. That rule came
from the `AGENTS.md` I wrote before onboarding, which says *"Type hints on
anything public."*

**Greptile read the repo's agent rules and reviewed against them.** That makes
`AGENTS.md` a live control surface, not documentation — worth a sentence in the
demo.

## ⚠️ It missed a real crash bug

The test file had two deliberate defects:

```python
def apply_discount(price, percent):
    return price - (price * percent)     # ambiguous: 20 or 0.20?

def average(values):
    return sum(values) / len(values)     # ZeroDivisionError on []
```

Greptile flagged **only the missing type annotations** — a style issue — and
rated the branch confidence **4/5, "appears safe to merge."** It did not mention
the divide-by-zero.

In fairness the functions had no callers, and its reasoning said as much: "no
established blocking failure in current repository usage." That is a defensible
position, not a broken tool.

**But it changes the strategy:**

1. **A Bouncer built on Greptile alone would have let that through.** Don't pitch
   it as "the agent can't ship a bug" — pitch it as "the agent can't ship code
   that violates *this repo's own rules*," which is what it demonstrably does
   well.
2. **It strengthens the case for Kayfabe over a pure Bouncer.** A test that
   actually called `average([])` would have caught this instantly. Static review
   missed it; execution would not have. That is a real argument for the
   test-integrity angle, and it is now something you have *measured* rather than
   asserted.
3. If both ship, the honest framing is complementary: Greptile checks the code
   against the codebase, Kayfabe checks whether the tests are real. Different
   failure classes.
