"""A credential must not be rendered, and must survive being sourced.

Both failures here are quiet. Echo left on puts the key in every screenshot of
the session, which is noticed much later if at all. An unquoted JSON value is
mangled by the shell and surfaces as a parse error two steps away from its
cause.
"""

import json
import unittest
from unittest import mock

from grokbot_cdp.secrets import (
    describe_env_file,
    json_header_value,
    shell_quote,
    write_env_file,
)


def unquote_single(token: str) -> str:
    """Reverse POSIX single-quoting, the way the shell would.

    'abc'  -> abc        'a'\\''b'  -> a'b
    """
    if not (token.startswith("'") and token.endswith("'")):
        raise AssertionError("argument was not single-quoted: %r" % token)
    return token[1:-1].replace("'\\''", "'")


class FakeVm:
    def __init__(self):
        self.typed = []

    def focus(self):
        self.typed.append("<focus>")

    def type(self, text, **_):
        self.typed.append(text)

    def run(self, command, **_):
        self.typed.append(command)

    def script(self):
        return "".join(t for t in self.typed if t != "<focus>")


class EchoTests(unittest.TestCase):
    def test_echo_is_off_before_the_secret_and_on_afterwards(self):
        vm = FakeVm()
        with mock.patch("time.sleep"):
            write_env_file(vm, "/tmp/env", {"TOKEN": "s3cret"})

        script = vm.script()
        off = script.index("stty -echo")
        secret = script.index("s3cret")
        on = script.index("stty echo")
        self.assertLess(off, secret, "the credential was typed with echo on")
        self.assertLess(secret, on, "echo was restored before the credential")

    def test_echo_is_restored_even_when_writing_fails(self):
        # A terminal left with echo off looks broken in a way nobody connects
        # back to this function.
        class Boom(FakeVm):
            def type(self, text, **_):
                super().type(text, **_)
                if "printf" in text:
                    raise RuntimeError("connection dropped")

        vm = Boom()
        with mock.patch("time.sleep"), self.assertRaises(RuntimeError):
            write_env_file(vm, "/tmp/env", {"TOKEN": "s3cret"})
        self.assertIn("stty echo", vm.script())

    def test_the_file_is_created_with_a_restrictive_umask(self):
        vm = FakeVm()
        with mock.patch("time.sleep"):
            write_env_file(vm, "/tmp/env", {"TOKEN": "s3cret"})
        self.assertIn("umask 077", vm.script(),
                      "the file is briefly world-readable")

    def test_describing_the_file_never_prints_a_value(self):
        vm = FakeVm()
        describe_env_file(vm, "/tmp/env")
        script = vm.script()
        self.assertIn("cut -d= -f1", script,
                      "key names only; cat would print the credentials")
        self.assertNotIn("cat /tmp/env", script)


class QuotingTests(unittest.TestCase):
    def test_a_json_credential_keeps_its_quotes(self):
        # An env file read with `.` is executed, not parsed, so bash performs
        # quote removal. A bare {"k":"v"} arrives as {k:v} and fails to parse.
        headers = json_header_value({"Ocp-Apim-Subscription-Key": "abc", "user": "u"})
        quoted = shell_quote(headers)
        self.assertTrue(quoted.startswith("'") and quoted.endswith("'"))
        self.assertEqual(json.loads(quoted[1:-1]),
                         {"Ocp-Apim-Subscription-Key": "abc", "user": "u"})

    def test_a_value_containing_a_single_quote_survives(self):
        self.assertEqual(shell_quote("it's"), "'it'\\''s'")

    def test_the_value_is_quoted_inside_the_file(self):
        # Checking that the JSON "appears somewhere in what was typed" is not
        # the invariant and does not fail when it is broken: the printf
        # ARGUMENT is shell-quoted either way. What matters is the line that
        # ends up in the file, because that file is sourced -- KEY='{"a":"b"}'
        # survives quote removal, KEY={"a":"b"} arrives as {a:b}.
        #
        # So undo one layer of shell single-quoting and look at the line
        # itself.
        vm = FakeVm()
        with mock.patch("time.sleep"):
            write_env_file(vm, "/tmp/env",
                           {"HEADERS": json_header_value({"a": "b"})})

        printf_line = next(t for t in vm.typed if t.startswith("printf "))
        self.assertIn("printf '%s\\n'", printf_line)
        argument = printf_line.split("printf '%s\\n' ", 1)[1].split(" >> ", 1)[0]
        file_line = unquote_single(argument)

        self.assertEqual(file_line, """HEADERS='{"a":"b"}'""",
                         "the value is not quoted in the file; bash strips its "
                         "double quotes when the file is sourced")

    def test_printf_is_used_rather_than_echo(self):
        # echo interprets escapes in some shells, so a credential containing a
        # backslash would arrive altered.
        vm = FakeVm()
        with mock.patch("time.sleep"):
            write_env_file(vm, "/tmp/env", {"K": "a\\b"})
        script = vm.script()
        self.assertIn("printf", script)
        self.assertNotIn("echo 'K=", script)

    def test_writing_nothing_is_refused(self):
        with self.assertRaises(ValueError):
            write_env_file(FakeVm(), "/tmp/env", {})


if __name__ == "__main__":
    unittest.main()
