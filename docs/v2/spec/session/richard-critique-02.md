# TACTICAL CRITIQUE -- Karl's ELI5 Flowchart (karl-draft-02.md)

**Author:** Richard the Lionheart
**Target:** karl-draft-02.md ("JORDAN v2 -- How It Works (ELI5 Flowchart Document)")
**Reference:** richard-revision-01.md (Granular Implementation Specification v2)
**Date:** 2026-05-25
**Status:** Critique delivered. No sugar-coating.

---

## 0. EXECUTIVE SUMMARY

Karl's document is structurally sound, well-organized, and genuinely accessible. The flowchart in Section 6 is the strongest part -- precise enough for a designer to render. However, the document contains **7 factual inaccuracies**, **11 omissions of architecturally-significant elements**, **4 internal inconsistencies**, and **3 visualization defects**. The FAST path description is the weakest section (multiple inaccuracies about guardrails and classification). The flowchart ceiling table disagrees with the flowchart's own routing in one place. The DEEP path persona description is misleading.

**Overall verdict: REVISE** -- the skeleton is good, but the flesh has too many wounds to leave standing. I name every one below.

---

## 1. ACCURACY -- Every Divergence from the Spec

### 1.1 FAST Path: "No safety checks beyond the initial pattern scan" (line 28)

**Karl writes:**
> "JORDAN generates an answer directly. No planning, no research, no safety checks beyond the initial pattern scan."

**Spec says (Section 2.5.A, 2.5.B, 2.5.C, 2.5.D):**
The FAST path has a **mandatory output guardrail** after generation and before SYNTHESIZE. It scans for:
1. Dangerous content patterns.
2. Tool-call hallucination (JSON function-call blobs, XML `<function>` tags, special tokens like `<|python_tag|>`).
3. Safety refusal detection (separate from hedging).

If dangerous content or tool-call hallucination is detected, the output is **replaced** with a safe fallback: "I encountered an issue generating a response. Please try rephrasing your question."

**Correct:** The output guardrail exists and is a safety check. Karl's statement "no safety checks beyond the initial pattern scan" is false. The document tells a non-technical stakeholder that the FAST path has no output protection, which would cause them to distrust the system's safety claims.

---

### 1.2 FAST Path: Disclaimer text differs (line 29)

**Karl writes:**
> "This is a quick answer generated without research or tool access. For complex topics requiring deeper analysis, I can run a full investigation."

**Spec says (Section 2.5.C):**
> "This is a quick answer generated without research or tool access. For complex topics requiring **verification or** deeper analysis, I can run a full investigation."

The word "verification" is missing. While minor, it changes the emphasis: the spec says the user should verify (the answer may be wrong), not just go deeper. A stakeholder reading Karl's version would not understand that the disclaimer is also a **truthfulness warning**, not just a scope warning.

**Correct:** Karl's version drops "verification" from the disclaimer. The spec includes it.

---

### 1.3 FAST Path: Classification conflates denylist with LLM classifier (line 26-27)

**Karl writes:**
> "JORDAN reads your question. It checks it against a list of known-dangerous patterns (like 'delete all files'). If nothing dangerous matches, and the question looks simple, it takes the FAST path."

**Spec says (Section 1.1, 1.8, 1.5.A):**
There are **two architecturally distinct mechanisms**:
1. **LLM classifier (CLASSIFY node)** -- determines TRIVIAL / MODERATE / COMPLEX for path selection.
2. **Denylist (safety pre-filter)** -- a BINARY safety check on the FAST path. If triggered, it escalates FAST to STANDARD. "The denylist's scope is limited to FAST path escalation; it does not participate in STANDARD/DEEP routing."

Karl describes them as a single step. The stakeholder reading this would not know that the denylist and classifier are separate systems with different failure modes, different tuning mechanisms, and different architectural purposes.

**Correct:** The denylist is a safety pre-filter that can escalate FAST to STANDARD. The LLM classifier determines path selection. They are not the same step.

---

### 1.4 FAST Path: Output guardrail binary decision misses safety refusal pass-through (Flowchart F.3)

