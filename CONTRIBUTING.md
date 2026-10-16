# Contributing

This library automates an interface nobody offered as one. Most of what is in
it is not design, it is the residue of a run that went wrong: the doubled
keystrokes, the missing Origin header, the JPEG default. So the rule that
matters most here is about evidence, not style.

## Clone it and arm the hooks

```
git clone https://github.com/DaizeDong/grokbot-cdp
cd grokbot-cdp
pip install -e .
git config core.hooksPath .githooks
```

**That last line is not optional and cannot be done for you.** `core.hooksPath`
is local configuration, so it is not in the repository and a fresh clone does
not have it. Without it none of `.githooks/` runs, every argument below about
what the hooks refuse is unreachable.

The gates live in two local checkouts outside this repository, fleet-guards and
fleet-style, named by `git config fleet.guards` and `git config fleet.style`.
When either setting is unset or its checkout has no hook, the `.githooks/` shims
refuse the commit instead of running nothing. Set them rather than working
around it.

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
mid-session or a credential if echo was on.

Three things stand between a frame and the public, and it is worth knowing what
each one is worth. `.gitignore` covers the default output names, and `.gitignore`
is advice: `git add -f` walks straight through it. `data_boundary` does not help
here at all, and this is measured rather than assumed, since force-adding a
`.jpg` and running it prints `clean` and exits 0: its run-shape check knows
ledgers and dated files, and an image is not a shape it recognises. What does
refuse is `.githooks/pre-commit`, which blocks any staged image outright, so a
clone that never armed the hook has nothing else in its way.

`pii-guard` runs as a pre-commit and pre-push hook. **Never use `--no-verify`.** If a hook blocks you, the content is the
problem. And never pipe `git commit` into something that truncates its output:
a severed pipe has destroyed a hook's exit status here before, and the commit
went in looking clean.

## Commits

End every commit message with a `Co-Authored-By:` trailer if the change was
co-written. Use a heredoc or `-F` for a multi-line message.

Commit author emails must be noreply-form GitHub addresses
(`<numeric-id>+<username>@users.noreply.github.com`). A real address in the
author line is invisible to any file scan and is what the identity gate in the
hooks exists to catch.
