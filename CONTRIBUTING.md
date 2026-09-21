# Contributing

This library automates an interface nobody offered as one. Most of what is in
it is not design, it is the residue of a run that went wrong: the doubled
keystrokes, the missing Origin header, the JPEG default. So the rule that
matters most here is about evidence, not style.

## Clone it with the submodules

```
git clone --recursive https://github.com/DaizeDong/grokbot-cdp
cd grokbot-cdp
pip install -e .
pip install pytest
```

The gates live in two submodules, `guards/` and `style/`. A plain `git clone`
leaves those directories present and **empty**, which is the dangerous shape:
git finds no hook there and runs nothing, exit 0, in silence. `.githooks/`
carries a stub that refuses the commit instead and tells you to run
`git submodule update --init --recursive`. Do that rather than working around
it.

Those two directories are other repositories. Do not edit anything inside
them from here.

## State only what you measured

Every number in the README came from a run against a real Bot: the container
facts, the screenshot sizes, the timeout that failed intermittently. If you
add a claim, add the run it came from, and if you are reporting behaviour
rather than measuring it, say which.

The same applies in reverse. If something in the README no longer matches a
real Bot, that is a valuable change even with no code in it. The app's
internals are not ours and can move without notice.

## Never put a real identifier in this repository

It is public. A machine id, a real hostname, an API key or token, the account
an app is signed in as: none of these belong in code, tests, documentation or
a commit message. Use the placeholders that are already here,
`grok-bot-vm-<id>` and `.invalid` hostnames.

Screenshots are the specific hazard of this project. A frame from one of these
sessions shows whatever was on that machine, which may be a terminal
mid-session or a credential if echo was on. `.gitignore` covers the default
output names, and `tests/test_repo_hygiene.py` is the control that `git add -f`
cannot walk through.

`pii-guard` runs as a pre-commit hook and again in CI, where it cannot be
skipped. **Never use `--no-verify`.** If a hook blocks you, the content is the
problem. And never pipe `git commit` into something that truncates its output:
a severed pipe has destroyed a hook's exit status here before, and the commit
went in looking clean.

## Tests

```
python -m pytest tests/ -q
```

Everything in the suite is offline. There is no fixture for a real Bot and
there should not be one, so the tests cover the parts that can be reasoned
about without a machine: target selection, the shape of the input events,
shell quoting, the repository hygiene checks and the packaging metadata.

Two conventions, both from the same failure. A check must be **able to fail**:
before comparing a list, assert the list is not empty, because a parser that
matched nothing prints exactly the same green as a genuine pass. And a check
should test the thing that ships, not a convenient stand-in: the CI
hollow-run assertion was verified against real `pytest` output and against an
empty run, not against a string someone wrote by hand.

If you add code, add a test. If you change behaviour that a comment explains
as "this cost a failed run", keep the explanation attached to it.

## Commits

End every commit message with a `Co-Authored-By:` trailer if the change was
co-written. Use a heredoc or `-F` for a multi-line message.

Commit author emails must be noreply-form GitHub addresses
(`<numeric-id>+<username>@users.noreply.github.com`). A real address in the
author line is invisible to any file scan and is what the identity gate in the
hooks exists to catch.
