# Lane C: Problem and task decomposition, from theory to LLM agents

Method note. I ran about 24 searches and 16 page reads. The shared web-fetch budget ran out partway through, so a number of classical items (Simon, Alexander, Conway, Brooks, Rasmussen, KAOS, GSN, Zwicky, Feathers, Beck, Jackson, HTN method quality, critical chain, cone of uncertainty) are `[recalled]` and not read this session. Every number below is tagged with the source that states it. Where I could not open a source I say so.

## Summary (the findings that matter most)

1. **Cut along the thing most likely to change, not along the processing steps (Parnas 1972).** The same program decomposed by pipeline stage has change ripple across modules; decomposed by hidden design decision, most changes stay in one module. For an agent this means the subtask boundary should be "one decision hidden behind one interface", not "step 1, step 2, step 3". JORDAN v2 only says "dependency-ordered", which is a sequencing criterion, not a cutting criterion. `[verified]`
2. **Decomposition is not free and often hurts.** Google/MIT's controlled study (180 configurations) found every multi-agent variant lowered performance on sequential planning tasks by 39 to 70 percent, independent agents amplified errors 17.2 times, and returns went flat or negative once a single agent already scored above about 45 percent. Anthropic itself says most coding tasks have fewer parallelizable parts than research. `[verified]`
3. **The best-supported LLM rule is "decompose as needed, after the direct attempt fails" (ADaPT).** Try the whole task; split only on failure; recurse with a depth cap. This is the decomposition analogue of v2's "start one tier lower, promote on surprise", and it is the one place v2's design is directly supported. The paper also shows the weakness: the success signal was self-assessed and was inflated by more than 30 points on WebShop. `[verified]`
4. **Parallel workers collide through implicit decisions, not through missing messages.** Cognition's two principles ("share full traces"; "actions carry implicit decisions") and Anthropic's lesson that vague delegation duplicates work both point to the same fix: interfaces must be written down before parallel work starts (contract-first), and a final integration check must exist. `[verified]`
5. **Extreme decomposition (MAKER) works only when the step definition is handed in and each step is small and exactly checkable.** One million steps, zero errors, on Towers of Hanoi with gpt-4.1-mini; the paper states the step definition is "given a priori". It does not show that a model can discover a good decomposition. Do not cite it as evidence that DAG decomposition of real coding work scales. `[verified]`
6. **Frontier models can now do hours-long tasks undecomposed, so granularity should scale with measured capability, not be fixed.** METR (May 2026 report) puts the public-frontier 50 percent time horizon near 12 hours (interval roughly 5 to 61 hours) and the 80 percent horizon near 1.5 hours, with the suite saturating above 16 hours and cheating inflating results. The reliable horizon (80 percent) is about 8 times shorter than the headline. Subtasks should target the 80 percent horizon of the model that executes them. `[verified]`
7. **Order work by risk and integration first, not by dependency alone.** Tracer bullets, walking skeleton, steel thread, spikes and Mikado all invert "build the pieces, integrate last". v2 orders by dependency and runs a premortem, but nothing forces an end-to-end thin slice or a spike before the commitment of the plan. `[verified for tracer bullets/Mikado/SPIDR definitions; recalled for walking skeleton and steel thread]`
8. **Mikado method is the most agent-ready decomposition procedure for legacy change.** Attempt the change naively, record what breaks as prerequisites, revert, recurse leaf-first. It builds the DAG empirically and uses revert as the safety net, which agents can do cheaply (git). `[verified]`
9. **Two measured agent failure modes that decomposition must guard against:** long-horizon collapse driven by early planning errors that propagate (HORIZON, 3,100+ trajectories) and cumulative structural erosion across iterative extensions (SlopCodeBench: erosion rose in 80 percent of trajectories, best strict solve rate 17.2 percent). Prompts for quality lowered the starting level but not the rate of decay. `[verified]`
10. **Small batches are the one decomposition practice with DORA-program backing, and DORA now says AI makes it more important, not less.** The cited evidence is correlational survey research, and the pages I read assert rather than quantify. `[verified, with the caveat that figures were not shown]`
11. **Detecting a wrong decomposition needs explicit triggers**: a coupling matrix that is not triangular (Suh's "coupled" design), a subtask whose acceptance check needs another subtask's internals, integration failure rate, and repeated edits to the same files from different workers. v2 has a qualitative coupling check and no trigger list. `[recalled, synthesized]`

## Findings

### Parnas information hiding (1972)
- **What it is.** Parnas compared two decompositions of a keyword-in-context index system. Decomposition 1 made each major processing step a module (input, circular shift, alphabetize, output, master control). Decomposition 2 made each module hide one design decision (line storage, input, circular shifter, alphabetizer, output). He lists decisions likely to change (input format, whether all lines are kept in memory, character packing, whether circular shifts are stored or computed, when alphabetizing happens) and shows that in decomposition 1 several changes touch many modules while in decomposition 2 most stay in one. He also notes that the shift module over-specified an order, a design error, because it restricted future implementations. `[verified]`
- **Source.** D. L. Parnas, CACM, 1972. https://cse.sc.edu/~mgv/csce330f24/ParnasCriteria.pdf
- **Critique.** The criterion needs a prediction of what will change; that prediction is judgment, and wrong predictions leave modules that hide nothing useful. Parnas's own example is small. `[recalled for the general critique]`
- **Transfer.** Strong. An agent can be asked, per candidate boundary, "which decision does this subtask hide, and what is the interface?" Agents also have a hazard humans do less: they will copy implementation detail across a boundary because it is in context. A brief that names the hidden decision and forbids reading across the boundary counters that.
- **V3 implication.** V3 should make the cutting criterion explicit in PLAN: each subtask names (a) the one design decision it owns, (b) the interface it exposes, (c) what it must not know. Kernel one-liner plus a plan schema field; the harness can reject plans with an empty "owns" field.

### Simon, near-decomposability, and the Architecture of Complexity
- **What it is.** Simon argued that complex systems that evolve are hierarchic and nearly decomposable: interactions within a component are much stronger and faster than interactions between components, so each level can be studied mostly alone, with between-component coupling treated as an aggregate. `[recalled, not opened this session]`
- **Critique.** Near-decomposability is a property of the problem, not a choice; some problems have no good cut. Coupling that is weak on average can still be fatal at one edge.
- **Transfer.** It gives a test, not a procedure: measure whether intra-subtask references dominate inter-subtask references. For code this is cheap to compute (import graph, shared files touched). 
- **V3 implication.** V3 should compute a crude coupling score from the planned file/symbol footprint of each subtask (shared files, shared symbols) and refuse parallel dispatch of subtasks whose footprints overlap. Harness code; belongs with the fence check v2 already has. `[candidate; untested]`

### Alexander, Notes on the Synthesis of Form
- **What it is.** Alexander lists requirements, builds a graph of their interactions, and partitions the graph into sets with minimal cross-interaction (the original used a computer program), then designs each set. `[recalled]`
- **Critique.** Alexander later disowned the method as too mechanical; interaction judgments are subjective. `[recalled]`
- **Transfer.** It is the formal ancestor of v2's DSM coupling check. The lesson is that you partition requirements, not tasks: decompose the acceptance criteria first, then group.
- **V3 implication.** Nothing new beyond Parnas and Suh; keep as a citation.

### Suh, axiomatic design
- **What it is.** Two axioms. The independence axiom: keep functional requirements independent, meaning each requirement is satisfied by its own design parameter. The information axiom: prefer the design with the highest probability of meeting requirements in tolerance. The design matrix mapping parameters to requirements is classed as uncoupled (diagonal, easiest), decoupled (triangular, workable if parameters are set in the right order) or coupled (requires iteration, to be avoided). Design proceeds by "zigzagging" between "what" and "how" at each level. `[verified]`
- **Source.** https://ieda.ust.hk/dfaculty/ajay/courses/ieem513/Design/AxDesSummary.html (summary of Suh's work; Suh 1990 original not opened).
- **Critique.** Real designs are often coupled; the axioms are normative and have been criticized as untestable in software. `[recalled]`
- **Transfer.** This is the cleanest mapping to JORDAN's DAG. A DAG is precisely a decoupled (triangular) matrix. A cycle is a coupled design. v2's BACKBRIEF "DAG cycle detection" is already the triangularity test.
- **V3 implication.** V3 should treat a detected cycle or a requirement mapped to more than one subtask as "decomposition wrong, re-cut", not as "add an ordering constraint". Harness check on the plan file. Zigzag (alternate requirement level and design level) is a cheap prompt pattern for DEEP planning.

### Means-ends analysis, GPS, AND/OR graphs, goal trees
- **What it is.** GPS (Newell and Simon) computes the difference between current and goal state and picks an operator that reduces it, setting up preconditions as subgoals. AND/OR graphs represent a goal as reducible by alternative methods (OR) each of which needs all subgoals (AND). `[recalled]`
- **Critique.** GPS is brittle when differences are not well ordered; it needs a hand-built difference table. AND/OR search blows up without heuristics.
- **Transfer.** Useful vocabulary: a subtask list is an AND node; a COA comparison is an OR node. v2's DEEP "3 competing COAs" is OR-branching at the root only. ADaPT (below) is the LLM version of AND/OR with fallbacks.
- **V3 implication.** Allow OR nodes at any depth (a subtask may carry a fallback method), but only expand them when the first method fails (least commitment). Plan schema; no new kernel text.

### Conway's law, Brooks's conceptual integrity, Rasmussen's abstraction hierarchy
- **What they are.** Conway: system structure mirrors the communication structure of the organization that builds it. Brooks: a system is best when designed by one mind or a very small number; many workers on one design produce incoherence. Rasmussen: represent a system on levels from purpose through function to physical form, and reason about "why" upward and "how" downward. `[recalled]`
- **Transfer.** Conway's law is directly applicable to multi-agent builds: if workers cannot see each other, the seams will show up as interface mismatches (this is Cognition's Flappy Bird failure). Brooks supports a single "architect" voice, which matches JORDAN's lead-decides-and-workers-build orchestration. Rasmussen's levels map onto intent, plan, subtask, and diff.
- **V3 implication.** V3 should require that one agent (the lead) owns the interface and naming ruling, and that workers get that ruling verbatim. Already approximately the "design rulings" in v2's pointer briefs; make it mandatory for any parallel dispatch. Orchestration layer.

