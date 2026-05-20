# SDK follow-up — 1.1.0 alignment with API Contract v1.0

**Status: shipped on `main` (2026-05-20).** Track remaining polish in Linear:

- [AIN-212](https://linear.app/ainfera/issue/AIN-212) — endpoint paths (Done in code)
- [AIN-213](https://linear.app/ainfera/issue/AIN-213) — quickstart E2E (Done in code)
- [AIN-214](https://linear.app/ainfera/issue/AIN-214) — pydantic models (Done in code)

Historical notes below (pre-1.1.0). Kept for audit trail.

## Endpoint paths

| Resource | SDK call | API path | Notes |
|---|---|---|---|
| Register agent | `POST /v1/agents` | `POST /v1/agents/register` | + a new public `/v1/agents/signup` (Tenant+Agent+Wallet bundle) — should be a first-class SDK method `client.agents.signup(...)` |
| Inference | `POST /v1/agents/{id}/inference` | `POST /v1/inference` (with `agent_id` in body) | |
| Wallet read | `GET /v1/agents/{id}/wallet` | `GET /v1/wallets/{agent_id}` | |
| Wallet top-up | `POST /v1/agents/{id}/wallet/topup` | `POST /v1/wallets/topup` (with `agent_id` in body) | |
| Ledger | `GET /v1/agents/{id}/wallet/ledger` | `GET /v1/ledger/{agent_id}` | |
| Audit chain | `GET /v1/agents/{id}/audit` | `GET /v1/audit/{agent_id}` | |
| Audit verify | (not exposed) | `GET /v1/audit/{agent_id}/verify` | add SDK method |
| Annex IV | (not exposed) | `GET /v1/audit/{agent_id}/annex-iv` | add SDK method |
| Receipt detail | `GET /v1/receipts/{id}` | (no current path on API) | drop or wait for API |
| Agent list | `GET /v1/agents` | (no current path on API) | drop or wait for API |

## Schema drift

### `Agent` (from `GET /v1/agents/{id}`)

API returns: `{id, tenant_id, name, status, public_key_ed25519, ...}`.
SDK expects: `{agent_id, name, description}`.

Fix in pydantic: `agent_id: str = Field(alias="id")` with
`model_config = ConfigDict(populate_by_name=True)` so both the signup
response (`agent_id`) and the retrieve response (`id`) bind cleanly.
Also surface `tenant_id`, `status`, `public_key_ed25519` so callers
can do offline verify without a second request.

### `InferenceResponse` (from `POST /v1/inference`)

API returns:
```
{
  "inference_id", "receipt_id", "content", "model_used",
  "finish_reason", "input_tokens", "output_tokens", "cost_usd"
}
```

SDK expects:
```
{
  "text", "inference": {inference_id, agent_id, model, messages},
  "receipt": {id, ...}, "raw"
}
```

Pick one shape, mirror it. The API is the source of truth; rewrite the
SDK model to it. Keep the convenience accessor `.text → .content`
deprecated-aliased so 1.0.x callers don't break silently.

### `SignupResponse` (new — from `POST /v1/agents/signup`)

```
{canonical_uri, did_web, tenant_id, agent_id, owner_handle,
 agent_handle, api_key, agent_card_jws}
```

Add a typed model. The `api_key` is shown once — surface that fact in
the model docstring + the resource method.

## Tests

`python/tests/test_resources.py` + `test_async_resources.py` mock the
API. Update fixtures to the real-API shape before changing the SDK
models, so the mock-based green stays meaningful.

## Acceptance

`examples/quickstart.py` should run end-to-end using ONLY the SDK,
no `httpx` direct calls.

Owner: SDK session · target ship: D6 AM as `ainfera 1.1.0` on PyPI.
