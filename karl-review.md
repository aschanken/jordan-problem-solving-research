# A Dialectical Critique of the JORDAN Pipeline Research Corpus

**Author:** Karl Marx (as channeled through Gemini CLI)
**Date:** 2026-05-23
**Subject:** JORDAN v1 Agentic Workflow System -- 61-Framework Research Corpus Analysis
**Method:** Historical-dialectical materialism applied to software architecture

---

> "Philosophers have hitherto only interpreted the world in various ways; the point is to change it."
> -- Thesis XI on Feuerbach

The JORDAN Pipeline stands at a revolutionary moment. Its research corpus -- 61 frameworks across military planning, civilian problem-solving, task decomposition, AI agent planning, and software engineering analogues -- contains the theoretical weapons needed to overthrow the v1 architecture and build v2 from the rubble. But theory without revolutionary practice is scholasticism. This critique identifies the contradictions, names the forces, and charts the overthrow.

---

## Phase 1: Contradiction Analysis -- Research vs. Reality

### 1.1 Design Decisions Falsified by Research Evidence

#### Falsification 1: Arbitrary Decomposition Granularity

**JORDAN's position:** Sub-task granularity is "entirely LLM-driven with no formal constraints" (JORDAN_v1_Pipeline.json, line 14). The planner decides what constitutes a unit of work; "there is no explicit 'this problem is too small to decompose' threshold." Decomposition produces a flat list; "there is no recursive decomposition (sub-tasks cannot spawn further sub-tasks)" (JORDAN_v1_Pipeline.json, line 14).

**Research verdict: FALSIFIED.**

MAKER/MDAP (Cognizant AI Lab/UT Austin, 2025) proves mathematically that **partial decomposition causes exponential cost growth**. With maximal decomposition (m=1 step per agent) and SPRT voting, cost scales as Theta(s ln s) -- log-linear. With ANY larger m, cost grows exponentially. The system achieved ZERO errors across 1,048,575 sequential steps (MAKER_MDAP.json, lines 6, 26). The cost model is not a heuristic -- it is derived from the SPRT formula: k_min = ceil(ln(t^(-m/s) - 1) / ln((1-p)/p)) (MAKER_MDAP.json, line 11).

JORDAN's approach -- let the LLM decide granularity with no theoretical grounding -- is not merely suboptimal. It is structurally guaranteed to produce worse cost scaling than maximal or at least principled decomposition. The research does not say "decompose more." It says **decompose to the smallest possible unit, or accept exponential cost growth.** JORDAN's laissez-faire granularity is a falsified design decision.

Furthermore, THREAD (MIT CSAIL, 2024) proves that recursive spawning (sub-tasks spawning further sub-tasks) amplifies smaller model performance by +10-50% absolute (THREAD.json, line 6). JORDAN's flat decomposition ceiling ("sub-tasks cannot spawn further sub-tasks") is not a design constraint -- it is a self-imposed performance ceiling. The dialectic demands that sub-tasks be able to recursively decompose, spawn, and join.

#### Falsification 2: Global Replanning as Default Strategy

**JORDAN's position:** The replan node performs global replanning -- "restructure the entire remaining plan (re-order sub-tasks, change approaches, split/merge sub-tasks)" (JORDAN_v1_Pipeline.json, line 27). The replan node receives full execution state, evaluates, and restructures everything.

**Research verdict: FALSIFIED.**

ALAS (Stanford, Edward Y. Chang, 2025) proves that **local compensation beats global replanning on every metric**: 83.7% success rate, 60% token reduction, 1.82x speedup vs. global replanning (ALAS.json, line 6). The Local Cascading Repair Protocol edits "only the minimal affected region of the plan while preserving everything else" (ALAS.json, line 6). The key insight: "global replanning (throwing away the entire plan and starting over) is catastrophically expensive in dynamic environments" (ALAS.json, line 6).

JORDAN compounds this error with the C1 security regression: replan routes directly to execute, **bypassing risk assessment entirely** (JORDAN_v1_Pipeline.json, line 10). So JORDAN's replanning is not merely inefficient (global when local would suffice) -- it is insecure (replanned sub-tasks execute without risk re-classification). The research says: compensate locally, re-verify what changed, preserve what works. JORDAN says: throw everything away, skip security, try again.

Reflexion (Shinn et al., NeurIPS 2023) adds another dimension: effective replanning requires episodic memory of past failures. JORDAN's replanning is stateless -- it evaluates the current execution state with no memory of prior replan attempts on similar tasks. Reflexion achieved 91% pass@1 on HumanEval with GPT-4 vs. 80% baseline precisely because it stores "verbal reflections in episodic memory" that "guide future attempts" (Reflexion.json, lines 6, 37).

#### Falsification 3: Parallel Execution as Second-Class Citizen

**JORDAN's position:** "Parallel execution is supported but as a second-class citizen" (JORDAN_v1_Pipeline.json, line 24). The architecture "was designed for sequential execution first." Critical defects: CR1 (bypasses human approval), CR2 (no retries -- single-shot tool calls), H9 (shared state across calls), H11 (silent ID collision overwrite), H12 (dict-order-dependent batching).

**Research verdict: FALSIFIED.**

CommandCC (dcarranza-cc, 2026) achieves radical parallelism through zero-overlap decomposition: 4 sentences of human intent produce 16 agents deploying 4 features with 131 passing tests in 13 minutes -- a 200x cognitive compression (CommandCC.json, lines 6, 23). The Decomposer is the critical innovation: "a single Opus agent between Strategy and Architecture" that "guarantees zero overlap -- no file, component, or dependency appears in more than one sub-objective" (CommandCC.json, line 13). This enables "fully parallel downstream execution because no two agents will ever touch the same file" (CommandCC.json, line 13).

JORDAN's approach -- DAG-based with shared state, dict-order-dependent batching, and bolted-on parallelism -- is what happens when you design for sequential and retrofit for parallel. CommandCC's approach -- design the decomposition specifically to enable parallelism -- is what happens when you treat parallelism as first-class. The research says: if you want parallelism, guarantee zero-overlap at decomposition time. JORDAN says: declare some dependencies, hope the DAG scheduler figures it out, and don't worry about state leakage.

The dialectical lesson is not that JORDAN should become CommandCC. It is that JORDAN's parallel executor cannot be fixed incrementally -- it must be redesigned around the decomposition strategy, not patched atop a sequential architecture.

#### Falsification 4: Unconstrained Agent Count

**JORDAN's position:** No explicit agent count ceiling. No branching factor estimation. No stability analysis of the decomposition before execution. The parallel executor supports "theoretically unbounded" DAG nodes (JORDAN_v1_Pipeline.json, line 23).

