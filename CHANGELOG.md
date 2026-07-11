# Changelog

All notable changes to the `ainfera` Python SDK are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **README rewritten**: removed stale "57 models" literal count claims; examples now use `model="ainfera-inference"` (the flagship route) instead of pinned `claude-haiku-4-5`; concept page links updated to point to live `/docs` sections.
- **`examples/quickstart.py`**: inference model changed from `claude-haiku-4-5` to `ainfera-inference`.
- **`python/examples/04_inference.py`**: model changed to `ainfera-inference`; fixed broken `.receipt.audit_url` reference (replaced with `.receipt_id`).
- **`examples/README.md`**: updated model reference and version pin (`>=1.1.0` instead of `==1.0.1`).

### Added

- **Compatibility table** in README: explicit feature matrix across `ainfera` SDK, `openai` SDK, and `anthropic` SDK.
- **Streaming example** (`examples/streaming.py`): SSE via the OpenAI-compatible endpoint.
- **Tools example** (`examples/tools.py`): function calling with `tools=` and `tool_choice=`.
- **Retries example** (`examples/retries.py`): exponential backoff for transient 5xx errors with semantic exception handling.
- **Async example** (`examples/async_usage.py`): `AsyncAinferaClient` with wallet and audit chain verification.
- **Receipt verification example** (`examples/receipt_verification.py`): inline receipt + local AuditChain verification.
- **Error handling example** (`examples/error_handling.py`): full semantic exception hierarchy mapping.
- **API versioning** section in README documenting the SDK↔API compatibility contract.
- **Local verification** clarification in README: tamper-evidence vs tamper-prevention; proves log integrity relative to the published key.
- **Semantic-release config** (`releaserc.toml`): automated version bumping from Conventional Commits.
- **Routing hints** example in README: `routing_hint`, `pool`, budget/latency/quality caps.

### Fixed

- **04_inference.py**: broken `.receipt.audit_url` reference — `Receipt` model has no `audit_url` field accessible via `.receipt` on `InferenceResponse`; replaced with `.receipt_id` which is the actual response field.
- **examples/README.md**: stale `ainfera==1.0.1` pin updated to `>=1.1.0`.

## [1.1.0] — 2026-05-19