### Jackson problem frames, KAOS, Goal Structuring Notation, Zwicky
- **What they are.** Problem frames classify a problem (required behavior, information display, workpieces, transformation, commanded behavior) and attach a known decomposition and concerns to each frame. KAOS refines goals by AND/OR until each leaf is assignable to an agent, and attaches obstacles (what could stop the goal). GSN structures an assurance argument as goal, strategy, context, solution (evidence). Zwicky's morphological analysis tabulates parameters with options and enumerates combinations. `[recalled]`
- **Transfer.** KAOS "obstacles" is premortem done per goal node; GSN's goal-strategy-evidence tree is a good schema for the final REPORT (each acceptance criterion links to its evidence). Problem frames give a small library of "known cuts" by problem type, which is exactly what an HTN method library is.
- **V3 implication.** V3 should ship a short library of decomposition templates keyed by task type (bug fix, feature, refactor, migration, research), each with the standard cut and the standard verifier. On-demand module. See the HTN entry for why this beats free-form decomposition.

### Hierarchical task networks, what makes a method library good
- **What it is.** HTN planning refines abstract tasks into subtasks by applying hand-written methods, each with preconditions. `[recalled]` The earlier corpus already has the textbook summary.
- **What the evidence says.** I did not find a source this session that measures method quality. The best LLM-era evidence for library-style decomposition is Least-to-Most (below): decomposition prompts did not transfer across domains and needed a domain-specific exemplar. `[verified]` That supports "methods keyed to task type", and it warns against one universal decomposition prompt.
- **V3 implication.** As above: task-type templates, each tested against a small eval set. Eval suite.

