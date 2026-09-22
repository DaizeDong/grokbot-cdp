# The input model: what happens to a click or a keystroke

This shard answers one question: what happens to a click or a keystroke between
the caller and the remote window manager, and which of those steps silently
swallows it or quietly duplicates it. Read it before writing anything that
clicks, types, or sends a command to the machine. If you are here to find out
why a command arrived doubled, why a click seemed to do nothing, or why a
coordinate read off a screenshot landed in the wrong place, you are in the right
place.

## The chain an input event travels

An input event does not go to the machine. It goes to a Chrome DevTools
Protocol websocket, which hands it to an Electron `<webview>`, which is running
noVNC, which translates it into RFB and sends it across the network to the
session host, which replays it into a container's window manager at 1280x800.

Four translations, and every one of them is an opportunity to lose the event or
to produce two events where you meant one. None of them reports an error when it
does. The only evidence you ever get is pixels coming back, and pixels take a
screenshot to read.

That is the shape of every rule below: the failure is silent, so the rule has to
be followed unconditionally rather than checked for afterwards.

## One character-producing key event per character

A `keyDown` that carries `text` already inserts the character. Adding a `char`
event inserts it a second time. Every command then arrives doubled, and it looks
like this:

```
cclleeaarr;; ssttttyy --eecchhoo
```

The dangerous part is not the doubling. It is that it does not double every
time. The first runs look correct, the approach looks safe, and the failure
arrives later on a long command, which is exactly the command whose mangled form
is hardest to recognise and most expensive to have executed.

So: one character-producing event per character. A `keyDown` carrying `text` is
that event. Do not also send a `char`.

## Coordinates must be fractions

There are three different scales in play at once, and a pixel offset is only
correct in one of them.

The canvas backing store is the machine's resolution. The `<webview>` element is
laid out at whatever size the app gives it, which is not that resolution. A
screenshot comes back at the device pixel ratio, which is a third number again.

A fraction of the canvas survives all three, because it is defined relative to
the surface rather than in any one of these coordinate systems. A pixel offset
read off a screenshot does not survive any of them: it is expressed in
screenshot pixels, and nothing downstream is in screenshot pixels.

So clicks take fractions. If you measured something on a screenshot, divide by
the screenshot's own dimensions before you send it.

## Focus before typing

Input goes wherever the machine's window manager has focus. Not wherever you
last clicked in the app, not wherever the terminal is on screen: wherever the
remote window manager decided focus is.

If focus is on the desktop background, the command lands on the desktop
background, and nothing happens. Nothing reports an error, because from the
protocol's point of view every event was delivered successfully. It was.

So click somewhere harmless first, and then type.

## The terminal does not open on a single click

The dock wants a double click, and the launch takes a few seconds after it.

A single click highlights the icon. A highlighted icon is exactly what a
successful launch looks like in the instant before the window appears, so a
single click reads as "it registered, the window is coming" and then the window
never comes. Double click, then wait for the window rather than assuming it.

## Multi-line scripts: base64 them, do not type them

Typing a multi-line script into the terminal is fragile for two separate
reasons, and the doubling above is only the first.

The second is focus drift. The window which has focus can change between the
focus click and the typing. When that happens, the script does not fail: part of
it lands in one window and the rest lands in another, so a script can arrive in a
different terminal with its head eaten. What executes is a suffix of what you
meant to run, which is a strictly worse outcome than nothing executing, because a
suffix can be a valid command.

The robust transport is to base64 the script into a single line, send that one
line, and decode it on the far side. One line of `[A-Za-z0-9+/=]` has nothing
left to mangle: there is no newline for focus to drift across, no quote for a
shell to remove, and no character whose doubling produces something that still
parses. The decode either produces the script or fails loudly.
