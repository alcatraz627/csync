import http.client
import json
import subprocess
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from media.library import Drive, Library, MediaError
from media.notes_store import NotesFolder
from media.reminders_store import RemindersFolder
from media.server import State, handler_for

NOW = 1_760_198_400_000   # 2025-10-11T16:00:00Z in epoch ms


class Clock:
    def __init__(self, now=NOW):
        self.now = now

    def __call__(self):
        return self.now


def timer(**over):
    return {"kind": "timer", "label": "Pasta", "color": "orange", "total_ms": 600_000, "fire_at": NOW + 600_000,
            "target": "phone", **over}


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.notes = NotesFolder(Path(self.tmp.name) / "notes")
        self.clock = Clock()
        self.store = RemindersFolder(self.notes, self.clock)
        self.root = self.store.root

    def head_files(self):
        out = subprocess.run(["git", "show", "--name-only", "--format=%s", "HEAD"], cwd=self.notes.folder,
                             capture_output=True, text=True).stdout.split("\n")
        return [line for line in out if line]

    def code(self, fn, *a):
        with self.assertRaises(MediaError) as ctx:
            fn(*a)
        return ctx.exception.code

    # templates
    def test_templates_newest_first_and_only_their_own_file_changes(self):
        a, _ = self.store.template_add({"label": "Tea", "minutes": 3, "color": "green"})
        self.clock.now += 5000
        b, _ = self.store.template_add({"label": "Pasta", "minutes": 10})
        self.assertEqual([t["id"] for t in self.store.templates()], [b["id"], a["id"]])
        self.assertEqual(self.head_files(), ["template: add", f".reminders/templates/{b['id']}.json"])
        updated = self.store.template_update(a["id"], {"label": "Green tea", "minutes": 4, "color": "green"})
        self.assertEqual((updated["label"], updated["minutes"], updated["created"]), ("Green tea", 4, a["created"]))
        self.assertEqual(self.head_files(), ["template: edit", f".reminders/templates/{a['id']}.json"])
        self.store.template_delete(a["id"])
        self.assertEqual([t["id"] for t in self.store.templates()], [b["id"]])
        self.assertEqual(self.code(self.store.template_delete, a["id"]), "RUN_NOT_FOUND")

    def test_template_validation_and_idempotent_seed(self):
        for bad in ({"label": "", "minutes": 3}, {"label": "x", "minutes": 0}, {"label": "x", "minutes": "3"},
                    {"label": "x", "minutes": 3, "color": "mauve"}, {"label": "x" * 81, "minutes": 3}):
            self.assertEqual(self.code(self.store.template_add, bad), "RUN_INVALID", bad)
        first, created = self.store.template_add({"id": "t-seed-1", "label": "Tea", "minutes": 3})
        again, created_again = self.store.template_add({"id": "t-seed-1", "label": "Changed", "minutes": 9})
        self.assertEqual((created, created_again, again["label"]), (True, False, "Tea"))
        self.assertEqual(self.code(self.store.template_add, {"id": "../x", "label": "x", "minutes": 3}), "RUN_INVALID")

    # runs
    def test_a_run_writes_only_its_request_and_waits_for_its_target(self):
        row, created = self.store.run_add(timer())
        self.assertTrue(created)
        self.assertEqual((row["status"], row["waitingFor"], row["from"], row["target"]), ("waiting", "phone", "phone", "phone"))
        self.assertEqual(self.head_files(), ["run: request to phone", f".reminders/runs/{row['id']}.json"])
        self.assertFalse((self.root / "runs" / (row["id"] + ".state.json")).exists())

    def test_one_writer_per_file_the_phone_cannot_write_a_mac_runs_state(self):
        row, _ = self.store.run_add(timer(target="mac"))
        self.assertEqual(self.code(self.store.run_state, row["id"], {"status": "running"}), "RUN_NOT_YOURS")
        self.assertEqual(self.code(self.store.device_set, "mac", {"running": []}), "RUN_NOT_YOURS")
        self.assertFalse((self.root / "runs" / (row["id"] + ".state.json")).exists())

    def test_request_sent_twice_is_one_run(self):
        first, c1 = self.store.run_add(timer(id="r-outbox-1"))
        second, c2 = self.store.run_add(timer(id="r-outbox-1", label="Other"))
        self.assertEqual((c1, c2, second["label"]), (True, False, "Pasta"))
        self.assertEqual(len(self.store.runs()["runs"]), 1)

    def test_state_flow_and_terminal_state_is_final(self):
        row, _ = self.store.run_add(timer())
        rid = row["id"]
        self.clock.now += 1000
        s = self.store.run_state(rid, {"status": "running", "end_ms": NOW + 600_000})
        self.assertEqual((s["status"], s["endMs"], s["waitingFor"], s["updatedAt"]), ("running", NOW + 600_000, None, NOW + 1000))
        self.assertEqual(self.head_files(), ["run: running", f".reminders/runs/{rid}.state.json"])
        self.store.run_state(rid, {"status": "ringing"})
        self.store.run_state(rid, {"status": "done"})
        self.assertEqual(self.store.run_state(rid, {"status": "done"})["status"], "done")
        self.assertEqual(self.code(self.store.run_state, rid, {"status": "running"}), "RUN_FINISHED")
        self.assertEqual(self.code(self.store.run_state, rid, {"status": "melting"}), "RUN_INVALID")

    def test_late_arrival_a_timer_is_missed_not_rung(self):
        row, _ = self.store.run_add(timer(total_ms=60_000, fire_at=NOW + 60_000))
        self.clock.now = NOW + 60_000 + 3 * 60_000     # picked up three minutes after it should have rung
        s = self.store.run_state(row["id"], {"status": "running", "end_ms": NOW + 60_000})
        self.assertEqual(s["status"], "missed")
        self.assertEqual(self.code(self.store.run_state, row["id"], {"status": "running"}), "RUN_FINISHED")

    def test_inside_the_grace_a_timer_still_runs(self):
        row, _ = self.store.run_add(timer(total_ms=60_000, fire_at=NOW + 60_000))
        self.clock.now = NOW + 60_000 + 119_000
        self.assertEqual(self.store.run_state(row["id"], {"status": "ringing"})["status"], "ringing")

    def test_late_reminder_rings_once_marked_missed_after_an_hour(self):
        row, _ = self.store.run_add({"kind": "reminder", "label": "Call", "fire_at": NOW + 1000, "target": "phone"})
        self.clock.now = NOW + 1000 + 61 * 60_000
        s = self.store.run_state(row["id"], {"status": "ringing"})
        self.assertEqual((s["status"], s["stateNote"]), ("ringing", "missed"))
        row2, _ = self.store.run_add({"kind": "reminder", "label": "Call", "fire_at": self.clock.now - 30 * 60_000, "target": "phone"})
        s2 = self.store.run_state(row2["id"], {"status": "ringing"})
        self.assertEqual((s2["status"], s2["stateNote"]), ("ringing", ""))

    def test_stop_file_is_written_once_and_not_for_finished_runs(self):
        row, _ = self.store.run_add(timer())
        rid = row["id"]
        self.store.run_state(rid, {"status": "running"})
        stopped = self.store.run_stop(rid)
        self.assertTrue(stopped["stopRequested"])
        self.assertEqual(self.head_files(), ["run: stop requested", f".reminders/runs/{rid}.stop"])
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.notes.folder, capture_output=True, text=True).stdout
        self.store.run_stop(rid)
        self.assertEqual(subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.notes.folder, capture_output=True, text=True).stdout, head)
        self.assertEqual(self.code(self.store.run_stop, "r-nope"), "RUN_NOT_FOUND")
        self.store.run_state(rid, {"status": "stopped"})
        other, _ = self.store.run_add(timer())
        self.store.run_state(other["id"], {"status": "done"})
        self.assertFalse(self.store.run_stop(other["id"])["stopRequested"])

    def test_run_validation(self):
        for bad in (timer(kind="alarm"), timer(target="tv"), timer(label=""), timer(fire_at="soon"),
                    timer(fire_at=True), timer(total_ms=10), timer(total_ms=None), timer(color="mauve"),
                    timer(id="../x"), timer(template=5)):
            if bad.get("total_ms", 0) is None:
                bad = {k: v for k, v in bad.items() if k != "total_ms"}
            self.assertEqual(self.code(self.store.run_add, bad), "RUN_INVALID", bad)
        self.assertEqual(list((self.root / "runs").iterdir()), [])

    def test_runs_merge_state_and_device_and_staleness(self):
        row, _ = self.store.run_add(timer(target="mac"))
        (self.root / "devices" / "mac.json").write_text(json.dumps({"seen_at": NOW - 120_000, "running": [{"run": "r-x", "label": "Tea", "end_ms": NOW}]}))
        listed = self.store.runs()
        self.assertEqual((listed["runs"][0]["waitingFor"], listed["runs"][0]["staleSeconds"]), ("mac", 120))
        self.assertEqual(listed["devices"]["mac"]["staleSeconds"], 120)
        (self.root / "runs" / (row["id"] + ".state.json")).write_text(json.dumps({"status": "running", "updated_at": NOW - 5000, "end_ms": NOW + 1, "remain_ms": None, "note": ""}))
        r = self.store.runs()["runs"][0]
        self.assertEqual((r["status"], r["waitingFor"], r["staleSeconds"]), ("running", None, 5))

    def test_runs_newest_first(self):
        a, _ = self.store.run_add(timer())
        self.clock.now += 1000
        b, _ = self.store.run_add(timer())
        self.assertEqual([r["id"] for r in self.store.runs()["runs"]], [b["id"], a["id"]])

    def test_device_file_is_not_rewritten_for_a_heartbeat(self):
        running = [{"run": "r-1", "label": "Tea", "end_ms": NOW + 5000}]
        first = self.store.device_set("phone", {"running": running})
        self.assertTrue(first["written"])
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.notes.folder, capture_output=True, text=True).stdout
        self.clock.now += 5 * 60_000
        self.assertFalse(self.store.device_set("phone", {"running": running})["written"])
        self.assertEqual(subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.notes.folder, capture_output=True, text=True).stdout, head)
        self.clock.now += 6 * 60_000
        self.assertTrue(self.store.device_set("phone", {"running": running})["written"])
        self.assertTrue(self.store.device_set("phone", {"running": []})["written"])
        self.assertEqual(self.code(self.store.device_set, "phone", {"running": [{"run": "../x", "label": "a", "end_ms": 1}]}), "RUN_INVALID")

    def test_cleanup_rules(self):
        done, _ = self.store.run_add(timer())                       # aimed at the phone, ends, then 25 hours pass
        self.store.run_state(done["id"], {"status": "done"})
        mac_done, _ = self.store.run_add(timer(target="mac"))       # the Mac's own to clean
        (self.root / "runs" / (mac_done["id"] + ".state.json")).write_text(json.dumps({"status": "done", "updated_at": NOW}))
        unanswered, _ = self.store.run_add(timer(target="mac"))     # never picked up
        fresh, _ = self.store.run_add(timer())
        (self.root / "runs" / "r-orphan.stop").write_text("")
        self.clock.now = NOW + 25 * 3600_000
        removed = self.store.cleanup(force=True)
        self.assertIn("r-orphan.stop", removed)
        self.assertIn(done["id"] + ".json", removed)
        self.assertIn(done["id"] + ".state.json", removed)
        self.assertFalse(any(mac_done["id"] in name for name in removed))
        self.assertFalse(any(unanswered["id"] in name for name in removed))
        self.clock.now = NOW + 8 * 24 * 3600_000
        removed = self.store.cleanup(force=True)
        self.assertIn(unanswered["id"] + ".json", removed)
        self.assertIn(fresh["id"] + ".json", removed)        # the phone's own, never answered for 7 days
        self.assertFalse(any(mac_done["id"] in name for name in removed))   # the Mac removes its own
        self.assertEqual(self.head_files()[0], "runs: cleanup")

    def test_cleanup_is_rate_limited_on_the_listing(self):
        row, _ = self.store.run_add(timer())
        self.store.run_state(row["id"], {"status": "done"})
        self.clock.now = NOW + 24 * 3600_000 - 30_000
        self.assertEqual(self.store.cleanup(force=True), [])      # not 24 hours old yet
        self.clock.now = NOW + 24 * 3600_000 + 10_000
        self.store.runs()                                # inside the 60 s window since the last sweep: left alone
        self.assertTrue((self.root / "runs" / (row["id"] + ".json")).exists())
        self.clock.now += 61_000
        self.store.runs()
        self.assertFalse((self.root / "runs" / (row["id"] + ".json")).exists())


class HttpTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        library = Library([Drive("disk1", "Test USB", Path(self.tmp.name), "u")], "secret", fixture_mounts=True)
        self.state = State(library, Path(self.tmp.name) / "history.db", notes_folder=Path(self.tmp.name) / "notes")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(self.state, "secret"))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def call(self, method, path, body=None, token="secret"):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {"X-Csync-Token": token}
        if body is not None:
            body, headers["Content-Type"] = json.dumps(body).encode(), "application/json"
        conn.request(method, path, body, headers)
        r = conn.getresponse()
        data = r.read()
        conn.close()
        return r.status, json.loads(data)

    def test_every_route_needs_the_token(self):
        for method, path in (("GET", "/v1/runs"), ("POST", "/v1/runs"), ("GET", "/v1/templates"),
                             ("PUT", "/v1/devices/phone"), ("POST", "/v1/runs/r-1/stop")):
            self.assertEqual(self.call(method, path, {} if method != "GET" else None, token="wrong")[0], 401, path)

    def test_templates_and_runs_over_http(self):
        status, body = self.call("POST", "/v1/templates", {"label": "Tea", "minutes": 3, "color": "green"})
        self.assertEqual((status, body["template"]["kind"]), (201, "timer"))
        tid = body["template"]["id"]
        self.assertEqual(self.call("GET", "/v1/templates")[1]["templates"][0]["id"], tid)
        self.assertEqual(self.call("PUT", f"/v1/templates/{tid}", {"label": "Tea", "minutes": 4})[1]["template"]["minutes"], 4)
        status, body = self.call("POST", "/v1/templates", {"label": "", "minutes": 4})
        self.assertEqual((status, body["code"], body["field"]), (400, "RUN_INVALID", "label"))
        self.assertEqual(self.call("DELETE", f"/v1/templates/{tid}")[1], {"deleted": True, "id": tid})
        self.assertEqual(self.call("DELETE", f"/v1/templates/{tid}")[0], 404)

        fire = int(__import__("time").time() * 1000) + 600_000
        status, body = self.call("POST", "/v1/runs", {"kind": "timer", "label": "Pasta", "color": "orange",
                                                      "total_ms": 600_000, "fire_at": fire, "target": "mac"})
        self.assertEqual((status, body["run"]["status"], body["run"]["waitingFor"]), (201, "waiting", "mac"))
        rid = body["run"]["id"]
        self.assertEqual(self.call("PUT", f"/v1/runs/{rid}/state", {"status": "running"})[1]["code"], "RUN_NOT_YOURS")
        status, body = self.call("POST", f"/v1/runs/{rid}/stop")
        self.assertEqual((status, body["run"]["stopRequested"]), (200, True))
        status, body = self.call("POST", "/v1/runs", {"kind": "timer", "label": "Tea", "total_ms": 60_000,
                                                      "fire_at": fire, "target": "phone"})
        mine = body["run"]["id"]
        status, body = self.call("PUT", f"/v1/runs/{mine}/state", {"status": "running", "end_ms": fire})
        self.assertEqual((status, body["run"]["status"]), (200, "running"))
        status, body = self.call("PUT", "/v1/devices/phone", {"running": [{"run": mine, "label": "Tea", "end_ms": fire}]})
        self.assertEqual((status, body["written"]), (200, True))
        status, body = self.call("PUT", "/v1/devices/mac", {"running": []})
        self.assertEqual((status, body["code"]), (403, "RUN_NOT_YOURS"))
        status, body = self.call("GET", "/v1/runs")
        self.assertEqual(status, 200)
        self.assertEqual({r["id"] for r in body["runs"]}, {rid, mine})
        self.assertEqual(body["devices"]["phone"]["running"], [{"run": mine, "label": "Tea", "endMs": fire}])
        self.assertEqual(self.call("POST", f"/v1/runs/nope/stop")[0], 404)
        # the notes list never shows the .reminders folder
        self.assertEqual(self.call("GET", "/v1/notes")[1]["notes"], [])


if __name__ == "__main__":
    unittest.main()
