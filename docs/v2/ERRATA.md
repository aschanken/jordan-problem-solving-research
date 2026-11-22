# Errata for the archived v2 documents

The archived files are left as written. This page records two statements in
them that misdescribe their sources. Both corrections come from the V3
research report (`JORDAN-V3-research-report.md`, November 2026) and its lane
files; the report tags both sources as verified, meaning the lane read them in
that session. Line numbers are those of the files in this directory.

## 1. The "45% rule" (seed section 8.6)

`universal-seed-prompt.md` line 581, under "8.6 The 45% Rule — As a Warning,
Not a Gate", says:

> Research on agentic compute criticality identifies a stability threshold: when more than ~45% of a model's capacity is consumed by orchestration (planning, verification, replanning) rather than execution, task success rates decline.

This misreads the study. The research report, section 3.5:

> The "45%" in that study is a saturation threshold. Once a single agent already scores above about 45%, adding agents gives diminishing or negative returns. v2's seed document, section 8.6, cites it as the share of capacity spent on orchestration. That reading is wrong.

Lane E, finding E1 ("Towards a Science of Scaling Agent Systems", Kim, Gu,
Park et al., December 2025), quotes the paper: coordination yields
diminishing or negative returns "once single-agent baselines exceed an
empirical threshold of ∼45%". The same finding records that the study
evaluated no software-engineering benchmark, and that the paper's visible text
gives no orchestration-overhead percentage.

Correction: 45% is a single-agent success rate, not a share of tokens or
capacity. The usage paragraph that follows in section 8.6 (track the ratio of
orchestration to execution tokens against a threshold) has no support in that
study. Files under `spec/` also cite the 45% figure (`grep -rn '45%' spec`); those
mentions were not checked one by one. V3 has no such rule; its nearest counterpart is step 7 of
`skills/jordan/modules/split.md`.

## 2. "MAKER decomposition"

`universal-seed-prompt.md` line 283 says:

> **MAKER decomposition (DEEP only):** Correctness-critical, verifiable subtasks are further decomposed into 4 atomic steps: **Design → Implement → Test → Verify**. Each step's output is verified before the next begins.

Line 501 repeats it, as does `JORDAN_v2_OVERVIEW.md` (lines 24 and 277).
Files under `spec/` use the name too (`grep -rln MAKER spec`); those were not
checked one by one.

The MAKER paper does not describe this. The research report, section 3.4:

> v2 misdescribes MAKER. The paper uses single-step subtasks, voting until one answer leads by k, and discarding over-long or malformed outputs. Its step definition is supplied by hand and its main experiment is Towers of Hanoi. It does not prescribe Design → Implement → Test → Verify.

Lane C ("MAKER (extreme decomposition with voting): the deeper reading",
source arXiv 2511.09030) adds that the method does not transfer to coding,
where outputs are diffs and not exact-match answers that can be voted on, and
that v2 "is borrowing the name" (lane C, Contradictions, item 3). Report
section 5, item 26, lists rewriting these passages as a factual correction.

Correction: Design → Implement → Test → Verify is a v2 invention with a
borrowed name, and carries no evidence from that paper. The one part lane C
judges transferable is the red flag: treat an unusually long or malformed
worker output as a failed attempt. V3 keeps that as step 8 of
`skills/jordan/modules/split.md` and drops the name.
