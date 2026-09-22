# Roadmap

Current: **v0.1.0**

## v0.1.0 (current)

Feature names only. Why each one behaves the way it does lives in `reference/`, which
is the single home for those rules, and what changed lives in `CHANGELOG.md`.

- Target selection and attachment: find the machine's webview behind the desktop app
  and connect to it ([reference/cdp-transport.md](reference/cdp-transport.md)).
- Screen capture, with a liveness gate and a reconnect
  ([reference/screen-capture.md](reference/screen-capture.md)).
- Click, type and run a shell command
  ([reference/input-model.md](reference/input-model.md)).
- Credential delivery without echo, and verification that never prints a value
  ([reference/secrets.md](reference/secrets.md)).
- Offline tests for target selection, input shape, shell quoting, screen liveness,
  packaging, documentation agreement and repository hygiene, on Python 3.11, 3.12
  and 3.13.

## Planned

- **A channel that carries stdout.** Output comes back as pixels, so nothing here reads
  a command's exit status or its text and a caller has to arrange another route. This is
  the single largest gap.
- **A liveness probe that does not cost a frame.** `is_visible()` answers whether the
  picture is current. There is no cheap way to ask whether the machine itself is still
  the same one, short of reading `uptime` off the screen.
- **Publish to PyPI.** Installing from a git URL works and is what the README documents,
  but it makes the library awkward to depend on.
- **More than one session.** The client assumes a single app with a single machine view,
  and nothing is designed around an account with several Bots open at once.
