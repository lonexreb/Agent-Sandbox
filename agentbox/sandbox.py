"""Sandbox: the SDK entry point. Picks a backend per platform, runs commands
under policy, and records every run in the audit log."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from agentbox import bwrap, seatbelt
from agentbox.audit import AuditLog
from agentbox.policy import Policy

DEFAULT_LOG = "agentbox-audit.jsonl"


class BackendError(RuntimeError):
    """Raised when no isolation backend is available on this host."""


class Sandbox:
    """Run commands under a Policy.

    >>> box = Sandbox(Policy(), workdir=".")
    >>> box.run(["echo", "hi"]).returncode
    0
    """

    def __init__(
        self,
        policy: Policy | None = None,
        workdir: str | Path = ".",
        log_path: str | Path = DEFAULT_LOG,
    ):
        self.policy = policy or Policy()
        self.workdir = Path(workdir).resolve()
        self.log = AuditLog(log_path)
        self.backend = self._pick_backend()

    @staticmethod
    def _pick_backend() -> str:
        if sys.platform == "darwin":
            return "seatbelt"
        if sys.platform.startswith("linux"):
            if shutil.which(bwrap.BWRAP) is None:
                raise BackendError(
                    "bubblewrap (bwrap) not found; install it, e.g. "
                    "`apt install bubblewrap`"
                )
            return "bwrap"
        raise BackendError(f"no isolation backend for platform {sys.platform!r}")

    def run(self, cmd: list[str], **popen_kw: object) -> subprocess.CompletedProcess:
        self.log.append(
            "run.start",
            cmd=list(cmd),
            backend=self.backend,
            workdir=str(self.workdir),
            policy=self.policy.name,
            policy_hash=self.policy.content_hash(),
            network=self.policy.network,
        )
        started = time.monotonic()
        profile_path: Path | None = None
        try:
            if self.backend == "seatbelt":
                profile = seatbelt.render_profile(self.policy, self.workdir)
                with tempfile.NamedTemporaryFile("w", suffix=".sb", delete=False) as fh:
                    fh.write(profile)
                    profile_path = Path(fh.name)
                argv = ["/usr/bin/sandbox-exec", "-f", str(profile_path), *cmd]
            else:
                argv = bwrap.render_args(self.policy, self.workdir) + list(cmd)
            proc = subprocess.run(argv, cwd=self.workdir, **popen_kw)  # type: ignore[call-overload]
        except OSError as exc:
            self.log.append("run.error", error=str(exc))
            raise
        finally:
            if profile_path is not None:
                profile_path.unlink(missing_ok=True)
        self.log.append(
            "run.end",
            exit_code=proc.returncode,
            duration_s=round(time.monotonic() - started, 3),
        )
        return proc
