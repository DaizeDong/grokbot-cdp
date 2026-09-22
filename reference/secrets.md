# Secrets: putting a credential on the machine

This shard answers two questions. How do you get a credential onto a Grok Bot's cloud machine without painting it on the screen, and what does putting it there actually expose. Read it before any run that carries a token, a key or a password across to the machine. If you only want to know which API calls exist, `grokbot_cdp/secrets.py` is the place; this is the reasoning behind their shape.

## The mechanism

`write_env_file` turns the terminal's echo off around the credential, creates the file under `umask 077`, and writes it one line at a time with `printf`.

Verify with `describe_env_file`. It prints permissions, key names and a line count, and never a value. That is the whole point of having a separate verification call: the natural way to check a file you just wrote is to `cat` it, and `cat` on a credential file puts the credential back on the screen, which is exactly the outcome the write path spent its effort avoiding.

## Why echo is suppressed: two reasons, both learned the hard way

**A secret typed with echo on is in every screenshot taken during or after the run.** Output on this machine comes back as pixels, so screenshots are not an optional debugging nicety here, they are the normal way to see what happened. They get saved, and they get pasted elsewhere. A credential echoed into the terminal is not only visible at the moment it is typed, it stays in the scrollback, so a screenshot taken minutes later, for an entirely unrelated reason, still carries it. There is no way to unsee a frame that has already been filed somewhere.

**An env file read with `.` is executed by the shell, so bash performs quote removal.** The dot command does not parse the file as data, it sources it, which means every line goes through the ordinary shell word-splitting and quote-removal rules. A JSON credential written bare arrives with its double quotes stripped, and then fails to parse. The failure does not look like a quoting failure. It surfaces later as an unrelated-looking error, at whatever point downstream code first tries to read the value as JSON, far away from the write that actually damaged it. That distance between cause and symptom is what makes this worth building into the write path rather than leaving to the caller to remember.

## Before you put a credential there

**The machine is shared.** The official documentation is explicit: *"All of your Bots use the same cloud computer, sharing its files, browser sessions and app logins."*

Read that as a security statement rather than a convenience one. It means the blast radius of a credential on this machine is not the one Bot you are driving. Anything any Bot on the account can be persuaded to do reaches that credential, and those Bots browse the web. A Bot reading an attacker-controlled page is a Bot reading attacker-supplied instructions, and it has a filesystem and a terminal on the same machine where your credential is sitting.

So send the narrowest thing that does the job. The question to ask is not "does this credential work", it is "if this credential were read by something hostile tomorrow, what is the largest thing it could do".

**A worked example: deploying a publisher.** Deploying a publisher to one of these machines, a repository deploy key is the right shape and a classic personal access token is not.

A classic personal access token with `repo` scope is read/write on **every** repository the account can reach, not just the one being published to, and that includes private repositories the account merely has access to rather than owns. A token carrying `workflow` can rewrite CI, which means it can change what runs on every push, with whatever secrets that CI already holds.

A deploy key is one repository. Its private half never leaves the machine, so it is not a bearer token that keeps working anywhere it is copied to. And it can be revoked on its own, without disturbing anything else the account is doing, which matters because the decision to revoke should be cheap enough that you make it on suspicion rather than on proof.
