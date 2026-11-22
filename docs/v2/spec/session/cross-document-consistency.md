# Cross-Document Consistency Audit -- JORDAN v2 Final Spec

**Auditor:** Richard the Lionheart
**Date:** 2026-05-25
**Scope:** richard-revision-01.md (implementation), karl-revision-02.md (flowchart), richard-revision-03.md (testing)

---

## Summary

| Priority | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH     | 7    |
| MEDIUM   | 9    |
| LOW      | 3    |
| **Total** | **20** |

---

## CRITICAL

### C1. Monotonic Compensation Escalation -- No Unit Test

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Implementation spec, Section 10.5.A (p. 894, Edge case -- Cascade prevention):**
> "The compensation handler ladder has an invariant: **a handler can only escalate UP, never sideways or down.** Specifically: `reprompt` can escalate to `catch_fallback`, `local_compensation`, etc., but cannot trigger ANOTHER `reprompt`. `catch_fallback` that fails escalates directly to `local_compensation`, not back to `reprompt`."

**Implementation spec, Section 10.9 (p. 1024, Integration risk):**
> "Second-hardest: **compensation handler cascade prevention** -- the monotonic escalation invariant (section 10.5.A) must be enforced programmatically, not just documented. **A unit test should verify that no handler can invoke a handler of the same or lower level.** "

**Testing spec:** No such unit test exists. Section 2 (Unit Tests) for EXECUTE is claimed "adequate as specified" (Section 2.3-2.12), but the implementation spec explicitly calls for this test. None of the NEW tests in the testing spec cover monotonic escalation.

**Verdict:** The implementation spec mandates a unit test; the testing spec does not provide one. This is the clearest inconsistency in the three documents.

**Action:** Add `test_execute_compensation_monotonic_escalation` to Section 2 (FAST EXECUTE or EXECUTE unit tests). The test should verify that each compensation handler, when it fails, transitions to the NEXT level in the ladder (never the same level, never a lower level).

---

## HIGH

### H1. Persona Calibration Auto-Disable -- No Test

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Implementation spec, Section 7.5.C (p. 542-547, Edge case -- Persona calibration tracking):**
> "If a persona's false-positive rate exceeds `max_false_positive_rate` (configurable, default 0.3), the persona is flagged for review. If it exceeds `max_false_positive_critical` (0.5), the persona is **disabled** until reviewed."
> "At pipeline startup, persona calibration data is loaded. Personas with `disabled = True` are skipped."

**Flowchart, Safety Features -- Pre-Mortem (p. 168, 2nd paragraph):**
> "There are two thresholds: **30% false-alarm rate:** The persona is flagged for review. **50% false-alarm rate:** The persona is disabled until reviewed."

**Testing spec, Section 2.3-2.12 (p. 242):**
> "Unit tests for PLAN, BACKBRIEF, RESEARCH, RISK ASSESSMENT, PREMORTEM, BRANCHING MONITOR, APPROVAL GATE, EXECUTE, SYNTHESIZE, and EVALUATE are adequate as specified."

No new test was added for persona calibration disabling. The flowchart and implementation spec agree on the behavior; the testing spec does not test it.

**Verdict:** Implementation and flowchart agree. Testing spec is missing a test for a defined behavioral invariant (auto-disable at 50%).

**Action:** Add `test_premortem_persona_calibration_disables_at_50_percent` to PREMORTEM unit tests. Verify that a persona with FP rate crossing 0.5 is excluded from subsequent analysis.

---

### H2. PREMORTEM Force-Pass on All-Persona-Failure -- No Test

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Implementation spec, Section 7.1 (p. 511):**
> "**Exception: if ALL persona LLM calls fail (not just some), PREMORTEM cannot produce scenarios and is force-passed with a critical log alert.** This is a system-health failure, not an advisory opt-out."

**Flowchart:** Does not explicitly mention this exception. The ceiling table says "Pre-mortem cycles -- 2 -- Force-pass; flag unresolved scenarios in approval," which describes the standard ceiling behavior, not the all-persona-failure exception.

**Testing spec:** No test for this edge case.

**Verdict:** Implementation spec defines a distinct force-pass condition (all personas fail). Neither the flowchart nor the testing spec covers it.

**Action:** Add `test_premortem_force_pass_all_personas_fail` to PREMORTEM unit tests. Mock all three (or five) persona calls to raise exceptions; verify PREMORTEM force-passes with `critical_log_alert = True`.

---

