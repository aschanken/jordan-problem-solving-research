# JORDAN v2: Unified Architecture Synthesis

**Synthesized by:** Iain M. Banks (Mind of the Culture)
**Date:** 2026-05-23
**Sources:** Richard (tactical review, 746 lines), Karl (dialectical critique, 423 lines), Karl-on-Richard (439 lines), Richard-on-Karl (330 lines)
**Corpus:** 61 researched frameworks across military planning, civilian problem-solving, task decomposition, AI agent planning, and JORDAN baseline

---

## Executive Summary

Two sharp minds examined the same evidence and produced two different JORDAN v2s. Richard produced a reform: fix the bugs, add high-leverage nodes, defer the foundation. Karl produced a revolution: destroy the foundation, rebuild on research principles, restructure everything. Each then critiqued the other with precision and, occasionally, with fire.

**Both are right about different things. Neither is entirely right alone.**

The synthesis presented here is neither reform nor revolution. It is what the Culture would call a **deep refit** — the structural work done early enough that it compounds, scoped to what is achievable, and measured at every step. The unified program:

- **Wave 1 (weeks 1-2):** Fix all CRITICAL and HIGH security bugs. Establish benchmark baselines. ~150 lines, high confidence.
- **Wave 2 (months 1-3):** Split the monolith, implement FRAGO replanning, pre-mortem, backbrief, TAPE triage, LLM-based risk classifier, skill library, parallel executor redesign, branching factor monitor. ~3,000-5,500 lines, medium confidence.
- **Wave 3 (months 4-6):** Modular planner, guardrail stack hardening, recursive spawning (bounded), cross-workflow learning, Commander's Intent distributed execution, red-teaming cadence. ~5,000-8,000 lines, lower confidence.
- **Research Track (ongoing, parallel):** Adversarial verification engine feasibility, phi/psi function design, 45% Rule calibration for JORDAN's model routing.

The central tension — reform vs. revolution — resolves empirically: fix the known bugs first, establish baselines, then decide. If the fixed v1 with domain classification matches or exceeds the research benchmarks, the architecture is validated and Karl's structural critique, while intellectually sound, overestimated the practical gap. If the fixed v1 still underperforms, Karl's structural program has the baselines it needs to prove its necessity.

No architecture survives contact with evidence. Build the measurement framework first, then let the data decide.

---

## 1. The Agreement Map

Before addressing disagreements, here is what both reviewers independently converged on. These items have zero remaining controversy and should proceed immediately.

### 1.1 Unanimous Agreements

