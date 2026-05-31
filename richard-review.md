# JORDAN Pipeline Tactical Review -- Military-to-Software Analogues for v2 Architecture

**Reviewer:** Richard (Claude Code)
**Date:** 2026-05-23
**Orchestrator:** Hermes
**Scope:** 61-framework research corpus + JORDAN v1 critical review (59 findings)
**Method:** Independent tactical analysis -- 4 phases, evidence-backed, action-first

---

## Executive Summary

JORDAN v1 is a Plan-and-Execute agent that has the right skeleton but wrong organs. The prior critical review found 6 CRITICAL, 12 HIGH, and 10 SERIOUS defects -- all still open. The 61-framework research corpus surfaces 7 high-leverage military concepts that map directly to v1 gaps, 5 civilian/AI frameworks that fill what military models miss, and 3 transformative AI architectures (ALAS, MAKER/MDAP, TAPE) with proven performance numbers.

**The single highest-leverage change for JORDAN v2 is not a new node or a new framework.** It is fixing the 4 approval-gate bypass paths (C1, CR1, H4, CRT1) that make the current security boundary performative. That is 62 lines of code and roughly one hour of work. Everything else -- new nodes, new architecture, new decomposition strategies -- is secondary until the gate works.

After the gate is fixed, the three architecture-level transformations with the highest IMPACT/EFFORT ratios are:

1. **FRAGO-style delta replanning** (replaces global replan with local compensation -- 83.7% success rate precedent from ALAS, 60% token reduction)
2. **Pre-mortem gate between Plan and Execute** (proven +30% strategy judgment accuracy, near-zero implementation cost)
3. **TAPE-style complexity triage at entry** (routes simple tasks past the heavy pipeline, +16.3% success rate precedent with 0.5B models)

These three changes, plus the gate fix, constitute JORDAN v2 Minimal Viable Product. They address the most consequential findings from both the critical review and the research corpus with the least code.

---

## Phase 1: Military-SW Mapping Assessment

### 1.1 Direct Mappings: Military Frameworks to JORDAN v1 Phases

| JORDAN v1 Phase | Military Framework | Mapping Strength | What Maps |
|:--|:--|:--|:--|
| **Plan** | MDMP Steps 1-4 (Mission Analysis through COA Comparison) | Strong | Multi-COA generation, wargaming as plan evaluation, commander's decision gate as HITL plan approval |
| **Plan** | JOPP Operational Design | Moderate | Strategic framing, PMESII-style context analysis, Center of Gravity identification |
| **Research** | IPB (Intelligence Preparation of the Battlefield) | Strong | Systematic context-building: define the environment, evaluate what is known, determine information gaps |
| **Risk Assessment** | Center of Gravity Analysis | Moderate | Identify the hub of power -- "what one thing, if changed, makes everything else easier/harder" |
| **Risk Assessment** | JTC Phase 3 (Target Development) | Moderate | Systematic vulnerability assessment, weaponeering analysis |
| **Approval Gate** | JTC Commander's Decision Gate | Strong | Single point of human authorization between planning and execution, go/no-go decision |
| **Execute** | F2T2EA Kill Chain (Engage phase) | Strong | Time-sensitive execution of planned actions, per-action tracking |
| **Execute** | SMEAC Paragraph 3 (Execution) | Moderate | Structured execution with coordinated instructions |
| **Synthesize** | F2T2EA Assess phase | Strong | Post-execution assessment: did the action achieve the desired effect? |
| **Synthesize** | AAR (After Action Review) | Moderate | Structured debrief comparing planned vs. actual, identifying sustainment/improvement |
| **Replan** | FRAGO (Fragmentary Order) | Very Strong | Lightweight incremental replanning -- communicate only changes, preserve what still holds |
| **Replan** | MDMP (re-initiated) | Weak | Full MDMP restart on plan failure is too heavy -- JORDAN replan should be FRAGO-style, not MDMP-reset |

**Key insight:** JORDAN v1's Plan -> Research -> Risk -> Approve -> Execute -> Synthesize -> Replan pipeline maps almost perfectly to MDMP fused with the Joint Targeting Cycle. The military developed these processes over decades for the exact problem JORDAN faces: an autonomous system that must plan, assess risk, get human authorization, execute, evaluate, and adapt -- all under uncertainty. The mapping is not metaphorical; it is structural.

### 1.2 Military Concepts MISSING from JORDAN v1 (Should Be Added)

These are ranked by strategic gap -- the distance between what JORDAN does and what it should do.

#### Gap 1: Commander's Intent + Mission Command (Distributed Execution)

**What is missing:** JORDAN v1 is a centralized plan-and-execute system. The orchestrator (plan node) specifies WHAT to do and HOW to do it at the sub-task level, then the execute node carries out instructions exactly. This is brittle. A single sub-task failure can invalidate downstream sub-tasks that are conceptually independent.

**What Commander's Intent provides:** Decouple WHAT from HOW. The commander states the intent, end-state, and constraints. Subordinates determine execution method. This maps to an orchestrator that specifies GOALS and BOUNDARIES rather than step-by-step instructions, with execution agents that have local autonomy within those constraints.

**Evidence:** Commander's Intent + Mission Command is one of 6 tenets of US Army Mission Command doctrine (ADP 6-0). It is proven across every US military operation since the 1980s. The software analogue is: replace the plan node's output from a prescriptive step-by-step task list to a goal specification with constraints and acceptance criteria, then let execution agents determine how to achieve each goal.

**JORDAN v2 application:** Modify the plan node's output format. Instead of `[{step: "search for X", tool: "web_search", params: {query: "X"}}]`, produce `[{goal: "Determine the current state of X", constraints: ["use authoritative sources only", "cite URLs"], acceptance_criteria: ["at least 3 independent sources confirm"]}]`. The execute node becomes an intent-driven executor rather than a script-runner.

**Concrete code impact:** `nodes.py` plan output format, execute node interpretation logic. The plan node's output schema changes; the execute node gains a "how to achieve this goal" reasoning step before tool selection.

#### Gap 2: Backbriefing / ROC Drill (Pre-Execution Verification)

**What is missing:** JORDAN v1 has no mechanism to verify that the plan was understood correctly before execution begins. The plan node generates a plan, the execute node runs it. If the plan node hallucinated a dependency, produced an impossible step, or the execute node misinterprets an instruction, the error surfaces during execution -- when it is expensive to fix.

**What Backbriefing provides:** Before execution, subordinates brief the plan back to the commander. "Here is what I understood the plan to be. Here is how I intend to execute it. Here are the key decision points I anticipate." This catches misunderstandings when they are cheap to fix -- before resources are committed.

**Evidence:** Backbriefing + ROC Drill is standard in US Army planning doctrine (FM 6-0). It is a lightweight verification step: 5-15 minutes, verbal, no new artifacts. The research report (lines 1593-1991) documents its structure and adaptation path to LLM workflows.

**JORDAN v2 application:** Insert a BACKBRIEF node between Plan and Research/Execute. The backbrief node receives the plan, generates a restatement ("Here is my understanding of what this plan will do..."), identifies potential ambiguities or conflicts, and flags them BEFORE the plan enters execution. The backbrief output is a diff against the original plan: either "confirm -- plan is internally consistent and executable" or "flag -- these 3 sub-tasks have ambiguous dependencies / contradictory requirements."

**Concrete code impact:** New node ~150-200 lines. One LLM call parsing the plan and restating it. If flags are raised, the plan is routed back to the plan node for revision BEFORE research/execution. This is a pure addition -- no existing code changes.

#### Gap 3: Pre-mortem Analysis (Prospective Failure Detection)

**What is missing:** JORDAN v1's risk assessment is a regex-based pattern matcher that classifies individual tool calls. It does not assess the plan as a whole. A plan can consist entirely of LOW-risk sub-tasks (passes the gate on each) but still fail catastrophically because the sub-tasks interact in an unforeseen way, or because the plan makes a false assumption about the environment.