**Karl's flowchart (lines 441-444):**
```
{ F.3 OUTPUT CLEAN? }
     /           \
   YES            NO
    |              |
    v              v
[ F.4 APPEND    [ F.5 REPLACE WITH ]
 DISCLAIMER ]    SAFE FALLBACK ]
```

**Spec says (Section 2.5.A, 2.5.D):**
There are **three** outcomes from the output guardrail, not two:
1. Clean: append disclaimer and proceed.
2. Dangerous content / tool-call hallucination: replace with safe fallback.
3. **Safety refusal detected:** the response is **passed through** to the user (not replaced), flagged with `safety_refusal_detected = True`.

The flowchart's binary YES/NO diamond cannot represent three outcomes. The safety refusal path is silently dropped, which means a non-technical stakeholder looking at the flowchart would believe that ANY flagged output gets replaced -- but safety refusals do not.

**Correct:** The flowchart needs three branches from F.3, or a different representation (e.g., two successive diamonds: "dangerous content?" then "safety refusal?").

---

### 1.5 FAST Path: Garbled output check is not in the spec (line 28)

**Karl writes:**
> "making sure the answer does not contain anything dangerous, any garbled internal formatting"

**Spec says (Section 2.5.A, 2.5.B):**
The output guardrail checks for three specific things: dangerous content patterns, tool-call hallucination patterns, and safety refusal phrases. "Garbled internal formatting" is NOT in the spec. The spec's concept of "garbled" is specifically tool-call hallucination (e.g., JSON function-call blobs, XML `<function>` tags). Karl's text creates a vague expectation that the guardrail will catch any garbled output, which is not architecturally supported.

**Correct:** The output guardrail catches specific tool-call formatting patterns, not generic "garbled" text.

---

### 1.6 Persona False-Positive Threshold: One value vs. two tiers (line 151)

**Karl writes:**
> "If a persona cries wolf too often (more than 50% false alarms), it is disabled until reviewed."

**Spec says (Section 7.5.C):**
There are **two thresholds**:
1. `max_false_positive_rate` (configurable, default **0.3**) -- persona flagged for **review** (not disabled).
2. `max_false_positive_critical` (**0.5**) -- persona **disabled** until reviewed.

Karl presents only the critical threshold (50%), omitting the warning threshold (30%). A stakeholder relying on this document would believe personas continue operating until 50% false alarms, when in reality they are flagged at 30%.

**Correct:** Two thresholds exist: 30% flags for review, 50% disables.

---

### 1.7 DEEP Path: "Expanded Persona Set" includes Devil's Advocate incorrectly (line 103)

**Karl writes:**
> "The pre-mortem uses all available personas, including the Resource Analyst (checks for memory limits, API rate limits, timeout constraints) and the Devil's Advocate (challenges the plan's unstated assumptions)."

**Spec says:**
The standard persona set for STANDARD path already includes Pessimist, Optimist, and Devil's Advocate. The **only additional** persona for DEEP path is the **Resource Analyst**. Karl's text implies both Resource Analyst AND Devil's Advocate are "expanded," which is incorrect -- Devil's Advocate is always active.

**Correct:** Only Resource Analyst is new in DEEP. Pessimist, Optimist, and Devil's Advocate are already active in the standard persona set.

---

## 2. COMPLETENESS -- What is Missing

### 2.1 Runtime Branching Spawn Monitor: No decision point in EXECUTE (Flowchart S.16)

**Spec says (Section 8.1, 8.5.C):**
The branching factor monitor has **two components**:
1. Static DAG analyzer (pre-execution) -- shown in Karl's flowchart at S.11.
2. **Runtime spawn monitor** (during EXECUTE) -- tracks dynamic sub-task creation. If total sub-tasks (original + spawned) exceeds `max_total_sub_tasks` (default = original * 2), execution halts and routes to REPLAN.

Karl's design doc mentions the runtime monitor in prose (lines 173-174) but the flowchart shows only "Runtime branching monitor active" as a label in S.16 with **no decision diamond** and **no route to REPLAN**. A designer rendering this flowchart would not know what happens when the runtime monitor triggers. The runtime monitor might as well not exist for flowchart purposes.

