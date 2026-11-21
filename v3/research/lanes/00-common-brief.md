# Common brief for every research lane (read fully before working)

## What this research is for

JORDAN is an operating framework for AI coding agents. It distills established problem-solving
frameworks, decomposition strategies and military planning doctrine (MDMP, commander's intent,
FRAGO, backbrief, premortem, AAR) into an agent workflow. It is at version 2 and is being
redesigned as version 3. Your lane's findings feed one research report that a separate design
team will use to build V3. They will not be able to ask you questions, so your file must stand
on its own.

## What JORDAN v2 already is (so you do not re-report the obvious)

- A ~500-token always-on kernel: CLASSIFY (FAST / STANDARD / DEEP; safety doubt classifies up,
  complexity doubt starts low and promotes on surprise) -> WIRE THE VERIFIER ("how will I know
  this worked?") -> PLAN (goal, constraints, acceptance criteria, dependency-ordered subtasks
  each with its own check) -> EXECUTE in a tight act/check/read/correct loop -> REPORT with
  quoted evidence, no unearned numbers -> ESCALATE, never bury -> SMALLEST CORRECT CHANGE.
- On-demand modules: premortem (persona lenses, compiled into runtime watchdogs), competing
  courses of action (2-3 COAs for DEEP), recovery (a monotonic ladder: retry with a named
  change -> fallback -> local -> radius -> FRAGO replan -> human), human briefing (BLUF,
  recommendation, provenance), research (known / cached / fetchable / genuine gap).
- A 12-phase pipeline: CLASSIFY, PLAN, BACKBRIEF, RESEARCH, RISK, PREMORTEM, BRANCHING MONITOR,
  APPROVAL, EXECUTE, SYNTHESIZE, EVALUATE, REPLAN.
- It runs inside Claude Code with a companion orchestration skill: a premium lead model that
  only decides, rules, dispatches, arbitrates and synthesizes; cheaper models build and sweep;
  fresh-context refuters verify; pointer briefs with "design rulings", fences and acceptance
  commands; an intake step that interrogates operator intent and writes INTENT.md; hooks that
  enforce some gates in code; credit-aware posture; handoff files at context limits.
- A prior internal review concluded: harness enforcement > model routing > context isolation >
  prompt content; prompt-simulated pipelines produce process theater; the framework has never
  been measured against a baseline.
- An earlier research corpus (May 2026) already has shallow records on: A3, AAR, backbrief/ROC
  drill, center of gravity, commander's intent, CPM, Cynefin, DMAIC, DSM, double diamond,
  F2T2EA, FRAGO, first principles, HTN, IPB, JOPP, Kepner-Tregoe, MDMP, MECE, METT-TC, MoSCoW,
  OODA, premortem, red teaming, reference class forecasting, SMEAC, systems thinking, TRIZ,
  Theory of Constraints, WBS, Wardley mapping, user story mapping; and AI items ReAct,
  Reflexion, Tree/Graph of Thoughts, Plan-and-Execute, LLMCompiler, AutoGen, LangGraph, MAKER,
  MAP, ALAS, TAPE, THREAD, RDD, Voyager, SWE-EVO. For anything on that list, do not restate the
  textbook summary. Report only what is deeper, more precise, corrected, or newly published.

## What a finding must contain

For every framework, concept, paper or practice you report:

1. **What it is**, in two to four sentences, precise enough to act on. Give the actual
   mechanism (steps, artifacts, rules), not a description of its reputation.
2. **Source**: a URL you actually opened or that a search result returned in this session,
   plus author / organization and year. Mark each claim `[verified]` (you read it on a source
   this session), `[recalled]` (from training memory, not checked) or `[uncertain]`.
   Never invent a URL, a paper title, an author, a number or a quotation. If you cannot find a
   source, say so. Any quantitative result must come with the source that states it.
3. **Known critiques and failure modes**: where it breaks, who says so, what the evidence is.
   A framework reported without its critique is half a finding.
4. **Transfer to an AI coding agent**: what concretely carries over, what does not carry over
   and why (for example: humans tire and forget, agents lose context and confabulate; agents
   can run fresh-context copies of themselves, humans cannot).
5. **V3 implication candidate**: one concrete, testable change to an agent workflow. State it
   as "V3 should ___ because ___", and name whether it belongs in the always-on kernel, an
   on-demand module, harness code (hooks, scripts, schemas), the orchestration layer, or the
   eval suite. If the honest answer is "nothing new, v2 already does this", say that.

Prefer primary sources (doctrine manuals, original papers, official engineering blogs) over
summaries. Prefer findings with evidence over findings with only advocacy, and say which is
which. Explicitly flag anything that contradicts JORDAN v2's current design; contradictions are
the most valuable findings. Also flag hype: popular ideas with weak or negative evidence.

Today is 2026-11-21. Material from 2025 and 2026 matters most for the AI lanes; search for it
explicitly rather than relying on memory.

## Tools and limits

- Use WebSearch (load it with ToolSearch `select:WebSearch` if it is not already available) and
  the `web-fetch` agent or WebFetch to read pages. Use `mode: "standard"` by default and
  `"extended"` only for niche or very recent items. Send independent searches in one turn.
- Do not read or search the local repositories. Do not spawn further subagents except
  `web-fetch` for reading pages.
- Budget: roughly 25 to 45 searches and 10 to 25 page reads. Stop when new searches stop
  changing your findings.

## Output

Write one Markdown file at the path your lane prompt gives. Target 3,000 to 5,000 words.
Structure:

```
# Lane <id>: <title>
## Summary (the 8-12 findings that matter most, one or two sentences each)
## Findings (one `###` section per item, using the five fields above)
## Contradictions with JORDAN v2
## Hype and weak evidence
## Gaps (what you looked for and could not find or verify)
## Sources (every URL used, as a Markdown list)
```

Write plainly: full sentences, no filler, define any term a reader new to the field would not
know. Your final reply to me should be at most 25 lines: the file path, the five findings you
judge most consequential for V3, and anything you could not verify.
