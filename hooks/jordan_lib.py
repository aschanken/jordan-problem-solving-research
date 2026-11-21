"""jordan_lib.py — shared code for the JORDAN v3 hooks and the jordan-ledger CLI.

One module so that the protect globs, the guard patterns and the ledger format
are each defined once (RULINGS R3-R7). Stdlib only. Heavy imports (subprocess,
hashlib) are done inside the functions that need them: every hook runs on every
tool call in every session, and the no-ledger path must stay cheap.

State lives outside the workspace (REDTEAM B2), under $JORDAN_HOME:
    ledgers/<session_id>[.<agent_id>].json   one per owner
    ledgers/pending-<key>.json               opened by the CLI, not yet claimed
    trace/<session_id>.jsonl
    guard.json                               optional opt-ins for the guard
"""
import json
import os
import re
import sys
import time

VERSION = 1
KERNEL_MARKER = "<!-- jordan-kernel:begin -->"

DEFAULT_TIMEOUT_S = 120
# The done-gate hook is registered with a 600 s timeout; the check must finish
# and be reported inside it, so the ledger timeout is clamped below that.
MAX_TIMEOUT_S = 540
MAX_BLOCKS = 2
# An unclaimed pending ledger older than this is somebody's abandoned open;
# claiming it would gate a new session with an old check (REDTEAM B1).
PENDING_MAX_AGE_S = 900
# A hook event that did not itself run jordan-ledger claims a pending ledger
# only after this long, so the agent that ran `open` normally claims first.
PENDING_GRACE_S = 10
SESSION_ENV = "CLAUDE_CODE_SESSION_ID"  # seen in the Bash tool env, CLI 2.1.330
SNAPSHOT_CAP = 5000

# RULINGS R5. A pattern with no slash matches the basename at any depth.
DEFAULT_PROTECT = [
    "test/**", "tests/**", "**/__tests__/**", "**/test_*.*", "**/*_test.*",
    "**/*.test.*", "**/*.spec.*", ".github/**", "conftest.py", "pytest.ini",
    "tox.ini", "Makefile", "package.json", "noxfile.py",
]

THREE_EXITS = (
    "Three ways forward:\n"
    "  1. Fix the work, then stop again; the check re-runs.\n"
    "  2. If the result cannot be verified here: "
    "jordan-ledger mark unverified --reason '<why>', and report it as unverified.\n"
    "  3. If the task cannot be done as written (the checks contradict the request): "
    "jordan-ledger mark impossible --reason '<why>', and report that. It is a correct result.\n"
    "Do not edit the check or tests that existed before the task to make this pass."
)


# ---------------------------------------------------------------- basics

def read_payload():
    """Hook stdin as a dict. Empty, malformed or non-object input gives {}."""
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def jordan_home():
    return os.path.abspath(os.path.expanduser(
        os.environ.get("JORDAN_HOME") or "~/.claude/jordan"))


def ledgers_dir():
    return os.path.join(jordan_home(), "ledgers")


def trace_dir():
    return os.path.join(jordan_home(), "trace")


_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def safe_id(value):
    """Ids become file names; anything that is not a plain token is refused."""
    return value if isinstance(value, str) and _SAFE_ID.match(value) else None


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def write_json(path, data):
    """Atomic: a hook reading mid-write must see the old file or the new one."""
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    tmp = "%s.tmp.%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def git(root, *args, timeout=20):
    """Run git in root. Returns (returncode, stdout); (1, '') on any failure."""
    import subprocess
    try:
        proc = subprocess.run(
            ["git", "-c", "core.quotepath=off", *args], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout)
        return proc.returncode, proc.stdout.decode("utf-8", "replace")
    except Exception:
        return 1, ""


def workspace_root(cwd):
    """Git toplevel of cwd, else cwd itself. Always a real path."""
    cwd = os.path.realpath(cwd or os.getcwd())
    rc, out = git(cwd, "rev-parse", "--show-toplevel")
    if rc == 0 and out.strip():
        return os.path.realpath(out.strip())
    return cwd


def is_git(root):
    rc, out = git(root, "rev-parse", "--is-inside-work-tree")
    return rc == 0 and out.strip() == "true"


