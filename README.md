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

```python
from ainfera import AinferaClient

# api_key also reads from the AINFERA_API_KEY environment variable
client = AinferaClient(api_key="ak_...")
agent = client.agents.register(name="my-agent")
agent.wallet.topup(amount_usd=10)

response = agent.inference(
    model="claude-opus-4-7",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.text)
print(response.receipt.audit_url)
```

## What is Ainfera?

**The Inference of AI Agents.** Ainfera Routing picks the best model under your agent's budget and latency caps. One Agent Card across 50+ models. Every routing decision and inference call cryptographically audited. See [ainfera.ai](https://ainfera.ai) and [ainfera-ai/routing](https://github.com/ainfera-ai/routing).

## Features

- **Signed AgentCards** per Agent (JWS, RFC 7515)
- **Provider-neutral routing** across Anthropic, OpenAI, Together (more soon)
- **Atomic per-call settlement** out of an Agent-scoped Wallet
- **Tamper-evident hash-chained AuditChain** for every Agent
- **Local verification** — auditors can verify a chain offline, no Ainfera trust required
- **Sync + async** clients sharing one resource surface

## Concepts

- [Agent](https://ainfera.ai/concepts/agent)
- [AgentCard](https://ainfera.ai/concepts/agent-card)
- [Inference](https://ainfera.ai/concepts/inference)
- [Wallet](https://ainfera.ai/concepts/wallet)
- [AuditChain](https://ainfera.ai/concepts/audit-chain)

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
