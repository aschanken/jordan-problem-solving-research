"""Checks on JORDAN-V3-AGENT.md, the one-file handover for a stock agent.

The handover copies text that has its own source (kernel, modules, shared agent
block), so these tests exist to stop the copy drifting and to keep the file
usable by an agent that has nothing else. Runs under unittest or pytest, stdlib
only.
"""
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIEF = os.path.join(ROOT, "JORDAN-V3-AGENT.md")
BUILD = os.path.join(ROOT, "tools", "build-agent-brief.py")
SKILL_DIR = os.path.join(ROOT, "skills", "jordan")
KERNEL = os.path.join(SKILL_DIR, "kernel.md")
SKILL = os.path.join(SKILL_DIR, "SKILL.md")
MODULES_DIR = os.path.join(SKILL_DIR, "modules")
CORE = os.path.join(ROOT, "agents", "shared", "jordan-core.md")

MODULES = ("plan", "split", "diagnose", "verify", "options", "recover", "brief")

# The handover is read once, when the user hands it over, so this cap is not a
# per-step cost like the kernel's. It is about whether a stock agent reads to
# the end and still acts on the first section. Measured with `wc -c` when this
# test was written: the file was 31,494 bytes, of which the embedded sources
# are fixed by their own caps (kernel 2,596; the seven modules 14,720 together;
# shared block about 1,200) and the pointer block repeats the triggers. A
# haiku-class agent read the whole file and carried out every step at that
# size (docs/v3/agent-brief-verification.md). The cap leaves about 1,500 bytes
# of room, so a reworded module still fits and new wrapper prose has to earn
# its place by replacing some.
BRIEF_CAP = 33000

# What must be in context on every step after adoption: kernel plus pointer
# block. The kernel alone is capped at 2,800 (RULINGS R2); the pointer block
# stands in for SKILL.md's trigger list and the hooks, and is held to the size
# of a small module index.
ALWAYS_LOADED_CAP = 4200

KERNEL_BEGIN = "<!-- jordan-kernel:begin -->"
KERNEL_END = "<!-- jordan-kernel:end -->"
POINTER_BEGIN = "<!-- jordan-pointer:begin -->"
POINTER_END = "<!-- jordan-pointer:end -->"
PROC_BEGIN = "<!-- jordan-procedures:begin -->"
PROC_END = "<!-- jordan-procedures:end -->"


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def between(text, begin, end):
    """Text between two marker lines; each marker must be a whole line, once."""
    lines = text.split("\n")
    starts = [i for i, line in enumerate(lines) if line == begin]
    stops = [i for i, line in enumerate(lines) if line == end]
    assert len(starts) == 1 and len(stops) == 1, (begin, starts, stops)
    assert starts[0] < stops[0]
    return "\n".join(lines[starts[0] + 1:stops[0]])


def skill_triggers():
    found = {}
    for line in read(SKILL).split("\n"):
        match = re.match(r"^- Read `modules/([a-z]+)\.md` (when .+)$", line)
        if match:
            found[match.group(1)] = match.group(2)
    return found


