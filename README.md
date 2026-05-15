# ainfera — Python SDK for Ainfera

[![PyPI version](https://img.shields.io/pypi/v/ainfera.svg)](https://pypi.org/project/ainfera/)
[![Python versions](https://img.shields.io/pypi/pyversions/ainfera.svg)](https://pypi.org/project/ainfera/)
[![CI](https://github.com/ainfera-ai/sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/ainfera-ai/sdk/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)

The Inference of AI Agents. Signed AgentCards, x402-ready Wallets, hash-chained AuditChains — out of the box.

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

Ainfera is prime inference infrastructure for AI agents. Every call your agent makes is signed, settled, and tamper-evidently logged — without you wiring any of that yourself. See [ainfera.ai](https://ainfera.ai).

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

This SDK is a thin wrapper around the Ainfera API. The underlying primitives align with:

- Open Agent Identity (OAI) Spec — [openagentidentity.org](https://openagentidentity.org)
- Mastercard Verifiable Intent
- x402 Foundation (Linux Foundation)
- NIST AI Agent Standards Initiative
- EU AI Act Annex IV

## License

Apache 2.0. See [LICENSE](./LICENSE).
