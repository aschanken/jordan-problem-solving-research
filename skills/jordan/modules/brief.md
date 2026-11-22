# brief

Read this when you hand a decision to a person or a lead: before an action that cannot be undone, at a choice the task does not settle, or when you are stuck.

1. Stop the item that needs the decision. Do not choose for the decider. Keep working on items that do not depend on it.

2. Write one line per decision, in this shape:

   `DR-<n> | <class> | <question> | options: A) … B) … (each with its consequence) | context: <file:line> | recommend: <letter + one line>`

   `<class>` is one of orchestrate's: SCOPE, MEANING, USER-VISIBLE, INTERFACE, STRUCTURAL, SYSTEMIC, CREATIVE. Without orchestrate, name the kind of decision in one word, such as IRREVERSIBLE.

3. Fill the fields so the decider needs nothing else. They may know less about the repo than you do now.
   - question: the exact action, as the command or change that would run.
   - options: each with its consequence and how to undo it, or "cannot be undone". One option is to do nothing, with what happens then.
   - context: one file:line the decider can open. Quote the evidence there or in the option text.
   - recommend: a letter and one line of reason.

4. Add one line under it: `default: <what happens if no answer comes>`. For an action that cannot be undone, the default is that it is not done.

5. Send it.
   - A person is reachable: ask, and wait for the answer.
   - You are a subagent or a run with nobody to ask: end your turn with this report and stop.

   ```
   STATUS: DONE|PARTIAL|BLOCKED|DECISION_REQUEST
   EVIDENCE: <command> → <result>
   CHANGED: <paths>
   OPEN: <issues>
   DETAIL: <path of any longer report>
   ```

   Use `STATUS: DECISION_REQUEST` and put the DR lines under `OPEN:`. Use `STATUS: BLOCKED` when you are stuck with no option to offer, and say what you tried.

6. Put every decision you can see into one request. Past three, keep the DR lines in the request and move longer context to a file the request names.

7. When the answer comes, apply it to that item and continue. Do not restart the task.
