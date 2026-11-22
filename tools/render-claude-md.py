#!/usr/bin/env python3
"""Render the JORDAN kernel block into a CLAUDE.md.

The kernel has one source, skills/jordan/kernel.md. A CLAUDE.md carries a copy
between two markers so the kernel is in context on every step. This tool keeps
that copy equal to the source and leaves every byte outside the markers alone,
because the target may be a user's own CLAUDE.md.

    render-claude-md.py [TARGET] [--kernel PATH] [--check]

TARGET defaults to CLAUDE.md in the repository root; a directory means the
CLAUDE.md inside it. Without --check the block is replaced, or appended when
the target has none, or the file is created. With --check nothing is written:
exit 0 when the target's block equals the kernel, 1 when it differs or is
missing. Exit 2 is a usage or file error (for example a begin marker with no
end marker, which this tool will not guess its way around).

Stdlib only.
"""
import argparse
import os
import sys
import tempfile

BEGIN = "<!-- jordan-kernel:begin -->"
END = "<!-- jordan-kernel:end -->"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_KERNEL = os.path.join(REPO_ROOT, "skills", "jordan", "kernel.md")
DEFAULT_TARGET = os.path.join(REPO_ROOT, "CLAUDE.md")


class BlockError(Exception):
    """The target's markers are malformed."""


def kernel_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read().strip("\n")


def block(kernel):
    return "%s\n%s\n%s" % (BEGIN, kernel, END)


def find_block(text):
    """Return (start, end) offsets of the marker block, or None if absent."""
    start = text.find(BEGIN)
    if start == -1:
        if END in text:
            raise BlockError("end marker without a begin marker")
        return None
    stop = text.find(END, start + len(BEGIN))
    if stop == -1:
        raise BlockError("begin marker without an end marker")
    if text.find(BEGIN, start + len(BEGIN)) != -1:
        raise BlockError("more than one begin marker")
    return start, stop + len(END)


def render(text, kernel):
    """Return text with its kernel block replaced, or appended if absent."""
    span = find_block(text)
    if span is not None:
        return text[: span[0]] + block(kernel) + text[span[1]:]
    if not text:
        return block(kernel) + "\n"
    gap = "" if text.endswith("\n\n") else "\n" if text.endswith("\n") else "\n\n"
    return text + gap + block(kernel) + "\n"


def write_atomic(path, text):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".claude-md-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        if os.path.exists(path):
            os.chmod(tmp, os.stat(path).st_mode & 0o777)
        else:
            os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("target", nargs="?", default=DEFAULT_TARGET,
                        help="CLAUDE.md file or a directory holding one (default: repo root)")
    parser.add_argument("--kernel", default=DEFAULT_KERNEL,
                        help="kernel source (default: skills/jordan/kernel.md)")
    parser.add_argument("--check", action="store_true",
                        help="write nothing; exit 1 if the block differs from the kernel")
    args = parser.parse_args(argv)

    target = args.target
    if os.path.isdir(target):
        target = os.path.join(target, "CLAUDE.md")

    try:
        kernel = kernel_text(args.kernel)
    except OSError as err:
        print("render-claude-md: cannot read kernel: %s" % err, file=sys.stderr)
        return 2
    if BEGIN in kernel or END in kernel:
        print("render-claude-md: kernel must not contain the markers", file=sys.stderr)
        return 2

    try:
        with open(target, encoding="utf-8", newline="") as handle:
            current = handle.read()
        exists = True
    except FileNotFoundError:
        current, exists = "", False
    except OSError as err:
        print("render-claude-md: cannot read %s: %s" % (target, err), file=sys.stderr)
        return 2

    try:
        span = find_block(current)
        wanted = render(current, kernel)
    except BlockError as err:
        print("render-claude-md: %s: %s; fix the file by hand" % (target, err), file=sys.stderr)
        return 2

    if args.check:
        if not exists:
            print("render-claude-md: %s does not exist" % target, file=sys.stderr)
            return 1
        if span is None:
            print("render-claude-md: %s has no kernel block" % target, file=sys.stderr)
            return 1
        if wanted != current:
            print("render-claude-md: kernel block in %s differs from %s; "
                  "run tools/render-claude-md.py" % (target, args.kernel), file=sys.stderr)
            return 1
        print("render-claude-md: %s is current" % target)
        return 0

    if wanted == current:
        print("render-claude-md: %s already current" % target)
        return 0
    write_atomic(target, wanted)
    verb = "replaced block in" if span is not None else "appended block to" if exists else "created"
    print("render-claude-md: %s %s" % (verb, target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
