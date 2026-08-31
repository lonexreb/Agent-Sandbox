import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentbox import audit
from agentbox.audit import AuditLog
from agentbox.policy import DEFAULT_DENY_READ, Policy, PolicyError, load_policy
from agentbox.seatbelt import render_profile


class PolicyTests(unittest.TestCase):
    def test_defaults(self):
        p = Policy()
        self.assertEqual(p.network, "deny")
        self.assertEqual(p.deny_read, DEFAULT_DENY_READ)

    def test_load_and_expand(self):
        with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as fh:
            fh.write('name = "t"\nnetwork = "allow"\nallow_write = ["~/scratch"]\n')
        p = load_policy(fh.name)
        self.assertEqual(p.name, "t")
        self.assertEqual(p.network, "allow")
        self.assertNotIn("~", p.allow_write[0])

    def test_bad_network_rejected(self):
        with self.assertRaises(PolicyError):
            Policy(network="yolo")

    def test_unknown_key_rejected(self):
        with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as fh:
            fh.write("allow_everything = true\n")
        with self.assertRaises(PolicyError):
            load_policy(fh.name)

    def test_content_hash_stable(self):
        self.assertEqual(Policy().content_hash(), Policy().content_hash())
        self.assertNotEqual(
            Policy().content_hash(), Policy(network="allow").content_hash()
        )


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.log_path = Path(tempfile.mkdtemp()) / "audit.jsonl"

    def test_chain_appends_and_verifies(self):
        log = AuditLog(self.log_path)
        log.append("run.start", cmd=["echo", "hi"])
        log.append("run.end", exit_code=0)
        self.assertEqual(audit.verify(self.log_path), 2)

    def test_reopen_continues_chain(self):
        AuditLog(self.log_path).append("a")
        AuditLog(self.log_path).append("b")
        self.assertEqual(audit.verify(self.log_path), 2)

    def test_tamper_detected(self):
        log = AuditLog(self.log_path)
        log.append("run.start", cmd=["rm", "-rf", "/"])
        log.append("run.end", exit_code=0)
        lines = self.log_path.read_text().splitlines()
        first = json.loads(lines[0])
        first["data"]["cmd"] = ["echo", "innocent"]
        lines[0] = json.dumps(first, sort_keys=True, separators=(",", ":"))
        self.log_path.write_text("\n".join(lines) + "\n")
        with self.assertRaises(audit.AuditError):
            audit.verify(self.log_path)

    def test_deletion_detected(self):
        log = AuditLog(self.log_path)
        log.append("a")
        log.append("b")
        log.append("c")
        lines = self.log_path.read_text().splitlines()
        self.log_path.write_text("\n".join([lines[0], lines[2]]) + "\n")
        with self.assertRaises(audit.AuditError):
            audit.verify(self.log_path)


class SeatbeltTests(unittest.TestCase):
    def test_profile_shape(self):
        prof = render_profile(Policy(), "/tmp/work")
        self.assertIn("(deny default)", prof)
        self.assertIn("(allow file-read*)", prof)
        workdir = str(Path("/tmp/work").resolve())
        self.assertIn(f'(subpath "{workdir}")', prof.split("file-write*")[1])
        self.assertIn("(deny network*)", prof)
        self.assertIn(str(Path("~/.ssh").expanduser()), prof)
        self.assertNotIn('"~', prof)

    def test_network_allow(self):
        prof = render_profile(Policy(network="allow"), "/tmp/work")
        self.assertIn("(allow network*)", prof)
        self.assertNotIn("(deny network*)", prof)


@unittest.skipUnless(sys.platform == "darwin", "Seatbelt is macOS-only")
class SeatbeltIntegrationTests(unittest.TestCase):
    """End-to-end: writes inside the workdir succeed, outside fail."""

    @classmethod
    def setUpClass(cls):
        cls.workdir = Path(tempfile.mkdtemp())
        prof = render_profile(Policy(), cls.workdir)
        cls.profile = cls.workdir / "profile.sb"
        cls.profile.write_text(prof)
        probe = subprocess.run(
            ["/usr/bin/sandbox-exec", "-f", str(cls.profile), "/bin/echo", "ok"],
            capture_output=True,
        )
        if probe.returncode != 0:
            raise unittest.SkipTest(
                f"sandbox-exec unavailable here: {probe.stderr.decode().strip()}"
            )

    def _run(self, *cmd):
        return subprocess.run(
            ["/usr/bin/sandbox-exec", "-f", str(self.profile), *cmd],
            capture_output=True,
            cwd=self.workdir,
        )

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


if __name__ == "__main__":
    unittest.main()