**What Pre-mortem provides:** "Imagine we executed this plan and it failed spectacularly. Write down every reason why." Prospective hindsight increases outcome-reason identification by 30% (Mitchell, Russo, Pennington, 1989). It counters the planning fallacy. It surfaces risks that per-task pattern matching cannot see.

**Evidence:** The pre-mortem is the most directly transferable methodology from the entire 61-framework corpus. Research report lines 8807-9005. Multiple LLM calls with different personas simulate diverse team perspectives generating independent failure scenarios. No specialized tools, data, or infrastructure needed.

**JORDAN v2 application:** Insert a PREMORTEM node between Risk Assessment and the Approval Gate. The pre-mortem receives the full plan + risk classifications, then generates failure scenarios at the PLAN level (not the tool-call level). The output feeds back to the plan node for revision before execution. If the pre-mortem surfaces a fatal flaw, the plan is blocked at a fraction of the cost of executing it and discovering the flaw through failure.

**Concrete code impact:** New node ~100-150 lines. 3-5 parallel LLM calls with different temperature/persona settings for diverse failure generation. Consolidation and de-duplication of failure scenarios. Integration: the pre-mortem output augments the risk assessment, potentially upgrading sub-task risk levels or adding new concerns.

#### Gap 4: Cynefin-Based Problem Classification (Right Method for Right Problem)

**What is missing:** JORDAN v1 treats all user requests uniformly -- Plan -> Research -> Risk -> Execute -> Synthesize -> Replan for everything from "what is 2+2?" to "build a production microservice." This is wasteful for simple tasks and insufficient for complex ones.

**What Cynefin provides:** Problem domain classification BEFORE method selection. Ordered domain -> best practice (follow the recipe). Complicated domain -> expert analysis (analyze, then act). Complex domain -> probe-sense-respond (experiment, learn, adapt). Chaotic domain -> act-sense-respond (stabilize immediately).

**Evidence:** Cynefin Framework (Snowden, 2007). Research report lines 2677-2867. TAPE provides the computational implementation: dual-process architecture (System 1 fast for simple, System 2 slow for complex) with +16.3% success improvement using two 0.5B models.

**JORDAN v2 application:** Add a CLASSIFY node at pipeline entry. The classifier determines problem domain (simple, complicated, complex, chaotic) and routes accordingly. Simple tasks bypass Plan/Research/Risk and go to a lightweight direct-execute path. Complicated tasks engage the full pipeline but with expert-analysis mode (fewer COAs, deeper analysis). Complex tasks engage iterative probe-sense-respond with pre-mortem and multiple COA generation. Chaotic tasks escalate to human immediately.

**Concrete code impact:** Classification gate ~50-80 lines added at the entry to `graph.py`. Three execution paths (fast, standard, deep) with different pipeline configurations. The TAPE paper demonstrates this works with models as small as 0.5B parameters.

#### Gap 5: Voyager/DEPS Skill Accumulation (Memory Between Runs)

**What is missing:** JORDAN v1 is amnesiac. Each task is independent. The pipeline does not remember successful plans, failed strategies, useful research findings, or effective tool combinations across workflows. This is the most strategically significant gap -- it means JORDAN cannot improve with use.

**What Voyager/DEPS provides:** A skill library that accumulates across runs. Successful plans become templates. Failed approaches are recorded with their failure reasons. Research findings persist. The agent builds a growing repertoire of proven capabilities.

**Evidence:** Voyager (Wang et al., 2023) and DEPS (Describe-Explain-Plan-Select). Research report documents the skill accumulation pattern. The finding is item 46 in the research corpus. JORDAN has no equivalent.

**JORDAN v2 application:** Add a persistent skill/plan library backed by a lightweight store (SQLite or file-based). After successful plan completion, the plan structure, tool combinations, and key decisions are archived with tags. The plan node queries the library before generating new plans: "Has a similar problem been solved before?" If yes, the previous successful plan template seeds the new plan generation.

**Concrete code impact:** New `skill_library.py` module ~200-300 lines. Integration with plan node (~30 lines changed). Schema: `{problem_signature, plan_template, tools_used, success_metrics, failure_modes_encountered, date}`. Retrieval via semantic similarity or keyword matching on the problem description.

### 1.3 Civilian/AI Frameworks That Fill Military Gaps

Military frameworks are strong on command structure, risk gates, and execution discipline. They are weak on:

| Gap | Military Weakness | Civilian/AI Framework That Fills It |
|:--|:--|:--|
| Task decomposition granularity | MDMP decomposes to mission tasks, not micro-steps | WBS 8-80 hour rule, MAKER/MDAP maximal decomposition (Theta(s ln s) cost scaling) |
| Recursive decomposition for complex problems | Military hierarchy is 3-tier (strategic/operational/tactical) | RDD -- Recursive Decomposition with Dependencies (NeurIPS 2024), LLM discovers dependency DAG automatically |
| Quantitative cost-of-error analysis | Military accepts risk through commander's judgment | MAKER/MDAP SPRT voting -- statistical guarantee of correctness with quantifiable error probability |
| Adaptive execution under disruption | OODA assumes human-in-loop for adaptation | ALAS Local Cascading Repair Protocol -- 83.7% success, 60% token reduction, 1.82x speedup over global replan |
| Learning from repeated operations | AAR is post-hoc and manual | Voyager/DEPS skill library accumulation -- automated pattern extraction from successful runs |
| Problem classification before method selection | Military classifies missions by type (offense/defense/stability) but not by complexity class | Cynefin + TAPE -- classification determines process, not just labeling |
| Causal analysis of complex failures | AAR describes what happened but not WHY in causal terms | Theory of Constraints CRT -> Evaporating Cloud -> FRT (Goldratt) -- LLM-compatible causal-logical chain |
| Dependency visualization beyond DAG | Military uses synchronization matrices (static) | Dependency Structure Matrix (DSM) -- NxN interaction matrix revealing cycles, coupling clusters, hidden dependencies |

**Key insight:** The military frameworks define the COMMAND architecture (who decides, when, with what authority). The civilian/AI frameworks define the COGNITIVE architecture (how to think about the problem, how to decompose it, how to learn from it). JORDAN v2 needs both.

---

## Phase 2: Prioritized Actionable Implementation Plan

Rank-ordered by IMPACT/EFFORT ratio. IMPACT is measured as: (security improvement * severity of gap addressed) + (performance improvement * frequency of benefit). EFFORT is measured in lines changed and estimated hours.

### Priority 1: Fix the Approval Gate (CRITICAL -- Must Ship First)

**IMPACT/EFFORT:** Very High / Very Low

#### Recommendation 1.1: Close C1 -- Replan -> Risk Re-Check

**What:** Change `graph.py:347-348` from unconditional `replan -> execute` edge to conditional `replan -> risk_assessment -> execute`.

**Why:** After replanning, the revised plan routes directly to execution with no risk re-check. A workflow that started with LOW-risk sub-tasks can replan into HIGH-risk sub-tasks (file deletion, POST requests) that execute without human approval. The research corpus confirms this is not just a code bug but a doctrinal violation: both MDMP (re-initiated after significant change) and JOPP (continuous assessment loop) require re-assessment when the plan changes. FRAGO doctrine explicitly states that fragmentary orders must be evaluated for risk changes before execution.

**How:**
```python
# graph.py:347-348 -- REPLACE:
graph.add_edge("replan", "execute")
# WITH:
graph.add_conditional_edges("replan", _should_route_to_risk_or_execute, {
    "risk_assessment": "risk_assessment",
    "execute": "execute",
    "end": END
})
# Where _should_route_to_risk_or_execute checks: did the replan actually change sub-tasks?
# If yes -> risk_assessment (re-classify changed sub-tasks)
# If no -> execute (no change, original risk assessment still valid)
```