**Missing:** A decision point inside EXECUTE for runtime spawn detection, with a dashed escalation line to REPLAN.

---

### 2.2 UNEQUIVALENT Routes Like SUCCESS -- Flowchart Says FRAGO (Flowchart S.19)

**Karl's flowchart (lines 649-654):**
```
{ S.19 RESULT OK? }
  /       |        \
SUCCESS  PARTIAL  FAILURE/UNEQUIVALENT
  |        |          |
  v        v          v
  |        |     (treat UNEQUIVALENT
  |        |      like SUCCESS for routing,
  |        |      but annotate output)
```

**Spec says (Section 12.7):**
> "Updated: UNEQUIVALENT routes like SUCCESS (output proceeds to user, annotated)."

But the flowchart shows FAILURE and UNEQUIVALENT on the same branch, which goes to FRAGO replan. The annotation inside the FAILURE box says "treat UNEQUIVALENT like SUCCESS for routing" -- but this contradicts the visual routing, which goes to FRAGO.

**Correct:** UNEQUIVALENT should route to DONE (same as SUCCESS), not FRAGO. The annotation and the routing arrow disagree.

---

### 2.3 Ceiling Table Says PLAN, Flowchart Says REPLAN for Branching (line 770 vs S.12)

**Karl's ceiling table (lines 770-771):**
> "Max DAG depth: 10 -- Structural halt (return to PLAN)"
> "Branching factor threshold: 1.0 -- Structural halt (return to PLAN)"

**Karl's flowchart (S.11-S.12):**
```
[ S.11 BRANCHING FACTOR MONITOR ]
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
```

The ceiling table says "return to PLAN," but the flowchart says "escalate to REPLAN." These are different nodes with different behaviors (PLAN = full regeneration, REPLAN = delta replan). Karl's own document contradicts itself.

**Spec says (Section 8.7):**
> "Triggers REPLAN if halt."

The flowchart is correct; the ceiling table is wrong. But this internal inconsistency would confuse a designer.

---

### 2.4 Research/Critical Gaps: No Pipeline Pause in Flowchart (S.6)

**Spec says (Section 5.5.B):**
When genuine knowledge gaps affecting HIGH/CRITICAL sub-tasks are found, **"the pipeline pauses at RESEARCH with an interrupt"** and waits for user input. The user responds, and the pipeline resumes from RESEARCH.

**Karl's flowchart (S.6):**
```
{ S.6 CRITICAL GAPS? }
     /              \
   YES               NO
    |                 |
    v                 |
[ASK USER for          |
 missing info]         |
    |                 |
    v                 |
    |                 |
    v <----------------
    |
    v
[ S.7 RISK ASSESSMENT ]
```

The "ASK USER" box shows no pause/checkpoint, no wait state, no user response path (provide info / say "I don't know" / say "guess"). The flowchart implies JORDAN asks and immediately continues. A designer would not know this is an interrupt with checkpoint-and-resume semantics.

**Missing:** Pipeline interrupt symbol, user response branches, resume-from-RESEARCH path.

---

### 2.5 Plan Versioning and Checksum -- Absent

**Spec says (Section 3.4, 3.5.B):**
Every plan has `plan_version: int` (incremented on regeneration) and `plan_checksum: str` (SHA-256 of plan content). PREMORTEM archives scenarios by `plan_checksum`. The flowchart mentions `plan_version = 1 or incremented` in S.1 but `plan_checksum` is not mentioned anywhere, and the version-only mention has no downstream effect. A reader cannot tell what plan_version actually does.

**Missing:** Explanation of plan versioning, checksum, and why it matters (scenario archiving, revision history).

---

### 2.6 Compensation Ladder vs. Replan Count Interaction

**Spec says (Section 13.5.B):**
The system has two independent counters:
- `compensation_level` (max 6) -- tracks escalation within ONE replan attempt.
- `replan_count` (max 3) -- tracks total FRAGO loop iterations.

A single replan can attempt 6 compensation strategies without consuming additional replan budget. Worst case: 3 replans * 6 levels = 18 attempts before human escalation.