API alignment release. Closes [AIN-79](https://linear.app/ainfera/issue/AIN-79).

The 1.0.x SDK shipped against pre-D4 mocks and several resource shapes
drifted from the production `/v1/*` API. Mock-based tests stayed green
but end-to-end calls against `https://api.ainfera.ai` failed (the D5
`examples/quickstart.py` had to fall back to raw `httpx` to round-trip).
1.1.0 realigns every resource to the canonical contract verified
against `ainfera_api/routers/` on 2026-05-19.

### Breaking

- **`Agent` model**: now binds against both retrieve and signup
  response shapes. `agent_id` aliases the API's `id` field via
  `validation_alias=AliasChoices("id", "agent_id")`. New optional
  fields surfaced: `tenant_id`, `status`, `public_key_ed25519`. The
  `description` field is retained for backward compat but is not
  populated from the API.
- **`InferenceResponse` model**: flattened to match the API. The
  nested `{text, inference, receipt, raw}` shape is replaced by
  `{inference_id, receipt_id, content, content_blocks, model_used,
  provider, finish_reason, finish_reason_native, input_tokens,
  output_tokens, cost_usd}`. The `.text` property is preserved as a
  back-compat alias for `.content` (deprecated, will be removed in 2.0).
- **`Wallet` model**: removed `wallet_id` field — the API never returned
  it. The Wallet is keyed by `agent_id` (each Agent has exactly one).
- **`AgentsResource.register(...)`**: now requires `tenant_id=` and `name=`
  (was `name=`, `description=`). Hits `POST /v1/agents/register` (was
  `POST /v1/agents`).
- **`AgentsResource.list()`**: removed — the API does not expose
  `GET /v1/agents`. Use the dashboard for multi-agent enumeration.
- **`Ledger`**: now reads `GET /v1/ledger/{agent_id}` which returns a
  `{agent_id, balance_usd, entries}` envelope. SDK extracts `entries`
  and surfaces the most recent balance via the new `Ledger.balance`
  property.
- **`AuditChain.events()`**: pagination switched from cursor-based to
  `since_seq`-based, matching the API contract. Walks until an empty
  page is returned (or `limit` is hit).
- **`Inference` model class**: removed from the public namespace. The
  flat `InferenceResponse` carries all the call metadata directly.

### Added

- **`AuditChain.verify_remote()`**: server-side verification via
  `GET /v1/audit/{agent_id}/verify`. Returns an `AuditVerifyResult`
  with `valid`, `event_count`, and failure details. The local
  `.verify()` remains the canonical trust-no-one check; `verify_remote`
  confirms the canonical control plane agrees at call time.
- **`AuditChain.annex_iv_bundle()`**: fetches the EU AI Act Annex IV
  audit export bundle via `GET /v1/audit/{agent_id}/annex-iv`.
  Returned as a raw dict to avoid churn on Annex IV schema revisions.
- **`AuditEvent.event_id`**: back-compat property that returns `.id`
  (the API field name changed from `event_id` → `id`).
- **`InferenceResponse.content_blocks`** (AIN-177), **`.provider`**
  (AIN-126), **`.finish_reason_native`** (AIN-176): structured response
  data now surfaced through the SDK.

### Fixed

- **`/v1/agents/{id}/pubkey`** endpoint never existed in production —
  the SDK was calling a 404 path. `AinferaClient._fetch_agent_pubkey`
  now reads `public_key_ed25519` from the Agent retrieve response.
- **Wallet topup body** now carries `agent_id` per the API contract
  (was implicit in the path). Amount is sent as a string so Decimal
  precision survives the JSON encoding round-trip.

### Path migration matrix

| 1.0.x SDK | 1.1.0 SDK / Prod API |
| --- | --- |
| `POST /v1/agents` (register) | `POST /v1/agents/register` |
| `POST /v1/agents/{id}/inference` | `POST /v1/inference` (agent_id in body) |
| `GET  /v1/agents/{id}/wallet` | `GET  /v1/wallets/{agent_id}` |
| `POST /v1/agents/{id}/wallet/topup` | `POST /v1/wallets/topup` (agent_id in body) |
| `GET  /v1/agents/{id}/wallet/ledger` | `GET  /v1/ledger/{agent_id}` |
| `GET  /v1/agents/{id}/audit` | `GET  /v1/audit/{agent_id}` |
| `GET  /v1/agents/{id}/pubkey` | (removed — read from Agent.public_key_ed25519) |
| (none) | `GET  /v1/audit/{agent_id}/verify` |
| (none) | `GET  /v1/audit/{agent_id}/annex-iv` |

### Still deferred

- **`POST /v1/agents/signup`** (the self-serve tenant+agent+wallet
  bundle): API endpoint exists, SDK method is a follow-up. File under
  AIN-79.
- **`examples/quickstart.py`** end-to-end run against prod: tracked
  as Piece 3 of AIN-79; requires founder-provided test API key and
  prod smoke time.

## [1.0.1] — 2026-05-15

Docstring-only release. No behaviour change.

### Fixed

- Module docstring on `ainfera.__init__` now reads
  `"Ainfera — the Inference of AI Agents."` (Brand v1.3 canonical).
  The 1.0.0 release shipped with the pre-lock `"prime inference for AI
  agents"` string — the source-tree fix in commit 4fd895c never made it
  into a tagged release.

## [1.0.0] — 2026-05-14

First stable release on PyPI. Published as 1.0.0 because the earlier 0.x
filenames are no longer available for upload on PyPI. Targets the D9 launch
deliverable: customers can `pip install ainfera` and exercise the five core
flows in ≤5 lines each.

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

[Unreleased]: https://github.com/ainfera-ai/sdk/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/ainfera-ai/sdk/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/ainfera-ai/sdk/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/ainfera-ai/sdk/releases/tag/v1.0.0
