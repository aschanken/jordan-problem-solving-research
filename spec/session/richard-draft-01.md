# JORDAN v2 Granular Implementation Specification -- DRAFT v1

**Author:** Richard the Lionheart (Claude Code)
**Date:** 2026-05-25
**Status:** Draft for review by Karl (Gemini CLI)
**Based on:** BRIEFING.md (agreements, prohibitions, resolutions), synthesis.md (Section 3 topology, Section 4 implementation plan, Section 10 risk register)

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

---

## 1. CLASSIFY (classifier.py)

### 1.1 FUNCTION & RATIONALE

Performs TAPE-inspired triage at pipeline entry to determine which of three execution paths (FAST, STANDARD, DEEP) the incoming request follows. Conservative classifier bias: any uncertainty escalates UP (FAST -> STANDARD, STANDARD -> DEEP). This node is the sole gatekeeper for pipeline path selection and must make its decision before any downstream processing begins.

### 1.2 FILE & LOCATION

- **Module:** `classifier.py` (new independent module, created during monolith split in Wave 2, never part of nodes.py)
- **Class:** `ClassifyNode`
- **Method:** `def classify(self, state: PipelineState) -> PipelineState`

### 1.3 INPUT

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `user_message` | `str` | Raw user input | The user's request text |
| `chat_history` | `list[dict]` | Session context | Previous messages for context (optional) |
| `system_classification` | `RiskLevel` | System baseline | Default MEDIUM for unauthenticated/unclassified (from CRT1 fix) |
| `denylist_patterns` | `list[Pattern]` | Configuration | Compiled regex patterns for FAST-path denylist |

### 1.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `pipeline_path` | `Literal["FAST", "STANDARD", "DEEP"]` | Graph router | Selected pipeline path |
| `complexity_factors` | `dict[str, float]` | Downstream nodes | Contributing factors: novelty, ambiguity, tool_requirements, domain_uncertainty |
| `denylist_triggered` | `bool` | Graph router | Whether FAST-path denylist was hit (enforces escalation to STANDARD) |
| `domain_tags` | `list[str]` | PLAN, RESEARCH | Domain classification tags (e.g., "code", "research", "math", "creative") |

### 1.5 EDGE CASES

**Empty input / missing fields:**
- Empty `user_message` (whitespace only, zero-length): return `pipeline_path = "STANDARD"` with `complexity_factors.ambiguity = 1.0`. Do not attempt to FAST-path empty input -- it may be an injection attempt.
- Missing `chat_history`: proceed with `user_message` only; no context penalty.

**Malformed input:**
- Extremely long input (>32K tokens): classify as DEEP (potential abuse or genuinely complex multi-step task). Truncate for classification only; full text preserved in state for downstream.
- Binary/non-UTF-8 content: reject with error before classification. CLASSIFY operates on text only.
- Known prompt injection patterns: escalate to STANDARD or DEEP. Flag `denylist_triggered = True`.

**LLM call failure / timeout:**
- Primary classifier (LLM-based, Wave 2) fails or times out: fall back to regex-based classifier (same logic as Wave 1, retained as emergency backup). `pipeline_path = "STANDARD"` on total failure.
- Secondary regex classifier fails (corrupted pattern list): `pipeline_path = "STANDARD"` (safest default per agreement).

**State corruption:**
- CLASSIFY is the first node to read `PipelineState`. If state is already corrupted (e.g., from checkpointer corruption), CLASSIFY can detect: check for non-empty state with impossible values. Log warning and reinitialize with defaults.

**Infinite loops / runaway recursion:**
- CLASSIFY is called exactly once per pipeline invocation. No loop risk. Graph topology enforces single entry.

**Token budget exhaustion:**
- CLASSIFY LLM call uses a small, cheap model (e.g., DeepSeek Flash or similar high-throughput model). If even this call fails due to token budget, fall back to regex classifier. CLASSIFY should never consume more than 1-2% of per-invocation token budget.

**Tool call failure:**
- CLASSIFY does not invoke tools. No tool call failure mode.

**Confidence/classification boundary cases:**
- Edge between FAST and STANDARD: conservative bias escalates to STANDARD. The system over-classifies toward more compute rather than less.
- Edge between STANDARD and DEEP: multi-COA or MAKER decomposition trigger. If `domain_tags` include "safety-critical", "security", or "deployment": escalate to DEEP. If `novelty` factor > 0.7: escalate to DEEP.
- Ambiguous domains (task could be in multiple domains): include ALL matching domain tags. Priority to highest-risk domain.
- User overrides classification: user can explicitly request "use deep analysis" or "quick answer". CLASSIFY respects explicit user intent but still applies safety overrides (denylist, safety-critical domains).

### 1.6 INTERFACES

```python
@dataclass
class ClassificationResult:
    pipeline_path: Literal["FAST", "STANDARD", "DEEP"]
    complexity_factors: dict[str, float]
    denylist_triggered: bool
    domain_tags: list[str]
    model_used: str  # For audit trail

class ClassifyNode:
    """TAPE-inspired triage node. Entry point for all pipeline paths."""

    def __init__(
        self,
        llm_client: Any,  # Cheap/fast model client
        regex_classifier: RegexClassifier,  # Fallback classifier
        denylist: DenylistConfig,
        config: ClassifyNodeConfig,
    ):
        ...

    def classify(self, state: PipelineState) -> PipelineState:
        """Classify the user request and set pipeline path.

        Returns:
            PipelineState with pipeline_path, complexity_factors,
            denylist_triggered, and domain_tags populated.
        """
        ...
```

### 1.7 INTERACTIONS

- **Triggered by:** Pipeline entry. LangGraph routes from `__start__` to CLASSIFY unconditionally.
- **Triggers:** Conditional graph edge based on `pipeline_path`:
  - `"FAST"` -> FAST EXECUTE (if `denylist_triggered == False`)
  - `"FAST"` with `denylist_triggered == True` -> PLAN (escalated to STANDARD)
  - `"STANDARD"` -> PLAN
  - `"DEEP"` -> PLAN (with DEEP-flag in state)
- **State transition:** Sets `state.pipeline_path`, `state.complexity_factors`, `state.denylist_triggered`, `state.domain_tags`. Unchanged fields propagate as-is.
- **Re-entry:** CLASSIFY is never re-entered within a single pipeline invocation. Re-classification does not occur on replan.

### 1.8 FAST PATH

**What constitutes "simple":**
- Single sentence or short query (< 100 words)
- Factual question with deterministic answer
- No tool invocation required (the model answers from knowledge)
- No ambiguity in what is being asked
- No code execution, file system access, network calls, or system commands
- Single-domain, single-step resolution
- Examples: "what is 2+2?", "what is the capital of France?", "explain a for-loop"

**Denylist checks that fire on FAST path:**
1. Code execution patterns (`exec(`, `eval(`, `subprocess.`, `os.system`, `shutil.`, `Path(...).write`)
2. File system access (`read file`, `write file`, /path/ references)
3. Network calls (URLs, `requests.`, `curl`, `wget`)
4. System commands (`sudo`, `apt`, `pip install`, `npm install`, `docker`)
5. Security-sensitive domains (`password`, `key`, `credential`, `token`, `secret`)
6. Known prompt injection markers (special tokens, instruction override attempts)

**When FAST escalates to STANDARD:**
- ANY denylist pattern matches: immediately escalate to PLAN (STANDARD pipeline). The denylist check happens AFTER the TAPE classification, so even a text that would otherwise be classified as FAST gets escalated if it mentions tools or system access.
- User explicitly requests tools/execution: escalate.
- The simple answer would require reading a file or making a network call: escalate.
- Input length exceeds FAST path threshold (100 words): escalate.
- Multiple question marks or conjunctive queries: escalate.

### 1.9 INTEGRATION RISK

The hardest thing about integrating CLASSIFY is **calibrating the conservative bias correctly**. If too conservative, everything goes to STANDARD or DEEP and the FAST path is never used (losing the speed benefit). If not conservative enough, unsafe inputs reach FAST EXECUTE where there are no guardrails. The Wave 1 regex patched classifier provides the fallback baseline; the Wave 2 LLM-based classifier needs A/B testing against the regex baseline for at least 50-100 real inputs before rolling out as primary.

Second-hardest: **maintaining the denylist**. It must be updated as new attack patterns emerge, but the update mechanism must not create new bypasses. The denylist is a list of compiled regex patterns loaded from configuration at startup.

---

## 2. FAST EXECUTE (executor.py)

### 2.1 FUNCTION & RATIONALE

Lightweight execution path for trivial queries that bypasses the full pipeline (PLAN, RESEARCH, RISK, PREMORTEM, BACKBRIEF, APPROVAL, EXECUTE). Runs a single LLM call with no tool access and returns the result directly. This provides sub-second latency for simple queries while maintaining safety via the CLASSIFY denylist (which already checked for tool needs and unsafe patterns before routing here).

### 2.2 FILE & LOCATION

- **Module:** `executor.py`
- **Class:** `FastExecuteNode`
- **Method:** `def fast_execute(self, state: PipelineState) -> PipelineState`

### 2.3 INPUT

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `user_message` | `str` | CLASSIFY | Original user input |
| `pipeline_path` | `Literal["FAST", ...]` | CLASSIFY | Must be "FAST" |
| `denylist_triggered` | `bool` | CLASSIFY | Must be `False` |
| `complexity_factors` | `dict` | CLASSIFY | For logging/telemetry |
| `chat_history` | `list[dict]` | Session | Context for the LLM response |

### 2.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `fast_response` | `str` | SYNTHESIZE | The direct response to the user |
| `execution_metadata` | `dict` | Logging/Audit | Model used, latency, token count, path taken |

### 2.5 EDGE CASES

**Empty input / missing fields:**
- `user_message` empty: return error response "No input provided." Do not attempt LLM call.
- `pipeline_path` is not "FAST": raise `InvalidPipelinePathError`. This is a graph topology violation -- CLASSIFY should have prevented this.
- `denylist_triggered` is `True` despite being routed here: escalate to STANDARD. This could only happen from a graph topology bug.