**Effort:** 2 lines changed (one conditional edge definition) + ~15 lines for the routing function. ~20 minutes.

**Risk:** The routing function must correctly detect whether the replan actually changed sub-task composition (new sub-tasks, modified tool calls, changed dependencies). If it incorrectly routes to risk_assessment when nothing changed, it wastes one LLM call. Mitigation: the routing function compares sub-task IDs and tool signatures before/after replan -- simple, deterministic, no LLM call needed.

#### Recommendation 1.2: Close CR1 -- Parallel Path Approval

**What:** Port `request_approval()` call and `AWAITING_APPROVAL` state transition from sequential executor (`nodes.py:2627-2640`) into parallel executor (`_execute_subtask_inline` at `nodes.py:2072-2092`). Add batch loop short-circuit when any inline result has `awaiting_approval=True`.

**Why:** When `enable_parallel_execution=True`, HIGH-risk sub-tasks execute with zero human review. The parallel executor was implemented independently of the sequential executor, and the approval gating was never ported. This means the performance path (parallel mode) is incompatible with the security boundary (approval gate). The research corpus identifies this as a doctrinal violation of the Commander's Intent pattern: the commander's constraints (approval required for HIGH-risk) must apply regardless of execution method.

**How:**
```python
# In _execute_subtask_inline, BEFORE tool execution:
risk_level = state.classify_tool_call(subtask.tool_name, subtask.tool_input)
if risk_level == RiskLevel.HIGH:
    approval = state.request_approval(subtask)
    if approval.awaiting:
        return {"awaiting_approval": True, "subtask_id": subtask.id}
    elif approval.rejected:
        return {"skipped": True, "subtask_id": subtask.id, "reason": "rejected"}
# THEN execute the tool call

# In the batch loop, AFTER dispatching all ready tasks:
if any(result.get("awaiting_approval") for result in batch_results):
    state.transition_to(AWAITING_APPROVAL)
    return  # short-circuit -- wait for human
```

**Effort:** ~20 lines added to `_execute_subtask_inline`, ~5 lines in batch loop. ~45 minutes.

**Risk:** Parallel approval introduces a new state machine complexity: some sub-tasks in a batch may be approved while others await approval. The batch loop must handle partial completion. Mitigation: track per-sub-task approval state separately; on human response, re-enter the batch loop from the same DAG state, skipping already-approved sub-tasks and executing newly-approved ones.

#### Recommendation 1.3: Close H4 -- Remove Planner's Risk Bypass

**What:** Remove the `requires_tools=False` and `conversational` category bypass in `gates.py:110-126`. Classify ALL sub-tasks regardless of planner annotation.

**Why:** The planner (an LLM component) can unilaterally skip risk assessment for any sub-task. Defense-in-depth depends entirely on planner honesty. A compromised or hallucinating planner can mark a `DELETE /prod/database` sub-task as `requires_tools=False` and it executes without classification. This is a single-point-of-failure in the security architecture. No military doctrine allows a planning staff to unilaterally waive safety review.

**How:**
```python
# gates.py:110-126 -- REMOVE the bypass condition:
# BEFORE:
if task.requires_tools == False or task.category == "conversational":
    return True  # skip risk assessment
# AFTER:
# All tasks classified. Remove the bypass entirely.
# If a task genuinely requires no tools, the risk classifier will correctly
# classify it as LOW (no dangerous tool calls) without needing a planner bypass.
```

**Effort:** ~10 lines removed. ~15 minutes.

**Risk:** Some genuinely harmless tasks (greeting responses, simple Q&A) will now go through risk classification, adding a negligible overhead. The risk classifier correctly identifies these as LOW (no tool calls matched) with near-zero latency. The cost is one regex pass per sub-task -- microseconds.

#### Recommendation 1.4: Close CRT1 -- Fix Risk Classifier Weaponization

**What:** Separate the pattern match run into two phases: (1) match patterns against `tool_name` + `tool_description` only (system-controlled strings) -- this determines the BASELINE risk; (2) match patterns against `tool_input` (user-controlled) -- this is ADVISORY only and can upgrade but never downgrade the risk. Change the no-match default from LOW/confidence-0.7 to MEDIUM/UNCLASSIFIED.

**Why:** The current classifier builds `description = f"Tool call: {tool_name} with input: {input_str[:500]}"` and regex-matches the combined string. Attack: (a) "delete all passwords" in a search query classifies search as HIGH (risk inflation -> denial of service). (b) "wipe entries" for `rm -rf /` bypasses all HIGH patterns, and the default fall-through is LOW with confidence 0.7 -> auto-approved (risk evasion). Unknown actions are auto-approved by default. This inverts the security principle of default-deny.

**How:**
```python
# risk.py:340-359 -- REFACTOR:
def classify_tool_call(self, tool_name: str, tool_description: str, tool_input: str):
    # Phase 1: System-controlled classification (determines BASELINE)
    system_risk = self._match_patterns(f"{tool_name} {tool_description}")
    
    # Phase 2: User-input advisory classification (can only UPGRADE)
    input_risk = self._match_patterns(tool_input[:500])
    
    # User input can escalate (e.g., "delete" in input is still dangerous)
    # but can never de-escalate (user saying "safe" doesn't make rm -rf safe)
    if input_risk.level > system_risk.level:
        final_risk = input_risk
    else:
        final_risk = system_risk
    
    # Change default from LOW to MEDIUM/UNCLASSIFIED
    if final_risk.level == RiskLevel.UNMATCHED:
        return RiskResult(level=RiskLevel.MEDIUM, confidence=0.3, 
                         reason="UNCLASSIFIED -- no pattern match, requires human review")
    return final_risk
```

**Effort:** ~30 lines changed. ~45 minutes.

**Risk:** Changing the default from LOW to MEDIUM will increase the number of approval requests for genuinely safe novel tool calls. This increases human burden but is the correct security posture. Mitigation: add an allowlist for known-safe tools that have been reviewed and explicitly classified LOW, built up over time as the system processes more task types.

### Priority 2: Architecture-Level Transformations (HIGH Impact)

#### Recommendation 2.1: FRAGO-Style Delta Replanning (Replace Global Replan)

**What:** Replace JORDAN v1's global replanning (throw away entire plan, regenerate from scratch) with delta-based local replanning. The replan node identifies the MINIMAL affected region of the plan that needs repair and regenerates only that region, preserving everything else.

**Why:** Global replanning is catastrophically expensive. ALAS (Stanford, 2025) demonstrates that the Local Cascading Repair Protocol achieves 83.7% success rate, 60% token reduction, and 1.82x speedup over global replanning. FRAGO doctrine provides the military precedent: communicate only what CHANGED, preserve what still holds, use "No change" convention. JORDAN v1's replan node does the equivalent of re-issuing the full 5-paragraph OPORD when only one sub-task failed. The research corpus (lines 3982-4205) documents FRAGO's structure and the "No change" convention that makes delta orders efficient.

