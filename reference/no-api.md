# Why there is no Grok Bot API

This shard answers one question: why does this library drive a desktop application over the Chrome DevTools Protocol instead of calling an endpoint? It also names the two near misses that anyone searching for a Grok Bot API will find first, and explains why neither of them is the thing they are looking for.

If you arrived here looking for the mechanics of the CDP attach, the noVNC webview or the input quirks, this is the wrong shard.

## The only documented interface is a chat message

Grok Bot gives each account a persistent cloud machine with a browser, a filesystem and a terminal. The official documentation describes exactly one way to use that machine: *"You work with a Bot by messaging it."*

That sentence is the whole interface. There is no REST endpoint, no webhook, no CLI, and nothing that creates a Bot or reads its output programmatically. The absence is not a gap in the published reference that a little more searching will close. It is the shape of the product: a Bot is something you talk to, and the machine behind it is reachable only through that conversation.

This is why the library exists. The machine is real, persistent and useful, and the only supported path to it runs through a human typing into a chat box. The desktop application that hosts that chat box is Electron, so it will open a Chrome DevTools port, and the machine itself turns out to be delivered through a noVNC session inside one of the application's webviews. Attach to that target and you can read the screen and send input. That is the other way in, and it is the only other way in.

## Near miss one: api.x.ai

`api.x.ai` is the **model** API. It serves the Grok models for text generation, and it has no relationship to Bots or to their machine. Nothing you can send to that endpoint creates a Bot, addresses an existing one, reaches the filesystem of the cloud computer, or reads anything that happened on it.

The name makes it look like the general purpose entry point to everything xAI offers, which is what makes it a near miss rather than an obvious dead end. An account that works against `api.x.ai` and an account that owns a Bot can be the same account, and the key that authenticates one of them tells you nothing about the other. Credentials working is not evidence that you are talking to the right service.

## Near miss two: the grok-cli packages

Several packages on GitHub are published under the name `grok-cli`. They are clients for the model API described above. They wrap `api.x.ai`, and so they do not help either, despite the name.

The word "cli" in the package name reads as "a command line way to drive the thing", which is precisely what someone automating a Bot is hoping to find. It is not that. Installing one of these gives you a terminal front end for chatting with a model, and no access at all to a Bot or its cloud computer. Do not read the existence of these packages as evidence that a Bot API exists somewhere and that these packages talk to it.

## What follows from this

Because there is no API, everything this library knows came from a run against a real Bot rather than from documentation. Where a number appears in this repository, it was measured. Nothing here is inferred from an interface contract, because there is no interface contract to infer from.

It also means the automation is unsupported by construction. This is automation against an interface that was not offered as one. It works today, and a change to the application's internals can end it without notice. That is a consequence of there being no API, not a defect that a later version fixes.
