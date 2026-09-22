# Reading the screen

This shard answers one question: when is the picture you just captured actually a picture of the machine right now, and how does it lie when it is not. It covers the size of a frame and the timeout it needs, the hidden-window freeze that returns an old frame without saying so, and the smaller-frame route through the canvas that survives a capture timeout but not the freeze.

## A frame is large enough to break the transport

`Page.captureScreenshot` returns the whole image as base64 inside a single websocket message. There is no chunking and no stream: either the whole frame arrives in that one message or the call fails.

A PNG of a 1280x800 desktop at device pixel ratio 2 is about a megabyte of base64 delivered in that one message. At a 30 second timeout it fails intermittently. The word that matters is intermittently: it succeeds often enough that a short probe run looks like proof the transport is fine, and then a longer run starts losing captures for no reason visible from the call site.

The same frame as JPEG is roughly a seventh of the size, and at that size it has not failed.

So the defaults are JPEG at quality 70 and a 120 second timeout. Ask for `fmt="png"` only when the pixels matter more than the reliability, for example when something is being read at the pixel level rather than looked at, and accept that the call is now the fragile one.

The rule is that the format and the timeout are one decision, not two. A PNG at a short timeout is the combination that fails, and it fails in the shape that is hardest to attribute: some captures return, some do not.

## A minimised window freezes the screen, and nothing says so

The host stops sending framebuffer updates to a hidden webview. On a desktop that means the app window is minimised or fully covered. The canvas is not cleared and not marked: it simply keeps whatever it last painted.

This is the dangerous failure on this transport, because every signal you would naturally check keeps saying that everything is fine:

- Input keeps working the whole time. Clicks and keystrokes go through, and they take effect on the machine.
- `status()` keeps answering `Connected (encrypted)`, because it is connected. The status line is reporting the RFB session, and that session is healthy.
- Successive screenshots come back byte-identical.

That last one is what actually does the damage. Two identical frames read as "nothing happened on the machine", which is a perfectly ordinary thing for a desktop to do. They do not read as "I am looking at an old picture". Two rounds of a real run were read off a stale frame this way: commands were sent, the commands ran, and the screen that was used to decide what to do next was from before any of it.

The rule is that a screenshot is only evidence about the present if the webview is visible. `screenshot()` refuses on a hidden webview and raises `StaleFrameError` rather than returning a frame that cannot be distinguished from a current one. `is_visible()` is the underlying check, `document.visibilityState`, and it is the only thing in the whole session that answers the question honestly. `allow_stale=True` exists for the case where an old frame is genuinely what is wanted, and it is the only way past the refusal.

The recovery is `reconnect()`. It reloads the viewer and reattaches, which restarts the framebuffer stream. It touches the viewer, not the machine: the container keeps running and the session comes back to the same one. Use it when the screen has stopped changing but commands still take effect, which is exactly the signature above. Restoring the app window works too, when there is someone at the machine to restore it.

## Reading the canvas instead of capturing the page

When `Page.captureScreenshot` times out, `Runtime.evaluate` on the same target stays responsive. The target is not wedged; it is the size of the one screenshot message that is the problem.

The noVNC canvas is same-origin, so it can be read directly. `canvas.toDataURL` of type `image/jpeg` returns a frame about an order of magnitude smaller than the capture, which is small enough to come back over a websocket message that a full capture cannot fit into. That makes it the workaround that survives a capture timeout.

State the limit plainly, because the two failures above look similar from the outside and this workaround only addresses one of them. Reading `toDataURL` reads the same canvas that a capture reads. It is therefore subject to exactly the same staleness when the page is hidden: a hidden webview stops receiving framebuffer updates, the canvas keeps its last painted frame, and `toDataURL` will hand that old frame over just as happily as a capture would. It is a workaround for the message size, not for the freeze. If the window is hidden, the answer is still `reconnect()` or restoring the window, and a smaller frame of the same stale pixels is not an improvement over a large one.
