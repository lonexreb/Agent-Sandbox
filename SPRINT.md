# Sprint Plan

## Sprint 0 — Research & Bootstrap (2026-08-31) — ✅ done

- [x] Deep landscape research (4 tracks) → RESEARCH.md
- [x] Repo scaffold: CLAUDE.md, MEMORY.md, SCOPE.md, SPRINT.md, README.md + SVG banner
- [x] git init, MIT license, publish to GitHub
- [x] Review SCOPE.md candidate directions and pick one → **A+D** (policy + audit control plane, local-first)

## Sprint 1 — Prototype (2026-08-31) — in progress

- [x] Define MVP: policy TOML → Seatbelt profile → sandboxed run → hash-chained audit log
- [x] `agentbox` Python package (stdlib-only, ≥3.11): policy, audit, seatbelt, CLI
- [x] Tests incl. real Seatbelt integration (workdir write allowed, $HOME write blocked, ~/.ssh read denied, network denied)
- [x] Linux backend (bubblewrap) with the same policy file (2026-10-02; arg-generation tested, needs validation on a real Linux box)
- [x] Per-domain egress: filtering proxy **design** → [docs/egress-proxy.md](docs/egress-proxy.md) (2026-10-02)
- [x] Python SDK surface: `agentbox.Sandbox` class; CLI now runs through it (2026-10-02)
- [x] Validate bwrap backend on Linux — CI green on ubuntu-latest: write confinement, escape blocked, network blocked (2026-10-02)
- [ ] Implement the egress proxy (`network = "proxy"` + `allow_net`)
- [ ] Richer audit events (per-exec, file-event capture options)

## Backlog (unsorted)

- E2B protocol compatibility layer
- Audit session-replay viewer
- Secret brokering (host-side proxy injects credentials; raw keys never enter sandbox)
- Multi-agent fleet management story
- CI (GitHub Actions: unit tests on Linux + macOS), contribution guide
- Project rename decision
