# Module: Pre-Mortem — Assume Failure, Explain Why

<!-- Load when: task is DEEP, or STANDARD with HIGH aggregate risk. Run after planning, before execution. -->

**The plan has already failed. It is six weeks later and the wreckage is in front of you. Write the incident report.** This framing counteracts the planning fallacy, optimism bias, and confirmation bias — flaws are cheapest to find before you have paid for them.

## Method

Examine the plan through each lens below. For each, produce the failure scenarios that lens sees — concrete, tied to specific subtasks, not generic worries.

| Lens | Key question |
|---|---|
| **Pessimist** | Which subtask produces wrong output, and why? |
| **Safety Officer** | Where does this touch credentials, destructive operations, or untrusted input — and how does that go wrong? |
| **Resource Monitor** | What exhausts first: time, tokens, quota, patience? |
| **Quality Auditor** | Which acceptance criterion will the output fail, and how would we not notice? |
| **Domain Expert** (DEEP only) | What core pattern of this domain does the approach misapply? |

Each scenario records:
- **What failed** and **which subtasks** it takes down
- **Severity:** LOW / MEDIUM / HIGH / CRITICAL
- **Likelihood:** *likely / possible / unlikely* — with one sentence of named evidence. Never a probability float you did not derive from data.

## Then act on it

1. **Mitigate:** every HIGH/CRITICAL scenario gets a mitigation folded into the plan (a changed subtask, an added check, a reordering). Maximum 2 mitigation cycles; if scenarios remain unmitigated after that, proceed with an explicit advisory flag — never silently.
2. **Compile watchdogs:** every HIGH/CRITICAL scenario is a *predicted observable*. Turn it into a concrete check that execution will actually run ("predicted PRNG misuse → grep the auth path for `Math.random` before that subtask completes"). A prediction without a tripwire expires unread.

## Independence note

If you can run the lenses as separate fresh-context calls (subagents), do — five labeled paragraphs from one context share that context's every bias. If you cannot, take a deliberate pause between lenses and forbid any lens from referencing another's findings.
