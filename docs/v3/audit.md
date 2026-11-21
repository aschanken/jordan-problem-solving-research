# JORDAN v2 Audit — Input to the V3 Design

Date: 2026-11-21. Scope: this repo, `swarmfucker`, `orchestrate-skill`. Every
figure below was read from a file or produced by a command in one of those
repos; the source is named beside it. Items marked *inference* are a reading,
not a file statement.

## 1. Where v2 stands

- v2.0.0 applied the prompt-side recommendations of `fable-review.md`: tiered
  delivery (kernel / modules / reference doc), no unearned numbers, the split
  escalation bias, six execution behaviors.
- The harness-side recommendations (B1 stop-hook verification, B2 routing,
  B4 deterministic gates, B5 schemas, B6 experience store) and the eval (R6)
  were never built. Review priority order was B1 → R1 → R6 → B2; only R1 and
  the small prompt edits shipped.
- The kernel is labelled "~500 tokens"; the file is 2,787 bytes (`wc -c`).

## 2. How JORDAN reaches agents today (swarmfucker)

- `install.sh` copies `CLAUDE.md`, `universal-seed-prompt.md`,
  `JORDAN_v2_OVERVIEW.md` to `~/.claude/` and merges `prompts/` into
  `~/.claude/prompts/` (install.sh:157-172).
- Only `~/.claude/CLAUDE.md` is ever loaded: 11,366 bytes in the vendored copy.
  Nothing loads the kernel or the five modules. The tiered delivery matrix is
  documentation with no deployer.
- No agent definition contains any JORDAN text (grep of `agents/` for JORDAN,
  FRAGO, premortem, kernel, tier, seed: zero hits). Seats carry orchestrate
  doctrine instead.
- No hook enforces a JORDAN rule. The closest is `design-gate` (a pointer brief
  must carry a non-empty "Design rulings" section).
- JORDAN has not changed in swarmfucker since the initial import
  (CHANGELOG.md:101). *Inference:* orchestrate has displaced it as the working
  doctrine; `swarm_instructions.txt:16-19` tells the lead to load orchestrate
  and follow it.
- The vendored CLAUDE.md adds two sections the plain one lacks: rg over grep,
  and the `bonemot` naming protocol. V3 must not drop them from that copy.
- `prompts/README.md:3` cites `../fable-review.md`, which is not vendored.

## 3. What orchestrate-skill has measured

Source for all: `orchestrate/references/economy.md` and
`docs/measurements/` in that repo.

- The lead re-reads its whole context every turn: 26,944,743 cache tokens over
  124 messages in one team session (economy.md:14-27).
- Every spawn pays a floor before doing work: lead first request 70,654 tokens;
  subagents 28-45k; Explore 19,137 (2026-09-04-baked-in-context/assessment.md).
  The global CLAUDE.md rides into every spawn, so an 11 KB JORDAN CLAUDE.md is
  part of that floor.
- 41 of 41 subagent/workflow compactions were on Sonnet (economy.md:41-63),
  driving a lane budget of ≤110k context, ≤250 KB read, ≤60 tool calls.
- A second refuter lens cost about 3x for equal outcomes; one refuter is the
  default (CHANGELOG:12).
- Large required output schemas killed 3 of 7 recon agents (workflows.md:54-59).
- A haiku parent truncated an 816-byte inline brief 2 of 2 times; a 117-byte
  pointer arrived intact (dispatch.md:42-48).

Conventions worth copying: an always-loaded kernel with a byte cap enforced by
a test (SKILL.md cap 14,000 bytes); references that state "read when X";
one-line frontmatter descriptions; agent files rendered from templates plus one
shared block by a build script with `--check`; `omitClaudeMd`, pinned effort,
tool allowlists (verifiers get no Edit); pointer briefs; a `STATUS:` report
shape; the Decision Request line shape.

## 4. Contradictions V3 must resolve

1. Two routers. JORDAN classifies FAST/STANDARD/DEEP; orchestrate's strategy
   gate picks the execution shape. Orchestrate's strategy block already takes a
   tier, so JORDAN should supply the tier and stop there.
2. The 12-phase pipeline versus measured economy. A 4-5 persona premortem as
   separate spawns exceeds orchestrate's ≤3 premium-seat cap; multi-channel
   verification conflicts with the single-refuter default.
3. "DEEP always escalates to a human" has no counterpart in a swarm run with
   permissions skipped; the working equivalent is the Decision Request.
4. JORDAN does not say who does the work. Orchestrate forbids the lead from
   implementing.
5. Small-model seats likely receive the full 11 KB CLAUDE.md (*inference* from
   swarm_instructions.txt:78), the opposite of the deployment matrix.

## 5. Constraints for V3

- Installable as a Claude Code plugin/skill; also droppable into
  `~/.claude/skills/jordan/` by swarmfucker's installer, which replaces skill
  directories wholesale (install.sh:195-206).
- If file names change, `install.sh`, `docs/verification.md:21` and the vendored
  `framework/` must change together.
- Always-loaded text must be small and capped by a test.
- Compose with orchestrate; do not duplicate dispatch, routing or economy.
- Hooks follow the existing pattern: fail-open, exit 2 with a reason,
  dedupe-by-command registration (install.sh:476-516).
- Agent base must fit the existing frontmatter conventions (name, one-line
  description, model, tools, effort) and the template-plus-shared-block build.
