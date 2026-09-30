import http.client
import json
import os
import io
import queue
import sqlite3
import socket
import time
import tempfile
import threading
import unittest
from unittest.mock import call, patch
from pathlib import Path
from http.server import ThreadingHTTPServer

from media.library import Drive, Library, MediaError
from media.server import State, handler_for
from media.camera import Camera


class MediaServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name) / "drive"
        root.mkdir()
        (root / "Movie α.mp4").write_bytes(b"0123456789")
        (root / "notes.db").write_bytes(b"not media")
        (root / "folder").mkdir()
        (root / "folder" / "track.mp3").write_bytes(b"audio")
        self.root = root
        library = Library([Drive("disk1", "Test USB", root, "fixture-uuid")], "secret", fixture_mounts=True)
        self.state = State(library, Path(self.tmp.name) / "history.db")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(self.state, "secret"))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {"X-Csync-Token": "secret", **(headers or {})}
        if body is not None:
            body = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        conn.request(method, path, body, headers)
        response = conn.getresponse()
        data = response.read()
        status = response.status
        received_headers = dict(response.getheaders())
        conn.close()
        return status, data, received_headers

    def item(self):
        status, data, _ = self.request("GET", "/v1/items?driveId=disk1")
        self.assertEqual(status, 200)
        return next(x for x in json.loads(data)["items"] if x["name"] == "Movie α.mp4")

    def test_auth_browse_search_and_range(self):
        status, data, _ = self.request("GET", "/v1/drives", headers={"X-Csync-Token": "wrong"})
        self.assertEqual(status, 401)
        self.assertEqual(json.loads(data)["code"], "AUTH_REQUIRED")
        item = self.item()
        self.assertEqual(item["driveId"], "disk1")
        status, data, _ = self.request("GET", "/v1/items?driveId=disk1")
        self.assertEqual(status, 200)
        self.assertNotIn("notes.db", [entry["name"] for entry in json.loads(data)["items"]])
        status, data, _ = self.request("GET", "/v1/search?q=track")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)["items"][0]["name"], "track.mp3")
        status, data, headers = self.request("GET", "/v1/items/" + item["id"] + "/stream",
                                              headers={"Range": "bytes=3-6"})
        self.assertEqual((status, data, headers.get("Content-Range")), (206, b"3456", "bytes 3-6/10"))
        status, data, _ = self.request("GET", "/v1/items/" + item["id"] + "/stream",
                                       headers={"Range": "bytes=100-"})
        self.assertEqual(status, 416)
        self.assertEqual(json.loads(data)["code"], "RANGE_INVALID")

    def test_videos_collect_old_and_new_folders_without_metadata_files(self):
        older = self.root / "media" / "older"
        older.mkdir(parents=True)
        (older / "Old Film.mkv").write_bytes(b"old")
        (older / "._Old Film.mkv").write_bytes(b"metadata")
        newer = self.root / "shared"
        newer.mkdir()
        (newer / "New Film.mp4").write_bytes(b"new")
        page = self.state.library.videos(0, 2)
        self.assertEqual(page["total"], 3)
        self.assertEqual(page["nextOffset"], 2)
        self.assertEqual([item["name"] for item in page["items"]], ["Movie α.mp4", "New Film.mp4"])
        status, data, _ = self.request("GET", "/v1/videos?offset=2")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)["items"][0]["relativePath"], "media/older/Old Film.mkv")
        status, data, _ = self.request("GET", "/v1/search?q=Old+Film")
        self.assertEqual([item["name"] for item in json.loads(data)["items"]], ["Old Film.mkv"])

    def test_youtube_cast_accepts_one_video_and_rejects_other_hosts(self):
        self.assertEqual(self.state.youtube_item("https://youtu.be/aqz-KE-bpKQ?si=test"),
                         "youtube:aqz-KE-bpKQ")
        self.assertEqual(self.state.youtube_item("https://www.youtube.com/watch?v=aqz-KE-bpKQ&list=ignored"),
                         "youtube:aqz-KE-bpKQ")
        for url in ("http://youtube.com/watch?v=aqz-KE-bpKQ",
                    "https://youtube.com.evil.test/watch?v=aqz-KE-bpKQ",
                    "https://youtube.com:444/watch?v=aqz-KE-bpKQ",
                    "https://youtube.com/playlist?list=test",
                    "https://youtube.com@evil.test/watch?v=aqz-KE-bpKQ"):
            with self.assertRaises(MediaError):
                self.state.youtube_item(url)
        with patch.object(self.state, "_start_player"), patch.object(self.state, "_mpv"), \
             patch.object(self.state, "command_pi", return_value={"status": "applied"}) as play:
            status, data, _ = self.request("POST", "/v1/cast/youtube",
                                          {"url": "https://youtu.be/aqz-KE-bpKQ"})
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(data)["status"], "applied")
            self.assertEqual(play.call_args.args[0]["itemId"], "youtube:aqz-KE-bpKQ")

    def test_phone_file_cast_streams_into_dedicated_drive_folder(self):
        (self.root / "shared").mkdir()
        body = b"video bytes" * 100
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request("POST", "/v1/cast/file?driveId=disk1&name=My+clip.mp4", body,
                     {"X-Csync-Token": "secret", "Content-Type": "video/mp4"})
        response = conn.getresponse()
        self.assertEqual(response.status, 201)
        item = json.loads(response.read())["item"]
        conn.close()
        self.assertEqual(item["driveId"], "disk1")
        self.assertTrue(item["relativePath"].startswith("shared/csync-casts/cast-"))
        status, streamed, _ = self.request("GET", "/v1/items/" + item["id"] + "/stream")
        self.assertEqual((status, streamed), (200, body))
        self.assertEqual(len(list((self.root / "shared" / "csync-casts").iterdir())), 1)
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request("POST", "/v1/cast/file?driveId=disk1&name=script.txt", b"text",
                     {"X-Csync-Token": "secret"})
        response = conn.getresponse()
        self.assertEqual((response.status, json.loads(response.read())["code"]), (400, "UPLOAD_TYPE"))
        conn.close()
        with self.assertRaises(MediaError) as error:
            self.state.library.import_media("disk1", "part.mp4", 100, io.BytesIO(b"partial"))
        self.assertEqual(error.exception.code, "UPLOAD_INCOMPLETE")
        self.assertEqual(len(list((self.root / "shared" / "csync-casts").iterdir())), 1)

    def test_app_update_requires_token_and_serves_only_staged_regular_file(self):
        route = "/v1/app/apk"
        status, data, _ = self.request("GET", route)
        self.assertEqual((status, json.loads(data)["code"]), (404, "UPDATE_UNAVAILABLE"))
        apk = Path(self.tmp.name) / "csync-hub-update.apk"
        apk.write_bytes(b"A" * 2048)
        status, data, headers = self.request("GET", route, headers={"X-Csync-Token": "wrong"})
        self.assertEqual(status, 401)
        status, data, headers = self.request("GET", route)
        self.assertEqual((status, data, headers["Content-Length"]), (200, b"A" * 2048, "2048"))
        apk.unlink()
        apk.symlink_to(Path(self.tmp.name) / "history.db")
        status, data, _ = self.request("GET", route)
        self.assertEqual((status, json.loads(data)["code"]), (503, "UPDATE_UNAVAILABLE"))

    def test_notes_crud_requires_token_and_revision(self):
        route = "/v1/notes"
        status, data, _ = self.request("POST", route, {"title": "Test", "body": "# Hello"},
                                        headers={"X-Csync-Token": "wrong"})
        self.assertEqual((status, json.loads(data)["code"]), (401, "AUTH_REQUIRED"))
        status, data, _ = self.request("POST", route, {"title": "Test", "body": "# Hello"})
        self.assertEqual(status, 201)
        note = json.loads(data)["note"]
        self.assertEqual((note["revision"], note["body"]), (1, "# Hello"))
        item = route + "/" + note["id"]
        status, data, _ = self.request("GET", route)
        self.assertEqual((status, json.loads(data)["notes"][0]["id"]), (200, note["id"]))
        status, data, _ = self.request("PUT", item,
                                        {"title": "Test 2", "body": "| A | B |", "expectedRevision": 1})
        self.assertEqual((status, json.loads(data)["note"]["revision"]), (200, 2))
        status, data, _ = self.request("PUT", item,
                                        {"title": "Stale", "body": "lost", "expectedRevision": 1})
        self.assertEqual((status, json.loads(data)["code"]), (409, "NOTE_CONFLICT"))
        status, data, _ = self.request("GET", item)
        self.assertEqual((status, json.loads(data)["note"]["title"]), (200, "Test 2"))
        status, data, _ = self.request("DELETE", item, {"expectedRevision": 1})
        self.assertEqual((status, json.loads(data)["code"]), (409, "NOTE_CONFLICT"))
        status, data, _ = self.request("DELETE", item, {"expectedRevision": 2})
        self.assertEqual((status, json.loads(data)["deleted"]), (200, True))
        status, data, _ = self.request("GET", item)
        self.assertEqual((status, json.loads(data)["code"]), (404, "NOTE_NOT_FOUND"))

    def test_notes_search_body_beyond_default_list_window(self):
        with self.state._db() as db:
            db.execute("INSERT INTO notes VALUES(?,?,?,?,?,?)",
                       ("older", "Unrelated title", "Needle in Markdown", 1, 1, 1))
            db.executemany("INSERT INTO notes VALUES(?,?,?,?,?,?)",
                           ((f"new-{i}", "Recent", "ordinary", 1, 2, i + 2)
                            for i in range(501)))
        status, data, _ = self.request("GET", "/v1/notes")
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(data)["notes"]), 500)
        self.assertNotIn("older", [item["id"] for item in json.loads(data)["notes"]])
        status, data, _ = self.request("GET", "/v1/notes?q=needle")
        self.assertEqual((status, [item["id"] for item in json.loads(data)["notes"]]),
                         (200, ["older"]))
        self.assertNotIn("body", json.loads(data)["notes"][0])
        status, data, _ = self.request("GET", "/v1/notes?q=" + "x" * 129)
        self.assertEqual((status, json.loads(data)["code"]), (400, "NOTE_INVALID"))

    def test_pins_store_urls_with_auth_and_revision_conflicts(self):
        route = "/v1/pins"
        body = {"title": "Example", "url": "https://example.org/article", "description": "Read later"}
        status, data, _ = self.request("POST", route, body, headers={"X-Csync-Token": "wrong"})
        self.assertEqual((status, json.loads(data)["code"]), (401, "AUTH_REQUIRED"))
        for url in ("javascript:alert(1)", "https://user:pass@example.org", "https://[bad"):
            status, data, _ = self.request("POST", route, {**body, "url": url})
            self.assertEqual((status, json.loads(data)["code"]), (400, "PIN_INVALID"))
        status, data, _ = self.request("POST", route, body)
        self.assertEqual(status, 201)
        pin = json.loads(data)["pin"]
        self.assertEqual((pin["revision"], pin["url"]), (1, body["url"]))
        item = route + "/" + pin["id"]
        status, data, _ = self.request("GET", route)
        self.assertEqual((status, json.loads(data)["pins"][0]["id"]), (200, pin["id"]))
        status, data, _ = self.request("PUT", item, {**body, "title": "Changed", "expectedRevision": 1})
        self.assertEqual((status, json.loads(data)["pin"]["revision"]), (200, 2))
        status, data, _ = self.request("PUT", item, {**body, "expectedRevision": 1})
        self.assertEqual((status, json.loads(data)["code"]), (409, "PIN_CONFLICT"))
        status, data, _ = self.request("GET", item)
        self.assertEqual((status, json.loads(data)["pin"]["title"]), (200, "Changed"))
        status, data, _ = self.request("DELETE", item, {"expectedRevision": 1})
        self.assertEqual((status, json.loads(data)["code"]), (409, "PIN_CONFLICT"))
        status, data, _ = self.request("DELETE", item, {"expectedRevision": 2})
        self.assertEqual((status, json.loads(data)["deleted"]), (200, True))
        status, data, _ = self.request("GET", item)
        self.assertEqual((status, json.loads(data)["code"]), (404, "PIN_NOT_FOUND"))

    def test_pin_snippets_tags_and_optional_title(self):
        route = "/v1/pins"
        snippet = {"content": "A useful text snippet", "tags": ["Read later", "Pi"]}
        status, data, _ = self.request("POST", route, snippet)
        self.assertEqual(status, 201)
        pin = json.loads(data)["pin"]
        self.assertEqual((pin["title"], pin["url"], pin["content"], pin["tags"]),
                         ("", "", snippet["content"], snippet["tags"]))
        item = route + "/" + pin["id"]
        status, data, _ = self.request("PUT", item, {"url": "https://example.org", "tags": ["Link"],
                                                      "expectedRevision": 1})
        self.assertEqual((status, json.loads(data)["pin"]["revision"]), (200, 2))
        for invalid in ({}, {"content": "text", "tags": [""]},
                        {"content": "text", "tags": ["x"] * 13},
                        {"content": "text", "url": "javascript:bad"}):
            status, data, _ = self.request("POST", route, invalid)
            self.assertEqual((status, json.loads(data)["code"]), (400, "PIN_INVALID"))

    def test_existing_url_pins_gain_snippet_columns_without_losing_data(self):
        old_db = Path(self.tmp.name) / "old-pins.db"
        with sqlite3.connect(old_db) as db:
            db.execute("""CREATE TABLE pins (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL,
                description TEXT NOT NULL, revision INTEGER NOT NULL,
                created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL)""")
            db.execute("INSERT INTO pins VALUES(?,?,?,?,?,?,?)",
                       ("old", "Old link", "https://example.org", "Kept", 3, 1, 2))
        migrated = State(self.state.library, old_db)
        pin = migrated.pin_get("old")
        self.assertEqual((pin["title"], pin["revision"], pin["content"], pin["tags"]),
                         ("Old link", 3, "", []))

    def test_note_png_attachment_is_authenticated_and_deleted_with_note(self):
        note = self.state.note_create({"title": "Screenshots", "body": "Evidence"})
        route = "/v1/notes/" + note["id"] + "/images"
        png = b"\x89PNG\r\n\x1a\n" + b"fixture-image"
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request("POST", route, png, {"X-Csync-Token": "secret", "Content-Type": "image/png"})
        response = conn.getresponse()
        self.assertEqual(response.status, 201)
        image_id = json.loads(response.read())["image"]["id"]
        conn.close()
        status, data, _ = self.request("GET", route)
        self.assertEqual((status, json.loads(data)["images"][0]["id"]), (200, image_id))
        status, data, headers = self.request("GET", route + "/" + image_id)
        self.assertEqual((status, data, headers["Content-Type"]), (200, png, "image/png"))
        status, data, _ = self.request("GET", route + "/" + image_id,
                                        headers={"X-Csync-Token": "wrong"})
        self.assertEqual((status, json.loads(data)["code"]), (401, "AUTH_REQUIRED"))
        status, data, _ = self.request("DELETE", "/v1/notes/" + note["id"], {"expectedRevision": 1})
        self.assertEqual(status, 200)
        with self.state._db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM note_images WHERE note_id=?", (note["id"],)).fetchone()[0], 0)

    def upload(self, path, body, headers):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request("POST", path, body, {"X-Csync-Token": "secret", **headers})
        response = conn.getresponse()
        result = response.status, json.loads(response.read())
        conn.close()
        return result

    def test_note_keeps_any_file_inside_its_own_folder_until_removed(self):
        note = self.state.note_create({"title": "Paperwork", "body": "Receipts"})
        route = "/v1/notes/" + note["id"] + "/files"
        pdf = b"%PDF-1.4 fixture" * 10
        status, result = self.upload(route + "?name=..%2F..%2F%C3%A9vil+report.pdf", pdf,
                                     {"Content-Type": "application/pdf"})
        self.assertEqual(status, 201)
        attached = result["file"]
        self.assertEqual((attached["name"], attached["mime"], attached["size"]),
                         ("_.._évil report.pdf", "application/pdf", len(pdf)))
        folder = Path(self.tmp.name) / "note-files" / note["id"]
        self.assertEqual([p.name for p in folder.iterdir()], [attached["id"]])
        self.assertEqual([p.name for p in Path(self.tmp.name).rglob("*évil*")], [])
        status, data, _ = self.request("GET", "/v1/notes/" + note["id"])
        self.assertEqual(json.loads(data)["note"]["files"], [attached])
        status, data, _ = self.request("GET", route)
        self.assertEqual(json.loads(data)["files"], [attached])
        status, data, _ = self.request("GET", "/v1/notes/" + note["id"] + "/images")
        self.assertEqual((status, json.loads(data)), (200, {"images": []}))
        status, data, headers = self.request("GET", route + "/" + attached["id"])
        self.assertEqual((status, data, headers["Content-Type"]), (200, pdf, "application/pdf"))
        self.assertIn('filename="_..__vil report.pdf"', headers["Content-Disposition"])
        self.assertIn("filename*=UTF-8''_.._%C3%A9vil%20report.pdf", headers["Content-Disposition"])
        status, data, _ = self.request("GET", route + "/" + attached["id"], headers={"X-Csync-Token": "wrong"})
        self.assertEqual((status, json.loads(data)["code"]), (401, "AUTH_REQUIRED"))
        status, result = self.upload(route + "?name=notes.txt", b"plain words", {})
        self.assertEqual((status, result["file"]["mime"]), (201, "text/plain"))
        with self.assertRaises(MediaError) as error:
            self.state.note_file_add(note["id"], "big.bin", "", 20 * 1024 * 1024 + 1, io.BytesIO(b""))
        self.assertEqual(error.exception.code, "FILE_INVALID")
        status, data, _ = self.request("DELETE", route + "/" + attached["id"])
        self.assertEqual((status, json.loads(data)["deleted"]), (200, True))
        self.assertFalse((folder / attached["id"]).exists())
        status, data, _ = self.request("GET", route + "/" + attached["id"])
        self.assertEqual((status, json.loads(data)["code"]), (404, "FILE_NOT_FOUND"))
        self.assertEqual(len(self.state.note_files(note["id"])), 1)
        status, data, _ = self.request("DELETE", "/v1/notes/" + note["id"], {"expectedRevision": 1})
        self.assertEqual(status, 200)
        self.assertFalse(folder.exists())
        with self.state._db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM note_files").fetchone()[0], 0)

    @staticmethod
    def edid(name, serial, maker="ACR", product=0x1234):
        data = bytearray(128)
        data[:8] = b"\x00\xff\xff\xff\xff\xff\xff\x00"
        word = sum((ord(letter) - 64) << shift for letter, shift in zip(maker, (10, 5, 0)))
        data[8:10] = bytes([word >> 8, word & 0xFF])
        data[10:12] = product.to_bytes(2, "little")
        data[54:56] = b"\x01\x01"
        data[56], data[58] = 1280 & 0xFF, (1280 >> 8) << 4
        data[59], data[61] = 800 & 0xFF, (800 >> 8) << 4
        for offset, tag, text in ((72, 0xFC, name), (90, 0xFF, serial)):
            data[offset:offset + 5] = bytes([0, 0, 0, tag, 0])
            data[offset + 5:offset + 18] = (text.encode() + b"\n").ljust(13, b" ")
        return bytes(data)

    def connector(self, name, status, edid=b"", modes="1920x1080\n1280x720\n"):
        folder = Path(self.tmp.name) / "drm" / ("card1-" + name)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "status").write_text(status + "\n")
        (folder / "edid").write_bytes(edid)
        (folder / "modes").write_text(modes)
        self.state.drm_root = folder.parent

    def play_and_capture(self):
        item = self.item()
        self.state.mpv_socket = Path(self.tmp.name) / "mpv.sock"
        self.state.mpv_socket.touch()
        def reply(command):
            if command[0] in ("loadfile", "set_property"):
                return {"error": "success"}
            return {"data": {"idle-active": False, "time-pos": 1.0, "duration": 80.0,
                             "pause": False, "eof-reached": False, "volume": None,
                             "path": str(self.root / "Movie α.mp4")}[command[1]]}
        with patch.object(self.state, "_start_player"), patch.object(self.state, "_mpv", side_effect=reply) as mpv, \
                patch.object(self.state, "_track_pi"):
            status, data, _ = self.request("POST", "/v1/player/pi/commands", {
                "action": "play", "itemId": item["id"], "expectedRevision": self.state.pi["revision"]})
        self.assertEqual(status, 200)
        sets = {c.args[0][1]: c.args[0][2] for c in mpv.call_args_list if c.args[0][0] == "set_property"}
        return sets, json.loads(data)["player"]

    def test_each_screen_keeps_its_own_settings_and_playback_uses_them(self):
        self.connector("HDMI-A-1", "connected")
        self.connector("HDMI-A-2", "disconnected")
        status, data, _ = self.request("GET", "/v1/displays")
        listed = json.loads(data)
        monitor = listed["displays"][0]
        self.assertEqual((status, len(listed["displays"]), listed["current"]), (200, 1, monitor["id"]))
        self.assertEqual((monitor["id"], monitor["name"], monitor["port"], monitor["size"], monitor["connected"]),
                         ("port-HDMI-A-1-1920x1080", "HDMI0 screen", "HDMI0", "1920 by 1080", True))
        self.assertEqual(monitor["settings"], {"rotate": 0, "startVolume": 0, "sound": "display"})
        self.assertIsInstance(monitor["lastSeen"], int)
        sets, player = self.play_and_capture()
        self.assertEqual((sets["volume"], sets["video-rotate"], player["volume"]), (0, 0, 0))
        route = "/v1/displays/" + monitor["id"]
        for body, field in (({"colour": "red"}, "colour"),
                            ({"settings": {"rotate": 45}}, "settings.rotate"),
                            ({"settings": {"startVolume": 101}}, "settings.startVolume"),
                            ({"settings": {"startVolume": True}}, "settings.startVolume"),
                            ({"settings": {"sound": "hdmi"}}, "settings.sound"),
                            ({"settings": {"brightness": 3}}, "settings.brightness"),
                            ({"name": ""}, "name")):
            status, data, _ = self.request("PUT", route, body)
            error = json.loads(data)
            self.assertEqual((status, error["code"], error["field"]), (400, "DISPLAY_INVALID", field))
        status, data, _ = self.request("PUT", "/v1/displays/port-unknown", {"name": "X"})
        self.assertEqual((status, json.loads(data)["code"]), (404, "DISPLAY_NOT_FOUND"))
        status, data, _ = self.request("PUT", route, {"name": "Desk monitor",
                                                      "settings": {"rotate": 180, "startVolume": 35}})
        saved = json.loads(data)["display"]
        self.assertEqual((status, saved["name"], saved["settings"]),
                         (200, "Desk monitor", {"rotate": 180, "startVolume": 35, "sound": "display"}))
        status, data, _ = self.request("PUT", route, {"settings": {"sound": "headphones"}})
        self.assertEqual(json.loads(data)["display"]["settings"],
                         {"rotate": 180, "startVolume": 35, "sound": "headphones"})
        sets, player = self.play_and_capture()
        self.assertEqual((sets["volume"], sets["video-rotate"], player["volume"], player["rotation"]),
                         (35, 180, 35, 180))
        # The Pi moves to a projector with an EDID on the other port.
        self.connector("HDMI-A-1", "disconnected")
        self.connector("HDMI-A-2", "connected", self.edid("PROJ X1", "ABC123"), modes="")
        status, data, _ = self.request("GET", "/v1/displays")
        listed = json.loads(data)
        by_id = {d["id"]: d for d in listed["displays"]}
        self.assertEqual(listed["current"], "edid-ACR-1234-ABC123")
        projector = by_id["edid-ACR-1234-ABC123"]
        self.assertEqual((projector["name"], projector["port"], projector["size"], projector["connected"]),
                         ("PROJ X1", "HDMI1", "1280 by 800", True))
        self.assertEqual((by_id[monitor["id"]]["connected"], by_id[monitor["id"]]["name"],
                          by_id[monitor["id"]]["settings"]["rotate"]), (False, "Desk monitor", 180))
        sets, _ = self.play_and_capture()
        self.assertEqual((sets["volume"], sets["video-rotate"]), (0, 0))
        self.connector("HDMI-A-1", "connected")
        listed = json.loads(self.request("GET", "/v1/displays")[1])
        self.assertEqual((listed["current"], len(listed["displays"])), (monitor["id"], 2))
        self.assertTrue(all(d["connected"] for d in listed["displays"]))
        status, data, _ = self.request("GET", "/v1/diagnostics")
        self.assertEqual(set(json.loads(data)), {"observedAt", "drives", "piPlayer", "phonePlayer",
                                                  "power", "displays", "playerErrors"})

    def fake_screen(self):
        """A stand-in mpv that accepts every command and reports a full HD OSD."""
        self.state.mpv_socket = Path(self.tmp.name) / "mpv.sock"
        self.state.mpv_socket.touch()
        def reply(command):
            if isinstance(command, list) and command[0] == "get_property":
                return {"data": {"osd-width": 1920, "osd-height": 1080}.get(command[1])}
            return {"error": "success"}
        return reply

    @staticmethod
    def overlays(mpv, format_name="ass-events"):
        return [c.args[0] for c in mpv.call_args_list
                if isinstance(c.args[0], dict) and c.args[0]["name"] == "osd-overlay" and
                c.args[0]["format"] == format_name]

    def test_show_picture_and_text_on_screen_then_stop_returns_to_cover(self):
        self.state.wallpaper.write_bytes(b"cover")
        picture = b"\x89PNG\r\n\x1a\n" + b"p" * 200
        with patch.object(self.state, "_start_player"), \
                patch.object(self.state, "_mpv", side_effect=self.fake_screen()) as mpv, \
                patch("media.server.subprocess.run") as probe:
            probe.return_value.stdout = b'{"streams":[{"codec_name":"png","width":640,"height":480}]}'
            status, result = self.upload("/v1/display/show?name=Sunset.png", picture, {"Content-Type": "image/png"})
            self.assertEqual((status, result["shown"], result["sentToDisplay"]), (200, True, True))
            self.assertEqual({k: result["player"][k] for k in ("state", "kind", "name", "itemId")},
                             {"state": "showing", "kind": "image", "name": "Sunset.png", "itemId": None})
            shown = Path(self.tmp.name) / "display-show.png"
            self.assertEqual(shown.read_bytes(), picture)
            self.assertEqual(self.state.wallpaper.read_bytes(), b"cover")
            mpv.assert_any_call(["loadfile", str(shown), "replace"])
            mpv.assert_any_call(["set_property", "image-display-duration", "inf"])
            self.assertEqual(json.loads(self.request("GET", "/v1/player/pi")[1])["state"], "showing")
            probe.return_value.stdout = b'{"streams":[{"codec_name":"h264","width":640,"height":480}]}'
            status, result = self.upload("/v1/display/show", picture, {"Content-Type": "image/png"})
            self.assertEqual((status, result["code"]), (400, "IMAGE_INVALID"))

            status, data, _ = self.request("POST", "/v1/display/show",
                                           {"title": "Dinner", "text": "Pasta at {7}, bring \\N wine"})
            result = json.loads(data)
            self.assertEqual((status, result["player"]["kind"], result["player"]["name"]), (200, "text", "Dinner"))
            blank = Path(self.tmp.name) / "display-blank.png"
            self.assertTrue(blank.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
            mpv.assert_any_call(["loadfile", str(blank), "replace"])
            overlay = self.overlays(mpv)
            self.assertEqual(len(overlay), 1)
            self.assertEqual((overlay[0]["id"], overlay[0]["res_x"], overlay[0]["res_y"]), (7, 1920, 1080))
            self.assertIn("{\\b1}Dinner{\\b0}", overlay[0]["data"])
            self.assertIn("\\{7}", overlay[0]["data"])
            self.assertIn("\\⁠N", overlay[0]["data"])
            self.assertNotIn("\\N wine", overlay[0]["data"])

            revision = self.state.pi["revision"]
            status, data, _ = self.request("POST", "/v1/player/pi/commands",
                                           {"action": "seek", "positionMs": 0, "expectedRevision": revision})
            self.assertEqual((status, json.loads(data)["code"]), (409, "NOT_PLAYING"))
            status, data, _ = self.request("POST", "/v1/player/pi/immediate", {"action": "pause"})
            player = json.loads(data)["player"]
            self.assertEqual((player["state"], player["paused"]), ("showing", True))
            status, data, _ = self.request("POST", "/v1/player/pi/commands",
                                           {"action": "rotate", "value": 90,
                                            "expectedRevision": self.state.pi["revision"]})
            self.assertEqual(status, 200)
            self.assertIn("\\frz270", self.overlays(mpv)[-1]["data"])
            for body, code, field in (({"text": "x" * 4001}, 400, "text"), ({"text": "   "}, 400, "text"),
                                      ({"text": "ok", "title": 5}, 400, "title")):
                status, data, _ = self.request("POST", "/v1/display/show", body)
                self.assertEqual((status, json.loads(data)["field"]), (code, field))
            status, result = self.upload("/v1/display/show", b"plain", {"Content-Type": "text/plain"})
            self.assertEqual((status, result["code"]), (415, "DISPLAY_INVALID"))
            with patch.object(self.state, "show_wallpaper", return_value=True) as cover:
                status, data, _ = self.request("POST", "/v1/player/pi/immediate", {"action": "stop"})
                cover.assert_called_once()
            player = json.loads(data)["player"]
            self.assertEqual((status, player["state"]), (200, "idle"))
            self.assertNotIn("kind", player)
            self.assertEqual(len(self.overlays(mpv, "none")), 1)
        self.assertEqual(self.state.wallpaper.read_bytes(), b"cover")

    def test_text_is_laid_out_large_and_cut_only_after_a_whole_word(self):
        from media import screen
        short = screen.layout("Hello", "Dinner is ready", 1920, 1080)
        self.assertEqual((short["cut"], short["size"], short["lines"], short["titleLines"]),
                         (False, 1080 // 7, ["Hello", "", "Dinner is ready"], 1))
        words = [f"word{i % 97}" for i in range(700)]
        long = screen.layout(None, " ".join(words), 1920, 1080)
        self.assertTrue(long["cut"])
        self.assertEqual(long["size"], 1080 // 18)
        cols = int(1920 * 0.88 // (long["size"] * screen.CHAR_WIDTH))
        rows = int(1080 * 0.84 // (long["size"] * screen.LINE_HEIGHT))
        self.assertLessEqual(len(long["lines"]), rows)
        self.assertTrue(all(screen.text_width(line) <= cols for line in long["lines"]))
        shown = " ".join(long["lines"]).split()
        self.assertEqual(shown, words[:len(shown)])
        self.assertNotIn("…", "".join(long["lines"]))
        self.assertFalse(long["lines"][-1].endswith("..."))
        # A word wider than the screen is wrapped; the cut never ends inside it.
        giant = "x" * 5000
        cut = screen.layout(None, "start " + giant, 1920, 1080)
        self.assertEqual(cut["lines"], ["start"])
        wide = screen.layout(None, "東京 " * 10, 1920, 1080)
        self.assertEqual(screen.text_width(wide["lines"][0]), len(wide["lines"][0].replace(" ", "")) * 2 +
                         wide["lines"][0].count(" "))

    def test_slideshow_loops_folder_photos_in_name_order_until_replaced_or_stopped(self):
        photos = self.root / "Photos"
        (photos / "sub").mkdir(parents=True)
        for name in ("b.jpg", "A.png", "c.JPG", "notes.txt", ".hidden.jpg", "sub/deeper.jpg"):
            (photos / name).write_bytes(b"image")
        (photos / "outside.jpg").symlink_to(Path(self.tmp.name) / "history.db")
        (self.root / "Empty").mkdir()
        (self.root / "linked").symlink_to(photos)
        with patch.object(self.state, "_start_player"), \
                patch.object(self.state, "_mpv", side_effect=self.fake_screen()) as mpv:
            status, data, _ = self.request("POST", "/v1/display/slideshow",
                                           {"driveId": "disk1", "path": "Photos", "seconds": 5})
            result = json.loads(data)
            self.assertEqual((status, result["sentToDisplay"]), (200, True))
            self.assertEqual({k: result["player"][k] for k in ("state", "kind", "name", "count")},
                             {"state": "showing", "kind": "slideshow", "name": "Photos", "count": 3})
            loads = [c.args[0][1:] for c in mpv.call_args_list
                     if isinstance(c.args[0], list) and c.args[0][0] == "loadfile"]
            self.assertEqual(loads, [[str(photos / "A.png"), "replace"], [str(photos / "b.jpg"), "append"],
                                     [str(photos / "c.JPG"), "append"]])
            mpv.assert_any_call(["set_property", "image-display-duration", 5])
            mpv.assert_any_call(["set_property", "loop-playlist", "inf"])
            status, data, _ = self.request("POST", "/v1/display/slideshow", {"driveId": "disk1", "path": "Photos"})
            mpv.assert_any_call(["set_property", "image-display-duration", 8])
            for body, code, error_code in (({"driveId": "disk1", "path": "Photos", "seconds": 2}, 400, "SLIDESHOW_INVALID"),
                                           ({"driveId": "disk1", "path": "Photos", "seconds": 61}, 400, "SLIDESHOW_INVALID"),
                                           ({"driveId": "disk1", "path": "Empty"}, 400, "SLIDESHOW_EMPTY"),
                                           ({"driveId": "disk1", "path": "../"}, 400, "PATH_INVALID"),
                                           ({"driveId": "disk1", "path": "linked"}, 400, "PATH_INVALID"),
                                           ({"driveId": "nope", "path": ""}, 404, "DRIVE_UNKNOWN")):
                status, data, _ = self.request("POST", "/v1/display/slideshow", body)
                self.assertEqual((status, json.loads(data)["code"]), (code, error_code), body)
            status, data, _ = self.request("POST", "/v1/display/slideshow", {"driveId": "disk1", "path": "Empty"})
            self.assertEqual(json.loads(data)["message"], "This folder has no photos to show")
            self.assertEqual(self.state.pi["kind"], "slideshow")
        sets, player = self.play_and_capture()
        self.assertEqual((sets["loop-playlist"], player["state"]), ("no", "playing"))
        self.assertNotIn("kind", player)
        with patch.object(self.state, "_start_player"), \
                patch.object(self.state, "_mpv", side_effect=self.fake_screen()) as mpv:
            self.state.slideshow({"driveId": "disk1", "path": "Photos"})
            with patch.object(self.state, "show_wallpaper", return_value=True):
                status, data, _ = self.request("POST", "/v1/player/pi/commands",
                                               {"action": "stop", "expectedRevision": self.state.pi["revision"]})
            self.assertEqual(json.loads(data)["player"]["state"], "idle")
            calls = [c.args[0] for c in mpv.call_args_list]
            self.assertLess(calls.index(["set_property", "loop-playlist", "no"]), calls.index(["stop"]))

    def test_bootstrap_link_is_secret_scoped_and_expires(self):
        marker = Path(self.tmp.name) / "app-bootstrap-token"
        marker.write_text("s" * 40)
        (Path(self.tmp.name) / "csync-hub-update.apk").write_bytes(b"A" * 2048)
        path = "/v1/app/bootstrap/" + "s" * 40
        status, data, _ = self.request("GET", path, headers={"X-Csync-Token": "wrong"})
        self.assertEqual((status, data), (200, b"A" * 2048))
        status, data, _ = self.request("GET", path + "x", headers={"X-Csync-Token": "wrong"})
        self.assertEqual((status, json.loads(data)["code"]), (404, "UPDATE_UNAVAILABLE"))
        old = time.time() - 8 * 86400
        os.utime(marker, (old, old))
        status, data, _ = self.request("GET", path, headers={"X-Csync-Token": "wrong"})
        self.assertEqual((status, json.loads(data)["code"]), (404, "UPDATE_UNAVAILABLE"))

    def test_replacement_and_symlink_escape(self):
        item = self.item()
        (self.root / "Movie α.mp4").write_bytes(b"new file content")
        status, data, _ = self.request("GET", "/v1/items/" + item["id"] + "/stream")
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(data)["code"], "ITEM_CHANGED")
        (self.root / "escape").symlink_to(Path(self.tmp.name) / "history.db")
        status, data, _ = self.request("GET", "/v1/items?driveId=disk1&path=escape")
        self.assertEqual(status, 404)
        status, data, _ = self.request("GET", "/v1/items?driveId=disk1&path=../")
        self.assertEqual(status, 400)

    def test_phone_commands_ack_and_stale_session(self):
        item = self.item()
        status, data, _ = self.request("POST", "/v1/phone/sessions", {"itemId": item["id"]})
        self.assertEqual(status, 200)
        session = json.loads(data)
        command = {"action": "pause", "commandId": "one", "expectedRevision": 0,
                   "expectedSessionId": session["id"], "expectedGeneration": session["generation"]}
        status, data, _ = self.request("POST", "/v1/player/phone/commands", command)
        self.assertEqual(status, 202)
        self.assertEqual(json.loads(data)["status"], "queued")
        status, data, _ = self.request("POST", "/v1/player/phone/commands", command)
        self.assertEqual(json.loads(data)["commandId"], "one")
        status, data, _ = self.request("GET", "/v1/phone/commands?sessionId=" + session["id"] + "&generation=1")
        self.assertEqual(len(json.loads(data)["commands"]), 1)
        ack = {"sessionId": session["id"], "generation": 1, "status": "applied", "state": "paused", "positionMs": 2000}
        status, data, _ = self.request("POST", "/v1/phone/commands/one/result", ack)
        self.assertEqual(json.loads(data)["status"], "applied")
        phone = json.loads(self.request("GET", "/v1/player/phone")[1])
        self.assertEqual((phone["state"], phone["positionMs"]), ("paused", 2000))
        status, data, _ = self.request("POST", "/v1/player/phone/commands",
            {"action": "volume", "value": 150, "commandId": "bad", "expectedRevision": 1})
        self.assertEqual((status, json.loads(data)["code"]), (400, "COMMAND_INVALID"))
        status, data, _ = self.request("POST", "/v1/progress", {"itemId": item["id"], "target": "phone",
            "sessionId": session["id"], "generation": 1, "sequence": 1, "positionMs": 8000})
        self.assertEqual(status, 200)
        status, data, _ = self.request("POST", "/v1/progress", {"itemId": item["id"], "target": "phone",
            "sessionId": session["id"], "generation": 1, "sequence": 2, "positionMs": 2000})
        self.assertEqual(status, 200)
        entry = json.loads(self.request("GET", "/v1/history")[1])["entries"][0]
        self.assertEqual(entry["positionMs"], 2000)
        self.assertEqual(entry["name"], "Movie α.mp4")
        self.assertEqual(entry["driveLabel"], "Test USB")
        self.request("POST", "/v1/phone/sessions", {"itemId": item["id"]})
        status, data, _ = self.request("POST", "/v1/phone/commands/one/result", ack)
        self.assertEqual(status, 404)

    def test_offline_progress_reconciles_only_for_last_session(self):
        item = self.item()
        session = self.state.register_phone({"itemId": item["id"]})
        body = {"itemId": item["id"], "target": "phone", "sessionId": session["id"],
                "generation": session["generation"], "sequence": 1, "positionMs": 1000}
        self.state.save_progress(body)
        restarted = State(self.state.library, self.state.database)
        body.update(sequence=2, positionMs=3000)
        self.assertEqual(restarted.save_progress(body)["positionMs"], 3000)
        restarted.register_phone({"itemId": item["id"]})
        body.update(sequence=3, positionMs=4000)
        with self.assertRaises(MediaError) as error:
            restarted.save_progress(body)
        self.assertEqual(error.exception.code, "SESSION_STALE")

    def test_phone_command_cannot_cross_replacement_with_same_revision(self):
        item = self.item()
        first = self.state.register_phone({"itemId": item["id"]})
        second = self.state.register_phone({"itemId": item["id"]})
        status, data, _ = self.request("POST", "/v1/player/phone/commands", {
            "action": "pause", "commandId": "stale", "expectedRevision": 0,
            "expectedSessionId": first["id"], "expectedGeneration": first["generation"]})
        self.assertEqual((status, json.loads(data)["code"]), (409, "SESSION_STALE"))
        status, data, _ = self.request("POST", "/v1/player/phone/commands", {
            "action": "pause", "commandId": "fresh", "expectedRevision": 0,
            "expectedSessionId": second["id"], "expectedGeneration": second["generation"]})
        self.assertEqual((status, json.loads(data)["status"]), (202, "queued"))

    def test_progress_saves_after_drive_removal(self):
        item = self.item()
        session = self.state.register_phone({"itemId": item["id"]})
        self.state.library.fixture_mounts = False
        status, data, _ = self.request("POST", "/v1/progress", {
            "itemId": item["id"], "target": "phone", "sessionId": session["id"],
            "generation": session["generation"], "sequence": 1, "positionMs": 4321})
        self.assertEqual((status, json.loads(data)["saved"]), (200, True))

    def test_phone_progress_cannot_claim_a_different_item(self):
        first = self.item()
        (self.root / "Other.mp4").write_bytes(b"other")
        other = next(x for x in json.loads(self.request("GET", "/v1/items?driveId=disk1")[1])["items"]
                     if x["name"] == "Other.mp4")
        session = self.state.register_phone({"itemId": first["id"]})
        status, data, _ = self.request("POST", "/v1/progress", {
            "itemId": other["id"], "target": "phone", "sessionId": session["id"],
            "generation": session["generation"], "sequence": 1, "positionMs": 1000})
        self.assertEqual((status, json.loads(data)["code"]), (409, "ITEM_MISMATCH"))

    def test_mpv_event_and_reply_in_one_read(self):
        address = Path(self.tmp.name) / "mpv.sock"
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(address))
        server.listen(1)
        self.addCleanup(server.close)
        self.state.mpv_socket = address
        def respond():
            peer, _ = server.accept()
            with peer:
                peer.recv(4096)
                peer.sendall(b'{"event":"property-change"}\n{"request_id":1,"error":"success","data":7}\n')
        worker = threading.Thread(target=respond, daemon=True)
        worker.start()
        self.assertEqual(self.state._mpv(["get_property", "volume"])["data"], 7)
        worker.join(timeout=1)

    def test_camera_write_error_releases_recording(self):
        camera = Camera(Path(self.tmp.name) / "captures")
        class FullFile:
            def write(self, frame):
                raise OSError(28, "No space left on device")
            def close(self):
                pass
        class Process:
            stdout = io.BytesIO(b"\xff\xd8picture\xff\xd9")
            def poll(self):
                return None
        camera.process = Process()
        camera.record_file = FullFile()
        camera.record_path = camera.captures / "failed.mjpeg"
        camera.record_started = time.monotonic()
        camera._read()
        self.assertFalse(camera.status()["recording"])
        self.assertIn("No space", camera.status()["recordingError"])

    def test_pi_missing_socket_and_early_idle_are_not_completion(self):
        self.state.pi.update(itemId=self.item()["id"], state="playing", positionMs=0,
                             durationMs=80000)
        self.state.mpv_socket = Path(self.tmp.name) / "missing.sock"
        self.assertEqual(self.state.pi_state()["state"], "unavailable")
        self.state.mpv_socket.touch()
        with patch.object(self.state, "_mpv", return_value={"data": True}):
            self.assertEqual(self.state.pi_state()["state"], "unavailable")
            self.state.pi.update(positionMs=98500, durationMs=100000)
            self.assertEqual(self.state.pi_state()["state"], "unavailable")
        self.assertNotEqual(self.state.pi_state()["state"], "finished")

    def test_pi_observed_position_is_retained(self):
        self.state.pi.update(itemId=self.item()["id"], state="playing", positionMs=0,
                             durationMs=None)
        self.state.mpv_socket = Path(self.tmp.name) / "mpv.sock"
        self.state.mpv_socket.touch()
        def reply(command):
            name = command[1]
            return {"data": {"idle-active": False, "time-pos": 37.5,
                             "duration": 80.0, "pause": False, "eof-reached": False,
                             "volume": 20}[name]}
        with patch.object(self.state, "_mpv", side_effect=reply):
            observed = self.state.pi_state()
        self.assertEqual((observed["positionMs"], self.state.pi["positionMs"]), (37500, 37500))

    def test_pi_state_rejects_wallpaper_after_media_was_replaced(self):
        item = self.item()
        source = str(self.root / "Movie α.mp4")
        self.state.pi.update(itemId=item["id"], state="playing", sourcePath=source,
                             positionMs=17000, durationMs=80000, revision=4)
        self.state.pi_generation = 1
        self.state.mpv_socket = Path(self.tmp.name) / "mpv.sock"
        self.state.mpv_socket.touch()
        with patch.object(self.state, "_mpv", return_value={"data": str(self.state.wallpaper)}) as mpv:
            status, data, _ = self.request("GET", "/v1/player/pi")
        player = json.loads(data)
        self.assertEqual(status, 200)
        self.assertEqual((player["state"], player["itemId"], player["revision"]),
                         ("unavailable", None, 5))
        self.assertIn("changed output", player["error"])
        self.assertNotEqual(self.state.pi_generation, 1)
        self.assertEqual(self.state.history(), [])
        mpv.assert_called_once_with(["get_property", "path"])

    def test_pi_play_does_not_claim_success_when_player_stays_idle(self):
        item = self.item()
        self.state.mpv_socket = Path(self.tmp.name) / "mpv.sock"
        self.state.mpv_socket.touch()
        self.state.PLAY_START_TIMEOUT = 0.01
        def reply(command):
            if command[0] in ("loadfile", "set_property", "stop"):
                return {"error": "success"}
            if command[1] == "idle-active":
                return {"data": True}
            if command[1] == "path":
                return {"data": str(self.root / "Movie α.mp4")}
            raise AssertionError(command)
        with patch.object(self.state, "_start_player"), patch.object(self.state, "_mpv", side_effect=reply) as mpv:
            status, data, _ = self.request("POST", "/v1/player/pi/commands", {
                "action": "play", "itemId": item["id"], "expectedRevision": 0})
            mpv.assert_any_call(["stop"])
        self.assertEqual((status, json.loads(data)["code"]), (503, "PLAYER_UNAVAILABLE"))
        self.assertEqual(self.state.pi["state"], "unavailable")
        self.assertIsNone(self.state.pi["itemId"])
        self.assertEqual(self.state.pi["revision"], 2)
        self.assertEqual(self.state.history(), [])

    def test_natural_end_restores_wallpaper_and_stop_keeps_completed_history(self):
        item = self.item()
        self.state.mpv_socket = Path(self.tmp.name) / "mpv.sock"
        self.state.mpv_socket.touch()
        self.state.pi.update(itemId=item["id"], state="playing", positionMs=0,
                             durationMs=10000, revision=1)
        self.state.pi_session = "test-session"
        self.state.pi_generation = 1
        values = {"idle-active": False, "time-pos": 10.0, "duration": 10.0,
                  "pause": False, "eof-reached": True, "volume": 0}
        def reply(command):
            if command[0] == "get_property":
                return {"data": values[command[1]]}
            return {"error": "success"}
        with patch("media.server.time.sleep"), patch.object(self.state, "_mpv", side_effect=reply), \
             patch.object(self.state, "show_wallpaper", return_value=True) as wallpaper:
            self.state._track_pi(1)
            wallpaper.assert_called_once()
            self.assertEqual(self.state.pi_state()["state"], "idle")
            self.assertTrue(self.state.history()[0]["completed"])
            status, data, _ = self.request("POST", "/v1/player/pi/immediate", {"action": "stop"})
            self.assertEqual(status, 200)
            self.assertTrue(self.state.history()[0]["completed"])

    def test_pi_play_confirms_loaded_item_before_saving_history(self):
        item = self.item()
        self.state.mpv_socket = Path(self.tmp.name) / "mpv.sock"
        self.state.mpv_socket.touch()
        def reply(command):
            if command[0] in ("loadfile", "set_property"):
                return {"error": "success"}
            return {"data": {"idle-active": False, "time-pos": 2.0, "duration": 80.0,
                             "pause": False, "eof-reached": False, "volume": 20,
                             "path": str(self.root / "Movie α.mp4")}[command[1]]}
        with patch.object(self.state, "_start_player"), patch.object(self.state, "_mpv", side_effect=reply) as mpv, \
                patch.object(self.state, "_track_pi"):
            status, data, _ = self.request("POST", "/v1/player/pi/commands", {
                "action": "play", "itemId": item["id"], "expectedRevision": 0})
            mpv.assert_any_call(["set_property", "volume", 0])
            self.assertLess(mpv.call_args_list.index(call(["set_property", "pause", False])),
                            mpv.call_args_list.index(call(["loadfile", str(self.root / "Movie α.mp4"), "replace"])))
        result = json.loads(data)
        self.assertEqual((status, result["status"], result["player"]["state"]),
                         (200, "applied", "playing"))
        self.assertEqual(self.state.history()[0]["positionMs"], 2000)

    def test_stop_interrupts_play_while_youtube_is_loading(self):
        self.state.mpv_socket = Path(self.tmp.name) / "mpv.sock"
        self.state.mpv_socket.touch()
        self.state.PLAY_START_TIMEOUT = 2
        def reply(command):
            if command[0] in ("loadfile", "set_property", "stop"):
                return {"error": "success"}
            if command == ["get_property", "path"]:
                return {"data": None}
            raise AssertionError(command)
        result = {}
        with patch.object(self.state, "_start_player"), patch.object(self.state, "_mpv", side_effect=reply):
            playing = threading.Thread(target=lambda: result.update(play=self.request(
                "POST", "/v1/player/pi/commands", {"action": "play", "itemId": self.item()["id"],
                                                        "expectedRevision": 0})))
            playing.start()
            for _ in range(100):
                if self.state.pi["state"] == "loading":
                    break
                time.sleep(0.01)
            self.assertEqual(self.state.pi["state"], "loading")
            status, data, _ = self.request("POST", "/v1/player/pi/immediate", {"action": "stop"})
            self.assertEqual((status, json.loads(data)["player"]["state"]), (200, "idle"))
            playing.join(timeout=2)
        self.assertFalse(playing.is_alive())
        self.assertEqual((result["play"][0], json.loads(result["play"][1])["code"]),
                         (409, "STATE_CHANGED"))
        self.assertEqual(self.state.history(), [])

    def test_pi_immediate_controls_do_not_wait_for_a_revision_read(self):
        with patch.object(self.state, "_mpv", return_value={"error": "success"}) as mpv:
            status, data, _ = self.request("POST", "/v1/player/pi/immediate", {"action": "mute"})
            self.assertEqual((status, json.loads(data)["player"]["volume"]), (200, 0))
            mpv.assert_called_with(["set_property", "volume", 0])
            status, data, _ = self.request("POST", "/v1/player/pi/immediate", {"action": "pause"})
            self.assertEqual((status, json.loads(data)["player"]["state"]), (200, "paused"))
            mpv.assert_called_with(["set_property", "pause", True])
            status, data, _ = self.request("POST", "/v1/player/pi/immediate", {"action": "stop"})
            self.assertEqual((status, json.loads(data)["player"]["state"]), (200, "idle"))
            mpv.assert_called_with(["stop"])
            self.assertEqual(self.state.pi["revision"], 3)

    def test_pi_rotate_and_loop_validate_and_reset_for_wallpaper(self):
        with patch.object(self.state, "_mpv", return_value={"error": "success"}) as mpv:
            for action, value, expected in (("rotate", 90, ["set_property", "video-rotate", 90]),
                                            ("loop", True, ["set_property", "loop-file", "inf"])):
                status, data, _ = self.request("POST", "/v1/player/pi/commands",
                                               {"action": action, "value": value,
                                                "expectedRevision": self.state.pi["revision"]})
                self.assertEqual((status, json.loads(data)["status"]), (200, "applied"))
                mpv.assert_any_call(expected)
            self.assertEqual((self.state.pi["rotation"], self.state.pi["loop"]), (90, True))
            for action, value in (("rotate", 45), ("rotate", True), ("loop", "true")):
                revision = self.state.pi["revision"]
                status, data, _ = self.request("POST", "/v1/player/pi/commands",
                                               {"action": action, "value": value,
                                                "expectedRevision": revision})
                self.assertEqual((status, json.loads(data)["code"]), (400, "COMMAND_INVALID"))
                self.assertEqual(self.state.pi["revision"], revision)
            self.state.wallpaper.write_bytes(b"image")
            with patch.object(self.state, "_start_player"):
                self.assertTrue(self.state.show_wallpaper())
            mpv.assert_any_call(["set_property", "video-rotate", 0])
            mpv.assert_any_call(["set_property", "loop-file", "no"])

    def test_wallpaper_upload_is_bounded_and_stop_returns_to_it(self):
        image = b"\xff\xd8\xff" + b"x" * 120
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request("POST", "/v1/display/wallpaper", b"bad", {"X-Csync-Token": "secret"})
        response = conn.getresponse()
        self.assertEqual(response.status, 400)
        response.read()
        conn.close()
        with patch("media.server.subprocess.run") as probe, patch.object(self.state, "show_wallpaper", return_value=True):
            probe.return_value.stdout = b'{"streams":[{"codec_name":"mjpeg","width":320,"height":180}]}'
            conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
            conn.request("POST", "/v1/display/wallpaper", image, {"X-Csync-Token": "secret"})
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            self.assertTrue(json.loads(response.read())["sentToDisplay"])
            conn.close()
        self.assertEqual(self.state.wallpaper.read_bytes(), image)
        with patch.object(self.state, "_mpv", return_value={"error": "success"}), \
                patch.object(self.state, "show_wallpaper", return_value=True) as show:
            status, data, _ = self.request("POST", "/v1/player/pi/immediate", {"action": "stop"})
            self.assertEqual((status, json.loads(data)["player"]["state"]), (200, "idle"))
            show.assert_called_once()

    def test_camera_blackholed_viewer_is_released(self):
        class BurstCamera:
            def __init__(self):
                self.viewers = 0
                self.done = threading.Event()
            def subscribe(self):
                self.viewers += 1
                frames = queue.Queue(maxsize=2)
                def push():
                    frame = b"\xff\xd8" + b"x" * 400_000 + b"\xff\xd9"
                    while not self.done.is_set():
                        try:
                            frames.put(frame, timeout=0.1)
                        except queue.Full:
                            pass
                threading.Thread(target=push, daemon=True).start()
                return frames
            def unsubscribe(self, listener):
                self.viewers -= 1
                self.done.set()
        camera = BurstCamera()
        self.state.camera = camera
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request("GET", "/v1/camera/stream", headers={"X-Csync-Token": "secret"})
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        time.sleep(7)
        self.assertEqual(camera.viewers, 0)
        conn.close()


if __name__ == "__main__":
    unittest.main()
