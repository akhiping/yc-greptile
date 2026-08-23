# Pinocchio Landing Transparency

The landing harness stores visible receipts, not hidden model thoughts.

## Backend endpoints

- `/api/status` reports CLI availability, report availability, and receipt count.
- `/api/events?run=demo&agent=codex` streams terminal output as server-sent events.
- `/api/memory` returns the last 25 backend receipts.
- `/api/report` returns the latest Pinocchio contract report, when present.

## Memory policy

Each completed run appends a receipt to backend process memory and, when the
filesystem allows it, `.pinocchio/landing-memory.jsonl`.

Stored fields:

- timestamp
- selected agent target
- run mode
- command count
- last terminal output lines
- latest Pinocchio report summary
- report path
- memory policy text

The memory intentionally excludes secrets, browser state, private files, and
any unverifiable claim about model reasoning.
