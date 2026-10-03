"""Render a bubblewrap argv prefix from a Policy (Linux backend).

Same model as the Seatbelt backend: reads broad (ro-bind of /), writes
confined to the workdir plus allowlisted paths, secrets hidden by mounting
an empty tmpfs over each denylisted path, network as an on/off toggle.
"""

from __future__ import annotations

from pathlib import Path

from agentbox.policy import Policy

BWRAP = "bwrap"


def render_args(policy: Policy, workdir: str | Path) -> list[str]:
    workdir = Path(workdir).resolve()
    args = [
        BWRAP,
        "--die-with-parent",
        "--unshare-user",  # needed for loopback setup inside --unshare-net
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
    ]
    if policy.network == "deny":
        args.append("--unshare-net")
    # reads broad; later mounts override earlier ones
    args += ["--ro-bind", "/", "/"]
    args += ["--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp"]
    args += ["--bind", str(workdir), str(workdir)]
    for p in policy.allow_write:
        args += ["--bind", p, p]
    for p in policy.deny_read:
        expanded = Path(p).expanduser()
        # tmpfs needs an existing mount point; a missing path is already unreadable
        if expanded.exists():
            args += ["--tmpfs", str(expanded)]
    args.append("--")
    return args