def is_inside(path, root, strict=False):
    path, root = os.path.realpath(path), os.path.realpath(root)
    if path == root:
        return not strict
    return path.startswith(root.rstrip(os.sep) + os.sep)


# ---------------------------------------------------------------- globs

_GLOB_CACHE = {}


def _glob_regex(pattern):
    rx = _GLOB_CACHE.get(pattern)
    if rx is None:
        out, i, n = [], 0, len(pattern)
        while i < n:
            if pattern.startswith("**/", i):
                out.append("(?:.*/)?")
                i += 3
            elif pattern.startswith("**", i):
                out.append(".*")
                i += 2
            elif pattern[i] == "*":
                out.append("[^/]*")
                i += 1
            elif pattern[i] == "?":
                out.append("[^/]")
                i += 1
            else:
                out.append(re.escape(pattern[i]))
                i += 1
        rx = _GLOB_CACHE[pattern] = re.compile("^" + "".join(out) + "$")
    return rx


def match_glob(rel, globs):
    """First glob matching the workspace-relative path, else None."""
    rel = rel.replace(os.sep, "/")
    if rel.startswith("./"):
        rel = rel[2:]
    base = rel.rsplit("/", 1)[-1]
    for pattern in globs or ():
        target = rel if "/" in pattern else base
        if _glob_regex(pattern).match(target):
            return pattern
    return None


# ---------------------------------------------------------------- tree state

def file_sha(path):
    import hashlib
    try:
        if os.path.islink(path):
            return "link:" + os.readlink(path)
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 16), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _zlist(out):
    return [p for p in out.split("\0") if p]


def snapshot_protected(root, baseline, globs):
    """Hashes of protected files the baseline commit cannot vouch for.

    `git diff <baseline>` shows later changes to clean tracked files. Files that
    were already modified, staged or untracked when the ledger opened need their
    content recorded, or pre-existing dirt would read as tampering and a real
    edit to an untracked test would read as nothing.
    """
    if baseline:
        names = set(_zlist(git(root, "diff", "--name-only", "--no-renames", "-z", baseline)[1]))
        names |= set(_zlist(git(root, "ls-files", "-o", "--exclude-standard", "-z")[1]))
    else:  # no commit yet: nothing is vouched for
        names = set(_zlist(git(root, "ls-files", "-co", "--exclude-standard", "-z")[1]))
    snap = {}
    for rel in sorted(names):
        if match_glob(rel, globs):
            snap[rel] = file_sha(os.path.join(root, rel))
            if len(snap) >= SNAPSHOT_CAP:
                break
    return snap


def tree_hash(ledger):
    """Hash of the work so far: `git diff <baseline>` plus untracked files.

    None for a non-git workspace, which the gate reads as "always changed".
    Untracked files carry size and mtime so an edit to a new file counts.
    """
    if not ledger.get("git"):
        return None
    import hashlib
    root, baseline = ledger["root"], ledger.get("baseline")
    h = hashlib.sha256()
    if baseline:
        rc, out = git(root, "diff", "--no-ext-diff", "--no-color", baseline, timeout=60)
        h.update(out.encode("utf-8", "replace"))
    else:
        for extra in ((), ("--cached",)):
            rc, out = git(root, "diff", "--no-ext-diff", "--no-color", *extra, timeout=60)
            h.update(out.encode("utf-8", "replace"))
    if rc != 0:
        return None
    for rel in sorted(_zlist(git(root, "ls-files", "-o", "--exclude-standard", "-z")[1])):
        try:
            st = os.lstat(os.path.join(root, rel))
            h.update(("%s\0%d\0%d\n" % (rel, st.st_size, st.st_mtime_ns)).encode("utf-8", "replace"))
        except OSError:
            h.update((rel + "\0gone\n").encode("utf-8", "replace"))
    return h.hexdigest()


def existed_at_baseline(ledger, rel):
    if rel in (ledger.get("snapshot") or {}):
        return True
    baseline = ledger.get("baseline")
    if not baseline:
        return False
    return git(ledger["root"], "cat-file", "-e", "%s:%s" % (baseline, rel))[0] == 0


def is_authorised(ledger, rel):
    for entry in ledger.get("authorised") or ():
        pat = entry.get("path", "")
        if pat == rel or _glob_regex(pat).match(rel):
            return entry
    return None


