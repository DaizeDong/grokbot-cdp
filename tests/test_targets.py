"""Finding the right target, and the handshake that refuses an Origin header."""

import unittest
from unittest import mock

from grokbot_cdp import cdp as cdp_mod


PAGE = {"type": "page", "title": "Grok Bot",
        "url": "file:///C:/Program%20Files/Grok%20Bot/resources/app.asar/dist/renderer/index.html",
        "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/AAA"}
VM = {"type": "webview", "title": "grok-bot-vm-000000000:2 - noVNC",
      "url": "https://example-pod-000-6081.invalid/vnc.html?network_token=x&autoconnect=1",
      "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/BBB"}
OTHER_WEBVIEW = {"type": "webview", "title": "docs",
                 "url": "https://example.invalid/help.html",
                 "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/CCC"}


class TargetSelectionTests(unittest.TestCase):
    def test_the_machine_is_the_webview_serving_novnc(self):
        with mock.patch.object(cdp_mod, "list_targets",
                               return_value=[PAGE, VM]):
            self.assertEqual(cdp_mod.find_vm_target(), VM)

    def test_the_app_window_is_not_the_machine(self):
        # It is the only `page`, so anything that takes the first target, or
        # the first one Playwright surfaces, drives the app's own UI instead.
        with mock.patch.object(cdp_mod, "list_targets", return_value=[PAGE]):
            self.assertIsNone(cdp_mod.find_vm_target())

    def test_another_webview_is_not_mistaken_for_the_machine(self):
        with mock.patch.object(cdp_mod, "list_targets",
                               return_value=[PAGE, OTHER_WEBVIEW]):
            self.assertIsNone(cdp_mod.find_vm_target())

    def test_selection_does_not_depend_on_the_title(self):
        # The title carries the machine's own name, which differs per account
        # and changes when the machine is replaced.
        renamed = dict(VM, title="something else entirely")
        with mock.patch.object(cdp_mod, "list_targets",
                               return_value=[PAGE, renamed]):
            self.assertEqual(cdp_mod.find_vm_target(), renamed)


class HandshakeTests(unittest.TestCase):
    def test_the_websocket_sends_no_origin_header(self):
        # Chrome answers a DevTools websocket carrying Origin with 403 and
        # names --remote-allow-origins, which reads like the app must be
        # relaunched. Sending no Origin is accepted and needs no relaunch.
        captured = {}

        def fake_create_connection(url, **kwargs):
            captured.update(kwargs)
            return mock.Mock()

        with mock.patch.object(cdp_mod.websocket, "create_connection",
                               fake_create_connection):
            cdp_mod.Cdp("ws://127.0.0.1:9222/devtools/page/BBB")

        self.assertTrue(captured.get("suppress_origin"),
                        "the handshake will be refused with 403")

    def test_the_default_timeout_allows_for_a_screenshot(self):
        # A PNG of a 1280x800 desktop at device pixel ratio 2 is about a
        # megabyte of base64 in one websocket message. Thirty seconds fails
        # intermittently on exactly the call you most want to succeed.
        self.assertGreaterEqual(cdp_mod.DEFAULT_TIMEOUT_S, 60)


class ReplyMatchingTests(unittest.TestCase):
    def test_an_interleaved_event_is_not_read_as_the_reply(self):
        # CDP interleaves events with replies. Taking the next message returns
        # an event whose shape is nothing like the result, and the failure
        # looks like the command misbehaved.
        import json

        messages = [
            json.dumps({"method": "Page.frameNavigated", "params": {}}),
            json.dumps({"id": 1, "result": {"value": 42}}),
        ]
        ws = mock.Mock()
        ws.recv.side_effect = messages

        client = cdp_mod.Cdp.__new__(cdp_mod.Cdp)
        client.ws = ws
        client._id = 0
        self.assertEqual(client.send("Anything"), {"value": 42})

    def test_a_cdp_error_is_raised_not_returned(self):
        import json

        ws = mock.Mock()
        ws.recv.return_value = json.dumps(
            {"id": 1, "error": {"code": -32000, "message": "nope"}})
        client = cdp_mod.Cdp.__new__(cdp_mod.Cdp)
        client.ws = ws
        client._id = 0
        with self.assertRaises(cdp_mod.CdpError):
            client.send("Anything")


if __name__ == "__main__":
    unittest.main()
