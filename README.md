# grokbot-cdp

Drive the cloud machine behind a Grok Bot (xAI's computer-use agent) from Python, over the Chrome DevTools Protocol, because there is no API to call.

[![Python](https://img.shields.io/badge/Python-3.11%2B-orange?style=flat)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Dependencies](https://img.shields.io/badge/Dependencies-2-green?style=flat)](pyproject.toml)
[![Languages](https://img.shields.io/badge/Languages-EN%20%2F%20CN-blue?style=flat)](#languages)
[![Roadmap](https://img.shields.io/badge/Roadmap-v0.1.0-purple?style=flat)](ROADMAP.md)

[English](README.md) | [中文版](README_CN.md)

---

## ⭐ Read this first, the design philosophy

Three commitments shape everything here, and they are worth more than the API surface.

**Measured, never inferred.** Every number, every error string and every quirk in this
repository came from a run against a real Bot. Nothing was read off documentation and
nothing was reasoned out from how the parts ought to behave. Where a claim rests on a
single observation, the text says so rather than rounding it up into a rule.

**A channel that can lie is made to fail instead.** The screen is the only channel this
library has, and it has a failure mode where it keeps answering and stops being true: a
hidden window returns the frame it last painted while input still lands and the session
still reports `Connected`. A caveat in a document does not survive contact with that,
because the wrong answer looks exactly like the right one. So the library refuses. It
raises rather than hand back a frame it cannot vouch for, and the same instinct runs
through the input model and the credential handling.

**The narrow credential.** The machine on the far end is shared with every other Bot on
the account, files and browser sessions included. Anything put there should therefore be
the smallest thing that does the job, should never be painted on the screen on its way
in, and should be revocable on its own.

## What it is (and isn't)

It is a small Python library that attaches to the Grok Bot desktop app's Chrome DevTools
port, finds the `<webview>` carrying the machine's noVNC session, and from there reads
the screen, sends clicks and keystrokes, runs shell commands, and places a credential
without echoing it. Two runtime dependencies, `requests` and `websocket-client`.

It is **not** a Claude Code skill or plugin, and it ships no `SKILL.md`: it is a library
you import. It is **not** a browser automation framework, and it does not wrap one,
because the framework everyone reaches for cannot see this target at all. It is **not**
supported by xAI, and it is automation against an interface that was never offered as
one, so a change to the app's internals can end it without notice.

Most of all it is **not a channel that carries stdout**. Output comes back as pixels.
Nothing here reads a command's exit status or its text, so a command whose result
matters has to write somewhere you can reach by another route.

## Install

Python 3.11 or newer, on Windows, macOS or Linux.

```bash
git clone --recursive https://github.com/DaizeDong/grokbot-cdp
cd grokbot-cdp
pip install -e .                       # or: pip install -r requirements.txt
git config core.hooksPath .githooks    # arms the guards; local config, so it cannot be committed
```

`--recursive` matters. The gates live in submodules, and a plain clone leaves those
directories present and empty, which `.githooks/pre-commit` refuses rather than passing
in silence. If you already cloned without it, run
`git submodule update --init --recursive`.

The app must be signed in already. This library does not handle login, and should not:
that is the one step worth doing yourself.

## Quick start

```python
from grokbot_cdp import launch, VmSession

launch()
with VmSession() as vm:
    print(vm.status())          # Connected (encrypted) to grok-bot-vm-<id>:2
    vm.run("uname -sr; python3 -V")
    vm.screenshot("screen.jpg")
```

```bash
python examples/probe_host.py          # what can this machine do
python examples/run_command.py "ls -la /workspace"
```

## Where the details live

Each rule has exactly one home, and it is not this file. Follow a pointer when the
question it answers is the one you have.

| Read this | When you are asking |
| --- | --- |
| [reference/cdp-transport.md](reference/cdp-transport.md) | How a process here reaches that screen, and what sits on which side of the network boundary |
| [reference/input-model.md](reference/input-model.md) | Why a click or a keystroke did not arrive, or arrived twice |
| [reference/screen-capture.md](reference/screen-capture.md) | Whether the frame you are holding is the machine as it is right now |
| [reference/machine-model.md](reference/machine-model.md) | What kind of host is on the other end, and what survives when it goes away |
| [reference/secrets.md](reference/secrets.md) | How to put a credential there, and what putting it there exposes |
| [reference/no-api.md](reference/no-api.md) | Why this exists instead of an API call, and which near miss you are about to try |

## API at a glance

| Path | What it is |
| --- | --- |
| `grokbot_cdp/app.py` | Find the installed app; start it with a debugging port; wait for it. |
| `grokbot_cdp/cdp.py` | Raw CDP client and target selection. |
| `grokbot_cdp/vm.py` | Read the screen, click, type, run a command, reconnect. |
| `grokbot_cdp/secrets.py` | Put a credential on the machine without showing it. |
| `examples/` | A capability probe and a one-command runner. |
| `tests/` | Offline checks: target selection, input shape, shell quoting, screen liveness, packaging, repository hygiene. |
| `CONTRIBUTING.md` | How to clone it with its gates, and what has to be measured rather than assumed. |

## Limitations

No stdout, as above: results come back as pixels or not at all. No support, from xAI or
anyone else. One session at a time, since the client assumes a single app with a single
machine view. And no guarantee of tomorrow: this drives an interface that was never
published as one.

## Languages

English (`README.md`) · 中文 (`README_CN.md`)

## Roadmap · Contributing · License

See [ROADMAP.md](ROADMAP.md) · [CHANGELOG.md](CHANGELOG.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [LICENSE](LICENSE) (MIT).

The deviations from the house repository spec, and the reasons for each, are recorded in
[docs/2026-09-22-spec-adaptation.md](docs/2026-09-22-spec-adaptation.md).
