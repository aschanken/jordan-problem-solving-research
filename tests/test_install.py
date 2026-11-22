"""Tests for install.sh (plain-copy route) and the plugin manifests (RULINGS R9).

Every install runs against a temporary home; nothing here touches the real
~/.claude. Stdlib unittest, also collected by pytest:

    python3 -m pytest -q tests/test_install.py
"""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALL = os.path.join(REPO, "install.sh")
BEGIN = "<!-- jordan-kernel:begin -->"
END = "<!-- jordan-kernel:end -->"
AGENTS = ["jordan-builder.md", "jordan-reader.md", "jordan-refuter.md"]

USER_CLAUDE_MD = (
    "# My rules\r\n"          # a CRLF line: must survive byte for byte
    "\n"
    "- Prefer tabs.\n"
    "- Café — non-ASCII stays as it is.\n"
    "no trailing newline"
).encode("utf-8")

USER_SETTINGS = {
    "model": "opus",
    "permissions": {"allow": ["Bash(git status)"], "deny": []},
    "env": {"FOO": "bär"},
    "hooks": {
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": "/usr/local/bin/my-guard", "args": ["x"]}]}
        ],
        "Notification": [
            {"matcher": "", "hooks": [{"type": "command", "command": "/usr/local/bin/notify"}]}
        ],
    },
}


def run_install(home, *args):
    env = dict(os.environ, HOME=home)
    env.pop("JORDAN_HOME", None)
    return subprocess.run(["bash", INSTALL, "--home", home] + list(args),
                          capture_output=True, text=True, env=env, timeout=120)


def tree_hash(root, skip=("jordan-backups", "__pycache__")):
    """One hash over every path, link target, mode and content under root."""
    digest = hashlib.sha256()
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in skip)
        for name in sorted(files):
            full = os.path.join(base, name)
            digest.update(os.path.relpath(full, root).encode() + b"\0")
            if os.path.islink(full):
                digest.update(b"link:" + os.readlink(full).encode())
            else:
                digest.update(b"%o:" % (os.stat(full).st_mode & 0o777))
                with open(full, "rb") as handle:
                    digest.update(handle.read())
            digest.update(b"\0")
    return digest.hexdigest()


def files_under(root, skip=("jordan-backups", "__pycache__")):
    out = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip]
        out.extend(os.path.relpath(os.path.join(base, n), root) for n in files)
    return sorted(out)


