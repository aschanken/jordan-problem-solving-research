# JORDAN v2 Spec — Arbitration Log

**Arbitrator:** Iain M. Banks (Mind of the Culture)
**Date:** 2026-05-23
**Source documents:** richard-revision-01.md (impl spec), karl-revision-02.md (flowchart), richard-revision-03.md (testing spec)
**Consistency audits:** cross-document-consistency.md (Richard, 20 findings), cross-document-consistency-karl.md (Karl, 9 findings)
**Total findings resolved:** 29

---

## Design Decisions

### DD-001: LangGraph Subgraphs for Isolated State

**Chosen over:** private-dict workaround, per-subtask channels
**Rationale:** Subgraphs provide true checkpoint-isolated state — each subgraph's state is checkpointed independently, supports Send/Join for parent-child orchestration, and integrates with LangGraph's existing checkpoint/resume machinery. A private-dict workaround would break checkpoint resume on parallel paths.
**Consequence:** Adds ~200 lines of Subgraph orchestration code. Requires LangGraph >=0.3.0. Subgraph serialization adds ~15% overhead to checkpoint size.

### DD-002: FRAGO Delta Validation (3-Check)

**Chosen:** Lightweight structural check on every FRAGO delta before re-execution
**Checks:** (1) DAG cycle detection on modified sub-tasks + transitive dependents, (2) branching factor estimate on new/modified sub-tasks (b < 1), (3) risk delta scan — if any new sub-task risk > original plan risk, escalate to full re-classification
**Consequence:** Adds 20-50ms per FRAGO cycle (deterministic checks, no LLM calls)

### DD-003: Risk Fusion — Max-Severity Rule

**Chosen:** `final_risk[sub_task] = max(RA_classification, PREMORTEM_severity)` with automatic escalation for safety-critical domains and branching violations. Individual signals preserved in briefing for human drill-down.
**Rationale:** Pre-mortem catches plan-level failure modes the per-task classifier misses. The max rule ensures the more conservative signal wins. The briefing preserves the raw signals so the human can assess trade-offs.

### DD-004: DEEP Path Mechanisms

**Resolved: All four add to the implementation spec.**

| Feature | Mechanism | Location |
|:--|:--|:--|
| Always-on approval | `path == "DEEP"` conditional in APPROVAL gate routing: ALL DEEP sub-tasks require human approval regardless of risk level (synthesis.md: "Complex tasks engage the full pipeline with pre-mortem and multiple COA generation") | APPROVAL routing (Section 9) |
| Multi-COA planning | Plan node receives `n_coas=3` parameter on DEEP path. Returns `list[Plan]`. Select best plan via backbrief + pre-mortem before committing. Cost: 3x planning LLM calls. DEEP path only. | PLAN node (Section 3) |
| MAKER decomposition | For DEEP sub-tasks flagged as `correctness_critical AND verifiable_output`, decompose to atomic steps (MAKER m=1). Verification via structured test/check at each step. Cost: more sub-tasks, but log-linear cost scaling per MAKER. | PLAN DEEP path (Section 3.8) |
| Sequential execution | `ExecutionMode.SEQUENTIAL` override on DAG scheduler when `path == "DEEP"`. Parallel mode requires explicit user opt-in on DEEP tasks. | DAG scheduler (Section 10) |

**Rationale for making DEEP real:** Karl is correct that flowchart DEEP vs implementation spec STANDARD being identical is a build-breaking contradiction. The synthesis.md explicitly defines DEEP as multi-COA, MAKER decomposition, sequential default. These must be in the implementation spec or the flowchart must downgrade DEEP to STANDARD. Synthesis chose the former — make DEEP real — because the architecture needs this capability for the complex/safety-critical tasks where the STANDARD path is insufficient.

### DD-005: PREMORTEM Backbrief Interaction — Independent Counters

**Chosen as specified in richard-revision-01.md:** BACKBRIEF tracks `backbrief_revision_count` (max 2). PREMORTEM tracks `premortem_cycle_count` (max 2). Two separate counters, both carried forward across cycles. PREMORTEM-triggered plan revision routes back through BACKBRIEF; BACKBRIEF re-verifies the revised plan; counter increments independently.

