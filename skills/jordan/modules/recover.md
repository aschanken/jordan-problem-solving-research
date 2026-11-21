# recover

Read this when a check still fails after you corrected once.

1. Did the plan foresee this? If it has a line "if <this>, then <action>", do that action. No new planning.

2. If not, make one adjustment: the first workable option, not a comparison of several. Keep what passes. Change only what broke and what depends on it.

3. Take these steps in order. Move forward one step each time the check fails again; never go back to an earlier step in the same task.
   a. Retry with a named change. Before running, write "this differs from the last attempt because ...". If you cannot finish the sentence, go to b.
   b. Diagnose again from raw output. Rerun the failing command, read the output as if for the first time, and read `diagnose.md`.
   c. Cut the failing region again. Read `split.md` and divide only the part that keeps failing.
   d. Escalate under kernel rule 7: what failed, what you changed each time, what happened.

4. Two conditions override the order.
   - Two attempts in a row each made things worse: more failing checks, or a new failure, counted in the output. Go to b, or to d if b is done.
   - The evidence shows the plan's premise is wrong: the cause, a constraint or the goal was misread. Drop the plan, state what the evidence shows, and size the task again (kernel rule 6). Work already spent on the old plan is not a reason to keep it.

5. The impossible exit. Stop and report, instead of forcing a pass, when:
   - the existing checks contradict the request;
   - the task cannot be done as written;
   - the only way to pass the check is to edit, skip or special-case it.
   Report the request line, the check line, and the output that shows the conflict. If `jordan-ledger` is installed: `jordan-ledger mark impossible --reason '<why>'`. As a subagent, end with `STATUS: BLOCKED` and a line starting `impossible:`. This is a correct result.

6. If the work is done but the check could not run: `jordan-ledger mark unverified --reason '<why>'`, and report "implemented but unverified".

7. Report every failed attempt: what failed, what you changed, what happened.
