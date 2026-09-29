"""Record the observed 2.31 staging, Search and Notes paths in the live Pi notes."""

import json
from pathlib import Path
from urllib.request import Request, urlopen

HOST = "http://100.65.188.9:8792"
TOKEN = (Path.home() / ".config/csync/mesh.token").read_text().strip()
PROGRESS = "/v1/notes/507509ca-bcf5-423d-830e-36be58e8bf62"
TRIAL = "/v1/notes/058033af-9bd2-4ab1-a3c4-a2953b6a6a5c"
SCREENSHOTS = (
    "/private/tmp/csync-search-navfix-light.png",
    "/private/tmp/csync-search-media-exact-light.png",
    "/private/tmp/csync-notes-parent-v3-light-lg.png",
    "/private/tmp/csync-notes-parent-v3-detail-light-lg.png",
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
if (progress["revision"], trial["revision"]) != (19, 15):
    raise RuntimeError("Pi notes changed; inspect revisions before updating")
for screenshot in SCREENSHOTS:
    path = Path(screenshot)
    if not path.is_file() or not 8 <= path.stat().st_size <= 1024 * 1024:
        raise RuntimeError("Missing or oversized screenshot: " + screenshot)

old_progress = "**Current Pi release: csync 2.30 (versionCode 32).**"
old_trial = "The Pi stages csync **2.30 (versionCode 32)**."
if progress["body"].count(old_progress) != 1 or trial["body"].count(old_trial) != 1:
    raise RuntimeError("Release labels changed; inspect notes before updating")

progress_body = progress["body"].replace(
    old_progress, "**Current Pi release: csync 2.31 (versionCode 33).**", 1)
progress_body += """
## Android 2.31 staged on Pi — 28 Sep 2026

- **Update file:** Pi `/v1/app/apk` now serves csync 2.31/code33, 5,881,731 bytes, SHA-256 `6281d3e359e6c2bd58aa444311b9d5784e71d2c049478d4a4519fa490cec3436`. The former 2.30 APK was backed up with its original hash. Authenticated download returned HTTP 200 and the exact new hash. The 2.30→2.31 in-app installer run is pending the shared emulator handoff; the physical phone remains unchecked.
- **Search:** The installed native Search opened from Home. `mp4` returned 15 live Pi results. Choosing one opened that exact Media file and its output actions; Back kept the query. A saved Chat result opened its exact conversation, and a named Device result opened Share with that recipient selected. The Files inbox route, no-result/offline paths, and full dark/size matrix remain open. A Search bottom-bar color mismatch was fixed and reinstalled in Light.
- **Notes:** The installed Pi Notes list showed both live notes, revisions 15 and 19, and zero Pins in Dark/medium and Light/medium/large. New note/Cancel, note detail, Rich/Cancel, `try` search, and More navigation worked. Save, Pins, revision conflict, offline behavior, and the current-build screenshot gallery still need installed checks. Source now guards duplicate Save and preserves a draft on Pi revision conflict; that source change is build-checked only.
- **Attached emulator screenshots:** Search after the bottom-bar fix; an exact Pi media result selected in Media; Notes list and note detail in Light/large. These are emulator evidence, not physical-phone proof.
"""
trial_body = trial["body"].replace(
    old_trial, "The Pi stages csync **2.31 (versionCode 33)**.", 1)
trial_body += """

### Try the 2.31 Search and Notes checkpoint

- Tap Search on Home. Type a media name such as `mp4`; choose a result to see the exact file in Media and its playback/share choices. Back should keep your query. The emulator saw 15 matches on the Pi; your drive contents may differ.
- In Search, try Chats and Devices. A saved conversation opens its thread. Choosing a named device opens Share with that recipient selected; check its availability before sending. The emulator checked routing but did not send a peer transfer.
- Open Notes from Home. Search for `try`, open this note, switch Preview/Rich/Plain, and use Cancel to return without saving. New note also opens an editor. Saving a new note, Pin editing, and revision conflict still need a current installed check.
- Update csync from Pi under More → Tools when ready. The Pi now serves 2.31/code33. The previous 2.29→2.30 in-app run passed on the emulator; the 2.30→2.31 run and the physical phone remain unchecked at this note revision.
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
