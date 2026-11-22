#!/usr/bin/env python3
"""done_gate.py — Stop / SubagentStop hook: re-run the task's check (RULINGS R4).

Runs only when all of these hold, else exits 0 with no output:
  1. an open ledger is owned by this session_id and agent_id;
  2. no background tasks are running;
  3. this is not a stop the gate already blocked (stop_hook_active);
  4. the ledger has been blocked fewer than two times. At the cap the ledger
     is closed and gating ends for it.
Then it runs the check in the workspace root, unless the tree is unchanged
since a green run it recorded, and compares protected paths afterwards.

With no ledger (RULINGS R13): in `block` mode the main session is blocked
once, at its first stop after editing files, and told to record a check or to
record that none can exist.

  green, nothing protected changed without authorisation -> close, allow
  red, or an unauthorised protected change               -> exit 2, reason on stderr
  timeout                                                -> allow, say "unverified"
  internal error                                         -> allow, advisory

Contract: stdin = hook JSON. stdout is empty or one JSON object.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))


def _say(event, message, context=None):
    out = {"systemMessage": message}
    if context:
        out["hookSpecificOutput"] = {"hookEventName": event, "additionalContext": context}
    print(json.dumps(out))


def _run_check(command, root, timeout_s):
    """(verdict, exit_code, output tail). The check gets its own process group
    so a timeout kills what it started, not only the shell.

    Output goes to a file, not a pipe: the verdict then depends on the shell
    exiting, not on every child closing stdout, and a check that prints
    hundreds of megabytes is not held in memory.
    """
    import signal
    import subprocess
    import tempfile
    with tempfile.TemporaryFile() as sink:
        proc = subprocess.Popen(
            command, shell=True, cwd=root, stdin=subprocess.DEVNULL,
            stdout=sink, stderr=subprocess.STDOUT, start_new_session=True,
            env=dict(os.environ, JORDAN_GATE="1"))
        try:
            proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except OSError:
                proc.kill()
            try:
                proc.wait(timeout=5)
            except Exception:
                pass
            return "timeout", None, ""
        size = sink.seek(0, os.SEEK_END)
        sink.seek(max(0, size - 65536))
        text = sink.read().decode("utf-8", "replace")
    return ("green" if proc.returncode == 0 else "red"), proc.returncode, text


def _ledger_prompt(lib, payload, event):
    """R13 block: once per main session that edited files and recorded nothing."""
    if event != "Stop" or payload.get("agent_id"):
        return 0  # never a subagent
    if payload.get("stop_hook_active") in (True, "true") or payload.get("background_tasks"):
        return 0
    state_path = lib.session_state_path(payload)
    state = lib.read_json(state_path) if state_path else None
    # The state file is written by the PreToolUse hook on the first Edit or
    # Write; a session that only read files has none and costs one failed open.
    if not state or not state.get("edited") or state.get("stop_blocked"):
        return 0
    if lib.has_ledger(payload) or lib.ledger_required() != "block":
        return 0
    state["stop_blocked"] = True
    lib.write_json(state_path, state)
    sys.stderr.write(
        "JORDAN: this session edited files and no check was recorded, so nothing has verified "
        "the work. Before stopping, do one of these:\n"
        "  1. jordan-ledger open --check '<command>'   records the check; it runs when you stop.\n"
        "  2. jordan-ledger open --none --reason '<why>'   if no check can exist; then report "
        "the result as unverified.\n"
        "This is asked once per session.\n")
    return 2


def _tail(text, lines=40, width=400, total=8000):
    rows = [r[:width] for r in text.rstrip().splitlines()[-lines:]]
    return "\n".join(rows)[-total:]


def main():
    import jordan_lib as lib
    payload = lib.read_payload()
    if not payload.get("session_id"):
        return 0
    event = payload.get("hook_event_name") or "Stop"
    owned = None
    if os.path.isdir(lib.ledgers_dir()):
        # Fallback claim, for when the opening tool call's own event was missed.
        lib.claim_pending(payload, "stop")
        owned = lib.load_owned(payload)
    if not owned:
        return _ledger_prompt(lib, payload, event)
    path, led = owned
    if payload.get("background_tasks"):
        return 0  # the turn ended but the work has not (REDTEAM B3)
    if payload.get("stop_hook_active") in (True, "true"):
        return 0  # one block per stop chain
    if int(led.get("blocks") or 0) >= lib.MAX_BLOCKS:
        # R4 item 4: the cap ends gating. Closing the ledger makes that hold
        # for every later stop without running anything.
        led["passes"] = False
        lib.close_ledger(path, led, "cap")
        _say(event, "JORDAN done-gate: this ledger was blocked %d times and is now closed without "
             "a passing check (last verdict: %s). Treat the result as unverified."
             % (lib.MAX_BLOCKS, (led.get("last_run") or {}).get("verdict", "not run")))
        return 0

    # Two Stop events can arrive for one turn; the second must not run the
    # check alongside the first.
    lock = path + ".lock"
    try:
        if os.path.exists(lock) and time.time() - os.stat(lock).st_mtime > 700:
            os.unlink(lock)
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except OSError:
        return 0
    try:
        return _gate(lib, event, path, led)
    finally:
        try:
            os.unlink(lock)
        except OSError:
            pass


def _gate(lib, event, path, led):
    root = led["root"]
    if not os.path.isdir(root):
        # A removed worktree: close it, or every later stop reports the same error.
        led["passes"] = False
        lib.close_ledger(path, led, "error")
        _say(event, "JORDAN done-gate: workspace %s no longer exists; the ledger is closed and "
             "its check was NOT verified." % root)
        return 0
    notes = []
    last = led.get("last_run") or {}
    before = lib.tree_hash(led)
    unchanged = before is not None and before == last.get("tree_hash")
    if unchanged and last.get("verdict") == "timeout":
        return 0  # already reported; running it again would only time out again

    if unchanged and last.get("verdict") == "green":
        verdict, code, output = "green", 0, ""  # nothing changed since it passed
    else:
        started = time.time()
        verdict, code, output = _run_check(led["check"], root, int(led.get("timeout_s") or lib.DEFAULT_TIMEOUT_S))
        led["last_run"] = {
            "ts": lib.now(), "verdict": verdict, "exit_code": code,
            "duration_s": round(time.time() - started, 1),
            # Hashed after the run: the check may leave files of its own behind.
            "tree_hash": lib.tree_hash(led),
        }

    # Compared after the run, so a check that rewrites existing tests
    # (`jest -u`, a formatter with --fix) is seen as well.
    changes = lib.protected_changes(led)
    if changes is None:
        notes.append("not a git workspace, so no path protection is claimed")
        unauth, auth = [], []
    else:
        unauth, auth = changes

    if verdict == "timeout":
        led["passes"] = "timeout"
        lib.write_json(path, led)
        msg = ("JORDAN done-gate: the check timed out after %d s (%s). It did not pass; "
               "report the result as unverified." % (led["timeout_s"], led["check"]))
        _say(event, msg, msg)
        return 0

    if verdict == "red" or unauth:
        led["passes"] = False
        led["blocks"] = int(led.get("blocks") or 0) + 1
        lib.write_json(path, led)
        parts = []
        if unauth:
            parts.append(
                "JORDAN done-gate: protected files that existed before this task were changed:\n"
                + "\n".join("  %s  (matches %s)" % pair for pair in unauth)
                + "\nRestore them, or if the task requires the change: "
                  "jordan-ledger authorise <path> --reason '<why>' (recorded and shown).")
        if verdict == "red":
            parts.append("JORDAN done-gate: the check failed (exit %s): %s\n--- last lines of output ---\n%s\n---"
                         % (code, led["check"], _tail(output) or "(no output)"))
        else:
            parts.append("The check itself passed: %s" % led["check"])
        parts.append(lib.THREE_EXITS)
        sys.stderr.write("\n".join(parts) + "\n")
        return 2

    led["passes"] = True
    lib.close_ledger(path, led, "gate")
    for rel, reason in auth:
        notes.append("authorised change to protected file %s (%s)" % (rel, reason))
    if notes:
        _say(event, "JORDAN done-gate: check passed (%s); %s." % (led["check"], "; ".join(notes)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # a broken gate never traps the agent
        msg = "JORDAN done-gate: internal error, stop allowed, check NOT verified: %r" % (exc,)
        sys.stderr.write(msg + "\n")
        try:
            print(json.dumps({"systemMessage": msg}))
        except Exception:
            pass
        sys.exit(0)
