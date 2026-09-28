# csync Android UI and behavior contract

This is the implementation contract for the csync phone app. The owner selected the [round 4 screen and component choices](/Users/alcatraz627/Code/Claude/csync/docs/android-ui-round4-reconciliation.md) and then corrected the [round 5 clickthrough](/Users/alcatraz627/Code/Claude/csync/docs/android-ui-round5-plan.md). Those decisions remain binding. The [28-route HTML preview](/Users/alcatraz627/Code/Claude/csync/assets/android-ui-clickthrough/index.html) shows intended flows with fixture data; it is not the installed app.

## Outcome and navigation

The phone reaches named devices for sharing, Pi media and display, the Pi assistant, camera, and notes. Home presents observed device state and useful entry points. Media browsing, playback, and camera remain independent of Chat. The five primary areas remain Home, Media, Share, Chat, and More; the mock's additional routes sit within those areas.

One fixed-height breadcrumb row shows the route's ancestry and an icon for every visible crumb. Back always goes one route level up. Folder traversal and playback controls use their own actions. The top right may hold contextual icon actions with accessible names. Section tabs and bottom navigation retain their chosen treatments from round 4. Every route keeps its title, relevant subtitle, and available actions without a circular focus card.

## Shared state contract

| State | Owner and required transition |
| --- | --- |
| Named peer | The persisted peer roster and current reachability determine target labels and available actions. A send keeps the selected recipient visible through completion or failure. |
| Media item | Browsing or searching selects an item for a possible action. It does not change any playing session's title, output, position, or controls. File identity and URI grant survive menus, sharing, and cancellation. |
| Playback session | Pi screen and phone each own title, state, volume, speed, position, loop, rotation, revision, and pending commands. A command applies to the named output. Stop invalidates older pending callbacks. Observed external state supersedes stale local intent. |
| Delayed control | Rotate and Loop have separate two-second pending edits per session. Volume and speed apply immediately. Stop or a newer observed revision cancels stale edits. The UI shows pending versus observed state. |
| Share item | MIME and source determine additive actions. A failed transfer retains the item, recipient, and retry path. Sent history records both success and failure; Inbox remains received content. |
| Conversation | The selected thread owns title, favorite/archive status, messages, model, effort, draft, and attachments. Filters reflect thread metadata. New and renamed conversations appear in history. Tool results preserve their typed payload. |
| Note | Each note owns an identity, Markdown source, revision, and attachments. Create, read, edit, delete, and share use the same Pi-backed authority for phone and agent tools. A stale revision returns a conflict instead of overwriting silently. |

## Surface behavior

| Area | Required UI and interaction |
| --- | --- |
| Home and search | Name the Pi and peers, show observed status, expose Capabilities and recent work. Search preserves the selected result identity when routing to media, chat, or a received item. |
| Media and Pi display | Show source, search, folders, files, videos, history, and access. Folder menus add download. File menus add every supported download, chat, share, playback, or display action. The Pi display can show its cover gallery or media; camera-to-display is a separate measured pipeline. |
| Player | Full player has one transport row, configurable skip, and volume/speed/rotate/loop settings. The mini row and expanded panel show the same observed title, output, and state. Large text keeps all controls reachable. Android's media notification publishes observed sessions and accepts pause/resume/stop. |
| Share | Compose supports text, files, typed clipboard, named recipient, and sent history. Incoming Android shares expose actions for supported video, image, YouTube, Instagram, and files with editable playback defaults. Share egress lets a csync item reenter csync with the same type-driven actions. |
| Chat | Message text renders Markdown with selection and safe links; Copy uses source Markdown. Inline title edit, favorite/archive, message actions, rich typed tool details, and a confirmation-based Fork preserve thread identity. The one-line composer grows upward for longer drafts while conversation scrolling remains independent. Model and effort choices are enabled only for working provider capabilities and require Save or Send. Telemetry appears only when measured. Tools is a tab alongside All, Favorites, and Archived. |
| Camera, Appearance, and reference | Camera capture stops streaming when its tab closes. Appearance applies System/Light/Dark, sm/md/lg, seven colors plus persistent Custom across every activity and system bar. Assistant capabilities and Help use readable Markdown tied to available behavior. |
| Notes and Pins | Notes require Pi-backed CRUD, Markdown/GFM preview, plain/rich editing on one source, and sharing to a selected conversation or device. The Pi assistant gets authenticated note tools. Pins need URL/snippet, title, tags, and description. |

