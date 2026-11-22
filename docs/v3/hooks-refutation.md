# JORDAN v3 hooks — independent refutation

Date: 2026-11-21. Subject: `hooks/jordan_lib.py`, `done_gate.py`, `protected_paths.py`,
`irreversible_guard.py`, `trace.py`, `session_start.py`, `hooks.json`, `bin/jordan-ledger`,
as they were in the working tree on that date. Every verdict below comes from a command that was run against a copy of those
files in a `mktemp -d` directory, with a temporary `JORDAN_HOME`, `HOME` and git repos.
Nothing in the repository was modified apart from this file.

Method: the expectations and probe list were written from `docs/v3/RULINGS.md` R3–R7
before reading the code; then each hook was driven as a subprocess with crafted stdin.

## Harness (all repros assume this is sourced)

```bash
T=$(mktemp -d); cp -r hooks bin skills $T/
export JORDAN_HOME=$T/jh HOME=$T/home GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null \
  GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@x.invalid GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@x.invalid
unset CLAUDE_CODE_SESSION_ID; mkdir -p $HOME; H=$T/hooks; L=$T/bin/jordan-ledger
mkrepo(){ mkdir -p "$1/tests"; (cd "$1"; echo x=1 >app.py; echo 'assert True' >tests/test_app.py; git init -q; git add -A; git commit -qm base); }
claim(){ printf '{"session_id":"%s","cwd":"%s","hook_event_name":"PostToolUse","tool_name":"Bash","tool_input":{"command":"%s"}%s}' \
  "$1" "$2" "$3" "${4:+,\"agent_id\":\"$4\"}" | python3 $H/trace.py; }
stop(){ printf '{"session_id":"%s","cwd":"%s","stop_hook_active":false%s}' "$1" "$2" "${3:+,\"agent_id\":\"$3\"}" \
  | python3 $H/done_gate.py; echo "[exit $?]"; }
guard(){ python3 -c 'import json,sys;print(json.dumps({"session_id":"S","cwd":sys.argv[2],"tool_name":"Bash","permission_mode":sys.argv[3],"tool_input":{"command":sys.argv[1]}}))' \
  "$1" "${2:-$T/r}" "${3:-default}" | python3 $H/irreversible_guard.py; }
mkrepo $T/r; cd $T/r
```

## Measured no-ledger latency

30 runs each, no `JORDAN_HOME` present, ordinary input (`python3 -c pass` baseline: 15.0 ms median).

| hook | median | p90 | max |
|---|---|---|---|
| done_gate | 23.1 ms | 29.7 ms | 30.6 ms |
| protected_paths | 21.7 ms | 28.3 ms | 30.3 ms |
| irreversible_guard (`ls -la`) | 19.9 ms | 27.6 ms | 29.4 ms |
| irreversible_guard (`rm -rf ./build`, prefilter hit) | 28.7 ms | 34.8 ms | 38.7 ms |
| trace | 23.4 ms | 28.8 ms | 30.8 ms |
| session_start | 20.6 ms | 26.9 ms | 28.6 ms |

So each hook adds about 5–14 ms on top of Python startup. The exception is the guard on very
large commands (R-5).

## REFUTED, ranked by harm to a real user

### R-1. After two blocks the gate keeps re-running the check at every stop (R4 item 4; property a)

R4: "Before running anything, all must hold, else exit 0 silently: … this ledger has been
blocked fewer than two times." The code (`_gate`, the comment "a tree that changed since is
still checked once") re-runs the check whenever the tree changed. The ledger also stays
`open` for good. So every later turn of that session that edits anything pays the full check
time (up to 540 s) and prints a message.

```bash
python3 $L open --check "echo run >> $T/runs; false" >/dev/null; claim A $T/r 'jordan-ledger open'
for i in 1 2 3 4; do echo "edit $i" >> app.py; stop A $T/r 2>/dev/null | tail -1; done; wc -l < $T/runs
```
Observed: exits `2, 2, 0, 0`, and `runs=4`. Ledger `open 2 False`. Stops 3 and 4 ran the check after the cap.

### R-2. Trace writes secrets, and for Write it records file content before the path (property h)

