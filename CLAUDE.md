# Agent Sandbox

Open-source project: a secure micro-VM runtime + SDK so enterprises can run many AI agents and models without trusting them — isolation, policy guardrails, and audit so a rogue agent can't do damage.

**Current phase:** Research → scoping. No product code yet.

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