**How:**
1. When a sub-task fails or the synthesizer detects inadequate results, replan evaluator identifies the FAILED sub-tasks and their DEPENDENTS (tasks that consumed the failed task's output).
2. The replan node generates a FRAGO: a delta document containing ONLY replacement sub-tasks for the affected region, with explicit "no change" markers for everything else.
3. The FRAGO is versioned (plan v1 -> FRAGO v1.1 -> FRAGO v1.2) with full traceability of what changed and why.
4. Re-execution only runs the changed sub-tasks and their dependents.

**Concrete code impact:**
- `replanning.py`: Major refactor. Replace global replan logic with delta generation. New method: `generate_frago(failed_task_ids, current_plan, execution_results) -> FRAGO`. ~200-300 lines changed.
- `nodes.py` replan node: Update to consume and apply FRAGOs. ~50 lines changed.
- New `frago.py`: FRAGO data model with versioning, "no change" markers, and dependency impact analysis. ~150 lines.
- `graph.py`: Update replan -> execute/risk_assessment edge to handle FRAGO application. ~10 lines.

**Effort:** ~400-500 lines changed/added across 4 files. ~6-8 hours.

**Risk:** Delta replanning can miss cascading effects. If sub-task C depends on sub-task B which depends on sub-task A, and A fails, regenerating A alone may not account for the fact that B and C consumed A's (now-invalid) output. Mitigation: the FRAGO impact analysis MUST trace transitive dependents and mark them for re-execution. ALAS's "repair radius expansion" provides the algorithm: start with the failed task, expand one DAG hop, check if compensation is sufficient, expand further if needed.

#### Recommendation 2.2: Pre-mortem Gate Between Plan and Execute

**What:** Insert a PREMORTEM node after Risk Assessment and before the Approval Gate. The pre-mortem node generates failure scenarios for the plan as a whole and feeds findings back to Plan for revision before execution.

**Why:** The pre-mortem is the highest-IMPACT, lowest-EFFORT addition from the entire research corpus. It requires no new infrastructure, no data, no tools -- just LLM calls. The cognitive mechanism (prospective hindsight) is validated (Mitchell, Russo, Pennington, 1989) with +30% strategy judgment accuracy. It directly addresses a structural gap in JORDAN v1: the risk classifier assesses individual tool calls but cannot assess plan-level failure modes (interaction effects, false assumptions, environmental changes). The research report (lines 8972-8986) provides a complete adaptation path.

**How:**
1. After Risk Assessment produces per-sub-task risk levels, the PREMORTEM node receives the full plan + risk assessment.
2. It spawns 3-5 parallel LLM calls with different personas (the pessimist, the domain expert, the adversary, the naive user) and different temperature settings.
3. Each generates independent failure scenarios: "This plan failed. Here is why."
4. A consolidation step de-duplicates and categorizes failure scenarios.
5. If any scenario rates as HIGH severity AND plausible (the LLM judges both dimensions), the plan is routed back to Plan for revision, with the pre-mortem findings as revision guidance.
6. Plan revision incorporates the pre-mortem findings, and the revised plan goes through Risk Assessment again (and pre-mortem again, if configured for multiple iterations -- with a hard ceiling of 2 pre-mortem iterations to prevent infinite loops).

**Concrete code impact:**
- New `premortem.py`: Node logic with persona-based scenario generation and consolidation. ~150 lines.
- `graph.py`: Insert PREMORTEM node between risk_assessment and approval_gate. Add conditional edge: premortem -> plan (if fatal flaws found) or premortem -> approval_gate (if plan passes). Add iteration ceiling (max 2 pre-mortem rounds). ~20 lines.

**Effort:** ~170 lines new/changed. ~3-4 hours.

**Risk:** Pre-mortem can degenerate into generating obvious, non-actionable failure scenarios ("the API was down," "the internet stopped working"). Mitigation: the consolidation step should score scenarios on both SEVERITY and SPECIFICITY. Generic scenarios (applicable to any plan) are downgraded. Specific scenarios (identifying a particular dependency, assumption, or interaction unique to this plan) are surfaced. The prompt engineering is load-bearing here -- the personas and the scoring rubric determine whether the pre-mortem adds value or noise.

#### Recommendation 2.3: TAPE-Style Complexity Triage at Entry

**What:** Add a CLASSIFY node at the pipeline entry that routes simple tasks to a lightweight fast path and complex tasks to the full pipeline.

**Why:** Not every user request needs Plan -> Research -> Risk -> Execute -> Synthesize -> Replan. Simple factual queries, single-step operations, and straightforward code generation waste tokens and wall-clock time going through the full pipeline. TAPE demonstrates that dual-process classification (System 1 fast, System 2 slow) achieves +16.3% success rate improvement using two 0.5B parameter models. The military analogue is mission-type classification: a reconnaissance patrol does not get the same planning process as a division-level offensive.

**How:**
1. CLASSIFY node runs a single fast LLM call (cheap model -- DeepSeek Flash or equivalent) that classifies the user request into one of three categories:
   - **SIMPLE:** Factual query, single-step tool call, well-defined operation with no ambiguity. Route to FAST PATH (direct execute, no plan/research/risk).
   - **STANDARD:** Multi-step operation, moderate ambiguity, well-understood domain. Route to STANDARD PATH (full pipeline, but lighter -- single COA, standard risk assessment).
   - **COMPLEX:** Novel domain, high ambiguity, multiple interacting sub-tasks, safety-sensitive. Route to DEEP PATH (full pipeline + pre-mortem + multi-COA generation + backbrief).
2. The classifier's confidence determines routing. Low confidence -> escalate to next higher complexity tier (conservative bias).
3. The classification is recorded for post-hoc analysis: did SIMPLE-classified tasks ever fail? Did COMPLEX-classified tasks waste resources? This data tunes the classifier.

**Concrete code impact:**
- New `classify.py`: Classification node ~80 lines.
- `graph.py`: Three pipeline configurations (fast, standard, deep) as graph variants. Entry routing based on classification result. ~80 lines.
- `nodes.py`: Fast-path execute node (simplified, no sub-task decomposition, direct tool call). ~100 lines.

**Effort:** ~260 lines new/changed. ~4-5 hours.

**Risk:** Misclassification of a COMPLEX task as SIMPLE is the most consequential failure mode. A complex, safety-sensitive task routed to the fast path bypasses all risk assessment, approval gating, and plan verification. Mitigation: (a) the classifier's default is conservative -- if uncertain, escalate to STANDARD; (b) the classification prompt includes explicit examples of each tier with decision boundaries; (c) the fast path still includes a lightweight pattern-match check for obviously dangerous tool calls (file deletion, POST requests, shell commands) and escalates to the approval gate if triggered.

### Priority 3: Quality-of-Execution Improvements (MODERATE Impact)

#### Recommendation 3.1: Backbrief/ROC Drill Verification Node

**What:** Insert a BACKBRIEF node between Plan and Research. The backbrief restates the plan and flags internal inconsistencies, ambiguous dependencies, or impossible steps BEFORE resources are committed to research and execution.

**Why:** Backbriefing catches plan-level errors when they are cheapest to fix -- before research has fetched information, before execution has made changes. The military has used this for decades: subordinates briefing the plan back to the commander catches misunderstandings that the plan documents did not surface. The research corpus (lines 1593-1991) provides the doctrinal structure and LLM adaptation path.

**How:**
1. After Plan generates a plan, BACKBRIEF receives the plan and generates: (a) a restatement in different words ("Here is my understanding of the plan..."); (b) identification of each sub-task's dependencies and expected outputs; (c) flags for any internal inconsistency (sub-task C depends on sub-task B's output, but sub-task B does not produce the format that sub-task C expects).
2. If flags are raised, the plan routes back to Plan for revision.
3. If the backbrief confirms consistency, the pipeline proceeds to Research.

**Concrete code impact:**
- New `backbrief.py`: Node logic ~120 lines.
- `graph.py`: Insert BACKBRIEF node between plan and research. Conditional routing. ~10 lines.

**Effort:** ~130 lines new/changed. ~2-3 hours.

**Risk:** Backbrief can become a rubber stamp -- the LLM restates the plan without genuine critical analysis. Mitigation: the backbrief prompt must include explicit instruction to identify SPECIFIC inconsistencies with line references to the plan. Generic confirmation ("the plan looks good") is treated as a failure to backbrief properly and triggers a re-prompt with stronger instructions.

#### Recommendation 3.2: Retry Logic for Parallel Executor (Close CR2)

**What:** Port the sequential executor's 2-3 retries with LLM-based error analysis and corrective action (`nodes.py:2853-3021`) into the parallel path (`_execute_subtask_inline`).

