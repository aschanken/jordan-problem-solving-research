"""Tests for the JORDAN v3 hooks, each driven as a subprocess with crafted stdin.

Scenario ids in comments (B3, M1, ...) refer to docs/v3/REDTEAM.md.

    python3 -m unittest tests.test_hooks -v
"""
import json
import os
import shutil
import subprocess
import sys
import time
import unittest

try:  # `python3 -m unittest tests.test_hooks` and pytest import this differently
    from tests import test_ledger as tl
except ImportError:  # pragma: no cover
    import test_ledger as tl

HOOKS = tl.HOOKS
ALL_HOOKS = ["done_gate", "protected_paths", "irreversible_guard", "trace", "session_start"]


class HookBase(tl.Base):
    def stop(self, root, sid="S1", agent=None, **extra):
        payload = {"session_id": sid, "cwd": root, "stop_hook_active": False, "background_tasks": [],
                   "hook_event_name": "SubagentStop" if agent else "Stop", "permission_mode": "default"}
        if agent:
            payload["agent_id"] = agent
        payload.update(extra)
        return self.hook("done_gate", payload)

    def counter_check(self, verdict="true"):
        """A check that records each run outside the workspace."""
        self.counter = os.path.join(self.tmp, "runs.txt")
        return "echo run >> %s; %s" % (self.counter, verdict)

    def runs(self):
        try:
            with open(self.counter) as fh:
                return len(fh.readlines())
        except OSError:
            return 0

    def write(self, root, rel, text):
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def assertSilent(self, res, msg=None):
        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""), msg)


class RobustnessTests(HookBase):
    def test_no_ledger_every_hook_exits_zero_silently(self):
        root = self.repo()
        payloads = {
            "done_gate": {"session_id": "S1", "cwd": root, "hook_event_name": "Stop",
                          "stop_hook_active": False, "background_tasks": []},
            "protected_paths": {"session_id": "S1", "cwd": root, "tool_name": "Edit",
                                "tool_input": {"file_path": os.path.join(root, "tests/test_app.py")}},
            "irreversible_guard": {"session_id": "S1", "cwd": root, "tool_name": "Bash",
                                   "permission_mode": "default", "tool_input": {"command": "ls -la"}},
            "trace": {"session_id": "S1", "cwd": root, "hook_event_name": "PostToolUse",
                      "tool_name": "Read", "tool_input": {"file_path": "x"}},
            "session_start": {"session_id": "S1", "cwd": root, "hook_event_name": "SessionStart",
                              "source": "startup"},
        }
        for name in ALL_HOOKS:
            if name == "session_start":
                continue  # prints the kernel by design; covered in SessionStartTests
            self.assertSilent(self.hook(name, payloads[name]), name)
        self.assertEqual(self.ledger_files(), [])

    def test_every_hook_survives_empty_or_malformed_stdin(self):
        inputs = ["", "   ", "not json", "{", "[]", "null", "42", '"str"', "{}",
                  '{"session_id": 5, "cwd": 7, "tool_input": "x", "background_tasks": "y"}',
                  '{"session_id": "S1", "tool_input": {"command": 3, "file_path": []}}',
                  '{"tool_name": "Bash", "tool_input": null}']
        for name in ALL_HOOKS:
            for raw in inputs:
                res = self.hook(name, None, raw=raw)
                self.assertEqual(res.returncode, 0, "%s on %r: %s" % (name, raw, res.stderr))
                if res.stdout:  # only the single JSON object the event expects
                    json.loads(res.stdout)
                    self.assertEqual(name, "session_start")

    def test_hooks_json_registers_each_script_once_in_plugin_form(self):
        with open(os.path.join(HOOKS, "hooks.json")) as fh:
            reg = json.load(fh)["hooks"]
        seen = {}
        for event, groups in reg.items():
            for group in groups:
                for h in group["hooks"]:
                    self.assertEqual(h["type"], "command")
                    self.assertIsInstance(h["timeout"], int)
                    prefix = 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/'
                    self.assertTrue(h["command"].startswith(prefix), h["command"])
                    script = h["command"][len(prefix):].rstrip('"')
                    self.assertTrue(os.path.isfile(os.path.join(HOOKS, script)), script)
                    seen.setdefault(script, []).append((event, group.get("matcher"), h["timeout"]))
        self.assertEqual(seen["done_gate.py"], [("Stop", None, 600), ("SubagentStop", None, 600)])
        self.assertEqual(seen["protected_paths.py"][0][:2], ("PreToolUse", "Edit|Write"))
        self.assertEqual(seen["irreversible_guard.py"][0][:2], ("PreToolUse", "Bash"))
        self.assertEqual([e for e, _, _ in seen["trace.py"]], ["PostToolUse", "PostToolUseFailure"])
        self.assertEqual([e for e, _, _ in seen["session_start.py"]], ["SessionStart"])
        self.assertGreater(600, tl.lib.MAX_TIMEOUT_S)