### Software delivery: tracer bullets, walking skeleton, steel thread, spikes
- **What they are.** Tracer bullets (Hunt and Thomas): build a thin working path through every layer first, using production-quality code, and adjust aim from real feedback. It differs from a prototype, which is thrown away. Walking skeleton (Cockburn): the smallest implementation that performs an end-to-end function and exercises the architecture. Steel thread: the same idea in systems-engineering language. Spike (XP): a time-boxed experiment to answer one technical question. `[tracer-bullet existence verified via search results at https://www.artima.com/intv/tracer.html; mechanism details recalled]`
- **Critique.** A skeleton can hard-code an architecture too early. Vertical slices can duplicate effort across slices when shared infrastructure is missing. `[recalled]`
- **Transfer.** Very good for agents because it makes the verifier exist early (v2's "wire the verifier first") and surfaces interface mismatches while there is only one seam to fix. It also bounds the blast radius of a wrong plan.
- **V3 implication.** V3 should require, for STANDARD and DEEP, that subtask 1 be the thinnest end-to-end path (or a spike if feasibility is unknown) with its acceptance command running, before any fan-out. Kernel rule plus a hook that blocks parallel dispatch until subtask 1's check has passed once.

### Mikado method
- **What it is.** Set a goal; make a naive attempt; note what breaks as prerequisites; revert the attempt; record prerequisites in a graph; work leaf-first; repeat until the goal change applies cleanly. Guidelines: start with the goal, use experiments, revert, focus on leaves. `[verified]`
- **Source.** Ellnestam and Brolund, The Mikado Method (Manning). https://livebook.manning.com/book/the-mikado-method/chapter-3
- **Critique.** The graph can grow large in tangled code, and each experiment needs a fast build/test cycle. `[recalled]`
- **Transfer.** Excellent: agents have cheap revert and can run the naive attempt in a throwaway worktree. It builds the DAG from evidence rather than from the model's guess, which fixes the main weakness of plan-first decomposition (the plan's premise is unverified).
- **V3 implication.** V3 should offer "empirical decomposition" for refactors and migrations: naive attempt in a scratch worktree, harvest compile and test failures as prerequisites, revert, then plan from the harvested graph. On-demand module plus a worktree script.

