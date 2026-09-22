# Changelog

All notable changes to this project are documented here (Keep a Changelog style).

## [Unreleased]

### Changed

- **docs: unify repo structure (Skill Repo Spec v1).** README split into an English
  authority and a Chinese counterpart with matching sections, the protocol and
  operational invariants moved out of the README into `reference/`, and the mandatory
  `ROADMAP.md` and `CHANGELOG.md` added. No functional version bump: nothing about the
  library changed.

  Six requirements of that spec are deliberately not met, every one of them because
  meeting it would claim something untrue of a Python library, and all six are argued
  in `docs/2026-09-22-spec-adaptation.md` rather than left as a silent omission: no
  `.claude-plugin/plugin.json`, no `SKILL.md` and therefore no L0 or L1 documentation
  layer, no load-budget workflow, no `.pii-allow` until there is an exemption to argue
  for, and five of the nine fingerprint topics refused. The base nine is read here as a
  base three: `ai`, `ai-agent` and `agent` are carried; `claude-code`, `claude-plugin`,
  `claude-skill`, `claude` and `skill` are not, and `llm` is judged against because this
  library makes no model call.

### Added

- **A commit-boundary block on images, and the reason it is not left to CI.** The only
  real-run output this repository can produce is a frame of a live remote machine, and
  `data_boundary` is blind to it: force-adding a `.jpg` and running the guard prints
  `clean` and exits 0, measured here rather than assumed. `tests/test_repo_hygiene.py`
  does catch it and runs in CI, which is one step after the frame is public.
  `.githooks/pre-commit` asks the same question before the commit, in shell, with no
  dependency that can be absent.

- **`tests/test_docs.py`.** The version appears in one literal and three pieces of prose,
  the two READMEs are meant to be one document in two languages, and a pointer to a
  missing file is worse than no pointer. Nothing held any of that except attention. Each
  assertion was poisoned once to confirm it fails for its own reason.

## [0.1.0] - 2026-09-21

### Added

- Initial release: drive the cloud machine behind a Grok Bot from Python over the
  Chrome DevTools Protocol. Target selection, screen capture, input, shell commands,
  and credential delivery with echo suppressed.

### Fixed

- **A hidden webview returned its last painted frame with nothing to say so.** The host
  stops sending framebuffer updates to a hidden page, so the canvas keeps whatever it
  last drew while input keeps working and the session keeps reporting `Connected`.
  Three successive screenshots came back byte-identical, which reads as "nothing
  happened on the machine" rather than "this picture is old", and two rounds of a real
  run were read off a stale frame before the cause was found. `screenshot()` now raises
  `StaleFrameError` before capturing, and `reconnect()` restarts the stream.

### Changed

- **The claim that the container outlives the app was corrected.** It survives the app
  closing and the client machine rebooting, which is what had been measured. It does
  not survive being restarted itself, which had not been: a restart mid-run left
  `up 9 min`, every window gone, a background loop's pid file pointing at nothing, and
  untracked working files deleted while the git checkout and the logs came back.
