# Cross-Document Consistency Audit -- KARL (Dialectical Critique)

**Auditor:** Karl (dialectical critic, structural analyst)
**Date:** 2026-05-25
**Scope:** richard-revision-01.md (implementation), karl-revision-02.md (flowchart), richard-revision-03.md (testing), cross-document-consistency.md (Richard's audit)
**Method:** Read Richard's audit AFTER completing my own independent analysis. This document contains only findings Richard did NOT catch or did not fully characterize.

---

## Summary

| Priority | Count | What Richard Caught | What I Found That He Missed |
|----------|-------|--------------------|---------------------------|
| BUILD-BREAKING | 6 | 0 | 6 (contradictions where spec A says X, spec B says Y, and the code literally cannot be written without choosing) |
| HIGH | 6 | 3 | 3 (hidden coupling + emergent gaps that will surface as runtime failures) |
| MEDIUM | 8 | 3 | 5 (verification blind spots at the intersection of specs) |
| LOW | 4 | 2 | 2 (terminology drift Richard either missed or undergraded) |
| **Total** | **24** | **8** | **16** |

**Richard's audit contribution (8 of 24):** Found H1 (persona calibration), H2 (all-personas-fail), H3 (runtime branching monitor), M5 (compensation/replan counter interaction), M6 (backbrief_forced consumers), M7 (Resource Analyst flowchart contradiction), M8 (denylist FP log target), M9 (hallucination integration test).

**My contribution (16 of 24):** Found 6 build-breaking contradictions Richard missed entirely, 3 HIGH coupling/gap findings, 5 MEDIUM verification blind spots, and 2 LOW terminology drifts.

---

## BUILD-BREAKING CONTRADICTIONS

These are not "missing tests" or "naming inconsistencies." These are contradictions where two specs describe mutually exclusive behavior, and the implementer must choose which spec to violate. Richard's audit found ZERO findings in this category.

---

### BB1. DEEP Path: Always-Show APPROVAL Has No Mechanism in Implementation Spec

**Documents in conflict:** FLOWCHART vs IMPLEMENTATION_SPEC

**Flowchart, Section 2 (DEEP Path, point 5, line 121):**
> "Approval Gate Always Active. On the DEEP path, the approval gate is always presented, regardless of risk level. Every sub-task gets human review."

**Flowchart, Section 3 (DEEP Path Detail, D.3, line 866-869):**
> "[D.3 APPROVAL -- ALWAYS ACTIVE] Regardless of risk level, briefing ALWAYS presented. Tier 2 detail shown by DEFAULT (not hidden)."

**Implementation spec, Section 9.7 (Interactions, line 780-784):**
> "On replan re-entry: On replan, if RISK ASSESSMENT re-classifies any sub-task as CRITICAL, the graph routes to RISK FUSION (refresh reconciliation) -> APPROVAL (with diff briefing). If no CRITICAL re-classification, APPROVAL is bypassed (as in v1)."

**Implementation spec, Section 9.5.C (line 749):**
> "CRITICAL sub-tasks always route through APPROVAL, but `approval_decision = 'approved'` allows execution to proceed."

**The contradiction:** The flowchart states APPROVAL is always shown on DEEP path regardless of risk. The implementation spec's APPROVAL routing logic triggers only on HIGH/CRITICAL risk levels and explicitly bypasses APPROVAL when no CRITICAL re-classification occurs. There is no `path == "DEEP"` conditional, no `force_approval_on_deep` flag, and no mechanism described for bypassing the risk-level trigger. A developer building from the implementation spec alone would skip APPROVAL on a DEEP path with all LOW sub-tasks. An E2E test expecting APPROVAL on every DEEP task would fail.

**Contradiction type:** Routing logic contradiction. The implementation spec provides no code path for the flowchart's behavior.

**What must change:** Add a `force_approval_on_deep_path: bool` routing flag to the APPROVAL GATE section (implementation spec 9.3-9.7) with explicit logic: `if state.path == "DEEP": always present briefing`. The routing decision {S.14} in the flowchart must fork on both `risk_level` AND `path_type`.

**Why Richard missed this:** Richard's audit searches for "implementation says X, testing doesn't test X" and "testing references field Y, implementation doesn't define Y." He never asks "does the implementation spec actually PRODUCE the behavior the flowchart describes?" His audit treats the implementation spec as the ground truth and only checks the testing spec against it -- it never checks the flowchart's behavioral claims against the implementation spec's mechanisms.

---

### BB2. DEEP Path: Multi-COA Planning Has No Data Model in Implementation Spec

**Documents in conflict:** FLOWCHART vs IMPLEMENTATION_SPEC

**Flowchart, Section 2 (DEEP Path, point 1, line 113):**
> "Multi-COA Planning. Instead of producing one plan, JORDAN generates multiple Courses of Action (COAs) -- different approaches to the same problem. It compares them and selects the best one (or presents options if the trade-offs are significant)."

**Flowchart, DEEP Path Detail (D.1, line 849-852):**
> "[D.1 PLAN -- MULTI-COA] Generate MULTIPLE Courses of Action. Compare and select best (or present options). MAKER decomposition: break sub-tasks to smallest verifiable units."

**Implementation spec, Section 3.4 (Plan dataclass, line 249-257):**
```python
@dataclass
class Plan:
    commander_intent: CommanderIntent
    sub_tasks: list[SubTaskDef]
    dag: dict[str, list[str]]
    plan_version: int
    plan_checksum: str
    metadata: dict
```

**The contradiction:** The flowchart says PLAN produces MULTIPLE plans on DEEP path. The implementation spec defines a single `Plan` dataclass. Every node downstream (BACKBRIEF, RESEARCH, RISK ASSESSMENT, PREMORTEM, BRANCHING MONITOR, APPROVAL, EXECUTE) accepts a single `Plan`. There is no `list[Plan]` anywhere in the type system. There is no COA comparison algorithm, no COA selection mechanism, and no interface for presenting multiple COAs at APPROVAL.

**Contradiction type:** Data model contradiction. The flowchart describes output cardinality (1 -> N) that the implementation spec's type system cannot represent.

**What must change:** Either (a) add multi-COA to the implementation spec with a `list[Plan]` type, COA comparison logic in PLAN, and COA selection in APPROVAL, or (b) acknowledge multi-COA as Wave 3 and remove it from the v2 flowchart. A developer building from the implementation spec cannot fudge this -- the data model literally cannot hold what the flowchart says it holds.

**Why Richard missed this:** Richard's audit scope is "implementation spec as ground truth." He verifies that the testing spec matches the implementation spec. He never checks the flowchart's functional claims against the implementation spec's data model. The flowchart can describe features that literally do not exist.

---

### BB3. DEEP Path: MAKER Decomposition Has No Mechanism

**Documents in conflict:** FLOWCHART vs IMPLEMENTATION_SPEC

**Flowchart, DEEP Path Detail (D.1, line 851):**
> "MAKER decomposition: break sub-tasks to smallest verifiable units."

**Flowchart, Section 2 (DEEP Path, point 2, line 117):**
> "MAKER Decomposition. Sub-tasks are broken down to the smallest verifiable units. If a sub-task is critical (could cause serious harm if wrong), it is decomposed further until each piece is independently checkable."

**Implementation spec:** The word "MAKER" does not appear anywhere in the 1662-line implementation spec. There is no decomposition algorithm, no "verifiable unit" threshold, no mechanism for dynamically splitting a sub-task into smaller sub-tasks at plan time. The PLAN node produces `list[SubTaskDef]` with no sub-splitting logic.

**Contradiction type:** Feature exists in flowchart, zero implementation.

**What must change:** Same as BB2 -- either implement MAKER decomposition with a recursive split algorithm in PLAN (and add to the data model), or remove it from the v2 flowchart.

**Why Richard missed this:** Same root cause as BB2. Richard's audit framework is implementation-spec-centric and does not validate the flowchart's feature claims.

---

### BB4. DEEP Path: Sequential Execution Default Has No Mechanism

**Documents in conflict:** FLOWCHART vs IMPLEMENTATION_SPEC

**Flowchart, Section 2 (DEEP Path, point 3, line 119):**
> "Sequential Default (not parallel). DEEP tasks default to sequential execution -- one step at a time -- because the dependencies are more intricate and the cost of a parallel execution mistake is higher."

**Flowchart, DEEP Path Detail (D.4, line 872-876):**
> "[D.4 EXECUTE -- SEQUENTIAL DEFAULT] Default: sequential execution (not parallel). Parallel only if explicitly approved during planning."

**Implementation spec, Section 10 (EXECUTE):** The entire EXECUTE node specification describes parallel dispatch via LangGraph Subgraphs with `Send()` and `Join()`. The `concurrency_limit` defaults to 4. The DAG scheduler's `get_ready()` returns a list of ready sub-tasks for parallel execution. There is no `execution_mode: Literal["parallel", "sequential"]` field. There is no DEEP-path conditional that overrides the DAG scheduler to single-threaded mode.

**Contradiction type:** Execution topology contradiction. The implementation spec's EXECUTE is inherently parallel; the flowchart says DEEP is sequentially default.

**What must change:** Add `execution_mode` to the Plan or ExecutionContext, respected by the DAG scheduler. `get_ready()` returns at most 1 sub-task when `execution_mode == "sequential"`.

**Why Richard missed this:** Same root cause. The flowchart-as-ground-truth check was never performed.

---

### BB5. Risk Fusion Rule 4 (BRANCHING MONITOR Halt Flag) Is Dead Code

**Documents in conflict:** IMPLEMENTATION_SPEC vs FLOWCHART (graph topology)

**Implementation spec, Section 9.10.3 (Reconciliation Rules, rule 4, line 816-817):**
> "If BRANCHING MONITOR's halt_flag is True: Overall risk is elevated to HIGH (divergent branching is a structural risk)."

**Implementation spec, Section 9.10.6 (Edge Cases, line 843):**
> "BRANCHING MONITOR halt with no other signals: Overall risk set to HIGH. Individual sub-task risks unchanged."

**Flowchart, Section 6 (STANDARD Path, S.11-S.12, line 650-667):**
```
[ S.11 BRANCHING FACTOR MONITOR ]
Static DAG analysis: fan-out, max depth
{ S.12 BRANCHING VIOLATION? }
     YES -> [HALT -> escalate to REPLAN with structural flag]
     NO  -> [continue to S.13 RISK FUSION -> S.14 APPROVAL]
```

**The contradiction:** The flowchart topology routes `halt_flag=True` to REPLAN, NOT to RISK FUSION. If the static BRANCHING MONITOR detects a violation, the graph bypasses RISK FUSION entirely and goes to REPLAN. The `halt_flag` can NEVER reach RISK FUSION under the current graph topology, because the only path to RISK FUSION is through the `NO` branch of {S.12}. Rule 4 in the reconciliation algorithm and the corresponding edge case in 9.10.6 describe a state that the graph topology makes unreachable. This is dead code in the specification -- a formally specified behavior that can never execute.

**Contradiction type:** Specified behavior contradicts graph topology. The rule is correct (divergent branching IS a structural risk), but the graph prevents it from ever firing.

**What must change:** Either (a) remove rule 4 and the 9.10.6 edge case from the implementation spec (accept that branching halt is handled at the graph level, not at the risk fusion level), or (b) change the graph topology to route to RISK FUSION even on branching violation (which would change the pipeline's behavior: instead of immediately replanning, it would present a HIGH-risk plan to APPROVAL). Option (a) is correct and simpler.

**Why Richard missed this:** Richard's audit treats each document's internal logic as correct and only checks cross-document field references. He did not trace the graph topology to verify that every state described in the node specs is actually reachable. This is a liveness analysis -- a dialectical, not documentary, concern.

---

### BB6. Persona Count: 4 in Flowchart, "5" in Testing Spec

**Documents in conflict:** IMPLEMENTATION_SPEC vs FLOWCHART vs TESTING_SPEC

**Flowchart, Section 3 (Safety Features -- Pre-Mortem, line 160-164):**
Lists exactly 4 personas: Pessimist, Optimist, Devil's Advocate, Resource Analyst.

**Implementation spec, Section C.3 (Resource feasibility persona, line 1506-1507):**
> "PREMORTEM's persona set now includes a 'Resource Analyst' persona (added to the standard set for DEEP path, available for STANDARD path)."

No enumeration of the complete persona set. The persona names "Pessimist," "Optimist," "Devil's Advocate" appear in section 7.5.C (calibration tracking) but the standard set is never formally listed.

**Implementation spec, Section 7.5.D (line 553):**
> "PREVIOUS PREMORTEM cycle will re-flag them."

No persona count given.

**Testing spec, Section 5.11.2 (PREVIOUS PREMORTEM Persona Consensus, line 1017-1044):**
```python
# Scenario: 3 of 5 personas flag the same fatal flaw
state_high_consensus = PipelineState(
    fatal_flags=[FatalFlag(description="Database risk", severity="HIGH",
                           flagged_by=["persona_A", "persona_B", "persona_C"])]
)
# Scenario: only 1 of 5 personas flags
state_low_consensus = PipelineState(
    fatal_flags=[FatalFlag(description="Database risk", severity="HIGH",
                           flagged_by=["persona_A"])]
)
```

Asserts "3 of 5" and "1 of 5" personas. The number 5 appears nowhere else in the spec system. The flowchart describes 4. The implementation spec never enumerates. Is there a fifth persona? What is it? If the test expects 5 and only 4 exist, the consensus ratio is wrong (3/4 vs 3/5, 1/4 vs 1/5 -- different agreement thresholds).

**Contradiction type:** Cardinality contradiction. Two documents disagree on a fundamental count (4 vs 5), and the third document is silent.

**What must change:** (a) Formally enumerate the persona set in the implementation spec (Section 7: Pessimist, Optimist, Devil's Advocate, Resource Analyst = 4 in v2). (b) Update testing spec 5.11.2 to use "3 of 4" and "1 of 4." (c) If a 5th persona genuinely exists, name it and add it to all three documents. The number must be consistent across the spec system.

**Why Richard missed this:** Richard's audit identifies the Resource Analyst contradiction (his M7 -- flagged as MEDIUM, internal flowchart ambiguity). He did not count the personas across documents and compare. His M7 finding is about the flowchart contradicting itself; it does not catch the cross-document count mismatch with the testing spec.

---

## HIGH PRIORITY FINDINGS

These are not build-breakers (no single contradiction prevents compilation), but they will surface as runtime failures, untested coupling, or emergent behavior gaps.

---

### H1. (Karl) PREMORTEM All-LLM-Fail Force-Pass vs. Cycle-Ceiling Force-Pass -- Two Conditions, Unclear Interaction

**Documents in conflict:** IMPLEMENTATION_SPEC internal (ambiguity)

**Implementation spec, Section 7.1 (line 512-513):**
> "Exception: if ALL persona LLM calls fail (not just some), PREMORTEM cannot produce scenarios and is force-passed with a critical log alert. This is a system-health failure, not an advisory opt-out."

**Implementation spec, Section 7.5 (line 534-533):**
> "Max 2 pre-mortem cycles."

**The gap:** There are two distinct force-pass conditions for PREMORTEM: (A) ALL persona LLMs fail (system-health failure), and (B) cycle count >= 2 (ceiling). The implementation spec does not specify their interaction. Does the ALL-fail force-pass consume a cycle? If ALL personas fail on cycle 1, does the cycle counter increment? On the next regeneration, will PREMORTEM run again (cycle 2) or is it already force-passed?

If ALL-fail does NOT consume a cycle: PREMORTEM runs again on regeneration with a fresh LLM call -- but why would the LLMs succeed this time if they all failed last time? This could cause infinite looping.

If ALL-fail DOES consume a cycle: explicit behavior needed. "ALL-persona-fail immediately force-passes and increments premortem_cycle_count by 1."

**Richard's H2** noted that this edge case is untested. He did not identify the ambiguous interaction between the two force-pass conditions. His finding is about missing test coverage; mine is about undefined behavior under simultaneous conditions.

**What must change:** Specify in implementation spec Section 7.5: "If ALL persona LLM calls fail, PREMORTEM immediately force-passes with `critical_log_alert = True` AND increments `premortem_cycle_count` by 1 (it consumes a cycle). If the ceiling (2) is also reached, the force-pass is attributed to BOTH causes in the log."

---

### H2. (Karl) FRAGO Replan Consumes Stale PREMORTEM Data Through Risk Fusion

**Documents in conflict:** IMPLEMENTATION_SPEC internal / FLOWCHART

**Implementation spec, Section 9.7 (line 782-783):**
> "On replan re-entry: On replan, if RISK ASSESSMENT re-classifies any sub-task as CRITICAL, the graph routes to RISK FUSION (refresh reconciliation) -> APPROVAL (with diff briefing)."

**Implementation spec, Section 13.5.A (line 1251):**
> "These three checks REPLACE full BACKBRIEF, PREMORTEM, and BRANCHING MONITOR re-runs on the replan path."

**The gap:** On replan, PREMORTEM is NOT re-run. But RISK FUSION reads `failure_scenario_severities` from PREMORTEM (section 9.10.2, line 803). On replan re-entry, RISK FUSION's PREMORTEM input is the ORIGINAL plan's scenarios -- now stale. The delta plan may have changed sub-tasks, added new ones, or removed old ones. The PREMORTEM scenarios indexed by the old `plan_checksum` do not correspond to the new delta plan. Risk fusion is reconciling fresh RISK ASSESSMENT data with stale PREMORTEM data against a changed plan.

**Contradiction type:** Temporal coupling. The risk fusion step assumes PREMORTEM data is current, but on the replan path it is stale by construction (PREMORTEM is skipped).

**What must change:** On replan re-entry to RISK FUSION: (a) invalidate PREMORTEM scenarios for changed sub-tasks (set to empty/default -- no PREMORTEM safety net for changed sub-tasks), or (b) mark the reconciled risk with `premortem_data_stale: True` in the APPROVAL briefing, or (c) run a lightweight PREMORTEM on changed sub-tasks only. Option (b) is the cheapest and documents the gap to the user.

**Why Richard missed this:** Richard's audit does not trace data freshness across graph cycles. It checks that fields are defined and referenced, not whether the data at the reference point is actually valid for the current pipeline state.

---

### H3. (Karl) User Scope Change at RESEARCH Interruption Has No Defined Behavior

**Documents in conflict:** IMPLEMENTATION_SPEC + TESTING_SPEC (gap at intersection of three specs)

**Flowchart, Section 6 (S.6, line 580-601):**
The RESEARCH interruption is a PIPELINE INTERRUPT that pauses execution and asks the user for missing information. Three response paths: provide info, "I don't know," "guess."

**Implementation spec, Section D.3 (line 1551-1554, User-intent-change handling):**
> "If detected before APPROVAL: restart the pipeline from CLASSIFY with the new request."
> "If detected during APPROVAL: the ApprovalGate detects divergence >50% [...] It asks: 'Your modifications significantly change the original task. Would you like to start fresh?'"

**Testing spec, Section 3.5 (test_scope_change_during_approval, line 521-541):**
Tests scope change detection ONLY at APPROVAL.

**The gap:** The RESEARCH interruption (S.6) is a user interaction point BEFORE APPROVAL. If the user, when asked for missing information, says "actually, I need something completely different. Instead of a Python script, I need a Kubernetes deployment manifest" -- this changes the Commander's Intent entirely. The flowchart's RESEARCH interruption only defines three response paths (provide info, don't know, guess). None of them handle scope change. The implementation spec D.3 says "if detected before APPROVAL, restart from CLASSIFY" but does not wire this detection into the RESEARCH interruption handler. The testing spec only tests scope change at APPROVAL.

This is the exact emergent-behavior gap described in the assignment brief: "what happens when a user submits feedback mid-pipeline that changes the problem scope -- the interaction of user interrupt + checkpoint/resume + plan revision." It exists at the intersection of RESEARCH (which defines the interrupt), D.3 (which defines scope-change handling), and the testing spec (which only tests one interrupt point).

**What must change:** Add a fourth response path to the RESEARCH interruption handler: "scope change." When the user's response to "I need more information" semantically diverges from the original Commander's Intent by >50% (same threshold as APPROVAL's scope-change detection), route to CLASSIFY restart (per D.3). Add a test for scope change at RESEARCH interruption (distinct from scope change at APPROVAL, which is already tested).

**Why Richard missed this:** Richard's audit framework matches "spec defines X" against "testing tests X." The RESEARCH interruption scope change is a behavior that does NOT have a name in any single spec -- it exists only at the intersection of three specs. None of the documents individually defines it; the gap only becomes visible when you trace the user's possible actions through the complete interaction graph. This requires dialectical analysis, not documentary matching.

---

## MEDIUM PRIORITY FINDINGS

---

### M1. (Karl) PREMORTEM Failure Count for Skill Library -- Only BACKBRIEF Tested

**Category:** HIDDEN COUPLING (one-sided testing)

**Implementation spec, Section 3.5.C (line 242-243):**
> "When a plan seeded from a skill library template is rejected by BACKBRIEF or triggers a fatal PREMORTEM finding, the template's failure_count is incremented and its last_failure_reason is updated in the skill library."

**Testing spec, Section 2.14 (test_skill_library_feedback_loop_replan_exclusion, line 362-382):**
This test: (1) creates a template, (2) seeds a plan, (3) simulates BACKBRIEF rejection, (4) triggers replan, (5) queries library, (6) asserts template is excluded. It tests ONLY the BACKBRIEF rejection path. It does NOT test that PREMORTEM fatal findings also increment failure_count.

**The gap:** The implementation spec says both BACKBRIEF AND PREMORTEM trigger failure_count. The test covers only BACKBRIEF. If the PREMORTEM failure-count code path is broken (e.g., PREMORTEM flags as fatal but the failure_count update is not wired), no test catches it.

**What must change:** Extend `test_skill_library_feedback_loop_replan_exclusion` or create a parallel test for PREMORTEM-triggered failure_count increment. Verify: (1) PREMORTEM fatal flag -> template.failure_count incremented, (2) template excluded from regeneration after PREMORTEM-triggered failure.

---

### M2. (Karl) APPROVAL Diff Briefing on Replan Re-Entry -- Defined but Untested

**Category:** VERIFICATION BLIND SPOT

**Implementation spec, Section 9.5.B (line 732-743):**
> "When APPROVAL is re-entered on a replan cycle, the briefing header shows a diff section: 'Changes since last approval (replan #{n}): New sub-tasks added, Sub-tasks removed, Sub-tasks with changed risk levels, New pre-mortem scenarios, Plan version: {n-1} -> {n}, Reason for replan.'"

**Implementation spec, Section 9.6 (line 766-775):**
Defines `_format_replan_diff()` method on `ApprovalGate`.

**Testing spec:** No test for the diff briefing format. The APPROVAL tests cover: Tier 1/Tier 2 formatting (5.11.1, implicitly), backbrief_forced banner (3.4 combined ceiling test), risk fusion briefing (5.11.1), and scope change detection (3.5). None test replan re-entry with a diff briefing.

**The gap:** A method is defined in the implementation spec (`_format_replan_diff`) with no corresponding test. If the diff formatting has a bug (e.g., returns empty string, shows wrong version numbers, omits pre-mortem scenario changes), no test catches it.

**What must change:** Add `test_approval_replan_diff_briefing` to the APPROVAL test suite. Verify: (1) diff header includes correct replan number, (2) changed sub-tasks are listed with old->new risk levels, (3) version numbers are correct, (4) reason for replan is included.

---

### M3. (Karl) EVALUATE Cache Invalidation on Criteria Change -- Undefined Mechanism

**Category:** IMPLEMENTATION_SPEC internal (implementation detail gap)

**Implementation spec, Section 12.5.B (line 1143):**
> "If the criteria list changed between evaluations (because REPLAN modified the Commander's Intent), the cache is invalidated for that invocation."

**The gap:** The spec says the cache is invalidated when criteria change, but it does not define HOW criteria-change is detected. The cache key is `sha256(output + canonical_json(criteria_list))`. If REPLAN modifies the Commander's Intent's acceptance criteria, the criteria list changes, so the cache key changes, so the cache miss is automatic -- the entry for the old key is never matched. The invalidation mechanism is implicit in the cache key construction, not explicit as a separate check.

**The problem:** The spec describes invalidation as an active action ("the cache is invalidated") when in fact it is passive (key mismatch = cache miss). If a future developer adds a cache lookup that does NOT include criteria in the key (e.g., cached by output hash alone for performance), the invalidation would silently break because the spec only describes the INTENT ("invalidate when criteria change") without the MECHANISM (criteria in the cache key). The testing spec has no test for this because it has no EVALUATE cache test at all.

**What must change:** Clarify in the implementation spec that cache invalidation is achieved by including criteria_list in the cache key, not by an active purge operation. Add `test_evaluate_cache_invalidated_on_criteria_change` to EVALUATE tests.

---

### M4. (Karl) Output Guardrail Safety-Refusal Flag -> SYNTHESIZE -- Promise Not Verified

**Category:** HIDDEN COUPLING (one-node promise to another)

**Implementation spec, Section 2.5.A (point 3, line 157-158):**
> "Safety refusal detection: [...] the response is flagged with `output_guardrail_flagged = True`. Unlike dangerous content, a refusal is passed through to the user [...] but the metadata flag is available for SYNTHESIZE to append an explanatory note."

**Testing spec:** No test verifies that SYNTHESIZE reads `output_guardrail_flagged` and appends an explanatory note. The FAST path SYNTHESIZE is a pass-through (F.7 in the flowchart). The implementation spec says the flag is "available" -- a promise that some future consumer will use it. But the consumer (SYNTHESIZE) has no defined behavior for this flag.

**The gap:** The implementation spec makes a cross-node promise (FAST EXECUTE sets a flag that SYNTHESIZE consumes) but neither specifies the consumption in SYNTHESIZE's interface NOR tests the consumption. If built as specified, the flag is set but never read -- a dead data path.

**What must change:** Either (a) add `output_guardrail_flagged: bool` to SYNTHESIZE's input and define the behavior ("when True, append: 'Note: the model declined to answer this question in its original response.'"), with a corresponding test, or (b) acknowledge the flag is for Wave 3 auditing and remove the "available for SYNTHESIZE" language.

---

### M5. (Karl) Denylist Hot-Reload with Bad Pattern Rejection -- Untested

**Category:** VERIFICATION BLIND SPOT

**Implementation spec, Section 1.5.B (line 97-99):**
> "The `DenylistConfig` object watches its configuration file for changes. When a change is detected, new patterns are compiled and atomically swapped with the old list. If any pattern in the updated list fails to compile, the entire update is rejected and the old list is retained."

**Testing spec:** No test for hot-reload, atomic swap, or bad pattern rejection. The CLASSIFY unit tests (Section 2.1) test denylist behavior with fixed patterns but do not test pattern reload or compilation failure.

**The gap:** The hot-reload mechanism is a production reliability feature with a specific invariant (bad pattern = entire update rejected). If the bad-pattern rejection is buggy (e.g., partially updates the list before the compilation failure is detected), the denylist could silently lose patterns or gain a corrupt one. This is untested.

**What must change:** Add `test_denylist_hot_reload_rejects_bad_patterns` to CLASSIFY unit tests. Verify: (1) good patterns update atomically, (2) a bad pattern rejects the entire update, (3) the old list is preserved, (4) concurrent invocations see consistent state throughout.

---

### M6. (Karl) DEEP Path + FRAGO Replan Interaction -- Multi-COA Re-Selection Never Considered

**Category:** EMERGENT BEHAVIOR GAP (intersection of DEEP + REPLAN)

**Flowchart (DEEP Path):** DEEP generates multiple COAs and selects the best.

**Implementation spec (Section 13, REPLAN):** REPLAN generates a delta against the current plan. No multi-COA logic.

**The gap:** If a DEEP path task enters the FRAGO replan loop, REPLAN produces a delta against the SELECTED COA. If the delta degrades the selected COA (makes it worse than one of the ALTERNATIVE COAs that were rejected at initial planning), the system blindly continues modifying the selected COA. It never reconsiders whether a different COA would now be better. This is reasonable for small deltas (1-3 sub-task changes) but could be suboptimal for larger deltas.

**Severity:** Medium. This is an optimization gap, not a correctness gap. But it should be documented as a known limitation in the REPLAN specification.

**What must change:** Add to implementation spec Section 13.1: "REPLAN operates on the currently selected plan/COA. It does not re-evaluate alternative COAs from multi-COA planning. This is a known limitation. If a delta is large enough to meaningfully change the COA's characteristics, the degrading replan detection (13.5.C) will escalate to human, who can request a fresh multi-COA regeneration."

---

### M7. (Karl) FRAGO Replan + Runtime Branching Halt + Active Compensation Ladder -- Undefined Interaction

**Category:** EMERGENT BEHAVIOR GAP (intersection of three mechanisms)

**Implementation spec, Section 8.5.C (Runtime monitor behavior on replan, line 641-642):**
> "When the runtime monitor halts execution mid-flow (during EXECUTE), it triggers an immediate transition to REPLAN. The REPLAN node receives the halted state, including which sub-tasks were in progress and which had spawned excessive sub-tasks."

**Implementation spec, Section 10.5.A (Compensation ladder, line 894-901):**
The compensation ladder is active on individual sub-tasks during EXECUTE. Handlers escalate monotonically.

**The gap:** If the runtime branching monitor triggers REPLAN while sub-task X is mid-compensation (e.g., at compensation level 3, "local_compensation"), what happens to sub-task X's compensation state? Is it checkpointed so REPLAN can resume from the compensation context? Is it aborted and restarted from scratch? Is the compensation level reset to 0 for the replanned sub-task?

The implementation spec says "REPLAN node receives the halted state, including which sub-tasks were in progress" but does not specify whether the compensation level is part of that state or whether it persists across the REPLAN boundary.

**What must change:** Add to implementation spec Section 8.5.C or 13.5: "If a sub-task was mid-compensation (compensation_level > 0) when the runtime branching monitor triggered REPLAN, the sub-task's compensation_level is checkpointed and carried forward. On re-execution, the sub-task resumes from its checkpointed compensation_level (not from 0). If the replanned delta removes or replaces this sub-task, the compensation state is discarded."

---

### M8. (Karl) PREMORTEM -> APPROVAL via plan_checksum -- Retrieval Contract Untested

**Category:** HIDDEN COUPLING

**Implementation spec, Section 7.5.A (Plan-versioned scenario storage, line 537-538):**
> "PREMORTEM stores `failure_scenarios` keyed by `plan_checksum`."

**Implementation spec, Section 9.5.A (Tier 2 details, line 726):**
APPROVAL's Tier 2 detail includes "Per sub-task breakdown, pre-mortem scenarios (if any)."

**The gap:** APPROVAL reads PREMORTEM's scenarios, implicitly keyed by the current plan's `plan_checksum`. If there is any mismatch between the checksum PREMORTEM stored under and the checksum APPROVAL reads under (e.g., a SHA-256 hash bug, PLAN regeneration that didn't propagate the checksum, or a graph state bug that carries forward a stale checksum), APPROVAL silently shows no pre-mortem scenarios. This is a silent failure -- the user sees a briefing missing critical safety information, with no indication that anything went wrong.

**What must change:** Add a cross-check in APPROVAL: if `plan_checksum` is present but PREMORTEM has no scenarios for this checksum, log a warning and display "Pre-mortem scenarios unavailable for this plan version" in the briefing. Add a test: `test_approval_premortem_scenario_retrieval_by_checksum` that verifies APPROVAL correctly retrieves scenarios keyed by checksum and handles checksum mismatch.

---

## LOW PRIORITY FINDINGS

---

### L1. (Karl) "Pipeline Halt" Has Three Different Meanings Across Documents

**Category:** TERMINOLOGY DRIFT

| Document | Term | Refers To |
|----------|------|-----------|
| Implementation spec 9.5.C | "pipeline halt" renamed to "mandatory human approval" | APPROVAL pause waiting for user |
| Flowchart S.12 | "HALT -> escalate to REPLAN" | BRANCHING violation routes to replan |
| Flowchart S.16a | "HALT -> escalate to REPLAN" | Runtime branch monitor triggers replan |
| Flowchart Ceiling table | "Structural halt (escalate to REPLAN)" | DAG depth / branching factor violations |
| Flowchart Escalation Path Map | "ANY PATH - - - -> USER ESCALATION" | Compensation ladder / ceiling exhausted |

The word "halt" is used for three different graph transitions: (1) APPROVAL pause-waiting-for-user, (2) REPLAN routing after branching/depth violation, and (3) USER ESCALATION after ceiling exhaustion. The implementation spec addresses this partially by renaming case (1) to "mandatory human approval," but the flowchart uses "HALT" for case (2) and "ESCALATE" for case (3). A developer implementing graph routing from the flowchart could confuse "HALT" (go to REPLAN) with "HALT" (stop and wait for user) with "HALT" (everything exhausted, escalate permanently).

**Richard's L1 and L2** cover naming inconsistencies (premortem vs pre-mortem, TRIVIAL vs FAST). He missed this semantic overload of "halt."

**What must change:** Standardize: "REPLAN-ROUTE" for branching violations, "APPROVAL-PAUSE" for mandatory human approval, "USER-ESCALATE" for ceiling exhaustion. Update flowchart node labels accordingly.

---

### L2. (Karl) Flowchart Missing PREMORTEM All-LLM-Fail Exception

**Category:** FLOWCHART vs IMPLEMENTATION_SPEC

**Implementation spec, Section 7.1 (line 512-513):**
> "Exception: if ALL persona LLM calls fail (not just some), PREMORTEM cannot produce scenarios and is force-passed with a critical log alert."

**Flowchart:** The PREMORTEM flowchart section (S.8-S.10) and the ceiling table describe only the cycle-ceiling force-pass condition. The ALL-LLM-fail exception is not represented anywhere in the flowchart. A non-technical stakeholder reading the flowchart would believe PREMORTEM always produces scenarios until the cycle ceiling is hit. They would not know about the system-health failure condition.

**Richard's H2** identified this as a testing gap (no test). I am identifying it as a separate issue: the flowchart's behavioral description is incomplete. The flowchart is the user-facing document; it should describe the ALL-fail force-pass so users understand why a plan might reach APPROVAL without pre-mortem scenarios despite being on cycle 1.

**What must change:** Add to the flowchart (S.8): "Exception: if ALL personas fail (a system-health event, not a plan quality issue), PREMORTEM force-passes immediately with a critical internal alert. This is different from hitting the ceiling -- it means the personas couldn't run at all."

---

### L3. (Karl) "briefing" vs "structured briefing" vs "approval briefing" vs "Tier 1/Tier 2"

**Category:** TERMINOLOGY DRIFT (minor)

The implementation spec uses "structured briefing" (9.5.A), "approval briefing" (9.5.A), "Tier 1 summary" / "Tier 2 detail" (9.5.A), and "briefing" throughout. The flowchart uses "briefing" and "Tier 1/Tier 2" consistently. The testing spec uses "briefing_summary" and "briefing_detail." Not a contradiction, but four terms for one concept across 2500+ lines of spec.

---

### L4. (Karl) Flowchart Ceiling Table Lists PREMORTEM Ceiling as "2", Implementation Spec Says "Max 2"

**Category:** NAMING INCONSISTENCY (Richard flagged L1 for hyphen, this is a different issue)

**Flowchart Ceiling table (line 887):**
> "Pre-mortem cycles -- 2"

**Implementation spec, Section 7.1 (line 512):**
> "Max 2 pre-mortem cycles."

"Cycles" in the ceiling table could be read as "2 cycles plus the initial run = 3 total invocations" or "2 invocations total (initial + 1 cycle)." The implementation spec clarifies "backbrief_revision_count >= 2" (count starts at 0, so 2 means 2 revisions after initial, or 3 total if initial counts as 0). The ceiling table's bare "2" is ambiguous without knowing whether it's zero-indexed or one-indexed.

**What must change:** Add "(zero-indexed: initial run = count 0, max 2 revisions)" to the ceiling table for clarity.

---

## Summary Table

| ID | Finding | Documents | Type | Priority | Richard? |
|----|---------|-----------|------|----------|----------|
| BB1 | DEEP always-show APPROVAL has no mechanism | FLOW vs IMPL | CONTRADICTION | BUILD-BREAKING | MISSED |
| BB2 | DEEP multi-COA has no data model | FLOW vs IMPL | CONTRADICTION | BUILD-BREAKING | MISSED |
| BB3 | DEEP MAKER decomposition has no mechanism | FLOW vs IMPL | CONTRADICTION | BUILD-BREAKING | MISSED |
| BB4 | DEEP sequential execution has no mechanism | FLOW vs IMPL | CONTRADICTION | BUILD-BREAKING | MISSED |
| BB5 | Risk fusion rule 4 (halt_flag) is dead code | IMPL vs FLOW | CONTRADICTION | BUILD-BREAKING | MISSED |
| BB6 | Persona count: 4 vs 5 | IMPL vs FLOW vs TEST | CONTRADICTION | BUILD-BREAKING | MISSED |
| H1 | PREMORTEM ALL-fail vs cycle-ceiling interaction undefined | IMPL internal | AMBIGUITY | HIGH | PARTIAL (H2) |
| H2 | FRAGO replan risk fusion uses stale PREMORTEM data | IMPL internal | HIDDEN COUPLING | HIGH | MISSED |
| H3 | User scope change at RESEARCH interruption not defined | IMPL+TEST (intersection) | EMERGENT GAP | HIGH | MISSED |
| M1 | PREMORTEM skill library failure count untested | IMPL vs TEST | HIDDEN COUPLING | MEDIUM | MISSED |
| M2 | APPROVAL replan diff briefing untested | IMPL vs TEST | VERIFICATION BLIND SPOT | MEDIUM | MISSED |
| M3 | EVALUATE cache invalidation mechanism undefined | IMPL internal | SPEC GAP | MEDIUM | MISSED |
| M4 | Output guardrail -> SYNTHESIZE promise unverified | IMPL vs TEST | HIDDEN COUPLING | MEDIUM | MISSED |
| M5 | Denylist hot-reload bad pattern rejection untested | IMPL vs TEST | VERIFICATION BLIND SPOT | MEDIUM | MISSED |
| M6 | DEEP + FRAGO replan COA re-selection gap | IMPL+FLOW (intersection) | EMERGENT GAP | MEDIUM | MISSED |
| M7 | Runtime branching halt + active compensation ladder interaction | IMPL internal (intersection) | EMERGENT GAP | MEDIUM | MISSED |
| M8 | PREMORTEM -> APPROVAL checksum retrieval contract untested | IMPL vs TEST | HIDDEN COUPLING | MEDIUM | MISSED |
| L1 | "Halt" means three different things | ALL | TERMINOLOGY DRIFT | LOW | MISSED |
| L2 | Flowchart missing PREMORTEM ALL-fail exception | FLOW vs IMPL | OMISSION | LOW | MISSED |
| L3 | Multiple terms for "briefing" | ALL | TERMINOLOGY DRIFT | LOW | MISSED |
| L4 | Ceiling table "2" ambiguous (zero vs one-indexed) | FLOW vs IMPL | NAMING | LOW | MISSED |

---

## Why Richard's Audit Missed These Categories

Richard's audit framework is a **documentary matching framework**. For each finding, it asks:

1. Does the implementation spec define a behavior X? Does the testing spec test X? (GAP)
2. Does the testing spec reference a field Y? Does the implementation spec define Y? (CONFLICT)
3. Does the flowchart use term Z where the implementation spec uses term W? (NAMING)

This framework catches: missing tests, undefined fields, and naming inconsistencies. It covers 14 of 20 findings at MEDIUM+ priority in his own audit.

What it DOES NOT catch, and what my 6 BUILD-BREAKING and 3 HIGH findings demonstrate:

1. **Flowchart-as-ground-truth validation.** Richard treats the implementation spec as authoritative and the flowchart as a derivative work. He never asks "does the implementation spec actually implement the behavior the flowchart claims?" This misses BB1-BB4 entirely.

2. **Graph topology liveness analysis.** Richard does not trace whether every state described in node specifications is actually reachable given the graph routing. This misses BB5.

3. **Cross-document cardinality.** Richard doesn't count things across documents (personas: 4 vs 5). This misses BB6.

4. **Temporal data freshness.** Richard doesn't check whether data consumed downstream is still valid after graph cycles (e.g., stale PREMORTEM data in risk fusion on replan). This misses H2.

5. **Intersection behavior.** Richard looks for behaviors defined in ONE document and tested or not tested. He does not look for behaviors that emerge from the INTERSECTION of multiple specs -- behaviors that no single document defines but that the combined spec system implies. This misses H3, M6, M7.

6. **Interaction of concurrent mechanisms.** Richard treats each mechanism in isolation (compensation ladder, branching monitor, replan). He does not analyze what happens when they fire simultaneously. This misses M7.

7. **Semantic overload.** Richard catches naming inconsistencies (hyphens, labels) but misses when the same word means fundamentally different things in different contexts ("halt"). This misses L1.

The dialectical question -- "do these three documents form a coherent whole, or do they contain contradictions that will surface during implementation?" -- requires more than matching. It requires tracing the graph topology, verifying data freshness across cycles, counting entities across documents, and analyzing the intersection of multiple mechanisms.

The most damaging category is the DEEP path specification gap (BB1-BB4). The flowchart describes a rich DEEP path with four additional features (multi-COA, MAKER decomposition, sequential execution, always-active approval), but the implementation spec provides mechanisms for NONE of them. If an engineer builds JORDAN v2 from the implementation spec alone, the DEEP path is indistinguishable from STANDARD with more risk checks. This is not a missing test -- it is a missing implementation. No amount of testing will surface it, because there is nothing to test.

---

## Correctness Guidance

The implementation spec, the flowchart, and the testing spec must be brought into coherence. For each contradiction, the resolution path:

**BB1-BB4 (DEEP path features):** The flowchart describes features the implementation spec does not implement. Two options: (A) Add DEEP-specific mechanisms to the implementation spec (multi-COA Planning, MAKER decomposition, sequential execution mode, force-approval routing). This is significant new implementation work. (B) Acknowledge these as Wave 3 features, remove from the v2 flowchart, and document the DEEP path for v2 as "STANDARD pipeline with expanded personas, always-on approval, and default-sequential execution." Option B is more honest for the current spec state.

**BB5 (dead code in risk fusion):** Remove rule 4 and the 9.10.6 edge case for branching monitor halt_flag. Branching violations are handled at the graph level.

**BB6 (persona count):** Standardize on 4 personas. Update testing spec 5.11.2.

**H1-H3:** Add specification text and tests for the undefined interactions.

**M1-M8:** Add tests for the untested coupling and verification blind spots.

**L1-L4:** Standardize terminology. Add the ALL-fail exception to the flowchart.

---

*End of Karl's Cross-Document Consistency Audit*
