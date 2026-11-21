#!/usr/bin/env bash
# install.sh — plain-copy install of JORDAN V3 into a Claude Code home
# (docs/v3/RULINGS.md R9; full description in docs/v3/install.md).
#
#   ./install.sh [--home <dir>] [--dry-run] [--uninstall]
#
#   --home <dir>   install under <dir>/.claude and <dir>/.local/bin
#                  (default: $HOME)
#   --dry-run      print what would change; change nothing
#   --uninstall    remove what an install added; leave everything else
#
# What it does, under <home>:
#   .claude/skills/jordan/       copy of skills/jordan/ (replaced as a whole)
#   .claude/jordan/hooks, bin    copies of hooks/ and bin/ (replaced as a whole)
#   .claude/agents/<name>.md     the rendered agents (top-level agents/*.md)
#   .claude/settings.json        hooks from hooks/hooks.json merged in,
#                                deduplicated by command; SessionStart skipped
#   .claude/CLAUDE.md            kernel block between the jordan-kernel markers;
#                                no other byte of the file is changed
#   .local/bin/jordan-ledger     symlink to .claude/jordan/bin/jordan-ledger
#   .claude/jordan/install.json  record of what was added, read by --uninstall
#
# Every existing file or directory that is about to change is first copied to
# <home>/.claude/jordan-backups/<YYYYmmdd-HHMMSS>/<same relative path>.
# A second run over the same home changes nothing and says so.
# A settings.json or CLAUDE.md that cannot be parsed stops the run before
# anything is written.
#
# Exit: 0 done (or nothing to do), 1 stopped without changing anything,
# 2 usage error. Needs bash and python3 (stdlib only).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo "install.sh: python3 is required and was not found on PATH" >&2
  exit 1
fi

JORDAN_REPO="$REPO_ROOT" exec python3 - "$@" <<'PY'
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time

REPO = os.environ["JORDAN_REPO"]
PLUGIN_ROOT_VAR = "${CLAUDE_PLUGIN_ROOT}"
SKIP_EVENTS = ("SessionStart",)  # the CLAUDE.md block replaces it (R9)
SCHEMA = 1


class Stop(Exception):
    """A reason to stop before changing anything."""


def load_renderer():
    path = os.path.join(REPO, "tools", "render-claude-md.py")
    spec = importlib.util.spec_from_file_location("jordan_render_claude_md", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------- file helpers

def read_bytes(path):
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except FileNotFoundError:
        return None


def write_atomic(path, data):
    """Write bytes through a temp file. A symlinked target keeps its link."""
    path = os.path.realpath(path)
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".jordan-install-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.chmod(tmp, (os.stat(path).st_mode & 0o777) if os.path.exists(path) else 0o644)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def skip_name(name):
    return name == "__pycache__" or name.endswith(".pyc")


def tree(path):
    """{relative path: (sha256, executable)} for a file tree, caches ignored."""
    out = {}
    if not os.path.isdir(path):
        return out
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if not skip_name(d))
        for name in sorted(files):
            if skip_name(name):
                continue
            full = os.path.join(root, name)
            with open(full, "rb") as handle:
                digest = hashlib.sha256(handle.read()).hexdigest()
            out[os.path.relpath(full, path)] = (digest, bool(os.stat(full).st_mode & 0o100))
    return out


