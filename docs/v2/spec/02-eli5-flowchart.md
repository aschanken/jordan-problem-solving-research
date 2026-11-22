# JORDAN v2 -- How It Works (ELI5 Flowchart Document)

**Author:** Karl (dialectical critic, structural analyst)
**Audience:** Non-technical stakeholder -- smart, curious, no prior AI knowledge required
**Status:** FINAL v2 -- All 29 arbitration findings incorporated (ARBITRATION.md)
**Based on:** richard-revision-01.md (implementation spec), BRIEFING.md (shared agreements), richard-critique-02.md, ARBITRATION.md (arbitration decisions)

**Change log from v1 (Richard's tactical critique):**
- FAST path: Output guardrail now described with its 3 actual checks (not "garbled formatting"); denylist separated from LLM classifier; disclaimer includes "verification."
- Persona tracking: Both thresholds (30% review, 50% disable) now listed.
- DEEP path: Persona set corrected per DD-009 -- 4 standard (Pessimist, Optimist, Devil's Advocate, Resource Analyst) + 1 DEEP-only (Domain Expert). Resource Analyst and Devil's Advocate are standard; Domain Expert is the sole DEEP addition.
- Flowchart: F.3 three-way decision; S.6 interrupt semantics; S.16 runtime spawn monitor; S.19 UNEQUIVALENT routes to DONE; ceiling table fixed (PLAN -> REPLAN).

**Change log from v2 draft (arbitration finalization):**
- R-M7 / K-BB6: Persona set fully aligned to DD-009 -- 4 standard + 1 DEEP = 5 total. Resource Analyst moved to standard set. Domain Expert added as DEEP-only persona. All persona lists in prose and flowchart synchronized.
- Naming standardization: "pre-mortem" (with hyphen) verified consistent in all prose; code identifiers (`premortem_cycle_count`) preserved as standard coding convention.
- Richard's 7 inaccuracy checks re-verified: all 7 items present and correct in final output.

---

## 1. THE BIG PICTURE

JORDAN is an AI assistant that thinks before it acts. Instead of blurting out the first answer that comes to mind, it classifies your question, builds a plan, checks the plan for mistakes, and then executes it -- pausing to ask your permission whenever the work is risky or dangerous. Why the HOW matters to you: the same system that answers "what is 2+2?" in under a second will, when you ask it to reconfigure a production database, spend several minutes building a safety-checked plan and present it for your approval before touching anything.

---

## 2. THE THREE PATHS

JORDAN has three ways of handling your request. It picks the right one automatically based on what you are asking.

### FAST Path

**When it is used:** Simple, factual questions. "What is the capital of France?" "What does `git status` do?" "Convert 100 USD to EUR." Single-step, well-understood, nothing that could break anything.

**What happens, step by step:**

1. **Path Selection (under 1 second).** JORDAN's LLM classifier reads your question and decides how complex it is. Questions are labeled TRIVIAL, MODERATE, or COMPLEX. If the classifier labels your question TRIVIAL, JORDAN considers the FAST path.

2. **Safety Pre-Check (under 1 second).** Before taking the FAST path, a separate safety scanner checks your question against a pattern-based denylist -- a list of known-dangerous text patterns (like "delete all files" or "format disk"). This scanner is architecturally distinct from the LLM classifier: it is a simple pattern-match engine, not an AI. It makes a binary safety decision: is this input known-unsafe? If a dangerous pattern matches, JORDAN escalates to the STANDARD path instead -- slightly slower, but safer. This escalation is logged, and if the same pattern keeps triggering on questions that turn out to be harmless, the pattern is flagged as a false-positive candidate for review.

3. **Quick Answer (a few seconds).** JORDAN generates an answer directly -- no planning, no research, no tool access. Before showing you the answer, it runs a mandatory rule-based output scan checking for three specific things:

   - **Dangerous content:** Instructions for harmful acts, weapon creation, self-harm, illegal activities.
   - **Tool-call hallucination:** Raw AI formatting leaking through -- JSON function-call blobs, XML function tags, special tokens. These are the model mistakenly "calling a tool" when it has no tools to call. If detected, the entire answer is replaced with a safe fallback message: "I encountered an issue generating a response. Please try rephrasing your question."
   - **Safety refusal:** The model actively declining to answer (e.g., "I can't answer that," "I'm not allowed to"). Unlike dangerous content, a safety refusal is passed through to you -- it is legitimate model behavior. The output is flagged so JORDAN knows it happened but you still see the response.

4. **Disclaimer (instant).** If the output passes the guardrail, JORDAN adds a short disclaimer: "This is a quick answer generated without research or tool access. For complex topics requiring verification or deeper analysis, I can run a full investigation." This tells you: the answer may be correct, but you should verify it yourself. It is a truthfulness warning, not just a scope warning.

5. **Done.** You see the answer. No further steps.

**What you see:** Your question, then the answer appears with the disclaimer.

**When you are asked for input:** Never. FAST path is fully automatic.

**Typical duration:** 2-10 seconds.

**What can go wrong:** The answer may be incomplete or shallow because no research was done. The disclaimer warns you about this. If your question accidentally triggered the safety pre-check (e.g., you asked "how does the `rm -rf` command work?" rather than "run `rm -rf`"), JORDAN escalates to the STANDARD path instead -- slightly slower, but safer. The false-positive feedback loop ensures the denylist improves over time by identifying patterns that trigger too often on harmless questions.

---

### STANDARD Path

**When it is used:** Multi-step tasks. "Write a Python script that reads a CSV file and generates a summary report." "Find the bug in this code and fix it." "Research three competitors and compare their pricing." The task requires several steps, but the domain is familiar and the approach is straightforward.

**What happens, step by step:**

1. **Classification (under 1 second).** JORDAN determines this is not trivial (too many steps) and not deeply novel (familiar domain). STANDARD path selected.

2. **Planning (a few seconds).** JORDAN writes a plan. The plan breaks your request into smaller sub-tasks, each with a clear purpose, the tools it needs, and dependencies between them (e.g., "Step C cannot start until Step A and Step B are both done"). The plan also states the Commander's Intent -- the goal, constraints, and how to measure success. The plan gets a version number (starting at 1) and a checksum (a digital fingerprint of the plan content) so downstream steps can detect when the plan has changed.

3. **Backbrief -- Structural Check (a few seconds).** JORDAN checks the plan for structural mistakes: circular dependencies ("Step A depends on B, but B depends on A" -- an impossible loop), hidden couplings (two steps that would interfere with each other without realizing it), and missing dependencies. If the plan has structural problems, JORDAN revises it and re-checks. This can happen up to 2 times. After that, it accepts the plan and moves on, flagging that the structure was force-accepted. The force-accept flag (called `backbrief_forced`) is shown later in the approval briefing and tracked in the audit trail.

4. **Research -- Cache Lookup (under 1 second).** JORDAN checks its memory of past tasks for relevant information: "Have I done something like this before? What tools worked well? What pitfalls were encountered?" This is a database lookup, not a new web search. It also validates that any recommended tools are still available (tools get deprecated or removed over time -- stale recommendations are stripped out). If critical information is missing and the task is high-risk, JORDAN will pause and ask you for the missing information before proceeding.

5. **Risk Assessment (a few seconds).** JORDAN classifies each sub-task by risk level: LOW, MEDIUM, HIGH, or CRITICAL. It asks an AI model: "What could go wrong with each of these steps?" This is based on what the plan says it will do, not on what actually happens during execution later.

6. **Pre-Mortem -- Failure Simulation (a few seconds).** JORDAN imagines the plan has already failed and works backwards: "Why did it fail?" It uses multiple personas (a pessimist, an optimist, a devil's advocate, a resource analyst) to generate failure scenarios from different angles. If any persona finds a failure that is both severe AND likely, the plan goes back for revision. This cycle can happen up to 2 times.

7. **Branching Factor Check (under 1 second).** JORDAN checks the plan's shape. There are two checks: (a) fan-out -- whether any sub-task spawns multiple child sub-tasks that would cause work to explode exponentially, and (b) depth -- how long the chain of sequential dependencies is. If a sub-task fans out (one task creates many, each of which creates many more), the plan is halted. If the sequential chain is deeper than 10 steps, the plan is also halted. These are mathematical checks, not AI judgments.

8. **Risk Fusion (under 1 second).** JORDAN combines all the risk signals collected so far (from classification, risk assessment, pre-mortem, and branching check) into a single risk rating per sub-task. This prevents contradictory signals from reaching you (e.g., one check says LOW risk, another says HIGH, and you are left confused).

9. **Approval Gate (waiting for you).** If ANY sub-task is rated HIGH or CRITICAL, JORDAN stops and shows you a briefing. The briefing has two tiers:
   - **Summary (always shown):** The goal, the overall risk level, and any critical flags. If the plan was force-accepted through the backbrief ceiling, the summary includes a banner: "Plan structurally forced through -- DAG may contain unresolved issues."
   - **Details (expandable):** A per-step breakdown, the failure scenarios, and the revision history.
   You can approve the plan (it proceeds), reject it (it stops), or ask questions. If all sub-tasks are LOW or MEDIUM risk, this step is skipped -- JORDAN proceeds silently.

10. **Execution (seconds to minutes).** JORDAN executes the sub-tasks in order, respecting dependencies. Independent sub-tasks run in parallel (up to 4 at a time). Each sub-task runs in its own isolated workspace so they cannot interfere with each other. If a sub-task fails, JORDAN tries to fix it using a ladder of escalating strategies: re-prompt, catch the error with a fallback, try a different approach, expand the scope of the fix, replan globally, or escalate to you. It only moves UP the ladder -- it never tries the same failed strategy twice.

    During execution, JORDAN also monitors whether any sub-task unexpectedly spawns new sub-tasks (dynamic work creation the plan did not anticipate). If the total number of sub-tasks -- original plus dynamically spawned -- exceeds twice the original count, execution halts and JORDAN triggers a replan to restructure the work.

11. **Synthesis (a few seconds).** JORDAN merges all the sub-task results into a single coherent answer. If some sub-tasks produced text and others produced code, it handles the formatting differences automatically.

12. **Evaluation (a few seconds).** JORDAN checks the final output against the success criteria defined in the Commander's Intent. Result: SUCCESS (everything passed), PARTIAL (some things passed, some failed), FAILURE (nothing passed), or UNEQUIVALENT (no criteria were defined, so quality cannot be judged).

13. **Replan (if needed).** If the evaluation was not SUCCESS (and was not UNEQUIVALENT), JORDAN creates a delta plan -- a modified version of only the sub-tasks that failed. It runs a quick structural check on the delta, re-checks risk for changed parts, and re-executes. This loop can repeat up to 3 times total. Each replan cycle can try up to 6 different compensation strategies internally before consuming another replan attempt, so the worst case is 3 replans x 6 compensation attempts = 18 attempts before JORDAN escalates to you. If after 3 replans the result still is not SUCCESS, JORDAN escalates to you with a summary of what it tried and what went wrong.

**What you see:** After you submit your request, you may see nothing for a few seconds while JORDAN classifies and plans. Then, if your task requires approval, a briefing appears with an approval prompt. After approval, you may see progress indicators (or nothing, depending on the interface) while JORDAN executes. Finally, the answer appears.

**When you are asked for input:**
- During Research, if critical information is missing
- At the Approval Gate, if any sub-task is HIGH or CRITICAL risk
- During Execution, if the compensation ladder reaches human escalation
- At the end, if the replan ceiling is hit and the result is still not acceptable

**Typical duration:** 30 seconds to 5 minutes, depending on task complexity and whether the approval gate triggers.

---

### DEEP Path

**When it is used:** Complex, novel, or safety-critical tasks. "Design a new authentication system for our platform." "Investigate this security incident and recommend fixes." "Plan a migration of our entire database infrastructure." The task involves multiple domains, novel approaches, or operations where mistakes have serious consequences.

**What happens, step by step:**

The DEEP path follows the same pipeline as STANDARD, with these differences:

1. **Multi-COA Planning.** Instead of producing one plan, JORDAN generates multiple Courses of Action (COAs) -- different approaches to the same problem. It compares them and selects the best one (or presents options if the trade-offs are significant).

2. **MAKER Decomposition.** Sub-tasks are broken down to the smallest verifiable units. If a sub-task is critical (could cause serious harm if wrong), it is decomposed further until each piece is independently checkable.

3. **Sequential Default (not parallel).** DEEP tasks default to sequential execution -- one step at a time -- because the dependencies are more intricate and the cost of a parallel execution mistake is higher.

4. **Expanded Persona Set.** The pre-mortem uses the standard personas (Pessimist, Optimist, Devil's Advocate, Resource Analyst) plus one additional persona: the **Domain Expert**, which brings deep subject-matter knowledge to evaluate the plan's technical assumptions and domain-specific constraints. The Resource Analyst (which checks for memory limits, API rate limits, timeout constraints, and other resource bottlenecks) and the Devil's Advocate (which challenges the plan's unstated assumptions) are already active in the STANDARD path -- neither is new to DEEP. The Domain Expert is the only persona added for DEEP tasks. Total persona count: 4 standard + 1 DEEP = 5.

5. **Approval Gate Always Active.** On the DEEP path, the approval gate is always presented, regardless of risk level. Every sub-task gets human review.

6. **Full Briefing Detail.** The Tier 2 detail briefing is shown by default (not hidden behind a prompt).

**What you see:** Same stages as STANDARD, but more detail at each stage. Multiple plan options may be presented during approval. Progress is more granular during execution.

**When you are asked for input:** At every approval gate (always for DEEP), plus all the STANDARD touchpoints.

**Typical duration:** 5 minutes to several hours, depending on the number of sub-tasks and the number of approval cycles.

---

## 3. THE SAFETY FEATURES

### Approval Gate: "JORDAN asks you before doing anything dangerous"

Before JORDAN executes a plan that involves risky operations (changing files, running commands that modify your system, accessing sensitive data), it stops and shows you exactly what it intends to do. You can say "go ahead," "don't do it," or "I have questions." The gate triggers based on JORDAN's formal risk assessment of each sub-task (not just based on what the operation looks like -- writing a file might be LOW risk if it is a temporary output; deleting files would be HIGH or CRITICAL). The gate is mandatory for HIGH and CRITICAL risk operations, and optional (skipped) for LOW and MEDIUM risk. On the DEEP path, the gate is always shown.

Think of it like a contractor who, before taking a sledgehammer to your wall, shows you the blueprint and says: "I'm about to knock down this wall. Here is why, here is what is behind it, and here is what it will look like after. Shall I proceed?"

### Risk Classification: "How JORDAN decides what is dangerous"

Every sub-task in the plan gets a risk label:

- **LOW:** Read-only operations. Looking at files, searching code, fetching information. Cannot break anything.
- **MEDIUM:** Writing files, making API calls that have side effects, running code in a sandbox. Could mess things up, but the blast radius is small.
- **HIGH:** Deleting files, modifying production systems, running untrusted code, accessing sensitive data. Significant potential for harm.
- **CRITICAL:** Operations where a mistake could cause data loss, security breaches, or system outages. Mandatory human approval.

The classification is done by an AI model that reads the plan description and asks: "What is the worst thing that could happen if this step goes wrong?" It also considers how familiar the domain is (novel = higher risk) and how many tools are involved (more tools = more failure points).

Risk classification happens multiple times during a task: once before the pre-mortem, and again after any replanning that changes the sub-tasks.

### Pre-Mortem: "Imagining what could go wrong before doing it"

Most teams do a post-mortem -- after something breaks, they figure out why. JORDAN does the opposite: it assumes the plan has ALREADY failed, and works backwards to figure out what caused the failure. This is called a pre-mortem.

JORDAN uses multiple personas (different AI roles with different perspectives) to generate failure scenarios. There are 4 standard personas active on every path, plus 1 additional persona on the DEEP path (5 total):

- **Pessimist:** "Everything that can go wrong, will go wrong. Here is how."
- **Optimist:** "Even if most things go right, here is the one thing that derails it."
- **Devil's Advocate:** "What did the planner assume that nobody confirmed? Here is where the assumption breaks."
- **Resource Analyst:** "Here are the memory, storage, API, and timeout constraints that will kill this plan."
- **Domain Expert (DEEP path only):** "Here are the domain-specific technical constraints and assumptions the plan is missing."

If any persona identifies a failure that is both severe (HIGH or CRITICAL impact) AND likely (more than 50% chance), the plan is sent back for revision. This cycle can repeat up to 2 times. After that, the plan proceeds with the unresolved flags noted in the approval briefing.

Each persona's accuracy is tracked over time. There are two thresholds:
- **30% false-alarm rate:** The persona is flagged for review. It is still active, but a human operator should investigate why it is crying wolf so often.
- **50% false-alarm rate:** The persona is disabled until reviewed. It stops participating in pre-mortems entirely.

This two-tier system ensures personas that drift into unreliability are caught early (at 30%) before they degrade to the point of producing noise (at 50%, when they are silenced).

### Backbrief: "Repeating the plan back to make sure it makes sense"

Before JORDAN commits to a plan, it checks the plan's internal structure. This is like checking that a building's blueprint does not have stairs that go in circles or walls that support nothing:

- **Circular dependency check:** "Step A says it needs Step B to finish first. Step B says it needs Step A to finish first." That is a loop that cannot be resolved. The plan is rejected.
- **Hidden coupling check:** Two steps do not declare a dependency but would interfere with each other (e.g., both try to write to the same file, or both use the same database table in conflicting ways). The plan is flagged.
- **Dangling reference check:** A step depends on a step that does not exist in the plan. The reference is removed.

The backbrief can reject a plan up to 2 times. After that, it force-accepts the plan and moves on, but the approval briefing notes that structural verification was incomplete. The `backbrief_forced` flag is also consumed by the pre-mortem (personas are told to pay special attention to structural issues) and by evaluation (the evaluator notes that the plan had unresolved structural issues).

### Branching Factor Monitor: "Stopping when the work explodes"

The branching factor monitor has two components -- one that runs before execution and one that runs during execution.

**Pre-execution (static check):**
The monitor checks the plan's shape before any work begins. It looks at two things:

1. **Fan-out (width):** Whether any sub-task spawns child sub-tasks. If sub-tasks spawn more sub-tasks (the work fans out instead of converging), the plan is halted. Think of it as detecting a pyramid scheme before anyone loses money -- one task creating ten tasks, each of which creates ten more.

2. **Depth (chain length):** How long the chain of sequential dependencies is. A plan where Step 1 feeds Step 2, which feeds Step 3, all the way to Step 50, is a very deep chain. Any single failure in the chain breaks everything downstream. Maximum depth defaults to 10 steps.

Both violations trigger a halt that routes the plan to the replan loop with a structural flag -- JORDAN must restructure the work before it can proceed.

**During execution (runtime monitor):**
A separate runtime monitor tracks whether any sub-task, during execution, dynamically creates new sub-tasks (something the plan did not anticipate). If the total number of sub-tasks (original + dynamically spawned) exceeds twice the original count, execution halts and the replan loop is triggered. This prevents a sub-task from silently expanding the scope of work beyond what was approved.

---

## 4. WHAT THE USER SEES

### Terminal/CLI Output at Each Stage

**During Classification (1 second):**
```
[=] Analyzing your request...
```
No user action needed. This passes almost instantly.

**During Planning (a few seconds):**
```
[=] Building execution plan...
[+] Plan created: 5 sub-tasks, 2 dependencies
```
You may see a brief summary of the plan structure.

**During Safety Checks (a few seconds):**
```
[=] Verifying plan structure...
[+] Backbrief passed -- no structural issues
[=] Researching relevant past experience...
[+] Found 2 relevant templates from previous tasks
[=] Assessing risk...
[+] 3 sub-tasks: LOW, 1 sub-task: MEDIUM, 1 sub-task: HIGH
[=] Running pre-mortem simulation...
[+] No fatal failure scenarios detected
[=] Checking plan complexity...
[+] Fan-out: within limits. Depth: 4 (max 10) -- within limits.
```

**At the Approval Gate (waits for you):**
```
╔══════════════════════════════════════════════════╗
║               APPROVAL REQUIRED                  ║
╠══════════════════════════════════════════════════╣
║ Commander's Intent: Generate a Python script     ║
║ that reads sales.csv and produces a summary      ║
║ report with charts.                              ║
║                                                  ║
║ Overall Risk: HIGH                               ║
║ Sub-tasks: 5 total                               ║
║   LOW: 3    MEDIUM: 1    HIGH: 1    CRITICAL: 0  ║
║                                                  ║
║ ⚠ HIGH-RISK SUB-TASK: "Write output files to     ║
║   /home/user/reports/" -- this step writes to    ║
║   your filesystem.                               ║
║                                                  ║
║ Press [a] to approve, [r] to reject, [d] for     ║
║   detailed breakdown, [?] for help               ║
╚══════════════════════════════════════════════════╝
```
This is the summary tier. If you press `[d]`, the detailed breakdown appears:
```
--- DETAILED BREAKDOWN ---

Sub-task 1/5: "Read sales.csv"
  Risk: LOW
  Tools: file_read
  Depends on: nothing

Sub-task 2/5: "Parse CSV into data structure"
  Risk: LOW
  Tools: python_interpreter
  Depends on: 1

Sub-task 3/5: "Calculate summary statistics"
  Risk: LOW
  Tools: python_interpreter
  Depends on: 2

Sub-task 4/5: "Generate charts"
  Risk: MEDIUM
  Tools: matplotlib
  Depends on: 3
  Pre-mortem scenarios:
    - (Pessimist, MEDIUM): Chart generation fails if
      matplotlib is not installed.
      Mitigation: check for matplotlib before starting.

Sub-task 5/5: "Write output files to /home/user/reports/"
  Risk: HIGH
  Tools: file_write
  Depends on: 4
  Pre-mortem scenarios:
    - (Pessimist, HIGH): Overwrites existing files
      without confirmation.
      Mitigation: check for file conflicts first.
    - (Resource Analyst, MEDIUM): Output directory
      may not exist. Mitigation: create directory
      if missing.

Plan version: 1 (initial)
No prior revisions.

Press [a] to approve, [r] to reject, [b] to go back
```

**During Execution (seconds to minutes):**
```
[=] Executing plan...
[1/5] [OK] Read sales.csv (0.3s)
[2/5] [OK] Parse CSV into data structure (0.5s)
[3/5] [OK] Calculate summary statistics (0.2s)
[4/5] [OK] Generate charts (2.1s)
[5/5] [..] Write output files... (running)
```
Failed sub-tasks look different:
```
[3/5] [!!] Calculate summary statistics -- FAILED
       Error: KeyError -- column "sales_amount" not found.
       Retrying with different approach...
[3/5] [OK] Calculate summary statistics (retry 1, 0.3s)
```

**During Evaluation (a few seconds):**
```
[=] Evaluating results...
[+] Evaluation: SUCCESS -- all criteria met
```
Or if things went wrong:
```
[=] Evaluating results...
[!] Evaluation: PARTIAL -- 3 of 4 criteria met
    Failed: "Output should include profit margin column"
    Replanning (attempt 1 of 3)...
```
Or if there were no criteria to check:
```
[=] Evaluating results...
[!] Evaluation: UNEQUIVALENT -- no criteria defined
    Output was not evaluated against any criteria.
    Quality is unconfirmed.
```

### What "Waiting for Approval" Looks Like

The approval prompt (shown above) waits indefinitely. There is no timeout. JORDAN will not proceed until you press `a`, `r`, or a navigation key. If you walk away and come back hours later, the prompt is still there.

### What Happens When Something Goes Wrong

**During classification:** If JORDAN cannot decide which path to take, it defaults to the safest one. Uncertainty escalates UP: FAST becomes STANDARD becomes DEEP.

**During planning:** If the planner produces a nonsensical plan, the backbrief catches it (circular dependencies, dangling references). The plan is regenerated up to 2 times.

**During execution:** If a sub-task fails, JORDAN tries to fix it using progressively more aggressive strategies, without re-asking you unless absolutely necessary:
1. Just try again (temporary errors like network timeouts)
2. Try a fallback approach
3. Try a different method locally
4. Expand the scope of the fix
5. Replan globally
6. Ask you for help

Each replan can attempt up to 6 compensation levels internally. A single replan counts as 1 use of the FRAGO replan budget (max 3), but within that replan, JORDAN can try up to 6 different compensation strategies without consuming additional budget. The worst case is 3 replans x 6 compensation levels = 18 attempts before human escalation.

**During replanning:** If JORDAN's replans make things WORSE (the evaluation goes from PARTIAL to FAILURE), it detects this "degrading replan" pattern and escalates to you directly after 2 consecutive degradations, skipping any remaining compensation strategies.

**Ceilings exhausted:** Every safety mechanism has a hard limit. When a limit is reached, the system force-proceeds (for structural checks) or escalates to you (for execution failures). You will never see JORDAN loop forever.

### What Errors/Messages You Might Encounter

| Message | What It Means | What To Do |
|---------|---------------|------------|
| "I need more information before I can proceed..." | JORDAN detected a critical gap in its knowledge that would make the task fail. This is a feature, not a bug -- it is asking instead of guessing. | Provide the missing information. If you do not know it either, say so and JORDAN will note the uncertainty in the plan. |
| "This plan was force-accepted after 2 structural revision attempts." | The backbrief found problems but hit its ceiling. The plan may have unresolved structural issues. | Review the detailed breakdown carefully before approving. Ask JORDAN to explain the issues. |
| "Execution halted: branching factor exceeded limits." | A sub-task spawned too many new sub-tasks during execution. The plan's shape exploded. | JORDAN will replan with a simpler structure. If it happens repeatedly, narrow the scope of your request. |
| "Replanning has made the output worse (attempt 2 of 2 degrading)." | JORDAN's fixes are causing more problems than they solve. | You will be prompted for guidance. Provide a specific direction or accept the partial result. |
| "All execution strategies exhausted after 3 replan cycles." | JORDAN tried everything it knows and still cannot produce an acceptable result. | You will see a summary of what was tried and where it failed. You may need to redefine the task or accept a partial result. |
| "This output was not evaluated against any criteria." | The plan had no defined success criteria, so JORDAN cannot confirm quality. The output may be fine, but quality is unconfirmed. | For important tasks, consider rephrasing your request with clearer expectations. |
| "Your modifications change the original task significantly." | During approval, you altered the plan so much that it is now a fundamentally different task. | JORDAN asks whether to start fresh. Say yes if your needs changed; say no to proceed with the modified plan (flagged as higher risk). |

---

## 5. TROUBLESHOOTING -- What To Do If...

### The plan does not make sense
1. At the approval prompt, press `[d]` to see the detailed breakdown.
2. Look at the "Commander's Intent" section -- does it match what you asked for? If not, press `[r]` to reject and rephrase your request.
3. Look at the pre-mortem scenarios -- do any of them describe concerns that seem irrelevant? That is valuable signal: it means JORDAN misunderstood something about your request.
4. You can reject the plan and rephrase your request with more detail. JORDAN learns from plan rejections (the failure is recorded and used to tune future plans).

### JORDAN asks for more information (and why that is a feature)
JORDAN asks for more information when it detects a knowledge gap that would likely cause the task to fail. This is a **feature**, not an inconvenience. Without it, JORDAN would guess, and guessing on high-risk tasks produces wrong answers delivered confidently.

When JORDAN asks, it will tell you:
- What specific information is missing
- Which sub-tasks are affected
- Why the gap matters (what could go wrong without this information)

Your options:
- Provide the information (best). JORDAN resumes from where it paused.
- Say "I do not know" (acceptable). JORDAN notes the uncertainty and proceeds, flagging the risk in the approval briefing.
- Say "guess" (not recommended for high-risk tasks, but available). JORDAN will make an assumption explicitly noted in the plan.

### A step fails
Look at the error output. JORDAN will show you what failed and what it tried. The compensation ladder is automatic -- you do not need to intervene unless JORDAN reaches the "human escalation" level, at which point it will explicitly ask for your help.

If a step fails repeatedly, check:
1. Is the error about something you can fix (e.g., a missing file, a typo in a path)? Tell JORDAN.
2. Is the error about something JORDAN should be able to handle (e.g., a code syntax error)? JORDAN will keep trying the compensation ladder. If it exhausts all strategies, it will escalate to you.
3. Is the error about a fundamental misunderstanding of your request? Reject and rephrase.

### JORDAN tries the same thing twice
This should not happen. The compensation ladder enforces monotonic escalation -- each attempt must be a different strategy from the previous one. If you see JORDAN repeating the same approach with the same error, that is a bug. Report it.

### Nothing seems to be happening
Check what stage JORDAN is in:
- If you see `[..]`, a sub-task is running. Some sub-tasks (especially those making API calls or running long computations) can take minutes. The status line updates when the sub-task completes.
- If you see the approval prompt, JORDAN is waiting for you. It will wait forever. Press a key.
- If you see no output at all for more than 30 seconds during planning or evaluation, something may be stuck. Interrupt with Ctrl+C. On resume, JORDAN will pick up from its last checkpoint (completed sub-tasks are preserved; in-progress ones restart).

### You see a message you do not understand
JORDAN's messages are designed to be self-explanatory, but if one is confusing:
1. Look for it in the "Errors/Messages" table in Section 4 of this document.
2. If it is not there, note the exact text of the message and the stage it appeared in (classification, planning, execution, etc.).
3. Most status messages follow a pattern: `[=]` means working, `[+]` means success, `[!]` means warning, `[!!]` means error, `[..]` means in progress. The text after the symbol explains what is happening.

---

## 6. VISUAL FLOWCHART

The following is a precise numbered-node description of the JORDAN v2 pipeline. Every decision point (diamond), every state (rectangle), every escalation path (dashed line), and every ceiling limit is marked. A designer can turn this directly into a visual flowchart.

### Legend

```
[ RECTANGLE ] = Process/Action (JORDAN does something)
{ DIAMOND  } = Decision (JORDAN checks something and branches)
< TERMINAL > = Start or End state
-------->   = Normal flow (solid line)
- - - - ->  = Escalation/Exception flow (dashed line)
###         = Safety gate (Approval, Backbrief, Pre-Mortem, Branching)
```

### Full Pipeline Flowchart

```
                                    <START>
                                       |
                                       v
                               [ 1. CLASSIFY ]
                         LLM classifier: TRIVIAL /
                         MODERATE / COMPLEX
                                       |
                                       v
                          { 2. WHICH PATH? }
                          /        |         \
                    TRIVIAL    MODERATE    COMPLEX
                      /          |             \
                     v           v              v
              [FAST PATH]  [STANDARD PATH]  [DEEP PATH]
              (see below)  (see below)      (see below)
```

### FAST PATH Detail

```
<FAST PATH ENTRY>
       |
       v
[ F.0 SAFETY PRE-CHECK ]
Denylist pattern-match scan.
(Architecturally distinct from LLM
 classifier -- binary safety check,
 not a complexity judgment.)
       |
       v
{ F.0a DENYLIST MATCH? }
     /           \
   YES            NO
    |              |
    v              v
[ESCALATE TO     |
 STANDARD PATH]  |
(BINARY safety   |
 escalation)     |
    |             |
    v             v
<STANDARD>    [ F.1 FAST EXECUTE ]
              Model generates answer directly
              (parallel execution: NO)
              (human touchpoints: NONE)
                     |
                     v
              [ F.2 OUTPUT GUARDRAIL ]
              Rule-based scan checking:
               1. Dangerous content patterns
               2. Tool-call hallucination
                  (JSON blobs, XML tags, special tokens)
               3. Safety refusal phrases
                     |
                     v
              { F.3a DANGEROUS CONTENT OR }
              {    TOOL HALLUCINATION?     }
                   /              \
                 YES               NO
                  |                 |
                  v                 v
              [ F.5 REPLACE      { F.3b SAFETY }
               WITH SAFE          {  REFUSAL?  }
               FALLBACK ]         /         \
                  |             YES          NO
                  |              |            |
                  |              v            v
                  |       [ F.6 FLAG     [ F.4 APPEND
                  |        AS REFUSAL,    DISCLAIMER ]
                  |        PASS THROUGH ]     |
                  |              |            |
                  v <--------------------------
                  |
                  v
              [ F.7 SYNTHESIZE (pass-through) ]
                  |
                  v
              [ F.8 EVALUATE (always SUCCESS) ]
                  |
                  v
                <DONE -- Return answer to user>
                  |
              (Duration: 2-10 seconds)
```

### STANDARD PATH Detail

```
<STANDARD PATH ENTRY>
       |
       v
[ S.1 PLAN ]
Generate plan: Commander's Intent, sub-tasks, DAG, tools
Plan versioning: plan_version starts at 1, incremented on
  each regeneration. plan_checksum (SHA-256) tracks content.
       |
       v
       |
  ╔══════════════════════════════════════╗
  ║ ### BACKBRIEF GATE (max 2 cycles) ###║
  ║ Counter: backbrief_revision_count   ║
  ║ (independent from premortem_cycle)  ║
  ╚══════════════════════════════════════╝
       |
       v
[ S.2 BACKBRIEF ]
Check plan structure:
 - Circular dependency detection
 - Hidden coupling detection (DSM)
 - Dangling reference check
       |
       v
{ S.3 STRUCTURE VALID? }
     /              \
   YES               NO
    |                 |
    v                 v
    |          { S.4 REVISION COUNT < 2? }
    |              /              \
    |            YES               NO
    |             |                 |
    |             v                 v
    |     [Regenerate plan     [ FORCE-PASS ]
    |      with BACKBRIEF       Flag: backbrief_forced = true
    |      flags as context]    Log warning
    |      (carries forward      (consumed by APPROVAL,
    |       backbrief_revision    PREMORTEM, EVALUATE,
    |       _count -- does NOT    and AUDIT TRAIL)
    |       reset counter)       |
    |             |                 |
    |             v                 |
    |       (return to S.1)         |
    |                               |
    v <-----------------------------
    |
    v
[ S.5 RESEARCH (cache lookup) ]
Check skill library for relevant past experience.
Validate tool recommendations against current registry.
Detect knowledge gaps (cache_miss vs. genuine_gap).
       |
       v
{ S.6 CRITICAL GAPS? }
(genuine knowledge gaps affecting HIGH/CRITICAL sub-tasks)
     /              \
   YES               NO
    |                 |
    v                 |
[ PIPELINE INTERRUPT ] |
[ ASK USER for         |
  missing info]         |
◉ (checkpoint --        |
   pipeline pauses      |
   until user responds) |
    |                   |
    v (user responds)   |
[RESUME from RESEARCH]  |
(3 user response paths: |
  - Provide info: resume|
  - "I don't know": flag|
    uncertainty, resume |
  - "Guess": record     |
    assumption, resume) |
    |                   |
    v <------------------
    |
    v
[ S.7 RISK ASSESSMENT ]
LLM classifies each sub-task:
LOW / MEDIUM / HIGH / CRITICAL
       |
       v
       |
  ╔════════════════════════════════════════╗
  ║ ### PRE-MORTEM GATE (max 2 cycles)  ###║
  ║ Counter: premortem_cycle_count       ║
  ║ (independent from backbrief_revision) ║
  ╚════════════════════════════════════════╝
       |
       v
[ S.8 PRE-MORTEM ]
Multiple personas generate failure scenarios
(4 standard: Pessimist, Optimist, Devil's Advocate,
 Resource Analyst; +1 DEEP-only: Domain Expert).
Each scenario: description, severity, likelihood.
Scenarios archived per plan_checksum (not appended
across plan versions).
If fatal flaw (HIGH+ severity AND >50% likelihood):
  -> Plan regenerated (return to S.1 with PREMORTEM flags;
     re-runs through BACKBRIEF; backbrief_revision_count
     carries forward, NOT reset)
       |
       v
{ S.9 FATAL FLAWS FOUND? }
     /              \
   YES               NO
    |                 |
    v                 v
{ S.10 CYCLE COUNT < 2? }    |
  /              \           |
YES               NO         |
 |                 |         |
 v                 v         |
[Regenerate        [FORCE-PASS    |
 plan with         Flag unresolved |
 PREMORTEM         scenarios in   |
 persona flags]    approval]      |
 |                 |              |
 v                 |              |
(return to S.1)    |              |
                    |              |
                    v <------------
                    |
                    v
[ S.11 BRANCHING FACTOR MONITOR ]
Static DAG analysis:
 - Fan-out (branching factor b: b >= 1 -> halt)
 - Max depth (> max_depth, default 10 -> halt)
       |
       v
{ S.12 BRANCHING VIOLATION? }
     /              \
   YES               NO
    |                 |
    v                 |
[HALT -> escalate     |
 to REPLAN with       |
 structural flag]     |
    |                 |
    v                 |
    |                 |
    v <----------------
    |
    v
[ S.13 RISK FUSION ]
Reconcile risk signals per sub-task:
 final_risk = max(
   risk_assessment_level,
   max(premortem_severities),
   escalate_if_safety_critical_domain
 )
(Branching violations route through BRANCHING MONITOR ->
 REPLAN path directly; risk fusion does NOT process
 stop signals -- per DD-008.)
       |
       v
       |
  ╔══════════════════════════════════════╗
  ║ ### APPROVAL GATE ###              ║
  ╚══════════════════════════════════════╝
       |
       v
{ S.14 ANY HIGH or CRITICAL? }
     /              \
   YES               NO
    |                 |
    v                 v
[PRESENT BRIEFING   [SKIP APPROVAL]
 Tier 1: Summary     Proceed silently]
 Tier 2: Details
 (expandable)
 Includes backbrief_forced
 banner if applicable]
    |
    v
{ S.15 USER DECISION }
   /      |      \
APPROVE  REJECT  ASK QUESTIONS
  |       |         |
  v       v         v
  |    <STOP>    [ANSWER and
  |    Return       re-present
  |    nothing]     briefing]
  |
  v
[ S.16 EXECUTE ]
DAG scheduler dispatches sub-tasks.
Isolated Subgraph per sub-task.
Parallel up to concurrency_limit (default 4).
Compensation ladder per sub-task:
  1. reprompt
  2. catch_fallback
  3. local_compensation
  4. radius_expansion
  5. global_replan
  6. human_escalation
(monotonic: only goes UP the ladder)

Runtime branching monitor active:
 sub-tasks dynamically spawning new sub-tasks?
       |
       v
{ S.16a RUNTIME SPAWN COUNT > }
{       original x 2 ?          }
     /              \
   YES               NO
    |                 |
    v                 v
[HALT -> escalate    |
 to REPLAN]          |
    |                |
    v <---------------
    |
    v
[ S.17 SYNTHESIZE ]
Merge sub-task results.
Type-aware merge (text, JSON, code, binary, mixed).
Conflict detection.
Format heterogeneity handling.
       |
       v
[ S.18 EVALUATE ]
Compare output against Commander's Intent criteria.
Result: SUCCESS / PARTIAL / FAILURE / UNEQUIVALENT
(Evaluation results cached per invocation to prevent
 LLM nondeterminism from flipping between replan cycles.)
       |
       v
{ S.19 RESULT? }
  /       |        \         \
SUCCESS  PARTIAL  FAILURE  UNEQUIVALENT
  |        |          |         |
  v        v          v         v
  |        |          |    (routed like
  |        |          |     SUCCESS -- no
  |        |          |     criteria to fail
  |        |          |     against, so no
  |        |          |     replan triggered.
  |        |          |     Output annotated:
  |        |          |     "quality unconfirmed")
  |        |          |         |
  |        |          |         |
  |        |          |         v
  |        |          |         |
  |        |          |         |
  |        |   ╔══════════════════════════════════════╗
  |        |   ║ ### FRAGO REPLAN LOOP (max 3)    ###║
  |        |   ║ replan_count (FRAGO iterations)   ║
  |        |   ║ compensation_level (within 1 replan)║
  |        |   ╚══════════════════════════════════════╝
  |        |          |
  |        |          v
  |        |   { S.20 REPLAN COUNT < 3? }
  |        |      /              \
  |        |    YES               NO
  |        |     |                 |
  |        |     v                 v
  |        | [ S.21 REPLAN ]   [ESCALATE TO USER]
  |        | Delta replan:      "All strategies exhausted.
  |        | only modify         Here is what I tried:
  |        | failed sub-tasks.   [summary].
  |        | Compensation        Here is the best partial
  |        | ladder available.   result."
  |        |     |                 |
  |        |     v                 v
  |        | [ S.22 DELTA        <DONE -- Return
  |        |   VALIDATION ]       partial result>
  |        | Lightweight 3-check:
  |        |  1. DAG cycles
  |        |  2. Branching factor
  |        |  3. Risk re-classify
  |        |     |
  |        |     v
  |        | { S.23 DELTA VALID? }
  |        |    /           \
  |        |  YES           NO
  |        |   |             |
  |        |   v             v
  |        |   |      { S.24 DEGRADING? }
  |        |   |      (2 consecutive worse
  |        |   |       evaluations?)
  |        |   |        /            \
  |        |   |      YES             NO
  |        |   |       |               |
  |        |   |       v               v
  |        |   |  [ESCALATE TO    [ESCALATE
  |        |   |   USER: "Fixes    COMPENSATION]
  |        |   |   are making       Try next
  |        |   |   things worse.    ladder level]
  |        |   |   Skips remaining  |
  |        |   |   compensation     |
  |        |   |   ladder levels.]  |
  |        |   |       |           |
  |        |   |       v           v
  |        |   |       |     (return to S.21
  |        |   |       |      with higher level)
  |        |   |       |
  |        |   v <------
  |        |   |
  |        |   v
  |        | [ S.25 RESEARCH cache re-query ]
  |        | [ S.26 RISK re-classify changed sub-tasks ]
  |        | [ S.27 RE-EXECUTE ]
  |        |   (back to S.16 for changed sub-tasks only)
  |        |       |
  |        |       v
  |        | [ S.28 RE-SYNTHESIZE ]
  |        | [ S.29 RE-EVALUATE ]
  |        |   (return to S.19)
  |        |
  |        |
  v <-------
  |
  v
[DONE -- Return final output + quality report to user]
```

### DEEP PATH Detail

The DEEP path follows the STANDARD path flowchart exactly, with these modifications to specific nodes:

```
<DEEP PATH ENTRY> (from CLASSIFY, complexity = COMPLEX)
       |
       v
[D.1 PLAN -- MULTI-COA]
Generate MULTIPLE Courses of Action (n_coas=3).
Compare and select best (or present options).
MAKER decomposition: break sub-tasks to smallest verifiable units.
       |
       v
[D.2 PRE-MORTEM -- EXPANDED PERSONAS]
Standard personas active (same 4 as STANDARD path):
 - Pessimist
 - Optimist
 - Devil's Advocate
 - Resource Analyst (memory, storage, API, timeout checks)
Added for DEEP path only:
 - Domain Expert (subject-matter evaluation of technical
   assumptions and domain-specific constraints)
   (Note: Resource Analyst and Devil's Advocate are already
    in the standard set; neither is new to DEEP.
    Total personas: 4 standard + 1 DEEP = 5.)
       |
       v
[D.3 APPROVAL -- ALWAYS ACTIVE]
Regardless of risk level, briefing ALWAYS presented.
Tier 2 detail shown by DEFAULT (not hidden).
If multiple COAs: present trade-off summary.
       |
       v
[D.4 EXECUTE -- SEQUENTIAL DEFAULT]
Default: sequential execution (not parallel).
Parallel only if explicitly approved during planning.
       |
       v
(Remaining nodes identical to STANDARD path)
```

### Ceiling/Limit Summary (for flowchart labels)

```
CEILING                         MAX     BEHAVIOR WHEN HIT
-------                         ---     ------------------
Backbrief revisions             2       Force-pass; flag "backbrief_forced = true"
Pre-mortem cycles               2       Force-pass; flag unresolved scenarios in approval
FRAGO replan cycles             3       Escalate to user with partial result
Compensation ladder levels      6       Human escalation (pipeline pauses)
Degrading replan threshold      2       Human escalation ("fixes making things worse");
                                        skips remaining compensation ladder levels
Max DAG depth                  10       Structural halt (escalate to REPLAN)
Branching factor threshold      1.0     Structural halt (escalate to REPLAN)
Sub-task spawn ceiling  original x 2    Runtime halt (trigger REPLAN)
Concurrent sub-tasks            4       Batched execution (wait for slot)
```

### Escalation Path Map

```
FAST PATH - - - -> STANDARD PATH
  (trigger: denylist pattern match on input)

STANDARD PATH - - - -> DEEP PATH
  (trigger: CLASSIFY detects complex/novel/safety-critical)

ANY PATH - - - -> USER ESCALATION
  (trigger: compensation ladder level 6, ceiling exhausted,
           2 consecutive degrading replans, or critical
           knowledge gap affecting CRITICAL sub-task)

EXECUTE - - - -> REPLAN (FRAGO loop)
  (trigger: sub-task failure, runtime branching halt,
           runtime spawn count exceeding original x 2)

REPLAN - - - -> EXECUTE (FRAGO loop iteration)
  (trigger: delta plan generated and validated)

REPLAN - - - -> USER ESCALATION
  (trigger: FRAGO ceiling hit, degrading replan detected)
```

---

*End of JORDAN v2 ELI5 Flowchart Document -- FINAL v2 (all 29 arbitration findings incorporated).*