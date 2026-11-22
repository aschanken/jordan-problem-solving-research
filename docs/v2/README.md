# JORDAN v2 archive

This directory holds JORDAN v2.0.0 as it stood when V3 replaced it. It is
frozen: nothing here is loaded by V3, and nothing here is edited except to
record an error in `ERRATA.md`.

| Path | What it is |
|---|---|
| `universal-seed-prompt.md` | The v2 source document: the 12-phase pipeline in full |
| `JORDAN_v2_OVERVIEW.md`, `jordan_v2_flow.png` | Overview and flow diagram |
| `prompts/` | The v2 kernel and its five on-demand modules |
| `spec/` | The implementation spec for a pipeline-as-code build that was not built, and the drafting session behind it |
| `ERRATA.md` | Two factual errors in the documents above, with corrections |

The files were moved with `git mv`, so `git log --follow` shows their history.
The only edit made in the move is one path in `prompts/README.md`, which
pointed at `fable-review.md` in the repository root.

Why v2 was retired: `../v3/audit.md` (what was installed and what loaded it)
and `../v3/DESIGN.md` section 2 (each v2 concept and what happened to it). The
v2 research corpus (`report.md`, `results/`, `synthesis.md`) and the review
files stay in the repository root.

The current kernel is `../../skills/jordan/kernel.md`.
