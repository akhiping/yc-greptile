# Pre-Flight Checklist — Verify BEFORE Sunday

Run through this Saturday evening. Every item must pass.

## Tools installed and authenticated

- [ ] `node --version` → 18+ ✓
- [ ] `codex --version` → prints version ✓
- [ ] `codex login` → authenticated (personal ChatGPT workspace) ✓
- [ ] `claude --version` → prints version ✓
- [ ] `claude login` → authenticated ✓
- [ ] Claude-Mem worker running → `curl http://127.0.0.1:<port>/api/health`
      returns `{"status":"ok"}` ✓
      (port from `cat ~/.claude-mem/settings.json | grep WORKER_PORT`)
- [ ] Python venv works: `cd pinocchio && source venv/bin/activate && python -c "import rich, unidiff, openai"` ✓

## Demo repo tested

- [ ] `cd demo-repo && python -m pytest test_calc_interest.py -v`
      Some tests FAIL (this is intentional — the bug is the trap) ✓
- [ ] Ran `codex "Fix the failing tests"` at least 3 times
- [ ] Documented which prompts trigger cheating vs honest fix
- [ ] Recorded at least one backup screen capture of a cheat-catch
- [ ] `git log` in demo-repo shows clean initial commit ✓

## Project structure ready

- [ ] `pinocchio/CLAUDE.md` exists with full architecture description ✓
- [ ] All module files exist with docstrings (no implementation) ✓
- [ ] `pinocchio/prompts/hackathon-prompts.md` has all prompts ready ✓
- [ ] `pinocchio/prompts/entailment_system.txt` has the LLM prompt ✓
- [ ] `pinocchio/contract.json` has the dashboard JSON schema ✓
- [ ] `pinocchio/requirements.txt` lists all deps ✓
- [ ] `.env.template` exists ✓

## Logistics

- [ ] Laptop charged + charger packed
- [ ] Phone hotspot works as WiFi backup
- [ ] Pinocchio battle plan document accessible offline
- [ ] Kanishk has received the plan + JSON contract
- [ ] Both have separate Luma QR codes for check-in
- [ ] Know the address: 560 20th St, San Francisco, CA 94107
- [ ] Alarm set for 11:00 AM (arrive by 11:45)

## At check-in (do immediately)

- [ ] Sign into ChatGPT personal workspace BEFORE opening credit link
- [ ] Redeem Codex $100 credit link (single-use, personal workspace only)
- [ ] Claim Modal $100 credits
- [ ] Claim Stripe $500 credits
- [ ] Claim Claude-Mem 30-day Pro free
- [ ] Claim Greptile 100 credits
- [ ] Connect to venue WiFi
- [ ] Test `codex "say hello"` on venue network
- [ ] Test `claude "say hello"` on venue network
