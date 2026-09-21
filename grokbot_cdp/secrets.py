"""Put a credential on the machine without painting it on the screen.

Typing is the only input channel, so a secret has to be typed. Two things make
that acceptable rather than careless, and both are easy to leave out.

Turn the terminal's echo off around the secret, so it never renders and cannot
be read from a screenshot taken during or after the run. Screenshots of these
sessions get saved, pasted into issues and handed to other tools; a key that
was on screen is a key in all of them.

Quote the value in the FILE. An env file read with `.` is executed by the
shell, not parsed, so bash performs quote removal on an unquoted value. A JSON
credential written bare arrives as {Ocp-Apim-Subscription-Key:...} with its
double quotes stripped and fails to parse -- measured, and the failure surfaced
as an unrelated-looking parse error two steps later.

Before using any of this: the machine behind a Grok Bot is shared by every Bot
on the account, together with their files, browser sessions and app logins. A
credential placed there is reachable by anything any of those Bots is
persuaded to do. Send the narrowest credential that does the job -- a deploy
key for one repository rather than an account-wide token -- and prefer one you
can revoke by itself.
"""

from __future__ import annotations

import json
import time

from .vm import VmSession


def shell_quote(value: str) -> str:
    """Single-quote a value for a file that will be sourced by the shell."""
    return "'" + value.replace("'", "'\\''") + "'"


def write_env_file(vm: VmSession, remote_path: str, values: dict[str, str],
                   *, settle_s: float = 0.35) -> None:
    """Write `values` to `remote_path` on the machine, with echo suppressed.

    The file is created under umask 077 and written one line at a time, so it
    is never briefly world-readable and never holds a partial line from a
    previous attempt.
    """
    if not values:
        raise ValueError("nothing to write")

    vm.focus()
    vm.type("stty -echo\n")
    time.sleep(0.5)
    try:
        vm.type(f"(umask 077; : > {remote_path})\n")
        time.sleep(settle_s)
        for key, value in values.items():
            line = f"{key}={shell_quote(value)}"
            # printf, not echo: echo interprets escapes in some shells, and a
            # credential containing a backslash would arrive altered.
            vm.type(f"printf '%s\\n' {shell_quote(line)} >> {remote_path}\n")
            time.sleep(settle_s)
    finally:
        # Even if a line above failed, echo must come back on. A terminal left
        # with echo off looks broken in a way nobody connects to this function.
        vm.type("stty echo\n")
        time.sleep(0.3)


def describe_env_file(vm: VmSession, remote_path: str) -> None:
    """Print the SHAPE of the file: permissions, key names, line count.

    Never the values. Verifying a secret landed should not undo the reason it
    was hidden.
    """
    vm.run(f"ls -l {remote_path}; cut -d= -f1 {remote_path}; "
           f"echo lines=$(wc -l < {remote_path})")


def json_header_value(headers: dict[str, str]) -> str:
    """Compact JSON for a header credential, ready to be shell-quoted."""
    return json.dumps(headers, separators=(",", ":"))
