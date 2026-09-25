import http.client
import json
import os
import io
import queue
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
