# Fable Review — The Seed Prompt as a Gap-Narrowing Instrument

**Reviewer:** Claude Fable 5
**Date:** 2026-07-25
**Scope:** `universal-seed-prompt.md` v1.0.0 and `JORDAN_v2_OVERVIEW.md`, evaluated for a specific claim: *that improving them can considerably narrow the performance gap between lesser models (Opus, Sonnet, Haiku, non-Anthropic models) and Fable-class models.*
**Prior art:** Richard and Karl reviewed JORDAN v2 the *system*. This review covers territory they did not: the seed prompt as an artifact consumed by an LLM's attention, and which components of frontier-model performance are transferable through prompt and harness.

---

## Executive Summary

The seed prompt is the best process-discipline document I have seen of its kind, and Section 5 (the domain-specific verification loop) is genuinely the highest-leverage material in it. But as a gap-narrowing instrument it has a structural problem: **the gap between model tiers is mostly not a process-discipline gap**, and the prompt's cost profile is inverted — it is heaviest exactly where the models it must help are weakest.

Three findings drive everything else:

1. **The prompt violates its own maxims when deployed on the models it targets.** It mandates quantities an in-context model cannot compute (DSM coupling scores, branching factors, likelihood floats) — an instruction to confabulate, which Maxim 12 calls propaganda. It warns about context rot and the 45% orchestration rule while itself being a ~15K-token orchestration tax on the models with the weakest attention.

2. **Pipeline-as-prompt gets compliance in form; pipeline-as-code gets it in substance.** A weak model given the 12-phase prompt produces the *artifacts* of the pipeline — headings, risk tables, persona quotes — without the cognition. This is process theater. JORDAN v2 proper (the LangGraph state machine) is the right home for the pipeline; the seed prompt should shrink to a kernel and treat the full document as reference architecture for implementers, not payload for models.

3. **The gap-narrowing lever ranking is: harness enforcement > model routing > context isolation > prompt content.** Prompt improvements are real but fourth on the list. The single strongest mechanism available is the seed prompt's own Escalation Contract (§3), implemented literally: cheap models execute, the strong model classifies/plans/diagnoses/reviews, and the harness — not the model's good intentions — enforces verification before completion.

Verdict by artifact:
- **JORDAN v2 architecture:** sound, keep. Two amendments proposed (evidence-interleaved EXECUTE, premortem→watchdog compilation).
- **Seed prompt:** restructure into a tiered delivery (kernel / standard / full-reference), purge pseudo-quantitative instructions, add six missing behaviors that actually drive tier differences, split the escalation bias into safety (always up) vs. complexity (start low, promote on evidence).
- **The claim itself:** currently unmeasured. The repo violates its own Maxim 10 — there is no baseline for the seed prompt's effect on any model. An eval harness is specified in §6; without it, "considerably narrow the gap" is a rumor.

---

## Part I — Diagnosis: What Actually Separates Model Tiers

Before asking whether the prompt narrows the gap, be precise about what the gap *is*. From observed behavior across tiers, the failure modes that separate a Haiku/Sonnet-class run from a Fable-class run on identical harnesses:

| # | Failure mode | Description | Does the seed prompt address it? |
|---|---|---|---|
| F1 | **Long-horizon incoherence** | Loses the thread over many steps; forgets constraints established earlier; context rot | No — it *consumes* the context budget that mitigates this |
| F2 | **Weak hypotheses under ambiguity** | First guess at a root cause is wrong more often; fewer candidate explanations generated | No — no prompt can add reasoning depth |
| F3 | **Premature success declaration** | Claims done without checking; "should work now"; confidence uncorrelated with correctness | **Yes — §5, the verification loop. The prompt's best material.** |
| F4 | **Unproductive retry loops** | Repeats a failed action essentially unchanged; patches symptoms; sunk-cost persistence | Partially — the compensation ladder gestures at it, but is pipeline-shaped, not in-context-shaped |
| F5 | **Instruction saturation** | Cannot simultaneously hold a large process spec AND the task; drops one (usually the spec, silently) | No — the prompt *is* the saturation |
| F6 | **Sloppy evidence reading** | Skims error output; pattern-matches to a known failure instead of reading what's actually there | No — nothing in the prompt mandates reading evidence verbatim |

