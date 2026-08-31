"""agentbox CLI: run a command under policy, verify the audit trail."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from agentbox import audit
from agentbox.audit import AuditLog
from agentbox.policy import Policy, PolicyError, load_policy
from agentbox.seatbelt import render_profile

DEFAULT_LOG = "agentbox-audit.jsonl"


def _policy_from_args(args: argparse.Namespace) -> Policy:
    return load_policy(args.policy) if args.policy else Policy()


def cmd_run(args: argparse.Namespace) -> int:
    if sys.platform != "darwin":
        print("agentbox: only the macOS Seatbelt backend exists so far", file=sys.stderr)
        return 2
    policy = _policy_from_args(args)
    workdir = Path(args.workdir).resolve()
    profile = render_profile(policy, workdir)
    log = AuditLog(args.log)
    log.append(
        "run.start",
        cmd=args.cmd,
        workdir=str(workdir),
        policy=policy.name,
        policy_hash=policy.content_hash(),
        network=policy.network,
    )
    started = time.monotonic()
    with tempfile.NamedTemporaryFile("w", suffix=".sb", delete=False) as fh:
        fh.write(profile)
        profile_path = fh.name
    try:
        proc = subprocess.run(
            ["/usr/bin/sandbox-exec", "-f", profile_path, *args.cmd], cwd=workdir
        )
        code = proc.returncode
    except OSError as exc:
        log.append("run.error", error=str(exc))
        print(f"agentbox: failed to launch sandbox: {exc}", file=sys.stderr)
        return 1
    finally:
        Path(profile_path).unlink(missing_ok=True)
    log.append("run.end", exit_code=code, duration_s=round(time.monotonic() - started, 3))
    return code


def cmd_verify(args: argparse.Namespace) -> int:
    try:
        count = audit.verify(args.log)
    except audit.AuditError as exc:
        print(f"TAMPERED: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"agentbox: no audit log at {args.log}", file=sys.stderr)
        return 1
    print(f"ok: {count} records, chain intact")
    return 0


def cmd_print_profile(args: argparse.Namespace) -> int:
    policy = _policy_from_args(args)
    sys.stdout.write(render_profile(policy, Path(args.workdir).resolve()))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentbox")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run a command under the policy sandbox")
    run.add_argument("--policy", help="path to policy TOML (default: built-in policy)")
    run.add_argument("--workdir", default=".", help="writable working directory")
    run.add_argument("--log", default=DEFAULT_LOG, help="audit log path")
    run.add_argument("cmd", nargs="+", help="command to run (prefix with --)")
    run.set_defaults(func=cmd_run)

    verify = sub.add_parser("verify", help="verify the audit log hash chain")
    verify.add_argument("--log", default=DEFAULT_LOG, help="audit log path")
    verify.set_defaults(func=cmd_verify)

    prof = sub.add_parser("print-profile", help="print the generated SBPL profile")
    prof.add_argument("--policy", help="path to policy TOML")
    prof.add_argument("--workdir", default=".", help="writable working directory")
    prof.set_defaults(func=cmd_print_profile)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PolicyError as exc:
        print(f"agentbox: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