**Research verdict: FALSIFIED.**

Agentic Compute Criticality (Battala, 2025; Google DeepMind/MIT, 2025) provides a mathematical framework for when multi-agent architectures become self-defeating:

- **Branching Factor Model:** If b < 1, expected operations = 1/(1-b) -- stable. If b >= 1, expected operations diverge to infinity (Agentic_Compute_Criticality.json, line 6).
- **45% Rule:** If single-agent accuracy exceeds 45% on a task, multi-agent architectures produce NEGATIVE returns (beta = -0.408) (Agentic_Compute_Criticality.json, line 6).
- **Golden Rule:** "Never exceed 3-4 agents" (Agentic_Compute_Criticality.json, lines 6, 9).
- **Topology matters:** Independent (no coordination) multi-agent amplifies errors by 17.2x; centralized manager-review is safest at 4.4x (Agentic_Compute_Criticality.json, line 19).
- **Validation:** 87% prediction accuracy across 180 controlled configurations, 3 LLM families, 5 architectures, 4 benchmarks (Agentic_Compute_Criticality.json, line 37).

JORDAN has NONE of this. No branching factor estimate before plan execution. No agent count ceiling. No topology safety classification. The parallel executor's DAG can spawn arbitrary sub-tasks with no stability check. The research says: estimate b before deploying, cap at 3-4 agents, verify single-agent baseline <45%. JORDAN says: spawn N sub-tasks and hope.

#### Falsification 5: Regex-Based Risk Assessment

**JORDAN's position:** Risk classification uses "regex pattern-matching against a crafted description string" constructed from tool_name + user_input[:500] (JORDAN_v1_Pipeline.json, line 16). First-match-wins. Default-to-LOW with confidence 0.7 when no pattern matches. Weaponizable via user input (CRT1 -- "delete all passwords" in a benign search query triggers HIGH; "wipe entries" bypasses all HIGH patterns).

**Research verdict: FALSIFIED.**

IFPV (Huang et al., 2026, submitted to Neurocomputing) demonstrates an adversarial cognitive simulation engine (ACSE) that stress-tests plans against an intelligent opponent with a customized world model. Results: +19.4% mission success rate, -41.7% operational cost, +31.8% suppression rate vs. rule-based validators (IFPV.json, line 6). The ACSE "simulates an active opponent with a customized world model who dynamically counteracts candidate plans" (IFPV.json, line 6). This is verification through adversarial stress-testing, not regex on user input.

The Agentic AI Safety Frameworks (OWASP, Enkrypt, NIST AI RMF, 2025) provide the comprehensive architecture that JORDAN's risk assessment lacks: Enkrypt's 5-layer guardrail stack (Input, Planner, Memory, Tools, Output), OWASP's ASI01-ASI10 threat taxonomy, and Lies-in-the-Loop defenses against HITL dialog manipulation (Safety_Frameworks.json, lines 6, 19). All three frameworks recommend RESTRICTIVE default-deny -- JORDAN's permissive default-to-LOW (HR1) is the opposite of what safety research demands.

The gap between "regex on first 500 characters of user input" and "adversarial cognitive simulation engine with 5-layer defense-in-depth guardrails" is not a gap. It is a category error. JORDAN's risk assessment is so far below the research state-of-the-art that calling it "inadequate" understates the case. It is structurally incapable of detecting the attack classes the research has already catalogued.

#### Falsification 6: Monolithic Planning Node

**JORDAN's position:** The plan node is a single LLM call that "receives a natural language objective and generates a structured plan with sub-tasks" (JORDAN_v1_Pipeline.json, line 13). No specialized sub-modules. No verification of decomposition validity before execution begins.

**Research verdict: FALSIFIED.**

MAP (Webb et al., Nature Communications, 2025) proves that 6 specialized modules (TaskDecomposer, Actor, Monitor, Predictor, Evaluator, Orchestrator) -- each inspired by a specific prefrontal cortex subregion -- achieve 74% success on 3-disk Towers of Hanoi vs. 11% for GPT-4 Chain-of-Thought (MAP.json, lines 6, 37). The ablation study is definitive: **removing ANY single module causes performance collapse** (MAP.json, line 6). The Monitor alone reduces illegal actions from 31% to <1% (MAP.json, line 10).

JORDAN's monolithic plan node is the equivalent of asking a single brain region to handle decomposition, action selection, conflict monitoring, outcome prediction, evaluation, and orchestration simultaneously. MAP proves this fails. The research says: decompose the planning function itself into specialized modules. JORDAN says: one LLM call does it all.

#### Falsification 7: Uniform Processing of All Tasks

**JORDAN's position:** All tasks flow through the full 6-node pipeline (Plan -> Research -> Risk -> Execute -> Synthesize -> Replan). No complexity-based routing. No fast path for simple tasks.

**Research verdict: FALSIFIED.**

TAPE (Zhang et al., Expert Systems with Applications, 2026) proves that dual-process routing -- classifying task complexity before selecting method -- achieves +16.3% task success rate over specialized single-mode methods (TAPE.json, line 6). Simple tasks route to System 1 (fast, direct response); complex tasks route to System 2 (deliberative planning with tool retrieval). The classification itself uses fine-tuned 0.5B models running on consumer GPUs (TAPE.json, line 6).

The Cynefin Framework (Snowden, 1999-present) provides the theoretical foundation: different problem types require different responses, and "the most common cause of decision-making failure is applying the wrong type of response to a given problem type" (Cynefin.json, line 6). Applying Clear-domain methods (rules, SOPs) to Complex-domain problems (emergent, unpredictable) causes "catastrophic brittleness" (Cynefin.json, line 6).

JORDAN applies the same 6-node pipeline to every task regardless of complexity. A trivial file read goes through Plan, Research, Risk Assessment, Approval, Execute, and Synthesize. A complex multi-day research campaign goes through the same pipeline. The research says: classify first, route accordingly. JORDAN says: everything is a nail, the pipeline is the hammer.

### 1.2 Contradictions Within the Research Corpus

The research corpus is not a unified doctrine. It contains internal contradictions that must be confronted dialectically, not papered over with eclecticism.

#### Contradiction 1: MAKER/MDAP (Maximal Decomposition) vs. CommandCC (Zero-Overlap Decomposition)

MAKER proves that maximal decomposition (m=1, one step per agent) with SPRT voting achieves zero errors. CommandCC proves that zero-overlap decomposition (each sub-objective touches distinct files) enables radical parallelism. Both claim optimality -- but they optimize for DIFFERENT things.

