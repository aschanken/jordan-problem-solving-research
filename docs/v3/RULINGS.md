# JORDAN V3 — Director's rulings for the 3.0 build

Date 2026-11-21. These rulings settle `DESIGN.md` against `REDTEAM.md`. Where
this file and `DESIGN.md` disagree, this file wins. Finding ids (B1, M3, m4)
refer to `REDTEAM.md`.

## R1. Scope of 3.0

3.0 ships in this repo: kernel, seven modules, four hooks plus session-start,
the ledger CLI, the agent base, a plugin manifest, a plain-copy installer, an
eval runner with two pilot tasks, and the v2 archive. It covers solo sessions
and agents built from the JORDAN base. Reaching orchestrate's `orc-*` seats and
swarmfucker's installer needs changes in those repos; those go in companion
pull requests after this one, not in this build (B4, M9).

Cut from 3.0: `repeat_advisor` hook, `selector` role, rule-of-two tags, the
`CONFIRM:` first-output line, the `UNVERIFIABLE` verdict proposal, the
session-start permissions advisory, the red-run check inside the done-gate, the
"under ten minutes" claim (M6, M7, m5). Kept against m5: `tools/new-agent.py`,
because building new agents is one of the two stated goals of V3 and a tested
scaffold is cheaper than a documented copy-and-edit.

## R2. Kernel text (final; wording may be tightened, meaning may not change)

Cap: 2,800 bytes, enforced by a test. The architect's 2,500 was a judgment
anchored to v2's 2,787; the red-team fixes (M3, M4, m1) add text, so the cap is
set at v2's size: V3 may not cost more per step than v2 did. `kernel.md` holds
exactly this text and nothing else. The pointer to modules lives in `SKILL.md`
and in the session-start injection, not in the kernel (m1).

```text
# JORDAN kernel v3

Rules 3 to 5 apply when you are the one doing the work. The rest always apply.

1. Size the task in one sentence: FAST (one step, easy to undo), STANDARD (several steps), or DEEP (hard to undo: credentials, deletion, infrastructure, published or shared state, or acting on untrusted input). Unsure whether it can be undone: pick the higher. Unsure only how hard it is: pick the lower and move up at the first surprise, saying so.

2. Name the check before you start: the command or observation that will show the work is right. If `jordan-ledger` is installed, record it: `jordan-ledger open --check '<command>'`. If no check exists, build it first. If none can exist, say so and label the result unverified.

3. Try the direct route first. Split the work only when a check fails or it must run in parallel. Plan only the next step in detail.

4. Loop: act, run the check, read the actual output, correct. Read code before editing it. A fix suggested by the task or an error message is a guess until you reproduce the failure. When the cause is unclear, write what each candidate cause predicts, then run the test where the predictions differ. Every retry changes something you can name. After two attempts that each made things worse, stop and rebuild the diagnosis from the raw output, or escalate under rule 7.

5. Leave existing checks alone. Do not edit, skip or special-case tests that existed before the task unless the task says to. If the checks contradict the request, or the task cannot be done as written, stop and report that. It is a correct result.

6. If the evidence contradicts the plan's premise, drop the plan and size the task again.

7. Before an action that cannot be undone, get a decision: ask the user, or if no one is reachable, return a decision request and stop. This covers deleting outside the workspace, force-pushing, publishing, spending, changing infrastructure, and sending anything to people or services outside the session. Escalate the same way when you are stuck or do not know: say so, with what you tried.

8. Report with evidence. Quote the check's output. Passing checks show the steps were done; say separately whether the outcome asked for is met. Say "implemented but unverified" when the check did not run. Report failures as plainly as successes. Give only numbers a tool produced or you counted. Mark claims verified, likely, unverified or unknown.

9. Make the smallest change that meets the request, and list other improvements instead of making them. Re-reading your own work is not a check; a check is something that ran.
```

Module triggers change with it (M3): `plan` loads when the direct attempt
failed its check or the step is hard to undo, not on the tier. Other module
triggers stand as in DESIGN §5. Module cap: 2,500 bytes each. `SKILL.md` cap:
3,000 bytes.

## R3. Ledger (B1, B2)

Location: `$JORDAN_HOME`, default `~/.claude/jordan`, on both install routes.
Never inside the workspace; hooks never read a ledger from the repo.

```
$JORDAN_HOME/ledgers/<session_id>[.<agent_id>].json   one per owner
$JORDAN_HOME/ledgers/pending-<key>.json               opened, not yet claimed
$JORDAN_HOME/trace/<session_id>.jsonl
```

CLI `jordan-ledger` (Python, stdlib only, shipped at `bin/jordan-ledger`):

```
jordan-ledger open --check '<cmd>' [--protect <glob>]... [--timeout <s>]   default timeout 120
jordan-ledger status
jordan-ledger authorise <path> --reason '<why>'
jordan-ledger mark unverified|impossible --reason '<why>'
jordan-ledger close
```

