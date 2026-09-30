"""Which screen is plugged into the Pi, and how the owner wants each one driven.

The owner moves the Pi between a monitor and a projector, so every screen gets a
stable key and its own remembered settings. The key comes from the screen's EDID
(maker, model and serial) when the kernel has one, and from the HDMI port plus
its mode when it does not, which is the case for the forced-mode HDMI0 today.
"""

from __future__ import annotations

import re
from pathlib import Path

from .library import MediaError


# What a screen gets until the owner changes it: the volume and rotation every
# playback used before screens were remembered, so nothing changes on its own.
# The cover fills the screen edge to edge, the way it was shown before it could be framed.
DEFAULT_SETTINGS = {"rotate": 0, "startVolume": 0, "sound": "display", "coverFit": "cover", "coverRotate": 0}
SOUND_OUTPUTS = ("display", "headphones")
# How the cover meets the screen's edges: cropped to fill, whole with bars, or pulled to fit.
COVER_FITS = ("cover", "contain", "stretch")
EDID_HEADER = b"\x00\xff\xff\xff\xff\xff\xff\x00"


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")[:120]


def parse_edid(data: bytes) -> dict | None:
    """Read the maker, model, serial, name and native size from a screen's EDID block."""
    if len(data) < 128 or data[:8] != EDID_HEADER:
        return None
    word = (data[8] << 8) | data[9]
    maker = "".join(chr(((word >> shift) & 0x1F) + 64) for shift in (10, 5, 0))
    if not re.fullmatch(r"[A-Z]{3}", maker):
        maker = "UNK"
    product = data[10] | (data[11] << 8)
    serial_number = int.from_bytes(data[12:16], "little")
    name = serial_text = None
    size = None
    for offset in (54, 72, 90, 108):
        block = data[offset:offset + 18]
        if block[0] or block[1]:
            if size is None:
                width = block[2] | ((block[4] & 0xF0) << 4)
                height = block[5] | ((block[7] & 0xF0) << 4)
                if width and height:
                    size = (width, height)
        elif block[3] in (0xFC, 0xFF):
            text = block[5:18].split(b"\n", 1)[0].decode("cp437", "replace").strip()
            if block[3] == 0xFC:
                name = name or text or None
            else:
                serial_text = serial_text or text or None
    serial = serial_text or (str(serial_number) if serial_number else "")
    return {"maker": maker, "product": product, "serial": serial, "name": name, "size": size}


def _port_label(connector: str) -> str:
    """Name the port the way it is printed on the Pi: HDMI-A-1 is HDMI0."""
    match = re.fullmatch(r"HDMI-A-(\d+)", connector)
    return f"HDMI{int(match.group(1)) - 1}" if match else connector


def scan(drm_root: Path) -> list[dict]:
    """Every screen the kernel reports as connected, first HDMI port first.

    mpv draws on the first connected connector, so the first entry is the
    screen playback appears on.
    """
    found = []
    for status in sorted(drm_root.glob("card*-HDMI-*/status")):
        folder = status.parent
        try:
            if status.read_text().strip() != "connected":
                continue
        except OSError:
            continue
        connector = folder.name.split("-", 1)[1] if "-" in folder.name else folder.name
        try:
            edid = parse_edid((folder / "edid").read_bytes())
        except OSError:
            edid = None
        mode = None
        try:
            first = (folder / "modes").read_text().split()
            match = re.match(r"(\d+)x(\d+)", first[0]) if first else None
            if match:
                mode = (int(match.group(1)), int(match.group(2)))
        except OSError:
            pass
        port = _port_label(connector)
        if edid:
            display_id = "edid-" + _slug(f"{edid['maker']}-{edid['product']:04X}-"
                                         f"{edid['serial'] or edid['name'] or 'unknown'}")
            name = edid["name"] or f"{edid['maker']} {edid['product']:04X}"
            size = mode or edid["size"]
        else:
            display_id = "port-" + _slug(f"{connector}-{mode[0]}x{mode[1]}" if mode else f"{connector}-nomode")
            name = f"{port} screen"
            size = mode
        found.append({"id": display_id, "name": name, "port": port,
                      "size": f"{size[0]} by {size[1]}" if size else None,
                      "pixels": size})
    return found


def validate_update(body: dict) -> tuple[str | None, dict]:
    """Check a change to one screen, naming the first field that is wrong."""
    for key in body:
        if key not in ("name", "settings"):
            raise MediaError("DISPLAY_INVALID", f"{str(key)[:40]} is not a screen field", 400, str(key)[:40])
    name = None
    if "name" in body:
        name = body["name"]
        if not isinstance(name, str) or not name.strip() or len(name) > 80:
            raise MediaError("DISPLAY_INVALID", "Give the screen a name of up to 80 characters", 400, "name")
        name = name.strip()
    settings = body.get("settings", {})
    if not isinstance(settings, dict):
        raise MediaError("DISPLAY_INVALID", "Send settings as an object", 400, "settings")
    for key, value in settings.items():
        field = f"settings.{str(key)[:40]}"
        if key == "rotate":
            if type(value) is not int or value not in (0, 90, 180, 270):
                raise MediaError("DISPLAY_INVALID", "Rotate by 0, 90, 180 or 270 degrees", 400, field)
        elif key == "startVolume":
            if type(value) is not int or not 0 <= value <= 100:
                raise MediaError("DISPLAY_INVALID", "Start volume is a whole number from 0 to 100", 400, field)
        elif key == "sound":
            if value not in SOUND_OUTPUTS:
                raise MediaError("DISPLAY_INVALID", "Sound goes to the display or the headphones", 400, field)
        elif key == "coverFit":
            if value not in COVER_FITS:
                raise MediaError("DISPLAY_INVALID", "The cover fits by cover, contain or stretch", 400, field)
        elif key == "coverRotate":
            if type(value) is not int or value not in (0, 90, 180, 270):
                raise MediaError("DISPLAY_INVALID", "Turn the cover by 0, 90, 180 or 270 degrees", 400, field)
        else:
            raise MediaError("DISPLAY_INVALID", f"{str(key)[:40]} is not a screen setting", 400, field)
    return name, dict(settings)