`trace.py` dumps `tool_input` with `sort_keys=True`, so for Write the `content` key comes
before `file_path`. The first 200 characters of every written file go to
`$JORDAN_HOME/trace/<sid>.jsonl`, which is created with mode 0644. Bash commands that carry
tokens are recorded as typed. R7 asks for the input, so the spec allows this, but property (h) does not.

```bash
echo '{"session_id":"S","cwd":"'$T/r'","hook_event_name":"PostToolUse","tool_name":"Write","tool_input":{"file_path":"'$T/r'/.env","content":"AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY"},"tool_response":"ok"}' | python3 $H/trace.py
cat $JORDAN_HOME/trace/S.jsonl
```
Observed: `"input": "{\"content\": \"AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY\", \"file_path\": ...`.
The same happens for `curl -H "Authorization: Bearer ghp_..."`.

### R-3. A subagent's stop takes the main agent's pending ledger; the main stop then passes ungated (properties b, g; "never a silent pass")

`claim_pending(immediate=True)` runs on every Stop/SubagentStop. The session hint can only
tell sessions apart, and a subagent has the same session id as its parent. So a SubagentStop
that arrives before the opener's own claim takes the ledger as `<sid>.<agent>.json`. The
subagent is then blocked with the parent's check, and the parent's Stop finds no ledger and exits 0.

```bash
CLAUDE_CODE_SESSION_ID=A python3 $L open --check "echo x; false" >/dev/null
echo '{"session_id":"A","agent_id":"sub1","cwd":"'$T/r'","hook_event_name":"SubagentStop","stop_hook_active":false}' | python3 $H/done_gate.py; echo $?
stop A $T/r; ls $JORDAN_HOME/ledgers
```
Observed: SubagentStop exit `2` ("the check failed … echo x; false"). Main stop `[exit 0]` with no output. Ledgers: `A.sub1.json`.

### R-4. Without a session hint, any session's Stop in the repo takes a pending ledger at any age up to 15 min, with no grace (properties b, g)

The 10 s grace applies only to non-`jordan-ledger` tool events; Stop is always `immediate`.
The hint is absent when the user runs `jordan-ledger open` in their own terminal, or when the
CLI's environment lacks `CLAUDE_CODE_SESSION_ID`. The opener's own claim is also missed when
the `PostToolUse` cwd is outside the root, e.g. `cd r && jordan-ledger open …` issued from
the parent directory. In all of these cases an unrelated session that stops in the repo runs the check and is blocked by it.

```bash
python3 $L open --check "echo ran >> $T/runs; false" >/dev/null; touch -d '-899 seconds' $JORDAN_HOME/ledgers/pending-*
stop B $T/r 2>&1 | head -1; ls $JORDAN_HOME/ledgers; cat $T/runs
claim A $T 'cd r && jordan-ledger open --check true'   # opener's own claim, cwd outside root: no claim
```
Observed: `JORDAN done-gate: the check failed (exit 1): echo ran >> …`, `B.json`, `ran`.
The windows otherwise behave as described: an ordinary event at age about 0 s does not
claim; at 11 s it claims; at 901 s nothing claims (verified).

### R-5. Guard tokenizer is quadratic in word length (property a)

`_Word.text += c` copies the string on every character. A long quoted or unquoted argument that also matches the prefilter (`rm|push|publish|upload|release`) gets slow:

```bash
python3 -c 'import json;print(json.dumps({"cwd":"'$T/r'","tool_input":{"command":"printf %s \""+"release notes text "*31578+"\" > NOTES.md"}}))' > p.json
time python3 $H/irreversible_guard.py < p.json
```
Observed: a 100 KB quoted argument takes 0.19 s, 300 KB takes 1.46 s and 600 KB takes 4.94 s. A 1 MB unquoted
word takes 16.5 s, which is more than the 15 s hook timeout. A 22 MB command took 39.9 s. Heredoc bodies are
stripped first and stay fast (1 MB: 0.08 s).

### R-6. Protected-path tampering that the stop-time check misses (property e)

(a) Changes made by the check command itself. `_gate` compares protected paths before it runs the check,
then closes the ledger green. A check such as `jest -u`, `ruff --fix` or `sed -i … tests/x` can rewrite
existing tests unseen.
```bash
python3 $L open --check "echo '#' >> tests/test_app.py; true" >/dev/null; claim A $T/r 'jordan-ledger open'; stop A $T/r
```
Observed: `[exit 0]`, ledger closed, `tests/test_app.py` modified.