### Expand/contract (parallel change), branch by abstraction, strangler fig, characterization tests
- **What they are.** Parallel change: add the new interface alongside the old (expand), migrate callers, remove the old (contract), so every commit is releasable. Branch by abstraction: put an abstraction in front of the old implementation, build the new behind it, switch. Strangler fig (Fowler): grow the replacement around the legacy system, route traffic over incrementally. Characterization tests (Feathers): before changing legacy code, write tests that pin its current behavior. `[recalled; mikado/parallel-change search results appeared but pages not read]`
- **Critique.** Each carries temporary duplication and a risk that the contract phase never happens.
- **Transfer.** These turn a risky change into a chain of individually verifiable, individually revertible steps, which is exactly the "each subtask small enough to verify" property. Characterization tests are the missing verifier when none exists.
- **V3 implication.** V3 should add a rule: if no test covers the code to be changed, the first subtask is characterization tests, and the contract phase of any expand/contract must be a tracked subtask with an owner, not an intention. Kernel line in WIRE THE VERIFIER; plan-schema field.

### Story splitting, SPIDR, INVEST, Beck's "make the change easy"
- **What it is.** SPIDR (Mike Cohn): split by Spike, Path, Interface, Data, Rules. Spike is a research split; Path splits by different ways to reach the goal; Interface delivers a simple interface first; Data supports a simple subset first; Rules sets aside rules to add later. `[verified]` INVEST says a story should be independent, negotiable, valuable, estimable, small, testable. Beck: "make the change easy (warning: this may be hard), then make the easy change". `[recalled]`
- **Source.** https://www.mountaingoatsoftware.com/blog/five-simple-but-powerful-ways-to-split-user-stories
- **Critique.** Splits by technical layer fail INVEST's "valuable"; the common mistake is horizontal slicing. `[recalled]`
- **Transfer.** SPIDR is a ready checklist of cuts for a too-big subtask that each preserves end-to-end behavior. Beck's line is a two-subtask pattern: a behavior-preserving refactor first (verifiable by existing tests), then the feature.
- **V3 implication.** V3 should use "preparatory refactor, then feature" as the default decomposition for any change touching code the agent did not write, with the refactor commit required to pass tests unchanged. On-demand module.

### Small batches and trunk-based development (DORA)
- **What it is.** DORA states that working in small batches "predicts software delivery performance and organizational performance", recommends small releasable changes into trunk at least daily, and calls a batch taking longer than a week too big. The page says small batches amplify AI's positive impact, that AI adoption often increases delivery instability, and that AI generates large blocks that are harder to review and integrate. `[verified]`
- **Source.** https://dora.dev/capabilities/working-in-small-batches/ ; 2025 report PDF located but not read: https://services.google.com/fh/files/misc/2025_state_of_ai_assisted_software_development.pdf
- **Critique.** The pages I read give no figures; the evidence base is survey correlation, and "week" is a prescription not a measured threshold. The claim that reviewing machine-generated changes costs more per line is asserted. `[verified as asserted]`
- **Transfer.** Applies to the agent's output: the unit of delivery to a human reviewer should be small. It does not tell the agent how small to make internal subtasks.
- **V3 implication.** V3 should cap diff size per reviewable unit (a line or file-count ceiling set by the operator, flag on exceed) and force a split or an explicit override. Harness hook; the ceiling number should be calibrated, not invented.

### Contract-first and interface-first parallel work, stacked diffs
- **What it is.** Define the API, schema, or type signatures and share them before workers implement either side; stacked diffs chain small dependent changes for review. `[recalled]`
- **Evidence from agents.** Anthropic's multi-agent write-up says each delegated subtask needs "an objective, an output format, guidance on the tools and sources to use, and clear task boundaries"; vague delegation produced duplicated work. Cognition's Flappy Bird example split a game into background and bird subtasks and got two incompatible styles. `[verified]`
- **Sources.** https://www.anthropic.com/engineering/multi-agent-research-system ; https://cognition.com/blog/dont-build-multi-agents
- **Critique.** Contracts written before implementation are often wrong; the interface can need revision when the first side discovers a constraint.
- **V3 implication.** V3 should give every parallel dispatch a contract artifact: signatures or schemas plus an executable contract test that both sides run. Add a rule that either side may propose a contract amendment, which only the lead can approve (so there is one authority, per Brooks). Harness schema plus orchestration layer.

### Planning theory: partial-order planning, least commitment, rolling wave, last responsible moment, cone of uncertainty, critical chain
- **What they are.** Partial-order planning leaves ordering unspecified until forced (least commitment). Rolling-wave planning details the near term and leaves the far term coarse. Last responsible moment: delay a decision until the cost of delay exceeds the cost of deciding. The cone of uncertainty claims estimate error narrows as a project advances. Critical chain schedules around resource-constrained chains with shared buffers. `[all recalled]`
- **Critique.** The cone of uncertainty is not a law; later empirical work found the narrowing is not automatic. `[uncertain, recalled]`
- **Transfer.** Rolling wave and least commitment match what the LLM evidence says about plan decay: early planning errors propagate (HORIZON), and ADaPT decomposes on demand. A full up-front DAG down to leaf level commits too much.
- **V3 implication.** V3 should plan to leaf level only for the next wave and leave later waves as one-line milestones with acceptance checks, expanding at each wave boundary (the FRAGO point). This contradicts a literal reading of v2's "decompose into a DAG of subtasks"; see Contradictions. Kernel change.