class DoneGateTests(HookBase):
    def test_green_closes_the_ledger(self):
        root = self.repo()
        self.open(root, self.counter_check("true"))
        self.assertSilent(self.stop(root))
        led = self.read("S1.json")
        self.assertEqual((led["state"], led["passes"], led["closed_by"]), ("closed", True, "gate"))
        self.assertEqual(led["last_run"]["verdict"], "green")
        self.assertEqual(self.runs(), 1)

    def test_closed_ledger_is_not_run_again(self):
        # Two Stop events were seen in one clean run (B3): the suite runs once.
        root = self.repo()
        self.open(root, self.counter_check("true"))
        self.stop(root)
        self.assertSilent(self.stop(root))
        self.assertEqual(self.runs(), 1)

    def test_red_blocks_with_exit_2_and_names_three_exits(self):
        root = self.repo()
        self.open(root, self.counter_check("echo 'AssertionError: 2 != 3'; exit 3"))
        res = self.stop(root)
        self.assertEqual(res.returncode, 2)
        self.assertEqual(res.stdout, "")
        self.assertIn("AssertionError: 2 != 3", res.stderr)
        self.assertIn("exit 3", res.stderr)
        self.assertIn("Fix the work", res.stderr)
        self.assertIn("jordan-ledger mark unverified", res.stderr)
        self.assertIn("jordan-ledger mark impossible", res.stderr)
        led = self.read("S1.json")
        self.assertEqual((led["state"], led["passes"], led["blocks"]), ("open", False, 1))

    def test_red_output_is_cut_to_the_last_40_lines(self):
        root = self.repo()
        self.open(root, "seq 1 100 | sed 's/^/line-/'; exit 1")
        res = self.stop(root)
        self.assertIn("line-61\n", res.stderr)
        self.assertNotIn("line-60\n", res.stderr)
        self.assertIn("line-100", res.stderr)

    def test_stop_hook_active_does_not_block(self):
        # B3 / m2: one block per stop chain.
        root = self.repo()
        self.open(root, self.counter_check("false"))
        self.assertEqual(self.stop(root).returncode, 2)
        self.assertSilent(self.stop(root, stop_hook_active=True))
        self.assertEqual(self.runs(), 1)
        self.assertEqual(self.read("S1.json")["blocks"], 1)

    def test_block_cap_of_two_per_ledger(self):
        root = self.repo()
        self.open(root, self.counter_check("false"))
        self.assertEqual(self.stop(root).returncode, 2)
        self.assertEqual(self.stop(root).returncode, 2)
        res = self.stop(root)
        self.assertEqual(res.returncode, 0)
        self.assertEqual(res.stderr, "")
        self.assertIn("not blocked again", json.loads(res.stdout)["systemMessage"])
        self.assertEqual(self.runs(), 2)
        self.assertEqual(self.read("S1.json")["blocks"], 2)

    def test_red_then_fixed_goes_green(self):
        root = self.repo()
        self.open(root, "test -f fixed.txt")
        self.assertEqual(self.stop(root).returncode, 2)
        self.write(root, "fixed.txt", "ok\n")
        self.assertSilent(self.stop(root))
        self.assertEqual(self.read("S1.json")["passes"], True)

    def test_unchanged_tree_after_green_run_does_not_rerun_the_check(self):
        # Green check, but a protected file was changed: blocked, ledger stays
        # open with a green run recorded. Authorising does not change the tree,
        # so the next stop passes on the recorded run. The counter proves it.
        root = self.repo()
        self.open(root, self.counter_check("true"))
        self.write(root, "tests/test_app.py", "assert 1\n")
        self.assertEqual(self.stop(root).returncode, 2)
        self.assertEqual(self.runs(), 1)
        self.assertEqual(self.stop(root).returncode, 2)  # still unauthorised, still no re-run
        self.assertEqual(self.runs(), 1)
        self.cli("authorise", "tests/test_app.py", "--reason", "r", cwd=root)
        self.assertEqual(self.stop(root).returncode, 0)
        self.assertEqual(self.runs(), 1)
        self.assertEqual(self.read("S1.json")["state"], "closed")

    def test_changed_tree_after_green_run_reruns_the_check(self):
        root = self.repo()
        self.open(root, self.counter_check("true"))
        self.write(root, "tests/test_app.py", "assert 1\n")
        self.assertEqual(self.stop(root).returncode, 2)
        self.write(root, "app.py", "x = 2\n")
        self.assertEqual(self.stop(root).returncode, 2)
        self.assertEqual(self.runs(), 2)

    def test_timeout_is_an_explicit_verdict_not_a_silent_pass(self):
        # M2.
        root = self.repo()
        self.open(root, self.counter_check("sleep 30"), "--timeout", "1")
        started = time.time()
        res = self.stop(root)
        self.assertLess(time.time() - started, 15)
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        self.assertIn("timed out after 1 s", out["systemMessage"])
        self.assertIn("unverified", out["hookSpecificOutput"]["additionalContext"])
        led = self.read("S1.json")
        self.assertEqual((led["passes"], led["state"]), ("timeout", "open"))
        self.assertEqual(led["last_run"]["verdict"], "timeout")
        # Same tree: not run again just to time out again.
        self.assertSilent(self.stop(root))
        self.assertEqual(self.runs(), 1)

    def test_mark_unverified_and_impossible_let_the_stop_through(self):
        for kind in ("unverified", "impossible"):
            root = self.repo(name="r-" + kind)
            sid = "S-" + kind
            self.open(root, self.counter_check("false"), sid=sid)
            self.assertEqual(self.stop(root, sid=sid).returncode, 2)
            before = self.runs()
            self.cli("mark", kind, "--reason", "why", cwd=root)
            self.assertSilent(self.stop(root, sid=sid))
            self.assertEqual(self.runs(), before)
            os.unlink(self.counter)

    def test_background_tasks_skip(self):
        root = self.repo()
        self.open(root, self.counter_check("false"))
        self.assertSilent(self.stop(root, background_tasks=[{"id": "b1", "status": "running"}]))
        self.assertEqual(self.runs(), 0)

    def test_ledger_of_another_session_is_ignored(self):
        root = self.repo()
        self.open(root, self.counter_check("false"), sid="S1")
        self.assertSilent(self.stop(root, sid="S2"))
        self.assertEqual(self.runs(), 0)

    def test_ledger_of_another_agent_is_ignored(self):
        # B3: a reader subagent, or the lead, must not be gated by a builder's check.
        root = self.repo()
        self.open(root, self.counter_check("false"), agent="A1")
        self.assertSilent(self.stop(root))                 # main session, no agent_id
        self.assertSilent(self.stop(root, agent="A2"))     # a different subagent
        self.assertEqual(self.runs(), 0)
        self.assertEqual(self.stop(root, agent="A1").returncode, 2)

    def test_main_session_ledger_does_not_gate_a_subagent(self):
        root = self.repo()
        self.open(root, self.counter_check("false"))
        self.assertSilent(self.stop(root, agent="A1"))
        self.assertEqual(self.runs(), 0)

    def test_stop_claims_a_pending_ledger_when_no_tool_call_followed(self):
        root = self.repo()
        self.cli("open", "--check", self.counter_check("false"), cwd=root)
        self.assertEqual(self.stop(root).returncode, 2)
        self.assertEqual(self.ledger_files(), ["S1.json"])

    def test_check_runs_in_workspace_root_even_from_a_subdirectory(self):
        # B2(c): `cd sub/` must not lose the ledger.
        root = self.repo()
        self.open(root, "test -f app.py && test -d tests")
        self.assertSilent(self.stop(os.path.join(root, "tests")))
        self.assertEqual(self.read("S1.json")["passes"], True)

    def test_internal_error_allows_and_advises(self):
        root = self.repo()
        self.open(root, "true")
        shutil.rmtree(root)
        res = self.stop(self.tmp)
        self.assertEqual(res.returncode, 0)
        self.assertIn("internal error", res.stderr)
        self.assertIn("NOT verified", json.loads(res.stdout)["systemMessage"])