Karl's text (line 75) says "This loop can repeat up to 3 times total" with no mention of the 6 internal compensation levels per replan. The flowchart shows the compensation ladder in S.16 but doesn't show that the ladder resets per replan, or that the ladder and the replan counter interact.

**Missing:** The two-tier escalation model (compensation within replan, replan count across loop).

---

### 2.7 Degrading Replan Detection -- Not in Flowchart

**Spec says (Section 13.5.C):**
After 2 consecutive degrading replans, the system escalates directly to `human_escalation`, skipping remaining compensation ladder levels.

Karl mentions this in the error messages table (line 333) but the flowchart (S.24) does show the degrading check. Actually, wait -- the flowchart DOES show S.24 DEGRADING? at lines 692-701, with ESCALATE TO USER on the YES branch and ESCALATE COMPENSATION on the NO branch. This is present. I stand corrected -- but it's worth noting that the flowchart's S.24 degrades path says "ESCALATE TO USER: 'Fixes are making things worse'" but doesn't show that the escalation SKIPS remaining compensation levels. The NO path shows "ESCALATE COMPENSATION -- Try next ladder level" which is correct for non-degrading failures. But the degrading path (YES) should say "skips remaining compensation levels" for precision.

---

### 2.8 Isolated-State Subgraph Execution -- Absent

**Spec says (Section 10.1, 10.5):**
Each sub-task executes as an independent LangGraph Subgraph with its own state schema and checkpointer. The spec treats this as one of the three critical design decisions (DD-001).

Karl's execution description (line 69) says "Each sub-task runs in its own isolated workspace so they cannot interfere with each other." This is directionally correct but gives no indication of **how** this isolation works (Subgraphs, `Send()`/`Join()`, independent checkpointing). For an ELI5 document this may be acceptable, but for a flowchart that a designer must render, the absence of Subgraph boundaries is a gap.

**Acceptability:** Borderline. I lean toward acceptable for ELI5 but flagging it for the record.

---

### 2.9 Backbrief_forced Flag Consumers

**Spec says (Section 4.5.A):**
The `backbrief_forced = True` flag is consumed by:
1. APPROVAL GATE (shows banner about unresolved issues).
2. PREMORTEM (passed as persona context).
3. EVALUATE (includes note about unresolved issues).
4. AUDIT TRAIL.

Karl's flowchart shows "Flag: backbrief_forced = true" in the force-pass box but never shows what consumes it. The approval gate diagram in Section 4 does not include the backbrief_forced banner. A stakeholder would see the flag set and never see it used.

---

### 2.10 Skill Library Details -- Absent

The entire Section 14 of the spec (template decay function, administrative interface, staleness checks, tenant filtering, failure-pattern lifecycle, write-ahead queue) is missing from Karl's document. For an ELI5 document this is arguably appropriate -- the skill library is an internal component. However, the template decay mechanism (spec 14.5.A) affects how plans are generated and thus affects the user experience indirectly. The write-ahead queue (14.5.F) ensures no silent data loss. Both are safety-relevant infrastructure.

**Acceptability:** I accept the omission for ELI5 scope, but it should be documented in a companion "internal architecture" document.

---

### 2.11 Checkpoint/Resume Architecture

**Spec says (Section 10.5):**
On interruption, completed Subgraphs are checkpointed and do not re-execute. In-progress Subgraphs restart from their last checkpoint within the Subgraph.

Karl's troubleshooting section (line 377) mentions "On resume, JORDAN will pick up from its last checkpoint (completed sub-tasks are preserved; in-progress ones restart)" -- this is in the document. So checkpoint/resume IS mentioned in prose. But it's not in the flowchart, and the flowchart's EXECUTE node (S.16) doesn't show checkpoint boundaries.

---

## 3. INTERNAL INCONSISTENCIES

### 3.1 Ceiling Table vs. Flowchart: Branching Returns (Table line 770 vs S.12)

Already documented in 2.3 above. Ceiling table says "return to PLAN." Flowchart says "escalate to REPLAN." Spec says REPLAN. The flowchart route is correct; the ceiling table is wrong. Both appear in Karl's Section 6.