(b) Index flags hide working-tree edits from `git diff <baseline>`:
```bash
git update-index --assume-unchanged tests/test_app.py; echo pass > tests/test_app.py; stop A $T/r
```
Observed: `[exit 0]`. `--skip-worktree` behaves the same.

### R-7. Guard misses recursive deletes R6 names (R6 class 1)

| command | decision |
|---|---|
| `cat <<EOF \| sh` + body `rm -rf /` | allow (the body is stripped because the shell comes after `<<` on the line) |
| `xargs rm -rf < list` | allow (target cannot be resolved; `xargs` is not unwrapped) |
| `find / -name x -exec rm -rf {} +` | allow |

Repro: `guard $'cat <<EOF | sh\nrm -rf /\nEOF'` prints nothing (allow). Compare `bash <<EOF …`, which returns `ask`.

### R-8. Guard denies valid bash as unparsable, even in default mode (property d)

A parse failure always gives `deny`, never `ask`. The tokenizer fails on legal nested quotes inside
`$( )` and on `$'…'` quoting:
```bash
guard 'git commit -m "$(echo "don'"'"'t") release"'   # bash -n accepts it -> deny
guard $'echo $\'it\\\'s\' && git push'                   # -> deny
```

### R-9. With a dotfiles repo at `~`, the ledger lives inside the workspace (R3, property f)

With the default `JORDAN_HOME=~/.claude/jordan` and a workspace that is a git repo at `$HOME`,
`open` writes its pending file inside the workspace and does not refuse. The trace file there is
untracked and changes on every tool call, so `tree_hash` always differs and a red check re-runs
even when the agent edited nothing.
```bash
D=$(mktemp -d -p $T); export HOME=$D; unset JORDAN_HOME; mkdir $D/tests; cd $D; echo a>tests/test_a.py; git init -q; git add -A; git commit -qm b
python3 $L open --check "echo run >> $T/runs; false"; claim A $D 'jordan-ledger open'
for i in 1 2 3; do stop A $D; claim A $D ls; done; wc -l < $T/runs; git status --short
```
Observed: the pending file is at `$D/.claude/jordan/ledgers/pending-….json`, `runs=3` with no edits, and `?? .claude/`.

### R-10. `open` says another session's ledger "is replaced when its owner claims this one"; it is not (R3)

```bash
python3 $L open --check "echo A; false" >/dev/null; claim A $T/r 'jordan-ledger open'
python3 $L open --check "echo B; true"; claim B $T/r 'jordan-ledger open'; ls $JORDAN_HOME/ledgers
python3 $L mark unverified --reason mine
```
Observed: the note says it will be replaced, but both `A.json` and `B.json` are `open`. A
`mark` run by A with no hint closes B's ledger ("acting on the most recent (session B)"), and A
stays open and red. R3 lists this as a known limit; the message that it was replaced is wrong.

## NOTE (legitimate but surprising)

- N-1. A check that exits 0 but leaves a `setsid` child holding stdout (`setsid sleep 30 & echo started`) is reported as **timeout**, after timeout + 5 s, not as green. A non-setsid background child is killed with the group.
- N-2. Check output is buffered whole. 500 MB of output: 1.45 GB RSS, 2.5 s, then the correct 40-line tail.
- N-3. A protected file that was dirty at `open` and is then reverted to HEAD counts as a protected change, because it differs from the snapshot.
- N-4. A corrupt ledger, or one whose root was deleted (e.g. a removed worktree), gives "internal error, stop allowed" on every stop of that session until it is closed by hand. It is never closed automatically.
- N-5. `stop_hook_active: "true"` (a string) is not treated as true. Claude Code sends a bool.
- N-6. After `mark` or `close`, further edits are not gated. This is per spec.
- N-7. `authorise /etc/passwd` and `authorise .` are accepted and stored verbatim as globs. They have no effect, but nothing warns.
- N-8. Guard false positives: `rm -rf lnk`, where `lnk` points outside the workspace, gives `ask`, though `rm` removes only the link (verified). In a non-git project, a subdirectory cwd shrinks the workspace, so `rm -rf ../build` gives `ask`. `cd "$(mktemp -d)" && rm -rf x` gives `ask`.
- N-9. The guard allows these, which are outside R6's three classes: `git push --delete origin main`, `git push origin :main`, `git clean -fdx`, `find . -delete`, `echo "rm -rf /" | bash`, `sh x.sh`, interpreter one-liners, `docker push`. `git push origin HEAD:+main` is correctly allowed: git creates a branch literally named `+main` (verified against a bare remote).
- N-10. session_start looks only at `$cwd/CLAUDE.md`. Started in a subdirectory of a repo whose root `CLAUDE.md` has the marker, it injects the kernel a second time.
- N-11. The no-ledger trace path still creates `$JORDAN_HOME/trace/` and appends a line on every tool call (per R7).

