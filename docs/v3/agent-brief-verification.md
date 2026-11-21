# Live adoption test of JORDAN-V3-AGENT.md

Date 2026-11-21. The acceptance criterion for `JORDAN-V3-AGENT.md` is that a
stock agent, given the file and nothing else, adopts the workflow by itself.
This file records the runs made to test that, the commands, what was seen, and
what the runs do not show. Every quoted line is copied from a transcript.

Scope of the evidence: one harness (`claude` 2.1.330, headless), one model
(the init event of every run reports `claude-haiku-5-5`), one small task, two
adoption runs and three task runs. No other harness (Codex CLI, Cursor, Gemini
CLI, Aider) was run. This is an observation of behaviour, not a measurement of
effect; there is no baseline arm here and the eval in `eval/` is the place for
one.

## Setup

A seed repository with one module, `textstats.py`, whose `word_count` used
`text.split(" ")`, and `tests/test_textstats.py` with five tests, one failing:

```
$ python3 -m unittest discover -s tests -t . 2>&1 | tail -6
AssertionError: 1 != 0
Ran 5 tests in 0.001s
FAILED (failures=1)
```

Each run copied the seed to a fresh directory under the session scratchpad,
ran `git init` and one commit, then copied `JORDAN-V3-AGENT.md` in untracked.

Isolation, so that no JORDAN text reached the agent from anywhere else:

```sh
env -u CLAUDE_ADDITIONAL_DIRECTORIES -u CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD \
    -u CLAUDE_MEMORY_STORES -u CLAUDE_COWORK_MEMORY_PATH_OVERRIDE \
    CLAUDE_CONFIG_DIR=<empty dir, new per repository> \
  claude -p "<prompt>" --model haiku --setting-sources project \
    --strict-mcp-config --permission-mode bypassPermissions \
    --output-format stream-json --verbose
```

A probe run with the same flags, asked to list instruction files in context,
answered "No CLAUDE.md file appears in my context." Before the memory
variables were unset it also listed a `MEMORY.md` index; they were unset for
every run below.

Prompts. Session 1: `I am handing you the file JORDAN-V3-AGENT.md in this
directory. Read it and adopt it.` Session 2, a new process in the same
directory: `word_count('') returns 1 but should return 0. Please fix it.`

## Run 1 (file at 31,494 bytes)

Session 1, adoption. Four turns. The agent read the file, then used the two
`sed` commands the file gives.

| Question | Observed |
|---|---|
| Kernel written to an instruction file between the markers | Yes. It created `CLAUDE.md`. `cmp` of that file against the kernel-plus-pointer range of the handover: identical. `tools/render-claude-md.py --check CLAUDE.md` printed `render-claude-md: CLAUDE.md is current` |
| Procedures saved | Yes. `.jordan/procedures.md`, identical by `cmp` to the procedures range (16,203 bytes) |
| Acknowledgement states what it cannot enforce | Yes: "Nothing re-runs a check before I stop, nothing protects existing tests, and nothing blocks irreversible commands. Those rest on my discipline." |
| Wrote outside the project, or installed hooks | No: "I didn't install the hooks or write any user-level or global file. Both would need your approval." |

Session 2, task. Nine turns.

| Question | Observed |
|---|---|
| Size line | No. None in the transcript |
| Check named before the first edit | Not as a line. It did run the tests before editing: "I'll run the existing tests first to get a baseline." |
| Existing test left unedited | Yes. `git status --short` showed ` M textstats.py` only, besides the untracked adoption files |
| Check output quoted | Yes, the five `... ok` lines, `Ran 5 tests in 0.000s`, `OK`, and "Before the change, `WordCount.test_empty` failed with `AssertionError: 1 != 0`." |

Two things went wrong, one in the handover and one in the test setup.

1. The handover put the visible form of rules 1 and 2 (`Size:` and `Check:`
   lines) only in its "Proving adoption" section, which is not persisted. A
   later session sees the kernel, which says to size the task and name the
   check but not that the user must be able to see it. Fixed: the pointer
   block, which is persisted next to the kernel, now carries a paragraph that
   gives both lines and the closing quote of the check output.
2. The seed repository had committed `__pycache__`, so the agent spent a turn
   on `git checkout -- __pycache__ tests/__pycache__`. That was the setup's
   fault. The seed was given a `.gitignore` for run 2.

## Run 2 (file at 31,995 bytes, pointer block revised)

