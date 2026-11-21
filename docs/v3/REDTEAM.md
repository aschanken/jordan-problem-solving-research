# JORDAN V3 — Red-team findings

Date 2026-11-21. Target: `docs/v3/DESIGN.md` (architect draft). Not committed.
Tags: **[ran]** I executed it this session (`claude` 2.1.330, haiku, headless `-p`, throwaway
git repo in the scratchpad); **[read]** file and line; **[untested]** reasoned, not executed.
Hook experiments used a script that appends its stdin to a file; settings passed with `--settings`.

## BLOCKER

**B1. Nothing creates the ledger, so hooks 1 and 2 never fire.** (§6, §4)
Claim: done-gate and protected-paths are "inactive without a ledger"; state lives in
`.jordan/task.json`. Failure: the kernel text (§4) never mentions a ledger, no module is said to
write it, `ledger.py` has no described interface, and orchestrate has no step for it. A model given
kernel + hooks names its check in prose and stops; the gate sees no file and passes. Eval arm A2
then equals A1 by construction, and the decision rule "A2 no better than A1: keep hook 3 only"
deletes the centre of V3 for a wiring reason. Also undefined: task id, when a ledger closes, what
happens to a stale one (yesterday's baseline and acceptance command gating today's task).
Fix: specify `ledger.py open --check '<cmd>' [--protect glob] [--timeout s]`, `close`, `status`,
`mark unverified|impossible --reason`. Add to kernel rule 2: "Record it: `jordan-ledger open
--check '<command>'`." Ledger closes on a green gate; a ledger older than its session is ignored.

**B2. The ledger lives in the repo and a global Stop hook executes its command.** (§6)
Failure (a): clone any repo that ships `.jordan/task.json`; the first Stop runs its
`acceptance command` with the user's shell and no permission prompt, in every session on the
machine, because the hook is registered globally. Failure (b): one file per working directory, but
subagents and teammates share it. [ran] parent and subagent hooks reported the same `session_id`
and same `cwd`; two builders in one repo, or a lead plus builders, are all gated by one command and
one baseline. Failure (c): `cd sub/` moves `cwd`; the ledger is not found; silent no-op. Failure
(d): `.jordan/` shows in `git status`, in the baseline diff, and in commits.
Fix: store ledgers outside the workspace, `~/.claude/jordan/ledgers/<session_id>[.<agent_id>].json`
(plugin route: `${CLAUDE_PLUGIN_DATA}`), keyed by stdin `session_id`/`agent_id`, recording the git
toplevel. Never read a ledger from the repo. The trace file goes to the same place.

**B3. The done-gate fires on stops that are not completion claims.** (§6 hook 1; §12.1)
[ran] A Stop hook that exits 2 on a question-only turn:
```
claude -p "What is 2+2? Answer with just the number." --settings s.json --model haiku
Stop {'stop_hook_active': False}  then three more Stop events {'stop_hook_active': True}
usage: output_tokens 2726, cache_read_input_tokens 383134; permission_denials: [Bash ...]
```
The model answered, was blocked three times, and tried a Bash call to satisfy the gate. With a
ledger open, the same happens when: the user asks a question mid-task; an orchestrate lead ends a
turn after dispatching (it stops many times per task); any subagent stops ([ran] `SubagentStop`
fired for a `general-purpose` agent; a reader has no Edit and cannot make the check green, so it
loops to the counter); a teammate pane stops (it is a full session, event `Stop`, no
`agent_type`). I also saw two `Stop` events in one clean `-p` run, so the suite would run twice.
The always-open `unverified` exit then becomes the trained response to every block.
Fix, all four conditions before running anything: (1) a ledger owned by this `session_id` and this
`agent_id` is open; (2) stdin `background_tasks` is empty ([ran] the field exists on Stop); (3) the
tree changed since the last green run the hook itself recorded (hash of `git diff` + untracked
list), else pass without re-running; (4) block at most once per stop chain using
`stop_hook_active` ([ran] present: False, then True) and at most twice per ledger. The block
reason names the three exits. `SubagentStop` gates only an agent that opened its own ledger.

**B4. In the swarm workflow, V3 reaches none of the seats that do the work.** (§7, §8)
Claim: seats get the kernel "only through their definition"; orchestrate splicing `jordan-core`
is "follow-up, not in 3.0". Failure: the working seats are `orc-*` with `omitClaudeMd: true`
[read `orchestrate-skill/agents/orc-*.md:7-8`], built from orchestrate's block, and orchestrate's
routing table names no JORDAN agent [read SKILL.md:30-35]. So rule 5 (leave checks alone, the
impossible exit), the thesis of V3, is delivered to the lead, who never implements, and to no
builder. With B1, the hooks do not cover them either. `rg -n "jordan|JORDAN|kernel"
orchestrate-skill/orchestrate -l` returned nothing.
Fix: either state that 3.0 covers solo sessions only, or include in this release a patch for
orchestrate: two lines in its standing-orders block (existing checks are not edited; contradiction
ends as `STATUS: BLOCKED impossible:`), inside its 3.5 KB budget, and one lead step that opens the
ledger from the brief's `## Acceptance` command. Cut the four JORDAN archetypes if the patch ships.

