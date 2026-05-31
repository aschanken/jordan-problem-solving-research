# JORDAN v2 — How It Actually Functions

**Version:** 2.0.0  
**Pipeline:** 12-node LangGraph state machine  
**Execution Paths:** FAST · STANDARD · DEEP  

JORDAN v2 is a general-purpose task execution pipeline built on LangGraph's
`StateGraph`. It takes a user query, classifies its complexity, decomposes it
into a dependency-ordered plan, assesses risk, solicits approval when
warranted, executes subtasks, evaluates the result, and replans if the output
fails quality checks — all with a military-planning-inspired discipline.

---

## 1. The Three Execution Paths

The first thing JORDAN does is classify the query's complexity. That single
decision determines which of three paths the entire run follows:

| Path | When | Gates | Approval |
|---|---|---|---|
| **FAST** | Trivial single-step queries ("What's the weather?", "List files") | None | None — auto-approved by routing |
| **STANDARD** | Multi-step tasks of moderate complexity | Backbrief → Research → Risk → Premortem → Branching → Approval | Auto-approves LOW/MEDIUM risk; escalates HIGH/CRITICAL |
| **DEEP** | Complex, multi-dimensional, or safety-flagged queries | Same full pipeline as STANDARD + multi-COA generation + MAKER decomposition | Always requires human approval |

---

## 2. The 12 Nodes in Traversal Order

```
CLASSIFY → PLAN → BACKBRIEF → RESEARCH → RISK ASSESSMENT → PREMORTEM →
BRANCHING MONITOR → APPROVAL GATE → EXECUTE → SYNTHESIZE → EVALUATE → [REPLAN ⟲]
```

### 2.1 CLASSIFY — The Router

**File:** `nodes/classifier.py`

The CLASSIFY node is a single gate everything passes through. It scores the
query across five dimensions:

| Dimension | What It Measures | Weight |
|---|---|---|
| **Length** | Character count (< 100 / 200 / 500) | 0–2 |
| **Structural complexity** | Sentence count, multi-part markers | 0–2 |
| **Deep-analysis signals** | Keywords like "analyze", "synthesize", "compare" | Variable sum |
| **Safety signals** | Regex patterns for credentials, exploits, bypass phrases | +3 per match |
| **Action-verb density** | Verbs like "write", "deploy", "configure", "refactor" | Floor/bump modifier |

**Conservative bias:** Any safety signal match forces DEEP regardless of the
score. If total score exceeds thresholds, it escalates upward (FAST → STANDARD,
STANDARD → DEEP) rather than down.

**Denylist pre-check:** Before scoring, the query is scanned against a
hot-reloadable YAML/JSON denylist of regex patterns. Any denylist match
overrides the heuristic and forces DEEP, regardless of what the heuristic
would have chosen. Disagreements between the denylist and the heuristic are
logged to the skill library for analysis.

**DEEP overrides:** If classified as DEEP, `n_coas` is set to 3 (three Courses
of Action will be generated), and execution mode is set to SEQUENTIAL (COAs
are compared one at a time, not in parallel).

**Routing outcome:**
- FAST → direct to EXECUTE node (skips everything between)
- STANDARD / DEEP → PLAN node

### 2.2 PLAN — Task Decomposition

**File:** `nodes/planner.py`

Decomposes the user query into a structured plan containing:

**Commander's Intent** — the "why" behind the plan:
- `goal`: What must be achieved
- `constraints`: What must not be violated
- `acceptance_criteria`: How success is measured
- `priority`: low / medium / high

**Sub-tasks** — each is a discrete unit of work:
- `id`, `description`, `tools_required[]`, `dependencies[]`,
  `domain`, `correctness_critical`, `verifiable_output`

**DAG** — a directed acyclic graph mapping dependency edges between sub-tasks
(`subtask_id → [dependency_ids]`). This defines the execution order.

**For DEEP path only:** PLAN generates **three Courses of Action (COAs)**
with distinct approach strategies:
- `top-down`: Decompose from goal to sub-tasks
- `bottom-up`: Build up from available tools
- `iterative`: Start minimal, refine cyclically

Each COA is a complete `Plan` with its own sub-tasks, DAG, and
`dsm_coupling_score`. The COA with the lowest coupling score is selected
for execution.

### 2.3 BACKBRIEF — Structural Review

**File:** `nodes/backbrief.py`

Inspired by the military backbrief — the executor briefs the commander on
*how they interpret the order* before executing. In JORDAN, this is a
structural integrity check on the plan DAG:

1. **DAG cycle detection** — DFS traversal; any cycle is reported for revision.
2. **DSM (Dependency Structure Matrix) coupling analysis** — measures hidden
   coupling between sub-tasks by projecting dependency edges into an N×N
   matrix and scoring how densely interconnected the plan is. A high coupling
   score (> 0.5) indicates the plan is fragile — changes to one sub-task are
   likely to cascade.
3. **Missing-dependency detection** — flags sub-tasks whose prerequisites
   aren't represented as edges.

**Routing:**
- First-pass clean → proceed to RESEARCH
- Issues found (revision_count < 2) → back to PLAN for regeneration
- Forced pass (backbrief_forced flag) or revision_count ≥ 2 → proceed
  (ceiling force-pass to prevent infinite loops)

### 2.4 RESEARCH — Cache & Knowledge Gap Detection

**File:** `nodes/research.py`

Checks whether the information needed to execute each sub-task is available:

1. **Cache lookup** — queries the skill library for previously cached research
   results matching each sub-task's domain.
2. **Knowledge gap detection** — if no cached data exists, classifies the gap
   as either `cache_miss` (the system just hasn't seen this before) or
   `genuine_gap` (the information genuinely isn't in the system).
3. **Scope change detection** — if the research reveals that the user's query
   is substantially different from what was originally classified, sets the
   `scope_change_detected` flag (appears as a warning in the approval briefing).

**Interrupt:** A `genuine_gap` with `requires_escalation=True` causes the
pipeline to pause at END and wait for the user to provide context via the
knowledge-gap resolution endpoint before re-entering.

### 2.5 RISK ASSESSMENT — Per-Subtask Risk Scoring

**File:** `nodes/risk.py`

Evaluates each sub-task for operational risk:

- **Constraint scanning** — checks each sub-task description against known
  dangerous patterns (shell injection, credential exposure, destructive
  filesystem operations).
- **Domain risk mapping** — sub-tasks in `safety_critical_domains`
  (authentication, infrastructure, data deletion) get floor-raised to HIGH.
- **Overall risk score** — a float 0.0 (safe) to 1.0 (critical), computed as
  the max per-sub-task risk level, normalized.

**Routing:**
- `risk.halted = True` (critical constraint violation) → END (pipeline aborts)
- FRAGO replan path (replan_count > 0) → skip premortem/branching/approval,
  proceed directly to EXECUTE
- Otherwise → PREMORTEM

### 2.6 PREMORTEM — Failure Scenario Analysis

**File:** `nodes/premortem.py`

Inspired by Klein's 2007 pre-mortem technique: *assume the plan has already
failed, then work backward to explain why.* Runs five distinct persona-driven
analyses:

| Persona | Lens | Example Concern |
|---|---|---|
| Pessimist | What goes wrong | "Sub-task X will produce incorrect output" |
| Safety Officer | Safety violations | "Tools with shell access on untrusted input" |
| Resource Monitor | Budget/time overruns | "Too many parallel sub-tasks" |
| Quality Auditor | Output quality failure | "Missing acceptance criteria" |
| Integration Lead | Cross-cutting failure | "Sub-task A's output won't match B's input" |

Each persona generates `FailureScenario` objects with `severity` (low/medium/
high/critical), `affected_sub_tasks[]`, and `likelihood` (0.0–1.0). The node
will iterate (up to 2 cycles) generating mitigations for any unmitigated
HIGH/CRITICAL scenarios.

**Routing:**
- All scenarios mitigated → BRANCHING MONITOR
- Unmitigated scenarios remain and cycle_count < 2 → back to PLAN for
  regeneration with mitigation directives
- Ceiling force-pass (cycle_count ≥ 2 or all_personas_failed) →
  BRANCHING MONITOR with advisory

### 2.7 BRANCHING MONITOR — DAG Complexity Governor

**File:** `nodes/branching.py`

Prevents the plan from becoming too wide or deep to execute effectively:

- **DAG depth** — longest path from leaf to root in the dependency graph.
- **Branching factor** — average number of children per parent node.
- **Spawn tracking** — cumulative count of sub-tasks across replan iterations
  (prevent unbounded growth from repeated FRAGO deltas).

**Halting conditions:** DAG depth exceeds `max_dag_depth` (default 10),
or total sub-tasks exceed `max_total_subtasks`.

**Routing:**
- Not halted → APPROVAL GATE
- Halted → END (pipeline aborts with branching_halt status)

### 2.8 APPROVAL GATE — Risk Fusion & Progressive Disclosure

**File:** `nodes/approval.py`

The most complex node. It reconciles signals from RISK ASSESSMENT and
PREMORTEM, builds a tiered briefing, and decides whether to approve, reject,
or escalate.

#### Risk Fusion

Fuses two independent risk signals per sub-task into a single fused level:

```
fused_risk = max(risk_assessment_level, premortem_max_level)
```

With two modifiers:
- **Safety domain floor:** If the sub-task's domain appears in
  `safety_critical_domains`, the floor is raised to HIGH.
- **Premortem staleness:** On FRAGO replan paths (replan_count > 0),
  premortem data is excluded from fusion (it analyzed a different plan
  iteration).

#### Progressive Disclosure Briefing

The briefing is structured in two tiers:

**Tier 1 (Executive Summary)** — what the commander sees first:
- Objective (from Commander's Intent)
- Overall risk level badge
- Total sub-tasks & CRITICAL ones
- Active path (STANDARD / DEEP)
- Warning flags: scope change, backbrief forced, unaddressed safety

**Tier 2 (Detailed Briefing)** — what the commander expands to see:
- Per-sub-task breakdown (risk, tools, deps, domain, correctness-critical)
- Knowledge gaps (cache misses / genuine gaps)
- Risk provenance (which signal contributed to each sub-task's risk)
- Revision history (replan iterations)

#### Decision Logic

Applied in priority order:

1. **Halted by risk → REJECTED** (pipeline stops)
2. **Any CRITICAL fused risk → ESCALATED to human**
3. **DEEP path → ESCALATED to human** (always-on approval)
4. **FAST path with LOW risk → APPROVED** (auto)
5. **STANDARD with LOW/MEDIUM risk → APPROVED** (auto)
6. **HIGH risk → ESCALATED to human**
7. **Fallback → APPROVED**

**Routing after decision:**
- Approved → EXECUTE
- Rejected → REPLAN
- Escalated → SYNTHESIZE (outputs an escalation note instead of executing)

### 2.9 EXECUTE — Dependency-Ordered Parallel Execution

**File:** `nodes/executor.py`

Runs the plan's sub-tasks in dependency order, respecting the DAG:

- **Dependency resolution** — a sub-task only launches when all its
  dependency edges have resolved to completed sub-tasks.
- **Parallelism** — respects `max_concurrent_subtasks` config; independent
  branches run concurrently.
- **Isolation** — sub-tasks with non-null `isolation_key` run in isolated
  contexts (worktrees or sandboxes).
- **Error handling** — a failed sub-task doesn't cascade; its error is
  recorded and execution continues with remaining sub-tasks. Compensation
  strategies from earlier replan cycles may be applied.
- **MAKER decomposition (DEEP only)** — correctness-critical, verifiable
  sub-tasks are further decomposed into 4 atomic steps:
  Design → Implement → Test → Verify. Each step is tracked independently.

**Routing:** Always proceeds to SYNTHESIZE after all sub-tasks complete.

### 2.10 SYNTHESIZE — Output Assembly

**File:** `nodes/synthesize.py`

Merges the outputs of all completed sub-tasks into a coherent final response:

- **Type-aware merge** — handles heterogeneous output formats
  (text + code + structured data) by detecting format heterogeneity and
  normalizing minority formats.
- **Completeness check** — scores how many acceptance criteria from
  Commander's Intent were satisfied by the collected outputs.
- **Output guardrail inspection** — scans the synthesized output for
  dangerous content, tool-call hallucinations, and safety refusals. If the
  guardrail fails, the output is intercepted and flagged rather than
  delivered.

### 2.11 EVALUATE — Quality Assessment

**File:** `nodes/evaluate.py`

Algorithmically evaluates the synthesized output against the original plan:

**4-result outcome:**
| Result | Meaning |
|---|---|
| `SUCCESS` | All acceptance criteria met, no degradation |
| `PARTIAL` | Some criteria met, some missed |
| `FAILURE` | Output fundamentally incorrect |
| `UNEQUIVALENT` | Output changed the subject or ignored the query |

**Metrics:**
- `score` (0.0–1.0): Overall quality score
- `criteria_met / criteria_total`: How many acceptance criteria passed
- `keyword_coverage`: Thematic overlap between query and output
- `degrading`: True if this evaluation score is *worse* than the previous
  evaluation (used for degradation detection in REPLAN)

**Routing:**
- PASSED (SUCCESS result) → END (pipeline complete)
- FAILED / PARTIAL / UNEQUIVALENT → REPLAN (unless max iterations hit)
- Degrading + previous also degrading → REPLAN triggers human escalation

### 2.12 REPLAN — FRAGO Delta Generation

**File:** `nodes/replanner.py`

When evaluation fails, the REPLAN node generates a **FRAGO (FRAGmentary
Order)** — a targeted delta to the *existing* plan rather than a full replan
from scratch. This is the military concept of issuing a fragmentary order to
adjust a plan in motion without re-issuing the entire operations order.

#### Trigger Identification

Determines what went wrong, in priority order:
1. **backbrief_rejection** — plan structure was flawed
2. **premortem_failure** — unmitigated failure scenarios remained
3. **approval_rejection** — the gate denied the plan
4. **evaluation_failure** — output quality was below threshold
5. **branching_halt** — DAG complexity exceeded limits
6. **unknown_trigger** — fallback

Each trigger generates targeted delta sub-tasks (e.g., mitigations for
premortem failures, fix-items for evaluation issues, DAG simplification for
branching halts).

#### Compensation Ladder

Each replan iteration climbs a rung on the compensation ladder:

| Level | Strategy | Description |
|---|---|---|
| 0 | Reprompt | Re-run the failed sub-task with more specific instructions |
| 1 | Catch fallback | Use a default/fallback output for the failed sub-task |
| 2 | Local compensation | Add a mitigation sub-task adjacent to the failed one |
| 3 | Radius expansion | Also compensate neighbor sub-tasks in the DAG |
| 4 | Global replan | Full plan restructure |
| 5 | Human escalation | Flag for human review |

The ladder advances monotonically: each failed replan iteration bumps the
compensation level by 1 (capped at 5).

#### Degradation Detection

If two *consecutive* evaluations both report `degrading = True`, the REPLAN
node immediately escalates to compensation level 5 (human escalation) —
regardless of the current ladder position. This catches the case where the
plan is actively getting *worse* with each iteration.

#### Delta Validation (3-Check)

Before a FRAGO delta is applied, it passes three validation checks:

1. **Structural consistency** — DFS cycle detection on the combined
   (original + delta) DAG; all dependency references must resolve to
   existing sub-task IDs (broken refs are auto-fixed).
2. **Branching factor** — applying the delta must not push branching_factor
   ≥ 1.0 or depth > max_dag_depth.
3. **Risk delta** — every changed sub-task must carry a non-null risk_level.

#### Routing After Replan

- `max_iterations_reached` → END (force output with current results)
- FRAGO path (replan_count > 0) → RESEARCH (cache-only re-query;
  skips backbrief, premortem, branching, and approval gates on the re-route)
- First-time fallback → PLAN

---

## 3. The Graph Topology (Condensed)

```
                          ┌──────────────────────────────────────────────────────────────┐
                          │                                                              │
                          v                                                              │
  CLASSIFY ──FAST──→ EXECUTE ──→ SYNTHESIZE ──→ EVALUATE ──PASS──→ END                  │
      │                      ▲                                          │                │
      │ STANDARD/DEEP        │    replan_count > 0 route                │                │
      v                      └──────────────────────────────────────┐   │                │
      PLAN ──→ BACKBRIEF ──→ RESEARCH ──→ RISK ──→ PREMORTEM ──→    │   │                │
                  │  ↑          │              │                    │   │                │
                  │  │          │ gap found    │ halted             │   │                │
                  │  │          v              v                    │   │                │
                  │  │        END            END                    │   │                │
                  │  │                                              │   │                │
                  │  └── revise ───┐                                │   │                │
                  │                v                                │   │                │
                  │         PLAN (regenerate)                       │   │                │
                  │                                                  │   │                │
                                                                     v   │                │
  BRANCHING ──→ APPROVAL GATE ──APPROVED──→ EXECUTE ──→ ... ──→ EVALUATE │                │
      │              │                           ↑              │   │    │                │
      │ halted       │ REJECTED                  │              │   │    │                │
      v              v                           │              v   v    │                │
      END           REPLAN ──FRAGO──────→ RESEARCH ───...──→ EXECUTE     │                │
                                                     replan_count > 0    │                │
                     ↑                               (skip gates)       │                │
                     └─────────────────── FAIL ──────────────────────────┘                │
                                                                                          │
                     max_iterations_reached → END                                          │
                                                                                          │
                     degradation_streak ≥ 2 → human_escalation                           │
                     ─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Key Design Properties

### 4.1 Conservative Escalation

Every decision point in JORDAN v2 biases toward the safer path:
- Classification choices escalate upward (never down) on uncertainty
- Safety signals force DEEP regardless of other scores
- Risk fusion takes the *max* of RA and PREMORTEM signals
- The compensation ladder advances monotonically (never decreases)
- Degradation detection short-circuits to human escalation

### 4.2 Provenance Transparency

Every risk signal tracks where it came from:
- `risk_provenance` per sub-task: `risk_assessment` | `premortem` | `safety_domain` | `fused`
- The approval briefing exposes which persona flagged which scenario
- FRAGO deltas record the exact trigger and compensation rationale

This ensures that when a human is asked to approve or intervene, they have
a complete audit trail of *why* the pipeline made each decision.

### 4.3 Ceiling Force-Passes

Several nodes have iteration ceilings that force-pass after N cycles:
- BACKBRIEF: 2 revisions max
- PREMORTEM: 2 cycles max (force-pass with advisory if still failing)
- REPLAN: configurable max iterations (default 3)

These prevent infinite loops without silently dropping failures — the ceiling
pass is accompanied by a flag (`backbrief_forced`, `all_personas_failed`,
`max_iterations_reached`) that propagates into the next node's decision logic.

### 4.4 Stale Premortem on FRAGO Paths

The FRAGO replan loop routes `research → risk_assessment → execute`, skipping
premortem, branching, and approval. The risk fusion in APPROVAL GATE detects
this via `replan_count > 0` and marks premortem data as stale — only the
risk assessment signal is used for fusion on FRAGO iterations. This prevents
the pipeline from using risk analysis that examined a different plan.

---

## 5. Configuration Surface

JORDAN v2 is configured via `config/jordan.yaml` (loaded at `Config.default()`):

| Key | Default | Purpose |
|---|---|---|
| `max_replan_iterations` | 3 | Ceiling on FRAGO iterations before force-output |
| `max_dag_depth` | 10 | Max DAG depth before branching monitor halts |
| `max_total_subtasks` | 25 | Max total sub-tasks across all replan iterations |
| `max_concurrent_subtasks` | 5 | Max parallel sub-tasks during execution |
| `deep_always_approval` | True | DEEP path always requires human approval |
| `denylist_config_path` | `denylist.yaml` | Hot-reloadable regex patterns that force DEEP |
| `skill_library_path` | — | Path to skill library cache |
| `denylist_watch_interval` | 5.0s | How often to check denylist file for changes |

---

## 6. Running It

The pipeline is built and invoked via LangGraph:

```python
from jordan.graph import build_pipeline
from jordan.state import PipelineState

graph = build_pipeline()
state = PipelineState(user_query="Write a comprehensive analysis of...")
result = graph.invoke(state)
print(result["final_output"])
```

For streaming with per-node callbacks (used by the CAIT adapter):

```python
async for event in graph.astream_events(
    state,
    config={"configurable": {"thread_id": "conv-123"}},
    version="v2",
):
    if event["event"] == "on_chain_end":
        node_name = event["name"]
        node_output = event["data"].get("output", {})
        # Emit WebSocket event for this node
```

---

## 7. File Map

```
src/jordan/
├── graph.py              # StateGraph topology + conditional edges
├── state.py              # PipelineState + all dataclasses
├── config.py             # Configuration loading
├── metrics.py            # Pipeline metrics collection
├── nodes/
│   ├── classifier.py     # CLASSIFY — query complexity routing
│   ├── planner.py        # PLAN — task decomposition + COA generation
│   ├── backbrief.py      # BACKBRIEF — DAG/DSM structural review
│   ├── research.py       # RESEARCH — cache lookup + gap detection
│   ├── risk.py           # RISK ASSESSMENT — per-subtask risk scoring
│   ├── premortem.py      # PREMORTEM — 5-persona failure analysis
│   ├── branching.py      # BRANCHING MONITOR — DAG complexity governor
│   ├── approval.py       # APPROVAL GATE — risk fusion + briefing + decision
│   ├── executor.py       # EXECUTE — DAG-ordered parallel execution
│   ├── synthesize.py     # SYNTHESIZE — type-aware output assembly
│   ├── evaluate.py       # EVALUATE — 4-result quality assessment
│   └── replanner.py      # REPLAN — FRAGO delta + compensation ladder
├── tools/
│   ├── bootstrap.py      # Tool registry initialization
│   ├── docker_mcp.py     # Docker MCP tool interface
│   ├── mcp.py            # MCP tool abstraction
│   ├── registry.py       # Tool registry
│   ├── sandbox.py        # Sub-task isolation sandbox
│   └── tool_loop.py      # Tool execution loop
├── memory/
│   └── skill_library.py  # Cached research skill library
└── utils/
    └── logging.py        # Structured logging
```