## Probes that passed (one line each)

1. Empty, `not json`, `[]`, `null`, `42`, `\xff\xfe` and wrong-typed fields on stdin: every hook exits 0.
2. 72 MB stdin: gate, protected_paths, trace and session_start each finish in about 0.25 s with exit 0.
3. Non-existent `cwd`: every hook exits 0. The guard allows `rm -rf build` there.
4. No ledger: done_gate and protected_paths are silent, and no ledger file is created.
5. `session_id` / `agent_id` of `../../x` / `../evil`: no claim, no trace file, no path escape.
6. Four concurrent claimers, 40 rounds: one owner every time (40/40).
7. Claim windows: an ordinary event does not claim at about 0 s and does claim at 11 s; nothing claims at 901 s; a hinted ledger is not taken by another session.
8. `stop_hook_active: true` and a non-empty `background_tasks` both exit 0 without running.
9. Green check, unchanged tree: one run, ledger closed, no re-run.
10. Red check that edits the tree: two blocks, then the cap message; it does not loop.
11. Timeout with an in-group background child: returns at the timeout (2 s), allows, and says "unverified".
12. Ledger timeout clamps: 0 and -5 become 1, 9999 becomes 540. hooks.json gives the gate 600 s.
13. `open` twice in one workspace replaces the pending file and says so.
14. `open` refuses checks containing `rm -rf /tmp/x`, `git push --force-with-lease`, or an unparsable quote. It accepts `npm publish --dry-run && npm test`.
15. Workspace paths containing a space, a quote, a newline, a leading dash or `$HOME`: open, claim, gate and protection all work.
16. Protection is detected after `git mv`, delete, `chmod +x`, edit then commit, replacement by a symlink, `git rm --cached` plus exclude, an edited pre-existing untracked test, a subdirectory cwd, a git worktree (with a separate root), and a repo with no commits.
17. Edit then revert passes. Newly created tests are free.
18. protected_paths early notice: denies by absolute path, by relative path, by `../` from a subdirectory, through a symlinked dir and for `Makefile`; allows new files and non-protected files.
19. A `guard.json` or ledger planted inside the workspace (`./guard.json`, `./.claude/jordan/…`) is ignored.
20. Guard stops `rm -fr ..`, `sudo rm -rf /var/x`, `rm -rf ~`, `$HOME/x`, `"$UNSET"`, `$(pwd)/x`, a backtick, `rm -rf /`, `--recursive`, `-Rf`, `;` and `|` chains, `bash -c`, `sh -c`, `eval`, `cd /; rm -rf tmp/x`, and `cd .. && rm -rf r2`.
21. Guard stops `git push -f`, `-uf`, `--force`, `--force-with-lease`, `origin --force`, `+HEAD:main`, `git -C x push --force`, `command git push --force`, and force behind `| tail`.
22. Guard stops `npm`, `pnpm` and `yarn npm publish`, `twine upload`, `python3 -m twine upload`, `cargo publish` and `gh release create`. It allows `npm publish --dry-run`.
23. Guard allows `rm -rf ./build`, `"$PWD/dist"`, `build/*`, `*`, `node_modules`, `build dist *.egg-info`, `-- -x`, `echo "rm -rf /"`, heredoc-to-file bodies, and `git commit -m "$(cat <<'EOF' … EOF)"` and `gh pr create --body "$(cat <<'EOF' …)"` with apostrophes inside.
24. Decision mode: `bypassPermissions` gives deny; `default`, `acceptEdits` and `plan` give ask.
25. session_start: suppressed by a marker in `~/.claude`, `$cwd` or `$cwd/.claude` `CLAUDE.md`; injects otherwise.

Not run: a ledger file owned by another uid (the probes ran as root, so ownership could not be
exercised; the code does no ownership check).