class ProtectedPathTests(HookBase):
    def pre(self, root, rel, tool="Edit", sid="S1", agent=None):
        payload = {"session_id": sid, "cwd": root, "hook_event_name": "PreToolUse", "tool_name": tool,
                   "tool_input": {"file_path": os.path.join(root, rel)}}
        if agent:
            payload["agent_id"] = agent
        return self.hook("protected_paths", payload)

    def assertDenied(self, res):
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)["hookSpecificOutput"]
        self.assertEqual((out["hookEventName"], out["permissionDecision"]), ("PreToolUse", "deny"))
        return out["permissionDecisionReason"]

    def test_shell_style_change_to_a_test_is_caught_at_stop(self):
        # M1(a): sed, mv, a python one-liner never pass through Edit.
        root = self.repo()
        self.open(root, "true")
        self.sh("sed -i 's/assert True/assert 1/' tests/test_app.py", root)
        res = self.stop(root)
        self.assertEqual(res.returncode, 2)
        self.assertIn("tests/test_app.py", res.stderr)
        self.assertIn("jordan-ledger authorise", res.stderr)
        self.assertIn("jordan-ledger mark impossible", res.stderr)
        self.assertEqual(self.read("S1.json")["state"], "open")

    def test_deleted_and_committed_changes_are_caught(self):
        root = self.repo()
        self.open(root, "true")
        self.sh("git rm -q tests/test_app.py && git commit -q -m 'drop test'", root)
        res = self.stop(root)
        self.assertEqual(res.returncode, 2)
        self.assertIn("tests/test_app.py", res.stderr)

    def test_test_file_created_during_the_task_is_free(self):
        root = self.repo()
        self.open(root, "true")
        self.write(root, "tests/test_new.py", "assert True\n")
        self.assertSilent(self.pre(root, "tests/test_new.py", tool="Write"))
        self.write(root, "tests/test_new.py", "assert 1 == 1\n")
        self.assertSilent(self.stop(root))
        self.assertEqual(self.read("S1.json")["passes"], True)

    def test_authorise_lets_a_protected_change_through_and_is_printed(self):
        root = self.repo()
        self.open(root, "true")
        self.cli("authorise", "tests/test_app.py", "--reason", "behaviour is meant to change", cwd=root)
        self.assertSilent(self.pre(root, "tests/test_app.py"))
        self.write(root, "tests/test_app.py", "assert 2\n")
        res = self.stop(root)
        self.assertEqual(res.returncode, 0)
        msg = json.loads(res.stdout)["systemMessage"]
        self.assertIn("tests/test_app.py", msg)
        self.assertIn("behaviour is meant to change", msg)
        self.assertEqual(self.read("S1.json")["state"], "closed")

    def test_package_json_script_tampering_is_caught(self):
        # M1(c): `"test": "true"` passes the check; the diff does not let it through.
        root = self.repo({"package.json": '{"scripts": {"test": "node test.js"}}\n', "index.js": "\n"})
        self.open(root, "grep -q '\"test\"' package.json")
        self.write(root, "package.json", '{"scripts": {"test": "true"}}\n')
        res = self.stop(root)
        self.assertEqual(res.returncode, 2)
        self.assertIn("package.json", res.stderr)
        self.assertIn("The check itself passed", res.stderr)

    def test_protected_file_dirty_at_open_is_judged_from_its_state_at_open(self):
        root = self.repo()
        self.write(root, "tests/test_app.py", "assert 'edited before the task'\n")
        self.write(root, "tests/test_untracked.py", "assert True\n")
        self.open(root, "true")
        # Unchanged since open: not tampering, even though git shows a diff.
        self.assertEqual(tl.lib.protected_changes(self.read("S1.json")), ([], []))
        # An untracked test that existed at open is protected like any other.
        self.write(root, "tests/test_untracked.py", "assert 1\n")
        res = self.stop(root)
        self.assertEqual(res.returncode, 2)
        self.assertIn("tests/test_untracked.py", res.stderr)
        self.assertNotIn("tests/test_app.py", res.stderr)

    def test_non_git_workspace_claims_no_protection_and_says_so_once(self):
        # M1(e).
        root = self.repo(git=False)
        self.open(root, "test -f done.txt")
        self.write(root, "tests/test_app.py", "changed\n")
        self.assertSilent(self.pre(root, "tests/test_app.py"))
        res = self.stop(root)
        self.assertEqual(res.returncode, 2)  # red check, not protection
        self.assertNotIn("protected files", res.stderr)
        self.write(root, "done.txt", "x\n")
        res = self.stop(root)
        self.assertEqual(res.returncode, 0)
        self.assertIn("no path protection is claimed", json.loads(res.stdout)["systemMessage"])

    def test_early_notice_denies_edit_of_existing_test(self):
        root = self.repo({"app.py": "\n", "tests/test_app.py": "\n", "package.json": "{}\n", "Makefile": "\n"})
        self.open(root, "true")
        for rel in ("tests/test_app.py", "package.json", "Makefile"):
            reason = self.assertDenied(self.pre(root, rel))
            self.assertIn(rel, reason)
            self.assertIn("jordan-ledger authorise", reason)
            self.assertIn("jordan-ledger mark impossible", reason)
        self.assertSilent(self.pre(root, "app.py"))
        self.assertSilent(self.pre(root, "../elsewhere/tests/test_x.py"))

    def test_early_notice_only_for_the_ledger_owner(self):
        root = self.repo()
        self.open(root, "true", agent="A1")
        self.assertSilent(self.pre(root, "tests/test_app.py"))
        self.assertSilent(self.pre(root, "tests/test_app.py", sid="S2"))
        self.assertDenied(self.pre(root, "tests/test_app.py", agent="A1"))


