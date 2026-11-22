# Building agents on the JORDAN base

The base is three role templates, one shared block, and three scripts. A new
agent is a copy of a role template with its own name, description and `## Role`
paragraph; the JORDAN discipline is spliced in at build time and is the same
bytes in every agent.

```
agents/shared/jordan-core.md       the shared block (cap 1,200 bytes)
agents/templates/<name>.md         what you edit
agents/<name>.md                   rendered; what gets installed
tools/new-agent.py                 scaffold
tools/build-agents.py [--check]    render / detect stale files
tools/lint-agents.py               check
tests/test_agents.py               python3 -m unittest tests.test_agents
```

## What the base gives an agent

Every agent runs with `omitClaudeMd: true`, so it does not see the kernel in
your `CLAUDE.md`. The shared block is the only JORDAN text it gets:

- the loop: act, run the check, read the output, correct; every retry changes
  something named; read code before editing it;
- existing checks are not edited; a contradiction or an impossible task ends
  as `STATUS: BLOCKED` with `OPEN: impossible: <why>`;
- stop and return a Decision Request before anything that cannot be undone, or
  a choice the brief left open;
- done quotes the check's output, otherwise "implemented but unverified";
- open a ledger from the brief's acceptance command when `jordan-ledger` is
  installed and the agent will change files;
- the final message in orchestrate's `STATUS:` shape, and its Decision Request
  line, both copied unchanged from
  `orchestrate/references/standing-orders.md` lines 53-59. A test pins them.

## What it deliberately does not give

- No routing: which model or tier a task goes to is the lead's decision.
- No dispatch doctrine: lanes, fences, fork classes, standing rulings S1-S10,
  tmux and lane-budget rules are orchestrate's and stay in its standing
  orders. A JORDAN agent is not an `orc-*` seat and does not carry that block.
- No task sizing (kernel rule 1) and no modules: a subagent gets one sized
  task from its brief.
- No enforcement. The block is instructions. Enforcement is the hooks (below)
  and the `tools` / `disallowedTools` fields.

## The three roles

| Role | Model, effort, turns | Tools | Derive from it when |
|---|---|---|---|
| `jordan-reader` | haiku, medium, 60 | Read, Grep, Glob, Bash; no Edit, Write, NotebookEdit | the agent finds and reports: recon, research, audits, summaries |
| `jordan-builder` | sonnet, high, 150 | Read, Grep, Glob, Edit, Write, Bash | the agent changes files to pass an acceptance command |
| `jordan-refuter` | sonnet, high, 100 | Read, Grep, Glob, Bash, Write; no Edit, NotebookEdit | the agent judges someone else's work by running it |

The model, effort and turn settings follow the `orc-*` seats of the same kind
(`orc-scout`, `orc-builder`, `orc-refuter`): volume reading on the cheap model,
building and judging one tier up. Change them in your template if your agent
needs otherwise; the lint does not check them beyond being present.

The reader keeps Bash for `wc`, `rg` and `git log`. Bash can write files, so
"cannot change files" is a tool-list fact about Edit and Write, not a sandbox.
The refuter keeps Write for reproduction scripts and Bash because a verdict
has to be executed. Its template adds the verdict protocol: expectations
written from the request before the diff is opened; `REFUTED` needs a
reproducing command and its output; `CONFIRMED` lists the commands run.

A frontmatter comment, `# jordan-role: <role>`, tells the lint which tool rule
applies, since your agent's name is free. It is a YAML comment; Claude Code
does not see it. The lint reads the real `tools` and `disallowedTools` fields,
and treats an omitted `tools` as "inherits everything, Edit included".

## Walk-through: one agent, end to end

Commands and output below are from a run on 2026-11-21 with `claude` 2.1.330,
in a scratch copy of this tree.

1. Scaffold. The name is kebab-case and need not start with `jordan-`.

```
$ python3 tools/new-agent.py changelog-reader --role reader --description "Reads CHANGELOG and release notes; reports what changed between two versions, with file:line."
created agents/templates/changelog-reader.md (from jordan-reader)
created agents/changelog-reader.md
next:
  1. edit agents/templates/changelog-reader.md: the description line and the `## Role` section. Leave the jordan-core marker and the jordan-role comment.
  2. python3 tools/build-agents.py && python3 tools/lint-agents.py
  3. install: ./install.sh copies agents/changelog-reader.md to ~/.claude/agents/changelog-reader.md (dispatch as `changelog-reader`); the plugin serves it as `jordan:changelog-reader`.
```

It refuses to overwrite and refuses a bad name (both exit 1):

```
$ python3 tools/new-agent.py changelog-reader --role reader
new-agent.py: agents/templates/changelog-reader.md exists; not overwriting
$ python3 tools/new-agent.py jordan:x --role reader
new-agent.py: name `jordan:x` must be kebab-case: lower-case letters, digits and single hyphens, no colon
```

2. Edit `agents/templates/changelog-reader.md`. The `## Role` section is the
   only hand-written text. Say what this agent is for, what it returns, and
   where it stops. Keep the description to one line, without `: ` inside it.

```
## Role
Changelog reader. Answer what changed between the versions your brief names,
from CHANGELOG.md and release notes only. Every finding carries `file:line`,
or the exact command you ran and what it printed. You change no files. If
the changelog does not say, report that; do not infer it from the code.
```

3. Build and lint.

```
$ python3 tools/build-agents.py changelog-reader
wrote agents/changelog-reader.md
$ python3 tools/build-agents.py --check
OK: 4 rendered agent files current
$ python3 tools/lint-agents.py
OK: 4 agent templates pass lint
```

