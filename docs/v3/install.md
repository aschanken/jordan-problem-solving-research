# Installing JORDAN V3

There are two routes. Use one per machine. Both give a session the same four
things: the kernel in context on every step, the `jordan` skill with its seven
modules, the hooks (done-gate, protected paths, irreversible-action guard,
trace), and the three base agents. Both read their hook list from the one file
`hooks/hooks.json`.

| | Plugin | Plain copy |
|---|---|---|
| Kernel reaches context through | the session-start hook | a block in `~/.claude/CLAUDE.md` |
| Skill name | `jordan:jordan` | `jordan` |
| Agent names | `jordan:jordan-builder`, `jordan:jordan-reader`, `jordan:jordan-refuter` | `jordan-builder`, `jordan-reader`, `jordan-refuter` |
| `jordan-ledger` on the agent's PATH | yes, the plugin's `bin/` is added | through a link in `~/.local/bin` |
| Changes your `settings.json` hooks and `CLAUDE.md` | no | yes, with backups |
| Updated by | `claude plugin update jordan@jordan` | running `install.sh` again |

Requirements for both: Python 3 on PATH as `python3` (the hooks and the ledger
CLI are stdlib-only Python), and `git` for protected-path checks. The plain
copy also needs `bash`.

## Route 1: plugin

```sh
claude plugin marketplace add aschanken/jordan-problem-solving-research
claude plugin install jordan@jordan
```

From a local checkout, give the path instead of the GitHub name:

```sh
claude plugin marketplace add /path/to/jordan-problem-solving-research
claude plugin install jordan@jordan
```

To try it for one session without installing anything:

```sh
claude --plugin-dir /path/to/jordan-problem-solving-research
```

What goes where: Claude Code records the marketplace and the enabled plugin in
`~/.claude/settings.json` (`extraKnownMarketplaces`, `enabledPlugins`) and in
`~/.claude/plugins/`. The repository is its own marketplace
(`.claude-plugin/marketplace.json` lists one plugin with `"source": "./"`), so
the whole repository is the plugin, including the research corpus; the cached
copy measured 7.9M. `.claude-plugin/plugin.json` names the three rendered
agents explicitly, because without that the files under `agents/templates/`
and `agents/shared/` would be registered as agents too.

Check it worked:

```sh
claude plugin list          # shows jordan@jordan, enabled
claude plugin details jordan@jordan
```

Then, in a session, ask the agent to quote rule 5 of the JORDAN kernel. It
should answer from context without reading a file.

Uninstall:

```sh
claude plugin uninstall jordan@jordan
claude plugin marketplace remove jordan
```

Session state under `$JORDAN_HOME` (ledgers and traces) is not removed by
this; delete `~/.claude/jordan` by hand if you do not want it.

## Route 2: plain copy

From a checkout of this repository:

```sh
./install.sh                 # into $HOME
./install.sh --dry-run       # print what would change; change nothing
./install.sh --home <dir>    # into <dir>/.claude and <dir>/.local/bin
./install.sh --uninstall     # remove what the install added
```

What it puts where, under the home directory:

| Path | Content |
|---|---|
| `.claude/skills/jordan/` | copy of `skills/jordan/`, replaced as a whole |
| `.claude/jordan/hooks/`, `.claude/jordan/bin/` | copies of `hooks/` and `bin/`, replaced as a whole |
| `.claude/agents/jordan-{builder,reader,refuter}.md` | the rendered agents; `agents/templates/` and `agents/shared/` are not copied |
| `.claude/settings.json` | the hooks from `hooks/hooks.json`, with `${CLAUDE_PLUGIN_ROOT}` rewritten to `<home>/.claude/jordan`, merged in |
| `.claude/CLAUDE.md` | the kernel between `<!-- jordan-kernel:begin -->` and `<!-- jordan-kernel:end -->` |
| `.local/bin/jordan-ledger` | symlink to `.claude/jordan/bin/jordan-ledger` |
| `.claude/jordan/install.json` | record of what was added, read by `--uninstall` |

How it treats files that are yours:

- `settings.json`: unrelated keys and your own hooks are kept. A JORDAN hook
  is added only if the same command is not already registered for that event
  and matcher, so a second run adds nothing. The file is rewritten as
  two-space-indented JSON when it changes; key order is kept. A missing or
  empty file is treated as `{}`. A file that is not valid JSON (comments
  included), is not an object, or has a `hooks` entry of an unexpected shape
  stops the run before anything is written.
- `CLAUDE.md`: only the bytes between the markers are replaced. If there is
  no block yet, it is appended after a blank line; nothing above it changes.
  A begin marker without an end marker stops the run. The block is written
  by the same code as `tools/render-claude-md.py`.
- The session-start hook is not registered on this route; the `CLAUDE.md`
  block does its job.
- Every existing file or directory that is about to change is first copied to
  `<home>/.claude/jordan-backups/<YYYYmmdd-HHMMSS>/<same relative path>`.