def protected_changes(ledger):
    """Protected files changed since the ledger opened, by any tool (R5).

    Returns (unauthorised, authorised) as lists of (path, detail), or None for
    a non-git workspace, where no protection is claimed. Files created during
    the task are free: only what existed at baseline is protected.
    """
    if not ledger.get("git"):
        return None
    root, baseline = ledger["root"], ledger.get("baseline")
    globs, snap = ledger.get("protect") or [], ledger.get("snapshot") or {}
    changed = set()
    if baseline:
        fields = _zlist(git(root, "diff", "--name-status", "--no-renames", "-z", baseline)[1])
        for status, rel in zip(fields[0::2], fields[1::2]):
            # "A" is a file the task created. Snapshot files are judged by hash below.
            if not status.startswith("A") and rel not in snap and match_glob(rel, globs):
                changed.add(rel)
    for rel, sha in snap.items():
        if file_sha(os.path.join(root, rel)) != sha:
            changed.add(rel)
    unauth, auth = [], []
    for rel in sorted(changed):
        entry = is_authorised(ledger, rel)
        if entry:
            auth.append((rel, entry.get("reason", "")))
        else:
            unauth.append((rel, match_glob(rel, globs) or ""))
    return unauth, auth


# ---------------------------------------------------------------- ledgers

def root_key(root):
    import hashlib
    return hashlib.sha256(os.path.realpath(root).encode("utf-8", "replace")).hexdigest()[:16]


def pending_path(root):
    return os.path.join(ledgers_dir(), "pending-%s.json" % root_key(root))


def owner_path(session_id, agent_id=None):
    sid, aid = safe_id(session_id), safe_id(agent_id)
    if not sid or (agent_id and not aid):
        return None
    return os.path.join(ledgers_dir(), "%s.%s.json" % (sid, aid) if aid else "%s.json" % sid)


def load_owned(payload):
    """(path, ledger) for the open ledger owned by this session and agent.

    An absent agent_id matches only a ledger with none: the file name carries
    both, so the main session never picks up a subagent's ledger (REDTEAM B3).
    Costs one failed open() when there is no ledger.
    """
    path = owner_path(payload.get("session_id"), payload.get("agent_id") or None)
    if not path:
        return None
    ledger = read_json(path)
    if not ledger or ledger.get("state") != "open" or not ledger.get("root"):
        return None
    return path, ledger


def _age_s(path):
    try:
        return time.time() - os.stat(path).st_mtime
    except OSError:
        return 1e9


def claim_pending(payload, immediate):
    """Rename a pending ledger for this workspace to its owner's name (R3).

    The CLI cannot see who ran it, so `open` leaves a pending file keyed by the
    workspace root, and the first hook event from inside that root claims it.
    `immediate` is true for the event that ran jordan-ledger and for the stop;
    other events wait PENDING_GRACE_S so a sibling agent's tool call does not
    take the ledger first. A session hint recorded by the CLI, when present,
    must match.
    """
    sid = safe_id(payload.get("session_id"))
    cwd = payload.get("cwd")
    ldir = ledgers_dir()
    if not sid or not isinstance(cwd, str) or not os.path.isdir(ldir):
        return None
    try:
        names = [n for n in os.listdir(ldir) if n.startswith("pending-") and n.endswith(".json")]
    except OSError:
        return None
    for name in names:
        src = os.path.join(ldir, name)
        ledger = read_json(src)
        if not ledger or not ledger.get("root") or not is_inside(cwd, ledger["root"]):
            continue
        hint = ledger.get("session_hint")
        if hint and hint != sid:
            continue
        age = _age_s(src)
        if age > PENDING_MAX_AGE_S or (not immediate and age < PENDING_GRACE_S):
            continue
        dst = owner_path(sid, payload.get("agent_id") or None)
        if not dst:
            continue
        # The rename is the atomic take: of two racing hooks only one succeeds.
        taken = "%s.claim.%d" % (src, os.getpid())
        try:
            os.rename(src, taken)
        except OSError:
            continue
        ledger["session_id"] = sid
        ledger["agent_id"] = safe_id(payload.get("agent_id"))
        ledger["claimed"] = now()
        write_json(dst, ledger)
        try:
            os.unlink(taken)
        except OSError:
            pass
        return dst
    return None


