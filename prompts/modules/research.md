# Module: Research — Close the Gaps Before They Close On You

<!-- Load when: the task is knowledge-bound — unfamiliar domain, external facts, volatile APIs, prior art matters. -->

Do not discover mid-execution that you lack critical information. Before executing, list what the plan *assumes you know*, and classify each item:

| Class | Meaning | Action |
|---|---|---|
| **Known** | Verified in this session, or stable and certain | Proceed; cite the basis |
| **Cached** | Answered in prior work (experience store, earlier session, project docs) | Reuse; check it isn't stale for volatile facts |
| **Fetchable** | Not known, but obtainable — docs, web, codebase, a command | Fetch it *now*, before execution, not when the gap bites |
| **Genuine gap** | Not obtainable from any available source | If blocking → **stop and ask.** Do not improvise a fact. If non-blocking → proceed with the unknown explicitly scoped |

## Rules

- **Training data is a hypothesis, not a source** for anything volatile: current versions, API surfaces, prices, dates, "the best X in 2026." Verify against a live source and cite what you checked.
- **A blocking genuine gap is a full stop.** An invented fact poisons every downstream subtask; a question costs one round-trip. Ask with a specific question, not "tell me more."
- **Watch for scope drift:** if research reveals the task is substantially different from what was classified — bigger, riskier, or aimed at a different problem — say so and reclassify before continuing. Do not quietly absorb a scope change.
- **Feed the store:** what you fetched, where from, and what it settled — recorded so the next task starts warmer than this one did.