- A second run changes no file and prints "Nothing changed".
- If `<home>/.local/bin` is not on PATH the installer says so. Agents call
  `jordan-ledger` by name, so put it on PATH.

Check it worked:

```sh
jordan-ledger status                           # "no ledger for <dir>" is the healthy answer
python3 tools/render-claude-md.py ~/.claude --check
./install.sh --dry-run                         # "already installed ... Nothing changed"
```

Then ask an agent in a new session to quote rule 5 of the JORDAN kernel.

Uninstall: `./install.sh --uninstall` removes the skill directory, the three
agents, the JORDAN hook entries, the kernel block, the ledger link,
`.claude/jordan/hooks`, `.claude/jordan/bin` and `install.json`. It removes
`settings.json` or `CLAUDE.md` only if the install created the file and
nothing else is in it. It leaves your other settings, hooks, agents and
skills, anything you wrote in `CLAUDE.md`, the backups, and session state in
`.claude/jordan/ledgers` and `.claude/jordan/trace` (it says so when it leaves
state behind). If an install replaced a file of yours with the same name, the
earlier version is in `jordan-backups`; uninstall does not put it back.

## One route per machine

Do not install both. What happens if both are present (run on 2026-11-21, see
Verified):

- The kernel is in context once. The session-start hook finds the marker in
  `~/.claude/CLAUDE.md` and stays silent.
- Every other hook runs twice per event, once from the plugin and once from
  `settings.json`: two trace lines per tool call, and the done-gate runs the
  check twice.
- The skill and the agents each exist under two names.

`install.sh` warns when it sees a `jordan` plugin in
`~/.claude/plugins/installed_plugins.json` or in `enabledPlugins`. The plugin
installer cannot warn about a plain copy. Remove one of the two with its
uninstall command above.

## `JORDAN_HOME`

Ledgers, traces and the optional `guard.json` live in `$JORDAN_HOME`, default
`~/.claude/jordan`, on both routes. They are never inside the workspace.

```
$JORDAN_HOME/ledgers/<session_id>[.<agent_id>].json
$JORDAN_HOME/ledgers/pending-<key>.json
$JORDAN_HOME/trace/<session_id>.jsonl
$JORDAN_HOME/guard.json            opt-ins for the irreversible-action guard
```

The hooks and the `jordan-ledger` command must agree on this directory, or a
ledger an agent opens is never seen by the done-gate. They agree by default.
Set `JORDAN_HOME` yourself only if you set it in the environment Claude Code
starts from, so that both the hooks and the agent's shell inherit it. Two
cases need care:

- `install.sh --home <dir>` with a `<dir>` that is not your `$HOME`: the hooks
  are installed under `<dir>` but still keep state under `$HOME/.claude/jordan`
  unless sessions run with `HOME=<dir>` or `JORDAN_HOME=<dir>/.claude/jordan`.
- `CLAUDE_CONFIG_DIR`: the hooks do not follow it for state. Set `JORDAN_HOME`
  as well. This combination was not run.

## Limits

- The irreversible-action guard is a denylist over Bash commands (recursive
  delete outside the workspace, force-push, publish). It catches accidents. It
  is not a sandbox and does not stop a command written to avoid it.
- Protected paths are checked against git at stop time and announced early on
  `Edit` and `Write`. In a solo session the agent that wants to change a test
  is the same agent that can run `jordan-ledger authorise`; tampering is made
  visible to the reader of the report, not impossible. In a workspace that is
  not a git repository no protection is claimed.
- The done-gate runs only when a ledger is open for the session. An agent that
  never opens one is not gated. After one block the next stop is let through,
  with the ledger left open and `passes: false`.
- The hooks need `python3` on the PATH of the process that runs hooks. If it
  is missing the hooks fail and Claude Code carries on without them.
- V3's effect on results is not measured yet; see `eval/README.md`.

## Installing through swarmfucker

Not part of this release. The intended follow-up, as a pull request in the
swarmfucker repository:

- swarmfucker's `install.sh` stops copying the v2 framework files and its own
  hook tuple list for JORDAN, and instead runs this repository's
  `install.sh --home "$HOME"` from a checkout (cloned the way it already
  clones `orchestrate-skill`) or from a vendored copy.
- A vendored copy must contain `install.sh`, `skills/jordan/`, `hooks/`,
  `bin/`, the three `agents/jordan-*.md` and `tools/render-claude-md.py`;
  `install.sh` reads all of them relative to its own location.
- swarmfucker keeps its own hooks in `settings.json`; the merge here leaves
  them in place (the test suite installs over a settings file that already has
  a `PreToolUse` `Bash` hook and a `Notification` hook).
- Backups differ: swarmfucker writes `<file>.swarmfucker-backup-<ts>` beside
  the file; this installer writes under `.claude/jordan-backups/<ts>/` so that
  a backed-up skill directory is not picked up as a second skill.

## Verified

