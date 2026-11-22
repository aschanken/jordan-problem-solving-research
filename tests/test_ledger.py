"""Tests for bin/jordan-ledger and the ledger half of hooks/jordan_lib.py.

Each test runs the CLI as a subprocess with a temporary JORDAN_HOME and a
temporary git repository, the way an agent's Bash tool would.

    python3 -m unittest tests.test_ledger -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = os.path.join(REPO, "bin", "jordan-ledger")
HOOKS = os.path.join(REPO, "hooks")
sys.path.insert(0, HOOKS)
import jordan_lib as lib  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="jordan-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = os.path.join(self.tmp, "jordan-home")
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ("CLAUDE_CODE_SESSION_ID", "CLAUDE_PLUGIN_ROOT", "JORDAN_DEBUG")}
        self.env.update({
            "JORDAN_HOME": self.home, "HOME": os.path.join(self.tmp, "home"),
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
        })
        os.makedirs(self.env["HOME"])

    def sh(self, cmd, cwd):
        return subprocess.run(cmd, shell=True, cwd=cwd, env=self.env, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def repo(self, files=None, name="repo", git=True):
        root = os.path.join(self.tmp, name)
        os.makedirs(root)
        for rel, text in (files or {"app.py": "x = 1\n", "tests/test_app.py": "assert True\n"}).items():
            path = os.path.join(root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fh:
                fh.write(text)
        if git:
            self.sh("git init -q . && git add -A && git commit -q -m base", root)
        return root

    def cli(self, *args, cwd, env=None):
        return subprocess.run([sys.executable, CLI, *args], cwd=cwd, env=env or self.env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def hook(self, name, payload, cwd=None, raw=None):
        data = raw if raw is not None else json.dumps(payload)
        return subprocess.run([sys.executable, os.path.join(HOOKS, name + ".py")], input=data,
                              cwd=cwd or self.tmp, env=self.env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def ledger_files(self):
        d = os.path.join(self.home, "ledgers")
        return sorted(os.listdir(d)) if os.path.isdir(d) else []

    def read(self, name):
        with open(os.path.join(self.home, "ledgers", name)) as fh:
            return json.load(fh)

    def claim(self, root, sid="S1", agent=None, command="jordan-ledger open --check x"):
        payload = {"session_id": sid, "cwd": root, "hook_event_name": "PostToolUse",
                   "tool_name": "Bash", "tool_input": {"command": command}, "tool_response": {"stdout": ""}}
        if agent:
            payload["agent_id"] = agent
        return self.hook("trace", payload)

    def open(self, root, check="true", *extra, sid="S1", agent=None):
        res = self.cli("open", "--check", check, *extra, cwd=root)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.claim(root, sid, agent)
        return res


class OpenTests(Base):
    def test_open_writes_pending_outside_workspace(self):
        root = self.repo()
        res = self.cli("open", "--check", "python3 -m pytest -q", cwd=root)
        self.assertEqual(res.returncode, 0, res.stderr)
        files = self.ledger_files()
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].startswith("pending-"))
        led = self.read(files[0])
        self.assertEqual(led["state"], "open")
        self.assertEqual(led["check"], "python3 -m pytest -q")
        self.assertEqual(led["timeout_s"], 120)
        self.assertEqual(led["root"], root)
        self.assertTrue(led["git"])
        self.assertRegex(led["baseline"], r"^[0-9a-f]{40}$")
        for glob in ("tests/**", "package.json", "Makefile", "**/*.spec.*"):
            self.assertIn(glob, led["protect"])
        # Nothing is written into the workspace (REDTEAM B2).
        self.assertEqual(self.sh("git status --porcelain", root).stdout, "")

    def test_open_from_subdirectory_records_git_toplevel(self):
        root = self.repo()
        self.cli("open", "--check", "true", cwd=os.path.join(root, "tests"))
        self.assertEqual(self.read(self.ledger_files()[0])["root"], root)

    def test_protect_flag_and_timeout_clamp(self):
        root = self.repo()
        res = self.cli("open", "--check", "true", "--protect", "schema/**", "--timeout", "9999", cwd=root)
        led = self.read(self.ledger_files()[0])
        self.assertIn("schema/**", led["protect"])
        self.assertEqual(led["timeout_s"], 540)
        self.assertIn("clamped", res.stdout)

    def test_non_git_workspace_claims_no_protection(self):
        root = self.repo(git=False)
        res = self.cli("open", "--check", "true", cwd=root)
        led = self.read(self.ledger_files()[0])
        self.assertFalse(led["git"])
        self.assertIsNone(led["baseline"])
        self.assertIn("no path protection", res.stdout)

    def test_open_replaces_and_says_so(self):
        root = self.repo()
        self.cli("open", "--check", "echo one", cwd=root)
        res = self.cli("open", "--check", "echo two", cwd=root)
        self.assertIn("replaced", res.stdout)
        self.assertEqual(len(self.ledger_files()), 1)
        self.assertEqual(self.read(self.ledger_files()[0])["check"], "echo two")

    def test_reopen_after_claim_replaces_owner_ledger(self):
        root = self.repo()
        self.open(root, "echo one")
        res = self.cli("open", "--check", "echo two", cwd=root)
        self.assertIn("another open ledger exists", res.stdout)
        self.claim(root)
        self.assertEqual(self.ledger_files(), ["S1.json"])
        self.assertEqual(self.read("S1.json")["check"], "echo two")

    def test_open_refuses_check_the_guard_would_stop(self):
        root = self.repo()
        for check in ("npm publish", "git push --force origin main", "rm -rf ~/build && make test",
                      "rm -rf $OUT/", "echo 'unterminated && rm -rf x"):
            res = self.cli("open", "--check", check, cwd=root)
            self.assertEqual(res.returncode, 2, check)
            self.assertIn("refused", res.stderr)
        self.assertEqual(self.ledger_files(), [])

    def test_open_accepts_in_workspace_clean_in_check(self):
        root = self.repo()
        res = self.cli("open", "--check", "rm -rf build/* && make test", cwd=root)
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_works_when_copied_to_installed_layout(self):
        # ~/.claude/jordan/bin + ~/.claude/jordan/hooks, reached through a symlink.
        inst = os.path.join(self.tmp, "inst")
        os.makedirs(os.path.join(inst, "bin"))
        os.makedirs(os.path.join(inst, "hooks"))
        shutil.copy(CLI, os.path.join(inst, "bin", "jordan-ledger"))
        shutil.copy(os.path.join(HOOKS, "jordan_lib.py"), os.path.join(inst, "hooks"))
        link = os.path.join(self.tmp, "localbin")
        os.makedirs(link)
        os.symlink(os.path.join(inst, "bin", "jordan-ledger"), os.path.join(link, "jordan-ledger"))
        root = self.repo()
        res = subprocess.run([os.path.join(link, "jordan-ledger"), "open", "--check", "true"],
                             cwd=root, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(len(self.ledger_files()), 1)


class ClaimTests(Base):
    def test_claim_by_session(self):
        root = self.repo()
        self.open(root)
        self.assertEqual(self.ledger_files(), ["S1.json"])
        led = self.read("S1.json")
        self.assertEqual((led["session_id"], led["agent_id"]), ("S1", None))

    def test_claim_by_agent(self):
        root = self.repo()
        self.open(root, agent="A7")
        self.assertEqual(self.ledger_files(), ["S1.A7.json"])
        self.assertEqual(self.read("S1.A7.json")["agent_id"], "A7")

    def test_event_outside_workspace_does_not_claim(self):
        root = self.repo()
        other = self.repo(name="other")
        self.cli("open", "--check", "true", cwd=root)
        self.claim(other, sid="S2")
        self.assertTrue(self.ledger_files()[0].startswith("pending-"))

    def test_event_from_subdirectory_claims(self):
        root = self.repo()
        self.cli("open", "--check", "true", cwd=root)
        self.claim(os.path.join(root, "tests"))
        self.assertEqual(self.ledger_files(), ["S1.json"])

    def age_pending(self, seconds):
        pending = os.path.join(self.home, "ledgers", self.ledger_files()[0])
        old = time.time() - seconds
        os.utime(pending, (old, old))

    def test_other_tool_call_claims_only_within_the_grace_window(self):
        # R14 / refutation R-4: an ordinary tool call claims only right after
        # the open (it was run through a wrapper); later it is someone else.
        root = self.repo()
        self.cli("open", "--check", "true", cwd=root)
        self.age_pending(60)
        self.claim(root, sid="S9", command="ls")
        self.assertTrue(self.ledger_files()[0].startswith("pending-"))
        self.cli("open", "--check", "true", cwd=root)
        self.claim(root, sid="S9", command="./scripts/start-task.sh")
        self.assertEqual(self.ledger_files(), ["S9.json"])

    def test_opener_claims_from_a_directory_above_the_workspace(self):
        # Refutation R-4: `cd r && jordan-ledger open ...` issued from the parent.
        root = self.repo()
        self.cli("open", "--check", "true", cwd=root)
        self.age_pending(120)
        self.claim(self.tmp, command="cd repo && jordan-ledger open --check true")
        self.assertEqual(self.ledger_files(), ["S1.json"])

    def test_opener_in_an_unrelated_directory_does_not_claim_unhinted(self):
        root = self.repo()
        other = self.repo(name="other")
        self.cli("open", "--check", "true", cwd=root)
        self.claim(other, sid="S2", command="jordan-ledger status")
        self.assertTrue(self.ledger_files()[0].startswith("pending-"))

    def test_hinted_ledger_is_claimed_by_its_session_from_any_cwd(self):
        root = self.repo()
        self.cli("open", "--check", "true", cwd=root, env=dict(self.env, CLAUDE_CODE_SESSION_ID="S1"))
        self.claim(os.path.join(self.tmp, "home"), command="cd ../repo; jordan-ledger open --check true")
        self.assertEqual(self.ledger_files(), ["S1.json"])

    def stop(self, root, sid, agent=None):
        payload = {"session_id": sid, "cwd": root, "stop_hook_active": False,
                   "hook_event_name": "SubagentStop" if agent else "Stop"}
        if agent:
            payload["agent_id"] = agent
        return self.hook("done_gate", payload)

    def test_subagent_stop_never_takes_the_parents_pending_ledger(self):
        # Refutation R-3: a subagent shares the session id, so the hint cannot
        # tell it from its parent. It used to be blocked by the parent's check
        # while the parent then stopped ungated.
        root = self.repo()
        self.cli("open", "--check", "echo x; false", cwd=root, env=dict(self.env, CLAUDE_CODE_SESSION_ID="S1"))
        res = self.stop(root, "S1", agent="sub1")
        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))
        self.assertTrue(self.ledger_files()[0].startswith("pending-"))
        res = self.stop(root, "S1")
        self.assertEqual(res.returncode, 2)
        self.assertEqual(self.ledger_files(), ["S1.json"])

    def test_stop_never_claims_an_unhinted_pending_ledger(self):
        # Refutation R-4: any session stopping in the repo used to take it and
        # be blocked by a check it never recorded.
        root = self.repo()
        counter = os.path.join(self.tmp, "runs")
        self.cli("open", "--check", "echo ran >> %s; false" % counter, cwd=root)
        for age in (0, 60, 899):
            self.age_pending(age)
            res = self.stop(root, "B")
            self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""), age)
        self.assertTrue(self.ledger_files()[0].startswith("pending-"))
        self.assertFalse(os.path.exists(counter))

    def test_stop_of_another_session_does_not_claim_a_hinted_ledger(self):
        root = self.repo()
        self.cli("open", "--check", "false", cwd=root, env=dict(self.env, CLAUDE_CODE_SESSION_ID="S1"))
        self.assertEqual(self.stop(root, "S2").returncode, 0)
        self.assertTrue(self.ledger_files()[0].startswith("pending-"))

    def test_stale_pending_is_never_claimed(self):
        root = self.repo()
        self.cli("open", "--check", "true", cwd=root)
        self.age_pending(3600)
        self.claim(root)
        self.assertTrue(self.ledger_files()[0].startswith("pending-"))

    def test_session_hint_from_env_restricts_claim(self):
        root = self.repo()
        env = dict(self.env, CLAUDE_CODE_SESSION_ID="S1")
        self.cli("open", "--check", "true", cwd=root, env=env)
        self.claim(root, sid="OTHER")
        self.assertTrue(self.ledger_files()[0].startswith("pending-"))
        self.claim(root, sid="S1")
        self.assertEqual(self.ledger_files(), ["S1.json"])

    def test_unsafe_session_id_is_refused(self):
        root = self.repo()
        self.cli("open", "--check", "true", cwd=root)
        res = self.claim(root, sid="../../evil")
        self.assertEqual(res.returncode, 0)
        self.assertTrue(self.ledger_files()[0].startswith("pending-"))
        self.assertFalse(os.path.exists(os.path.join(self.home, "evil.json")))


class CommandTests(Base):
    def test_status_with_no_ledger(self):
        root = self.repo()
        res = self.cli("status", cwd=root)
        self.assertEqual(res.returncode, 0)
        self.assertIn("no ledger", res.stdout)

    def test_commands_without_open_ledger_fail_plainly(self):
        root = self.repo()
        for args in (("close",), ("mark", "unverified", "--reason", "r"), ("authorise", "x", "--reason", "r")):
            res = self.cli(*args, cwd=root)
            self.assertEqual(res.returncode, 1, args)
            self.assertIn("no open ledger", res.stderr)

    def test_status_close(self):
        root = self.repo()
        self.open(root, "echo hi")
        res = self.cli("status", cwd=root)
        self.assertIn("ledger: open (session S1)", res.stdout)
        self.assertIn("check: echo hi", res.stdout)
        self.assertEqual(self.cli("close", cwd=root).returncode, 0)
        led = self.read("S1.json")
        self.assertEqual((led["state"], led["closed_by"]), ("closed", "close"))
        self.assertIn("ledger: closed", self.cli("status", cwd=root).stdout)

    def test_mark_records_kind_and_reason(self):
        for kind in ("unverified", "impossible"):
            root = self.repo(name="r-" + kind)
            self.open(root, sid="S-" + kind)
            res = self.cli("mark", kind, "--reason", "no test runner here", cwd=root)
            self.assertEqual(res.returncode, 0, res.stderr)
            led = self.read("S-%s.json" % kind)
            self.assertEqual(led["state"], "closed")
            self.assertEqual(led["mark"]["kind"], kind)
            self.assertEqual(led["mark"]["reason"], "no test runner here")

    def test_mark_needs_a_reason(self):
        root = self.repo()
        self.open(root)
        self.assertNotEqual(self.cli("mark", "unverified", cwd=root).returncode, 0)
        self.assertNotEqual(self.cli("mark", "unverified", "--reason", " ", cwd=root).returncode, 0)
        self.assertNotEqual(self.cli("mark", "done", "--reason", "x", cwd=root).returncode, 0)
        self.assertEqual(self.read("S1.json")["state"], "open")

    def test_authorise_stores_root_relative_path(self):
        root = self.repo()
        self.open(root)
        res = self.cli("authorise", "test_app.py", "--reason", "spec changed", cwd=os.path.join(root, "tests"))
        self.assertEqual(res.returncode, 0, res.stderr)
        entry = self.read("S1.json")["authorised"][0]
        self.assertEqual((entry["path"], entry["reason"]), ("tests/test_app.py", "spec changed"))

    def test_open_none_records_an_unverified_ledger(self):
        # RULINGS R13: the decision not to verify is on file, and nothing is gated.
        root = self.repo()
        res = self.cli("open", "--none", "--reason", "docs-only change", cwd=root)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("unverified", res.stdout)
        self.claim(root, command="jordan-ledger open --none --reason x")
        led = self.read("S1.json")
        self.assertEqual((led["state"], led["check"], led["closed_by"]), ("closed", None, "none"))
        self.assertEqual((led["mark"]["kind"], led["mark"]["reason"]), ("unverified", "docs-only change"))
        res = self.hook("done_gate", {"session_id": "S1", "cwd": root, "hook_event_name": "Stop",
                                      "stop_hook_active": False})
        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))
        self.assertIn("marked unverified: docs-only change", self.cli("status", cwd=root).stdout)

    def test_open_needs_exactly_one_of_check_or_none(self):
        root = self.repo()
        for args in (("open",), ("open", "--none"), ("open", "--none", "--reason", " "),
                     ("open", "--check", "true", "--none", "--reason", "r"),
                     ("open", "--check", "true", "--reason", "r")):
            self.assertEqual(self.cli(*args, cwd=root).returncode, 2, args)
        self.assertEqual(self.ledger_files(), [])

    def test_open_refuses_when_jordan_home_is_inside_the_workspace(self):
        # Refutation R-9: a dotfiles repo at ~ with the default JORDAN_HOME.
        root = self.repo()
        env = dict(self.env, JORDAN_HOME=os.path.join(root, ".claude", "jordan"))
        res = self.cli("open", "--check", "true", cwd=root, env=env)
        self.assertEqual(res.returncode, 2)
        self.assertIn("inside this workspace", res.stderr)
        self.assertFalse(os.path.exists(os.path.join(root, ".claude")))
        # Ignored by git, it cannot disturb the tree, so it is accepted.
        with open(os.path.join(root, ".git", "info", "exclude"), "a") as fh:
            fh.write(".claude/\n")
        self.assertEqual(self.cli("open", "--check", "true", cwd=root, env=env).returncode, 0)
        self.assertEqual(self.sh("git status --porcelain", root).stdout, "")

    def test_authorise_refuses_a_path_outside_the_workspace(self):
        # Refutation N-7.
        root = self.repo()
        self.open(root)
        for target in ("/etc/passwd", ".", "../other/file.py"):
            res = self.cli("authorise", target, "--reason", "r", cwd=root)
            self.assertEqual(res.returncode, 1, target)
            self.assertIn("not a file inside the workspace", res.stderr)
        self.assertEqual(self.read("S1.json")["authorised"], [])
        self.assertEqual(self.cli("authorise", "tests/*.py", "--reason", "r", cwd=root).returncode, 0)

    def test_second_session_note_does_not_claim_replacement(self):
        # Refutation R-10: the old note said the other ledger would be replaced.
        root = self.repo()
        self.open(root, "echo A", sid="A")
        res = self.cli("open", "--check", "echo B", cwd=root)
        self.assertIn("stays open", res.stdout)
        self.assertNotIn("is replaced when", res.stdout)
        self.claim(root, sid="B")
        self.assertEqual(self.ledger_files(), ["A.json", "B.json"])

    def test_acts_on_pending_before_claim(self):
        root = self.repo()
        self.cli("open", "--check", "true", cwd=root)
        self.assertIn("pending claim", self.cli("status", cwd=root).stdout)
        self.assertEqual(self.cli("close", cwd=root).returncode, 0)

    def test_two_open_for_one_root_acts_on_most_recent_and_says_which(self):
        root = self.repo()
        self.open(root, "echo first", agent="A1")
        time.sleep(0.05)
        self.open(root, "echo second", agent="A2")
        res = self.cli("mark", "unverified", "--reason", "r", cwd=root)
        self.assertIn("2 open ledgers", res.stdout)
        self.assertIn("agent A2", res.stdout)
        self.assertEqual(self.read("S1.A2.json")["state"], "closed")
        self.assertEqual(self.read("S1.A1.json")["state"], "open")


class LibTests(unittest.TestCase):
    def test_default_globs(self):
        protected = ["tests/test_a.py", "test/x.js", "src/__tests__/a.js", "src/test_util.py",
                     "pkg/util_test.go", "web/a.test.ts", "web/a.spec.tsx", ".github/workflows/ci.yml",
                     "conftest.py", "sub/conftest.py", "pytest.ini", "tox.ini", "Makefile",
                     "package.json", "packages/a/package.json", "noxfile.py", "test_root.py"]
        free = ["src/app.py", "README.md", "src/testing.py", "latest/x.py", "contest.py",
                "package-lock.json", "src/attest.rs", "docs/tests.md"]
        for rel in protected:
            self.assertIsNotNone(lib.match_glob(rel, lib.DEFAULT_PROTECT), rel)
        for rel in free:
            self.assertIsNone(lib.match_glob(rel, lib.DEFAULT_PROTECT), rel)

    def test_safe_id(self):
        self.assertEqual(lib.safe_id("a1b2-c3_d"), "a1b2-c3_d")
        for bad in ("", "a/b", "..", "a.b", None, 5, "x" * 200):
            self.assertIsNone(lib.safe_id(bad))

    def test_write_json_is_atomic_and_leaves_no_temp_file(self):
        d = tempfile.mkdtemp(prefix="jordan-test-")
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        path = os.path.join(d, "sub", "x.json")
        lib.write_json(path, {"a": 1})
        lib.write_json(path, {"a": 2})
        self.assertEqual(lib.read_json(path), {"a": 2})
        self.assertEqual(os.listdir(os.path.dirname(path)), ["x.json"])
        self.assertIsNone(lib.read_json(os.path.join(d, "missing.json")))


if __name__ == "__main__":
    unittest.main()
