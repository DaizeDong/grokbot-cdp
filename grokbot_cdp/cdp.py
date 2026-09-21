"""A raw Chrome DevTools Protocol client, because Playwright cannot see the VM.

Grok Bot is an Electron app. Its window is an ordinary CDP `page`, but the
remote machine it drives is delivered inside an Electron `<webview>`, and
`<webview>` is a target type Playwright's `connect_over_cdp` does not surface
as a page: attaching with Playwright lists the renderer and nothing else. The
only way to reach the machine is to speak CDP to that target's own websocket.

Two details here were each found by a failure, not by reading documentation.
"""

from __future__ import annotations

import json
from typing import Any

import requests
import websocket

#: Screenshots of a remote desktop are large -- a 1280x800 canvas comes back as
#: roughly a megabyte of base64 at device pixel ratio 2 -- and the response
#: arrives as one websocket message. The default here is generous for that
#: reason: a 30 second timeout produces intermittent WebSocketTimeoutException
#: on exactly the call you most want to succeed.
DEFAULT_TIMEOUT_S = 120


class CdpError(RuntimeError):
    """A CDP command came back with an error, or the target refused to attach."""


class Cdp:
    """One websocket to one CDP target."""

    def __init__(self, ws_url: str, timeout: int = DEFAULT_TIMEOUT_S) -> None:
        # suppress_origin is not optional. Chrome refuses a DevTools websocket
        # that carries an Origin header unless the browser was started with
        # --remote-allow-origins, and most websocket clients send one by
        # default. The refusal is a 403 during the handshake with a message
        # naming the flag, which reads like the browser needs relaunching; it
        # does not. Sending no Origin at all is accepted.
        self.ws = websocket.create_connection(ws_url, timeout=timeout,
                                              suppress_origin=True)
        self._id = 0

    def send(self, method: str, params: dict | None = None) -> dict:
        """Issue one command and return its result."""
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method,
                                 "params": params or {}}))
        # CDP interleaves events with replies, so read until the id matches
        # rather than taking the next message.
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") != self._id:
                continue
            if "error" in message:
                raise CdpError(f"{method}: {message['error']}")
            return message.get("result", {})

    def eval(self, expression: str, await_promise: bool = False) -> Any:
        """Evaluate JavaScript in the target and return the value."""
        result = self.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": await_promise,
        })
        if "exceptionDetails" in result:
            detail = result["exceptionDetails"]
            raise CdpError(detail.get("text") or "evaluate failed")
        return result.get("result", {}).get("value")

    def close(self) -> None:
        try:
            self.ws.close()
        except Exception:  # noqa: BLE001 - closing must not raise
            pass

    def __enter__(self) -> "Cdp":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def list_targets(port: int = 9222, timeout: int = 15) -> list[dict]:
    """Every debuggable target in the app."""
    return requests.get(f"http://127.0.0.1:{port}/json/list", timeout=timeout).json()


def find_vm_target(port: int = 9222, timeout: int = 15) -> dict | None:
    """The webview carrying the remote machine, or None.

    Matched by target TYPE and by the noVNC page it loads, not by its title.
    The title contains the machine's own name, which differs per account and
    changes when the machine is replaced.
    """
    for target in list_targets(port, timeout):
        if target.get("type") == "webview" and "vnc.html" in target.get("url", ""):
            return target
    return None