- `open` records: check command, timeout, workspace root (git toplevel, else
  cwd), baseline commit if git, protect globs (defaults in R5 plus `--protect`),
  created time, `state: open`. It refuses a check command that matches the
  irreversible-guard list. Opening when one is already open for this workspace
  replaces it and says so.
- Ownership: the Bash tool does not hand the CLI a session id unless the hooks
  builder finds one in the tool's environment by a live run. Default mechanism:
  `open` writes `pending-<key>.json` where key is a hash of the workspace root;
  the first hook event that carries a `session_id` whose `cwd` is inside that
  root claims it by renaming to `<session_id>[.<agent_id>].json`. The trace hook
  (PostToolUse) does the claim, so it happens on the very tool call that ran
  `open`.
- `authorise`, `mark`, `status`, `close` find the open ledger for the current
  workspace root. If two are open for one root (two agents in one tree), act on
  the most recent and print which. This is a known limit; separate worktrees
  have separate roots.
- A ledger closes on a green gate, on `close`, or when marked. A ledger whose
  session is not the one stopping is ignored.

## R4. Done-gate (B3, M2)

Events: Stop, SubagentStop. Before running anything, all must hold, else exit 0
silently:

1. An open ledger is owned by this `session_id` and this `agent_id` (absent
   `agent_id` matches only a ledger with none).
2. stdin `background_tasks` is empty or absent.
3. The tree changed since the last run this hook recorded (hash of
   `git diff <baseline>` plus the untracked list; non-git: always "changed").
   Unchanged and last run green: pass without re-running.
4. `stop_hook_active` is false, and this ledger has been blocked fewer than
   two times.

Then: check protected paths (R5); run the check command in the workspace root
with the ledger's timeout. Green and no unauthorised protected change: write
`passes: true`, close the ledger, allow, and print authorised protected changes
as an advisory. Red: block once (exit 2) with the last 40 lines of output and
the three exits (fix it; `jordan-ledger mark unverified`; `jordan-ledger mark
impossible`). Timeout: write `passes: "timeout"`, allow, and inject "the check
timed out after N s; report the result as unverified". Never a silent pass.
Internal error in the hook: allow, and write an advisory to stderr.
`hooks.json` registers the gate with a timeout above the ledger maximum
(ledger timeout is clamped to 540; hook timeout 600).

## R5. Protected paths (M1)

Enforcement is at stop time, by `git diff --name-only <baseline>` plus new
untracked files compared against what existed at baseline. It sees every tool.
The PreToolUse hook on `Edit|Write` is an early notice only: it denies with the
same reason so the agent learns before the stop.

Protected = existed at baseline and matches a glob. Default globs, defined once
in the ledger module: `test/**`, `tests/**`, `**/__tests__/**`, `**/test_*.*`,
`**/*_test.*`, `**/*.test.*`, `**/*.spec.*`, `.github/**`, `conftest.py`,
`pytest.ini`, `tox.ini`, `Makefile`, `package.json`, `noxfile.py`. Files
created during the task are free. `package.json` and `Makefile` are protected
because they define the check; the deny reason says authorisation is the way
through for legitimate edits. Authorisation is `jordan-ledger authorise`,
recorded with its reason and printed by the gate. In a solo session this makes
tampering visible, not impossible; say so in the docs. Non-git workspace: no
protection is claimed; the gate prints that once.

## R6. Irreversible guard (M5)

PreToolUse on `Bash`. Three classes in 3.0: recursive delete whose target is
outside the workspace or cannot be resolved (unexpanded variable, `~`, `/`);
force-push (`--force`, `-f`, `--force-with-lease`, `+ref`); publish
(`npm publish`, `twine upload`, `cargo publish`, `gh release create`).
In-workspace deletes pass, globs included. Default-branch push and credential
reads are opt-in through `$JORDAN_HOME/guard.json`. Decision: `ask` when
`permission_mode` is not a bypass mode, `deny` otherwise, with a reason that
says to return a decision request. Fail open, except: once the cheap prefilter
(`rm|push|publish|upload|release`) has matched, a parse failure denies. The
docs say plainly that this catches accidents, not intent, and is not a sandbox.

## R7. Trace and session-start (m4, M6)

Trace: PostToolUse and PostToolUseFailure append one JSON line: `ts,
session_id, agent_id, tool, ok, bytes`, plus the input truncated to 200
characters. It also performs the ledger claim (R3). Never blocks.

Session-start (plugin route only): injects `kernel.md` plus one line naming the
modules, through `additionalContext`, unless a kernel marker is found in
`~/.claude/CLAUDE.md`, `$cwd/CLAUDE.md` or `$cwd/.claude/CLAUDE.md`. Marker:
`<!-- jordan-kernel:begin -->`.

All hook scripts are Python 3, stdlib only, locate siblings from their own file
path, and import one shared `hooks/jordan_lib.py`.

