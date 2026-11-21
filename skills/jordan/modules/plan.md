# plan

Read this when a direct attempt failed its check, or when the next step is hard to undo. Otherwise skip it and follow kernel rule 3.

Write the plan as a short note: in your reply, or in the brief if you are handing the work on. Detail the next step only; later steps get one line each.

1. Purpose and end state. Two lines: why the work is wanted, and what is true when it is done. Add a third: what must still hold if the plan fails (for example "main still builds", "no data is lost").

2. Acceptance.
   - The check command, exactly as it will be run. If `jordan-ledger` is installed and no ledger is open: `jordan-ledger open --check '<command>'`.
   - One structural requirement the tests cannot see, checkable by a command or by reading. Example: "the application imports the new module instead of copying its logic".

3. Assumptions. List what you are treating as true but have not checked. Beside each write one of:
   - a command that would confirm it. Run the cheap ones now and keep the output;
   - `risk:` what goes wrong if it is false, and what you would see first.
   An item with neither may not stay on the list.

4. Decision triggers. At most five lines of the form "if <observation>, then <action>". Write a trigger only when its action differs from carrying on. One of them names the observation that would mean the plan's premise is wrong; its action is "drop the plan and size the task again".

5. Failure pass. Do this only when the step cannot be undone or no fast check exists. Give a fresh context (a subagent if you have one) the plan and this prompt: "This plan was carried out and it failed. Write the most likely causes." With no fresh context, write the causes yourself and label the pass "same context". Turn each cause into a check under step 2 or an assumption under step 3. Drop a cause that becomes neither.

6. Before a step that cannot be undone, read `options.md` and get the decision kernel rule 7 requires.

Then act. When a trigger's observation appears, do its action without planning again. When something appears that no trigger covers, read `recover.md`.
