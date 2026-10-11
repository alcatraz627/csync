import http.client
import json
import os
import re
import subprocess
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest import mock
from pathlib import Path

from media.library import Drive, Library
from media.notes_store import NotesFolder, between, parse, spread
from media.server import State, handler_for


def write_note(folder: Path, note_id: str, created: str, **extra) -> None:
    lines = ["---", f'title: "{note_id}"', f"created: {created}"]
    lines += [f"{k}: {v}" for k, v in extra.items()]
    lines += ["---", "body of " + note_id, ""]
    (folder / (note_id + ".md")).write_text("\n".join(lines))


class BetweenTest(unittest.TestCase):
    def test_the_seven_vectors(self):
        for a, b, want in [("", None, "i"), ("i", None, "r"), ("", "i", "9"), ("a", "b", "ai"),
                           ("a", "ai", "a9"), ("az", "b", "azi"), ("1", "2", "1i")]:
            self.assertEqual(between(a, b), want, (a, b))

    def test_twenty_inserts_into_one_gap_stay_ordered(self):
        lo, hi = "a", "b"
        for _ in range(20):
            mid = between(lo, hi)
            self.assertTrue(lo < mid < hi and not mid.endswith("0"), (lo, mid, hi))
            hi = mid
        lo, hi = "a", "b"
        for _ in range(20):
            mid = between(lo, hi)
            self.assertTrue(lo < mid < hi and not mid.endswith("0"), (lo, mid, hi))
            lo = mid

    def test_spread(self):
        self.assertEqual(spread(1), ["i"])
        for n in (2, 5, 60, 46655):
            keys = spread(n)
            self.assertEqual((len(keys), keys == sorted(set(keys))), (n, True))
            self.assertFalse(any(k.endswith("0") for k in keys))


class OrderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name) / "notes"
        self.store = NotesFolder(self.folder)
        # created: A oldest .. E newest, so the unarranged order is E D C B A
        for i, name in enumerate("ABCDE"):
            write_note(self.folder, name, f"2026-10-0{i + 1}T10:00:00Z")
        self.store.commit("fixtures")

    def ids(self):
        return [n["id"] for n in self.store.all()]

    def changed_files(self):
        out = subprocess.run(["git", "show", "--name-only", "--format=%s", "HEAD"], cwd=self.folder,
                             capture_output=True, text=True).stdout.split()
        return out

    def test_unarranged_notes_are_newest_first_and_pinned_lead(self):
        self.assertEqual(self.ids(), list("EDCBA"))
        self.store.set_meta("A", pinned=True)
        self.assertEqual(self.ids(), list("AEDCB"))

    def test_pos_reads_back_and_writes_bare(self):
        write_note(self.folder, "P", "2026-10-09T10:00:00Z", pos="i")
        note = self.store.read("P")
        self.assertEqual(note["pos"], "i")
        self.store.set_meta("P", color="red")
        self.assertIn("\npos: i\n---\n", (self.folder / "P.md").read_text())

    def test_awkward_pos_values_come_back_as_the_same_strings(self):
        for raw in ("no", "1e5", "null"):
            write_note(self.folder, "Q", "2026-10-09T10:00:00Z", pos=raw)
            self.assertEqual(self.store.read("Q")["pos"], raw)
            self.assertEqual(parse((self.folder / "Q.md").read_text())[0]["pos"], raw)
            self.store.set_meta("Q", color="blue")
            self.assertIn(f"\npos: {raw}\n---\n", (self.folder / "Q.md").read_text())
            self.assertEqual(self.store.read("Q")["pos"], raw)

    def test_comparator_arranged_below_unarranged_and_by_bytes(self):
        write_note(self.folder, "X", "2026-01-01T00:00:00Z", pos="b")
        write_note(self.folder, "Y", "2026-01-02T00:00:00Z", pos="a")
        write_note(self.folder, "Z", "2026-01-03T00:00:00Z", pos="a")   # ties break by id
        self.assertEqual(self.ids(), list("EDCBA") + ["Y", "Z", "X"])

    def test_pos_is_kept_while_pinned_and_unpin_returns_the_place(self):
        self.store.set_meta("C", after="E")
        before = self.ids()
        self.store.set_meta("C", pinned=True)
        self.assertEqual(self.ids()[0], "C")
        self.store.set_meta("C", pinned=False)
        self.assertEqual(self.ids(), before)

    def test_move_after_settles_once_then_writes_one_file(self):
        self.store.set_meta("A", after="E")             # A directly under E
        self.assertEqual(self.ids(), list("EADCB"))
        first = self.changed_files()
        self.assertEqual(first[0], "move")
        self.assertGreater(len(first), 2)               # the one-time settle touched the others
        self.store.set_meta("B", after="E")
        self.assertEqual(self.ids(), list("EBADC"))
        self.assertEqual(self.changed_files(), ["move", "B.md"])
        self.store.set_meta("C", after=None)
        self.assertEqual(self.ids(), list("CEBAD"))
        self.assertEqual(self.changed_files(), ["move", "C.md"])
        self.store.set_meta("C", after="D")             # last place
        self.assertEqual(self.ids(), list("EBADC"))
        self.assertEqual(self.changed_files(), ["move", "C.md"])

    def test_move_to_top_beats_a_note_nobody_arranged(self):
        self.store.set_meta("A", after="E")
        write_note(self.folder, "F", "2026-10-10T10:00:00Z")   # new, no pos
        self.assertEqual(self.ids()[0], "F")
        self.store.set_meta("D", after=None)
        self.assertEqual(self.ids()[0], "D")

    def test_move_stays_in_its_pin_group(self):
        self.store.set_meta("A", pinned=True)
        for bad in ("E", "nope", "C"):
            with self.assertRaises(Exception) as ctx:
                self.store.set_meta("B", after="A") if bad == "E" else self.store.set_meta("A", after=bad)
            self.assertEqual(ctx.exception.code, "NOTE_INVALID")
        with self.assertRaises(Exception):
            self.store.set_meta("B", after="B")
        self.assertEqual(self.ids(), list("AEDCB"))

    def test_a_move_changes_only_the_pos_line_even_in_an_awkward_file(self):
        raw = ('---\r\ntitle: "Odd"\r\ncreated: 2026-10-07T10:00:00Z\r\npinned: false\r\n'
               'tags: [a, b]\r\nmood: calm\r\n---\r\nbody line\r\n')
        (self.folder / "O.md").write_bytes(raw.encode())
        self.store.commit("odd")
        self.store.set_meta("A", after="O")              # settles O too: it is unarranged and above A
        mine = (self.folder / "O.md").read_bytes().decode()
        self.assertEqual(mine.replace("\r\npos: ", "\r\nPOS: ").split("POS: ")[0] + mine.split("\r\n---\r\n", 1)[1],
                         raw.split("\r\n---\r\n", 1)[0] + "\r\n" + raw.split("\r\n---\r\n", 1)[1])
        self.assertIn("\r\npos: ", mine)
        self.assertFalse(self.store.read("O").get("pinned"))   # "pinned: false" never turns into a pin

    def test_rewriting_a_note_with_pinned_false_does_not_pin_it(self):
        write_note(self.folder, "R", "2026-10-07T10:00:00Z", pinned="false")
        self.assertFalse(self.store.read("R").get("pinned"))
        self.store.set_meta("R", color="red")
        self.assertFalse(self.store.read("R").get("pinned"))

    def test_move_with_unusable_neighbour_pos_does_not_crash(self):
        write_note(self.folder, "W", "2026-01-01T00:00:00Z", pos="NOT OK!")
        self.store.set_meta("E", after="W")
        self.assertEqual(self.ids().index("E"), self.ids().index("W") + 1)

    def commit_on(self, when: str, reason: str) -> None:
        with mock.patch.dict(os.environ, {"GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when}):
            self.store.commit(reason)

    def edit_times(self) -> dict[str, int]:
        return {n["id"]: n["updatedAt"] for n in self.store.all()}

    def test_a_move_or_settle_never_changes_an_edit_time(self):
        # G has two real saves, long ago; the fixtures A..E have one commit each (their import)
        old = "2026-09-01T09:00:00Z"
        write_note(self.folder, "G", "2026-08-01T10:00:00Z")
        self.commit_on(old, "save (phone)")
        (self.folder / "G.md").write_text((self.folder / "G.md").read_text().replace("body of G", "second words"))
        self.commit_on(old, "save (phone)")
        before = self.edit_times()
        self.assertEqual(before["G"], 1788253200)    # 2026-09-01T09:00:00Z
        self.store.set_meta("A", after="E")          # the first move settles every note in the group
        self.assertGreater(len(self.changed_files()), 3)
        self.store.set_meta("B", after=None)         # a later one-file move
        self.assertEqual(self.edit_times(), before)
        # the note count of commits still moves, so a save made on the old revision still clashes
        self.assertEqual(self.store.revision("G"), 3)

    def test_a_real_edit_still_moves_the_edit_time(self):
        old = "2026-09-01T09:00:00Z"
        write_note(self.folder, "G", "2026-08-01T10:00:00Z")
        self.commit_on(old, "save (phone)")
        (self.folder / "G.md").write_text((self.folder / "G.md").read_text().replace("body of G", "second words"))
        self.commit_on(old, "save (phone)")
        self.store.set_meta("G", after=None)
        self.assertEqual(self.store.read("G")["updatedAt"], 1788253200)
        self.store.update("G", "G", "third words", self.store.revision("G"))
        self.assertGreater(self.store.read("G")["updatedAt"], 1788253200 + 86400)


class ReminderKeysTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name) / "notes"
        self.store = NotesFolder(self.folder)
        write_note(self.folder, "N", "2026-10-01T10:00:00Z", remind_at="2026-10-12T09:30:00Z",
                   remind_repeat="weekly", reminder_id='"EK-1"')
        self.store.commit("fixture")

    def test_shape_returns_the_three_keys(self):
        note = self.store.read("N")
        self.assertEqual((note["remindAt"], note["remindRepeat"], note.get("remindOn")), (1791797400, "weekly", None))

    def test_set_and_clear_and_key_order(self):
        self.store.set_meta("N", remind_on="phone")
        text = (self.folder / "N.md").read_text()
        self.assertIn("remind_repeat: weekly\nremind_on: phone\nreminder_id:", text)
        self.assertEqual(self.store.read("N")["remindOn"], "phone")
        self.store.set_meta("N", remind_at=1791711000, remind_repeat="daily", remind_on="mac")
        note = self.store.read("N")
        self.assertEqual((note["remindAt"], note["remindRepeat"], note["remindOn"]), (1791711000, "daily", "mac"))
        self.assertIn("remind_at: 2026-10-11T09:30:00Z\n", (self.folder / "N.md").read_text())
        self.store.set_meta("N", remind_on=None)
        self.assertNotIn("remindOn", self.store.read("N"))
        self.store.set_meta("N", remind_at=None)
        note = self.store.read("N")
        self.assertEqual([k in note for k in ("remindAt", "remindRepeat", "remindOn")], [False] * 3)
        self.assertEqual(note["revision"], 5)

    def test_bad_values_are_refused_and_nothing_is_written(self):
        before = (self.folder / "N.md").read_text()
        for kw in ({"remind_on": "tablet"}, {"remind_repeat": "hourly"}, {"remind_at": "tomorrow"},
                   {"remind_at": True}, {"remind_at": -5}):
            with self.assertRaises(Exception) as ctx:
                self.store.set_meta("N", **kw)
            self.assertEqual(ctx.exception.code, "NOTE_INVALID", kw)
        self.assertEqual((self.folder / "N.md").read_text(), before)

    def test_a_note_save_keeps_the_keys(self):
        self.store.set_meta("N", remind_on="phone")
        self.store.update("N", "N", "new words", self.store.revision("N"))
        self.assertEqual(self.store.read("N")["remindOn"], "phone")


class OrderHttpTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        library = Library([Drive("disk1", "Test USB", Path(self.tmp.name), "u")], "secret", fixture_mounts=True)
        self.state = State(library, Path(self.tmp.name) / "history.db", notes_folder=Path(self.tmp.name) / "notes")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(self.state, "secret"))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def call(self, method, path, body=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {"X-Csync-Token": "secret"}
        if body is not None:
            body, headers["Content-Type"] = json.dumps(body).encode(), "application/json"
        conn.request(method, path, body, headers)
        r = conn.getresponse()
        data = r.read()
        conn.close()
        return r.status, json.loads(data)

    def test_meta_after_over_http_and_list_order(self):
        ids = [self.call("POST", "/v1/notes", {"title": t, "body": "x"})[1]["note"]["id"] for t in "abc"]
        # same-second saves tie on created, so give them distinct times: newest first until arranged is c b a
        for i, note_id in enumerate(ids):
            f = Path(self.tmp.name) / "notes" / (note_id + ".md")
            f.write_text(re.sub(r"(?m)^created: .*$", f"created: 2026-10-0{i + 1}T00:00:00Z", f.read_text()))
        listed = lambda: [n["id"] for n in self.call("GET", "/v1/notes")[1]["notes"]]
        self.assertEqual(listed(), ids[::-1])
        status, body = self.call("PUT", f"/v1/notes/{ids[0]}/meta", {"after": ids[2]})
        self.assertEqual((status, bool(body["note"].get("pos"))), (200, True))
        self.assertEqual(listed(), [ids[2], ids[0], ids[1]])
        self.assertEqual(self.call("PUT", f"/v1/notes/{ids[0]}/meta", {"after": None})[0], 200)
        self.assertEqual(listed()[0], ids[0])
        status, body = self.call("PUT", f"/v1/notes/{ids[0]}/meta", {"after": 5})
        self.assertEqual((status, body["code"]), (400, "NOTE_INVALID"))
        status, body = self.call("PUT", f"/v1/notes/{ids[0]}/meta", {"after": "missing"})
        self.assertEqual((status, body["code"]), (400, "NOTE_INVALID"))
        status, body = self.call("PUT", f"/v1/notes/{ids[0]}/meta", {"remindAt": 1791711000, "remindOn": "phone"})
        self.assertEqual((status, body["note"]["remindAt"], body["note"]["remindOn"]), (200, 1791711000, "phone"))
        for bad in ({"remindAt": "soon"}, {"remindOn": "tablet"}, {"remindRepeat": 3}, {"remindAt": True}):
            status, body = self.call("PUT", f"/v1/notes/{ids[0]}/meta", bad)
            self.assertEqual((status, body["code"]), (400, "NOTE_INVALID"), bad)
        status, body = self.call("GET", f"/v1/notes/{ids[0]}")
        self.assertEqual(body["note"]["remindOn"], "phone")
        status, body = self.call("GET", "/v1/notes")
        self.assertEqual({n["id"]: n.get("remindOn") for n in body["notes"]}[ids[0]], "phone")
        status, body = self.call("PUT", f"/v1/notes/{ids[0]}/meta", {"color": "red"})
        self.assertEqual((status, body["note"].get("pos") is not None), (200, True))


if __name__ == "__main__":
    unittest.main()