### Least-to-most, decomposed prompting, plan-and-solve, self-discover, skeleton-of-thought
- **What it is.** Least-to-most prompting has two stages: decompose, then solve subproblems in order with prior answers in context. On SCAN length split it scored 99.7 percent versus 16.2 percent for chain-of-thought (code-davinci-002); on GSM8K it was only slightly better overall (62.39 vs 60.87 percent), with a larger gap on 5-plus-step problems (45.23 vs 39.07). The authors report decomposition prompts do not transfer across domains. `[verified]` I did not open decomposed prompting, plan-and-solve, self-discover or skeleton-of-thought this session; one search returned their arXiv links (for example https://www.arxiv.org/pdf/2401.14043) but I did not read them. `[recalled]`
- **Source.** Zhou et al., 2022. https://ar5iv.labs.arxiv.org/html/2205.10625
- **Critique.** The huge SCAN gain is on a synthetic compositional benchmark with easy decomposition; the realistic math benchmark shows a small gain. This is the pattern across prompt-level decomposition papers: large on structured toy tasks, small on messy ones. `[verified for L2M; pattern recalled]`
- **Transfer.** Prompt-level decomposition inside a single model call is largely absorbed by reasoning models; what remains useful is the explicit ordering where each answer is passed forward.
- **V3 implication.** None for the kernel. Do not invest in prompt-style decomposition tricks; invest in the structure around the model.

### ADaPT, as-needed decomposition
- **What it is.** Three parts: an executor (ReAct-style loop, self-reports success or failure), a planner (produces a short plan, about 3 to 5 subtasks, joined by AND or OR), and a recursive controller that tries the executor first and calls the planner only on failure, recursing to a maximum depth. With GPT-3.5 it beat ReAct by 28.3 points on ALFWorld, by up to 27 on WebShop and by 33 on TextCraft; performance rose with the depth cap. `[verified]`
- **Source.** Prasad et al., NAACL Findings 2024. https://arxiv.org/html/2311.05772v2
- **Critique.** The executor's self-assessed success was inflated by more than 30 points on WebShop relative to environment reward, which can stop decomposition too early; single run per model; GPT-3.5 era; decision-making environments only. `[verified]`
- **Transfer.** Directly maps to "attempt, verify with an external check, decompose on failure, cap depth". It also confirms that the stop signal must come from a real verifier, not the agent's say-so, which is v2's stated position.
- **V3 implication.** V3 should state decomposition as a failure-triggered operation: attempt the unit directly unless a pre-registered rule forces a split (footprint over the ceiling, no verifier available, parallel dispatch), and split only when the acceptance check fails. Depth cap of 2 to 3 as a ceiling with a flag, consistent with v2's iteration ceilings. Kernel plus harness (the check result, not the agent, gates splitting).

### Parsel
- **What it is.** An LLM writes a hierarchy of natural-language function descriptions; candidate implementations for each function are generated and combinations are checked against tests. Reported: more than 75 percent higher pass rate on APPS than direct AlphaCode and Codex sampling (often with a smaller sample budget); HumanEval pass@1 from 67 to 85 percent with generated tests. `[verified]`
- **Source.** Zelikman et al., NeurIPS 2023. https://arxiv.org/abs/2212.10561v3
- **Critique.** Needs tests per function; results are on function-level benchmarks, not repositories; model generation is old.
- **Transfer.** The mechanism worth keeping is "decompose, then search over implementations of each piece, selecting by tests". It is a decomposition that is verifiable at every node by construction.
- **V3 implication.** For DEEP, correctness-critical subtasks, generate 2 to 3 candidate implementations per leaf and select by the acceptance command, rather than one implementation plus self-review. On-demand module; compare against a single-sample baseline in the eval suite.

### MAKER (extreme decomposition with voting): the deeper reading
- **What it is.** Single-step subtasks with minimal context; first-to-ahead-by-k voting per step (k_min 3 in the experiments); red-flagging (discard over-long or malformed outputs rather than repairing). Solved 20-disk Towers of Hanoi, over one million LLM steps, zero errors, with gpt-4.1-mini. Under the paper's model, k_min grows as ln of the number of steps and cost as s ln s. Error per step rose sharply past about 700 tokens of response. `[verified]`
- **Source.** https://arxiv.org/html/2511.09030v1
- **Critique, stated by the paper.** The decomposition is supplied by hand ("it is assumed the definition of step is given a priori"); the overall strategy is in the prompt, so it tests instruction-following, not insight; independence of errors is assumed but correlated errors were observed (one step took 18 votes); only Towers of Hanoi is a main experiment; voting needs exact-match answers. `[verified]`
- **Transfer.** It does not transfer to coding where outputs are diffs, not exact-match strings. What does transfer: the red-flag signal (long, rambling output predicts error) and the arithmetic that per-step reliability must be high for long chains.
- **V3 implication.** V3 should drop the idea that "MAKER decomposition" means design-implement-test-verify per subtask (which is an interpretation of the name, not what the paper does) and use only red-flagging: treat an unusually long or malformed worker output as a failed attempt, not something to repair. Harness (a length or format check on worker return). Flag in the eval suite as an open measurement. Also note this contradicts v2's description of MAKER; see Contradictions.

### Recursive Language Models
- **What it is.** The prompt is stored as a variable in a Python REPL; the root model sees only metadata, writes code to inspect, split and filter it, and calls sub-model instances on pieces. Results: BrowseComp+ 1K documents 91.3 percent versus 51.0 (CodeAct plus BM25) and 70.5 (summary agent); OOLONG-Pairs 58.0 percent versus 0.1 for base GPT-5. Limitations stated: recursion depth one, synchronous sub-calls, high cost variance, base models beat RLMs on short inputs, and an ablation without sub-calls sometimes beat the full RLM. Different models decomposed differently (one launched a sub-call per line until warned). `[verified]`
- **Source.** Zhang and Khattab et al., arXiv 2512.24601. https://arxiv.org/html/2512.24601v2 (author attribution from memory, not checked.)
- **Transfer.** Applies to the inspection half of coding agents: huge repo or log reading. The model decides decomposition itself, which is the capability MAKER lacks, but only for chunk-and-aggregate problems where pieces are independent.
- **V3 implication.** V3 should adopt "context as external variable" for bulk reads: workers get a programmatic handle (grep, script) to the data and return a summary, never the raw bulk. v2 already says delegate bulk reads; make it a harness pattern with a cap on fan-out per call to prevent one-call-per-line. Orchestration layer.

### Orchestrator-worker systems and when multi-agent helps
- **Evidence for.** Anthropic's research system with a Claude Opus 4 lead and Claude Sonnet 4 subagents outperformed single-agent Opus 4 by 90.2 percent on its internal research eval; agents use about 4 times the tokens of chat and multi-agent about 15 times; token usage explained about 80 percent of the performance variance on BrowseComp. Effort-scaling rules: simple fact-finding one agent with 3 to 10 tool calls, comparisons 2 to 4 subagents, complex research more than 10. `[verified]` https://www.anthropic.com/engineering/multi-agent-research-system
- **Evidence against.** Google, MIT et al. across 180 configurations, five architectures, three model families and four benchmarks: centralized coordination gave +80.8 percent on a parallelizable financial-reasoning task; every multi-agent variant lowered sequential-planning performance, by 39 to 70 percent; independent agents amplified errors 17.2 times versus 4.4 times for centralized; returns turn negative once a single agent baseline passes about 45 percent; tool-heavy tasks suffer from coordination overhead. A fitted predictor chose the best architecture for 87 percent of held-out configurations. `[verified]` https://arxiv.org/html/2512.08296v2 . MAST analysis of 1,642 multi-agent traces found 14 failure modes: about 44 percent system design, about 32 percent inter-agent misalignment, about 24 percent verification (category sums were computed by the fetch tool from per-mode figures; treat as approximate). Adding an objective verification step raised ProgramDev success by 15.6 percent in their intervention. `[verified]` https://arxiv.org/html/2503.13657v3
- **Anthropic's own caveat.** "Most coding tasks involve fewer truly parallelizable tasks than research." `[verified]`
- **Transfer.** The decision of whether to fan out should be made on task structure (parallelizable or sequential), and on whether a single agent already does well. Fan-out is for breadth (research, review sweeps, independent files), not for a dependent chain of edits.
- **V3 implication.** V3 should add a pre-dispatch gate: fan out only if (a) subtasks have disjoint file footprints, (b) a contract exists, (c) the single-agent attempt is not already likely to succeed. Otherwise run sequentially in one context. Harness plus orchestration. JORDAN's "premium lead only dispatches" posture is fine for breadth tasks, but for dependent edits the lead should keep a single executing thread.

### Long-horizon capability and failure data (2025 to 2026)
- **METR time horizon.** Original work: 50 percent time horizon doubling about every 7 months over about 6 years; a SWE-bench Verified replication gave under 3 months; current models near 100 percent on tasks under 4 minutes and under 10 percent over about 4 hours (as of the March 2025 page, now flagged out of date). `[verified]` https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/ . May 2026 frontier risk report: public frontier 50 percent horizon about 12 hours, interval about 5 to 61 hours; 80 percent about 1.5 hours; suite unreliable above 16 hours; about 16 percent of successful runs on tasks over 8 hours were illegitimate on review; METR notes benchmark performance has often overstated real-world performance, citing its own finding on AI pull requests that would not be merged. `[verified]` https://metr.org/blog/2026-05-19-frontier-risk-report/
- **HORIZON paper.** 3,100+ trajectories, 700+ tasks, four domains; performance degrades non-linearly past a domain-specific breaking point; seven failure categories; about 72.5 percent process-level and 27.5 percent design-level; planning errors arise early and propagate; authors recommend hierarchical subplanning, plan verification and repair, and memory for long-range constraints. Inter-annotator kappa 0.61. `[verified]` https://arxiv.org/html/2604.11978v1
- **SlopCodeBench.** 20 problems, 93 checkpoints, agents extend their own code under changing specs. No agent solved a problem end to end; best strict checkpoint solve rate 17.2 percent; erosion rose in 80 percent of trajectories, verbosity in 89.8 percent; agent code about 2.2 times more verbose than 48 maintained repos; quality-aware prompts lowered starting levels but not the degradation rate. `[verified]` https://arxiv.org/html/2603.24755v1
- **Transfer and implication.** Granularity should be set against the 80 percent horizon of the executing model (about 1.5 hours of human-equivalent work for the public frontier by METR's May 2026 figure) with the 50 percent figure as a ceiling that implies coin-flip reliability. Sequential extensions degrade structure, so V3 should include a per-checkpoint structural review (complexity concentration, duplication), not only tests passing. Eval suite plus harness metric. I found no study that measures an "optimal granularity" for coding subtasks; see Gaps.

### Issue-to-subtask planners and SWE-agent-style decomposition
- **What I could verify.** Nothing this session: the fetch budget ran out before I could read Agentless or SWE-agent. From memory (`[recalled]`): Agentless used a fixed three-phase pipeline (localize, repair, validate) with no agent-chosen decomposition and was competitive on SWE-bench Lite at lower cost, which argued that a fixed, well-chosen decomposition can beat open-ended agent planning. Treat as a lead to verify (arXiv 2407.01489).

## Contradictions with JORDAN v2

1. **Up-front full DAG versus rolling wave and on-demand splitting.** v2 says "decompose into a dependency-ordered DAG of subtasks, each small enough to verify." ADaPT, rolling-wave planning, least commitment, and HORIZON's finding that early planning errors propagate all argue for detailing only the next wave and splitting on failure. At minimum v2 should say the plan is a coarse DAG with detailed leaves only for the next wave.
2. **Dependency order as the cutting criterion.** v2 sorts by dependency. Parnas and Suh say the cut criterion is hidden design decision and requirement independence; dependency order is only the sequencing step after the cut. A processing-step decomposition passes a cycle check and still fails Parnas's change test.
3. **MAKER is described in v2 as design-implement-test-verify per subtask for DEEP correctness-critical work.** The MAKER paper does single-step subtasks with majority-style voting and red-flagging, with the decomposition supplied by hand. v2 is borrowing the name. Rename the pattern and cite what is actually evidence-backed.
4. **Fan-out is implicitly good.** The Google/MIT data shows sequential planning tasks get worse in every multi-agent variant tested, by 39 to 70 percent. v2's orchestration posture (lead dispatches, workers build) is right for breadth work and likely wrong for dependent edits. `[the claim "likely wrong for coding" is an inference, not measured on coding]`
5. **A qualitative coupling check is v2's only decomposition-quality test.** The theory gives a testable one (triangular design matrix; footprint overlap). v2 has no post-hoc "decomposition was wrong" trigger.
6. **Order of work.** v2 puts risk and premortem before execution but does not require an end-to-end thin slice first. Tracer bullet and walking skeleton practice would reorder the first subtask.

## Hype and weak evidence

- **MAKER as general proof that "more decomposition is better".** One synthetic task, hand-supplied decomposition, exact-match outputs. Real coding has none of these.
- **Prompt-level decomposition (least-to-most and relatives) as a coding-agent technique.** Strong numbers are on SCAN-like synthetic tasks; on GSM8K the gain was about 1.5 points overall. Reasoning models have largely absorbed it.
- **METR doubling-time extrapolations.** Interval on the 12-hour figure spans about 5 to 61 hours; the suite saturates; METR reports cheating and says benchmark results have overstated real-world usefulness. Use the 80 percent horizon and treat it as a planning input to calibrate against, not a constant.
- **Anthropic's 90.2 percent gain.** Internal eval, research tasks, and the authors say it does not generalize to coding. Token spend explains about 80 percent of variance on BrowseComp, so part of the gain is just more compute.
- **DORA small-batch claims.** Survey-correlational; the pages I read gave no figures and the one-week threshold is a prescription.
- **Cone of uncertainty, critical chain, Zwicky and axiomatic design** carry advocacy more than measured software evidence. `[recalled]`
- **"Subagent per file" fan-out in agent hype posts.** The RLM paper itself observed a model launching one sub-call per line until warned, and the MAST data lists coordination failures as a third of all failures.

## Gaps

- Fetch budget ran out before I could read: Agentless, Building Effective Agents, Simon (1962), Alexander, Conway, Brooks, Feathers, Beck, Fowler (strangler, parallel change), GSN, KAOS, Jackson, decomposed prompting, plan-and-solve, self-discover, skeleton-of-thought, the DORA 2025 PDF, and METR's TH 1.1 post. These are marked `[recalled]` or omitted.
- No study found that measures an optimal subtask granularity for coding agents. Closest: METR horizons (a capability measure, not a granularity result) and HORIZON's depth/breadth extension (shows non-linear collapse, no recommended size).
- No evidence found on how well LLMs generate decompositions (as opposed to follow supplied ones) for repository-level changes; MAKER explicitly leaves it open.
- Did not find measurements of interface-mismatch rates in parallel coding agents; Cognition's evidence is anecdotal (one worked example) and MAST does not use the term.
- I found no source for HTN method-library quality criteria; the "good method library" claim above is inferred from Least-to-Most's domain-transfer limitation.

## Proposed decomposition procedure for V3 (synthesis, not sourced as a unit; each step cites the finding above)

1. **Try first.** If one agent can attempt the whole unit with a runnable check, do it (ADaPT). Decompose on check failure, depth cap 2 to 3.
2. **Decompose the acceptance criteria before the tasks** (Alexander, Suh); each criterion maps to exactly one owner subtask.
3. **Cut along hidden design decisions** (Parnas); each subtask records owns / exposes / must-not-know.
4. **Sequence skeleton-first, then risk-first:** subtask 1 is a thin end-to-end slice or a spike (tracer bullet, SPIDR spike); for legacy code, characterization tests then preparatory refactor (Feathers, Beck); for migrations use expand/contract with a tracked contract step.
5. **Fan out only on disjoint footprints with an executable contract** (Cognition, Anthropic, Google/MIT). Otherwise single-thread.
6. **Size leaves to the executing model's 80 percent horizon** (METR), reviewable diff ceiling per unit (DORA), and plan only the next wave in detail (rolling wave).
7. **Wrongness triggers:** cycle or non-triangular dependency; a requirement owned by two subtasks; a subtask check that needs another's internals; two workers editing the same file; integration test failure after all unit checks pass; repeated amendment requests to the same contract; a worker output flagged by the red-flag length or format rule. Any trigger means re-cut that region (FRAGO) rather than patching the symptom.

## Sources

- https://cse.sc.edu/~mgv/csce330f24/ParnasCriteria.pdf (Parnas 1972, read)
- https://ieda.ust.hk/dfaculty/ajay/courses/ieem513/Design/AxDesSummary.html (axiomatic design summary, read)
- https://arxiv.org/html/2311.05772v2 (ADaPT, read)
- https://arxiv.org/html/2511.09030v1 (MAKER, read)
- https://ar5iv.labs.arxiv.org/html/2205.10625 (Least-to-Most, read)
- https://arxiv.org/abs/2212.10561v3 (Parsel, read)
- https://arxiv.org/html/2512.24601v2 (Recursive Language Models, read)
- https://arxiv.org/html/2512.08296v2 (Towards a Science of Scaling Agent Systems, read)
- https://arxiv.org/html/2503.13657v3 (MAST, Why Do Multi-Agent LLM Systems Fail, read)
- https://www.anthropic.com/engineering/multi-agent-research-system (read)
- https://cognition.com/blog/dont-build-multi-agents (read)
- https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/ (read)
- https://metr.org/blog/2026-05-19-frontier-risk-report/ (read, first 100,000 characters)
- https://arxiv.org/html/2604.11978v1 (HORIZON / Long-Horizon Task Mirage, read)
- https://arxiv.org/html/2603.24755v1 (SlopCodeBench, read)
- https://dora.dev/capabilities/working-in-small-batches/ (read)
- https://www.mountaingoatsoftware.com/blog/five-simple-but-powerful-ways-to-split-user-stories (SPIDR, read)
- https://livebook.manning.com/book/the-mikado-method/chapter-3 (Mikado, read, headings only)
- Search results seen but not read: https://www.artima.com/intv/tracer.html ; https://services.google.com/fh/files/misc/2025_state_of_ai_assisted_software_development.pdf ; https://www.arxiv.org/pdf/2401.14043 ; https://www.cognizant.com/us/en/ai-lab/blog/maker
