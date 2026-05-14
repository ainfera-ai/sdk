# Changelog

All notable changes to the `ainfera` Python SDK are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-05-17

First public release on PyPI. Targets the D9 launch deliverable: customers
can `pip install ainfera` and exercise the five core flows in ≤5 lines each.

### Added

- **Clients**: `AinferaClient` (sync) and `AsyncAinferaClient` (async).
  Both support context-manager use and share the same `agents` / `receipts`
  resource surface. `api_key` falls back to the `AINFERA_API_KEY`
  environment variable when not passed explicitly. Default HTTP timeout
  is 60s; `agent.inference(timeout=...)` overrides it per-call for
  long-context requests.
- **Agent registration + retrieval**: `client.agents.register(...)`,
  `.list(...)`, `.retrieve(...)`. `agent.refresh()` re-fetches an Agent's
  data and drops its cached Wallet / AuditChain handles.
- **AgentCard**: `Agent.get_card()` returns a JWS-signed identity card.
  `AgentCard.verify(public_key=...)` verifies signatures locally with no
  network call; with auto-fetch when bound to a client.
- **Inference**: `agent.inference(model=..., messages=...)` routes through
  Ainfera and returns an `InferenceResponse` with the model output plus
  a `Receipt` linking the call into the AuditChain.
- **Wallet**: `agent.wallet.topup(amount_usd=...)` for the prepaid funding
  path. x402 USDC topup is deferred to D14+.
- **Ledger**: `Ledger.entries(limit=...)` for the per-Wallet append-only
  balance-change log.
- **AuditChain**: `agent.audit_chain.events(limit=...)` to read events,
  `agent.audit_chain.verify()` to walk the hash chain locally — the
  customer-trust primitive that lets Annex IV auditors confirm tamper-
  evidence without trusting Ainfera.
- **Local verification primitives**: `verify_event_hash` and
  `verify_chain` exposed at the top level for offline use.
- **Exception hierarchy**: `AinferaError`, `APIError`, `AgentCardInvalid`,
  `ModelUnavailable`, `WalletInsufficient`, `SpendPolicyExceeded`,
  `AuditChainBroken`. HTTP 402 / 403 / 422 codes map to semantic
  subclasses; others to `APIError`.
- **Type info**: `py.typed` marker ships in the wheel so downstream mypy
  picks up our signatures.

### Deferred to D14+

- Streaming inference
- Sigstore verification of AgentCards
- TrustScore API
- x402 USDC wallet topup
- Sphinx reference docs

### Deferred to D30

- TypeScript SDK (AIN-44)

[Unreleased]: https://github.com/ainfera-ai/sdk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ainfera-ai/sdk/releases/tag/v0.1.0
