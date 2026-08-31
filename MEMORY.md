# Decision Journal

Append-only. Newest entries at the top. Format: date — decision — rationale.

## 2026-08-31 (later)

- **Direction decided: A+D.** Policy-as-code + tamper-evident audit control plane, shipped first as a local-first CLI (`agentbox`). Rationale: only open spot on the landscape map (see SCOPE.md gap table); rides existing runtimes instead of competing with them.
- **Tech choices:** Python ≥3.11 stdlib-only; TOML policy files; macOS Seatbelt (`sandbox-exec`) as backend v0 (same primitive Claude Code/Codex use), bubblewrap for Linux next; hash-chained JSONL audit log.
- **Prototype shipped and verified end-to-end** on macOS: workdir writes allowed, $HOME writes blocked, ~/.ssh reads denied, network denied, audit chain verifies and detects tampering/deletion. 13 tests green.
- **Known ceiling:** Seatbelt network control is on/off only — per-domain egress needs a filtering proxy (open question in SCOPE.md).

## 2026-08-31

- **Project direction: build our own open-source secure agent sandbox (VM + SDK)**, informed by landscape research first. Rationale: the space (E2B, Daytona, Modal, etc.) is crowded on the hosted side but gaps may exist for self-hostable / policy-driven tooling — SCOPE.md will decide.
- **Repo bootstrapped** with CLAUDE.md as the doc index, RESEARCH.md (deep multi-agent research), SCOPE.md (gap analysis), SPRINT.md (sprint tracking), MEMORY.md (this file).
- **Research method:** 4 parallel research tracks — sandbox startups/SDKs, isolation primitives (Firecracker/gVisor/Kata/Hyperlight), big-cloud + AI-lab offerings, OSS + gap analysis. All claims cited.
- **License: MIT.** Rationale: maximize adoption for an early-stage OSS infra project.
- **Published to GitHub** as a public repo under the user's account.
