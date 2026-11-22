#!/usr/bin/env python3
"""Build JORDAN-V3-AGENT.md, the one-file handover for a stock coding agent.

The handover embeds the kernel, the seven modules and the shared agent block.
Each of those has one source in this repository, so the handover is assembled
from them and never edited by hand; otherwise it would drift the first time a
rule is reworded.

    build-agent-brief.py [--check] [--out PATH]

The wrapper prose lives in tools/agent-brief.template.md. A line of the form
`<!-- include: NAME -->` in the template is replaced:

    kernel         skills/jordan/kernel.md, unchanged
    module <name>  skills/jordan/modules/<name>.md, unchanged except that its
                   headings are pushed down one level, so the saved procedures
                   file has one top heading
    triggers       one line per module, taken from the "Read `modules/x.md`
                   when ..." lines of skills/jordan/SKILL.md
    pointer        the short always-loaded note that names the procedures file,
                   repeats the triggers, says which lines the user must be able
                   to see, and states the no-hooks duties
    core           agents/shared/jordan-core.md between its markers, unchanged

Without --check the file is written. With --check nothing is written: exit 0
when the file on disk equals the build, 1 when it is stale or missing. Exit 2
is a usage or source error. Stdlib only.
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "tools", "agent-brief.template.md")
OUT = os.path.join(ROOT, "JORDAN-V3-AGENT.md")
SKILL_DIR = os.path.join(ROOT, "skills", "jordan")
KERNEL = os.path.join(SKILL_DIR, "kernel.md")
SKILL = os.path.join(SKILL_DIR, "SKILL.md")
MODULES_DIR = os.path.join(SKILL_DIR, "modules")
CORE = os.path.join(ROOT, "agents", "shared", "jordan-core.md")

# Order an agent meets them in: plan before the modules it refers on to.
MODULES = ("plan", "split", "diagnose", "verify", "options", "recover", "brief")
PROCEDURES_PATH = ".jordan/procedures.md"

INCLUDE = re.compile(r"^<!-- include: ([a-z]+)(?: ([a-z]+))? -->$")
TRIGGER = re.compile(r"^- Read `modules/([a-z]+)\.md` (when .+)$")
CORE_BEGIN = "<!-- jordan-core:begin -->"
CORE_END = "<!-- jordan-core:end -->"

# The always-loaded stand-in for the hooks. Kept to one paragraph because it is
# paid for on every step, like the kernel.
NO_HOOKS = (
    "No JORDAN hooks run in this harness, so nothing re-runs the check for you. "
    "Run the check as your last action before saying a task is done and quote "
    "its output. Before reporting, run `git diff --name-only <starting commit>` "
    "and name any test or CI file in it that existed before the task. Stop and "
    "ask before deleting outside the workspace, force-pushing or publishing."
)


# Rules 1, 2 and 8 can be followed silently, and then the user cannot tell an
# agent that sized the task from one that did not. In the first live run the
# agent reproduced, fixed and quoted the check but wrote no size or check line
# (docs/v3/agent-brief-verification.md), so the visible form is stated here,
# where a later session will see it.
VISIBLE = (
    "Make rules 1, 2 and 8 visible to the user on every task that changes "
    "files. Before your first edit, write two lines in your reply: "
    "`Size: FAST|STANDARD|DEEP, because <reason>` and "
    "`Check: <command or observation>`. End with the check's output, quoted "
    "from a run made after your last edit."
)


class BuildError(Exception):
    pass


def read(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError as error:
        raise BuildError("cannot read %s: %s" % (os.path.relpath(path, ROOT), error))


def kernel():
    return read(KERNEL).strip("\n")


def demote(text):
    """Push Markdown headings down one level, leaving fenced code alone."""
    out, fenced = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{1,5} ", line):
            line = "#" + line
        out.append(line)
    return "\n".join(out)


def module(name):
    if name not in MODULES:
        raise BuildError("unknown module %r" % name)
    return demote(read(os.path.join(MODULES_DIR, name + ".md")).strip("\n"))


def triggers():
    found = {}
    for line in read(SKILL).split("\n"):
        match = TRIGGER.match(line)
        if match:
            found[match.group(1)] = match.group(2)
    missing = [name for name in MODULES if name not in found]
    extra = sorted(set(found) - set(MODULES))
    if missing or extra:
        raise BuildError(
            "SKILL.md triggers do not match the module list: missing %s, extra %s"
            % (missing, extra))
    return "\n".join("- `%s`: %s" % (name, found[name]) for name in MODULES)


def pointer():
    return "\n".join([
        "JORDAN procedures are in `%s`. Do not read them in advance. Read one "
        "section only when its trigger occurs:" % PROCEDURES_PATH,
        "",
        triggers(),
        "",
        VISIBLE,
        "",
        NO_HOOKS,
    ])


def core():
    text = read(CORE)
    start, stop = text.find(CORE_BEGIN), text.find(CORE_END)
    if start == -1 or stop == -1 or stop < start:
        raise BuildError("jordan-core.md has no begin/end marker pair")
    return text[start + len(CORE_BEGIN):stop].strip("\n")


def build():
    out = []
    for number, line in enumerate(read(TEMPLATE).split("\n"), 1):
        match = INCLUDE.match(line)
        if not match:
            out.append(line)
            continue
        kind, arg = match.groups()
        if kind == "kernel" and arg is None:
            out.append(kernel())
        elif kind == "module" and arg:
            out.append(module(arg))
        elif kind == "triggers" and arg is None:
            out.append(triggers())
        elif kind == "pointer" and arg is None:
            out.append(pointer())
        elif kind == "core" and arg is None:
            out.append(core())
        else:
            raise BuildError("template line %d: unknown include %r" % (number, line))
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="write nothing; exit 1 when the built file is stale")
    parser.add_argument("--out", default=OUT, help="output path (default: repo root)")
    args = parser.parse_args(argv)
    try:
        built = build()
    except BuildError as error:
        print("build-agent-brief: %s" % error, file=sys.stderr)
        return 2
    if args.check:
        try:
            with open(args.out, encoding="utf-8") as handle:
                current = handle.read()
        except OSError:
            print("build-agent-brief: %s is missing; run tools/build-agent-brief.py"
                  % args.out, file=sys.stderr)
            return 1
        if current != built:
            print("build-agent-brief: %s is stale; run tools/build-agent-brief.py"
                  % args.out, file=sys.stderr)
            return 1
        return 0
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(built)
    print("wrote %s (%d bytes)" % (args.out, len(built.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