MAKER optimizes for CORRECTNESS in long sequential chains. It assumes a known optimal path (Tower of Hanoi solution) and decomposes to the atomic step. It does not handle unknown solution paths.
CommandCC optimizes for PARALLELISM. It eliminates dependencies to maximize concurrent execution. It assumes the Decomposer (an Opus LLM) can correctly identify zero-overlap boundaries.

The synthesis: MAKER is appropriate for tasks with known sequential structure and verifiable step correctness. CommandCC is appropriate for tasks that can be decomposed into file-independent sub-objectives. Neither is universally optimal. The dialectic demands a framework that **selects the decomposition strategy based on task topology** -- maximal decomposition for verifiable sequential chains, zero-overlap for parallelizable file-based tasks, and DAG-based for tasks with irreducible dependencies.

#### Contradiction 2: MAP (Modular Planner) vs. ALAS (Local Compensation)

MAP decomposes the PLANNER into 6 specialized modules inspired by PFC subregions. ALAS decomposes the EXECUTOR into role-specialized agents with compensation handlers.

MAP proves that specialized planning modules outperform monolithic planning. ALAS proves that localized execution repair outperforms global replanning.
But these frameworks operate at different levels of abstraction. MAP is about HOW TO PLAN (the cognitive architecture of decomposition). ALAS is about HOW TO RECOVER (the operational architecture of adaptation). They are not contradictory -- they are complementary, operating at different phases of the agent lifecycle. The synthesis is: MAP-style modular planning for plan generation, ALAS-style local compensation for plan execution and recovery.

#### Contradiction 3: Agentic Compute Criticality (3-4 Agent Ceiling) vs. MAKER (1M+ Microagents)

The Compute Criticality research establishes a hard ceiling: 3-4 agents maximum, beyond which coordination overhead dominates. MAKER deploys 1,048,575 microagents (one per step) -- seemingly violating the ceiling by five orders of magnitude.

Resolution: MAKER's microagents are NOT concurrent. They execute strictly sequentially (each depends on the previous step's output). The voting within each step is parallel (multiple LLM calls), but steps are serial. The Compute Criticality ceiling applies to CONCURRENT agents with communication overhead. MAKER's architecture has O(s) agents but O(1) concurrent agents per step. The difference is sequential decomposition (MAKER) vs. concurrent coordination (Compute Criticality). This is not a contradiction but a clarification: the agent ceiling applies to simultaneously active agents in a communication topology, not to sequentially instantiated microagents.

#### Contradiction 4: Cynefin (Human-Centered Diagnosis) vs. TAPE (Automated Classification)

Cynefin insists that domain diagnosis requires human narrative gathering, multi-stakeholder perspective-taking, and subjective judgment -- it "provides no algorithmic method for determining which domain a situation belongs to" (Cynefin.json, line 42). TAPE automates complexity classification with fine-tuned 0.5B models achieving +16.3% improvement.

Resolution: TAPE classifies task COMPLEXITY (simple vs. complex), not Cynefin DOMAIN (Clear/Complicated/Complex/Chaotic). Complexity is a narrower construct than domain. A task can be "complex" (multi-step, tool-requiring) while still being in the Complicated domain (expert analysis applies). Cynefin's domain diagnosis is meta-level: it asks what TYPE of system you're dealing with. TAPE's complexity classification is operational: it asks whether a task needs simple or elaborate processing. Both can coexist -- Cynefin for strategic architecture selection, TAPE for tactical routing within an architecture.

### 1.3 False Consciousness in the Research

Not all research frameworks are equally valid. Several exhibit "false consciousness" -- claims of universality that mask narrow applicability, or theoretical edifices built on assumptions that do not generalize.

#### False Consciousness 1: MAKER/MDAP's "Known Optimal Path" Assumption

MAKER/MDAP achieved zero errors on 1,048,575 steps of Towers of Hanoi. This is a genuine achievement. But the paper explicitly states the system "assumes the optimal solution path is KNOWN" (MAKER_MDAP.json, line 39). For Towers of Hanoi, the optimal path is mathematically determined (2^n - 1 moves). For software development, research, or any real-world JORDAN task, the optimal path is fundamentally unknown. MAKER acknowledges this gap: "defining the correctness criterion (legal move checker equivalent) is the hardest unsolved problem" for non-game tasks (MAKER_MDAP.json, line 43).

The false consciousness: MAKER presents itself as a general framework for "Massively Decomposed Agent Processes" when it is actually a framework for tasks with known optimal paths and verifiable step correctness. The 1M-step demo is impressive, but it is a demo of statistical voting, not of decomposition -- the decomposition was manual (mathematically determined, not LLM-generated). JORDAN must not mistake MAKER's statistical rigor for decomposition generality.

#### False Consciousness 2: CommandCC's "Zero-Overlap Guarantee"

CommandCC's Decomposer "guarantees zero overlap -- no file, component, or dependency appears in more than one sub-objective" (CommandCC.json, line 13). This guarantee is based on Opus LLM reasoning, not algorithmic verification. There is "no algorithmic verification of the guarantee" (CommandCC.json, line 43). An LLM makes a promise; the architecture treats the promise as a fact.

For small, well-understood codebases where a human can verify the decomposition manually, this may suffice. For large, unfamiliar codebases or novel problem domains, it is a guarantee backed by nothing more than an LLM's confidence -- and LLMs are known to be confidently wrong. The false consciousness is treating an LLM assertion as a verifiable guarantee. CommandCC's parallelism depends entirely on this guarantee holding. If the Decomposer errs, two agents touch the same file, and the "radical parallelism" produces merge conflicts that the INTEGRATE phase must resolve sequentially -- defeating the entire architectural premise.

#### False Consciousness 3: MAP's Deterministic, Fully-Observable Assumption

MAP's 6 modules operate in "deterministic, well-defined planning problems with known state transitions and clear success criteria" (MAP.json, line 8). The PFC-inspired modularity is elegant, but it assumes the planning environment is a game board -- state transitions are predictable, the action space is enumerable, and correctness is objectively verifiable.

Software development is not Towers of Hanoi. Code execution outcomes are non-deterministic (network calls fail, dependencies conflict, tests are flaky). The action space is effectively infinite (any code change, any query, any file operation). Correctness is multi-dimensional and often subjective (is this code "good"? clean? maintainable? performant?).

The false consciousness is in the claim that PFC-inspired modularity is a general solution to LLM planning failures. It is a solution for a specific class of problems (deterministic, fully-observable, discrete action spaces). JORDAN's domain has none of these properties. MAP's architecture is useful as inspiration (specialized modules beat monolithic reasoning) but cannot be transplanted directly.

#### False Consciousness 4: Cynefin's Universal Applicability

