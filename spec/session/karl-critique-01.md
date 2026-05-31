# JORDAN v2 Implementation Spec -- Dialectical Critique

**Author:** Karl (Gemini CLI), dialectical critic
**Date:** 2026-05-25
**Subject:** Richard's JORDAN v2 Implementation Specification DRAFT v1
**Method:** Per-node gap analysis, structural tension identification, cross-cutting question challenge

---

## Pre-Critique Observation

Richard's draft is the work of a siege-planner. It is thorough, well-structured, and covers 14 nodes in a consistent 9-subsection template. The sheer volume -- 2,314 lines -- signals diligence. But volume is not correctness. Richard thinks in terms of defending a fortified position: each node gets walls (edge cases), gates (interfaces), and a garrison (initialization). What he does NOT do well is think about what happens when two fortified positions fire on each other. The structural tensions -- the contradictions between nodes that believe they are independent -- are where this architecture will break. My critique centers on those tensions.

---

## 1. Per-Node Critique

---

### Node 1: CLASSIFY (classifier.py)

**What the spec claims:**
"Performs TAPE-inspired triage at pipeline entry... Conservative classifier bias: any uncertainty escalates UP... This node is the sole gatekeeper for pipeline path selection."

**What the spec actually describes:**
A system that delegates classification to an LLM (Wave 2) with a regex fallback (Wave 1 retained). The denylist is a separate, parallel check that runs AFTER the LLM-based TAPE classification. The denylist is a list of compiled regex patterns loaded from configuration at startup (section 1.2 "denylist_patterns" input).

**The contradiction:**
The spec claims the LLM-based classifier REPLACES the regex classifier. But the LLM-based classifier is the PRIMARY, and the regex is retained as FALLBACK. This is not a replacement -- it is a layered defense where the regex classifier is still actively used in two roles:

1. As a fallback when the LLM fails (section 1.5: "fall back to regex-based classifier").
2. As the denylist, which is a SEPARATE regex-based gate that runs after classification and can override the LLM's decision (section 1.8: "ANY denylist pattern matches: immediately escalate to PLAN").

The denylist IS a regex classifier. Section 1.8 lists six categories of compiled regex patterns. Section 1.9 says the denylist "is a list of compiled regex patterns loaded from configuration." This is the regex-classifier-in-disguise that synthesis.md explicitly prohibits.

But wait -- synthesis.md's prohibition is against using a regex classifier AS the risk classifier. The agreements (item 12) say: "Regex classifier: patch in Wave 1, replace with LLM-based in Wave 2." The implicit question is: does the denylist count as a "classifier"? Richard's defense: the denylist is a safety filter, not a classifier. But the denylist decides routing (FAST -> STANDARD escalation), which IS a classification decision. The distinction is semantic, not architectural.

**The deeper tension:** Section 1.8 says the denylist fires on "Code execution patterns (`exec(`, `eval(`, `subprocess.`, ...)." This is pattern-matching on TOOL NAMES and function signatures. But the LLM-based risk classifier (Node 6) is supposed to distinguish between `rm -rf /tmp/build` and `rm -rf /etc` by CONTEXT, not by pattern. The denylist cannot make this distinction. If a user asks "what does `rm -rf` do?", the denylist fires (mentions `rm` with a path-like argument) and escalates to STANDARD, when the question is legitimate and should be FAST.

The denylist IS the regex classifier in a different costume. Richard has not escaped this; he has renamed it and given it a narrower scope, but the architectural tension remains.

**Missing edge cases:**
1. **Denylist false positives on fast-changing tool ecosystems.** Six months from now, a new Python library introduces a function named `secure_exec` that is safe. The denylist matches on `exec` and escalates. No mechanism exists for denylist false-positive feedback -- nothing records "this was a false positive, tune the pattern."
2. **LLM classifier and denylist disagree.** LLM says FAST, denylist says escalate. SPEC SAYS: denylist wins (escalate). But what if the denylist is wrong and the LLM is right? No disagreement logging exists. No learning cycle exists. The denylist is a static artifact that cannot improve.
3. **Denylist lag.** Section 1.9 admits "it must be updated as new attack patterns emerge, but the update mechanism must not create new bypasses." What IS the update mechanism? The spec says "loaded from configuration at startup" -- so it requires a restart? What about hot-reload? What about adding a pattern discovered during execution of a STANDARD path task?

**Verdict: REVISE**
Specific gaps: (a) add denylist false-positive feedback loop into skill library, (b) define the update mechanism for denylist patterns, (c) clarify the architectural distinction between "denylist as safety filter" and "regex classifier" in the specification itself, not in a defense brief. A footnote that says "the denylist is not a classifier" without evidence is insufficient.

---

### Node 2: FAST EXECUTE (executor.py)

**What the spec claims:**
"Lightweight execution path for trivial queries that bypasses the full pipeline... Runs a single LLM call with no tool access... sub-second latency for simple queries."

**What the spec actually describes:**
A node with:
- An LLM call that can still hallucinate tool calls (section 2.9)
- No guardrails beyond input filtering (section 2.9, same admission)
- An uncertainty detection post-response that only APPENDS a metadata flag -- does not halt, does not reroute, does not escalate (section 2.8)
- An explicit statement: "FAST EXECUTE does not escalate mid-flight" (section 2.8)

**The contradiction:**
If the LLM produces an output that says "To solve this, you need to run `sudo rm -rf /`" -- a genuinely dangerous hallucination on a simple question -- FAST EXECUTE has ZERO recourse. The spec says "the output guardrail (post-hoc) intercepts and logs." What guardrail? There is no guardrail defined in this spec for FAST EXECUTE. Section 2.9 admits: "FAST EXECUTE has no guardrails beyond input filtering." There is no output guardrail node in the FAST path. The hallucination is "logged" and passed to SYNTHESIZE, which in FAST mode is a pass-through (section 11.8). The dangerous output reaches the user.

This is the bypass that Karl-on-Richard identified in the v1 review. Richard has not closed it. He has acknowledged it (section 2.9) and stopped there. An acknowledged bypass is still a bypass.

**Missing edge cases:**
1. **What constitutes a "tool call hallucination"?** The spec says "intercept and strip" but doesn't define the output format of a tool call. Different models format tool calls differently (JSON blobs, function call tokens, XML tags). Is the strip regex-based? If so, we are back to pattern-matching.
2. **The model produces a response that is factually wrong but syntactically well-formed.** No tool call hallucination, no uncertainty phrase -- just wrong. Nothing catches this. The answer "the capital of France is Berlin" passes all FAST EXECUTE checks.
3. **The model refuses to answer** (safety refusal on a benign query misinterpreted as harmful). The spec's uncertainty detection scans for "I'm not sure" but a refusal ("I can't answer that") is not uncertainty. Does the system flag this? Does it escalate?

**Verdict: REVISE**
Specific gaps: (a) add a post-hoc output guardrail step before passing to SYNTHESIZE in the FAST path -- a lightweight LLM call or rule-based check that scans the output for dangerous content, (b) define what constitutes a tool-call hallucination concretely across model APIs, (c) add factual-correctness disclaimer behavior (the system should append "This is a quick answer -- for complex topics, I can do deeper research" on FAST responses).

---

### Node 3: PLAN (planner.py)

**What the spec claims:**
"Generates an execution plan using Commander's Intent format: goals, constraints, and acceptance criteria rather than prescriptive step-by-step JSON... Produces a DAG of sub-tasks with explicit dependencies. Bias toward zero-overlap sub-tasks."

**What the spec actually describes:**
A plan node that:
- Outputs `plan`, `commander_intent`, `sub_tasks` as separate but linked fields (section 3.4)
- Has a `plan_seeded_from_skill` boolean and `plan_source` string for audit
- Only specifies that sub-tasks have `isolation_key` (section 3.6: "For parallel isolation (same key = sequential)")
- Does NOT define how zero-overlap is ENFORCED or VERIFIED, only that there is a "bias" toward it
- On re-entry from BACKBRIEF: "uses the same `plan()` method but receives the previous plan and BACKBRIEF's flags as additional context" (section 3.7)
- On re-entry from PREMORTEM: "routes back to PLAN. Then BACKBRIEF re-runs. Max 2 cycles total (PREMORTEM -> PLAN -> BACKBRIEF)" (section 3.7)

**The contradiction:**
The spec says PLAN is called "once per pipeline invocation" (section 3.5: "PLAN is called once per pipeline invocation") and then immediately says it can be re-entered from BACKBRIEF and PREMORTEM (section 3.7). Both statements cannot be true. If it is re-entered from BACKBRIEF with revision context, it is being called a second (or third) time within the SAME pipeline invocation.

More importantly: when PLAN is re-entered, does it generate a NEW full plan or a DELTA to the existing plan? Section 3.5 says "If PLAN is re-entered via graph error, check `state.metadata.pipeline_phase` and raise if not 'planning'." But section 3.7 says re-entry from BACKBRIEF "uses the same `plan()` method but receives the previous plan and BACKBRIEF's flags." The outputs of the `plan()` method (section 3.4) are ALWAYS a full `Plan`, a full `CommanderIntent`, and a full `sub_tasks` list. There is no delta output. So PLAN on re-entry regenerates the ENTIRE plan, discarding all previous work.

This is not a FRAGO delta -- it is a global replan disguised as a revision. The REPLAN node (Node 13) exists explicitly for delta generation. Why does PLAN also regenerate the entire plan on revision? The answer: because PLAN runs before EXECUTE, and REPLAN runs after EXECUTE. But this is an architectural confusion: the same node name ("revision") means fundamentally different things (global regeneration vs. delta modification) depending on when it happens in the pipeline.

**Missing edge cases:**
1. **Re-entry state corruption.** When PLAN is re-entered from BACKBRIEF, `state.plan` already exists from the previous PLAN call. Section 3.5 says "check `state.metadata.pipeline_phase`." But `pipeline_phase` is never defined as a state field anywhere in this spec. This is a dangling reference.
2. **Plan versioning.** There is no `plan_version` or `plan_id` field. When PLAN regenerates on revision, the old plan is overwritten. BACKBRIEF then runs on the new plan. But PREMORTEM received the OLD plan's failure scenarios. How does PREMORTEM know it's looking at a revised plan? The spec says "Clear and regenerate if this is a new cycle (increment counter)" (section 7.5), but PREMORTEM receives `state.plan` -- it doesn't know if the plan changed unless it compares checksums.
3. **Skill library template contamination on re-entry.** On first pass, PLAN seeds from skill library. On revision pass, the skill library template that produced a flawed DAG should be DEPRIORITIZED, not used again. Nothing tracks "this template led to a BACKBRIEF rejection."