## Release and acceptance

The independent [mock indictment](/Users/alcatraz627/Code/Claude/csync/.claude/output/20260927-1515-android-ui-review/indictment.md) found 13 state and layout defects. The repaired preview has a targeted [regression probe](/Users/alcatraz627/Code/Claude/csync/assets/android-ui-clickthrough/verify-audit.mjs) for those transitions and a broader [route and journey probe](/Users/alcatraz627/Code/Claude/csync/assets/android-ui-clickthrough/verify.mjs). Browser results establish preview behavior only.

The installed app must be built, installed, and exercised on a phone or emulator. Acceptance includes light/dark, narrow and large text, full and mini player parity, Pi/phone command results, external playback changes, typed Android share intents, note conflicts, and persistence. The older media reliability, actual Pi frame rate, native Cast, widget, launcher, process, and performance checks remain in the [Android backlog](/Users/alcatraz627/Code/Claude/csync/docs/android-improvement-backlog.md).

The [independent all-route visual audit](/Users/alcatraz627/Code/Claude/csync/.claude/output/20260927-1648-all-routes-review/report.md) captured all 28 routes at standard and large text. Its three fixture findings led to scrollable section tabs with the selected tab visible, shorter current breadcrumb labels with middle levels omitted, and an inactive idle player. The targeted browser probe exercises those cases. Its first-view captures and fixture state do not establish Android behavior.

The release must produce a newer signed app version, stage its APK on the Pi, and complete **Tools → Update csync from Pi** on the phone. The Pi media service serves the APK at `/v1/app/apk` with the shared token; package identity, version, installer result, and opened updated app must be checked. The Notes feature must then hold two Pi-backed notes: a completed-work summary with screenshots and observed behavior, and a separate list of features the owner can try. Write only observed results into those notes.

## Current implementation status, 27 September 2026

| Area | Evidence and remaining check |
| --- | --- |
| Pi Notes | Token-gated CRUD, revision conflict, and PNG attachment tests passed locally and on the Pi in the earlier release. The two Pi-backed notes now cover 2.26 at revisions 13 and 10. The progress note has twenty-six screenshots, including installed 2.26 Home and Chat frames and explicitly labeled synthetic Chat fixture frames. The private Camera frame was kept local. The Pi assistant advertises its Notes tool. A live model call was rejected by automatic approval review because it would send private note titles to an external provider. |
| Android release | Version 2.26, code 28, is staged on the Pi with SHA-256 `96b513a1df75b7ba2a4f9833566b0389c68a063ffb7604c925c203c4d91e7d8a`. The 2.25 APK was backed up. The emulator installed 2.26 over 2.25 through More → Tools and diagnostics → Update csync from Pi; Android reported code28 and the app reopened. The owner's physical phone has not been checked. |
| Native Home, Media, Share, and Conversations | The 2.23 emulator renders the selected clickthrough's compact breadcrumb, section, and card hierarchy on these four screens. Home now checks the authenticated Pi media health route separately from assistant reachability; the updated emulator showed both reachable. Conversations' Tools tab loaded live declared Pi tools. Share's Android document picker selected a file and retained it after a send without a recipient. Delivery to an online peer, full Media item actions, and Home search beyond chat titles and destination routing remain open. |
| Native Notes, Tools, Camera, Player, and other UI | The staged 2.26 app renders a Notes list with title search and Pi revision labels, plus Preview, Rich, and Plain modes over the same Markdown source. More has Areas and Reference cards; Settings has a compact breadcrumb and keeps its older deeper controls. Tools renders live Pi health and an undervoltage warning. Camera rendered a live frame, with Pi status changing from one viewer while open to zero after leaving. The idle full player opens from Pi display and shows output, observed state, seek, transport, and settings; its skip interval persisted through the update. Home cards are one column at narrow width or large text. Chat has icon-only message Copy/Fork preview and conversation Favorite/Archive actions; an early and late preview showed the expected bounded bubbles using a disposable fixture. Fork creation, Pins, Settings depth, and other owner callouts remain open. Both Pi media drives were absent, so active player behavior, rotation, and loop remain open. Light and Dark normal-size Home and idle Player were rendered; narrow 1.3× checks covered Home and idle Player in Dark. |

