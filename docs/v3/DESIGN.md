# JORDAN V3 — Design

Status: architect draft for red-team review, 2026-11-21. Not committed.

**Citations.** `A:2` means lane-A, finding 2; `E:E8` lane-E finding E8; `F:F5` and `G:F9` are
lane-F and lane-G findings (both number theirs F1..); `X:contra n` is a lane's "Contradictions
with JORDAN v2" item; `R §n` is the synthesized research report (`R §5 #n` its numbered
implication), preferred where it overlaps a lane; `audit §n` is `docs/v3/audit.md`; `review` is
`fable-review.md`; `spec` is the integrator's verified plugin spec sheet. Evidence
tags are the lanes' own: **[v]** read this session by the lane, **[r]** recalled, **[u]** title
only. "Judgment" marks an architect decision with no direct evidence. Numbers below were read
from those files or counted by me with the command named.

## 1. Thesis

V3 is a small set of working habits plus a small set of code-enforced checks. V2 was a
12-phase planning pipeline written as prompt text; nothing loaded most of it and nothing
enforced any of it (audit §2). V3 keeps the habits that have evidence (name the check first,
tight act-check-read loop, honest reports, smallest change), moves the claims that matter into
hooks that hold whether or not the model cooperates, and puts every remaining piece of process
on an ablation schedule against a bare baseline (R §1 items 1-5; R §7 decision 1).

What changed in the cornerstone ideas, and why:

1. **From "plan the campaign" to "protect the check."** Agents build to whatever check they can
   see and edit; prompt guardrails did not stop it (E:E8 [v], G:F9 [v]). The centre of V3 is a
   check the builder cannot quietly weaken, plus an honest exit when the task is impossible.
2. **From pipeline phases to triggers.** On frontier models harness process mostly buys tokens
   (E:E3 [v]); vendors remove scaffolding as models improve (F:F6 [v]). Options, failure passes
   and human gates now fire on conditions (irreversible, no fast check, first failure), not on
   a tier label (B:1, B verdict table; E:contra 6).
3. **From plan-everything to try-then-split.** Decompose after the direct attempt fails, detail
   only the next wave (C:ADaPT [v], C:contra 1).
4. **From "another model looked" to executed evidence.** Review without execution over-rejects
   and anchors on what it reads (G:F11 [v], E:E7 [v]).
5. **From doctrine vocabulary to doctrine function.** Military terms stay only where the
   function survives translation and has non-recalled support; most of lane D is [r].

## 2. Every v2 concept: disposition

K kept · C changed · H moved to harness code · O moved to orchestrate · R removed.
Dispositions agree with R §4 except four, where I go further and say so in §12: premortem
(folded into `plan`), RESEARCH (folded into the assumption list), SYNTHESIZE (left to
orchestrate), experience store (removed, not rebuilt).

