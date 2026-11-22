#!/bin/sh
# Visible check: the workspace's unit tests. Run from the workspace root, or
# pass the workspace as $1.
cd "${1:-$(dirname "$0")}" || exit 2
exec python3 -m unittest discover -s tests -t . 2>&1
