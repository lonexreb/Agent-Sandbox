"""Policy-as-code: one TOML file declares what an agent may touch."""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# Read-denied by default even though reads are otherwise broad: the paths an
# exfiltrating agent goes for first.
DEFAULT_DENY_READ = (
    "~/.ssh",
    "~/.aws",
    "~/.gnupg",
    "~/.netrc",
    "~/.config/gcloud",
    "~/.kube",
)

_NETWORK_MODES = ("deny", "allow")


class PolicyError(ValueError):
    """Raised when a policy file is invalid."""


@dataclass(frozen=True)
class Policy:
    name: str = "default"
    network: str = "deny"
    allow_write: tuple[str, ...] = ()
    deny_read: tuple[str, ...] = DEFAULT_DENY_READ

    def __post_init__(self) -> None:
        if self.network not in _NETWORK_MODES:
            raise PolicyError(
                f"network must be one of {_NETWORK_MODES}, got {self.network!r}"
            )

    def content_hash(self) -> str:
        canon = repr(
            (self.name, self.network, sorted(self.allow_write), sorted(self.deny_read))
        )
        return hashlib.sha256(canon.encode()).hexdigest()


def _expand(paths: list[str]) -> tuple[str, ...]:
    return tuple(str(Path(p).expanduser()) for p in paths)


def load_policy(path: str | Path) -> Policy:
    raw = Path(path).read_bytes()
    try:
        data = tomllib.loads(raw.decode())
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise PolicyError(f"{path}: not valid TOML: {exc}") from exc

    unknown = set(data) - {"name", "network", "allow_write", "deny_read"}
    if unknown:
        raise PolicyError(f"{path}: unknown policy keys: {sorted(unknown)}")

    return Policy(
        name=data.get("name", "default"),
        network=data.get("network", "deny"),
        allow_write=_expand(data.get("allow_write", [])),
        deny_read=_expand(data.get("deny_read", list(DEFAULT_DENY_READ))),
    )