### H3. Runtime Branching Monitor -- Not Tested

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Implementation spec, Section 8.1 (p. 588-594):**
> **"Two-component design:**
> 1. **Static DAG analyzer (pre-execution):** Computes branching factor from the plan's DAG before execution. [...] Runs before APPROVAL (unchanged position in topology).
> 2. **True runtime sub-task spawn monitor (during execution): NEW component.** Tracks dynamic sub-task spawning during EXECUTE. If a sub-task dynamically spawns new sub-tasks [...], the runtime monitor detects this and can halt execution mid-flow."

**Implementation spec, Section 8.5.C (p. 641, Edge case -- Runtime monitor behavior on replan):**
> "When the runtime monitor halts execution mid-flow (during EXECUTE), it triggers an immediate transition to REPLAN."

**Testing spec, Section 5.4 (p. 677):**
> "| 5.4 | Branching Factor Halt | RETAINED | Unchanged |"

The testing spec retains the branching test unchanged from the original draft. The runtime monitor is a NEW component. If the original test was written for the static analyzer only, the new runtime behavior is untested.

**Verdict:** New runtime component (implementation spec) has no corresponding new test in the testing spec.

**Action:** Add `test_branching_runtime_spawn_monitor_halts` to Section 5.4 or as a new Section 5.4a. Verify that dynamic sub-task spawning exceeding `original * 2` triggers a halt to REPLAN.

---

### H4. UNEQUIVALENT Evaluation Status -- No Test

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Implementation spec, Section 12.5.C (p. 1147, Edge case -- No criteria = unevaluable):**
> "If the Commander's Intent has no acceptance criteria (`acceptance_criteria: []` or `None`), EVALUATE returns `evaluation_result = 'UNEQUIVALENT'` (new enum value)."
> "The pipeline still proceeds (UNEQUIVALENT is treated like SUCCESS for routing -- it does not trigger replan), but the output is annotated."

**Flowchart, Section 6 (S.19, p. 752-763):**
> "UNEQUIVALENT -- routed like SUCCESS -- no criteria to fail against, so no replan triggered. Output annotated: 'quality unconfirmed'."

**Testing spec, Section 2.3-2.12 (p. 242):**
> "[KARL-ADOPT: CONFIRMED] Unit tests for [...] EVALUATE [...] are adequate as specified."

No new test added for UNEQUIVALENT. The implementation spec adds UNEQUIVALENT as a new enum value with distinct routing behavior. The testing spec claims EVALUATE tests are adequate but does not test the new status.

**Verdict:** New behavioral invariant (UNEQUIVALENT) untested.

**Action:** Add `test_evaluate_no_criteria_returns_unequivalent` to EVALUATE unit tests. Verify: (1) empty criteria list returns UNEQUIVALENT, (2) UNEQUIVALENT routes like SUCCESS (no replan), (3) output is annotated with quality disclaimer.

---

### H5. `skill_template_sanitized` Field -- Does Not Exist in Implementation Spec

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Implementation spec:** Does not define a `skill_template_sanitized` field anywhere. ADversarial test `test_adversarial_template_prompt_injection` in the testing spec references it.

**Testing spec, Section 5.9.1 (p. 858):**
> ```python
> assert result.plan_source != "skill_template" or result.skill_template_sanitized == True
> ```

The test expects a boolean field `skill_template_sanitized` to exist on the pipeline result when a skill template is used. The implementation spec defines `plan_source: Literal["fresh", "skill_template", "backbrief_revision", "premortem_revision"]` (Section 3.4) and describes template sanitization in speculative terms (adversarial test description mentions "Option A: template description was sanitized"), but no field `skill_template_sanitized` is specified in any node's output schema.

**Verdict:** Testing spec asserts a field that the implementation spec does not define. A developer following the implementation spec would not produce code that sets this field, so the test would fail (or the field would not exist).

**Action:** Either add `skill_template_sanitized: bool` to the PLAN output schema (or equivalent) in the implementation spec, or change the test to not require this field.

---

### H6. `scope_change_message` -- Not Defined in Implementation Spec

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Implementation spec, Section D.3 (p. 1552-1554, User-intent-change handling):**
Describes the APPROVAL gate asking the user about scope changes, but does not define a `scope_change_message` field or method return value on the ApprovalGate.

**Testing spec, Section 3.5 (p. 535):**
> ```python
> assert "significantly changes" in gate.scope_change_message.lower()
> ```

The test accesses `gate.scope_change_message` but the implementation spec does not define this property on the ApprovalGate class (Section 9.6).

**Verdict:** Testing spec references an undefined interface member.

**Action:** Add `scope_change_message: str` property to the `ApprovalGate` class in the implementation spec (Section 9.6), or adjust the test to check the formatted briefing string instead.

---

