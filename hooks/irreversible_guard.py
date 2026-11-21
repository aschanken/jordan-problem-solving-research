#!/usr/bin/env python3
"""irreversible_guard.py — PreToolUse on Bash (RULINGS R6).

Stops three classes before they run: a recursive delete whose target is
outside the workspace or cannot be resolved, a force-push, and a publish.
Default-branch push and credential reads are opt-in via $JORDAN_HOME/guard.json
({"default_branch_push": true, "credential_reads": true}).

Decision is "ask" when someone can answer, "deny" in a bypass permission mode.
It catches accidents, not intent, and is not a sandbox: a script file or an
interpreter one-liner goes straight past it.

Fails open, with one exception: once the cheap prefilter has matched, a
command that cannot be parsed is denied.

Contract: stdin = PreToolUse JSON. Exit 0 silently to allow; otherwise print
one PreToolUse decision object and exit 0.
"""
import json
import os
import re
import sys

# Kept here as well as in jordan_lib so the common case (an unrelated command)
# returns before the library is even imported. test_hooks checks they agree.
PREFILTER = re.compile(r"\b(?:rm|push|publish|upload|release)\b")


def _decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}))
    return 0


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    if not isinstance(payload, dict):
        return 0
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or not command:
        return 0
    matched = bool(PREFILTER.search(command))
    home = os.path.expanduser(os.environ.get("JORDAN_HOME") or "~/.claude/jordan")
    if not matched and not os.path.exists(os.path.join(home, "guard.json")):
        return 0

    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    import jordan_lib as lib
    config = lib.load_guard_config()
    if not matched and not config.get("credential_reads"):
        return 0
    try:
        findings = lib.guard_findings(
            command, payload.get("cwd") or os.getcwd(), config, payload.get("scratchpad_dir"))
    except lib.GuardParseError as exc:
        if not matched:
            return 0
        return _decide("deny", "JORDAN irreversible-guard: this command mentions a delete, push or "
                       "publish and could not be parsed (%s), so it was not run. Rewrite it more "
                       "simply, or put the risky step in its own command." % exc)
    except Exception:
        if matched and os.environ.get("JORDAN_DEBUG"):
            raise
        return 0
    if not findings:
        return 0
    bypass = payload.get("permission_mode") in lib.BYPASS_MODES
    reason = "JORDAN irreversible-guard: " + "; ".join(d for _, d in findings) + "." + lib.GUARD_ADVICE
    return _decide("deny" if bypass else "ask", reason)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