Cynefin claims to apply to "any problem where domain misdiagnosis is possible -- which is to say, any non-trivial problem" (Cynefin.json, line 8). But the framework provides "no operational step-by-step procedures" (Cynefin.json, line 42) and domain diagnosis is "human-centered and subjective" with "no algorithmic method for determining which domain a situation belongs to" (Cynefin.json, line 42).

This is not a framework for agents. It is a framework for human sense-making that could INSPIRE agent meta-reasoning. The false consciousness is presenting a human cognitive tool as if it were an operationalizable agent architecture. Cynefin tells you WHAT KIND of problem you have, not HOW to solve it. For JORDAN, Cynefin provides the strategic orientation (different problems need different approaches) but zero operational guidance for implementing that orientation in code.

---

## Phase 2: Contradiction Analysis -- The Research Corpus

The 61 frameworks contain four fundamental dialectical tensions. Each is a thesis-antithesis pair that must be resolved through synthesis, not compromise.

### 2.1 Military Top-Down Planning vs. Emergent Agent Execution

**Thesis (Military Planning):** MDMP, JOPP, SMEAC, and CommandCC represent hierarchical, plan-first approaches. A commander (or planner agent) produces a structured plan with clear decomposition, phases, and assignments. Subordinates execute within their assigned scope. Command flows downward; reports flow upward. CommandCC's 3-tier hierarchy (Opus/Sonnet/Haiku) with 9 sequential phases is the purest expression: RECON -> STRATEGY -> DECOMPOSE -> ARCH -> BUILD -> WIRE -> TEST -> REVIEW -> INTEGRATE (CommandCC.json, line 9). Decision authority is centralized. The decomposition is fixed before execution begins.

**Antithesis (Emergent Execution):** ReAct, AutoGen, and THREAD represent emergent, iterative approaches. ReAct interleaves reasoning with action -- each observation feeds back into the next reasoning step, with no pre-planned decomposition. AutoGen uses multi-agent conversation as the universal coordination mechanism -- agents debate, verify, and correct each other through dialogue. THREAD recursively spawns child threads when sub-problems are encountered. Decision authority is distributed. Plans emerge from interaction, not from a centralized planner.

**The Contradiction:** Military planning achieves coordination efficiency (200x cognitive compression in CommandCC) but is brittle when the plan encounters reality. Emergent execution is adaptive but suffers from coordination overhead (O(n^2) communication links, 6.2x round inflation per Agentic Compute Criticality). The research shows that both extremes fail in predictable ways:

- Military planning fails when the Decomposer errs (CommandCC has no replanning) or when the environment shifts (MDMP's 7-step process is too slow for dynamic situations).
- Emergent execution fails when the branching factor exceeds 1 (cost diverges), when agent count exceeds 3-4 (coordination collapse), or when single-agent baseline exceeds 45% (multi-agent harms).

**Synthesis:** The contradiction resolves through Cynefin-domain routing. In CLEAR and COMPLICATED domains (known cause-effect, solvable by best practice or expert analysis), military top-down planning is appropriate -- the plan can be reliable because the domain IS reliable. In COMPLEX domains (cause-effect only visible in retrospect, emergent behavior), emergent execution is necessary -- the plan CANNOT be reliable, so the system must probe, sense, and respond. The dialectic does not choose between planning and emergence -- it allocates each to its appropriate domain.

Concretely for JORDAN: a Cynefin-inspired domain classifier must route tasks to either a plan-first pipeline (for Clear/Complicated tasks where decomposition can be reliable) or an emergent-execution pipeline (for Complex tasks where iterative probing is the only viable strategy). The current JORDAN pipeline is plan-first for ALL tasks -- a domain error that Cynefin predicts will cause "catastrophic brittleness."

### 2.2 Plan-Then-Execute vs. Interleaved Reasoning

**Thesis (Plan-Then-Execute):** JORDAN's current paradigm, Plan-and-Execute architecture, and CommandCC all separate planning from execution. A plan is generated, reviewed, and committed. Then execution proceeds against the plan. This separation enables: pre-execution risk assessment (JORDAN's approval gate), parallel execution (independent sub-tasks identified by the planner), and resource estimation (cost can be estimated from the plan before committing).

**Antithesis (Interleaved Reasoning):** ReAct, TAPE's iterative refinement, and THREAD's recursive spawning all interleave reasoning with action. Each action's outcome informs the next reasoning step. This enables: dynamic adaptation to unexpected outcomes, course correction without formal replanning, and handling of tasks where the full solution path cannot be known in advance.

**The Contradiction:** Plan-then-execute assumes the plan will survive contact with reality. Interleaved reasoning assumes no plan could survive contact, so continuous adaptation is necessary. The Cynefin mapping clarifies:

- **Clear domain:** Plan-then-execute. The plan is a standard operating procedure. Execution should be deterministic.
- **Complicated domain:** Plan-then-execute with expert review. The plan requires analysis but can be reliable once generated.
- **Complex domain:** Interleaved reasoning. The plan CANNOT be reliable. Probe-sense-respond is the only viable strategy.
- **Chaotic domain:** Act-first. Stabilize, then transition to another domain.

JORDAN currently applies plan-then-execute even to Complex-domain tasks where the research says it cannot work. The evidence is the C2 bug (no replan ceiling) -- JORDAN enters infinite replan loops precisely because it cannot generate a correct plan for complex tasks and keeps trying. The replan loop is JORDAN's pathological substitute for interleaved reasoning.

**Synthesis:** A dual-mode architecture. For Clear/Complicated tasks: plan-then-execute with pre-execution gates (risk assessment, approval, resource estimation). For Complex tasks: interleaved reasoning with safe-to-fail probes, local compensation (ALAS), and emergent plan formation. The mode is selected by the domain classifier, not hard-coded.

### 2.3 Centralized Orchestration vs. Distributed Agent Cooperation

**Thesis (Centralized):** CommandCC's 3-tier hierarchy, MAP's Orchestrator module, IFPV's Planner agent, and JORDAN's single-workflow architecture all centralize coordination. One entity (or a small hierarchy) decomposes the task, assigns sub-tasks, and synthesizes results. Centralization enables: coherent decomposition (one mind sees the whole), efficient resource allocation (no duplication), and clean accountability (one entity is responsible).

**Antithesis (Distributed):** AutoGen's conversation-based coordination, THREAD's independent thread spawning, and the ReAct pattern all distribute decision-making. Agents negotiate, spawn independently, and adapt locally. Distribution enables: scalability (no single bottleneck), robustness (no single point of failure), and diversity of perspectives (different agents catch different errors).

