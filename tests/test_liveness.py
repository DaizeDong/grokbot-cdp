"""A hidden webview returns its last painted frame, and says nothing about it.

This was not a theory. During a real run the app window was minimised; typed
commands kept landing and producing output on the machine, `status()` kept
answering "Connected (encrypted)", and three screenshots in a row came back
byte-identical because the host had stopped sending framebuffer updates to a
hidden page. Two rounds of work were read off a stale frame before the cause
was found. The screen was the only channel, and it lied without failing.
"""

import unittest
from unittest import mock

from grokbot_cdp import StaleFrameError
from grokbot_cdp import vm as vm_mod


class FakeCdp:
    """Enough of the protocol client to exercise the gate, and nothing more."""

    def __init__(self, visibility="visible"):
        self.visibility = visibility
        self.captures = 0

    def eval(self, js):
        if js == vm_mod._VISIBILITY_JS:
            return self.visibility
        raise AssertionError("unexpected eval: %r" % js)

    def send(self, method, params=None):
        if method == "Page.captureScreenshot":
            self.captures += 1
            # One transparent pixel, base64; the bytes do not matter here.
            return {"data": "iVBORw0KGgo="}
        raise AssertionError("unexpected method: %r" % method)


def session_with(cdp):
    session = vm_mod.VmSession.__new__(vm_mod.VmSession)
    session.cdp = cdp
    session._port = 9222
    session._timeout = 120
    return session


class HiddenWebviewTests(unittest.TestCase):
    def test_a_hidden_webview_refuses_to_be_screenshotted(self, ):
        cdp = FakeCdp("hidden")
        session = session_with(cdp)
        with self.assertRaises(StaleFrameError):
            session.screenshot("unused.jpg")
        self.assertEqual(cdp.captures, 0,
                         "it must refuse before capturing, not after")

    def test_a_visible_webview_is_captured(self, tmp=None):
        # The negative control. Without it the gate could pass by refusing
        # every capture, which would be just as useless and far quieter.
        import tempfile, pathlib
        cdp = FakeCdp("visible")
        session = session_with(cdp)
        with tempfile.TemporaryDirectory() as d:
            out = session.screenshot(pathlib.Path(d) / "shot.jpg")
            self.assertTrue(out.exists())
        self.assertEqual(cdp.captures, 1)

    def test_the_caller_can_insist_on_the_stale_frame(self):
        cdp = FakeCdp("hidden")
        session = session_with(cdp)
        import tempfile, pathlib
        with tempfile.TemporaryDirectory() as d:
            session.screenshot(pathlib.Path(d) / "shot.jpg", allow_stale=True)
        self.assertEqual(cdp.captures, 1)

    def test_is_visible_reports_the_document_state(self):
        self.assertTrue(session_with(FakeCdp("visible")).is_visible())
        self.assertFalse(session_with(FakeCdp("hidden")).is_visible())
        self.assertFalse(session_with(FakeCdp("prerender")).is_visible())


if __name__ == "__main__":
    unittest.main()
