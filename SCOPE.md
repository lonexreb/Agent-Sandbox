# Scope & Product Direction

> Derived from [RESEARCH.md](RESEARCH.md) (2026-08-31). Status: **direction proposed, not yet decided** — see Open Questions.

## Working thesis

Don't build another isolation runtime — that layer is crowded, capital-intensive, and contested by Alibaba, Google/K8s, Anthropic, and every Firecracker startup. The durable indie opening is the **governance layer**: policy-as-code guardrails + tamper-evident audit that work across existing runtimes, shipped with a local-first UX as the on-ramp and E2B-protocol compatibility as the enterprise bridge.

## In scope (proposed)

- Declarative, versionable, runtime-agnostic policy files (egress allowlists, filesystem scopes, secret-brokering rules)
- Append-only, hash-chained audit log of every exec / file / network event, attributable to an agent identity
- SDK (Python and/or TypeScript) + CLI wrapping existing isolation backends (srt, microsandbox, Docker/gVisor, E2B-compatible remotes)
- Local-first developer experience on macOS + Linux

## Out of scope (proposed)

- Building a new VMM / hypervisor / kernel-level isolation primitive
- Hosted cloud service (self-hostable OSS first)
- Kubernetes operator (later, if ever)
- Computer-use / GUI desktops

## Open questions

- [ ] Pick primary direction: A (policy + audit control plane) vs D (local-first policy-bound sandbox UX) vs A+D combined
- [ ] First SDK language: Python or TypeScript?
- [ ] Policy file format: TOML vs YAML vs Cedar-inspired DSL?
- [ ] E2B protocol compatibility in v1 or later?
- [ ] Project name (Agent-Sandbox is a working title; the k8s SIG already uses "agent-sandbox")

---

# Gap Analysis (full research output)

## What the landscape actually covers

| Capability | State of the art | Verdict |
|---|---|---|
| Fast local microVMs | microsandbox (excellent) | **Solved** |
| Cloud-scale sandbox platform | E2B, OpenSandbox (K8s) | Solved, but heavy |
| K8s fleet orchestration | kubernetes-sigs/agent-sandbox, OpenSandbox | Solved *if you have K8s* |
| OS-level policy (FS/egress) | srt (per-process, beta) | Partial — no platform around it |
| Egress policy + secret brokering | OpenSandbox (K8s-only); iron-proxy/Infisical (proxies only); microsandbox (secrets only) | **Fragmented** |
| Audit trails / forensics / replay | Essentially nobody | **Open** |
| Snapshot/backtracking for multi-step agents | Arrakis (dead, AGPL) | **Open** |
| Mid-scale self-hosting (1–10 nodes, no K8s) | Dormice (1 node, pre-production) | **Open** |
| Local-first macOS + Linux parity | Fragmented (srt, Dory-GPL, containerization, agent-sandbox.nix) | **Open** |
| Model-/framework-agnostic SDK + E2B compat | E2B protocol emerging as standard | Compat = distribution wedge |

## The five real gaps

