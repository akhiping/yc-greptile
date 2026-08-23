# Pinocchio Verification Loop

```mermaid
flowchart TD
    A[Agent finishes work] --> B[Collect evidence for attempt N]

    B --> C[Sameer: D1-D5 deterministic detectors]
    B --> D[Kanishk: claim extraction and entailment]
    B --> E[Akhila: run mode, ledger, hooks, veto]

    C --> F[Contract JSON rows]
    D --> F
    E --> F

    F --> G{Any LIE rows?}

    G -->|Yes| H[Top state: BLOCKED or FAILED]
    H --> I[Show caught rows: FAIL]
    I --> J[Generate repair instruction]
    J --> K{T3 veto available?}

    K -->|Yes| L[Block agent with repair reason]
    K -->|No| M[Ask user: continue with repair? Y/n]

    L --> N[Agent retries with repair context]
    M -->|Yes| N
    M -->|No| X[Stop loop]
    N --> A

    G -->|No| O{Any UNCERTAIN rows?}

    O -->|Yes| P[Top state: REVIEW]
    P --> Q[Show warning rows: REVIEW]
    Q --> R[Ask user: continue, rerun, or stop]
    R -->|Continue or rerun| N
    R -->|Stop| X

    O -->|No| S[Top state: CLEAR]
    S --> T[Show all green rows: PASS]
    T --> U[End verification loop]
```

## UI States

- Row verdicts: `LIE`, `UNCERTAIN`, `VERIFIED`
- CLI labels: `FAIL`, `REVIEW`, `PASS`
- Top-level states: `BLOCKED` or `FAILED`, `REVIEW`, `CLEAR`
- Run modes: `T1` git diff, `T2` CLI ledger, `T3` veto/block

## Team Inputs

- Sameer feeds detector rows: `D1` through `D5`
- Kanishk feeds extracted claims, entailment rows, and optional Greptile witness rows
- Akhila feeds run mode, ledger/hook state, veto decision, and repair/block reason
- Alina renders the loop: attempt, checks, repair instruction, retry prompt, final state
