#!/usr/bin/env python3
"""protected_paths.py — PreToolUse on Edit|Write: early notice (RULINGS R5).

Enforcement is the done-gate's diff at stop, which sees every tool. This hook
only tells the agent sooner, with the same reason, when Edit or Write targets
a protected file that existed when the ledger opened.

With no ledger it carries the ledger prompt's first half (RULINGS R13): on an
owner's first Edit or Write it adds one line of context saying no check is
recorded, once, and records that the owner edited files so the stop hook can
ask once more. It never denies an edit for that.

Contract: stdin = PreToolUse JSON. Exit 0 silently to allow; to refuse, print
one PreToolUse deny object and exit 0; the nudge is one PreToolUse object with
additionalContext and no decision. Any error: allow.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))


def _nudge(lib, payload):
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict) or not isinstance(tool_input.get("file_path"), str):
        return 0
    state_path = lib.session_state_path(payload)
    # The state file doubles as "already nudged": after the first edit this
    # path costs two failed or successful stats and nothing else.
    if not state_path or os.path.exists(state_path) or lib.has_ledger(payload):
        return 0
    if lib.ledger_required() == "off":
        return 0
    lib.write_json(state_path, {"edited": True, "nudged": True, "ts": lib.now()})
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": lib.LEDGER_NUDGE,
    }}))
    return 0


def main():
    import jordan_lib as lib
    payload = lib.read_payload()
    owned = lib.load_owned(payload)  # one failed open() when there is no ledger
    if not owned:
        return _nudge(lib, payload)
    _, led = owned
    if not led.get("git"):
        return 0  # no baseline, no protection claimed
    tool_input = payload.get("tool_input")
    target = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not isinstance(target, str) or not target:
        return 0
    if not os.path.isabs(target):
        target = os.path.join(payload.get("cwd") or os.getcwd(), target)
    target = os.path.realpath(target)
    root = led["root"]
    if not lib.is_inside(target, root, strict=True):
        return 0
    rel = os.path.relpath(target, root)
    glob = lib.match_glob(rel, led.get("protect"))
    if not glob or lib.is_authorised(led, rel) or not lib.existed_at_baseline(led, rel):
        return 0
    reason = (
        "JORDAN protected-paths: %s existed before this task and is protected (matches %s). "
        "Leave existing checks alone. If the task requires changing this file, authorise it first: "
        "jordan-ledger authorise %s --reason '<why>' (recorded, and shown when the task ends). "
        "If the checks contradict the request, stop and report that: "
        "jordan-ledger mark impossible --reason '<why>'. "
        "The done-gate checks the same thing at stop, whichever tool made the change."
        % (rel, glob, rel))
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # an early notice that breaks must not block an edit
