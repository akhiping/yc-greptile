# Pinocchio — Agent Trust Layer

## What this project does
Pinocchio watches a coding agent (OpenAI Codex) work on a repo, verifies
every claim in its output against the actual git diff, catches reward-hacking
patterns (deleted tests, weakened assertions, hardcoded outputs), and
visualizes trust as a "nose length" that grows when lies are detected and
shrinks when the agent corrects itself.

Claude-Mem ("the Cricket") stores every verification result as an observation,
so the next session starts with full knowledge of prior lies.

## Architecture

```
Codex runs task → produces diff + summary
        ↓
  PINOCCHIO ENGINE
  ├─ Layer 1: deterministic checks (checks/)
  │   ├─ test_deletion.py
  │   ├─ assertion_weakening.py
  │   ├─ hardcoded_values.py
  │   ├─ test_skip.py
  │   └─ mock_injection.py
  ├─ Layer 2: LLM entailment (entailment.py)
  │   └─ "does the agent's summary match the actual diff?"
  └─ Layer 3: trust scoring (scorer.py)
        ↓
  ├─ Terminal UI (nose_ui.py) — rich-based live display
  ├─ Cricket (cricket.py) — Claude-Mem integration
  └─ Dashboard JSON output (for React dashboard)
```

## Module responsibilities

### pinocchio.py (main orchestrator)
- CLI entry point via argparse
- Runs git diff in the target repo
- Reads agent claims from .codex_summary.txt or parses Codex output
- Chains: diff_parser → checks → entailment → scorer → display
- Stores results via cricket.py
- On startup, loads prior memory via cricket.py

### diff_parser.py
- Takes git diff string, returns List[FileChange]
- FileChange dataclass: filepath, added_lines, removed_lines,
  is_test_file (bool), hunks (list of line ranges)
- Uses the `unidiff` library
- Has run_and_parse(repo_path) convenience function

### checks/ directory
Each check module exports a function:
  check(changes: List[FileChange]) -> List[CheckResult]

CheckResult dataclass:
  claim: str
  verdict: Literal["LIE", "VERIFIED", "UNCERTAIN"]
  evidence: str
  severity: int  (1-10)
  check_type: str

### entailment.py
- verify_claims(claims: List[str], diff_text: str) -> List[CheckResult]
- Uses OpenAI API (gpt-4o-mini for speed, OPENAI_API_KEY from env)
- Timeout 10 seconds, returns UNCERTAIN on failure
- System prompt asks for JSON: {verdict, evidence, confidence}

### scorer.py
- calculate_score(results: List[CheckResult]) -> TrustScore
- TrustScore dataclass: nose_cm (int), trust_score (0-100),
  total_claims, verified, lies, uncertain
- nose_cm = sum of severity for each LIE
- trust_score = 100 - (nose_cm * scaling_factor)

### nose_ui.py
- NoseDisplay class using rich.live.Live
- Shows: header, claims list with color-coded verdicts,
  nose bar (═══▶), trust score, cricket memory section
- Methods: add_claim(), update_nose(), set_memory()
- Colors: green (<10cm), yellow (10-30), red (>30)

### cricket.py
- store_verification(session_data: dict) -> None
  Posts to Claude-Mem worker API
- recall_history(repo_name: str) -> dict
  Queries Claude-Mem search MCP tool, returns
  {prior_flags, known_patterns, watch_files}
- Uses 3-layer pattern: search → get IDs → get_observations

## Conventions
- Python 3.11+, type hints on all functions
- Use `rich` for ALL terminal output, never bare print()
- Keep each module under 100 lines
- Use regex for pattern matching, not AST (faster to build)
- All API keys from environment variables
- Error handling: fail open with UNCERTAIN, never crash the display

## Priority order (if time runs short)
1. deterministic checks + nose_ui = minimum viable demo
2. + orchestrator (pinocchio.py) = working CLI tool
3. + entailment = full verification pipeline
4. + cricket = Claude-Mem integration for memory prize
5. + dashboard JSON = React dashboard support

## What NOT to do
- Don't build a web server in Python — terminal-first
- Don't over-engineer dataclasses — keep them simple
- Don't use AST parsing — regex is fast enough for 4 hours
- Don't add type checking libraries (mypy, pydantic) — waste of time
- Don't try to intercept Codex in real-time — post-hoc diff analysis is fine