class Current(unittest.TestCase):
    def test_built_file_is_current(self):
        result = subprocess.run(
            [sys.executable, BUILD, "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_fails_on_a_stale_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            stale = os.path.join(tmp, "stale.md")
            with open(stale, "w", encoding="utf-8") as handle:
                handle.write(read(BRIEF) + "drift\n")
            result = subprocess.run(
                [sys.executable, BUILD, "--check", "--out", stale],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            missing = subprocess.run(
                [sys.executable, BUILD, "--check", "--out", os.path.join(tmp, "no.md")],
                capture_output=True, text=True)
            self.assertEqual(missing.returncode, 1, missing.stderr)


class Content(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brief = read(BRIEF)

    def test_kernel_verbatim_between_markers(self):
        self.assertEqual(
            between(self.brief, KERNEL_BEGIN, KERNEL_END),
            read(KERNEL).strip("\n"))

    def test_every_marker_is_a_whole_line_exactly_once(self):
        # The copy commands in the file match whole lines, so a marker quoted
        # in prose is harmless, but a second whole-line copy would not be.
        lines = self.brief.split("\n")
        for marker in (KERNEL_BEGIN, KERNEL_END, POINTER_BEGIN, POINTER_END,
                       PROC_BEGIN, PROC_END):
            with self.subTest(marker=marker):
                self.assertEqual(lines.count(marker), 1)

    def test_all_seven_modules_with_their_triggers(self):
        triggers = skill_triggers()
        self.assertEqual(set(triggers), set(MODULES))
        procedures = between(self.brief, PROC_BEGIN, PROC_END)
        pointer = between(self.brief, POINTER_BEGIN, POINTER_END)
        for name in MODULES:
            with self.subTest(module=name):
                line = "- `%s`: %s" % (name, triggers[name])
                self.assertIn(line, procedures)
                self.assertIn(line, pointer)
                self.assertIn("\n## %s\n" % name, procedures)

    def test_module_text_is_not_reworded(self):
        # Headings are pushed down a level by the generator; every other line
        # of every module must appear unchanged, and in order.
        procedures = between(self.brief, PROC_BEGIN, PROC_END)
        for name in MODULES:
            with self.subTest(module=name):
                source = read(os.path.join(MODULES_DIR, name + ".md")).strip("\n")
                body = "\n".join(
                    line for line in source.split("\n") if not line.startswith("#"))
                built = "\n".join(
                    line for line in procedures.split("\n") if not line.startswith("#"))
                self.assertIn(body.strip("\n"), built)

    def test_shared_block_verbatim(self):
        core = read(CORE)
        block = core[core.index("<!-- jordan-core:begin -->")
                     + len("<!-- jordan-core:begin -->"):
                     core.index("<!-- jordan-core:end -->")].strip("\n")
        self.assertIn(block, self.brief)

    def test_no_unexpanded_include(self):
        self.assertNotIn("<!-- include:", self.brief)

    def test_names_the_instruction_files(self):
        for name in ("CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursor/rules",
                     "CONVENTIONS.md"):
            with self.subTest(file=name):
                self.assertIn(name, self.brief)

    def test_version_line(self):
        self.assertIn("JORDAN v3.0", self.brief)
        self.assertIn("jordan-problem-solving-research", self.brief)

    def test_says_the_effect_is_not_measured(self):
        self.assertIn("has not been measured", self.brief)

    def test_no_builder_machine_paths(self):
        # Absolute paths into a home, temp or root directory exist only on the
        # machine that built the file. `~/...` is allowed: it names a place on
        # the reader's machine.
        for pattern in (r"/home/", r"/Users/", r"/tmp/", r"/root/", r"/var/",
                        r"/mnt/", r"[A-Za-z]:\\"):
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, self.brief))
        self.assertNotIn(ROOT, self.brief)

    def test_no_capitals_for_emphasis(self):
        # Outside the embedded sources, which have their own vocabulary (tier
        # names, STATUS values, verdicts), the wrapper uses no shouted words.
        allowed = {"JORDAN", "FAST", "STANDARD", "DEEP", "CLAUDE", "AGENTS",
                   "GEMINI", "CONVENTIONS", "PATH", "HEAD", "CI", "CLI", "JORDAN-V3-AGENT"}
        text = self.brief
        for begin, end in ((KERNEL_BEGIN, KERNEL_END), (PROC_BEGIN, PROC_END)):
            text = text.replace(between(text, begin, end), "")
        core = read(CORE)
        text = text.replace(
            core[core.index("<!-- jordan-core:begin -->") + 26:
                 core.index("<!-- jordan-core:end -->")].strip("\n"), "")
        shouted = set(re.findall(r"\b[A-Z][A-Z0-9-]{2,}\b", text)) - allowed
        self.assertEqual(shouted, set())


class Size(unittest.TestCase):
    def test_brief_cap(self):
        size = os.path.getsize(BRIEF)
        self.assertLessEqual(size, BRIEF_CAP, "%d bytes, cap %d" % (size, BRIEF_CAP))

    def test_always_loaded_part_cap(self):
        brief = read(BRIEF)
        part = (between(brief, KERNEL_BEGIN, KERNEL_END)
                + between(brief, POINTER_BEGIN, POINTER_END))
        size = len(part.encode("utf-8"))
        self.assertLessEqual(
            size, ALWAYS_LOADED_CAP, "%d bytes, cap %d" % (size, ALWAYS_LOADED_CAP))


if __name__ == "__main__":
    unittest.main()