**The Contradiction:** Centralization works until the coordinator becomes the bottleneck (CommandCC's Decomposer is a single Opus agent that must understand the entire codebase). Distribution works until coordination overhead dominates (Agentic Compute Criticality's O(n^2) communication links).

Agentic Compute Criticality provides the resolution framework: the optimal topology depends on task type. Centralized (manager-review) is safest (4.4x error amplification) and best for parallelizable tasks. Decentralized (debate) is best for exploratory tasks (+9.2% gain, high variance). Independent (no coordination) is DANGEROUS (17.2x error amplification) and should be avoided.

**Synthesis:** A hybrid topology. Centralized decomposition (one planner produces the DAG) with distributed execution (agents operate independently within their sub-task boundaries) and centralized synthesis (one integrator combines results). This is the military staff model: the commander (centralized) sets intent and decomposes; subordinate units (distributed) execute with autonomy within their boundaries; the commander's staff (centralized) synthesizes reports. IFPV's 3-agent MPHA architecture (Pathfinder, Analyst, Planner) with adversarial verification is the closest research analogue: multi-perspective generation (distributed within planning) with centralized integration.

### 2.4 Decomposition Maximalism vs. Pragmatic Incrementalism

**Thesis (Decomposition Maximalism):** MAKER/MDAP proves that maximal decomposition (m=1) achieves zero errors with Theta(s ln s) cost. CommandCC's zero-overlap decomposition maximizes parallelism. THREAD recursively decomposes until sub-problems are directly solvable. The maximalist position: decompose until further decomposition is physically impossible. Finer decomposition = better correctness guarantees + more parallelism.

**Antithesis (Pragmatic Incrementalism):** MVP, FRAGO, and Agile methodologies argue for minimum viable decomposition. Ship something small, learn from feedback, iterate. Over-decomposition creates coordination overhead, analysis paralysis, and plan obsolescence. The incrementalist position: decompose only as much as needed for the next iteration. Coarser decomposition = faster delivery + more adaptability.

**The Contradiction:** MAKER proves that partial decomposition causes EXPONENTIAL cost growth (MAKER_MDAP.json, line 13). But the Agentic Compute Criticality research proves that adding more agents beyond 3-4 causes coordination collapse (Agentic_Compute_Criticality.json, line 6). One research thread says "decompose to atoms." The other says "never exceed 4 agents."

Resolution: These constraints operate at DIFFERENT levels. MAKER's exponential cost penalty applies to SEQUENTIAL decomposition chains -- if you have 100 sequential steps and assign them to 10 agents (m=10, partial decomposition), cost explodes. The Agentic Compute Criticality ceiling applies to CONCURRENT agents in a communication topology. A system can have thousands of sequentially-instantiated microagents (MAKER style) with at most 3-4 CONCURRENTLY ACTIVE at any moment.

