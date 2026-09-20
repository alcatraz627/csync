"""The disk section says what each volume is FOR, not just how full it is.

The Linux branch is exercised against stub lsblk/tune2fs on PATH, because the
console that runs these tests is a Mac and the answer this feature exists to give
only appears on a Linux target with a detached disk attached.
"""

import os
import shutil
import stat
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INFO = os.path.join(REPO, "ops", "info.sh")

# Two volumes mounted, one ext4 sitting detached, one swap. The detached one is
# the whole point: nothing but its superblock says what it was for.
LSBLK = r"""#!/bin/bash
args="$*"
case "$args" in
  *"-rno NAME,TYPE"*)  printf 'mmcblk0 disk\nmmcblk0p1 part\nmmcblk0p2 part\nsda part\nsdb part\n'; exit 0 ;;
esac
dev="${args##* }"
field="$(printf '%s' "$args" | sed -n 's/.*-rndo \([A-Z]*\).*/\1/p')"
case "$dev/$field" in
  */dev/mmcblk0p1/SIZE) ;;
esac
case "$dev" in
  /dev/mmcblk0p1) size=512M; fs=vfat; label=bootfs; mnt=/boot/firmware ;;
  /dev/mmcblk0p2) size=63G;  fs=ext4; label=rootfs; mnt=/ ;;
  /dev/sda)       size=137G; fs=ext4; label='';     mnt='' ;;
  /dev/sdb)       size=8G;   fs=swap; label='';     mnt='' ;;
  *)              size='';   fs='';   label='';     mnt='' ;;
esac
case "$field" in
  SIZE) printf '%s\n' "$size" ;;
  FSTYPE) printf '%s\n' "$fs" ;;
  LABEL) printf '%s\n' "$label" ;;
  MOUNTPOINT) printf '%s\n' "$mnt" ;;
esac
exit 0
"""

TUNE2FS_OK = r"""#!/bin/bash
printf 'Filesystem volume name:   <none>\n'
printf 'Last mounted on:          /media/alcatraz627/Elements\n'
exit 0
"""

TUNE2FS_DENIED = r"""#!/bin/bash
printf 'tune2fs: Permission denied while trying to open %s\n' "$2" >&2
exit 1
"""


class InfoDisk(unittest.TestCase):
    def setUp(self):
        self.bin = tempfile.mkdtemp(prefix="csync-info-")

    def tearDown(self):
        shutil.rmtree(self.bin, ignore_errors=True)

    def stub(self, name, body):
        p = os.path.join(self.bin, name)
        with open(p, "w") as fh:
            fh.write(body)
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def run_disk(self, force_linux=True):
        env = dict(os.environ)
        env["PATH"] = self.bin + os.pathsep + env["PATH"]
        if force_linux:
            # info.sh branches on uname -s; a stub uname puts us on the Linux path.
            self.stub("uname", '#!/bin/bash\n[ "$1" = "-s" ] && { echo Linux; exit 0; }\necho Linux\n')
        p = subprocess.run(["bash", INFO, "disk"], capture_output=True, text=True, env=env)
        return p.stdout

    def test_a_detached_ext4_reports_where_it_was_last_used(self):
        self.stub("lsblk", LSBLK)
        self.stub("tune2fs", TUNE2FS_OK)
        out = self.run_disk()
        self.assertIn("last used at /media/alcatraz627/Elements", out)

    def test_a_mounted_volume_reports_its_mount_point(self):
        self.stub("lsblk", LSBLK)
        self.stub("tune2fs", TUNE2FS_OK)
        out = self.run_disk()
        self.assertIn("mounted at /boot/firmware", out)
        self.assertIn("mounted at /", out)
        self.assertIn("bootfs", out)

    def test_whole_disks_are_not_listed_as_volumes(self):
        self.stub("lsblk", LSBLK)
        self.stub("tune2fs", TUNE2FS_OK)
        out = self.run_disk()
        self.assertNotIn("/dev/mmcblk0 ", out)

    def test_root_only_answer_says_so_instead_of_going_quiet(self):
        # The target user is unprivileged by design, so this is the common case on
        # a real target and it must not silently drop the volume.
        self.stub("lsblk", LSBLK)
        self.stub("tune2fs", TUNE2FS_DENIED)
        out = self.run_disk()
        self.assertIn("/dev/sda", out)
        self.assertIn("only readable as root", out)

    def test_missing_tune2fs_names_the_package_rather_than_blaming_permissions(self):
        self.stub("lsblk", LSBLK)
        out = self.run_disk()  # no tune2fs stub at all
        self.assertIn("needs tune2fs", out)
        self.assertNotIn("only readable as root", out)

    def test_a_non_ext_volume_is_not_claimed_to_have_a_last_use(self):
        self.stub("lsblk", LSBLK)
        self.stub("tune2fs", TUNE2FS_OK)
        out = self.run_disk()
        swap = [l for l in out.splitlines() if l.startswith("/dev/sdb")]
        self.assertEqual(len(swap), 1, out)
        self.assertNotIn("last used at", swap[0])

    def test_this_mac_answers_for_every_mounted_volume(self):
        # The Darwin branch, run for real against whatever is attached right now.
        p = subprocess.run(["bash", INFO, "disk"], capture_output=True, text=True)
        self.assertIn("## disk", p.stdout)
        self.assertIn("mounted at /", p.stdout)


if __name__ == "__main__":
    unittest.main()