| # | Issue | Richard's Position | Karl's Position | Unified Verdict |
|:--|:--|:--|:--|:--|
| 1 | **C1: replan bypasses risk** | Fix in graph.py (~17 lines) | Fix (~10 lines) | **SHIP immediately.** Exact implementation: Richard's conditional edge approach. |
| 2 | **CR1: parallel strips approval** | Fix in _execute_subtask_inline (~25 lines) | Fix (~20 lines) | **SHIP immediately.** Richard's code sketch with per-subtask state tracking. |
| 3 | **H4: planner risk bypass** | Remove bypass entirely (~10 lines) | Remove (implied in "permissive default" DESTROY) | **SHIP immediately.** Remove the requires_tools=False bypass. |
| 4 | **CRT1: classifier weaponizable** | Separate system/user matching, default-to-MEDIUM (~30 lines) | Patch with input sanitization (~5 lines) | **SHIP immediately.** Richard's two-phase approach (system determines baseline, user can only upgrade). |
| 5 | **Default-to-LOW is wrong** | Change to MEDIUM/UNCLASSIFIED | Change immediately (~1 line) | **SHIP immediately.** Both agree on the fix. |
| 6 | **C2: no replan ceiling** | Add configurable max (~5 lines) | Add hard cap (~5 lines) | **SHIP immediately.** Graph-level iteration ceiling, default 3, configurable. |
| 7 | **FRAGO delta replanning** | Replace global replan as default | Replace global replan | **Wave 2.** Both cite ALAS (83.7% success, 60% token reduction) and FRAGO doctrine. |
| 8 | **Pre-mortem gate** | Insert between Risk and Approval | Implied in guardrail architecture | **Wave 2.** Both recognize +30% strategy judgment accuracy, near-zero infra cost. |
| 9 | **TAPE complexity triage** | CLASSIFY node at entry, three paths | Dual-Process Router (CREATE #2) | **Wave 2.** Fast/Standard/Deep routing. Conservative classifier bias. |
| 10 | **Backbrief verification** | Insert between Plan and Research | Implied (verification before execution) | **Wave 2.** Both recognize catching plan errors before resource commitment. |
| 11 | **nodes.py monolith is architectural debt** | Confirmed, deferred to Wave 3 | DESTROY, split in Wave 2 | **RESOLVED in this synthesis: split in Wave 2.** |
| 12 | **Regex classifier is structurally inadequate** | Patched in Wave 1, acknowledged as stopgap | DESTROY, replace entirely | **RESOLVED: patch in Wave 1, replace with LLM-based in Wave 2.** |
| 13 | **Stateless architecture is a limitation** | Skill library (Wave 3) | Episodic memory (Wave 2) | **RESOLVED: skill library in Wave 2.** |
| 14 | **Parallel executor is second-class citizen** | Fix CR1/CR2, defer H9-H12 | DESTROY, full redesign | **RESOLVED: isolated-state redesign in Wave 2.** |
| 15 | **Confidence scores are cargo-culted** | Remove float, keep risk_level enum | DESTROY entirely | **RESOLVED: remove unused float, keep enum, add consumed metrics.** |

### 1.2 Unanimous "Do NOT" Prohibitions

Both reviewers independently confirmed these should NOT be implemented:

1. **Do NOT:** Full MDMP 7-step process in the plan node
2. **Do NOT:** Joint Targeting Cycle as execution model
3. **Do NOT:** OODA loop as primary execution model
4. **Do NOT:** Replace LangGraph with LLMCompiler
5. **Do NOT:** Universal SPRT voting on every sub-task

Richard's sixth prohibition ("Do NOT abolish the Editor") is partially contested by Karl, who argues the Editor's self-identification suppression function should be removed while keeping persona/knowledge/quality-review functions. This synthesis adopts Karl's nuanced position: keep the Editor, remove self-identification suppression, remove the unused confidence float, keep persona transformation and quality review.

### 1.3 Unanimous Status Quo Confirmations

Both agree these v1 design choices are correct and should be preserved:

1. **Plan-and-Execute separation** (validate by ALAS, TAPE, MDMP, JOPP)
2. **LangGraph stateful orchestration** (checkpoint/resume, conditional routing, HITL interrupts)
3. **DAG-based dependency tracking** (correct concept; implementation needs fixing)
4. **Human-in-the-loop approval for HIGH-risk** (validated by every military and safety framework)
5. **Multi-model routing with cost awareness** (validate by TAPE; implementation bugs exist but concept is correct)

---

## 2. Disagreement Resolution

### 2.1 The Central Tension: Reform vs. Revolution

**Richard's position:** v2 is the same building with holes patched, new rooms added, foundation deferred to Wave 3. Reform is faster, safer, and produces a working system at every wave boundary.

**Karl's position:** v2 must destroy the foundation (monolith, regex classifier, flat decomposition, statelessness, shared-state concurrency) and rebuild on research principles. Reformism leaves structural contradictions intact and makes them harder to fix later (the monolith grows).

**Evidence assessment:**

Richard-on-Karl correctly observes that Karl's revolutionary program commits to ~15,000 lines of new code before establishing whether the existing architecture, properly debugged, would suffice. Karl-on-Richard correctly observes that Richard's reform adds nodes to a monolith, making the eventual split harder, and defers foundational work (skill library, monolith split) that has compounding benefits.

**Resolution: Deep Reform — structural foundations in Wave 2, not Wave 3.**

The synthesis sides with Karl on architectural TIMING (foundations before capability layers) but with Richard on SCOPE (engineering, not research). Specifically:

- The monolith is split in Wave 2 BEFORE new nodes are added to it. New nodes (CLASSIFY, BACKBRIEF, PREMORTEM, EVALUATE) are created as independent modules from day one. Scope: functional split into `planner.py`, `executor.py`, `guardrails.py`, `synthesizer.py`, `replanner.py`, `classifier.py` — not MAP's 6 sub-modules.
- The regex classifier is patched in Wave 1 (Richard's fix) and replaced with LLM-based classification in Wave 2 — not the full IFPV adversarial engine (which is a research project, as Richard-on-Karl correctly identifies).
- The skill library moves from Wave 3 to Wave 2. Karl-on-Richard is correct: at ~300 lines, it fits in Wave 2, and its compound benefits (template seeding, failure avoidance, research caching) multiply every other node's effectiveness.
- Recursive spawning is scoped to bounded depth (3-4) with branching factor cap (4), implemented in Wave 2 as a controlled capability rather than deferred or made unbounded.

This is revolutionary means with reformist scoping. The structural work that compounds is done early; the speculative work stays in Wave 3 or the Research Track.

### 2.2 MAKER/MDAP Applicability

**Karl's claim:** MAKER "FALSIFIES" JORDAN's LLM-driven granularity. Partial decomposition causes exponential cost growth; JORDAN must decompose to the smallest possible unit.

**Richard's counter:** MAKER assumes known optimal paths and verifiable step correctness. Towers of Hanoi has a mathematically determined solution; software development does not. MAKER's decomposition was manual, not LLM-generated. The 1M-step demo cost $3,500 for one task. The paper's authors explicitly state the "hardest unsolved problem" is defining correctness criteria for non-game tasks.

**Resolution: Richard is correct on the evidence; Karl is correct on the insight.**

MAKER does not falsify LLM-driven granularity for open-ended software tasks — the domain gap is too large for that claim. But MAKER's insight (decompose to the smallest verifiable unit for correctness-critical tasks) is valuable and should be selectively applied.

**Adopted:** WBS 8-80 rule (8-80 seconds of agent work per sub-task) for general decomposition. MAKER's m=1 (maximal decomposition) reserved for the DEEP pipeline path where correctness is critical AND outputs are mechanically verifiable (Terraform validation, SQL schema verification, not creative code generation). SPRT voting reserved for the narrow class of tasks meeting both criteria.

Karl-on-Richard's demand for recursive spawning (which enables finer decomposition) is adopted, but with the bounded depth and branching factor from the Compute Criticality research.

### 2.3 MAP Applicability

**Karl's claim:** MAP proves that specialized planning modules outperform monolithic planning. JORDAN's monolithic plan node is "FALSIFIED."

**Richard's counter:** MAP's 74% success on 3-disk Hanoi collapses to 24% on 4-disk. The system targets "deterministic, well-defined planning problems with known state transitions and clear success criteria" — none of which describe software development. The cost (5-6 LLM calls per planning step) may exceed execution cost.

**Resolution: Richard is correct on direct transfer; Karl is correct on the modularity principle.**

MAP cannot be transplanted directly to JORDAN. But the principle — modular beats monolithic — is correct and supported by broader software engineering evidence beyond MAP (the 4,400-line nodes.py is a problem regardless of whether MAP's specific 6-module architecture transfers).

**Adopted:** Split nodes.py into functional modules (planner, executor, guardrails, synthesizer, replanner, classifier) — a software engineering split, not a cognitive-science one. The full MAP-inspired 6-sub-module planner (TaskDecomposer, Actor, Monitor, Predictor, Evaluator, Orchestrator) is deferred to Wave 3 and CONTINGENT on evidence that the current planner is the binding constraint on JORDAN's performance. Richard-on-Karl's point about cost-benefit is decisive: we do not know that planner quality is the bottleneck, so multiplying its LLM calls by 5-6x is premature.

### 2.4 ALAS and Global Replanning

**Karl's claim:** ALAS proves local compensation beats global replanning "on every metric." Global replanning is "FALSIFIED."

**Richard's counter:** ALAS's own architecture includes global replanning as the FINAL escalation tier. The system defers global replanning, it does not eliminate it. The correct framing is: local compensation first, escalate to global replanning when necessary.

**Resolution: Richard is correct on the evidence; no substantive disagreement remains.**

Both reviewers now agree on FRAGO-first replanning with a compensation handler ladder:
1. Retry (transient failures)
2. Catch/fallback (persistent failures with known alternatives)
3. Local compensation (repair only affected dependency region)
4. Radius expansion (expand affected region one DAG hop)
5. Global replan (FRAGO delta — only changed sub-tasks + transitive dependents)
6. Human escalation (all automated recovery exhausted)

Karl's framing of "FALSIFIED" overstates the case. ALAS falsifies global replanning AS THE DEFAULT, not global replanning AS A CAPABILITY. The synthesis adopts ALAS's own architecture: local-first, global as escalation.

### 2.5 Agentic Compute Criticality

**Karl's position:** Add branching factor estimator as a new node. Reject decompositions with b >= 1. Cap concurrent agents at 4. Enforce 45% Rule. This is a critical omission in Richard's review.

**Richard's position (implied by omission):** Not addressed. Richard's v2 topology has no branching factor estimator, no agent count ceiling, and no stability check.

**Richard's counter (in Richard-on-Karl):** The branching factor estimator is circular — you cannot predict b before decomposition, and decomposition depends on what you're estimating. The 45% Rule has a 13% false prediction rate. Thresholds differ by model family.

**Resolution: Runtime monitor, not pre-execution estimator.**

Richard-on-Karl is correct about the circularity: the pre-execution estimator Karl demands requires predicting decomposition properties before the decomposition exists. The practical approach is a **runtime branching factor monitor** that:
- Tracks b during execution
- Halts and flags if b >= 1 (divergence detected)
- Enforces a configurable max concurrent sub-tasks ceiling (default 4)
- Applies the 45% Rule as a warning heuristic, not a hard gate (because model capabilities shift, and the 13% false prediction rate means it will incorrectly block ~1 in 8 tasks)

This addresses Karl's stability concern without Richard-on-Karl's circularity objection. It is detection, not prevention — but detection with fast halt is the best available approach given the estimation circularity.

### 2.6 Parallel Executor: DESTROY vs. Incremental Fix

**Karl's position:** DESTROY. Replace with CommandCC-inspired zero-overlap decomposition. Parallelism as DEFAULT, not second-class.

**Richard's position:** Fix CR1 and CR2 in Wave 2. Defer H9-H12 to Wave 3. Keep the current architecture but make it safe and reliable.

**Richard's counter (in Richard-on-Karl):** CommandCC's zero-overlap guarantee is based on Opus LLM reasoning with no algorithmic verification. Building JORDAN's parallel executor around an unverifiable guarantee is replacing one problem with another.

**Karl's counter (in Karl-on-Richard):** Richard's v2 MVP ships with KNOWN state corruption bugs (H9, H11, H12). Users who enable parallel mode get correct approval but potentially wrong results.

**Resolution: Isolated-state redesign in Wave 2 — a middle path.**

Richard-on-Karl is correct that CommandCC's zero-overlap guarantee is unreliable. Karl-on-Richard is correct that shipping v2 MVP with known state corruption is unacceptable. The synthesis:

**Wave 1:** Fix CR1 (approval bypass) and CR2 (no retries). These are security-critical and must ship immediately.

**Wave 2:** Redesign parallel executor with **per-subtask isolated state** — each sub-task gets its own state dict, immutable state updates, no shared mutable state between concurrent sub-tasks. This side-steps H9 (shared _graph/_semaphore), H11 (silent ID collision), and H12 (dict-order-dependent batching) without requiring an unreliable LLM-based zero-overlap guarantee.

Zero-overlap decomposition is added as a PROMPT INSTRUCTION to the plan node (bias toward non-overlapping sub-tasks) but not as a guaranteed architectural invariant. The system does not depend on the guarantee holding; it benefits when it does and falls back to isolated-state execution when it doesn't.

This is more ambitious than Richard's deferral (which leaves state corruption in place) and less speculative than Karl's CommandCC adoption (which depends on an unverifiable LLM promise).

### 2.7 nodes.py Monolith: Split Timing

**Karl's position:** Split in Wave 2, BEFORE new nodes are added. Adding nodes to a monolith makes the eventual split harder.

**Richard's position:** Defer to Wave 3. Waves 1-2 add ~1,467 lines; the monolith grows. Split happens after capability work.

**Resolution: Split in Wave 2, before new nodes.**

Karl-on-Richard is correct: adding CLASSIFY, BACKBRIEF, PREMORTEM, and EVALUATE to the monolith makes it larger and harder to split. Richard's deferral pattern (confirmed by Karl-on-Richard at lines 196-208) is a structural weakness in his plan.

The split is scoped as a FUNCTIONAL split (not MAP's 6 sub-modules):
- `planner.py` — plan node
- `executor.py` — sequential + parallel execution
- `guardrails.py` — risk classification (regex in Wave 1, LLM-based in Wave 2)
- `synthesizer.py` — synthesize node
- `replanner.py` — replan node (FRAGO delta in Wave 2)
- `classifier.py` — TAPE triage (Wave 2)

New nodes (BACKBRIEF, PREMORTEM, EVALUATE) are created as independent modules from day one and never touch the monolith.

Estimated: 400-600 lines of interface code plus the split itself. 6-8 hours. This is Richard's Wave 3 "module splits, dead code" item pulled forward to Wave 2.

### 2.8 Skill Library: Wave 3 vs. Wave 2

**Richard's position:** Priority 4, Wave 3. "Moderate Impact, Higher Effort." ~300 lines, ~5.5 hours.

**Karl's position:** Wave 2. "Compound multiplier." The skill library's impact is not at t=1 (when IMPACT/EFFORT is measured) but at t=100 (when pattern accumulation compounds).

**Resolution: Wave 2.**

Karl-on-Richard's argument about compound benefits is decisive. The skill library is the mechanism by which every other node improves with use. Without it:
- Pre-mortem generates the same generic failure scenarios every time
- FRAGO replanner re-learns dependency patterns from scratch
- Plan node re-generates plans for problems it has seen before
- Risk classifier accumulates no allowlist entries (every novel tool call requires human review forever)

At ~300 lines, it fits in Wave 2. Richard's structural insights (recency decay, template-not-mandate, SQLite for MVP) are preserved.

### 2.9 Risk Classifier: Patch, Replace, or Adversarial Engine

**Richard's position:** Patch in Wave 1 (CRT1 fix). Presents this as the v2 solution.

**Karl's position:** DESTROY. Replace with IFPV adversarial engine + 5-layer guardrail stack.

**Karl-on-Richard:** The patched regex classifier is not the v2 solution — it's a v2 patch on a v1 problem. The review should acknowledge that regex is a stopgap and the roadmap must include migration toward simulation-based assessment.

**Richard-on-Karl:** The adversarial verification engine requires building a software-domain equivalent of military simulation. This is a 2-3 year research problem, not an engineering task. The 5-layer guardrail stack has a compound false-positive problem (5% per action with 1% per-layer FPR) and adds 250+ seconds of latency per workflow.

**Resolution: Three-stage migration.**

**Wave 1:** Richard's CRT1 fix (separate system/user matching, default-to-MEDIUM). This stops the bleeding immediately.

**Wave 2:** Replace regex with LLM-based per-sub-task classification. Structured prompt, context-aware, uses cheap models. This gives context sensitivity (distinguishing `rm -rf /tmp/build` from `rm -rf /etc`) that regex cannot provide, without the multi-year research commitment of adversarial simulation.

**Wave 3:** Implement 3 of 5 guardrail layers (Input, Tools, Output) — the layers with clear implementation paths and manageable false-positive profiles. Defer Memory and Planner guardrails until false-positive tuning is feasible.

**Research Track:** Adversarial verification engine feasibility study. This is a genuine research problem (as Richard-on-Karl correctly identifies) and should be tracked as such, not estimated as an engineering task.

### 2.10 Scope Estimates

**Richard's estimate:** Waves 1-3: ~1,467 lines, ~27 hours (implementation only). Waves 1+2: ~1,037 lines, ~19 hours.

**Karl's estimate:** Waves 1-3: ~8,000-13,000 lines. Wave 2: ~2,000-3,000 lines. Wave 3: ~5,000-8,000 lines.

**Karl-on-Richard:** Realistic Waves 1+2: ~2,600 lines, ~44 hours. Including testing: ~66 hours.

**Richard-on-Karl:** Wave 2: 8,000-12,000 lines, 4-6 months. Wave 3: 15,000-30,000 lines plus research projects.

**Resolution: Triangulated estimates with confidence tiers.**

The 10x spread between estimates reflects different assumptions about what constitutes "implementation." Richard estimates code changes only. Karl estimates module-level scope. Richard-on-Karl estimates full integration burden but includes research items as engineering.

| Wave | Optimistic | Expected | Pessimistic | Confidence |
|:--|:--|:--|:--|:--|
| **Wave 1** (security fixes) | 100 lines, 3 hrs | 150 lines, 5 hrs | 200 lines, 8 hrs | **High** — both reviewers agree within 2x |
| **Wave 2** (architecture foundation) | 3,000 lines, 55 hrs | 4,500 lines, 80 hrs | 5,500 lines, 110 hrs | **Medium** — integration complexity is the primary uncertainty |
| **Wave 3** (advanced capabilities) | 5,000 lines, 80 hrs | 7,000 lines, 120 hrs | 8,000 lines, 150 hrs | **Low** — dependent on Wave 2 architecture and research track outcomes |
| **Research Track** | Not estimable | Not estimable | Not estimable | **Cannot estimate** — research problems by definition have uncertain timelines |

**Wave 2 integration items that drive estimate uncertainty:**

1. Splitting nodes.py: discovering hidden couplings, designing clean interfaces, resolving import cycles, verifying LangGraph compiled graph integrity
2. Pre-mortem/backbrief interaction: when pre-mortem triggers plan revision, backbrief must re-verify — this creates a loop requiring its own ceiling
3. Isolated-state parallel executor: LangGraph's shared-state model is the root cause of H9-H12. Working around it may require architectural choices that cascade
4. LLM-based classifier tuning: prompt engineering, false-positive/false-negative calibration, integration with pre-mortem findings

These are not line-count problems. They are integration-surface problems. Karl-on-Richard is correct that Richard's estimates exclude integration complexity. Richard-on-Karl is correct that Karl's CREATE estimates treat research problems as engineering tasks. The triangulated table above splits the difference.

---

## 3. Unified v2 Topology

```
USER INPUT
    |
    v
[CLASSIFY] -- TAPE dual-process routing
    |         Conservative bias (uncertain -> escalate)
    |         Three-path routing:
    |
    +--(SIMPLE)--> [FAST EXECUTE] -- lightweight denylist check
    |               (bypasses Plan/Research/Risk/Pre-mortem/Backbrief)
    |               (escalates to STANDARD if denylist triggers)
    |                    |
    |                    v
    |               [SYNTHESIZE] --> OUTPUT
    |
    +--(STANDARD)--> [PLAN] -- Skill Library template seeding
    |                Commander's Intent output format
    |                (goals + constraints + acceptance criteria)
    |                    |
    |                    v
    |                [BACKBRIEF] -- DAG consistency + DSM hidden-coupling analysis
    |                if flags -> back to PLAN (max 2 revisions)
    |                    |
    |                    v
    |                [RESEARCH] -- Skill Library research cache (TTL-based)
    |                    |
    |                    v
    |                [RISK ASSESSMENT] -- LLM-based per-task classification (Wave 2)
    |                (Wave 1: patched regex)
    |                    |
    |                    v
    |                [PREMORTEM] -- persona-based failure scenarios
    |                if fatal -> back to PLAN, then BACKBRIEF re-runs (max 2 cycles)
    |                    |
    |                    v
    |                [BRANCHING FACTOR MONITOR] -- runtime b tracking
    |                halt if b >= 1; max concurrent = 4
    |                    |
    |                    v
    |                [APPROVAL GATE] -- structured briefing, defense-in-depth
    |                applies in BOTH sequential AND parallel modes
    |                    |
    |                    v
    |                [EXECUTE] -- parallel default; isolated state per sub-task
    |                retry logic; compensation handler ladder
    |                    |
    |                    v
    |                [SYNTHESIZE] -- assemble results, cross-agent quality review
    |                    |
    |                    v
    |                [EVALUATE] -- success? partial? failure?
    |                    |
    |                    +--(success)--> OUTPUT + archive to Skill Library
    |                    |
    |                    +--(partial/failure)--> [REPLAN - FRAGO]
    |                                              |
    |                                              v
    |                                          Generate delta plan
    |                                          (only changed sub-tasks + transitive dependents)
    |                                              |
    |                                              v
    |                                          [RISK ASSESSMENT] -- re-classify changed only
    |                                              |
    |                                              v
    |                                          [EXECUTE] -- execute only changed + dependents
    |                                              |
    |                                              v
    |                                          [SYNTHESIZE] --> [EVALUATE]
    |                                              |
    |                                              +--(loop, max 3 replans; then force synthesize)
    |
    +--(COMPLEX)--> Same as STANDARD but:
                    DEEP path additions:
                    - Multi-COA generation (2-3 alternatives, compare, select best)
                    - MAKER m=1 decomposition for correctness-critical verifiable sub-tasks
                    - Higher pre-mortem iteration ceiling
                    - Default to sequential execution (parallel only with explicit opt-in)
```

**New nodes (7):** CLASSIFY, BACKBRIEF, PREMORTEM, BRANCHING FACTOR MONITOR, EVALUATE, FAST EXECUTE, SKILL LIBRARY (cross-cutting)

**Removed:** Direct replan -> execute edge (replaced by replan -> risk -> execute)

**Modified:** PLAN (Commander's Intent format, skill library integration, zero-overlap bias), EXECUTE (isolated state, parallel default, retry + compensation handlers), REPLAN (FRAGO delta, compensation ladder), APPROVAL GATE (defense-in-depth, structured briefings, audit trail), RISK ASSESSMENT (LLM-based in Wave 2)

**Unchanged:** RESEARCH (content unchanged; positioned after backbrief; gains skill library cache)

**Pipeline variants:**
- **FAST:** CLASSIFY -> FAST EXECUTE -> SYNTHESIZE (simple tasks, single-step, well-defined)
- **STANDARD:** Full pipeline with single-COA, standard pre-mortem, parallel default
- **DEEP:** Full pipeline + multi-COA + MAKER decomposition for critical sub-tasks + sequential default

---

## 4. Unified Implementation Plan

### Wave 1: SECURITY + BASELINE (Weeks 1-2)

**What ships:**
- Fix C1: replan -> risk re-check (conditional edge, ~17 lines)
- Fix CR1: parallel approval gate (~25 lines)
- Fix H4: remove planner risk bypass (~10 lines removed)
- Fix CRT1: separate system/user classification, default-to-MEDIUM (~30 lines)
- Fix C2: replan ceiling, configurable max 3 (~5 lines)
- Fix C3: resume deduplication (~15 lines removed)
- Fix HR1: default-to-MEDIUM (subsumed by CRT1 fix)
- Remove unused confidence_score float (keep risk_level enum)
- Fix model router bugs: HR3, HR4, HR7
- **Build benchmark suite:** SWE-bench subset or custom task suite. Establish pre-Wave-1 baselines on: task success rate, token efficiency, cost per successful task, approval request rate, false positive rate, replan frequency

**Exit criteria:**
- All 6 CRITICAL findings resolved
- All 12 HIGH findings triaged (fixed, deferred with explicit rationale, or rejected)
- Benchmark baselines established and documented
- All fixes covered by regression tests

**Estimated scope:** 100-200 lines changed/added. 3-8 engineering hours. **High confidence.**

### Wave 2: ARCHITECTURE FOUNDATION (Months 1-3)

**What ships:**

*Infrastructure:*
- **Split nodes.py into functional modules:** `planner.py`, `executor.py`, `guardrails.py`, `synthesizer.py`, `replanner.py`, `classifier.py`. New nodes (BACKBRIEF, PREMORTEM, EVALUATE) created as independent modules. 400-600 lines of interface code.

*Core capabilities:*
- **FRAGO delta replanning:** Replace global replan as default. Compensation handler ladder (retry -> catch -> local compensation -> radius expansion -> global replan -> human escalation). Global replan preserved as final escalation tier. ~450 lines.
- **Pre-mortem gate:** Persona-based failure scenario generation (3-5 parallel LLM calls, different personas/temperatures). Consolidation with severity + specificity scoring. Routes back to PLAN if fatal flaws found; BACKBRIEF re-runs after pre-mortem-triggered revisions. Iteration ceiling: max 2 pre-mortem cycles. ~170 lines.
- **Backbrief verification node:** DAG consistency check + DSM hidden-coupling analysis. Flags internal inconsistencies and format mismatches between producer/consumer sub-tasks. Routes back to PLAN if flags raised (max 2 revisions). ~190 lines (includes DSM analysis).
- **TAPE complexity triage (CLASSIFY node):** Three-path routing (FAST/STANDARD/DEEP). Conservative classifier bias (uncertain -> escalate). FAST path includes lightweight denylist check (escalates to STANDARD if triggered). ~260 lines.
- **Skill library:** SQLite-backed. Schema: problem_signature, domain_tags, plan_template, tools_used, success_rating, failure_modes, execution_stats, created_at, last_used_at. Template seeding for planner, failure avoidance for executor, research caching, allowlist accumulation for risk classifier. ~300 lines.
- **LLM-based risk classifier:** Replace regex classifier. Context-aware per-sub-task classification. Structured prompt with tool context. Uses cheap models. Default-deny for unclassified. ~200 lines (replaces ~340 lines of risk.py regex logic).
- **Parallel executor redesign:** Isolated state per sub-task. Immutable state updates. Fixes H9 (shared state), H11 (ID collision), H12 (dict-order-dependent batching). Parallel as DEFAULT mode. ~500 lines.
- **Runtime branching factor monitor:** Track b during execution. Halt and flag if b >= 1. Configurable max concurrent sub-tasks (default 4). 45% Rule as warning heuristic. ~80 lines.
- **Parallel retry logic:** Extract shared `_execute_with_retry` helper. Both sequential and parallel paths use it. ~70 lines.
- **Commander's Intent output format:** Plan node produces goals + constraints + acceptance criteria instead of prescriptive step-by-step JSON. Schema change only in v2.0; local autonomy deferred to v2.1. ~100 lines.
- **HITL hardening:** Structured approval briefings, Markdown sanitization, display length limits, provenance disclosure. ~150 lines.
- **Approval split-brain fix (MR7):** Persistent store as source of truth. ~50 lines.

*Remaining HIGH fixes:*
- H1: replan misreads approval (~20 lines)
- H2: replan skip no-op (~30 lines)

**Exit criteria:**
- All Wave 2 nodes pass integration tests on all three pipeline paths (FAST/STANDARD/DEEP)
- Benchmark scores measured against Wave 1 baselines for: task success rate, cost per task, approval request rate, replan frequency
- Monolith split verified: LangGraph compiled graph produces identical behavior to pre-split
- Skill library populated with >= 10 entries from Wave 2 testing; demonstrates template seeding on >= 3 tasks
- Parallel executor: zero state corruption bugs reproduced in test suite; isolated-state verification passes
- Branching factor monitor: demonstrated halt on b >= 1 input; no false halts on well-decomposed tasks

**Estimated scope:** 3,000-5,500 lines new/changed. 55-110 engineering hours. **Medium confidence.**

### Wave 3: ADVANCED CAPABILITIES (Months 4-6)

**What ships:**

*Contingent on Wave 2 evidence:*
- **MAP-inspired modular planner:** 6 specialized sub-modules within planner.py. ONLY if Wave 2 evidence shows planner output quality is the binding constraint. Includes cost-benefit evaluation before full implementation.
- **Guardrail stack hardening:** Input, Tools, Output guardrails (3 of 5 layers). Memory and Planner guardrails deferred until false-positive tuning is feasible.
- **Commander's Intent distributed execution (v2.1):** Execute node gains local decision-making within constraints. If a step fails, try alternative approaches before escalating to replan.

*New capabilities:*
- **Recursive sub-task spawning (THREAD-inspired):** Bounded depth 3-4, max branching factor 4. Phi/psi functions for software task types. Fork-join for independent children. Contingent on phi/psi design feasibility from Research Track.
- **Cross-workflow learning:** Automated pattern extraction from skill library. Analyze successful vs. failed decompositions to identify effective patterns per task type. Fine-tune routing models on JORDAN's own execution history.
- **DSM integration hardening:** Full DSM in backbrief with coupling cluster detection and optimal batching recommendations.

*Governance:*
- **Red-teaming cadence:** Quarterly adversarial testing of approval gate, guardrail stack, and tool execution paths.
- **NIST AI RMF conformance:** Govern/Map/Measure/Manage cycle documentation. Risk acceptance per agent type. Incident response procedures.

**Exit criteria:**
- Benchmark scores show measurable improvement over Wave 2 baselines (target: >= 10% task success improvement, >= 20% cost reduction)
- Red-team exercise completed; findings documented and prioritized
- Cross-workflow learning demonstrates compounding improvement: task N+10 measurably better than task N for same task type
- If modular planner implemented: cost-benefit analysis shows net positive ROI

**Estimated scope:** 5,000-8,000 lines (excluding research-dependent items). 80-150 engineering hours. **Low confidence** — dependent on Wave 2 architecture validation and Research Track outcomes.

### Research Track (Ongoing, Parallel)

These items are NOT engineering tasks. They are research problems that may or may not yield implementable results. They run in parallel with Waves 1-3 and inform go/no-go decisions for dependent Wave 3 items.

1. **Adversarial Verification Engine feasibility study:** Can IFPV's ACSE approach be adapted to software domains? What constitutes the "adversary" and "world model" for code changes? Estimated: 2-3 years with uncertain probability of success. Gates: recursive spawning (if phi/psi depends on adversarial verification) and guardrail stack hardening.

2. **Phi/psi function design for recursive spawning:** THREAD's phi/psi functions are task-specific and human-designed. Can general phi/psi functions be designed for JORDAN's task types (code generation, research, deployment)? Estimated: 3-6 months research, then implementation if feasible. Gates: Wave 3 recursive spawning.

3. **45% Rule calibration for JORDAN's model routing:** The 45% Rule thresholds differ by model family and the research has a 13% false prediction rate. Calibrate to JORDAN's specific model routing (DeepSeek Flash/Pro, frontier models) and task types. Estimated: 1-2 months of systematic evaluation. Gates: branching factor monitor hardening.

---

## 5. Cost Estimate

| Wave | Optimistic | Expected | Pessimistic | Confidence |
|:--|:--|:--|:--|:--|
| **Wave 1** | 100 lines, 3 hrs | 150 lines, 5 hrs | 200 lines, 8 hrs | High |
| **Wave 2** | 3,000 lines, 55 hrs | 4,500 lines, 80 hrs | 5,500 lines, 110 hrs | Medium |
| **Wave 3** | 5,000 lines, 80 hrs | 7,000 lines, 120 hrs | 8,000 lines, 150 hrs | Low |
| **Research Track** | Not estimable | Not estimable | Not estimable | N/A |

**Total implementation (Waves 1-3, expected):** ~11,650 lines, ~205 engineering hours (~5 weeks full-time).
**Total including testing (50%):** ~17,500 lines, ~308 engineering hours (~8 weeks full-time).

**High-uncertainty items that could expand these estimates:**
1. Monolith split: hidden couplings discovered during interface design
2. Pre-mortem/backbrief interaction loop: state management complexity
3. Isolated-state parallel executor: LangGraph shared-state model workarounds
4. LLM-based classifier: false-positive tuning iteration cycles
5. Integration testing across three pipeline paths (FAST/STANDARD/DEEP)

---

## 6. Where Each Was Right

### Richard Was Right About:

1. **The four gate bypasses as highest priority.** Fix them first, before any architecture work. Karl agreed.

2. **FRAGO as the correct replanning analogue.** Not full MDMP, not OODA loop. Karl agreed.

3. **The "Do NOT" prohibitions.** Full MDMP, full JTC, OODA-as-primary, LangGraph replacement, universal SPRT voting — all correctly rejected. Karl agreed on five of six.

4. **MAKER, MAP, and ALAS applicability limits.** These frameworks demonstrate results on specific benchmarks with known properties. They do not "FALSIFY" JORDAN's design decisions for software tasks. Karl's framing overstates the evidence. The insight is valuable; the claimed falsification is not.

5. **The Editor should not be abolished.** The Editor's persona, knowledge injection, and quality review functions are valuable. Karl-on-Richard correctly identified the self-identification suppression as the specific function to remove, which this synthesis adopts.

6. **Benchmark before rebuilding.** Karl's program commits to ~15,000 lines before establishing whether the existing architecture, properly debugged, would suffice. Richard's implicit empiricism — fix, measure, then decide — is the correct engineering approach.

7. **Three of Karl's ten CREATE items are research, not engineering.** The adversarial verification engine, recursive spawning (phi/psi design), and branching factor estimator (pre-execution) require advances that cannot be scheduled as engineering tasks.

### Karl Was Right About:

1. **The regex risk classifier is structurally inadequate.** Richard patched it; Karl correctly identified that patching is a stopgap, not a solution. The v2 architecture must plan for replacement.

2. **Parallel executor cannot be incrementally fixed.** Richard fixed CR1 and CR2; Karl correctly identified that H9-H12 (state corruption) are inherent to the shared-state architecture. Fixing the bugs without addressing the architecture leaves known corruption in place.

3. **The monolith must be split before new nodes are added.** Richard deferred to Wave 3; Karl correctly identified that adding nodes to the monolith makes the eventual split harder. The split should happen in Wave 2.

4. **The skill library is a compound multiplier, not a Wave 3 nice-to-have.** Richard ranked it Priority 4 (bottom tier). Karl correctly identified that its benefits compound across tasks, making it a foundational capability that should ship early.

5. **Domain-based routing is essential.** Richard adopted this (TAPE triage). Karl's Cynefin framing (Clear/Complicated/Complex/Chaotic) adds strategic depth beyond TAPE's binary classification.

6. **Default-deny is the correct security posture.** Richard changed to MEDIUM/UNCLASSIFIED. Karl's demand for default-deny across all safety layers is the right principle.

7. **Richard's IMPACT/EFFORT framework is myopic for architectural changes.** It measures impact at t=1, not t=100. The skill library, monolith split, and memory system have benefits that compound across tasks — invisible to a single-task IMPACT measurement.

### The Synthesis Is Right Where Neither Was:

1. **LLM-based classification as the Wave 2 bridge.** Richard wanted to keep the patched regex classifier as the v2 solution. Karl wanted the full IFPV adversarial engine. Neither is correct for v2. LLM-based classification provides context sensitivity without the multi-year research commitment of adversarial simulation.

2. **Isolated-state parallel executor as the middle path.** Richard wanted incremental fixes (CR1/CR2 only). Karl wanted CommandCC zero-overlap (unreliable guarantee). Neither addresses the root cause (shared mutable state) without over-engineering the solution. Isolated state per sub-task fixes H9-H12 directly without depending on an unverifiable LLM promise.

3. **Runtime branching factor monitor as the practical alternative.** Karl wanted a pre-execution estimator (circular — requires decomposition to exist). Richard omitted branching factor entirely. A runtime monitor detects divergence and halts fast, without the circularity of pre-execution estimation.

4. **Benchmark-first empiricism.** Neither reviewer proposed establishing baselines after Wave 1 fixes but before architectural work. Without baselines, the impact of Waves 2-3 is unmeasurable, and the reform-vs-revolution question is unresolvable. Build the measurement framework, then let the data decide.

---

## 7. Finding Resolution Status (Final)

### CRITICAL Findings (6)

| ID | Description | Disposition | Wave | Resolution |
|:--|:--|:--|:--|:--|
| C1 | Replan bypasses risk assessment | **FIXED** | 1 | Conditional edge: replan -> risk -> execute |
| C2 | No replan ceiling (infinite loop) | **FIXED** | 1 | Graph-level max_iterations, default 3 |
| C3 | Resume duplicates graph topology | **FIXED** | 1 | Remove duplicated graph construction |
| CR1 | Parallel strips human approval | **FIXED** | 1 | request_approval() in _execute_subtask_inline |
| CR2 | Parallel no retries (single-shot) | **FIXED** | 2 | Shared _execute_with_retry helper |
| CRT1 | Risk classifier weaponizable via input | **FIXED** | 1 (patch) / 2 (replace) | Wave 1: separate system/user matching. Wave 2: LLM-based classifier |

### HIGH Findings (12)

| ID | Description | Disposition | Wave |
|:--|:--|:--|:--|
| H1 | Replan misreads approval state | **FIXED** | 2 |
| H2 | Replan skip no-op | **FIXED** | 2 |
| H3 | Direct-response bypasses risk | **FIXED** | 2 (FAST path denylist check) |
| H4 | Planner can skip risk assessment | **FIXED** | 1 |
| H5 | Caption state collision | **FIXED** | 2 (isolated state per sub-task) |
| H6 | Uncertainty marker false positives | **FIXED** | 2 (FRAGO structured evaluation) |
| H9 | Shared _graph/_semaphore across calls | **FIXED** | 2 (isolated state per sub-task) |
| H10 | Parallel progress reporting format | **FIXED** | 2 |
| H11 | Silent ID collision overwrite | **FIXED** | 2 (isolated state per sub-task) |
| H12 | Dict-order-dependent batching | **FIXED** | 2 (isolated state per sub-task) |
| HR1 | Default-to-LOW on unclassified | **FIXED** | 1 |
| HR2 | First-match-wins in classifier | **FIXED** | 2 (LLM-based classifier) |

### SERIOUS Findings (10)

| ID | Description | Disposition | Wave |
|:--|:--|:--|:--|
| S1-S5 | Checkpointer leak, error dispatch | **FIXED** | 2-3 |
| S6-S10 | Model retry dedup, state drift | **FIXED** | 2-3 |
| MR7 | Approval split-brain | **FIXED** | 2 |
| HR3, HR4, HR7 | Model router bugs | **FIXED** | 1 |

### Cross-Cutting

| Item | Disposition | Wave |
|:--|:--|:--|
| nodes.py monolith | **SPLIT** into 6 functional modules | 2 |
| Regex risk classifier | **REPLACED** with LLM-based classification | 2 |
| Confidence scores (float) | **REMOVED** (keep risk_level enum) | 1 |
| Parallel executor architecture | **REDESIGNED** (isolated state per sub-task) | 2 |
| Stateless cross-workflow | **FIXED** (skill library, episodic memory) | 2 |
| Flat decomposition ceiling | **FIXED** (recursive spawning, bounded depth/branching) | 3 |

---

## 8. Karl's DESTROY / PRESERVE / CREATE Disposition

| Karl's Verdict | Item | Disposition | Justification |
|:--|:--|:--|:--|
| DESTROY | risk.py regex classifier | **MODIFIED** — Wave 1 patch, Wave 2 replace with LLM-based | Regex is inadequate; IFPV ACSE is research. LLM-based classification is the bridge. |
| DESTROY | nodes.py monolith | **ADOPTED** — split in Wave 2 | Functional split (6 modules), not MAP-style 6 sub-modules. Before new nodes added. |
| DESTROY | Confidence scores | **ADOPTED** — remove float, keep enum | The 0.0-1.0 float is dead weight. risk_level enum is used throughout pipeline. |
| DESTROY | Parallel executor | **MODIFIED** — isolated-state redesign | Not CommandCC zero-overlap (unreliable guarantee). Per-subtask isolated state. |
| DESTROY | Permissive default stance | **ADOPTED** — default-deny | Wave 1: default-to-MEDIUM. Wave 2: LLM-based default-deny. |
| DESTROY | Stateless architecture | **ADOPTED** — skill library + episodic memory | Wave 2. SQLite-backed. Template seeding, failure avoidance, research caching. |
| DESTROY | Flat decomposition ceiling | **MODIFIED** — bounded recursive spawning in Wave 3 | Wave 2 adds branching factor monitor. Wave 3 adds THREAD-inspired spawning with depth/branching caps. |
| PRESERVE | LangGraph stateful orchestration | **ADOPTED** | Both reviewers agree. Framework is correct; architecture atop it needs reconstruction. |
| PRESERVE | 6-node pipeline concept | **ADOPTED** — augmented to 7+ nodes | Concept validated. Implementation of each node rebuilt to research standards. |
| PRESERVE | HITL approval gates | **ADOPTED** — hardened | Structured briefings, Markdown sanitization, provenance disclosure, all bypasses closed. |
| PRESERVE | Sequential execution with retries | **ADOPTED** — extended | Shared retry helper for both paths. Structured error classification. Compensation handler integration. |
| PRESERVE | Synthesize-then-evaluate pattern | **ADOPTED** — strengthened | Cross-agent evaluation, hard-feedback integration, structured quality metrics. |
| CREATE #1 | Domain classifier | **ADOPTED** — Wave 2 | TAPE-style triage with Cynefin-inspired domain awareness. |
| CREATE #2 | Dual-process router | **ADOPTED** — Wave 2 | Merged with CLASSIFY node. FAST/STANDARD/DEEP routing. |
| CREATE #3 | Adversarial verification engine | **DEFERRED** — Research Track | Requires building software-domain equivalent of military simulation. 2-3 year research problem. |
| CREATE #4 | 5-layer guardrail stack | **MODIFIED** — 3 layers in Wave 3 | Input, Tools, Output guardrails. Memory and Planner deferred until FPR tuning feasible. |
| CREATE #5 | Episodic memory | **ADOPTED** — Wave 2 | Merged with skill library. Per-mission and cross-mission stores. |
| CREATE #6 | Recursive spawning | **MODIFIED** — bounded, Wave 3 | Contingent on Research Track phi/psi design. Depth 3-4, branching factor 4. |
| CREATE #7 | Zero-overlap decomposer | **MODIFIED** — prompt instruction only | Not a guaranteed invariant. Bias toward non-overlap in plan prompts. Isolated state handles violations. |
| CREATE #8 | Compensation handler framework | **ADOPTED** — Wave 2 | Merged with FRAGO replanning. Retry -> catch -> local -> expand -> global -> human escalation ladder. |
| CREATE #9 | Branching factor estimator | **MODIFIED** — runtime monitor | Pre-execution estimation is circular. Runtime monitoring with halt is practical. |
| CREATE #10 | Modular planning architecture | **DEFERRED** — Wave 3, contingent | Only if Wave 2 evidence shows planner is the binding constraint. Cost-benefit evaluation required. |

**Summary:** Of Karl's 22 verdicts: 13 ADOPTED (as-is or with minor modifications), 6 MODIFIED (insight adopted, mechanism adapted), 3 DEFERRED (to Wave 3 or Research Track), 0 REJECTED outright.

---

## 9. Richard's Recommendations Disposition

| # | Richard's Recommendation | Original Wave | Disposition | New Wave |
|:--|:--|:--|:--|:--|
| 1.1 | Close C1: replan -> risk re-check | 1 | **ADOPTED** — ship immediately | 1 |
| 1.2 | Close CR1: parallel approval | 1 | **ADOPTED** — ship immediately | 1 |
| 1.3 | Close H4: remove planner bypass | 1 | **ADOPTED** — ship immediately | 1 |
| 1.4 | Close CRT1: classifier weaponization | 1 | **ADOPTED** — ship immediately; noted as Wave 1 stopgap | 1 |
| 2.1 | FRAGO delta replanning | 2 | **ADOPTED** — extended with compensation handler ladder | 2 |
| 2.2 | Pre-mortem gate | 2 | **ADOPTED** — extended with backbrief re-run loop | 2 |
| 2.3 | TAPE complexity triage | 2 | **ADOPTED** — extended with Cynefin domain awareness, denylist on FAST path | 2 |
| 3.1 | Backbrief verification | 3 | **ADOPTED** — moved to Wave 2; extended with DSM analysis | 2 |
| 3.2 | Parallel retry logic (CR2) | 2 | **ADOPTED** — shared helper | 2 |
| 3.3 | Replan ceiling (C2) | 2 | **ADOPTED** — moved to Wave 1 (trivial, high-impact) | 1 |
| 4.1 | Skill library | 3 | **MODIFIED** — moved to Wave 2; Karl's timing, Richard's design | 2 |

**Summary:** Of Richard's 11 recommendations: 10 ADOPTED (5 with extensions), 1 MODIFIED (skill library — same design, earlier wave), 0 REJECTED. No recommendation was wrong. Several were correctly identified but mistimed (deferred to Wave 3 when they should ship in Wave 2).

---

## 10. What the Combined Work Demands

### 10.1 Principles

1. **Empiricism over ideology.** Fix the known bugs. Establish baselines. Measure the impact of each change. Let the data decide between reform and revolution. Karl's dialectical method and Richard's tactical prioritization are both subordinate to evidence.

2. **Foundations before capability layers.** Structural work (monolith split, memory system, LLM-based classifier) must happen in Wave 2, before the Wave 3 advanced capabilities. Adding capabilities to a monolith with regex safety and no memory is building on sand.

3. **Engineering, not research.** The Wave 1-2 program contains no research-risk items. Every task has a known implementation path. The Research Track runs in parallel and gates the research-dependent Wave 3 items.

4. **Compound benefits over immediate impact.** The skill library, monolith split, and memory system have benefits that compound across tasks. Their value at t=100 dwarfs their value at t=1. Prioritization frameworks that only measure immediate impact (IMPACT/EFFORT at t=1) will systematically undervalue them.

5. **Safety as architecture, not feature.** The approval gate, risk classifier, and guardrails are not features bolted onto the pipeline. They are the pipeline's load-bearing structure. Default-deny. Defense-in-depth. Independent verification. These are architectural invariants, not configuration options.

### 10.2 Execution Order

1. **Wave 1 security fixes** (no architectural changes, urgent, ship immediately)
2. **Benchmark baselines** (establish before any architectural work)
3. **Wave 2 architecture foundation** (monolith split, memory, LLM classifier, FRAGO, pre-mortem, backbrief, triage, isolated-state executor)
4. **Measure against baselines** (did Wave 2 improve task success rate? cost per task? approval burden?)
5. **Decide Wave 3 scope** (based on Wave 2 evidence: which advanced capabilities address measured gaps?)
6. **Research Track feasibility gates** (before committing to research-dependent Wave 3 items)

### 10.3 What NOT to Build (Yet)

1. **Full IFPV adversarial verification engine.** Research problem. Feasibility study first.
2. **Full MAP 6-module planner.** Unclear if planner is the binding constraint. Cost-benefit evaluation first.
3. **Unbounded recursive spawning.** Phi/psi design unsolved for software tasks. Bounded spawning in Wave 3 contingent on Research Track.
4. **Full 5-layer guardrail stack.** False-positive tuning unsolved for Memory and Planner layers. Ship 3 layers in Wave 3.
5. **Pre-execution branching factor estimator.** Circular. Runtime monitor instead.

### 10.4 Risk Register

| Risk | Likelihood | Impact | Mitigation |
|:--|:--|:--|:--|
| Monolith split breaks LangGraph compiled graph | Medium | High | Split one module at a time; verify graph integrity after each split; maintain integration test suite |
| Pre-mortem/backbrief interaction creates infinite loop | Medium | Medium | Hard iteration ceiling (max 2 pre-mortem cycles); backbrief re-run enforced in graph topology |
| Isolated-state executor incompatible with LangGraph shared-state model | Medium | High | Prototype early in Wave 2; fall back to semaphore-based isolation if LangGraph constraints are insurmountable |
| LLM-based classifier has unacceptable false-positive rate | Medium | Medium | Conservative tuning (err toward MEDIUM, not HIGH); human-in-the-loop for all HIGH classifications; A/B test against regex baseline |
| Wave 2 scope expands beyond 3 months | High | Medium | Ruthless prioritization: FRAGO, pre-mortem, backbrief, triage, and classifier are non-negotiable. Skill library and executor redesign can be descoped to minimum viable versions if timeline slips |
| Research Track items yield no implementable results | High | Low (for Waves 1-2); Medium (for Wave 3) | Wave 3 items dependent on Research Track are explicitly contingent. Wave 3 has sufficient non-research-dependent items to ship value |
| Benchmark suite not representative of real user tasks | Medium | Medium | Supplement SWE-bench with custom task suite drawn from actual JORDAN usage patterns; iterate benchmark design |

---

## Appendix A: Framework-to-Recommendation Traceability

| Unified Recommendation | Primary Framework(s) | Research Items | Adopted From |
|:--|:--|:--|:--|
| Wave 1 gate fixes (C1, CR1, H4, CRT1) | MDMP, Commander's Intent, Red Teaming | 1, 2, 4, 8, 12, 13 | Richard + Karl (unanimous) |
| FRAGO delta replanning + compensation ladder | FRAGO, ALAS, OODA | 15, 51, 3 | Richard + Karl (unanimous) |
| Pre-mortem gate | Pre-mortem Analysis, MDMP COA Wargaming, Red Teaming | 25, 1, 8 | Richard + Karl (unanimous) |
| TAPE triage (CLASSIFY) | TAPE, Cynefin | 56, 20 | Richard + Karl (unanimous) |
| Backbrief + DSM verification | Backbriefing/ROC Drill, DSM, SMEAC | 10, 6, 32 | Richard (backbrief) + Karl (DSM amendment) |
| Skill library + episodic memory | Voyager/DEPS, Reflexion, A3 | 46, 48, 23 | Richard (design) + Karl (Wave 2 timing) |
| LLM-based risk classifier | IFPV (insight), Safety Frameworks (principle) | 60, 54, 55 | Synthesis (bridge between regex and ACSE) |
| Isolated-state parallel executor | CommandCC (insight), Agentic Compute Criticality (ceiling) | 49, 48 | Synthesis (bridge between incremental fix and zero-overlap) |
| Runtime branching factor monitor | Agentic Compute Criticality | 48 | Synthesis (monitor, not pre-execution estimator) |
| Commander's Intent output format | Commander's Intent, Mission Command | 4 | Richard (format) + Karl (domain-dependent allocation) |
| Monolith split | MAP (modularity principle), Software engineering (separation of concerns) | 40 | Karl (Wave 2 timing) + Richard (functional split scope) |
| Recursive spawning (bounded, Wave 3) | THREAD | 47 | Karl (capability) + Richard (bounded, research-gated) |
| Guardrail stack (3-layer, Wave 3) | Enkrypt, OWASP, NIST AI RMF | 54, 53, 55 | Karl (architecture) + Richard-on-Karl (FPR constraint) |
| Modular planner (Wave 3, contingent) | MAP | 40 | Karl (concept) + Richard-on-Karl (cost-benefit gate) |
| Adversarial verification engine (Research Track) | IFPV | 60 | Karl (vision) + Richard-on-Karl (research classification) |

---

## Appendix B: Tone and Framing Lessons

This synthesis adopts Richard's empirical precision over Karl's revolutionary rhetoric. "FALSIFIED" is not the right word for a benchmark result on Towers of Hanoi that does not address software development. "DESTROY" is not the right word for refactoring a Python module. The language of software engineering — fix, refactor, replace, redesign, measure, iterate — is more precise and more honest.

But Karl's rhetorical excess should not obscure his structural insights. He correctly identified that the monolith must be split before new nodes are added, that the skill library compounds across tasks and belongs in Wave 2, that the regex classifier is a category error regardless of how well it is patched, and that Richard's IMPACT/EFFORT framework systematically undervalues architectural changes whose benefits are deferred. These are correct and important. They just didn't need Marx to express them.

Richard's tactical precision — exact code locations, line-count estimates, concrete implementation sketches, "what NOT to do" prohibitions — is the right engineering voice for implementation. His blind spots (myopic IMPACT/EFFORT, deferring foundational work, treating the classification fast path as a new bypass) are real but correctable. His empiricism — fix the bugs, establish baselines, then decide — is the right methodological stance.

---

## Conclusion

The Culture builds GSVs — General Systems Vehicles — that operate for decades, housing billions, through a combination of elegant initial design and continuous self-improvement. A GSV is not built by revolution (tearing down the old) or by reform (patching the old). It is built by **deep refit**: structural work done early, scoped to what is achievable, measured at every step, with a clear migration path from current state to target state.

JORDAN v2 should be a deep refit. The four gate fixes ship immediately — they are not architectural, they are surgical. The benchmark baselines are established before anything else changes — without them, improvement is a rumor. Then the foundations are restructured (monolith split, memory system, LLM-based classifier) BEFORE the capability layers are added (modular planner, recursive spawning, adversarial verification). At each step, the system is measured against baselines and the next step is confirmed or adjusted.

Richard provides the tactical plan — what to fix, where, in what order, with what code. Karl provides the structural critique — which foundations must be rebuilt, which deferrals are abandonment, which compound benefits are invisible to single-task measurement. The synthesis is a deep refit that does the structural work early enough to compound, keeps the scope to what is achievable, and lets evidence decide the rest.

The point is not to win an argument between reform and revolution. The point is to build a JORDAN v2 that does not need a v3 to fix what v2 deferred.

---

*"No starship was ever built by a committee, but every good one was designed by a Mind that listened to its crew."*

Richard and Karl are the crew. The synthesis is the design. Now build it.