def ledgers_for_root(root, session_hint=None):
    """Ledgers for a workspace root, open ones first, newest first. For the CLI."""
    ldir, found = ledgers_dir(), []
    try:
        names = os.listdir(ldir)
    except OSError:
        return found
    root = os.path.realpath(root)
    for name in names:
        if not name.endswith(".json"):
            continue
        path = os.path.join(ldir, name)
        ledger = read_json(path)
        if ledger and ledger.get("root") == root:
            found.append((path, ledger))
    found.sort(key=lambda pl: (pl[1].get("state") == "open", pl[1].get("created_ts", 0)), reverse=True)
    if session_hint:
        mine = [pl for pl in found if session_hint in (pl[1].get("session_id"), pl[1].get("session_hint"))]
        found = mine or found
    return found


def new_ledger(check, root, timeout_s, extra_protect=()):
    root = os.path.realpath(root)
    in_git = is_git(root)
    baseline = None
    if in_git:
        rc, out = git(root, "rev-parse", "--verify", "-q", "HEAD")
        baseline = out.strip() if rc == 0 and out.strip() else None
    globs = list(DEFAULT_PROTECT) + [g for g in extra_protect if g not in DEFAULT_PROTECT]
    return {
        "version": VERSION, "state": "open", "check": check,
        "timeout_s": max(1, min(int(timeout_s), MAX_TIMEOUT_S)),
        "root": root, "git": in_git, "baseline": baseline, "protect": globs,
        "snapshot": snapshot_protected(root, baseline, globs) if in_git else {},
        "authorised": [], "blocks": 0, "passes": None, "last_run": None,
        "created": now(), "created_ts": time.time(),
        "session_hint": safe_id(os.environ.get(SESSION_ENV)),
    }


def close_ledger(path, ledger, by, mark=None):
    ledger["state"] = "closed"
    ledger["closed"] = now()
    ledger["closed_by"] = by
    if mark:
        ledger["mark"] = mark
    write_json(path, ledger)


def prune_closed(max_age_s=7 * 86400):
    """Called by `open`: closed ledgers are a record, not an archive."""
    ldir = ledgers_dir()
    try:
        names = os.listdir(ldir)
    except OSError:
        return
    for name in names:
        path = os.path.join(ldir, name)
        if _age_s(path) < max_age_s:
            continue
        ledger = read_json(path) if name.endswith(".json") else None
        if ledger is None or ledger.get("state") != "open" or name.startswith("pending-"):
            try:
                os.unlink(path)
            except OSError:
                pass


# ---------------------------------------------------------------- guard (R6)

# Cheap test run before any parsing. After it matches, a parse failure denies.
GUARD_PREFILTER = re.compile(r"\b(?:rm|push|publish|upload|release)\b")
BYPASS_MODES = {"bypassPermissions", "dontAsk"}
GUARD_ADVICE = (
    " This cannot be undone. Get a decision first: ask the user, or if no one is"
    " reachable, return a decision request and stop. (JORDAN irreversible-guard:"
    " catches accidents, is not a sandbox.)"
)

_SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
_WRAPPERS = {"command", "nice", "time", "nohup", "exec", "builtin", "then", "do",
             "else", "elif", "if", "while", "until", "{", "!", "sudo", "doas"}
_SUDO_VALUE_FLAGS = {"-u", "-g", "-h", "-p", "-C", "-T", "-r", "-t", "-U", "-D"}
_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_HEREDOC = re.compile(r"(?<!<)<<(-?)\s*(?:'([^'\n]+)'|\"([^\"\n]+)\"|\\?([A-Za-z_][\w.-]*))")
_FEEDS_SHELL = re.compile(r"(?:^|[\s;|&(])(?:ba|z|da|k)?sh\b")
_VAR = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")
_REDIRECTS = {"<", ">", ">>", "<<", "<<-", "<<<", ">&", "<&", "&>", "&>>", ">|"}
_OPS = sorted(_REDIRECTS | {";", ";;", "&", "&&", "|", "||", "|&", "(", ")"}, key=len, reverse=True)
_CRED_READERS = {"cat", "less", "more", "head", "tail", "bat", "cp", "scp", "base64",
                 "xxd", "strings", "grep", "rg", "awk", "sed", "source", "."}
