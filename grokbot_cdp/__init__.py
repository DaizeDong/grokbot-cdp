"""Drive the machine behind a Grok Bot from your own code.

    from grokbot_cdp import launch, VmSession

    launch()                       # start the app with a debugging port open
    with VmSession() as vm:
        print(vm.status())         # Connected (encrypted) to ...
        vm.run("uname -sr")
        vm.screenshot("screen.jpg")

See README.md for what the machine turns out to be, and for the things that
are not possible on it.
"""

from .app import cdp_is_open, find_app, launch
from .cdp import Cdp, CdpError, find_vm_target, list_targets
from .secrets import describe_env_file, json_header_value, shell_quote, write_env_file
from .vm import CanvasRect, VmSession

__all__ = [
    "Cdp",
    "CdpError",
    "CanvasRect",
    "VmSession",
    "cdp_is_open",
    "describe_env_file",
    "find_app",
    "find_vm_target",
    "json_header_value",
    "launch",
    "list_targets",
    "shell_quote",
    "write_env_file",
]

__version__ = "0.1.0"
