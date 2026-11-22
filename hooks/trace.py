#!/usr/bin/env python3
"""trace.py — PostToolUse / PostToolUseFailure: one line per tool call (RULINGS R7).

Appends {ts, session_id, agent_id, tool, ok, bytes, input} to
$JORDAN_HOME/trace/<session_id>.jsonl (owner-only). `input` is the first 200
characters of a Bash command, without heredoc bodies, or the path a file tool
was given. File contents and other tool arguments are never recorded
(RULINGS R14): a trace is read by people other than the one who typed. It also
claims a pending ledger for the owner (R3): this event carries the session and
agent ids that `jordan-ledger open` could not see, and fires on the very tool
call that ran it.

Never blocks, never prints. Any error exits 0.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

INPUT_CHARS = 200
PATH_KEYS = ("file_path", "path", "notebook_path")
# Credentials typed on a command line. Best effort: it catches the common
# shapes, not every secret.
SECRET = re.compile(
    r"(?i)((?:bearer|basic)\s+|(?:token|secret|password|passwd|api[_-]?key|access[_-]?key)[\w-]*\s*[=:]\s*"
    r"|--(?:password|token)\s+|\b(?:gh[pousr]_|sk-|xox[bpas]-|AKIA))[^\s'\"]+")


def shown_input(tool_input):
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    if isinstance(command, str):
        first = command.find("<<")
        if first >= 0:  # a heredoc body is the command's stdin, often a whole file
            end = command.find("\n", first)
            command = command if end < 0 else command[:end] + " [heredoc body omitted]"
        return SECRET.sub(lambda m: m.group(1) + "[redacted]", command[:4000])[:INPUT_CHARS]
    for key in PATH_KEYS:
        if isinstance(tool_input.get(key), str):
            return tool_input[key][:INPUT_CHARS]
    return ""
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
        opener = isinstance(command, str) and "jordan-ledger" in command
        lib.claim_pending(payload, "opener" if opener else "tool")
    except Exception:
        pass  # the trace line is still worth writing

    response = payload.get("tool_response", payload.get("error"))
    size = len(response) if isinstance(response, str) else len(json.dumps(response, default=str)) if response is not None else 0
    line = json.dumps({
        "ts": lib.now(), "session_id": sid, "agent_id": lib.safe_id(payload.get("agent_id")),
        "tool": str(tool)[:80] if tool else None,
        "ok": payload.get("hook_event_name") != "PostToolUseFailure",
        "bytes": size, "input": shown_input(tool_input),
    })
    path = os.path.join(lib.trace_dir(), sid + ".jsonl")
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    try:
        if os.stat(path).st_size > MAX_TRACE_BYTES:
            return 0
    except OSError:
        pass
    # One write() of a short line in append mode: concurrent hooks do not interleave.
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, (line + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
