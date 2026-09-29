"""Mark the observed Android 2.30 in-app installer result in the Pi notes."""

import json
from pathlib import Path
from urllib.request import Request, urlopen


HOST = "http://100.65.188.9:8792"
TOKEN = (Path.home() / ".config/csync/mesh.token").read_text().strip()
PROGRESS = "/v1/notes/507509ca-bcf5-423d-830e-36be58e8bf62"
TRIAL = "/v1/notes/058033af-9bd2-4ab1-a3c4-a2953b6a6a5c"
SCREENSHOTS = (
    "/private/tmp/csync-230-update-entry-20260928.png",
    "/private/tmp/csync-230-home-after-update-20260928.png",
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
if (progress["revision"], trial["revision"]) != (18, 14):
    raise RuntimeError("Pi notes changed; inspect revisions before updating")
for screenshot in SCREENSHOTS:
    path = Path(screenshot)
    if not path.is_file() or not 8 <= path.stat().st_size <= 1024 * 1024:
        raise RuntimeError("Missing or oversized screenshot: " + screenshot)

progress_old = "The 2.29→2.30 in-app installer run is pending the UI agent's emulator handoff. The earlier 2.28→2.29 in-app run passed on the emulator; the physical phone remains unchecked."
progress_new = "The emulator installed the exact Pi-backed 2.29 APK, then used More → Tools → Update csync from Pi to reach 2.30/code32. Android's installed base.apk SHA-256 matches this served file. Home reopened with the Pi badge Online. The physical phone remains unchecked."
trial_old = "The emulator's 2.29→2.30 installer test is still pending; the physical phone is also pending. The older 2.28→2.29 updater run succeeded on the emulator."
trial_new = "The emulator completed the 2.29→2.30 in-app update from the Pi. Android reports 2.30/code32 and the installed APK hash matches the Pi file. The physical phone remains unchecked."
if progress["body"].count(progress_old) != 1 or trial["body"].count(trial_old) != 1:
    raise RuntimeError("Pending installer text changed; inspect notes")

progress_body = progress["body"].replace(progress_old, progress_new, 1)
progress_body += "\nTwo more screenshots show the 2.29 Update csync from Pi entry and 2.30 Home after the Pi-served update.\n"
trial_body = trial["body"].replace(trial_old, trial_new, 1)

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
