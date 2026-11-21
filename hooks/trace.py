#!/usr/bin/env python3
"""trace.py — PostToolUse / PostToolUseFailure: one line per tool call (RULINGS R7).

Appends {ts, session_id, agent_id, tool, ok, bytes, input} to
$JORDAN_HOME/trace/<session_id>.jsonl, input cut to 200 characters. It also
claims a pending ledger for the owner (R3): this event carries the session and
agent ids that `jordan-ledger open` could not see, and fires on the very tool
call that ran it.

Never blocks, never prints. Any error exits 0.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

INPUT_CHARS = 200
MAX_TRACE_BYTES = 20 * 1024 * 1024  # stop appending; a trace is not a log archive


def main():
    import jordan_lib as lib
    payload = lib.read_payload()
    sid = lib.safe_id(payload.get("session_id"))
    if not sid:
        return 0
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None

    try:
        lib.claim_pending(payload, immediate=isinstance(command, str) and "jordan-ledger" in command)
    except Exception:
        pass  # the trace line is still worth writing

    if isinstance(command, str):
        shown = command
    else:
        shown = json.dumps(tool_input, sort_keys=True, default=str) if tool_input is not None else ""
    response = payload.get("tool_response", payload.get("error"))
    size = len(response) if isinstance(response, str) else len(json.dumps(response, default=str)) if response is not None else 0
    line = json.dumps({
        "ts": lib.now(), "session_id": sid, "agent_id": lib.safe_id(payload.get("agent_id")),
        "tool": str(tool)[:80] if tool else None,
        "ok": payload.get("hook_event_name") != "PostToolUseFailure",
        "bytes": size, "input": shown[:INPUT_CHARS],
    })
    path = os.path.join(lib.trace_dir(), sid + ".jsonl")
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    try:
        if os.stat(path).st_size > MAX_TRACE_BYTES:
            return 0
    except OSError:
        pass
    # One write() of a short line in append mode: concurrent hooks do not interleave.
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