**Interaction rule:** When PREMORTEM triggers a revision, the plan version increments. BACKBRIEF tracks its count against the CURRENT plan version — revisions from PREMORTEM do NOT reset BACKBRIEF's counter for the same version, but BACKBRIEF must re-verify on version change and its counter increments on each verification pass.

### DD-006: Risk Fusion and FRAGO Staleness

**Chosen:** PREMORTEM data in FRAGO risk fusion is marked with plan version. If the FRAGO delta changes the plan version, stale PREMORTEM data is NOT consumed in risk fusion — only fresh RA re-classification of changed sub-tasks is used. PREMORTEM re-runs only on full replan (non-delta), not on FRAGO.
**Consequence:** Risk fusion in FRAGO mode uses RA data only. PREMORTEM data is excluded by version check. This is correct because PREMORTEM operates on the full plan, and FRAGO is a delta — the full-plan analysis is only valid for the pre-delta plan.

### DD-007: DEEP Path in Monolith Split Scope

**Chosen:** The monolith split (Wave 2) includes the DEEP path extensions. The `Plan` dataclass supports `n_coas` and `list[Plan]` from day one. The DAG scheduler supports `ExecutionMode` from day one. MAKER decomposition is a Wire 2.5 incremental addition (prompt engineering + step verification, not a framework change).
**Rationale:** Adding DEEP path mechanisms after the monolith split would require revisiting the split interfaces. Build them into the split from the start.

### DD-008: Risk Fusion Dead Code Fix

**Chosen:** Remove rule 4 from the risk fusion algorithm (elevation on `halt_flag`). The branching factor monitor routes to REPLAN directly, not through risk fusion. Add a note in risk fusion: "Branching violations are handled by the BRANCHING MONITOR → REPLAN path. Risk fusion does not process stop signals."
**Rationale:** Karl BB5 is correct — the rule references state that cannot occur under the graph topology. Remove dead code rather than change the topology.

### DD-009: Persona Count and Set

