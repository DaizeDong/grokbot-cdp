# The machine model: a container, not a VM

This shard answers three questions about the host on the other end of a Grok Bot session: what kind of machine it actually is, what it does not have, and what survives when it goes away. Read it before you plan anything that assumes the machine is a persistent VM, before you try to schedule recurring work on it, and before you decide where a long job's output should live. Everything here was measured against a real Bot, not read from documentation. Where a number appears, it came from a run.

## What it is

Grok Bot presents the account's "cloud computer" as a machine with a browser, a filesystem and a terminal. Probed from inside, it is a container, not a VM.

| | |
| --- | --- |
| PID 1 | `tini` |
| `systemctl` | not installed |
| `cron`, `crond`, `systemd-run` | none present |
| restarts | yes, unannounced; observed `up 9 min` mid-run |
| `sudo` | passwordless |
| network | outbound works; `github.com` answers 200 |
| python3 | 3.13 |
| `ssh`, `ssh-keygen` | absent until you `apt-get install openssh-client` |
| disk | 126G, a few percent used |
| user, cwd | `box`, `/workspace` |
| delivery | noVNC over HTTPS, 1280x800 |

Two consequences matter more than the rest, and each of them is a place where the machine looks like something it is not.

## There is no scheduler

No systemd and no cron means a recurring job has to be a foreground loop you start yourself. There is no timer to install, no crontab to edit, and no `systemd-run` to fire a one-shot from.

The dangerous part is that the machine does not look that way at first. `/etc/systemd/system` exists as an empty directory. A directory that exists is the normal sign that a unit file goes there, so "install a timer" looks available: you can write the unit, put it in the right place, and see it sitting on disk exactly where it should be. The illusion holds right up until `systemctl` is not found, which is the first and only point at which anything pushes back. Nothing before that step fails, so a plan built on scheduling can be several steps deep before it collapses.

The rule: on this machine, a recurring job is a process you start and keep alive. Write it as a loop, start it in the foreground or under `nohup`, and treat its liveness as something you have to check yourself, because nothing on the machine is watching it for you.

## The container outlives the app, but not indefinitely, and it restarts without telling you

The container's lifetime is not tied to the desktop app on your own machine. Uptime kept counting while the desktop app was closed for a day, and the session reattached to the same machine after the client machine rebooted. So a `nohup`-ed loop does survive both of those: closing the app does not kill your work, and neither does rebooting your own computer.

What it does not survive is the container itself being restarted, and that happened mid-run. The session reconnected to a machine reporting `up 9 min`. Every open window was gone. A background loop's pid file pointed at nothing. Untracked working files were deleted, while the git checkout and its log files came back.

Nothing announced any of it. The session said `Connected` throughout, so the client side gave no signal at all. The loop's own log simply stopped, and a log that stops reads as a quiet period rather than as a loop that ended. That is the shape of the failure worth remembering: the restart is silent on every channel you would normally watch, and the evidence it leaves behind is indistinguishable from nothing having happened.

### What that one restart does and does not establish

Be explicit about how much is known here. The survival list above, the git checkout and its log files coming back while untracked working files were gone, came from ONE observed restart. It is a single data point, not a characterised behaviour.

The tidy explanation offers itself immediately: that the restore respects `.gitignore`, keeping what git would keep and discarding what git would discard. That explanation is ruled out. `.venv` is not in `.gitignore`, and it did not survive. So whatever rule governs the restore, it is not the one that would have been easiest to believe, and no other rule has been established in its place.

One observation does not establish a rule. The operating instruction is therefore the conservative one: assume nothing untracked survives. Do not reason from the single observation about which specific files came back, and in particular do not reason that a file will survive because a similar file did once.

## How to work with a machine like this

Treat the machine as able to restart at any moment, without warning and without any signal on the connection.

Anything generated there is not safe until it has been pushed somewhere else. A result that exists only on the machine is a result you may lose, and you will not be told when you lose it.

Any long job should publish incrementally rather than at the end. A job that writes its output once, at completion, has a window of its entire runtime during which a restart destroys all of it. A job that publishes as it goes loses only the last interval.

Check `uptime` when you reattach. It is the only thing that says a restart happened. `status()` will not tell you, the log will not tell you, and the files that came back will not tell you either.