class Run:
    def __init__(self, home, dry):
        self.home = home
        self.dry = dry
        self.changes = 0
        self.backup_root = None

    def say(self, text):
        self.changes += 1
        print("%s%s" % ("would: " if self.dry else "", text))

    def backup(self, path):
        if not os.path.lexists(path):
            return
        if self.backup_root is None:
            base = os.path.join(self.home, ".claude", "jordan-backups", time.strftime("%Y%m%d-%H%M%S"))
            root, n = base, 1
            while os.path.lexists(root):
                root, n = "%s-%d" % (base, n), n + 1
            self.backup_root = root
        dest = os.path.join(self.backup_root, os.path.relpath(path, self.home))
        print("  %s %s -> %s" % ("would back up" if self.dry else "backed up", path, dest))
        if self.dry:
            return
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.copytree(path, dest, symlinks=True)
        else:
            shutil.copy2(path, dest, follow_symlinks=False)

    def remove(self, path):
        if self.dry:
            return
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        elif os.path.lexists(path):
            os.unlink(path)

    # -- steps shared by install

    def replace_dir(self, src, dest, executable=False):
        if os.path.isdir(dest) and not os.path.islink(dest) and tree(src) == tree(dest):
            return
        self.say("copy %s -> %s" % (src, dest))
        self.backup(dest)
        if self.dry:
            return
        self.remove(dest)
        shutil.copytree(src, dest, ignore=lambda _d, names: [n for n in names if skip_name(n)])
        if executable:
            for name in os.listdir(dest):
                full = os.path.join(dest, name)
                if os.path.isfile(full):
                    os.chmod(full, 0o755)

    def copy_file(self, src, dest):
        if os.path.isfile(dest) and not os.path.islink(dest) and read_bytes(src) == read_bytes(dest):
            return
        self.say("copy %s -> %s" % (src, dest))
        self.backup(dest)
        if self.dry:
            return
        self.remove(dest)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)

    def write(self, path, data, what):
        self.say("%s %s" % (what, path))
        self.backup(path)
        if not self.dry:
            write_atomic(path, data)


# ------------------------------------------------------------------- settings

def load_settings(path):
    """Return (raw bytes or None, parsed dict). Stop on anything unparseable."""
    raw = read_bytes(path)
    if raw is None:
        return None, {}
    advice = "Nothing was changed. Fix or move that file, then run again."
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as err:
        raise Stop("%s is not UTF-8 (%s). %s" % (path, err, advice))
    if not text.strip():
        return raw, {}
    try:
        data = json.loads(text)
    except ValueError as err:
        raise Stop("%s is not valid JSON (%s). %s" % (path, err, advice))
    if not isinstance(data, dict):
        raise Stop("%s does not hold a JSON object. %s" % (path, advice))
    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        raise Stop('"hooks" in %s is not an object. %s' % (path, advice))
    for event, groups in hooks.items():
        ok = isinstance(groups, list) and all(
            isinstance(g, dict) and isinstance(g.get("hooks", []), list) for g in groups)
        if not ok:
            raise Stop('"hooks.%s" in %s does not have the shape Claude Code documents '
                       "(a list of {matcher, hooks: [...]}). %s" % (event, path, advice))
    return raw, data


def wanted_hooks(installed):
    """[(event, matcher, hook)] from hooks/hooks.json with the plugin prefix rewritten."""
    path = os.path.join(REPO, "hooks", "hooks.json")
    with open(path, encoding="utf-8") as handle:
        source = json.load(handle)
    out = []
    for event, groups in source["hooks"].items():
        if event in SKIP_EVENTS:
            continue
        for group in groups:
            for hook in group["hooks"]:
                hook = dict(hook)
                if PLUGIN_ROOT_VAR not in hook.get("command", ""):
                    raise Stop("%s: a %s hook has no %s prefix to rewrite: %r"
                               % (path, event, PLUGIN_ROOT_VAR, hook.get("command")))
                hook["command"] = hook["command"].replace(PLUGIN_ROOT_VAR, installed)
                out.append((event, group.get("matcher", ""), hook))
    return out


def merge_hooks(data, wanted):
    data = copy.deepcopy(data)
    for event, matcher, hook in wanted:
        groups = data.setdefault("hooks", {}).setdefault(event, [])
        same = [g for g in groups if g.get("matcher", "") == matcher]
        if any(isinstance(h, dict) and h.get("command") == hook["command"]
               for g in same for h in g.get("hooks", [])):
            continue
        if same:
            same[0].setdefault("hooks", []).append(hook)
        else:
            group = {"matcher": matcher} if matcher else {}
            group["hooks"] = [hook]
            groups.append(group)
    return data