### H7. `has_unaddressed_safety_flags` -- Not Defined in Implementation Spec

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Testing spec, Section 5.8 (p. 804, Chain 3: Approval Timeout -> Audit):**
> ```python
> assert result.audit_trail.has_unaddressed_safety_flags == True
> ```

**Implementation spec, Section D.5 (Observability architecture):**
Defines audit trail metrics and tracing but does not define a `has_unaddressed_safety_flags` field on the audit trail structure.

**Verdict:** Testing spec asserts a field the implementation spec does not specify.

**Action:** Add `has_unaddressed_safety_flags: bool` to the audit trail data model in the implementation spec (Section D.5 or a new subsection). Define the condition under which this flag is set (PREMORTEM flags exist but were overridden by force-pass or timeout).

---

## MEDIUM

### M1. Denylist False-Positive Feedback Loop -- No Test

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Implementation spec, Section 1.5.A (p. 94-96, Edge case -- Denylist false-positive feedback loop):**
> "When the denylist triggers and the pipeline subsequently completes successfully [...] the CLASSIFY node appends `triggered_pattern`, `input_excerpt`, and `pipeline_outcome = SUCCESS` to a `denylist_false_positive_log` table in the skill library."
> "High-frequency false-positive patterns (triggered >5 times with SUCCESS outcome) are automatically flagged for denylist removal."

**Testing spec, Section 2.1:**
Has `test_classify_denylist_false_negative_llm_catches` (denylist FN, LLM catches) and `test_classify_both_fail_conservative_escalation` (both miss). Does NOT have a test for the false-positive feedback loop where the denylist triggers correctly and false-positive is logged.

**Verdict:** Defined behavior, not tested.

---

### M2. Scope Change Detection in CLASSIFY -- No Test

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Implementation spec, Section B.3 (p. 1494, Per-session scope change detection):**
> "Added a mechanism in CLASSIFY that compares the current `user_message` against the conversation history (`chat_history`). If the estimated scope [...] has expanded by >50% compared to the initial request in the session, a `scope_change_detected` flag is set."

**Testing spec, Section 3.5 (p. 521-541):**
Tests scope change detection during APPROVAL (user modifies plan mid-approval). Does NOT test scope change detection in CLASSIFY (comparing current message against conversation history).

**Verdict:** These are two different scope-change mechanisms. The CLASSIFY mechanism (implementation spec B.3) is untested.

---

### M3. Cross-Tenant Isolation -- Not Tested

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Implementation spec, Section 14.5.D (p. 1392, Tenant filtering on template queries):**
> "All template queries include `WHERE tenant_id = ?` or `WHERE tenant_id IS NULL` (global templates). Cross-tenant template sharing is OFF by default for Wave 2."

**Implementation spec, Section 14.5.D (p. 1392):**
> "Tenant-specific templates are never visible to other tenants. This prevents cross-tenant information leakage."