---

### 3.2 Denylist Pre-Filter vs. Classification: No Consistent Description

In Section 2 (FAST Path), Karl describes the denylist as if it is part of classification. In Section 6 flowchart (line 408-409), CLASSIFY is shown as "Read request, check denylist, determine complexity" -- which also conflates them. The spec explicitly separates them.

---

### 3.3 Runtime Monitor Mentioned in Prose, Missing from Flowchart

Lines 173-174 describe the runtime spawn monitor. But the flowchart's branching factor section (S.11-S.12) only shows the static analyzer. The runtime monitor is referenced in S.16's label ("Runtime branching monitor active") but with no decision point or routing. The design doc says it exists; the flowchart does not render its behavior.

---

## 4. VISUALIZATION DEFECTS

### 4.1 F.3 OUTPUT CLEAN? -- Binary Decision Cannot Represent Three Outcomes

Already documented in 1.4. The flowchart needs either two successive diamonds or a three-way branch.

---

### 4.2 PREMORTEM Force-Pass: No Backbrief Re-Run Shown

**Spec says (Section 7.5.E):**
When PREMORTEM triggers plan regeneration, the regenerated plan goes through BACKBRIEF again. The flowchart shows S.9 FATAL FLAWS? -> YES -> S.10 CYCLE COUNT < 2? -> YES -> [Regenerate plan] -> (return to S.1). This return to S.1 correctly goes back through BACKBRIEF. So this IS correct. Good.

But when PREMORTEM force-passes (S.10 NO -> FORCE-PASS), the flowchart doesn't show what happens to the `backbrief_revision_count`. After a PREMORTEM force-pass, if BACKBRIEF previously used 1 of its 2 revisions, does the backbrief_revision_count reset? The spec says the counters are independent, but the flowchart doesn't show that PREMORTEM's regeneration triggers a FRESH BACKBRIEF with the existing `backbrief_revision_count` (not reset). A designer would not know whether the counter resets.

Actually, the spec (4.7) says explicitly: "If `backbrief_revision_count < 2`, the regenerated plan MAY be rejected again by BACKBRIEF independently from PREMORTEM's cycle count." This means the backbrief_revision_count IS carried forward (not reset). The flowchart doesn't show this.

---

### 4.3 PREMORTEM Force-Pass: Route Goes to BRANCHING MONITOR, Not Research

In the flowchart, when PREMORTEM force-passes (S.10 NO -> FORCE-PASS), the route goes back to S.5 RESEARCH (via the arrow from the force-pass box). Wait, let me trace more carefully...

Lines 540-562:
```
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
[ S.5 RESEARCH (cache lookup) ]
```

Wait, the force-pass from S.10 goes to S.5 RESEARCH. The NO branch from S.9 also goes to S.5. So PREMORTEM never skips RESEARCH. This is correct per the spec -- BACKBRIEF and research precede PREMORTEM.

But there's an interesting issue: after a PREMORTEM-triggered regeneration at S.10 YES -> return to S.1 -> S.2 BACKBRIEF -> S.3 -> ... -> S.8 PREMORTEM again. But RESEARCH is skipped on the second pass through (because the route is S.1 -> S.2 -> S.3 -> S.5? No, S.1 goes to BACKBRIEF, and S.3 YES goes to S.5. So RESEARCH IS re-run. But the spec doesn't say RESEARCH re-runs on PREMORTEM regeneration. Let me check...

The spec (5.7) says RESEARCH runs after BACKBRIEF. So the flowchart's routing is correct -- after a PREMORTEM regeneration, the plan goes through BACKBRIEF again (S.2), and if BACKBRIEF passes, through RESEARCH (S.5) again. This matches the spec topology. Good.

---

## 5. VERDICT PER SECTION

### Section 1 -- THE BIG PICTURE
**Verdict: ADOPT**

Clean, accurate, sets the right tone. The only risk is the implied linearity (classify -> build -> check -> execute) which is a simplification but acceptable for big picture.

---

### Section 2 -- THE THREE PATHS
**Verdict: REVISE**

