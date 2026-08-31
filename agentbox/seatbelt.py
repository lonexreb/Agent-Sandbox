"""Render a macOS Seatbelt (SBPL) profile from a Policy.

Model (matches Anthropic srt / Codex CLI philosophy): reads broad minus a
secrets denylist, writes confined to the workdir plus allowlisted paths,
network as an on/off toggle.
"""

from __future__ import annotations

from pathlib import Path

from agentbox.policy import Policy

# ponytail: network is on/off only; per-domain egress needs a filtering proxy
# (tracked in SCOPE.md open questions).

_BASE_WRITE = ("/private/tmp", "/private/var/folders", "/dev")


def _quote(path: str) -> str:
    return '"' + path.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _subpaths(paths: tuple[str, ...]) -> str:
    return " ".join(
        f"(subpath {_quote(str(Path(p).expanduser()))})" for p in paths
    )


def render_profile(policy: Policy, workdir: str | Path) -> str:
    write_paths = (str(Path(workdir).resolve()),) + _BASE_WRITE + policy.allow_write
    lines = [
        "(version 1)",
        "(deny default)",
        "; process bootstrap",
        "(allow process-fork)",
        "(allow process-exec*)",
        "(allow signal (target children))",
        "(allow signal (target self))",
        "(allow sysctl-read)",
        "(allow mach-lookup)",
        "(allow file-ioctl)",
        "; reads: broad, minus the secrets denylist below",
        "(allow file-read*)",
        "; writes: workdir + explicit allowlist only",
        f"(allow file-write* {_subpaths(write_paths)})",
    ]
    if policy.deny_read:
        lines.append("; secrets denylist (later rules win in SBPL)")
        lines.append(f"(deny file-read* {_subpaths(policy.deny_read)})")
    lines.append(f"({'allow' if policy.network == 'allow' else 'deny'} network*)")
    return "\n".join(lines) + "\n"