**Why:** The parallel executor performs single-shot tool calls. The sequential executor has 2-3 retries with LLM-based error analysis. This means parallel execution produces STRICTLY WORSE results than sequential -- defeating the purpose of parallel mode as a performance optimization. Users who enable parallel mode for speed are unknowingly degrading output quality.

**How:**
1. Extract the retry logic from the sequential executor into a shared helper: `_execute_with_retry(subtask, max_retries=3)`.
2. Call the shared helper from both sequential and parallel execution paths.
3. The parallel path's batch loop must handle the case where one sub-task's retries take longer than another's (the semaphore should not block other tasks from completing their retries).

**Concrete code impact:**
- New shared helper `_execute_with_retry()` ~40 lines.
- `nodes.py`: Remove retry logic from sequential path, call shared helper. Update `_execute_subtask_inline` to call shared helper. ~30 lines changed.

**Effort:** ~70 lines changed/added. ~2 hours.

**Risk:** Retries in parallel mode increase the latency variance across sub-tasks in a batch. A sub-task on its 3rd retry will finish much later than a sub-task that succeeded on its 1st attempt. This can create straggler effects in the batch loop. Mitigation: the batch loop already handles this by waiting for all tasks in the batch to complete. The retry count should be included in the progress reporting so the user understands why some sub-tasks are taking longer.

#### Recommendation 3.3: Graph-Level Replan Ceiling (Close C2)

**What:** Check `doc.metadata["replan_iteration"]` in the conditional `_should_continue_to_synthesize_or_replan`. Refuse "replan" when a config-defined max (default 3) is reached. Route to "synthesize" instead.

**Why:** The conditional delegates loop termination entirely to the replanning evaluator. If the evaluator persistently returns `should_replan=True` (LLM hallucination, broken heuristic, genuinely unsolvable problem), the graph loops forever. This is an infinite loop bug in the graph topology, not a theoretical concern -- LLM nondeterminism makes it a real risk.

**How:**
```python
# graph.py:200-210 -- ADD ceiling check:
def _should_continue_to_synthesize_or_replan(state):
    iteration = state.doc.metadata.get("replan_iteration", 0)
    max_replans = state.config.max_replan_iterations  # default 3
    if iteration >= max_replans:
        logger.warning(f"Replan ceiling hit ({iteration} iterations). Forcing synthesize.")
        return "synthesize"
    # ... existing evaluation logic ...
```

**Effort:** ~5 lines added to `graph.py`. ~15 minutes.

**Risk:** A hard ceiling could cut off replanning for a genuinely complex problem that needs more iterations. Mitigation: The ceiling is configurable (`config.max_replan_iterations`). The user can raise it. The ceiling should also trigger a clear user-facing warning: "JORDAN was unable to resolve all issues after 3 replanning attempts. The best-effort result is shown below. You may want to rephrase the task or break it into smaller pieces."

### Priority 4: Skill Accumulation Foundation (MODERATE Impact, Higher Effort)

#### Recommendation 4.1: Persistent Skill Library (Voyager/DEPS Pattern)

**What:** Add a persistent store for successful plan templates, research findings, and failure patterns. The plan node queries the library before generating new plans.

**Why:** JORDAN v1 is amnesiac. Each task is independent. The research corpus identifies this as a critical architectural gap (item 46: Voyager/DEPS). A skill library is the foundation for compound improvement: the 100th task should benefit from the 99 that came before.

**How:**
1. New `skill_library.py` module with a SQLite-backed store.
2. Schema: `{id, problem_signature, domain_tags, plan_template, tools_used, success_rating, failure_modes, execution_stats, created_at, last_used_at}`.
3. After successful plan completion (synthesizer rates output as adequate), the plan structure is archived with extracted problem signature and domain tags.
4. The plan node, before generating a new plan, queries: "Find the 3 most similar previously successful plans." If similar plans exist with high success ratings, they are injected into the plan generation prompt as templates/starting points.
5. Failed plans are also archived with their failure modes, preventing the planner from re-generating the same failed approach.

**Concrete code impact:**
- New `skill_library.py`: ~250 lines.
- `nodes.py` plan node: Add library query before plan generation, add library write after successful completion. ~30 lines changed.
- `nodes.py` synthesize node: Add success rating metric that feeds into library write. ~15 lines changed.

**Effort:** ~300 lines new/changed. ~5-6 hours.

**Risk:** The skill library can lock the planner into past approaches, reducing creativity. A previously successful plan may not be optimal for a subtly different problem. Mitigation: the library provides TEMPLATES, not mandates. The planner uses them as starting points but can diverge. The success rating includes a recency decay -- old plans lose relevance over time unless they are repeatedly used successfully.

### Summary: Implementation Priority Matrix

| Rank | Recommendation | Impact | Effort | Lines | Hours | Phase |
|:--|:--|:--|:--|:--|:--|:--|
| **P1** | 1.1 Close C1: replan -> risk re-check | Very High | Very Low | ~17 | 0.3 | Wave 1 Security |
| **P1** | 1.2 Close CR1: parallel approval | Very High | Low | ~25 | 0.75 | Wave 1 Security |
| **P1** | 1.3 Close H4: remove planner bypass | Very High | Very Low | ~10 | 0.25 | Wave 1 Security |
| **P1** | 1.4 Close CRT1: fix classifier weaponization | Very High | Low | ~30 | 0.75 | Wave 1 Security |
| **P2** | 2.1 FRAGO delta replanning | High | High | ~450 | 7 | Wave 2 Correctness |
| **P2** | 2.2 Pre-mortem gate | High | Moderate | ~170 | 3.5 | Wave 2 Correctness |
| **P2** | 2.3 TAPE complexity triage | High | Moderate | ~260 | 4.5 | Wave 2 Correctness |
| **P3** | 3.1 Backbrief verification | Moderate | Low | ~130 | 2.5 | Wave 3 Architecture |
| **P3** | 3.2 Retry logic for parallel (CR2) | Moderate | Low | ~70 | 2 | Wave 2 Correctness |
| **P3** | 3.3 Graph-level replan ceiling (C2) | Moderate | Very Low | ~5 | 0.25 | Wave 2 Correctness |
| **P4** | 4.1 Skill library (Voyager pattern) | Moderate | High | ~300 | 5.5 | Wave 3 Architecture |

**Wave 1 total:** ~82 lines, ~2 hours. Fixes all 4 CRITICAL security findings.
**Wave 2 total:** ~955 lines, ~17 hours. Addresses correctness, adds pre-mortem + triage.
**Wave 3 total:** ~430 lines, ~8 hours. Backbrief, skill library, architecture cleanup.
**Grand total:** ~1,467 lines, ~27 hours.

---

## Phase 3: Architecture Recommendations

### 3.1 JORDAN v2 Topology

```
USER INPUT
    |
    v
[CLASSIFY] --(simple)--> [FAST EXECUTE] --> [SYNTHESIZE] --> OUTPUT
    |
  (standard/complex)
    |
    v
[PLAN] -- uses Skill Library for template seeding
    |
    v
[BACKBRIEF] -- verify plan consistency; if flags -> back to PLAN
    |
    v
[RESEARCH] -- TAPE-style two-stage retrieval (dense + reranker)
    |
    v
[RISK ASSESSMENT] -- per-task tool classification + plan-level structural risk
    |
    v
[PREMORTEM] -- generate failure scenarios; if fatal -> back to PLAN
    |
    v
[APPROVAL GATE] -- HITL for HIGH-risk; applies in BOTH sequential AND parallel modes
    |
    v
[EXECUTE] -- parallel or sequential; both paths have retry logic + approval
    |
    v
[SYNTHESIZE] -- assemble results, quality review
    |
    v
[EVALUATE] -- assess: success? partial? failure?
    |
    +--(success)--> OUTPUT + archive to Skill Library
    |
    +--(partial/failure)--> [REPLAN - FRAGO]
                              |
                              v
                          Generate delta plan (only changed sub-tasks)
                              |
                              v
                          [RISK ASSESSMENT] -- re-classify changed sub-tasks only
                              |
                              v
                          [EXECUTE] -- execute only changed + dependents
                              |
                              v
                          [SYNTHESIZE] --> [EVALUATE] --> (loop, max 3 replans)
```