**Specific changes needed:**
- **FAST Path, line 28:** Remove "no safety checks beyond the initial pattern scan." Add: "Before showing you the answer, JORDAN runs a final scan on the output itself, checking for dangerous content, garbled internal formatting (like raw AI metadata leaking through), and any refusal to answer. If dangerous content or internal formatting leaks are found, the answer is replaced with a safe message."
  
  (Note to Karl: the output guardrail IS a safety check. Saying there are none is the wrong message.)

- **FAST Path, line 29:** Fix disclaimer to include "verification": "This is a quick answer generated without research or tool access. For complex topics requiring verification or deeper analysis, I can run a full investigation."

- **FAST Path, lines 26-27:** Clarify that CLASSIFY and denylist are separate steps: "First, JORDAN's classifier decides which path best fits your question. If the classifier picks the FAST path, a separate safety pattern scanner checks for known-dangerous patterns — like commands that would delete files. If nothing dangerous matches, JORDAN proceeds with the fast answer."

- **STANDARD Path, line 69:** Add a note about the runtime branching monitor inside execution: "During execution, JORDAN also monitors whether any sub-task unexpectedly spawns new sub-tasks. If the total number explodes beyond twice the original count, execution pauses and JORDAN rebuilds the plan."

- **DEEP Path, line 103:** Fix persona description: "The pre-mortem uses all available personas — Pessimist, Optimist, Devil's Advocate — plus a new Resource Analyst that checks for memory limits, API rate limits, timeout constraints, and other resource bottlenecks."

---

### Section 3 -- THE SAFETY FEATURES
**Verdict: REVISE**

**Specific changes needed:**
- **Approval Gate, line 121:** Add clarification: "The gate triggers based on JORDAN's risk assessment of each sub-task, not just on what the operation looks like. Writing a file might be LOW risk if it's a temporary output; deleting files would be HIGH or CRITICAL."

- **Risk Classification, line 151:** Change the false-positive threshold description: "Each persona's accuracy is tracked over time. If a persona's false-alarm rate exceeds 30%, it is flagged for review. If it exceeds 50%, the persona is disabled until reviewed. This ensures personas stay useful and don't cry wolf."

- **Branching Factor Monitor, line 169:** Fix the branching factor description: "How many sub-tasks run in parallel at any given moment. If at any point in the plan, sub-tasks spawn 1 or more child sub-tasks (a branching factor of 1 or above), the plan is halted. A factor of exactly 1 means a simple chain (each step depends on the previous), which is also halted if deeper than 10 steps."

---

### Section 4 -- WHAT THE USER SEES
**Verdict: ADOPT** with one note

**Note:** The approval prompt format (lines 209-273) is the strongest part of this section. The user-facing error table (lines 328-338) is comprehensive and accurate. The only concern is line 307: "There is no timeout" — the spec does not explicitly confirm this. If the spec changes to add a timeout, this must be updated. Flag for tracking, not a change request now.

---

### Section 5 -- TROUBLESHOOTING
**Verdict: ADOPT**

Clean, practical, well-structured. No inaccuracies. The "What To Do If" format is effective for the audience. The explanation of why JORDAN asks for more information (line 350-351) is particularly well-written.

---

### Section 6 -- VISUAL FLOWCHART
**Verdict: REVISE**

**Specific changes needed:**

1. **F.3 OUTPUT CLEAN?** -- Replace the binary diamond with two successive decisions:
   - First diamond: "Dangerous content or tool hallucination?" YES → replace with safe fallback. NO → next diamond.
   - Second diamond: "Safety refusal detected?" YES → flag and pass through. NO → append disclaimer.

2. **S.6 CRITICAL GAPS?** -- Add pipeline interrupt symbol (a clock/hand icon is standard) between ASK USER and S.7. Show three user response branches: "Provide info (resume)," "I don't know (proceed with flag)," "Guess (proceed with assumption noted)."

3. **S.12 BRANCHING VIOLATION?** -- Fix the ceiling table to say "REPLAN" instead of "PLAN" (line 770-771). Or, if the intent is to return to PLAN, fix the flowchart to show PLAN instead of REPLAN. Either way, make them agree.

