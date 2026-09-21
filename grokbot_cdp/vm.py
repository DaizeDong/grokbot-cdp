"""Drive the remote machine through its noVNC canvas.

The machine is delivered as a noVNC session inside the app's webview: a canvas
element, a websocket to the host, and nothing else the page exposes. noVNC's
own RFB object is module-scoped, so there is no `window.rfb` to call. What
works is dispatching input events at the canvas through CDP, which noVNC's
listeners pick up and forward exactly as if a person had typed.

Coordinates are fractions of the canvas rather than pixels, deliberately. The
canvas backing store is the machine's resolution, the element is laid out at
whatever size the webview gives it, and a screenshot comes back at the device
pixel ratio. Three different scales; a fraction survives all of them.
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from pathlib import Path

from .cdp import Cdp, find_vm_target

#: One character-producing event per character, not two.
#:
#: A keyDown carrying `text` already inserts the character. Sending a `char`
#: event as well inserts it a second time, and every command comes out doubled
#: ("cclleeaarr"). It does not double every time, which is worse than if it
#: always did: early runs look fine and the habit looks safe until a command
#: that matters is mangled.
_SPECIAL = {"\n": ("Enter", "Enter", 13), "\t": ("Tab", "Tab", 9)}


@dataclass(frozen=True)
class CanvasRect:
    x: float
    y: float
    w: float
    h: float
    backing_w: int
    backing_h: int


_RECT_JS = """
(() => {
  const c = document.querySelector('canvas');
  if (!c) return null;
  const r = c.getBoundingClientRect();
  return {x: r.x, y: r.y, w: r.width, h: r.height, bw: c.width, bh: c.height};
})()
"""

_STATUS_JS = """
(() => {
  const e = document.getElementById('noVNC_status');
  return e ? e.textContent.trim() : null;
})()
"""

_VISIBILITY_JS = "document.visibilityState"


class StaleFrameError(RuntimeError):
    """The screen cannot be read right now, and reading it would lie.

    Raised when the webview is hidden, which on a desktop means the app window
    is minimised or fully covered. The host stops sending framebuffer updates
    to a hidden page, so the canvas keeps whatever it last painted -- and the
    session reports `Connected` throughout, because it is.
    """


class VmSession:
    """A connection to the machine behind one Grok Bot app."""

    def __init__(self, port: int = 9222, timeout: int = 120) -> None:
        target = find_vm_target(port)
        if target is None:
            raise RuntimeError(
                "no noVNC webview found. The app is running but its machine view "
                "is not open, or the app has not finished connecting."
            )
        self._port = port
        self._timeout = timeout
        self.cdp = Cdp(target["webSocketDebuggerUrl"], timeout=timeout)

    # ---------------------------------------------------------------- state

    def status(self) -> str | None:
        """What noVNC says about the connection, e.g. 'Connected (encrypted) to ...'."""
        return self.cdp.eval(_STATUS_JS)

    def canvas(self) -> CanvasRect:
        raw = self.cdp.eval(_RECT_JS)
        if not raw:
            raise RuntimeError("the webview has no canvas; the session is not connected")
        return CanvasRect(raw["x"], raw["y"], raw["w"], raw["h"], raw["bw"], raw["bh"])

    def is_visible(self) -> bool:
        """Whether the webview is being painted, and so whether the screen is live."""
        return self.cdp.eval(_VISIBILITY_JS) == "visible"

    def reconnect(self, *, wait_s: float = 18.0) -> str | None:
        """Reload the viewer and reattach, which restarts the framebuffer stream.

        This touches the viewer, not the machine: the container keeps running
        and the session comes back to the same one. Use it when the screen has
        stopped changing but commands still take effect.
        """
        self.cdp.eval("location.reload()")
        self.cdp.close()
        time.sleep(wait_s)
        target = find_vm_target(self._port)
        if target is None:
            raise RuntimeError("the viewer did not come back after a reload")
        self.cdp = Cdp(target["webSocketDebuggerUrl"], timeout=self._timeout)
        return self.status()

    def screenshot(self, path: str | Path, *, fmt: str = "jpeg",
                   quality: int = 70, allow_stale: bool = False) -> Path:
        """Capture the machine's screen.

        JPEG by default. A PNG of a 1280x800 desktop at device pixel ratio 2 is
        around a megabyte of base64 in a single websocket message, which times
        out intermittently; the same frame as JPEG is a seventh of that and has
        not. Pass fmt="png" when the pixels matter more than the reliability.

        Refuses to capture a hidden webview, because that returns the last
        painted frame with nothing to distinguish it from a current one. Pass
        allow_stale=True to take it anyway.
        """
        if not allow_stale and not self.is_visible():
            raise StaleFrameError(
                "the webview is hidden, so this would return the last frame it "
                "painted rather than the screen now. Restore the app window, or "
                "call reconnect(), or pass allow_stale=True."
            )
        params: dict = {"format": fmt}
        if fmt == "jpeg":
            params["quality"] = quality
        data = self.cdp.send("Page.captureScreenshot", params)["data"]
        out = Path(path)
        out.write_bytes(base64.b64decode(data))
        return out

    # ---------------------------------------------------------------- input

    def click(self, fx: float, fy: float, *, clicks: int = 1,
              settle_s: float = 0.12) -> None:
        """Click at a fraction of the canvas: (0,0) top left, (1,1) bottom right."""
        rect = self.canvas()
        x = rect.x + fx * rect.w
        y = rect.y + fy * rect.h
        self.cdp.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
        for n in range(1, clicks + 1):
            for kind in ("mousePressed", "mouseReleased"):
                self.cdp.send("Input.dispatchMouseEvent", {
                    "type": kind, "x": x, "y": y, "button": "left", "clickCount": n,
                })
            time.sleep(settle_s)

    def focus(self) -> None:
        """Put keyboard focus on the canvas.

        Typing goes to whatever the machine has focused, so a click somewhere
        harmless first is the difference between a command and a command typed
        into the desktop background.
        """
        self.click(0.25, 0.35)
        time.sleep(0.2)

    def type(self, text: str, *, per_char_s: float = 0.012) -> None:
        """Type text, one character-producing event per character."""
        for ch in text:
            if ch in _SPECIAL:
                key, code, vk = _SPECIAL[ch]
                for kind in ("keyDown", "keyUp"):
                    self.cdp.send("Input.dispatchKeyEvent", {
                        "type": kind, "key": key, "code": code,
                        "windowsVirtualKeyCode": vk,
                    })
            else:
                self.cdp.send("Input.dispatchKeyEvent",
                              {"type": "keyDown", "text": ch, "key": ch})
                self.cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": ch})
            time.sleep(per_char_s)

    def run(self, command: str, *, focus: bool = True) -> None:
        """Type a shell command into the focused terminal and press Enter.

        Fire and forget: nothing here reads the output, because the only
        channel back is the screen. Capture a screenshot afterwards, or have
        the command write somewhere you can read another way.
        """
        if focus:
            self.focus()
        self.type(command + "\n")

    def close(self) -> None:
        self.cdp.close()

    def __enter__(self) -> "VmSession":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
