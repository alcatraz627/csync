# csync phone app: every page, state and transition

<!-- sessions: catch-mock-7f@2026-10-01 -->

The map in `android-app-model.md` §3 says where each place lives. This document
says what each place can be in, and every way in and out, read from the code on
2026-10-01 (csync-hub `a4577f1`). Places are pages the breadcrumb names; views are
looks at one place; sheets are drawers over a place; states are what a place shows
depending on the Pi and the phone. Arrows: `→` opens, `←` Back goes to, `⇢` a
non-page entry (widget, tile, notification, share menu, search result).

## The tree

```
csync (MainActivity holds Home, Share, Chat, Tools, Settings, Camera, More;
       Media, Notes, Search and From another app are their own screens)
│
├─ Home                                   bar place 1
│   states: Pi online · Pi offline · Pi not connected (lead line at the foot)
│   sections: Pick up (last conversation, last played) · Play Ask Send Camera · Your devices · status line
│   ├─ Search                             child; scopes All Media Chats Files Devices
│   │   states: nothing typed · searching · N results · nothing matches (scope) · Pi unreachable
│   │   result ⇢ Media item sheet · Conversation · Received item sheet · Device sheet
│   └─ Your devices (sheet: every peer with Online or Offline, tap selects the recipient)
│
├─ Media                                  bar place 2 (MediaActivity)
│   views: Files · Videos · History · Access          (a view is never a level)
│   Files states: drives list · folder (Folders, Files, Up row, Load more) · empty folder · drive unreadable
│   Videos states: N videos · none · scanning
│   History states: rows "output · stopped at" · empty
│   Access states: SMB and FTP addresses · drives Connected or Disconnected · shared folders
│   sheets: item (7a list) · folder (Open, slideshow, Copy path) · Switch source · resume (Resume on Pi, Start over, the other output) · File details
│   foot: Pi screen row while idle ("Nothing is playing on the Pi screen"), mini player row while playing
│   ├─ Pi screen                          child; the Pi output
│   │   states: idle (cover + sources) · loading · playing · paused · buffering · finished · showing (image, text, slideshow, document, camera, screen) · offline · failed
│   │   idle sections: From the Pi (Photos as a slideshow, The Pi camera) · From this phone (A file, A link, A note, This phone's screen) · This screen (Cover image, Display)
│   │   playing controls: seek, rewind, pause, forward, skip length, stop, favorite; Volume, Speed, Rotate, Loop tiles
│   │   showing controls: Stop showing; for a document Previous, Page N of M, Next
│   │   landscape: picture left, controls right
│   │   sheets: slideshow (folder, seconds) · note (pick) · link (field) · Cover image (Fit, Rotate, Choose) · Display (name, rotate, starting volume, sound) · skip length
│   │   └─ Full screen video               a mode of the player, Back returns to the player
│   └─ This phone                         child; the phone output
│       states: idle (Browse Media) · loading · playing · paused · finished · failed
│       also: PhonePlaybackService notification (pause, stop) survives the page
│
├─ Share                                  bar place 3
│   states: recipient row Online or Offline · composing · sending · sent rows Delivered or Failed
│   sheets: Choose who receives · Attach a file (system picker) · Use the clipboard
│   ├─ Received                           child; newest first, "N items", empty state
│   │   item → item sheet (7a: Show on Pi screen, Open, Send…, Save, Share)
│   └─ From another app                   own screen (ShareActivity), entered only from Android's share sheet
│       kinds: video, audio, image, PDF, other file, text, link, YouTube link, several files
│       states: choosing · sending to the Pi · not shown (retry) · connect the Pi first
│       ← returns to the sharing app
│
├─ Chat                                   bar place 4
│   views: All · Favorites · Archived · Tools
│   states: list · searching · empty · Pi unreachable
│   └─ Conversation                       child
│       states: reading · typing (heading folds) · reply being written (Send is Stop) · jump row on a long reply · renaming · find open · suggestions open
│       sheets: attach (file, photo, Pi file) · model and effort · fork · item sheet on a message's file
│       landscape: heading folds
│       ⇢ reply notification (ChatService) opens it; reply from the notification
│
└─ More                                   bar place 5
    sections: On the Pi · Looking after things · Reference
    ├─ Pi camera                          child
    │   states: live preview · no camera · Pi offline · recording (dot)
    │   actions: take photo, start and stop recording, Open captures, Show on Pi screen
    │   └─ Captures                       grandchild; grouped by day, empty state
    │       item → item sheet (7a plus Delete)
    ├─ Notes                              own screen (NotesActivity); views Notes · Pins
    │   states: list · searching · empty · Pi unreachable
    │   ├─ Note                           read; files under "In this note", pictures
    │   │   └─ Edit                       a page, Save in the body and the top bar; Add to this note (picture, file)
    │   └─ Pin                            read; Link and Text fields on edit
    │   sheets: new note or pin · item sheet on a note file · Take out of this note
    ├─ Tools                              child
    │   states: lead line (Everything is ready · One thing needs a look · Power is low · The Pi cannot be reached · not connected)
    │   sections: Raspberry Pi (Media, Assistant, Camera, Power, Drives) · This phone · This app (update row: Up to date, Install N, from the Pi)
    │   ├─ Process monitor                grandchild; readings rows, or "Open Shizuku"
    │   └─ Widgets                        grandchild; launcher widgets, Quick Settings tiles, share menu entries, Added or Not added
    ├─ Settings                           child; sections fold in place
    │   sections: Connection (row) · Playback (Starting volume, Resume, Loop, Skip length, Display) · Assistant (Model, providers, Pi commands) · Appearance (Theme, Text size, Primary colour, App icon)
    │   └─ Connection                     grandchild; addresses, token, Receive on this phone, phone name
    ├─ Assistant guide                    child; what the assistant can do
    └─ Help and about                     child; version
        └─ Design system                  grandchild; every kit part drawn once
```

