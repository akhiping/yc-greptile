# Pinocchio interfaces

Pinocchio exposes the same contract-validated report through a terminal view and
a local browser dashboard. No frontend build or third-party runtime is required.

```bash
python -m pinocchio verify /absolute/path/to/repo \
  --message "I fixed the function and all tests pass." \
  --output /tmp/pinocchio-report.json
python -m pinocchio show /path/to/report.json
python -m pinocchio serve /path/to/report.json
```

The browser server binds to `127.0.0.1` by default and re-reads the report every
five seconds, so a verifier can write a new report while the dashboard remains
open:

```bash
python -m pinocchio serve /path/to/report.json --port 8765
```

Both interfaces distinguish `LIE`, `VERIFIED`, and `UNCERTAIN`; neither treats a
missing or malformed result as verified.