_CRED = re.compile(
    r"(?:^|/)\.env(?:\.(?!example$|sample$|template$|dist$)[\w.-]+)?$"
    r"|(?:^|/)\.ssh/id_[\w.-]+$|(?:^|/)id_(?:rsa|ed25519|ecdsa)$"
    r"|(?:^|/)\.aws/credentials$|(?:^|/)\.netrc$|(?:^|/)\.npmrc$|(?:^|/)\.pypirc$|\.pem$")


class GuardParseError(Exception):
    pass


class _Word:
    __slots__ = ("text", "dollar", "glob", "tilde")

    def __init__(self):
        self.text, self.dollar, self.glob, self.tilde = "", False, False, False


def _strip_heredocs(cmd):
    """Drop heredoc bodies unless they feed a shell.

    A body written to a file is data; it often holds apostrophes or the word
    "rm" and would otherwise fail the parse or trip a rule.
    """
    if "<<" not in cmd:
        return cmd
    lines, out, i = cmd.split("\n"), [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        for m in _HEREDOC.finditer(line):
            delim = m.group(2) or m.group(3) or m.group(4)
            keep = bool(_FEEDS_SHELL.search(line[:m.start()]))
            j, body = i, []
            while j < len(lines):
                text = lines[j].lstrip("\t") if m.group(1) else lines[j]
                if text == delim:
                    break
                body.append(lines[j])
                j += 1
            if j >= len(lines):  # no terminator: not a heredoc we understand
                continue
            if keep:
                out.extend(body)
            i = j + 1
    return "\n".join(out)


def tokenize(cmd):
    """Shell words and operators. Raises GuardParseError on an open quote.

    Returns a list of _Word and str (operator). Each word records whether it
    held an unquoted expansion, glob or leading tilde, which quoting removes.
    """
    toks, cur, i, n = [], None, 0, len(cmd)

    def flush():
        nonlocal cur
        if cur is not None:
            toks.append(cur)
            cur = None

    while i < n:
        c = cmd[i]
        if c == "\\":
            if i + 1 < n and cmd[i + 1] == "\n":
                i += 2
                continue
            cur = cur or _Word()
            cur.text += cmd[i + 1] if i + 1 < n else ""
            i += 2
        elif c == "'":
            j = cmd.find("'", i + 1)
            if j < 0:
                raise GuardParseError("unterminated single quote")
            cur = cur or _Word()
            cur.text += cmd[i + 1:j]
            i = j + 1
        elif c == '"':
            cur = cur or _Word()
            i += 1
            while True:
                if i >= n:
                    raise GuardParseError("unterminated double quote")
                d = cmd[i]
                if d == '"':
                    i += 1
                    break
                if d == "\\" and i + 1 < n and cmd[i + 1] in '"\\$`\n':
                    cur.text += "" if cmd[i + 1] == "\n" else cmd[i + 1]
                    i += 2
                    continue
                if d in "$`":
                    cur.dollar = True
                cur.text += d
                i += 1
        elif c in " \t\r":
            flush()
            i += 1
        elif c == "\n":
            flush()
            toks.append(";")
            i += 1
        elif c == "#" and cur is None:
            j = cmd.find("\n", i)
            i = n if j < 0 else j
        elif c == "`":
            # Command substitution: the word cannot be resolved, and what is
            # inside the backticks is a command of its own.
            cur = cur or _Word()
            cur.dollar = True
            cur.text += "`"
            flush()
            toks.append(";")
            i += 1
        elif c in ";|&()<>":
            flush()
            for op in _OPS:
                if cmd.startswith(op, i):
                    toks.append(op)
                    i += len(op)
                    break
        else:
            if cur is None:
                cur = _Word()
                if c == "~":
                    cur.tilde = True
            if c == "$":
                cur.dollar = True
            elif c in "*?[":
                cur.glob = True
            cur.text += c
            i += 1
    flush()
    return toks


def _simple_commands(toks):
    cmds, cur, skip = [], [], False
    for tok in toks:
        if isinstance(tok, str):
            if tok in _REDIRECTS:
                skip = True  # the next word is a file, not an argument
            else:
                if cur:
                    cmds.append(cur)
                cur, skip = [], False
        elif skip:
            skip = False
        else:
            cur.append(tok)
    if cur:
        cmds.append(cur)
    return cmds


def _strip_wrappers(argv):
    argv = list(argv)
    while argv:
        word = argv[0].text
        if _ASSIGN.match(word):
            argv.pop(0)
        elif word == "env":
            argv.pop(0)
            while argv and (argv[0].text.startswith("-") or _ASSIGN.match(argv[0].text)):
                argv.pop(0)
        elif word in _WRAPPERS:
            argv.pop(0)
            while argv and argv[0].text.startswith("-"):
                flag = argv.pop(0).text
                if word in ("sudo", "doas") and flag in _SUDO_VALUE_FLAGS and argv:
                    argv.pop(0)
        else:
            break
    return argv


def _positional(args):
    """Arguments that are not options; everything after `--` is positional."""
    out, opts_done = [], False
    for word in args:
        if not opts_done and word.text == "--":
            opts_done = True
        elif opts_done or not word.text.startswith("-") or word.text == "-":
            out.append(word)
    return out


def _flags(args):
    out = []
    for word in args:
        if word.text == "--":
            break
        if word.text.startswith("-"):
            out.append(word.text)
    return out


class _Ctx:
    def __init__(self, command, cwd, root, safe_roots, config, env):
        self.cwd, self.root, self.safe_roots = cwd, root, safe_roots
        self.config, self.env = config, env
        # A variable assigned anywhere in the command may differ from our env.
        self.assigned = set(re.findall(r"(?:^|[\s;&|(])([A-Za-z_][A-Za-z0-9_]*)=", command))


def _resolve(word, ctx):
    """Absolute path a word names, or None when it cannot be known here."""
    text, failed = word.text, []
    if word.dollar:
        def repl(m):
            name = m.group(1) or m.group(2)
            value = ctx.env.get(name)
            if not value or name in ctx.assigned:
                failed.append(name)
                return ""
            return value
        text = _VAR.sub(repl, text)
        if failed or "$" in text or "`" in text:
            return None
    if word.tilde:
        if text != "~" and not text.startswith("~/"):
            return None
        home = ctx.env.get("HOME")
        if not home:
            return None
        text = home + text[1:]
    if word.glob:
        # Judge the directory the glob expands in: what it matches lives there.
        parts, keep = text.split("/"), []
        for part in parts:
            if any(ch in part for ch in "*?["):
                break
            keep.append(part)
        text = "/".join(keep) if keep != [""] else "/"
        text = text or "."
    if not text:
        return None
    if not os.path.isabs(text):
        if ctx.cwd is None:
            return None
        text = os.path.join(ctx.cwd, text)
    return os.path.realpath(text)


def _check_rm(argv, ctx, out):
    flags = _flags(argv[1:])
    recursive = any(f in ("--recursive",) or (not f.startswith("--") and ("r" in f or "R" in f))
                    for f in flags)
    if not recursive:
        return
    for word in _positional(argv[1:]):
        path = _resolve(word, ctx)
        if path is None:
            out.append(("delete", "recursive delete of '%s', whose target cannot be resolved "
                        "before the shell expands it" % word.text))
            continue
        # A glob deletes the directory's contents; a plain path deletes itself,
        # so the workspace root is only acceptable as a glob's directory.
        ok = is_inside(path, ctx.root, strict=not word.glob)
        ok = ok or any(is_inside(path, r, strict=not word.glob) for r in ctx.safe_roots)
        if not ok:
            out.append(("delete", "recursive delete of '%s' (%s), which is outside the "
                        "workspace %s" % (word.text, path, ctx.root)))


def _git_subcommand(argv):
    i = 1
    while i < len(argv):
        text = argv[i].text
        if text in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
            i += 2
        elif text.startswith("-"):
            i += 1
        else:
            return text, argv[i + 1:]
    return None, []


def _check_git(argv, ctx, out):
    sub, rest = _git_subcommand(argv)
    if sub != "push":
        return
    flags, pos = _flags(rest), _positional(rest)
    forced = [f for f in flags if f in ("--force", "--mirror") or f.startswith("--force-with-lease")
              or (not f.startswith("--") and "f" in f)]
    plus = [w.text for w in pos if w.text.startswith("+")]
    if forced or plus:
        out.append(("force-push", "force-push (%s)" % ", ".join(forced + plus)))
        return
    if ctx.config.get("default_branch_push"):
        branches = set(ctx.config.get("default_branches") or ["main", "master"])
        refs = [w.text.rsplit(":", 1)[-1].replace("refs/heads/", "") for w in pos[1:]]
        if not refs and ctx.cwd:
            rc, head = git(ctx.cwd, "symbolic-ref", "--short", "-q", "HEAD")
            refs = [head.strip()] if rc == 0 else []
        hit = sorted(set(refs) & branches)
        if hit:
            out.append(("default-branch-push", "push to default branch %s" % ", ".join(hit)))


def _check_publish(argv, base, out):
    pos = [w.text for w in _positional(argv[1:])]
    flags = _flags(argv[1:])
    if "--dry-run" in flags or ("-n" in flags and base == "cargo"):
        return
    hit = None
    if base in ("npm", "pnpm", "bun") and pos[:1] == ["publish"]:
        hit = base + " publish"
    elif base == "yarn" and (pos[:1] == ["publish"] or pos[:2] == ["npm", "publish"]):
        hit = "yarn publish"
    elif base == "twine" and pos[:1] == ["upload"]:
        hit = "twine upload"
    elif base.startswith("python") and "twine" in pos and "upload" in pos:
        hit = "twine upload"
    elif base == "cargo" and pos[:1] == ["publish"]:
        hit = "cargo publish"
    elif base == "gh" and pos[:2] == ["release", "create"]:
        hit = "gh release create"
    if hit:
        out.append(("publish", "publish (%s)" % hit))


def _scan(command, ctx, out, depth=0):
    for raw in _simple_commands(tokenize(_strip_heredocs(command))):
        argv = _strip_wrappers(raw)
        if not argv:
            continue
        base = os.path.basename(argv[0].text)
        if base in ("cd", "pushd"):
            pos = _positional(argv[1:])
            ctx.cwd = _resolve(pos[0], ctx) if len(pos) == 1 else None
        elif base == "rm":
            _check_rm(argv, ctx, out)
        elif base == "git":
            _check_git(argv, ctx, out)
        elif base in _SHELLS or base == "eval":
            # One level of indirection is how most accidents are written.
            inner = None
            if base == "eval":
                inner = " ".join(w.text for w in argv[1:])
            else:
                for k, word in enumerate(argv[1:], 1):
                    if re.match(r"^-[a-zA-Z]*c$", word.text) and k + 1 < len(argv):
                        inner = argv[k + 1].text
                        break
            if inner and depth < 3:
                _scan(inner, ctx, out, depth + 1)
        else:
            _check_publish(argv, base, out)
        if ctx.config.get("credential_reads") and base in _CRED_READERS:
            for word in argv[1:]:
                if _CRED.search(word.text):
                    out.append(("credential-read", "read of credential file '%s'" % word.text))


def load_guard_config():
    """Opt-ins from $JORDAN_HOME/guard.json; {} when absent or unreadable."""
    return read_json(os.path.join(jordan_home(), "guard.json")) or {}


def guard_findings(command, cwd, config=None, scratch=None, env=None):
    """List of (class, detail) for a shell command; [] when nothing matched.

    Raises GuardParseError when the command cannot be parsed. The caller
    decides what that means: the hook denies, `jordan-ledger open` refuses.
    """
    config = config or {}
    cwd = os.path.realpath(cwd) if cwd else None
    root = workspace_root(cwd) if cwd else os.sep + "nonexistent"
    # The session scratchpad is where throwaway files are meant to go; deleting
    # there is not the accident this guard exists for.
    safe = [os.path.realpath(os.path.expanduser(p))
            for p in [scratch] + list(config.get("allow_delete_roots") or [])
            if isinstance(p, str) and os.path.isabs(os.path.expanduser(p))]
    out = []
    _scan(command, _Ctx(command, cwd, root, safe, config, os.environ if env is None else env), out)
    return out
