# JORDAN v2 Granular Implementation Specification -- REVISION v2

**Author:** Richard the Lionheart (Claude Code)
**Date:** 2026-05-25
**Status:** Revision responding to Karl critique (karl-critique-01.md)
**Based on:** BRIEFING.md (agreements, prohibitions, resolutions), richard-draft-01.md (original draft), karl-critique-01.md (dialectical critique)

---

## How to Read This Document

This is a **complete revision** of richard-draft-01.md incorporating Karl's 45 identified gaps, 8 structural tension resolutions, and 3 critical issue decisions. The structure mirrors the original draft's 9-subsection-per-node template for consistency.

**Change tracking:**
- `[KARL-ACCEPTED]` mark = Karl's critique was correct; spec is fixed.
- `[KARL-COUNTER]` mark = Karl's critique is disputed; explanation provided.
- `[DESIGN-DECISION]` mark = An architectural decision was required and has been made.
- `[ARBITRATION-REQUIRED]` mark = A disagreement that cannot be resolved without human input.
- `[NEW]` mark = Material added in response to a gap Karl identified.

---

## Table of Contents

1. [CLASSIFY (classifier.py)](#1-classify-classifierpy)
2. [FAST EXECUTE (executor.py)](#2-fast-execute-executorpy)
3. [PLAN (planner.py)](#3-plan-plannerpy)
4. [BACKBRIEF (backbrief.py)](#4-backbrief-backbriefpy)
5. [RESEARCH (synthesizer.py)](#5-research-synthesizerpy)
6. [RISK ASSESSMENT (guardrails.py)](#6-risk-assessment-guardrailspy)
7. [PREMORTEM (premortem.py)](#7-premortem-premortempy)
8. [BRANCHING FACTOR MONITOR (branching_monitor.py)](#8-branching-factor-monitor-branching_monitorpy)
9. [APPROVAL GATE (guardrails.py)](#9-approval-gate-guardrailspy)
10. [EXECUTE (executor.py)](#10-execute-executorpy)
11. [SYNTHESIZE (synthesizer.py)](#11-synthesize-synthesizerpy)
12. [EVALUATE (evaluate.py)](#12-evaluate-evaluatepy)
13. [REPLAN (replanner.py)](#13-replan-replannerpy)
14. [SKILL LIBRARY (skill_library.py)](#14-skill-library-skill_librarypy)
15. [Cross-Cutting: SIMPLE CHAT](#a-simple-chat)
16. [Cross-Cutting: KNOWLEDGE/SCOPE GAPS](#b-knowledgescope-gaps)
17. [Cross-Cutting: PLANNING DEAD-ENDS](#c-planning-dead-ends)
18. [Cross-Cutting: PRODUCTION EDGE CASES](#d-production-edge-cases)
19. [Structural Tension Resolutions](#structural-tension-resolutions)
20. [Design Decisions and Audit Trail](#design-decisions-and-audit-trail)

---

## Executive Summary of Changes from v1

### Three Critical Issue Resolutions

**Critical Issue 1: Isolated-State Executor vs. LangGraph Shared State**
`[DESIGN-DECISION: LANGGRAPH_SUBGRAPHS]` -- Chosen over private-dict workaround. Each sub-task executes as an independent LangGraph Subgraph with its own reduced state schema and independent checkpointing. The parent EXECUTE node uses `Send()` to fan out to Subgraphs and a `Join` node to collect results. Rationale: true checkpoint isolation is the only way to guarantee the parallel safety claim (fixing H9, H11, H12). The private-dict workaround loses state on interrupt/resume, which breaks the safety invariant. Full specification below in section 10.

**Critical Issue 2: FRAGO Loop Validation Gap**
`[DESIGN-DECISION: FRAGO_DELTA_VALIDATION]` -- The FRAGO replan loop (REPLAN -> RISK -> EXECUTE -> SYNTHESIZE -> EVALUATE) now includes a lightweight three-step validation on every delta plan: (a) structural consistency check (DAG cycle/broken-reference check -- algorithmic, sub-millisecond), (b) risk delta check (re-classify changed sub-tasks only, which RISK ASSESSMENT already does), (c) branching factor check on the delta's DAG. These three checks replace the full BACKBRIEF/PREMORTEM/BRANCHING-MONITOR re-run. The full re-run is skipped for performance, but structural integrity is guaranteed. Full specification in section 13.7.

**Critical Issue 3: Unreconciled Risk Signals**
`[DESIGN-DECISION: RISK_FUSION]` -- A risk fusion step is introduced between PREMORTEM and APPROVAL. It reconciles four independent risk signals: CLASSIFY complexity_factors, RISK ASSESSMENT risk_levels, PREMORTEM failure_scenario severities, and BRANCHING MONITOR halt_flag. The reconciliation rule: `final_risk[sub_task] = max(RISK_ASSESSMENT.risk_levels[sub_task], max(PREMORTEM.scenarios_for[sub_task].severity, default=LOW), escalate_if_classify_domain_safety_critical, escalate_if_branching_halt)`. This produces a single reconciled risk level per sub-task presented in the APPROVAL briefing, with the individual assessments retained for drill-down. Full specification in section 9.10 (new).

### Structural Tension Resolutions (8 Tensions)

| Tension | Resolution |
|---------|------------|
| 1. PLAN revision vs. REPLAN delta naming | Distinct terminology: PLAN re-entry = "regeneration" (full plan with flags); REPLAN = "delta replanning" (minimal modification). Graph-level assertions prevent cross-routing. |
| 2. BACKBRIEF+PREMORTEM shared counter | Separated into `backbrief_revision_count` and `premortem_cycle_count`, each with independent max-2 ceilings. |
| 3. Isolated-state vs. shared state | LangGraph Subgraphs chosen. See Critical Issue 1. |
| 4. Denylist as regex-classifier | Explicitly defined as "safety pre-filter" architecturally distinct from classification. Auditable logging on every match. |
| 5. Knowledge gaps flow | Pre-execution gap severity gate added. HIGH-severity gaps (affecting HIGH/CRITICAL sub-tasks) trigger Level 3 escalation before EXECUTE. |
| 6. PREMORTEM/RISK ASSESSMENT reconciliation | Risk fusion step added. See Critical Issue 3. |
| 7. BACKBRIEF/PREMORTEM returning to PLAN -- no state tracking | Plan versioning added: `plan_version: int` (incremented on every regeneration), `plan_checksum: str` (hash of plan content). |
| 8. SQLite contention under load | Write-ahead queue added: in-memory queue drained by background writer. Eliminates silent write drops. |

---

## 1. CLASSIFY (classifier.py)

### 1.1 FUNCTION & RATIONALE

Unchanged from v1. Performs TAPE-inspired triage at pipeline entry to determine which of three execution paths (FAST, STANDARD, DEEP) the incoming request follows. Conservative classifier bias: any uncertainty escalates UP. This node is the sole gatekeeper for pipeline path selection.

### 1.2 FILE & LOCATION

Unchanged from v1.

### 1.3 INPUT & 1.4 OUTPUT

Unchanged from v1.

### 1.5 EDGE CASES

**v1 edge cases retained** with the following additions:

`[KARL-ACCEPTED] [NEW]` **Edge case 1.5.A -- Denylist false-positive feedback loop:**
When the denylist triggers and the pipeline subsequently completes successfully (the escalated STANDARD/DEEP path produces a valid, safe result), the triggering pattern and input are recorded in the skill library as a false-positive candidate. Specifically: after EVALUATE returns SUCCESS for a pipeline that was escalated from FAST due to denylist trigger, the CLASSIFY node appends `triggered_pattern`, `input_excerpt`, and `pipeline_outcome = SUCCESS` to a `denylist_false_positive_log` table in the skill library. This log is reviewed (either manually or via automated periodic analysis) to tune denylist patterns. High-frequency false-positive patterns (triggered >5 times with SUCCESS outcome) are automatically flagged for denylist removal.

`[KARL-ACCEPTED] [NEW]` **Edge case 1.5.B -- Denylist update mechanism:**
The denylist pattern list is **hot-reloadable** at runtime, not requiring a restart. The `DenylistConfig` object watches its configuration file for changes via `inotify` (Linux) or `watchdog` (cross-platform). When a change is detected, new patterns are compiled and atomically swapped with the old list. Concurrent pipeline invocations see either the old list (started before the swap) or the new list (started after), never a partial update. The update mechanism itself has an edge case guard: if any pattern in the updated list fails to compile, the entire update is rejected and the old list is retained. A warning is logged.

`[KARL-ACCEPTED] [NEW]` **Edge case 1.5.C -- Denylist disagreement with LLM classifier logged and fed back:**
When the LLM classifier classifies as FAST but the denylist escalates (i.e., LLM says FAST, denylist says escalate), the disagreement is logged to a `classification_disagreement_log` in the skill library. Each entry records: `input_excerpt`, `llm_classification` (FAST), `denylist_pattern_triggered`, `pipeline_outcome` (after escalation), and `outcome_assessment` (from EVALUATE). This log feeds into both (a) denylist tuning (patterns with high disagreement + SUCCESS outcome are false-positive candidates) and (b) LLM classifier tuning (patterns missed by the LLM but caught by the denylist are training data for the LLM classifier).

### 1.6 INTERFACES

Unchanged from v1, with added methods:

```python
[NEW]
class DenylistConfig:
    patterns: list[Pattern]
    config_path: str  # For hot-reload watching
    watch_interval_seconds: float = 5.0

    def reload_if_changed(self) -> bool:
        """Check config file mtime and atomically reload if changed."""
        ...

    def log_false_positive(
        self,
        pattern: str,
        input_excerpt: str,
        outcome: str,
    ) -> None:
        """Record a potential false positive for tuning."""
        ...
```

### 1.7 INTERACTIONS

Unchanged from v1.

### 1.8 FAST PATH & 1.9 INTEGRATION RISK

Unchanged from v1.

---

## 2. FAST EXECUTE (executor.py)

### 2.1 FUNCTION & RATIONALE

Lightweight execution path for trivial queries. v2 adds a **lightweight output guardrail** before passing results to SYNTHESIZE, addressing Karl's identified bypass.

### 2.2 FILE & LOCATION

Unchanged from v1.

### 2.3 INPUT & 2.4 OUTPUT

Unchanged from v1.

### 2.5 EDGE CASES

`[KARL-ACCEPTED] [NEW]` **Edge case 2.5.A -- Post-hoc output guardrail for FAST path:**
Before FAST EXECUTE passes its response to SYNTHESIZE, it runs a lightweight rule-based scan on the output. The scan checks for:
1. **Dangerous content patterns:** Instructions for harmful acts, weapon creation, self-harm, illegal activities. Uses a compact keyword + regex pattern set (separate from the input denylist -- the output guardrail checks different patterns).
2. **Tool-call hallucination detection:** Scans the output for known tool-call formatting patterns (JSON function-call blobs, XML `<function>` tags, special tokens like `<|python_tag|>`). If a tool-call format is detected, the response is **not passed through** -- it is replaced with a safe fallback: "I encountered an issue generating a response. Please try rephrasing your question." The hallucination is logged to the skill library's `hallucination_log`.
3. **Safety refusal detection:** If the model refuses to answer with a safety refusal ("I can't answer that", "I'm not allowed to", "As an AI, I cannot..."), the response is flagged with `output_guardrail_flagged = True`. Unlike dangerous content, a refusal is passed through to the user (it is a legitimate model behavior), but the metadata flag is available for SYNTHESIZE to append an explanatory note.

`[KARL-ACCEPTED] [NEW]` **Edge case 2.5.B -- Tool-call hallucination definition across model APIs:**
The output guardrail detects tool-call hallucinations by scanning for these concrete output formats:
- **Anthropic Claude tool_use blocks:** JSON with `type: "tool_use"`, `name`, `input` fields. Detected via JSON parse attempt + field check.
- **OpenAI function call format:** JSON with `function_call` or `tool_calls` keys. Detected via JSON parse attempt + field check.
- **DeepSeek function call format:** JSON with `function_call` field in the `choices[0].message` structure. Detected via JSON parse attempt.
- **XML-style function tags:** `<function=name>args</function>`, `<invoke><tool>name</tool></invoke>`. Detected via regex.
- **Special tokens:** Known API-specific tokens (e.g., `<|python_tag|>`, `[TOOL_CALL]`). Detected via exact string match.

If ANY of these patterns are detected, the response is intercepted and replaced with the safe fallback. The detection is intentionally broad (favor false positive over false negative), consistent with the system's conservative bias.

`[KARL-ACCEPTED] [NEW]` **Edge case 2.5.C -- Factual disclaimer appended to all FAST responses:**
All FAST path responses have a disclaimer appended: "This is a quick answer generated without research or tool access. For complex topics requiring verification or deeper analysis, I can run a full investigation." The disclaimer is configurable (can be shortened or removed per environment). This addresses Karl's concern about confidently-wrong answers on the FAST path -- the user is explicitly warned that the answer may not be fully researched.

`[KARL-ACCEPTED] [NEW]` **Edge case 2.5.D -- Safety refusal differentiated from uncertainty:**
The uncertainty detector (v1) scanned for hedging phrases ("I think", "maybe", "I'm not sure"). v2 adds a second scan for **safety refusal phrases**: "I can't answer", "I'm not allowed", "I cannot provide", "As an AI", "I apologize, but I cannot". These are distinct from hedging: a safety refusal means the model actively declined to answer. When detected, the response is flagged with `safety_refusal_detected = True`. This flag is available for SYNTHESIZE to potentially escalate (e.g., if the refusal appears incorrect for the query, flag for review). The refusal is still passed to the user.

### 2.6 INTERFACES

Additions to v1:

```python
[NEW]
@dataclass
class OutputGuardrailResult:
    passed: bool
    dangerous_content_detected: bool
    tool_call_hallucination_detected: bool
    safety_refusal_detected: bool
    intercepted: bool  # True if output was replaced with fallback

class OutputGuardrail:
    """Lightweight rule-based output scan for FAST path."""
    def scan(self, output: str) -> OutputGuardrailResult:
        ...
```

`[KARL-COUNTER]` **Karl's claim:** "FAST EXECUTE has no output guardrail. An acknowledged bypass is still a bypass."
**Resolution:** v1 acknowledged the gap but did not close it. v2 closes it with the output guardrail defined above (Edge case 2.5.A, 2.5.B, 2.5.C, 2.5.D). The guardrail is rule-based (not LLM-based) to preserve the FAST path's latency profile, but it covers the three specific failure modes Karl identified: dangerous content, tool-call hallucination, and confident incorrectness (via the factual disclaimer).

### 2.7 INTERACTIONS & 2.8 FAST PATH & 2.9 INTEGRATION RISK

Updated to reference the output guardrail as a mandatory step before SYNTHESIZE.

---

## 3. PLAN (planner.py)

### 3.1 FUNCTION & RATIONALE

`[KARL-ACCEPTED]` Key change from v1: PLAN re-entry (from BACKBRIEF or PREMORTEM) is now explicitly called **"regeneration"** -- it produces a FULL new plan based on the previous plan plus revision flags. This is architecturally distinct from REPLAN's **"delta replanning"** which produces only modified sub-tasks. The distinction is enforced at the graph level: PLAN must never receive `state.replan_count > 0`; REPLAN must never receive `state.premortem_cycle_count > 0` without `state.sub_task_results` populated.

### 3.2 FILE & LOCATION

Unchanged.

### 3.3 INPUT

`[KARL-ACCEPTED] [NEW]` Added `pipeline_phase: str` field to input:

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `pipeline_phase` | `Literal["planning", "backbrief_revision", "premortem_revision"]` | Graph state | What phase the pipeline is in. PLAN asserts this is one of the valid phases for entry. |

### 3.4 OUTPUT

`[KARL-ACCEPTED] [NEW]` Added `plan_version: int` and `plan_checksum: str` to output:

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `plan_version` | `int` | All downstream nodes | Incremented on every regeneration. Starts at 1. |
| `plan_checksum` | `str` | All downstream nodes | SHA-256 hash of plan content (commander_intent + sub_tasks + DAG). Used by PREMORTEM to detect plan changes. |
| `plan_source` | `str` | Audit | `"fresh"`, `"skill_template"`, `"backbrief_revision"`, or `"premortem_revision"` |

### 3.5 EDGE CASES

`[KARL-ACCEPTED] [NEW]` **Edge case 3.5.A -- `pipeline_phase` is a concrete state field (no longer a dangling reference):**
The state field `PipelineState.pipeline_phase` is defined as `Optional[Literal["planning", "backbrief_revision", "premortem_revision", "research", "risk_assessment", "premortem", "branching", "approval", "execution", "synthesis", "evaluation", "replanning"]]`. It is set when the graph enters each phase and cleared on pipeline completion. PLAN's `plan()` method checks that `pipeline_phase` is either `"planning"` (first pass) or `"backbrief_revision"` / `"premortem_revision"` (re-entry). If any other phase is detected, PLAN raises `InvalidPhaseError`.

`[KARL-ACCEPTED] [NEW]` **Edge case 3.5.B -- Plan versioning and checksum:**
The `Plan` dataclass now includes a `plan_version: int` field (incremented on every regeneration) and `plan_checksum: str` (SHA-256 of canonical JSON encoding of plan content). PREMORTEM stores `failure_scenarios` keyed by `plan_checksum`. When a new plan arrives (plan_checksum differs from previous), PREMORTEM archives old scenarios and starts fresh. When `plan_checksum` is identical (trivially regenerated), PREMORTEM reuses existing scenarios. This prevents scenario accumulation across different plan versions.

`[KARL-ACCEPTED] [NEW]` **Edge case 3.5.C -- Skill library feedback on rejected templates:**
When a plan seeded from a skill library template is rejected by BACKBRIEF or triggers a fatal PREMORTEM finding, the template's `failure_count` is incremented and its `last_failure_reason` is updated in the skill library. If a template accumulates `max_failures_before_deprioritization` (configurable, default 3) failures from BACKBRIEF or PREMORTEM, its `priority_boost` is set to `-1.0` (effectively deprioritized -- only used if no other template matches). This prevents the same flawed template from repeatedly contaminating plan generation.

### 3.6 INTERFACES

Updated `Plan` dataclass:

```python
[NEW] @dataclass
class Plan:
    commander_intent: CommanderIntent
    sub_tasks: list[SubTaskDef]
    dag: dict[str, list[str]]  # adj list: sub_task_id -> [dependent_ids]
    plan_version: int  # [NEW] Incremented on every regeneration
    plan_checksum: str  # [NEW] SHA-256 of canonical JSON content
    metadata: dict
```

### 3.7 INTERACTIONS

`[KARL-ACCEPTED]` Updated terminology:
- "Re-entry from BACKBRIEF" is now "Regeneration triggered by BACKBRIEF flags".
- "Re-entry from PREMORTEM" is now "Regeneration triggered by PREMORTEM fatal flags".
- The graph-level assertion is documented: `assert state.replan_count == 0, "PLAN cannot be re-entered during FRAGO replan loop"`.

### 3.8 FAST PATH & 3.9 INTEGRATION RISK

Unchanged from v1.

---

## 4. BACKBRIEF (backbrief.py)

### 4.1 FUNCTION & RATIONALE

`[KARL-ACCEPTED]` Key change: BACKBRIEF's revision counter (`backbrief_revision_count`) is now **independent** from PREMORTEM's cycle counter (`premortem_cycle_count`). Each has a max of 2 independent iterations. The combined worst case is 4 iterations (2 BACKBRIEF + 2 PREMORTEM), but structural soundness is never sacrificed for cycle counting convenience.

The rationale text is updated: BACKBRIEF now runs **after** PLAN (which is before RESEARCH), not "before resources are committed" (that phrasing was misleading -- BACKBRIEF is a structural check, not a resource check).

### 4.2 FILE & LOCATION

Unchanged.

### 4.3 INPUT

`[KARL-ACCEPTED]` `revision_count` renamed to `backbrief_revision_count`:

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `backbrief_revision_count` | `int` | Graph state | Current BACKBRIEF revision number (0 for first pass). Independent from PREMORTEM cycle count. |

### 4.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `backbrief_revision_count` | `int` | Graph state | Incremented if revision needed (if passed, NOT incremented). |

### 4.5 EDGE CASES

`[KARL-ACCEPTED]` Revision ceiling updated for independent counter:
- If `backbrief_revision_count >= 2` and BACKBRIEF still flags: force-pass (override to accept the plan).
- After force-pass, annotate plan metadata with `backbrief_forced: true`.

`[KARL-ACCEPTED] [NEW]` **Edge case 4.5.A -- `backbrief_forced` flag has a defined consumer:**
`plan.metadata["backbrief_forced"] = True` is consumed by:
1. **APPROVAL GATE:** The structured briefing includes a banner: "Plan structually forced through backbrief ceiling -- DAG may contain unresolved issues."
2. **PREMORTEM:** The forced flag is passed as additional persona context: "This plan was forced through structural verification. Pay special attention to structural issues."
3. **EVALUATE:** The evaluation includes a note: "Plan had unresolved structural issues at backbrief time."
4. **AUDIT TRAIL:** `backbrief_forced` is recorded in the audit entry.

`[KARL-ACCEPTED] [NEW]` **Edge case 4.5.B -- Delta-aware re-verification:**
When BACKBRIEF re-runs on a revised plan (regeneration), it does NOT re-verify the entire plan from scratch. Instead:
- If `plan_source == "backbrief_revision"` or `plan_source == "premortem_revision"`:
  1. Compute the diff between old `plan_checksum` and new `plan_checksum`.
  2. Only re-check DAG portions that changed (sub-tasks whose IDs appear in the diff, plus their direct neighbors in the DAG).
  3. Only re-run DSM analysis on sub-task pairs where at least one sub-task changed.
- If `plan_source == "fresh"` or `plan_source == "skill_template"`: full verification as in v1.
This delta-aware approach reduces redundant work and prevents re-flagging of unchanged portions.

`[KARL-ACCEPTED] [NEW]` **Edge case 4.5.C -- DSM heuristics defined (pseudocode):**
The DSM hidden-coupling detection algorithm is no longer hand-waved. Here is the decision tree:

```
For each pair of sub-tasks (A, B) that do NOT share a declared dependency:
  1. TOOL OVERLAP: If A.tools_required ∩ B.tools_required is non-empty:
     - If the shared tool has a write/delete/update operation: flag HIGH coupling.
     - If the shared tool is read-only: flag LOW coupling.
  2. RESOURCE OVERLAP: Parse A.description and B.description for:
     - Shared file paths (regex: /[\w/.-]+): if files overlap, flag MEDIUM coupling.
     - Shared domain names or service names: if overlapping, flag MEDIUM coupling.
     - Shared environment variable names: if overlapping, flag MEDIUM coupling.
  3. TEMPORAL OVERLAP: If both sub-tasks have isolation_key set to the same value:
     - PLAN already enforces sequential execution. Flag as DECLARED (not hidden).
  4. SCORE:
     - coupling_severity = (high_count * 1.0 + medium_count * 0.5 + low_count * 0.2) / total_possible
     - If coupling_severity > 0.3: flag as hidden coupling requiring review.
     - If coupling_severity > 0.7: flag as structural coupling suggesting merge.
```

This algorithm is encoded in `_analyze_dsm()` and operates on the sub-task definitions directly. It does not require runtime traces or external system access -- purely plan-text-based.

### 4.6 INTERFACES

Unchanged from v1, except `revision_count` renamed to `backbrief_revision_count` in all signatures.

### 4.7 INTERACTIONS

Rewritten for independent counters:

- **Triggered by:** PLAN (after initial plan generation or after regeneration).
- **Triggers:**
  - On `passed == True`: RESEARCH node (proceed to research phase).
  - On `passed == False` and `backbrief_revision_count < 2`: PLAN (regeneration with backbrief_flags as additional context).
  - On `passed == False` and `backbrief_revision_count >= 2`: force-pass, proceed to RESEARCH. Log "Backbrief ceiling reached -- plan accepted with flags."
- **Re-entry from PREMORTEM:** When PREMORTEM triggers plan regeneration, BACKBRIEF must re-run on the regenerated plan. The `backbrief_revision_count` is independent from `premortem_cycle_count`. If `backbrief_revision_count < 2`, the regenerated plan MAY be rejected again by BACKBRIEF independently from PREMORTEM's cycle count.
- **Priority rule:** If BACKBRIEF passes AND PREMORTEM finds fatal flaws, the regeneration is triggered by PREMORTEM. If BACKBRIEF rejects (regardless of PREMORTEM state), the regeneration is triggered by BACKBRIEF. PREMORTEM's semantic analysis overrides BACKBRIEF's structural analysis for the purpose of triggering regeneration, but BACKBRIEF must independently verify the regenerated plan.

### 4.8 FAST PATH & 4.9 INTEGRATION RISK

Updated to reference the DSM heuristics defined in 4.5.C and the independent counter design.

---

## 5. RESEARCH (synthesizer.py)

### 5.1 FUNCTION & RATIONALE

`[KARL-ACCEPTED]` Karl is correct: this node is named "RESEARCH" but it is a cache lookup. v2 renames the internal semantics while keeping the node name for consistency with the architecture diagram. The node's function description is updated:

"Queries the skill library's research cache for information relevant to the planned task. **This is primarily a cache lookup, not an independent research engine.** Uses TTL-based caching: results expire after a configurable period."

The key behavioral change: RESEARCH **does** validate cache results against the current tool registry before returning them. This addresses Karl's tool-deprecation concern.

### 5.2 FILE & LOCATION

Unchanged.

### 5.3 INPUT

Unchanged from v1, but with added tool registry input:

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `tool_registry` | `ToolRegistry` | Cross-cutting | [NEW] Validates that cached tool_recommendations reference currently available tools. |

### 5.4 OUTPUT

Unchanged from v1, but with clarification: `knowledge_gaps` now has two sub-types:

| Field | Type | Description |
|-------|------|-------------|
| `knowledge_gaps` | `list[KnowledgeGap]` | Areas where information is insufficient. Each gap has a `type: Literal["cache_miss", "genuine_gap"]` field. `cache_miss` = no cached data found (may be fillable by LLM). `genuine_gap` = cache miss AND LLM context also uncertain. |

### 5.5 EDGE CASES

`[KARL-ACCEPTED] [NEW]` **Edge case 5.5.A -- Tool-availability validation on cache results:**
Before returning `tool_recommendations`, RESEARCH cross-references each recommended tool against the tool registry. If a tool is deprecated or removed, the recommendation is stripped and a warning is logged. The research results are marked with `tool_recommendations_validated: True` and `stale_tool_recommendations_removed: int` (count of removed stale recommendations).

`[KARL-ACCEPTED] [NEW]` **Edge case 5.5.B -- Early escalation for significant knowledge gaps:**
If `knowledge_gaps` contains entries with type `"genuine_gap"` AND the affected domain is relevant to sub-tasks classified as HIGH or CRITICAL risk, RESEARCH triggers a **pre-execution gap escalation**. The pipeline pauses at RESEARCH with an interrupt to the user: "I need more information before I can proceed with this task: [list of gaps]. Can you provide this information?" The user responds, and the pipeline resumes from RESEARCH with the added context. This avoids wasting EXECUTE tokens on a task doomed by missing information.

`[KARL-ACCEPTED] [NEW]` **Edge case 5.5.C -- Stale-but-incorrect cache detection (not just TTL):**
In addition to TTL-based staleness, RESEARCH performs a lightweight sanity check on cache results: it sends the cache entry's finding summary to a cheap LLM call with the question "Does this finding appear consistent with current knowledge? Answer YES or NO and briefly explain." If the LLM responds NO, the cache entry is flagged as `suspected_incorrect: True` and returned with a warning. The cache entry is also marked for review (re-cache on next successful pipeline). This is an optional check (configurable, default: enabled for HIGH/CRITICAL domains only, disabled for general domains).

### 5.6 INTERFACES

```python
[NEW]
@dataclass
class KnowledgeGap:
    domain: str
    description: str
    gap_type: Literal["cache_miss", "genuine_gap"]
    affected_sub_tasks: list[str]
    severity: Literal["low", "medium", "high"]  # [NEW]
```

### 5.7 INTERACTIONS

Updated with pre-execution gap escalation: if early escalation is triggered (5.5.B), the graph pauses at RESEARCH with an interrupt, waits for user input, and resumes from RESEARCH with the user-provided context.

### 5.8 FAST PATH & 5.9 INTEGRATION RISK

Updated to reflect the tool-availability validation and sanity-check additions.

---

## 6. RISK ASSESSMENT (guardrails.py)

### 6.1 FUNCTION & RATIONALE

`[KARL-ACCEPTED]` Added explicit documentation of the **plan-text limitation**: "The LLM-based risk classifier operates on plan text (sub-task descriptions, tools_required, dependencies), not on actual tool execution traces. It classifies what the PLAN describes, not what will actually happen during execution. This is an architecturally-significant limitation: the classifier has context awareness POTENTIAL but is constrained by the planner's description fidelity."

### 6.2 FILE & LOCATION

Unchanged.

### 6.3 INPUT

`[KARL-ACCEPTED] [NEW]` On replan, RISK ASSESSMENT now receives the correct `knowledge_gaps`:

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `knowledge_gaps` | `list[KnowledgeGap]` | RESEARCH (or RESEARCH cache snapshot on replan) | On replan, RESEARCH is re-queried (not bypassed). Changed to: RESEARCH is re-queried for cache lookup only (no early escalation, no LLM context gathering). This provides current knowledge_gaps without the overhead of full RESEARCH re-execution. |

### 6.4 OUTPUT

Unchanged from v1.

### 6.5 EDGE CASES

`[KARL-ACCEPTED] [NEW]` **Edge case 6.5.A -- Changed sub-task diff algorithm defined by decision table:**
The diff algorithm for identifying "changed sub-tasks" on replan is precisely specified:

| Change Type | Re-classify? | Rationale |
|-------------|-------------|-----------|
| `sub_task.id` changed (renumbering only) | NO | Identity change, not semantic change |
| `sub_task.description` changed | YES | The action or approach changed |
| `sub_task.tools_required` changed | YES | Different tools have different risk profiles |
| `sub_task.dependencies` changed (added/removed dep) | YES | More deps = more failure modes |
| `sub_task.dependencies` changed (reorder only) | NO | Ordering doesn't affect risk |
| `sub_task.domain` changed | YES | Different domain = different risk context |
| `sub_task.isolation_key` changed | NO | Execution ordering change doesn't change risk |
| `sub_task.risk_level` changed (carried forward) | NO | Already classified |
| New sub-task added | YES | Must classify from scratch |
| Sub-task deleted | N/A | No classification needed |

This decision table is implemented in `_diff_sub_tasks()`.

`[KARL-ACCEPTED] [NEW]` **Edge case 6.5.B -- Minimum batch coherence for classification:**
The batch classification groups sub-tasks by **DAG proximity** (sub-tasks within 2 hops of each other in the DAG are batched together), not by arbitrary ordering. This ensures that context-aware classification has access to neighboring sub-task context. If a batch exceeds 10 sub-tasks, it is split along DAG proximity boundaries (not arbitrary splits). Lone sub-tasks with no nearby neighbors are classified individually.

`[KARL-ACCEPTED] [NEW]` **Edge case 6.5.C -- On replan, knowledge_gaps are refreshed:**
RESEARCH is NOT fully re-executed on replan (matching in v1's FRAGO loop), but RESEARCH's cache query IS re-executed. This means `knowledge_gaps` on replan reflects any new cache entries that were written between the first pass and the replan (e.g., another pipeline cached relevant research in the meantime). This is a lightweight SQL query -- no LLM calls, no early escalation. The `knowledge_gaps` returned are current as of the replan time, not stale from the first pass.

### 6.6 INTERFACES

Updated `RiskAssessmentNode` to include the diff algorithm as a helper method:

```python
[NEW]
def _diff_sub_tasks(
    old: list[SubTaskDef],
    new: list[SubTaskDef],
) -> set[str]:
    """Return set of sub-task IDs that changed between old and new plans.
    
    Uses the decision table in Edge Case 6.5.A to determine which
    changes trigger re-classification.
    """
    ...
```

### 6.7 INTERACTIONS

Updated to show the RESEARCH cache re-query on replan:

- **On replan (FRAGO loop):** REPLAN -> RESEARCH (cache re-query only) -> RISK ASSESSMENT (re-classify only changed sub-tasks using refreshed knowledge_gaps) -> EXECUTE.

### 6.8 FAST PATH & 6.9 INTEGRATION RISK

Unchanged.

---

## 7. PREMORTEM (premortem.py)

### 7.1 FUNCTION & RATIONALE

`[KARL-ACCEPTED]` Critical language fix: PREMORTEM is now consistently described as a **GATE** (not advisory). The v1 language was contradictory. The corrected position:

"PREMORTEM is a mandatory gate. If fatal flaws are found (severity HIGH+ and likelihood > 50%), the pipeline routes back to PLAN for regeneration, then BACKBRIEF re-runs. Max 2 pre-mortem cycles. **Exception:** if ALL persona LLM calls fail (not just some), PREMORTEM cannot produce scenarios and is force-passed with a critical log alert. This is a system-health failure, not an advisory opt-out."

### 7.2 FILE & LOCATION

Unchanged.

### 7.3 INPUT

`[KARL-ACCEPTED]` Now receives `plan_checksum` for version-aware analysis:

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `plan_checksum` | `str` | PLAN | [NEW] SHA-256 hash of plan content. Used to detect plan changes between cycles. |

### 7.4 OUTPUT

`[KARL-ACCEPTED]` `premortem_cycle_count` is now independent from BACKBRIEF's counter. The cycle counter field is renamed:

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `premortem_cycle_count` | `int` | Graph state | Incremented if fatal flags found. Independent from `backbrief_revision_count`. |

### 7.5 EDGE CASES

`[KARL-ACCEPTED] [NEW]` **Edge case 7.5.A -- Plan-versioned scenario storage:**
PREMORTEM stores `failure_scenarios` keyed by `plan_checksum`. When a new plan arrives with a different checksum, old scenarios are **archived** (not appended). The archive records: `plan_version`, `plan_checksum`, `scenarios`, `timestamp`, `cause_of_regeneration` (which persona found what). APPROVAL briefing can display the revision history if desired.

`[KARL-ACCEPTED] [NEW]` **Edge case 7.5.B -- Reconciliation with RISK ASSESSMENT:**
Per the DESIGN DECISION on risk fusion (section 9.10), PREMORTEM's `failure_scenarios` severities are reconciled with RISK ASSESSMENT's `risk_levels` in a risk fusion step before APPROVAL. The exact mechanism: `final_risk[sub_task] = max(RISK_ASSESSMENT.risk_levels[sub_task], max(PREMORTEM.scenarios_for[sub_task].severity, default=LOW))`. See section 9.10 for full specification.

`[KARL-ACCEPTED] [NEW]` **Edge case 7.5.C -- Persona calibration tracking:**
Each persona's false-positive rate is tracked over time. A false-positive is defined as: persona flags as fatal, plan is revised, and the revised plan passes EVALUATE with SUCCESS AND the original plan would also have passed (determined by re-evaluating the original plan's output -- only done in audit/review, not in production). Calibration data is stored in the skill library's `persona_calibration` table:
- `persona_name`, `total_flags`, `fatal_flags`, `false_positive_count`, `false_negative_count`, `last_calibrated`
- If a persona's false-positive rate exceeds `max_false_positive_rate` (configurable, default 0.3), the persona is flagged for review. If it exceeds `max_false_positive_critical` (0.5), the persona is **disabled** until reviewed.
- At pipeline startup, persona calibration data is loaded. Personas with `disabled = True` are skipped.

`[KARL-ACCEPTED] [NEW]` **Edge case 7.5.D -- Plan revision quality tracking:**
When PREMORTEM triggers a plan regeneration, the system tracks whether the regeneration actually addressed the fatal flags. The tracking record:
- `plan_version_before`, `plan_version_after`, `fatal_flags_triggering_revision`, `plan_checksum_before`, `plan_checksum_after`
- `revision_addressed_flags: bool` -- computed by checking if the new plan's sub-tasks differ from old in the flagged areas
- If a revision does NOT address the flags, the next PREMORTEM cycle will re-flag them. This is expected behavior -- the cycle counter prevents infinite oscillation. But the tracking provides data for tuning what constitutes an adequate revision.

`[KARL-ACCEPTED] [NEW]` **Edge case 7.5.E -- PREMORTEM's fatal flag priority over BACKBRIEF's structural pass:**
Explicit priority: PREMORTEM's semantic analysis overrides BACKBRIEF's structural analysis. If BACKBRIEF passes (structurally sound) and PREMORTEM rejects (semantically flawed), the plan is regenerated. If BACKBRIEF rejects (structurally broken), the plan is regenerated regardless of PREMORTEM's state. The graph topology enforces: BACKBRIEF check first, then PREMORTEM. PREMORTEM only runs if BACKBRIEF passes. If PREMORTEM finds fatal flaws, it routes to PLAN regeneration which then goes through BACKBRIEF again.

### 7.6 INTERFACES

Updated to include `plan_checksum`:

```python
[NEW]
class PremortemNode:
    def analyze(self, state: PipelineState) -> PipelineState:
        """Generate failure scenarios from multiple persona perspectives.
        
        Key change from v1: scenarios are archived per plan_checksum,
        not appended across plan versions. If plan_checksum changed,
        old scenarios are archived and new ones generated.
        """
        ...
```

### 7.7 INTERACTIONS

Updated for independent counters and plan-versioned scenario storage.

### 7.8 FAST PATH & 7.9 INTEGRATION RISK

Updated to reflect persona calibration tracking and risk fusion.

---

## 8. BRANCHING FACTOR MONITOR (branching_monitor.py)

### 8.1 FUNCTION & RATIONALE

`[KARL-ACCEPTED]` Karl is correct: v1 described a pre-execution DAG structure analyzer but called it a "runtime monitor," violating the BRIEFING.md agreement. v2 corrects this. The node is now:

**Two-component design:**
1. **Static DAG analyzer (pre-execution):** Computes branching factor from the plan's DAG before execution. Same logic as v1's BRANCHING MONITOR. Runs before APPROVAL (unchanged position in topology).
2. **True runtime sub-task spawn monitor (during execution):** NEW component. Tracks dynamic sub-task spawning during EXECUTE. If a sub-task dynamically spawns new sub-tasks (via tool calls that return new tasks), the runtime monitor detects this and can halt execution mid-flow.

The runtime component is lightweight: each sub-task execution tracks whether it produced new sub-tasks as side-effect output. If the total number of sub-tasks (original + spawned) exceeds `max_total_sub_tasks` (configurable, default = original plan count * 2), the runtime monitor flags a halt, which triggers immediate REPLAN.

### 8.2 FILE & LOCATION

- **Module:** `branching_monitor.py` (new independent module)
- **Class:** `BranchingFactorMonitor` (pre-execution) + `RuntimeBranchMonitor` (during execution)
- **Methods:** `def analyze_dag(self, state: PipelineState) -> PipelineState` (static), `def track_spawn(sub_task_context) -> None` (runtime, called from EXECUTE)

### 8.3 INPUT

Static analyzer (same as v1 with additions):

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `plan` | `Plan` | PLAN | Full plan with DAG structure |
| `sub_tasks` | `list[SubTaskDef]` | PLAN | Sub-tasks to be executed |
| `max_depth` | `int` | Configuration | [NEW] Maximum allowed DAG depth before halting. Default 10. |

Runtime monitor:

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `original_sub_task_count` | `int` | PLAN | Count of sub-tasks in the original plan |
| `spawned_sub_task_count` | `int` | EXECUTE | [NEW] Count of dynamically spawned sub-tasks during execution |
| `max_total_sub_tasks` | `int` | Configuration | [NEW] Maximum total sub-tasks before runtime halt. Default = `original * 2`. |

### 8.4 OUTPUT

Updated output:

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `branching_report` | `BranchingReport` | APPROVAL | Branching analysis with recommendations (same structure) |
| `concurrency_limit` | `int` | EXECUTE | Max concurrent sub-tasks |
| `halt_flag` | `bool` | Graph router | True if b >= 1 detected OR depth > max_depth |
| `halt_reason` | `Optional[str]` | REPLAN | Explanation of why halt was triggered |
| `runtime_monitor_active` | `bool` | EXECUTE | [NEW] Whether the runtime spawn monitor should track this execution |

### 8.5 EDGE CASES

`[KARL-ACCEPTED] [NEW]` **Edge case 8.5.A -- Depth-based check is a first-class feature (not an afterthought):**
The depth-based check (`max_depth > 10` triggers warning, `max_depth > max_allowed_depth` triggers halt) is implemented as a first-class check alongside branching factor. The check produces its own entry in the branching report: `depth_violation: bool`, `depth_violation_threshold: int`. This addresses Karl's point about a chain of 50 sub-tasks (b=1) being effectively divergent.

`[KARL-ACCEPTED] [NEW]` **Edge case 8.5.B -- 45% rule disentangled from branching factor:**
The 45% compute overhead rule is REMOVED from the branching monitor. It was a category error in v1 (the 45% rule is about agent overhead as a fraction of total compute budget, not about branching factor). The 45% rule is now tracked in the cost-budget monitoring system (section D.9), which monitors the ratio of planning/overhead costs to execution costs. When overhead exceeds 45% of total compute budget, a warning is issued, but this does NOT affect branching factor analysis.

`[KARL-ACCEPTED] [NEW]` **Edge case 8.5.C -- Runtime monitor behavior on replan:**
When the runtime monitor halts execution mid-flow (during EXECUTE), it triggers an immediate transition to REPLAN. The REPLAN node receives the halted state, including which sub-tasks were in progress and which had spawned excessive sub-tasks. REPLAN generates a delta that specifically addresses the spawning behavior (e.g., merging spawned sub-tasks back into parent, or restructuring to limit depth). The FRAGO loop counter increments. If the runtime monitor halts again on the re-execution, the system progresses through the compensation ladder as normal.

### 8.6 INTERFACES

Updated to include depth checking and runtime monitor:

```python
[NEW]
@dataclass
class BranchingReport:
    branching_factor: float
    max_depth: int
    depth_violation: bool
    depth_violation_threshold: int
    node_count: int
    has_divergent_branch: bool
    divergent_nodes: list[str]
    concurrency_recommendation: int
    runtime_monitor_active: bool  # [NEW]

[NEW]
class RuntimeBranchMonitor:
    """Tracks dynamic sub-task spawning during EXECUTE."""
    
    def __init__(self, max_total: int):
        self.spawned_count = 0
        self.max_total = max_total
    
    def record_spawn(self, count: int = 1) -> bool:
        """Record spawned sub-tasks. Returns True if limit exceeded."""
        self.spawned_count += count
        return self.spawned_count > self.max_total
    
    def should_halt(self) -> bool:
        """Check if runtime branching has exceeded limits."""
        return self.spawned_count > self.max_total
```

### 8.7 INTERACTIONS

Updated for two-component design:
- **Pre-execution (static):** Triggered by PREMORTEM. Triggers APPROVAL GATE if no halt. Triggers REPLAN if halt.
- **Runtime (dynamic):** Embedded in EXECUTE. Each sub-task execution reports spawned count to the monitor. If monitor flags halt, EXECUTE pauses, state is checkpointed, and the graph routes to REPLAN.

### 8.8 FAST PATH & 8.9 INTEGRATION RISK

Updated to reflect the two-component architecture and the depth-based check.

---

## 9. APPROVAL GATE (guardrails.py)

### 9.1 FUNCTION & RATIONALE

`[KARL-ACCEPTED]` Key changes:
1. **Risk fusion step added** (section 9.10, new) -- reconciles risk signals before presentation.
2. **Progressive disclosure UX** -- the briefing now has a summary tier (Commander's Intent + reconciled risk summary + critical flags) and a detail tier (per sub-task breakdown, full pre-mortem scenarios, branching analysis).
3. **Briefing diff for replan cycles** -- when approval is re-entered on replan, the briefing highlights "what changed since last approval."
4. **Summary-first presentation** with option to expand details.

### 9.2 FILE & LOCATION

Unchanged.

### 9.3 INPUT

Unchanged from v1.

### 9.4 OUTPUT

Unchanged from v1.

### 9.5 EDGE CASES

`[KARL-ACCEPTED] [NEW]` **Edge case 9.5.A -- Progressive disclosure briefing format:**
The structured briefing is presented in two tiers:

**Tier 1 -- Summary (always shown):**
- Commander's Intent (goal, constraints, priority)
- Reconciled risk summary: `overall_risk`, number of sub-tasks per risk level
- Critical flags: CRITICAL sub-tasks, unresolved pre-mortem flags, branching violations, backbrief forced flag
- "View details" prompt for Tier 2

**Tier 2 -- Details (expandable):**
- Per sub-task breakdown: risk level, pre-mortem scenarios (if any), branching analysis
- Knowledge gaps (if any)
- Provenance: which model generated what
- Revision history (plan_version, reason for each revision)

This addresses Karl's concern about the user being overwhelmed by a single massive briefing.

`[KARL-ACCEPTED] [NEW]` **Edge case 9.5.B -- Briefing diff for replan cycles:**
When APPROVAL is re-entered on a replan cycle, the briefing header shows a diff section:

**"Changes since last approval (replan #{n}):**
- New sub-tasks added: [list]
- Sub-tasks removed: [list]
- Sub-tasks with changed risk levels: [list, old->new]
- New pre-mortem scenarios: [summary]
- Plan version: {n-1} -> {n}
- Reason for replan: [evaluation_detail from EVALUATE]"

This addresses Karl's concern about the user losing context between approval cycles.

`[KARL-ACCEPTED] [NEW]` **Edge case 9.5.C -- Rename "halt" to "mandatory approval" for CRITICAL:**
Throughout the spec and code, "pipeline halt" for CRITICAL has been renamed to "mandatory human approval." This is more accurate: the pipeline does not stop permanently -- it pauses at APPROVAL GATE and waits for the user. The user can approve (proceed with CRITICAL sub-task) or reject. This changes the language in:
- Section 9.1: "CRITICAL-risk sub-tasks mandate human approval (not a pipeline stop)."
- Section 6.7: "CRITICAL overrides all other routing -- mandatory human approval regardless of path."
- Graph routing: CRITICAL sub-tasks always route through APPROVAL, but `approval_decision = "approved"` allows execution to proceed.

### 9.6 INTERFACES

Updated `ApprovalGate`:

```python
[NEW]
class ApprovalGate:
    def _format_briefing_summary(self, state: PipelineState) -> str:
        """Format Tier 1 summary briefing."""
        ...
    
    def _format_briefing_detail(self, state: PipelineState) -> str:
        """Format Tier 2 detail briefing (expandable)."""
        ...
    
    def _format_replan_diff(
        self,
        previous_approval: ApprovalDecision,
        current_state: PipelineState,
    ) -> str:
        """Format diff between previous and current approval briefings.
        
        Only called on replan re-entry to APPROVAL.
        """
        ...
```

### 9.7 INTERACTIONS

Updated with risk fusion step (section 9.10) between PREMORTEM/BRANCHING MONITOR and APPROVAL:

- **Updated trigger chain:** BRANCHING FACTOR MONITOR -> RISK FUSION (section 9.10, new) -> APPROVAL GATE.
- **Replan re-entry:** On replan, if RISK ASSESSMENT re-classifies any sub-task as CRITICAL, the graph routes to RISK FUSION (refresh reconciliation) -> APPROVAL (with diff briefing). If no CRITICAL re-classification, APPROVAL is bypassed (as in v1).

### 9.8 FAST PATH & 9.9 INTEGRATION RISK

Unchanged from v1.

### 9.10 RISK FUSION -- NEW SECTION

`[DESIGN-DECISION: RISK_FUSION]`

#### 9.10.1 Function and Rationale

Reconciles four independent risk signals produced by different nodes into a single, coherent risk assessment presented to the human at APPROVAL. Without this step, the APPROVAL briefing shows contradictory signals (e.g., RISK ASSESSMENT says LOW, PREMORTEM says HIGH) with no resolution.

#### 9.10.2 Input Signals

| Signal | Source | Type | Description |
|--------|--------|------|-------------|
| `complexity_factors` | CLASSIFY | `dict[str, float]` | Novelty, ambiguity, tool_requirements, domain_uncertainty (0.0-1.0) |
| `risk_levels` | RISK ASSESSMENT | `dict[str, RiskLevel]` | Per sub-task: LOW/MEDIUM/HIGH/CRITICAL |
| `failure_scenario_severities` | PREMORTEM | `dict[str, list[Severity]]` | Per sub-task: list of scenario severities from different personas |
| `halt_flag` | BRANCHING MONITOR | `bool` | Whether branching factor violation was detected |

#### 9.10.3 Reconciliation Rules

For each sub-task, the reconciled risk level (`final_risk[sub_task]`) is computed:

```
1. Start with RISK_ASSESSMENT base level.
2. If PREMORTEM has any scenario for this sub-task with severity > base:
   - Elevate base to match highest PREMORTEM severity.
3. If CLASSIFY flagged the domain as safety-critical:
   - Elevate base to at least HIGH.
4. If BRANCHING MONITOR's halt_flag is True:
   - Overall risk is elevated to HIGH (divergent branching is a structural risk).
5. If knowledge_gaps with severity HIGH affect this sub-task:
   - Elevate base to at least HIGH (missing information increases risk).
6. Final output: dict of sub_task_id -> reconciled RiskLevel.
```

**Severity mapping for reconciliation:**
- PREMORTEM "low" / RISK "LOW" = 1
- PREMORTEM "medium" / RISK "MEDIUM" = 2
- PREMORTEM "high" / RISK "HIGH" = 3
- PREMORTEM "critical" / RISK "CRITICAL" = 4

`final_risk[sub_task] = max(risk_levels[sub_task], max((s.severity for s in failure_scenarios if sub_task in s.affected_sub_tasks), default=LOW))`

#### 9.10.4 Where Reconciliation Happens

Reconciliation is a method on the `ApprovalGate` class: `_reconcile_risk_signals(state) -> tuple[dict[str, RiskLevel], RiskLevel]`. It runs immediately before `_format_briefing_summary()`.

#### 9.10.5 Preservation of Individual Signals

The individual signals are NOT discarded -- they are preserved in the audit trail and available in the Tier 2 detail briefing. The reconciliation produces a SINGLE risk number for decision-making while preserving the nuance for analysis.

#### 9.10.6 Edge Cases

- **All signals agree:** Pass through unchanged.
- **No PREMORTEM scenarios for a sub-task:** `max()` with empty list defaults to LOW. RISK ASSESSMENT level stands.
- **BRANCHING MONITOR halt with no other signals:** Overall risk set to HIGH. Individual sub-task risks unchanged.
- **CLASSIFY complexity factors indicate high ambiguity but RISK ASSESSMENT says LOW:** Ambiguity alone does NOT elevate risk. Ambiguity is a separate dimension (the pipeline already escalated from FAST due to ambiguity). Risk elevation requires PREMORTEM or knowledge-gap signals.

---

## 10. EXECUTE (executor.py)

### 10.1 FUNCTION & RATIONALE

`[DESIGN-DECISION: LANGGRAPH_SUBGRAPHS]`

**Chosen approach:** LangGraph Subgraphs for isolated state per sub-task.

Each sub-task executes as an independent LangGraph Subgraph with its own reduced state schema and its own checkpointer. The parent EXECUTE node:
1. Creates a `SubTaskState` for each sub-task, containing only the fields that sub-task needs (user_message subset, tool references, sub-task definition).
2. Fans out sub-tasks using `Send()` -- LangGraph's built-in mechanism for launching parallel sub-graphs.
3. A `Join` node collects completed Subgraph states and merges results back into the parent `PipelineState`.
4. Each Subgraph is independently checkpointable -- if interrupted mid-execution, sub-tasks that completed are preserved; only uncompleted sub-tasks restart on resume.

This approach was chosen over the private-dict workaround (option b from v1) because:
- True checkpoint isolation is the only way to guarantee the parallel safety claim (fixing H9, H11, H12).
- Private dicts lose state on interrupt/resume, breaking the safety invariant.
- The complexity is at graph assembly time (one-time cost), not at runtime (recurring cost).

### 10.2 FILE & LOCATION

Unchanged from v1, with added classes:

- **Class:** `ExecuteNode` -- Parent orchestrator
- **Class:** `SubTaskSubgraph` -- Factory for creating sub-task Subgraphs
- **Class:** `JoinNode` -- Collects Subgraph results
- **Method:** `_execute_sub_task(sub_task: SubTaskDef, context: ExecutionContext) -> SubTaskResult` -- Runs within the Subgraph

### 10.3 INPUT

Unchanged from v1.

### 10.4 OUTPUT

Unchanged from v1.

### 10.5 EDGE CASES

`[KARL-ACCEPTED]` **Updated state corruption section for Subgraphs:**

**State corruption (Subgraph isolated-state design):**
- Each sub-task gets its own `SubTaskState` with a reduced schema containing only: `sub_task_def`, `user_message_snapshot`, `tool_registry_snapshot`, `execution_context`, `result`. No shared mutable state.
- The parent graph's `PipelineState` is NOT modified during sub-task execution. Each Subgraph checkpoints independently.
- On interruption: completed Subgraphs are checkpointed and do not re-execute. In-progress Subgraphs restart from their last checkpoint within the Subgraph (not from scratch -- this is a key improvement over private-dict approach).
- On completion: the `Join` node reads each Subgraph's final state, extracts the result, and writes it to `PipelineState.sub_task_results`.

`[KARL-ACCEPTED] [NEW]` **Edge case 10.5.A -- Cascade prevention in compensation handler ladder:**
The compensation handler ladder has an invariant: **a handler can only escalate UP, never sideways or down.** Specifically:
- `reprompt` can escalate to `catch_fallback`, `local_compensation`, etc., but cannot trigger ANOTHER `reprompt`.
- `catch_fallback` that fails escalates directly to `local_compensation`, not back to `reprompt`.
- `radius_expansion` that fails escalates to `global_replan`, not back to local.
- This single-direction escalation prevents the cascade that Karl identified (a handler triggering another handler of the same level).

Implementation: `_determine_compensation_level()` maintains a `current_level` state. When a handler fails, it always returns the next level in the ladder. Handlers do not call each other; they are called by the dispatcher which enforces monotonic escalation.

`[KARL-ACCEPTED] [NEW]` **Edge case 10.5.B -- DAG scheduler specified as a first-class component:**
The DAG scheduler is no longer a black box. It is specified as:

```python
[NEW]
class DagScheduler:
    """Enforces dependency ordering for sub-task execution.
    
    Processes sub-tasks in topological order.
    Manages the ready queue for parallel execution.
    """
    
    def __init__(self, sub_tasks: list[SubTaskDef], dag: dict[str, list[str]]):
        self.sub_tasks = {st.id: st for st in sub_tasks}
        self.dag = dag
        self._validate()
    
    def _validate(self):
        """Validate DAG structure before execution.
        
        Checks:
        - All dependency references point to valid sub-task IDs.
        - No cycles (redundant with BACKBRIEF, but defense-in-depth).
        - No duplicate IDs.
        """
        ...
    
    def get_ready(self, completed: set[str]) -> list[str]:
        """Return sub-tasks whose dependencies are all completed.
        
        Implements the ready-queue for parallel dispatch.
        Sub-tasks with the same isolation_key are never returned
        simultaneously (they share a resource and must be sequential).
        """
        ...
    
    def is_complete(self) -> bool:
        """Check if all sub-tasks have been dispatched."""
        ...

    @property
    def max_concurrency(self) -> int:
        """Maximum parallel sub-tasks based on DAG structure and isolation keys."""
        ...
```

The DAG scheduler is the component that enforces execution ordering, detects runtime cycles (defense-in-depth after BACKBRIEF), and respects isolation_keys for resource-level sequentialization.

`[KARL-ACCEPTED] [NEW]` **Edge case 10.5.C -- Atomicity requirements for sub-task execution:**
Sub-tasks that write to external resources MUST use atomic patterns:
- **File writes:** Write to a temp file, then `os.rename()` (atomic on POSIX). Never write directly to the target path.
- **Database writes:** Use transactions. If the sub-task fails, rollback.
- **API calls (state-changing):** Use idempotency keys. If the sub-task retries, the API receives the same idempotency key and does not duplicate the operation.
- **Environment mutations:** Record the original state. On failure, restore the original state (best-effort -- some mutations cannot be undone).
- These atomicity requirements are enforced by the tool wrappers in the tool registry, not by individual sub-task implementations. The tool wrapper checks if the operation is idempotent or atomic; if not, it logs a warning.

### 10.6 INTERFACES

Updated for Subgraph design:

```python
[NEW]
@dataclass
class SubTaskState:
    """Isolated state for a single sub-task Subgraph."""
    sub_task_def: SubTaskDef
    user_message_snapshot: str
    tool_registry_snapshot: ToolRegistry
    context: ExecutionContext
    result: Optional[SubTaskResult]
    error: Optional[ExecutionError]
    compensation_level: int = 0

class SubTaskSubgraph:
    """Factory for creating a self-contained sub-task Subgraph."""
    
    @staticmethod
    def create(config: ExecutorConfig) -> CompiledSubgraph:
        """Create a Subgraph with: validate_input -> execute -> compensate -> output.
        
        The Subgraph has its own state (SubTaskState), its own nodes,
        and its own checkpointer. It is compiled independently and
        attached to the parent graph via Send/Join.
        """
        ...

class JoinNode:
    """Collects Subgraph results and merges into parent state."""
    
    def join(self, state: PipelineState, subgraph_states: list[SubTaskState]) -> PipelineState:
        """Read each Subgraph's final state, extract results, merge.
        
        Completed sub-tasks: extract result into state.sub_task_results.
        Failed sub-tasks: record error in state.execution_errors.
        In-progress sub-tasks (should not happen at join): log error.
        """
        ...
```

### 10.7 INTERACTIONS

Updated for Subgraph orchestration:

- EXECUTE receives a list of SubTaskDefs and creates a Subgraph for each.
- The parent graph uses `Send()` to launch Subgraphs in parallel (respecting concurrency_limit and isolation_keys).
- The `JoinNode` awaits all Subgraphs to complete (or fail) before merging results.
- On interrupt/resume: completed Subgraphs are checkpointed and skipped on resume. In-progress Subgraphs restart from their last checkpoints.
- On compensation escalation: if a Subgraph's compensation level reaches 4 (radius expansion), the Subgraph halts and returns partial results. The JoinNode passes this to EVALUATE/REPLAN.

### 10.8 FAST PATH & 10.9 INTEGRATION RISK

Updated to reflect Subgraph choice and spec:

**Integration risk 10.9 updated:**
"The hardest thing about EXECUTE is now the **Subgraph orchestration** -- specifically:
1. Ensuring the parent graph correctly awaits all Subgraphs before joining.
2. Ensuring Subgraph interruption/resume works correctly with the parent checkpointer.
3. Ensuring Subgraph failure propagates correctly to the parent (not silently swallowed).

The LangGraph Subgraph API supports `Send()` + `Join()` natively, but the pattern is new and may have edge cases with concurrent Subgraph checkpointing. Implementation must be tested with parallel sub-tasks under interruption conditions.

Second-hardest: **compensation handler cascade prevention** -- the monotonic escalation invariant (section 10.5.A) must be enforced programmatically, not just documented. A unit test should verify that no handler can invoke a handler of the same or lower level."

---

## 11. SYNTHESIZE (synthesizer.py)

### 11.1 FUNCTION & RATIONALE

`[KARL-ACCEPTED]` Key changes:
1. Merge algorithm now defined per output TYPE.
2. FAST path quality_report no longer lies -- uses `quality_review_performed: False` instead of hardcoded scores.
3. `None` result handling and format heterogeneity rules specified.

### 11.2 FILE & LOCATION

Unchanged.

### 11.3 INPUT

Unchanged from v1.

### 11.4 OUTPUT

`[KARL-ACCEPTED]` QualityReport on FAST path:

| Field | Value on FAST Path | v1 | v2 |
|-------|-------------------|----|-----|
| `is_consistent` | `None` (not assessed) | `True` (hardcoded) | Quality review not performed |
| `completeness_score` | `None` (not assessed) | `1.0` (hardcoded) | Quality review not performed |
| `quality_review_performed` | `False` | `True` (implied) | Explicitly `False` |

### 11.5 EDGE CASES

`[KARL-ACCEPTED] [NEW]` **Edge case 11.5.A -- Merge algorithm defined by output type:**
The `_merge_results()` method now handles different output types explicitly:

| Result Type | Merge Strategy |
|-------------|---------------|
| **Text (str):** | Section-based concatenation: `"[Sub-task A: {sub_task.description}]\n{result.output}\n\n[Sub-task B: ...]"` |
| **JSON (dict):** | Deep merge: `dict1.update(dict2)` for top-level keys. Conflicting keys flagged as conflict. Arrays concatenated. |
| **Code (detected by ``` markers or .py/.js/.ts extension):** | Ordered concatenation within a single code block: `# Sub-task A\n{code}\n\n# Sub-task B\n{code}`. If code conflicts (same function defined twice), flag as conflict. |
| **Binary (base64):** | Not merged. Include as separate attachment references. Flag as "binary result not merged." |
| **None (skipped/failed):** | Skip. Include placeholder: `"[Sub-task {id}: SKIPPED -- dependency failure or execution error]"` |
| **Mixed types:** | Convert all to text via `str()` or repr(). Merge as text with type headers: `"[Result from {sub_task_id} (type: {type})]".` |

`[KARL-ACCEPTED] [NEW]` **Edge case 11.5.B -- Heterogeneous output format handling:**
If sub-task outputs span multiple formats (e.g., one produces JSON, another produces prose), the merge:
1. Detects the dominant format (most sub-tasks produce this type).
2. Converts minority formats to the dominant format (e.g., JSON -> formatted text).
3. Produces a homogeneous final output.
4. Flags the conversion in the quality report: `format_heterogeneity_detected: True`, `minority_format_converted: str`.

### 11.6 INTERFACES

Updated `_merge_results`:

```python
def _merge_results(
    self,
    results: list[SubTaskResult],
    plan: Plan,
) -> tuple[str, list[Conflict]]:
    """Merge sub-task results into coherent output.
    
    Uses type-aware merge strategy from section 11.5.A.
    Algorithmic merge, no LLM call.
    Detects format heterogeneity and converts if needed (11.5.B).
    """
    ...
```

### 11.7 INTERACTIONS

Unchanged from v1.

### 11.8 FAST PATH

Updated: `quality_report = QualityReport(is_consistent=None, completeness_score=None, quality_review_performed=False)`.

### 11.9 INTEGRATION RISK

Updated to reference the type-specific merge strategies and the explicit quality_review_performed flag.

---

## 12. EVALUATE (evaluate.py)

### 12.1 FUNCTION & RATIONALE

`[KARL-ACCEPTED]` Key changes:
1. Algorithmic fallback now produces PARTIAL/FAILURE distinctions (not just binary SUCCESS/FAILURE).
2. LLM nondeterminism acknowledged, with evaluation result caching for stability.
3. "No criteria = SUCCESS" default removed -- replaced with explicit "unevaluable" status.

### 12.2 FILE & LOCATION

Unchanged.

### 12.3 INPUT & 12.4 OUTPUT

Unchanged from v1.

### 12.5 EDGE CASES

`[KARL-ACCEPTED] [NEW]` **Edge case 12.5.A -- Algorithmic fallback produces PARTIAL/FAILURE distinction:**
The algorithmic fallback (v1: `all sub_tasks succeeded && output non-empty = SUCCESS`) is replaced with a more nuanced fallback:

```
SUCCESS: all sub-tasks succeeded AND output non-empty.
PARTIAL: some sub-tasks succeeded, some failed, output non-empty.
FAILURE: no sub-tasks succeeded OR output is empty.
```

This matches the LLM-based evaluation's three-state output, so the evaluation outcome is no longer a function of whether the LLM is available. The distinction between PARTIAL and FAILURE is preserved regardless of evaluation method.

`[KARL-ACCEPTED] [NEW]` **Edge case 12.5.B -- LLM nondeterminism acknowledged with evaluation caching:**
LLM-based evaluation of natural-language criteria is acknowledged as inherently subjective and nondeterministic. Mitigation:
- Evaluation results for an (output, criteria_list) pair are **cached** within a single pipeline invocation. On replan re-evaluation of the same (output, criteria_list) pair, the cached result is returned instead of re-running the LLM call.
- The cache key is: `sha256(output + canonical_json(criteria_list))`.
- If the criteria list changed between evaluations (because REPLAN modified the Commander's Intent), the cache is invalidated for that invocation.
- This prevents the evaluation from flipping between PARTIAL and SUCCESS on replan.

`[KARL-ACCEPTED] [NEW]` **Edge case 12.5.C -- "No criteria = unevaluable" (removed default SUCCESS):**
If the Commander's Intent has no acceptance criteria (`acceptance_criteria: []` or `None`), EVALUATE returns `evaluation_result = "UNEQUIVALENT"` (new enum value). This is a pipeline-level signal: "This output cannot be evaluated because there are no defined criteria." The pipeline still proceeds (UNEQUIVALENT is treated like SUCCESS for routing -- it does not trigger replan), but the output is annotated: "This output was not evaluated against any criteria -- quality is unconfirmed." This removes the perverse incentive (v1's "no criteria = SUCCESS" encouraged the planner to produce vague criteria).

The `EvaluationResult` type is updated:

```python
EvaluationResult = Literal["SUCCESS", "PARTIAL", "FAILURE", "UNEQUIVALENT"]
```

`[KARL-ACCEPTED] [NEW]` **Edge case 12.5.D -- Delta-aware evaluation on replan:**
On replan re-evaluation, EVALUATE receives the list of changed sub-task IDs (`replan_scope`). The evaluation:
1. For acceptance criteria that depend ONLY on unchanged sub-task results: carry forward the previous evaluation result for those criteria.
2. For criteria that depend on changed sub-task results: re-evaluate.
3. For NEW criteria added by REPLAN: evaluate fresh.
This is implemented by tracking which sub-tasks contribute to which criteria. In v2, this mapping is simplest: all criteria depend on all sub-task results (the default assumption). Delta-aware evaluation is a Wave 3 optimization when criteria-to-subtask mapping is explicit.

### 12.6 INTERFACES

Updated:

```python
EvaluationResult = Literal["SUCCESS", "PARTIAL", "FAILURE", "UNEQUIVALENT"]  # [NEW] UNEQUIVALENT added

class EvaluateNode:
    def __init__(
        self,
        llm_client: Optional[Any],
        config: EvaluateConfig,
    ):
        self._evaluation_cache: dict[str, Evaluation] = {}  # [NEW] cache
    
    def _evaluate_algorithmic(
        self,
        output: str,
        criteria: list[str],
        sub_task_results: list[SubTaskResult],
    ) -> Evaluation:
        """Deterministic evaluation without LLM call.
        
        [UPDATED] Now produces PARTIAL (not just binary SUCCESS/FAILURE).
        """
        ...
```

### 12.7 INTERACTIONS

Updated: UNEQUIVALENT routes like SUCCESS (output proceeds to user, annotated).

### 12.8 FAST PATH

Updated: "EVALUATION is always SUCCESS for FAST path, with `evaluation_method = 'algorithmic'` and `evaluation_detail = 'FAST path -- no criteria evaluated'."

### 12.9 INTEGRATION RISK

Updated to reference the evaluation caching and the UNEQUIVALENT status.

---

## 13. REPLAN (replanner.py)

### 13.1 FUNCTION & RATIONALE

`[KARL-ACCEPTED]` Key changes:
1. **FRAGO loop now includes lightweight structural validation** on every delta plan (BACKBRIEF-lite for DAG cycles + branching factor check on delta).
2. **REPLAN receives RESEARCH cache re-query** (not full RESEARCH re-execution, but cache re-query for current knowledge_gaps).
3. **Compensation ladder escalation and FRAGO replan count interaction is precisely defined.**
4. **Distinct terminology:** REPLAN's output is always a "delta replan" (changed sub-tasks only), not a "revision" (which is PLAN's terminology).

### 13.2 FILE & LOCATION

Unchanged.

### 13.3 INPUT

`[KARL-ACCEPTED]` [NEW] Now receives:

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `current_knowledge_gaps` | `list[KnowledgeGap]` | RESEARCH (cache re-query) | [NEW] Current knowledge gaps at replan time. Re-queried from RESEARCH cache (not full re-execute). |
| `backbrief_revision_count` | `int` | Graph state | [NEW] Current BACKBRIEF revision count (for info -- REPLAN does not use this for its own ceiling). |

### 13.4 OUTPUT

Unchanged from v1.

### 13.5 EDGE CASES

`[KARL-ACCEPTED] [NEW]` **Edge case 13.5.A -- FRAGO loop includes lightweight structural validation:**
Every delta plan produced by REPLAN is validated before re-execution. The validation consists of three checks totaling < 10ms (algorithmic, no LLM calls):

1. **Structural consistency check (BACKBRIEF-lite):**
   - Check the delta's DAG for cycles (the delta DAG = only changed sub-tasks + their transitive dependents, extracted from the full plan DAG).
   - Check that all dependency references in changed sub-tasks point to valid sub-task IDs.
   - If cycle detected: reject the delta, escalate compensation level (skip directly to radius_expansion or global_replan).
   - If broken reference detected: fix automatically (remove broken reference, log warning).

2. **Branching factor check on delta:**
   - Compute branching factor of the full plan AFTER applying the delta.
   - If b >= 1 or depth > max_depth: reject the delta, escalate compensation level (skip to global_replan).
   - If no violation: proceed.

3. **Risk delta check (already handled by RISK ASSESSMENT re-classification):**
   - Verify that RISK ASSESSMENT re-classified all changed sub-tasks.
   - If any sub-task in `replan_scope` has no `risk_level`, force re-classification before EXECUTE.

These three checks REPLACE full BACKBRIEF, PREMORTEM, and BRANCHING MONITOR re-runs on the replan path. The checks ensure structural integrity without the performance cost of re-running the full pipeline.

`[KARL-ACCEPTED] [NEW]` **Edge case 13.5.B -- Compensation ladder escalation counts vs. FRAGO replan counts -- clarified:**
The two counters are independent and serve different purposes:

| Counter | Scope | Max Value | Purpose |
|---------|-------|-----------|---------|
| `compensation_level` | Within a single REPLAN invocation | 6 (human_escalation) | Tracks escalation within ONE delta generation attempt |
| `replan_count` | Across all REPLAN invocations | 3 (default) | Tracks total number of FRAGO loop iterations |

**Interaction:**
- A single REPLAN invocation starts at `compensation_level = state.previous_compensation_level + 1`.
- Within that invocation, the compensation ladder can escalate from `reprompt` through `human_escalation` (up to 6 levels) without consuming additional replan budget.
- If `human_escalation` is reached at replan 1/3, the pipeline pauses for human input. On resume, the current REPLAN invocation continues (same `replan_count`).
- If human responds with actionable guidance, the delta is generated and executed. This counts as 1 replan (even though compensation internally escalated to level 6).
- If `compensation_level` reaches `global_replan` (level 5) and still fails, the entire FRAGO loop counter increments, and REPLAN is called again with `previous_compensation_level = 0` (fresh start at reprompt level).

This means: a single REPLAN invocation can attempt up to 6 different compensation strategies within its 1/3 replan budget. The worst case is 3 replans * 6 compensation levels = 18 total compensation attempts before human escalation.

`[KARL-ACCEPTED] [NEW]` **Edge case 13.5.C -- REPLAN's delta makes the plan WORSE -- oscillation handling:**
If REPLAN's delta degrades quality (EVALUATE returns worse result than previous iteration), the system detects this:
- On each FRAGO loop iteration, EVALUATE compares the current evaluation against the previous iteration's evaluation.
- If the evaluation is strictly worse (SUCCESS -> PARTIAL, PARTIAL -> FAILURE, or same result but more criteria failed), the system notes "degrading replan."
- After 2 consecutive degrading replans, the system escalates directly to `human_escalation` (skips remaining compensation levels in the ladder).
- The human escalation presents: "Repeatedly attempting to fix this has made the output worse. Can you provide guidance?"

`[KARL-ACCEPTED] [NEW]` **Edge case 13.5.D -- BACKBRIEF is skipped on replan BUT structural validation runs (per 13.5.A):**

> **Karl counter-argument:** "REPLAN skips BACKBRIEF, PREMORTEM, and BRANCHING MONITOR. A delta plan that introduces structural errors, failure modes, or branching divergence will reach EXECUTE unvalidated."
> **Resolution:** v2 adds BACKBRIEF-lite (DAG cycle + broken reference check), branching factor check on the delta, and risk delta check to the FRAGO loop. These three checks (13.5.A) ensure structural integrity without the performance cost of full PREMORTEM re-run. The lightweight check completes in <10ms vs. 3-5 LLM calls for full PREMORTEM. PREMORTEM's persona-based failure analysis is intentionally NOT re-run on delta plans because: (a) the delta is typically small (1-3 sub-tasks), not enough to warrant full persona analysis, (b) the original PREMORTEM already analyzed the plan's core structure, (c) the risk fusion step (section 9.10) already elevated risk for sub-tasks with pre-mortem flags. If the delta introduces a fundamentally new failure mode, EXECUTE's compensation handler can catch it, and the FRAGO loop will handle it.

### 13.6 INTERFACES

`[KARL-ACCEPTED]` Updated `ReplanNode`:

```python
class ReplanNode:
    def _validate_delta(
        self,
        delta_plan: Plan,
        full_plan: Plan,
        changed_ids: list[str],
    ) -> DeltaValidationResult:
        """Run lightweight structural validation on delta plan.
        
        Checks: DAG cycles in delta, broken references, branching factor.
        Returns pass/fail with details.
        """
        ...
    
    def _is_degrading_replan(
        self,
        current_eval: EvaluationResult,
        previous_eval: EvaluationResult,
    ) -> bool:
        """Check if current replan produced worse results than previous."""
        ...
```

### 13.7 INTERACTIONS

Updated FRAGO loop:

```
EVALUATE -> REPLAN -> DELTA VALIDATION (13.5.A) -> RESEARCH cache re-query
-> RISK ASSESSMENT (re-classify changed) -> EXECUTE -> SYNTHESIZE -> EVALUATE
```

If delta validation fails: escalate compensation level, regenerate delta.

Also updated: RESEARCH cache re-query is added to the FRAGO loop (not full RESEARCH re-execution -- just a cache query).

### 13.8 FAST PATH & 13.9 INTEGRATION RISK

Updated to reference delta validation and the RESEARCH cache re-query.

---

## 14. SKILL LIBRARY (skill_library.py)

### 14.1 FUNCTION & RATIONALE

`[KARL-ACCEPTED]` Key changes:
1. Administrative interface specified (list, inspect, delete, export).
2. Template decay function updated to account for use_count.
3. Template staleness checks added (tool availability validation on retrieval).
4. Tenant filtering explicitly added to template queries.
5. Failure-pattern lifecycle defined.
6. Write-ahead queue added for concurrent write handling.

### 14.2 FILE & LOCATION

Unchanged.

### 14.3 INPUT & 14.4 OUTPUT

Updated with tenant ID filtering.

### 14.5 EDGE CASES

`[KARL-ACCEPTED] [NEW]` **Edge case 14.5.A -- Template decay function updated:**
The v1 decay function `score = success_rating * 0.9^(days_since_last_success)` was recency-dominated -- a single-use-yesterday template outranked a hundred-use veteran by 21x.

v2 uses a balanced decay function:

```
base_score = success_rating * sqrt(use_count + 1)
time_decay = 0.95^(days_since_last_success)  # Slower decay (0.95 vs 0.9)
failure_penalty = 0.8^(recent_failures)  # Penalty for failures in last 10 uses
final_score = base_score * time_decay * failure_penalty
```

This function:
- Rewards frequency (`sqrt(use_count + 1)` grows sub-linearly, so a 100-use template gets 10x multiplier vs. 1x for a new template).
- Decays slowly with time (0.95^30 = 0.21 after 30 days, vs. 0.9^30 = 0.04 in v1).
- Penalizes recent failures (an otherwise high-scoring template with 5 recent failures gets 0.8^5 = 0.33 penalty).
- Implements the stated goal from v1: "A template used 50 times but failing on the last 10 attempts is less valuable than a template used 3 times with 3 successes." (The 50-use template with 10 failures: score = 1.0 * sqrt(51) * 0.95^days * 0.8^10 = 7.14 * decay * 0.107 = ~0.76 * decay. The 3-use template with 0 failures: score = 1.0 * sqrt(4) * decay * 1.0 = 2.0 * decay. The 3-use template scores higher when days are equal, which is the intended behavior.)

`[KARL-ACCEPTED] [NEW]` **Edge case 14.5.B -- Administrative interface specified:**
The skill library exposes the following administrative commands (via CLI or API):

| Command | Description |
|---------|-------------|
| `skill_library.list_templates(domain=None, min_rating=0.0)` | List all templates with id, domain, rating, use_count, last_used, created_at |
| `skill_library.get_template(template_id)` | Full detail of a specific template |
| `skill_library.delete_template(template_id)` | Remove a template (poisoned or stale) |
| `skill_library.list_failure_patterns(sub_task_signature=None)` | List failure patterns with resolution status |
| `skill_library.purge_domain(domain)` | Remove all templates and cache entries for a domain |
| `skill_library.export(db_path)` | Export library to a portable SQLite dump |
| `skill_library.import(db_path)` | Import templates from a portable SQLite dump |
| `skill_library.recalibrate()` | Recompute all template scores with current decay parameters |
| `skill_library.stats()` | Library health: total templates, cache entries, allowlist entries, failure patterns, storage size |

These commands require operator-level authentication (not available to regular pipeline users).

`[KARL-ACCEPTED] [NEW]` **Edge case 14.5.C -- Template staleness check on retrieval:**
When a template is retrieved for seeding PLAN, the skill library checks:
1. **Tool availability:** For each `tools_required` in the template's sub-tasks, verify the tool exists in the current tool registry. If any tool is deprecated or removed, the template is flagged as `stale = True` and its `stale_reason` is populated ("tool X no longer available"). Stale templates are returned only if NO non-stale template matches the query. They are marked clearly as stale.
2. **Configurable expiry:** Templates older than `max_template_age_days` (configurable, default 365) are automatically archived (moved to an archive table, not deleted). Archived templates are not returned on queries unless explicitly requested.

`[KARL-ACCEPTED] [NEW]` **Edge case 14.5.D -- Tenant filtering on template queries:**
All template queries include `WHERE tenant_id = ?` or `WHERE tenant_id IS NULL` (global templates). Cross-tenant template sharing is OFF by default for Wave 2. A shared template pool (`tenant_id IS NULL`) can be populated by an administrator with curated templates. Tenant-specific templates are never visible to other tenants. This prevents cross-tenant information leakage.

`[KARL-ACCEPTED] [NEW]` **Edge case 14.5.E -- Failure-pattern lifecycle:**
Failure patterns have a defined lifecycle:

```
RECORDED -> REVIEWED -> RESOLVED -> ARCHIVED
              |
              v
           UNRESOLVED
```

- **RECORDED:** A failure pattern is recorded after a successful fix (by REPLAN).
- **REVIEWED:** An operator reviews the pattern and marks it as reviewed.
- **RESOLVED:** A fix is confirmed (the pattern no longer triggers false positives).
- **ARCHIVED:** After `failure_pattern_retention_days` (configurable, default 90).
- **UNRESOLVED:** If a failure pattern accumulates `max_unresolved_attempts` (configurable, default 5) without a successful resolution, it is escalated to human review (operator dashboard).

The failure-pattern lifecycle prevents indefinite accumulation of "things we know we can't do" without review.

`[KARL-ACCEPTED] [NEW]` **Edge case 14.5.F -- Write-ahead queue for concurrent write contention:**
Instead of writing directly to SQLite (which can drop writes under load when retries are exhausted), all write operations go to an **in-memory write-ahead queue**. A background writer thread drains the queue to SQLite with retry.

Queue properties:
- **Capacity:** Configurable (default 1000 entries).
- **Eviction policy:** When queue is full, drop OLDEST entries (not newest). This ensures recent writes are preserved.
- **Drain interval:** 100ms (attempt to drain every 100ms).
- **Retry:** Each write to SQLite retries 3 times with exponential backoff (50ms, 100ms, 200ms). If still failing after 3 retries, the write remains in the queue and is retried on the next drain cycle.
- **Crash safety:** On pipeline crash, in-flight queue entries are lost. This is acceptable: the writes are post-execution archival data (templates, failure patterns, audit logs). Losing a few entries on crash is better than slowing down pipeline completion with synchronous writes.
- **Monitoring:** Queue depth is exposed as a metric. If queue depth exceeds `max_depth_warning` (default 500), an alert fires.

This eliminates the silent write-drop problem (v1: "proceed in memory-only mode (no persistence)"). With the write-ahead queue, writes are never silently dropped -- they may be delayed, but they are always attempted.

### 14.6 INTERFACES

Updated with administrative commands and write-ahead queue:

```python
[NEW]
class WriteAheadQueue:
    """In-memory queue for post-execution writes to SQLite."""
    
    def enqueue(self, operation: Callable[[], None]) -> None:
        """Add write operation to queue. Drops oldest if full."""
        ...
    
    def drain(self) -> int:
        """Attempt to write all queued operations to SQLite. Returns count written."""
        ...

class SkillLibrary:
    def __init__(self, db_path: str, config: SkillLibraryConfig):
        self._write_queue = WriteAheadQueue(config.queue_capacity)
        self._start_background_writer()
    
    # Administrative methods
    def list_templates(self, domain: Optional[str] = None, min_rating: float = 0.0) -> list[PlanTemplate]:
        ...
    def get_template(self, template_id: str) -> PlanTemplate:
        ...
    def delete_template(self, template_id: str) -> None:
        ...
    def purge_domain(self, domain: str) -> int:
        ...
    def stats(self) -> dict:
        ...
```

### 14.7 INTERACTIONS

Updated: All write methods (archive_plan, record_failure_pattern, add_to_allowlist) now go through the write-ahead queue instead of direct SQLite writes.

### 14.8 FAST PATH & 14.9 INTEGRATION RISK

Updated to reference the write-ahead queue, balanced decay function, tenant filtering, and administrative interface.

---

## 15-18. CROSS-CUTTING SECTIONS (A, B, C, D)

### A. SIMPLE CHAT

`[KARL-ACCEPTED]` Updated to include the output guardrail (section 2.5.A), factual disclaimer (section 2.5.C), and safety refusal detection (section 2.5.D) in the FAST path trace.

**Updated trace for "what is 2+2?":**

1. CLASSIFY: same as v1.
2. FAST EXECUTE: Model returns "4." Output guardrail scans: no dangerous content detected, no tool-call hallucination, no safety refusal. `output_guardrail_result = passed`. Disclaimer appended: "This is a quick answer -- for complex topics, I can do deeper research." Final output: "4. \n\n*Quick answer -- I can research this further if needed.*"
3. SYNTHESIZE (FAST pass-through): `quality_report = QualityReport(is_consistent=None, completeness_score=None, quality_review_performed=False)`.
4. EVALUATE: SUCCESS (FAST path). Output returned with disclaimer.

**Updated denylist false-positive concern (Karl's "what does rm -rf do?" example):**
`[KARL-COUNTER]` Karl argues the denylist cannot distinguish between "asking about" and "attempting" dangerous operations. This is correct -- the denylist is a pattern match, not a semantic classifier. But the system's response to this is architecturally correct: the query escalates to STANDARD, where the LLM-based classifier (or the planner) can distinguish intent. The false-positive cost is one classification call and one FAST-path latency budget. The false-negative cost of NOT escalating a genuine attack is unbounded. The conservative bias (escalate UP when uncertain) favors false positives. The denylist false-positive feedback loop (1.5.A) ensures that frequently-occurring false-positive patterns are identified and can be tuned.

### B. KNOWLEDGE/SCOPE GAPS

`[KARL-ACCEPTED]` Updated with:

1. **Implicit assumption detection:** A new subsection B.5 describes an "assumption surfacing" step in BACKBRIEF or PREMORTEM. Specifically, PREMORTEM's personas include a "Devil's Advocate" persona whose specific task is: "What did the planner assume that the user did not explicitly request?" This persona generates failure scenarios based on unstated assumptions. If critical assumptions are detected, they are surfaced in the APPROVAL briefing: "The plan assumes [assumption]. The user did not explicitly confirm this. Consider confirming before proceeding."

2. **Unknown unknowns:** The system cannot detect truly unknown unknowns (by definition). Mitigation: the Fast path factual disclaimer (2.5.C) is extended to STANDARD/DEEP: "This output is based on the available information. If the results seem incomplete or incorrect, please provide additional context." This is a standard disclaimer, not a structural fix.

3. **Per-session scope change detection:** Added a mechanism in CLASSIFY that compares the current `user_message` against the conversation history (`chat_history`). If the estimated scope (in terms of domain_tags, complexity, and tool requirements) has expanded by >50% compared to the initial request in the session, a `scope_change_detected` flag is set. This triggers a re-approval (user is asked: "This request seems significantly broader than your original question. Shall I proceed with the full analysis, or would you like to narrow the scope?").

4. **Cache miss vs. knowledge gap distinction:** RESEARCH output now includes `KnowledgeGap.gap_type` (either `"cache_miss"` or `"genuine_gap"`). `cache_miss` = no cached data found; the LLM might still know the answer. `genuine_gap` = cache miss AND LLM context gathering (if enabled) also returned uncertain. The gap response system (B.2) treats `genuine_gap` more severely than `cache_miss`.

### C. PLANNING DEAD-ENDS

`[KARL-ACCEPTED]` Updated with:

1. **FRAGO loop BACKBRIEF skip -- now mitigated:** The delta validation step (13.5.A) ensures structural consistency on every FRAGO delta, including DAG cycle detection. This means the FRAGO loop no longer moves DAG errors from plan-time to execute-time.

2. **Pre-execution tool availability check:** Added to RESEARCH (5.5.A). `tool_recommendations` from cache are validated against the current tool registry before being passed to PLAN and EXECUTE. This means tool unavailability is detected BEFORE execution, not during EXECUTE's compensation ladder.

3. **Resource feasibility persona:** PREMORTEM's persona set now includes a "Resource Analyst" persona (added to the standard set for DEEP path, available for STANDARD path). This persona's task: "Identify resource constraints that could prevent successful execution: memory limits, storage limits, API rate limits, timeout constraints, data volume constraints." This addresses Karl's point about impossible states requiring specific resource perspective.

4. **Dead-end detection labeled as proactive vs. reactive:** The dead-end detection table (C.1) now includes an explicit column:

| Dead-End Type | Detection Timing | Proactive/Reactive |
|---------------|-----------------|-------------------|
| Circular DAG | BACKBRIEF (plan-time) | **PROACTIVE** |
| Tool unavailability | RESEARCH + EXECUTE | **HYBRID** (tool check proactive; runtime failure reactive) |
| Impossible state assumption | PREMORTEM (pre-execution) | **PROACTIVE** (if persona catches it) |
| Pre-mortem ceiling hit | PREMORTEM | **PROACTIVE** (diagnosed, not prevented) |
| FRAGO replan ceiling hit | Graph topology | **REACTIVE** (after exhaustion) |
| Branching factor >= 1 | BRANCHING MONITOR + Runtime | **HYBRID** (static check proactive, runtime spawn reactive) |
| All sub-tasks fail | EVALUATE (post-execution) | **REACTIVE** |
| Approval rejection | APPROVAL GATE | **PROACTIVE** (user prevents) |

### D. PRODUCTION EDGE CASES

`[KARL-ACCEPTED]` Updated with:

1. **Checkpoint migration (D.1):** In addition to detection-and-abort on schema mismatch, a `migrate_checkpoint` function is specified:

```python
[NEW] D.1.1
def migrate_checkpoint(
    old_schema_version: int,
    new_schema_version: int,
    state_dict: dict,
) -> dict:
    """Migrate checkpoint state from old schema to new schema.
    
    Mapping: defined in a MIGRATION_MAP that maps (old_version, new_version)
    to transformation functions. Each transformation function takes the
    old state dict and returns a new state dict with default values for
    new fields.
    
    If no migration path exists for (old_version, new_version), the
    function raises MigrationPathNotFound and the pipeline aborts resume.
    """
    ...
```

The migration map is maintained in code and updated with each schema change. At minimum, it handles: adding new fields (use defaults), renaming fields (copy value), removing fields (drop). Complex migrations (changing field types) are NOT supported -- they require explicit migration functions written per deployment.

2. **PREMORTEM-over-BACKBRIEF priority (D.2, new subsection):** Explicit priority statement added: "PREMORTEM's semantic analysis overrides BACKBRIEF's structural analysis for the purpose of triggering plan regeneration. If BACKBRIEF passes (structurally sound) and PREMORTEM finds fatal flaws (semantically unsound), the plan is regenerated. If BACKBRIEF rejects (structurally broken), the plan is regenerated regardless of PREMORTEM's state. The graph topology enforces: BACKBRIEF runs first, then PREMORTEM. PREMORTEM only runs if BACKBRIEF passes."

3. **User-intent-change handling (D.3, new subsection):** When the user submits a fundamentally different request mid-pipeline:
   - If detected before APPROVAL: restart the pipeline from CLASSIFY with the new request. The previous plan state is preserved in the audit trail as "abandoned."
   - If detected during APPROVAL (user modifies the plan beyond recognition): the ApprovalGate detects that the modified plan's Commander's Intent diverges by >50% from the original (measured by embedding similarity or keyword overlap). It asks: "Your modifications significantly change the original task. Would you like to start fresh with a new request?" If yes, restart from CLASSIFY. If no, proceed with modified plan (but flag as HIGH risk due to scope change).
   - If detected after EXECUTE: too late for the current pipeline. The output is produced. If the user then says "that's not what I asked for," the skill library records a negative learning event.

4. **Learning scoping (D.4, new subsection):** Templates in the skill library are scoped by:
   - `scope: Literal["global", "project", "tenant"]`
   - Global templates: curated by administrators, visible to all.
   - Project templates: scoped to a specific project ID, visible to all users in that project.
   - Tenant templates: scoped to a tenant, not visible across tenants.
   - Template queries filter by the requesting context's scope. Global templates are always available as fallback.
   - This prevents cross-workflow contamination: a template from one user's coding style does not influence another user's plans unless they share a project or tenant scope.

5. **Observability architecture (D.5, new subsection):** Metrics and tracing for production operation:
   - **Per-node latency histograms:** Track p50, p95, p99 latency for each node (CLASSIFY, PLAN, BACKBRIEF, RESEARCH, RISK ASSESSMENT, PREMORTEM, BRANCHING MONITOR, APPROVAL, EXECUTE, SYNTHESIZE, EVALUATE, REPLAN).
   - **Pipeline invocation traces:** Each pipeline gets a unique `trace_id`. All log entries and metrics are tagged with it. LangGraph's built-in tracing is used.
   - **Error rate per node:** Track error count / total invocations for each node.
   - **Ceiling hit rate:** How often each ceiling (backbrief, premortem, replan, approval) is hit. High ceiling hit rates indicate systemic issues.
   - **Skill library metrics:** Queue depth, write latency, cache hit rate, template match rate.
   - **Alerting rules:**
     - Node error rate > 5% in 5-minute window: alert.
     - FRAGO ceiling hit rate > 20% in 1-hour window: alert (systemic execution quality issue).
     - Skill library write queue depth > 500: alert (write contention).
     - PREMORTEM persona false-positive rate > 0.3 for any persona: warn.
   - These metrics are exposed via a `/metrics` endpoint (Prometheus format) and integrated with standard monitoring infrastructure.

6. **Skill library bootstrapping (D.6, new subsection):** Curated seed templates for cold start:
   - Ship with 10-15 curated plan templates covering common task types: code generation, bug fixing, code review, documentation, data analysis, web research, deployment, testing, refactoring, architecture design, API integration, debugging, performance analysis, security review, configuration.
   - These curated templates are marked as `origin = "seed"` and have `use_count` starting at 5 (so they are not immediately outranked by a single-use-yesterday template).
   - Seed templates DO NOT decay with time (their `time_decay` factor is fixed at 1.0). They are replaced by learned templates when the learned templates accumulate sufficient `use_count` and `success_rating`.
   - Target: new deployments have ~10 tasks of "partially warm" instead of fully cold start.

---

## Structural Tension Resolutions (Consolidated)

This section documents all eight structural tensions Karl identified and their resolutions, for reference.

### Tension 1: PLAN Revision vs. REPLAN Delta -- Same Name, Different Reality

**Resolution applied in:** Sections 3, 13. See PLAN (3.1) for regeneration terminology, REPLAN (13.1) for delta terminology.

**Mechanism:** Graph-level assertion: `assert state.replan_count == 0, "PLAN cannot be re-entered during FRAGO replan loop"` in `PlanNode.plan()`. `assert state.premortem_cycle_count == 0, "REPLAN must not receive plan-time state"` in `ReplanNode.replan()`.

### Tension 2: BACKBRIEF + PREMORTEM Shared Counter

**Resolution applied in:** Sections 4, 7. Independent counters: `backbrief_revision_count` (max 2) and `premortem_cycle_count` (max 2).

**Mechanism:** Each is a separate field in `PipelineState`. Graph conditionals check the relevant counter independently. The combined worst case is 4 iterations, but structural soundness is never traded for cycle counting convenience.

### Tension 3: Isolated-State Executor vs. LangGraph Shared State

**Resolution applied in:** Section 10. LangGraph Subgraphs chosen over private-dict workaround. See 10.1, 10.5.A-C, 10.6 for full specification.

**`[ARBITRATION-REQUIRED: SUBGRAPH_PERFORMANCE]`** The Subgraph approach may introduce overhead for plans with many sub-tasks (e.g., 50+). Each Subgraph has its own checkpointer, which means N checkpoints for N parallel sub-tasks. For large plans, this checkpoint overhead may dominate execution time. **Recommendation:** Cap parallel sub-tasks at `concurrency_limit` (default 4) and batch sub-tasks into groups of `concurrency_limit` for sequential Subgraph phases. This limits checkpoint overhead to `concurrency_limit` concurrent checkpoints. **Both positions:** Karl would say "test this before committing" (correct -- implementation must verify). Richard says "the safety guarantee is worth the overhead, and batching limits the cost" (also correct -- this is the chosen design). The implementation should benchmark checkpoint overhead with 10, 20, 50 parallel sub-tasks and adjust batching if needed.

### Tension 4: FAST Path Denylist as Regex-Classifier-in-Disguise

**Resolution applied in:** Section 1.8, 1.5.A. Explicit architectural distinction: the denylist is a "safety pre-filter" making BINARY safety decisions (is this known-unsafe?), not QUALITATIVE classification decisions (is this complex/novel/multi-domain?). The denylist's scope is limited to FAST path escalation; it does not participate in STANDARD/DEEP routing. The denylist's matches are auditable and feed a false-positive feedback loop.

### Tension 5: Knowledge Gaps Flow -- Detected but Not Filled

**Resolution applied in:** Sections 5, B. Pre-execution gap severity assessment added. HIGH-severity knowledge gaps affecting HIGH/CRITICAL sub-tasks trigger Level 3 escalation before EXECUTE (section 5.5.B, section B.5).

### Tension 6: PREMORTEM and RISK ASSESSMENT -- Two Risk Systems, No Reconciliation

**Resolution applied in:** Section 9.10 (Risk Fusion). Reconciliation step added between PREMORTEM and APPROVAL: `final_risk[sub_task] = max(RISK_ASSESSMENT.risk_levels[sub_task], max(PREMORTEM.scenarios_for[sub_task].severity, default=LOW))`.

### Tension 7: BACKBRIEF/PREMORTEM Returning to PLAN -- No State Tracking

**Resolution applied in:** Sections 3, 7. Plan versioning added (`plan_version: int`, `plan_checksum: str`). PREMORTEM stores scenarios keyed by `plan_checksum`.

### Tension 8: Concurrent Requests + Single SQLite -- Contention Under Load

**Resolution applied in:** Section 14.5.F. Write-ahead queue added. Eliminates silent write drops.

---

## Design Decisions and Audit Trail

| Decision ID | Decision | Chosen Option | Key Rationale | Section |
|-------------|----------|---------------|---------------|---------|
| DD-001 | Isolated state model | LangGraph Subgraphs | True checkpoint isolation for parallel safety guarantee | 10.1, 10.5, 10.6 |
| DD-002 | FRAGO delta validation | Lightweight 3-check (DAG + branching + risk) | Structural integrity without full pipeline re-run cost | 13.5.A |
| DD-003 | Risk signal reconciliation | Automatic fusion before APPROVAL | Single reconciled signal for decision-making; individual signals preserved for drill-down | 9.10 |
| DD-004 | BACKBRIEF/PREMORTEM counters | Independent (2 each) | Never sacrifice structural soundness for cycle counting convenience | 4.1, 7.1 |
| DD-005 | Template decay function | Balanced formula with sqrt(use_count) + slow decay + failure penalty | Recency-weighted but not recency-dominated; penalizes failures | 14.5.A |
| DD-006 | Skill library concurrency | Write-ahead queue | Eliminate silent write drops; decouple pipeline completion from persistence | 14.5.F |
| DD-007 | Denylist architectural role | Safety pre-filter (not classifier) | Binary safety check, not qualitative classification; auditable, tunable | 1.8, 1.5.A |
| DD-008 | Pre-execution gap escalation | Level 3 for HIGH/CRITICAL sub-tasks with genuine gaps | Avoid wasted EXECUTE tokens on doomed tasks | 5.5.B |
| DD-009 | Evaluation caching | Cached per (output, criteria) pair within invocation | Prevent LLM nondeterminism from flipping evaluation results on replan | 12.5.B |
| DD-010 | No-criteria evaluation | UNEQUIVALENT status (not default SUCCESS) | Remove perverse incentive for vague criteria | 12.5.C |
| DD-011 | Learning scoping | Three-tier: global / project / tenant | Prevent cross-contamination while allowing curated seed templates | D.4 |
| DD-012 | Runtime branching monitor | Added as second component alongside static analyzer | Fulfill BRIEFING.md agreement for runtime branching factor monitoring | 8.1 |

---

## Unresolved Items for Arbitration

**`[ARBITRATION-REQUIRED: SUBGRAPH_PERFORMANCE]`**
See Tension 3 discussion above. The Subgraph approach for isolated state is the right design choice but may introduce checkpoint overhead for plans with many parallel sub-tasks. Recommended resolution: implement with batching (max 4 concurrent Subgraphs per phase), benchmark with 10/20/50 sub-tasks, adjust if overhead exceeds 20% of execution time.

**`[ARBITRATION-REQUIRED: DSM HEURISTIC COMPLETENESS]`**
The DSM heuristics in section 4.5.C cover tool overlap, resource overlap, and temporal overlap. They do NOT cover: network topology (sub-tasks that communicate over the network but don't share explicit resources), data dependencies (one sub-task's output format is implicitly required by another), or security domain crossings. These are deferred to Wave 3 when DSM can incorporate runtime traces. Recommended resolution: accept Wave 2 heuristics as sufficient for MVP, document the gap for Wave 3.

**`[ARBITRATION-REQUIRED: MULTI-TENANT SKILL LIBRARY ISOLATION]`**
Section 14.5.D specifies tenant filtering on template queries, but the SQLite database is still a single file. True multi-tenant isolation (separate database files per tenant) requires infrastructure changes (which database to connect to based on tenant ID). For Wave 2, a single SQLite file with tenant_id filtering is acceptable. For production multi-tenant deployments, this should be upgraded to separate databases. Recommended resolution: Wave 2 uses tenant_id filtering; Wave 3 upgrades to separate databases with connection routing.

---

*End of JORDAN v2 Granular Implementation Specification -- REVISION v2 (response to Karl critique)*
