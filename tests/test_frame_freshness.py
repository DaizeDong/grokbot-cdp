"""Visible is not the same as fresh, and the difference cost two readings.

The hidden-webview gate in test_liveness.py catches a minimised window. It does not catch
the other way a frame goes stale: a view that has just reconnected reports `visible` and
answers `Connected` while the host has not yet pushed anything, so the canvas still holds
the previous session's picture. On 2026-09-23 a capture taken a second after a reconnect
showed the output of a command run hours earlier, and it was read as the result of the
command just sent.

The fix is to fingerprint before sending and require the screen to change. What that
cannot distinguish is a command whose output is genuinely identical to what was already
there, which is why the contract is "fingerprint before you send", not "compare two
captures afterwards" -- any command at least moves the prompt.
"""

import unittest
from unittest import mock

from grokbot_cdp import StaleFrameError
from grokbot_cdp import vm as vm_mod


class FrozenCanvas:
    """A canvas that never repaints, however often it is read."""

    def __init__(self, frames):
        self.frames = list(frames)
        self.reads = 0

    def eval(self, js):
        if js == vm_mod._VISIBILITY_JS:
            return "visible"          # the point: it says visible throughout
        self.reads += 1
        return self.frames[min(self.reads - 1, len(self.frames) - 1)]


def session_with(cdp):
    session = vm_mod.VmSession.__new__(vm_mod.VmSession)
    session.cdp = cdp
    session._port = 9222
    session._timeout = 120
    return session


class FrameFreshnessTests(unittest.TestCase):
    def test_a_frozen_frame_is_refused_even_though_the_view_is_visible(self):
        cdp = FrozenCanvas(["data:image/jpeg;base64,AAAA"])
        session = session_with(cdp)
        before = session.frame_hash()
        with mock.patch.object(vm_mod.time, "sleep"):
            with self.assertRaises(StaleFrameError):
                session.wait_for_new_frame(before, tries=3, delay_s=0)
        self.assertGreaterEqual(cdp.reads, 4, "it should have looked more than once")

    def test_a_frame_that_advances_is_accepted(self):
        # The negative control. Without it the check could pass by rejecting everything,
        # which would be just as wrong and much louder.
        cdp = FrozenCanvas(["data:image/jpeg;base64,AAAA",
                            "data:image/jpeg;base64,AAAA",
                            "data:image/jpeg;base64,BBBB"])
        session = session_with(cdp)
        before = session.frame_hash()
        with mock.patch.object(vm_mod.time, "sleep"):
            now = session.wait_for_new_frame(before, tries=5, delay_s=0)
        self.assertNotEqual(now, before)

    def test_the_fingerprint_is_of_the_picture_and_not_of_the_call(self):
        """Two reads of the same unchanged canvas must agree, or every frame looks new."""
        cdp = FrozenCanvas(["data:image/jpeg;base64,AAAA"])
        session = session_with(cdp)
        self.assertEqual(session.frame_hash(), session.frame_hash())


if __name__ == "__main__":
    unittest.main()
