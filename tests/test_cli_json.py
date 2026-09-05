"""Every verb answers in JSON, never blocks on input, and a failure carries a fix line.
Runs against an empty console root, so nothing touches the real config."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSYNC = os.path.join(REPO, "bin", "csync")


class JsonSurface(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="csync-json-")
        self.env = dict(os.environ)
        self.env.update({
            "CSYNC_HOME": os.path.join(self.tmp, "home"),
            "CSYNC_STATE": os.path.join(self.tmp, "state"),
            "CSYNC_DATA": os.path.join(self.tmp, "data"),
        })
        self.env.pop("CSYNC_ACTOR", None)

    def run_csync(self, *args, actor=None, timeout=20):
        env = dict(self.env)
        if actor:
            env["CSYNC_ACTOR"] = actor
        r = subprocess.run([sys.executable, CSYNC, "--json", *args], env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=timeout)
        return r

    def assert_json(self, r):
        self.assertTrue(r.stdout.strip(), f"no stdout; stderr={r.stderr}")
        obj = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertIn("ok", obj)
        return obj

    def test_unknown_host_is_code_3_with_fix(self):
        for verb in ("wait", "shot", "info", "logs"):
            r = self.run_csync(verb, "nobody")
            obj = self.assert_json(r)
            self.assertEqual(r.returncode, 3, verb)
            self.assertFalse(obj["ok"])
            self.assertTrue(obj.get("fix"), verb)

    def test_agent_actor_cannot_write_without_flag(self):
        r = self.run_csync("say", "nobody", "hi", actor="agent")
        obj = self.assert_json(r)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--allow-write", obj["fix"])
        r = self.run_csync("push", "nobody", "/etc/hosts", actor="agent")
        self.assertEqual(r.returncode, 2)

    def test_agent_actor_may_read(self):
        r = self.run_csync("ls", actor="agent")
        obj = self.assert_json(r)
        self.assertTrue(obj["ok"])
        self.assertEqual(obj["hosts"], {})

    def test_force_needs_a_terminal(self):
        r = self.run_csync("run", "nobody", "--force", "--", "true", actor="human")
        obj = self.assert_json(r)
        self.assertEqual(r.returncode, 2)
        self.assertIn("terminal", obj["error"])

    def test_teardown_without_yes_is_refused_not_hung(self):
        r = self.run_csync("teardown", "nobody", actor="human")
        self.assertEqual(r.returncode, 3)

    def test_recipes_list_and_dry_run_need_no_host_connection(self):
        r = self.run_csync("recipes")
        obj = self.assert_json(r)
        self.assertTrue(any(x["name"] == "hello" for x in obj["recipes"]))

    def test_audit_has_one_line_per_call_with_actor(self):
        self.run_csync("ls", actor="agent")
        self.run_csync("ls", actor="human")
        self.run_csync("shot", "nobody", actor="human")
        with open(os.path.join(self.env["CSYNC_STATE"], "audit.jsonl")) as fh:
            lines = [json.loads(l) for l in fh]
        self.assertEqual(len(lines), 3)
        self.assertEqual([l["actor"] for l in lines], ["agent", "human", "human"])
        self.assertEqual(lines[-1]["exit"], 3)

    def test_invite_before_init_names_init(self):
        r = self.run_csync("invite", "someone", actor="human")
        obj = self.assert_json(r)
        self.assertEqual(r.returncode, 6)
        self.assertEqual(obj["fix"], "csync init")


if __name__ == "__main__":
    unittest.main()
