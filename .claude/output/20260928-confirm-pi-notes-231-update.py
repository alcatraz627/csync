"""Record the observed 2.30-to-2.31 Pi updater result in both live Pi notes."""

import json
from pathlib import Path
from urllib.request import Request, urlopen

HOST = "http://100.65.188.9:8792"
TOKEN = (Path.home() / ".config/csync/mesh.token").read_text().strip()
PROGRESS = "/v1/notes/507509ca-bcf5-423d-830e-36be58e8bf62"
TRIAL = "/v1/notes/058033af-9bd2-4ab1-a3c4-a2953b6a6a5c"
SCREENSHOTS = (
    "/private/tmp/csync-231-update-entry-20260928.png",
    "/private/tmp/csync-231-home-ready-20260928.png",
    "/private/tmp/csync-231-tools-after-update-20260928.png",
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
if (progress["revision"], trial["revision"]) != (20, 16):
    raise RuntimeError("Pi notes changed; inspect revisions before updating")
for screenshot in SCREENSHOTS:
    path = Path(screenshot)
    if not path.is_file() or not 8 <= path.stat().st_size <= 1024 * 1024:
        raise RuntimeError("Missing or oversized screenshot: " + screenshot)

progress_body = progress["body"] + """

### 2.30→2.31 in-app update checked on emulator

I installed the exact Pi-backed-up 2.30 APK (code32; SHA-256 `1b8878a5c7d2c4bb9c9e1726b3a683aaf76654fc57cebaea001e3091f756a84e`) over the developer build, then tapped More → Tools → Update csync from Pi. Android reported 2.31/code33 afterward. Pulling the installed `base.apk` gave SHA-256 `6281d3e359e6c2bd58aa444311b9d5784e71d2c049478d4a4519fa490cec3436`, exactly the Pi-served 2.31 file. Home reopened with Raspberry Pi Online; authenticated mesh, assistant, and media endpoints all returned HTTP 200. Light theme, large text, and coral accent remained selected. Tools no longer showed the old literal `null` power status; it currently reports an observed Pi undervoltage warning. The app loaded these two Pi Notes at revisions 20 and 16 after installation. The attached emulator screenshots show the 2.30 update entry, 2.31 Home, and 2.31 Tools power warning. A physical-phone installation and visible HDMI output remain unchecked.
"""
old_trial = "The previous 2.29→2.30 in-app run passed on the emulator; the 2.30→2.31 run and the physical phone remain unchecked at this note revision."
new_trial = "The emulator completed the exact Pi-served 2.30→2.31 in-app update: Android reports 2.31/code33 and its installed APK hash matches the Pi file. The physical phone remains unchecked."
if trial["body"].count(old_trial) != 1:
    raise RuntimeError("Trial update wording changed; inspect before editing")
trial_body = trial["body"].replace(old_trial, new_trial, 1)
trial_body += "\n\nThe Pi currently reports undervoltage in Tools. Check its power supply before relying on screen playback.\n"

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
