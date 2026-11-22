# JORDAN V3

JORDAN is a problem-solving framework for AI coding agents. Version 3 is a
small set of working habits that is always in context, a set of procedures
read only when needed, and a few checks enforced by code instead of by prompt.

Status: V3's effect is not yet measured. The eval in `eval/` exists to
measure it against a baseline with no JORDAN at all, and every component is
listed in [docs/v3/evidence.md](docs/v3/evidence.md) with the result that
would remove it.

## Layers

| Layer | Where | What it does |
|---|---|---|
| Kernel | [skills/jordan/kernel.md](skills/jordan/kernel.md) | Nine rules, always on, capped at 2,800 bytes by a test |
| Modules | [skills/jordan/modules/](skills/jordan/modules/) | Seven procedures (plan, split, diagnose, verify, options, recover, brief), each read on its trigger; index in [SKILL.md](skills/jordan/SKILL.md) |
| Hooks | `hooks/`, `bin/jordan-ledger` | Done-gate (the named check must run green before a stop counts as done), protected paths (existing tests and check-defining files), irreversible-action guard, trace |
| Agent base | `agents/`, `tools/` | Templates and a shared block for building agents that carry the same habits |
| Eval | `eval/` | Tasks and arms that compare JORDAN against no JORDAN |

The hooks catch accidents and make tampering visible. They are not a sandbox.

## Install

Use one route per machine. Detail, uninstall and limits: [docs/v3/install.md](docs/v3/install.md).

Plugin:

```sh
claude plugin marketplace add aschanken/jordan-problem-solving-research
claude plugin install jordan@jordan
```

Plain copy into `~/.claude`:

```sh
./install.sh
```

To put only the kernel into a project's `CLAUDE.md`:
`python3 tools/render-claude-md.py path/to/project`.

## Build a new agent

Start from one of the three roles (reader, builder, refuter) with
`tools/new-agent.py <name> --role <role>`. Steps and conventions:
[docs/v3/building-agents.md](docs/v3/building-agents.md).

## Eval

[eval/README.md](eval/README.md) describes the arms, the two pilot tasks, the
measures, and how to add tasks from your own failures.

## Design record

- [docs/v3/RULINGS.md](docs/v3/RULINGS.md): the binding decisions for 3.0.
- [docs/v3/DESIGN.md](docs/v3/DESIGN.md) and [docs/v3/REDTEAM.md](docs/v3/REDTEAM.md): the design and the attack on it.
- [docs/v3/audit.md](docs/v3/audit.md): what v2 was and how it reached agents.

## Where v2 went

JORDAN v2, the 12-phase pipeline, is archived and frozen in
[docs/v2/](docs/v2/README.md), with [errata](docs/v2/ERRATA.md) for two
factual errors. The research corpus behind v2 (`report.md`, `results/`,
`synthesis.md`) and the review files remain in the repository root.

## Tests

```sh
python3 -m pytest tests
```