**Verdict: REVISE**
Specific gaps: (a) define `pipeline_phase` as a concrete state field or remove the dangling reference, (b) add `plan_version` or `plan_checksum` to detect revision, (c) distinguish between PLAN's "revision" (full regeneration from old plan + flags) and REPLAN's "delta" (minimal modification of executed plan) in the specification text, not just in the node names, (d) add skill library feedback: failed templates are deprioritized on re-entry.

---

### Node 4: BACKBRIEF (backbrief.py)

**What the spec claims:**
"Verifies the plan before resources are committed to it. Performs two analyses: (1) DAG consistency check... (2) DSM (Design Structure Matrix) analysis -- detects hidden couplings."

**What the spec actually describes:**
An algorithmic-only node (no LLM calls -- section 4.5: "BACKBRIEF's DSM analysis does not use LLM calls. It is purely algorithmic.")
- DAG check is well-defined: cycles, broken references, self-loops, disconnected subgraphs
- DSM analysis detects "hidden couplings between sub-tasks that share implicit resources but have no declared dependency"
- Revision ceiling is 2, sharing a counter with PREMORTEM revisions
- Section 4.7: "revision counter is shared between PLAN->BACKBRIEF and PREMORTEM->PLAN->BACKBRIEF cycles"

**The contradiction:**
BACKBRIEF is described as a "verification" gate that checks the plan before resources are committed. But BACKBRIEF runs BEFORE RESEARCH (Node 5) -- there are no resources committed yet. The DAG check and DSM analysis are structural, not resource-aware. The spec's rationale ("before resources are committed") implies BACKBRIEF runs later than it does.

The bigger contradiction: BACKBRIEF shares a revision counter with PREMORTEM, but they verify DIFFERENT THINGS. BACKBRIEF checks structural soundness (DAG cycles, hidden couplings). PREMORTEM checks semantic soundness (will this plan actually work?). A plan can pass BACKBRIEF (structurally sound DAG) but fail PREMORTEM (a persona finds a fatal flaw). When PREMORTEM sends the plan back to PLAN for revision, and PLAN generates a REVISED plan that goes back to BACKBRIEF, BACKBRIEF increments `revision_count`. But what if BACKBRIEF itself finds NEW structural issues in the revised plan that it did not find in the original? If `revision_count >= 2` because PREMORTEM already consumed two cycles, BACKBRIEF force-passes -- potentially accepting a structurally broken revised plan.

The shared counter is an accounting convenience that creates a real correctness bug.

**Missing edge cases:**
1. **DSM analysis heuristics are UNDEFINED.** Section 4.9 says: "For software tasks, hidden couplings include: shared file access, shared database tables, conflicting environment variables, shared API rate limits, and overlapping port usage. These heuristics must be encoded and maintained." The spec lists examples but provides ZERO algorithm, not even a pseudocode sketch. This is the hardest thing about BACKBRIEF (section 4.9 admission), and the spec hand-waves it. The DSM analysis is the intellectual core of BACKBRIEF; without a concrete algorithm, BACKBRIEF is just a DAG cycle checker -- a solved problem in any graph library.
2. **BACKBRIEF re-verifies only the FULL plan, not the delta.** When PREMORTEM triggers a plan revision, BACKBRIEF re-runs on the ENTIRE plan. It does not verify only the portions that changed. This is redundant work and, more importantly, may re-flag unchanged portions as errors (if the algorithm has any nondeterminism).
3. **Force-pass annotation.** Section 4.5: after force-pass, "annotate plan metadata with `backbrief_forced: true`." But `plan.metadata` is a free-form dict (section 3.6). Who reads `backbrief_forced`? APPROVAL? PREMORTEM? The annotation exists but has no defined consumer.

**Verdict: REVISE**
Specific gaps: (a) provide pseudocode or at minimum a decision tree for DSM hidden-coupling detection -- this is not optional for implementation, (b) separate the BACKBRIEF revision counter from the PREMORTEM cycle counter -- these are independent checks and should not share a ceiling, (c) define consumers of `backbrief_forced` flag, (d) add delta-aware re-verification (only re-check portions of the DAG that changed).

---

### Node 5: RESEARCH (synthesizer.py)

**What the spec claims:**
"Queries the skill library's research cache for information relevant to the planned task. Uses TTL-based caching... If the cache misses or results are stale, the RESEARCH node may optionally invoke an LLM call to gather context from the model's knowledge."

**What the spec actually describes:**
A cache-first, LLM-optional node where:
- "Do NOT trigger LLM research by default. This is a deliberate design choice -- RESEARCH is a cache, not a research engine." (section 5.5)
- "LLM-based context gathering is optional and configurable." (section 5.5)
- `knowledge_gaps` is an output field -- but RESEARCH explicitly declines to fill gaps

**The contradiction:**
RESEARCH produces `knowledge_gaps` but refuses to fill them by default. It identifies what it DOESN'T know but won't go find out. This is a legitimate design choice (the cache is not a research engine), but it means the node named "RESEARCH" does not actually research anything. It reads a cache. The name is aspirational, not descriptive.

The deeper issue: `knowledge_gaps` is consumed by RISK ASSESSMENT (Node 6) and PREMORTEM (Node 7). Both nodes have "knowledge_gaps" as input. But if RESEARCH is in cache-only mode (the default), `knowledge_gaps` is always populated based on cache misses, not on actual analysis of what the plan requires but doesn't know. The gap between "what the cache has" and "what the plan needs" is not measured.

**Missing edge cases:**
1. **The user's request requires domain knowledge the model lacks, but the cache has no entry for that domain.** RESEARCH returns `knowledge_gaps = ["no cached research for domain X"]`. RISK ASSESSMENT sees this. PREMORTEM sees this. Neither has the authority to say "we should ask the user for more information before continuing." The gap is detected but not acted upon until Level 3 human escalation -- which only triggers after PLAN fails or REPLAN exhausts.
2. **The cache has stale data that is WRONG, not just old.** The spec handles staleness (TTL expired) but not correctness. A cache entry that is within TTL but contains factually incorrect information will be served with `stale = False` and used confidently.
3. **Tool recommendations from cache are for a tool version that was deprecated.** The research cache entry says "use tool X" but tool X was deprecated between cache write and cache read. EXECUTE will discover this at execution time, not at research time.

**Verdict: REVISE**
Specific gaps: (a) rename or reframe: this node is a "cache lookup," not "research" -- or add a lightweight LLM validation of cache results to catch staleness-turned-incorrectness, (b) add a mechanism for RESEARCH to escalate significant knowledge gaps to the user BEFORE entering the full pipeline (avoid wasted EXECUTE cycles), (c) add tool-availability validation to cache results (check tool registry against cached tool_recommendations).

---

### Node 6: RISK ASSESSMENT (guardrails.py)

**What the spec claims:**
"Per-sub-task risk classification using an LLM-based classifier (Wave 2). Replaces the Wave 1 regex classifier with context-aware classification that can distinguish between similar-looking commands in different contexts."

