import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentbox import audit, bwrap
from agentbox.policy import Policy


class BwrapArgsTests(unittest.TestCase):
    def test_network_deny_unshares_net(self):
        args = bwrap.render_args(Policy(), "/tmp/work")
        self.assertIn("--unshare-net", args)

    def test_network_allow_keeps_net(self):
        args = bwrap.render_args(Policy(network="allow"), "/tmp/work")
        self.assertNotIn("--unshare-net", args)

    def test_workdir_bound_writable(self):
        workdir = str(Path("/tmp/work").resolve())
        args = bwrap.render_args(Policy(), "/tmp/work")
        i = args.index("--bind")
        self.assertEqual(args[i + 1 : i + 3], [workdir, workdir])

    def test_existing_deny_read_masked_with_tmpfs(self):
        secret = tempfile.mkdtemp()
        pol = Policy(deny_read=(secret,))
        args = bwrap.render_args(pol, "/tmp/work")
        i = len(args) - 1 - args[::-1].index("--tmpfs")
        self.assertEqual(args[i + 1], secret)

    def test_missing_deny_read_skipped(self):
        pol = Policy(deny_read=("/nonexistent/agentbox-nope",))
        args = bwrap.render_args(pol, "/tmp/work")
        self.assertNotIn("/nonexistent/agentbox-nope", args)

    def test_ends_with_separator(self):
        self.assertEqual(bwrap.render_args(Policy(), "/tmp/work")[-1], "--")


@unittest.skipUnless(sys.platform.startswith("linux"), "bwrap backend is Linux-only")
class BwrapIntegrationTests(unittest.TestCase):
    """End-to-end on Linux: writes inside the workdir succeed, outside fail."""

    @classmethod
    def setUpClass(cls):
        import shutil
        import subprocess

        if shutil.which("bwrap") is None:
            raise unittest.SkipTest("bubblewrap not installed")
        cls.workdir = Path(tempfile.mkdtemp())
        cls.prefix = bwrap.render_args(Policy(), cls.workdir)
        probe = subprocess.run(
            cls.prefix + ["/bin/echo", "ok"], capture_output=True, cwd=cls.workdir
        )
        if probe.returncode != 0:
            raise unittest.SkipTest(
                f"bwrap unavailable here: {probe.stderr.decode().strip()}"
            )

    def _run(self, *cmd):
        import subprocess

        return subprocess.run(self.prefix + list(cmd), capture_output=True, cwd=self.workdir)

    def test_write_inside_workdir_allowed(self):
        target = self.workdir / "out.txt"
        proc = self._run("/usr/bin/touch", str(target))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(target.exists())

    def test_write_outside_workdir_blocked(self):
        outside = Path.home() / "agentbox-escape-test.txt"
        proc = self._run("/usr/bin/touch", str(outside))
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(outside.exists())

    def test_network_blocked(self):
        proc = self._run("/bin/sh", "-c", "command -v getent && getent hosts example.com")
        self.assertNotEqual(proc.returncode, 0)


@unittest.skipUnless(sys.platform == "darwin", "Seatbelt backend is macOS-only")
class SandboxSdkTests(unittest.TestCase):
    def test_run_logs_and_returns(self):
        from agentbox.sandbox import Sandbox

        workdir = Path(tempfile.mkdtemp())
        log = workdir / "audit.jsonl"
        box = Sandbox(Policy(), workdir=workdir, log_path=log)
        proc = box.run(["/bin/echo", "hi"], capture_output=True)
        if proc.returncode != 0:  # nested-sandbox hosts can't run sandbox-exec
            self.skipTest(f"sandbox-exec unavailable: {proc.stderr!r}")
        self.assertEqual(proc.stdout.strip(), b"hi")
        self.assertEqual(audit.verify(log), 2)
        self.assertEqual(box.backend, "seatbelt")


if __name__ == "__main__":
    unittest.main()