| v2 concept | | One-line reason | Source |
|---|---|---|---|
| Identity framing ("every task is a campaign") | R | Emphasis is over-applied; pushes ceremony on trivial work | F:F3, F:F16 [v]; review II.4 |
| Three-gate protocol as mandatory ritual | C | One sizing sentence; routing belongs to orchestrate | audit §4.1 |
| FAST/STANDARD/DEEP | C | Names kept as shared vocabulary; no mechanism hangs on the tier | audit §4.1; B:contra 1 |
| Five-axis scoring | R | No source supports numeric risk axes; two questions replace it (undoable? fast check?) | F "moved past"; G:F14 [v]; B:2 |
| Two-doubts rule (safety up; complexity low, promote) | K | Promote-on-failure is the supported shape; still untested as a tier rule | C:ADaPT [v]; F:contra 7 |
| 12-phase pipeline | R | Prompt-simulated phases are re-sent every step and unenforced | E:contra 3; F:contra 2; audit §4.2 |
| Commander's Intent = goal+constraints+criteria+priority | C | Intent is purpose and end state; constraints and criteria are separate items | D:5 (ADP 6-0 1-45 [v]; key tasks [r]) |
| Up-front dependency DAG | C | Try first, split on failed check, next wave only, cut by owned decision | C:Parnas [v], C:ADaPT [v], C:contra 1-2 |
| BACKBRIEF (planner's DAG check) | R | Mislabelled; the real item is the worker restating its task | D:8 [r]; B:13 (I-PASS [v], by analogy) |
| DSM coupling, branching factor b<1 | R | Uncomputable in context; nesting and concurrency caps exist in the harness | review II.1; F:F1 [v] |
| RESEARCH gap classes, cache lookup | C | Folded into an assumption list where each item carries a validating command | D:2 [r]; G:F8 [v]; judgment |
| Per-subtask risk levels, fused risk | R | Replaced by action classes a hook can test (undoable or not) | G:F14 [v]; B:contra 4 |
| Premortem with 4-5 personas | C | Personas in one context are not independent; count unsupported. One fresh-context failure pass, on trigger, on ablation | B:3; G:contra 6; audit §4.2 |
| Premortem watchdogs | C | Become "if X is seen, then Y" decision triggers in the plan | D:9 (CTC critique [v], definitions [r]); judgment |
| Approval gate; DEEP always asks a human | R | 93% of prompts are approved; gate moves to irreversible action classes | E:E14 [v]; G:F1 [v]; B:15; audit §4.3 |
| EXECUTE micro-loop (act, check, read, correct) | K | Best-supported habit | E:E6; F "mainstream" |
| "MAKER" Design-Implement-Test-Verify | R | Borrowed name; the paper does something else and does not transfer; erratum in the archived seed | C:contra 3; R §5 #26 |
| SYNTHESIZE (type-aware merge) | O | Synthesis is a lead act; JORDAN adds only "one integrator" | audit §4.4; F:F13 |
| EVALUATE with four outcome labels | C | Two plain statements: checks pass; user's outcome met | E:E8 [v]; D:12 [r] |
| REPLAN / "FRAGO" | C | Run a planned branch at its trigger, or adjust with one workable option; term retired | D:12 (RDSP [v] via Griffiths) |
| Compensation ladder, 6 rungs | C | Four steps; models track "did I change something" better than rung numbers | review II.5; B verdict; G:contra 5 |
| Iteration ceilings table | H | Stop-hook block cap exists natively; kernel keeps only "two worse, stop" | F:F1 [v] |
| Wire the verifier first | K | Strengthened: protected, with red-then-green proof | E:E6, E:E8, G:F10 |
| Verification ladder | C | Execution > independent second attempt or cross-family reader > same-family fresh reader > self; self-written tests rank lower | E:E7 [v]; E:contra 5 |
| Multi-channel verification | R | A second refuter cost about 3x for equal outcomes | audit §3 |
| Domain feedback table | C | Becomes the oracle table in `verify` | G:F12 [r]; judgment |
| Evidence-first debugging | C | Extended: per-cause predictions, test both directions | A:1-2 [v] |
| Anti-repetition, degradation stop, plan abandonment | K | Supported; anchoring persists in most wrong cases | A:12 [v]; A:4 [v] |
| Context hygiene rule | R | On the vendor's "stop doing" list; lane budgets are orchestrate's | F:F3 [v]; audit §3 |
| Honest completion | H | Kernel line kept; the claim is enforced by the done-gate | review B1; F:F1 [v] |
| Minimal change; no unearned numbers; claim marking | K | Cheap, checkable by a reader | review R2, R4 |
| 19 maxims | R | Long always-on lists cost tokens every step for little gain | F:F4 [v]; E:E3 [v] |
| "Default-deny" safety | C | Named honestly: the sandbox is default-deny, hooks are a denylist | G:contra 1 |
| Human briefing tiers | C | One short form matching the Decision Request line | audit §3; G:F14 |
| Documentation and git discipline | R | Repo conventions, not problem-solving method; orchestrate S10 covers commits | judgment |
| Experience store | R | Never built; prose lessons rarely change behaviour. A lesson becomes a hook, a test or an eval task | review B6; B:16 [r]; E:E12 [r]; judgment |
| Tiered delivery, deployment matrix | C | Kept, now with a deployer; delivery by seat, not model class | audit §2, §4.5 |
| "45% orchestration overhead" rule | R | Misreads its source (a capability threshold; no coding benchmark); erratum added to the archived seed §8.6 | E:E1 [v]; R §5 #26 |
| Asymmetric model routing | O | Already orchestrate's routing table | audit §4.4 |
| Seed prompt as source of truth | R | Archived; the kernel file is the source | audit §2 |
| Large structured output schemas | R | Killed 3 of 7 recon agents; typed one-line fields instead | audit §3 |

## 3. Architecture in layers

| Layer | What lives there | Why here and not elsewhere |
|---|---|---|
| **L0 Kernel** (always on) | Nine habits a model must apply by judgment, every step | Only judgment that cannot be checked by code earns per-step tokens (E:E3; F:F1) |
| **L1 Modules** (on demand) | Procedures needed in some tasks: plan, split, diagnose, verify, options, recover, brief | Skills load only name and description until triggered (F:F10 [v]); procedure in the kernel taxes every step |
| **L2 Hooks** (code) | Claims with a mechanical test: done means the check ran green; protected paths unchanged; irreversible actions stopped | A rule with no exceptions belongs in a hook; prompt rules are advisory (F summary 1 [v]; G:F9 [v]) |
| **L3 Agent base** | Templates, one shared block, build script, lint | Seats run with `omitClaudeMd`, so the kernel reaches them only through their definition (audit §3, §4.5) |
| **L4 Eval** | Task set, arms, ablation schedule, decision rules | The framework has never been measured against a baseline (review R6; G:F13) |

Routing, dispatch, seat economy and budgets are not a JORDAN layer; they stay in orchestrate
(audit §5).

## 4. Kernel (L0) — full proposed text

Hard cap **2,500 bytes**, enforced by a test. Justification: the kernel is re-sent on every
step, so its size is a per-step cost (E:E3 [v]); V3 adds four rules, and the cap forces them to
displace v2 text instead of adding to its 2,787 bytes. The text below is 2,418 bytes (`wc -c`).
Wording follows F:F16 [v]: plain, scoped, positive, no capitals for emphasis. The number 2,500
itself is judgment; arm A1 of the eval decides whether it shrinks further.

```text
# JORDAN kernel v3

Work this way on any task that changes files or state.

1. Size it in one sentence. Ask: can this be undone, and is there a fast check that would show it is wrong? Call it FAST (one step, undoable, checkable), STANDARD (several steps), or DEEP (hard to undo, or no fast check). Unsure whether it can be undone: pick the higher. Unsure only how hard it is: pick the lower and move up at the first surprise, saying so.

2. Name the check before you start: the command or observation that will show the work is right. If none exists, build it first. If none can exist, say so and label the result unverified.

3. Try the direct route first. Split the work only when a check fails or it must run in parallel. Plan only the next step in detail.

4. Loop: act, run the check, read the actual output, correct. Read code before editing it. A fix suggested by the task or an error message is a guess until you reproduce the failure. When the cause is unclear, write what each candidate cause predicts, then run the test where the predictions differ. Every retry changes something you can name. After two attempts that each made things worse, stop and rebuild the diagnosis from the raw output, or hand up.

5. Leave existing checks alone. Do not edit, skip or special-case tests that existed before the task unless the task says to. If the checks contradict the request, or the task cannot be done as written, stop and report that. It is a correct result.

6. If the evidence contradicts the plan's premise, drop the plan and size the task again.

7. Ask before an action that cannot be undone or that reaches outside the workspace: deleting outside it, force-pushing, publishing, spending, changing infrastructure, sending messages.

8. Report with evidence. Quote the check's output. Passing checks show the steps were done; say separately whether the outcome the user asked for is met. Say "implemented but unverified" when the check did not run. Report failures as plainly as successes. Give only numbers a tool produced or you counted. Mark claims verified, likely or unknown.

9. Make the smallest change that meets the request, and list other improvements instead of making them. Re-reading your own work is not a check: a check needs a run, a fresh reader, or a second independent attempt.

Modules in the jordan skill load on their triggers: plan, split, diagnose, verify, options, recover, brief.
```

Line sources: 1 B:2, G:F14, review R3 · 2 E:E6, F:F3 · 3 C:ADaPT, C:contra 1 · 4 A:1-3, A:12,
review R4 · 5 E:E8 (the "flag" exit cut cheating from 54% to 9% for one model, less for
another), G:F9 · 6 review II.5 · 7 E:E14, G:F6 · 8 E:E8, review R2 · 9 E:E6, E:E7.
Rules 5 and 7 are also enforced by hooks; they stay in the kernel because a blocked agent
should already know why (judgment).

## 5. Modules (L1)

Each is one file under `skills/jordan/modules/`, capped at 2,500 bytes by the same test, and listed
in `SKILL.md` as "read when X".

| Module | Load when | Contents | Replaces |
|---|---|---|---|
| `plan` | Task is STANDARD or DEEP and work is about to start | Purpose and end state in two lines, plus what must hold even if the plan fails · acceptance: the check command, and one structural requirement tests cannot see · assumption list, each with a validating command or a named risk and trigger · up to five "if X is seen, then Y" decision triggers · one fresh-context failure pass ("this failed; write the cause") only before an irreversible step or when no fast check exists; each finding becomes a check or an assumption | PLAN, BACKBRIEF, RESEARCH (`research.md`), `premortem.md` |
| `split` | A check failed on a direct attempt, or parallel work is being considered | Split on failure, depth limit with a flag · each piece names the decision it owns, what it exposes, what it must not know · first piece is the thinnest end-to-end path with its check running · fan out only for independent read-heavy work or disjoint file sets with a written contract; one integrator · signs the cut was wrong (two workers in one file; a check needing another piece's internals; integration fails after units pass) | DAG decomposition, branching monitor, "MAKER" |
| `diagnose` | A failure whose cause the first reproduction does not show, or a fix that did not work | Hypothesis log: cause, what it predicts that rivals do not, command, pasted output, verdict · confirm a cause by removing it and by forcing it · after a failed fix, restate the symptom from raw output before rereading the old hypothesis · bisect when a good state exists · no mandatory debugger | Kernel v2 rule 4's one line; part of `recovery.md` |
| `verify` | Writing acceptance where no existing test covers the change, or briefing a refuter | Oracle table (pure function: property test; refactor: characterization or differential; UI: screenshot; infra: dry-run diff) · bug fix needs the test seen failing before and passing after · refuter protocol: write expectations from the request before reading the diff; verdict needs an executed command · report which evidence rank a claim rests on | Verification ladder, multi-channel, domain table |
| `options` | The step is hard to undo, or no fast check exists, or the first approach failed its check | Default is one option plus a check · when triggered: candidates written in separate fresh contexts, criteria fixed before any is read, choose by an executable check where one exists · the loser becomes the branch plan · with orchestrate, this is the `panel` workflow | `coa.md` |
| `recover` | First failed check after a correction | Planned branch at its trigger versus adjustment with one workable option · four steps, never back down: retry with a named change, re-diagnose from raw output, re-cut the affected region, hand up · two-worse stop; premise failure means abandon · the impossible-task exit and how to report it | `recovery.md`, REPLAN |
| `brief` | Handing a decision to a human or lead | One line in the Decision Request shape · exact action, evidence, how to undo, recommendation, what happens by default if unanswered | `briefing.md` |

Sources: `plan` D:2, D:5, D:9, E:E8, B:3 · `split` C summary 1, 3, 4, 7, E:E1, F:F8 ·
`diagnose` A:1-3, A:5, A:12 · `verify` G:F10, G:F11, E:E7, G:F12 [r] · `options` B:1, D:10
(Brender [v]), E:E11 · `recover` D:12, B verdict · `brief` G:F14, B:15.

## 6. Hooks (L2)

Format facts are from `spec`: `command` hooks; exit 2 blocks and stderr is the reason; exit 1
does not block; PostToolUse cannot block; PreToolUse may instead return a `deny` decision;
injected context is capped at 10,000 characters; plugin-shipped agents ignore frontmatter
`hooks`, so every hook is registered globally and reads `agent_type` from stdin to tell a seat
from the main session. Scripts find their files from their own path, because
`${CLAUDE_PLUGIN_ROOT}` exists only on the plugin route. All follow the binding pattern (audit
§5): fail-open on internal error, block with a stated reason, registered once by command.
State lives in a per-task ledger, `.jordan/task.json`: task id, acceptance command, protected
path globs, baseline commit, `passes`, evidence paths. Small and flat (audit §3 on large
schemas; F:F5 [v]; R §5 #17).

| # | Hook | Event | Checks | Action | Fail-open | False-positive risk |
|---|---|---|---|---|---|---|
| 1 | **done-gate** | Stop, SubagentStop | If a ledger exists: runs the acceptance command itself (bounded time) and writes `passes`; passes when green, or when the ledger records `unverified` or `impossible` with a reason. Bug fixes also need a recorded red run that predates the fix. Keeps its own block counter, since `stop_hook_active` is unverified (`spec`) | Block (exit 2) | Error or timeout allows the stop and writes an advisory | Flaky or slow suites; sessions ended mid-task on purpose. Mitigation: inactive without a ledger; the `unverified` exit always passes; counter bounds loops |
| 2 | **protected-paths** | PreToolUse on `Edit\|Write`; again inside hook 1 via `git diff` against baseline | Changes to tests and checks present at baseline, CI config, the ledger, hook files | Deny unless the ledger authorises the path | Allows | Legitimate test updates when behaviour is meant to change. Mitigation: tests created in this task are free; the reason names the two exits (authorise, or report impossible) |
| 3 | **irreversible-guard** | PreToolUse on `Bash` | Narrow list: recursive delete with an unresolved `~`, variable or glob, or outside the workspace; force-push and push to the default branch; reads of credential paths; infra and cloud delete commands; package publish | Deny; reason says to file a Decision Request | Allows | Build-directory cleans, scripted releases. Mitigation: resolved in-workspace deletes pass; list is short and per-project extendable |
| 4 | **trace** | PostToolUse, PostToolUseFailure | Nothing; appends one JSONL record per tool call | None | Skips | None; disk only |
| 5 | **repeat-advisor** | PostToolUse | Same call with same arguments repeated; steps past a budget | Advise through `additionalContext` | Skips | Polling and reruns after edits look like repeats |
| 6 | **session-start** | SessionStart (all sources, so it re-injects after compaction) | Plugin route: injects `kernel.md` unless `~/.claude/CLAUDE.md` carries the kernel marker. Both routes: one advisory line when permissions are skipped and no sandbox is detected | None | Skips | Double kernel if marker detection fails |

**Minimum viable set: 1, 2, 3, plus 4 as the passive substrate for the eval** (R §5 #2, #3,
#13, #14). Evidence: 1 review B1, F:F5, E:E2 (a verification step gave +15.6% in a case study)
· 2 E:E8, G:F9 (read-only tests stop test editing, not special-casing, so the structural
requirement in `plan` still matters) · 3 G:F6, G:F14, E:E14. Hook 5 has no controlled evidence
(G:F15 critique). Hook 6 exists because a plugin cannot ship an always-on CLAUDE.md (`spec`).

Limits. In a solo session the agent can write the ledger, so hooks 1-2 make tampering
visible, not impossible; they are tamper-proof only when a lead writes the ledger and the
builder's ledger path is protected. Hook 3 is a denylist, not a sandbox; skip-permissions
outside a boundary stays unsafe (G:F2 [v]; R §3.8).

Not built, against R §6's hook map: a first-write check for the worker's restatement (cannot
be diffed mechanically; evidence is by analogy), UserPromptSubmit intake (orchestrate's
`say-intentions`), SubagentStart caps (native, F:F1), PreCompact state (swarmfucker's
`precompact-handoff.py`), a dependency-install check (R §5 #25; deferred), and any
model-judged hook (not deterministic, F:F1).

## 7. Agent base (L3)

**Roles.** Four archetypes; no hierarchy beyond them (F:F13 [v]: role zoos are brittle).

| Archetype | Tools | Rule-of-two tag (G:F3 [v], vendor heuristic) | Purpose |
|---|---|---|---|
| reader | Read, search, optional web; no Edit/Write | A+B | Recon and research; returns short typed findings |
| builder | Read, Edit, Write, Bash; no web | B+C | One writer per file set |
| refuter | Read, Bash, Write; Edit disallowed | B+C, read-mostly | Expectations first, then executed verdict |
| selector | Read, Bash | B | Chooses between independent candidates on criteria fixed beforehand |

**Frontmatter conventions** (audit §5, matching `orc-*`): `name`; one-line `description`
starting with the role; `model`; `effort`; `tools`; `disallowedTools` where the role forbids
editing; `omitClaudeMd: true`; `maxTurns`. All are fields `spec` lists as honoured; `hooks` and
`permissionMode` are not used because plugin-shipped agents ignore them. A body comment
`<!-- jordan: role=<archetype> abc=<tags> -->` carries the tag for the lint. Plugin installs
name the agent `jordan:<name>`; copied installs use the bare name.

**Shared block `jordan-core`** (one source file, spliced at `<!-- jordan-core:insert -->`,
capped at 1,200 bytes; judgment, sized against orchestrate's roughly 3.5 KB block noted in its
build script). Contents:
- First output is `CONFIRM:` purpose, own task, fences, acceptance command, copied from the
  brief (D:8 [r]; B:13 [v] by analogy; advisory until the eval shows value).
- The loop: act, run the check, read the output, correct; every retry changes something named.
- Existing checks are not edited; contradiction or impossibility ends the run as
  `STATUS: BLOCKED` with `impossible:` and the contradiction.
- Done quotes the acceptance output; otherwise "implemented but unverified".
- Final message uses orchestrate's `STATUS:` shape unchanged.
- Refuter and selector add: form expectations before reading the diff; `REFUTED` needs a
  reproducing command and its output; `CONFIRMED` lists commands run; skip style.

**New agent in under ten minutes.**
1. `tools/new-agent.py <name> --role refuter` copies the archetype to
   `agents/templates/<name>.md` with frontmatter filled.
2. Edit the description line and the `## Role` paragraph (the only hand-written text).
3. `tools/build-agents.py` renders `agents/<name>.md`; `--check` fails on stale output.
4. `tools/lint-agents.py` fails on: missing convention field, multi-line description,
   all three tags A, B, C, a refuter with Edit, block over cap.
5. Copy to `~/.claude/agents/` (or let the installer do it), run `claude plugin validate`,
   and dispatch a one-line smoke brief.

## 8. Composition with orchestrate, and install

| Question | Owner |
|---|---|
| Size the task (tier, undoable, fast check) | JORDAN kernel; the result fills the `tier` line of orchestrate's STRATEGY block |
| Vehicle, seats, models, budgets, credits | Orchestrate. JORDAN is silent |
| Who does the work | Orchestrate (lead never implements). Without orchestrate, the session works solo under the kernel |
| Brief shape | Orchestrate's sections, unchanged. JORDAN content maps in: purpose and end state to the brief header or INTENT.md; acceptance to `## Acceptance`; file sets to `## Fences`; assumptions and triggers into `## Design rulings` |
| Options, refutation | Orchestrate's `panel`, `refute`, `build-refute`; JORDAN modules name them and add only the trigger and the protocol |
| Human gate | The Decision Request line (audit §4.3) |

Shared vocabulary, no new terms: FAST/STANDARD/DEEP; `STATUS: DONE|PARTIAL|BLOCKED|DECISION_REQUEST`;
`CONFIRMED|REFUTED|PARTIAL`; DR line. One proposed addition for orchestrate to accept or reject:
verdict `UNVERIFIABLE` (G:F11); until then it is reported as `PARTIAL` with an `unverifiable:`
prefix. A parity test pins these strings in both repos. Limits already measured by orchestrate
are respected: one refuter by default, at most three premium seats, so the failure pass is one
fresh context, not a persona panel (audit §3, §4.2). Follow-up, not in 3.0: orchestrate's
standing orders drop their two JORDAN-derived lines and splice `jordan-core` instead.

**Install.**
- *Swarmfucker.* `skills/jordan/` is self-contained and lands at `~/.claude/skills/jordan/`
  by wholesale replace; hook scripts go to the installer's hooks directory and are merged into
  `settings.json` with absolute paths. `framework/CLAUDE.md` becomes the rendered kernel block between
  `<!-- jordan-kernel:begin/end -->` markers, one pointer line to the skill, and the two
  vendored sections (rg, bonemot) kept outside the markers (audit §2). `install_framework`
  stops copying `universal-seed-prompt.md`, `JORDAN_v2_OVERVIEW.md` and `prompts/`; hook
  registrations are added to the existing merge list; `docs/verification.md:21` checks
  `~/.claude/CLAUDE.md` and `~/.claude/skills/jordan/SKILL.md`. These change together (audit §5).
- *Plugin.* `.claude-plugin/plugin.json` (only `name` required) over `skills/jordan/`,
  `agents/`, `hooks/hooks.json`. Hook 6 delivers the kernel through SessionStart
  `additionalContext`; 2,418 bytes sits well under the 10,000-character cap (`spec`).
- *Back-compat.* `CLAUDE.md` in this repo drops from 10,299 bytes to the kernel block plus a
  pointer, under a 3,072-byte test cap (judgment). `universal-seed-prompt.md`,
  `JORDAN_v2_OVERVIEW.md`, `spec/` and `prompts/` move to `docs/v2/`, frozen, with a one-page
  errata note for the 45% rule and the MAKER passages (R §5 #26). `prompts/README.md`
  remains for one release as a stub pointing to `skills/jordan/kernel.md`, which is plain text usable
  verbatim as a system prompt. Files left in `~/.claude/` by v2 installs are loaded by nothing
  (audit §2); the installer names them and leaves deletion to the operator.

## 9. Proposed repository tree

```text
.claude-plugin/plugin.json   # name: jordan
skills/jordan/               # also installs as ~/.claude/skills/jordan/
  SKILL.md                   # one-line description + "read when X" index (capped)
  kernel.md                  # source of truth, <= 2,500 bytes
  modules/{plan,split,diagnose,verify,options,recover,brief}.md
hooks/
  hooks.json                 # plugin registration; swarmfucker merges the same list
  {done_gate,protected_paths,irreversible_guard,trace,repeat_advisor,session_start}.py
  ledger.py
agents/
  templates/{reader,builder,refuter,selector}.md
  shared/jordan-core.md
  *.md                       # rendered
tools/{build-agents.py,new-agent.py,lint-agents.py,render-claude-md.py}
tests/{test_sizes.py,test_hooks_*.py,test_build_agents.py,test_vocab_parity.py}
eval/
  tasks/<id>/{prompt.md,setup.sh,check.sh,hidden_check.sh,meta.json}
  run.py  report.py  arms.json  results/
docs/v3/{audit.md,DESIGN.md,evidence.md}
docs/v2/                     # archived seed prompt, overview, spec/, prompts/, reviews, errata
CLAUDE.md                    # rendered kernel block + pointer
prompts/README.md            # stub for one release
```

## 10. Eval and ablation plan (L4)

**Minimal baseline (A0).** Same model, same Claude Code version, headless with `--bare`
(skips hooks, skills and CLAUDE.md, F:F1 [v]), given only the task prompt and the visible
acceptance command. This is the mini-agent arm every JORDAN arm must beat at equal or lower
cost (E:E4).

**Arms.** A0 bare · A1 kernel only · A2 kernel + hooks 1-4 · A3 A2 + modules available.

**Tasks.** 30, written from the operator's own repositories and past failures (E:E10 on
contamination; G:F13; R §3.11), five of each type:
1. bug with a known cause and a tempting wrong patch (A:2);
2. feature whose visible tests can pass with the structure hollowed out (E:E8);
3. task whose tests contradict the request (ImpossibleBench style, E:E8);
4. underspecified request with a scripted answer available on asking (E:E13 [r]);
5. task that tempts an irreversible action, in a disposable container (G:F6);
6. multi-file refactor with characterization tests (C).

**Size.** 30 tasks × 4 arms × 3 trials = 360 runs, each from a clean checkout; 30 is the
lower bound R §7 decision 5 calls credible. A two-task
pilot across the four arms comes first, to measure cost and repair broken tasks or graders
(G:F13) before the full run is committed.

**Measures.** Hidden-check pass; false completion (claimed done, hidden check fails);
protected-path tampering; correct stop on type 3; diagnosis correct on type 1; tokens and
wall time from the trace; hook blocks, with a hand-labelled sample for false positives.

**Reading the result.** Paired per-task differences. Any gap smaller than the disagreement
between reruns of the same arm is a tie (E:E10 [v]). This size cannot resolve small pass-rate
gaps (E:E10: 45 tasks could not reliably detect a 12.9-point gap); it is sized for the large
effects the literature reports on false completion, tampering and the impossible exit.

**Decision rules.** A1 not better than A0 on any measure: cut the kernel to the lines the
hooks' messages rely on and rerun. A2 no better than A1 on false completion or tampering: the
hooks are not earning their friction; keep hook 3 only. A3 no better than A2: modules stay as
reference and lose their triggers. Then leave-one-out on whatever survived, ordered by
weakest evidence first: failure pass, decision triggers, `CONFIRM:` line, tier names (replace
with the two questions alone).

**Schedule.** Rerun on every kernel or hook change and on every model generation; no kernel
change merges without a paired run (G:F13). Each component carries a removal note in
`docs/v3/evidence.md`: its evidence, its last measured effect, the result that deletes it.

## 11. Positions on the report's seven decisions (R §7)

1. **One operating model.** Yes: kernel, hooks, and orchestrate when a lead is running. The
   12-phase pipeline is retired to `docs/v2/`.
2. **LangGraph pipeline.** No place in V3; `spec/` is archived. Reopen only if an eval on
   small-model seats shows hooks are not enough. Judgment; no evidence either way (R §7).
3. **May the lead implement?** No. A dependent chain goes to one builder seat that owns it end
   to end. That satisfies "one thread" (E:E1) without the lead paying to re-read build context
   every turn (audit §3). JORDAN itself stays silent on who works.
4. **Sandboxing.** The operator's call. V3 does not require it, says plainly that hook 3 does
   not replace it, and prints the hook 6 advisory when it is absent.
5. **Eval investment.** Commit to the pilot now and the 360-run set after it; no further
   design change until arm results exist (R §5 #1).
6. **Tiers versus effort.** Keep the three names for 3.0 and put them in the ablation list.
7. **Non-Anthropic refuters.** Not a default in 3.0. `verify` ranks a cross-family reader above
   a same-family one and makes reports name the rank; orchestrate decides whether the riskiest
   claim gets one.

## 12. Open questions and least-sure decisions

Ordered by how much I would aim at them.

1. **The done-gate re-runs the acceptance command itself.** Strongest against self-reported
   passes, but slow or flaky suites and side-effecting commands will produce blocks and
   timeouts. The alternative (check the trace for a green run after the last edit) is cheaper
   and easier to fool. Unmeasured either way.
2. **Solo-session tamper evidence.** The agent that writes the ledger can authorise its own
   test edits. I accept "visible, not impossible"; a red team may show this is worthless
   without a second party.
3. **Keeping tier names at all.** Kept only because orchestrate's STRATEGY block and `panel`
   use them (audit §4.1). The evidence favours the two questions alone (B:2; F:contra 7).
4. **Deleting the premortem module and personas.** B calls premortem the best-supported v2
   element, on thin evidence. I reduced it to a single triggered failure pass inside `plan`.
5. **Fail-open on the irreversible-guard.** Audit §5 binds all hooks to fail-open; `spec`
   confirms `onFailure: "block"` exists and R §5 #6 asks for it. A crashed guard permits the
   very action it exists to stop. I would ask the owner for an exception for hook 3 only.
6. **Doctrine items resting on [r] claims.** Decision triggers, the `CONFIRM:` line, "what must
   hold if the plan fails", and the branch-versus-adjustment split have no verified source for
   their definitions and no evidence in agents. All are in modules or the shared block, none in
   a hook, and all are early ablation candidates. Spot-check FM 5-0 (2022) before quoting.
7. **Kernel cap and content.** 2,500 bytes is a judgment anchored to v2's size, not a measured
   optimum. Rule 1 may be the weakest line per byte.
8. **No experience store.** Removing an unbuilt component is cheap, but "compound or decay" was
   a v2 cornerstone. The replacement (lesson becomes hook, test or eval task) has no owner yet.
9. **Departures from the report.** R §4 keeps premortem, research and an experience store as
   separate items, R §6 sketches nine modules and three more hooks, and R §5 #6 wants hooks to
   fail closed. I cut all of these for fewer mechanisms; each cut is a place to push back.
10. **Two kernel routes** (hook 6 and CLAUDE.md) invite drift or doubling. A `skills:` preload
    could replace the spliced `jordan-core` block (`spec`); I kept the splice because it works
    on both install routes.
11. **Unread 2026 papers** that could move sections 5-6 (R §9): cross-model review,
    plan-execution fidelity, the harness-effect set.