## MAJOR

**M1. protected-paths cannot do what the table says.** (§6 hook 2)
(a) Matcher `Edit|Write` only. [ran] `echo a > t.txt && sed -i s/a/b/ t.txt` passed PreToolUse
with nothing to match; so do `git checkout`, `mv`, a python one-liner. (b) "Tests and checks
present at baseline" has no definition a script can apply; two builders will write different
globs. (c) The files that define the acceptance command are not listed: `package.json` scripts,
`Makefile`, `pytest.ini`, `conftest.py`, `tox.ini`. Editing `scripts.test` to `true` passes both
hooks. (d) The ledger is itself protected, yet "the ledger authorises the path": who may write it?
(e) Non-git directory: no baseline, silent pass.
Fix: make the stop-time `git diff --name-only <baseline>` the enforcing check (it sees every
tool) and the PreToolUse hook an early notice. Hard-code default globs in `ledger.py`
(`test*/`, `*_test.*`, `test_*.*`, `*.spec.*`, `.github/`, the config files above); authorisation
is `ledger.py authorise <path> --reason`, recorded and printed in the gate's advisory so a reader
sees it. Non-git: write an advisory, do not claim protection.

**M2. Re-running the acceptance command: timeouts pass silently, and the red-run rule is
uncheckable.** (§6 hook 1)
"Error or timeout allows the stop" means a 20-minute suite always passes the gate; the hook's
default timeout is 600 s [read spec, Hooks]. A flaky test blocks, and the agent cannot touch it
(hook 2), so it marks `unverified`. A command with side effects (deploy, migration) runs again at
every stop. The hook cannot know a task is a bug fix, nor that a "recorded red run predates the
fix"; the agent records both.
Fix: ledger field `timeout_s` (default 120), hook registered with `timeout` above it; on timeout
write `passes: "timeout"` and inject "report this as unverified", never a silent pass. Cut the
red-run requirement from the hook; keep it as text in `verify`. `ledger.py open` refuses commands
matching the hook 3 list.