1. **The policy plane is divorced from the isolation plane.** The projects with strong isolation (microsandbox, E2B, Firecracker DIY) have weak policy vocabularies; the project with rich policy (OpenSandbox: egress controls, credential vault) requires Kubernetes; the project with the right policy primitives (srt) has the weakest isolation boundary. No one offers *declarative, versionable, runtime-agnostic* guardrails — "this agent may reach `api.github.com` and `pypi.org`, read `/workspace`, never see raw secrets" — enforced identically on a laptop and a server fleet.
2. **Nobody records what agents actually did.** Enterprises deploying fleets need tamper-evident audit: every command, file mutation, and network flow attributable to an agent identity, exportable as compliance evidence. Not one project in the landscape treats this as a first-class feature.
3. **The middle of the deployment curve is empty.** Below: single-host tools (microsandbox, Dormice). Above: Terraform+Nomad (E2B) or Kubernetes (OpenSandbox, agent-sandbox). An enterprise team wanting 3–10 boxes running 200 concurrent agents without a platform team has no OSS option — and Daytona's exit proved demand for self-hostable options is real and trust in VC-backed "open source" is shaken.
4. **Snapshot/backtracking died with Arrakis.** Branchable VM state for multi-step agent workflows (retry from step 4, fork exploration branches, RL rollouts) is validated by Arrakis's reception and by RL-training demand (the k8s agent-sandbox README names RL explicitly), but no maintained, permissively-licensed implementation exists.
5. **macOS local-first is fragmented.** Developers run agents on MacBooks; the serious pieces (apple/containerization, srt's Seatbelt mode, libkrun) exist but the polished, policy-bound, cross-platform product doesn't — Dory is GPL and Apple-only, yoloAI and agent-sandbox.nix are small.

## Candidate directions

**Direction A — Runtime-agnostic policy & audit control plane ("OPA + flight recorder for agent sandboxes").** *Recommended.* A daemon + SDK that wraps existing runtimes (srt profiles locally, microsandbox/Docker/gVisor for isolation, E2B-compatible backends remotely) and adds what none of them have: policy-as-code guardrail files (egress allowlists, filesystem scopes, secret-brokering rules — enforced via network proxy + mount policy) and an append-only, hash-chained audit log of every exec/file/network event, with a session-replay viewer. **Differentiation:** you're not competing on isolation (a losing game vs. Firecracker/Alibaba/Google); you're the layer everyone is missing, and you ride every runtime's adoption instead of fighting it. **Feasibility: high** — the hard kernel work is delegated; the deliverables are a proxy, a policy engine, an event log, and SDKs. This is exactly solo-buildable, and it's the piece enterprises must currently assemble from iron-proxy + Vault + hope.

**Direction B — Modern Arrakis: a snapshot-native agent sandbox (Apache-2.0).** MicroVM sandboxes where `fork()`/`checkpoint()`/`restore()` are first-class SDK verbs, built on Firecracker's mature snapshot API or CRIU. Targets multi-step agent reliability (backtrack on failure), parallel exploration, and the fast-growing RL-environment market. **Differentiation:** the only validated player is dead and AGPL; k8s agent-sandbox wants this at orchestration level but owns no runtime. **Feasibility: medium** — Firecracker snapshotting is well-documented, but making branching cheap (copy-on-write disk/memory) and correct is real systems work; scope tightly to Linux/KVM first.

**Direction C — E2B-compatible "small fleet" server.** A single static binary that clusters: run it on 1–10 machines, get one E2B-protocol endpoint with scheduling, warm pools, per-tenant quotas, and built-in egress policy — no K8s, no Nomad, no Terraform. **Differentiation:** Dormice proved the single-binary + E2B-compat wedge but stops at one machine and is pre-production; E2B's own self-hosting starts at ~$1,250/mo of cloud floor. Daytona refugees are the ready-made audience. **Feasibility: medium** — distributed scheduling is where solo projects go to die; mitigate by shipping single-node first and using boring primitives (SQLite/raft via litefs or embedded etcd) for the cluster step.

**Direction D — Local-first, policy-bound agent sandbox for macOS + Linux dev machines.** A polished `agentbox run claude-code` that gives Claude Code/Codex/opencode a per-project VM (apple/containerization on macOS, libkrun/bubblewrap on Linux) governed by a shared TOML policy file, with secret brokering and a local audit log. **Differentiation:** the demand is visible in a dozen fragmented sub-1k-star projects (yoloAI, agent-sandbox.nix, mattolson/agent-sandbox, Dory); none is cross-platform, permissively licensed, and product-quality at once. **Feasibility: high**, but the moat is thin — microsandbox or Anthropic could absorb this; win on UX and the policy/audit features from Direction A.

**Direction E — Agent sandbox conformance/eval suite.** A test harness that scores any sandbox against the [agent-sandbox-taxonomy](https://github.com/kajogo777/the-agent-sandbox-taxonomy)'s 7 defense layers (escape attempts, egress leaks, secret exfiltration, DoS), publishing reproducible scorecards. **Differentiation:** post-Daytona, "prove your sandbox" is a live enterprise question and nobody owns the benchmark. **Feasibility: high**; monetization/growth is via authority rather than adoption — best as a companion to A or D, not a standalone bet.

**Bottom line:** the governance layer (Direction A, with Direction D's local-first UX as the on-ramp and E2B-protocol compatibility as the enterprise bridge) is the only spot on the map where every current player is weak, where enterprise budgets already exist (compliance), and where a small team's output compounds with — rather than competes against — the ecosystem's momentum.
