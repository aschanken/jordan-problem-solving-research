"""Size caps and consistency checks for the kernel, modules, SKILL.md and CLAUDE.md.

The kernel is sent on every step and modules on every trigger, so their size is
a running cost. The caps are the ones set in docs/v3/RULINGS.md (R2, R10); this
file is what enforces them. Runs under unittest or pytest, stdlib only.
"""
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(ROOT, "skills", "jordan")
KERNEL = os.path.join(SKILL_DIR, "kernel.md")
SKILL = os.path.join(SKILL_DIR, "SKILL.md")
MODULES_DIR = os.path.join(SKILL_DIR, "modules")
CLAUDE_MD = os.path.join(ROOT, "CLAUDE.md")
RENDER = os.path.join(ROOT, "tools", "render-claude-md.py")

KERNEL_CAP = 2800
MODULE_CAP = 2500
SKILL_CAP = 3000
CLAUDE_MD_CAP = 3400
EXPECTED_MODULES = {"plan", "split", "diagnose", "verify", "options", "recover", "brief"}

BEGIN = "<!-- jordan-kernel:begin -->"
END = "<!-- jordan-kernel:end -->"


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def module_files():
    return {name[:-3] for name in os.listdir(MODULES_DIR) if name.endswith(".md")}


class ByteCaps(unittest.TestCase):
    def assert_cap(self, path, cap):
        size = os.path.getsize(path)
        self.assertLessEqual(
            size, cap, "%s is %d bytes, cap is %d" % (os.path.relpath(path, ROOT), size, cap))

    def test_kernel_cap(self):
        self.assert_cap(KERNEL, KERNEL_CAP)

    def test_module_caps(self):
        for name in sorted(module_files()):
            with self.subTest(module=name):
                self.assert_cap(os.path.join(MODULES_DIR, name + ".md"), MODULE_CAP)

    def test_skill_cap(self):
        self.assert_cap(SKILL, SKILL_CAP)

    def test_claude_md_cap(self):
        self.assert_cap(CLAUDE_MD, CLAUDE_MD_CAP)


class Kernel(unittest.TestCase):
    def test_title(self):
        self.assertEqual(read(KERNEL).splitlines()[0], "# JORDAN kernel v3")

    def test_rules_one_to_nine_in_order(self):
        numbers = [int(m) for m in re.findall(r"^(\d+)\. ", read(KERNEL), flags=re.M)]
        self.assertEqual(numbers, list(range(1, 10)))

    def test_nothing_but_the_kernel(self):
        # RULINGS R2 / REDTEAM m1: the module pointer lives in SKILL.md, because
        # it dangles for a reader who has the kernel and not the skill.
        text = read(KERNEL)
        self.assertNotIn("modules/", text)
        self.assertNotIn(BEGIN, text)
        self.assertNotIn(END, text)


class ClaudeMd(unittest.TestCase):
    def test_block_equals_kernel(self):
        text = read(CLAUDE_MD)
        self.assertEqual(text.count(BEGIN), 1)
        self.assertEqual(text.count(END), 1)
        inner = text.split(BEGIN, 1)[1].split(END, 1)[0]
        self.assertEqual(inner.strip("\n"), read(KERNEL).strip("\n"))

    def test_render_tool_check_passes(self):
        result = subprocess.run(
            [sys.executable, RENDER, "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_block_comes_first(self):
        # Session-start looks for the marker to avoid injecting the kernel twice.
        self.assertTrue(read(CLAUDE_MD).startswith(BEGIN))


class Skill(unittest.TestCase):
    def frontmatter(self):
        lines = read(SKILL).splitlines()
        self.assertEqual(lines[0], "---", "frontmatter must start on line 1")
        self.assertIn("---", lines[1:], "frontmatter is not closed")
        return lines[1:lines.index("---", 1)]

    def test_frontmatter_name_and_description(self):
        fields = {}
        for line in self.frontmatter():
            self.assertRegex(line, r"^[A-Za-z-]+: \S", "one field per line, no folded values")
            key, value = line.split(": ", 1)
            fields[key] = value
        self.assertEqual(fields.get("name"), "jordan")
        self.assertTrue(fields.get("description"))

    def test_expected_modules_exist(self):
        self.assertEqual(module_files(), EXPECTED_MODULES)

    def test_index_matches_files(self):
        named = set(re.findall(r"modules/([a-z-]+)\.md", read(SKILL)))
        self.assertEqual(named, module_files())

    def test_each_module_is_indexed_with_a_trigger(self):
        text = read(SKILL)
        for name in sorted(module_files()):
            with self.subTest(module=name):
                self.assertRegex(text, r"(?m)^- Read `modules/%s\.md` when \S" % name)

    def test_each_module_opens_with_when_it_applies(self):
        for name in sorted(module_files()):
            with self.subTest(module=name):
                lines = [l for l in read(os.path.join(MODULES_DIR, name + ".md")).splitlines() if l]
                self.assertEqual(lines[0], "# " + name)
                self.assertTrue(lines[1].startswith("Read this when "), lines[1])

    def test_module_cross_references_resolve(self):
        for name in sorted(module_files()):
            text = read(os.path.join(MODULES_DIR, name + ".md"))
            for ref in re.findall(r"`([a-z-]+)\.md`", text):
                with self.subTest(module=name, ref=ref):
                    self.assertIn(ref, module_files())


if __name__ == "__main__":
    unittest.main()