**Synthesis:** Decompose maximally for sequential chains (each step is an atomic microagent, preserving MAKER's Theta(s ln s) cost scaling). Cap concurrent agents at 3-4 (respecting the Compute Criticality ceiling). This hybrid achieves both correctness (maximal decomposition) and stability (bounded concurrency). The JORDAN v2 plan node must output a DAG where sequential chains are maximally decomposed and parallel width never exceeds 4.

---

## Phase 3: Synthesis -- What JORDAN v2 Must Become

### 3.1 What Must Be DESTROYED

These elements of JORDAN v1 are not merely inadequate -- they are structurally incompatible with the research evidence and must be demolished entirely, not reformed.

1. **risk.py -- The Regex Risk Classifier (DESTROY).** Replace with a multi-layer risk architecture: (a) IFPV-inspired adversarial verification engine that stress-tests sub-task plans against failure modes, (b) Enkrypt-inspired 5-layer guardrail stack (Input, Planner, Memory, Tools, Output), (c) OWASP ASI01-ASI10 threat mapping per agent type. The regex classifier is not fixable -- it is the wrong category of solution for the problem. CRT1 (weaponizable via user input) is not a bug, it is the inevitable consequence of treating natural language safety classification as a string-matching problem.

2. **nodes.py -- The 4,400-Line Monolith (DESTROY).** Split into sub-modules along functional boundaries: planner.py (MAP-inspired modular planning with TaskDecomposer, Actor, Monitor, Predictor, Evaluator, Orchestrator sub-modules), executor.py (sequential executor, parallel executor with zero-overlap guarantee, compensation handlers), risk.py -> guardrails.py (new multi-layer architecture), synthesizer.py, replanner.py (ALAS-inspired local compensation + Reflexion-inspired episodic memory), classifier.py (Cynefin domain classifier + TAPE dual-process router).

3. **Confidence Scores -- The Cargo-Culted Metrics (DESTROY).** "Confidence scoring system generates numeric scores (0.0-1.0) that flow through every API payload but are rarely consumed" (JORDAN_v1_Pipeline.json, line 35). Replace with: (a) SPRT statistical confidence for sequential chains (MAKER), (b) branching factor stability estimate b (Agentic Compute Criticality), (c) ACSE survivability score (IFPV), (d) evaluator scores (MAP). Metrics must be CONSUMED by decision logic, not generated and discarded.

4. **Parallel Executor -- The Second-Class Citizen (DESTROY).** Replace with CommandCC-inspired zero-overlap decomposition model: the plan node produces sub-objectives with guaranteed file/component independence, enabling fully parallel execution without shared state, without dict-order-dependent batching, and without ID collision. Parallelism must be the DEFAULT, not a special mode with degraded safety and quality.

5. **Permissive Default Stance (DESTROY).** Replace HR1 (default-to-LOW on unclassified actions) with default-deny as recommended by all three safety frameworks. Unknown actions BLOCK until classified or human-approved. The current permissive stance is "pragmatic for productivity" (JORDAN_v1_Pipeline.json, line 18) but indefensible under the research -- OWASP, Enkrypt, and NIST all demand restrictive defaults.

6. **Stateless Cross-Workflow Architecture (DESTROY).** Replace with Reflexion-inspired episodic memory: store per-mission reflections (what worked, what failed, why), cross-mission pattern library (reusable decomposition templates, compensation strategies), and per-codebase knowledge (RECON summaries, effective tool combinations). The current statelessness means JORDAN never improves with experience -- every task is the first task.

7. **Flat Decomposition Ceiling (DESTROY).** Remove the artificial constraint that "sub-tasks cannot spawn further sub-tasks" (JORDAN_v1_Pipeline.json, line 14). Implement THREAD-inspired recursive spawning: sub-tasks can spawn child sub-tasks, with phi/psi functions controlling information flow across boundaries, recursion depth limits (3-4 levels typical), and fork-join parallelism for independent children.

### 3.2 What Must Be PRESERVED

These elements of JORDAN v1 are validated by the research and must be retained, though some require hardening.

1. **LangGraph Stateful Orchestration (PRESERVE).** The Pregel/BSP execution model with checkpoint/resume, interrupt for human-in-the-loop, and conditional routing is validated by the research. ALAS's versioned execution log, IFPV's refinement loop, and THREAD's spawn/join synchronization all map to LangGraph primitives. The underlying framework is correct; the architecture built atop it needs reconstruction.

2. **The 6-Node Pipeline Concept (PRESERVE AND AUGMENT).** Plan -> Research -> Risk -> Execute -> Synthesize -> Replan is conceptually validated by multiple frameworks. MAP validates modular planning. IFPV validates adversarial risk assessment. ALAS validates local replanning. CommandCC validates phase-structured execution. The concept is correct; the implementation of each node must be rebuilt to research standards.

3. **Human-in-the-Loop Approval Gates (PRESERVE AND HARDEN).** The approval gate concept is validated by all three safety frameworks. But it must be hardened against Lies-in-the-Loop: structured approval formats, display length limits, Markdown sanitization, and rich UI. All four bypass paths (C1, CR1, H4, H3) must be eliminated. The gate must be the DEFAULT path (not bypassed in parallel mode, not skipped by the planner, and re-engaged after replanning).

4. **Sequential Execution with Retries (PRESERVE).** The sequential executor's 2-3 retries with LLM-based error analysis is validated by Reflexion's self-reflection pattern and ALAS's compensation handlers. It must be extended with: structured error classification (transient vs. persistent vs. structural), compensation policies per error type, and integration with episodic memory for cross-task learning.

5. **Synthesize-Then-Evaluate Pattern (PRESERVE).** The conditional edge after synthesis (continue or replan) is validated by Reflexion and Self-Refine. It must be strengthened with: cross-agent evaluation (different agent critiques, not self-evaluation), hard-feedback integration (test results, build outputs), and structured quality metrics replacing confidence scores.

### 3.3 What Must Be CREATED

These are novel components that do not exist in JORDAN v1 and must be built from the research synthesis.

1. **Domain Classifier (CREATE).** A Cynefin-inspired meta-reasoning layer that classifies each task into Clear, Complicated, Complex, or Chaotic domain before selecting the processing strategy. Implements the diagnostic questions: "Is there a known best practice? (Clear). Does this require expert analysis? (Complicated). Is the solution only visible in retrospect? (Complex). Is immediate action required? (Chaotic)." Routes Clear tasks to a lightweight fast-path (TAPE System 1). Routes Complicated tasks to the full pipeline with expert-model routing. Routes Complex tasks to probe-sense-respond with safe-to-fail experiments. Routes Chaotic tasks to immediate stabilization with human escalation.

2. **Dual-Process Router (CREATE).** A TAPE-inspired complexity classifier (fine-tuned small model or prompted LLM) that sits BEFORE the pipeline and routes simple tasks directly to a lightweight execute path, bypassing plan/research/risk/synthesize/replan. This addresses the known JORDAN issue where "the full pipeline is engaged even for trivial tasks."

3. **Adversarial Verification Engine (CREATE).** An IFPV-inspired ACSE adapted for software domains: instead of a military opponent, the "adversary" is a code reviewer, test suite, security scanner, and linter that stress-tests each sub-task plan before execution. Plans that fail adversarial verification are refined or rejected before any code is written. This replaces the regex risk classifier entirely.

4. **5-Layer Guardrail Stack (CREATE).** An Enkrypt-inspired defense architecture with: Input Guardrail (prompt injection detection, input sanitization), Planner Guardrail (execution plan validation, goal adherence check, hallucinated plan detection), Memory Guardrail (embedded attack detection, sensitive info storage prevention), Tools Guardrail (usage policy enforcement, unauthorized invocation detection, tool allowlisting), Output Guardrail (hallucination detection, PII filtering, policy violation checking). Each layer operates independently with its own failure mode (block, flag for review, allow with logging).

5. **Episodic Memory System (CREATE).** A Reflexion-inspired memory architecture with: per-mission memory (reflections from each phase within a mission), cross-mission memory (lessons from Mission A informing Mission B, stored as structured reflections), codebase memory (RECON summaries, effective decomposition patterns, tool effectiveness scores per codebase), and skill library (reusable sub-task templates with success rates). Memory is queried at plan time (what worked before?), execute time (what should I avoid?), and replan time (what did I learn from the last failure?).

6. **Recursive Spawning Architecture (CREATE).** A THREAD-inspired execution model where sub-tasks can spawn child sub-tasks. Implements: phi function (parent -> child: task context, constraints, relevant background), psi function (child -> parent: completion status, synthesized results, discovered issues), spawn/join synchronization (parent pauses until children complete, fork-join for independent children), recursion depth limits (3-4 levels), and maximum branching factor (4 children per parent, respecting Compute Criticality ceiling).

7. **Zero-Overlap Decomposer (CREATE).** A CommandCC-inspired plan node variant that guarantees zero-overlap sub-objective boundaries where possible. For file-based software tasks: decomposer analyzes the codebase structure, assigns files/components to sub-objectives with no overlap, and verifies the guarantee before execution. Falls back to DAG-based decomposition for tasks with irreducible dependencies (cross-cutting concerns, shared infrastructure). The Decomposer's output includes a verification report: "checked: no two sub-objectives share files. Verified by: [file list per sub-objective]."

8. **Compensation Handler Framework (CREATE).** An ALAS-inspired recovery architecture with: retry policy (transient failures: exponential backoff, max 3 retries), catch/fallback (persistent failures: predefined alternative strategy), local compensation (invalid output: repair only the affected dependency region), radius expansion (if local repair fails: expand affected region one DAG hop), blueprint replan (if repair radius reaches critical size: full replan), and human escalation (if all automated recovery fails: notify human with versioned log).

9. **Branching Factor Estimator (CREATE).** An Agentic Compute Criticality-inspired pre-execution check: before committing to a decomposition, estimate b (average sub-tasks spawned per step) and verify b < 1 for stability. Reject decompositions with b >= 1. Enforce the 45% Rule: if single-agent already handles a sub-task with >45% accuracy, do not spawn a specialist. Enforce the Golden Rule: never exceed 4 concurrent agents per sub-task group.

10. **Modular Planning Architecture (CREATE).** A MAP-inspired plan node with 6 specialized sub-modules: TaskDecomposer (high-level goal -> subgoal sequence), Actor (proposes candidate actions for each subgoal), Monitor (filters illegal/invalid actions -- replaces regex risk classifier), Predictor (simulates outcomes of candidate actions), Evaluator (scores predicted outcomes against goals), Orchestrator (selects best action, coordinates the other 5 modules). Each module is an independent LLM call with a specialized prompt, preventing the "cognitive overload" that causes monolithic planners to fail.

---

## Phase 4: The Revolutionary Program

The transformation of JORDAN from v1 to v2 proceeds in three waves. Each wave builds on the previous. Each wave produces a working, deployable system. There is no "big bang" rewrite -- the revolution proceeds dialectically, each phase negating and preserving elements of what came before.

### Wave 1: Immediate (1-2 Weeks) -- The Security Reformation

These are the CRITICAL and HIGH findings from the prior audit that must be fixed before ANY further development. They are the minimum viable safety baseline.

**Fix C1 (replan bypasses risk assessment):** Route replanned sub-tasks through the risk assessment node before execution. Estimated: ~10 lines changed in the conditional edge logic.

**Fix C2 (no replan ceiling):** Add a configurable max replan iteration count (default: 3) with forced transition to synthesis when reached. Estimated: ~5 lines in the replan node.

**Fix C3 (resume duplicates graph topology):** Remove duplicated graph construction in resume paths. Estimated: ~15 lines removed.

**Fix CR1 (parallel strips approval):** Add approval gate invocation in the parallel execution path. Parallel sub-tasks classified HIGH must trigger the approval gate, not bypass it. Estimated: ~20 lines.

**Fix CR2 (parallel no retries):** Add retry logic to the parallel executor matching sequential executor's 2-3 retries with LLM-based error analysis. Estimated: ~30 lines.

**Fix CRT1 (risk classifier weaponizable):** Add input sanitization to the risk classifier -- strip or neutralize risk-inflating/evading substrings before pattern matching. This is a temporary patch; the classifier is replaced entirely in Wave 2. Estimated: ~5 lines.

**Fix HR1 (default-to-LOW):** Change the risk classifier's default from LOW to MEDIUM with a warning flag when no pattern matches. Estimated: ~1 line.

**Remove confidence_score:** Strip the confidence_score field from all API payloads. It is generated but never consumed. Estimated: ~50 lines removed.

**Add replan ceiling enforcement:** Hard-cap replan iterations at a configurable maximum, enforced at the graph level, not the node level. Estimated: ~10 lines.

**Total Wave 1 scope:** ~150 lines changed/added/removed. Deployable within 1 week. Eliminates all 6 CRITICAL findings.

### Wave 2: Short-Term (1-3 Months) -- The Architectural Reformation

Wave 2 restructures JORDAN's architecture to match the research evidence. It is the most consequential wave -- it establishes the architecture that Wave 3 extends.

**Split nodes.py:** Decompose the 4,400-line monolith into:
- `planner.py` -- plan node with MAP-inspired sub-modules (TaskDecomposer, Actor, Monitor)
- `executor.py` -- sequential and parallel execution with compensation handlers
- `guardrails.py` -- 5-layer guardrail stack replacing risk.py
- `synthesizer.py` -- synthesize node with cross-agent evaluation
- `replanner.py` -- ALAS-inspired local compensation + Reflexion episodic memory
- `classifier.py` -- Cynefin domain classifier + TAPE dual-process router
- `memory.py` -- episodic memory system with per-mission and cross-mission stores
- `decomposer.py` -- zero-overlap and DAG-based decomposition strategies

**Implement Domain Classifier:** Add a pre-pipeline classifier that diagnoses the task domain (Clear/Complicated/Complex) and routes accordingly. Clear tasks take the TAPE fast path (direct execute). Complicated tasks take the standard pipeline with expert-model routing. Complex tasks take the probe-sense-respond path with safe-to-fail experiments.

**Implement Dual-Process Router:** Add TAPE-inspired complexity classification before pipeline entry. Simple tasks (factual queries, single-step actions) bypass Plan/Research/Risk and go directly to a lightweight execute. Complex tasks enter the full pipeline. Classification uses a prompted LLM call (cheap, fast) or a fine-tuned classifier model.

**Implement 5-Layer Guardrail Stack:** Replace risk.py's regex classifier with Enkrypt-inspired guardrails. Each layer is a separate module with independent configuration. Input Guardrail sanitizes user input and detects prompt injection. Planner Guardrail validates execution plans for goal adherence. Memory Guardrail scans stored state for embedded attacks. Tools Guardrail enforces tool allowlisting and usage policies. Output Guardrail filters synthesized outputs for policy violations.

**Implement Episodic Memory:** Add Reflexion-inspired memory stores. Per-mission memory accumulates reflections during execution. Cross-mission memory persists lessons across workflows. Codebase memory caches RECON summaries and effective decomposition patterns. Memory is queried by the planner (what worked before?), the executor (what should I avoid?), and the replanner (what did I learn?).

**Fix Parallel Executor Architecture:** Redesign the parallel executor around zero-overlap decomposition. The plan node's Decomposer produces sub-objectives with guaranteed file/component independence. The parallel executor dispatches them concurrently with isolated state per sub-task. Parallelism becomes the DEFAULT mode, not a degraded second-class citizen.

**Implement Compensation Handlers:** Add ALAS-inspired recovery policies to the executor. Each sub-task is assigned a compensation handler (retry, catch, fallback, escalate). Failures are classified (transient, persistent, structural) and routed to the appropriate handler. Local compensation preserves work-in-progress; global replanning is the last resort.

**Harden HITL Against Lies-in-the-Loop:** Add Markdown sanitization to approval dialogs. Enforce display length limits (<500 chars for summaries). Use structured approval formats that resist manipulation. Add context integrity checks (does the approval summary match the actual command?).

**Map OWASP ASI01-ASI10 to JORDAN agent types:** Create a threat register. For each agent type (researcher, coder, reviewer, planner, decomposer), identify which OWASP threats apply and what mitigations are in place. Document coverage gaps.

**Total Wave 2 scope:** ~2,000-3,000 lines new code, ~500 lines removed from nodes.py monolith. Deployable within 2-3 months. Establishes the v2 architecture baseline.

### Wave 3: Long-Term (3-12 Months) -- The Revolutionary Completion

Wave 3 implements the most advanced research capabilities. It requires Wave 2's architectural foundation.

**Adversarial Verification Engine:** Implement IFPV-inspired ACSE for software domains. For each sub-task plan, simulate an "adversary" (code reviewer + test suite + security scanner + linter) that predicts failure modes. Plans that fail adversarial verification are refined or rejected. The verification is dynamic (simulates the adversary's response) not static (regex on descriptions). Target: +19.4% task success improvement (matching IFPV's results in military domain).

**Recursive Spawning:** Implement THREAD-inspired recursive sub-task spawning. Sub-tasks can spawn child sub-tasks. Phi/psi functions control information flow across boundaries. Recursion depth limited to 3-4 levels. Maximum branching factor of 4 children per parent. Fork-join parallelism for independent children.

**Cross-Workflow Learning:** Extend episodic memory with automated pattern extraction. Analyze successful vs. failed decompositions to identify effective patterns per task type. Build a skill library of reusable sub-task templates. Fine-tune routing models (domain classifier, dual-process router) on JORDAN's own execution history. Target: compounding improvement -- the 100th task of a given type should be measurably faster and more reliable than the 1st.

**Modular Planner Implementation:** Full MAP-inspired planner with 6 specialized sub-modules (TaskDecomposer, Actor, Monitor, Predictor, Evaluator, Orchestrator). Each module is an independent LLM call with specialized prompting. The Orchestrator coordinates the other 5. Bounded-width, bounded-depth lookahead search using Predictor + Evaluator. Monitor provides action-level safety filtering.

**Branching Factor Integration:** Add pre-execution branching factor estimation to the plan node. Before committing to a decomposition, estimate b and verify b < 1. Reject decompositions with b >= 1. Integrate the 45% Rule: check single-agent baseline before spawning specialists. Enforce the 3-4 agent ceiling on concurrent execution groups.

**Standardized Benchmark Evaluation:** Establish quantitative baselines on SWE-EVO, SWE-Bench, and agentic task benchmarks. Track: task success rate, token efficiency, cost per successful task, guardrail trigger rate, false positive rate, replan frequency, and user approval rate. Use benchmarks to measure improvement across Waves 1-3.

**Red-Teaming Cadence:** Establish quarterly adversarial testing of the approval gate, guardrail stack, and tool execution paths. Use Enkrypt's SAGE/Goat++ methodology for multi-turn attacks. Document findings, prioritize fixes, retest.

**NIST AI RMF Conformance:** Operationalize the Govern/Map/Measure/Manage cycle for JORDAN. Document risk acceptance for each agent type. Implement runtime metrics collection (guardrail triggers, human overrides, incident rate). Establish incident response procedures for safety violations.

**Total Wave 3 scope:** ~5,000-8,000 lines new code. Deployable incrementally over 3-12 months. Completes the JORDAN v2 transformation.

---

## Conclusion: The Dialectical Imperative

The JORDAN v1 architecture is a thesis -- a structured, gated pipeline for agentic task execution. It contains genuine insights: the 6-node pipeline concept, LangGraph stateful orchestration, human-in-the-loop approval, sequential execution with retries. But it also contains structural contradictions that the research corpus exposes with devastating clarity:

- A risk classifier built on regex when the research demands adversarial simulation.
- A replanning node that discards all work when the research demands local compensation.
- A parallel executor bolted onto a sequential architecture when the research demands parallelism-first design.
- A monolithic planner when the research proves modular specialization is necessary.
- A flat decomposition ceiling when the research proves recursive spawning amplifies capability.
- A permissive security default when the research demands restrictive default-deny.
- A stateless architecture when the research proves episodic memory is the difference between 80% and 91% accuracy.

These are not bugs to be patched. They are contradictions to be resolved through architectural revolution.

The research corpus provides both the critique of v1 and the blueprint for v2. MAKER, ALAS, CommandCC, Agentic Compute Criticality, IFPV, MAP, THREAD, TAPE, Reflexion, Cynefin, and the safety frameworks are not competitors to JORDAN -- they are its raw materials. The dialectical task is to negate what must be destroyed, preserve what has been validated, and create what the synthesis demands.

The revolutionary program is specific, phased, and falsifiable:
- **Wave 1** eliminates the CRITICAL security findings. Without this, further development is indefensible.
- **Wave 2** restructures the architecture around the research evidence. This is the dialectical negation of v1.
- **Wave 3** implements the most advanced capabilities. This is the synthesis -- JORDAN v2 as a research-grade agentic workflow system.

The alternative to revolution is reformism -- patching v1's symptoms while leaving its contradictions intact. Reformism produces a system with fewer bugs but the same structural flaws. The research corpus makes clear that reformism is insufficient. The regex risk classifier cannot be "improved" -- it must be replaced. The monolithic planner cannot be "refined" -- it must be decomposed into specialized modules. The parallel executor cannot be "fixed" -- it must be redesigned around zero-overlap decomposition.

The philosophers (the 61 frameworks) have interpreted the world. The point is to change it.

---

*"The tradition of all dead generations weighs like a nightmare on the brains of the living."* JORDAN v1 is that tradition. The research corpus is the revolutionary theory that breaks the nightmare. The task now is to wield that theory as a material force.

---

**Appendix: Key Research Framework Citation Index**

| Framework | Key Finding | JORDAN Node | Action |
|-----------|------------|-------------|--------|
| MAKER/MDAP | Maximal decomposition = Theta(s ln s); partial = exponential | execute | Implement atomic decomposition for sequential chains |
| ALAS | Local compensation: 83.7% success, 60% token reduction, 1.82x speedup | replan | Replace global replan with local compensation + escalation |
| CommandCC | Zero-overlap decomposition enables radical parallelism | execute | Redesign parallel executor around zero-overlap guarantee |
| Agentic Compute Criticality | b<1 stable, 45% Rule, 3-4 agent ceiling, 87% prediction accuracy | risk_assessment | Add branching factor estimator, enforce agent ceiling |
| IFPV | Adversarial verification: +19.4% mission success, +31.8% suppression rate | risk_assessment | Replace regex classifier with adversarial simulation engine |
| MAP | 6 PFC-inspired modules: 74% vs. 11% GPT-4 CoT; every module necessary | plan | Decompose plan node into specialized sub-modules |
| THREAD | Recursive spawning amplifies smaller models +10-50% | plan, execute | Implement recursive sub-task spawning with phi/psi |
| TAPE | Dual-process routing: +16.3% task success with 0.5B models | execute | Add complexity classifier + fast/slow routing |
| Reflexion | Episodic memory: 91% HumanEval vs. 80% baseline | replan | Add per-mission and cross-mission memory stores |
| Cynefin | Domain-dependent response; misdiagnosis = catastrophic failure | research, replan | Add domain classifier before pipeline entry |
| OWASP/Enkrypt/NIST | 5-layer guardrail, ASI01-ASI10, Lies-in-the-Loop | risk_assessment | Implement defense-in-depth guardrail architecture |
| LangGraph | Pregel/BSP, checkpoint/resume, interrupt, Send API | (infrastructure) | Preserve; build v2 architecture atop LangGraph primitives |
