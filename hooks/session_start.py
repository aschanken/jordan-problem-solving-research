#!/usr/bin/env python3
"""session_start.py — SessionStart: put the kernel in context (RULINGS R7).

Plugin route only: a plugin cannot ship an always-on CLAUDE.md, so this hook
injects skills/jordan/kernel.md plus one line naming the modules. It stays
silent when a kernel block is already loaded through CLAUDE.md, i.e. when the
marker is found in ~/.claude/CLAUDE.md, $cwd/CLAUDE.md or
$cwd/.claude/CLAUDE.md (REDTEAM M6), or in the same two files in a directory
above cwd. It runs for every source, so the kernel
comes back after /clear and compaction.

Contract: stdin = SessionStart JSON. stdout is empty or one JSON object with
hookSpecificOutput.additionalContext. A missing kernel file or any error: exit
0 silently.
"""
import json
import os
import sys

MARKER = "<!-- jordan-kernel:begin -->"
MODULES = ["plan", "split", "diagnose", "verify", "options", "recover", "brief"]
CAP = 10000  # additionalContext limit


def _has_marker(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return MARKER in fh.read()
    except OSError:
        return False


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    here = os.path.dirname(os.path.realpath(__file__))
    skill = os.path.join(here, "..", "skills", "jordan")
    try:
        with open(os.path.join(skill, "kernel.md"), encoding="utf-8") as fh:
            kernel = fh.read().strip()
    except OSError:
        return 0
    if not kernel:
        return 0
    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else os.getcwd()
    config = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    places = [os.path.join(config, "CLAUDE.md")]
    # Claude Code also loads CLAUDE.md from the directories above cwd, so a
    # session started in a subdirectory of a repo with the kernel block has it.
    here_dir = os.path.abspath(cwd)
    for _ in range(40):
        places += [os.path.join(here_dir, "CLAUDE.md"), os.path.join(here_dir, ".claude", "CLAUDE.md")]
        parent = os.path.dirname(here_dir)
        if parent == here_dir:
            break
        here_dir = parent
    for path in places:
        if _has_marker(path):
            return 0
    # Name the modules that are actually shipped, so this line cannot drift.
    try:
        found = sorted(n[:-3] for n in os.listdir(os.path.join(skill, "modules")) if n.endswith(".md"))
    except OSError:
        found = []
    names = [m for m in MODULES if m in found] + [m for m in found if m not in MODULES] or MODULES
    pointer = ("Modules, in the jordan skill; read one only when its trigger occurs: %s. "
               "The skill's SKILL.md gives each trigger." % ", ".join(names))
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": (kernel + "\n\n" + pointer)[:CAP],
    }}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