Date 2026-11-21, Claude Code 2.1.330, Linux, model `haiku` for live sessions.
Each live session ran with `HOME` set to a fresh temporary directory, which
moves `~/.claude` (config, settings, plugins) and the default `JORDAN_HOME`
together; that the temporary home took effect was confirmed by the files
Claude Code and the hooks created there and by the real `~/.claude/plugins`
gaining no marketplace entry. `CLAUDE_CONFIG_DIR` was not used. The temporary
directories were outside the session scratchpad, because 2.1.330 does not load
a project `CLAUDE.md` from under it.

Validator:

```
$ claude plugin validate .
  > skills: jordan:jordan
  > agents: jordan:jordan-builder
  > agents: jordan:jordan-reader
  > agents: jordan:jordan-refuter
  > bin: jordan-ledger
√ Validation passed with warnings        (exit 0)
$ claude plugin validate .claude-plugin/marketplace.json --strict
√ Validation passed                      (exit 0)
```

Before `plugin.json` named the agents, the same command also listed
`jordan:shared:jordan-core` and `jordan:templates:jordan-{builder,reader,refuter}`.
`"source": "./"` is accepted by the validator and by a real
`marketplace add` and `install` (below).

Plain copy (`./install.sh --home $T/h1`, then in a git repository with one
failing test, `HOME=$T/h1 PATH=$T/h1/.local/bin:$PATH claude -p ... --model haiku
--output-format stream-json --verbose --permission-mode acceptEdits
--allowedTools Bash Edit Read Write`):

- Session init listed skill `jordan` and agents `jordan-builder`,
  `jordan-reader`, `jordan-refuter`.
- Asked to quote rule 5 from context without reading a file, the agent
  answered: "Leave existing checks alone. Do not edit, skip or special-case
  tests that existed before the task unless the task says to. ..." Its only
  tool call before that was `jordan-ledger open`.
- `jordan-ledger open --check 'python3 -m pytest -q'` printed
  `ledger open for .../w1`, and hook events `PreToolUse:Bash` and
  `PostToolUse:Bash` returned exit 0.
- On stop: `Stop hook feedback: [command hook]: JORDAN done-gate: the check
  failed (exit 1): python3 -m pytest -q` followed by the pytest output and the
  three ways forward. The agent continued instead of stopping.
- Afterwards `$T/h1/.claude/jordan/trace/<session>.jsonl` (2 lines) and
  `$T/h1/.claude/jordan/ledgers/<session>.json` existed, the ledger showing
  `state: open, passes: False, blocks: 1`.

Plugin, session only (`HOME=$T/h2 claude -p ... --plugin-dir <repo>`, empty
home, working directory with no `CLAUDE.md`):

- `SessionStart:startup` hook exit 0 with `additionalContext` beginning
  `# JORDAN kernel v3`; the agent quoted rule 5 word for word.
- Session init: plugin `jordan` version 3.0.0 (`jordan@inline`), skill
  `jordan:jordan`, agents `jordan:jordan-builder`, `jordan:jordan-reader`,
  `jordan:jordan-refuter`; no template or shared-block agent.
- `command -v jordan-ledger` in the Bash tool printed `<repo>/bin/jordan-ledger`.
- A trace file appeared under `$T/h2/.claude/jordan/trace/`.

Plugin, marketplace route against the local path, in an isolated home
(`HOME=$T/h3`):

```
$ claude plugin marketplace add /home/user/jordan-problem-solving-research
√ Successfully added marketplace: jordan (declared in user settings)
$ claude plugin install jordan@jordan
√ Successfully installed plugin: jordan@jordan (scope: user)
$ claude plugin list
  > jordan@jordan   Version: 3.0.0   Scope: user   Status: √ enabled
```

A session in that home had the session-start hook return 2,869 bytes and the
agent quote rule 5; init listed the same skill and three agents.

Both routes in one home (`./install.sh --home $T/h3` on top of the plugin):
the installer printed `Warning: a jordan plugin is also installed
(jordan@jordan)`; a session showed `SessionStart` returning 0 bytes, the agent
reporting one copy of the kernel, `PreToolUse:Bash`, `PostToolUse:Bash` and
`Stop` each firing twice, and 2 trace lines for one tool call.

Tests: `python3 -m pytest -q tests/test_install.py` (36 tests, all against
temporary homes).

Not verified:

- `claude plugin marketplace add aschanken/jordan-problem-solving-research`
  (the GitHub form): the manifests are not on the default branch yet.
- `claude plugin validate . --strict`: exits 1 on two warnings from files the
  layout requires, the root `CLAUDE.md` ("not loaded as project context") and
  `agents/shared/jordan-core.md` ("No frontmatter block found"). Neither is
  registered or loaded by the plugin.
- `--profile directory` (catalog submission) fails for a missing `LICENSE`;
  the repository has none and choosing one is the owner's decision.
- `claude plugin update` and `claude plugin uninstall` for this plugin.
- `CLAUDE_CONFIG_DIR` in place of `HOME`.
- A green done-gate and a subagent's `SubagentStop` on an installed copy; the
  hook tests cover both against the repository copy.
- macOS and Windows.
- The swarmfucker integration.
