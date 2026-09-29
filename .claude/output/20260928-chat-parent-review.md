# Chat native page review — pending installed pass

The current clickthrough requires the History filters All, Favorites, Archived, and Tools in one tab row, with Tools content switching inline. A fresh isolated browser probe exercised that behavior. The native app still needs a whole-frame and interaction review.

Source checks in `/Users/alcatraz627/Code/csync-hub/app/src/main/java/com/csync/hub/MainActivity.java` found Markwon rendering, selectable message text, and link movement at lines 1781–1812. Copy and Fork actions at lines 1835–1846 use 48dp targets and spoken labels, but draw their symbols as Unicode text. Inspect those controls against the owner's icon requirement before claiming the page. Source inspection does not prove that links and text selection work together in installed user and assistant bubbles.

After the agent hands off Chat, install its APK and test:

1. Same-row History filters; rename, favorite, archive, and delete.
2. Rich Markdown and a real tappable link in user and assistant bubbles. Select part and all of a message.
3. Separate Copy and Fork actions, then fork preview and confirmation.
4. Long draft expansion, independent transcript scroll, model and effort capability, and draft retention through navigation.

Capture light/dark, normal/large whole frames and one long transcript. Record PASS/FAIL/UNRUN for each item and the relevant owner callouts.

Verdict: UNRUN. The agent has not handed off the installed Chat page.

Interim visual comparison: I inspected the current 390px mock `/private/tmp/csync-reference-20260928/chat-history-light.png` and installed agent capture `/private/tmp/csync-appwide-final-chat-light-normal.png`. The native page shows an honest zero-thread state and icon-and-label filters, consistent with the latest owner tab-icon callout. Its search remains a bare underlined input with much taller surrounding spacing than the mock's rounded scoped field. The mock places New chat and Settings in the page body; the native capture shows a top-right plus, so both actions and their return paths need a live check. No Chat page verdict follows from these images.

I also inspected the current Conversation mock `/private/tmp/csync-reference-20260928/chat-view-light.png` and the installed live thread `/private/tmp/csync-appwide-final-chat-message-settled-light.png`, plus the installed Copy/Fork, fork preview, and draft captures in `/private/tmp/csync-appwide-final-chat-actions-light-normal.png`, `/private/tmp/csync-appwide-final-chat-fork-preview-light.png`, and `/private/tmp/csync-appwide-final-chat-draft-light.png`. Native Copy/Fork icons and a fork preview are visible, but the page has two tall header rows and substantial empty space before messages; the mock has one compact breadcrumb row and a smaller title/action area. The native composer is also much taller, and raw tool JSON is clipped in the thread. The current Conversation visual parity verdict is FAIL. I sent the agent these specific hierarchy corrections while keeping its work active. Link clicking, selection, and complete assistant response remain UNRUN by the parent.