4. Smoke-run it. Put the rendered file where Claude Code looks and dispatch
   one trivial task.

```
$ mkdir -p proj/.claude/agents && cp agents/changelog-reader.md proj/.claude/agents/
$ cd proj     # holds a CHANGELOG.md with two entries under 1.2.0
$ claude -p "Use the changelog-reader agent to report how many entries CHANGELOG.md lists under 1.2.0. Then print the agent's final message verbatim, with nothing added." \
    --model haiku --output-format stream-json --verbose --permission-mode bypassPermissions < /dev/null
```

   From the event stream: the init event listed `changelog-reader` among the
   agents; the lead called `Agent` with `"subagent_type": "changelog-reader"`;
   the subagent ran one Bash call (`grep -n "1\.2\.0" ...; cat -n ...`); and
   the final result was:

```
STATUS: DONE
EVIDENCE:
- `grep -n "1\.2\.0" CHANGELOG.md` → `3:## 1.2.0`
- `cat -n CHANGELOG.md` shows the 1.2.0 section runs from line 3 to line 5, with the two entries at lines 4 and 5. Line 7 starts the 1.1.0 heading, which is outside 1.2.0.

Count under 1.2.0: **2 entries**
- `<proj>/CHANGELOG.md:4` add --json flag
- `<proj>/CHANGELOG.md:5` fix crash on empty input

Heading: `<proj>/CHANGELOG.md:3`

CHANGED: none
OPEN: none
```

   (`<proj>` stands for the absolute scratch path.) Reported cost of that run:
   `total_cost_usd` 0.00420201. What this shows: the rendered file loads,
   YAML comments in the frontmatter included, the agent is dispatchable by
   its bare name, and its report opens with the `STATUS:` line and carries
   `EVIDENCE:`, `CHANGED:` and `OPEN:`. What it does not show: that the
   `tools` restriction or `maxTurns` were applied; nothing in this run tried
   to edit. Haiku put the answer in free lines between the labelled ones; the
   shape is instructed, not enforced.

   With `--output-format json` instead, the first result may be "the agent is
   running in the background"; the dispatch is asynchronous. Read the stream,
   or the last result.

5. Install. `./install.sh` copies every rendered `agents/*.md` to
   `~/.claude/agents/` (RULINGS R9); the plugin serves the same files.

## Names: plugin versus copied

| Route | The agent is called | Brief says |
|---|---|---|
| plain copy (`install.sh`, or `.claude/agents/` in a project) | `changelog-reader` | "Use the changelog-reader agent" |
| plugin | `jordan:changelog-reader` | "Use the jordan:changelog-reader agent" |

Use one route per machine. A brief written for one route names an agent the
other route does not have. A project or user copy wins over a plugin agent of
the same bare name. Two fields a copied agent may use are ignored when the
plugin ships it: `hooks` and `permissionMode`; the templates use neither.

## With orchestrate briefs

A JORDAN agent reads three sections of an orchestrate brief:

- **Acceptance**: the command there is the agent's check. It is the command
  the agent runs in its loop, quotes under `EVIDENCE:`, and passes to
  `jordan-ledger open --check`.
- **Fences**: the files it owns and the things it must not touch. The builder
  role says "change only the files your brief says you own".
- **Design rulings**: settled. A choice the rulings do not cover is a
  Decision Request in orchestrate's line shape, not a pick.

Its final message is the report orchestrate's lead already parses: `STATUS:`
on line 1 with one of `DONE`, `PARTIAL`, `BLOCKED`, `DECISION_REQUEST`. Kernel
rule 5's "the task cannot be done" has no fifth status; it is `BLOCKED` with
`impossible:` under `OPEN:`. A refuter's `DONE` means verdicts were reached;
the verdicts are under `EVIDENCE:`.

A JORDAN agent does not carry orchestrate's standing orders. If the lane needs
them (tmux fences, lane budget, S1-S10), dispatch an `orc-*` seat, or add
orchestrate's pointer line to the brief as its standing-orders file describes
for non-orc agent types.

## How the hooks treat a subagent

- **Done-gate** (SubagentStop): it acts only when an open ledger is owned by
  this session and this `agent_id` (RULINGS R4). So it gates an agent that
  opened its own ledger, and no other. A reader that opened nothing stops
  freely. A builder that ran `jordan-ledger open --check '<acceptance>'` has
  that command run when it tries to stop: green closes the ledger; red blocks
  once with the output and the three exits (fix it, `jordan-ledger mark
  unverified`, `jordan-ledger mark impossible`). The lead's own ledger is not
  the subagent's, and the reverse.
- **Protected paths**: checked at the same stop, for the same ledger owner. A
  builder that changed a test that existed at baseline is stopped unless it
  ran `jordan-ledger authorise <path> --reason '<why>'`.
- **Irreversible guard and trace**: apply to every Bash call and every tool
  call, subagent or not. The trace line carries the `agent_id`.
- Two agents in one worktree share a workspace root, so their ledgers can be
  confused (RULINGS R3, a known limit). Give builders separate worktrees.

The hooks are a separate part of this build; this section states what the
rulings specify, and was not run against the hook scripts.

## Changing the shared block

Edit between the markers in `agents/shared/jordan-core.md`, then run
`tools/build-agents.py`, `tools/lint-agents.py` and the tests. Every line is
paid for on every spawn of every agent; the cap is 1,200 bytes and the lint
fails above it. Do not reword the `STATUS:` or Decision Request lines; they
are orchestrate's, and `tests/test_agents.py` compares them to the source.