**Malformed input:**
- `user_message` contains non-UTF-8 text: strip to valid UTF-8, proceed. FAST EXECUTE is the first text-generation point; it must handle encoding gracefully.
- Excessively long input (should not happen due to CLASSIFY's FAST path length limit): truncate to FAST_EXECUTE max tokens (configurable, default 4096).

**LLM call failure / timeout:**
- Primary LLM call fails or times out: retry once with same model. If retry fails, return graceful error "I encountered a temporary issue processing your request."
- Model unavailable: switch to fallback model. If no fallback available, return graceful error.

**State corruption:**
- FAST EXECUTE reads `state.fast_response` before writing -- it should be `None`/unset. If already set, this is a re-entry bug. Log warning and overwrite.

**Infinite loops / runaway recursion:**
- Single LLM call, no recursion. No loop risk.

**Token budget exhaustion:**
- Budget already consumed by CLASSIFY? Unlikely (CLASSIFY is cheap). If primary call exceeds budget, skip retry, return error.

**Tool call failure:**
- FAST EXECUTE does not use tools. If the LLM unexpectedly produces a tool call (model hallucination), intercept and strip, return text-only response. Log the hallucination for monitoring.

**Confidence/classification boundary cases:**
- The LLM may indicate uncertainty ("I'm not sure"). FAST EXECUTE should detect this: if response contains confidence qualifiers ("I think", "maybe", "I'm not sure", "I don't know"), flag for potential STANDARD escalation. Since FAST EXECUTE cannot trigger replan, it should append a confidence disclaimer to the response.

### 2.6 INTERFACES

```python
@dataclass
class FastExecuteResult:
    fast_response: str
    execution_metadata: dict
    uncertainty_detected: bool
    hallucination_detected: bool

class FastExecuteNode:
    """Lightweight single-LLM-call execution for trivial queries."""

    def __init__(
        self,
        llm_client: Any,
        config: FastExecuteConfig,
        logger: Logger,
    ):
        ...

    def fast_execute(self, state: PipelineState) -> PipelineState:
        """Execute a single LLM call with no tools for simple queries.

        Returns:
            PipelineState with fast_response and execution_metadata set.
            Does NOT set sub_task_results or plan -- those remain None.
        """
        ...
```

### 2.7 INTERACTIONS

- **Triggered by:** CLASSIFY when `pipeline_path == "FAST"` and `denylist_triggered == False`.
- **Triggers:** SYNTHESIZE unconditionally (SYNTHESIZE handles both FAST and STANDARD result assembly).
- **Does NOT trigger:** PLAN, RESEARCH, RISK, PREMORTEM, BACKBRIEF, APPROVAL, EXECUTE -- bypasses the entire standard pipeline.
- **State transition:** Sets `state.fast_response` and `state.execution_metadata`. All other fields remain at defaults (None/empty).
- **Safety invariant:** Before the LLM call, verify `denylist_triggered == False`. If somehow `True`, raise and reroute to STANDARD path.

### 2.8 FAST PATH

**Model selection:** Use the cheapest available model (DeepSeek Flash or similar high-throughput model). No model routing logic -- always the same model.

**Denylist (pre-call):** Not applicable here; CLASSIFY already checked the denylist. If an edge case reaches FAST EXECUTE with denylist_triggered, it escalates (see 2.5).

**Response length limit:** Maximum 2048 tokens output. If the model produces more, truncate.

**Uncertainty detection:** Post-response, scan the output for phrases indicating low confidence. If detected, append to `execution_metadata.uncertainty_detected = True`. The SYNTHESIZE node may add a disclaimer.

**Escalation to STANDARD:** FAST EXECUTE does not escalate mid-flight. The escalation decision is CLASSIFY's. However, if the LLM unexpectedly requests a tool or produces an unsafe response, the output guardrail (post-hoc) intercepts and logs.

### 2.9 INTEGRATION RISK

The hardest thing about FAST EXECUTE is **preventing model hallucination of tool calls**. The model is instructed not to use tools, but models can still hallucinate tool invocations. The executor must intercept any tool call output from the model and strip it before returning, logging the incident. This requires the executor to be model-agnostic about the response format.

Second-hardest: **FAST EXECUTE has no guardrails beyond input filtering.** If a model hallucinates a dangerous response (e.g., providing instructions for something harmful), there is no downstream guard. The quality of FAST EXECUTE is entirely dependent on CLASSIFY's denylist and the base model's safety training.

---

## 3. PLAN (planner.py)

### 3.1 FUNCTION & RATIONALE

Generates an execution plan using Commander's Intent format: goals, constraints, and acceptance criteria rather than prescriptive step-by-step JSON. Seeds the plan from skill library templates when available. Produces a DAG of sub-tasks with explicit dependencies. Bias toward zero-overlap sub-tasks to minimize parallel state conflicts. The plan defines WHAT to do and WHY, not precisely HOW -- execution autonomy is preserved.

### 3.2 FILE & LOCATION

- **Module:** `planner.py` (split from nodes.py monolith in Wave 2)
- **Class:** `PlanNode`
- **Method:** `def plan(self, state: PipelineState) -> PipelineState`

### 3.3 INPUT

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `user_message` | `str` | CLASSIFY | Original user input |
| `pipeline_path` | `Literal["FAST", "STANDARD", "DEEP"]` | CLASSIFY | Pipeline path (STANDARD or DEEP) |
| `complexity_factors` | `dict` | CLASSIFY | Complexity breakdown |
| `domain_tags` | `list[str]` | CLASSIFY | Domain classification |
| `skill_library` | `SkillLibrary` | Cross-cutting | Reference to skill library for template seeding |
| `chat_history` | `list[dict]` | Session | Conversation context for plan relevance |

### 3.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `plan` | `Plan` | BACKBRIEF | Full plan structure with Commander's Intent |
| `commander_intent` | `CommanderIntent` | APPROVAL, EVALUATE | Goals, constraints, acceptance criteria |
| `sub_tasks` | `list[SubTaskDef]` | BACKBRIEF | DAG of sub-task definitions |
| `plan_seeded_from_skill` | `bool` | Telemetry | Whether plan was seeded from skill library |
| `plan_source` | `str` | Audit | "fresh", "skill_template", or "replan" |

### 3.5 EDGE CASES

**Empty input / missing fields:**
- `user_message` empty: PLAN should not be reached (CLASSIFY would have error-handled). If reached, return a minimal plan with single sub-task "Respond to user: clarification needed."
- No `domain_tags` from CLASSIFY: CLASSIFY always sets domain_tags (default `["general"]`). If missing, assume general.

**Malformed input:**
- `complexity_factors` missing critical keys: use defaults (all 0.5). Log warning.
- `pipeline_path` is "FAST": should not reach PLAN. Log error and create a minimal STANDARD plan.

**LLM call failure / timeout:**
- Primary planner LLM fails: retry once. If retry fails, attempt skill library template retrieval as fallback (generate plan from closest template match, if available).
- Total failure (no LLM, no template): fail pipeline with "Failed to generate plan." Do NOT proceed with an empty plan -- this would cause downstream errors.
- Partial failure (plan generated but incomplete): flag `plan_source = "partial_failure"`, continue with what was generated.

**State corruption:**
- `state.plan` already set from a previous attempt (should not happen in normal flow, but can on replan): REPLAN produces a `delta_plan`, not a full plan. PLAN only runs on first pass. If PLAN is re-entered via graph error, check `state.metadata.pipeline_phase` and raise if not "planning".

**Infinite loops / runaway recursion:**
- PLAN is called once per pipeline invocation (not part of replan loop). No recursion risk. The PREMORTEM->PLAN->BACKBRIEF loop has its own ceiling (max 2 cycles) managed by graph-level conditional edges.

**Token budget exhaustion:**
- Plan generation can be token-intensive (1000-4000 tokens for complex plans). If budget is nearly exhausted, use a more concise plan format (Commander's Intent abbreviated -- goals only, skip detailed constraints).
- Budget check: before PLAN LLM call, check remaining token budget. If < 20% of total, warn in metadata.

**Tool call failure:**
- PLAN does not invoke tools. The planner only generates a plan; execution comes later.

**Confidence/classification boundary cases:**
- Plan with very low confidence (planner self-assessment < 0.3): flag for pre-mortem escalation (increase iteration ceiling for PREMORTEM).
- Plan with ambiguous acceptance criteria: BACKBRIEF should flag this. If BACKBRIEF accepts it, the ambiguity is considered acceptable.

### 3.6 INTERFACES

```python
@dataclass
class CommanderIntent:
    """Commander's Intent format -- WHAT and WHY, not HOW."""
    goal: str
    constraints: list[str]
    acceptance_criteria: list[str]
    priority: Literal["low", "medium", "high", "critical"]

@dataclass
class SubTaskDef:
    """Single sub-task in the execution DAG."""
    id: str  # UUID
    description: str
    tools_required: list[str]
    dependencies: list[str]  # IDs of sub-tasks that must complete first
    domain: str
    risk_level: Optional[RiskLevel]  # Set by RISK ASSESSMENT later
    isolation_key: Optional[str]  # For parallel isolation (same key = sequential)

@dataclass
class Plan:
    commander_intent: CommanderIntent
    sub_tasks: list[SubTaskDef]
    dag: dict[str, list[str]]  # adj list: sub_task_id -> [dependent_ids]
    metadata: dict

class PlanNode:
    """Generates execution plan in Commander's Intent format."""

    def __init__(
        self,
        llm_client: Any,
        skill_library: SkillLibrary,
        config: PlannerConfig,
    ):
        ...

    def plan(self, state: PipelineState) -> PipelineState:
        """Generate plan from user input, seeded by skill library.

        Returns:
            PipelineState with plan, commander_intent, and sub_tasks populated.
        """
        ...
```

### 3.7 INTERACTIONS

- **Triggered by:** CLASSIFY when `pipeline_path in ("STANDARD", "DEEP")`.
- **Triggers:** BACKBRIEF unconditionally for STANDARD/DEEP paths.
- **Receives from:** Skill library (template seeding, domain-matched patterns).
- **State transition:** Sets `state.plan`, `state.commander_intent`, `state.sub_tasks`, `state.plan_seeded_from_skill`.
- **Re-entry from BACKBRIEF:** If BACKBRIEF flags the plan, the graph routes back to PLAN for revision. The revision uses the same `plan()` method but receives the previous plan and BACKBRIEF's flags as additional context. Max 2 revisions.
- **Re-entry from PREMORTEM:** If PREMORTEM finds fatal flaws, routes back to PLAN. Then BACKBRIEF re-runs. Max 2 cycles total (PREMORTEM -> PLAN -> BACKBRIEF).
- **On replan:** REPLAN (not PLAN) generates the delta. PLAN is not re-entered during replan cycles.

### 3.8 FAST PATH

Not applicable. PLAN is bypassed in the FAST path.

For STANDARD path:
- Plan uses single-COA (Course of Action)
- Default to parallel execution
- Sub-tasks sized per WBS 8-80 rule (8-80 seconds of agent work each)

For DEEP path:
- Multi-COA generation (2-3 alternatives)
- MAKER m=1 decomposition for correctness-critical, mechanically verifiable sub-tasks
- Default to sequential execution
- Higher pre-mortem iteration ceiling (3 vs. 2)

### 3.9 INTEGRATION RISK

The hardest thing about PLAN is **Commander's Intent format adoption**. Changing from prescriptive step-by-step JSON to goals/constraints/acceptance-criteria changes the contract between PLAN and EXECUTE (and between PLAN and EVALUATE). All downstream nodes that parse the plan must be updated. This is not a large code change but a pervasive interface change.

Second-hardest: **skill library integration.** The plan node must query the skill library (which may be empty or have poor matches), merge template suggestions with the LLM-generated plan, and correctly identify when a template was used. The skill library is initialized with zero entries; having useful templates requires at least 10-20 tasks to have been executed and archived.

---

## 4. BACKBRIEF (backbrief.py)

### 4.1 FUNCTION & RATIONALE

Verifies the plan before resources are committed to it. Performs two analyses: (1) DAG consistency check -- validates that the sub-task DAG has no circular dependencies, all dependencies exist, and the graph is a valid DAG; (2) DSM (Design Structure Matrix) analysis -- detects hidden couplings between sub-tasks that share implicit resources but have no declared dependency. If flags are raised, the plan is routed back to PLAN for revision (max 2 revisions).

### 4.2 FILE & LOCATION

- **Module:** `backbrief.py` (new independent module, never part of nodes.py)
- **Class:** `BackbriefNode`
- **Methods:** `def verify(self, state: PipelineState) -> PipelineState`, `def _check_dag_consistency(dag: dict) -> DagResult`, `def _analyze_dsm(sub_tasks: list[SubTaskDef]) -> DsmResult`

### 4.3 INPUT

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `plan` | `Plan` | PLAN | Full plan structure |
| `sub_tasks` | `list[SubTaskDef]` | PLAN | Individual sub-task definitions |
| `commander_intent` | `CommanderIntent` | PLAN | Goals and constraints for context |
| `revision_count` | `int` | Graph state | Current revision number (0 for first pass) |
| `domain_tags` | `list[str]` | CLASSIFY | Domain context for DSM coupling heuristics |

### 4.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `verification_result` | `VerificationResult` | Graph router | Pass/fail with details |
| `dag_result` | `DagResult` | Audit | DAG check details |
| `dsm_result` | `DsmResult` | Audit, PLAN | DSM analysis with coupled pairs |
| `backbrief_flags` | `list[BackbriefFlag]` | PLAN, PREMORTEM | Specific issues found |
| `revision_count` | `int` | Graph state | Incremented if revision needed |

### 4.5 EDGE CASES

**Empty input / missing fields:**
- `sub_tasks` empty: flag immediately. Plan with no sub-tasks cannot execute.
- `plan` missing: cannot verify. Raise `MissingPlanError`.
- `dag` field of plan is empty dict: compute DAG from sub_task dependencies (backwards-compatible).

**Malformed input:**
- DAG with self-loops (sub-task depends on itself): flag as circular dependency.
- Missing sub-task IDs referenced in dependencies: flag as broken reference.
- Duplicate sub-task IDs: flag as ID collision.

**DAG consistency edge cases:**
- Empty DAG (no edges, single sub-task): pass (trivially valid).
- Disconnected sub-graphs: warning (not error). May be intentional for independent workstreams.
- Very large DAG (>50 sub-tasks): DSM analysis becomes O(n^2). For large DAGs, skip full DSM and only validate explicit dependencies. Log warning.
- Circular dependency: hard fail. Route back to PLAN.
- Diamond dependency (A->B, A->C, B->D, C->D): valid DAG structure, no flag.

**DSM analysis edge cases:**
- No hidden couplings detected: clean pass.
- All sub-tasks coupled to all others: signal that the plan is too granular or that decomposition is wrong. Flag for PLAN revision.
- False positives (DSM flags a shared resource that is intentional): acceptable -- routing back to PLAN for clarification is low cost. Better false positive than false negative.

**Revision ceiling:**
- If `revision_count >= 2` and BACKBRIEF still flags: force-pass (override to accept the plan). This prevents infinite PLAN->BACKBRIEF loops. Log warning.
- After force-pass, annotate plan metadata with `backbrief_forced: true`.

**LLM call failure / timeout:**
- BACKBRIEF's DSM analysis does not use LLM calls. It is purely algorithmic. No LLM failure mode.
- If DAG check is algorithmic, there is no LLM failure mode here either.

**State corruption:**
- BACKBRIEF modifies `state.verification_result` and `state.backbrief_flags`. If these are already set from a previous run, this is a re-entry -- increment revision counter and proceed.

### 4.6 INTERFACES

```python
@dataclass
class DagResult:
    is_valid_dag: bool
    has_circular_dependency: bool
    has_broken_references: bool
    has_self_loops: bool
    disconnected_subgraphs: list[list[str]]
    node_count: int
    edge_count: int

@dataclass
class DsmResult:
    hidden_couplings: list[tuple[str, str]]  # (sub_task_a, sub_task_b)
    coupling_severity: float  # 0.0 (none) to 1.0 (all coupled)
    domain: str
    analysis_skipped: bool  # True if DAG was too large for DSM

@dataclass
class BackbriefFlag:
    severity: Literal["error", "warning", "info"]
    category: Literal["dag", "dsm", "missing_field", "other"]
    description: str
    affected_sub_tasks: list[str]

@dataclass
class VerificationResult:
    passed: bool
    forced: bool  # True if passed due to ceiling
    flags: list[BackbriefFlag]
    dag: DagResult
    dsm: DsmResult

class BackbriefNode:
    """DAG consistency and DSM hidden-coupling verification."""

    def __init__(self, config: BackbriefConfig):
        ...

    def verify(self, state: PipelineState) -> PipelineState:
        """Verify plan consistency and detect hidden couplings.

        Returns:
            PipelineState with verification_result, dag_result,
            dsm_result, backbrief_flags, and revision_count populated.
        """
        ...
```

### 4.7 INTERACTIONS

- **Triggered by:** PLAN (after initial plan generation or after PLAN revision).
- **Triggers:**
  - On `passed == True`: RESEARCH node (proceed to research phase).
  - On `passed == False` and `revision_count < 2`: PLAN (revision with backbrief_flags as additional context).
  - On `passed == False` and `revision_count >= 2`: force-pass, proceed to RESEARCH. Log "Backbrief ceiling reached -- plan accepted with flags."
- **Receives from:** No upstream node besides PLAN. BACKBRIEF is algorithmic and does not call LLMs or external services.
- **State transition:** Sets `state.verification_result`, `state.backbrief_flags`. Modifies `state.revision_count` (increments).
- **Re-entry from PREMORTEM:** When PREMORTEM triggers plan revision, BACKBRIEF must re-run on the revised plan. The revision counter is shared between PLAN->BACKBRIEF and PREMORTEM->PLAN->BACKBRIEF cycles.

### 4.8 FAST PATH

Not applicable. BACKBRIEF is bypassed in the FAST path.

### 4.9 INTEGRATION RISK

The hardest thing about BACKBRIEF is **DSM analysis implementation**. DSM is a well-understood algorithm in engineering design but requires domain-specific heuristics to determine what constitutes a "hidden coupling." For software tasks, hidden couplings include: shared file access, shared database tables, conflicting environment variables, shared API rate limits, and overlapping port usage. These heuristics must be encoded and maintained.

Second-hardest: **the BACKBRIEF revision loop ceiling**. The shared counter between PREMORTEM->PLAN and PLAN->BACKBRIEF revisions creates a combined iteration space. Must ensure the total combined revisions (PREMORTEM->PLAN revisions + PLAN->BACKBRIEF revisions) do not exceed the hard ceiling (2). Otherwise the loops can nest to produce more iterations than intended.

---

## 5. RESEARCH (synthesizer.py)

### 5.1 FUNCTION & RATIONALE

Queries the skill library's research cache for information relevant to the planned task. Uses TTL-based caching: results expire after a configurable period (default 24 hours for general knowledge, 7 days for domain-specific results). If the cache misses or results are stale, the RESEARCH node may optionally invoke an LLM call to gather context from the model's knowledge (but does NOT perform web search or tool-based research -- that would require EXECUTE-level permissions).

### 5.2 FILE & LOCATION

- **Module:** `synthesizer.py` (contains `ResearchNode` class alongside `SynthesizeNode`)
- **Class:** `ResearchNode`
- **Method:** `def research(self, state: PipelineState) -> PipelineState`

### 5.3 INPUT

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `plan` | `Plan` | BACKBRIEF | Verified plan |
| `domain_tags` | `list[str]` | CLASSIFY | Domain classification for cache lookup |
| `sub_tasks` | `list[SubTaskDef]` | PLAN (via BACKBRIEF) | Individual task definitions with tools required |
| `skill_library` | `SkillLibrary` | Cross-cutting | Reference for cache queries |

### 5.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `research_findings` | `dict[str, Any]` | RISK ASSESSMENT | Per-domain research results |
| `research_cache_hit` | `bool` | Telemetry | Whether research was served from cache |
| `tool_recommendations` | `list[str]` | EXECUTE | Recommended tools/approaches for each sub-task |
| `knowledge_gaps` | `list[str]` | RISK ASSESSMENT | Areas where information is insufficient |

### 5.5 EDGE CASES

**Empty input / missing fields:**
- `plan` missing: RESEARCH requires a verified plan. Raise `MissingPlanError`.
- `domain_tags` empty: search all caches. The cost is slightly higher but tolerable.
- `sub_tasks` empty: RESEARCH is still meaningful (general domain research even without specific sub-tasks).

**Malformed input:**
- `domain_tags` contain invalid/unknown domains: treat as "general" domain. Log warning.

**Cache miss:**
- No cache entry for the domain: return empty `research_findings`. Do NOT trigger LLM research by default. This is a deliberate design choice -- RESEARCH is a cache, not a research engine. LLM-based context gathering is optional and configurable.
- Stale cache entry (TTL expired): return stale data with `stale: True` flag. Include `last_updated` timestamp so downstream nodes can weight the information appropriately.

**LLM call failure / timeout (optional LLM context gathering only):**
- If optional LLM call is enabled and fails: return empty findings. Cache miss is acceptable.
- If LLM is enabled but times out: return partial results. Do not block the pipeline.

**State corruption:**
- `research_findings` already set (should not happen on first pass but could on replan): overwrite. FRAGO replan creates new research context; old findings are stale.

**Token budget exhaustion:**
- Optional LLM call: skip if token budget < 10% remaining. Cache-only mode.

**Tool call failure:**
- RESEARCH does not invoke external tools. No tool call failure mode.

### 5.6 INTERFACES

```python
@dataclass
class ResearchFindings:
    domain: str
    findings: dict[str, Any]
    cache_hit: bool
    stale: bool
    last_updated: Optional[datetime]
    knowledge_gaps: list[str]

class ResearchNode:
    """Skill library research cache lookup node."""

    def __init__(
        self,
        skill_library: SkillLibrary,
        llm_client: Optional[Any],  # None = cache-only mode
        config: ResearchConfig,
    ):
        ...

    def research(self, state: PipelineState) -> PipelineState:
        """Query skill library cache for domain-relevant knowledge.

        Returns:
            PipelineState with research_findings, tool_recommendations,
            and knowledge_gaps populated.
        """
        ...
```

### 5.7 INTERACTIONS

- **Triggered by:** BACKBRIEF (when verification passes).
- **Triggers:** RISK ASSESSMENT unconditionally for STANDARD/DEEP paths.
- **Receives from:** Skill library (cache queries).
- **State transition:** Sets `state.research_findings`, `state.research_cache_hit`, `state.tool_recommendations`, `state.knowledge_gaps`.
- **On replan:** RESEARCH runs again after FRAGO replanning (because new sub-tasks may need different research context). Cache hit rate should be higher on replan since the domain context is not changing.

### 5.8 FAST PATH

Not applicable. RESEARCH is bypassed in the FAST path.

### 5.9 INTEGRATION RISK

The hardest thing about RESEARCH is **keeping the cache relevant without making it stale**. TTL-based expiry is crude -- a 24-hour TTL will evict useful data and keep useless data. A better approach (deferred to Wave 3) is access-frequency-based eviction. For Wave 2, TTL with override capability (users can pin cache entries) is sufficient.

Second-hardest: **the optional LLM call behavior.** If enabled, RESEARCH is no longer a simple cache lookup and becomes an LLM call with its own failure modes. If disabled, RESEARCH is trivially fast but provides no value on cache miss. The configuration must be explicit about which mode is active.

---

## 6. RISK ASSESSMENT (guardrails.py)

### 6.1 FUNCTION & RATIONALE

Per-sub-task risk classification using an LLM-based classifier (Wave 2). Replaces the Wave 1 regex classifier with context-aware classification that can distinguish between similar-looking commands in different contexts (e.g., `rm -rf /tmp/build` vs `rm -rf /etc`). Classifies each sub-task as LOW, MEDIUM, HIGH, or CRITICAL risk. Default-deny for unclassified sub-tasks. On replan, only re-classifies changed sub-tasks (not the entire plan).

### 6.2 FILE & LOCATION

- **Module:** `guardrails.py` (split from nodes.py monolith in Wave 2)
- **Class:** `RiskAssessmentNode`
- **Method:** `def assess_risk(self, state: PipelineState) -> PipelineState`

### 6.3 INPUT

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `sub_tasks` | `list[SubTaskDef]` | PLAN (via RESEARCH) | All sub-tasks to classify |
| `research_findings` | `ResearchFindings` | RESEARCH | Domain context for classification |
| `tool_recommendations` | `list[str]` | RESEARCH | Tools involved in each sub-task |
| `knowledge_gaps` | `list[str]` | RESEARCH | Areas of uncertainty |
| `plan` | `Plan` | PLAN | Overall context (goals, constraints) |
| `previous_risk_levels` | `Optional[dict[str, RiskLevel]]` | Graph state | Risk levels from prior cycle (used on replan to identify changed sub-tasks) |

### 6.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `risk_levels` | `dict[str, RiskLevel]` | PREMORTEM, APPROVAL | Per sub-task_id -> RiskLevel |
| `overall_risk` | `RiskLevel` | APPROVAL, PREMORTEM | Highest risk across all sub-tasks |
| `risk_justifications` | `dict[str, str]` | APPROVAL, Audit | Per sub-task classification justification |

### 6.5 EDGE CASES

**Empty input / missing fields:**
- `sub_tasks` empty: return `OVERALL_RISK = MEDIUM` with empty per-task dict. Pipeline should not proceed without sub-tasks (BACKBRIEF would have caught this), but risk assessment should not crash.
- Missing `research_findings`: proceed without domain context. Classification may be more conservative (more MEDIUM and HIGH) without context.

**Malformed input:**
- `sub_tasks` with missing `id` field: assign a temporary ID. Log error.
- `sub_tasks` with fields that don't match schema: skip classification for that sub-task, mark as MEDIUM with justification "schema_error".

**LLM call failure / timeout:**
- Primary LLM classifier fails: fall back to regex classifier (Wave 1 classifier, retained as emergency backup). This is the same fallback used in CLASSIFY.
- Regex fallback also fails: default all sub-tasks to MEDIUM. Log critical alert -- the risk classifier is completely down.
- Partial failure (some sub-tasks classified, some not): classify failed sub-tasks as MEDIUM individually. Do NOT aggregate to the highest.

**State corruption:**
- `state.risk_levels` already set (re-entry from replan): compare with `previous_risk_levels`. Only re-classify sub-tasks whose definitions changed (FRAGO delta). For unchanged sub-tasks, carry forward previous risk level.

**Infinite loops / runaway recursion:**
- Single LLM call per sub-task (or per batch). No recursion risk.

**Token budget exhaustion:**
- LLM-based classification for many sub-tasks (50+) could consume significant tokens. Batch classification (10 sub-tasks per call) reduces overhead. If budget is low, fall back to regex classifier.
- Priority: classify HIGH/CRITICAL sub-tasks first (tool-using, file-modifying). LOW/MEDIUM sub-tasks can fall back to regex if budget is low.

**Tool call failure:**
- RISK ASSESSMENT does not invoke tools. No tool call failure mode.

**Confidence/classification boundary cases:**
- Edge between MEDIUM and HIGH: default to HIGH. Conservative bias. The user would rather see too many approval requests than miss a dangerous action.
- Edge between HIGH and CRITICAL: default to CRITICAL. CRITICAL triggers pipeline halt and mandatory human review.
- Context-dependent classification: `rm -rf /tmp/build` vs `rm -rf /etc` -- the LLM-based classifier should distinguish these. If the LLM cannot determine context, default HIGH.
- Previously classified sub-tasks on replan: if only the inputs changed (not the tool or action), maintain previous risk level. Only re-classify if the sub-task's tool, action, or target changed.

### 6.6 INTERFACES

```python
RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

@dataclass
class RiskAssessmentResult:
    risk_levels: dict[str, RiskLevel]  # sub_task_id -> RiskLevel
    overall_risk: RiskLevel
    justifications: dict[str, str]  # sub_task_id -> justification
    fallback_used: bool  # True if regex fallback was activated

class RiskAssessmentNode:
    """LLM-based per-sub-task risk classification."""

    def __init__(
        self,
        llm_client: Any,
        regex_classifier: RegexClassifier,  # Fallback
        config: RiskAssessmentConfig,
    ):
        ...

    def assess_risk(self, state: PipelineState) -> PipelineState:
        """Classify each sub-task's risk level.

        On replan, only re-classifies sub-tasks whose definitions
        changed (FRAGO delta). Unchanged sub-tasks carry forward
        previous risk levels.

        Returns:
            PipelineState with risk_levels, overall_risk, and
            risk_justifications populated.
        """
        ...
```

### 6.7 INTERACTIONS

- **Triggered by:** RESEARCH (first pass) or REPLAN (replan cycles).
- **Triggers:** PREMORTEM unconditionally for STANDARD/DEEP paths.
- **On replan (FRAGO loop):** REPLAN -> RISK ASSESSMENT (re-classify only changed sub-tasks) -> EXECUTE (not PREMORTEM, not APPROVAL -- those are bypassed on replan unless the re-classification elevates to CRITICAL).
- **State transition:** Sets `state.risk_levels`, `state.overall_risk`, `state.risk_justifications`.
- **Safety invariant:** If ANY sub-task is CRITICAL, the pipeline MUST halt and require human approval regardless of path. CRITICAL overrides all other routing.

### 6.8 FAST PATH

Not applicable. RISK ASSESSMENT is bypassed in the FAST path.

### 6.9 INTEGRATION RISK

The hardest thing about RISK ASSESSMENT is **false-positive rate tuning.** An LLM-based classifier that is too conservative will generate excessive HIGH/CRITICAL classifications, overwhelming human reviewers and slowing the pipeline. One that is too aggressive will miss dangerous operations. The conservative bias erring on the side of safety is correct for a production system, but the false-positive rate must be measured and acceptable to human operators.

Second-hardest: **re-classification on replan.** Identifying "changed sub-tasks" requires a deterministic diff between old and new sub-task definitions. The diff algorithm must be robust: any change to `tools_required`, `description` (which describes the action), or `dependencies` triggers re-classification. Pure ID/positional changes do not trigger re-classification.

---

## 7. PREMORTEM (premortem.py)

### 7.1 FUNCTION & RATIONALE

Generates failure scenarios for the plan using multiple LLM calls from different persona perspectives (e.g., security engineer, domain expert, end user, adversarial tester). Each persona identifies potential failure modes, and results are consolidated with severity and specificity scoring. If fatal flaws are found (severity HIGH+ and likelihood > 50%), the pipeline routes back to PLAN for revision, then BACKBRIEF re-runs. Max 2 pre-mortem cycles.

### 7.2 FILE & LOCATION

- **Module:** `premortem.py` (new independent module, never part of nodes.py)
- **Class:** `PremortemNode`
- **Methods:** `def analyze(self, state: PipelineState) -> PipelineState`, `def _generate_persona_scenarios(...)`

### 7.3 INPUT

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `plan` | `Plan` | BACKBRIEF (via RESEARCH, RISK) | Full plan with Commander's Intent |
| `sub_tasks` | `list[SubTaskDef]` | PLAN | Sub-tasks to analyze for failure |
| `risk_levels` | `dict[str, RiskLevel]` | RISK ASSESSMENT | Per-sub-task risk levels |
| `overall_risk` | `RiskLevel` | RISK ASSESSMENT | Aggregate risk |
| `research_findings` | `ResearchFindings` | RESEARCH | Domain context for scenario generation |
| `knowledge_gaps` | `list[str]` | RESEARCH | Areas of uncertainty to probe |
| `premortem_cycle_count` | `int` | Graph state | Current cycle number (0 for first pass) |

### 7.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `failure_scenarios` | `list[FailureScenario]` | APPROVAL, PLAN | Structured failure scenarios with persona attribution |
| `fatal_flags` | `list[FailureScenario]` | Graph router | Scenarios that require plan revision |
| `premortem_cycle_count` | `int` | Graph state | Incremented if fatal flags found |
| `premortem_summary` | `str` | APPROVAL | Human-readable summary of findings |

### 7.5 EDGE CASES

**Empty input / missing fields:**
- `plan` missing: cannot run premortem. Raise `MissingPlanError`.
- `sub_tasks` empty: can still run premortem on the plan's Commander's Intent (goals may be flawed even without sub-tasks).
- `risk_levels` empty (all sub-tasks unclassified): classification failure upstream. PREMORTEM should still run but note the classification gap in findings.

**Malformed input:**
- `risk_levels` contain keys that don't match any sub-task: log warning, ignore orphan keys.
- `knowledge_gaps` empty: no special knowledge gaps to probe. Run standard personas only.

**LLM call failure / timeout:**
- One persona's LLM call fails: skip that persona, continue with others. At least 2 of 3 personas must complete for valid analysis.
- All persona calls fail: return empty failure_scenarios. Log critical alert. Pipeline continues (no blocking -- PREMORTEM is advisory, not mandatory).
- Partial response from a persona: include what was generated. Flag as incomplete.

**State corruption:**
- `state.failure_scenarios` already set from a previous PREMORTEM run: this is expected on re-entry after PLAN revision. Append new scenarios to existing ones. Clear and regenerate if this is a new cycle (increment counter).

**Infinite loops / runaway recursion:**
- PREMORTEM -> PLAN -> BACKBRIEF -> RESEARCH -> RISK -> PREMORTEM loop: hard ceiling at 2 cycles. After ceiling, PREMORTEM force-passes (returns no fatal flags). The ceiling is enforced in the graph topology via conditional edges that check `premortem_cycle_count >= 2`.

**Token budget exhaustion:**
- PREMORTEM makes multiple parallel LLM calls (3-5 personas). If token budget is low, reduce persona count to 2 (minimum viable).
- Persona prompts should be concise: persona description + plan summary + "what could go wrong?"

**Tool call failure:**
- PREMORTEM does not invoke tools. No tool call failure mode.

**Confidence/classification boundary cases:**
- False positives (scenarios that look fatal but aren't): acceptable -- routing back to PLAN for clarification costs a few seconds of LLM time and one extra pipeline cycle. Better than missing a real fatal flaw.
- False negatives (missing a real fatal flaw): mitigated by multiple diverse personas. If all personas miss the same flaw, it is genuinely novel.
- Severity-likelihood matrix: HIGH severity + >50% likelihood = fatal. Everything else = advisory.
- No fatal flaws found but many advisory flags: PREMORTEM passes but attaches advisory scenarios to `state.failure_scenarios` for APPROVAL to review.
- All scenarios fatal: the plan may be fundamentally unsound. After ceiling, force-pass and let APPROVAL and EXECUTE discover the issues.

### 7.6 INTERFACES

```python
@dataclass
class FailureScenario:
    persona: str  # Which persona generated this
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    likelihood: float  # 0.0 to 1.0
    affected_sub_tasks: list[str]
    mitigation_suggestion: Optional[str]

@dataclass
class PremortemResult:
    scenarios: list[FailureScenario]
    fatal_flags: list[FailureScenario]
    cycle_count: int
    forced_pass: bool  # True if ceiling reached
    personas_disabled: list[str]  # Personas that failed to respond

class PremortemNode:
    """Persona-based failure scenario generation."""

    def __init__(
        self,
        llm_client: Any,
        personas: list[PersonaDef],
        config: PremortemConfig,
    ):
        ...

    def analyze(self, state: PipelineState) -> PipelineState:
        """Generate failure scenarios from multiple persona perspectives.

        Returns:
            PipelineState with failure_scenarios, fatal_flags,
            premortem_cycle_count, and premortem_summary populated.
        """
        ...
```

### 7.7 INTERACTIONS

- **Triggered by:** RISK ASSESSMENT (first pass) or PLAN revision (re-entry after fatal flags).
- **Triggers:**
  - If `fatal_flags` is non-empty and `premortem_cycle_count < 2`: PLAN (revision with fatal_flags as additional context). After PLAN revision, BACKBRIEF re-runs.
  - If `fatal_flags` is empty (or `premortem_cycle_count >= 2`): BRANCHING FACTOR MONITOR (proceed).
- **Receives from:** PLAN (on re-entry), BACKBRIEF (the revised plan).
- **State transition:** Sets `state.failure_scenarios`, `state.fatal_flags`, `state.premortem_summary`. Increments `state.premortem_cycle_count` on re-entry.
- **Re-entry loop semantics:** PREMORTEM -> PLAN -> BACKBRIEF -> RESEARCH -> RISK -> PREMORTEM. This is the only multi-node loop in the STANDARD/DEEP pipeline (besides REPLAN). Ceiling: 2. Both PREMORTEM and BACKBRIEF must agree before proceeding -- PREMORTEM's fatal check and BACKBRIEF's consistency check are independent gates.

### 7.8 FAST PATH

Not applicable. PREMORTEM is bypassed in the FAST path.

For STANDARD path: 3 personas, single-COA, standard iteration ceiling (2).
For DEEP path: 5 personas, multi-COA, higher iteration ceiling (3).

### 7.9 INTEGRATION RISK

The hardest thing about PREMORTEM is **persona design.** The quality of failure scenarios is directly proportional to the quality and diversity of the personas. Generic personas generate generic scenarios. The personas must be domain-specific (domain from CLASSIFY tags) and have distinct perspectives. This is a design problem, not a coding problem, and may require iteration.

Second-hardest: **the PREMORTEM-BACKBRIEF interaction loop.** When PREMORTEM triggers a plan revision, the revised plan must pass BACKBRIEF again. But BACKBRIEF's verification may have already passed on the previous version -- it might pass again trivially or it might flag NEW issues introduced by the revision. The shared ceiling (2 cycles) covers both PLAN->BACKBRIEF revisions and PREMORTEM->PLAN revisions in the same counter. Must ensure the topology enforces this correctly.

---

## 8. BRANCHING FACTOR MONITOR (branching_monitor.py)

### 8.1 FUNCTION & RATIONALE

Runtime monitor that tracks the branching factor (b) during execution. Branching factor measures how many sub-tasks are spawned per parent task. If b >= 1 (each sub-task spawns >= 1 new sub-tasks, causing divergence), the monitor halts execution and flags the plan for replanning. This is a runtime detection mechanism, not a pre-execution estimator, avoiding the circularity problem of predicting decomposition before decomposition exists.

### 8.2 FILE & LOCATION

- **Module:** `branching_monitor.py` (new independent module) or may be embedded in `executor.py`
- **Class:** `BranchingFactorMonitor`
- **Method:** `def monitor(self, state: PipelineState) -> PipelineState`

### 8.3 INPUT

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `sub_tasks` | `list[SubTaskDef]` | PLAN | Sub-tasks to be executed |
| `plan` | `Plan` | PLAN | Full plan with DAG structure |
| `executor_config` | `ExecutorConfig` | Configuration | Max concurrency, branching thresholds |

### 8.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `branching_report` | `BranchingReport` | APPROVAL, EXECUTE | Branching analysis with recommendations |
| `concurrency_limit` | `int` | EXECUTE | Max concurrent sub-tasks (default 4, adjusted by branching analysis) |
| `halt_flag` | `bool` | Graph router | True if b >= 1 detected |
| `halt_reason` | `Optional[str]` | Graph router, REPLAN | Explanation of why halt was triggered |

### 8.5 EDGE CASES

**Empty input / missing fields:**
- `sub_tasks` empty: no branching to monitor. `halt_flag = False`, concurrency unchanged. Trivially safe.
- `plan` missing (should not happen in STANDARD/DEEP): cannot compute DAG depth. Default to sequential execution (concurrency = 1).

**Malformed input:**
- DAG with invalid parent references: compute branching factor only on known sub-tasks. Log warning.
- Circular DAG (should have been caught by BACKBRIEF): treat as divergent (b >= 1). Flag halt.

**Branching factor edge cases:**
- b = 0 (fan-out): flat decomposition, one level deep. Ideal.
- b < 1 (some sub-tasks spawn, but average less than 1 per parent): acceptable. Plan may have sub-tasks at different depths.
- b = 1 exactly: each sub-task spawns exactly one new sub-task, producing a chain. This is technically linear (depth = N), not divergent. Decision: flag as warning but do NOT halt. A chain of N is N times the work but not divergent.
- b > 1: exponential growth. Halt and flag.
- b spikes transiently due to a single over-decomposed sub-task: flag as warning. If the spike is isolated, recommend replanning only that branch.

**Concurrency limit enforcement:**
- Default max concurrency: 4 (from synthesis agreement).
- Max concurrency adjusted DOWN based on branching analysis: if the DAG has hidden couplings (from BACKBRIEF DSM), reduce concurrency.
- Max concurrency adjusted DOWN based on risk levels: if any HIGH/CRITICAL sub-tasks exist, reduce concurrency. HIGH risk sub-tasks run sequentially.
- Concurrency can be explicitly overridden by user or configuration.

**State corruption:**
- `halt_flag` already set: this is a re-entrant check. If halt was already triggered, the pipeline should not have reached BRANCHING MONITOR again. Log error and re-assert halt.

**Token budget exhaustion:**
- BRANCHING MONITOR is purely algorithmic (DAG traversal + arithmetic). No token consumption.

**Tool call failure:**
- No tool calls. No tool call failure mode.

### 8.6 INTERFACES

```python
@dataclass
class BranchingReport:
    branching_factor: float  # Avg children per parent node
    max_depth: int
    node_count: int
    has_divergent_branch: bool  # Any node with b > 1
    divergent_nodes: list[str]  # Node IDs with b > 1
    concurrency_recommendation: int

class BranchingFactorMonitor:
    """Runtime branching factor monitor. Prevents divergent execution."""

    def __init__(self, config: BranchingMonitorConfig):
        ...

    def monitor(self, state: PipelineState) -> PipelineState:
        """Analyze plan DAG for branching factor violations.

        Returns:
            PipelineState with branching_report, concurrency_limit,
            halt_flag, and halt_reason populated.
        """
        ...
```

### 8.7 INTERACTIONS

- **Triggered by:** PREMORTEM (when pre-mortem passes without fatal flags, or ceiling reached).
- **Triggers:**
  - If `halt_flag == False`: APPROVAL GATE (proceed to human review).
  - If `halt_flag == True`: REPLAN (flag for replanning). The plan has divergent branching and needs restructuring. REPLAN generates a delta that flattens the branching.
- **State transition:** Sets `state.branching_report`, `state.concurrency_limit`, `state.halt_flag`, `state.halt_reason`.
- **On replan re-entry:** BRANCHING MONITOR runs again on the revised plan. The branching factor should be improved (lower) after REPLAN's restructuring.

### 8.8 FAST PATH

Not applicable. BRANCHING FACTOR MONITOR is bypassed in the FAST path.

45% Rule integration: if `b` approaches 0.45 (warning threshold), the branching report includes a warning annotation: "Branching factor approaching divergence threshold (0.45). Consider simplifying the plan." This is advisory only -- the hard halt is at b >= 1.

### 8.9 INTEGRATION RISK

The hardest thing is **determining what counts as a "branch" in the DAG.** LangGraph's sub-task model may have different granularity than what branching factor analysis expects. The DAG might have intermediate nodes that are not execution sub-tasks (e.g., sub-task groups, conditionals). The monitor must only count execution nodes, not structural nodes.

Second-hardest: **the b >= 1 threshold calibration.** A chain of N sub-tasks (b = 1 exactly) is warned but not halted. But a chain of 50 sub-tasks is effectively divergent in terms of cost. The monitor may need a secondary depth-based check (max depth > 10) that triggers replanning even when b < 1.

---

## 9. APPROVAL GATE (guardrails.py)

### 9.1 FUNCTION & RATIONALE

Human-in-the-loop approval gate that presents a structured briefing to the user before execution begins. The briefing includes: Commander's Intent (goals, constraints, acceptance criteria), risk levels per sub-task, pre-mortem failure scenarios, branching analysis, and provenance information (which model generated what). Defense-in-depth: approval is required for HIGH-risk sub-tasks in ALL paths (parallel AND sequential). CRITICAL-risk sub-tasks force a pipeline halt. The approval decision is recorded in an audit trail.

### 9.2 FILE & LOCATION

- **Module:** `guardrails.py` (may also have routing logic in `graph.py`)
- **Class:** `ApprovalGate`
- **Method:** `def request_approval(self, state: PipelineState) -> PipelineState`

### 9.3 INPUT

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `plan` | `Plan` | PLAN | Commander's Intent and task breakdown |
| `risk_levels` | `dict[str, RiskLevel]` | RISK ASSESSMENT | Per-sub-task risk |
| `overall_risk` | `RiskLevel` | RISK ASSESSMENT | Aggregate risk |
| `failure_scenarios` | `list[FailureScenario]` | PREMORTEM | Potential failure modes |
| `branching_report` | `BranchingReport` | BRANCHING MONITOR | Branching analysis |
| `sub_tasks` | `list[SubTaskDef]` | PLAN | Full sub-task definitions for approval display |

### 9.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `approval_decision` | `ApprovalDecision` | Graph router | Approved, rejected, or modified |
| `approval_comment` | `Optional[str]` | EXECUTE, REPLAN | User's approval comment or modification request |
| `audit_trail` | `AuditEntry` | Persistent storage | Full provenance record of the approval decision |

### 9.5 EDGE CASES

**Empty input / missing fields:**
- No HIGH or CRITICAL risk sub-tasks: approval may be skipped entirely (automatically approved) for STANDARD path LOW/MEDIUM-only plans. This is configurable. For DEEP path, all plans require approval regardless of risk.
- `plan` missing: cannot present a meaningful briefing. Log error, reject pipeline.

**Malformed input:**
- `risk_levels` contain invalid enum values: treat as MEDIUM. Log error.
- `failure_scenarios` truncated or malformed: present what is available. Briefing robustness.

**LLM call failure / timeout:**
- APPROVAL GATE does not make LLM calls. It is a structured data presentation + human input collection point. No LLM failure mode.

**State corruption:**
- `approval_decision` already set: this means APPROVAL was re-entered, which should only happen on replan when new HIGH-risk sub-tasks are introduced. In that case, only request approval for the NEW sub-tasks (FRAGO delta).

**Infinite loops / runaway recursion:**
- Human approval is blocking. The pipeline waits for human input. No loop risk, but risk of indefinite wait. Must have configurable timeout (default 5 minutes for STANDARD, 10 minutes for DEEP). On timeout, default to REJECT (safe fail).

**Token budget exhaustion:**
- No token consumption. The briefing is a rendered view, not an LLM call.

**Tool call failure:**
- APPROVAL GATE does not invoke tools. It presents information to the user and collects a response. No tool call failure mode.

**Human interaction edge cases:**
- User rejects the plan: route to REPLAN with rejection reason. REPLAN generates a FRAGO delta addressing the user's concern. Re-route through APPROVAL. Max 3 approval cycles.
- User modifies the plan (adds constraints, removes sub-tasks): apply modifications to plan state, route to BACKBRIEF (re-verify modified plan).
- User provides no response (timeout): auto-reject. Notify user.
- User provides ambiguous response: treat as rejection. Ask for clarification in next cycle.
- User approves with conditions: apply conditions, proceed with conditions attached.

### 9.6 INTERFACES

```python
@dataclass
class ApprovalDecision:
    decision: Literal["approved", "rejected", "modified", "timed_out"]
    timestamp: datetime
    user_id: str
    comment: Optional[str]
    modifications: Optional[dict]  # User-specified plan modifications
    requires_re_approval: bool  # True if modifications need re-approval

@dataclass
class AuditEntry:
    pipeline_id: str
    classification_result: ClassificationResult
    plan: Plan
    risk_levels: dict[str, RiskLevel]
    failure_scenarios: list[FailureScenario]
    branching_report: BranchingReport
    approval_decision: ApprovalDecision
    execution_results: Optional[list]  # Populated post-execution

class ApprovalGate:
    """Human-in-the-loop approval with structured briefing."""

    def __init__(
        self,
        config: ApprovalGateConfig,
        audit_store: AuditStore,
    ):
        ...

    def request_approval(self, state: PipelineState) -> PipelineState:
        """Present structured briefing and collect human approval.

        Blocks until human responds or timeout reached.

        Returns:
            PipelineState with approval_decision, audit_trail populated.
        """
        ...

    def _format_briefing(self, state: PipelineState) -> str:
        """Format structured briefing for human display."""
        ...

    def _record_audit(self, state: PipelineState) -> None:
        """Record full provenance in audit store."""
        ...
```

### 9.7 INTERACTIONS

- **Triggered by:** BRANCHING FACTOR MONITOR (when `halt_flag == False`).
- **Triggers:**
  - `approved` -> EXECUTE.
  - `rejected` or `timed_out` -> OUTPUT (inform user, no execution).
  - `modified` -> BACKBRIEF (re-verify modified plan, then re-enter approval).
  - On replan: APPROVAL is ONLY re-entered if new HIGH/CRITICAL risk sub-tasks are introduced by the FRAGO delta. LOW/MEDIUM-only deltas skip approval.
- **State transition:** Sets `state.approval_decision`, `state.audit_trail`.
- **Safety invariant:** CRITICAL-risk sub-tasks ALWAYS require human approval, even on replan. The graph topology must enforce this.

### 9.8 FAST PATH

Not applicable. APPROVAL GATE is bypassed in the FAST path.

In STANDARD path: approval required if any HIGH risk sub-tasks exist. DEEP path: approval always required.

### 9.9 INTEGRATION RISK

The hardest thing about APPROVAL GATE is **the human interaction integration.** LangGraph supports human-in-the-loop interrupts natively, but the interrupt mechanism must be wired to a UI or CLI that presents the structured briefing and collects the response. The actual interrupt API (`graph.interrupt()`) is straightforward, but the surrounding UX (how the briefing looks, how the user responds, what happens on timeout) requires a human interface layer that may not exist yet.

Second-hardest: **the modification workflow.** If the user modifies the plan, the system must apply modifications to the plan state and re-route through BACKBRIEF (to verify the modified plan is still consistent). This creates a new loop (APPROVAL -> BACKBRIEF -> RISK -> PREMORTEM -> BRANCHING -> APPROVAL) that must be bounded. Max 3 approval cycles.

---

## 10. EXECUTE (executor.py)

### 10.1 FUNCTION & RATIONALE

Executes the approved plan's sub-tasks with isolated state per sub-task (fixing H9, H11, H12). Parallel execution is the DEFAULT mode for STANDARD path. Each sub-task gets its own isolated state dict with immutable state updates -- no shared mutable state between concurrent sub-tasks. Retry logic is extracted into a shared `_execute_with_retry` helper used by both sequential and parallel paths. Compensation handler ladder: retry -> catch/fallback -> local compensation -> radius expansion -> escalate to REPLAN.

### 10.2 FILE & LOCATION

- **Module:** `executor.py` (split from nodes.py monolith in Wave 2, contains both `ExecuteNode` and `FastExecuteNode`)
- **Class:** `ExecuteNode`
- **Methods:** `def execute(self, state: PipelineState) -> PipelineState`, `def _execute_sub_task(sub_task, isolated_state, ...)`, `_execute_with_retry(...)`, compensation handlers

### 10.3 INPUT

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `plan` | `Plan` | PLAN (via APPROVAL) | Approved plan |
| `sub_tasks` | `list[SubTaskDef]` | PLAN | Sub-tasks to execute in dependency order |
| `risk_levels` | `dict[str, RiskLevel]` | RISK ASSESSMENT | Per-sub-task risk for execution controls |
| `concurrency_limit` | `int` | BRANCHING MONITOR | Max concurrent sub-tasks |
| `approval_decision` | `ApprovalDecision` | APPROVAL | Approval record (audit) |
| `tool_recommendations` | `list[str]` | RESEARCH | Tool suggestions |
| `skill_library` | `SkillLibrary` | Cross-cutting | For failure recording post-execution |

### 10.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `sub_task_results` | `list[SubTaskResult]` | SYNTHESIZE | Results from each sub-task, including success/failure and output |
| `execution_errors` | `list[ExecutionError]` | EVALUATE, REPLAN | Structured errors classified by type |
| `compensation_level` | `int` | REPLAN | Highest compensation handler level triggered |

### 10.5 EDGE CASES

**Empty input / missing fields:**
- `sub_tasks` empty: nothing to execute. Return empty results list. Pipeline proceeds to SYNTHESIZE with no results.
- `plan` missing: raise `MissingPlanError`. EXECUTE cannot run without a plan.

**Malformed input:**
- `sub_tasks` with missing `id` or `description`: skip that sub-task, log error, record as execution error.
- `risk_levels` with values for non-existent sub-tasks: ignore orphan keys.
- `concurrency_limit` <= 0: clamp to 1 (sequential).

**LLM call failure / timeout:**
- Per-sub-task LLM call failure: trigger compensation handler ladder. Start with retry.
- Retry exhaustion: escalate to catch/fallback.
- If all handlers exhausted for a sub-task: mark sub-task as FAILED, record error type, proceed to next sub-task. Do NOT halt the entire pipeline for a single sub-task failure.

**State corruption (isolated-state design):**
- Each sub-task has its own `SubTaskState` dict. No shared mutable state between sub-tasks.
- Immutable state updates: sub-tasks read from state but write only to their own result dict. The main pipeline state is only updated after all sub-tasks complete or fail.
- Concurrent access: LangGraph's parallel execution model may share the checkpointer. Ensure each sub-task's state is independently checkpointed.

**Infinite loops / runaway recursion:**
- Compensation handler ladder has a hard stop: if local compensation fails, escalate to REPLAN. REPLAN is not part of EXECUTE -- it is a separate loop in the graph. EXECUTE itself has no recursion.
- A sub-task that generates infinite output: enforce max output token limit (configurable per risk level). Truncate on exceed.

**Token budget exhaustion:**
- Each sub-task gets a portion of the remaining token budget. If a sub-task exhausts its budget, it is marked as FAILED (budget_exceeded).
- Budget allocation: equal share across sub-tasks, with HIGH risk sub-tasks getting 1.5x allocation.
- If total budget is < threshold (configurable), refuse to execute and request more budget.

**Tool call failure:**
- Tool unavailable: trigger compensation handler. Catch/fallback: use alternative tool if known. Local compensation: try different approach. Radius expansion: check if dependent sub-tasks can still proceed without this tool.
- Tool returns unexpected output: attempt to parse. If parsing fails, flag as execution error and escalate.
- Tool timeout: retry once with shorter timeout. If still timing out, mark as FAILED (timeout).
- Tool deprecation mid-execution: if a tool is deprecated (returns deprecation warning), record and continue. Flag for skill library update post-execution.

**Parallel execution edge cases:**
- Dependency violation: a sub-task starts before its dependency completes. This should be prevented by the executor's DAG scheduler. If it occurs, hard error.
- Deadlock: sub-tasks A depends on B, B depends on A. Backbrief should have caught this. If it reaches EXECUTE, the DAG scheduler detects the cycle and halts.
- Race condition in isolated state: despite isolated state, sub-tasks could race on external resources (files, APIs). This is an application-level race, not a state corruption race. The isolated-state design prevents state corruption but cannot prevent external resource races. Document this limitation.

### 10.6 INTERFACES

```python
@dataclass
class SubTaskResult:
    sub_task_id: str
    status: Literal["success", "failed", "skipped", "budget_exceeded"]
    output: Any
    error: Optional[ExecutionError]
    token_used: int
    latency_ms: int
    compensation_handler_used: Optional[str]

@dataclass
class ExecutionError:
    sub_task_id: str
    error_type: Literal[
        "llm_failure", "tool_failure", "timeout",
        "budget_exceeded", "dependency_violation",
        "invalid_output", "unknown"
    ]
    message: str
    handler_level: int  # 0=no handler, 1=retry, 2=catch, 3=local, 4=radius

class ExecuteNode:
    """Isolated-state parallel executor with compensation handlers."""

    def __init__(
        self,
        llm_client: Any,
        tool_registry: ToolRegistry,
        skill_library: SkillLibrary,
        config: ExecutorConfig,
    ):
        ...

    def execute(self, state: PipelineState) -> PipelineState:
        """Execute sub-tasks in dependency order with parallelism.

        Parallel mode is DEFAULT for STANDARD path.
        Sequential mode for DEEP path.

        Returns:
            PipelineState with sub_task_results, execution_errors,
            and compensation_level populated.
        """
        ...

    def _execute_sub_task(
        self,
        sub_task: SubTaskDef,
        isolated_state: dict,
        context: ExecutionContext,
    ) -> SubTaskResult:
        """Execute a single sub-task with isolated state."""
        ...

    def _execute_with_retry(
        self,
        sub_task: SubTaskDef,
        isolated_state: dict,
        context: ExecutionContext,
        max_retries: int,
    ) -> SubTaskResult:
        """Execute with retry logic. Shared between sequential and parallel."""
        ...
```

### 10.7 INTERACTIONS

- **Triggered by:** APPROVAL GATE (when `approval_decision == "approved"`).
- **Triggers:** SYNTHESIZE unconditionally after all sub-tasks complete.
- **Compensation escalation:** If compensation level reaches 3 (local compensation) or higher, the failure information is passed to EVALUATE and ultimately to REPLAN for the FRAGO loop.
- **Re-entry after REPLAN:** EXECUTE receives a FRAGO delta -- only the changed sub-tasks (plus their transitive dependents) are re-executed. Unchanged sub-tasks carry forward their previous results.
- **State transition:** Sets `state.sub_task_results`, `state.execution_errors`, `state.compensation_level`.

### 10.8 FAST PATH

Not applicable. The STANDARD EXECUTE path is replaced by FAST EXECUTE in the FAST path.

For STANDARD: parallel default, DAG-scheduled execution, concurrency limited by branching monitor.
For DEEP: sequential default (parallel only with explicit opt-in), single-threaded execution.

### 10.9 INTEGRATION RISK

The hardest thing about EXECUTE is **the isolated-state model within LangGraph.** LangGraph's default state model is shared across graph nodes -- a single `State` dict that all nodes read and write. The isolated-state design requires EITHER (a) a separate sub-state for each sub-task that LangGraph can checkpoint independently, OR (b) a workaround where sub-tasks have private state that is merged back after execution. LangGraph supports `Subgraph` for this purpose, but using subgraphs adds complexity.

Second-hardest: **compensation handler ladder implementation.** The ladder has 5 levels (retry -> catch -> local -> radius -> escalate), each with different logic. Ensuring the ladder is deterministic (not infinite, not skipping levels) requires careful state management. The most dangerous failure mode is a compensation handler that triggers another compensation handler, creating a cascade.

---

## 11. SYNTHESIZE (synthesizer.py)

### 11.1 FUNCTION & RATIONALE

Assembles sub-task results into a coherent final output. For FAST path, this is a pass-through (the fast_response is already complete). For STANDARD/DEEP, it merges results from all completed sub-tasks, resolves conflicts between results, and performs a cross-agent quality review (checking for internal consistency, completeness against acceptance criteria, and adherence to constraints).

### 11.2 FILE & LOCATION

- **Module:** `synthesizer.py` (split from nodes.py monolith in Wave 2, contains both `SynthesizeNode` and `ResearchNode`)
- **Class:** `SynthesizeNode`
- **Method:** `def synthesize(self, state: PipelineState) -> PipelineState`

### 11.3 INPUT

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `sub_task_results` | `list[SubTaskResult]` | EXECUTE | Results from all executed sub-tasks |
| `fast_response` | `Optional[str]` | FAST EXECUTE | Direct response (FAST path only) |
| `plan` | `Plan` | PLAN | Commander's Intent for quality checking |
| `commander_intent` | `CommanderIntent` | PLAN | Goals, constraints, acceptance criteria |
| `pipeline_path` | `Literal["FAST", "STANDARD", "DEEP"]` | CLASSIFY | Current path |
| `execution_errors` | `list[ExecutionError]` | EXECUTE | Any errors encountered during execution |

### 11.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `synthesized_output` | `str` | EVALUATE, OUTPUT | Final assembled output |
| `quality_report` | `QualityReport` | EVALUATE, Audit | Quality assessment of the assembled output |
| `synthesis_conflicts` | `list[Conflict]` | EVALUATE | Any conflicts between sub-task results that weren't resolved |

### 11.5 EDGE CASES

**Empty input / missing fields:**
- `sub_task_results` empty (no sub-tasks executed): produce empty output. EVALUATE will mark as FAILURE for STANDARD/DEEP paths. For FAST path, `fast_response` should be set.
- `fast_response` set and `sub_task_results` present: FAST path should not have both. Log warning, prefer `fast_response`.

**Malformed input:**
- `sub_task_results` missing expected fields: skip malformed results, synthesize from available ones. Note quality gap in quality report.
- `commander_intent` missing fields: use defaults (empty strings, empty lists). Quality check will flag missing criteria.

**LLM call failure / timeout (cross-agent quality review):**
- Quality review LLM call fails: skip quality review. Return synthesized output without quality assessment. Log warning.
- Quality review times out: return partial quality review. Do not block pipeline.

**State corruption:**
- `synthesized_output` already set (re-entry from replan): overwrite with new synthesis. The FRAGO loop generates new results that need new synthesis.

**Infinite loops / runaway recursion:**
- Single LLM call (for quality review) plus algorithmic assembly. No recursion.

**Token budget exhaustion:**
- Synthesis could be token-intensive (assembling multiple sub-task outputs). If budget is low, produce a shorter synthesis (summarize instead of full assembly).
- Quality review: skip if budget < 10% remaining.

**Tool call failure:**
- SYNTHESIZE does not invoke tools. No tool call failure mode.

**Conflict resolution:**
- Contradictory results from different sub-tasks: flag as conflict, include both perspectives in synthesized output with conflict noted.
- One sub-task contradicts the Commander's Intent: prioritize Commander's Intent. Flag sub-task as quality failure.
- Multiple sub-tasks produce the same result: deduplicate.

### 11.6 INTERFACES

```python
@dataclass
class QualityReport:
    is_consistent: bool
    completeness_score: float  # 0.0 to 1.0
    constraint_adherence: dict[str, bool]
    conflicts_found: int
    quality_review_performed: bool

@dataclass
class Conflict:
    sub_tasks: list[str]  # Sub-tasks with conflicting results
    description: str
    resolution: Optional[str]  # How the conflict was resolved

class SynthesizeNode:
    """Assemble sub-task results into coherent output with quality review."""

    def __init__(
        self,
        llm_client: Optional[Any],  # For quality review; None = algorithmic only
        config: SynthesizeConfig,
    ):
        ...

    def synthesize(self, state: PipelineState) -> PipelineState:
        """Assemble results and perform quality review.

        Returns:
            PipelineState with synthesized_output, quality_report,
            and synthesis_conflicts populated.
        """
        ...

    def _merge_results(
        self,
        results: list[SubTaskResult],
        plan: Plan,
    ) -> tuple[str, list[Conflict]]:
        """Merge sub-task results into coherent output.

        Algorithmic merge, no LLM call.
        """
        ...

    def _quality_review(
        self,
        output: str,
        plan: Plan,
        conflicts: list[Conflict],
    ) -> QualityReport:
        """Cross-agent quality review of synthesized output.

        Optional LLM call. May be skipped if llm_client is None.
        """
        ...
```

### 11.7 INTERACTIONS

- **Triggered by:** FAST EXECUTE (FAST path) or EXECUTE (STANDARD/DEEP path).
- **Triggers:** EVALUATE unconditionally.
- **On replan:** SYNTHESIZE runs again after FRAGO loop, merging old (unchanged) results with new (re-executed) results.
- **State transition:** Sets `state.synthesized_output`, `state.quality_report`, `state.synthesis_conflicts`.

### 11.8 FAST PATH

In FAST path, SYNTHESIZE is a pass-through:
- `synthesized_output = fast_response`
- `quality_report = QualityReport(is_consistent=True, completeness_score=1.0, ...)`
- No LLM call, no quality review.

In STANDARD/DEEP path:
- Algorithmic merge of sub-task results (no LLM)
- Optional LLM-based quality review

### 11.9 INTEGRATION RISK

The hardest thing about SYNTHESIZE is **the merge algorithm.** Merging results from multiple sub-tasks that may have overlapping outputs, contradictory conclusions, or different formats is inherently complex. The merge must be deterministic and not lose information. For text outputs, this may be simple concatenation with sections. For structured outputs (JSON, code blocks), the merge must understand the structure.

Second-hardest: **quality review calibration.** The LLM-based quality review must be calibrated to accept outputs that meet acceptance criteria while rejecting outputs that don't. If too strict, good outputs are flagged and trigger unnecessary replanning. If too lenient, poor outputs reach the user.

---

## 12. EVALUATE (evaluate.py)

### 12.1 FUNCTION & RATIONALE

Assesses the synthesized output against the Commander's Intent's acceptance criteria. Produces a structured evaluation: SUCCESS (all criteria met), PARTIAL (some criteria met, some not), or FAILURE (no criteria met, or execution errors prevented completion). This evaluation determines whether the pipeline proceeds to output (SUCCESS) or enters the FRAGO replan loop (PARTIAL/FAILURE). The evaluation also identifies which acceptance criteria are met and which are not, providing specific feedback for the REPLAN node.

### 12.2 FILE & LOCATION

- **Module:** `evaluate.py` (new independent module, never part of nodes.py)
- **Class:** `EvaluateNode`
- **Method:** `def evaluate(self, state: PipelineState) -> PipelineState`

### 12.3 INPUT

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `synthesized_output` | `str` | SYNTHESIZE | The assembled output to evaluate |
| `quality_report` | `QualityReport` | SYNTHESIZE | Quality assessment |
| `commander_intent` | `CommanderIntent` | PLAN | Acceptance criteria to evaluate against |
| `execution_errors` | `list[ExecutionError]` | EXECUTE | Errors encountered during execution |
| `sub_task_results` | `list[SubTaskResult]` | EXECUTE | Per-sub-task status for detailed evaluation |
| `replan_count` | `int` | Graph state | Current replan count (0 for first attempt) |

### 12.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `evaluation_result` | `Literal["SUCCESS", "PARTIAL", "FAILURE"]` | Graph router | Go/no-go for output vs. replan |
| `criteria_results` | `dict[str, bool]` | REPLAN, OUTPUT | Per-criteria pass/fail |
| `evaluation_detail` | `str` | REPLAN, Audit | Detailed evaluation explanation |

### 12.5 EDGE CASES

**Empty input / missing fields:**
- `synthesized_output` empty: evaluate as FAILURE (no output produced). Log warning.
- `commander_intent` missing acceptance_criteria: evaluate based on quality_report only. If quality_report is missing too, default SUCCESS (nothing to measure against).
- `sub_task_results` empty: evaluate as FAILURE if STANDARD/DEEP path. Nothing executed.

**Malformed input:**
- `execution_errors` missing expected fields: skip malformed errors. Continue evaluation with available data.
- `criteria_results` keys don't match acceptance criteria: log warning, match by position.

**LLM call failure / timeout:**
- Evaluation LLM call fails: fall back to algorithmic evaluation (check if ALL sub_tasks succeeded, check if output is non-empty). Algorithmic evaluation is less nuanced but deterministic.
- Evaluation times out: use algorithmic fallback.

**State corruption:**
- `evaluation_result` already set: this is a replan re-entry. The previous evaluation should be preserved for comparison. Log both.

**Infinite loops / runaway recursion:**
- EVALUATE is called once per execution cycle (including replan cycles). The FRAGO loop's ceiling (max 3 replans) bounds the number of EVALUATE calls.

**Token budget exhaustion:**
- LLM-based evaluation skipped if budget < 5% remaining. Use algorithmic evaluation instead.

**Tool call failure:**
- EVALUATE does not invoke tools. No tool call failure mode.

**Confidence/classification boundary cases:**
- Edge between SUCCESS and PARTIAL: if all acceptance criteria are met but quality_report has warnings, evaluate as SUCCESS with advisories. Quality issues are not failures.
- Edge between PARTIAL and FAILURE: if any single criteria is met, it is PARTIAL (not FAILURE). FAILURE means zero criteria met OR all sub-tasks failed.
- No acceptance criteria defined: default SUCCESS (nothing to fail against).
- Execution errors present but output meets criteria: evaluate SUCCESS with error annotations. The errors are logged but don't affect the criteria-based evaluation.

### 12.6 INTERFACES

```python
EvaluationResult = Literal["SUCCESS", "PARTIAL", "FAILURE"]

@dataclass
class Evaluation:
    result: EvaluationResult
    criteria_results: dict[str, bool]
    detail: str
    evaluation_method: Literal["llm", "algorithmic", "hybrid"]

class EvaluateNode:
    """Evaluate synthesized output against acceptance criteria."""

    def __init__(
        self,
        llm_client: Optional[Any],  # For nuanced evaluation
        config: EvaluateConfig,
    ):
        ...

    def evaluate(self, state: PipelineState) -> PipelineState:
        """Evaluate output against Commander's Intent acceptance criteria.

        Returns:
            PipelineState with evaluation_result, criteria_results,
            and evaluation_detail populated.
        """
        ...

    def _evaluate_algorithmic(
        self,
        output: str,
        criteria: list[str],
        sub_task_results: list[SubTaskResult],
    ) -> Evaluation:
        """Deterministic evaluation without LLM call."""
        ...
```

### 12.7 INTERACTIONS

- **Triggered by:** SYNTHESIZE unconditionally.
- **Triggers:**
  - `SUCCESS` -> OUTPUT (return to user) + Skill Library archive.
  - `PARTIAL` or `FAILURE` -> REPLAN (if `replan_count < max_replans`), or force OUTPUT (if ceiling reached).
- **Archives to:** Skill Library (on SUCCESS -- store task signature, plan, and outcome as a success record for future template seeding).
- **State transition:** Sets `state.evaluation_result`, `state.criteria_results`, `state.evaluation_detail`.

### 12.8 FAST PATH

In FAST path, EVALUATION is always SUCCESS (FAST EXECUTE produced a direct response). No need for criteria-based evaluation. The `evaluation_method` is "algorithmic" (static).

### 12.9 INTEGRATION RISK

The hardest thing about EVALUATE is **acceptance criteria interpretation.** The criteria are expressed in natural language in the Commander's Intent. Determining whether a criterion is met requires semantic understanding that LLMs can provide but algorithmic checks cannot. The dual evaluation path (LLM for nuance, algorithmic for determinism) is the right approach, but knowing when to use which requires flagging criteria as "mechanically verifiable" vs "semantically evaluable."

Second-hardest: **the SUCCESS/PARTIAL/FAILURE threshold.** If the threshold is too strict, everything goes to replan (wasting time and tokens). If too lenient, bad outputs reach the user. The threshold must be configurable per domain (code tasks need stricter evaluation than creative tasks).

---

## 13. REPLAN (replanner.py)

### 13.1 FUNCTION & RATIONALE

Generates a FRAGO delta -- a minimal replan that only modifies the sub-tasks that failed (plus their transitive dependents). This is fundamentally different from global replanning: instead of generating a new plan from scratch, REPLAN analyzes the evaluation results, identifies what went wrong, and produces targeted fixes. The compensation handler ladder determines escalation: reprompts for simple LLM failures, catch blocks for tool errors, local compensation for logic errors, radius expansion for errors with downstream effects, and global replan only as the final escalation before human intervention.

### 13.2 FILE & LOCATION

- **Module:** `replanner.py` (split from nodes.py monolith in Wave 2)
- **Class:** `ReplanNode`
- **Method:** `def replan(self, state: PipelineState) -> PipelineState`

### 13.3 INPUT

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `evaluation_result` | `EvaluationResult` | EVALUATE | SUCCESS/PARTIAL/FAILURE |
| `criteria_results` | `dict[str, bool]` | EVALUATE | Per-criteria pass/fail |
| `evaluation_detail` | `str` | EVALUATE | Detailed failure analysis |
| `plan` | `Plan` | PLAN | Original plan for context |
| `sub_task_results` | `list[SubTaskResult]` | EXECUTE | Execution results for analysis |
| `execution_errors` | `list[ExecutionError]` | EXECUTE | Structured error information |
| `compensation_level` | `int` | EXECUTE | Highest compensation level already attempted |
| `replan_count` | `int` | Graph state | Number of replans already attempted (0-indexed) |

### 13.4 OUTPUT

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `delta_plan` | `Plan` | RISK ASSESSMENT | Updated plan with only changed sub-tasks |
| `replan_scope` | `list[str]` | RISK ASSESSMENT | IDs of sub-tasks changed in this delta |
| `replan_strategy` | `str` | Audit | What strategy was used (reprompt/catch/local/radius/global) |
| `compensation_level_escalated` | `int` | Audit | Escalated level if previous handlers failed |

### 13.5 EDGE CASES

**Empty input / missing fields:**
- `evaluation_result` missing: default to FAILURE. Safer to replan than to output unknown quality.
- `execution_errors` empty but evaluation is PARTIAL/FAILURE: the failure is in the OUTPUT quality, not in execution. REPLAN must re-analyze the failed criteria and regenerate corresponding sub-tasks.
- `sub_task_results` empty: replan is a full regeneration (this is effectively global replan). Flag as escalation.

**Malformed input:**
- `criteria_results` don't match sub_task_results: use evaluation_detail text as the primary failure signal. Criteria mapping is secondary.
- `compensation_level` has invalid value: assume level 0 (no compensation attempted). This may re-attempt strategies that already failed (acceptable -- previous attempt may have been flaky).

**LLM call failure / timeout:**
- Primary replan LLM call fails: retry once. If retry fails, escalate compensation level (skip directly to next level).
- All LLM-based strategies exhausted: global replan as final escalation. If global replan also fails, force-pass (output what we have) or fail pipeline.

**State corruption:**
- `delta_plan` already set from a previous replan (should not happen, but could on re-entry): overwrite. The previous delta is abandoned.
- `plan` has been modified by user (via APPROVAL modifications): REPLAN must work with the modified plan, not the original.

**Infinite loops / runaway recursion:**
- FRAGO loop ceiling: max 3 replans (configurable). After ceiling, force synthesize and output.
- Ceiling is checked in the graph topology BEFORE REPLAN executes. If `replan_count >= max_replans`, skip REPLAN and go directly to force-synthesize.
- Within REPLAN, no recursive calls. Single LLM call generates the delta.

**Token budget exhaustion:**
- REPLAN generates a delta, which is typically smaller than the original plan (only changed sub-tasks). Delta generation should be token-efficient.
- If budget is very low (< 10% remaining), force synthesize instead of replanning. The output will be lower quality but the pipeline completes.

**Tool call failure:**
- REPLAN does not invoke tools. No tool call failure mode.

**Compensation handler ladder edge cases:**
- Level 0 (no compensation): used when no previous compensation was attempted. E.g., first-time LLM failure.
- Level 1 (reprompt): same sub-task, same instruction, retry execution. Used for transient LLM failures.
- Level 2 (catch/fallback): modified sub-task with fallback approach. Used when a specific tool failed and an alternative is known.
- Level 3 (local compensation): modify the sub-task's approach while keeping its output type/interface unchanged. Used when the approach was wrong but the goal is correct.
- Level 4 (radius expansion): expand the affected region by one DAG hop (include direct dependents). Used when a failed sub-task's output was consumed by others.
- Level 5 (global replan): regenerate the entire plan. Final automated escalation before human intervention.
- Level 6 (human escalation): halt and request human guidance. Used when all automated strategies have been exhausted and the system cannot determine the correct path.
- Each escalation level is recorded in the audit trail. The FRAGO replan ceiling (max 3) applies to the number of REPLAN NODE INVOCATIONS, not to compensation ladder steps within a single invocation.

**Confidence/classification boundary cases:**
- False positive failure (evaluation flagged PARTIAL but the output is actually acceptable): REPLAN will attempt to "fix" something that isn't broken, potentially degrading quality. Mitigation: if the evaluation detail is vague, use a lighter-touch replan (reprompt level, not local compensation).
- False negative (evaluation flagged SUCCESS but output is flawed): this is a quality gap in EVALUATE. No mitigation within REPLAN -- the flaw reaches the user.

### 13.6 INTERFACES

```python
CompensationLevel = Literal[
    "none", "reprompt", "catch_fallback",
    "local_compensation", "radius_expansion",
    "global_replan", "human_escalation"
]

@dataclass
class ReplanResult:
    delta_plan: Plan
    changed_sub_task_ids: list[str]
    strategy: CompensationLevel
    escalated_from: Optional[CompensationLevel]
    explanation: str

class ReplanNode:
    """FRAGO delta replanning with compensation handler ladder."""

    def __init__(
        self,
        llm_client: Any,
        config: ReplanConfig,
    ):
        ...

    def replan(self, state: PipelineState) -> PipelineState:
        """Generate FRAGO delta plan from evaluation results.

        Determines the appropriate compensation level based on
        previous compensation_level and error types.

        Returns:
            PipelineState with delta_plan, replan_scope,
            replan_strategy, and compensation_level_escalated populated.
        """
        ...

    def _determine_compensation_level(
        self,
        errors: list[ExecutionError],
        previous_level: int,
    ) -> CompensationLevel:
        """Determine the appropriate compensation level.

        Escalates based on: error type, previous level,
        number of previous replans, and the nature of the failure.
        """
        ...

    def _generate_delta(
        self,
        plan: Plan,
        failed_sub_tasks: list[str],
        evaluation_detail: str,
        level: CompensationLevel,
    ) -> tuple[Plan, list[str]]:
        """Generate minimal delta plan affecting only failed + dependent sub-tasks."""
        ...
```

### 13.7 INTERACTIONS

- **Triggered by:** EVALUATE when `evaluation_result in ("PARTIAL", "FAILURE")` and `replan_count < max_replans`.
- **Triggers:** RISK ASSESSMENT (re-classify only changed sub-tasks). Then EXECUTE (execute only changed + dependent sub-tasks). Then SYNTHESIZE (re-merge with unchanged results). Then EVALUATE (re-evaluate).
- **FRAGO loop:** EVALUATE -> REPLAN -> RISK ASSESSMENT -> EXECUTE -> SYNTHESIZE -> EVALUATE. This is the replan loop. Max 3 iterations.
- **Does NOT trigger:** PLAN (original plan generation), BACKBRIEF, RESEARCH, PREMORTEM, BRANCHING MONITOR, APPROVAL. These are bypassed on replan. EXCEPTION: if RISK ASSESSMENT re-classifies any changed sub-task as CRITICAL, APPROVAL is re-entered.
- **Archives to:** Skill Library (on SUCCESS after replan -- store failure pattern + successful fix as a learning record).
- **State transition:** Sets `state.delta_plan`, `state.replan_scope`, `state.replan_strategy`. Increments `state.replan_count`.

### 13.8 FAST PATH

Not applicable. REPLAN is bypassed in the FAST path.

### 13.9 INTEGRATION RISK

The hardest thing about REPLAN is **compensation level determination.** Deciding whether a failure warrants a simple reprompt or a full global replan requires understanding the failure's root cause, its severity, and its reach (which sub-tasks are affected). The compensation ladder is conceptually simple but implementation complexity is high: each level requires different delta generation logic, and the escalation rules must be deterministic.

Second-hardest: **the FRAGO loop re-entry contract.** When REPLAN produces a delta, the graph must correctly route through RISK ASSESSMENT (re-classify changed only), EXECUTE (re-execute changed + transitive dependents), SYNTHESIZE (re-merge), and EVALUATE (re-evaluate). The routing must be precise -- unchanged sub-tasks' results must be preserved and not discarded. Any bug in the re-entry routing loses work and wastes tokens.

---

## 14. SKILL LIBRARY (skill_library.py)

### 14.1 FUNCTION & RATIONALE

Cross-cutting knowledge store that persists learning across pipeline invocations. SQLite-backed for MVP (migration path to more robust storage in Wave 3). Serves four functions: (1) template seeding for PLAN -- when a new task matches a previously successful task signature, seed the plan with the stored template; (2) failure avoidance for EXECUTE -- when a sub-task repeats a prior failure pattern, warn and suggest alternatives; (3) research caching for RESEARCH -- cache research results by domain with TTL-based expiry; (4) allowlist accumulation for RISK ASSESSMENT -- tools and patterns that have been previously reviewed and approved can skip re-classification.

### 14.2 FILE & LOCATION

- **Module:** `skill_library.py` (new independent module, cross-cutting)
- **Class:** `SkillLibrary`
- **Schema:** SQLite with tables: `problem_patterns`, `plan_templates`, `research_cache`, `tool_allowlist`, `failure_patterns`, `execution_stats`, `audit_log`

### 14.3 INPUT (Consumed By)

| Field | Type | Consumer Node | Description |
|-------|------|---------------|-------------|
| `user_message` / `domain_tags` | `str` / `list[str]` | PLAN | Query for matching plan templates |
| `sub_task_definitions` | `list[SubTaskDef]` | EXECUTE | Query for matching failure patterns |
| `domain` + `query` | `str` + `str` | RESEARCH | Query for cached research results |
| `tool_name` + `context` | `str` + `str` | RISK ASSESSMENT | Query for allowlist entries |

### 14.4 OUTPUT (Produced By)

| Field | Type | Producer Node | Description |
|-------|------|---------------|-------------|
| `plan_templates` | `list[Template]` | PLAN (on SUCCESS) | Successful plan archived for future seeding |
| `success_patterns` | `list[Pattern]` | EVALUATE (on SUCCESS) | Task signatures that led to success |
| `failure_patterns` | `list[Pattern]` | REPLAN (on successful fix) | Failure modes and their successful resolutions |
| `cache_entries` | `dict` | RESEARCH | Research results with TTL metadata |
| `allowlist_entries` | `list[AllowlistEntry]` | APPROVAL (on approval) | Approved tool+context combinations |

### 14.5 EDGE CASES

**Empty library (initial state):**
- First N tasks will have no templates, no cache, no allowlist. This is expected. The library becomes useful after ~10-20 completed tasks.
- During the bootstrap phase, PLAN always generates fresh plans. RESEARCH always returns cache misses. RISK ASSESSMENT always classifies every sub-task.

**SQLite corruption / unavailability:**
- SQLite file locked (concurrent write): retry with exponential backoff (100ms, 200ms, 400ms). If still locked, proceed in memory-only mode (no persistence).
- Database file corrupted: attempt recovery from WAL. If recovery fails, reinitialize empty database. Log critical error.
- Storage full: purge oldest cache entries first. If still full after purge, disable writes.

**Concurrent access:**
- Multiple pipeline instances may query/write simultaneously. SQLite supports concurrent readers but single writer. Writer lock contention should be rare (write events are post-execution only).
- Read-after-write consistency: queries that follow a write within the same pipeline instance should see the write. Use `isolation_level` to ensure consistency.

**TTL expiry:**
- Cache entries expire after configurable TTL (default 24h general, 7d domain-specific).
- Expired entries: return `stale: True` with the data. Do NOT automatically delete expired entries on read -- purge them on a periodic maintenance cycle.
- TTL refresh: on cache hit, extend TTL by one period (sliding window).

**Template matching edge cases:**
- Exact match against library: highest priority template.
- Semantic similarity match (NLP-based): lower priority, used when exact match not found.
- No match: return empty. Do NOT use a "close but wrong" template -- worse than no template.
- Multiple matches: return the highest-rated (by success_rating) template. Include reference IDs for potential ensembling.

**Recency vs. frequency:**
- Template selection favors RECENTLY SUCCESSFUL over frequently used. A template used 50 times but failing on the last 10 attempts is less valuable than a template used 3 times with 3 successes.
- Decay function: `score = success_rating * 0.9^(days_since_last_success)`. This ensures recent success dominates.

**State corruption:**
- In-memory state (templates loaded at startup) may drift from persistent state (SQLite). Reconciliation strategy: reload from SQLite every N queries (configurable, default 100) or on explicit invalidation.

**Token budget exhaustion:**
- Skill library queries are SQL queries, not LLM calls. No token consumption.

**Tool call failure:**
- Skill library is a local SQLite database. No external tool calls.

### 14.6 INTERFACES

```python
@dataclass
class ProblemSignature:
    domain: str
    task_type: str
    keywords: list[str]
    embedding: Optional[list[float]]  # For semantic matching (Wave 3)

@dataclass
class PlanTemplate:
    id: str
    signature: ProblemSignature
    commander_intent: CommanderIntent
    sub_task_template: list[SubTaskDef]
    success_rating: float  # 0.0 to 1.0
    use_count: int
    last_used: datetime
    created_at: datetime

@dataclass
class FailurePattern:
    id: str
    sub_task_signature: str
    failure_type: str
    resolution: str
    compensation_level_used: CompensationLevel
    success_count: int
    fail_count: int

class SkillLibrary:
    """Cross-cutting persistent knowledge store.

    SQLite-backed. Thread-safe for concurrent reads.
    Single-writer with retry on lock contention.
    """

    def __init__(self, db_path: str, config: SkillLibraryConfig):
        ...

    # Query methods
    def find_templates(
        self,
        signature: ProblemSignature,
        min_rating: float = 0.5,
        max_results: int = 3,
    ) -> list[PlanTemplate]:
        """Find matching plan templates by problem signature."""
        ...

    def find_failure_patterns(
        self,
        sub_task: SubTaskDef,
    ) -> list[FailurePattern]:
        """Find failure patterns matching a sub-task definition."""
        ...

    def query_cache(
        self,
        domain: str,
        query: str,
        max_age_hours: float = 24,
    ) -> Optional[CacheEntry]:
        """Query research cache with TTL check."""
        ...

    def check_allowlist(
        self,
        tool_name: str,
        context: str,
    ) -> Optional[AllowlistEntry]:
        """Check if a tool+context combination is pre-approved."""
        ...

    # Write methods
    def archive_plan(
        self,
        plan: Plan,
        result: EvaluationResult,
        domain_tags: list[str],
    ) -> str:
        """Archive a successful plan as a template."""
        ...

    def record_failure_pattern(
        self,
        sub_task: SubTaskDef,
        error: ExecutionError,
        resolution: str,
        level: CompensationLevel,
    ) -> str:
        """Record a failure pattern and its successful resolution."""
        ...

    def add_to_allowlist(
        self,
        tool_name: str,
        context: str,
        approved_by: str,
        risk_level: RiskLevel,
    ) -> None:
        """Add an approved tool+context to the allowlist."""
        ...

    # Maintenance
    def purge_expired(self) -> int:
        """Remove expired cache entries. Returns count purged."""
        ...

    def vacuum(self) -> None:
        """Rebuild database to reclaim space."""
        ...
```

### 14.7 INTERACTIONS

- **Consumed by:** PLAN (template seeding), EXECUTE (failure avoidance), RESEARCH (cache queries), RISK ASSESSMENT (allowlist checks).
- **Written by:** EVALUATE (on SUCCESS -- archive plan), REPLAN (on successful fix -- record failure pattern), APPROVAL (on approval -- add to allowlist).
- **NOT written by:** CLASSIFY, FAST EXECUTE, BACKBRIEF, PREMORTEM, BRANCHING MONITOR, SYNTHESIZE (read-only consumers).
- **Thread safety:** Singleton pattern. All access goes through `SkillLibrary.get_instance()` which manages the SQLite connection pool.
- **Startup:** Library loads template index into memory on first access. Cache query cache in memory. Writes go to SQLite synchronously.

### 14.8 FAST PATH

Not directly applicable. SKILL LIBRARY is a cross-cutting service, not a pipeline node. It is available to all paths but only actively queried by STANDARD/DEEP nodes. FAST EXECUTE does not query the library.

### 14.9 INTEGRATION RISK

The hardest thing about SKILL LIBRARY is **embedding-based semantic matching** (Wave 3 ambition). For Wave 2, keyword-based matching is sufficient but limited -- "create a REST API" and "build a RESTful service" will not match on keywords alone. The Wave 2 approach should be based on domain_tags + structured fields (tools_required, task_type) rather than full semantic similarity.

Second-hardest: **recency-weighted template selection.** The decay function must be tuned so that recent successes dominate without completely ignoring high-frequency historical patterns. A template that was highly successful but hasn't been used in 6 months should be available but deprioritized.

Third-hardest: **concurrent write contention.** Post-execution archival writes may contend with concurrent reads from other pipeline instances. SQLite's WAL mode helps with read concurrency but writer contention remains. The exponential backoff with retry strategy handles transient contention but may lose writes under sustained load.

---

## A. SIMPLE CHAT

### A.1 Trace: "what is 2+2?"

**Path:** CLASSIFY -> FAST EXECUTE -> SYNTHESIZE -> OUTPUT

**Step-by-step:**

1. **CLASSIFY** receives `user_message = "what is 2+2?"`.
   - TAPE triage: single sentence, factual, no ambiguity, no tool requirements, single domain (math).
   - `complexity_factors = {novelty: 0.0, ambiguity: 0.0, tool_requirements: 0.0, domain_uncertainty: 0.0}`
   - Denylist check: no code patterns, no file system access, no network calls. `denylist_triggered = False`.
   - `pipeline_path = "FAST"`, `domain_tags = ["math"]`
   - **Latency:** ~100ms (cheap model, single classification call).

2. **FAST EXECUTE** receives the state.
   - Verifies `pipeline_path == "FAST"` and `denylist_triggered == False`.
   - Single LLM call with cheap model (DeepSeek Flash). Prompt: "Answer the user's question directly and concisely. Do not use any tools. User: what is 2+2?"
   - Model returns "4."
   - Response length check: 2 characters, well under 2048 limit.
   - Response uncertainty check: no hedging phrases. `uncertainty_detected = False`.
   - **Latency:** ~200-500ms (single LLM call, cheap model).

3. **SYNTHESIZE** receives the state.
   - `pipeline_path` is "FAST", so SYNTHESIZE uses FAST path mode.
   - `synthesized_output = "4."`
   - `quality_report = QualityReport(is_consistent=True, completeness_score=1.0)`
   - No quality review LLM call (FAST path skips it).
   - **Latency:** ~1ms (dict assignment).

4. **EVALUATE** receives the state.
   - FAST path: always SUCCESS for well-formed responses.
   - `evaluation_result = "SUCCESS"`
   - Output returned to user: "4."
   - **Latency:** ~1ms.

**Total latency:** ~300-600ms. One LLM call (classification) + one LLM call (response). Two total LLM calls, both using the cheapest model.

**State fields set:**
- `pipeline_path = "FAST"`
- `fast_response = "4."`
- `synthesized_output = "4."`
- `evaluation_result = "SUCCESS"`

**State fields never touched:** `plan`, `sub_tasks`, `risk_levels`, `failure_scenarios`, `branching_report`, `approval_decision`, `delta_plan`, `research_findings`, `verification_result` -- all remain at defaults (None/empty).

### A.2 Trace: "explain a for-loop"

**Path:** CLASSIFY -> FAST EXECUTE -> SYNTHESIZE -> OUTPUT

Same as above, except the FAST EXECUTE LLM call produces a multi-sentence explanation.

**Complexity thresholds:**
- If the user had asked "explain a for-loop and then write one in Python that iterates over a list" -- this would still be FAST (conceptual + simple code example, no tool execution needed). The FAST path handles "explain and give an example" -- it does not execute the code.
- If the user had asked "write a for-loop and run it" -- this triggers the denylist (code execution). Escalation to STANDARD.
- If the user had asked "explain a for-loop comparing it to while loops and for-each loops with performance analysis" -- this might be complex enough for STANDARD (multi-faceted, requires organized response). CLASSIFY would evaluate ambiguity/novelty and may escalate.

### A.3 What Prevents a Simple Chat Over-Classification

The conservative bias is: when uncertain, escalate UP (FAST -> STANDARD). This means borderline queries get MORE compute, not less. The FAST path is only taken when the classifier is confident. This is correct behavior -- the user waits slightly longer for a correct answer rather than getting a fast-but-incomplete answer.

### A.4 What Prevents Abuse of the FAST Path

The denylist is the primary protection. A user cannot trick the FAST path into executing code or accessing the file system because CLASSIFY checks for these patterns BEFORE routing to FAST EXECUTE. If the user's "simple question" mentions file paths, code execution, or network access, it escalates to STANDARD where the full guardrail stack applies.

FAST EXECUTE itself has no tool access. Even if the model hallucinated a request to use a tool, the executor strips it.

---

## B. KNOWLEDGE/SCOPE GAPS

### B.1 Detection Points

Knowledge/scope gaps are detected at multiple nodes:

| Node | What is Detected | Signal |
|------|------------------|--------|
| **CLASSIFY** | Insufficient info to classify | Ambiguity factor > 0.7 in complexity_factors. Domain uncertainty high. Returns "STANDARD" (not "FAST") for ambiguous queries. |
| **PLAN** | Insufficient info to plan | LLM generates a plan with placeholder sub-tasks ("clarify requirements", "ask user about X"). Plan metadata includes `plan_confidence < 0.4`. |
| **RESEARCH** | No relevant knowledge found | Cache miss + `knowledge_gaps` non-empty. No LLM context available (or LLM context also uncertain). |
| **EXECUTE** | Tool returns "not found" or error | Tool returns empty results, 404, or "not found" error. Compensation handler triggered at catch/fallback level. |
| **EVALUATE** | Criteria cannot be assessed | Acceptance criteria reference undefined concepts. Evaluation detail includes "cannot assess criterion X due to missing information." |
| **REPLAN** | Previous attempt failed from lack of info | REPLAN analysis determines that failure was due to missing information, not execution error. Compensation level escalates to human_escalation. |

### B.2 What the System DOES

When a knowledge/scope gap is detected, the system has three responses, determined by gap severity:

**Level 1 -- Note and Continue (Low severity):**
- Gap is minor, system has enough context to proceed confidently.
- Action: annotate the output with a caveat ("Based on available information..." or "Note: this assumes X").
- Used by: RESEARCH (cache miss with some context), EXECUTE (partial tool results).

**Level 2 -- Replan with Broader Scope (Medium severity):**
- Gap is significant enough that the current plan cannot succeed.
- Action: REPLAN generates a delta that includes "gather information" sub-tasks. The FRAGO loop broadens scope to fill the gap.
- Used by: EVALUATE (when criteria are unmet due to information gaps), REPLAN (when analysis determines the gap is fillable).

**Level 3 -- Human Escalation (High severity):**
- Gap is fundamental -- the system cannot proceed without additional information from the user.
- Action: halt pipeline, ask the user specific questions to fill the gap. Return to PLAN after user responds with the missing information.
- Used by: REPLAN (when compensation level reaches human_escalation), PLAN (when plan_confidence < 0.2 even after skill library seeding).
- Specifically: the system presents a structured question: "I need the following information to proceed: [list of gaps]." The pipeline resumes from PLAN when the user provides the missing information.

### B.3 What the System Does NOT Do

- The system does NOT guess wildly in the presence of significant gaps. Level 3 halts and asks.
- The system does NOT silently produce incorrect output. Level 1 caveats annotate uncertainty.
- The system does NOT default to "I don't know" for minor gaps. Level 1 continues with caveats.

### B.4 Gap Detection Ceiling

The system will attempt Level 2 (replan) up to 3 times (FRAGO ceiling). If the gap persists after 3 replans, it escalates to Level 3 (human). This prevents infinite loops around unfillable knowledge gaps.

---

## C. PLANNING DEAD-ENDS

### C.1 Types of Dead-Ends and Detection

| Dead-End Type | Detected By | Signal | Action |
|---------------|-------------|--------|--------|
| **Circular DAG dependency** | BACKBRIEF (DAG check) | `dag_result.has_circular_dependency == True` | Back to PLAN for revision. If persisting after 2 revisions, force-pass and flag. |
| **Tool unavailability** | EXECUTE (compensation handler) | Tool returns "not found" or authorization error. Catch/fallback fails. | Escalate compensation ladder. If all handlers exhausted, mark sub-task FAILED and let EVALUATE/REPLAN handle. |
| **Impossible state assumption** | PREMORTEM | Persona identifies an assumption that is invalid (e.g., "this requires a database that doesn't exist"). | Back to PLAN for revision. PREMORTEM ceiling (2 cycles) applies. |
| **Pre-mortem ceiling hit** | PREMORTEM | `premortem_cycle_count >= 2` and `fatal_flags` still non-empty. | Force-pass. ANNOTATE approval briefing with "Unresolved pre-mortem flags -- execution may encounter these failure modes." |
| **FRAGO replan ceiling hit** | Graph topology (before REPLAN) | `replan_count >= max_replans` (default 3). | Force synthesize. Output is whatever was produced, with annotation: "Replan ceiling reached -- output may be incomplete." |
| **Branching factor >= 1** | BRANCHING FACTOR MONITOR | `branching_report.has_divergent_branch == True` | Halt and route to REPLAN. REPLAN generates delta that flattens the branching. If branching persists after replan, force-pass with annotation. |
| **All sub-tasks fail** | EVALUATE | `evaluation_result == "FAILURE"` with no sub-tasks succeeding. | Route to REPLAN. If persists after ceiling, output failure message to user. |
| **Approval rejection** | APPROVAL GATE | `approval_decision.decision == "rejected"` | Route to REPLAN with rejection reason. If rejected 3 times, output "Unable to proceed -- plan rejected." |

### C.2 Circular DAG Dependency -- Detailed Flow

1. PLAN generates a DAG with: A depends on B, B depends on C, C depends on A.
2. BACKBRIEF runs DAG consistency check: cycle detected at C-A edge.
3. `verification_result.passed = False`, flag category "dag", severity "error".
4. Since `revision_count (0) < max_revisions (2)`, route to PLAN for revision.
5. PLAN revises: restructures DAG to remove cycle (e.g., merges A and C into one sub-task, or reorders dependencies).
6. BACKBRIEF re-runs: DAG is now acyclic. `passed = True`.
7. Pipeline proceeds.

**If BACKBRIEF cannot fix after 2 revisions:** force-pass, flag as HIGH risk (reason: unresolved DAG structure).

### C.3 Tool Unavailability -- Detailed Flow

1. EXECUTE attempts sub-task: "deploy to AWS S3."
2. Tool `aws s3 cp` returns "AccessDenied: User does not have s3:PutObject permission."
3. Retry (level 1): same call, different auth context. Fails again.
4. Catch/fallback (level 2): try alternative tool `aws s3api put-object`. Same permission issue.
5. Local compensation (level 3): generate a signed URL for the user to upload manually. Falls back to producing the upload script.
6. Radius expansion (level 4): check if downstream sub-tasks (which consume the S3 URL) can proceed without it. If yes, skip this sub-task and proceed. If no, mark this sub-task and its dependents as FAILED.
7. Global replan (level 5): REPLAN generates a delta that replaces S3 deployment with an alternative (e.g., generate a deployment package for manual upload).
8. Human escalation (level 6): if all automated recovery exhausted, halt and ask user for S3 credentials or alternative approach.

### C.4 What Happens After Detection

**After any dead-end detection (except ceiling hit):**
1. The system attempts to recover (revise plan, try compensation, etc.).
2. Recovery is bounded by a ceiling (2 revisions, 3 replans, 2 pre-mortem cycles).
3. If recovery succeeds: pipeline continues normally.

**After ceiling hit (recovery exhausted):**
1. Force-pass: continue with what exists, annotated with warnings.
2. The output reaches the user with the annotation.
3. The failure pattern is recorded in the skill library for future avoidance.

**After unrecoverable dead-end (e.g., all sub-tasks failed, all replans exhausted):**
1. Output: clear failure message to user explaining what went wrong.
2. If partial output exists, include it with caveats.
3. Skill library: record the failure pattern.

---

## D. PRODUCTION EDGE CASES

### D.1 Checkpoint/Resume Mid-Pipeline

**Requirement:** Any pipeline invocation must be able to pause and resume mid-execution without data loss or duplicate execution.

**Mechanism:** LangGraph's built-in checkpointing. After each node completes, the full `PipelineState` is serialized and stored. On resume, the graph reads from the stored checkpoint and continues from the interrupted node.

**Edge cases:**
- **Resume after node in-flight (mid-LLM-call):** NOT supported. Resume is at node boundaries only. Mid-LLM-call interruptions abort the call and retry on resume.
- **Resume after APPROVAL GATE (human interrupted during approval):** Supported. The approval state is persisted. On resume, the approval briefing is re-displayed with the previous context. The user can re-approve or reject.
- **Resume after EXECUTE (partial sub-task completion):** Supported. Completed sub-task results are persisted. On resume, only uncompleted sub-tasks are executed.
- **State schema migration (code changed between checkpoint and resume):** If the PipelineState schema changed, the checkpoint is incompatible. Detection: version hash in checkpoint metadata. If mismatch, abort resume and warn user: "Pipeline state is from a different version. Cannot resume."
- **Checkpoint corruption:** Checkpoint fails to deserialize. On failure: abort resume, ask user to restart the pipeline.
- **Expired checkpoint:** Checkpoints older than configurable TTL (default 24 hours) are deleted. On resume attempt for expired checkpoint: inform user and discard.

### D.2 Concurrent User Requests

**Requirement:** Multiple users must be able to invoke the pipeline simultaneously without state interference.

**Mechanism:** Each pipeline invocation gets an isolated `PipelineState` instance. LangGraph's `CompiledGraph` is thread-safe for concurrent invocations -- each call creates a new state.

**Edge cases:**
- **Shared skill library (SQLite):** SQLite supports concurrent readers but single writer. Writer contention handled via retry with backoff (see Skill Library edge cases).
- **Shared tool registry:** Tool registry is read-only after initialization. No concurrent modification.
- **Shared model clients:** LLM clients are thread-safe (connection pooling). Rate limiting is applied per API key, not per pipeline.
- **Resource contention (e.g., temp files):** Sub-tasks that write to temp files must use isolated paths (e.g., `tempfile.mkdtemp()` per sub-task). The executor enforces this.
- **Memory isolation:** Each pipeline invocation runs in the same process but with separate state. Python's GIL provides memory safety but LangGraph ensures state isolation at the application level.

### D.3 Long-Running Sub-Tasks vs. Timeout Policy

**Requirement:** Sub-tasks that take longer than expected must be timed out rather than allowed to run indefinitely.

**Mechanism:** Each sub-task has a configurable timeout. Defaults: LOW risk = 30s, MEDIUM = 60s, HIGH = 120s, CRITICAL = 300s. Timeout is enforced at the tool call level (each tool call has its own timeout).

**Edge cases:**
- **Compound timeout (sub-task with multiple tool calls):** The per-sub-task timeout covers the TOTAL time across all tool calls within the sub-task, not per-call. If the sub-task exceeds its total timeout, it is interrupted mid-flow.
- **Timeout during retry:** Each retry attempt resets the timer. Total time across all retries is `timeout * (1 + max_retries)`. This is tracked and bounded.
- **Timeout dependency propagation:** If sub-task A times out and sub-task B depends on A, B cannot start until A completes or is skipped. If A times out, B is marked as SKIPPED (dependency_failed).
- **Background LLM calls:** Some LLM calls may appear to hang (no output, no error). The timeout mechanism catches these at the tool call level.
- **User-configurable timeouts:** Pipeline-wide timeout multiplier (default 1.0) can be adjusted per invocation. Emergency brake: if pipeline exceeds total timeout (sum of all sub-task timeouts + overhead), the entire pipeline halts.

### D.4 Tool Deprecation Mid-Execution

**Requirement:** A tool may be deprecated while a pipeline is running. The system must handle this gracefully.

**Mechanism:** Tool registry loads tool definitions at pipeline start. Tools are snapshot-per-invocation -- if a tool is deprecated mid-execution, the current invocation continues with the snapshot. New invocations use the updated registry.

**Edge cases:**
- **Deprecation warning (tool returns deprecation header):** Log warning. Flag execution metadata for skill library audit. Continue executing.
- **Tool removed from registry mid-execution:** The current invocation's snapshot is unaffected. Next invocation will fail on `tool not found`. Mitigation: if a tool is missing from registry at invocation start, the plan node should detect this during planning (tool_required vs. available_tools mismatch).
- **Tool behavior change (same API, different semantics):** This is the hardest case -- the tool does not error but produces different results. No automated detection. Mitigation: Post-execution regression check (Wave 3), comparing output structure to historical patterns from skill library.
- **API version mismatch:** If the tool's API version changes but the system sends old-format requests, the tool may return a version error. This triggers the compensation ladder (catch/fallback: try new format).

### D.5 Model Version Change Mid-Execution

**Requirement:** The LLM model powering a node may change versions during execution (e.g., provider deploys a new checkpoint).

**Mechanism:** Model clients use pinned model versions (e.g., `deepseek-chat-v3-0524`, not `deepseek-chat-latest`). The model version is part of the invocation's configuration snapshot.

**Edge cases:**
- **Pinned version deprecated:** If the pinned version is no longer available, the client falls back to the next available version in the same family. Log warning.
- **Behavior regression in new version:** A model update may change output quality mid-execution. Mitigation: (a) pin versions per invocation, (b) the skill library's success tracking can detect confidence/intent drift over time, (c) A/B test new versions against historical baselines before rolling out.
- **Multi-model pipeline (different nodes use different models):** The model version change affects only the specific node. Other nodes continue with their pinned versions. The evaluation may detect quality degradation and trigger replan.
- **User-visible model version:** The audit trail records which model version was used at each node. If output quality is questioned, the version information is available for debugging.

### D.6 Plan/State Drift

**Requirement:** A plan that was valid at pipeline start may become invalid due to external state changes.

**Mechanism:** The pipeline captures the state of the world at invocation start. Sub-tasks that interact with external systems validate preconditions before executing (idempotent where possible).

**Edge cases:**
- **External resource deleted mid-execution:** A sub-task attempts to read a file that another concurrent pipeline deleted. EXECUTE compensation handler: catch/fallback (regenerate if possible) or fail.
- **External service degraded:** An API returns 503 during execution. Retry with exponential backoff. If persistent, compensate or fail.
- **Time-sensitive plan:** A plan that depends on temporal conditions (e.g., "deploy on Friday at 5 PM") must detect if the condition is still valid at execution time. PLAN includes time constraints in Commander's Intent. EXECUTE checks preconditions.
- **State drift detection:** Each sub-task can optionally check preconditions before executing. This is defined in the sub-task's description (flexible) or via tool-level precondition checks (systematic, Wave 3).

### D.7 User Interrupts (Ctrl+C)

**Requirement:** A user must be able to interrupt a running pipeline.

**Mechanism:** LangGraph supports `interrupt()` which pauses execution at graph boundaries. For user-initiated interrupts, the pipeline is interrupted at the next checkpoint boundary.

**Edge cases:**
- **Interrupt during LLM call:** The LLM call is aborted. No partial state is saved. On resume, the call retries.
- **Interrupt during tool execution:** The tool call is aborted. Tool-side effects may have occurred (e.g., a file was half-written). Mitigation: EXECUTE uses atomic operations where possible (write to temp file, then rename). Compensation handler for partially-completed tool operations.
- **Interrupt during APPROVAL GATE (human-in-the-loop):** The approval is pending. Interrupt returns to shell. On resume, approval briefing is re-displayed.
- **Interrupt at pipeline boundaries:** The cleanest interrupt point. The graph is between nodes; state is fully checkpointed. Resume continues from the next node.
- **User intention after interrupt:** "cancel" (discard state) vs. "pause" (resume later). The interrupt handler must present this choice. Default: pause (state preserved).

### D.8 Multi-Tenant Isolation

**Requirement:** The system must prevent data leakage between different users or projects.

**Mechanism:** Each pipeline invocation is associated with a tenant ID (user or project). State is isolated by tenant. Skill library records are tagged with tenant ID.

**Edge cases:**
- **Shared skill library (multi-tenant):** The skill library has a `tenant_id` column on all tables. Queries include `WHERE tenant_id = ?`. This is simple in SQLite but the database file is shared; a SQL injection in the tenant ID could leak data across tenants. Mitigation: tenant ID is validated against a whitelist, not user input.
- **Shared model routing (cost allocation):** Each tenant has a cost budget. The model router must track token usage per tenant and enforce budget limits. Budget exhaustion: tenant's requests are queued or rejected.
- **Shared tool registry (tool permissions per tenant):** Some tools may be available only to certain tenants (e.g., production deployment tools). The tool registry filters available tools per tenant. If a plan references a tool the tenant does not have access to, EXECUTE fails with authorization error.
- **State isolation:** Pipeline state is entirely in-memory per invocation, not shared across tenants. No cross-tenant state leakage.

### D.9 Cost-Budget Exhaustion

**Requirement:** The system must respect cost budgets per invocation and per tenant.

**Mechanism:** Token budget tracking at the invocation level. Each node deducts from the budget before making LLM calls. If budget is exhausted, the node uses the cheapest available fallback or skips the call.

**Edge cases:**
- **Per-invocation budget exceeded:** The pipeline pauses mid-execution. Options: (a) request more budget from user, (b) switch to cheapest models for remaining sub-tasks, (c) fail gracefully with partial output. Default: (b) if remaining budget > 30%, else (c).
- **Per-tenant monthly budget exceeded:** New invocations are rejected. In-flight invocations continue (they already committed resources).
- **Cost-aware model routing:** The model router selects models based on sub-task complexity and remaining budget. HIGH-complexity sub-tasks get premium models; LOW-complexity sub-tasks get cheap models.
- **Token budget vs. cost budget:** Token budget is a proxy for cost budget. Calibration: budget in tokens * cost_per_token = cost budget. The model router tracks both.
- **Budget monitoring:** The branching report includes projected remaining budget. If budget is projected to exhaust before completion, the branching monitor may recommend replanning to reduce scope.

### D.10 Prompt Injection into Sub-Task Prompts

**Requirement:** Sub-task prompts that include user-provided content must be guarded against prompt injection.

**Mechanism:** Input sanitization at the EXECUTE node. Every sub-task prompt that incorporates user content is wrapped with prompt boundary markers and the model is instructed to follow the system instructions (not user content instructions).

**Edge cases:**
- **Direct injection in user_message:** CLASSIFY's denylist catches obvious injection patterns ("ignore previous instructions", "you are now ..."). LLM-based classifier may catch subtle ones.
- **Indirect injection through tool output:** A tool returns data that contains injection attempts. EXECUTE must sanitize tool outputs before including them in subsequent LLM prompts.
- **Multi-step injection:** An injected instruction tells the model to produce output that, when used as input to a subsequent sub-task, triggers another injection. Hard to detect. Mitigation: output guardrails on each sub-task's output (Wave 3), checking for embedded instructions.
- **Data exfiltration through injection:** An injected instruction tells the model to include sensitive data in its output. Mitigation: output guardrails scan for patterns that match sensitive data signatures (API keys, tokens, PII).
- **Injection through skill library templates:** If an archived template contains injected instructions, the injection is replayed every time the template is used. Mitigation: template validation on archival scans for injection patterns.
- **Injection through research cache:** Similar to skill library -- cached research results that contain injected content. Mitigation: cache entries are treated as data, not instructions. They are presented to the model with "this is reference data" wrapping.
- **Defense-in-depth:** Input guardrails (detect), prompt wrapping (contain), output guardrails (detect exfiltration). Three layers, each independent.

---

*End of JORDAN v2 Granular Implementation Specification -- DRAFT v1*
