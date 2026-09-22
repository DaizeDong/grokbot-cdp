# 2026-09-22: applying the house repository spec to a library

This repository was brought in line with Skill Repo Spec v1, which was written for
Claude Code skill repositories. This one is a Python library. Seven of its eleven
chapters apply as written, four need adapting, and a handful of individual requirements
are refused outright because meeting them would mean claiming something untrue.

This file is the record of those decisions, so the next person auditing this repository
against the spec finds a reasoned position rather than silence, and can argue with it.
It is dated evidence, not a rule: the rules live in `reference/`, the version history in
`CHANGELOG.md`.

## Refused, because meeting them would be a false claim

**No `.claude-plugin/plugin.json`.** Chapter 1 makes it mandatory so that even a
single-skill repository stays installable with `/plugin install`. There is nothing here
for that command to install: no `SKILL.md`, no skill entrypoint, no agent behaviour at
all. A manifest would be advertising rather than metadata. The honest equivalent is
`pyproject.toml`, which carries the same fields the spec cares about, and which a test
already pins to a single version literal.

**No `claude-code`, `claude-plugin`, `claude-skill`, `claude` or `skill` topic.**
Chapter 6 calls these part of a nine-topic identity fingerprint that every repository
carries. Five of the nine are false here. The product this library drives is xAI's Grok
Bot; the repository contains no Claude integration of any kind, and `skill` on GitHub
reads as "Agent Skill", which this is not. Putting them on would pollute the search
results for the repositories where they are true.

Of the remaining four, `ai`, `ai-agent` and `agent` are honest and are carried. `llm` is
not: this library makes no model call and contains no prompt or model code. It drives a
desktop application over a debugging protocol. So the base nine is read here as a base
three, and the domain topics do the rest of the work.

**No `SKILL.md`, and no L0 or L1 layer.** Chapter 11's first two layers are the
frontmatter description and the per-invocation preamble, both of which exist because a
skill pays for them on every turn. A library is imported, not invoked, so there is
nothing to pay and nothing to budget. L2 through L5 apply unchanged and are implemented:
`reference/` holds each rule, the two READMEs are a tour, and `ROADMAP.md` plus
`CHANGELOG.md` are the only places a version number appears in prose.

**No load-budget workflow.** `style/ci/load-budget` measures what a `SKILL.md` costs to
load. With no `SKILL.md` it would report that there is nothing to measure, on every
commit, forever. A check that cannot fail is worse than no check, because it teaches
people that green means something.

## Adapted, because the intent survives and the letter does not

**The orange type badge.** Chapter 3 fixes the first badge as `Claude Code Skill`
linking to the Claude Code docs. The slot is kept, because a reader should learn what
kind of thing this is from the first line of badges, but its content is
`Python 3.11+` linking to `pyproject.toml`, which is both true and the thing a visitor
actually needs to know.

**Version consistency.** Chapter 7 asks for four copies of the version kept in step.
There is exactly one literal, `grokbot_cdp.__version__`; `pyproject.toml` derives from
it through `[tool.setuptools.dynamic]`, and `tests/test_packaging.py` fails if anyone
writes a second one. The three prose copies that the spec's shape creates, in the README
badge, the ROADMAP heading and the CHANGELOG entry, are checked against that literal by
a test rather than by memory.

**No `.pii-allow`.** Chapter 8 lists it as a required file. It is a list of real
third-party identifiers this repository is allowed to contain, each with an argued
reason. This repository contains none, and an empty allowlist asserts nothing. It is
created when there is a first exemption to argue for, and not before.

**The data-boundary toolchain.** Chapter 9 requires `tools/datadir.py`,
`tools/test_datadir.py`, `tools/data_boundary.py` and `tools/make_fixtures.py` in every
repository. They are present through the `guards` submodule and run in CI, which is the
newer fleet form; vendoring a second copy is what the submodule migration existed to
stop. This repository declares no DATA and no FIXTURE, and `.dataclass.json` argues both
conclusions rather than defaulting to them.

## The one real hole the audit found, and how it is closed

`data_boundary`'s run-shape check is blind to this repository's only real-run output.
The check knows jsonl ledgers, dated files under output directories and database files.
The only thing this library can produce is a **screenshot**, and a bare `.jpg` is not a
shape it recognises. Measured on a scratch copy: `git add -f screen.jpg` followed by
`python guards/tools/data_boundary.py` prints `clean, 28 tracked files carry no
real-run shape` and exits 0.

`tests/test_repo_hygiene.py` does catch it, and it ran only in CI, which is one step
after the frame is public. For a frame of a live machine that is one step too late, and
`CONTRIBUTING.md` described that test as the control `git add -f` could not walk
through, which overstated it.

So the question is asked at the commit boundary too, in `.githooks/pre-commit`, in
shell, with no dependency that can be absent. The pre-commit framework chain that the
stub already offers was not used for this: it is skipped when its binary is missing,
which is the right shape for a formatter and the wrong shape for a control whose whole
job is to be there.

## What was measured, and where

| Claim | How it was checked |
| --- | --- |
| The guards are armed, not merely present | `data_boundary.py` and `pii_guard.py --tree --history` both run clean in the checkout; force-adding a jsonl ledger under `metrics/` turns the first one red, so check 4 is not vacuous here |
| No CI gate step passes silently when its file is absent | Every step in `guards/ci/pii-guard/action.yml` uses `test -f X || exit 1`; the only `if [ -f ... ]` in this repository guards the optional pre-commit framework, not a gate |
| The style gate had never run | `style/` was pinned and its own 28 tests passed, and a full-tree grep for "dash" outside the submodules returned nothing: no workflow called it |
| One dash violation existed | `python style/tools/dash_guard.py --tree` flagged `README.md:25`, a full-width dash in the Chinese paragraph that has since moved to `README_CN.md` and been rewritten without it |
| The version agrees everywhere | One literal at `grokbot_cdp/__init__.py`, derived by `pyproject.toml`, asserted by `tests/test_packaging.py` |
