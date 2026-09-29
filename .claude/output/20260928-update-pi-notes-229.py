"""Record the observed Android 2.29 Pi update checkpoint in the two Pi notes."""

import json
from pathlib import Path
from urllib.request import Request, urlopen


HOST = "http://100.65.188.9:8792"
TOKEN = (Path.home() / ".config/csync/mesh.token").read_text().strip()
PROGRESS = "/v1/notes/507509ca-bcf5-423d-830e-36be58e8bf62"
TRIAL = "/v1/notes/058033af-9bd2-4ab1-a3c4-a2953b6a6a5c"
SCREENSHOTS = (
    "/private/tmp/csync-229-update-from-228.png",
    "/private/tmp/csync-229-home-after-pi-update.png",
    "/private/tmp/csync-media-icons-only.png",
    "/private/tmp/csync-pin-tags-list.png",
    "/private/tmp/csync-pin-tags-detail.png",
    "/private/tmp/csync-pin-conflict-draft.png",
    "/private/tmp/csync-pin-tags-cleanup.png",
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
if progress["revision"] != 16 or trial["revision"] != 12:
    raise RuntimeError("Pi notes changed; inspect revisions before updating")
for screenshot in SCREENSHOTS:
    if not Path(screenshot).is_file():
        raise RuntimeError("Missing screenshot: " + screenshot)

old_release = "**Current Pi release: csync 2.28 (versionCode 30).**"
if progress["body"].count(old_release) != 1:
    raise RuntimeError("Progress release label changed")
body = progress["body"].replace(
    old_release, "**Current Pi release: csync 2.29 (versionCode 31).**", 1)
body += """
## Android 2.29 from Pi — 28 Sep 2026

- **Pi update and retained connection:** The Pi stages csync 2.29/code31 with SHA-256 `a51796a1bdcc004235fb2dbbcdfce1ee93a15f7e2b9eb0cbb07b490e83a4f391`. Its prior 2.28 APK was backed up. I installed the exact Pi-served 2.28/code30 APK on the emulator, used More → Tools → Update csync from Pi, then Android package info reported 2.29/code31. The updated app reopened on Home with its saved Pi connection and current authenticated reachability. This tests the emulator updater; the physical phone is still unchecked.
- **Home and navigation:** The local Home revision follows the current plain-headline clickthrough. The owner-feedback checks for section chevrons, card icon/title alignment, spacing, top bar, device row ends, and five icon-only bottom tabs have fresh installed passes. Media has its own bottom bar and was corrected too. Normal/large text and light/dark Home frames were captured. Search remains a narrower chats/devices dialog; the separate mixed-result Search page and Pi-offline runtime remain open.
- **Pins:** A local installed build showed saved tags in Pin list and detail. A deliberately stale edit received Pi `PIN_CONFLICT`; the editor stayed open with the local title and a visible conflict message. I reopened the Pin at its newer revision and deleted it through the app. Authenticated Pi `GET /v1/pins` returned zero items afterward. These Pins captures were made on the local 2.29 candidate before staging; that candidate's code is in the staged 2.29 APK. Full Notes/Pin page parity is still open.
- **Screenshots attached with this section:** Tools update entry before the 2.28→2.29 update; updated 2.29 Home; Media's icon-only bottom bar; local-candidate Pin tags in list and detail; conflict with retained draft; cleaned Pin list. No private camera image is included.
- **Remaining checks:** Native parity across all 28 clickthrough routes, media drives/playback and physical HDMI, image/media/Note circular sharing, external-provider behavior, and the owner's physical Android phone remain open. The Pi reported undervoltage during Tools inspection.
"""

old_trial = "The Pi stages csync **2.28 (versionCode 30)**."
if trial["body"].count(old_trial) != 1:
    raise RuntimeError("Trial release label changed")
trial_body = trial["body"].replace(
    old_trial, "The Pi stages csync **2.29 (versionCode 31)**.", 1)
trial_body += """

### New in 2.29 to try

- Update through More → Tools and diagnostics → Update csync from Pi. Android app info should report 2.29. The emulator completed this from the Pi's 2.28 APK; your physical phone remains to be checked.
- Open Home in Light and Dark, then increase system text size. Try the Devices, Capabilities, and Pick up chevrons. The five bottom tabs show icons only, including in Media.
- In More → Pi Notes, create a text or URL Pin with tags. The list and Pin detail show `#tags`. Search can find a tag. Edit, share, and delete the Pin. If a different device edits the Pin first, Save keeps your draft visible and asks you to reopen the newer version rather than overwriting it.
- Share a text snippet or web URL to csync from another Android app, choose a Pin, Note, or unsent Chat draft, and inspect the content before saving or sending. The emulator checked a text Pin's round trip through Android Sharesheet back to Chat.

Search across media/transfers and circular sharing for app-owned images, media, and Notes are still in progress. Physical Pi screen playback needs a mounted drive and visible display check.
"""

saved = request(PROGRESS, "PUT", {
    "title": progress["title"], "body": body,
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