def unmerge_hooks(data, commands):
    data = copy.deepcopy(data)
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return data
    touched = False
    for event in list(hooks):
        groups, hit = [], False
        for group in hooks[event]:
            kept = [h for h in group.get("hooks", [])
                    if not (isinstance(h, dict) and h.get("command") in commands)]
            if len(kept) != len(group.get("hooks", [])):
                hit = True
                if not kept:
                    continue
                group["hooks"] = kept
            groups.append(group)
        if hit:
            touched = True
            if groups:
                hooks[event] = groups
            else:
                del hooks[event]
    if touched and not hooks:
        del data["hooks"]
    return data


def dump_settings(data):
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def plugin_also_installed(claude_dir, settings):
    found = set()
    try:
        with open(os.path.join(claude_dir, "plugins", "installed_plugins.json"), encoding="utf-8") as handle:
            plugins = json.load(handle).get("plugins", {})
        found.update(k for k in plugins if k.split("@")[0] == "jordan")
    except (OSError, ValueError, AttributeError):
        pass
    enabled = settings.get("enabledPlugins")
    if isinstance(enabled, dict):
        found.update(k for k, v in enabled.items() if k.split("@")[0] == "jordan" and v)
    return sorted(found)


# ------------------------------------------------------------------ CLAUDE.md

def load_claude_md(path, renderer):
    """Return (raw or None, text, span). Stop on malformed markers."""
    raw = read_bytes(path)
    text = "" if raw is None else raw.decode("utf-8", "surrogateescape")
    try:
        span = renderer.find_block(text)
    except renderer.BlockError as err:
        raise Stop("%s: %s. Nothing was changed. Fix the markers by hand, then run again." % (path, err))
    return raw, text, span


def encode(text):
    return text.encode("utf-8", "surrogateescape")


# -------------------------------------------------------------------- install

def paths(home):
    claude = os.path.join(home, ".claude")
    jordan = os.path.join(claude, "jordan")
    return {
        "claude": claude,
        "jordan": jordan,
        "skill": os.path.join(claude, "skills", "jordan"),
        "hooks": os.path.join(jordan, "hooks"),
        "bin": os.path.join(jordan, "bin"),
        "agents": os.path.join(claude, "agents"),
        "settings": os.path.join(claude, "settings.json"),
        "claude_md": os.path.join(claude, "CLAUDE.md"),
        "manifest": os.path.join(jordan, "install.json"),
        "link": os.path.join(home, ".local", "bin", "jordan-ledger"),
        "ledger": os.path.join(jordan, "bin", "jordan-ledger"),
    }


def load_manifest(path):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def agent_sources():
    directory = os.path.join(REPO, "agents")
    return sorted(os.path.join(directory, n) for n in os.listdir(directory)
                  if n.endswith(".md") and os.path.isfile(os.path.join(directory, n)))


