#!/usr/bin/env python3
"""Lint the JORDAN agent base (RULINGS R8).

Prints one line per problem and exits 1; prints one OK line and exits 0
otherwise. It fails on:

  - a template with no frontmatter, or missing a required field
  - `name` that is not the file name, or not kebab-case
  - a description that is empty or spans more than one line
  - no `# jordan-role: reader|builder|refuter` comment in the frontmatter
  - a reader that can Edit, Write or NotebookEdit; a refuter that can Edit or
    NotebookEdit. This reads `tools` and `disallowedTools` themselves: a tool
    is available when `tools` lists it, or when `tools` is absent (everything
    is inherited), and `disallowedTools` does not list it.
  - `omitClaudeMd` not true (the shared block is then not the only JORDAN
    text the seat sees, and the user's CLAUDE.md is paid for on every spawn)
  - a template without the insert marker
  - the shared block missing its markers or over the byte cap
  - a rendered file that is missing, stale, or left over from a deleted
    template

The role comment is a YAML comment, so Claude Code never sees it. It exists
because an agent made by new-agent.py may have any name, and the lint has to
know which rule applies to it. It records the role only; the tool check reads
the real fields.

Usage: lint-agents.py        (no arguments; lints the tree this file is in)
Stdlib only.
"""
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

REQUIRED = ("name", "description", "model", "effort", "tools",
            "omitClaudeMd", "maxTurns")
ROLES = ("reader", "builder", "refuter")
# Tools each role must not be able to use.
FORBIDDEN = {
    "reader": ("Edit", "Write", "NotebookEdit"),
    "refuter": ("Edit", "NotebookEdit"),
    "builder": (),
}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ROLE_RE = re.compile(r"^#\s*jordan-role:\s*(\S+)\s*$")
KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(.*)$")


def load_build():
    """Import build-agents.py (the hyphen rules out a plain import)."""
    spec = importlib.util.spec_from_file_location(
        "jordan_build_agents", HERE / "build-agents.py")
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True  # no tools/__pycache__ in the repo
    spec.loader.exec_module(module)
    return module


def parse_frontmatter(text: str):
    """Return (fields, role, multiline_keys), or None when there is no
    frontmatter. `fields` maps key to a string, or to a list for a YAML
    list. This is not a YAML parser: it reads the flat `key: value` shape the
    agent files use and reports anything that continues over a line."""
    lines = text.split("\n")
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        return None
    fields, role, multiline, key = {}, None, set(), None
    for line in lines[1:lines.index("---", 1)]:
        if line.lstrip().startswith("#"):
            found = ROLE_RE.match(line.strip())
            if found:
                role = found.group(1)
            continue
        if not line.strip():
            continue
        match = None if line[0] in " \t-" else KEY_RE.match(line)
        if match:
            key, value = match.group(1), match.group(2).strip()
            if value[:1] in ("|", ">"):
                multiline.add(key)
                value = ""
            elif value.startswith("[") and value.endswith("]"):
                value = [v.strip().strip("'\"")
                         for v in value[1:-1].split(",") if v.strip()]
            elif len(value) > 1 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            fields[key] = value
        elif key is not None:
            # A continuation line: a block-list item or folded text.
            item = line.strip()
            if item.startswith("- "):
                if not isinstance(fields[key], list):
                    fields[key] = [fields[key]] if fields[key] else []
                fields[key].append(item[2:].strip().strip("'\""))
            else:
                multiline.add(key)
    return fields, role, multiline


def tool_names(value) -> set:
    """Bare tool names from a `tools` or `disallowedTools` value;
    `Bash(git *)` counts as `Bash`."""
    items = value if isinstance(value, list) else str(value).split(",")
    return {i.split("(")[0].strip() for i in items if i.strip()}


def can_use(fields: dict, tool: str) -> bool:
    if tool in tool_names(fields.get("disallowedTools", "")):
        return False
    if "tools" not in fields:
        return True  # omitted: the agent inherits every tool
    return tool in tool_names(fields["tools"])


def lint_template(path: Path, insert_marker: str) -> list:
    text = path.read_text(encoding="utf-8")
    where = f"agents/templates/{path.name}"
    problems = []
    if insert_marker not in text:
        problems.append(f"{where}: missing {insert_marker}")
    parsed = parse_frontmatter(text)
    if parsed is None:
        return problems + [f"{where}: no frontmatter between --- lines"]
    fields, role, multiline = parsed
    for field in REQUIRED:
        if field not in fields:
            problems.append(f"{where}: missing required field `{field}`")
    if "name" in fields:
        if fields["name"] != path.stem:
            problems.append(
                f"{where}: name `{fields['name']}` is not the file name")
        elif not NAME_RE.match(path.stem):
            problems.append(f"{where}: name is not kebab-case")
    if "description" in multiline:
        problems.append(f"{where}: description spans more than one line")
    elif "description" in fields and not fields["description"]:
        problems.append(f"{where}: description is empty")
    if "omitClaudeMd" in fields and fields["omitClaudeMd"] != "true":
        problems.append(f"{where}: omitClaudeMd must be true")
    if role is None:
        problems.append(f"{where}: no `# jordan-role: <role>` comment")
    elif role not in ROLES:
        problems.append(f"{where}: unknown jordan-role `{role}`")
    else:
        for tool in FORBIDDEN[role]:
            if can_use(fields, tool):
                how = ("listed in tools" if "tools" in fields else
                       "tools is omitted, so every tool is inherited")
                problems.append(
                    f"{where}: {role} can use {tool} ({how}; add it to "
                    f"disallowedTools)")
    return problems


def lint() -> tuple:
    build = load_build()
    problems = []
    block = None
    try:
        block = build.shared_block(build.read(build.SHARED))
    except (build.BuildError, OSError) as exc:
        problems.append(f"agents/shared/jordan-core.md: {exc}")
    if block is not None:
        size = build.block_size(block)
        if size > build.BLOCK_CAP:
            problems.append(
                f"agents/shared/jordan-core.md: shared block is {size} "
                f"bytes, cap {build.BLOCK_CAP}")
    templates = sorted(build.TEMPLATES_DIR.glob("*.md"))
    if not templates:
        problems.append("agents/templates: no templates")
    for path in templates:
        problems.extend(lint_template(path, build.INSERT_MARKER))
    if block is not None:
        for path, reason in build.stale_files(block):
            if build.INSERT_MARKER in reason:
                continue  # already reported against the template
            problems.append(
                f"{path.relative_to(build.ROOT)}: rendered file {reason} "
                f"(run tools/build-agents.py)")
    return problems, len(templates)


def main() -> int:
    problems, count = lint()
    for line in problems:
        print(line)
    if problems:
        return 1
    print(f"OK: {count} agent templates pass lint")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