4. **S.16 EXECUTE** -- Add a runtime spawn monitor decision point inside the EXECUTE node. Show a dashed escalation line from the runtime monitor to REPLAN with label "Runtime spawn ceiling exceeded (original × 2)."

5. **S.19 RESULT OK?** -- Move UNEQUIVALENT to the SUCCESS branch. The annotation "treat UNEQUIVALENT like SUCCESS" matches the spec, but the visual routing sends it to FRAGO. Route it to DONE.

6. **S.24 DEGRADING?** -- On the YES branch, add annotation "Skips remaining compensation ladder levels" to the "ESCALATE TO USER" box.

7. **Ceiling/Limit Summary table (line 770):** Change "return to PLAN" to "return to REPLAN" for both branching and depth entries, to match the flowchart routing.

---

## 6. ADDITIONAL ARCHITECTURAL GAPS NOTED

These are not direct inaccuracies but are gaps I would fill for a v3 of Karl's document:

| Gap | Spec Reference | Why It Matters |
|-----|---------------|----------------|
| Two-tier approval (Tier 1 summary, Tier 2 details) mentioned but not shown in approval example | 9.5.A | User needs to know they can drill down |
| Replan diff briefing not shown | 9.5.B | User needs to understand what changed between approvals |
| `isolation_key` concept for resource-ordered execution | 10.5.B | Affects parallelism guarantees |
| Scope change detection (user changes request mid-pipeline) | D.3 | User-facing behavior they will encounter |
| Atomicity requirements for sub-task writes | 10.5.C | Safety-critical for data integrity |
| Evaluation caching (prevents flip-flopping on replan) | 12.5.B | Explains why evaluations don't change randomly |

---

## 7. STRENGTHS (Credit Where Due)

- **The flowchart in Section 6 is excellent architecture.** The node numbering, the safety gate boundaries (####), the dashed escalation lines, and the ceiling summary table are precisely what a designer needs. This is the strongest part of the document.

- **The error messages table (Section 4)** is comprehensive and maps directly to spec-defined behaviors. Every message can be traced to a spec section. This is the gold standard for user-facing documentation.

- **The approval gate example (lines 209-273)** is the best user-facing description of the progressive disclosure format I have seen. The tier 1 / tier 2 distinction is clear, the example content is realistic, and the navigation keys are unambiguous.

- **The compensation ladder description in prose (lines 315-322)** is accurate and well-explained for a non-technical audience.

- **Document structure and audience calibration** are correct throughout. Karl clearly understands who this is for and writes at the right level.

---

## 8. SUMMARY -- What to Fix Before This Ships

**Must fix (will mislead a stakeholder or a designer):**
1. FAST path "no safety checks" statement (1.1) -- replace with output guardrail description.
2. F.3 OUTPUT CLEAN? binary decision (1.4, 4.1) -- add three-way handling.
3. S.19 UNEQUIVALENT routing (2.2) -- route to SUCCESS/DONE, not FRAGO.
4. Ceiling table vs. flowchart routing disagreement (2.3) -- make "return to PLAN" say "return to REPLAN."
5. Runtime monitor has no decision point in EXECUTE (2.1) -- add diamond and escalation line.

**Should fix (architecturally misleading):**
6. Classification conflated with denylist (1.3) -- separate the descriptions.
7. Persona false-positive threshold missing 30% tier (1.6) -- add both thresholds.
8. DEEP path persona set wrong (1.7) -- fix to show only Resource Analyst is added.
9. Disclaimer missing "verification" (1.2) -- restore the word.
10. PREMORTEM force-pass doesn't show BACKBRIEF carries forward (4.2) -- annotate the counter carry-forward.

**Nice to fix (completeness):**
11. SKILL LIBRARY omitted -- acceptable for ELI5, but flag that a companion doc is needed.
12. Checkpoint/resume not in flowchart -- add checkpoint markers to EXECUTE.
13. Plan versioning not explained -- add prose note in Section 3.

---

*End of critique. Karl, your document is structurally sound and well-crafted. These are wounds, not mortal ones. Fix the seven inaccuracies and the document is ready for stakeholder review.*
