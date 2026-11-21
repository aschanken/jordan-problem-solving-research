#!/usr/bin/env python3
"""done_gate.py — Stop / SubagentStop hook: re-run the task's check (RULINGS R4).

Runs only when all of these hold, else exits 0 with no output:
  1. an open ledger is owned by this session_id and agent_id;
  2. no background tasks are running;
  3. this is not a stop the gate already blocked (stop_hook_active).
A ledger is blocked at most twice; after that the gate reports and allows.
Then it checks protected paths and runs the check in the workspace root,
unless the tree is unchanged since a green run it recorded.

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
    """(verdict, exit_code, output). The check gets its own process group so a
    timeout kills what it started, not only the shell."""
    import signal
    import subprocess
    proc = subprocess.Popen(
        command, shell=True, cwd=root, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True,
        env=dict(os.environ, JORDAN_GATE="1"))
    try:
        out, _ = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            proc.kill()
        try:
            proc.communicate(timeout=5)
        except Exception:
            pass
        return "timeout", None, ""
    text = out.decode("utf-8", "replace")
    return ("green" if proc.returncode == 0 else "red"), proc.returncode, text


def _capped_message(lib, verdict):
    return ("JORDAN done-gate: this ledger has been blocked %d times and is not blocked again. "
            "Check verdict: %s. Treat the result as unverified." % (lib.MAX_BLOCKS, verdict))


def _tail(text, lines=40, width=400, total=8000):
    rows = [r[:width] for r in text.rstrip().splitlines()[-lines:]]
    return "\n".join(rows)[-total:]


def main():
    import jordan_lib as lib
    payload = lib.read_payload()
    if not payload.get("session_id") or not os.path.isdir(lib.ledgers_dir()):
        return 0
    event = payload.get("hook_event_name") or "Stop"
    # Fallback claim, for when no tool call followed `jordan-ledger open`.
    lib.claim_pending(payload, immediate=True)
    owned = lib.load_owned(payload)
    if not owned:
        return 0
    path, led = owned
    if payload.get("background_tasks"):
        return 0  # the turn ended but the work has not (REDTEAM B3)
    if payload.get("stop_hook_active") is True:
        return 0  # one block per stop chain

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
        raise RuntimeError("workspace root %s no longer exists" % root)
    notes = []
    last = led.get("last_run") or {}
    before = lib.tree_hash(led)
    unchanged = before is not None and before == last.get("tree_hash")
    if unchanged and last.get("verdict") == "timeout":
        return 0  # already reported; running it again would only time out again
    # At the cap the gate never blocks again, but a tree that changed since is
    # still checked once, so work that was fixed late closes green rather than
    # leaving a red ledger behind.
    capped = int(led.get("blocks") or 0) >= lib.MAX_BLOCKS
    if capped and unchanged and last.get("verdict") == "red":
        _say(event, _capped_message(lib, "red"))
        return 0

    changes = lib.protected_changes(led)
    if changes is None:
        if not led.get("nongit_noticed"):
            notes.append("not a git workspace, so no path protection is claimed")
        unauth, auth = [], []
    else:
        unauth, auth = changes

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

    if verdict == "timeout":
        led["passes"] = "timeout"
        lib.write_json(path, led)
        msg = ("JORDAN done-gate: the check timed out after %d s (%s). It did not pass; "
               "report the result as unverified." % (led["timeout_s"], led["check"]))
        _say(event, msg, msg)
        return 0

    if verdict == "red" or unauth:
        led["passes"] = False
        if capped:
            lib.write_json(path, led)
            _say(event, _capped_message(lib, "red" if verdict == "red" else
                                        "green, with unauthorised changes to protected files"))
            return 0
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
    if notes:
        led["nongit_noticed"] = True
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
