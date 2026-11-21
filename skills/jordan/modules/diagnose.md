# diagnose

Read this when you have reproduced a failure and the output does not show its cause, or when a fix did not work.

1. Reproduce. Run the failing command and paste its output unchanged. If it will not reproduce, that is the first problem to solve. Do not edit code yet.

2. Find a passing neighbour: the closest case that passes (another input, an earlier commit, the same test run alone). Write what differs between the two. The cause is in the difference.

3. If a good revision exists, bisect: `git bisect start <bad> <good>`, then `git bisect run <check>`. Prefer this to reasoning; it is mechanical.

4. Otherwise keep a hypothesis log, one row per candidate cause, at least two rows:

   cause | predicts | command | output | verdict

   "predicts" is what you would see if this is the cause and would not see otherwise. Fill it in before running anything. A fix named in the task text or in the error message goes in as one row, not as the answer. If two causes predict the same result for every command listed, find a command where they differ.

5. Run the command where the predictions differ. Paste the output; do not summarise it. Read it for what it says, not for whether it matches what you expected. Mark each row "ruled out", "consistent" or "untested".

6. Confirm in both directions before fixing. Remove the suspected cause and see the failure stop; put it back, or force it, and see the failure return. One direction alone is weak evidence.

7. Fix the cause with the smallest change. Rerun the original failing command, then the task's check.

8. If the fix did not work, revert it. Rerun the failing command and write the symptom again from the new raw output before rereading your log. Mark the failed hypothesis "ruled out" unless the new output says otherwise, then add or revise rows.

9. Report the cause, the output that confirmed it in each direction, and which check should have caught the fault. Add that check as a test if the task allows.

Notes.
- A debugger is optional. Any command whose output separates the candidates will do.
- More exploring is not progress. If the log grows and no row is confirmed, return to step 2 or escalate under kernel rule 7.
- If the diagnosis is costly and still ambiguous, get diagnoses from separate fresh contexts and compare them.