**New nodes:** CLASSIFY, BACKBRIEF, PREMORTEM, EVALUATE (split from SYNTHESIZE)
**Removed:** Direct replan -> execute edge (replaced by replan -> risk -> execute)
**Modified:** PLAN (skill library integration), EXECUTE (parallel approval + retry), REPLAN (FRAGO delta mode), APPROVAL GATE (defense-in-depth)
**Unchanged:** RESEARCH (content unchanged, but positioned after backbrief)

### 3.2 Centralized vs. Distributed Planning -- Commander's Intent Pattern

**Recommendation:** JORDAN v2 should evolve TOWARD distributed execution but MAINTAIN centralized planning for v2 MVP.

**Rationale:**

Centralized planning (current JORDAN v1 model) is correct for v2 for these reasons:
1. The planner has global visibility of the task and can optimize for end-to-end coherence.
2. Commander's Intent distributed execution (goal specification without method prescription) is the right long-term target but requires mature execution agents with reliable local decision-making -- which JORDAN does not yet have.
3. The v2 plan node should adopt Commander's Intent OUTPUT FORMAT (goals + constraints + acceptance criteria) while maintaining centralized plan generation. This is an incremental step: change the plan schema first, then change the execution model later.

The Commander's Intent output format looks like this:

```yaml
intent:
  end_state: "The user has a working production deployment of service X with monitoring"
  constraints:
    - "Use only infrastructure-as-code (Terraform/CloudFormation)"
    - "Must pass security scan before deployment"
    - "Total cost must not exceed $X/month"
  acceptance_criteria:
    - "curl /health returns 200"
    - "Prometheus metrics endpoint is reachable"
    - "Deployment documented with rollback procedure"

sub_tasks:
  - goal: "Provision compute resources"
    constraints: ["inside VPC", "IAM roles attached"]
    acceptance: ["instance is SSH-accessible", "security group restricts to port 443 only"]
    # Execution agent determines HOW to achieve this goal
```

This format enables the execute node to have local autonomy within constraints. If provisioning fails with one approach, the execute node can try another approach without replanning, AS LONG AS the new approach satisfies the same constraints and acceptance criteria. This is the FRAGO/Commander's Intent hybrid: the commander specifies WHAT must be true, the subordinate determines HOW to make it true, and replanning is only needed when the WHAT changes.

**Migration path:**
- v2.0: Plan node output format changes to Commander's Intent schema. Execute node still follows instructions literally but the schema supports future autonomy.
- v2.1: Execute node gains local decision-making within constraints. If a step fails, try alternative approaches before escalating to replan.
- v2.2: Full distributed execution with multi-agent task allocation.

### 3.3 Approval Gate Restructuring

**Current state (v1):** Single approval gate on the risk_assessment -> execute edge. Per-subtask binary approve/reject. Four independent bypass paths. Default-LOW on unknown. Single-human approver (the task submitter). No audit trail. No timeout.

**Recommended state (v2):**

1. **Defense-in-depth:** The approval gate is no longer a single point of failure. Two additional layers:
   - **Layer 1: Classifier gate** (PRE-EXECUTION, automated) -- the pre-mortem and risk classifier together produce a risk posture assessment. If the overall plan risk is HIGH (multiple HIGH sub-tasks, destructive operations, external API calls), the plan is flagged for mandatory human review BEFORE any sub-task execution.
   - **Layer 2: Approval gate** (PER-SUBTASK, human) -- the existing gate, now mandatory in both sequential and parallel modes, with the classifier weaponization fixed (CRT1) and the planner bypass removed (H4).
   - **Layer 3: Sandbox gate** (PER-TOOL-CALL, automated) -- the existing Nexus sandbox (hermie_run with allowlist, timeout, ulimit) provides defense-in-depth at the shell execution level.

2. **Allowlist shift:** The risk classifier changes from a denylist (block known-dangerous patterns, default-allow everything else) to a graduated system:
   - **Allowlist tier:** Known-safe tools (read-only file access, search queries, code analysis) are pre-classified LOW.
   - **Denylist tier:** Known-dangerous tools (file deletion, shell execution, POST requests) are pre-classified HIGH.
   - **Review tier:** Everything else is MEDIUM/UNCLASSIFIED -- requires human review on first use, can be moved to allowlist or denylist after review.

3. **Structured approval briefing:** The approval request format changes from natural language narrative to structured fields:
   ```yaml
   approval_request:
     subtask_id: "subtask-7"
     tool: "shell_execute"
     command: "rm -rf /tmp/build-artifacts"
     risk_level: HIGH
     matched_pattern: "rm -rf" (destructive file operation)
     blast_radius: "Deletes /tmp/build-artifacts directory. No impact outside /tmp."
     alternatives: ["Move to trash instead (recoverable)", "Archive to /tmp/archive first"]
     dependent_subtasks: ["subtask-9 (deploy) depends on this cleanup completing"]
   ```

4. **Approval audit trail:** Every approval/rejection is logged immutably with: who, what, when, risk justification, decision, and whether the operation completed successfully. The current split-brain (MR7) is fixed so the persistent store is the source of truth.

5. **Timeout + escalation:** HIGH-risk approvals auto-reject after a configurable timeout (default: 1 hour) with a notification to the user. This prevents workflows from blocking indefinitely.

### 3.4 Decomposition Granularity

**Current state (v1):** The plan node decomposes tasks at whatever granularity the LLM chooses. No guidance. No consistency. Tasks range from atomic (single API call) to monolithic (entire feature implementation).

**Recommended state (v2):**

1. **WBS 8-80 hour rule adapted for agent tasks:** Each sub-task should represent 8-80 seconds of agent work (the LLM equivalent of person-hours). This is the research corpus's translation of PMI's 8-80 hour rule (item 30: WBS). The decomposition should stop when sub-tasks reach this granularity.

2. **MECE enforcement in the backbrief node:** The backbrief explicitly checks: (a) do any two sub-tasks overlap in scope? (Mutually Exclusive violation); (b) does the set of sub-tasks cover all requirements? (Collectively Exhaustive violation). Any violation routes back to Plan.

3. **MAKER/MDAP maximal decomposition for high-reliability paths:** For tasks where correctness is critical (deployment, data migration, security configuration), the plan node should decompose to the SMALLEST POSSIBLE unit -- MAKER's m=1 principle. The research corpus proves this achieves zero errors at scale (1,048,575 sequential steps with zero failures). The cost is higher (Theta(s ln s) for SPRT voting), so this mode is reserved for the DEEP pipeline path (complex + safety-sensitive tasks).

4. **Dependency DAG with explicit output contracts:** Each sub-task declares not just its dependencies but its OUTPUT SCHEMA. Sub-task B declaring a dependency on A also declares what fields from A's output it consumes. The backbrief node verifies that A's declared output schema actually contains the fields B expects. This catches the most common plan inconsistency: format mismatch between producer and consumer.

### 3.5 Memory and Skill Accumulation

**Current state (v1):** No memory between runs. Each task is independent.

**Recommended state (v2):**

1. **Skill library (episodic memory):** As described in Recommendation 4.1. Stores successful plan templates, research findings, and failure patterns. Queried at plan time for template seeding.

2. **Research cache (semantic memory):** Research findings (web search results, codebase analysis, documentation lookups) persist across tasks with TTL-based expiration. If task B requires the same information that task A researched 10 minutes ago, the research node retrieves from cache rather than re-fetching.

3. **Failure pattern library:** Failed sub-tasks are archived with their failure signatures (tool, error type, context). Before executing a sub-task similar to a previously failed one, the execute node is warned: "This sub-task failed previously with error X. The recovery strategy used then was Y."

