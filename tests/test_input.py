"""Input has to arrive exactly once, and where the caller aimed.

Both of these cost a run. The doubling was silent and intermittent, and the
coordinate scaling is wrong in three different ways at once if you reach for
pixels.
"""

import unittest
from unittest import mock

from grokbot_cdp.vm import VmSession


class FakeCdp:
    """Records every CDP command instead of sending it."""

    def __init__(self, canvas=None):
        self.sent = []
        self._canvas = canvas or {"x": 0.0, "y": 0.0, "w": 640.0, "h": 400.0,
                                  "bw": 1280, "bh": 800}

    def send(self, method, params=None):
        self.sent.append((method, params or {}))
        return {}

    def eval(self, expression, await_promise=False):
        if "canvas" in expression:
            return dict(self._canvas)
        return None

    def close(self):
        pass

    def keys(self):
        return [p for m, p in self.sent if m == "Input.dispatchKeyEvent"]

    def mouse(self):
        return [p for m, p in self.sent if m == "Input.dispatchMouseEvent"]


def session(canvas=None) -> VmSession:
    vm = VmSession.__new__(VmSession)
    vm.cdp = FakeCdp(canvas)
    return vm


class TypingTests(unittest.TestCase):
    def test_each_character_produces_exactly_one_insertion(self):
        # A keyDown carrying `text` already inserts the character. Adding a
        # `char` event inserts it again and every command arrives doubled --
        # "cclleeaarr". It did not double on every run, so the habit looked
        # safe until a long command was mangled.
        vm = session()
        with mock.patch("time.sleep"):
            vm.type("ab")

        inserting = [k for k in vm.cdp.keys() if k.get("text")]
        self.assertEqual(
            [k["text"] for k in inserting], ["a", "b"],
            "a character was inserted more than once: %r" % (inserting,),
        )

    def test_no_char_events_are_sent(self):
        vm = session()
        with mock.patch("time.sleep"):
            vm.type("x")
        self.assertNotIn("char", [k.get("type") for k in vm.cdp.keys()],
                         "a char event is a second insertion of the same key")

    def test_enter_is_a_key_not_a_character(self):
        # Sending a newline as text types a literal character into some
        # terminals instead of submitting the line.
        vm = session()
        with mock.patch("time.sleep"):
            vm.type("\n")
        keys = vm.cdp.keys()
        self.assertTrue(all(k.get("key") == "Enter" for k in keys), keys)
        self.assertTrue(all("text" not in k for k in keys),
                        "Enter was sent as text")

    def test_every_key_down_is_released(self):
        # A held modifier or an unreleased key changes how everything after it
        # is interpreted, and the machine has no way to recover on its own.
        vm = session()
        with mock.patch("time.sleep"):
            vm.type("hi\n")
        kinds = [k["type"] for k in vm.cdp.keys()]
        self.assertEqual(kinds.count("keyDown"), kinds.count("keyUp"))


class CoordinateTests(unittest.TestCase):
    def test_a_click_is_placed_by_fraction_of_the_laid_out_canvas(self):
        # The canvas backing store is the machine's resolution (1280x800), the
        # element is laid out at whatever the webview gives it (640x400 here),
        # and a screenshot returns at the device pixel ratio. Pixels read off a
        # screenshot land somewhere else entirely.
        vm = session()
        with mock.patch("time.sleep"):
            vm.click(0.5, 0.25)

        moved = vm.cdp.mouse()[0]
        self.assertEqual((moved["x"], moved["y"]), (320.0, 100.0))

    def test_the_canvas_offset_is_included(self):
        vm = session({"x": 10.0, "y": 20.0, "w": 100.0, "h": 100.0,
                      "bw": 1280, "bh": 800})
        with mock.patch("time.sleep"):
            vm.click(0.0, 0.0)
        moved = vm.cdp.mouse()[0]
        self.assertEqual((moved["x"], moved["y"]), (10.0, 20.0),
                         "the click ignored where the canvas sits in the page")

    def test_a_double_click_reports_increasing_click_counts(self):
        # The dock needs a real double click; two separate single clicks
        # highlight the icon and launch nothing.
        vm = session()
        with mock.patch("time.sleep"):
            vm.click(0.5, 0.5, clicks=2)
        pressed = [m for m in vm.cdp.mouse() if m["type"] == "mousePressed"]
        self.assertEqual([m["clickCount"] for m in pressed], [1, 2])

    def test_typing_a_command_focuses_first(self):
        # Input goes wherever the machine has focus. Without a click the
        # command lands on the desktop background and nothing happens, with no
        # error anywhere.
        vm = session()
        with mock.patch("time.sleep"):
            vm.run("echo hi")
        self.assertTrue(vm.cdp.mouse(), "run() typed without taking focus")


if __name__ == "__main__":
    unittest.main()
