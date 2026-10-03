"""agentbox CLI: run a command under policy, verify the audit trail."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentbox import audit
from agentbox.policy import Policy, PolicyError, load_policy
from agentbox.sandbox import DEFAULT_LOG, BackendError, Sandbox
from agentbox.seatbelt import render_profile


def _policy_from_args(args: argparse.Namespace) -> Policy:
    return load_policy(args.policy) if args.policy else Policy()


def cmd_run(args: argparse.Namespace) -> int:
    try:
        box = Sandbox(_policy_from_args(args), workdir=args.workdir, log_path=args.log)
        return box.run(args.cmd).returncode
    except BackendError as exc:
        print(f"agentbox: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"agentbox: failed to launch sandbox: {exc}", file=sys.stderr)
        return 1


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