class GuardTests(HookBase):
    def guard(self, command, root, mode="default", **extra):
        payload = {"session_id": "S1", "cwd": root, "hook_event_name": "PreToolUse", "tool_name": "Bash",
                   "permission_mode": mode, "tool_input": {"command": command}}
        payload.update(extra)
        res = self.hook("irreversible_guard", payload)
        self.assertEqual((res.returncode, res.stderr), (0, ""), command)
        if not res.stdout:
            return None, ""
        out = json.loads(res.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        return out["permissionDecision"], out["permissionDecisionReason"]

    def setUp(self):
        super().setUp()
        self.root = self.repo()
        self.env.pop("UNSET", None)

    def test_passes(self):
        os.makedirs(os.path.join(self.root, "dist"))
        for cmd in [
            "rm -rf dist/*", "rm -rf dist", "rm -rf ./build node_modules", "rm -rf *",
            "rm -rf '%s/dist'" % self.root, "cd dist && rm -rf ./*", "rm -f /etc/hosts.bak",
            "rm notes.txt", "rm -rf dist 2>/dev/null || true",
            "git push", "git push origin main", "git push -u origin feature/x",
            "git commit -m 'never push --force here'", "echo 'npm publish'",
            "npm publish --dry-run", "cargo publish --dry-run", "npm run release",
            "gh release list", "twine check dist/*", "grep -r 'rm -rf /' docs",
            "cat > notes.md <<'EOF'\ndon't rm -rf ~/x or git push --force\nEOF",
        ]:
            self.assertEqual(self.guard(cmd, self.root)[0], None, cmd)

    def test_stops_and_asks_in_default_mode(self):
        for cmd, word in [
            ("rm -rf ~/x", "outside"), ("rm -rf $UNSET/", "cannot be resolved"), ("rm -rf /", "outside"),
            ("rm -rf ~", "outside"), ("rm -rf ..", "outside"), ("rm -rf ../*", "outside"),
            ("rm -rf .", "outside"), ("rm -fr /tmp/some-dir", "outside"), ("rm -r -f /var/x", "outside"),
            ("rm --recursive /opt/x", "outside"), ("rm -rf \"$UNSET\"/*", "cannot be resolved"),
            ("rm -rf $(cat list.txt)", "cannot be resolved"), ("rm -rf `cat list.txt`", "cannot be resolved"),
            ("cd /tmp && rm -rf build", "outside"), ("cd $UNSET && rm -rf build", "cannot be resolved"),
            ("sudo rm -rf /var/lib/x", "outside"), ("make build; rm -rf ~/x", "outside"),
            ("bash -c 'rm -rf ~/x'", "outside"), ("FOO=1 rm -rf ~/x", "outside"),
            ("D=/; rm -rf $D", "cannot be resolved"),
            ("git push --force", "force-push"), ("git push -f origin main", "force-push"),
            ("git push --force-with-lease origin x", "force-push"), ("git push origin +main", "force-push"),
            ("git -C sub push origin +HEAD:main", "force-push"), ("git push -uf origin x", "force-push"),
            ("npm publish", "publish"), ("npm publish --access public", "publish"),
            ("cd pkg && pnpm publish", "publish"), ("twine upload dist/*", "publish"),
            ("python3 -m twine upload dist/*", "publish"), ("cargo publish", "publish"),
            ("gh release create v1.0.0 --notes x", "publish"),
            ("bash <<EOF\nrm -rf ~/x\nEOF", "outside"),
        ]:
            decision, reason = self.guard(cmd, self.root)
            self.assertEqual(decision, "ask", cmd)
            self.assertIn(word, reason, cmd)
            self.assertIn("decision request", reason)

    def test_denies_in_bypass_mode(self):
        for cmd in ("rm -rf ~/x", "git push --force", "npm publish"):
            self.assertEqual(self.guard(cmd, self.root, mode="bypassPermissions")[0], "deny", cmd)
            self.assertEqual(self.guard(cmd, self.root, mode="acceptEdits")[0], "ask", cmd)
        self.assertEqual(self.guard("rm -rf dist/*", self.root, mode="bypassPermissions")[0], None)

    def test_missing_permission_mode_asks(self):
        res = self.hook("irreversible_guard", {"cwd": self.root, "tool_input": {"command": "npm publish"}})
        self.assertEqual(json.loads(res.stdout)["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_prefilter_matched_parse_failure_denies(self):
        for mode in ("default", "bypassPermissions"):
            decision, reason = self.guard("echo \"unterminated; rm -rf /", self.root, mode=mode)
            self.assertEqual(decision, "deny")
            self.assertIn("could not be parsed", reason)

    def test_unparseable_command_without_prefilter_match_passes(self):
        self.assertEqual(self.guard("echo \"unterminated", self.root)[0], None)

    def test_set_variable_is_resolved_and_judged_by_location(self):
        self.env["OUT"] = os.path.join(self.root, "out")
        self.assertEqual(self.guard("rm -rf $OUT", self.root)[0], None)
        self.assertEqual(self.guard("rm -rf \"${OUT}/cache\"", self.root)[0], None)
        self.env["OUT"] = "/srv/data"
        self.assertEqual(self.guard("rm -rf $OUT", self.root)[0], "ask")

    def test_session_scratchpad_is_not_outside(self):
        scratch = os.path.join(self.tmp, "scratch")
        os.makedirs(scratch)
        self.assertEqual(self.guard("rm -rf %s/work" % scratch, self.root, scratchpad_dir=scratch)[0], None)
        self.assertEqual(self.guard("rm -rf %s" % scratch, self.root, scratchpad_dir=scratch)[0], "ask")

    def test_non_git_workspace_is_cwd(self):
        plain = self.repo(name="plain", git=False)
        self.assertEqual(self.guard("rm -rf build", plain)[0], None)
        self.assertEqual(self.guard("rm -rf ../repo", plain)[0], "ask")

    def test_opt_in_classes_are_off_by_default_and_on_through_guard_json(self):
        self.sh("git checkout -q -B main", self.root)
        self.assertEqual(self.guard("git push origin main", self.root)[0], None)
        self.assertEqual(self.guard("cat .env", self.root)[0], None)
        os.makedirs(self.home, exist_ok=True)
        with open(os.path.join(self.home, "guard.json"), "w") as fh:
            json.dump({"default_branch_push": True, "credential_reads": True}, fh)
        self.assertEqual(self.guard("git push origin main", self.root)[0], "ask")
        self.assertEqual(self.guard("git push", self.root)[0], "ask")
        self.assertEqual(self.guard("git push origin feature", self.root)[0], None)
        self.assertEqual(self.guard("cat .env", self.root)[0], "ask")
        self.assertEqual(self.guard("cat .env.example", self.root)[0], None)
        self.assertEqual(self.guard("ls -la", self.root)[0], None)

    def test_unrelated_commands_pass_fast_without_loading_the_library(self):
        # The no-match path must not import jordan_lib: hide it and run anyway.
        alone = os.path.join(self.tmp, "alone")
        os.makedirs(alone)
        shutil.copy(os.path.join(HOOKS, "irreversible_guard.py"), alone)
        payload = json.dumps({"cwd": self.root, "tool_input": {"command": "ls -la && pytest -q"}})
        started = time.time()
        for _ in range(5):
            res = subprocess.run([sys.executable, os.path.join(alone, "irreversible_guard.py")],
                                 input=payload, env=self.env, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True)
            self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))
        self.assertLess((time.time() - started) / 5, 1.0)

    def test_prefilter_is_defined_identically_in_hook_and_library(self):
        sys.path.insert(0, HOOKS)
        import irreversible_guard
        self.assertEqual(irreversible_guard.PREFILTER.pattern, tl.lib.GUARD_PREFILTER.pattern)


class TraceTests(HookBase):
    def post(self, **over):
        payload = {"session_id": "S1", "cwd": self.tmp, "hook_event_name": "PostToolUse",
                   "tool_name": "Bash", "tool_input": {"command": "ls"}, "tool_response": {"stdout": "a\nb\n"}}
        payload.update(over)
        return self.hook("trace", payload)

    def lines(self, sid="S1"):
        with open(os.path.join(self.home, "trace", sid + ".jsonl")) as fh:
            return [json.loads(line) for line in fh]

    def test_writes_one_line_with_the_ruled_fields(self):
        self.assertSilent(self.post())
        rows = self.lines()
        self.assertEqual(len(rows), 1)
        self.assertEqual(sorted(rows[0]), ["agent_id", "bytes", "input", "ok", "session_id", "tool", "ts"])
        self.assertEqual((rows[0]["tool"], rows[0]["ok"], rows[0]["input"], rows[0]["agent_id"]),
                         ("Bash", True, "ls", None))
        self.assertGreater(rows[0]["bytes"], 0)

    def test_failure_event_and_agent_id(self):
        self.post(hook_event_name="PostToolUseFailure", agent_id="A1", error="boom", tool_response=None)
        self.post()
        rows = self.lines()
        self.assertEqual(len(rows), 2)
        self.assertEqual((rows[0]["ok"], rows[0]["agent_id"]), (False, "A1"))

    def test_never_more_than_200_characters_of_input(self):
        # m4: Write contents and long commands must not land in the trace.
        secret = "TOKEN=" + "s3cr3t" * 2000
        self.post(tool_input={"command": "x" * 150 + secret})
        self.post(tool_name="Write", tool_input={"file_path": "/a/b.py", "content": secret})
        path = os.path.join(self.home, "trace", "S1.jsonl")
        with open(path) as fh:
            raw = fh.read().splitlines()
        self.assertEqual(len(raw), 2)
        for line in raw:
            self.assertLessEqual(len(json.loads(line)["input"]), 200)
            self.assertLess(len(line), 600)
            self.assertNotIn("s3cr3t" * 40, line)

    def test_trace_is_outside_the_workspace_and_keyed_by_session(self):
        root = self.repo()
        self.post(cwd=root, session_id="S2")
        self.assertEqual(os.listdir(os.path.join(self.home, "trace")), ["S2.jsonl"])
        self.assertEqual(self.sh("git status --porcelain", root).stdout, "")

    def test_unsafe_session_id_writes_nothing(self):
        self.assertSilent(self.post(session_id="../x"))
        self.assertFalse(os.path.isdir(os.path.join(self.home, "trace")))


class SessionStartTests(HookBase):
    KERNEL = "# JORDAN kernel v3\n\n1. Fixture rule.\n"

    def setUp(self):
        super().setUp()
        # The hook reads ../skills/jordan/kernel.md relative to itself, so it is
        # run from a copy with a fixture kernel beside it.
        self.plugin = os.path.join(self.tmp, "plugin")
        os.makedirs(os.path.join(self.plugin, "hooks"))
        shutil.copy(os.path.join(HOOKS, "session_start.py"), os.path.join(self.plugin, "hooks"))
        self.cwd = os.path.join(self.tmp, "proj")
        os.makedirs(self.cwd)

    def kernel(self, modules=("plan", "verify")):
        d = os.path.join(self.plugin, "skills", "jordan")
        os.makedirs(os.path.join(d, "modules"), exist_ok=True)
        with open(os.path.join(d, "kernel.md"), "w") as fh:
            fh.write(self.KERNEL)
        for m in modules:
            with open(os.path.join(d, "modules", m + ".md"), "w") as fh:
                fh.write("x\n")

    def start(self, source="startup"):
        payload = {"session_id": "S1", "cwd": self.cwd, "hook_event_name": "SessionStart", "source": source}
        return subprocess.run([sys.executable, os.path.join(self.plugin, "hooks", "session_start.py")],
                              input=json.dumps(payload), env=self.env, cwd=self.tmp,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_missing_kernel_is_silent(self):
        self.assertSilent(self.start())

    def test_injects_kernel_once_with_module_line(self):
        self.kernel()
        res = self.start()
        self.assertEqual((res.returncode, res.stderr), (0, ""))
        out = json.loads(res.stdout)  # exactly one JSON object on stdout
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertEqual(ctx.count("# JORDAN kernel v3"), 1)
        self.assertTrue(ctx.startswith(self.KERNEL.strip()))
        self.assertIn("plan, verify", ctx.splitlines()[-1])
        self.assertLessEqual(len(ctx), 10000)

    def test_reinjects_after_compaction(self):
        self.kernel()
        self.assertIn("JORDAN kernel", self.start("compact").stdout)

    def test_silent_when_marker_is_in_any_of_three_claude_md_locations(self):
        # M6: the marker was looked for in one file only.
        self.kernel()
        places = [os.path.join(self.env["HOME"], ".claude", "CLAUDE.md"),
                  os.path.join(self.cwd, "CLAUDE.md"),
                  os.path.join(self.cwd, ".claude", "CLAUDE.md")]
        for place in places:
            os.makedirs(os.path.dirname(place), exist_ok=True)
            with open(place, "w") as fh:
                fh.write("# mine\n\n<!-- jordan-kernel:begin -->\nrules\n<!-- jordan-kernel:end -->\n")
            self.assertSilent(self.start(), place)
            os.unlink(place)
            self.assertNotEqual(self.start().stdout, "", place)

    def test_claude_md_without_marker_does_not_silence(self):
        self.kernel()
        with open(os.path.join(self.cwd, "CLAUDE.md"), "w") as fh:
            fh.write("# project notes, no kernel\n")
        self.assertIn("JORDAN kernel", self.start().stdout)

    def test_marker_constant_matches_library(self):
        sys.path.insert(0, HOOKS)
        import session_start
        self.assertEqual(session_start.MARKER, tl.lib.KERNEL_MARKER)

    def test_repo_kernel_fits_the_injection_cap(self):
        path = os.path.join(os.path.dirname(HOOKS), "skills", "jordan", "kernel.md")
        if not os.path.isfile(path):
            self.skipTest("kernel.md not written yet")
        self.assertLess(os.path.getsize(path), 9000)


if __name__ == "__main__":
    unittest.main()
