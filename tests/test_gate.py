"""The gate writes a record the target's own owner can read.

Drives target/gate.sh the way sshd does, with SSH_ORIGINAL_COMMAND set and the
script arriving on stdin, against a throwaway copy so the real log is untouched.
"""

import os
import shutil
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(REPO, "target", "gate.sh")


class Gate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="csync-gate-")
        self.gate = os.path.join(self.tmp, "gate.sh")
        shutil.copy(GATE, self.gate)
        os.chmod(self.gate, 0o755)
        self.log = os.path.join(self.tmp, "session.log")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def call(self, cmd, stdin=b""):
        env = dict(os.environ, SSH_ORIGINAL_COMMAND=cmd)
        p = subprocess.run([self.gate], input=stdin, capture_output=True, env=env)
        return p.returncode, p.stdout.decode(errors="replace"), p.stderr.decode(errors="replace")

    def lines(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log) as fh:
            return [l for l in fh.read().splitlines() if l.strip()]

    def last(self):
        return self.lines()[-1]

    def test_a_streamed_op_says_what_it_did(self):
        rc, out, _ = self.call("CSYNC_OP=shot bash -s -- 1", b'echo "ran with $1"\n')
        self.assertIn("ran with 1", out)
        self.assertIn("bash -s -- 1", self.last())
        self.assertIn("(took a screenshot)", self.last())

    def test_the_raw_command_is_never_replaced_by_the_phrase(self):
        # A console that lies about which op it is running cannot hide the command,
        # because both go on the line.
        self.call("CSYNC_OP=say uname -a")
        self.assertIn("uname -a", self.last())
        self.assertIn("(spoke a message out loud)", self.last())

    def test_liveness_probe_is_not_written_down(self):
        rc, _, _ = self.call("true")
        self.assertEqual(rc, 0)
        self.assertEqual(self.lines(), [])

    def test_a_plain_command_logs_exactly_as_before(self):
        self.call("uname -a")
        self.assertNotIn("(", self.last())
        self.assertIn("uname -a", self.last())

    def test_force_still_marks_the_line(self):
        self.call("CSYNC_FORCE=1 mkfs.ext4 /dev/null")
        self.assertIn("[force]", self.last())

    def test_deny_list_fires_underneath_an_op_marker(self):
        rc, _, err = self.call("CSYNC_OP=info mkfs.ext4 /dev/null")
        self.assertEqual(rc, 126)
        self.assertIn("refused: mkfs", err)

    def test_an_unknown_key_is_named_not_described(self):
        self.call("CSYNC_OP=wibble echo hi")
        self.assertIn("(ran the wibble operation)", self.last())

    def test_a_key_that_is_not_a_bare_lowercase_name_is_dropped(self):
        # Guards the log against prose arriving from the console. 'UPPER' is here
        # because a bracket range written a-z matches it under most locales, which
        # is how this leaked the first time.
        for bad in ["a;rm", "took-a-nap' and stole", "UPPER", "MiXeD", "op.name", "a/b"]:
            with self.subTest(key=bad):
                self.call("CSYNC_OP=%s echo hi" % bad)
                self.assertNotIn("(", self.last())

    def test_both_markers_together(self):
        self.call("CSYNC_FORCE=1 CSYNC_OP=logs bash -s --", b"echo ok\n")
        self.assertIn("(collected log files)", self.last())
        self.assertIn("[force]", self.last())

    def test_every_op_the_console_streams_has_wording_here(self):
        # ops/*.sh is the set stream_script can send; a new one must not reach the
        # owner's log as "ran the X operation".
        ops = sorted(f[:-3] for f in os.listdir(os.path.join(REPO, "ops")) if f.endswith(".sh"))
        self.assertTrue(ops, "no ops found")
        for op in ops:
            with self.subTest(op=op):
                self.call("CSYNC_OP=%s echo hi" % op)
                self.assertNotIn("ran the %s operation" % op, self.last())


if __name__ == "__main__":
    unittest.main()