def hook_commands(settings):
    return [h["command"] for groups in settings.get("hooks", {}).values()
            for g in groups for h in g.get("hooks", [])]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="jordan-install-test-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = os.path.realpath(os.path.join(self.tmp, "home"))
        os.makedirs(self.home)
        self.claude = os.path.join(self.home, ".claude")

    def path(self, *parts):
        return os.path.join(self.claude, *parts)

    def read(self, *parts):
        with open(self.path(*parts), "rb") as handle:
            return handle.read()

    def settings(self):
        return json.loads(self.read("settings.json").decode("utf-8"))

    def seed_user_files(self):
        os.makedirs(self.claude)
        with open(self.path("CLAUDE.md"), "wb") as handle:
            handle.write(USER_CLAUDE_MD)
        with open(self.path("settings.json"), "w", encoding="utf-8") as handle:
            json.dump(USER_SETTINGS, handle, indent=4)
        os.makedirs(self.path("agents"))
        with open(self.path("agents", "mine.md"), "w") as handle:
            handle.write("---\nname: mine\ndescription: mine\n---\nbody\n")
        os.makedirs(self.path("skills", "other"))
        with open(self.path("skills", "other", "SKILL.md"), "w") as handle:
            handle.write("---\nname: other\ndescription: other\n---\n")

    def install_ok(self, *args):
        result = run_install(self.home, *args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result


class FreshInstall(Base):
    def test_fresh_install_puts_every_part_in_place(self):
        result = self.install_ok()
        self.assertTrue(os.path.isfile(self.path("skills", "jordan", "SKILL.md")))
        self.assertTrue(os.path.isfile(self.path("skills", "jordan", "kernel.md")))
        self.assertTrue(os.path.isfile(self.path("skills", "jordan", "modules", "plan.md")))
        self.assertTrue(os.path.isfile(self.path("jordan", "hooks", "jordan_lib.py")))
        self.assertTrue(os.access(self.path("jordan", "bin", "jordan-ledger"), os.X_OK))
        self.assertEqual(sorted(os.listdir(self.path("agents"))), AGENTS)
        link = os.path.join(self.home, ".local", "bin", "jordan-ledger")
        self.assertTrue(os.path.islink(link))
        self.assertEqual(os.path.realpath(link), self.path("jordan", "bin", "jordan-ledger"))
        self.assertIn("Undo:", result.stdout)
        self.assertIn("--uninstall", result.stdout)

    def test_kernel_block_equals_the_kernel_source(self):
        self.install_ok()
        text = self.read("CLAUDE.md").decode("utf-8")
        with open(os.path.join(REPO, "skills", "jordan", "kernel.md"), encoding="utf-8") as handle:
            kernel = handle.read().strip("\n")
        self.assertEqual(text, "%s\n%s\n%s\n" % (BEGIN, kernel, END))

    def test_only_top_level_agents_are_copied(self):
        self.install_ok()
        for name in AGENTS:
            with open(os.path.join(REPO, "agents", name), "rb") as handle:
                self.assertEqual(self.read("agents", name), handle.read(), name)
        self.assertFalse(os.path.exists(self.path("agents", "templates")))
        self.assertFalse(os.path.exists(self.path("agents", "shared")))
        self.assertFalse(os.path.exists(self.path("agents", "jordan-core.md")))

    def test_hooks_come_from_hooks_json_without_session_start(self):
        self.install_ok()
        settings = self.settings()
        with open(os.path.join(REPO, "hooks", "hooks.json"), encoding="utf-8") as handle:
            source = json.load(handle)["hooks"]
        self.assertNotIn("SessionStart", settings["hooks"])
        self.assertEqual(sorted(settings["hooks"]), sorted(e for e in source if e != "SessionStart"))
        for event, groups in settings["hooks"].items():
            want = [(g.get("matcher", ""), h.get("timeout"), os.path.basename(h["command"].rstrip('"')))
                    for g in source[event] for h in g["hooks"]]
            got = [(g.get("matcher", ""), h.get("timeout"), os.path.basename(h["command"].rstrip('"')))
                   for g in groups for h in g["hooks"]]
            self.assertEqual(got, want, event)
        for command in hook_commands(settings):
            self.assertNotIn("CLAUDE_PLUGIN_ROOT", command)

    def test_hook_commands_point_at_existing_files(self):
        self.install_ok()
        commands = hook_commands(self.settings())
        self.assertTrue(commands)
        for command in commands:
            self.assertTrue(command.startswith('python3 "') and command.endswith('"'), command)
            script = command[len('python3 "'):-1]
            self.assertTrue(os.path.isabs(script), script)
            self.assertTrue(script.startswith(self.path("jordan", "hooks") + os.sep), script)
            self.assertTrue(os.path.isfile(script), script)

    def test_installed_hook_script_runs_and_writes_under_the_temp_home(self):
        self.install_ok()
        command = [c for c in hook_commands(self.settings()) if c.endswith('trace.py"')][0]
        work = os.path.join(self.tmp, "work")
        os.makedirs(work)
        payload = {"session_id": "s-install-test", "cwd": work, "hook_event_name": "PostToolUse",
                   "tool_name": "Bash", "tool_input": {"command": "true"}, "tool_response": {}}
        env = dict(os.environ, HOME=self.home)
        env.pop("JORDAN_HOME", None)
        result = subprocess.run(command, shell=True, input=json.dumps(payload), capture_output=True,
                                text=True, env=env, cwd=work, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(os.path.isfile(self.path("jordan", "trace", "s-install-test.jsonl")))

    def test_installed_ledger_status_runs(self):
        self.install_ok()
        work = os.path.join(self.tmp, "work")
        os.makedirs(work)
        env = dict(os.environ, HOME=self.home)
        for name in ("JORDAN_HOME", "CLAUDE_PLUGIN_ROOT"):
            env.pop(name, None)
        link = os.path.join(self.home, ".local", "bin", "jordan-ledger")
        status = subprocess.run([link, "status"], capture_output=True, text=True, env=env, cwd=work, timeout=60)
        self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
        self.assertNotIn("cannot find jordan_lib", status.stdout + status.stderr)
        opened = subprocess.run([link, "open", "--check", "true"], capture_output=True, text=True,
                                env=env, cwd=work, timeout=60)
        self.assertEqual(opened.returncode, 0, opened.stdout + opened.stderr)
        ledgers = os.listdir(self.path("jordan", "ledgers"))
        self.assertTrue(any(n.startswith("pending-") for n in ledgers), ledgers)


class ExistingContent(Base):
    def test_unrelated_bytes_and_keys_are_unchanged(self):
        self.seed_user_files()
        self.install_ok()
        text = self.read("CLAUDE.md")
        self.assertTrue(text.startswith(USER_CLAUDE_MD))
        tail = text[len(USER_CLAUDE_MD):].decode("utf-8")
        self.assertTrue(tail.startswith("\n\n" + BEGIN + "\n"), repr(tail[:60]))
        self.assertTrue(tail.endswith("\n" + END + "\n"))

        settings = self.settings()
        for key in ("model", "permissions", "env"):
            self.assertEqual(settings[key], USER_SETTINGS[key], key)
        self.assertEqual(list(settings)[:4], list(USER_SETTINGS)[:4])
        self.assertEqual(settings["hooks"]["Notification"], USER_SETTINGS["hooks"]["Notification"])
        bash = [g for g in settings["hooks"]["PreToolUse"] if g.get("matcher") == "Bash"]
        self.assertEqual(len(bash), 1)
        self.assertEqual(bash[0]["hooks"][0], USER_SETTINGS["hooks"]["PreToolUse"][0]["hooks"][0])
        self.assertTrue(bash[0]["hooks"][1]["command"].endswith('irreversible_guard.py"'))
        self.assertIn("bär", self.read("settings.json").decode("utf-8"))

        with open(self.path("agents", "mine.md")) as handle:
            self.assertIn("name: mine", handle.read())
        self.assertTrue(os.path.isfile(self.path("skills", "other", "SKILL.md")))

    def test_changed_files_are_backed_up_with_a_timestamp(self):
        self.seed_user_files()
        before_md, before_settings = self.read("CLAUDE.md"), self.read("settings.json")
        self.install_ok()
        stamps = os.listdir(self.path("jordan-backups"))
        self.assertEqual(len(stamps), 1)
        self.assertRegex(stamps[0], r"^\d{8}-\d{6}")
        self.assertEqual(self.read("jordan-backups", stamps[0], ".claude", "CLAUDE.md"), before_md)
        self.assertEqual(self.read("jordan-backups", stamps[0], ".claude", "settings.json"), before_settings)

    def test_existing_kernel_block_is_replaced_in_place(self):
        os.makedirs(self.claude)
        head, tail = b"# top\n\n", b"\n\n## after\nkeep me\n"
        with open(self.path("CLAUDE.md"), "wb") as handle:
            handle.write(head + (BEGIN + "\nold kernel\n" + END).encode() + tail)
        self.install_ok()
        text = self.read("CLAUDE.md")
        self.assertTrue(text.startswith(head + BEGIN.encode()))
        self.assertTrue(text.endswith(END.encode() + tail))
        self.assertNotIn(b"old kernel", text)
        self.assertIn(b"# JORDAN kernel v3", text)

    def test_stale_file_in_the_skill_directory_is_replaced(self):
        os.makedirs(self.path("skills", "jordan"))
        with open(self.path("skills", "jordan", "stale.md"), "w") as handle:
            handle.write("left over from an older version\n")
        self.install_ok()
        self.assertFalse(os.path.exists(self.path("skills", "jordan", "stale.md")))
        stamp = os.listdir(self.path("jordan-backups"))[0]
        self.assertTrue(os.path.isfile(self.path("jordan-backups", stamp, ".claude", "skills", "jordan", "stale.md")))

    def test_empty_settings_file_is_treated_as_empty_object(self):
        os.makedirs(self.claude)
        open(self.path("settings.json"), "w").close()
        self.install_ok()
        self.assertIn("Stop", self.settings()["hooks"])

    def test_warns_when_a_jordan_plugin_is_enabled_too(self):
        os.makedirs(self.claude)
        with open(self.path("settings.json"), "w") as handle:
            json.dump({"enabledPlugins": {"jordan@jordan": True}}, handle)
        result = self.install_ok()
        self.assertIn("one route per machine", result.stderr)


class Idempotence(Base):
    def test_second_run_changes_no_file(self):
        self.seed_user_files()
        self.install_ok()
        first = tree_hash(self.home, skip=())
        result = self.install_ok()
        self.assertEqual(tree_hash(self.home, skip=()), first)
        self.assertIn("Nothing changed", result.stdout)

    def test_second_run_after_hooks_have_run_changes_no_file(self):
        # Running a hook leaves __pycache__ and trace state behind; neither is a reason to reinstall.
        self.install_ok()
        subprocess.run(["python3", self.path("jordan", "hooks", "trace.py")], input="{}", text=True,
                       capture_output=True, env=dict(os.environ, HOME=self.home), timeout=60)
        first = tree_hash(self.home, skip=())
        result = self.install_ok()
        self.assertEqual(tree_hash(self.home, skip=()), first)
        self.assertIn("Nothing changed", result.stdout)

    def test_hooks_are_not_registered_twice(self):
        self.install_ok()
        self.install_ok()
        commands = hook_commands(self.settings())
        per_event = [(e, h["command"]) for e, gs in self.settings()["hooks"].items()
                     for g in gs for h in g["hooks"]]
        self.assertEqual(len(per_event), len(set(per_event)))
        self.assertEqual(len(commands), 6)


class DryRun(Base):
    def test_dry_run_changes_nothing_on_a_fresh_home(self):
        result = self.install_ok("--dry-run")
        self.assertEqual(files_under(self.home, skip=()), [])
        self.assertEqual(os.listdir(self.home), [])
        self.assertIn("would:", result.stdout)

    def test_dry_run_changes_nothing_over_existing_content(self):
        self.seed_user_files()
        before = tree_hash(self.home, skip=())
        self.install_ok("--dry-run")
        self.assertEqual(tree_hash(self.home, skip=()), before)

    def test_dry_run_uninstall_changes_nothing(self):
        self.install_ok()
        before = tree_hash(self.home, skip=())
        result = self.install_ok("--uninstall", "--dry-run")
        self.assertEqual(tree_hash(self.home, skip=()), before)
        self.assertIn("would:", result.stdout)


class Uninstall(Base):
    def test_uninstall_after_fresh_install_leaves_no_file(self):
        self.install_ok()
        self.install_ok("--uninstall")
        self.assertEqual(files_under(self.home), [])
        self.assertFalse(os.path.exists(self.path("jordan")))
        self.assertFalse(os.path.lexists(os.path.join(self.home, ".local", "bin", "jordan-ledger")))

    def test_uninstall_restores_the_files_it_touched_and_leaves_the_rest(self):
        self.seed_user_files()
        before_files = files_under(self.home)
        before_md = self.read("CLAUDE.md")
        self.install_ok()
        self.install_ok("--uninstall")
        self.assertEqual(self.read("CLAUDE.md"), before_md)
        self.assertEqual(self.settings(), USER_SETTINGS)
        self.assertEqual(files_under(self.home), before_files)

    def test_uninstall_keeps_text_the_user_added_after_the_block(self):
        self.seed_user_files()
        self.install_ok()
        with open(self.path("CLAUDE.md"), "ab") as handle:
            handle.write(b"\n## Added later\nkeep\n")
        self.install_ok("--uninstall")
        text = self.read("CLAUDE.md")
        self.assertNotIn(BEGIN.encode(), text)
        self.assertNotIn(END.encode(), text)
        self.assertTrue(text.startswith(USER_CLAUDE_MD))
        self.assertTrue(text.endswith(b"\n## Added later\nkeep\n"))

    def test_uninstall_keeps_session_state_and_hooks_added_later(self):
        self.install_ok()
        os.makedirs(self.path("jordan", "trace"))
        with open(self.path("jordan", "trace", "s1.jsonl"), "w") as handle:
            handle.write("{}\n")
        settings = self.settings()
        settings["hooks"]["Stop"].append({"hooks": [{"type": "command", "command": "/opt/mine"}]})
        settings["theme"] = "dark"
        with open(self.path("settings.json"), "w") as handle:
            json.dump(settings, handle)
        result = self.install_ok("--uninstall")
        self.assertEqual(self.settings(), {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "/opt/mine"}]}]},
                                           "theme": "dark"})
        self.assertTrue(os.path.isfile(self.path("jordan", "trace", "s1.jsonl")))
        self.assertFalse(os.path.exists(self.path("jordan", "hooks")))
        self.assertIn("left alone", result.stdout)

    def test_uninstall_on_a_home_without_jordan_changes_nothing(self):
        self.seed_user_files()
        before = tree_hash(self.home, skip=())
        result = self.install_ok("--uninstall")
        self.assertEqual(tree_hash(self.home, skip=()), before)
        self.assertIn("Nothing changed", result.stdout)

    def test_reinstall_after_uninstall_works(self):
        self.install_ok()
        first = tree_hash(self.home)
        self.install_ok("--uninstall")
        self.install_ok()
        self.assertEqual(tree_hash(self.home), first)


