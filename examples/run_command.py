"""Run one command on the machine and screenshot the result.

    python examples/run_command.py "ls -la /workspace"

The screenshot is the output. Nothing here parses it, and nothing can: the
session carries pixels, not a stream. For anything you need to act on, have the
command write to a place you can reach another way -- a file the machine then
pushes, or a request it makes outward.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from grokbot_cdp import VmSession, launch  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    command = sys.argv[1]
    settle = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0

    launch()
    with VmSession() as vm:
        status = vm.status() or ""
        if "Connected" not in status:
            # Worth failing on rather than typing into a session that is still
            # negotiating: the keystrokes go nowhere and the command looks like
            # it silently did nothing.
            print(f"not connected: {status!r}")
            return 1
        vm.run(f"clear; {command}")
        time.sleep(settle)
        print("wrote", vm.screenshot("command-output.jpg"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
