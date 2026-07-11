# ainfera — Python SDK for Ainfera

[![PyPI version](https://img.shields.io/pypi/v/ainfera.svg)](https://pypi.org/project/ainfera/)
[![Python versions](https://img.shields.io/pypi/pyversions/ainfera.svg)](https://pypi.org/project/ainfera/)
[![CI](https://github.com/ainfera-ai/sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/ainfera-ai/sdk/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)

Agent-native inference routing by Ainfera. Signed AgentCards, provider-neutral routing, hash-chained AuditChains — out of the box.

## Install

```bash
pip install ainfera
```

Requires Python 3.10+.

## Quickstart

One-shot signup provisions a Tenant + Agent + Wallet and returns a one-time
API key — persist it, then build a bound client and run a signed Inference:

```python
from ainfera import AinferaClient

# The signup endpoint is public — no API key required for this call.
result = AinferaClient().agents.signup(
    agent_handle="my-bot",
    owner_handle="your-github-login",
)
print(result.api_key)  # shown once — save it

client = AinferaClient.from_signup(result)
agent = client.agents.retrieve(result.agent_id)

response = agent.inference(
    model="ainfera-inference",  # the flagship route — Ainfera picks the best model
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=20,
)
print(response.content)     # response.text is a deprecated 1.0.x alias
print(response.receipt_id)  # links to this call's AuditChain entry
```

If you already hold a key (also read from the `AINFERA_API_KEY` environment
variable), construct the client directly and retrieve an existing Agent:

```python
client = AinferaClient(api_key="ainfera_...")
agent = client.agents.retrieve("agent_...")
```

### Ledger and AuditChain on `Agent`

Each agent exposes an append-only ledger handle backed by
`GET /v1/ledger/{agent_id}`, and a locally-verifiable AuditChain:

```python
entries = agent.ledger.entries(limit=20)
balance = agent.ledger.balance  # set after entries()

ok = agent.audit_chain.verify()  # walks the chain, verifies hashes offline
```

## What is Ainfera?

**The Inference of AI Agents.** Ainfera Inference (the flagship product — the routing brain) picks the best model under your agent's budget and latency caps. Point at `ainfera-inference` and trust the researched decision. Every routing decision and inference call cryptographically audited. See [ainfera.ai](https://ainfera.ai) and the [`ainfera-routing`](https://github.com/ainfera-ai/routing) decision library.

## Features

- **Signed AgentCards** per Agent (JWS, RFC 7515)
- **Provider-neutral routing** — pass `model="ainfera-inference"` and Ainfera selects the best model across all enrolled providers (Anthropic, OpenAI, Together, and more)
- **Atomic per-call settlement** out of an Agent-scoped Wallet
- **Tamper-evident hash-chained AuditChain** for every Agent
- **Local verification** — auditors can verify a chain offline, no Ainfera trust required
- **Sync + async** clients sharing one resource surface
- **Tools & tool_choice** pass-through for function-calling workflows
- **Routing hints** — budget caps, latency caps, quality floors, pool filters

## Compatibility table

The Ainfera API is wire-compatible with both OpenAI and Anthropic SDKs. This
Python SDK (`ainfera`) is the native wrapper with first-class typed access to
Ainfera-specific features (AgentCards, Wallets, AuditChains, Ledger).

| Feature | `ainfera` SDK | `openai` SDK (drop-in) | `anthropic` SDK (drop-in) |
|---|---|---|---|
| Routed inference (`ainfera-inference`) | ✅ | ✅ `model="ainfera-inference"` | ✅ `model="ainfera-inference"` |
| Pinned model (e.g. `claude-opus-4-7`) | ✅ | ✅ | ✅ |
| Streaming (SSE) | ⚠️ API returns 501 on `/v1/inference`; use OpenAI/Anthropic SDK for streaming | ✅ `stream=True` | ✅ `stream=True` |
| Tools / function calling | ✅ `tools=`, `tool_choice=` pass-through | ✅ | ✅ |
| Spend policies (caps) | ✅ `per_call_cap_usd`, `daily_cap_usd` | ✅ via `extra_body` | ✅ via `extra_body` |
| AgentCards (JWS-signed) | ✅ | — | — |
| Wallets & topup | ✅ | — | — |
| AuditChain local verify | ✅ `agent.audit_chain.verify()` | — | — |
| Ledger | ✅ `agent.ledger.entries()` | — | — |
| Routing hints (`routing_hint`) | ✅ `routing_hint={...}` | ✅ via `extra_body` | ✅ via `extra_body` |
| Pool filter (`auto`/`open`/`frontier`) | ✅ `pool=` | ✅ via `extra_body` | ✅ via `extra_body` |
| API base | `https://api.ainfera.ai` | `https://api.ainfera.ai/v1` | `https://api.ainfera.ai` |

**Wire format:** The Ainfera API serves both OpenAI-compatible
(`/v1/chat/completions`) and Anthropic-compatible (`/v1/messages`) endpoints.
The `ainfera` SDK uses the native `/v1/inference` surface which is
single-shot JSON only. For streaming, point an OpenAI or Anthropic SDK at
`api.ainfera.ai`.

## API versioning

The SDK targets API version `v1`. The API follows semantic versioning:

- **Major** — breaking changes to request/response shapes
- **Minor** — new optional fields, new endpoints
- **Patch** — bug fixes, no schema changes

SDK releases track API compatibility via `__version__`. The current SDK
version targets API `v1` and is backward-compatible with all `v1.x` API
revisions. See [CHANGELOG.md](./CHANGELOG.md) for the version history.

## Streaming

SSE streaming on `/v1/inference` returns `501 streaming_not_supported`.
Streaming is available via the OpenAI-compatible (`/v1/chat/completions`)
and Anthropic-compatible (`/v1/messages`) endpoints. Use the `openai` or
`anthropic` SDK pointed at `api.ainfera.ai`:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.ainfera.ai/v1",
    api_key="ainfera_...",
)
stream = client.chat.completions.create(
    model="ainfera-inference",
    messages=[{"role": "user", "content": "Write a haiku about routing."}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Tools (function calling)

Pass `tools` and `tool_choice` directly to `agent.inference()`. The API
forwards them to the selected backend and returns tool-use blocks in
`content_blocks` (Anthropic shape):

```python
response = agent.inference(
    model="ainfera-inference",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }],
    tool_choice="auto",
)
# response.content_blocks may contain {"type": "tool_use", ...}
```

## Retries and error handling

The SDK does not auto-retry. Wrap calls in your own retry logic for
production resilience. The exception hierarchy maps HTTP status codes to
semantic types:

```python
import time
from ainfera import (
    AinferaError,
    APIError,
    ModelUnavailable,
    SpendPolicyExceeded,
    WalletInsufficient,
)

def inference_with_retry(agent, *, model, messages, max_retries=3, **kwargs):
    """Retry on transient errors; surface semantic exceptions to caller."""
    for attempt in range(max_retries):
        try:
            return agent.inference(model=model, messages=messages, **kwargs)
        except (ModelUnavailable, SpendPolicyExceeded, WalletInsufficient):
            raise  # not transient — caller must fix
        except APIError as exc:
            if exc.status_code >= 500 and attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # exponential backoff
                continue
            raise
```

| Exception | HTTP status | When |
|---|---|---|
| `WalletInsufficient` | 402 | Wallet balance below request cost |
| `SpendPolicyExceeded` | 403 | Agent's spend policy blocked the call |
| `ModelUnavailable` | 422 | Requested model not available from any provider |
| `APIError` | other 4xx/5xx | All other API errors |
| `AgentCardInvalid` | — | JWS signature verification failed |
| `AuditChainBroken` | — | Local hash-chain verification detected a break |

## Async usage

```python
import asyncio
from ainfera import AsyncAinferaClient

async def main():
    client = AsyncAinferaClient(api_key="ainfera_...")
    try:
        agent = await client.agents.retrieve("agent_...")
        response = await agent.inference(
            model="ainfera-inference",
            messages=[{"role": "user", "content": "Hello"}],
        )
        print(response.content)

        # Wallet is awaitable on async agents
        wallet = await agent.wallet
        print(f"Balance: ${wallet.balance_usd}")

        # Verify audit chain locally
        ok = await agent.audit_chain.verify()
        print(f"Chain intact: {ok}")
    finally:
        await client.aclose()

asyncio.run(main())
```

## Receipt verification

Every inference response carries a `receipt_id` linking to an AuditChain
entry. The receipt is returned inline — there is no `GET /v1/receipts/{id}`
endpoint:

```python
response = agent.inference(
    model="ainfera-inference",
    messages=[{"role": "user", "content": "Hello"}],
)
# receipt_id links this call to its AuditChain entry
print(response.receipt_id)
print(response.inference_id)
print(response.cost_usd)
```

To verify the integrity of the audit trail (which includes this call's
receipt), walk the AuditChain locally:

```python
from ainfera import verify_chain

# Fetch all events and verify the hash chain offline
events = list(agent.audit_chain.events())
assert verify_chain(events) is True  # raises AuditChainBroken if tampered
```

## Local verification

Local verification proves log integrity relative to the published key —
it confirms that the AuditChain events you received from the API have not
been tampered with since the control plane hashed them. The chain rule:

    event_hash = sha256_hex(
        (previous_hash or "") + canonical_json(payload)
    )

This is a **tamper-evidence** check, not a **tamper-prevention** check.
It proves the chain is internally consistent and that no event has been
modified, inserted, or removed. It does not prove the events are truthful
— only that they are structurally intact relative to each other.

An Annex IV auditor can verify a chain without trusting Ainfera: hand
them the events plus the `verify_chain()` function and they can confirm
tamper-evidence themselves. No API key, no network call, no Ainfera trust
required.

## Routing hints

Pass `routing_hint` to influence how the routing brain selects a model:

```python
response = agent.inference(
    model="ainfera-inference",
    messages=[{"role": "user", "content": "Explain quantum computing."}],
    routing_hint={
        "quality_floor": "production",  # frontier|production|good
        "budget_cap_usd": 0.012,
        "latency_cap_ms": 2000,
    },
    pool="auto",  # auto (default) | open | frontier
)
```

## Concepts

- [Agent](https://ainfera.ai/docs#auth)
- [AgentCard](https://ainfera.ai/docs#auth)
- [Inference](https://ainfera.ai/docs#chat)
- [Wallet](https://ainfera.ai/docs#caps)
- [AuditChain](https://ainfera.ai/docs#audit)

## Compose, don't invent

This SDK is a thin wrapper around the Ainfera API. The underlying primitives align with — and link to — public standards work:

- **[Open Agent Identity (OAI) Spec](https://openagentidentity.org)** — Autonomy Next, Inc., draft v1.0.5 (Feb 2026)
- **[Mastercard Verifiable Intent](https://www.mastercard.com/us/en/news-and-trends/stories/2026/verifiable-intent.html)** — open agentic-commerce trust layer (March 2026)
- **[x402 Foundation](https://x402.foundation/)** — HTTP-native payments protocol, Linux Foundation (April 2026)
- **[NIST AI Agent Standards Initiative](https://www.nist.gov/caisi/ai-agent-standards-initiative)** — NIST CAISI (Feb 2026)
- **[EU AI Act Annex IV](https://artificialintelligenceact.eu/annex/4/)** — technical documentation for high-risk AI systems (Regulation 2024/1689)
- **[JWS, RFC 7515](https://www.rfc-editor.org/rfc/rfc7515)** — used internally for AgentCard signing

## License

Apache 2.0. See [LICENSE](./LICENSE).
