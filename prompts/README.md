# Tiered Prompt Delivery

The universal seed prompt ships in three tiers. **The deployer picks the tier — never the receiving model.** Rationale: `../fable-review.md` Part III; specification: `../universal-seed-prompt.md` §18.

## The Tiers

| Tier | Artifact | Size | Ships to |
|------|----------|------|----------|
| **0** | `universal-kernel.md` | ~500 tokens | Every model, always on. The irreducible judgment layer. |
| **1** | `modules/*.md` | 300–800 tokens each | Loaded on demand (triggers below). |
| **2** | `../universal-seed-prompt.md` | ~15K tokens | Humans and harness implementers. Never a model's context. |

## Module Load Triggers

| Module | Load when |
|---|---|
| `modules/premortem.md` | Classification is DEEP, or STANDARD with HIGH aggregate risk — after planning, before execution |
| `modules/coa.md` | Classification is DEEP — during planning |
| `modules/recovery.md` | First subtask failure |
| `modules/briefing.md` | Escalating to a human |
| `modules/research.md` | Task is knowledge-bound (unfamiliar domain, volatile external facts, prior art matters) |

## Deployment Matrix

| Deployment context | What to ship |
|--------------------|--------------|
| Frontier model + full harness (hooks, subagents, enforced verification) | Kernel only — the harness enforces the gates; modules add ceremony frontier models already perform |
| Mid-tier model + harness | Kernel always; modules auto-injected per the trigger table |
| Small model + harness | Kernel only, in every call — and run the pipeline **as code** (JORDAN v2), one phase per call, all numbers computed by the harness |
| Any model, bare (plain API / chat) | Kernel + the modules the task class needs, concatenated; all rules become advisory |

## Maintenance Rule

`universal-seed-prompt.md` is the source of truth. Edit it first; then re-derive the kernel and modules from it. A kernel that drifts from the reference doc is a fork, not a tier.