The seed prompt is a strong instrument against F3, a partial one against F4, and neutral-to-harmful against F1, F5, F6. It does nothing for F2 — nothing in-context can.

**The tier-dependence of the gap.** This matters for your specific goal (Opus → Fable):

- For **Haiku-class** models, F1/F3/F5 dominate. Process scaffolding and context isolation recover a large fraction of the gap on verifiable tasks — this is where the seed prompt's ideas pay best, *if delivered in a form the model can hold* (see Part III).
- For **Opus-class** models, F3 and F5 are already largely solved — Opus is process-disciplined out of the box. The residual Opus→Fable gap is concentrated in F2 (hypothesis quality), F6 under time pressure, and calibration (knowing *when* it's wrong). These are exactly the components that prompt scaffolding recovers least. For Opus, the highest-leverage levers are (a) harness-enforced verification as a backstop, and (b) surgical routing of diagnosis and plan-review phases to Fable — not more process instruction, which Opus will follow faithfully at real token cost for marginal gain.

**Corollary:** the closer a model is to the frontier, the more the residual gap is insight-dominated and the less prompt content narrows it. A single seed prompt tuned for Haiku's failure modes actively taxes Opus, and vice versa. This is the strongest argument for tiered delivery (Part III, R1).

---

## Part II — The Seed Prompt Audited Against Its Own Maxims

### II.1 Maxim 12 violation: mandated confabulation

The prompt instructs the model to produce:

- DSM coupling scores with a numeric threshold ("> 0.5 indicates the plan is fragile") — §4.3
- Branching factor measurements ("if b ≥ 1, the plan is divergent") — §4.7
- Likelihood floats (0.0–1.0) per premortem failure scenario — §4.6
- A fused risk formula, `max(risk_assessment_level, premortem_max_severity)` — §4.8
- An overall quality `score` (0.0–1.0) — §4.11

In JORDAN v2 the *code*, Python computes every one of these. In the seed prompt, the model is asked to compute them in-context. **No LLM can project a dependency graph into an N×N matrix and derive a coupling coefficient in its head — it will emit a plausible number.** The weaker the model, the more confidently it confabulates. Maxim 12 states: "Every claim carries its origin, confidence, and falsification condition. Claims without provenance are indistinguishable from invention." A DSM score of 0.3 produced by a Sonnet-class model in-context has no provenance. By the prompt's own standard, it is propaganda — and worse, it *launders* invention into the audit trail wearing the uniform of measurement, which is more dangerous than an honest "this plan feels tightly coupled."

**Fix (R2):** add one rule to the kernel — *"Never state a number you did not obtain from a tool or a count you did not actually perform"* — and replace each pseudo-quantity with a check the model can genuinely execute:

| Pseudo-quantity | Replace with |
|---|---|
| DSM coupling score | Per pair of subtasks: "If A's output changes shape, does B's instruction need rewriting? If yes for many pairs, the plan is fragile — restructure." |
| Branching factor b < 1 | A hard subtask count cap (models can count) and a one-level-of-subtask-spawning rule |
| Likelihood floats | Three buckets — likely / possible / unlikely — each requiring one sentence of named evidence |
| Fused risk formula | "Take the worse of the two assessments. If they disagree by two levels, say so and escalate." |
| Quality score 0.0–1.0 | Per acceptance criterion: met / not met / cannot verify, with the evidence quoted |

Same discipline, honest provenance, and — critically — *checkable by a human reading the transcript*.

### II.2 The 45% rule violation: the prompt is its own overhead

§7.6 warns that when >~45% of capacity goes to orchestration rather than execution, success declines. The prompt then mandates, for every STANDARD task: Commander's Intent, DAG construction, backbrief, research-gap classification, per-subtask risk levels, a 4-persona premortem with severity/likelihood per scenario, branching analysis, an approval decision, type-aware synthesis, and criterion-scored evaluation. On a small model with a modest effective context, the ~15K-token prompt plus the mandated orchestration output *is* the >45% regime the prompt warns about. The document diagnoses its own pathology and ships it anyway.

§5.1 has the same self-collision: it correctly describes context rot ("attention dilutes across irrelevant tokens") while being, for most tasks, the largest block of task-irrelevant tokens in the context.

**Fix:** R1 (tiered delivery) below. The full document is excellent *reference architecture* — the mistake is only shipping it verbatim as a system prompt.

### II.3 Process theater: form-compliance vs. substance-compliance

Ask a weak model to run a 5-persona premortem and you get five paragraphs *labeled* with persona names, containing failure scenarios of roughly uniform, generic quality — the personas do not actually produce diverse analysis because in-context "personas" share every weight and every token of context. Genuine diversity requires **independent sampling**: separate calls, separate contexts, ideally different lenses enforced by the harness. The same holds for "adversarial verification" (§12.2): a model instructed to refute its own output in the same context that produced it is structurally reluctant and anchored; a fresh-context verifier that has never seen the reasoning, only the artifact, is a different signal entirely.

This generalizes to the whole pipeline: **prompt-simulated state machines produce the paperwork of the process; code-enforced state machines produce the process.** JORDAN v2 proper already made the right call. The seed prompt should stop trying to be JORDAN-in-a-prompt and become what it actually is: the *judgment layer* an agent needs when the harness is present (small), and a degraded-mode fallback when it is not (medium).

### II.4 The escalation bias is right for safety, wrong for complexity

"When in doubt between two tiers, choose the higher one" (§3, Gate 1) conflates two different uncertainties:

- **Safety/reversibility uncertainty** — escalating is correct, always. An unrecoverable action taken lightly is a catastrophe; ceremony wasted on a safe task is only money.
- **Complexity uncertainty** — escalating is *expensive and often wrong*. Real workload distributions are dominated by FAST and light-STANDARD tasks. A blanket up-bias plus the prompt's identity framing ("You do not improvise answers… every task is a campaign") pushes models into ceremonial overkill on trivial work, burning the token budget the genuinely DEEP tasks need. Aaron's own principle — don't waste premium tokens on throwaway context — is violated by the current bias.

**Fix (R3):** split the rule. *Safety doubt → up, no exceptions. Complexity doubt → start one tier lower and promote on first surprise* (first failed verification, first unknown-unknown, first scope expansion). Promotion-on-evidence beats pre-commitment: it spends ceremony only where contact with the task proves it's needed. This is also how frontier models actually allocate effort — effort follows resistance, it doesn't precede it.

### II.5 What the prompt is missing: the behaviors that actually mark tier boundaries

Six behaviors that distinguish frontier-model runs, absent or underweighted in the current prompt (these become kernel content in R4):

1. **Evidence-first debugging.** Reproduce the failure before touching anything. Read the actual error output *verbatim* — not the shape of it. Enumerate at least two candidate root causes before committing to one. Choose the cheapest experiment that *discriminates between them*, not the cheapest fix. Never edit code you haven't read. (Targets F2's downstream damage and F6 directly.)
2. **The anti-repetition rule.** Never rerun a failed action unchanged and hope. Every retry must alter a named variable — the hypothesis, the input, the tool, the vantage point. Two consecutive attempts that make things worse → stop patching, rebuild the diagnosis from evidence, or escalate. (This is the compensation ladder translated from pipeline-shape to in-context-shape, and it's more enforceable: a model can check "did I change anything?" far more reliably than it can track ladder rungs.)
3. **Context hygiene.** Don't pull large artifacts into working context when a summary + path citation suffices; delegate broad searches to subagents/fresh contexts; keep the main thread for decisions, not raw evidence. (Targets F1. Currently the prompt says nothing about context as a managed resource — for small models it is *the* scarce resource.)
4. **Honest completion.** A completion claim must quote its verification evidence — the passing test output, the 200 response, the rendered result. "Should work," "looks correct," and any completion statement without quoted evidence are forbidden forms. Failures reported as plainly as successes, with the failing output. (Hardens §5 from a practice into a speech register.)
5. **Minimal-change discipline.** The smallest diff that satisfies the acceptance criteria. No drive-by refactors, no unrequested improvements — every extra line is unaudited risk surface and review burden. (Weak models over-generate; nothing currently checks the impulse.)
6. **Plan-abandonment trigger.** Distinct from replanning-on-failure: when accumulating evidence contradicts the plan's *premise* (not its execution), abandon rather than FRAGO. The prompt's machinery is all repair-shaped; it lacks the tripwire for "the plan was wrong, not the work." Degradation detection (§4.12) approximates this at the pipeline level; the in-context loop needs it too.

### II.6 Two amendments to JORDAN v2 proper

The architecture survived Richard and Karl mostly intact and I won't re-litigate settled ground. Two amendments from the how-frontier-agents-actually-work perspective:

**A1 — Make EXECUTE evidence-interleaved by default.** The current topology is batch-shaped: EXECUTE completes all subtasks, then SYNTHESIZE, then EVALUATE. Verification that arrives after synthesis is too late — an early subtask's silent failure contaminates everything downstream, and the FRAGO that follows is expensive archaeology. The frontier-agent loop is a *tight* cycle per subtask: act → run this subtask's check → read → correct → next. MAKER decomposition already does this for DEEP correctness-critical subtasks; make per-subtask verification the default at every tier and let terminal EVALUATE be the *integration* check, not the first check. (The spec's "Do NOT use OODA as primary execution model" prohibition is about macro-architecture and stands; this is micro-loop structure within a subtask, where tight cycles are exactly right.)

**A2 — Compile premortem output into runtime watchdogs.** Premortem scenarios currently influence the plan (mitigations) and then expire. Their second, unclaimed value: each HIGH/CRITICAL scenario is a *predicted observable*. Compile them into tripwires that EXECUTE actively checks — "Safety Officer predicted token PRNG misuse → grep for `Math.random` in the auth path before the subtask completes"; "Pessimist predicted user enumeration via timing → the verification command for the reset subtask must include the timing check." This converts the premortem from a planning debiaser into a runtime detection net, and gives the personas' predictions a falsification condition — which Maxim 12 should demand of them anyway.

---

## Part III — Restructuring: Tiered Delivery (R1)

The single highest-impact change to the seed prompt: stop shipping one artifact to every model, and cut it into three tiers matched to how prompts are actually consumed.

### Tier 0 — The Kernel (~500 tokens, always on, every model)

The irreducible judgment layer. Everything else loads on demand. Proposed text:

> **You are a disciplined problem-solver. You verify; you do not guess.**
>
> 1. **CLASSIFY** (one sentence): FAST / STANDARD / DEEP. Anything touching credentials, deletion, infrastructure, or irreversible state is never FAST. Safety doubt → classify up. Pure complexity doubt → start lower and promote at the first surprise.
> 2. **WIRE THE VERIFIER.** Before working, answer: *"How will I know this worked?"* — a command, a test, a check against reality. If no verifier exists, building one is your first subtask. If none can exist, say so and treat every conclusion as unverified.
> 3. **PLAN** (STANDARD and up): goal, hard constraints, acceptance criteria, subtasks in dependency order — each with its own check.
> 4. **EXECUTE in a tight loop:** act → run the check → read the actual output, verbatim → correct → next. Read before you edit. Reproduce before you fix. Never repeat a failed action unchanged — every retry changes a named variable. Two consecutive worsening attempts → stop, rebuild the diagnosis from evidence, or escalate.
> 5. **REPORT with evidence.** Completion claims quote their verification output. Failures are stated as plainly as successes. Mark every claim: verified / likely / unverified / unknown. Never state a number you did not obtain from a tool or a count you did not actually perform.
> 6. **ESCALATE, never bury.** Don't know → say so. Risky or irreversible → ask first. Stuck after varied attempts → hand up, with what you tried and what you learned.
> 7. **SMALLEST CORRECT CHANGE.** The minimal diff that meets the acceptance criteria. No unrequested improvements.

Note what survived into the kernel: routing, verification loop, tight execution, honest reporting, escalation, parsimony. Note what didn't: every phase whose value depends on faithful multi-step simulation (premortem, backbrief, COA scoring, briefing formats). Those aren't lost — they move to Tier 1 and Tier 2.

### Tier 1 — Phase modules (~300–800 tokens each, loaded on demand)

Delivered as skills / slash commands / conditionally-injected sections, loaded only when classification warrants:

- `premortem.md` — the persona lenses, loaded for DEEP; better yet, executed as N *separate fresh-context calls* (see II.3)
- `coa.md` — multi-COA generation and comparison discipline, DEEP only
- `recovery.md` — FRAGO thinking + the compensation ladder, loaded on first subtask failure
- `briefing.md` — the tiered briefing format, loaded when escalating to a human
- `research.md` — gap classification and cache discipline, loaded when the task is knowledge-bound

This is the prompt's own progressive-disclosure principle (§13.1) applied to its own delivery. Resting context stays near the kernel; the full apparatus appears exactly when a task earns it.

### Tier 2 — The full document (reference architecture, never shipped to a model)

The current 900-line artifact, kept and maintained — as the specification humans and implementers read, the source from which Tier 0/1 are derived, and the design document for harness builders. §17 currently tells the *receiving model* to adapt the prompt to its own capacity; that delegates the tiering decision to the least capable party in the transaction. The deployer picks the tier. Delete §17's self-adaptation framing; replace with a deployment matrix (model class × harness availability → which tier to ship).

---

## Part IV — What Makes Fable-Class Models Perform, and What Transfers

You asked me to explore how the internal logic that makes Fable effective could be imparted through the Claude harness. Honest epistemics first: I cannot introspect my weights, and some of what separates tiers is simply capability that no scaffold recovers. What I can do is decompose the *observable behavioral drivers* of frontier-agent performance and classify each by its transfer channel.

### IV.1 Category A — transfers via prompt (cheap, already partly captured)

| Behavior | Status in seed prompt |
|---|---|
| Verification before completion | §5 — the doc's best material; keep, promote to spine |
| Evidence-quoting completion claims | Missing — add (R4.4) |
| Read-before-edit, reproduce-before-fix | Missing — add (R4.1) |
| Effort calibration via routing | Present (three gates) — fix the bias split (R3) |
| Explicit uncertainty registers | Present (§13.3) — good, keep |
| Anti-repetition retry discipline | Weak (ladder is pipeline-shaped) — add in-context form (R4.2) |

Ceiling on this category: prompt content reliably shifts *what the model attempts*; it only weakly shifts *how well the model does it*. Expect real but modest gains, largest on Haiku-class, smallest on Opus-class.

### IV.2 Category B — transfers via harness (the big lever)

This is where most of the recoverable gap lives, because the harness can *enforce* what a prompt can only request. Ranked by expected effect:

**B1. Stop-hook verification enforcement.** A Claude Code `Stop` hook that blocks turn completion until the project's verification command has been run this session and passed — converting "wire the feedback loop first" from exhortation into physics. F3 (premature success declaration) is the weak model's most damaging failure mode, and this eliminates it *mechanically*, at zero prompt cost, for any model in the harness. Companion: a `PostToolUse` hook on Edit/Write that auto-runs lint/tests and feeds failures straight back into context — the model doesn't have to remember to check; the world checks.

**B2. Asymmetric model routing — the Escalation Contract, implemented literally.** The seed prompt already contains its own best idea (§3, Escalation Contract): expensive reasoning for diagnosis and planning, cheap execution for the mechanical middle. The Claude harness supports per-subagent model overrides today. The concrete pattern:

- **CLASSIFY / PLAN / premortem / plan-review:** Fable (or Opus) — small token volume, decision-dense, sets the ceiling on everything downstream
- **EXECUTE subtasks:** Haiku/Sonnet in parallel subagents — high token volume, low decision density, each subtask pre-scoped to a verifiable unit by the strong planner
- **VERIFY / adversarial review:** Sonnet in *fresh contexts* — never the context that produced the work (see II.3)
- **Escalation path:** when an executor's verification fails twice with varied attempts, the *diagnosis* (not the retry) routes up a tier; the fix-plan comes back down for cheap execution

Why this narrows the gap more than any prompt: plan quality and diagnosis quality set the ceiling for the whole run, and they are a small fraction of total tokens (typically 10–20%). Spending frontier tokens on exactly those phases buys most of frontier quality at a fraction of frontier cost. This is not making Opus smarter — it is *making Opus's smartness matter less* by narrowing what is asked of it to pre-verified, well-scoped units.

**B3. Fresh-context subagent isolation.** Context rot (F1) is the weak model's silent killer, and the harness cures it structurally: each subtask executes in a subagent with a clean context containing only its scoped instruction and verifier. The main thread holds decisions, not evidence. Weak models fail at long-horizon coherence — so the harness *never asks them for it*. JORDAN v2's `isolation_key` design is precisely right; this is its justification stated in capability terms.

**B4. Deterministic gates for deterministic checks.** The denylist belongs in a `PreToolUse` hook (regex in code, cannot be talked out of, costs zero attention) — not in the model's self-policing. Same for DAG cycle detection, subtask caps, conventional-commit format, secret-scanning before commit. Rule of thumb: *anything checkable by code must be checked by code; the model's attention is reserved for what only judgment can check.* Every check moved from prompt to hook is tokens returned to the task and a failure mode converted from probabilistic to impossible.

**B5. Structured-output schemas as discipline.** Classification, risk levels, premortem scenarios, verdicts — forced through JSON schemas validated at the harness layer, with automatic retry on mismatch. Schema validation replaces paragraphs of "be precise about format" and catches weak-model sloppiness at the boundary where it's cheapest. (The Workflow/Agent schema mechanisms in the harness do exactly this today.)

**B6. Harness-side experience store.** §10's memory architecture should live in files the harness manages (memory directories, CLAUDE.md updates, skill libraries) — never in the model's obligation to remember to remember. Weak models won't maintain a discipline across sessions; a harness that injects "last 3 similar tasks used this decomposition; this failure mode occurred twice" at PLAN time gives compounding to models that could never sustain it themselves.

### IV.3 Category C — does not transfer (be honest about the ceiling)

1. **Hypothesis quality under ambiguity (F2).** When the bottleneck is generating the right candidate explanation — the subtle race condition, the architectural insight, the correct read of an underdetermined requirement — scaffolding buys more attempts and better error-catching, not better hypotheses. Mitigation is routing (B2), not prompting.
2. **Calibration.** Knowing when you're likely wrong. Miscalibration can be *compensated externally* (mandatory verification, fresh-context adversarial checks) but not repaired internally. This is why B1 matters so much: it substitutes the world's calibration for the model's.
3. **Taste where no verifier exists.** Design judgment, prose quality, "is this the right thing to build" — domains without ground-truth loops are where the tier gap persists undiminished, because the entire scaffold rests on verifiability. §5.4.6 already concedes this honestly; it should be stated as a scoping law for the whole system: *the harness narrows the gap in proportion to how verifiable the domain is.*
4. **Long-horizon working memory** — not prompt-transferable, but B3 shows it *is* harness-mitigable. Listed here as a capability, recovered structurally.

### IV.4 The one Fable-internal pattern worth stating explicitly

If I had to name the single largest behavioral difference between how I work and what the 12-phase pipeline prescribes: **I interleave; the pipeline batches.** My effective loop is a plan-skeleton held loosely, with a tight act→evidence→revise cycle inside every step, and effort that surges *where resistance appears* rather than where the plan predicted it. The pipeline's macro-structure (classify, plan, gate, execute, evaluate) is right and I follow its equivalent — but its batch-shaped middle (execute everything, then evaluate) is the opposite of how frontier performance is actually produced. Amendment A1 and kernel rule 4 are this pattern, exported. It is, fortunately, the most transferable thing about me: tight loops are cheap to specify and every model tier benefits from them.

---

## Part V — The Missing Eval (R6)

Maxim 10: "Without baselines, improvement is a rumor." The seed prompt has no baselines. Nothing in this repo measures whether any model, on any task, performs better with the prompt than without it — which means the central claim this review was asked to evaluate is currently unfalsifiable.

Minimum viable harness (build with the Claude Agent SDK; ~a day of work):

- **Task suite:** 24 tasks — 8 FAST, 10 STANDARD, 6 DEEP — spanning code-with-tests (verifiable), research-with-checkable-facts (semi-verifiable), and ops/config (dry-runnable). Each with a mechanical pass/fail check.
- **Run matrix:** {Haiku, Sonnet, Opus} × {no seed, kernel-only (Tier 0), full seed} × {bare, harness-enforced (B1+B4 hooks)}. 3–5 seeds per cell.
- **Metrics:** task success (mechanical check), false-completion rate (claimed done but check fails — the F3 metric), total tokens, orchestration-token share (tests the 45% rule on your own workload), wall time.
- **Decisions the data makes:** Does the full seed beat the kernel on any model? (Prediction: no on Opus; marginal on Haiku; kernel+hooks beats full-seed-bare everywhere.) Does harness enforcement dominate prompt content? (Prediction: yes, decisively on false-completion rate.) Where does Opus+scaffold land relative to Fable-bare? (The actual number behind "considerably narrow.")

Predictions are stated so the eval can embarrass me. That's the point of provenance.

---

## Recommendation Summary

| ID | Recommendation | Effort | Expected effect |
|---|---|---|---|
| R1 | Tier the prompt: kernel / phase modules / reference doc | Medium | Largest prompt-side win; fixes F5, II.2 |
| R2 | Purge pseudo-quantities; add "no unearned numbers" rule | Small | Fixes II.1; restores audit-trail integrity |
| R3 | Split escalation bias: safety up, complexity starts low + promotes on evidence | Small | Cuts ceremony tax on real workloads |
| R4 | Add six missing behaviors (evidence-first debugging, anti-repetition, context hygiene, honest completion, minimal change, plan abandonment) | Small | Targets F2-damage, F4, F6 directly |
| R5 | Verification loop becomes the spine (kernel rule 2/4), not §5-of-17 | Small | Aligns structure with actual leverage |
| A1 | JORDAN EXECUTE → evidence-interleaved per subtask | Medium | Catches failures at first contamination point |
| A2 | Premortem scenarios compiled to runtime watchdogs | Medium | Doubles premortem ROI; gives predictions falsification conditions |
| B1–B6 | Harness enforcement suite (stop-hook verify, model routing, isolation, deterministic gates, schemas, memory) | Medium–Large | **The dominant gap-narrowing mechanism** |
| R6 | Eval harness; run the matrix | Medium | Converts the central claim from rumor to measurement |

Priority order if resources are constrained: **B1 → R1 → R6 → B2 → R2/R3/R4 → A1/A2.** The stop-hook plus the kernel plus the eval gives you, within days, both the biggest single improvement and the instrument to prove (or disprove) everything else.

---

*The gap between models is real and no prompt abolishes it. But most of what looks like an intelligence gap in deployed agents is actually an enforcement gap — the strong model checks itself, the weak model doesn't, and the harness can check anybody. Build the harness that makes honesty mandatory, spend the frontier tokens only where judgment is dense, measure everything, and the gap that remains will be the true one — much smaller than the one you see today.*
