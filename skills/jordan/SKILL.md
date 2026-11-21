---
name: jordan
description: Problem-solving procedures for coding work. Use when a check fails, a failure's cause is unclear, a step is hard to undo, no test covers the change, work must be split, or a decision must go to a person or lead.
---

# JORDAN

JORDAN is a small set of working habits for coding agents: name the check first, act and read the real output, leave existing checks alone, report with evidence. Nine always-on rules form the kernel; the modules below are procedures to read only when their trigger occurs.

## Kernel

`kernel.md` holds the nine rules. It is normally in context already, through CLAUDE.md or the session-start hook. If you cannot see the heading "JORDAN kernel v3" in your context, read `kernel.md` now.

## Modules

When a trigger occurs, read that one file, follow its steps, and return to the kernel loop. Do not read modules in advance.

- Read `modules/plan.md` when a direct attempt failed its check, or the next step is hard to undo.
- Read `modules/split.md` when a failed attempt needs dividing into pieces, or you are considering parallel work.
- Read `modules/diagnose.md` when you reproduced a failure and its cause is not visible, or a fix did not work.
- Read `modules/verify.md` when no existing test covers the change, or you brief or act as a refuter.
- Read `modules/options.md` when the step is hard to undo, no fast check exists, or the first approach failed its check.
- Read `modules/recover.md` when a check still fails after one correction, or the task looks impossible as written.
- Read `modules/brief.md` when you hand a decision to a person or a lead.

## With the hooks installed

- `jordan-ledger open --check '<command>'` records the check. When you stop, the done-gate runs it.
- If the check cannot go green: `jordan-ledger mark unverified --reason '<why>'` or `jordan-ledger mark impossible --reason '<why>'`.
- Tests, CI files and files that define the check are protected if they existed at the start. For a legitimate edit: `jordan-ledger authorise <path> --reason '<why>'`. The reason is shown to the reader.

## With orchestrate

Orchestrate decides who works, on which model, and in what shape. JORDAN supplies the task size and the habits of the seat doing the work. A lead that does not implement skips kernel rules 3 to 5. Reports and decision requests use orchestrate's shapes, given in `modules/brief.md`.
