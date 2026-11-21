# JORDAN v2 Spec Collaboration — Shared Briefing

## Context

You are Richard (Claude Code, crusader-king tactician) or Karl (Gemini CLI, dialectical critic). You have both produced independent reviews of the JORDAN v1 agentic workflow system based on a 61-framework research corpus. Iain M. Banks has synthesized your findings into a unified plan (see `synthesis.md` at the project root). Now you must **collaborate** — draft, critique, revise — to produce three deliverable documents.

## The Agreed Architecture (LAW — Do Not Re-litigate)

### v2 Topology

```
CLASSIFY → PLAN → BACKBRIEF → RESEARCH → RISK → PREMORTEM → BRANCHING FACTOR MONITOR → APPROVAL → EXECUTE → SYNTHESIZE → EVALUATE → REPLAN (FRAGO)
```

### Three Pipeline Paths

| Path | Trigger | Nodes Active | Human Touchpoints |
|:--|:--|:--|:--|
| **FAST** | Trivial queries (facts, simple Q&A, single-step) | CLASSIFY → FAST EXECUTE → SYNTHESIZE | None (unless denylist triggers) |
| **STANDARD** | Multi-step, moderate complexity | Full pipeline, single COA, parallel default | Approval gate on HIGH risk; backbrief/pre-mortem silent |
| **DEEP** | Complex/novel/safety-critical | Full pipeline + multi-COA, MAKER decomposition, sequential default | Approval gate; pre-mortem escalation; backbrief flags |

### Three Waves

| Wave | What Ships | Lines | Est. Time |
|:--|:--|:--|:--|
| **Wave 1** | Security fixes: C1, CR1, H4, CRT1, C2, C3, HR1, remove confidence float, model router fixes, benchmark baselines | ~150 | 1-2 weeks |
| **Wave 2** | Monolith split, FRAGO replanning, pre-mortem, backbrief + DSM, TAPE triage, LLM-based risk classifier, skill library, isolated-state parallel executor, branching factor monitor, Commander's Intent format, HITL hardening | ~4,500 | 1-3 months |
| **Wave 3** | Modular planner (contingent), guardrail stack (3-layer), recursive spawning (bounded), cross-workflow learning, Commander's Intent v2.1, red-teaming, NIST RMF | ~7,000 | 3-6 months |

### 15 Unanimous Agreements

1. Fix C1: replan → risk re-check
2. Fix CR1: parallel approval
3. Fix H4: remove planner risk bypass
4. Fix CRT1: separate system/user classification, default-to-MEDIUM
5. Fix C2: graph-level replan ceiling (default 3)
6. Fix C3: resume deduplication
7. FRAGO delta replanning (ALAS-inspired compensation ladder)
8. Pre-mortem gate with persona-based failure generation
9. TAPE complexity triage (CLASSIFY node, 3-path routing)
10. Backbrief verification with DAG consistency check
11. nodes.py monolith split in Wave 2 (before new nodes)
12. Regex classifier: patch in Wave 1, replace with LLM-based in Wave 2
13. Skill library + episodic memory in Wave 2
14. Isolated-state parallel executor redesign in Wave 2
15. Remove unused confidence float, keep risk_level enum

### 5 Status Quo Confirmations (Preserve)

1. Plan-and-Execute separation
2. LangGraph stateful orchestration
3. DAG-based dependency tracking
4. Human-in-the-loop approval for HIGH-risk
5. Multi-model routing with cost awareness

### 5 "Do NOT" Prohibitions

1. Do NOT implement full MDMP 7-step process
2. Do NOT use JTC as execution model
3. Do NOT use OODA loop as primary execution model
4. Do NOT replace LangGraph with LLMCompiler
5. Do NOT implement universal SPRT voting

### 10 Disagreement Resolutions (Settled — Do Not Re-argue)

| Disagreement | Verdict |
|:--|:--|
| Reform vs. Revolution | Deep refit: structural foundations in Wave 2, research in Research Track |
| MAKER applicability | Insight (decompose to smallest unit for critical/verifiable sub-tasks) NOT mechanism (SPRT on every step) |
| MAP applicability | Modular beats monolithic (split into functional modules) NOT MAP's 6 PFC sub-modules |
| ALAS / global replanning | Local first, global as escalation (ALAS's own architecture) |
| Agentic Compute Criticality | Runtime branching factor monitor (not pre-execution estimator) |
| Parallel executor | Isolated-state redesign (not CommandCC zero-overlap, not incremental CR1/CR2 only) |
| Monolith split timing | Wave 2, BEFORE new nodes added |
| Skill library timing | Wave 2 (compounds across tasks) |
| Risk classifier | Three-stage: Wave 1 patch → Wave 2 LLM-based → Research Track for ACSE |
| Scope estimates | Triangulated table with confidence tiers (synthesis.md Section 2.10) |

## The 4 Cross-Cutting Questions the User Requires

1. **SIMPLE CHAT:** How does the pipeline handle trivial queries ("what is 2+2?")?
2. **KNOWLEDGE/SCOPE GAPS:** How does the system detect missing information and ask for it?
3. **PLANNING DEAD-ENDS:** How does the system detect its plan is invalid and refactor?
4. **PRODUCTION EDGE CASES:** What must a production agentic workflow handle (checkpoint/resume, concurrent requests, tool deprecation, user interrupts, etc.)?

## Collaboration Protocol

Each step specifies:
- **Who** drafts or critiques
- **What** they produce
- **Format** requirements
- **Verification** criteria

Output files go to `spec/session/` for intermediate drafts, `spec/` for final deliverables.
