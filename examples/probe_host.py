"""Ask the machine what it is, and read the answer off the screen.

Run this first against a new Bot. What comes back decides whether anything you
were planning is possible: the machine this was written against has no
scheduler at all, which is not something the documentation says anywhere.

    python examples/probe_host.py

A terminal must already be open on the machine's desktop -- double-click the
terminal icon in the dock and give it a few seconds.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from grokbot_cdp import VmSession, launch  # noqa: E402

PROBE = (
    'clear; '
    'echo "pid1=$(ps -p 1 -o comm=)"; '
    'uname -sr; '
    'python3 -V 2>&1; '
    'id -un; '
    '(sudo -n true 2>/dev/null && echo SUDO=yes || echo SUDO=no); '
    'command -v systemctl crontab cron ssh >/dev/null 2>&1 '
    '&& echo "schedulers: some present" || echo "schedulers: none of systemctl/crontab/cron"; '
    'timeout 10 curl -sS -o /dev/null -w "github=%{http_code}\\n" https://github.com; '
    'df -h / | tail -1'
)


def main() -> int:
    launch()
    with VmSession() as vm:
        print("status:", vm.status())
        rect = vm.canvas()
        print(f"screen: {rect.backing_w}x{rect.backing_h}")

        vm.run(PROBE)
        # No channel carries stdout back, so the only way to read the answer is
        # to wait for the machine to finish drawing it and look.
        time.sleep(15)
        out = vm.screenshot("host-probe.jpg")
        print(f"answer is in {out} -- open it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
