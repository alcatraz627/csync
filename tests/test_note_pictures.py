import http.client
import json
import subprocess
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from media.library import Drive, Library, MediaError
from media.server import State, handler_for

PNG = b"\x89PNG\r\n\x1a\n"


class NotePicturesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name) / "drive"
        root.mkdir()
        library = Library([Drive("disk1", "Test USB", root, "fixture-uuid")], "secret", fixture_mounts=True)
        self.state = State(library, Path(self.tmp.name) / "history.db", notes_folder=Path(self.tmp.name) / "notes")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(self.state, "secret"))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, method, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request(method, path, None, {"X-Csync-Token": "secret"})
        response = conn.getresponse()
        data, status, headers = response.read(), response.status, dict(response.getheaders())
        conn.close()
        return status, data, headers

    def folder(self) -> Path:
        return Path(self.tmp.name) / "notes"

    def git(self, *args) -> str:
        return subprocess.run(["git", *args], cwd=self.folder(), capture_output=True, text=True).stdout

    def test_a_picture_is_a_committed_file_in_the_notes_folder(self):
        note = self.state.note_create({"title": "Trip", "body": "Notes"})
        added = self.state.note_image_add(note["id"], PNG + b"one")
        rel = f"attachments/{note['id']}-{added['id']}.png"
        self.assertEqual(added["path"], rel)
        self.assertEqual((self.folder() / rel).read_bytes(), PNG + b"one")
        self.assertIn(rel, self.git("show", "--name-only", "--format=%s", "HEAD"))
        self.assertEqual(self.git("status", "--porcelain"), "")
        # adding a picture is not an edit of the note's words
        self.assertEqual(self.state.note_get(note["id"])["revision"], note["revision"])

    def test_the_old_routes_serve_and_list_the_file(self):
        note = self.state.note_create({"title": "Trip", "body": "Notes"})
        added = self.state.note_image_add(note["id"], PNG + b"one")
        route = "/v1/notes/" + note["id"] + "/images"
        status, data, headers = self.request("GET", route + "/" + added["id"])
        self.assertEqual((status, data, headers["Content-Type"]), (200, PNG + b"one", "image/png"))
        status, data, _ = self.request("GET", route)
        self.assertEqual([i["id"] for i in json.loads(data)["images"]], [added["id"]])
        status, data, _ = self.request("GET", "/v1/notes")
        self.assertEqual(json.loads(data)["notes"][0]["items"], 1)

    def test_a_picture_the_mac_wrote_is_found_by_its_name(self):
        note = self.state.note_create({"title": "Mac", "body": "Notes"})
        (self.folder() / "attachments").mkdir()
        (self.folder() / "attachments" / f"{note['id']}-20261011-143000.png").write_bytes(PNG + b"mac")
        self.assertEqual([i["id"] for i in self.state.note_images(note["id"])], ["20261011-143000"])
        self.assertEqual(self.state.note_image_get(note["id"], "20261011-143000"), PNG + b"mac")

    def test_removing_a_picture_and_deleting_the_note_remove_the_file(self):
        note = self.state.note_create({"title": "Trip", "body": "Notes"})
        a = self.state.note_image_add(note["id"], PNG + b"a")
        b = self.state.note_image_add(note["id"], PNG + b"b")
        self.state.note_image_delete(note["id"], a["id"])
        self.assertEqual([i["id"] for i in self.state.note_images(note["id"])], [b["id"]])
        with self.assertRaises(MediaError) as error:
            self.state.note_image_delete(note["id"], a["id"])
        self.assertEqual(error.exception.code, "IMAGE_NOT_FOUND")
        self.state.note_delete(note["id"], {"expectedRevision": 1})
        self.assertEqual(list((self.folder() / "attachments").iterdir()), [])

    def test_a_name_that_climbs_out_is_refused(self):
        note = self.state.note_create({"title": "Trip", "body": "Notes"})
        for bad in ("../x", "a/b", ""):
            with self.assertRaises(MediaError):
                self.state.note_image_get(note["id"], bad)

    def test_database_pictures_stay_readable_then_move_and_lines_are_rewritten(self):
        note = self.state.note_create({"title": "Old", "body": "x"})
        other = self.state.note_create({"title": "Plain", "body": "no pictures"})
        old_line = f"![Picture](/v1/notes/{note['id']}/images/legacy-1)"
        self.state.note_update(note["id"], {"title": "Old", "body": f"words\n{old_line}\n", "expectedRevision": 1})
        with self.state._db() as db:
            db.execute("INSERT INTO note_images VALUES(?,?,?,?)", ("legacy-1", note["id"], PNG + b"old", 1))
        self.assertEqual(self.state.note_image_get(note["id"], "legacy-1"), PNG + b"old")
        before = self.state.note_get(note["id"])
        result = self.state.migrate_note_pictures()
        self.assertEqual(result, {"moved": 1, "rewritten": 1})
        rel = f"attachments/{note['id']}-legacy-1.png"
        self.assertIn(f"![Picture]({rel})", self.state.note_get(note["id"])["body"])
        self.assertEqual((self.folder() / rel).read_bytes(), PNG + b"old")
        self.assertEqual(self.state.note_image_get(note["id"], "legacy-1"), PNG + b"old")
        with self.state._db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM note_images").fetchone()[0], 0)
        after = self.state.note_get(note["id"])
        self.assertEqual(after["updatedAt"], before["updatedAt"])
        self.assertEqual(self.state.note_get(other["id"])["body"], "no pictures")
        # a second run finds nothing left to do
        self.assertEqual(self.state.migrate_note_pictures(), {"moved": 0, "rewritten": 0})


if __name__ == "__main__":
    unittest.main()