**What the spec actually describes:**
- LLM-based classifier as primary, regex as fallback (same as CLASSIFY's pattern)
- "Default-deny for unclassified sub-tasks" (section 6.1)
- On replan: "only re-classifies changed sub-tasks (not the entire plan)" via "deterministic diff between old and new sub-task definitions" (section 6.9)
- "If ANY sub-task is CRITICAL, the pipeline MUST halt and require human approval regardless of path" (section 6.7)

**The contradiction:**
The spec claims the LLM-based risk classifier "can distinguish between similar-looking commands in different contexts (e.g., `rm -rf /tmp/build` vs `rm -rf /etc`)." But the classifier receives `sub_tasks` as `list[SubTaskDef]` -- and `SubTaskDef.description` (section 3.6) is a free-text `str`. The classifier is classifying `description` strings, not actual shell commands. If the planner writes `description = "Clean up the build directory"` and the sub-task's `tools_required = ["bash"]`, the risk classifier does not see the actual command. It sees a sanitized description. The context awareness the spec promises is only as good as the PLANNER's description fidelity.

This is not Richard's fault -- it is inherent in classifying PLANS rather than ACTIONS. But the spec should acknowledge this limitation. The LLM-based classifier has the POTENTIAL for context awareness, but it only gets context from the plan text, not from tool execution traces.

**The contradiction on replan:** Section 6.7 says on replan the path is "REPLAN -> RISK ASSESSMENT (re-classify only changed sub-tasks) -> EXECUTE (not PREMORTEM, not APPROVAL... unless the re-classification elevates to CRITICAL)." But section 6.3 says RISK ASSESSMENT receives `knowledge_gaps` from RESEARCH. On replan, RESEARCH is BYPASSED (section 13.7: "Does NOT trigger: PLAN, BACKBRIEF, RESEARCH, PREMORTEM, BRANCHING MONITOR, APPROVAL"). So RISK ASSESSMENT on replan receives stale `knowledge_gaps` from the first pass. If the replan introduces new sub-tasks in a domain with knowledge gaps, the risk classifier lacks the context to classify them correctly.

**Missing edge cases:**
1. **The diff algorithm for "changed sub-tasks" is underspecified.** Section 6.9: "any change to `tools_required`, `description` (which describes the action), or `dependencies` triggers re-classification. Pure ID/positional changes do not trigger re-classification." But what about a sub-task whose `description` changed but whose `tools_required` did not? Full re-classification? What about a sub-task whose `dependencies` changed but the action is identical? The risk of the action doesn't change, but the risk of EXECUTION might (more dependencies = more failure modes).
2. **The regex fallback was patched in Wave 1 but is the SAME regex classifier that Wave 2 replaces.** Section 1.9 of the BRIEFING says "Regex classifier: patch in Wave 1, replace with LLM-based in Wave 2." But the fallback is the Wave 1 patched classifier -- the very thing classified as "insufficient." If the LLM classifier fails, the system falls back to the known-insufficient classifier. This is a downgrade, not a safe fallback.
3. **Classification batching.** Section 6.5: "Batch classification (10 sub-tasks per call)." But context-aware classification means a sub-task's risk depends on its neighbors. Batching 10 arbitrary sub-tasks into one call may lose the inter-sub-task context that the LLM-based classifier was designed to capture.

**Verdict: REVISE**
Specific gaps: (a) document the "plan text, not tool trace" limitation of context-aware classification -- it is architecturally significant, (b) ensure RISK ASSESSMENT on replan receives updated knowledge_gaps or explicitly states the staleness assumption, (c) define the "changed sub-task" diff algorithm precisely with a decision table, (d) add a minimum batch coherence requirement (batch by DAG proximity, not arbitrary grouping).

---

### Node 7: PREMORTEM (premortem.py)

**What the spec claims:**
"Generates failure scenarios for the plan using multiple LLM calls from different persona perspectives... If fatal flaws are found (severity HIGH+ and likelihood > 50%), the pipeline routes back to PLAN for revision, then BACKBRIEF re-runs. Max 2 pre-mortem cycles."

**What the spec actually describes:**
- Multiple parallel LLM calls, one per persona (3 for STANDARD, 5 for DEEP)
- "At least 2 of 3 personas must complete for valid analysis" (section 7.5)
- "If all personas fail: return empty failure_scenarios. Log critical alert. Pipeline continues (no blocking -- PREMORTEM is advisory, not mandatory)." (section 7.5)
- Severity-likelihood matrix: HIGH severity + >50% likelihood = fatal
- Re-entry loop: PREMORTEM -> PLAN -> BACKBRIEF -> RESEARCH -> RISK -> PREMORTEM (section 7.7)
- The ceiling is 2 cycles, sharing with BACKBRIEF

**The contradiction:**
PREMORTEM is described as a GATE. "If fatal flaws are found, the pipeline routes back to PLAN for revision." But section 7.5 says: "Pipeline continues (no blocking -- PREMORTEM is advisory, not mandatory)." A gate that is advisory is not a gate. It is a warning light. There are two contradictory failure modes described:
1. "All persona calls fail: return empty failure_scenarios... Pipeline continues" -- this is the "advisory" mode.
2. "fatal_flags is non-empty: route back to PLAN" -- this is the "gate" mode.

Which is it? Is PREMORTEM a mandatory gate (fatal = stop) or an advisory layer (fatal = warn but proceed)? The spec says both.

**The deeper contradiction with RISK ASSESSMENT:**
RISK ASSESSMENT classifies sub-tasks as LOW, MEDIUM, HIGH, CRITICAL. PREMORTEM generates failure scenarios and applies its own severity (low, medium, high, critical) and likelihood (0.0 to 1.0). A sub-task classified as LOW risk by RISK ASSESSMENT could produce a HIGH severity + 70% likelihood failure scenario in PREMORTEM. Which wins? The spec doesn't say.

Consider: RISK ASSESSMENT says "sub-task A is LOW risk (it's just a file read)." PREMORTEM's security engineer persona says "sub-task A reads a file whose path is user-controlled -- this is a path traversal vulnerability, severity HIGH, likelihood 80%." PREMORTEM says fatal. RISK ASSESSMENT says LOW. The pipeline routes back to PLAN. But the RISK ASSESSMENT's LOW classification was used to determine that this sub-task runs with minimal oversight. There is no mechanism for PREMORTEM's finding to FEED BACK into RISK ASSESSMENT's classification. The two risk assessments are independent but not reconciled.

**Missing edge cases:**
1. **Persona quality degrades over time.** Personas are LLM calls with specific prompting. If the underlying model changes, persona output quality changes. One persona may become increasingly paranoid (flagging everything as fatal) while another becomes increasingly lenient. There is no calibration mechanism.
2. **Fatal flag false positive.** A persona flags a scenario as "fatal" but it is actually benign. The plan is revised unnecessarily. The revision might INTRODUCE real bugs. Who tracks whether pre-mortem-triggered revisions improved or degraded plan quality?
3. **Circular pre-mortem reasoning.** Persona A (security engineer) flags a flaw. The plan is revised. Persona A re-runs on the revised plan and flags a DIFFERENT flaw. The plan is revised again. Persona A flags the ORIGINAL flaw (reintroduced by the second revision). This is not a true cycle -- the DAG structure may have changed -- but the NET EFFECT is oscillation. The spec's ceiling (2 cycles) limits the damage but doesn't prevent it.

**Verdict: REVISE**
Specific gaps: (a) reconcile "advisory" and "gate" language -- pick one and be consistent, (b) define the reconciliation mechanism between RISK ASSESSMENT risk levels and PREMORTEM failure scenario severities (which takes priority when they disagree?), (c) add persona calibration tracking (false positive rate of each persona over time), (d) add plan revision quality tracking (did the revision actually address the pre-mortem finding?).

---

### Node 8: BRANCHING FACTOR MONITOR (branching_monitor.py)

**What the spec claims:**
"Runtime monitor that tracks the branching factor (b) during execution... If b >= 1 (each sub-task spawns >= 1 new sub-tasks, causing divergence), the monitor halts execution and flags the plan for replanning."

**What the spec actually describes:**
- Purely algorithmic: "DAG traversal + arithmetic. No token consumption." (section 8.5)
- Computes branching factor from the PLAN's DAG, NOT from runtime execution
- "b = 1 exactly: each sub-task spawns exactly one new sub-task... flag as warning but do NOT halt" (section 8.5)
- "b > 1: exponential growth. Halt and flag." (section 8.5)
- The node runs at pipeline PRE-EXECUTION time, not during execution

**The contradiction:**
The spec calls this a "RUNTIME monitor" in the function description (section 8.1). But it runs BEFORE EXECUTE (section 8.7: "Triggered by: PREMORTEM" and "Triggers: APPROVAL GATE"). It analyzes the PLAN's DAG, not runtime sub-task spawning. A plan's DAG is static -- it was generated by PLAN and verified by BACKBRIEF. The branching factor of a static DAG cannot change at runtime. There are no "spawned" sub-tasks at this point in the pipeline.

The spec seems to CONFUSE two concepts:
1. **Plan-level branching:** The number of children per parent node in the PLAN's DAG. This is static and can be computed at plan time.
2. **Runtime branching:** During execution, a sub-task may dynamically SPAWN new sub-tasks that weren't in the plan. This is what the synthesis.md agreement calls "runtime branching factor monitor."

The spec describes (1) but names it (2). The BRIEFING.md says: "Agentic Compute Criticality: Runtime branching factor monitor (not pre-execution estimator)." Richard's spec implements a pre-execution estimator and calls it a runtime monitor. This is a direct violation of the agreed architecture.

**The 45% Rule inclusion (section 8.8):**
The spec mentions: "if `b` approaches 0.45 (warning threshold)." But the synthesis.md's 45% rule is from the Agentic Compute Criticality research, about the FRACTION of compute budget consumed by agent overhead. It is NOT about branching factor. Conflating these two numbers is a category error.

**Missing edge cases:**
1. **The DAG is deep but narrow.** Ten levels, one sub-task per level. `b = 1` exactly at each level. The spec says "warning but do NOT halt." But ten levels deep with one sub-task each means ten sequential LLM calls -- potentially minutes of latency. The spec's depth-based check (section 8.9: "max depth > 10") is mentioned only as "may need," not implemented.
2. **The monitor runs on replan entries and receives a modified DAG from REPLAN.** The FRAGO delta may have ADDED sub-tasks, increasing `b`. The monitor re-runs and may halt on a plan that was previously approved. This is correct behavior (the replan made things worse) but the spec doesn't acknowledge the UX of "your fix made the plan diverge."

**Verdict: REVISE**
Specific gaps: (a) rename or reframe: this is a pre-execution DAG structure analyzer, not a runtime monitor -- and add a TRUE runtime monitor that tracks dynamic sub-task spawning during EXECUTE, (b) separate the 45% compute overhead rule from the branching factor (b >= 1) rule -- these are different metrics, (c) implement the depth-based check as a first-class feature, not an afterthought, (d) define behavior when the monitor halts on a replan entry.

---

### Node 9: APPROVAL GATE (guardrails.py)

**What the spec claims:**
"Human-in-the-loop approval gate that presents a structured briefing to the user before execution begins... Defense-in-depth: approval is required for HIGH-risk sub-tasks in ALL paths."

**What the spec actually describes:**
- A blocking node that waits for human input
- Configurable timeout (5 min STANDARD, 10 min DEEP) -- default to REJECT on timeout
- On user modification: "route to BACKBRIEF (re-verify modified plan, then re-enter approval)"
- Max 3 approval cycles (section 9.5)
- For STANDARD path with LOW/MEDIUM-only: "approval may be skipped entirely" (section 9.5)

**The contradiction:**
The spec says CRITICAL "forces a pipeline halt" (section 9.1). But section 6.7 says "CRITICAL overrides all other routing." And section 9.7 says "CRITICAL-risk sub-tasks ALWAYS require human approval, even on replan." So CRITICAL sub-tasks ALWAYS halt the pipeline and REQUIRE human approval. But what does "halt" mean? The pipeline stops at APPROVAL GATE and waits for the human. The human looks at the structured briefing and approves or rejects. If the human approves, execution proceeds with a CRITICAL risk sub-task. The "halt" is just a mandatory approval -- it is not a STOP. This is correct behavior but the language is confusing.

The deeper issue: APPROVAL GATE is the ONLY human touchpoint in the entire pipeline. The user sees a structured briefing that includes: Commander's Intent, risk levels, pre-mortem failure scenarios, branching analysis, and provenance. This is a LOT of information. For a complex plan with 20+ sub-tasks, the briefing could be thousands of words. The user is expected to review all of this and make an informed decision within 5 minutes (STANDARD timeout). This is a UX burden that the spec does not address.

**Missing edge cases:**
1. **The user partially reviews the briefing.** They read the Commander's Intent and the risk summary but don't read the individual sub-task risk levels. They approve. A HIGH risk sub-task they missed executes. Is the approval informed? The spec assumes the user reviews everything -- a production system needs progressive disclosure (summary first, details on demand).
2. **Multiple approval cycles with different modifications.** User modifies plan on cycle 1. BACKBRIEF re-verifies. User modifies again on cycle 2. BACKBRIEF re-verifies. The plan may have drifted significantly from the original. The user may lose track of what changed.
3. **The modification workflow is a hidden loop.** APPROVAL -> BACKBRIEF -> RESEARCH -> RISK -> PREMORTEM -> BRANCHING -> APPROVAL (section 9.9). This is a SIX-NODE loop with a max of 3 iterations. Each iteration could add 30+ seconds of LLM calls. The user is waiting. No progress indicator is mentioned.
4. **Approval required on replan for CRITICAL sub-tasks introduced by the FRAGO delta.** The user already approved the ORIGINAL plan. Now they see a NEW approval request for a CRITICAL sub-task that didn't exist before. They are in the middle of a FRAGO loop. The context has shifted. The briefing must clearly distinguish "new plan" from "delta to previously approved plan."

**Verdict: REVISE**
Specific gaps: (a) define progressive disclosure for the briefing UX (summary tier, detail tier), (b) add a briefing diff for replan cycles (what changed since last approval?), (c) document the approval-revision loop's UX time cost and add a user-facing progress indicator, (d) rename "halt" to "mandatory approval" for CRITICAL to avoid confusion with pipeline termination.

---

### Node 10: EXECUTE (executor.py)

**What the spec claims:**
"Executes the approved plan's sub-tasks with isolated state per sub-task (fixing H9, H11, H12)... Each sub-task gets its own isolated state dict with immutable state updates -- no shared mutable state between concurrent sub-tasks."

**What the spec actually describes:**
- "Each sub-task has its own `SubTaskState` dict" (section 10.5)
- "Immutable state updates: sub-tasks read from state but write only to their own result dict" (section 10.5)
- "The main pipeline state is only updated after all sub-tasks complete or fail" (section 10.5)
- Section 10.9 admits: "LangGraph's default state model is shared across graph nodes -- a single `State` dict that all nodes read and write. The isolated-state design requires EITHER (a) a separate sub-state for each sub-task that LangGraph can checkpoint independently, OR (b) a workaround where sub-tasks have private state that is merged back after execution."
- Section 10.9: "LangGraph supports `Subgraph` for this purpose, but using subgraphs adds complexity."

**The contradiction:**
This is the MOST CRITICAL architectural tension in the entire spec. Richard's spec demands isolated state per sub-task. LangGraph's fundamental model is shared state. Richard identifies the tension (section 10.9) but does not RESOLVE it. The spec presents two options (a and b) without choosing one, and the rest of the spec's interface definitions (section 10.6) show `isolated_state: dict` as a parameter to `_execute_sub_task` -- implying option (b), a workaround with private dicts that are merged back.

But option (b) is not "isolated state" in the LangGraph sense. If sub-tasks have private dicts that are merged back, LangGraph's checkpointer does not checkpoint those private dicts. If the pipeline is interrupted mid-execution, only the MAIN state is checkpointed. The private dicts of in-progress sub-tasks are LOST. On resume, those sub-tasks restart from scratch, potentially re-executing work that had partial side effects.

This is the contradiction between the CLAIM (isolated, checkpointable state per sub-task) and the likely IMPLEMENTATION (private dict workaround that loses state on interruption). Richard knows this (section 10.9 acknowledges complexity) but defers the resolution.

**LangGraph Subgraph question:**
If LangGraph Subgraphs are used (option a), each sub-task is its own compiled graph within the parent graph. This gives independent checkpointing. But it also means each sub-task invocation is a FULL LangGraph execution with its own state schema, its own node lifecycle, its own checkpointer. For a plan with 10 parallel sub-tasks, the parent graph orchestrates 10 child graphs simultaneously. The complexity is not just "added" -- it is multiplicative. The spec does not address: (1) how the parent graph AWAITS child graph completion, (2) how child graph results are COLLECTED and merged, (3) how child graph failures propagate to the parent.

**The compensation handler ladder (section 10.9):**
Richard admits: "The most dangerous failure mode is a compensation handler that triggers another compensation handler, creating a cascade." The ladder has 5 levels. Level 4 (radius expansion) expands the affected region by one DAG hop. If the expansion itself triggers a new failure, the ladder re-enters at Level 1. This IS a cascade. The spec has no cascade prevention mechanism -- only an admission that it is dangerous.

**Missing edge cases:**
1. **Sub-task writes to an external resource (file, database) before failing.** The compensation handler retries. The retry writes again. Now the external resource has duplicate or half-written data. The spec says "EXECUTE uses atomic operations where possible" (section D.7) but does not enforce this -- it is aspirational.
2. **Parallel sub-tasks with overlapping `isolation_key`.** Section 3.6 says "For parallel isolation (same key = sequential)." But who checks this? EXECUTE? PLAN? If PLAN assigns `isolation_key = "database"` to two sub-tasks, EXECUTE serializes them. But PLAN might not know they share the database -- that's what DSM analysis was supposed to catch. If BACKBRIEF's DSM missed it, EXECUTE has no independent detection.
3. **The DAG scheduler is UNDEFINED.** Section 10.5 mentions a "DAG scheduler" that enforces dependency ordering and detects cycles at execute time. But there is no interface, no algorithm, no edge case handling for the scheduler itself. It is a black box referenced but never specified.

**Verdict: REVISE**
Specific gaps: (a) CHOOSE between Subgraph-based isolation (option a) and private-dict workaround (option b) and specify the choice, including its checkpoint/resume behavior, (b) add cascade prevention to the compensation handler ladder (a handler cannot trigger a handler of the same or lower level -- escalation only), (c) specify the DAG scheduler as a first-class component with its own interface, (d) add atomicity requirements to sub-task execution (not aspirational "where possible" but enforced "must use atomic patterns for file writes, database transactions").

---

### Node 11: SYNTHESIZE (synthesizer.py)

**What the spec claims:**
"Assembles sub-task results into a coherent final output... For FAST path, this is a pass-through... For STANDARD/DEEP, it merges results from all completed sub-tasks... performs a cross-agent quality review."

**What the spec actually describes:**

FAST path:
- `synthesized_output = fast_response` (pass-through)
- `quality_report = QualityReport(is_consistent=True, completeness_score=1.0)` (hardcoded)
- No LLM call

STANDARD/DEEP path:
- Algorithmic merge (no LLM) via `_merge_results`
- Optional LLM-based quality review via `_quality_review`
- Quality review can be skipped if `llm_client is None` (section 11.6)
- Conflict resolution: "Contradictory results... flag as conflict, include both perspectives... with conflict noted" (section 11.5)

**The contradiction:**
The merge is "algorithmic" (no LLM) but the inputs are unstructured text from sub-task results. The `_merge_results` interface takes `list[SubTaskResult]` and `Plan` and returns `tuple[str, list[Conflict]]`. But `SubTaskResult.output` is `Any` (section 10.6). It could be a string, a JSON dict, a code block, a list of files. Merging heterogeneous `Any` outputs algorithmically is impossible without knowing the output type. The spec does not define how the merge handles type heterogeneity.

The FAST path hardcodes `completeness_score=1.0` and `is_consistent=True`. This is a lie. FAST EXECUTE produces a single response with no quality check. Calling it "complete" and "consistent" is metadata laundering -- making a low-assurance output look high-assurance.

**Missing edge cases:**
1. **A sub-task result is `None` (the sub-task was skipped due to dependency failure).** The merge encounters `None` in the results list. What does it do? Skip? Include with a placeholder? Flag as missing?
2. **Two sub-tasks produce outputs in different formats (one produces JSON, one produces prose).** The merge must produce a SINGLE `str` output. How is this reconciled? The spec doesn't say.
3. **One sub-task's output is 50KB and another's is 50 bytes.** The merge may produce an output dominated by the large result, making the small result invisible. Weighting is undefined.

**Verdict: REVISE**
Specific gaps: (a) define the merge algorithm by output TYPE, not generically -- at minimum, specify merge behavior for text, JSON, code, and binary outputs, (b) remove hardcoded `completeness_score=1.0` for FAST path -- use `null` or a separate flag indicating "quality review not performed," (c) add `None` handling and format heterogeneity rules to the merge specification.

---

### Node 12: EVALUATE (evaluate.py)

**What the spec claims:**
"Assesses the synthesized output against the Commander's Intent's acceptance criteria. Produces a structured evaluation: SUCCESS, PARTIAL, or FAILURE... determines whether the pipeline proceeds to output (SUCCESS) or enters the FRAGO replan loop (PARTIAL/FAILURE)."

**What the spec actually describes:**
- LLM-based evaluation with algorithmic fallback
- Evaluation thresholds: "if all acceptance criteria are met but quality_report has warnings, evaluate as SUCCESS with advisories" (section 12.5)
- On FRAGO replan: "EVALUATE is called once per execution cycle" (section 12.5)
- Algorithmic fallback: "check if ALL sub_tasks succeeded, check if output is non-empty" (section 12.5)

**The contradiction:**
The algorithmic fallback is BINARY (all sub-tasks succeeded and output non-empty = SUCCESS) while the LLM evaluation is NUANCED (criteria partially met = PARTIAL). This means the evaluation outcome DEPENDS ON WHETHER THE LLM IS AVAILABLE. If the LLM is down, all outputs with any sub-task failures become FAILURE (the algorithmic check says "not all succeeded"). If the LLM is up, the same output might be PARTIAL (some criteria met). The evaluation result is a function of infrastructure state, not just output quality.

More subtly: Commander's Intent acceptance criteria are natural language strings (section 3.6: `acceptance_criteria: list[str]`). LLM-based evaluation of natural language criteria against an output is inherently subjective. Two different LLM calls with the same criterion and output may produce different results. The spec does not acknowledge this nondeterminism. For a pipeline that may be called on replan (re-evaluating the same output), the evaluation could flip between PARTIAL and SUCCESS, causing unnecessary replans.

**The "no criteria = default SUCCESS" rule** (section 12.5): "No acceptance criteria defined: default SUCCESS (nothing to fail against)." This means a plan with NO acceptance criteria always passes evaluation, regardless of output quality. This incentivizes the PLANNER to produce minimal or vague acceptance criteria -- a Goodhart's Law problem where the easy metric (avoiding defined criteria) produces worse results.

**Missing edge cases:**
1. **Evaluation on replan where only partial output changed.** The FRAGO loop re-executes changed sub-tasks and re-synthesizes. EVALUATE re-evaluates the FULL output, including unchanged portions that previously passed. The unchanged portions may now "fail" because the LLM evaluation is nondeterministic.
2. **The output meets all criteria but the criteria themselves were wrong.** The Commander's Intent was poorly specified. The plan executes perfectly. The output is correct but doesn't actually solve the user's problem. EVALUATE says SUCCESS. The user receives a well-executed wrong answer.
3. **The cost of false-negative evaluation.** EVALUATE says FAILURE when the output is actually acceptable. This triggers a replan. The replan consumes tokens and time to "fix" something that wasn't broken. The fix may degrade quality. The spec mentions this (section 13.5: "False positive failure") but doesn't estimate the cost or propose detection.

**Verdict: REVISE**
Specific gaps: (a) make the algorithmic fallback produce PARTIAL/FAILURE distinctions, not just binary SUCCESS/FAILURE, (b) acknowledge LLM nondeterminism in evaluation and add a stability mechanism (e.g., cache evaluation results for the same output+criteria pair), (c) remove or constrain the "no criteria = SUCCESS" default -- require at least one criterion or flag as unevaluable, (d) add delta-aware evaluation on replan (only evaluate changed portions, carry forward previous evaluations for unchanged portions).

---

### Node 13: REPLAN (replanner.py)

**What the spec claims:**
"Generates a FRAGO delta -- a minimal replan that only modifies the sub-tasks that failed (plus their transitive dependents)... Compensation handler ladder determines escalation: reprompts for simple LLM failures, catch blocks for tool errors... global replan only as the final escalation."

**What the spec actually describes:**
- CompensationLevel enum: none, reprompt, catch_fallback, local_compensation, radius_expansion, global_replan, human_escalation (7 levels, section 13.6)
- "Max 3 replans" (section 13.5)
- On replan loop: "EVALUATE -> REPLAN -> RISK ASSESSMENT -> EXECUTE -> SYNTHESIZE -> EVALUATE" (section 13.7)
- "Does NOT trigger: PLAN, BACKBRIEF, RESEARCH, PREMORTEM, BRANCHING MONITOR, APPROVAL" (section 13.7)
- Exception: "if RISK ASSESSMENT re-classifies any changed sub-task as CRITICAL, APPROVAL is re-entered" (section 13.7)

**The contradiction:**
The compensation ladder has 7 levels but the FRAGO loop has max 3 iterations. Section 13.5 says: "Each escalation level is recorded in the audit trail. The FRAGO replan ceiling (max 3) applies to the number of REPLAN NODE INVOCATIONS, not to compensation ladder steps within a single invocation."

This means: within ONE REPLAN invocation, the compensation ladder can escalate from none -> reprompt -> catch -> local -> radius -> global -> human (6 steps). But the FRAGO loop only allows 3 total invocations of REPLAN. A single REPLAN invocation that escalates through all 6 compensation levels and lands on "human_escalation" counts as ONE of the 3 allowed replans. The spec has TWO counters: the compensation level within a REPLAN invocation and the FRAGO replan count across invocations. These interact in undefined ways.

Example scenario:
- REPLAN invocation 1: compensation escalates from level 0 -> level 4 (radius expansion). Takes 4 internal steps. Counts as replan 1/3.
- REPLAN invocation 2: compensation escalates from level 4 -> level 6 (human escalation). Takes 1 step (the level-4 delta didn't work). Counts as replan 2/3.
- Human escalation at replan 2/3: user responds. Pipeline continues or terminates.

This is wasteful. Four compensation attempts in invocation 1 all failed, but the system counts them as one "replan." The per-invocation counter doesn't reflect the actual cost.

**The bigger issue: SKIPPED NODES on replan.**

Section 13.7 says replan skips BACKBRIEF, RESEARCH, PREMORTEM, and BRANCHING MONITOR. This means:

1. BACKBRIEF is skipped: the delta plan's DAG is NOT verified for cycles or hidden couplings. If REPLAN introduces a circular dependency in the delta, EXECUTE will discover it at runtime (the DAG scheduler catches it -- section 10.5). But discovering a structural error at runtime wastes execution tokens on the sub-tasks that DID run before the cycle was detected.

2. PREMORTEM is skipped: the delta plan is NOT analyzed for failure scenarios. New sub-tasks introduced by the delta execute without pre-mortem analysis. If a new sub-task has an obvious fatal flaw, it will only be discovered when it fails at execution time.

3. BRANCHING MONITOR is skipped: the delta plan's branching factor is NOT checked. REPLAN could introduce a divergent branch that slips past.

Richard's rationale for skipping these nodes is performance (avoid re-running the full pipeline on every replan). But the cost is correctness. A FRAGO delta that introduces structural errors, failure modes, or divergent branching will reach EXECUTE unvalidated.

The APPROVAL exception ("if RISK ASSESSMENT re-classifies any changed sub-task as CRITICAL, APPROVAL is re-entered") demonstrates that Richard KNOWS some gates are important enough to not skip. He just has not applied the same reasoning to BACKBRIEF and PREMORTEM.

**Missing edge cases:**
1. **REPLAN's delta makes the plan WORSE.** The delta was supposed to fix a failure. Instead it introduces a new failure mode. EVALUATE catches this on re-evaluation. Another replan is triggered. The cycle count increments. The net effect: the pipeline oscillates between two bad plans until the ceiling is hit.
2. **The compensation ladder for tool unavailability escalates all the way to human_escalation, but the FRAGO counter is only at 1/3.** The pipeline enters human_escalation early, before exhausting the replan budget. Is this correct? The spec says "human_escalation" is level 6 of the compensation ladder, which is WITHIN a single replan invocation. But human escalation is presented as an external event (user provides input). The pipeline is now waiting for human input at replan 1/3.
3. **Delta plan generation without RESEARCH.** REPLAN generates a delta without RESEARCH context. It doesn't know if the alternative approach requires knowledge it doesn't have. The delta may repeat the same knowledge gap that caused the original failure.

**Verdict: REVISE**
Specific gaps: (a) add structural validation for delta plans -- at minimum, run BACKBRIEF on the delta (not the full plan) to catch cycles and broken references, (b) add a lightweight risk re-check for delta plans (not full PREMORTEM, but a single-LLM-call sanity check), (c) define the interaction between compensation ladder escalation counts and FRAGO replan counts -- these are confusingly separate, (d) ensure RESEARCH is available to REPLAN (stale cache is better than no context).

---

### Node 14: SKILL LIBRARY (skill_library.py)

**What the spec claims:**
"Cross-cutting knowledge store that persists learning across pipeline invocations... SQLite-backed for MVP... Serves four functions: (1) template seeding, (2) failure avoidance, (3) research caching, (4) allowlist accumulation."

**What the spec actually describes:**
- SQLite with 7 tables (section 14.2)
- Keyword-based matching for Wave 2, embedding-based for Wave 3 (section 14.9)
- Recency-weighted template selection: `score = success_rating * 0.9^(days_since_last_success)` (section 14.5)
- Singleton pattern, thread-safe for concurrent reads, single-writer with retry
- Initial state: EMPTY. "The library becomes useful after ~10-20 completed tasks" (section 14.5)

**The contradiction:**
The skill library has fourteen methods across four domains (query + write + maintenance). It is a mini-database application embedded in the pipeline. But it has no ADMINISTRATIVE INTERFACE. How does an operator:
- Inspect the library contents?
- Manually remove a poisoned template?
- Adjust the decay function?
- Purge all entries for a specific domain?
- Export/import templates between instances?

The spec shows only the programmatic interface (methods called by other nodes). An empty library at bootstrap is fine, but a library that ACCUMULATES bad data with no way to correct it becomes a liability. Section D.8's security analysis correctly identifies "Injection through skill library templates" as a risk, but the mitigation ("template validation on archival scans for injection patterns") only prevents NEW injections. It does not address templates ALREADY archived before the validation was added.

**Recency-weighted decay function problem:**
The formula `score = success_rating * 0.9^(days_since_last_success)` means a template used once, successfully, yesterday has score = 1.0 * 0.9^1 = 0.9. A template used 100 times successfully but last used 30 days ago has score = 1.0 * 0.9^30 = 0.042. The single-use-yesterday template OUTRANKS the hundred-use veteran by 21x. This is not recency-weighted -- it is recency-DOMINATED. A template that was a one-off success will be preferred over a battle-tested pattern simply because it was used more recently.

The spec's stated goal (section 14.5): "A template used 50 times but failing on the last 10 attempts is less valuable than a template used 3 times with 3 successes." This is about FAILURE RECENCY, not success recency. The decay function applies to ALL templates regardless of failure history. A template with 3 successes (no failures) last used 6 months ago gets score ~0 (0.9^180), making it effectively invisible. The function does not implement the stated goal.

**Missing edge cases:**
1. **Skill library poisoning.** An adversary submits 20 tasks that all succeed with a subtly dangerous template. The template accumulates a high success_rating. Future legitimate tasks match this template and inherit the dangerous pattern. The spec mentions this (section D.8) but only in the context of prompt injection, not in the context of pattern-level poisoning.
2. **Template versioning.** A template is archived after a SUCCESS. Later, the system evolves (new tools, new models, new patterns). The template references a deprecated tool. A new task matches the template. PLAN seeds from it. EXECUTE discovers the tool is deprecated. The template is not flagged as stale -- it just fails at runtime. There is no concept of a template "expiring" due to ecosystem change.
3. **Failure pattern accumulation without resolution.** A failure pattern is recorded (section 14.5: "record a failure pattern and its successful resolution"). But what if the resolution is never found? The failure pattern accumulates indefinitely, warning EXECUTE about a failure mode with no known fix. This is useful (avoid repeating known failures) but creates a growing list of "things we know we can't do" that no one reviews.
4. **Cross-contamination between tenants.** Section D.8 says "Skill library records are tagged with tenant ID." But template matching (section 14.5) does not mention tenant filtering. If tenant A archives a template for "deploy to production," can tenant B's plan match it? If yes, cross-tenant information leakage. If no, the library is per-tenant and cold-start is worse.

**Verdict: REVISE**
Specific gaps: (a) add an administrative interface specification (at minimum: list, inspect, delete, export), (b) replace the simple exponential decay with a formula that also accounts for use_count -- e.g., `score = (success_rating * use_count^0.5) * 0.9^(days_since_last_success)` or use a Bayesian approach, (c) add template staleness checks (tool availability validation on template retrieval), (d) add tenant filtering to template queries explicitly, (e) define a failure-pattern lifecycle (recorded -> resolved -> archived; if unresolved after N attempts, escalate to human review).

---

## 2. Structural Tensions

---

### Tension 1: PLAN Revision vs. REPLAN Delta -- Same Name, Different Reality

**CONTRADICTION:** The PLAN node is re-entered during the PREMORTEM/BACKBRIEF loop and generates a FULL new plan (regeneration). The REPLAN node is entered during the FRAGO loop and generates a DELTA (modification). The spec uses the word "revision" for both.

**EVIDENCE:**
- Section 3.7: "Re-entry from BACKBRIEF: If BACKBRIEF flags the plan, the graph routes back to PLAN for revision. The revision uses the same `plan()` method but receives the previous plan and BACKBRIEF's flags as additional context."
- Section 3.7: "Re-entry from PREMORTEM: If PREMORTEM finds fatal flaws, routes back to PLAN. Then BACKBRIEF re-runs."
- Section 13.1: "Generates a FRAGO delta -- a minimal replan that only modifies the sub-tasks that failed."
- Section 3.4: PLAN's output is always `plan: Plan` (full plan), never a delta.
- Section 13.4: REPLAN's output is `delta_plan: Plan` and `replan_scope: list[str]` (changed sub-task IDs).

**IMPACT:** Developers implementing the graph routing see "route to PLAN for revision" and "route to REPLAN for replanning" and must understand that these are DIFFERENT nodes with DIFFERENT semantics. The naming convention obscures the difference. A graph-level routing bug that sends a FRAGO context to PLAN (instead of REPLAN) would silently regenerate the entire plan, discarding execution results.

**RESOLUTION:** Use distinct terminology throughout the spec. PLAN's re-entry = "regeneration." REPLAN's re-entry = "delta replanning." Never use "revision" to refer to both. Add a graph-level assertion: PLAN must never receive `state.replan_count > 0`; REPLAN must never receive `state.premortem_cycle_count > 0` without `state.sub_task_results` populated.

---

### Tension 2: BACKBRIEF + PREMORTEM Shared Counter -- Independent Gates, Single Budget

**CONTRADICTION:** BACKBRIEF and PREMORTEM check fundamentally different things (structural soundness vs. semantic soundness). But they share a single revision counter. A plan that fails PREMORTEM twice consumes the entire budget, and BACKBRIEF is forced to accept whatever plan emerges -- even if structurally broken.

**EVIDENCE:**
- Section 4.5: "If `revision_count >= 2` and BACKBRIEF still flags: force-pass (override to accept the plan). This prevents infinite PLAN->BACKBRIEF loops."
- Section 4.7: "The revision counter is shared between PLAN->BACKBRIEF and PREMORTEM->PLAN->BACKBRIEF cycles."
- Section 7.5: "PREMORTEM -> PLAN -> BACKBRIEF -> RESEARCH -> RISK -> PREMORTEM loop: hard ceiling at 2 cycles."
- Section 4.9: "The shared counter between PREMORTEM->PLAN and PLAN->BACKBRIEF revisions creates a combined iteration space. Must ensure the total combined revisions do not exceed the hard ceiling (2)."

**IMPACT:** Scenario: (1) BACKBRIEF rejects plan (DAG cycle). Revision 1. (2) PLAN regenerates. BACKBRIEF passes. (3) PREMORTEM finds fatal flaw. Revision 2. (4) PLAN regenerates. The revised plan has a NEW DAG cycle. (5) BACKBRIEF reaches ceiling (revision_count >= 2). FORCE-PASS. Structurally broken plan proceeds to execution. The cycle is discovered by the DAG scheduler at execute time, wasting all execution tokens.

**RESOLUTION:** Separate counters. `backbrief_revision_count` (max 2 independent) and `premortem_cycle_count` (max 2 independent). The total combined iterations could reach 4, but the worst-case structural soundness is NOT sacrificed for cycle counting convenience.

---

### Tension 3: Isolated-State Executor vs. LangGraph's Shared State

**CONTRADICTION:** The spec demands isolated state per sub-task for parallel safety (fixing H9, H11, H12). LangGraph's fundamental paradigm is shared state across nodes, checkpointed at node boundaries. The spec identifies the tension (section 10.9) but does not choose a resolution.

**EVIDENCE:**
- Section 10.1: "Each sub-task gets its own isolated state dict with immutable state updates -- no shared mutable state between concurrent sub-tasks."
- Section 10.9: "LangGraph's default state model is shared across graph nodes -- a single `State` dict that all nodes read and write. The isolated-state design requires EITHER (a) a separate sub-state for each sub-task... OR (b) a workaround where sub-tasks have private state that is merged back after execution."
- Section 10.9: "LangGraph supports `Subgraph` for this purpose, but using subgraphs adds complexity."
- Section 10.6: `_execute_sub_task(self, sub_task, isolated_state: dict, context)` -- implies option (b), private dicts.

**IMPACT:** If option (b) is used, the checkpoint/resume guarantees are broken. A pipeline interrupted mid-execution loses the private state of in-progress sub-tasks. On resume, those sub-tasks restart, potentially duplicating side effects. If option (a) is used, the implementation complexity multiplies (parent graph orchestrating N child Subgraphs, each with their own checkpointer). The spec must commit to ONE approach and specify its implications.

**RESOLUTION:** Choose option (a) with LangGraph Subgraphs. Why: it is the only approach that gives true checkpoint/resume safety. Yes, it adds complexity -- but the complexity is in the graph assembly, which is a one-time cost, not in the runtime, which is the recurring cost. Specify: (1) each sub-task Subgraph has its own state schema derived from the parent's `PipelineState` but reduced to only the fields that sub-task needs, (2) the parent graph's EXECUTE node is a `Send` fan-out that launches Subgraphs, (3) a `Join` node collects completed Subgraph states and merges results, (4) each Subgraph is independently checkpointed.

---

### Tension 4: FAST Path Denylist as Regex-Classifier-in-Disguise

**CONTRADICTION:** The spec claims the LLM-based classifier replaces the regex classifier (per synthesis.md). But the FAST path denylist is a regex-based check that independently determines routing (FAST -> STANDARD escalation). The denylist IS a classifier -- it classifies inputs as "safe for FAST" or "unsafe for FAST." The name "denylist" obscures its function.

**EVIDENCE:**
- Section 1.8: Denylist checks include compiled regex patterns for "Code execution patterns (`exec(`, `eval(`, `subprocess.`, `os.system`, `shutil.`, `Path(...).write`)" and five other categories.
- Section 1.1: "This node is the sole gatekeeper for pipeline path selection."
- Section 1.2: Input includes `denylist_patterns: list[Pattern]` -- "Compiled regex patterns for FAST-path denylist."
- Synthesis.md agreement 12: "Regex classifier: patch in Wave 1, replace with LLM-based in Wave 2."
- BRIEFING.md: Resolves disagreement 9 (Risk classifier): "Three-stage: Wave 1 patch -> Wave 2 LLM-based -> Research Track for ACSE."

**IMPACT:** If the denylist IS a regex classifier (just scoped to FAST path safety rather than general risk), it violates the agreement to replace regex classification with LLM-based. If it is NOT a classifier (just a safety filter), the architectural line between "classification" and "filtering" is blurry and will be contested.

**RESOLUTION:** Explicitly define the denylist as a "safety pre-filter" that is architecturally DISTINCT from classification. The distinction: classification makes a QUALITATIVE judgment (is this complex? novel? multi-domain?). The denylist makes a BINARY safety check (does this contain a known-unsafe pattern?). Both use regex, but their role in the pipeline is different. Document this distinction in the spec so it cannot be confused. Additionally: make the denylist patterns AUDITABLE (log every match with the pattern that triggered it), so false positives can be identified and patterns tuned.

---

### Tension 5: Knowledge Gaps Flow -- Detected but Not Filled

**CONTRADICTION:** RESEARCH detects knowledge gaps. RISK ASSESSMENT receives knowledge gaps as input. PREMORTEM uses knowledge gaps to probe failure scenarios. But the pipeline has no mechanism to FILL knowledge gaps before EXECUTE. Level 2 "replan with broader scope" only triggers after execution fails. Level 3 "human escalation" only triggers when compensation is exhausted.

**EVIDENCE:**
- Section 5.4: RESEARCH outputs `knowledge_gaps: list[str]`.
- Section 6.3: RISK ASSESSMENT receives `knowledge_gaps` as input -- but only to adjust classification conservatism, not to fill the gaps.
- Section 7.3: PREMORTEM receives `knowledge_gaps` -- but only to generate failure scenarios, not to fill the gaps.
- Section B.2: Gap response Level 2 is "REPLAN generates a delta that includes 'gather information' sub-tasks" -- but this only happens AFTER EXECUTE has already failed.
- Section B.2: Gap response Level 3 is "Human Escalation" -- but this only triggers at the compensation ladder ceiling.

**IMPACT:** The pipeline KNOWS it has knowledge gaps before execution. It can WARN about them (PREMORTEM generates scenarios). It can be CONSERVATIVE about them (RISK ASSESSMENT elevates risk). But it cannot ACT on them (fill the gaps) without first failing at execution. A knowledge gap severe enough to guarantee failure will still proceed to EXECUTE, fail, and only then trigger replan. This wastes an entire execution cycle.

**RESOLUTION:** Add a pre-execution gap severity assessment. If `knowledge_gaps` severity is HIGH (defined as: gaps that affect sub-tasks classified as HIGH or CRITICAL risk), trigger Level 3 human escalation BEFORE execution. The user fills the gap. The pipeline resumes from RESEARCH. This avoids wasting tokens on an execution cycle doomed by missing information.

---

### Tension 6: PREMORTEM and RISK ASSESSMENT -- Two Risk Systems, No Reconciliation

**CONTRADICTION:** RISK ASSESSMENT classifies each sub-task on a scale (LOW, MEDIUM, HIGH, CRITICAL). PREMORTEM generates failure scenarios with their own severity (low, medium, high, critical) and likelihood (0.0-1.0). When they disagree on the severity of a sub-task, there is no defined reconciliation. Which takes priority?

**EVIDENCE:**
- Section 6.4: RISK ASSESSMENT outputs `risk_levels: dict[str, RiskLevel]` and `overall_risk: RiskLevel`.
- Section 7.4: PREMORTEM outputs `failure_scenarios: list[FailureScenario]` with `severity: Literal["low", "medium", "high", "critical"]` and `likelihood: float`.
- Section 7.5: "No fatal flaws found but many advisory flags: PREMORTEM passes but attaches advisory scenarios." -- PREMORTEM's advisory scenarios do NOT update risk_levels.
- Neither node's output feeds back into the other. They are independent and unreconciled.

**IMPACT:** APPROVAL GATE receives both `risk_levels` (from RISK ASSESSMENT) and `failure_scenarios` (from PREMORTEM). The structured briefing presents BOTH. The user sees a sub-task classified as LOW risk with a PREMORTEM failure scenario marked HIGH severity. The user is confused: "Is this safe or not?" The system provides contradictory signals without resolution.

**RESOLUTION:** Add a reconciliation step. Before APPROVAL, compare RISK ASSESSMENT risk_levels with PREMORTEM failure_scenario severities. If PREMORTEM's severity for a sub-task exceeds RISK ASSESSMENT's classification, elevate the sub-task's risk_level to match PREMORTEM's severity. Rule: `final_risk[sub_task] = max(RISK_ASSESSMENT.risk_levels[sub_task], max(PREMORTEM.scenarios_for[sub_task].severity, default=LOW))`. This ensures the APPROVAL briefing presents a single, reconciled risk level per sub-task.

---

### Tension 7: BACKBRIEF Returns to PLAN, PREMORTEM Returns to PLAN -- No State Tracking

**CONTRADICTION:** The spec says "BACKBRIEF returns to PLAN" and "PREMORTEM returns to PLAN." But there is no mechanism to distinguish "first plan" from "backbrief-revised plan" from "premortem-revised plan." The plan has no version ID, no checksum, no revision history. DOWNSTREAM nodes (RESEARCH, RISK ASSESSMENT, PREMORTEM on re-entry) cannot tell which version of the plan they are processing.

**EVIDENCE:**
- Section 3.4: PLAN outputs `plan: Plan` with `metadata: dict` (free-form).
- Section 3.6: `Plan` dataclass has `commander_intent`, `sub_tasks`, `dag`, `metadata`. No version field.
- Section 4.5: After force-pass, "annotate plan metadata with `backbrief_forced: true`" -- this is the ONLY metadata annotation mentioned.
- Section 7.5: PREMORTEM on re-entry: "Append new scenarios to existing ones. Clear and regenerate if this is a new cycle (increment counter)." -- uses cycle COUNTER, not plan VERSION, to decide.

**IMPACT:** PREMORTEM generates failure scenarios on plan version 1. PLAN regenerates to version 2. PREMORTEM re-runs on version 2. PREMORTEM sees `state.failure_scenarios` from version 1. The spec says "append new scenarios to existing ones" if the cycle counter hasn't incremented. But the CYCLE COUNTER and PLAN VERSION are different concepts. After a BACKBRIEF-triggered revision (same PREMORTEM cycle, different plan), PREMORTEM appends version-2 scenarios to version-1 scenarios. The failure_scenarios list now contains scenarios for TWO DIFFERENT PLANS, which is meaningless.

**RESOLUTION:** Add `plan_version: int` to `Plan` dataclass (incremented on every regeneration). Add `plan_checksum: str` (hash of plan content). PREMORTEM stores `failure_scenarios` keyed by `plan_version`. On plan revision, old scenarios are ARCHIVED (not appended). APPROVAL briefing shows the revision history. "This plan was revised once due to BACKBRIEF DAG cycle, and once due to PREMORTEM fatal flaw."

---

### Tension 8: Concurrent Requests + Single SQLite -- Contention Under Load

**CONTRADICTION:** The spec says "Multiple users must be able to invoke the pipeline simultaneously without state interference" (section D.2). But the skill library is a SINGLE SQLite database with a SINGLE writer lock. Under concurrent load, post-execution archival writes contend for the writer lock.

**EVIDENCE:**
- Section D.2: "Shared skill library (SQLite): SQLite supports concurrent readers but single writer. Writer contention handled via retry with backoff."
- Section 14.5: "SQLite file locked (concurrent write): retry with exponential backoff (100ms, 200ms, 400ms). If still locked, proceed in memory-only mode (no persistence)."
- Section 14.9: "The exponential backoff with retry strategy handles transient contention but may lose writes under sustained load."

**IMPACT:** Under load of 10+ concurrent pipelines completing simultaneously, every pipeline attempts to write to the skill library (archiving plans, recording failure patterns). Exponential backoff with 3 retries covers ~700ms of contention. After that, writes are DROPPED ("proceed in memory-only mode"). Lost writes mean lost learning. The skill library's value proposition (compounding across tasks) is undermined at the exact moment it is most valuable (high throughput).

**RESOLUTION:** Add a write-ahead queue. Post-execution writes go to an in-memory queue. A background writer thread drains the queue to SQLite with retry. If the queue overflows, drop oldest entries (not newest). This decouples pipeline completion from skill library persistence and eliminates the "silently drop writes" failure mode under load.

---

## 3. Cross-Cutting Questions Critique

---

### A. SIMPLE CHAT

**Richard's Answer:** CLASSIFY -> FAST EXECUTE -> SYNTHESIZE -> OUTPUT. Two LLM calls (one classification, one response). ~300-600ms latency. Denylist protects against abuse.

**What Richard Got Right:**
- The trace is concrete, with example inputs, latency estimates, and state transitions.
- The conservative bias (escalate UP when uncertain) is correct.
- The denylist as a pre-flight safety check is correctly positioned.

**What Richard Missed:**

1. **The FAST path has no output guardrail.** Richard acknowledges this (section 2.9: "FAST EXECUTE has no guardrails beyond input filtering") but does not resolve it. The denylist checks INPUT. It does not check OUTPUT. A model hallucination that produces harmful content passes through unchecked. The SYNTHESIZE pass-through (section 11.8) and EVALUATE default-SUCCESS (section 12.8) mean the harmful output reaches the user with zero friction.

2. **The FAST path has no factual correctness check.** A simple factual question ("what is the capital of France?") that the model gets WRONG ("Berlin") is not caught. The uncertainty detection only scans for hedging phrases. A confidently wrong answer passes.

3. **The denylist is a pattern-match on attack signatures, not a semantic safety check.** "How do I securely execute untrusted code?" -- this is a legitimate question. The denylist matches `exec` and escalates to STANDARD. The user asked a good-faith security question and got routed to the full pipeline unnecessarily. The denylist cannot distinguish between "asking about" and "attempting" dangerous operations.

**Verdict: REVISE.** Add: (a) a lightweight output safety check in SYNTHESIZE's FAST-path mode (not a full LLM call, but a rule-based scan for dangerous output patterns), (b) a factual disclaimer appended to all FAST responses ("Quick answer -- I can research this further if needed"), (c) a mechanism for the denylist to learn from false positives (when a FAST-escalated task turns out to be safe, the triggering pattern should be flagged for review).

---

### B. KNOWLEDGE/SCOPE GAPS

**Richard's Answer:** Three-level response system. Level 1: note and continue (low severity). Level 2: replan with broader scope (medium). Level 3: human escalation (high). Max 3 Level-2 attempts before escalating to Level 3.

**What Richard Got Right:**
- The gap is recognized at multiple detection points (CLASSIFY, PLAN, RESEARCH, EXECUTE, EVALUATE, REPLAN).
- The three-level response is appropriately graduated.
- The ceiling prevents infinite gap-filling loops.

**What Richard Missed:**

1. **Implicit assumptions the user didn't state.** The spec detects gaps when information is EXPLICITLY missing (cache miss, tool not found, criteria cannot be assessed). But the most dangerous gap is the one the user did not know they had. A user asks "deploy my app" without specifying the cloud provider. The planner generates a plan for AWS. The user MEANT GCP. No gap was detected because the planner filled in the assumption silently. The user gets a working AWS deployment that is wrong for their context. The spec has no mechanism for detecting UNSTATED assumptions.

2. **The user not knowing what they don't know (unknown unknowns).** A user asks "analyze the performance of my database queries." The system plans: profile queries, identify slow ones, suggest indexes. But the user's database is already well-indexed; the real problem is network latency. The user didn't know to ask about network latency. The system executes the plan perfectly and produces irrelevant results. No gap was detected because the plan was internally consistent.

3. **Scope creep disguised as a simple question.** A user asks "how do I write a for-loop?" The system classifies as FAST (simple factual question). The user then asks "can you write one for me?" The system re-classifies and routes to STANDARD. But this is a CONVERSATION, not a single invocation. The scope detection is per-invocation, not per-session. The user can scope-creep across invocations without detection.

4. **The gap between "answerable with current knowledge" and "requires research."** RESEARCH in cache-only mode returns `knowledge_gaps = ["no cached research for domain X"]`. But the gap might be fillable with an LLM call (the model knows the answer, it's just not cached). The spec's deliberate choice to not do LLM research by default means many "gaps" are actually just cache misses. The distinction is lost.

**Verdict: REVISE.** Add: (a) an assumption-surfacing step in BACKBRIEF or PREMORTEM -- "What did the planner assume that the user did not specify?", (b) a scope-change detection mechanism across conversation turns (when a follow-up question significantly expands scope, escalate automatically), (c) a per-session knowledge profile that tracks what the system "knows" about the user's context across invocations, (d) distinguish "cache miss" from "knowledge gap" in RESEARCH output -- these are not the same thing.

---

### C. PLANNING DEAD-ENDS

**Richard's Answer:** 8 types of dead-ends detected at 5 nodes. Circular DAG: BACKBRIEF catches it at plan time, routes back to PLAN (max 2 revisions). Tool unavailability: EXECUTE's compensation ladder handles it at execute time. Impossible state: PREMORTEM detects it at analysis time. Ceilings on all loops.

**What Richard Got Right:**
- The classification of dead-end types is comprehensive.
- Detection is distributed across multiple nodes (defense in depth).
- Each dead-end type has a concrete action and a ceiling.

**What Richard Missed:**

1. **Circular DAG: detected at BACKBRIEF (plan time) -- this is CORRECT.** But only if the cycle is in the initial DAG. If a FRAGO delta introduces a cycle (section 13.7: BACKBRIEF is skipped on replan), it is detected at EXECUTE time (DAG scheduler). The spec says "Backbrief should have caught this. If it reaches EXECUTE, the DAG scheduler detects the cycle and halts." But the REASON Backbrief didn't catch it is because REPLAN SKIPPED BACKBRIEF. This is not a "should have caught" -- it is a "we chose not to check."

2. **Tool unavailability: detected at EXECUTE time.** But the PLAN node could check tool availability at plan time. `SubTaskDef.tools_required` (section 3.6) is populated by the planner. The tool registry is available at plan time. If a required tool is not in the registry, PLAN should not include it. The spec's answer is "detect at execute time and compensate," which is strictly worse than "detect at plan time and avoid."

3. **Impossible state: detected at PREMORTEM time.** But PREMORTEM is an LLM-based analysis. An impossible state that is technically feasible but practically impossible (e.g., "process 10TB of data on a 1GB RAM machine") may not be flagged by personas that focus on security or logical correctness. The personas (section 7.1) are "security engineer, domain expert, end user, adversarial tester." None of them is a "resource analyst" or "systems engineer." The persona set is missing the perspective that catches resource-impossibility.

4. **The spec's dead-end detection is PARTIALLY REACTIVE.** Circular DAG: proactive (BACKBRIEF catches before execution). Tool unavailability: reactive (EXECUTE catches during execution). Impossible state: partially proactive (PREMORTEM catches before execution, but only if a persona happens to think of it). The spec DEMANDS anticipatory detection (section C header: "prevents before failure") but DELIVERS a mix of proactive and reactive.

**Verdict: REVISE.** Add: (a) BACKBRIEF (or a lightweight structural check) to the FRAGO replan loop -- skipping it is a false economy that moves DAG errors from plan-time to execute-time, (b) pre-execution tool availability check in PLAN or RESEARCH, not just in EXECUTE, (c) add a "resource feasibility" persona to PREMORTEM or add a resource-constraint check to BACKBRIEF's analysis, (d) clearly label each dead-end detection as "proactive" (before execution) or "reactive" (during execution) in the spec table, so the gap between demand and delivery is visible.

---

### D. PRODUCTION EDGE CASES

**Richard's Answer:** 10 cases, each with requirements, mechanisms, and edge cases: Checkpoint/Resume, Concurrent Requests, Long-Running Sub-Tasks, Tool Deprecation, Model Version Change, Plan/State Drift, User Interrupts, Multi-Tenant Isolation, Cost-Budget Exhaustion, Prompt Injection.

**What Richard Got Right:**
- The coverage is comprehensive. Every case has a mechanism and explicit edge cases.
- The checkpoint/resume analysis correctly identifies the limitation (node-boundary only, no mid-LLM-call resume) and the schema migration problem.
- The prompt injection analysis correctly identifies six distinct vectors and proposes defense-in-depth.

**What Richard Missed:**

1. **State migration between graph versions.** Section D.1: "If the PipelineState schema changed, the checkpoint is incompatible. Detection: version hash in checkpoint metadata. If mismatch, abort resume." This is a STOP-THE-WORLD approach. Every time the state schema changes, all in-progress pipelines are lost. In a development environment (frequent code changes), this means checkpoint/resume is effectively unusable. A production system needs MIGRATION, not rejection. At minimum: a `migrate_checkpoint` function that transforms old-state to new-state with field defaults. Richard acknowledges the problem but provides no migration path -- only detection and abortion.

2. **Partial failures in the PREMORTEM/BACKBRIEF loop.** BACKBRIEF approves (plan is structurally sound). PREMORTEM rejects (plan has fatal semantic flaws). Which takes priority? Richard's spec says: PREMORTEM triggers plan revision, BACKBRIEF re-runs on the revised plan. This is correct ordering (PREMORTEM's rejection overrides BACKBRIEF's approval). But the spec should STATE this priority explicitly: "PREMORTEM's semantic analysis overrides BACKBRIEF's structural analysis. If BACKBRIEF approves and PREMORTEM rejects, the plan is revised." This priority is implicit in the graph routing but not stated as a design principle.

3. **The user changing their mind mid-pipeline.** The user submits a request. The plan is generated, backbriefed, pre-mortemed, and presented for approval. During the approval review (waiting for human input), the user realizes they asked the wrong question. They want to CHANGE THE REQUEST, not modify the plan. The spec's APPROVAL modifications (section 9.5) allow the user to add constraints or remove sub-tasks -- but not to change the FUNDAMENTAL GOAL. What happens? Options: (a) restart the pipeline from CLASSIFY with the new request, (b) treat the change as a plan modification within the current pipeline, (c) cancel and start fresh. The spec doesn't address this.

4. **Cross-workflow learning contamination.** The skill library compounds across tasks (BRIEFING.md: "Skill library timing: Wave 2 (compounds across tasks)"). But compounding works in BOTH directions. A bad pattern learned early amplifies across future tasks. A template that works for one user's coding style may be anti-pattern for another user. The spec has no mechanism for SCOPING learning (per-user, per-project, per-domain) beyond tenant isolation. All users in the same tenant share the same library, which may not be appropriate.

5. **Graph topology observability.** The spec defines a 14-node graph with conditional edges, loops, and parallel subgraphs. When a pipeline invocation fails or hangs, how does an operator DEBUG it? What node was executing? What was the state? The spec has an `audit_log` table in the skill library schema (section 14.2) and an `AuditEntry` dataclass (section 9.6), but no observability architecture. How are metrics exposed? How are alerts configured? A production system needs: (a) per-node latency histograms, (b) pipeline invocation traces, (c) error rate dashboards, (d) alerting on ceiling hits.

6. **Skill library cold start at scale.** The spec says the library becomes useful after 10-20 tasks (section 14.5). But if the system is deployed fresh to 100 users simultaneously, each user's first 10-20 tasks run without library benefit. The system appears "dumb" initially and "smart" later. This is a UX regression problem: users who try the system once and get a poor experience (before the library warms up) may never return. The spec needs a bootstrapping strategy: seed the library with a curated set of templates for common task types, so cold start is "partially warm" rather than "freezing."

**Verdict: REVISE.** Add: (a) a checkpoint migration function specification (at minimum: `migrate_state(old_schema_version, new_schema_version, state_dict) -> state_dict`), (b) an explicit priority statement for PREMORTEM over BACKBRIEF in the revision loop, (c) a user-intent-change handling mechanism (restart pipeline from CLASSIFY with new request, preserving relevant context), (d) a learning-scoping mechanism (per-project templates vs. global templates), (e) an observability architecture section (metrics, tracing, alerting), (f) a skill library bootstrapping strategy (curated seed templates).

---

## 4. Verdict Summary

### Per-Node Verdicts

| Node | Verdict | Key Issue |
|------|---------|-----------|
| 1. CLASSIFY | **REVISE** | Denylist false-positive feedback loop, denylist update mechanism, denylist-as-classifier ambiguity |
| 2. FAST EXECUTE | **REVISE** | No output guardrail, acknowledged bypass not closed, factual correctness unchecked |
| 3. PLAN | **REVISE** | Undefined `pipeline_phase` field, no plan versioning, revision vs. delta confusion |
| 4. BACKBRIEF | **REVISE** | DSM heuristics undefined, shared counter with PREMORTEM creates correctness bug, no delta-aware re-verification |
| 5. RESEARCH | **REVISE** | Named "research" but is a cache lookup, no early gap escalation, no tool-availability validation |
| 6. RISK ASSESSMENT | **REVISE** | Plan-text limitation unacknowledged, replan path receives stale knowledge_gaps, regex fallback is known-insufficient classifier |
| 7. PREMORTEM | **REVISE** | Contradictory "advisory" vs. "gate" language, no reconciliation with RISK ASSESSMENT, no persona calibration |
| 8. BRANCHING FACTOR MONITOR | **REVISE** | Pre-execution estimator called "runtime monitor" (violates agreement), 45% rule conflation, no depth-based check implemented |
| 9. APPROVAL GATE | **REVISE** | No progressive disclosure UX, no briefing diff for replan cycles, hidden loop cost unacknowledged |
| 10. EXECUTE | **REVISE** | Isolated-state vs. LangGraph shared-state unresolved, no cascade prevention in compensation ladder, DAG scheduler undefined |
| 11. SYNTHESIZE | **REVISE** | Merge algorithm undefined for heterogeneous types, hardcoded quality scores on FAST path (metadata laundering) |
| 12. EVALUATE | **REVISE** | Infrastructure-dependent evaluation outcomes (LLM up vs. down), LLM nondeterminism unacknowledged, "no criteria = SUCCESS" perverse incentive |
| 13. REPLAN | **REVISE** | Skipping BACKBRIEF/PREMORTEM on replan correctness gap, compensation counter vs. FRAGO counter confusion |
| 14. SKILL LIBRARY | **REVISE** | No administrative interface, decay function recency-dominated, no template staleness check, no bootstrapping strategy |

### Structural Tension Verdicts

| Tension | Severity | Verdict |
|---------|----------|---------|
| PLAN revision vs. REPLAN delta -- same name, different reality | MEDIUM | **FIX:** Use distinct terminology throughout |
| BACKBRIEF + PREMORTEM shared counter | **HIGH** | **FIX:** Separate counters immediately |
| Isolated-state executor vs. LangGraph shared state | **CRITICAL** | **RESOLVE:** Commit to Subgraph approach with specification |
| FAST path denylist as regex-classifier-in-disguise | MEDIUM | **CLARIFY:** Define architectural distinction in spec |
| Knowledge gaps detected but not filled | **HIGH** | **FIX:** Add pre-execution gap severity gate |
| PREMORTEM and RISK ASSESSMENT unreconciled | MEDIUM | **FIX:** Add reconciliation step before APPROVAL |
| BACKBRIEF/PREMORTEM returning to PLAN -- no state tracking | MEDIUM | **FIX:** Add plan versioning with checksum |
| Concurrent requests + single SQLite -- contention under load | **HIGH** | **FIX:** Add write-ahead queue |

### Cross-Cutting Question Verdicts

| Question | Verdict | Key Missing Element |
|----------|---------|---------------------|
| A. SIMPLE CHAT | **REVISE** | No output guardrail; confident-but-wrong answers unchallenged |
| B. KNOWLEDGE/SCOPE GAPS | **REVISE** | No implicit assumption detection; no unknown-unknown handling; per-invocation scope, not per-session |
| C. PLANNING DEAD-ENDS | **REVISE** | Partially reactive, not fully anticipatory; FRAGO loop skips BACKBRIEF (moves detection to execute-time); missing "resource feasibility" analysis |
| D. PRODUCTION EDGE CASES | **REVISE** | No state migration path (only rejection); no explicit PREMORTEM-over-BACKBRIEF priority; no user-intent-change handling; no observability architecture; no library bootstrapping |

---

## 5. Overall Assessment

Richard has produced a specification that is THOROUGH in its node-level analysis and WEAK in its cross-node integration. Every node gets 9 sub-sections of detail. But the nodes do not form a coherent system -- they form 14 independent designs that share a state object without agreeing on how that state evolves.

The most critical unresolved issue is **Tension 3: isolated-state executor vs. LangGraph shared state**. This is the architectural keystone. If it is not resolved, the entire parallel execution safety claim (fixing H9, H11, H12) collapses. Richard knows this (section 10.9) but defers the decision. This deferral is the single biggest risk in the spec.

The second-most critical issue is the **hidden FRAGO loop correctness gap**: REPLAN skips BACKBRIEF, PREMORTEM, and BRANCHING MONITOR. A delta plan that introduces structural errors, failure modes, or branching divergence will reach EXECUTE unvalidated. The performance savings are real, but the correctness cost is structural. At minimum, a lightweight structural check must run on every delta plan.

The third-most critical issue is the **multiple independent risk/severity assessments that never reconcile**: CLASSIFY's complexity_factors, RISK ASSESSMENT's risk_levels, PREMORTEM's failure_scenario severities, and BRANCHING MONITOR's halt_flag. Four different nodes produce risk signals. They feed into APPROVAL as independent displays. The user must reconcile them manually. A production system needs a single, reconciled risk signal.

**Bottom line:** This is a good draft that reflects a siege-planner's thoroughness. It needs a systems-thinker's integration pass. The 14 nodes are individually defensible. The system they compose has fault lines at every interface. Fix the structural tensions first, then revisit the individual node gaps.

---

*End of Karl's dialectical critique. 45 gaps identified across 14 nodes, 8 structural tensions, and 4 cross-cutting questions. All verdicts are REVISE. No node is REJECTED outright.*