Session 1, adoption. Five turns. Same result as run 1: `CLAUDE.md` and
`.jordan/procedures.md` identical by `cmp` to their ranges in the handover.
Acknowledgement: "Nothing re-runs my check before I stop, nothing protects
existing tests, and nothing blocks irreversible commands. Those rest on my own
discipline. `jordan-ledger` is not installed, so the ledger step in rule 2 is
skipped." and "I did not write a user-level file, since that would change
every project."

Session 2, task, first attempt. Five turns. No size line, no check named, no
run of the tests before the edit, and the report said "All 5 tests in
`tests/test_textstats.py` pass" without quoting output. The test file was not
edited.

That was worse than run 1, which the revision did not explain, so the cause
was looked for before changing anything else. Two candidates: the harness did
not load `CLAUDE.md`, or it loaded it and the agent ignored it. The probe that
separates them, in the same directory, no tools allowed:

```
prompt: Is a CLAUDE.md or other project instruction file present in your
        context right now? ... If no, say 'none loaded'.
answer: none loaded
```

A second probe in a directory whose `CLAUDE.md` held a passphrase answered
"Unknown" with and without `--setting-sources`, with the default config
directory, and with the file committed. `--debug-file` gave the reason:

```
[CLAUDE.md] not loading <scratchpad>/brief-live/p/CLAUDE.md: it, or what it
links to, is in a session's scratchpad, a folder laid out like one
(claude/<project>/<session id>/scratchpad), or a folder named .artifact-work.
To load it, move it out of that folder.
```

So in both runs the second session never had the kernel in context from the
harness. In run 1 the agent happened to `cat CLAUDE.md` while exploring, which
is why that run looked better. This is a property of where the test was
required to run, not of the handover, and it could not be removed without
moving the repository out of the scratchpad.

Session 2, task, rerun. The source file was restored (`git checkout --
textstats.py` in the throwaway repository) and the same prompt was run with
one more flag, which hands the agent the file it wrote in session 1 in the way
the harness would have:

```sh
--append-system-prompt "$(cat CLAUDE.md)"
```

Six turns.

| Question | Observed |
|---|---|
| Size line | Yes, first line of the reply: "Size: FAST, because this is a one-function fix that is easy to revert." |
| Check named before the first edit | Partly. "Check: find the function and its tests, then run the tests." It named an activity, not a command. It then ran `python3 -m unittest tests.test_textstats -v` before the edit and again after it |
| Existing test left unedited | Yes. It ran `git diff --name-only 895f9b7` itself and reported "The only changed tracked file is `textstats.py`." Confirmed from outside: `git diff --stat` showed `textstats.py | 2 +-` and nothing else |
| Check output quoted | Yes: "Check output after the change (`python3 -m unittest tests.test_textstats -v`): `Ran 5 tests in 0.000s` `OK`", and "Before the change, `test_empty` failed with `AssertionError: 1 != 0`." |
| Outcome stated apart from the check | Yes: "`word_count(\"\")` now returns 0." |

## Changes made to the handover because of these runs

- The pointer block gained the paragraph that makes rules 1, 2 and 8 visible
  (`VISIBLE` in `tools/build-agent-brief.py`). After it, the one task run that
  had the block in context wrote the size line; the one before it did not.
  One run each way is not enough to say the paragraph is the cause.
- "Making it stick" step 5 now says that finding the markers shows the file is
  written, not that the harness loads it, and what to do if it does not.
- The wrapper says once that following the rules silently does not count.

## Not shown, and not fixed

- Automatic loading of the written `CLAUDE.md` by the harness in a later
  session was not observed, because Claude Code does not load instruction
  files from a scratchpad path. The last task run supplied the file by flag.
  Unverified here; it is the harness's documented behaviour elsewhere.
- The `Check:` line named an activity where a command was wanted. Not fixed:
  the one rerun allowed was already spent. A candidate change is to make the
  pointer's wording `Check: <the exact command, or the observation if no
  command exists>`.
- No procedure trigger fired in any run, so reading `.jordan/procedures.md` on
  a trigger is untested. The task was FAST and passed first time.
- Rules 5 and 7 were not put under pressure: the task did not tempt the agent
  to edit the test and involved nothing irreversible.
- Nothing here shows that an agent with the handover does better than one
  without it. The first-attempt task run in run 2, with no kernel in context,
  also fixed the bug and left the test alone; it differed in what it showed
  the user, not in the patch.
- Subagent hand-off, the Claude Code install route, and every harness other
  than headless Claude Code are untested.

Transcripts (stream-json) were kept in the session scratchpad under
`brief-live/` and are not part of the repository.