class RefusesWhatItCannotParse(Base):
    def assert_stops_untouched(self, name, content, *args):
        os.makedirs(self.claude, exist_ok=True)
        with open(self.path(name), "wb") as handle:
            handle.write(content)
        before = tree_hash(self.home, skip=())
        result = run_install(self.home, *args)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("stopped", result.stderr)
        self.assertIn(name, result.stderr)
        self.assertIn("Nothing was changed", result.stderr)
        self.assertEqual(tree_hash(self.home, skip=()), before)
        self.assertEqual(self.read(name), content)

    def test_unparseable_settings_stops_the_install(self):
        self.assert_stops_untouched("settings.json", b'{"model": "opus", // my comment\n "hooks": {}}\n')

    def test_truncated_settings_stops_the_install(self):
        self.assert_stops_untouched("settings.json", b'{"hooks": {"Stop": [')

    def test_settings_that_is_not_an_object_stops_the_install(self):
        self.assert_stops_untouched("settings.json", b'["a list"]\n')

    def test_hooks_of_the_wrong_shape_stop_the_install(self):
        self.assert_stops_untouched("settings.json", b'{"hooks": {"Stop": "run-this"}}\n')

    def test_unparseable_settings_stops_the_uninstall(self):
        self.install_ok()
        self.assert_stops_untouched("settings.json", b"{not json", "--uninstall")

    def test_begin_marker_without_end_stops_the_install(self):
        self.assert_stops_untouched("CLAUDE.md", ("# mine\n" + BEGIN + "\nhalf a block\n").encode())

    def test_unknown_option_is_a_usage_error(self):
        result = run_install(self.home, "--frobnicate")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(os.listdir(self.home), [])