def install(run):
    p = paths(run.home)
    renderer = load_renderer()

    # Read and validate everything before the first write.
    for needed in ("skills/jordan/kernel.md", "skills/jordan/SKILL.md", "hooks/hooks.json",
                   "hooks/jordan_lib.py", "bin/jordan-ledger"):
        if not os.path.isfile(os.path.join(REPO, needed)):
            raise Stop("%s is missing from %s; run install.sh from a complete checkout." % (needed, REPO))
    agents = agent_sources()
    if not agents:
        raise Stop("no rendered agents in %s/agents; run tools/build-agents.py first." % REPO)
    kernel = renderer.kernel_text(os.path.join(REPO, "skills", "jordan", "kernel.md"))
    if renderer.BEGIN in kernel or renderer.END in kernel:
        raise Stop("skills/jordan/kernel.md must not contain the kernel markers.")
    settings_raw, settings = load_settings(p["settings"])
    wanted = wanted_hooks(p["jordan"])
    merged = merge_hooks(settings, wanted)
    md_raw, md_text, md_span = load_claude_md(p["claude_md"], renderer)
    md_new = renderer.render(md_text, kernel)
    old_manifest = load_manifest(p["manifest"])

    run.replace_dir(os.path.join(REPO, "skills", "jordan"), p["skill"])
    run.replace_dir(os.path.join(REPO, "hooks"), p["hooks"])
    run.replace_dir(os.path.join(REPO, "bin"), p["bin"], executable=True)
    for src in agents:
        run.copy_file(src, os.path.join(p["agents"], os.path.basename(src)))

    if merged != settings:
        run.write(p["settings"], dump_settings(merged),
                  "create" if settings_raw is None else "merge JORDAN hooks into")

    md_info = old_manifest.get("claude_md")
    if md_new != md_text:
        verb = "create" if md_raw is None else "append kernel block to" if md_span is None else "replace kernel block in"
        run.write(p["claude_md"], encode(md_new), verb)
    if md_span is None:
        gap = md_new[len(md_text):md_new.index(renderer.BEGIN, len(md_text))]
        md_info = {"created": md_raw is None, "appended": True, "gap": gap}
    elif not isinstance(md_info, dict):
        md_info = {"created": False, "appended": False, "gap": ""}

    if not (os.path.islink(p["link"]) and os.readlink(p["link"]) == p["ledger"]):
        run.say("link %s -> %s" % (p["link"], p["ledger"]))
        run.backup(p["link"])
        if not run.dry:
            run.remove(p["link"])
            os.makedirs(os.path.dirname(p["link"]), exist_ok=True)
            os.symlink(p["ledger"], p["link"])

    old_settings = old_manifest.get("settings") if isinstance(old_manifest.get("settings"), dict) else None
    manifest = {
        "schema": SCHEMA,
        "agents": [os.path.basename(a) for a in agents],
        "hook_commands": sorted({h["command"] for _e, _m, h in wanted}),
        "settings": old_settings or {"created": settings_raw is None},
        "claude_md": md_info,
        "link": p["link"],
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if read_bytes(p["manifest"]) != manifest_bytes:
        run.say("record the install in %s" % p["manifest"])
        if not run.dry:
            write_atomic(p["manifest"], manifest_bytes)

    print()
    if run.changes == 0:
        print("JORDAN is already installed in %s and up to date. Nothing changed." % p["claude"])
    elif run.dry:
        print("Dry run: %d change(s) listed above; nothing was written." % run.changes)
    else:
        print("JORDAN installed in %s (%d change(s) above)." % (p["claude"], run.changes))
        print("  kernel:  %s (between the jordan-kernel markers)" % p["claude_md"])
        print("  hooks:   %d registered in %s (session-start is not registered: the" % (len(wanted), p["settings"]))
        print("           CLAUDE.md block carries the kernel on this route)")
        print("  skill:   %s" % p["skill"])
        print("  agents:  %s" % ", ".join(os.path.splitext(n)[0] for n in manifest["agents"]))
        print("  ledger:  %s" % p["link"])
        if run.backup_root:
            print("  backups: %s" % run.backup_root)
    home_note = "" if run.home == os.path.realpath(os.path.expanduser("~")) else " --home %s" % run.home
    if run.changes and not run.dry:
        print("Undo: %s/install.sh --uninstall%s" % (REPO, home_note))
    link_dir = os.path.dirname(p["link"])
    on_path = any(d and os.path.realpath(d) == os.path.realpath(link_dir)
                  for d in os.environ.get("PATH", "").split(os.pathsep))
    if not on_path:
        print("Note: %s is not on PATH. Add it, or agents cannot run `jordan-ledger`:" % link_dir)
        print('  export PATH="%s:$PATH"' % link_dir)
    both = plugin_also_installed(p["claude"], merged)
    if both:
        print("Warning: a jordan plugin is also installed (%s). Use one route per machine: with"
              % ", ".join(both), file=sys.stderr)
        print("  both, every hook runs twice. Remove one: `claude plugin uninstall jordan` or "
              "`install.sh --uninstall`.", file=sys.stderr)
    return 0


# ------------------------------------------------------------------ uninstall

def uninstall(run):
    p = paths(run.home)
    renderer = load_renderer()
    manifest = load_manifest(p["manifest"])

    settings_raw, settings = load_settings(p["settings"])
    commands = set(manifest.get("hook_commands") or [])
    commands.update(h["command"] for _e, _m, h in wanted_hooks(p["jordan"]))
    stripped = unmerge_hooks(settings, commands)
    md_raw, md_text, md_span = load_claude_md(p["claude_md"], renderer)

    if settings_raw is not None and stripped != settings:
        created = isinstance(manifest.get("settings"), dict) and manifest["settings"].get("created")
        if created and not stripped:
            run.say("remove %s (install created it and nothing else is in it)" % p["settings"])
            run.backup(p["settings"])
            run.remove(p["settings"])
        else:
            run.write(p["settings"], dump_settings(stripped), "remove JORDAN hooks from")

    if md_span is not None:
        info = manifest.get("claude_md") if isinstance(manifest.get("claude_md"), dict) else {}
        start, end = md_span
        gap = info.get("gap") or ""
        if info.get("appended") and md_text[end:] == "\n" and md_text[:start].endswith(gap):
            new = md_text[:start - len(gap)] if gap else md_text[:start]
        else:
            new = md_text[:start] + md_text[end + 1 if md_text[end:end + 1] == "\n" else end:]
        if info.get("created") and not new.strip():
            run.say("remove %s (install created it and nothing else is in it)" % p["claude_md"])
            run.backup(p["claude_md"])
            run.remove(p["claude_md"])
        else:
            run.write(p["claude_md"], encode(new), "remove kernel block from")

    names = set(manifest.get("agents") or []) | {os.path.basename(a) for a in agent_sources()}
    for name in sorted(names):
        dest = os.path.join(p["agents"], os.path.basename(name))
        if os.path.lexists(dest):
            run.say("remove %s" % dest)
            run.remove(dest)
    if os.path.islink(p["link"]) and os.readlink(p["link"]) == p["ledger"]:
        run.say("remove link %s" % p["link"])
        run.remove(p["link"])
    elif os.path.lexists(p["link"]):
        print("left alone: %s is not the link this installer makes" % p["link"])
    for key in ("skill", "hooks", "bin", "manifest"):
        if os.path.lexists(p[key]):
            run.say("remove %s" % p[key])
            run.remove(p[key])
    if os.path.isdir(p["jordan"]):
        left = sorted(os.listdir(p["jordan"]))
        if run.dry:
            left = [n for n in left if n not in ("hooks", "bin", "install.json")]
        if not left:
            run.say("remove empty %s" % p["jordan"])
            if not run.dry:
                os.rmdir(p["jordan"])
        else:
            print("left alone: %s still holds session state (%s); delete it by hand if unwanted"
                  % (p["jordan"], ", ".join(left)))

    print()
    if run.changes == 0:
        print("No JORDAN plain-copy install found under %s. Nothing changed." % p["claude"])
    elif run.dry:
        print("Dry run: %d change(s) listed above; nothing was removed." % run.changes)
    else:
        print("JORDAN removed from %s (%d change(s) above)." % (p["claude"], run.changes))
        if run.backup_root:
            print("  settings.json and CLAUDE.md as they were before this run: %s" % run.backup_root)
    older = os.path.join(p["claude"], "jordan-backups")
    if os.path.isdir(older):
        print("  backups are kept in %s; delete them when you no longer need them" % older)
    return 0


def main(argv):
    parser = argparse.ArgumentParser(prog="install.sh", description="Plain-copy install of JORDAN V3.")
    parser.add_argument("--home", default=os.path.expanduser("~"),
                        help="install under <dir>/.claude and <dir>/.local/bin (default: $HOME)")
    parser.add_argument("--dry-run", action="store_true", help="print what would change; change nothing")
    parser.add_argument("--uninstall", action="store_true", help="remove what an install added")
    args = parser.parse_args(argv)

    home = os.path.realpath(os.path.expanduser(args.home))
    if not os.path.isdir(home):
        print("install.sh: --home %s is not a directory" % home, file=sys.stderr)
        return 2
    if any(c in home for c in '"$`\\\n'):
        print("install.sh: %s contains a character (one of \" $ ` \\) that cannot be written "
              "safely into a hook command; choose another home." % home, file=sys.stderr)
        return 1
    run = Run(home, args.dry_run)
    try:
        return uninstall(run) if args.uninstall else install(run)
    except Stop as stop:
        print("install.sh: stopped: %s" % stop, file=sys.stderr)
        return 1


sys.exit(main(sys.argv[1:]))
PY
