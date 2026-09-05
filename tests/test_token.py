"""Token round trip and duration parsing."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csync import invite  # noqa: E402
from csync.errors import CsyncError  # noqa: E402


class TokenTests(unittest.TestCase):
    def test_round_trip_keeps_every_field_and_spaces(self):
        fields = {"v": 1, "id": "3f9c2e1a", "name": "rahul-mbp", "route": "auto", "exp": 1757104800, "ttl": 14400,
                  "lan": "192.168.1.103:5122", "funnel": "aakarshs-m5-pro.tail905820.ts.net:10000", "relay_user": "alcatraz627",
                  "relay_hostkey": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIExample", "port": 5201, "target_port": 22,
                  "console_pub": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIConsole", "console_name": "Aakarsh's Mac",
                  "src": "file:///tmp/csync", "gate_sha": "a" * 64, "teardown_sha": "b" * 64, "teardown_root_sha": "c" * 64,
                  "invite_key_b64": "LS0tLS1CRUdJTiBPUEVOU1NIIFBSSVZBVEUgS0VZLS0tLS0="}
        tok = invite.build_token(fields)
        self.assertNotIn("\n", tok)
        back = invite.parse_token(tok)
        for k, v in fields.items():
            self.assertEqual(back[k], str(v), k)

    def test_durations(self):
        self.assertEqual(invite.parse_duration("4h"), 14400)
        self.assertEqual(invite.parse_duration("30m"), 1800)
        self.assertEqual(invite.parse_duration("1d"), 86400)
        self.assertEqual(invite.parse_duration("90"), 90)
        with self.assertRaises(CsyncError):
            invite.parse_duration("soon")

    def test_names(self):
        self.assertTrue(invite.NAME_RE.match("rahul-mbp"))
        self.assertFalse(invite.NAME_RE.match("Rahul"))
        self.assertFalse(invite.NAME_RE.match("a"))
        self.assertFalse(invite.NAME_RE.match("-x"))


if __name__ == "__main__":
    unittest.main()