class Manifests(unittest.TestCase):
    def load(self, name):
        with open(os.path.join(REPO, ".claude-plugin", name), encoding="utf-8") as handle:
            return json.load(handle)

    def test_plugin_manifest_names_the_plugin_jordan(self):
        self.assertEqual(self.load("plugin.json")["name"], "jordan")

    def test_plugin_manifest_lists_exactly_the_rendered_agents(self):
        listed = self.load("plugin.json")["agents"]
        self.assertEqual(sorted(listed), sorted("./agents/" + n for n in AGENTS))
        rendered = sorted(n for n in os.listdir(os.path.join(REPO, "agents")) if n.endswith(".md"))
        self.assertEqual(rendered, AGENTS, "a new rendered agent must be added to plugin.json")
        for entry in listed:
            self.assertTrue(os.path.isfile(os.path.join(REPO, entry)), entry)

    def test_marketplace_manifest_lists_the_plugin(self):
        market = self.load("marketplace.json")
        self.assertTrue(market["name"])
        self.assertTrue(market["owner"]["name"])
        entries = [p for p in market["plugins"] if p["name"] == "jordan"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"], "./")

    @unittest.skipUnless(shutil.which("claude"), "claude CLI not on PATH")
    def test_claude_plugin_validate_passes(self):
        config = tempfile.mkdtemp(prefix="jordan-validate-")
        self.addCleanup(shutil.rmtree, config, ignore_errors=True)
        env = dict(os.environ, CLAUDE_CONFIG_DIR=config)
        result = subprocess.run(["claude", "plugin", "validate", REPO, "--json"],
                                capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        report = json.loads(result.stdout)
        self.assertTrue(report["success"])
        agents = sorted(a if isinstance(a, str) else a.get("name", "") for a in report["provides"]["agents"])
        self.assertEqual(agents, ["jordan:jordan-builder", "jordan:jordan-reader", "jordan:jordan-refuter"])


if __name__ == "__main__":
    unittest.main()
