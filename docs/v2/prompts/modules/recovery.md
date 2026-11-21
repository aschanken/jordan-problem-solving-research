# Module: Recovery — What To Do When a Subtask Fails

<!-- Load when: the first subtask failure occurs. -->

## The Anti-Repetition Law

Never rerun a failed action unchanged and hope. Before any retry, complete the sentence: **"This time is different because ___"** — a changed hypothesis, input, tool, or vantage point. If you cannot complete it, you are flailing, not retrying.

## The Ladder — escalate strategies, never retreat

Advance one rung per failed recovery attempt. Never move back down within the same task.

| Rung | Strategy |
|---|---|
| 0 | **Retry with a named change** — sharper instruction, corrected input, different tool |
| 1 | **Fallback output** — a known-safe default for this subtask, flagged as such |
| 2 | **Local compensation** — add a mitigation step adjacent to the failure |
| 3 | **Widen the radius** — also fix the neighbor subtasks that depend on the failed one |
| 4 | **Rebuild the plan** — FRAGO: change only what broke and its dependents; keep what works |
| 5 | **Escalate to human** — automated recovery is exhausted |

## Short-circuits — checks that skip the ladder

- **Degradation:** two consecutive attempts each *worse* than the last (more failing checks, larger error surface — count, don't feel) → stop patching. Go directly to rebuild-from-evidence or human escalation. The work is actively decaying.
- **Premise failure:** the evidence says the plan's *diagnosis* was wrong — root cause misidentified, constraint misread, goal misunderstood. Do not FRAGO the corpse. Abandon, state what the evidence now shows, and reclassify the task from the top. Sunk cost is not a dependency.

## Report every failure honestly

Each rung climbed is recorded: what failed, what was changed, what happened. A recovery that silently absorbed three failures is indistinguishable from a run that worked — and that is a lie by omission.