## Transitions, each direction

### The bottom bar

| From | Tap | Lands on |
|---|---|---|
| anywhere | Home | Home root |
| anywhere | Media | Media, the view it was left on |
| anywhere | Share | Share compose (Received closes) |
| anywhere | Chat | Chat list (a conversation closes) |
| anywhere | More | More root |

The highlighted icon is the bar place that owns the current place: More stays
lit on Settings, Tools, Notes, the camera; Media stays lit on the Pi screen page.

### Back, both the arrow and the gesture

| Where | Back goes |
|---|---|
| a sheet | closes it |
| full screen video | the player page |
| Pi screen or This phone | Media |
| Search | Home |
| Received | Share |
| Conversation (find or suggestions open) | closes that first, then the list |
| Conversation | Chat list |
| Captures | Pi camera; Pi camera → More |
| Note edit | the note; Note or Pin → the list; Notes list → More |
| Process monitor or Widgets | Tools; Tools → More |
| Connection | Settings; Settings → More |
| Assistant guide, Help and about | More |
| a bar place other than Home | Home (gesture only; the arrow is absent) |
| Home | leaves the app (gesture only) |
| From another app | the app that shared the item |
| a page reached sideways from an item, or from a Search result | the page the item or the result was on |

Inside a page the gesture shrinks the page as it moves (predictive back); at a
root the system's own preview runs. Back never stops playback, never walks a
folder and never changes a view.

A page reached sideways is a visit: the crumbs still climb that page's own path
(the Media crumb on a visited Pi screen page opens Media, the Notes crumb opens
the list), and once a crumb or a bar place is tapped the visit is over and Back
walks the path as usual. A visit never leaves a second copy of a place underneath.

### Down, from each place

| From | To | How |
|---|---|---|
| Home | Search | the search icon in the top bar |
| Home | Media, Chat (new), Share, Camera | the four action tiles |
| Home | Conversation, the player | the Pick up rows |
| Home | Tools | the status line |
| Home | Your devices sheet | the devices row |
| Media | Pi screen | the Pi screen row at the foot, or Play on Pi screen from an item |
| Media | This phone | Play on this phone from an item |
| Media | folder | a folder row; Up row climbs, inside the list |
| Pi screen | full screen video | the picture while a film plays |
| Share | Received | the top bar action |
| Share | recipient sheet | the recipient row or the top bar action |
| Chat | Conversation | a row, or the new conversation action |
| More | Pi camera, Notes, Tools, Settings, Assistant guide, Help and about | rows |
| Pi camera | Captures | the top bar action or the Captures row |
| Tools | Process monitor, Widgets | rows under This phone |
| Settings | Connection | the Connection row; other sections fold in place |
| Help and about | Design system | a row |
| Notes | Note, Pin | rows; the plus makes a new one |
| Note | Edit | the edit action |

### Sideways: the same item, wherever it appears

Every item kind offers the same list (model §7a): Play on Pi screen, Play on this
phone, Show on Pi screen, Open, Open in VLC, Set as the Pi cover, Copy the text,
Send to a device, Send to a conversation, Add to a note, Save as a pin, Save on
this phone, Share with another app. Those choices move between places:

| Choice | Lands on |
|---|---|
| Play on Pi screen | Pi screen page (via From another app for a file on the phone) |
| Show on Pi screen | sends in place; the page stays |
| Play on this phone | This phone page, or the system player |
| Send to a device | From another app, device chosen |
| Send to a conversation | Conversation with the item attached |
| Add to a note | Note edit with the item |
| Save as a pin | Pin edit |
| Share with another app | Android's share sheet |

### In from outside the app

| Entry | Lands on |
|---|---|
| launcher shortcut New chat | Conversation, new |
| launcher shortcut Send | Share compose |
| launcher shortcut Camera | Pi camera |
| widget Media remote (Pause, Stop act in place; tap) | Pi screen page |
| widget Pi status | Tools |
| widget Camera glance | Pi camera |
| widget Ask the Pi | Conversation, new |
| widget xkcd | the comic in the browser |
| Quick Settings tile Pi screen | stops what plays, else Media |
| Quick Settings tile Pi camera | Pi camera |
| Quick Settings tiles Clipboard, Last photo | send in place, no page |
| share menu csync | From another app, choosing |
| share menu Send to Pi screen | Pi screen page, playing or showing at once |
| share menu Send to your last device | sends, then From another app |
| chat reply notification | Conversation (reply from the notification stays there) |
| playback notification | This phone page |
| screen share notification Stop | ends sharing, no page |
| search result | Media item sheet, Conversation, Received item sheet, Device sheet |

### Out to the Pi screen, and back

The Pi screen changes state without a page changing: Play, Show, the slideshow,
the note, the link, the camera, the phone screen and a document all move it
from idle to playing or showing; Stop, Stop showing, a film ending, a slideshow
replaced, or the phone ending its share move it back to idle, where the cover
returns. Every page that shows the Pi's state (Home's lead line, Media's foot
row, the Pi screen page, the Media remote widget, the Pi screen tile) reads the
same `/v1/player/pi` and follows it.