**Chosen:** 4 standard personas (Pessimist, Optimist, Devil's Advocate, Resource Analyst). DEEP path adds one more (Domain Expert). Total 5.
**Add to implementation spec Section 7.** Align flowchart Section 3 and testing spec Section 2 (PREMORTEM tests).
**Rationale:** Karl BB6 is correct — three documents disagree on the count. The implementation spec must enumerate the set, and the other two documents must reference the same enumeration.

---

## Finding Resolutions

### Richard's Consistency Audit (20 findings)

| ID | Severity | Description | Resolution | Action |
|:--|:--|:--|:--|:--|
| R-C1 | CRITICAL | Compensation escalation monotonicity untested | **Add test** to testing spec Section 5 | `test_compensation_monotonic_escalation` |
| R-H1 | HIGH | Persona calibration auto-disable untested | **Add test** to testing spec Section 2 (PREMORTEM) | `test_persona_fp_threshold_disable` |
| R-H2 | HIGH | PREMORTEM force-pass on all-persona-failure untested | **Add test** to testing spec Section 2 (PREMORTEM) | `test_premortem_all_personas_fail_forces_pass` |
| R-H3 | HIGH | Branching monitor runtime halt untested | **Add test** to testing spec Section 2 (BRANCHING MONITOR) | `test_branching_monitor_runtime_halt` |
| R-H4 | HIGH | UNEQUIVALENT evaluation status untested | **Add test** to testing spec Section 2 (EVALUATE) | `test_evaluate_unequivalent_status` |
| R-H5 | HIGH | `skill_template_sanitized` field undefined in impl spec | **Add field** to impl spec Section 14 (SKILL LIBRARY) | Add to SkillLibrary schema |
| R-H6 | HIGH | `scope_change_message` field undefined in impl spec | **Add field** to impl spec Section 9 (APPROVAL) | Add to ApprovalBriefing schema |
| R-H7 | HIGH | `has_unaddressed_safety_flags` field undefined in impl spec | **Add field** to impl spec Section 9 (APPROVAL) | Add to ApprovalBriefing schema |
| R-M1 | MEDIUM | Denylist FP feedback loop untested | **Add test** to testing spec Section 5 | Add denylist FP log test |
| R-M2 | MEDIUM | CLASSIFY scope change detection untested | **Add test** to testing spec Section 2 (CLASSIFY) | Add scope change test |
| R-M3 | MEDIUM | Cross-tenant isolation untested | **Add test** to testing spec Section 7 | Add isolation test |
| R-M4 | MEDIUM | Stale template handling untested | **Add test** to testing spec Section 2 (SKILL LIBRARY) | Add stale template test |
| R-M5 | MEDIUM | Compensation/replan counter interaction untested | **Add test** to testing spec Section 3 | Add interaction test |
| R-M6 | MEDIUM | `backbrief_forced` consumer coverage untested | **Add test** to testing spec Section 2 (PREMORTEM) | Add consumer test |
| R-M7 | MEDIUM | Resource Analyst persona flowchart self-contradiction | **Fix flowchart** Section 3 | Align to DD-009 persona set |
| R-M8 | MEDIUM | Denylist FP log in skill library untested | **Add test** to testing spec Section 2 (SKILL LIBRARY) | Add FP log test |
| R-M9 | MEDIUM | Hallucination fallback flow untested | **Add integration test** to testing spec Section 3 | Add hallucination recovery test |
| R-L1 | LOW | "pre-mortem" vs "premortem" hyphenation | **Standardize** to "pre-mortem" throughout (synthesis.md usage) | Global find-replace |
| R-L2 | LOW | TRIVIAL/MODERATE/COMPLEX labels not in impl spec | **Add labels** to impl spec Section 1 (CLASSIFY) | Add classification outcome labels |
| R-L3 | LOW | Delta-aware BACKBRIEF detail omitted from flowchart | **Acceptable simplification** — flowchart is ELI5 | No action |

### Karl's Consistency Audit (9 findings)

| ID | Severity | Description | Resolution | Action |
|:--|:--|:--|:--|:--|
| K-BB1 | BUILD-BREAKING | DEEP always-on approval missing from impl spec | **Add** `path == "DEEP"` conditional to APPROVAL routing | Impl spec Section 9 (DD-004) |
| K-BB2 | BUILD-BREAKING | Multi-COA planning missing from impl spec | **Add** `n_coas` param, `list[Plan]` output, COA selection via backbrief+premortem | Impl spec Section 3 (DD-004) |
| K-BB3 | BUILD-BREAKING | MAKER decomposition missing from impl spec | **Add** MAKER m=1 mode for correctness_critical AND verifiable_output sub-tasks | Impl spec Section 3.8 (DD-004) |
| K-BB4 | BUILD-BREAKING | Sequential execution mode missing from impl spec | **Add** ExecutionMode.SEQUENTIAL override to DAG scheduler | Impl spec Section 10 (DD-004) |
| K-BB5 | BUILD-BREAKING | Risk fusion rule 4 dead code | **Remove** rule 4, add note about branching monitor handling | Impl spec Section 9.10 (DD-008) |
| K-BB6 | BUILD-BREAKING | Persona count mismatch (4 vs 5 across docs) | **Enumerate** set in impl spec Section 7, align flowchart and testing spec | DD-009 |
| K-H1 | HIGH | PREMORTEM force-pass conditions interaction undefined | **Define** in impl spec: if ALL personas fail, skip PREMORTEM (force-pass) rather than blocking. On ceiling hit, force-pass with highest-severity findings attached as advisory (not blocking). | Impl spec Section 7.5 |
| K-H2 | HIGH | FRAGO risk fusion consumes stale PREMORTEM | **Define** in impl spec DD-006: FRAGO risk fusion excludes PREMORTEM data by plan-version check | Impl spec Section 13.5 (DD-006) |
| K-H3 | HIGH | User scope change at RESEARCH interruption undefined | **Define** in impl spec: if user changes scope during RESEARCH interruption, re-run CLASSIFY on the new scope before resuming. Scope change detected via diff on user input. | Impl spec Section 4.5 |

---

## Summary

**29 findings resolved:**
- 6 BUILD-BREAKING → all fixed in design decisions above
- 1 CRITICAL → test added
- 10 HIGH → 7 tests added, 3 field definitions added to implementation spec
- 9 MEDIUM → 8 tests added, 1 flowchart fix
- 3 LOW → 1 standardization, 1 label addition, 1 no-action

**9 design decisions documented** covering the DEEP path architecture, risk fusion, FRAGO staleness, persona sets, and interaction rules.

The three final deliverables incorporate all resolutions above.