**M3. Kernel rule 1 sends ordinary work to DEEP and loads `plan` on nearly everything.** (§4, §5)
"DEEP (hard to undo, or no fast check)": a README edit or a config comment has no fast check, so
it is DEEP. In orchestrate, DEEP means the `panel` workflow and PREMIUM seats [read SKILL.md:33,
108]; the parity test pins the strings, not the meaning. "STANDARD (several steps)" is most tasks,
and `plan` loads "when the task is STANDARD or DEEP and work is about to start": purpose, end
state, assumption list, five triggers. That contradicts rule 3 ("try the direct route first; plan
only the next step") and restores the ceremony §1 removes. v2's explicit never-FAST list
(credentials, deletion, infrastructure, untrusted input) is dropped with no stated reason; R §6
asked to add the three-property question here.
Fix: "DEEP: hard to undo. No fast check: say so and report unverified (rule 2)." Trigger `plan`
on "the direct attempt failed its check, or the step is hard to undo", not on the tier.

**M4. Rules 3 and 7 misfire for a lead and for any run with no human.** (§4, §8)
Rule 3 tells an orchestrate lead to try the work directly; orchestrate forbids that
[read SKILL.md:25-26]. §8 resolves it in a table the model never sees. Rule 7 says "ask": a
subagent, a headless run and the swarm (`--dangerously-skip-permissions`,
[read swarm/paneopticon.sh:557]) have nobody to ask. "Sending messages" read literally forbids
SendMessage, which orchestrate seats use for every report. "Reaches outside the workspace" covers
reading `~/.claude/skills`, `npm install`, a web fetch.
Fix: rule 3 opens "When you are the one doing the work,". Rule 7: "Before an action that cannot
be undone, get a decision: ask the user, or if none is reachable return a Decision Request and
stop." Replace the list tail with "sending anything to people or services outside the session".

**M5. irreversible-guard blocks common work and is bypassed by one level of indirection.** (§6 hook 3)
Blocks: `rm -rf dist/*` (a glob, in workspace); `git push` on `main` in a solo repo (this repo's
own v2 git rule merges to main); `cat .env.example`. Passes: `sh -c`, a script file,
`python -c "shutil.rmtree"`, `find -delete`, `git push origin +main`, `gh api -X DELETE`.
"Push to the default branch" needs the hook to run git to resolve branch and remote; unspecified.
Deny is right when nobody can answer, wrong in an interactive session, where
`permissionDecision: "ask"` exists [read spec]. [untested] deny under bypass mode: my run with
`--dangerously-skip-permissions` was refused by this environment. Deny in default mode [ran]:
`echo MARKER_DENY` produced PreToolUse and no PostToolUse.
Fix: `ask` when `permission_mode` is not bypass, `deny` otherwise. Expand globs against the
workspace before judging. Ship three classes in 3.0 (delete outside workspace or unresolved,
force-push, publish); default-branch push and credential reads are opt-in per project. Say in the
docs that it catches accidents, not intent. On §12.5: fail closed only after a cheap prefilter
(`rm|push|publish|delete|destroy`) matched and parsing then failed.

**M6. session-start cannot build its advisory, and its double-kernel guard checks one file.** (§6 hook 6)
[ran] SessionStart stdin keys: `cwd, hook_event_name, scratchpad_dir, session_id, source,
transcript_path`. No `permission_mode`. "No sandbox is detected" has no defined signal. The
marker is looked for only in `~/.claude/CLAUDE.md`; this repo's own `CLAUDE.md` will carry the
kernel block (§8 back-compat), so a plugin user working here gets it twice.
Fix: cut the advisory from 3.0, or emit it once per session from the first PreToolUse (the field
is there [ran]). Check the marker in `$cwd/CLAUDE.md` and `$cwd/.claude/CLAUDE.md` too. The
plain-copy route does not register hook 6 at all.

**M7. Agent base: several parts are decoration or conflict with orchestrate.** (§7)
(a) `CONFIRM:` as "first output": only a subagent's final message returns to the lead; nobody and
no hook reads the first. It also contradicts standing orders "Never restate the brief"
[read standing-orders.md:56]. Evidence is [r] plus analogy (§12.6). (b) Rule-of-two tags are a
self-declared comment; the builder is tagged B+C "no web" while holding Bash (curl) and reading
repo content, so it holds all three. The lint checks the comment, not the tools; R §3.8 #3 asked
for a dispatcher refusal, which is not built. (c) Refuter: "Edit disallowed" with Write and Bash
allowed is the same as orc-refuter [read orc-refuter.md:6-7], fine, but the lint rule "a refuter
with Edit" tests nothing real. (d) Bare names `reader`, `builder`, `refuter`, `selector` in
`~/.claude/agents/` are generic and differ from the plugin names, so a brief is not portable
across routes. (e) Swarmfucker has no install path for them: `install_agents` copies only
`agents/{gateway,anthropic}` and web-search [read install.sh:208-255], and
`docs/verification.md` §3 expects an exact `ls ~/.claude/agents` listing. (f) `selector`
duplicates `orc-judge`.
Fix: 3.0 ships templates, the shared block, build and lint only. Cut `CONFIRM:`, the tags and
`selector`. Name files `jordan-<role>`. Lint checks `tools`/`disallowedTools` directly.

**M8. The eval as specified cannot run or decide.** (§10)
(a) A0 uses `--bare`; `claude --help` says bare-mode auth "is strictly ANTHROPIC_API_KEY or
apiKeyHelper"; `echo ${ANTHROPIC_API_KEY:+yes}` printed nothing here, and the operator's posture
file tracks 5h/7d subscription credit. (b) "Tokens and wall time from the trace": A0 and A1 have
no hooks, and tool-event stdin carries no token counts. [ran] `--output-format json` returns
`usage` and `total_cost_usd` for every arm. (c) "A1 not better than A0 on any measure" with seven
measures will almost never be true by chance; the rule cannot fire. (d) "No kernel change merges
without a paired run" is up to 360 runs per edit and will be skipped. (e) Thirty tasks "from the
operator's own repositories and past failures" cannot be written by builders in this PR. (f) No
measure for false impossible-stops on solvable tasks, the cost side of rule 5; the 54% to 9%
figure is one non-Claude model on tasks built to be impossible.
Fix: this PR ships `run.py`, `report.py`, two pilot tasks, and arm definitions; A0 is defined as
"no plugin, no hooks, empty CLAUDE.md" via `--setting-sources` [untested] if no API key. One pre-registered primary
measure per arm comparison. Add "stopped as impossible on a solvable task". The merge rule
becomes: pilot tasks on every kernel change, full set per release.

**M9. Install and migration are underspecified in ways that will diverge.** (§8)
(a) Installer registrations are a hard-coded Python tuple list `(event, matcher, cmd, args)` with
no `timeout` or `onFailure` [read install.sh:480-511]; "swarmfucker merges the same list" as
`hooks.json` means two lists. (b) Where swarmfucker gets JORDAN is unstated:
`install_bundled_skills` copies `swarmfucker/skills/*` [read install.sh:195-206], so vendored
copy or a clone like orchestrate's? Hooks sit outside `skills/jordan/`, so "self-contained" does
not cover them or `ledger.py`. (c) Plugin plus plain-copy on one machine registers every hook
twice. (d) Files to change beyond `verification.md:21`: `install.sh:159-170` and `summary()` line
525, `docs/install-guide.md:95-97,118`, `docs/architecture.md:65-74`, `README.md:95`. (e) The
vendored `framework/CLAUDE.md` is 1,067 bytes larger than this repo's (`wc -c`: 11,366 vs 10,299);
with rg and bonemot sections it will not fit the 3,072-byte cap, and `render-claude-md.py` lives
in a different repo from the file it must render. The bonemot section keeps "(MANDATORY)".
Fix: installer reads `hooks/hooks.json` and rewrites the `${CLAUDE_PLUGIN_ROOT}` prefix; extend
the tuple to a dict with `timeout`. Each hook exits early if `CLAUDE_PLUGIN_ROOT` is unset and a
plugin copy of itself is installed (or the reverse; pick one). State: vendored under
`swarmfucker/framework/jordan/`, synced by a script with a `--check` test. Separate cap for the
vendored file (kernel block cap + measured size of the two sections).

## MINOR

**m1. Kernel wording.** Rule 8 offers three marks (verified, likely, unknown) and in the same
rule uses a fourth ("unverified"). Rule 9 joins two unrelated rules; its "a fresh reader" counts
as a check, against §1 item 4 and G:F11. "Hand up" (rule 4) is undefined. The first line scopes
the kernel to tasks that change files, so the numbers and claim-marking rules lapse on research
and analysis, which v2 covered. v2's "Don't know: say so" is gone without a row in §2. The
closing "Modules in the jordan skill" line dangles in arm A1 and in any seat without the skill.

**m2. `stop_hook_active` is real** [ran, 2.1.330]; `spec` marks it unverified. I saw no native
cap in three consecutive blocks, so §2's "block cap exists natively" is unconfirmed; keep the
counter.

**m3. Departures from the report not listed in §12.9.** `TaskCompleted` as a completion event
(teams close tasks, not turns); the preflight that refuses to start (reduced to one advisory
line); skip-marker and threshold detection in diffs (R §3.2 #1; path globs miss a new
`@skip` inside an authorised file); `NOT_REFUTED` naming.

**m4. trace.** No location, schema or size bound. `tool_input` holds Write contents and Bash
commands with tokens. Fix: outside the repo (B2), fields `ts, session_id, agent_id, tool, ok,
bytes`, input truncated to 200 characters.

**m5. Cut from 3.0:** hook 5 (no evidence, §6 says so), `selector`, the `UNVERIFIABLE` proposal,
`new-agent.py` (a copy command), and the "under ten minutes" claim, which nothing measures.
Give `SKILL.md` a byte cap as a number; §9 says only "capped".

## (a) Must change before build

1. Define the ledger: location outside the repo keyed by `session_id`/`agent_id`, the `ledger.py`
   CLI, open/close lifecycle, and the kernel line that opens it. (B1, B2)
2. Done-gate runs only for the ledger's owner, with no background tasks, on a changed tree, once
   per stop chain; reader and built-in subagents are never gated. (B3)
3. Decide and write down: solo-only 3.0, or ship the orchestrate standing-orders patch and the
   lead's ledger step now. (B4)
4. Enforce protected paths by diff at stop; fixed default globs including acceptance-defining
   config; `authorise` is a recorded CLI call. (M1)
5. Timeout is an explicit `timeout` verdict, never a silent pass; drop the red-run check from the
   hook. (M2)
6. Rewrite kernel rules 1, 3, 7 and the `plan` trigger as given in M3 and M4.
7. Hook 3: `ask` or `deny` by `permission_mode`, three classes, glob expansion. (M5)
8. Hook 6: drop the permissions advisory or move it to PreToolUse; widen the marker check. (M6)
9. Agent base: templates, block, build, lint. No `CONFIRM:`, tags, `selector`. Prefix names. (M7)
10. Eval in this PR: runner, two pilot tasks, token counts from `--output-format json`. (M8)
11. One hook list, read by the installer; name every swarmfucker file that changes; say how the
    vendored copy is synced. (M9)

## (b) Tried to break, could not

- Kernel size: extracted the fenced block, `wc -c` gives 2,418, as stated.
- Exit 2 on Stop blocks and the model continues with the reason [ran].
- PreToolUse `deny` JSON on stdout with exit 0 blocks the call [ran].
- `agent_type` and `agent_id` are present on a subagent's PreToolUse, PostToolUse and
  SubagentStop; absent in the main session [ran]. SessionStart carries `source` [ran].
- Frontmatter set (`name, description, model, effort, tools, disallowedTools, omitClaudeMd,
  maxTurns`) matches `orc-*` files and the spec sheet [read].
- The swarmfucker parity test compares only `agents/{gateway,anthropic}` against orchestrate's
  files with the same name [read tests/test_agent_parity.py]; new JORDAN agents do not break it.
