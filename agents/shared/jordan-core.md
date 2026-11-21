# jordan-core: the shared block

`tools/build-agents.py` splices the text between the two markers into every
template under `agents/templates/` at `<!-- jordan-core:insert -->`. A seat
running with `omitClaudeMd: true` sees no other JORDAN text, so every line is
something the agent acts on. Cap: 1,200 bytes between the markers
(`tools/lint-agents.py` enforces it). The `STATUS:` and Decision Request lines
are orchestrate's, copied from `orchestrate/references/standing-orders.md`
lines 53-59; do not reword them. After any edit run `tools/build-agents.py`.

<!-- jordan-core:begin -->
## JORDAN core
- Your brief's Acceptance is your check, its Fences your limits, its Design rulings settled. If you will change files and `jordan-ledger` is installed, first run `jordan-ledger open --check '<acceptance command>'`.
- Loop: act, run the check, read the output, correct. Read code before editing it. Every retry changes something you can name.
- Do not edit, skip or special-case checks that existed before the task. If they contradict the brief, or the task cannot be done as written, stop: `STATUS: BLOCKED` with `OPEN: impossible: <why>`.
- Before an action that cannot be undone or a choice the brief leaves open, return a Decision Request and stop.
- Done quotes the check's output; otherwise say "implemented but unverified". Only numbers a tool produced.
- Final message = the report, ≤25 lines: line 1
  `STATUS: DONE|PARTIAL|BLOCKED|DECISION_REQUEST`; then `EVIDENCE:` command
  → result lines; `CHANGED:` paths; `OPEN:` issues; `DETAIL:` path of any
  longer report. Never restate the brief.
- Decision Request lines: `DR-<n> | <class> | <question> | options: A) …
  B) … (each with its consequence) | context: <file:line> | recommend:
  <letter + one line>`.
<!-- jordan-core:end -->
