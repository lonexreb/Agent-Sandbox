# Design: Per-Domain Egress Proxy

> Status: design accepted 2026-10-02, not yet implemented. Context in [SCOPE.md](../SCOPE.md).

## Problem

Both backends can only toggle network on/off (Seatbelt `(deny network*)`, bwrap `--unshare-net`). Real policies need: *"this agent may reach `api.github.com` and `pypi.org`, nothing else."*

## Approach (same shape as Anthropic srt and Docker Sandboxes)

1. **Cut direct network entirely** inside the sandbox (today's deny mode).
2. **Run a host-side filtering proxy** owned by agentbox, outside the sandbox:
   an HTTP CONNECT proxy bound to localhost that consults the policy's
   `allow_net = ["api.github.com", "pypi.org"]` list per request.
3. **Bridge the sandbox to the proxy only.**
   - Linux/bwrap: keep `--unshare-net`, pass a Unix socket into the sandbox
     (`--bind /run/agentbox/proxy.sock ...`); in-sandbox `HTTP_PROXY` points at
     a tiny socket-to-proxy relay.
   - macOS/Seatbelt: allow network to localhost:port only
     (`(allow network-outbound (remote tcp "localhost:PORT"))`), set
     `HTTP_PROXY`/`HTTPS_PROXY` in the child environment.
4. **Audit every flow**: the proxy appends `net.request` events
   (domain, port, decision, bytes) to the same hash-chained log.

## Policy addition

```toml
network = "proxy"            # third mode, alongside "deny" / "allow"
allow_net = ["api.github.com", "pypi.org"]
```

## Known limits (accepted for v1)

- Only proxies cooperating protocols (HTTP/S via env vars). Raw sockets stay
  blocked — that's a feature, not a gap.
- An allowlisted domain is a **capability grant, not just a destination**
  (Anthropic's Files-API exfiltration lesson): v2 should support per-domain
  request inspection (e.g. deny bodies containing marked secrets).
- Proxy is one Python stdlib process (`http.server` + `socket`); no TLS MITM.
