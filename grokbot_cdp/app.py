"""Find the Grok Bot desktop app and start it with a debugging port open.

There is no API to start from. xAI's documentation describes exactly one way to
work with a Bot -- "You work with a Bot by messaging it" -- and offers no REST
endpoint, webhook or CLI for the machine behind it. api.x.ai is the MODEL API
and has nothing to do with Bots. The third-party `grok-cli` packages on GitHub
talk to that model API too, so they do not help either.

What does exist is that the desktop app is Electron, and an Electron app will
open a DevTools port if asked. That is the entire foothold.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import requests

DEFAULT_PORT = 9222

#: Where the installer puts the executable, per platform. Checked in order.
CANDIDATES = {
    "win32": [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Grok Bot" / "Grok Bot.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Grok Bot" / "Grok Bot.exe",
    ],
    "darwin": [
        Path("/Applications/Grok Bot.app/Contents/MacOS/Grok Bot"),
    ],
    "linux": [
        Path("/opt/Grok Bot/grok-bot"),
        Path("/usr/bin/grok-bot"),
    ],
}


def find_app(platform: str | None = None) -> Path | None:
    """The installed executable, or None if it is not where installers put it."""
    import sys

    for candidate in CANDIDATES.get(platform or sys.platform, []):
        if candidate and candidate.exists():
            return candidate
    return None


def cdp_is_open(port: int = DEFAULT_PORT, timeout: int = 5) -> bool:
    try:
        requests.get(f"http://127.0.0.1:{port}/json/version", timeout=timeout)
        return True
    except Exception:  # noqa: BLE001 - any failure means "not open"
        return False


def launch(port: int = DEFAULT_PORT, app: Path | None = None,
           wait_s: int = 60, poll_s: float = 2.0) -> None:
    """Start the app with the debugging port open, and wait until it answers.

    Idempotent: if something is already listening on the port, this returns
    without starting a second copy. That matters because the app is a normal
    desktop application -- a second instance may take over the session, and the
    first one's webview then belongs to a process nobody is holding.

    The port listens on loopback only. It is still a debugging port into a
    signed-in application, so close the app when a run is finished rather than
    leaving it open indefinitely.
    """
    if cdp_is_open(port):
        return

    exe = app or find_app()
    if exe is None:
        raise FileNotFoundError(
            "Grok Bot is not installed where installers put it. Pass app=Path(...)."
        )

    # Detached: the app outlives this process, which is what a caller driving
    # several sessions wants, and killing the driver should not kill the window
    # someone may be watching.
    creation = 0
    if os.name == "nt":
        creation = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen([str(exe), f"--remote-debugging-port={port}"],
                     creationflags=creation, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)

    deadline = time.monotonic() + wait_s
    while time.monotonic() < deadline:
        if cdp_is_open(port):
            return
        time.sleep(poll_s)
    raise TimeoutError(
        f"the app did not open a debugging port on {port} within {wait_s}s"
    )
