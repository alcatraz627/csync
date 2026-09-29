"""Record the staged Android 2.30 checkpoint in the two live Pi notes."""

import json
from pathlib import Path
from urllib.request import Request, urlopen


HOST = "http://100.65.188.9:8792"
TOKEN = (Path.home() / ".config/csync/mesh.token").read_text().strip()
PROGRESS = "/v1/notes/507509ca-bcf5-423d-830e-36be58e8bf62"
TRIAL = "/v1/notes/058033af-9bd2-4ab1-a3c4-a2953b6a6a5c"
SCREENSHOTS = (
    "/private/tmp/csync-note-share-reentry-20260928.png",
    "/private/tmp/csync-share-failure-retry-20260928.png",
    "/private/tmp/csync-widgets-v4-light-normal.png",
    "/private/tmp/csync-tools-v3-dark-normal.png",
)


def request(path, method="GET", data=None):
    headers = {"X-Csync-Token": TOKEN}
    if isinstance(data, dict):
        data = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    elif data is not None:
        headers["Content-Type"] = "image/png"
    with urlopen(Request(HOST + path, data=data, headers=headers, method=method), timeout=30) as response:
        return json.load(response)


progress = request(PROGRESS)["note"]
trial = request(TRIAL)["note"]
if (progress["revision"], trial["revision"]) != (17, 13):
    raise RuntimeError("Pi notes changed; inspect revisions before updating")
for screenshot in SCREENSHOTS:
    path = Path(screenshot)
    if not path.is_file() or not 8 <= path.stat().st_size <= 1024 * 1024:
        raise RuntimeError("Missing or oversized screenshot: " + screenshot)

old_progress = "**Current Pi release: csync 2.29 (versionCode 31).**"
old_trial = "The Pi stages csync **2.29 (versionCode 31)**."
if progress["body"].count(old_progress) != 1 or trial["body"].count(old_trial) != 1:
    raise RuntimeError("Release labels changed; inspect notes before updating")

progress_body = progress["body"].replace(
    old_progress, "**Current Pi release: csync 2.30 (versionCode 32).**", 1)
progress_body += """
## Android 2.30 staged on Pi — 28 Sep 2026

- **Update file:** Pi `/v1/app/apk` serves csync 2.30/code32, 5,853,935 bytes, SHA-256 `1b8878a5c7d2c4bb9c9e1726b3a683aaf76654fc57cebaea001e3091f756a84e`. The former 2.29 APK is backed up. The 2.29→2.30 in-app installer run is pending the UI agent's emulator handoff. The earlier 2.28→2.29 in-app run passed on the emulator; the physical phone remains unchecked.
- **Tools:** The native Tools/Process/Widgets pages now have separate health, metric, Current, and Ideas sections. The Pi health refresh showed authenticated media reachability and an undervoltage warning. Dark/light normal/large captures and route/Back checks exist. Live Shizuku process sampling and the xkcd launcher widget are still unchecked. The later Widget star, chevrons, and row dialogs were installed after the first page handoff; full parent acceptance remains open.
- **Image round trip:** A screenshot attached to this very Pi Note opened full size in Android, left through Android Sharesheet, and reentered csync's incoming Image actions. Save on phone produced a PNG with exactly the same SHA-256 as the shared original. Set as Pi cover changed the Pi wallpaper through its authenticated API; the previous JPEG was restored to its original hash immediately afterward. Physical HDMI output was not observed.
- **Failure handling:** A deliberately missing image URI failed before any peer transfer. The sender retained the named recipient and item, reported 0 of 1 confirmed sent, and offered Retry remaining. Retrying showed the same failure. No peer was contacted. Successful peer delivery remains unchecked.
- **New screenshots:** Incoming image choices, retained failed-send dialog, Widgets in Light, and Tools live status in Dark. They show the installed emulator checkpoint, not the owner's physical phone.
- **Still open:** Search as a full route, the full 28-route native acceptance pass, Media light/dark action matrix, Chat and Camera page reviews, Notes layout parity, owner callout rechecks, physical phone, and visible HDMI output.
"""

trial_body = trial["body"].replace(
    old_trial, "The Pi stages csync **2.30 (versionCode 32)**.", 1)
trial_body += """

### More to try in 2.30

- From the progress Pi Note, tap a screenshot. View it full size or share it through Android Sharesheet. Pick csync again to see Save on this phone, Set as Pi cover, and Send to device. Saving preserves the original PNG bytes. Setting the cover replaces active Pi playback after a confirmation.
- Open More → Tools. Recheck live Pi media and power status. Open Process monitor for its metric grid and honest Shizuku availability, and Widgets for the built xkcd widget plus clearly marked planned ideas. Tap rows for explanations. Launcher widget refresh and live Shizuku sampling have not been verified.
- Share a web URL or image from another app into csync. Choose a named peer and inspect the selected destination before sending. If a file cannot be read, the failed-send dialog keeps the item and recipient for Retry remaining. An actual peer transfer has not been tested in this checkpoint.
- The Pi now serves 2.30 from the in-app update endpoint. The emulator's 2.29→2.30 installer test is still pending; the physical phone is also pending. The older 2.28→2.29 updater run succeeded on the emulator.
"""

saved = request(PROGRESS, "PUT", {
    "title": progress["title"], "body": progress_body,
    "expectedRevision": progress["revision"],
})["note"]
for screenshot in SCREENSHOTS:
    request(PROGRESS + "/images", "POST", Path(screenshot).read_bytes())
images = request(PROGRESS + "/images")["images"]
trial_saved = request(TRIAL, "PUT", {
    "title": trial["title"], "body": trial_body,
    "expectedRevision": trial["revision"],
})["note"]
print(json.dumps({"progress_revision": saved["revision"],
                  "progress_images": len(images),
                  "try_revision": trial_saved["revision"]}))
