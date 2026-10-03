# Agent Sandbox

Open-source project: a secure micro-VM runtime + SDK so enterprises can run many AI agents and models without trusting them — isolation, policy guardrails, and audit so a rogue agent can't do damage.

**Current phase:** Sprint 1 — prototype. Direction: policy + audit control plane (`agentbox` CLI), decided in SCOPE.md.

## Code

- `agentbox/` — Python ≥3.11, stdlib-only package: `policy.py` (TOML → frozen Policy), `seatbelt.py` (Policy → SBPL profile, macOS), `bwrap.py` (Policy → bubblewrap argv, Linux), `sandbox.py` (`Sandbox` SDK class, picks backend per platform), `audit.py` (hash-chained JSONL log), `cli.py` (thin wrapper: `run` / `verify` / `print-profile`)
- `tests/` — run with `python3.12 -m unittest discover -s tests` (includes real Seatbelt integration tests, macOS-only)
- `docs/egress-proxy.md` — accepted design for per-domain network egress (`network = "proxy"`)
- Keep it stdlib-only; new dependencies need a MEMORY.md entry justifying them.

## Project documents

Read these before doing any work; keep them updated as you go.

| File | Purpose | When to touch |
|------|---------|---------------|
| [README.md](README.md) | Public GitHub face: pitch, landscape summary, status | Update when scope or status changes |
| [RESEARCH.md](RESEARCH.md) | Cited landscape research: startups, isolation tech, cloud/AI-lab offerings, OSS | Append new findings with source links; never delete citations |
| [SCOPE.md](SCOPE.md) | Gap analysis, product direction, in/out of scope, open questions | Update when a direction decision is made |
| [SPRINT.md](SPRINT.md) | Sprint plan: current sprint goals and backlog | Update at start/end of each work session |
| [MEMORY.md](MEMORY.md) | Decision journal: dated log of decisions and why | Append a dated entry for every non-trivial decision |

## Working rules

- Every factual claim about a competitor or technology in RESEARCH.md needs an inline source link.
- Decisions go in MEMORY.md with a date and one-line rationale — never rewrite history, only append.
- SCOPE.md is the single source of truth for what we are and aren't building; when in doubt, check it before writing code.
- Keep docs scannable: tables for comparisons, bullets for profiles.
- Commit messages: conventional format (`feat:`, `docs:`, `fix:`, `chore:`).
