#!/usr/bin/env python3
"""Start a new agent from a JORDAN role template (RULINGS R8).

    new-agent.py <name> --role reader|builder|refuter [--description "..."]

Copies agents/templates/jordan-<role>.md to agents/templates/<name>.md with
`name:` set (and `description:` when given), renders agents/<name>.md, and
prints what to do next. The name is free: it does not have to start with
`jordan-`. It refuses a name that is not kebab-case (a colon would collide
with the `plugin:agent` form) and refuses to overwrite an existing template
or rendered file.

Exit codes: 0 created, 1 refused, 2 bad usage. Stdlib only.
"""
import argparse
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ROLES = ("reader", "builder", "refuter")


def load_build():
    spec = importlib.util.spec_from_file_location(
        "jordan_build_agents", HERE / "build-agents.py")
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True  # no tools/__pycache__ in the repo
    spec.loader.exec_module(module)
    return module


def set_field(text: str, key: str, value: str) -> str:
    """Replace one `key: value` line inside the frontmatter."""
    lines = text.split("\n")
    close = lines.index("---", 1)
    for i in range(1, close):
        if lines[i].startswith(f"{key}:"):
            lines[i] = f"{key}: {value}"
            return "\n".join(lines)
    raise SystemExit(f"new-agent.py: role template has no `{key}:` line")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="new-agent.py",
        description="Start a new agent from a JORDAN role template.")
    parser.add_argument("name", help="kebab-case agent name, e.g. api-reader")
    parser.add_argument("--role", required=True, choices=ROLES)
    parser.add_argument("--description",
                        help="one line; when the lead should pick this agent")
    args = parser.parse_args(argv)

    def refuse(message: str) -> int:
        print(f"new-agent.py: {message}", file=sys.stderr)
        return 1

    if not NAME_RE.match(args.name):
        return refuse(
            f"name `{args.name}` must be kebab-case: lower-case letters, "
            f"digits and single hyphens, no colon")
    if args.description is not None and (
            "\n" in args.description or not args.description.strip()):
        return refuse("description must be one non-empty line")

    build = load_build()
    source = build.TEMPLATES_DIR / f"jordan-{args.role}.md"
    template = build.TEMPLATES_DIR / f"{args.name}.md"
    rendered = build.OUT_DIR / f"{args.name}.md"
    if not source.exists():
        return refuse(f"role template {source} is missing")
    for path in (template, rendered):
        if path.exists():
            return refuse(
                f"{path.relative_to(build.ROOT)} exists; not overwriting")

    text = set_field(build.read(source), "name", args.name)
    if args.description is not None:
        text = set_field(text, "description", args.description.strip())
    template.write_text(text, encoding="utf-8")
    try:
        block = build.shared_block(build.read(build.SHARED))
        rendered.write_text(build.render(args.name, block), encoding="utf-8")
    except (build.BuildError, OSError) as exc:
        return refuse(f"template written, but the build failed: {exc}")

    t = template.relative_to(build.ROOT)
    r = rendered.relative_to(build.ROOT)
    print(f"created {t} (from jordan-{args.role})")
    print(f"created {r}")
    print("next:")
    print(f"  1. edit {t}: the description line and the `## Role` section."
          f" Leave the jordan-core marker and the jordan-role comment.")
    print("  2. python3 tools/build-agents.py && python3 tools/lint-agents.py")
    print(f"  3. install: ./install.sh copies {r} to ~/.claude/agents/"
          f"{args.name}.md (dispatch as `{args.name}`); the plugin serves it"
          f" as `jordan:{args.name}`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
