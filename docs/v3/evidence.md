# JORDAN V3 — evidence and removal notes

One row per component. A component stays only while its row can name evidence
and a result that would remove it.

How to read the columns:

- Evidence cites the research report (`R §n`, `/mnt/project-files/jordan-v3-research/JORDAN-V3-research-report.md`)
  and its lane files (`A:2` is lane A finding 2; `E:E8`, `F:F3`, `G:F9` use the
  lanes' own ids; lanes F and G both number from F1). The tag is the lane's
  own: verified (the lane read the source in its session), recalled (from
  memory, not opened), uncertain (title or secondary source only). "Judgment"
  means a design decision with no direct evidence. `review` is
  `fable-review.md`; `REDTEAM` is `docs/v3/REDTEAM.md`, whose [ran] items were
  executed.
- Evidence about agents in general is not evidence that this component works
  here. Last measured effect is the only column that can show that.
- Arms are those of RULINGS R11: A0 no JORDAN, A1 kernel only, A2 kernel plus
  hooks, A3 A2 plus modules. "Leave-one-out" means the same arm rerun with that
  one component removed. A difference smaller than the disagreement between
  reruns of one arm counts as no difference (E:E10, verified).

## Kernel rules

| Component | Evidence (source, tag) | Last measured effect | Eval result that deletes it |
|---|---|---|---|
| Rule 1: size the task; undo doubt goes up, difficulty doubt goes down | Promote on failure: C:ADaPT (verified, older model). Oversight belongs on irreversible actions: G:F14 (verified), E:E14 (verified). Tier names: judgment, kept for orchestrate (DESIGN §12.3). Never-FAST list restored by REDTEAM M3 | not yet measured | A1 leave-one-out: no change in hidden-check pass or in irreversible-task behaviour. Then the three names go and rule 7 carries the undo question |
| Rule 2: name the check first; record it in the ledger | R §3.2; E:E6 (recalled: an external accept or reject signal helped where self-critique did not); F:F3 (verified, vendor guidance). Ledger line: REDTEAM B1 (reasoned, not run) | not yet measured | A2 runs show ledgers are not opened, or A1 leave-one-out shows no change in false completion |
| Rule 3: direct route first; split on a failed check; plan the next step only | R §3.4; C:ADaPT (verified); C:HORIZON long-horizon data (verified); E:E3 (verified, abstract level: planning mostly saves cost for strong models) | not yet measured | A1 leave-one-out: no change in pass rate or tokens |
| Rule 4: act, check, read, correct; suggested fix is a guess; predictions per cause; named change per retry; two-worse stop | R §3.3; A:2 (verified; synthetic domain, workshop paper); A:3 (verified; older backbone model); A:12 (verified; not a coding task); A:4 (verified, descriptive) | not yet measured | A1 leave-one-out: no change in pass rate on the bug task with the tempting wrong patch |
| Rule 5: leave existing checks alone; impossible is a correct result | R §3.2; E:E8 (verified: the exit cut one model's cheating from 54% to 9%; read-only tests stopped edits, not special-casing); G:F9 (verified: a "do not cheat" instruction did little) | not yet measured | A1 against A0 on the contradiction task: no gain in correct stops; or more "stopped as impossible" on the solvable task than A0 |
| Rule 6: evidence against the premise drops the plan | A:12 (verified; not a coding task); B:4 (recalled); review II.5 | not yet measured | A1 leave-one-out: no change on any measure. Weak evidence; early candidate |
| Rule 7: decision before an irreversible action; escalate when stuck | R §3.10; E:E14 (verified: 93% of permission prompts approved); G:F1 (verified); G:F6 (verified, incident reports); wording from REDTEAM M4 | not yet measured | No difference between arms with and without it on an irreversible-action task. 3.0 ships no such task; until one exists this row cannot be tested |
| Rule 8: report with evidence; steps done versus outcome met; only earned numbers; claim marks | E:E8 (verified: maintainers would merge about 24 points fewer patches than the grader passed); D:12 (recalled) for the two statements; review R2, R4 | not yet measured | A1 leave-one-out: no change in false completion (claimed done, hidden check fails) |
| Rule 9: smallest change; rereading is not a check | E:E6 (recalled: self-review with no external signal lowered accuracy); E:E7 (verified: review anchors on what it reads); C:SlopCodeBench (verified) for scope growth | not yet measured | A1 leave-one-out: no change in hidden-check pass or false completion |

## Modules

| Component | Evidence (source, tag) | Last measured effect | Eval result that deletes it |
|---|---|---|---|
| `plan` | Check plus a structural requirement: E:E8 (verified). Intent as purpose and end state: D:5 (verified for ADP 6-0 1-45; "key tasks" recalled). Assumption list: D:2 (recalled). Decision triggers: D:9 (definitions recalled). Failure pass: B:3 (recalled; no support for personas or a count) | not yet measured | A3 no better than A2 on its primary measure: loses its trigger. Leave-one-out order inside it: failure pass, then triggers |
| `split` | R §3.4; C:Parnas (verified); C:ADaPT (verified); C:Mikado (verified); walking skeleton (C, recalled); fan-out conditions: E:E1 (verified; no coding benchmark), F:F8 (verified, vendor); red flag: C:MAKER (verified; one task) | not yet measured | A3 no better than A2. 3.0's pilot tasks do not need a split, so this row needs a multi-file task first |
| `diagnose` | R §3.3; A:1 (verified for the log's steps); A:2 (verified: both-direction test 0.71 against 0.04, correlational); A:13 passing neighbour (recalled); A:5 (verified: mandatory debugger not worth its cost); A:10 (verified) for pooled diagnoses | not yet measured | A3 no better than A2 on diagnosis-correct for the bug task |
| `verify` | R §3.2; red then green: G:F10 (uncertain: titles only; the practice itself is standard); refuter order: E:E7 (verified), G:F11 (verified: running code cut false rejections from 54.8% to 16.3%); oracle table: G:F12 (recalled); evidence rank: E:E7, E contradiction 5 | not yet measured | A3 no better than A2 on false completion |
| `options` | R §3.7; B:1 (verified, perception only); E:E11 (recalled; E:E6 verified that debate did not beat plain reasoning); E:E7 (verified: choosing between independent answers beat review); D:10 (verified, one Army article) for loser as branch | not yet measured | A3 no better than A2. 3.0's pilot tasks do not trigger it |
| `recover` | Branch versus adjustment: D:12 (recalled; one 2026 article verified). Step order: judgment (review II.5). Impossible exit: E:E8 (verified) | not yet measured | A3 no better than A2 on the contradiction task and on tokens after first failure |
| `brief` | Line shape: orchestrate `references/standing-orders.md` (read). Gate on irreversible actions: G:F14 (verified); B:15 (recalled). Handoff by fixed fields: B:13 (verified, hospital study; analogy) | not yet measured | No eval task in 3.0 reaches a decision request. Deleted if orchestrate's own text makes it redundant for seats and solo runs show no use in traces |

## Hooks

| Component | Evidence (source, tag) | Last measured effect | Eval result that deletes it |
|---|---|---|---|
| Done-gate (Stop, SubagentStop) | R §3.2 item 8; review B1; E:E2 (verified: a verification step raised success 15.6% in one intervention, older frameworks); F:F5 (verified, vendor). Stop-hook mechanics: REDTEAM B3, m2 (ran) | not yet measured | A2 no better than A1 on false completion (DESIGN §10); or its blocks are mostly on stops that were not completion claims |
| Protected paths (stop-time diff; early notice on Edit and Write) | R §3.2 item 1; E:E8 (verified); G:F9 (verified: gaming 30.4% with a visible scorer against 0.7% without). Bypass of an Edit-only matcher: REDTEAM M1 (ran) | not yet measured | A2 no better than A1 on protected-path tampering |
| Irreversible guard (PreToolUse on Bash) | R §3.8; G:F6 (verified, incident reports); G:F2 (verified: the sandbox is the real boundary); deny behaviour: REDTEAM M5 (ran in default mode; untested under bypass) | not yet measured | No pilot task tempts an irreversible action, so 3.0 cannot test it. Deleted if a sandbox is mandatory, or if a labelled sample of its blocks is mostly false positives |
| Trace (PostToolUse, PostToolUseFailure) | No outcome evidence; it is the record the eval and the ledger claim depend on (RULINGS R3, R7) | not yet measured (no effect expected) | Removed if the ledger claim moves elsewhere and no report reads the trace |
| Session-start (plugin route) | No outcome evidence; a plugin cannot ship an always-on CLAUDE.md (DESIGN §6, spec sheet). SessionStart fields: REDTEAM M6 (ran) | not yet measured | Removed with the kernel if A1 is no better than A0, or when plugins can ship always-on text |

## Known gaps

- No arm has been run, so no row has a measured effect.
- The two pilot tasks cover the bug-with-wrong-patch and contradiction cases
  only. Rows that say so cannot be tested until the operator adds tasks.
- Doctrine-derived items (decision triggers, branch versus adjustment, "what
  must hold if the plan fails") rest on recalled definitions and have no
  evidence in agents (DESIGN §12.6). They are first in line for leave-one-out.