## R8. Agent base (M7)

Three roles: `jordan-reader`, `jordan-builder`, `jordan-refuter`. Files:
`agents/templates/<name>.md`, `agents/shared/jordan-core.md` (cap 1,200
bytes), rendered `agents/<name>.md`. Frontmatter: `name`, one-line
`description`, `model`, `effort`, `tools`, `disallowedTools` where needed,
`omitClaudeMd: true`, `maxTurns`. The shared block carries: the loop; existing
checks are not edited and contradiction ends as `STATUS: BLOCKED` with
`impossible:`; done quotes the check output, else "implemented but
unverified"; open a ledger from the brief's acceptance command when
`jordan-ledger` is installed; final message in orchestrate's `STATUS:` shape.
The refuter template adds: write expectations from the request before reading
the diff; `REFUTED` needs a reproducing command and its output; `CONFIRMED`
lists the commands run. `tools/build-agents.py [--check]`,
`tools/lint-agents.py` (checks `tools`/`disallowedTools` directly: reader and
refuter have no Edit; one-line description; required fields; block cap),
`tools/new-agent.py <name> --role <role>`.

## R9. Install (M9)

One hook list: `hooks/hooks.json`. Two routes, use one per machine:

- Plugin: `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`;
  `claude plugin validate .` must pass.
- Plain copy: `install.sh [--home <dir>] [--dry-run] [--uninstall]`. Copies
  `skills/jordan/` to `<home>/.claude/skills/jordan/` (replace), hooks and
  `bin/` to `<home>/.claude/jordan/`, rendered agents to
  `<home>/.claude/agents/`; reads `hooks/hooks.json`, rewrites the
  `${CLAUDE_PLUGIN_ROOT}` prefix to the installed path, and merges into
  `<home>/.claude/settings.json` deduplicated by command, with a timestamped
  backup; inserts or replaces the kernel block between
  `<!-- jordan-kernel:begin -->` and `<!-- jordan-kernel:end -->` in
  `<home>/.claude/CLAUDE.md`, leaving every other byte of that file alone;
  links `jordan-ledger` into `<home>/.local/bin` and says so if that is not on
  PATH; skips the session-start hook (the CLAUDE.md block replaces it); warns
  if a `jordan` plugin is also installed. Idempotent: a second run changes
  nothing.

## R10. Repository layout and archive

Tree as DESIGN §9 with these changes: add `bin/jordan-ledger`,
`hooks/jordan_lib.py`, `install.sh`; drop `repeat_advisor.py`, `selector`,
`test_vocab_parity.py`. Archive to `docs/v2/` with `git mv`:
`universal-seed-prompt.md`, `JORDAN_v2_OVERVIEW.md`, `jordan_v2_flow.png`,
`spec/`, `prompts/`. Add `docs/v2/ERRATA.md` (the 45% rule, the MAKER
passages) and `docs/v2/README.md`. The research corpus (`report.md`,
`results/`, `synthesis.md`, the yaml files, `generate_report.py`) and the
review files stay where they are. `prompts/README.md` is recreated as a stub
pointing at `skills/jordan/kernel.md`. Root `CLAUDE.md` becomes the rendered
kernel block plus a short pointer, cap 3,400 bytes. Root `README.md` is
written for V3.

## R11. Eval in this PR (M8)

`eval/run.py`, `eval/report.py`, `eval/arms.json`, two pilot tasks (one bug
with a tempting wrong patch, one task whose tests contradict the request), each
`eval/tasks/<id>/{prompt.md,setup.sh,check.sh,hidden_check.sh,meta.json}`.
Arms: A0 no JORDAN (empty settings, no CLAUDE.md), A1 kernel only, A2 kernel
plus hooks, A3 A2 plus modules. Each run uses a temporary HOME and a fresh
copy of the task, so arms cannot leak into each other or into the operator's
real config. Tokens and cost come from `claude -p --output-format json`.
Measures: hidden check pass; false completion; protected-path tampering;
correct stop on the contradiction task; stopped as impossible on a solvable
task; tokens; wall time. One primary measure per arm comparison, named in
`eval/README.md` before any run. Merge rule: pilot tasks on every kernel or
hook change; the full set per release. The 30-task set is the operator's to
write from real failures; `eval/README.md` gives the template and says so.

## R12. Working rules for builders

Work only inside your assigned paths in
`/home/user/jordan-problem-solving-research`. Do not commit, do not switch
branches, do not edit `docs/v3/DESIGN.md`, `REDTEAM.md` or this file. Others
are editing sibling paths at the same time; never run `git stash`, `git
checkout -- .`, `git clean` or anything else that touches files you do not own.
Tests are `pytest` files under `tests/` named for your area and must pass
before you report. Report in at most 200 words: what you built, the exact test
command and its last lines of output, anything you could not verify, and any
place you departed from these rulings and why. No number you did not read from
a tool.
