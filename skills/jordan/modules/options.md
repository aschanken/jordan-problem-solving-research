# options

Read this when the step is hard to undo, when no fast check exists, or when the first approach failed its check. In every other case use one approach and its check.

1. Write the criteria before any candidate exists: what the result must do, what it must not do, and the check command if there is one. Do not change the criteria after reading a candidate.

2. Get two or three candidates, each written in a separate fresh context that has not seen the others. Give each the same task and criteria and a different starting direction (for example "smallest change to the existing code", "replace the component", "solve it outside this code path"). Candidates written one after another in one context are not independent; if that is all you can do, say so in the report. With orchestrate loaded, use its `panel` workflow for this step.

3. Drop any candidate that fails a criterion outright.

4. Choose.
   - A check command exists: build each remaining candidate as a small working spike and run the check on each. The check picks. Do not pick by reading when you can pick by running.
   - No check can exist: compare the candidates one criterion at a time against the written criteria, and report the choice as unverified.
   Do not have the candidates argue with each other; choose by the check or the criteria.

5. Record the choice, the criterion that decided it, and the best loser as a branch: "if <what would show the choice was wrong>, switch to <loser>". Put that line with the plan's decision triggers.

6. If the step cannot be undone, the choice belongs to a person or the lead (kernel rule 7). Read `brief.md` and send the candidates as its options.