The earlier Home and Media reliability changes remain in the native app. Their phone and YouTube actions still need interaction checks in the new layout.

## Android 2.27 candidate, 28 September 2026

| Check | Observed state |
| --- | --- |
| Pi service | The token-gated Pins endpoint is live. Local media tests passed 27 cases. A disposable Pin was created, edited, shared, and deleted through Android. The Pi now reports zero Pins and two Notes. |
| Android | 2.27/code29 built with SHA-256 `2e30e5fa3e6326dba8c4d48b32cfe369ded38ecacabb90d510d22837f1c76d0d`. A direct emulator install reported code29, and its Pi Notes list rendered both current note revisions and the corrected search label. Incoming web URL sharing kept the URL in new Pin, Note, and Chat drafts in the local build. |
| Pi APK update | Tailscale SSH requested an additional login check before the existing 2.26 APK could be backed up. The Pi still serves 2.26/code28, confirmed by downloading it and checking its SHA-256 against `96b513a1df75b7ba2a4f9833566b0389c68a063ffb7604c925c203c4d91e7d8a`. The 2.27 in-app updater path has not run. |
| Pi Notes | The progress note is revision 15 with 33 images. The features-to-try note is revision 11. Both distinguish local 2.27 behavior from the current Pi release. |

At that earlier 2.27 checkpoint, the Pins list supported web URLs, titles, and descriptions; snippets and tags remained open. The current 2.29 status appears below. Android sharing of images, media, and notes back into csync still needs the type-driven routes and live interaction checks. The owner's physical phone has not been checked.

## Current release and page review, 28 September 2026

The [native completion and page review list](/Users/alcatraz627/Code/Claude/csync/.claude/output/20260928-android-native-parity-tasks.md) tracks each page, shared control pattern, runtime check, and final review gate. The earlier 2.27 candidate section above is historical.

| Check | Observed state |
| --- | --- |
| Pi APK | Android 2.29/code31 is staged on the Pi at `/home/alcatraz627/.local/state/csync/csync-hub-update.apk`; SHA-256 is `a51796a1bdcc004235fb2dbbcdfce1ee93a15f7e2b9eb0cbb07b490e83a4f391`. The exact prior 2.28 APK is backed up at `/home/alcatraz627/.local/state/csync/csync-hub-update-2.28-before-2.29.apk`. |
| In-app update | The emulator installed the exact backed-up Pi 2.28 APK, then used More → Tools → Update csync from Pi. Android reported 2.29/code31 afterward, and Home reopened with its saved Pi connection. The owner's physical phone has not been checked. |
| Pi Pins | The Pi media service serves authenticated URL and text Pins with optional title and tags. The 29 media service tests passed. The installed app saved a shared text snippet, searched its fallback title, edited it, opened its detail, shared it through Android Sharesheet back into csync, and deleted the disposable item. Tags were stored on the Pi, but visible tags and revision-conflict UI still need review. |
| Pi Notes | Authenticated reads confirmed the progress note at revision 17 with 47 screenshots and the features-to-try note at revision 13. Both describe observed 2.29 behavior and remaining limits. |
| Home page review | The corrected Home has installed light/dark, normal/large, and scrolled captures. The parent inspected them against the current plain-headline clickthrough, checked the controls and return from Media, and fixed Media's separate bottom bar to show icons only. `android-ui-home` callouts gate exited 0 after fresh rechecks. This code is in the Pi's 2.29 APK. Pi-offline runtime behavior and the separate Search route remain open. |
| Pins follow-up | The installed 2.29 candidate showed saved tags on Pin list and detail. A revision-conflict probe kept the edit dialog and draft open and showed an error. After refreshing, the disposable Pin was deleted through the app; authenticated Pi GET returned zero Pins. This code is in the staged 2.29 APK. |

Image, media, and note round-trip sharing, full clickthrough route parity, physical-phone behavior, mounted-drive playback, and visible HDMI output remain open.