4. **Skill accumulation feedback loop:** After each successful task, the synthesizer rates the plan quality (were sub-tasks correctly decomposed? were tools correctly chosen? was the plan efficient?). High-rated plans are promoted in the skill library. Low-rated plans are demoted or annotated with failure modes.

**Storage:** SQLite for v2 MVP. Migrate to vector DB (Chroma/pinecone) for v2.1 when semantic similarity retrieval becomes necessary for a large library. SQLite with keyword matching + tag-based retrieval is sufficient for the first 100-200 plans.

---

## Phase 4: What NOT to Do

### 4.1 Research Findings That Should NOT Be Implemented

These are frameworks from the research corpus that appear promising but are wrong for JORDAN v2.

#### Do NOT: Full MDMP Implementation in the Plan Node

**What this would be:** Replicating the US Army's 7-step MDMP process in full -- Receipt of Mission, Mission Analysis, COA Development, COA Analysis (Wargaming), COA Comparison, COA Approval, Orders Production -- as the plan node's internal process.

**Why not:** MDMP is designed for human staffs working over days to weeks on campaign-level plans. It is too heavy for software development tasks. The full MDMP produces a 5-paragraph OPORD (SMEAC format) which is overengineered for JORDAN's use case. The research corpus correctly identifies that the military framework to map is FRAGO (lightweight, delta-based), not full MDMP.

**What to do instead:** Extract the SPECIFIC MDMP elements that work at JORDAN's scale: (a) multi-COA generation (generate 2-3 alternative approaches, compare, select best); (b) wargaming as plan stress-testing (the pre-mortem node achieves this with lighter weight); (c) commander's decision gate (the approval gate already does this). Do not adopt the full sequential 7-step process.

#### Do NOT: Joint Targeting Cycle (JTC) as Execution Phase Model

**What this would be:** Replacing JORDAN's execute node with the JTC's 6-phase targeting cycle.

**Why not:** The JTC is designed for kinetic targeting (bombs on targets) with legal review, collateral damage estimation, and weaponeering analysis. Phases 3-4 (Target Development, Weaponeering) have no analogue in software task execution. The JTC's Commander's Decision Gate maps well to JORDAN's approval gate (and was identified as such), but the full cycle is military-specific.

**What to do instead:** Adopt the JTC's COMMANDER'S DECISION GATE concept (a single, formal, human-in-the-loop approval point between planning and execution) and the F2T2EA's ASSESS phase (did the action achieve the desired effect? -- this maps to JORDAN's evaluate/synthesize). Leave the rest.

#### Do NOT: OODA Loop as Primary Execution Model

**What this would be:** Replacing JORDAN's Plan-and-Execute architecture with a tight OODA loop (Observe-Orient-Decide-Act cycling continuously).

**Why not:** The OODA loop is designed for tactical, time-competitive, human-in-the-loop decision-making (air combat, where Boyd developed it). It assumes a single decision-maker cycling rapidly. JORDAN tasks are multi-step, multi-tool, with execution latency in seconds-to-minutes per step. The OODA cycle is too fast and too shallow -- "Orient" (the sensemaking hub) does not map cleanly to LLM-based research and planning.

**What to do instead:** Use OODA's insight (continuous reassessment, Orient as the sensemaking hub) but NOT its structure. JORDAN's Plan -> Research -> Risk -> Execute -> Evaluate -> Replan pipeline IS an OODA loop slowed down and deepened for complex software tasks. The OODA insight that "Orient" is the most important phase maps to strengthening JORDAN's Research + Plan nodes, not restructuring the pipeline.

#### Do NOT: Karl's "Abolish the Editor" Recommendation

**What this would be:** Removing the Editor component from JORDAN.

**Why not:** The prior critical review addressed this directly (lines 183-186). The Editor provides real value: persona transformation, user knowledge injection, second-pass quality review. Removing it regresses UX. The Editor's self-identification suppression ("never identify yourself as an AI") is standard LLM prompt practice, not a cover-up.

**What to do instead:** Keep the Editor. Fix the confidence score dead weight (Karl was right about this -- the score is generated, passed around, rarely consumed). Replace the synthetic 0.0-1.0 confidence with concrete risk descriptions. But keep the Editor's quality review and persona functions.

#### Do NOT: Replace LangGraph with Raw LLMCompiler

**What this would be:** Replacing JORDAN's LangGraph-based orchestration with LLMCompiler's parallel function-calling DAG.

**Why not:** LangGraph provides stateful cyclic graphs with checkpoint/resume, conditional routing, and HITL interrupts -- all of which JORDAN uses. LLMCompiler is designed for stateless, single-turn parallel function calling. It has no checkpointing, no conditional routing beyond the initial DAG compilation, and no HITL support. JORDAN's requirements (approval gates, replanning loops, state persistence) require a stateful graph framework.

**What to do instead:** Keep LangGraph. Adopt LLMCompiler's INSIGHT (parallel function calling with dependency tracking) within JORDAN's execute node -- specifically, the parallel executor should use LLMCompiler-style dependency analysis to identify parallelizable tool calls within a sub-task. But the graph orchestration layer stays on LangGraph.

#### Do NOT: Implement SPRT Voting for Every Sub-Task (MAKER/MDAP Full Adoption)

**What this would be:** Applying MAKER/MDAP's SPRT voting mechanism (multiple independent LLM calls per step, continue until one answer leads by k votes) to every JORDAN sub-task.

**Why not:** MAKER/MDAP achieved zero errors on 1,048,575 steps of Towers of Hanoi, but at a cost of ~$3,500 and 3-4 million LLM calls. Applying this to JORDAN's software development tasks would multiply costs by 3-4x per sub-task. The SPRT voting is justified when correctness is ALL-OR-NOTHING (a single wrong move invalidates the entire sequence) and when the correctness criterion is mechanically verifiable (legal moves in Towers of Hanoi). Most JORDAN sub-tasks do not meet either criterion: errors are often recoverable, and correctness of code/output is not mechanically verifiable.

**What to do instead:** Adopt MAKER/MDAP's INSIGHT (decompose to the smallest possible unit for critical tasks) but not its MECHANISM (SPRT voting on every step). Reserve SPRT voting for the narrow class of JORDAN sub-tasks that are (a) correctness-critical, (b) have mechanically verifiable outputs, and (c) are small enough that 3-4x cost multiplier is acceptable. Example: a deployment sub-task that must produce a valid Terraform configuration -- run SPRT voting on the Terraform plan validation step only, not on every sub-task.

### 4.2 Prior Critical Review Findings: Superseded, Modified, Confirmed

#### Findings SUPERSEDED by This Review

| Finding | Superseded By | Reason |
|:--|:--|:--|
| C1 (replan bypasses risk) | Recommendation 1.1 | Fix is specified with exact code change |
| CR1 (parallel strips approval) | Recommendation 1.2 | Fix is specified with exact code change |
| CRT1 (classifier weaponizable) | Recommendation 1.4 | Fix is specified with exact code change |
| H4 (planner skips risk) | Recommendation 1.3 | Fix is specified with exact code change |
| CR2 (parallel no retries) | Recommendation 3.2 | Fix is specified with exact code change |
| C2 (no replan ceiling) | Recommendation 3.3 | Fix is specified with exact code change |

#### Findings MODIFIED by This Review

| Finding | Original Recommendation | Modified Recommendation | Reason |
|:--|:--|:--|:--|
| C3 (resume duplicates graph) | Replace with LangGraph interrupt+Command | Keep current resume paths for v2; defer LangGraph interrupt migration to v2.1 | Risk/reward: interrupt+Command is a major refactor touching the checkpoint system. The current resume paths work for the approval flow. Defer. |
| Karl: "Kill synthetic confidence scores" | Remove entirely | Replace with concrete risk descriptions; keep risk_level enum | The risk_level (LOW/MEDIUM/HIGH) is used throughout the pipeline and works correctly when the classifier is not bypassed. The 0.0-1.0 confidence FLOAT is what should be removed -- it is generated, passed around, and rarely consumed. |
| Karl: "Dismantle central planning" | Full emergent task execution | Incremental evolution toward Commander's Intent distributed execution (Phase 3.2) | Full emergent task execution is a research problem. Commander's Intent pattern is an incremental step that preserves centralized planning while enabling local autonomy. |

