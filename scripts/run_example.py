#!/usr/bin/env python3
"""Start one of the example apps and return at once.

    python scripts/run_example.py                    # the calculator example
    python scripts/run_example.py example_test       # the plain window example

The app keeps running after this script and the terminal it was started from
are gone. Its output goes to ``<temp>/qtpy-nodeeditor-<example>.log`` so a
startup error can still be read afterwards.
"""

import glob
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(ROOT, "examples")
DEFAULT_EXAMPLE = "example_calculator"


def find_entry_points():
    """``{example directory name: path of its main script}``."""
    entry_points = {}
    for path in sorted(glob.glob(os.path.join(EXAMPLES_DIR, "*", "main*.py"))):
        entry_points[os.path.basename(os.path.dirname(path))] = path
    return entry_points


def main(argv):
    entry_points = find_entry_points()
    name = argv[1] if len(argv) > 1 else DEFAULT_EXAMPLE
    if name not in entry_points:
        print("unknown example %r, available: %s" % (
            name, ", ".join(sorted(entry_points))))
        return 2

    log_path = os.path.join(
        tempfile.gettempdir(), "qtpy-nodeeditor-%s.log" % name)
    with open(log_path, "wb") as log:
        # Detach from this terminal: closing the shell must not close the app.
        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            kwargs["start_new_session"] = True
        process = subprocess.Popen(
            [sys.executable, entry_points[name]],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            **kwargs)

    print("started %s in process %d" % (name, process.pid))
    print("log: %s" % log_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