**Testing spec, Section 2.14:**
`test_skill_library_cross_user_isolation_within_tenant` tests that User A and User B (same tenant) share failure counts. Does NOT test cross-tenant isolation (User A in `tenant_1` cannot see User B's templates in `tenant_2`).

**Verdict:** Half the isolation invariant is tested (within-tenant sharing); the other half (cross-tenant blocking) is not.

---

### M4. Stale Template Handling -- No Test

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Implementation spec, Section 14.5.C (p. 1387-1389, Template staleness check on retrieval):**
> "For each `tools_required` in the template's sub-tasks, verify the tool exists in the current tool registry. If any tool is deprecated or removed, the template is flagged as `stale = True`."
> "Stale templates are returned only if NO non-stale template matches the query."

**Testing spec, Section 2.14:**
No test for stale template handling (tool deprecation detection, filter logic, fallback behavior).

---

### M5. Compensation/Replan Counter Interaction -- No Test

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Implementation spec, Section 13.5.B (p. 1253-1268, Compensation ladder escalation counts vs. FRAGO replan counts):**
> "A single REPLAN invocation can attempt up to 6 different compensation strategies within its 1/3 replan budget."
> "The worst case is 3 replans * 6 compensation levels = 18 total compensation attempts before human escalation."

**Testing spec:**
No test verifying that 6 compensations within 1 replan do NOT consume additional replan budget, or that the counter interaction is correctly bounded.

---

### M6. `backbrief_forced` Consumers (APPROVAL, EVALUATE, AUDIT) -- Not Tested

**Category:** IMPLEMENTATION_SPEC vs TESTING_SPEC

**Implementation spec, Section 4.5.A (p. 304-310, Edge case -- backbrief_forced flag consumers):**
Defines four consumers:
1. APPROVAL GATE -- banner
2. PREMORTEM -- extra persona context
3. EVALUATE -- note about unresolved issues
4. AUDIT TRAIL -- recorded

**Testing spec, Section 5.11.3:**
`test_iv_backbrief_force_pass_changes_premortem` tests only the PREMORTEM consumer. The APPROVAL banner, EVALUATE note, and AUDIT TRAIL consumers are untested.

---

### M7. Resource Analyst Persona -- Flowchart Self-Contradiction

**Category:** FLOWCHART vs IMPLEMENTATION_SPEC (also FLOWCHART internal)

**Flowchart, Safety Features -- Pre-Mortem (p. 163, personas list):**
> "- **Resource Analyst (always available, required on DEEP path):** 'Here are the memory, storage, API, and timeout constraints that will kill this plan.'"

The bullet list placement implies Resource Analyst is a standard persona alongside Pessimist, Optimist, and Devil's Advocate (in the general pre-mortem description, not in the DEEP section).

**Flowchart, DEEP Path Detail (D.2, p. 855-863):**
> "Standard personas active (same as STANDARD path): Pessimist, Optimist, Devil's Advocate. Added for DEEP path: Resource Analyst."

D.2 clearly states Resource Analyst is added ONLY for DEEP path -- contradicting the "always available" implication in the safety features section.

**Implementation spec, Section C.3 (p. 1506):**
> "PREMORTEM's persona set now includes a 'Resource Analyst' persona (added to the standard set for DEEP path, **available** for STANDARD path)."

The implementation spec splits the difference: "available" for STANDARD (optional), "added to the standard set" for DEEP (default). The flowchart's safety section says "always available" (consistent with impl spec's "available"), but D.2 says "Added for DEEP path" (consistent with impl spec's "added to the standard set for DEEP"). The inconsistency is in the flowchart's tone: the safety section implies active-by-default, D.2 says DEEP-only.

**Verdict:** The flowchart contradicts itself. The implementation spec resolves it (available optionally for STANDARD, default for DEEP). The flowchart's D.2 should say "Added to the standard persona set for DEEP; available for STANDARD on request."

---

### M8. Denylist False-Positive Logging -- CLASSIFY vs. SKILL LIBRARY Target

**Category:** IMPLEMENTATION_SPEC internal (carried into testing gap)

**Implementation spec, Section 1.5.A (p. 95):**
> "the CLASSIFY node appends `triggered_pattern`, `input_excerpt`, and `pipeline_outcome = SUCCESS` to a `denylist_false_positive_log` table **in the skill library**."

This means the denylist false-positive log lives in the skill library database. The testing spec's skill library tests (Section 2.14) do not include a test for this log table being populated correctly. Testing spec also has no CLASSIFY test for denylist false-positive recording.

---

### M9. Novel Hallucination Format Test -- Only Covers Guardrail, Not Downstream

**Category:** FLOWCHART vs TESTING_SPEC

**Flowchart, FAST Path (F.3a, F.5, F.7, F.8):**
When tool hallucination is detected: replace with safe fallback -> SYNTHESIZE (pass-through) -> EVALUATE (always SUCCESS). The safe fallback message replaces the output.

**Testing spec, Section 2.2 (test_fast_execute_novel_hallucination_format_caught, p. 206-237):**
Tests that the guardrail `scan()` method detects novel formats. Does NOT test the full flow: that the safe fallback reaches SYNTHESIZE and that SYNTHESIZE's pass-through handles it correctly, and EVALUATE returns SUCCESS on the fallback.

The test is a unit test on `guardrail.scan()`, not an integration test of the full FAST path after interception.

---

## LOW

### L1. Flowchart Uses "Pre-mortem cycles" (Hyphenated); Implementation Uses "premortem" (No Hyphen)

**Category:** NAMING INCONSISTENCY

**Flowchart, Ceiling/Limit Summary table (p. 882-894):**
> "Pre-mortem cycles -- 2 -- Force-pass; flag unresolved scenarios in approval"

**Implementation spec:**
Consistently uses "PREMORTEM" / "premortem" without hyphen throughout (Sections 7.1, 7.5, etc.).

**Flowchart elsewhere:**
Uses "Pre-Mortem" in the Safety Features heading, "pre-mortem" in body text, and "PREMORTEM" in S.8-S.10 node labels. Inconsistent within the flowchart itself.

---

### L2. Flowchart Uses TRIVIAL/MODERATE/COMPLEX Labels; Implementation Spec Does Not

**Category:** NAMING INCONSISTENCY

**Flowchart, CLASSIFY node (p. 441-452):**
> "LLM classifier: TRIVIAL / MODERATE / COMPLEX"
> "{ 2. WHICH PATH? } / TRIVIAL -> FAST PATH / MODERATE -> STANDARD PATH / COMPLEX -> DEEP PATH"

**Implementation spec, Section 1.1 (p. 80):**
> "Performs TAPE-inspired triage at pipeline entry to determine which of three execution paths (FAST, STANDARD, DEEP) the incoming request follows."

The implementation spec describes the output as a path (FAST/STANDARD/DEEP), not a complexity label (TRIVIAL/MODERATE/COMPLEX). The flowchart adds an intermediate label abstraction layer that the implementation spec does not use. A developer reading only the implementation spec would not know about TRIVIAL/MODERATE/COMPLEX labels.

**Verdict:** Minor. The flowchart simplifies for its audience. But the mapping between labels and paths could cause confusion if someone treats the labels as state fields.

---

### L3. Flowchart Does Not Describe Delta-Aware BACKBRIEF Re-Verification

**Category:** IMPLEMENTATION_SPEC vs FLOWCHART

**Implementation spec, Section 4.5.B (p. 312-318, Edge case -- Delta-aware re-verification):**
> "When BACKBRIEF re-runs on a revised plan (regeneration), it does NOT re-verify the entire plan from scratch. [...] Compute the diff between old `plan_checksum` and new `plan_checksum`. Only re-check DAG portions that changed."

**Flowchart, S.2-S.3 (p. 543-572):**
Shows BACKBRIEF running and branching on "Structure valid?" but does not distinguish between full verification and delta re-verification.

**Verdict:** Acceptable simplification for the flowchart's audience. Not a contradiction.

---

## Cross-Reference Summary

| Finding | IMPL vs FLOW | IMPL vs TEST | FLOW vs TEST | Priority |
|---------|-------------|--------------|-------------|----------|
| C1: Monotonic escalation test | -- | CONFLICT | -- | CRITICAL |
| H1: Persona calibration test | -- | GAP | -- | HIGH |
| H2: All-personas-fail test | -- | GAP | -- | HIGH |
| H3: Runtime branching test | -- | GAP | -- | HIGH |
| H4: UNEQUIVALENT test | -- | GAP | -- | HIGH |
| H5: skill_template_sanitized field | -- | CONFLICT | -- | HIGH |
| H6: scope_change_message field | -- | CONFLICT | -- | HIGH |
| H7: has_unaddressed_safety_flags field | -- | CONFLICT | -- | HIGH |
| M1: Denylist FP log test | -- | GAP | -- | MEDIUM |
| M2: CLASSIFY scope change test | -- | GAP | -- | MEDIUM |
| M3: Cross-tenant isolation test | -- | GAP | -- | MEDIUM |
| M4: Stale template test | -- | GAP | -- | MEDIUM |
| M5: Counter interaction test | -- | GAP | -- | MEDIUM |
| M6: backbrief_forced consumer tests | -- | GAP | -- | MEDIUM |
| M7: Resource Analyst role | AMBIGUOUS | -- | AMBIGUOUS | MEDIUM |
| M8: Denylist FP log target | -- | GAP | -- | MEDIUM |
| M9: Hallucination integration test | -- | GAP | -- | MEDIUM |
| L1: "premortem" vs "pre-mortem" | NAMING | -- | NAMING | LOW |
| L2: TRIVIAL/MODERATE labels | NAMING | -- | -- | LOW |
| L3: Delta-aware BACKBRIEF | OMISSION | -- | -- | LOW |

**Legend:**
- `CONFLICT` = The two documents say different things about the same behavior or interface.
- `GAP` = One document describes it, the other doesn't cover it (missing test or missing description).
- `AMBIGUOUS` = Neither document is clearly wrong, but together they create confusion.
- `NAMING` = Different terms for the same concept.
- `OMISSION` = A flowchart-level simplification omits a detail.

---

## Correctness Guidance

For each conflict, the authoritative source is:

1. **Implementation spec** (richard-revision-01.md) -- This is the build document. When the testing spec or flowchart differs, the implementation spec is the ground truth for behavior.
2. **Testing spec** (richard-revision-03.md) -- Must be updated to match the implementation spec's field definitions and behaviors. Any test referencing a field the implementation spec does not define (H5, H6, H7) must be resolved by either adding the field to the implementation spec or changing the test.
3. **Flowchart** (karl-revision-02.md) -- Should accurately reflect the implementation spec's behavior for the non-technical stakeholder. Simplifications are acceptable as long as they do not introduce factual errors. The Resource Analyst contradiction (M7) should be fixed in the flowchart.

---

*End of Cross-Document Consistency Audit*