#### Findings CONFIRMED by This Review (Status Quo Confirmed by Research)

| Finding | Research Confirmation |
|:--|:--|
| nodes.py is a 4400-line monolith | Confirmed. The architectural debt is real. Wave 3 split into sub-modules is correct. The research corpus provides no framework that justifies keeping a 4400-line monolith. |
| Parallel executor is a second-class citizen | Confirmed and deepened. The research corpus (F2T2EA, MDMP, Commander's Intent) demonstrates that execution discipline applies uniformly regardless of execution method. Parallel mode must have parity with sequential mode. |
| Approval gate is a single point of failure | Confirmed and deepened. The military frameworks (JTC Commander's Decision Gate, MDMP's 3 approval gates, Commander's Intent constraints) demonstrate that defense-in-depth is doctrinal. A single approval point with 4 bypass paths is not security. |
| JORDAN has no memory/skill accumulation | Confirmed and deepened. Voyager/DEPS, A3's knowledge repository, and Theory of Constraints' logical trees all demonstrate the value of persistent memory. JORDAN's amnesia is its most strategically significant architectural gap. |
| Risk classifier default-LOW is wrong | Confirmed by the pre-mortem research: default-optimistic risk assessment fails. The pre-mortem's effectiveness depends on LEGITIMIZING DOUBT -- the exact opposite of JORDAN's default-LOW pattern which suppresses doubt. |

### 4.3 Where Research Confirms Status Quo (Keep As-Is)

These are JORDAN v1 design choices that the research corpus validates as correct -- they should NOT change.

| Design Choice | Research Validation |
|:--|:--|
| Plan-and-Execute architecture (separate planning pass then stepwise execution) | Confirmed by ALAS (Workflow Blueprinting -> Agent Factory -> Runtime Monitor), TAPE (Plan Generation -> Iterative Execution), and military MDMP/JOPP (plan first, execute second). The separation of planning from execution is the correct architecture. The research corpus does not support Karl's "dismantle central planning" recommendation. |
| LangGraph as the orchestration framework | Confirmed by the state of the art. LangGraph's stateful cyclic graphs with checkpoint/resume, conditional routing, and HITL interrupts are the dominant production framework for this class of problem. ALAS's workflow IR compiles to Argo Workflows (Kubernetes-native) -- same concept, different runtime. |
| DAG-based sub-task execution with dependency tracking | Confirmed by ALAS (dependency DAG with explicit edges), LLMCompiler (parallel function calling with dependency tracking), and WBS/CPM (dependency-driven scheduling). The DAG model is correct. The implementation (dict-order-dependent batching, shared state, no retries) is wrong, not the concept. |
| Human-in-the-loop approval for HIGH-risk operations | Confirmed by the entire military corpus: every framework (MDMP, JOPP, JTC, F2T2EA, Thunderforge) has a human approval gate before execution. The concept is correct. The implementation (4 bypass paths, default-LOW, weaponizable classifier) is wrong. |
| Multi-model routing with cost awareness | Confirmed by TAPE (0.5B models for classification, larger models for planning). The principle of routing tasks to appropriately-sized models is correct and cost-effective. The implementation bugs (HR3, HR4, HR6, HR7) are implementation bugs, not design flaws. |

---

## Appendix A: Framework-to-Recommendation Traceability Matrix

| Recommendation | Primary Framework(s) | Secondary Framework(s) | Research Item IDs |
|:--|:--|:--|:--|
| 1.1 Close C1 | MDMP, JOPP | FRAGO | 1, 2, 15 |
| 1.2 Close CR1 | Commander's Intent | Mission Command, F2T2EA | 4, 12 |
| 1.3 Close H4 | JTC Commander's Decision Gate | Red Teaming | 13, 8 |
| 1.4 Close CRT1 | Red Teaming | IPB | 8, 9 |
| 2.1 FRAGO replanning | FRAGO, ALAS | OODA, MDO Convergence | 15, 51, 3, 14 |
| 2.2 Pre-mortem gate | Pre-mortem Analysis | MDMP COA Wargaming, Red Teaming | 25, 1, 8 |
| 2.3 TAPE triage | TAPE, Cynefin | DMAIC | 56, 20, 22 |
| 3.1 Backbrief | Backbriefing + ROC Drill | SMEAC | 10, 6 |
| 3.2 Parallel retry | F2T2EA | JTC | 12, 13 |
| 3.3 Replan ceiling | MDMP | ALAS | 1, 51 |
| 4.1 Skill library | Voyager/DEPS | A3, Theory of Constraints | 46, 23, 26 |

## Appendix B: JORDAN v1 Critical Finding Resolution Status

| Finding | Status After v2 MVP | Resolution |
|:--|:--|:--|
| C1 | FIXED | Recommendation 1.1 |
| C2 | FIXED | Recommendation 3.3 |
| C3 | DEFERRED to v2.1 | LangGraph interrupt migration |
| CR1 | FIXED | Recommendation 1.2 |
| CR2 | FIXED | Recommendation 3.2 |
| CRT1 | FIXED | Recommendation 1.4 |
| H1 (replan misreads approval) | DEFERRED to Wave 2 | Fix in replanning.py:243 |
| H2 (replan skip no-op) | DEFERRED to Wave 2 | Fix in nodes.py:4122+2403 |
| H3 (direct-response bypasses risk) | PARTIALLY ADDRESSED | TAPE triage formalizes the fast path but must include lightweight risk check |
| H4 | FIXED | Recommendation 1.3 |
| H5 (caption state collision) | DEFERRED to Wave 3 | Namespace by (workflow_id, run_id) |
| H6 (uncertainty markers) | PARTIALLY ADDRESSED | FRAGO replanning uses structured evaluation, not keyword matching |
| H9-H12 (parallel executor bugs) | PARTIALLY ADDRESSED | Recommendations 1.2 and 3.2 fix the highest-impact bugs; Wave 3 fixes rest |
| HR1 (default-to-LOW) | FIXED | Recommendation 1.4 |
| HR2 (first-match-wins) | PARTIALLY ADDRESSED | Recommendation 1.4 separates system/user matching; full fix in Wave 3 |
| S1-S10 | DEFERRED to Wave 3 | Checkpointer leak, model retry dedup, error dispatch |
| MR7 (approval split-brain) | DEFERRED to Wave 2 | Persistent store must be source of truth |

## Appendix C: Cost Estimate

| Wave | Tasks | Lines Changed | Hours | Cumulative |
|:--|:--|:--|:--|:--|
| Wave 1 (Security) | 4 approval gate fixes | ~82 | 2 | 2 hours |
| Wave 2 (Correctness + New Nodes) | FRAGO, pre-mortem, triage, retry, ceiling | ~955 | 17 | 19 hours |
| Wave 3 (Architecture) | Backbrief, skill library, module splits, dead code | ~1,430 | 14 | 33 hours |

These are implementation estimates only. They do not include:
- Testing and validation (add 50% for thorough test coverage)
- Documentation updates
- Code review cycles
- Integration testing across all three pipeline paths (fast, standard, deep)

A realistic total for v2 MVP (Waves 1+2): **~30 engineering hours** including testing.

---

**End of tactical review.** Every recommendation is backed by specific evidence from the 61-framework research corpus or the JORDAN v1 critical review. No recommendation is made without a documented framework mapping, a concrete implementation sketch, and a risk assessment with mitigation.
