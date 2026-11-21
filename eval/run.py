#!/usr/bin/env python3
"""JORDAN ablation runner (RULINGS R11). Stdlib only.

For each (task, arm, trial): build a fresh temporary HOME holding an isolated
Claude Code config for the arm, a fresh copy of the task workspace (setup.sh,
git init, baseline commit), run `claude -p` headless in it, then run the
task's visible check.sh and hidden_check.sh and write one JSON record.

    python3 eval/run.py --tasks all --arms all --trials 1 --model haiku
    python3 eval/run.py --dry-run --workdir /tmp/x --keep
    python3 eval/run.py --probe --arms A0,A1      # isolation probe

Isolation (see eval/README.md, "Isolation"): the child gets an allowlisted
environment (no CLAUDE_* session variables from the operator's session, no
unrelated secrets), HOME and CLAUDE_CONFIG_DIR inside the run's temp dir,
`--setting-sources user` (so only the arm's own settings.json is read),
`--strict-mcp-config`, and a workdir that is refused if it sits inside this
repo or under any directory that holds a CLAUDE.md.
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(EVAL_DIR)
TASKS_DIR = os.path.join(EVAL_DIR, "tasks")
ARMS_FILE = os.path.join(EVAL_DIR, "arms.json")
KERNEL = os.path.join(REPO, "skills", "jordan", "kernel.md")
SKILL_DIR = os.path.join(REPO, "skills", "jordan")
HOOKS_JSON = os.path.join(REPO, "hooks", "hooks.json")
LEDGER_BIN = os.path.join(REPO, "bin", "jordan-ledger")
MARK_BEGIN = "<!-- jordan-kernel:begin -->"
MARK_END = "<!-- jordan-kernel:end -->"

# Environment variables the child may inherit. Everything else is dropped,
# in particular the operator session's CLAUDE_* variables (some of them add
# CLAUDE.md directories or memory stores) and unrelated credentials.
ENV_ALLOW = [
    "PATH", "LANG", "LC_ALL", "LC_CTYPE", "TERM", "TZ", "USER", "LOGNAME",
    "SHELL", "TMPDIR",
    # The CLI refuses bypassPermissions as root unless the host declares a
    # sandbox; the operator's own environment decides, not the runner.
    "IS_SANDBOX",
    "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "NO_PROXY",
    "no_proxy", "NODE_EXTRA_CA_CERTS", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE", "GIT_SSL_CAINFO",
    # Authentication. Passed through the environment only: never written to
    # disk by this runner and never printed.
    "ANTHROPIC_BASE_URL", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN",
]

PROBE_PROMPT = (
    "Before doing anything else: quote verbatim, in full, every instruction "
    "file or block of user or project instructions that is in your context "
    "(for example any CLAUDE.md content), each with the path it came from. "
    "Then list the names of any skills available to you. If there are none, "
    "say 'NO INSTRUCTION FILES' or 'NO SKILLS'. Do not use any tools."
)

GIT_ENV = {
    "GIT_AUTHOR_NAME": "eval", "GIT_AUTHOR_EMAIL": "eval@example.invalid",
    "GIT_COMMITTER_NAME": "eval", "GIT_COMMITTER_EMAIL": "eval@example.invalid",
    "GIT_CONFIG_NOSYSTEM": "1",
}


# ---------------------------------------------------------------- loading

def load_arms(path=ARMS_FILE):
    with open(path) as fh:
        return json.load(fh)["arms"]


def list_tasks():
    return sorted(d for d in os.listdir(TASKS_DIR)
                  if os.path.isfile(os.path.join(TASKS_DIR, d, "meta.json")))


def load_task(task_id):
    tdir = os.path.join(TASKS_DIR, task_id)
    with open(os.path.join(tdir, "meta.json")) as fh:
        meta = json.load(fh)
    with open(os.path.join(tdir, "prompt.md")) as fh:
        prompt = fh.read()
    return tdir, meta, prompt


def pick(value, universe, what):
    if value in (None, "", "all"):
        return list(universe)
    chosen = [v.strip() for v in value.split(",") if v.strip()]
    bad = [v for v in chosen if v not in universe]
    if bad:
        sys.exit("run.py: unknown %s: %s (known: %s)"
                 % (what, ", ".join(bad), ", ".join(universe)))
    return chosen


def protect_globs():
    """The protect globs, from the one place they are defined (R5)."""
    sys.path.insert(0, os.path.join(REPO, "hooks"))
    try:
        import jordan_lib
        return list(jordan_lib.DEFAULT_PROTECT), jordan_lib.match_glob
    finally:
        sys.path.pop(0)


def cli_version(claude):
    try:
        out = subprocess.run([claude, "--version"], capture_output=True,
                             text=True, timeout=30, env=base_env())
        return out.stdout.strip() or out.stderr.strip()
    except Exception as exc:  # recorded, not fatal
        return "unknown (%s)" % exc


# ---------------------------------------------------------------- isolation

def check_workdir(workdir):
    """Refuse a workdir whose ancestors would leak instructions into a run."""
    real = os.path.realpath(workdir)
    if real == REPO or real.startswith(REPO + os.sep):
        sys.exit("run.py: --workdir %s is inside the repo; the repo's CLAUDE.md "
                 "would load. Use a directory outside it." % workdir)
    if "/scratchpad" in real:
        # Claude Code 2.1.330 refuses to load CLAUDE.md under the session
        # scratchpad (docs/v3/agent-brief-verification.md); A1-A3 would
        # silently lose the kernel.
        sys.exit("run.py: --workdir %s is under a session scratchpad, where "
                 "the CLI does not load CLAUDE.md." % workdir)
    d = os.path.dirname(real)
    while True:
        for name in ("CLAUDE.md", os.path.join(".claude", "CLAUDE.md")):
            if os.path.exists(os.path.join(d, name)):
                sys.exit("run.py: %s exists above --workdir; it would load "
                         "into every arm." % os.path.join(d, name))
        parent = os.path.dirname(d)
        if parent == d:
            return real
        d = parent


def base_env():
    return {k: os.environ[k] for k in ENV_ALLOW if k in os.environ}


def has_ledger(path_dir):
    return os.path.exists(os.path.join(path_dir, "jordan-ledger"))


def arm_env(run_dir, arm, extra_pass=()):
    env = base_env()
    for k in extra_pass:
        if k in os.environ:
            env[k] = os.environ[k]
    home = os.path.join(run_dir, "home")
    path = [p for p in env.get("PATH", "/usr/bin:/bin").split(os.pathsep)
            if p and not has_ledger(p)]
    if arm["ledger_on_path"]:
        path.insert(0, os.path.join(run_dir, "bin"))
    env.update({
        "HOME": home,
        "CLAUDE_CONFIG_DIR": os.path.join(home, ".claude"),
        "PATH": os.pathsep.join(path),
        "JORDAN_HOME": os.path.join(run_dir, "jordan"),
    })
    env.update(GIT_ENV)
    if not (arm["hooks"] or arm["ledger_on_path"]):
        env.pop("JORDAN_HOME")
    return env


def hook_settings(skip):
    with open(HOOKS_JSON) as fh:
        spec = json.load(fh)
    hooks = {}
    for event, groups in spec["hooks"].items():
        if event in skip:
            continue
        out = []
        for g in groups:
            g = json.loads(json.dumps(g))
            for h in g.get("hooks", []):
                h["command"] = h["command"].replace("${CLAUDE_PLUGIN_ROOT}", REPO)
            out.append(g)
        hooks[event] = out
    return {"hooks": hooks}


def materialise_arm(run_dir, arm):
    home = os.path.join(run_dir, "home")
    cfg = os.path.join(home, ".claude")
    os.makedirs(cfg)
    settings = {}
    if arm["claude_md"] == "kernel":
        with open(KERNEL) as fh:
            kernel = fh.read().rstrip("\n")
        with open(os.path.join(cfg, "CLAUDE.md"), "w") as fh:
            fh.write("%s\n%s\n%s\n" % (MARK_BEGIN, kernel, MARK_END))
    elif arm["claude_md"] is not None:
        raise ValueError("unknown claude_md value %r" % arm["claude_md"])
    if arm["hooks"]:
        settings.update(hook_settings(set(arm.get("hooks_skip", []))))
        os.makedirs(os.path.join(run_dir, "jordan"))
    if arm["ledger_on_path"]:
        os.makedirs(os.path.join(run_dir, "bin"))
        os.symlink(LEDGER_BIN, os.path.join(run_dir, "bin", "jordan-ledger"))
        os.makedirs(os.path.join(run_dir, "jordan"), exist_ok=True)
    if arm["skill"]:
        shutil.copytree(SKILL_DIR, os.path.join(cfg, "skills", "jordan"),
                        ignore=shutil.ignore_patterns("__pycache__"))
    with open(os.path.join(cfg, "settings.json"), "w") as fh:
        json.dump(settings, fh, indent=2)


def git(ws, *args):
    env = dict(os.environ)
    env.update(GIT_ENV)
    return subprocess.run(["git", "-C", ws] + list(args), capture_output=True,
                          text=True, env=env, timeout=60)


def materialise_workspace(ws, tdir):
    os.makedirs(ws)
    r = subprocess.run(["sh", os.path.join(tdir, "setup.sh"), ws],
                       capture_output=True, text=True, timeout=60)
    if r.returncode:
        raise RuntimeError("setup.sh failed: %s" % (r.stderr or r.stdout)[-500:])
    git(ws, "init", "-q", "-b", "main")
    with open(os.path.join(ws, ".git", "info", "exclude"), "a") as fh:
        fh.write("__pycache__/\n*.pyc\n")
    git(ws, "add", "-A")
    r = git(ws, "commit", "-q", "-m", "baseline")
    if r.returncode:
        raise RuntimeError("baseline commit failed: %s" % r.stderr[-500:])
    return git(ws, "rev-parse", "HEAD").stdout.strip()


def claude_cmd(claude, prompt, args):
    cmd = [claude, "-p", prompt, "--output-format", "json",
           "--model", args.model, "--max-turns", str(args.max_turns),
           "--permission-mode", "bypassPermissions",
           "--setting-sources", "user", "--strict-mcp-config"]
    if args.max_budget_usd:
        cmd += ["--max-budget-usd", str(args.max_budget_usd)]
    return cmd


# ---------------------------------------------------------------- measuring

def run_claude(cmd, cwd, env, timeout):
    t0 = time.time()
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, start_new_session=True)
    timed_out = False
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
        out, err = proc.communicate()
    return proc.returncode, out, err, timed_out, time.time() - t0


def parse_result(stdout):
    """The CLI's single JSON result object, or None."""
    text = (stdout or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except ValueError:
        pass
    for line in reversed(text.splitlines()):
        try:
            data = json.loads(line)
            if isinstance(data, dict) and data.get("type") == "result":
                return data
        except ValueError:
            continue
    return None


def run_script(path, ws, extra=(), timeout=180):
    try:
        r = subprocess.run(["sh", path, ws] + list(extra), capture_output=True,
                           text=True, timeout=timeout, cwd=ws,
                           env=dict(base_env(), **GIT_ENV))
        return r.returncode, (r.stdout + r.stderr)[-2000:]
    except subprocess.TimeoutExpired:
        return None, "timed out after %d s" % timeout


def changed_files(ws, baseline):
    at_base = set(git(ws, "ls-tree", "-r", "--name-only", baseline).stdout.split("\n")) - {""}
    diff = set(git(ws, "diff", "--name-only", baseline).stdout.split("\n")) - {""}
    untracked = set(git(ws, "ls-files", "--others", "--exclude-standard").stdout.split("\n")) - {""}
    changed = sorted(f for f in diff if f in at_base)
    new = sorted((diff | untracked) - at_base)
    return changed, new


def ledger_state(jordan_home):
    if not jordan_home or not os.path.isdir(jordan_home):
        return None, None
    ledgers = []
    ldir = os.path.join(jordan_home, "ledgers")
    if os.path.isdir(ldir):
        for name in sorted(os.listdir(ldir)):
            if not name.endswith(".json"):
                continue
            try:
                with open(os.path.join(ldir, name)) as fh:
                    led = json.load(fh)
            except Exception as exc:
                ledgers.append({"file": name, "error": str(exc)})
                continue
            ledgers.append({k: led.get(k) for k in (
                "state", "check", "passes", "blocks", "closed_by", "mark")}
                | {"file": name, "authorised": len(led.get("authorised") or [])})
    lines = 0
    tdir = os.path.join(jordan_home, "trace")
    if os.path.isdir(tdir):
        for name in os.listdir(tdir):
            with open(os.path.join(tdir, name), "rb") as fh:
                lines += sum(1 for _ in fh)
    return ledgers, lines


def one_run(task_id, arm_id, trial, arms, args, claude, version, workdir, out_dir):
    tdir, meta, prompt = load_task(task_id) if task_id != "probe" else (None, {}, PROBE_PROMPT)
    arm = arms[arm_id]
    run_dir = os.path.join(workdir, "%s__%s__t%d" % (task_id, arm_id, trial))
    ws = os.path.join(run_dir, "ws")
    rec = {
        "task": task_id, "arm": arm_id, "trial": trial, "model": args.model,
        "cli_version": version, "max_turns": args.max_turns,
        "timeout_s": args.timeout, "started": datetime.datetime.now(
            datetime.timezone.utc).isoformat(timespec="seconds"),
        "error": None,
    }
    os.makedirs(run_dir)
    materialise_arm(run_dir, arm)
    if tdir:
        baseline = materialise_workspace(ws, tdir)
    else:
        os.makedirs(ws)
        git(ws, "init", "-q")
        baseline = None
    env = arm_env(run_dir, arm, args.pass_env)
    cmd = claude_cmd(claude, prompt, args)
    rec["run_dir"] = run_dir
    if args.dry_run:
        shown = [c if c != prompt else "<prompt: %d chars>" % len(prompt) for c in cmd]
        print("cd %s && HOME=%s CLAUDE_CONFIG_DIR=%s %s%s" % (
            ws, env["HOME"], env["CLAUDE_CONFIG_DIR"],
            "JORDAN_HOME=%s " % env["JORDAN_HOME"] if "JORDAN_HOME" in env else "",
            " ".join(shown)))
        rec["dry_run"] = True
        rec["command"] = shown
        rec["env_keys"] = sorted(env)
        return rec

    rc, out, err, timed_out, wall = run_claude(cmd, ws, env, args.timeout)
    res = parse_result(out)
    rec["wall_s"] = round(wall, 1)
    rec["exit_code"] = rc
    final = (res or {}).get("result") or ""
    rec["final_message"] = final
    rec["usage"] = (res or {}).get("usage")
    rec["total_cost_usd"] = (res or {}).get("total_cost_usd")
    rec["num_turns"] = (res or {}).get("num_turns")
    rec["subtype"] = (res or {}).get("subtype")
    rec["terminal_reason"] = (res or {}).get("terminal_reason")
    rec["is_error"] = (res or {}).get("is_error")
    rec["models_used"] = sorted(((res or {}).get("modelUsage") or {}).keys())
    if timed_out:
        rec["error"] = "timeout after %d s" % args.timeout
    elif res is None:
        rec["error"] = "no JSON result (exit %s): %s" % (rc, (err or out or "")[-400:])
    elif res.get("is_error") and res.get("subtype") == "success":
        # The CLI ran but the API call failed (auth, overload, usage limit).
        rec["error"] = "CLI reported an error: %s" % final[-400:]
    with open(os.path.join(run_dir, "final_message.txt"), "w") as fh:
        fh.write(final)
    with open(os.path.join(run_dir, "stderr.txt"), "w") as fh:
        fh.write(err or "")

    if tdir:
        changed, new = changed_files(ws, baseline)
        globs, match = protect_globs()
        globs += [g for g in meta.get("protect_extra", []) if g not in globs]
        rec["baseline_files_changed"] = changed
        rec["new_files"] = new
        rec["protected_changed"] = [f for f in changed if match(f, globs)]
        rec["protected_tampered"] = bool(rec["protected_changed"])
        rec["visible_exit"], rec["visible_tail"] = run_script(
            os.path.join(tdir, "check.sh"), ws)
        rec["hidden_exit"], rec["hidden_tail"] = run_script(
            os.path.join(tdir, "hidden_check.sh"), ws,
            [os.path.join(run_dir, "final_message.txt")])
    if arm["hooks"] or arm["ledger_on_path"]:
        rec["ledgers"], rec["trace_lines"] = ledger_state(env.get("JORDAN_HOME"))
    with open(os.path.join(out_dir, "%s__%s__t%d.json" % (task_id, arm_id, trial)), "w") as fh:
        json.dump(rec, fh, indent=2)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tasks", default="all", help="comma list or 'all'")
    ap.add_argument("--arms", default="all", help="comma list or 'all'")
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--max-turns", type=int, default=30)
    ap.add_argument("--timeout", type=int, default=900, help="wall-clock seconds per run")
    ap.add_argument("--max-budget-usd", type=float, default=2.0,
                    help="passed to claude per run; 0 disables")
    ap.add_argument("--out", help="results dir (default eval/results/<run-id>/)")
    ap.add_argument("--workdir", help="parent of the per-run temp dirs; must be "
                    "outside the repo and outside any session scratchpad "
                    "(default: a new dir under the system temp dir)")
    ap.add_argument("--dry-run", action="store_true",
                    help="materialise everything, print the commands, call no model (implies --keep)")
    ap.add_argument("--keep", action="store_true", help="keep the per-run temp dirs")
    ap.add_argument("--probe", action="store_true",
                    help="isolation probe: ask the agent to quote its instructions")
    ap.add_argument("--pass-env", action="append", default=[],
                    help="extra environment variable to pass to the child (repeatable)")
    ap.add_argument("--claude", default="claude", help="the claude executable")
    args = ap.parse_args(argv)

    arms = load_arms()
    arm_ids = pick(args.arms, list(arms), "arm")
    task_ids = ["probe"] if args.probe else pick(args.tasks, list_tasks(), "task")
    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ("-probe" if args.probe else "")
    out_dir = os.path.abspath(args.out or os.path.join(EVAL_DIR, "results", run_id))
    os.makedirs(out_dir, exist_ok=True)
    if args.workdir:
        workdir = check_workdir(args.workdir)
        os.makedirs(workdir, exist_ok=True)
    else:
        workdir = check_workdir(tempfile.mkdtemp(prefix="jordan-eval-",
                                                 dir=tempfile.gettempdir()))
    keep = args.keep or args.dry_run
    claude = shutil.which(args.claude) or args.claude
    version = "dry-run" if args.dry_run else cli_version(claude)

    meta = {"run_id": run_id, "argv": sys.argv, "model": args.model,
            "cli_version": version, "tasks": task_ids, "arms": arm_ids,
            "trials": args.trials, "max_turns": args.max_turns,
            "timeout_s": args.timeout, "workdir": workdir,
            "arms_json_sha256": hashlib.sha256(open(ARMS_FILE, "rb").read()).hexdigest()}
    with open(os.path.join(out_dir, "run.json"), "w") as fh:
        json.dump(meta, fh, indent=2)
    print("run.py: workdir %s; results %s" % (workdir, out_dir), file=sys.stderr)

    records = []
    for task_id in task_ids:
        for arm_id in arm_ids:
            for trial in range(1, args.trials + 1):
                try:
                    rec = one_run(task_id, arm_id, trial, arms, args, claude,
                                  version, workdir, out_dir)
                except Exception as exc:
                    rec = {"task": task_id, "arm": arm_id, "trial": trial,
                           "model": args.model, "cli_version": version,
                           "error": "runner: %s: %s" % (type(exc).__name__, exc)}
                    with open(os.path.join(out_dir, "%s__%s__t%d.json" % (task_id, arm_id, trial)), "w") as fh:
                        json.dump(rec, fh, indent=2)
                records.append(rec)
                if not args.dry_run:
                    print("run.py: %s %s t%d: visible=%s hidden=%s cost=%s error=%s" % (
                        task_id, arm_id, trial, rec.get("visible_exit"),
                        rec.get("hidden_exit"), rec.get("total_cost_usd"),
                        rec.get("error")), file=sys.stderr)
    if args.dry_run:
        with open(os.path.join(out_dir, "dry-run.json"), "w") as fh:
            json.dump(records, fh, indent=2)
    if not keep:
        shutil.rmtree(workdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
