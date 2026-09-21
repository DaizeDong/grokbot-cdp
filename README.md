# grokbot-cdp

Drive the machine behind a Grok Bot from your own code.

## Introduction

Grok Bot gives each account a persistent cloud machine with a browser, a
filesystem and a terminal, and exactly one way to use it: message the Bot.
There is no API. This library takes the other way in -- the desktop app is
Electron, so it will open a Chrome DevTools port, and the machine turns out to
be delivered through a noVNC session inside one of its webviews. Attach to that
target and you can read the screen and send input.

Grok Bot 给每个账号一台持久云主机，带浏览器、文件系统和终端，但只有一种使用
方式：给 Bot 发消息，没有 API。这个库走另一条路——桌面端是 Electron，可以开
DevTools 端口，而那台主机是通过某个 webview 里的 noVNC 会话交付的。挂上那个
target 就能读屏和发输入。

Everything below was measured against a real Bot, not read from documentation.
Where a number appears, it came from a run.

```python
from grokbot_cdp import launch, VmSession

launch()
with VmSession() as vm:
    print(vm.status())          # Connected (encrypted) to grok-bot-vm-<id>:2
    vm.run("uname -sr; python3 -V")
    vm.screenshot("screen.jpg")
```

## What the machine actually is

Probed from inside, a Bot's "cloud computer" is a container, not a VM:

| | |
| --- | --- |
| PID 1 | `tini` |
| `systemctl` | not installed |
| `cron`, `crond`, `systemd-run` | none present |
| `sudo` | passwordless |
| network | outbound works; `github.com` answers 200 |
| python3 | 3.13 |
| `ssh`, `ssh-keygen` | absent until you `apt-get install openssh-client` |
| disk | 126G, a few percent used |
| user, cwd | `box`, `/workspace` |
| delivery | noVNC over HTTPS, 1280x800 |

Two consequences matter more than the rest.

**There is no scheduler.** No systemd and no cron means a recurring job has to
be a foreground loop you start yourself. `/etc/systemd/system` exists as an
empty directory, which makes "install a timer" look available right up until
`systemctl` is not found.

**The container outlives the app.** Uptime kept counting while the desktop app
was closed for a day, and the session reattached to the same machine after the
client machine rebooted. So a `nohup`-ed loop does survive -- but the container
is managed by xAI, nothing documents when it is recycled, and `/workspace` was
empty on first contact.

## Why not the documented paths

The official docs describe one interface: *"You work with a Bot by messaging
it."* No REST endpoint, no webhook, no CLI, nothing to create a Bot or read its
output programmatically.

`api.x.ai` is the **model** API and has no relationship to Bots or their
machine. The `grok-cli` packages on GitHub are clients for that model API, so
they do not help either, despite the name.

## What is fragile, and why

Every item here cost a failed run.

**Playwright cannot see the machine.** `connect_over_cdp` lists page targets;
the machine is an Electron `<webview>`, which it does not surface. Attaching
with Playwright shows the app's renderer and nothing else. Raw CDP to the
webview's own websocket is the only route, which is why this library carries a
small protocol client instead of wrapping a browser automation framework.

**The websocket handshake needs no Origin header.** Chrome answers a DevTools
websocket carrying `Origin` with `403 Rejected an incoming WebSocket connection
from the http://127.0.0.1:9222 origin`, and names `--remote-allow-origins` in
the message. Relaunching the app with that flag works, and so does simply not
sending the header. This library sends none.

**One character-producing key event per character.** A `keyDown` carrying
`text` already inserts the character; adding a `char` event inserts it again
and every command arrives doubled -- `cclleeaarr;; ssttttyy --eecchhoo`. It
does not double every time, which is the dangerous part: the first runs look
correct and the approach looks safe until a long command is mangled.

**Screenshots need a generous timeout, and JPEG.** A PNG of a 1280x800 desktop
at device pixel ratio 2 is about a megabyte of base64 delivered in one
websocket message. At a 30 second timeout it fails intermittently; the same
frame as JPEG is roughly a seventh of the size. This library defaults to JPEG
at quality 70 and a 120 second timeout.

**Coordinates must be fractions.** The canvas backing store is the machine's
resolution, the element is laid out at whatever size the webview gives it, and
a screenshot returns at the device pixel ratio. Three scales. A fraction of the
canvas survives all three; a pixel offset read off a screenshot does not.

**Focus before typing.** Input goes wherever the machine's window manager has
focus. Click somewhere harmless first, or the command lands on the desktop
background and nothing happens -- silently.

**The terminal does not open on a single click.** The dock wants a double
click, and the launch takes a few seconds. A single click highlights the icon,
which looks like it registered.

## Secrets

`write_env_file` turns the terminal's echo off around the credential, creates
the file under `umask 077`, and writes it one line at a time with `printf`.

Two reasons, both learned the hard way. A secret typed with echo on is in every
screenshot taken during or after the run, and these screenshots get saved and
pasted elsewhere. And an env file read with `.` is *executed* by the shell, so
bash performs quote removal: a JSON credential written bare arrives with its
double quotes stripped and fails to parse, surfacing later as an unrelated-
looking error.

Verify with `describe_env_file`, which prints permissions, key names and a line
count, and never a value.

### Before you put a credential there

The machine is shared. The official documentation is explicit: *"All of your
Bots use the same cloud computer, sharing its files, browser sessions and app
logins."* Anything any Bot on the account can be persuaded to do reaches that
credential, and those Bots browse the web.

So send the narrowest thing that does the job. Deploying a publisher to one of
these machines, a repository deploy key is the right shape and a classic
personal access token is not: `repo` scope is read/write on **every**
repository the account can reach, and `workflow` can rewrite CI. A deploy key
is one repository, its private half never leaves the machine, and it can be
revoked on its own.

## Arrangement

| Path | What it is |
| --- | --- |
| `grokbot_cdp/app.py` | Find the installed app; start it with a debugging port; wait for it. |
| `grokbot_cdp/cdp.py` | Raw CDP client and target selection. |
| `grokbot_cdp/vm.py` | Read the screen, click, type, run a command. |
| `grokbot_cdp/secrets.py` | Put a credential on the machine without showing it. |
| `examples/` | A capability probe and a one-command runner. |

## Usage

```
pip install -r requirements.txt
python examples/probe_host.py          # what can this machine do
python examples/run_command.py "ls -la /workspace"
```

The app must be signed in already. This library does not handle login, and
should not: that is the one step worth doing yourself.

## Limitations

Output comes back as pixels. Nothing here reads a command's stdout, because
there is no channel that carries it -- have the command write somewhere you can
reach another way, or screenshot and read.

This is automation against an interface that was not offered as one. It works
today; a change to the app's internals can end it without notice, and none of
it is supported by xAI.

## Licence

MIT.
